#!/usr/bin/env python3
"""
Query and test Axis camera presets including home position
"""
import asyncio
import httpx

async def test_presets():
    """Query presets and test home position"""
    
    url = "http://192.168.10.90/axis-cgi/com/ptz.cgi"
    username = "root"
    password = "Enabled123!"
    
    print("=" * 80)
    print("Axis Camera Preset Testing")
    print("=" * 80)
    
    # Test 1: Query all presets
    print("\n" + "-" * 80)
    print("Test 1: Query All Presets (query=presetposall)")
    print("-" * 80)
    try:
        async with httpx.AsyncClient(verify=False, timeout=10.0) as client:
            response = await client.get(
                url,
                params={'query': 'presetposall'},
                auth=httpx.DigestAuth(username, password)
            )
            print(f"Status: {response.status_code}")
            print(f"Response:\n{response.text}")
    except Exception as e:
        print(f"Error: {e}")
    
    # Test 2: Get current position before home
    print("\n" + "-" * 80)
    print("Test 2: Get Current Position BEFORE Home Command")
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
    
    # Test 3: Send home command
    print("\n" + "-" * 80)
    print("Test 3: Send Home Command (move=home)")
    print("-" * 80)
    try:
        async with httpx.AsyncClient(verify=False, timeout=10.0) as client:
            response = await client.get(
                url,
                params={'move': 'home'},
                auth=httpx.DigestAuth(username, password)
            )
            print(f"Status: {response.status_code}")
            print(f"Response: {response.text if response.text else '(empty)'}")
            if response.status_code in [200, 204]:
                print("✅ Home command sent successfully")
    except Exception as e:
        print(f"Error: {e}")
    
    # Wait a moment for camera to move
    print("\n⏳ Waiting 3 seconds for camera to move...")
    await asyncio.sleep(3)
    
    # Test 4: Get position after home
    print("\n" + "-" * 80)
    print("Test 4: Get Current Position AFTER Home Command")
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
    
    print("\n" + "=" * 80)
    print("💡 If the position changed, the home command worked!")
    print("💡 If position is the same, the camera might already be at home")
    print("=" * 80)

if __name__ == "__main__":
    asyncio.run(test_presets())