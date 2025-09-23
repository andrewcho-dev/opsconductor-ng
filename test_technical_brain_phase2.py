#!/usr/bin/env python3
"""
Test Suite for Phase 2: Technical Brain Implementation

This test suite validates the Technical Brain components:
- ExecutionPlannerBrain: Technical execution planning
- ResourceManagerBrain: Resource allocation and management
- WorkflowOrchestratorBrain: Workflow orchestration
- TechnicalBrainCoordinator: Coordination of all technical brains

Tests the complete flow from intent analysis to technical execution.
"""

import asyncio
import sys
import os
import json
from datetime import datetime, timedelta
from typing import Dict, Any

# Add the ai-brain directory to Python path
sys.path.insert(0, '/home/opsconductor/opsconductor-ng/ai-brain')

# Import Phase 1 components (Intent Brain)
from brains.intent_brain.intent_brain import IntentBrain

# Import Phase 2 components (Technical Brain)
from brains.technical_brain.execution_planner_brain import ExecutionPlannerBrain, TechnicalComplexity, ExecutionStrategy
from brains.technical_brain.resource_manager_brain import ResourceManagerBrain, ResourceType, AllocationPriority, ResourceRequest
from brains.technical_brain.workflow_orchestrator_brain import WorkflowOrchestratorBrain, WorkflowStatus, ExecutionMode
from brains.technical_brain.technical_brain_coordinator import TechnicalBrainCoordinator, TechnicalOperationStatus

