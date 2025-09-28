"""
Smart Progress Messaging for OUIOE Phase 3
Provides contextual, adaptive progress messages with intelligent communication.
"""

import asyncio
import time
import random
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass, field
from enum import Enum
import json
from datetime import datetime, timedelta

from .progress_intelligence import (
    OperationType, ComplexityLevel, ProgressPhase,
    OperationContext, ProgressMilestone, ProgressIntelligence
)
from .operation_analyzer import OperationMetrics, OperationAnalyzer


class MessageTone(Enum):
    """Different tones for progress messages."""
    PROFESSIONAL = "professional"
    FRIENDLY = "friendly"
    TECHNICAL = "technical"
    ENCOURAGING = "encouraging"
    DETAILED = "detailed"
    CONCISE = "concise"


class MessageContext(Enum):
    """Context for message delivery."""
    STARTUP = "startup"
    PROGRESS = "progress"
    MILESTONE = "milestone"
    CHALLENGE = "challenge"
    SUCCESS = "success"
    COMPLETION = "completion"


@dataclass
class MessageTemplate:
    """Template for contextual messages."""
    template: str
    tone: MessageTone
    context: MessageContext
    operation_types: List[OperationType]
    complexity_levels: List[ComplexityLevel]
    variables: List[str] = field(default_factory=list)


@dataclass
class AdaptiveMessage:
    """Adaptive message with context and metadata."""
    content: str
    tone: MessageTone
    context: MessageContext
    confidence: float
    technical_detail: Optional[str] = None
    user_benefit: Optional[str] = None
    estimated_time: Optional[str] = None
    progress_indicator: Optional[str] = None


