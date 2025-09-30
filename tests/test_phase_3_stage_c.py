"""
Comprehensive Test Suite for Phase 3: Stage C Planner

Tests all components of the planning stage including:
- Plan V1 Schema validation
- Step Generation functionality
- Dependency Resolution logic
- Safety Planning measures
- Resource Planning allocation
- Stage C Planner integration
- Error handling and fallbacks
- Performance characteristics
"""

import pytest
import asyncio
from datetime import datetime
from typing import Dict, Any, List

# Import schemas
from pipeline.schemas.decision_v1 import DecisionV1, IntentV1, EntityV1, RiskLevel
from pipeline.schemas.selection_v1 import SelectionV1, SelectedTool, ExecutionPolicy
from pipeline.schemas.plan_v1 import (
    PlanV1, ExecutionPlan, ExecutionStep, SafetyCheck, RollbackStep, 
    ObservabilityConfig, ExecutionMetadata, SafetyStage, FailureAction
)

# Import Stage C components
from pipeline.stages.stage_c.planner import StageCPlanner, PlanningError
from pipeline.stages.stage_c.step_generator import StepGenerator
from pipeline.stages.stage_c.dependency_resolver import DependencyResolver, DependencyError
from pipeline.stages.stage_c.safety_planner import SafetyPlanner
from pipeline.stages.stage_c.resource_planner import ResourcePlanner


class TestPlanV1Schema:
    """Test Plan V1 schema validation and structure"""
    
    def test_plan_v1_schema_structure(self):
        """Test Plan V1 schema has correct structure"""
        # Create minimal valid plan
        step = ExecutionStep(
            id="test_001",
            description="Test step",
            tool="ps",
            estimated_duration=10,
            failure_handling="Log error"
        )
        
        safety_check = SafetyCheck(
            check="Test safety check",
            stage=SafetyStage.BEFORE,
            failure_action=FailureAction.WARN
        )
        
        execution_plan = ExecutionPlan(
            steps=[step],
            safety_checks=[safety_check],
            rollback_plan=[],
            observability=ObservabilityConfig()
        )
        
        metadata = ExecutionMetadata(
            total_estimated_time=10,
            risk_factors=[],
            approval_points=[],
            checkpoint_steps=[]
        )
        
        plan = PlanV1(
            plan=execution_plan,
            execution_metadata=metadata,
            timestamp=datetime.now().isoformat(),
            processing_time_ms=100
        )
        
        # Validate structure
        assert plan.stage == "stage_c_planner"
        assert plan.version == "1.0"
        assert len(plan.plan.steps) == 1
        assert len(plan.plan.safety_checks) == 1
        assert plan.execution_metadata.total_estimated_time == 10
    
    def test_execution_step_validation(self):
        """Test execution step validation"""
        step = ExecutionStep(
            id="step_001_test",
            description="Test execution step",
            tool="systemctl",
            inputs={"action": "status", "service": "nginx"},
            preconditions=["systemctl_available"],
            success_criteria=["command_executed"],
            failure_handling="Log error and continue",
            estimated_duration=15,
            depends_on=["step_000_prep"]
        )
        
        assert step.id == "step_001_test"
        assert step.tool == "systemctl"
        assert step.estimated_duration == 15
        assert len(step.preconditions) == 1
        assert len(step.depends_on) == 1
    
    def test_safety_check_validation(self):
        """Test safety check validation"""
        safety_check = SafetyCheck(
            check="Verify system is accessible",
            stage=SafetyStage.BEFORE,
            failure_action=FailureAction.ABORT
        )
        
        assert safety_check.stage == SafetyStage.BEFORE
        assert safety_check.failure_action == FailureAction.ABORT
    
    def test_observability_config_structure(self):
        """Test observability configuration structure"""
        obs_config = ObservabilityConfig(
            metrics_to_collect=["cpu_usage", "memory_usage"],
            logs_to_monitor=["/var/log/syslog"],
            alerts_to_set=["high_cpu > 80%"]
        )
        
        assert len(obs_config.metrics_to_collect) == 2
        assert len(obs_config.logs_to_monitor) == 1
        assert len(obs_config.alerts_to_set) == 1


