"""
Pydantic Schemas for Optimization-Based Tool Selection

Defines the structure for tool optimization profiles loaded from YAML.
Includes validation and inheritance support.
"""

from typing import Dict, List, Optional, Union
from pydantic import BaseModel, Field, field_validator, model_validator


class PolicyConfig(BaseModel):
    """Policy constraints for a tool pattern"""
    
    max_cost: Optional[float] = Field(None, description="Maximum cost allowed")
    max_N_immediate: Optional[int] = Field(None, description="Max asset count for immediate execution")
    requires_approval: bool = Field(False, description="Whether approval is required")
    requires_background_if: Optional[str] = Field(None, description="Condition requiring background execution")
    production_safe: bool = Field(True, description="Whether safe for production use")
    
    @field_validator('requires_background_if')
    @classmethod
    def validate_condition(cls, v):
        """Validate condition expression"""
        if v is not None:
            # Simple validation - must contain allowed variables
            allowed_vars = ['N', 'cost', 'time_ms']
            # Just check it's a string for now - will be validated at runtime
            if not isinstance(v, str):
                raise ValueError("Condition must be a string")
        return v


class PreferenceMatchScores(BaseModel):
    """Preference match scores for optimization dimensions"""
    
    speed: float = Field(0.5, ge=0.0, le=1.0, description="Speed match score (0-1)")
    accuracy: float = Field(0.5, ge=0.0, le=1.0, description="Accuracy match score (0-1)")
    cost: float = Field(0.5, ge=0.0, le=1.0, description="Cost match score (0-1)")
    complexity: float = Field(0.5, ge=0.0, le=1.0, description="Complexity match score (0-1)")
    completeness: float = Field(0.5, ge=0.0, le=1.0, description="Completeness match score (0-1)")


class PatternProfile(BaseModel):
    """Optimization profile for a specific usage pattern"""
    
    # Pattern identification
    description: str = Field(..., description="Human-readable description")
    typical_use_cases: List[str] = Field(default_factory=list, description="Typical query patterns")
    
    # Performance estimates (can be expressions)
    time_estimate_ms: Union[str, int, float] = Field(..., description="Time estimate in ms or expression")
    cost_estimate: Union[str, int, float] = Field(1, description="Cost estimate or expression")
    complexity_score: float = Field(0.5, ge=0.0, le=1.0, description="Complexity score (0-1)")
    
    # Quality metrics
    accuracy_level: Optional[str] = Field(None, description="Accuracy level (cached, realtime, etc)")
    freshness: Optional[str] = Field(None, description="Data freshness description")
    scope: Optional[str] = Field(None, description="Result scope (single, summary, exhaustive)")
    completeness: Optional[str] = Field(None, description="Result completeness description")
    data_source: Optional[str] = Field(None, description="Data source description")
    
    # Constraints
    limitations: List[str] = Field(default_factory=list, description="Known limitations")
    requires_inputs: List[str] = Field(default_factory=list, description="Required inputs")
    
    # Policy
    policy: PolicyConfig = Field(default_factory=PolicyConfig, description="Policy constraints")
    
    # Preference matching
    preference_match: PreferenceMatchScores = Field(
        default_factory=PreferenceMatchScores,
        description="Preference match scores"
    )
    
    @field_validator('time_estimate_ms', 'cost_estimate')
    @classmethod
    def validate_expression(cls, v):
        """Validate that expression is either a number or valid string"""
        if isinstance(v, (int, float)):
            return v
        if isinstance(v, str):
            # Will be validated by SafeMathEvaluator at runtime
            return v
        raise ValueError("Must be a number or expression string")


class CapabilityProfile(BaseModel):
    """Optimization profiles for a capability"""
    
    patterns: Dict[str, PatternProfile] = Field(
        ...,
        description="Usage patterns for this capability"
    )
    
    @model_validator(mode='after')
    def validate_pattern_count(self):
        """Limit pattern count to prevent sprawl"""
        if len(self.patterns) > 5:
            raise ValueError(f"Too many patterns ({len(self.patterns)}). Max 5 per capability.")
        return self


class ToolDefaults(BaseModel):
    """Default values for a tool (inherited by patterns)"""
    
    accuracy_level: Optional[str] = None
    freshness: Optional[str] = None
    data_source: Optional[str] = None
    scope: Optional[str] = None
    completeness: Optional[str] = None