class SmartProgressMessaging:
    """
    Intelligent progress messaging system that adapts communication
    based on operation context, user preferences, and progress state.
    """
    
    def __init__(self):
        self.message_templates = self._initialize_message_templates()
        self.tone_preferences: Dict[str, MessageTone] = {}
        self.user_interaction_history: Dict[str, List[str]] = {}
        self.context_adaptations = self._initialize_context_adaptations()
        self.encouragement_phrases = self._initialize_encouragement_phrases()
        
    def _initialize_message_templates(self) -> Dict[str, List[MessageTemplate]]:
        """Initialize comprehensive message templates."""
        return {
            "startup": [
                MessageTemplate(
                    "🧠 Starting to analyze your {operation_type} request...",
                    MessageTone.FRIENDLY,
                    MessageContext.STARTUP,
                    [OperationType.CODE_ANALYSIS, OperationType.PROBLEM_SOLVING],
                    [ComplexityLevel.MODERATE, ComplexityLevel.COMPLEX],
                    ["operation_type"]
                ),
                MessageTemplate(
                    "⚡ Processing your {complexity} {operation_type} task...",
                    MessageTone.PROFESSIONAL,
                    MessageContext.STARTUP,
                    list(OperationType),
                    [ComplexityLevel.COMPLEX, ComplexityLevel.ADVANCED],
                    ["complexity", "operation_type"]
                ),
                MessageTemplate(
                    "🎯 Ready to help with your {domain} question!",
                    MessageTone.ENCOURAGING,
                    MessageContext.STARTUP,
                    [OperationType.CHAT_CONVERSATION, OperationType.TECHNICAL_EXPLANATION],
                    [ComplexityLevel.SIMPLE, ComplexityLevel.MODERATE],
                    ["domain"]
                )
            ],
            
            "progress": [
                MessageTemplate(
                    "🔍 Deep diving into {current_phase} - {progress}% complete",
                    MessageTone.TECHNICAL,
                    MessageContext.PROGRESS,
                    [OperationType.CODE_ANALYSIS, OperationType.RESEARCH_ANALYSIS],
                    [ComplexityLevel.COMPLEX, ComplexityLevel.ADVANCED],
                    ["current_phase", "progress"]
                ),
                MessageTemplate(
                    "⚡ Making great progress on {current_phase}... {eta} remaining",
                    MessageTone.ENCOURAGING,
                    MessageContext.PROGRESS,
                    list(OperationType),
                    [ComplexityLevel.MODERATE, ComplexityLevel.COMPLEX],
                    ["current_phase", "eta"]
                ),
                MessageTemplate(
                    "🧠 Thinking through {complexity_indicator}... {progress}% done",
                    MessageTone.FRIENDLY,
                    MessageContext.PROGRESS,
                    [OperationType.PROBLEM_SOLVING, OperationType.DECISION_MAKING],
                    [ComplexityLevel.COMPLEX, ComplexityLevel.ADVANCED],
                    ["complexity_indicator", "progress"]
                )
            ],
            
            "milestone": [
                MessageTemplate(
                    "✅ {milestone_name} completed! Moving to {next_phase}...",
                    MessageTone.ENCOURAGING,
                    MessageContext.MILESTONE,
                    list(OperationType),
                    list(ComplexityLevel),
                    ["milestone_name", "next_phase"]
                ),
                MessageTemplate(
                    "🎯 Reached {milestone_name} milestone - {user_benefit}",
                    MessageTone.PROFESSIONAL,
                    MessageContext.MILESTONE,
                    [OperationType.CODE_ANALYSIS, OperationType.TECHNICAL_EXPLANATION],
                    [ComplexityLevel.MODERATE, ComplexityLevel.COMPLEX],
                    ["milestone_name", "user_benefit"]
                ),
                MessageTemplate(
                    "⭐ {milestone_name} phase complete! {technical_insight}",
                    MessageTone.TECHNICAL,
                    MessageContext.MILESTONE,
                    [OperationType.RESEARCH_ANALYSIS, OperationType.DATA_PROCESSING],
                    [ComplexityLevel.COMPLEX, ComplexityLevel.ADVANCED],
                    ["milestone_name", "technical_insight"]
                )
            ],
            
            "challenge": [
                MessageTemplate(
                    "🤔 Encountering {challenge_type} - taking extra time for accuracy...",
                    MessageTone.PROFESSIONAL,
                    MessageContext.CHALLENGE,
                    list(OperationType),
                    [ComplexityLevel.COMPLEX, ComplexityLevel.ADVANCED],
                    ["challenge_type"]
                ),
                MessageTemplate(
                    "💪 Working through complex {domain} aspects - almost there!",
                    MessageTone.ENCOURAGING,
                    MessageContext.CHALLENGE,
                    [OperationType.PROBLEM_SOLVING, OperationType.CODE_ANALYSIS],
                    [ComplexityLevel.ADVANCED],
                    ["domain"]
                ),
                MessageTemplate(
                    "🔧 Handling {complexity_indicator} requires careful analysis...",
                    MessageTone.TECHNICAL,
                    MessageContext.CHALLENGE,
                    [OperationType.TECHNICAL_EXPLANATION, OperationType.RESEARCH_ANALYSIS],
                    [ComplexityLevel.COMPLEX, ComplexityLevel.ADVANCED],
                    ["complexity_indicator"]
                )
            ],
            
            "completion": [
                MessageTemplate(
                    "🎉 Successfully completed your {operation_type} request!",
                    MessageTone.ENCOURAGING,
                    MessageContext.COMPLETION,
                    list(OperationType),
                    list(ComplexityLevel),
                    ["operation_type"]
                ),
                MessageTemplate(
                    "✨ {operation_type} analysis complete - {key_insight}",
                    MessageTone.PROFESSIONAL,
                    MessageContext.COMPLETION,
                    [OperationType.CODE_ANALYSIS, OperationType.RESEARCH_ANALYSIS],
                    [ComplexityLevel.MODERATE, ComplexityLevel.COMPLEX],
                    ["operation_type", "key_insight"]
                ),
                MessageTemplate(
                    "🚀 Task accomplished! Processed {complexity} {operation_type} in {duration}",
                    MessageTone.TECHNICAL,
                    MessageContext.COMPLETION,
                    list(OperationType),
                    [ComplexityLevel.COMPLEX, ComplexityLevel.ADVANCED],
                    ["complexity", "operation_type", "duration"]
                )
            ]
        }
    
    def _initialize_context_adaptations(self) -> Dict[str, Dict[str, str]]:
        """Initialize context-specific adaptations."""
        return {
            "operation_type_names": {
                "chat_conversation": "conversation",
                "code_analysis": "code review",
                "problem_solving": "problem solving",
                "creative_writing": "creative writing",
                "data_processing": "data analysis",
                "technical_explanation": "technical explanation",
                "decision_making": "decision analysis",
                "research_analysis": "research analysis"
            },
            
            "complexity_descriptions": {
                "simple": "straightforward",
                "moderate": "detailed",
                "complex": "comprehensive",
                "advanced": "in-depth"
            },
            
            "phase_descriptions": {
                "initialization": "getting started",
                "context_analysis": "understanding context",
                "problem_decomposition": "breaking down the problem",
                "solution_generation": "developing solutions",
                "validation": "validating approach",
                "refinement": "refining details",
                "finalization": "finalizing results"
            },
            
            "domain_friendly_names": {
                "web_development": "web development",
                "data_science": "data science",
                "devops": "DevOps",
                "database": "database",
                "networking": "networking",
                "security": "security"
            }
        }
    
    def _initialize_encouragement_phrases(self) -> Dict[str, List[str]]:
        """Initialize encouragement phrases for different contexts."""
        return {
            "progress": [
                "Making excellent progress!",
                "Right on track!",
                "Coming along nicely!",
                "Steady progress being made!",
                "Moving forward smoothly!"
            ],
            
            "complex_task": [
                "Taking the time needed for quality results!",
                "Thorough analysis in progress!",
                "Ensuring comprehensive coverage!",
                "Quality takes time - almost there!",
                "Deep thinking for the best outcome!"
            ],
            
            "milestone": [
                "Great milestone reached!",
                "Excellent progress checkpoint!",
                "Another step closer to completion!",
                "Significant progress made!",
                "Key phase accomplished!"
            ],
            
            "completion": [
                "Mission accomplished!",
                "Task completed successfully!",
                "Excellent work completed!",
                "Successfully delivered!",
                "All done and ready!"
            ]
        }
    
    async def generate_adaptive_message(self,
                                      progress_intelligence: ProgressIntelligence,
                                      operation_metrics: OperationMetrics,
                                      message_context: MessageContext,
                                      user_id: Optional[str] = None,
                                      elapsed_time: float = 0.0) -> AdaptiveMessage:
        """
        Generate an adaptive message based on current progress and context.
        
        Args:
            progress_intelligence: Current progress intelligence
            operation_metrics: Operation metrics and analysis
            message_context: Context for the message
            user_id: Optional user ID for personalization
            elapsed_time: Time elapsed since operation start
            
        Returns:
            AdaptiveMessage with contextual content
        """
        # Determine appropriate tone
        tone = self._determine_message_tone(
            progress_intelligence.operation_context,
            operation_metrics,
            user_id
        )
        
        # Select appropriate template
        template = self._select_message_template(
            message_context,
            progress_intelligence.operation_context,
            tone
        )
        
        # Generate message content
        content = await self._generate_message_content(
            template,
            progress_intelligence,
            operation_metrics,
            elapsed_time
        )
        
        # Add contextual enhancements
        enhanced_content = self._enhance_message_content(
            content,
            progress_intelligence,
            operation_metrics,
            message_context
        )
        
        # Generate additional details
        technical_detail = self._generate_technical_detail(
            progress_intelligence,
            operation_metrics,
            tone
        )
        
        user_benefit = self._generate_user_benefit(
            progress_intelligence,
            message_context
        )
        
        estimated_time = self._format_estimated_time(
            progress_intelligence.eta_seconds
        )
        
        progress_indicator = self._generate_progress_indicator(
            progress_intelligence.completion_percentage,
            progress_intelligence.current_phase
        )
        
        return AdaptiveMessage(
            content=enhanced_content,
            tone=tone,
            context=message_context,
            confidence=progress_intelligence.confidence_score,
            technical_detail=technical_detail,
            user_benefit=user_benefit,
            estimated_time=estimated_time,
            progress_indicator=progress_indicator
        )
    
    def _determine_message_tone(self,
                              operation_context: OperationContext,
                              metrics: OperationMetrics,
                              user_id: Optional[str]) -> MessageTone:
        """Determine the appropriate message tone."""
        # Check user preferences
        if user_id and user_id in self.tone_preferences:
            return self.tone_preferences[user_id]
        
        # Determine based on operation characteristics
        if operation_context.operation_type in [
            OperationType.CODE_ANALYSIS, 
            OperationType.TECHNICAL_EXPLANATION
        ]:
            return MessageTone.TECHNICAL
        
        if operation_context.complexity_level == ComplexityLevel.ADVANCED:
            return MessageTone.PROFESSIONAL
        
        if operation_context.operation_type == OperationType.CREATIVE_WRITING:
            return MessageTone.ENCOURAGING
        
        # Default to friendly for most interactions
        return MessageTone.FRIENDLY
    
    def _select_message_template(self,
                               context: MessageContext,
                               operation_context: OperationContext,
                               tone: MessageTone) -> MessageTemplate:
        """Select the most appropriate message template."""
        context_key = context.value
        available_templates = self.message_templates.get(context_key, [])
        
        # Filter templates by operation type and complexity
        suitable_templates = []
        for template in available_templates:
            if (operation_context.operation_type in template.operation_types and
                operation_context.complexity_level in template.complexity_levels):
                suitable_templates.append(template)
        
        # If no suitable templates, use any template for the context
        if not suitable_templates:
            suitable_templates = available_templates
        
        # Prefer templates with matching tone
        tone_matched = [t for t in suitable_templates if t.tone == tone]
        if tone_matched:
            return random.choice(tone_matched)
        
        # Fall back to any suitable template
        if suitable_templates:
            return random.choice(suitable_templates)
        
        # Ultimate fallback
        return MessageTemplate(
            "Processing your request...",
            tone,
            context,
            [operation_context.operation_type],
            [operation_context.complexity_level]
        )
    
    async def _generate_message_content(self,
                                      template: MessageTemplate,
                                      progress_intelligence: ProgressIntelligence,
                                      metrics: OperationMetrics,
                                      elapsed_time: float) -> str:
        """Generate message content from template."""
        content = template.template
        
        # Prepare variable substitutions
        substitutions = {
            "operation_type": self._get_friendly_operation_name(
                progress_intelligence.operation_context.operation_type
            ),
            "complexity": self._get_complexity_description(
                progress_intelligence.operation_context.complexity_level
            ),
            "current_phase": self._get_phase_description(
                progress_intelligence.current_phase
            ),
            "progress": str(int(progress_intelligence.completion_percentage * 100)),
            "eta": self._format_estimated_time(progress_intelligence.eta_seconds),
            "domain": progress_intelligence.operation_context.technical_domain or "general",
            "complexity_indicator": self._get_complexity_indicator_description(metrics),
            "milestone_name": self._get_current_milestone_name(progress_intelligence),
            "next_phase": self._get_next_phase_name(progress_intelligence),
            "user_benefit": self._get_milestone_benefit(progress_intelligence),
            "technical_insight": progress_intelligence.technical_insight or "detailed analysis",
            "challenge_type": self._get_challenge_description(metrics),
            "key_insight": self._get_key_insight(progress_intelligence),
            "duration": self._format_duration(elapsed_time)
        }
        
        # Apply substitutions
        for variable, value in substitutions.items():
            placeholder = "{" + variable + "}"
            if placeholder in content:
                content = content.replace(placeholder, str(value))
        
        return content
    
    def _enhance_message_content(self,
                               content: str,
                               progress_intelligence: ProgressIntelligence,
                               metrics: OperationMetrics,
                               context: MessageContext) -> str:
        """Enhance message content with contextual additions."""
        enhanced = content
        
        # Add encouragement for complex tasks
        if (progress_intelligence.operation_context.complexity_level == ComplexityLevel.ADVANCED and
            context == MessageContext.PROGRESS):
            encouragement = random.choice(self.encouragement_phrases["complex_task"])
            enhanced = f"{enhanced} {encouragement}"
        
        # Add progress indicators for milestone contexts
        if context == MessageContext.MILESTONE:
            milestone_encouragement = random.choice(self.encouragement_phrases["milestone"])
            enhanced = f"{enhanced} {milestone_encouragement}"
        
        # Add technical context for technical operations
        if (progress_intelligence.operation_context.operation_type in [
            OperationType.CODE_ANALYSIS, OperationType.TECHNICAL_EXPLANATION
        ] and len(metrics.complexity_indicators) > 2):
            enhanced = f"{enhanced} (handling {len(metrics.complexity_indicators)} complexity factors)"
        
        return enhanced
    
    def _generate_technical_detail(self,
                                 progress_intelligence: ProgressIntelligence,
                                 metrics: OperationMetrics,
                                 tone: MessageTone) -> Optional[str]:
        """Generate technical detail if appropriate for the tone."""
        if tone not in [MessageTone.TECHNICAL, MessageTone.DETAILED]:
            return None
        
        details = []
        
        # Add thinking step information
        if metrics.thinking_steps_count > 0:
            details.append(f"Processing {metrics.thinking_steps_count} thinking steps")
        
        # Add complexity indicators
        if metrics.complexity_indicators:
            top_indicators = metrics.complexity_indicators[:2]
            details.append(f"Handling {', '.join(top_indicators)}")
        
        # Add performance information
        if metrics.performance_score > 0.8:
            details.append("High-efficiency processing")
        elif metrics.performance_score < 0.6:
            details.append("Thorough analysis mode")
        
        return " | ".join(details) if details else None
    
    def _generate_user_benefit(self,
                             progress_intelligence: ProgressIntelligence,
                             context: MessageContext) -> Optional[str]:
        """Generate user benefit description."""
        if context not in [MessageContext.MILESTONE, MessageContext.COMPLETION]:
            return None
        
        operation_type = progress_intelligence.operation_context.operation_type
        
        benefits = {
            OperationType.CODE_ANALYSIS: "Identifying improvements and potential issues",
            OperationType.PROBLEM_SOLVING: "Developing a clear solution path",
            OperationType.CREATIVE_WRITING: "Crafting engaging and original content",
            OperationType.TECHNICAL_EXPLANATION: "Providing clear, understandable explanations",
            OperationType.RESEARCH_ANALYSIS: "Delivering comprehensive insights",
            OperationType.DATA_PROCESSING: "Extracting meaningful patterns and insights",
            OperationType.DECISION_MAKING: "Evaluating options for informed decisions"
        }
        
        return benefits.get(operation_type, "Providing helpful assistance")
    
    def _get_friendly_operation_name(self, operation_type: OperationType) -> str:
        """Get user-friendly operation name."""
        return self.context_adaptations["operation_type_names"].get(
            operation_type.value, operation_type.value.replace("_", " ")
        )
    
    def _get_complexity_description(self, complexity: ComplexityLevel) -> str:
        """Get user-friendly complexity description."""
        return self.context_adaptations["complexity_descriptions"].get(
            complexity.value, complexity.value
        )
    
    def _get_phase_description(self, phase: ProgressPhase) -> str:
        """Get user-friendly phase description."""
        return self.context_adaptations["phase_descriptions"].get(
            phase.value, phase.value.replace("_", " ")
        )
    
    def _get_complexity_indicator_description(self, metrics: OperationMetrics) -> str:
        """Get description of complexity indicators."""
        if not metrics.complexity_indicators:
            return "standard complexity"
        
        # Get the most significant indicator
        primary_indicator = metrics.complexity_indicators[0]
        return primary_indicator.replace("_", " ")
    
    def _get_current_milestone_name(self, progress_intelligence: ProgressIntelligence) -> str:
        """Get current milestone name."""
        if progress_intelligence.milestones:
            for milestone in progress_intelligence.milestones:
                if milestone.phase == progress_intelligence.current_phase:
                    return milestone.name
        return self._get_phase_description(progress_intelligence.current_phase)
    
    def _get_next_phase_name(self, progress_intelligence: ProgressIntelligence) -> str:
        """Get next phase name."""
        if progress_intelligence.next_milestone:
            return self._get_phase_description(progress_intelligence.next_milestone.phase)
        return "completion"
    
    def _get_milestone_benefit(self, progress_intelligence: ProgressIntelligence) -> str:
        """Get milestone benefit description."""
        if progress_intelligence.next_milestone and progress_intelligence.next_milestone.user_benefit:
            return progress_intelligence.next_milestone.user_benefit
        return "moving closer to completion"
    
    def _get_challenge_description(self, metrics: OperationMetrics) -> str:
        """Get challenge description based on metrics."""
        if "high_reasoning_complexity" in metrics.complexity_indicators:
            return "complex reasoning challenges"
        elif "multi_step_process" in metrics.complexity_indicators:
            return "multi-step process complexity"
        elif metrics.context_switches > 2:
            return "multi-faceted analysis requirements"
        else:
            return "technical complexity"
    
    def _get_key_insight(self, progress_intelligence: ProgressIntelligence) -> str:
        """Get key insight for completion messages."""
        operation_type = progress_intelligence.operation_context.operation_type
        
        insights = {
            OperationType.CODE_ANALYSIS: "comprehensive code review completed",
            OperationType.PROBLEM_SOLVING: "solution strategy developed",
            OperationType.CREATIVE_WRITING: "creative content generated",
            OperationType.TECHNICAL_EXPLANATION: "clear explanation provided",
            OperationType.RESEARCH_ANALYSIS: "thorough analysis completed"
        }
        
        return insights.get(operation_type, "task completed successfully")
    
    def _format_estimated_time(self, eta_seconds: float) -> str:
        """Format estimated time in user-friendly format."""
        if eta_seconds < 1:
            return "moments"
        elif eta_seconds < 60:
            return f"{int(eta_seconds)} seconds"
        elif eta_seconds < 3600:
            minutes = int(eta_seconds / 60)
            return f"{minutes} minute{'s' if minutes != 1 else ''}"
        else:
            hours = int(eta_seconds / 3600)
            return f"{hours} hour{'s' if hours != 1 else ''}"
    
    def _format_duration(self, elapsed_seconds: float) -> str:
        """Format elapsed duration."""
        if elapsed_seconds < 60:
            return f"{elapsed_seconds:.1f} seconds"
        else:
            minutes = int(elapsed_seconds / 60)
            seconds = int(elapsed_seconds % 60)
            return f"{minutes}m {seconds}s"
    
    def _generate_progress_indicator(self, completion: float, phase: ProgressPhase) -> str:
        """Generate visual progress indicator."""
        percentage = int(completion * 100)
        
        # Create progress bar
        bar_length = 20
        filled_length = int(bar_length * completion)
        bar = "█" * filled_length + "░" * (bar_length - filled_length)
        
        # Add phase emoji
        phase_emojis = {
            ProgressPhase.INITIALIZATION: "🚀",
            ProgressPhase.CONTEXT_ANALYSIS: "🔍",
            ProgressPhase.PROBLEM_DECOMPOSITION: "🧩",
            ProgressPhase.SOLUTION_GENERATION: "⚡",
            ProgressPhase.VALIDATION: "✅",
            ProgressPhase.REFINEMENT: "✨",
            ProgressPhase.FINALIZATION: "🎯"
        }
        
        emoji = phase_emojis.get(phase, "⚡")
        
        return f"{emoji} [{bar}] {percentage}%"
    
    def set_user_tone_preference(self, user_id: str, tone: MessageTone):
        """Set user's preferred message tone."""
        self.tone_preferences[user_id] = tone
    
    def record_user_interaction(self, user_id: str, message_content: str):
        """Record user interaction for learning preferences."""
        if user_id not in self.user_interaction_history:
            self.user_interaction_history[user_id] = []
        
        self.user_interaction_history[user_id].append(message_content)
        
        # Keep only recent history
        if len(self.user_interaction_history[user_id]) > 50:
            self.user_interaction_history[user_id] = self.user_interaction_history[user_id][-50:]
    
    def get_messaging_insights(self, user_id: Optional[str] = None) -> Dict[str, Any]:
        """Get insights about messaging patterns."""
        insights = {
            "total_templates": sum(len(templates) for templates in self.message_templates.values()),
            "supported_tones": [tone.value for tone in MessageTone],
            "supported_contexts": [context.value for context in MessageContext]
        }
        
        if user_id and user_id in self.user_interaction_history:
            history = self.user_interaction_history[user_id]
            insights["user_interaction_count"] = len(history)
            insights["preferred_tone"] = self.tone_preferences.get(user_id, MessageTone.FRIENDLY).value
        
        return insights


# Convenience function for creating the messaging system
def create_smart_progress_messaging() -> SmartProgressMessaging:
    """Create and return a new Smart Progress Messaging instance."""
    return SmartProgressMessaging()