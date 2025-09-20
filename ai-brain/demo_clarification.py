#!/usr/bin/env python3
"""
Direct demonstration of the enhanced clarification system methods.
"""

import re
from dataclasses import dataclass
from typing import Dict, List, Any, Optional

@dataclass
class ValidationResult:
    is_valid: bool
    overall_confidence: float
    field_confidence_scores: Dict[str, float]
    clarification_questions: List[Dict[str, Any]]
    risk_assessment: Dict[str, Any]
    validation_issues: List[str] = None

class JobValidatorDemo:
    """Simplified version to demonstrate the clarification system."""
    
    def __init__(self):
        self.field_weights = {
            'job_type': 0.25,
            'source_location': 0.20,
            'target_location': 0.20,
            'technology_stack': 0.15,
            'environment': 0.10,
            'authentication': 0.10
        }
    
    def extract_job_fields(self, request: str) -> Dict[str, Any]:
        """Extract job fields from request."""
        fields = {}
        request_lower = request.lower()
        
        # Job type detection
        if any(word in request_lower for word in ['deploy', 'deployment']):
            fields['job_type'] = 'deployment'
        elif any(word in request_lower for word in ['backup', 'backup']):
            fields['job_type'] = 'backup'
        elif any(word in request_lower for word in ['test', 'testing']):
            fields['job_type'] = 'testing'
        else:
            fields['job_type'] = None
        
        # Source location
        if 'github' in request_lower or 'git' in request_lower:
            fields['source_location'] = 'git_repository'
        elif any(word in request_lower for word in ['s3', 'bucket']):
            fields['source_location'] = 's3'
        else:
            fields['source_location'] = None
        
        # Target location
        if any(word in request_lower for word in ['aws', 'ec2', 'instance']):
            fields['target_location'] = 'aws_ec2'
        elif any(word in request_lower for word in ['kubernetes', 'k8s']):
            fields['target_location'] = 'kubernetes'
        else:
            fields['target_location'] = None
        
        # Technology stack
        if any(word in request_lower for word in ['node', 'nodejs', 'javascript']):
            fields['technology_stack'] = 'nodejs'
        elif any(word in request_lower for word in ['python', 'django', 'flask']):
            fields['technology_stack'] = 'python'
        elif any(word in request_lower for word in ['docker', 'container']):
            fields['technology_stack'] = 'docker'
        else:
            fields['technology_stack'] = None
        
        # Environment
        if 'production' in request_lower:
            fields['environment'] = 'production'
        elif any(word in request_lower for word in ['staging', 'test']):
            fields['environment'] = 'staging'
        else:
            fields['environment'] = None
        
        # Authentication (usually missing)
        fields['authentication'] = None
        
        return fields
    
    def calculate_field_confidence(self, field_name: str, field_value: Any, request: str) -> float:
        """Calculate confidence score for a field."""
        if field_value is None:
            return 0.0
        
        # Simple confidence calculation based on specificity
        if field_name == 'source_location':
            if 'github.com' in request or re.search(r'https?://[^\s]+', request):
                return 0.9
            elif field_value:
                return 0.6
        
        elif field_name == 'target_location':
            if re.search(r'i-[a-f0-9]+', request):  # EC2 instance ID
                return 0.9
            elif field_value:
                return 0.7
        
        elif field_name == 'job_type':
            return 0.8 if field_value else 0.0
        
        elif field_name == 'technology_stack':
            return 0.7 if field_value else 0.0
        
        elif field_name == 'environment':
            return 0.8 if field_value else 0.0
        
        elif field_name == 'authentication':
            return 0.0  # Usually missing
        
        return 0.5 if field_value else 0.0
    
    def generate_targeted_clarification_questions(self, fields: Dict[str, Any], 
                                                field_confidence_scores: Dict[str, float]) -> List[Dict[str, Any]]:
        """Generate targeted clarification questions based on confidence scores."""
        questions = []
        
        # Sort fields by importance (weight) and low confidence
        critical_fields = []
        for field, weight in self.field_weights.items():
            confidence = field_confidence_scores.get(field, 0.0)
            if confidence < 0.7:  # Low confidence threshold
                critical_fields.append((field, weight, confidence))
        
        # Sort by weight (descending) then by confidence (ascending)
        critical_fields.sort(key=lambda x: (-x[1], x[2]))
        
        for field, weight, confidence in critical_fields[:5]:  # Top 5 most critical
            question_data = self._generate_field_question(field, fields.get(field), confidence)
            if question_data:
                questions.append(question_data)
        
        return questions
    
    def _generate_field_question(self, field: str, current_value: Any, confidence: float) -> Optional[Dict[str, Any]]:
        """Generate a specific question for a field."""
        
        if field == 'job_type':
            return {
                'field': field,
                'question': 'What type of automation job do you want to create?',
                'options': ['Deployment', 'Backup', 'Testing', 'Data Migration', 'Monitoring Setup'],
                'explanation': 'The job type determines which automation workflow will be used.',
                'risk_warning': 'Without knowing the job type, the system cannot create an appropriate automation workflow.'
            }
        
        elif field == 'source_location':
            return {
                'field': field,
                'question': 'Where is your source code or data located?',
                'options': ['GitHub repository', 'GitLab repository', 'S3 bucket', 'Local file system', 'Other'],
                'explanation': 'We need to know where to get your code/data from.',
                'risk_warning': 'Without source location, the automation cannot access your code or data.'
            }
        
        elif field == 'target_location':
            return {
                'field': field,
                'question': 'Where do you want to deploy or process your application?',
                'options': ['AWS EC2', 'AWS ECS', 'Kubernetes cluster', 'Azure VM', 'Google Cloud', 'On-premises server'],
                'explanation': 'The target location determines deployment strategy and configuration.',
                'risk_warning': 'Without target location, the system cannot determine where to deploy your application.'
            }
        
        elif field == 'technology_stack':
            return {
                'field': field,
                'question': 'What technology stack is your application built with?',
                'options': ['Node.js', 'Python (Django/Flask)', 'Java (Spring)', 'Docker container', '.NET', 'PHP'],
                'explanation': 'Technology stack determines build and deployment processes.',
                'risk_warning': 'Incorrect technology detection may result in failed deployments.'
            }
        
        elif field == 'environment':
            return {
                'field': field,
                'question': 'Which environment are you targeting?',
                'options': ['Production', 'Staging', 'Development', 'Testing'],
                'explanation': 'Environment affects security settings, resource allocation, and deployment strategies.',
                'risk_warning': 'Wrong environment selection could impact security and performance.'
            }
        
        elif field == 'authentication':
            return {
                'field': field,
                'question': 'What authentication credentials should be used?',
                'options': ['AWS IAM role', 'Service account', 'API keys', 'SSH keys', 'Username/password'],
                'explanation': 'Authentication is required to access target systems securely.',
                'risk_warning': 'Missing authentication will prevent the automation from accessing target systems.'
            }
        
        return None
    
    def generate_risk_assessment(self, field_confidence_scores: Dict[str, float]) -> Dict[str, Any]:
        """Generate comprehensive risk assessment."""
        
        # Calculate weighted confidence
        total_weight = 0
        weighted_confidence = 0
        
        for field, weight in self.field_weights.items():
            confidence = field_confidence_scores.get(field, 0.0)
            weighted_confidence += confidence * weight
            total_weight += weight
        
        overall_confidence = weighted_confidence / total_weight if total_weight > 0 else 0
        
        # Determine risk level
        if overall_confidence >= 0.9:
            risk_level = "MINIMAL"
        elif overall_confidence >= 0.7:
            risk_level = "LOW"
        elif overall_confidence >= 0.5:
            risk_level = "MEDIUM"
        elif overall_confidence >= 0.3:
            risk_level = "HIGH"
        else:
            risk_level = "CRITICAL"
        
        # Generate recommendations
        critical_issues = []
        for field, weight in self.field_weights.items():
            confidence = field_confidence_scores.get(field, 0.0)
            if confidence < 0.3 and weight > 0.15:  # Critical field with very low confidence
                critical_issues.append(f"Missing or unclear {field.replace('_', ' ')} (critical for automation success)")
        
        # Risk-based recommendations
        if risk_level in ["CRITICAL", "HIGH"]:
            recommendation = "❌ NOT RECOMMENDED to proceed. Please provide more information."
        elif risk_level == "MEDIUM":
            recommendation = "⚠️ PROCEED WITH CAUTION. Consider providing more details for better results."
        else:
            recommendation = "✅ SAFE TO PROCEED with current information."
        
        return {
            'risk_level': risk_level,
            'overall_confidence': overall_confidence,
            'recommendation': recommendation,
            'critical_issues': critical_issues,
            'can_proceed': risk_level not in ["CRITICAL", "HIGH"]
        }
    
    def validate_job_request(self, request: str) -> ValidationResult:
        """Main validation method with enhanced clarification."""
        
        # Extract fields
        fields = self.extract_job_fields(request)
        
        # Calculate field confidence scores
        field_confidence_scores = {}
        for field, value in fields.items():
            confidence = self.calculate_field_confidence(field, value, request)
            field_confidence_scores[field] = confidence
        
        # Calculate overall confidence
        total_weight = sum(self.field_weights.values())
        overall_confidence = sum(
            field_confidence_scores.get(field, 0) * weight 
            for field, weight in self.field_weights.items()
        ) / total_weight
        
        # Generate targeted clarification questions
        clarification_questions = self.generate_targeted_clarification_questions(
            fields, field_confidence_scores
        )
        
        # Generate risk assessment
        risk_assessment = self.generate_risk_assessment(field_confidence_scores)
        
        # Determine if valid (high confidence and no critical missing fields)
        is_valid = overall_confidence >= 0.8 and len(clarification_questions) <= 2
        
        return ValidationResult(
            is_valid=is_valid,
            overall_confidence=overall_confidence,
            field_confidence_scores=field_confidence_scores,
            clarification_questions=clarification_questions,
            risk_assessment=risk_assessment
        )

