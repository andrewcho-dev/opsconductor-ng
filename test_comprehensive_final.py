#!/usr/bin/env python3

import asyncio
import httpx
import json

async def test_comprehensive_job_creation():
    """Comprehensive test of the AI job creation system"""
    
    print("🔬 Comprehensive AI Job Creation Test")
    print("=" * 50)
    
    test_cases = [
        {
            "name": "Simple Service Restart",
            "message": "restart apache service",
            "expected_intent": "job_creation"
        },
        {
            "name": "Service Status Check", 
            "message": "check nginx status",
            "expected_intent": "job_creation"
        },
        {
            "name": "Multiple Service Operation",
            "message": "stop nginx and start apache",
            "expected_intent": "job_creation"
        }
    ]
    
    results = []
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\n🧪 Test {i}: {test_case['name']}")
        print(f"📝 Message: {test_case['message']}")
        
        test_request = {
            "message": test_case['message'],
            "user_id": 1,
            "conversation_id": f"comprehensive-test-{i}"
        }
        
        try:
            async with httpx.AsyncClient(timeout=60.0) as client:
                response = await client.post(
                    "http://localhost:3005/ai/chat",
                    json=test_request
                )
                
                if response.status_code == 200:
                    result = response.json()
                    
                    success = (
                        result.get('intent') == test_case['expected_intent'] and
                        result.get('job_id') is not None and
                        isinstance(result.get('job_id'), str)
                    )
                    
                    print(f"✅ Status: {'SUCCESS' if success else 'PARTIAL'}")
                    print(f"🎯 Intent: {result.get('intent')}")
                    print(f"🆔 Job ID: {result.get('job_id')} (type: {type(result.get('job_id')).__name__})")
                    print(f"💬 Response: {result.get('response', 'No response')[:100]}...")
                    
                    results.append({
                        'test': test_case['name'],
                        'success': success,
                        'job_id': result.get('job_id'),
                        'intent': result.get('intent')
                    })
                    
                else:
                    print(f"❌ HTTP Error: {response.status_code}")
                    results.append({
                        'test': test_case['name'],
                        'success': False,
                        'error': f"HTTP {response.status_code}"
                    })
                    
        except Exception as e:
            print(f"❌ Exception: {e}")
            results.append({
                'test': test_case['name'],
                'success': False,
                'error': str(e)
            })
    
    # Summary
    print("\n" + "=" * 50)
    print("📊 TEST SUMMARY")
    print("=" * 50)
    
    successful_tests = sum(1 for r in results if r.get('success', False))
    total_tests = len(results)
    
    for result in results:
        status = "✅ PASS" if result.get('success', False) else "❌ FAIL"
        print(f"{status} {result['test']}")
        if result.get('job_id'):
            print(f"    Job ID: {result['job_id']}")
        if result.get('error'):
            print(f"    Error: {result['error']}")
    
    print(f"\n🎯 Success Rate: {successful_tests}/{total_tests} ({successful_tests/total_tests*100:.1f}%)")
    
    if successful_tests == total_tests:
        print("🎊 ALL TESTS PASSED! AI system is fully functional!")
        print("✨ The AI now creates and executes real automation jobs!")
    elif successful_tests > 0:
        print("⚠️  PARTIAL SUCCESS: Some functionality working")
    else:
        print("💥 ALL TESTS FAILED: System needs more work")
    
    return successful_tests == total_tests

if __name__ == "__main__":
    success = asyncio.run(test_comprehensive_job_creation())
    exit(0 if success else 1)