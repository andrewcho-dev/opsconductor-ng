#!/usr/bin/env python3
"""
Test C Drive Retrieval with Asset Credentials
This test uses the credentials stored in the database for each Windows 10 asset.
"""

import requests
import json
from datetime import datetime

# Configuration
AUTOMATION_SERVICE_URL = "http://localhost:8010"

def test_cdrive_with_credentials():
    """Test C drive retrieval using asset credentials from database"""
    
    execution_id = f"cdrive-test-{datetime.now().strftime('%Y%m%d-%H%M%S')}"
    
    # Execution plan with use_asset_credentials enabled
    plan = {
        "execution_id": execution_id,
        "plan": {
            "name": "Get C Drive Sizes from Windows 10 Assets",
            "description": "Query Windows 10 assets and retrieve C drive sizes using stored credentials",
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
                        "target_hosts": ["{{item.ip_address}}"],
                        "command": "Get-Volume -DriveLetter C | Select-Object DriveLetter, @{Name='SizeGB';Expression={[math]::Round($_.Size/1GB,2)}}, @{Name='FreeGB';Expression={[math]::Round($_.SizeRemaining/1GB,2)}} | ConvertTo-Json",
                        "use_asset_credentials": True  # Use credentials from database
                    }
                }
            ]
        },
        "tenant_id": "test-tenant",
        "actor_id": 1
    }
    
    print(f"Testing C Drive Retrieval with Asset Credentials")
    print(f"Execution ID: {execution_id}")
    print(f"\nSending request to: {AUTOMATION_SERVICE_URL}/execute-plan")
    print(f"\nPlan:")
    print(json.dumps(plan, indent=2))
    
    try:
        response = requests.post(
            f"{AUTOMATION_SERVICE_URL}/execute-plan",
            json=plan,
            headers={"Content-Type": "application/json"},
            timeout=120  # 2 minute timeout
        )
        
        print(f"\nResponse Status: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print(f"\nResponse:")
            print(json.dumps(result, indent=2))
            
            # Analyze results
            print("\n" + "="*80)
            print("EXECUTION SUMMARY")
            print("="*80)
            
            status = result.get("status", "unknown")
            print(f"Status: {status}")
            
            if "result" in result:
                summary = result["result"]
                print(f"Steps Completed: {summary.get('steps_completed', 0)}")
                print(f"Steps Succeeded: {summary.get('steps_succeeded', 0)}")
                print(f"Steps Failed: {summary.get('steps_failed', 0)}")
            
            # Show step results
            if "step_results" in result:
                print(f"\n{'='*80}")
                print("STEP RESULTS")
                print(f"{'='*80}")
                
                for step_result in result["step_results"]:
                    step_num = step_result.get("step", "?")
                    tool = step_result.get("tool", "unknown")
                    step_status = step_result.get("status", "unknown")
                    
                    print(f"\nStep {step_num}: {tool}")
                    print(f"  Status: {step_status}")
                    
                    if "output" in step_result:
                        output = step_result["output"]
                        
                        # For asset-query step
                        if tool == "asset-query" and isinstance(output, dict):
                            if output.get("success"):
                                assets = output.get("assets", [])
                                print(f"  Found {len(assets)} Windows 10 assets:")
                                for asset in assets:
                                    print(f"    - {asset.get('name')} ({asset.get('ip_address')})")
                        
                        # For PowerShell step
                        elif tool == "powershell":
                            if isinstance(output, list):
                                print(f"  Executed on {len(output)} hosts:")
                                for host_result in output:
                                    hostname = host_result.get("host", "unknown")
                                    success = host_result.get("success", False)
                                    
                                    if success:
                                        print(f"    ✅ {hostname}")
                                        stdout = host_result.get("stdout", "")
                                        if stdout:
                                            try:
                                                drive_info = json.loads(stdout)
                                                size_gb = drive_info.get("SizeGB", "?")
                                                free_gb = drive_info.get("FreeGB", "?")
                                                used_gb = size_gb - free_gb if isinstance(size_gb, (int, float)) and isinstance(free_gb, (int, float)) else "?"
                                                print(f"       C: Drive - Total: {size_gb} GB, Free: {free_gb} GB, Used: {used_gb} GB")
                                            except:
                                                print(f"       Output: {stdout[:100]}")
                                    else:
                                        error = host_result.get("error", "Unknown error")
                                        print(f"    ❌ {hostname}: {error}")
            
            # Final verdict
            print(f"\n{'='*80}")
            if status == "completed" and result.get("result", {}).get("steps_failed", 0) == 0:
                print("✅ SUCCESS: C drive sizes retrieved from all Windows 10 assets!")
            elif status == "completed":
                print("⚠️  PARTIAL SUCCESS: Some steps failed")
            else:
                print("❌ FAILED: Execution did not complete successfully")
            print(f"{'='*80}\n")
            
        else:
            print(f"\n❌ Request failed with status {response.status_code}")
            print(f"Response: {response.text}")
    
    except requests.exceptions.Timeout:
        print("\n❌ Request timed out after 120 seconds")
    except Exception as e:
        print(f"\n❌ Error: {e}")

if __name__ == "__main__":
    test_cdrive_with_credentials()