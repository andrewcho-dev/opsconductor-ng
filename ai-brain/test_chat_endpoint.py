#!/usr/bin/env python3
"""
Test script to simulate the chat endpoint processing
"""

import sys
from pathlib import Path

# Add the ai-brain directory to the path
sys.path.insert(0, str(Path(__file__).parent))

try:
    print("Testing chat endpoint processing...")
    
    # Test brain engine initialization
    print("1. Importing AIBrainEngine...")
    from brain_engine import AIBrainEngine
    print("   ✓ AIBrainEngine imported successfully")
    
    print("2. Creating AIBrainEngine instance...")
    ai_engine = AIBrainEngine()
    print(f"   ✓ AIBrainEngine created")
    print(f"   - Intent engine enabled: {ai_engine.intent_engine_enabled}")
    
    if hasattr(ai_engine, 'clarification_manager'):
        print(f"   - ClarificationManager: {type(ai_engine.clarification_manager)}")
    else:
        print("   - ClarificationManager: Not initialized")
    
    print("3. Testing message processing...")
    import asyncio
    
    async def test_message():
        try:
            response = await ai_engine.process_message(
                message="i want to create a job to get the file listing on a machine",
                conversation_id="test-123",
                user_id="test-user"
            )
            print(f"   ✓ Message processed successfully: {response.get('response', 'No response')[:100]}...")
            return True
        except Exception as e:
            print(f"   ❌ Message processing failed: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    success = asyncio.run(test_message())
    
    if success:
        print("\n🎉 Chat endpoint simulation passed!")
    else:
        print("\n❌ Chat endpoint simulation failed!")
    
except Exception as e:
    print(f"\n❌ Error during setup: {e}")
    import traceback
    traceback.print_exc()