class ToolProfile(BaseModel):
    """Complete optimization profile for a tool"""
    
    description: str = Field(..., description="Tool description")
    defaults: ToolDefaults = Field(default_factory=ToolDefaults, description="Default values")
    capabilities: Dict[str, CapabilityProfile] = Field(
        ...,
        description="Capabilities and their patterns"
    )
    
    def apply_defaults(self):
        """Apply tool defaults to patterns that don't specify values"""
        for capability in self.capabilities.values():
            for pattern in capability.patterns.values():
                # Apply defaults if not specified
                if pattern.accuracy_level is None and self.defaults.accuracy_level:
                    pattern.accuracy_level = self.defaults.accuracy_level
                if pattern.freshness is None and self.defaults.freshness:
                    pattern.freshness = self.defaults.freshness
                if pattern.data_source is None and self.defaults.data_source:
                    pattern.data_source = self.defaults.data_source
                if pattern.scope is None and self.defaults.scope:
                    pattern.scope = self.defaults.scope
                if pattern.completeness is None and self.defaults.completeness:
                    pattern.completeness = self.defaults.completeness


class OptimizationProfilesConfig(BaseModel):
    """Root configuration for all tool optimization profiles"""
    
    version: str = Field("1.0", description="Schema version")
    tools: Dict[str, ToolProfile] = Field(..., description="Tool profiles")
    
    @model_validator(mode='after')
    def apply_all_defaults(self):
        """Apply defaults across all tools"""
        for tool in self.tools.values():
            tool.apply_defaults()
        return self


class UserPreferences(BaseModel):
    """User preferences for optimization"""
    
    speed_weight: float = Field(0.8, ge=0.0, le=1.0, description="Weight for speed preference")
    accuracy_weight: float = Field(0.4, ge=0.0, le=1.0, description="Weight for accuracy preference")
    cost_weight: float = Field(0.3, ge=0.0, le=1.0, description="Weight for cost preference")
    complexity_weight: float = Field(0.2, ge=0.0, le=1.0, description="Weight for complexity preference")
    completeness_weight: float = Field(0.3, ge=0.0, le=1.0, description="Weight for completeness preference")
    
    # User preference mode
    mode: str = Field("balanced", description="Preference mode: fast, balanced, accurate")
    
    @field_validator('mode')
    @classmethod
    def validate_mode(cls, v):
        """Validate preference mode"""
        allowed_modes = ['fast', 'balanced', 'accurate', 'thorough']
        if v not in allowed_modes:
            raise ValueError(f"Mode must be one of {allowed_modes}")
        return v
    
    @classmethod
    def from_mode(cls, mode: str) -> 'UserPreferences':
        """Create preferences from mode"""
        if mode == 'fast':
            return cls(
                speed_weight=1.0,
                accuracy_weight=0.3,
                cost_weight=0.8,
                complexity_weight=0.8,
                completeness_weight=0.2,
                mode='fast'
            )
        elif mode == 'accurate':
            return cls(
                speed_weight=0.3,
                accuracy_weight=1.0,
                cost_weight=0.2,
                complexity_weight=0.3,
                completeness_weight=0.9,
                mode='accurate'
            )
        elif mode == 'thorough':
            return cls(
                speed_weight=0.2,
                accuracy_weight=0.9,
                cost_weight=0.1,
                complexity_weight=0.2,
                completeness_weight=1.0,
                mode='thorough'
            )
        else:  # balanced
            return cls(
                speed_weight=0.6,
                accuracy_weight=0.6,
                cost_weight=0.5,
                complexity_weight=0.5,
                completeness_weight=0.5,
                mode='balanced'
            )


class ToolCandidate(BaseModel):
    """A candidate tool with specific usage pattern"""
    
    tool_name: str
    capability_name: str
    pattern_name: str
    
    # Estimated metrics
    time_estimate_ms: float
    cost_estimate: float
    complexity_score: float
    
    # Quality metrics
    accuracy_level: str
    freshness: str
    scope: str
    completeness: str
    
    # Policy
    policy_ok: bool
    policy_violations: List[str] = Field(default_factory=list)
    
    # Scoring
    preference_match_scores: PreferenceMatchScores
    final_score: float
    
    # Metadata
    description: str
    typical_use_cases: List[str] = Field(default_factory=list)
    limitations: List[str] = Field(default_factory=list)
    
    # Execution hints
    execution_mode_hint: Optional[str] = Field(None, description="Hint for Stage E: immediate, background, approval")
    sla_class: Optional[str] = Field(None, description="SLA class: interactive, batch, long_running")