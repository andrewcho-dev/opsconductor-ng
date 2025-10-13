"""
Selector Data Access Object (DAO).

Provides database operations for tool selection using vector similarity search.
Uses shared embedding functions to ensure compatibility with tool indexing.

Usage:
    import asyncpg
    from selector.dao import select_topk
    
    conn = await asyncpg.connect(dsn="postgresql://...")
    results = await select_topk(conn, "scan network", platform=["linux"], k=5)
    for tool in results:
        print(f"{tool['key']}: {tool['name']}")
"""

import os
import sys
from typing import Sequence, Optional, Dict, Any, List

# Add parent directory to path so 'shared' module can be imported
# Try both /app (Docker) and relative path (local dev)
parent_paths = [
    '/app',
    os.path.abspath(os.path.join(os.path.dirname(__file__), '../..'))
]
for path in parent_paths:
    shared_dir = os.path.join(path, 'shared')
    if os.path.exists(shared_dir) and path not in sys.path:
        sys.path.insert(0, path)
        break

import asyncpg
from shared.embeddings import embed_128, to_vec_literal

# OpenTelemetry tracing (optional)
try:
    from shared.otel import get_tracer
    _tracer = None  # Will be initialized on first use
except ImportError:
    get_tracer = None
    _tracer = None


async def select_topk(
    conn: asyncpg.Connection,
    query_text: str,
    platform: Optional[Sequence[str]] = None,
    k: int = 8
) -> List[Dict[str, Any]]:
    """
    Select top-k tools most similar to query text using vector similarity.
    
    Uses cosine distance (<=> operator) to find tools with embeddings closest
    to the query embedding. Results are ordered by:
    1. Vector similarity (primary)
    2. Usage count (secondary, for ties)
    3. Updated timestamp (tertiary, for freshness)
    
    Args:
        conn: Active asyncpg database connection
        query_text: User query or intent text
        platform: Optional list of platform filters (e.g., ["linux", "windows"])
                 If empty or None, returns tools for all platforms
        k: Number of results to return (default: 8)
        
    Returns:
        List of tool dictionaries with keys: key, name, short_desc, platform, tags
        
    Example:
        >>> # Find top 3 network tools for Linux
        >>> results = await select_topk(conn, "scan network", ["linux"], k=3)
        >>> len(results) <= 3
        True
        >>> all('key' in r and 'name' in r for r in results)
        True
    """
    # Get tracer for span creation
    global _tracer
    if get_tracer and _tracer is None:
        _tracer = get_tracer("selector.dao")
    
    # Create span for database operation
    if _tracer:
        with _tracer.start_as_current_span("selector.select_topk") as span:
            import time
            t0 = time.time()
            
            # Generate embedding for query
            vec = embed_128(query_text)
            vec_lit = to_vec_literal(vec)
            
            # Convert platform to list (empty list means no filter)
            plat = list(platform) if platform else []
            
            # Execute vector similarity search
            # Note: $2::text[] = '{}'::text[] checks if platform filter is empty
            #       platform && $2::text[] checks if tool's platform overlaps with filter
            rows = await conn.fetch(
                """
                WITH q AS (SELECT CAST($1 AS vector(128)) AS v)
                SELECT key, name, LEFT(short_desc,160) AS short_desc, platform, tags
                FROM tool, q
                WHERE ($2::text[] = '{}'::text[] OR platform && $2::text[])
                ORDER BY embedding <=> q.v NULLS LAST, usage_count DESC, updated_at DESC
                LIMIT $3;
                """,
                vec_lit, plat, k
            )
            
            elapsed_ms = (time.time() - t0) * 1000
            
            # Add span attributes
            span.set_attribute("db.operation", "select_topk")
            span.set_attribute("db.row_count", len(rows))
            span.set_attribute("db.elapsed_ms", round(elapsed_ms, 2))
            span.set_attribute("selector.k", k)
            span.set_attribute("selector.platforms", str(plat))
            
            # Convert asyncpg.Record objects to dicts
            return [dict(r) for r in rows]
    else:
        # No tracing available, execute without span
        # Generate embedding for query
        vec = embed_128(query_text)
        vec_lit = to_vec_literal(vec)
        
        # Convert platform to list (empty list means no filter)
        plat = list(platform) if platform else []
        
        # Execute vector similarity search
        rows = await conn.fetch(
            """
            WITH q AS (SELECT CAST($1 AS vector(128)) AS v)
            SELECT key, name, LEFT(short_desc,160) AS short_desc, platform, tags
            FROM tool, q
            WHERE ($2::text[] = '{}'::text[] OR platform && $2::text[])
            ORDER BY embedding <=> q.v NULLS LAST, usage_count DESC, updated_at DESC
            LIMIT $3;
            """,
            vec_lit, plat, k
        )
        
        # Convert asyncpg.Record objects to dicts
        return [dict(r) for r in rows]