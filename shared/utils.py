#!/usr/bin/env python3
"""
Shared Utilities
Common utility functions for all services
"""

import os
import time
import asyncio
from typing import Dict, Any, Optional, List, Union
import httpx
from .logging import log_service_call, get_logger
from .errors import handle_service_communication_error

logger = get_logger(__name__)

class ServiceClient:
    """
    Standardized HTTP client for inter-service communication
    """
    
    def __init__(
        self,
        service_name: str,
        base_url: str,
        timeout: float = 10.0,
        retries: int = 3,
        retry_delay: float = 1.0
    ):
        self.service_name = service_name
        self.base_url = base_url.rstrip('/')
        self.timeout = timeout
        self.retries = retries
        self.retry_delay = retry_delay
        self.logger = get_logger(f"service_client.{service_name}")
    
    async def _make_request(
        self,
        method: str,
        endpoint: str,
        headers: Optional[Dict[str, str]] = None,
        json_data: Optional[Dict[str, Any]] = None,
        params: Optional[Dict[str, Any]] = None,
        **kwargs
    ) -> httpx.Response:
        """Make HTTP request with retry logic"""
        
        url = f"{self.base_url}{endpoint}"
        headers = headers or {}
        
        # Add standard headers
        headers.setdefault("Content-Type", "application/json")
        headers.setdefault("User-Agent", f"OpsConductor-ServiceClient/{self.service_name}")
        
        last_exception = None
        
        for attempt in range(self.retries + 1):
            try:
                start_time = time.time()
                
                async with httpx.AsyncClient(timeout=self.timeout) as client:
                    response = await client.request(
                        method=method,
                        url=url,
                        headers=headers,
                        json=json_data,
                        params=params,
                        **kwargs
                    )
                
                duration_ms = round((time.time() - start_time) * 1000, 2)
                
                # Log successful call
                log_service_call(
                    service_name=self.service_name,
                    endpoint=endpoint,
                    method=method,
                    status_code=response.status_code,
                    duration_ms=duration_ms
                )
                
                # Raise for HTTP errors
                response.raise_for_status()
                return response
                
            except Exception as e:
                last_exception = e
                duration_ms = round((time.time() - start_time) * 1000, 2) if 'start_time' in locals() else None
                
                # Log failed attempt
                log_service_call(
                    service_name=self.service_name,
                    endpoint=endpoint,
                    method=method,
                    duration_ms=duration_ms,
                    error=str(e)
                )
                
                # Don't retry on client errors (4xx)
                if isinstance(e, httpx.HTTPStatusError) and 400 <= e.response.status_code < 500:
                    break
                
                # Wait before retry (except on last attempt)
                if attempt < self.retries:
                    await asyncio.sleep(self.retry_delay * (2 ** attempt))  # Exponential backoff
        
        # All retries failed, raise standardized error
        raise handle_service_communication_error(last_exception, self.service_name, f"{method} {endpoint}")
    
    async def get(self, endpoint: str, **kwargs) -> httpx.Response:
        """Make GET request"""
        return await self._make_request("GET", endpoint, **kwargs)
    
    async def post(self, endpoint: str, json_data: Dict[str, Any] = None, **kwargs) -> httpx.Response:
        """Make POST request"""
        return await self._make_request("POST", endpoint, json_data=json_data, **kwargs)
    
    async def put(self, endpoint: str, json_data: Dict[str, Any] = None, **kwargs) -> httpx.Response:
        """Make PUT request"""
        return await self._make_request("PUT", endpoint, json_data=json_data, **kwargs)
    
    async def patch(self, endpoint: str, json_data: Dict[str, Any] = None, **kwargs) -> httpx.Response:
        """Make PATCH request"""
        return await self._make_request("PATCH", endpoint, json_data=json_data, **kwargs)
    
    async def delete(self, endpoint: str, **kwargs) -> httpx.Response:
        """Make DELETE request"""
        return await self._make_request("DELETE", endpoint, **kwargs)
    
    async def get_json(self, endpoint: str, **kwargs) -> Dict[str, Any]:
        """Make GET request and return JSON response"""
        response = await self.get(endpoint, **kwargs)
        return response.json()
    
    async def post_json(self, endpoint: str, json_data: Dict[str, Any] = None, **kwargs) -> Dict[str, Any]:
        """Make POST request and return JSON response"""
        response = await self.post(endpoint, json_data=json_data, **kwargs)
        return response.json()