class TestStepGenerator:
    """Test step generation functionality"""
    
    def setup_method(self):
        """Set up test fixtures"""
        self.step_generator = StepGenerator()
        
        # Create test decision
        self.decision = DecisionV1(
            decision_id="test_decision_001",
            decision_type="action",
            timestamp=datetime.now().isoformat(),
            intent=IntentV1(category="monitor_system", action="check_processes", confidence=0.9),
            entities=[
                EntityV1(type="service_name", value="nginx", confidence=0.9)
            ],
            overall_confidence=0.85,
            confidence_level="high",
            risk_level=RiskLevel.LOW,
            original_request="Check nginx service status",
            next_stage="stage_b",
            processing_time_ms=100
        )
        
        # Create test selection
        self.selection = SelectionV1(
            selection_id="test_selection_001",
            decision_id="test_decision_001",
            selected_tools=[
                SelectedTool(
                    tool_name="systemctl",
                    justification="Check service status",
                    execution_order=1
                ),
                SelectedTool(
                    tool_name="ps",
                    justification="List processes",
                    execution_order=2
                )
            ],
            policy=ExecutionPolicy(
                risk_level=RiskLevel.LOW,
                requires_approval=False,
                max_execution_time=30,
                parallel_execution=True
            ),
            environment_requirements={
                "production_safe": True,
                "min_memory_mb": 100,
                "min_disk_gb": 1
            },
            total_tools=2,
            selection_confidence=0.85,
            next_stage="stage_c",
            timestamp=datetime.now().isoformat(),
            processing_time_ms=150
        )
    
    def test_generate_steps_basic(self):
        """Test basic step generation"""
        steps = self.step_generator.generate_steps(self.decision, self.selection)
        
        assert len(steps) == 2
        assert steps[0].tool == "systemctl"
        assert steps[1].tool == "ps"
        assert all(step.id.startswith("step_") for step in steps)
    
    def test_systemctl_step_generation(self):
        """Test systemctl-specific step generation"""
        systemctl_selection = SelectionV1(
            selection_id="test_selection_systemctl",
            decision_id="test_decision_restart",
            selected_tools=[
                SelectedTool(
                    tool_name="systemctl",
                    justification="Restart service",
                    execution_order=1
                )
            ],
            policy=ExecutionPolicy(
                requires_approval=False,
                risk_level=RiskLevel.MEDIUM,
                max_execution_time=60
            ),
            environment_requirements={},
            total_tools=1,
            selection_confidence=0.8,
            next_stage="stage_c",
            timestamp=datetime.now().isoformat(),
            processing_time_ms=100
        )
        
        restart_decision = DecisionV1(
            decision_id="test_decision_restart",
            decision_type="action",
            timestamp=datetime.now().isoformat(),
            intent=IntentV1(category="restart_service", action="restart_nginx", confidence=0.9),
            entities=[EntityV1(type="service_name", value="nginx", confidence=0.9)],
            overall_confidence=0.8,
            confidence_level="high",
            risk_level=RiskLevel.MEDIUM,
            original_request="restart nginx service",
            next_stage="stage_b",
            processing_time_ms=100
        )
        
        steps = self.step_generator.generate_steps(restart_decision, systemctl_selection)
        
        assert len(steps) == 1
        step = steps[0]
        assert step.tool == "systemctl"
        assert step.inputs["action"] == "restart"
        assert step.inputs["service"] == "nginx"
        assert "systemctl_command_available" in step.preconditions
    
    def test_file_manager_step_generation(self):
        """Test file manager step generation"""
        file_selection = SelectionV1(
            selection_id="test_selection_file",
            decision_id="test_decision_file",
            selected_tools=[
                SelectedTool(
                    tool_name="file_manager",
                    justification="Backup configuration",
                    execution_order=1
                )
            ],
            policy=ExecutionPolicy(
                requires_approval=False,
                risk_level=RiskLevel.MEDIUM,
                max_execution_time=60
            ),
            environment_requirements={},
            total_tools=1,
            selection_confidence=0.8,
            next_stage="stage_c",
            timestamp=datetime.now().isoformat(),
            processing_time_ms=100
        )
        
        config_decision = DecisionV1(
            decision_id="test_decision_config",
            decision_type="action",
            timestamp=datetime.now().isoformat(),
            intent=IntentV1(category="modify_config", action="backup_config", confidence=0.9),
            entities=[EntityV1(type="file_path", value="/etc/nginx/nginx.conf", confidence=0.9)],
            overall_confidence=0.8,
            confidence_level="high",
            risk_level=RiskLevel.MEDIUM,
            original_request="backup nginx config",
            next_stage="stage_b",
            processing_time_ms=100
        )
        
        steps = self.step_generator.generate_steps(config_decision, file_selection)
        
        assert len(steps) == 1
        step = steps[0]
        assert step.tool == "file_manager"
        assert step.inputs["operation"] == "backup"
        assert step.inputs["path"] == "/etc/nginx/nginx.conf"
    
    def test_docker_step_generation(self):
        """Test Docker step generation"""
        docker_selection = SelectionV1(
            selection_id="test_selection_docker",
            decision_id="test_decision_docker",
            selected_tools=[
                SelectedTool(
                    tool_name="docker",
                    justification="Check containers",
                    execution_order=1
                )
            ],
            policy=ExecutionPolicy(
                requires_approval=False,
                risk_level=RiskLevel.LOW,
                max_execution_time=30
            ),
            environment_requirements={},
            total_tools=1,
            selection_confidence=0.8,
            next_stage="stage_c",
            timestamp=datetime.now().isoformat(),
            processing_time_ms=100
        )
        
        steps = self.step_generator.generate_steps(self.decision, docker_selection)
        
        assert len(steps) == 1
        step = steps[0]
        assert step.tool == "docker"
        assert step.inputs["operation"] == "ps"
        assert "docker_command_available" in step.preconditions
    
    def test_step_id_generation(self):
        """Test unique step ID generation"""
        steps = self.step_generator.generate_steps(self.decision, self.selection)
        
        step_ids = [step.id for step in steps]
        assert len(step_ids) == len(set(step_ids))  # All IDs are unique
        assert all("step_" in step_id for step_id in step_ids)
    
    def test_execution_time_estimation(self):
        """Test execution time estimation"""
        steps = self.step_generator.generate_steps(self.decision, self.selection)
        
        for step in steps:
            assert step.estimated_duration > 0
            assert step.estimated_duration <= 60  # Reasonable upper bound


