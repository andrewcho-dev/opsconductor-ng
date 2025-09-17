#!/usr/bin/env python3
"""
Test script for AI microservices architecture
Tests NLP, Vector, LLM, and AI Orchestrator services
"""
import asyncio
import httpx
import json
import time
from typing import Dict, Any

# Service URLs
SERVICES = {
    "nlp": "http://localhost:3006",
    "vector": "http://localhost:3007", 
    "llm": "http://localhost:3008",
    "orchestrator": "http://localhost:3005"
}

class AIServiceTester:
    def __init__(self):
        self.results = {}
        
    async def test_service_health(self, service_name: str, url: str) -> bool:
        """Test if a service is healthy"""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(f"{url}/health", timeout=10.0)
                if response.status_code == 200:
                    print(f"✅ {service_name.upper()} service is healthy")
                    return True
                else:
                    print(f"❌ {service_name.upper()} service unhealthy: {response.status_code}")
                    return False
        except Exception as e:
            print(f"❌ {service_name.upper()} service connection failed: {e}")
            return False
    
    async def test_nlp_service(self) -> Dict[str, Any]:
        """Test NLP service functionality"""
        print("\n🧠 Testing NLP Service...")
        
        test_cases = [
            "restart nginx on web servers",
            "update stationcontroller on CIS servers", 
            "check status of MySQL on database servers",
            "What is the current CPU usage?",
            "stop Apache service on all servers"
        ]
        
        results = []
        
        try:
            async with httpx.AsyncClient() as client:
                for text in test_cases:
                    print(f"  Testing: '{text}'")
                    
                    # Test parsing
                    parse_response = await client.post(
                        f"{SERVICES['nlp']}/nlp/parse",
                        json={"text": text}
                    )
                    
                    # Test classification
                    classify_response = await client.post(
                        f"{SERVICES['nlp']}/nlp/classify", 
                        json={"text": text}
                    )
                    
                    if parse_response.status_code == 200 and classify_response.status_code == 200:
                        parse_data = parse_response.json()
                        classify_data = classify_response.json()
                        
                        result = {
                            "text": text,
                            "operation": parse_data.get("operation"),
                            "target_process": parse_data.get("target_process"),
                            "target_group": parse_data.get("target_group"),
                            "intent": classify_data.get("intent"),
                            "confidence": parse_data.get("confidence")
                        }
                        results.append(result)
                        print(f"    ✅ Operation: {result['operation']}, Intent: {result['intent']}, Confidence: {result['confidence']:.2f}")
                    else:
                        print(f"    ❌ Failed to process text")
                        
        except Exception as e:
            print(f"❌ NLP service test failed: {e}")
            
        return {"nlp_tests": results}
    
    async def test_vector_service(self) -> Dict[str, Any]:
        """Test Vector service functionality"""
        print("\n🔍 Testing Vector Service...")
        
        results = []
        
        try:
            async with httpx.AsyncClient() as client:
                # Test storing knowledge
                print("  Testing knowledge storage...")
                store_response = await client.post(
                    f"{SERVICES['vector']}/vector/store",
                    json={
                        "content": "To restart nginx service, use 'sudo systemctl restart nginx' on Linux systems",
                        "category": "system_administration",
                        "title": "Nginx Restart Procedure"
                    }
                )
                
                if store_response.status_code == 200:
                    print("    ✅ Knowledge stored successfully")
                    
                    # Test searching knowledge
                    print("  Testing knowledge search...")
                    search_response = await client.post(
                        f"{SERVICES['vector']}/vector/search",
                        json={"query": "how to restart nginx", "limit": 3}
                    )
                    
                    if search_response.status_code == 200:
                        search_data = search_response.json()
                        results.append({
                            "stored_knowledge": True,
                            "search_results": len(search_data.get("results", [])),
                            "search_successful": True
                        })
                        print(f"    ✅ Found {len(search_data.get('results', []))} relevant results")
                    else:
                        print("    ❌ Knowledge search failed")
                else:
                    print("    ❌ Knowledge storage failed")
                    
                # Test vector stats
                print("  Testing vector statistics...")
                stats_response = await client.get(f"{SERVICES['vector']}/vector/stats")
                if stats_response.status_code == 200:
                    stats_data = stats_response.json()
                    print(f"    ✅ Vector stats: {stats_data.get('total_documents', 0)} total documents")
                    
        except Exception as e:
            print(f"❌ Vector service test failed: {e}")
            
        return {"vector_tests": results}
    
    async def test_llm_service(self) -> Dict[str, Any]:
        """Test LLM service functionality"""
        print("\n🤖 Testing LLM Service...")
        
        results = []
        
        try:
            async with httpx.AsyncClient() as client:
                # Test chat functionality
                print("  Testing chat functionality...")
                chat_response = await client.post(
                    f"{SERVICES['llm']}/llm/chat",
                    json={
                        "message": "What is OpsConductor?",
                        "system_prompt": "You are OpsConductor AI, an IT operations assistant."
                    },
                    timeout=30.0
                )
                
                if chat_response.status_code == 200:
                    chat_data = chat_response.json()
                    print(f"    ✅ Chat response generated (confidence: {chat_data.get('confidence', 0):.2f})")
                    results.append({
                        "chat_test": True,
                        "response_length": len(chat_data.get("response", "")),
                        "confidence": chat_data.get("confidence", 0)
                    })
                else:
                    print("    ❌ Chat test failed")
                
                # Test text analysis
                print("  Testing text analysis...")
                analyze_response = await client.post(
                    f"{SERVICES['llm']}/llm/analyze",
                    json={
                        "text": "I need to restart the web server urgently!",
                        "analysis_type": "sentiment"
                    },
                    timeout=30.0
                )
                
                if analyze_response.status_code == 200:
                    analyze_data = analyze_response.json()
                    print(f"    ✅ Text analysis completed")
                    results.append({
                        "analysis_test": True,
                        "analysis_result": analyze_data.get("result", {})
                    })
                else:
                    print("    ❌ Text analysis failed")
                    
        except Exception as e:
            print(f"❌ LLM service test failed: {e}")
            
        return {"llm_tests": results}
    
    async def test_orchestrator_service(self) -> Dict[str, Any]:
        """Test AI Orchestrator service functionality"""
        print("\n🎭 Testing AI Orchestrator Service...")
        
        results = []
        
        try:
            async with httpx.AsyncClient() as client:
                # Test chat interface
                print("  Testing orchestrated chat...")
                chat_response = await client.post(
                    f"{SERVICES['orchestrator']}/ai/chat",
                    json={
                        "message": "restart nginx on web servers",
                        "user_id": 1
                    },
                    timeout=30.0
                )
                
                if chat_response.status_code == 200:
                    chat_data = chat_response.json()
                    print(f"    ✅ Orchestrated chat successful")
                    print(f"    Intent: {chat_data.get('intent')}")
                    print(f"    Response: {chat_data.get('response', '')[:100]}...")
                    
                    results.append({
                        "orchestrated_chat": True,
                        "intent": chat_data.get("intent"),
                        "confidence": chat_data.get("confidence"),
                        "workflow_created": chat_data.get("workflow") is not None
                    })
                else:
                    print("    ❌ Orchestrated chat failed")
                
                # Test job creation
                print("  Testing job creation...")
                job_response = await client.post(
                    f"{SERVICES['orchestrator']}/ai/create-job",
                    json={
                        "description": "update stationcontroller on CIS servers",
                        "user_id": 1
                    },
                    timeout=30.0
                )
                
                if job_response.status_code == 200:
                    job_data = job_response.json()
                    print(f"    ✅ Job created successfully")
                    print(f"    Job ID: {job_data.get('job_id')}")
                    print(f"    Workflow steps: {len(job_data.get('workflow', {}).get('steps', []))}")
                    
                    results.append({
                        "job_creation": True,
                        "job_id": job_data.get("job_id"),
                        "workflow_steps": len(job_data.get("workflow", {}).get("steps", []))
                    })
                else:
                    print("    ❌ Job creation failed")
                    
        except Exception as e:
            print(f"❌ Orchestrator service test failed: {e}")
            
        return {"orchestrator_tests": results}
    
    async def test_service_integration(self) -> Dict[str, Any]:
        """Test integration between services"""
        print("\n🔗 Testing Service Integration...")
        
        results = []
        
        try:
            # Test full pipeline: NLP -> Vector -> LLM -> Orchestrator
            test_message = "I need help restarting the database service on production servers"
            
            async with httpx.AsyncClient() as client:
                # Store some relevant knowledge first
                await client.post(
                    f"{SERVICES['vector']}/vector/store",
                    json={
                        "content": "Database restart procedure: 1. Check current connections 2. Stop service gracefully 3. Restart service 4. Verify connectivity",
                        "category": "database_operations",
                        "title": "Database Restart Best Practices"
                    }
                )
                
                # Test orchestrated response that should use all services
                start_time = time.time()
                response = await client.post(
                    f"{SERVICES['orchestrator']}/ai/chat",
                    json={"message": test_message, "user_id": 1},
                    timeout=45.0
                )
                end_time = time.time()
                
                if response.status_code == 200:
                    data = response.json()
                    print(f"    ✅ Full pipeline test successful")
                    print(f"    Processing time: {end_time - start_time:.2f} seconds")
                    print(f"    Intent detected: {data.get('intent')}")
                    
                    results.append({
                        "full_pipeline": True,
                        "processing_time": end_time - start_time,
                        "intent_detected": data.get("intent"),
                        "response_generated": len(data.get("response", "")) > 0
                    })
                else:
                    print("    ❌ Full pipeline test failed")
                    
        except Exception as e:
            print(f"❌ Integration test failed: {e}")
            
        return {"integration_tests": results}
    
    async def run_all_tests(self):
        """Run all tests"""
        print("🚀 Starting AI Microservices Test Suite")
        print("=" * 50)
        
        # Test service health
        print("\n🏥 Testing Service Health...")
        health_results = {}
        for service_name, url in SERVICES.items():
            health_results[service_name] = await self.test_service_health(service_name, url)
        
        # Only proceed with functional tests if all services are healthy
        healthy_services = sum(health_results.values())
        total_services = len(health_results)
        
        print(f"\n📊 Health Check Results: {healthy_services}/{total_services} services healthy")
        
        if healthy_services < total_services:
            print("⚠️  Some services are unhealthy. Functional tests may fail.")
        
        # Run functional tests
        self.results["health"] = health_results
        self.results.update(await self.test_nlp_service())
        self.results.update(await self.test_vector_service())
        self.results.update(await self.test_llm_service())
        self.results.update(await self.test_orchestrator_service())
        self.results.update(await self.test_service_integration())
        
        # Print summary
        print("\n" + "=" * 50)
        print("📋 Test Summary")
        print("=" * 50)
        
        total_tests = 0
        passed_tests = 0
        
        for category, tests in self.results.items():
            if category == "health":
                continue
            if isinstance(tests, list):
                total_tests += len(tests)
                passed_tests += len([t for t in tests if any(v for v in t.values() if v is True)])
        
        print(f"Total functional tests: {total_tests}")
        print(f"Passed tests: {passed_tests}")
        print(f"Success rate: {(passed_tests/total_tests*100) if total_tests > 0 else 0:.1f}%")
        
        # Save detailed results
        with open("ai_microservices_test_results.json", "w") as f:
            json.dump(self.results, f, indent=2, default=str)
        
        print(f"\n💾 Detailed results saved to: ai_microservices_test_results.json")
        
        if healthy_services == total_services and passed_tests == total_tests:
            print("\n🎉 All tests passed! AI microservices architecture is working correctly.")
            return True
        else:
            print("\n⚠️  Some tests failed. Check the results for details.")
            return False

async def main():
    """Main test function"""
    tester = AIServiceTester()
    success = await tester.run_all_tests()
    return 0 if success else 1

if __name__ == "__main__":
    import sys
    sys.exit(asyncio.run(main()))