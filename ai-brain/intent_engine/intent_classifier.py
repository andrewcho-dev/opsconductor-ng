"""
Intent Classifier Module for AI Brain Intent Engine

This module provides advanced intent classification capabilities with machine learning-like
pattern recognition, confidence scoring, and intelligent intent disambiguation.
"""

import re
import json
import math
from typing import Dict, List, Optional, Tuple, Any, Set
from dataclasses import dataclass, field
from enum import Enum
from collections import defaultdict, Counter
import logging

from .natural_language_understanding import Intent, IntentType, Entity, EntityType

logger = logging.getLogger(__name__)

class ClassificationMethod(Enum):
    """Methods used for intent classification"""
    PATTERN_MATCHING = "pattern_matching"
    ENTITY_ANALYSIS = "entity_analysis"
    CONTEXT_ANALYSIS = "context_analysis"
    SEMANTIC_ANALYSIS = "semantic_analysis"
    HYBRID = "hybrid"

@dataclass
class ClassificationResult:
    """Result of intent classification"""
    intent_type: IntentType
    confidence: float
    method: ClassificationMethod
    evidence: List[str] = field(default_factory=list)
    alternative_intents: List[Tuple[IntentType, float]] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)

@dataclass
class IntentSignature:
    """Signature pattern for an intent type"""
    intent_type: IntentType
    required_patterns: List[str] = field(default_factory=list)
    optional_patterns: List[str] = field(default_factory=list)
    required_entities: List[EntityType] = field(default_factory=list)
    optional_entities: List[EntityType] = field(default_factory=list)
    context_indicators: List[str] = field(default_factory=list)
    exclusion_patterns: List[str] = field(default_factory=list)
    weight: float = 1.0

