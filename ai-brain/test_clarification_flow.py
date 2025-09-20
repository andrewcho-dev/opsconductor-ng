#!/usr/bin/env python3
"""
Test script to demonstrate the AI clarification flow
"""

import asyncio
import json
import sys
from pathlib import Path

# Add the ai-brain directory to the path
sys.path.insert(0, str(Path(__file__).parent))

from intent_engine.clarification_manager import ClarificationManager
from intent_engine.conversation_manager import ConversationManager
from job_engine.job_validator import JobValidator
from nlp_engine.nlp_processor import NLPProcessor

async def test_clarification_flow():
    """Test the complete clarification flow"""
    
    print("🤖 AI Clarification Flow Test")
    print("=" * 50)
    
    # Initialize components
    conversation_manager = ConversationManager()
    clarification_manager = ClarificationManager(conversation_manager)
    validator = JobValidator()
    nlp_processor = NLPProcessor()
    
    # Test scenarios
    test_scenarios = [
        {
            "name": "Vague Request",
            "request": "restart something on the servers",
            "conversation_id": "test-conv-1"
        },
        {
            "name": "Missing Target",
            "request": "restart apache service",
            "conversation_id": "test-conv-2"
        },
        {
            "name": "Complete Request",
            "request": "restart apache2 service on web-servers group",
            "conversation_id": "test-conv-3"
        },
        {
            "name": "Ambiguous Operation",
            "request": "fix the database issues on prod servers",
            "conversation_id": "test-conv-4"
        }
    ]
    
    for scenario in test_scenarios:
        print(f"\n📝 Testing: {scenario['name']}")
        print(f"Request: '{scenario['request']}'")
        print("-" * 40)
        
        # Parse the request
        parsed_request = nlp_processor.parse_request(scenario['request'])
        print(f"Parsed Intent: {parsed_request.intent}")
        print(f"Operation: {parsed_request.operation}")
        print(f"Target: {parsed_request.target_service or parsed_request.target_process or 'None'}")
        print(f"Group: {parsed_request.target_group or 'None'}")
        
        # Validate the request
        requirements = {
            "description": scenario['request'],
            "operation": parsed_request.operation,
            "target_process": parsed_request.target_process,
            "target_service": parsed_request.target_service,
            "target_group": parsed_request.target_group,
            "target_os": parsed_request.target_os
        }
        
        validation_result = await validator.validate_job_request(
            intent_type=parsed_request.intent,
            requirements=requirements,
            target_systems=[]
        )
        
        print(f"Validation Score: {validation_result.confidence_score:.2f}")
        print(f"Is Valid: {validation_result.is_valid}")
        
        if validation_result.issues:
            print("Issues found:")
            for issue in validation_result.issues:
                print(f"  - {issue.level.value}: {issue.message}")
        
        # Check if clarification is needed
        needs_clarification = await clarification_manager.needs_clarification(
            request=scenario['request'],
            parsed_request=parsed_request,
            validation_result=validation_result
        )
        
        print(f"Needs Clarification: {needs_clarification}")
        
        if needs_clarification:
            # Start clarification process
            clarification_state = await clarification_manager.start_clarification(
                conversation_id=scenario['conversation_id'],
                original_request=scenario['request'],
                parsed_request=parsed_request,
                validation_result=validation_result
            )
            
            print(f"🤔 Clarification Question:")
            print(f"   {clarification_state.current_question}")
            
            # Simulate user responses
            if "restart something" in scenario['request']:
                # Simulate answering the vague request
                print(f"👤 User Response: 'apache2 service'")
                updated_state = await clarification_manager.process_clarification_response(
                    conversation_id=scenario['conversation_id'],
                    response="apache2 service"
                )
                
                if updated_state.status == "pending":
                    print(f"🤔 Next Question:")
                    print(f"   {updated_state.current_question}")
                    print(f"👤 User Response: 'web-servers'")
                    
                    final_state = await clarification_manager.process_clarification_response(
                        conversation_id=scenario['conversation_id'],
                        response="web-servers"
                    )
                    
                    if final_state.status == "complete":
                        print("✅ Clarification Complete!")
                        print("Final Requirements:")
                        for key, value in final_state.clarified_requirements.items():
                            if value:
                                print(f"  {key}: {value}")
            
            elif "missing target" in scenario['name'].lower():
                print(f"👤 User Response: 'web-servers group'")
                updated_state = await clarification_manager.process_clarification_response(
                    conversation_id=scenario['conversation_id'],
                    response="web-servers group"
                )
                
                if updated_state.status == "complete":
                    print("✅ Clarification Complete!")
                    print("Final Requirements:")
                    for key, value in updated_state.clarified_requirements.items():
                        if value:
                            print(f"  {key}: {value}")
            
            # Clean up
            await clarification_manager.clear_clarification_state(scenario['conversation_id'])
        else:
            print("✅ Request is clear enough to proceed!")
        
        print()

async def test_validation_scenarios():
    """Test various validation scenarios"""
    
    print("\n🔍 Validation Test Scenarios")
    print("=" * 50)
    
    validator = JobValidator()
    
    validation_tests = [
        {
            "name": "PowerShell Syntax Error",
            "requirements": {
                "description": "run command with bash syntax in powershell",
                "operation": "execute",
                "commands": ["Get-Process && Stop-Process -Name notepad"],
                "target_os": "windows"
            }
        },
        {
            "name": "Dangerous Command",
            "requirements": {
                "description": "format the hard drive",
                "operation": "execute",
                "commands": ["format C: /q"],
                "target_os": "windows"
            }
        },
        {
            "name": "OS Compatibility Issue",
            "requirements": {
                "description": "restart systemd service on windows",
                "operation": "restart",
                "target_service": "apache2",
                "target_os": "windows"
            }
        },
        {
            "name": "Valid Request",
            "requirements": {
                "description": "restart apache service on linux servers",
                "operation": "restart",
                "target_service": "apache2",
                "target_os": "linux"
            }
        }
    ]
    
    for test in validation_tests:
        print(f"\n📋 Testing: {test['name']}")
        print(f"Description: {test['requirements']['description']}")
        
        validation_result = await validator.validate_job_request(
            intent_type="automation_request",
            requirements=test['requirements'],
            target_systems=["test-server-1"]
        )
        
        print(f"Valid: {validation_result.is_valid}")
        print(f"Confidence: {validation_result.confidence_score:.2f}")
        
        if validation_result.issues:
            print("Issues:")
            for issue in validation_result.issues:
                print(f"  - {issue.level.value}: {issue.message}")
                if issue.suggestion:
                    print(f"    Suggestion: {issue.suggestion}")

if __name__ == "__main__":
    print("Starting AI Clarification and Validation Tests...")
    
    asyncio.run(test_clarification_flow())
    asyncio.run(test_validation_scenarios())
    
    print("\n✅ All tests completed!")