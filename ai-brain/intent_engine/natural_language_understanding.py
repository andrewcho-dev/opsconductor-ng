"""
Natural Language Understanding Module for AI Brain Intent Engine

This module provides comprehensive natural language understanding capabilities
for parsing user intents, extracting entities, and understanding automation requests.
"""

import re
import json
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass, field
from enum import Enum
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

class IntentType(Enum):
    """Types of user intents that can be recognized"""
    AUTOMATION_REQUEST = "automation_request"
    INFORMATION_QUERY = "information_query"
    SYSTEM_STATUS = "system_status"
    TROUBLESHOOTING = "troubleshooting"
    CONFIGURATION = "configuration"
    MONITORING = "monitoring"
    DEPLOYMENT = "deployment"
    MAINTENANCE = "maintenance"
    SECURITY = "security"
    BACKUP_RESTORE = "backup_restore"
    USER_MANAGEMENT = "user_management"
    NETWORK_OPERATIONS = "network_operations"
    DATABASE_OPERATIONS = "database_operations"
    FILE_OPERATIONS = "file_operations"
    SERVICE_MANAGEMENT = "service_management"
    UNKNOWN = "unknown"

class EntityType(Enum):
    """Types of entities that can be extracted from user input"""
    TARGET = "target"           # Servers, hosts, groups
    SERVICE = "service"         # Service names
    ACTION = "action"           # Actions to perform
    PARAMETER = "parameter"     # Configuration parameters
    TIME = "time"              # Time expressions
    FILE_PATH = "file_path"    # File and directory paths
    USER = "user"              # Usernames
    PROTOCOL = "protocol"      # SSH, WinRM, etc.
    PORT = "port"              # Port numbers
    CREDENTIAL = "credential"   # Credential references
    CONDITION = "condition"     # Conditional expressions
    QUANTITY = "quantity"       # Numbers and quantities

@dataclass
class Entity:
    """Represents an extracted entity from user input"""
    type: EntityType
    value: str
    confidence: float
    start_pos: int
    end_pos: int
    context: Optional[str] = None
    normalized_value: Optional[str] = None

@dataclass
class Intent:
    """Represents a parsed user intent"""
    type: IntentType
    confidence: float
    entities: List[Entity] = field(default_factory=list)
    raw_text: str = ""
    processed_text: str = ""
    context: Dict[str, Any] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.now)

