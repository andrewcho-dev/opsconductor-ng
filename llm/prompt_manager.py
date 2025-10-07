"""
Prompt Manager for LLM Interactions
Manages prompts for different pipeline stages
"""

from typing import Dict, Any, List, Optional
from enum import Enum

class PromptType(str, Enum):
    """Types of prompts used in the pipeline"""
    INTENT_CLASSIFICATION = "intent_classification"
    ENTITY_EXTRACTION = "entity_extraction"
    CONFIDENCE_SCORING = "confidence_scoring"
    RISK_ASSESSMENT = "risk_assessment"
    TOOL_SELECTION = "tool_selection"
    PLANNING = "planning"

class PromptManager:
    """Manages prompts for different pipeline stages"""
    
    def __init__(self):
        self.prompts = self._load_default_prompts()
    
    def _load_default_prompts(self) -> Dict[str, Dict[str, str]]:
        """Load default prompts for all stages"""
        return {
            PromptType.INTENT_CLASSIFICATION: {
                "system": """Classify infrastructure request. Return JSON: {{"category":"CAT","action":"ACTION","confidence":0.0-1.0,"capabilities":["cap1","cap2"]}}

Categories: automation|monitoring|troubleshooting|configuration|information|asset_management

Capabilities: api_query|asset_management|asset_query|credential_access|disk_management|disk_monitoring|dns_query|http_client|infrastructure_info|log_analysis|memory_monitoring|network_info|network_monitoring|network_testing|packet_capture|process_management|process_monitoring|protocol_analysis|resource_listing|secret_retrieval|service_management|system_info|system_monitoring|text_search|windows_automation|windows_service_management

Key distinctions:
- monitoring: LIVE/REAL-TIME checks (is X up?, current CPU)
- asset_management: INVENTORY queries (list servers, show IPs)
- GATED (credential_access, secret_retrieval): explicit credential requests only""",
                
                "user": "Classify: {user_request}"
            },
            
            PromptType.ENTITY_EXTRACTION: {
                "system": """Extract entities. Return JSON: [{{"type":"TYPE","value":"VALUE","confidence":0.0-1.0}}]

Types: hostname|service|command|file_path|port|environment|application|database

Return [] if none found.""",
                
                "user": "Extract from: {user_request}"
            },
            
            PromptType.CONFIDENCE_SCORING: {
                "system": """Assess confidence (0.0-1.0) and risk (low|medium|high|critical). Return JSON: {{"confidence":0.0-1.0,"risk":"LEVEL","reasoning":"brief"}}

Risk levels:
- low: Read-only, status checks
- medium: Service restarts, config changes
- high: DB operations, system changes
- critical: Data deletion, production-wide impact""",
                
                "user": "Request: {user_request}\nIntent: {intent}\nEntities: {entities}"
            },
            
            PromptType.RISK_ASSESSMENT: {
                "system": """Assess risk (low|medium|high|critical). Return one word.""",
                
                "user": "Intent: {intent}\nEntities: {entities}\nRequest: {user_request}"
            },
            
            PromptType.TOOL_SELECTION: {
                "system": """Select tools for decision. Return JSON: {{"selected_tools":[{{"tool_name":"str","justification":"str","inputs_needed":[],"execution_order":1,"depends_on":[]}}]}}

Rules: Least-privilege|Read-only for info|asset-service for infra queries|production_safe=true for prod|Score S∈[0,1]: S≥0.6→select, 0.4-0.6→clarify, <0.4→skip

Risk: low=read/status|medium=restart/config|high=delete/prod-change

Approval: Required for high-risk|prod changes|production_safe=false""",
                
                "user": "Decision: {decision}\nTools: {available_tools}"
            },
        
        PromptType.PLANNING: {
            "system": """Create execution plan. Return JSON: {{"steps":[{{"id":"str","description":"str","tool":"str","inputs":{{}},"preconditions":[],"success_criteria":[],"failure_handling":"str","estimated_duration":30,"depends_on":[]}}],"safety_checks":[{{"check":"str","stage":"before|during|after","failure_action":"abort|warn|continue"}}],"rollback_plan":[{{"step_id":"str","rollback_action":"str"}}]}}

Principles: Discovery first|Idempotent|Fail-safe|Explicit deps|Info→validate→modify

Safety: Pre-flight checks|Rollback for destructive ops|Approval for high-risk|Realistic time estimates""",
                
            "user": "Decision: {decision}\nSelection: {selection}\nSOPs: {sop_snippets}"
        }
    }
    
    def get_prompt(self, prompt_type: PromptType, **kwargs) -> Dict[str, str]:
        """
        Get formatted prompt for a specific type
        
        Args:
            prompt_type: Type of prompt to get
            **kwargs: Variables to substitute in the prompt
            
        Returns:
            Dictionary with 'system' and 'user' prompts
        """
        if prompt_type not in self.prompts:
            raise ValueError(f"Unknown prompt type: {prompt_type}")
        
        prompt_template = self.prompts[prompt_type]
        
        # Format the prompts with provided variables
        formatted_prompt = {}
        for key, template in prompt_template.items():
            try:
                formatted_prompt[key] = template.format(**kwargs)
            except KeyError as e:
                raise ValueError(f"Missing required variable {e} for prompt type {prompt_type}")
        
        return formatted_prompt
    
    def add_custom_prompt(self, prompt_type: str, system_prompt: str, user_prompt: str):
        """
        Add a custom prompt
        
        Args:
            prompt_type: Custom prompt type name
            system_prompt: System prompt template
            user_prompt: User prompt template
        """
        self.prompts[prompt_type] = {
            "system": system_prompt,
            "user": user_prompt
        }
    
    def get_available_prompt_types(self) -> List[str]:
        """Get list of available prompt types"""
        return list(self.prompts.keys())
    
    def get_tool_selection_prompt(self, decision: Dict[str, Any], available_tools: List[Dict[str, Any]]) -> Dict[str, str]:
        """
        Get tool selection prompt for Stage B
        
        Args:
            decision: Decision v1 data from Stage A
            available_tools: List of available tools with their capabilities
            
        Returns:
            Formatted prompt dictionary
        """
        import json
        
        # Format decision and tools as JSON strings for the prompt
        decision_str = json.dumps(decision, indent=2)
        tools_str = json.dumps(available_tools, indent=2)
        
        return self.get_prompt(
            PromptType.TOOL_SELECTION,
            decision=decision_str,
            available_tools=tools_str
        )