class TestDependencyResolver:
    """Test dependency resolution logic"""
    
    def setup_method(self):
        """Set up test fixtures"""
        self.dependency_resolver = DependencyResolver()
    
    def test_simple_dependency_resolution(self):
        """Test simple dependency resolution"""
        steps = [
            ExecutionStep(
                id="step_001",
                description="First step",
                tool="ps",
                estimated_duration=5,
                failure_handling="Continue",
                depends_on=[]
            ),
            ExecutionStep(
                id="step_002", 
                description="Second step",
                tool="systemctl",
                estimated_duration=10,
                failure_handling="Continue",
                depends_on=["step_001"]
            )
        ]
        
        ordered_steps = self.dependency_resolver.resolve_dependencies(steps)
        
        assert len(ordered_steps) == 2
        assert ordered_steps[0].id == "step_001"
        assert ordered_steps[1].id == "step_002"
    
    def test_complex_dependency_resolution(self):
        """Test complex dependency resolution"""
        steps = [
            ExecutionStep(
                id="step_003",
                description="Third step",
                tool="docker",
                estimated_duration=15,
                failure_handling="Continue",
                depends_on=["step_001", "step_002"]
            ),
            ExecutionStep(
                id="step_001",
                description="First step", 
                tool="ps",
                estimated_duration=5,
                failure_handling="Continue",
                depends_on=[]
            ),
            ExecutionStep(
                id="step_002",
                description="Second step",
                tool="systemctl", 
                estimated_duration=10,
                failure_handling="Continue",
                depends_on=["step_001"]
            )
        ]
        
        ordered_steps = self.dependency_resolver.resolve_dependencies(steps)
        
        assert len(ordered_steps) == 3
        assert ordered_steps[0].id == "step_001"
        assert ordered_steps[1].id == "step_002"
        assert ordered_steps[2].id == "step_003"
    
    def test_parallel_execution_identification(self):
        """Test parallel execution group identification"""
        steps = [
            ExecutionStep(
                id="step_001",
                description="Independent step 1",
                tool="ps",
                estimated_duration=5,
                failure_handling="Continue",
                depends_on=[]
            ),
            ExecutionStep(
                id="step_002",
                description="Independent step 2", 
                tool="journalctl",
                estimated_duration=10,
                failure_handling="Continue",
                depends_on=[]
            ),
            ExecutionStep(
                id="step_003",
                description="Dependent step",
                tool="systemctl",
                estimated_duration=15,
                failure_handling="Continue", 
                depends_on=["step_001", "step_002"]
            )
        ]
        
        parallel_groups = self.dependency_resolver.identify_parallel_groups(steps)
        
        assert len(parallel_groups) == 2
        assert len(parallel_groups[0]) == 2  # First two steps can run in parallel
        assert len(parallel_groups[1]) == 1  # Last step runs alone
    
    def test_circular_dependency_detection(self):
        """Test circular dependency detection"""
        steps = [
            ExecutionStep(
                id="step_001",
                description="Step 1",
                tool="ps",
                estimated_duration=5,
                failure_handling="Continue",
                depends_on=["step_002"]
            ),
            ExecutionStep(
                id="step_002",
                description="Step 2",
                tool="systemctl",
                estimated_duration=10,
                failure_handling="Continue",
                depends_on=["step_001"]
            )
        ]
        
        with pytest.raises(DependencyError):
            self.dependency_resolver.resolve_dependencies(steps)
    
    def test_wildcard_dependency_resolution(self):
        """Test wildcard dependency pattern resolution"""
        steps = [
            ExecutionStep(
                id="step_001_systemctl_status",
                description="Check service status",
                tool="systemctl",
                estimated_duration=10,
                failure_handling="Continue",
                depends_on=[]
            ),
            ExecutionStep(
                id="step_002_analysis",
                description="Analyze results",
                tool="info_display",
                estimated_duration=5,
                failure_handling="Continue",
                depends_on=["step_*_systemctl_*"]
            )
        ]
        
        ordered_steps = self.dependency_resolver.resolve_dependencies(steps)
        
        assert len(ordered_steps) == 2
        assert ordered_steps[0].id == "step_001_systemctl_status"
        assert ordered_steps[1].id == "step_002_analysis"
    
    def test_dependency_validation(self):
        """Test dependency validation"""
        valid_steps = [
            ExecutionStep(
                id="step_001",
                description="Valid step",
                tool="ps",
                estimated_duration=5,
                failure_handling="Continue",
                depends_on=[]
            )
        ]
        
        is_valid, errors = self.dependency_resolver.validate_dependencies(valid_steps)
        assert is_valid
        assert len(errors) == 0
        
        # Test invalid dependencies
        invalid_steps = [
            ExecutionStep(
                id="step_001",
                description="Invalid step",
                tool="ps", 
                estimated_duration=5,
                failure_handling="Continue",
                depends_on=["nonexistent_step"]
            )
        ]
        
        is_valid, errors = self.dependency_resolver.validate_dependencies(invalid_steps)
        assert not is_valid
        assert len(errors) > 0


