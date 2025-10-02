"""
Phase 4 Tests: Asset-Service Response Formatting

Tests for asset-service result formatting with disambiguation logic,
error handling, and credential redaction.
"""

import pytest
from pipeline.stages.stage_d.response_formatter import ResponseFormatter
from llm.ollama_client import OllamaClient


# Mock LLM client for testing
class MockLLMClient:
    """Mock LLM client for testing"""
    def __init__(self):
        self.is_connected = True


@pytest.fixture
def formatter():
    """Create response formatter with mock LLM client"""
    mock_client = MockLLMClient()
    return ResponseFormatter(mock_client)


# ========================================
# Test: format_asset_results() - No Results
# ========================================

def test_format_no_assets_found(formatter):
    """Test formatting when no assets are found"""
    assets = []
    query_context = {
        "hostname": "web-prod-01",
        "environment": "production"
    }
    
    result = formatter.format_asset_results(assets, query_context)
    
    # Verify message structure
    assert "No assets found" in result
    assert "web-prod-01" in result
    assert "production" in result
    assert "Suggestions:" in result
    assert "typos" in result.lower()


def test_format_no_assets_without_context(formatter):
    """Test formatting when no assets found without query context"""
    assets = []
    
    result = formatter.format_asset_results(assets, None)
    
    assert "No assets found" in result
    assert "Suggestions:" in result


# ========================================
# Test: format_asset_results() - Single Result
# ========================================

def test_format_single_asset(formatter):
    """Test formatting a single asset result"""
    assets = [
        {
            "hostname": "web-prod-01",
            "ip_address": "10.0.1.50",
            "environment": "production",
            "status": "active",
            "os_type": "Ubuntu 22.04",
            "service_type": "web"
        }
    ]
    
    result = formatter.format_asset_results(assets)
    
    # Verify all important fields are present
    assert "Asset found:" in result
    assert "web-prod-01" in result
    assert "10.0.1.50" in result
    assert "production" in result
    assert "active" in result
    assert "Ubuntu 22.04" in result
    assert "web" in result


def test_format_single_asset_with_missing_fields(formatter):
    """Test formatting single asset with some missing fields"""
    assets = [
        {
            "hostname": "db-staging-02",
            "ip_address": "10.0.2.100",
            "environment": "staging"
            # Missing: status, os_type, service_type
        }
    ]
    
    result = formatter.format_asset_results(assets)
    
    assert "Asset found:" in result
    assert "db-staging-02" in result
    assert "10.0.2.100" in result
    assert "staging" in result


# ========================================
# Test: format_asset_results() - Few Results (2-5)
# ========================================

def test_format_few_assets(formatter):
    """Test formatting 2-5 assets as a table"""
    assets = [
        {
            "hostname": "web-prod-01",
            "ip_address": "10.0.1.50",
            "environment": "production",
            "status": "active"
        },
        {
            "hostname": "web-prod-02",
            "ip_address": "10.0.1.51",
            "environment": "production",
            "status": "active"
        },
        {
            "hostname": "web-staging-01",
            "ip_address": "10.0.2.50",
            "environment": "staging",
            "status": "active"
        }
    ]
    
    result = formatter.format_asset_results(assets)
    
    # Verify table structure
    assert "Found 3 matching assets:" in result
    assert "hostname" in result
    assert "ip_address" in result
    assert "environment" in result
    assert "status" in result
    assert "web-prod-01" in result
    assert "web-prod-02" in result
    assert "web-staging-01" in result
    assert "specify which asset" in result.lower()


# ========================================
# Test: format_asset_results() - Many Results (6-50)
# ========================================

def test_format_many_assets(formatter):
    """Test formatting 6-50 assets grouped by environment"""
    assets = []
    
    # Create 20 assets across different environments
    for i in range(10):
        assets.append({
            "hostname": f"web-prod-{i:02d}",
            "ip_address": f"10.0.1.{50+i}",
            "environment": "production",
            "status": "active"
        })
    
    for i in range(7):
        assets.append({
            "hostname": f"web-staging-{i:02d}",
            "ip_address": f"10.0.2.{50+i}",
            "environment": "staging",
            "status": "active"
        })
    
    for i in range(3):
        assets.append({
            "hostname": f"web-dev-{i:02d}",
            "ip_address": f"10.0.3.{50+i}",
            "environment": "development",
            "status": "active"
        })
    
    result = formatter.format_asset_results(assets)
    
    # Verify grouped summary
    assert "Found 20 matching assets" in result
    assert "Summary by environment:" in result
    assert "production: 10 assets" in result
    assert "staging: 7 assets" in result
    assert "development: 3 assets" in result
    assert "Showing first 10 assets:" in result
    assert "narrow results" in result.lower()


# ========================================
# Test: format_asset_results() - Too Many Results (50+)
# ========================================

