#!/usr/bin/env python3
"""
Test script for the updated resource mapper
"""
import asyncio
import sys
import os

# Add the ai-brain directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'ai-brain'))

from system_model.resource_mapper import ResourceMapper

async def test_resource_mapper():
    """Test the updated resource mapper"""
    print("=== Testing Updated Resource Mapper ===")
    
    # Create resource mapper instance
    mapper = ResourceMapper("http://localhost:3002")
    
    # Test cache refresh
    print("1. Testing cache refresh...")
    await mapper._refresh_cache()
    
    # Check what we got
    stats = mapper.get_resource_statistics()
    print(f"   Found {stats['targets']['total']} assets/targets")
    print(f"   Target types: {stats['targets']['by_type']}")
    print(f"   Target statuses: {stats['targets']['by_status']}")
    
    # Test target resolution by name
    print("\n2. Testing target resolution by name...")
    targets = await mapper.resolve_targets("Windows Server 2019")
    if targets:
        target = targets[0]
        print(f"   Found target: {target.name} ({target.host}) - {target.target_type.value}")
        print(f"   Properties: {target.properties}")
    else:
        print("   No target found")
    
    # Test target resolution by IP (through host pattern)
    print("\n3. Testing target resolution by IP...")
    targets = await mapper.resolve_targets("host:192.168.50.210")
    if targets:
        target = targets[0]
        print(f"   Found target: {target.name} ({target.host}) - {target.target_type.value}")
    else:
        print("   No target found")
    
    # Test tag-based resolution
    print("\n4. Testing tag-based resolution...")
    targets = await mapper.resolve_targets("tag:win10")
    print(f"   Found {len(targets)} targets with 'win10' tag")
    for target in targets:
        print(f"     - {target.name} ({target.host})")
    
    # Test type-based resolution
    print("\n5. Testing type-based resolution...")
    targets = await mapper.resolve_targets("type:windows_server")
    print(f"   Found {len(targets)} Windows server targets")
    for target in targets:
        print(f"     - {target.name} ({target.host})")
    
    print("\n=== Test Complete ===")

if __name__ == "__main__":
    asyncio.run(test_resource_mapper())