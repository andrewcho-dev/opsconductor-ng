"""
Service authentication utility module

Handles service-to-service authentication including token management,
credential caching, and authentication header preparation for inter-service
communication within the OpsConductor platform.

Features:
- Service token acquisition and caching
- Authentication header preparation
- Token refresh and expiration handling
- Service identity management

Example:
    import utility_service_auth as service_auth_utility
    
    # Initialize with configuration
    service_auth_utility.set_config({
        "auth_service_url": "http://auth-service:3001",
        "service_credentials": {
            "username": "scheduler-service",
            "password": "service_password"
        }
    })
    
    # Get authentication headers for service calls
    headers = await service_auth_utility.get_service_auth_headers("scheduler-service")
    
    # Use with ServiceClient
    client = get_service_client("jobs-service")
    response = await client.get("/jobs", headers=headers)
"""

import os
import time
import logging
from typing import Dict, Any, Optional, Tuple
from datetime import datetime, timedelta

from .utils import get_service_client
from .errors import AuthError, ServiceCommunicationError
from .logging import get_logger

# Global configuration and state
CONFIG = {}
_token_cache: Dict[str, Dict[str, Any]] = {}
_default_service_credentials = {
    "username": "admin",
    "password": "admin123"
}

logger = get_logger(__name__)

def set_config(config: Dict[str, Any]) -> None:
    """
    Set configuration for service authentication
    
    Args:
        config: Configuration dictionary containing:
            - auth_service_url: URL of the auth service
            - service_credentials: Dict with username/password for service auth
            - token_cache_duration: Token cache duration in seconds (default: 3600)
    """
    global CONFIG
    CONFIG.update(config)
    logger.info("Service authentication configuration updated")

def _get_auth_service_url() -> str:
    """Get auth service URL from config or environment"""
    return CONFIG.get("auth_service_url") or os.getenv("AUTH_SERVICE_URL", "http://auth-service:3001")

def _get_service_credentials(service_name: str) -> Dict[str, str]:
    """
    Get service credentials for authentication
    
    Args:
        service_name: Name of the service requesting authentication
        
    Returns:
        Dict containing username and password
    """
    # Check for service-specific credentials in config
    service_creds = CONFIG.get("service_credentials", {})
    if isinstance(service_creds, dict) and "username" in service_creds:
        return service_creds
    
    # Check for service-specific environment variables
    username = os.getenv(f"{service_name.upper().replace('-', '_')}_USERNAME")
    password = os.getenv(f"{service_name.upper().replace('-', '_')}_PASSWORD")
    
    if username and password:
        return {"username": username, "password": password}
    
    # Fall back to default admin credentials
    logger.warning(f"Using default credentials for service {service_name}")
    return _default_service_credentials

def _is_token_valid(token_data: Dict[str, Any]) -> bool:
    """
    Check if cached token is still valid
    
    Args:
        token_data: Token data from cache
        
    Returns:
        True if token is valid, False otherwise
    """
    if not token_data or "expires_at" not in token_data:
        return False
    
    # Add 60 second buffer before expiration
    buffer_time = 60
    return time.time() < (token_data["expires_at"] - buffer_time)

async def _acquire_service_token(service_name: str) -> Dict[str, Any]:
    """
    Acquire a new service token from auth service
    
    Args:
        service_name: Name of the service requesting token
        
    Returns:
        Dict containing token and expiration info
        
    Raises:
        AuthError: If authentication fails
        ServiceCommunicationError: If auth service is unavailable
    """
    try:
        auth_service_url = _get_auth_service_url()
        credentials = _get_service_credentials(service_name)
        
        # Get auth service client
        auth_client = get_service_client("auth-service", auth_service_url)
        
        # Authenticate with auth service
        response = await auth_client.post_json("/login", {
            "username": credentials["username"],
            "password": credentials["password"]
        })
        
        if "access_token" not in response:
            raise AuthError("Invalid response from auth service - no access token")
        
        # Calculate expiration time (default to 1 hour if not provided)
        expires_in = response.get("expires_in", 3600)
        expires_at = time.time() + expires_in
        
        token_data = {
            "access_token": response["access_token"],
            "expires_at": expires_at,
            "expires_in": expires_in,
            "acquired_at": time.time()
        }
        
        logger.info(f"Successfully acquired service token for {service_name}")
        return token_data
        
    except Exception as e:
        if isinstance(e, (AuthError, ServiceCommunicationError)):
            raise
        
        logger.error(f"Failed to acquire service token for {service_name}: {e}")
        raise ServiceCommunicationError("auth-service", f"Token acquisition failed: {str(e)}")

