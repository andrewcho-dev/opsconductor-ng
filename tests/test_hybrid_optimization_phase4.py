"""
Tests for Hybrid Optimization Phase 4: Ambiguity Detection & LLM Tie-Breaker

This phase handles edge cases where deterministic scoring is ambiguous.
When top-2 candidates have scores within 8% of each other, we delegate to LLM.

Test Coverage:
1. Ambiguity Detector (15 tests)
   - Clear winner detection
   - Ambiguous case detection
   - Clarifying question generation
   - Edge cases (single candidate, identical scores)
   - Custom epsilon threshold
   
2. LLM Tie-Breaker (10 tests)
   - Successful tie-breaking
   - JSON response parsing
   - Fallback to deterministic winner
   - Timeout handling
   - Invalid response handling
   
3. Integration Tests (5 tests)
   - End-to-end ambiguity detection → LLM tie-breaking
   - Phase 4 → Phase 2 compatibility
   - Real-world scenarios
"""

import pytest
import json
from unittest.mock import Mock, AsyncMock, patch

from pipeline.stages.stage_b.ambiguity_detector import (
    AmbiguityDetector,
    AmbiguityResult
)
from pipeline.stages.stage_b.llm_tie_breaker import (
    LLMTieBreaker,
    TieBreakerResult
)


# ============================================================================
# Test Fixtures
# ============================================================================

@pytest.fixture
def ambiguity_detector():
    """Create AmbiguityDetector instance"""
    return AmbiguityDetector()


@pytest.fixture
def llm_tie_breaker():
    """Create LLMTieBreaker with mock LLM client"""
    mock_client = Mock()
    return LLMTieBreaker(llm_client=mock_client)


@pytest.fixture
def sample_candidates():
    """Sample scored candidates for testing"""
    return [
        {
            'tool_name': 'asset-service-query',
            'pattern_name': 'count_aggregate',
            'total_score': 0.85,
            'feature_scores': {
                'time': 0.9,
                'cost': 0.8,
                'complexity': 0.85,
                'accuracy': 0.85,
                'completeness': 0.75
            },
            'raw_features': {
                'time_ms': 122,
                'cost': 0.05,
                'complexity': 0.3,
                'accuracy': 0.85,
                'completeness': 0.75,
                'limitations': 'Cached data (5min delay)'
            }
        },
        {
            'tool_name': 'asset-direct-poll',
            'pattern_name': 'single_query',
            'total_score': 0.82,
            'feature_scores': {
                'time': 0.7,
                'cost': 1.0,
                'complexity': 0.9,
                'accuracy': 1.0,
                'completeness': 0.8
            },
            'raw_features': {
                'time_ms': 800,
                'cost': 0.0,
                'complexity': 0.2,
                'accuracy': 1.0,
                'completeness': 0.8,
                'limitations': 'Real-time but slower'
            }
        }
    ]


# ============================================================================
# Ambiguity Detector Tests
# ============================================================================

