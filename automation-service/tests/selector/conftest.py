"""
Fixtures for selector v3 tests.
"""

import pytest
from selector.v3 import get_cache


@pytest.fixture(autouse=True)
async def clear_cache():
    """Clear the selector cache before each test to avoid cross-test contamination."""
    cache = get_cache()
    await cache.clear()
    yield
    # Optionally clear after test as well
    await cache.clear()