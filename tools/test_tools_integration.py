#!/usr/bin/env python3
"""
Integration tests for tools_upsert.py

Tests the complete workflow with a real database.
Requires DATABASE_URL environment variable.
"""

import asyncio
import os
import sys
from pathlib import Path

import pytest

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

# Skip all tests if DATABASE_URL not set
pytestmark = pytest.mark.skipif(
    not os.getenv('DATABASE_URL'),
    reason="DATABASE_URL not set"
)


@pytest.mark.asyncio
async def test_full_workflow():
    """Test complete workflow: load YAML -> generate embeddings -> upsert."""
    import asyncpg
    from tools.tools_upsert import load_yaml_tool, upsert_tool
    from selector.embeddings import EmbeddingProvider
    
    # Connect to database
    conn = await asyncpg.connect(dsn=os.getenv('DATABASE_URL'))
    
    try:
        # Ensure table exists
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS tool (
              id BIGSERIAL PRIMARY KEY,
              key TEXT UNIQUE NOT NULL,
              name TEXT NOT NULL,
              short_desc TEXT NOT NULL,
              platform TEXT[] DEFAULT '{}'::TEXT[],
              tags TEXT[] DEFAULT '{}'::TEXT[],
              meta JSONB DEFAULT '{}'::JSONB,
              embedding VECTOR(128),
              usage_count INTEGER DEFAULT 0,
              updated_at TIMESTAMPTZ DEFAULT now()
            )
        """)
        
        # Load a test tool
        tool_path = "config/tools/linux/grep.yaml"
        if not Path(tool_path).exists():
            pytest.skip(f"Test tool not found: {tool_path}")
        
        tool = await load_yaml_tool(tool_path)
        assert tool is not None, "Failed to load test tool"
        
        # Initialize embedding provider
        provider = EmbeddingProvider()
        
        # Upsert the tool
        result = await upsert_tool(conn, tool, provider, dry_run=False)
        assert result is True, "Upsert failed"
        
        # Verify tool was inserted
        row = await conn.fetchrow(
            "SELECT key, name, short_desc, platform, tags, meta, embedding FROM tool WHERE key = $1",
            tool['key']
        )
        
        assert row is not None, "Tool not found in database"
        assert row['key'] == tool['key']
        assert row['name'] == tool['name']
        assert row['short_desc'] == tool['short_desc']
        assert list(row['platform']) == tool['platform']
        assert list(row['tags']) == tool['tags']
        assert dict(row['meta']) == tool['meta']
        assert row['embedding'] is not None
        assert len(row['embedding']) == 128
        
        # Test idempotency - upsert again
        result2 = await upsert_tool(conn, tool, provider, dry_run=False)
        assert result2 is True, "Second upsert failed"
        
        # Verify still only one row
        count = await conn.fetchval(
            "SELECT COUNT(*) FROM tool WHERE key = $1",
            tool['key']
        )
        assert count == 1, "Duplicate tool created"
        
        # Test update - modify tool and upsert again
        tool['name'] = "Updated Tool Name"
        result3 = await upsert_tool(conn, tool, provider, dry_run=False)
        assert result3 is True, "Update upsert failed"
        
        # Verify name was updated
        updated_row = await conn.fetchrow(
            "SELECT name FROM tool WHERE key = $1",
            tool['key']
        )
        assert updated_row['name'] == "Updated Tool Name"
        
        # Cleanup
        await conn.execute("DELETE FROM tool WHERE key = $1", tool['key'])
        
    finally:
        await conn.close()


@pytest.mark.asyncio
async def test_multiple_tools_upsert():
    """Test upserting multiple tools."""
    import asyncpg
    from tools.tools_upsert import load_yaml_tool, upsert_tool
    from selector.embeddings import EmbeddingProvider
    
    conn = await asyncpg.connect(dsn=os.getenv('DATABASE_URL'))
    
    try:
        # Ensure table exists
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS tool (
              id BIGSERIAL PRIMARY KEY,
              key TEXT UNIQUE NOT NULL,
              name TEXT NOT NULL,
              short_desc TEXT NOT NULL,
              platform TEXT[] DEFAULT '{}'::TEXT[],
              tags TEXT[] DEFAULT '{}'::TEXT[],
              meta JSONB DEFAULT '{}'::JSONB,
              embedding VECTOR(128),
              usage_count INTEGER DEFAULT 0,
              updated_at TIMESTAMPTZ DEFAULT now()
            )
        """)
        
        # Load multiple tools
        tool_paths = [
            "config/tools/linux/grep.yaml",
            "config/tools/windows/powershell.yaml"
        ]
        
        tools = []
        for path in tool_paths:
            if Path(path).exists():
                tool = await load_yaml_tool(path)
                if tool:
                    tools.append(tool)
        
        if not tools:
            pytest.skip("No test tools found")
        
        # Initialize embedding provider
        provider = EmbeddingProvider()
        
        # Upsert all tools
        for tool in tools:
            result = await upsert_tool(conn, tool, provider, dry_run=False)
            assert result is True, f"Failed to upsert {tool['key']}"
        
        # Verify all tools were inserted
        for tool in tools:
            row = await conn.fetchrow(
                "SELECT key FROM tool WHERE key = $1",
                tool['key']
            )
            assert row is not None, f"Tool {tool['key']} not found"
        
        # Cleanup
        for tool in tools:
            await conn.execute("DELETE FROM tool WHERE key = $1", tool['key'])
        
    finally:
        await conn.close()


