#!/usr/bin/env python3
"""
Service Discovery System
Provides service registration, discovery, and load balancing
"""

import asyncio
import aiohttp
import json
import time
import logging
from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta
from enum import Enum
import hashlib
import random

logger = logging.getLogger(__name__)

class ServiceStatus(Enum):
    HEALTHY = "healthy"
    UNHEALTHY = "unhealthy"
    STARTING = "starting"
    STOPPING = "stopping"

@dataclass
class ServiceInstance:
    """Represents a service instance"""
    id: str
    name: str
    host: str
    port: int
    health_check_url: str
    metadata: Dict[str, Any]
    status: ServiceStatus = ServiceStatus.STARTING
    last_heartbeat: float = 0
    registration_time: float = 0
    version: str = "1.0.0"
    tags: List[str] = None

    def __post_init__(self):
        if self.tags is None:
            self.tags = []
        if self.registration_time == 0:
            self.registration_time = time.time()
        if self.last_heartbeat == 0:
            self.last_heartbeat = time.time()

    @property
    def url(self) -> str:
        """Get the base URL for this service instance"""
        return f"http://{self.host}:{self.port}"

    @property
    def is_healthy(self) -> bool:
        """Check if instance is considered healthy"""
        return (self.status == ServiceStatus.HEALTHY and 
                time.time() - self.last_heartbeat < 60)  # 60 second timeout

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        result = asdict(self)
        result['status'] = self.status.value
        result['url'] = self.url
        result['is_healthy'] = self.is_healthy
        return result

class LoadBalancer:
    """Load balancing strategies"""
    
    @staticmethod
    def round_robin(instances: List[ServiceInstance], state: Dict[str, Any]) -> Optional[ServiceInstance]:
        """Round robin load balancing"""
        if not instances:
            return None
        
        counter = state.get('counter', 0)
        instance = instances[counter % len(instances)]
        state['counter'] = counter + 1
        return instance

    @staticmethod
    def random_choice(instances: List[ServiceInstance], state: Dict[str, Any]) -> Optional[ServiceInstance]:
        """Random selection"""
        return random.choice(instances) if instances else None

    @staticmethod
    def least_connections(instances: List[ServiceInstance], state: Dict[str, Any]) -> Optional[ServiceInstance]:
        """Select instance with least connections (simulated)"""
        if not instances:
            return None
        
        # In a real implementation, this would track actual connections
        # For now, we'll use a simple random selection with preference for newer instances
        weights = []
        for instance in instances:
            # Newer instances get higher weight (lower connection assumption)
            age = time.time() - instance.registration_time
            weight = max(1, 100 - age)  # Newer = higher weight
            weights.append(weight)
        
        return random.choices(instances, weights=weights)[0]