def demonstrate_enhanced_clarification():
    """Demonstrate the enhanced clarification system."""
    
    validator = JobValidatorDemo()
    
    print("=" * 80)
    print("ENHANCED TARGETED CLARIFICATION SYSTEM DEMONSTRATION")
    print("=" * 80)
    
    test_cases = [
        {
            'name': 'Very Vague Request',
            'request': 'I need to automate something'
        },
        {
            'name': 'Partially Complete Request', 
            'request': 'Deploy my web application to production'
        },
        {
            'name': 'Well-Defined Request',
            'request': 'Deploy my Node.js application from GitHub repo https://github.com/user/app to AWS EC2 instance i-1234567890abcdef0 using Docker'
        }
    ]
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\n{'='*50}")
        print(f"TEST CASE {i}: {test_case['name']}")
        print(f"{'='*50}")
        print(f"User Request: '{test_case['request']}'")
        
        result = validator.validate_job_request(test_case['request'])
        
        print(f"\n📊 VALIDATION RESULTS:")
        print(f"   Valid: {result.is_valid}")
        print(f"   Overall Confidence: {result.overall_confidence:.2f}")
        print(f"   Risk Level: {result.risk_assessment['risk_level']}")
        
        print(f"\n📈 FIELD CONFIDENCE SCORES:")
        for field, score in result.field_confidence_scores.items():
            status = "✅" if score >= 0.7 else "⚠️" if score >= 0.3 else "❌"
            print(f"   {status} {field.replace('_', ' ').title()}: {score:.2f}")
        
        if result.clarification_questions:
            print(f"\n❓ TARGETED CLARIFICATION QUESTIONS ({len(result.clarification_questions)}):")
            for j, question in enumerate(result.clarification_questions, 1):
                print(f"\n   {j}. {question['question']}")
                if question.get('explanation'):
                    print(f"      💡 {question['explanation']}")
                if question.get('risk_warning'):
                    print(f"      ⚠️  {question['risk_warning']}")
                if question.get('options'):
                    print(f"      Options: {', '.join(question['options'])}")
        else:
            print(f"\n✅ NO CLARIFICATION QUESTIONS NEEDED!")
        
        print(f"\n🎯 RISK ASSESSMENT:")
        print(f"   Risk Level: {result.risk_assessment['risk_level']}")
        print(f"   Recommendation: {result.risk_assessment['recommendation']}")
        
        if result.risk_assessment['critical_issues']:
            print(f"   Critical Issues:")
            for issue in result.risk_assessment['critical_issues']:
                print(f"   • {issue}")
        
        print(f"\n🚀 USER OPTIONS:")
        if result.risk_assessment['can_proceed']:
            print("   1. ✅ Proceed with automation (acceptable risk)")
            print("   2. 📝 Provide more information for better results")
        else:
            print("   1. 📝 Provide more information (recommended)")
            print("   2. ⚠️  Proceed anyway (high risk - not recommended)")
        print("   3. ❌ Cancel automation request")

if __name__ == "__main__":
    demonstrate_enhanced_clarification()