"""
Asset Service Integration Module
Handles all interactions with the asset-service API for infrastructure metadata and credentials.

This module implements:
- Query execution with filtering and pagination
- Credential retrieval with RBAC enforcement
- Result normalization and formatting
- Circuit breaker pattern for reliability
- LRU cache for performance
- Comprehensive error handling
- Observability logging
"""

import os
import time
import logging
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime, timedelta
from collections import OrderedDict
import aiohttp
from enum import Enum

# Import our context module
from pipeline.integration.asset_service_context import (
    ASSET_SERVICE_SCHEMA,
    selection_score,
    should_inject_asset_context,
    get_compact_asset_context
)

logger = logging.getLogger(__name__)


# ============================================================================
# CONFIGURATION
# ============================================================================

ASSET_SERVICE_URL = os.getenv("ASSET_SERVICE_URL", "http://asset-service:3002")
ASSET_SERVICE_TIMEOUT = int(os.getenv("ASSET_SERVICE_TIMEOUT", "10"))
CIRCUIT_BREAKER_THRESHOLD = int(os.getenv("CIRCUIT_BREAKER_THRESHOLD", "5"))
CIRCUIT_BREAKER_TIMEOUT = int(os.getenv("CIRCUIT_BREAKER_TIMEOUT", "60"))
CACHE_SIZE = int(os.getenv("ASSET_CACHE_SIZE", "128"))
CACHE_TTL = int(os.getenv("ASSET_CACHE_TTL", "120"))


# ============================================================================
# ENUMS
# ============================================================================

class QueryMode(str, Enum):
    """Asset query modes"""
    GET_BY_ID = "get_by_id"
    GET_BY_HOSTNAME = "get_by_hostname"
    LIST_ALL = "list_all"
    SEARCH = "search"
    FILTER = "filter"


class CircuitState(str, Enum):
    """Circuit breaker states"""
    CLOSED = "closed"      # Normal operation
    OPEN = "open"          # Failing, reject requests
    HALF_OPEN = "half_open"  # Testing recovery


# ============================================================================
# LRU CACHE
# ============================================================================

