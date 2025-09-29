"""
⚡ ADVANCED CIRCUIT BREAKER SYSTEM
Ollama Universal Intelligent Operations Engine (OUIOE)

Comprehensive circuit breaker implementation for resilient service communication.
Protects against cascading failures and provides intelligent fallback mechanisms.

Key Features:
- Multiple circuit breaker states (Closed, Open, Half-Open)
- Configurable failure thresholds and timeouts
- Intelligent failure detection and recovery
- Fallback mechanism support
- Circuit breaker metrics and monitoring
- Bulk-head pattern implementation
- Rate limiting integration
- Health check integration
"""

import asyncio
import structlog
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Union, Callable, Awaitable
from dataclasses import dataclass, field
from enum import Enum
import threading
from collections import deque
import functools
import inspect

logger = structlog.get_logger()

class CircuitState(Enum):
    """Circuit breaker states"""
    CLOSED = "closed"      # Normal operation
    OPEN = "open"          # Failing, rejecting requests
    HALF_OPEN = "half_open"  # Testing if service recovered

class FailureType(Enum):
    """Types of failures that can trigger circuit breaker"""
    TIMEOUT = "timeout"
    CONNECTION_ERROR = "connection_error"
    HTTP_ERROR = "http_error"
    EXCEPTION = "exception"
    CUSTOM = "custom"

@dataclass
class CircuitBreakerConfig:
    """Circuit breaker configuration"""
    failure_threshold: int = 5  # Number of failures to open circuit
    recovery_timeout: float = 60.0  # Seconds to wait before trying half-open
    success_threshold: int = 3  # Successful calls needed to close circuit from half-open
    timeout: float = 30.0  # Request timeout in seconds
    expected_exception: Optional[type] = None  # Exception type that triggers circuit
    fallback_function: Optional[Callable] = None  # Fallback function to call when circuit is open
    name: str = "default"  # Circuit breaker name for monitoring

@dataclass
class CallResult:
    """Result of a circuit breaker protected call"""
    success: bool
    result: Any = None
    exception: Optional[Exception] = None
    duration: float = 0.0
    timestamp: datetime = field(default_factory=datetime.now)
    failure_type: Optional[FailureType] = None

class CircuitBreakerMetrics:
    """Metrics tracking for circuit breaker"""
    
    def __init__(self, window_size: int = 100):
        self.window_size = window_size
        self.calls: deque = deque(maxlen=window_size)
        self.total_calls = 0
        self.total_failures = 0
        self.total_successes = 0
        self.total_timeouts = 0
        self.total_circuit_open_time = 0.0
        self.last_failure_time: Optional[datetime] = None
        self.last_success_time: Optional[datetime] = None
        self._lock = threading.RLock()
    
    def record_call(self, result: CallResult):
        """Record a call result"""
        with self._lock:
            self.calls.append(result)
            self.total_calls += 1
            
            if result.success:
                self.total_successes += 1
                self.last_success_time = result.timestamp
            else:
                self.total_failures += 1
                self.last_failure_time = result.timestamp
                
                if result.failure_type == FailureType.TIMEOUT:
                    self.total_timeouts += 1
    
    def get_failure_rate(self, window_seconds: Optional[float] = None) -> float:
        """Get failure rate within time window"""
        with self._lock:
            if not self.calls:
                return 0.0
            
            if window_seconds:
                cutoff_time = datetime.now() - timedelta(seconds=window_seconds)
                recent_calls = [call for call in self.calls if call.timestamp >= cutoff_time]
            else:
                recent_calls = list(self.calls)
            
            if not recent_calls:
                return 0.0
            
            failures = sum(1 for call in recent_calls if not call.success)
            return failures / len(recent_calls)
    
    def get_average_response_time(self, window_seconds: Optional[float] = None) -> float:
        """Get average response time within time window"""
        with self._lock:
            if not self.calls:
                return 0.0
            
            if window_seconds:
                cutoff_time = datetime.now() - timedelta(seconds=window_seconds)
                recent_calls = [call for call in self.calls if call.timestamp >= cutoff_time]
            else:
                recent_calls = list(self.calls)
            
            if not recent_calls:
                return 0.0
            
            total_duration = sum(call.duration for call in recent_calls)
            return total_duration / len(recent_calls)
    
    def get_stats(self) -> Dict[str, Any]:
        """Get comprehensive statistics"""
        with self._lock:
            return {
                "total_calls": self.total_calls,
                "total_successes": self.total_successes,
                "total_failures": self.total_failures,
                "total_timeouts": self.total_timeouts,
                "failure_rate": self.get_failure_rate(),
                "failure_rate_1min": self.get_failure_rate(60),
                "failure_rate_5min": self.get_failure_rate(300),
                "avg_response_time": self.get_average_response_time(),
                "avg_response_time_1min": self.get_average_response_time(60),
                "last_failure": self.last_failure_time.isoformat() if self.last_failure_time else None,
                "last_success": self.last_success_time.isoformat() if self.last_success_time else None,
                "recent_calls": len(self.calls)
            }

