#!/usr/bin/env python3

import asyncio
import sys
import os
sys.path.append('/home/opsconductor/opsconductor-ng/shared')

from integrations.llm_client import LLMEngine
import json

async def test_intent_analysis():
    """Test the intent analysis directly"""
    
    # Initialize LLM engine
    ollama_host = os.getenv("OLLAMA_HOST", "http://ollama:11434")
    default_model = os.getenv("DEFAULT_MODEL", "llama3.2:3b")
    llm_engine = LLMEngine(ollama_host, default_model)
    
    await llm_engine.initialize()
    
    message = "run echo hello on localhost"
    
    analysis_prompt = f"""Analyze this user message and determine if they want to create an automation job or just have a conversation.

User message: "{message}"

CRITICAL RULE: If the user wants to RUN, EXECUTE, or PERFORM any command or action on any system (including localhost), this is ALWAYS a JOB REQUEST.

Respond with JSON only:
{{
    "is_job_request": true/false,
    "confidence": 0.0-1.0,
    "reasoning": "brief explanation",
    "job_type": "automation/deployment/monitoring/maintenance/query" (if job request),
    "conversation_type": "question/help/general" (if conversation)
}}

JOB REQUEST indicators (set is_job_request=true):
- Action verbs: restart, start, stop, deploy, install, configure, backup, monitor, update, upgrade, create, delete, remove, run, execute, automate
- Target mentions: server, service, application, database, container, VM, system, host, node, localhost
- Commands or operations to be performed (including simple commands like "echo")
- Infrastructure management tasks
- System administration requests
- ANY request to execute a command or script

CONVERSATION indicators (set is_job_request=false):
- Questions starting with: what, how, why, when, where (without requesting action)
- Requests for information, explanations, or help (without requesting action)
- General inquiries about system status (without requesting changes)
- Documentation or guidance requests (without requesting action)

Examples:
- "restart nginx service on server1" → JOB REQUEST (action: restart, target: service)
- "run echo hello on localhost" → JOB REQUEST (action: run, command: echo hello, target: localhost)
- "execute ls -la on server1" → JOB REQUEST (action: execute, command: ls -la, target: server1)
- "create a job that runs echo hello" → JOB REQUEST (action: create job, command: echo hello)
- "how does nginx work?" → CONVERSATION (question about how something works)
- "deploy application to production" → JOB REQUEST (action: deploy, target: application)
- "what is the status of server1?" → CONVERSATION (information request without action)"""

    print(f"🔍 Testing intent analysis for: '{message}'")
    print(f"📤 Sending prompt to LLM...")
    
    llm_response = await llm_engine.generate(analysis_prompt)
    print(f"📥 LLM Response: {llm_response}")
    
    # Extract the generated text from the LLM response
    if isinstance(llm_response, dict) and "generated_text" in llm_response:
        generated_text = llm_response["generated_text"]
    else:
        generated_text = str(llm_response)
    
    print(f"📝 Generated Text: {generated_text}")
    
    # Try to parse as JSON
    try:
        analysis = json.loads(generated_text)
        print(f"✅ Parsed Analysis: {analysis}")
        
        is_job_request = analysis.get("is_job_request", False)
        confidence = analysis.get("confidence", 0.0)
        reasoning = analysis.get("reasoning", "No reasoning provided")
        
        print(f"🎯 Result:")
        print(f"  Is Job Request: {is_job_request}")
        print(f"  Confidence: {confidence}")
        print(f"  Reasoning: {reasoning}")
        
    except json.JSONDecodeError as e:
        print(f"❌ JSON parsing failed: {e}")
        print(f"📄 Raw response: {generated_text}")

if __name__ == "__main__":
    asyncio.run(test_intent_analysis())