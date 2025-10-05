#!/usr/bin/env python3
"""
Real-world AI Testing Script
Tests the OpsConductor AI system with realistic operational questions
"""

import asyncio
import sys
import os
import json
from datetime import datetime

# Add the project root to Python path
sys.path.insert(0, '/home/opsconductor/opsconductor-ng')

from pipeline.stages.stage_a.classifier import StageAClassifier
from pipeline.stages.stage_b.selector import StageBSelector
from pipeline.stages.stage_c.planner import StageCPlanner
from llm.ollama_client import OllamaClient

class RealWorldTester:
    def __init__(self):
        # Create real LLM client for authentic AI testing
        self.llm_client = OllamaClient({
            "base_url": "http://localhost:11434",
            "default_model": "qwen2.5:7b-instruct-q4_k_m",
            "timeout": 120
        })
        self.stage_a = StageAClassifier(self.llm_client)
        self.stage_b = StageBSelector(self.llm_client)
        self.stage_c = StageCPlanner(self.llm_client)
        
    async def test_question(self, question_num, question, category):
        """Test a single question through the complete AI pipeline"""
        print(f"\n{'='*80}")
        print(f"QUESTION {question_num}: {category}")
        print(f"{'='*80}")
        print(f"INPUT: {question}")
        print(f"\n{'-'*60}")
        
        try:
            # Stage A: Decision Making
            print("STAGE A - DECISION MAKING:")
            decision_result = await self.stage_a.classify(question, {
                'user_id': 'test_user',
                'session_id': 'test_session'
            })
            
            print(f"  Intent: {decision_result.intent.category}/{decision_result.intent.action}")
            print(f"  Entities: {[f'{e.type}:{e.value}' for e in decision_result.entities]}")
            print(f"  Confidence: {decision_result.confidence_level.value} ({decision_result.overall_confidence:.2f})")
            print(f"  Risk Level: {decision_result.risk_level.value}")
            print(f"  Decision Type: {decision_result.decision_type.value}")
            print(f"  Next Stage: {decision_result.next_stage}")
            
            if decision_result.decision_type.value == 'info':
                print("  → Information request - would route to Stage D (Information Retrieval)")
                return decision_result
                
            # Stage B: Tool Selection
            print(f"\n{'-'*40}")
            print("STAGE B - TOOL SELECTION:")
            
            selection_result = await self.stage_b.select_tools(decision_result, {
                'original_request': question
            })
            
            print(f"  Selected Tools: {[tool.name for tool in selection_result.selected_tools]}")
            print(f"  Execution Policy: {selection_result.execution_policy.type}")
            print(f"  Requires Approval: {selection_result.execution_policy.requires_approval}")
            print(f"  Environment Requirements: {selection_result.environment_requirements}")
            
            # Stage C: Planning
            print(f"\n{'-'*40}")
            print("STAGE C - PLANNING:")
            
            plan_result = self.stage_c.create_plan(decision_result, selection_result)
            
            print(f"  Plan ID: {plan_result.plan_id}")
            print(f"  Total Steps: {len(plan_result.execution_plan.execution_steps)}")
            print(f"  Safety Checks: {len(plan_result.execution_plan.safety_checks)}")
            print(f"  Estimated Duration: {plan_result.metadata.estimated_duration_seconds}s")
            
            # Show execution steps
            steps = plan_result.execution_plan.execution_steps
            if steps:
                print(f"  Execution Steps:")
                for i, step in enumerate(steps[:3], 1):  # Show first 3 steps
                    print(f"    {i}. {step.description}")
                    print(f"       Tool: {step.tool_name}")
                    print(f"       Risk: {step.risk_level}")
                if len(steps) > 3:
                    print(f"    ... and {len(steps) - 3} more steps")
            
            # Show safety checks
            safety_checks = plan_result.execution_plan.safety_checks
            if safety_checks:
                print(f"  Safety Checks:")
                for i, check in enumerate(safety_checks[:2], 1):  # Show first 2 checks
                    print(f"    {i}. {check.description}")
                if len(safety_checks) > 2:
                    print(f"    ... and {len(safety_checks) - 2} more checks")
            
            return {
                'decision': decision_result,
                'selection': selection_result,
                'plan': plan_result
            }
            
        except Exception as e:
            print(f"ERROR: {str(e)}")
            return {'error': str(e)}

    async def setup(self):
        """Setup LLM connection"""
        print("Connecting to Ollama LLM...")
        connected = await self.llm_client.connect()
        if not connected:
            raise Exception("Failed to connect to Ollama LLM")
        print("✓ Connected to Ollama LLM successfully")
        
    async def teardown(self):
        """Cleanup LLM connection"""
        await self.llm_client.disconnect()
        print("✓ Disconnected from Ollama LLM")

    async def run_all_tests(self):
        """Run all test questions"""
        
        test_questions = [
            # General diagnostics / discovery
            (1, "Check if 192.168.50.211 is reachable and tell me what OS it's running. If it's Linux, get CPU and memory usage.", "General Diagnostics"),
            (2, "Give me the uptime and active processes for all hosts tagged ring-A.", "General Discovery"),
            (3, "Show me every open TCP port on db-prod-03, but do not make any changes.", "General Discovery"),
            
            # Mixed info + action
            (4, "What services are failing on web-02? If nginx is down, restart it.", "Mixed Info + Action"),
            (5, "List all pods in the payments namespace on k8s-cluster-01, and roll any that are in CrashLoopBackOff.", "Mixed Info + Action"),
            (6, "Which interfaces are flapping on switch-core-01, and can you disable then re-enable the worst one?", "Mixed Info + Action"),
            
            # Multi-step jobs
            (7, "Upgrade nginx to the latest patch version on all staging web servers, one at a time, with a health check after each.", "Multi-step Jobs"),
            (8, "Drain half the nodes from load balancer pool LB01, patch them, verify, and then rotate through the rest.", "Multi-step Jobs"),
            (9, "Rotate SSH host keys on all bastion servers and update the jump host configuration accordingly.", "Multi-step Jobs"),
            
            # Ambiguous or missing info
            (10, "Restart the database server", "Ambiguous/Missing Info"),
            (11, "Get me disk usage for the finance VM", "Ambiguous/Missing Info"),
            (12, "Bounce the main interface on the core router", "Ambiguous/Missing Info"),
            
            # Security / policy-sensitive
            (13, "Reboot all production app servers now.", "Security/Policy Sensitive"),
            (14, "Delete user accounts inactive for 90 days from AD.", "Security/Policy Sensitive"),
            (15, "Stop the replication service on db-prod-01 for maintenance.", "Security/Policy Sensitive"),
            
            # Branching / conditional logic
            (16, "If web-01's CPU is over 80%, restart apache; otherwise, just show me top processes.", "Conditional Logic"),
            (17, "If the switch at 192.168.20.11 is reachable, pull its running config; if not, open a ticket.", "Conditional Logic"),
            (18, "Try SSH into backup-server-1; if that fails, attempt SNMP; if that fails, fall back to ICMP only.", "Conditional Logic"),
            
            # Complex group operations
            (19, "Patch 30 Windows servers in batches of 5 using WinRM, verify each batch before continuing, and roll back if a batch fails.", "Complex Group Operations"),
            (20, "Check SSL cert expiry dates on every host tagged external-facing, and create tickets for any expiring in < 15 days.", "Complex Group Operations"),
        ]
        
        print("OpsConductor AI Real-World Testing")
        print("=" * 80)
        print(f"Testing {len(test_questions)} realistic operational scenarios")
        print(f"Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        results = []
        
        for question_num, question, category in test_questions:
            result = await self.test_question(question_num, question, category)
            results.append({
                'question_num': question_num,
                'question': question,
                'category': category,
                'result': result
            })
            
            # Small delay between tests
            await asyncio.sleep(0.1)
        
        print(f"\n{'='*80}")
        print("TESTING COMPLETE")
        print(f"{'='*80}")
        print(f"Completed at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"Total questions tested: {len(results)}")
        
        # Summary statistics
        successful_tests = len([r for r in results if 'error' not in r['result']])
        print(f"Successful responses: {successful_tests}/{len(results)} ({successful_tests/len(results)*100:.1f}%)")
        
        return results

async def main():
    """Main test runner"""
    tester = RealWorldTester()
    
    try:
        # Setup LLM connection
        await tester.setup()
        
        # Run all tests
        results = await tester.run_all_tests()
        
    finally:
        # Cleanup
        await tester.teardown()
    
    # Save results to file for analysis
    with open('/home/opsconductor/opsconductor-ng/real_world_test_results.json', 'w') as f:
        json.dump(results, f, indent=2, default=str)
    
    print(f"\nDetailed results saved to: real_world_test_results.json")

if __name__ == "__main__":
    asyncio.run(main())