"""
Progress Intelligence Engine for OUIOE Phase 3
Provides contextual progress analysis, dynamic milestone detection, and intelligent messaging.
"""

import asyncio
import time
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass, field
from enum import Enum
import re
import json
from datetime import datetime, timedelta


class OperationType(Enum):
    """Types of AI operations for contextual analysis."""
    CHAT_CONVERSATION = "chat_conversation"
    CODE_ANALYSIS = "code_analysis"
    PROBLEM_SOLVING = "problem_solving"
    CREATIVE_WRITING = "creative_writing"
    DATA_PROCESSING = "data_processing"
    TECHNICAL_EXPLANATION = "technical_explanation"
    DECISION_MAKING = "decision_making"
    RESEARCH_ANALYSIS = "research_analysis"
    UNKNOWN = "unknown"


class ComplexityLevel(Enum):
    """Complexity levels for operation assessment."""
    SIMPLE = "simple"          # 1-2 thinking steps, quick response
    MODERATE = "moderate"      # 3-5 thinking steps, standard processing
    COMPLEX = "complex"        # 6-10 thinking steps, detailed analysis
    ADVANCED = "advanced"      # 10+ thinking steps, deep reasoning


class ProgressPhase(Enum):
    """Dynamic progress phases based on operation context."""
    INITIALIZATION = "initialization"
    CONTEXT_ANALYSIS = "context_analysis"
    PROBLEM_DECOMPOSITION = "problem_decomposition"
    SOLUTION_GENERATION = "solution_generation"
    VALIDATION = "validation"
    REFINEMENT = "refinement"
    FINALIZATION = "finalization"


@dataclass
class OperationContext:
    """Context information for an AI operation."""
    operation_type: OperationType
    complexity_level: ComplexityLevel
    estimated_duration: float  # seconds
    key_concepts: List[str]
    user_intent: str
    technical_domain: Optional[str] = None
    requires_code: bool = False
    requires_analysis: bool = False
    requires_creativity: bool = False


@dataclass
class ProgressMilestone:
    """Dynamic milestone for progress tracking."""
    phase: ProgressPhase
    name: str
    description: str
    estimated_completion: float  # 0.0 to 1.0
    context_message: str
    technical_details: Optional[str] = None
    user_benefit: Optional[str] = None


@dataclass
class ProgressIntelligence:
    """Intelligent progress analysis result."""
    operation_context: OperationContext
    milestones: List[ProgressMilestone]
    current_phase: ProgressPhase
    completion_percentage: float
    eta_seconds: float
    confidence_score: float  # 0.0 to 1.0
    contextual_message: str
    technical_insight: Optional[str] = None
    next_milestone: Optional[ProgressMilestone] = None


