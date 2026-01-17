"""Background worker for collecting metrics from SQL Servers."""
import signal
import time
import logging
from datetime import datetime, timezone
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Optional

from app import create_app
from app.extensions import db
from app.models.system import Tenant
from app.models.tenant import Server, ServerSnapshot, CollectionConfig, RunningQuerySnapshot
from app.core.tenant_manager import tenant_manager
from app.core.encryption import decrypt_password, EncryptionError
from app.connectors import SQLServerConnector
from app.connectors.sqlserver import PYODBC_AVAILABLE

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('metric_collector')


class MetricCollector:
    """
    Background worker that collects metrics from SQL Servers.

    Iterates over all active tenants and their enabled servers,
    collecting metrics and storing them in the tenant's database.
    """

    # Default settings
    DEFAULT_CONCURRENCY = 10
    MAIN_LOOP_INTERVAL = 30  # seconds between collection cycles
    COLLECTION_TIMEOUT = 5  # seconds per server

    def __init__(self, concurrency: int = DEFAULT_CONCURRENCY):
        """
        Initialize the metric collector.

        Args:
            concurrency: Number of parallel server connections
        """
        self.app = create_app()
        self.running = True
        self.concurrency = concurrency
        self.executor: Optional[ThreadPoolExecutor] = None
        self.connector = None

    def setup(self):
        """Initialize resources."""
        if not PYODBC_AVAILABLE:
            logger.warning("pyodbc not available - SQL Server connectivity disabled")
        else:
            self.connector = SQLServerConnector()

        self.executor = ThreadPoolExecutor(max_workers=self.concurrency)
        logger.info(f"Metric collector initialized with {self.concurrency} workers")

    def shutdown(self, signum=None, frame=None):
        """Handle graceful shutdown."""
        logger.info("Shutdown signal received, stopping collector...")
        self.running = False

        if self.executor:
            self.executor.shutdown(wait=True)
            logger.info("Thread pool shut down")

    def run(self):
        """Main worker loop."""
        # Setup signal handlers
        signal.signal(signal.SIGTERM, self.shutdown)
        signal.signal(signal.SIGINT, self.shutdown)

        self.setup()

        logger.info("Metric collector started")

        while self.running:
            try:
                cycle_start = time.time()
                self.collect_all()
                cycle_duration = time.time() - cycle_start

                # Calculate sleep time to maintain interval
                sleep_time = max(0, self.MAIN_LOOP_INTERVAL - cycle_duration)
                if sleep_time > 0:
                    # Sleep in small intervals to check running flag
                    for _ in range(int(sleep_time)):
                        if not self.running:
                            break
                        time.sleep(1)

            except Exception as e:
                logger.exception(f"Error in collection cycle: {e}")
                time.sleep(5)  # Wait before retrying

        logger.info("Metric collector stopped")

    def collect_all(self):
        """Collect metrics from all active tenants."""
        with self.app.app_context():
            try:
                tenants = Tenant.query.filter_by(status='active').all()
                logger.info(f"Processing {len(tenants)} active tenants")

                for tenant in tenants:
                    if not self.running:
                        break
                    try:
                        self.collect_tenant(tenant)
                    except Exception as e:
                        logger.exception(f"Error collecting tenant {tenant.slug}: {e}")

            except Exception as e:
                logger.exception(f"Error querying tenants: {e}")

    def collect_tenant(self, tenant: Tenant):
        """Collect metrics from all enabled servers for a tenant."""
        try:
            session = tenant_manager.get_session(tenant.slug)

            # Query servers with collection enabled
            servers_with_config = session.query(Server, CollectionConfig).join(
                CollectionConfig,
                Server.id == CollectionConfig.server_id
            ).filter(
                Server.is_deleted == False,
                CollectionConfig.enabled == True
            ).all()

            if not servers_with_config:
                return

            logger.info(f"Tenant {tenant.slug}: collecting from {len(servers_with_config)} servers")

            # Submit collection tasks
            futures = []
            for server, config in servers_with_config:
                if not self.running:
                    break

                # Check if enough time has passed since last collection
                if config.last_collected_at:
                    elapsed = (datetime.now(timezone.utc) - config.last_collected_at).total_seconds()
                    if elapsed < config.interval_seconds:
                        continue  # Skip, not time yet

                future = self.executor.submit(
                    self.collect_server,
                    tenant.slug,
                    server,
                    config
                )
                futures.append((future, server.id))

            # Wait for completion with timeout
            for future, server_id in futures:
                try:
                    future.result(timeout=self.COLLECTION_TIMEOUT)
                except Exception as e:
                    logger.warning(f"Collection timeout/error for server {server_id}: {e}")

        except Exception as e:
            logger.exception(f"Error in tenant collection: {e}")
        finally:
            # Clean up session
            try:
                session.remove()
            except Exception:
                pass

    def collect_server(self, tenant_slug: str, server: Server, config: CollectionConfig):
        """
        Collect metrics from a single server.

        Args:
            tenant_slug: Tenant identifier
            server: Server model instance
            config: Collection config for the server
        """
        if not self.connector:
            logger.warning("SQL Server connector not available")
            return

        # Push Flask app context for this thread (needed for tenant_manager)
        with self.app.app_context():
            session = None
            try:
                session = tenant_manager.get_session(tenant_slug)

                # Re-query server and config in this session to ensure they're tracked
                server = session.query(Server).filter_by(id=server.id).first()
                config = session.query(CollectionConfig).filter_by(server_id=server.id).first()
                if not server or not config:
                    logger.warning(f"Server or config not found for {tenant_slug}")
                    return

                # Decrypt password
                password = None
                if server.encrypted_password:
                    try:
                        password = decrypt_password(server.encrypted_password)
                    except EncryptionError as e:
                        logger.error(f"Failed to decrypt password for {server.name}: {e}")
                        self._update_server_status(session, server, 'error')
                        return

                # Connect and collect metrics
                try:
                    conn = self.connector.connect(
                        hostname=server.hostname,
                        port=server.port,
                        instance_name=server.instance_name,
                        auth_type=server.auth_type,
                        username=server.username,
                        password=password,
                        database='master'
                    )
                except Exception as e:
                    logger.warning(f"Connection failed for {server.name}: {e}")
                    self._update_server_status(session, server, 'offline')
                    return

                try:
                    cursor = conn.cursor()
                    metrics = self._collect_metrics(cursor)

                    # Create snapshot
                    snapshot = ServerSnapshot(
                        server_id=server.id,
                        collected_at=datetime.now(timezone.utc),
                        cpu_percent=metrics.get('cpu_percent'),
                        memory_percent=metrics.get('memory_percent'),
                        connection_count=metrics.get('connection_count'),
                        batch_requests_sec=metrics.get('batch_requests_sec'),
                        page_life_expectancy=metrics.get('page_life_expectancy'),
                        blocked_processes=metrics.get('blocked_processes'),
                        extended_metrics=metrics.get('extended_metrics'),
                        status='online'
                    )
                    session.add(snapshot)

                    # Update config last_collected_at
                    config.last_collected_at = datetime.now(timezone.utc)

                    # Collect running queries if enabled
                    if config.query_collection_enabled:
                        if self._should_collect_queries(config):
                            self._collect_running_queries(session, server, config, cursor)

                    conn.close()

                    # Update server status
                    self._update_server_status(session, server, 'online')

                    session.commit()
                    logger.debug(f"Collected metrics from {server.name}")

                except Exception as e:
                    logger.exception(f"Error collecting metrics from {server.name}: {e}")
                    conn.close()
                    self._update_server_status(session, server, 'error')

            except Exception as e:
                logger.exception(f"Error in collect_server for {server.name}: {e}")
            finally:
                if session:
                    try:
                        session.remove()
                    except Exception:
                        pass

    def _collect_metrics(self, cursor) -> dict:
        """
        Execute metric collection queries.

        Returns:
            Dict of collected metrics
        """
        metrics = {}

        # Collect CPU from ring buffers
        try:
            cursor.execute("""
                SELECT TOP 1
                    record.value('(./Record/SchedulerMonitorEvent/SystemHealth/ProcessUtilization)[1]', 'int') AS SqlProcessUtilization
                FROM (
                    SELECT CAST(record AS XML) AS record
                    FROM sys.dm_os_ring_buffers
                    WHERE ring_buffer_type = N'RING_BUFFER_SCHEDULER_MONITOR'
                    AND record LIKE '%<SystemHealth>%'
                ) AS t
            """)
            row = cursor.fetchone()
            if row and row[0] is not None:
                metrics['cpu_percent'] = row[0]
        except Exception as e:
            logger.debug(f"CPU collection failed: {e}")

        # Collect memory
        try:
            cursor.execute("""
                SELECT
                    (total_physical_memory_kb - available_physical_memory_kb) * 100.0 / total_physical_memory_kb
                FROM sys.dm_os_sys_memory
            """)
            row = cursor.fetchone()
            if row and row[0] is not None:
                metrics['memory_percent'] = round(float(row[0]), 2)
        except Exception as e:
            logger.debug(f"Memory collection failed: {e}")

        # Collect connection count
        try:
            cursor.execute("SELECT COUNT(*) FROM sys.dm_exec_sessions WHERE is_user_process = 1")
            row = cursor.fetchone()
            if row:
                metrics['connection_count'] = row[0]
        except Exception as e:
            logger.debug(f"Connection count failed: {e}")

        # Collect batch requests per second
        try:
            cursor.execute("""
                SELECT cntr_value
                FROM sys.dm_os_performance_counters
                WHERE counter_name = 'Batch Requests/sec'
            """)
            row = cursor.fetchone()
            if row:
                metrics['batch_requests_sec'] = row[0]
        except Exception as e:
            logger.debug(f"Batch requests failed: {e}")

        # Collect page life expectancy
        try:
            cursor.execute("""
                SELECT cntr_value
                FROM sys.dm_os_performance_counters
                WHERE counter_name = 'Page life expectancy'
                AND object_name LIKE '%Buffer Manager%'
            """)
            row = cursor.fetchone()
            if row:
                metrics['page_life_expectancy'] = row[0]
        except Exception as e:
            logger.debug(f"PLE collection failed: {e}")

        # Collect blocked processes
        try:
            cursor.execute("SELECT COUNT(*) FROM sys.dm_exec_requests WHERE blocking_session_id > 0")
            row = cursor.fetchone()
            if row:
                metrics['blocked_processes'] = row[0]
        except Exception as e:
            logger.debug(f"Blocked processes failed: {e}")

        return metrics

    def _should_collect_queries(self, config: CollectionConfig) -> bool:
        """Check if enough time has passed to collect running queries."""
        if not config.last_query_collected_at:
            return True

        elapsed = (datetime.now(timezone.utc) - config.last_query_collected_at).total_seconds()
        return elapsed >= config.query_collection_interval

    def _collect_running_queries(self, session, server: Server, config: CollectionConfig, cursor):
        """
        Collect running queries from SQL Server.

        Args:
            session: Database session
            server: Server model instance
            config: Collection config for the server
            cursor: Database cursor
        """
        try:
            min_duration_ms = config.query_min_duration_ms or 0
            collected_at = datetime.now(timezone.utc)

            # Build dynamic WHERE clause based on filters
            where_conditions = [
                "r.session_id > 50",
                "r.session_id != @@SPID",
                "r.sql_handle IS NOT NULL",
                f"DATEDIFF(MILLISECOND, r.start_time, GETDATE()) >= {min_duration_ms}"
            ]

            # Add filter conditions (using parameterized-style escaping)
            if config.query_filter_database:
                # Escape single quotes in the pattern
                db_pattern = config.query_filter_database.replace("'", "''")
                where_conditions.append(f"DB_NAME(r.database_id) LIKE '{db_pattern}'")

            if config.query_filter_login:
                login_pattern = config.query_filter_login.replace("'", "''")
                where_conditions.append(f"s.login_name LIKE '{login_pattern}'")

            if config.query_filter_user:
                user_pattern = config.query_filter_user.replace("'", "''")
                where_conditions.append(f"s.nt_user_name LIKE '{user_pattern}'")

            if config.query_filter_text_include:
                include_pattern = config.query_filter_text_include.replace("'", "''")
                where_conditions.append(f"t.text LIKE '{include_pattern}'")

            if config.query_filter_text_exclude:
                exclude_pattern = config.query_filter_text_exclude.replace("'", "''")
                where_conditions.append(f"t.text NOT LIKE '{exclude_pattern}'")

            where_clause = " AND ".join(where_conditions)

            # Determine if we need to join sys.dm_exec_sessions
            needs_session_join = bool(config.query_filter_login or config.query_filter_user)
            session_join = "JOIN sys.dm_exec_sessions s ON r.session_id = s.session_id" if needs_session_join else ""

            # Query to fetch running queries with query text
            cursor.execute(f"""
                SELECT
                    r.session_id,
                    r.request_id,
                    DB_NAME(r.database_id) AS database_name,
                    SUBSTRING(t.text,
                        (r.statement_start_offset/2) + 1,
                        ((CASE WHEN r.statement_end_offset = -1
                             THEN LEN(CONVERT(NVARCHAR(MAX), t.text)) * 2
                             ELSE r.statement_end_offset
                        END) - r.statement_start_offset) / 2 + 1) AS query_text,
                    r.start_time,
                    DATEDIFF(MILLISECOND, r.start_time, GETDATE()) AS duration_ms,
                    r.status,
                    r.wait_type,
                    r.wait_time AS wait_time_ms,
                    r.cpu_time AS cpu_time_ms,
                    r.logical_reads,
                    r.reads AS physical_reads,
                    r.writes
                FROM sys.dm_exec_requests r
                CROSS APPLY sys.dm_exec_sql_text(r.sql_handle) t
                {session_join}
                WHERE {where_clause}
                ORDER BY r.start_time
            """)

            rows = cursor.fetchall()
            query_count = 0

            for row in rows:
                try:
                    snapshot = RunningQuerySnapshot(
                        server_id=server.id,
                        collected_at=collected_at,
                        session_id=row[0],
                        request_id=row[1],
                        database_name=row[2],
                        query_text=row[3],
                        start_time=row[4],
                        duration_ms=row[5],
                        status=row[6],
                        wait_type=row[7],
                        wait_time_ms=row[8],
                        cpu_time_ms=row[9],
                        logical_reads=row[10],
                        physical_reads=row[11],
                        writes=row[12],
                    )
                    session.add(snapshot)
                    query_count += 1
                except Exception as e:
                    logger.debug(f"Error processing query row: {e}")
                    continue

            # Update last_query_collected_at
            config.last_query_collected_at = collected_at

            if query_count > 0:
                logger.debug(f"Collected {query_count} running queries from {server.name}")

        except Exception as e:
            logger.debug(f"Running queries collection failed for {server.name}: {e}")

    def _update_server_status(self, session, server: Server, status: str):
        """Update server status and last_checked timestamp."""
        try:
            server.status = status
            server.last_checked = datetime.now(timezone.utc)
            session.commit()
        except Exception as e:
            logger.error(f"Failed to update server status: {e}")
            session.rollback()


def main():
    """Entry point for running the collector."""
    import argparse

    parser = argparse.ArgumentParser(description='DbTools Metric Collector')
    parser.add_argument(
        '--concurrency',
        type=int,
        default=MetricCollector.DEFAULT_CONCURRENCY,
        help=f'Number of parallel connections (default: {MetricCollector.DEFAULT_CONCURRENCY})'
    )
    args = parser.parse_args()

    collector = MetricCollector(concurrency=args.concurrency)
    collector.run()


if __name__ == '__main__':
    main()
