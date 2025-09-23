"""
Continuous Learning System - Phase 2 Week 5 Implementation

This system implements continuous learning capabilities for the Multi-Brain Architecture:
- Execution feedback analysis
- Cross-brain learning coordination
- External knowledge integration
- Learning quality assurance
"""

from typing import Dict, List, Any, Optional, Union
import asyncio
import json
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
import logging

logger = logging.getLogger(__name__)


class LearningType(Enum):
    """Types of learning updates"""
    EXECUTION_FEEDBACK = "execution_feedback"
    PATTERN_RECOGNITION = "pattern_recognition"
    EXTERNAL_KNOWLEDGE = "external_knowledge"
    CROSS_BRAIN_INSIGHT = "cross_brain_insight"
    ERROR_CORRECTION = "error_correction"


class LearningQuality(Enum):
    """Quality levels for learning updates"""
    HIGH = "high"           # Validated, reliable learning
    MEDIUM = "medium"       # Partially validated learning
    LOW = "low"            # Unvalidated, experimental learning
    REJECTED = "rejected"   # Failed validation


@dataclass
class LearningUpdate:
    """Represents a learning update for the system"""
    update_id: str
    learning_type: LearningType
    source_brain: str
    target_brain: str
    content: Dict[str, Any]
    confidence: float
    timestamp: datetime = field(default_factory=datetime.now)
    validation_status: LearningQuality = LearningQuality.LOW
    validation_notes: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ExecutionFeedback:
    """Execution feedback data for learning"""
    execution_id: str
    user_request: str
    intent_analysis: Dict[str, Any]
    technical_plan: Dict[str, Any]
    sme_recommendations: Dict[str, Any]
    execution_result: Dict[str, Any]
    success: bool
    execution_time: float
    user_satisfaction: Optional[float] = None
    lessons_learned: List[str] = field(default_factory=list)
    improvement_suggestions: List[str] = field(default_factory=list)