class ServiceRegistry:
    """Service registry for service discovery"""
    
    def __init__(self):
        self.services: Dict[str, Dict[str, ServiceInstance]] = {}  # service_name -> {instance_id -> instance}
        self.load_balancer_state: Dict[str, Dict[str, Any]] = {}  # service_name -> state
        self.health_check_interval = 30  # seconds
        self.cleanup_interval = 60  # seconds
        self.running = False

    async def register_service(self, instance: ServiceInstance) -> bool:
        """Register a service instance"""
        try:
            if instance.name not in self.services:
                self.services[instance.name] = {}
            
            self.services[instance.name][instance.id] = instance
            logger.info(f"Registered service instance: {instance.name}#{instance.id} at {instance.url}")
            
            # Initialize load balancer state if needed
            if instance.name not in self.load_balancer_state:
                self.load_balancer_state[instance.name] = {}
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to register service {instance.name}#{instance.id}: {e}")
            return False

    async def deregister_service(self, service_name: str, instance_id: str) -> bool:
        """Deregister a service instance"""
        try:
            if service_name in self.services and instance_id in self.services[service_name]:
                del self.services[service_name][instance_id]
                logger.info(f"Deregistered service instance: {service_name}#{instance_id}")
                
                # Clean up empty service entries
                if not self.services[service_name]:
                    del self.services[service_name]
                    if service_name in self.load_balancer_state:
                        del self.load_balancer_state[service_name]
                
                return True
            return False
            
        except Exception as e:
            logger.error(f"Failed to deregister service {service_name}#{instance_id}: {e}")
            return False

    async def heartbeat(self, service_name: str, instance_id: str) -> bool:
        """Update heartbeat for a service instance"""
        try:
            if (service_name in self.services and 
                instance_id in self.services[service_name]):
                
                instance = self.services[service_name][instance_id]
                instance.last_heartbeat = time.time()
                
                # Update status to healthy if it was starting
                if instance.status == ServiceStatus.STARTING:
                    instance.status = ServiceStatus.HEALTHY
                
                return True
            return False
            
        except Exception as e:
            logger.error(f"Failed to update heartbeat for {service_name}#{instance_id}: {e}")
            return False

    def discover_service(self, service_name: str, tags: List[str] = None) -> List[ServiceInstance]:
        """Discover healthy instances of a service"""
        if service_name not in self.services:
            return []
        
        instances = []
        for instance in self.services[service_name].values():
            if not instance.is_healthy:
                continue
            
            # Filter by tags if specified
            if tags:
                if not all(tag in instance.tags for tag in tags):
                    continue
            
            instances.append(instance)
        
        return instances

    def get_service_instance(self, service_name: str, strategy: str = "round_robin", tags: List[str] = None) -> Optional[ServiceInstance]:
        """Get a service instance using load balancing"""
        instances = self.discover_service(service_name, tags)
        
        if not instances:
            return None
        
        # Get load balancer state for this service
        state = self.load_balancer_state.get(service_name, {})
        
        # Apply load balancing strategy
        if strategy == "round_robin":
            instance = LoadBalancer.round_robin(instances, state)
        elif strategy == "random":
            instance = LoadBalancer.random_choice(instances, state)
        elif strategy == "least_connections":
            instance = LoadBalancer.least_connections(instances, state)
        else:
            logger.warning(f"Unknown load balancing strategy: {strategy}, using round_robin")
            instance = LoadBalancer.round_robin(instances, state)
        
        # Update state
        self.load_balancer_state[service_name] = state
        
        return instance

    def get_all_services(self) -> Dict[str, List[Dict[str, Any]]]:
        """Get all registered services"""
        result = {}
        for service_name, instances in self.services.items():
            result[service_name] = [instance.to_dict() for instance in instances.values()]
        return result

    def get_service_stats(self, service_name: str) -> Dict[str, Any]:
        """Get statistics for a service"""
        if service_name not in self.services:
            return {}
        
        instances = list(self.services[service_name].values())
        healthy_count = sum(1 for i in instances if i.is_healthy)
        
        return {
            "service_name": service_name,
            "total_instances": len(instances),
            "healthy_instances": healthy_count,
            "unhealthy_instances": len(instances) - healthy_count,
            "instances": [i.to_dict() for i in instances]
        }

    async def health_check_instance(self, instance: ServiceInstance) -> bool:
        """Perform health check on an instance"""
        try:
            async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=10)) as session:
                async with session.get(instance.health_check_url) as response:
                    if response.status == 200:
                        instance.status = ServiceStatus.HEALTHY
                        instance.last_heartbeat = time.time()
                        return True
                    else:
                        instance.status = ServiceStatus.UNHEALTHY
                        return False
                        
        except Exception as e:
            logger.debug(f"Health check failed for {instance.name}#{instance.id}: {e}")
            instance.status = ServiceStatus.UNHEALTHY
            return False

    async def run_health_checks(self):
        """Run health checks for all instances"""
        tasks = []
        for service_instances in self.services.values():
            for instance in service_instances.values():
                if instance.health_check_url:
                    tasks.append(self.health_check_instance(instance))
        
        if tasks:
            await asyncio.gather(*tasks, return_exceptions=True)

    async def cleanup_stale_instances(self):
        """Remove stale instances that haven't sent heartbeats"""
        current_time = time.time()
        stale_threshold = 120  # 2 minutes
        
        to_remove = []
        for service_name, instances in self.services.items():
            for instance_id, instance in instances.items():
                if current_time - instance.last_heartbeat > stale_threshold:
                    to_remove.append((service_name, instance_id))
        
        for service_name, instance_id in to_remove:
            await self.deregister_service(service_name, instance_id)
            logger.info(f"Removed stale instance: {service_name}#{instance_id}")

    async def start_background_tasks(self):
        """Start background maintenance tasks"""
        self.running = True
        
        async def health_check_loop():
            while self.running:
                try:
                    await self.run_health_checks()
                    await asyncio.sleep(self.health_check_interval)
                except Exception as e:
                    logger.error(f"Health check loop error: {e}")
                    await asyncio.sleep(5)
        
        async def cleanup_loop():
            while self.running:
                try:
                    await self.cleanup_stale_instances()
                    await asyncio.sleep(self.cleanup_interval)
                except Exception as e:
                    logger.error(f"Cleanup loop error: {e}")
                    await asyncio.sleep(10)
        
        # Start background tasks
        asyncio.create_task(health_check_loop())
        asyncio.create_task(cleanup_loop())
        
        logger.info("Service registry background tasks started")

    def stop_background_tasks(self):
        """Stop background tasks"""
        self.running = False
        logger.info("Service registry background tasks stopped")

