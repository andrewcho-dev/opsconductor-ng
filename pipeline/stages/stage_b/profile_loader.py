"""
YAML Profile Loader

Loads and validates tool optimization profiles from YAML configuration.
Supports inheritance and validation at load time.
"""

import yaml
from pathlib import Path
from typing import Optional
import logging

from .optimization_schemas import OptimizationProfilesConfig, ToolProfile


logger = logging.getLogger(__name__)


class ProfileLoader:
    """
    Loads tool optimization profiles from YAML
    
    Features:
    - Pydantic validation at load time
    - Inheritance (tool defaults → capability → pattern)
    - Expression validation
    - Caching for performance
    """
    
    def __init__(self, config_path: Optional[Path] = None):
        """
        Initialize loader
        
        Args:
            config_path: Path to YAML config file. If None, uses default location.
        """
        if config_path is None:
            # Default location
            config_path = Path(__file__).parent.parent.parent / "config" / "tool_optimization_profiles.yaml"
        
        self.config_path = Path(config_path)
        self._profiles: Optional[OptimizationProfilesConfig] = None
    
    def load(self, force_reload: bool = False) -> OptimizationProfilesConfig:
        """
        Load profiles from YAML
        
        Args:
            force_reload: Force reload even if cached
            
        Returns:
            Validated optimization profiles
            
        Raises:
            FileNotFoundError: If config file doesn't exist
            ValueError: If config is invalid
        """
        # Return cached if available
        if self._profiles is not None and not force_reload:
            return self._profiles
        
        # Check file exists
        if not self.config_path.exists():
            raise FileNotFoundError(
                f"Optimization profiles config not found: {self.config_path}\n"
                f"Please create the config file or specify a different path."
            )
        
        # Load YAML
        logger.info(f"Loading optimization profiles from {self.config_path}")
        try:
            with open(self.config_path, 'r') as f:
                raw_config = yaml.safe_load(f)
        except yaml.YAMLError as e:
            raise ValueError(f"Invalid YAML in {self.config_path}: {e}") from e
        
        # Validate with Pydantic
        try:
            self._profiles = OptimizationProfilesConfig(**raw_config)
        except Exception as e:
            raise ValueError(f"Invalid optimization profiles config: {e}") from e
        
        logger.info(f"Loaded {len(self._profiles.tools)} tool profiles")
        
        # Log summary
        for tool_name, tool_profile in self._profiles.tools.items():
            pattern_count = sum(
                len(cap.patterns)
                for cap in tool_profile.capabilities.values()
            )
            logger.debug(f"  {tool_name}: {len(tool_profile.capabilities)} capabilities, {pattern_count} patterns")
        
        return self._profiles
    
    def get_tool_profile(self, tool_name: str) -> Optional[ToolProfile]:
        """
        Get profile for a specific tool
        
        Args:
            tool_name: Name of the tool
            
        Returns:
            Tool profile or None if not found
        """
        if self._profiles is None:
            self.load()
        
        return self._profiles.tools.get(tool_name)
    
    def get_all_tools(self) -> dict[str, ToolProfile]:
        """
        Get all tool profiles
        
        Returns:
            Dictionary of tool name -> profile
        """
        if self._profiles is None:
            self.load()
        
        return self._profiles.tools
    
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


def get_loader(config_path: Optional[Path] = None) -> ProfileLoader:
    """
    Get global profile loader instance
    
    Args:
        config_path: Optional custom config path
        
    Returns:
        ProfileLoader instance
    """
    global _loader
    
    if _loader is None or config_path is not None:
        _loader = ProfileLoader(config_path)
    
    return _loader


def load_profiles(force_reload: bool = False) -> OptimizationProfilesConfig:
    """
    Convenience function to load profiles
    
    Args:
        force_reload: Force reload even if cached
        
    Returns:
        Validated optimization profiles
    """
    return get_loader().load(force_reload=force_reload)