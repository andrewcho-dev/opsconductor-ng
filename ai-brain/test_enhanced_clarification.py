#!/usr/bin/env python3
"""
Enhanced Clarification System Test Script

This script demonstrates the new granular field-level confidence scoring and 
targeted clarification system that provides intelligent risk assessment and 
user guidance.

Key Features Tested:
1. Granular field-level confidence scoring
2. Targeted clarification questions based on specific missing/unclear fields
3. Risk assessment with detailed warnings and recommendations
4. User choice to proceed with risks or provide more information
5. Progressive clarification (most critical fields first)
"""

import asyncio
import json
from typing import Dict, Any, List
from job_engine.job_validator import JobValidator, ValidationResult
from intent_engine.nlp_processor import SimpleNLPProcessor

class EnhancedClarificationDemo:
    """Demonstration of the enhanced clarification system"""
    
    def __init__(self):
        self.validator = JobValidator()
        self.nlp_processor = SimpleNLPProcessor()
    
    async def run_demo(self):
        """Run comprehensive demonstration of enhanced clarification features"""
        print("🚀 Enhanced AI Clarification System Demo")
        print("=" * 60)
        
        # Test scenarios with different levels of completeness and clarity
        test_scenarios = [
            {
                "name": "Completely Vague Request",
                "request": "restart some service",
                "expected_risk": "HIGH",
                "description": "Missing critical information: target systems, specific service"
            },
            {
                "name": "Partially Clear Request", 
                "request": "restart apache on web servers",
                "expected_risk": "MEDIUM",
                "description": "Has service and general target, but 'web servers' is vague"
            },
            {
                "name": "Mostly Complete Request",
                "request": "restart httpd service on web01.example.com",
                "expected_risk": "LOW",
                "description": "Specific service and target, should have high confidence"
            },
            {
                "name": "Ambiguous Service Name",
                "request": "start the database on db-server",
                "expected_risk": "MEDIUM", 
                "description": "Vague service name 'database', unclear target"
            },
            {
                "name": "Dangerous Operation",
                "request": "delete all files in /tmp on all servers",
                "expected_risk": "HIGH",
                "description": "Potentially dangerous operation with broad target"
            }
        ]
        
        for i, scenario in enumerate(test_scenarios, 1):
            print(f"\n📋 Test Scenario {i}: {scenario['name']}")
            print(f"Request: '{scenario['request']}'")
            print(f"Expected Risk Level: {scenario['expected_risk']}")
            print(f"Description: {scenario['description']}")
            print("-" * 50)
            
            await self.test_scenario(scenario)
            
            print("\n" + "="*60)
    
    async def test_scenario(self, scenario: Dict[str, Any]):
        """Test a specific scenario and demonstrate the enhanced clarification system"""
        
        # 1. Parse the request
        parsed_request = self.nlp_processor.parse_request(scenario['request'])
        print(f"🔍 Parsed Intent: {parsed_request.intent}")
        
        # 2. Prepare requirements for validation
        requirements = {
            "description": scenario['request'],
            "operation": parsed_request.operation,
            "target_process": parsed_request.target_process,
            "target_service": parsed_request.target_service,
            "target_group": parsed_request.target_group,
            "target_os": parsed_request.target_os,
            "service_name": parsed_request.target_service,
            "action": parsed_request.operation
        }
        
        # Add target systems if we can infer them
        target_systems = []
        if parsed_request.target_group:
            # Simulate some target resolution
            if "web" in parsed_request.target_group.lower():
                target_systems = ["web01.example.com", "web02.example.com"]
            elif "db" in parsed_request.target_group.lower():
                target_systems = ["db01.example.com"]
            elif "all" in parsed_request.target_group.lower():
                target_systems = ["web01.example.com", "web02.example.com", "db01.example.com", "app01.example.com"]
        
        # 3. Validate the request
        validation_result = await self.validator.validate_job_request(
            intent_type=parsed_request.intent,
            requirements=requirements,
            target_systems=target_systems
        )
        
        # 4. Display validation results
        await self.display_validation_results(validation_result)
        
        # 5. Demonstrate targeted clarification questions
        await self.demonstrate_targeted_questions(validation_result, requirements, parsed_request.intent)
        
        # 6. Show risk assessment and user options
        await self.demonstrate_risk_assessment(validation_result)
    
    async def display_validation_results(self, result: ValidationResult):
        """Display comprehensive validation results"""
        print(f"✅ Overall Confidence: {result.confidence_score:.2f}")
        print(f"📊 Valid: {result.is_valid}")
        
        if result.field_confidence_scores:
            print("\n🎯 Field-Level Confidence Scores:")
            for field, scores in result.field_confidence_scores.items():
                confidence = scores['confidence']
                weight = scores['weight']
                weighted_score = scores['weighted_score']
                
                # Color coding based on confidence
                if confidence >= 0.8:
                    status = "🟢 HIGH"
                elif confidence >= 0.6:
                    status = "🟡 MEDIUM"
                else:
                    status = "🔴 LOW"
                
                print(f"  {field}: {confidence:.2f} {status} (weight: {weight:.1%}, weighted: {weighted_score:.2f})")
        
        if result.issues:
            print(f"\n⚠️  Validation Issues ({len(result.issues)}):")
            for issue in result.issues:
                level_icon = {"CRITICAL": "🚨", "ERROR": "❌", "WARNING": "⚠️"}.get(issue.level.value, "ℹ️")
                print(f"  {level_icon} {issue.level.value}: {issue.message}")
                if issue.suggestion:
                    print(f"     💡 Suggestion: {issue.suggestion}")
    
    async def demonstrate_targeted_questions(self, result: ValidationResult, requirements: Dict[str, Any], intent_type: str):
        """Demonstrate the targeted clarification question generation"""
        
        if not result.field_confidence_scores:
            return
        
        # Generate targeted questions
        targeted_questions = self.validator.generate_targeted_clarification_questions(
            result.field_confidence_scores, intent_type, requirements
        )
        
        if targeted_questions:
            print(f"\n🎯 Targeted Clarification Questions ({len(targeted_questions)}):")
            for i, question in enumerate(targeted_questions, 1):
                priority_icon = {"critical": "🚨", "high": "⚠️", "medium": "ℹ️"}.get(question.get('priority', 'medium'), "❓")
                print(f"\n  {priority_icon} Question {i} (Priority: {question.get('priority', 'medium').upper()}):")
                print(f"     Field: {question.get('field', 'unknown')}")
                print(f"     Question: {question['question']}")
                
                if question.get('explanation'):
                    print(f"     Explanation: {question['explanation']}")
                
                if question.get('options'):
                    print(f"     Options: {', '.join(question['options'])}")
                
                if question.get('risk_warning'):
                    print(f"     ⚠️ Risk Warning: {question['risk_warning']}")
        else:
            print("\n✅ No targeted clarification questions needed")
    
    async def demonstrate_risk_assessment(self, result: ValidationResult):
        """Demonstrate the risk assessment system"""
        
        if not result.risk_assessment:
            print("\n📊 No risk assessment available")
            return
        
        risk = result.risk_assessment
        print(f"\n🛡️  Risk Assessment:")
        
        # Risk level with appropriate icon
        risk_icons = {
            "MINIMAL": "🟢",
            "LOW": "🟡", 
            "MEDIUM": "🟠",
            "HIGH": "🔴",
            "CRITICAL": "🚨"
        }
        risk_icon = risk_icons.get(risk['risk_level'], "❓")
        
        print(f"   Risk Level: {risk_icon} {risk['risk_level']}")
        print(f"   Overall Confidence: {risk['overall_confidence']:.2f}")
        print(f"   Recommendation: {risk['recommendation']}")
        print(f"   Can Proceed: {'✅ Yes' if risk['can_proceed'] else '❌ No'}")
        print(f"   Should Clarify: {'⚠️ Yes' if risk['should_clarify'] else '✅ No'}")
        
        if risk.get('critical_issues'):
            print(f"\n   🚨 Critical Issues ({len(risk['critical_issues'])}):")
            for issue in risk['critical_issues']:
                print(f"     • {issue['message']}")
                print(f"       Impact: {issue['impact']}")
        
        if risk.get('warnings'):
            print(f"\n   ⚠️ Warnings ({len(risk['warnings'])}):")
            for warning in risk['warnings']:
                print(f"     • {warning['message']}")
                print(f"       Impact: {warning['impact']}")
        
        # Show user options based on risk level
        await self.show_user_options(risk)
    
    async def show_user_options(self, risk_assessment: Dict[str, Any]):
        """Show what options the user would have based on risk assessment"""
        
        print(f"\n🎮 User Options:")
        
        if risk_assessment['can_proceed']:
            if risk_assessment['should_clarify']:
                print("   1. ✅ Provide more information (Recommended)")
                print("   2. ⚠️ Proceed with current information (with risk acknowledgment)")
                print("   3. ❌ Cancel the request")
            else:
                print("   1. ✅ Proceed with job creation")
                print("   2. ℹ️ Provide additional details (optional)")
                print("   3. ❌ Cancel the request")
        else:
            print("   1. ✅ Provide required information")
            print("   2. ❌ Cancel the request")
            print("   ⚠️ Cannot proceed without addressing critical issues")
        
        # Show what API endpoints would be available
        print(f"\n🔗 Available API Endpoints:")
        print("   • POST /ai/chat - Continue clarification conversation")
        print("   • GET /ai/risk-assessment/{conversation_id} - Get detailed risk info")
        
        if risk_assessment['can_proceed']:
            print("   • POST /ai/proceed-with-risk - Acknowledge risks and proceed")
            print("   • POST /ai/skip-clarification/{conversation_id} - Skip remaining questions")

async def main():
    """Run the enhanced clarification system demonstration"""
    demo = EnhancedClarificationDemo()
    await demo.run_demo()
    
    print("\n🎉 Demo Complete!")
    print("\nKey Benefits of Enhanced System:")
    print("✅ Granular field-level confidence scoring")
    print("✅ Targeted questions for specific missing information")
    print("✅ Clear risk assessment with actionable recommendations")
    print("✅ User choice to proceed with informed consent")
    print("✅ Progressive clarification (most critical fields first)")
    print("✅ Rich API responses with detailed validation information")

if __name__ == "__main__":
    asyncio.run(main())