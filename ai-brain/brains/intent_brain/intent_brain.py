"""
Intent Brain - Multi-Brain AI Architecture with 4W Framework

The Intent Brain is responsible for understanding WHAT the user wants using a systematic
4W framework approach:
- WHAT: Action type and root need analysis
- WHERE/WHAT: Target identification and scope determination  
- WHEN: Urgency and timeline analysis
- HOW: Method preferences and execution constraints

This replaces the previous ITIL-based approach with operational action normalization
focused on resource complexity and systematic intent understanding.
"""

import logging
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, asdict
from datetime import datetime
import asyncio

from .four_w_analyzer import FourWAnalyzer, FourWAnalysis, ActionType
from .business_intent_analyzer import BusinessIntentAnalyzer, BusinessIntent
from .intent_technical_bridge import IntentTechnicalBridge

logger = logging.getLogger(__name__)

@dataclass
class IntentAnalysisResult:
    """Complete intent analysis result from Intent Brain using 4W Framework"""
    # Core identification
    intent_id: str
    user_message: str
    timestamp: datetime
    
    # 4W Framework Analysis
    four_w_analysis: FourWAnalysis
    
    # Business Intent Analysis (retained for business context)
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
            
            # 4W Framework data
            "action_type": self.four_w_analysis.what_analysis.action_type.value,
            "specific_outcome": self.four_w_analysis.what_analysis.specific_outcome,
            "root_need": self.four_w_analysis.what_analysis.root_need,
            "target_systems": self.four_w_analysis.where_what_analysis.target_systems,
            "scope_level": self.four_w_analysis.where_what_analysis.scope_level.value,
            "urgency": self.four_w_analysis.when_analysis.urgency.value,
            "timeline_type": self.four_w_analysis.when_analysis.timeline_type.value,
            "method_preference": self.four_w_analysis.how_analysis.method_preference.value,
            
            # Backward compatibility mappings
            "primary_intent": self.four_w_analysis.what_analysis.action_type.value,  # Maps action_type to old primary_intent
            "intent_confidence": self.four_w_analysis.overall_confidence,
            "complexity": self.four_w_analysis.resource_complexity.lower(),  # Maps resource_complexity to old complexity
            "risk_level_intent": self.four_w_analysis.risk_level.lower(),
            "missing_information": self.four_w_analysis.missing_information,
            
            # Business intent (retained)
            "business_intent": self.business_intent.primary_outcome.value,
            "business_outcomes": [outcome.value for outcome in self.business_intent.secondary_outcomes],
            "business_confidence": self.business_intent.confidence,
            
            # Aggregated results
            "overall_confidence": self.overall_confidence,
            "confidence_score": self.overall_confidence,  # Alias for backward compatibility
            "intent_summary": self.intent_summary,
            "recommended_approach": self.recommended_approach,
            "technical_requirements": self.technical_requirements,
            "resource_requirements": self.resource_requirements,
            "risk_level": self.risk_level,
            "risk_factors": self.risk_factors,
            "processing_time": self.processing_time,
            "brain_version": self.brain_version,
            
            # 4W Framework detailed data (for advanced consumers)
            "four_w_analysis": {
                "what": {
                    "action_type": self.four_w_analysis.what_analysis.action_type.value,
                    "specific_outcome": self.four_w_analysis.what_analysis.specific_outcome,
                    "root_need": self.four_w_analysis.what_analysis.root_need,
                    "surface_request": self.four_w_analysis.what_analysis.surface_request,
                    "confidence": self.four_w_analysis.what_analysis.confidence,
                    "reasoning": self.four_w_analysis.what_analysis.reasoning
                },
                "where_what": {
                    "target_systems": self.four_w_analysis.where_what_analysis.target_systems,
                    "scope_level": self.four_w_analysis.where_what_analysis.scope_level.value,
                    "affected_components": self.four_w_analysis.where_what_analysis.affected_components,
                    "dependencies": self.four_w_analysis.where_what_analysis.dependencies,
                    "confidence": self.four_w_analysis.where_what_analysis.confidence,
                    "reasoning": self.four_w_analysis.where_what_analysis.reasoning
                },
                "when": {
                    "urgency": self.four_w_analysis.when_analysis.urgency.value,
                    "timeline_type": self.four_w_analysis.when_analysis.timeline_type.value,
                    "specific_timeline": self.four_w_analysis.when_analysis.specific_timeline,
                    "scheduling_constraints": self.four_w_analysis.when_analysis.scheduling_constraints,
                    "business_hours_required": self.four_w_analysis.when_analysis.business_hours_required,
                    "confidence": self.four_w_analysis.when_analysis.confidence,
                    "reasoning": self.four_w_analysis.when_analysis.reasoning
                },
                "how": {
                    "method_preference": self.four_w_analysis.how_analysis.method_preference.value,
                    "execution_constraints": self.four_w_analysis.how_analysis.execution_constraints,
                    "approval_required": self.four_w_analysis.how_analysis.approval_required,
                    "rollback_needed": self.four_w_analysis.how_analysis.rollback_needed,
                    "testing_required": self.four_w_analysis.how_analysis.testing_required,
                    "confidence": self.four_w_analysis.how_analysis.confidence,
                    "reasoning": self.four_w_analysis.how_analysis.reasoning
                },
                "resource_analysis": {
                    "resource_complexity": self.four_w_analysis.resource_complexity,
                    "estimated_effort": self.four_w_analysis.estimated_effort,
                    "required_capabilities": self.four_w_analysis.required_capabilities
                }
            }
        }
    
    def get(self, key: str, default: Any = None) -> Any:
        """Dictionary-like get method for backward compatibility"""
        dict_data = self.to_dict()
        return dict_data.get(key, default)

