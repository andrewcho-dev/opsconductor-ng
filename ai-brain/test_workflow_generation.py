#!/usr/bin/env python3

import asyncio
import sys
import os

# Add the ai-brain directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__)))

from fulfillment_engine.workflow_planner import WorkflowPlanner

class MockLLMEngine:
    """Mock LLM engine for testing workflow generation"""
    
    async def generate(self, prompt):
        """Return a natural language workflow response"""
        return {
            "generated_text": """
            WORKFLOW NAME: Ping Job for 192.168.50.210
            DESCRIPTION: Create a recurring ping job to monitor network connectivity to IP address 192.168.50.210 every 10 seconds
            ESTIMATED DURATION: 5 minutes
            RISK LEVEL: low
            REQUIRES APPROVAL: no
            
            1. STEP: Setup Ping Command
               NAME: Create Ping Job
               DESCRIPTION: Configure a ping command to test connectivity to 192.168.50.210
               COMMAND: ping -c 1 192.168.50.210
               TARGET: 192.168.50.210
               TIMEOUT: 30 seconds
               DEPENDENCIES: none
               VALIDATION: check exit code is 0
            
            2. STEP: Schedule Recurring Execution
               NAME: Schedule Ping Job
               DESCRIPTION: Set up recurring execution every 10 seconds using celery-beat
               COMMAND: celery -A automation_service.celery beat --schedule-file=/tmp/celerybeat-schedule --loglevel=info
               TARGET: localhost
               TIMEOUT: 60 seconds
               DEPENDENCIES: 1
               VALIDATION: verify celery beat is running
            """
        }

async def test_workflow_generation():
    """Test workflow generation for ping job"""
    print("🧪 Testing Workflow Generation for Ping Job...")
    
    # Create workflow planner with mock LLM
    mock_llm = MockLLMEngine()
    workflow_planner = WorkflowPlanner(llm_engine=mock_llm)
    
    try:
        # Test workflow generation
        user_intent = "automation"
        user_message = "create a job that pings 192.168.50.210 every 10 seconds"
        
        workflow = await workflow_planner.create_workflow(user_intent, user_message)
        
        print(f"✅ Workflow generation successful!")
        print(f"   Workflow ID: {workflow.workflow_id}")
        print(f"   Name: {workflow.name}")
        print(f"   Description: {workflow.description}")
        print(f"   Steps: {len(workflow.steps)}")
        print(f"   Estimated Duration: {workflow.estimated_duration_minutes} minutes")
        print(f"   Risk Level: {workflow.risk_level}")
        print(f"   Requires Approval: {workflow.requires_approval}")
        
        # Print step details
        for i, step in enumerate(workflow.steps, 1):
            print(f"   Step {i}: {step.name}")
            print(f"     Command: {step.command}")
            print(f"     Target: {step.target_systems}")
            print(f"     Timeout: {step.timeout_seconds}s")
            
        return workflow
        
    except Exception as e:
        print(f"❌ Workflow generation failed: {e}")
        import traceback
        traceback.print_exc()
        return None

if __name__ == "__main__":
    workflow = asyncio.run(test_workflow_generation())
    if workflow:
        print("\n🎉 Workflow generation test PASSED!")
        print(f"Generated workflow with {len(workflow.steps)} steps")
    else:
        print("\n💥 Workflow generation test FAILED!")
        sys.exit(1)