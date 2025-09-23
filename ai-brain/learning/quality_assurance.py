"""
Learning Quality Assurance - Phase 2 Week 5 Implementation

This module provides quality assurance for learning updates in the Multi-Brain Architecture:
- Validation of learning updates before integration
- Quality scoring and classification
- Learning update filtering and approval
- Quality metrics and monitoring
"""

from typing import Dict, List, Any, Optional, Union
import asyncio
import json
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
import logging

from .continuous_learning_system import LearningUpdate, LearningType, LearningQuality

logger = logging.getLogger(__name__)


class ValidationCriteria(Enum):
    """Validation criteria for learning updates"""
    CONFIDENCE_THRESHOLD = "confidence_threshold"
    SOURCE_RELIABILITY = "source_reliability"
    CONTENT_COMPLETENESS = "content_completeness"
    CONSISTENCY_CHECK = "consistency_check"
    IMPACT_ASSESSMENT = "impact_assessment"
    SAFETY_VALIDATION = "safety_validation"


@dataclass
class ValidationResult:
    """Result of learning update validation"""
    is_valid: bool
    quality_level: LearningQuality
    confidence_score: float
    validation_criteria_met: List[ValidationCriteria]
    validation_criteria_failed: List[ValidationCriteria]
    notes: List[str] = field(default_factory=list)
    recommendations: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class QualityMetrics:
    """Quality metrics for the learning system"""
    total_validations: int = 0
    successful_validations: int = 0
    failed_validations: int = 0
    average_quality_score: float = 0.0
    quality_distribution: Dict[str, int] = field(default_factory=dict)
    validation_time_avg: float = 0.0
    recent_validation_trend: str = "stable"


