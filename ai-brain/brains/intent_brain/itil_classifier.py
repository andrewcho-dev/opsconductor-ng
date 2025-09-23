"""
Intent Analysis Brain - AI-Powered User Intent Classification

This brain uses LLM analysis to understand user intent and determine what additional 
information is needed to fulfill requests. It uses ITIL Operations Management as a 
reference framework to categorize intents and intelligently prompt for missing details.
"""

import logging
import json
from typing import Dict, Any, List, Optional
from enum import Enum
from dataclasses import dataclass
from datetime import datetime

logger = logging.getLogger(__name__)

class IntentCategory(Enum):
    """General intent categories for operational requests"""
    INCIDENT_RESPONSE = "incident_response"           # Something is broken, needs fixing
    CHANGE_REQUEST = "change_request"                 # Want to modify/update something
    INFORMATION_REQUEST = "information_request"       # Need information/status
    PROVISIONING_REQUEST = "provisioning_request"    # Need new resources/services
    MONITORING_REQUEST = "monitoring_request"         # Want to monitor/track something
    TROUBLESHOOTING = "troubleshooting"              # Need help diagnosing issues
    OPTIMIZATION_REQUEST = "optimization_request"     # Want to improve performance
    SECURITY_REQUEST = "security_request"            # Security-related needs
    COMPLIANCE_REQUEST = "compliance_request"        # Compliance/audit needs
    GENERAL_SUPPORT = "general_support"              # General help/guidance

class InformationNeeded(Enum):
    """Types of additional information that might be needed"""
    SYSTEM_DETAILS = "system_details"               # Which systems/servers
    SCOPE_CLARIFICATION = "scope_clarification"     # How extensive is the request
    TIMELINE_REQUIREMENTS = "timeline_requirements" # When does this need to happen
    BUSINESS_JUSTIFICATION = "business_justification" # Why is this needed
    TECHNICAL_SPECIFICATIONS = "technical_specifications" # Technical requirements
    IMPACT_ASSESSMENT = "impact_assessment"         # What will be affected
    RESOURCE_REQUIREMENTS = "resource_requirements" # What resources are needed
    APPROVAL_REQUIREMENTS = "approval_requirements" # Who needs to approve
    ROLLBACK_PLAN = "rollback_plan"                 # How to undo if needed
    TESTING_REQUIREMENTS = "testing_requirements"   # How to validate success

class UrgencyLevel(Enum):
    """Urgency levels for intent analysis"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"

class ComplexityLevel(Enum):
    """Complexity levels for intent analysis"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"

class RiskLevel(Enum):
    """Risk levels for intent analysis"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"

@dataclass
class IntentAnalysis:
    """Result of AI-powered intent analysis"""
    primary_intent: IntentCategory
    urgency: UrgencyLevel
    complexity: ComplexityLevel
    risk_level: RiskLevel
    missing_information: List[InformationNeeded]
    suggested_questions: List[str]
    confidence: float
    reasoning: str

class IntentAnalysisBrain:
    """
    AI-powered intent analysis brain that understands user requests and determines
    what additional information is needed to fulfill them effectively.
    """
    
    def __init__(self, llm_engine=None):
        """Initialize the intent analysis brain with LLM engine."""
        self.llm_engine = llm_engine
        self.analysis_history = []
        self.learning_patterns = {}
        
        # Build the system prompt for intent analysis
        self.system_prompt = self._build_system_prompt()
    
    def _build_system_prompt(self) -> str:
        """Build the system prompt for LLM-powered intent analysis."""
        return """You are an expert IT Operations Intent Analyst. Your job is to analyze user requests and determine:

1. WHAT the user actually wants (intent classification)
2. WHAT additional information is needed to fulfill the request
3. HOW to intelligently prompt the user for missing details

Use ITIL Operations Management practices as a reference framework, but focus on practical intent analysis.

INTENT CATEGORIES:
- incident_response: Something is broken and needs immediate fixing
- change_request: User wants to modify, update, or change something
- information_request: User needs information, status, or documentation
- provisioning_request: User needs new resources, services, or access
- monitoring_request: User wants to monitor, track, or observe something
- troubleshooting: User needs help diagnosing or understanding issues
- optimization_request: User wants to improve performance or efficiency
- security_request: Security-related needs (access, policies, vulnerabilities)
- compliance_request: Compliance, audit, or regulatory requirements
- general_support: General help, guidance, or consultation

INFORMATION TYPES TO ASSESS:
- system_details: Which specific systems, servers, applications are involved?
- scope_clarification: How extensive is this request? What's included/excluded?
- timeline_requirements: When does this need to happen? Any deadlines?
- business_justification: Why is this needed? What's the business impact?
- technical_specifications: What are the technical requirements or constraints?
- impact_assessment: What systems/users will be affected?
- resource_requirements: What resources (time, people, tools) are needed?
- approval_requirements: Who needs to approve this? Any change control?
- rollback_plan: How can this be undone if something goes wrong?
- testing_requirements: How will success be validated?

