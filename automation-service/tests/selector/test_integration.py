"""
Integration tests for Selector v3.

Tests degraded mode, metrics exposure, and database interaction.
"""

import asyncio
import os
import sys
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

# Add automation-service to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from selector.v3 import router as selector_v3_router


@pytest.fixture
def app():
    """Create test FastAPI app with selector v3 router."""
    app = FastAPI()
    app.include_router(selector_v3_router)
    return app


@pytest.fixture
def client(app):
    """Create test client."""
    return TestClient(app)


@pytest.fixture
def mock_db_pool():
    """Create mock database pool."""
    pool = MagicMock()
    
    # Mock connection
    conn = MagicMock()
    
    # Mock acquire context manager
    acquire_ctx = MagicMock()
    acquire_ctx.__aenter__ = AsyncMock(return_value=conn)
    acquire_ctx.__aexit__ = AsyncMock(return_value=None)
    pool.acquire.return_value = acquire_ctx
    
    return pool, conn


class TestDegradedMode:
    """Test degraded mode behavior during DB outages."""
    
    def test_warm_key_serves_from_cache_when_db_down(self, client, app):
        """Test warm key returns 200 from cache when DB is unavailable."""
        # First request - populate cache (DB available)
        with patch("selector.dao.select_topk") as mock_select:
            mock_select.return_value = [
                {"name": "test_tool", "short_desc": "Test tool"}
            ]
            
            # Mock DB pool
            pool = MagicMock()
            conn = MagicMock()
            acquire_ctx = MagicMock()
            acquire_ctx.__aenter__ = AsyncMock(return_value=conn)
            acquire_ctx.__aexit__ = AsyncMock(return_value=None)
            pool.acquire.return_value = acquire_ctx
            app.state.db_pool = pool
            
            response = client.get("/api/selector/search?query=test&k=3")
            assert response.status_code == 200
            assert response.json()["from_cache"] is False
        
        # Second request - DB unavailable, should serve from cache
        app.state.db_pool = None
        
        response = client.get("/api/selector/search?query=test&k=3")
        assert response.status_code == 200
        data = response.json()
        assert data["from_cache"] is True
        assert data["query"] == "test"
    
    def test_cold_key_returns_503_when_db_down(self, client, app):
        """Test cold key returns 503 when DB is unavailable."""
        # No cache, no DB
        app.state.db_pool = None
        
        response = client.get("/api/selector/search?query=cold_key_test&k=3")
        assert response.status_code == 503
        assert "Retry-After" in response.headers
        assert response.headers["Retry-After"] == "30"
        
        data = response.json()
        assert data["error"] == "DependencyUnavailable"
        assert data["code"] == "SELECTOR_DB_UNAVAILABLE"
        assert data["degraded"] is False
    
    def test_degraded_mode_on_db_error(self, client, app):
        """Test degraded mode serves LKG when DB query fails."""
        # First request - populate cache
        with patch("selector.dao.select_topk") as mock_select:
            mock_select.return_value = [
                {"name": "test_tool", "short_desc": "Test tool"}
            ]
            
            pool = MagicMock()
            conn = MagicMock()
            acquire_ctx = MagicMock()
            acquire_ctx.__aenter__ = AsyncMock(return_value=conn)
            acquire_ctx.__aexit__ = AsyncMock(return_value=None)
            pool.acquire.return_value = acquire_ctx
            app.state.db_pool = pool
            
            response = client.get("/api/selector/search?query=test&k=3")
            assert response.status_code == 200
        
        # Second request - DB query fails, should serve from cache
        with patch("selector.dao.select_topk") as mock_select:
            mock_select.side_effect = Exception("DB connection failed")
            
            response = client.get("/api/selector/search?query=test&k=3")
            assert response.status_code == 200
            data = response.json()
            assert data["from_cache"] is True


