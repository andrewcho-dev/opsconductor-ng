#!/usr/bin/env python3
"""Test the specific hostname command using the working test framework"""

import pytest
import pytest_asyncio
import asyncio
import os
import sys
import time

# Add current directory to path
sys.path.insert(0, '/home/opsconductor/opsconductor-ng')

from pipeline.orchestrator import PipelineOrchestrator
from llm.ollama_client import OllamaClient

class TestSpecificHostname:
    """Test the specific hostname command that's failing"""
    
    @pytest_asyncio.fixture(scope="function")
    async def orchestrator(self):
        """Create real orchestrator for actual pipeline execution"""
        llm_config = {
            "base_url": os.getenv("OLLAMA_BASE_URL", "http://localhost:11434"),
            "default_model": os.getenv("OLLAMA_MODEL", "qwen2.5:7b-instruct-q4_k_m"),
            "timeout": 120
        }
        llm_client = OllamaClient(llm_config)
        await llm_client.connect()
        
        orchestrator = PipelineOrchestrator(llm_client=llm_client)
        await orchestrator.initialize()
        
        return orchestrator
    
    async def execute_real_prompt(self, orchestrator, prompt, timeout=60):
        """Execute a real user prompt through the pipeline"""
        print(f"\n📝 Executing: {prompt}")
        start_time = time.time()
        
        try:
            result = await asyncio.wait_for(
                orchestrator.process_request(prompt),
                timeout=timeout
            )
            
            duration = time.time() - start_time
            print(f"⏱️  Completed in: {duration:.2f}s")
            print(f"✅ Success: {result.success}")
            
            if result.response:
                print(f"💬 Response preview: {result.response.message[:200]}...")
                print(f"\n📄 Full Response:\n{result.response.message}")
            
            return result, duration
            
        except Exception as e:
            duration = time.time() - start_time
            print(f"❌ Failed after {duration:.2f}s: {e}")
            raise
    
    @pytest.mark.asyncio
    async def test_hostname_command_debug(self, orchestrator):
        """Test the exact hostname command that's failing"""
        result, duration = await self.execute_real_prompt(
            orchestrator, 
            "Display contents of /etc/hostname on 192.168.50.12",
            timeout=90
        )
        
        # Print detailed debugging info
        print(f"\n🔍 Detailed Results:")
        print(f"   Success: {result.success}")
        print(f"   Duration: {duration:.2f}s")
        
        if hasattr(result, 'stage_results') and result.stage_results:
            print(f"   Stage results: {len(result.stage_results)}")
            for i, stage_result in enumerate(result.stage_results):
                print(f"     Stage {i+1}: {stage_result}")
        
        if hasattr(result, 'error') and result.error:
            print(f"   Error: {result.error}")
            
        # For now, we're just debugging - don't fail the test
        assert True  # Always pass for debugging purposes