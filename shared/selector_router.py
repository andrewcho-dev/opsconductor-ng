from fastapi import APIRouter, Request, Query
from typing import Optional, List
from selector.dao import select_topk

router = APIRouter()

@router.get("/api/selector/search")
async def selector_search(
    request: Request,
    query: str = Query(..., min_length=1),
    k: int = Query(5, ge=1, le=20),
    platform: Optional[str] = None,
):
    plats: List[str] = [p.strip() for p in platform.split(",")] if platform else []
    
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
        async with pool.acquire() as conn:
            rows = await select_topk(conn, query, plats, k)
        
        return {
            "query": query,
            "k": k,
            "platform": plats,
            "results": rows
        }
    except Exception as e:
        return {
            "error": f"Search failed: {str(e)}",
            "status": 500
        }