class IntentClassifier:
    """
    Advanced intent classifier with multiple classification methods and confidence scoring
    """
    
    def __init__(self):
        self.intent_signatures = self._initialize_intent_signatures()
        self.semantic_clusters = self._initialize_semantic_clusters()
        self.disambiguation_rules = self._initialize_disambiguation_rules()
        self.confidence_thresholds = self._initialize_confidence_thresholds()
        
    def _initialize_intent_signatures(self) -> Dict[IntentType, IntentSignature]:
        """Initialize detailed intent signatures for classification"""
        return {
            IntentType.AUTOMATION_REQUEST: IntentSignature(
                intent_type=IntentType.AUTOMATION_REQUEST,
                required_patterns=[
                    r'\b(run|execute|perform|do|automate|automation)\b',
                    r'\b(task|job|workflow|script|command)\b'
                ],
                optional_patterns=[
                    r'\b(please|can you|could you|would you|help me)\b',
                    r'\b(need to|want to|should|must)\b'
                ],
                required_entities=[EntityType.ACTION],
                optional_entities=[EntityType.TARGET, EntityType.SERVICE, EntityType.PARAMETER],
                context_indicators=['automation', 'workflow', 'job', 'task'],
                weight=1.2
            ),
            
            IntentType.SERVICE_MANAGEMENT: IntentSignature(
                intent_type=IntentType.SERVICE_MANAGEMENT,
                required_patterns=[
                    r'\b(service|daemon|process)\b',
                    r'\b(start|stop|restart|reload|enable|disable|status)\b'
                ],
                optional_patterns=[
                    r'\bsystemctl\b|\bservice\b|\binit\.d\b',
                    r'\b(check|verify|manage)\b'
                ],
                required_entities=[EntityType.SERVICE, EntityType.ACTION],
                optional_entities=[EntityType.TARGET],
                context_indicators=['systemctl', 'daemon', 'init'],
                weight=1.3
            ),
            
            IntentType.INFORMATION_QUERY: IntentSignature(
                intent_type=IntentType.INFORMATION_QUERY,
                required_patterns=[
                    r'\b(what|how|when|where|why|which|who)\b',
                    r'\b(show|list|display|get|find|search|tell me|explain)\b'
                ],
                optional_patterns=[
                    r'\b(information|info|details|status|report)\b',
                    r'\b(can you show|please show|I want to see)\b'
                ],
                required_entities=[],
                optional_entities=[EntityType.TARGET, EntityType.SERVICE],
                context_indicators=['query', 'information', 'details'],
                exclusion_patterns=[r'\b(do|execute|run|perform|start|stop)\b'],
                weight=1.0
            ),
            
            IntentType.SYSTEM_STATUS: IntentSignature(
                intent_type=IntentType.SYSTEM_STATUS,
                required_patterns=[
                    r'\b(status|health|state|condition|up|down|running|stopped)\b',
                    r'\b(check|monitor|verify|validate|test|ping)\b'
                ],
                optional_patterns=[
                    r'\b(system|server|service|application)\b',
                    r'\b(is.*running|is.*up|is.*down|is.*working)\b'
                ],
                required_entities=[],
                optional_entities=[EntityType.TARGET, EntityType.SERVICE],
                context_indicators=['status', 'health', 'monitoring'],
                weight=1.1
            ),
            
            IntentType.TROUBLESHOOTING: IntentSignature(
                intent_type=IntentType.TROUBLESHOOTING,
                required_patterns=[
                    r'\b(error|problem|issue|trouble|fail|broken|not working)\b',
                    r'\b(debug|diagnose|troubleshoot|fix|resolve|solve)\b'
                ],
                optional_patterns=[
                    r'\b(why.*not|what.*wrong|help.*with)\b',
                    r'\b(investigate|analyze|examine)\b'
                ],
                required_entities=[],
                optional_entities=[EntityType.TARGET, EntityType.SERVICE],
                context_indicators=['error', 'problem', 'troubleshoot'],
                weight=1.2
            ),
            
            IntentType.FILE_OPERATIONS: IntentSignature(
                intent_type=IntentType.FILE_OPERATIONS,
                required_patterns=[
                    r'\b(file|directory|folder|path)\b',
                    r'\b(copy|move|delete|create|backup|restore|transfer)\b'
                ],
                optional_patterns=[
                    r'\b(cp|mv|rm|mkdir|rmdir|tar|zip|unzip|rsync)\b',
                    r'\b(upload|download|sync|archive)\b'
                ],
                required_entities=[EntityType.FILE_PATH, EntityType.ACTION],
                optional_entities=[EntityType.TARGET, EntityType.USER],
                context_indicators=['filesystem', 'directory', 'backup'],
                weight=1.1
            ),
            
            IntentType.USER_MANAGEMENT: IntentSignature(
                intent_type=IntentType.USER_MANAGEMENT,
                required_patterns=[
                    r'\b(user|account|password|permission|access|role)\b',
                    r'\b(create|add|delete|remove|modify|update|manage)\b'
                ],
                optional_patterns=[
                    r'\buseradd\b|\buserdel\b|\busermod\b|\bpasswd\b',
                    r'\b(grant|revoke|assign|unassign)\b'
                ],
                required_entities=[EntityType.USER, EntityType.ACTION],
                optional_entities=[EntityType.TARGET, EntityType.PARAMETER],
                context_indicators=['user', 'account', 'permission'],
                weight=1.2
            ),
            
            IntentType.DATABASE_OPERATIONS: IntentSignature(
                intent_type=IntentType.DATABASE_OPERATIONS,
                required_patterns=[
                    r'\b(database|db|mysql|postgresql|postgres|mongodb|redis)\b',
                    r'\b(backup|restore|dump|import|export|query|connect)\b'
                ],
                optional_patterns=[
                    r'\bmysqldump\b|\bpg_dump\b|\bmongodump\b',
                    r'\b(table|collection|schema|index)\b'
                ],
                required_entities=[EntityType.SERVICE, EntityType.ACTION],
                optional_entities=[EntityType.TARGET, EntityType.PARAMETER],
                context_indicators=['database', 'sql', 'nosql'],
                weight=1.3
            ),
            
            IntentType.NETWORK_OPERATIONS: IntentSignature(
                intent_type=IntentType.NETWORK_OPERATIONS,
                required_patterns=[
                    r'\b(network|firewall|port|connection|ping|telnet|ssh)\b',
                    r'\b(open|close|block|allow|connect|disconnect)\b'
                ],
                optional_patterns=[
                    r'\biptables\b|\bufw\b|\bnetstat\b|\bss\b',
                    r'\b(route|routing|gateway|dns)\b'
                ],
                required_entities=[EntityType.ACTION],
                optional_entities=[EntityType.TARGET, EntityType.PORT, EntityType.PROTOCOL],
                context_indicators=['network', 'firewall', 'connectivity'],
                weight=1.1
            ),
            
            IntentType.MONITORING: IntentSignature(
                intent_type=IntentType.MONITORING,
                required_patterns=[
                    r'\b(monitor|monitoring|alert|notification|watch|observe)\b',
                    r'\b(cpu|memory|disk|load|performance|metrics)\b'
                ],
                optional_patterns=[
                    r'\btop\b|\bhtop\b|\bps\b|\bdf\b|\bfree\b',
                    r'\b(dashboard|graph|chart|report)\b'
                ],
                required_entities=[],
                optional_entities=[EntityType.TARGET, EntityType.SERVICE],
                context_indicators=['monitoring', 'metrics', 'performance'],
                weight=1.0
            ),
            
            IntentType.SECURITY: IntentSignature(
                intent_type=IntentType.SECURITY,
                required_patterns=[
                    r'\b(security|secure|vulnerability|patch|update|hardening)\b',
                    r'\b(ssl|tls|certificate|cert|key|encryption)\b'
                ],
                optional_patterns=[
                    r'\b(audit|compliance|policy|permission|access control)\b',
                    r'\b(scan|assess|review|analyze)\b'
                ],
                required_entities=[],
                optional_entities=[EntityType.TARGET, EntityType.SERVICE],
                context_indicators=['security', 'encryption', 'compliance'],
                weight=1.2
            ),
            
            IntentType.BACKUP_RESTORE: IntentSignature(
                intent_type=IntentType.BACKUP_RESTORE,
                required_patterns=[
                    r'\b(backup|restore|snapshot|archive|recovery)\b',
                    r'\b(create|make|perform|execute|run)\b.*\b(backup|restore)\b'
                ],
                optional_patterns=[
                    r'\brsync\b|\btar\b|\bgzip\b|\bzip\b',
                    r'\b(full|incremental|differential)\b.*\b(backup|restore)\b'
                ],
                required_entities=[EntityType.ACTION],
                optional_entities=[EntityType.TARGET, EntityType.FILE_PATH, EntityType.SERVICE],
                context_indicators=['backup', 'restore', 'recovery'],
                weight=1.1
            ),
            
            IntentType.CONFIGURATION: IntentSignature(
                intent_type=IntentType.CONFIGURATION,
                required_patterns=[
                    r'\b(configure|configuration|config|setup|set up)\b',
                    r'\b(change|modify|update|edit|adjust)\b.*\b(config|configuration|settings)\b'
                ],
                optional_patterns=[
                    r'\b(parameter|option|setting|property|value)\b',
                    r'\b(nginx\.conf|httpd\.conf|my\.cnf|postgresql\.conf)\b'
                ],
                required_entities=[EntityType.ACTION],
                optional_entities=[EntityType.TARGET, EntityType.SERVICE, EntityType.PARAMETER],
                context_indicators=['configuration', 'settings', 'parameters'],
                weight=1.1
            ),
            
            IntentType.DEPLOYMENT: IntentSignature(
                intent_type=IntentType.DEPLOYMENT,
                required_patterns=[
                    r'\b(deploy|deployment|install|installation|provision)\b',
                    r'\b(release|rollout|update|upgrade|migrate)\b'
                ],
                optional_patterns=[
                    r'\b(docker|container|kubernetes|k8s)\b',
                    r'\b(application|app|service|package)\b'
                ],
                required_entities=[EntityType.ACTION],
                optional_entities=[EntityType.TARGET, EntityType.SERVICE],
                context_indicators=['deployment', 'installation', 'provisioning'],
                weight=1.2
            ),
            
            IntentType.MAINTENANCE: IntentSignature(
                intent_type=IntentType.MAINTENANCE,
                required_patterns=[
                    r'\b(maintenance|maintain|upkeep|service)\b',
                    r'\b(clean|cleanup|optimize|tune|update)\b'
                ],
                optional_patterns=[
                    r'\b(scheduled|routine|regular|periodic)\b',
                    r'\b(disk|log|cache|temporary|temp)\b.*\b(clean|cleanup)\b'
                ],
                required_entities=[EntityType.ACTION],
                optional_entities=[EntityType.TARGET, EntityType.SERVICE],
                context_indicators=['maintenance', 'cleanup', 'optimization'],
                weight=1.0
            )
        }
    
    def _initialize_semantic_clusters(self) -> Dict[str, List[str]]:
        """Initialize semantic word clusters for better classification"""
        return {
            'action_words': [
                'run', 'execute', 'perform', 'do', 'start', 'stop', 'restart', 'create', 'delete',
                'modify', 'update', 'install', 'configure', 'deploy', 'backup', 'restore'
            ],
            'query_words': [
                'what', 'how', 'when', 'where', 'why', 'which', 'who', 'show', 'list', 'display',
                'get', 'find', 'search', 'tell', 'explain', 'describe'
            ],
            'system_words': [
                'server', 'host', 'machine', 'system', 'node', 'cluster', 'infrastructure',
                'environment', 'platform', 'service', 'application', 'process'
            ],
            'problem_words': [
                'error', 'problem', 'issue', 'trouble', 'fail', 'failure', 'broken', 'down',
                'not working', 'debug', 'troubleshoot', 'fix', 'resolve', 'solve'
            ],
            'status_words': [
                'status', 'health', 'state', 'condition', 'up', 'down', 'running', 'stopped',
                'active', 'inactive', 'available', 'unavailable', 'online', 'offline'
            ],
            'file_words': [
                'file', 'directory', 'folder', 'path', 'document', 'data', 'backup', 'archive',
                'copy', 'move', 'transfer', 'sync', 'upload', 'download'
            ],
            'security_words': [
                'security', 'secure', 'permission', 'access', 'authentication', 'authorization',
                'certificate', 'key', 'encryption', 'ssl', 'tls', 'firewall', 'audit'
            ],
            'database_words': [
                'database', 'db', 'mysql', 'postgresql', 'postgres', 'mongodb', 'redis',
                'table', 'query', 'sql', 'nosql', 'dump', 'import', 'export'
            ],
            'network_words': [
                'network', 'connection', 'connectivity', 'port', 'protocol', 'ssh', 'http',
                'https', 'tcp', 'udp', 'ping', 'telnet', 'firewall', 'route'
            ]
        }
    
    def _initialize_disambiguation_rules(self) -> List[Dict[str, Any]]:
        """Initialize rules for disambiguating between similar intents"""
        return [
            {
                'condition': 'has_query_word_and_action_word',
                'rule': 'prefer_information_query_if_no_execution_context',
                'priority': 1
            },
            {
                'condition': 'has_service_and_action',
                'rule': 'prefer_service_management_over_automation',
                'priority': 2
            },
            {
                'condition': 'has_problem_indicators',
                'rule': 'prefer_troubleshooting_over_information_query',
                'priority': 3
            },
            {
                'condition': 'has_file_path_and_action',
                'rule': 'prefer_file_operations_over_automation',
                'priority': 2
            },
            {
                'condition': 'has_user_and_action',
                'rule': 'prefer_user_management_over_automation',
                'priority': 2
            },
            {
                'condition': 'has_database_service',
                'rule': 'prefer_database_operations_over_service_management',
                'priority': 2
            }
        ]
    
    def _initialize_confidence_thresholds(self) -> Dict[str, float]:
        """Initialize confidence thresholds for classification decisions"""
        return {
            'high_confidence': 0.8,
            'medium_confidence': 0.6,
            'low_confidence': 0.4,
            'minimum_confidence': 0.2,
            'disambiguation_threshold': 0.1  # Minimum difference between top intents
        }
    
    def classify_intent(self, text: str, entities: List[Entity], context: Optional[Dict[str, Any]] = None) -> ClassificationResult:
        """
        Classify intent using multiple methods and confidence scoring
        
        Args:
            text: Input text to classify
            entities: Extracted entities from the text
            context: Optional context information
            
        Returns:
            ClassificationResult with intent type and confidence
        """
        try:
            # Preprocess text
            processed_text = text.lower().strip()
            
            # Apply different classification methods
            pattern_results = self._classify_by_patterns(processed_text)
            entity_results = self._classify_by_entities(entities)
            context_results = self._classify_by_context(processed_text, context or {})
            semantic_results = self._classify_by_semantics(processed_text)
            
            # Combine results using weighted scoring
            combined_scores = self._combine_classification_results([
                (pattern_results, 0.4),
                (entity_results, 0.3),
                (context_results, 0.2),
                (semantic_results, 0.1)
            ])
            
            # Apply disambiguation rules
            disambiguated_scores = self._apply_disambiguation_rules(
                combined_scores, processed_text, entities
            )
            
            # Select best intent
            best_intent, confidence = self._select_best_intent(disambiguated_scores)
            
            # Generate alternative intents
            alternatives = self._generate_alternatives(disambiguated_scores, best_intent)
            
            # Collect evidence
            evidence = self._collect_evidence(best_intent, processed_text, entities)
            
            result = ClassificationResult(
                intent_type=best_intent,
                confidence=confidence,
                method=ClassificationMethod.HYBRID,
                evidence=evidence,
                alternative_intents=alternatives,
                metadata={
                    'pattern_scores': pattern_results,
                    'entity_scores': entity_results,
                    'context_scores': context_results,
                    'semantic_scores': semantic_results,
                    'combined_scores': combined_scores,
                    'text_length': len(text),
                    'entity_count': len(entities)
                }
            )
            
            logger.info(f"Classified intent: {best_intent.value} (confidence: {confidence:.2f})")
            return result
            
        except Exception as e:
            logger.error(f"Error classifying intent: {e}")
            return ClassificationResult(
                intent_type=IntentType.UNKNOWN,
                confidence=0.0,
                method=ClassificationMethod.HYBRID,
                evidence=[f"Classification error: {str(e)}"]
            )
    
    def _classify_by_patterns(self, text: str) -> Dict[IntentType, float]:
        """Classify intent based on pattern matching"""
        scores = defaultdict(float)
        
        for intent_type, signature in self.intent_signatures.items():
            score = 0.0
            
            # Check required patterns
            required_matches = 0
            for pattern in signature.required_patterns:
                if re.search(pattern, text, re.IGNORECASE):
                    required_matches += 1
                    score += 1.0
            
            # Must have at least one required pattern match
            if required_matches == 0:
                continue
            
            # Check optional patterns
            for pattern in signature.optional_patterns:
                if re.search(pattern, text, re.IGNORECASE):
                    score += 0.5
            
            # Check exclusion patterns (negative scoring)
            for pattern in signature.exclusion_patterns:
                if re.search(pattern, text, re.IGNORECASE):
                    score -= 0.5
            
            # Apply signature weight
            score *= signature.weight
            
            # Normalize by number of patterns
            total_patterns = len(signature.required_patterns) + len(signature.optional_patterns)
            if total_patterns > 0:
                score = score / total_patterns
            
            scores[intent_type] = max(0.0, min(1.0, score))
        
        return dict(scores)
    
    def _classify_by_entities(self, entities: List[Entity]) -> Dict[IntentType, float]:
        """Classify intent based on entity analysis"""
        scores = defaultdict(float)
        entity_types = [e.type for e in entities]
        entity_counter = Counter(entity_types)
        
        for intent_type, signature in self.intent_signatures.items():
            score = 0.0
            
            # Check required entities
            required_found = 0
            for required_entity in signature.required_entities:
                if required_entity in entity_types:
                    required_found += 1
                    score += 1.0
            
            # Penalty for missing required entities
            if signature.required_entities and required_found == 0:
                continue
            
            # Bonus for optional entities
            for optional_entity in signature.optional_entities:
                if optional_entity in entity_types:
                    score += 0.3
            
            # Bonus for entity combinations
            score += self._calculate_entity_combination_bonus(entity_types, intent_type)
            
            # Normalize by total possible entities
            total_entities = len(signature.required_entities) + len(signature.optional_entities)
            if total_entities > 0:
                score = score / (total_entities + 1)  # +1 to avoid division by zero
            
            scores[intent_type] = max(0.0, min(1.0, score))
        
        return dict(scores)
    
    def _classify_by_context(self, text: str, context: Dict[str, Any]) -> Dict[IntentType, float]:
        """Classify intent based on context analysis"""
        scores = defaultdict(float)
        
        for intent_type, signature in self.intent_signatures.items():
            score = 0.0
            
            # Check context indicators in text
            for indicator in signature.context_indicators:
                if indicator in text:
                    score += 0.5
            
            # Check context from previous conversations
            if 'previous_intent' in context:
                prev_intent = context['previous_intent']
                if prev_intent == intent_type:
                    score += 0.3  # Continuity bonus
            
            # Check domain context
            if 'domain' in context:
                domain = context['domain']
                if self._is_intent_relevant_to_domain(intent_type, domain):
                    score += 0.2
            
            # Check urgency context
            if 'urgency' in context:
                urgency = context['urgency']
                if urgency == 'high' and intent_type == IntentType.TROUBLESHOOTING:
                    score += 0.3
            
            scores[intent_type] = max(0.0, min(1.0, score))
        
        return dict(scores)
    
    def _classify_by_semantics(self, text: str) -> Dict[IntentType, float]:
        """Classify intent based on semantic analysis"""
        scores = defaultdict(float)
        words = text.split()
        
        # Count semantic cluster matches
        cluster_matches = {}
        for cluster_name, cluster_words in self.semantic_clusters.items():
            matches = sum(1 for word in words if any(cw in word for cw in cluster_words))
            cluster_matches[cluster_name] = matches
        
        # Map clusters to intents
        cluster_intent_mapping = {
            'action_words': [IntentType.AUTOMATION_REQUEST, IntentType.SERVICE_MANAGEMENT],
            'query_words': [IntentType.INFORMATION_QUERY, IntentType.SYSTEM_STATUS],
            'problem_words': [IntentType.TROUBLESHOOTING],
            'status_words': [IntentType.SYSTEM_STATUS, IntentType.MONITORING],
            'file_words': [IntentType.FILE_OPERATIONS, IntentType.BACKUP_RESTORE],
            'security_words': [IntentType.SECURITY],
            'database_words': [IntentType.DATABASE_OPERATIONS],
            'network_words': [IntentType.NETWORK_OPERATIONS]
        }
        
        # Calculate scores based on cluster matches
        for cluster_name, intent_types in cluster_intent_mapping.items():
            match_count = cluster_matches.get(cluster_name, 0)
            if match_count > 0:
                semantic_score = min(1.0, match_count / len(words))
                for intent_type in intent_types:
                    scores[intent_type] += semantic_score
        
        # Normalize scores
        max_score = max(scores.values()) if scores else 1.0
        if max_score > 0:
            scores = {k: v / max_score for k, v in scores.items()}
        
        return dict(scores)
    
    def _calculate_entity_combination_bonus(self, entity_types: List[EntityType], intent_type: IntentType) -> float:
        """Calculate bonus score for specific entity combinations"""
        bonus = 0.0
        
        # Service + Action combination
        if EntityType.SERVICE in entity_types and EntityType.ACTION in entity_types:
            if intent_type == IntentType.SERVICE_MANAGEMENT:
                bonus += 0.3
            elif intent_type == IntentType.DATABASE_OPERATIONS:
                bonus += 0.2
        
        # File + Action combination
        if EntityType.FILE_PATH in entity_types and EntityType.ACTION in entity_types:
            if intent_type == IntentType.FILE_OPERATIONS:
                bonus += 0.3
            elif intent_type == IntentType.BACKUP_RESTORE:
                bonus += 0.2
        
        # User + Action combination
        if EntityType.USER in entity_types and EntityType.ACTION in entity_types:
            if intent_type == IntentType.USER_MANAGEMENT:
                bonus += 0.3
        
        # Target + Action combination
        if EntityType.TARGET in entity_types and EntityType.ACTION in entity_types:
            if intent_type == IntentType.AUTOMATION_REQUEST:
                bonus += 0.2
        
        return bonus
    
    def _combine_classification_results(self, results: List[Tuple[Dict[IntentType, float], float]]) -> Dict[IntentType, float]:
        """Combine results from different classification methods using weighted scoring"""
        combined_scores = defaultdict(float)
        total_weight = sum(weight for _, weight in results)
        
        for scores, weight in results:
            normalized_weight = weight / total_weight
            for intent_type, score in scores.items():
                combined_scores[intent_type] += score * normalized_weight
        
        return dict(combined_scores)
    
    def _apply_disambiguation_rules(self, scores: Dict[IntentType, float], text: str, entities: List[Entity]) -> Dict[IntentType, float]:
        """Apply disambiguation rules to resolve conflicts between similar intents"""
        adjusted_scores = scores.copy()
        entity_types = [e.type for e in entities]
        
        # Rule 1: Query words + action words -> prefer information query if no execution context
        if self._has_query_words(text) and self._has_action_words(text):
            if not self._has_execution_context(text):
                adjusted_scores[IntentType.INFORMATION_QUERY] *= 1.2
                adjusted_scores[IntentType.AUTOMATION_REQUEST] *= 0.8
        
        # Rule 2: Service + Action -> prefer service management
        if EntityType.SERVICE in entity_types and EntityType.ACTION in entity_types:
            adjusted_scores[IntentType.SERVICE_MANAGEMENT] *= 1.3
            adjusted_scores[IntentType.AUTOMATION_REQUEST] *= 0.9
        
        # Rule 3: Problem indicators -> prefer troubleshooting
        if self._has_problem_indicators(text):
            adjusted_scores[IntentType.TROUBLESHOOTING] *= 1.4
            adjusted_scores[IntentType.INFORMATION_QUERY] *= 0.8
        
        # Rule 4: File path + Action -> prefer file operations
        if EntityType.FILE_PATH in entity_types and EntityType.ACTION in entity_types:
            adjusted_scores[IntentType.FILE_OPERATIONS] *= 1.3
            adjusted_scores[IntentType.AUTOMATION_REQUEST] *= 0.9
        
        # Rule 5: User + Action -> prefer user management
        if EntityType.USER in entity_types and EntityType.ACTION in entity_types:
            adjusted_scores[IntentType.USER_MANAGEMENT] *= 1.3
            adjusted_scores[IntentType.AUTOMATION_REQUEST] *= 0.9
        
        # Rule 6: Database service -> prefer database operations
        if self._has_database_service(entities):
            adjusted_scores[IntentType.DATABASE_OPERATIONS] *= 1.2
            adjusted_scores[IntentType.SERVICE_MANAGEMENT] *= 0.9
        
        return adjusted_scores
    
    def _select_best_intent(self, scores: Dict[IntentType, float]) -> Tuple[IntentType, float]:
        """Select the best intent based on scores and confidence thresholds"""
        if not scores:
            return IntentType.UNKNOWN, 0.0
        
        # Sort by score
        sorted_intents = sorted(scores.items(), key=lambda x: x[1], reverse=True)
        
        best_intent, best_score = sorted_intents[0]
        
        # Check minimum confidence threshold
        if best_score < self.confidence_thresholds['minimum_confidence']:
            return IntentType.UNKNOWN, best_score
        
        # Check disambiguation threshold if there are multiple high-scoring intents
        if len(sorted_intents) > 1:
            second_best_score = sorted_intents[1][1]
            score_difference = best_score - second_best_score
            
            if score_difference < self.confidence_thresholds['disambiguation_threshold']:
                # Scores are too close, reduce confidence
                best_score *= 0.8
        
        return best_intent, best_score
    
    def _generate_alternatives(self, scores: Dict[IntentType, float], best_intent: IntentType) -> List[Tuple[IntentType, float]]:
        """Generate alternative intent suggestions"""
        alternatives = []
        
        # Sort all intents by score
        sorted_intents = sorted(scores.items(), key=lambda x: x[1], reverse=True)
        
        # Take top alternatives (excluding the best intent)
        for intent_type, score in sorted_intents:
            if intent_type != best_intent and score > self.confidence_thresholds['minimum_confidence']:
                alternatives.append((intent_type, score))
                if len(alternatives) >= 3:  # Limit to top 3 alternatives
                    break
        
        return alternatives
    
    def _collect_evidence(self, intent_type: IntentType, text: str, entities: List[Entity]) -> List[str]:
        """Collect evidence for the classification decision"""
        evidence = []
        
        # Pattern evidence
        signature = self.intent_signatures.get(intent_type)
        if signature:
            for pattern in signature.required_patterns:
                if re.search(pattern, text, re.IGNORECASE):
                    evidence.append(f"Pattern match: {pattern}")
        
        # Entity evidence
        entity_types = [e.type for e in entities]
        if signature:
            for entity_type in signature.required_entities:
                if entity_type in entity_types:
                    evidence.append(f"Required entity found: {entity_type.value}")
        
        # Semantic evidence
        for cluster_name, cluster_words in self.semantic_clusters.items():
            matches = [word for word in text.split() if any(cw in word for cw in cluster_words)]
            if matches:
                evidence.append(f"Semantic cluster '{cluster_name}': {', '.join(matches[:3])}")
        
        return evidence[:5]  # Limit to top 5 pieces of evidence
    
    def _has_query_words(self, text: str) -> bool:
        """Check if text contains query words"""
        query_words = self.semantic_clusters['query_words']
        return any(word in text for word in query_words)
    
    def _has_action_words(self, text: str) -> bool:
        """Check if text contains action words"""
        action_words = self.semantic_clusters['action_words']
        return any(word in text for word in action_words)
    
    def _has_execution_context(self, text: str) -> bool:
        """Check if text has execution context indicators"""
        execution_indicators = ['execute', 'run', 'perform', 'do it', 'go ahead', 'start']
        return any(indicator in text for indicator in execution_indicators)
    
    def _has_problem_indicators(self, text: str) -> bool:
        """Check if text contains problem indicators"""
        problem_words = self.semantic_clusters['problem_words']
        return any(word in text for word in problem_words)
    
    def _has_database_service(self, entities: List[Entity]) -> bool:
        """Check if entities contain database services"""
        database_services = ['mysql', 'postgresql', 'postgres', 'mongodb', 'redis']
        service_entities = [e for e in entities if e.type == EntityType.SERVICE]
        
        for entity in service_entities:
            service_name = entity.normalized_value or entity.value
            if service_name in database_services:
                return True
        
        return False
    
    def _is_intent_relevant_to_domain(self, intent_type: IntentType, domain: str) -> bool:
        """Check if intent is relevant to a specific domain"""
        domain_mappings = {
            'database': [IntentType.DATABASE_OPERATIONS, IntentType.BACKUP_RESTORE],
            'security': [IntentType.SECURITY, IntentType.USER_MANAGEMENT],
            'network': [IntentType.NETWORK_OPERATIONS, IntentType.MONITORING],
            'system': [IntentType.SYSTEM_STATUS, IntentType.SERVICE_MANAGEMENT, IntentType.MONITORING],
            'development': [IntentType.DEPLOYMENT, IntentType.CONFIGURATION]
        }
        
        return intent_type in domain_mappings.get(domain, [])
    
    def get_intent_confidence_explanation(self, result: ClassificationResult) -> str:
        """Generate human-readable explanation of confidence score"""
        confidence = result.confidence
        
        if confidence >= self.confidence_thresholds['high_confidence']:
            explanation = "High confidence - strong pattern matches and clear intent indicators"
        elif confidence >= self.confidence_thresholds['medium_confidence']:
            explanation = "Medium confidence - good pattern matches with some ambiguity"
        elif confidence >= self.confidence_thresholds['low_confidence']:
            explanation = "Low confidence - weak pattern matches or conflicting indicators"
        else:
            explanation = "Very low confidence - unclear intent or insufficient information"
        
        if result.alternative_intents:
            explanation += f". Alternative possibilities: {', '.join([alt[0].value for alt in result.alternative_intents[:2]])}"
        
        return explanation
    
    def export_classification_data(self) -> Dict[str, Any]:
        """Export classification data for analysis or debugging"""
        return {
            'intent_signatures': {
                intent.value: {
                    'required_patterns': sig.required_patterns,
                    'optional_patterns': sig.optional_patterns,
                    'required_entities': [e.value for e in sig.required_entities],
                    'optional_entities': [e.value for e in sig.optional_entities],
                    'context_indicators': sig.context_indicators,
                    'weight': sig.weight
                }
                for intent, sig in self.intent_signatures.items()
            },
            'semantic_clusters': self.semantic_clusters,
            'disambiguation_rules': self.disambiguation_rules,
            'confidence_thresholds': self.confidence_thresholds
        }

# Global instance for easy access
intent_classifier = IntentClassifier()