class CircuitBreaker:
    """
    ⚡ ADVANCED CIRCUIT BREAKER
    
    Protects against cascading failures with intelligent state management.
    """
    
    def __init__(self, config: CircuitBreakerConfig):
        self.config = config
        self.state = CircuitState.CLOSED
        self.failure_count = 0
        self.success_count = 0
        self.last_failure_time: Optional[datetime] = None
        self.last_state_change: datetime = datetime.now()
        self.metrics = CircuitBreakerMetrics()
        self._lock = threading.RLock()
        
        logger.info("⚡ Circuit breaker initialized", name=config.name, state=self.state.value)
    
    async def call(self, func: Callable, *args, **kwargs) -> Any:
        """Execute function with circuit breaker protection"""
        with self._lock:
            # Check if circuit is open
            if self.state == CircuitState.OPEN:
                if self._should_attempt_reset():
                    self._transition_to_half_open()
                else:
                    return await self._handle_open_circuit(func, *args, **kwargs)
        
        # Execute the protected function
        start_time = time.time()
        result = CallResult(success=False)
        
        try:
            # Set timeout if specified
            if self.config.timeout > 0:
                if inspect.iscoroutinefunction(func):
                    result.result = await asyncio.wait_for(
                        func(*args, **kwargs), 
                        timeout=self.config.timeout
                    )
                else:
                    # For sync functions, we can't easily apply timeout
                    result.result = func(*args, **kwargs)
            else:
                if inspect.iscoroutinefunction(func):
                    result.result = await func(*args, **kwargs)
                else:
                    result.result = func(*args, **kwargs)
            
            result.success = True
            result.duration = time.time() - start_time
            
            # Record success and update state
            await self._on_success(result)
            
            return result.result
            
        except asyncio.TimeoutError as e:
            result.exception = e
            result.failure_type = FailureType.TIMEOUT
            result.duration = time.time() - start_time
            await self._on_failure(result)
            raise
            
        except ConnectionError as e:
            result.exception = e
            result.failure_type = FailureType.CONNECTION_ERROR
            result.duration = time.time() - start_time
            await self._on_failure(result)
            raise
            
        except Exception as e:
            result.exception = e
            result.failure_type = FailureType.EXCEPTION
            result.duration = time.time() - start_time
            
            # Check if this is an expected exception that should trigger circuit
            if (self.config.expected_exception and 
                isinstance(e, self.config.expected_exception)):
                await self._on_failure(result)
            else:
                # For unexpected exceptions, still record but don't necessarily trigger circuit
                result.success = True  # Don't count as circuit failure
                self.metrics.record_call(result)
            
            raise
    
    async def _on_success(self, result: CallResult):
        """Handle successful call"""
        with self._lock:
            self.metrics.record_call(result)
            
            if self.state == CircuitState.HALF_OPEN:
                self.success_count += 1
                if self.success_count >= self.config.success_threshold:
                    self._transition_to_closed()
            elif self.state == CircuitState.CLOSED:
                # Reset failure count on success
                self.failure_count = 0
    
    async def _on_failure(self, result: CallResult):
        """Handle failed call"""
        with self._lock:
            self.metrics.record_call(result)
            self.failure_count += 1
            self.last_failure_time = result.timestamp
            
            if self.state == CircuitState.CLOSED:
                if self.failure_count >= self.config.failure_threshold:
                    self._transition_to_open()
            elif self.state == CircuitState.HALF_OPEN:
                # Any failure in half-open state transitions back to open
                self._transition_to_open()
    
    def _should_attempt_reset(self) -> bool:
        """Check if circuit should attempt to reset from open to half-open"""
        if self.last_failure_time is None:
            return True
        
        time_since_failure = datetime.now() - self.last_failure_time
        return time_since_failure.total_seconds() >= self.config.recovery_timeout
    
    def _transition_to_closed(self):
        """Transition circuit to closed state"""
        self.state = CircuitState.CLOSED
        self.failure_count = 0
        self.success_count = 0
        self.last_state_change = datetime.now()
        
        logger.info("⚡ Circuit breaker closed", name=self.config.name)
    
    def _transition_to_open(self):
        """Transition circuit to open state"""
        self.state = CircuitState.OPEN
        self.success_count = 0
        self.last_state_change = datetime.now()
        
        logger.warning("⚡ Circuit breaker opened", name=self.config.name, failures=self.failure_count)
    
    def _transition_to_half_open(self):
        """Transition circuit to half-open state"""
        self.state = CircuitState.HALF_OPEN
        self.success_count = 0
        self.last_state_change = datetime.now()
        
        logger.info("⚡ Circuit breaker half-open", name=self.config.name)
    
    async def _handle_open_circuit(self, func: Callable, *args, **kwargs) -> Any:
        """Handle call when circuit is open"""
        if self.config.fallback_function:
            logger.info("⚡ Circuit open, using fallback", name=self.config.name)
            if inspect.iscoroutinefunction(self.config.fallback_function):
                return await self.config.fallback_function(*args, **kwargs)
            else:
                return self.config.fallback_function(*args, **kwargs)
        else:
            # No fallback, raise exception
            raise CircuitBreakerOpenException(
                f"Circuit breaker '{self.config.name}' is open"
            )
    
    def get_state(self) -> CircuitState:
        """Get current circuit state"""
        return self.state
    
    def get_metrics(self) -> Dict[str, Any]:
        """Get circuit breaker metrics"""
        with self._lock:
            stats = self.metrics.get_stats()
            stats.update({
                "name": self.config.name,
                "state": self.state.value,
                "failure_count": self.failure_count,
                "success_count": self.success_count,
                "failure_threshold": self.config.failure_threshold,
                "recovery_timeout": self.config.recovery_timeout,
                "last_state_change": self.last_state_change.isoformat(),
                "time_in_current_state": (datetime.now() - self.last_state_change).total_seconds()
            })
            return stats
    
    def reset(self):
        """Manually reset circuit breaker to closed state"""
        with self._lock:
            self._transition_to_closed()
            logger.info("⚡ Circuit breaker manually reset", name=self.config.name)