class TestMetrics:
    """Test metrics exposure and correctness."""
    
    def test_metrics_endpoint_exists(self, client):
        """Test /metrics endpoint is accessible."""
        response = client.get("/metrics")
        assert response.status_code == 200
        assert response.headers["content-type"] == "text/plain; charset=utf-8"
    
    def test_metrics_format(self, client):
        """Test metrics are in Prometheus text format."""
        response = client.get("/metrics")
        text = response.text
        
        # Check for required metric families
        assert "selector_requests_total" in text
        assert "selector_request_duration_seconds" in text
        assert "selector_cache_entries" in text
        assert "selector_cache_ttl_seconds" in text
        assert "selector_cache_evictions_total" in text
        assert "selector_db_errors_total" in text
        assert "selector_build_info" in text
    
    def test_metrics_well_typed(self, client):
        """Test metrics have correct types."""
        response = client.get("/metrics")
        text = response.text
        
        # Check TYPE declarations
        assert "# TYPE selector_requests_total counter" in text
        assert "# TYPE selector_request_duration_seconds histogram" in text
        assert "# TYPE selector_cache_entries gauge" in text
        assert "# TYPE selector_cache_ttl_seconds gauge" in text
        assert "# TYPE selector_cache_evictions_total counter" in text
        assert "# TYPE selector_db_errors_total counter" in text
        assert "# TYPE selector_build_info gauge" in text
    
    def test_metrics_updated_on_request(self, client, app):
        """Test metrics are updated after requests."""
        # Make a request
        with patch("selector.dao.select_topk") as mock_select:
            mock_select.return_value = [
                {"name": "test_tool", "short_desc": "Test tool"}
            ]
            
            pool = MagicMock()
            conn = MagicMock()
            acquire_ctx = MagicMock()
            acquire_ctx.__aenter__ = AsyncMock(return_value=conn)
            acquire_ctx.__aexit__ = AsyncMock(return_value=None)
            pool.acquire.return_value = acquire_ctx
            app.state.db_pool = pool
            
            client.get("/api/selector/search?query=test&k=3")
        
        # Check metrics
        response = client.get("/metrics")
        text = response.text
        
        # Should have at least one request
        assert 'selector_requests_total{status="ok",source="fresh"}' in text
        
        # Should have duration histogram
        assert "selector_request_duration_seconds_sum" in text
        assert "selector_request_duration_seconds_count" in text


class TestValidation:
    """Test input validation at API level."""
    
    def test_empty_query_returns_400(self, client):
        """Test empty query returns 400."""
        response = client.get("/api/selector/search?query=&k=3")
        assert response.status_code == 422  # FastAPI validation
    
    def test_query_too_long_returns_400(self, client):
        """Test query exceeding 200 chars returns 400."""
        long_query = "a" * 201
        response = client.get(f"/api/selector/search?query={long_query}&k=3")
        assert response.status_code == 400
        data = response.json()
        assert data["detail"]["code"] == "QUERY_TOO_LONG"
    
    def test_k_out_of_range_returns_400(self, client):
        """Test k out of range returns 400."""
        # k < 1
        response = client.get("/api/selector/search?query=test&k=0")
        assert response.status_code == 422  # FastAPI validation
        
        # k > 10
        response = client.get("/api/selector/search?query=test&k=11")
        assert response.status_code == 422  # FastAPI validation
    
    def test_too_many_platforms_returns_400(self, client):
        """Test more than 5 platforms returns 400."""
        platforms = "&".join([f"platform={p}" for p in ["linux", "windows", "macos", "freebsd", "solaris", "aix"]])
        response = client.get(f"/api/selector/search?query=test&k=3&{platforms}")
        assert response.status_code == 400
        data = response.json()
        assert data["detail"]["code"] == "TOO_MANY_PLATFORMS"


class TestCaching:
    """Test caching behavior."""
    
    def test_cache_hit_on_second_request(self, client, app):
        """Test second identical request is served from cache."""
        with patch("selector.dao.select_topk") as mock_select:
            mock_select.return_value = [
                {"name": "test_tool", "short_desc": "Test tool"}
            ]
            
            pool = MagicMock()
            conn = MagicMock()
            acquire_ctx = MagicMock()
            acquire_ctx.__aenter__ = AsyncMock(return_value=conn)
            acquire_ctx.__aexit__ = AsyncMock(return_value=None)
            pool.acquire.return_value = acquire_ctx
            app.state.db_pool = pool
            
            # First request
            response1 = client.get("/api/selector/search?query=test&k=3")
            assert response1.status_code == 200
            assert response1.json()["from_cache"] is False
            
            # Second request - should be cached
            response2 = client.get("/api/selector/search?query=test&k=3")
            assert response2.status_code == 200
            assert response2.json()["from_cache"] is True
            
            # Should only call DB once
            assert mock_select.call_count == 1
    
    def test_cache_key_normalization(self, client, app):
        """Test cache key normalization works correctly."""
        with patch("selector.dao.select_topk") as mock_select:
            mock_select.return_value = [
                {"name": "test_tool", "short_desc": "Test tool"}
            ]
            
            pool = MagicMock()
            conn = MagicMock()
            acquire_ctx = MagicMock()
            acquire_ctx.__aenter__ = AsyncMock(return_value=conn)
            acquire_ctx.__aexit__ = AsyncMock(return_value=None)
            pool.acquire.return_value = acquire_ctx
            app.state.db_pool = pool
            
            # First request
            response1 = client.get("/api/selector/search?query=TEST&platform=LINUX&k=3")
            assert response1.status_code == 200
            assert response1.json()["from_cache"] is False
            
            # Second request with different case - should hit cache
            response2 = client.get("/api/selector/search?query=test&platform=linux&k=3")
            assert response2.status_code == 200
            assert response2.json()["from_cache"] is True
            
            # Should only call DB once
            assert mock_select.call_count == 1


if __name__ == "__main__":
    pytest.main([__file__, "-v"])