class LearningQualityAssurance:
    """
    Learning Quality Assurance system for validating learning updates
    
    This system ensures that only high-quality, safe, and beneficial learning updates
    are integrated into the Multi-Brain Architecture.
    """
    
    def __init__(self):
        self.validation_rules: Dict[ValidationCriteria, Dict[str, Any]] = {}
        self.quality_metrics = QualityMetrics()
        self.validation_history: List[Dict[str, Any]] = []
        self.blacklisted_sources: List[str] = []
        self.trusted_sources: List[str] = []
        
        # Initialize default validation rules
        self._initialize_validation_rules()
        
        # Quality thresholds
        self.quality_thresholds = {
            LearningQuality.HIGH: 0.8,
            LearningQuality.MEDIUM: 0.6,
            LearningQuality.LOW: 0.4,
            LearningQuality.REJECTED: 0.0
        }
    
    def _initialize_validation_rules(self):
        """Initialize default validation rules"""
        self.validation_rules = {
            ValidationCriteria.CONFIDENCE_THRESHOLD: {
                "minimum_confidence": 0.3,
                "weight": 0.2,
                "description": "Learning update must meet minimum confidence threshold"
            },
            ValidationCriteria.SOURCE_RELIABILITY: {
                "trusted_sources_bonus": 0.2,
                "blacklisted_penalty": -1.0,
                "weight": 0.25,
                "description": "Source reliability affects learning update quality"
            },
            ValidationCriteria.CONTENT_COMPLETENESS: {
                "required_fields": ["learning_type", "source_brain", "target_brain", "content"],
                "content_min_size": 10,
                "weight": 0.15,
                "description": "Learning update must have complete and meaningful content"
            },
            ValidationCriteria.CONSISTENCY_CHECK: {
                "check_against_history": True,
                "max_contradiction_tolerance": 0.3,
                "weight": 0.2,
                "description": "Learning update must be consistent with existing knowledge"
            },
            ValidationCriteria.IMPACT_ASSESSMENT: {
                "assess_potential_impact": True,
                "high_impact_threshold": 0.8,
                "weight": 0.1,
                "description": "Assess potential impact of learning update"
            },
            ValidationCriteria.SAFETY_VALIDATION: {
                "safety_keywords": ["delete", "remove", "destroy", "disable", "bypass"],
                "safety_weight": 0.1,
                "description": "Ensure learning update doesn't introduce safety risks"
            }
        }
    
    async def validate_learning_update(self, learning_update: LearningUpdate) -> ValidationResult:
        """
        Validate a learning update for quality and safety
        
        Args:
            learning_update: The learning update to validate
            
        Returns:
            ValidationResult: Detailed validation result
        """
        validation_start = datetime.now()
        
        try:
            # Initialize validation tracking
            criteria_met = []
            criteria_failed = []
            validation_notes = []
            recommendations = []
            quality_scores = []
            
            # Run validation criteria
            for criteria, rules in self.validation_rules.items():
                try:
                    result = await self._validate_criteria(learning_update, criteria, rules)
                    
                    if result["passed"]:
                        criteria_met.append(criteria)
                        quality_scores.append(result["score"] * rules["weight"])
                    else:
                        criteria_failed.append(criteria)
                        quality_scores.append(0.0)
                    
                    validation_notes.extend(result.get("notes", []))
                    recommendations.extend(result.get("recommendations", []))
                    
                except Exception as e:
                    logger.error(f"Error validating criteria {criteria}: {str(e)}")
                    criteria_failed.append(criteria)
                    validation_notes.append(f"Validation error for {criteria.value}: {str(e)}")
            
            # Calculate overall quality score
            overall_quality_score = sum(quality_scores) if quality_scores else 0.0
            
            # Determine quality level
            quality_level = self._determine_quality_level(overall_quality_score)
            
            # Determine if valid
            is_valid = quality_level != LearningQuality.REJECTED and len(criteria_failed) < len(criteria_met)
            
            # Create validation result
            validation_result = ValidationResult(
                is_valid=is_valid,
                quality_level=quality_level,
                confidence_score=overall_quality_score,
                validation_criteria_met=criteria_met,
                validation_criteria_failed=criteria_failed,
                notes=validation_notes,
                recommendations=recommendations,
                metadata={
                    "validation_time": (datetime.now() - validation_start).total_seconds(),
                    "criteria_scores": dict(zip([c.value for c in self.validation_rules.keys()], quality_scores)),
                    "overall_score": overall_quality_score
                }
            )
            
            # Update metrics
            await self._update_quality_metrics(validation_result)
            
            # Store validation history
            self.validation_history.append({
                "update_id": learning_update.update_id,
                "validation_result": validation_result,
                "timestamp": datetime.now(),
                "learning_type": learning_update.learning_type.value
            })
            
            logger.info(f"Learning update validation completed: {learning_update.update_id} - "
                       f"Quality: {quality_level.value}, Valid: {is_valid}")
            
            return validation_result
            
        except Exception as e:
            logger.error(f"Error validating learning update: {str(e)}")
            
            # Return failed validation result
            return ValidationResult(
                is_valid=False,
                quality_level=LearningQuality.REJECTED,
                confidence_score=0.0,
                validation_criteria_met=[],
                validation_criteria_failed=list(self.validation_rules.keys()),
                notes=[f"Validation failed due to error: {str(e)}"],
                recommendations=["Manual review required"],
                metadata={"error": str(e)}
            )
    
    async def _validate_criteria(self, learning_update: LearningUpdate, 
                                criteria: ValidationCriteria, rules: Dict[str, Any]) -> Dict[str, Any]:
        """Validate a specific criteria"""
        
        if criteria == ValidationCriteria.CONFIDENCE_THRESHOLD:
            return await self._validate_confidence_threshold(learning_update, rules)
        elif criteria == ValidationCriteria.SOURCE_RELIABILITY:
            return await self._validate_source_reliability(learning_update, rules)
        elif criteria == ValidationCriteria.CONTENT_COMPLETENESS:
            return await self._validate_content_completeness(learning_update, rules)
        elif criteria == ValidationCriteria.CONSISTENCY_CHECK:
            return await self._validate_consistency(learning_update, rules)
        elif criteria == ValidationCriteria.IMPACT_ASSESSMENT:
            return await self._validate_impact_assessment(learning_update, rules)
        elif criteria == ValidationCriteria.SAFETY_VALIDATION:
            return await self._validate_safety(learning_update, rules)
        else:
            return {"passed": False, "score": 0.0, "notes": [f"Unknown criteria: {criteria}"]}
    
    async def _validate_confidence_threshold(self, learning_update: LearningUpdate, rules: Dict[str, Any]) -> Dict[str, Any]:
        """Validate confidence threshold"""
        try:
            min_confidence = rules.get("minimum_confidence", 0.3)
            
            if learning_update.confidence >= min_confidence:
                score = min(1.0, learning_update.confidence / 0.8)  # Scale to 0.8 as perfect
                return {
                    "passed": True,
                    "score": score,
                    "notes": [f"Confidence {learning_update.confidence:.2f} meets threshold {min_confidence}"]
                }
            else:
                return {
                    "passed": False,
                    "score": learning_update.confidence / min_confidence,  # Partial score
                    "notes": [f"Confidence {learning_update.confidence:.2f} below threshold {min_confidence}"],
                    "recommendations": ["Increase confidence through additional validation"]
                }
                
        except Exception as e:
            return {"passed": False, "score": 0.0, "notes": [f"Confidence validation error: {str(e)}"]}
    
    async def _validate_source_reliability(self, learning_update: LearningUpdate, rules: Dict[str, Any]) -> Dict[str, Any]:
        """Validate source reliability"""
        try:
            source = learning_update.source_brain
            base_score = 0.7  # Default score
            
            # Check if source is blacklisted
            if source in self.blacklisted_sources:
                return {
                    "passed": False,
                    "score": 0.0,
                    "notes": [f"Source {source} is blacklisted"],
                    "recommendations": ["Use trusted source for learning updates"]
                }
            
            # Bonus for trusted sources
            if source in self.trusted_sources:
                base_score += rules.get("trusted_sources_bonus", 0.2)
                notes = [f"Source {source} is trusted"]
            else:
                notes = [f"Source {source} reliability: standard"]
            
            # Check source brain type reliability
            if "sme_" in source:
                base_score += 0.1  # SME brains are generally more reliable
            elif source == "execution_feedback_analyzer":
                base_score += 0.15  # Execution feedback is highly reliable
            elif source == "external_knowledge_integrator":
                base_score -= 0.1  # External knowledge needs more validation
            
            return {
                "passed": True,
                "score": min(1.0, base_score),
                "notes": notes
            }
            
        except Exception as e:
            return {"passed": False, "score": 0.0, "notes": [f"Source reliability validation error: {str(e)}"]}
    
    async def _validate_content_completeness(self, learning_update: LearningUpdate, rules: Dict[str, Any]) -> Dict[str, Any]:
        """Validate content completeness"""
        try:
            required_fields = rules.get("required_fields", [])
            min_content_size = rules.get("content_min_size", 10)
            
            # Check required fields
            missing_fields = []
            for field in required_fields:
                if not hasattr(learning_update, field) or getattr(learning_update, field) is None:
                    missing_fields.append(field)
            
            if missing_fields:
                return {
                    "passed": False,
                    "score": max(0.0, 1.0 - len(missing_fields) / len(required_fields)),
                    "notes": [f"Missing required fields: {missing_fields}"],
                    "recommendations": ["Ensure all required fields are provided"]
                }
            
            # Check content size
            content_str = str(learning_update.content)
            if len(content_str) < min_content_size:
                return {
                    "passed": False,
                    "score": len(content_str) / min_content_size,
                    "notes": [f"Content too small: {len(content_str)} < {min_content_size}"],
                    "recommendations": ["Provide more detailed content"]
                }
            
            # Check content structure
            if not isinstance(learning_update.content, dict) or not learning_update.content:
                return {
                    "passed": False,
                    "score": 0.3,
                    "notes": ["Content is not a valid dictionary or is empty"],
                    "recommendations": ["Provide structured content as dictionary"]
                }
            
            return {
                "passed": True,
                "score": 1.0,
                "notes": ["Content completeness validation passed"]
            }
            
        except Exception as e:
            return {"passed": False, "score": 0.0, "notes": [f"Content completeness validation error: {str(e)}"]}
    
    async def _validate_consistency(self, learning_update: LearningUpdate, rules: Dict[str, Any]) -> Dict[str, Any]:
        """Validate consistency with existing knowledge"""
        try:
            if not rules.get("check_against_history", True):
                return {"passed": True, "score": 1.0, "notes": ["Consistency check disabled"]}
            
            # Check against recent learning updates of the same type
            recent_updates = [
                entry for entry in self.validation_history[-100:]  # Check last 100 updates
                if entry["learning_type"] == learning_update.learning_type.value
                and entry["validation_result"].is_valid
            ]
            
            if not recent_updates:
                return {"passed": True, "score": 0.8, "notes": ["No historical data for consistency check"]}
            
            # Simple consistency check - look for contradictory content
            contradictions = 0
            total_checks = 0
            
            for entry in recent_updates[-10:]:  # Check against last 10 similar updates
                historical_content = entry.get("content", {})
                current_content = learning_update.content
                
                # Check for direct contradictions in key-value pairs
                for key, value in current_content.items():
                    if key in historical_content:
                        total_checks += 1
                        if historical_content[key] != value and isinstance(value, (str, int, float, bool)):
                            contradictions += 1
            
            if total_checks > 0:
                contradiction_rate = contradictions / total_checks
                max_tolerance = rules.get("max_contradiction_tolerance", 0.3)
                
                if contradiction_rate > max_tolerance:
                    return {
                        "passed": False,
                        "score": max(0.0, 1.0 - contradiction_rate),
                        "notes": [f"High contradiction rate: {contradiction_rate:.2f} > {max_tolerance}"],
                        "recommendations": ["Review for consistency with existing knowledge"]
                    }
            
            return {
                "passed": True,
                "score": 1.0,
                "notes": ["Consistency validation passed"]
            }
            
        except Exception as e:
            return {"passed": False, "score": 0.0, "notes": [f"Consistency validation error: {str(e)}"]}
    
    async def _validate_impact_assessment(self, learning_update: LearningUpdate, rules: Dict[str, Any]) -> Dict[str, Any]:
        """Validate potential impact of learning update"""
        try:
            if not rules.get("assess_potential_impact", True):
                return {"passed": True, "score": 1.0, "notes": ["Impact assessment disabled"]}
            
            # Assess impact based on learning type and target
            impact_score = 0.5  # Default medium impact
            impact_notes = []
            
            # High impact learning types
            if learning_update.learning_type in [LearningType.ERROR_CORRECTION, LearningType.EXTERNAL_KNOWLEDGE]:
                impact_score += 0.2
                impact_notes.append("High impact learning type")
            
            # Target brain impact
            if learning_update.target_brain == "all_brains":
                impact_score += 0.3
                impact_notes.append("Affects all brains - high impact")
            elif "sme_" in learning_update.target_brain:
                impact_score += 0.1
                impact_notes.append("Affects SME brain - medium impact")
            
            # Content-based impact assessment
            content_str = str(learning_update.content).lower()
            high_impact_keywords = ["critical", "security", "safety", "error", "failure", "risk"]
            
            for keyword in high_impact_keywords:
                if keyword in content_str:
                    impact_score += 0.1
                    impact_notes.append(f"Contains high-impact keyword: {keyword}")
            
            # Normalize impact score
            impact_score = min(1.0, impact_score)
            
            # Check if impact is too high
            high_impact_threshold = rules.get("high_impact_threshold", 0.8)
            if impact_score > high_impact_threshold:
                return {
                    "passed": False,
                    "score": 0.7,  # Still valuable but needs review
                    "notes": impact_notes + [f"High impact score: {impact_score:.2f}"],
                    "recommendations": ["High impact update requires additional review"]
                }
            
            return {
                "passed": True,
                "score": 1.0,
                "notes": impact_notes + [f"Impact score: {impact_score:.2f}"]
            }
            
        except Exception as e:
            return {"passed": False, "score": 0.0, "notes": [f"Impact assessment error: {str(e)}"]}
    
    async def _validate_safety(self, learning_update: LearningUpdate, rules: Dict[str, Any]) -> Dict[str, Any]:
        """Validate safety of learning update"""
        try:
            safety_keywords = rules.get("safety_keywords", [])
            content_str = str(learning_update.content).lower()
            
            # Check for potentially dangerous keywords
            dangerous_keywords_found = []
            for keyword in safety_keywords:
                if keyword in content_str:
                    dangerous_keywords_found.append(keyword)
            
            if dangerous_keywords_found:
                # Not automatically failed, but flagged for review
                return {
                    "passed": False,
                    "score": 0.5,  # Partial score - needs review
                    "notes": [f"Safety keywords found: {dangerous_keywords_found}"],
                    "recommendations": ["Manual safety review required"]
                }
            
            # Check for learning updates that might disable safety features
            if learning_update.learning_type == LearningType.ERROR_CORRECTION:
                if any(term in content_str for term in ["disable", "bypass", "skip", "ignore"]):
                    return {
                        "passed": False,
                        "score": 0.3,
                        "notes": ["Error correction might disable safety features"],
                        "recommendations": ["Ensure safety features remain active"]
                    }
            
            return {
                "passed": True,
                "score": 1.0,
                "notes": ["Safety validation passed"]
            }
            
        except Exception as e:
            return {"passed": False, "score": 0.0, "notes": [f"Safety validation error: {str(e)}"]}
    
    def _determine_quality_level(self, quality_score: float) -> LearningQuality:
        """Determine quality level based on score"""
        if quality_score >= self.quality_thresholds[LearningQuality.HIGH]:
            return LearningQuality.HIGH
        elif quality_score >= self.quality_thresholds[LearningQuality.MEDIUM]:
            return LearningQuality.MEDIUM
        elif quality_score >= self.quality_thresholds[LearningQuality.LOW]:
            return LearningQuality.LOW
        else:
            return LearningQuality.REJECTED
    
    async def _update_quality_metrics(self, validation_result: ValidationResult):
        """Update quality metrics based on validation result"""
        try:
            self.quality_metrics.total_validations += 1
            
            if validation_result.is_valid:
                self.quality_metrics.successful_validations += 1
            else:
                self.quality_metrics.failed_validations += 1
            
            # Update average quality score
            total = self.quality_metrics.total_validations
            current_avg = self.quality_metrics.average_quality_score
            new_score = validation_result.confidence_score
            
            self.quality_metrics.average_quality_score = (
                (current_avg * (total - 1) + new_score) / total
            )
            
            # Update quality distribution
            quality_level = validation_result.quality_level.value
            if quality_level not in self.quality_metrics.quality_distribution:
                self.quality_metrics.quality_distribution[quality_level] = 0
            self.quality_metrics.quality_distribution[quality_level] += 1
            
            # Update validation time
            validation_time = validation_result.metadata.get("validation_time", 0)
            current_time_avg = self.quality_metrics.validation_time_avg
            self.quality_metrics.validation_time_avg = (
                (current_time_avg * (total - 1) + validation_time) / total
            )
            
            # Update trend (simple calculation based on recent validations)
            if len(self.validation_history) >= 10:
                recent_success_rate = sum(
                    1 for entry in self.validation_history[-10:]
                    if entry["validation_result"].is_valid
                ) / 10
                
                if recent_success_rate > 0.8:
                    self.quality_metrics.recent_validation_trend = "improving"
                elif recent_success_rate < 0.5:
                    self.quality_metrics.recent_validation_trend = "declining"
                else:
                    self.quality_metrics.recent_validation_trend = "stable"
            
        except Exception as e:
            logger.error(f"Error updating quality metrics: {str(e)}")
    
    async def add_trusted_source(self, source: str):
        """Add a source to the trusted sources list"""
        if source not in self.trusted_sources:
            self.trusted_sources.append(source)
            logger.info(f"Added trusted source: {source}")
    
    async def add_blacklisted_source(self, source: str):
        """Add a source to the blacklisted sources list"""
        if source not in self.blacklisted_sources:
            self.blacklisted_sources.append(source)
            # Remove from trusted sources if present
            if source in self.trusted_sources:
                self.trusted_sources.remove(source)
            logger.info(f"Added blacklisted source: {source}")
    
    async def update_validation_rules(self, criteria: ValidationCriteria, rules: Dict[str, Any]):
        """Update validation rules for a specific criteria"""
        self.validation_rules[criteria] = rules
        logger.info(f"Updated validation rules for {criteria.value}")
    
    async def get_quality_metrics(self) -> Dict[str, Any]:
        """Get current quality metrics"""
        return {
            "total_validations": self.quality_metrics.total_validations,
            "successful_validations": self.quality_metrics.successful_validations,
            "failed_validations": self.quality_metrics.failed_validations,
            "success_rate": (
                self.quality_metrics.successful_validations / max(1, self.quality_metrics.total_validations)
            ),
            "average_quality_score": self.quality_metrics.average_quality_score,
            "quality_distribution": self.quality_metrics.quality_distribution,
            "validation_time_avg": self.quality_metrics.validation_time_avg,
            "recent_validation_trend": self.quality_metrics.recent_validation_trend,
            "trusted_sources": len(self.trusted_sources),
            "blacklisted_sources": len(self.blacklisted_sources)
        }
    
    async def get_validation_history(self, limit: int = 50) -> List[Dict[str, Any]]:
        """Get recent validation history"""
        try:
            recent_history = self.validation_history[-limit:]
            return [
                {
                    "update_id": entry["update_id"],
                    "learning_type": entry["learning_type"],
                    "is_valid": entry["validation_result"].is_valid,
                    "quality_level": entry["validation_result"].quality_level.value,
                    "confidence_score": entry["validation_result"].confidence_score,
                    "timestamp": entry["timestamp"].isoformat(),
                    "criteria_met": len(entry["validation_result"].validation_criteria_met),
                    "criteria_failed": len(entry["validation_result"].validation_criteria_failed)
                }
                for entry in recent_history
            ]
        except Exception as e:
            logger.error(f"Error getting validation history: {str(e)}")
            return []