"""
Tests for Hybrid Optimization Phase 2: Feature Normalization & Deterministic Scoring

Test Coverage:
1. FeatureNormalizer (20 tests)
   - Time normalization (log scale)
   - Cost normalization (linear scale)
   - Complexity normalization (inversion)
   - Accuracy/completeness (passthrough)
   - Denormalization (reverse transforms)
   - Edge cases and bounds

2. DeterministicScorer (20 tests)
   - Preference modes (fast, accurate, thorough, cheap, simple, balanced)
   - Score computation
   - Ranking
   - Ambiguity detection
   - Justification generation

3. PolicyEnforcer (10 tests)
   - Hard constraints (cost, production_safe, permissions, environment)
   - Soft constraints (background, approval)
   - Filtering
   - Violation reporting

Total: 50 tests
"""

import pytest
import math
from typing import Dict, Any

from pipeline.stages.stage_b.feature_normalizer import (
    FeatureNormalizer, 
    NormalizationConfig,
    normalize_features
)
from pipeline.stages.stage_b.deterministic_scorer import (
    DeterministicScorer,
    PreferenceMode,
    FeatureWeights,
    score_candidates
)
from pipeline.stages.stage_b.policy_enforcer import (
    PolicyEnforcer,
    PolicyConfig,
    PolicyViolationType,
    enforce_policies
)


# ============================================================================
# FEATURE NORMALIZER TESTS (20 tests)
# ============================================================================

