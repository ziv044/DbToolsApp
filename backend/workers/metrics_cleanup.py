"""Background worker for cleaning up old metrics data."""
import signal
import time
import logging
from datetime import datetime, timezone, timedelta
from typing import Optional

from app import create_app
from app.models.system import Tenant
from app.models.tenant import Setting, ServerSnapshot, Metric, RunningQuerySnapshot
from app.core.tenant_manager import tenant_manager
from app.services.retention_service import RetentionService

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('metrics_cleanup')


class MetricsCleanup:
    """
    Background worker that cleans up old metrics data.

    Runs daily to delete metrics older than the configured retention period.
    Deletes in batches to avoid long locks.
    """

    # Batch size for deletions
    BATCH_SIZE = 10000

    # Run cleanup every 24 hours
    CLEANUP_INTERVAL_HOURS = 24

    def __init__(self):
        """Initialize the cleanup worker."""
        self.app = create_app()
        self.running = True
        self.last_cleanup: Optional[datetime] = None

    def shutdown(self, signum=None, frame=None):
        """Handle graceful shutdown."""
        logger.info("Shutdown signal received, stopping cleanup worker...")
        self.running = False

    def run(self):
        """Main worker loop - runs cleanup daily."""
        # Setup signal handlers
        signal.signal(signal.SIGTERM, self.shutdown)
        signal.signal(signal.SIGINT, self.shutdown)

        logger.info("Metrics cleanup worker started")

        # Run immediately on startup
        self.run_cleanup_all()
        self.last_cleanup = datetime.now(timezone.utc)

        while self.running:
            try:
                # Check if it's time to run cleanup (every 24 hours)
                now = datetime.now(timezone.utc)
                if self.last_cleanup:
                    hours_since_cleanup = (now - self.last_cleanup).total_seconds() / 3600
                    if hours_since_cleanup >= self.CLEANUP_INTERVAL_HOURS:
                        self.run_cleanup_all()
                        self.last_cleanup = now

                # Sleep in small intervals to check running flag
                for _ in range(60):  # Check every minute
                    if not self.running:
                        break
                    time.sleep(1)

            except Exception as e:
                logger.exception(f"Error in cleanup loop: {e}")
                time.sleep(60)

        logger.info("Metrics cleanup worker stopped")

    def run_cleanup_all(self):
        """Run cleanup for all active tenants."""
        with self.app.app_context():
            try:
                tenants = Tenant.query.filter_by(status='active').all()
                logger.info(f"Running cleanup for {len(tenants)} active tenants")

                for tenant in tenants:
                    if not self.running:
                        break
                    try:
                        self.cleanup_tenant(tenant)
                    except Exception as e:
                        logger.exception(f"Error cleaning up tenant {tenant.slug}: {e}")

            except Exception as e:
                logger.exception(f"Error querying tenants: {e}")

    def cleanup_tenant(self, tenant: Tenant):
        """Clean up old metrics for a tenant."""
        session = None
        try:
            session = tenant_manager.get_session(tenant.slug)

            # Get retention period
            service = RetentionService(session)
            retention_days = service.get_retention_days()

            # Calculate cutoff date
            cutoff = datetime.now(timezone.utc) - timedelta(days=retention_days)

            logger.info(f"Tenant {tenant.slug}: cleaning data older than {cutoff.date()} ({retention_days} days retention)")

            # Clean up snapshots
            snapshots_deleted = self._delete_in_batches(
                session,
                ServerSnapshot,
                ServerSnapshot.collected_at < cutoff
            )

            # Clean up individual metrics
            metrics_deleted = self._delete_in_batches(
                session,
                Metric,
                Metric.collected_at < cutoff
            )

            # Clean up running query snapshots
            queries_deleted = self._delete_in_batches(
                session,
                RunningQuerySnapshot,
                RunningQuerySnapshot.collected_at < cutoff
            )

            if snapshots_deleted > 0 or metrics_deleted > 0 or queries_deleted > 0:
                logger.info(
                    f"Tenant {tenant.slug}: deleted {snapshots_deleted} snapshots, "
                    f"{metrics_deleted} metrics, {queries_deleted} running queries"
                )
            else:
                logger.debug(f"Tenant {tenant.slug}: no data to clean up")

        except Exception as e:
            logger.exception(f"Error in tenant cleanup: {e}")
        finally:
            if session:
                try:
                    session.remove()
                except Exception:
                    pass

    def _delete_in_batches(self, session, model, condition) -> int:
        """
        Delete rows matching condition in batches.

        Args:
            session: SQLAlchemy session
            model: Model class to delete from
            condition: Filter condition for deletion

        Returns:
            Total number of rows deleted
        """
        total_deleted = 0

        while self.running:
            try:
                # Get IDs of rows to delete (limited batch)
                rows_to_delete = session.query(model.id).filter(
                    condition
                ).limit(self.BATCH_SIZE).all()

                if not rows_to_delete:
                    break

                ids_to_delete = [row[0] for row in rows_to_delete]

                # Delete the batch
                deleted = session.query(model).filter(
                    model.id.in_(ids_to_delete)
                ).delete(synchronize_session=False)

                session.commit()
                total_deleted += deleted

                logger.debug(f"Deleted batch of {deleted} {model.__tablename__}")

                if deleted < self.BATCH_SIZE:
                    break

            except Exception as e:
                logger.exception(f"Error deleting batch: {e}")
                session.rollback()
                break

        return total_deleted


def main():
    """Entry point for running the cleanup worker."""
    import argparse

    parser = argparse.ArgumentParser(description='DbTools Metrics Cleanup Worker')
    parser.add_argument(
        '--once',
        action='store_true',
        help='Run cleanup once and exit (no scheduling)'
    )
    args = parser.parse_args()

    cleanup = MetricsCleanup()

    if args.once:
        with cleanup.app.app_context():
            cleanup.run_cleanup_all()
    else:
        cleanup.run()


if __name__ == '__main__':
    main()