class ExecutionFeedbackAnalyzer:
    """
    Analyzes execution feedback to generate learning insights
    """
    
    def __init__(self):
        self.feedback_history: List[ExecutionFeedback] = []
        self.pattern_cache: Dict[str, Any] = {}
        self.success_patterns: Dict[str, float] = {}
        self.failure_patterns: Dict[str, float] = {}
    
    async def analyze_execution_feedback(self, feedback: ExecutionFeedback) -> List[LearningUpdate]:
        """
        Analyze execution feedback to generate learning updates
        
        Args:
            feedback: Execution feedback data
            
        Returns:
            List of learning updates generated from the feedback
        """
        learning_updates = []
        
        try:
            # Store feedback
            self.feedback_history.append(feedback)
            
            # Analyze success/failure patterns
            pattern_updates = await self._analyze_patterns(feedback)
            learning_updates.extend(pattern_updates)
            
            # Analyze confidence accuracy
            confidence_updates = await self._analyze_confidence_accuracy(feedback)
            learning_updates.extend(confidence_updates)
            
            # Analyze execution time patterns
            timing_updates = await self._analyze_timing_patterns(feedback)
            learning_updates.extend(timing_updates)
            
            # Analyze SME recommendation effectiveness
            sme_updates = await self._analyze_sme_effectiveness(feedback)
            learning_updates.extend(sme_updates)
            
            # Generate improvement suggestions
            improvement_updates = await self._generate_improvement_suggestions(feedback)
            learning_updates.extend(improvement_updates)
            
            logger.info(f"Generated {len(learning_updates)} learning updates from execution feedback")
            return learning_updates
            
        except Exception as e:
            logger.error(f"Error analyzing execution feedback: {str(e)}")
            return []
    
    async def _analyze_patterns(self, feedback: ExecutionFeedback) -> List[LearningUpdate]:
        """Analyze success/failure patterns"""
        updates = []
        
        try:
            # Extract key characteristics
            intent_type = feedback.intent_analysis.get("primary_intent", "unknown")
            complexity = feedback.technical_plan.get("complexity", "unknown")
            execution_strategy = feedback.technical_plan.get("execution_strategy", "unknown")
            
            pattern_key = f"{intent_type}_{complexity}_{execution_strategy}"
            
            # Update success/failure patterns
            if feedback.success:
                self.success_patterns[pattern_key] = self.success_patterns.get(pattern_key, 0) + 1
            else:
                self.failure_patterns[pattern_key] = self.failure_patterns.get(pattern_key, 0) + 1
            
            # Generate learning update if we have enough data
            total_attempts = self.success_patterns.get(pattern_key, 0) + self.failure_patterns.get(pattern_key, 0)
            if total_attempts >= 5:  # Minimum threshold for pattern recognition
                success_rate = self.success_patterns.get(pattern_key, 0) / total_attempts
                
                update = LearningUpdate(
                    update_id=f"pattern_{pattern_key}_{datetime.now().timestamp()}",
                    learning_type=LearningType.PATTERN_RECOGNITION,
                    source_brain="execution_feedback_analyzer",
                    target_brain="technical_brain",
                    content={
                        "pattern": pattern_key,
                        "success_rate": success_rate,
                        "total_attempts": total_attempts,
                        "recommendation": "high_confidence" if success_rate > 0.8 else "review_approach" if success_rate < 0.4 else "standard_approach"
                    },
                    confidence=min(0.9, total_attempts / 20),  # Higher confidence with more data
                    metadata={
                        "intent_type": intent_type,
                        "complexity": complexity,
                        "execution_strategy": execution_strategy
                    }
                )
                updates.append(update)
            
            return updates
            
        except Exception as e:
            logger.error(f"Error analyzing patterns: {str(e)}")
            return []
    
    async def _analyze_confidence_accuracy(self, feedback: ExecutionFeedback) -> List[LearningUpdate]:
        """Analyze how accurate confidence predictions were"""
        updates = []
        
        try:
            # Extract confidence scores
            intent_confidence = feedback.intent_analysis.get("overall_confidence", 0.5)
            technical_confidence = feedback.technical_plan.get("confidence_score", 0.5)
            
            # Calculate confidence accuracy
            predicted_success = (intent_confidence + technical_confidence) / 2
            actual_success = 1.0 if feedback.success else 0.0
            
            confidence_error = abs(predicted_success - actual_success)
            
            # Generate learning update for confidence calibration
            if confidence_error > 0.3:  # Significant confidence error
                update = LearningUpdate(
                    update_id=f"confidence_calibration_{datetime.now().timestamp()}",
                    learning_type=LearningType.ERROR_CORRECTION,
                    source_brain="execution_feedback_analyzer",
                    target_brain="all_brains",
                    content={
                        "confidence_error": confidence_error,
                        "predicted_success": predicted_success,
                        "actual_success": actual_success,
                        "calibration_adjustment": -0.1 if predicted_success > actual_success else 0.1,
                        "context": {
                            "intent_type": feedback.intent_analysis.get("primary_intent"),
                            "complexity": feedback.technical_plan.get("complexity")
                        }
                    },
                    confidence=0.7,
                    metadata={
                        "confidence_error": confidence_error,
                        "execution_id": feedback.execution_id
                    }
                )
                updates.append(update)
            
            return updates
            
        except Exception as e:
            logger.error(f"Error analyzing confidence accuracy: {str(e)}")
            return []
    
    async def _analyze_timing_patterns(self, feedback: ExecutionFeedback) -> List[LearningUpdate]:
        """Analyze execution timing patterns"""
        updates = []
        
        try:
            estimated_time = feedback.technical_plan.get("estimated_duration", 0)
            actual_time = feedback.execution_time
            
            if estimated_time > 0:
                timing_error = abs(actual_time - estimated_time) / estimated_time
                
                # Generate learning update for timing estimation
                if timing_error > 0.5:  # Significant timing error
                    update = LearningUpdate(
                        update_id=f"timing_estimation_{datetime.now().timestamp()}",
                        learning_type=LearningType.EXECUTION_FEEDBACK,
                        source_brain="execution_feedback_analyzer",
                        target_brain="technical_brain",
                        content={
                            "timing_error": timing_error,
                            "estimated_time": estimated_time,
                            "actual_time": actual_time,
                            "adjustment_factor": actual_time / estimated_time,
                            "operation_type": feedback.technical_plan.get("operation_type", "unknown")
                        },
                        confidence=0.8,
                        metadata={
                            "timing_error": timing_error,
                            "execution_id": feedback.execution_id
                        }
                    )
                    updates.append(update)
            
            return updates
            
        except Exception as e:
            logger.error(f"Error analyzing timing patterns: {str(e)}")
            return []
    
    async def _analyze_sme_effectiveness(self, feedback: ExecutionFeedback) -> List[LearningUpdate]:
        """Analyze SME recommendation effectiveness"""
        updates = []
        
        try:
            for sme_domain, recommendations in feedback.sme_recommendations.items():
                if isinstance(recommendations, dict) and "recommendations" in recommendations:
                    sme_confidence = recommendations.get("confidence", {}).get("score", 0.5)
                    
                    # Analyze if SME recommendations were helpful
                    effectiveness_score = 0.8 if feedback.success else 0.3
                    
                    update = LearningUpdate(
                        update_id=f"sme_effectiveness_{sme_domain}_{datetime.now().timestamp()}",
                        learning_type=LearningType.EXECUTION_FEEDBACK,
                        source_brain="execution_feedback_analyzer",
                        target_brain=f"sme_{sme_domain}",
                        content={
                            "effectiveness_score": effectiveness_score,
                            "sme_confidence": sme_confidence,
                            "execution_success": feedback.success,
                            "recommendation_count": len(recommendations.get("recommendations", [])),
                            "domain": sme_domain
                        },
                        confidence=0.6,
                        metadata={
                            "sme_domain": sme_domain,
                            "execution_id": feedback.execution_id
                        }
                    )
                    updates.append(update)
            
            return updates
            
        except Exception as e:
            logger.error(f"Error analyzing SME effectiveness: {str(e)}")
            return []
    
    async def _generate_improvement_suggestions(self, feedback: ExecutionFeedback) -> List[LearningUpdate]:
        """Generate improvement suggestions based on feedback"""
        updates = []
        
        try:
            if not feedback.success:
                # Analyze failure reasons and suggest improvements
                error_info = feedback.execution_result.get("error", "Unknown error")
                
                improvement_suggestions = []
                
                # Common improvement patterns
                if "timeout" in error_info.lower():
                    improvement_suggestions.append("Increase timeout values for similar operations")
                elif "permission" in error_info.lower():
                    improvement_suggestions.append("Add permission validation to pre-execution checks")
                elif "resource" in error_info.lower():
                    improvement_suggestions.append("Implement resource availability checks")
                elif "network" in error_info.lower():
                    improvement_suggestions.append("Add network connectivity validation")
                
                if improvement_suggestions:
                    update = LearningUpdate(
                        update_id=f"improvement_suggestion_{datetime.now().timestamp()}",
                        learning_type=LearningType.ERROR_CORRECTION,
                        source_brain="execution_feedback_analyzer",
                        target_brain="technical_brain",
                        content={
                            "error_type": error_info,
                            "improvement_suggestions": improvement_suggestions,
                            "failure_context": {
                                "intent": feedback.intent_analysis.get("primary_intent"),
                                "complexity": feedback.technical_plan.get("complexity")
                            }
                        },
                        confidence=0.7,
                        metadata={
                            "error_info": error_info,
                            "execution_id": feedback.execution_id
                        }
                    )
                    updates.append(update)
            
            return updates
            
        except Exception as e:
            logger.error(f"Error generating improvement suggestions: {str(e)}")
            return []