class TestFeatureNormalizer:
    """Test feature normalization"""
    
    def test_normalize_time_fast(self):
        """Test time normalization for fast operations"""
        normalizer = FeatureNormalizer()
        
        # 50ms (minimum) should normalize to ~1.0 (fastest)
        normalized = normalizer._normalize_time(50.0)
        assert normalized >= 0.99
        
        # 100ms should be high (fast)
        normalized = normalizer._normalize_time(100.0)
        assert normalized >= 0.85
    
    def test_normalize_time_slow(self):
        """Test time normalization for slow operations"""
        normalizer = FeatureNormalizer()
        
        # 60s (maximum) should normalize to ~0.0 (slowest)
        normalized = normalizer._normalize_time(60000.0)
        assert normalized <= 0.01
        
        # 30s should be low (slow)
        normalized = normalizer._normalize_time(30000.0)
        assert normalized <= 0.15
    
    def test_normalize_time_medium(self):
        """Test time normalization for medium operations"""
        normalizer = FeatureNormalizer()
        
        # 500ms should be in middle-high range
        normalized = normalizer._normalize_time(500.0)
        assert 0.6 <= normalized <= 0.8
        
        # 2s should be in middle range
        normalized = normalizer._normalize_time(2000.0)
        assert 0.4 <= normalized <= 0.6
    
    def test_normalize_time_bounds(self):
        """Test time normalization respects bounds"""
        normalizer = FeatureNormalizer()
        
        # Below minimum should clamp to minimum
        normalized = normalizer._normalize_time(10.0)
        assert normalized >= 0.99
        
        # Above maximum should clamp to maximum
        normalized = normalizer._normalize_time(120000.0)
        assert normalized <= 0.01
    
    def test_normalize_cost_cheap(self):
        """Test cost normalization for cheap operations"""
        normalizer = FeatureNormalizer()
        
        # $0 (minimum) should normalize to 1.0 (cheapest)
        normalized = normalizer._normalize_cost(0.0)
        assert normalized == 1.0
        
        # $0.05 should be high (cheap)
        normalized = normalizer._normalize_cost(0.05)
        assert normalized >= 0.99
    
    def test_normalize_cost_expensive(self):
        """Test cost normalization for expensive operations"""
        normalizer = FeatureNormalizer()
        
        # $10 (maximum) should normalize to 0.0 (most expensive)
        normalized = normalizer._normalize_cost(10.0)
        assert normalized == 0.0
        
        # $5 should be in middle
        normalized = normalizer._normalize_cost(5.0)
        assert 0.45 <= normalized <= 0.55
    
    def test_normalize_cost_bounds(self):
        """Test cost normalization respects bounds"""
        normalizer = FeatureNormalizer()
        
        # Below minimum should clamp to minimum
        normalized = normalizer._normalize_cost(-1.0)
        assert normalized == 1.0
        
        # Above maximum should clamp to maximum
        normalized = normalizer._normalize_cost(20.0)
        assert normalized == 0.0
    
    def test_normalize_complexity(self):
        """Test complexity normalization (inversion)"""
        normalizer = FeatureNormalizer()
        
        # 0.0 (simple) should normalize to 1.0
        normalized = normalizer._normalize_complexity(0.0)
        assert normalized == 1.0
        
        # 1.0 (complex) should normalize to 0.0
        normalized = normalizer._normalize_complexity(1.0)
        assert normalized == 0.0
        
        # 0.3 (low complexity) should normalize to 0.7
        normalized = normalizer._normalize_complexity(0.3)
        assert abs(normalized - 0.7) < 0.01
    
    def test_normalize_accuracy_passthrough(self):
        """Test accuracy normalization (passthrough with clamping)"""
        normalizer = FeatureNormalizer()
        features = {'accuracy': 0.9}
        normalized = normalizer.normalize_features(features)
        assert normalized['accuracy'] == 0.9
    
    def test_normalize_completeness_passthrough(self):
        """Test completeness normalization (passthrough with clamping)"""
        normalizer = FeatureNormalizer()
        features = {'completeness': 0.95}
        normalized = normalizer.normalize_features(features)
        assert normalized['completeness'] == 0.95
    
    def test_normalize_all_features(self):
        """Test normalizing all features together"""
        normalizer = FeatureNormalizer()
        features = {
            'time_ms': 500.0,
            'cost': 0.05,
            'complexity': 0.3,
            'accuracy': 0.9,
            'completeness': 0.95
        }
        normalized = normalizer.normalize_features(features)
        
        # All features should be present
        assert 'time_ms' in normalized
        assert 'cost' in normalized
        assert 'complexity' in normalized
        assert 'accuracy' in normalized
        assert 'completeness' in normalized
        
        # All should be in [0,1]
        for value in normalized.values():
            assert 0.0 <= value <= 1.0
    
    def test_denormalize_time(self):
        """Test time denormalization (reverse transform)"""
        normalizer = FeatureNormalizer()
        
        # Normalize then denormalize should give original
        original = 500.0
        normalized = normalizer._normalize_time(original)
        denormalized = normalizer.denormalize_time(normalized)
        assert abs(denormalized - original) < 1.0  # Within 1ms
    
    def test_denormalize_cost(self):
        """Test cost denormalization (reverse transform)"""
        normalizer = FeatureNormalizer()
        
        # Normalize then denormalize should give original
        original = 0.05
        normalized = normalizer._normalize_cost(original)
        denormalized = normalizer.denormalize_cost(normalized)
        assert abs(denormalized - original) < 0.01  # Within 1 cent
    
    def test_custom_config(self):
        """Test custom normalization configuration"""
        config = NormalizationConfig(
            time_min_ms=100.0,
            time_max_ms=30000.0,
            cost_min=0.0,
            cost_max=5.0
        )
        normalizer = FeatureNormalizer(config)
        
        # 100ms should normalize to ~1.0
        normalized = normalizer._normalize_time(100.0)
        assert normalized >= 0.99
        
        # $5 should normalize to 0.0
        normalized = normalizer._normalize_cost(5.0)
        assert normalized == 0.0
    
    def test_convenience_function(self):
        """Test convenience function"""
        features = {'time_ms': 500.0, 'cost': 0.05}
        normalized = normalize_features(features)
        
        assert 'time_ms' in normalized
        assert 'cost' in normalized
        assert 0.0 <= normalized['time_ms'] <= 1.0
        assert 0.0 <= normalized['cost'] <= 1.0
    
    def test_partial_features(self):
        """Test normalizing partial feature sets"""
        normalizer = FeatureNormalizer()
        
        # Only time
        features = {'time_ms': 500.0}
        normalized = normalizer.normalize_features(features)
        assert 'time_ms' in normalized
        assert len(normalized) == 1
        
        # Only cost and complexity
        features = {'cost': 0.05, 'complexity': 0.3}
        normalized = normalizer.normalize_features(features)
        assert 'cost' in normalized
        assert 'complexity' in normalized
        assert len(normalized) == 2
    
    def test_empty_features(self):
        """Test normalizing empty feature set"""
        normalizer = FeatureNormalizer()
        features = {}
        normalized = normalizer.normalize_features(features)
        assert len(normalized) == 0
    
    def test_time_log_scale_property(self):
        """Test that time uses log scale (equal ratios = equal differences)"""
        normalizer = FeatureNormalizer()
        
        # 100ms -> 200ms should have similar difference as 1s -> 2s
        norm_100 = normalizer._normalize_time(100.0)
        norm_200 = normalizer._normalize_time(200.0)
        diff_1 = norm_100 - norm_200
        
        norm_1000 = normalizer._normalize_time(1000.0)
        norm_2000 = normalizer._normalize_time(2000.0)
        diff_2 = norm_1000 - norm_2000
        
        # Differences should be similar (within 10%)
        assert abs(diff_1 - diff_2) < 0.1 * max(diff_1, diff_2)
    
    def test_cost_linear_scale_property(self):
        """Test that cost uses linear scale (equal differences)"""
        normalizer = FeatureNormalizer()
        
        # $0 -> $1 should have same difference as $5 -> $6
        norm_0 = normalizer._normalize_cost(0.0)
        norm_1 = normalizer._normalize_cost(1.0)
        diff_1 = norm_0 - norm_1
        
        norm_5 = normalizer._normalize_cost(5.0)
        norm_6 = normalizer._normalize_cost(6.0)
        diff_2 = norm_5 - norm_6
        
        # Differences should be equal (within floating point error)
        assert abs(diff_1 - diff_2) < 0.01
    
    def test_all_features_higher_is_better(self):
        """Test that all normalized features follow 'higher is better' convention"""
        normalizer = FeatureNormalizer()
        
        # Fast time (50ms) should score higher than slow time (60s)
        fast_time = normalizer._normalize_time(50.0)
        slow_time = normalizer._normalize_time(60000.0)
        assert fast_time > slow_time
        
        # Cheap cost ($0) should score higher than expensive cost ($10)
        cheap_cost = normalizer._normalize_cost(0.0)
        expensive_cost = normalizer._normalize_cost(10.0)
        assert cheap_cost > expensive_cost
        
        # Simple complexity (0.0) should score higher than complex (1.0)
        simple_complexity = normalizer._normalize_complexity(0.0)
        complex_complexity = normalizer._normalize_complexity(1.0)
        assert simple_complexity > complex_complexity


