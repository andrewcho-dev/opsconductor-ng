#!/usr/bin/env python3
"""Backfill tool embeddings for semantic search.

This script:
1. Reads all enabled tools from tool_catalog.tools
2. Generates embeddings using configured provider/model
3. UPSERTs embeddings into tool_catalog.tool_embeddings

Environment variables:
- EMBEDDING_PROVIDER: openai, huggingface, local (default: openai)
- EMBEDDING_MODEL: model name (default: text-embedding-3-small)
- EMBEDDING_API_KEY: API key for provider (required for openai)
- EMBEDDING_DIMENSION: vector dimension (default: 768)
- DATABASE_URL: PostgreSQL connection string
"""

import asyncio
import os
import sys
from typing import List, Optional

import asyncpg
from shared.logging import json_log


# Configuration from environment
EMBEDDING_PROVIDER = os.getenv("EMBEDDING_PROVIDER", "openai")
EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "text-embedding-3-small")
EMBEDDING_API_KEY = os.getenv("EMBEDDING_API_KEY", "")
EMBEDDING_DIMENSION = int(os.getenv("EMBEDDING_DIMENSION", "768"))
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://opsconductor:opsconductor@localhost:5432/opsconductor")


async def get_embedding(text: str) -> Optional[List[float]]:
    """Generate embedding for text using configured provider.
    
    Args:
        text: Text to embed
        
    Returns:
        List of floats representing the embedding vector, or None on error
    """
    if EMBEDDING_PROVIDER == "openai":
        return await get_openai_embedding(text)
    elif EMBEDDING_PROVIDER == "huggingface":
        return await get_huggingface_embedding(text)
    elif EMBEDDING_PROVIDER == "local":
        return await get_local_embedding(text)
    else:
        json_log(f"Unknown embedding provider: {EMBEDDING_PROVIDER}", level="ERROR")
        return None


async def get_openai_embedding(text: str) -> Optional[List[float]]:
    """Get embedding from OpenAI API.
    
    Args:
        text: Text to embed
        
    Returns:
        Embedding vector or None on error
    """
    try:
        import httpx
        
        if not EMBEDDING_API_KEY:
            json_log("EMBEDDING_API_KEY not set for OpenAI provider", level="ERROR")
            return None
        
        async with httpx.AsyncClient() as client:
            response = await client.post(
                "https://api.openai.com/v1/embeddings",
                headers={
                    "Authorization": f"Bearer {EMBEDDING_API_KEY}",
                    "Content-Type": "application/json",
                },
                json={
                    "input": text,
                    "model": EMBEDDING_MODEL,
                },
                timeout=30.0,
            )
            response.raise_for_status()
            data = response.json()
            return data["data"][0]["embedding"]
    except Exception as e:
        json_log(f"Error getting OpenAI embedding: {e}", level="ERROR")
        return None


async def get_huggingface_embedding(text: str) -> Optional[List[float]]:
    """Get embedding from HuggingFace API.
    
    Args:
        text: Text to embed
        
    Returns:
        Embedding vector or None on error
    """
    try:
        import httpx
        
        if not EMBEDDING_API_KEY:
            json_log("EMBEDDING_API_KEY not set for HuggingFace provider", level="ERROR")
            return None
        
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"https://api-inference.huggingface.co/pipeline/feature-extraction/{EMBEDDING_MODEL}",
                headers={
                    "Authorization": f"Bearer {EMBEDDING_API_KEY}",
                },
                json={"inputs": text},
                timeout=30.0,
            )
            response.raise_for_status()
            # HuggingFace returns a list of embeddings, take the first one
            embeddings = response.json()
            if isinstance(embeddings, list) and len(embeddings) > 0:
                return embeddings[0]
            return None
    except Exception as e:
        json_log(f"Error getting HuggingFace embedding: {e}", level="ERROR")
        return None


async def get_local_embedding(text: str) -> Optional[List[float]]:
    """Get embedding from local model using sentence-transformers.
    
    Args:
        text: Text to embed
        
    Returns:
        Embedding vector or None on error
    """
    try:
        from sentence_transformers import SentenceTransformer
        
        # Load model (cached after first load)
        model = SentenceTransformer(EMBEDDING_MODEL)
        embedding = model.encode(text, convert_to_numpy=True)
        return embedding.tolist()
    except ImportError:
        json_log("sentence-transformers not installed. Install with: pip install sentence-transformers", level="ERROR")
        return None
    except Exception as e:
        json_log(f"Error getting local embedding: {e}", level="ERROR")
        return None


async def backfill_embeddings():
    """Backfill embeddings for all enabled tools."""
    json_log("Starting tool embeddings backfill", 
             provider=EMBEDDING_PROVIDER, 
             model=EMBEDDING_MODEL,
             dimension=EMBEDDING_DIMENSION)
    
    # Connect to database
    try:
        conn = await asyncpg.connect(DATABASE_URL)
        json_log("Connected to database")
    except Exception as e:
        json_log(f"Failed to connect to database: {e}", level="ERROR")
        return 1
    
    try:
        # Get all enabled tools
        tools = await conn.fetch("""
            SELECT id, tool_name, description, platform, category
            FROM tool_catalog.tools
            WHERE enabled = true AND is_latest = true
            ORDER BY id
        """)
        
        json_log(f"Found {len(tools)} enabled tools to process")
        
        processed = 0
        skipped = 0
        errors = 0
        
        for tool in tools:
            tool_id = tool['id']
            tool_name = tool['tool_name']
            
            # Create embedding text from tool metadata
            embedding_text = f"{tool_name} {tool['description'] or ''} {tool['platform'] or ''} {tool['category'] or ''}"
            
            json_log(f"Processing tool: {tool_name}", tool_id=tool_id)
            
            # Generate embedding
            embedding = await get_embedding(embedding_text)
            
            if embedding is None:
                json_log(f"Failed to generate embedding for tool: {tool_name}", 
                        tool_id=tool_id, level="ERROR")
                errors += 1
                continue
            
            # Validate embedding dimension
            if len(embedding) != EMBEDDING_DIMENSION:
                json_log(f"Embedding dimension mismatch: expected {EMBEDDING_DIMENSION}, got {len(embedding)}", 
                        tool_id=tool_id, level="ERROR")
                errors += 1
                continue
            
            # UPSERT embedding
            try:
                await conn.execute("""
                    INSERT INTO tool_catalog.tool_embeddings (tool_id, embedding, embedding_model, embedding_provider)
                    VALUES ($1, $2, $3, $4)
                    ON CONFLICT (tool_id) 
                    DO UPDATE SET 
                        embedding = EXCLUDED.embedding,
                        embedding_model = EXCLUDED.embedding_model,
                        embedding_provider = EXCLUDED.embedding_provider,
                        updated_at = now()
                """, tool_id, embedding, EMBEDDING_MODEL, EMBEDDING_PROVIDER)
                
                processed += 1
                json_log(f"Upserted embedding for tool: {tool_name}", tool_id=tool_id)
            except Exception as e:
                json_log(f"Failed to upsert embedding for tool: {tool_name}: {e}", 
                        tool_id=tool_id, level="ERROR")
                errors += 1
        
        # Run ANALYZE to update statistics
        await conn.execute("ANALYZE tool_catalog.tool_embeddings")
        
        json_log("Backfill complete", 
                processed=processed, 
                skipped=skipped, 
                errors=errors,
                total=len(tools))
        
        return 0 if errors == 0 else 1
        
    finally:
        await conn.close()


if __name__ == "__main__":
    exit_code = asyncio.run(backfill_embeddings())
    sys.exit(exit_code)