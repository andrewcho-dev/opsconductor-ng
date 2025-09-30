"""
Entity Extractor for Stage A
Extracts technical entities from user requests
"""

import re
from typing import List, Dict, Any, Optional
from ...schemas.decision_v1 import EntityV1
from llm.client import LLMClient, LLMRequest
from llm.prompt_manager import PromptManager, PromptType
from llm.response_parser import ResponseParser

class EntityExtractor:
    """Extracts entities from user requests using LLM and regex patterns"""
    
    def __init__(self, llm_client: LLMClient):
        self.llm_client = llm_client
        self.prompt_manager = PromptManager()
        self.response_parser = ResponseParser()
        self.regex_patterns = self._load_regex_patterns()
    
    def _load_regex_patterns(self) -> Dict[str, List[Dict[str, Any]]]:
        """Load regex patterns for entity extraction"""
        return {
            "hostname": [
                {
                    "pattern": r'\b(?:[a-zA-Z0-9](?:[a-zA-Z0-9\-]{0,61}[a-zA-Z0-9])?\.)+[a-zA-Z]{2,}\b',
                    "confidence": 0.9,
                    "description": "FQDN hostname"
                },
                {
                    "pattern": r'\b(?:(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\b',
                    "confidence": 0.95,
                    "description": "IPv4 address"
                },
                {
                    "pattern": r'\b[a-zA-Z0-9][a-zA-Z0-9\-]*[a-zA-Z0-9]\b(?=\s*(?:server|host|node|machine))',
                    "confidence": 0.8,
                    "description": "Server name with context"
                }
            ],
            "service": [
                {
                    "pattern": r'\b(?:nginx|apache|httpd|mysql|postgresql|postgres|redis|mongodb|docker|kubernetes|k8s)\b',
                    "confidence": 0.95,
                    "description": "Common services"
                },
                {
                    "pattern": r'\b[a-zA-Z0-9\-_]+\.service\b',
                    "confidence": 0.9,
                    "description": "Systemd service"
                },
                {
                    "pattern": r'\b[a-zA-Z0-9\-_]+(?=\s*(?:service|daemon|process))',
                    "confidence": 0.7,
                    "description": "Service with context"
                }
            ],
            "command": [
                {
                    "pattern": r'\b(?:systemctl|service|docker|kubectl|git|npm|pip|apt|yum|curl|wget)\s+[^\s]+',
                    "confidence": 0.9,
                    "description": "Command with arguments"
                },
                {
                    "pattern": r'`([^`]+)`',
                    "confidence": 0.85,
                    "description": "Command in backticks"
                }
            ],
            "file_path": [
                {
                    "pattern": r'(?:/[^/\s]+)+/?',
                    "confidence": 0.8,
                    "description": "Unix file path"
                },
                {
                    "pattern": r'[A-Za-z]:\\(?:[^\\/:*?"<>|\r\n]+\\)*[^\\/:*?"<>|\r\n]*',
                    "confidence": 0.8,
                    "description": "Windows file path"
                }
            ],
            "port": [
                {
                    "pattern": r'\b(?:port\s+)?(\d{1,5})\b',
                    "confidence": 0.9,
                    "description": "Port number"
                },
                {
                    "pattern": r':(\d{1,5})\b',
                    "confidence": 0.85,
                    "description": "Port in URL format"
                }
            ],
            "environment": [
                {
                    "pattern": r'\b(?:prod|production|staging|stage|dev|development|test|testing)\b',
                    "confidence": 0.9,
                    "description": "Environment names"
                }
            ]
        }
    
    async def extract_entities(self, user_request: str) -> List[EntityV1]:
        """
        Extract entities from user request using both LLM and regex
        
        Args:
            user_request: Original user request string
            
        Returns:
            List of EntityV1 objects
        """
        # Extract using LLM
        llm_entities = await self._extract_with_llm(user_request)
        
        # Extract using regex patterns
        regex_entities = self._extract_with_regex(user_request)
        
        # Merge and deduplicate entities
        merged_entities = self._merge_entities(llm_entities, regex_entities)
        
        return merged_entities
    
    async def _extract_with_llm(self, user_request: str) -> List[EntityV1]:
        """Extract entities using LLM"""
        try:
            # Get the entity extraction prompt
            prompts = self.prompt_manager.get_prompt(
                PromptType.ENTITY_EXTRACTION,
                user_request=user_request
            )
            
            # Create LLM request
            llm_request = LLMRequest(
                prompt=prompts["user"],
                system_prompt=prompts["system"],
                temperature=0.1,
                max_tokens=300
            )
            
            # Get response from LLM
            response = await self.llm_client.generate(llm_request)
            
            # Parse the response
            entities_data = self.response_parser.parse_entities_response(response.content)
            
            # Convert to EntityV1 objects
            entities = []
            for entity_data in entities_data:
                entities.append(EntityV1(
                    type=entity_data["type"],
                    value=entity_data["value"],
                    confidence=entity_data["confidence"]
                ))
            
            return entities
            
        except Exception as e:
            # Return empty list if LLM extraction fails
            return []
    
    def _extract_with_regex(self, user_request: str) -> List[EntityV1]:
        """Extract entities using regex patterns"""
        entities = []
        
        for entity_type, patterns in self.regex_patterns.items():
            for pattern_info in patterns:
                pattern = pattern_info["pattern"]
                base_confidence = pattern_info["confidence"]
                
                matches = re.finditer(pattern, user_request, re.IGNORECASE)
                for match in matches:
                    # Use the first group if available, otherwise the whole match
                    value = match.group(1) if match.groups() else match.group(0)
                    value = value.strip()
                    
                    if value and len(value) > 0:
                        # Adjust confidence based on context
                        confidence = self._adjust_confidence(
                            entity_type, value, user_request, base_confidence
                        )
                        
                        entities.append(EntityV1(
                            type=entity_type,
                            value=value,
                            confidence=confidence
                        ))
        
        return entities
    
    def _adjust_confidence(self, entity_type: str, value: str, context: str, base_confidence: float) -> float:
        """Adjust confidence based on context"""
        confidence = base_confidence
        
        # Boost confidence if entity appears in relevant context
        context_lower = context.lower()
        
        if entity_type == "service":
            if any(word in context_lower for word in ["restart", "start", "stop", "status"]):
                confidence = min(1.0, confidence + 0.1)
        
        elif entity_type == "hostname":
            if any(word in context_lower for word in ["server", "host", "machine", "node"]):
                confidence = min(1.0, confidence + 0.1)
        
        elif entity_type == "port":
            # Validate port range
            try:
                port_num = int(value)
                if not (1 <= port_num <= 65535):
                    confidence = 0.1
            except ValueError:
                confidence = 0.1
        
        return confidence
    
    def _merge_entities(self, llm_entities: List[EntityV1], regex_entities: List[EntityV1]) -> List[EntityV1]:
        """Merge and deduplicate entities from LLM and regex extraction"""
        merged = {}
        
        # Add LLM entities (higher priority)
        for entity in llm_entities:
            key = (entity.type, entity.value.lower())
            merged[key] = entity
        
        # Add regex entities if not already present
        for entity in regex_entities:
            key = (entity.type, entity.value.lower())
            if key not in merged:
                merged[key] = entity
            else:
                # If same entity found by both methods, use higher confidence
                if entity.confidence > merged[key].confidence:
                    merged[key] = entity
        
        # Sort by confidence (highest first)
        result = list(merged.values())
        result.sort(key=lambda x: x.confidence, reverse=True)
        
        return result
    
    def get_supported_entity_types(self) -> List[str]:
        """Get list of supported entity types"""
        return [
            "hostname",
            "service", 
            "command",
            "file_path",
            "port",
            "environment",
            "application",
            "database"
        ]
    
    def validate_entity(self, entity: EntityV1) -> bool:
        """
        Validate an extracted entity
        
        Args:
            entity: Entity to validate
            
        Returns:
            True if entity is valid, False otherwise
        """
        # Check if entity type is supported
        if entity.type not in self.get_supported_entity_types():
            return False
        
        # Check confidence range
        if not 0 <= entity.confidence <= 1:
            return False
        
        # Check value is not empty
        if not entity.value or len(entity.value.strip()) == 0:
            return False
        
        # Type-specific validation
        if entity.type == "port":
            try:
                port = int(entity.value)
                return 1 <= port <= 65535
            except ValueError:
                return False
        
        return True