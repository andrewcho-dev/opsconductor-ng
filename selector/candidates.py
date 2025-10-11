import os
from psycopg2.extras import RealDictCursor  # type: ignore

def _conn():
    import psycopg2  # defer import so merely importing this module doesn't require the wheel
    dsn = os.environ.get("DATABASE_URL")
    if not dsn:
        raise RuntimeError("DATABASE_URL not set")
    return psycopg2.connect(dsn)

def candidate_tools_from_intent(intent: str, k: int = 10):
    """
    Returns compact tool 'stubs' ranked by vector similarity.
    Uses Postgres hashed_embed() — no external models/keys.
    """
    sql = """
    SELECT t.key,
           t.name,
           LEFT(COALESCE(t.description,''), 160) AS short_desc
    FROM public.tool_embedding te
    JOIN public.tool t ON t.id = te.tool_id
    ORDER BY te.embedding <=> public.hashed_embed(%s)
    LIMIT %s
    """
    with _conn() as conn, conn.cursor(cursor_factory=RealDictCursor) as cur:
        cur.execute(sql, (intent, k))
        rows = cur.fetchall()
    return [{"key": r["key"], "name": r["name"], "short_desc": r["short_desc"]} for r in rows]
