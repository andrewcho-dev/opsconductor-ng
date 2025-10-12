"""
Pluggable embedding provider with optional sentence-transformers support
and deterministic SHA256-based fallback.

Usage:
    provider = EmbeddingProvider()  # Uses env EMBED_MODEL or fallback
    vec = await provider.embed("scan network for open ports")
    assert len(vec) == 128
    assert 0.95 <= sum(x*x for x in vec)**0.5 <= 1.05  # ~unit norm
"""

import hashlib
import math
import os
from typing import Optional

# Optional import - module works without sentence-transformers
try:
    from sentence_transformers import SentenceTransformer
    HAS_SENTENCE_TRANSFORMERS = True
except ImportError:
    SentenceTransformer = None
    HAS_SENTENCE_TRANSFORMERS = False


class EmbeddingProvider:
    """
    Embedding provider with optional sentence-transformers support.
    Falls back to deterministic SHA256-based embeddings if model unavailable.
    """
    
    def __init__(self, model: Optional[str] = None):
        """
        Initialize embedding provider.
        
        Args:
            model: Model name/path for sentence-transformers, or None to use env EMBED_MODEL
        """
        self.model_name = model or os.getenv("EMBED_MODEL")
        self._model = None
        self._use_fallback = False
        
        if self.model_name and HAS_SENTENCE_TRANSFORMERS:
            try:
                self._model = SentenceTransformer(self.model_name)
            except Exception as e:
                print(f"Warning: Failed to load model {self.model_name}: {e}")
                print("Falling back to deterministic embeddings")
                self._use_fallback = True
        else:
            self._use_fallback = True
    
    async def embed(self, text: str) -> list[float]:
        """
        Generate 128-dimensional L2-normalized embedding for text.
        
        Args:
            text: Input text to embed
            
        Returns:
            List of 128 floats with L2 norm ≈ 1.0
        """
        if self._use_fallback or self._model is None:
            return self._deterministic_embed(text)
        
        # Use sentence-transformers model
        try:
            vec = self._model.encode(text, convert_to_numpy=True)
            # Ensure exactly 128 dimensions
            if len(vec) > 128:
                vec = vec[:128]
            elif len(vec) < 128:
                # Pad with zeros
                import numpy as np
                padded = np.zeros(128, dtype=vec.dtype)
                padded[:len(vec)] = vec
                vec = padded
            
            # L2 normalize
            return self._normalize(vec.tolist())
        except Exception as e:
            print(f"Warning: Model encoding failed: {e}, using fallback")
            return self._deterministic_embed(text)
    
    def _deterministic_embed(self, text: str) -> list[float]:
        """
        Generate deterministic 128-d embedding from SHA256 hash expansion.
        Same input always produces same output.
        
        Args:
            text: Input text
            
        Returns:
            List of 128 normalized floats
        """
        # Generate multiple hashes to get 128 values
        # SHA256 gives 32 bytes = 32 values, need 4 rounds for 128
        vec = []
        for i in range(4):
            # Hash with salt to get different values per round
            salted = f"{text}::{i}".encode('utf-8')
            hash_bytes = hashlib.sha256(salted).digest()
            # Convert bytes to floats in [-1, 1]
            for byte in hash_bytes:
                # Map byte (0-255) to float (-1 to 1)
                vec.append((byte / 127.5) - 1.0)
        
        # Take first 128 values and normalize
        vec = vec[:128]
        return self._normalize(vec)
    
    def _normalize(self, vec: list[float]) -> list[float]:
        """L2 normalize vector to unit length."""
        norm = math.sqrt(sum(x * x for x in vec))
        if norm < 1e-10:
            # Avoid division by zero
            norm = 1.0
        return [x / norm for x in vec]


async def embed_intent(provider: EmbeddingProvider, intent: str) -> list[float]:
    """
    Convenience function to embed user intent.
    
    Args:
        provider: EmbeddingProvider instance
        intent: User intent string
        
    Returns:
        128-dimensional normalized embedding
    """
    return await provider.embed(intent)


# Doctest examples
if __name__ == "__main__":
    import asyncio
    
    async def test_embeddings():
        """Test embedding provider."""
        provider = EmbeddingProvider()
        
        # Test 1: Correct dimensions
        vec = await provider.embed("hello world")
        assert len(vec) == 128, f"Expected 128 dims, got {len(vec)}"
        print(f"✓ Dimension test passed: {len(vec)} dims")
        
        # Test 2: Unit norm
        norm = math.sqrt(sum(x * x for x in vec))
        assert 0.95 <= norm <= 1.05, f"Expected unit norm, got {norm}"
        print(f"✓ Norm test passed: {norm:.4f}")
        
        # Test 3: Deterministic (same input = same output)
        vec1 = await provider.embed("test string")
        vec2 = await provider.embed("test string")
        assert vec1 == vec2, "Deterministic embedding failed"
        print(f"✓ Deterministic test passed")
        
        # Test 4: Different inputs = different outputs
        vec3 = await provider.embed("different string")
        assert vec1 != vec3, "Different inputs should produce different embeddings"
        print(f"✓ Uniqueness test passed")
        
        # Test 5: embed_intent helper
        vec4 = await embed_intent(provider, "scan network")
        assert len(vec4) == 128
        print(f"✓ embed_intent test passed")
        
        print("\n✅ All tests passed!")
    
    asyncio.run(test_embeddings())