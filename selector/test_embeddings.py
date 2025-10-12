"""Tests for EmbeddingProvider."""

import math
import pytest

from selector.embeddings import EmbeddingProvider, embed_intent


@pytest.mark.asyncio
async def test_embedding_dimensions():
    """Test that embeddings have correct dimensions."""
    provider = EmbeddingProvider()
    vec = await provider.embed("test string")
    assert len(vec) == 128


@pytest.mark.asyncio
async def test_embedding_normalized():
    """Test that embeddings are L2 normalized."""
    provider = EmbeddingProvider()
    vec = await provider.embed("hello world")
    norm = math.sqrt(sum(x * x for x in vec))
    assert 0.95 <= norm <= 1.05, f"Expected unit norm, got {norm}"


@pytest.mark.asyncio
async def test_deterministic_fallback():
    """Test that fallback embeddings are deterministic."""
    provider = EmbeddingProvider()  # No model = fallback
    vec1 = await provider.embed("scan network")
    vec2 = await provider.embed("scan network")
    assert vec1 == vec2, "Same input should produce same embedding"


@pytest.mark.asyncio
async def test_different_inputs_different_outputs():
    """Test that different inputs produce different embeddings."""
    provider = EmbeddingProvider()
    vec1 = await provider.embed("input A")
    vec2 = await provider.embed("input B")
    assert vec1 != vec2, "Different inputs should produce different embeddings"


@pytest.mark.asyncio
async def test_embed_intent_helper():
    """Test embed_intent convenience function."""
    provider = EmbeddingProvider()
    vec = await embed_intent(provider, "restart apache service")
    assert len(vec) == 128
    norm = math.sqrt(sum(x * x for x in vec))
    assert 0.95 <= norm <= 1.05


@pytest.mark.asyncio
async def test_empty_string():
    """Test embedding empty string doesn't crash."""
    provider = EmbeddingProvider()
    vec = await provider.embed("")
    assert len(vec) == 128
    norm = math.sqrt(sum(x * x for x in vec))
    assert norm > 0