ANALYSIS APPROACH:
1. Understand the core intent behind the request
2. Identify what information is missing or unclear
3. Assess risk, urgency, and complexity
4. Reference relevant ITIL practices for context
5. Suggest intelligent follow-up questions
6. Provide clear next steps

Respond with a JSON object containing your analysis."""

    async def analyze_intent(self, user_message: str, context: Optional[Dict] = None) -> IntentAnalysis:
        """
        Analyze user intent using AI and determine what additional information is needed.
        
        Args:
            user_message: The user's request
            context: Optional context information
            
        Returns:
            IntentAnalysis with detailed analysis and recommendations
        """
        try:
            logger.info(f"Analyzing intent for message: {user_message[:100]}...")
            
            if not self.llm_engine:
                logger.warning("No LLM engine available, using fallback analysis")
                return self._fallback_analysis(user_message)
            
            # Prepare the analysis prompt
            analysis_prompt = self._build_analysis_prompt(user_message, context)
            
            # Get LLM analysis
            llm_response = await self.llm_engine.chat(
                message=analysis_prompt,
                system_prompt=self.system_prompt,
                context="Intent Analysis"
            )
            
            # Parse the LLM response
            analysis_result = self._parse_llm_response(llm_response, user_message)
            
            # Store for learning
            self.analysis_history.append({
                "message": user_message,
                "analysis": analysis_result,
                "timestamp": datetime.now()
            })
            
            logger.info(f"Intent analysis completed: {analysis_result.primary_intent.value}")
            return analysis_result
            
        except Exception as e:
            logger.error(f"Error in intent analysis: {e}")
            return self._fallback_analysis(user_message, error=str(e))
    
    def _build_analysis_prompt(self, user_message: str, context: Optional[Dict] = None) -> str:
        """Build the analysis prompt for the LLM."""
        prompt = f"""Analyze this user request for intent and missing information:

USER REQUEST: "{user_message}"
"""
        
        if context:
            prompt += f"\nCONTEXT: {json.dumps(context, indent=2)}\n"
        
        prompt += """
Please analyze this request and provide:

1. Primary intent category (from the list provided)
2. Confidence level (0.0 to 1.0)
3. Brief summary of what the user wants
4. List of missing information types needed
5. Specific questions to ask the user
6. Risk assessment (low/medium/high)
7. Urgency assessment (low/medium/high/critical)
8. Complexity estimate (simple/moderate/complex)
9. Relevant ITIL practice reference
10. Your reasoning for the analysis
11. Suggested next steps

