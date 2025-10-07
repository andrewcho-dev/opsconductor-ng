#!/usr/bin/env python3
"""
Test different parameter formats for Axis camera
"""
import asyncio
import httpx

async def test_params():
    """Test different parameter formats"""
    
    url = "http://192.168.10.90/axis-cgi/com/ptz.cgi"
    username = "root"
    password = "Enabled123!"
    
    print("=" * 80)
    print("Testing Different Parameter Formats")
    print("=" * 80)
    
    # Test 1: Correct format - move=home
    print("\n" + "-" * 80)
    print("Test 1: params={'move': 'home'}")
    print("-" * 80)
    try:
        async with httpx.AsyncClient(verify=False, timeout=10.0) as client:
            response = await client.get(
                url,
                params={'move': 'home'},
                auth=httpx.DigestAuth(username, password)
            )
            print(f"URL: {response.url}")
            print(f"Status: {response.status_code}")
            print(f"Response: {response.text if response.text else '(empty)'}")
    except Exception as e:
        print(f"Error: {e}")
    
    # Test 2: Wrong format - cmd=move=home
    print("\n" + "-" * 80)
    print("Test 2: params={'cmd': 'move=home'}")
    print("-" * 80)
    try:
        async with httpx.AsyncClient(verify=False, timeout=10.0) as client:
            response = await client.get(
                url,
                params={'cmd': 'move=home'},
                auth=httpx.DigestAuth(username, password)
            )
            print(f"URL: {response.url}")
            print(f"Status: {response.status_code}")
            print(f"Response: {response.text if response.text else '(empty)'}")
    except Exception as e:
        print(f"Error: {e}")
    
    print("\n" + "=" * 80)

if __name__ == "__main__":
    asyncio.run(test_params())