"""
Confidence Scorer for Stage A
Assesses overall confidence in classification and entity extraction
"""

from typing import List, Dict, Any
from ...schemas.decision_v1 import IntentV1, EntityV1, ConfidenceLevel
from llm.client import LLMClient, LLMRequest
from llm.prompt_manager import PromptManager, PromptType
from llm.response_parser import ResponseParser

class ConfidenceScorer:
    """Scores confidence in Stage A classifications"""
    
    def __init__(self, llm_client: LLMClient):
        self.llm_client = llm_client
        self.prompt_manager = PromptManager()
        self.response_parser = ResponseParser()
    
    async def calculate_overall_confidence(
        self, 
        user_request: str,
        intent: IntentV1,
        entities: List[EntityV1]
    ) -> Dict[str, Any]:
        """
        Calculate overall confidence for the classification
        
        Args:
            user_request: Original user request
            intent: Classified intent
            entities: Extracted entities
            
        Returns:
            Dictionary with confidence score and level
        """
        # Get LLM-based confidence assessment
        llm_confidence = await self._get_llm_confidence(user_request, intent, entities)
        
        # Calculate rule-based confidence
        rule_confidence = self._calculate_rule_based_confidence(user_request, intent, entities)
        
        # Combine confidences (weighted average)
        overall_confidence = (llm_confidence * 0.6) + (rule_confidence * 0.4)
        
        # Determine confidence level
        confidence_level = self._determine_confidence_level(overall_confidence)
        
        return {
            "overall_confidence": overall_confidence,
            "confidence_level": confidence_level,
            "llm_confidence": llm_confidence,
            "rule_confidence": rule_confidence
        }
    
    async def _get_llm_confidence(
        self,
        user_request: str,
        intent: IntentV1,
        entities: List[EntityV1]
    ) -> float:
        """Get confidence assessment from LLM"""
        try:
            # Format entities for prompt
            entities_str = ", ".join([f"{e.type}:{e.value}" for e in entities])
            intent_str = f"{intent.category}/{intent.action}"
            
            # Get confidence scoring prompt
            prompts = self.prompt_manager.get_prompt(
                PromptType.CONFIDENCE_SCORING,
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
            
            # Parse confidence score
            confidence = self.response_parser.parse_confidence_response(response.content)
            
            return confidence
            
        except Exception as e:
            # Fallback to rule-based confidence if LLM fails
            return self._calculate_rule_based_confidence(user_request, intent, entities)
    
    def _calculate_rule_based_confidence(
        self,
        user_request: str,
        intent: IntentV1,
        entities: List[EntityV1]
    ) -> float:
        """Calculate confidence using rule-based approach"""
        confidence_factors = []
        
        # Factor 1: Intent confidence
        confidence_factors.append(intent.confidence)
        
        # Factor 2: Entity confidence (average of top entities)
        if entities:
            entity_confidences = [e.confidence for e in entities[:3]]  # Top 3 entities
            avg_entity_confidence = sum(entity_confidences) / len(entity_confidences)
            confidence_factors.append(avg_entity_confidence)
        else:
            # No entities found - depends on intent type
            if intent.category in ["information", "monitoring"]:
                confidence_factors.append(0.8)  # These often don't need entities
            else:
                confidence_factors.append(0.3)  # Action intents usually need entities
        
        # Factor 3: Request clarity (based on length and keywords)
        clarity_score = self._assess_request_clarity(user_request)
        confidence_factors.append(clarity_score)
        
        # Factor 4: Technical term presence
        tech_score = self._assess_technical_terms(user_request)
        confidence_factors.append(tech_score)
        
        # Calculate weighted average
        weights = [0.3, 0.3, 0.2, 0.2]  # Intent, entities, clarity, tech terms
        overall_confidence = sum(f * w for f, w in zip(confidence_factors, weights))
        
        return min(1.0, max(0.0, overall_confidence))
    
    def _assess_request_clarity(self, user_request: str) -> float:
        """Assess clarity of the user request"""
        request_lower = user_request.lower()
        
        # Positive indicators
        positive_score = 0.0
        
        # Clear action words
        action_words = [
            "restart", "start", "stop", "check", "show", "list", "get", "set",
            "update", "install", "remove", "deploy", "backup", "restore"
        ]
        if any(word in request_lower for word in action_words):
            positive_score += 0.3
        
        # Specific technical terms
        tech_terms = [
            "service", "server", "database", "application", "container",
            "nginx", "apache", "mysql", "docker", "kubernetes"
        ]
        if any(term in request_lower for term in tech_terms):
            positive_score += 0.2
        
        # Reasonable length (not too short, not too long)
        word_count = len(user_request.split())
        if 3 <= word_count <= 15:
            positive_score += 0.2
        elif word_count < 3:
            positive_score -= 0.2
        
        # Negative indicators
        negative_score = 0.0
        
        # Vague words
        vague_words = ["something", "anything", "stuff", "thing", "maybe", "perhaps"]
        if any(word in request_lower for word in vague_words):
            negative_score -= 0.2
        
        # Question marks (often indicate uncertainty)
        if "?" in user_request:
            negative_score -= 0.1
        
        # Multiple exclamation marks (often indicate frustration/unclear)
        if user_request.count("!") > 1:
            negative_score -= 0.1
        
        final_score = positive_score + negative_score
        return min(1.0, max(0.0, 0.5 + final_score))  # Base score of 0.5
    
    def _assess_technical_terms(self, user_request: str) -> float:
        """Assess presence of technical terms"""
        request_lower = user_request.lower()
        
        # Technical term categories
        tech_categories = {
            "services": ["nginx", "apache", "mysql", "postgresql", "redis", "mongodb"],
            "commands": ["systemctl", "docker", "kubectl", "git", "curl", "wget"],
            "systems": ["linux", "ubuntu", "centos", "windows", "kubernetes", "aws"],
            "protocols": ["http", "https", "ssh", "ftp", "tcp", "udp"],
            "formats": ["json", "xml", "yaml", "csv", "log"]
        }
        
        found_categories = 0
        total_terms_found = 0
        
        for category, terms in tech_categories.items():
            category_found = False
            for term in terms:
                if term in request_lower:
                    total_terms_found += 1
                    category_found = True
            
            if category_found:
                found_categories += 1
        
        # Score based on diversity and quantity of technical terms
        category_score = found_categories / len(tech_categories)
        term_score = min(1.0, total_terms_found / 5)  # Normalize to max 5 terms
        
        return (category_score * 0.6) + (term_score * 0.4)
    
    def _determine_confidence_level(self, confidence_score: float) -> ConfidenceLevel:
        """Determine confidence level from score"""
        if confidence_score >= 0.8:
            return ConfidenceLevel.HIGH
        elif confidence_score >= 0.5:
            return ConfidenceLevel.MEDIUM
        else:
            return ConfidenceLevel.LOW
    
    def get_confidence_explanation(
        self,
        user_request: str,
        intent: IntentV1,
        entities: List[EntityV1],
        confidence_data: Dict[str, Any]
    ) -> str:
        """
        Generate human-readable explanation of confidence assessment
        
        Args:
            user_request: Original request
            intent: Classified intent
            entities: Extracted entities
            confidence_data: Confidence calculation results
            
        Returns:
            Human-readable explanation string
        """
        explanations = []
        
        confidence_level = confidence_data["confidence_level"]
        overall_confidence = confidence_data["overall_confidence"]
        
        # Overall assessment
        if confidence_level == ConfidenceLevel.HIGH:
            explanations.append("High confidence: Request is clear and well-understood.")
        elif confidence_level == ConfidenceLevel.MEDIUM:
            explanations.append("Medium confidence: Request is mostly clear but may need clarification.")
        else:
            explanations.append("Low confidence: Request is ambiguous and likely needs clarification.")
        
        # Intent confidence
        if intent.confidence >= 0.8:
            explanations.append(f"Intent '{intent.category}/{intent.action}' identified with high confidence.")
        elif intent.confidence >= 0.5:
            explanations.append(f"Intent '{intent.category}/{intent.action}' identified with moderate confidence.")
        else:
            explanations.append(f"Intent '{intent.category}/{intent.action}' identified with low confidence.")
        
        # Entity assessment
        if entities:
            high_conf_entities = [e for e in entities if e.confidence >= 0.8]
            if high_conf_entities:
                explanations.append(f"Found {len(high_conf_entities)} high-confidence entities.")
            else:
                explanations.append("Entities found but with lower confidence.")
        else:
            if intent.category in ["information", "monitoring"]:
                explanations.append("No specific entities required for this type of request.")
            else:
                explanations.append("No entities found - may need more specific information.")
        
        return " ".join(explanations)