class ServiceClient:
    """Client for making requests to discovered services"""
    
    def __init__(self, registry: ServiceRegistry, service_name: str, strategy: str = "round_robin"):
        self.registry = registry
        self.service_name = service_name
        self.strategy = strategy

    async def get(self, path: str, **kwargs) -> Any:
        """Make GET request to service"""
        return await self._request("GET", path, **kwargs)

    async def post(self, path: str, **kwargs) -> Any:
        """Make POST request to service"""
        return await self._request("POST", path, **kwargs)

    async def put(self, path: str, **kwargs) -> Any:
        """Make PUT request to service"""
        return await self._request("PUT", path, **kwargs)

    async def delete(self, path: str, **kwargs) -> Any:
        """Make DELETE request to service"""
        return await self._request("DELETE", path, **kwargs)

    async def _request(self, method: str, path: str, **kwargs) -> Any:
        """Make HTTP request to discovered service instance"""
        instance = self.registry.get_service_instance(self.service_name, self.strategy)
        
        if not instance:
            raise Exception(f"No healthy instances found for service: {self.service_name}")
        
        url = f"{instance.url}{path}"
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.request(method, url, **kwargs) as response:
                    if response.content_type == 'application/json':
                        return await response.json()
                    else:
                        return await response.text()
                        
        except Exception as e:
            logger.error(f"Request failed to {instance.name}#{instance.id}: {e}")
            # Mark instance as unhealthy
            instance.status = ServiceStatus.UNHEALTHY
            raise

# Global service registry
service_registry = ServiceRegistry()

class ServiceRegistrar:
    """Helper class for service registration"""
    
    def __init__(self, service_name: str, host: str, port: int, health_check_path: str = "/health"):
        self.service_name = service_name
        self.host = host
        self.port = port
        self.health_check_path = health_check_path
        self.instance_id = self._generate_instance_id()
        self.registered = False

    def _generate_instance_id(self) -> str:
        """Generate unique instance ID"""
        data = f"{self.service_name}-{self.host}-{self.port}-{time.time()}"
        return hashlib.md5(data.encode()).hexdigest()[:8]

    async def register(self, metadata: Dict[str, Any] = None, tags: List[str] = None, version: str = "1.0.0") -> bool:
        """Register this service instance"""
        instance = ServiceInstance(
            id=self.instance_id,
            name=self.service_name,
            host=self.host,
            port=self.port,
            health_check_url=f"http://{self.host}:{self.port}{self.health_check_path}",
            metadata=metadata or {},
            tags=tags or [],
            version=version
        )
        
        success = await service_registry.register_service(instance)
        if success:
            self.registered = True
            # Start heartbeat task
            asyncio.create_task(self._heartbeat_loop())
        
        return success

    async def deregister(self) -> bool:
        """Deregister this service instance"""
        if self.registered:
            success = await service_registry.deregister_service(self.service_name, self.instance_id)
            if success:
                self.registered = False
            return success
        return True

    async def _heartbeat_loop(self):
        """Send periodic heartbeats"""
        while self.registered:
            try:
                await service_registry.heartbeat(self.service_name, self.instance_id)
                await asyncio.sleep(30)  # Heartbeat every 30 seconds
            except Exception as e:
                logger.error(f"Heartbeat failed for {self.service_name}#{self.instance_id}: {e}")
                await asyncio.sleep(5)

# Example usage
async def example_usage():
    """Example of service discovery usage"""
    
    # Start the registry background tasks
    await service_registry.start_background_tasks()
    
    # Register some services
    registrar1 = ServiceRegistrar("identity-service", "localhost", 3001)
    registrar2 = ServiceRegistrar("identity-service", "localhost", 3002)  # Second instance
    
    await registrar1.register(metadata={"version": "1.0.0"}, tags=["auth", "users"])
    await registrar2.register(metadata={"version": "1.0.1"}, tags=["auth", "users"])
    
    # Discover services
    instances = service_registry.discover_service("identity-service")
    print(f"Found {len(instances)} instances of identity-service")
    
    # Use service client
    client = ServiceClient(service_registry, "identity-service", "round_robin")
    
    try:
        # This would make a request to one of the discovered instances
        # result = await client.get("/health")
        # print(f"Health check result: {result}")
        pass
    except Exception as e:
        print(f"Request failed: {e}")
    
    # Get service stats
    stats = service_registry.get_service_stats("identity-service")
    print(f"Service stats: {stats}")
    
    # Cleanup
    await registrar1.deregister()
    await registrar2.deregister()
    service_registry.stop_background_tasks()

if __name__ == "__main__":
    asyncio.run(example_usage())