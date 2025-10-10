#!/usr/bin/env python3
"""
Multi-Step Execution System Demo

This script demonstrates the complete multi-step execution workflow with:
- Asset discovery via asset-query
- Template variable resolution
- Loop execution over multiple targets
- Real-world automation scenarios
"""

import httpx
import json
from datetime import datetime
import time

# Service endpoints
AUTOMATION_SERVICE = "http://localhost:8010"
ASSET_SERVICE = "http://localhost:8002"

def print_section(title):
    """Print a formatted section header"""
    print("\n" + "=" * 80)
    print(f"🎯 {title}")
    print("=" * 80)

def print_step(step_num, description):
    """Print a formatted step"""
    print(f"\n📍 Step {step_num}: {description}")
    print("-" * 80)

def execute_plan(plan_name, steps, description=""):
    """Execute a multi-step plan and display results"""
    execution_id = f"demo-{datetime.now().strftime('%Y%m%d-%H%M%S')}"
    
    print(f"\n🚀 Executing Plan: {plan_name}")
    if description:
        print(f"   {description}")
    print(f"   Execution ID: {execution_id}")
    print(f"   Steps: {len(steps)}")
    
    # Display plan steps
    for i, step in enumerate(steps, 1):
        tool = step.get("tool", "unknown")
        print(f"   {i}. {tool}")
    
    # Execute plan
    payload = {
        "execution_id": execution_id,
        "plan": {
            "name": plan_name,
            "steps": steps
        },
        "tenant_id": "demo-tenant",
        "actor_id": 1  # Must be int, not string
    }
    
    print(f"\n📤 Sending request to automation service...")
    
    try:
        response = httpx.post(
            f"{AUTOMATION_SERVICE}/execute-plan",
            json=payload,
            timeout=120.0
        )
        response.raise_for_status()
        result = response.json()
        
        print(f"✅ Status: {response.status_code}")
        print(f"✅ Execution Status: {result.get('status', 'unknown')}")
        
        # Display step results
        step_results = result.get("step_results", [])
        print(f"\n📊 Step Results ({len(step_results)} steps executed):")
        
        for step_result in step_results:
            step_num = step_result.get("step", "?")
            tool = step_result.get("tool", "unknown")
            status = step_result.get("status", "unknown")
            
            # Check if this is a loop iteration
            loop_iter = step_result.get("loop_iteration")
            loop_total = step_result.get("loop_total")
            
            if loop_iter and loop_total:
                print(f"\n   Step {step_num} ({tool}) - Iteration {loop_iter}/{loop_total}: {status}")
            else:
                print(f"\n   Step {step_num} ({tool}): {status}")
            
            # Display relevant output
            if tool == "asset-query":
                output = step_result.get("output", {})
                assets = output.get("assets", [])
                print(f"      Found {len(assets)} assets")
                for asset in assets[:5]:  # Show first 5
                    hostname = asset.get("hostname", "unknown")
                    ip = asset.get("ip_address", "unknown")
                    print(f"      - {hostname} ({ip})")
                if len(assets) > 5:
                    print(f"      ... and {len(assets) - 5} more")
            
            elif status == "failed":
                message = step_result.get("message", "")
                stderr = step_result.get("stderr", "")
                error_msg = message or stderr or "Unknown error"
                print(f"      Error: {error_msg[:100]}")
            
            elif status == "success":
                stdout = step_result.get("stdout", "")
                if stdout:
                    print(f"      Output: {stdout[:100]}")
        
        # Display timing
        duration = result.get("duration_seconds", 0)
        print(f"\n⏱️  Total Duration: {duration:.2f} seconds")
        
        return result
        
    except httpx.HTTPError as e:
        print(f"❌ HTTP Error: {e}")
        return None
    except Exception as e:
        print(f"❌ Error: {e}")
        return None

