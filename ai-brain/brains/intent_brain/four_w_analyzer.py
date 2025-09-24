"""
4W Framework Intent Analyzer - Systematic Intent Analysis

This module implements the 4W framework for analyzing user intents:
- WHAT: What action/outcome do they want? (with root cause analysis)
- WHERE/WHAT: What target/scope is involved?
- WHEN: When should this happen?
- HOW: How should it be executed?

Focuses on operational action understanding and resource complexity rather than
traditional ITIL process categorization.
"""

import logging
import json
from typing import Dict, Any, List, Optional, Tuple
from enum import Enum
from dataclasses import dataclass
from datetime import datetime

logger = logging.getLogger(__name__)

class ActionType(Enum):
    """Core action types based on resource complexity and operational needs"""
    INFORMATION = "information"      # Knowledge base queries, status checks (lightweight)
    OPERATIONAL = "operational"      # Standard system operations (standard orchestration)
    DIAGNOSTIC = "diagnostic"        # Problem analysis and resolution (specialized resources)
    PROVISIONING = "provisioning"    # Resource creation and allocation (heavy orchestration)

class ScopeLevel(Enum):
    """Scope levels for target analysis"""
    SINGLE_SYSTEM = "single_system"     # Individual server/service
    CLUSTER = "cluster"                 # Group of related systems
    ENVIRONMENT = "environment"         # Dev/staging/prod environment
    ORG_WIDE = "org_wide"              # Organization-wide impact

class UrgencyLevel(Enum):
    """Urgency levels for timing analysis"""
    LOW = "low"           # Can wait, flexible timing
    MEDIUM = "medium"     # Should be done soon
    HIGH = "high"         # Needs immediate attention
    CRITICAL = "critical" # Emergency, drop everything

class MethodType(Enum):
    """Execution method preferences"""
    AUTOMATED = "automated"   # Fully automated execution preferred
    GUIDED = "guided"         # Guided/assisted execution
    MANUAL = "manual"         # Manual execution required
    HYBRID = "hybrid"         # Mix of automated and manual steps

class TimelineType(Enum):
    """Timeline categories"""
    IMMEDIATE = "immediate"       # Right now
    SCHEDULED = "scheduled"       # Specific time/date
    MAINTENANCE = "maintenance"   # During maintenance window
    FLEXIBLE = "flexible"         # When convenient

@dataclass
class WhatAnalysis:
    """WHAT dimension analysis - Action and outcome understanding"""
    action_type: ActionType
    specific_outcome: str
    root_need: str
    surface_request: str
    confidence: float
    reasoning: str

@dataclass
class WhereWhatAnalysis:
    """WHERE/WHAT dimension analysis - Target and scope understanding"""
    target_systems: List[str]
    scope_level: ScopeLevel
    affected_components: List[str]
    dependencies: List[str]
    confidence: float
    reasoning: str

@dataclass
class WhenAnalysis:
    """WHEN dimension analysis - Timing and urgency understanding"""
    urgency: UrgencyLevel
    timeline_type: TimelineType
    specific_timeline: Optional[str]
    scheduling_constraints: List[str]
    business_hours_required: bool
    confidence: float
    reasoning: str

@dataclass
class HowAnalysis:
    """HOW dimension analysis - Execution method and constraints"""
    method_preference: MethodType
    execution_constraints: List[str]
    approval_required: bool
    rollback_needed: bool
    testing_required: bool
    confidence: float
    reasoning: str

@dataclass
class FourWAnalysis:
    """Complete 4W Framework Analysis Result"""
    # Individual dimension analyses
    what_analysis: WhatAnalysis
    where_what_analysis: WhereWhatAnalysis
    when_analysis: WhenAnalysis
    how_analysis: HowAnalysis
    
    # Overall analysis
    overall_confidence: float
    missing_information: List[str]
    clarifying_questions: List[str]
    
    # Resource requirements (derived from 4W analysis)
    resource_complexity: str  # LOW, MEDIUM, HIGH
    estimated_effort: str     # MINUTES, HOURS, DAYS
    required_capabilities: List[str]
    
    # Risk assessment
    risk_level: str
    risk_factors: List[str]
    
    # Metadata
    analysis_timestamp: datetime
    processing_time: float

