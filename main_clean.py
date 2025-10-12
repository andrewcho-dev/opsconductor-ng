# --- SELECTOR ENDPOINT HOTFIX ---
from typing import Optional, List
from fastapi import APIRouter, Request, Query

try:
    from selector.dao import select_topk
except Exception as e:
    select_topk = None
    print("[selector] import error:", e)

_selector_router = APIRouter()

@_selector_router.get("/api/selector/search")
async def _selector_search(
    request: Request,
    query: str = Query(..., min_length=1),
    k: int = Query(5, ge=1, le=20),
    platform: Optional[str] = None,
):
    if select_topk is None:
        return {"error": "selector.dao not available"}
    plats: List[str] = [p.strip() for p in platform.split(",")] if platform else []
    app = request.app
    pool = getattr(getattr(app, "state", app), "db", None) or \
           getattr(getattr(app, "state", app), "db_pool", None) or \
           getattr(app, "db_pool", None)
    if pool is None:
        return {"error": "DB pool not found on app.state"}
    async with pool.acquire() as conn:
        rows = await select_topk(conn, query, plats, k)
    return {"query": query, "k": k, "platform": plats, "results": rows}

def _mount_selector(candidate):
    if candidate is None:
        return False
    app_obj = getattr(candidate, "app", None) if hasattr(candidate, "app") else candidate
    if hasattr(app_obj, "include_router"):
        app_obj.include_router(_selector_router)
        print("[selector] route mounted on", getattr(app_obj, "title", "app"))
        return True
    return False

_mounted = False
for _name in ("service", "app", "application", "api"):
    _mounted |= _mount_selector(globals().get(_name))
if not _mounted:
    print("[selector] WARNING: failed to mount; ensure this block is at file end after app creation")
# --- END SELECTOR ENDPOINT HOTFIX ---
