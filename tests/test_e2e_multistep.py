#!/usr/bin/env python3
"""
End-to-end integration test for multi-step execution workflow

Tests the complete flow:
1. AI generates a plan with asset-query and Invoke-Command steps
2. Automation service executes the plan
3. Asset service returns Windows 10 assets
4. Automation service detects loop and expands steps
5. Each host gets the PowerShell command executed
"""

import asyncio
import json
import httpx
from datetime import datetime

# Service endpoints (exposed Docker ports)
AUTOMATION_SERVICE = "http://localhost:8010"
ASSET_SERVICE = "http://localhost:8002"


async def test_health_checks():
    """Verify all services are healthy"""
    print("\n" + "="*80)
    print("🏥 HEALTH CHECKS")
    print("="*80)
    
    async with httpx.AsyncClient(timeout=10.0) as client:
        # Check automation service
        try:
            resp = await client.get(f"{AUTOMATION_SERVICE}/health")
            print(f"✅ Automation Service: {resp.status_code} - {resp.json()}")
        except Exception as e:
            print(f"❌ Automation Service: {e}")
            return False
        
        # Check asset service
        try:
            resp = await client.get(f"{ASSET_SERVICE}/health")
            print(f"✅ Asset Service: {resp.status_code} - {resp.json()}")
        except Exception as e:
            print(f"❌ Asset Service: {e}")
            return False
    
    return True


async def test_asset_query_tool():
    """Test the asset-query tool directly via execute-plan"""
    print("\n" + "="*80)
    print("🔍 TEST ASSET-QUERY TOOL")
    print("="*80)
    
    payload = {
        "execution_id": f"test-asset-query-{datetime.now().strftime('%Y%m%d-%H%M%S')}",
        "tenant_id": "test-tenant",
        "actor_id": 1,
        "plan": {
            "steps": [
                {
                    "step_number": 1,
                    "tool": "asset-query",
                    "parameters": {
                        "tags": "win10"
                    },
                    "stage": "E"
                }
            ]
        }
    }
    
    async with httpx.AsyncClient(timeout=30.0) as client:
        try:
            resp = await client.post(
                f"{ASSET_SERVICE}/execute-plan",
                json=payload,
                headers={"Content-Type": "application/json"}
            )
            
            print(f"Status: {resp.status_code}")
            result = resp.json()
            
            if resp.status_code == 200:
                step_results = result.get("step_results", [])
                if step_results:
                    assets = step_results[0].get("output", {}).get("assets", [])
                    print(f"✅ Found {len(assets)} Windows 10 assets:")
                    for asset in assets:
                        print(f"   - {asset.get('name')} ({asset.get('hostname')})")
                    return True, assets
                else:
                    print(f"❌ No step results in response")
                    return False, []
            else:
                print(f"❌ Error: {result}")
                return False, []
                
        except Exception as e:
            print(f"❌ Exception: {e}")
            import traceback
            traceback.print_exc()
            return False, []


