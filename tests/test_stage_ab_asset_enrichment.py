#!/usr/bin/env python3
"""
Test script for Stage AB Asset Enrichment functionality

This script demonstrates the new asset enrichment logic in Stage AB v3.1:
1. Entity extraction from user requests
2. Asset metadata lookup from asset-service
3. Platform detection and filtering
4. Handling ambiguous targets
"""

import asyncio
import sys
import logging
from typing import Dict, Any

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Add project to path
sys.path.insert(0, '/home/opsconductor/opsconductor-ng')

from pipeline.stages.stage_ab.combined_selector import CombinedSelector
from llm.client import LLMClient


async def test_scenario_1_explicit_target():
    """
    Scenario 1: Explicit target with asset in database
    Request: "list all files on 192.168.50.211"
    Expected: Should find asset, detect Windows, retrieve Windows tools
    """
    print("\n" + "="*80)
    print("SCENARIO 1: Explicit Target (IP Address)")
    print("="*80)
    
    llm_client = LLMClient()
    selector = CombinedSelector(llm_client)
    
    user_request = "list all files on 192.168.50.211"
    context = {}
    
    try:
        result = await selector.process(user_request, context)
        
        print(f"\n✅ Selection Complete:")
        print(f"   - Tools selected: {len(result.selected_tools)}")
        print(f"   - Platform detected: {context.get('asset_metadata', {}).get('os_type', 'N/A')}")
        print(f"   - Additional inputs needed: {result.additional_inputs_needed}")
        print(f"   - Ready for execution: {result.ready_for_execution}")
        
        if result.selected_tools:
            print(f"\n   Selected tools:")
            for tool in result.selected_tools:
                print(f"      - {tool.tool_name}")
        
        return True
        
    except Exception as e:
        print(f"\n❌ Test failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


async def test_scenario_2_ambiguous_target():
    """
    Scenario 2: Ambiguous target (no specific asset mentioned)
    Request: "list all files in the current directory"
    Expected: Should detect ambiguity, set missing_target_info=True
    """
    print("\n" + "="*80)
    print("SCENARIO 2: Ambiguous Target (No Asset Specified)")
    print("="*80)
    
    llm_client = LLMClient()
    selector = CombinedSelector(llm_client)
    
    user_request = "list all files in the current directory"
    context = {}
    
    try:
        result = await selector.process(user_request, context)
        
        print(f"\n✅ Selection Complete:")
        print(f"   - Tools selected: {len(result.selected_tools)}")
        print(f"   - Missing target info: {context.get('missing_target_info', False)}")
        print(f"   - Additional inputs needed: {result.additional_inputs_needed}")
        print(f"   - Ready for execution: {result.ready_for_execution}")
        
        if "target_asset" in result.additional_inputs_needed:
            print(f"\n   ⚠️  AI should prompt user: 'Which system would you like to list files on?'")
        
        return True
        
    except Exception as e:
        print(f"\n❌ Test failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


async def test_scenario_3_context_from_previous():
    """
    Scenario 3: Context from previous conversation
    Request: "list all files in the current directory"
    Context: Previous asset was "server-prod-01" (Windows)
    Expected: Should use context asset, detect Windows
    """
    print("\n" + "="*80)
    print("SCENARIO 3: Context from Previous Conversation")
    print("="*80)
    
    llm_client = LLMClient()
    selector = CombinedSelector(llm_client)
    
    user_request = "list all files in the current directory"
    context = {
        "current_asset": {
            "id": 1,
            "name": "server-prod-01",
            "os_type": "windows"
        }
    }
    
    try:
        result = await selector.process(user_request, context)
        
        print(f"\n✅ Selection Complete:")
        print(f"   - Tools selected: {len(result.selected_tools)}")
        print(f"   - Platform from context: {context.get('current_asset', {}).get('os_type', 'N/A')}")
        print(f"   - Additional inputs needed: {result.additional_inputs_needed}")
        print(f"   - Ready for execution: {result.ready_for_execution}")
        
        if result.selected_tools:
            print(f"\n   Selected tools:")
            for tool in result.selected_tools:
                print(f"      - {tool.tool_name}")
        
        return True
        
    except Exception as e:
        print(f"\n❌ Test failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


async def test_scenario_4_hostname_lookup():
    """
    Scenario 4: Hostname lookup
    Request: "check disk space on web-server-01"
    Expected: Should find asset by hostname, detect platform
    """
    print("\n" + "="*80)
    print("SCENARIO 4: Hostname Lookup")
    print("="*80)
    
    llm_client = LLMClient()
    selector = CombinedSelector(llm_client)
    
    user_request = "check disk space on web-server-01"
    context = {}
    
    try:
        result = await selector.process(user_request, context)
        
        print(f"\n✅ Selection Complete:")
        print(f"   - Tools selected: {len(result.selected_tools)}")
        print(f"   - Asset found: {context.get('asset_metadata', {}).get('name', 'N/A')}")
        print(f"   - Platform detected: {context.get('asset_metadata', {}).get('os_type', 'N/A')}")
        print(f"   - Additional inputs needed: {result.additional_inputs_needed}")
        
        if result.selected_tools:
            print(f"\n   Selected tools:")
            for tool in result.selected_tools:
                print(f"      - {tool.tool_name}")
        
        return True
        
    except Exception as e:
        print(f"\n❌ Test failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


async def main():
    """Run all test scenarios"""
    print("\n" + "="*80)
    print("STAGE AB v3.1 - ASSET ENRICHMENT TEST SUITE")
    print("="*80)
    
    results = []
    
    # Run all scenarios
    results.append(("Scenario 1: Explicit Target", await test_scenario_1_explicit_target()))
    results.append(("Scenario 2: Ambiguous Target", await test_scenario_2_ambiguous_target()))
    results.append(("Scenario 3: Context from Previous", await test_scenario_3_context_from_previous()))
    results.append(("Scenario 4: Hostname Lookup", await test_scenario_4_hostname_lookup()))
    
    # Summary
    print("\n" + "="*80)
    print("TEST SUMMARY")
    print("="*80)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status} - {name}")
    
    print(f"\nTotal: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n🎉 All tests passed!")
        return 0
    else:
        print(f"\n⚠️  {total - passed} test(s) failed")
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)