"""
Risk Assessor for Stage A
Assesses operational risk for classified intents and entities
"""

from typing import List, Dict, Any
from ...schemas.decision_v1 import IntentV1, EntityV1, RiskLevel
from llm.client import LLMClient, LLMRequest
from llm.prompt_manager import PromptManager, PromptType
from llm.response_parser import ResponseParser

class RiskAssessor:
    """Assesses operational risk for Stage A classifications"""
    
    def __init__(self, llm_client: LLMClient):
        self.llm_client = llm_client
        self.prompt_manager = PromptManager()
        self.response_parser = ResponseParser()
        self.risk_rules = self._load_risk_rules()
    
    def _load_risk_rules(self) -> Dict[str, Any]:
        """Load risk assessment rules"""
        return {
            "high_risk_actions": [
                "delete", "remove", "drop", "truncate", "format", "wipe",
                "shutdown", "reboot", "kill", "terminate", "destroy"
            ],
            "medium_risk_actions": [
                "restart", "stop", "update", "modify", "change", "deploy",
                "backup", "restore", "migrate", "scale"
            ],
            "low_risk_actions": [
                "start", "check", "show", "list", "get", "view", "read",
                "status", "info", "help", "describe"
            ],
            "high_risk_entities": [
                "production", "prod", "database", "db", "master", "primary"
            ],
            "medium_risk_entities": [
                "staging", "stage", "service", "application", "server"
            ],
            "critical_combinations": [
                {"action": "delete", "entity_type": "database"},
                {"action": "drop", "entity_type": "database"},
                {"action": "shutdown", "entity_type": "hostname", "entity_value": "prod"},
                {"action": "remove", "entity_type": "service", "entity_value": "production"}
            ]
        }
    
    async def assess_risk(
        self,
        user_request: str,
        intent: IntentV1,
        entities: List[EntityV1]
    ) -> Dict[str, Any]:
        """
        Assess operational risk for the classified request
        
        Args:
            user_request: Original user request
            intent: Classified intent
            entities: Extracted entities
            
        Returns:
            Dictionary with risk level and assessment details
        """
        # Get LLM-based risk assessment
        llm_risk = await self._get_llm_risk_assessment(user_request, intent, entities)
        
        # Calculate rule-based risk
        rule_risk = self._calculate_rule_based_risk(intent, entities)
        
        # Combine assessments (take the higher risk)
        final_risk = self._combine_risk_assessments(llm_risk, rule_risk)
        
        # Check for critical combinations
        critical_risk = self._check_critical_combinations(intent, entities)
        if critical_risk == RiskLevel.CRITICAL:
            final_risk = critical_risk
        
        # Generate risk explanation
        explanation = self._generate_risk_explanation(
            intent, entities, final_risk, llm_risk, rule_risk
        )
        
        return {
            "risk_level": final_risk,
            "llm_risk": llm_risk,
            "rule_risk": rule_risk,
            "explanation": explanation,
            "requires_approval": self._requires_approval(final_risk, intent, entities)
        }
    
    async def _get_llm_risk_assessment(
        self,
        user_request: str,
        intent: IntentV1,
        entities: List[EntityV1]
    ) -> RiskLevel:
        """Get risk assessment from LLM"""
        try:
            # Format entities for prompt
            entities_str = ", ".join([f"{e.type}:{e.value}" for e in entities])
            intent_str = f"{intent.category}/{intent.action}"
            
            # Get risk assessment prompt
            prompts = self.prompt_manager.get_prompt(
                PromptType.RISK_ASSESSMENT,
                user_request=user_request,
                intent=intent_str,
                entities=entities_str
            )
            
            # Create LLM request
            llm_request = LLMRequest(
                prompt=prompts["user"],
                system_prompt=prompts["system"],
                temperature=0.1,
                max_tokens=50
            )
            
            # Get response from LLM
            response = await self.llm_client.generate(llm_request)
            
            # Parse risk level
            risk_str = self.response_parser.parse_risk_response(response.content)
            return RiskLevel(risk_str)
            
        except Exception as e:
            # Fallback to rule-based risk if LLM fails
            return self._calculate_rule_based_risk(intent, entities)
    
    def _calculate_rule_based_risk(self, intent: IntentV1, entities: List[EntityV1]) -> RiskLevel:
        """Calculate risk using rule-based approach"""
        risk_score = 0
        
        # Assess action risk
        action_lower = intent.action.lower()
        
        if any(high_risk in action_lower for high_risk in self.risk_rules["high_risk_actions"]):
            risk_score += 3
        elif any(med_risk in action_lower for med_risk in self.risk_rules["medium_risk_actions"]):
            risk_score += 2
        elif any(low_risk in action_lower for low_risk in self.risk_rules["low_risk_actions"]):
            risk_score += 1
        else:
            risk_score += 2  # Unknown actions are medium risk
        
        # Assess entity risk
        for entity in entities:
            entity_value_lower = entity.value.lower()
            
            if any(high_risk in entity_value_lower for high_risk in self.risk_rules["high_risk_entities"]):
                risk_score += 2
            elif any(med_risk in entity_value_lower for med_risk in self.risk_rules["medium_risk_entities"]):
                risk_score += 1
        
        # Assess category risk
        if intent.category == "automation":
            risk_score += 1  # Automation has inherent risk
        elif intent.category == "troubleshooting":
            risk_score += 1  # Troubleshooting can involve risky operations
        elif intent.category == "information":
            pass  # Information requests are generally safe
        
        # Convert score to risk level
        if risk_score >= 5:
            return RiskLevel.CRITICAL
        elif risk_score >= 4:
            return RiskLevel.HIGH
        elif risk_score >= 2:
            return RiskLevel.MEDIUM
        else:
            return RiskLevel.LOW
    
    def _check_critical_combinations(self, intent: IntentV1, entities: List[EntityV1]) -> RiskLevel:
        """Check for critical risk combinations"""
        action_lower = intent.action.lower()
        
        for combo in self.risk_rules["critical_combinations"]:
            if combo["action"] in action_lower:
                # Check if matching entity exists
                for entity in entities:
                    if entity.type == combo["entity_type"]:
                        if "entity_value" in combo:
                            if combo["entity_value"] in entity.value.lower():
                                return RiskLevel.CRITICAL
                        else:
                            return RiskLevel.CRITICAL
        
        return RiskLevel.LOW  # No critical combinations found
    
    def _combine_risk_assessments(self, llm_risk: RiskLevel, rule_risk: RiskLevel) -> RiskLevel:
        """Combine LLM and rule-based risk assessments"""
        # Risk level hierarchy
        risk_hierarchy = {
            RiskLevel.LOW: 1,
            RiskLevel.MEDIUM: 2,
            RiskLevel.HIGH: 3,
            RiskLevel.CRITICAL: 4
        }
        
        # Take the higher risk
        llm_score = risk_hierarchy[llm_risk]
        rule_score = risk_hierarchy[rule_risk]
        
        max_score = max(llm_score, rule_score)
        
        # Convert back to risk level
        for risk_level, score in risk_hierarchy.items():
            if score == max_score:
                return risk_level
        
        return RiskLevel.MEDIUM  # Fallback
    
    def _requires_approval(self, risk_level: RiskLevel, intent: IntentV1, entities: List[EntityV1]) -> bool:
        """Determine if the request requires approval"""
        # Critical and high risk always require approval
        if risk_level in [RiskLevel.CRITICAL, RiskLevel.HIGH]:
            return True
        
        # Medium risk automation requires approval
        if risk_level == RiskLevel.MEDIUM and intent.category == "automation":
            return True
        
        # Production entities require approval for non-read operations
        if intent.category != "information":
            for entity in entities:
                if any(prod_term in entity.value.lower() for prod_term in ["prod", "production"]):
                    return True
        
        return False
    
    def _generate_risk_explanation(
        self,
        intent: IntentV1,
        entities: List[EntityV1],
        final_risk: RiskLevel,
        llm_risk: RiskLevel,
        rule_risk: RiskLevel
    ) -> str:
        """Generate human-readable risk explanation"""
        explanations = []
        
        # Overall risk assessment
        if final_risk == RiskLevel.CRITICAL:
            explanations.append("CRITICAL RISK: This operation could cause severe system damage or data loss.")
        elif final_risk == RiskLevel.HIGH:
            explanations.append("HIGH RISK: This operation could cause significant service disruption.")
        elif final_risk == RiskLevel.MEDIUM:
            explanations.append("MEDIUM RISK: This operation has moderate potential for issues.")
        else:
            explanations.append("LOW RISK: This operation is generally safe.")
        
        # Action-specific risks
        action_lower = intent.action.lower()
        if any(high_risk in action_lower for high_risk in self.risk_rules["high_risk_actions"]):
            explanations.append(f"Action '{intent.action}' is inherently high-risk.")
        
        # Entity-specific risks
        risky_entities = []
        for entity in entities:
            if any(high_risk in entity.value.lower() for high_risk in self.risk_rules["high_risk_entities"]):
                risky_entities.append(f"{entity.type}:{entity.value}")
        
        if risky_entities:
            explanations.append(f"High-risk entities detected: {', '.join(risky_entities)}")
        
        # Production environment warning
        prod_entities = [e for e in entities if "prod" in e.value.lower()]
        if prod_entities:
            explanations.append("Production environment detected - extra caution required.")
        
        return " ".join(explanations)
    
    def get_risk_mitigation_suggestions(
        self,
        intent: IntentV1,
        entities: List[EntityV1],
        risk_level: RiskLevel
    ) -> List[str]:
        """
        Get risk mitigation suggestions
        
        Args:
            intent: Classified intent
            entities: Extracted entities
            risk_level: Assessed risk level
            
        Returns:
            List of mitigation suggestions
        """
        suggestions = []
        
        if risk_level in [RiskLevel.HIGH, RiskLevel.CRITICAL]:
            suggestions.append("Require manual approval before execution")
            suggestions.append("Create backup before proceeding")
            suggestions.append("Test in non-production environment first")
            suggestions.append("Have rollback plan ready")
        
        if risk_level in [RiskLevel.MEDIUM, RiskLevel.HIGH, RiskLevel.CRITICAL]:
            suggestions.append("Verify target systems before execution")
            suggestions.append("Monitor system status during operation")
            suggestions.append("Have support team on standby")
        
        # Action-specific suggestions
        if "restart" in intent.action.lower():
            suggestions.append("Check service dependencies before restart")
            suggestions.append("Verify no critical processes are running")
        
        if "delete" in intent.action.lower() or "remove" in intent.action.lower():
            suggestions.append("Confirm data is backed up")
            suggestions.append("Double-check target identification")
        
        return suggestions