class TestSafetyPlanner:
    """Test safety planning functionality"""
    
    def setup_method(self):
        """Set up test fixtures"""
        self.safety_planner = SafetyPlanner()
        
        # Create test data
        self.decision = DecisionV1(
            decision_id="test_decision_safety",
            decision_type="action",
            timestamp=datetime.now().isoformat(),
            intent=IntentV1(category="restart_service", action="restart_nginx", confidence=0.9),
            entities=[EntityV1(type="service_name", value="nginx", confidence=0.9)],
            overall_confidence=0.8,
            confidence_level="high",
            risk_level=RiskLevel.HIGH,
            original_request="restart nginx service",
            next_stage="stage_b",
            processing_time_ms=100
        )
        
        self.selection = SelectionV1(
            selection_id="test_selection_setup",
            decision_id="test_decision_setup",
            selected_tools=[
                SelectedTool(
                    tool_name="systemctl",
                    justification="Restart service",
                    execution_order=1
                )
            ],
            policy=ExecutionPolicy(
                risk_level=RiskLevel.HIGH,
                requires_approval=True,
                max_execution_time=60
            ),
            environment_requirements={
                "production_safe": True,
                "min_memory_mb": 512
            },
            total_tools=1,
            selection_confidence=0.8,
            next_stage="stage_c",
            timestamp=datetime.now().isoformat(),
            processing_time_ms=100
        )
        
        self.steps = [
            ExecutionStep(
                id="step_001_systemctl_restart",
                description="Restart nginx service",
                tool="systemctl",
                inputs={"action": "restart", "service": "nginx"},
                estimated_duration=15,
                failure_handling="Rollback to previous state"
            )
        ]
    
    def test_create_safety_plan(self):
        """Test comprehensive safety plan creation"""
        safety_checks, rollback_steps = self.safety_planner.create_safety_plan(
            self.steps, self.decision, self.selection
        )
        
        assert len(safety_checks) > 0
        assert len(rollback_steps) > 0
        
        # Check for high-risk safety measures
        check_descriptions = [check.check for check in safety_checks]
        assert any("backup" in desc.lower() for desc in check_descriptions)
        assert any("approval" in desc.lower() for desc in check_descriptions)
    
    def test_risk_based_safety_checks(self):
        """Test risk-based safety check generation"""
        # Test high-risk checks
        high_risk_decision = self.decision
        safety_checks, _ = self.safety_planner.create_safety_plan(
            self.steps, high_risk_decision, self.selection
        )
        
        high_risk_checks = [check for check in safety_checks if check.failure_action == FailureAction.ABORT]
        assert len(high_risk_checks) > 0
        
        # Test low-risk checks
        low_risk_decision = DecisionV1(
            decision_id="test_decision_low_risk",
            decision_type="action",
            timestamp=datetime.now().isoformat(),
            intent=IntentV1(category="monitor_system", action="check_status", confidence=0.9),
            entities=[],
            overall_confidence=0.8,
            confidence_level="high",
            risk_level=RiskLevel.LOW,
            original_request="check system status",
            next_stage="stage_b",
            processing_time_ms=100
        )
        
        low_risk_selection = SelectionV1(
            selection_id="test_selection_low_risk",
            decision_id="test_decision_low_risk",
            selected_tools=[
                SelectedTool(tool_name="ps", justification="List processes", execution_order=1)
            ],
            policy=ExecutionPolicy(
                requires_approval=False,
                risk_level=RiskLevel.LOW,
                max_execution_time=30
            ),
            environment_requirements={},
            total_tools=1,
            selection_confidence=0.8,
            next_stage="stage_c",
            timestamp=datetime.now().isoformat(),
            processing_time_ms=100
        )
        
        low_risk_steps = [
            ExecutionStep(
                id="step_001_ps",
                description="List processes",
                tool="ps",
                estimated_duration=5,
                failure_handling="Continue"
            )
        ]
        
        safety_checks, _ = self.safety_planner.create_safety_plan(
            low_risk_steps, low_risk_decision, low_risk_selection
        )
        
        warn_checks = [check for check in safety_checks if check.failure_action == FailureAction.WARN]
        assert len(warn_checks) > 0
    
    def test_tool_specific_safety_checks(self):
        """Test tool-specific safety check generation"""
        systemctl_steps = [
            ExecutionStep(
                id="step_001_systemctl",
                description="Systemctl operation",
                tool="systemctl",
                inputs={"action": "restart", "service": "nginx"},
                estimated_duration=10,
                failure_handling="Continue"
            )
        ]
        
        safety_checks, _ = self.safety_planner.create_safety_plan(
            systemctl_steps, self.decision, self.selection
        )
        
        systemctl_checks = [
            check for check in safety_checks 
            if "systemd" in check.check.lower() or "service" in check.check.lower()
        ]
        assert len(systemctl_checks) > 0
    
    def test_rollback_procedure_creation(self):
        """Test rollback procedure creation"""
        safety_checks, rollback_steps = self.safety_planner.create_safety_plan(
            self.steps, self.decision, self.selection
        )
        
        assert len(rollback_steps) > 0
        
        # Check rollback for systemctl restart
        systemctl_rollback = next(
            (rb for rb in rollback_steps if rb.step_id == "step_001_systemctl_restart"),
            None
        )
        assert systemctl_rollback is not None
        assert "service" in systemctl_rollback.rollback_action.lower()
    
    def test_production_environment_safety(self):
        """Test production environment safety measures"""
        prod_selection = SelectionV1(
            selection_id="test_selection_prod",
            decision_id="test_decision_prod",
            selected_tools=[
                SelectedTool(tool_name="systemctl", justification="Restart service", execution_order=1)
            ],
            policy=ExecutionPolicy(
                requires_approval=True,
                risk_level=RiskLevel.HIGH,
                max_execution_time=120
            ),
            environment_requirements={
                "production_safe": True,
                "min_memory_mb": 1024,
                "min_disk_gb": 10
            },
            total_tools=1,
            selection_confidence=0.8,
            next_stage="stage_c",
            timestamp=datetime.now().isoformat(),
            processing_time_ms=100
        )
        
        safety_checks, _ = self.safety_planner.create_safety_plan(
            self.steps, self.decision, prod_selection
        )
        
        prod_checks = [
            check for check in safety_checks 
            if "production" in check.check.lower() or "backup" in check.check.lower()
        ]
        assert len(prod_checks) > 0


