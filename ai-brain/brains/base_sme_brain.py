"""
SME Brain Base Class - Multi-Brain AI Architecture

Base class for all Subject Matter Expert (SME) brains in the multi-brain architecture.
SME brains provide domain-specific expertise and recommendations.

Phase 1 Week 3 Implementation - Following exact roadmap specification.
"""

import logging
from typing import Dict, Any, List, Optional, Set
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime
from abc import ABC, abstractmethod
import asyncio

logger = logging.getLogger(__name__)

class SMEConfidenceLevel(Enum):
    """SME confidence levels for recommendations"""
    VERY_HIGH = "very_high"     # 0.9-1.0
    HIGH = "high"               # 0.7-0.89
    MEDIUM = "medium"           # 0.5-0.69
    LOW = "low"                 # 0.3-0.49
    VERY_LOW = "very_low"       # 0.0-0.29

class SMERecommendationType(Enum):
    """Types of SME recommendations"""
    BEST_PRACTICE = "best_practice"
    SECURITY_REQUIREMENT = "security_requirement"
    PERFORMANCE_OPTIMIZATION = "performance_optimization"
    RISK_MITIGATION = "risk_mitigation"
    CONFIGURATION_GUIDANCE = "configuration_guidance"
    TROUBLESHOOTING_STEP = "troubleshooting_step"
    VALIDATION_CHECK = "validation_check"

@dataclass
class SMEQuery:
    """Query sent to SME brain for expertise"""
    query_id: str
    domain: str
    context: str
    technical_plan: Dict[str, Any]
    intent_analysis: Dict[str, Any]
    specific_questions: List[str] = field(default_factory=list)
    urgency: str = "medium"
    risk_level: str = "medium"
    environment: str = "production"  # production, staging, development
    constraints: List[str] = field(default_factory=list)
    timestamp: datetime = field(default_factory=datetime.now)

@dataclass
class SMEConfidence:
    """Confidence score with reasoning for SME recommendations"""
    score: float  # 0.0 to 1.0
    reasoning: str
    factors: Dict[str, float] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization"""
        return {
            "score": self.score,
            "reasoning": self.reasoning,
            "factors": self.factors
        }

@dataclass
class SMERecommendation:
    """Recommendation from SME brain"""
    recommendation_id: str
    domain: str
    query_id: str
    recommendation_type: SMERecommendationType
    title: str
    description: str
    rationale: str
    confidence: float
    priority: str  # critical, high, medium, low
    implementation_steps: List[str] = field(default_factory=list)
    validation_criteria: List[str] = field(default_factory=list)
    risks_if_ignored: List[str] = field(default_factory=list)
    dependencies: List[str] = field(default_factory=list)
    estimated_effort: str = "medium"  # low, medium, high
    references: List[str] = field(default_factory=list)
    tags: List[str] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.now)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization"""
        return {
            "recommendation_id": self.recommendation_id,
            "domain": self.domain,
            "query_id": self.query_id,
            "recommendation_type": self.recommendation_type.value,
            "title": self.title,
            "description": self.description,
            "rationale": self.rationale,
            "confidence": self.confidence,
            "priority": self.priority,
            "implementation_steps": self.implementation_steps,
            "validation_criteria": self.validation_criteria,
            "risks_if_ignored": self.risks_if_ignored,
            "dependencies": self.dependencies,
            "estimated_effort": self.estimated_effort,
            "references": self.references,
            "tags": self.tags,
            "created_at": self.created_at.isoformat()
        }

@dataclass
class ExecutionData:
    """Data from execution results for learning"""
    execution_id: str
    domain: str
    recommendations_used: List[str]
    execution_success: bool
    performance_metrics: Dict[str, Any] = field(default_factory=dict)
    error_details: Optional[str] = None
    user_feedback: Optional[str] = None
    lessons_learned: List[str] = field(default_factory=list)
    execution_time: Optional[float] = None
    resource_usage: Dict[str, Any] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.now)

