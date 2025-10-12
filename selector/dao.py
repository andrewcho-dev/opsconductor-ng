"""
Database access layer for tool selection using pgvector semantic search.

This module provides low-level asyncpg-based queries for retrieving tools
from the database using vector similarity search with optional platform filtering.
"""

from typing import Optional
import asyncpg

from selector.embeddings import EmbeddingProvider, embed_intent


def _vec_literal(vec: list[float]) -> str:
    """
    Convert a Python list of floats to a PostgreSQL vector literal string.
    
    Args:
        vec: List of float values representing an embedding vector
        
    Returns:
        String in format '[0.123, 0.456, ...]' suitable for CAST to vector type
        
    Example:
        >>> _vec_literal([0.1, 0.2, 0.3])
        '[0.1,0.2,0.3]'
    """
    return "[" + ",".join(str(x) for x in vec) + "]"


async def select_topk(
    conn: asyncpg.Connection,
    intent: str,
    platform: Optional[list[str]] = None,
    k: int = 8,
    provider: Optional[EmbeddingProvider] = None,
) -> list[dict]:
    """
    Select top-k tools using vector similarity search with optional platform filtering.
    
    This function:
    1. Embeds the user intent using the provided or default EmbeddingProvider
    2. Queries the tool table using pgvector cosine distance (<=> operator)
    3. Applies platform filtering if specified (array overlap with &&)
    4. Handles NULL embeddings (sorts them last via NULLS LAST)
    5. Uses tie-breakers: usage_count DESC, updated_at DESC
    
    Args:
        conn: Active asyncpg database connection
        intent: User intent text to embed and search for
        platform: Optional list of platform names to filter by (e.g., ['linux', 'docker'])
                 If None or empty list, no platform filtering is applied
        k: Maximum number of results to return (default: 8)
        provider: Optional EmbeddingProvider instance. If None, creates default provider
        
    Returns:
        List of dictionaries with keys: key, name, short_desc, platform, tags
        Sorted by vector similarity (closest first), then usage_count, then updated_at
        
    Example:
        >>> conn = await asyncpg.connect(dsn=DATABASE_URL)
        >>> results = await select_topk(conn, "scan network for vulnerabilities", platform=["linux"], k=5)
        >>> for tool in results:
        ...     print(f"{tool['key']}: {tool['short_desc']}")
    """
    # Step 1: Embed the intent
    if provider is None:
        provider = EmbeddingProvider()
    
    vec = await embed_intent(provider, intent)
    vec_str = _vec_literal(vec)
    
    # Step 2: Prepare platform filter parameter
    # PostgreSQL array literal: empty array if no filter, otherwise the platform list
    platform_param = platform if platform else []
    
    # Step 3: Execute query with pgvector similarity search
    sql = """
        WITH q AS (SELECT CAST($1 AS vector(128)) AS v)
        SELECT 
            key,
            name,
            LEFT(short_desc, 160) AS short_desc,
            platform,
            tags
        FROM tool, q
        WHERE ($2::text[] = '{}'::text[] OR platform && $2::text[])
        ORDER BY embedding <=> q.v NULLS LAST, usage_count DESC, updated_at DESC
        LIMIT $3
    """
    
    rows = await conn.fetch(sql, vec_str, platform_param, k)
    
    # Step 4: Convert asyncpg.Record objects to dictionaries
    results = []
    for row in rows:
        results.append({
            "key": row["key"],
            "name": row["name"],
            "short_desc": row["short_desc"],
            "platform": row["platform"],
            "tags": row["tags"],
        })
    
    return results