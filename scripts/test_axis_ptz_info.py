#!/usr/bin/env python3
"""
Query Axis camera PTZ capabilities and status
"""
import asyncio
import httpx

async def test_ptz_info():
    """Query PTZ information from Axis camera"""
    
    url = "http://192.168.10.90/axis-cgi/com/ptz.cgi"
    username = "root"
    password = "Enabled123!"
    
    print("=" * 80)
    print("Axis Camera PTZ Information")
    print("=" * 80)
    
    # Test 1: Query PTZ info
    print("\n" + "-" * 80)
    print("Test 1: Query PTZ Info (info=1)")
    print("-" * 80)
    try:
        async with httpx.AsyncClient(verify=False, timeout=10.0) as client:
            response = await client.get(
                url,
                params={'info': '1'},
                auth=httpx.DigestAuth(username, password)
            )
            print(f"Status: {response.status_code}")
            print(f"Response:\n{response.text}")
    except Exception as e:
        print(f"Error: {e}")
    
    # Test 2: Query current position
    print("\n" + "-" * 80)
    print("Test 2: Query Current Position (query=position)")
    print("-" * 80)
    try:
        async with httpx.AsyncClient(verify=False, timeout=10.0) as client:
            response = await client.get(
                url,
                params={'query': 'position'},
                auth=httpx.DigestAuth(username, password)
            )
            print(f"Status: {response.status_code}")
            print(f"Response:\n{response.text}")
    except Exception as e:
        print(f"Error: {e}")
    
    # Test 3: Try a small pan movement to test if PTZ works
    print("\n" + "-" * 80)
    print("Test 3: Small Pan Movement (rpan=5)")
    print("-" * 80)
    try:
        async with httpx.AsyncClient(verify=False, timeout=10.0) as client:
            response = await client.get(
                url,
                params={'rpan': '5'},
                auth=httpx.DigestAuth(username, password)
            )
            print(f"Status: {response.status_code}")
            print(f"Response: {response.text if response.text else '(empty)'}")
            if response.status_code in [200, 204]:
                print("✅ Pan command accepted - camera should have moved slightly")
    except Exception as e:
        print(f"Error: {e}")
    
    print("\n" + "=" * 80)

if __name__ == "__main__":
    asyncio.run(test_ptz_info())