class FourWAnalyzer:
    """
    4W Framework Analyzer - Systematic intent analysis using the 4W approach
    
    Analyzes user requests through four key dimensions:
    - WHAT: Action type and root need analysis
    - WHERE/WHAT: Target identification and scope determination  
    - WHEN: Urgency and timeline analysis
    - HOW: Method preferences and execution constraints
    """
    
    def __init__(self, llm_engine=None):
        """Initialize the 4W analyzer with LLM engine."""
        self.llm_engine = llm_engine
        self.analysis_history = []
        
        # Build system prompts for each dimension
        self.what_prompt = self._build_what_prompt()
        self.where_what_prompt = self._build_where_what_prompt()
        self.when_prompt = self._build_when_prompt()
        self.how_prompt = self._build_how_prompt()
    
    async def analyze_4w(self, user_message: str, context: Optional[Dict] = None) -> FourWAnalysis:
        """
        Perform complete 4W analysis of user intent.
        
        Args:
            user_message: The user's natural language request
            context: Optional context information
            
        Returns:
            FourWAnalysis with complete systematic analysis
        """
        start_time = datetime.now()
        
        try:
            logger.info(f"Starting 4W analysis: {user_message[:100]}...")
            
            # Analyze each dimension
            what_analysis = await self._analyze_what(user_message, context)
            where_what_analysis = await self._analyze_where_what(user_message, context)
            when_analysis = await self._analyze_when(user_message, context)
            how_analysis = await self._analyze_how(user_message, context)
            
            # Calculate overall confidence
            overall_confidence = self._calculate_overall_confidence(
                what_analysis.confidence,
                where_what_analysis.confidence,
                when_analysis.confidence,
                how_analysis.confidence
            )
            
            # Identify missing information across all dimensions
            missing_information = self._identify_missing_information(
                what_analysis, where_what_analysis, when_analysis, how_analysis
            )
            
            # Generate clarifying questions
            clarifying_questions = self._generate_clarifying_questions(
                what_analysis, where_what_analysis, when_analysis, how_analysis, missing_information
            )
            
            # Derive resource requirements
            resource_complexity, estimated_effort, required_capabilities = self._derive_resource_requirements(
                what_analysis, where_what_analysis, when_analysis, how_analysis
            )
            
            # Assess risk
            risk_level, risk_factors = self._assess_risk(
                what_analysis, where_what_analysis, when_analysis, how_analysis
            )
            
            processing_time = (datetime.now() - start_time).total_seconds()
            
            analysis = FourWAnalysis(
                what_analysis=what_analysis,
                where_what_analysis=where_what_analysis,
                when_analysis=when_analysis,
                how_analysis=how_analysis,
                overall_confidence=overall_confidence,
                missing_information=missing_information,
                clarifying_questions=clarifying_questions,
                resource_complexity=resource_complexity,
                estimated_effort=estimated_effort,
                required_capabilities=required_capabilities,
                risk_level=risk_level,
                risk_factors=risk_factors,
                analysis_timestamp=start_time,
                processing_time=processing_time
            )
            
            logger.info(f"4W analysis completed in {processing_time:.2f}s - "
                       f"Confidence: {overall_confidence:.2%}")
            
            return analysis
            
        except Exception as e:
            logger.error(f"4W analysis failed: {e}")
            # NO FALLBACK - FAIL HARD AS REQUESTED
            raise Exception(f"4W Framework analysis FAILED - NO FALLBACK ALLOWED: {e}")
    
    async def _analyze_what(self, message: str, context: Optional[Dict]) -> WhatAnalysis:
        """Analyze the WHAT dimension - action type and root need using LLM intelligence."""
        if not self.llm_engine:
            raise Exception("LLM engine required for 4W analysis - NO FALLBACKS ALLOWED")
        return await self._llm_analyze_what(message, context)
    
    async def _analyze_where_what(self, message: str, context: Optional[Dict]) -> WhereWhatAnalysis:
        """Analyze the WHERE/WHAT dimension - targets and scope using LLM intelligence."""
        if not self.llm_engine:
            raise Exception("LLM engine required for 4W analysis - NO FALLBACKS ALLOWED")
        return await self._llm_analyze_where_what(message, context)
    
    async def _analyze_when(self, message: str, context: Optional[Dict]) -> WhenAnalysis:
        """Analyze the WHEN dimension - timing and urgency using LLM intelligence."""
        if not self.llm_engine:
            raise Exception("LLM engine required for 4W analysis - NO FALLBACKS ALLOWED")
        return await self._llm_analyze_when(message, context)
    
    async def _analyze_how(self, message: str, context: Optional[Dict]) -> HowAnalysis:
        """Analyze the HOW dimension - execution method and constraints using LLM intelligence."""
        if not self.llm_engine:
            raise Exception("LLM engine required for 4W analysis - NO FALLBACKS ALLOWED")
        return await self._llm_analyze_how(message, context)
    

    
    def _calculate_overall_confidence(self, what_conf: float, where_conf: float, 
                                    when_conf: float, how_conf: float) -> float:
        """Calculate overall confidence from dimension confidences."""
        # Weighted average with emphasis on WHAT (most important)
        return (what_conf * 0.4 + where_conf * 0.25 + when_conf * 0.2 + how_conf * 0.15)
    
    def _identify_missing_information(self, what: WhatAnalysis, where_what: WhereWhatAnalysis,
                                    when: WhenAnalysis, how: HowAnalysis) -> List[str]:
        """Identify missing information across all dimensions."""
        missing = []
        
        # WHAT dimension gaps
        if what.confidence < 0.7:
            missing.append("WHAT: Action type or desired outcome unclear")
        
        # WHERE/WHAT dimension gaps
        if not where_what.target_systems:
            missing.append("WHERE: Target systems not specified")
        if where_what.confidence < 0.7:
            missing.append("WHERE: Scope or affected components unclear")
        
        # WHEN dimension gaps
        if when.timeline_type == TimelineType.SCHEDULED and not when.specific_timeline:
            missing.append("WHEN: Specific timeline not provided")
        if when.confidence < 0.7:
            missing.append("WHEN: Timing requirements unclear")
        
        # HOW dimension gaps
        if how.confidence < 0.7:
            missing.append("HOW: Execution method or constraints unclear")
        
        return missing
    
    def _generate_clarifying_questions(self, what: WhatAnalysis, where_what: WhereWhatAnalysis,
                                     when: WhenAnalysis, how: HowAnalysis, 
                                     missing: List[str]) -> List[str]:
        """Generate clarifying questions based on missing information."""
        questions = []
        
        # Questions based on missing information
        for missing_item in missing:
            if "WHAT:" in missing_item:
                questions.append("Could you clarify what specific outcome you're trying to achieve?")
            elif "WHERE:" in missing_item and "Target systems" in missing_item:
                questions.append("Which specific systems or services should this apply to?")
            elif "WHERE:" in missing_item and "Scope" in missing_item:
                questions.append("What's the scope of this request - single system, environment, or organization-wide?")
            elif "WHEN:" in missing_item and "timeline" in missing_item:
                questions.append("When do you need this completed? Do you have a specific deadline?")
            elif "HOW:" in missing_item:
                questions.append("Do you have any preferences for how this should be executed (automated vs manual)?")
        
        # Additional context-specific questions
        if what.action_type == ActionType.DIAGNOSTIC and not where_what.target_systems:
            questions.append("What symptoms or errors are you experiencing, and on which systems?")
        
        if what.action_type == ActionType.PROVISIONING and when.urgency == UrgencyLevel.LOW:
            questions.append("Are there any specific requirements or constraints for the new resources?")
        
        return list(set(questions))  # Remove duplicates
    
    def _derive_resource_requirements(self, what: WhatAnalysis, where_what: WhereWhatAnalysis,
                                    when: WhenAnalysis, how: HowAnalysis) -> Tuple[str, str, List[str]]:
        """Derive resource requirements from 4W analysis."""
        # Resource complexity based on action type and scope
        complexity_score = 0
        
        # Action type complexity
        action_complexity = {
            ActionType.INFORMATION: 1,
            ActionType.OPERATIONAL: 2,
            ActionType.DIAGNOSTIC: 3,
            ActionType.PROVISIONING: 4
        }
        complexity_score += action_complexity[what.action_type]
        
        # Scope complexity
        scope_complexity = {
            ScopeLevel.SINGLE_SYSTEM: 1,
            ScopeLevel.CLUSTER: 2,
            ScopeLevel.ENVIRONMENT: 3,
            ScopeLevel.ORG_WIDE: 4
        }
        complexity_score += scope_complexity[where_what.scope_level]
        
        # Urgency complexity
        urgency_complexity = {
            UrgencyLevel.LOW: 0,
            UrgencyLevel.MEDIUM: 1,
            UrgencyLevel.HIGH: 2,
            UrgencyLevel.CRITICAL: 3
        }
        complexity_score += urgency_complexity[when.urgency]
        
        # Determine resource complexity
        if complexity_score <= 3:
            resource_complexity = "LOW"
            estimated_effort = "MINUTES"
        elif complexity_score <= 6:
            resource_complexity = "MEDIUM"
            estimated_effort = "HOURS"
        else:
            resource_complexity = "HIGH"
            estimated_effort = "DAYS"
        
        # Required capabilities
        capabilities = []
        if what.action_type == ActionType.DIAGNOSTIC:
            capabilities.extend(["System diagnostics", "Troubleshooting expertise"])
        if what.action_type == ActionType.PROVISIONING:
            capabilities.extend(["Resource provisioning", "Configuration management"])
        if where_what.scope_level in [ScopeLevel.ENVIRONMENT, ScopeLevel.ORG_WIDE]:
            capabilities.append("Multi-system orchestration")
        if when.urgency in [UrgencyLevel.HIGH, UrgencyLevel.CRITICAL]:
            capabilities.append("Emergency response procedures")
        
        return resource_complexity, estimated_effort, capabilities
    
    def _assess_risk(self, what: WhatAnalysis, where_what: WhereWhatAnalysis,
                    when: WhenAnalysis, how: HowAnalysis) -> Tuple[str, List[str]]:
        """Assess risk based on 4W analysis."""
        risk_score = 0
        risk_factors = []
        
        # Action type risk
        if what.action_type in [ActionType.OPERATIONAL, ActionType.PROVISIONING]:
            risk_score += 2
            risk_factors.append("System modification involved")
        
        # Scope risk
        if where_what.scope_level in [ScopeLevel.ENVIRONMENT, ScopeLevel.ORG_WIDE]:
            risk_score += 3
            risk_factors.append("Wide scope of impact")
        
        # Urgency risk
        if when.urgency == UrgencyLevel.CRITICAL:
            risk_score += 2
            risk_factors.append("High urgency may lead to rushed execution")
        
        # Method risk
        if how.method_preference == MethodType.MANUAL:
            risk_score += 1
            risk_factors.append("Manual execution increases error risk")
        
        # Determine risk level
        if risk_score <= 2:
            risk_level = "LOW"
        elif risk_score <= 5:
            risk_level = "MEDIUM"
        else:
            risk_level = "HIGH"
        
        return risk_level, risk_factors
    
    # FALLBACK METHOD REMOVED - NO FALLBACKS ALLOWED
    
    def _build_what_prompt(self) -> str:
        """Build system prompt for WHAT dimension analysis."""
        return """You are analyzing the WHAT dimension of a user request. Determine:

1. ACTION TYPE (based on resource complexity):
   - INFORMATION: Knowledge queries, status checks (lightweight resources)
   - OPERATIONAL: Standard system operations (standard orchestration)
   - DIAGNOSTIC: Problem analysis and resolution (specialized resources)
   - PROVISIONING: Resource creation and allocation (heavy orchestration)

2. SPECIFIC OUTCOME: What exactly they want to achieve

3. ROOT NEED: What they REALLY need (not just surface request)
   - Look for underlying business drivers
   - Distinguish symptoms from root causes
   - Consider "why" they're asking for this

Respond with JSON containing action_type, specific_outcome, root_need, surface_request, confidence, and reasoning."""
    
    def _build_where_what_prompt(self) -> str:
        """Build system prompt for WHERE/WHAT dimension analysis."""
        return """You are analyzing the WHERE/WHAT dimension of a user request. Determine:

1. TARGET SYSTEMS: Specific systems, services, or components mentioned
2. SCOPE LEVEL:
   - SINGLE_SYSTEM: Individual server/service
   - CLUSTER: Group of related systems
   - ENVIRONMENT: Dev/staging/prod environment
   - ORG_WIDE: Organization-wide impact

3. AFFECTED COMPONENTS: What will be impacted
4. DEPENDENCIES: What other systems might be affected

Respond with JSON containing target_systems, scope_level, affected_components, dependencies, confidence, and reasoning."""
    
    def _build_when_prompt(self) -> str:
        """Build system prompt for WHEN dimension analysis."""
        return """You are analyzing the WHEN dimension of a user request. Determine:

1. URGENCY LEVEL:
   - LOW: Can wait, flexible timing
   - MEDIUM: Should be done soon
   - HIGH: Needs immediate attention
   - CRITICAL: Emergency, drop everything

2. TIMELINE TYPE:
   - IMMEDIATE: Right now
   - SCHEDULED: Specific time/date
   - MAINTENANCE: During maintenance window
   - FLEXIBLE: When convenient

3. SPECIFIC TIMELINE: If mentioned
4. SCHEDULING CONSTRAINTS: Any timing restrictions
5. BUSINESS HOURS REQUIRED: Whether this needs to be done during business hours

Respond with JSON containing urgency, timeline_type, specific_timeline, scheduling_constraints, business_hours_required, confidence, and reasoning."""
    
    def _build_how_prompt(self) -> str:
        """Build system prompt for HOW dimension analysis."""
        return """You are analyzing the HOW dimension of a user request. Determine:

1. METHOD PREFERENCE:
   - AUTOMATED: Fully automated execution preferred
   - GUIDED: Guided/assisted execution
   - MANUAL: Manual execution required
   - HYBRID: Mix of automated and manual steps

2. EXECUTION CONSTRAINTS: Any limitations or requirements
3. APPROVAL REQUIRED: Whether approvals are needed
4. ROLLBACK NEEDED: Whether rollback capability is required
5. TESTING REQUIRED: Whether testing is needed

Respond with JSON containing method_preference, execution_constraints, approval_required, rollback_needed, testing_required, confidence, and reasoning."""

    async def _llm_analyze_what(self, message: str, context: Optional[Dict]) -> WhatAnalysis:
        """LLM-powered WHAT analysis using actual LLM intelligence."""
        # Build the analysis prompt
        system_prompt = self._build_what_prompt()
        user_prompt = f"Analyze this user request: '{message}'"
        
        # Get LLM response
        response = await self.llm_engine.generate_response(
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            max_tokens=500,
            temperature=0.1  # Low temperature for consistent analysis
        )
        
        # Parse JSON response
        import json
        result = json.loads(response)
        
        # Map action type string to enum
        action_type_str = result.get('action_type', 'OPERATIONAL').upper()
        action_type = ActionType(action_type_str.lower())
        
        return WhatAnalysis(
            action_type=action_type,
            specific_outcome=result.get('specific_outcome', 'Perform requested action'),
            root_need=result.get('root_need', 'Address user requirement'),
            surface_request=message,
            confidence=float(result.get('confidence', 0.8)),
            reasoning=result.get('reasoning', 'LLM-based analysis')
        )
    
    async def _llm_analyze_where_what(self, message: str, context: Optional[Dict]) -> WhereWhatAnalysis:
        """LLM-powered WHERE/WHAT analysis using actual LLM intelligence."""
        # Build the analysis prompt
        system_prompt = self._build_where_what_prompt()
        user_prompt = f"Analyze this user request: '{message}'"
        
        # Get LLM response
        response = await self.llm_engine.generate_response(
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            max_tokens=500,
            temperature=0.1  # Low temperature for consistent analysis
        )
        
        # Parse JSON response
        import json
        result = json.loads(response)
        
        # Map scope level string to enum
        scope_level_str = result.get('scope_level', 'SINGLE_SYSTEM').upper()
        scope_level = ScopeLevel(scope_level_str.lower())
        
        return WhereWhatAnalysis(
            target_systems=result.get('target_systems', []),
            scope_level=scope_level,
            affected_components=result.get('affected_components', []),
            dependencies=result.get('dependencies', []),
            confidence=float(result.get('confidence', 0.8)),
            reasoning=result.get('reasoning', 'LLM-based analysis')
        )
    
    async def _llm_analyze_when(self, message: str, context: Optional[Dict]) -> WhenAnalysis:
        """LLM-powered WHEN analysis using actual LLM intelligence."""
        # Build the analysis prompt
        system_prompt = self._build_when_prompt()
        user_prompt = f"Analyze this user request: '{message}'"
        
        # Get LLM response
        response = await self.llm_engine.generate_response(
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            max_tokens=500,
            temperature=0.1  # Low temperature for consistent analysis
        )
        
        # Parse JSON response
        import json
        result = json.loads(response)
        
        # Map enum values
        urgency_str = result.get('urgency', 'MEDIUM').upper()
        urgency = UrgencyLevel(urgency_str.lower())
        
        timeline_type_str = result.get('timeline_type', 'FLEXIBLE').upper()
        timeline_type = TimelineType(timeline_type_str.lower())
        
        return WhenAnalysis(
            urgency=urgency,
            timeline_type=timeline_type,
            specific_timeline=result.get('specific_timeline'),
            scheduling_constraints=result.get('scheduling_constraints', []),
            business_hours_required=result.get('business_hours_required', False),
            confidence=float(result.get('confidence', 0.8)),
            reasoning=result.get('reasoning', 'LLM-based analysis')
        )
    
    async def _llm_analyze_how(self, message: str, context: Optional[Dict]) -> HowAnalysis:
        """LLM-powered HOW analysis using actual LLM intelligence."""
        # Build the analysis prompt
        system_prompt = self._build_how_prompt()
        user_prompt = f"Analyze this user request: '{message}'"
        
        # Get LLM response
        response = await self.llm_engine.generate_response(
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            max_tokens=500,
            temperature=0.1  # Low temperature for consistent analysis
        )
        
        # Parse JSON response
        import json
        result = json.loads(response)
        
        # Map method preference string to enum
        method_str = result.get('method_preference', 'AUTOMATED').upper()
        method_preference = MethodType(method_str.lower())
        
        return HowAnalysis(
            method_preference=method_preference,
            execution_constraints=result.get('execution_constraints', []),
            approval_required=result.get('approval_required', False),
            rollback_needed=result.get('rollback_needed', False),
            testing_required=result.get('testing_required', False),
            confidence=float(result.get('confidence', 0.8)),
            reasoning=result.get('reasoning', 'LLM-based analysis')
        )