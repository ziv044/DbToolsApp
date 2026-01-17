"""Job scheduler service for executing scheduled jobs across tenants."""
import logging
from datetime import datetime, timezone, timedelta
from concurrent.futures import ThreadPoolExecutor, TimeoutError as FuturesTimeoutError
from typing import Optional, Callable
from uuid import UUID

from croniter import croniter
from sqlalchemy.orm import Session

from app.models.tenant import Job, JobExecution


logger = logging.getLogger(__name__)

# Default configuration
DEFAULT_CONCURRENCY_LIMIT = 5
DEFAULT_TIMEOUT_SECONDS = 1800  # 30 minutes


class JobExecutionContext:
    """Context for a job execution."""

    def __init__(self, job: Job, execution: JobExecution, session: Session, tenant_slug: str):
        self.job = job
        self.execution = execution
        self.session = session
        self.tenant_slug = tenant_slug


class SchedulerService:
    """Service for managing job scheduling and execution."""

    def __init__(self, session: Session):
        self.session = session

    def get_due_jobs(self) -> list[Job]:
        """Get all jobs that are due to run.

        Returns jobs where:
        - next_run_at <= now
        - is_enabled = True
        """
        now = datetime.now(timezone.utc)

        return self.session.query(Job).filter(
            Job.next_run_at <= now,
            Job.is_enabled == True
        ).order_by(Job.next_run_at).all()

    def create_execution(self, job: Job, server_id: Optional[UUID] = None) -> JobExecution:
        """Create a new job execution record.

        Args:
            job: The job to execute
            server_id: Optional server ID if job targets a specific server

        Returns:
            Created JobExecution with status 'running'
        """
        execution = JobExecution(
            job_id=job.id,
            server_id=server_id,
            status=JobExecution.STATUS_RUNNING,
            started_at=datetime.now(timezone.utc),
        )
        self.session.add(execution)
        self.session.commit()

        return execution

    def complete_execution(
        self,
        execution: JobExecution,
        success: bool,
        result: Optional[dict] = None,
        error_message: Optional[str] = None
    ) -> JobExecution:
        """Mark an execution as complete.

        Args:
            execution: The execution to complete
            success: Whether the execution was successful
            result: Optional result data
            error_message: Optional error message if failed

        Returns:
            Updated JobExecution
        """
        execution.status = JobExecution.STATUS_SUCCESS if success else JobExecution.STATUS_FAILED
        execution.completed_at = datetime.now(timezone.utc)
        execution.result = result
        execution.error_message = error_message

        self.session.commit()
        return execution

    def calculate_next_run(self, job: Job) -> Optional[datetime]:
        """Calculate the next run time for a job based on its schedule.

        Args:
            job: The job to calculate next run for

        Returns:
            Next run datetime or None if job should not run again
        """
        now = datetime.now(timezone.utc)
        schedule_type = job.schedule_type
        schedule_config = job.schedule_config or {}

        if schedule_type == Job.SCHEDULE_ONCE:
            # One-time job, no next run
            return None

        elif schedule_type == Job.SCHEDULE_INTERVAL:
            # Interval-based scheduling
            interval_seconds = schedule_config.get('interval_seconds', 3600)
            return now + timedelta(seconds=interval_seconds)

        elif schedule_type == Job.SCHEDULE_CRON:
            # Cron-based scheduling
            expression = schedule_config.get('expression', '0 * * * *')  # Default: every hour
            try:
                cron = croniter(expression, now)
                return cron.get_next(datetime)
            except (ValueError, KeyError) as e:
                logger.error(f"Invalid cron expression for job {job.id}: {expression} - {e}")
                return None

        elif schedule_type == Job.SCHEDULE_EVENT_TRIGGERED:
            # Event-triggered jobs don't have scheduled next run
            return None

        return None

    def update_job_after_execution(self, job: Job) -> Job:
        """Update job after execution (set next_run_at and last_run_at).

        Args:
            job: The job to update

        Returns:
            Updated job
        """
        job.last_run_at = datetime.now(timezone.utc)
        job.next_run_at = self.calculate_next_run(job)

        self.session.commit()
        return job


