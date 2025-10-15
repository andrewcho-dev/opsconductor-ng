#!/usr/bin/env python3
"""
Test script to verify the C drive size retrieval execution plan
"""
import requests
import json
import time
from datetime import datetime

# Service endpoints
AUTOMATION_SERVICE = "http://localhost:8010"
ASSET_SERVICE = "http://localhost:8002"

def test_health_checks():
    """Verify services are healthy"""
    print("\n" + "="*80)
    print("HEALTH CHECKS")
    print("="*80)
    
    # Check automation service
    try:
        resp = requests.get(f"{AUTOMATION_SERVICE}/health", timeout=5)
        print(f"✅ Automation Service: {resp.status_code} - {resp.json()}")
    except Exception as e:
        print(f"❌ Automation Service: {e}")
        return False
    
    # Check asset service
    try:
        resp = requests.get(f"{ASSET_SERVICE}/health", timeout=5)
        print(f"✅ Asset Service: {resp.status_code} - {resp.json()}")
    except Exception as e:
        print(f"❌ Asset Service: {e}")
        return False
    
    return True

def test_cdrive_plan():
    """Test the C drive size retrieval plan"""
    print("\n" + "="*80)
    print("C DRIVE SIZE RETRIEVAL TEST")
    print("="*80)
    
    # Create execution plan
    execution_id = f"cdrive-test-{datetime.now().strftime('%Y%m%d-%H%M%S')}"
    
    plan = {
        "execution_id": execution_id,
        "plan": {
            "name": "Get C Drive Sizes - Windows 10",
            "description": "Query Windows 10 assets and retrieve C drive sizes",
            "steps": [
                {
                    "step_number": 1,
                    "name": "Find Windows 10 Assets",
                    "tool": "asset-query",
                    "parameters": {
                        "filters": {
                            "tags": ["win10"]
                        }
                    }
                },
                {
                    "step_number": 2,
                    "name": "Get C Drive Size",
                    "tool": "powershell",
                    "parameters": {
                        "target_hosts": ["{{hostname}}"],
                        "command": "Get-Volume -DriveLetter C | Select-Object DriveLetter, Size, SizeRemaining | ConvertTo-Json",
                        "username": "Administrator",
                        "password": "P@ssw0rd123"  # Test credentials
                    }
                }
            ]
        },
        "tenant_id": "test-tenant",
        "actor_id": 1
    }
    
    print(f"\n📋 Execution ID: {execution_id}")
    print(f"📋 Plan: {plan['plan']['name']}")
    print(f"📋 Steps: {len(plan['plan']['steps'])}")
    
    # Execute plan
    print("\n🚀 Executing plan...")
    try:
        resp = requests.post(
            f"{AUTOMATION_SERVICE}/execute-plan",
            json=plan,
            timeout=60
        )
        
        print(f"\n📊 Response Status: {resp.status_code}")
        
        if resp.status_code == 200:
            result = resp.json()
            print(f"\n✅ Execution completed successfully!")
            print(f"\n📄 Full Response:")
            print(json.dumps(result, indent=2))
            
            # Analyze results
            if "results" in result:
                print(f"\n📊 STEP RESULTS:")
                print("="*80)
                for step_result in result["results"]:
                    step_num = step_result.get("step_number", "?")
                    step_name = step_result.get("step_name", "Unknown")
                    status = step_result.get("status", "unknown")
                    
                    print(f"\nStep {step_num}: {step_name}")
                    print(f"  Status: {status}")
                    
                    if "result" in step_result:
                        step_data = step_result["result"]
                        if isinstance(step_data, dict):
                            # Asset query result
                            if "assets" in step_data:
                                assets = step_data["assets"]
                                print(f"  Assets Found: {len(assets)}")
                                for asset in assets:
                                    print(f"    - {asset.get('hostname', 'N/A')} ({asset.get('ip_address', 'N/A')})")
                            # PowerShell result
                            elif "output" in step_data:
                                print(f"  Output: {step_data['output'][:200]}...")
                        else:
                            print(f"  Result: {step_data}")
                    
                    if "error" in step_result:
                        print(f"  ❌ Error: {step_result['error']}")
            
            return True
        else:
            print(f"\n❌ Execution failed with status {resp.status_code}")
            print(f"Response: {resp.text}")
            return False
            
    except Exception as e:
        print(f"\n❌ Exception during execution: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_simple_asset_query():
    """Test just the asset query step"""
    print("\n" + "="*80)
    print("SIMPLE ASSET QUERY TEST")
    print("="*80)
    
    execution_id = f"asset-query-test-{datetime.now().strftime('%Y%m%d-%H%M%S')}"
    
    plan = {
        "execution_id": execution_id,
        "plan": {
            "name": "Find Windows 10 Assets",
            "description": "Query for Windows 10 assets only",
            "steps": [
                {
                    "step_number": 1,
                    "name": "Find Windows 10 Assets",
                    "tool": "asset-query",
                    "parameters": {
                        "filters": {
                            "tags": ["win10"]
                        }
                    }
                }
            ]
        },
        "tenant_id": "test-tenant",
        "actor_id": 1
    }
    
    print(f"\n📋 Execution ID: {execution_id}")
    
    try:
        resp = requests.post(
            f"{AUTOMATION_SERVICE}/execute-plan",
            json=plan,
            timeout=30
        )
        
        print(f"\n📊 Response Status: {resp.status_code}")
        
        if resp.status_code == 200:
            result = resp.json()
            print(f"\n✅ Query completed!")
            print(json.dumps(result, indent=2))
            return True
        else:
            print(f"\n❌ Query failed: {resp.text}")
            return False
            
    except Exception as e:
        print(f"\n❌ Exception: {e}")
        return False

if __name__ == "__main__":
    print("\n" + "="*80)
    print("C DRIVE SIZE RETRIEVAL - DIAGNOSTIC TEST")
    print("="*80)
    
    # Run tests
    if not test_health_checks():
        print("\n❌ Health checks failed. Exiting.")
        exit(1)
    
    # Test simple asset query first
    print("\n\n")
    if not test_simple_asset_query():
        print("\n❌ Asset query test failed.")
    
    # Test full C drive plan
    print("\n\n")
    if not test_cdrive_plan():
        print("\n❌ C drive plan test failed.")
    else:
        print("\n✅ All tests completed!")