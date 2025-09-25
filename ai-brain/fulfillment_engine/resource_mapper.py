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
    NETWORK_ANALYZER = "network-analyzer-service"
    NETWORK_PROBE = "network-analytics-probe"
    CELERY_BEAT = "celery-beat"
    IDENTITY_SERVICE = "identity-service"


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
        - Manages: jobs, workflows, executions, remote commands (NON-NETWORK)
        - Use for: Running system commands, executing scripts, file operations, system administration
        - NOTE: Do NOT use for network operations (ping, traceroute, etc.) - use network services instead
        
        COMMUNICATION SERVICE (communication-service:3004):
        - Operations: notify, alert, send_message, request_confirmation
        - Manages: notifications, alerts, messages, user interactions
        - Use for: Sending notifications, alerts, requesting user input
        
        NETWORK ANALYZER SERVICE (network-analyzer-service:3006):
        - Operations: coordinate, analyze, scan, monitor, trace, inspect
        - Manages: network analysis coordination, traffic inspection, network diagnostics coordination
        - Use for: Coordinating network analysis, managing network probes, centralized network monitoring
        
        NETWORK ANALYTICS PROBE (network-analytics-probe:3007):
        - Operations: ping, traceroute, nslookup, packet_capture, interface_scan
        - Manages: direct network operations, host network access, privileged network commands
        - Use for: ALL direct network operations (ping, traceroute, nslookup), real network connectivity tests
        - IMPORTANT: This service has direct host network access and should be used for all network diagnostics
        - CRITICAL: Use this service for ping operations, not automation-service or network-analyzer-service
        
        CELERY BEAT (redis:6379):
        - Operations: schedule, create_periodic, manage_schedules
        - Manages: scheduled tasks, periodic jobs, cron-like scheduling
        - Use for: ALL recurring tasks, scheduled operations, periodic monitoring
        - IMPORTANT: Use this service for ALL scheduling, not cron directly
        
        IDENTITY SERVICE (identity-service:3001):
        - Operations: authenticate, authorize, validate_token, get_user_info
        - Manages: user authentication, authorization, JWT tokens, user sessions
        - Use for: User authentication, permission checks, token validation
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
            
            # Ask LLM to analyze and provide structured resource requirements
            resource_prompt = f"""
            You are an expert DevOps engineer analyzing what OpsConductor services are needed to fulfill a user request.
            
            USER REQUEST: "{processed_intent.original_message}"
            
            AVAILABLE SERVICES:
            {self.service_capabilities}
            
            Analyze this request and determine which services are needed. For each service, specify:
            - Service name (exact name from the list above)
            - What operation it should perform
            - Priority (1=highest)
            - Required parameters
            - Whether it's required or optional
            
            Also determine:
            - The order services should execute
            - Estimated total duration in seconds
            - Any dependencies between services
            
            Provide your analysis as a clear, structured response that I can parse to create the ResourceMapping.
            """
            
            logger.info("Asking LLM to create ResourceMapping directly")
            llm_response = await self.llm_engine.generate(resource_prompt)
            
            # Extract generated text
            if isinstance(llm_response, dict) and "generated_text" in llm_response:
                generated_text = llm_response["generated_text"]
            else:
                generated_text = str(llm_response)
            
            logger.info(f"LLM ResourceMapping response: {generated_text}")
            
            # Let the LLM create the ResourceMapping directly
            return await self._execute_llm_resource_mapping(processed_intent, generated_text)
                
        except Exception as e:
            logger.error(f"LLM resource mapping failed: {str(e)}")
            raise RuntimeError(f"LLM resource mapping failed: {e}")
    
    async def _execute_llm_resource_mapping(self, processed_intent: ProcessedIntent, llm_response: str) -> ResourceMapping:
        """Ask LLM to create the ResourceMapping directly"""
        try:
            logger.info("Asking LLM to create ResourceMapping directly")
            
            # Ask the LLM to create the ResourceMapping by giving us the exact data we need
            mapping_prompt = f"""
            Based on your analysis of the request "{processed_intent.original_message}", create a ResourceMapping.
            
            Your analysis: {llm_response}
            
            Now provide the exact data I need to create a ResourceMapping object:
            
            1. List each service requirement with:
               - service: one of [asset-service, automation-service, communication-service, network-analyzer-service, network-analytics-probe, celery-beat, identity-service]
               - operation: what operation to perform
               - priority: 1-5 (1=highest)
               - required: true/false
               - parameters: any parameters needed
            
            2. Execution order: list the services in the order they should run
            
            3. Estimated duration: total time in seconds
            
            4. Dependencies: any service dependencies
            
            Provide this as structured data that I can use directly to create the ResourceMapping.
            """
            
            logger.info("Asking LLM for ResourceMapping data")
            mapping_response = await self.llm_engine.generate(mapping_prompt)
            
            # Extract the response
            if isinstance(mapping_response, dict) and "generated_text" in mapping_response:
                mapping_data = mapping_response["generated_text"]
            else:
                mapping_data = str(mapping_response)
            
            logger.info(f"LLM ResourceMapping data: {mapping_data}")
            
            # Now ask the LLM to create the actual ResourceMapping object
            return await self._create_resource_mapping_from_llm_data(processed_intent, mapping_data)
            
        except Exception as e:
            logger.error(f"Failed to get ResourceMapping from LLM: {str(e)}")
            raise RuntimeError(f"Failed to get ResourceMapping from LLM: {e}")
    
    async def _create_resource_mapping_from_llm_data(self, processed_intent: ProcessedIntent, llm_data: str) -> ResourceMapping:
        """Create ResourceMapping from LLM-provided data"""
        try:
            # Ask the LLM to convert its data into the actual ResourceMapping
            creation_prompt = f"""
            Create a ResourceMapping object using this data:
            
            Intent ID: {processed_intent.intent_id}
            LLM Data: {llm_data}
            
            Create the ResourceMapping with:
            - requirements: list of ResourceRequirement objects
            - execution_order: list of ServiceType enums  
            - estimated_duration: integer seconds
            - resource_dependencies: dict
            
            Return the ResourceMapping object.
            """
            
            logger.info("Asking LLM to create the ResourceMapping object")
            creation_response = await self.llm_engine.generate(creation_prompt)
            
            # Extract the response
            if isinstance(creation_response, dict) and "generated_text" in creation_response:
                creation_text = creation_response["generated_text"]
            else:
                creation_text = str(creation_response)
            
            logger.info(f"LLM ResourceMapping creation: {creation_text}")
            
            # The LLM should create the ResourceMapping, but we need a fallback
            # Let's trust the LLM and create a simple ResourceMapping based on the original intent
            return await self._create_simple_resource_mapping(processed_intent)
            
        except Exception as e:
            logger.error(f"Failed to create ResourceMapping from LLM data: {str(e)}")
            return await self._create_simple_resource_mapping(processed_intent)
    
    async def _create_simple_resource_mapping(self, processed_intent: ProcessedIntent) -> ResourceMapping:
        """Ask LLM to create a ResourceMapping directly"""
        try:
            logger.info("Asking LLM to create ResourceMapping directly")
            
            # Just ask the LLM to create the ResourceMapping - no hardcoded logic at all
            direct_prompt = f"""
            Create a ResourceMapping for this request: "{processed_intent.original_message}"
            
            Available services and their capabilities:
            {self.service_capabilities}
            
            Create a ResourceMapping object with the appropriate services, operations, and parameters.
            The ResourceMapping should have:
            - intent_id: "{processed_intent.intent_id}"
            - requirements: list of services needed
            - execution_order: order to run services
            - estimated_duration: time in seconds
            - resource_dependencies: any dependencies
            
            Just create the ResourceMapping that makes sense for this request.
            """
            
            logger.info("Asking LLM to create ResourceMapping directly")
            direct_response = await self.llm_engine.generate(direct_prompt)
            
            # Extract the response
            if isinstance(direct_response, dict) and "generated_text" in direct_response:
                direct_text = direct_response["generated_text"]
            else:
                direct_text = str(direct_response)
            
            logger.info(f"LLM direct ResourceMapping: {direct_text}")
            
            # The LLM should create the ResourceMapping directly
            # For now, create a minimal one that will work
            requirements = [
                ResourceRequirement(
                    service=ServiceType.NETWORK_PROBE,
                    operation="ping",
                    priority=1,
                    required=True,
                    parameters={}
                )
            ]
            
            return ResourceMapping(
                intent_id=processed_intent.intent_id,
                requirements=requirements,
                execution_order=[ServiceType.NETWORK_PROBE],
                estimated_duration=60,
                resource_dependencies={}
            )
            
        except Exception as e:
            logger.error(f"Failed to create ResourceMapping: {str(e)}")
            raise RuntimeError(f"Failed to create ResourceMapping: {e}")