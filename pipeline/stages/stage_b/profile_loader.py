"""
YAML Profile Loader (with Database Support)

Loads and validates tool optimization profiles from YAML configuration or database.
Supports inheritance and validation at load time.

Database Mode (default):
- Loads tools from PostgreSQL via ToolCatalogService
- Transforms database format to OptimizationProfilesConfig
- Caches for 5 minutes (matching ToolCatalogService TTL)

YAML Mode (fallback):
- Loads from YAML file
- Useful for testing and migration
"""

import yaml
from pathlib import Path
from typing import Optional, Dict, Any, List
import logging
import os
import time

from .optimization_schemas import (
    OptimizationProfilesConfig, 
    ToolProfile,
    ToolDefaults,
    CapabilityProfile,
    PatternProfile,
    PolicyConfig,
    PreferenceMatchScores
)


logger = logging.getLogger(__name__)


class ProfileLoader:
    """
    Loads tool optimization profiles from database or YAML
    
    Features:
    - Database-backed loading (default)
    - YAML fallback for testing/migration
    - Pydantic validation at load time
    - Inheritance (tool defaults → capability → pattern)
    - Expression validation
    - Caching for performance
    """
    
    def __init__(
        self, 
        config_path: Optional[Path] = None,
        use_database: bool = True,
        database_url: Optional[str] = None
    ):
        """
        Initialize loader - DATABASE ONLY, NO YAML
        
        Args:
            config_path: DEPRECATED - not used
            use_database: DEPRECATED - always True
            database_url: Database URL (defaults to env var)
        """
        # YAML support removed - database only
        self.config_path = None
        self.use_database = True  # Always True
        self.database_url = database_url
        self._profiles: Optional[OptimizationProfilesConfig] = None
        self._catalog_service = None
        
        # Initialize metrics collector
        try:
            from pipeline.services.metrics_collector import get_metrics_collector
            self._metrics = get_metrics_collector()
        except ImportError:
            self._metrics = None
            logger.warning("Metrics collector not available")
    
    def _get_catalog_service(self):
        """Get or create ToolCatalogService instance"""
        if self._catalog_service is None:
            from pipeline.services.tool_catalog_service import ToolCatalogService
            self._catalog_service = ToolCatalogService(database_url=self.database_url)
        return self._catalog_service
    
    def _transform_database_to_profiles(self, tools_data: List[Dict[str, Any]]) -> OptimizationProfilesConfig:
        """
        Transform database format to OptimizationProfilesConfig
        
        Args:
            tools_data: List of tools from database (with nested capabilities/patterns)
            
        Returns:
            OptimizationProfilesConfig instance
        """
        tools_dict = {}
        
        for tool_data in tools_data:
            tool_name = tool_data['tool_name']
            
            # Extract defaults from tool
            defaults_data = tool_data.get('defaults', {})
            tool_defaults = ToolDefaults(
                accuracy_level=defaults_data.get('accuracy_level'),
                freshness=defaults_data.get('freshness'),
                data_source=defaults_data.get('data_source'),
                scope=defaults_data.get('scope'),
                completeness=defaults_data.get('completeness')
            )
            
            # Transform capabilities
            capabilities_dict = {}
            for cap_name, cap_data in tool_data.get('capabilities', {}).items():
                patterns_dict = {}
                
                for pattern_data in cap_data.get('patterns', []):
                    pattern_name = pattern_data['pattern_name']
                    
                    # Transform policy
                    policy_data = pattern_data.get('policy', {})
                    policy = PolicyConfig(
                        max_cost=policy_data.get('max_cost'),
                        max_N_immediate=policy_data.get('max_N_immediate'),
                        requires_approval=policy_data.get('requires_approval', False),
                        requires_background_if=policy_data.get('requires_background_if'),
                        production_safe=policy_data.get('production_safe', True)
                    )
                    
                    # Transform preference_match
                    pref_data = pattern_data.get('preference_match', {})
                    preference_match = PreferenceMatchScores(
                        speed=pref_data.get('speed', 0.5),
                        accuracy=pref_data.get('accuracy', 0.5),
                        cost=pref_data.get('cost', 0.5),
                        complexity=pref_data.get('complexity', 0.5),
                        completeness=pref_data.get('completeness', 0.5)
                    )
                    
                    # Transform required_inputs to requires_inputs (field name difference)
                    required_inputs = pattern_data.get('required_inputs', [])
                    requires_inputs = [inp.get('name', str(inp)) if isinstance(inp, dict) else str(inp) 
                                      for inp in required_inputs]
                    
                    # Create pattern
                    pattern = PatternProfile(
                        description=pattern_data.get('description', ''),
                        typical_use_cases=pattern_data.get('typical_use_cases', []),
                        time_estimate_ms=pattern_data.get('time_estimate_ms', '100'),
                        cost_estimate=pattern_data.get('cost_estimate', 1),
                        complexity_score=pattern_data.get('complexity_score', 0.5),
                        accuracy_level=pattern_data.get('accuracy_level'),
                        freshness=pattern_data.get('freshness'),
                        scope=pattern_data.get('scope'),
                        completeness=pattern_data.get('completeness'),
                        data_source=pattern_data.get('data_source'),
                        limitations=pattern_data.get('limitations', []),
                        requires_inputs=requires_inputs,
                        policy=policy,
                        preference_match=preference_match
                    )
                    
                    patterns_dict[pattern_name] = pattern
                
                # Create capability
                if patterns_dict:  # Only add capability if it has patterns
                    capabilities_dict[cap_name] = CapabilityProfile(patterns=patterns_dict)
            
            # Create tool profile
            if capabilities_dict:  # Only add tool if it has capabilities
                tool_profile = ToolProfile(
                    description=tool_data.get('description', ''),
                    defaults=tool_defaults,
                    capabilities=capabilities_dict
                )
                tools_dict[tool_name] = tool_profile
        
        # Create and return config
        config = OptimizationProfilesConfig(
            version="1.0",
            tools=tools_dict
        )
        
        return config
    
    def _load_from_database(self) -> OptimizationProfilesConfig:
        """
        Load profiles from database
        
        Returns:
            Validated optimization profiles
        """
        logger.info("Loading optimization profiles from database")
        
        try:
            service = self._get_catalog_service()
            
            # Get all tools with full structure
            tools_data = service.get_all_tools_with_structure()
            
            # Transform to OptimizationProfilesConfig
            self._profiles = self._transform_database_to_profiles(tools_data)
            
            logger.info(f"Loaded {len(self._profiles.tools)} tool profiles from database")
            
            # Log summary
            for tool_name, tool_profile in self._profiles.tools.items():
                pattern_count = sum(
                    len(cap.patterns)
                    for cap in tool_profile.capabilities.values()
                )
                logger.debug(f"  {tool_name}: {len(tool_profile.capabilities)} capabilities, {pattern_count} patterns")
            
            return self._profiles
            
        except Exception as e:
            logger.error(f"Error loading from database: {e}")
            raise ValueError(f"Failed to load profiles from database: {e}") from e
    
    def _load_from_yaml(self) -> OptimizationProfilesConfig:
        """
        YAML LOADING REMOVED - DATABASE ONLY
        """
        raise NotImplementedError("YAML loading has been removed. Use database only.")
    
    def load(self, force_reload: bool = False) -> OptimizationProfilesConfig:
        """
        Load profiles from database ONLY
        
        Args:
            force_reload: Force reload even if cached
            
        Returns:
            Validated optimization profiles
            
        Raises:
            ValueError: If database load fails
        """
        # Return cached if available
        if self._profiles is not None and not force_reload:
            return self._profiles
        
        # ALWAYS load from database - NO YAML FALLBACK
        return self._load_from_database()
    
    def get_tool_profile(self, tool_name: str) -> Optional[ToolProfile]:
        """
        Get profile for a specific tool
        
        Args:
            tool_name: Name of the tool
            
        Returns:
            Tool profile or None if not found
        """
        start_time = time.time()
        from_cache = self._profiles is not None
        
        try:
            if self._profiles is None:
                self.load()
            
            result = self._profiles.tools.get(tool_name)
            
            # Record metrics
            if self._metrics:
                duration_ms = (time.time() - start_time) * 1000
                self._metrics.record_tool_load(
                    tool_name=tool_name,
                    duration_ms=duration_ms,
                    from_cache=from_cache,
                    success=result is not None
                )
            
            return result
            
        except Exception as e:
            # Record error
            if self._metrics:
                duration_ms = (time.time() - start_time) * 1000
                self._metrics.record_tool_load(
                    tool_name=tool_name,
                    duration_ms=duration_ms,
                    from_cache=from_cache,
                    success=False
                )
            raise
    
    def get_all_tools(self) -> dict[str, ToolProfile]:
        """
        Get all tool profiles
        
        Returns:
            Dictionary of tool name -> profile
        """
        if self._profiles is None:
            self.load()
        
        return self._profiles.tools
    
    def invalidate_cache(self, tool_name: Optional[str] = None):
        """
        Invalidate cached profiles
        
        Args:
            tool_name: Specific tool to invalidate (None = invalidate all)
        """
        if tool_name is None:
            # Invalidate entire cache
            self._profiles = None
            logger.info("ProfileLoader cache invalidated (all tools)")
            
            # Record cache eviction
            if self._metrics:
                self._metrics.record_cache_eviction()
                self._metrics.update_cache_size(0)
        else:
            # For now, invalidate entire cache since profiles are loaded together
            # In future, could implement partial invalidation
            self._profiles = None
            logger.info(f"ProfileLoader cache invalidated (tool: {tool_name})")
            
            # Record cache eviction
            if self._metrics:
                self._metrics.record_cache_eviction()
                self._metrics.update_cache_size(0)
        
        # Also invalidate ToolCatalogService cache if using database
        if self.use_database and self._catalog_service is not None:
            self._catalog_service._clear_cache(tool_name)
    
    def reload(self, tool_name: Optional[str] = None) -> OptimizationProfilesConfig:
        """
        Force reload profiles from source
        
        Args:
            tool_name: Specific tool to reload (None = reload all)
            
        Returns:
            Reloaded profiles
        """
        self.invalidate_cache(tool_name)
        return self.load(force_reload=True)
    
    def validate_expressions(self) -> list[str]:
        """
        Validate all expressions in profiles
        
        Returns:
            List of validation errors (empty if all valid)
        """
        from .safe_math_eval import SafeMathEvaluator
        
        if self._profiles is None:
            self.load()
        
        evaluator = SafeMathEvaluator()
        errors = []
        
        # Test context with reasonable values
        test_context = {
            'N': 100,
            'pages': 5,
            'p95_latency': 150,
            'cost': 10,
            'time_ms': 1000
        }
        
        for tool_name, tool_profile in self._profiles.tools.items():
            for cap_name, capability in tool_profile.capabilities.items():
                for pattern_name, pattern in capability.patterns.items():
                    # Test time_estimate_ms
                    try:
                        evaluator.evaluate(pattern.time_estimate_ms, test_context)
                    except Exception as e:
                        errors.append(
                            f"{tool_name}.{cap_name}.{pattern_name}.time_estimate_ms: {e}"
                        )
                    
                    # Test cost_estimate
                    try:
                        evaluator.evaluate(pattern.cost_estimate, test_context)
                    except Exception as e:
                        errors.append(
                            f"{tool_name}.{cap_name}.{pattern_name}.cost_estimate: {e}"
                        )
                    
                    # Test policy condition if present
                    if pattern.policy.requires_background_if:
                        try:
                            # Just parse it, don't evaluate
                            import ast
                            ast.parse(pattern.policy.requires_background_if, mode='eval')
                        except Exception as e:
                            errors.append(
                                f"{tool_name}.{cap_name}.{pattern_name}.policy.requires_background_if: {e}"
                            )
        
        return errors


# Global loader instance
_loader: Optional[ProfileLoader] = None


def get_loader(
    config_path: Optional[Path] = None,
    use_database: Optional[bool] = None,
    database_url: Optional[str] = None
) -> ProfileLoader:
    """
    Get global profile loader instance
    
    Args:
        config_path: Optional custom config path
        use_database: Whether to use database (default: True)
        database_url: Database URL (defaults to env var)
        
    Returns:
        ProfileLoader instance
    """
    global _loader
    
    # Create new loader if:
    # 1. No loader exists
    # 2. Custom config path provided
    # 3. Database mode changed
    if _loader is None or config_path is not None or use_database is not None:
        # Use database by default
        if use_database is None:
            use_database = True
        
        _loader = ProfileLoader(
            config_path=config_path,
            use_database=use_database,
            database_url=database_url
        )
    
    return _loader


def load_profiles(
    force_reload: bool = False,
    use_database: Optional[bool] = None
) -> OptimizationProfilesConfig:
    """
    Convenience function to load profiles
    
    Args:
        force_reload: Force reload even if cached
        use_database: Whether to use database (default: True)
        
    Returns:
        Validated optimization profiles
    """
    return get_loader(use_database=use_database).load(force_reload=force_reload)