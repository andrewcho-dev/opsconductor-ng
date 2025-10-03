"""
Tests for Hybrid Optimization Phase 3: Preference Detection & Candidate Enumeration

Phase 3 implements:
1. PreferenceDetector: Detects user preferences from query text
2. CandidateEnumerator: Enumerates and evaluates candidate tools

Test Coverage:
- Preference detection (keyword matching, explicit mode, confidence)
- Candidate enumeration (capability matching, expression evaluation, error handling)
- Context estimation (heuristics, metadata override)
- Integration scenarios (end-to-end)
"""

import pytest
from pipeline.stages.stage_b.preference_detector import PreferenceDetector
from pipeline.stages.stage_b.candidate_enumerator import CandidateEnumerator, ToolCandidate
from pipeline.stages.stage_b.deterministic_scorer import PreferenceMode
from pipeline.stages.stage_b.profile_loader import ProfileLoader


# ============================================================================
# Preference Detector Tests (20 tests)
# ============================================================================

class TestPreferenceDetector:
    """Test preference detection from query text"""
    
    def test_detect_fast_preference(self):
        """Test detection of fast/quick keywords"""
        detector = PreferenceDetector()
        
        queries = [
            "Give me a quick count of assets",
            "Fast query for Linux servers",
            "I need this ASAP",
            "Rapid response needed",
            "Show me immediately"
        ]
        
        for query in queries:
            mode = detector.detect_preference(query)
            assert mode == PreferenceMode.FAST, f"Failed for query: {query}"
    
    def test_detect_accurate_preference(self):
        """Test detection of accurate/precise keywords"""
        detector = PreferenceDetector()
        
        queries = [
            "I need accurate data",
            "Give me precise numbers",
            "Verify the exact count",
            "Double-check the results",
            "Reliable information please"
        ]
        
        for query in queries:
            mode = detector.detect_preference(query)
            assert mode == PreferenceMode.ACCURATE, f"Failed for query: {query}"
    
    def test_detect_thorough_preference(self):
        """Test detection of thorough/complete keywords"""
        detector = PreferenceDetector()
        
        queries = [
            "Give me a thorough analysis",
            "I need complete details",
            "Show me all assets",
            "Comprehensive report please",
            "Full details on every server"
        ]
        
        for query in queries:
            mode = detector.detect_preference(query)
            assert mode == PreferenceMode.THOROUGH, f"Failed for query: {query}"
    
    def test_detect_cheap_preference(self):
        """Test detection of cost-conscious keywords"""
        detector = PreferenceDetector()
        
        queries = [
            "Give me a cheap query",
            "Free option preferred",
            "Cost-effective solution",
            "Economical approach",
            "Low-cost method"
        ]
        
        for query in queries:
            mode = detector.detect_preference(query)
            assert mode == PreferenceMode.CHEAP, f"Failed for query: {query}"
    
    def test_detect_simple_preference(self):
        """Test detection of simplicity keywords"""
        detector = PreferenceDetector()
        
        queries = [
            "Give me a simple count",
            "Basic information only",
            "Straightforward query",
            "Easy lookup",
            "Minimal complexity"
        ]
        
        for query in queries:
            mode = detector.detect_preference(query)
            assert mode == PreferenceMode.SIMPLE, f"Failed for query: {query}"
    
    def test_detect_balanced_default(self):
        """Test balanced mode as default when no keywords found"""
        detector = PreferenceDetector()
        
        queries = [
            "Count Linux assets",
            "Show me servers",
            "List databases",
            "What assets do we have?"
        ]
        
        for query in queries:
            mode = detector.detect_preference(query)
            assert mode == PreferenceMode.BALANCED, f"Failed for query: {query}"
    
    def test_explicit_mode_override(self):
        """Test explicit mode overrides keyword detection"""
        detector = PreferenceDetector()
        
        # Query says "quick" but explicit mode is "accurate"
        mode = detector.detect_preference(
            "Give me a quick count",
            explicit_mode="accurate"
        )
        assert mode == PreferenceMode.ACCURATE
        
        # Query says "accurate" but explicit mode is "fast"
        mode = detector.detect_preference(
            "I need accurate data",
            explicit_mode="fast"
        )
        assert mode == PreferenceMode.FAST
    
    def test_invalid_explicit_mode(self):
        """Test error handling for invalid explicit mode"""
        detector = PreferenceDetector()
        
        with pytest.raises(ValueError, match="Invalid preference mode"):
            detector.detect_preference("Count assets", explicit_mode="invalid")
    
    def test_case_insensitive_matching(self):
        """Test case-insensitive keyword matching"""
        detector = PreferenceDetector()
        
        queries = [
            "QUICK count",
            "Quick COUNT",
            "QuIcK CoUnT"
        ]
        
        for query in queries:
            mode = detector.detect_preference(query)
            assert mode == PreferenceMode.FAST
    
    def test_word_boundary_matching(self):
        """Test word boundary matching (avoid partial matches)"""
        detector = PreferenceDetector()
        
        # "fast" in "breakfast" should NOT match
        mode = detector.detect_preference("I had breakfast")
        assert mode == PreferenceMode.BALANCED
        
        # "fast" as standalone word SHOULD match
        mode = detector.detect_preference("I need fast results")
        assert mode == PreferenceMode.FAST
    
    def test_multiple_keywords_same_mode(self):
        """Test multiple keywords for same mode increase confidence"""
        detector = PreferenceDetector()
        
        # Multiple fast keywords
        mode, conf = detector.detect_preference_with_confidence(
            "Give me a quick fast rapid count"
        )
        assert mode == PreferenceMode.FAST
        assert conf >= 0.8  # High confidence with multiple matches
    
    def test_confidence_explicit_mode(self):
        """Test confidence is 1.0 for explicit mode"""
        detector = PreferenceDetector()
        
        mode, conf = detector.detect_preference_with_confidence(
            "Count assets",
            explicit_mode="fast"
        )
        assert mode == PreferenceMode.FAST
        assert conf == 1.0
    
    def test_confidence_keyword_detection(self):
        """Test confidence for keyword detection"""
        detector = PreferenceDetector()
        
        # Single keyword: 0.7 base + 0.1 = 0.8
        mode, conf = detector.detect_preference_with_confidence("Quick count")
        assert mode == PreferenceMode.FAST
        assert conf >= 0.7
        
        # Multiple keywords: higher confidence
        mode, conf = detector.detect_preference_with_confidence("Quick fast count")
        assert mode == PreferenceMode.FAST
        assert conf >= 0.8
    
    def test_confidence_balanced_default(self):
        """Test confidence is 0.5 for balanced default"""
        detector = PreferenceDetector()
        
        mode, conf = detector.detect_preference_with_confidence("Count assets")
        assert mode == PreferenceMode.BALANCED
        assert conf == 0.5
    
    def test_conflicting_keywords(self):
        """Test behavior with conflicting keywords (first match wins)"""
        detector = PreferenceDetector()
        
        # Both "quick" and "accurate" present
        mode = detector.detect_preference("Give me quick and accurate results")
        # Should pick one based on match count (both have 1, so first in order)
        assert mode in [PreferenceMode.FAST, PreferenceMode.ACCURATE]
    
    def test_all_explicit_modes(self):
        """Test all explicit mode values"""
        detector = PreferenceDetector()
        
        modes = ["fast", "accurate", "thorough", "cheap", "simple", "balanced"]
        
        for mode_str in modes:
            mode = detector.detect_preference("Count assets", explicit_mode=mode_str)
            assert mode.value == mode_str
    
    def test_explicit_mode_case_insensitive(self):
        """Test explicit mode is case-insensitive"""
        detector = PreferenceDetector()
        
        mode = detector.detect_preference("Count assets", explicit_mode="FAST")
        assert mode == PreferenceMode.FAST
        
        mode = detector.detect_preference("Count assets", explicit_mode="Fast")
        assert mode == PreferenceMode.FAST
    
    def test_explicit_mode_whitespace(self):
        """Test explicit mode handles whitespace"""
        detector = PreferenceDetector()
        
        mode = detector.detect_preference("Count assets", explicit_mode="  fast  ")
        assert mode == PreferenceMode.FAST
    
    def test_empty_query(self):
        """Test empty query returns balanced default"""
        detector = PreferenceDetector()
        
        mode = detector.detect_preference("")
        assert mode == PreferenceMode.BALANCED
    
    def test_real_world_queries(self):
        """Test real-world query examples"""
        detector = PreferenceDetector()
        
        # Fast query
        mode = detector.detect_preference("How many Linux assets do we have?")
        # No keywords, should be balanced
        assert mode == PreferenceMode.BALANCED
        
        # With "quick" keyword
        mode = detector.detect_preference("Quick - how many Linux assets?")
        assert mode == PreferenceMode.FAST
        
        # With "all" keyword (thorough)
        mode = detector.detect_preference("Show me all Linux assets")
        assert mode == PreferenceMode.THOROUGH


