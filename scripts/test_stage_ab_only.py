#!/usr/bin/env python3
"""
Test Stage AB (Combined Selector) in isolation
"""

import asyncio
import os
import sys
from dotenv import load_dotenv

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Load environment variables
load_dotenv()

async def test_stage_ab():
    """Test Stage AB with database connectivity"""
    from llm.factory import create_llm_client
    from pipeline.stages.stage_ab.combined_selector import CombinedSelector
    from pipeline.services.tool_catalog_service import ToolCatalogService
    
    print("\n" + "="*80)
    print("STAGE AB ISOLATED TEST")
    print("="*80)
    
    # Create LLM client
    print("\n1. Creating LLM client...")
    llm_client = create_llm_client()
    await llm_client.connect()
    print("✅ LLM client connected")
    
    # Create tool catalog service
    print("\n2. Creating tool catalog service...")
    tool_catalog = ToolCatalogService()
    print("✅ Tool catalog service created")
    
    # Load tools from database
    print("\n3. Loading tools from database...")
    try:
        tools = tool_catalog.get_all_tools_with_structure()
        print(f"✅ Loaded {len(tools)} tools from database")
        
        # Show first 3 tools
        print("\n📦 Sample tools:")
        for i, tool in enumerate(tools[:3]):
            print(f"   {i+1}. {tool['tool_name']}")
            print(f"      Platform: {tool['platform']}, Category: {tool['category']}")
            print(f"      Capabilities: {len(tool.get('capabilities', {}))}")
    except Exception as e:
        print(f"❌ Failed to load tools: {e}")
        return False
    
    # Create Stage AB
    print("\n4. Creating Stage AB (Combined Selector)...")
    stage_ab = CombinedSelector(llm_client, tool_catalog)
    print("✅ Stage AB created")
    
    # Test with a simple request
    print("\n5. Testing Stage AB with request...")
    test_request = "Show me all running Docker containers"
    print(f"   Request: {test_request}")
    
    try:
        result = await stage_ab.process(test_request, context={})
        
        print(f"\n✅ Stage AB completed!")
        print(f"   Selected Tools: {len(result.selected_tools)}")
        if result.selected_tools:
            for tool in result.selected_tools:
                print(f"      - {tool.tool_name}")
        print(f"   Risk Level: {result.policy.risk_level}")
        print(f"   Confidence: {result.selection_confidence:.2f}")
        print(f"   Next Stage: {result.next_stage}")
        
        return True
        
    except Exception as e:
        print(f"❌ Stage AB failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = asyncio.run(test_stage_ab())
    sys.exit(0 if success else 1)