def test_format_too_many_assets(formatter):
    """Test formatting when there are too many results (50+)"""
    assets = []
    
    # Create 75 assets
    for i in range(75):
        assets.append({
            "hostname": f"server-{i:03d}",
            "ip_address": f"10.0.{i//256}.{i%256}",
            "environment": "production",
            "status": "active"
        })
    
    result = formatter.format_asset_results(assets)
    
    # Verify pagination guidance
    assert "Found 75 matching assets" in result
    assert "showing first 10" in result.lower()
    assert "and 65 more assets" in result
    assert "Too many results" in result
    assert "narrow your search" in result.lower()
    assert "Specify an environment" in result


# ========================================
# Test: rank_assets()
# ========================================

def test_rank_assets_exact_match(formatter):
    """Test asset ranking with exact hostname match"""
    assets = [
        {"hostname": "web-staging-01", "environment": "staging", "status": "active"},
        {"hostname": "web-prod-01", "environment": "production", "status": "active"},
        {"hostname": "web-dev-01", "environment": "development", "status": "active"}
    ]
    
    query_context = {"hostname": "web-prod-01"}
    
    ranked = formatter.rank_assets(assets, query_context)
    
    # Exact match should be first
    assert ranked[0]["hostname"] == "web-prod-01"


def test_rank_assets_by_environment(formatter):
    """Test asset ranking by environment priority"""
    assets = [
        {"hostname": "server-dev", "environment": "development", "status": "active"},
        {"hostname": "server-staging", "environment": "staging", "status": "active"},
        {"hostname": "server-prod", "environment": "production", "status": "active"}
    ]
    
    ranked = formatter.rank_assets(assets)
    
    # Production should be first, then staging, then development
    assert ranked[0]["environment"] == "production"
    assert ranked[1]["environment"] == "staging"
    assert ranked[2]["environment"] == "development"


def test_rank_assets_by_status(formatter):
    """Test asset ranking by status"""
    assets = [
        {"hostname": "server-01", "environment": "production", "status": "inactive"},
        {"hostname": "server-02", "environment": "production", "status": "active"},
        {"hostname": "server-03", "environment": "production", "status": "unknown"}
    ]
    
    ranked = formatter.rank_assets(assets)
    
    # Active should be first
    assert ranked[0]["status"] == "active"
    assert ranked[1]["status"] == "inactive"
    assert ranked[2]["status"] == "unknown"


def test_rank_assets_alphabetically(formatter):
    """Test asset ranking alphabetically when other factors are equal"""
    assets = [
        {"hostname": "zebra-server", "environment": "production", "status": "active"},
        {"hostname": "alpha-server", "environment": "production", "status": "active"},
        {"hostname": "beta-server", "environment": "production", "status": "active"}
    ]
    
    ranked = formatter.rank_assets(assets)
    
    # Should be alphabetical
    assert ranked[0]["hostname"] == "alpha-server"
    assert ranked[1]["hostname"] == "beta-server"
    assert ranked[2]["hostname"] == "zebra-server"


# ========================================
# Test: format_asset_error()
# ========================================

def test_format_timeout_error(formatter):
    """Test formatting timeout error"""
    result = formatter.format_asset_error("timeout")
    
    assert "⚠️" in result
    assert "timed out" in result.lower()
    assert "try again" in result.lower()


def test_format_circuit_breaker_error(formatter):
    """Test formatting circuit breaker error"""
    result = formatter.format_asset_error("circuit_breaker")
    
    assert "⚠️" in result
    assert "temporarily unavailable" in result.lower()
    assert "recovery mode" in result.lower()


def test_format_schema_error(formatter):
    """Test formatting schema validation error"""
    result = formatter.format_asset_error("schema_error")
    
    assert "⚠️" in result
    assert "unexpected data format" in result.lower()
    assert "schema" in result.lower()


def test_format_permission_denied_error(formatter):
    """Test formatting permission denied error"""
    result = formatter.format_asset_error("permission_denied")
    
    assert "⚠️" in result
    assert "permission denied" in result.lower()
    assert "administrator" in result.lower()


def test_format_error_with_details(formatter):
    """Test formatting error with additional details"""
    error_details = {
        "message": "Connection refused",
        "status_code": 503
    }
    
    result = formatter.format_asset_error("network_error", error_details)
    
    assert "⚠️" in result
    assert "network error" in result.lower()
    assert "Connection refused" in result
    assert "503" in result


def test_format_unknown_error(formatter):
    """Test formatting unknown error type"""
    result = formatter.format_asset_error("unknown_error_type")
    
    assert "⚠️" in result
    assert "unknown_error_type" in result


# ========================================
# Test: redact_credential_handle()
# ========================================

