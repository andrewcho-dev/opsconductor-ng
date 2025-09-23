"""
Intent Brain - Multi-Brain AI Architecture

The Intent Brain is responsible for understanding WHAT the user wants - their business
intent and desired outcomes. It combines ITIL-based classification with business
intent analysis to provide comprehensive understanding of user requests.
"""

import logging
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, asdict
from datetime import datetime
import asyncio

from .itil_classifier import IntentAnalysisBrain, IntentAnalysis
from .business_intent_analyzer import BusinessIntentAnalyzer, BusinessIntent

logger = logging.getLogger(__name__)

@dataclass
class IntentAnalysisResult:
    """Complete intent analysis result from Intent Brain"""
    # Core identification
    intent_id: str
    user_message: str
    timestamp: datetime
    
    # Intent Analysis
    intent_analysis: IntentAnalysis
    
    # Business Intent Analysis
    business_intent: BusinessIntent
    
    # Aggregated confidence and reasoning
    overall_confidence: float
    intent_summary: str
    recommended_approach: str
    
    # Technical requirements (for Technical Brain)
    technical_requirements: List[str]
    resource_requirements: List[str]
    
    # Risk assessment
    risk_level: str
    risk_factors: List[str]
    
    # Metadata
    processing_time: float
    brain_version: str
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary format for Technical Brain compatibility"""
        return {
            "intent_id": self.intent_id,
            "user_message": self.user_message,
            "timestamp": self.timestamp.isoformat(),
            "primary_intent": self.intent_analysis.primary_intent.value,
            "intent_confidence": self.intent_analysis.confidence,
            "urgency": self.intent_analysis.urgency.value,
            "complexity": self.intent_analysis.complexity.value,
            "risk_level_intent": self.intent_analysis.risk_level.value,
            "missing_information": [info.value for info in self.intent_analysis.missing_information],
            "business_intent": self.business_intent.primary_outcome.value,
            "business_outcomes": [outcome.value for outcome in self.business_intent.secondary_outcomes],
            "business_confidence": self.business_intent.confidence,
            "overall_confidence": self.overall_confidence,
            "confidence_score": self.overall_confidence,  # Alias for backward compatibility
            "intent_summary": self.intent_summary,
            "recommended_approach": self.recommended_approach,
            "technical_requirements": self.technical_requirements,
            "resource_requirements": self.resource_requirements,
            "risk_level": self.risk_level,
            "risk_factors": self.risk_factors,
            "processing_time": self.processing_time,
            "brain_version": self.brain_version
        }
    
    def get(self, key: str, default: Any = None) -> Any:
        """Dictionary-like get method for backward compatibility"""
        dict_data = self.to_dict()
        return dict_data.get(key, default)

class IntentBrain:
    """
    Intent Brain - Understanding WHAT the user wants
    
    The Intent Brain is the first component in the multi-brain architecture,
    responsible for:
    1. AI-powered intent analysis and categorization
    2. Intelligent identification of missing information
    3. Smart question generation for user clarification
    4. Business intent and outcome analysis
    5. Risk assessment and prioritization
    6. Technical requirement identification
    7. Confidence scoring and reasoning
    
    Uses ITIL Operations Management concepts as guidance/reference for
    intelligent categorization, not as strict classification rules.
    """
    
    def __init__(self, llm_engine=None):
        """
        Initialize the Intent Brain.
        
        Args:
            llm_engine: Optional LLM engine for enhanced analysis
        """
        self.brain_id = "intent_brain"
        self.version = "1.0.0"
        self.llm_engine = llm_engine
        
        # Initialize components
        self.intent_analyzer = IntentAnalysisBrain(llm_engine)
        self.business_analyzer = BusinessIntentAnalyzer()
        
        # Learning and adaptation
        self.learning_enabled = True
        self.confidence_threshold = 0.7
        
        logger.info(f"Intent Brain v{self.version} initialized")
    
    async def analyze_intent(self, user_message: str, 
                           context: Optional[Dict] = None) -> IntentAnalysisResult:
        """
        Analyze user intent comprehensively.
        
        Args:
            user_message: The user's natural language request
            context: Optional context information (user_id, conversation_id, etc.)
            
        Returns:
            IntentAnalysisResult with complete intent analysis
        """
        start_time = datetime.now()
        intent_id = f"intent_{int(start_time.timestamp())}"
        
        try:
            logger.info(f"Intent Brain analyzing: {user_message[:100]}...")
            
            # Parallel analysis for efficiency
            intent_task = asyncio.create_task(
                self.intent_analyzer.analyze_intent(user_message, context)
            )
            business_task = asyncio.create_task(
                self.business_analyzer.analyze_business_intent(user_message, context)
            )
            
            # Wait for both analyses to complete
            intent_analysis, business_intent = await asyncio.gather(
                intent_task, business_task
            )
            
            # Aggregate confidence scores
            overall_confidence = self._calculate_overall_confidence(
                intent_analysis.confidence, business_intent.confidence
            )
            
            # Generate intent summary
            intent_summary = self._generate_intent_summary(
                intent_analysis, business_intent
            )
            
            # Determine recommended approach
            recommended_approach = self._determine_recommended_approach(
                intent_analysis, business_intent
            )
            
            # Identify technical requirements
            technical_requirements = self._identify_technical_requirements(
                intent_analysis, business_intent, user_message
            )
            
            # Identify resource requirements
            resource_requirements = self._identify_resource_requirements(
                intent_analysis, business_intent
            )
            
            # Assess risk
            risk_level, risk_factors = self._assess_risk(
                intent_analysis, business_intent
            )
            
            # Calculate processing time
            processing_time = (datetime.now() - start_time).total_seconds()
            
            result = IntentAnalysisResult(
                intent_id=intent_id,
                user_message=user_message,
                timestamp=start_time,
                intent_analysis=intent_analysis,
                business_intent=business_intent,
                overall_confidence=overall_confidence,
                intent_summary=intent_summary,
                recommended_approach=recommended_approach,
                technical_requirements=technical_requirements,
                resource_requirements=resource_requirements,
                risk_level=risk_level,
                risk_factors=risk_factors,
                processing_time=processing_time,
                brain_version=self.version
            )
            
            logger.info(f"Intent analysis completed in {processing_time:.2f}s - "
                       f"Confidence: {overall_confidence:.2%}")
            
            # Learn from this analysis if enabled
            if self.learning_enabled:
                await self._learn_from_analysis(result)
            
            return result
            
        except Exception as e:
            logger.error(f"Intent Brain analysis failed: {e}")
            processing_time = (datetime.now() - start_time).total_seconds()
            
            # Return fallback result
            return self._create_fallback_result(
                intent_id, user_message, start_time, processing_time, str(e)
            )
    
    def _calculate_overall_confidence(self, intent_confidence: float, 
                                    business_confidence: float) -> float:
        """Calculate overall confidence from component confidences."""
        # Weighted average with slight bias toward intent analysis
        return (intent_confidence * 0.6 + business_confidence * 0.4)
    
    def _generate_intent_summary(self, intent: IntentAnalysis, 
                               business: BusinessIntent) -> str:
        """Generate a concise summary of the user's intent."""
        return (f"{intent.primary_intent.value.replace('_', ' ').title()} request "
                f"aimed at {business.primary_outcome.value.replace('_', ' ')} "
                f"with {intent.urgency.value} urgency")
    
    def _determine_recommended_approach(self, intent: IntentAnalysis,
                                      business: BusinessIntent) -> str:
        """Determine the recommended approach for handling this intent."""
        approach_map = {
            ("incident_response", "critical"): "Immediate escalation and emergency response",
            ("incident_response", "high"): "Priority incident response with stakeholder notification",
            ("provisioning_request", "strategic"): "Strategic project planning with executive oversight",
            ("change_request", "high"): "Formal change approval process with risk assessment",
            ("monitoring_request", "operational"): "Standard monitoring implementation"
        }
        
        key = (intent.primary_intent.value, intent.urgency.value)
        if key in approach_map:
            return approach_map[key]
        
        # Default approach based on intent type
        if intent.primary_intent.value == "incident_response":
            return "Standard incident response process"
        elif intent.primary_intent.value == "provisioning_request":
            return "Service provisioning process"
        elif intent.primary_intent.value == "change_request":
            return "Change management process with approval workflow"
        else:
            return f"Standard {intent.primary_intent.value.replace('_', ' ')} process execution"
    
    def _identify_technical_requirements(self, intent: IntentAnalysis,
                                       business: BusinessIntent, 
                                       message: str) -> List[str]:
        """Identify technical requirements for the Technical Brain."""
        requirements = []
        
        # Base requirements from intent type
        intent_requirements = {
            "incident_response": [
                "System diagnostics and troubleshooting",
                "Service restoration procedures",
                "Root cause analysis"
            ],
            "provisioning_request": [
                "Resource provisioning",
                "Configuration management",
                "Access control implementation"
            ],
            "change_request": [
                "Change impact assessment",
                "Implementation planning",
                "Rollback procedures"
            ],
            "monitoring_request": [
                "Monitoring system configuration",
                "Alert threshold definition",
                "Dashboard and reporting setup"
            ],
            "security_request": [
                "Security policy implementation",
                "Access control configuration",
                "Vulnerability assessment"
            ]
        }
        
        requirements.extend(
            intent_requirements.get(intent.primary_intent.value, ["Standard technical implementation"])
        )
        
        # Additional requirements from business intent
        if business.primary_outcome.value == "performance_improvement":
            requirements.append("Performance optimization analysis")
        elif business.primary_outcome.value == "scalability_improvement":
            requirements.append("Scalability architecture design")
        elif business.primary_outcome.value == "cost_reduction":
            requirements.append("Resource optimization analysis")
        
        # Context-specific requirements from message analysis
        message_lower = message.lower()
        if "database" in message_lower:
            requirements.append("Database administration expertise")
        if "network" in message_lower:
            requirements.append("Network configuration and analysis")
        if "security" in message_lower:
            requirements.append("Security implementation and hardening")
        if "backup" in message_lower:
            requirements.append("Backup and recovery procedures")
        
        return list(set(requirements))  # Remove duplicates
    
    def _identify_resource_requirements(self, intent: IntentAnalysis,
                                      business: BusinessIntent) -> List[str]:
        """Identify resource requirements."""
        resources = []
        
        # Priority-based resource allocation
        if intent.urgency.value == "high" and intent.risk_level.value == "high":
            resources.extend(["Senior technical staff", "Emergency response team"])
        elif intent.urgency.value == "high" or intent.risk_level.value == "high":
            resources.extend(["Experienced technical staff", "Management oversight"])
        else:
            resources.extend(["Standard technical staff"])
        
        # Intent-specific resources
        if intent.primary_intent.value == "incident_response":
            resources.extend(["Incident response team", "Diagnostic tools"])
        elif intent.primary_intent.value == "change_request":
            resources.extend(["Change advisory board", "Testing environment"])
        elif intent.primary_intent.value == "security_request":
            resources.extend(["Security team", "Compliance tools"])
        
        # Business outcome resources
        if business.business_priority.value == "strategic":
            resources.extend(["Executive sponsorship", "Project management"])
        
        return list(set(resources))
    
    def _assess_risk(self, intent: IntentAnalysis, 
                    business: BusinessIntent) -> tuple[str, List[str]]:
        """Assess overall risk level and identify risk factors."""
        risk_factors = []
        
        # Intent-based risk factors
        if intent.risk_level.value == "high":
            risk_factors.append("High operational risk identified")
        if intent.urgency.value == "high":
            risk_factors.append("Time-sensitive execution required")
        if intent.complexity.value == "high":
            risk_factors.append("High complexity implementation")
        
        # Business intent risk factors
        if business.business_priority.value == "strategic":
            risk_factors.append("Strategic business initiative")
        if intent.primary_intent.value == "security_request":
            risk_factors.append("Security implications")
        if "compliance" in business.business_risk.lower():
            risk_factors.append("Compliance requirements")
        
        # Determine overall risk level
        if intent.risk_level.value == "high" or business.business_priority.value == "strategic":
            risk_level = "HIGH"
        elif intent.risk_level.value == "medium" or len(risk_factors) >= 3:
            risk_level = "MEDIUM"
        else:
            risk_level = "LOW"
        
        return risk_level, risk_factors
    
    async def _learn_from_analysis(self, result: IntentAnalysisResult):
        """Learn from the analysis result to improve future performance."""
        try:
            # This is a placeholder for learning implementation
            # In a full implementation, this would:
            # 1. Store successful patterns
            # 2. Update confidence thresholds
            # 3. Improve classification accuracy
            # 4. Learn from user feedback
            
            logger.debug(f"Learning from intent analysis: {result.intent_id}")
            
            # Example learning: Track confidence vs success rates
            if result.overall_confidence > self.confidence_threshold:
                logger.debug("High confidence analysis - reinforcing patterns")
            else:
                logger.debug("Low confidence analysis - flagging for review")
                
        except Exception as e:
            logger.warning(f"Learning process failed: {e}")
    
    def _create_fallback_result(self, intent_id: str, user_message: str,
                              start_time: datetime, processing_time: float,
                              error: str) -> IntentAnalysisResult:
        """Create a fallback result when analysis fails."""
        from .itil_classifier import IntentCategory, UrgencyLevel, ComplexityLevel, RiskLevel, InformationNeeded, IntentAnalysis
        from .business_intent_analyzer import BusinessOutcome, BusinessPriority, BusinessIntent
        
        # Create minimal fallback intent analysis
        fallback_intent = IntentAnalysis(
            primary_intent=IntentCategory.INFORMATION_REQUEST,
            urgency=UrgencyLevel.MEDIUM,
            complexity=ComplexityLevel.MEDIUM,
            risk_level=RiskLevel.MEDIUM,
            missing_information=[InformationNeeded.SYSTEM_DETAILS],
            suggested_questions=["Could you provide more details about your request?"],
            confidence=0.3,
            reasoning=f"Fallback analysis due to error: {error}"
        )
        
        fallback_business = BusinessIntent(
            primary_outcome=BusinessOutcome.OPERATIONAL_EFFICIENCY,
            secondary_outcomes=[],
            business_priority=BusinessPriority.OPERATIONAL,
            value_proposition="Standard IT operational support",
            success_criteria=["Request completed successfully"],
            stakeholders=["IT Operations"],
            business_risk="Low operational risk",
            roi_indicators=["Operational continuity"],
            confidence=0.3,
            reasoning=f"Fallback analysis due to error: {error}"
        )
        
        return IntentAnalysisResult(
            intent_id=intent_id,
            user_message=user_message,
            timestamp=start_time,
            intent_analysis=fallback_intent,
            business_intent=fallback_business,
            overall_confidence=0.3,
            intent_summary="General service request",
            recommended_approach="Standard processing with manual review",
            technical_requirements=["Manual analysis required"],
            resource_requirements=["Technical staff review"],
            risk_level="MEDIUM",
            risk_factors=["Analysis failure requires manual review"],
            processing_time=processing_time,
            brain_version=self.version
        )
    
    async def get_brain_status(self) -> Dict[str, Any]:
        """Get current brain status and capabilities."""
        from .itil_classifier import IntentCategory
        from .business_intent_analyzer import BusinessOutcome
        
        return {
            "brain_id": self.brain_id,
            "version": self.version,
            "status": "active",
            "capabilities": {
                "ai_powered_intent_analysis": True,
                "business_intent_analysis": True,
                "risk_assessment": True,
                "technical_requirement_identification": True,
                "learning_enabled": self.learning_enabled,
                "intelligent_question_generation": True
            },
            "confidence_threshold": self.confidence_threshold,
            "supported_intent_categories": [intent.value for intent in IntentCategory],
            "supported_business_outcomes": [outcome.value for outcome in BusinessOutcome]
        }
    
    def to_dict(self, result: IntentAnalysisResult) -> Dict[str, Any]:
        """Convert IntentAnalysisResult to dictionary for serialization."""
        return {
            "intent_id": result.intent_id,
            "user_message": result.user_message,
            "timestamp": result.timestamp.isoformat(),
            "intent_analysis": {
                "primary_intent": result.intent_analysis.primary_intent.value,
                "urgency": result.intent_analysis.urgency.value,
                "complexity": result.intent_analysis.complexity.value,
                "risk_level": result.intent_analysis.risk_level.value,
                "missing_information": [info.value for info in result.intent_analysis.missing_information],
                "suggested_questions": result.intent_analysis.suggested_questions,
                "confidence": result.intent_analysis.confidence,
                "reasoning": result.intent_analysis.reasoning
            },
            "business_intent": {
                "primary_outcome": result.business_intent.primary_outcome.value,
                "secondary_outcomes": [outcome.value for outcome in result.business_intent.secondary_outcomes],
                "business_priority": result.business_intent.business_priority.value,
                "value_proposition": result.business_intent.value_proposition,
                "success_criteria": result.business_intent.success_criteria,
                "stakeholders": result.business_intent.stakeholders,
                "business_risk": result.business_intent.business_risk,
                "roi_indicators": result.business_intent.roi_indicators,
                "confidence": result.business_intent.confidence,
                "reasoning": result.business_intent.reasoning
            },
            "overall_confidence": result.overall_confidence,
            "intent_summary": result.intent_summary,
            "recommended_approach": result.recommended_approach,
            "technical_requirements": result.technical_requirements,
            "resource_requirements": result.resource_requirements,
            "risk_level": result.risk_level,
            "risk_factors": result.risk_factors,
            "processing_time": result.processing_time,
            "brain_version": result.brain_version
        }