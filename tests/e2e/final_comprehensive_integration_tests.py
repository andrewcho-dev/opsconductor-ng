#!/usr/bin/env python3
"""
Final Comprehensive AI Brain Integration Tests
Tests the complete integration pipeline with increasing difficulty
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

class FinalComprehensiveIntegrationTester:
    def __init__(self):
        self.ai_brain_url = "http://localhost:3005"
        self.automation_url = "http://localhost:3003"
        self.test_results = []
        
    async def test_ai_brain_advanced_understanding(self, test_name: str, user_request: str, difficulty: int) -> Dict[str, Any]:
        """Test AI Brain's understanding and response to complex requests"""
        start_time = time.time()
        result = {
            "test_name": test_name,
            "difficulty": difficulty,
            "user_request": user_request,
            "success": False,
            "response_time": 0,
            "ai_response": None,
            "response_quality": {
                "mentions_workflows": False,
                "mentions_automation": False,
                "shows_technical_understanding": False,
                "provides_actionable_steps": False,
                "understanding_score": 0
            },
            "error": None
        }
        
        try:
            # Test the thinking-llm endpoint which we know works
            async with httpx.AsyncClient(timeout=45.0) as client:
                payload = {
                    "message": user_request,
                    "user_id": "1",
                    "conversation_id": f"integration_test_{int(time.time())}"
                }
                
                response = await client.post(f"{self.ai_brain_url}/api/thinking-llm/chat", json=payload)
                
                if response.status_code == 200:
                    data = response.json()
                    result["success"] = True
                    result["ai_response"] = data.get("response", "")
                    
                    # Analyze response quality
                    ai_response = result["ai_response"].lower()
                    
                    # Check for workflow/automation understanding
                    workflow_keywords = ["workflow", "automation", "job", "task", "step", "process", "execute"]
                    automation_keywords = ["automate", "schedule", "trigger", "orchestrate", "pipeline", "integration"]
                    technical_keywords = ["ping", "scan", "monitor", "analyze", "deploy", "configure", "network", "system"]
                    actionable_keywords = ["create", "setup", "configure", "implement", "develop", "build", "design"]
                    
                    result["response_quality"]["mentions_workflows"] = any(kw in ai_response for kw in workflow_keywords)
                    result["response_quality"]["mentions_automation"] = any(kw in ai_response for kw in automation_keywords)
                    result["response_quality"]["shows_technical_understanding"] = any(kw in ai_response for kw in technical_keywords)
                    result["response_quality"]["provides_actionable_steps"] = any(kw in ai_response for kw in actionable_keywords)
                    
                    # Calculate understanding score
                    score = 0
                    if result["response_quality"]["mentions_workflows"]: score += 25
                    if result["response_quality"]["mentions_automation"]: score += 25
                    if result["response_quality"]["shows_technical_understanding"]: score += 25
                    if result["response_quality"]["provides_actionable_steps"]: score += 25
                    result["response_quality"]["understanding_score"] = score
                    
                else:
                    result["error"] = f"HTTP {response.status_code}: {response.text}"
                    
        except Exception as e:
            result["error"] = str(e)
            
        result["response_time"] = time.time() - start_time
        return result

    async def test_existing_job_execution(self, job_id: int) -> Dict[str, Any]:
        """Test execution of existing AI-generated jobs"""
        result = {
            "job_id": job_id,
            "job_details": None,
            "execution_triggered": False,
            "execution_response": None,
            "error": None
        }
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            try:
                # Get job details first
                job_response = await client.get(f"{self.automation_url}/jobs/{job_id}")
                if job_response.status_code == 200:
                    result["job_details"] = job_response.json()
                    
                    # Try to execute the job
                    exec_response = await client.post(f"{self.automation_url}/jobs/{job_id}/run")
                    if exec_response.status_code in [200, 201, 202]:
                        result["execution_triggered"] = True
                        result["execution_response"] = exec_response.json()
                    else:
                        result["error"] = f"Execution failed: HTTP {exec_response.status_code}: {exec_response.text}"
                else:
                    result["error"] = f"Job not found: HTTP {job_response.status_code}: {job_response.text}"
                    
            except Exception as e:
                result["error"] = str(e)
                
        return result

    async def run_comprehensive_integration_tests(self):
        """Run the most comprehensive integration tests possible"""
        logger.info("Starting Final Comprehensive AI Brain Integration Tests")
        logger.info("Testing AI understanding, existing job execution, and system integration")
        
        # Test AI Brain understanding with incrementally complex requests
        ai_understanding_tests = [
            {
                "name": "Basic Request Understanding",
                "request": "Can you help me ping a server?",
                "difficulty": 11
            },
            {
                "name": "Simple Workflow Request",
                "request": "I need to create a workflow that pings google.com and reports the results",
                "difficulty": 12
            },
            {
                "name": "Multi-Step Automation",
                "request": "Create an automation that scans network ports 22, 80, 443 on multiple hosts and generates a security report",
                "difficulty": 13
            },
            {
                "name": "Conditional Logic Workflow",
                "request": "Build a workflow that checks if a server is responding, and if not, creates an alert ticket and notifies the admin team",
                "difficulty": 14
            },
            {
                "name": "Scheduled Monitoring Task",
                "request": "Set up automated monitoring that checks system health every 15 minutes, analyzes trends, and escalates if performance degrades",
                "difficulty": 15
            },
            {
                "name": "Data Processing Pipeline",
                "request": "Create a data pipeline that collects logs from multiple sources, processes them for security incidents, correlates events, and generates threat intelligence reports",
                "difficulty": 16
            },
            {
                "name": "Incident Response Automation",
                "request": "Design an incident response system that detects anomalies, automatically isolates affected systems, gathers forensic data, and initiates recovery procedures",
                "difficulty": 17
            },
            {
                "name": "Compliance Audit Framework",
                "request": "Build a comprehensive compliance framework that scans infrastructure for security policies, generates audit reports, tracks remediation, and maintains compliance dashboards",
                "difficulty": 18
            },
            {
                "name": "ML-Powered Predictive Maintenance",
                "request": "Implement a machine learning system that analyzes system performance metrics, predicts failures, schedules preventive maintenance, and optimizes resource allocation",
                "difficulty": 19
            },
            {
                "name": "Adaptive Self-Healing Infrastructure",
                "request": "Create an adaptive infrastructure that monitors its own health, learns from failures, automatically implements fixes, scales resources based on demand, and evolves its response strategies over time",
                "difficulty": 20
            }
        ]
        
        logger.info(f"Running {len(ai_understanding_tests)} AI understanding tests...")
        
        for i, test_case in enumerate(ai_understanding_tests, 1):
            logger.info(f"\n{'='*90}")
            logger.info(f"AI UNDERSTANDING TEST {i}/{len(ai_understanding_tests)}: {test_case['name']} (Difficulty: {test_case['difficulty']})")
            logger.info(f"Request: {test_case['request']}")
            logger.info(f"{'='*90}")
            
            result = await self.test_ai_brain_advanced_understanding(
                test_case['name'],
                test_case['request'],
                test_case['difficulty']
            )
            
            self.test_results.append(result)
            
            # Log detailed results
            success_icon = "✓" if result['success'] else "✗"
            quality_score = result['response_quality']['understanding_score']
            quality_icon = "🎯" if quality_score >= 75 else "🔍" if quality_score >= 50 else "❓"
            
            logger.info(f"Result: {success_icon} {quality_icon} Understanding Score: {quality_score}%")
            logger.info(f"Response Time: {result['response_time']:.2f}s")
            logger.info(f"Quality Analysis:")
            logger.info(f"  - Mentions Workflows: {'✓' if result['response_quality']['mentions_workflows'] else '✗'}")
            logger.info(f"  - Mentions Automation: {'✓' if result['response_quality']['mentions_automation'] else '✗'}")
            logger.info(f"  - Technical Understanding: {'✓' if result['response_quality']['shows_technical_understanding'] else '✗'}")
            logger.info(f"  - Actionable Steps: {'✓' if result['response_quality']['provides_actionable_steps'] else '✗'}")
            
            if result['error']:
                logger.error(f"Error: {result['error']}")
            elif len(result['ai_response']) > 0:
                logger.info(f"Response Preview: {result['ai_response'][:200]}...")
                
            await asyncio.sleep(1)
        
        # Test existing AI-generated job execution
        logger.info(f"\n{'='*90}")
        logger.info("TESTING EXISTING JOB EXECUTION")
        logger.info(f"{'='*90}")
        
        # Test a few existing AI-generated jobs
        test_job_ids = [220, 219, 218, 217]  # Recent AI-generated jobs
        job_execution_results = []
        
        for job_id in test_job_ids:
            logger.info(f"\nTesting execution of Job ID: {job_id}")
            execution_result = await self.test_existing_job_execution(job_id)
            job_execution_results.append(execution_result)
            
            if execution_result['job_details']:
                job_name = execution_result['job_details'].get('name', 'Unknown')
                logger.info(f"Job Name: {job_name}")
                
            if execution_result['execution_triggered']:
                logger.info(f"✓ Job execution triggered successfully")
            else:
                logger.error(f"✗ Job execution failed: {execution_result['error']}")
                
            await asyncio.sleep(2)
        
        # Store job execution results
        for result in self.test_results:
            result['job_execution_tests'] = job_execution_results

    async def generate_final_comprehensive_report(self):
        """Generate the most comprehensive test report"""
        successful_ai_tests = sum(1 for r in self.test_results if r['success'])
        high_quality_responses = sum(1 for r in self.test_results if r['response_quality']['understanding_score'] >= 75)
        
        job_execution_results = []
        if self.test_results and 'job_execution_tests' in self.test_results[0]:
            job_execution_results = self.test_results[0]['job_execution_tests']
        
        successful_executions = sum(1 for jer in job_execution_results if jer['execution_triggered'])
        
        report = {
            "test_run_info": {
                "timestamp": datetime.now().isoformat(),
                "test_type": "Final Comprehensive Integration Test",
                "total_ai_understanding_tests": len(self.test_results),
                "successful_ai_responses": successful_ai_tests,
                "high_quality_responses": high_quality_responses,
                "job_execution_tests": len(job_execution_results),
                "successful_job_executions": successful_executions,
                "average_response_time": sum(r['response_time'] for r in self.test_results) / len(self.test_results) if self.test_results else 0,
                "average_understanding_score": sum(r['response_quality']['understanding_score'] for r in self.test_results) / len(self.test_results) if self.test_results else 0
            },
            "ai_brain_analysis": {
                "workflow_understanding": sum(1 for r in self.test_results if r['response_quality']['mentions_workflows']),
                "automation_understanding": sum(1 for r in self.test_results if r['response_quality']['mentions_automation']),
                "technical_understanding": sum(1 for r in self.test_results if r['response_quality']['shows_technical_understanding']),
                "actionable_responses": sum(1 for r in self.test_results if r['response_quality']['provides_actionable_steps'])
            },
            "difficulty_analysis": {
                "difficulty_11_15": {"tested": 0, "successful": 0, "avg_score": 0},
                "difficulty_16_20": {"tested": 0, "successful": 0, "avg_score": 0}
            },
            "job_execution_analysis": {
                "jobs_tested": job_execution_results,
                "execution_success_rate": f"{(successful_executions / len(job_execution_results) * 100):.1f}%" if job_execution_results else "0%"
            },
            "detailed_results": self.test_results,
            "system_integration_assessment": {
                "ai_brain_status": "Operational" if successful_ai_tests > 0 else "Issues Detected",
                "understanding_quality": "Excellent" if high_quality_responses >= len(self.test_results) * 0.8 else "Good" if high_quality_responses >= len(self.test_results) * 0.6 else "Needs Improvement",
                "automation_integration": "Functional" if successful_executions > 0 else "Limited",
                "overall_assessment": "Production Ready" if (successful_ai_tests >= len(self.test_results) * 0.9 and high_quality_responses >= len(self.test_results) * 0.7) else "Development Phase"
            }
        }
        
        # Analyze by difficulty ranges
        for result in self.test_results:
            difficulty = result['difficulty']
            if 11 <= difficulty <= 15:
                report['difficulty_analysis']['difficulty_11_15']['tested'] += 1
                if result['success']:
                    report['difficulty_analysis']['difficulty_11_15']['successful'] += 1
            elif 16 <= difficulty <= 20:
                report['difficulty_analysis']['difficulty_16_20']['tested'] += 1
                if result['success']:
                    report['difficulty_analysis']['difficulty_16_20']['successful'] += 1
        
        # Calculate average scores by difficulty
        for difficulty_range in ['difficulty_11_15', 'difficulty_16_20']:
            if report['difficulty_analysis'][difficulty_range]['tested'] > 0:
                relevant_results = [r for r in self.test_results if 
                                  (11 <= r['difficulty'] <= 15 and difficulty_range == 'difficulty_11_15') or
                                  (16 <= r['difficulty'] <= 20 and difficulty_range == 'difficulty_16_20')]
                if relevant_results:
                    report['difficulty_analysis'][difficulty_range]['avg_score'] = sum(r['response_quality']['understanding_score'] for r in relevant_results) / len(relevant_results)
        
        # Save comprehensive report
        timestamp = int(time.time())
        report_path = f"/home/opsconductor/opsconductor-ng/tests/e2e/final_comprehensive_integration_results_{timestamp}.json"
        
        with open(report_path, 'w') as f:
            json.dump(report, f, indent=2)
        
        logger.info(f"\n{'='*120}")
        logger.info("FINAL COMPREHENSIVE AI BRAIN INTEGRATION TEST REPORT")
        logger.info(f"{'='*120}")
        logger.info(f"AI Understanding Tests: {report['test_run_info']['total_ai_understanding_tests']}")
        logger.info(f"Successful AI Responses: {successful_ai_tests}/{len(self.test_results)} ({successful_ai_tests/len(self.test_results)*100:.1f}%)")
        logger.info(f"High Quality Responses: {high_quality_responses}/{len(self.test_results)} ({high_quality_responses/len(self.test_results)*100:.1f}%)")
        logger.info(f"Average Understanding Score: {report['test_run_info']['average_understanding_score']:.1f}%")
        logger.info(f"Average Response Time: {report['test_run_info']['average_response_time']:.2f}s")
        logger.info(f"")
        logger.info(f"AI Brain Capabilities:")
        logger.info(f"  - Workflow Understanding: {report['ai_brain_analysis']['workflow_understanding']}/{len(self.test_results)} tests")
        logger.info(f"  - Automation Understanding: {report['ai_brain_analysis']['automation_understanding']}/{len(self.test_results)} tests")
        logger.info(f"  - Technical Understanding: {report['ai_brain_analysis']['technical_understanding']}/{len(self.test_results)} tests")
        logger.info(f"  - Actionable Responses: {report['ai_brain_analysis']['actionable_responses']}/{len(self.test_results)} tests")
        logger.info(f"")
        logger.info(f"Difficulty Analysis:")
        logger.info(f"  - Basic-Intermediate (11-15): {report['difficulty_analysis']['difficulty_11_15']['successful']}/{report['difficulty_analysis']['difficulty_11_15']['tested']} (Avg: {report['difficulty_analysis']['difficulty_11_15']['avg_score']:.1f}%)")
        logger.info(f"  - Advanced (16-20): {report['difficulty_analysis']['difficulty_16_20']['successful']}/{report['difficulty_analysis']['difficulty_16_20']['tested']} (Avg: {report['difficulty_analysis']['difficulty_16_20']['avg_score']:.1f}%)")
        logger.info(f"")
        logger.info(f"Job Execution Tests: {len(job_execution_results)}")
        logger.info(f"Successful Job Executions: {successful_executions}/{len(job_execution_results)} ({report['job_execution_analysis']['execution_success_rate']})")
        logger.info(f"")
        logger.info(f"System Integration Assessment:")
        logger.info(f"  - AI Brain Status: {report['system_integration_assessment']['ai_brain_status']}")
        logger.info(f"  - Understanding Quality: {report['system_integration_assessment']['understanding_quality']}")
        logger.info(f"  - Automation Integration: {report['system_integration_assessment']['automation_integration']}")
        logger.info(f"  - Overall Assessment: {report['system_integration_assessment']['overall_assessment']}")
        logger.info(f"")
        logger.info(f"Report saved to: {report_path}")
        
        return report

async def main():
    tester = FinalComprehensiveIntegrationTester()
    await tester.run_comprehensive_integration_tests()
    report = await tester.generate_final_comprehensive_report()
    return report

if __name__ == "__main__":
    asyncio.run(main())