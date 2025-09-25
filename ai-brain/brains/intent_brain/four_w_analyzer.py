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
import re
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


def extract_json_from_llm_response(response_text: str) -> Optional[Dict[str, Any]]:
    """
    Extract and parse JSON from LLM response text.
    
    LLMs often return JSON wrapped in explanatory text or with formatting issues.
    This function attempts multiple strategies to extract valid JSON.
    
    Args:
        response_text: Raw text response from LLM
        
    Returns:
        Parsed JSON dict if successful, None if no valid JSON found
    """
    if not response_text or not response_text.strip():
        return None
    
    # Log the raw response for debugging JSON parsing issues
    logger.debug(f"Attempting to parse LLM response: {response_text[:500]}...")
    
    # Strategy 1: Try parsing the entire response as JSON
    try:
        parsed = json.loads(response_text.strip())
        # Only return dictionaries, not lists
        if isinstance(parsed, dict):
            logger.debug("Successfully parsed entire response as JSON")
            return parsed
    except json.JSONDecodeError as e:
        logger.debug(f"Failed to parse entire response as JSON: {e}")
        pass
    
    # Strategy 2: Look for JSON blocks between ```json and ``` or ``` and ```
    json_block_patterns = [
        r'```json\s*(\{.*?\})\s*```',
        r'```\s*(\{.*?\})\s*```',
        r'```json\s*(\[.*?\])\s*```',
        r'```\s*(\[.*?\])\s*```'
    ]
    
    for pattern in json_block_patterns:
        matches = re.findall(pattern, response_text, re.DOTALL | re.IGNORECASE)
        for match in matches:
            try:
                parsed = json.loads(match.strip())
                # Only return dictionaries, not lists
                if isinstance(parsed, dict):
                    logger.debug("Successfully parsed JSON from code block")
                    return parsed
            except json.JSONDecodeError as e:
                logger.debug(f"Failed to parse JSON from code block: {e}")
                continue
    
    # Strategy 3: Find JSON objects/arrays in the text with enhanced cleaning
    json_patterns = [
        r'\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\}',  # Simple nested objects
        r'\{.*?\}',  # Any object (greedy)
        r'\[.*?\]'   # Any array (greedy)
    ]
    
    for pattern in json_patterns:
        matches = re.findall(pattern, response_text, re.DOTALL)
        for match in matches:
            try:
                # Enhanced cleaning for common LLM JSON issues
                cleaned = match.strip()
                
                # Remove trailing commas before closing braces/brackets
                cleaned = re.sub(r',(\s*[}\]])', r'\1', cleaned)
                
                # Remove comments (// style)
                cleaned = re.sub(r'//.*?$', '', cleaned, flags=re.MULTILINE)
                
                # Remove comments (/* */ style)
                cleaned = re.sub(r'/\*.*?\*/', '', cleaned, flags=re.DOTALL)
                
                # Fix common LLM mistakes: missing quotes around keys
                cleaned = re.sub(r'(\w+)(\s*:\s*)', r'"\1"\2', cleaned)
                
                # Fix single quotes to double quotes
                cleaned = re.sub(r"'([^']*)'", r'"\1"', cleaned)
                
                # Fix boolean values
                cleaned = re.sub(r'\btrue\b', 'true', cleaned, flags=re.IGNORECASE)
                cleaned = re.sub(r'\bfalse\b', 'false', cleaned, flags=re.IGNORECASE)
                cleaned = re.sub(r'\bnull\b', 'null', cleaned, flags=re.IGNORECASE)
                
                # Remove any remaining non-JSON text before/after the JSON
                cleaned = re.sub(r'^[^{]*(\{.*\})[^}]*$', r'\1', cleaned, flags=re.DOTALL)
                
                logger.debug(f"Attempting to parse cleaned JSON: {cleaned[:200]}...")
                parsed = json.loads(cleaned)
                # Only return dictionaries, not lists
                if isinstance(parsed, dict):
                    logger.debug("Successfully parsed JSON after cleaning")
                    return parsed
            except json.JSONDecodeError as e:
                logger.debug(f"Failed to parse cleaned JSON: {e}")
                continue
    
    # Strategy 4: Try to extract key-value pairs and build JSON
    try:
        # Look for patterns like "key": "value" or 'key': 'value'
        kv_pattern = r'["\']([^"\']+)["\']\s*:\s*["\']([^"\']+)["\']'
        matches = re.findall(kv_pattern, response_text)
        if matches:
            result = {}
            for key, value in matches:
                # Try to convert numeric values
                try:
                    if '.' in value:
                        result[key] = float(value)
                    else:
                        result[key] = int(value)
                except ValueError:
                    # Keep as string if not numeric
                    result[key] = value
            if result:
                logger.debug("Successfully extracted key-value pairs")
                return result
    except Exception as e:
        logger.debug(f"Failed to extract key-value pairs: {e}")
        pass
    
    # Strategy 5: Last resort - try to fix common JSON syntax errors
    try:
        # Look for the most likely JSON structure in the response
        json_match = re.search(r'\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\}', response_text, re.DOTALL)
        if json_match:
            potential_json = json_match.group(0)
            
            # Apply aggressive fixes
            fixed_json = potential_json
            
            # Fix missing commas between key-value pairs
            fixed_json = re.sub(r'"\s*\n\s*"', '",\n"', fixed_json)
            
            # Fix missing quotes around string values
            fixed_json = re.sub(r':\s*([a-zA-Z_][a-zA-Z0-9_]*)\s*([,}])', r': "\1"\2', fixed_json)
            
            # Fix array syntax issues
            fixed_json = re.sub(r'\[\s*([^"\[\]]+)\s*\]', r'["\1"]', fixed_json)
            
            logger.debug(f"Attempting to parse aggressively fixed JSON: {fixed_json[:200]}...")
            parsed = json.loads(fixed_json)
            if isinstance(parsed, dict):
                logger.debug("Successfully parsed aggressively fixed JSON")
                return parsed
                
    except Exception as e:
        logger.debug(f"Failed to parse aggressively fixed JSON: {e}")
        pass
    
    logger.warning(f"All JSON parsing strategies failed for response: {response_text[:200]}...")
    return None


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
    
    def _parse_scope_level(self, scope_level_str: str) -> ScopeLevel:
        """
        Safely parse scope level string to enum, handling LLM formatting issues.
        
        Args:
            scope_level_str: Raw scope level string from LLM
            
        Returns:
            ScopeLevel enum value
        """
        try:
            # Handle None or empty values
            if not scope_level_str:
                logger.warning("Empty scope level string, defaulting to SINGLE_SYSTEM")
                return ScopeLevel.SINGLE_SYSTEM
                
            # Clean up the string
            scope_level_str = str(scope_level_str).strip().upper()
            
            # Handle cases where LLM returns multiple values separated by |
            if '|' in scope_level_str:
                # Take the first valid option
                options = scope_level_str.split('|')
                for option in options:
                    option = option.strip()
                    if option in ['SINGLE_SYSTEM', 'CLUSTER', 'ENVIRONMENT', 'ORG_WIDE']:
                        scope_level_str = option
                        break
                else:
                    # If no valid option found, default to SINGLE_SYSTEM
                    logger.warning(f"No valid scope level found in '{scope_level_str}', defaulting to SINGLE_SYSTEM")
                    scope_level_str = 'SINGLE_SYSTEM'
            
            # Handle common variations and typos
            scope_mapping = {
                'SINGLE_SYSTEM': 'SINGLE_SYSTEM',
                'SINGLE': 'SINGLE_SYSTEM',
                'SYSTEM': 'SINGLE_SYSTEM',
                'CLUSTER': 'CLUSTER',
                'GROUP': 'CLUSTER',
                'ENVIRONMENT': 'ENVIRONMENT',
                'ENV': 'ENVIRONMENT',
                'ORG_WIDE': 'ORG_WIDE',
                'ORGANIZATION': 'ORG_WIDE',
                'WIDE': 'ORG_WIDE',
                'GLOBAL': 'ORG_WIDE'
            }
            
            # Try to map the value
            mapped_value = scope_mapping.get(scope_level_str, scope_level_str)
            
            # Validate it's a known value
            if mapped_value not in ['SINGLE_SYSTEM', 'CLUSTER', 'ENVIRONMENT', 'ORG_WIDE']:
                logger.warning(f"Unknown scope level '{scope_level_str}', defaulting to SINGLE_SYSTEM")
                mapped_value = 'SINGLE_SYSTEM'
            
            # Map to enum value
            return ScopeLevel(mapped_value.lower())
            
        except (ValueError, AttributeError) as e:
            logger.error(f"Failed to parse scope level '{scope_level_str}': {e}")
            logger.warning("Falling back to SINGLE_SYSTEM due to parsing error")
            return ScopeLevel.SINGLE_SYSTEM
    
    def _parse_action_type(self, action_type_str: str) -> ActionType:
        """Safely parse action type string to enum, handling LLM formatting issues."""
        try:
            # Handle None or empty values
            if not action_type_str:
                logger.warning("Empty action type string, defaulting to INFORMATION")
                return ActionType.INFORMATION
                
            action_type_str = str(action_type_str).strip().upper()
            
            # Handle pipe-separated values
            if '|' in action_type_str:
                options = action_type_str.split('|')
                for option in options:
                    option = option.strip()
                    if option in ['INFORMATION', 'OPERATIONAL', 'DIAGNOSTIC', 'PROVISIONING']:
                        action_type_str = option
                        break
                else:
                    logger.warning(f"No valid action type found in '{action_type_str}', defaulting to INFORMATION")
                    action_type_str = 'INFORMATION'
            
            # Handle common variations and typos
            action_mapping = {
                'INFORMATION': 'INFORMATION',
                'INFO': 'INFORMATION',
                'QUERY': 'INFORMATION',
                'GET': 'INFORMATION',
                'OPERATIONAL': 'OPERATIONAL',
                'OPERATION': 'OPERATIONAL',
                'OPS': 'OPERATIONAL',
                'DIAGNOSTIC': 'DIAGNOSTIC',
                'DIAGNOSE': 'DIAGNOSTIC',
                'DEBUG': 'DIAGNOSTIC',
                'TROUBLESHOOT': 'DIAGNOSTIC',
                'PROVISIONING': 'PROVISIONING',
                'PROVISION': 'PROVISIONING',
                'CREATE': 'PROVISIONING',
                'DEPLOY': 'PROVISIONING'
            }
            
            # Try to map the value
            mapped_value = action_mapping.get(action_type_str, action_type_str)
            
            # Validate it's a known value
            if mapped_value not in ['INFORMATION', 'OPERATIONAL', 'DIAGNOSTIC', 'PROVISIONING']:
                logger.warning(f"Unknown action type '{action_type_str}', defaulting to INFORMATION")
                mapped_value = 'INFORMATION'
            
            return ActionType(mapped_value.lower())
            
        except (ValueError, AttributeError) as e:
            logger.error(f"Failed to parse action type '{action_type_str}': {e}")
            logger.warning("Falling back to INFORMATION due to parsing error")
            return ActionType.INFORMATION
    
    def _parse_urgency_level(self, urgency_str: str) -> UrgencyLevel:
        """Safely parse urgency level string to enum, handling LLM formatting issues."""
        try:
            # Handle None or empty values
            if not urgency_str:
                logger.warning("Empty urgency level string, defaulting to LOW")
                return UrgencyLevel.LOW
                
            urgency_str = str(urgency_str).strip().upper()
            
            # Handle pipe-separated values
            if '|' in urgency_str:
                options = urgency_str.split('|')
                for option in options:
                    option = option.strip()
                    if option in ['LOW', 'MEDIUM', 'HIGH', 'CRITICAL']:
                        urgency_str = option
                        break
                else:
                    logger.warning(f"No valid urgency level found in '{urgency_str}', defaulting to LOW")
                    urgency_str = 'LOW'
            
            # Handle common variations and typos
            urgency_mapping = {
                'LOW': 'LOW',
                'MEDIUM': 'MEDIUM',
                'MED': 'MEDIUM',
                'MODERATE': 'MEDIUM',
                'HIGH': 'HIGH',
                'URGENT': 'HIGH',
                'CRITICAL': 'CRITICAL',
                'EMERGENCY': 'CRITICAL',
                'IMMEDIATE': 'CRITICAL'
            }
            
            # Try to map the value
            mapped_value = urgency_mapping.get(urgency_str, urgency_str)
            
            # Validate it's a known value
            if mapped_value not in ['LOW', 'MEDIUM', 'HIGH', 'CRITICAL']:
                logger.warning(f"Unknown urgency level '{urgency_str}', defaulting to LOW")
                mapped_value = 'LOW'
            
            return UrgencyLevel(mapped_value.lower())
            
        except (ValueError, AttributeError) as e:
            logger.error(f"Failed to parse urgency level '{urgency_str}': {e}")
            logger.warning("Falling back to LOW due to parsing error")
            return UrgencyLevel.LOW
    
    def _parse_timeline_type(self, timeline_str: str) -> TimelineType:
        """Safely parse timeline type string to enum, handling LLM formatting issues."""
        try:
            # Handle None or empty values
            if not timeline_str:
                logger.warning("Empty timeline type string, defaulting to FLEXIBLE")
                return TimelineType.FLEXIBLE
                
            timeline_str = str(timeline_str).strip().upper()
            
            # Handle pipe-separated values
            if '|' in timeline_str:
                options = timeline_str.split('|')
                for option in options:
                    option = option.strip()
                    if option in ['IMMEDIATE', 'SCHEDULED', 'MAINTENANCE', 'FLEXIBLE']:
                        timeline_str = option
                        break
                else:
                    logger.warning(f"No valid timeline type found in '{timeline_str}', defaulting to FLEXIBLE")
                    timeline_str = 'FLEXIBLE'
            
            # Handle common variations and typos
            timeline_mapping = {
                'IMMEDIATE': 'IMMEDIATE',
                'NOW': 'IMMEDIATE',
                'ASAP': 'IMMEDIATE',
                'URGENT': 'IMMEDIATE',
                'SCHEDULED': 'SCHEDULED',
                'SCHEDULE': 'SCHEDULED',
                'PLANNED': 'SCHEDULED',
                'MAINTENANCE': 'MAINTENANCE',
                'MAINT': 'MAINTENANCE',
                'WINDOW': 'MAINTENANCE',
                'FLEXIBLE': 'FLEXIBLE',
                'FLEX': 'FLEXIBLE',
                'ANYTIME': 'FLEXIBLE',
                'WHENEVER': 'FLEXIBLE'
            }
            
            # Try to map the value
            mapped_value = timeline_mapping.get(timeline_str, timeline_str)
            
            # Validate it's a known value
            if mapped_value not in ['IMMEDIATE', 'SCHEDULED', 'MAINTENANCE', 'FLEXIBLE']:
                logger.warning(f"Unknown timeline type '{timeline_str}', defaulting to FLEXIBLE")
                mapped_value = 'FLEXIBLE'
            
            return TimelineType(mapped_value.lower())
            
        except (ValueError, AttributeError) as e:
            logger.error(f"Failed to parse timeline type '{timeline_str}': {e}")
            logger.warning("Falling back to FLEXIBLE due to parsing error")
            return TimelineType.FLEXIBLE
    
    def _parse_method_type(self, method_str: str) -> MethodType:
        """Safely parse method type string to enum, handling LLM formatting issues."""
        try:
            # Handle None or empty values
            if not method_str:
                logger.warning("Empty method type string, defaulting to AUTOMATED")
                return MethodType.AUTOMATED
                
            method_str = str(method_str).strip().upper()
            
            # Handle pipe-separated values
            if '|' in method_str:
                options = method_str.split('|')
                for option in options:
                    option = option.strip()
                    if option in ['AUTOMATED', 'GUIDED', 'MANUAL', 'HYBRID']:
                        method_str = option
                        break
                else:
                    logger.warning(f"No valid method type found in '{method_str}', defaulting to AUTOMATED")
                    method_str = 'AUTOMATED'
            
            # Handle common variations and typos
            method_mapping = {
                'AUTOMATED': 'AUTOMATED',
                'AUTO': 'AUTOMATED',
                'AUTOMATIC': 'AUTOMATED',
                'GUIDED': 'GUIDED',
                'GUIDE': 'GUIDED',
                'ASSISTED': 'GUIDED',
                'MANUAL': 'MANUAL',
                'HAND': 'MANUAL',
                'HUMAN': 'MANUAL',
                'HYBRID': 'HYBRID',
                'MIXED': 'HYBRID',
                'COMBINED': 'HYBRID'
            }
            
            # Try to map the value
            mapped_value = method_mapping.get(method_str, method_str)
            
            # Validate it's a known value
            if mapped_value not in ['AUTOMATED', 'GUIDED', 'MANUAL', 'HYBRID']:
                logger.warning(f"Unknown method type '{method_str}', defaulting to AUTOMATED")
                mapped_value = 'AUTOMATED'
            
            return MethodType(mapped_value.lower())
            
        except (ValueError, AttributeError) as e:
            logger.error(f"Failed to parse method type '{method_str}': {e}")
            logger.warning("Falling back to AUTOMATED due to parsing error")
            return MethodType.AUTOMATED
    
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
            missing_information = await self._identify_missing_information(
                user_message, what_analysis, where_what_analysis, when_analysis, how_analysis
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
    
    async def _identify_missing_information(self, message: str, what: WhatAnalysis, where_what: WhereWhatAnalysis,
                                    when: WhenAnalysis, how: HowAnalysis) -> List[str]:
        """Use LLM to intelligently identify missing information instead of hardcoded patterns."""
        missing = []
        
        # Use LLM to analyze if information is truly missing
        if hasattr(self, 'llm_engine') and self.llm_engine:
            try:
                analysis_prompt = f"""Analyze this user request to determine if any critical information is missing for creating an automated job/task.

User request: "{message}"

Current analysis results:
- WHAT: {what.action_type} (confidence: {what.confidence}) - {what.reasoning}
- WHERE: {where_what.target_systems} (confidence: {where_what.confidence}) - {where_what.reasoning}  
- WHEN: {when.timeline_type} - {when.specific_timeline} (confidence: {when.confidence}) - {when.reasoning}
- HOW: {how.method_preference} (confidence: {how.confidence}) - {how.reasoning}

Determine if any of these dimensions are truly missing or unclear from the original request. Only flag something as missing if it's genuinely needed and not derivable from context.

For example:
- "every day" clearly specifies timing
- "critical" clearly specifies a threshold condition  
- "disk space" clearly specifies what to monitor
- "windows machines" clearly specifies target systems

Respond with JSON only:
{{
    "missing_information": [
        // Only include items that are genuinely missing and needed
        // Format: "DIMENSION: specific missing detail"
    ],
    "reasoning": "brief explanation of what is/isn't missing"
}}"""

                response_data = await self.llm_engine.generate(analysis_prompt)
                response = response_data.get("generated_text", "")
                
                import json
                import re
                json_match = re.search(r'\{.*\}', response, re.DOTALL)
                if json_match:
                    analysis = json.loads(json_match.group())
                    missing = analysis.get("missing_information", [])
                    logger.info(f"🧠 LLM missing info analysis: {analysis.get('reasoning', 'No reasoning')}")
                    return missing
                    
            except Exception as e:
                logger.error(f"🧠 LLM missing info analysis FAILED: {e} - NO FALLBACKS ALLOWED")
                raise Exception(f"Missing information analysis FAILED - NO FALLBACK ALLOWED: {e}")
        
        # If we get here, LLM engine is not available
        raise Exception("LLM engine required for missing information analysis - NO FALLBACKS ALLOWED")
    
    def _generate_clarifying_questions(self, what: WhatAnalysis, where_what: WhereWhatAnalysis,
                                     when: WhenAnalysis, how: HowAnalysis, 
                                     missing: List[str]) -> List[str]:
        """Generate clarifying questions based on missing information with enhanced specificity."""
        questions = []
        
        # Questions based on missing information
        for missing_item in missing:
            if "WHAT:" in missing_item:
                if "outcome" in missing_item:
                    questions.append("Could you clarify what specific outcome you're trying to achieve?")
                elif "Monitoring criteria" in missing_item:
                    questions.append("What specific values should be monitored and what thresholds should trigger alerts?")
                elif "Monitoring thresholds" in missing_item:
                    questions.append("What are the acceptable ranges for the values you want to monitor? When should I alert you?")
            elif "WHERE:" in missing_item and "Target systems" in missing_item:
                questions.append("Which specific systems or services should this apply to?")
            elif "WHERE:" in missing_item and "Scope" in missing_item:
                questions.append("What's the scope of this request - single system, environment, or organization-wide?")
            elif "WHEN:" in missing_item:
                if "Recurrence interval" in missing_item:
                    questions.append("How often should this recurring job run? (e.g., every hour, every 30 minutes, daily)")
                elif "timeline" in missing_item:
                    questions.append("When do you need this completed? Do you have a specific deadline?")
                elif "Timing requirements" in missing_item:
                    questions.append("When should this be executed? Is this urgent or can it be scheduled?")
            elif "HOW:" in missing_item:
                questions.append("Do you have any preferences for how this should be executed (automated vs manual)?")
        
        # Additional context-specific questions
        if what.action_type == ActionType.DIAGNOSTIC and not where_what.target_systems:
            questions.append("What symptoms or errors are you experiencing, and on which systems?")
        
        if what.action_type == ActionType.PROVISIONING and when.urgency == UrgencyLevel.LOW:
            questions.append("Are there any specific requirements or constraints for the new resources?")
        
        # Enhanced questions for monitoring/recurring tasks
        if ("recurring" in what.reasoning.lower() or 
            "monitor" in what.reasoning.lower() or 
            "check" in what.reasoning.lower()):
            
            # SFP monitoring specific questions
            if ("sfp" in what.reasoning.lower() or 
                "rx" in what.reasoning.lower() or 
                "tx" in what.reasoning.lower()):
                questions.append("What are the acceptable dBm ranges for RX and TX power levels? At what point should I alert you?")
                questions.append("Should I alert on any specific conditions like high error rates or signal degradation?")
        
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
        
        # Required capabilities - only add if actually needed
        capabilities = []
        if what.action_type == ActionType.DIAGNOSTIC:
            capabilities.append("System diagnostics")
        elif what.action_type == ActionType.PROVISIONING:
            capabilities.append("Resource provisioning")
        elif what.action_type == ActionType.INFORMATION:
            capabilities.append("Information retrieval")
        # Only add orchestration for truly complex multi-system operations
        if where_what.scope_level == ScopeLevel.ORG_WIDE and what.action_type != ActionType.INFORMATION:
            capabilities.append("Multi-system orchestration")
        
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

1. ACTION TYPE (based on what they're asking for):
   - INFORMATION: Knowledge queries, status checks, counts, reports
   - OPERATIONAL: System operations, changes, configurations
   - DIAGNOSTIC: Problem analysis, troubleshooting, investigation
   - PROVISIONING: Creating new resources, deployments, installations

2. SPECIFIC OUTCOME: What exactly they want to achieve (be literal, don't elaborate)

3. ROOT NEED: The basic need behind the request (keep it simple, don't over-analyze)

IMPORTANT: 
- Only describe what is EXPLICITLY stated in the request
- Do NOT invent details, assumptions, or business drivers not mentioned
- Keep descriptions concise and factual
- If something is unclear, state that rather than guessing

Respond with ONLY valid JSON in this exact format:
{
  "action_type": "INFORMATION",
  "specific_outcome": "exactly what they asked for",
  "root_need": "basic need without speculation",
  "confidence": 0.8,
  "reasoning": "brief explanation based only on what was stated"
}

Choose ONE action_type from: INFORMATION, OPERATIONAL, DIAGNOSTIC, PROVISIONING"""
    
    def _build_where_what_prompt(self) -> str:
        """Build system prompt for WHERE/WHAT dimension analysis."""
        return """You are analyzing the WHERE/WHAT dimension of a user request. Determine:

1. TARGET SYSTEMS: Only systems/services explicitly mentioned (use empty array if none specified)
2. SCOPE LEVEL:
   - SINGLE_SYSTEM: Individual server/service mentioned
   - CLUSTER: Group of related systems mentioned
   - ENVIRONMENT: Dev/staging/prod environment mentioned
   - ORG_WIDE: Organization-wide scope mentioned or implied by the request

3. AFFECTED COMPONENTS: Only components explicitly mentioned (use empty array if none)
4. DEPENDENCIES: Only dependencies explicitly mentioned (use empty array if none)

IMPORTANT: 
- Only include what is EXPLICITLY mentioned in the request
- Do NOT assume or invent systems, components, or dependencies
- Use empty arrays [] when nothing is specified
- Base scope_level on what the request actually asks for

Respond with ONLY valid JSON in this exact format:
{
  "target_systems": [],
  "scope_level": "ORG_WIDE",
  "affected_components": [],
  "dependencies": [],
  "confidence": 0.8,
  "reasoning": "brief explanation based only on what was stated"
}

Choose ONE scope_level from: SINGLE_SYSTEM, CLUSTER, ENVIRONMENT, ORG_WIDE"""
    
    def _build_when_prompt(self) -> str:
        """Build system prompt for WHEN dimension analysis."""
        return """You are analyzing the WHEN dimension of a user request. Determine:

1. URGENCY LEVEL (based only on explicit urgency indicators):
   - LOW: No urgency mentioned, routine request
   - MEDIUM: Some urgency indicated
   - HIGH: Urgent language used
   - CRITICAL: Emergency language used

2. TIMELINE TYPE (based only on what's stated):
   - IMMEDIATE: "now", "immediately", "right away" mentioned
   - SCHEDULED: Specific time/date mentioned
   - MAINTENANCE: Maintenance window mentioned
   - FLEXIBLE: No specific timing mentioned

3. SPECIFIC TIMELINE: Only if explicitly mentioned (use null if not)
4. SCHEDULING CONSTRAINTS: Only explicit constraints mentioned (use empty array if none)
5. BUSINESS HOURS REQUIRED: Only if explicitly mentioned (default to false)

IMPORTANT: 
- Only analyze timing information that is EXPLICITLY stated
- Do NOT assume urgency or timing requirements
- Use defaults for information requests: LOW urgency, FLEXIBLE timeline
- Use empty arrays [] and null for unspecified information

Respond with ONLY valid JSON in this exact format:
{
  "urgency": "LOW",
  "timeline_type": "FLEXIBLE",
  "specific_timeline": null,
  "scheduling_constraints": [],
  "business_hours_required": false,
  "confidence": 0.8,
  "reasoning": "brief explanation based only on what was stated"
}

Choose ONE urgency from: LOW, MEDIUM, HIGH, CRITICAL
Choose ONE timeline_type from: IMMEDIATE, SCHEDULED, MAINTENANCE, FLEXIBLE"""
    
    def _build_how_prompt(self) -> str:
        """Build system prompt for HOW dimension analysis."""
        return """You are analyzing the HOW dimension of a user request. Determine:

1. METHOD PREFERENCE (based only on what's stated):
   - AUTOMATED: Automation explicitly requested or implied by request type
   - GUIDED: Guided execution requested
   - MANUAL: Manual execution requested
   - HYBRID: Mix explicitly requested

2. EXECUTION CONSTRAINTS: Only explicit constraints mentioned (use empty array if none)
3. APPROVAL REQUIRED: Only if explicitly mentioned (default to false)
4. ROLLBACK NEEDED: Only if explicitly mentioned (default to false)
5. TESTING REQUIRED: Only if explicitly mentioned (default to false)

IMPORTANT: 
- Only analyze execution information that is EXPLICITLY stated
- Do NOT assume method preferences, constraints, or requirements
- For information requests, default to AUTOMATED method
- Use empty arrays [] and false for unspecified information

Respond with ONLY valid JSON in this exact format:
{
  "method_preference": "AUTOMATED",
  "execution_constraints": [],
  "approval_required": false,
  "rollback_needed": false,
  "testing_required": false,
  "confidence": 0.8,
  "reasoning": "brief explanation based only on what was stated"
}

Choose ONE method_preference from: AUTOMATED, GUIDED, MANUAL, HYBRID"""

    async def _llm_analyze_what(self, message: str, context: Optional[Dict]) -> WhatAnalysis:
        """LLM-powered WHAT analysis using actual LLM intelligence."""
        # Build the analysis prompt
        system_prompt = self._build_what_prompt()
        user_prompt = f"Analyze this user request: '{message}'"
        
        # Get LLM response
        full_prompt = f"{system_prompt}\n\n{user_prompt}"
        response_data = await self.llm_engine.generate(
            prompt=full_prompt
        )
        
        # Parse JSON response using robust extraction
        result = extract_json_from_llm_response(response_data["generated_text"])
        
        if result is None:
            logger.error(f"Failed to extract JSON from LLM response for WHAT analysis - NO FALLBACKS ALLOWED")
            logger.debug(f"Raw LLM response: {response_data['generated_text']}")
            raise Exception("WHAT analysis JSON parsing FAILED - NO FALLBACK ALLOWED")
        
        # Map action type string to enum with robust parsing
        action_type_str = result.get('action_type', 'INFORMATION')
        action_type = self._parse_action_type(action_type_str)
        
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
        full_prompt = f"{system_prompt}\n\n{user_prompt}"
        response_data = await self.llm_engine.generate(
            prompt=full_prompt
        )
        
        # Parse JSON response using robust extraction
        result = extract_json_from_llm_response(response_data["generated_text"])
        
        if result is None:
            logger.error(f"Failed to extract JSON from LLM response for WHERE/WHAT analysis - NO FALLBACKS ALLOWED")
            logger.debug(f"Raw LLM response: {response_data['generated_text']}")
            raise Exception("WHERE/WHAT analysis JSON parsing FAILED - NO FALLBACK ALLOWED")
        
        # Map scope level string to enum with robust parsing
        scope_level_str = result.get('scope_level', 'SINGLE_SYSTEM').upper()
        scope_level = self._parse_scope_level(scope_level_str)
        
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
        full_prompt = f"{system_prompt}\n\n{user_prompt}"
        response_data = await self.llm_engine.generate(
            prompt=full_prompt
        )
        
        # Parse JSON response using robust extraction
        result = extract_json_from_llm_response(response_data["generated_text"])
        
        if result is None:
            logger.error(f"Failed to extract JSON from LLM response for WHEN analysis - NO FALLBACKS ALLOWED")
            logger.debug(f"Raw LLM response: {response_data['generated_text']}")
            raise Exception("WHEN analysis JSON parsing FAILED - NO FALLBACK ALLOWED")
        
        # Map enum values with robust parsing
        urgency_str = result.get('urgency', 'MEDIUM')
        urgency = self._parse_urgency_level(urgency_str)
        
        timeline_type_str = result.get('timeline_type', 'FLEXIBLE')
        timeline_type = self._parse_timeline_type(timeline_type_str)
        
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
        full_prompt = f"{system_prompt}\n\n{user_prompt}"
        response_data = await self.llm_engine.generate(
            prompt=full_prompt
        )
        
        # Parse JSON response using robust extraction
        result = extract_json_from_llm_response(response_data["generated_text"])
        
        if result is None:
            logger.error(f"Failed to extract JSON from LLM response for HOW analysis - NO FALLBACKS ALLOWED")
            logger.debug(f"Raw LLM response: {response_data['generated_text']}")
            raise Exception("HOW analysis JSON parsing FAILED - NO FALLBACK ALLOWED")
        
        # Map method preference string to enum with robust parsing
        method_str = result.get('method_preference', 'AUTOMATED')
        method_preference = self._parse_method_type(method_str)
        
        return HowAnalysis(
            method_preference=method_preference,
            execution_constraints=result.get('execution_constraints', []),
            approval_required=result.get('approval_required', False),
            rollback_needed=result.get('rollback_needed', False),
            testing_required=result.get('testing_required', False),
            confidence=float(result.get('confidence', 0.8)),
            reasoning=result.get('reasoning', 'LLM-based analysis')
        )