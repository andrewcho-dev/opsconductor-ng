"""
Policy Enforcer - Phase 2 Module 3/3

Enforces hard constraints and policies on tool candidates.
These are NEVER bypassable by LLM - they are security/compliance boundaries.

Policy Types:
1. Hard Constraints: Must be satisfied (filter out violators)
   - max_cost limits
   - production_safe flag
   - required permissions
   - environment restrictions

2. Soft Constraints: Require approval but don't filter
   - requires_approval flag
   - elevated permissions
   - background execution requirements

Design Principles:
1. Security first (hard constraints are absolute)
2. Explainable (clear reasons for filtering)
3. Auditable (log all policy decisions)
4. Fail-safe (default to restrictive)
"""

from typing import Dict, List, Optional, Any, Set
from dataclasses import dataclass
from enum import Enum
import logging

from pipeline.stages.stage_b.safe_math_eval import safe_eval

logger = logging.getLogger(__name__)


class PolicyViolationType(Enum):
    """Types of policy violations"""
    COST_EXCEEDED = "cost_exceeded"
    NOT_PRODUCTION_SAFE = "not_production_safe"
    MISSING_PERMISSION = "missing_permission"
    ENVIRONMENT_MISMATCH = "environment_mismatch"
    BACKGROUND_REQUIRED = "background_required"
    REQUIRES_APPROVAL = "requires_approval"


@dataclass
class PolicyViolation:
    """Details of a policy violation"""
    violation_type: PolicyViolationType
    severity: str  # "hard" (filter) or "soft" (flag)
    message: str
    details: Dict[str, Any]


@dataclass
class PolicyConfig:
    """Configuration for policy enforcement"""
    # Cost limits
    max_cost: Optional[float] = None  # Maximum allowed cost (None = no limit)
    
    # Environment
    environment: str = "production"  # production, staging, development
    
    # Permissions
    available_permissions: Set[str] = None  # Available permissions (None = all)
    
    # Safety
    require_production_safe: bool = True  # Require production_safe=true
    
    # Approval
    require_approval_for_elevated: bool = True  # Flag elevated permissions
    
    def __post_init__(self):
        """Initialize default values"""
        if self.available_permissions is None:
            self.available_permissions = {"read", "write", "execute", "admin"}


@dataclass
class PolicyResult:
    """Result of policy enforcement"""
    allowed: bool  # True if candidate passes all hard constraints
    violations: List[PolicyViolation]  # All violations (hard + soft)
    requires_approval: bool  # True if soft constraints require approval
    filtered_reason: Optional[str] = None  # Reason if filtered (hard constraint)


