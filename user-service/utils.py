#!/usr/bin/env python3
"""
Service Utils Template
Self-contained utilities for microservices
Copy this file to your service directory and customize as needed
"""

import os
import time
import asyncio
from typing import Dict, Any, Optional, List, Union
import httpx
import logging

logger = logging.getLogger(__name__)

class ServiceClient:
    """Standardized HTTP client for inter-service communication"""
    
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
        self.logger = logging.getLogger(f"service_client.{service_name}")
    
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
                
                duration = time.time() - start_time
                self.logger.info(f"{method} {url} - {response.status_code} - {duration:.3f}s")
                
                return response
                
            except Exception as e:
                self.logger.warning(f"Request failed (attempt {attempt + 1}/{self.retries + 1}): {e}")
                
                if attempt < self.retries:
                    await asyncio.sleep(self.retry_delay * (2 ** attempt))  # Exponential backoff
                else:
                    raise
    
    async def get(self, endpoint: str, **kwargs) -> httpx.Response:
        """Make GET request"""
        return await self._make_request("GET", endpoint, **kwargs)
    
    async def post(self, endpoint: str, **kwargs) -> httpx.Response:
        """Make POST request"""
        return await self._make_request("POST", endpoint, **kwargs)
    
    async def put(self, endpoint: str, **kwargs) -> httpx.Response:
        """Make PUT request"""
        return await self._make_request("PUT", endpoint, **kwargs)
    
    async def delete(self, endpoint: str, **kwargs) -> httpx.Response:
        """Make DELETE request"""
        return await self._make_request("DELETE", endpoint, **kwargs)
    
    async def patch(self, endpoint: str, **kwargs) -> httpx.Response:
        """Make PATCH request"""
        return await self._make_request("PATCH", endpoint, **kwargs)

def get_service_client(service_name: str, base_url: str = None) -> ServiceClient:
    """Get a service client instance"""
    if base_url is None:
        # Default service URLs based on service name
        service_urls = {
            "auth-service": "http://auth-service:3001",
            "user-service": "http://user-service:3002", 
            "credentials-service": "http://credentials-service:3003",
            "targets-service": "http://targets-service:3004",
            "notification-service": "http://notification-service:3005",
            "discovery-service": "http://discovery-service:3006",
            "step-libraries-service": "http://step-libraries-service:3007",
            "jobs-service": "http://jobs-service:3008",
            "executor-service": "http://executor-service:3009"
        }
        base_url = service_urls.get(service_name, f"http://{service_name}:3000")
    
    return ServiceClient(service_name, base_url)

def validate_pagination_params(page: int = 1, limit: int = 50) -> tuple[int, int]:
    """Validate and normalize pagination parameters"""
    page = max(1, page)
    limit = max(1, min(limit, 1000))  # Cap at 1000 items per page
    return page, limit

def calculate_offset(page: int, limit: int) -> int:
    """Calculate database offset from page and limit"""
    return (page - 1) * limit