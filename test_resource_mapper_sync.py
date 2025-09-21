#!/usr/bin/env python3
"""
Test script for the updated synchronous ResourceMapper
"""

import sys
import os
sys.path.append('/home/opsconductor/opsconductor-ng')

from ai_brain.system_model.resource_mapper import ResourceMapper, TargetType

def test_resource_mapper():
    """Test the resource mapper functionality"""
    print("Testing ResourceMapper with synchronous requests...")
    
    # Initialize resource mapper
    mapper = ResourceMapper()
    
    # Test cache refresh
    print("\n1. Testing cache refresh...")
    try:
        mapper._refresh_cache()
        print("✓ Cache refresh completed successfully")
    except Exception as e:
        print(f"✗ Cache refresh failed: {e}")
        return False
    
    # Test target resolution
    print("\n2. Testing target resolution...")
    try:
        # Test resolving all targets
        all_targets = mapper.resolve_targets("*")
        print(f"✓ Found {len(all_targets)} targets")
        
        if all_targets:
            # Test resolving by name
            first_target = all_targets[0]
            resolved = mapper.resolve_targets(first_target.name)
            print(f"✓ Resolved target by name: {first_target.name}")
            
            # Test resolving by ID
            resolved_by_id = mapper.resolve_targets(str(first_target.id))
            print(f"✓ Resolved target by ID: {first_target.id}")
            
            # Test tag resolution
            tag_targets = mapper.resolve_targets("tag:environment=prod")
            print(f"✓ Tag resolution found {len(tag_targets)} targets")
            
            # Test type resolution
            type_targets = mapper.resolve_targets("type:linux_server")
            print(f"✓ Type resolution found {len(type_targets)} targets")
            
    except Exception as e:
        print(f"✗ Target resolution failed: {e}")
        return False
    
    # Test resource statistics
    print("\n3. Testing resource statistics...")
    try:
        stats = mapper.get_resource_statistics()
        print(f"✓ Statistics: {stats['targets']['total']} targets, {stats['groups']['total']} groups")
    except Exception as e:
        print(f"✗ Statistics failed: {e}")
        return False
    
    # Test comprehensive resource resolution
    print("\n4. Testing comprehensive resource resolution...")
    try:
        result = mapper.resolve_resources("*")
        print(f"✓ Comprehensive resolution: {len(result.resolved_targets)} targets, {len(result.resolved_credentials)} credentials")
        if result.warnings:
            print(f"  Warnings: {len(result.warnings)}")
        if result.errors:
            print(f"  Errors: {len(result.errors)}")
    except Exception as e:
        print(f"✗ Comprehensive resolution failed: {e}")
        return False
    
    print("\n✓ All tests completed successfully!")
    return True

if __name__ == "__main__":
    success = test_resource_mapper()
    sys.exit(0 if success else 1)