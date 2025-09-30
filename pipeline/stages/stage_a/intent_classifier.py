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
                max_tokens=200
            )
            
            # Get response from LLM
            response = await self.llm_client.generate(llm_request)
            
            # Parse the response
            intent_data = self.response_parser.parse_intent_response(response.content)
            
            # Create IntentV1 object
            return IntentV1(
                category=intent_data["category"],
                action=intent_data["action"],
                confidence=intent_data["confidence"]
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
                "get_status_info"
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
        
        if intent.category not in supported:
            return False
        
        if intent.action not in supported[intent.category]:
            return False
        
        return True
    
    async def classify_with_fallback(self, user_request: str, max_retries: int = 2) -> IntentV1:
        """
        Classify intent with retry logic
        
        🚨 CRITICAL ARCHITECTURAL PRINCIPLE: NO FALLBACK SYSTEMS
        
        OpsConductor is AI-BRAIN DEPENDENT and must FAIL FAST when LLM is unavailable.
        The pattern-based fallback below VIOLATES this principle and should be REMOVED.
        
        TODO: Remove _pattern_based_classification and let system fail when LLM is down.
        
        Args:
            user_request: User request to classify
            max_retries: Maximum number of retries
            
        Returns:
            IntentV1 object with classification
        """
        last_intent = None
        
        for attempt in range(max_retries + 1):
            try:
                intent = await self.classify_intent(user_request)
                last_intent = intent
                
                # Validate the intent
                if self.validate_intent(intent):
                    return intent
                
                # If invalid, try again with lower temperature
                if attempt < max_retries:
                    continue
                
            except Exception as e:
                if attempt == max_retries:
                    # FAIL FAST: OpsConductor requires AI-BRAIN to function
                    raise Exception(f"AI-BRAIN (LLM) unavailable - OpsConductor cannot function without LLM: {str(e)}")
        
        # If we have an invalid intent after retries, return it with low confidence
        # This allows the orchestrator's clarification system to handle it
        if last_intent:
            # Force low confidence for invalid intents to trigger clarification
            last_intent.confidence = 0.3
            return last_intent
        
        # Should not reach here, but just in case - FAIL FAST
        raise Exception("AI-BRAIN (LLM) unavailable - OpsConductor cannot function without LLM")
    
    # 🚨 ARCHITECTURAL VIOLATION REMOVED
    # The _pattern_based_classification method has been REMOVED because it violates
    # the core architectural principle: OpsConductor is AI-BRAIN DEPENDENT and must
    # FAIL FAST when LLM is unavailable. No fallback systems should exist.