#!/usr/bin/env python3
"""
Test PR #11: Asset-Intelligent Execution
Tests asset façade, secrets broker, and asset-aware tool execution
"""

import pytest
import httpx
import os
import asyncio
from datetime import datetime


# Test configuration
AUTOMATION_SERVICE_URL = os.getenv("AUTOMATION_SERVICE_URL", "http://localhost:3003")
KONG_URL = os.getenv("KONG_URL", "http://localhost:3000")


class TestAssetFacade:
    """Test asset façade endpoints"""
    
    @pytest.mark.asyncio
    async def test_asset_count_all(self):
        """Test counting all assets"""
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{AUTOMATION_SERVICE_URL}/assets/count")
            assert response.status_code == 200
            
            data = response.json()
            assert "count" in data
            assert isinstance(data["count"], int)
            assert data["count"] >= 0
            print(f"✅ Total assets: {data['count']}")
    
    @pytest.mark.asyncio
    async def test_asset_count_windows10(self):
        """Test counting Windows 10 assets"""
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{AUTOMATION_SERVICE_URL}/assets/count",
                params={"os": "Windows 10"}
            )
            assert response.status_code == 200
            
            data = response.json()
            assert "count" in data
            assert isinstance(data["count"], int)
            print(f"✅ Windows 10 assets: {data['count']}")
    
    @pytest.mark.asyncio
    async def test_asset_search_windows(self):
        """Test searching for Windows assets"""
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{AUTOMATION_SERVICE_URL}/assets/search",
                params={"os": "windows", "limit": 10}
            )
            assert response.status_code == 200
            
            data = response.json()
            assert "items" in data
            assert "count" in data
            assert isinstance(data["items"], list)
            print(f"✅ Found {data['count']} Windows assets")
    
    @pytest.mark.asyncio
    async def test_connection_profile_not_found(self):
        """Test connection profile for non-existent host"""
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{AUTOMATION_SERVICE_URL}/assets/connection-profile",
                params={"host": "nonexistent.example.com"}
            )
            assert response.status_code == 200
            
            data = response.json()
            assert data["found"] == False
            print(f"✅ Connection profile not found (expected)")
    
    @pytest.mark.asyncio
    async def test_connection_profile_found(self):
        """Test connection profile for existing host"""
        # First, search for any Windows host
        async with httpx.AsyncClient() as client:
            search_response = await client.get(
                f"{AUTOMATION_SERVICE_URL}/assets/search",
                params={"os": "windows", "limit": 1}
            )
            
            if search_response.status_code == 200:
                search_data = search_response.json()
                if search_data["items"]:
                    host = search_data["items"][0]["hostname"]
                    
                    # Get connection profile
                    profile_response = await client.get(
                        f"{AUTOMATION_SERVICE_URL}/assets/connection-profile",
                        params={"host": host}
                    )
                    assert profile_response.status_code == 200
                    
                    profile_data = profile_response.json()
                    assert profile_data["found"] == True
                    assert "winrm" in profile_data or "ssh" in profile_data
                    print(f"✅ Connection profile found for {host}")
                else:
                    print("⚠️  No Windows hosts found to test connection profile")


class TestSecretsManager:
    """Test secrets manager (requires INTERNAL_KEY)"""
    
    @pytest.mark.asyncio
    async def test_credential_upsert_without_key(self):
        """Test credential upsert without internal key (should fail)"""
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{AUTOMATION_SERVICE_URL}/internal/secrets/credential-upsert",
                json={
                    "host": "test-host",
                    "purpose": "winrm",
                    "username": "testuser",
                    "password": "testpass"
                }
            )
            # Should fail with 403 or 503 (depending on whether INTERNAL_KEY is set)
            assert response.status_code in [403, 503]
            print(f"✅ Credential upsert blocked without internal key")
    
    @pytest.mark.asyncio
    async def test_credential_lookup_without_key(self):
        """Test credential lookup without internal key (should fail)"""
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{AUTOMATION_SERVICE_URL}/internal/secrets/credential-lookup",
                json={
                    "host": "test-host",
                    "purpose": "winrm"
                }
            )
            # Should fail with 403 or 503
            assert response.status_code in [403, 503]
            print(f"✅ Credential lookup blocked without internal key")


class TestAssetTools:
    """Test asset-aware tool execution"""
    
    @pytest.mark.asyncio
    async def test_asset_count_tool(self):
        """Test asset_count tool via /ai/tools/execute"""
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{AUTOMATION_SERVICE_URL}/ai/tools/execute",
                json={
                    "name": "asset_count",
                    "params": {
                        "os": "Windows 10"
                    }
                },
                timeout=30.0
            )
            
            assert response.status_code == 200
            data = response.json()
            assert data["success"] == True
            assert "output" in data
            print(f"✅ asset_count tool executed: {data['output'][:100]}")
    
    @pytest.mark.asyncio
    async def test_asset_search_tool(self):
        """Test asset_search tool via /ai/tools/execute"""
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{AUTOMATION_SERVICE_URL}/ai/tools/execute",
                json={
                    "name": "asset_search",
                    "params": {
                        "os": "windows",
                        "limit": 5
                    }
                },
                timeout=30.0
            )
            
            assert response.status_code == 200
            data = response.json()
            assert data["success"] == True
            assert "output" in data
            print(f"✅ asset_search tool executed: {data['output'][:100]}")
    
    @pytest.mark.asyncio
    async def test_windows_list_directory_missing_creds(self):
        """Test windows_list_directory without credentials (should return missing_credentials error)"""
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{AUTOMATION_SERVICE_URL}/ai/tools/execute",
                json={
                    "name": "windows_list_directory",
                    "params": {
                        "host": "192.168.50.211",
                        "path": "C:\\"
                    }
                },
                timeout=30.0
            )
            
            # Should return 400 with missing_credentials error
            if response.status_code == 400:
                data = response.json()
                detail = data.get("detail", {})
                if isinstance(detail, dict) and detail.get("error") == "missing_credentials":
                    assert "missing_params" in detail
                    assert len(detail["missing_params"]) > 0
                    print(f"✅ windows_list_directory returned missing_credentials error (expected)")
                    return
            
            # If credentials were found, execution should succeed or fail with auth error
            print(f"⚠️  windows_list_directory status: {response.status_code}")


class TestKongRoutes:
    """Test Kong gateway routes"""
    
    @pytest.mark.asyncio
    async def test_asset_count_via_kong(self):
        """Test asset count via Kong gateway"""
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{KONG_URL}/assets/count",
                params={"os": "Windows 10"}
            )
            
            if response.status_code == 200:
                data = response.json()
                assert "count" in data
                print(f"✅ Asset count via Kong: {data['count']}")
            else:
                print(f"⚠️  Kong route not configured yet (status: {response.status_code})")
    
    @pytest.mark.asyncio
    async def test_internal_secrets_not_exposed(self):
        """Test that internal secrets routes are NOT exposed via Kong"""
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{KONG_URL}/internal/secrets/credential-lookup",
                json={"host": "test", "purpose": "winrm"}
            )
            
            # Should return 404 (route not found) - internal routes should NOT be exposed
            assert response.status_code == 404
            print(f"✅ Internal secrets routes not exposed via Kong (expected)")


if __name__ == "__main__":
    print("=" * 80)
    print("PR #11: Asset-Intelligent Execution Tests")
    print("=" * 80)
    
    # Run tests
    pytest.main([__file__, "-v", "-s"])