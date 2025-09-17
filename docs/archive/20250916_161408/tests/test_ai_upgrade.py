#!/usr/bin/env python3
"""
Test script for the upgraded AI service
"""
import asyncio
import httpx
import json
import time

async def test_ai_service():
    """Test the upgraded AI service functionality"""
    base_url = "http://localhost:3005"
    
    print("🧪 Testing OpsConductor AI Service Upgrade")
    print("=" * 50)
    
    async with httpx.AsyncClient(timeout=30.0) as client:
        
        # Test 1: Health Check
        print("\n1. Testing Health Check...")
        try:
            response = await client.get(f"{base_url}/health")
            if response.status_code == 200:
                print("✅ Health check passed")
                print(f"   Response: {response.json()}")
            else:
                print(f"❌ Health check failed: {response.status_code}")
        except Exception as e:
            print(f"❌ Health check error: {e}")
        
        # Test 2: Service Info
        print("\n2. Testing Service Info...")
        try:
            response = await client.get(f"{base_url}/info")
            if response.status_code == 200:
                print("✅ Service info retrieved")
                info = response.json()
                print(f"   Service: {info.get('service')}")
                print(f"   Version: {info.get('version')}")
                print(f"   Capabilities: {len(info.get('capabilities', []))}")
            else:
                print(f"❌ Service info failed: {response.status_code}")
        except Exception as e:
            print(f"❌ Service info error: {e}")
        
        # Test 3: System Query
        print("\n3. Testing System Query...")
        try:
            query_data = {"question": "How many targets do I have?"}
            response = await client.post(f"{base_url}/ai/query-system", json=query_data)
            if response.status_code == 200:
                print("✅ System query successful")
                result = response.json()
                print(f"   Answer: {result.get('answer', 'No answer')}")
                if 'count' in result:
                    print(f"   Count: {result['count']}")
            else:
                print(f"❌ System query failed: {response.status_code}")
                print(f"   Response: {response.text}")
        except Exception as e:
            print(f"❌ System query error: {e}")
        
        # Test 4: Chat Interface
        print("\n4. Testing Chat Interface...")
        try:
            chat_data = {"message": "Hello, what can you help me with?", "user_id": 1}
            response = await client.post(f"{base_url}/ai/chat", json=chat_data)
            if response.status_code == 200:
                print("✅ Chat interface working")
                result = response.json()
                print(f"   Response: {result.get('response', 'No response')[:100]}...")
                if 'suggestions' in result:
                    print(f"   Suggestions: {len(result['suggestions'])} provided")
            else:
                print(f"❌ Chat interface failed: {response.status_code}")
                print(f"   Response: {response.text}")
        except Exception as e:
            print(f"❌ Chat interface error: {e}")
        
        # Test 5: Script Generation (if Ollama is ready)
        print("\n5. Testing Script Generation...")
        try:
            script_data = {
                "request": "Create a simple PowerShell script to check disk space",
                "language": "powershell"
            }
            response = await client.post(f"{base_url}/ai/generate-script", json=script_data)
            if response.status_code == 200:
                print("✅ Script generation working")
                result = response.json()
                if 'script' in result:
                    print(f"   Generated script length: {len(result['script'])} characters")
                    print(f"   Language: {result.get('language')}")
                elif 'error' in result:
                    print(f"   Note: {result['error']} (Ollama may still be initializing)")
            else:
                print(f"❌ Script generation failed: {response.status_code}")
                print(f"   Response: {response.text}")
        except Exception as e:
            print(f"❌ Script generation error: {e}")
        
        # Test 6: Target Query with Tag
        print("\n6. Testing Target Query with Tag...")
        try:
            query_data = {"question": "Which targets are tagged with win10?"}
            response = await client.post(f"{base_url}/ai/query-system", json=query_data)
            if response.status_code == 200:
                print("✅ Target tag query successful")
                result = response.json()
                print(f"   Answer: {result.get('answer', 'No answer')}")
                if 'targets' in result:
                    print(f"   Found targets: {len(result['targets'])}")
            else:
                print(f"❌ Target tag query failed: {response.status_code}")
        except Exception as e:
            print(f"❌ Target tag query error: {e}")

def main():
    """Main test function"""
    print("Starting AI Service Tests...")
    print("Make sure the AI service is running on port 3005")
    print("Waiting 5 seconds for service to be ready...")
    time.sleep(5)
    
    try:
        asyncio.run(test_ai_service())
    except KeyboardInterrupt:
        print("\n\n⚠️ Tests interrupted by user")
    except Exception as e:
        print(f"\n\n❌ Test suite failed: {e}")
    
    print("\n" + "=" * 50)
    print("🏁 AI Service Tests Complete")

if __name__ == "__main__":
    main()