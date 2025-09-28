#!/usr/bin/env python3
"""
Test script to verify AI Brain can access asset data
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

async def test_asset_access():
    """Test if the AI can access asset data"""
    
    print("=== Testing Asset Access ===")
    
    # Test 1: Direct asset client access
    print("\n1. Testing direct asset client access...")
    asset_client = AssetServiceClient("http://asset-service:3002")
    
    # Health check
    healthy = await asset_client.health_check()
    print(f"Asset service healthy: {healthy}")
    
    if not healthy:
        print("❌ Asset service is not healthy!")
        return False
    
    # Get all assets
    assets = await asset_client.get_all_assets()
    print(f"Found {len(assets)} assets")
    
    if len(assets) == 0:
        print("❌ No assets found!")
        return False
    
    # Test specific IP lookup
    test_ip = "192.168.50.210"
    asset = await asset_client.get_asset_by_ip(test_ip)
    if asset:
        print(f"✅ Found asset for IP {test_ip}: {asset['name']} ({asset['os_type']})")
    else:
        print(f"❌ No asset found for IP {test_ip}")
        return False
    
    # Test 2: LLM Conversation Handler with asset access
    print("\n2. Testing LLM conversation handler with asset access...")
    
    try:
        # Initialize LLM engine
        ollama_host = os.getenv("OLLAMA_HOST", "http://ollama:11434")
        default_model = os.getenv("DEFAULT_MODEL", "llama3.2:3b")
        llm_engine = LLMEngine(ollama_host, default_model)
        
        # Initialize the LLM engine
        llm_init_success = await llm_engine.initialize()
        if not llm_init_success:
            print("❌ Failed to initialize LLM engine!")
            return False
        
        # Initialize conversation handler with asset client
        conversation_handler = LLMConversationHandler(llm_engine, asset_client)
        
        # Test message with IP address
        test_message = f"What do you know about {test_ip}?"
        print(f"Testing message: '{test_message}'")
        
        # Process the message
        result = await conversation_handler.process_message(test_message, "test_user")
        
        if result.get("success"):
            response = result.get("response", "")
            print(f"✅ AI Response: {response[:200]}...")
            
            # Check if the response contains asset information
            if asset['name'].lower() in response.lower() or asset['os_type'].lower() in response.lower():
                print("✅ AI successfully used asset database information!")
                return True
            else:
                print("❌ AI response doesn't contain expected asset information")
                print(f"Expected to find: {asset['name']} or {asset['os_type']}")
                print(f"Full response: {response}")
                return False
        else:
            print(f"❌ AI conversation failed: {result.get('error', 'Unknown error')}")
            return False
            
    except Exception as e:
        print(f"❌ Error testing LLM conversation handler: {e}")
        return False

async def main():
    """Main test function"""
    success = await test_asset_access()
    
    if success:
        print("\n🎉 SUCCESS: AI has access to asset database!")
    else:
        print("\n💥 FAILURE: AI cannot access asset database properly!")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())