#!/usr/bin/env python3
"""
Simple test to verify asset filtering works
"""
import requests
import json
from datetime import datetime

AUTOMATION_SERVICE = "http://localhost:8010"

execution_id = f"filter-test-{datetime.now().strftime('%Y%m%d-%H%M%S')}"

plan = {
    "execution_id": execution_id,
    "plan": {
        "name": "Test Asset Filtering",
        "description": "Test that win10 tag filtering works",
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

print(f"Testing asset filtering with execution ID: {execution_id}")
print(f"Sending request to: {AUTOMATION_SERVICE}/execute-plan")
print(f"\nPlan:")
print(json.dumps(plan, indent=2))

try:
    resp = requests.post(
        f"{AUTOMATION_SERVICE}/execute-plan",
        json=plan,
        timeout=15
    )
    
    print(f"\nResponse Status: {resp.status_code}")
    
    if resp.status_code == 200:
        result = resp.json()
        print(f"\nResponse:")
        print(json.dumps(result, indent=2))
        
        # Check if filtering worked
        if "step_results" in result and len(result["step_results"]) > 0:
            step_result = result["step_results"][0]
            if "output" in step_result:
                output = step_result["output"]
                if "assets" in output:
                    assets = output["assets"]
                    print(f"\n✅ Found {len(assets)} assets")
                    for asset in assets:
                        print(f"  - {asset.get('name', 'N/A')} ({asset.get('hostname', 'N/A')}) - Tags: {asset.get('tags', [])}")
                    
                    # Verify all assets have win10 tag
                    all_have_win10 = all("win10" in asset.get("tags", []) for asset in assets)
                    if all_have_win10:
                        print(f"\n✅ SUCCESS: All assets have 'win10' tag - filtering works!")
                    else:
                        print(f"\n❌ FAILURE: Some assets don't have 'win10' tag - filtering not working!")
                else:
                    print(f"\n❌ No assets in output")
            else:
                print(f"\n❌ No output in step result")
        else:
            print(f"\n❌ No step results")
    else:
        print(f"\n❌ Request failed: {resp.text}")
        
except Exception as e:
    print(f"\n❌ Exception: {e}")
    import traceback
    traceback.print_exc()