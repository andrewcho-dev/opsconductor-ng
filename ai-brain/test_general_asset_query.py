#!/usr/bin/env python3
"""
Test script to verify AI Brain can handle general asset queries
"""

import asyncio
import sys
import os
import logging

# Add the ai-brain directory to the path
sys.path.insert(0, '/home/opsconductor/opsconductor-ng/ai-brain')

from integrations.asset_client import AssetServiceClient
from llm_conversation_handler import LLMConversationHandler
from integrations.llm_client import LLMEngine

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_general_asset_query():
    """Test if the AI can handle general asset queries"""
    
    print("=== Testing General Asset Query ===")
    
    # Initialize components
    asset_client = AssetServiceClient("http://localhost:3002")
    
    # Health check
    healthy = await asset_client.health_check()
    print(f"Asset service healthy: {healthy}")
    
    if not healthy:
        print("❌ Asset service is not healthy!")
        return False
    
    # Initialize LLM engine
    ollama_host = os.getenv("OLLAMA_HOST", "http://localhost:11434")
    default_model = os.getenv("DEFAULT_MODEL", "llama3.2:3b")
    llm_engine = LLMEngine(ollama_host, default_model)
    
    # Initialize the LLM engine
    llm_init_success = await llm_engine.initialize()
    if not llm_init_success:
        print("❌ Failed to initialize LLM engine!")
        return False
    
    # Initialize conversation handler with asset client
    conversation_handler = LLMConversationHandler(llm_engine, asset_client)
    
    # Test the exact query that was failing
    test_message = "tell me about what assets we have in our system"
    print(f"Testing message: '{test_message}'")
    
    # Process the message
    result = await conversation_handler.process_message(test_message, "test_user")
    
    if result.get("success"):
        response = result.get("response", "")
        print(f"✅ AI Response: {response}")
        
        # Check if the response contains real asset names (not fictional ones)
        real_asset_names = ["win10-test05", "win11-test01", "win10-test04", "win10-test03", "win10-test02", "Windows Server 2019"]
        fake_asset_names = ["primary-server", "secondary-server", "database-server", "web-server"]
        
        contains_real_data = any(name.lower() in response.lower() for name in real_asset_names)
        contains_fake_data = any(name.lower() in response.lower() for name in fake_asset_names)
        
        if contains_real_data and not contains_fake_data:
            print("✅ AI successfully used REAL asset database information!")
            return True
        elif contains_fake_data:
            print("❌ AI is still using FAKE/HALLUCINATED data!")
            print("Fake data found in response")
            return False
        else:
            print("❌ AI response doesn't contain expected real asset information")
            print("Expected to find real asset names like: win10-test05, win11-test01, etc.")
            return False
    else:
        print(f"❌ AI conversation failed: {result.get('error', 'Unknown error')}")
        return False

async def main():
    """Main test function"""
    success = await test_general_asset_query()
    
    if success:
        print("\n🎉 SUCCESS: AI now uses REAL asset database information!")
    else:
        print("\n💥 FAILURE: AI is still hallucinating fake data!")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())