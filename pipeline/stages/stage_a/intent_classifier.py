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
            # Fallback to default intent with low confidence
            return IntentV1(
                category="unknown",
                action="unknown",
                confidence=0.0
            )
    
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
                "restore_data"
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
        Classify intent with fallback and retry logic
        
        Args:
            user_request: User request to classify
            max_retries: Maximum number of retries
            
        Returns:
            IntentV1 object with classification
        """
        for attempt in range(max_retries + 1):
            try:
                intent = await self.classify_intent(user_request)
                
                # Validate the intent
                if self.validate_intent(intent):
                    return intent
                
                # If invalid, try again with lower temperature
                if attempt < max_retries:
                    continue
                
            except Exception as e:
                if attempt == max_retries:
                    # Use smart pattern-based fallback instead of defaulting to information
                    return self._pattern_based_classification(user_request)
        
        # Should not reach here, but just in case
        return self._pattern_based_classification(user_request)
    
    def _pattern_based_classification(self, user_request: str) -> IntentV1:
        """
        Pattern-based classification fallback when LLM is unavailable
        
        Args:
            user_request: User request to classify
            
        Returns:
            IntentV1 object with pattern-based classification
        """
        request_lower = user_request.lower()
        
        # Action patterns - these should be classified as ACTION, not INFO
        action_patterns = {
            # Service management
            ("restart", "service"): ("automation", "restart_service", 0.8),
            ("start", "service"): ("automation", "start_service", 0.8),
            ("stop", "service"): ("automation", "stop_service", 0.8),
            ("restart", "apache"): ("automation", "restart_service", 0.8),
            ("restart", "nginx"): ("automation", "restart_service", 0.8),
            ("restart", "mysql"): ("automation", "restart_service", 0.8),
            
            # Deployment and execution
            ("deploy", "application"): ("automation", "deploy_application", 0.8),
            ("run", "script"): ("automation", "run_script", 0.8),
            ("execute", "command"): ("automation", "execute_command", 0.8),
            ("backup", "data"): ("automation", "backup_data", 0.8),
            ("restore", "data"): ("automation", "restore_data", 0.8),
            
            # Configuration changes
            ("update", "config"): ("configuration", "update_config", 0.8),
            ("change", "settings"): ("configuration", "change_settings", 0.8),
            ("modify", "parameters"): ("configuration", "modify_parameters", 0.8),
            ("configure", "service"): ("configuration", "configure_service", 0.8),
            ("set", "permissions"): ("configuration", "set_permissions", 0.8),
            
            # Troubleshooting actions
            ("fix", "problem"): ("troubleshooting", "fix_problem", 0.8),
            ("diagnose", "issue"): ("troubleshooting", "diagnose_issue", 0.8),
            ("investigate", "error"): ("troubleshooting", "investigate_error", 0.8),
            ("debug", "application"): ("troubleshooting", "debug_application", 0.8),
            
            # Emergency patterns - these should always be ACTION
            ("urgent", "database"): ("automation", "emergency_response", 0.9),
            ("emergency", "down"): ("automation", "emergency_response", 0.9),
            ("critical", "issue"): ("automation", "emergency_response", 0.9),
            ("database", "down"): ("automation", "emergency_response", 0.9),
            ("server", "down"): ("automation", "emergency_response", 0.9),
            ("system", "down"): ("automation", "emergency_response", 0.9),
            ("outage", "users"): ("automation", "emergency_response", 0.9),
        }
        
        # Information patterns
        info_patterns = {
            ("show", "status"): ("information", "get_status_info", 0.8),
            ("get", "help"): ("information", "get_help", 0.8),
            ("explain", "concept"): ("information", "explain_concept", 0.8),
            ("show", "documentation"): ("information", "show_documentation", 0.8),
            ("list", "resources"): ("information", "list_resources", 0.8),
            ("describe", "system"): ("information", "describe_system", 0.8),
            ("what", "is"): ("information", "explain_concept", 0.7),
            ("how", "to"): ("information", "show_examples", 0.7),
        }
        
        # Monitoring patterns
        monitoring_patterns = {
            ("check", "status"): ("monitoring", "check_status", 0.8),
            ("view", "logs"): ("monitoring", "view_logs", 0.8),
            ("get", "metrics"): ("monitoring", "get_metrics", 0.8),
            ("check", "health"): ("monitoring", "check_health", 0.8),
            ("monitor", "performance"): ("monitoring", "monitor_performance", 0.8),
            ("view", "dashboard"): ("monitoring", "view_dashboard", 0.8),
            ("check", "alerts"): ("monitoring", "check_alerts", 0.8),
        }
        
        # Check action patterns first (higher priority)
        for (word1, word2), (category, action, confidence) in action_patterns.items():
            if word1 in request_lower and word2 in request_lower:
                return IntentV1(
                    category=category,
                    action=action,
                    confidence=confidence
                )
        
        # Check monitoring patterns
        for (word1, word2), (category, action, confidence) in monitoring_patterns.items():
            if word1 in request_lower and word2 in request_lower:
                return IntentV1(
                    category=category,
                    action=action,
                    confidence=confidence
                )
        
        # Check information patterns
        for (word1, word2), (category, action, confidence) in info_patterns.items():
            if word1 in request_lower and word2 in request_lower:
                return IntentV1(
                    category=category,
                    action=action,
                    confidence=confidence
                )
        
        # Emergency single word patterns (highest priority)
        if any(word in request_lower for word in ["urgent", "emergency", "critical", "down", "outage", "failure", "crashed"]):
            return IntentV1(
                category="automation",
                action="emergency_response",
                confidence=0.8
            )
        
        # Single word action patterns
        if any(word in request_lower for word in ["restart", "start", "stop", "deploy", "execute", "run", "backup", "restore", "fix", "configure", "update", "modify"]):
            return IntentV1(
                category="automation",
                action="execute_command",
                confidence=0.6
            )
        
        # Single word monitoring patterns  
        if any(word in request_lower for word in ["check", "monitor", "view", "show", "get"]):
            return IntentV1(
                category="monitoring",
                action="check_status",
                confidence=0.6
            )
        
        # Default fallback to information
        return IntentV1(
            category="information",
            action="get_help",
            confidence=0.3
        )