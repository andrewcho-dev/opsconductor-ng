"""
Stage Communication Validator - Phase 5

Validates communication and data flow between individual pipeline stages.
Ensures schema compatibility and proper error propagation.
"""

import asyncio
import time
from typing import Dict, List, Any, Optional, Type
from dataclasses import dataclass
from enum import Enum

from pipeline.stages.stage_a.classifier import StageAClassifier
from pipeline.stages.stage_b.selector import StageBSelector
from pipeline.stages.stage_c.planner import StageCPlanner
from pipeline.stages.stage_d.answerer import StageDAnswerer
from pipeline.schemas.decision_v1 import DecisionV1, DecisionType, RiskLevel, ConfidenceLevel, IntentV1
from pipeline.schemas.selection_v1 import SelectionV1, SelectedTool, ExecutionPolicy, RiskLevel as SelectionRiskLevel
from pipeline.schemas.plan_v1 import PlanV1, ExecutionPlan, ExecutionStep, ExecutionMetadata
from pipeline.schemas.response_v1 import ResponseV1, ResponseType


class StageTransition(Enum):
    """Pipeline stage transitions."""
    A_TO_B = "stage_a_to_stage_b"
    B_TO_C = "stage_b_to_stage_c"
    C_TO_D = "stage_c_to_stage_d"


@dataclass
class CommunicationTestCase:
    """Test case for stage-to-stage communication."""
    name: str
    transition: StageTransition
    input_data: Any
    expected_output_type: Type
    description: str = ""


@dataclass
class CommunicationTestResult:
    """Result of a stage communication test."""
    test_case: CommunicationTestCase
    success: bool
    output_data: Any
    execution_time_ms: float
    error_message: Optional[str] = None
    validation_details: Dict[str, Any] = None


