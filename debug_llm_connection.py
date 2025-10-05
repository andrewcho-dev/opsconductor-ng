#!/usr/bin/env python3
"""
Debug LLM Connection for Phase 5 Integration Testing
"""

import asyncio
import os
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from llm.ollama_client import OllamaClient
from llm.client import LLMRequest
from pipeline.orchestrator import PipelineOrchestrator

async def test_llm_connection():
    """Test LLM connection directly."""
    print("🔍 Testing LLM Connection...")
    
    # Test 1: Direct Ollama client
    print("\n1️⃣ Testing Direct Ollama Client:")
    config = {
        "base_url": os.getenv("OLLAMA_HOST", "http://localhost:11434"),
        "default_model": os.getenv("DEFAULT_MODEL", "qwen2.5:7b-instruct-q4_k_m"),
        "timeout": int(os.getenv("OLLAMA_TIMEOUT", "30"))
    }
    print(f"   Config: {config}")
    
    client = OllamaClient(config)
    try:
        await client.connect()
        print(f"   ✅ Connected: {client.is_connected}")
        
        # Test simple generation
        request = LLMRequest(prompt="Hello, test connection")
        response = await client.generate(request)
        print(f"   ✅ Generation test: {response.content[:50]}...")
        
    except Exception as e:
        print(f"   ❌ Connection failed: {e}")
        return False
    
    # Test 2: Pipeline Orchestrator
    print("\n2️⃣ Testing Pipeline Orchestrator:")
    try:
        orchestrator = PipelineOrchestrator(llm_client=client)
        await orchestrator.initialize()
        print("   ✅ Orchestrator initialized successfully")
        
        # Test simple request
        result = await orchestrator.process_request("test request")
        print(f"   ✅ Request processed: {result.success}")
        print(f"   Response type: {result.response.response_type}")
        
    except Exception as e:
        print(f"   ❌ Orchestrator failed: {e}")
        return False
    
    print("\n🎉 All tests passed!")
    return True

if __name__ == "__main__":
    asyncio.run(test_llm_connection())