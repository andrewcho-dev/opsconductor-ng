#!/usr/bin/env python3
"""
Comprehensive Job Engine Test Suite
Tests all AI Brain Job Engine endpoints and functionality
"""

import asyncio
import aiohttp
import json
import time
from typing import Dict, Any

# AI Brain service configuration
AI_BRAIN_URL = "http://localhost:3005"

class JobEngineTestSuite:
    def __init__(self):
        self.session = None
        self.test_results = []
        
    async def __aenter__(self):
        self.session = aiohttp.ClientSession()
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()
    
    async def test_endpoint(self, name: str, method: str, endpoint: str, data: Dict[Any, Any] = None) -> Dict[str, Any]:
        """Test a single endpoint and return results"""
        print(f"\n🧪 Testing {name}...")
        
        try:
            url = f"{AI_BRAIN_URL}{endpoint}"
            
            if method.upper() == "GET":
                async with self.session.get(url) as response:
                    status = response.status
                    result = await response.json()
            elif method.upper() == "POST":
                async with self.session.post(url, json=data) as response:
                    status = response.status
                    result = await response.json()
            else:
                raise ValueError(f"Unsupported method: {method}")
            
            success = status == 200
            
            test_result = {
                "name": name,
                "endpoint": endpoint,
                "method": method,
                "status_code": status,
                "success": success,
                "response": result,
                "error": None
            }
            
            if success:
                print(f"✅ {name} - SUCCESS")
                if isinstance(result, dict):
                    # Print key information from response
                    if "job_id" in result:
                        print(f"   📋 Job ID: {result['job_id']}")
                    if "workflow" in result and isinstance(result["workflow"], dict):
                        workflow = result["workflow"]
                        print(f"   🔄 Workflow: {workflow.get('name', 'N/A')}")
                        print(f"   📝 Steps: {len(workflow.get('steps', []))}")
                    if "message" in result:
                        print(f"   💬 Message: {result['message']}")
                    if "confidence" in result:
                        print(f"   🎯 Confidence: {result['confidence']:.2f}")
            else:
                print(f"❌ {name} - FAILED (Status: {status})")
                print(f"   Error: {result}")
                test_result["error"] = result
                
        except Exception as e:
            print(f"❌ {name} - EXCEPTION: {str(e)}")
            test_result = {
                "name": name,
                "endpoint": endpoint,
                "method": method,
                "status_code": None,
                "success": False,
                "response": None,
                "error": str(e)
            }
        
        self.test_results.append(test_result)
        return test_result
    
    async def run_comprehensive_tests(self):
        """Run all Job Engine tests"""
        print("🚀 Starting Comprehensive Job Engine Test Suite")
        print("=" * 60)
        
        # Test 1: Health Check
        await self.test_endpoint(
            "Health Check",
            "GET",
            "/health"
        )
        
        # Test 2: Chat Interface (Main Entry Point)
        await self.test_endpoint(
            "Chat Interface - Job Creation",
            "POST",
            "/ai/chat",
            {
                "message": "restart nginx on web servers",
                "user_id": "test_user"
            }
        )
        
        # Test 3: Direct Job Creation
        await self.test_endpoint(
            "Direct Job Creation",
            "POST",
            "/ai/create-job",
            {
                "description": "update stationcontroller on CIS servers"
            }
        )
        
        # Test 4: Job Execution
        await self.test_endpoint(
            "Job Execution (Create + Execute)",
            "POST",
            "/ai/execute-job",
            {
                "description": "check status of Apache on production servers",
                "execute_immediately": True
            }
        )
        
        # Test 5: Text Analysis
        await self.test_endpoint(
            "Text Analysis",
            "POST",
            "/ai/analyze-text",
            {
                "text": "stop IIS service on all Windows servers"
            }
        )
        
        # Test 6: NLP Testing
        await self.test_endpoint(
            "NLP Testing",
            "GET",
            "/ai/test-nlp"
        )
        
        # Test 7: Workflow Testing
        await self.test_endpoint(
            "Workflow Testing",
            "GET",
            "/ai/test-workflow"
        )
        
        # Test 8: Asset Service Integration
        await self.test_endpoint(
            "Asset Service Integration",
            "GET",
            "/ai/test-assets"
        )
        
        # Test 9: Automation Service Integration
        await self.test_endpoint(
            "Automation Service Integration",
            "GET",
            "/ai/test-automation"
        )
        
        # Test 10: Full Integration Test
        await self.test_endpoint(
            "Full Integration Test",
            "GET",
            "/ai/test-integration"
        )
        
        # Test 11: Knowledge Stats
        await self.test_endpoint(
            "Knowledge Stats",
            "GET",
            "/ai/knowledge-stats"
        )
        
        # Test 12: Protocol Capabilities
        await self.test_endpoint(
            "Protocol Capabilities",
            "GET",
            "/ai/protocols/capabilities"
        )
        
        # Test 13: Predictive Analytics - Insights
        await self.test_endpoint(
            "Predictive Insights",
            "GET",
            "/ai/predictive/insights"
        )
        
        # Test 14: Predictive Analytics - Performance Analysis
        await self.test_endpoint(
            "Performance Analysis",
            "POST",
            "/ai/predictive/analyze-performance",
            {
                "cpu_usage": 75.5,
                "memory_usage": 82.3,
                "disk_usage": 45.2,
                "network_io": 1024.5
            }
        )
        
        # Test 15: Anomaly Detection
        await self.test_endpoint(
            "Anomaly Detection",
            "POST",
            "/ai/predictive/detect-anomalies",
            {
                "metrics": {
                    "cpu_usage": 95.0,
                    "memory_usage": 98.5,
                    "response_time": 5000
                },
                "execution_data": {
                    "job_count": 50,
                    "error_rate": 0.15
                }
            }
        )
        
        # Test 16: Maintenance Schedule
        await self.test_endpoint(
            "Maintenance Schedule",
            "GET",
            "/ai/predictive/maintenance-schedule"
        )
        
        # Test 17: Security Monitoring
        await self.test_endpoint(
            "Security Monitoring",
            "POST",
            "/ai/predictive/security-monitor",
            [
                {
                    "timestamp": "2024-01-15T10:30:00Z",
                    "level": "WARNING",
                    "message": "Multiple failed login attempts from IP 192.168.1.100",
                    "source": "auth_service"
                },
                {
                    "timestamp": "2024-01-15T10:31:00Z",
                    "level": "ERROR",
                    "message": "Unauthorized access attempt to /admin endpoint",
                    "source": "web_server"
                }
            ]
        )
        
        # Print comprehensive results
        await self.print_test_summary()
    
    async def print_test_summary(self):
        """Print comprehensive test results summary"""
        print("\n" + "=" * 60)
        print("📊 COMPREHENSIVE TEST RESULTS SUMMARY")
        print("=" * 60)
        
        total_tests = len(self.test_results)
        successful_tests = sum(1 for result in self.test_results if result["success"])
        failed_tests = total_tests - successful_tests
        
        print(f"Total Tests: {total_tests}")
        print(f"✅ Successful: {successful_tests}")
        print(f"❌ Failed: {failed_tests}")
        print(f"Success Rate: {(successful_tests/total_tests)*100:.1f}%")
        
        print("\n📋 DETAILED RESULTS:")
        print("-" * 60)
        
        for result in self.test_results:
            status_icon = "✅" if result["success"] else "❌"
            status_code = result["status_code"] if result["status_code"] else "N/A"
            print(f"{status_icon} {result['name']:<35} [{result['method']}] ({status_code})")
            
            if not result["success"] and result["error"]:
                print(f"    Error: {result['error']}")
        
        print("\n🔍 KEY FUNCTIONALITY STATUS:")
        print("-" * 60)
        
        # Check core Job Engine functionality
        job_creation_tests = [r for r in self.test_results if "Job Creation" in r["name"] or "create-job" in r["endpoint"]]
        job_execution_tests = [r for r in self.test_results if "Job Execution" in r["name"] or "execute-job" in r["endpoint"]]
        chat_tests = [r for r in self.test_results if "Chat" in r["name"]]
        nlp_tests = [r for r in self.test_results if "NLP" in r["name"] or "analyze-text" in r["endpoint"]]
        integration_tests = [r for r in self.test_results if "Integration" in r["name"]]
        predictive_tests = [r for r in self.test_results if "predictive" in r["endpoint"]]
        
        def check_functionality(tests, name):
            if not tests:
                return f"❓ {name}: No tests found"
            success_count = sum(1 for t in tests if t["success"])
            total_count = len(tests)
            if success_count == total_count:
                return f"✅ {name}: All tests passed ({success_count}/{total_count})"
            else:
                return f"⚠️  {name}: Partial success ({success_count}/{total_count})"
        
        print(check_functionality(job_creation_tests, "Job Creation"))
        print(check_functionality(job_execution_tests, "Job Execution"))
        print(check_functionality(chat_tests, "Chat Interface"))
        print(check_functionality(nlp_tests, "NLP Processing"))
        print(check_functionality(integration_tests, "Service Integration"))
        print(check_functionality(predictive_tests, "Predictive Analytics"))
        
        print("\n🎯 RECOMMENDATIONS:")
        print("-" * 60)
        
        if failed_tests == 0:
            print("🎉 All tests passed! The Job Engine is fully operational.")
            print("✨ Ready for production use and Phase 7 integration testing.")
        elif failed_tests <= 2:
            print("⚠️  Minor issues detected. Most functionality is working.")
            print("🔧 Review failed tests and address specific issues.")
        else:
            print("🚨 Multiple issues detected. Requires attention.")
            print("🔍 Focus on core Job Engine functionality first.")
        
        print("\n💡 NEXT STEPS:")
        print("-" * 60)
        print("1. Review any failed tests and their error messages")
        print("2. Test with real automation service integration")
        print("3. Validate job execution with actual infrastructure")
        print("4. Monitor logs for any runtime issues")
        print("5. Proceed with Phase 7 comprehensive integration testing")

async def main():
    """Main test execution"""
    print("🧠 AI Brain Job Engine - Comprehensive Test Suite")
    print("🔧 Testing all endpoints and functionality...")
    
    async with JobEngineTestSuite() as test_suite:
        await test_suite.run_comprehensive_tests()

if __name__ == "__main__":
    asyncio.run(main())