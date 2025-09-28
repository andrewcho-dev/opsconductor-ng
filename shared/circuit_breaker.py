#!/usr/bin/env python3
"""
Circuit Breaker Pattern Implementation
Provides fault tolerance and prevents cascading failures
"""

import asyncio
import time
import logging
from typing import Any, Callable, Optional, Dict
from enum import Enum
from dataclasses import dataclass
from functools import wraps

logger = logging.getLogger(__name__)

class CircuitState(Enum):
    CLOSED = "closed"      # Normal operation
    OPEN = "open"          # Circuit is open, calls fail fast
    HALF_OPEN = "half_open"  # Testing if service is back

@dataclass
class CircuitBreakerConfig:
    """Configuration for circuit breaker"""
    failure_threshold: int = 5          # Number of failures to open circuit
    recovery_timeout: float = 60.0      # Seconds to wait before trying half-open
    success_threshold: int = 3          # Successes needed to close from half-open
    timeout: float = 30.0               # Request timeout
    expected_exception: type = Exception # Exception type that counts as failure

class CircuitBreakerError(Exception):
    """Exception raised when circuit breaker is open"""
    pass

class CircuitBreaker:
    """Circuit breaker implementation"""
    
    def __init__(self, name: str, config: CircuitBreakerConfig = None):
        self.name = name
        self.config = config or CircuitBreakerConfig()
        
        # State tracking
        self.state = CircuitState.CLOSED
        self.failure_count = 0
        self.success_count = 0
        self.last_failure_time = 0
        self.last_success_time = 0
        
        # Metrics
        self.total_requests = 0
        self.total_failures = 0
        self.total_successes = 0
        self.total_timeouts = 0
        self.total_circuit_open_calls = 0
        
        logger.info(f"Circuit breaker '{name}' initialized")

    async def call(self, func: Callable, *args, **kwargs) -> Any:
        """Execute function with circuit breaker protection"""
        self.total_requests += 1
        
        # Check if circuit should be closed (recovery)
        if self.state == CircuitState.OPEN:
            if time.time() - self.last_failure_time >= self.config.recovery_timeout:
                logger.info(f"Circuit breaker '{self.name}' transitioning to HALF_OPEN")
                self.state = CircuitState.HALF_OPEN
                self.success_count = 0
            else:
                self.total_circuit_open_calls += 1
                raise CircuitBreakerError(f"Circuit breaker '{self.name}' is OPEN")
        
        try:
            # Execute the function with timeout
            if asyncio.iscoroutinefunction(func):
                result = await asyncio.wait_for(
                    func(*args, **kwargs), 
                    timeout=self.config.timeout
                )
            else:
                result = func(*args, **kwargs)
            
            # Success handling
            self._on_success()
            return result
            
        except asyncio.TimeoutError:
            self.total_timeouts += 1
            self._on_failure()
            raise
            
        except self.config.expected_exception as e:
            self._on_failure()
            raise
            
        except Exception as e:
            # Unexpected exceptions don't count as failures
            logger.warning(f"Unexpected exception in circuit breaker '{self.name}': {e}")
            raise

    def _on_success(self):
        """Handle successful call"""
        self.total_successes += 1
        self.last_success_time = time.time()
        
        if self.state == CircuitState.HALF_OPEN:
            self.success_count += 1
            if self.success_count >= self.config.success_threshold:
                logger.info(f"Circuit breaker '{self.name}' transitioning to CLOSED")
                self.state = CircuitState.CLOSED
                self.failure_count = 0
                self.success_count = 0
        elif self.state == CircuitState.CLOSED:
            # Reset failure count on success
            self.failure_count = 0

    def _on_failure(self):
        """Handle failed call"""
        self.total_failures += 1
        self.last_failure_time = time.time()
        self.failure_count += 1
        
        if self.state == CircuitState.CLOSED:
            if self.failure_count >= self.config.failure_threshold:
                logger.warning(f"Circuit breaker '{self.name}' transitioning to OPEN")
                self.state = CircuitState.OPEN
        elif self.state == CircuitState.HALF_OPEN:
            logger.warning(f"Circuit breaker '{self.name}' transitioning back to OPEN")
            self.state = CircuitState.OPEN
            self.success_count = 0

    def get_stats(self) -> Dict[str, Any]:
        """Get circuit breaker statistics"""
        return {
            "name": self.name,
            "state": self.state.value,
            "failure_count": self.failure_count,
            "success_count": self.success_count,
            "total_requests": self.total_requests,
            "total_failures": self.total_failures,
            "total_successes": self.total_successes,
            "total_timeouts": self.total_timeouts,
            "total_circuit_open_calls": self.total_circuit_open_calls,
            "failure_rate": self.total_failures / max(self.total_requests, 1),
            "last_failure_time": self.last_failure_time,
            "last_success_time": self.last_success_time,
            "config": {
                "failure_threshold": self.config.failure_threshold,
                "recovery_timeout": self.config.recovery_timeout,
                "success_threshold": self.config.success_threshold,
                "timeout": self.config.timeout
            }
        }

    def reset(self):
        """Reset circuit breaker to initial state"""
        logger.info(f"Resetting circuit breaker '{self.name}'")
        self.state = CircuitState.CLOSED
        self.failure_count = 0
        self.success_count = 0

    def force_open(self):
        """Force circuit breaker to open state"""
        logger.warning(f"Forcing circuit breaker '{self.name}' to OPEN")
        self.state = CircuitState.OPEN
        self.last_failure_time = time.time()

    def force_close(self):
        """Force circuit breaker to closed state"""
        logger.info(f"Forcing circuit breaker '{self.name}' to CLOSED")
        self.state = CircuitState.CLOSED
        self.failure_count = 0
        self.success_count = 0

