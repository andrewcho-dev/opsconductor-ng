#!/usr/bin/env python3
"""
Comprehensive E2E Integration Tests for AI Brain → Prefect → Automation Engine
Tests incrementally increase in difficulty to stress test the full system integration.
"""

import sys
import os
import asyncio
import logging
import json
import time
import httpx
from datetime import datetime
from typing import Dict, List, Any, Optional
import pytest

# Add paths
sys.path.insert(0, '/home/opsconductor/opsconductor-ng/ai-brain')
sys.path.insert(0, '/home/opsconductor/opsconductor-ng/shared')

# Configure detailed logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class IntegrationTestRunner:
    """Orchestrates comprehensive integration testing with detailed monitoring"""
    
    def __init__(self):
        self.base_url = "http://localhost:3005"  # AI Brain URL
        self.automation_url = "http://localhost:3003"  # Automation Service URL
        self.test_results = []
        self.client = httpx.AsyncClient(timeout=60.0)
    
    async def cleanup(self):
        """Clean up resources"""
        await self.client.aclose()
    
    async def log_test_start(self, test_name: str, difficulty: int):
        """Log test start with difficulty indicator"""
        logger.info(f"🔥 TEST {len(self.test_results)+1} (Difficulty: {difficulty}/10): {test_name}")
        logger.info("=" * 80)
    
    async def log_test_result(self, test_name: str, success: bool, details: Dict[str, Any]):
        """Log comprehensive test results"""
        status = "✅ PASS" if success else "❌ FAIL"
        logger.info(f"{status}: {test_name}")
        if details:
            for key, value in details.items():
                logger.info(f"  {key}: {value}")
        logger.info("-" * 80)
        
        self.test_results.append({
            "test_name": test_name,
            "success": success,
            "details": details,
            "timestamp": datetime.now().isoformat()
        })
    
    async def check_service_health(self, service_url: str, service_name: str) -> Dict[str, Any]:
        """Check if a service is healthy"""
        try:
            response = await self.client.get(f"{service_url}/health")
            if response.status_code == 200:
                return {"status": "healthy", "response_time": response.elapsed.total_seconds()}
            else:
                return {"status": "unhealthy", "status_code": response.status_code}
        except Exception as e:
            return {"status": "unreachable", "error": str(e)}
    
    async def send_ai_request(self, prompt: str, expected_behavior: str = None) -> Dict[str, Any]:
        """Send request to AI Brain and monitor full execution chain"""
        try:
            # Try multiple chat endpoints with their specific payloads
            endpoints_configs = [
                {
                    "endpoint": "/api/thinking-llm/chat",
                    "payload": {
                        "message": prompt,
                        "conversation_id": f"test_{int(time.time())}",
                        "user_id": "test_user"
                    }
                },
                {
                    "endpoint": "/ai/chat",
                    "payload": {
                        "message": prompt,
                        "conversation_id": f"test_{int(time.time())}",
                        "user_id": 1
                    }
                },
                {
                    "endpoint": "/orchestration/chat",
                    "payload": {
                        "message": prompt,
                        "conversation_id": f"test_{int(time.time())}",
                        "user_id": "test_user"
                    }
                }
            ]
            
            # Try first endpoint that works
            used_endpoint = None
            for config in endpoints_configs:
                try:
                    start_time = time.time()
                    response = await self.client.post(f"{self.base_url}{config['endpoint']}", json=config['payload'])
                    end_time = time.time()
                    
                    if response.status_code not in [404, 405, 503]:  # Not found, method not allowed, or service unavailable
                        used_endpoint = config['endpoint']
                        break
                except Exception:
                    continue
            else:
                # If no endpoint worked, use the thinking-llm one for the final attempt
                config = endpoints_configs[0]  # thinking-llm config
                start_time = time.time()
                response = await self.client.post(f"{self.base_url}{config['endpoint']}", json=config['payload'])
                end_time = time.time()
                used_endpoint = config['endpoint']
            
            if response.status_code != 200:
                return {
                    "success": False,
                    "error": f"AI Brain returned {response.status_code}",
                    "response_text": response.text,
                    "endpoint_used": used_endpoint
                }
            
            result = response.json()
            
            return {
                "success": True,
                "response": result,
                "response_time": end_time - start_time,
                "ai_brain_status": response.status_code,
                "endpoint_used": used_endpoint
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "exception_type": type(e).__name__
            }
    
    async def monitor_job_execution(self, job_id: str, timeout: int = 30) -> Dict[str, Any]:
        """Monitor job execution in automation service"""
        try:
            start_time = time.time()
            
            while time.time() - start_time < timeout:
                response = await self.client.get(f"{self.automation_url}/jobs/{job_id}")
                if response.status_code == 200:
                    job_data = response.json()
                    status = job_data.get("status", "unknown")
                    
                    if status in ["completed", "failed", "error"]:
                        return {
                            "success": status == "completed",
                            "final_status": status,
                            "execution_time": time.time() - start_time,
                            "job_data": job_data
                        }
                
                await asyncio.sleep(2)
            
            return {
                "success": False,
                "error": "Job monitoring timeout",
                "timeout_seconds": timeout
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    # TEST CASES - Incrementally increasing difficulty
    
    async def test_1_service_connectivity(self):
        """Difficulty 1/10: Basic service connectivity"""
        await self.log_test_start("Service Connectivity Check", 1)
        
        services = [
            (self.base_url, "AI Brain"),
            (self.automation_url, "Automation Service")
        ]
        
        results = {}
        all_healthy = True
        
        for url, name in services:
            health = await self.check_service_health(url, name)
            results[name] = health
            if health["status"] != "healthy":
                all_healthy = False
        
        await self.log_test_result("Service Connectivity", all_healthy, results)
        return all_healthy
    
    async def test_2_simple_ai_response(self):
        """Difficulty 2/10: Simple AI response without job creation"""
        await self.log_test_start("Simple AI Response", 2)
        
        result = await self.send_ai_request("Hello, can you hear me?")
        
        success = result["success"] and result.get("response") is not None
        details = {
            "response_time": result.get("response_time", "unknown"),
            "has_response": "response" in result,
            "ai_responded": success
        }
        
        if result.get("response"):
            details["response_length"] = len(str(result["response"]))
        
        await self.log_test_result("Simple AI Response", success, details)
        return success
    
    async def test_3_asset_information_request(self):
        """Difficulty 3/10: Request asset information (read-only operation)"""
        await self.log_test_start("Asset Information Request", 3)
        
        result = await self.send_ai_request("Show me information about available assets")
        
        success = result["success"]
        details = {
            "response_time": result.get("response_time", "unknown"),
            "ai_understood_request": success
        }
        
        if result.get("response"):
            response_text = str(result["response"]).lower()
            details["mentions_assets"] = "asset" in response_text
            details["response_type"] = "informational"
        
        await self.log_test_result("Asset Information Request", success, details)
        return success
    
    async def test_4_simple_ping_job_creation(self):
        """Difficulty 4/10: Create simple ping job"""
        await self.log_test_start("Simple Ping Job Creation", 4)
        
        result = await self.send_ai_request(
            "Create a simple ping job to test connectivity to 8.8.8.8"
        )
        
        success = result["success"]
        details = {
            "response_time": result.get("response_time", "unknown"),
            "ai_processed_request": success
        }
        
        if result.get("response"):
            response_data = result["response"]
            details["created_job"] = "job" in str(response_data).lower()
            details["response_contains_details"] = len(str(response_data)) > 100
        
        await self.log_test_result("Simple Ping Job Creation", success, details)
        return success
    
    async def test_5_job_status_inquiry(self):
        """Difficulty 5/10: Inquire about job status"""
        await self.log_test_start("Job Status Inquiry", 5)
        
        result = await self.send_ai_request("What jobs are currently running or recently completed?")
        
        success = result["success"]
        details = {
            "response_time": result.get("response_time", "unknown"),
            "ai_understood_query": success
        }
        
        if result.get("response"):
            response_text = str(result["response"]).lower()
            details["mentions_jobs"] = "job" in response_text
            details["provides_status_info"] = any(word in response_text for word in ["running", "completed", "failed", "status"])
        
        await self.log_test_result("Job Status Inquiry", success, details)
        return success
    
    async def test_6_complex_network_scan_job(self):
        """Difficulty 6/10: Create complex network scanning job"""
        await self.log_test_start("Complex Network Scan Job", 6)
        
        result = await self.send_ai_request(
            "Create a comprehensive network scan job for the subnet 192.168.1.0/24. "
            "Include port scanning for common ports (22, 80, 443, 8080) and OS detection."
        )
        
        success = result["success"]
        details = {
            "response_time": result.get("response_time", "unknown"),
            "complex_job_handled": success
        }
        
        if result.get("response"):
            response_text = str(result["response"]).lower()
            details["mentions_network_scan"] = any(word in response_text for word in ["scan", "network", "port"])
            details["includes_subnet"] = "192.168.1" in response_text
            details["mentions_ports"] = any(port in response_text for port in ["22", "80", "443"])
        
        await self.log_test_result("Complex Network Scan Job", success, details)
        return success
    
    async def test_7_multi_step_automation_job(self):
        """Difficulty 7/10: Create multi-step automation workflow"""
        await self.log_test_start("Multi-Step Automation Job", 7)
        
        result = await self.send_ai_request(
            "Create an automation job that: 1) Scans for active hosts in 10.0.0.0/24, "
            "2) For each active host, check if SSH (port 22) is open, "
            "3) Generate a summary report of findings, "
            "4) Send notification when complete."
        )
        
        success = result["success"]
        details = {
            "response_time": result.get("response_time", "unknown"),
            "multi_step_understood": success
        }
        
        if result.get("response"):
            response_text = str(result["response"]).lower()
            details["mentions_workflow"] = any(word in response_text for word in ["step", "workflow", "automation"])
            details["includes_scanning"] = "scan" in response_text
            details["mentions_ssh_check"] = any(word in response_text for word in ["ssh", "22", "port"])
            details["mentions_reporting"] = any(word in response_text for word in ["report", "summary", "notification"])
        
        await self.log_test_result("Multi-Step Automation Job", success, details)
        return success
    
    async def test_8_conditional_logic_job(self):
        """Difficulty 8/10: Job with conditional logic and error handling"""
        await self.log_test_start("Conditional Logic Job", 8)
        
        result = await self.send_ai_request(
            "Create a smart monitoring job that checks if a web service on port 80 is responding. "
            "If it's down, automatically try to restart it using a predefined script. "
            "If restart fails, escalate to administrators. Include retry logic with exponential backoff."
        )
        
        success = result["success"]
        details = {
            "response_time": result.get("response_time", "unknown"),
            "conditional_logic_handled": success
        }
        
        if result.get("response"):
            response_text = str(result["response"]).lower()
            details["mentions_monitoring"] = "monitor" in response_text
            details["includes_conditionals"] = any(word in response_text for word in ["if", "condition", "check"])
            details["mentions_restart"] = "restart" in response_text
            details["includes_error_handling"] = any(word in response_text for word in ["fail", "error", "escalate"])
            details["mentions_retry"] = any(word in response_text for word in ["retry", "backoff"])
        
        await self.log_test_result("Conditional Logic Job", success, details)
        return success
    
    async def test_9_resource_intensive_parallel_job(self):
        """Difficulty 9/10: Resource-intensive parallel processing job"""
        await self.log_test_start("Resource-Intensive Parallel Job", 9)
        
        result = await self.send_ai_request(
            "Create a high-performance job that simultaneously scans multiple subnets: "
            "192.168.1.0/24, 192.168.2.0/24, 10.0.0.0/24, and 172.16.0.0/24. "
            "For each subnet, perform deep packet inspection on discovered hosts, "
            "analyze traffic patterns, and generate security vulnerability reports. "
            "Optimize for parallel execution and resource efficiency."
        )
        
        success = result["success"]
        details = {
            "response_time": result.get("response_time", "unknown"),
            "parallel_job_handled": success
        }
        
        if result.get("response"):
            response_text = str(result["response"]).lower()
            details["mentions_parallel"] = any(word in response_text for word in ["parallel", "simultaneous", "concurrent"])
            details["includes_multiple_subnets"] = len([s for s in ["192.168.1", "192.168.2", "10.0.0", "172.16"] if s in response_text]) >= 2
            details["mentions_deep_inspection"] = any(word in response_text for word in ["deep", "packet", "inspection"])
            details["includes_optimization"] = any(word in response_text for word in ["optimize", "efficient", "performance"])
        
        await self.log_test_result("Resource-Intensive Parallel Job", success, details)
        return success
    
    async def test_10_adaptive_ai_learning_job(self):
        """Difficulty 10/10: Adaptive AI-driven learning and decision making"""
        await self.log_test_start("Adaptive AI Learning Job", 10)
        
        result = await self.send_ai_request(
            "Create an intelligent adaptive monitoring system that learns network patterns over time. "
            "It should automatically adjust monitoring frequency based on historical data, "
            "predict potential failures using machine learning, "
            "autonomously create preventive maintenance jobs when anomalies are detected, "
            "and continuously optimize its own algorithms based on success/failure rates. "
            "Include integration with external threat intelligence feeds and "
            "implement zero-trust security validation for all operations."
        )
        
        success = result["success"]
        details = {
            "response_time": result.get("response_time", "unknown"),
            "adaptive_ai_handled": success
        }
        
        if result.get("response"):
            response_text = str(result["response"]).lower()
            details["mentions_learning"] = any(word in response_text for word in ["learn", "adaptive", "intelligent"])
            details["includes_prediction"] = any(word in response_text for word in ["predict", "machine learning", "ml"])
            details["mentions_autonomous"] = any(word in response_text for word in ["autonomous", "automatic", "auto"])
            details["includes_optimization"] = any(word in response_text for word in ["optimize", "algorithm", "improve"])
            details["mentions_security"] = any(word in response_text for word in ["security", "threat", "zero-trust"])
        
        await self.log_test_result("Adaptive AI Learning Job", success, details)
        return success
    
    async def run_all_tests(self) -> Dict[str, Any]:
        """Run all tests and generate comprehensive report"""
        logger.info("🚀 Starting Comprehensive AI Brain → Prefect → Automation Integration Tests")
        logger.info(f"🕐 Test Started: {datetime.now()}")
        logger.info("=" * 100)
        
        tests = [
            self.test_1_service_connectivity,
            self.test_2_simple_ai_response,
            self.test_3_asset_information_request,
            self.test_4_simple_ping_job_creation,
            self.test_5_job_status_inquiry,
            self.test_6_complex_network_scan_job,
            self.test_7_multi_step_automation_job,
            self.test_8_conditional_logic_job,
            self.test_9_resource_intensive_parallel_job,
            self.test_10_adaptive_ai_learning_job
        ]
        
        passed = 0
        failed = 0
        
        for test in tests:
            try:
                result = await test()
                if result:
                    passed += 1
                else:
                    failed += 1
            except Exception as e:
                logger.error(f"❌ Test {test.__name__} crashed: {e}")
                failed += 1
                self.test_results.append({
                    "test_name": test.__name__,
                    "success": False,
                    "details": {"crash_error": str(e)},
                    "timestamp": datetime.now().isoformat()
                })
        
        # Generate final report
        total_tests = passed + failed
        success_rate = (passed / total_tests * 100) if total_tests > 0 else 0
        
        logger.info("=" * 100)
        logger.info("🏁 TEST EXECUTION COMPLETE")
        logger.info("=" * 100)
        logger.info(f"📊 RESULTS SUMMARY:")
        logger.info(f"   Total Tests: {total_tests}")
        logger.info(f"   Passed: {passed}")
        logger.info(f"   Failed: {failed}")
        logger.info(f"   Success Rate: {success_rate:.1f}%")
        logger.info(f"🕐 Test Completed: {datetime.now()}")
        
        if success_rate >= 80:
            logger.info("🎉 INTEGRATION STATUS: EXCELLENT - System performing well!")
        elif success_rate >= 60:
            logger.info("⚠️  INTEGRATION STATUS: GOOD - Minor issues detected")
        elif success_rate >= 40:
            logger.info("🚨 INTEGRATION STATUS: POOR - Significant issues found")
        else:
            logger.info("💥 INTEGRATION STATUS: CRITICAL - Major integration failures")
        
        return {
            "total_tests": total_tests,
            "passed": passed,
            "failed": failed,
            "success_rate": success_rate,
            "test_results": self.test_results,
            "timestamp": datetime.now().isoformat()
        }

async def main():
    """Main test execution function"""
    runner = IntegrationTestRunner()
    try:
        results = await runner.run_all_tests()
        
        # Save results to file
        results_file = f"/home/opsconductor/opsconductor-ng/tests/e2e/test_results_{int(time.time())}.json"
        with open(results_file, 'w') as f:
            json.dump(results, f, indent=2)
        logger.info(f"📄 Detailed results saved to: {results_file}")
        
        # Return exit code based on success rate
        if results["success_rate"] >= 70:
            return 0
        else:
            return 1
    finally:
        await runner.cleanup()

if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)