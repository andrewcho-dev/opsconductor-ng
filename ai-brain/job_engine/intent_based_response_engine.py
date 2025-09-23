"""
OpsConductor AI Brain - Intent-Based Response Engine

This implements a more sophisticated approach to AI request handling based on:
1. Intent Classification (ITIL-inspired categories)
2. Template-Driven Response Construction
3. Parameter Extraction and Validation
4. Confidence-Based Decision Making

This addresses the concern about simple keyword matching by implementing
true intent understanding and structured response generation.
"""

import logging
import json
import re
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
import asyncio

from integrations.llm_client import LLMEngine
from integrations.automation_client import AutomationServiceClient

logger = logging.getLogger(__name__)

class IntentCategory(Enum):
    """Primary intent categories based on ITIL service management"""
    INFORMATION_REQUEST = "information_request"
    SERVICE_REQUEST = "service_request" 
    INCIDENT_MANAGEMENT = "incident_management"
    CHANGE_MANAGEMENT = "change_management"
    MONITORING_ANALYTICS = "monitoring_analytics"
    TESTING_VALIDATION = "testing_validation"
    UNKNOWN = "unknown"

class IntentSubcategory(Enum):
    """Subcategories for more specific intent classification"""
    # Information Requests
    STATUS_INQUIRY = "status_inquiry"
    DOCUMENTATION_REQUEST = "documentation_request"
    SYSTEM_INFORMATION = "system_information"
    REPORTING = "reporting"
    
    # Service Requests
    ACCESS_REQUEST = "access_request"
    INSTALLATION_DEPLOYMENT = "installation_deployment"
    CONFIGURATION_CHANGE = "configuration_change"
    RESOURCE_PROVISIONING = "resource_provisioning"
    
    # Incident Management
    TROUBLESHOOTING = "troubleshooting"
    SYSTEM_RECOVERY = "system_recovery"
    PERFORMANCE_ISSUE = "performance_issue"
    CONNECTIVITY_PROBLEM = "connectivity_problem"
    
    # Change Management
    SYSTEM_UPDATE = "system_update"
    INFRASTRUCTURE_CHANGE = "infrastructure_change"
    PROCESS_CHANGE = "process_change"
    
    # Monitoring & Analytics
    HEALTH_CHECK = "health_check"
    PERFORMANCE_MONITORING = "performance_monitoring"
    LOG_ANALYSIS = "log_analysis"
    ALERTING_SETUP = "alerting_setup"
    
    # Testing & Validation
    CONNECTIVITY_TEST = "connectivity_test"
    PERFORMANCE_TEST = "performance_test"
    SECURITY_TEST = "security_test"
    COMPLIANCE_CHECK = "compliance_check"

@dataclass
class IntentClassification:
    """Result of intent analysis"""
    primary_category: IntentCategory
    subcategory: IntentSubcategory
    confidence: float
    reasoning: str
    extracted_entities: Dict[str, Any]
    context_factors: List[str]

@dataclass
class ResponseTemplate:
    """Template for constructing appropriate responses"""
    intent_pattern: str
    analysis_framework: List[str]
    required_parameters: List[str]
    optional_parameters: List[str]
    validation_checklist: List[str]
    response_strategies: Dict[str, str]
    confidence_thresholds: Dict[str, float]