class LRUCache:
    """Simple LRU cache with TTL support"""
    
    def __init__(self, max_size: int = 128, ttl_seconds: int = 120):
        self.max_size = max_size
        self.ttl_seconds = ttl_seconds
        self.cache: OrderedDict = OrderedDict()
        self.timestamps: Dict[str, float] = {}
        self.hits = 0
        self.misses = 0
    
    def get(self, key: str) -> Optional[Any]:
        """Get value from cache if not expired"""
        if key not in self.cache:
            self.misses += 1
            return None
        
        # Check TTL
        if time.time() - self.timestamps[key] > self.ttl_seconds:
            self.cache.pop(key)
            self.timestamps.pop(key)
            self.misses += 1
            return None
        
        # Move to end (most recently used)
        self.cache.move_to_end(key)
        self.hits += 1
        return self.cache[key]
    
    def put(self, key: str, value: Any) -> None:
        """Put value in cache, evict oldest if full"""
        if key in self.cache:
            self.cache.move_to_end(key)
        else:
            if len(self.cache) >= self.max_size:
                # Evict oldest
                oldest_key = next(iter(self.cache))
                self.cache.pop(oldest_key)
                self.timestamps.pop(oldest_key)
        
        self.cache[key] = value
        self.timestamps[key] = time.time()
    
    def clear(self) -> None:
        """Clear all cache entries"""
        self.cache.clear()
        self.timestamps.clear()
    
    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics"""
        total_requests = self.hits + self.misses
        hit_rate = (self.hits / total_requests * 100) if total_requests > 0 else 0
        
        return {
            "size": len(self.cache),
            "max_size": self.max_size,
            "hits": self.hits,
            "misses": self.misses,
            "hit_rate": f"{hit_rate:.1f}%",
            "ttl_seconds": self.ttl_seconds
        }


# ============================================================================
# CIRCUIT BREAKER
# ============================================================================

class CircuitBreaker:
    """Circuit breaker for asset-service calls"""
    
    def __init__(self, threshold: int = 5, timeout: int = 60):
        self.threshold = threshold
        self.timeout = timeout
        self.failure_count = 0
        self.last_failure_time: Optional[float] = None
        self.state = CircuitState.CLOSED
    
    def record_success(self) -> None:
        """Record successful call"""
        self.failure_count = 0
        self.state = CircuitState.CLOSED
    
    def record_failure(self) -> None:
        """Record failed call"""
        self.failure_count += 1
        self.last_failure_time = time.time()
        
        if self.failure_count >= self.threshold:
            self.state = CircuitState.OPEN
            logger.warning(
                f"Circuit breaker OPEN: {self.failure_count} failures",
                extra={"threshold": self.threshold}
            )
    
    def can_attempt(self) -> Tuple[bool, str]:
        """Check if request can be attempted"""
        if self.state == CircuitState.CLOSED:
            return True, "Circuit closed, normal operation"
        
        if self.state == CircuitState.OPEN:
            # Check if timeout has passed
            if self.last_failure_time and (time.time() - self.last_failure_time) > self.timeout:
                self.state = CircuitState.HALF_OPEN
                logger.info("Circuit breaker entering HALF_OPEN state")
                return True, "Circuit half-open, testing recovery"
            
            return False, f"Circuit breaker OPEN, retry after {self.timeout}s"
        
        # HALF_OPEN state
        return True, "Circuit half-open, testing recovery"
    
    def get_state(self) -> Dict[str, Any]:
        """Get circuit breaker state"""
        return {
            "state": self.state.value,
            "failure_count": self.failure_count,
            "threshold": self.threshold,
            "timeout": self.timeout,
            "last_failure": datetime.fromtimestamp(self.last_failure_time).isoformat() if self.last_failure_time else None
        }


# ============================================================================
# ASSET SERVICE CLIENT
# ============================================================================

class AssetServiceClient:
    """Client for interacting with asset-service API"""
    
    def __init__(self):
        self.base_url = ASSET_SERVICE_URL
        self.timeout = ASSET_SERVICE_TIMEOUT
        self.cache = LRUCache(max_size=CACHE_SIZE, ttl_seconds=CACHE_TTL)
        self.circuit_breaker = CircuitBreaker(
            threshold=CIRCUIT_BREAKER_THRESHOLD,
            timeout=CIRCUIT_BREAKER_TIMEOUT
        )
        self.session: Optional[aiohttp.ClientSession] = None
    
    async def _get_session(self) -> aiohttp.ClientSession:
        """Get or create aiohttp session"""
        if self.session is None or self.session.closed:
            timeout = aiohttp.ClientTimeout(total=self.timeout)
            self.session = aiohttp.ClientSession(timeout=timeout)
        return self.session
    
    async def close(self) -> None:
        """Close aiohttp session"""
        if self.session and not self.session.closed:
            await self.session.close()
    
    async def _make_request(
        self,
        method: str,
        endpoint: str,
        params: Optional[Dict] = None,
        json_data: Optional[Dict] = None,
        use_cache: bool = True
    ) -> Dict[str, Any]:
        """Make HTTP request to asset-service with circuit breaker and caching"""
        
        # Check circuit breaker
        can_attempt, reason = self.circuit_breaker.can_attempt()
        if not can_attempt:
            logger.error(f"Circuit breaker prevented request: {reason}")
            return {
                "success": False,
                "error": "service_unavailable",
                "message": reason
            }
        
        # Check cache for GET requests
        cache_key = None
        if method == "GET" and use_cache:
            cache_key = f"{endpoint}:{str(params)}"
            cached = self.cache.get(cache_key)
            if cached:
                logger.debug(f"Cache HIT: {cache_key}")
                return cached
            logger.debug(f"Cache MISS: {cache_key}")
        
        # Make request
        url = f"{self.base_url}{endpoint}"
        start_time = time.time()
        
        try:
            session = await self._get_session()
            
            async with session.request(
                method=method,
                url=url,
                params=params,
                json=json_data
            ) as response:
                duration_ms = (time.time() - start_time) * 1000
                
                if response.status == 200:
                    result = await response.json()
                    
                    # Cache successful GET responses
                    if method == "GET" and use_cache and cache_key:
                        self.cache.put(cache_key, result)
                    
                    self.circuit_breaker.record_success()
                    
                    logger.info(
                        f"Asset-service request successful",
                        extra={
                            "method": method,
                            "endpoint": endpoint,
                            "status": response.status,
                            "duration_ms": f"{duration_ms:.1f}"
                        }
                    )
                    
                    return result
                
                else:
                    error_text = await response.text()
                    self.circuit_breaker.record_failure()
                    
                    logger.error(
                        f"Asset-service request failed",
                        extra={
                            "method": method,
                            "endpoint": endpoint,
                            "status": response.status,
                            "error": error_text,
                            "duration_ms": f"{duration_ms:.1f}"
                        }
                    )
                    
                    return {
                        "success": False,
                        "error": "api_error",
                        "message": f"HTTP {response.status}: {error_text}",
                        "status_code": response.status
                    }
        
        except aiohttp.ClientError as e:
            duration_ms = (time.time() - start_time) * 1000
            self.circuit_breaker.record_failure()
            
            logger.error(
                f"Asset-service connection error",
                extra={
                    "method": method,
                    "endpoint": endpoint,
                    "error": str(e),
                    "duration_ms": f"{duration_ms:.1f}"
                }
            )
            
            return {
                "success": False,
                "error": "connection_error",
                "message": f"Failed to connect to asset-service: {str(e)}"
            }
        
        except Exception as e:
            duration_ms = (time.time() - start_time) * 1000
            self.circuit_breaker.record_failure()
            
            logger.error(
                f"Asset-service unexpected error",
                extra={
                    "method": method,
                    "endpoint": endpoint,
                    "error": str(e),
                    "duration_ms": f"{duration_ms:.1f}"
                }
            )
            
            return {
                "success": False,
                "error": "unexpected_error",
                "message": f"Unexpected error: {str(e)}"
            }
    
    # ========================================================================
    # QUERY METHODS (READ-ONLY, LOW RISK)
    # ========================================================================
    
    async def list_assets(
        self,
        search: Optional[str] = None,
        os_type: Optional[str] = None,
        service_type: Optional[str] = None,
        environment: Optional[str] = None,
        is_active: Optional[bool] = None,
        limit: int = 100,
        skip: int = 0
    ) -> Dict[str, Any]:
        """
        List assets with optional filtering.
        
        Returns metadata only (no credentials).
        """
        params = {
            "limit": limit,
            "skip": skip
        }
        
        if search:
            params["search"] = search
        if os_type:
            params["os_type"] = os_type
        if service_type:
            params["service_type"] = service_type
        if is_active is not None:
            params["is_active"] = is_active
        
        return await self._make_request("GET", "/", params=params)
    
    async def get_asset_by_id(self, asset_id: int) -> Dict[str, Any]:
        """
        Get asset by ID.
        
        Returns full metadata (no credentials in response).
        """
        return await self._make_request("GET", f"/{asset_id}")
    
    async def search_assets(self, query: str, limit: int = 10) -> Dict[str, Any]:
        """
        Search assets by name, hostname, or description.
        
        Convenience wrapper around list_assets.
        """
        return await self.list_assets(search=query, limit=limit)
    
    # ========================================================================
    # EXPORT METHODS
    # ========================================================================
    
    async def export_assets_csv(self) -> str:
        """
        Export all assets to CSV format.
        
        Returns:
            CSV string with all assets
            
        Raises:
            Exception: If export fails
        """
        try:
            url = f"{self.base_url}/export/csv"
            logger.info(f"Exporting assets to CSV from {url}")
            
            async with aiohttp.ClientSession() as session:
                async with session.get(url, timeout=aiohttp.ClientTimeout(total=30)) as response:
                    if response.status == 200:
                        csv_content = await response.text()
                        logger.info(f"Successfully exported {len(csv_content)} bytes of CSV data")
                        return csv_content
                    else:
                        error_msg = f"CSV export failed with status {response.status}"
                        logger.error(error_msg)
                        raise Exception(error_msg)
                        
        except Exception as e:
            logger.error(f"Failed to export CSV: {e}")
            raise
    
    # ========================================================================
    # CREDENTIAL METHODS (GATED, HIGH RISK)
    # ========================================================================
    
    async def get_asset_credentials(
        self,
        asset_id: int,
        credential_type: str,
        justification: str,
        user_id: Optional[str] = None,
        tenant_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Retrieve credentials for an asset (GATED ACCESS).
        
        This method should:
        1. Enforce RBAC checks
        2. Log access attempts
        3. Return credential handles (not raw secrets)
        4. Require justification
        
        NOTE: This is a placeholder. Real implementation needs:
        - RBAC enforcement
        - Audit logging
        - Credential handle generation
        - TTL management
        """
        
        # TODO: Implement RBAC check
        # if not has_permission(user_id, "asset-credentials-read"):
        #     return {"success": False, "error": "permission_denied"}
        
        # TODO: Log access attempt
        logger.warning(
            f"Credential access requested",
            extra={
                "asset_id": asset_id,
                "credential_type": credential_type,
                "justification": justification,
                "user_id": user_id,
                "tenant_id": tenant_id
            }
        )
        
        # For now, return error (not implemented)
        return {
            "success": False,
            "error": "not_implemented",
            "message": "Credential retrieval not yet implemented. Use asset-service UI for now."
        }
    
    # ========================================================================
    # UTILITY METHODS
    # ========================================================================
    
    def get_health(self) -> Dict[str, Any]:
        """Get client health status"""
        return {
            "service_url": self.base_url,
            "circuit_breaker": self.circuit_breaker.get_state(),
            "cache": self.cache.get_stats(),
            "session_open": self.session is not None and not self.session.closed
        }
    
    def clear_cache(self) -> None:
        """Clear the cache"""
        self.cache.clear()
        logger.info("Asset-service cache cleared")


