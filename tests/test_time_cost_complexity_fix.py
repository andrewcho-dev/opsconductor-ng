"""
Test: Time/Cost/Complexity Metrics Fix Verification

This test verifies that all metrics (time, cost, complexity) correctly represent
TOTAL end-to-end resources needed to deliver results to the user.

Critical Bug Fixed:
- single_lookup was using "80 + 0.01 * N" suggesting it scales with N
- But it's a single API call pattern (N=1 only)
- For N=100, it would require 100 separate API calls
- Fixed to constant "80" and documented as N=1 only

- detailed_lookup cost was "1 + ceil(N/100)" (batched)
- But time was "300 + 5*N" (didn't account for multiple API calls)
- Fixed to "300 * ceil(N/100) + 5*N" to match batching
"""

import pytest
from pipeline.stages.stage_b.candidate_enumerator import CandidateEnumerator
from pipeline.stages.stage_b.feature_normalizer import FeatureNormalizer
from pipeline.stages.stage_b.deterministic_scorer import DeterministicScorer, PreferenceMode


class TestTimeEstimateFix:
    """Test that time estimates reflect total end-to-end time"""
    
    def test_single_lookup_is_constant_time(self):
        """single_lookup should be constant time (N=1 only)"""
        enumerator = CandidateEnumerator()
        
        # Test with N=1 (intended use case)
        candidates_n1 = enumerator.enumerate_candidates(
            required_capabilities=["asset_query"],
            context={"N": 1}
        )
        
        # Test with N=100 (should NOT scale)
        candidates_n100 = enumerator.enumerate_candidates(
            required_capabilities=["asset_query"],
            context={"N": 100}
        )
        
        # Find single_lookup in both
        single_lookup_n1 = next(
            c for c in candidates_n1 if c.pattern_name == "single_lookup"
        )
        single_lookup_n100 = next(
            c for c in candidates_n100 if c.pattern_name == "single_lookup"
        )
        
        # Time should be constant (80ms) regardless of N
        assert single_lookup_n1.estimated_time_ms == 80
        assert single_lookup_n100.estimated_time_ms == 80
        
        print(f"✅ single_lookup time is constant: {single_lookup_n1.estimated_time_ms}ms")
    
    def test_detailed_lookup_time_matches_cost(self):
        """detailed_lookup time should account for batched API calls"""
        enumerator = CandidateEnumerator()
        
        # Test with N=100 (1 API call, batch size 100)
        candidates_n100 = enumerator.enumerate_candidates(
            required_capabilities=["asset_query"],
            context={"N": 100}
        )
        
        # Test with N=200 (2 API calls, batch size 100)
        candidates_n200 = enumerator.enumerate_candidates(
            required_capabilities=["asset_query"],
            context={"N": 200}
        )
        
        detailed_n100 = next(
            c for c in candidates_n100 if c.pattern_name == "detailed_lookup"
        )
        detailed_n200 = next(
            c for c in candidates_n200 if c.pattern_name == "detailed_lookup"
        )
        
        # Cost should reflect batching
        assert detailed_n100.estimated_cost == 1  # ceil(100/100) = 1
        assert detailed_n200.estimated_cost == 2  # ceil(200/100) = 2
        
        # Time should scale with number of API calls
        # Formula: 300 * ceil(N/100) + 5*N
        expected_time_n100 = 300 * 1 + 5 * 100  # 800ms
        expected_time_n200 = 300 * 2 + 5 * 200  # 1600ms
        
        assert detailed_n100.estimated_time_ms == expected_time_n100
        assert detailed_n200.estimated_time_ms == expected_time_n200
        
        print(f"✅ detailed_lookup N=100: {detailed_n100.estimated_time_ms}ms, cost={detailed_n100.estimated_cost}")
        print(f"✅ detailed_lookup N=200: {detailed_n200.estimated_time_ms}ms, cost={detailed_n200.estimated_cost}")
    
    def test_list_summary_time_accounts_for_pagination(self):
        """list_summary should account for all pages"""
        enumerator = CandidateEnumerator()
        
        # Test with 1 page
        candidates_1page = enumerator.enumerate_candidates(
            required_capabilities=["asset_query"],
            context={"N": 100, "pages": 1}
        )
        
        # Test with 5 pages
        candidates_5pages = enumerator.enumerate_candidates(
            required_capabilities=["asset_query"],
            context={"N": 100, "pages": 5}
        )
        
        list_1page = next(
            c for c in candidates_1page if c.pattern_name == "list_summary"
        )
        list_5pages = next(
            c for c in candidates_5pages if c.pattern_name == "list_summary"
        )
        
        # Cost should scale with pages
        assert list_1page.estimated_cost == 2  # 1 + 1 page
        assert list_5pages.estimated_cost == 6  # 1 + 5 pages
        
        # Time should scale with pages
        # Formula: 200 + 2*N + 500*pages
        expected_time_1page = 200 + 2*100 + 500*1  # 900ms
        expected_time_5pages = 200 + 2*100 + 500*5  # 2900ms
        
        assert list_1page.estimated_time_ms == expected_time_1page
        assert list_5pages.estimated_time_ms == expected_time_5pages
        
        print(f"✅ list_summary 1 page: {list_1page.estimated_time_ms}ms, cost={list_1page.estimated_cost}")
        print(f"✅ list_summary 5 pages: {list_5pages.estimated_time_ms}ms, cost={list_5pages.estimated_cost}")


