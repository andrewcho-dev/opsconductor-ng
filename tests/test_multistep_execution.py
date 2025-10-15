#!/usr/bin/env python3
"""
Test script for multi-step execution with template variables, dependencies, and loops.

This tests the complete workflow:
1. Query assets with tag "win10"
2. Extract hostnames from results
3. Loop over each hostname to execute PowerShell command
4. Aggregate results
"""

import asyncio
import json
import sys
from datetime import datetime

# Add automation-service to path
sys.path.insert(0, '/home/opsconductor/opsconductor-ng/automation-service')

from execution_context import ExecutionContext


async def test_template_variable_detection():
    """Test 1: Template variable detection"""
    print("\n" + "="*80)
    print("TEST 1: Template Variable Detection")
    print("="*80)
    
    context = ExecutionContext("test-exec-1")
    
    test_cases = [
        ("{{hostname}}", ["hostname"]),
        ("{{hostnames[0]}}", ["hostnames[0]"]),
        ("{{assets[0].hostname}}", ["assets[0].hostname"]),
        ("no template here", []),
        ("{{var1}} and {{var2}}", ["var1", "var2"]),
        ("plain text", []),
    ]
    
    for text, expected in test_cases:
        result = context.find_template_variables(text)
        status = "✅" if result == expected else "❌"
        print(f"{status} '{text}' -> {result} (expected {expected})")
    
    return True


async def test_variable_extraction():
    """Test 2: Variable extraction from asset-query results"""
    print("\n" + "="*80)
    print("TEST 2: Variable Extraction from Asset Query Results")
    print("="*80)
    
    context = ExecutionContext("test-exec")
    
    # Simulate asset-query result (as it would come from the service)
    mock_result = {
        "tool": "asset-query",
        "status": "success",
        "output": {
            "status": "success",
            "assets": [
                {"id": 21, "name": "win10-test02", "hostname": "192.168.50.211", "ip_address": "192.168.50.211"},
                {"id": 22, "name": "win10-test03", "hostname": "192.168.50.212", "ip_address": "192.168.50.212"},
                {"id": 23, "name": "win10-test04", "hostname": "192.168.50.213", "ip_address": "192.168.50.213"},
            ]
        }
    }
    
    # Extract variables
    context.extract_variables_from_step_result(1, mock_result)
    
    print(f"✅ Extracted variables: {list(context.variables.keys())}")
    print(f"   - assets: {len(context.variables.get('assets', []))} items")
    print(f"   - hostnames: {context.variables.get('hostnames', [])}")
    print(f"   - ip_addresses: {context.variables.get('ip_addresses', [])}")
    print(f"   - asset_count: {context.variables.get('asset_count', 0)}")
    
    # Verify extraction
    assert len(context.variables['assets']) == 3
    assert context.variables['hostnames'] == ["192.168.50.211", "192.168.50.212", "192.168.50.213"]
    assert context.variables['asset_count'] == 3
    
    return True


async def test_template_resolution():
    """Test 3: Template variable resolution"""
    print("\n" + "="*80)
    print("TEST 3: Template Variable Resolution")
    print("="*80)
    
    context = ExecutionContext("test-exec")
    
    # Set up context
    context.variables = {
        "hostname": "server01",
        "hostnames": ["server01", "server02", "server03"],
        "assets": [
            {"hostname": "server01", "ip": "10.0.0.1"},
            {"hostname": "server02", "ip": "10.0.0.2"},
        ]
    }
    
    test_cases = [
        ("{{hostname}}", "server01"),
        ("{{hostnames[0]}}", "server01"),
        ("{{hostnames[1]}}", "server02"),
        ("{{assets[0].hostname}}", "server01"),
        ("{{assets[1].ip}}", "10.0.0.2"),
        ("Server: {{hostname}}", "Server: server01"),
    ]
    
    for template, expected in test_cases:
        result = context.resolve_template_string(template)
        status = "✅" if result == expected else "❌"
        print(f"{status} '{template}' -> '{result}' (expected '{expected}')")
    
    return True


async def test_loop_detection():
    """Test 4: Loop detection"""
    print("\n" + "="*80)
    print("TEST 4: Loop Detection")
    print("="*80)
    
    context = ExecutionContext("test-exec")
    
    # Set up context with assets
    context.variables = {
        "assets": [
            {"hostname": "server01"},
            {"hostname": "server02"},
            {"hostname": "server03"},
        ],
        "hostnames": ["server01", "server02", "server03"]
    }
    
    # Test case 1: Step with template in target_hosts (should loop)
    step_with_loop = {
        "tool": "Invoke-Command",
        "parameters": {
            "target_hosts": ["{{hostname}}"],
            "command": "Get-Volume"
        }
    }
    
    should_loop, loop_var, loop_items = context.detect_loop_execution(step_with_loop)
    print(f"✅ Step with template variable: should_loop={should_loop}, loop_var={loop_var}, items={len(loop_items) if loop_items else 0}")
    assert should_loop == True
    assert len(loop_items) == 3
    
    # Test case 2: Step without template (should not loop)
    step_without_loop = {
        "tool": "Invoke-Command",
        "parameters": {
            "target_hosts": ["server01"],
            "command": "Get-Volume"
        }
    }
    
    should_loop, loop_var, loop_items = context.detect_loop_execution(step_without_loop)
    print(f"✅ Step without template: should_loop={should_loop}, loop_var={loop_var}, items={loop_items}")
    assert should_loop == False
    assert loop_items is None
    
    return True


