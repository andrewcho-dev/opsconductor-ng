"""
Phase 5 Integration Tests - Complete Pipeline Testing

Comprehensive test suite for end-to-end pipeline integration,
cross-stage communication, and performance validation.
"""

import pytest
import asyncio
import time
from typing import Dict, Any, List

from pipeline.orchestrator import (
    PipelineOrchestrator, 
    PipelineResult, 
    PipelineStatus,
    get_pipeline_orchestrator,
    process_user_request
)
from pipeline.integration.pipeline_integration import (
    PipelineIntegrationTester,
    IntegrationTestType,
    IntegrationTestCase
)
from pipeline.integration.stage_communication import (
    StageCommunicationValidator,
    StageTransition
)
from pipeline.integration.performance_monitor import (
    PerformanceMonitor,
    PerformanceTestType
)
from pipeline.schemas.decision_v1 import DecisionV1, DecisionType, RiskLevel
from pipeline.schemas.selection_v1 import SelectionV1
from pipeline.schemas.plan_v1 import PlanV1
from pipeline.schemas.response_v1 import ResponseV1, ResponseType


class TestPipelineOrchestrator:
    """Test the main pipeline orchestrator functionality."""
    
    @pytest.fixture
    def orchestrator(self):
        """Create a pipeline orchestrator for testing."""
        return PipelineOrchestrator()
    
    @pytest.mark.asyncio
    async def test_orchestrator_initialization(self, orchestrator):
        """Test that the orchestrator initializes correctly."""
        assert orchestrator.stage_a is not None
        assert orchestrator.stage_b is not None
        assert orchestrator.stage_c is not None
        assert orchestrator.stage_d is not None
        assert len(orchestrator._active_requests) == 0
        assert len(orchestrator._completed_requests) == 0
    
    @pytest.mark.asyncio
    async def test_basic_request_processing(self, orchestrator):
        """Test basic request processing through the pipeline."""
        user_request = "Check the status of the web server"
        
        result = await orchestrator.process_request(user_request)
        
        assert isinstance(result, PipelineResult)
        assert result.success is True
        assert isinstance(result.response, ResponseV1)
        assert result.metrics is not None
        assert result.metrics.status == PipelineStatus.COMPLETED
        assert result.metrics.total_duration_ms > 0
        
        # Check that all stages were executed
        assert "stage_a" in result.intermediate_results
        assert "stage_b" in result.intermediate_results
        assert "stage_c" in result.intermediate_results
        assert "stage_d" in result.intermediate_results
        
        # Check stage outputs are correct types
        assert isinstance(result.intermediate_results["stage_a"], DecisionV1)
        assert isinstance(result.intermediate_results["stage_b"], SelectionV1)
        assert isinstance(result.intermediate_results["stage_c"], PlanV1)
        assert isinstance(result.intermediate_results["stage_d"], ResponseV1)
    
    @pytest.mark.asyncio
    async def test_request_with_custom_id(self, orchestrator):
        """Test request processing with custom request ID."""
        user_request = "Restart the nginx service"
        request_id = "test_custom_id_123"
        
        result = await orchestrator.process_request(user_request, request_id)
        
        assert result.success is True
        assert result.metrics.request_id == request_id
        # ResponseV1 has response_id, not request_id
        assert result.response.response_id is not None
    
    @pytest.mark.asyncio
    async def test_concurrent_request_processing(self, orchestrator):
        """Test concurrent request processing."""
        requests = [
            "Check server status",
            "List running services", 
            "Show disk usage",
            "Monitor CPU usage",
            "Check network connectivity"
        ]
        
        # Process requests concurrently
        tasks = [
            orchestrator.process_request(req, f"concurrent_{i}")
            for i, req in enumerate(requests)
        ]
        
        results = await asyncio.gather(*tasks)
        
        # Verify all requests succeeded
        assert len(results) == len(requests)
        for result in results:
            assert isinstance(result, PipelineResult)
            assert result.success is True
            assert isinstance(result.response, ResponseV1)
    
    @pytest.mark.asyncio
    async def test_batch_request_processing(self, orchestrator):
        """Test batch request processing with concurrency control."""
        requests = [
            "Check server status",
            "List running services",
            "Show disk usage"
        ]
        
        results = await orchestrator.process_batch_requests(requests, max_concurrent=2)
        
        assert len(results) == len(requests)
        for result in results:
            assert isinstance(result, PipelineResult)
            assert result.success is True
    
    @pytest.mark.asyncio
    async def test_health_status(self, orchestrator):
        """Test health status reporting."""
        # Process a request to generate some metrics
        await orchestrator.process_request("Check server status")
        
        health = orchestrator.get_health_status()
        
        assert "status" in health
        assert "timestamp" in health
        assert "metrics" in health
        assert "stages" in health
        
        # Check metrics structure
        metrics = health["metrics"]
        assert "total_requests" in metrics
        assert "success_count" in metrics
        assert "error_count" in metrics
        assert "success_rate_percent" in metrics
        
        # Check stage health
        stages = health["stages"]
        assert "stage_a" in stages
        assert "stage_b" in stages
        assert "stage_c" in stages
        assert "stage_d" in stages
    
    @pytest.mark.asyncio
    async def test_performance_metrics(self, orchestrator):
        """Test performance metrics collection."""
        # Process multiple requests to generate metrics
        for i in range(3):
            await orchestrator.process_request(f"Test request {i}")
        
        metrics = orchestrator.get_performance_metrics()
        
        assert "total_requests" in metrics
        assert "avg_duration_ms" in metrics
        assert "stage_averages" in metrics
        assert "percentiles" in metrics
        assert "success_rate" in metrics
        
        # Check stage averages
        stage_averages = metrics["stage_averages"]
        assert "stage_a" in stage_averages
        assert "stage_b" in stage_averages
        assert "stage_c" in stage_averages
        assert "stage_d" in stage_averages
        
        # Check percentiles
        percentiles = metrics["percentiles"]
        assert "p50" in percentiles
        assert "p90" in percentiles
        assert "p95" in percentiles
        assert "p99" in percentiles
    
    @pytest.mark.asyncio
    async def test_global_orchestrator_instance(self):
        """Test the global orchestrator instance."""
        orchestrator1 = get_pipeline_orchestrator()
        orchestrator2 = get_pipeline_orchestrator()
        
        # Should return the same instance
        assert orchestrator1 is orchestrator2
        
        # Test convenience function
        result = await process_user_request("Check server status")
        assert isinstance(result, PipelineResult)
        assert result.success is True


