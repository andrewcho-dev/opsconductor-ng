#!/usr/bin/env python3
"""
Direct Automation Engine Integration Tests
Tests workflow creation, execution, and monitoring through the automation service
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

class DirectAutomationTester:
    def __init__(self):
        self.automation_url = "http://localhost:3003"
        self.test_results = []
        self.job_ids = []
        
    async def create_job(self, name: str, description: str, job_type: str = "manual", priority: str = "medium") -> Dict[str, Any]:
        """Create a job directly in the automation engine"""
        payload = {
            "name": name,
            "description": description,
            "job_type": job_type,
            "is_enabled": True,
            "metadata": {
                "created_by": "integration_test",
                "test_category": "workflow_creation",
                "priority": priority
            }
        }
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            try:
                response = await client.post(f"{self.automation_url}/jobs", json=payload)
                if response.status_code in [200, 201]:
                    data = response.json()
                    job_id = data.get("job_id") or data.get("id")
                    if job_id:
                        self.job_ids.append(job_id)
                    return {
                        "success": True,
                        "job_id": job_id,
                        "response": data,
                        "status_code": response.status_code
                    }
                else:
                    return {
                        "success": False,
                        "error": f"HTTP {response.status_code}: {response.text}",
                        "status_code": response.status_code
                    }
            except Exception as e:
                return {
                    "success": False,
                    "error": str(e)
                }
    
    async def execute_job(self, job_id: str) -> Dict[str, Any]:
        """Execute a job and monitor its progress"""
        async with httpx.AsyncClient(timeout=30.0) as client:
            try:
                # Trigger job execution
                response = await client.post(f"{self.automation_url}/jobs/{job_id}/run")
                
                if response.status_code in [200, 201, 202]:
                    data = response.json()
                    return {
                        "success": True,
                        "execution_response": data,
                        "status_code": response.status_code
                    }
                else:
                    return {
                        "success": False,
                        "error": f"HTTP {response.status_code}: {response.text}",
                        "status_code": response.status_code
                    }
            except Exception as e:
                return {
                    "success": False,
                    "error": str(e)
                }
    
    async def get_job_status(self, job_id: str) -> Dict[str, Any]:
        """Get current job status and details"""
        async with httpx.AsyncClient(timeout=10.0) as client:
            try:
                response = await client.get(f"{self.automation_url}/jobs/{job_id}")
                if response.status_code == 200:
                    return {
                        "success": True,
                        "job_details": response.json()
                    }
                else:
                    return {
                        "success": False,
                        "error": f"HTTP {response.status_code}: {response.text}"
                    }
            except Exception as e:
                return {
                    "success": False,
                    "error": str(e)
                }
    
    async def get_execution_status(self, job_id: str) -> Dict[str, Any]:
        """Get job execution status"""
        async with httpx.AsyncClient(timeout=10.0) as client:
            try:
                response = await client.get(f"{self.automation_url}/jobs/{job_id}/execution-status")
                if response.status_code == 200:
                    return {
                        "success": True,
                        "execution_status": response.json()
                    }
                else:
                    return {
                        "success": False,
                        "error": f"HTTP {response.status_code}: {response.text}"
                    }
            except Exception as e:
                return {
                    "success": False,
                    "error": str(e)
                }
    
    async def test_full_workflow_cycle(self, test_name: str, description: str, difficulty: int) -> Dict[str, Any]:
        """Test complete workflow: creation → execution → monitoring"""
        start_time = time.time()
        result = {
            "test_name": test_name,
            "description": description,
            "difficulty": difficulty,
            "job_created": False,
            "job_executed": False,
            "job_id": None,
            "creation_time": 0,
            "execution_time": 0,
            "total_time": 0,
            "final_status": "unknown",
            "errors": [],
            "steps": []
        }
        
        # Step 1: Create Job
        create_start = time.time()
        job_name = f"{test_name.replace(' ', '_').lower()}_{int(time.time())}"
        creation_result = await self.create_job(job_name, description)
        result["creation_time"] = time.time() - create_start
        
        if creation_result["success"]:
            result["job_created"] = True
            result["job_id"] = creation_result["job_id"]
            result["steps"].append({
                "step": "job_creation",
                "success": True,
                "time": result["creation_time"],
                "response": creation_result["response"]
            })
            logger.info(f"✓ Job created: {result['job_id']}")
            
            # Step 2: Execute Job
            exec_start = time.time()
            execution_result = await self.execute_job(result["job_id"])
            result["execution_time"] = time.time() - exec_start
            
            if execution_result["success"]:
                result["job_executed"] = True
                result["steps"].append({
                    "step": "job_execution",
                    "success": True,
                    "time": result["execution_time"],
                    "response": execution_result["execution_response"]
                })
                logger.info(f"✓ Job executed: {result['job_id']}")
                
                # Step 3: Monitor execution for up to 60 seconds
                monitor_start = time.time()
                monitoring_timeout = 60
                last_status = None
                status_changes = []
                
                while time.time() - monitor_start < monitoring_timeout:
                    status_result = await self.get_execution_status(result["job_id"])
                    if status_result["success"]:
                        current_status = status_result["execution_status"].get("status", "unknown")
                        
                        if current_status != last_status:
                            status_changes.append({
                                "timestamp": datetime.now().isoformat(),
                                "status": current_status,
                                "details": status_result["execution_status"]
                            })
                            last_status = current_status
                            logger.info(f"Status: {current_status}")
                            
                        if current_status in ["completed", "failed", "cancelled", "success", "error"]:
                            result["final_status"] = current_status
                            break
                    
                    await asyncio.sleep(3)  # Check every 3 seconds
                
                result["steps"].append({
                    "step": "monitoring",
                    "success": True,
                    "status_changes": status_changes,
                    "final_status": result["final_status"]
                })
                
            else:
                result["errors"].append(f"Job execution failed: {execution_result['error']}")
                result["steps"].append({
                    "step": "job_execution",
                    "success": False,
                    "error": execution_result["error"]
                })
        else:
            result["errors"].append(f"Job creation failed: {creation_result['error']}")
            result["steps"].append({
                "step": "job_creation",
                "success": False,
                "error": creation_result["error"]
            })
            
        result["total_time"] = time.time() - start_time
        return result
    
    async def run_intensive_automation_tests(self):
        """Run intensive automation engine tests with increasing difficulty"""
        logger.info("Starting Intensive Direct Automation Engine Tests")
        
        # Check automation service health
        async with httpx.AsyncClient(timeout=10.0) as client:
            try:
                response = await client.get(f"{self.automation_url}/health")
                if response.status_code == 200:
                    logger.info("✓ Automation service is healthy")
                else:
                    logger.error(f"✗ Automation service health check failed: {response.status_code}")
                    return
            except Exception as e:
                logger.error(f"✗ Cannot connect to automation service: {e}")
                return
        
        # Define intensive test scenarios
        test_scenarios = [
            {
                "name": "Basic Ping Test",
                "description": "Execute a simple ping to google.com",
                "difficulty": 11
            },
            {
                "name": "Multi-Target Ping",
                "description": "Ping multiple hosts: google.com, github.com, stackoverflow.com",
                "difficulty": 12
            },
            {
                "name": "Network Port Scan",
                "description": "Perform a port scan on localhost ports 22, 80, 443, 3000-3010",
                "difficulty": 13
            },
            {
                "name": "Service Discovery",
                "description": "Discover all running services on localhost and identify their versions",
                "difficulty": 14
            },
            {
                "name": "System Health Check",
                "description": "Check system resources: CPU usage, memory usage, disk space, network interfaces",
                "difficulty": 15
            },
            {
                "name": "Log Analysis Workflow",
                "description": "Analyze system logs for errors in the last hour, categorize by severity, generate summary report",
                "difficulty": 16
            },
            {
                "name": "Security Audit Scan",
                "description": "Perform security audit: check for open ports, analyze running processes, check file permissions on sensitive directories",
                "difficulty": 17
            },
            {
                "name": "Performance Benchmarking",
                "description": "Run comprehensive performance tests: CPU benchmarks, memory tests, disk I/O tests, network throughput tests",
                "difficulty": 18
            },
            {
                "name": "Automated Backup Verification",
                "description": "Create test files, backup them, verify backup integrity, restore files, compare checksums, cleanup",
                "difficulty": 19
            },
            {
                "name": "Full System Integration Test",
                "description": "Execute comprehensive system test: database connectivity, API endpoints, service dependencies, failover scenarios, performance under load",
                "difficulty": 20
            }
        ]
        
        logger.info(f"Running {len(test_scenarios)} intensive automation tests...")
        
        for i, scenario in enumerate(test_scenarios, 1):
            logger.info(f"\n{'='*80}")
            logger.info(f"TEST {i}/{len(test_scenarios)}: {scenario['name']} (Difficulty: {scenario['difficulty']})")
            logger.info(f"Description: {scenario['description']}")
            logger.info(f"{'='*80}")
            
            result = await self.test_full_workflow_cycle(
                scenario['name'],
                scenario['description'],
                scenario['difficulty']
            )
            
            self.test_results.append(result)
            
            # Log detailed results
            success_icon = "✓" if result["job_created"] and result["job_executed"] else "✗"
            exec_icon = "🚀" if result["job_executed"] else "💤"
            status_icon = "🎯" if result["final_status"] in ["completed", "success"] else "⚠️"
            
            logger.info(f"Result: {success_icon} {exec_icon} {status_icon}")
            logger.info(f"Job ID: {result['job_id']}")
            logger.info(f"Creation: {result['creation_time']:.2f}s")
            logger.info(f"Execution: {result['execution_time']:.2f}s") 
            logger.info(f"Total: {result['total_time']:.2f}s")
            logger.info(f"Final Status: {result['final_status']}")
            
            if result["errors"]:
                logger.error(f"Errors: {result['errors']}")
                
            await asyncio.sleep(2)  # Brief pause between tests
    
    async def generate_intensive_report(self):
        """Generate comprehensive test report"""
        successful_creations = sum(1 for r in self.test_results if r['job_created'])
        successful_executions = sum(1 for r in self.test_results if r['job_executed'])
        completed_jobs = sum(1 for r in self.test_results if r['final_status'] in ['completed', 'success'])
        
        report = {
            "test_run_info": {
                "timestamp": datetime.now().isoformat(),
                "total_tests": len(self.test_results),
                "successful_creations": successful_creations,
                "successful_executions": successful_executions,
                "completed_jobs": completed_jobs,
                "average_creation_time": sum(r['creation_time'] for r in self.test_results) / len(self.test_results) if self.test_results else 0,
                "average_execution_time": sum(r['execution_time'] for r in self.test_results if r['job_executed']) / successful_executions if successful_executions else 0,
                "average_total_time": sum(r['total_time'] for r in self.test_results) / len(self.test_results) if self.test_results else 0
            },
            "job_analysis": {
                "total_jobs_created": len(self.job_ids),
                "job_ids": self.job_ids,
                "status_distribution": {}
            },
            "detailed_results": self.test_results,
            "performance_insights": {
                "fastest_creation": min((r['creation_time'] for r in self.test_results), default=0),
                "slowest_creation": max((r['creation_time'] for r in self.test_results), default=0),
                "fastest_execution": min((r['execution_time'] for r in self.test_results if r['job_executed']), default=0),
                "slowest_execution": max((r['execution_time'] for r in self.test_results if r['job_executed']), default=0)
            },
            "system_assessment": {
                "automation_engine_status": "Operational" if successful_creations > 0 else "Issues Detected",
                "job_execution_capability": "Functional" if successful_executions > 0 else "Limited",
                "workflow_completion_rate": f"{(completed_jobs / len(self.test_results) * 100):.1f}%" if self.test_results else "0%",
                "integration_maturity": "Production Ready" if completed_jobs >= len(self.test_results) * 0.8 else "Development/Testing"
            }
        }
        
        # Analyze status distribution
        for result in self.test_results:
            status = result['final_status']
            report['job_analysis']['status_distribution'][status] = report['job_analysis']['status_distribution'].get(status, 0) + 1
        
        # Save report
        timestamp = int(time.time())
        report_path = f"/home/opsconductor/opsconductor-ng/tests/e2e/intensive_automation_test_results_{timestamp}.json"
        
        with open(report_path, 'w') as f:
            json.dump(report, f, indent=2)
        
        logger.info(f"\n{'='*100}")
        logger.info("INTENSIVE AUTOMATION ENGINE TEST REPORT")
        logger.info(f"{'='*100}")
        logger.info(f"Total Tests: {report['test_run_info']['total_tests']}")
        logger.info(f"Successful Job Creations: {successful_creations}")
        logger.info(f"Successful Job Executions: {successful_executions}")
        logger.info(f"Completed Jobs: {completed_jobs}")
        logger.info(f"Success Rate: {(successful_executions / len(self.test_results) * 100):.1f}%")
        logger.info(f"Completion Rate: {(completed_jobs / len(self.test_results) * 100):.1f}%")
        logger.info(f"Average Creation Time: {report['test_run_info']['average_creation_time']:.2f}s")
        logger.info(f"Average Execution Time: {report['test_run_info']['average_execution_time']:.2f}s")
        logger.info(f"Average Total Time: {report['test_run_info']['average_total_time']:.2f}s")
        logger.info(f"Status Distribution: {report['job_analysis']['status_distribution']}")
        logger.info(f"System Assessment: {report['system_assessment']['integration_maturity']}")
        logger.info(f"Report saved to: {report_path}")
        
        return report

async def main():
    tester = DirectAutomationTester()
    await tester.run_intensive_automation_tests()
    report = await tester.generate_intensive_report()
    return report

if __name__ == "__main__":
    asyncio.run(main())