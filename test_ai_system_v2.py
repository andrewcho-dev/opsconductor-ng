#!/usr/bin/env python3
"""
Test Script for OpsConductor AI System V2
Tests the new centralized AI architecture with learning and monitoring
"""
import asyncio
import httpx
import json
import time
from typing import Dict, Any

# Test configuration
API_GATEWAY_URL = "http://localhost:3000"
TEST_TOKEN = None  # Will be set after login

async def login():
    """Login and get authentication token"""
    global TEST_TOKEN
    
    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{API_GATEWAY_URL}/api/v1/auth/login",
            json={
                "username": "admin",
                "password": "admin123"
            }
        )
        
        if response.status_code == 200:
            data = response.json()
            TEST_TOKEN = data.get("data", {}).get("token")
            print(f"✓ Login successful. Token: {TEST_TOKEN[:20]}...")
            return True
        else:
            print(f"✗ Login failed: {response.status_code}")
            return False

async def test_unified_ai_chat():
    """Test the unified AI chat endpoint"""
    print("\n=== Testing Unified AI Chat ===")
    
    test_queries = [
        "List all targets in the system",
        "Show me running jobs",
        "Create a backup workflow for database servers",
        "What's the health status of the system?",
        "Help me troubleshoot a connection issue"
    ]
    
    async with httpx.AsyncClient() as client:
        for query in test_queries:
            print(f"\nQuery: {query}")
            
            response = await client.post(
                f"{API_GATEWAY_URL}/api/v1/ai/chat",
                json={"query": query},
                headers={"Authorization": f"Bearer {TEST_TOKEN}"}
            )
            
            if response.status_code == 200:
                data = response.json()
                print(f"✓ Response received")
                print(f"  Success: {data.get('success')}")
                
                if data.get('_routing'):
                    routing = data['_routing']
                    print(f"  Routed to: {routing.get('service')}")
                    print(f"  Service type: {routing.get('service_type')}")
                    print(f"  Response time: {routing.get('response_time', 0):.2f}s")
                    print(f"  Cached: {routing.get('cached', False)}")
                
                if data.get('response'):
                    print(f"  Response preview: {data['response'][:100]}...")
            else:
                print(f"✗ Failed: {response.status_code}")
                print(f"  Error: {response.text}")
            
            await asyncio.sleep(1)  # Rate limiting

async def test_ai_health():
    """Test AI health endpoint"""
    print("\n=== Testing AI Health Check ===")
    
    async with httpx.AsyncClient() as client:
        response = await client.get(
            f"{API_GATEWAY_URL}/api/v1/ai/health",
            headers={"Authorization": f"Bearer {TEST_TOKEN}"}
        )
        
        if response.status_code == 200:
            data = response.json()
            print(f"✓ Overall status: {data.get('status')}")
            
            services = data.get('services', {})
            for service_name, service_data in services.items():
                status = service_data.get('status', 'unknown')
                symbol = "✓" if status == "healthy" else "✗"
                print(f"  {symbol} {service_name}: {status}")
                
                if service_data.get('circuit_breaker'):
                    print(f"      Circuit breaker: {service_data['circuit_breaker']}")
                if service_data.get('success_rate') is not None:
                    print(f"      Success rate: {service_data['success_rate']:.2%}")
                if service_data.get('avg_response_time'):
                    print(f"      Avg response: {service_data['avg_response_time']:.3f}s")
        else:
            print(f"✗ Health check failed: {response.status_code}")

async def test_ai_monitoring_dashboard():
    """Test AI monitoring dashboard"""
    print("\n=== Testing AI Monitoring Dashboard ===")
    
    async with httpx.AsyncClient() as client:
        response = await client.get(
            f"{API_GATEWAY_URL}/api/v1/ai/monitoring/dashboard",
            headers={"Authorization": f"Bearer {TEST_TOKEN}"}
        )
        
        if response.status_code == 200:
            data = response.json()
            print(f"✓ Dashboard data received")
            
            # Current metrics
            if data.get('current'):
                current = data['current']
                print(f"\nCurrent Metrics:")
                for service, metrics in current.get('services', {}).items():
                    print(f"  {service}:")
                    print(f"    Status: {metrics.get('status')}")
                    if metrics.get('response_time'):
                        print(f"    Response time: {metrics['response_time']:.3f}s")
            
            # Analysis
            if data.get('analysis'):
                analysis = data['analysis']
                print(f"\nAnalysis:")
                print(f"  Overall health: {analysis.get('overall_health')}")
                
                # Alerts
                alerts = analysis.get('alerts', [])
                if alerts:
                    print(f"  Alerts ({len(alerts)}):")
                    for alert in alerts[:3]:  # Show first 3
                        print(f"    [{alert['severity']}] {alert['message']}")
                
                # Recommendations
                recommendations = analysis.get('recommendations', [])
                if recommendations:
                    print(f"  Recommendations:")
                    for rec in recommendations[:3]:  # Show first 3
                        print(f"    - {rec}")
        else:
            print(f"✗ Dashboard request failed: {response.status_code}")

