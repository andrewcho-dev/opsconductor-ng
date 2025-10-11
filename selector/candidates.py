"""Candidate tool generation from user intent."""

import os
from typing import List, Optional

import asyncpg
import db.retrieval
from db.retrieval import ToolStub
from shared.logging import json_log


# Always-include tools from environment (comma-separated tool names)
ALWAYS_INCLUDE_TOOLS = os.getenv("ALWAYS_INCLUDE_TOOLS", "").split(",")
ALWAYS_INCLUDE_TOOLS = [t.strip() for t in ALWAYS_INCLUDE_TOOLS if t.strip()]


async def get_embedding_for_text(text: str) -> Optional[List[float]]:
    """Generate embedding for user intent text.
    
    This is a placeholder that should be replaced with actual embedding generation.
    For now, it returns None to indicate embedding generation is not implemented.
    
    Args:
        text: User intent text
        
    Returns:
        Embedding vector or None
    """
    # TODO: Implement actual embedding generation
    # This should use the same provider/model as backfill_tool_embeddings.py
    json_log("Embedding generation not implemented yet", level="WARNING")
    return None


async def get_always_include_tools(conn: asyncpg.Connection) -> List[ToolStub]:
    """Get tools that should always be included in candidates.
    
    Args:
        conn: Database connection
        
    Returns:
        List of ToolStub objects for always-include tools
    """
    if not ALWAYS_INCLUDE_TOOLS:
        return []
    
    query = """
        SELECT 
            id,
            tool_name,
            description,
            platform,
            category
        FROM tool_catalog.tools
        WHERE tool_name = ANY($1)
            AND enabled = true
            AND is_latest = true
    """
    
    rows = await conn.fetch(query, ALWAYS_INCLUDE_TOOLS)
    
    return [
        ToolStub(
            id=row['id'],
            tool_name=row['tool_name'],
            description=row['description'] or '',
            platform=row['platform'] or '',
            category=row['category'] or '',
        )
        for row in rows
    ]


async def candidate_tools_from_intent(
    conn: asyncpg.Connection,
    text: str,
    k: int = 50,
    platform: Optional[str] = None,
) -> List[ToolStub]:
    """Get candidate tools for user intent using semantic search.
    
    Args:
        conn: Database connection
        text: User intent text
        k: Number of candidates to return (default: 50)
        platform: Optional platform filter
        
    Returns:
        List of ToolStub objects (minimal tool information)
    """
    json_log("Getting candidate tools from intent", 
             intent_length=len(text), 
             top_k=k, 
             platform=platform)
    
    # Get embedding for user intent
    query_embedding = await get_embedding_for_text(text)
    
    # If embedding generation fails, fall back to always-include tools only
    if query_embedding is None:
        json_log("Falling back to always-include tools only", level="WARNING")
        always_include = await get_always_include_tools(conn)
        return always_include[:k]
    
    # Search for similar tools
    candidates = await db.retrieval.search_tools(conn, query_embedding, top_k=k, platform=platform)
    
    # Add always-include tools if not already present
    always_include = await get_always_include_tools(conn)
    candidate_names = {c.tool_name for c in candidates}
    
    for tool in always_include:
        if tool.tool_name not in candidate_names:
            candidates.append(tool)
    
    # Limit to k results
    candidates = candidates[:k]
    
    json_log("Retrieved candidate tools", 
             count=len(candidates),
             always_included=len([t for t in candidates if t.tool_name in ALWAYS_INCLUDE_TOOLS]))
    
    return candidates