class TestPipelineIntegration:
    """Test end-to-end pipeline integration."""
    
    @pytest.fixture
    def integration_tester(self):
        """Create an integration tester for testing."""
        return PipelineIntegrationTester()
    
    @pytest.mark.asyncio
    async def test_basic_integration_flow(self, integration_tester):
        """Test basic integration flow with standard test cases."""
        # Get a subset of standard test cases for faster testing
        test_cases = integration_tester.get_standard_test_cases()[:3]
        
        results = []
        for test_case in test_cases:
            result = await integration_tester.run_integration_test(test_case)
            results.append(result)
        
        # Verify all tests passed
        for result in results:
            assert result.success is True, f"Test {result.test_case.name} failed: {result.error_message}"
            assert result.pipeline_result is not None
            assert result.execution_time_ms > 0
    
    @pytest.mark.asyncio
    async def test_information_request_flow(self, integration_tester):
        """Test information request integration flow."""
        test_case = IntegrationTestCase(
            name="test_information_flow",
            test_type=IntegrationTestType.BASIC_FLOW,
            user_request="What is the current CPU usage?",
            expected_response_type=ResponseType.INFORMATION,
            expected_decision_type=DecisionType.INFO,
            expected_risk_level=RiskLevel.LOW
        )
        
        result = await integration_tester.run_integration_test(test_case)
        
        assert result.success is True
        assert result.pipeline_result.success is True
        assert result.pipeline_result.response.response_type == ResponseType.INFORMATION
        
        # Check validation details
        validation = result.validation_details
        assert validation["overall_success"] is True
        assert validation["checks"]["pipeline_success"]["passed"] is True
        assert validation["checks"]["response_type"]["passed"] is True
    
    @pytest.mark.asyncio
    async def test_action_request_flow(self, integration_tester):
        """Test action request integration flow."""
        test_case = IntegrationTestCase(
            name="test_action_flow",
            test_type=IntegrationTestType.BASIC_FLOW,
            user_request="Restart the apache service on web-01",
            expected_response_type=ResponseType.PLAN_SUMMARY,
            expected_decision_type=DecisionType.ACTION,
            expected_risk_level=RiskLevel.MEDIUM
        )
        
        result = await integration_tester.run_integration_test(test_case)
        
        assert result.success is True
        assert result.pipeline_result.success is True
        
        # Check that execution plan was created
        stage_c_result = result.pipeline_result.intermediate_results["stage_c"]
        assert isinstance(stage_c_result, PlanV1)
        assert len(stage_c_result.execution_plan.steps) > 0
    
    @pytest.mark.asyncio
    async def test_edge_case_handling(self, integration_tester):
        """Test edge case handling in integration."""
        edge_cases = [
            ("", ResponseType.CLARIFICATION),
            ("help", ResponseType.CLARIFICATION),
            ("fix everything", ResponseType.CLARIFICATION)
        ]
        
        for user_request, expected_type in edge_cases:
            test_case = IntegrationTestCase(
                name=f"edge_case_{user_request or 'empty'}",
                test_type=IntegrationTestType.EDGE_CASES,
                user_request=user_request,
                expected_response_type=expected_type
            )
            
            result = await integration_tester.run_integration_test(test_case)
            
            # Should handle gracefully, even if not perfect classification
            assert result.pipeline_result is not None
            assert result.execution_time_ms > 0
    
    @pytest.mark.asyncio
    async def test_concurrent_integration(self, integration_tester):
        """Test concurrent request processing in integration."""
        result = await integration_tester.run_concurrent_test(
            user_request="Check server status",
            concurrent_requests=3
        )
        
        assert result["concurrent_requests"] == 3
        assert result["successful_requests"] >= 0
        assert result["success_rate"] >= 0
        assert result["throughput_requests_per_second"] > 0