class CrossBrainLearner:
    """
    Coordinates learning across different brain components
    """
    
    def __init__(self):
        self.cross_brain_insights: Dict[str, List[LearningUpdate]] = {}
        self.brain_performance_metrics: Dict[str, Dict[str, float]] = {}
    
    async def coordinate_cross_brain_learning(self, learning_updates: List[LearningUpdate]) -> List[LearningUpdate]:
        """
        Coordinate learning across brain components
        
        Args:
            learning_updates: Learning updates from various sources
            
        Returns:
            Cross-brain learning insights
        """
        cross_brain_updates = []
        
        try:
            # Group updates by target brain
            brain_updates = {}
            for update in learning_updates:
                if update.target_brain not in brain_updates:
                    brain_updates[update.target_brain] = []
                brain_updates[update.target_brain].append(update)
            
            # Identify cross-brain patterns
            pattern_updates = await self._identify_cross_brain_patterns(brain_updates)
            cross_brain_updates.extend(pattern_updates)
            
            # Generate brain collaboration insights
            collaboration_updates = await self._generate_collaboration_insights(brain_updates)
            cross_brain_updates.extend(collaboration_updates)
            
            # Optimize brain coordination
            coordination_updates = await self._optimize_brain_coordination(brain_updates)
            cross_brain_updates.extend(coordination_updates)
            
            logger.info(f"Generated {len(cross_brain_updates)} cross-brain learning updates")
            return cross_brain_updates
            
        except Exception as e:
            logger.error(f"Error in cross-brain learning coordination: {str(e)}")
            return []
    
    async def _identify_cross_brain_patterns(self, brain_updates: Dict[str, List[LearningUpdate]]) -> List[LearningUpdate]:
        """Identify patterns across different brains"""
        updates = []
        
        try:
            # Look for patterns where multiple brains have similar learning updates
            for brain1, updates1 in brain_updates.items():
                for brain2, updates2 in brain_updates.items():
                    if brain1 != brain2:
                        # Find similar learning patterns
                        similar_patterns = await self._find_similar_patterns(updates1, updates2)
                        
                        for pattern in similar_patterns:
                            update = LearningUpdate(
                                update_id=f"cross_brain_pattern_{brain1}_{brain2}_{datetime.now().timestamp()}",
                                learning_type=LearningType.CROSS_BRAIN_INSIGHT,
                                source_brain="cross_brain_learner",
                                target_brain="all_brains",
                                content={
                                    "pattern_type": pattern["type"],
                                    "involved_brains": [brain1, brain2],
                                    "pattern_details": pattern["details"],
                                    "coordination_suggestion": pattern["suggestion"]
                                },
                                confidence=pattern["confidence"],
                                metadata={
                                    "brain1": brain1,
                                    "brain2": brain2,
                                    "pattern_strength": pattern["strength"]
                                }
                            )
                            updates.append(update)
            
            return updates
            
        except Exception as e:
            logger.error(f"Error identifying cross-brain patterns: {str(e)}")
            return []
    
    async def _find_similar_patterns(self, updates1: List[LearningUpdate], updates2: List[LearningUpdate]) -> List[Dict[str, Any]]:
        """Find similar patterns between two sets of learning updates"""
        patterns = []
        
        try:
            # Look for similar learning types and content
            for update1 in updates1:
                for update2 in updates2:
                    if update1.learning_type == update2.learning_type:
                        # Calculate similarity
                        similarity = await self._calculate_content_similarity(update1.content, update2.content)
                        
                        if similarity > 0.7:  # High similarity threshold
                            pattern = {
                                "type": update1.learning_type.value,
                                "details": {
                                    "update1_content": update1.content,
                                    "update2_content": update2.content,
                                    "similarity_score": similarity
                                },
                                "suggestion": f"Coordinate {update1.learning_type.value} learning between brains",
                                "confidence": similarity * 0.8,
                                "strength": similarity
                            }
                            patterns.append(pattern)
            
            return patterns
            
        except Exception as e:
            logger.error(f"Error finding similar patterns: {str(e)}")
            return []
    
    async def _calculate_content_similarity(self, content1: Dict[str, Any], content2: Dict[str, Any]) -> float:
        """Calculate similarity between two content dictionaries"""
        try:
            # Simple similarity calculation based on common keys and values
            common_keys = set(content1.keys()) & set(content2.keys())
            total_keys = set(content1.keys()) | set(content2.keys())
            
            if not total_keys:
                return 0.0
            
            key_similarity = len(common_keys) / len(total_keys)
            
            # Check value similarity for common keys
            value_similarity = 0.0
            if common_keys:
                matching_values = 0
                for key in common_keys:
                    if content1[key] == content2[key]:
                        matching_values += 1
                value_similarity = matching_values / len(common_keys)
            
            return (key_similarity + value_similarity) / 2
            
        except Exception as e:
            logger.error(f"Error calculating content similarity: {str(e)}")
            return 0.0
    
    async def _generate_collaboration_insights(self, brain_updates: Dict[str, List[LearningUpdate]]) -> List[LearningUpdate]:
        """Generate insights for better brain collaboration"""
        updates = []
        
        try:
            # Analyze which brains are learning similar things
            collaboration_opportunities = []
            
            for brain, brain_updates_list in brain_updates.items():
                if len(brain_updates_list) > 3:  # Brain with significant learning activity
                    collaboration_opportunities.append({
                        "brain": brain,
                        "learning_activity": len(brain_updates_list),
                        "learning_types": [update.learning_type.value for update in brain_updates_list]
                    })
            
            if len(collaboration_opportunities) > 1:
                update = LearningUpdate(
                    update_id=f"collaboration_insight_{datetime.now().timestamp()}",
                    learning_type=LearningType.CROSS_BRAIN_INSIGHT,
                    source_brain="cross_brain_learner",
                    target_brain="communication_protocol",
                    content={
                        "collaboration_opportunities": collaboration_opportunities,
                        "suggestion": "Increase communication frequency between active learning brains",
                        "coordination_strategy": "shared_learning_sessions"
                    },
                    confidence=0.8,
                    metadata={
                        "active_brains": len(collaboration_opportunities),
                        "total_learning_updates": sum(len(updates) for updates in brain_updates.values())
                    }
                )
                updates.append(update)
            
            return updates
            
        except Exception as e:
            logger.error(f"Error generating collaboration insights: {str(e)}")
            return []
    
    async def _optimize_brain_coordination(self, brain_updates: Dict[str, List[LearningUpdate]]) -> List[LearningUpdate]:
        """Optimize coordination between brains"""
        updates = []
        
        try:
            # Analyze coordination efficiency
            coordination_metrics = {}
            
            for brain, brain_updates_list in brain_updates.items():
                error_corrections = [u for u in brain_updates_list if u.learning_type == LearningType.ERROR_CORRECTION]
                pattern_recognitions = [u for u in brain_updates_list if u.learning_type == LearningType.PATTERN_RECOGNITION]
                
                coordination_metrics[brain] = {
                    "error_rate": len(error_corrections) / max(1, len(brain_updates_list)),
                    "pattern_recognition_rate": len(pattern_recognitions) / max(1, len(brain_updates_list)),
                    "total_updates": len(brain_updates_list)
                }
            
            # Generate optimization suggestions
            high_error_brains = [brain for brain, metrics in coordination_metrics.items() 
                               if metrics["error_rate"] > 0.3]
            
            if high_error_brains:
                update = LearningUpdate(
                    update_id=f"coordination_optimization_{datetime.now().timestamp()}",
                    learning_type=LearningType.CROSS_BRAIN_INSIGHT,
                    source_brain="cross_brain_learner",
                    target_brain="communication_protocol",
                    content={
                        "high_error_brains": high_error_brains,
                        "optimization_suggestion": "Increase validation and cross-checking for high-error brains",
                        "coordination_metrics": coordination_metrics
                    },
                    confidence=0.7,
                    metadata={
                        "optimization_type": "error_reduction",
                        "affected_brains": high_error_brains
                    }
                )
                updates.append(update)
            
            return updates
            
        except Exception as e:
            logger.error(f"Error optimizing brain coordination: {str(e)}")
            return []


