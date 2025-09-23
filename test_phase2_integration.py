#!/usr/bin/env python3
"""
Test script for Phase 2 Technical Brain Real Infrastructure Integration

This script tests the integration of Phase 2 Technical Brain components
with real OpsConductor infrastructure services.
"""

import asyncio
import logging
import sys
import json
from datetime import datetime

# Add the project root to Python path
sys.path.insert(0, '/home/opsconductor/opsconductor-ng')
sys.path.insert(0, '/home/opsconductor/opsconductor-ng/ai-brain')

from brains.technical_brain import TechnicalBrainCoordinator

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

async def test_service_connections():
    """Test service connections for all integration clients"""
    logger.info("=== Testing Service Connections ===")
    
    coordinator = TechnicalBrainCoordinator()
    
    try:
        # Test service connections
        await coordinator.refresh_service_connections()
        logger.info("✓ Service connections refreshed successfully")
        
        # Get capabilities to check service integration status
        capabilities = await coordinator.get_brain_capabilities()
        
        # Check each brain's service integrations
        for brain_name, brain_caps in capabilities.get('technical_brains', {}).items():
            service_integrations = brain_caps.get('service_integrations', {})
            logger.info(f"Brain: {brain_name}")
            for service, status in service_integrations.items():
                logger.info(f"  - {service}: {status}")
        
        return True
        
    except Exception as e:
        logger.error(f"✗ Service connection test failed: {str(e)}")
        return False
    
    finally:
        await coordinator.cleanup()

async def test_resource_discovery():
    """Test real infrastructure resource discovery"""
    logger.info("=== Testing Resource Discovery ===")
    
    coordinator = TechnicalBrainCoordinator()
    
    try:
        # Discover real infrastructure resources
        await coordinator.discover_infrastructure_resources()
        logger.info("✓ Infrastructure resource discovery completed")
        
        # Get resource manager capabilities to check discovered resources
        resource_manager = coordinator.resource_manager
        resource_pools = resource_manager.resource_pools
        
        logger.info(f"Discovered resource pools:")
        for pool_type, pool in resource_pools.items():
            logger.info(f"  - {pool_type}: {len(pool.resources)} resources")
            if pool.resources:
                # Show first resource as example
                first_resource = list(pool.resources.values())[0]
                logger.info(f"    Example: {first_resource.resource_id} ({first_resource.resource_type})")
        
        return True
        
    except Exception as e:
        logger.error(f"✗ Resource discovery test failed: {str(e)}")
        return False
    
    finally:
        await coordinator.cleanup()

async def test_execution_planning():
    """Test execution planning with real resource awareness"""
    logger.info("=== Testing Execution Planning ===")
    
    coordinator = TechnicalBrainCoordinator()
    
    try:
        # Mock intent analysis for testing
        intent_analysis = {
            'business_intent': 'Deploy application update',
            'itil_service_type': 'change_management',
            'risk_level': 'MEDIUM',
            'confidence_score': 0.85,
            'target_systems': ['web-server-01', 'web-server-02'],
            'estimated_duration': 30
        }
        
        context = {
            'target_systems': ['web-server-01', 'web-server-02'],
            'maintenance_window': '2024-01-15T02:00:00Z',
            'rollback_required': True
        }
        
        # Create execution plan
        execution_plan = await coordinator.execution_planner.create_execution_plan(
            intent_analysis, context
        )
        
        logger.info("✓ Execution plan created successfully")
        logger.info(f"  - Plan ID: {execution_plan.plan_id}")
        logger.info(f"  - Complexity: {execution_plan.complexity.value}")
        logger.info(f"  - Strategy: {execution_plan.strategy.value}")
        logger.info(f"  - Steps: {len(execution_plan.steps)}")
        logger.info(f"  - Resource Plan: CPU={execution_plan.resource_plan.cpu_cores}, Memory={execution_plan.resource_plan.memory_mb}MB")
        
        # Check if resource plan includes real infrastructure data
        resource_tags = execution_plan.resource_plan.resource_tags
        real_resource_tags = [tag for tag in resource_tags if tag.startswith('available_')]
        if real_resource_tags:
            logger.info("✓ Resource plan includes real infrastructure data:")
            for tag in real_resource_tags:
                logger.info(f"    - {tag}")
        else:
            logger.info("! Resource plan using default values (services may be unavailable)")
        
        return True
        
    except Exception as e:
        logger.error(f"✗ Execution planning test failed: {str(e)}")
        return False
    
    finally:
        await coordinator.cleanup()

