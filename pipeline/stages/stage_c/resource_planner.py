"""
Resource Planner for Stage C Planner

Manages resource allocation, constraints, and observability configuration.
Ensures optimal resource utilization and comprehensive monitoring setup.
"""

from typing import Dict, Any, List, Optional, Set
from datetime import datetime, timedelta

from ...schemas.decision_v1 import DecisionV1
from ...schemas.selection_v1 import SelectionV1
from ...schemas.plan_v1 import ExecutionStep, ObservabilityConfig, ExecutionMetadata


class ResourcePlanner:
    """
    Plans resource allocation and observability for execution plans.
    
    This class is responsible for:
    - Calculating resource requirements and constraints
    - Setting up observability and monitoring configuration
    - Identifying approval points and checkpoints
    - Estimating execution times and resource usage
    - Planning resource allocation strategies
    """
    
    def __init__(self):
        """Initialize the resource planner"""
        
        # Tool resource requirements (baseline estimates)
        self.tool_resources = {
            "systemctl": {"cpu": 0.1, "memory_mb": 10, "disk_mb": 1, "network": False},
            "ps": {"cpu": 0.2, "memory_mb": 20, "disk_mb": 1, "network": False},
            "journalctl": {"cpu": 0.3, "memory_mb": 50, "disk_mb": 10, "network": False},
            "file_manager": {"cpu": 0.2, "memory_mb": 30, "disk_mb": 100, "network": False},
            "network_tools": {"cpu": 0.1, "memory_mb": 15, "disk_mb": 1, "network": True},
            "docker": {"cpu": 0.5, "memory_mb": 100, "disk_mb": 50, "network": True},
            "config_manager": {"cpu": 0.2, "memory_mb": 40, "disk_mb": 20, "network": False},
            "info_display": {"cpu": 0.1, "memory_mb": 10, "disk_mb": 1, "network": False}
        }
        
        # Observability templates by tool
        self.observability_templates = {
            "systemctl": self._get_systemctl_observability,
            "ps": self._get_ps_observability,
            "journalctl": self._get_journalctl_observability,
            "file_manager": self._get_file_manager_observability,
            "network_tools": self._get_network_tools_observability,
            "docker": self._get_docker_observability,
            "config_manager": self._get_config_manager_observability,
            "info_display": self._get_info_display_observability
        }
    
    def create_resource_plan(
        self, 
        steps: List[ExecutionStep], 
        decision: DecisionV1, 
        selection: SelectionV1
    ) -> tuple[ObservabilityConfig, ExecutionMetadata]:
        """
        Create comprehensive resource and observability plan.
        
        Args:
            steps: Execution steps to plan resources for
            decision: Original decision context
            selection: Tool selection context
            
        Returns:
            Tuple of (observability_config, execution_metadata)
        """
        # Create observability configuration
        observability = self._create_observability_config(steps, decision, selection)
        
        # Create execution metadata
        metadata = self._create_execution_metadata(steps, decision, selection)
        
        return observability, metadata
    
    def calculate_resource_requirements(
        self, 
        steps: List[ExecutionStep]
    ) -> Dict[str, Any]:
        """
        Calculate total resource requirements for the execution plan.
        
        Args:
            steps: Execution steps to calculate resources for
            
        Returns:
            Dictionary with resource requirements
        """
        total_cpu = 0.0
        total_memory_mb = 0
        total_disk_mb = 0
        requires_network = False
        
        # Calculate peak resource usage (assuming parallel execution)
        tools_used = set()
        for step in steps:
            tools_used.add(step.tool)
        
        for tool in tools_used:
            if tool in self.tool_resources:
                resources = self.tool_resources[tool]
                total_cpu += resources["cpu"]
                total_memory_mb += resources["memory_mb"]
                total_disk_mb += resources["disk_mb"]
                if resources["network"]:
                    requires_network = True
        
        return {
            "cpu_cores": round(total_cpu, 2),
            "memory_mb": total_memory_mb,
            "disk_mb": total_disk_mb,
            "network_required": requires_network,
            "estimated_peak_usage": {
                "cpu_percent": min(total_cpu * 100, 100),
                "memory_mb": total_memory_mb,
                "disk_io_mb": total_disk_mb
            }
        }
    
    def _create_observability_config(
        self, 
        steps: List[ExecutionStep], 
        decision: DecisionV1, 
        selection: SelectionV1
    ) -> ObservabilityConfig:
        """Create comprehensive observability configuration"""
        
        metrics = set()
        logs = set()
        alerts = set()
        
        # Add base system metrics
        metrics.update([
            "cpu_usage_percent",
            "memory_usage_mb",
            "disk_usage_percent",
            "execution_time_seconds"
        ])
        
        # Add base system logs
        logs.update([
            "/var/log/syslog",
            "/var/log/messages"
        ])
        
        # Add tool-specific observability
        for step in steps:
            tool_name = step.tool
            if tool_name in self.observability_templates:
                tool_obs = self.observability_templates[tool_name](step, decision, selection)
                metrics.update(tool_obs.get("metrics", []))
                logs.update(tool_obs.get("logs", []))
                alerts.update(tool_obs.get("alerts", []))
        
        # Add risk-based monitoring
        risk_level = decision.risk_level
        if risk_level.value in ["high", "critical"]:
            metrics.update([
                "system_load_average",
                "network_connections_count",
                "process_count",
                "file_descriptor_count"
            ])
            alerts.update([
                "cpu_usage > 80%",
                "memory_usage > 85%",
                "disk_usage > 90%"
            ])
        
        # Add production-specific monitoring
        if selection.environment_requirements.get("production_safe", False):
            metrics.update([
                "service_availability_percent",
                "response_time_ms",
                "error_rate_percent"
            ])
            alerts.update([
                "service_down",
                "response_time > 5000ms",
                "error_rate > 5%"
            ])
        
        return ObservabilityConfig(
            metrics_to_collect=sorted(list(metrics)),
            logs_to_monitor=sorted(list(logs)),
            alerts_to_set=sorted(list(alerts))
        )
    
    def _create_execution_metadata(
        self, 
        steps: List[ExecutionStep], 
        decision: DecisionV1, 
        selection: SelectionV1
    ) -> ExecutionMetadata:
        """Create execution metadata with timing and approval requirements"""
        
        # Calculate total estimated time
        total_time = sum(step.estimated_duration for step in steps)
        
        # Identify risk factors
        risk_factors = []
        # Add basic risk factor based on risk level
        risk_factors.append(f"risk_level_{decision.risk_level.value}")
        
        # Add tool-specific risk factors
        destructive_tools = {"systemctl", "file_manager", "config_manager", "docker"}
        for step in steps:
            if step.tool in destructive_tools:
                risk_factors.append(f"uses_destructive_tool_{step.tool}")
        
        # Add environment risk factors
        if selection.environment_requirements.get("production_safe", False):
            risk_factors.append("production_environment")
        
        # Identify approval points
        approval_points = []
        if selection.policy.requires_approval:
            # High-risk steps require approval
            for step in steps:
                if step.tool in destructive_tools:
                    approval_points.append(step.id)
        
        # Add manual approval for critical risk
        if decision.risk_level.value == "critical":
            approval_points.extend([step.id for step in steps])
        
        # Identify checkpoint steps
        checkpoint_steps = []
        
        # Add checkpoints before destructive operations
        for i, step in enumerate(steps):
            if step.tool in destructive_tools:
                checkpoint_steps.append(step.id)
                
                # Add checkpoint after backup operations
                if "backup" in step.inputs.get("operation", ""):
                    checkpoint_steps.append(step.id)
        
        # Add checkpoints for long-running operations
        for step in steps:
            if step.estimated_duration > 60:  # More than 1 minute
                checkpoint_steps.append(step.id)
        
        # Add final checkpoint
        if steps:
            checkpoint_steps.append(steps[-1].id)
        
        return ExecutionMetadata(
            total_estimated_time=total_time,
            risk_factors=sorted(list(set(risk_factors))),
            approval_points=sorted(list(set(approval_points))),
            checkpoint_steps=sorted(list(set(checkpoint_steps)))
        )
    
    # Tool-specific observability generators
    def _get_systemctl_observability(
        self, 
        step: ExecutionStep, 
        decision: DecisionV1, 
        selection: SelectionV1
    ) -> Dict[str, List[str]]:
        """Get observability config for systemctl operations"""
        service = step.inputs.get("service", "unknown")
        
        return {
            "metrics": [
                f"service_{service}_status",
                f"service_{service}_memory_usage",
                f"service_{service}_cpu_usage",
                "systemctl_execution_time"
            ],
            "logs": [
                "/var/log/syslog",
                f"/var/log/{service}.log",
                "/var/log/systemd.log"
            ],
            "alerts": [
                f"service_{service}_failed",
                f"service_{service}_restart_count > 3",
                "systemctl_command_timeout"
            ]
        }
    
    def _get_ps_observability(
        self, 
        step: ExecutionStep, 
        decision: DecisionV1, 
        selection: SelectionV1
    ) -> Dict[str, List[str]]:
        """Get observability config for ps operations"""
        return {
            "metrics": [
                "process_count",
                "zombie_process_count",
                "high_cpu_process_count",
                "ps_execution_time"
            ],
            "logs": [
                "/var/log/syslog"
            ],
            "alerts": [
                "zombie_processes > 10",
                "process_count > 1000",
                "ps_command_timeout"
            ]
        }
    
    def _get_journalctl_observability(
        self, 
        step: ExecutionStep, 
        decision: DecisionV1, 
        selection: SelectionV1
    ) -> Dict[str, List[str]]:
        """Get observability config for journalctl operations"""
        return {
            "metrics": [
                "journal_size_mb",
                "journal_entries_count",
                "journal_error_count",
                "journalctl_execution_time"
            ],
            "logs": [
                "/var/log/journal/*"
            ],
            "alerts": [
                "journal_size > 1000MB",
                "journal_errors > 100",
                "journalctl_command_timeout"
            ]
        }
    
    def _get_file_manager_observability(
        self, 
        step: ExecutionStep, 
        decision: DecisionV1, 
        selection: SelectionV1
    ) -> Dict[str, List[str]]:
        """Get observability config for file manager operations"""
        file_path = step.inputs.get("path", "unknown")
        
        return {
            "metrics": [
                "file_operation_duration",
                "file_size_bytes",
                "disk_io_operations",
                "file_permissions_changes"
            ],
            "logs": [
                "/var/log/syslog",
                "/var/log/audit/audit.log"
            ],
            "alerts": [
                "file_operation_timeout",
                "file_permission_denied",
                f"file_size_changed_{file_path}"
            ]
        }
    
    def _get_network_tools_observability(
        self, 
        step: ExecutionStep, 
        decision: DecisionV1, 
        selection: SelectionV1
    ) -> Dict[str, List[str]]:
        """Get observability config for network tools"""
        tool_type = step.inputs.get("tool", "ping")
        target = step.inputs.get("target", "unknown")
        
        return {
            "metrics": [
                f"{tool_type}_response_time_ms",
                f"{tool_type}_success_rate",
                "network_packet_loss_percent",
                "network_bandwidth_usage"
            ],
            "logs": [
                "/var/log/syslog",
                "/var/log/network.log"
            ],
            "alerts": [
                f"{tool_type}_timeout",
                f"packet_loss > 10%",
                f"target_{target}_unreachable"
            ]
        }
    
    def _get_docker_observability(
        self, 
        step: ExecutionStep, 
        decision: DecisionV1, 
        selection: SelectionV1
    ) -> Dict[str, List[str]]:
        """Get observability config for Docker operations"""
        container = step.inputs.get("container", "unknown")
        
        return {
            "metrics": [
                f"container_{container}_cpu_usage",
                f"container_{container}_memory_usage",
                f"container_{container}_status",
                "docker_operation_duration"
            ],
            "logs": [
                "/var/log/docker.log",
                f"/var/lib/docker/containers/{container}/*.log"
            ],
            "alerts": [
                f"container_{container}_unhealthy",
                f"container_{container}_high_memory",
                "docker_daemon_error"
            ]
        }
    
    def _get_config_manager_observability(
        self, 
        step: ExecutionStep, 
        decision: DecisionV1, 
        selection: SelectionV1
    ) -> Dict[str, List[str]]:
        """Get observability config for config manager operations"""
        config_file = step.inputs.get("config_file", "unknown")
        
        return {
            "metrics": [
                "config_validation_time",
                "config_file_size_bytes",
                "config_syntax_errors",
                "config_backup_count"
            ],
            "logs": [
                "/var/log/syslog",
                "/var/log/config-manager.log"
            ],
            "alerts": [
                "config_validation_failed",
                "config_syntax_error",
                f"config_file_modified_{config_file}"
            ]
        }
    
    def _get_info_display_observability(
        self, 
        step: ExecutionStep, 
        decision: DecisionV1, 
        selection: SelectionV1
    ) -> Dict[str, List[str]]:
        """Get observability config for info display operations"""
        return {
            "metrics": [
                "info_collection_time",
                "info_data_size_bytes",
                "info_sources_available"
            ],
            "logs": [
                "/var/log/syslog"
            ],
            "alerts": [
                "info_collection_timeout",
                "info_source_unavailable"
            ]
        }
    
    def get_resource_constraints(
        self, 
        steps: List[ExecutionStep], 
        selection: SelectionV1
    ) -> Dict[str, Any]:
        """
        Get resource constraints and limits for execution.
        
        Args:
            steps: Execution steps
            selection: Selection context
            
        Returns:
            Resource constraints dictionary
        """
        requirements = self.calculate_resource_requirements(steps)
        
        constraints = {
            "max_cpu_percent": 80,  # Don't use more than 80% CPU
            "max_memory_mb": requirements["memory_mb"] * 2,  # 2x buffer
            "max_disk_mb": requirements["disk_mb"] * 3,  # 3x buffer for temp files
            "max_execution_time_seconds": sum(step.estimated_duration for step in steps) * 2,
            "max_parallel_operations": 3 if selection.policy.parallel_execution else 1,
            "network_timeout_seconds": 30,
            "file_operation_timeout_seconds": 60
        }
        
        # Adjust for environment requirements
        min_memory = selection.environment_requirements.get("min_memory_mb", 0)
        if min_memory > 0:
            constraints["required_memory_mb"] = min_memory
        
        min_disk = selection.environment_requirements.get("min_disk_gb", 0)
        if min_disk > 0:
            constraints["required_disk_gb"] = min_disk
        
        return constraints