class PolicyEnforcer:
    """
    Enforces policies on tool candidates.
    
    Hard constraints filter out candidates.
    Soft constraints flag candidates for approval.
    
    Usage:
        enforcer = PolicyEnforcer(PolicyConfig(
            max_cost=1.0,
            environment="production",
            require_production_safe=True
        ))
        
        result = enforcer.enforce_policies(candidate)
        if result.allowed:
            if result.requires_approval:
                # Flag for approval
                pass
            else:
                # Safe to execute
                pass
        else:
            # Filtered out
            logger.warning(f"Filtered: {result.filtered_reason}")
    """
    
    def __init__(self, config: Optional[PolicyConfig] = None):
        """
        Initialize policy enforcer.
        
        Args:
            config: Policy configuration (uses defaults if not provided)
        """
        self.config = config or PolicyConfig()
    
    def enforce_policies(self, candidate: Dict[str, Any]) -> PolicyResult:
        """
        Enforce all policies on a candidate.
        
        Args:
            candidate: Tool candidate with profile data
            
        Returns:
            PolicyResult with enforcement decision
            
        Example:
            >>> enforcer = PolicyEnforcer(PolicyConfig(max_cost=1.0))
            >>> candidate = {
            ...     'tool_name': 'expensive_tool',
            ...     'pattern': 'default',
            ...     'profile': {
            ...         'cost': 2.0,
            ...         'production_safe': True,
            ...         'required_permissions': ['read']
            ...     }
            ... }
            >>> result = enforcer.enforce_policies(candidate)
            >>> result.allowed  # False (cost exceeded)
        """
        violations = []
        
        profile = candidate.get('profile', {})
        
        # Check hard constraints
        cost_violation = self._check_cost_limit(profile)
        if cost_violation:
            violations.append(cost_violation)
        
        production_violation = self._check_production_safe(profile)
        if production_violation:
            violations.append(production_violation)
        
        permission_violation = self._check_permissions(profile)
        if permission_violation:
            violations.append(permission_violation)
        
        environment_violation = self._check_environment(profile)
        if environment_violation:
            violations.append(environment_violation)
        
        # Check soft constraints
        background_violation = self._check_background_required(candidate)
        if background_violation:
            violations.append(background_violation)
        
        approval_violation = self._check_requires_approval(profile)
        if approval_violation:
            violations.append(approval_violation)
        
        # Determine if allowed (no hard constraint violations)
        hard_violations = [v for v in violations if v.severity == "hard"]
        allowed = len(hard_violations) == 0
        
        # Determine if requires approval (any soft constraint violations)
        soft_violations = [v for v in violations if v.severity == "soft"]
        requires_approval = len(soft_violations) > 0
        
        # Generate filtered reason if not allowed
        filtered_reason = None
        if not allowed:
            filtered_reason = "; ".join([v.message for v in hard_violations])
        
        return PolicyResult(
            allowed=allowed,
            violations=violations,
            requires_approval=requires_approval,
            filtered_reason=filtered_reason
        )
    
    def filter_candidates(self, candidates: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Filter candidates by policies (remove hard constraint violators).
        
        Args:
            candidates: List of tool candidates
            
        Returns:
            Filtered list of candidates (only those passing hard constraints)
            
        Example:
            >>> enforcer = PolicyEnforcer(PolicyConfig(max_cost=1.0))
            >>> candidates = [
            ...     {'tool_name': 'cheap', 'profile': {'cost': 0.5}},
            ...     {'tool_name': 'expensive', 'profile': {'cost': 2.0}}
            ... ]
            >>> filtered = enforcer.filter_candidates(candidates)
            >>> len(filtered)  # 1 (only 'cheap' passes)
        """
        filtered = []
        
        for candidate in candidates:
            result = self.enforce_policies(candidate)
            
            if result.allowed:
                # Add policy result to candidate
                candidate['policy_result'] = result
                filtered.append(candidate)
            else:
                # Log filtering
                logger.info(
                    f"Filtered candidate {candidate.get('tool_name')} "
                    f"({candidate.get('pattern')}): {result.filtered_reason}"
                )
        
        return filtered
    
    def _check_cost_limit(self, profile: Dict[str, Any]) -> Optional[PolicyViolation]:
        """Check if cost exceeds limit (hard constraint)"""
        if self.config.max_cost is None:
            return None  # No limit
        
        cost = profile.get('cost', 0.0)
        
        if cost > self.config.max_cost:
            return PolicyViolation(
                violation_type=PolicyViolationType.COST_EXCEEDED,
                severity="hard",
                message=f"Cost ${cost:.2f} exceeds limit ${self.config.max_cost:.2f}",
                details={'cost': cost, 'limit': self.config.max_cost}
            )
        
        return None
    
    def _check_production_safe(self, profile: Dict[str, Any]) -> Optional[PolicyViolation]:
        """Check if production_safe flag is set (hard constraint in production)"""
        if not self.config.require_production_safe:
            return None  # Not required
        
        if self.config.environment != "production":
            return None  # Only enforce in production
        
        production_safe = profile.get('production_safe', False)
        
        if not production_safe:
            return PolicyViolation(
                violation_type=PolicyViolationType.NOT_PRODUCTION_SAFE,
                severity="hard",
                message="Tool not marked as production-safe",
                details={'production_safe': production_safe}
            )
        
        return None
    
    def _check_permissions(self, profile: Dict[str, Any]) -> Optional[PolicyViolation]:
        """Check if required permissions are available (hard constraint)"""
        required_permissions = set(profile.get('required_permissions', []))
        
        if not required_permissions:
            return None  # No permissions required
        
        # Check if all required permissions are available
        missing_permissions = required_permissions - self.config.available_permissions
        
        if missing_permissions:
            return PolicyViolation(
                violation_type=PolicyViolationType.MISSING_PERMISSION,
                severity="hard",
                message=f"Missing required permissions: {', '.join(missing_permissions)}",
                details={
                    'required': list(required_permissions),
                    'available': list(self.config.available_permissions),
                    'missing': list(missing_permissions)
                }
            )
        
        return None
    
    def _check_environment(self, profile: Dict[str, Any]) -> Optional[PolicyViolation]:
        """Check if tool is allowed in current environment (hard constraint)"""
        allowed_environments = profile.get('allowed_environments', None)
        
        if allowed_environments is None:
            return None  # No restrictions
        
        if self.config.environment not in allowed_environments:
            return PolicyViolation(
                violation_type=PolicyViolationType.ENVIRONMENT_MISMATCH,
                severity="hard",
                message=f"Tool not allowed in {self.config.environment} environment",
                details={
                    'current_environment': self.config.environment,
                    'allowed_environments': allowed_environments
                }
            )
        
        return None
    
    def _check_background_required(self, candidate: Dict[str, Any]) -> Optional[PolicyViolation]:
        """Check if background execution is required (soft constraint)"""
        profile = candidate.get('profile', {})
        context = candidate.get('context', {})
        
        # Check requires_background_if expression
        requires_background_if = profile.get('requires_background_if', None)
        
        if requires_background_if is None:
            return None  # No background requirement
        
        # Evaluate expression
        try:
            requires_background = safe_eval(requires_background_if, context)
            
            if requires_background:
                return PolicyViolation(
                    violation_type=PolicyViolationType.BACKGROUND_REQUIRED,
                    severity="soft",
                    message="Tool requires background execution",
                    details={
                        'expression': requires_background_if,
                        'context': context
                    }
                )
        except Exception as e:
            logger.warning(f"Failed to evaluate requires_background_if: {e}")
        
        return None
    
    def _check_requires_approval(self, profile: Dict[str, Any]) -> Optional[PolicyViolation]:
        """Check if tool requires approval (soft constraint)"""
        requires_approval = profile.get('requires_approval', False)
        
        if requires_approval:
            return PolicyViolation(
                violation_type=PolicyViolationType.REQUIRES_APPROVAL,
                severity="soft",
                message="Tool requires approval before execution",
                details={'requires_approval': True}
            )
        
        # Check for elevated permissions
        if self.config.require_approval_for_elevated:
            required_permissions = set(profile.get('required_permissions', []))
            elevated_permissions = {'admin', 'root', 'sudo'}
            
            if required_permissions & elevated_permissions:
                return PolicyViolation(
                    violation_type=PolicyViolationType.REQUIRES_APPROVAL,
                    severity="soft",
                    message=f"Tool requires elevated permissions: {', '.join(required_permissions & elevated_permissions)}",
                    details={
                        'required_permissions': list(required_permissions),
                        'elevated_permissions': list(required_permissions & elevated_permissions)
                    }
                )
        
        return None


# Convenience function for quick policy enforcement
def enforce_policies(candidate: Dict[str, Any], 
                    config: Optional[PolicyConfig] = None) -> PolicyResult:
    """
    Convenience function for policy enforcement.
    
    Args:
        candidate: Tool candidate
        config: Optional policy configuration
        
    Returns:
        PolicyResult
        
    Example:
        >>> from pipeline.stages.stage_b.policy_enforcer import enforce_policies, PolicyConfig
        >>> result = enforce_policies(candidate, PolicyConfig(max_cost=1.0))
    """
    enforcer = PolicyEnforcer(config)
    return enforcer.enforce_policies(candidate)