# ============================================================================
# DETERMINISTIC SCORER TESTS (20 tests)
# ============================================================================

class TestDeterministicScorer:
    """Test deterministic scoring"""
    
    def test_balanced_mode_weights(self):
        """Test balanced mode has equal weights"""
        weights = FeatureWeights.from_mode(PreferenceMode.BALANCED)
        assert weights.time == 0.2
        assert weights.cost == 0.2
        assert weights.complexity == 0.2
        assert weights.accuracy == 0.2
        assert weights.completeness == 0.2
    
    def test_fast_mode_weights(self):
        """Test fast mode prioritizes time"""
        weights = FeatureWeights.from_mode(PreferenceMode.FAST)
        assert weights.time == 0.4  # Highest
        assert weights.cost == 0.15
        assert weights.complexity == 0.15
        assert weights.accuracy == 0.15
        assert weights.completeness == 0.15
    
    def test_accurate_mode_weights(self):
        """Test accurate mode prioritizes accuracy"""
        weights = FeatureWeights.from_mode(PreferenceMode.ACCURATE)
        assert weights.accuracy == 0.4  # Highest
        assert weights.time == 0.15
    
    def test_thorough_mode_weights(self):
        """Test thorough mode prioritizes completeness"""
        weights = FeatureWeights.from_mode(PreferenceMode.THOROUGH)
        assert weights.completeness == 0.4  # Highest
    
    def test_cheap_mode_weights(self):
        """Test cheap mode prioritizes cost"""
        weights = FeatureWeights.from_mode(PreferenceMode.CHEAP)
        assert weights.cost == 0.4  # Highest
    
    def test_simple_mode_weights(self):
        """Test simple mode prioritizes low complexity"""
        weights = FeatureWeights.from_mode(PreferenceMode.SIMPLE)
        assert weights.complexity == 0.4  # Highest
    
    def test_weights_sum_to_one(self):
        """Test all weight modes sum to 1.0"""
        for mode in PreferenceMode:
            weights = FeatureWeights.from_mode(mode)
            total = weights.time + weights.cost + weights.complexity + weights.accuracy + weights.completeness
            assert abs(total - 1.0) < 0.01
    
    def test_score_single_candidate(self):
        """Test scoring a single candidate"""
        scorer = DeterministicScorer()
        candidates = [
            {
                'tool_name': 'test_tool',
                'pattern': 'default',
                'features': {
                    'time_ms': 0.8,
                    'cost': 0.9,
                    'complexity': 0.7,
                    'accuracy': 0.85,
                    'completeness': 0.9
                }
            }
        ]
        
        scored = scorer.score_candidates(candidates, PreferenceMode.BALANCED)
        assert len(scored) == 1
        assert scored[0].tool_name == 'test_tool'
        assert 0.0 <= scored[0].total_score <= 1.0
    
    def test_score_computation(self):
        """Test score computation is correct"""
        scorer = DeterministicScorer()
        candidates = [
            {
                'tool_name': 'test_tool',
                'pattern': 'default',
                'features': {
                    'time_ms': 0.8,
                    'cost': 0.9,
                    'complexity': 0.7,
                    'accuracy': 0.85,
                    'completeness': 0.9
                }
            }
        ]
        
        # Balanced mode: all weights = 0.2
        scored = scorer.score_candidates(candidates, PreferenceMode.BALANCED)
        expected_score = 0.2 * 0.8 + 0.2 * 0.9 + 0.2 * 0.7 + 0.2 * 0.85 + 0.2 * 0.9
        assert abs(scored[0].total_score - expected_score) < 0.01
    
    def test_ranking_by_score(self):
        """Test candidates are ranked by score"""
        scorer = DeterministicScorer()
        candidates = [
            {
                'tool_name': 'slow_tool',
                'pattern': 'default',
                'features': {'time_ms': 0.3, 'cost': 0.9, 'complexity': 0.7, 'accuracy': 0.8, 'completeness': 0.8}
            },
            {
                'tool_name': 'fast_tool',
                'pattern': 'default',
                'features': {'time_ms': 0.9, 'cost': 0.9, 'complexity': 0.7, 'accuracy': 0.8, 'completeness': 0.8}
            }
        ]
        
        scored = scorer.score_candidates(candidates, PreferenceMode.FAST)
        
        # fast_tool should rank higher (higher time score with fast mode)
        assert scored[0].tool_name == 'fast_tool'
        assert scored[1].tool_name == 'slow_tool'
        assert scored[0].total_score > scored[1].total_score
    
    def test_preference_mode_affects_ranking(self):
        """Test different preference modes produce different rankings"""
        scorer = DeterministicScorer()
        candidates = [
            {
                'tool_name': 'fast_inaccurate',
                'pattern': 'default',
                'features': {'time_ms': 0.9, 'cost': 0.8, 'complexity': 0.7, 'accuracy': 0.6, 'completeness': 0.6}
            },
            {
                'tool_name': 'slow_accurate',
                'pattern': 'default',
                'features': {'time_ms': 0.4, 'cost': 0.8, 'complexity': 0.7, 'accuracy': 0.95, 'completeness': 0.95}
            }
        ]
        
        # Fast mode should prefer fast_inaccurate
        scored_fast = scorer.score_candidates(candidates, PreferenceMode.FAST)
        assert scored_fast[0].tool_name == 'fast_inaccurate'
        
        # Accurate mode should prefer slow_accurate
        scored_accurate = scorer.score_candidates(candidates, PreferenceMode.ACCURATE)
        assert scored_accurate[0].tool_name == 'slow_accurate'
    
    def test_justification_generation(self):
        """Test justification is generated"""
        scorer = DeterministicScorer()
        candidates = [
            {
                'tool_name': 'test_tool',
                'pattern': 'default',
                'features': {'time_ms': 0.8, 'cost': 0.9, 'complexity': 0.7, 'accuracy': 0.85, 'completeness': 0.9}
            }
        ]
        
        scored = scorer.score_candidates(candidates, PreferenceMode.BALANCED)
        assert scored[0].justification is not None
        assert len(scored[0].justification) > 0
        assert 'Score:' in scored[0].justification
    
    def test_score_gap_computation(self):
        """Test score gap computation"""
        scorer = DeterministicScorer()
        candidates = [
            {
                'tool_name': 'tool1',
                'pattern': 'default',
                'features': {'time_ms': 0.8, 'cost': 0.9, 'complexity': 0.7, 'accuracy': 0.85, 'completeness': 0.9}
            },
            {
                'tool_name': 'tool2',
                'pattern': 'default',
                'features': {'time_ms': 0.7, 'cost': 0.8, 'complexity': 0.6, 'accuracy': 0.75, 'completeness': 0.8}
            }
        ]
        
        scored = scorer.score_candidates(candidates, PreferenceMode.BALANCED)
        gap = scorer.compute_score_gap(scored)
        
        assert gap >= 0.0
        assert gap <= 1.0
        assert gap == abs(scored[0].total_score - scored[1].total_score)
    
    def test_ambiguity_detection_clear_winner(self):
        """Test ambiguity detection with clear winner"""
        scorer = DeterministicScorer()
        candidates = [
            {
                'tool_name': 'much_better',
                'pattern': 'default',
                'features': {'time_ms': 0.9, 'cost': 0.9, 'complexity': 0.9, 'accuracy': 0.9, 'completeness': 0.9}
            },
            {
                'tool_name': 'much_worse',
                'pattern': 'default',
                'features': {'time_ms': 0.3, 'cost': 0.3, 'complexity': 0.3, 'accuracy': 0.3, 'completeness': 0.3}
            }
        ]
        
        scored = scorer.score_candidates(candidates, PreferenceMode.BALANCED)
        is_ambiguous = scorer.is_ambiguous(scored, threshold=0.08)
        
        assert not is_ambiguous  # Clear winner
    
    def test_ambiguity_detection_close_scores(self):
        """Test ambiguity detection with close scores"""
        scorer = DeterministicScorer()
        candidates = [
            {
                'tool_name': 'tool1',
                'pattern': 'default',
                'features': {'time_ms': 0.80, 'cost': 0.80, 'complexity': 0.80, 'accuracy': 0.80, 'completeness': 0.80}
            },
            {
                'tool_name': 'tool2',
                'pattern': 'default',
                'features': {'time_ms': 0.79, 'cost': 0.79, 'complexity': 0.79, 'accuracy': 0.79, 'completeness': 0.79}
            }
        ]
        
        scored = scorer.score_candidates(candidates, PreferenceMode.BALANCED)
        is_ambiguous = scorer.is_ambiguous(scored, threshold=0.08)
        
        assert is_ambiguous  # Very close scores
    
    def test_custom_weights(self):
        """Test custom feature weights"""
        scorer = DeterministicScorer()
        custom_weights = FeatureWeights(
            time=0.5,
            cost=0.3,
            complexity=0.1,
            accuracy=0.05,
            completeness=0.05
        )
        
        candidates = [
            {
                'tool_name': 'test_tool',
                'pattern': 'default',
                'features': {'time_ms': 0.8, 'cost': 0.9, 'complexity': 0.7, 'accuracy': 0.85, 'completeness': 0.9}
            }
        ]
        
        scored = scorer.score_candidates(candidates, custom_weights=custom_weights)
        expected_score = 0.5 * 0.8 + 0.3 * 0.9 + 0.1 * 0.7 + 0.05 * 0.85 + 0.05 * 0.9
        assert abs(scored[0].total_score - expected_score) < 0.01
    
    def test_convenience_function(self):
        """Test convenience function"""
        candidates = [
            {
                'tool_name': 'test_tool',
                'pattern': 'default',
                'features': {'time_ms': 0.8, 'cost': 0.9, 'complexity': 0.7, 'accuracy': 0.85, 'completeness': 0.9}
            }
        ]
        
        scored = score_candidates(candidates, PreferenceMode.FAST)
        assert len(scored) == 1
        assert scored[0].tool_name == 'test_tool'
    
    def test_empty_candidates(self):
        """Test scoring empty candidate list"""
        scorer = DeterministicScorer()
        scored = scorer.score_candidates([], PreferenceMode.BALANCED)
        assert len(scored) == 0
    
    def test_single_candidate_not_ambiguous(self):
        """Test single candidate is never ambiguous"""
        scorer = DeterministicScorer()
        candidates = [
            {
                'tool_name': 'only_tool',
                'pattern': 'default',
                'features': {'time_ms': 0.5, 'cost': 0.5, 'complexity': 0.5, 'accuracy': 0.5, 'completeness': 0.5}
            }
        ]
        
        scored = scorer.score_candidates(candidates, PreferenceMode.BALANCED)
        is_ambiguous = scorer.is_ambiguous(scored, threshold=0.08)
        
        assert not is_ambiguous  # Single candidate = clear winner


