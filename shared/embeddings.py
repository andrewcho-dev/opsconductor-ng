"""
Shared embedding utilities for tool catalog and runtime search.

Provides deterministic 128-dimensional embeddings using SHA256-based hashing.
This ensures compatibility between tool indexing and runtime search queries.

Usage:
    from shared.embeddings import embed_128, to_vec_literal
    
    vec = embed_128("scan network for open ports")
    vec_lit = to_vec_literal(vec)  # -> "[0.123456,0.234567,...]"
"""

import hashlib
import math
from typing import List


def embed_128(text: str) -> List[float]:
    """
    Generate deterministic 128-dimensional L2-normalized embedding from text.
    
    Uses SHA256 hash expansion to create consistent embeddings. Same input
    always produces the same output, ensuring index compatibility.
    
    Args:
        text: Input text to embed
        
    Returns:
        List of 128 floats with L2 norm ≈ 1.0
        
    Example:
        >>> vec = embed_128("hello world")
        >>> len(vec)
        128
        >>> 0.95 <= sum(x*x for x in vec)**0.5 <= 1.05
        True
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
    return _normalize(vec)


def to_vec_literal(vec: List[float]) -> str:
    """
    Convert a vector to PostgreSQL vector literal format.
    
    Formats floats with 6 decimal places for consistency with database storage.
    
    Args:
        vec: List of floats (typically 128-dimensional)
        
    Returns:
        PostgreSQL vector literal string: "[x,y,z,...]"
        
    Example:
        >>> vec = [0.1, 0.2, 0.3]
        >>> to_vec_literal(vec)
        '[0.100000,0.200000,0.300000]'
    """
    return "[" + ",".join(f"{x:.6f}" for x in vec) + "]"


def _normalize(vec: List[float]) -> List[float]:
    """
    L2 normalize vector to unit length.
    
    Args:
        vec: Input vector
        
    Returns:
        Normalized vector with L2 norm ≈ 1.0
    """
    norm = math.sqrt(sum(x * x for x in vec))
    if norm < 1e-10:
        # Avoid division by zero
        norm = 1.0
    return [x / norm for x in vec]


# Doctest examples
if __name__ == "__main__":
    import doctest
    doctest.testmod()
    
    # Additional tests
    print("Testing shared embeddings module...")
    
    # Test 1: Correct dimensions
    vec = embed_128("hello world")
    assert len(vec) == 128, f"Expected 128 dims, got {len(vec)}"
    print(f"✓ Dimension test passed: {len(vec)} dims")
    
    # Test 2: Unit norm
    norm = math.sqrt(sum(x * x for x in vec))
    assert 0.95 <= norm <= 1.05, f"Expected unit norm, got {norm}"
    print(f"✓ Norm test passed: {norm:.4f}")
    
    # Test 3: Deterministic (same input = same output)
    vec1 = embed_128("test string")
    vec2 = embed_128("test string")
    assert vec1 == vec2, "Deterministic embedding failed"
    print(f"✓ Deterministic test passed")
    
    # Test 4: Different inputs = different outputs
    vec3 = embed_128("different string")
    assert vec1 != vec3, "Different inputs should produce different embeddings"
    print(f"✓ Uniqueness test passed")
    
    # Test 5: Vector literal formatting
    vec_lit = to_vec_literal([0.1, 0.2, 0.3])
    assert vec_lit == "[0.100000,0.200000,0.300000]", f"Unexpected format: {vec_lit}"
    print(f"✓ Vector literal test passed")
    
    print("\n✅ All tests passed!")