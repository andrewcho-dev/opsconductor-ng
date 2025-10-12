"""
Unit tests for selector DAO.

Tests the select_topk function with various inputs and edge cases.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock
from selector.dao import select_topk


@pytest.mark.asyncio
async def test_select_topk_basic():
    """Test basic select_topk functionality."""
    # Mock connection
    conn = AsyncMock()
    conn.fetch = AsyncMock(return_value=[
        {
            'key': 'nmap_scan',
            'name': 'Nmap Network Scanner',
            'short_desc': 'Scan network for open ports',
            'platform': ['linux'],
            'tags': ['network', 'security']
        }
    ])
    
    # Execute query
    results = await select_topk(conn, "scan network", platform=["linux"], k=5)
    
    # Verify results
    assert len(results) == 1
    assert results[0]['key'] == 'nmap_scan'
    assert 'name' in results[0]
    assert 'short_desc' in results[0]
    assert 'platform' in results[0]
    assert 'tags' in results[0]
    
    # Verify SQL was called
    conn.fetch.assert_called_once()
    call_args = conn.fetch.call_args[0]
    assert 'vector(128)' in call_args[0]  # SQL query
    assert call_args[2] == ['linux']  # platform filter
    assert call_args[3] == 5  # k value


@pytest.mark.asyncio
async def test_select_topk_no_platform_filter():
    """Test select_topk without platform filter."""
    conn = AsyncMock()
    conn.fetch = AsyncMock(return_value=[])
    
    results = await select_topk(conn, "test query", platform=None, k=3)
    
    assert results == []
    conn.fetch.assert_called_once()
    call_args = conn.fetch.call_args[0]
    assert call_args[2] == []  # empty platform list


@pytest.mark.asyncio
async def test_select_topk_k_bounds():
    """Test that k parameter is passed correctly."""
    conn = AsyncMock()
    conn.fetch = AsyncMock(return_value=[])
    
    # Test k=1
    await select_topk(conn, "query", k=1)
    assert conn.fetch.call_args[0][3] == 1
    
    # Test k=20
    await select_topk(conn, "query", k=20)
    assert conn.fetch.call_args[0][3] == 20


@pytest.mark.asyncio
async def test_select_topk_multiple_platforms():
    """Test select_topk with multiple platform filters."""
    conn = AsyncMock()
    conn.fetch = AsyncMock(return_value=[])
    
    results = await select_topk(conn, "query", platform=["linux", "windows"], k=5)
    
    call_args = conn.fetch.call_args[0]
    assert call_args[2] == ["linux", "windows"]


@pytest.mark.asyncio
async def test_select_topk_embedding_generation():
    """Test that embeddings are generated correctly."""
    conn = AsyncMock()
    conn.fetch = AsyncMock(return_value=[])
    
    await select_topk(conn, "test query", k=5)
    
    # Verify that a vector literal was passed (starts with '[' and ends with ']')
    call_args = conn.fetch.call_args[0]
    vec_literal = call_args[1]
    assert isinstance(vec_literal, str)
    assert vec_literal.startswith('[')
    assert vec_literal.endswith(']')
    # Should have 127 commas for 128 values
    assert vec_literal.count(',') == 127


if __name__ == "__main__":
    pytest.main([__file__, "-v"])