class SMEKnowledgeBase:
    """Knowledge base for SME domain expertise"""
    
    def __init__(self, domain: str):
        self.domain = domain
        self.knowledge_entries = {}
        self.best_practices = []
        self.common_patterns = {}
        self.failure_patterns = {}
        self.performance_benchmarks = {}
        
        # Load domain-specific knowledge
        self._load_domain_knowledge()
    
    def _load_domain_knowledge(self):
        """Load domain-specific knowledge (to be overridden by specific SME brains)"""
        pass
    
    async def query_knowledge(self, query: str, context: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Query the knowledge base"""
        # Simple keyword-based search for Phase 1
        # Will be enhanced with vector search in later phases
        results = []
        query_lower = query.lower()
        
        for entry_id, entry in self.knowledge_entries.items():
            if any(keyword in entry.get("content", "").lower() for keyword in query_lower.split()):
                results.append({
                    "entry_id": entry_id,
                    "relevance_score": 0.7,  # Simplified scoring
                    "content": entry.get("content", ""),
                    "tags": entry.get("tags", []),
                    "confidence": entry.get("confidence", 0.5)
                })
        
        return sorted(results, key=lambda x: x["relevance_score"], reverse=True)[:5]
    
    async def add_knowledge(self, entry_id: str, content: str, tags: List[str], confidence: float = 0.8):
        """Add new knowledge entry"""
        self.knowledge_entries[entry_id] = {
            "content": content,
            "tags": tags,
            "confidence": confidence,
            "created_at": datetime.now().isoformat()
        }
    
    async def update_knowledge(self, entry_id: str, updates: Dict[str, Any]):
        """Update existing knowledge entry"""
        if entry_id in self.knowledge_entries:
            self.knowledge_entries[entry_id].update(updates)
            self.knowledge_entries[entry_id]["updated_at"] = datetime.now().isoformat()

class SMELearningEngine:
    """Learning engine for SME brains"""
    
    def __init__(self, domain: str):
        self.domain = domain
        self.learning_history = []
        self.success_patterns = {}
        self.failure_patterns = {}
        self.performance_trends = {}
    
    async def learn_from_execution(self, execution_data: ExecutionData):
        """Learn from execution results"""
        try:
            # Record learning event
            learning_event = {
                "execution_id": execution_data.execution_id,
                "success": execution_data.execution_success,
                "recommendations_used": execution_data.recommendations_used,
                "performance_metrics": execution_data.performance_metrics,
                "timestamp": execution_data.timestamp.isoformat()
            }
            self.learning_history.append(learning_event)
            
            # Update success/failure patterns
            if execution_data.execution_success:
                await self._update_success_patterns(execution_data)
            else:
                await self._update_failure_patterns(execution_data)
            
            # Update performance trends
            await self._update_performance_trends(execution_data)
            
            logger.info(f"SME Learning Engine ({self.domain}) learned from execution: {execution_data.execution_id}")
            
        except Exception as e:
            logger.error(f"Error in SME learning: {str(e)}")
    
    async def _update_success_patterns(self, execution_data: ExecutionData):
        """Update patterns that lead to success"""
        for recommendation_id in execution_data.recommendations_used:
            if recommendation_id not in self.success_patterns:
                self.success_patterns[recommendation_id] = {"count": 0, "avg_performance": 0.0}
            
            self.success_patterns[recommendation_id]["count"] += 1
            
            # Update average performance if metrics available
            if execution_data.performance_metrics:
                current_avg = self.success_patterns[recommendation_id]["avg_performance"]
                new_performance = execution_data.performance_metrics.get("overall_score", 0.5)
                count = self.success_patterns[recommendation_id]["count"]
                self.success_patterns[recommendation_id]["avg_performance"] = (current_avg * (count - 1) + new_performance) / count
    
    async def _update_failure_patterns(self, execution_data: ExecutionData):
        """Update patterns that lead to failure"""
        failure_key = f"failure_{len(self.failure_patterns)}"
        self.failure_patterns[failure_key] = {
            "recommendations_used": execution_data.recommendations_used,
            "error_details": execution_data.error_details,
            "context": execution_data.resource_usage,
            "timestamp": execution_data.timestamp.isoformat()
        }
    
    async def _update_performance_trends(self, execution_data: ExecutionData):
        """Update performance trends"""
        if execution_data.performance_metrics:
            date_key = execution_data.timestamp.strftime("%Y-%m-%d")
            if date_key not in self.performance_trends:
                self.performance_trends[date_key] = []
            
            self.performance_trends[date_key].append({
                "execution_id": execution_data.execution_id,
                "metrics": execution_data.performance_metrics,
                "success": execution_data.execution_success
            })
    
    async def get_learning_insights(self) -> Dict[str, Any]:
        """Get insights from learning data"""
        total_executions = len(self.learning_history)
        successful_executions = sum(1 for event in self.learning_history if event["success"])
        
        return {
            "domain": self.domain,
            "total_executions": total_executions,
            "success_rate": successful_executions / total_executions if total_executions > 0 else 0.0,
            "top_successful_recommendations": sorted(
                self.success_patterns.items(),
                key=lambda x: x[1]["count"],
                reverse=True
            )[:5],
            "failure_count": len(self.failure_patterns),
            "learning_trend": "improving" if successful_executions > total_executions * 0.7 else "needs_attention"
        }

class SMEConfidenceCalculator:
    """Calculates confidence scores for SME recommendations"""
    
    def __init__(self):
        self.base_confidence = 0.7
        self.confidence_factors = {
            "knowledge_base_match": 0.2,
            "historical_success": 0.15,
            "domain_expertise": 0.1,
            "context_relevance": 0.15,
            "risk_assessment": -0.1  # High risk reduces confidence
        }
    
    async def calculate_confidence(self, recommendation: SMERecommendation, context: Dict[str, Any]) -> float:
        """Calculate confidence score for a recommendation"""
        confidence = self.base_confidence
        
        # Adjust based on knowledge base match
        knowledge_match_score = context.get("knowledge_match_score", 0.5)
        confidence += knowledge_match_score * self.confidence_factors["knowledge_base_match"]
        
        # Adjust based on historical success
        historical_success = context.get("historical_success_rate", 0.5)
        confidence += historical_success * self.confidence_factors["historical_success"]
        
        # Adjust based on domain expertise level
        domain_expertise = context.get("domain_expertise_level", 0.7)
        confidence += domain_expertise * self.confidence_factors["domain_expertise"]
        
        # Adjust based on context relevance
        context_relevance = context.get("context_relevance_score", 0.6)
        confidence += context_relevance * self.confidence_factors["context_relevance"]
        
        # Adjust based on risk level
        risk_level = context.get("risk_level", "medium")
        if risk_level == "high":
            confidence += self.confidence_factors["risk_assessment"]
        
        # Ensure confidence is within valid range
        return max(0.1, min(1.0, confidence))

class SMEBrain(ABC):
    """
    Abstract base class for all SME (Subject Matter Expert) brains
    
    Phase 1 Week 3 Implementation following exact roadmap specification.
    
    Each SME brain provides domain-specific expertise and recommendations
    to enhance the Technical Brain's execution plans.
    """
    
    def __init__(self, domain: str, expertise_areas: List[str]):
        self.domain = domain
        self.expertise_areas = expertise_areas
        self.brain_id = f"sme_brain_{domain}"
        self.brain_type = "sme"
        self.brain_version = "1.0.0"
        
        # Core components
        self.knowledge_base = SMEKnowledgeBase(domain)
        self.learning_engine = SMELearningEngine(domain)
        self.confidence_calculator = SMEConfidenceCalculator()
        
        # SME-specific configuration
        self.confidence_threshold = 0.6
        self.max_recommendations_per_query = 5
        
        # Tracking
        self.query_history = []
        self.recommendation_history = []
        
        logger.info(f"SME Brain initialized for domain: {domain}")
    
    @abstractmethod
    async def provide_expertise(self, query: SMEQuery) -> List[SMERecommendation]:
        """
        Provide domain-specific expertise for a query
        
        This method must be implemented by each specific SME brain.
        
        Args:
            query: SME query containing context and requirements
            
        Returns:
            List of SME recommendations
        """
        pass
    
    @abstractmethod
    async def analyze_technical_plan(self, technical_plan: Dict[str, Any], intent_analysis: Dict[str, Any]) -> Dict[str, Any]:
        """
        Analyze technical plan from domain perspective
        
        Args:
            technical_plan: Technical plan from Technical Brain
            intent_analysis: Original intent analysis
            
        Returns:
            Analysis results with recommendations and risk assessment
        """
        pass
    
    async def learn_from_execution(self, execution_data: ExecutionData):
        """
        Learn from execution results to improve future recommendations
        
        Args:
            execution_data: Data from execution results
        """
        try:
            await self.learning_engine.learn_from_execution(execution_data)
            
            # Update knowledge base based on learnings
            if execution_data.lessons_learned:
                for lesson in execution_data.lessons_learned:
                    await self.knowledge_base.add_knowledge(
                        entry_id=f"lesson_{execution_data.execution_id}_{len(execution_data.lessons_learned)}",
                        content=lesson,
                        tags=["lesson_learned", self.domain],
                        confidence=0.8 if execution_data.execution_success else 0.6
                    )
            
            logger.info(f"SME Brain ({self.domain}) learned from execution: {execution_data.execution_id}")
            
        except Exception as e:
            logger.error(f"Error in SME learning: {str(e)}")
    
    async def get_domain_expertise_level(self, context: str) -> float:
        """Get expertise level for specific context"""
        # Simple implementation for Phase 1
        # Will be enhanced with more sophisticated analysis in later phases
        context_lower = context.lower()
        
        expertise_score = 0.5  # Base expertise
        
        # Increase score if context matches expertise areas
        for area in self.expertise_areas:
            if area.replace("_", " ") in context_lower:
                expertise_score += 0.1
        
        return min(1.0, expertise_score)
    
    async def validate_recommendation(self, recommendation: SMERecommendation, context: Dict[str, Any]) -> Dict[str, Any]:
        """Validate a recommendation against context and constraints"""
        validation_result = {
            "valid": True,
            "confidence_adjustment": 0.0,
            "warnings": [],
            "blocking_issues": []
        }
        
        # Check against constraints
        constraints = context.get("constraints", [])
        for constraint in constraints:
            if constraint.lower() in recommendation.description.lower():
                validation_result["warnings"].append(f"Recommendation may conflict with constraint: {constraint}")
                validation_result["confidence_adjustment"] -= 0.1
        
        # Check risk level compatibility
        risk_level = context.get("risk_level", "medium")
        if risk_level == "high" and recommendation.priority == "low":
            validation_result["warnings"].append("Low priority recommendation in high-risk context")
            validation_result["confidence_adjustment"] -= 0.05
        
        return validation_result
    
    async def get_brain_status(self) -> Dict[str, Any]:
        """Get current status of SME brain"""
        learning_insights = await self.learning_engine.get_learning_insights()
        
        return {
            "brain_id": self.brain_id,
            "brain_type": self.brain_type,
            "brain_version": self.brain_version,
            "domain": self.domain,
            "expertise_areas": self.expertise_areas,
            "confidence_threshold": self.confidence_threshold,
            "status": "active",
            "knowledge_base_size": len(self.knowledge_base.knowledge_entries),
            "query_count": len(self.query_history),
            "recommendation_count": len(self.recommendation_history),
            "learning_insights": learning_insights
        }
    
    async def _create_recommendation(
        self,
        query: SMEQuery,
        recommendation_type: SMERecommendationType,
        title: str,
        description: str,
        rationale: str,
        implementation_steps: List[str],
        priority: str = "medium",
        validation_criteria: List[str] = None,
        risks_if_ignored: List[str] = None,
        dependencies: List[str] = None,
        estimated_effort: str = "medium",
        references: List[str] = None,
        tags: List[str] = None
    ) -> SMERecommendation:
        """Helper method to create SME recommendations"""
        
        recommendation_id = f"{self.domain}_rec_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{len(self.recommendation_history)}"
        
        # Calculate confidence
        context = {
            "knowledge_match_score": 0.7,  # Will be calculated based on knowledge base match
            "historical_success_rate": 0.6,  # Will be calculated from learning engine
            "domain_expertise_level": await self.get_domain_expertise_level(query.context),
            "context_relevance_score": 0.8,  # Will be calculated based on query relevance
            "risk_level": query.risk_level
        }
        
        recommendation = SMERecommendation(
            recommendation_id=recommendation_id,
            domain=self.domain,
            query_id=query.query_id,
            recommendation_type=recommendation_type,
            title=title,
            description=description,
            rationale=rationale,
            confidence=0.7,  # Will be calculated by confidence calculator
            priority=priority,
            implementation_steps=implementation_steps or [],
            validation_criteria=validation_criteria or [],
            risks_if_ignored=risks_if_ignored or [],
            dependencies=dependencies or [],
            estimated_effort=estimated_effort,
            references=references or [],
            tags=tags or [self.domain]
        )
        
        # Calculate actual confidence
        recommendation.confidence = await self.confidence_calculator.calculate_confidence(recommendation, context)
        
        # Validate recommendation
        validation_result = await self.validate_recommendation(recommendation, context)
        recommendation.confidence += validation_result["confidence_adjustment"]
        recommendation.confidence = max(0.1, min(1.0, recommendation.confidence))
        
        # Track recommendation
        self.recommendation_history.append(recommendation)
        
        return recommendation
    
    def _extract_relevant_context(self, technical_plan: Dict[str, Any], intent_analysis: Dict[str, Any]) -> str:
        """Extract relevant context for domain analysis"""
        context_parts = []
        
        # Add intent information
        context_parts.append(f"Business Intent: {intent_analysis.get('business_intent', 'Unknown')}")
        context_parts.append(f"ITIL Service Type: {intent_analysis.get('itil_service_type', 'Unknown')}")
        
        # Add technical plan information
        if technical_plan.get("steps"):
            context_parts.append(f"Technical Steps: {len(technical_plan['steps'])} steps planned")
        
        if technical_plan.get("resource_requirements"):
            context_parts.append(f"Resources: {', '.join(technical_plan['resource_requirements'])}")
        
        return " | ".join(context_parts)