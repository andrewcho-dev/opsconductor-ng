"""
Unit tests for Profile Loader

Tests loading and validation of optimization profiles from YAML.
"""

import pytest
from pathlib import Path
from pipeline.stages.stage_b.profile_loader import ProfileLoader, load_profiles
from pipeline.stages.stage_b.optimization_schemas import OptimizationProfilesConfig


class TestProfileLoader:
    """Test profile loading and validation"""
    
    def test_load_default_config(self):
        """Test loading default configuration"""
        loader = ProfileLoader()
        profiles = loader.load()
        
        assert isinstance(profiles, OptimizationProfilesConfig)
        assert profiles.version == "1.0"
        assert len(profiles.tools) > 0
    
    def test_load_asset_service_query(self):
        """Test asset-service-query profile"""
        loader = ProfileLoader()
        profiles = loader.load()
        
        assert "asset-service-query" in profiles.tools
        tool = profiles.tools["asset-service-query"]
        
        # Check defaults
        assert tool.defaults.accuracy_level == "cached"
        assert tool.defaults.freshness == "recent (5-15 min stale)"
        
        # Check capabilities
        assert "asset_query" in tool.capabilities
        capability = tool.capabilities["asset_query"]
        
        # Check patterns
        assert "count_aggregate" in capability.patterns
        assert "list_summary" in capability.patterns
        assert "single_lookup" in capability.patterns
        assert "detailed_lookup" in capability.patterns
    
    def test_count_aggregate_pattern(self):
        """Test count_aggregate pattern details"""
        loader = ProfileLoader()
        profiles = loader.load()
        
        pattern = profiles.tools["asset-service-query"].capabilities["asset_query"].patterns["count_aggregate"]
        
        # Check description
        assert "count" in pattern.description.lower()
        
        # Check expressions
        assert pattern.time_estimate_ms == "120 + 0.02 * N"
        assert pattern.cost_estimate == 1
        assert pattern.complexity_score == 0.1
        
        # Check quality (should inherit from defaults)
        assert pattern.accuracy_level == "cached"
        assert pattern.freshness == "recent (5-15 min stale)"
        
        # Check policy
        assert pattern.policy.production_safe is True
        assert pattern.policy.requires_approval is False
        
        # Check preference scores
        assert pattern.preference_match.speed == 0.95
        assert pattern.preference_match.accuracy == 0.6
        assert pattern.preference_match.cost == 0.95
    
    def test_asset_direct_poll_pattern(self):
        """Test asset-direct-poll parallel_poll pattern"""
        loader = ProfileLoader()
        profiles = loader.load()
        
        pattern = profiles.tools["asset-direct-poll"].capabilities["live_asset_query"].patterns["parallel_poll"]
        
        # Check it's marked as slow but accurate
        assert pattern.preference_match.speed < 0.5  # Slow
        assert pattern.preference_match.accuracy == 1.0  # Perfect accuracy
        
        # Check policy constraints
        assert pattern.policy.max_N_immediate == 50
        assert pattern.policy.requires_background_if == "N > 50"
        
        # Check quality
        assert pattern.accuracy_level == "realtime"
        assert pattern.freshness == "live (current state)"
    
    def test_defaults_inheritance(self):
        """Test that defaults are inherited by patterns"""
        loader = ProfileLoader()
        profiles = loader.load()
        
        # asset-service-query patterns should inherit cached/recent defaults
        tool = profiles.tools["asset-service-query"]
        for capability in tool.capabilities.values():
            for pattern in capability.patterns.values():
                assert pattern.accuracy_level == "cached"
                assert "recent" in pattern.freshness.lower()
        
        # asset-direct-poll patterns should inherit realtime/live defaults
        tool = profiles.tools["asset-direct-poll"]
        for capability in tool.capabilities.values():
            for pattern in capability.patterns.values():
                assert pattern.accuracy_level == "realtime"
                assert "live" in pattern.freshness.lower()
    
    def test_validate_expressions(self):
        """Test expression validation"""
        loader = ProfileLoader()
        loader.load()
        
        errors = loader.validate_expressions()
        
        # Should have no errors
        assert len(errors) == 0, f"Expression validation errors: {errors}"
    
    def test_get_tool_profile(self):
        """Test getting specific tool profile"""
        loader = ProfileLoader()
        loader.load()
        
        profile = loader.get_tool_profile("asset-service-query")
        assert profile is not None
        assert profile.description
        
        # Non-existent tool
        profile = loader.get_tool_profile("nonexistent-tool")
        assert profile is None
    
    def test_get_all_tools(self):
        """Test getting all tool profiles"""
        loader = ProfileLoader()
        loader.load()
        
        tools = loader.get_all_tools()
        assert isinstance(tools, dict)
        assert len(tools) >= 3  # At least asset-service-query, asset-direct-poll, info_display
        assert "asset-service-query" in tools
        assert "asset-direct-poll" in tools
        assert "info_display" in tools
    
    def test_caching(self):
        """Test that profiles are cached"""
        loader = ProfileLoader()
        
        profiles1 = loader.load()
        profiles2 = loader.load()
        
        # Should be the same object (cached)
        assert profiles1 is profiles2
        
        # Force reload
        profiles3 = loader.load(force_reload=True)
        
        # Should be different object
        assert profiles1 is not profiles3
    
    def test_convenience_function(self):
        """Test convenience function"""
        profiles = load_profiles()
        
        assert isinstance(profiles, OptimizationProfilesConfig)
        assert len(profiles.tools) > 0