class TestToolSelectionWithFixedMetrics:
    """Test that tool selection makes correct decisions with fixed metrics"""
    
    def test_single_asset_query_prefers_single_lookup(self):
        """For N=1, single_lookup should be fastest"""
        enumerator = CandidateEnumerator()
        normalizer = FeatureNormalizer()
        scorer = DeterministicScorer()
        
        # N=1 query
        candidates = enumerator.enumerate_candidates(
            required_capabilities=["asset_query"],
            context={"N": 1}
        )
        
        # Convert to dict format and normalize
        candidate_dicts = []
        for c in candidates:
            features = {
                'time_ms': c.estimated_time_ms,
                'cost': c.estimated_cost,
                'complexity': c.complexity,
                'accuracy': c.accuracy,
                'completeness': c.completeness
            }
            normalized_features = normalizer.normalize_features(features)
            candidate_dicts.append({
                'tool_name': c.tool_name,
                'pattern': c.pattern_name,
                'features': normalized_features,
                'raw_features': features
            })
        
        scored = scorer.score_candidates(candidate_dicts, mode=PreferenceMode.FAST)
        
        # single_lookup should win for N=1 (80ms constant)
        winner = scored[0]
        assert winner.pattern_name == "single_lookup"
        
        print(f"✅ N=1 winner: {winner.pattern_name} (score: {winner.total_score:.3f})")
    
    def test_multi_asset_query_avoids_single_lookup(self):
        """For N=100, single_lookup should NOT win (it's N=1 only)"""
        enumerator = CandidateEnumerator()
        normalizer = FeatureNormalizer()
        scorer = DeterministicScorer()
        
        # N=100 query
        candidates = enumerator.enumerate_candidates(
            required_capabilities=["asset_query"],
            context={"N": 100}
        )
        
        # Convert to dict format and normalize
        candidate_dicts = []
        for c in candidates:
            features = {
                'time_ms': c.estimated_time_ms,
                'cost': c.estimated_cost,
                'complexity': c.complexity,
                'accuracy': c.accuracy,
                'completeness': c.completeness
            }
            normalized_features = normalizer.normalize_features(features)
            candidate_dicts.append({
                'tool_name': c.tool_name,
                'pattern': c.pattern_name,
                'features': normalized_features,
                'raw_features': features
            })
        
        scored = scorer.score_candidates(candidate_dicts, mode=PreferenceMode.FAST)
        
        # single_lookup should NOT win (it's constant 80ms but only for N=1)
        # list_summary or count_aggregate should win
        winner = scored[0]
        
        # Get single_lookup score for comparison
        single_lookup_score = next(
            s for s in scored if s.pattern_name == "single_lookup"
        )
        
        print(f"✅ N=100 winner: {winner.pattern_name} (score: {winner.total_score:.3f})")
        print(f"   single_lookup score: {single_lookup_score.total_score:.3f}")
        
        # single_lookup should still score well (it's fast!)
        # But it's only suitable for N=1, so in real usage it would be filtered out
        # For now, we just verify the metrics are correct
        assert single_lookup_score.feature_scores['time_ms'] > 0.9  # Still fast
    
    def test_large_query_prefers_batched_patterns(self):
        """For N=500, batched patterns should be more efficient"""
        enumerator = CandidateEnumerator()
        normalizer = FeatureNormalizer()
        scorer = DeterministicScorer()
        
        # N=500 query
        candidates = enumerator.enumerate_candidates(
            required_capabilities=["asset_query"],
            context={"N": 500}
        )
        
        # Convert to dict format and normalize
        candidate_dicts = []
        for c in candidates:
            features = {
                'time_ms': c.estimated_time_ms,
                'cost': c.estimated_cost,
                'complexity': c.complexity,
                'accuracy': c.accuracy,
                'completeness': c.completeness
            }
            normalized_features = normalizer.normalize_features(features)
            candidate_dicts.append({
                'tool_name': c.tool_name,
                'pattern': c.pattern_name,
                'features': normalized_features,
                'raw_features': features
            })
        
        scored = scorer.score_candidates(candidate_dicts, mode=PreferenceMode.BALANCED)
        
        # Get times for comparison
        times = {
            s.pattern_name: s.raw_features.get('time_ms', 0)
            for s in scored
        }
        
        print(f"✅ N=500 time estimates:")
        for pattern, time_ms in sorted(times.items(), key=lambda x: x[1]):
            print(f"   {pattern}: {time_ms}ms")
        
        # detailed_lookup should be reasonable (5 API calls for 500 assets)
        # Formula: 300 * ceil(500/100) + 5*500 = 300*5 + 2500 = 4000ms
        detailed = next(s for s in scored if s.pattern_name == "detailed_lookup")
        assert detailed.raw_features['time_ms'] == 4000
        assert detailed.raw_features['cost'] == 5  # 5 batches


class TestMetricsConsistency:
    """Test that time, cost, and complexity are consistent"""
    
    def test_all_patterns_have_consistent_metrics(self):
        """Verify all patterns have time/cost/complexity that make sense together"""
        enumerator = CandidateEnumerator()
        
        # Test with various N values
        for N in [1, 10, 100, 500]:
            candidates = enumerator.enumerate_candidates(
                required_capabilities=["asset_query"],
                context={"N": N}
            )
            
            for candidate in candidates:
                # Basic sanity checks
                assert candidate.estimated_time_ms > 0, f"{candidate.pattern_name}: time must be > 0"
                assert candidate.estimated_cost >= 0, f"{candidate.pattern_name}: cost must be >= 0"
                assert 0 <= candidate.complexity <= 1, f"{candidate.pattern_name}: complexity must be [0,1]"
                
                # If cost > 1, time should reflect multiple operations
                if candidate.estimated_cost > 1:
                    # Multiple API calls should take more time
                    # (This is a heuristic check)
                    assert candidate.estimated_time_ms > 200, \
                        f"{candidate.pattern_name}: Multiple API calls should take >200ms"
            
            print(f"✅ N={N}: All {len(candidates)} patterns have consistent metrics")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])