#!/usr/bin/env python3
"""
Test script to verify the execution ID fix
"""

import asyncio
import sys
import os
sys.path.append('/app')

from integrations.automation_client import AutomationServiceClient

async def test_execution_id_fix():
    """Test that execution IDs are properly extracted from automation service responses"""
    
    print("🧪 Testing Execution ID Fix...")
    
    # Initialize automation client
    client = AutomationServiceClient()
    
    # Test 1: Check if automation service is healthy
    print("\n1️⃣ Testing automation service health...")
    is_healthy = await client.health_check()
    if not is_healthy:
        print("❌ Automation service is not healthy!")
        return False
    print("✅ Automation service is healthy")
    
    # Test 2: Create a simple test workflow
    print("\n2️⃣ Creating test workflow...")
    test_workflow = {
        "name": "Test Execution ID Fix",
        "description": "Simple test to verify execution ID extraction",
        "steps": [
            {
                "id": "test_step_1",
                "name": "Echo Test",
                "command": "echo 'Testing execution ID fix'",
                "type": "command",
                "timeout": 30
            }
        ]
    }
    
    try:
        # Submit the workflow
        result = await client.submit_ai_workflow(
            workflow=test_workflow,
            job_name="Execution ID Fix Test"
        )
        
        print(f"📋 Workflow submission result:")
        print(f"   Success: {result.get('success', False)}")
        print(f"   Job ID: {result.get('job_id', 'None')}")
        print(f"   Execution ID: {result.get('execution_id', 'None')}")
        print(f"   Message: {result.get('message', 'No message')}")
        
        # Check if we got a valid execution ID
        execution_id = result.get('execution_id')
        if execution_id and execution_id != 'None':
            print("✅ SUCCESS: Got valid execution ID!")
            print(f"   Execution ID: {execution_id}")
            return True
        else:
            print("❌ FAILED: No valid execution ID returned")
            print(f"   Got: {execution_id}")
            return False
            
    except Exception as e:
        print(f"❌ ERROR: {str(e)}")
        return False

if __name__ == "__main__":
    success = asyncio.run(test_execution_id_fix())
    if success:
        print("\n🎉 Execution ID fix is working!")
        sys.exit(0)
    else:
        print("\n💥 Execution ID fix failed!")
        sys.exit(1)