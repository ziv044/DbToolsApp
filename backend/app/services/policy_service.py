"""Service for managing policies."""
from typing import Optional, List, Dict, Any
from uuid import UUID
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

from app.models.tenant import Policy, PolicyVersion


# Configuration schemas for different policy types
POLICY_SCHEMAS = {
    'backup': {
        'required': ['backup_type', 'destination_path'],
        'optional': ['compression', 'retention_days', 'verify_backup', 'copy_only'],
        'defaults': {
            'compression': True,
            'retention_days': 7,
            'verify_backup': True,
            'copy_only': False,
        },
        'valid_values': {
            'backup_type': ['full', 'differential', 'log'],
        },
    },
    'index_maintenance': {
        'required': [],
        'optional': ['fragmentation_threshold', 'rebuild_threshold', 'include_statistics', 'max_dop', 'online'],
        'defaults': {
            'fragmentation_threshold': 10,
            'rebuild_threshold': 30,
            'include_statistics': True,
            'max_dop': 0,
            'online': True,
        },
    },
    'integrity_check': {
        'required': [],
        'optional': ['check_type', 'include_indexes', 'include_extended_logical_checks', 'max_dop'],
        'defaults': {
            'check_type': 'physical',
            'include_indexes': True,
            'include_extended_logical_checks': False,
            'max_dop': 0,
        },
        'valid_values': {
            'check_type': ['physical', 'logical', 'both'],
        },
    },
    'custom_script': {
        'required': ['script_content'],
        'optional': ['timeout_seconds', 'run_as_user'],
        'defaults': {
            'timeout_seconds': 3600,
        },
    },
}


class PolicyValidationError(Exception):
    """Raised when policy configuration validation fails."""
    def __init__(self, errors: List[str]):
        self.errors = errors
        super().__init__(f"Validation errors: {', '.join(errors)}")


