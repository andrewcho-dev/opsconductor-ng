"""
Resource Mapper - LLM-Powered Resource Planning

Uses LLM intelligence to determine what OpsConductor resources are needed
to fulfill any user request. NO HARDCODED RULES OR TEMPLATES!
"""

import logging
import json
from typing import Dict, Any, List, Optional
from dataclasses import dataclass
from enum import Enum

from .intent_processor import ProcessedIntent

logger = logging.getLogger(__name__)


class ServiceType(Enum):
    """OpsConductor service types"""
    ASSET_SERVICE = "asset-service"
    AUTOMATION_SERVICE = "automation-service"
    COMMUNICATION_SERVICE = "communication-service"
    NETWORK_ANALYZER = "network-analyzer"
    CELERY_BEAT = "celery-beat"


@dataclass
class ResourceRequirement:
    """Requirement for a specific resource"""
    service: ServiceType
    operation: str
    priority: int  # 1 = highest priority
    required: bool = True
    parameters: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.parameters is None:
            self.parameters = {}


@dataclass
class ResourceMapping:
    """Complete mapping of intent to required resources"""
    intent_id: str
    requirements: List[ResourceRequirement]
    execution_order: List[ServiceType]
    estimated_duration: int  # seconds
    resource_dependencies: Dict[ServiceType, List[ServiceType]] = None
    
    def __post_init__(self):
        if self.resource_dependencies is None:
            self.resource_dependencies = {}


