#!/usr/bin/env python3
"""
Simple test to demonstrate the enhanced targeted clarification system
without external dependencies.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Mock the external dependencies
class MockAssetServiceClient:
    def __init__(self, *args, **kwargs):
        pass

class MockHttpx:
    class AsyncClient:
        def __init__(self, *args, **kwargs):
            pass

# Patch the imports
sys.modules['httpx'] = MockHttpx()
sys.modules['integrations.asset_client'] = type('MockModule', (), {'AssetServiceClient': MockAssetServiceClient})()

from job_engine.job_validator import JobValidator, ValidationResult

def test_enhanced_clarification():
    """Test the enhanced clarification system with various scenarios."""
    
    validator = JobValidator()
    
    print("=" * 80)
    print("ENHANCED TARGETED CLARIFICATION SYSTEM DEMONSTRATION")
    print("=" * 80)
    
    # Test Case 1: Very vague request
    print("\n" + "=" * 50)
    print("TEST CASE 1: Very Vague Request")
    print("=" * 50)
    print("User Request: 'I need to automate something'")
    
    result = validator.validate_job_request("I need to automate something")
    
    print(f"\nValidation Result:")
    print(f"- Valid: {result.is_valid}")
    print(f"- Overall Confidence: {result.overall_confidence:.2f}")
    print(f"- Risk Level: {result.risk_assessment['risk_level']}")
    
    print(f"\nField Confidence Scores:")
    for field, score in result.field_confidence_scores.items():
        print(f"  {field}: {score:.2f}")
    
    print(f"\nTargeted Clarification Questions ({len(result.clarification_questions)}):")
    for i, question in enumerate(result.clarification_questions, 1):
        print(f"\n{i}. {question['question']}")
        if question.get('explanation'):
            print(f"   Explanation: {question['explanation']}")
        if question.get('risk_warning'):
            print(f"   ⚠️  Risk: {question['risk_warning']}")
    
    print(f"\nRisk Assessment:")
    print(f"- Overall Risk: {result.risk_assessment['risk_level']}")
    print(f"- Recommendation: {result.risk_assessment['recommendation']}")
    if result.risk_assessment['critical_issues']:
        print("- Critical Issues:")
        for issue in result.risk_assessment['critical_issues']:
            print(f"  • {issue}")
    
    # Test Case 2: Partially complete request
    print("\n" + "=" * 50)
    print("TEST CASE 2: Partially Complete Request")
    print("=" * 50)
    print("User Request: 'Deploy my web application to production'")
    
    result = validator.validate_job_request("Deploy my web application to production")
    
    print(f"\nValidation Result:")
    print(f"- Valid: {result.is_valid}")
    print(f"- Overall Confidence: {result.overall_confidence:.2f}")
    print(f"- Risk Level: {result.risk_assessment['risk_level']}")
    
    print(f"\nField Confidence Scores:")
    for field, score in result.field_confidence_scores.items():
        if score < 0.8:  # Only show low confidence fields
            print(f"  {field}: {score:.2f} (LOW)")
    
    print(f"\nTargeted Clarification Questions ({len(result.clarification_questions)}):")
    for i, question in enumerate(result.clarification_questions[:3], 1):  # Show first 3
        print(f"\n{i}. {question['question']}")
        if question.get('risk_warning'):
            print(f"   ⚠️  Risk: {question['risk_warning']}")
    
    # Test Case 3: Well-defined request
    print("\n" + "=" * 50)
    print("TEST CASE 3: Well-Defined Request")
    print("=" * 50)
    print("User Request: 'Deploy my Node.js application from GitHub repo https://github.com/user/app to AWS EC2 instance i-1234567890abcdef0 using Docker'")
    
    result = validator.validate_job_request("Deploy my Node.js application from GitHub repo https://github.com/user/app to AWS EC2 instance i-1234567890abcdef0 using Docker")
    
    print(f"\nValidation Result:")
    print(f"- Valid: {result.is_valid}")
    print(f"- Overall Confidence: {result.overall_confidence:.2f}")
    print(f"- Risk Level: {result.risk_assessment['risk_level']}")
    
    if result.clarification_questions:
        print(f"\nRemaining Questions ({len(result.clarification_questions)}):")
        for i, question in enumerate(result.clarification_questions[:2], 1):
            print(f"{i}. {question['question']}")
    else:
        print("\n✅ No clarification questions needed!")
    
    print(f"\nRisk Assessment: {result.risk_assessment['recommendation']}")

if __name__ == "__main__":
    test_enhanced_clarification()