Format your response as a JSON object with these fields:
{
    "primary_intent": "intent_category",
    "confidence": 0.85,
    "intent_summary": "Brief description of what user wants",
    "missing_information": ["info_type1", "info_type2"],
    "suggested_questions": ["Question 1?", "Question 2?"],
    "risk_level": "medium",
    "urgency_assessment": "high", 
    "complexity_estimate": "moderate",
    "itil_reference": "Relevant ITIL practice",
    "reasoning": "Why you classified it this way",
    "next_steps": ["Step 1", "Step 2"]
}
"""
        return prompt
    
    def _parse_llm_response(self, llm_response: Dict[str, Any], user_message: str) -> IntentAnalysis:
        """Parse the LLM response into an IntentAnalysis object."""
        try:
            # Extract the response content
            response_content = llm_response.get('response', '{}')
            
            # Try to parse as JSON
            if isinstance(response_content, str):
                # Look for JSON in the response
                json_start = response_content.find('{')
                json_end = response_content.rfind('}') + 1
                if json_start >= 0 and json_end > json_start:
                    json_content = response_content[json_start:json_end]
                    analysis_data = json.loads(json_content)
                else:
                    raise ValueError("No JSON found in response")
            else:
                analysis_data = response_content
            
            # Map to our data structures
            primary_intent = IntentCategory(analysis_data.get('primary_intent', 'general_support'))
            
            missing_info = []
            for info_type in analysis_data.get('missing_information', []):
                try:
                    missing_info.append(InformationNeeded(info_type))
                except ValueError:
                    logger.warning(f"Unknown information type: {info_type}")
            
            # Parse enum values with fallbacks
            urgency = UrgencyLevel.MEDIUM
            try:
                urgency = UrgencyLevel(analysis_data.get('urgency_assessment', 'medium'))
            except ValueError:
                logger.warning(f"Invalid urgency level, using default: {analysis_data.get('urgency_assessment')}")
            
            complexity = ComplexityLevel.MEDIUM
            try:
                complexity = ComplexityLevel(analysis_data.get('complexity_estimate', 'medium'))
            except ValueError:
                logger.warning(f"Invalid complexity level, using default: {analysis_data.get('complexity_estimate')}")
            
            risk_level = RiskLevel.MEDIUM
            try:
                risk_level = RiskLevel(analysis_data.get('risk_level', 'medium'))
            except ValueError:
                logger.warning(f"Invalid risk level, using default: {analysis_data.get('risk_level')}")
            
            return IntentAnalysis(
                primary_intent=primary_intent,
                urgency=urgency,
                complexity=complexity,
                risk_level=risk_level,
                missing_information=missing_info,
                suggested_questions=analysis_data.get('suggested_questions', []),
                confidence=float(analysis_data.get('confidence', 0.5)),
                reasoning=analysis_data.get('reasoning', 'AI analysis completed')
            )
            
        except Exception as e:
            logger.error(f"Error parsing LLM response: {e}")
            return self._fallback_analysis(user_message, error=f"Parse error: {str(e)}")
    
    def _fallback_analysis(self, user_message: str, error: Optional[str] = None) -> IntentAnalysis:
        """Provide fallback analysis when LLM is not available."""
        logger.warning("Using fallback intent analysis")
        
        # Simple keyword-based fallback
        message_lower = user_message.lower()
        
        if any(word in message_lower for word in ['down', 'broken', 'not working', 'error', 'failed']):
            intent = IntentCategory.INCIDENT_RESPONSE
            summary = "System appears to have an issue that needs resolution"
            missing_info = [InformationNeeded.SYSTEM_DETAILS, InformationNeeded.IMPACT_ASSESSMENT]
        elif any(word in message_lower for word in ['change', 'update', 'modify', 'configure']):
            intent = IntentCategory.CHANGE_REQUEST
            summary = "User wants to make changes to systems or configuration"
            missing_info = [InformationNeeded.SCOPE_CLARIFICATION, InformationNeeded.TIMELINE_REQUIREMENTS]
        elif any(word in message_lower for word in ['new', 'create', 'provision', 'setup']):
            intent = IntentCategory.PROVISIONING_REQUEST
            summary = "User needs new resources or services"
            missing_info = [InformationNeeded.TECHNICAL_SPECIFICATIONS, InformationNeeded.RESOURCE_REQUIREMENTS]
        else:
            intent = IntentCategory.GENERAL_SUPPORT
            summary = "General support request"
            missing_info = [InformationNeeded.SCOPE_CLARIFICATION]
        
        reasoning = "Fallback analysis using basic keyword matching"
        if error:
            reasoning += f" (Error: {error})"
        
        return IntentAnalysis(
            primary_intent=intent,
            urgency=UrgencyLevel.MEDIUM,
            complexity=ComplexityLevel.MEDIUM,
            risk_level=RiskLevel.MEDIUM,
            missing_information=missing_info,
            suggested_questions=["Can you provide more details about your request?"],
            confidence=0.3,
            reasoning=reasoning
        )
    
    async def suggest_follow_up_questions(self, analysis: IntentAnalysis) -> List[str]:
        """Generate intelligent follow-up questions based on missing information."""
        questions = []
        
        for info_needed in analysis.missing_information:
            if info_needed == InformationNeeded.SYSTEM_DETAILS:
                questions.append("Which specific systems, servers, or applications are involved?")
            elif info_needed == InformationNeeded.SCOPE_CLARIFICATION:
                questions.append("What is the scope of this request? What should be included or excluded?")
            elif info_needed == InformationNeeded.TIMELINE_REQUIREMENTS:
                questions.append("When do you need this completed? Are there any specific deadlines?")
            elif info_needed == InformationNeeded.BUSINESS_JUSTIFICATION:
                questions.append("What is the business reason for this request? How will it help?")
            elif info_needed == InformationNeeded.TECHNICAL_SPECIFICATIONS:
                questions.append("What are the technical requirements or specifications?")
            elif info_needed == InformationNeeded.IMPACT_ASSESSMENT:
                questions.append("What systems or users might be affected by this change?")
            elif info_needed == InformationNeeded.RESOURCE_REQUIREMENTS:
                questions.append("What resources (time, people, tools) will be needed?")
            elif info_needed == InformationNeeded.APPROVAL_REQUIREMENTS:
                questions.append("Who needs to approve this request? Any change control process?")
            elif info_needed == InformationNeeded.ROLLBACK_PLAN:
                questions.append("How should we handle rollback if something goes wrong?")
            elif info_needed == InformationNeeded.TESTING_REQUIREMENTS:
                questions.append("How will we validate that this request was completed successfully?")
        
        return questions
    
    async def learn_from_feedback(self, analysis: IntentAnalysis, feedback: Dict[str, Any]):
        """Learn from user feedback to improve future analysis."""
        learning_entry = {
            "analysis": analysis,
            "feedback": feedback,
            "timestamp": datetime.now()
        }
        
        # Store learning data for future improvements
        intent_key = analysis.primary_intent.value
        if intent_key not in self.learning_patterns:
            self.learning_patterns[intent_key] = []
        
        self.learning_patterns[intent_key].append(learning_entry)
        logger.info(f"Learned from feedback for intent: {intent_key}")

# Maintain backward compatibility
ITILOperationsClassifier = IntentAnalysisBrain
ITILOperationsClassification = IntentAnalysis
ITILOperationsType = IntentCategory