async def test_workflow_execution():
    """Test workflow execution with real Celery integration"""
    logger.info("=== Testing Workflow Execution ===")
    
    coordinator = TechnicalBrainCoordinator()
    
    try:
        # Create a simple execution plan for testing
        from brains.technical_brain.execution_planner_brain import ExecutionPlan, TechnicalStep, TechnicalComplexity, ExecutionStrategy, ResourcePlan
        
        # Create test execution plan
        test_plan = ExecutionPlan(
            plan_id="test_plan_001",
            name="Test Workflow Execution",
            description="Test workflow execution with real Celery integration",
            business_intent="test_execution",
            itil_service_type="change_management",
            complexity=TechnicalComplexity.SIMPLE,
            strategy=ExecutionStrategy.SEQUENTIAL,
            steps=[
                TechnicalStep(
                    step_id="test_step_001",
                    name="Test Command Step",
                    description="Execute a test command",
                    step_type="command",
                    command="echo 'Hello from Phase 2 Technical Brain!'",
                    estimated_duration=5,
                    risk_level="LOW"
                )
            ],
            resource_plan=ResourcePlan(cpu_cores=1, memory_mb=512, disk_space_mb=100),
            estimated_duration=5,
            confidence_score=0.95
        )
        
        # Execute the workflow
        execution_result = await coordinator.workflow_orchestrator.execute_workflow(
            test_plan
        )
        
        logger.info("✓ Workflow execution completed")
        logger.info(f"  - Status: {execution_result.status.value}")
        logger.info(f"  - Steps Completed: {execution_result.steps_completed}")
        logger.info(f"  - Steps Failed: {execution_result.steps_failed}")
        
        # Check if execution used real Celery workers
        if execution_result.results:
            for step_id, result in execution_result.results.items():
                if 'task_id' in result:
                    logger.info(f"✓ Step {step_id} executed on real Celery worker (Task ID: {result['task_id']})")
                elif result.get('fallback'):
                    logger.info(f"! Step {step_id} used fallback execution (Celery unavailable)")
                else:
                    logger.info(f"- Step {step_id} executed successfully")
        
        return execution_result.status.value == 'completed'
        
    except Exception as e:
        logger.error(f"✗ Workflow execution test failed: {str(e)}")
        return False
    
    finally:
        await coordinator.cleanup()

async def test_complete_technical_operation():
    """Test complete technical operation from intent to execution"""
    logger.info("=== Testing Complete Technical Operation ===")
    
    coordinator = TechnicalBrainCoordinator()
    
    try:
        # Mock intent analysis for a complete operation
        intent_analysis = {
            'business_intent': 'System health check',
            'itil_service_type': 'monitoring_alerting',
            'risk_level': 'LOW',
            'confidence_score': 0.90,
            'target_systems': ['monitoring-server'],
            'estimated_duration': 10
        }
        
        context = {
            'target_systems': ['monitoring-server'],
            'check_type': 'health_check',
            'automated': True
        }
        
        # Execute complete technical operation
        operation_result = await coordinator.execute_technical_operation(
            intent_analysis, context
        )
        
        logger.info("✓ Complete technical operation executed")
        logger.info(f"  - Operation ID: {operation_result.get('operation_id')}")
        logger.info(f"  - Status: {operation_result.get('status')}")
        logger.info(f"  - Phase: {operation_result.get('current_phase')}")
        
        # Check execution results
        execution_result = operation_result.get('execution_result')
        if execution_result:
            logger.info(f"  - Execution Status: {execution_result.get('status')}")
            logger.info(f"  - Steps Completed: {execution_result.get('steps_completed', 0)}")
        
        return operation_result.get('status') == 'completed'
        
    except Exception as e:
        logger.error(f"✗ Complete technical operation test failed: {str(e)}")
        return False
    
    finally:
        await coordinator.cleanup()

async def main():
    """Run all Phase 2 integration tests"""
    logger.info("Starting Phase 2 Technical Brain Real Infrastructure Integration Tests")
    logger.info("=" * 80)
    
    test_results = []
    
    # Run all tests
    tests = [
        ("Service Connections", test_service_connections),
        ("Resource Discovery", test_resource_discovery),
        ("Execution Planning", test_execution_planning),
        ("Workflow Execution", test_workflow_execution),
        ("Complete Technical Operation", test_complete_technical_operation)
    ]
    
    for test_name, test_func in tests:
        logger.info(f"\nRunning test: {test_name}")
        logger.info("-" * 40)
        
        try:
            result = await test_func()
            test_results.append((test_name, result))
            
            if result:
                logger.info(f"✓ {test_name}: PASSED")
            else:
                logger.info(f"✗ {test_name}: FAILED")
                
        except Exception as e:
            logger.error(f"✗ {test_name}: ERROR - {str(e)}")
            test_results.append((test_name, False))
    
    # Summary
    logger.info("\n" + "=" * 80)
    logger.info("PHASE 2 INTEGRATION TEST SUMMARY")
    logger.info("=" * 80)
    
    passed = sum(1 for _, result in test_results if result)
    total = len(test_results)
    
    for test_name, result in test_results:
        status = "PASSED" if result else "FAILED"
        logger.info(f"{test_name:.<40} {status}")
    
    logger.info("-" * 80)
    logger.info(f"Total Tests: {total}")
    logger.info(f"Passed: {passed}")
    logger.info(f"Failed: {total - passed}")
    logger.info(f"Success Rate: {(passed/total)*100:.1f}%")
    
    if passed == total:
        logger.info("🎉 ALL TESTS PASSED! Phase 2 integration is working correctly.")
        return 0
    else:
        logger.info("⚠️  Some tests failed. Check the logs above for details.")
        return 1

if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)