"""
Cache Key Generation Utilities

Provides utilities for generating consistent cache keys across
different pipeline stages.
"""

import hashlib
import json
from typing import Any, Dict, List


class CacheKeyGenerator:
    """
    Utility class for generating consistent cache keys.
    
    Ensures that identical requests generate identical keys,
    regardless of parameter order or formatting.
    """
    
    @staticmethod
    def normalize_string(s: str) -> str:
        """
        Normalize string for consistent hashing.
        
        Args:
            s: String to normalize
            
        Returns:
            Normalized string (lowercase, stripped)
        """
        return s.strip().lower()
    
    @staticmethod
    def hash_data(data: Dict[str, Any]) -> str:
        """
        Generate hash from data dictionary.
        
        Args:
            data: Data to hash
            
        Returns:
            16-character hash string
        """
        # Sort keys for consistent hashing
        sorted_data = json.dumps(data, sort_keys=True)
        hash_value = hashlib.sha256(sorted_data.encode()).hexdigest()
        return hash_value[:16]
    
    @staticmethod
    def generate_key(prefix: str, data: Dict[str, Any]) -> str:
        """
        Generate cache key with prefix.
        
        Args:
            prefix: Key prefix (e.g., "stage_a")
            data: Data to hash
            
        Returns:
            Full cache key
        """
        hash_value = CacheKeyGenerator.hash_data(data)
        return f"opsconductor:{prefix}:{hash_value}"
    
    @staticmethod
    def stage_a_key(user_request: str) -> str:
        """Generate Stage A cache key"""
        return CacheKeyGenerator.generate_key(
            "stage_a",
            {"request": CacheKeyGenerator.normalize_string(user_request)}
        )
    
    @staticmethod
    def stage_b_key(capabilities: List[str], risk_level: str = "unknown") -> str:
        """Generate Stage B cache key"""
        return CacheKeyGenerator.generate_key(
            "stage_b",
            {
                "capabilities": sorted(capabilities),
                "risk": risk_level
            }
        )
    
    @staticmethod
    def stage_c_key(action: str, entities: List[Dict[str, Any]], tools: List[str]) -> str:
        """Generate Stage C cache key"""
        # Normalize entities for consistent hashing
        normalized_entities = sorted([
            f"{e.get('type', '')}:{CacheKeyGenerator.normalize_string(e.get('value', ''))}"
            for e in entities
        ])
        
        return CacheKeyGenerator.generate_key(
            "stage_c",
            {
                "action": CacheKeyGenerator.normalize_string(action),
                "entities": normalized_entities,
                "tools": sorted(tools)
            }
        )