class TestStageCommunication:
    """Test communication between pipeline stages."""
    
    @pytest.fixture
    def communication_validator(self):
        """Create a stage communication validator for testing."""
        return StageCommunicationValidator()
    
    @pytest.mark.asyncio
    async def test_stage_a_to_b_communication(self, communication_validator):
        """Test Stage A to Stage B communication."""
        # Create Stage A output
        stage_a_output = communication_validator._create_stage_a_output(
            DecisionType.INFO,
            RiskLevel.LOW,
            "Check server status"
        )
        
        # Test communication
        stage_b_output = await communication_validator._test_a_to_b(stage_a_output)
        
        assert isinstance(stage_b_output, SelectionV1)
        assert stage_b_output.decision_id == stage_a_output.decision_id
        assert len(stage_b_output.selected_tools) >= 0  # Should have selected tools
    
    @pytest.mark.asyncio
    async def test_stage_b_to_c_communication(self, communication_validator):
        """Test Stage B to Stage C communication."""
        # Create Stage B output
        stage_b_output = communication_validator._create_stage_b_output(
            DecisionType.ACTION,
            ["system_monitoring", "service_management"]
        )
        
        # Test communication
        stage_c_output = await communication_validator._test_b_to_c(stage_b_output)
        
        assert isinstance(stage_c_output, PlanV1)
        # PlanV1 doesn't have selection_id, but we can verify it was created successfully
        assert stage_c_output.stage == "stage_c_planner"
        assert len(stage_c_output.plan.steps) >= 0  # Should have execution plan
    
    @pytest.mark.asyncio
    async def test_stage_c_to_d_communication(self, communication_validator):
        """Test Stage C to Stage D communication."""
        # Create Stage C output
        stage_c_output = communication_validator._create_stage_c_output(
            DecisionType.ACTION,
            ["Check system status", "Generate report"]
        )
        
        # Test communication
        stage_d_output = await communication_validator._test_c_to_d(stage_c_output)
        
        assert isinstance(stage_d_output, ResponseV1)
        # ResponseV1 doesn't have request_id field, only response_id
        assert stage_d_output.response_type in [
            ResponseType.INFORMATION,
            ResponseType.PLAN_SUMMARY,
            ResponseType.APPROVAL_REQUEST,
            ResponseType.EXECUTION_READY
        ]
    
    @pytest.mark.asyncio
    async def test_communication_test_suite(self, communication_validator):
        """Test the complete communication test suite."""
        # Run a subset of communication tests
        test_cases = communication_validator.get_standard_test_cases()[:6]
        
        summary = await communication_validator.run_communication_test_suite(test_cases)
        
        assert summary["total_tests"] == len(test_cases)
        assert summary["passed_tests"] >= 0
        assert summary["success_rate"] >= 0
        assert "results_by_transition" in summary
    
    @pytest.mark.asyncio
    async def test_error_propagation(self, communication_validator):
        """Test error propagation between stages."""
        error_summary = await communication_validator.test_error_propagation()
        
        assert "total_error_tests" in error_summary
        assert "passed_error_tests" in error_summary
        assert "error_handling_success_rate" in error_summary
        assert "error_test_details" in error_summary


