"""
CI Gate: Metrics Presence Test (PR #5)

This test ensures that required Prometheus metrics are exposed and accessible.
Fails CI if any required metric family is missing or /metrics is unreachable.

Required metrics:
- ai_requests_total
- ai_request_duration_seconds
- ai_request_errors_total
- selector_requests_total
- selector_request_duration_seconds
- selector_build_info
"""
import pytest
import httpx
import os
from typing import List, Set


# Get automation service URL from environment
AUTOMATION_SERVICE_URL = os.getenv("AUTOMATION_SERVICE_URL", "http://localhost:8010")
METRICS_ENDPOINT = f"{AUTOMATION_SERVICE_URL}/metrics"

# Required metric families
REQUIRED_AI_METRICS = [
    "ai_requests_total",
    "ai_request_duration_seconds",
    "ai_request_errors_total",
]

REQUIRED_SELECTOR_METRICS = [
    "selector_requests_total",
    "selector_request_duration_seconds",
    "selector_build_info",
]

ALL_REQUIRED_METRICS = REQUIRED_AI_METRICS + REQUIRED_SELECTOR_METRICS


def parse_metric_families(metrics_text: str) -> Set[str]:
    """
    Parse Prometheus metrics text and extract metric family names.
    
    Args:
        metrics_text: Raw Prometheus metrics text
        
    Returns:
        Set of metric family names found
    """
    families = set()
    for line in metrics_text.split('\n'):
        line = line.strip()
        # Skip comments and empty lines
        if not line or line.startswith('#'):
            # Extract from HELP/TYPE lines
            if line.startswith('# HELP ') or line.startswith('# TYPE '):
                parts = line.split()
                if len(parts) >= 3:
                    families.add(parts[2])
            continue
        # Extract from metric lines
        if line:
            # Metric name is before { or space
            metric_name = line.split('{')[0].split()[0]
            # Remove _bucket, _sum, _count suffixes for histograms
            base_name = metric_name.replace('_bucket', '').replace('_sum', '').replace('_count', '')
            families.add(base_name)
    return families


@pytest.mark.asyncio
async def test_metrics_endpoint_reachable():
    """Test that /metrics endpoint is reachable and returns 200 OK"""
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(METRICS_ENDPOINT, timeout=5.0)
            assert response.status_code == 200, \
                f"Metrics endpoint returned {response.status_code}, expected 200"
            assert len(response.text) > 0, \
                "Metrics endpoint returned empty response"
        except httpx.ConnectError as e:
            pytest.fail(f"Cannot connect to metrics endpoint {METRICS_ENDPOINT}: {e}")
        except httpx.TimeoutException as e:
            pytest.fail(f"Timeout connecting to metrics endpoint {METRICS_ENDPOINT}: {e}")


@pytest.mark.asyncio
async def test_metrics_content_type():
    """Test that /metrics endpoint returns correct content type"""
    async with httpx.AsyncClient() as client:
        response = await client.get(METRICS_ENDPOINT, timeout=5.0)
        content_type = response.headers.get('content-type', '')
        # Prometheus metrics should be text/plain or application/openmetrics-text
        assert 'text/plain' in content_type or 'openmetrics' in content_type, \
            f"Unexpected content type: {content_type}"


@pytest.mark.asyncio
async def test_ai_metrics_present():
    """Test that all required AI execution metrics are present"""
    async with httpx.AsyncClient() as client:
        response = await client.get(METRICS_ENDPOINT, timeout=5.0)
        metrics_text = response.text
        
        families = parse_metric_families(metrics_text)
        
        missing_metrics = []
        for metric in REQUIRED_AI_METRICS:
            if metric not in families:
                missing_metrics.append(metric)
        
        assert not missing_metrics, \
            f"Missing required AI metrics: {', '.join(missing_metrics)}\n" \
            f"Found metrics: {sorted(families)}"


@pytest.mark.asyncio
async def test_selector_metrics_present():
    """Test that all required selector metrics are present"""
    async with httpx.AsyncClient() as client:
        response = await client.get(METRICS_ENDPOINT, timeout=5.0)
        metrics_text = response.text
        
        families = parse_metric_families(metrics_text)
        
        missing_metrics = []
        for metric in REQUIRED_SELECTOR_METRICS:
            if metric not in families:
                missing_metrics.append(metric)
        
        assert not missing_metrics, \
            f"Missing required selector metrics: {', '.join(missing_metrics)}\n" \
            f"Found metrics: {sorted(families)}"


