#!/usr/bin/env python3
"""
Simple Pipeline V2 Test - Tests basic functionality without Docker dependencies
"""
import asyncio
import sys
import os
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# Override DATABASE_URL to use localhost instead of postgres hostname
os.environ["DATABASE_URL"] = "postgresql://opsconductor:opsconductor_secure_2024@localhost:5432/opsconductor"

from pipeline.orchestrator_v2 import PipelineOrchestratorV2
from llm.factory import get_default_llm_client


async def test_simple_info_request():
    """Test 1: Simple information request (no execution)"""
    print("\n" + "="*80)
    print("TEST 1: Simple Information Request")
    print("="*80)
    
    try:
        llm_client = get_default_llm_client()
        orchestrator = PipelineOrchestratorV2(llm_client)
        
        request = "What servers do we have in production?"
        print(f"\n📝 Request: {request}")
        
        result = await orchestrator.process_request(
            user_request=request,
            session_id="test-session-1"
        )
        
        print(f"\n✅ Status: {result.status}")
        print(f"📊 Intent: {result.intent}")
        print(f"🔧 Tools Selected: {[t.tool_name for t in result.selected_tools]}")
        print(f"📋 Plan: {result.plan.plan_type if result.plan else 'None'}")
        print(f"💬 Response Preview: {result.response[:200]}...")
        
        return result.status == "success"
        
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_simple_execution_request():
    """Test 2: Simple execution request"""
    print("\n" + "="*80)
    print("TEST 2: Simple Execution Request")
    print("="*80)
    
    try:
        llm_client = get_default_llm_client()
        orchestrator = PipelineOrchestratorV2(llm_client)
        
        request = "List all running Docker containers"
        print(f"\n📝 Request: {request}")
        
        result = await orchestrator.process_request(
            user_request=request,
            session_id="test-session-2"
        )
        
        print(f"\n✅ Status: {result.status}")
        print(f"📊 Intent: {result.intent}")
        print(f"🔧 Tools Selected: {[t.tool_name for t in result.selected_tools]}")
        print(f"📋 Plan: {result.plan.plan_type if result.plan else 'None'}")
        print(f"💬 Response Preview: {result.response[:200]}...")
        
        return result.status == "success"
        
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_llm_connection():
    """Test 0: Verify LLM is working"""
    print("\n" + "="*80)
    print("TEST 0: LLM Connection")
    print("="*80)
    
    try:
        from llm.client import LLMRequest
        
        llm_client = get_default_llm_client()
        print(f"✅ LLM Client initialized")
        print(f"   Provider: {llm_client.provider}")
        print(f"   Base URL: {llm_client.base_url}")
        print(f"   Model: {llm_client.model}")
        
        # Test simple generation
        response = await llm_client.generate(
            LLMRequest(
                prompt="Say 'Hello from Pipeline V2!' and nothing else.",
                max_tokens=50
            )
        )
        
        print(f"\n✅ LLM Response: {response.content}")
        return True
        
    except Exception as e:
        print(f"\n❌ LLM test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_database_connection():
    """Test -1: Verify database is accessible"""
    print("\n" + "="*80)
    print("TEST -1: Database Connection")
    print("="*80)
    
    try:
        import psycopg2
        
        conn = psycopg2.connect(
            host="localhost",
            port=5432,
            database="opsconductor",
            user="opsconductor",
            password="opsconductor_secure_2024"
        )
        
        cursor = conn.cursor()
        cursor.execute("SELECT version();")
        version = cursor.fetchone()
        
        print(f"✅ Database connected: {version[0][:50]}...")
        
        cursor.close()
        conn.close()
        
        return True
        
    except Exception as e:
        print(f"\n❌ Database test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


async def main():
    """Run all tests"""
    print("\n" + "="*80)
    print("PIPELINE V2 SIMPLE TEST SUITE")
    print("="*80)
    
    results = {}
    
    # Test database
    results["database"] = await test_database_connection()
    
    # Test LLM
    results["llm"] = await test_llm_connection()
    
    # Only run pipeline tests if basics work
    if results["database"] and results["llm"]:
        results["info_request"] = await test_simple_info_request()
        results["execution_request"] = await test_simple_execution_request()
    else:
        print("\n⚠️  Skipping pipeline tests - prerequisites failed")
        results["info_request"] = False
        results["execution_request"] = False
    
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
    else:
        print(f"\n❌ {total - passed} test(s) failed")
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)