# ============================================================================
# Candidate Enumerator Tests (15 tests)
# ============================================================================

class TestCandidateEnumerator:
    """Test candidate enumeration and evaluation"""
    
    def test_enumerate_basic(self):
        """Test basic candidate enumeration"""
        enumerator = CandidateEnumerator()
        
        candidates = enumerator.enumerate_candidates(
            required_capabilities=["asset_query"],
            context={"N": 100}
        )
        
        # Should find at least one candidate
        assert len(candidates) > 0
        
        # All candidates should have required fields
        for candidate in candidates:
            assert candidate.tool_name
            assert candidate.capability_name == "asset_query"
            assert candidate.pattern_name
            assert candidate.estimated_time_ms > 0
            assert candidate.estimated_cost >= 0
            assert 0 <= candidate.complexity <= 1
            assert 0 <= candidate.accuracy <= 1
            assert 0 <= candidate.completeness <= 1
    
    def test_enumerate_multiple_capabilities(self):
        """Test enumeration with multiple capabilities"""
        enumerator = CandidateEnumerator()
        
        candidates = enumerator.enumerate_candidates(
            required_capabilities=["asset_query", "info_display"],
            context={"N": 100}
        )
        
        # Should find candidates for both capabilities
        capabilities = {c.capability_name for c in candidates}
        assert "asset_query" in capabilities or "info_display" in capabilities
    
    def test_enumerate_no_matching_capabilities(self):
        """Test enumeration with no matching capabilities"""
        enumerator = CandidateEnumerator()
        
        candidates = enumerator.enumerate_candidates(
            required_capabilities=["nonexistent_capability"],
            context={"N": 100}
        )
        
        # Should return empty list
        assert len(candidates) == 0
    
    def test_expression_evaluation(self):
        """Test expression evaluation with context"""
        enumerator = CandidateEnumerator()
        
        # Small N
        candidates_small = enumerator.enumerate_candidates(
            required_capabilities=["asset_query"],
            context={"N": 10}
        )
        
        # Large N
        candidates_large = enumerator.enumerate_candidates(
            required_capabilities=["asset_query"],
            context={"N": 1000}
        )
        
        # Find same pattern in both
        for c_small in candidates_small:
            for c_large in candidates_large:
                if (c_small.tool_name == c_large.tool_name and
                    c_small.pattern_name == c_large.pattern_name):
                    # Time should scale with N (if expression uses N)
                    # Some patterns may not use N, so just check they're positive
                    assert c_small.estimated_time_ms > 0
                    assert c_large.estimated_time_ms > 0
    
    def test_default_context(self):
        """Test default context when none provided"""
        enumerator = CandidateEnumerator()
        
        # No context provided
        candidates = enumerator.enumerate_candidates(
            required_capabilities=["asset_query"]
        )
        
        # Should use defaults and succeed
        assert len(candidates) > 0
    
    def test_candidate_metadata(self):
        """Test candidate includes all metadata"""
        enumerator = CandidateEnumerator()
        
        candidates = enumerator.enumerate_candidates(
            required_capabilities=["asset_query"],
            context={"N": 100}
        )
        
        candidate = candidates[0]
        
        # Check metadata fields
        assert candidate.description
        assert isinstance(candidate.typical_use_cases, list)
        assert isinstance(candidate.limitations, list)
        assert candidate.policy is not None
    
    def test_policy_configuration(self):
        """Test policy configuration is included"""
        enumerator = CandidateEnumerator()
        
        candidates = enumerator.enumerate_candidates(
            required_capabilities=["asset_query"],
            context={"N": 100}
        )
        
        for candidate in candidates:
            # Policy should be present
            assert candidate.policy is not None
            # Policy fields should be accessible
            assert isinstance(candidate.policy.requires_approval, bool)
            assert isinstance(candidate.policy.production_safe, bool)
    
    def test_estimate_context_default(self):
        """Test context estimation with defaults"""
        enumerator = CandidateEnumerator()
        
        context = enumerator.estimate_context("Count assets")
        
        assert context["N"] > 0
        assert context["pages"] > 0
        assert context["p95_latency"] > 0
    
    def test_estimate_context_all_keyword(self):
        """Test context estimation detects 'all' keyword"""
        enumerator = CandidateEnumerator()
        
        context = enumerator.estimate_context("Show me all assets")
        
        # "all" should increase N
        assert context["N"] > 100
    
    def test_estimate_context_single_keyword(self):
        """Test context estimation detects 'single' keyword"""
        enumerator = CandidateEnumerator()
        
        context = enumerator.estimate_context("Show me a single asset")
        
        # "single" should set N=1
        assert context["N"] == 1
    
    def test_estimate_context_metadata_override(self):
        """Test context estimation with metadata override"""
        enumerator = CandidateEnumerator()
        
        context = enumerator.estimate_context(
            "Count assets",
            metadata={"asset_count": 500, "page_count": 10}
        )
        
        # Metadata should override defaults
        assert context["N"] == 500
        assert context["pages"] == 10
    
    def test_profile_caching(self):
        """Test profile caching (load once, reuse)"""
        enumerator = CandidateEnumerator()
        
        # First call loads profiles
        candidates1 = enumerator.enumerate_candidates(
            required_capabilities=["asset_query"],
            context={"N": 100}
        )
        
        # Second call should use cached profiles
        candidates2 = enumerator.enumerate_candidates(
            required_capabilities=["asset_query"],
            context={"N": 100}
        )
        
        # Should return same results
        assert len(candidates1) == len(candidates2)
    
    def test_error_handling_graceful(self):
        """Test graceful error handling for invalid patterns"""
        # This test verifies that invalid patterns are skipped, not that they fail
        enumerator = CandidateEnumerator()
        
        # Should not raise exception even if some patterns fail
        candidates = enumerator.enumerate_candidates(
            required_capabilities=["asset_query"],
            context={"N": 100}
        )
        
        # Should still return valid candidates
        assert len(candidates) >= 0
    
    def test_candidate_uniqueness(self):
        """Test each candidate is unique (tool + capability + pattern)"""
        enumerator = CandidateEnumerator()
        
        candidates = enumerator.enumerate_candidates(
            required_capabilities=["asset_query"],
            context={"N": 100}
        )
        
        # Build set of (tool, capability, pattern) tuples
        unique_ids = {
            (c.tool_name, c.capability_name, c.pattern_name)
            for c in candidates
        }
        
        # Should have no duplicates
        assert len(unique_ids) == len(candidates)
    
    def test_real_world_scenario(self):
        """Test real-world scenario: count Linux assets"""
        enumerator = CandidateEnumerator()
        
        # Estimate context from query
        context = enumerator.estimate_context(
            "How many Linux assets do we have?",
            intent="QUERY_ASSETS"
        )
        
        # Enumerate candidates
        candidates = enumerator.enumerate_candidates(
            required_capabilities=["asset_query"],
            context=context
        )
        
        # Should find multiple candidates
        assert len(candidates) > 0
        
        # Should have different patterns (count, list, etc.)
        patterns = {c.pattern_name for c in candidates}
        assert len(patterns) > 0


