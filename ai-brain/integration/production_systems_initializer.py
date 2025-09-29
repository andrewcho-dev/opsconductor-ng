"""
🚀 PRODUCTION SYSTEMS INITIALIZER
Ollama Universal Intelligent Operations Engine (OUIOE)

Comprehensive initialization system for all production-ready components.
Ensures proper startup sequence and integration of all monitoring, security,
and resilience systems.

Key Features:
- Ordered initialization of production systems
- Health checks and validation
- Graceful error handling and fallbacks
- System readiness verification
- Performance optimization
- Production metrics collection
"""

import asyncio
import structlog
from datetime import datetime
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass
from enum import Enum

logger = structlog.get_logger()

class InitializationStatus(Enum):
    """Initialization status"""
    PENDING = "pending"
    INITIALIZING = "initializing"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"

@dataclass
class SystemInitResult:
    """Result of system initialization"""
    system_name: str
    status: InitializationStatus
    duration_ms: float
    error: Optional[str] = None
    details: Dict[str, Any] = None

class ProductionSystemsInitializer:
    """
    🚀 PRODUCTION SYSTEMS INITIALIZER
    
    Manages the initialization of all production-ready systems in the correct order.
    """
    
    def __init__(self):
        self.initialization_results: Dict[str, SystemInitResult] = {}
        self.initialization_order = [
            "metrics_collection",
            "distributed_tracing", 
            "circuit_breakers",
            "rate_limiting",
            "alerting_system",
            "dashboard_system",
            "production_validator"
        ]
        
        logger.info("🚀 Production Systems Initializer created")
    
    async def initialize_all_systems(self) -> Dict[str, SystemInitResult]:
        """Initialize all production systems in the correct order"""
        logger.info("🚀 Starting production systems initialization")
        start_time = datetime.now()
        
        for system_name in self.initialization_order:
            result = await self._initialize_system(system_name)
            self.initialization_results[system_name] = result
            
            if result.status == InitializationStatus.FAILED:
                logger.error(f"❌ Critical system failed to initialize: {system_name}")
                # Continue with other systems but log the failure
        
        total_duration = (datetime.now() - start_time).total_seconds() * 1000
        
        # Generate summary
        successful = sum(1 for r in self.initialization_results.values() if r.status == InitializationStatus.COMPLETED)
        failed = sum(1 for r in self.initialization_results.values() if r.status == InitializationStatus.FAILED)
        
        logger.info("🚀 Production systems initialization complete",
                   total_duration=total_duration,
                   successful=successful,
                   failed=failed,
                   total=len(self.initialization_results))
        
        return self.initialization_results
    
    async def _initialize_system(self, system_name: str) -> SystemInitResult:
        """Initialize a specific system"""
        logger.info(f"🔧 Initializing {system_name}")
        start_time = datetime.now()
        
        try:
            if system_name == "metrics_collection":
                success, details = await self._initialize_metrics_collection()
            elif system_name == "distributed_tracing":
                success, details = await self._initialize_distributed_tracing()
            elif system_name == "circuit_breakers":
                success, details = await self._initialize_circuit_breakers()
            elif system_name == "rate_limiting":
                success, details = await self._initialize_rate_limiting()
            elif system_name == "alerting_system":
                success, details = await self._initialize_alerting_system()
            elif system_name == "dashboard_system":
                success, details = await self._initialize_dashboard_system()
            elif system_name == "production_validator":
                success, details = await self._initialize_production_validator()
            else:
                success, details = False, {"error": f"Unknown system: {system_name}"}
            
            duration = (datetime.now() - start_time).total_seconds() * 1000
            status = InitializationStatus.COMPLETED if success else InitializationStatus.FAILED
            
            result = SystemInitResult(
                system_name=system_name,
                status=status,
                duration_ms=duration,
                error=details.get("error") if not success else None,
                details=details
            )
            
            if success:
                logger.info(f"✅ {system_name} initialized successfully", duration=duration)
            else:
                logger.error(f"❌ {system_name} initialization failed", error=details.get("error"))
            
            return result
            
        except Exception as e:
            duration = (datetime.now() - start_time).total_seconds() * 1000
            logger.error(f"❌ {system_name} initialization exception", error=str(e), exc_info=True)
            
            return SystemInitResult(
                system_name=system_name,
                status=InitializationStatus.FAILED,
                duration_ms=duration,
                error=str(e)
            )
    
    async def _initialize_metrics_collection(self) -> Tuple[bool, Dict[str, Any]]:
        """Initialize metrics collection system"""
        try:
            from monitoring.metrics_collector import initialize_metrics_system
            success = await initialize_metrics_system()
            
            if success:
                from monitoring.metrics_collector import get_metrics_collector
                collector = await get_metrics_collector()
                summary = await collector.get_metrics_summary()
                
                return True, {
                    "total_metrics": summary.get("total_metrics", 0),
                    "is_collecting": summary.get("is_collecting", False),
                    "collection_interval": summary.get("collection_interval", 0)
                }
            else:
                return False, {"error": "Failed to initialize metrics system"}
                
        except Exception as e:
            return False, {"error": str(e)}
    
    async def _initialize_distributed_tracing(self) -> Tuple[bool, Dict[str, Any]]:
        """Initialize distributed tracing system"""
        try:
            from monitoring.distributed_tracing import initialize_tracing_system
            success = await initialize_tracing_system("ai-brain")
            
            if success:
                from monitoring.distributed_tracing import get_tracing_system
                tracer = await get_tracing_system()
                metrics = await tracer.get_metrics()
                
                return True, {
                    "service_name": metrics.get("service_name"),
                    "sampling_rate": metrics.get("sampling_rate"),
                    "total_spans": metrics.get("total_spans", 0)
                }
            else:
                return False, {"error": "Failed to initialize tracing system"}
                
        except Exception as e:
            return False, {"error": str(e)}
    
    async def _initialize_circuit_breakers(self) -> Tuple[bool, Dict[str, Any]]:
        """Initialize circuit breaker system"""
        try:
            from resilience.circuit_breaker import initialize_service_circuit_breakers, get_circuit_breaker_manager
            await initialize_service_circuit_breakers()
            
            manager = get_circuit_breaker_manager()
            summary = manager.get_summary()
            
            return True, {
                "total_circuit_breakers": summary.get("total_circuit_breakers", 0),
                "closed": summary.get("closed", 0),
                "open": summary.get("open", 0),
                "half_open": summary.get("half_open", 0)
            }
            
        except Exception as e:
            return False, {"error": str(e)}
    
    async def _initialize_rate_limiting(self) -> Tuple[bool, Dict[str, Any]]:
        """Initialize rate limiting system"""
        try:
            from security.rate_limiter import initialize_rate_limiting_system
            success = await initialize_rate_limiting_system()
            
            if success:
                from security.rate_limiter import get_rate_limit_manager
                manager = await get_rate_limit_manager()
                metrics = await manager.get_metrics()
                
                return True, {
                    "total_configs": metrics.get("total_configs", 0),
                    "active_limiters": metrics.get("active_limiters", 0)
                }
            else:
                return False, {"error": "Failed to initialize rate limiting system"}
                
        except Exception as e:
            return False, {"error": str(e)}
    
    async def _initialize_alerting_system(self) -> Tuple[bool, Dict[str, Any]]:
        """Initialize alerting system"""
        try:
            from monitoring.alerting_system import initialize_alerting_system
            success = await initialize_alerting_system()
            
            if success:
                from monitoring.alerting_system import get_alerting_system
                alerting = await get_alerting_system()
                summary = await alerting.get_alert_summary()
                
                return True, {
                    "total_rules": summary.get("total_rules", 0),
                    "enabled_rules": summary.get("enabled_rules", 0),
                    "active_alerts": summary.get("active_alerts", 0),
                    "is_evaluating": summary.get("is_evaluating", False)
                }
            else:
                return False, {"error": "Failed to initialize alerting system"}
                
        except Exception as e:
            return False, {"error": str(e)}
    
    async def _initialize_dashboard_system(self) -> Tuple[bool, Dict[str, Any]]:
        """Initialize dashboard system"""
        try:
            from monitoring.dashboard_system import initialize_dashboard_system
            success = await initialize_dashboard_system()
            
            if success:
                from monitoring.dashboard_system import get_dashboard_system
                dashboard_sys = await get_dashboard_system()
                summary = await dashboard_sys.get_system_summary()
                
                return True, {
                    "total_dashboards": summary.get("total_dashboards", 0),
                    "dashboard_categories": summary.get("dashboard_categories", {}),
                    "system_status": summary.get("system_status", "unknown")
                }
            else:
                return False, {"error": "Failed to initialize dashboard system"}
                
        except Exception as e:
            return False, {"error": str(e)}
    
    async def _initialize_production_validator(self) -> Tuple[bool, Dict[str, Any]]:
        """Initialize production readiness validator"""
        try:
            # The validator doesn't need explicit initialization, just verify it works
            from integration.production_readiness_validator import ProductionReadinessValidator
            
            # Create a mock system integrator for testing
            class MockSystemIntegrator:
                def __init__(self):
                    self.capabilities = type('obj', (object,), {
                        'streaming_infrastructure': True,
                        'thinking_visualization': True,
                        'decision_engine': True,
                        'workflow_orchestration': True,
                        'deductive_analysis': True,
                        'conversational_intelligence': True,
                        'service_integrations': {'asset': True, 'automation': True, 'network': True, 'communication': True, 'prefect': True},
                        'advanced_features': {'advanced_thinking': True, 'complex_workflows': True, 'sophisticated_analysis': True, 'real_time_optimization': True}
                    })
            
            mock_integrator = MockSystemIntegrator()
            validator = ProductionReadinessValidator(mock_integrator)
            
            # Run a quick validation to test the system
            result = await validator.validate_production_readiness()
            
            return True, {
                "readiness_level": result.readiness_level.value,
                "overall_score": result.overall_score,
                "security_score": result.security.security_score,
                "performance_score": result.performance.performance_score,
                "error_handling_score": result.error_handling.error_handling_score,
                "monitoring_score": result.monitoring.monitoring_score,
                "deployment_ready": result.deployment_ready
            }
            
        except Exception as e:
            return False, {"error": str(e)}
    
    async def get_initialization_summary(self) -> Dict[str, Any]:
        """Get comprehensive initialization summary"""
        if not self.initialization_results:
            return {"status": "not_initialized"}
        
        successful_systems = [r for r in self.initialization_results.values() if r.status == InitializationStatus.COMPLETED]
        failed_systems = [r for r in self.initialization_results.values() if r.status == InitializationStatus.FAILED]
        
        total_duration = sum(r.duration_ms for r in self.initialization_results.values())
        
        return {
            "status": "completed",
            "total_systems": len(self.initialization_results),
            "successful_systems": len(successful_systems),
            "failed_systems": len(failed_systems),
            "success_rate": len(successful_systems) / len(self.initialization_results) * 100,
            "total_duration_ms": total_duration,
            "systems": {
                r.system_name: {
                    "status": r.status.value,
                    "duration_ms": r.duration_ms,
                    "error": r.error,
                    "details": r.details
                } for r in self.initialization_results.values()
            },
            "production_ready": len(failed_systems) == 0,
            "timestamp": datetime.now().isoformat()
        }
    
    async def verify_system_health(self) -> Dict[str, Any]:
        """Verify health of all initialized systems"""
        health_checks = {}
        
        # Check metrics collection
        try:
            from monitoring.metrics_collector import get_metrics_collector
            collector = await get_metrics_collector()
            summary = await collector.get_metrics_summary()
            health_checks["metrics_collection"] = {
                "healthy": summary.get("is_collecting", False),
                "metrics_count": summary.get("total_metrics", 0)
            }
        except Exception as e:
            health_checks["metrics_collection"] = {"healthy": False, "error": str(e)}
        
        # Check alerting system
        try:
            from monitoring.alerting_system import get_alerting_system
            alerting = await get_alerting_system()
            summary = await alerting.get_alert_summary()
            health_checks["alerting_system"] = {
                "healthy": summary.get("is_evaluating", False),
                "active_alerts": summary.get("active_alerts", 0),
                "total_rules": summary.get("total_rules", 0)
            }
        except Exception as e:
            health_checks["alerting_system"] = {"healthy": False, "error": str(e)}
        
        # Check circuit breakers
        try:
            from resilience.circuit_breaker import get_circuit_breaker_manager
            cb_manager = get_circuit_breaker_manager()
            summary = cb_manager.get_summary()
            health_checks["circuit_breakers"] = {
                "healthy": summary.get("total_circuit_breakers", 0) > 0,
                "total_breakers": summary.get("total_circuit_breakers", 0),
                "open_breakers": summary.get("open", 0)
            }
        except Exception as e:
            health_checks["circuit_breakers"] = {"healthy": False, "error": str(e)}
        
        # Check rate limiting
        try:
            from security.rate_limiter import get_rate_limit_manager
            rate_manager = await get_rate_limit_manager()
            metrics = await rate_manager.get_metrics()
            health_checks["rate_limiting"] = {
                "healthy": metrics.get("total_configs", 0) > 0,
                "total_configs": metrics.get("total_configs", 0)
            }
        except Exception as e:
            health_checks["rate_limiting"] = {"healthy": False, "error": str(e)}
        
        # Check dashboard system
        try:
            from monitoring.dashboard_system import get_dashboard_system
            dashboard_sys = await get_dashboard_system()
            dashboards = await dashboard_sys.list_dashboards()
            health_checks["dashboard_system"] = {
                "healthy": len(dashboards) > 0,
                "total_dashboards": len(dashboards)
            }
        except Exception as e:
            health_checks["dashboard_system"] = {"healthy": False, "error": str(e)}
        
        # Check distributed tracing
        try:
            from monitoring.distributed_tracing import get_tracing_system
            tracer = await get_tracing_system()
            metrics = await tracer.get_metrics()
            health_checks["distributed_tracing"] = {
                "healthy": True,  # If we can get metrics, it's healthy
                "total_spans": metrics.get("total_spans", 0),
                "error_rate": metrics.get("error_rate", 0)
            }
        except Exception as e:
            health_checks["distributed_tracing"] = {"healthy": False, "error": str(e)}
        
        # Calculate overall health
        healthy_systems = sum(1 for check in health_checks.values() if check.get("healthy", False))
        total_systems = len(health_checks)
        overall_health = (healthy_systems / total_systems) * 100 if total_systems > 0 else 0
        
        return {
            "overall_health_percent": overall_health,
            "healthy_systems": healthy_systems,
            "total_systems": total_systems,
            "systems": health_checks,
            "timestamp": datetime.now().isoformat()
        }

# Global initializer instance
_production_initializer: Optional[ProductionSystemsInitializer] = None

async def get_production_initializer() -> ProductionSystemsInitializer:
    """Get the global production initializer instance"""
    global _production_initializer
    if _production_initializer is None:
        _production_initializer = ProductionSystemsInitializer()
    return _production_initializer

async def initialize_all_production_systems() -> Dict[str, SystemInitResult]:
    """Initialize all production systems"""
    initializer = await get_production_initializer()
    return await initializer.initialize_all_systems()

async def get_production_systems_health() -> Dict[str, Any]:
    """Get health status of all production systems"""
    initializer = await get_production_initializer()
    return await initializer.verify_system_health()