class TestResourcePlanner:
    """Test resource planning functionality"""
    
    def setup_method(self):
        """Set up test fixtures"""
        self.resource_planner = ResourcePlanner()
        
        self.decision = DecisionV1(
            decision_id="test_decision_resource",
            decision_type="action",
            timestamp=datetime.now().isoformat(),
            intent=IntentV1(category="monitor_system", action="check_processes", confidence=0.9),
            entities=[],
            overall_confidence=0.8,
            confidence_level="high",
            risk_level=RiskLevel.MEDIUM,
            original_request="monitor system processes",
            next_stage="stage_b",
            processing_time_ms=100
        )
        
        self.selection = SelectionV1(
            selection_id="test_selection_setup",
            decision_id="test_decision_setup",
            selected_tools=[
                SelectedTool(tool_name="ps", justification="List processes", execution_order=1),
                SelectedTool(tool_name="systemctl", justification="Check services", execution_order=2)
            ],
            policy=ExecutionPolicy(
                requires_approval=False,
                risk_level=RiskLevel.MEDIUM,
                max_execution_time=60
            ),
            environment_requirements={
                "min_memory_mb": 256,
                "min_disk_gb": 5
            },
            total_tools=2,
            selection_confidence=0.8,
            next_stage="stage_c",
            timestamp=datetime.now().isoformat(),
            processing_time_ms=100
        )
        
        self.steps = [
            ExecutionStep(
                id="step_001_ps",
                description="List processes",
                tool="ps",
                estimated_duration=5,
                failure_handling="Continue"
            ),
            ExecutionStep(
                id="step_002_systemctl",
                description="Check services",
                tool="systemctl",
                estimated_duration=10,
                failure_handling="Continue"
            )
        ]
    
    def test_create_resource_plan(self):
        """Test resource plan creation"""
        observability, metadata = self.resource_planner.create_resource_plan(
            self.steps, self.decision, self.selection
        )
        
        assert isinstance(observability, ObservabilityConfig)
        assert isinstance(metadata, ExecutionMetadata)
        
        assert len(observability.metrics_to_collect) > 0
        assert len(observability.logs_to_monitor) > 0
        assert metadata.total_estimated_time == 15  # 5 + 10
    
    def test_resource_requirements_calculation(self):
        """Test resource requirements calculation"""
        requirements = self.resource_planner.calculate_resource_requirements(self.steps)
        
        assert "cpu_cores" in requirements
        assert "memory_mb" in requirements
        assert "disk_mb" in requirements
        assert "network_required" in requirements
        
        assert requirements["cpu_cores"] > 0
        assert requirements["memory_mb"] > 0
    
    def test_observability_configuration(self):
        """Test observability configuration generation"""
        observability, _ = self.resource_planner.create_resource_plan(
            self.steps, self.decision, self.selection
        )
        
        # Check base metrics are included
        assert "cpu_usage_percent" in observability.metrics_to_collect
        assert "memory_usage_mb" in observability.metrics_to_collect
        assert "execution_time_seconds" in observability.metrics_to_collect
        
        # Check base logs are included
        assert any("/var/log" in log for log in observability.logs_to_monitor)
    
    def test_execution_metadata_generation(self):
        """Test execution metadata generation"""
        _, metadata = self.resource_planner.create_resource_plan(
            self.steps, self.decision, self.selection
        )
        
        assert metadata.total_estimated_time == 15
        assert len(metadata.risk_factors) > 0
        assert len(metadata.checkpoint_steps) > 0
    
    def test_high_risk_observability(self):
        """Test enhanced observability for high-risk operations"""
        high_risk_decision = DecisionV1(
            decision_id="test_decision_high_risk",
            decision_type="action",
            timestamp=datetime.now().isoformat(),
            intent=IntentV1(category="restart_service", action="restart_nginx", confidence=0.9),
            entities=[],
            overall_confidence=0.8,
            confidence_level="high",
            risk_level=RiskLevel.HIGH,
            original_request="restart nginx",
            next_stage="stage_b",
            processing_time_ms=100
        )
        
        observability, _ = self.resource_planner.create_resource_plan(
            self.steps, high_risk_decision, self.selection
        )
        
        # High-risk operations should have more comprehensive monitoring
        assert "system_load_average" in observability.metrics_to_collect
        assert len(observability.alerts_to_set) > 0
    
    def test_resource_constraints(self):
        """Test resource constraint calculation"""
        constraints = self.resource_planner.get_resource_constraints(self.steps, self.selection)
        
        assert "max_cpu_percent" in constraints
        assert "max_memory_mb" in constraints
        assert "max_execution_time_seconds" in constraints
        
        assert constraints["max_cpu_percent"] <= 100
        assert constraints["max_memory_mb"] > 0


