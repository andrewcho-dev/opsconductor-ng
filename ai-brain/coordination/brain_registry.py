"""
Brain Registry

Registry system for managing and discovering brain components in the
multi-brain AI architecture.
"""

import logging
from typing import Dict, Any, List, Optional, Type
from dataclasses import dataclass
from datetime import datetime
from enum import Enum

logger = logging.getLogger(__name__)

class BrainType(Enum):
    """Types of brains in the architecture"""
    INTENT_BRAIN = "intent_brain"
    TECHNICAL_BRAIN = "technical_brain"
    SME_BRAIN = "sme_brain"
    COORDINATOR = "coordinator"

class BrainStatus(Enum):
    """Brain status levels"""
    ACTIVE = "active"
    INACTIVE = "inactive"
    ERROR = "error"
    INITIALIZING = "initializing"

@dataclass
class BrainInfo:
    """Brain registration information"""
    brain_id: str
    brain_type: BrainType
    version: str
    status: BrainStatus
    capabilities: List[str]
    domains: List[str]
    instance: Any
    registered_at: datetime
    last_health_check: Optional[datetime]
    metadata: Dict[str, Any]

class BrainRegistry:
    """
    Brain Registry for Multi-Brain AI Architecture
    
    Manages registration, discovery, and health monitoring of brain components:
    1. Brain registration and deregistration
    2. Brain discovery and lookup
    3. Health monitoring and status tracking
    4. Capability and domain mapping
    5. Load balancing for multiple instances
    """
    
    def __init__(self):
        """Initialize the brain registry."""
        self.registry_id = "brain_registry"
        self.version = "1.0.0"
        
        # Brain storage
        self.registered_brains: Dict[str, BrainInfo] = {}
        self.brain_types: Dict[BrainType, List[str]] = {
            brain_type: [] for brain_type in BrainType
        }
        self.capability_index: Dict[str, List[str]] = {}
        self.domain_index: Dict[str, List[str]] = {}
        
        # Health monitoring
        self.health_check_interval = 60  # seconds
        self.max_failed_health_checks = 3
        
        logger.info(f"Brain Registry v{self.version} initialized")
    
    def register_brain(self, brain_id: str, brain_type: BrainType, 
                      brain_instance: Any, capabilities: List[str] = None,
                      domains: List[str] = None, metadata: Dict[str, Any] = None) -> bool:
        """
        Register a brain component.
        
        Args:
            brain_id: Unique identifier for the brain
            brain_type: Type of brain being registered
            brain_instance: The actual brain instance
            capabilities: List of capabilities the brain provides
            domains: List of domains the brain specializes in
            metadata: Additional metadata about the brain
            
        Returns:
            bool: True if registration was successful
        """
        try:
            logger.info(f"Registering brain: {brain_id} ({brain_type.value})")
            
            # Validate brain instance
            if not self._validate_brain_instance(brain_instance, brain_type):
                logger.error(f"Brain validation failed for {brain_id}")
                return False
            
            # Get brain version
            version = getattr(brain_instance, 'version', '1.0.0')
            
            # Create brain info
            brain_info = BrainInfo(
                brain_id=brain_id,
                brain_type=brain_type,
                version=version,
                status=BrainStatus.INITIALIZING,
                capabilities=capabilities or [],
                domains=domains or [],
                instance=brain_instance,
                registered_at=datetime.now(),
                last_health_check=None,
                metadata=metadata or {}
            )
            
            # Register the brain
            self.registered_brains[brain_id] = brain_info
            self.brain_types[brain_type].append(brain_id)
            
            # Update capability index
            for capability in brain_info.capabilities:
                if capability not in self.capability_index:
                    self.capability_index[capability] = []
                self.capability_index[capability].append(brain_id)
            
            # Update domain index
            for domain in brain_info.domains:
                if domain not in self.domain_index:
                    self.domain_index[domain] = []
                self.domain_index[domain].append(brain_id)
            
            # Perform initial health check
            if self._perform_health_check(brain_info):
                brain_info.status = BrainStatus.ACTIVE
                logger.info(f"Brain {brain_id} registered and activated successfully")
                return True
            else:
                brain_info.status = BrainStatus.ERROR
                logger.warning(f"Brain {brain_id} registered but failed health check")
                return False
                
        except Exception as e:
            logger.error(f"Brain registration failed for {brain_id}: {e}")
            return False
    
    def deregister_brain(self, brain_id: str) -> bool:
        """
        Deregister a brain component.
        
        Args:
            brain_id: ID of the brain to deregister
            
        Returns:
            bool: True if deregistration was successful
        """
        try:
            if brain_id not in self.registered_brains:
                logger.warning(f"Brain {brain_id} not found for deregistration")
                return False
            
            brain_info = self.registered_brains[brain_id]
            
            # Remove from type index
            if brain_id in self.brain_types[brain_info.brain_type]:
                self.brain_types[brain_info.brain_type].remove(brain_id)
            
            # Remove from capability index
            for capability in brain_info.capabilities:
                if capability in self.capability_index and brain_id in self.capability_index[capability]:
                    self.capability_index[capability].remove(brain_id)
                    if not self.capability_index[capability]:
                        del self.capability_index[capability]
            
            # Remove from domain index
            for domain in brain_info.domains:
                if domain in self.domain_index and brain_id in self.domain_index[domain]:
                    self.domain_index[domain].remove(brain_id)
                    if not self.domain_index[domain]:
                        del self.domain_index[domain]
            
            # Remove from registry
            del self.registered_brains[brain_id]
            
            logger.info(f"Brain {brain_id} deregistered successfully")
            return True
            
        except Exception as e:
            logger.error(f"Brain deregistration failed for {brain_id}: {e}")
            return False
    
    def get_brain(self, brain_id: str) -> Optional[Any]:
        """
        Get a brain instance by ID.
        
        Args:
            brain_id: ID of the brain to retrieve
            
        Returns:
            Brain instance or None if not found
        """
        brain_info = self.registered_brains.get(brain_id)
        if brain_info and brain_info.status == BrainStatus.ACTIVE:
            return brain_info.instance
        return None
    
    def get_brains_by_type(self, brain_type: BrainType) -> List[Any]:
        """
        Get all active brains of a specific type.
        
        Args:
            brain_type: Type of brains to retrieve
            
        Returns:
            List of brain instances
        """
        brain_ids = self.brain_types.get(brain_type, [])
        brains = []
        
        for brain_id in brain_ids:
            brain_info = self.registered_brains.get(brain_id)
            if brain_info and brain_info.status == BrainStatus.ACTIVE:
                brains.append(brain_info.instance)
        
        return brains
    
    def get_brains_by_capability(self, capability: str) -> List[Any]:
        """
        Get all active brains with a specific capability.
        
        Args:
            capability: Capability to search for
            
        Returns:
            List of brain instances with the capability
        """
        brain_ids = self.capability_index.get(capability, [])
        brains = []
        
        for brain_id in brain_ids:
            brain_info = self.registered_brains.get(brain_id)
            if brain_info and brain_info.status == BrainStatus.ACTIVE:
                brains.append(brain_info.instance)
        
        return brains
    
    def get_brains_by_domain(self, domain: str) -> List[Any]:
        """
        Get all active brains specializing in a domain.
        
        Args:
            domain: Domain to search for
            
        Returns:
            List of brain instances specializing in the domain
        """
        brain_ids = self.domain_index.get(domain, [])
        brains = []
        
        for brain_id in brain_ids:
            brain_info = self.registered_brains.get(brain_id)
            if brain_info and brain_info.status == BrainStatus.ACTIVE:
                brains.append(brain_info.instance)
        
        return brains
    
    def get_registered_brains(self) -> Dict[str, Dict[str, Any]]:
        """
        Get information about all registered brains.
        
        Returns:
            Dictionary of brain information
        """
        brain_summary = {}
        
        for brain_id, brain_info in self.registered_brains.items():
            brain_summary[brain_id] = {
                "brain_type": brain_info.brain_type.value,
                "version": brain_info.version,
                "status": brain_info.status.value,
                "capabilities": brain_info.capabilities,
                "domains": brain_info.domains,
                "registered_at": brain_info.registered_at.isoformat(),
                "last_health_check": (
                    brain_info.last_health_check.isoformat() 
                    if brain_info.last_health_check else None
                ),
                "metadata": brain_info.metadata
            }
        
        return brain_summary
    
    def _validate_brain_instance(self, brain_instance: Any, brain_type: BrainType) -> bool:
        """Validate that a brain instance meets requirements for its type."""
        try:
            # Basic validation - brain should have required methods
            required_methods = {
                BrainType.INTENT_BRAIN: ['analyze_intent'],
                BrainType.TECHNICAL_BRAIN: ['plan_execution'],
                BrainType.SME_BRAIN: ['provide_expertise'],
                BrainType.COORDINATOR: ['coordinate_request']
            }
            
            if brain_type in required_methods:
                for method_name in required_methods[brain_type]:
                    if not hasattr(brain_instance, method_name):
                        logger.error(f"Brain missing required method: {method_name}")
                        return False
            
            return True
            
        except Exception as e:
            logger.error(f"Brain validation error: {e}")
            return False
    
    def _perform_health_check(self, brain_info: BrainInfo) -> bool:
        """Perform health check on a brain instance."""
        try:
            brain_instance = brain_info.instance
            
            # Check if brain has health check method
            if hasattr(brain_instance, 'get_brain_status'):
                # Attempt to get status
                status = brain_instance.get_brain_status()
                if isinstance(status, dict) and status.get('status') == 'active':
                    brain_info.last_health_check = datetime.now()
                    return True
            
            # Fallback - check if brain instance is still valid
            if brain_instance is not None:
                brain_info.last_health_check = datetime.now()
                return True
            
            return False
            
        except Exception as e:
            logger.warning(f"Health check failed for {brain_info.brain_id}: {e}")
            return False
    
    async def perform_health_checks(self):
        """Perform health checks on all registered brains."""
        logger.debug("Performing health checks on all registered brains")
        
        for brain_id, brain_info in self.registered_brains.items():
            if brain_info.status == BrainStatus.ACTIVE:
                if self._perform_health_check(brain_info):
                    logger.debug(f"Health check passed for {brain_id}")
                else:
                    logger.warning(f"Health check failed for {brain_id}")
                    brain_info.status = BrainStatus.ERROR
    
    def get_registry_status(self) -> Dict[str, Any]:
        """Get current registry status and statistics."""
        status_counts = {}
        for status in BrainStatus:
            status_counts[status.value] = sum(
                1 for brain in self.registered_brains.values() 
                if brain.status == status
            )
        
        type_counts = {}
        for brain_type in BrainType:
            type_counts[brain_type.value] = len(self.brain_types[brain_type])
        
        return {
            "registry_id": self.registry_id,
            "version": self.version,
            "total_brains": len(self.registered_brains),
            "status_breakdown": status_counts,
            "type_breakdown": type_counts,
            "available_capabilities": list(self.capability_index.keys()),
            "available_domains": list(self.domain_index.keys()),
            "health_check_interval": self.health_check_interval
        }