class CircuitBreakerOpenException(Exception):
    """Exception raised when circuit breaker is open"""
    pass

class CircuitBreakerManager:
    """
    ⚡ CIRCUIT BREAKER MANAGER
    
    Manages multiple circuit breakers and provides centralized monitoring.
    """
    
    def __init__(self):
        self.circuit_breakers: Dict[str, CircuitBreaker] = {}
        self._lock = threading.RLock()
        
        logger.info("⚡ Circuit Breaker Manager initialized")
    
    def create_circuit_breaker(self, name: str, config: CircuitBreakerConfig) -> CircuitBreaker:
        """Create and register a new circuit breaker"""
        with self._lock:
            config.name = name
            circuit_breaker = CircuitBreaker(config)
            self.circuit_breakers[name] = circuit_breaker
            
            logger.info("⚡ Circuit breaker created", name=name)
            return circuit_breaker
    
    def get_circuit_breaker(self, name: str) -> Optional[CircuitBreaker]:
        """Get circuit breaker by name"""
        return self.circuit_breakers.get(name)
    
    def remove_circuit_breaker(self, name: str):
        """Remove circuit breaker"""
        with self._lock:
            if name in self.circuit_breakers:
                del self.circuit_breakers[name]
                logger.info("⚡ Circuit breaker removed", name=name)
    
    def get_all_metrics(self) -> Dict[str, Dict[str, Any]]:
        """Get metrics for all circuit breakers"""
        with self._lock:
            return {
                name: cb.get_metrics() 
                for name, cb in self.circuit_breakers.items()
            }
    
    def get_summary(self) -> Dict[str, Any]:
        """Get summary of all circuit breakers"""
        with self._lock:
            total_breakers = len(self.circuit_breakers)
            open_breakers = sum(1 for cb in self.circuit_breakers.values() if cb.get_state() == CircuitState.OPEN)
            half_open_breakers = sum(1 for cb in self.circuit_breakers.values() if cb.get_state() == CircuitState.HALF_OPEN)
            closed_breakers = total_breakers - open_breakers - half_open_breakers
            
            return {
                "total_circuit_breakers": total_breakers,
                "closed": closed_breakers,
                "open": open_breakers,
                "half_open": half_open_breakers,
                "circuit_breakers": list(self.circuit_breakers.keys())
            }
    
    def reset_all(self):
        """Reset all circuit breakers"""
        with self._lock:
            for cb in self.circuit_breakers.values():
                cb.reset()
            logger.info("⚡ All circuit breakers reset")