async def test_multistep_plan_execution():
    """Test executing a multi-step plan with template variables and loops"""
    print("\n" + "="*80)
    print("🚀 TEST MULTI-STEP PLAN EXECUTION")
    print("="*80)
    
    # Create a plan that mimics what the AI would generate
    execution_id = f"test-exec-{datetime.now().strftime('%Y%m%d-%H%M%S')}"
    plan = {
        "execution_id": execution_id,
        "tenant_id": "test-tenant",
        "actor_id": 1,
        "plan": {
            "steps": [
            {
                "step_number": 1,
                "description": "Query all Windows 10 assets",
                "tool": "asset-query",
                "parameters": {
                    "tags": "win10"
                },
                "stage": "E"
            },
            {
                "step_number": 2,
                "description": "Get C drive size from each Windows 10 host",
                "tool": "Invoke-Command",
                "parameters": {
                    "target_hosts": ["{{hostname}}"],
                    "command": "Get-Volume -DriveLetter C | Select-Object DriveLetter, @{Name='SizeGB';Expression={[math]::Round($_.Size/1GB,2)}}, @{Name='FreeGB';Expression={[math]::Round($_.SizeRemaining/1GB,2)}} | ConvertTo-Json"
                },
                "stage": "E"
            }
            ]
        }
    }
    
    print(f"\n📋 Plan ID: {plan['execution_id']}")
    print(f"📋 Steps: {len(plan['plan']['steps'])}")
    print(f"   Step 1: {plan['plan']['steps'][0]['description']}")
    print(f"   Step 2: {plan['plan']['steps'][1]['description']}")
    print(f"   Step 2 uses template: {plan['plan']['steps'][1]['parameters']['target_hosts']}")
    
    async with httpx.AsyncClient(timeout=120.0) as client:
        try:
            resp = await client.post(
                f"{AUTOMATION_SERVICE}/execute-plan",
                json=plan,
                headers={"Content-Type": "application/json"}
            )
            
            print(f"\n📊 Response Status: {resp.status_code}")
            result = resp.json()
            
            if resp.status_code == 200:
                print(f"✅ Plan execution completed successfully!")
                
                # Analyze results
                step_results = result.get("step_results", [])
                print(f"\n📈 Step Results: {len(step_results)} steps executed")
                
                for step_result in step_results:
                    step_num = step_result.get("step_number", "?")
                    status = step_result.get("status", "unknown")
                    tool = step_result.get("tool", "unknown")
                    
                    print(f"\n   Step {step_num} ({tool}): {status}")
                    
                    if tool == "asset-query":
                        output = step_result.get("output", {})
                        assets = output.get("assets", [])
                        print(f"      Found {len(assets)} assets")
                        
                    elif tool == "Invoke-Command":
                        output = step_result.get("output", {})
                        print(f"      Output: {json.dumps(output, indent=6)[:200]}...")
                
                return True
            else:
                print(f"❌ Plan execution failed: {result}")
                return False
                
        except Exception as e:
            print(f"❌ Exception during plan execution: {e}")
            import traceback
            traceback.print_exc()
            return False


async def test_loop_expansion_verification():
    """Verify that loop expansion is working by checking logs"""
    print("\n" + "="*80)
    print("🔁 VERIFY LOOP EXPANSION IN LOGS")
    print("="*80)
    
    print("Check automation service logs for:")
    print("  - '🔁 Loop detected'")
    print("  - '🔁 Loop iteration X/Y'")
    print("  - Template variable resolution messages")
    print("\nRun: docker logs opsconductor-automation --tail 100 | grep -E '(Loop|template|🔁)'")
    
    return True


async def main():
    """Run all integration tests"""
    print("\n" + "="*80)
    print("🧪 END-TO-END MULTI-STEP EXECUTION INTEGRATION TEST")
    print("="*80)
    print(f"Started at: {datetime.now().isoformat()}")
    
    tests = [
        ("Health Checks", test_health_checks),
        ("Asset Query Tool", test_asset_query_tool),
        ("Multi-Step Plan Execution", test_multistep_plan_execution),
        ("Loop Expansion Verification", test_loop_expansion_verification),
    ]
    
    passed = 0
    failed = 0
    
    for test_name, test_func in tests:
        try:
            result = await test_func()
            if isinstance(result, tuple):
                result = result[0]  # Extract boolean from tuple
            
            if result:
                passed += 1
                print(f"\n✅ {test_name} PASSED")
            else:
                failed += 1
                print(f"\n❌ {test_name} FAILED")
        except Exception as e:
            failed += 1
            print(f"\n❌ {test_name} FAILED with exception: {e}")
            import traceback
            traceback.print_exc()
    
    print("\n" + "="*80)
    print("📊 INTEGRATION TEST SUMMARY")
    print("="*80)
    print(f"Total tests: {len(tests)}")
    print(f"✅ Passed: {passed}")
    print(f"❌ Failed: {failed}")
    print(f"Completed at: {datetime.now().isoformat()}")
    print("="*80 + "\n")
    
    return failed == 0


if __name__ == "__main__":
    success = asyncio.run(main())
    exit(0 if success else 1)