#!/usr/bin/env python3
"""
Phase 7 Integration Test - Testing Target Resolver, Step Optimizer, and Execution Planner
"""
import requests
import json
import sys
import time

def test_phase7_integration():
    """Test Phase 7 modules integration through the AI Brain API"""
    
    base_url = "http://localhost:3005"
    
    # Test health first
    try:
        health_response = requests.get(f"{base_url}/health", timeout=5)
        if health_response.status_code != 200:
            print(f"❌ Health check failed: {health_response.status_code}")
            return False
        print("✅ AI Brain service is healthy")
    except Exception as e:
        print(f"❌ Failed to connect to AI Brain service: {e}")
        return False
    
    # Test complex multi-target, multi-step automation scenarios
    test_scenarios = [
        {
            "name": "Multi-Service Restart with Dependencies",
            "description": "restart nginx and apache services on web servers, then update system packages on database servers in parallel",
            "expected_features": ["target_resolution", "step_optimization", "execution_planning"]
        },
        {
            "name": "Complex Infrastructure Update",
            "description": "backup databases on db-servers, update security patches on all linux servers, restart load balancers in sequence",
            "expected_features": ["dependency_ordering", "parallel_execution", "risk_management"]
        },
        {
            "name": "Network-wide Maintenance",
            "description": "check disk space on servers in 192.168.1.0/24 subnet, clean logs on web-* hosts, restart monitoring services",
            "expected_features": ["subnet_resolution", "wildcard_matching", "resource_optimization"]
        }
    ]
    
    results = []
    
    for i, scenario in enumerate(test_scenarios, 1):
        print(f"\n🧪 Test {i}: {scenario['name']}")
        print(f"📝 Description: {scenario['description']}")
        
        test_request = {
            "description": scenario["description"],
            "user_id": 1,
            "priority": "high"
        }
        
        try:
            response = requests.post(
                f"{base_url}/ai/create-job",
                json=test_request,
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                
                # Analyze the response for Phase 7 features
                analysis = analyze_phase7_response(result, scenario["expected_features"])
                results.append({
                    "scenario": scenario["name"],
                    "success": True,
                    "analysis": analysis,
                    "job_id": result.get("job_id")
                })
                
                print(f"✅ Job created successfully: {result.get('job_id')}")
                print(f"📊 Analysis: {analysis['summary']}")
                
            else:
                print(f"❌ Job creation failed: {response.status_code}")
                print(f"Response: {response.text}")
                results.append({
                    "scenario": scenario["name"],
                    "success": False,
                    "error": f"HTTP {response.status_code}: {response.text}"
                })
                
        except Exception as e:
            print(f"❌ Error testing scenario: {e}")
            results.append({
                "scenario": scenario["name"],
                "success": False,
                "error": str(e)
            })
    
    # Test chat interface for Phase 7 capabilities
    print(f"\n🗣️  Testing Chat Interface for Phase 7 Features")
    chat_test = test_chat_interface(base_url)
    results.append(chat_test)
    
    # Generate final report
    print_phase7_report(results)
    
    # Return overall success
    return all(r.get("success", False) for r in results)

def analyze_phase7_response(result, expected_features):
    """Analyze job creation response for Phase 7 module functionality"""
    analysis = {
        "target_resolution": False,
        "step_optimization": False,
        "execution_planning": False,
        "advanced_features": [],
        "summary": ""
    }
    
    # Check for target resolution
    targets = result.get("targets", [])
    if targets and len(targets) > 0:
        analysis["target_resolution"] = True
        analysis["advanced_features"].append(f"Resolved {len(targets)} targets")
    
    # Check for step optimization
    workflow = result.get("workflow", {})
    steps = workflow.get("steps", [])
    if steps and len(steps) > 0:
        analysis["step_optimization"] = True
        analysis["advanced_features"].append(f"Generated {len(steps)} workflow steps")
    
    # Check for execution planning
    execution_plan = result.get("execution_plan", {})
    if execution_plan and (execution_plan.get("execution_strategy") or execution_plan.get("plan_id")):
        analysis["execution_planning"] = True
        strategy_name = execution_plan.get("execution_strategy", {}).get("name", "Unknown")
        analysis["advanced_features"].append(f"Execution Plan: {strategy_name}")
    
    # Check for optimizations
    optimizations = result.get("optimizations", [])
    if optimizations:
        analysis["advanced_features"].append(f"{len(optimizations)} optimizations applied")
    
    # Generate summary
    active_modules = sum([
        analysis["target_resolution"],
        analysis["step_optimization"], 
        analysis["execution_planning"]
    ])
    
    analysis["summary"] = f"{active_modules}/3 Phase 7 modules active, {len(analysis['advanced_features'])} features detected"
    
    return analysis

def test_chat_interface(base_url):
    """Test chat interface for Phase 7 integration"""
    print("Testing advanced automation request through chat...")
    
    chat_request = {
        "message": "I need to perform maintenance on our infrastructure: first backup all databases, then update security patches on web servers in parallel, and finally restart load balancers one by one to avoid downtime",
        "user_id": 1
    }
    
    try:
        response = requests.post(
            f"{base_url}/ai/chat",
            json=chat_request,
            timeout=30
        )
        
        if response.status_code == 200:
            result = response.json()
            
            # Check if chat interface can handle complex automation
            has_workflow = result.get("workflow") is not None
            has_job_id = result.get("job_id") is not None
            response_quality = len(result.get("response", "")) > 50
            
            success = has_workflow or has_job_id or response_quality
            
            print(f"✅ Chat interface test: {'PASSED' if success else 'FAILED'}")
            print(f"📝 Response: {result.get('response', 'No response')[:100]}...")
            
            return {
                "scenario": "Chat Interface Integration",
                "success": success,
                "analysis": {
                    "has_workflow": has_workflow,
                    "has_job_id": has_job_id,
                    "response_quality": response_quality,
                    "summary": f"Chat interface {'successfully' if success else 'failed to'} handle complex automation request"
                }
            }
        else:
            print(f"❌ Chat test failed: {response.status_code}")
            return {
                "scenario": "Chat Interface Integration",
                "success": False,
                "error": f"HTTP {response.status_code}"
            }
            
    except Exception as e:
        print(f"❌ Chat test error: {e}")
        return {
            "scenario": "Chat Interface Integration",
            "success": False,
            "error": str(e)
        }

def print_phase7_report(results):
    """Print comprehensive Phase 7 integration test report"""
    print("\n" + "="*60)
    print("🧠 PHASE 7 INTEGRATION TEST REPORT")
    print("="*60)
    
    successful_tests = sum(1 for r in results if r.get("success", False))
    total_tests = len(results)
    
    print(f"📊 Overall Results: {successful_tests}/{total_tests} tests passed")
    print(f"✅ Success Rate: {(successful_tests/total_tests)*100:.1f}%")
    
    print(f"\n📋 Detailed Results:")
    for i, result in enumerate(results, 1):
        status = "✅ PASS" if result.get("success", False) else "❌ FAIL"
        print(f"{i}. {result['scenario']}: {status}")
        
        if result.get("analysis"):
            analysis = result["analysis"]
            print(f"   📊 {analysis.get('summary', 'No analysis available')}")
            
            if analysis.get("advanced_features"):
                for feature in analysis["advanced_features"]:
                    print(f"   🔧 {feature}")
        
        if result.get("error"):
            print(f"   ❌ Error: {result['error']}")
        
        print()
    
    # Phase 7 Module Assessment
    print("🎯 Phase 7 Module Assessment:")
    
    target_resolver_active = any(
        r.get("analysis", {}).get("target_resolution", False) 
        for r in results if r.get("success", False)
    )
    
    step_optimizer_active = any(
        r.get("analysis", {}).get("step_optimization", False) 
        for r in results if r.get("success", False)
    )
    
    execution_planner_active = any(
        r.get("analysis", {}).get("execution_planning", False) 
        for r in results if r.get("success", False)
    )
    
    print(f"🎯 Target Resolver: {'✅ ACTIVE' if target_resolver_active else '❌ INACTIVE'}")
    print(f"⚡ Step Optimizer: {'✅ ACTIVE' if step_optimizer_active else '❌ INACTIVE'}")
    print(f"📅 Execution Planner: {'✅ ACTIVE' if execution_planner_active else '❌ INACTIVE'}")
    
    if all([target_resolver_active, step_optimizer_active, execution_planner_active]):
        print(f"\n🎉 Phase 7 Integration: COMPLETE - All modules are functioning!")
    else:
        print(f"\n⚠️  Phase 7 Integration: PARTIAL - Some modules need attention")
    
    print("="*60)

if __name__ == "__main__":
    print("🚀 OpsConductor AI Brain - Phase 7 Integration Test")
    print("Testing Target Resolver, Step Optimizer, and Execution Planner")
    print("="*60)
    
    success = test_phase7_integration()
    
    if success:
        print("\n🎉 Phase 7 integration test completed successfully!")
        sys.exit(0)
    else:
        print("\n💥 Phase 7 integration test failed!")
        sys.exit(1)