class TestStageCPlanner:
    """Test Stage C Planner integration"""
    
    def setup_method(self):
        """Set up test fixtures"""
        self.planner = StageCPlanner()
        
        self.decision = DecisionV1(
            decision_id="test_decision_planner",
            decision_type="action",
            timestamp=datetime.now().isoformat(),
            intent=IntentV1(category="monitor_system", action="check_processes", confidence=0.9),
            entities=[EntityV1(type="service_name", value="nginx", confidence=0.9)],
            overall_confidence=0.8,
            confidence_level="high",
            risk_level=RiskLevel.MEDIUM,
            original_request="check nginx service and processes",
            next_stage="stage_b",
            processing_time_ms=100
        )
        
        self.selection = SelectionV1(
            selection_id="test_selection_setup",
            decision_id="test_decision_setup",
            selected_tools=[
                SelectedTool(
                    tool_name="systemctl",
                    justification="Check service status",
                    execution_order=1
                ),
                SelectedTool(
                    tool_name="ps",
                    justification="List processes",
                    execution_order=2
                )
            ],
            policy=ExecutionPolicy(
                requires_approval=False,
                risk_level=RiskLevel.MEDIUM,
                max_execution_time=60
            ),
            environment_requirements={},
            total_tools=2,
            selection_confidence=0.8,
            next_stage="stage_c",
            timestamp=datetime.now().isoformat(),
            processing_time_ms=100
        )
    
    def test_create_plan_success(self):
        """Test successful plan creation"""
        plan = self.planner.create_plan(self.decision, self.selection)
        
        assert isinstance(plan, PlanV1)
        assert len(plan.plan.steps) > 0
        assert len(plan.plan.safety_checks) > 0
        assert plan.execution_metadata.total_estimated_time > 0
        assert plan.processing_time_ms > 0
    
    def test_plan_structure_validation(self):
        """Test plan structure validation"""
        plan = self.planner.create_plan(self.decision, self.selection)
        
        # Validate plan structure
        is_valid, issues = self.planner.validate_plan(plan)
        assert is_valid
        assert len(issues) == 0
    
    def test_complex_plan_creation(self):
        """Test complex plan with multiple tools and dependencies"""
        complex_selection = SelectionV1(
            selection_id="test_selection_complex",
            decision_id="test_decision_complex",
            selected_tools=[
                SelectedTool(
                    tool_name="file_manager",
                    justification="Backup config",
                    execution_order=1
                ),
                SelectedTool(
                    tool_name="config_manager",
                    justification="Validate config",
                    execution_order=2,
                    depends_on=["file_manager"]
                ),
                SelectedTool(
                    tool_name="systemctl",
                    justification="Restart service",
                    execution_order=3,
                    depends_on=["config_manager"]
                )
            ],
            policy=ExecutionPolicy(
                risk_level=RiskLevel.HIGH,
                requires_approval=True,
                max_execution_time=60
            ),
            environment_requirements={"production_safe": True},
            total_tools=3,
            selection_confidence=0.8,
            next_stage="stage_c",
            timestamp=datetime.now().isoformat(),
            processing_time_ms=200
        )
        
        complex_decision = DecisionV1(
            decision_id="test_decision_complex",
            decision_type="action",
            timestamp=datetime.now().isoformat(),
            intent=IntentV1(category="modify_config", action="update_nginx_config", confidence=0.9),
            entities=[
                EntityV1(type="file_path", value="/etc/nginx/nginx.conf", confidence=0.9),
                EntityV1(type="service_name", value="nginx", confidence=0.9)
            ],
            overall_confidence=0.85,
            confidence_level="high",
            risk_level=RiskLevel.HIGH,
            original_request="update nginx configuration and restart service",
            next_stage="stage_b",
            processing_time_ms=150
        )
        
        plan = self.planner.create_plan(complex_decision, complex_selection)
        
        assert len(plan.plan.steps) == 3
        assert len(plan.plan.safety_checks) > 5  # High-risk should have many safety checks
        assert len(plan.plan.rollback_plan) > 0  # Should have rollback procedures
        assert len(plan.execution_metadata.approval_points) > 0  # Should require approvals
    
    def test_fallback_plan_creation(self):
        """Test fallback plan creation when main planning fails"""
        # Create invalid selection that should trigger fallback
        invalid_selection = SelectionV1(
            selection_id="test_selection_invalid",
            decision_id="test_decision_invalid",
            selected_tools=[],  # Empty tools should trigger fallback
            policy=ExecutionPolicy(
                requires_approval=False,
                risk_level=RiskLevel.LOW,
                max_execution_time=30
            ),
            environment_requirements={},
            total_tools=0,
            selection_confidence=0.8,
            next_stage="stage_c",
            timestamp=datetime.now().isoformat(),
            processing_time_ms=100
        )
        
        plan = self.planner.create_plan(self.decision, invalid_selection)
        
        # Should still create a plan (fallback)
        assert isinstance(plan, PlanV1)
        assert len(plan.plan.steps) > 0
        assert "fallback" in plan.execution_metadata.risk_factors
    
    def test_plan_optimization(self):
        """Test plan optimization functionality"""
        plan = self.planner.create_plan(self.decision, self.selection)
        optimized_plan = self.planner.optimize_plan(plan)
        
        assert isinstance(optimized_plan, PlanV1)
        assert "plan_optimized" in optimized_plan.execution_metadata.risk_factors
    
    def test_health_status(self):
        """Test planner health status"""
        health = self.planner.get_health_status()
        
        assert health["status"] == "healthy"
        assert health["component"] == "stage_c_planner"
        assert "statistics" in health
        assert "components" in health
    
    def test_statistics_tracking(self):
        """Test statistics tracking"""
        initial_stats = self.planner.stats.copy()
        
        # Create a plan
        self.planner.create_plan(self.decision, self.selection)
        
        # Check statistics were updated
        assert self.planner.stats["plans_created"] == initial_stats["plans_created"] + 1
        assert self.planner.stats["total_processing_time_ms"] > initial_stats["total_processing_time_ms"]


