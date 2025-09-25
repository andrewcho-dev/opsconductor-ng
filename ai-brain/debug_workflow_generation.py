#!/usr/bin/env python3

import asyncio
import sys
import os

# Add the current directory to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from fulfillment_engine.fulfillment_engine import FulfillmentEngine
from fulfillment_engine.execution_coordinator import ExecutionCoordinator
from fulfillment_engine.fulfillment_orchestrator import FulfillmentOrchestrator
from integrations.automation_client import AutomationServiceClient
from integrations.llm_client import LLMEngine

async def debug_workflow_generation():
    """Debug the workflow generation process"""
    
    print("🔍 Debugging workflow generation...")
    
    try:
        # Initialize components
        ollama_host = "http://ollama:11434"
        default_model = "llama3.2:3b"
        llm_engine = LLMEngine(ollama_host, default_model)
        automation_client = AutomationServiceClient("http://localhost:3003")
        
        execution_coordinator = ExecutionCoordinator(
            automation_client=automation_client,
            max_concurrent_steps=3
        )
        
        fulfillment_orchestrator = FulfillmentOrchestrator(
            execution_coordinator=execution_coordinator
        )
        
        fulfillment_engine = FulfillmentEngine(
            llm_engine=llm_engine,
            fulfillment_orchestrator=fulfillment_orchestrator
        )
        
        # Test request - just use the message string
        message = "create a job that pings 192.168.50.210 every 10 seconds"
        
        print(f"📤 Request: {message}")
        
        # Generate workflow
        print("\n🔧 Generating workflow...")
        workflow_result = await fulfillment_engine._generate_workflow(message)
        
        if workflow_result:
            print("✅ Workflow generated successfully!")
            print(f"📋 Workflow Name: {workflow_result.name}")
            print(f"📋 Workflow Description: {workflow_result.description}")
            print(f"📋 Number of Steps: {len(workflow_result.steps)}")
            
            print("\n📝 Workflow Steps:")
            for i, step in enumerate(workflow_result.steps):
                print(f"  Step {i+1}: {step.name}")
                print(f"    Description: {step.description}")
                print(f"    Command: {step.command}")
                print(f"    Script Content: {step.script_content}")
                print(f"    Expected Output: {step.expected_output}")
                print()
            
            # Try to convert to job data
            print("🔧 Converting workflow to job data...")
            job_data = fulfillment_engine._workflow_to_job_data(workflow_result)
            
            print("✅ Job data created:")
            print(f"📋 Job Name: {job_data.get('name', 'N/A')}")
            print(f"📋 Job Description: {job_data.get('description', 'N/A')}")
            print(f"📋 Number of Steps: {len(job_data.get('steps', []))}")
            
            # Test automation client submission
            print("\n🔧 Testing automation client submission...")
            automation_result = await automation_client.submit_ai_workflow(
                workflow=job_data,
                job_name=job_data.get("name", "Debug Test Job")
            )
            
            print("📥 Automation service response:")
            print(f"  Success: {automation_result.get('success', False)}")
            print(f"  Job ID: {automation_result.get('job_id', 'N/A')}")
            print(f"  Job Name: {automation_result.get('job_name', 'N/A')}")
            print(f"  Execution ID: {automation_result.get('execution_id', 'N/A')}")
            print(f"  Error: {automation_result.get('error', 'None')}")
            
            return True
        else:
            print("❌ Workflow generation failed!")
            return False
            
    except Exception as e:
        print(f"❌ Debug failed with exception: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = asyncio.run(debug_workflow_generation())
    if success:
        print("\n🎉 Debug completed!")
    else:
        print("\n💥 Debug failed!")