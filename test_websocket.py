#!/usr/bin/env python3
"""
Simple WebSocket test script to verify thinking visualization WebSocket connection
"""

import asyncio
import websockets
import json
import sys

async def test_websocket_connection(session_id):
    """Test WebSocket connection to thinking stream"""
    uri = f"ws://localhost:3005/ws/thinking/{session_id}"
    print(f"🔌 Connecting to: {uri}")
    
    try:
        async with websockets.connect(uri) as websocket:
            print("✅ WebSocket connected successfully!")
            
            # Wait for connection established message
            try:
                message = await asyncio.wait_for(websocket.recv(), timeout=5.0)
                data = json.loads(message)
                print(f"📨 Received: {data}")
                
                if data.get("type") == "connection_established":
                    print("🎉 Connection established message received!")
                    
                    # Request history
                    await websocket.send(json.dumps({"type": "get_history"}))
                    print("📤 Requested history")
                    
                    # Wait for history response
                    history_message = await asyncio.wait_for(websocket.recv(), timeout=5.0)
                    history_data = json.loads(history_message)
                    print(f"📚 History received: {len(history_data.get('thinking_history', []))} thinking steps")
                    
                    # Wait for any real-time messages
                    print("⏳ Waiting for real-time messages (10 seconds)...")
                    try:
                        while True:
                            message = await asyncio.wait_for(websocket.recv(), timeout=10.0)
                            data = json.loads(message)
                            print(f"📨 Real-time message: {data.get('type')}")
                    except asyncio.TimeoutError:
                        print("⏰ No real-time messages received in 10 seconds")
                
            except asyncio.TimeoutError:
                print("⏰ Timeout waiting for initial message")
                
    except Exception as e:
        print(f"❌ WebSocket connection failed: {e}")
        return False
    
    return True

async def main():
    if len(sys.argv) != 2:
        print("Usage: python test_websocket.py <session_id>")
        sys.exit(1)
    
    session_id = sys.argv[1]
    success = await test_websocket_connection(session_id)
    
    if success:
        print("✅ WebSocket test completed successfully")
    else:
        print("❌ WebSocket test failed")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())