# Service client factory
_service_clients: Dict[str, ServiceClient] = {}

def get_service_client(service_name: str, base_url: str = None) -> ServiceClient:
    """
    Get or create a service client instance
    """
    if service_name not in _service_clients:
        if not base_url:
            # Try to get URL from environment
            env_var = f"{service_name.upper().replace('-', '_')}_SERVICE_URL"
            base_url = os.getenv(env_var)
            
            if not base_url:
                raise ValueError(f"No base URL provided for {service_name} and {env_var} not set")
        
        _service_clients[service_name] = ServiceClient(service_name, base_url)
    
    return _service_clients[service_name]

# Convenience functions for common service calls
async def call_auth_service(endpoint: str, method: str = "GET", **kwargs) -> Dict[str, Any]:
    """Call auth service"""
    client = get_service_client("auth-service")
    response = await client._make_request(method, endpoint, **kwargs)
    return response.json()

async def call_user_service(endpoint: str, method: str = "GET", **kwargs) -> Dict[str, Any]:
    """Call user service"""
    client = get_service_client("user-service")
    response = await client._make_request(method, endpoint, **kwargs)
    return response.json()

async def validate_service_health(service_url: str, timeout: float = 5.0) -> Dict[str, Any]:
    """
    Check if a service is healthy
    """
    try:
        async with httpx.AsyncClient(timeout=timeout) as client:
            response = await client.get(f"{service_url}/health")
            
            if response.status_code == 200:
                return {
                    "healthy": True,
                    "status_code": response.status_code,
                    "response": response.json()
                }
            else:
                return {
                    "healthy": False,
                    "status_code": response.status_code,
                    "error": "Non-200 status code"
                }
                
    except Exception as e:
        return {
            "healthy": False,
            "error": str(e)
        }

def parse_database_url(database_url: str) -> Dict[str, str]:
    """
    Parse database URL into components
    """
    # Simple parser for postgresql://user:pass@host:port/dbname
    if not database_url.startswith("postgresql://"):
        raise ValueError("Only PostgreSQL URLs are supported")
    
    url = database_url[13:]  # Remove postgresql://
    
    # Split user:pass@host:port/dbname
    if "@" in url:
        auth, rest = url.split("@", 1)
        if ":" in auth:
            user, password = auth.split(":", 1)
        else:
            user, password = auth, ""
    else:
        user, password = "", ""
        rest = url
    
    if "/" in rest:
        host_port, dbname = rest.split("/", 1)
    else:
        host_port, dbname = rest, ""
    
    if ":" in host_port:
        host, port = host_port.split(":", 1)
    else:
        host, port = host_port, "5432"
    
    return {
        "host": host,
        "port": port,
        "user": user,
        "password": password,
        "dbname": dbname
    }

