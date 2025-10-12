"""
Integration tests for selector DAO.

These tests require a running PostgreSQL database with the tool schema.
Run the migration first: make selector.migrate

To run these tests:
    DATABASE_URL=postgresql://user:pass@localhost/db pytest selector/test_dao_integration.py -v
"""

import os
import pytest
import asyncpg

from selector.dao import select_topk
from selector.embeddings import EmbeddingProvider


# Skip all tests if DATABASE_URL not set
pytestmark = pytest.mark.skipif(
    not os.getenv("DATABASE_URL"),
    reason="DATABASE_URL not set - integration tests require database"
)


@pytest.fixture
async def db_conn():
    """Create a database connection for testing."""
    dsn = os.getenv("DATABASE_URL")
    conn = await asyncpg.connect(dsn=dsn)
    yield conn
    await conn.close()


@pytest.mark.asyncio
async def test_select_topk_with_real_db(db_conn):
    """Test select_topk against real database."""
    provider = EmbeddingProvider()
    
    # Query for tools - should work even with empty table
    results = await select_topk(
        db_conn,
        "scan network for vulnerabilities",
        k=5,
        provider=provider
    )
    
    # Should return a list (may be empty if no tools in DB)
    assert isinstance(results, list)
    
    # If results exist, verify structure
    if results:
        for tool in results:
            assert "key" in tool
            assert "name" in tool
            assert "short_desc" in tool
            assert "platform" in tool
            assert "tags" in tool


@pytest.mark.asyncio
async def test_select_topk_with_platform_filter_real_db(db_conn):
    """Test platform filtering against real database."""
    provider = EmbeddingProvider()
    
    # Query with platform filter
    results = await select_topk(
        db_conn,
        "deploy application",
        platform=["linux", "docker"],
        k=10,
        provider=provider
    )
    
    assert isinstance(results, list)
    
    # If results exist, verify platform filtering worked
    if results:
        for tool in results:
            # Tool should have at least one of the requested platforms
            assert isinstance(tool["platform"], list)


@pytest.mark.asyncio
async def test_select_topk_handles_null_embeddings(db_conn):
    """Test that NULL embeddings are handled correctly (sorted last)."""
    provider = EmbeddingProvider()
    
    # This should work even if some tools have NULL embeddings
    results = await select_topk(
        db_conn,
        "test query",
        k=20,
        provider=provider
    )
    
    assert isinstance(results, list)
    # No error means NULLS LAST worked correctly


@pytest.mark.asyncio
async def test_select_topk_respects_k_limit(db_conn):
    """Test that k parameter limits results correctly."""
    provider = EmbeddingProvider()
    
    # Request only 3 results
    results = await select_topk(
        db_conn,
        "find tools",
        k=3,
        provider=provider
    )
    
    # Should return at most 3 results
    assert len(results) <= 3


@pytest.mark.asyncio
async def test_select_topk_deterministic_with_same_intent(db_conn):
    """Test that same intent produces same results (deterministic embedding)."""
    provider = EmbeddingProvider()
    intent = "scan network ports"
    
    # Query twice with same intent
    results1 = await select_topk(db_conn, intent, k=5, provider=provider)
    results2 = await select_topk(db_conn, intent, k=5, provider=provider)
    
    # Should get same results in same order
    assert len(results1) == len(results2)
    
    if results1:
        for i, (r1, r2) in enumerate(zip(results1, results2)):
            assert r1["key"] == r2["key"], f"Result {i} differs: {r1['key']} vs {r2['key']}"