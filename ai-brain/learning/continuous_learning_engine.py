"""
Continuous Learning Engine

Core learning engine that coordinates learning across all brain components,
processes feedback, and maintains learning quality assurance.
"""

import logging
from typing import Dict, Any, List, Optional
from dataclasses import dataclass
from datetime import datetime, timedelta
from enum import Enum
import asyncio
import json

logger = logging.getLogger(__name__)

class LearningType(Enum):
    """Types of learning events"""
    EXECUTION_FEEDBACK = "execution_feedback"
    CROSS_BRAIN_SHARING = "cross_brain_sharing"
    EXTERNAL_KNOWLEDGE = "external_knowledge"
    PATTERN_RECOGNITION = "pattern_recognition"
    ERROR_CORRECTION = "error_correction"

class LearningQuality(Enum):
    """Learning quality levels"""
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    REJECTED = "rejected"

@dataclass
class LearningEvent:
    """Learning event data structure"""
    event_id: str
    learning_type: LearningType
    source_brain: str
    target_brain: str
    timestamp: datetime
    data: Dict[str, Any]
    quality_score: float
    validation_status: str
    impact_metrics: Dict[str, float]

@dataclass
class LearningMetrics:
    """Learning system metrics"""
    total_events: int
    successful_learnings: int
    rejected_learnings: int
    average_quality_score: float
    learning_rate: float
    improvement_metrics: Dict[str, float]

