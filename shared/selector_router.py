from fastapi import APIRouter, Request, Query, Response
from typing import Optional, List
from selector.dao import select_topk
import asyncio
import time
import hashlib

router = APIRouter()

# Last-Known-Good cache: process-local, no Redis
_LKG = {}   # key -> (expiry_ts, payload)
_TTL = 600  # seconds (10 minutes)

def _key(query: str, k: int, plats: list[str]) -> str:
    """Generate cache key from query parameters"""
    raw = f"{query}|{k}|{','.join(sorted(plats))}"
    return "selector:" + hashlib.sha256(raw.encode()).hexdigest()

@router.get("/api/selector/search")
async def selector_search(
    request: Request,
    response: Response,
    query: str = Query(..., min_length=1),
    k: int = Query(5, ge=1, le=20),
    platform: Optional[str] = None,
):
    # Normalize k to valid range
    k = max(1, min(20, k))
    
    plats: List[str] = [p.strip() for p in platform.split(",")] if platform else []
    key = _key(query, k, plats)
    
    # Get the database pool from the service instance
    app = request.app
    service = getattr(app.state, "service", None)
    
    if service is None:
        return {"error": "Service instance not found on app.state", "status": 503}
    
    # Get the pool from service.db.pool (DatabasePool wrapper)
    pool = None
    if hasattr(service, 'db') and hasattr(service.db, 'pool'):
        pool = service.db.pool
    
    if pool is None:
        return {"error": "Database pool not initialized", "status": 503}
    
    try:
        # Try to fetch from DB with 1s timeout
        async with pool.acquire() as conn:
            async def _run():
                return await select_topk(conn, query, plats, k)
            rows = await asyncio.wait_for(_run(), timeout=1.0)
        
        # Success: build payload and cache it
        payload = {
            "query": query,
            "k": k,
            "platform": plats,
            "results": rows,
            "from_cache": False
        }
        _LKG[key] = (time.time() + _TTL, payload)
        return payload
        
    except Exception:
        # DB failed or timed out: try LKG cache
        exp, payload = _LKG.get(key, (0, None))
        if payload and exp > time.time():
            # Return cached result
            payload = dict(payload)
            payload["from_cache"] = True
            return payload
        
        # No valid cache: return 503
        response.status_code = 503
        return {"error": "selector unavailable", "retry": "soon"}