class CircuitBreakerManager:
    """Manages multiple circuit breakers"""
    
    def __init__(self):
        self.breakers: Dict[str, CircuitBreaker] = {}

    def get_breaker(self, name: str, config: CircuitBreakerConfig = None) -> CircuitBreaker:
        """Get or create a circuit breaker"""
        if name not in self.breakers:
            self.breakers[name] = CircuitBreaker(name, config)
        return self.breakers[name]

    def get_all_stats(self) -> Dict[str, Dict[str, Any]]:
        """Get statistics for all circuit breakers"""
        return {name: breaker.get_stats() for name, breaker in self.breakers.items()}

    def reset_all(self):
        """Reset all circuit breakers"""
        for breaker in self.breakers.values():
            breaker.reset()

    def get_unhealthy_breakers(self) -> List[str]:
        """Get list of circuit breakers that are open"""
        return [name for name, breaker in self.breakers.items() 
                if breaker.state == CircuitState.OPEN]

# Global circuit breaker manager
circuit_breaker_manager = CircuitBreakerManager()

def circuit_breaker(name: str, config: CircuitBreakerConfig = None):
    """Decorator for circuit breaker protection"""
    def decorator(func):
        breaker = circuit_breaker_manager.get_breaker(name, config)
        
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            return await breaker.call(func, *args, **kwargs)
        
        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            return asyncio.run(breaker.call(func, *args, **kwargs))
        
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper
    
    return decorator

# Enhanced service client with circuit breaker
class ResilientServiceClient:
    """HTTP client with circuit breaker protection"""
    
    def __init__(self, service_name: str, base_url: str, config: CircuitBreakerConfig = None):
        self.service_name = service_name
        self.base_url = base_url.rstrip('/')
        self.breaker = circuit_breaker_manager.get_breaker(f"{service_name}-client", config)

    async def get(self, path: str, **kwargs) -> Any:
        """GET request with circuit breaker protection"""
        return await self._request("GET", path, **kwargs)

    async def post(self, path: str, **kwargs) -> Any:
        """POST request with circuit breaker protection"""
        return await self._request("POST", path, **kwargs)

    async def put(self, path: str, **kwargs) -> Any:
        """PUT request with circuit breaker protection"""
        return await self._request("PUT", path, **kwargs)

    async def delete(self, path: str, **kwargs) -> Any:
        """DELETE request with circuit breaker protection"""
        return await self._request("DELETE", path, **kwargs)

    async def _request(self, method: str, path: str, **kwargs) -> Any:
        """Make HTTP request with circuit breaker protection"""
        import aiohttp
        
        async def make_request():
            url = f"{self.base_url}{path}"
            async with aiohttp.ClientSession() as session:
                async with session.request(method, url, **kwargs) as response:
                    if response.status >= 500:
                        raise aiohttp.ClientResponseError(
                            request_info=response.request_info,
                            history=response.history,
                            status=response.status
                        )
                    return await response.json() if response.content_type == 'application/json' else await response.text()
        
        return await self.breaker.call(make_request)

    def get_stats(self) -> Dict[str, Any]:
        """Get client statistics"""
        return self.breaker.get_stats()

# Example usage and testing
async def example_usage():
    """Example of how to use circuit breakers"""
    
    # Using decorator
    @circuit_breaker("example-service", CircuitBreakerConfig(failure_threshold=3))
    async def unreliable_service():
        import random
        if random.random() < 0.7:  # 70% failure rate
            raise Exception("Service failed")
        return "Success"
    
    # Using client - use environment variable for host IP
    host_ip = os.getenv('HOST_IP', '127.0.0.1')
    client = ResilientServiceClient(
        "identity-service", 
        f"http://{host_ip}:3001",
        CircuitBreakerConfig(failure_threshold=5, recovery_timeout=30)
    )
    
    # Test the service
    for i in range(10):
        try:
            result = await unreliable_service()
            print(f"Call {i+1}: {result}")
        except (Exception, CircuitBreakerError) as e:
            print(f"Call {i+1}: Failed - {e}")
        
        await asyncio.sleep(1)
    
    # Print statistics
    print("\nCircuit Breaker Stats:")
    for name, stats in circuit_breaker_manager.get_all_stats().items():
        print(f"{name}: {stats}")

if __name__ == "__main__":
    asyncio.run(example_usage())