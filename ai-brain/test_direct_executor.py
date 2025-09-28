#!/usr/bin/env python3
"""
Test Direct Executor - Simple Ollama-driven execution
"""

import asyncio
import sys
import os

# Add the shared directory to the path
sys.path.append('/home/opsconductor/opsconductor-ng/shared')

from fulfillment_engine.direct_executor import DirectExecutor
from integrations.llm_client import LLMEngine
from integrations.automation_client import AutomationServiceClient

async def test_direct_executor():
    """Test the direct executor with a simple request"""
    
    print("🚀 Testing Direct Executor - Ollama makes ALL decisions!")
    
    # Initialize LLM engine
    ollama_host = os.getenv("OLLAMA_HOST", "http://ollama:11434")  # Use Docker service name
    default_model = os.getenv("DEFAULT_MODEL", "llama3.2:3b")
    llm_engine = LLMEngine(ollama_host, default_model)
    
    # Initialize automation client
    automation_client = AutomationServiceClient(os.getenv("AUTOMATION_SERVICE_URL", "http://automation-service:3003"))
    
    # Initialize direct executor
    direct_executor = DirectExecutor(
        llm_engine=llm_engine,
        automation_client=automation_client
    )
    
    # Test with a simple request
    test_message = "run echo hello world on target-host"
    
    print(f"\n🧠 Testing with message: '{test_message}'")
    print("=" * 60)
    
    try:
        # Initialize LLM engine
        llm_success = await llm_engine.initialize()
        if not llm_success:
            print("❌ Failed to initialize LLM engine")
            return False
        
        print("✅ LLM engine initialized")
        
        # Execute the request
        result = await direct_executor.execute_user_request(test_message)
        
        print("\n📋 EXECUTION RESULT:")
        print(f"Status: {result.get('status')}")
        print(f"Message: {result.get('message')}")
        
        if result.get('job_details'):
            print("\n📋 Job Details:")
            for job_detail in result['job_details']:
                print(f"  • Job: {job_detail.get('job_name')}")
                print(f"    ID: {job_detail.get('job_id')}")
                print(f"    Execution: {job_detail.get('execution_id')}")
        
        if result.get('execution_plan'):
            print(f"\n🧠 Ollama's Plan:\n{result['execution_plan']}")
        
        if result.get('execution_response'):
            print(f"\n🚀 Ollama's Execution:\n{result['execution_response']}")
        
        success = result.get('status') == 'completed'
        print(f"\n{'✅ SUCCESS' if success else '❌ FAILED'}: Direct execution test")
        return success
        
    except Exception as e:
        print(f"❌ Test failed with exception: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = asyncio.run(test_direct_executor())
    sys.exit(0 if success else 1)