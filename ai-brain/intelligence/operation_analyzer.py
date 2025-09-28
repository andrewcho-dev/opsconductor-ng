"""
Operation Analyzer for OUIOE Phase 3
Provides detailed analysis of AI operations for intelligent progress tracking.
"""

import asyncio
import time
import re
from typing import Dict, List, Optional, Tuple, Any, Set
from dataclasses import dataclass, field
from enum import Enum
import json
from datetime import datetime, timedelta

from .progress_intelligence import (
    OperationType, ComplexityLevel, ProgressPhase,
    OperationContext, ProgressMilestone
)


@dataclass
class OperationMetrics:
    """Metrics for operation performance analysis."""
    thinking_steps_count: int = 0
    processing_time: float = 0.0
    context_switches: int = 0
    complexity_indicators: List[str] = field(default_factory=list)
    resource_usage: Dict[str, float] = field(default_factory=dict)
    performance_score: float = 0.0


@dataclass
class OperationPattern:
    """Pattern recognition for operation types."""
    pattern_type: str
    confidence: float
    indicators: List[str]
    typical_duration: float
    complexity_factors: List[str]


class OperationAnalyzer:
    """
    Advanced analyzer for AI operations providing detailed insights
    for intelligent progress tracking and optimization.
    """
    
    def __init__(self):
        self.operation_history: Dict[str, List[OperationMetrics]] = {}
        self.pattern_library = self._initialize_pattern_library()
        self.performance_baselines = self._initialize_performance_baselines()
        self.complexity_analyzers = self._initialize_complexity_analyzers()
        
    def _initialize_pattern_library(self) -> Dict[str, OperationPattern]:
        """Initialize the library of operation patterns."""
        return {
            "code_review": OperationPattern(
                pattern_type="code_review",
                confidence=0.9,
                indicators=["review", "analyze code", "check", "debug", "syntax"],
                typical_duration=8.5,
                complexity_factors=["file_size", "language_complexity", "error_count"]
            ),
            "problem_solving": OperationPattern(
                pattern_type="problem_solving",
                confidence=0.85,
                indicators=["solve", "fix", "resolve", "troubleshoot", "issue"],
                typical_duration=12.0,
                complexity_factors=["problem_scope", "dependencies", "constraints"]
            ),
            "explanation": OperationPattern(
                pattern_type="explanation",
                confidence=0.8,
                indicators=["explain", "how", "why", "what is", "describe"],
                typical_duration=6.0,
                complexity_factors=["topic_depth", "technical_level", "audience"]
            ),
            "creative_task": OperationPattern(
                pattern_type="creative_task",
                confidence=0.75,
                indicators=["create", "write", "design", "generate", "compose"],
                typical_duration=10.0,
                complexity_factors=["creativity_level", "length", "originality"]
            ),
            "data_analysis": OperationPattern(
                pattern_type="data_analysis",
                confidence=0.88,
                indicators=["analyze data", "statistics", "metrics", "calculate"],
                typical_duration=9.0,
                complexity_factors=["data_size", "analysis_depth", "visualization"]
            )
        }
    
    def _initialize_performance_baselines(self) -> Dict[OperationType, Dict[str, float]]:
        """Initialize performance baselines for different operation types."""
        return {
            OperationType.CHAT_CONVERSATION: {
                "avg_thinking_steps": 3.0,
                "avg_duration": 3.5,
                "complexity_threshold": 2.0
            },
            OperationType.CODE_ANALYSIS: {
                "avg_thinking_steps": 6.0,
                "avg_duration": 8.0,
                "complexity_threshold": 4.0
            },
            OperationType.PROBLEM_SOLVING: {
                "avg_thinking_steps": 8.0,
                "avg_duration": 12.0,
                "complexity_threshold": 5.0
            },
            OperationType.CREATIVE_WRITING: {
                "avg_thinking_steps": 7.0,
                "avg_duration": 10.0,
                "complexity_threshold": 4.5
            },
            OperationType.DATA_PROCESSING: {
                "avg_thinking_steps": 5.0,
                "avg_duration": 6.0,
                "complexity_threshold": 3.5
            },
            OperationType.TECHNICAL_EXPLANATION: {
                "avg_thinking_steps": 6.0,
                "avg_duration": 7.0,
                "complexity_threshold": 4.0
            },
            OperationType.DECISION_MAKING: {
                "avg_thinking_steps": 7.0,
                "avg_duration": 9.0,
                "complexity_threshold": 4.5
            },
            OperationType.RESEARCH_ANALYSIS: {
                "avg_thinking_steps": 10.0,
                "avg_duration": 15.0,
                "complexity_threshold": 6.0
            }
        }
    
    def _initialize_complexity_analyzers(self) -> Dict[str, callable]:
        """Initialize complexity analysis functions."""
        return {
            "lexical_complexity": self._analyze_lexical_complexity,
            "semantic_complexity": self._analyze_semantic_complexity,
            "structural_complexity": self._analyze_structural_complexity,
            "domain_complexity": self._analyze_domain_complexity,
            "cognitive_complexity": self._analyze_cognitive_complexity
        }
    
    async def analyze_operation_depth(self, 
                                    message: str, 
                                    operation_context: OperationContext,
                                    thinking_steps: Optional[List[str]] = None) -> OperationMetrics:
        """
        Perform deep analysis of an operation for intelligent progress tracking.
        
        Args:
            message: The original user message
            operation_context: The operation context from progress intelligence
            thinking_steps: Current thinking steps (if available)
            
        Returns:
            OperationMetrics with detailed analysis
        """
        metrics = OperationMetrics()
        
        # Analyze thinking steps if available
        if thinking_steps:
            metrics.thinking_steps_count = len(thinking_steps)
            metrics.context_switches = self._count_context_switches(thinking_steps)
        
        # Analyze complexity indicators
        metrics.complexity_indicators = await self._identify_complexity_indicators(
            message, operation_context, thinking_steps
        )
        
        # Calculate performance score
        metrics.performance_score = await self._calculate_performance_score(
            operation_context, metrics
        )
        
        # Analyze resource usage patterns
        metrics.resource_usage = await self._analyze_resource_usage(
            operation_context, metrics
        )
        
        return metrics
    
    def _count_context_switches(self, thinking_steps: List[str]) -> int:
        """Count context switches in thinking steps."""
        if not thinking_steps or len(thinking_steps) < 2:
            return 0
        
        context_indicators = [
            "however", "but", "on the other hand", "alternatively",
            "let me think", "actually", "wait", "hmm", "also"
        ]
        
        switches = 0
        for step in thinking_steps:
            step_lower = step.lower()
            for indicator in context_indicators:
                if indicator in step_lower:
                    switches += 1
                    break
        
        return switches
    
    async def _identify_complexity_indicators(self,
                                            message: str,
                                            context: OperationContext,
                                            thinking_steps: Optional[List[str]]) -> List[str]:
        """Identify specific complexity indicators in the operation."""
        indicators = []
        
        # Run all complexity analyzers
        for analyzer_name, analyzer_func in self.complexity_analyzers.items():
            result = await analyzer_func(message, context, thinking_steps)
            if result:
                indicators.extend(result)
        
        return list(set(indicators))  # Remove duplicates
    
    async def _analyze_lexical_complexity(self,
                                        message: str,
                                        context: OperationContext,
                                        thinking_steps: Optional[List[str]]) -> List[str]:
        """Analyze lexical complexity indicators."""
        indicators = []
        
        # Word count analysis
        word_count = len(message.split())
        if word_count > 100:
            indicators.append("high_word_count")
        elif word_count > 50:
            indicators.append("moderate_word_count")
        
        # Technical vocabulary density
        technical_terms = [
            "algorithm", "implementation", "architecture", "optimization",
            "performance", "scalability", "integration", "configuration"
        ]
        
        message_lower = message.lower()
        tech_term_count = sum(1 for term in technical_terms if term in message_lower)
        
        if tech_term_count >= 3:
            indicators.append("high_technical_vocabulary")
        elif tech_term_count >= 1:
            indicators.append("moderate_technical_vocabulary")
        
        # Sentence complexity
        sentences = message.split('.')
        avg_sentence_length = sum(len(s.split()) for s in sentences) / max(len(sentences), 1)
        
        if avg_sentence_length > 20:
            indicators.append("complex_sentence_structure")
        
        return indicators
    
    async def _analyze_semantic_complexity(self,
                                         message: str,
                                         context: OperationContext,
                                         thinking_steps: Optional[List[str]]) -> List[str]:
        """Analyze semantic complexity indicators."""
        indicators = []
        
        # Multi-concept analysis
        if len(context.key_concepts) > 5:
            indicators.append("multi_concept_operation")
        
        # Abstract concept detection
        abstract_indicators = [
            "concept", "theory", "principle", "methodology", "framework",
            "paradigm", "philosophy", "strategy", "approach"
        ]
        
        message_lower = message.lower()
        abstract_count = sum(1 for term in abstract_indicators if term in message_lower)
        
        if abstract_count >= 2:
            indicators.append("high_abstraction_level")
        elif abstract_count >= 1:
            indicators.append("moderate_abstraction_level")
        
        # Relationship complexity
        relationship_indicators = [
            "relationship", "connection", "dependency", "interaction",
            "correlation", "causation", "influence", "impact"
        ]
        
        relationship_count = sum(1 for term in relationship_indicators if term in message_lower)
        if relationship_count >= 1:
            indicators.append("complex_relationships")
        
        return indicators
    
    async def _analyze_structural_complexity(self,
                                           message: str,
                                           context: OperationContext,
                                           thinking_steps: Optional[List[str]]) -> List[str]:
        """Analyze structural complexity indicators."""
        indicators = []
        
        # Multi-step operation detection
        step_indicators = [
            "first", "second", "then", "next", "finally", "step",
            "phase", "stage", "process", "procedure"
        ]
        
        message_lower = message.lower()
        step_count = sum(1 for term in step_indicators if term in message_lower)
        
        if step_count >= 3:
            indicators.append("multi_step_process")
        elif step_count >= 1:
            indicators.append("sequential_process")
        
        # Conditional complexity
        conditional_indicators = [
            "if", "when", "unless", "provided", "assuming", "depending",
            "case", "scenario", "condition", "requirement"
        ]
        
        conditional_count = sum(1 for term in conditional_indicators if term in message_lower)
        if conditional_count >= 2:
            indicators.append("high_conditional_complexity")
        elif conditional_count >= 1:
            indicators.append("moderate_conditional_complexity")
        
        # Hierarchical structure detection
        hierarchy_indicators = [
            "level", "layer", "tier", "category", "subcategory",
            "parent", "child", "nested", "hierarchy"
        ]
        
        hierarchy_count = sum(1 for term in hierarchy_indicators if term in message_lower)
        if hierarchy_count >= 1:
            indicators.append("hierarchical_structure")
        
        return indicators
    
    async def _analyze_domain_complexity(self,
                                        message: str,
                                        context: OperationContext,
                                        thinking_steps: Optional[List[str]]) -> List[str]:
        """Analyze domain-specific complexity indicators."""
        indicators = []
        
        # Domain expertise requirements
        if context.technical_domain:
            domain_complexity = {
                "web_development": ["moderate_domain_complexity"],
                "data_science": ["high_domain_complexity", "mathematical_complexity"],
                "devops": ["high_domain_complexity", "infrastructure_complexity"],
                "database": ["moderate_domain_complexity", "query_complexity"],
                "networking": ["high_domain_complexity", "protocol_complexity"],
                "security": ["high_domain_complexity", "security_complexity"]
            }
            
            domain_indicators = domain_complexity.get(context.technical_domain, [])
            indicators.extend(domain_indicators)
        
        # Cross-domain complexity
        domains_mentioned = 0
        domain_keywords = {
            "frontend", "backend", "database", "network", "security",
            "devops", "cloud", "mobile", "desktop", "api"
        }
        
        message_lower = message.lower()
        for keyword in domain_keywords:
            if keyword in message_lower:
                domains_mentioned += 1
        
        if domains_mentioned >= 3:
            indicators.append("cross_domain_complexity")
        elif domains_mentioned >= 2:
            indicators.append("multi_domain_operation")
        
        return indicators
    
    async def _analyze_cognitive_complexity(self,
                                          message: str,
                                          context: OperationContext,
                                          thinking_steps: Optional[List[str]]) -> List[str]:
        """Analyze cognitive complexity indicators."""
        indicators = []
        
        # Reasoning complexity
        reasoning_indicators = [
            "analyze", "evaluate", "compare", "contrast", "synthesize",
            "deduce", "infer", "conclude", "reason", "logic"
        ]
        
        message_lower = message.lower()
        reasoning_count = sum(1 for term in reasoning_indicators if term in message_lower)
        
        if reasoning_count >= 3:
            indicators.append("high_reasoning_complexity")
        elif reasoning_count >= 1:
            indicators.append("moderate_reasoning_complexity")
        
        # Problem-solving complexity
        if context.operation_type == OperationType.PROBLEM_SOLVING:
            if context.complexity_level in [ComplexityLevel.COMPLEX, ComplexityLevel.ADVANCED]:
                indicators.append("complex_problem_solving")
        
        # Creative complexity
        if context.requires_creativity:
            creativity_indicators = [
                "creative", "innovative", "original", "unique", "novel",
                "imaginative", "artistic", "design"
            ]
            
            creativity_count = sum(1 for term in creativity_indicators if term in message_lower)
            if creativity_count >= 2:
                indicators.append("high_creative_complexity")
            elif creativity_count >= 1:
                indicators.append("moderate_creative_complexity")
        
        return indicators
    
    async def _calculate_performance_score(self,
                                         context: OperationContext,
                                         metrics: OperationMetrics) -> float:
        """Calculate performance score for the operation."""
        base_score = 0.7
        
        # Adjust based on complexity indicators
        complexity_bonus = len(metrics.complexity_indicators) * 0.02
        
        # Adjust based on operation type
        type_adjustments = {
            OperationType.CHAT_CONVERSATION: 0.1,
            OperationType.CODE_ANALYSIS: 0.05,
            OperationType.PROBLEM_SOLVING: -0.05,
            OperationType.CREATIVE_WRITING: 0.0,
            OperationType.RESEARCH_ANALYSIS: -0.1
        }
        
        type_adjustment = type_adjustments.get(context.operation_type, 0)
        
        # Adjust based on thinking efficiency
        thinking_efficiency = 0.0
        if metrics.thinking_steps_count > 0:
            baseline = self.performance_baselines.get(context.operation_type, {})
            expected_steps = baseline.get("avg_thinking_steps", 5.0)
            
            if metrics.thinking_steps_count <= expected_steps:
                thinking_efficiency = 0.1  # Efficient thinking
            elif metrics.thinking_steps_count > expected_steps * 1.5:
                thinking_efficiency = -0.05  # Less efficient
        
        # Context switch penalty
        context_switch_penalty = min(0.1, metrics.context_switches * 0.02)
        
        performance_score = (
            base_score + 
            complexity_bonus + 
            type_adjustment + 
            thinking_efficiency - 
            context_switch_penalty
        )
        
        return min(1.0, max(0.1, performance_score))
    
    async def _analyze_resource_usage(self,
                                    context: OperationContext,
                                    metrics: OperationMetrics) -> Dict[str, float]:
        """Analyze estimated resource usage patterns."""
        resource_usage = {
            "cognitive_load": 0.5,
            "processing_intensity": 0.5,
            "memory_usage": 0.3,
            "context_retention": 0.4
        }
        
        # Adjust based on complexity
        complexity_multipliers = {
            ComplexityLevel.SIMPLE: 0.7,
            ComplexityLevel.MODERATE: 1.0,
            ComplexityLevel.COMPLEX: 1.4,
            ComplexityLevel.ADVANCED: 1.8
        }
        
        multiplier = complexity_multipliers[context.complexity_level]
        
        for resource in resource_usage:
            resource_usage[resource] *= multiplier
        
        # Adjust based on operation type
        if context.operation_type == OperationType.CODE_ANALYSIS:
            resource_usage["processing_intensity"] *= 1.2
            resource_usage["memory_usage"] *= 1.3
        elif context.operation_type == OperationType.CREATIVE_WRITING:
            resource_usage["cognitive_load"] *= 1.3
            resource_usage["context_retention"] *= 1.2
        elif context.operation_type == OperationType.RESEARCH_ANALYSIS:
            resource_usage["memory_usage"] *= 1.5
            resource_usage["context_retention"] *= 1.4
        
        # Adjust based on complexity indicators
        if "high_reasoning_complexity" in metrics.complexity_indicators:
            resource_usage["cognitive_load"] *= 1.2
        
        if "multi_step_process" in metrics.complexity_indicators:
            resource_usage["processing_intensity"] *= 1.15
        
        # Normalize to 0-1 range
        for resource in resource_usage:
            resource_usage[resource] = min(1.0, resource_usage[resource])
        
        return resource_usage
    
    async def predict_operation_trajectory(self,
                                         context: OperationContext,
                                         current_metrics: OperationMetrics,
                                         elapsed_time: float) -> Dict[str, Any]:
        """
        Predict the trajectory of the operation based on current analysis.
        
        Args:
            context: Operation context
            current_metrics: Current operation metrics
            elapsed_time: Time elapsed so far
            
        Returns:
            Dictionary with trajectory predictions
        """
        baseline = self.performance_baselines.get(context.operation_type, {})
        
        # Predict total thinking steps
        current_steps = current_metrics.thinking_steps_count
        expected_total = baseline.get("avg_thinking_steps", 5.0)
        
        # Adjust based on complexity
        complexity_multipliers = {
            ComplexityLevel.SIMPLE: 0.7,
            ComplexityLevel.MODERATE: 1.0,
            ComplexityLevel.COMPLEX: 1.4,
            ComplexityLevel.ADVANCED: 1.8
        }
        
        predicted_total_steps = expected_total * complexity_multipliers[context.complexity_level]
        
        # Predict remaining phases
        remaining_phases = self._predict_remaining_phases(
            context, current_metrics, elapsed_time
        )
        
        # Predict performance characteristics
        predicted_performance = self._predict_performance_characteristics(
            context, current_metrics
        )
        
        return {
            "predicted_total_steps": int(predicted_total_steps),
            "predicted_remaining_time": context.estimated_duration - elapsed_time,
            "remaining_phases": remaining_phases,
            "performance_prediction": predicted_performance,
            "confidence": current_metrics.performance_score,
            "trajectory_type": self._classify_trajectory_type(context, current_metrics)
        }
    
    def _predict_remaining_phases(self,
                                context: OperationContext,
                                metrics: OperationMetrics,
                                elapsed_time: float) -> List[str]:
        """Predict remaining phases in the operation."""
        all_phases = [
            "context_analysis", "problem_decomposition", "solution_generation",
            "validation", "refinement", "finalization"
        ]
        
        # Estimate current phase based on elapsed time and complexity
        progress_ratio = elapsed_time / context.estimated_duration
        
        if progress_ratio < 0.2:
            current_phase_index = 0
        elif progress_ratio < 0.4:
            current_phase_index = 1
        elif progress_ratio < 0.7:
            current_phase_index = 2
        elif progress_ratio < 0.85:
            current_phase_index = 3
        elif progress_ratio < 0.95:
            current_phase_index = 4
        else:
            current_phase_index = 5
        
        return all_phases[current_phase_index + 1:]
    
    def _predict_performance_characteristics(self,
                                           context: OperationContext,
                                           metrics: OperationMetrics) -> Dict[str, str]:
        """Predict performance characteristics for the operation."""
        characteristics = {}
        
        # Predict thinking pattern
        if metrics.context_switches > 3:
            characteristics["thinking_pattern"] = "exploratory"
        elif metrics.context_switches < 1:
            characteristics["thinking_pattern"] = "linear"
        else:
            characteristics["thinking_pattern"] = "structured"
        
        # Predict processing style
        if "high_reasoning_complexity" in metrics.complexity_indicators:
            characteristics["processing_style"] = "analytical"
        elif "high_creative_complexity" in metrics.complexity_indicators:
            characteristics["processing_style"] = "creative"
        else:
            characteristics["processing_style"] = "systematic"
        
        # Predict completion style
        if context.complexity_level == ComplexityLevel.ADVANCED:
            characteristics["completion_style"] = "thorough"
        elif context.operation_type == OperationType.CREATIVE_WRITING:
            characteristics["completion_style"] = "iterative"
        else:
            characteristics["completion_style"] = "efficient"
        
        return characteristics
    
    def _classify_trajectory_type(self,
                                context: OperationContext,
                                metrics: OperationMetrics) -> str:
        """Classify the type of operation trajectory."""
        if context.complexity_level == ComplexityLevel.ADVANCED:
            return "deep_analysis"
        elif metrics.context_switches > 2:
            return "exploratory"
        elif context.operation_type == OperationType.CREATIVE_WRITING:
            return "creative_flow"
        elif context.operation_type == OperationType.CODE_ANALYSIS:
            return "systematic_review"
        else:
            return "standard_processing"
    
    def update_operation_history(self,
                               operation_type: OperationType,
                               metrics: OperationMetrics):
        """Update the operation history for learning and improvement."""
        if operation_type not in self.operation_history:
            self.operation_history[operation_type] = []
        
        self.operation_history[operation_type].append(metrics)
        
        # Keep only recent history (last 100 operations per type)
        if len(self.operation_history[operation_type]) > 100:
            self.operation_history[operation_type] = self.operation_history[operation_type][-100:]
    
    def get_operation_insights(self, operation_type: OperationType) -> Dict[str, Any]:
        """Get insights about operation patterns from history."""
        if operation_type not in self.operation_history:
            return {"message": "No historical data available"}
        
        history = self.operation_history[operation_type]
        
        if not history:
            return {"message": "No historical data available"}
        
        # Calculate averages
        avg_thinking_steps = sum(m.thinking_steps_count for m in history) / len(history)
        avg_performance = sum(m.performance_score for m in history) / len(history)
        avg_context_switches = sum(m.context_switches for m in history) / len(history)
        
        # Find common complexity indicators
        all_indicators = []
        for metrics in history:
            all_indicators.extend(metrics.complexity_indicators)
        
        indicator_counts = {}
        for indicator in all_indicators:
            indicator_counts[indicator] = indicator_counts.get(indicator, 0) + 1
        
        common_indicators = sorted(
            indicator_counts.items(), 
            key=lambda x: x[1], 
            reverse=True
        )[:5]
        
        return {
            "operation_count": len(history),
            "avg_thinking_steps": round(avg_thinking_steps, 1),
            "avg_performance_score": round(avg_performance, 2),
            "avg_context_switches": round(avg_context_switches, 1),
            "common_complexity_indicators": [indicator for indicator, count in common_indicators],
            "performance_trend": "improving" if len(history) > 5 and 
                               sum(m.performance_score for m in history[-5:]) / 5 > avg_performance 
                               else "stable"
        }


# Convenience function for creating the analyzer
def create_operation_analyzer() -> OperationAnalyzer:
    """Create and return a new Operation Analyzer instance."""
    return OperationAnalyzer()