class TestAmbiguityDetector:
    """Tests for AmbiguityDetector module"""
    
    def test_clear_winner_large_difference(self, ambiguity_detector, sample_candidates):
        """Test clear winner when score difference > 8%"""
        # Modify scores to have large difference (15%)
        candidates = sample_candidates.copy()
        candidates[0]['total_score'] = 0.90
        candidates[1]['total_score'] = 0.75
        
        result = ambiguity_detector.detect_ambiguity(candidates)
        
        assert result.is_ambiguous is False
        assert abs(result.score_difference - 0.15) < 0.001  # Floating point tolerance
        assert result.clarifying_question is None
        assert len(result.top_candidates) == 2
    
    def test_ambiguous_small_difference(self, ambiguity_detector, sample_candidates):
        """Test ambiguous case when score difference < 8%"""
        # Modify scores to have small difference (3%)
        candidates = sample_candidates.copy()
        candidates[0]['total_score'] = 0.85
        candidates[1]['total_score'] = 0.82
        
        result = ambiguity_detector.detect_ambiguity(candidates)
        
        assert result.is_ambiguous is True
        assert abs(result.score_difference - 0.03) < 0.001  # Floating point tolerance
        assert result.clarifying_question is not None
        assert len(result.clarifying_question) > 0
        assert len(result.top_candidates) == 2
    
    def test_ambiguous_exactly_at_threshold(self, ambiguity_detector, sample_candidates):
        """Test ambiguous case when score difference exactly at 8%"""
        candidates = sample_candidates.copy()
        candidates[0]['total_score'] = 0.85
        candidates[1]['total_score'] = 0.77  # Exactly 0.08 difference
        
        result = ambiguity_detector.detect_ambiguity(candidates)
        
        # Should be ambiguous (< threshold, not <=)
        assert result.is_ambiguous is True
        assert abs(result.score_difference - 0.08) < 0.001
    
    def test_single_candidate_not_ambiguous(self, ambiguity_detector):
        """Test single candidate is not ambiguous"""
        candidates = [{
            'tool_name': 'asset-service-query',
            'pattern_name': 'count_aggregate',
            'total_score': 0.85,
            'feature_scores': {},
            'raw_features': {}
        }]
        
        result = ambiguity_detector.detect_ambiguity(candidates)
        
        assert result.is_ambiguous is False
        assert result.score_difference == 0.0
        assert len(result.top_candidates) == 1
    
    def test_empty_candidates_not_ambiguous(self, ambiguity_detector):
        """Test empty candidate list is not ambiguous"""
        result = ambiguity_detector.detect_ambiguity([])
        
        assert result.is_ambiguous is False
        assert result.score_difference == 0.0
        assert len(result.top_candidates) == 0
    
    def test_identical_scores_ambiguous(self, ambiguity_detector, sample_candidates):
        """Test identical scores are ambiguous"""
        candidates = sample_candidates.copy()
        candidates[0]['total_score'] = 0.85
        candidates[1]['total_score'] = 0.85
        
        result = ambiguity_detector.detect_ambiguity(candidates)
        
        assert result.is_ambiguous is True
        assert result.score_difference == 0.0
        assert result.clarifying_question is not None
    
    def test_custom_epsilon_threshold(self, ambiguity_detector, sample_candidates):
        """Test custom epsilon threshold"""
        candidates = sample_candidates.copy()
        candidates[0]['total_score'] = 0.85
        candidates[1]['total_score'] = 0.76  # 9% difference
        
        # With default epsilon (8%), should not be ambiguous (9% > 8%)
        result1 = ambiguity_detector.detect_ambiguity(candidates)
        assert result1.is_ambiguous is False
        
        # With custom epsilon (12%), should be ambiguous (9% < 12%)
        result2 = ambiguity_detector.detect_ambiguity(candidates, epsilon=0.12)
        assert result2.is_ambiguous is True
    
    def test_clarifying_question_speed_difference(self, ambiguity_detector):
        """Test clarifying question when speed is main difference"""
        candidates = [
            {
                'tool_name': 'fast-tool',
                'pattern_name': 'quick',
                'total_score': 0.85,
                'feature_scores': {},
                'raw_features': {
                    'time_ms': 100,  # Fast
                    'cost': 0.05,
                    'accuracy': 0.8,
                    'completeness': 0.8,
                    'complexity': 0.5
                }
            },
            {
                'tool_name': 'slow-tool',
                'pattern_name': 'thorough',
                'total_score': 0.83,
                'feature_scores': {},
                'raw_features': {
                    'time_ms': 5000,  # Slow
                    'cost': 0.05,
                    'accuracy': 0.8,
                    'completeness': 0.8,
                    'complexity': 0.5
                }
            }
        ]
        
        result = ambiguity_detector.detect_ambiguity(candidates)
        
        assert result.is_ambiguous is True
        assert 'speed' in result.clarifying_question.lower() or 'immediately' in result.clarifying_question.lower()
    
    def test_clarifying_question_cost_difference(self, ambiguity_detector):
        """Test clarifying question when cost is main difference"""
        candidates = [
            {
                'tool_name': 'expensive-tool',
                'pattern_name': 'premium',
                'total_score': 0.85,
                'feature_scores': {},
                'raw_features': {
                    'time_ms': 500,
                    'cost': 5.0,  # Expensive
                    'accuracy': 0.8,
                    'completeness': 0.8,
                    'complexity': 0.5
                }
            },
            {
                'tool_name': 'cheap-tool',
                'pattern_name': 'budget',
                'total_score': 0.83,
                'feature_scores': {},
                'raw_features': {
                    'time_ms': 500,
                    'cost': 0.01,  # Cheap
                    'accuracy': 0.8,
                    'completeness': 0.8,
                    'complexity': 0.5
                }
            }
        ]
        
        result = ambiguity_detector.detect_ambiguity(candidates)
        
        assert result.is_ambiguous is True
        assert 'cost' in result.clarifying_question.lower() or 'pay' in result.clarifying_question.lower()
    
    def test_clarifying_question_accuracy_difference(self, ambiguity_detector):
        """Test clarifying question when accuracy is main difference"""
        candidates = [
            {
                'tool_name': 'accurate-tool',
                'pattern_name': 'precise',
                'total_score': 0.85,
                'feature_scores': {},
                'raw_features': {
                    'time_ms': 500,
                    'cost': 0.05,
                    'accuracy': 1.0,  # Very accurate
                    'completeness': 0.8,
                    'complexity': 0.5
                }
            },
            {
                'tool_name': 'approximate-tool',
                'pattern_name': 'estimate',
                'total_score': 0.83,
                'feature_scores': {},
                'raw_features': {
                    'time_ms': 500,
                    'cost': 0.05,
                    'accuracy': 0.6,  # Less accurate
                    'completeness': 0.8,
                    'complexity': 0.5
                }
            }
        ]
        
        result = ambiguity_detector.detect_ambiguity(candidates)
        
        assert result.is_ambiguous is True
        assert 'accura' in result.clarifying_question.lower() or 'real-time' in result.clarifying_question.lower()
    
    def test_clarifying_question_completeness_difference(self, ambiguity_detector):
        """Test clarifying question when completeness is main difference"""
        candidates = [
            {
                'tool_name': 'complete-tool',
                'pattern_name': 'full',
                'total_score': 0.85,
                'feature_scores': {},
                'raw_features': {
                    'time_ms': 500,
                    'cost': 0.05,
                    'accuracy': 0.8,
                    'completeness': 1.0,  # Complete
                    'complexity': 0.5
                }
            },
            {
                'tool_name': 'summary-tool',
                'pattern_name': 'brief',
                'total_score': 0.83,
                'feature_scores': {},
                'raw_features': {
                    'time_ms': 500,
                    'cost': 0.05,
                    'accuracy': 0.8,
                    'completeness': 0.5,  # Summary only
                    'complexity': 0.5
                }
            }
        ]
        
        result = ambiguity_detector.detect_ambiguity(candidates)
        
        assert result.is_ambiguous is True
        assert 'detail' in result.clarifying_question.lower() or 'summary' in result.clarifying_question.lower()
    
    def test_clarifying_question_no_clear_difference(self, ambiguity_detector):
        """Test clarifying question when all features are similar"""
        candidates = [
            {
                'tool_name': 'tool-a',
                'pattern_name': 'pattern-a',
                'total_score': 0.85,
                'feature_scores': {},
                'raw_features': {
                    'time_ms': 500,
                    'cost': 0.05,
                    'accuracy': 0.8,
                    'completeness': 0.8,
                    'complexity': 0.5
                }
            },
            {
                'tool_name': 'tool-b',
                'pattern_name': 'pattern-b',
                'total_score': 0.84,
                'feature_scores': {},
                'raw_features': {
                    'time_ms': 510,  # Very similar
                    'cost': 0.051,
                    'accuracy': 0.81,
                    'completeness': 0.81,
                    'complexity': 0.51
                }
            }
        ]
        
        result = ambiguity_detector.detect_ambiguity(candidates)
        
        assert result.is_ambiguous is True
        # Should return generic question
        assert 'speed' in result.clarifying_question.lower() or 'accuracy' in result.clarifying_question.lower()
    
    def test_normalization_consistency(self, ambiguity_detector):
        """Test that normalization matches FeatureNormalizer"""
        # Test time normalization
        assert ambiguity_detector._normalize_time(50) == 1.0  # MIN_TIME
        assert ambiguity_detector._normalize_time(60000) == 0.0  # MAX_TIME
        assert 0.0 < ambiguity_detector._normalize_time(500) < 1.0
        
        # Test cost normalization
        assert ambiguity_detector._normalize_cost(0.0) == 1.0  # MIN_COST
        assert ambiguity_detector._normalize_cost(10.0) == 0.0  # MAX_COST
        assert 0.0 < ambiguity_detector._normalize_cost(5.0) < 1.0
    
    def test_multiple_candidates_only_top2_matter(self, ambiguity_detector):
        """Test that only top-2 candidates are considered for ambiguity"""
        candidates = [
            {'tool_name': 'tool1', 'pattern_name': 'p1', 'total_score': 0.85, 'feature_scores': {}, 'raw_features': {}},
            {'tool_name': 'tool2', 'pattern_name': 'p2', 'total_score': 0.83, 'feature_scores': {}, 'raw_features': {}},
            {'tool_name': 'tool3', 'pattern_name': 'p3', 'total_score': 0.50, 'feature_scores': {}, 'raw_features': {}},
            {'tool_name': 'tool4', 'pattern_name': 'p4', 'total_score': 0.30, 'feature_scores': {}, 'raw_features': {}}
        ]
        
        result = ambiguity_detector.detect_ambiguity(candidates)
        
        # Should only compare top-2 (0.85 vs 0.83 = 0.02 difference)
        assert result.is_ambiguous is True
        assert abs(result.score_difference - 0.02) < 0.001
        assert len(result.top_candidates) == 2


