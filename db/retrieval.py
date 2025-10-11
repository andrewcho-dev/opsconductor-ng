"""Tool retrieval using pgvector semantic search."""

from typing import List, Optional

import asyncpg
from pydantic import BaseModel


class ToolStub(BaseModel):
    """Minimal tool information for LLM consumption."""
    
    id: int
    tool_name: str
    description: str
    platform: str
    category: str
    similarity: Optional[float] = None


async def search_tools(
    conn: asyncpg.Connection,
    query_embedding: List[float],
    top_k: int = 50,
    platform: Optional[str] = None,
) -> List[ToolStub]:
    """Search for tools using semantic similarity.
    
    Args:
        conn: Database connection
        query_embedding: Query embedding vector
        top_k: Number of results to return (default: 50)
        platform: Optional platform filter (windows, linux, both, etc.)
        
    Returns:
        List of ToolStub objects ordered by similarity (most similar first)
    """
    # Build query with optional platform filter
    if platform:
        query = """
            SELECT 
                t.id,
                t.tool_name,
                t.description,
                t.platform,
                t.category,
                (te.embedding <=> $1::vector) as distance
            FROM tool_catalog.tools t
            INNER JOIN tool_catalog.tool_embeddings te ON t.id = te.tool_id
            WHERE t.enabled = true 
                AND t.is_latest = true
                AND t.platform = $3
            ORDER BY te.embedding <=> $1::vector
            LIMIT $2
        """
        rows = await conn.fetch(query, query_embedding, top_k, platform)
    else:
        query = """
            SELECT 
                t.id,
                t.tool_name,
                t.description,
                t.platform,
                t.category,
                (te.embedding <=> $1::vector) as distance
            FROM tool_catalog.tools t
            INNER JOIN tool_catalog.tool_embeddings te ON t.id = te.tool_id
            WHERE t.enabled = true 
                AND t.is_latest = true
            ORDER BY te.embedding <=> $1::vector
            LIMIT $2
        """
        rows = await conn.fetch(query, query_embedding, top_k)
    
    # Convert to ToolStub objects
    # Note: cosine distance is 0-2, where 0 = identical, 2 = opposite
    # Convert to similarity score: 1 - (distance / 2)
    results = []
    for row in rows:
        similarity = 1.0 - (row['distance'] / 2.0)
        results.append(ToolStub(
            id=row['id'],
            tool_name=row['tool_name'],
            description=row['description'] or '',
            platform=row['platform'] or '',
            category=row['category'] or '',
            similarity=similarity,
        ))
    
    return results