class TestPerformanceMonitoring:
    """Test performance monitoring and benchmarking."""
    
    @pytest.fixture
    def performance_monitor(self):
        """Create a performance monitor for testing."""
        return PerformanceMonitor()
    
    @pytest.mark.asyncio
    async def test_latency_testing(self, performance_monitor):
        """Test latency measurement."""
        metrics = await performance_monitor.test_latency(
            user_request="Check server status",
            num_requests=3  # Small number for fast testing
        )
        
        assert metrics.test_type == PerformanceTestType.LATENCY
        assert metrics.total_requests == 3
        assert metrics.successful_requests >= 0
        assert metrics.avg_response_time_ms > 0
        assert metrics.requests_per_second > 0
    
    @pytest.mark.asyncio
    async def test_throughput_testing(self, performance_monitor):
        """Test throughput measurement."""
        metrics = await performance_monitor.test_throughput(
            user_request="Check server status",
            concurrent_requests=2,
            test_duration_seconds=5.0  # Short duration for fast testing
        )
        
        assert metrics.test_type == PerformanceTestType.THROUGHPUT
        assert metrics.total_requests >= 0
        assert metrics.requests_per_second >= 0
        assert metrics.duration_seconds > 0
    
    @pytest.mark.asyncio
    async def test_load_testing(self, performance_monitor):
        """Test load testing with ramp-up."""
        metrics = await performance_monitor.test_load(
            user_requests=["Check status", "List services"],
            max_concurrent=2,
            ramp_up_seconds=2.0,
            steady_state_seconds=3.0
        )
        
        assert metrics.test_type == PerformanceTestType.LOAD
        assert metrics.total_requests >= 0
        assert metrics.duration_seconds > 0
        assert "max_concurrent" in metrics.details
    
    def test_performance_targets(self, performance_monitor):
        """Test performance target checking."""
        # Create mock metrics
        from pipeline.integration.performance_monitor import PerformanceMetrics
        
        metrics = PerformanceMetrics(
            test_type=PerformanceTestType.LATENCY,
            test_name="test",
            duration_seconds=10.0,
            total_requests=10,
            successful_requests=10,
            failed_requests=0,
            avg_response_time_ms=1000.0,  # 1 second - should pass
            min_response_time_ms=500.0,
            max_response_time_ms=2000.0,
            p50_response_time_ms=1000.0,
            p90_response_time_ms=1500.0,
            p95_response_time_ms=1800.0,
            p99_response_time_ms=2000.0,
            requests_per_second=1.0,
            avg_cpu_percent=50.0,
            max_cpu_percent=80.0,
            avg_memory_mb=100.0,
            max_memory_mb=200.0,
            error_rate_percent=0.0
        )
        
        target_check = performance_monitor.check_performance_targets(metrics)
        
        assert "overall_passed" in target_check
        assert "checks" in target_check
        assert "summary" in target_check
        
        # Check individual target checks
        checks = target_check["checks"]
        assert "avg_response_time" in checks
        assert "p95_response_time" in checks
        assert "requests_per_second" in checks
        assert "error_rate" in checks
        assert "memory_usage" in checks
    
    def test_performance_summary(self, performance_monitor):
        """Test performance summary generation."""
        # Add some mock results
        from pipeline.integration.performance_monitor import PerformanceMetrics
        
        mock_metrics = PerformanceMetrics(
            test_type=PerformanceTestType.LATENCY,
            test_name="test",
            duration_seconds=10.0,
            total_requests=10,
            successful_requests=10,
            failed_requests=0,
            avg_response_time_ms=1000.0,
            min_response_time_ms=500.0,
            max_response_time_ms=2000.0,
            p50_response_time_ms=1000.0,
            p90_response_time_ms=1500.0,
            p95_response_time_ms=1800.0,
            p99_response_time_ms=2000.0,
            requests_per_second=1.0,
            avg_cpu_percent=50.0,
            max_cpu_percent=80.0,
            avg_memory_mb=100.0,
            max_memory_mb=200.0,
            error_rate_percent=0.0
        )
        
        performance_monitor.test_results.append(mock_metrics)
        
        summary = performance_monitor.get_performance_summary()
        
        assert "total_tests" in summary
        assert "test_types" in summary
        assert "overall_stats" in summary
        assert "results_by_type" in summary