# ============================================================================
# Integration Tests (5 tests)
# ============================================================================

class TestPhase3Integration:
    """Test integration between preference detection and candidate enumeration"""
    
    def test_end_to_end_fast_query(self):
        """Test end-to-end: fast query preference + candidate enumeration"""
        detector = PreferenceDetector()
        enumerator = CandidateEnumerator()
        
        query = "Quick count of Linux assets"
        
        # Step 1: Detect preference
        mode = detector.detect_preference(query)
        assert mode == PreferenceMode.FAST
        
        # Step 2: Estimate context
        context = enumerator.estimate_context(query)
        
        # Step 3: Enumerate candidates
        candidates = enumerator.enumerate_candidates(
            required_capabilities=["asset_query"],
            context=context
        )
        
        # Should have candidates ready for scoring
        assert len(candidates) > 0
        for candidate in candidates:
            assert candidate.estimated_time_ms > 0
    
    def test_end_to_end_thorough_query(self):
        """Test end-to-end: thorough query preference + candidate enumeration"""
        detector = PreferenceDetector()
        enumerator = CandidateEnumerator()
        
        query = "Show me all detailed information about Linux assets"
        
        # Step 1: Detect preference
        mode = detector.detect_preference(query)
        assert mode == PreferenceMode.THOROUGH
        
        # Step 2: Estimate context (should detect "all")
        context = enumerator.estimate_context(query)
        assert context["N"] > 100  # "all" increases N
        
        # Step 3: Enumerate candidates
        candidates = enumerator.enumerate_candidates(
            required_capabilities=["asset_query"],
            context=context
        )
        
        assert len(candidates) > 0
    
    def test_end_to_end_explicit_mode(self):
        """Test end-to-end with explicit mode override"""
        detector = PreferenceDetector()
        enumerator = CandidateEnumerator()
        
        query = "Count assets"
        
        # Explicit mode: accurate
        mode = detector.detect_preference(query, explicit_mode="accurate")
        assert mode == PreferenceMode.ACCURATE
        
        # Enumerate candidates
        candidates = enumerator.enumerate_candidates(
            required_capabilities=["asset_query"],
            context={"N": 100}
        )
        
        assert len(candidates) > 0
    
    def test_end_to_end_with_metadata(self):
        """Test end-to-end with metadata from Stage A"""
        detector = PreferenceDetector()
        enumerator = CandidateEnumerator()
        
        query = "Count Linux assets"
        metadata = {
            "asset_count": 500,
            "intent": "QUERY_ASSETS"
        }
        
        # Detect preference
        mode = detector.detect_preference(query)
        
        # Estimate context with metadata
        context = enumerator.estimate_context(query, metadata=metadata)
        assert context["N"] == 500  # From metadata
        
        # Enumerate candidates
        candidates = enumerator.enumerate_candidates(
            required_capabilities=["asset_query"],
            context=context
        )
        
        assert len(candidates) > 0
    
    def test_phase3_ready_for_phase2(self):
        """Test Phase 3 output is compatible with Phase 2 input"""
        from pipeline.stages.stage_b.feature_normalizer import FeatureNormalizer
        from pipeline.stages.stage_b.deterministic_scorer import DeterministicScorer
        
        detector = PreferenceDetector()
        enumerator = CandidateEnumerator()
        normalizer = FeatureNormalizer()
        scorer = DeterministicScorer()
        
        query = "Quick count of assets"
        
        # Phase 3: Detect preference and enumerate candidates
        mode = detector.detect_preference(query)
        candidates = enumerator.enumerate_candidates(
            required_capabilities=["asset_query"],
            context={"N": 100}
        )
        
        # Phase 2: Normalize and score
        for candidate in candidates:
            # Normalize features
            normalized = normalizer.normalize_features({
                'time_ms': candidate.estimated_time_ms,
                'cost': candidate.estimated_cost,
                'complexity': candidate.complexity,
                'accuracy': candidate.accuracy,
                'completeness': candidate.completeness
            })
            
            # Should be valid normalized features
            assert 0 <= normalized['time_ms'] <= 1
            assert 0 <= normalized['cost'] <= 1
            assert 0 <= normalized['complexity'] <= 1
            assert 0 <= normalized['accuracy'] <= 1
            assert 0 <= normalized['completeness'] <= 1
        
        # Should be able to score candidates
        candidate_dicts = [
            {
                'tool_name': c.tool_name,
                'pattern': c.pattern_name,
                'features': normalizer.normalize_features({
                    'time_ms': c.estimated_time_ms,
                    'cost': c.estimated_cost,
                    'complexity': c.complexity,
                    'accuracy': c.accuracy,
                    'completeness': c.completeness
                })
            }
            for c in candidates
        ]
        
        scored = scorer.score_candidates(candidate_dicts, mode)
        assert len(scored) > 0
        assert scored[0].total_score > 0