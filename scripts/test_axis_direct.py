#!/usr/bin/env python3
"""
Direct test of Axis camera API with Digest authentication
"""
import asyncio
import httpx

async def test_axis_camera():
    """Test Axis camera API with both Basic and Digest auth"""
    
    url = "http://192.168.10.90/axis-cgi/com/ptz.cgi"
    params = {"autofocus": "on", "camera": "1"}
    username = "root"
    password = "Enabled123!"
    
    print("=" * 80)
    print("Testing Axis Camera API Authentication")
    print("=" * 80)
    print(f"\n📍 URL: {url}")
    print(f"🔑 Username: {username}")
    print(f"🎯 Action: Autofocus lens\n")
    
    # Test 1: Basic Authentication
    print("-" * 80)
    print("Test 1: HTTP Basic Authentication")
    print("-" * 80)
    try:
        async with httpx.AsyncClient(verify=False, timeout=10.0) as client:
            response = await client.get(
                url,
                params=params,
                auth=httpx.BasicAuth(username, password)
            )
            print(f"✅ Status Code: {response.status_code}")
            print(f"📄 Response: {response.text[:200]}")
    except Exception as e:
        print(f"❌ Error: {e}")
    
    print()
    
    # Test 2: Digest Authentication
    print("-" * 80)
    print("Test 2: HTTP Digest Authentication")
    print("-" * 80)
    try:
        async with httpx.AsyncClient(verify=False, timeout=10.0) as client:
            response = await client.get(
                url,
                params=params,
                auth=httpx.DigestAuth(username, password)
            )
            print(f"✅ Status Code: {response.status_code}")
            print(f"📄 Response: {response.text[:200]}")
            
            if response.status_code == 200:
                print("\n🎉 SUCCESS! Digest authentication worked!")
            else:
                print(f"\n⚠️  Unexpected status code: {response.status_code}")
                
    except Exception as e:
        print(f"❌ Error: {e}")
    
    print("\n" + "=" * 80)

if __name__ == "__main__":
    asyncio.run(test_axis_camera())