@pytest.mark.asyncio
async def test_all_required_metrics_present():
    """
    CI GATE: Test that ALL required metrics are present.
    This is the main gate that fails CI if any metric is missing.
    """
    async with httpx.AsyncClient() as client:
        response = await client.get(METRICS_ENDPOINT, timeout=5.0)
        assert response.status_code == 200, \
            f"Metrics endpoint returned {response.status_code}"
        
        metrics_text = response.text
        families = parse_metric_families(metrics_text)
        
        missing_metrics = []
        for metric in ALL_REQUIRED_METRICS:
            if metric not in families:
                missing_metrics.append(metric)
        
        if missing_metrics:
            pytest.fail(
                f"❌ CI GATE FAILED: Missing required metrics\n"
                f"Missing: {', '.join(missing_metrics)}\n"
                f"Required: {', '.join(ALL_REQUIRED_METRICS)}\n"
                f"Found: {', '.join(sorted(families))}\n\n"
                f"This test ensures that Prometheus metrics are properly exposed.\n"
                f"Fix by ensuring all metric families are registered and exported."
            )


@pytest.mark.asyncio
async def test_metrics_have_help_and_type():
    """Test that metrics have proper HELP and TYPE annotations"""
    async with httpx.AsyncClient() as client:
        response = await client.get(METRICS_ENDPOINT, timeout=5.0)
        metrics_text = response.text
        
        for metric in ALL_REQUIRED_METRICS:
            assert f"# HELP {metric}" in metrics_text, \
                f"Metric {metric} missing HELP annotation"
            assert f"# TYPE {metric}" in metrics_text, \
                f"Metric {metric} missing TYPE annotation"


@pytest.mark.asyncio
async def test_histogram_metrics_have_buckets():
    """Test that histogram metrics have proper bucket structure"""
    async with httpx.AsyncClient() as client:
        response = await client.get(METRICS_ENDPOINT, timeout=5.0)
        metrics_text = response.text
        
        histogram_metrics = [
            "ai_request_duration_seconds",
            "selector_request_duration_seconds",
        ]
        
        for metric in histogram_metrics:
            # Check for histogram type
            assert f"# TYPE {metric} histogram" in metrics_text, \
                f"Metric {metric} not declared as histogram"
            
            # Check for bucket, sum, and count
            assert f"{metric}_bucket" in metrics_text, \
                f"Histogram {metric} missing _bucket"
            assert f"{metric}_sum" in metrics_text, \
                f"Histogram {metric} missing _sum"
            assert f"{metric}_count" in metrics_text, \
                f"Histogram {metric} missing _count"


@pytest.mark.asyncio
async def test_counter_metrics_have_labels():
    """Test that counter metrics have expected labels"""
    async with httpx.AsyncClient() as client:
        response = await client.get(METRICS_ENDPOINT, timeout=5.0)
        metrics_text = response.text
        
        # ai_requests_total should have status and tool labels
        if "ai_requests_total{" in metrics_text:
            assert 'status=' in metrics_text, \
                "ai_requests_total missing status label"
            assert 'tool=' in metrics_text, \
                "ai_requests_total missing tool label"
        
        # selector_requests_total should have status and source labels
        if "selector_requests_total{" in metrics_text:
            assert 'status=' in metrics_text, \
                "selector_requests_total missing status label"
            assert 'source=' in metrics_text, \
                "selector_requests_total missing source label"


@pytest.mark.asyncio
async def test_build_info_metric():
    """Test that selector_build_info metric is present with version info"""
    async with httpx.AsyncClient() as client:
        response = await client.get(METRICS_ENDPOINT, timeout=5.0)
        metrics_text = response.text
        
        assert "selector_build_info" in metrics_text, \
            "selector_build_info metric not found"
        
        # Should have version label
        assert 'version=' in metrics_text, \
            "selector_build_info missing version label"


if __name__ == "__main__":
    # Run tests with pytest
    pytest.main([__file__, "-v", "-s"])