class JobExecutor:
    """Executes jobs with proper error handling and timeouts."""

    def __init__(
        self,
        max_workers: int = DEFAULT_CONCURRENCY_LIMIT,
        default_timeout: int = DEFAULT_TIMEOUT_SECONDS
    ):
        self.executor = ThreadPoolExecutor(max_workers=max_workers)
        self.default_timeout = default_timeout
        self.handlers: dict[str, Callable[[JobExecutionContext], dict]] = {}

    def register_handler(self, job_type: str, handler: Callable[[JobExecutionContext], dict]):
        """Register a handler for a specific job type.

        Args:
            job_type: The job type (e.g., 'policy_execution', 'data_collection')
            handler: Function that takes JobExecutionContext and returns result dict
        """
        self.handlers[job_type] = handler
        logger.info(f"Registered handler for job type: {job_type}")

    def execute(
        self,
        context: JobExecutionContext,
        timeout: Optional[int] = None
    ) -> tuple[bool, Optional[dict], Optional[str]]:
        """Execute a job with timeout handling.

        Args:
            context: The job execution context
            timeout: Timeout in seconds (uses job config or default)

        Returns:
            Tuple of (success, result_dict, error_message)
        """
        job = context.job
        timeout = timeout or context.job.configuration.get('timeout_seconds', self.default_timeout)

        handler = self.handlers.get(job.type)
        if not handler:
            error_msg = f"No handler registered for job type: {job.type}"
            logger.error(error_msg)
            return False, None, error_msg

        try:
            future = self.executor.submit(handler, context)
            result = future.result(timeout=timeout)
            return True, result, None

        except FuturesTimeoutError:
            error_msg = f"Job execution timed out after {timeout} seconds"
            logger.error(f"Job {job.id} ({job.name}): {error_msg}")
            return False, None, error_msg

        except Exception as e:
            error_msg = str(e)
            logger.exception(f"Job {job.id} ({job.name}) failed: {error_msg}")
            return False, None, error_msg

    def shutdown(self, wait: bool = True):
        """Shutdown the executor.

        Args:
            wait: Whether to wait for pending jobs to complete
        """
        self.executor.shutdown(wait=wait)


# ============== Default Job Handlers ==============


def policy_execution_handler(context: JobExecutionContext) -> dict:
    """Handler for policy execution jobs.

    This handler executes a policy against target servers.
    """
    job = context.job
    config = job.configuration

    # Get policy and deployment info from config
    policy_id = config.get('policy_id')
    deployment_id = config.get('deployment_id')

    # TODO: Implement actual policy execution
    # For now, return placeholder result
    return {
        'policy_id': policy_id,
        'deployment_id': deployment_id,
        'servers_affected': 0,
        'message': 'Policy execution placeholder - implementation pending',
    }


def data_collection_handler(context: JobExecutionContext) -> dict:
    """Handler for data collection jobs.

    This handler collects metrics from target servers.
    """
    job = context.job
    config = job.configuration

    # Get server or group info from config
    server_id = config.get('server_id')
    group_id = config.get('group_id')

    # TODO: Implement actual data collection
    return {
        'server_id': server_id,
        'group_id': group_id,
        'metrics_collected': 0,
        'message': 'Data collection placeholder - implementation pending',
    }


def custom_script_handler(context: JobExecutionContext) -> dict:
    """Handler for custom script jobs.

    This handler executes custom T-SQL scripts.
    """
    job = context.job
    config = job.configuration

    script_content = config.get('script_content', '')

    # TODO: Implement actual script execution
    return {
        'script_length': len(script_content),
        'rows_affected': 0,
        'message': 'Custom script placeholder - implementation pending',
    }


def alert_check_handler(context: JobExecutionContext) -> dict:
    """Handler for alert checking jobs.

    This handler checks for alert conditions.
    """
    job = context.job
    config = job.configuration

    # TODO: Implement actual alert checking
    return {
        'alerts_triggered': 0,
        'conditions_checked': 0,
        'message': 'Alert check placeholder - implementation pending',
    }


def create_default_executor() -> JobExecutor:
    """Create a JobExecutor with default handlers registered.

    Returns:
        Configured JobExecutor instance
    """
    executor = JobExecutor()

    # Register default handlers
    executor.register_handler(Job.TYPE_POLICY_EXECUTION, policy_execution_handler)
    executor.register_handler(Job.TYPE_DATA_COLLECTION, data_collection_handler)
    executor.register_handler(Job.TYPE_CUSTOM_SCRIPT, custom_script_handler)
    executor.register_handler(Job.TYPE_ALERT_CHECK, alert_check_handler)

    return executor