class IntentBrain:
    """
    Intent Brain - Understanding WHAT the user wants using 4W Framework
    
    The Intent Brain is the first component in the multi-brain architecture,
    responsible for systematic intent analysis using the 4W framework:
    
    1. WHAT: Action type and root need analysis (operational action normalization)
    2. WHERE/WHAT: Target identification and scope determination
    3. WHEN: Urgency and timeline analysis  
    4. HOW: Method preferences and execution constraints
    5. Business intent and outcome analysis
    6. Resource complexity assessment
    7. Risk assessment and prioritization
    8. Technical requirement identification
    9. Confidence scoring and reasoning
    
    Focuses on operational action understanding and resource complexity rather than
    traditional ITIL process categorization.
    """
    
    def __init__(self, llm_engine=None):
        """
        Initialize the Intent Brain with 4W Framework.
        
        Args:
            llm_engine: Optional LLM engine for enhanced analysis
        """
        self.brain_id = "intent_brain"
        self.version = "2.0.0"  # Updated version for 4W framework
        self.llm_engine = llm_engine
        
        # Initialize components
        self.four_w_analyzer = FourWAnalyzer(llm_engine)
        self.business_analyzer = BusinessIntentAnalyzer()
        self.technical_bridge = IntentTechnicalBridge()
        
        # Learning and adaptation
        self.learning_enabled = True
        self.confidence_threshold = 0.7
        
        logger.info(f"Intent Brain v{self.version} initialized with 4W Framework")
    
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
            logger.info(f"Intent Brain analyzing with 4W Framework: {user_message[:100]}...")
            
            # Parallel analysis for efficiency
            four_w_task = asyncio.create_task(
                self.four_w_analyzer.analyze_4w(user_message, context)
            )
            business_task = asyncio.create_task(
                self.business_analyzer.analyze_business_intent(user_message, context)
            )
            
            # Wait for both analyses to complete
            four_w_analysis, business_intent = await asyncio.gather(
                four_w_task, business_task
            )
            
            # Aggregate confidence scores (4W analysis already has overall confidence)
            overall_confidence = self._calculate_overall_confidence(
                four_w_analysis.overall_confidence, business_intent.confidence
            )
            
            # Generate intent summary using 4W analysis
            intent_summary = self._generate_intent_summary_4w(
                four_w_analysis, business_intent
            )
            
            # Determine recommended approach using 4W analysis
            recommended_approach = self._determine_recommended_approach_4w(
                four_w_analysis, business_intent
            )
            
            # Identify technical requirements from 4W analysis
            technical_requirements = self._identify_technical_requirements_4w(
                four_w_analysis, business_intent, user_message
            )
            
            # Resource requirements come directly from 4W analysis
            resource_requirements = four_w_analysis.required_capabilities
            
            # Risk assessment comes from 4W analysis
            risk_level = four_w_analysis.risk_level
            risk_factors = four_w_analysis.risk_factors
            
            # Calculate processing time
            processing_time = (datetime.now() - start_time).total_seconds()
            
            result = IntentAnalysisResult(
                intent_id=intent_id,
                user_message=user_message,
                timestamp=start_time,
                four_w_analysis=four_w_analysis,
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
            
            # NO FALLBACK - FAIL HARD AS REQUESTED
            raise Exception(f"Intent Brain analysis FAILED - NO FALLBACK ALLOWED: {e}")
    
    def _calculate_overall_confidence(self, intent_confidence: float, 
                                    business_confidence: float) -> float:
        """Calculate overall confidence from component confidences."""
        # Weighted average with slight bias toward intent analysis
        return (intent_confidence * 0.6 + business_confidence * 0.4)
    
    def _generate_intent_summary(self, four_w: FourWAnalysis, 
                               business: BusinessIntent) -> str:
        """Generate a concise summary of the user's intent."""
        return (f"{four_w.what_analysis.action_type.value.replace('_', ' ').title()} request "
                f"aimed at {business.primary_outcome.value.replace('_', ' ')} "
                f"with {four_w.when_analysis.urgency.value} urgency")
    
    def _determine_recommended_approach(self, four_w: FourWAnalysis,
                                      business: BusinessIntent) -> str:
        """Determine the recommended approach for handling this intent."""
        approach_map = {
            ("diagnostic", "critical"): "Immediate escalation and emergency response",
            ("diagnostic", "high"): "Priority incident response with stakeholder notification",
            ("provisioning", "high"): "Strategic project planning with executive oversight",
            ("operational", "high"): "Formal change approval process with risk assessment",
            ("information", "low"): "Standard information gathering"
        }
        
        key = (four_w.what_analysis.action_type.value, four_w.when_analysis.urgency.value)
        if key in approach_map:
            return approach_map[key]
        
        # Default approach based on action type
        action_type = four_w.what_analysis.action_type.value
        if action_type == "diagnostic":
            return "Standard diagnostic and troubleshooting process"
        elif action_type == "provisioning":
            return "Service provisioning process"
        elif action_type == "operational":
            return "Operational task execution with approval workflow"
        else:
            return f"Standard {action_type.replace('_', ' ')} process execution"
    
    def _identify_technical_requirements(self, four_w: FourWAnalysis,
                                       business: BusinessIntent, 
                                       message: str) -> List[str]:
        """Identify technical requirements for the Technical Brain."""
        requirements = []
        
        # Base requirements from 4W action type
        action_requirements = {
            "information": [
                "Information gathering and reporting",
                "Status monitoring and analysis"
            ],
            "operational": [
                "System operation and management",
                "Service control and coordination"
            ],
            "diagnostic": [
                "System diagnostics and troubleshooting",
                "Service restoration procedures",
                "Root cause analysis"
            ],
            "provisioning": [
                "Resource provisioning and allocation",
                "Configuration management",
                "Access control implementation"
            ]
        }
        
        requirements.extend(
            action_requirements.get(four_w.what_analysis.action_type.value, ["Standard technical implementation"])
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
    
    def _identify_resource_requirements(self, four_w: FourWAnalysis,
                                      business: BusinessIntent) -> List[str]:
        """Identify resource requirements."""
        resources = []
        
        # Priority-based resource allocation from 4W analysis
        urgency = four_w.when_analysis.urgency.value
        risk_level = four_w.risk_level
        
        if urgency == "critical" or risk_level == "HIGH":
            resources.extend(["Senior technical staff", "Emergency response team"])
        elif urgency == "high" or risk_level == "MEDIUM":
            resources.extend(["Experienced technical staff", "Management oversight"])
        else:
            resources.extend(["Standard technical staff"])
        
        # Action type-specific resources
        action_type = four_w.what_analysis.action_type.value
        if action_type == "diagnostic":
            resources.extend(["Diagnostic specialists", "Troubleshooting tools"])
        elif action_type == "provisioning":
            resources.extend(["Infrastructure team", "Provisioning tools"])
        elif action_type == "operational":
            resources.extend(["Operations team", "Management tools"])
        
        # Business outcome resources
        if business.business_priority.value == "strategic":
            resources.extend(["Executive sponsorship", "Project management"])
        
        return list(set(resources))
    
    def _assess_risk(self, four_w: FourWAnalysis, 
                    business: BusinessIntent) -> tuple[str, List[str]]:
        """Assess overall risk level and identify risk factors."""
        risk_factors = []
        
        # 4W-based risk factors
        if four_w.risk_level == "HIGH":
            risk_factors.append("High operational risk identified")
        if four_w.when_analysis.urgency.value in ["critical", "high"]:
            risk_factors.append("Time-sensitive execution required")
        if four_w.resource_complexity == "HIGH":
            risk_factors.append("High complexity implementation")
        
        # Scope-based risk factors
        scope = four_w.where_what_analysis.scope_level.value
        if scope == "org_wide":
            risk_factors.append("Organization-wide impact")
        elif scope == "environment":
            risk_factors.append("Environment-wide changes")
        
        # Business intent risk factors
        if business.business_priority.value == "strategic":
            risk_factors.append("Strategic business initiative")
        if "security" in four_w.what_analysis.root_need.lower():
            risk_factors.append("Security implications")
        if "compliance" in business.business_risk.lower():
            risk_factors.append("Compliance requirements")
        
        # Determine overall risk level
        if four_w.risk_level == "HIGH" or business.business_priority.value == "strategic":
            risk_level = "HIGH"
        elif four_w.risk_level == "MEDIUM" or len(risk_factors) >= 3:
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
    
    # 4W Framework Helper Methods
    
    def _generate_intent_summary_4w(self, four_w: FourWAnalysis, 
                                   business: BusinessIntent) -> str:
        """Generate a concise summary using 4W analysis."""
        action_type = four_w.what_analysis.action_type.value.replace('_', ' ').title()
        scope = four_w.where_what_analysis.scope_level.value.replace('_', ' ')
        urgency = four_w.when_analysis.urgency.value
        business_outcome = business.primary_outcome.value.replace('_', ' ')
        
        return (f"{action_type} request for {scope} scope "
                f"aimed at {business_outcome} with {urgency} urgency")
    
    def _determine_recommended_approach_4w(self, four_w: FourWAnalysis,
                                         business: BusinessIntent) -> str:
        """Determine recommended approach using 4W analysis."""
        action_type = four_w.what_analysis.action_type
        urgency = four_w.when_analysis.urgency
        scope = four_w.where_what_analysis.scope_level
        method = four_w.how_analysis.method_preference
        
        # High-level approach mapping based on 4W dimensions
        if urgency.value == "critical":
            if action_type == ActionType.DIAGNOSTIC:
                return "Emergency diagnostic response with immediate escalation"
            elif action_type == ActionType.OPERATIONAL:
                return "Emergency operational response with stakeholder notification"
            else:
                return "Critical priority handling with executive oversight"
        
        elif urgency.value == "high":
            if action_type == ActionType.PROVISIONING:
                return "Priority provisioning with accelerated approval process"
            elif action_type == ActionType.DIAGNOSTIC:
                return "Priority diagnostic response with senior technical staff"
            else:
                return "High priority operational response"
        
        # Standard approaches based on action type
        approach_map = {
            ActionType.INFORMATION: "Standard information retrieval and analysis",
            ActionType.OPERATIONAL: "Standard operational execution with monitoring",
            ActionType.DIAGNOSTIC: "Systematic diagnostic process with root cause analysis",
            ActionType.PROVISIONING: "Standard provisioning process with proper approvals"
        }
        
        base_approach = approach_map.get(action_type, "Standard operational process")
        
        # Modify based on method preference
        if method.value == "automated":
            return f"{base_approach} (automated execution preferred)"
        elif method.value == "manual":
            return f"{base_approach} (manual execution required)"
        elif method.value == "guided":
            return f"{base_approach} (guided execution with assistance)"
        
        return base_approach
    
    def _identify_technical_requirements_4w(self, four_w: FourWAnalysis,
                                          business: BusinessIntent, 
                                          message: str) -> List[str]:
        """Identify technical requirements using 4W analysis."""
        requirements = []
        
        # Requirements based on action type
        action_requirements = {
            ActionType.INFORMATION: [
                "Data retrieval and analysis capabilities",
                "System monitoring and reporting tools"
            ],
            ActionType.OPERATIONAL: [
                "System administration capabilities",
                "Change execution procedures",
                "Monitoring and validation tools"
            ],
            ActionType.DIAGNOSTIC: [
                "Advanced diagnostic tools and expertise",
                "System troubleshooting capabilities",
                "Root cause analysis procedures",
                "Performance monitoring and analysis"
            ],
            ActionType.PROVISIONING: [
                "Resource provisioning capabilities",
                "Configuration management tools",
                "Infrastructure automation",
                "Access control implementation"
            ]
        }
        
        requirements.extend(
            action_requirements.get(four_w.what_analysis.action_type, [])
        )
        
        # Requirements based on scope
        if four_w.where_what_analysis.scope_level.value in ["environment", "org_wide"]:
            requirements.extend([
                "Multi-system orchestration capabilities",
                "Enterprise-scale coordination",
                "Cross-environment management"
            ])
        
        # Requirements based on urgency
        if four_w.when_analysis.urgency.value in ["high", "critical"]:
            requirements.extend([
                "Emergency response procedures",
                "Rapid escalation capabilities",
                "24/7 operational support"
            ])
        
        # Requirements based on method preference
        if four_w.how_analysis.method_preference.value == "automated":
            requirements.append("Automated execution capabilities")
        elif four_w.how_analysis.rollback_needed:
            requirements.append("Rollback and recovery procedures")
        elif four_w.how_analysis.testing_required:
            requirements.append("Testing and validation frameworks")
        
        # Business-driven requirements
        if business.primary_outcome.value == "performance_improvement":
            requirements.append("Performance optimization expertise")
        elif business.primary_outcome.value == "scalability_improvement":
            requirements.append("Scalability architecture and planning")
        elif business.primary_outcome.value == "cost_reduction":
            requirements.append("Resource optimization and cost analysis")
        
        # Context-specific requirements from message analysis
        message_lower = message.lower()
        context_requirements = {
            "database": "Database administration expertise",
            "network": "Network configuration and analysis",
            "security": "Security implementation and hardening",
            "backup": "Backup and recovery procedures",
            "monitoring": "Monitoring system configuration",
            "performance": "Performance tuning and optimization",
            "cloud": "Cloud platform expertise",
            "kubernetes": "Container orchestration expertise",
            "docker": "Container technology expertise"
        }
        
        for keyword, requirement in context_requirements.items():
            if keyword in message_lower:
                requirements.append(requirement)
        
        return list(set(requirements))  # Remove duplicates
    
    # FALLBACK METHOD REMOVED - NO FALLBACKS ALLOWED
    
    def get_technical_brain_input(self, intent_result: IntentAnalysisResult) -> Dict[str, Any]:
        """
        Convert Intent Brain analysis result to Technical Brain compatible input.
        
        This method uses the Intent-to-Technical Bridge to convert 4W Framework
        analysis into the format expected by the Technical Brain.
        
        Args:
            intent_result: Complete intent analysis result from Intent Brain
            
        Returns:
            Dict compatible with Technical Brain create_execution_plan() method
        """
        try:
            logger.info(f"Converting Intent Brain result to Technical Brain input: {intent_result.intent_id}")
            
            # Use the bridge to convert 4W analysis
            technical_input = self.technical_bridge.convert_4w_to_technical_input(
                intent_result.four_w_analysis
            )
            
            # Add additional context from Intent Brain analysis
            technical_input.update({
                "intent_id": intent_result.intent_id,
                "user_message": intent_result.user_message,
                "intent_summary": intent_result.intent_summary,
                "recommended_approach": intent_result.recommended_approach,
                "business_context": {
                    "primary_outcome": intent_result.business_intent.primary_outcome.value,
                    "business_priority": intent_result.business_intent.business_priority.value,
                    "value_proposition": intent_result.business_intent.value_proposition,
                    "success_criteria": intent_result.business_intent.success_criteria,
                    "stakeholders": intent_result.business_intent.stakeholders
                }
            })
            
            logger.info(f"Technical Brain input generated successfully for intent: {intent_result.intent_id}")
            return technical_input
            
        except Exception as e:
            logger.error(f"Error generating Technical Brain input: {e}")
            # NO FALLBACK - FAIL HARD AS REQUESTED
            raise Exception(f"Technical Brain input generation FAILED - NO FALLBACK ALLOWED: {e}")
    
    def get_bridge_stats(self) -> Dict[str, Any]:
        """Get statistics from the Intent-to-Technical Bridge."""
        return self.technical_bridge.get_conversion_stats()
    
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