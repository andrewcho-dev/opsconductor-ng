"""
Hybrid Orchestrator - Integrates all optimization modules

Coordinates the hybrid optimization system:
1. Preference Detection (Phase 3)
2. Candidate Enumeration (Phase 3)
3. Policy Enforcement (Phase 2)
4. Feature Normalization (Phase 2)
5. Deterministic Scoring (Phase 2)
6. Ambiguity Detection (Phase 4)
7. LLM Tie-Breaking (Phase 4)

This is the main entry point for the hybrid optimization system.
"""

import logging
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict

from .profile_loader import ProfileLoader
from .preference_detector import PreferenceDetector
from .candidate_enumerator import CandidateEnumerator, ToolCandidate
from .feature_normalizer import FeatureNormalizer
from .policy_enforcer import PolicyEnforcer, PolicyConfig
from .deterministic_scorer import DeterministicScorer, ScoredCandidate, PreferenceMode
from .ambiguity_detector import AmbiguityDetector
from .llm_tie_breaker import LLMTieBreaker

logger = logging.getLogger(__name__)


@dataclass
class ToolSelectionResult:
    """Result of hybrid tool selection"""
    
    # Selected tool
    tool_name: str
    capability_name: str
    pattern_name: str
    
    # Execution hints
    execution_mode_hint: str  # "immediate", "background", "approval_required"
    sla_class: str  # "interactive", "batch", "background"
    
    # Justification
    justification: str
    
    # Estimates
    estimated_time_ms: float
    estimated_cost: float
    
    # Alternatives
    alternatives: List[str]  # List of alternative tool names
    
    # Selection metadata
    selection_method: str  # "deterministic" or "llm_tiebreaker"
    is_ambiguous: bool
    clarifying_question: Optional[str] = None
    
    # Scoring details
    final_score: float = 0.0
    num_candidates: int = 0
    num_policy_violations: int = 0