@pytest.mark.asyncio
async def test_embedding_similarity():
    """Test that similar tools have similar embeddings."""
    import asyncpg
    from tools.tools_upsert import load_yaml_tool, upsert_tool
    from selector.embeddings import EmbeddingProvider
    
    conn = await asyncpg.connect(dsn=os.getenv('DATABASE_URL'))
    
    try:
        # Ensure table exists
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS tool (
              id BIGSERIAL PRIMARY KEY,
              key TEXT UNIQUE NOT NULL,
              name TEXT NOT NULL,
              short_desc TEXT NOT NULL,
              platform TEXT[] DEFAULT '{}'::TEXT[],
              tags TEXT[] DEFAULT '{}'::TEXT[],
              meta JSONB DEFAULT '{}'::JSONB,
              embedding VECTOR(128),
              usage_count INTEGER DEFAULT 0,
              updated_at TIMESTAMPTZ DEFAULT now()
            )
        """)
        
        # Create two similar tools
        provider = EmbeddingProvider()
        
        tool1 = {
            'key': 'test.network1',
            'name': 'Network Tool 1',
            'short_desc': 'Display network connections and statistics.',
            'platform': ['linux'],
            'tags': ['network'],
            'meta': {}
        }
        
        tool2 = {
            'key': 'test.network2',
            'name': 'Network Tool 2',
            'short_desc': 'Show network connections and interface info.',
            'platform': ['linux'],
            'tags': ['network'],
            'meta': {}
        }
        
        # Upsert both tools
        await upsert_tool(conn, tool1, provider, dry_run=False)
        await upsert_tool(conn, tool2, provider, dry_run=False)
        
        # Calculate cosine distance between embeddings
        distance = await conn.fetchval("""
            SELECT 
                t1.embedding <=> t2.embedding AS distance
            FROM tool t1, tool t2
            WHERE t1.key = $1 AND t2.key = $2
        """, tool1['key'], tool2['key'])
        
        # Similar tools should have small distance (< 0.5)
        assert distance is not None
        assert distance < 0.5, f"Distance too large: {distance}"
        
        # Cleanup
        await conn.execute("DELETE FROM tool WHERE key IN ($1, $2)", tool1['key'], tool2['key'])
        
    finally:
        await conn.close()


if __name__ == '__main__':
    pytest.main([__file__, '-v'])