async def test_ai_feedback():
    """Test AI feedback submission"""
    print("\n=== Testing AI Feedback System ===")
    
    # First, make a query to get an interaction ID
    async with httpx.AsyncClient() as client:
        # Make a test query
        response = await client.post(
            f"{API_GATEWAY_URL}/api/v1/ai/chat",
            json={"query": "Test query for feedback"},
            headers={"Authorization": f"Bearer {TEST_TOKEN}"}
        )
        
        if response.status_code == 200:
            data = response.json()
            # Generate a test interaction ID
            interaction_id = f"test_{int(time.time())}"
            
            # Submit feedback
            feedback_response = await client.post(
                f"{API_GATEWAY_URL}/api/v1/ai/feedback",
                json={
                    "interaction_id": interaction_id,
                    "rating": 4,
                    "comment": "Good response, very helpful",
                    "correction": None
                },
                headers={"Authorization": f"Bearer {TEST_TOKEN}"}
            )
            
            if feedback_response.status_code == 200:
                feedback_data = feedback_response.json()
                print(f"✓ Feedback submitted successfully")
                print(f"  Feedback ID: {feedback_data.get('feedback_id')}")
                print(f"  Message: {feedback_data.get('message')}")
            else:
                print(f"✗ Feedback submission failed: {feedback_response.status_code}")
        else:
            print(f"✗ Initial query failed: {response.status_code}")

async def test_service_monitoring():
    """Test individual service monitoring"""
    print("\n=== Testing Individual Service Monitoring ===")
    
    services_to_check = ["ai_command", "nlp_service", "vector_service"]
    
    async with httpx.AsyncClient() as client:
        for service in services_to_check:
            print(f"\nChecking {service}:")
            
            response = await client.get(
                f"{API_GATEWAY_URL}/api/v1/ai/monitoring/service/{service}",
                headers={"Authorization": f"Bearer {TEST_TOKEN}"}
            )
            
            if response.status_code == 200:
                data = response.json()
                
                if data.get('error'):
                    print(f"  ✗ {data['error']}")
                else:
                    stats = data.get('statistics', {})
                    print(f"  ✓ Service URL: {data.get('url')}")
                    print(f"    Availability: {stats.get('availability', 0):.2%}")
                    
                    if stats.get('avg_response_time'):
                        print(f"    Avg response: {stats['avg_response_time']:.3f}s")
                    if stats.get('min_response_time'):
                        print(f"    Min response: {stats['min_response_time']:.3f}s")
                    if stats.get('max_response_time'):
                        print(f"    Max response: {stats['max_response_time']:.3f}s")
                    
                    print(f"    Samples: {stats.get('sample_count', 0)}")
            else:
                print(f"  ✗ Request failed: {response.status_code}")

async def test_circuit_breaker():
    """Test circuit breaker functionality"""
    print("\n=== Testing Circuit Breaker ===")
    
    # This test requires admin privileges
    async with httpx.AsyncClient() as client:
        # Try to reset circuit breaker for a service
        response = await client.post(
            f"{API_GATEWAY_URL}/api/v1/ai/circuit-breaker/reset/ai_command",
            headers={"Authorization": f"Bearer {TEST_TOKEN}"}
        )
        
        if response.status_code == 200:
            data = response.json()
            print(f"✓ Circuit breaker reset successful")
            print(f"  Message: {data.get('message')}")
        elif response.status_code == 403:
            print(f"✗ Access denied (admin only)")
        else:
            print(f"✗ Reset failed: {response.status_code}")

async def stress_test_ai():
    """Perform a simple stress test"""
    print("\n=== AI System Stress Test ===")
    
    num_requests = 10
    queries = [
        "List targets",
        "Show jobs",
        "Check health",
        "Get metrics",
        "Help"
    ]
    
    print(f"Sending {num_requests} concurrent requests...")
    
    async with httpx.AsyncClient() as client:
        tasks = []
        
        for i in range(num_requests):
            query = queries[i % len(queries)]
            task = client.post(
                f"{API_GATEWAY_URL}/api/v1/ai/chat",
                json={"query": f"{query} #{i}"},
                headers={"Authorization": f"Bearer {TEST_TOKEN}"},
                timeout=30.0
            )
            tasks.append(task)
        
        start_time = time.time()
        responses = await asyncio.gather(*tasks, return_exceptions=True)
        end_time = time.time()
        
        # Analyze results
        successful = 0
        failed = 0
        total_time = end_time - start_time
        
        for response in responses:
            if isinstance(response, Exception):
                failed += 1
                print(f"  ✗ Request failed: {type(response).__name__}")
            elif response.status_code == 200:
                successful += 1
            else:
                failed += 1
                print(f"  ✗ HTTP {response.status_code}")
        
        print(f"\nResults:")
        print(f"  Total time: {total_time:.2f}s")
        print(f"  Successful: {successful}/{num_requests}")
        print(f"  Failed: {failed}/{num_requests}")
        print(f"  Avg time per request: {total_time/num_requests:.2f}s")
        
        if successful == num_requests:
            print("  ✓ All requests succeeded!")
        elif successful > 0:
            print(f"  ⚠ Partial success ({successful}/{num_requests})")
        else:
            print("  ✗ All requests failed")

async def main():
    """Run all tests"""
    print("=" * 60)
    print("OpsConductor AI System V2 Test Suite")
    print("=" * 60)
    
    # Login first
    if not await login():
        print("Cannot proceed without authentication")
        return
    
    # Run tests
    tests = [
        ("Unified AI Chat", test_unified_ai_chat),
        ("AI Health Check", test_ai_health),
        ("Monitoring Dashboard", test_ai_monitoring_dashboard),
        ("Feedback System", test_ai_feedback),
        ("Service Monitoring", test_service_monitoring),
        ("Circuit Breaker", test_circuit_breaker),
        ("Stress Test", stress_test_ai)
    ]
    
    for test_name, test_func in tests:
        try:
            await test_func()
        except Exception as e:
            print(f"\n✗ Test '{test_name}' failed with error: {e}")
    
    print("\n" + "=" * 60)
    print("Test suite completed!")
    print("=" * 60)

if __name__ == "__main__":
    asyncio.run(main())