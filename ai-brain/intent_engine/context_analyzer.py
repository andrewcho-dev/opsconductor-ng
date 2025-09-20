"""
Context Analyzer Module for AI Brain Intent Engine

This module analyzes conversation context, extracts requirements, and provides
intelligent context-aware recommendations for automation tasks.
"""

import re
import json
from typing import Dict, List, Optional, Any, Tuple, Set
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime, timedelta
import logging

from .natural_language_understanding import Intent, IntentType, Entity, EntityType
from .conversation_manager import Conversation, ConversationContext

logger = logging.getLogger(__name__)

class ContextType(Enum):
    """Types of context that can be analyzed"""
    TECHNICAL = "technical"
    TEMPORAL = "temporal"
    SECURITY = "security"
    BUSINESS = "business"
    OPERATIONAL = "operational"
    ENVIRONMENTAL = "environmental"

class RequirementType(Enum):
    """Types of requirements that can be extracted"""
    FUNCTIONAL = "functional"
    NON_FUNCTIONAL = "non_functional"
    SECURITY = "security"
    PERFORMANCE = "performance"
    AVAILABILITY = "availability"
    COMPLIANCE = "compliance"
    OPERATIONAL = "operational"

class RiskLevel(Enum):
    """Risk levels for operations"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

@dataclass
class ContextualRequirement:
    """Represents a requirement extracted from context"""
    type: RequirementType
    description: str
    priority: int  # 1-10, 10 being highest
    source: str  # Where this requirement came from
    confidence: float
    metadata: Dict[str, Any] = field(default_factory=dict)

@dataclass
class RiskAssessment:
    """Risk assessment for an operation"""
    level: RiskLevel
    factors: List[str]
    mitigation_suggestions: List[str]
    approval_required: bool = False
    backup_recommended: bool = False

@dataclass
class ContextualInsight:
    """Insights derived from context analysis"""
    category: str
    insight: str
    confidence: float
    actionable: bool = False
    recommendations: List[str] = field(default_factory=list)

@dataclass
class AnalyzedContext:
    """Complete context analysis result"""
    requirements: List[ContextualRequirement] = field(default_factory=list)
    risk_assessment: Optional[RiskAssessment] = None
    insights: List[ContextualInsight] = field(default_factory=list)
    recommendations: List[str] = field(default_factory=list)
    missing_information: List[str] = field(default_factory=list)
    confidence_score: float = 0.0
    analysis_timestamp: datetime = field(default_factory=datetime.now)

class ContextAnalyzer:
    """
    Advanced context analyzer for intelligent automation requirements extraction
    """
    
    def __init__(self):
        self.risk_patterns = self._initialize_risk_patterns()
        self.requirement_extractors = self._initialize_requirement_extractors()
        self.context_enrichers = self._initialize_context_enrichers()
        self.business_rules = self._initialize_business_rules()
        
    def _initialize_risk_patterns(self) -> Dict[RiskLevel, List[str]]:
        """Initialize patterns that indicate different risk levels"""
        return {
            RiskLevel.CRITICAL: [
                r'\b(production|prod|live|critical|essential|mission.critical)\b',
                r'\b(database|db).*\b(drop|delete|remove|destroy)\b',
                r'\b(delete|remove|destroy).*\b(all|everything|entire)\b',
                r'\b(shutdown|stop|halt).*\b(all|entire|whole)\b',
                r'\b(format|wipe|erase).*\b(disk|drive|partition)\b'
            ],
            RiskLevel.HIGH: [
                r'\b(restart|reboot).*\b(production|prod|live)\b',
                r'\b(modify|change|update).*\b(config|configuration|settings)\b',
                r'\b(install|deploy|upgrade).*\b(production|prod)\b',
                r'\b(firewall|security|access).*\b(disable|remove|open)\b',
                r'\b(root|admin|administrator).*\b(password|access|permission)\b'
            ],
            RiskLevel.MEDIUM: [
                r'\b(restart|reboot|stop|start).*\b(service|daemon)\b',
                r'\b(backup|archive|copy).*\b(large|big|entire)\b',
                r'\b(network|connectivity|connection).*\b(change|modify)\b',
                r'\b(user|account).*\b(create|add|modify|delete)\b',
                r'\b(cron|scheduled|automation).*\b(job|task)\b'
            ],
            RiskLevel.LOW: [
                r'\b(check|verify|test|validate|monitor)\b',
                r'\b(read|view|display|show|list)\b',
                r'\b(log|logs|logging).*\b(view|check|analyze)\b',
                r'\b(status|health|info|information)\b',
                r'\b(temporary|temp|test).*\b(file|directory)\b'
            ]
        }
    
    def _initialize_requirement_extractors(self) -> Dict[RequirementType, List[str]]:
        """Initialize patterns for extracting different types of requirements"""
        return {
            RequirementType.FUNCTIONAL: [
                r'\b(must|should|need to|required to|have to)\b.*\b(work|function|operate|run)\b',
                r'\b(ensure|make sure|verify).*\b(working|running|operational)\b',
                r'\b(automate|automation).*\b(process|task|workflow)\b'
            ],
            RequirementType.PERFORMANCE: [
                r'\b(fast|quick|quickly|speed|performance|efficient)\b',
                r'\b(within|under|less than).*\b(second|minute|hour)\b',
                r'\b(optimize|optimization|improve|enhance)\b.*\b(performance|speed)\b',
                r'\b(load|capacity|throughput|response time)\b'
            ],
            RequirementType.SECURITY: [
                r'\b(secure|security|safely|safe|protected|encrypted)\b',
                r'\b(permission|access|authorization|authentication)\b',
                r'\b(ssl|tls|https|certificate|key|password)\b',
                r'\b(audit|compliance|policy|governance)\b'
            ],
            RequirementType.AVAILABILITY: [
                r'\b(uptime|availability|reliable|always|24/7)\b',
                r'\b(backup|redundancy|failover|disaster recovery)\b',
                r'\b(high availability|ha|cluster|load balance)\b',
                r'\b(downtime|outage|interruption).*\b(minimize|avoid|prevent)\b'
            ],
            RequirementType.COMPLIANCE: [
                r'\b(compliance|compliant|regulation|regulatory|standard)\b',
                r'\b(audit|auditing|logging|tracking|monitoring)\b',
                r'\b(gdpr|hipaa|sox|pci|iso)\b',
                r'\b(policy|procedure|guideline|requirement)\b'
            ],
            RequirementType.OPERATIONAL: [
                r'\b(maintain|maintenance|support|operation|operational)\b',
                r'\b(monitor|monitoring|alert|notification|dashboard)\b',
                r'\b(schedule|scheduled|cron|automated|automatic)\b',
                r'\b(rollback|recovery|restore|undo)\b'
            ]
        }
    
    def _initialize_context_enrichers(self) -> Dict[str, Any]:
        """Initialize context enrichment rules"""
        return {
            'time_sensitivity': {
                'urgent': ['urgent', 'asap', 'immediately', 'now', 'emergency'],
                'scheduled': ['schedule', 'later', 'tonight', 'tomorrow', 'weekend'],
                'maintenance_window': ['maintenance', 'window', 'downtime', 'off-hours']
            },
            'environment_indicators': {
                'production': ['prod', 'production', 'live', 'customer', 'client'],
                'staging': ['staging', 'stage', 'pre-prod', 'uat', 'test'],
                'development': ['dev', 'development', 'local', 'sandbox']
            },
            'scale_indicators': {
                'single': ['server', 'host', 'machine', 'node'],
                'multiple': ['servers', 'hosts', 'machines', 'nodes', 'cluster'],
                'all': ['all', 'entire', 'whole', 'every', 'complete']
            },
            'impact_indicators': {
                'high': ['critical', 'important', 'essential', 'vital', 'key'],
                'medium': ['significant', 'notable', 'considerable'],
                'low': ['minor', 'small', 'simple', 'basic']
            }
        }
    
    def _initialize_business_rules(self) -> Dict[str, Any]:
        """Initialize business rules for context analysis"""
        return {
            'approval_required': {
                'production_changes': True,
                'user_management': True,
                'security_changes': True,
                'data_operations': True
            },
            'backup_required': {
                'database_operations': True,
                'configuration_changes': True,
                'file_operations': True
            },
            'maintenance_window': {
                'production_restarts': True,
                'system_updates': True,
                'network_changes': True
            }
        }
    
    def analyze_context(self, conversation: Conversation, additional_context: Optional[Dict[str, Any]] = None) -> AnalyzedContext:
        """
        Perform comprehensive context analysis
        
        Args:
            conversation: Conversation to analyze
            additional_context: Additional context information
            
        Returns:
            AnalyzedContext with complete analysis results
        """
        try:
            # Initialize analysis result
            analysis = AnalyzedContext()
            
            # Extract text content from conversation
            text_content = self._extract_text_content(conversation)
            
            # Analyze different aspects
            analysis.requirements = self._extract_requirements(text_content, conversation)
            analysis.risk_assessment = self._assess_risk(text_content, conversation)
            analysis.insights = self._generate_insights(text_content, conversation)
            analysis.recommendations = self._generate_recommendations(analysis)
            analysis.missing_information = self._identify_missing_information(conversation)
            
            # Calculate overall confidence
            analysis.confidence_score = self._calculate_confidence_score(analysis)
            
            logger.info(f"Context analysis completed with confidence {analysis.confidence_score:.2f}")
            return analysis
            
        except Exception as e:
            logger.error(f"Error analyzing context: {e}")
            return AnalyzedContext()
    
    def _extract_text_content(self, conversation: Conversation) -> str:
        """Extract all text content from conversation messages"""
        text_parts = []
        
        for message in conversation.messages:
            if message.content:
                text_parts.append(message.content)
        
        return " ".join(text_parts).lower()
    
    def _extract_requirements(self, text_content: str, conversation: Conversation) -> List[ContextualRequirement]:
        """Extract requirements from text content and conversation context"""
        requirements = []
        
        for req_type, patterns in self.requirement_extractors.items():
            for pattern in patterns:
                matches = re.findall(pattern, text_content, re.IGNORECASE)
                
                if matches:
                    # Calculate confidence based on pattern strength and frequency
                    confidence = min(0.7 + (len(matches) * 0.1), 1.0)
                    
                    # Determine priority based on requirement type and context
                    priority = self._calculate_requirement_priority(req_type, conversation)
                    
                    requirement = ContextualRequirement(
                        type=req_type,
                        description=self._generate_requirement_description(req_type, matches),
                        priority=priority,
                        source="text_analysis",
                        confidence=confidence,
                        metadata={'matches': matches, 'pattern': pattern}
                    )
                    
                    requirements.append(requirement)
        
        # Add requirements from entities
        entity_requirements = self._extract_requirements_from_entities(conversation)
        requirements.extend(entity_requirements)
        
        # Deduplicate and sort by priority
        requirements = self._deduplicate_requirements(requirements)
        requirements.sort(key=lambda r: r.priority, reverse=True)
        
        return requirements
    
    def _assess_risk(self, text_content: str, conversation: Conversation) -> RiskAssessment:
        """Assess risk level for the operation"""
        risk_scores = {level: 0 for level in RiskLevel}
        risk_factors = []
        
        # Analyze text patterns
        for risk_level, patterns in self.risk_patterns.items():
            for pattern in patterns:
                matches = re.findall(pattern, text_content, re.IGNORECASE)
                if matches:
                    risk_scores[risk_level] += len(matches)
                    risk_factors.extend([f"Pattern match: {match}" for match in matches])
        
        # Analyze entities for risk indicators
        entity_risks = self._assess_entity_risks(conversation)
        for risk_level, factors in entity_risks.items():
            risk_scores[risk_level] += len(factors)
            risk_factors.extend(factors)
        
        # Determine overall risk level
        max_risk_level = max(risk_scores.items(), key=lambda x: x[1])[0]
        
        # Generate mitigation suggestions
        mitigation_suggestions = self._generate_mitigation_suggestions(max_risk_level, risk_factors)
        
        # Determine if approval/backup is required
        approval_required = self._requires_approval(max_risk_level, conversation)
        backup_recommended = self._requires_backup(max_risk_level, conversation)
        
        return RiskAssessment(
            level=max_risk_level,
            factors=risk_factors,
            mitigation_suggestions=mitigation_suggestions,
            approval_required=approval_required,
            backup_recommended=backup_recommended
        )
    
    def _generate_insights(self, text_content: str, conversation: Conversation) -> List[ContextualInsight]:
        """Generate contextual insights from analysis"""
        insights = []
        
        # Time sensitivity insights
        time_insights = self._analyze_time_sensitivity(text_content)
        insights.extend(time_insights)
        
        # Environment insights
        env_insights = self._analyze_environment_context(text_content)
        insights.extend(env_insights)
        
        # Scale insights
        scale_insights = self._analyze_scale_context(text_content)
        insights.extend(scale_insights)
        
        # Impact insights
        impact_insights = self._analyze_impact_context(text_content)
        insights.extend(impact_insights)
        
        # Entity relationship insights
        entity_insights = self._analyze_entity_relationships(conversation)
        insights.extend(entity_insights)
        
        return insights
    
    def _analyze_time_sensitivity(self, text_content: str) -> List[ContextualInsight]:
        """Analyze time sensitivity from text"""
        insights = []
        
        for sensitivity, keywords in self.context_enrichers['time_sensitivity'].items():
            if any(keyword in text_content for keyword in keywords):
                if sensitivity == 'urgent':
                    insights.append(ContextualInsight(
                        category="time_sensitivity",
                        insight="This request appears to be urgent and requires immediate attention",
                        confidence=0.8,
                        actionable=True,
                        recommendations=["Prioritize this request", "Consider immediate execution"]
                    ))
                elif sensitivity == 'scheduled':
                    insights.append(ContextualInsight(
                        category="time_sensitivity",
                        insight="This request can be scheduled for later execution",
                        confidence=0.7,
                        actionable=True,
                        recommendations=["Schedule during appropriate time window", "Consider maintenance window"]
                    ))
        
        return insights
    
    def _analyze_environment_context(self, text_content: str) -> List[ContextualInsight]:
        """Analyze environment context from text"""
        insights = []
        
        for env_type, keywords in self.context_enrichers['environment_indicators'].items():
            if any(keyword in text_content for keyword in keywords):
                if env_type == 'production':
                    insights.append(ContextualInsight(
                        category="environment",
                        insight="This operation targets production environment - extra caution required",
                        confidence=0.9,
                        actionable=True,
                        recommendations=[
                            "Require approval before execution",
                            "Create backup before changes",
                            "Schedule during maintenance window",
                            "Have rollback plan ready"
                        ]
                    ))
                elif env_type == 'development':
                    insights.append(ContextualInsight(
                        category="environment",
                        insight="This operation targets development environment - lower risk",
                        confidence=0.8,
                        actionable=True,
                        recommendations=["Can proceed with standard precautions"]
                    ))
        
        return insights
    
    def _analyze_scale_context(self, text_content: str) -> List[ContextualInsight]:
        """Analyze scale context from text"""
        insights = []
        
        for scale, keywords in self.context_enrichers['scale_indicators'].items():
            if any(keyword in text_content for keyword in keywords):
                if scale == 'all':
                    insights.append(ContextualInsight(
                        category="scale",
                        insight="This operation affects all systems - high impact potential",
                        confidence=0.9,
                        actionable=True,
                        recommendations=[
                            "Consider phased rollout",
                            "Test on subset first",
                            "Have comprehensive rollback plan"
                        ]
                    ))
                elif scale == 'multiple':
                    insights.append(ContextualInsight(
                        category="scale",
                        insight="This operation affects multiple systems - consider parallel execution",
                        confidence=0.7,
                        actionable=True,
                        recommendations=["Consider parallel execution", "Monitor all systems during execution"]
                    ))
        
        return insights
    
    def _analyze_impact_context(self, text_content: str) -> List[ContextualInsight]:
        """Analyze impact context from text"""
        insights = []
        
        for impact_level, keywords in self.context_enrichers['impact_indicators'].items():
            if any(keyword in text_content for keyword in keywords):
                if impact_level == 'high':
                    insights.append(ContextualInsight(
                        category="impact",
                        insight="This operation has high business impact",
                        confidence=0.8,
                        actionable=True,
                        recommendations=[
                            "Notify stakeholders",
                            "Schedule during low-usage period",
                            "Have support team on standby"
                        ]
                    ))
        
        return insights
    
    def _analyze_entity_relationships(self, conversation: Conversation) -> List[ContextualInsight]:
        """Analyze relationships between entities"""
        insights = []
        entities = conversation.context.collected_entities
        
        # Check for database + destructive action combination
        if (EntityType.SERVICE in entities and EntityType.ACTION in entities):
            services = [e.normalized_value or e.value for e in entities[EntityType.SERVICE]]
            actions = [e.normalized_value or e.value for e in entities[EntityType.ACTION]]
            
            db_services = ['mysql', 'postgresql', 'mongodb', 'redis']
            destructive_actions = ['delete', 'drop', 'remove', 'destroy']
            
            if (any(svc in db_services for svc in services) and 
                any(action in destructive_actions for action in actions)):
                insights.append(ContextualInsight(
                    category="entity_relationship",
                    insight="Database destructive operation detected - critical risk",
                    confidence=0.95,
                    actionable=True,
                    recommendations=[
                        "Mandatory backup before execution",
                        "Require multiple approvals",
                        "Test on non-production first"
                    ]
                ))
        
        return insights
    
    def _calculate_requirement_priority(self, req_type: RequirementType, conversation: Conversation) -> int:
        """Calculate priority for a requirement based on type and context"""
        base_priorities = {
            RequirementType.SECURITY: 9,
            RequirementType.COMPLIANCE: 8,
            RequirementType.AVAILABILITY: 7,
            RequirementType.FUNCTIONAL: 6,
            RequirementType.PERFORMANCE: 5,
            RequirementType.OPERATIONAL: 4,
            RequirementType.NON_FUNCTIONAL: 3
        }
        
        priority = base_priorities.get(req_type, 5)
        
        # Adjust based on context
        if conversation.context.target_intent == IntentType.TROUBLESHOOTING:
            priority += 2
        elif conversation.context.target_intent == IntentType.SECURITY:
            priority += 1
        
        return min(priority, 10)
    
    def _generate_requirement_description(self, req_type: RequirementType, matches: List[str]) -> str:
        """Generate human-readable requirement description"""
        descriptions = {
            RequirementType.FUNCTIONAL: f"System must function properly: {', '.join(matches[:3])}",
            RequirementType.PERFORMANCE: f"Performance requirements identified: {', '.join(matches[:3])}",
            RequirementType.SECURITY: f"Security requirements detected: {', '.join(matches[:3])}",
            RequirementType.AVAILABILITY: f"Availability requirements: {', '.join(matches[:3])}",
            RequirementType.COMPLIANCE: f"Compliance requirements: {', '.join(matches[:3])}",
            RequirementType.OPERATIONAL: f"Operational requirements: {', '.join(matches[:3])}"
        }
        
        return descriptions.get(req_type, f"Requirements of type {req_type.value}")
    
    def _extract_requirements_from_entities(self, conversation: Conversation) -> List[ContextualRequirement]:
        """Extract requirements from conversation entities"""
        requirements = []
        entities = conversation.context.collected_entities
        
        # If targets are specified, add operational requirement
        if EntityType.TARGET in entities:
            requirements.append(ContextualRequirement(
                type=RequirementType.OPERATIONAL,
                description="Operation must target specified systems",
                priority=7,
                source="entity_analysis",
                confidence=0.9
            ))
        
        # If time is specified, add scheduling requirement
        if EntityType.TIME in entities:
            requirements.append(ContextualRequirement(
                type=RequirementType.OPERATIONAL,
                description="Operation must be executed at specified time",
                priority=6,
                source="entity_analysis",
                confidence=0.8
            ))
        
        return requirements
    
    def _deduplicate_requirements(self, requirements: List[ContextualRequirement]) -> List[ContextualRequirement]:
        """Remove duplicate requirements"""
        seen = set()
        deduplicated = []
        
        for req in requirements:
            key = (req.type, req.description[:50])  # Use first 50 chars as key
            if key not in seen:
                seen.add(key)
                deduplicated.append(req)
        
        return deduplicated
    
    def _assess_entity_risks(self, conversation: Conversation) -> Dict[RiskLevel, List[str]]:
        """Assess risks based on entities"""
        risks = {level: [] for level in RiskLevel}
        entities = conversation.context.collected_entities
        
        # Check for high-risk combinations
        if EntityType.ACTION in entities and EntityType.SERVICE in entities:
            actions = [e.normalized_value or e.value for e in entities[EntityType.ACTION]]
            services = [e.normalized_value or e.value for e in entities[EntityType.SERVICE]]
            
            # Database + destructive action = critical risk
            if any(svc in ['mysql', 'postgresql', 'mongodb'] for svc in services):
                if any(action in ['delete', 'drop', 'remove'] for action in actions):
                    risks[RiskLevel.CRITICAL].append("Database destructive operation")
                elif any(action in ['restart', 'stop'] for action in actions):
                    risks[RiskLevel.HIGH].append("Database service interruption")
        
        return risks
    
    def _generate_mitigation_suggestions(self, risk_level: RiskLevel, risk_factors: List[str]) -> List[str]:
        """Generate mitigation suggestions based on risk level"""
        suggestions = []
        
        if risk_level == RiskLevel.CRITICAL:
            suggestions.extend([
                "Create full system backup before execution",
                "Require multiple approvals",
                "Test on non-production environment first",
                "Have immediate rollback plan ready",
                "Notify all stakeholders",
                "Schedule during maintenance window"
            ])
        elif risk_level == RiskLevel.HIGH:
            suggestions.extend([
                "Create backup of affected components",
                "Require approval from team lead",
                "Test on staging environment",
                "Have rollback plan ready",
                "Monitor closely during execution"
            ])
        elif risk_level == RiskLevel.MEDIUM:
            suggestions.extend([
                "Create backup if modifying data",
                "Test on development environment",
                "Monitor execution progress",
                "Have basic rollback plan"
            ])
        else:  # LOW risk
            suggestions.extend([
                "Standard monitoring during execution",
                "Basic logging and verification"
            ])
        
        return suggestions
    
    def _requires_approval(self, risk_level: RiskLevel, conversation: Conversation) -> bool:
        """Determine if approval is required"""
        if risk_level in [RiskLevel.CRITICAL, RiskLevel.HIGH]:
            return True
        
        # Check business rules
        intent_type = conversation.context.target_intent
        if intent_type in [IntentType.USER_MANAGEMENT, IntentType.SECURITY]:
            return True
        
        return False
    
    def _requires_backup(self, risk_level: RiskLevel, conversation: Conversation) -> bool:
        """Determine if backup is recommended"""
        if risk_level in [RiskLevel.CRITICAL, RiskLevel.HIGH]:
            return True
        
        # Check for data operations
        entities = conversation.context.collected_entities
        if EntityType.SERVICE in entities:
            services = [e.normalized_value or e.value for e in entities[EntityType.SERVICE]]
            if any(svc in ['mysql', 'postgresql', 'mongodb'] for svc in services):
                return True
        
        return False
    
    def _generate_recommendations(self, analysis: AnalyzedContext) -> List[str]:
        """Generate overall recommendations based on analysis"""
        recommendations = []
        
        # Risk-based recommendations
        if analysis.risk_assessment:
            recommendations.extend(analysis.risk_assessment.mitigation_suggestions[:3])
        
        # Requirement-based recommendations
        high_priority_reqs = [req for req in analysis.requirements if req.priority >= 8]
        if high_priority_reqs:
            recommendations.append("Address high-priority requirements before execution")
        
        # Insight-based recommendations
        actionable_insights = [insight for insight in analysis.insights if insight.actionable]
        for insight in actionable_insights[:2]:  # Top 2 actionable insights
            recommendations.extend(insight.recommendations[:2])
        
        # Remove duplicates and limit
        recommendations = list(dict.fromkeys(recommendations))[:5]
        
        return recommendations
    
    def _identify_missing_information(self, conversation: Conversation) -> List[str]:
        """Identify missing information that could improve analysis"""
        missing = []
        entities = conversation.context.collected_entities
        
        # Check for missing critical entities
        if EntityType.TARGET not in entities:
            missing.append("Target systems not specified")
        
        if EntityType.ACTION not in entities:
            missing.append("Specific action not clearly defined")
        
        # Check for missing context based on intent
        intent_type = conversation.context.target_intent
        if intent_type == IntentType.SERVICE_MANAGEMENT and EntityType.SERVICE not in entities:
            missing.append("Service name not specified")
        
        if intent_type == IntentType.FILE_OPERATIONS and EntityType.FILE_PATH not in entities:
            missing.append("File paths not specified")
        
        # Check for missing operational details
        if EntityType.TIME not in entities:
            missing.append("Execution timing not specified")
        
        return missing
    
    def _calculate_confidence_score(self, analysis: AnalyzedContext) -> float:
        """Calculate overall confidence score for the analysis"""
        scores = []
        
        # Requirement confidence
        if analysis.requirements:
            req_confidence = sum(req.confidence for req in analysis.requirements) / len(analysis.requirements)
            scores.append(req_confidence)
        
        # Insight confidence
        if analysis.insights:
            insight_confidence = sum(insight.confidence for insight in analysis.insights) / len(analysis.insights)
            scores.append(insight_confidence)
        
        # Completeness score (based on missing information)
        completeness = max(0.3, 1.0 - (len(analysis.missing_information) * 0.1))
        scores.append(completeness)
        
        # Overall confidence
        if scores:
            return sum(scores) / len(scores)
        else:
            return 0.5  # Default moderate confidence
    
    def export_analysis(self, analysis: AnalyzedContext) -> Dict[str, Any]:
        """Export analysis results for documentation or debugging"""
        return {
            'requirements': [
                {
                    'type': req.type.value,
                    'description': req.description,
                    'priority': req.priority,
                    'confidence': req.confidence,
                    'source': req.source
                }
                for req in analysis.requirements
            ],
            'risk_assessment': {
                'level': analysis.risk_assessment.level.value if analysis.risk_assessment else 'unknown',
                'factors': analysis.risk_assessment.factors if analysis.risk_assessment else [],
                'mitigation_suggestions': analysis.risk_assessment.mitigation_suggestions if analysis.risk_assessment else [],
                'approval_required': analysis.risk_assessment.approval_required if analysis.risk_assessment else False,
                'backup_recommended': analysis.risk_assessment.backup_recommended if analysis.risk_assessment else False
            },
            'insights': [
                {
                    'category': insight.category,
                    'insight': insight.insight,
                    'confidence': insight.confidence,
                    'actionable': insight.actionable,
                    'recommendations': insight.recommendations
                }
                for insight in analysis.insights
            ],
            'recommendations': analysis.recommendations,
            'missing_information': analysis.missing_information,
            'confidence_score': analysis.confidence_score,
            'analysis_timestamp': analysis.analysis_timestamp.isoformat()
        }

# Global instance for easy access
context_analyzer = ContextAnalyzer()