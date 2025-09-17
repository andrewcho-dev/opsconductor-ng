#!/usr/bin/env python3
"""Test the frontend integration with new AI endpoints"""

import asyncio
import httpx
import json
import time
from typing import Optional

class FrontendIntegrationTester:
    def __init__(self, base_url: str = "http://localhost:3000"):
        self.base_url = base_url
        self.token: Optional[str] = None
        
    async def login(self) -> bool:
        """Login to get auth token"""
        async with httpx.AsyncClient() as client:
            try:
                response = await client.post(
                    f"{self.base_url}/api/v1/auth/login",
                    json={"username": "admin", "password": "admin123"},
                    timeout=10
                )
                if response.status_code == 200:
                    data = response.json()
                    self.token = data.get("data", {}).get("token")
                    print("✅ Login successful")
                    return True
                else:
                    print(f"❌ Login failed: {response.status_code}")
                    return False
            except Exception as e:
                print(f"❌ Login error: {e}")
                return False
    
    async def test_ai_chat_endpoint(self):
        """Test the /api/v1/ai/chat endpoint as used by frontend"""
        print("\n=== Testing AI Chat Endpoint ===")
        
        if not self.token:
            print("❌ No auth token available")
            return
        
        test_queries = [
            "List all targets",
            "What can you help me with?",
            "Show system health"
        ]
        
        async with httpx.AsyncClient() as client:
            for query in test_queries:
                print(f"\n📝 Query: {query}")
                
                try:
                    response = await client.post(
                        f"{self.base_url}/api/v1/ai/chat",
                        json={"query": query},  # Using 'query' as expected by new endpoint
                        headers={"Authorization": f"Bearer {self.token}"},
                        timeout=30
                    )
                    
                    if response.status_code == 200:
                        data = response.json()
                        print(f"✅ Status: Success")
                        print(f"   Response: {data.get('response', 'No response')[:100]}...")
                        
                        # Check for routing info
                        if '_routing' in data:
                            routing = data['_routing']
                            print(f"   Service: {routing.get('service', 'unknown')}")
                            print(f"   Response Time: {routing.get('response_time', 0):.3f}s")
                            print(f"   Cached: {routing.get('cached', False)}")
                    else:
                        print(f"❌ Request failed: {response.status_code}")
                        print(f"   Response: {response.text[:200]}")
                        
                except Exception as e:
                    print(f"❌ Error: {e}")
                
                await asyncio.sleep(1)  # Small delay between requests
    
    async def test_ai_health_endpoint(self):
        """Test the /api/v1/ai/health endpoint"""
        print("\n=== Testing AI Health Endpoint ===")
        
        if not self.token:
            print("❌ No auth token available")
            return
        
        async with httpx.AsyncClient() as client:
            try:
                response = await client.get(
                    f"{self.base_url}/api/v1/ai/health",
                    headers={"Authorization": f"Bearer {self.token}"},
                    timeout=10
                )
                
                if response.status_code == 200:
                    data = response.json()
                    print(f"✅ Overall Status: {data.get('status', 'unknown')}")
                    
                    # Check services
                    services = data.get('services', {})
                    for service_name, service_data in services.items():
                        print(f"\n   Service: {service_name}")
                        print(f"   - Status: {service_data.get('status', 'unknown')}")
                        print(f"   - Circuit Breaker: {service_data.get('circuit_breaker', 'unknown')}")
                        print(f"   - Success Rate: {service_data.get('success_rate', 0)*100:.1f}%")
                        print(f"   - Avg Response: {service_data.get('avg_response_time', 0):.3f}s")
                else:
                    print(f"❌ Request failed: {response.status_code}")
                    
            except Exception as e:
                print(f"❌ Error: {e}")
    
    async def test_ai_monitoring_dashboard(self):
        """Test the /api/v1/ai/monitoring/dashboard endpoint"""
        print("\n=== Testing AI Monitoring Dashboard ===")
        
        if not self.token:
            print("❌ No auth token available")
            return
        
        async with httpx.AsyncClient() as client:
            try:
                response = await client.get(
                    f"{self.base_url}/api/v1/ai/monitoring/dashboard",
                    headers={"Authorization": f"Bearer {self.token}"},
                    timeout=10
                )
                
                if response.status_code == 200:
                    data = response.json()
                    print(f"✅ Dashboard data received")
                    
                    # Check current metrics
                    current = data.get('current', {})
                    print(f"   Overall Health: {current.get('overall_health', 'unknown')}")
                    
                    # Check for alerts
                    analysis = data.get('analysis', {})
                    alerts = analysis.get('alerts', [])
                    if alerts:
                        print(f"\n   ⚠️  Active Alerts:")
                        for alert in alerts[:3]:  # Show first 3 alerts
                            print(f"   - [{alert.get('severity')}] {alert.get('service')}: {alert.get('message')}")
                    
                    # Check recommendations
                    recommendations = analysis.get('recommendations', [])
                    if recommendations:
                        print(f"\n   💡 Recommendations:")
                        for rec in recommendations[:3]:  # Show first 3 recommendations
                            print(f"   - {rec}")
                else:
                    print(f"❌ Request failed: {response.status_code}")
                    
            except Exception as e:
                print(f"❌ Error: {e}")
    
    async def test_frontend_compatibility(self):
        """Test that frontend components work with new endpoints"""
        print("\n=== Testing Frontend Compatibility ===")
        
        # Test the exact payload format frontend sends
        test_payload = {
            "query": "List all targets"  # Frontend now uses 'query' instead of 'message'
        }
        
        async with httpx.AsyncClient() as client:
            try:
                response = await client.post(
                    f"{self.base_url}/api/v1/ai/chat",
                    json=test_payload,
                    headers={
                        "Authorization": f"Bearer {self.token}",
                        "Content-Type": "application/json"
                    },
                    timeout=30
                )
                
                if response.status_code == 200:
                    data = response.json()
                    
                    # Check response format matches what frontend expects
                    required_fields = ['success', 'response']
                    missing_fields = [f for f in required_fields if f not in data]
                    
                    if not missing_fields:
                        print("✅ Response format compatible with frontend")
                        print(f"   Success: {data.get('success')}")
                        print(f"   Response length: {len(data.get('response', ''))}")
                        
                        # Check optional fields
                        if 'confidence' in data:
                            print(f"   Confidence: {data['confidence']*100:.1f}%")
                        if '_routing' in data:
                            print(f"   Routing info present: ✅")
                    else:
                        print(f"❌ Missing required fields: {missing_fields}")
                else:
                    print(f"❌ Request failed: {response.status_code}")
                    print(f"   Response: {response.text[:200]}")
                    
            except Exception as e:
                print(f"❌ Error: {e}")
    
    async def run_all_tests(self):
        """Run all integration tests"""
        print("🚀 Starting Frontend Integration Tests")
        print("=" * 50)
        
        # Login first
        if not await self.login():
            print("\n❌ Cannot proceed without authentication")
            return
        
        # Run all tests
        await self.test_ai_chat_endpoint()
        await self.test_ai_health_endpoint()
        await self.test_ai_monitoring_dashboard()
        await self.test_frontend_compatibility()
        
        print("\n" + "=" * 50)
        print("✅ Frontend Integration Tests Complete")

async def main():
    """Main entry point"""
    tester = FrontendIntegrationTester()
    await tester.run_all_tests()

if __name__ == "__main__":
    print("\n🔍 Testing Frontend Integration with New AI Endpoints")
    print("Make sure services are running: docker compose up -d")
    print("-" * 50)
    
    asyncio.run(main())