# ============================================================================
# POLICY ENFORCER TESTS (10 tests)
# ============================================================================

class TestPolicyEnforcer:
    """Test policy enforcement"""
    
    def test_cost_limit_pass(self):
        """Test candidate passes cost limit"""
        enforcer = PolicyEnforcer(PolicyConfig(
            max_cost=1.0,
            environment="development",  # Don't require production_safe in dev
            require_production_safe=False
        ))
        candidate = {
            'tool_name': 'cheap_tool',
            'pattern': 'default',
            'profile': {'cost': 0.5}
        }
        
        result = enforcer.enforce_policies(candidate)
        assert result.allowed
        assert len([v for v in result.violations if v.violation_type == PolicyViolationType.COST_EXCEEDED]) == 0
    
    def test_cost_limit_fail(self):
        """Test candidate fails cost limit"""
        enforcer = PolicyEnforcer(PolicyConfig(
            max_cost=1.0,
            environment="development",
            require_production_safe=False
        ))
        candidate = {
            'tool_name': 'expensive_tool',
            'pattern': 'default',
            'profile': {'cost': 2.0}
        }
        
        result = enforcer.enforce_policies(candidate)
        assert not result.allowed
        assert any(v.violation_type == PolicyViolationType.COST_EXCEEDED for v in result.violations)
    
    def test_production_safe_pass(self):
        """Test candidate passes production_safe check"""
        enforcer = PolicyEnforcer(PolicyConfig(
            environment="production",
            require_production_safe=True
        ))
        candidate = {
            'tool_name': 'safe_tool',
            'pattern': 'default',
            'profile': {'production_safe': True}
        }
        
        result = enforcer.enforce_policies(candidate)
        assert result.allowed
    
    def test_production_safe_fail(self):
        """Test candidate fails production_safe check"""
        enforcer = PolicyEnforcer(PolicyConfig(
            environment="production",
            require_production_safe=True
        ))
        candidate = {
            'tool_name': 'unsafe_tool',
            'pattern': 'default',
            'profile': {'production_safe': False}
        }
        
        result = enforcer.enforce_policies(candidate)
        assert not result.allowed
        assert any(v.violation_type == PolicyViolationType.NOT_PRODUCTION_SAFE for v in result.violations)
    
    def test_permissions_pass(self):
        """Test candidate passes permission check"""
        enforcer = PolicyEnforcer(PolicyConfig(
            available_permissions={'read', 'write', 'execute'},
            environment="development",
            require_production_safe=False
        ))
        candidate = {
            'tool_name': 'tool',
            'pattern': 'default',
            'profile': {'required_permissions': ['read', 'write']}
        }
        
        result = enforcer.enforce_policies(candidate)
        assert result.allowed
    
    def test_permissions_fail(self):
        """Test candidate fails permission check"""
        enforcer = PolicyEnforcer(PolicyConfig(
            available_permissions={'read'},
            environment="development",
            require_production_safe=False
        ))
        candidate = {
            'tool_name': 'tool',
            'pattern': 'default',
            'profile': {'required_permissions': ['read', 'write', 'admin']}
        }
        
        result = enforcer.enforce_policies(candidate)
        assert not result.allowed
        assert any(v.violation_type == PolicyViolationType.MISSING_PERMISSION for v in result.violations)
    
    def test_requires_approval_soft_constraint(self):
        """Test requires_approval is soft constraint"""
        enforcer = PolicyEnforcer(PolicyConfig(
            environment="development",
            require_production_safe=False
        ))
        candidate = {
            'tool_name': 'tool',
            'pattern': 'default',
            'profile': {'requires_approval': True}
        }
        
        result = enforcer.enforce_policies(candidate)
        assert result.allowed  # Soft constraint doesn't filter
        assert result.requires_approval  # But flags for approval
    
    def test_filter_candidates(self):
        """Test filtering multiple candidates"""
        enforcer = PolicyEnforcer(PolicyConfig(
            max_cost=1.0,
            environment="development",
            require_production_safe=False
        ))
        candidates = [
            {'tool_name': 'cheap', 'pattern': 'default', 'profile': {'cost': 0.5}},
            {'tool_name': 'expensive', 'pattern': 'default', 'profile': {'cost': 2.0}},
            {'tool_name': 'free', 'pattern': 'default', 'profile': {'cost': 0.0}}
        ]
        
        filtered = enforcer.filter_candidates(candidates)
        
        assert len(filtered) == 2  # Only cheap and free pass
        assert filtered[0]['tool_name'] == 'cheap'
        assert filtered[1]['tool_name'] == 'free'
    
    def test_convenience_function(self):
        """Test convenience function"""
        candidate = {
            'tool_name': 'tool',
            'pattern': 'default',
            'profile': {'cost': 0.5}
        }
        
        result = enforce_policies(candidate, PolicyConfig(
            max_cost=1.0,
            environment="development",
            require_production_safe=False
        ))
        assert result.allowed
    
    def test_no_cost_limit(self):
        """Test no cost limit allows all costs"""
        enforcer = PolicyEnforcer(PolicyConfig(
            max_cost=None,
            environment="development",
            require_production_safe=False
        ))
        candidate = {
            'tool_name': 'expensive_tool',
            'pattern': 'default',
            'profile': {'cost': 100.0}
        }
        
        result = enforcer.enforce_policies(candidate)
        assert result.allowed  # No cost limit


