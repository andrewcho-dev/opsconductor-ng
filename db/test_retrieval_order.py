"""Unit tests for tool retrieval ordering.

These tests use tiny mock vectors to verify retrieval logic without requiring
a full PostgreSQL instance with pgvector.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock
from db.retrieval import search_tools, ToolStub


@pytest.mark.asyncio
async def test_search_tools_returns_ordered_results():
    """Test that search_tools returns results ordered by similarity."""
    # Mock database connection
    mock_conn = AsyncMock()
    
    # Mock query results (ordered by distance: lower = more similar)
    mock_conn.fetch.return_value = [
        {
            'id': 1,
            'tool_name': 'tool_a',
            'description': 'Most similar tool',
            'platform': 'linux',
            'category': 'system',
            'distance': 0.1,  # Very similar
        },
        {
            'id': 2,
            'tool_name': 'tool_b',
            'description': 'Moderately similar tool',
            'platform': 'windows',
            'category': 'network',
            'distance': 0.5,  # Moderately similar
        },
        {
            'id': 3,
            'tool_name': 'tool_c',
            'description': 'Least similar tool',
            'platform': 'both',
            'category': 'database',
            'distance': 1.0,  # Less similar
        },
    ]
    
    # Query embedding (doesn't matter for mock)
    query_embedding = [0.1] * 768
    
    # Execute search
    results = await search_tools(mock_conn, query_embedding, top_k=3)
    
    # Verify results
    assert len(results) == 3
    assert all(isinstance(r, ToolStub) for r in results)
    
    # Verify ordering (most similar first)
    assert results[0].tool_name == 'tool_a'
    assert results[1].tool_name == 'tool_b'
    assert results[2].tool_name == 'tool_c'
    
    # Verify similarity scores (higher = more similar)
    assert results[0].similarity > results[1].similarity
    assert results[1].similarity > results[2].similarity
    
    # Verify similarity calculation (1 - distance/2)
    assert abs(results[0].similarity - 0.95) < 0.01  # 1 - 0.1/2 = 0.95
    assert abs(results[1].similarity - 0.75) < 0.01  # 1 - 0.5/2 = 0.75
    assert abs(results[2].similarity - 0.50) < 0.01  # 1 - 1.0/2 = 0.50


@pytest.mark.asyncio
async def test_search_tools_with_platform_filter():
    """Test that platform filter is applied correctly."""
    mock_conn = AsyncMock()
    
    mock_conn.fetch.return_value = [
        {
            'id': 1,
            'tool_name': 'linux_tool',
            'description': 'Linux-specific tool',
            'platform': 'linux',
            'category': 'system',
            'distance': 0.2,
        },
    ]
    
    query_embedding = [0.1] * 768
    
    # Execute search with platform filter
    results = await search_tools(mock_conn, query_embedding, top_k=10, platform='linux')
    
    # Verify platform filter was used in query
    mock_conn.fetch.assert_called_once()
    call_args = mock_conn.fetch.call_args
    
    # Verify the query includes platform filter
    query_sql = call_args[0][0]
    assert 'platform = $3' in query_sql
    
    # Verify platform parameter was passed
    assert call_args[0][3] == 'linux'


@pytest.mark.asyncio
async def test_search_tools_respects_top_k():
    """Test that top_k parameter limits results."""
    mock_conn = AsyncMock()
    
    # Return more results than requested
    mock_conn.fetch.return_value = [
        {
            'id': i,
            'tool_name': f'tool_{i}',
            'description': f'Tool {i}',
            'platform': 'linux',
            'category': 'system',
            'distance': 0.1 * i,
        }
        for i in range(1, 11)  # 10 results
    ]
    
    query_embedding = [0.1] * 768
    
    # Request only 5 results
    results = await search_tools(mock_conn, query_embedding, top_k=5)
    
    # Verify LIMIT was passed to query
    call_args = mock_conn.fetch.call_args
    assert call_args[0][2] == 5  # top_k parameter


@pytest.mark.asyncio
async def test_search_tools_handles_empty_results():
    """Test that empty results are handled gracefully."""
    mock_conn = AsyncMock()
    mock_conn.fetch.return_value = []
    
    query_embedding = [0.1] * 768
    
    results = await search_tools(mock_conn, query_embedding, top_k=10)
    
    assert results == []


@pytest.mark.asyncio
async def test_search_tools_handles_missing_description():
    """Test that None description is handled gracefully."""
    mock_conn = AsyncMock()
    
    mock_conn.fetch.return_value = [
        {
            'id': 1,
            'tool_name': 'tool_a',
            'description': None,  # Missing description
            'platform': 'linux',
            'category': 'system',
            'distance': 0.1,
        },
    ]
    
    query_embedding = [0.1] * 768
    
    results = await search_tools(mock_conn, query_embedding, top_k=1)
    
    assert len(results) == 1
    assert results[0].description == ''  # Should default to empty string