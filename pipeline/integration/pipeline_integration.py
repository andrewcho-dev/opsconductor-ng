"""
Pipeline Integration Tester - Phase 5

Comprehensive end-to-end integration testing for the 4-stage pipeline.
Validates complete data flow from user request to final response.
"""

import asyncio
import time
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
from enum import Enum

from pipeline.orchestrator import PipelineOrchestrator, PipelineResult
from pipeline.schemas.decision_v1 import DecisionV1, DecisionType, RiskLevel
from pipeline.schemas.response_v1 import ResponseV1, ResponseType


class IntegrationTestType(Enum):
    """Types of integration tests."""
    BASIC_FLOW = "basic_flow"
    ERROR_HANDLING = "error_handling"
    PERFORMANCE = "performance"
    CONCURRENT = "concurrent"
    EDGE_CASES = "edge_cases"


@dataclass
class IntegrationTestCase:
    """Integration test case definition."""
    name: str
    test_type: IntegrationTestType
    user_request: str
    expected_response_type: ResponseType
    expected_decision_type: Optional[DecisionType] = None
    expected_risk_level: Optional[RiskLevel] = None
    timeout_seconds: float = 30.0
    description: str = ""


@dataclass
class IntegrationTestResult:
    """Result of an integration test."""
    test_case: IntegrationTestCase
    success: bool
    pipeline_result: Optional[PipelineResult]
    execution_time_ms: float
    error_message: Optional[str] = None
    validation_details: Dict[str, Any] = None