def test_redact_credential_handle(formatter):
    """Test credential data redaction"""
    credential_data = {
        "credential_id": "cred_12345",
        "credential_type": "ssh_key",
        "asset_id": "asset_67890",
        "created_at": "2024-01-15T10:00:00Z",
        "expires_at": "2024-02-15T10:00:00Z",
        "status": "active",
        # Sensitive fields that should be redacted
        "private_key": "-----BEGIN RSA PRIVATE KEY-----\nMIIEpAIBAAKCAQEA...",
        "password": "super_secret_password",
        "api_token": "sk_live_abc123xyz789"
    }
    
    redacted = formatter.redact_credential_handle(credential_data)
    
    # Verify safe fields are included
    assert redacted["credential_id"] == "cred_12345"
    assert redacted["credential_type"] == "ssh_key"
    assert redacted["asset_id"] == "asset_67890"
    assert redacted["created_at"] == "2024-01-15T10:00:00Z"
    assert redacted["expires_at"] == "2024-02-15T10:00:00Z"
    assert redacted["status"] == "active"
    
    # Verify sensitive fields are NOT included
    assert "private_key" not in redacted
    assert "password" not in redacted
    assert "api_token" not in redacted
    
    # Verify redaction notice
    assert redacted["_redacted"] is True
    assert "_note" in redacted
    assert "redacted" in redacted["_note"].lower()


def test_redact_credential_handle_partial_data(formatter):
    """Test credential redaction with partial data"""
    credential_data = {
        "credential_id": "cred_99999",
        "credential_type": "api_key"
        # Missing other fields
    }
    
    redacted = formatter.redact_credential_handle(credential_data)
    
    assert redacted["credential_id"] == "cred_99999"
    assert redacted["credential_type"] == "api_key"
    assert redacted["_redacted"] is True


# ========================================
# Test: Integration Scenarios
# ========================================

def test_format_and_rank_assets_together(formatter):
    """Test ranking and formatting assets together"""
    assets = [
        {"hostname": "web-dev-01", "environment": "development", "status": "active", "ip_address": "10.0.3.1"},
        {"hostname": "web-prod-01", "environment": "production", "status": "active", "ip_address": "10.0.1.1"},
        {"hostname": "web-staging-01", "environment": "staging", "status": "active", "ip_address": "10.0.2.1"}
    ]
    
    # Rank first
    ranked = formatter.rank_assets(assets)
    
    # Then format
    result = formatter.format_asset_results(ranked)
    
    # Production should appear first in the table
    assert result.index("web-prod-01") < result.index("web-staging-01")
    assert result.index("web-staging-01") < result.index("web-dev-01")


def test_format_assets_with_query_context(formatter):
    """Test formatting assets with query context for better messages"""
    assets = []
    query_context = {
        "hostname": "nonexistent-server",
        "environment": "production"
    }
    
    result = formatter.format_asset_results(assets, query_context)
    
    assert "nonexistent-server" in result
    assert "production" in result


# ========================================
# Test: Edge Cases
# ========================================

def test_format_assets_with_empty_fields(formatter):
    """Test formatting assets with empty string fields"""
    assets = [
        {
            "hostname": "server-01",
            "ip_address": "",  # Empty string
            "environment": "production",
            "status": None  # None value
        }
    ]
    
    result = formatter.format_asset_results(assets)
    
    # Should handle gracefully
    assert "Asset found:" in result
    assert "server-01" in result


def test_rank_assets_with_missing_fields(formatter):
    """Test ranking assets with missing fields"""
    assets = [
        {"hostname": "server-01"},  # Missing environment and status
        {"hostname": "server-02", "environment": "production"},
        {"hostname": "server-03", "environment": "production", "status": "active"}
    ]
    
    # Should not crash
    ranked = formatter.rank_assets(assets)
    
    assert len(ranked) == 3
    # Asset with most complete data should rank higher
    assert ranked[0]["hostname"] == "server-03"


def test_format_assets_boundary_cases(formatter):
    """Test formatting at boundary conditions"""
    # Exactly 5 assets (boundary between few and many)
    assets_5 = [{"hostname": f"server-{i}", "environment": "prod", "status": "active", "ip_address": f"10.0.0.{i}"} 
                for i in range(5)]
    result_5 = formatter.format_asset_results(assets_5)
    assert "Found 5 matching assets:" in result_5
    assert "hostname" in result_5  # Should show table
    
    # Exactly 6 assets (boundary to grouped view)
    assets_6 = [{"hostname": f"server-{i}", "environment": "prod", "status": "active", "ip_address": f"10.0.0.{i}"} 
                for i in range(6)]
    result_6 = formatter.format_asset_results(assets_6)
    assert "Found 6 matching assets" in result_6
    assert "Summary by environment:" in result_6  # Should show grouped view
    
    # Exactly 50 assets (boundary before pagination)
    assets_50 = [{"hostname": f"server-{i:02d}", "environment": "prod", "status": "active", "ip_address": f"10.0.0.{i}"} 
                 for i in range(50)]
    result_50 = formatter.format_asset_results(assets_50)
    assert "Found 50 matching assets" in result_50
    assert "Summary by environment:" in result_50
    assert "Too many results" not in result_50  # Should NOT show pagination warning
    
    # Exactly 51 assets (triggers pagination)
    assets_51 = [{"hostname": f"server-{i:02d}", "environment": "prod", "status": "active", "ip_address": f"10.0.0.{i}"} 
                 for i in range(51)]
    result_51 = formatter.format_asset_results(assets_51)
    assert "Found 51 matching assets" in result_51
    assert "Too many results" in result_51  # Should show pagination warning


if __name__ == "__main__":
    pytest.main([__file__, "-v"])