def format_duration(seconds: float) -> str:
    """
    Format duration in seconds to human-readable string
    """
    if seconds < 1:
        return f"{int(seconds * 1000)}ms"
    elif seconds < 60:
        return f"{seconds:.1f}s"
    elif seconds < 3600:
        minutes = int(seconds // 60)
        remaining_seconds = seconds % 60
        return f"{minutes}m {remaining_seconds:.1f}s"
    else:
        hours = int(seconds // 3600)
        remaining_minutes = int((seconds % 3600) // 60)
        return f"{hours}h {remaining_minutes}m"

def sanitize_filename(filename: str) -> str:
    """
    Sanitize filename for safe filesystem usage
    """
    import re
    # Remove or replace unsafe characters
    filename = re.sub(r'[<>:"/\\|?*]', '_', filename)
    # Remove leading/trailing spaces and dots
    filename = filename.strip(' .')
    # Limit length
    if len(filename) > 255:
        filename = filename[:255]
    return filename

def chunk_list(lst: List[Any], chunk_size: int) -> List[List[Any]]:
    """
    Split a list into chunks of specified size
    """
    return [lst[i:i + chunk_size] for i in range(0, len(lst), chunk_size)]

def deep_merge_dicts(dict1: Dict[str, Any], dict2: Dict[str, Any]) -> Dict[str, Any]:
    """
    Deep merge two dictionaries
    """
    result = dict1.copy()
    
    for key, value in dict2.items():
        if key in result and isinstance(result[key], dict) and isinstance(value, dict):
            result[key] = deep_merge_dicts(result[key], value)
        else:
            result[key] = value
    
    return result

def mask_sensitive_data(data: Dict[str, Any], sensitive_keys: List[str] = None) -> Dict[str, Any]:
    """
    Mask sensitive data in dictionaries for logging
    """
    if sensitive_keys is None:
        sensitive_keys = ['password', 'token', 'secret', 'key', 'credential']
    
    def mask_value(key: str, value: Any) -> Any:
        if isinstance(key, str) and any(sensitive in key.lower() for sensitive in sensitive_keys):
            if isinstance(value, str) and len(value) > 4:
                return f"{value[:2]}{'*' * (len(value) - 4)}{value[-2:]}"
            else:
                return "***"
        elif isinstance(value, dict):
            return {k: mask_value(k, v) for k, v in value.items()}
        elif isinstance(value, list):
            return [mask_value("", item) if isinstance(item, dict) else item for item in value]
        else:
            return value
    
    return {k: mask_value(k, v) for k, v in data.items()}

class RetryConfig:
    """Configuration for retry logic"""
    
    def __init__(
        self,
        max_attempts: int = 3,
        initial_delay: float = 1.0,
        max_delay: float = 60.0,
        exponential_base: float = 2.0,
        jitter: bool = True
    ):
        self.max_attempts = max_attempts
        self.initial_delay = initial_delay
        self.max_delay = max_delay
        self.exponential_base = exponential_base
        self.jitter = jitter

async def retry_async(
    func,
    config: RetryConfig = None,
    exceptions: tuple = (Exception,),
    on_retry: callable = None
):
    """
    Retry an async function with configurable backoff
    """
    import random
    
    config = config or RetryConfig()
    last_exception = None
    
    for attempt in range(config.max_attempts):
        try:
            return await func()
        except exceptions as e:
            last_exception = e
            
            if attempt == config.max_attempts - 1:
                break
            
            # Calculate delay
            delay = min(
                config.initial_delay * (config.exponential_base ** attempt),
                config.max_delay
            )
            
            # Add jitter
            if config.jitter:
                delay *= (0.5 + random.random() * 0.5)
            
            # Call retry callback if provided
            if on_retry:
                await on_retry(attempt + 1, delay, e)
            
            await asyncio.sleep(delay)
    
    raise last_exception

# Template rendering utilities
def utility_render_template(template_str: str, context: Dict[str, Any]) -> str:
    """
    Render Jinja2 template with context
    
    Args:
        template_str: The template string to render
        context: Dictionary of variables to use in template
        
    Returns:
        Rendered template string
        
    Raises:
        Exception: If template rendering fails
    """
    try:
        from jinja2 import Template
        template = Template(template_str)
        return template.render(**context)
    except Exception as e:
        logger.error(f"Template rendering error: {e}")
        raise Exception(f"Template rendering failed: {str(e)}")

def utility_render_file_paths(source_template: str, dest_template: str, 
                             context: Dict[str, Any]) -> tuple[str, str]:
    """
    Render file path templates with parameters
    
    Args:
        source_template: Source file path template
        dest_template: Destination file path template  
        context: Dictionary of variables to use in templates
        
    Returns:
        Tuple of (rendered_source_path, rendered_dest_path)
        
    Raises:
        Exception: If template rendering fails
    """
    try:
        rendered_source = utility_render_template(source_template, context)
        rendered_dest = utility_render_template(dest_template, context)
        return rendered_source, rendered_dest
    except Exception as e:
        logger.error(f"File path rendering error: {e}")
        raise Exception(f"File path rendering failed: {str(e)}")

# Error handling utilities
def utility_create_error_result(error_message: str, log_message: str = None, 
                               exception: Exception = None, exit_code: int = 1) -> Dict[str, Any]:
    """
    Create standardized error result dictionary
    
    Args:
        error_message: Error message to include in stderr
        log_message: Optional message to log (defaults to error_message)
        exception: Optional exception to log
        exit_code: Exit code to return (defaults to 1)
        
    Returns:
        Standardized error result dictionary
    """
    if log_message and exception:
        logger.error(f"{log_message}: {exception}")
    elif log_message:
        logger.error(log_message)
    elif exception:
        logger.error(f"Error: {exception}")
    
    return {
        'status': 'failed',
        'exit_code': exit_code,
        'stdout': '',
        'stderr': error_message
    }