class PipelineIntegrationTester:
    """
    Comprehensive integration tester for the OpsConductor pipeline.
    
    Validates:
    - End-to-end data flow
    - Schema compatibility across stages
    - Error handling and recovery
    - Performance characteristics
    - Concurrent processing
    """
    
    def __init__(self):
        """Initialize the integration tester."""
        self.orchestrator = PipelineOrchestrator()
        self.test_results: List[IntegrationTestResult] = []
    
    def get_standard_test_cases(self) -> List[IntegrationTestCase]:
        """Get standard integration test cases covering common scenarios."""
        return [
            # Basic flow tests
            IntegrationTestCase(
                name="basic_information_request",
                test_type=IntegrationTestType.BASIC_FLOW,
                user_request="What is the current status of the web server?",
                expected_response_type=ResponseType.INFORMATION,
                expected_decision_type=DecisionType.INFO,
                expected_risk_level=RiskLevel.LOW,
                description="Basic information request flow"
            ),
            IntegrationTestCase(
                name="basic_action_request",
                test_type=IntegrationTestType.BASIC_FLOW,
                user_request="Restart the nginx service on web-01",
                expected_response_type=ResponseType.PLAN_SUMMARY,
                expected_decision_type=DecisionType.ACTION,
                expected_risk_level=RiskLevel.MEDIUM,
                description="Basic action request flow"
            ),
            IntegrationTestCase(
                name="complex_deployment_request",
                test_type=IntegrationTestType.BASIC_FLOW,
                user_request="Deploy the new API version to production with zero downtime",
                expected_response_type=ResponseType.APPROVAL_REQUEST,
                expected_decision_type=DecisionType.ACTION,
                expected_risk_level=RiskLevel.HIGH,
                description="Complex deployment requiring approval"
            ),
            IntegrationTestCase(
                name="emergency_response",
                test_type=IntegrationTestType.BASIC_FLOW,
                user_request="URGENT: Database is down, need immediate recovery",
                expected_response_type=ResponseType.EXECUTION_READY,
                expected_decision_type=DecisionType.ACTION,
                expected_risk_level=RiskLevel.CRITICAL,
                description="Emergency response flow"
            ),
            
            # Edge cases
            IntegrationTestCase(
                name="empty_request",
                test_type=IntegrationTestType.EDGE_CASES,
                user_request="",
                expected_response_type=ResponseType.CLARIFICATION,
                description="Empty user request"
            ),
            IntegrationTestCase(
                name="very_long_request",
                test_type=IntegrationTestType.EDGE_CASES,
                user_request="Please " + "help me " * 100 + "with the server",
                expected_response_type=ResponseType.CLARIFICATION,
                description="Very long user request"
            ),
            IntegrationTestCase(
                name="ambiguous_request",
                test_type=IntegrationTestType.EDGE_CASES,
                user_request="Fix it",
                expected_response_type=ResponseType.CLARIFICATION,
                description="Ambiguous user request"
            ),
            IntegrationTestCase(
                name="mixed_language_request",
                test_type=IntegrationTestType.EDGE_CASES,
                user_request="Restart el servidor web por favor",
                expected_response_type=ResponseType.CLARIFICATION,
                description="Mixed language request"
            ),
            
            # Performance tests
            IntegrationTestCase(
                name="performance_simple",
                test_type=IntegrationTestType.PERFORMANCE,
                user_request="Check server status",
                expected_response_type=ResponseType.INFORMATION,
                timeout_seconds=5.0,
                description="Simple request performance test"
            ),
            IntegrationTestCase(
                name="performance_complex",
                test_type=IntegrationTestType.PERFORMANCE,
                user_request="Deploy microservices to kubernetes cluster with health checks and monitoring",
                expected_response_type=ResponseType.APPROVAL_REQUEST,
                timeout_seconds=10.0,
                description="Complex request performance test"
            )
        ]
    
    async def run_integration_test(self, test_case: IntegrationTestCase) -> IntegrationTestResult:
        """
        Run a single integration test case.
        
        Args:
            test_case: The test case to execute
            
        Returns:
            IntegrationTestResult with execution details
        """
        start_time = time.time()
        
        try:
            # Execute the pipeline with timeout
            pipeline_result = await asyncio.wait_for(
                self.orchestrator.process_request(
                    test_case.user_request,
                    f"test_{test_case.name}"
                ),
                timeout=test_case.timeout_seconds
            )
            
            execution_time = (time.time() - start_time) * 1000
            
            # Validate the result
            validation_details = self._validate_pipeline_result(test_case, pipeline_result)
            success = validation_details["overall_success"]
            
            return IntegrationTestResult(
                test_case=test_case,
                success=success,
                pipeline_result=pipeline_result,
                execution_time_ms=execution_time,
                validation_details=validation_details
            )
            
        except asyncio.TimeoutError:
            execution_time = (time.time() - start_time) * 1000
            return IntegrationTestResult(
                test_case=test_case,
                success=False,
                pipeline_result=None,
                execution_time_ms=execution_time,
                error_message=f"Test timed out after {test_case.timeout_seconds} seconds"
            )
            
        except Exception as e:
            execution_time = (time.time() - start_time) * 1000
            return IntegrationTestResult(
                test_case=test_case,
                success=False,
                pipeline_result=None,
                execution_time_ms=execution_time,
                error_message=f"Test failed with exception: {str(e)}"
            )
    
    def _validate_pipeline_result(
        self, 
        test_case: IntegrationTestCase, 
        pipeline_result: PipelineResult
    ) -> Dict[str, Any]:
        """
        Validate pipeline result against test case expectations.
        
        Args:
            test_case: The test case with expectations
            pipeline_result: The actual pipeline result
            
        Returns:
            Dictionary with validation details
        """
        validation_details = {
            "overall_success": True,
            "checks": {}
        }
        
        # Check if pipeline succeeded
        if not pipeline_result.success:
            validation_details["checks"]["pipeline_success"] = {
                "passed": False,
                "expected": True,
                "actual": False,
                "message": f"Pipeline failed: {pipeline_result.error_message}"
            }
            validation_details["overall_success"] = False
        else:
            validation_details["checks"]["pipeline_success"] = {
                "passed": True,
                "expected": True,
                "actual": True
            }
        
        # Check response type
        if test_case.expected_response_type:
            actual_type = pipeline_result.response.type
            expected_type = test_case.expected_response_type
            
            type_match = actual_type == expected_type
            validation_details["checks"]["response_type"] = {
                "passed": type_match,
                "expected": expected_type.value,
                "actual": actual_type.value
            }
            
            if not type_match:
                validation_details["overall_success"] = False
        
        # Check intermediate results structure
        required_stages = ["stage_a", "stage_b", "stage_c", "stage_d"]
        for stage in required_stages:
            stage_present = stage in pipeline_result.intermediate_results
            validation_details["checks"][f"{stage}_present"] = {
                "passed": stage_present,
                "expected": True,
                "actual": stage_present
            }
            
            if not stage_present:
                validation_details["overall_success"] = False
        
        # Check Stage A classification if expected
        if test_case.expected_decision_type and "stage_a" in pipeline_result.intermediate_results:
            stage_a_result = pipeline_result.intermediate_results["stage_a"]
            if isinstance(stage_a_result, DecisionV1):
                actual_decision_type = stage_a_result.decision_type
                expected_decision_type = test_case.expected_decision_type
                
                decision_type_match = actual_decision_type == expected_decision_type
                validation_details["checks"]["decision_type"] = {
                    "passed": decision_type_match,
                    "expected": expected_decision_type.value,
                    "actual": actual_decision_type.value
                }
                
                if not decision_type_match:
                    validation_details["overall_success"] = False
        
        # Check risk level if expected
        if test_case.expected_risk_level and "stage_a" in pipeline_result.intermediate_results:
            stage_a_result = pipeline_result.intermediate_results["stage_a"]
            if isinstance(stage_a_result, DecisionV1):
                actual_risk_level = stage_a_result.risk_level
                expected_risk_level = test_case.expected_risk_level
                
                risk_level_match = actual_risk_level == expected_risk_level
                validation_details["checks"]["risk_level"] = {
                    "passed": risk_level_match,
                    "expected": expected_risk_level.value,
                    "actual": actual_risk_level.value
                }
                
                if not risk_level_match:
                    validation_details["overall_success"] = False
        
        # Check performance metrics
        if pipeline_result.metrics:
            performance_ok = pipeline_result.metrics.total_duration_ms < (test_case.timeout_seconds * 1000)
            validation_details["checks"]["performance"] = {
                "passed": performance_ok,
                "expected": f"< {test_case.timeout_seconds * 1000}ms",
                "actual": f"{pipeline_result.metrics.total_duration_ms:.2f}ms"
            }
            
            if not performance_ok:
                validation_details["overall_success"] = False
        
        return validation_details
    
    async def run_test_suite(
        self, 
        test_cases: Optional[List[IntegrationTestCase]] = None
    ) -> Dict[str, Any]:
        """
        Run a complete integration test suite.
        
        Args:
            test_cases: Optional list of test cases. If None, uses standard test cases.
            
        Returns:
            Dictionary with test suite results and summary
        """
        if test_cases is None:
            test_cases = self.get_standard_test_cases()
        
        print(f"🧪 Running integration test suite with {len(test_cases)} test cases...")
        
        # Run all test cases
        results = []
        for i, test_case in enumerate(test_cases, 1):
            print(f"  [{i}/{len(test_cases)}] Running: {test_case.name}")
            result = await self.run_integration_test(test_case)
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
        
        # Group results by test type
        results_by_type = {}
        for result in results:
            test_type = result.test_case.test_type.value
            if test_type not in results_by_type:
                results_by_type[test_type] = []
            results_by_type[test_type].append(result)
        
        summary = {
            "total_tests": total_tests,
            "passed_tests": passed_tests,
            "failed_tests": failed_tests,
            "success_rate": (passed_tests / total_tests * 100) if total_tests > 0 else 0.0,
            "avg_execution_time_ms": avg_execution_time,
            "results_by_type": {
                test_type: {
                    "total": len(type_results),
                    "passed": sum(1 for r in type_results if r.success),
                    "avg_time_ms": sum(r.execution_time_ms for r in type_results) / len(type_results)
                }
                for test_type, type_results in results_by_type.items()
            },
            "detailed_results": results
        }
        
        # Print summary
        print(f"\n📊 Integration Test Suite Summary:")
        print(f"  Total Tests: {total_tests}")
        print(f"  Passed: {passed_tests} ({passed_tests/total_tests*100:.1f}%)")
        print(f"  Failed: {failed_tests}")
        print(f"  Average Execution Time: {avg_execution_time:.1f}ms")
        
        return summary
    
    async def run_concurrent_test(
        self, 
        user_request: str, 
        concurrent_requests: int = 5
    ) -> Dict[str, Any]:
        """
        Test concurrent request processing.
        
        Args:
            user_request: The request to send concurrently
            concurrent_requests: Number of concurrent requests
            
        Returns:
            Dictionary with concurrent test results
        """
        print(f"🔄 Running concurrent test with {concurrent_requests} requests...")
        
        start_time = time.time()
        
        # Create tasks for concurrent execution
        tasks = [
            self.orchestrator.process_request(user_request, f"concurrent_{i}")
            for i in range(concurrent_requests)
        ]
        
        # Execute all requests concurrently
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        total_time = (time.time() - start_time) * 1000
        
        # Analyze results
        successful_results = [r for r in results if isinstance(r, PipelineResult) and r.success]
        failed_results = [r for r in results if not isinstance(r, PipelineResult) or not r.success]
        
        if successful_results:
            avg_response_time = sum(r.metrics.total_duration_ms for r in successful_results) / len(successful_results)
            min_response_time = min(r.metrics.total_duration_ms for r in successful_results)
            max_response_time = max(r.metrics.total_duration_ms for r in successful_results)
        else:
            avg_response_time = min_response_time = max_response_time = 0.0
        
        summary = {
            "concurrent_requests": concurrent_requests,
            "successful_requests": len(successful_results),
            "failed_requests": len(failed_results),
            "success_rate": len(successful_results) / concurrent_requests * 100,
            "total_execution_time_ms": total_time,
            "avg_response_time_ms": avg_response_time,
            "min_response_time_ms": min_response_time,
            "max_response_time_ms": max_response_time,
            "throughput_requests_per_second": concurrent_requests / (total_time / 1000)
        }
        
        print(f"  Successful: {len(successful_results)}/{concurrent_requests}")
        print(f"  Success Rate: {summary['success_rate']:.1f}%")
        print(f"  Throughput: {summary['throughput_requests_per_second']:.1f} req/s")
        print(f"  Avg Response Time: {avg_response_time:.1f}ms")
        
        return summary
    
    def get_test_report(self) -> Dict[str, Any]:
        """Generate a comprehensive test report."""
        if not self.test_results:
            return {"message": "No test results available"}
        
        # Overall statistics
        total_tests = len(self.test_results)
        passed_tests = sum(1 for r in self.test_results if r.success)
        
        # Performance statistics
        execution_times = [r.execution_time_ms for r in self.test_results]
        execution_times.sort()
        
        def percentile(data: List[float], p: float) -> float:
            if not data:
                return 0.0
            index = int(len(data) * p / 100)
            return data[min(index, len(data) - 1)]
        
        # Failed tests details
        failed_tests = [r for r in self.test_results if not r.success]
        
        return {
            "summary": {
                "total_tests": total_tests,
                "passed_tests": passed_tests,
                "failed_tests": len(failed_tests),
                "success_rate": passed_tests / total_tests * 100 if total_tests > 0 else 0.0
            },
            "performance": {
                "avg_execution_time_ms": sum(execution_times) / len(execution_times),
                "min_execution_time_ms": min(execution_times),
                "max_execution_time_ms": max(execution_times),
                "p50_execution_time_ms": percentile(execution_times, 50),
                "p90_execution_time_ms": percentile(execution_times, 90),
                "p95_execution_time_ms": percentile(execution_times, 95)
            },
            "failed_tests": [
                {
                    "name": r.test_case.name,
                    "error": r.error_message,
                    "execution_time_ms": r.execution_time_ms
                }
                for r in failed_tests
            ]
        }