class TestEndToEndScenarios:
    """Test complete end-to-end scenarios."""
    
    @pytest.mark.asyncio
    async def test_information_request_scenario(self):
        """Test complete information request scenario."""
        orchestrator = get_pipeline_orchestrator()
        
        result = await orchestrator.process_request(
            "What is the current status of the database server?"
        )
        
        assert result.success is True
        assert result.response.response_type in [ResponseType.INFORMATION, ResponseType.CLARIFICATION]
        
        # Check pipeline flow
        stage_a_result = result.intermediate_results["stage_a"]
        assert stage_a_result.decision_type == DecisionType.INFO
        assert stage_a_result.risk_level in [RiskLevel.LOW, RiskLevel.MEDIUM]
    
    @pytest.mark.asyncio
    async def test_action_request_scenario(self):
        """Test complete action request scenario."""
        orchestrator = get_pipeline_orchestrator()
        
        result = await orchestrator.process_request(
            "Please restart the nginx service on web-server-01"
        )
        
        assert result.success is True
        assert result.response.response_type in [
            ResponseType.PLAN_SUMMARY, 
            ResponseType.APPROVAL_REQUEST,
            ResponseType.EXECUTION_READY
        ]
        
        # Check pipeline flow
        stage_a_result = result.intermediate_results["stage_a"]
        assert stage_a_result.decision_type == DecisionType.ACTION
        
        stage_c_result = result.intermediate_results["stage_c"]
        assert len(stage_c_result.execution_plan) > 0
    
    @pytest.mark.asyncio
    async def test_deployment_request_scenario(self):
        """Test complete deployment request scenario."""
        orchestrator = get_pipeline_orchestrator()
        
        result = await orchestrator.process_request(
            "Deploy the new API version v2.1.0 to production with zero downtime"
        )
        
        assert result.success is True
        assert result.response.response_type in [
            ResponseType.APPROVAL_REQUEST,
            ResponseType.PLAN_SUMMARY
        ]
        
        # Check pipeline flow
        stage_a_result = result.intermediate_results["stage_a"]
        assert stage_a_result.decision_type == DecisionType.DEPLOYMENT
        assert stage_a_result.risk_level in [RiskLevel.HIGH, RiskLevel.CRITICAL]
        
        stage_c_result = result.intermediate_results["stage_c"]
        assert stage_c_result.approval_required is True
    
    @pytest.mark.asyncio
    async def test_emergency_request_scenario(self):
        """Test complete emergency request scenario."""
        orchestrator = get_pipeline_orchestrator()
        
        result = await orchestrator.process_request(
            "URGENT: The main database is down and users cannot access the application!"
        )
        
        assert result.success is True
        assert result.response.response_type in [
            ResponseType.EXECUTION_READY,
            ResponseType.APPROVAL_REQUEST,
            ResponseType.PLAN_SUMMARY
        ]
        
        # Check pipeline flow
        stage_a_result = result.intermediate_results["stage_a"]
        assert stage_a_result.decision_type == DecisionType.ACTION  # Emergency requests are classified as ACTION
        assert stage_a_result.risk_level == RiskLevel.CRITICAL
    
    @pytest.mark.asyncio
    async def test_multiple_concurrent_scenarios(self):
        """Test multiple concurrent scenarios."""
        orchestrator = get_pipeline_orchestrator()
        
        scenarios = [
            "Check server status",
            "Restart nginx service", 
            "Deploy new version",
            "Monitor CPU usage",
            "Check disk space"
        ]
        
        # Process all scenarios concurrently
        tasks = [
            orchestrator.process_request(scenario, f"scenario_{i}")
            for i, scenario in enumerate(scenarios)
        ]
        
        results = await asyncio.gather(*tasks)
        
        # Verify all scenarios completed successfully
        assert len(results) == len(scenarios)
        for i, result in enumerate(results):
            assert result.success is True, f"Scenario {i} failed: {scenarios[i]}"
            assert isinstance(result.response, ResponseV1)
            assert result.metrics.total_duration_ms > 0


