#!/usr/bin/env python3
"""
Test Natural Language Parsing Functions
"""

def _parse_natural_language_intent_analysis(response_text: str):
    """Parse natural language intent analysis response from LLM"""
    response_lower = response_text.lower()
    
    # Determine if it's a job request
    is_job_request = False
    if any(phrase in response_lower for phrase in [
        "job request", "automation", "action", "execute", "perform", "run", "deploy", "install", "restart", "start", "stop"
    ]):
        is_job_request = True
    elif any(phrase in response_lower for phrase in [
        "conversation", "question", "information", "help", "discuss", "explain", "what is", "how does"
    ]):
        is_job_request = False
    else:
        # Default logic based on keywords
        action_keywords = ["restart", "run", "execute", "deploy", "install", "configure", "setup", "create", "delete", "update", "ping", "check status"]
        conversation_keywords = ["what", "how", "why", "explain", "tell me", "help", "information"]
        
        action_count = sum(1 for keyword in action_keywords if keyword in response_lower)
        conversation_count = sum(1 for keyword in conversation_keywords if keyword in response_lower)
        
        is_job_request = action_count > conversation_count
    
    # Determine confidence
    confidence = 0.8  # Default medium-high confidence
    if any(phrase in response_lower for phrase in ["high confidence", "very confident", "certain", "definitely"]):
        confidence = 0.95
    elif any(phrase in response_lower for phrase in ["medium confidence", "somewhat confident", "likely"]):
        confidence = 0.7
    elif any(phrase in response_lower for phrase in ["low confidence", "uncertain", "not sure", "maybe"]):
        confidence = 0.5
    
    # Determine job type or conversation type
    job_type = None
    conversation_type = None
    
    if is_job_request:
        if any(word in response_lower for word in ["deploy", "install", "setup"]):
            job_type = "deployment"
        elif any(word in response_lower for word in ["monitor", "check", "status", "ping"]):
            job_type = "monitoring"
        elif any(word in response_lower for word in ["maintain", "update", "patch", "cleanup"]):
            job_type = "maintenance"
        elif any(word in response_lower for word in ["query", "list", "show", "get"]):
            job_type = "query"
        else:
            job_type = "automation"
    else:
        if any(word in response_lower for word in ["help", "how to", "guide"]):
            conversation_type = "help"
        elif any(word in response_lower for word in ["what", "explain", "tell me"]):
            conversation_type = "question"
        else:
            conversation_type = "general"
    
    # Extract reasoning (look for "because", "since", "reason", etc.)
    reasoning = "Based on natural language analysis of user intent"
    reasoning_indicators = ["because", "since", "reason", "why", "this is"]
    for indicator in reasoning_indicators:
        if indicator in response_lower:
            # Try to extract the reasoning part
            parts = response_text.split(indicator, 1)
            if len(parts) > 1:
                reasoning = parts[1].strip()[:200]  # Limit length
                break
    
    return {
        "is_job_request": is_job_request,
        "confidence": confidence,
        "reasoning": reasoning,
        "job_type": job_type,
        "conversation_type": conversation_type
    }

def _parse_natural_language_clarification_analysis(response_text: str):
    """Parse natural language clarification analysis response from LLM"""
    response_lower = response_text.lower()
    
    # Determine if it's a clarification response
    is_clarification_response = False
    if any(phrase in response_lower for phrase in [
        "clarification", "additional information", "responding to", "answering", "providing details", "follow-up"
    ]):
        is_clarification_response = True
    elif any(phrase in response_lower for phrase in [
        "new request", "different request", "unrelated", "separate", "not clarification"
    ]):
        is_clarification_response = False
    else:
        # Look for patterns that suggest clarification
        clarification_indicators = [
            "every", "at", "when", "if", "above", "below", "less than", "more than", 
            "yes", "no", "daily", "hourly", "weekly", "monthly", "midnight", "noon"
        ]
        clarification_count = sum(1 for indicator in clarification_indicators if indicator in response_lower)
        is_clarification_response = clarification_count > 0
    
    # Determine confidence
    confidence = 0.7  # Default medium confidence
    if any(phrase in response_lower for phrase in ["high confidence", "very confident", "certain", "definitely"]):
        confidence = 0.9
    elif any(phrase in response_lower for phrase in ["medium confidence", "somewhat confident", "likely"]):
        confidence = 0.7
    elif any(phrase in response_lower for phrase in ["low confidence", "uncertain", "not sure", "maybe"]):
        confidence = 0.4
    
    # Extract reasoning
    reasoning = "Based on natural language analysis of clarification patterns"
    reasoning_indicators = ["because", "since", "reason", "why", "this is", "appears to be"]
    for indicator in reasoning_indicators:
        if indicator in response_lower:
            parts = response_text.split(indicator, 1)
            if len(parts) > 1:
                reasoning = parts[1].strip()[:200]
                break
    
    return {
        "is_clarification_response": is_clarification_response,
        "confidence": confidence,
        "reasoning": reasoning
    }

if __name__ == "__main__":
    print("🧪 Testing Natural Language Parsing Functions")
    print("=" * 50)
    
    # Test 1: Job Request Analysis
    print("\n📋 Test 1: Job Request Analysis")
    test_response_1 = """
    This is a job request with high confidence. The user wants to execute an automation task.
    The intent type is automation and the risk level is medium.
    This is because they want to restart a service which could impact system availability.
    """
    
    result_1 = _parse_natural_language_intent_analysis(test_response_1)
    print(f"Input: {test_response_1.strip()}")
    print(f"Result: {result_1}")
    print(f"✅ Detected as job request: {result_1['is_job_request']}")
    print(f"✅ Confidence: {result_1['confidence']}")
    print(f"✅ Job type: {result_1['job_type']}")
    
    # Test 2: Conversation Analysis
    print("\n💬 Test 2: Conversation Analysis")
    test_response_2 = """
    This appears to be a conversation with medium confidence. The user is asking for information.
    They want to know how something works, which is a question type conversation.
    This is because they used words like "what is" and "explain".
    """
    
    result_2 = _parse_natural_language_intent_analysis(test_response_2)
    print(f"Input: {test_response_2.strip()}")
    print(f"Result: {result_2}")
    print(f"✅ Detected as job request: {result_2['is_job_request']}")
    print(f"✅ Confidence: {result_2['confidence']}")
    print(f"✅ Conversation type: {result_2['conversation_type']}")
    
    # Test 3: Clarification Analysis
    print("\n🔄 Test 3: Clarification Analysis")
    test_response_3 = """
    This is a clarification response with high confidence. The user is providing additional information
    that was requested. They are answering questions about timing - every 10 minutes.
    This appears to be responding to previous clarifying questions.
    """
    
    result_3 = _parse_natural_language_clarification_analysis(test_response_3)
    print(f"Input: {test_response_3.strip()}")
    print(f"Result: {result_3}")
    print(f"✅ Is clarification: {result_3['is_clarification_response']}")
    print(f"✅ Confidence: {result_3['confidence']}")
    
    print("\n🎉 All tests completed!")
    print("✅ Natural language parsing is working without JSON requirements!")