class HybridOrchestrator:
    """
    Hybrid Orchestrator - Main entry point for optimization-based tool selection
    
    Coordinates all optimization modules to select the best tool for a query.
    Uses deterministic scoring when possible, LLM tie-breaking when ambiguous.
    """
    
    def __init__(
        self,
        profile_loader: Optional[ProfileLoader] = None,
        llm_client: Optional[Any] = None,
        telemetry_logger: Optional[Any] = None
    ):
        """
        Initialize hybrid orchestrator
        
        Args:
            profile_loader: Profile loader (creates default if None)
            llm_client: LLM client for tie-breaking (optional)
            telemetry_logger: Telemetry logger (optional)
        """
        self.profile_loader = profile_loader or ProfileLoader()
        self.preference_detector = PreferenceDetector()
        self.candidate_enumerator = CandidateEnumerator(self.profile_loader)
        self.feature_normalizer = FeatureNormalizer()
        self.policy_enforcer = PolicyEnforcer()
        self.deterministic_scorer = DeterministicScorer()
        self.ambiguity_detector = AmbiguityDetector()
        self.llm_tie_breaker = LLMTieBreaker(llm_client) if llm_client else None
        self.telemetry_logger = telemetry_logger
        
        logger.info("HybridOrchestrator initialized")
    
    async def select_tool(
        self,
        query: str,
        required_capabilities: List[str],
        context: Dict[str, Any],
        explicit_mode: Optional[str] = None
    ) -> ToolSelectionResult:
        """
        Select the best tool for a query using hybrid approach
        
        Args:
            query: User query text
            required_capabilities: List of required capabilities (from Stage A)
            context: Runtime context (N, pages, p95_latency, etc.)
            explicit_mode: Optional explicit preference mode (fast/balanced/accurate/thorough)
        
        Returns:
            ToolSelectionResult with selected tool and metadata
        
        Raises:
            ValueError: If no viable tools found or all violate policies
        """
        logger.info(f"Selecting tool for query: {query[:50]}...")
        
        # Step 1: Detect preferences
        preference_mode = self.preference_detector.detect_preference(query, explicit_mode)
        logger.debug(f"Detected preference mode: {preference_mode.value}")
        
        # Step 2: Enumerate candidates
        candidates = self.candidate_enumerator.enumerate_candidates(
            required_capabilities, context
        )
        logger.debug(f"Enumerated {len(candidates)} candidates")
        
        if not candidates:
            raise ValueError(
                f"No viable tools found for capabilities: {required_capabilities}"
            )
        
        # Step 3: Enforce policies
        # Create policy config from context
        policy_config = PolicyConfig(
            max_cost=context.get('cost_limit'),  # None if not specified
            environment=context.get('environment', 'production'),
            require_production_safe=context.get('require_production_safe', True)
        )
        
        # Create policy enforcer with context-specific config
        policy_enforcer = PolicyEnforcer(policy_config)
        
        # Convert candidates to dict format for policy enforcement
        candidate_dicts_for_policy = []
        for candidate in candidates:
            candidate_dict = {
                'tool_name': candidate.tool_name,
                'pattern': candidate.pattern_name,
                'profile': {
                    'cost': candidate.estimated_cost,
                    'production_safe': True,  # Assume all tools are production safe
                    'required_permissions': []  # No special permissions required
                },
                'context': context
            }
            candidate_dicts_for_policy.append((candidate, candidate_dict))
        
        # Filter candidates by policies
        allowed_candidates = []
        violations = []
        
        for candidate, candidate_dict in candidate_dicts_for_policy:
            result = policy_enforcer.enforce_policies(candidate_dict)
            
            if result.allowed:
                allowed_candidates.append(candidate)
            else:
                violations.append({
                    'candidate': candidate,
                    'reason': result.filtered_reason
                })
        
        logger.debug(
            f"Policy enforcement: {len(allowed_candidates)} allowed, "
            f"{len(violations)} violations"
        )
        
        if not allowed_candidates:
            raise ValueError(
                f"All candidates violate policies. "
                f"Violations: {[v['reason'] for v in violations]}"
            )
        
        # Step 4: Score candidates (convert to dicts with normalized features)
        candidate_dicts = []
        for candidate in allowed_candidates:
            # Normalize features
            normalized_features = self.feature_normalizer.normalize_features({
                'time_ms': candidate.estimated_time_ms,
                'cost': candidate.estimated_cost,
                'complexity': candidate.complexity,
                'accuracy': candidate.accuracy,
                'completeness': candidate.completeness
            })
            
            # Convert to dict format expected by scorer
            candidate_dict = {
                'tool_name': candidate.tool_name,
                'pattern': candidate.pattern_name,
                'features': normalized_features,
                'raw_features': {'candidate': candidate}  # Keep reference to original
            }
            candidate_dicts.append(candidate_dict)
        
        scored_candidates = self.deterministic_scorer.score_candidates(
            candidate_dicts, preference_mode
        )
        logger.debug(
            f"Scored candidates: top score={scored_candidates[0].total_score:.3f}"
        )
        
        # Step 5: Detect ambiguity
        ambiguity_result = self.ambiguity_detector.detect_ambiguity(scored_candidates)
        is_ambiguous = ambiguity_result.is_ambiguous
        clarifying_question = ambiguity_result.clarifying_question
        
        logger.debug(f"Ambiguity detection: is_ambiguous={is_ambiguous}")
        
        # Step 6: Break tie if ambiguous
        if is_ambiguous and self.llm_tie_breaker:
            logger.info("Ambiguous case detected, using LLM tie-breaker")
            # Convert ScoredCandidate objects to dicts for LLM tie-breaker
            tie_result = await self.llm_tie_breaker.break_tie(
                query, asdict(scored_candidates[0]), asdict(scored_candidates[1])
            )
            # tie_result.chosen_candidate is a dict, need to find matching ScoredCandidate
            winner_tool_name = tie_result.chosen_candidate['tool_name']
            winner = next(c for c in scored_candidates if c.tool_name == winner_tool_name)
            justification = tie_result.justification
            selection_method = "llm_tiebreaker"
        else:
            # Use deterministic winner
            winner = scored_candidates[0]
            justification = self._generate_deterministic_justification(
                winner, preference_mode
            )
            selection_method = "deterministic"
            
            if is_ambiguous and not self.llm_tie_breaker:
                logger.warning(
                    "Ambiguous case detected but no LLM client available, "
                    "using deterministic winner"
                )
        
        logger.info(
            f"Selected: {winner.tool_name}.{winner.pattern_name} "
            f"(method={selection_method})"
        )
        
        # Step 7: Log telemetry
        if self.telemetry_logger:
            self.telemetry_logger.log_selection(
                query=query,
                preference_mode=preference_mode,
                candidates=scored_candidates,
                winner=winner,
                selection_method=selection_method,
                is_ambiguous=is_ambiguous
            )
        
        # Step 8: Build result
        # Get original candidate from raw_features (we stored it there)
        winner_candidate = winner.raw_features.get('candidate')
        if not winner_candidate:
            # Fallback: find it from allowed_candidates
            winner_candidate = next(
                (c for c in allowed_candidates 
                 if c.tool_name == winner.tool_name and c.pattern_name == winner.pattern_name),
                allowed_candidates[0]  # Fallback to first
            )
        
        # Derive execution hints from candidate
        execution_mode_hint = self._derive_execution_mode(winner_candidate)
        sla_class = self._derive_sla_class(winner_candidate)
        
        result = ToolSelectionResult(
            tool_name=winner.tool_name,
            capability_name=winner_candidate.capability_name,
            pattern_name=winner.pattern_name,
            execution_mode_hint=execution_mode_hint,
            sla_class=sla_class,
            justification=justification,
            estimated_time_ms=winner_candidate.estimated_time_ms,
            estimated_cost=winner_candidate.estimated_cost,
            alternatives=[
                f"{c.tool_name}.{c.pattern_name}"
                for c in scored_candidates[1:4]  # Top 3 alternatives
            ],
            selection_method=selection_method,
            is_ambiguous=is_ambiguous,
            clarifying_question=clarifying_question,
            final_score=winner.total_score,
            num_candidates=len(candidates),
            num_policy_violations=len(violations)
        )
        
        return result
    
    def _generate_deterministic_justification(
        self,
        winner: ScoredCandidate,
        preference_mode: PreferenceMode
    ) -> str:
        """
        Generate justification for deterministic selection
        
        Args:
            winner: Winning candidate
            preference_mode: User preference mode
        
        Returns:
            Human-readable justification string
        """
        # Map preference mode to dominant dimension
        mode_to_dimension = {
            PreferenceMode.FAST: "speed",
            PreferenceMode.ACCURATE: "accuracy",
            PreferenceMode.THOROUGH: "completeness",
            PreferenceMode.CHEAP: "cost",
            PreferenceMode.SIMPLE: "complexity",
            PreferenceMode.BALANCED: "balanced"
        }
        dominant = mode_to_dimension.get(preference_mode, "balanced")
        
        # Get raw features from winner
        raw_features = winner.raw_features
        
        # Generate justification based on dominant preference
        justifications = {
            "speed": (
                f"Selected for fast response time. "
                f"Optimized for speed preference."
            ),
            "accuracy": (
                f"Selected for high accuracy. "
                f"Provides reliable data."
            ),
            "cost": (
                f"Selected for low cost. "
                f"Most economical option."
            ),
            "complexity": (
                f"Selected for simplicity. "
                f"Easy to use and understand."
            ),
            "completeness": (
                f"Selected for comprehensive results. "
                f"Provides complete coverage."
            ),
            "balanced": (
                f"Selected based on balanced optimization across all dimensions."
            )
        }
        
        base_justification = justifications.get(
            dominant,
            f"Selected based on overall score ({winner.total_score:.2f})"
        )
        
        return base_justification
    
    def _derive_execution_mode(self, candidate: ToolCandidate) -> str:
        """
        Derive execution mode hint from candidate
        
        Args:
            candidate: Tool candidate
        
        Returns:
            Execution mode: "immediate", "background", or "approval_required"
        """
        # Check policy for approval requirement
        if candidate.policy.requires_approval:
            return "approval_required"
        
        # Check if background execution is required
        if candidate.policy.requires_background_if:
            # For now, assume immediate unless explicitly requires approval
            # TODO: Evaluate requires_background_if condition
            pass
        
        # Check estimated time (> 5 seconds suggests background)
        if candidate.estimated_time_ms > 5000:
            return "background"
        
        return "immediate"
    
    def _derive_sla_class(self, candidate: ToolCandidate) -> str:
        """
        Derive SLA class from candidate
        
        Args:
            candidate: Tool candidate
        
        Returns:
            SLA class: "interactive", "batch", or "background"
        """
        # Based on estimated time
        if candidate.estimated_time_ms < 1000:  # < 1 second
            return "interactive"
        elif candidate.estimated_time_ms < 10000:  # < 10 seconds
            return "batch"
        else:
            return "background"