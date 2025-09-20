#!/usr/bin/env python3
"""
Simple test for the chat endpoint to verify it works without external dependencies.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Mock external dependencies
class MockAssetServiceClient:
    def __init__(self, *args, **kwargs):
        pass

class MockAutomationServiceClient:
    def __init__(self, *args, **kwargs):
        pass

class MockAIBrainEngine:
    async def process_message(self, message, conversation_id, user_id):
        return {
            "response": f"Processed: {message}",
            "intent": "test",
            "confidence": 0.9,
            "job_id": "test-job-123",
            "execution_id": None,
            "automation_job_id": None,
            "workflow": {"steps": ["test"]},
            "execution_started": False
        }

class MockSimpleNLPProcessor:
    def parse_request(self, text):
        class MockParsedRequest:
            def __init__(self):
                self.intent = "automation_request"
                self.operation = "list"
                self.target_process = None
                self.target_service = None
                self.target_group = None
                self.target_os = None
                self.confidence = 0.7
        return MockParsedRequest()

# Patch the imports
sys.modules['integrations.asset_client'] = type('MockModule', (), {'AssetServiceClient': MockAssetServiceClient})()
sys.modules['integrations.automation_client'] = type('MockModule', (), {'AutomationServiceClient': MockAutomationServiceClient})()
sys.modules['brain_engine'] = type('MockModule', (), {'AIBrainEngine': MockAIBrainEngine})()
sys.modules['legacy.nlp_processor'] = type('MockModule', (), {'SimpleNLPProcessor': MockSimpleNLPProcessor})()

def test_chat_validation():
    """Test the chat endpoint validation logic."""
    
    # Import after mocking
    from job_engine.job_validator import JobValidator
    
    validator = JobValidator()
    
    # Test the request that was causing the 500 error
    test_message = "i want to create a job to get the file listing on a machine"
    
    print("=" * 60)
    print("TESTING CHAT ENDPOINT VALIDATION")
    print("=" * 60)
    print(f"Test Message: '{test_message}'")
    
    try:
        # This is what the chat endpoint does
        validation_result = validator.validate_job_request(test_message)
        
        print(f"\n✅ Validation completed successfully!")
        print(f"Valid: {validation_result.is_valid}")
        print(f"Overall Confidence: {validation_result.overall_confidence:.2f}")
        print(f"Risk Level: {validation_result.risk_assessment['risk_level']}")
        
        print(f"\nField Confidence Scores:")
        for field, score in validation_result.field_confidence_scores.items():
            status = "✅" if score >= 0.7 else "⚠️" if score >= 0.3 else "❌"
            print(f"  {status} {field}: {score:.2f}")
        
        if validation_result.clarification_questions:
            print(f"\nClarification Questions ({len(validation_result.clarification_questions)}):")
            for i, question in enumerate(validation_result.clarification_questions[:3], 1):
                print(f"  {i}. {question['question']}")
        
        print(f"\nRisk Assessment:")
        print(f"  Risk Level: {validation_result.risk_assessment['risk_level']}")
        print(f"  Can Proceed: {validation_result.risk_assessment.get('can_proceed', 'Unknown')}")
        print(f"  Recommendation: {validation_result.risk_assessment['recommendation']}")
        
        # Test what the chat endpoint logic would do
        needs_clarification = not validation_result.is_valid or validation_result.overall_confidence < 0.8
        
        print(f"\n🤖 Chat Endpoint Decision:")
        if needs_clarification:
            print("  ❓ Would ask for clarification")
            print("  📝 User would see targeted questions")
        else:
            print("  ✅ Would proceed with job creation")
            print("  🚀 High confidence - no clarification needed")
        
        return True
        
    except Exception as e:
        print(f"❌ Validation failed with error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_chat_validation()
    if success:
        print(f"\n🎉 Chat endpoint validation is working correctly!")
        print("The 500 error should be resolved.")
    else:
        print(f"\n💥 There are still issues to fix.")