class ContinuousLearningEngine:
    """
    Continuous Learning Engine for Multi-Brain AI Architecture
    
    This engine coordinates learning across all brain components:
    1. Processes execution feedback from completed operations
    2. Facilitates cross-brain knowledge sharing
    3. Integrates external knowledge sources
    4. Maintains learning quality assurance
    5. Tracks learning effectiveness and metrics
    """
    
    def __init__(self, vector_store=None, llm_engine=None):
        """
        Initialize the continuous learning engine.
        
        Args:
            vector_store: Vector database for knowledge storage
            llm_engine: LLM engine for knowledge processing
        """
        self.engine_id = "continuous_learning_engine"
        self.version = "1.0.0"
        self.vector_store = vector_store
        self.llm_engine = llm_engine
        
        # Learning configuration
        self.learning_enabled = True
        self.quality_threshold = 0.7
        self.max_learning_events_per_hour = 100
        self.learning_retention_days = 30
        
        # Learning storage
        self.learning_events: List[LearningEvent] = []
        self.learning_patterns: Dict[str, Any] = {}
        self.brain_knowledge_bases: Dict[str, Dict] = {}
        
        # Quality assurance
        self.validation_rules = self._initialize_validation_rules()
        self.learning_metrics = LearningMetrics(0, 0, 0, 0.0, 0.0, {})
        
        logger.info(f"Continuous Learning Engine v{self.version} initialized")
    
    def _initialize_validation_rules(self) -> Dict[str, Any]:
        """Initialize learning validation rules."""
        return {
            "min_confidence_threshold": 0.6,
            "max_error_rate": 0.1,
            "required_validation_samples": 3,
            "cross_validation_required": True,
            "external_source_verification": True
        }
    
    async def process_execution_feedback(self, execution_result: Dict[str, Any],
                                       source_brain: str) -> bool:
        """
        Process execution feedback for learning.
        
        Args:
            execution_result: Results from executed operations
            source_brain: Brain that generated the execution
            
        Returns:
            bool: True if learning was successful
        """
        try:
            logger.info(f"Processing execution feedback from {source_brain}")
            
            # Extract learning data from execution result
            learning_data = self._extract_learning_data(execution_result)
            
            if not learning_data:
                logger.debug("No learning data extracted from execution result")
                return False
            
            # Create learning event
            event = LearningEvent(
                event_id=f"exec_{int(datetime.now().timestamp())}",
                learning_type=LearningType.EXECUTION_FEEDBACK,
                source_brain=source_brain,
                target_brain=source_brain,  # Self-learning
                timestamp=datetime.now(),
                data=learning_data,
                quality_score=0.0,  # Will be calculated
                validation_status="pending",
                impact_metrics={}
            )
            
            # Validate and score the learning
            if await self._validate_learning_event(event):
                await self._apply_learning(event)
                self.learning_events.append(event)
                self._update_metrics(event, success=True)
                logger.info(f"Execution feedback learning applied successfully")
                return True
            else:
                self._update_metrics(event, success=False)
                logger.warning(f"Execution feedback learning validation failed")
                return False
                
        except Exception as e:
            logger.error(f"Error processing execution feedback: {e}")
            return False
    
    async def facilitate_cross_brain_learning(self, source_brain: str,
                                            target_brain: str,
                                            knowledge_data: Dict[str, Any]) -> bool:
        """
        Facilitate knowledge sharing between brains.
        
        Args:
            source_brain: Brain sharing knowledge
            target_brain: Brain receiving knowledge
            knowledge_data: Knowledge to be shared
            
        Returns:
            bool: True if cross-brain learning was successful
        """
        try:
            logger.info(f"Facilitating cross-brain learning: {source_brain} -> {target_brain}")
            
            # Create cross-brain learning event
            event = LearningEvent(
                event_id=f"cross_{int(datetime.now().timestamp())}",
                learning_type=LearningType.CROSS_BRAIN_SHARING,
                source_brain=source_brain,
                target_brain=target_brain,
                timestamp=datetime.now(),
                data=knowledge_data,
                quality_score=0.0,
                validation_status="pending",
                impact_metrics={}
            )
            
            # Validate cross-brain compatibility
            if await self._validate_cross_brain_compatibility(event):
                await self._apply_cross_brain_learning(event)
                self.learning_events.append(event)
                self._update_metrics(event, success=True)
                logger.info(f"Cross-brain learning applied successfully")
                return True
            else:
                self._update_metrics(event, success=False)
                logger.warning(f"Cross-brain learning validation failed")
                return False
                
        except Exception as e:
            logger.error(f"Error in cross-brain learning: {e}")
            return False
    
    async def integrate_external_knowledge(self, knowledge_source: str,
                                         knowledge_data: Dict[str, Any],
                                         target_brains: List[str]) -> bool:
        """
        Integrate external knowledge into specified brains.
        
        Args:
            knowledge_source: Source of external knowledge
            knowledge_data: External knowledge data
            target_brains: List of brains to receive the knowledge
            
        Returns:
            bool: True if external knowledge integration was successful
        """
        try:
            logger.info(f"Integrating external knowledge from {knowledge_source}")
            
            success_count = 0
            for target_brain in target_brains:
                event = LearningEvent(
                    event_id=f"ext_{int(datetime.now().timestamp())}_{target_brain}",
                    learning_type=LearningType.EXTERNAL_KNOWLEDGE,
                    source_brain=knowledge_source,
                    target_brain=target_brain,
                    timestamp=datetime.now(),
                    data=knowledge_data,
                    quality_score=0.0,
                    validation_status="pending",
                    impact_metrics={}
                )
                
                if await self._validate_external_knowledge(event):
                    await self._apply_external_learning(event)
                    self.learning_events.append(event)
                    self._update_metrics(event, success=True)
                    success_count += 1
                else:
                    self._update_metrics(event, success=False)
            
            logger.info(f"External knowledge integrated into {success_count}/{len(target_brains)} brains")
            return success_count > 0
            
        except Exception as e:
            logger.error(f"Error integrating external knowledge: {e}")
            return False
    
    def _extract_learning_data(self, execution_result: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Extract learning data from execution results."""
        learning_data = {}
        
        # Extract success/failure patterns
        if "success" in execution_result:
            learning_data["execution_success"] = execution_result["success"]
        
        # Extract performance metrics
        if "execution_time" in execution_result:
            learning_data["performance_metrics"] = {
                "execution_time": execution_result["execution_time"]
            }
        
        # Extract error patterns
        if "error" in execution_result and execution_result["error"]:
            learning_data["error_patterns"] = {
                "error_type": execution_result.get("error_type", "unknown"),
                "error_message": execution_result["error"]
            }
        
        # Extract confidence correlation
        if "confidence" in execution_result and "success" in execution_result:
            learning_data["confidence_correlation"] = {
                "predicted_confidence": execution_result["confidence"],
                "actual_success": execution_result["success"]
            }
        
        # Extract user feedback if available
        if "user_feedback" in execution_result:
            learning_data["user_feedback"] = execution_result["user_feedback"]
        
        return learning_data if learning_data else None
    
    async def _validate_learning_event(self, event: LearningEvent) -> bool:
        """Validate a learning event for quality and safety."""
        try:
            # Calculate quality score
            quality_score = await self._calculate_quality_score(event)
            event.quality_score = quality_score
            
            # Check quality threshold
            if quality_score < self.quality_threshold:
                event.validation_status = "rejected_low_quality"
                return False
            
            # Validate data integrity
            if not self._validate_data_integrity(event.data):
                event.validation_status = "rejected_data_integrity"
                return False
            
            # Check for conflicting patterns
            if await self._check_pattern_conflicts(event):
                event.validation_status = "rejected_pattern_conflict"
                return False
            
            event.validation_status = "validated"
            return True
            
        except Exception as e:
            logger.error(f"Error validating learning event: {e}")
            event.validation_status = f"validation_error: {str(e)}"
            return False
    
    async def _calculate_quality_score(self, event: LearningEvent) -> float:
        """Calculate quality score for a learning event."""
        score = 0.0
        
        # Base score from data completeness
        data_completeness = len(event.data) / 10.0  # Normalize to 0-1
        score += min(data_completeness, 0.3)
        
        # Score from confidence correlation (if available)
        if "confidence_correlation" in event.data:
            correlation_data = event.data["confidence_correlation"]
            predicted = correlation_data.get("predicted_confidence", 0.5)
            actual = 1.0 if correlation_data.get("actual_success", False) else 0.0
            correlation_accuracy = 1.0 - abs(predicted - actual)
            score += correlation_accuracy * 0.4
        
        # Score from execution success
        if "execution_success" in event.data:
            if event.data["execution_success"]:
                score += 0.2
        
        # Score from user feedback (if available)
        if "user_feedback" in event.data:
            feedback = event.data["user_feedback"]
            if isinstance(feedback, dict) and "rating" in feedback:
                rating = feedback["rating"]
                if isinstance(rating, (int, float)) and 1 <= rating <= 5:
                    score += (rating / 5.0) * 0.1
        
        return min(score, 1.0)
    
    def _validate_data_integrity(self, data: Dict[str, Any]) -> bool:
        """Validate data integrity for learning."""
        try:
            # Check for required fields based on learning type
            if not isinstance(data, dict):
                return False
            
            # Validate data types
            for key, value in data.items():
                if not isinstance(key, str):
                    return False
                # Allow various value types but ensure they're serializable
                try:
                    json.dumps(value)
                except (TypeError, ValueError):
                    return False
            
            return True
            
        except Exception:
            return False
    
    async def _check_pattern_conflicts(self, event: LearningEvent) -> bool:
        """Check for conflicting patterns in existing knowledge."""
        try:
            # This is a simplified conflict detection
            # In a full implementation, this would check against existing patterns
            # and identify contradictions or conflicts
            
            brain_knowledge = self.brain_knowledge_bases.get(event.target_brain, {})
            
            # Check for direct contradictions
            if "error_patterns" in event.data and "error_patterns" in brain_knowledge:
                # Simple conflict check - in reality this would be more sophisticated
                existing_errors = brain_knowledge["error_patterns"]
                new_errors = event.data["error_patterns"]
                
                # Check if we're learning contradictory error patterns
                if (existing_errors.get("error_type") == new_errors.get("error_type") and
                    existing_errors.get("resolution") != new_errors.get("resolution")):
                    return True  # Conflict detected
            
            return False  # No conflicts
            
        except Exception as e:
            logger.warning(f"Error checking pattern conflicts: {e}")
            return False
    
    async def _validate_cross_brain_compatibility(self, event: LearningEvent) -> bool:
        """Validate compatibility for cross-brain learning."""
        # Check if knowledge is applicable to target brain
        source_capabilities = self._get_brain_capabilities(event.source_brain)
        target_capabilities = self._get_brain_capabilities(event.target_brain)
        
        # Simple compatibility check
        if not source_capabilities or not target_capabilities:
            return False
        
        # Check for compatible domains
        source_domains = set(source_capabilities.get("domains", []))
        target_domains = set(target_capabilities.get("domains", []))
        
        return len(source_domains.intersection(target_domains)) > 0
    
    async def _validate_external_knowledge(self, event: LearningEvent) -> bool:
        """Validate external knowledge for integration."""
        # Validate source credibility
        trusted_sources = [
            "documentation_update",
            "security_advisory", 
            "best_practices_guide",
            "vendor_recommendation"
        ]
        
        if event.source_brain not in trusted_sources:
            return False
        
        # Validate knowledge format and content
        return self._validate_data_integrity(event.data)
    
    def _get_brain_capabilities(self, brain_id: str) -> Dict[str, Any]:
        """Get capabilities for a specific brain."""
        # This would be populated from actual brain registrations
        brain_capabilities = {
            "intent_brain": {
                "domains": ["itil", "business_analysis", "intent_classification"],
                "capabilities": ["classification", "analysis", "prioritization"]
            },
            "technical_brain": {
                "domains": ["system_administration", "automation", "troubleshooting"],
                "capabilities": ["execution_planning", "resource_management", "orchestration"]
            },
            "container_sme": {
                "domains": ["containers", "kubernetes", "docker"],
                "capabilities": ["container_management", "orchestration", "scaling"]
            }
        }
        
        return brain_capabilities.get(brain_id, {})
    
    async def _apply_learning(self, event: LearningEvent):
        """Apply learning from a validated event."""
        brain_id = event.target_brain
        
        # Initialize brain knowledge base if not exists
        if brain_id not in self.brain_knowledge_bases:
            self.brain_knowledge_bases[brain_id] = {}
        
        brain_knowledge = self.brain_knowledge_bases[brain_id]
        
        # Apply different types of learning
        if event.learning_type == LearningType.EXECUTION_FEEDBACK:
            await self._apply_execution_learning(brain_knowledge, event.data)
        elif event.learning_type == LearningType.CROSS_BRAIN_SHARING:
            await self._apply_cross_brain_learning(event)
        elif event.learning_type == LearningType.EXTERNAL_KNOWLEDGE:
            await self._apply_external_learning(event)
        
        # Update learning patterns
        self._update_learning_patterns(event)
    
    async def _apply_execution_learning(self, brain_knowledge: Dict, learning_data: Dict):
        """Apply execution-based learning."""
        # Update confidence calibration
        if "confidence_correlation" in learning_data:
            if "confidence_calibration" not in brain_knowledge:
                brain_knowledge["confidence_calibration"] = []
            brain_knowledge["confidence_calibration"].append(learning_data["confidence_correlation"])
        
        # Update error patterns
        if "error_patterns" in learning_data:
            if "error_patterns" not in brain_knowledge:
                brain_knowledge["error_patterns"] = {}
            error_type = learning_data["error_patterns"]["error_type"]
            brain_knowledge["error_patterns"][error_type] = learning_data["error_patterns"]
        
        # Update performance baselines
        if "performance_metrics" in learning_data:
            if "performance_baselines" not in brain_knowledge:
                brain_knowledge["performance_baselines"] = []
            brain_knowledge["performance_baselines"].append(learning_data["performance_metrics"])
    
    async def _apply_cross_brain_learning(self, event: LearningEvent):
        """Apply cross-brain learning."""
        target_knowledge = self.brain_knowledge_bases.get(event.target_brain, {})
        
        # Transfer applicable knowledge
        if "shared_patterns" not in target_knowledge:
            target_knowledge["shared_patterns"] = {}
        
        target_knowledge["shared_patterns"][event.source_brain] = event.data
    
    async def _apply_external_learning(self, event: LearningEvent):
        """Apply external knowledge learning."""
        target_knowledge = self.brain_knowledge_bases.get(event.target_brain, {})
        
        # Integrate external knowledge
        if "external_knowledge" not in target_knowledge:
            target_knowledge["external_knowledge"] = {}
        
        target_knowledge["external_knowledge"][event.source_brain] = {
            "data": event.data,
            "timestamp": event.timestamp.isoformat(),
            "quality_score": event.quality_score
        }
    
    def _update_learning_patterns(self, event: LearningEvent):
        """Update learning patterns for pattern recognition."""
        pattern_key = f"{event.learning_type.value}_{event.source_brain}_{event.target_brain}"
        
        if pattern_key not in self.learning_patterns:
            self.learning_patterns[pattern_key] = {
                "count": 0,
                "average_quality": 0.0,
                "success_rate": 0.0,
                "last_updated": None
            }
        
        pattern = self.learning_patterns[pattern_key]
        pattern["count"] += 1
        pattern["average_quality"] = (
            (pattern["average_quality"] * (pattern["count"] - 1) + event.quality_score) / 
            pattern["count"]
        )
        pattern["last_updated"] = event.timestamp.isoformat()
    
    def _update_metrics(self, event: LearningEvent, success: bool):
        """Update learning metrics."""
        self.learning_metrics.total_events += 1
        
        if success:
            self.learning_metrics.successful_learnings += 1
        else:
            self.learning_metrics.rejected_learnings += 1
        
        # Update average quality score
        if self.learning_metrics.total_events > 0:
            self.learning_metrics.average_quality_score = (
                self.learning_metrics.successful_learnings / self.learning_metrics.total_events
            )
        
        # Update learning rate (events per hour)
        now = datetime.now()
        hour_ago = now - timedelta(hours=1)
        recent_events = [e for e in self.learning_events if e.timestamp > hour_ago]
        self.learning_metrics.learning_rate = len(recent_events)
    
    async def get_learning_status(self) -> Dict[str, Any]:
        """Get current learning system status."""
        return {
            "engine_id": self.engine_id,
            "version": self.version,
            "learning_enabled": self.learning_enabled,
            "metrics": {
                "total_events": self.learning_metrics.total_events,
                "successful_learnings": self.learning_metrics.successful_learnings,
                "rejected_learnings": self.learning_metrics.rejected_learnings,
                "success_rate": (
                    self.learning_metrics.successful_learnings / max(self.learning_metrics.total_events, 1)
                ),
                "average_quality_score": self.learning_metrics.average_quality_score,
                "learning_rate_per_hour": self.learning_metrics.learning_rate
            },
            "brain_knowledge_bases": list(self.brain_knowledge_bases.keys()),
            "learning_patterns_count": len(self.learning_patterns),
            "quality_threshold": self.quality_threshold
        }
    
    async def cleanup_old_learning_events(self):
        """Clean up old learning events to manage memory."""
        cutoff_date = datetime.now() - timedelta(days=self.learning_retention_days)
        
        initial_count = len(self.learning_events)
        self.learning_events = [
            event for event in self.learning_events 
            if event.timestamp > cutoff_date
        ]
        
        cleaned_count = initial_count - len(self.learning_events)
        if cleaned_count > 0:
            logger.info(f"Cleaned up {cleaned_count} old learning events")