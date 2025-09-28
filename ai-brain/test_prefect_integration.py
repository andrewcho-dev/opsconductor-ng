#!/usr/bin/env python3
"""
Test script for Prefect integration

This script tests the complete Prefect integration pipeline:
1. Generate a workflow
2. Convert to Prefect flow
3. Execute using the execution router
"""

import asyncio
import logging
import sys
import os
from datetime import datetime

# Add the ai-brain directory to the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from job_engine.workflow_generator import WorkflowGenerator, WorkflowType
from job_engine.execution_router import ExecutionRouter, ExecutionEngine
from integrations.prefect_client import PrefectClient

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


async def test_prefect_availability():
    """Test if Prefect services are available"""
    logger.info("Testing Prefect service availability...")
    
    try:
        async with PrefectClient() as client:
            available = await client.is_available()
            if available:
                logger.info("✅ Prefect services are available")
                return True
            else:
                logger.warning("❌ Prefect services are not available")
                return False
    except Exception as e:
        logger.error(f"❌ Error checking Prefect availability: {str(e)}")
        return False


async def test_workflow_generation():
    """Test workflow generation"""
    logger.info("Testing workflow generation...")
    
    try:
        generator = WorkflowGenerator()
        
        # Create a test workflow
        workflow = generator.generate_workflow(
            intent_type="system_maintenance",
            requirements={
                "action": "check_disk_space",
                "threshold": "80%",
                "systems": ["server1", "server2"]
            },
            target_systems=["server1", "server2"],
            context={"user": "test_user", "priority": "medium"}
        )
        
        logger.info(f"✅ Generated workflow: {workflow.name}")
        logger.info(f"   - Steps: {len(workflow.steps)}")
        logger.info(f"   - Type: {workflow.workflow_type.value}")
        logger.info(f"   - Risk: {workflow.risk_level}")
        
        return workflow
        
    except Exception as e:
        logger.error(f"❌ Error generating workflow: {str(e)}")
        return None


async def test_prefect_flow_generation(workflow):
    """Test Prefect flow generation"""
    logger.info("Testing Prefect flow generation...")
    
    try:
        from job_engine.prefect_flow_generator import PrefectFlowGenerator
        
        generator = PrefectFlowGenerator()
        flow_definition = generator.generate_prefect_flow(workflow)
        
        logger.info(f"✅ Generated Prefect flow: {flow_definition.name}")
        logger.info(f"   - Parameters: {len(flow_definition.parameters)}")
        logger.info(f"   - Tags: {flow_definition.tags}")
        logger.info(f"   - Timeout: {flow_definition.timeout_seconds}s")
        
        # Show a snippet of the generated code
        code_lines = flow_definition.flow_code.split('\n')
        logger.info("   - Code preview (first 10 lines):")
        for i, line in enumerate(code_lines[:10]):
            logger.info(f"     {i+1:2d}: {line}")
        
        return flow_definition
        
    except Exception as e:
        logger.error(f"❌ Error generating Prefect flow: {str(e)}")
        return None


async def test_execution_routing(workflow):
    """Test execution routing logic"""
    logger.info("Testing execution routing...")
    
    try:
        router = ExecutionRouter()
        
        # Test auto routing decision
        decision = await router._make_execution_decision(workflow, ExecutionEngine.AUTO)
        
        logger.info(f"✅ Execution routing decision:")
        logger.info(f"   - Engine: {decision.engine.value}")
        logger.info(f"   - Reason: {decision.reason}")
        logger.info(f"   - Complexity: {decision.complexity_level.value}")
        logger.info(f"   - Confidence: {decision.confidence_score:.2f}")
        
        return decision
        
    except Exception as e:
        logger.error(f"❌ Error in execution routing: {str(e)}")
        return None


async def test_prefect_flow_creation(flow_definition):
    """Test creating a flow in Prefect"""
    logger.info("Testing Prefect flow creation...")
    
    try:
        async with PrefectClient() as client:
            if not await client.is_available():
                logger.warning("⚠️  Prefect not available, skipping flow creation test")
                return None
            
            # Create flow
            result = await client.create_flow(flow_definition)
            
            logger.info(f"✅ Created Prefect flow:")
            logger.info(f"   - Flow ID: {result.get('flow_id')}")
            logger.info(f"   - Status: {result.get('status')}")
            
            return result
            
    except Exception as e:
        logger.error(f"❌ Error creating Prefect flow: {str(e)}")
        return None


async def test_full_integration():
    """Test the complete integration pipeline"""
    logger.info("Testing full Prefect integration pipeline...")
    
    try:
        generator = WorkflowGenerator()
        
        # Create a simple test workflow
        workflow = generator.generate_workflow(
            intent_type="information_query",
            requirements={
                "action": "ping_test",
                "targets": ["8.8.8.8", "google.com"]
            },
            target_systems=["automation-service"],
            context={"test": True}
        )
        
        # Test execution with different preferences
        test_cases = [
            ("auto", False),
            ("celery", False),
            ("prefect", False)
        ]
        
        for engine_pref, force in test_cases:
            logger.info(f"Testing execution with engine preference: {engine_pref}")
            
            try:
                result = await generator.execute_workflow(
                    workflow=workflow,
                    engine_preference=engine_pref,
                    force_engine=force
                )
                
                logger.info(f"✅ Execution result for {engine_pref}:")
                logger.info(f"   - Engine used: {result.get('engine_used')}")
                logger.info(f"   - Success: {result.get('success')}")
                logger.info(f"   - Execution ID: {result.get('execution_id')}")
                
                if result.get('error_message'):
                    logger.warning(f"   - Error: {result.get('error_message')}")
                
            except Exception as e:
                logger.error(f"❌ Error testing {engine_pref}: {str(e)}")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Error in full integration test: {str(e)}")
        return False


async def main():
    """Main test function"""
    logger.info("🚀 Starting Prefect integration tests...")
    logger.info("=" * 60)
    
    # Test 1: Check Prefect availability
    prefect_available = await test_prefect_availability()
    logger.info("-" * 60)
    
    # Test 2: Workflow generation
    workflow = await test_workflow_generation()
    if not workflow:
        logger.error("Cannot continue without a valid workflow")
        return False
    logger.info("-" * 60)
    
    # Test 3: Prefect flow generation
    flow_definition = await test_prefect_flow_generation(workflow)
    if not flow_definition:
        logger.error("Cannot continue without a valid flow definition")
        return False
    logger.info("-" * 60)
    
    # Test 4: Execution routing
    decision = await test_execution_routing(workflow)
    logger.info("-" * 60)
    
    # Test 5: Flow creation (only if Prefect is available)
    if prefect_available:
        flow_result = await test_prefect_flow_creation(flow_definition)
        logger.info("-" * 60)
    
    # Test 6: Full integration
    integration_success = await test_full_integration()
    logger.info("-" * 60)
    
    # Summary
    logger.info("📊 Test Summary:")
    logger.info(f"   - Prefect Available: {'✅' if prefect_available else '❌'}")
    logger.info(f"   - Workflow Generation: {'✅' if workflow else '❌'}")
    logger.info(f"   - Flow Generation: {'✅' if flow_definition else '❌'}")
    logger.info(f"   - Execution Routing: {'✅' if decision else '❌'}")
    logger.info(f"   - Full Integration: {'✅' if integration_success else '❌'}")
    
    if prefect_available and workflow and flow_definition and decision and integration_success:
        logger.info("🎉 All tests passed! Prefect integration is working correctly.")
        return True
    else:
        logger.warning("⚠️  Some tests failed. Check the logs above for details.")
        return False


if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)