class TestErrorHandling:
    """Test error handling and edge cases"""
    
    def setup_method(self):
        """Set up test fixtures"""
        self.planner = StageCPlanner()
    
    def test_invalid_decision_handling(self):
        """Test handling of invalid decision data"""
        invalid_decision = DecisionV1(
            decision_id="test_decision_invalid",
            decision_type="action",
            timestamp=datetime.now().isoformat(),
            intent=IntentV1(category="unknown_category", action="unknown_action", confidence=0.5),
            entities=[],
            overall_confidence=0.8,
            confidence_level="high",
            risk_level=RiskLevel.LOW,
            original_request="invalid request",
            next_stage="stage_b",
            processing_time_ms=100
        )
        
        valid_selection = SelectionV1(
            selection_id="test_selection_valid",
            decision_id="test_decision_valid",
            selected_tools=[
                SelectedTool(tool_name="ps", justification="List processes", execution_order=1)
            ],
            policy=ExecutionPolicy(
                requires_approval=False,
                risk_level=RiskLevel.LOW,
                max_execution_time=30
            ),
            environment_requirements={},
            total_tools=1,
            selection_confidence=0.8,
            next_stage="stage_c",
            timestamp=datetime.now().isoformat(),
            processing_time_ms=100
        )
        
        # Should still create a plan (possibly fallback)
        plan = self.planner.create_plan(invalid_decision, valid_selection)
        assert isinstance(plan, PlanV1)
    
    def test_empty_selection_handling(self):
        """Test handling of empty tool selection"""
        valid_decision = DecisionV1(
            decision_id="test_decision_valid",
            decision_type="action",
            timestamp=datetime.now().isoformat(),
            intent=IntentV1(category="monitor_system", action="check_status", confidence=0.9),
            entities=[],
            overall_confidence=0.8,
            confidence_level="high",
            risk_level=RiskLevel.LOW,
            original_request="check system status",
            next_stage="stage_b",
            processing_time_ms=100
        )
        
        empty_selection = SelectionV1(
            selection_id="test_selection_empty",
            decision_id="test_decision_empty",
            selected_tools=[],
            policy=ExecutionPolicy(
                requires_approval=False,
                risk_level=RiskLevel.LOW,
                max_execution_time=30
            ),
            environment_requirements={},
            total_tools=0,
            selection_confidence=0.8,
            next_stage="stage_c",
            timestamp=datetime.now().isoformat(),
            processing_time_ms=100
        )
        
        plan = self.planner.create_plan(valid_decision, empty_selection)
        assert isinstance(plan, PlanV1)
        assert len(plan.plan.steps) > 0  # Should create fallback steps
    
    def test_dependency_error_recovery(self):
        """Test recovery from dependency resolution errors"""
        # This would be tested with the dependency resolver directly
        resolver = DependencyResolver()
        
        # Create steps with circular dependencies
        circular_steps = [
            ExecutionStep(
                id="step_001",
                description="Step 1",
                tool="ps",
                estimated_duration=5,
                failure_handling="Continue",
                depends_on=["step_002"]
            ),
            ExecutionStep(
                id="step_002",
                description="Step 2",
                tool="systemctl",
                estimated_duration=10,
                failure_handling="Continue",
                depends_on=["step_001"]
            )
        ]
        
        with pytest.raises(DependencyError):
            resolver.resolve_dependencies(circular_steps)