class ProgressIntelligenceEngine:
    """
    Core engine for intelligent progress analysis and contextual messaging.
    Provides operation-aware progress tracking with dynamic milestone detection.
    """
    
    def __init__(self):
        self.operation_patterns = self._initialize_operation_patterns()
        self.complexity_indicators = self._initialize_complexity_indicators()
        self.milestone_templates = self._initialize_milestone_templates()
        self.message_templates = self._initialize_message_templates()
        self.performance_history: Dict[str, List[float]] = {}
        
    def _initialize_operation_patterns(self) -> Dict[OperationType, List[str]]:
        """Initialize patterns for operation type detection."""
        return {
            OperationType.CHAT_CONVERSATION: [
                r"chat|conversation|talk|discuss|ask|tell me",
                r"what do you think|opinion|advice",
                r"help me understand|explain to me"
            ],
            OperationType.CODE_ANALYSIS: [
                r"analyze.*code|review.*code|debug|fix.*bug",
                r"function|class|method|variable|syntax",
                r"programming|development|software"
            ],
            OperationType.PROBLEM_SOLVING: [
                r"solve|solution|problem|issue|challenge",
                r"how to|step by step|approach|strategy",
                r"troubleshoot|resolve|fix"
            ],
            OperationType.CREATIVE_WRITING: [
                r"write|create|compose|draft|story",
                r"creative|imaginative|narrative|fiction",
                r"poem|article|essay|script"
            ],
            OperationType.DATA_PROCESSING: [
                r"analyze.*data|process.*data|data.*analysis",
                r"statistics|metrics|numbers|dataset",
                r"calculate|compute|aggregate"
            ],
            OperationType.TECHNICAL_EXPLANATION: [
                r"explain.*how|how.*works|technical.*details",
                r"architecture|system|design|implementation",
                r"documentation|specification|guide"
            ],
            OperationType.DECISION_MAKING: [
                r"decide|choose|select|recommend|suggest",
                r"comparison|evaluate|assess|pros.*cons",
                r"best.*option|which.*better|should.*use"
            ],
            OperationType.RESEARCH_ANALYSIS: [
                r"research|investigate|study|examine",
                r"findings|evidence|sources|references",
                r"comprehensive.*analysis|detailed.*review"
            ]
        }
    
    def _initialize_complexity_indicators(self) -> Dict[str, int]:
        """Initialize indicators for complexity assessment."""
        return {
            # High complexity indicators
            "multiple steps": 3,
            "complex analysis": 4,
            "comprehensive": 3,
            "detailed": 2,
            "in-depth": 3,
            "thorough": 2,
            "advanced": 4,
            "sophisticated": 3,
            
            # Medium complexity indicators
            "analyze": 2,
            "compare": 2,
            "evaluate": 2,
            "implement": 2,
            "design": 2,
            
            # Low complexity indicators
            "simple": -2,
            "quick": -1,
            "basic": -1,
            "straightforward": -1,
            "easy": -2
        }
    
    def _initialize_milestone_templates(self) -> Dict[OperationType, List[ProgressMilestone]]:
        """Initialize milestone templates for different operation types."""
        return {
            OperationType.CHAT_CONVERSATION: [
                ProgressMilestone(
                    ProgressPhase.INITIALIZATION,
                    "Understanding Context",
                    "Processing your message and understanding the conversation context",
                    0.15,
                    "Getting ready to help you with your question...",
                    "Parsing user input and conversation history",
                    "Ensures I understand exactly what you're asking"
                ),
                ProgressMilestone(
                    ProgressPhase.SOLUTION_GENERATION,
                    "Formulating Response",
                    "Thinking through the best way to answer your question",
                    0.70,
                    "Crafting a helpful and accurate response...",
                    "Generating contextually appropriate response",
                    "Provides you with a thoughtful, relevant answer"
                ),
                ProgressMilestone(
                    ProgressPhase.FINALIZATION,
                    "Finalizing Answer",
                    "Reviewing and polishing the response for clarity",
                    0.95,
                    "Almost ready with your answer!",
                    "Final review and formatting",
                    "Ensures the response is clear and helpful"
                )
            ],
            
            OperationType.CODE_ANALYSIS: [
                ProgressMilestone(
                    ProgressPhase.INITIALIZATION,
                    "Code Parsing",
                    "Reading and parsing the provided code",
                    0.10,
                    "Examining your code structure...",
                    "Syntax analysis and code structure parsing",
                    "Understands the code you want me to analyze"
                ),
                ProgressMilestone(
                    ProgressPhase.CONTEXT_ANALYSIS,
                    "Pattern Recognition",
                    "Identifying code patterns, functions, and logic flow",
                    0.30,
                    "Analyzing code patterns and logic...",
                    "Control flow and pattern analysis",
                    "Identifies key components and potential issues"
                ),
                ProgressMilestone(
                    ProgressPhase.PROBLEM_DECOMPOSITION,
                    "Issue Detection",
                    "Scanning for bugs, improvements, and optimization opportunities",
                    0.60,
                    "Looking for issues and improvements...",
                    "Static analysis and best practice evaluation",
                    "Finds problems and suggests enhancements"
                ),
                ProgressMilestone(
                    ProgressPhase.SOLUTION_GENERATION,
                    "Solution Formulation",
                    "Developing recommendations and fixes",
                    0.85,
                    "Preparing recommendations and solutions...",
                    "Solution generation and code improvement suggestions",
                    "Provides actionable fixes and improvements"
                )
            ],
            
            OperationType.PROBLEM_SOLVING: [
                ProgressMilestone(
                    ProgressPhase.CONTEXT_ANALYSIS,
                    "Problem Understanding",
                    "Analyzing the problem and understanding requirements",
                    0.20,
                    "Breaking down the problem...",
                    "Problem decomposition and requirement analysis",
                    "Ensures I fully understand what needs to be solved"
                ),
                ProgressMilestone(
                    ProgressPhase.PROBLEM_DECOMPOSITION,
                    "Strategy Development",
                    "Developing a step-by-step approach to solve the problem",
                    0.45,
                    "Developing a solution strategy...",
                    "Solution methodology and approach planning",
                    "Creates a clear path to the solution"
                ),
                ProgressMilestone(
                    ProgressPhase.SOLUTION_GENERATION,
                    "Solution Implementation",
                    "Working through the solution step by step",
                    0.75,
                    "Implementing the solution approach...",
                    "Step-by-step solution execution",
                    "Provides the actual solution to your problem"
                ),
                ProgressMilestone(
                    ProgressPhase.VALIDATION,
                    "Solution Verification",
                    "Checking the solution for completeness and accuracy",
                    0.90,
                    "Verifying the solution quality...",
                    "Solution validation and quality assurance",
                    "Ensures the solution is correct and complete"
                )
            ]
        }
    
    def _initialize_message_templates(self) -> Dict[str, Dict[str, str]]:
        """Initialize contextual message templates."""
        return {
            "initialization": {
                "default": "Starting to process your request...",
                "code": "Beginning code analysis...",
                "problem": "Understanding your problem...",
                "creative": "Preparing for creative work...",
                "data": "Initializing data processing...",
                "research": "Starting research analysis..."
            },
            "progress": {
                "simple": "Making good progress...",
                "moderate": "Working through the details...",
                "complex": "Analyzing complex aspects...",
                "advanced": "Deep thinking in progress..."
            },
            "completion": {
                "success": "Successfully completed!",
                "partial": "Completed with insights...",
                "complex_done": "Complex analysis finished!"
            }
        }
    
    async def analyze_operation(self, 
                              message: str, 
                              context: Optional[Dict[str, Any]] = None) -> OperationContext:
        """
        Analyze an operation to determine its type, complexity, and context.
        
        Args:
            message: The user's message or operation description
            context: Additional context information
            
        Returns:
            OperationContext with detailed analysis
        """
        # Detect operation type
        operation_type = self._detect_operation_type(message)
        
        # Assess complexity
        complexity_level = self._assess_complexity(message, context)
        
        # Extract key concepts
        key_concepts = self._extract_key_concepts(message)
        
        # Determine user intent
        user_intent = self._determine_user_intent(message, operation_type)
        
        # Estimate duration based on complexity and type
        estimated_duration = self._estimate_duration(operation_type, complexity_level)
        
        # Determine technical domain
        technical_domain = self._detect_technical_domain(message)
        
        # Analyze requirements
        requires_code = self._requires_code_analysis(message)
        requires_analysis = self._requires_deep_analysis(message)
        requires_creativity = self._requires_creativity(message)
        
        return OperationContext(
            operation_type=operation_type,
            complexity_level=complexity_level,
            estimated_duration=estimated_duration,
            key_concepts=key_concepts,
            user_intent=user_intent,
            technical_domain=technical_domain,
            requires_code=requires_code,
            requires_analysis=requires_analysis,
            requires_creativity=requires_creativity
        )
    
    def _detect_operation_type(self, message: str) -> OperationType:
        """Detect the type of operation based on message content."""
        message_lower = message.lower()
        
        # Score each operation type
        type_scores = {}
        for op_type, patterns in self.operation_patterns.items():
            score = 0
            for pattern in patterns:
                if re.search(pattern, message_lower):
                    score += 1
            type_scores[op_type] = score
        
        # Return the highest scoring type, or UNKNOWN if no matches
        if max(type_scores.values()) > 0:
            return max(type_scores, key=type_scores.get)
        return OperationType.UNKNOWN
    
    def _assess_complexity(self, message: str, context: Optional[Dict[str, Any]]) -> ComplexityLevel:
        """Assess the complexity level of the operation."""
        message_lower = message.lower()
        complexity_score = 0
        
        # Analyze message for complexity indicators
        for indicator, score in self.complexity_indicators.items():
            if indicator in message_lower:
                complexity_score += score
        
        # Consider message length
        word_count = len(message.split())
        if word_count > 50:
            complexity_score += 2
        elif word_count > 20:
            complexity_score += 1
        
        # Consider context if available
        if context:
            if context.get("requires_multiple_steps", False):
                complexity_score += 3
            if context.get("technical_depth", 0) > 5:
                complexity_score += 2
        
        # Map score to complexity level
        if complexity_score >= 8:
            return ComplexityLevel.ADVANCED
        elif complexity_score >= 5:
            return ComplexityLevel.COMPLEX
        elif complexity_score >= 2:
            return ComplexityLevel.MODERATE
        else:
            return ComplexityLevel.SIMPLE
    
    def _extract_key_concepts(self, message: str) -> List[str]:
        """Extract key concepts from the message."""
        # Simple keyword extraction (can be enhanced with NLP)
        technical_terms = [
            "api", "database", "server", "client", "function", "class", "method",
            "algorithm", "data", "analysis", "performance", "security", "network",
            "system", "architecture", "design", "implementation", "optimization"
        ]
        
        message_lower = message.lower()
        found_concepts = []
        
        for term in technical_terms:
            if term in message_lower:
                found_concepts.append(term)
        
        # Add important nouns (simplified approach)
        words = message.split()
        for word in words:
            if len(word) > 6 and word.lower() not in found_concepts:
                found_concepts.append(word.lower())
        
        return found_concepts[:10]  # Limit to top 10 concepts
    
    def _determine_user_intent(self, message: str, operation_type: OperationType) -> str:
        """Determine the user's intent based on message and operation type."""
        intent_patterns = {
            "learn": ["learn", "understand", "explain", "teach", "show me"],
            "solve": ["solve", "fix", "resolve", "help", "problem"],
            "create": ["create", "build", "make", "generate", "write"],
            "analyze": ["analyze", "review", "examine", "check", "evaluate"],
            "improve": ["improve", "optimize", "enhance", "better", "upgrade"]
        }
        
        message_lower = message.lower()
        for intent, keywords in intent_patterns.items():
            if any(keyword in message_lower for keyword in keywords):
                return intent
        
        return "assist"  # Default intent
    
    def _estimate_duration(self, operation_type: OperationType, complexity: ComplexityLevel) -> float:
        """Estimate operation duration in seconds."""
        base_durations = {
            OperationType.CHAT_CONVERSATION: 3.0,
            OperationType.CODE_ANALYSIS: 8.0,
            OperationType.PROBLEM_SOLVING: 12.0,
            OperationType.CREATIVE_WRITING: 10.0,
            OperationType.DATA_PROCESSING: 6.0,
            OperationType.TECHNICAL_EXPLANATION: 7.0,
            OperationType.DECISION_MAKING: 9.0,
            OperationType.RESEARCH_ANALYSIS: 15.0,
            OperationType.UNKNOWN: 5.0
        }
        
        complexity_multipliers = {
            ComplexityLevel.SIMPLE: 0.7,
            ComplexityLevel.MODERATE: 1.0,
            ComplexityLevel.COMPLEX: 1.5,
            ComplexityLevel.ADVANCED: 2.2
        }
        
        base_duration = base_durations[operation_type]
        multiplier = complexity_multipliers[complexity]
        
        return base_duration * multiplier
    
    def _detect_technical_domain(self, message: str) -> Optional[str]:
        """Detect the technical domain of the operation."""
        domains = {
            "web_development": ["html", "css", "javascript", "react", "vue", "angular", "frontend", "backend"],
            "data_science": ["data", "analysis", "machine learning", "ai", "statistics", "pandas", "numpy"],
            "devops": ["docker", "kubernetes", "deployment", "ci/cd", "infrastructure", "cloud"],
            "database": ["sql", "database", "query", "mysql", "postgresql", "mongodb"],
            "networking": ["network", "tcp", "http", "api", "rest", "graphql", "protocol"],
            "security": ["security", "authentication", "encryption", "vulnerability", "penetration"]
        }
        
        message_lower = message.lower()
        for domain, keywords in domains.items():
            if any(keyword in message_lower for keyword in keywords):
                return domain
        
        return None
    
    def _requires_code_analysis(self, message: str) -> bool:
        """Check if the operation requires code analysis."""
        code_indicators = ["code", "function", "class", "method", "syntax", "debug", "programming"]
        return any(indicator in message.lower() for indicator in code_indicators)
    
    def _requires_deep_analysis(self, message: str) -> bool:
        """Check if the operation requires deep analysis."""
        analysis_indicators = ["analyze", "detailed", "comprehensive", "thorough", "in-depth", "examine"]
        return any(indicator in message.lower() for indicator in analysis_indicators)
    
    def _requires_creativity(self, message: str) -> bool:
        """Check if the operation requires creativity."""
        creative_indicators = ["create", "creative", "write", "story", "design", "innovative", "original"]
        return any(indicator in message.lower() for indicator in creative_indicators)
    
    async def generate_dynamic_milestones(self, operation_context: OperationContext) -> List[ProgressMilestone]:
        """
        Generate dynamic milestones based on operation context.
        
        Args:
            operation_context: The analyzed operation context
            
        Returns:
            List of dynamic milestones for the operation
        """
        # Get base milestones for operation type
        base_milestones = self.milestone_templates.get(
            operation_context.operation_type,
            self.milestone_templates[OperationType.CHAT_CONVERSATION]
        )
        
        # Customize milestones based on complexity and requirements
        customized_milestones = []
        
        for milestone in base_milestones:
            # Adjust milestone based on complexity
            adjusted_milestone = self._adjust_milestone_for_complexity(
                milestone, operation_context.complexity_level
            )
            
            # Customize message based on context
            adjusted_milestone.context_message = self._customize_milestone_message(
                adjusted_milestone, operation_context
            )
            
            customized_milestones.append(adjusted_milestone)
        
        # Add additional milestones for complex operations
        if operation_context.complexity_level in [ComplexityLevel.COMPLEX, ComplexityLevel.ADVANCED]:
            customized_milestones = self._add_complexity_milestones(
                customized_milestones, operation_context
            )
        
        return customized_milestones
    
    def _adjust_milestone_for_complexity(self, 
                                       milestone: ProgressMilestone, 
                                       complexity: ComplexityLevel) -> ProgressMilestone:
        """Adjust milestone timing and details based on complexity."""
        # Create a copy to avoid modifying the original
        adjusted = ProgressMilestone(
            phase=milestone.phase,
            name=milestone.name,
            description=milestone.description,
            estimated_completion=milestone.estimated_completion,
            context_message=milestone.context_message,
            technical_details=milestone.technical_details,
            user_benefit=milestone.user_benefit
        )
        
        # Adjust completion percentages for complex operations
        if complexity == ComplexityLevel.ADVANCED:
            # Spread milestones more evenly for advanced operations
            adjusted.estimated_completion *= 0.8
        elif complexity == ComplexityLevel.SIMPLE:
            # Compress milestones for simple operations
            adjusted.estimated_completion = min(0.95, adjusted.estimated_completion * 1.2)
        
        return adjusted
    
    def _customize_milestone_message(self, 
                                   milestone: ProgressMilestone, 
                                   context: OperationContext) -> str:
        """Customize milestone message based on operation context."""
        base_message = milestone.context_message
        
        # Add context-specific details
        if context.technical_domain:
            domain_context = {
                "web_development": "web development",
                "data_science": "data analysis",
                "devops": "infrastructure",
                "database": "database operations",
                "networking": "network analysis",
                "security": "security assessment"
            }
            domain_name = domain_context.get(context.technical_domain, context.technical_domain)
            base_message = f"{base_message} (focusing on {domain_name})"
        
        # Add complexity indicators
        if context.complexity_level == ComplexityLevel.ADVANCED:
            base_message = f"🧠 {base_message} - This requires deep analysis..."
        elif context.complexity_level == ComplexityLevel.COMPLEX:
            base_message = f"⚡ {base_message} - Working through complex details..."
        
        return base_message
    
    def _add_complexity_milestones(self, 
                                 milestones: List[ProgressMilestone], 
                                 context: OperationContext) -> List[ProgressMilestone]:
        """Add additional milestones for complex operations."""
        if context.requires_analysis and context.complexity_level == ComplexityLevel.ADVANCED:
            # Add deep analysis milestone
            analysis_milestone = ProgressMilestone(
                ProgressPhase.VALIDATION,
                "Deep Analysis",
                "Performing comprehensive analysis of all aspects",
                0.80,
                "🔍 Conducting thorough analysis...",
                "Multi-dimensional analysis and validation",
                "Ensures comprehensive understanding and accuracy"
            )
            milestones.insert(-1, analysis_milestone)
        
        return milestones
    
    async def calculate_progress_intelligence(self,
                                            operation_context: OperationContext,
                                            milestones: List[ProgressMilestone],
                                            current_step: int,
                                            total_steps: int,
                                            elapsed_time: float) -> ProgressIntelligence:
        """
        Calculate intelligent progress analysis with contextual insights.
        
        Args:
            operation_context: The operation context
            milestones: Dynamic milestones for the operation
            current_step: Current thinking step number
            total_steps: Total estimated thinking steps
            elapsed_time: Time elapsed since operation start
            
        Returns:
            ProgressIntelligence with comprehensive analysis
        """
        # Calculate basic completion percentage
        step_completion = current_step / max(total_steps, 1) if total_steps > 0 else 0.0
        
        # Determine current phase based on completion and milestones
        current_phase = self._determine_current_phase(step_completion, milestones)
        
        # Calculate intelligent completion percentage
        completion_percentage = self._calculate_intelligent_completion(
            step_completion, current_phase, milestones, operation_context
        )
        
        # Estimate remaining time
        eta_seconds = self._estimate_remaining_time(
            completion_percentage, elapsed_time, operation_context
        )
        
        # Calculate confidence score
        confidence_score = self._calculate_confidence_score(
            completion_percentage, elapsed_time, operation_context
        )
        
        # Generate contextual message
        contextual_message = self._generate_contextual_message(
            current_phase, completion_percentage, operation_context
        )
        
        # Generate technical insight
        technical_insight = self._generate_technical_insight(
            current_phase, operation_context, elapsed_time
        )
        
        # Find next milestone
        next_milestone = self._find_next_milestone(completion_percentage, milestones)
        
        return ProgressIntelligence(
            operation_context=operation_context,
            milestones=milestones,
            current_phase=current_phase,
            completion_percentage=completion_percentage,
            eta_seconds=eta_seconds,
            confidence_score=confidence_score,
            contextual_message=contextual_message,
            technical_insight=technical_insight,
            next_milestone=next_milestone
        )
    
    def _determine_current_phase(self, 
                               completion: float, 
                               milestones: List[ProgressMilestone]) -> ProgressPhase:
        """Determine the current progress phase."""
        for milestone in milestones:
            if completion <= milestone.estimated_completion:
                return milestone.phase
        
        return ProgressPhase.FINALIZATION
    
    def _calculate_intelligent_completion(self,
                                        step_completion: float,
                                        current_phase: ProgressPhase,
                                        milestones: List[ProgressMilestone],
                                        context: OperationContext) -> float:
        """Calculate intelligent completion percentage with context awareness."""
        # Base completion from steps
        base_completion = step_completion
        
        # Adjust based on current phase
        phase_adjustments = {
            ProgressPhase.INITIALIZATION: 0.05,
            ProgressPhase.CONTEXT_ANALYSIS: 0.15,
            ProgressPhase.PROBLEM_DECOMPOSITION: 0.35,
            ProgressPhase.SOLUTION_GENERATION: 0.70,
            ProgressPhase.VALIDATION: 0.85,
            ProgressPhase.REFINEMENT: 0.92,
            ProgressPhase.FINALIZATION: 0.98
        }
        
        phase_base = phase_adjustments.get(current_phase, base_completion)
        
        # Blend step completion with phase-based completion
        intelligent_completion = (base_completion * 0.7) + (phase_base * 0.3)
        
        # Adjust for complexity (complex operations show progress more gradually)
        if context.complexity_level == ComplexityLevel.ADVANCED:
            intelligent_completion *= 0.9
        elif context.complexity_level == ComplexityLevel.SIMPLE:
            intelligent_completion = min(0.95, intelligent_completion * 1.1)
        
        return min(0.99, max(0.01, intelligent_completion))
    
    def _estimate_remaining_time(self,
                               completion: float,
                               elapsed_time: float,
                               context: OperationContext) -> float:
        """Estimate remaining time with intelligent analysis."""
        if completion <= 0.01:
            return context.estimated_duration
        
        # Calculate ETA based on current progress
        estimated_total_time = elapsed_time / completion
        remaining_time = estimated_total_time - elapsed_time
        
        # Adjust based on operation characteristics
        if context.complexity_level == ComplexityLevel.ADVANCED and completion < 0.5:
            # Advanced operations often take longer in the middle phases
            remaining_time *= 1.3
        elif context.operation_type == OperationType.CREATIVE_WRITING and completion > 0.7:
            # Creative work often speeds up near the end
            remaining_time *= 0.8
        
        return max(0.5, remaining_time)
    
    def _calculate_confidence_score(self,
                                  completion: float,
                                  elapsed_time: float,
                                  context: OperationContext) -> float:
        """Calculate confidence score for progress estimation."""
        base_confidence = 0.7
        
        # Higher confidence as we progress
        progress_confidence = completion * 0.3
        
        # Adjust based on operation type predictability
        type_confidence_adjustments = {
            OperationType.CHAT_CONVERSATION: 0.1,
            OperationType.CODE_ANALYSIS: 0.05,
            OperationType.PROBLEM_SOLVING: -0.05,
            OperationType.CREATIVE_WRITING: -0.1,
            OperationType.RESEARCH_ANALYSIS: -0.15
        }
        
        type_adjustment = type_confidence_adjustments.get(context.operation_type, 0)
        
        # Lower confidence for very complex operations
        complexity_adjustment = 0
        if context.complexity_level == ComplexityLevel.ADVANCED:
            complexity_adjustment = -0.1
        elif context.complexity_level == ComplexityLevel.SIMPLE:
            complexity_adjustment = 0.1
        
        confidence = base_confidence + progress_confidence + type_adjustment + complexity_adjustment
        return min(0.95, max(0.3, confidence))
    
    def _generate_contextual_message(self,
                                   current_phase: ProgressPhase,
                                   completion: float,
                                   context: OperationContext) -> str:
        """Generate contextual progress message."""
        phase_messages = {
            ProgressPhase.INITIALIZATION: "Getting started with your request...",
            ProgressPhase.CONTEXT_ANALYSIS: "Understanding the context and requirements...",
            ProgressPhase.PROBLEM_DECOMPOSITION: "Breaking down the problem into manageable parts...",
            ProgressPhase.SOLUTION_GENERATION: "Working on the solution...",
            ProgressPhase.VALIDATION: "Validating and refining the approach...",
            ProgressPhase.REFINEMENT: "Adding final touches and improvements...",
            ProgressPhase.FINALIZATION: "Almost ready with your result!"
        }
        
        base_message = phase_messages.get(current_phase, "Processing your request...")
        
        # Add operation-specific context
        if context.operation_type == OperationType.CODE_ANALYSIS:
            if current_phase == ProgressPhase.SOLUTION_GENERATION:
                base_message = "Analyzing code patterns and identifying improvements..."
        elif context.operation_type == OperationType.PROBLEM_SOLVING:
            if current_phase == ProgressPhase.PROBLEM_DECOMPOSITION:
                base_message = "Breaking down the problem and planning the solution..."
        
        # Add progress indicator
        if completion > 0.8:
            base_message = f"🎯 {base_message}"
        elif completion > 0.5:
            base_message = f"⚡ {base_message}"
        else:
            base_message = f"🧠 {base_message}"
        
        return base_message
    
    def _generate_technical_insight(self,
                                  current_phase: ProgressPhase,
                                  context: OperationContext,
                                  elapsed_time: float) -> Optional[str]:
        """Generate technical insight about the operation progress."""
        if context.complexity_level in [ComplexityLevel.SIMPLE, ComplexityLevel.MODERATE]:
            return None
        
        insights = {
            ProgressPhase.CONTEXT_ANALYSIS: f"Analyzing {len(context.key_concepts)} key concepts in {context.technical_domain or 'general'} domain",
            ProgressPhase.PROBLEM_DECOMPOSITION: f"Complex {context.operation_type.value} requiring multi-step reasoning",
            ProgressPhase.SOLUTION_GENERATION: f"Processing {context.complexity_level.value} operation with {context.user_intent} intent",
            ProgressPhase.VALIDATION: f"Validating solution quality for {context.operation_type.value} operation"
        }
        
        base_insight = insights.get(current_phase)
        if base_insight and elapsed_time > 5:
            return f"{base_insight} (taking extra time for thoroughness)"
        
        return base_insight
    
    def _find_next_milestone(self,
                           completion: float,
                           milestones: List[ProgressMilestone]) -> Optional[ProgressMilestone]:
        """Find the next milestone to reach."""
        for milestone in milestones:
            if completion < milestone.estimated_completion:
                return milestone
        return None


# Convenience function for creating the engine
def create_progress_intelligence_engine() -> ProgressIntelligenceEngine:
    """Create and return a new Progress Intelligence Engine instance."""
    return ProgressIntelligenceEngine()