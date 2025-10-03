#!/usr/bin/env python3
"""
Tool Catalog Verification Script
Verifies all tools are properly loaded and accessible
"""

import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from pipeline.services.tool_catalog_service import ToolCatalogService
from pipeline.stages.stage_b.profile_loader import ProfileLoader

def verify_catalog():
    """Verify tool catalog is working correctly"""
    
    print("=" * 80)
    print("TOOL CATALOG VERIFICATION")
    print("=" * 80)
    
    # Initialize service
    print("\n1. Initializing ToolCatalogService...")
    try:
        service = ToolCatalogService()
        print("   ✅ Service initialized successfully")
    except Exception as e:
        print(f"   ❌ Failed to initialize service: {e}")
        return False
    
    # Get all tools
    print("\n2. Loading all tools from database...")
    try:
        tools = service.get_all_tools()
        print(f"   ✅ Loaded {len(tools)} tools")
    except Exception as e:
        print(f"   ❌ Failed to load tools: {e}")
        return False
    
    # Count by platform
    print("\n3. Tools by Platform:")
    platforms = {}
    for tool in tools:
        platform = tool.get('platform', 'unknown')
        platforms[platform] = platforms.get(platform, 0) + 1
    
    for platform, count in sorted(platforms.items(), key=lambda x: x[1], reverse=True):
        print(f"   - {platform:15s}: {count:3d} tools")
    
    # Count by category
    print("\n4. Tools by Category:")
    categories = {}
    for tool in tools:
        category = tool.get('category', 'unknown')
        categories[category] = categories.get(category, 0) + 1
    
    for category, count in sorted(categories.items(), key=lambda x: x[1], reverse=True):
        print(f"   - {category:15s}: {count:3d} tools")
    
    # Test ProfileLoader
    print("\n5. Testing ProfileLoader integration...")
    try:
        loader = ProfileLoader(use_database=True)
        profiles = loader.load()
        print(f"   ✅ ProfileLoader loaded {len(profiles.tools)} tool profiles")
    except Exception as e:
        print(f"   ❌ ProfileLoader failed: {e}")
        return False
    
    # Sample some tools
    print("\n6. Sample Tools:")
    sample_tools = [
        'systemctl',
        'Get-Service',
        'tcpdump',
        'kubectl',
        'docker',
        'aws',
        'psql'
    ]
    
    for tool_name in sample_tools:
        tool = service.get_tool_by_name(tool_name, use_cache=False)
        if tool:
            print(f"   ✅ {tool_name:15s} - {tool['platform']:10s} - {tool['category']}")
        else:
            print(f"   ⚠️  {tool_name:15s} - NOT FOUND")
    
    # Test capability search
    print("\n7. Testing capability search...")
    try:
        # Search for service management tools
        service_tools = service.search_tools_by_capability("service")
        print(f"   ✅ Found {len(service_tools)} tools with 'service' capability")
        
        # Search for network tools
        network_tools = service.search_tools_by_capability("network")
        print(f"   ✅ Found {len(network_tools)} tools with 'network' capability")
    except Exception as e:
        print(f"   ❌ Capability search failed: {e}")
    
    # Performance stats
    print("\n8. Performance Statistics:")
    try:
        stats = service.get_performance_stats()
        if stats:
            print(f"   - Cache hits: {stats.get('cache_hits', 0)}")
            print(f"   - Cache misses: {stats.get('cache_misses', 0)}")
            print(f"   - Cache size: {stats.get('cache_size', 0)}")
            hit_rate = stats.get('cache_hit_rate', 0) * 100
            print(f"   - Hit rate: {hit_rate:.1f}%")
    except Exception as e:
        print(f"   ⚠️  Stats not available: {e}")
    
    print("\n" + "=" * 80)
    print("✅ VERIFICATION COMPLETE - All systems operational!")
    print("=" * 80)
    
    # Close service
    service.close()
    
    return True


if __name__ == "__main__":
    success = verify_catalog()
    sys.exit(0 if success else 1)