class TestProfileValidation:
    """Test profile validation rules"""
    
    def test_pattern_count_limit(self):
        """Test that pattern count is limited"""
        loader = ProfileLoader()
        profiles = loader.load()
        
        # Each capability should have <= 5 patterns
        for tool in profiles.tools.values():
            for capability in tool.capabilities.values():
                assert len(capability.patterns) <= 5, \
                    f"Too many patterns: {len(capability.patterns)}"
    
    def test_preference_scores_valid(self):
        """Test that all preference scores are in [0, 1]"""
        loader = ProfileLoader()
        profiles = loader.load()
        
        for tool_name, tool in profiles.tools.items():
            for cap_name, capability in tool.capabilities.items():
                for pattern_name, pattern in capability.patterns.items():
                    scores = pattern.preference_match
                    
                    assert 0.0 <= scores.speed <= 1.0, \
                        f"{tool_name}.{cap_name}.{pattern_name}.speed out of range"
                    assert 0.0 <= scores.accuracy <= 1.0, \
                        f"{tool_name}.{cap_name}.{pattern_name}.accuracy out of range"
                    assert 0.0 <= scores.cost <= 1.0, \
                        f"{tool_name}.{cap_name}.{pattern_name}.cost out of range"
                    assert 0.0 <= scores.complexity <= 1.0, \
                        f"{tool_name}.{cap_name}.{pattern_name}.complexity out of range"
                    assert 0.0 <= scores.completeness <= 1.0, \
                        f"{tool_name}.{cap_name}.{pattern_name}.completeness out of range"
    
    def test_complexity_scores_valid(self):
        """Test that complexity scores are in [0, 1]"""
        loader = ProfileLoader()
        profiles = loader.load()
        
        for tool in profiles.tools.values():
            for capability in tool.capabilities.values():
                for pattern in capability.patterns.values():
                    assert 0.0 <= pattern.complexity_score <= 1.0


class TestRealWorldScenarios:
    """Test real-world usage scenarios"""
    
    def test_fast_count_query(self):
        """Test profile for 'how many linux assets' query"""
        loader = ProfileLoader()
        profiles = loader.load()
        
        # Should prefer asset-service-query count_aggregate
        pattern = profiles.tools["asset-service-query"].capabilities["asset_query"].patterns["count_aggregate"]
        
        # Should be fast and cheap
        assert pattern.preference_match.speed >= 0.9
        assert pattern.preference_match.cost >= 0.9
        
        # But moderate accuracy (cached)
        assert pattern.preference_match.accuracy < 0.8
    
    def test_accurate_verification_query(self):
        """Test profile for 'verify exact count' query"""
        loader = ProfileLoader()
        profiles = loader.load()
        
        # Should prefer asset-direct-poll parallel_poll
        pattern = profiles.tools["asset-direct-poll"].capabilities["live_asset_query"].patterns["parallel_poll"]
        
        # Should be accurate but slow/expensive
        assert pattern.preference_match.accuracy == 1.0
        assert pattern.preference_match.speed < 0.5
        assert pattern.preference_match.cost < 0.5
    
    def test_single_asset_lookup(self):
        """Test profile for single asset lookup"""
        loader = ProfileLoader()
        profiles = loader.load()
        
        # Should prefer asset-service-query single_lookup
        pattern = profiles.tools["asset-service-query"].capabilities["asset_query"].patterns["single_lookup"]
        
        # Should be very fast and cheap
        assert pattern.preference_match.speed >= 0.95
        assert pattern.preference_match.cost >= 0.95
        assert pattern.preference_match.complexity >= 0.95


if __name__ == "__main__":
    pytest.main([__file__, "-v"])