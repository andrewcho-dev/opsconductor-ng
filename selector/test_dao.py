"""Tests for selector DAO functions."""

import pytest
from unittest.mock import AsyncMock, MagicMock
from selector.dao import _vec_literal, select_topk
from selector.embeddings import EmbeddingProvider


def test_vec_literal():
    """Test vector literal string formatting."""
    vec = [0.1, 0.2, 0.3]
    result = _vec_literal(vec)
    assert result == "[0.1,0.2,0.3]"
    
    # Test with negative values
    vec2 = [-0.5, 0.0, 0.5]
    result2 = _vec_literal(vec2)
    assert result2 == "[-0.5,0.0,0.5]"
    
    # Test with many values
    vec3 = [float(i) for i in range(128)]
    result3 = _vec_literal(vec3)
    assert result3.startswith("[0.0,1.0,2.0")
    assert result3.endswith("127.0]")
    assert result3.count(",") == 127  # 128 values = 127 commas


@pytest.mark.asyncio
async def test_select_topk_basic():
    """Test select_topk with basic parameters."""
    # Create mock connection
    mock_conn = AsyncMock()
    
    # Mock the fetch result - need to mock __getitem__ for dict-like access
    mock_row = MagicMock()
    mock_row.__getitem__ = lambda self, key: {
        "key": "nmap",
        "name": "Network Mapper",
        "short_desc": "Network scanning tool",
        "platform": ["linux", "docker"],
        "tags": ["network", "security"],
    }[key]
    mock_conn.fetch.return_value = [mock_row]
    
    # Create provider (will use deterministic fallback)
    provider = EmbeddingProvider()
    
    # Call select_topk
    results = await select_topk(mock_conn, "scan network", k=5, provider=provider)
    
    # Verify fetch was called
    assert mock_conn.fetch.called
    call_args = mock_conn.fetch.call_args
    
    # Check SQL structure
    sql = call_args[0][0]
    assert "WITH q AS (SELECT CAST($1 AS vector(128)) AS v)" in sql
    assert "embedding <=> q.v NULLS LAST" in sql
    assert "usage_count DESC" in sql
    assert "updated_at DESC" in sql
    assert "LIMIT $3" in sql
    
    # Check parameters
    vec_param = call_args[0][1]
    assert vec_param.startswith("[")
    assert vec_param.endswith("]")
    
    platform_param = call_args[0][2]
    assert platform_param == []  # No platform filter
    
    k_param = call_args[0][3]
    assert k_param == 5
    
    # Check results
    assert len(results) == 1
    assert results[0]["key"] == "nmap"
    assert results[0]["name"] == "Network Mapper"


@pytest.mark.asyncio
async def test_select_topk_with_platform_filter():
    """Test select_topk with platform filtering."""
    mock_conn = AsyncMock()
    mock_conn.fetch.return_value = []
    
    provider = EmbeddingProvider()
    
    # Call with platform filter
    await select_topk(
        mock_conn,
        "deploy application",
        platform=["linux", "docker"],
        k=10,
        provider=provider
    )
    
    # Verify platform parameter was passed
    call_args = mock_conn.fetch.call_args
    platform_param = call_args[0][2]
    assert platform_param == ["linux", "docker"]


@pytest.mark.asyncio
async def test_select_topk_default_provider():
    """Test select_topk creates default provider when none provided."""
    mock_conn = AsyncMock()
    mock_conn.fetch.return_value = []
    
    # Call without provider
    results = await select_topk(mock_conn, "test intent", k=3)
    
    # Should complete without error
    assert results == []
    assert mock_conn.fetch.called


@pytest.mark.asyncio
async def test_select_topk_multiple_results():
    """Test select_topk with multiple results."""
    mock_conn = AsyncMock()
    
    # Mock multiple rows - need proper dict-like access
    def make_mock_row(data):
        mock = MagicMock()
        mock.__getitem__ = lambda self, key: data[key]
        return mock
    
    mock_rows = [
        make_mock_row({
            "key": "tool1",
            "name": "Tool One",
            "short_desc": "First tool",
            "platform": ["linux"],
            "tags": ["tag1"],
        }),
        make_mock_row({
            "key": "tool2",
            "name": "Tool Two",
            "short_desc": "Second tool",
            "platform": ["docker"],
            "tags": ["tag2"],
        }),
        make_mock_row({
            "key": "tool3",
            "name": "Tool Three",
            "short_desc": "Third tool",
            "platform": ["linux", "docker"],
            "tags": ["tag1", "tag2"],
        }),
    ]
    mock_conn.fetch.return_value = mock_rows
    
    provider = EmbeddingProvider()
    results = await select_topk(mock_conn, "find tools", k=10, provider=provider)
    
    # Check all results returned
    assert len(results) == 3
    assert results[0]["key"] == "tool1"
    assert results[1]["key"] == "tool2"
    assert results[2]["key"] == "tool3"


@pytest.mark.asyncio
async def test_select_topk_empty_platform_list():
    """Test that empty platform list is treated as no filter."""
    mock_conn = AsyncMock()
    mock_conn.fetch.return_value = []
    
    provider = EmbeddingProvider()
    
    # Call with empty platform list
    await select_topk(mock_conn, "test", platform=[], k=5, provider=provider)
    
    # Verify empty array was passed (no filter)
    call_args = mock_conn.fetch.call_args
    platform_param = call_args[0][2]
    assert platform_param == []


@pytest.mark.asyncio
async def test_select_topk_short_desc_truncation():
    """Test that short_desc is truncated to 160 chars in SQL."""
    mock_conn = AsyncMock()
    
    # Mock row with long description
    long_desc = "x" * 200
    mock_row = MagicMock()
    mock_row.__getitem__ = lambda self, key: {
        "key": "tool",
        "name": "Tool",
        "short_desc": long_desc[:160],  # SQL will truncate
        "platform": [],
        "tags": [],
    }[key]
    mock_conn.fetch.return_value = [mock_row]
    
    provider = EmbeddingProvider()
    results = await select_topk(mock_conn, "test", k=1, provider=provider)
    
    # Verify SQL has LEFT(short_desc, 160)
    call_args = mock_conn.fetch.call_args
    sql = call_args[0][0]
    assert "LEFT(short_desc, 160)" in sql
    
    # Result should have truncated description
    assert len(results[0]["short_desc"]) <= 160