class ResourceMapper:
    """
    LLM-Powered Resource Mapper - Uses AI to determine required resources
    
    NO HARDCODED RULES! LLM decides what services are needed for any request.
    """
    
    def __init__(self, llm_engine=None):
        """Initialize the LLM-Powered Resource Mapper"""
        self.llm_engine = llm_engine
        self.service_capabilities = self._get_service_capabilities()
        logger.info("LLM-Powered Resource Mapper initialized")
    
    def _get_service_capabilities(self) -> str:
        """Get OpsConductor service capabilities for LLM context"""
        return """
        OPSCONDUCTOR SERVICES AVAILABLE:
        
        ASSET SERVICE (asset-service:3002):
        - Operations: query, list, get_details, get_credentials, validate_access
        - Manages: servers, networks, credentials, inventory, system information
        - Use for: Finding servers, getting system details, credential management
        
        AUTOMATION SERVICE (automation-service:3003):
        - Operations: execute, schedule, monitor, cancel, create_job
        - Manages: jobs, workflows, executions, remote commands
        - Use for: Running commands, executing scripts, system operations
        
        COMMUNICATION SERVICE (communication-service:3004):
        - Operations: notify, alert, send_message, request_confirmation
        - Manages: notifications, alerts, messages, user interactions
        - Use for: Sending notifications, alerts, requesting user input
        
        NETWORK ANALYZER (network-analyzer-service:3006):
        - Operations: analyze, scan, monitor, trace, inspect
        - Manages: network analysis, traffic inspection, connectivity testing
        - Use for: Network diagnostics, connectivity tests, traffic analysis
        
        CELERY BEAT (redis:6379):
        - Operations: schedule, create_periodic, manage_schedules
        - Manages: scheduled tasks, periodic jobs, cron-like scheduling
        - Use for: Recurring tasks, scheduled operations, periodic monitoring
        """
    
    async def map_intent_to_resources(self, processed_intent: ProcessedIntent) -> ResourceMapping:
        """
        LLM-POWERED resource mapping - NO HARDCODED RULES!
        
        Uses LLM intelligence to determine what OpsConductor services are needed
        to fulfill the user's request.
        
        Args:
            processed_intent: Processed intent from IntentProcessor
            
        Returns:
            ResourceMapping with all required resources and execution order
        """
        try:
            logger.info(f"LLM analyzing resource requirements for intent: {processed_intent.intent_id}")
            
            if not self.llm_engine:
                raise RuntimeError("LLM engine not available - cannot perform resource mapping")
            
            # Create comprehensive prompt for LLM resource analysis
            resource_prompt = f"""
            You are an expert DevOps engineer analyzing what OpsConductor services are needed to fulfill a user request.
            
            USER REQUEST ANALYSIS:
            Intent ID: {processed_intent.intent_id}
            Intent Type: {processed_intent.intent_type.value}
            Description: {processed_intent.description}
            Original Message: {processed_intent.original_message}
            Risk Level: {processed_intent.risk_level.value}
            Confidence: {processed_intent.confidence}
            
            TARGET SYSTEMS: {processed_intent.target_systems}
            OPERATIONS: {processed_intent.operations}
            PARAMETERS: {processed_intent.parameters}
            
            REQUIREMENTS FLAGS:
            - Requires Asset Info: {processed_intent.requires_asset_info}
            - Requires Network Info: {processed_intent.requires_network_info}
            - Requires Credentials: {processed_intent.requires_credentials}
            
            {self.service_capabilities}
            
            TASK: Analyze this request and determine exactly which OpsConductor services are needed, in what order, and with what operations.
            
            IMPORTANT GUIDELINES:
            1. Think step by step about what needs to happen to fulfill this request
            2. Consider dependencies between services (e.g., need asset info before automation)
            3. Include ALL necessary services - don't skip any required steps
            4. Estimate realistic duration based on the complexity of operations
            5. Set appropriate priorities (1 = highest priority, execute first)
            
            RESPOND WITH JSON ONLY:
            {{
                "requirements": [
                    {{
                        "service": "asset-service|automation-service|communication-service|network-analyzer|celery-beat",
                        "operation": "specific_operation_name",
                        "priority": 1-10,
                        "required": true/false,
                        "parameters": {{"key": "value"}},
                        "reasoning": "why this service is needed"
                    }}
                ],
                "execution_order": ["service1", "service2", "service3"],
                "dependencies": {{
                    "service_name": ["depends_on_service1", "depends_on_service2"]
                }},
                "estimated_duration_seconds": 60,
                "reasoning": "overall analysis of why these services are needed"
            }}
            
            EXAMPLES OF SERVICE USAGE:
            - Asset queries → asset-service (query, get_details)
            - Server commands → asset-service (get_credentials) + automation-service (execute)
            - Network tests → network-analyzer (analyze, scan)
            - Notifications → communication-service (notify, alert)
            - Scheduled tasks → celery-beat (schedule, create_periodic)
            - Recurring operations → celery-beat + automation-service
            """
            
            logger.info("Sending resource analysis request to LLM")
            llm_response = await self.llm_engine.generate(resource_prompt)
            
            # Extract generated text
            if isinstance(llm_response, dict) and "generated_text" in llm_response:
                generated_text = llm_response["generated_text"]
            else:
                generated_text = str(llm_response)
            
            logger.info(f"LLM resource analysis response: {generated_text}")
            
            # Clean and parse JSON response
            try:
                # Remove any markdown code blocks
                if "```json" in generated_text:
                    generated_text = generated_text.split("```json")[1].split("```")[0]
                elif "```" in generated_text:
                    generated_text = generated_text.split("```")[1].split("```")[0]
                
                resource_analysis = json.loads(generated_text.strip())
                logger.info(f"Parsed LLM resource analysis: {resource_analysis}")
                
                # Convert LLM response to ResourceMapping
                return await self._convert_llm_analysis_to_mapping(processed_intent, resource_analysis)
                
            except json.JSONDecodeError as e:
                logger.error(f"Failed to parse LLM resource analysis as JSON: {e}")
                logger.error(f"Raw LLM Response: {generated_text}")
                raise RuntimeError(f"LLM returned invalid JSON for resource analysis: {e}")
                
        except Exception as e:
            logger.error(f"LLM resource mapping failed: {str(e)}")
            raise RuntimeError(f"LLM resource mapping failed: {e}")
    
    async def _convert_llm_analysis_to_mapping(self, processed_intent: ProcessedIntent, resource_analysis: Dict[str, Any]) -> ResourceMapping:
        """Convert LLM resource analysis to ResourceMapping object"""
        try:
            requirements = []
            
            # Convert LLM requirements to ResourceRequirement objects
            for req_data in resource_analysis.get("requirements", []):
                service_name = req_data.get("service")
                
                # Map service name to ServiceType enum
                service_type = None
                for service in ServiceType:
                    if service.value == service_name:
                        service_type = service
                        break
                
                if not service_type:
                    logger.warning(f"Unknown service type: {service_name}, skipping")
                    continue
                
                requirement = ResourceRequirement(
                    service=service_type,
                    operation=req_data.get("operation", "execute"),
                    priority=req_data.get("priority", 5),
                    required=req_data.get("required", True),
                    parameters=req_data.get("parameters", {})
                )
                requirements.append(requirement)
            
            # Convert execution order
            execution_order = []
            for service_name in resource_analysis.get("execution_order", []):
                for service in ServiceType:
                    if service.value == service_name:
                        execution_order.append(service)
                        break
            
            # Convert dependencies
            dependencies = {}
            for service_name, deps in resource_analysis.get("dependencies", {}).items():
                service_type = None
                for service in ServiceType:
                    if service.value == service_name:
                        service_type = service
                        break
                
                if service_type:
                    dep_services = []
                    for dep_name in deps:
                        for service in ServiceType:
                            if service.value == dep_name:
                                dep_services.append(service)
                                break
                    dependencies[service_type] = dep_services
            
            # Create ResourceMapping
            resource_mapping = ResourceMapping(
                intent_id=processed_intent.intent_id,
                requirements=requirements,
                execution_order=execution_order,
                estimated_duration=resource_analysis.get("estimated_duration_seconds", 60),
                resource_dependencies=dependencies
            )
            
            logger.info(f"LLM resource mapping completed: {len(requirements)} requirements, {resource_mapping.estimated_duration}s estimated")
            logger.info(f"LLM reasoning: {resource_analysis.get('reasoning', 'No reasoning provided')}")
            
            return resource_mapping
            
        except Exception as e:
            logger.error(f"Failed to convert LLM analysis to ResourceMapping: {str(e)}")
            raise RuntimeError(f"Failed to convert LLM analysis: {e}")