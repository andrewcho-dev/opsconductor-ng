"""
Minimal E2E tests for /ai/execute endpoint (PR #4)
Tests the walking skeleton execution path
"""
import pytest
import httpx
import os


# Get automation service URL from environment
AUTOMATION_SERVICE_URL = os.getenv("AUTOMATION_SERVICE_URL", "http://localhost:8010")


@pytest.mark.asyncio
async def test_exec_ping_pong():
    """Test echo tool with 'ping' input returns 'pong'"""
    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{AUTOMATION_SERVICE_URL}/ai/execute",
            json={"input": "ping", "tool": "echo"},
            headers={"Content-Type": "application/json"},
            timeout=10.0
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["success"] is True
        assert data["output"] == "pong"
        assert data["tool"] == "echo"
        assert "trace_id" in data
        assert "duration_ms" in data
        assert data["duration_ms"] > 0


@pytest.mark.asyncio
async def test_exec_hello_echo():
    """Test echo tool with 'hello' input returns 'hello'"""
    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{AUTOMATION_SERVICE_URL}/ai/execute",
            json={"input": "hello", "tool": "echo"},
            headers={"Content-Type": "application/json"},
            timeout=10.0
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["success"] is True
        assert data["output"] == "hello"
        assert data["tool"] == "echo"


@pytest.mark.asyncio
async def test_exec_trace_id_propagation():
    """Test that trace_id is propagated through the system"""
    trace_id = "test_trace_12345"
    
    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{AUTOMATION_SERVICE_URL}/ai/execute",
            json={"input": "ping", "tool": "echo", "trace_id": trace_id},
            headers={"Content-Type": "application/json", "X-Trace-Id": trace_id},
            timeout=10.0
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["trace_id"] == trace_id


@pytest.mark.asyncio
async def test_exec_empty_input_validation():
    """Test that empty input returns validation error"""
    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{AUTOMATION_SERVICE_URL}/ai/execute",
            json={"input": "", "tool": "echo"},
            headers={"Content-Type": "application/json"},
            timeout=10.0
        )
        
        # Should return 400 or 422 for validation error
        assert response.status_code in [400, 422]


@pytest.mark.asyncio
async def test_exec_long_input():
    """Test echo with longer input text"""
    long_input = "Hello OpsConductor! This is a test of the execution path."
    
    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{AUTOMATION_SERVICE_URL}/ai/execute",
            json={"input": long_input, "tool": "echo"},
            headers={"Content-Type": "application/json"},
            timeout=10.0
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["success"] is True
        assert data["output"] == long_input


@pytest.mark.asyncio
async def test_metrics_endpoint():
    """Test that /metrics endpoint includes ai_* metrics"""
    async with httpx.AsyncClient() as client:
        response = await client.get(
            f"{AUTOMATION_SERVICE_URL}/metrics",
            timeout=5.0
        )
        
        assert response.status_code == 200
        metrics_text = response.text
        
        # Check for AI exec metrics
        assert "ai_requests_total" in metrics_text
        assert "ai_request_errors_total" in metrics_text
        assert "ai_request_duration_seconds" in metrics_text
        
        # Check for HELP and TYPE lines
        assert "# HELP ai_requests_total" in metrics_text
        assert "# TYPE ai_requests_total counter" in metrics_text
        assert "# TYPE ai_request_duration_seconds histogram" in metrics_text


if __name__ == "__main__":
    # Run tests with pytest
    pytest.main([__file__, "-v"])