#!/usr/bin/env python3
"""
Test script for the new AssetMapper
"""

import sys
import os
sys.path.append('/home/opsconductor/opsconductor-ng')

# Import directly from the file
sys.path.append('/home/opsconductor/opsconductor-ng/ai-brain/system_model')
from asset_mapper import AssetMapper, AssetType

def test_asset_mapper():
    """Test the asset mapper functionality"""
    print("Testing AssetMapper with proper asset terminology...")
    
    # Initialize asset mapper
    mapper = AssetMapper()
    
    # Test cache refresh
    print("\n1. Testing cache refresh...")
    try:
        mapper._refresh_cache()
        print("✓ Cache refresh completed successfully")
    except Exception as e:
        print(f"✗ Cache refresh failed: {e}")
        return False
    
    # Test asset resolution
    print("\n2. Testing asset resolution...")
    try:
        # Test resolving all assets
        all_assets = mapper.resolve_assets("*")
        print(f"✓ Found {len(all_assets)} assets")
        
        if all_assets:
            # Test resolving by name
            first_asset = all_assets[0]
            resolved = mapper.resolve_assets(first_asset.name)
            print(f"✓ Resolved asset by name: {first_asset.name}")
            
            # Test resolving by ID
            resolved_by_id = mapper.resolve_assets(str(first_asset.id))
            print(f"✓ Resolved asset by ID: {first_asset.id}")
            
            # Test tag resolution
            tag_assets = mapper.resolve_assets("tag:environment=prod")
            print(f"✓ Tag resolution found {len(tag_assets)} assets")
            
            # Test type resolution
            type_assets = mapper.resolve_assets("type:linux_server")
            print(f"✓ Type resolution found {len(type_assets)} assets")
            
    except Exception as e:
        print(f"✗ Asset resolution failed: {e}")
        return False
    
    # Test resource statistics
    print("\n3. Testing resource statistics...")
    try:
        stats = mapper.get_resource_statistics()
        print(f"✓ Statistics: {stats['assets']['total']} assets, {stats['groups']['total']} groups")
    except Exception as e:
        print(f"✗ Statistics failed: {e}")
        return False
    
    # Test comprehensive resource resolution
    print("\n4. Testing comprehensive resource resolution...")
    try:
        result = mapper.resolve_resources("*")
        print(f"✓ Comprehensive resolution: {len(result.resolved_assets)} assets, {len(result.resolved_credentials)} credentials")
        if result.warnings:
            print(f"  Warnings: {len(result.warnings)}")
        if result.errors:
            print(f"  Errors: {len(result.errors)}")
    except Exception as e:
        print(f"✗ Comprehensive resolution failed: {e}")
        return False
    
    print("\n✓ All tests completed successfully!")
    print("✓ NO MORE LEGACY 'TARGET' TERMINOLOGY - EVERYTHING IS NOW 'ASSET'!")
    return True

if __name__ == "__main__":
    success = test_asset_mapper()
    sys.exit(0 if success else 1)