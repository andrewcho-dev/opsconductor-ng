#!/usr/bin/env python3
"""
Test script to verify the AI target query fix
"""
import asyncio
import sys
import os
sys.path.append('/home/opsconductor/opsconductor-ng/ai-service')

from ai_engine import OpsConductorAI

async def test_target_query():
    """Test the target query functionality"""
    print("🧪 Testing AI Target Query Fix...")
    
    # Initialize AI engine
    ai = OpsConductorAI()
    
    # Mock some target data for testing
    ai.system_knowledge = {
        'targets': [
            {
                'hostname': 'workstation-01',
                'ip_address': '192.168.1.10',
                'os': 'Windows 10 Pro',
                'tags': 'win10,workstation,office'
            },
            {
                'hostname': 'workstation-02', 
                'ip_address': '192.168.1.11',
                'os': 'Windows 10 Home',
                'tags': 'win10,workstation,office'
            },
            {
                'hostname': 'server-01',
                'ip_address': '192.168.1.100',
                'os': 'Windows Server 2019',
                'tags': 'server,windows,production'
            },
            {
                'hostname': 'ubuntu-dev',
                'ip_address': '192.168.1.50',
                'os': 'Ubuntu 22.04 LTS',
                'tags': 'linux,ubuntu,development'
            }
        ],
        'enhanced_targets': [],
        'recent_jobs': []
    }
    
    # Test Windows 10 query
    print("\n1️⃣ Testing Windows 10 query...")
    result = await ai.handle_target_query("How many targets are Windows 10 OS?", [])
    print(f"Response: {result['response'][:200]}...")
    print(f"Success: {result['success']}")
    print(f"Filtered targets: {result['data']['filtered_targets']}")
    
    # Test win10 tag query
    print("\n2️⃣ Testing win10 tag query...")
    result = await ai.handle_target_query("Show me targets with win10 tag", [])
    print(f"Response: {result['response'][:200]}...")
    print(f"Success: {result['success']}")
    print(f"Filtered targets: {result['data']['filtered_targets']}")
    
    # Test general Windows query
    print("\n3️⃣ Testing general Windows query...")
    result = await ai.handle_target_query("Show me all Windows targets", [])
    print(f"Response: {result['response'][:200]}...")
    print(f"Success: {result['success']}")
    print(f"Filtered targets: {result['data']['filtered_targets']}")
    
    # Test Linux query
    print("\n4️⃣ Testing Linux query...")
    result = await ai.handle_target_query("Show me Linux targets", [])
    print(f"Response: {result['response'][:200]}...")
    print(f"Success: {result['success']}")
    print(f"Filtered targets: {result['data']['filtered_targets']}")
    
    print("\n✅ Target query tests completed!")

if __name__ == "__main__":
    asyncio.run(test_target_query())