# ============================================================================
# LLM Tie-Breaker Tests
# ============================================================================

class TestLLMTieBreaker:
    """Tests for LLMTieBreaker module"""
    
    @pytest.mark.asyncio
    async def test_successful_tie_breaking_choice_a(self, sample_candidates):
        """Test successful tie-breaking choosing option A"""
        mock_client = AsyncMock()
        mock_client.chat = AsyncMock(return_value={
            'content': '{"choice": "A", "justification": "Faster response time is better for user experience"}'
        })
        
        tie_breaker = LLMTieBreaker(llm_client=mock_client)
        
        result = await tie_breaker.break_tie(
            query="How many Linux assets do we have?",
            candidate1=sample_candidates[0],
            candidate2=sample_candidates[1]
        )
        
        assert result.chosen_candidate == sample_candidates[0]
        assert result.llm_choice == "A"
        assert "faster" in result.justification.lower()
        assert result.fallback_used is False
        assert result.llm_response_raw is not None
    
    @pytest.mark.asyncio
    async def test_successful_tie_breaking_choice_b(self, sample_candidates):
        """Test successful tie-breaking choosing option B"""
        mock_client = AsyncMock()
        mock_client.chat = AsyncMock(return_value={
            'content': '{"choice": "B", "justification": "Real-time accuracy is more important"}'
        })
        
        tie_breaker = LLMTieBreaker(llm_client=mock_client)
        
        result = await tie_breaker.break_tie(
            query="How many Linux assets do we have?",
            candidate1=sample_candidates[0],
            candidate2=sample_candidates[1]
        )
        
        assert result.chosen_candidate == sample_candidates[1]
        assert result.llm_choice == "B"
        assert "accuracy" in result.justification.lower()
        assert result.fallback_used is False
    
    @pytest.mark.asyncio
    async def test_llm_response_with_markdown(self, sample_candidates):
        """Test parsing LLM response wrapped in markdown code blocks"""
        mock_client = AsyncMock()
        mock_client.chat = AsyncMock(return_value={
            'content': '```json\n{"choice": "A", "justification": "Better performance"}\n```'
        })
        
        tie_breaker = LLMTieBreaker(llm_client=mock_client)
        
        result = await tie_breaker.break_tie(
            query="Test query",
            candidate1=sample_candidates[0],
            candidate2=sample_candidates[1]
        )
        
        assert result.chosen_candidate == sample_candidates[0]
        assert result.llm_choice == "A"
        assert result.fallback_used is False
    
    @pytest.mark.asyncio
    async def test_fallback_when_no_llm_client(self, sample_candidates):
        """Test fallback to deterministic winner when no LLM client"""
        tie_breaker = LLMTieBreaker(llm_client=None)
        
        result = await tie_breaker.break_tie(
            query="Test query",
            candidate1=sample_candidates[0],
            candidate2=sample_candidates[1]
        )
        
        assert result.chosen_candidate == sample_candidates[0]  # Always chooses first
        assert result.llm_choice == "A"
        assert result.fallback_used is True
        assert "unavailable" in result.justification.lower()
    
    @pytest.mark.asyncio
    async def test_fallback_when_llm_fails(self, sample_candidates):
        """Test fallback when LLM call fails"""
        mock_client = AsyncMock()
        mock_client.chat = AsyncMock(side_effect=Exception("LLM timeout"))
        
        tie_breaker = LLMTieBreaker(llm_client=mock_client)
        
        result = await tie_breaker.break_tie(
            query="Test query",
            candidate1=sample_candidates[0],
            candidate2=sample_candidates[1]
        )
        
        assert result.chosen_candidate == sample_candidates[0]
        assert result.fallback_used is True
    
    @pytest.mark.asyncio
    async def test_fallback_when_invalid_json(self, sample_candidates):
        """Test fallback when LLM returns invalid JSON"""
        mock_client = AsyncMock()
        mock_client.chat = AsyncMock(return_value={
            'content': 'This is not valid JSON'
        })
        
        tie_breaker = LLMTieBreaker(llm_client=mock_client)
        
        result = await tie_breaker.break_tie(
            query="Test query",
            candidate1=sample_candidates[0],
            candidate2=sample_candidates[1]
        )
        
        assert result.chosen_candidate == sample_candidates[0]
        assert result.fallback_used is True
    
    @pytest.mark.asyncio
    async def test_fallback_when_invalid_choice(self, sample_candidates):
        """Test fallback when LLM returns invalid choice"""
        mock_client = AsyncMock()
        mock_client.chat = AsyncMock(return_value={
            'content': '{"choice": "C", "justification": "Invalid choice"}'
        })
        
        tie_breaker = LLMTieBreaker(llm_client=mock_client)
        
        result = await tie_breaker.break_tie(
            query="Test query",
            candidate1=sample_candidates[0],
            candidate2=sample_candidates[1]
        )
        
        assert result.chosen_candidate == sample_candidates[0]
        assert result.fallback_used is True
    
    @pytest.mark.asyncio
    async def test_fallback_when_missing_justification(self, sample_candidates):
        """Test fallback when LLM returns no justification"""
        mock_client = AsyncMock()
        mock_client.chat = AsyncMock(return_value={
            'content': '{"choice": "A"}'
        })
        
        tie_breaker = LLMTieBreaker(llm_client=mock_client)
        
        result = await tie_breaker.break_tie(
            query="Test query",
            candidate1=sample_candidates[0],
            candidate2=sample_candidates[1]
        )
        
        assert result.chosen_candidate == sample_candidates[0]
        assert result.fallback_used is True
    
    def test_prompt_building(self, llm_tie_breaker, sample_candidates):
        """Test prompt building includes all necessary information"""
        prompt = llm_tie_breaker._build_prompt(
            query="How many Linux assets?",
            candidate1=sample_candidates[0],
            candidate2=sample_candidates[1]
        )
        
        # Check query is included
        assert "How many Linux assets?" in prompt
        
        # Check both candidates are included
        assert "asset-service-query" in prompt
        assert "asset-direct-poll" in prompt
        
        # Check features are included
        assert "122ms" in prompt or "122" in prompt
        assert "800ms" in prompt or "800" in prompt
        assert "0.05" in prompt
        
        # Check format instructions
        assert "JSON" in prompt
        assert "choice" in prompt
        assert "justification" in prompt
    
    @pytest.mark.asyncio
    async def test_lowercase_choice_accepted(self, sample_candidates):
        """Test that lowercase choice is accepted and normalized"""
        mock_client = AsyncMock()
        mock_client.chat = AsyncMock(return_value={
            'content': '{"choice": "a", "justification": "Better option"}'
        })
        
        tie_breaker = LLMTieBreaker(llm_client=mock_client)
        
        result = await tie_breaker.break_tie(
            query="Test query",
            candidate1=sample_candidates[0],
            candidate2=sample_candidates[1]
        )
        
        assert result.llm_choice == "A"  # Normalized to uppercase
        assert result.chosen_candidate == sample_candidates[0]


