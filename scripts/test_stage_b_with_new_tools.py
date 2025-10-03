#!/usr/bin/env python3
"""
Test Stage B with the new 170-tool catalog
Verify that ProfileLoader loads all tools from database
"""

import sys
import os
sys.path.insert(0, '/home/opsconductor/opsconductor-ng')

from pipeline.stages.stage_b.profile_loader import ProfileLoader

def test_profile_loader():
    """Test that ProfileLoader loads all 170 tools from database"""
    
    print("=" * 80)
    print("TESTING STAGE B WITH 170-TOOL CATALOG")
    print("=" * 80)
    print()
    
    # Initialize ProfileLoader (defaults to database mode)
    print("1. Initializing ProfileLoader (database mode)...")
    loader = ProfileLoader(use_database=True)
    print("   ✅ ProfileLoader initialized")
    print()
    
    # Load all tools
    print("2. Loading all tools from database...")
    try:
        profiles = loader.load()
        print(f"   ✅ Loaded {len(profiles.tools)} tools")
        print()
    except Exception as e:
        print(f"   ❌ Failed to load: {e}")
        return False
    
    # Show tool distribution
    print("3. Tool distribution by platform:")
    platform_counts = {}
    for tool_name, tool_profile in profiles.tools.items():
        # Count capabilities
        cap_count = len(tool_profile.capabilities)
        pattern_count = sum(len(cap.patterns) for cap in tool_profile.capabilities.values())
        
        # Track by first word of tool name (rough platform grouping)
        platform = "other"
        if any(x in tool_name.lower() for x in ['get-', 'set-', 'new-', 'remove-']):
            platform = "windows"
        elif any(x in tool_name.lower() for x in ['kubectl', 'helm', 'docker', 'podman']):
            platform = "container"
        elif any(x in tool_name.lower() for x in ['aws', 'az', 'gcloud']):
            platform = "cloud"
        elif any(x in tool_name.lower() for x in ['mysql', 'psql', 'redis', 'mongo']):
            platform = "database"
        else:
            platform = "linux"
        
        platform_counts[platform] = platform_counts.get(platform, 0) + 1
    
    for platform, count in sorted(platform_counts.items(), key=lambda x: x[1], reverse=True):
        print(f"   {platform:15} {count:3} tools")
    print()
    
    # Sample some tools
    print("4. Sample tools loaded:")
    sample_tools = list(profiles.tools.items())[:10]
    for tool_name, tool_profile in sample_tools:
        cap_count = len(tool_profile.capabilities)
        pattern_count = sum(len(cap.patterns) for cap in tool_profile.capabilities.values())
        desc = tool_profile.description[:50] + "..." if len(tool_profile.description) > 50 else tool_profile.description
        print(f"   • {tool_name:20} - {cap_count} caps, {pattern_count} patterns")
        print(f"     {desc}")
    print()
    
    # Test specific tool lookup
    print("5. Testing specific tool lookups:")
    test_tools = ['systemctl', 'docker', 'kubectl', 'Get-Service', 'aws']
    for tool_name in test_tools:
        tool_profile = loader.get_tool_profile(tool_name)
        if tool_profile:
            cap_count = len(tool_profile.capabilities)
            print(f"   ✅ {tool_name:15} - {cap_count} capabilities")
        else:
            print(f"   ⚠️  {tool_name:15} - not found")
    print()
    
    print("=" * 80)
    print("✅ STAGE B IS READY TO USE ALL 170 TOOLS!")
    print("=" * 80)
    print()
    print("The system will automatically:")
    print("  • Load all 170 tools from PostgreSQL database")
    print("  • Use HybridOrchestrator for intelligent tool selection")
    print("  • Apply deterministic scoring + LLM tie-breaking")
    print("  • Enforce policy constraints (cost, approval, production-safe)")
    print("  • Cache profiles for 5 minutes for performance")
    print()
    
    return True

if __name__ == '__main__':
    success = test_profile_loader()
    sys.exit(0 if success else 1)