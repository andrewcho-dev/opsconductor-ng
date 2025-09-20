#!/usr/bin/env python3
"""
Debug script to test ClarificationManager initialization
"""

import sys
from pathlib import Path

# Add the ai-brain directory to the path
sys.path.insert(0, str(Path(__file__).parent))

try:
    print("Testing ClarificationManager import and initialization...")
    
    # Test import
    print("1. Importing ConversationManager...")
    from intent_engine.conversation_manager import ConversationManager
    print("   ✓ ConversationManager imported successfully")
    
    print("2. Importing ClarificationManager...")
    from intent_engine.clarification_manager import ClarificationManager
    print("   ✓ ClarificationManager imported successfully")
    
    print("3. Creating ConversationManager instance...")
    conversation_manager = ConversationManager()
    print(f"   ✓ ConversationManager created: {type(conversation_manager)}")
    
    print("4. Creating ClarificationManager instance...")
    clarification_manager = ClarificationManager(conversation_manager)
    print(f"   ✓ ClarificationManager created: {type(clarification_manager)}")
    
    print("\n🎉 All tests passed! ClarificationManager can be initialized correctly.")
    
except Exception as e:
    print(f"\n❌ Error: {e}")
    import traceback
    traceback.print_exc()