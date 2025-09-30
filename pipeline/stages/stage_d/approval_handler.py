"""
Approval Handler
Processes approval requirements and workflows

This component handles the identification and processing of approval points
in execution plans, determining required approvers and approval workflows.
"""

import logging
from typing import Dict, Any, List, Optional
from datetime import datetime

from pipeline.schemas.plan_v1 import ExecutionMetadata
from pipeline.schemas.response_v1 import ApprovalPoint

logger = logging.getLogger(__name__)

class ApprovalHandler:
    """
    Approval Handler for Stage D
    
    Processes approval requirements from execution plans and determines
    appropriate approval workflows and required approvers.
    """
    
    def __init__(self):
        """Initialize approval handler"""
        
        # Define approval role mappings based on risk levels and operations
        self.approval_roles = {
            "low": "team_lead",
            "medium": "operations_manager", 
            "high": "operations_manager",
            "critical": "security_officer"
        }
        
        # Define operations that require specific approvers
        self.operation_approvers = {
            "production_deployment": "operations_manager",
            "security_change": "security_officer",
            "database_modification": "database_administrator",
            "network_change": "network_administrator",
            "service_restart": "operations_manager",
            "configuration_change": "operations_manager",
            "user_access_modification": "security_officer"
        }
        
        logger.info("Approval Handler initialized")
    
    def process_approval_points(
        self,
        approval_metadata: List[Dict[str, Any]]
    ) -> List[ApprovalPoint]:
        """
        Process approval points from execution metadata
        
        Args:
            approval_metadata: List of approval point metadata from execution plan
            
        Returns:
            List[ApprovalPoint]: Processed approval points with required approvers
        """
        
        approval_points = []
        
        for metadata in approval_metadata:
            try:
                # Handle both string step IDs and dictionary metadata
                if isinstance(metadata, str):
                    # Simple step ID - create basic approval point
                    approval_point = ApprovalPoint(
                        step_id=metadata,
                        reason="Approval required for this step",
                        risk_level="medium",
                        approver_role=self._determine_approver_role("medium", "general")
                    )
                else:
                    # Dictionary metadata - extract detailed information
                    step_id = metadata.get("step_id", "unknown")
                    reason = metadata.get("reason", "High-risk operation requires approval")
                    risk_level = metadata.get("risk_level", "medium")
                    operation_type = metadata.get("operation_type", "general")
                    
                    # Determine required approver
                    approver_role = self._determine_approver_role(risk_level, operation_type)
                    
                    # Create approval point
                    approval_point = ApprovalPoint(
                        step_id=step_id,
                        reason=reason,
                        risk_level=risk_level,
                        approver_role=approver_role
                    )
                
                approval_points.append(approval_point)
                
                logger.debug(f"Processed approval point for {approval_point.step_id}: {approval_point.approver_role} required")
                
            except Exception as e:
                logger.error(f"Failed to process approval point {metadata}: {e}")
                # Create fallback approval point
                fallback_step_id = metadata if isinstance(metadata, str) else metadata.get("step_id", "unknown")
                approval_points.append(ApprovalPoint(
                    step_id=fallback_step_id,
                    reason="Approval required due to processing error",
                    risk_level="high",
                    approver_role="operations_manager"
                ))
        
        logger.info(f"Processed {len(approval_points)} approval points")
        return approval_points
    
    def _determine_approver_role(self, risk_level: str, operation_type: str) -> str:
        """
        Determine the required approver role based on risk level and operation type
        
        Args:
            risk_level: Risk level of the operation (low, medium, high, critical)
            operation_type: Type of operation being performed
            
        Returns:
            str: Required approver role
        """
        
        # Check for operation-specific approvers first
        if operation_type in self.operation_approvers:
            return self.operation_approvers[operation_type]
        
        # Fall back to risk-level based approvers
        return self.approval_roles.get(risk_level, "operations_manager")
    
    def validate_approval_workflow(
        self,
        approval_points: List[ApprovalPoint]
    ) -> Dict[str, Any]:
        """
        Validate the approval workflow and identify any issues
        
        Args:
            approval_points: List of approval points to validate
            
        Returns:
            Dict containing validation results
        """
        
        validation_result = {
            "valid": True,
            "issues": [],
            "warnings": [],
            "approval_summary": {}
        }
        
        try:
            # Group approvals by role
            approvals_by_role = {}
            for ap in approval_points:
                role = ap.approver_role
                if role not in approvals_by_role:
                    approvals_by_role[role] = []
                approvals_by_role[role].append(ap)
            
            validation_result["approval_summary"] = {
                role: len(points) for role, points in approvals_by_role.items()
            }
            
            # Check for potential issues
            
            # Too many approval points
            if len(approval_points) > 5:
                validation_result["warnings"].append(
                    f"High number of approval points ({len(approval_points)}) may slow execution"
                )
            
            # Critical operations without security officer approval
            critical_points = [ap for ap in approval_points if ap.risk_level == "critical"]
            if critical_points and not any(ap.approver_role == "security_officer" for ap in critical_points):
                validation_result["warnings"].append(
                    "Critical operations detected but no security officer approval required"
                )
            
            # Multiple roles required
            if len(approvals_by_role) > 3:
                validation_result["warnings"].append(
                    f"Multiple approver roles required ({len(approvals_by_role)}), coordination may be complex"
                )
            
            logger.info(f"Approval workflow validation completed: {len(approval_points)} points, {len(approvals_by_role)} roles")
            
        except Exception as e:
            logger.error(f"Approval workflow validation failed: {e}")
            validation_result["valid"] = False
            validation_result["issues"].append(f"Validation error: {e}")
        
        return validation_result
    
    def get_approval_summary(
        self,
        approval_points: List[ApprovalPoint]
    ) -> Dict[str, Any]:
        """
        Generate a summary of approval requirements
        
        Args:
            approval_points: List of approval points
            
        Returns:
            Dict containing approval summary
        """
        
        if not approval_points:
            return {
                "total_approvals": 0,
                "required_roles": [],
                "risk_breakdown": {},
                "estimated_approval_time": 0
            }
        
        # Group by risk level
        risk_breakdown = {}
        for ap in approval_points:
            risk = ap.risk_level
            if risk not in risk_breakdown:
                risk_breakdown[risk] = 0
            risk_breakdown[risk] += 1
        
        # Get unique required roles
        required_roles = list(set(ap.approver_role for ap in approval_points))
        
        # Estimate approval time based on complexity
        base_time = 300  # 5 minutes base
        role_multiplier = len(required_roles) * 180  # 3 minutes per additional role
        risk_multiplier = risk_breakdown.get("critical", 0) * 600  # 10 minutes per critical
        
        estimated_time = base_time + role_multiplier + risk_multiplier
        
        return {
            "total_approvals": len(approval_points),
            "required_roles": required_roles,
            "risk_breakdown": risk_breakdown,
            "estimated_approval_time": estimated_time,
            "approval_complexity": self._assess_approval_complexity(approval_points)
        }
    
    def _assess_approval_complexity(self, approval_points: List[ApprovalPoint]) -> str:
        """Assess the complexity of the approval workflow"""
        
        if not approval_points:
            return "none"
        
        unique_roles = len(set(ap.approver_role for ap in approval_points))
        critical_count = sum(1 for ap in approval_points if ap.risk_level == "critical")
        
        if critical_count > 0 or unique_roles > 2:
            return "high"
        elif len(approval_points) > 2 or unique_roles > 1:
            return "medium"
        else:
            return "low"
    
    def format_approval_requirements(
        self,
        approval_points: List[ApprovalPoint]
    ) -> List[str]:
        """
        Format approval requirements into human-readable strings
        
        Args:
            approval_points: List of approval points
            
        Returns:
            List of formatted requirement strings
        """
        
        requirements = []
        
        # Group by approver role
        by_role = {}
        for ap in approval_points:
            role = ap.approver_role
            if role not in by_role:
                by_role[role] = []
            by_role[role].append(ap)
        
        # Format requirements by role
        for role, points in by_role.items():
            if len(points) == 1:
                requirements.append(f"{role.replace('_', ' ').title()} approval required for {points[0].reason.lower()}")
            else:
                requirements.append(f"{role.replace('_', ' ').title()} approval required for {len(points)} operations")
        
        return requirements
    
    def get_next_approval_step(
        self,
        approval_points: List[ApprovalPoint],
        completed_approvals: Optional[List[str]] = None
    ) -> Optional[ApprovalPoint]:
        """
        Get the next approval step that needs to be completed
        
        Args:
            approval_points: List of all approval points
            completed_approvals: List of completed approval step IDs
            
        Returns:
            Next approval point to complete, or None if all complete
        """
        
        if not approval_points:
            return None
        
        completed_approvals = completed_approvals or []
        
        # Find first uncompleted approval point
        for ap in approval_points:
            if ap.step_id not in completed_approvals:
                return ap
        
        return None  # All approvals completed