class NaturalLanguageUnderstanding:
    """
    Advanced Natural Language Understanding system for automation intents
    """
    
    def __init__(self):
        self.intent_patterns = self._initialize_intent_patterns()
        self.entity_patterns = self._initialize_entity_patterns()
        self.action_synonyms = self._initialize_action_synonyms()
        self.service_aliases = self._initialize_service_aliases()
        
    def _initialize_intent_patterns(self) -> Dict[IntentType, List[str]]:
        """Initialize regex patterns for intent classification"""
        return {
            IntentType.AUTOMATION_REQUEST: [
                r'\b(run|execute|perform|do|start|stop|restart|deploy|install|update|configure)\b',
                r'\b(automate|automation|script|workflow|job|task)\b',
                r'\b(please|can you|could you|would you|help me)\b.*\b(run|execute|perform)\b'
            ],
            IntentType.INFORMATION_QUERY: [
                r'\b(what|how|when|where|why|which|who)\b',
                r'\b(show|list|display|get|find|search|check|tell me|explain)\b',
                r'\b(status|information|info|details|summary|report)\b'
            ],
            IntentType.SYSTEM_STATUS: [
                r'\b(status|health|state|condition|up|down|running|stopped)\b',
                r'\b(check|monitor|verify|validate|test|ping)\b.*\b(system|server|service)\b',
                r'\b(is.*running|is.*up|is.*down|is.*working)\b'
            ],
            IntentType.TROUBLESHOOTING: [
                r'\b(error|problem|issue|trouble|fail|broken|not working)\b',
                r'\b(debug|diagnose|troubleshoot|fix|resolve|solve)\b',
                r'\b(why.*not|what.*wrong|help.*with)\b'
            ],
            IntentType.SERVICE_MANAGEMENT: [
                r'\b(service|daemon|process)\b.*\b(start|stop|restart|reload|enable|disable)\b',
                r'\b(start|stop|restart|reload|enable|disable)\b.*\b(service|daemon)\b',
                r'\bsystemctl\b|\bservice\b|\binit\.d\b'
            ],
            IntentType.FILE_OPERATIONS: [
                r'\b(file|directory|folder|path)\b.*\b(copy|move|delete|create|backup|restore)\b',
                r'\b(copy|move|delete|create|backup|restore)\b.*\b(file|directory|folder)\b',
                r'\b(cp|mv|rm|mkdir|rmdir|tar|zip|unzip)\b'
            ],
            IntentType.USER_MANAGEMENT: [
                r'\b(user|account|password|permission|access|role)\b',
                r'\b(create|add|delete|remove|modify|update)\b.*\b(user|account)\b',
                r'\buseradd\b|\buserdel\b|\busermod\b|\bpasswd\b'
            ],
            IntentType.DATABASE_OPERATIONS: [
                r'\b(database|db|mysql|postgresql|postgres|mongodb|redis)\b',
                r'\b(backup|restore|dump|import|export)\b.*\b(database|db)\b',
                r'\bmysqldump\b|\bpg_dump\b|\bmongodump\b'
            ],
            IntentType.NETWORK_OPERATIONS: [
                r'\b(network|firewall|port|connection|ping|telnet|ssh)\b',
                r'\b(open|close|block|allow)\b.*\b(port|connection)\b',
                r'\biptables\b|\bufw\b|\bnetstat\b|\bss\b'
            ],
            IntentType.MONITORING: [
                r'\b(monitor|monitoring|alert|notification|watch|observe)\b',
                r'\b(cpu|memory|disk|load|performance|metrics)\b',
                r'\btop\b|\bhtop\b|\bps\b|\bdf\b|\bfree\b'
            ],
            IntentType.SECURITY: [
                r'\b(security|secure|vulnerability|patch|update|hardening)\b',
                r'\b(ssl|tls|certificate|cert|key|encryption)\b',
                r'\b(audit|compliance|policy|permission|access control)\b'
            ],
            IntentType.BACKUP_RESTORE: [
                r'\b(backup|restore|snapshot|archive|recovery)\b',
                r'\b(backup|restore)\b.*\b(database|file|system|data)\b',
                r'\brsync\b|\btar\b|\bgzip\b|\bzip\b'
            ]
        }
    
    def _initialize_entity_patterns(self) -> Dict[EntityType, List[str]]:
        """Initialize regex patterns for entity extraction"""
        return {
            EntityType.TARGET: [
                r'\b(?:server|host|machine|node|target|system)s?\s+([a-zA-Z0-9\-\.]+(?:\s*,\s*[a-zA-Z0-9\-\.]+)*)\b',
                r'\b([a-zA-Z0-9\-\.]+\.[a-zA-Z]{2,})\b',  # Domain names
                r'\b(\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})\b',  # IP addresses
                r'\bgroup\s+([a-zA-Z0-9\-_]+)\b',
                r'\bon\s+([a-zA-Z0-9\-\.,\s]+)\b'
            ],
            EntityType.SERVICE: [
                r'\b(apache2?|nginx|mysql|postgresql|postgres|redis|mongodb|docker|ssh|ftp|dns|dhcp|ntp)\b',
                r'\bservice\s+([a-zA-Z0-9\-_]+)\b',
                r'\b([a-zA-Z0-9\-_]+)\.service\b'
            ],
            EntityType.ACTION: [
                r'\b(start|stop|restart|reload|enable|disable|install|uninstall|update|upgrade|configure|backup|restore)\b',
                r'\b(create|delete|modify|copy|move|remove|add|set|get|check|test|verify)\b'
            ],
            EntityType.FILE_PATH: [
                r'\b(/[a-zA-Z0-9\-_/\.]+)\b',  # Unix paths
                r'\b([A-Z]:\\[a-zA-Z0-9\-_\\\.]+)\b',  # Windows paths
                r'\b([a-zA-Z0-9\-_\.]+\.[a-zA-Z0-9]+)\b'  # Filenames with extensions
            ],
            EntityType.USER: [
                r'\buser\s+([a-zA-Z0-9\-_]+)\b',
                r'\baccount\s+([a-zA-Z0-9\-_]+)\b',
                r'\b(?:for|as)\s+([a-zA-Z0-9\-_]+)\b'
            ],
            EntityType.PORT: [
                r'\bport\s+(\d{1,5})\b',
                r'\b:(\d{1,5})\b',
                r'\b(\d{1,5})/(?:tcp|udp)\b'
            ],
            EntityType.PROTOCOL: [
                r'\b(ssh|http|https|ftp|sftp|telnet|snmp|winrm|powershell)\b'
            ],
            EntityType.TIME: [
                r'\b(?:in|after|at)\s+(\d+\s*(?:second|minute|hour|day)s?)\b',
                r'\b(\d{1,2}:\d{2}(?::\d{2})?(?:\s*[ap]m)?)\b',
                r'\b(now|immediately|asap|tonight|tomorrow|today)\b'
            ],
            EntityType.QUANTITY: [
                r'\b(\d+(?:\.\d+)?)\s*(?:gb|mb|kb|%|percent)\b',
                r'\b(\d+)\s*(?:times|instances|copies|backups)\b'
            ]
        }
    
    def _initialize_action_synonyms(self) -> Dict[str, str]:
        """Initialize action synonyms for normalization"""
        return {
            'begin': 'start',
            'commence': 'start',
            'initiate': 'start',
            'launch': 'start',
            'boot': 'start',
            'terminate': 'stop',
            'halt': 'stop',
            'shutdown': 'stop',
            'kill': 'stop',
            'end': 'stop',
            'reboot': 'restart',
            'reset': 'restart',
            'bounce': 'restart',
            'cycle': 'restart',
            'refresh': 'reload',
            'update': 'reload',
            'reconfigure': 'configure',
            'setup': 'configure',
            'set up': 'configure',
            'deploy': 'install',
            'provision': 'install',
            'remove': 'uninstall',
            'uninstall': 'delete',
            'erase': 'delete',
            'destroy': 'delete'
        }
    
    def _initialize_service_aliases(self) -> Dict[str, str]:
        """Initialize service aliases for normalization"""
        return {
            'apache': 'apache2',
            'httpd': 'apache2',
            'web server': 'apache2',
            'mysql': 'mysql',
            'mariadb': 'mysql',
            'database': 'mysql',
            'db': 'mysql',
            'postgres': 'postgresql',
            'pg': 'postgresql',
            'ssh': 'sshd',
            'secure shell': 'sshd',
            'web': 'nginx',
            'reverse proxy': 'nginx',
            'cache': 'redis',
            'memory store': 'redis',
            'document store': 'mongodb',
            'mongo': 'mongodb',
            'container': 'docker',
            'containers': 'docker'
        }
    
    def parse_intent(self, text: str, context: Optional[Dict[str, Any]] = None) -> Intent:
        """
        Parse user input to extract intent and entities
        
        Args:
            text: User input text
            context: Optional conversation context
            
        Returns:
            Intent object with classification and extracted entities
        """
        try:
            # Preprocess text
            processed_text = self._preprocess_text(text)
            
            # Classify intent
            intent_type, intent_confidence = self._classify_intent(processed_text)
            
            # Extract entities
            entities = self._extract_entities(processed_text)
            
            # Create intent object
            intent = Intent(
                type=intent_type,
                confidence=intent_confidence,
                entities=entities,
                raw_text=text,
                processed_text=processed_text,
                context=context or {}
            )
            
            # Post-process and validate
            intent = self._post_process_intent(intent)
            
            logger.info(f"Parsed intent: {intent_type.value} (confidence: {intent_confidence:.2f})")
            return intent
            
        except Exception as e:
            logger.error(f"Error parsing intent: {e}")
            return Intent(
                type=IntentType.UNKNOWN,
                confidence=0.0,
                raw_text=text,
                processed_text=text
            )
    
    def _preprocess_text(self, text: str) -> str:
        """Preprocess text for better parsing"""
        # Convert to lowercase
        text = text.lower().strip()
        
        # Remove extra whitespace
        text = re.sub(r'\s+', ' ', text)
        
        # Expand contractions
        contractions = {
            "can't": "cannot",
            "won't": "will not",
            "n't": " not",
            "'re": " are",
            "'ve": " have",
            "'ll": " will",
            "'d": " would"
        }
        
        for contraction, expansion in contractions.items():
            text = text.replace(contraction, expansion)
        
        return text
    
    def _classify_intent(self, text: str) -> Tuple[IntentType, float]:
        """Classify the intent type from processed text"""
        intent_scores = {}
        
        for intent_type, patterns in self.intent_patterns.items():
            score = 0.0
            matches = 0
            
            for pattern in patterns:
                if re.search(pattern, text, re.IGNORECASE):
                    matches += 1
                    # Weight based on pattern specificity
                    pattern_weight = len(pattern.split('|')) / 10.0 + 0.1
                    score += pattern_weight
            
            if matches > 0:
                # Normalize score based on number of patterns and matches
                normalized_score = min(score / len(patterns), 1.0)
                intent_scores[intent_type] = normalized_score
        
        if not intent_scores:
            return IntentType.UNKNOWN, 0.0
        
        # Return intent with highest score
        best_intent = max(intent_scores.items(), key=lambda x: x[1])
        return best_intent[0], best_intent[1]
    
    def _extract_entities(self, text: str) -> List[Entity]:
        """Extract entities from processed text"""
        entities = []
        
        for entity_type, patterns in self.entity_patterns.items():
            for pattern in patterns:
                matches = re.finditer(pattern, text, re.IGNORECASE)
                
                for match in matches:
                    # Get the captured group or full match
                    if match.groups():
                        value = match.group(1)
                        start_pos = match.start(1)
                        end_pos = match.end(1)
                    else:
                        value = match.group(0)
                        start_pos = match.start()
                        end_pos = match.end()
                    
                    # Calculate confidence based on pattern specificity
                    confidence = min(0.8 + (len(pattern) / 100.0), 1.0)
                    
                    # Normalize entity value
                    normalized_value = self._normalize_entity_value(entity_type, value)
                    
                    entity = Entity(
                        type=entity_type,
                        value=value,
                        confidence=confidence,
                        start_pos=start_pos,
                        end_pos=end_pos,
                        normalized_value=normalized_value,
                        context=text[max(0, start_pos-20):min(len(text), end_pos+20)]
                    )
                    
                    entities.append(entity)
        
        # Remove duplicate entities (same type and overlapping positions)
        entities = self._deduplicate_entities(entities)
        
        # Sort by position
        entities.sort(key=lambda e: e.start_pos)
        
        return entities
    
    def _normalize_entity_value(self, entity_type: EntityType, value: str) -> str:
        """Normalize entity values using synonyms and aliases"""
        value = value.lower().strip()
        
        if entity_type == EntityType.ACTION:
            return self.action_synonyms.get(value, value)
        elif entity_type == EntityType.SERVICE:
            return self.service_aliases.get(value, value)
        elif entity_type == EntityType.TARGET:
            # Handle comma-separated targets
            if ',' in value:
                targets = [t.strip() for t in value.split(',')]
                return ','.join(targets)
            return value
        elif entity_type == EntityType.TIME:
            # Normalize time expressions
            time_mappings = {
                'now': 'immediately',
                'asap': 'immediately',
                'tonight': 'today 20:00',
                'tomorrow': '+1 day'
            }
            return time_mappings.get(value, value)
        
        return value
    
    def _deduplicate_entities(self, entities: List[Entity]) -> List[Entity]:
        """Remove duplicate and overlapping entities"""
        if not entities:
            return entities
        
        # Sort by start position
        entities.sort(key=lambda e: (e.start_pos, -e.confidence))
        
        deduplicated = []
        
        for entity in entities:
            # Check for overlap with existing entities
            overlaps = False
            for existing in deduplicated:
                if (entity.type == existing.type and 
                    entity.start_pos < existing.end_pos and 
                    entity.end_pos > existing.start_pos):
                    # Keep the one with higher confidence
                    if entity.confidence > existing.confidence:
                        deduplicated.remove(existing)
                        break
                    else:
                        overlaps = True
                        break
            
            if not overlaps:
                deduplicated.append(entity)
        
        return deduplicated
    
    def _post_process_intent(self, intent: Intent) -> Intent:
        """Post-process intent to improve accuracy and add context"""
        # Adjust confidence based on entity quality
        if intent.entities:
            entity_confidence = sum(e.confidence for e in intent.entities) / len(intent.entities)
            intent.confidence = (intent.confidence + entity_confidence) / 2
        
        # Add context based on entities
        intent.context['entity_count'] = len(intent.entities)
        intent.context['has_targets'] = any(e.type == EntityType.TARGET for e in intent.entities)
        intent.context['has_actions'] = any(e.type == EntityType.ACTION for e in intent.entities)
        intent.context['has_services'] = any(e.type == EntityType.SERVICE for e in intent.entities)
        
        # Refine intent type based on entities
        if intent.type == IntentType.UNKNOWN and intent.entities:
            intent.type = self._infer_intent_from_entities(intent.entities)
            intent.confidence = max(intent.confidence, 0.3)
        
        return intent
    
    def _infer_intent_from_entities(self, entities: List[Entity]) -> IntentType:
        """Infer intent type from extracted entities"""
        entity_types = [e.type for e in entities]
        
        if EntityType.ACTION in entity_types and EntityType.SERVICE in entity_types:
            return IntentType.SERVICE_MANAGEMENT
        elif EntityType.ACTION in entity_types and EntityType.FILE_PATH in entity_types:
            return IntentType.FILE_OPERATIONS
        elif EntityType.ACTION in entity_types and EntityType.USER in entity_types:
            return IntentType.USER_MANAGEMENT
        elif EntityType.TARGET in entity_types:
            return IntentType.AUTOMATION_REQUEST
        else:
            return IntentType.INFORMATION_QUERY
    
    def get_entity_by_type(self, intent: Intent, entity_type: EntityType) -> Optional[Entity]:
        """Get the first entity of a specific type from an intent"""
        for entity in intent.entities:
            if entity.type == entity_type:
                return entity
        return None
    
    def get_entities_by_type(self, intent: Intent, entity_type: EntityType) -> List[Entity]:
        """Get all entities of a specific type from an intent"""
        return [entity for entity in intent.entities if entity.type == entity_type]
    
    def export_patterns(self) -> Dict[str, Any]:
        """Export patterns for documentation or debugging"""
        return {
            'intent_patterns': {k.value: v for k, v in self.intent_patterns.items()},
            'entity_patterns': {k.value: v for k, v in self.entity_patterns.items()},
            'action_synonyms': self.action_synonyms,
            'service_aliases': self.service_aliases
        }

# Global instance for easy access
nlu_engine = NaturalLanguageUnderstanding()