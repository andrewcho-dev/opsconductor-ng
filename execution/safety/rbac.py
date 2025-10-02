"""
RBAC Validator - Safety Feature #3

Worker-side RBAC validation to prevent privilege escalation:
- Validates actor permissions before execution
- Checks resource-level permissions (asset, action, environment)
- Prevents unauthorized operations even if API gateway is bypassed
- Defense-in-depth: API gateway + worker-side validation

Implementation:
- Permission model: (tenant, actor, resource_type, resource_id, action)
- Environment-based restrictions (e.g., prod requires higher privileges)
- Action-level permissions (read, write, execute, delete)
- Audit trail for all permission checks

Usage:
    validator = RBACValidator(repository)
    await validator.validate_execution(execution_id, actor_id, tenant_id)
"""

import logging
from typing import List, Dict, Any, Optional
from enum import Enum

from execution.models import ExecutionModel
from execution.repository import ExecutionRepository

logger = logging.getLogger(__name__)


class Permission(str, Enum):
    """Permission types"""
    READ = "read"
    WRITE = "write"
    EXECUTE = "execute"
    DELETE = "delete"
    ADMIN = "admin"


class Environment(str, Enum):
    """Environment types"""
    DEV = "dev"
    STAGING = "staging"
    PROD = "prod"


class RBACValidationError(Exception):
    """Raised when RBAC validation fails"""
    pass