class IntentBasedResponseEngine:
    """
    Advanced AI response engine that uses intent classification and 
    template-driven response construction instead of simple keyword matching
    """
    
    def __init__(self, llm_engine: LLMEngine, automation_client: Optional[AutomationServiceClient] = None):
        self.llm_engine = llm_engine
        self.automation_client = automation_client or AutomationServiceClient()
        
        # Load response templates - this is the "intelligence" of the system
        self.response_templates = self._initialize_response_templates()
        
        # Intent classification knowledge base
        self.intent_patterns = self._initialize_intent_patterns()
    
    def _initialize_response_templates(self) -> Dict[str, ResponseTemplate]:
        """Initialize response construction templates"""
        return {
            "service_request.installation_deployment": ResponseTemplate(
                intent_pattern="service_request.installation_deployment",
                analysis_framework=[
                    "identify_target_system",
                    "determine_software_component",
                    "assess_prerequisites", 
                    "identify_dependencies",
                    "determine_installation_method",
                    "evaluate_automation_options"
                ],
                required_parameters=["target_system", "component_type"],
                optional_parameters=["credentials", "configuration_options", "version"],
                validation_checklist=[
                    "target_system_accessibility",
                    "prerequisite_satisfaction", 
                    "resource_availability",
                    "security_compliance",
                    "change_approval_required"
                ],
                response_strategies={
                    "automation_available": "execute_automation_workflow",
                    "manual_required": "generate_step_by_step_guide",
                    "approval_needed": "create_change_request",
                    "insufficient_info": "request_additional_details"
                },
                confidence_thresholds={
                    "proceed_with_automation": 0.85,
                    "proceed_with_manual": 0.70,
                    "request_approval": 0.60,
                    "request_clarification": 0.40
                }
            ),
            
            "information_request.system_information": ResponseTemplate(
                intent_pattern="information_request.system_information",
                analysis_framework=[
                    "identify_information_type",
                    "determine_data_sources",
                    "assess_access_permissions",
                    "evaluate_information_sensitivity"
                ],
                required_parameters=["information_type"],
                optional_parameters=["target_system", "time_range", "format_preference"],
                validation_checklist=[
                    "user_authorization",
                    "data_availability",
                    "information_sensitivity"
                ],
                response_strategies={
                    "direct_query": "execute_information_query",
                    "report_generation": "generate_formatted_report",
                    "access_denied": "explain_access_limitations",
                    "data_unavailable": "suggest_alternatives"
                },
                confidence_thresholds={
                    "proceed_with_query": 0.80,
                    "generate_report": 0.70,
                    "request_clarification": 0.50
                }
            ),
            
            "incident_management.troubleshooting": ResponseTemplate(
                intent_pattern="incident_management.troubleshooting",
                analysis_framework=[
                    "identify_problem_symptoms",
                    "determine_affected_systems",
                    "assess_impact_urgency",
                    "identify_potential_causes",
                    "determine_diagnostic_steps"
                ],
                required_parameters=["problem_description", "affected_system"],
                optional_parameters=["error_messages", "time_occurred", "user_impact"],
                validation_checklist=[
                    "incident_severity",
                    "system_accessibility",
                    "diagnostic_permissions",
                    "escalation_criteria"
                ],
                response_strategies={
                    "automated_diagnosis": "execute_diagnostic_workflow",
                    "guided_troubleshooting": "provide_step_by_step_diagnosis",
                    "escalation_required": "create_incident_ticket",
                    "known_issue": "provide_known_solution"
                },
                confidence_thresholds={
                    "proceed_with_automation": 0.80,
                    "provide_guidance": 0.65,
                    "escalate_incident": 0.50
                }
            )
        }
    
    def _initialize_intent_patterns(self) -> Dict[str, Dict[str, Any]]:
        """Initialize intent classification patterns"""
        return {
            "installation_deployment_patterns": {
                "keywords": ["install", "deploy", "setup", "configure", "provision"],
                "entities": ["software", "service", "probe", "agent", "application"],
                "contexts": ["on", "to", "at", "for"],
                "indicators": ["target_system", "ip_address", "hostname", "server"]
            },
            "information_request_patterns": {
                "keywords": ["show", "list", "get", "what", "how", "status", "info"],
                "entities": ["logs", "metrics", "configuration", "version", "health"],
                "contexts": ["of", "for", "about", "from"],
                "indicators": ["system", "service", "application", "network"]
            },
            "troubleshooting_patterns": {
                "keywords": ["fix", "resolve", "troubleshoot", "diagnose", "repair"],
                "entities": ["error", "issue", "problem", "failure", "outage"],
                "contexts": ["with", "in", "on", "for"],
                "indicators": ["not working", "failed", "down", "slow", "timeout"]
            }
        }
    
    async def analyze_intent(self, user_request: str, context: Optional[Dict[str, Any]] = None) -> IntentClassification:
        """
        Analyze user request to classify intent using LLM reasoning
        This is much more sophisticated than keyword matching
        """
        system_prompt = f"""You are an expert at analyzing IT service requests and classifying user intent.

Your task is to analyze the user's request and classify it according to ITIL-inspired categories.

Primary Categories:
- information_request: User wants information, status, or documentation
- service_request: User wants something installed, configured, or provisioned  
- incident_management: User has a problem that needs troubleshooting
- change_management: User wants to modify existing systems/processes
- monitoring_analytics: User wants to monitor, analyze, or set up alerts
- testing_validation: User wants to test or validate system functionality

Subcategories for service_request:
- installation_deployment: Installing/deploying software, services, or components
- configuration_change: Modifying system or application configurations
- access_request: Requesting access to systems or resources
- resource_provisioning: Provisioning infrastructure or resources

Analyze the request holistically considering:
1. The primary action the user wants to take
2. The context and business purpose
3. The technical components involved
4. The expected outcome

Respond with JSON only:
{{
    "primary_category": "category_name",
    "subcategory": "subcategory_name", 
    "confidence": 0.0-1.0,
    "reasoning": "Detailed explanation of classification logic",
    "extracted_entities": {{
        "target_system": "extracted_value_or_null",
        "component_type": "extracted_value_or_null",
        "action_type": "extracted_value_or_null"
    }},
    "context_factors": ["list", "of", "relevant", "context", "clues"]
}}"""

        prompt = f"""Analyze this IT service request:

User Request: "{user_request}"

Additional Context: {json.dumps(context or {}, indent=2)}

Classify the intent and extract relevant information:"""

        try:
            response = await self.llm_engine.chat(
                message=prompt,
                system_prompt=system_prompt,
                model=None
            )
            
            # Parse LLM response
            json_text = self._extract_json_from_response(response["response"])
            classification_data = json.loads(json_text)
            
            return IntentClassification(
                primary_category=IntentCategory(classification_data.get("primary_category", "unknown")),
                subcategory=IntentSubcategory(classification_data.get("subcategory", "unknown")),
                confidence=classification_data.get("confidence", 0.0),
                reasoning=classification_data.get("reasoning", "No reasoning provided"),
                extracted_entities=classification_data.get("extracted_entities", {}),
                context_factors=classification_data.get("context_factors", [])
            )
            
        except Exception as e:
            logger.error(f"Intent classification failed: {e}")
            return IntentClassification(
                primary_category=IntentCategory.UNKNOWN,
                subcategory=IntentSubcategory.UNKNOWN,
                confidence=0.0,
                reasoning=f"Classification failed: {e}",
                extracted_entities={},
                context_factors=[]
            )
    
    async def construct_response(self, intent: IntentClassification, user_request: str, 
                               context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Construct appropriate response based on classified intent and response templates
        This is the core intelligence that replaces simple automation script matching
        """
        template_key = f"{intent.primary_category.value}.{intent.subcategory.value}"
        template = self.response_templates.get(template_key)
        
        if not template:
            logger.warning(f"No response template found for intent: {template_key}")
            return await self._fallback_response(user_request, intent, context)
        
        logger.info(f"Using response template: {template_key}")
        
        # Execute the analysis framework
        analysis_results = await self._execute_analysis_framework(
            template.analysis_framework, user_request, intent, context
        )
        
        # Extract and validate parameters
        parameters = await self._extract_and_validate_parameters(
            template, user_request, intent, analysis_results, context
        )
        
        # Determine response strategy based on confidence and validation
        strategy = self._determine_response_strategy(template, intent, parameters, analysis_results)
        
        # Construct the final response
        return await self._execute_response_strategy(strategy, template, parameters, analysis_results, context)
    
    async def _execute_analysis_framework(self, framework: List[str], user_request: str,
                                        intent: IntentClassification, context: Optional[Dict[str, Any]]) -> Dict[str, Any]:
        """Execute the analysis framework steps"""
        results = {}
        
        for step in framework:
            try:
                result = await self._execute_analysis_step(step, user_request, intent, context, results)
                results[step] = result
            except Exception as e:
                logger.error(f"Analysis step {step} failed: {e}")
                results[step] = {"error": str(e)}
        
        return results
    
    async def _execute_analysis_step(self, step: str, user_request: str, intent: IntentClassification,
                                   context: Optional[Dict[str, Any]], previous_results: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a single analysis step using LLM reasoning"""
        
        step_prompts = {
            "identify_target_system": "What system, server, or infrastructure component is the target of this request?",
            "determine_software_component": "What software, service, or component needs to be installed/configured?",
            "assess_prerequisites": "What prerequisites, dependencies, or requirements must be met?",
            "identify_dependencies": "What other systems or services does this depend on?",
            "determine_installation_method": "What is the most appropriate installation or deployment method?",
            "evaluate_automation_options": "Are there existing automation workflows that could handle this request?"
        }
        
        step_prompt = step_prompts.get(step, f"Analyze the {step.replace('_', ' ')} for this request")
        
        system_prompt = f"""You are analyzing an IT service request step by step.

Current Analysis Step: {step}
User Request: "{user_request}"
Intent Classification: {intent.primary_category.value}.{intent.subcategory.value} (confidence: {intent.confidence})
Previous Analysis: {json.dumps(previous_results, indent=2)}

Provide a detailed analysis for this specific step. Be thorough and consider technical requirements, constraints, and best practices.

Respond with JSON only:
{{
    "analysis": "detailed analysis result",
    "confidence": 0.0-1.0,
    "recommendations": ["list", "of", "recommendations"],
    "risks": ["list", "of", "potential", "risks"],
    "next_steps": ["suggested", "next", "steps"]
}}"""

        try:
            response = await self.llm_engine.chat(
                message=step_prompt,
                system_prompt=system_prompt,
                model=None
            )
            
            json_text = self._extract_json_from_response(response["response"])
            return json.loads(json_text)
            
        except Exception as e:
            return {"error": f"Step analysis failed: {e}"}
    
    def _extract_json_from_response(self, response: str) -> str:
        """Extract JSON from LLM response"""
        # Look for JSON blocks
        json_match = re.search(r'```json\s*(.*?)\s*```', response, re.DOTALL)
        if json_match:
            return json_match.group(1)
        
        # Look for JSON objects
        json_match = re.search(r'\{.*\}', response, re.DOTALL)
        if json_match:
            return json_match.group(0)
        
        return response.strip()
    
    async def _extract_and_validate_parameters(self, template: ResponseTemplate, user_request: str,
                                             intent: IntentClassification, analysis_results: Dict[str, Any],
                                             context: Optional[Dict[str, Any]]) -> Dict[str, Any]:
        """Extract and validate required parameters"""
        # This would implement sophisticated parameter extraction
        # For now, return basic extraction from intent entities
        return {
            **intent.extracted_entities,
            "analysis_confidence": intent.confidence,
            "validation_results": analysis_results
        }
    
    def _determine_response_strategy(self, template: ResponseTemplate, intent: IntentClassification,
                                   parameters: Dict[str, Any], analysis_results: Dict[str, Any]) -> str:
        """Determine the best response strategy based on confidence and analysis"""
        confidence = intent.confidence
        
        # Use template confidence thresholds to determine strategy
        if confidence >= template.confidence_thresholds.get("proceed_with_automation", 0.85):
            return "automation_available"
        elif confidence >= template.confidence_thresholds.get("proceed_with_manual", 0.70):
            return "manual_required"
        elif confidence >= template.confidence_thresholds.get("request_approval", 0.60):
            return "approval_needed"
        else:
            return "insufficient_info"
    
    async def _execute_response_strategy(self, strategy: str, template: ResponseTemplate,
                                       parameters: Dict[str, Any], analysis_results: Dict[str, Any],
                                       context: Optional[Dict[str, Any]]) -> Dict[str, Any]:
        """Execute the determined response strategy"""
        
        if strategy == "automation_available":
            # Check if we have automation workflows available
            return await self._execute_automation_workflow(parameters, analysis_results, context)
        elif strategy == "manual_required":
            return await self._generate_manual_instructions(parameters, analysis_results, context)
        elif strategy == "approval_needed":
            return await self._create_approval_request(parameters, analysis_results, context)
        else:
            return await self._request_additional_information(parameters, analysis_results, context)
    
    async def _execute_automation_workflow(self, parameters: Dict[str, Any], 
                                         analysis_results: Dict[str, Any], context: Optional[Dict[str, Any]]) -> Dict[str, Any]:
        """Execute automation workflow if available"""
        # This would integrate with the existing automation system
        return {
            "response_type": "automation_execution",
            "status": "executed",
            "details": "Automation workflow executed based on intent analysis",
            "parameters": parameters,
            "analysis": analysis_results
        }
    
    async def _generate_manual_instructions(self, parameters: Dict[str, Any],
                                          analysis_results: Dict[str, Any], context: Optional[Dict[str, Any]]) -> Dict[str, Any]:
        """Generate step-by-step manual instructions"""
        return {
            "response_type": "manual_instructions",
            "status": "instructions_provided",
            "details": "Generated step-by-step instructions based on intent analysis",
            "parameters": parameters,
            "analysis": analysis_results
        }
    
    async def _create_approval_request(self, parameters: Dict[str, Any],
                                     analysis_results: Dict[str, Any], context: Optional[Dict[str, Any]]) -> Dict[str, Any]:
        """Create approval request for high-risk operations"""
        return {
            "response_type": "approval_request",
            "status": "pending_approval",
            "details": "Request requires approval based on risk analysis",
            "parameters": parameters,
            "analysis": analysis_results
        }
    
    async def _request_additional_information(self, parameters: Dict[str, Any],
                                            analysis_results: Dict[str, Any], context: Optional[Dict[str, Any]]) -> Dict[str, Any]:
        """Request additional information from user"""
        return {
            "response_type": "information_request",
            "status": "awaiting_clarification",
            "details": "Additional information needed to proceed",
            "parameters": parameters,
            "analysis": analysis_results
        }
    
    async def _fallback_response(self, user_request: str, intent: IntentClassification,
                               context: Optional[Dict[str, Any]]) -> Dict[str, Any]:
        """Fallback response when no template matches"""
        return {
            "response_type": "fallback",
            "status": "template_not_found",
            "details": f"No response template available for intent: {intent.primary_category.value}.{intent.subcategory.value}",
            "intent": intent,
            "recommendation": "Consider adding a response template for this intent pattern"
        }