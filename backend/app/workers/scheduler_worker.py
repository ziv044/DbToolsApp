"""Background scheduler worker for executing scheduled jobs.

This worker runs as a background process and:
1. Polls for due jobs across all active tenants
2. Executes jobs with proper error handling and timeouts
3. Updates job execution records and next_run_at times
4. Handles graceful recovery after restarts

Usage:
    python -m app.workers.scheduler_worker

Or import and run programmatically:
    from app.workers.scheduler_worker import JobSchedulerWorker
    worker = JobSchedulerWorker()
    worker.start()
"""
import logging
import signal
import sys
import time
from datetime import datetime, timezone
from threading import Event

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('scheduler_worker')


class JobSchedulerWorker:
    """Background worker that polls and executes scheduled jobs."""

    def __init__(
        self,
        poll_interval_seconds: int = 30,
        max_workers: int = 5,
        default_timeout: int = 1800
    ):
        """Initialize the scheduler worker.

        Args:
            poll_interval_seconds: How often to poll for due jobs
            max_workers: Maximum concurrent job executions
            default_timeout: Default job timeout in seconds
        """
        self.poll_interval = poll_interval_seconds
        self.max_workers = max_workers
        self.default_timeout = default_timeout

        self.scheduler = None
        self.executor = None
        self.app = None
        self._shutdown_event = Event()

    def create_app(self):
        """Create Flask app instance."""
        # Import here to avoid circular imports
        from app import create_app
        return create_app()

    def start(self):
        """Start the scheduler worker."""
        logger.info("Starting Job Scheduler Worker...")

        # Create Flask app context
        self.app = self.create_app()

        # Import services within app context
        with self.app.app_context():
            from app.services.scheduler_service import create_default_executor

            self.executor = create_default_executor()

            # Create APScheduler
            self.scheduler = BackgroundScheduler()

            # Add job checker
            self.scheduler.add_job(
                self._check_jobs,
                IntervalTrigger(seconds=self.poll_interval),
                id='job_checker',
                name='Check for due jobs',
                replace_existing=True,
            )

            # Start scheduler
            self.scheduler.start()
            logger.info(f"Scheduler started. Polling every {self.poll_interval} seconds.")

            # Run initial check immediately
            self._check_jobs()

    def stop(self):
        """Stop the scheduler worker gracefully."""
        logger.info("Stopping Job Scheduler Worker...")
        self._shutdown_event.set()

        if self.scheduler:
            self.scheduler.shutdown(wait=True)
            logger.info("Scheduler stopped.")

        if self.executor:
            self.executor.shutdown(wait=True)
            logger.info("Executor stopped.")

    def _check_jobs(self):
        """Check for and execute due jobs across all tenants."""
        if self._shutdown_event.is_set():
            return

        with self.app.app_context():
            try:
                from app.models.system import Tenant
                from app.core.tenant_manager import tenant_manager
                from app.models.tenant import Job
                from app.services.scheduler_service import (
                    SchedulerService,
                    JobExecutionContext
                )

                # Get all active tenants
                tenants = Tenant.query.filter_by(status='active').all()
                logger.debug(f"Checking {len(tenants)} active tenants for due jobs")

                for tenant in tenants:
                    if self._shutdown_event.is_set():
                        break

                    try:
                        self._process_tenant_jobs(tenant, tenant_manager)
                    except Exception as e:
                        logger.error(f"Error processing jobs for tenant {tenant.slug}: {e}")

            except Exception as e:
                logger.exception(f"Error in job checker: {e}")

    def _process_tenant_jobs(self, tenant, tenant_manager):
        """Process due jobs for a specific tenant.

        Args:
            tenant: Tenant instance
            tenant_manager: TenantManager instance
        """
        from app.models.tenant import Job
        from app.services.scheduler_service import (
            SchedulerService,
            JobExecutionContext
        )

        session = tenant_manager.get_session(tenant.slug)

        try:
            service = SchedulerService(session)
            due_jobs = service.get_due_jobs()

            if due_jobs:
                logger.info(f"Found {len(due_jobs)} due jobs for tenant {tenant.slug}")

            for job in due_jobs:
                if self._shutdown_event.is_set():
                    break

                try:
                    self._execute_job(tenant.slug, job, session, service)
                except Exception as e:
                    logger.error(f"Error executing job {job.id} ({job.name}): {e}")

        finally:
            # Clean up session
            session.remove()

    def _execute_job(self, tenant_slug: str, job, session, service):
        """Execute a single job.

        Args:
            tenant_slug: Tenant identifier
            job: Job instance to execute
            session: SQLAlchemy session
            service: SchedulerService instance
        """
        from app.services.scheduler_service import JobExecutionContext

        logger.info(f"Executing job {job.id} ({job.name}) for tenant {tenant_slug}")

        # Create execution record
        execution = service.create_execution(job)

        try:
            # Create execution context
            context = JobExecutionContext(
                job=job,
                execution=execution,
                session=session,
                tenant_slug=tenant_slug
            )

            # Execute job
            success, result, error_message = self.executor.execute(context)

            # Update execution record
            service.complete_execution(
                execution,
                success=success,
                result=result,
                error_message=error_message
            )

            # Update job's next_run_at
            service.update_job_after_execution(job)

            if success:
                logger.info(f"Job {job.id} ({job.name}) completed successfully")
            else:
                logger.warning(f"Job {job.id} ({job.name}) failed: {error_message}")

        except Exception as e:
            logger.exception(f"Error executing job {job.id}: {e}")

            # Mark execution as failed
            service.complete_execution(
                execution,
                success=False,
                error_message=str(e)
            )

            # Still update next_run_at to avoid infinite retries
            service.update_job_after_execution(job)

    def run_forever(self):
        """Run the worker until shutdown signal received."""
        self.start()

        # Setup signal handlers
        def signal_handler(signum, frame):
            logger.info(f"Received signal {signum}, shutting down...")
            self.stop()
            sys.exit(0)

        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)

        # Keep running
        try:
            while not self._shutdown_event.is_set():
                time.sleep(1)
        except KeyboardInterrupt:
            self.stop()


def main():
    """Main entry point for the scheduler worker."""
    import argparse

    parser = argparse.ArgumentParser(description='Job Scheduler Worker')
    parser.add_argument(
        '--poll-interval',
        type=int,
        default=30,
        help='Seconds between job checks (default: 30)'
    )
    parser.add_argument(
        '--max-workers',
        type=int,
        default=5,
        help='Maximum concurrent job executions (default: 5)'
    )
    parser.add_argument(
        '--timeout',
        type=int,
        default=1800,
        help='Default job timeout in seconds (default: 1800)'
    )

    args = parser.parse_args()

    worker = JobSchedulerWorker(
        poll_interval_seconds=args.poll_interval,
        max_workers=args.max_workers,
        default_timeout=args.timeout
    )
    worker.run_forever()


if __name__ == '__main__':
    main()
