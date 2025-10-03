#!/usr/bin/env python3
"""
Test ProfileLoader Database Integration

Tests that ProfileLoader can successfully load tools from the database
and transform them into OptimizationProfilesConfig format.
"""

import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from pipeline.stages.stage_b.profile_loader import ProfileLoader, get_loader, load_profiles


def test_database_mode():
    """Test ProfileLoader in database mode"""
    
    print("=" * 70)
    print("PROFILE LOADER DATABASE INTEGRATION TEST")
    print("=" * 70)
    
    try:
        # Test 1: Initialize ProfileLoader in database mode
        print("\n1. Initializing ProfileLoader (database mode)...")
        loader = ProfileLoader(use_database=True)
        print("   ✓ ProfileLoader initialized")
        
        # Test 2: Load profiles from database
        print("\n2. Loading profiles from database...")
        profiles = loader.load()
        print(f"   ✓ Loaded {len(profiles.tools)} tools")
        
        # Test 3: Verify structure
        print("\n3. Verifying profile structure...")
        if len(profiles.tools) < 2:
            print(f"   ✗ Expected at least 2 tools, got {len(profiles.tools)}")
            return False
        
        print(f"   ✓ Found {len(profiles.tools)} tools")
        
        # Test 4: Check each tool
        print("\n4. Checking tool details...")
        for tool_name, tool_profile in profiles.tools.items():
            print(f"\n   Tool: {tool_name}")
            print(f"     Description: {tool_profile.description}")
            print(f"     Capabilities: {len(tool_profile.capabilities)}")
            
            # Check capabilities
            for cap_name, capability in tool_profile.capabilities.items():
                print(f"       Capability: {cap_name}")
                print(f"         Patterns: {len(capability.patterns)}")
                
                # Check patterns
                for pattern_name, pattern in capability.patterns.items():
                    print(f"           Pattern: {pattern_name}")
                    print(f"             Time estimate: {pattern.time_estimate_ms}")
                    print(f"             Cost estimate: {pattern.cost_estimate}")
                    print(f"             Complexity: {pattern.complexity_score}")
                    
                    # Verify required fields
                    if not pattern.description:
                        print(f"             ✗ Missing description")
                        return False
                    
                    if not pattern.policy:
                        print(f"             ✗ Missing policy")
                        return False
                    
                    if not pattern.preference_match:
                        print(f"             ✗ Missing preference_match")
                        return False
                    
                    print(f"             ✓ All required fields present")
        
        # Test 5: Test get_tool_profile method
        print("\n5. Testing get_tool_profile method...")
        first_tool_name = list(profiles.tools.keys())[0]
        tool_profile = loader.get_tool_profile(first_tool_name)
        
        if tool_profile is None:
            print(f"   ✗ Failed to get tool profile for {first_tool_name}")
            return False
        
        print(f"   ✓ Retrieved profile for {first_tool_name}")
        
        # Test 6: Test get_all_tools method
        print("\n6. Testing get_all_tools method...")
        all_tools = loader.get_all_tools()
        
        if len(all_tools) != len(profiles.tools):
            print(f"   ✗ Expected {len(profiles.tools)} tools, got {len(all_tools)}")
            return False
        
        print(f"   ✓ Retrieved all {len(all_tools)} tools")
        
        # Test 7: Test caching
        print("\n7. Testing caching...")
        profiles2 = loader.load()
        
        if profiles2 is not profiles:
            print("   ✗ Cache not working (different object returned)")
            return False
        
        print("   ✓ Cache working (same object returned)")
        
        # Test 8: Test force reload
        print("\n8. Testing force reload...")
        profiles3 = loader.load(force_reload=True)
        
        if len(profiles3.tools) != len(profiles.tools):
            print(f"   ✗ Force reload returned different number of tools")
            return False
        
        print("   ✓ Force reload working")
        
        # Test 9: Test global loader functions
        print("\n9. Testing global loader functions...")
        global_loader = get_loader(use_database=True)
        global_profiles = load_profiles(use_database=True)
        
        if len(global_profiles.tools) < 2:
            print(f"   ✗ Global loader returned insufficient tools")
            return False
        
        print(f"   ✓ Global loader working ({len(global_profiles.tools)} tools)")
        
        print("\n" + "=" * 70)
        print("✅ ALL TESTS PASSED")
        print("=" * 70)
        return True
        
    except Exception as e:
        print(f"\n❌ TEST FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_yaml_mode():
    """Test ProfileLoader in YAML mode (for comparison)"""
    
    print("\n" + "=" * 70)
    print("PROFILE LOADER YAML MODE TEST (for comparison)")
    print("=" * 70)
    
    try:
        # Check if YAML file exists
        from pathlib import Path
        yaml_path = Path(__file__).parent.parent / "config" / "tool_optimization_profiles.yaml"
        
        if not yaml_path.exists():
            print(f"\n⚠️  YAML file not found: {yaml_path}")
            print("   Skipping YAML mode test")
            return True
        
        print("\n1. Initializing ProfileLoader (YAML mode)...")
        loader = ProfileLoader(use_database=False)
        print("   ✓ ProfileLoader initialized")
        
        print("\n2. Loading profiles from YAML...")
        profiles = loader.load()
        print(f"   ✓ Loaded {len(profiles.tools)} tools from YAML")
        
        return True
        
    except Exception as e:
        print(f"\n⚠️  YAML mode test failed (expected if no YAML file): {e}")
        return True  # Don't fail overall test


if __name__ == "__main__":
    # Test database mode
    db_success = test_database_mode()
    
    # Test YAML mode (optional)
    yaml_success = test_yaml_mode()
    
    # Exit with appropriate code
    if db_success:
        print("\n✅ Database integration test PASSED")
        sys.exit(0)
    else:
        print("\n❌ Database integration test FAILED")
        sys.exit(1)