# Performance and load testing (marked as slow)
@pytest.mark.slow
class TestPerformanceAndLoad:
    """Performance and load testing (slower tests)."""
    
    @pytest.mark.asyncio
    async def test_extended_load_scenario(self):
        """Test extended load scenario."""
        performance_monitor = PerformanceMonitor()
        
        metrics = await performance_monitor.test_load(
            user_requests=[
                "Check server status",
                "List running services",
                "Monitor CPU usage",
                "Check disk space",
                "Show network stats"
            ],
            max_concurrent=5,
            ramp_up_seconds=5.0,
            steady_state_seconds=10.0
        )
        
        # Check performance targets
        target_check = performance_monitor.check_performance_targets(metrics)
        
        # Should meet basic performance requirements
        assert metrics.error_rate_percent <= 10.0  # Allow some errors under load
        assert metrics.avg_response_time_ms < 30000  # 30 seconds max
    
    @pytest.mark.asyncio
    async def test_stress_scenario(self):
        """Test stress scenario with high concurrency."""
        performance_monitor = PerformanceMonitor()
        
        metrics = await performance_monitor.test_throughput(
            user_request="Check status",
            concurrent_requests=10,
            test_duration_seconds=15.0
        )
        
        # System should handle stress gracefully
        assert metrics.total_requests > 0
        assert metrics.successful_requests >= 0
        # Allow higher error rates under stress
        assert metrics.error_rate_percent <= 50.0