"""
Cache Management API Endpoints

Provides endpoints for cache statistics, health checks, and manual invalidation.
"""

from fastapi import APIRouter, HTTPException, Query
from typing import Dict, Any
import logging

from pipeline.cache.cache_manager import CacheManager
import os

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/cache", tags=["cache"])

# Initialize cache manager (shared instance)
cache_enabled = os.getenv("CACHE_ENABLED", "true").lower() == "true"
redis_url = os.getenv("REDIS_URL", "redis://localhost:6379")
cache_manager = CacheManager(redis_url=redis_url, enabled=cache_enabled)


@router.get("/stats", response_model=Dict[str, Any])
async def get_cache_stats():
    """
    Get cache statistics.
    
    Returns:
        Cache statistics including hits, misses, and hit rate
    """
    try:
        stats = cache_manager.get_stats()
        redis_info = cache_manager.get_redis_info()
        
        return {
            "cache_stats": stats,
            "redis_stats": redis_info,
            "timestamp": "2025-01-XX"  # Will be updated dynamically
        }
    except Exception as e:
        logger.error(f"Failed to get cache stats: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get cache stats: {str(e)}")


@router.get("/health", response_model=Dict[str, Any])
async def get_cache_health():
    """
    Check cache health status.
    
    Returns:
        Health status of the cache system
    """
    try:
        health = cache_manager.health_check()
        return health
    except Exception as e:
        logger.error(f"Cache health check failed: {e}")
        return {
            "status": "unhealthy",
            "message": f"Health check failed: {str(e)}"
        }


@router.post("/invalidate", response_model=Dict[str, Any])
async def invalidate_cache(
    pattern: str = Query("*", description="Redis key pattern to invalidate (e.g., 'stage_a:*', '*')")
):
    """
    Invalidate cache entries matching pattern.
    
    Args:
        pattern: Redis key pattern (default: "*" for all keys)
        
    Returns:
        Number of keys invalidated
    """
    try:
        count = cache_manager.invalidate(pattern)
        logger.info(f"Invalidated {count} cache entries matching pattern: {pattern}")
        
        return {
            "success": True,
            "pattern": pattern,
            "invalidated_count": count,
            "message": f"Successfully invalidated {count} cache entries"
        }
    except Exception as e:
        logger.error(f"Failed to invalidate cache: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to invalidate cache: {str(e)}")


@router.post("/invalidate/all", response_model=Dict[str, Any])
async def invalidate_all_cache():
    """
    Invalidate all OpsConductor cache entries.
    
    Returns:
        Number of keys invalidated
    """
    try:
        count = cache_manager.invalidate_all()
        logger.info(f"Invalidated all cache entries: {count} keys")
        
        return {
            "success": True,
            "invalidated_count": count,
            "message": f"Successfully invalidated all {count} cache entries"
        }
    except Exception as e:
        logger.error(f"Failed to invalidate all cache: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to invalidate all cache: {str(e)}")


@router.post("/invalidate/stage/{stage}", response_model=Dict[str, Any])
async def invalidate_stage_cache(stage: str):
    """
    Invalidate cache for a specific pipeline stage.
    
    Args:
        stage: Stage name (stage_a, stage_b, stage_c)
        
    Returns:
        Number of keys invalidated
    """
    valid_stages = ["stage_a", "stage_b", "stage_c"]
    if stage not in valid_stages:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid stage: {stage}. Must be one of: {', '.join(valid_stages)}"
        )
    
    try:
        pattern = f"{stage}:*"
        count = cache_manager.invalidate(pattern)
        logger.info(f"Invalidated {stage} cache: {count} keys")
        
        return {
            "success": True,
            "stage": stage,
            "invalidated_count": count,
            "message": f"Successfully invalidated {count} {stage} cache entries"
        }
    except Exception as e:
        logger.error(f"Failed to invalidate {stage} cache: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to invalidate {stage} cache: {str(e)}")