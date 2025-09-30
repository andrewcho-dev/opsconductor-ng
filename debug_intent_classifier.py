#!/usr/bin/env python3
"""
Debug script to identify the intent classification issue
"""

import asyncio
import sys
import traceback
from unittest.mock import Mock, AsyncMock

# Add the project root to the path
sys.path.insert(0, '/home/opsconductor/opsconductor-ng')

from pipeline.stages.stage_a.intent_classifier import IntentClassifier
from llm.client import LLMClient, LLMResponse

async def debug_intent_classification():
    """Debug the intent classification issue"""
    
    # Create mock LLM client
    mock_llm_client = Mock(spec=LLMClient)
    mock_llm_client.is_connected = True
    mock_llm_client.health_check = AsyncMock(return_value=True)
    
    # Create a valid response
    valid_response = LLMResponse(
        content='{"category": "automation", "action": "restart_service", "confidence": 0.95}',
        model="llama2",
        tokens_used=50,
        processing_time_ms=1500
    )
    
    mock_llm_client.generate = AsyncMock(return_value=valid_response)
    
    # Create intent classifier
    classifier = IntentClassifier(mock_llm_client)
    
    print("Testing intent classification...")
    print(f"Mock LLM response: {valid_response.content}")
    
    try:
        # Test the classification step by step
        print("\n1. Testing prompt generation...")
        from llm.prompt_manager import PromptType
        prompts = classifier.prompt_manager.get_prompt(
            PromptType.INTENT_CLASSIFICATION,
            user_request="restart nginx service"
        )
        print(f"Prompts generated successfully: {list(prompts.keys())}")
        
        print("\n2. Testing LLM request creation...")
        from llm.client import LLMRequest
        llm_request = LLMRequest(
            prompt=prompts["user"],
            system_prompt=prompts["system"],
            temperature=0.1,
            max_tokens=200
        )
        print("LLM request created successfully")
        
        print("\n3. Testing LLM generation...")
        response = await classifier.llm_client.generate(llm_request)
        print(f"LLM response: {response.content}")
        
        print("\n4. Testing response parsing...")
        intent_data = classifier.response_parser.parse_intent_response(response.content)
        print(f"Parsed intent data: {intent_data}")
        
        print("\n5. Testing IntentV1 creation...")
        from pipeline.schemas.decision_v1 import IntentV1
        intent = IntentV1(
            category=intent_data["category"],
            action=intent_data["action"],
            confidence=intent_data["confidence"]
        )
        print(f"IntentV1 created: category={intent.category}, action={intent.action}, confidence={intent.confidence}")
        
        print("\n6. Testing full classification...")
        result = await classifier.classify_intent("restart nginx service")
        
        print(f"Final result category: {result.category}")
        print(f"Final result action: {result.action}")
        print(f"Final result confidence: {result.confidence}")
        
        if result.category == "unknown":
            print("ERROR: Classification returned 'unknown' - this indicates an exception occurred")
        else:
            print("SUCCESS: Classification worked correctly")
            
    except Exception as e:
        print(f"EXCEPTION during classification: {e}")
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(debug_intent_classification())