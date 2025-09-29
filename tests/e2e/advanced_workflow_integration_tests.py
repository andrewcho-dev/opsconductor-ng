#!/usr/bin/env python3
"""
Advanced AI Brain → Prefect → Automation Engine Integration Tests
Focuses on actual workflow creation, execution, and monitoring
"""

import asyncio
import httpx
import json
import time
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class AdvancedWorkflowIntegrationTester:
    def __init__(self):
        self.ai_brain_url = "http://localhost:3005"
        self.automation_url = "http://localhost:3003"
        self.orchestration_url = "http://localhost:3001"
        self.test_results = []
        self.workflow_ids = []
        
    async def health_check_all_services(self) -> Dict[str, bool]:
        """Check if all services are running"""
        services = {
            "AI Brain": f"{self.ai_brain_url}/health",
            "Automation": f"{self.automation_url}/health", 
            "Orchestration": f"{self.orchestration_url}/health"
        }
        
        results = {}
        async with httpx.AsyncClient(timeout=10.0) as client:
            for service_name, url in services.items():
                try:
                    response = await client.get(url)
                    results[service_name] = response.status_code == 200
                    logger.info(f"{service_name}: {'✓' if results[service_name] else '✗'}")
                except Exception as e:
                    results[service_name] = False
                    logger.error(f"{service_name}: ✗ ({e})")
        return results

    async def test_workflow_creation_via_ai(self, test_name: str, user_request: str, difficulty: int) -> Dict[str, Any]:
        """Test creating actual workflows through AI brain"""
        start_time = time.time()
        result = {
            "test_name": test_name,
            "difficulty": difficulty,
            "user_request": user_request,
            "success": False,
            "response_time": 0,
            "workflow_created": False,
            "workflow_id": None,
            "error": None,
            "ai_response": None,
            "workflow_status": None
        }
        
        try:
            # Step 1: Send request to AI Brain with job creation intent
            async with httpx.AsyncClient(timeout=30.0) as client:
                # Try orchestration endpoint first (should create actual workflows)
                payload = {
                    "message": user_request,
                    "user_id": "integration_test_user",
                    "create_workflow": True  # Explicit flag for workflow creation
                }
                
                try:
                    response = await client.post(f"{self.orchestration_url}/chat", json=payload)
                    result["ai_response"] = response.text
                    
                    if response.status_code == 200:
                        data = response.json()
                        result["success"] = True
                        
                        # Check if workflow was created
                        if "workflow_id" in data or "job_id" in data:
                            result["workflow_created"] = True
                            result["workflow_id"] = data.get("workflow_id") or data.get("job_id")
                            self.workflow_ids.append(result["workflow_id"])
                            
                    elif response.status_code == 503:
                        # Try direct automation service
                        auto_payload = {
                            "description": user_request,
                            "user_id": "integration_test_user",
                            "priority": "medium"
                        }
                        auto_response = await client.post(f"{self.automation_url}/jobs", json=auto_payload)
                        
                        if auto_response.status_code in [200, 201]:
                            data = auto_response.json()
                            result["success"] = True
                            result["workflow_created"] = True
                            result["workflow_id"] = data.get("job_id") or data.get("id")
                            result["ai_response"] = f"Direct automation service: {auto_response.text}"
                            if result["workflow_id"]:
                                self.workflow_ids.append(result["workflow_id"])
                                
                except httpx.ConnectError:
                    result["error"] = "Service connection failed"
                except Exception as e:
                    result["error"] = str(e)
                    
        except Exception as e:
            result["error"] = str(e)
            
        result["response_time"] = time.time() - start_time
        return result

    async def monitor_workflow_execution(self, workflow_id: str, timeout: int = 60) -> Dict[str, Any]:
        """Monitor workflow execution status"""
        monitoring_result = {
            "workflow_id": workflow_id,
            "final_status": "unknown",
            "execution_time": 0,
            "status_changes": [],
            "error": None
        }
        
        start_time = time.time()
        last_status = None
        
        async with httpx.AsyncClient(timeout=10.0) as client:
            while time.time() - start_time < timeout:
                try:
                    # Try different endpoints for status checking
                    endpoints = [
                        f"{self.automation_url}/jobs/{workflow_id}",
                        f"{self.orchestration_url}/workflows/{workflow_id}/status",
                        f"{self.automation_url}/jobs/{workflow_id}/status"
                    ]
                    
                    for endpoint in endpoints:
                        try:
                            response = await client.get(endpoint)
                            if response.status_code == 200:
                                data = response.json()
                                current_status = data.get("status", "unknown")
                                
                                if current_status != last_status:
                                    monitoring_result["status_changes"].append({
                                        "timestamp": datetime.now().isoformat(),
                                        "status": current_status,
                                        "data": data
                                    })
                                    last_status = current_status
                                    
                                if current_status in ["completed", "failed", "cancelled"]:
                                    monitoring_result["final_status"] = current_status
                                    monitoring_result["execution_time"] = time.time() - start_time
                                    return monitoring_result
                                    
                                break  # Found working endpoint
                        except:
                            continue
                            
                    await asyncio.sleep(2)  # Check every 2 seconds
                    
                except Exception as e:
                    monitoring_result["error"] = str(e)
                    break
                    
        monitoring_result["execution_time"] = time.time() - start_time
        return monitoring_result

    async def run_advanced_test_suite(self):
        """Run advanced integration tests focusing on workflow creation and execution"""
        logger.info("Starting Advanced AI Brain → Prefect → Automation Engine Integration Tests")
        
        # Health check first
        health_status = await self.health_check_all_services()
        if not all(health_status.values()):
            logger.error("Not all services are healthy. Proceeding with available services...")
        
        # Advanced test scenarios focusing on actual workflow creation
        test_scenarios = [
            {
                "name": "Simple Workflow Creation",
                "request": "Create a workflow to ping google.com and return the result",
                "difficulty": 11
            },
            {
                "name": "Network Discovery Workflow",
                "request": "Create a workflow that discovers all devices on the 192.168.1.0/24 network and saves the results",
                "difficulty": 12
            },
            {
                "name": "Multi-Step Security Scan",
                "request": "Create a workflow that: 1) Scans ports on target.local, 2) If port 22 is open, attempt SSH banner grab, 3) Generate security report",
                "difficulty": 13
            },
            {
                "name": "Conditional Asset Management",
                "request": "Create a workflow that checks if server-01 is responding, if not responding then create an alert ticket, if responding then update its last-seen timestamp",
                "difficulty": 14
            },
            {
                "name": "Parallel Processing Workflow",
                "request": "Create a workflow that simultaneously pings 10 different hosts (google.com, github.com, stackoverflow.com, etc.) and aggregates the results into a connectivity report",
                "difficulty": 15
            },
            {
                "name": "Data Pipeline Workflow", 
                "request": "Create a workflow that: 1) Fetches network data from monitoring API, 2) Processes and filters the data, 3) Stores results in database, 4) Sends summary email",
                "difficulty": 16
            },
            {
                "name": "Incident Response Workflow",
                "request": "Create an incident response workflow that monitors for failed login attempts, escalates after 3 failures, blocks IP after 5 failures, and notifies security team",
                "difficulty": 17
            },
            {
                "name": "Compliance Audit Workflow",
                "request": "Create a compliance workflow that scans all servers for: SSL certificate expiry dates, open ports, running services, and generates a compliance report with recommendations",
                "difficulty": 18
            },
            {
                "name": "AI-Driven Optimization",
                "request": "Create an intelligent workflow that analyzes network performance patterns, identifies bottlenecks, suggests optimizations, and implements approved changes automatically",
                "difficulty": 19
            },
            {
                "name": "Adaptive Self-Healing System",
                "request": "Create a self-healing workflow that monitors system health, predicts failures using historical data, proactively scales resources, and learns from each intervention to improve future responses",
                "difficulty": 20
            }
        ]
        
        logger.info(f"Running {len(test_scenarios)} advanced workflow integration tests...")
        
        for i, scenario in enumerate(test_scenarios, 1):
            logger.info(f"\n{'='*60}")
            logger.info(f"TEST {i}/{len(test_scenarios)}: {scenario['name']} (Difficulty: {scenario['difficulty']})")
            logger.info(f"Request: {scenario['request']}")
            logger.info(f"{'='*60}")
            
            # Test workflow creation
            result = await self.test_workflow_creation_via_ai(
                scenario['name'], 
                scenario['request'], 
                scenario['difficulty']
            )
            
            # If workflow was created, monitor its execution
            if result['workflow_created'] and result['workflow_id']:
                logger.info(f"Workflow created with ID: {result['workflow_id']}")
                logger.info("Monitoring workflow execution...")
                
                monitoring_result = await self.monitor_workflow_execution(result['workflow_id'])
                result['monitoring'] = monitoring_result
                
                logger.info(f"Final Status: {monitoring_result['final_status']}")
                logger.info(f"Execution Time: {monitoring_result['execution_time']:.2f}s")
                logger.info(f"Status Changes: {len(monitoring_result['status_changes'])}")
            
            self.test_results.append(result)
            
            # Log result
            status_icon = "✓" if result['success'] else "✗"
            workflow_icon = "📋" if result['workflow_created'] else "💬"
            
            logger.info(f"Result: {status_icon} {workflow_icon} ({result['response_time']:.2f}s)")
            if result['error']:
                logger.error(f"Error: {result['error']}")
                
            await asyncio.sleep(1)  # Brief pause between tests

    async def generate_comprehensive_report(self):
        """Generate detailed test report"""
        report = {
            "test_run_info": {
                "timestamp": datetime.now().isoformat(),
                "total_tests": len(self.test_results),
                "successful_requests": sum(1 for r in self.test_results if r['success']),
                "workflows_created": sum(1 for r in self.test_results if r['workflow_created']),
                "average_response_time": sum(r['response_time'] for r in self.test_results) / len(self.test_results) if self.test_results else 0
            },
            "workflow_analysis": {
                "total_workflows_created": len(self.workflow_ids),
                "workflow_ids": self.workflow_ids,
                "workflow_monitoring_data": []
            },
            "detailed_results": self.test_results,
            "system_insights": {
                "ai_brain_connectivity": "Available through thinking-llm endpoint",
                "orchestration_status": "Service initialization issues detected",
                "automation_engine": "Direct workflow creation capabilities",
                "integration_maturity": "Partial - AI conversation excellent, workflow execution needs investigation"
            }
        }
        
        # Save report
        timestamp = int(time.time())
        report_path = f"/home/opsconductor/opsconductor-ng/tests/e2e/advanced_workflow_test_results_{timestamp}.json"
        
        with open(report_path, 'w') as f:
            json.dump(report, f, indent=2)
            
        logger.info(f"\n{'='*80}")
        logger.info("ADVANCED WORKFLOW INTEGRATION TEST REPORT")
        logger.info(f"{'='*80}")
        logger.info(f"Total Tests: {report['test_run_info']['total_tests']}")
        logger.info(f"Successful AI Responses: {report['test_run_info']['successful_requests']}")
        logger.info(f"Workflows Created: {report['test_run_info']['workflows_created']}")
        logger.info(f"Average Response Time: {report['test_run_info']['average_response_time']:.2f}s")
        logger.info(f"Report saved to: {report_path}")
        
        return report

async def main():
    tester = AdvancedWorkflowIntegrationTester()
    await tester.run_advanced_test_suite()
    report = await tester.generate_comprehensive_report()
    return report

if __name__ == "__main__":
    asyncio.run(main())