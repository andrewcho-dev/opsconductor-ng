#!/usr/bin/env python3
"""
Debug script to check the prompts dictionary
"""

import sys
sys.path.insert(0, '/home/opsconductor/opsconductor-ng')

from llm.prompt_manager import PromptManager, PromptType

def debug_prompts():
    """Debug the prompts dictionary"""
    
    print("Creating PromptManager...")
    try:
        pm = PromptManager()
        print("PromptManager created successfully")
        
        print(f"Available prompt types: {list(pm.prompts.keys())}")
        print(f"PromptType.INTENT_CLASSIFICATION value: {PromptType.INTENT_CLASSIFICATION}")
        
        # Check if the key exists
        if PromptType.INTENT_CLASSIFICATION in pm.prompts:
            print("INTENT_CLASSIFICATION key found in prompts")
        else:
            print("INTENT_CLASSIFICATION key NOT found in prompts")
            
    except Exception as e:
        print(f"Error creating PromptManager: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    debug_prompts()