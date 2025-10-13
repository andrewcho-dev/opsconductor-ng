"""
CI metrics validation test.

This test ensures that required Prometheus metrics are exposed.
CI should fail if these metrics are missing.
"""

import os
import urllib.request
from urllib.error import HTTPError, URLError

import pytest


def test_required_metrics_present():
    """
    Test that all required Prometheus metrics are present.
    
    This test is designed to fail CI if metrics are missing.
    """
    base_url = os.getenv("SELECTOR_URL", "http://localhost:3003")
    url = f"{base_url}/metrics"
    
    # Required metric families
    required_metrics = [
        "selector_requests_total",
        "selector_request_duration_seconds",
    ]
    
    try:
        with urllib.request.urlopen(url, timeout=10) as response:
            assert response.status == 200, f"Expected 200, got {response.status}"
            
            text = response.read().decode("utf-8")
            
            # Check each required metric
            missing = []
            for metric in required_metrics:
                if metric not in text:
                    missing.append(metric)
            
            assert not missing, f"Missing required metrics: {', '.join(missing)}"
            
            print(f"✅ All required metrics present: {', '.join(required_metrics)}")
    
    except (HTTPError, URLError) as e:
        pytest.fail(f"Failed to fetch metrics: {e}")
    except Exception as e:
        pytest.fail(f"Unexpected error: {e}")


def test_metrics_well_formed():
    """Test that metrics are well-formed Prometheus text format."""
    base_url = os.getenv("SELECTOR_URL", "http://localhost:3003")
    url = f"{base_url}/metrics"
    
    try:
        with urllib.request.urlopen(url, timeout=10) as response:
            text = response.read().decode("utf-8")
            
            # Check for TYPE declarations
            assert "# TYPE selector_requests_total counter" in text
            assert "# TYPE selector_request_duration_seconds histogram" in text
            
            # Check for HELP declarations
            assert "# HELP selector_requests_total" in text
            assert "# HELP selector_request_duration_seconds" in text
            
            print("✅ Metrics are well-formed")
    
    except (HTTPError, URLError) as e:
        pytest.fail(f"Failed to fetch metrics: {e}")
    except Exception as e:
        pytest.fail(f"Unexpected error: {e}")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])