class TestPerformance:
    """Test performance characteristics"""
    
    def setup_method(self):
        """Set up test fixtures"""
        self.planner = StageCPlanner()
    
    def test_planning_performance(self):
        """Test planning performance with reasonable execution time"""
        decision = DecisionV1(
            decision_id="test_decision_performance",
            decision_type="action",
            timestamp=datetime.now().isoformat(),
            intent=IntentV1(category="monitor_system", action="comprehensive_check", confidence=0.9),
            entities=[
                EntityV1(type="service_name", value="nginx", confidence=0.9),
                EntityV1(type="service_name", value="mysql", confidence=0.8),
                EntityV1(type="file_path", value="/var/log/syslog", confidence=0.9)
            ],
            overall_confidence=0.8,
            confidence_level="high",
            risk_level=RiskLevel.MEDIUM,
            original_request="comprehensive system monitoring",
            next_stage="stage_b",
            processing_time_ms=100
        )
        
        selection = SelectionV1(
            selection_id="test_selection_selection",
            decision_id="test_decision_selection",
            selected_tools=[
                SelectedTool(tool_name="systemctl", justification="Check services", execution_order=1),
                SelectedTool(tool_name="ps", justification="List processes", execution_order=2),
                SelectedTool(tool_name="journalctl", justification="Check logs", execution_order=3),
                SelectedTool(tool_name="docker", justification="Check containers", execution_order=4),
                SelectedTool(tool_name="network_tools", justification="Check network", execution_order=5)
            ],
            policy=ExecutionPolicy(
                requires_approval=False,
                risk_level=RiskLevel.MEDIUM,
                max_execution_time=60
            ),
            environment_requirements={},
            total_tools=5,
            selection_confidence=0.8,
            next_stage="stage_c",
            timestamp=datetime.now().isoformat(),
            processing_time_ms=200
        )
        
        import time
        start_time = time.time()
        plan = self.planner.create_plan(decision, selection)
        end_time = time.time()
        
        processing_time_ms = (end_time - start_time) * 1000
        
        # Should complete within reasonable time (excluding LLM latency)
        assert processing_time_ms < 1000  # Less than 1 second
        assert isinstance(plan, PlanV1)
        assert len(plan.plan.steps) == 5
    
    def test_concurrent_planning(self):
        """Test concurrent plan creation"""
        import threading
        import time
        
        decision = DecisionV1(
            decision_id="test_decision_concurrent",
            decision_type="action",
            timestamp=datetime.now().isoformat(),
            intent=IntentV1(category="monitor_system", action="check_status", confidence=0.9),
            entities=[],
            overall_confidence=0.8,
            confidence_level="high",
            risk_level=RiskLevel.LOW,
            original_request="check system status",
            next_stage="stage_b",
            processing_time_ms=100
        )
        
        selection = SelectionV1(
            selection_id="test_selection_selection",
            decision_id="test_decision_selection",
            selected_tools=[
                SelectedTool(tool_name="ps", justification="List processes", execution_order=1)
            ],
            policy=ExecutionPolicy(
                requires_approval=False,
                risk_level=RiskLevel.LOW,
                max_execution_time=30
            ),
            environment_requirements={},
            total_tools=1,
            selection_confidence=0.8,
            next_stage="stage_c",
            timestamp=datetime.now().isoformat(),
            processing_time_ms=100
        )
        
        results = []
        errors = []
        
        def create_plan_thread():
            try:
                plan = self.planner.create_plan(decision, selection)
                results.append(plan)
            except Exception as e:
                errors.append(e)
        
        # Create multiple threads
        threads = []
        for _ in range(3):
            thread = threading.Thread(target=create_plan_thread)
            threads.append(thread)
            thread.start()
        
        # Wait for all threads to complete
        for thread in threads:
            thread.join()
        
        # Check results
        assert len(errors) == 0
        assert len(results) == 3
        assert all(isinstance(plan, PlanV1) for plan in results)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])