"""
Safety Planner for Stage C Planner

Implements comprehensive safety checks, rollback procedures, and risk mitigation.
Ensures safe execution with proper failure handling and recovery mechanisms.
"""

from typing import Dict, Any, List, Optional, Set
from enum import Enum

from ...schemas.decision_v1 import DecisionV1, RiskLevel as DecisionRiskLevel
from ...schemas.selection_v1 import SelectionV1, RiskLevel as SelectionRiskLevel
from ...schemas.plan_v1 import ExecutionStep, SafetyCheck, SafetyStage, FailureAction


class SafetyPlanner:
    """
    Creates comprehensive safety measures for execution plans.
    
    This class is responsible for:
    - Generating safety checks for different execution stages
    - Implementing risk mitigation strategies
    - Setting up failure handling mechanisms
    - Ensuring production safety compliance
    """
    
    def __init__(self):
        """Initialize the safety planner"""
        
        # Risk-based safety check templates
        self.risk_safety_checks = {
            DecisionRiskLevel.LOW: self._get_low_risk_checks,
            DecisionRiskLevel.MEDIUM: self._get_medium_risk_checks,
            DecisionRiskLevel.HIGH: self._get_high_risk_checks,
            DecisionRiskLevel.CRITICAL: self._get_critical_risk_checks
        }
        
        # Tool-specific safety checks
        self.tool_safety_checks = {
            "systemctl": self._get_systemctl_safety_checks,
            "file_manager": self._get_file_manager_safety_checks,
            "config_manager": self._get_config_manager_safety_checks,
            "docker": self._get_docker_safety_checks,
            "network_tools": self._get_network_tools_safety_checks,
            "journalctl": self._get_journalctl_safety_checks,
            "ps": self._get_ps_safety_checks,
            "info_display": self._get_info_display_safety_checks
        }
    
    def create_safety_plan(
        self, 
        steps: List[ExecutionStep], 
        decision: DecisionV1, 
        selection: SelectionV1
    ) -> List[SafetyCheck]:
        """
        Create comprehensive safety checks for execution plans.
        
        Args:
            steps: Execution steps to create safety measures for
            decision: Original decision context
            selection: Tool selection context
            
        Returns:
            List of safety checks
        """
        safety_checks = []
        
        # Add risk-based safety checks
        risk_checks = self._create_risk_based_checks(decision, selection)
        safety_checks.extend(risk_checks)
        
        # Add tool-specific safety checks
        for step in steps:
            tool_checks = self._create_tool_safety_checks(step, decision, selection)
            safety_checks.extend(tool_checks)
        
        # Add environment-specific safety checks
        env_checks = self._create_environment_checks(selection)
        safety_checks.extend(env_checks)
        
        # Add pre-execution validation checks
        validation_checks = self._create_validation_checks(steps, decision)
        safety_checks.extend(validation_checks)
        
        return safety_checks
    
    def _create_risk_based_checks(
        self, 
        decision: DecisionV1, 
        selection: SelectionV1
    ) -> List[SafetyCheck]:
        """Create safety checks based on risk assessment"""
        checks = []
        
        # Use decision risk level
        risk_level = decision.risk_level
        
        if risk_level in self.risk_safety_checks:
            risk_checks = self.risk_safety_checks[risk_level]()
            checks.extend(risk_checks)
        
        # Add selection-specific risk checks
        if selection.policy.requires_approval:
            checks.append(SafetyCheck(
                check="Manual approval obtained for high-risk operation",
                stage=SafetyStage.BEFORE,
                failure_action=FailureAction.ABORT
            ))
        
        if not selection.policy.parallel_execution:
            checks.append(SafetyCheck(
                check="Ensure sequential execution for safety-critical operations",
                stage=SafetyStage.BEFORE,
                failure_action=FailureAction.ABORT
            ))
        
        return checks
    
    def _create_tool_safety_checks(
        self, 
        step: ExecutionStep, 
        decision: DecisionV1, 
        selection: SelectionV1
    ) -> List[SafetyCheck]:
        """Create tool-specific safety checks"""
        tool_name = step.tool
        
        if tool_name in self.tool_safety_checks:
            return self.tool_safety_checks[tool_name](step, decision, selection)
        
        # Generic safety checks for unknown tools
        return [
            SafetyCheck(
                check=f"Verify {tool_name} tool is available and accessible",
                stage=SafetyStage.BEFORE,
                failure_action=FailureAction.ABORT
            ),
            SafetyCheck(
                check=f"Monitor {tool_name} execution for errors",
                stage=SafetyStage.DURING,
                failure_action=FailureAction.WARN
            )
        ]
    

    
    def _create_environment_checks(self, selection: SelectionV1) -> List[SafetyCheck]:
        """Create environment-specific safety checks"""
        checks = []
        
        # Production environment checks
        if selection.environment_requirements.get("production_safe", False):
            checks.extend([
                SafetyCheck(
                    check="Verify operation is approved for production environment",
                    stage=SafetyStage.BEFORE,
                    failure_action=FailureAction.ABORT
                ),
                SafetyCheck(
                    check="Confirm backup procedures are in place",
                    stage=SafetyStage.BEFORE,
                    failure_action=FailureAction.ABORT
                ),
                SafetyCheck(
                    check="Validate rollback procedures are tested and ready",
                    stage=SafetyStage.BEFORE,
                    failure_action=FailureAction.ABORT
                )
            ])
        
        # Resource requirement checks
        min_memory = selection.environment_requirements.get("min_memory_mb", 0)
        if min_memory > 0:
            checks.append(SafetyCheck(
                check=f"Verify system has at least {min_memory}MB available memory",
                stage=SafetyStage.BEFORE,
                failure_action=FailureAction.ABORT
            ))
        
        min_disk = selection.environment_requirements.get("min_disk_gb", 0)
        if min_disk > 0:
            checks.append(SafetyCheck(
                check=f"Verify system has at least {min_disk}GB available disk space",
                stage=SafetyStage.BEFORE,
                failure_action=FailureAction.ABORT
            ))
        
        return checks
    
    def _create_validation_checks(
        self, 
        steps: List[ExecutionStep], 
        decision: DecisionV1
    ) -> List[SafetyCheck]:
        """Create pre-execution validation checks"""
        checks = [
            SafetyCheck(
                check="Validate all required tools are available on the system",
                stage=SafetyStage.BEFORE,
                failure_action=FailureAction.ABORT
            ),
            SafetyCheck(
                check="Verify user has sufficient permissions for all operations",
                stage=SafetyStage.BEFORE,
                failure_action=FailureAction.ABORT
            ),
            SafetyCheck(
                check="Confirm system is in stable state before execution",
                stage=SafetyStage.BEFORE,
                failure_action=FailureAction.ABORT
            )
        ]
        
        # Add step-specific validation
        destructive_tools = {"systemctl", "file_manager", "config_manager", "docker"}
        has_destructive = any(step.tool in destructive_tools for step in steps)
        
        if has_destructive:
            checks.append(SafetyCheck(
                check="Create system checkpoint before destructive operations",
                stage=SafetyStage.BEFORE,
                failure_action=FailureAction.ABORT
            ))
        
        return checks
    
    # Risk-based safety check generators
    def _get_low_risk_checks(self) -> List[SafetyCheck]:
        """Safety checks for low-risk operations"""
        return [
            SafetyCheck(
                check="Basic system health check",
                stage=SafetyStage.BEFORE,
                failure_action=FailureAction.WARN
            ),
            SafetyCheck(
                check="Monitor operation completion",
                stage=SafetyStage.DURING,
                failure_action=FailureAction.WARN
            )
        ]
    
    def _get_medium_risk_checks(self) -> List[SafetyCheck]:
        """Safety checks for medium-risk operations"""
        return [
            SafetyCheck(
                check="Comprehensive system health validation",
                stage=SafetyStage.BEFORE,
                failure_action=FailureAction.ABORT
            ),
            SafetyCheck(
                check="Verify backup systems are operational",
                stage=SafetyStage.BEFORE,
                failure_action=FailureAction.WARN
            ),
            SafetyCheck(
                check="Monitor system resources during execution",
                stage=SafetyStage.DURING,
                failure_action=FailureAction.WARN
            ),
            SafetyCheck(
                check="Validate operation completed successfully",
                stage=SafetyStage.AFTER,
                failure_action=FailureAction.WARN
            )
        ]
    
    def _get_high_risk_checks(self) -> List[SafetyCheck]:
        """Safety checks for high-risk operations"""
        return [
            SafetyCheck(
                check="Complete system state backup created",
                stage=SafetyStage.BEFORE,
                failure_action=FailureAction.ABORT
            ),
            SafetyCheck(
                check="Emergency rollback procedures validated",
                stage=SafetyStage.BEFORE,
                failure_action=FailureAction.ABORT
            ),
            SafetyCheck(
                check="Real-time monitoring systems active",
                stage=SafetyStage.DURING,
                failure_action=FailureAction.ABORT
            ),
            SafetyCheck(
                check="System integrity verification completed",
                stage=SafetyStage.AFTER,
                failure_action=FailureAction.ABORT
            )
        ]
    
    def _get_critical_risk_checks(self) -> List[SafetyCheck]:
        """Safety checks for critical-risk operations"""
        return [
            SafetyCheck(
                check="Full system backup and disaster recovery plan activated",
                stage=SafetyStage.BEFORE,
                failure_action=FailureAction.ABORT
            ),
            SafetyCheck(
                check="Secondary approval from senior administrator obtained",
                stage=SafetyStage.BEFORE,
                failure_action=FailureAction.ABORT
            ),
            SafetyCheck(
                check="Maintenance window scheduled and stakeholders notified",
                stage=SafetyStage.BEFORE,
                failure_action=FailureAction.ABORT
            ),
            SafetyCheck(
                check="Real-time system monitoring with automatic rollback triggers",
                stage=SafetyStage.DURING,
                failure_action=FailureAction.ABORT
            ),
            SafetyCheck(
                check="Complete system validation and performance baseline comparison",
                stage=SafetyStage.AFTER,
                failure_action=FailureAction.ABORT
            )
        ]
    
    # Tool-specific safety check generators
    def _get_systemctl_safety_checks(
        self, 
        step: ExecutionStep, 
        decision: DecisionV1, 
        selection: SelectionV1
    ) -> List[SafetyCheck]:
        """Safety checks for systemctl operations"""
        checks = [
            SafetyCheck(
                check="Verify systemd service exists and is manageable",
                stage=SafetyStage.BEFORE,
                failure_action=FailureAction.ABORT
            )
        ]
        
        operation = step.inputs.get("action", "status")
        if operation in ["restart", "stop", "start"]:
            checks.extend([
                SafetyCheck(
                    check="Check service dependencies before modification",
                    stage=SafetyStage.BEFORE,
                    failure_action=FailureAction.WARN
                ),
                SafetyCheck(
                    check="Monitor service status during operation",
                    stage=SafetyStage.DURING,
                    failure_action=FailureAction.WARN
                ),
                SafetyCheck(
                    check="Verify service reached expected state",
                    stage=SafetyStage.AFTER,
                    failure_action=FailureAction.WARN
                )
            ])
        
        return checks
    
    def _get_file_manager_safety_checks(
        self, 
        step: ExecutionStep, 
        decision: DecisionV1, 
        selection: SelectionV1
    ) -> List[SafetyCheck]:
        """Safety checks for file manager operations"""
        checks = [
            SafetyCheck(
                check="Verify file path exists and is accessible",
                stage=SafetyStage.BEFORE,
                failure_action=FailureAction.ABORT
            ),
            SafetyCheck(
                check="Check file permissions and ownership",
                stage=SafetyStage.BEFORE,
                failure_action=FailureAction.ABORT
            )
        ]
        
        operation = step.inputs.get("operation", "read")
        if operation in ["write", "backup", "restore"]:
            checks.extend([
                SafetyCheck(
                    check="Create backup before file modification",
                    stage=SafetyStage.BEFORE,
                    failure_action=FailureAction.ABORT
                ),
                SafetyCheck(
                    check="Verify sufficient disk space for operation",
                    stage=SafetyStage.BEFORE,
                    failure_action=FailureAction.ABORT
                ),
                SafetyCheck(
                    check="Validate file integrity after modification",
                    stage=SafetyStage.AFTER,
                    failure_action=FailureAction.WARN
                )
            ])
        
        return checks
    
    def _get_config_manager_safety_checks(
        self, 
        step: ExecutionStep, 
        decision: DecisionV1, 
        selection: SelectionV1
    ) -> List[SafetyCheck]:
        """Safety checks for config manager operations"""
        return [
            SafetyCheck(
                check="Validate configuration file syntax before modification",
                stage=SafetyStage.BEFORE,
                failure_action=FailureAction.ABORT
            ),
            SafetyCheck(
                check="Create configuration backup with timestamp",
                stage=SafetyStage.BEFORE,
                failure_action=FailureAction.ABORT
            ),
            SafetyCheck(
                check="Test configuration validity after changes",
                stage=SafetyStage.AFTER,
                failure_action=FailureAction.ABORT
            )
        ]
    
    def _get_docker_safety_checks(
        self, 
        step: ExecutionStep, 
        decision: DecisionV1, 
        selection: SelectionV1
    ) -> List[SafetyCheck]:
        """Safety checks for Docker operations"""
        checks = [
            SafetyCheck(
                check="Verify Docker daemon is running and accessible",
                stage=SafetyStage.BEFORE,
                failure_action=FailureAction.ABORT
            )
        ]
        
        operation = step.inputs.get("operation", "ps")
        if operation in ["restart", "stop", "start"]:
            checks.extend([
                SafetyCheck(
                    check="Check container dependencies and linked services",
                    stage=SafetyStage.BEFORE,
                    failure_action=FailureAction.WARN
                ),
                SafetyCheck(
                    check="Monitor container health during operation",
                    stage=SafetyStage.DURING,
                    failure_action=FailureAction.WARN
                )
            ])
        
        return checks
    
    def _get_network_tools_safety_checks(
        self, 
        step: ExecutionStep, 
        decision: DecisionV1, 
        selection: SelectionV1
    ) -> List[SafetyCheck]:
        """Safety checks for network tools"""
        return [
            SafetyCheck(
                check="Verify network interface is available",
                stage=SafetyStage.BEFORE,
                failure_action=FailureAction.WARN
            ),
            SafetyCheck(
                check="Check network connectivity before testing",
                stage=SafetyStage.BEFORE,
                failure_action=FailureAction.WARN
            )
        ]
    
    def _get_journalctl_safety_checks(
        self, 
        step: ExecutionStep, 
        decision: DecisionV1, 
        selection: SelectionV1
    ) -> List[SafetyCheck]:
        """Safety checks for journalctl operations"""
        return [
            SafetyCheck(
                check="Verify systemd journal is accessible",
                stage=SafetyStage.BEFORE,
                failure_action=FailureAction.WARN
            ),
            SafetyCheck(
                check="Check log rotation and disk space",
                stage=SafetyStage.BEFORE,
                failure_action=FailureAction.WARN
            )
        ]
    
    def _get_ps_safety_checks(
        self, 
        step: ExecutionStep, 
        decision: DecisionV1, 
        selection: SelectionV1
    ) -> List[SafetyCheck]:
        """Safety checks for ps operations"""
        return [
            SafetyCheck(
                check="Verify ps command is available",
                stage=SafetyStage.BEFORE,
                failure_action=FailureAction.WARN
            )
        ]
    
    def _get_info_display_safety_checks(
        self, 
        step: ExecutionStep, 
        decision: DecisionV1, 
        selection: SelectionV1
    ) -> List[SafetyCheck]:
        """Safety checks for info display operations"""
        return [
            SafetyCheck(
                check="Verify system information sources are accessible",
                stage=SafetyStage.BEFORE,
                failure_action=FailureAction.WARN
            )
        ]