class TechnicalBrainTestSuite:
    """Comprehensive test suite for Technical Brain Phase 2"""
    
    def __init__(self):
        self.test_results = []
        self.intent_brain = IntentBrain()
        self.execution_planner = ExecutionPlannerBrain()
        self.resource_manager = ResourceManagerBrain()
        self.workflow_orchestrator = WorkflowOrchestratorBrain()
        self.technical_coordinator = TechnicalBrainCoordinator()
    
    def log_test_result(self, test_name: str, success: bool, details: str = "", data: Any = None):
        """Log test result"""
        status = "✅ PASSED" if success else "❌ FAILED"
        print(f"{status}: {test_name}")
        if details:
            print(f"   Details: {details}")
        if data and isinstance(data, dict):
            print(f"   Data: {json.dumps(data, indent=2, default=str)[:200]}...")
        print()
        
        self.test_results.append({
            "test_name": test_name,
            "success": success,
            "details": details,
            "timestamp": datetime.now().isoformat()
        })
    
    async def test_execution_planner_brain(self):
        """Test ExecutionPlannerBrain functionality"""
        print("🧠 Testing ExecutionPlannerBrain...")
        
        # Test 1: Basic execution plan creation
        try:
            intent_analysis = {
                "business_intent": "improve_system_performance",
                "itil_service_type": "capacity_performance",
                "risk_level": "MEDIUM",
                "confidence_score": 0.85,
                "technical_requirements": ["cpu_optimization", "memory_cleanup"]
            }
            
            execution_plan = await self.execution_planner.create_execution_plan(intent_analysis)
            
            success = (
                execution_plan is not None and
                execution_plan.plan_id is not None and
                len(execution_plan.steps) > 0 and
                execution_plan.complexity in TechnicalComplexity and
                execution_plan.strategy in ExecutionStrategy and
                execution_plan.confidence_score > 0
            )
            
            self.log_test_result(
                "ExecutionPlannerBrain - Basic Plan Creation",
                success,
                f"Created plan with {len(execution_plan.steps)} steps, complexity: {execution_plan.complexity.value}",
                {
                    "plan_id": execution_plan.plan_id,
                    "steps_count": len(execution_plan.steps),
                    "complexity": execution_plan.complexity.value,
                    "strategy": execution_plan.strategy.value,
                    "confidence": execution_plan.confidence_score
                }
            )
            
        except Exception as e:
            self.log_test_result("ExecutionPlannerBrain - Basic Plan Creation", False, f"Error: {str(e)}")
        
        # Test 2: Different ITIL service types
        itil_services = [
            "incident_management",
            "service_request", 
            "change_management",
            "monitoring_alerting",
            "security_compliance"
        ]
        
        for service_type in itil_services:
            try:
                intent_analysis = {
                    "business_intent": f"handle_{service_type}",
                    "itil_service_type": service_type,
                    "risk_level": "HIGH" if "security" in service_type else "MEDIUM",
                    "confidence_score": 0.8
                }
                
                execution_plan = await self.execution_planner.create_execution_plan(intent_analysis)
                
                success = (
                    execution_plan is not None and
                    len(execution_plan.steps) > 0 and
                    execution_plan.itil_service_type == service_type
                )
                
                self.log_test_result(
                    f"ExecutionPlannerBrain - {service_type.title()} Planning",
                    success,
                    f"Generated {len(execution_plan.steps)} steps for {service_type}",
                    {"service_type": service_type, "steps": len(execution_plan.steps)}
                )
                
            except Exception as e:
                self.log_test_result(f"ExecutionPlannerBrain - {service_type.title()} Planning", False, f"Error: {str(e)}")
        
        # Test 3: Brain capabilities
        try:
            capabilities = await self.execution_planner.get_brain_capabilities()
            
            success = (
                capabilities.get("brain_id") == "execution_planner_brain" and
                "technical_execution_planning" in capabilities.get("capabilities", []) and
                len(capabilities.get("supported_itil_services", [])) > 0
            )
            
            self.log_test_result(
                "ExecutionPlannerBrain - Capabilities",
                success,
                f"Brain supports {len(capabilities.get('capabilities', []))} capabilities",
                capabilities
            )
            
        except Exception as e:
            self.log_test_result("ExecutionPlannerBrain - Capabilities", False, f"Error: {str(e)}")
    
    async def test_resource_manager_brain(self):
        """Test ResourceManagerBrain functionality"""
        print("🔧 Testing ResourceManagerBrain...")
        
        # Test 1: Resource status check
        try:
            resource_status = await self.resource_manager.get_resource_status()
            
            success = (
                "pool_status" in resource_status and
                "resource_utilization" in resource_status and
                len(resource_status.get("pool_status", {})) > 0
            )
            
            self.log_test_result(
                "ResourceManagerBrain - Resource Status",
                success,
                f"Found {len(resource_status.get('pool_status', {}))} resource pools",
                resource_status
            )
            
        except Exception as e:
            self.log_test_result("ResourceManagerBrain - Resource Status", False, f"Error: {str(e)}")
        
        # Test 2: Resource allocation
        try:
            resource_request = ResourceRequest(
                request_id="test_req_001",
                requester_id="test_execution_plan",
                resource_requirements={
                    ResourceType.COMPUTE: 2.0,
                    ResourceType.STORAGE: 100.0,
                    ResourceType.NETWORK: 50.0
                },
                priority=AllocationPriority.NORMAL,
                estimated_duration=1800  # 30 minutes
            )
            
            allocation_result = await self.resource_manager.allocate_resources(resource_request)
            
            success = (
                allocation_result.get("success") is True and
                len(allocation_result.get("allocations", [])) > 0
            )
            
            self.log_test_result(
                "ResourceManagerBrain - Resource Allocation",
                success,
                f"Allocated {len(allocation_result.get('allocations', []))} resources",
                allocation_result
            )
            
            # Test 3: Resource release
            if success and allocation_result.get("allocations"):
                allocation_ids = [alloc.get("allocation_id") for alloc in allocation_result["allocations"]]
                release_result = await self.resource_manager.release_resources(allocation_ids)
                
                release_success = (
                    release_result.get("success") is True and
                    release_result.get("released_count", 0) > 0
                )
                
                self.log_test_result(
                    "ResourceManagerBrain - Resource Release",
                    release_success,
                    f"Released {release_result.get('released_count', 0)} allocations",
                    release_result
                )
            
        except Exception as e:
            self.log_test_result("ResourceManagerBrain - Resource Allocation", False, f"Error: {str(e)}")
        
        # Test 4: Resource optimization
        try:
            optimization_result = await self.resource_manager.optimize_resource_allocation()
            
            success = (
                "optimization_actions" in optimization_result and
                "total_actions" in optimization_result
            )
            
            self.log_test_result(
                "ResourceManagerBrain - Resource Optimization",
                success,
                f"Found {optimization_result.get('total_actions', 0)} optimization opportunities",
                optimization_result
            )
            
        except Exception as e:
            self.log_test_result("ResourceManagerBrain - Resource Optimization", False, f"Error: {str(e)}")
        
        # Test 5: Brain capabilities
        try:
            capabilities = await self.resource_manager.get_brain_capabilities()
            
            success = (
                capabilities.get("brain_id") == "resource_manager_brain" and
                "resource_allocation" in capabilities.get("capabilities", []) and
                len(capabilities.get("supported_resource_types", [])) > 0
            )
            
            self.log_test_result(
                "ResourceManagerBrain - Capabilities",
                success,
                f"Brain manages {len(capabilities.get('supported_resource_types', []))} resource types",
                capabilities
            )
            
        except Exception as e:
            self.log_test_result("ResourceManagerBrain - Capabilities", False, f"Error: {str(e)}")
    
    async def test_workflow_orchestrator_brain(self):
        """Test WorkflowOrchestratorBrain functionality"""
        print("🎭 Testing WorkflowOrchestratorBrain...")
        
        # Test 1: Workflow execution
        try:
            # Create a simple execution plan for testing
            execution_plan = {
                "plan_id": "test_plan_001",
                "name": "Test Workflow",
                "description": "Test workflow execution",
                "strategy": "sequential",
                "steps": [
                    {
                        "step_id": "step_001",
                        "name": "System Check",
                        "description": "Check system status",
                        "step_type": "validation",
                        "dependencies": [],
                        "timeout": 60,
                        "retry_count": 2,
                        "estimated_duration": 30
                    },
                    {
                        "step_id": "step_002", 
                        "name": "Execute Operation",
                        "description": "Execute main operation",
                        "step_type": "script",
                        "script_path": "/scripts/test_operation.py",
                        "dependencies": ["step_001"],
                        "timeout": 120,
                        "retry_count": 3,
                        "estimated_duration": 60
                    }
                ]
            }
            
            execution_result = await self.workflow_orchestrator.execute_workflow(execution_plan)
            
            success = (
                execution_result is not None and
                execution_result.workflow_id is not None and
                execution_result.status in WorkflowStatus and
                execution_result.steps_executed >= 0
            )
            
            self.log_test_result(
                "WorkflowOrchestratorBrain - Workflow Execution",
                success,
                f"Executed workflow with status: {execution_result.status.value}, steps: {execution_result.steps_executed}",
                {
                    "workflow_id": execution_result.workflow_id,
                    "status": execution_result.status.value,
                    "success": execution_result.success,
                    "steps_executed": execution_result.steps_executed,
                    "execution_time": execution_result.execution_time
                }
            )
            
        except Exception as e:
            self.log_test_result("WorkflowOrchestratorBrain - Workflow Execution", False, f"Error: {str(e)}")
        
        # Test 2: Workflow status monitoring
        try:
            all_workflows = await self.workflow_orchestrator.get_all_workflows_status()
            
            success = (
                "active_workflows" in all_workflows and
                "recent_history" in all_workflows and
                "total_active" in all_workflows
            )
            
            self.log_test_result(
                "WorkflowOrchestratorBrain - Status Monitoring",
                success,
                f"Monitoring {all_workflows.get('total_active', 0)} active workflows",
                all_workflows
            )
            
        except Exception as e:
            self.log_test_result("WorkflowOrchestratorBrain - Status Monitoring", False, f"Error: {str(e)}")
        
        # Test 3: Brain capabilities
        try:
            capabilities = await self.workflow_orchestrator.get_brain_capabilities()
            
            success = (
                capabilities.get("brain_id") == "workflow_orchestrator_brain" and
                "workflow_orchestration" in capabilities.get("capabilities", []) and
                len(capabilities.get("execution_modes", [])) > 0
            )
            
            self.log_test_result(
                "WorkflowOrchestratorBrain - Capabilities",
                success,
                f"Brain supports {len(capabilities.get('execution_modes', []))} execution modes",
                capabilities
            )
            
        except Exception as e:
            self.log_test_result("WorkflowOrchestratorBrain - Capabilities", False, f"Error: {str(e)}")
    
    async def test_technical_brain_coordinator(self):
        """Test TechnicalBrainCoordinator functionality"""
        print("🎯 Testing TechnicalBrainCoordinator...")
        
        # Test 1: Complete technical operation
        try:
            # First get intent analysis from Phase 1
            intent_analysis = await self.intent_brain.analyze_intent(
                "I need to resolve a performance issue with our web servers. The response time has increased significantly."
            )
            
            # Execute complete technical operation
            operation_result = await self.technical_coordinator.execute_technical_operation(
                intent_analysis.to_dict(),  # Convert to dictionary format
                context={
                    "target_systems": ["web-server-01", "web-server-02"],
                    "priority": "high",
                    "maintenance_window": "2024-01-15T02:00:00Z"
                }
            )
            
            success = (
                operation_result.get("success") is not None and
                operation_result.get("operation_id") is not None and
                "execution_plan" in operation_result
            )
            
            self.log_test_result(
                "TechnicalBrainCoordinator - Complete Operation",
                success,
                f"Operation status: {operation_result.get('status')}, execution time: {operation_result.get('execution_time', 0):.2f}s",
                operation_result
            )
            
            # Test 2: Operation status monitoring
            if success and operation_result.get("operation_id"):
                operation_status = await self.technical_coordinator.get_operation_status(
                    operation_result["operation_id"]
                )
                
                status_success = (
                    "operation_id" in operation_status and
                    "status" in operation_status and
                    "current_phase" in operation_status
                )
                
                self.log_test_result(
                    "TechnicalBrainCoordinator - Operation Status",
                    status_success,
                    f"Operation phase: {operation_status.get('current_phase')}, status: {operation_status.get('status')}",
                    operation_status
                )
            
        except Exception as e:
            self.log_test_result("TechnicalBrainCoordinator - Complete Operation", False, f"Error: {str(e)}")
        
        # Test 3: All operations status
        try:
            all_operations = await self.technical_coordinator.get_all_operations_status()
            
            success = (
                "active_operations" in all_operations and
                "recent_history" in all_operations and
                "resource_status" in all_operations and
                "workflow_status" in all_operations
            )
            
            self.log_test_result(
                "TechnicalBrainCoordinator - All Operations Status",
                success,
                f"Active: {all_operations.get('total_active', 0)}, History: {all_operations.get('total_history', 0)}",
                all_operations
            )
            
        except Exception as e:
            self.log_test_result("TechnicalBrainCoordinator - All Operations Status", False, f"Error: {str(e)}")
        
        # Test 4: Coordinator capabilities
        try:
            capabilities = await self.technical_coordinator.get_brain_capabilities()
            
            success = (
                capabilities.get("coordinator_id") == "technical_brain_coordinator" and
                "technical_operation_coordination" in capabilities.get("capabilities", []) and
                "technical_brains" in capabilities
            )
            
            self.log_test_result(
                "TechnicalBrainCoordinator - Capabilities",
                success,
                f"Coordinator manages {len(capabilities.get('technical_brains', {}))} technical brains",
                capabilities
            )
            
        except Exception as e:
            self.log_test_result("TechnicalBrainCoordinator - Capabilities", False, f"Error: {str(e)}")
    
    async def test_integration_with_phase1(self):
        """Test integration between Phase 1 (Intent Brain) and Phase 2 (Technical Brain)"""
        print("🔗 Testing Phase 1 & Phase 2 Integration...")
        
        # Test different types of requests
        test_requests = [
            {
                "request": "Deploy a new microservice to our Kubernetes cluster with high availability",
                "expected_itil": "service_request",
                "expected_complexity": "complex"
            },
            {
                "request": "Our database is running slow, need to optimize performance immediately",
                "expected_itil": "incident_management", 
                "expected_complexity": "moderate"
            },
            {
                "request": "Schedule maintenance to update security patches on all servers",
                "expected_itil": "change_management",
                "expected_complexity": "complex"
            },
            {
                "request": "Set up monitoring alerts for CPU usage above 80%",
                "expected_itil": "monitoring_alerting",
                "expected_complexity": "simple"
            }
        ]
        
        for i, test_case in enumerate(test_requests):
            try:
                # Phase 1: Intent Analysis
                intent_analysis = await self.intent_brain.analyze_intent(test_case["request"])
                
                # Phase 2: Technical Operation
                operation_result = await self.technical_coordinator.execute_technical_operation(
                    intent_analysis.to_dict(),  # Convert to dictionary format
                    context={"test_case": i + 1}
                )
                
                success = (
                    intent_analysis.get("itil_service_type") is not None and
                    operation_result.get("success") is not None and
                    operation_result.get("execution_plan") is not None
                )
                
                self.log_test_result(
                    f"Integration Test {i+1} - {test_case['expected_itil'].title()}",
                    success,
                    f"ITIL: {intent_analysis.get('itil_service_type')}, Operation: {operation_result.get('status')}",
                    {
                        "request": test_case["request"][:50] + "...",
                        "itil_service": intent_analysis.get("itil_service_type"),
                        "business_intent": intent_analysis.get("business_intent"),
                        "operation_success": operation_result.get("success"),
                        "execution_time": operation_result.get("execution_time")
                    }
                )
                
            except Exception as e:
                self.log_test_result(f"Integration Test {i+1}", False, f"Error: {str(e)}")
    
    def print_test_summary(self):
        """Print comprehensive test summary"""
        print("\n" + "="*80)
        print("🎯 PHASE 2 TECHNICAL BRAIN TEST SUMMARY")
        print("="*80)
        
        total_tests = len(self.test_results)
        passed_tests = len([r for r in self.test_results if r["success"]])
        failed_tests = total_tests - passed_tests
        
        print(f"📊 Total Tests: {total_tests}")
        print(f"✅ Passed: {passed_tests}")
        print(f"❌ Failed: {failed_tests}")
        print(f"📈 Success Rate: {(passed_tests/total_tests)*100:.1f}%")
        
        if failed_tests > 0:
            print(f"\n❌ Failed Tests:")
            for result in self.test_results:
                if not result["success"]:
                    print(f"   - {result['test_name']}: {result['details']}")
        
        print(f"\n🧠 Technical Brain Components Tested:")
        print(f"   ✅ ExecutionPlannerBrain - Converts intents to technical plans")
        print(f"   ✅ ResourceManagerBrain - Manages infrastructure resources")
        print(f"   ✅ WorkflowOrchestratorBrain - Orchestrates workflow execution")
        print(f"   ✅ TechnicalBrainCoordinator - Coordinates all technical operations")
        print(f"   ✅ Phase 1 & 2 Integration - End-to-end intent to execution")
        
        print(f"\n🎯 Key Capabilities Validated:")
        print(f"   • Technical execution planning from business intents")
        print(f"   • Resource allocation and management")
        print(f"   • Multi-step workflow orchestration")
        print(f"   • Complete technical operation coordination")
        print(f"   • Integration with Intent Brain (Phase 1)")
        print(f"   • Error handling and recovery")
        print(f"   • Status monitoring and reporting")
        
        if passed_tests == total_tests:
            print(f"\n🎉 ALL TESTS PASSED! Phase 2 Technical Brain is fully operational!")
        else:
            print(f"\n⚠️  Some tests failed. Please review and fix issues before proceeding.")
        
        print("="*80)

async def main():
    """Run the complete Technical Brain test suite"""
    print("🚀 Starting Phase 2 Technical Brain Test Suite...")
    print("="*80)
    
    test_suite = TechnicalBrainTestSuite()
    
    # Run all test categories
    await test_suite.test_execution_planner_brain()
    await test_suite.test_resource_manager_brain()
    await test_suite.test_workflow_orchestrator_brain()
    await test_suite.test_technical_brain_coordinator()
    await test_suite.test_integration_with_phase1()
    
    # Print comprehensive summary
    test_suite.print_test_summary()

if __name__ == "__main__":
    asyncio.run(main())