# ============================================================================
# Integration Tests
# ============================================================================

class TestPhase4Integration:
    """Integration tests for Phase 4 modules"""
    
    @pytest.mark.asyncio
    async def test_end_to_end_ambiguous_case(self, sample_candidates):
        """Test end-to-end flow: ambiguity detection → LLM tie-breaking"""
        # Step 1: Detect ambiguity
        detector = AmbiguityDetector()
        
        # Make scores very close (2% difference)
        candidates = sample_candidates.copy()
        candidates[0]['total_score'] = 0.85
        candidates[1]['total_score'] = 0.83
        
        ambiguity_result = detector.detect_ambiguity(candidates)
        
        assert ambiguity_result.is_ambiguous is True
        
        # Step 2: Break tie with LLM
        mock_client = AsyncMock()
        mock_client.chat = AsyncMock(return_value={
            'content': '{"choice": "A", "justification": "Faster is better for this query"}'
        })
        
        tie_breaker = LLMTieBreaker(llm_client=mock_client)
        
        tie_result = await tie_breaker.break_tie(
            query="How many Linux assets?",
            candidate1=candidates[0],
            candidate2=candidates[1]
        )
        
        assert tie_result.chosen_candidate == candidates[0]
        assert tie_result.fallback_used is False
    
    @pytest.mark.asyncio
    async def test_end_to_end_clear_winner(self, sample_candidates):
        """Test end-to-end flow: clear winner (no LLM needed)"""
        detector = AmbiguityDetector()
        
        # Make scores far apart (15% difference)
        candidates = sample_candidates.copy()
        candidates[0]['total_score'] = 0.90
        candidates[1]['total_score'] = 0.75
        
        ambiguity_result = detector.detect_ambiguity(candidates)
        
        assert ambiguity_result.is_ambiguous is False
        
        # No need to call LLM - deterministic winner is clear
        winner = candidates[0]
        assert winner['total_score'] == 0.90
    
    @pytest.mark.asyncio
    async def test_end_to_end_with_fallback(self, sample_candidates):
        """Test end-to-end flow: ambiguous case with LLM fallback"""
        detector = AmbiguityDetector()
        
        candidates = sample_candidates.copy()
        candidates[0]['total_score'] = 0.85
        candidates[1]['total_score'] = 0.83
        
        ambiguity_result = detector.detect_ambiguity(candidates)
        assert ambiguity_result.is_ambiguous is True
        
        # LLM fails, use fallback
        tie_breaker = LLMTieBreaker(llm_client=None)
        
        tie_result = await tie_breaker.break_tie(
            query="Test query",
            candidate1=candidates[0],
            candidate2=candidates[1]
        )
        
        assert tie_result.chosen_candidate == candidates[0]
        assert tie_result.fallback_used is True
    
    def test_phase4_compatible_with_phase2_output(self):
        """Test that Phase 4 works with Phase 2 DeterministicScorer output"""
        # This test verifies that the data structures are compatible
        from pipeline.stages.stage_b.deterministic_scorer import DeterministicScorer, PreferenceMode
        from pipeline.stages.stage_b.feature_normalizer import FeatureNormalizer
        
        # Create Phase 2 modules
        normalizer = FeatureNormalizer()
        scorer = DeterministicScorer()
        
        # Sample candidates (from Phase 3 output format)
        candidates = [
            {
                'tool_name': 'tool1',
                'pattern_name': 'pattern1',
                'time_ms': 100,
                'cost': 0.05,
                'complexity': 0.3,
                'accuracy': 0.85,
                'completeness': 0.75
            },
            {
                'tool_name': 'tool2',
                'pattern_name': 'pattern2',
                'time_ms': 500,
                'cost': 0.0,
                'complexity': 0.2,
                'accuracy': 1.0,
                'completeness': 0.8
            }
        ]
        
        # Phase 2: Normalize and score
        normalized = [normalizer.normalize_features(c) for c in candidates]
        scored = scorer.score_candidates(normalized, PreferenceMode.FAST)
        
        # Phase 4: Detect ambiguity
        detector = AmbiguityDetector()
        result = detector.detect_ambiguity(scored)
        
        # Should work without errors
        assert isinstance(result, AmbiguityResult)
        assert result.score_difference >= 0.0
    
    @pytest.mark.asyncio
    async def test_real_world_scenario_fast_query(self):
        """Test real-world scenario: fast query with ambiguous candidates"""
        # Scenario: User asks "Quick count of Linux assets"
        # Two candidates have similar scores after deterministic scoring
        
        candidates = [
            {
                'tool_name': 'asset-service-query',
                'pattern_name': 'count_aggregate',
                'total_score': 0.87,
                'feature_scores': {
                    'time': 0.95,  # Very fast
                    'cost': 0.85,
                    'complexity': 0.90,
                    'accuracy': 0.80,  # Cached
                    'completeness': 0.85
                },
                'raw_features': {
                    'time_ms': 81,
                    'cost': 0.03,
                    'complexity': 0.2,
                    'accuracy': 0.80,
                    'completeness': 0.85,
                    'limitations': 'Cached data (5min delay)'
                }
            },
            {
                'tool_name': 'asset-service-query',
                'pattern_name': 'single_lookup',
                'total_score': 0.85,
                'feature_scores': {
                    'time': 0.93,  # Also fast
                    'cost': 0.90,
                    'complexity': 0.85,
                    'accuracy': 0.85,
                    'completeness': 0.75  # Less complete
                },
                'raw_features': {
                    'time_ms': 100,
                    'cost': 0.02,
                    'complexity': 0.25,
                    'accuracy': 0.85,
                    'completeness': 0.75,
                    'limitations': 'Single asset lookup only'
                }
            }
        ]
        
        # Detect ambiguity
        detector = AmbiguityDetector()
        ambiguity_result = detector.detect_ambiguity(candidates)
        
        assert ambiguity_result.is_ambiguous is True
        assert ambiguity_result.score_difference < 0.08
        
        # LLM breaks tie
        mock_client = AsyncMock()
        mock_client.chat = AsyncMock(return_value={
            'content': '{"choice": "A", "justification": "Count aggregate is better for counting all assets"}'
        })
        
        tie_breaker = LLMTieBreaker(llm_client=mock_client)
        
        tie_result = await tie_breaker.break_tie(
            query="Quick count of Linux assets",
            candidate1=candidates[0],
            candidate2=candidates[1]
        )
        
        assert tie_result.chosen_candidate['pattern_name'] == 'count_aggregate'
        assert 'aggregate' in tie_result.justification.lower()
        assert tie_result.fallback_used is False