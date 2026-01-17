"""Service for managing scheduled jobs."""
from datetime import datetime, timezone
from typing import Optional, List, Dict, Any
from uuid import UUID

from sqlalchemy.orm import Session

from app.models.tenant import Job, JobExecution
from app.services.scheduler_service import SchedulerService


class JobValidationError(Exception):
    """Raised when job validation fails."""
    def __init__(self, errors: List[str]):
        self.errors = errors
        super().__init__(f"Validation errors: {', '.join(errors)}")


class JobService:
    """Service for managing jobs."""

    def __init__(self, session: Session):
        self.session = session
        self.scheduler_service = SchedulerService(session)

    def validate_job_input(
        self,
        name: str,
        job_type: str,
        schedule_type: str,
        schedule_config: Dict[str, Any],
        configuration: Optional[Dict[str, Any]] = None
    ) -> List[str]:
        """Validate job input data.

        Returns list of error messages (empty if valid).
        """
        errors = []

        if not name or not name.strip():
            errors.append("name is required")

        if not job_type:
            errors.append("type is required")
        elif job_type not in Job.VALID_JOB_TYPES:
            errors.append(f"Invalid type. Must be one of: {Job.VALID_JOB_TYPES}")

        if not schedule_type:
            errors.append("schedule_type is required")
        elif schedule_type not in Job.VALID_SCHEDULE_TYPES:
            errors.append(f"Invalid schedule_type. Must be one of: {Job.VALID_SCHEDULE_TYPES}")
        else:
            # Validate schedule_config based on type
            if schedule_type == Job.SCHEDULE_INTERVAL:
                if not schedule_config or 'interval_seconds' not in schedule_config:
                    errors.append("schedule_config.interval_seconds is required for interval schedule")
                elif not isinstance(schedule_config.get('interval_seconds'), int):
                    errors.append("interval_seconds must be an integer")
                elif schedule_config['interval_seconds'] < 60:
                    errors.append("interval_seconds must be at least 60")

            elif schedule_type == Job.SCHEDULE_CRON:
                if not schedule_config or 'expression' not in schedule_config:
                    errors.append("schedule_config.expression is required for cron schedule")

            elif schedule_type == Job.SCHEDULE_ONCE:
                if not schedule_config or 'run_at' not in schedule_config:
                    errors.append("schedule_config.run_at is required for once schedule")

        return errors

    def create_job(
        self,
        name: str,
        job_type: str,
        schedule_type: str,
        schedule_config: Dict[str, Any],
        configuration: Optional[Dict[str, Any]] = None,
        is_enabled: bool = True,
    ) -> Job:
        """Create a new scheduled job.

        Args:
            name: Job name
            job_type: Type of job
            schedule_type: Type of schedule
            schedule_config: Schedule configuration
            configuration: Job-specific configuration
            is_enabled: Whether job is enabled

        Returns:
            Created job

        Raises:
            JobValidationError: If validation fails
        """
        errors = self.validate_job_input(name, job_type, schedule_type, schedule_config, configuration)
        if errors:
            raise JobValidationError(errors)

        job = Job(
            name=name.strip(),
            type=job_type,
            configuration=configuration or {},
            schedule_type=schedule_type,
            schedule_config=schedule_config,
            is_enabled=is_enabled,
        )

        # Calculate initial next_run_at
        if is_enabled:
            job.next_run_at = self.scheduler_service.calculate_next_run(job)

        self.session.add(job)
        self.session.commit()

        return job

    def get_job(self, job_id: UUID) -> Optional[Job]:
        """Get a job by ID.

        Args:
            job_id: Job UUID

        Returns:
            Job or None if not found
        """
        return self.session.query(Job).filter(Job.id == job_id).first()

    def get_all_jobs(
        self,
        job_type: Optional[str] = None,
        is_enabled: Optional[bool] = None,
        limit: int = 100,
        offset: int = 0,
    ) -> tuple[List[Job], int]:
        """Get all jobs with optional filters.

        Args:
            job_type: Filter by job type
            is_enabled: Filter by enabled status
            limit: Maximum results
            offset: Pagination offset

        Returns:
            Tuple of (jobs list, total count)
        """
        query = self.session.query(Job)

        if job_type:
            query = query.filter(Job.type == job_type)

        if is_enabled is not None:
            query = query.filter(Job.is_enabled == is_enabled)

        total = query.count()
        jobs = query.order_by(Job.name).offset(offset).limit(limit).all()

        return jobs, total

    def update_job(
        self,
        job_id: UUID,
        name: Optional[str] = None,
        configuration: Optional[Dict[str, Any]] = None,
        schedule_type: Optional[str] = None,
        schedule_config: Optional[Dict[str, Any]] = None,
        is_enabled: Optional[bool] = None,
    ) -> Optional[Job]:
        """Update a job.

        Args:
            job_id: Job UUID
            name: New name
            configuration: New configuration
            schedule_type: New schedule type
            schedule_config: New schedule config
            is_enabled: New enabled status

        Returns:
            Updated job or None if not found

        Raises:
            JobValidationError: If validation fails
        """
        job = self.get_job(job_id)
        if not job:
            return None

        # Build updated values for validation
        new_name = name if name is not None else job.name
        new_type = job.type  # Type cannot be changed
        new_schedule_type = schedule_type if schedule_type is not None else job.schedule_type
        new_schedule_config = schedule_config if schedule_config is not None else job.schedule_config
        new_configuration = configuration if configuration is not None else job.configuration

        # Validate if schedule is being changed
        if schedule_type is not None or schedule_config is not None:
            errors = self.validate_job_input(
                new_name, new_type, new_schedule_type, new_schedule_config, new_configuration
            )
            if errors:
                raise JobValidationError(errors)

        # Apply updates
        if name is not None:
            job.name = name.strip()

        if configuration is not None:
            job.configuration = configuration

        if schedule_type is not None:
            job.schedule_type = schedule_type

        if schedule_config is not None:
            job.schedule_config = schedule_config

        # Recalculate next_run if schedule changed or job is being enabled
        schedule_changed = schedule_type is not None or schedule_config is not None
        was_disabled = not job.is_enabled

        if is_enabled is not None:
            job.is_enabled = is_enabled

        if job.is_enabled and (schedule_changed or (was_disabled and is_enabled)):
            job.next_run_at = self.scheduler_service.calculate_next_run(job)
        elif not job.is_enabled:
            job.next_run_at = None

        self.session.commit()
        return job

    def delete_job(self, job_id: UUID) -> bool:
        """Delete a job.

        Args:
            job_id: Job UUID

        Returns:
            True if deleted, False if not found
        """
        job = self.get_job(job_id)
        if not job:
            return False

        self.session.delete(job)
        self.session.commit()
        return True

    def enable_job(self, job_id: UUID) -> Optional[Job]:
        """Enable a job.

        Args:
            job_id: Job UUID

        Returns:
            Updated job or None if not found
        """
        job = self.get_job(job_id)
        if not job:
            return None

        job.is_enabled = True
        job.next_run_at = self.scheduler_service.calculate_next_run(job)

        self.session.commit()
        return job

    def disable_job(self, job_id: UUID) -> Optional[Job]:
        """Disable a job.

        Args:
            job_id: Job UUID

        Returns:
            Updated job or None if not found
        """
        job = self.get_job(job_id)
        if not job:
            return None

        job.is_enabled = False
        job.next_run_at = None

        self.session.commit()
        return job

    def run_job_now(self, job_id: UUID) -> Optional[JobExecution]:
        """Trigger immediate execution of a job.

        Creates an execution record with status 'pending'.
        The scheduler worker will pick it up on next poll.

        Args:
            job_id: Job UUID

        Returns:
            Created execution or None if job not found
        """
        job = self.get_job(job_id)
        if not job:
            return None

        # Set next_run_at to now to trigger immediate execution
        job.next_run_at = datetime.now(timezone.utc)

        self.session.commit()
        return job

    def get_job_executions(
        self,
        job_id: UUID,
        limit: int = 50,
        offset: int = 0,
        status: Optional[str] = None,
    ) -> tuple[List[JobExecution], int]:
        """Get execution history for a job.

        Args:
            job_id: Job UUID
            limit: Maximum results
            offset: Pagination offset
            status: Filter by status

        Returns:
            Tuple of (executions list, total count)
        """
        query = self.session.query(JobExecution).filter(
            JobExecution.job_id == job_id
        )

        if status:
            query = query.filter(JobExecution.status == status)

        total = query.count()
        executions = query.order_by(
            JobExecution.started_at.desc()
        ).offset(offset).limit(limit).all()

        return executions, total

    def get_execution(self, execution_id: UUID) -> Optional[JobExecution]:
        """Get an execution by ID.

        Args:
            execution_id: Execution UUID

        Returns:
            JobExecution or None if not found
        """
        return self.session.query(JobExecution).filter(
            JobExecution.id == execution_id
        ).first()

    def get_job_with_last_execution(self, job: Job) -> Dict[str, Any]:
        """Get job dict with last execution status.

        Args:
            job: Job instance

        Returns:
            Job dict with last_status and last_run_at
        """
        result = job.to_dict()

        # Get last execution
        last_exec = self.session.query(JobExecution).filter(
            JobExecution.job_id == job.id
        ).order_by(JobExecution.started_at.desc()).first()

        if last_exec:
            result['last_status'] = last_exec.status
            result['last_execution_at'] = last_exec.started_at.isoformat() if last_exec.started_at else None
        else:
            result['last_status'] = None
            result['last_execution_at'] = None

        return result