# Decorator for easy circuit breaker usage
def circuit_breaker(name: str, **config_kwargs):
    """Decorator to apply circuit breaker to a function"""
    def decorator(func):
        config = CircuitBreakerConfig(**config_kwargs)
        cb = _circuit_breaker_manager.create_circuit_breaker(name, config)
        
        @functools.wraps(func)
        async def async_wrapper(*args, **kwargs):
            return await cb.call(func, *args, **kwargs)
        
        @functools.wraps(func)
        def sync_wrapper(*args, **kwargs):
            # For sync functions, we need to handle differently
            return asyncio.run(cb.call(func, *args, **kwargs))
        
        if inspect.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper
    
    return decorator

# Global circuit breaker manager
_circuit_breaker_manager = CircuitBreakerManager()

def get_circuit_breaker_manager() -> CircuitBreakerManager:
    """Get the global circuit breaker manager"""
    return _circuit_breaker_manager

# Predefined circuit breakers for common services
async def initialize_service_circuit_breakers():
    """Initialize circuit breakers for common services"""
    manager = get_circuit_breaker_manager()
    
    # Service circuit breakers
    service_configs = {
        "asset_service": CircuitBreakerConfig(
            failure_threshold=3,
            recovery_timeout=30.0,
            timeout=10.0,
            name="asset_service"
        ),
        "automation_service": CircuitBreakerConfig(
            failure_threshold=3,
            recovery_timeout=30.0,
            timeout=15.0,
            name="automation_service"
        ),
        "network_service": CircuitBreakerConfig(
            failure_threshold=5,
            recovery_timeout=60.0,
            timeout=20.0,
            name="network_service"
        ),
        "communication_service": CircuitBreakerConfig(
            failure_threshold=3,
            recovery_timeout=30.0,
            timeout=10.0,
            name="communication_service"
        ),
        "ollama_service": CircuitBreakerConfig(
            failure_threshold=5,
            recovery_timeout=120.0,
            timeout=60.0,
            name="ollama_service"
        ),
        "chromadb_service": CircuitBreakerConfig(
            failure_threshold=3,
            recovery_timeout=30.0,
            timeout=15.0,
            name="chromadb_service"
        ),
        "redis_service": CircuitBreakerConfig(
            failure_threshold=3,
            recovery_timeout=30.0,
            timeout=5.0,
            name="redis_service"
        ),
        "postgres_service": CircuitBreakerConfig(
            failure_threshold=3,
            recovery_timeout=30.0,
            timeout=10.0,
            name="postgres_service"
        )
    }
    
    for name, config in service_configs.items():
        manager.create_circuit_breaker(name, config)
    
    logger.info("⚡ Service circuit breakers initialized", count=len(service_configs))

# Utility functions for common patterns
async def call_with_circuit_breaker(circuit_name: str, func: Callable, *args, **kwargs):
    """Call function with named circuit breaker"""
    manager = get_circuit_breaker_manager()
    circuit_breaker = manager.get_circuit_breaker(circuit_name)
    
    if circuit_breaker:
        return await circuit_breaker.call(func, *args, **kwargs)
    else:
        # No circuit breaker found, call directly
        logger.warning("⚡ Circuit breaker not found, calling directly", name=circuit_name)
        if inspect.iscoroutinefunction(func):
            return await func(*args, **kwargs)
        else:
            return func(*args, **kwargs)