async def get_service_token(service_name: str, force_refresh: bool = False) -> str:
    """
    Get a valid service token, using cache when possible
    
    Args:
        service_name: Name of the service requesting token
        force_refresh: Force token refresh even if cached token is valid
        
    Returns:
        Valid access token string
        
    Raises:
        AuthError: If authentication fails
        ServiceCommunicationError: If auth service is unavailable
    """
    try:
        # Check cache first (unless force refresh)
        if not force_refresh and service_name in _token_cache:
            cached_token = _token_cache[service_name]
            if _is_token_valid(cached_token):
                logger.debug(f"Using cached token for {service_name}")
                return cached_token["access_token"]
        
        # Acquire new token
        logger.info(f"Acquiring new service token for {service_name}")
        token_data = await _acquire_service_token(service_name)
        
        # Cache the token
        _token_cache[service_name] = token_data
        
        return token_data["access_token"]
        
    except Exception as e:
        logger.error(f"Failed to get service token for {service_name}: {e}")
        raise

async def get_service_auth_headers(service_name: str, additional_headers: Optional[Dict[str, str]] = None) -> Dict[str, str]:
    """
    Get authentication headers for service-to-service calls
    
    Args:
        service_name: Name of the service making the request
        additional_headers: Optional additional headers to include
        
    Returns:
        Dict containing authentication headers
        
    Raises:
        AuthError: If authentication fails
        ServiceCommunicationError: If auth service is unavailable
    """
    try:
        token = await get_service_token(service_name)
        
        headers = {
            "Authorization": f"Bearer {token}",
            "User-Agent": f"OpsConductor-{service_name}/1.0.0",
            "Content-Type": "application/json"
        }
        
        # Add any additional headers
        if additional_headers:
            headers.update(additional_headers)
        
        return headers
        
    except Exception as e:
        logger.error(f"Failed to get auth headers for {service_name}: {e}")
        raise

async def refresh_service_token(service_name: str) -> str:
    """
    Force refresh of service token
    
    Args:
        service_name: Name of the service
        
    Returns:
        New access token string
    """
    logger.info(f"Force refreshing token for {service_name}")
    return await get_service_token(service_name, force_refresh=True)

def clear_token_cache(service_name: Optional[str] = None) -> None:
    """
    Clear token cache for specific service or all services
    
    Args:
        service_name: Service name to clear, or None to clear all
    """
    global _token_cache
    
    if service_name:
        if service_name in _token_cache:
            del _token_cache[service_name]
            logger.info(f"Cleared token cache for {service_name}")
    else:
        _token_cache.clear()
        logger.info("Cleared all token cache")

def get_token_cache_info(service_name: Optional[str] = None) -> Dict[str, Any]:
    """
    Get information about cached tokens
    
    Args:
        service_name: Specific service to check, or None for all services
        
    Returns:
        Dict containing cache information
    """
    if service_name:
        if service_name in _token_cache:
            token_data = _token_cache[service_name]
            return {
                "service": service_name,
                "has_token": True,
                "is_valid": _is_token_valid(token_data),
                "expires_at": datetime.fromtimestamp(token_data["expires_at"]).isoformat(),
                "acquired_at": datetime.fromtimestamp(token_data["acquired_at"]).isoformat()
            }
        else:
            return {
                "service": service_name,
                "has_token": False,
                "is_valid": False
            }
    else:
        # Return info for all cached tokens
        cache_info = {}
        for svc_name, token_data in _token_cache.items():
            cache_info[svc_name] = {
                "has_token": True,
                "is_valid": _is_token_valid(token_data),
                "expires_at": datetime.fromtimestamp(token_data["expires_at"]).isoformat(),
                "acquired_at": datetime.fromtimestamp(token_data["acquired_at"]).isoformat()
            }
        return cache_info

async def validate_service_token(token: str) -> bool:
    """
    Validate a service token with the auth service
    
    Args:
        token: Token to validate
        
    Returns:
        True if token is valid, False otherwise
    """
    try:
        auth_service_url = _get_auth_service_url()
        auth_client = get_service_client("auth-service", auth_service_url)
        
        headers = {"Authorization": f"Bearer {token}"}
        response = await auth_client.get("/verify", headers=headers)
        
        return response.status_code == 200
        
    except Exception as e:
        logger.error(f"Token validation failed: {e}")
        return False