"""
Intent Classifier for Stage A
Classifies user requests into intent categories and specific actions
"""

import asyncio
from typing import Dict, Any, Optional
from ...schemas.decision_v1 import IntentV1
from llm.client import LLMClient, LLMRequest
from llm.prompt_manager import PromptManager, PromptType
from llm.response_parser import ResponseParser

class IntentClassifier:
    """Classifies user intents using LLM"""
    
    def __init__(self, llm_client: LLMClient):
        self.llm_client = llm_client
        self.prompt_manager = PromptManager()
        self.response_parser = ResponseParser()
    
    async def classify_intent(self, user_request: str) -> IntentV1:
        """
        Classify user intent from natural language request
        
        Args:
            user_request: Original user request string
            
        Returns:
            IntentV1 object with classification results
            
        Raises:
            Exception: If classification fails
        """
        try:
            # Get the intent classification prompt
            prompts = self.prompt_manager.get_prompt(
                PromptType.INTENT_CLASSIFICATION,
                user_request=user_request
            )
            
            # Create LLM request
            llm_request = LLMRequest(
                prompt=prompts["user"],
                system_prompt=prompts["system"],
                temperature=0.1,  # Low temperature for consistent classification
                max_tokens=100  # Reduced: only needs category/action
            )
            
            # Get response from LLM
            response = await self.llm_client.generate(llm_request)
            
            # Parse the response
            intent_data = self.response_parser.parse_intent_response(response.content)
            
            # Create IntentV1 object
            return IntentV1(
                category=intent_data["category"],
                action=intent_data["action"],
                confidence=intent_data["confidence"],
                capabilities=intent_data.get("capabilities", [])
            )
            
        except Exception as e:
            # FAIL FAST: OpsConductor requires AI-BRAIN to function
            raise Exception(f"AI-BRAIN (LLM) unavailable - OpsConductor cannot function without LLM: {str(e)}")
    
    def get_supported_categories(self) -> Dict[str, list]:
        """
        Get supported intent categories and their actions
        
        Returns:
            Dictionary mapping categories to lists of actions
        """
        return {
            "automation": [
                "restart_service",
                "start_service", 
                "stop_service",
                "deploy_application",
                "run_script",
                "execute_command",
                "backup_data",
                "restore_data",
                "emergency_response"
            ],
            "monitoring": [
                "check_status",
                "view_logs",
                "get_metrics",
                "check_health",
                "monitor_performance",
                "view_dashboard",
                "check_alerts"
            ],
            "troubleshooting": [
                "diagnose_issue",
                "fix_problem",
                "investigate_error",
                "diagnose_performance",
                "check_connectivity",
                "analyze_logs",
                "debug_application"
            ],
            "configuration": [
                "update_config",
                "change_settings",
                "modify_parameters",
                "update_environment",
                "configure_service",
                "set_permissions",
                "update_security"
            ],
            "information": [
                "get_help",
                "explain_concept",
                "show_documentation",
                "list_resources",
                "describe_system",
                "show_examples",
                "get_status_info",
                "calculate",
                "compute",
                "math",
                "answer_question",
                "provide_information"
            ],
            "asset_management": [
                "list_assets",
                "get_asset",
                "search_assets",
                "count_assets",
                "get_credentials",
                "list_credentials",
                "find_asset",
                "query_assets",
                "list_servers",
                "list_hosts",
                "get_asset_info",
                "asset_count",
                "asset_discovery"
            ]
        }
    
    def validate_intent(self, intent: IntentV1) -> bool:
        """
        Validate that the intent is supported
        
        Args:
            intent: Intent to validate
            
        Returns:
            True if intent is valid, False otherwise
        """
        supported = self.get_supported_categories()
        
        # Category validation - must be exact match
        if intent.category not in supported:
            return False
        
        # Action validation - allow partial matching for flexibility
        supported_actions = supported[intent.category]
        
        # Exact match first
        if intent.action in supported_actions:
            return True
        
        # Flexible matching - check if action contains any supported action keywords
        for supported_action in supported_actions:
            if supported_action in intent.action.lower() or intent.action.lower() in supported_action:
                return True
        
        # Special case: For information category, be more lenient
        if intent.category == "information":
            # Accept any reasonable information request
            info_keywords = ["help", "info", "show", "get", "explain", "calculate", "compute", "math", "question", "answer"]
            if any(keyword in intent.action.lower() for keyword in info_keywords):
                return True
        
        return False
    
    async def classify_with_fallback(self, user_request: str, max_retries: int = 0) -> IntentV1:
        """
        Classify intent - TRUST THE LLM, NO VALIDATION
        
        Args:
            user_request: User request to classify
            max_retries: Maximum number of retries (set to 0 - trust LLM first response)
            
        Returns:
            IntentV1 object with classification
        """
        try:
            # TRUST THE LLM - single call, no validation bullshit
            intent = await self.classify_intent(user_request)
            return intent
                
        except Exception as e:
            # FAIL FAST: OpsConductor requires AI-BRAIN to function
            raise Exception(f"AI-BRAIN (LLM) unavailable - OpsConductor cannot function without LLM: {str(e)}")
    
    # 🚨 ARCHITECTURAL VIOLATION REMOVED
    # The _pattern_based_classification method has been REMOVED because it violates
    # the core architectural principle: OpsConductor is AI-BRAIN DEPENDENT and must
    # FAIL FAST when LLM is unavailable. No fallback systems should exist.