# ============================================================================
# INTEGRATION TESTS
# ============================================================================

class TestPhase2Integration:
    """Test Phase 2 modules working together"""
    
    def test_end_to_end_pipeline(self):
        """Test complete Phase 2 pipeline: normalize -> score -> enforce"""
        # Step 1: Normalize features
        normalizer = FeatureNormalizer()
        raw_features = {
            'time_ms': 500.0,
            'cost': 0.05,
            'complexity': 0.3,
            'accuracy': 0.9,
            'completeness': 0.95
        }
        normalized = normalizer.normalize_features(raw_features)
        
        # Step 2: Score candidates
        scorer = DeterministicScorer()
        candidates = [
            {
                'tool_name': 'asset-service-query',
                'pattern': 'count',
                'features': normalized,
                'raw_features': raw_features
            }
        ]
        scored = scorer.score_candidates(candidates, PreferenceMode.FAST)
        
        # Step 3: Enforce policies
        enforcer = PolicyEnforcer(PolicyConfig(max_cost=1.0))
        candidate_with_profile = {
            'tool_name': scored[0].tool_name,
            'pattern': scored[0].pattern_name,
            'profile': {'cost': raw_features['cost'], 'production_safe': True}
        }
        policy_result = enforcer.enforce_policies(candidate_with_profile)
        
        # Verify end-to-end
        assert scored[0].total_score > 0.0
        assert policy_result.allowed
        assert not policy_result.requires_approval
    
    def test_realistic_tool_comparison(self):
        """Test realistic comparison of asset-service-query vs asset-direct-poll"""
        normalizer = FeatureNormalizer()
        scorer = DeterministicScorer()
        
        # asset-service-query (count pattern): fast, cheap, less accurate
        asq_features = normalizer.normalize_features({
            'time_ms': 500.0,
            'cost': 0.05,
            'complexity': 0.3,
            'accuracy': 0.85,  # Lower accuracy
            'completeness': 0.9
        })
        
        # asset-direct-poll (parallel pattern): slower, free, more accurate
        adp_features = normalizer.normalize_features({
            'time_ms': 2000.0,
            'cost': 0.0,
            'complexity': 0.6,
            'accuracy': 1.0,
            'completeness': 1.0
        })
        
        candidates = [
            {'tool_name': 'asset-service-query', 'pattern': 'count', 'features': asq_features},
            {'tool_name': 'asset-direct-poll', 'pattern': 'parallel', 'features': adp_features}
        ]
        
        # Fast mode should prefer asset-service-query (time weight = 0.4)
        scored_fast = scorer.score_candidates(candidates, PreferenceMode.FAST)
        assert scored_fast[0].tool_name == 'asset-service-query'
        
        # Accurate mode should prefer asset-direct-poll (accuracy weight = 0.4)
        scored_accurate = scorer.score_candidates(candidates, PreferenceMode.ACCURATE)
        assert scored_accurate[0].tool_name == 'asset-direct-poll'


if __name__ == '__main__':
    pytest.main([__file__, '-v'])