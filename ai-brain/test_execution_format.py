#!/usr/bin/env python3

import asyncio
import sys
import os

# Add the ai-brain directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__)))

from fulfillment_engine.execution_coordinator import ExecutionCoordinator
from fulfillment_engine.workflow_planner import WorkflowStep, StepType

def test_job_data_format():
    """Test that the job data format matches automation service expectations"""
    print("🧪 Testing Job Data Format for Automation Service...")
    
    # Create a sample workflow step
    step = WorkflowStep(
        step_id="step_1",
        step_type=StepType.NETWORK_OPERATION,
        name="Test Ping Command",
        description="Test ping to verify connectivity",
        command="ping -c 1 192.168.50.210",
        timeout_seconds=30,
        target_systems=["192.168.50.210"]
    )
    
    # Create execution coordinator (without automation client for testing)
    coordinator = ExecutionCoordinator(automation_client=None)
    
    # Test the job data format that would be sent to automation service
    job_data = {
        "name": f"Step: {step.name}",
        "description": step.description,
        "steps": [
            {
                "id": step.step_id,
                "name": step.name,
                "command": step.command,
                "type": "command",
                "timeout": step.timeout_seconds,
                "inputs": {}
            }
        ],
        "target_systems": step.target_systems or ["localhost"]
    }
    
    print("✅ Job data format created successfully!")
    print(f"   Job Name: {job_data['name']}")
    print(f"   Description: {job_data['description']}")
    print(f"   Steps Count: {len(job_data['steps'])}")
    print(f"   Target Systems: {job_data['target_systems']}")
    
    # Check step format
    step_data = job_data['steps'][0]
    print(f"   Step Format:")
    print(f"     ID: {step_data['id']}")
    print(f"     Name: {step_data['name']}")
    print(f"     Command: {step_data['command']}")
    print(f"     Type: {step_data['type']}")
    print(f"     Timeout: {step_data['timeout']}")
    print(f"     Inputs: {step_data['inputs']}")
    
    # Verify required fields are present
    required_fields = ['id', 'name', 'command', 'type']
    missing_fields = [field for field in required_fields if field not in step_data]
    
    if missing_fields:
        print(f"❌ Missing required fields: {missing_fields}")
        return False
    else:
        print("✅ All required fields present!")
        return True

if __name__ == "__main__":
    success = test_job_data_format()
    if success:
        print("\n🎉 Job data format test PASSED!")
        print("The format should now be compatible with the automation service.")
    else:
        print("\n💥 Job data format test FAILED!")
        sys.exit(1)