class StageCommunicationValidator:
    """
    Validates communication between pipeline stages.
    
    Tests:
    - Schema compatibility between stages
    - Data transformation correctness
    - Error propagation
    - Performance characteristics
    """
    
    def __init__(self, llm_client=None):
        """Initialize the stage communication validator."""
        # Initialize LLM client if not provided
        if llm_client is None:
            from llm.ollama_client import OllamaClient
            default_config = {
                "base_url": "http://localhost:11434",
                "default_model": "llama2",
                "timeout": 30
            }
            llm_client = OllamaClient(default_config)
        
        self.llm_client = llm_client
        self.stage_a = StageAClassifier(llm_client)
        self.stage_b = StageBSelector(llm_client)
        self.stage_c = StageCPlanner(llm_client)
        self.stage_d = StageDAnswerer(llm_client)
        
        self.test_results: List[CommunicationTestResult] = []
    
    def get_standard_test_cases(self) -> List[CommunicationTestCase]:
        """Get standard communication test cases."""
        return [
            # Stage A → Stage B tests
            CommunicationTestCase(
                name="a_to_b_information_request",
                transition=StageTransition.A_TO_B,
                input_data=self._create_stage_a_output(
                    DecisionType.INFO,
                    RiskLevel.LOW,
                    "Check server status"
                ),
                expected_output_type=DecisionV1,
                description="Information request from Stage A to Stage B"
            ),
            CommunicationTestCase(
                name="a_to_b_action_request",
                transition=StageTransition.A_TO_B,
                input_data=self._create_stage_a_output(
                    DecisionType.ACTION,
                    RiskLevel.MEDIUM,
                    "Restart nginx service"
                ),
                expected_output_type=DecisionV1,
                description="Action request from Stage A to Stage B"
            ),
            CommunicationTestCase(
                name="a_to_b_deployment_request",
                transition=StageTransition.A_TO_B,
                input_data=self._create_stage_a_output(
                    DecisionType.ACTION,
                    RiskLevel.HIGH,
                    "Deploy new API version"
                ),
                expected_output_type=DecisionV1,
                description="Deployment request from Stage A to Stage B"
            ),
            CommunicationTestCase(
                name="a_to_b_emergency_request",
                transition=StageTransition.A_TO_B,
                input_data=self._create_stage_a_output(
                    DecisionType.ACTION,
                    RiskLevel.CRITICAL,
                    "Database is down"
                ),
                expected_output_type=DecisionV1,
                description="Emergency request from Stage A to Stage B"
            ),
            
            # Stage B → Stage C tests
            CommunicationTestCase(
                name="b_to_c_with_capabilities",
                transition=StageTransition.B_TO_C,
                input_data=self._create_stage_b_output(
                    DecisionType.ACTION,
                    ["system_monitoring", "service_management"]
                ),
                expected_output_type=DecisionV1,
                description="Stage B output with capabilities to Stage C"
            ),
            CommunicationTestCase(
                name="b_to_c_deployment_capabilities",
                transition=StageTransition.B_TO_C,
                input_data=self._create_stage_b_output(
                    DecisionType.ACTION,
                    ["kubernetes_deployment", "health_monitoring", "rollback_capability"]
                ),
                expected_output_type=DecisionV1,
                description="Deployment capabilities from Stage B to Stage C"
            ),
            CommunicationTestCase(
                name="b_to_c_emergency_capabilities",
                transition=StageTransition.B_TO_C,
                input_data=self._create_stage_b_output(
                    DecisionType.ACTION,
                    ["database_recovery", "backup_restoration", "failover_management"]
                ),
                expected_output_type=DecisionV1,
                description="Emergency capabilities from Stage B to Stage C"
            ),
            
            # Stage C → Stage D tests
            CommunicationTestCase(
                name="c_to_d_execution_plan",
                transition=StageTransition.C_TO_D,
                input_data=self._create_stage_c_output(
                    DecisionType.ACTION,
                    ["Check system status", "Generate report"]
                ),
                expected_output_type=ResponseV1,
                description="Execution plan from Stage C to Stage D"
            ),
            CommunicationTestCase(
                name="c_to_d_deployment_plan",
                transition=StageTransition.C_TO_D,
                input_data=self._create_stage_c_output(
                    DecisionType.ACTION,
                    ["Backup current version", "Deploy new version", "Run health checks", "Update load balancer"]
                ),
                expected_output_type=ResponseV1,
                description="Deployment plan from Stage C to Stage D"
            ),
            CommunicationTestCase(
                name="c_to_d_emergency_plan",
                transition=StageTransition.C_TO_D,
                input_data=self._create_stage_c_output(
                    DecisionType.ACTION,
                    ["Stop failing service", "Restore from backup", "Verify system integrity"]
                ),
                expected_output_type=ResponseV1,
                description="Emergency plan from Stage C to Stage D"
            )
        ]
    
    def _create_stage_a_output(
        self, 
        decision_type: DecisionType, 
        risk_level: RiskLevel, 
        user_request: str
    ) -> DecisionV1:
        """Create a mock Stage A output for testing."""
        from datetime import datetime
        return DecisionV1(
            decision_id=f"test_{int(time.time())}",
            decision_type=decision_type,
            timestamp=datetime.now().isoformat(),
            intent=IntentV1(
                category="test",
                action="test_action",
                confidence=0.95
            ),
            entities=[],
            overall_confidence=0.95,
            confidence_level=ConfidenceLevel.HIGH,
            risk_level=risk_level,
            original_request=user_request,
            context={"test": True},
            requires_approval=False,
            next_stage="stage_b"
        )
    
    def _create_stage_b_output(
        self, 
        decision_type: DecisionType, 
        capabilities: List[str]
    ) -> SelectionV1:
        """Create a mock Stage B output for testing."""
        from datetime import datetime
        
        selected_tools = [
            SelectedTool(
                tool_name=tool,
                justification=f"Selected {tool} for testing purposes",
                inputs_needed=[],
                execution_order=i+1,
                depends_on=[]
            ) for i, tool in enumerate(capabilities)
        ]
        
        policy = ExecutionPolicy(
            requires_approval=False,
            production_environment=False,
            risk_level=SelectionRiskLevel.LOW,
            max_execution_time=300,
            parallel_execution=False,
            rollback_required=False
        )
        
        return SelectionV1(
            selection_id=f"sel_test_{int(time.time())}",
            decision_id=f"dec_test_{int(time.time())}",
            timestamp=datetime.now().isoformat(),
            selected_tools=selected_tools,
            total_tools=len(capabilities),
            policy=policy,
            additional_inputs_needed=[],
            environment_requirements={},
            selection_confidence=0.9,
            next_stage="stage_c",
            ready_for_execution=True
        )
    
    def _create_stage_c_output(
        self, 
        decision_type: DecisionType, 
        execution_steps: List[str]
    ) -> PlanV1:
        """Create a mock Stage C output for testing."""
        from datetime import datetime
        
        steps = [
            ExecutionStep(
                id=f"step_{i+1:03d}",
                description=step,
                tool="test_tool",
                inputs={},
                preconditions=[],
                success_criteria=["step_completed"],
                failure_handling="Log error and continue",
                estimated_duration=30,
                depends_on=[],
                execution_order=i+1
            ) for i, step in enumerate(execution_steps)
        ]
        
        plan = ExecutionPlan(
            steps=steps,
            safety_checks=[],
            rollback_plan=[],
            observability={}
        )
        
        metadata = ExecutionMetadata(
            total_estimated_time=len(execution_steps) * 30,
            risk_factors=[],
            approval_points=[],
            checkpoint_steps=[]
        )
        
        return PlanV1(
            plan=plan,
            execution_metadata=metadata,
            timestamp=datetime.now().isoformat(),
            processing_time_ms=100
        )
    
    async def test_stage_communication(
        self, 
        test_case: CommunicationTestCase
    ) -> CommunicationTestResult:
        """
        Test communication between two specific stages.
        
        Args:
            test_case: The communication test case to execute
            
        Returns:
            CommunicationTestResult with execution details
        """
        start_time = time.time()
        
        try:
            # Execute the appropriate stage transition
            if test_case.transition == StageTransition.A_TO_B:
                output = await self._test_a_to_b(test_case.input_data)
            elif test_case.transition == StageTransition.B_TO_C:
                output = await self._test_b_to_c(test_case.input_data)
            elif test_case.transition == StageTransition.C_TO_D:
                output = await self._test_c_to_d(test_case.input_data)
            else:
                raise ValueError(f"Unknown transition: {test_case.transition}")
            
            execution_time = (time.time() - start_time) * 1000
            
            # Validate the output
            validation_details = self._validate_stage_output(
                test_case, 
                output
            )
            
            success = validation_details["overall_success"]
            
            return CommunicationTestResult(
                test_case=test_case,
                success=success,
                output_data=output,
                execution_time_ms=execution_time,
                validation_details=validation_details
            )
            
        except Exception as e:
            execution_time = (time.time() - start_time) * 1000
            return CommunicationTestResult(
                test_case=test_case,
                success=False,
                output_data=None,
                execution_time_ms=execution_time,
                error_message=f"Stage communication failed: {str(e)}"
            )
    
    async def _test_a_to_b(self, stage_a_output: DecisionV1) -> SelectionV1:
        """Test Stage A → Stage B communication."""
        return await self.stage_b.select_tools(stage_a_output)
    
    async def _test_b_to_c(self, stage_b_output: SelectionV1) -> PlanV1:
        """Test Stage B → Stage C communication."""
        # Stage C needs both decision and selection
        decision = DecisionV1(
            decision_id=stage_b_output.decision_id,
            decision_type=DecisionType.ACTION,
            timestamp=stage_b_output.timestamp,
            intent=IntentV1(category="test", action="test", confidence=0.9),
            entities=[],
            overall_confidence=0.9,
            confidence_level=ConfidenceLevel.HIGH,
            risk_level=RiskLevel.LOW,
            original_request="test request",
            context={},
            requires_approval=False,
            next_stage="stage_b"
        )
        return self.stage_c.create_plan(decision, stage_b_output)
    
    async def _test_c_to_d(self, stage_c_output: PlanV1) -> ResponseV1:
        """Test Stage C → Stage D communication."""
        # Stage D needs decision, selection, and plan
        decision = DecisionV1(
            decision_id="test_decision",
            decision_type=DecisionType.ACTION,
            timestamp=stage_c_output.timestamp,
            intent=IntentV1(category="test", action="test", confidence=0.9),
            entities=[],
            overall_confidence=0.9,
            confidence_level=ConfidenceLevel.HIGH,
            risk_level=RiskLevel.LOW,
            original_request="test request",
            context={},
            requires_approval=False,
            next_stage="stage_d"
        )
        selection = SelectionV1(
            selection_id=f"sel_{stage_c_output.timestamp}",
            decision_id="test_decision",
            timestamp=stage_c_output.timestamp,
            selected_tools=[],
            total_tools=0,
            policy=ExecutionPolicy(
                requires_approval=False,
                production_environment=False,
                risk_level=SelectionRiskLevel.LOW,
                max_execution_time=300,
                parallel_execution=False,
                rollback_required=False
            ),
            additional_inputs_needed=[],
            environment_requirements={},
            selection_confidence=0.9,
            next_stage="stage_d",
            ready_for_execution=True
        )
        return await self.stage_d.generate_response(decision, selection, stage_c_output)
    
    def _validate_stage_output(
        self, 
        test_case: CommunicationTestCase, 
        output: Any
    ) -> Dict[str, Any]:
        """
        Validate stage output against expectations.
        
        Args:
            test_case: The test case with expectations
            output: The actual stage output
            
        Returns:
            Dictionary with validation details
        """
        validation_details = {
            "overall_success": True,
            "checks": {}
        }
        
        # Check output type
        expected_type = test_case.expected_output_type
        actual_type = type(output)
        
        type_match = isinstance(output, expected_type)
        validation_details["checks"]["output_type"] = {
            "passed": type_match,
            "expected": expected_type.__name__,
            "actual": actual_type.__name__
        }
        
        if not type_match:
            validation_details["overall_success"] = False
            return validation_details
        
        # Validate DecisionV1 specific fields
        if isinstance(output, DecisionV1):
            # Check required fields
            required_fields = [
                "request_id", "user_request", "request_type", 
                "priority", "entities", "capabilities", 
                "execution_plan", "confidence_score"
            ]
            
            for field in required_fields:
                field_present = hasattr(output, field) and getattr(output, field) is not None
                validation_details["checks"][f"field_{field}"] = {
                    "passed": field_present,
                    "expected": "present",
                    "actual": "present" if field_present else "missing"
                }
                
                if not field_present:
                    validation_details["overall_success"] = False
            
            # Check confidence score range
            if hasattr(output, "confidence_score"):
                confidence_valid = 0.0 <= output.confidence_score <= 1.0
                validation_details["checks"]["confidence_range"] = {
                    "passed": confidence_valid,
                    "expected": "0.0 <= score <= 1.0",
                    "actual": output.confidence_score
                }
                
                if not confidence_valid:
                    validation_details["overall_success"] = False
        
        # Validate ResponseV1 specific fields
        elif isinstance(output, ResponseV1):
            # Check required fields
            required_fields = ["response_type", "message", "confidence"]
            
            for field in required_fields:
                field_present = hasattr(output, field) and getattr(output, field) is not None
                validation_details["checks"][f"field_{field}"] = {
                    "passed": field_present,
                    "expected": "present",
                    "actual": "present" if field_present else "missing"
                }
                
                if not field_present:
                    validation_details["overall_success"] = False
            
            # Check response type is valid
            if hasattr(output, "response_type"):
                type_valid = isinstance(output.response_type, ResponseType)
                validation_details["checks"]["response_type_valid"] = {
                    "passed": type_valid,
                    "expected": "ResponseType enum",
                    "actual": type(output.response_type).__name__
                }
                
                if not type_valid:
                    validation_details["overall_success"] = False
        
        return validation_details
    
    async def run_communication_test_suite(
        self, 
        test_cases: Optional[List[CommunicationTestCase]] = None
    ) -> Dict[str, Any]:
        """
        Run a complete stage communication test suite.
        
        Args:
            test_cases: Optional list of test cases. If None, uses standard test cases.
            
        Returns:
            Dictionary with test suite results and summary
        """
        if test_cases is None:
            test_cases = self.get_standard_test_cases()
        
        print(f"🔗 Running stage communication test suite with {len(test_cases)} test cases...")
        
        # Run all test cases
        results = []
        for i, test_case in enumerate(test_cases, 1):
            print(f"  [{i}/{len(test_cases)}] Testing: {test_case.name}")
            result = await self.test_stage_communication(test_case)
            results.append(result)
            
            # Print immediate result
            status = "✅ PASS" if result.success else "❌ FAIL"
            print(f"    {status} ({result.execution_time_ms:.1f}ms)")
            if not result.success and result.error_message:
                print(f"    Error: {result.error_message}")
        
        # Store results
        self.test_results.extend(results)
        
        # Calculate summary statistics
        total_tests = len(results)
        passed_tests = sum(1 for r in results if r.success)
        failed_tests = total_tests - passed_tests
        
        avg_execution_time = sum(r.execution_time_ms for r in results) / total_tests
        
        # Group results by transition
        results_by_transition = {}
        for result in results:
            transition = result.test_case.transition.value
            if transition not in results_by_transition:
                results_by_transition[transition] = []
            results_by_transition[transition].append(result)
        
        summary = {
            "total_tests": total_tests,
            "passed_tests": passed_tests,
            "failed_tests": failed_tests,
            "success_rate": (passed_tests / total_tests * 100) if total_tests > 0 else 0.0,
            "avg_execution_time_ms": avg_execution_time,
            "results_by_transition": {
                transition: {
                    "total": len(transition_results),
                    "passed": sum(1 for r in transition_results if r.success),
                    "avg_time_ms": sum(r.execution_time_ms for r in transition_results) / len(transition_results)
                }
                for transition, transition_results in results_by_transition.items()
            },
            "detailed_results": results
        }
        
        # Print summary
        print(f"\n📊 Stage Communication Test Summary:")
        print(f"  Total Tests: {total_tests}")
        print(f"  Passed: {passed_tests} ({passed_tests/total_tests*100:.1f}%)")
        print(f"  Failed: {failed_tests}")
        print(f"  Average Execution Time: {avg_execution_time:.1f}ms")
        
        for transition, stats in summary["results_by_transition"].items():
            print(f"  {transition}: {stats['passed']}/{stats['total']} passed")
        
        return summary
    
    async def test_error_propagation(self) -> Dict[str, Any]:
        """
        Test error propagation between stages.
        
        Returns:
            Dictionary with error propagation test results
        """
        print("🚨 Testing error propagation between stages...")
        
        error_tests = []
        
        # Test Stage A error handling
        try:
            # This should trigger an error in Stage A
            invalid_decision = self._create_stage_a_output(
                DecisionType.INFO,
                RiskLevel.LOW,
                ""  # Empty request should trigger error handling
            )
            
            result = await self.stage_b.select_tools(invalid_decision)
            error_tests.append({
                "stage": "stage_b_error_handling",
                "success": True,
                "message": "Stage B handled invalid input gracefully"
            })
        except Exception as e:
            error_tests.append({
                "stage": "stage_b_error_handling",
                "success": False,
                "message": f"Stage B failed to handle invalid input: {str(e)}"
            })
        
        # Test Stage C error handling
        try:
            # Create tool selection with no tools
            empty_tool_selection = self._create_stage_b_output(
                DecisionType.ACTION,
                []  # Empty tools should trigger error handling
            )
            
            result = await self.stage_c.create_plan(
                self._create_stage_a_output(DecisionType.ACTION, RiskLevel.MEDIUM, "Test request"),
                empty_tool_selection
            )
            error_tests.append({
                "stage": "stage_c_error_handling",
                "success": True,
                "message": "Stage C handled missing capabilities gracefully"
            })
        except Exception as e:
            error_tests.append({
                "stage": "stage_c_error_handling",
                "success": False,
                "message": f"Stage C failed to handle missing capabilities: {str(e)}"
            })
        
        # Test Stage D error handling
        try:
            # Create execution plan with no steps
            empty_execution_plan = self._create_stage_c_output(
                DecisionType.ACTION,
                []  # Empty steps should trigger error handling
            )
            
            result = await self.stage_d.generate_response(
                self._create_stage_a_output(DecisionType.ACTION, RiskLevel.MEDIUM, "Test request"),
                self._create_stage_b_output(DecisionType.ACTION, ["test_tool"]),
                empty_execution_plan
            )
            error_tests.append({
                "stage": "stage_d_error_handling",
                "success": True,
                "message": "Stage D handled empty execution plan gracefully"
            })
        except Exception as e:
            error_tests.append({
                "stage": "stage_d_error_handling",
                "success": False,
                "message": f"Stage D failed to handle empty execution plan: {str(e)}"
            })
        
        # Calculate summary
        total_error_tests = len(error_tests)
        passed_error_tests = sum(1 for t in error_tests if t["success"])
        
        summary = {
            "total_error_tests": total_error_tests,
            "passed_error_tests": passed_error_tests,
            "error_handling_success_rate": (passed_error_tests / total_error_tests * 100) if total_error_tests > 0 else 0.0,
            "error_test_details": error_tests
        }
        
        print(f"  Error Handling Tests: {passed_error_tests}/{total_error_tests} passed")
        
        return summary