# ============================================================================
# RESULT FORMATTING
# ============================================================================

def format_asset_for_llm(asset: Dict[str, Any]) -> str:
    """
    Format asset data for LLM consumption.
    
    Returns a compact, readable string representation.
    """
    lines = []
    
    # Basic info
    lines.append(f"Asset: {asset.get('name', 'Unknown')}")
    lines.append(f"  Hostname: {asset.get('hostname', 'N/A')}")
    
    if asset.get('ip_address'):
        lines.append(f"  IP: {asset['ip_address']}")
    
    if asset.get('description'):
        lines.append(f"  Description: {asset['description']}")
    
    # Environment and status
    lines.append(f"  Environment: {asset.get('environment', 'unknown')}")
    lines.append(f"  Status: {asset.get('status', 'unknown')}")
    
    # OS info
    if asset.get('os_type'):
        os_info = asset['os_type']
        if asset.get('os_version'):
            os_info += f" {asset['os_version']}"
        lines.append(f"  OS: {os_info}")
    
    # Service info
    if asset.get('service_type'):
        service_info = asset['service_type']
        if asset.get('port'):
            service_info += f":{asset['port']}"
        lines.append(f"  Service: {service_info}")
    
    # Tags
    if asset.get('tags'):
        tags = asset['tags']
        if isinstance(tags, list) and tags:
            lines.append(f"  Tags: {', '.join(tags)}")
    
    # Location
    if asset.get('data_center'):
        lines.append(f"  Location: {asset['data_center']}")
    
    return "\n".join(lines)


def format_asset_list_for_llm(assets: List[Dict[str, Any]], total: int) -> str:
    """
    Format list of assets for LLM consumption.
    
    Returns a compact table-like representation.
    """
    if not assets:
        return "No assets found."
    
    lines = [f"Found {total} asset(s):\n"]
    
    for asset in assets:
        lines.append(f"• {asset.get('name', 'Unknown')} ({asset.get('hostname', 'N/A')})")
        
        if asset.get('ip_address'):
            lines.append(f"  IP: {asset['ip_address']}")
        
        if asset.get('environment'):
            lines.append(f"  Env: {asset['environment']}")
        
        if asset.get('status'):
            lines.append(f"  Status: {asset['status']}")
        
        lines.append("")  # Blank line between assets
    
    return "\n".join(lines)


# ============================================================================
# SINGLETON INSTANCE
# ============================================================================

# Global client instance
_client: Optional[AssetServiceClient] = None


def get_asset_client() -> AssetServiceClient:
    """Get or create the global asset service client"""
    global _client
    if _client is None:
        _client = AssetServiceClient()
    return _client


async def close_asset_client() -> None:
    """Close the global asset service client"""
    global _client
    if _client:
        await _client.close()
        _client = None