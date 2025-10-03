#!/usr/bin/env python3
"""
Integration Test for Tool Catalog System
Tests the full pipeline: Schema → Import → Query
"""

import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from pipeline.services.tool_catalog_service import ToolCatalogService

def test_integration():
    """Test the full tool catalog integration"""
    
    print("=" * 60)
    print("TOOL CATALOG INTEGRATION TEST")
    print("=" * 60)
    
    try:
        # Initialize service
        print("\n1. Initializing ToolCatalogService...")
        service = ToolCatalogService()
        print("   ✓ Service initialized")
        
        # Test health check
        print("\n2. Testing health check...")
        if service.health_check():
            print("   ✓ Health check passed")
        else:
            print("   ✗ Health check failed")
            return False
        
        # Get statistics
        print("\n3. Getting catalog statistics...")
        stats = service.get_stats()
        print(f"   ✓ Total tools: {stats['total_tools']}")
        print(f"   ✓ Total capabilities: {stats['total_capabilities']}")
        print(f"   ✓ Total patterns: {stats['total_patterns']}")
        
        if stats['total_tools'] < 2:
            print("   ✗ Expected at least 2 tools")
            return False
        
        # Test get tool by name
        print("\n4. Testing get_tool_by_name('grep')...")
        grep_tool = service.get_tool_by_name('grep')
        if grep_tool:
            print(f"   ✓ Found tool: {grep_tool['tool_name']} v{grep_tool['version']}")
            print(f"   ✓ Platform: {grep_tool['platform']}")
            print(f"   ✓ Category: {grep_tool['category']}")
        else:
            print("   ✗ Tool 'grep' not found")
            return False
        
        # Test get tools by capability
        print("\n5. Testing get_tools_by_capability('text_search')...")
        text_search_tools = service.get_tools_by_capability('text_search')
        if text_search_tools:
            print(f"   ✓ Found {len(text_search_tools)} tool(s) with text_search capability")
            for tool in text_search_tools:
                print(f"     - {tool['tool_name']}")
                
                # Check capabilities structure
                for cap_name, cap_data in tool['capabilities'].items():
                    print(f"       Capability: {cap_name}")
                    for pattern in cap_data['patterns']:
                        print(f"         Pattern: {pattern['pattern_name']}")
                        
                        # Verify expected_outputs field exists
                        if 'expected_outputs' in pattern:
                            print(f"           ✓ expected_outputs field present ({len(pattern['expected_outputs'])} outputs)")
                        else:
                            print("           ✗ expected_outputs field missing")
                            return False
        else:
            print("   ✗ No tools found with text_search capability")
            return False
        
        # Test get all tools
        print("\n6. Testing get_all_tools()...")
        all_tools = service.get_all_tools()
        print(f"   ✓ Retrieved {len(all_tools)} tool(s)")
        for tool in all_tools:
            print(f"     - {tool['tool_name']} ({tool['platform']}/{tool['category']})")
        
        # Test platform filtering
        print("\n7. Testing platform filtering...")
        linux_tools = service.get_tools_by_capability('text_search', platform='linux')
        windows_tools = service.get_tools_by_capability('windows_automation', platform='windows')
        print(f"   ✓ Linux tools with text_search: {len(linux_tools)}")
        print(f"   ✓ Windows tools with windows_automation: {len(windows_tools)}")
        
        # Close service
        print("\n8. Closing service...")
        service.close()
        print("   ✓ Service closed")
        
        print("\n" + "=" * 60)
        print("✅ ALL TESTS PASSED")
        print("=" * 60)
        return True
        
    except Exception as e:
        print(f"\n❌ TEST FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_integration()
    sys.exit(0 if success else 1)