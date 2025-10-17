#!/usr/bin/env python3
import asyncio
import sys
import os
import time

# Add current directory to path
sys.path.insert(0, '/home/opsconductor/opsconductor-ng')

from pipeline.orchestrator import PipelineOrchestrator
from llm.ollama_client import OllamaClient

async def test_hostname_command():
    """Test the specific hostname command that's failing"""
    print("🔧 Initializing pipeline...")
    
    # Configure LLM client
    llm_config = {
        'base_url': 'http://localhost:11434',
        'default_model': 'qwen2.5:7b-instruct-q4_k_m',
        'timeout': 120
    }
    
    try:
        # Initialize components
        llm_client = OllamaClient(llm_config)
        await llm_client.connect()
        print("✅ LLM client connected")
        
        orchestrator = PipelineOrchestrator(llm_client=llm_client)
        await orchestrator.initialize()
        print("✅ Orchestrator initialized")
        
        # Test the failing command
        command = "Display contents of /etc/hostname on 192.168.50.12"
        print(f"\n🚀 Testing: {command}")
        print("=" * 80)
        
        start_time = time.time()
        
        try:
            result = await orchestrator.process_request(command)
            
            duration = time.time() - start_time
            print(f"\n⏱️  Total time: {duration:.2f}s")
            print(f"✅ Success: {result.success}")
            
            if result.response:
                print(f"\n📄 Response:\n{result.response.message}")
            
            if hasattr(result, 'error') and result.error:
                print(f"\n❌ Error: {result.error}")
                
            if hasattr(result, 'stage_results'):
                print(f"\n🔍 Stage results available: {len(result.stage_results) if result.stage_results else 0}")
                
        except Exception as e:
            duration = time.time() - start_time
            print(f"\n💥 Exception after {duration:.2f}s:")
            print(f"   Type: {type(e).__name__}")
            print(f"   Message: {str(e)}")
            import traceback
            print("\n📊 Full traceback:")
            traceback.print_exc()
        
        finally:
            # Note: OllamaClient doesn't have a close() method
            print("\n🔒 Test completed")
            
    except Exception as init_error:
        print(f"💥 Initialization failed: {init_error}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_hostname_command())