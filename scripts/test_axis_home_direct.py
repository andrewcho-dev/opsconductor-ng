#!/usr/bin/env python3
"""
Direct test of Axis camera PTZ home position command
"""
import asyncio
import httpx

async def test_axis_home():
    """Test Axis camera PTZ home position command"""
    
    url = "http://192.168.10.90/axis-cgi/com/ptz.cgi"
    params = {"move": "home"}
    username = "root"
    password = "Enabled123!"
    
    print("=" * 80)
    print("Testing Axis Camera PTZ Home Position")
    print("=" * 80)
    print(f"\n📍 URL: {url}")
    print(f"🔑 Username: {username}")
    print(f"🎯 Action: Move to home position\n")
    
    print("-" * 80)
    print("Sending PTZ Home Command")
    print("-" * 80)
    try:
        async with httpx.AsyncClient(verify=False, timeout=10.0) as client:
            response = await client.get(
                url,
                params=params,
                auth=httpx.DigestAuth(username, password)
            )
            print(f"✅ Status Code: {response.status_code}")
            print(f"📄 Response: {response.text if response.text else '(empty response)'}")
            
            if response.status_code in [200, 204]:
                print("\n🎉 SUCCESS! PTZ home command sent successfully!")
            else:
                print(f"\n⚠️  Unexpected status code: {response.status_code}")
                
    except Exception as e:
        print(f"❌ Error: {e}")
    
    print("\n" + "=" * 80)

if __name__ == "__main__":
    asyncio.run(test_axis_home())