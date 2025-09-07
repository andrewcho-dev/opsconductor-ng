"""
Shared health check utilities for all services
"""

from datetime import datetime
from typing import Dict, Any, List, Optional
from .database import check_database_health, get_database_metrics
from .models import HealthResponse, HealthCheck

def create_standard_health_response(
    service_name: str, 
    version: str = "1.0.0",
    additional_checks: Optional[List[HealthCheck]] = None
) -> HealthResponse:
    """
    Create a standard health response with database check
    
    Args:
        service_name: Name of the service
        version: Service version
        additional_checks: Additional health checks to include
        
    Returns:
        HealthResponse with database and optional additional checks
    """
    db_health = check_database_health()
    
    # Standard database health check
    checks = [
        HealthCheck(
            name="database",
            status=db_health["status"],
            message=db_health.get("message", "Database connection check"),
            duration_ms=db_health.get("response_time_ms")
        )
    ]
    
    # Add any additional checks
    if additional_checks:
        checks.extend(additional_checks)
    
    # Determine overall status
    overall_status = "healthy"
    if any(check.status != "healthy" for check in checks):
        overall_status = "unhealthy"
    
    return HealthResponse(
        status=overall_status,
        service=service_name,
        version=version,
        timestamp=datetime.utcnow().isoformat(),
        checks=checks
    )

def create_database_metrics_response(service_name: str) -> Dict[str, Any]:
    """
    Create a standard database metrics response
    
    Args:
        service_name: Name of the service
        
    Returns:
        Dict containing database metrics
    """
    metrics = get_database_metrics()
    return {
        "service": service_name,
        "timestamp": datetime.utcnow().isoformat(),
        "database": metrics
    }

def create_simple_health_response(service_name: str, version: str = "1.0.0") -> Dict[str, str]:
    """
    Create a simple health response without detailed checks
    
    Args:
        service_name: Name of the service
        version: Service version
        
    Returns:
        Simple health status dict
    """
    return {
        "status": "healthy",
        "service": service_name,
        "version": version
    }

def check_worker_health(worker_status: Dict[str, Any]) -> HealthCheck:
    """
    Create a health check for background workers
    
    Args:
        worker_status: Worker status information
        
    Returns:
        HealthCheck for the worker
    """
    is_running = worker_status.get("running", False)
    last_activity = worker_status.get("last_activity")
    
    if is_running:
        status = "healthy"
        message = f"Worker active, last activity: {last_activity}"
    else:
        status = "unhealthy"
        message = "Worker not running"
    
    return HealthCheck(
        name="worker",
        status=status,
        message=message,
        duration_ms=None
    )

def check_external_service_health(
    service_name: str, 
    service_url: str, 
    timeout: int = 5
) -> HealthCheck:
    """
    Check health of an external service dependency
    
    Args:
        service_name: Name of the external service
        service_url: URL to check
        timeout: Request timeout in seconds
        
    Returns:
        HealthCheck for the external service
    """
    import requests
    from time import time
    
    start_time = time()
    
    try:
        response = requests.get(f"{service_url}/health", timeout=timeout)
        duration_ms = int((time() - start_time) * 1000)
        
        if response.status_code == 200:
            return HealthCheck(
                name=service_name,
                status="healthy",
                message=f"{service_name} is responding",
                duration_ms=duration_ms
            )
        else:
            return HealthCheck(
                name=service_name,
                status="unhealthy",
                message=f"{service_name} returned status {response.status_code}",
                duration_ms=duration_ms
            )
    
    except requests.RequestException as e:
        duration_ms = int((time() - start_time) * 1000)
        return HealthCheck(
            name=service_name,
            status="unhealthy",
            message=f"{service_name} connection failed: {str(e)}",
            duration_ms=duration_ms
        )