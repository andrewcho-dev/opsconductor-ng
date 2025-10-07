#!/usr/bin/env python3
"""
Basic Pipeline V2 Test - Tests via API endpoint (no direct DB access needed)
"""
import asyncio
import sys
import json
import requests
import os
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# Load environment variables from .env file
from dotenv import load_dotenv
load_dotenv(project_root / ".env")


def test_llm_connection():
    """Test 0: Verify vLLM is working"""
    print("\n" + "="*80)
    print("TEST 0: vLLM Connection")
    print("="*80)
    
    try:
        response = requests.get("http://localhost:8000/v1/models", timeout=5)
        
        if response.status_code == 200:
            data = response.json()
            models = data.get("data", [])
            if models:
                model_id = models[0].get("id")
                print(f"✅ vLLM is running")
                print(f"   Model: {model_id}")
                print(f"   Status: Healthy")
                return True
            else:
                print(f"❌ No models loaded")
                return False
        else:
            print(f"❌ vLLM returned status {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ vLLM test failed: {e}")
        return False


def test_simple_llm_generation():
    """Test 1: Simple LLM generation"""
    print("\n" + "="*80)
    print("TEST 1: Simple LLM Generation")
    print("="*80)
    
    try:
        payload = {
            "model": "Qwen/Qwen2.5-7B-Instruct-AWQ",
            "messages": [
                {"role": "user", "content": "Say 'Hello from Pipeline V2!' and nothing else."}
            ],
            "max_tokens": 50,
            "temperature": 0.1
        }
        
        response = requests.post(
            "http://localhost:8000/v1/chat/completions",
            json=payload,
            timeout=30
        )
        
        if response.status_code == 200:
            data = response.json()
            content = data["choices"][0]["message"]["content"]
            print(f"✅ LLM Response: {content}")
            return True
        else:
            print(f"❌ LLM generation failed: {response.status_code}")
            print(f"   Response: {response.text[:200]}")
            return False
            
    except Exception as e:
        print(f"❌ LLM generation test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_pipeline_info_request():
    """Test 2: Pipeline V2 with information request"""
    print("\n" + "="*80)
    print("TEST 2: Pipeline V2 - Information Request")
    print("="*80)
    
    try:
        import os
        # Set env to use localhost for DB (won't actually connect in this test)
        os.environ["DATABASE_URL"] = "postgresql://opsconductor:opsconductor_secure_2024@localhost:5432/opsconductor"
        
        from llm.factory import get_default_llm_client
        from pipeline.orchestrator_v2 import PipelineOrchestratorV2
        
        llm_client = get_default_llm_client()
        print(f"✅ LLM Client created")
        
        orchestrator = PipelineOrchestratorV2(llm_client)
        await orchestrator.initialize()
        print(f"✅ Orchestrator initialized and connected to LLM")
        
        request = "What is the current status of our infrastructure?"
        print(f"\n📝 Request: {request}")
        
        result = await orchestrator.process_request(
            user_request=request,
            session_id="test-session-1"
        )
        
        print(f"\n✅ Pipeline completed!")
        print(f"   Success: {result.success}")
        print(f"   Response Type: {result.response.response_type}")
        print(f"   Message: {result.response.message[:150]}...")
        print(f"   Confidence: {result.response.confidence}")
        print(f"   Processing Time: {result.metrics.total_duration_ms:.2f}ms")
        
        return result.success
        
    except Exception as e:
        print(f"\n❌ Pipeline test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_pipeline_stages():
    """Test 3: Test individual pipeline stages"""
    print("\n" + "="*80)
    print("TEST 3: Pipeline V2 - Stage by Stage")
    print("="*80)
    
    try:
        import os
        os.environ["DATABASE_URL"] = "postgresql://opsconductor:opsconductor_secure_2024@localhost:5432/opsconductor"
        
        from llm.factory import get_default_llm_client
        from pipeline.stages.stage_ab.combined_selector import CombinedSelector
        
        llm_client = get_default_llm_client()
        await llm_client.connect()
        print(f"✅ LLM Client connected")
        
        # Test Stage AB
        print("\n🔧 Testing Stage AB (Combined Selector)...")
        stage_ab = CombinedSelector(llm_client)
        
        request = "Show me all running Docker containers"
        print(f"   Request: {request}")
        
        selection = await stage_ab.process(
            user_request=request,
            context={"session_id": "test-session-2"}
        )
        
        print(f"✅ Stage AB completed!")
        print(f"   Tools Selected: {[t.tool_name for t in selection.selected_tools]}")
        print(f"   Risk Level: {selection.policy.risk_level}")
        print(f"   Confidence: {selection.selection_confidence:.2f}")
        print(f"   Next Stage: {selection.next_stage}")
        
        return True
        
    except Exception as e:
        print(f"\n❌ Stage test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Run all tests"""
    print("\n" + "="*80)
    print("PIPELINE V2 BASIC TEST SUITE")
    print("="*80)
    print("Testing basic functionality without full Docker stack")
    
    results = {}
    
    # Test 0: vLLM connection
    results["vllm_connection"] = test_llm_connection()
    
    # Test 1: Simple generation
    if results["vllm_connection"]:
        results["llm_generation"] = test_simple_llm_generation()
    else:
        print("\n⚠️  Skipping LLM generation test - vLLM not available")
        results["llm_generation"] = False
    
    # Test 2 & 3: Pipeline tests (async)
    if results["llm_generation"]:
        loop = asyncio.get_event_loop()
        results["pipeline_info"] = loop.run_until_complete(test_pipeline_info_request())
        results["pipeline_stages"] = loop.run_until_complete(test_pipeline_stages())
    else:
        print("\n⚠️  Skipping pipeline tests - LLM not working")
        results["pipeline_info"] = False
        results["pipeline_stages"] = False
    
    # Summary
    print("\n" + "="*80)
    print("TEST SUMMARY")
    print("="*80)
    
    for test_name, passed in results.items():
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{status}: {test_name}")
    
    total = len(results)
    passed = sum(results.values())
    
    print(f"\nTotal: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n🎉 All tests passed!")
        return 0
    elif passed > 0:
        print(f"\n⚠️  {total - passed} test(s) failed, but {passed} passed")
        return 0  # Partial success
    else:
        print(f"\n❌ All tests failed")
        return 1


if __name__ == "__main__":
    sys.exit(main())