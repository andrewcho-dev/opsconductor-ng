"""Candidate tool generation from user intent (DB-backed or fallback)."""

import os
from typing import List, Dict


def get_always_include_tools() -> List[str]:
    """Read ALWAYS_INCLUDE_TOOLS env var and return a cleaned list."""
    raw = os.environ.get("ALWAYS_INCLUDE_TOOLS", "")
    vals = [s.strip() for s in raw.split(",")]
    return [v for v in vals if v]


# Feature flag: only hit Postgres when explicitly enabled
USE_SELECTOR_DB = os.environ.get("USE_SELECTOR_DB") == "1"


def _conn():
    """
    Lazy import psycopg2 so this module can be imported without the package.
    Only called if USE_SELECTOR_DB=1.
    """
    import psycopg2  # type: ignore
    from psycopg2.extras import RealDictCursor  # type: ignore

    dsn = os.environ.get("DATABASE_URL")
    if not dsn:
        raise RuntimeError("DATABASE_URL not set")
    return psycopg2.connect(dsn), RealDictCursor


def _fallback(intent: str, k: int = 10) -> List[Dict[str, str]]:
    """
    No-DB path used in CI unit tests.
    Returns compact stubs from ALWAYS_INCLUDE_TOOLS or a small default set.
    """
    tools = get_always_include_tools() or ["asset-query", "service-status", "network-ping"]
    return [{"key": t, "name": t, "short_desc": ""} for t in tools][:k]


def candidate_tools_from_intent(intent: str, k: int = 10) -> List[Dict[str, str]]:
    """
    If USE_SELECTOR_DB=1 and a DATABASE_URL is set, query Postgres using hashed_embed().
    Otherwise, return the fallback stubs so unit tests don’t need a DB.
    """
    if not USE_SELECTOR_DB:
        return _fallback(intent, k)

    try:
        conn, RealDictCursor = _conn()
    except Exception:
        # If DB isn’t reachable or psycopg2 isn’t available, fall back gracefully.
        return _fallback(intent, k)

    sql = """
        SELECT t.key,
               t.name,
               LEFT(COALESCE(t.description,''), 160) AS short_desc
        FROM public.tool_embedding te
        JOIN public.tool t ON t.id = te.tool_id
        ORDER BY te.embedding <=> public.hashed_embed(%s)
        LIMIT %s
    """
    with conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(sql, (intent, k))
            rows = cur.fetchall()
    return [{"key": r["key"], "name": r["name"], "short_desc": r["short_desc"]} for r in rows]