def demo_1_simple_asset_query():
    """Demo 1: Simple asset query"""
    print_section("DEMO 1: Simple Asset Query")
    
    print("""
This demo shows basic asset discovery using the asset-query tool.
The query finds all Windows 10 assets with the 'win10' tag.
    """)
    
    steps = [
        {
            "tool": "asset-query",
            "inputs": {
                "tags": ["win10"],
                "limit": 10
            }
        }
    ]
    
    execute_plan(
        "Simple Asset Query",
        steps,
        "Find all Windows 10 assets"
    )

def demo_2_template_variables():
    """Demo 2: Template variable resolution"""
    print_section("DEMO 2: Template Variable Resolution")
    
    print("""
This demo shows template variable resolution in action:
1. Asset-query finds Windows 10 hosts
2. Variables are extracted: assets, hostnames, ip_addresses, asset_count
3. Second step uses {{asset_count}} template variable
    """)
    
    steps = [
        {
            "tool": "asset-query",
            "inputs": {
                "tags": ["win10"],
                "limit": 10
            }
        },
        {
            "tool": "ping",
            "inputs": {
                "target_host": "localhost",
                "count": 1
            }
        }
    ]
    
    execute_plan(
        "Template Variable Resolution",
        steps,
        "Query assets and use template variables"
    )

def demo_3_loop_execution():
    """Demo 3: Loop execution over multiple targets"""
    print_section("DEMO 3: Loop Execution Over Multiple Targets")
    
    print("""
This demo shows automatic loop execution:
1. Asset-query finds Windows 10 hosts
2. System detects template variable {{hostname}} in target_hosts
3. Single Invoke-Command step expands to N iterations (one per asset)
4. Each iteration executes on a different host

NOTE: This will fail without valid credentials, but demonstrates loop expansion.
    """)
    
    steps = [
        {
            "tool": "asset-query",
            "inputs": {
                "tags": ["win10"],
                "limit": 5
            }
        },
        {
            "tool": "Invoke-Command",
            "inputs": {
                "target_hosts": ["{{hostname}}"],
                "command": "Get-ComputerInfo | Select-Object CsName, OsName, OsVersion"
            }
        }
    ]
    
    execute_plan(
        "Loop Execution Demo",
        steps,
        "Execute PowerShell command on multiple Windows hosts"
    )

def demo_4_complex_workflow():
    """Demo 4: Complex multi-step workflow"""
    print_section("DEMO 4: Complex Multi-Step Workflow")
    
    print("""
This demo shows a complex workflow with multiple steps:
1. Query production Windows servers
2. Check connectivity to each server (loop)
3. Get disk space information (loop)
4. Get running services (loop)

This demonstrates:
- Multiple asset queries
- Multiple loop executions
- Sequential step dependencies
    """)
    
    steps = [
        {
            "tool": "asset-query",
            "inputs": {
                "tags": ["win10"],
                "limit": 3
            }
        },
        {
            "tool": "ping",
            "inputs": {
                "target_hosts": ["{{hostname}}"],
                "count": 2
            }
        },
        {
            "tool": "Invoke-Command",
            "inputs": {
                "target_hosts": ["{{hostname}}"],
                "command": "Get-Volume C | Select-Object DriveLetter, Size, SizeRemaining"
            }
        }
    ]
    
    execute_plan(
        "Complex Workflow Demo",
        steps,
        "Multi-step workflow with multiple loop executions"
    )