class ExternalKnowledgeIntegrator:
    """
    Integrates external knowledge sources into the learning system
    """
    
    def __init__(self):
        self.knowledge_sources: Dict[str, Dict[str, Any]] = {}
        self.integration_history: List[Dict[str, Any]] = []
    
    async def integrate_external_knowledge(self, knowledge_source: str, knowledge_data: Dict[str, Any]) -> List[LearningUpdate]:
        """
        Integrate external knowledge into the system
        
        Args:
            knowledge_source: Source of the knowledge (e.g., "documentation", "best_practices")
            knowledge_data: The knowledge data to integrate
            
        Returns:
            Learning updates generated from external knowledge
        """
        updates = []
        
        try:
            # Validate knowledge data
            if not await self._validate_external_knowledge(knowledge_data):
                logger.warning(f"External knowledge validation failed for source: {knowledge_source}")
                return []
            
            # Process different types of external knowledge
            if knowledge_source == "best_practices":
                updates.extend(await self._integrate_best_practices(knowledge_data))
            elif knowledge_source == "documentation":
                updates.extend(await self._integrate_documentation(knowledge_data))
            elif knowledge_source == "industry_standards":
                updates.extend(await self._integrate_industry_standards(knowledge_data))
            elif knowledge_source == "security_advisories":
                updates.extend(await self._integrate_security_advisories(knowledge_data))
            
            # Store integration history
            self.integration_history.append({
                "source": knowledge_source,
                "timestamp": datetime.now(),
                "updates_generated": len(updates),
                "data_summary": self._summarize_knowledge_data(knowledge_data)
            })
            
            logger.info(f"Integrated external knowledge from {knowledge_source}, generated {len(updates)} updates")
            return updates
            
        except Exception as e:
            logger.error(f"Error integrating external knowledge: {str(e)}")
            return []
    
    async def _validate_external_knowledge(self, knowledge_data: Dict[str, Any]) -> bool:
        """Validate external knowledge data"""
        try:
            # Basic validation checks
            required_fields = ["content", "source", "reliability"]
            
            for field in required_fields:
                if field not in knowledge_data:
                    return False
            
            # Check reliability score
            reliability = knowledge_data.get("reliability", 0)
            if reliability < 0.5:  # Minimum reliability threshold
                return False
            
            return True
            
        except Exception as e:
            logger.error(f"Error validating external knowledge: {str(e)}")
            return False
    
    async def _integrate_best_practices(self, knowledge_data: Dict[str, Any]) -> List[LearningUpdate]:
        """Integrate best practices knowledge"""
        updates = []
        
        try:
            practices = knowledge_data.get("content", {}).get("practices", [])
            
            for practice in practices:
                update = LearningUpdate(
                    update_id=f"best_practice_{datetime.now().timestamp()}",
                    learning_type=LearningType.EXTERNAL_KNOWLEDGE,
                    source_brain="external_knowledge_integrator",
                    target_brain=practice.get("target_domain", "all_brains"),
                    content={
                        "practice_type": "best_practice",
                        "practice_description": practice.get("description", ""),
                        "implementation_guidance": practice.get("implementation", ""),
                        "benefits": practice.get("benefits", []),
                        "applicability": practice.get("applicability", "general")
                    },
                    confidence=knowledge_data.get("reliability", 0.7),
                    metadata={
                        "source": knowledge_data.get("source", "unknown"),
                        "practice_category": practice.get("category", "general")
                    }
                )
                updates.append(update)
            
            return updates
            
        except Exception as e:
            logger.error(f"Error integrating best practices: {str(e)}")
            return []
    
    async def _integrate_documentation(self, knowledge_data: Dict[str, Any]) -> List[LearningUpdate]:
        """Integrate documentation knowledge"""
        updates = []
        
        try:
            docs = knowledge_data.get("content", {}).get("documentation", [])
            
            for doc in docs:
                update = LearningUpdate(
                    update_id=f"documentation_{datetime.now().timestamp()}",
                    learning_type=LearningType.EXTERNAL_KNOWLEDGE,
                    source_brain="external_knowledge_integrator",
                    target_brain=doc.get("target_domain", "all_brains"),
                    content={
                        "knowledge_type": "documentation",
                        "topic": doc.get("topic", ""),
                        "content_summary": doc.get("summary", ""),
                        "key_points": doc.get("key_points", []),
                        "examples": doc.get("examples", [])
                    },
                    confidence=knowledge_data.get("reliability", 0.6),
                    metadata={
                        "source": knowledge_data.get("source", "unknown"),
                        "doc_type": doc.get("type", "general")
                    }
                )
                updates.append(update)
            
            return updates
            
        except Exception as e:
            logger.error(f"Error integrating documentation: {str(e)}")
            return []
    
    async def _integrate_industry_standards(self, knowledge_data: Dict[str, Any]) -> List[LearningUpdate]:
        """Integrate industry standards knowledge"""
        updates = []
        
        try:
            standards = knowledge_data.get("content", {}).get("standards", [])
            
            for standard in standards:
                update = LearningUpdate(
                    update_id=f"industry_standard_{datetime.now().timestamp()}",
                    learning_type=LearningType.EXTERNAL_KNOWLEDGE,
                    source_brain="external_knowledge_integrator",
                    target_brain="security_and_compliance",  # Standards often relate to compliance
                    content={
                        "knowledge_type": "industry_standard",
                        "standard_name": standard.get("name", ""),
                        "requirements": standard.get("requirements", []),
                        "compliance_guidelines": standard.get("guidelines", []),
                        "validation_criteria": standard.get("validation", [])
                    },
                    confidence=knowledge_data.get("reliability", 0.8),
                    metadata={
                        "source": knowledge_data.get("source", "unknown"),
                        "standard_type": standard.get("type", "general")
                    }
                )
                updates.append(update)
            
            return updates
            
        except Exception as e:
            logger.error(f"Error integrating industry standards: {str(e)}")
            return []
    
    async def _integrate_security_advisories(self, knowledge_data: Dict[str, Any]) -> List[LearningUpdate]:
        """Integrate security advisories knowledge"""
        updates = []
        
        try:
            advisories = knowledge_data.get("content", {}).get("advisories", [])
            
            for advisory in advisories:
                update = LearningUpdate(
                    update_id=f"security_advisory_{datetime.now().timestamp()}",
                    learning_type=LearningType.EXTERNAL_KNOWLEDGE,
                    source_brain="external_knowledge_integrator",
                    target_brain="security_and_compliance",
                    content={
                        "knowledge_type": "security_advisory",
                        "vulnerability_description": advisory.get("description", ""),
                        "affected_systems": advisory.get("affected_systems", []),
                        "mitigation_steps": advisory.get("mitigation", []),
                        "severity": advisory.get("severity", "medium")
                    },
                    confidence=knowledge_data.get("reliability", 0.9),
                    metadata={
                        "source": knowledge_data.get("source", "unknown"),
                        "advisory_id": advisory.get("id", "unknown"),
                        "severity": advisory.get("severity", "medium")
                    }
                )
                updates.append(update)
            
            return updates
            
        except Exception as e:
            logger.error(f"Error integrating security advisories: {str(e)}")
            return []
    
    def _summarize_knowledge_data(self, knowledge_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a summary of knowledge data for history tracking"""
        try:
            return {
                "source": knowledge_data.get("source", "unknown"),
                "reliability": knowledge_data.get("reliability", 0.0),
                "content_type": list(knowledge_data.get("content", {}).keys()),
                "data_size": len(str(knowledge_data))
            }
        except Exception as e:
            logger.error(f"Error summarizing knowledge data: {str(e)}")
            return {"error": str(e)}


class ContinuousLearningSystem:
    """
    Main continuous learning system that coordinates all learning components
    """
    
    def __init__(self):
        self.execution_feedback_analyzer = ExecutionFeedbackAnalyzer()
        self.cross_brain_learner = CrossBrainLearner()
        self.external_knowledge_integrator = ExternalKnowledgeIntegrator()
        self.learning_quality_assurance = None  # Will be initialized separately
        
        self.learning_history: List[LearningUpdate] = []
        self.system_metrics = {
            "total_learning_updates": 0,
            "successful_integrations": 0,
            "failed_integrations": 0,
            "average_learning_quality": 0.0
        }
    
    async def initialize(self, quality_assurance_system):
        """Initialize the continuous learning system"""
        self.learning_quality_assurance = quality_assurance_system
        logger.info("Continuous Learning System initialized")
    
    async def process_execution_feedback(self, feedback: ExecutionFeedback) -> List[LearningUpdate]:
        """
        Process execution feedback through the learning pipeline
        
        Args:
            feedback: Execution feedback data
            
        Returns:
            Validated learning updates
        """
        try:
            # Analyze execution feedback
            feedback_updates = await self.execution_feedback_analyzer.analyze_execution_feedback(feedback)
            
            # Coordinate cross-brain learning
            cross_brain_updates = await self.cross_brain_learner.coordinate_cross_brain_learning(feedback_updates)
            
            # Combine all updates
            all_updates = feedback_updates + cross_brain_updates
            
            # Validate learning updates
            validated_updates = []
            if self.learning_quality_assurance:
                for update in all_updates:
                    validation_result = await self.learning_quality_assurance.validate_learning_update(update)
                    if validation_result.is_valid:
                        update.validation_status = validation_result.quality_level
                        update.validation_notes = validation_result.notes
                        validated_updates.append(update)
                        self.system_metrics["successful_integrations"] += 1
                    else:
                        self.system_metrics["failed_integrations"] += 1
            else:
                validated_updates = all_updates
            
            # Store learning history
            self.learning_history.extend(validated_updates)
            self.system_metrics["total_learning_updates"] += len(validated_updates)
            
            # Update average quality
            if validated_updates:
                quality_scores = [self._quality_to_score(update.validation_status) for update in validated_updates]
                avg_quality = sum(quality_scores) / len(quality_scores)
                
                total_updates = self.system_metrics["total_learning_updates"]
                current_avg = self.system_metrics["average_learning_quality"]
                self.system_metrics["average_learning_quality"] = (
                    (current_avg * (total_updates - len(validated_updates)) + avg_quality * len(validated_updates)) / total_updates
                )
            
            logger.info(f"Processed execution feedback, generated {len(validated_updates)} validated learning updates")
            return validated_updates
            
        except Exception as e:
            logger.error(f"Error processing execution feedback: {str(e)}")
            return []
    
    async def integrate_external_knowledge(self, knowledge_source: str, knowledge_data: Dict[str, Any]) -> List[LearningUpdate]:
        """
        Integrate external knowledge through the learning pipeline
        
        Args:
            knowledge_source: Source of the knowledge
            knowledge_data: The knowledge data
            
        Returns:
            Validated learning updates
        """
        try:
            # Integrate external knowledge
            knowledge_updates = await self.external_knowledge_integrator.integrate_external_knowledge(
                knowledge_source, knowledge_data
            )
            
            # Validate learning updates
            validated_updates = []
            if self.learning_quality_assurance:
                for update in knowledge_updates:
                    validation_result = await self.learning_quality_assurance.validate_learning_update(update)
                    if validation_result.is_valid:
                        update.validation_status = validation_result.quality_level
                        update.validation_notes = validation_result.notes
                        validated_updates.append(update)
                        self.system_metrics["successful_integrations"] += 1
                    else:
                        self.system_metrics["failed_integrations"] += 1
            else:
                validated_updates = knowledge_updates
            
            # Store learning history
            self.learning_history.extend(validated_updates)
            self.system_metrics["total_learning_updates"] += len(validated_updates)
            
            logger.info(f"Integrated external knowledge from {knowledge_source}, generated {len(validated_updates)} validated updates")
            return validated_updates
            
        except Exception as e:
            logger.error(f"Error integrating external knowledge: {str(e)}")
            return []
    
    def _quality_to_score(self, quality: LearningQuality) -> float:
        """Convert learning quality to numeric score"""
        quality_scores = {
            LearningQuality.HIGH: 1.0,
            LearningQuality.MEDIUM: 0.7,
            LearningQuality.LOW: 0.4,
            LearningQuality.REJECTED: 0.0
        }
        return quality_scores.get(quality, 0.5)
    
    async def get_learning_metrics(self) -> Dict[str, Any]:
        """Get learning system metrics"""
        return {
            "system_metrics": self.system_metrics,
            "learning_history_size": len(self.learning_history),
            "recent_learning_activity": len([u for u in self.learning_history 
                                           if (datetime.now() - u.timestamp).days < 7]),
            "quality_distribution": self._get_quality_distribution()
        }
    
    def _get_quality_distribution(self) -> Dict[str, int]:
        """Get distribution of learning quality levels"""
        distribution = {quality.value: 0 for quality in LearningQuality}
        
        for update in self.learning_history:
            distribution[update.validation_status.value] += 1
        
        return distribution
    
    async def get_recent_learning_updates(self, limit: int = 50) -> List[Dict[str, Any]]:
        """Get recent learning updates"""
        try:
            recent_updates = sorted(self.learning_history, key=lambda x: x.timestamp, reverse=True)[:limit]
            return [
                {
                    "update_id": update.update_id,
                    "learning_type": update.learning_type.value,
                    "source_brain": update.source_brain,
                    "target_brain": update.target_brain,
                    "confidence": update.confidence,
                    "validation_status": update.validation_status.value,
                    "timestamp": update.timestamp.isoformat(),
                    "content_summary": str(update.content)[:200] + "..." if len(str(update.content)) > 200 else str(update.content)
                }
                for update in recent_updates
            ]
        except Exception as e:
            logger.error(f"Error getting recent learning updates: {str(e)}")
            return []