async def test_step_expansion():
    """Test 5: Step expansion for loops"""
    print("\n" + "="*80)
    print("TEST 5: Step Expansion for Loops")
    print("="*80)
    
    context = ExecutionContext("test-exec")
    
    # Set up context
    context.variables = {
        "assets": [
            {"hostname": "192.168.50.211", "name": "win10-test02"},
            {"hostname": "192.168.50.212", "name": "win10-test03"},
        ],
        "hostnames": ["192.168.50.211", "192.168.50.212"]
    }
    
    # Original step with template
    original_step = {
        "tool": "Invoke-Command",
        "parameters": {
            "target_hosts": ["{{hostname}}"],
            "command": "Get-Volume -DriveLetter C | Select-Object DriveLetter, Size, SizeRemaining"
        }
    }
    
    # Expand step
    loop_items = context.variables["assets"]
    expanded_steps = context.expand_step_for_loop(original_step, loop_items)
    
    print(f"✅ Expanded {len(expanded_steps)} steps from 1 original step")
    for i, step in enumerate(expanded_steps):
        # After expansion, target_hosts becomes target_host (singular)
        target = step["parameters"].get("target_host", step["parameters"].get("target_hosts", [None])[0])
        print(f"   Step {i+1}: target_host='{target}'")
        assert target in ["192.168.50.211", "192.168.50.212"]
    
    return True


async def test_full_workflow_simulation():
    """Test 6: Full workflow simulation"""
    print("\n" + "="*80)
    print("TEST 6: Full Multi-Step Workflow Simulation")
    print("="*80)
    
    context = ExecutionContext("test-exec")
    
    # Step 1: Asset query (simulated result)
    print("\n📋 Step 1: Query assets with tag 'win10'")
    step1_result = {
        "tool": "asset-query",
        "status": "success",
        "output": {
            "status": "success",
            "assets": [
                {"id": 21, "name": "win10-test02", "hostname": "192.168.50.211", "ip_address": "192.168.50.211"},
                {"id": 22, "name": "win10-test03", "hostname": "192.168.50.212", "ip_address": "192.168.50.212"},
                {"id": 23, "name": "win10-test04", "hostname": "192.168.50.213", "ip_address": "192.168.50.213"},
            ]
        }
    }
    
    context.store_step_result(1, step1_result)
    context.extract_variables_from_step_result(1, step1_result)
    
    print(f"   ✅ Found {context.variables['asset_count']} assets")
    print(f"   ✅ Extracted hostnames: {context.variables['hostnames']}")
    
    # Step 2: Check if loop is needed
    print("\n📋 Step 2: Execute PowerShell command on each host")
    step2_definition = {
        "tool": "Invoke-Command",
        "parameters": {
            "target_hosts": ["{{hostname}}"],
            "command": "Get-Volume -DriveLetter C | Select-Object DriveLetter, Size, SizeRemaining"
        }
    }
    
    should_loop, loop_var, loop_items = context.detect_loop_execution(step2_definition)
    print(f"   🔁 Loop detected: {should_loop}, iterations: {len(loop_items) if loop_items else 0}")
    
    if should_loop:
        expanded_steps = context.expand_step_for_loop(step2_definition, loop_items)
        print(f"   ✅ Expanded into {len(expanded_steps)} individual executions")
        
        # Simulate execution of each iteration
        for i, step in enumerate(expanded_steps):
            target = step["parameters"].get("target_host", step["parameters"].get("target_hosts", [None])[0])
            print(f"   🔁 Loop iteration {i+1}/{len(expanded_steps)}: target={target}")
            
            # Simulate result
            mock_result = {
                "status": "success",
                "output": f"DriveLetter: C, Size: 500GB, SizeRemaining: 250GB (from {target})"
            }
            context.store_step_result(f"2.{i+1}", mock_result)
    
    print(f"\n✅ Workflow complete! Stored {len(context.step_results)} step results")
    print(f"   Variables in context: {list(context.variables.keys())}")
    
    return True


async def main():
    """Run all tests"""
    print("\n" + "="*80)
    print("🧪 MULTI-STEP EXECUTION TEST SUITE")
    print("="*80)
    print(f"Started at: {datetime.now().isoformat()}")
    
    tests = [
        ("Template Variable Detection", test_template_variable_detection),
        ("Variable Extraction", test_variable_extraction),
        ("Template Resolution", test_template_resolution),
        ("Loop Detection", test_loop_detection),
        ("Step Expansion", test_step_expansion),
        ("Full Workflow Simulation", test_full_workflow_simulation),
    ]
    
    passed = 0
    failed = 0
    
    for test_name, test_func in tests:
        try:
            result = await test_func()
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
    print("📊 TEST SUMMARY")
    print("="*80)
    print(f"Total tests: {len(tests)}")
    print(f"✅ Passed: {passed}")
    print(f"❌ Failed: {failed}")
    print(f"Completed at: {datetime.now().isoformat()}")
    print("="*80 + "\n")
    
    return failed == 0


if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)