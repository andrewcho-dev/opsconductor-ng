#!/usr/bin/env python3
"""
Capability Validation Hook
Ensures capability consistency during tool operations
"""
import asyncio
import logging
from typing import Dict, Any, List, Tuple
from capability_management_system import CapabilityRegistry, CapabilityValidator

logger = logging.getLogger(__name__)

class CapabilityValidationHook:
    """
    Integration hook for capability validation in OpsConductor pipelines
    """
    
    def __init__(self, db_connection_string: str):
        self.registry = CapabilityRegistry()
        self.validator = CapabilityValidator(self.registry, db_connection_string)
    
    def validate_tool_capabilities(self, capabilities: List[str]) -> Tuple[bool, List[str]]:
        """
        Validate tool capabilities before tool selection
        
        Args:
            capabilities: List of capability names from Stage A
            
        Returns:
            (is_valid, normalized_capabilities)
        """
        normalized = []
        warnings = []
        
        for cap in capabilities:
            canonical = self.registry.get_canonical_name(cap)
            
            if not self.registry.is_valid_capability(cap):
                warnings.append(f"Unknown capability '{cap}' - using as-is")
                normalized.append(cap)
            elif cap != canonical:
                logger.info(f"Normalized capability: {cap} → {canonical}")
                normalized.append(canonical)
            else:
                normalized.append(cap)
        
        return len(warnings) == 0, normalized
    
    async def ensure_system_consistency(self) -> bool:
        """
        Perform quick consistency check
        
        Returns:
            True if system is consistent, False otherwise
        """
        return await self.validator.continuous_validation()

# Singleton instance for easy integration
_validation_hook = None

def get_capability_hook(db_connection_string: str = None) -> CapabilityValidationHook:
    """Get the capability validation hook instance"""
    global _validation_hook
    
    if _validation_hook is None:
        if db_connection_string is None:
            import os
            db_connection_string = os.getenv(
                'DATABASE_URL', 
                'postgresql://opsconductor:opsconductor_secure_2024@localhost:5432/opsconductor'
            )
        _validation_hook = CapabilityValidationHook(db_connection_string)
    
    return _validation_hook

# Integration function for Stage B
def normalize_stage_a_capabilities(capabilities: List[str]) -> List[str]:
    """
    Normalize capabilities from Stage A before tool selection
    
    This function should be called in Stage B before candidate enumeration
    """
    hook = get_capability_hook()
    is_valid, normalized = hook.validate_tool_capabilities(capabilities)
    
    if not is_valid:
        logger.warning("Some capabilities could not be validated")
    
    return normalized