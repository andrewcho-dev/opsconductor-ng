#!/usr/bin/env python3
"""
Modern AI Brain Integration Test
Tests the clean Prefect-first architecture
"""

import asyncio
import httpx
import json
import time
from datetime import datetime
from typing import Dict, Any

class ModernIntegrationTester:
    """Test the modern AI Brain with Prefect integration"""
    
    def __init__(self, ai_brain_url: str = "http://ai-brain:3005"):
        self.ai_brain_url = ai_brain_url
        self.client = httpx.AsyncClient(timeout=30.0)
        
    async def test_health_check(self) -> bool:
        """Test basic health check"""
        print("🏥 Testing health check...")
        
        try:
            response = await self.client.get(f"{self.ai_brain_url}/health")
            if response.status_code == 200:
                data = response.json()
                print(f"✅ Health check passed: {data['status']}")
                print(f"   Service: {data['service']}")
                print(f"   Version: {data['version']}")
                print(f"   AI Brain Initialized: {data['ai_brain_initialized']}")
                return True
            else:
                print(f"❌ Health check failed: {response.status_code}")
                return False
                
        except Exception as e:
            print(f"❌ Health check error: {e}")
            return False
    
    async def test_capabilities(self) -> bool:
        """Test capabilities endpoint"""
        print("\n🎯 Testing capabilities...")
        
        try:
            response = await self.client.get(f"{self.ai_brain_url}/capabilities")
            if response.status_code == 200:
                data = response.json()
                print("✅ Capabilities retrieved:")
                print(f"   Orchestration Engine: {data['orchestration_engine']}")
                print(f"   Flow Types: {', '.join(data['flow_types'])}")
                print(f"   Features: {len(data['features'])} features")
                print(f"   Integrations: {', '.join(data['integrations'])}")
                return True
            else:
                print(f"❌ Capabilities test failed: {response.status_code}")
                return False
                
        except Exception as e:
            print(f"❌ Capabilities test error: {e}")
            return False
    
    async def test_simple_conversation(self) -> bool:
        """Test simple conversational request"""
        print("\n💬 Testing simple conversation...")
        
        try:
            request = {
                "message": "What can you help me with?",
                "user_id": "test_user",
                "context": {"test": "simple_conversation"}
            }
            
            response = await self.client.post(
                f"{self.ai_brain_url}/chat",
                json=request
            )
            
            if response.status_code == 200:
                data = response.json()
                print("✅ Conversation test passed:")
                print(f"   Intent Type: {data['intent_type']}")
                print(f"   Confidence: {data['confidence']}")
                print(f"   Response: {data['message'][:100]}...")
                print(f"   Conversation ID: {data['conversation_id']}")
                return True
            else:
                print(f"❌ Conversation test failed: {response.status_code}")
                print(f"   Response: {response.text}")
                return False
                
        except Exception as e:
            print(f"❌ Conversation test error: {e}")
            return False
    
    async def test_workflow_creation(self) -> Dict[str, Any]:
        """Test workflow creation and execution"""
        print("\n🔧 Testing workflow creation...")
        
        try:
            request = {
                "message": "Deploy a simple web server with nginx and configure it to serve static files",
                "user_id": "test_user",
                "context": {
                    "environment": "test",
                    "server_type": "nginx"
                }
            }
            
            response = await self.client.post(
                f"{self.ai_brain_url}/chat",
                json=request
            )
            
            if response.status_code == 200:
                data = response.json()
                print("✅ Workflow creation test passed:")
                print(f"   Intent Type: {data['intent_type']}")
                print(f"   Confidence: {data['confidence']}")
                print(f"   Execution Started: {data['execution_started']}")
                
                if data.get('flow_id'):
                    print(f"   Flow ID: {data['flow_id']}")
                if data.get('run_id'):
                    print(f"   Run ID: {data['run_id']}")
                
                print(f"   Response: {data['message'][:200]}...")
                
                return {
                    "success": True,
                    "flow_id": data.get('flow_id'),
                    "run_id": data.get('run_id'),
                    "conversation_id": data['conversation_id']
                }
            else:
                print(f"❌ Workflow creation failed: {response.status_code}")
                print(f"   Response: {response.text}")
                return {"success": False}
                
        except Exception as e:
            print(f"❌ Workflow creation error: {e}")
            return {"success": False}
    
    async def test_flow_status(self, run_id: str) -> bool:
        """Test flow status checking"""
        if not run_id:
            print("⚠️ No run ID provided, skipping status test")
            return True
            
        print(f"\n📊 Testing flow status for run {run_id}...")
        
        try:
            response = await self.client.get(
                f"{self.ai_brain_url}/flows/status/{run_id}"
            )
            
            if response.status_code == 200:
                data = response.json()
                print("✅ Flow status test passed:")
                print(f"   Run ID: {data['run_id']}")
                print(f"   Status: {data['status']}")
                print(f"   Flow Name: {data.get('flow_name', 'N/A')}")
                print(f"   Started At: {data.get('started_at', 'N/A')}")
                return True
            else:
                print(f"❌ Flow status test failed: {response.status_code}")
                return False
                
        except Exception as e:
            print(f"❌ Flow status test error: {e}")
            return False
    
    async def test_active_flows(self) -> bool:
        """Test listing active flows"""
        print("\n📋 Testing active flows listing...")
        
        try:
            response = await self.client.get(f"{self.ai_brain_url}/flows/active")
            
            if response.status_code == 200:
                data = response.json()
                print("✅ Active flows test passed:")
                print(f"   Total Flows: {data['total_count']}")
                
                if data['flows']:
                    print("   Recent flows:")
                    for flow in data['flows'][:3]:  # Show first 3
                        print(f"     • {flow.get('flow_name', 'Unknown')} ({flow.get('status', 'unknown')})")
                else:
                    print("   No active flows found")
                
                return True
            else:
                print(f"❌ Active flows test failed: {response.status_code}")
                return False
                
        except Exception as e:
            print(f"❌ Active flows test error: {e}")
            return False
    
    async def test_legacy_compatibility(self) -> bool:
        """Test legacy endpoint compatibility"""
        print("\n🔄 Testing legacy compatibility...")
        
        try:
            request = {
                "message": "Check system status",
                "user_id": "legacy_user"
            }
            
            response = await self.client.post(
                f"{self.ai_brain_url}/process",
                json=request
            )
            
            if response.status_code == 200:
                data = response.json()
                print("✅ Legacy compatibility test passed:")
                print(f"   Response: {data['response'][:100]}...")
                print(f"   Intent: {data['intent']}")
                print(f"   Migration Notice: {data.get('_modern_migration_notice', 'N/A')[:50]}...")
                return True
            else:
                print(f"❌ Legacy compatibility test failed: {response.status_code}")
                return False
                
        except Exception as e:
            print(f"❌ Legacy compatibility test error: {e}")
            return False
    
    async def run_all_tests(self) -> Dict[str, bool]:
        """Run all integration tests"""
        print("🚀 Starting Modern AI Brain Integration Tests")
        print("=" * 60)
        
        results = {}
        
        # Basic tests
        results["health_check"] = await self.test_health_check()
        results["capabilities"] = await self.test_capabilities()
        results["simple_conversation"] = await self.test_simple_conversation()
        
        # Workflow tests
        workflow_result = await self.test_workflow_creation()
        results["workflow_creation"] = workflow_result["success"]
        
        if workflow_result["success"] and workflow_result.get("run_id"):
            # Wait a moment for workflow to start
            await asyncio.sleep(2)
            results["flow_status"] = await self.test_flow_status(workflow_result["run_id"])
        else:
            results["flow_status"] = True  # Skip if no workflow created
        
        results["active_flows"] = await self.test_active_flows()
        results["legacy_compatibility"] = await self.test_legacy_compatibility()
        
        # Summary
        print("\n" + "=" * 60)
        print("🏁 Test Results Summary:")
        
        passed = sum(1 for result in results.values() if result)
        total = len(results)
        
        for test_name, result in results.items():
            status = "✅ PASS" if result else "❌ FAIL"
            print(f"   {test_name}: {status}")
        
        print(f"\nOverall: {passed}/{total} tests passed")
        
        if passed == total:
            print("🎉 All tests passed! Modern AI Brain is working correctly.")
        else:
            print("⚠️ Some tests failed. Check the logs above for details.")
        
        return results
    
    async def cleanup(self):
        """Cleanup resources"""
        await self.client.aclose()

async def main():
    """Main test function"""
    tester = ModernIntegrationTester()
    
    try:
        results = await tester.run_all_tests()
        return results
    finally:
        await tester.cleanup()

if __name__ == "__main__":
    # Run the tests
    results = asyncio.run(main())
    
    # Exit with appropriate code
    if all(results.values()):
        exit(0)  # All tests passed
    else:
        exit(1)  # Some tests failed