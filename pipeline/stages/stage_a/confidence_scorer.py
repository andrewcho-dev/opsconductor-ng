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
        NOW ALSO RETURNS RISK (rule-based for speed, LLM fallback for edge cases)
        
        Args:
            user_request: Original user request
            intent: Classified intent
            entities: Extracted entities
            
        Returns:
            Dictionary with confidence score, level, AND risk assessment
        """
        # Calculate rule-based confidence
        rule_confidence = self._calculate_rule_based_confidence(user_request, intent, entities)
        
        # Calculate rule-based risk (fast, no LLM call)
        risk_assessment = self._calculate_rule_based_risk(user_request, intent, entities)
        
        # Only use LLM for edge cases (low confidence or ambiguous risk)
        use_llm = rule_confidence < 0.6 or risk_assessment['risk'] == 'medium'
        
        if use_llm:
            # Get LLM-based confidence AND risk assessment (merged, single call)
            llm_assessment = await self._get_llm_confidence_and_risk(user_request, intent, entities)
            
            # Combine confidences (weighted average)
            overall_confidence = (llm_assessment['confidence'] * 0.6) + (rule_confidence * 0.4)
            risk_level = llm_assessment['risk']
            risk_reasoning = llm_assessment.get('reasoning', '')
        else:
            # Use rule-based only (no LLM call - faster!)
            overall_confidence = rule_confidence
            risk_level = risk_assessment['risk']
            risk_reasoning = risk_assessment['reasoning']
        
        # Determine confidence level
        confidence_level = self._determine_confidence_level(overall_confidence)
        
        return {
            "overall_confidence": overall_confidence,
            "confidence_level": confidence_level,
            "llm_confidence": None if not use_llm else llm_assessment['confidence'],
            "rule_confidence": rule_confidence,
            "risk_level": risk_level,
            "risk_reasoning": risk_reasoning
        }
    
    async def _get_llm_confidence_and_risk(
        self,
        user_request: str,
        intent: IntentV1,
        entities: List[EntityV1]
    ) -> Dict[str, Any]:
        """
        Get MERGED confidence AND risk assessment from LLM (single call)
        This replaces separate confidence and risk LLM calls
        """
        try:
            # Format entities for prompt
            entities_str = ", ".join([f"{e.type}:{e.value}" for e in entities])
            intent_str = f"{intent.category}/{intent.action}"
            
            # Get merged confidence+risk scoring prompt
            prompts = self.prompt_manager.get_prompt(
                PromptType.CONFIDENCE_SCORING,  # Now returns both confidence AND risk
                user_request=user_request,
                intent=intent_str,
                entities=entities_str
            )
            
            # Create LLM request
            llm_request = LLMRequest(
                prompt=prompts["user"],
                system_prompt=prompts["system"],
                temperature=0.1,
                max_tokens=80  # Reduced: compact JSON response
            )
            
            # Get response from LLM
            response = await self.llm_client.generate(llm_request)
            
            # Parse merged confidence+risk response
            import json
            try:
                result = json.loads(response.content)
                # Validate response structure
                assert 'confidence' in result and 'risk' in result
                assert 0.0 <= result['confidence'] <= 1.0
                assert result['risk'] in ['low', 'medium', 'high', 'critical']
                return result
            except (json.JSONDecodeError, AssertionError, KeyError):
                # Fallback: try to parse as old format
                confidence = self.response_parser.parse_confidence_response(response.content)
                return {
                    'confidence': confidence,
                    'risk': 'medium',  # Conservative default
                    'reasoning': 'Fallback assessment'
                }
            
        except Exception as e:
            # Fallback to rule-based assessment if LLM fails
            rule_confidence = self._calculate_rule_based_confidence(user_request, intent, entities)
            return {
                'confidence': rule_confidence,
                'risk': 'medium',  # Conservative default
                'reasoning': f'LLM failed, using rule-based: {e}'
            }
    
    async def _get_llm_confidence(
        self,
        user_request: str,
        intent: IntentV1,
        entities: List[EntityV1]
    ) -> float:
        """DEPRECATED: Use _get_llm_confidence_and_risk instead"""
        result = await self._get_llm_confidence_and_risk(user_request, intent, entities)
        return result['confidence']
    
    def _calculate_rule_based_confidence(
        self,
        user_request: str,
        intent: IntentV1,
        entities: List[EntityV1]
    ) -> float:
        """Calculate confidence using rule-based approach"""
        
        # SPECIAL CASE: Simple, self-contained questions should have HIGH confidence
        # These are clear, unambiguous requests that don't need clarification
        if self._is_simple_self_contained_question(user_request, intent):
            return 0.95  # Very high confidence for simple questions
        
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
    
    def _is_simple_self_contained_question(self, user_request: str, intent: IntentV1) -> bool:
        """
        Detect simple, self-contained questions that don't need clarification.
        Examples: "what is 2+2", "what is kubernetes", "explain docker", "calculate 5*10"
        """
        request_lower = user_request.lower().strip()
        
        # Must be an information request
        if intent.category != "information":
            return False
        
        # Pattern 1: Simple math questions
        # "what is 2+2", "calculate 5*10", "compute 100/5"
        math_patterns = [
            "what is",
            "what's",
            "calculate",
            "compute",
            "solve"
        ]
        has_math_pattern = any(pattern in request_lower for pattern in math_patterns)
        has_numbers = any(char.isdigit() for char in user_request)
        has_math_operators = any(op in user_request for op in ['+', '-', '*', '/', '='])
        
        if has_math_pattern and has_numbers and has_math_operators:
            return True
        
        # Pattern 2: Simple definition/explanation questions
        # "what is kubernetes", "explain docker", "define CI/CD"
        definition_patterns = [
            "what is",
            "what's",
            "what are",
            "explain",
            "define",
            "describe"
        ]
        has_definition_pattern = any(pattern in request_lower for pattern in definition_patterns)
        word_count = len(user_request.split())
        
        # Simple definition questions are typically 2-6 words
        if has_definition_pattern and 2 <= word_count <= 6:
            return True
        
        # Pattern 3: Direct information queries with clear intent
        # "help", "status", "version", "list tools"
        direct_queries = [
            "help",
            "status", 
            "version",
            "list tools",
            "show tools",
            "available tools"
        ]
        if any(query == request_lower or query in request_lower for query in direct_queries):
            return True
        
        return False
    
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
    
    def _calculate_rule_based_risk(
        self,
        user_request: str,
        intent: IntentV1,
        entities: List[EntityV1]
    ) -> Dict[str, str]:
        """
        Calculate risk level using rule-based approach (fast, no LLM call)
        
        Returns:
            Dictionary with 'risk' (low|medium|high|critical) and 'reasoning'
        """
        request_lower = user_request.lower()
        
        # CRITICAL RISK: Destructive operations
        critical_keywords = ['delete', 'remove', 'drop', 'destroy', 'purge', 'wipe', 'erase', 'truncate']
        if any(keyword in request_lower for keyword in critical_keywords):
            return {'risk': 'critical', 'reasoning': 'Destructive operation detected'}
        
        # HIGH RISK: Production changes, security operations, database operations
        high_risk_keywords = ['production', 'prod', 'live', 'security', 'firewall', 'iptables', 'database', 'db']
        high_risk_actions = ['modify', 'change', 'update', 'alter', 'grant', 'revoke']
        
        has_high_risk_context = any(keyword in request_lower for keyword in high_risk_keywords)
        has_high_risk_action = any(action in request_lower for action in high_risk_actions)
        
        if has_high_risk_context and has_high_risk_action:
            return {'risk': 'high', 'reasoning': 'Production or security modification'}
        
        # HIGH RISK: Action intents in production environment
        prod_entities = [e for e in entities if e.type == 'environment' and e.value.lower() in ['prod', 'production']]
        if intent.category in ['execution', 'deployment', 'configuration'] and prod_entities:
            return {'risk': 'high', 'reasoning': 'Action in production environment'}
        
        # MEDIUM RISK: Service restarts, configuration changes
        medium_risk_keywords = ['restart', 'reload', 'config', 'configure', 'install', 'upgrade']
        if any(keyword in request_lower for keyword in medium_risk_keywords):
            return {'risk': 'medium', 'reasoning': 'Service or configuration change'}
        
        # MEDIUM RISK: Action intents without clear context
        if intent.category in ['execution', 'deployment', 'configuration']:
            return {'risk': 'medium', 'reasoning': 'Action intent requires validation'}
        
        # LOW RISK: Read-only operations, status checks, information requests
        low_risk_keywords = ['show', 'list', 'get', 'status', 'check', 'view', 'display', 'info']
        if any(keyword in request_lower for keyword in low_risk_keywords):
            return {'risk': 'low', 'reasoning': 'Read-only operation'}
        
        # LOW RISK: Information category
        if intent.category == 'information':
            return {'risk': 'low', 'reasoning': 'Information request'}
        
        # DEFAULT: Medium risk (conservative)
        return {'risk': 'medium', 'reasoning': 'Default conservative assessment'}
    
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