class PolicyService:
    """Service for managing policies."""

    def __init__(self, session: Session):
        self.session = session

    def validate_configuration(self, policy_type: str, configuration: Dict[str, Any]) -> Dict[str, Any]:
        """Validate and normalize policy configuration.

        Args:
            policy_type: Type of policy
            configuration: Configuration dictionary to validate

        Returns:
            Normalized configuration with defaults applied

        Raises:
            PolicyValidationError: If validation fails
        """
        if policy_type not in Policy.VALID_TYPES:
            raise PolicyValidationError([f"Invalid policy type: {policy_type}"])

        schema = POLICY_SCHEMAS.get(policy_type)
        if not schema:
            raise PolicyValidationError([f"No schema defined for policy type: {policy_type}"])

        errors = []

        # Check required fields
        for field in schema.get('required', []):
            if field not in configuration or configuration[field] is None:
                errors.append(f"Missing required field: {field}")

        # Validate values against allowed values
        for field, valid_values in schema.get('valid_values', {}).items():
            if field in configuration and configuration[field] not in valid_values:
                errors.append(f"Invalid value for {field}: {configuration[field]}. Must be one of: {valid_values}")

        # Validate numeric ranges
        if policy_type == 'index_maintenance':
            if 'fragmentation_threshold' in configuration:
                val = configuration['fragmentation_threshold']
                if not isinstance(val, (int, float)) or val < 0 or val > 100:
                    errors.append("fragmentation_threshold must be between 0 and 100")
            if 'rebuild_threshold' in configuration:
                val = configuration['rebuild_threshold']
                if not isinstance(val, (int, float)) or val < 0 or val > 100:
                    errors.append("rebuild_threshold must be between 0 and 100")

        if policy_type == 'backup' and 'retention_days' in configuration:
            val = configuration['retention_days']
            if not isinstance(val, int) or val < 1 or val > 365:
                errors.append("retention_days must be between 1 and 365")

        if policy_type == 'custom_script' and 'timeout_seconds' in configuration:
            val = configuration['timeout_seconds']
            if not isinstance(val, int) or val < 1 or val > 86400:
                errors.append("timeout_seconds must be between 1 and 86400 (24 hours)")

        if errors:
            raise PolicyValidationError(errors)

        # Apply defaults
        defaults = schema.get('defaults', {})
        result = {**defaults, **configuration}

        # Only include known fields
        known_fields = set(schema.get('required', [])) | set(schema.get('optional', []))
        return {k: v for k, v in result.items() if k in known_fields}

    def create_policy(
        self,
        name: str,
        policy_type: str,
        configuration: Dict[str, Any],
        description: Optional[str] = None,
        is_active: bool = True,
    ) -> Policy:
        """Create a new policy.

        Args:
            name: Policy name (must be unique within tenant)
            policy_type: Type of policy
            configuration: Policy configuration
            description: Optional description
            is_active: Whether policy is active (default True)

        Returns:
            Created policy

        Raises:
            PolicyValidationError: If validation fails
            IntegrityError: If name already exists
        """
        # Validate configuration
        normalized_config = self.validate_configuration(policy_type, configuration)

        # Create policy
        policy = Policy(
            name=name,
            type=policy_type,
            description=description,
            configuration=normalized_config,
            version=1,
            is_active=is_active,
        )

        try:
            self.session.add(policy)
            self.session.flush()  # Get the ID

            # Create initial version record
            version = PolicyVersion(
                policy_id=policy.id,
                version=1,
                configuration=normalized_config,
                description=description,
            )
            self.session.add(version)
            self.session.commit()

            return policy

        except IntegrityError:
            self.session.rollback()
            raise PolicyValidationError([f"Policy with name '{name}' already exists"])

    def get_policy(self, policy_id: UUID) -> Optional[Policy]:
        """Get a policy by ID.

        Args:
            policy_id: Policy UUID

        Returns:
            Policy or None if not found
        """
        return self.session.query(Policy).filter(
            Policy.id == policy_id,
            Policy.is_deleted == False
        ).first()

    def get_all_policies(
        self,
        policy_type: Optional[str] = None,
        is_active: Optional[bool] = None,
    ) -> List[Policy]:
        """Get all policies, optionally filtered.

        Args:
            policy_type: Filter by policy type
            is_active: Filter by active status

        Returns:
            List of policies
        """
        query = self.session.query(Policy).filter(Policy.is_deleted == False)

        if policy_type:
            query = query.filter(Policy.type == policy_type)

        if is_active is not None:
            query = query.filter(Policy.is_active == is_active)

        return query.order_by(Policy.name).all()

    def update_policy(
        self,
        policy_id: UUID,
        name: Optional[str] = None,
        description: Optional[str] = None,
        configuration: Optional[Dict[str, Any]] = None,
        is_active: Optional[bool] = None,
    ) -> Optional[Policy]:
        """Update a policy.

        If configuration changes, creates a new version (immutable versioning).

        Args:
            policy_id: Policy UUID
            name: New name (optional)
            description: New description (optional)
            configuration: New configuration (optional, triggers new version)
            is_active: New active status (optional)

        Returns:
            Updated policy or None if not found

        Raises:
            PolicyValidationError: If validation fails
        """
        policy = self.get_policy(policy_id)
        if not policy:
            return None

        # Track if we need a new version
        needs_new_version = False
        new_config = policy.configuration

        if name is not None and name != policy.name:
            # Check uniqueness
            existing = self.session.query(Policy).filter(
                Policy.name == name,
                Policy.id != policy_id,
                Policy.is_deleted == False
            ).first()
            if existing:
                raise PolicyValidationError([f"Policy with name '{name}' already exists"])
            policy.name = name

        if description is not None:
            policy.description = description

        if configuration is not None:
            # Validate and normalize
            new_config = self.validate_configuration(policy.type, configuration)
            if new_config != policy.configuration:
                needs_new_version = True
                policy.configuration = new_config

        if is_active is not None:
            policy.is_active = is_active

        if needs_new_version:
            policy.version += 1
            version = PolicyVersion(
                policy_id=policy.id,
                version=policy.version,
                configuration=new_config,
                description=policy.description,
            )
            self.session.add(version)

        self.session.commit()
        return policy

    def delete_policy(self, policy_id: UUID) -> bool:
        """Soft-delete a policy.

        Args:
            policy_id: Policy UUID

        Returns:
            True if deleted, False if not found
        """
        policy = self.get_policy(policy_id)
        if not policy:
            return False

        policy.is_deleted = True
        self.session.commit()
        return True

    def get_policy_versions(self, policy_id: UUID) -> List[PolicyVersion]:
        """Get version history for a policy.

        Args:
            policy_id: Policy UUID

        Returns:
            List of policy versions, newest first
        """
        return self.session.query(PolicyVersion).filter(
            PolicyVersion.policy_id == policy_id
        ).order_by(PolicyVersion.version.desc()).all()

    def get_policy_version(self, policy_id: UUID, version: int) -> Optional[PolicyVersion]:
        """Get a specific version of a policy.

        Args:
            policy_id: Policy UUID
            version: Version number

        Returns:
            Policy version or None if not found
        """
        return self.session.query(PolicyVersion).filter(
            PolicyVersion.policy_id == policy_id,
            PolicyVersion.version == version
        ).first()

    @staticmethod
    def get_schema(policy_type: str) -> Optional[Dict[str, Any]]:
        """Get the configuration schema for a policy type.

        Args:
            policy_type: Policy type

        Returns:
            Schema dictionary or None if type not found
        """
        return POLICY_SCHEMAS.get(policy_type)

    @staticmethod
    def get_all_schemas() -> Dict[str, Dict[str, Any]]:
        """Get all policy configuration schemas.

        Returns:
            Dictionary of policy type -> schema
        """
        return POLICY_SCHEMAS