def demo_5_real_world_scenario():
    """Demo 5: Real-world automation scenario"""
    print_section("DEMO 5: Real-World Automation Scenario")
    
    print("""
Real-World Scenario: Windows Server Health Check

This workflow performs a comprehensive health check on Windows servers:
1. Discover all Windows 10 test servers
2. Check network connectivity
3. Get system information
4. Check disk space
5. List critical services

This is a typical automation task that would be run on a schedule.
    """)
    
    steps = [
        {
            "tool": "asset-query",
            "inputs": {
                "tags": ["win10"],
                "os_type": "Windows",
                "limit": 10
            }
        },
        {
            "tool": "ping",
            "inputs": {
                "target_hosts": ["{{hostname}}"],
                "count": 4
            }
        },
        {
            "tool": "Invoke-Command",
            "inputs": {
                "target_hosts": ["{{hostname}}"],
                "command": "Get-ComputerInfo | Select-Object CsName, WindowsVersion, OsArchitecture, TotalPhysicalMemory"
            }
        },
        {
            "tool": "Invoke-Command",
            "inputs": {
                "target_hosts": ["{{hostname}}"],
                "command": "Get-Volume | Where-Object {$_.DriveLetter} | Select-Object DriveLetter, FileSystem, Size, SizeRemaining"
            }
        },
        {
            "tool": "Invoke-Command",
            "inputs": {
                "target_hosts": ["{{hostname}}"],
                "command": "Get-Service | Where-Object {$_.Status -eq 'Running'} | Select-Object Name, DisplayName, Status"
            }
        }
    ]
    
    execute_plan(
        "Windows Server Health Check",
        steps,
        "Comprehensive health check across all Windows servers"
    )

def check_services():
    """Check if services are running"""
    print_section("Service Health Check")
    
    try:
        # Check automation service
        response = httpx.get(f"{AUTOMATION_SERVICE}/health", timeout=5.0)
        if response.status_code == 200:
            print("✅ Automation Service: Healthy")
        else:
            print(f"⚠️  Automation Service: Status {response.status_code}")
    except Exception as e:
        print(f"❌ Automation Service: Not reachable - {e}")
        return False
    
    try:
        # Check asset service
        response = httpx.get(f"{ASSET_SERVICE}/health", timeout=5.0)
        if response.status_code == 200:
            print("✅ Asset Service: Healthy")
        else:
            print(f"⚠️  Asset Service: Status {response.status_code}")
    except Exception as e:
        print(f"❌ Asset Service: Not reachable - {e}")
        return False
    
    return True

def main():
    """Run all demos"""
    print("\n" + "=" * 80)
    print("🎬 MULTI-STEP EXECUTION SYSTEM DEMO")
    print("=" * 80)
    print("""
This demo showcases the OpsConductor multi-step execution system with:
- Template variable resolution
- Loop execution over multiple targets
- Asset discovery and integration
- Real-world automation scenarios

The demos will execute against the running services.
Some demos may show failures (e.g., PowerShell without credentials),
but they demonstrate the system's capabilities.
    """)
    
    # Check services
    if not check_services():
        print("\n❌ Services are not healthy. Please start the services first.")
        print("   Run: docker compose up -d")
        return
    
    # Run demos
    demos = [
        ("1", "Simple Asset Query", demo_1_simple_asset_query),
        ("2", "Template Variable Resolution", demo_2_template_variables),
        ("3", "Loop Execution", demo_3_loop_execution),
        ("4", "Complex Workflow", demo_4_complex_workflow),
        ("5", "Real-World Scenario", demo_5_real_world_scenario),
    ]
    
    print("\n" + "=" * 80)
    print("Available Demos:")
    for num, name, _ in demos:
        print(f"  {num}. {name}")
    print("  A. Run All Demos")
    print("  Q. Quit")
    print("=" * 80)
    
    choice = input("\nSelect demo (1-5, A, or Q): ").strip().upper()
    
    if choice == "Q":
        print("\n👋 Goodbye!")
        return
    elif choice == "A":
        for num, name, demo_func in demos:
            demo_func()
            time.sleep(2)  # Pause between demos
    elif choice in ["1", "2", "3", "4", "5"]:
        demo_func = demos[int(choice) - 1][2]
        demo_func()
    else:
        print("\n❌ Invalid choice")
        return
    
    print("\n" + "=" * 80)
    print("🎉 Demo Complete!")
    print("=" * 80)
    print("""
Next Steps:
1. Check logs: docker logs opsconductor-automation --tail 100
2. Look for loop execution: docker logs opsconductor-automation | grep -E '(Loop|🔁)'
3. Review documentation: MULTISTEP_EXECUTION.md
4. Run tests: python3 test_multistep_execution.py
    """)

if __name__ == "__main__":
    main()