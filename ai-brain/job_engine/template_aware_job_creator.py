"""
OpsConductor AI Brain - Template-Aware Job Creation Engine

This module extends the LLM job creator with knowledge of existing automation job templates.
It can intelligently decide whether to use an existing template or create a new workflow.

Key Features:
1. Template Recognition: Identifies when user requests match existing templates
2. Template Selection: Chooses the best template for the request
3. Parameter Extraction: Extracts parameters from natural language for template substitution
4. Fallback Creation: Falls back to LLM workflow generation when no template matches
"""

import logging
import json
import re
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass
from datetime import datetime
import asyncio

from integrations.llm_client import LLMEngine
from integrations.automation_client import AutomationServiceClient
from job_engine.llm_job_creator import LLMJobCreator

logger = logging.getLogger(__name__)

@dataclass
class TemplateMatch:
    """Represents a match between user request and available template"""
    template_path: str
    template_name: str
    confidence: float
    reasoning: str
    required_parameters: Dict[str, Any]
    missing_parameters: List[str]

class TemplateAwareJobCreator:
    """
    Enhanced job creator that knows about existing automation templates
    and can intelligently choose between using templates or creating new workflows
    """
    
    def __init__(self, llm_engine: LLMEngine, automation_client: Optional[AutomationServiceClient] = None):
        self.llm_engine = llm_engine
        self.automation_client = automation_client or AutomationServiceClient()
        self.llm_job_creator = LLMJobCreator(llm_engine, automation_client)
        
        # Cache for available templates
        self._templates_cache = None
        self._cache_timestamp = None
        
        # Template knowledge base - this is what teaches the AI about existing templates
        self.template_knowledge = {
            "install-windows-remote-probe.json": {
                "name": "Install OpsConductor Remote Probe on Windows",
                "description": "Automated installation of OpsConductor Network Analytics Remote Probe on Windows systems",
                "keywords": ["install", "remote probe", "windows", "probe", "network analytics", "monitoring"],
                "target_patterns": ["192.168.50.211", "windows server", "remote system"],
                "use_cases": [
                    "install remote probe on 192.168.50.211",
                    "deploy network probe to windows server",
                    "setup monitoring probe on remote windows system",
                    "install opsconductor probe on windows",
                    "deploy remote network analytics probe"
                ],
                "required_parameters": {
                    "target_host": "IP address or hostname of target Windows system",
                    "credentials": {
                        "username": "Windows administrator username",
                        "password": "Windows administrator password"
                    }
                },
                "capabilities": [
                    "Installs Python 3.11",
                    "Creates probe directory structure", 
                    "Installs probe application and dependencies",
                    "Creates Windows service",
                    "Configures automatic startup",
                    "Tests connectivity to central analyzer"
                ]
            }
        }
    
    async def create_job_from_natural_language(self, description: str, 
                                             user_context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Create a job using template-aware intelligence
        
        First tries to match the request to existing templates, then falls back to LLM generation
        """
        try:
            logger.info(f"Template-aware job creation for: {description}")
            
            # STAGE 1: Try to match request to existing templates
            template_match = await self._find_matching_template(description, user_context)
            
            if template_match and template_match.confidence >= 0.7:
                logger.info(f"✅ Found template match: {template_match.template_name} (confidence: {template_match.confidence})")
                
                # STAGE 2: Extract parameters for template
                parameters = await self._extract_template_parameters(description, template_match, user_context)
                
                # STAGE 3: Execute template-based job
                return await self._execute_template_job(template_match, parameters, description, user_context)
            
            else:
                logger.info("❌ No suitable template found, falling back to LLM workflow generation")
                
                # STAGE 4: Fall back to LLM-generated workflow
                return await self.llm_job_creator.create_job_from_natural_language(description, user_context)
                
        except Exception as e:
            logger.error(f"Error in template-aware job creation: {e}")
            return {
                "success": False,
                "error": f"Template-aware job creation failed: {str(e)}",
                "timestamp": datetime.now().isoformat()
            }
    
    async def _find_matching_template(self, description: str, 
                                    user_context: Optional[Dict[str, Any]]) -> Optional[TemplateMatch]:
        """
        Use LLM to analyze the request and find the best matching template
        """
        try:
            # Get available templates
            templates = await self._get_available_templates()
            if not templates:
                logger.warning("No templates available")
                return None
            
            # Create template knowledge for LLM
            template_info = self._build_template_knowledge_for_llm(templates)
            
            system_prompt = f"""You are an expert at matching user automation requests to existing job templates.

Available Templates:
{template_info}

Your task is to analyze the user's request and determine if it matches any existing template.

Respond with JSON only:
{{
    "best_match": {{
        "template_filename": "exact-filename.json" or null,
        "template_name": "Template Name" or null,
        "confidence": 0.0-1.0,
        "reasoning": "Why this template matches or why no match",
        "required_parameters": {{
            "parameter_name": "extracted_value_or_placeholder"
        }},
        "missing_parameters": ["list", "of", "missing", "required", "params"]
    }}
}}

Matching Guidelines:
- Confidence 0.9+: Perfect match (exact use case)
- Confidence 0.7-0.9: Good match (similar purpose, minor differences)
- Confidence 0.5-0.7: Partial match (related but significant differences)
- Confidence <0.5: Poor match (different purpose)

For remote probe installation requests:
- Look for keywords: "install", "probe", "remote", "monitoring", "network analytics"
- Target system mentions: IP addresses, "windows", "server"
- If user mentions 192.168.50.211 specifically, this strongly indicates the Windows remote probe template

Be conservative - only suggest templates with confidence ≥0.7 for actual execution."""

            prompt = f"""Analyze this automation request and find the best matching template:

User Request: "{description}"

Context: {json.dumps(user_context or {}, indent=2)}

Find the best template match:"""

            response = await self.llm_engine.chat(
                message=prompt,
                system_prompt=system_prompt,
                model=None
            )
            
            # Parse LLM response
            try:
                json_text = self._extract_json_from_response(response["response"])
                match_data = json.loads(json_text)
                
                best_match = match_data.get("best_match", {})
                
                if not best_match.get("template_filename"):
                    logger.info("LLM found no suitable template match")
                    return None
                
                return TemplateMatch(
                    template_path=best_match["template_filename"],
                    template_name=best_match.get("template_name", "Unknown"),
                    confidence=best_match.get("confidence", 0.0),
                    reasoning=best_match.get("reasoning", "No reasoning provided"),
                    required_parameters=best_match.get("required_parameters", {}),
                    missing_parameters=best_match.get("missing_parameters", [])
                )
                
            except json.JSONDecodeError as e:
                logger.error(f"Failed to parse template matching response: {e}")
                return None
                
        except Exception as e:
            logger.error(f"Error finding matching template: {e}")
            return None
    
    async def _extract_template_parameters(self, description: str, template_match: TemplateMatch,
                                         user_context: Optional[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Extract parameters from the user request for template substitution
        """
        try:
            # Get template details for parameter extraction
            template_knowledge = self.template_knowledge.get(template_match.template_path, {})
            
            system_prompt = f"""You are an expert at extracting parameters from user requests for automation templates.

Template: {template_match.template_name}
Template Requirements: {json.dumps(template_knowledge.get('required_parameters', {}), indent=2)}

Your task is to extract parameter values from the user's request.

Respond with JSON only:
{{
    "extracted_parameters": {{
        "target_host": "192.168.50.211",
        "credentials": {{
            "username": "administrator",
            "password": "ask_user_for_password"
        }}
    }},
    "confidence": 0.85,
    "missing_info": ["password needs to be provided"],
    "assumptions": ["Using default administrator account"]
}}

Parameter Extraction Guidelines:
- Extract IP addresses, hostnames, server names
- For credentials, if not provided, use placeholders like "ask_user_for_password"
- Be conservative - don't guess sensitive information
- For the Windows remote probe template, target_host is critical
- Look for specific mentions of 192.168.50.211 or other IP addresses"""

            prompt = f"""Extract parameters from this request for the template:

User Request: "{description}"
Template Match: {template_match.template_name}
Required Parameters: {json.dumps(template_match.required_parameters, indent=2)}

Extract the parameters:"""

            response = await self.llm_engine.chat(
                message=prompt,
                system_prompt=system_prompt,
                model=None
            )
            
            # Parse LLM response
            try:
                json_text = self._extract_json_from_response(response["response"])
                param_data = json.loads(json_text)
                
                extracted = param_data.get("extracted_parameters", {})
                
                # Add default credentials if not provided (for demo purposes)
                if template_match.template_path == "install-windows-remote-probe.json":
                    if "credentials" not in extracted:
                        extracted["credentials"] = {
                            "username": "Administrator",
                            "password": "OpsConductor2024!"  # Default demo password
                        }
                    
                    # Ensure target_host is set
                    if "target_host" not in extracted:
                        # Try to extract IP from description
                        ip_pattern = r'\b(?:\d{1,3}\.){3}\d{1,3}\b'
                        ip_match = re.search(ip_pattern, description)
                        if ip_match:
                            extracted["target_host"] = ip_match.group(0)
                        else:
                            extracted["target_host"] = "192.168.50.211"  # Default for demo
                
                logger.info(f"Extracted parameters: {extracted}")
                return extracted
                
            except json.JSONDecodeError as e:
                logger.error(f"Failed to parse parameter extraction response: {e}")
                return {}
                
        except Exception as e:
            logger.error(f"Error extracting template parameters: {e}")
            return {}
    
    async def _execute_template_job(self, template_match: TemplateMatch, parameters: Dict[str, Any],
                                  original_description: str, user_context: Optional[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Execute a job using the matched template
        """
        try:
            logger.info(f"Executing template job: {template_match.template_name}")
            
            # Execute the template with extracted parameters
            result = await self.automation_client.execute_job_template(
                template_path=template_match.template_path,
                parameters=parameters
            )
            
            if result.get('success'):
                return {
                    "success": True,
                    "job_id": result.get('job_id'),
                    "execution_id": result.get('execution_id'),
                    "task_id": result.get('task_id'),
                    "job_name": result.get('job_name'),
                    "response": f"I've successfully started the '{template_match.template_name}' automation using the existing template. The job is now running and will install the OpsConductor remote probe on the target system.",
                    "confidence": template_match.confidence,
                    "template_used": {
                        "template_name": template_match.template_name,
                        "template_path": template_match.template_path,
                        "confidence": template_match.confidence,
                        "reasoning": template_match.reasoning,
                        "parameters_applied": parameters
                    },
                    "execution_started": True,
                    "automation_job_id": result.get('job_id'),
                    "workflow": result.get('template_data', {}).get('workflow_definition', {}),
                    "timestamp": datetime.now().isoformat(),
                    "method": "template_based_execution"
                }
            else:
                # Template execution failed, fall back to LLM generation
                logger.warning(f"Template execution failed: {result.get('error')}, falling back to LLM generation")
                return await self.llm_job_creator.create_job_from_natural_language(original_description, user_context)
                
        except Exception as e:
            logger.error(f"Error executing template job: {e}")
            # Fall back to LLM generation on error
            return await self.llm_job_creator.create_job_from_natural_language(original_description, user_context)
    
    async def _get_available_templates(self) -> List[Dict[str, Any]]:
        """
        Get list of available templates with caching
        """
        try:
            # Check cache validity (refresh every 5 minutes)
            now = datetime.now()
            if (self._templates_cache is None or 
                self._cache_timestamp is None or 
                (now - self._cache_timestamp).total_seconds() > 300):
                
                logger.info("Refreshing templates cache")
                self._templates_cache = await self.automation_client.list_available_templates()
                self._cache_timestamp = now
            
            return self._templates_cache or []
            
        except Exception as e:
            logger.error(f"Error getting available templates: {e}")
            return []
    
    def _build_template_knowledge_for_llm(self, templates: List[Dict[str, Any]]) -> str:
        """
        Build a comprehensive knowledge base about templates for the LLM
        """
        knowledge_parts = []
        
        for template in templates:
            filename = template.get('filename', 'unknown.json')
            name = template.get('name', 'Unknown Template')
            description = template.get('description', 'No description')
            tags = template.get('tags', [])
            target_os = template.get('target_os', 'any')
            duration = template.get('estimated_duration', 'unknown')
            
            # Get enhanced knowledge from our knowledge base
            enhanced_info = self.template_knowledge.get(filename, {})
            keywords = enhanced_info.get('keywords', [])
            use_cases = enhanced_info.get('use_cases', [])
            capabilities = enhanced_info.get('capabilities', [])
            
            template_info = f"""
Template: {filename}
Name: {name}
Description: {description}
Target OS: {target_os}
Duration: {duration}
Tags: {', '.join(tags)}
Keywords: {', '.join(keywords)}
Use Cases:
{chr(10).join(f'  - {case}' for case in use_cases)}
Capabilities:
{chr(10).join(f'  - {cap}' for cap in capabilities)}
"""
            knowledge_parts.append(template_info.strip())
        
        return "\n\n".join(knowledge_parts)
    
    def _extract_json_from_response(self, response_text: str) -> str:
        """Extract JSON from LLM response that may be wrapped in markdown code blocks"""
        # First try to find JSON in code blocks
        json_pattern = r'```(?:json)?\s*(\{.*?\})\s*```'
        match = re.search(json_pattern, response_text, re.DOTALL)
        if match:
            return match.group(1)
        
        # If no code blocks, try to find JSON object directly
        json_pattern = r'\{.*\}'
        match = re.search(json_pattern, response_text, re.DOTALL)
        if match:
            return match.group(0)
        
        # If still no match, return the original text
        return response_text.strip()
    
    def get_template_knowledge_summary(self) -> Dict[str, Any]:
        """
        Get a summary of the template knowledge for debugging/monitoring
        """
        return {
            "templates_known": len(self.template_knowledge),
            "template_files": list(self.template_knowledge.keys()),
            "capabilities": [
                "Template matching via LLM analysis",
                "Parameter extraction from natural language",
                "Fallback to LLM workflow generation",
                "Template caching for performance"
            ],
            "cache_status": {
                "cached_templates": len(self._templates_cache) if self._templates_cache else 0,
                "cache_timestamp": self._cache_timestamp.isoformat() if self._cache_timestamp else None
            }
        }