class RBACValidator:
    """
    RBAC validator for worker-side permission checks.
    
    This is Safety Feature #3 and is critical for production deployment.
    """
    
    def __init__(
        self,
        repository: ExecutionRepository,
        strict_mode: bool = True,
    ):
        """
        Initialize RBAC validator.
        
        Args:
            repository: Execution repository for database access
            strict_mode: If True, deny by default; if False, allow by default (default: True)
        """
        self.repository = repository
        self.strict_mode = strict_mode
    
    async def validate_execution(
        self,
        execution: ExecutionModel,
        actor_id: str,
        tenant_id: str,
    ) -> None:
        """
        Validate actor has permission to execute the plan.
        
        This is the main entry point for RBAC validation.
        
        Args:
            execution: Execution model
            actor_id: Actor ID (user who initiated execution)
            tenant_id: Tenant ID
        
        Raises:
            RBACValidationError: If actor does not have permission
        """
        logger.info(
            f"Validating RBAC for execution: execution_id={execution.execution_id}, "
            f"actor_id={actor_id}, tenant_id={tenant_id}"
        )
        
        # Extract targets from plan
        targets = self._extract_targets_from_plan(execution.plan_snapshot)
        
        # Validate each target
        for target in targets:
            await self._validate_target_permission(
                actor_id=actor_id,
                tenant_id=tenant_id,
                target=target,
                execution_id=execution.execution_id,
            )
        
        logger.info(
            f"RBAC validation passed: execution_id={execution.execution_id}, "
            f"targets={len(targets)}"
        )
    
    async def validate_step(
        self,
        step_data: Dict[str, Any],
        actor_id: str,
        tenant_id: str,
        execution_id: str,
    ) -> None:
        """
        Validate actor has permission to execute a specific step.
        
        Args:
            step_data: Step data from plan
            actor_id: Actor ID
            tenant_id: Tenant ID
            execution_id: Execution ID
        
        Raises:
            RBACValidationError: If actor does not have permission
        """
        logger.debug(
            f"Validating RBAC for step: execution_id={execution_id}, "
            f"actor_id={actor_id}"
        )
        
        # Extract target from step
        target = self._extract_target_from_step(step_data)
        
        # Validate target permission
        await self._validate_target_permission(
            actor_id=actor_id,
            tenant_id=tenant_id,
            target=target,
            execution_id=execution_id,
        )
    
    async def _validate_target_permission(
        self,
        actor_id: str,
        tenant_id: str,
        target: Dict[str, Any],
        execution_id: str,
    ) -> None:
        """
        Validate actor has permission for a specific target.
        
        Args:
            actor_id: Actor ID
            tenant_id: Tenant ID
            target: Target data (asset_id, action, environment)
            execution_id: Execution ID
        
        Raises:
            RBACValidationError: If actor does not have permission
        """
        asset_id = target.get("asset_id")
        action = target.get("action")
        environment = target.get("environment", "dev")
        
        logger.debug(
            f"Checking permission: actor_id={actor_id}, asset_id={asset_id}, "
            f"action={action}, environment={environment}"
        )
        
        # Check if actor has permission
        has_permission = await self._check_permission(
            actor_id=actor_id,
            tenant_id=tenant_id,
            asset_id=asset_id,
            action=action,
            environment=environment,
        )
        
        if not has_permission:
            error_msg = (
                f"RBAC validation failed: actor {actor_id} does not have permission "
                f"to execute {action} on asset {asset_id} in {environment} environment"
            )
            logger.error(error_msg)
            
            # Add event to audit trail
            self.repository.create_execution_event(
                execution_id=execution_id,
                event_type="rbac_validation_failed",
                event_data={
                    "actor_id": actor_id,
                    "asset_id": asset_id,
                    "action": action,
                    "environment": environment,
                    "reason": "Insufficient permissions",
                },
            )
            
            raise RBACValidationError(error_msg)
        
        logger.debug(
            f"Permission granted: actor_id={actor_id}, asset_id={asset_id}, "
            f"action={action}"
        )
    
    async def _check_permission(
        self,
        actor_id: str,
        tenant_id: str,
        asset_id: str,
        action: str,
        environment: str,
    ) -> bool:
        """
        Check if actor has permission.
        
        This is a placeholder implementation. In production, this should:
        1. Query permissions from database or cache
        2. Check role-based permissions
        3. Check resource-level permissions
        4. Apply environment-based restrictions
        
        Args:
            actor_id: Actor ID
            tenant_id: Tenant ID
            asset_id: Asset ID
            action: Action to perform
            environment: Environment (dev/staging/prod)
        
        Returns:
            True if actor has permission, False otherwise
        """
        # TODO: Implement actual permission check
        # For now, we'll use a simple placeholder logic
        
        # In strict mode, deny by default
        if self.strict_mode:
            # Check if actor is admin
            is_admin = await self._is_admin(actor_id, tenant_id)
            if is_admin:
                return True
            
            # Check if actor has specific permission
            has_permission = await self._has_specific_permission(
                actor_id=actor_id,
                tenant_id=tenant_id,
                asset_id=asset_id,
                action=action,
                environment=environment,
            )
            return has_permission
        
        # In non-strict mode, allow by default (for development)
        return True
    
    async def _is_admin(self, actor_id: str, tenant_id: str) -> bool:
        """
        Check if actor is admin.
        
        Args:
            actor_id: Actor ID
            tenant_id: Tenant ID
        
        Returns:
            True if actor is admin, False otherwise
        """
        # TODO: Implement actual admin check
        # This should query the user/role database
        return False
    
    async def _has_specific_permission(
        self,
        actor_id: str,
        tenant_id: str,
        asset_id: str,
        action: str,
        environment: str,
    ) -> bool:
        """
        Check if actor has specific permission.
        
        Args:
            actor_id: Actor ID
            tenant_id: Tenant ID
            asset_id: Asset ID
            action: Action to perform
            environment: Environment
        
        Returns:
            True if actor has permission, False otherwise
        """
        # TODO: Implement actual permission check
        # This should query the permissions database
        return False
    
    def _extract_targets_from_plan(self, plan: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Extract targets from plan.
        
        Args:
            plan: Plan snapshot
        
        Returns:
            List of targets
        """
        targets = []
        
        # Extract targets from plan structure
        # This depends on the plan format
        if "steps" in plan:
            for step in plan["steps"]:
                target = self._extract_target_from_step(step)
                if target:
                    targets.append(target)
        
        return targets
    
    def _extract_target_from_step(self, step: Dict[str, Any]) -> Dict[str, Any]:
        """
        Extract target from step.
        
        Args:
            step: Step data
        
        Returns:
            Target data
        """
        # Extract target information from step
        # This depends on the step format
        return {
            "asset_id": step.get("asset_id"),
            "action": step.get("action"),
            "environment": step.get("environment", "dev"),
        }
    
    async def get_actor_permissions(
        self,
        actor_id: str,
        tenant_id: str,
    ) -> List[Dict[str, Any]]:
        """
        Get all permissions for an actor.
        
        This is useful for debugging and auditing.
        
        Args:
            actor_id: Actor ID
            tenant_id: Tenant ID
        
        Returns:
            List of permissions
        """
        # TODO: Implement actual permission query
        # This should return all permissions for the actor
        return []