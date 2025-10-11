"""Snapshot tests for candidate tool selection.

These tests verify that:
1. The prompt contains only tool stubs (minimal information)
2. The prompt size is below the token budget
"""

import pytest
from unittest.mock import AsyncMock, patch
from selector.candidates import candidate_tools_from_intent, get_always_include_tools
from db.retrieval import ToolStub


# Token budget constants (from requirements)
CTX_SIZE = 8192
HEADROOM = 0.30
BASE_TOKENS = 900
TOKENS_PER_CHAR = 0.25  # Approximate: 4 chars per token


def estimate_tokens(text: str) -> int:
    """Estimate token count from text length.
    
    Args:
        text: Text to estimate
        
    Returns:
        Estimated token count
    """
    return int(len(text) * TOKENS_PER_CHAR)


def calculate_budget() -> int:
    """Calculate available token budget for tool candidates.
    
    Returns:
        Available tokens for tool candidates
    """
    return int(CTX_SIZE - (CTX_SIZE * HEADROOM) - BASE_TOKENS)


@pytest.mark.asyncio
async def test_candidate_tools_returns_stubs_only():
    """Test that candidate_tools_from_intent returns minimal stubs."""
    mock_conn = AsyncMock()
    
    # Mock the search_tools function to return stubs
    mock_stubs = [
        ToolStub(
            id=i,
            tool_name=f"tool_{i}",
            description=f"Description for tool {i}",
            platform="linux",
            category="system",
            similarity=0.9 - (i * 0.1),
        )
        for i in range(1, 6)
    ]
    
    # Mock functions
    async def mock_get_embedding(text):
        return [0.1] * 768
    
    async def mock_search_tools(conn, query_embedding, top_k=50, platform=None):
        return mock_stubs[:top_k]
    
    async def mock_get_always_include(conn):
        return []
    
    with patch('selector.candidates.get_embedding_for_text', mock_get_embedding), \
         patch('db.retrieval.search_tools', mock_search_tools), \
         patch('selector.candidates.get_always_include_tools', mock_get_always_include):
        
        # Execute
        results = await candidate_tools_from_intent(mock_conn, "test query", k=5)
        
        # Verify results are stubs
        assert len(results) == 5
        assert all(isinstance(r, ToolStub) for r in results)
        
        # Verify stubs contain only minimal fields
        for stub in results:
            assert hasattr(stub, 'id')
            assert hasattr(stub, 'tool_name')
            assert hasattr(stub, 'description')
            assert hasattr(stub, 'platform')
            assert hasattr(stub, 'category')
            
            # Verify no full tool spec fields
            assert not hasattr(stub, 'parameters')
            assert not hasattr(stub, 'examples')
            assert not hasattr(stub, 'full_specification')


@pytest.mark.asyncio
async def test_candidate_prompt_size_below_budget():
    """Test that candidate tools fit within token budget."""
    mock_conn = AsyncMock()
    
    # Create realistic tool stubs
    mock_stubs = [
        ToolStub(
            id=i,
            tool_name=f"tool_name_{i}",
            description=f"This is a description for tool {i} that provides some functionality",
            platform="linux",
            category="system",
            similarity=0.9,
        )
        for i in range(1, 51)  # 50 tools
    ]
    
    # Mock functions
    async def mock_get_embedding(text):
        return [0.1] * 768
    
    async def mock_search_tools(conn, query_embedding, top_k=50, platform=None):
        return mock_stubs[:top_k]
    
    async def mock_get_always_include(conn):
        return []
    
    with patch('selector.candidates.get_embedding_for_text', mock_get_embedding), \
         patch('db.retrieval.search_tools', mock_search_tools), \
         patch('selector.candidates.get_always_include_tools', mock_get_always_include):
        
        # Execute
        results = await candidate_tools_from_intent(mock_conn, "test query", k=50)
        
        # Build a mock prompt with the stubs
        prompt_parts = ["Available tools:\n"]
        for stub in results:
            prompt_parts.append(f"- {stub.tool_name}: {stub.description} ({stub.platform}/{stub.category})\n")
        
        prompt = "".join(prompt_parts)
        
        # Estimate tokens
        estimated_tokens = estimate_tokens(prompt)
        budget = calculate_budget()
        
        # Verify prompt is below budget
        assert estimated_tokens < budget, (
            f"Prompt size ({estimated_tokens} tokens) exceeds budget ({budget} tokens). "
            f"Prompt length: {len(prompt)} chars"
        )
        
        # Verify we have at least 30% headroom
        headroom_pct = (budget - estimated_tokens) / budget
        assert headroom_pct >= 0.30, (
            f"Insufficient headroom: {headroom_pct:.1%} (need ≥30%)"
        )


@pytest.mark.asyncio
async def test_always_include_tools_are_added():
    """Test that always-include tools are added to candidates."""
    mock_conn = AsyncMock()
    
    # Mock regular search results
    regular_stubs = [
        ToolStub(
            id=i,
            tool_name=f"regular_tool_{i}",
            description=f"Regular tool {i}",
            platform="linux",
            category="system",
            similarity=0.8,
        )
        for i in range(1, 6)
    ]
    
    # Mock always-include tools
    always_include_stubs = [
        ToolStub(
            id=100,
            tool_name="critical_tool",
            description="Always included critical tool",
            platform="both",
            category="core",
        )
    ]
    
    # Mock functions
    async def mock_get_embedding(text):
        return [0.1] * 768
    
    async def mock_search_tools(conn, query_embedding, top_k=50, platform=None):
        return regular_stubs
    
    async def mock_get_always_include(conn):
        return always_include_stubs
    
    with patch('selector.candidates.get_embedding_for_text', mock_get_embedding), \
         patch('db.retrieval.search_tools', mock_search_tools), \
         patch('selector.candidates.get_always_include_tools', mock_get_always_include):
        
        # Execute
        results = await candidate_tools_from_intent(mock_conn, "test query", k=10)
        
        # Verify always-include tool is present
        tool_names = [r.tool_name for r in results]
        assert "critical_tool" in tool_names
        
        # Verify we have both regular and always-include tools
        assert len(results) == 6  # 5 regular + 1 always-include