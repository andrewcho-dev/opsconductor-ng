#!/usr/bin/env python3
"""
Integration tests for the Asset Service

These tests verify the API endpoints with a test database.
"""

import os
import unittest
import asyncio
import json
from unittest.mock import patch, MagicMock, AsyncMock
import sys
from datetime import datetime
import httpx
import pytest
from fastapi.testclient import TestClient

# Add the parent directory to the path so we can import the module
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from main import ConsolidatedAssetService, AssetCreate, AssetUpdate

class TestAssetServiceIntegration(unittest.IsolatedAsyncioTestCase):
    """Integration tests for the Asset Service"""
    
    async def asyncSetUp(self):
        """Set up test fixtures"""
        # Create a mock database pool
        self.mock_pool = MagicMock()
        self.mock_conn = AsyncMock()
        self.mock_pool.acquire.return_value.__aenter__.return_value = self.mock_conn
        
        # Create a mock credential manager
        self.mock_credential_manager = MagicMock()
        self.mock_credential_manager.encrypt_field.side_effect = lambda x: f"encrypted_{x}" if x else None
        self.mock_credential_manager.decrypt_field.side_effect = lambda x: x.replace("encrypted_", "") if x else None
        
        # Create a test asset service
        with patch('main.CredentialManager', return_value=self.mock_credential_manager):
            self.service = ConsolidatedAssetService()
            
        # Replace the database pool with our mock
        self.service.db = MagicMock()
        self.service.db.pool = self.mock_pool
        
        # Create a test client
        self.client = TestClient(self.service.app)
        
        # Test data
        self.test_asset_id = 1
        self.test_asset = {
            "id": self.test_asset_id,
            "name": "Test Server",
            "hostname": "test-server.example.com",
            "ip_address": "192.168.1.100",
            "description": "Test server for unit tests",
            "tags": json.dumps(["test", "server"]),
            "device_type": "server",
            "os_type": "linux",
            "os_version": "Ubuntu 20.04",
            "service_type": "ssh",
            "port": 22,
            "is_secure": True,
            "credential_type": "username_password",
            "username": "test_user",
            "password_encrypted": "encrypted_test_password",
            "private_key_encrypted": None,
            "public_key": None,
            "api_key_encrypted": None,
            "bearer_token_encrypted": None,
            "certificate_encrypted": None,
            "passphrase_encrypted": None,
            "domain": None,
            "database_type": None,
            "database_name": None,
            "secondary_service_type": "none",
            "secondary_port": None,
            "ftp_type": None,
            "secondary_username": None,
            "secondary_password_encrypted": None,
            "additional_services": json.dumps([]),
            "is_active": True,
            "connection_status": "connected",
            "last_tested_at": datetime.now(),
            "notes": "Test notes",
            "created_by": 1,
            "updated_by": None,
            "created_at": datetime.now(),
            "updated_at": None
        }
        
        # Create a test asset for creation
        self.test_asset_create = {
            "name": "New Test Server",
            "hostname": "new-test-server.example.com",
            "ip_address": "192.168.1.101",
            "description": "New test server for integration tests",
            "tags": ["test", "server", "integration"],
            "device_type": "server",
            "os_type": "linux",
            "os_version": "Ubuntu 22.04",
            "service_type": "ssh",
            "port": 22,
            "is_secure": True,
            "credential_type": "username_password",
            "username": "integration_user",
            "password": "integration_password"
        }
    
    async def test_api_get_asset(self):
        """Test the GET /api/v1/assets/{asset_id} endpoint"""
        # Set up the mock to return our test asset
        self.mock_conn.fetchrow.return_value = self.test_asset
        
        # Make the request
        response = self.client.get(f"/api/v1/assets/{self.test_asset_id}")
        
        # Verify the response
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["data"]["id"] == self.test_asset_id
        assert data["data"]["name"] == self.test_asset["name"]
        assert data["data"]["hostname"] == self.test_asset["hostname"]
    
    async def test_api_get_asset_not_found(self):
        """Test the GET /api/v1/assets/{asset_id} endpoint with a non-existent asset"""
        # Set up the mock to return None
        self.mock_conn.fetchrow.return_value = None
        
        # Make the request
        response = self.client.get("/api/v1/assets/999")
        
        # Verify the response
        assert response.status_code == 404
    
    async def test_api_create_asset(self):
        """Test the POST /api/v1/assets endpoint"""
        # Set up the mock to return an asset ID
        self.mock_conn.fetchval.return_value = self.test_asset_id
        
        # Make the request
        response = self.client.post(
            "/api/v1/assets",
            json=self.test_asset_create
        )
        
        # Verify the response
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["data"]["asset_id"] == self.test_asset_id
        
        # Verify that the credential manager was called to encrypt the password
        self.mock_credential_manager.encrypt_field.assert_called_with(self.test_asset_create["password"])
    
    async def test_api_update_asset(self):
        """Test the PUT /api/v1/assets/{asset_id} endpoint"""
        # Set up the mock to return success
        self.mock_conn.execute.return_value = "UPDATE 1"
        
        # Update data
        update_data = {
            "name": "Updated Test Server",
            "description": "Updated description"
        }
        
        # Make the request
        response = self.client.put(
            f"/api/v1/assets/{self.test_asset_id}",
            json=update_data
        )
        
        # Verify the response
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
    
    async def test_api_delete_asset(self):
        """Test the DELETE /api/v1/assets/{asset_id} endpoint"""
        # Set up the mock to return success
        self.mock_conn.execute.return_value = "DELETE 1"
        
        # Make the request
        response = self.client.delete(f"/api/v1/assets/{self.test_asset_id}")
        
        # Verify the response
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
    
    async def test_api_test_connection(self):
        """Test the POST /api/v1/assets/{asset_id}/test endpoint"""
        # Set up the mock to return our test asset
        self.mock_conn.fetchrow.return_value = self.test_asset
        
        # Mock the connection test method
        with patch.object(self.service, '_test_ssh_connection', return_value="connected"):
            # Make the request
            response = self.client.post(f"/api/v1/assets/{self.test_asset_id}/test")
            
            # Verify the response
            assert response.status_code == 200
            data = response.json()
            assert data["success"] is True
            assert data["data"]["connection_status"] == "connected"
            
    async def test_api_test_winrm_connection(self):
        """Test the POST /api/v1/assets/{asset_id}/test endpoint for WinRM"""
        # Create a WinRM test asset
        winrm_test_asset = dict(self.test_asset)
        winrm_test_asset["service_type"] = "winrm"
        winrm_test_asset["port"] = 5985
        winrm_test_asset["domain"] = "example"
        
        # Set up the mock to return our WinRM test asset
        self.mock_conn.fetchrow.return_value = winrm_test_asset
        
        # Mock the connection test method
        with patch.object(self.service, '_test_winrm_connection', return_value="connected"):
            # Make the request
            response = self.client.post(f"/api/v1/assets/{self.test_asset_id}/test")
            
            # Verify the response
            assert response.status_code == 200
            data = response.json()
            assert data["success"] is True
            assert data["data"]["connection_status"] == "connected"
            
        # Test secure WinRM (HTTPS)
        winrm_https_test_asset = dict(winrm_test_asset)
        winrm_https_test_asset["service_type"] = "winrm_https"
        winrm_https_test_asset["port"] = 5986
        winrm_https_test_asset["is_secure"] = True
        
        # Set up the mock to return our WinRM HTTPS test asset
        self.mock_conn.fetchrow.return_value = winrm_https_test_asset
        
        # Mock the connection test method
        with patch.object(self.service, '_test_winrm_connection', return_value="connected"):
            # Make the request
            response = self.client.post(f"/api/v1/assets/{self.test_asset_id}/test")
            
            # Verify the response
            assert response.status_code == 200
            data = response.json()
            assert data["success"] is True
            assert data["data"]["connection_status"] == "connected"
            
    async def test_api_test_rdp_connection(self):
        """Test the POST /api/v1/assets/{asset_id}/test endpoint for RDP"""
        # Create an RDP test asset
        rdp_test_asset = dict(self.test_asset)
        rdp_test_asset["service_type"] = "rdp"
        rdp_test_asset["port"] = 3389
        rdp_test_asset["domain"] = "example"
        
        # Set up the mock to return our RDP test asset
        self.mock_conn.fetchrow.return_value = rdp_test_asset
        
        # Mock the connection test method
        with patch.object(self.service, '_test_rdp_connection', return_value="connected"):
            # Make the request
            response = self.client.post(f"/api/v1/assets/{self.test_asset_id}/test")
            
            # Verify the response
            assert response.status_code == 200
            data = response.json()
            assert data["success"] is True
            assert data["data"]["connection_status"] == "connected"
            
    async def test_api_test_smb_connection(self):
        """Test the POST /api/v1/assets/{asset_id}/test endpoint for SMB"""
        # Create an SMB test asset
        smb_test_asset = dict(self.test_asset)
        smb_test_asset["service_type"] = "smb"
        smb_test_asset["port"] = 445
        smb_test_asset["domain"] = "example"
        
        # Set up the mock to return our SMB test asset
        self.mock_conn.fetchrow.return_value = smb_test_asset
        
        # Mock the connection test method
        with patch.object(self.service, '_test_smb_connection', return_value="connected"):
            # Make the request
            response = self.client.post(f"/api/v1/assets/{self.test_asset_id}/test")
            
            # Verify the response
            assert response.status_code == 200
            data = response.json()
            assert data["success"] is True
            assert data["data"]["connection_status"] == "connected"
            
    async def test_api_test_snmp_connection(self):
        """Test the POST /api/v1/assets/{asset_id}/test endpoint for SNMP"""
        # Create an SNMP test asset
        snmp_test_asset = dict(self.test_asset)
        snmp_test_asset["service_type"] = "snmp"
        snmp_test_asset["port"] = 161
        snmp_test_asset["username"] = "public"  # Community string
        
        # Set up the mock to return our SNMP test asset
        self.mock_conn.fetchrow.return_value = snmp_test_asset
        
        # Mock the connection test method
        with patch.object(self.service, '_test_snmp_connection', return_value="connected"):
            # Make the request
            response = self.client.post(f"/api/v1/assets/{self.test_asset_id}/test")
            
            # Verify the response
            assert response.status_code == 200
            data = response.json()
            assert data["success"] is True
            assert data["data"]["connection_status"] == "connected"
    
    async def test_api_full_flow(self):
        """Test the full API flow: create, get, update, test, delete"""
        # Set up mocks for each operation
        self.mock_conn.fetchval.return_value = self.test_asset_id  # For create
        self.mock_conn.fetchrow.return_value = self.test_asset     # For get and test
        self.mock_conn.execute.side_effect = ["UPDATE 1", "DELETE 1"]  # For update and delete
        
        # 1. Create an asset
        create_response = self.client.post(
            "/api/v1/assets",
            json=self.test_asset_create
        )
        assert create_response.status_code == 200
        create_data = create_response.json()
        asset_id = create_data["data"]["asset_id"]
        
        # 2. Get the asset
        get_response = self.client.get(f"/api/v1/assets/{asset_id}")
        assert get_response.status_code == 200
        
        # 3. Update the asset
        update_data = {"name": "Updated Name"}
        update_response = self.client.put(
            f"/api/v1/assets/{asset_id}",
            json=update_data
        )
        assert update_response.status_code == 200
        
        # 4. Test connection
        with patch.object(self.service, '_test_ssh_connection', return_value="connected"):
            test_response = self.client.post(f"/api/v1/assets/{asset_id}/test")
            assert test_response.status_code == 200
            test_data = test_response.json()
            assert test_data["data"]["connection_status"] == "connected"
            
        # 4.1 Update to WinRM and test that connection
        winrm_update = {
            "service_type": "winrm",
            "port": 5985,
            "domain": "example",
            "username": "winrm_user",
            "password": "winrm_password"
        }
        self.client.put(f"/api/v1/assets/{asset_id}", json=winrm_update)
        
        # Mock the WinRM test asset
        winrm_test_asset = dict(self.test_asset)
        winrm_test_asset["service_type"] = "winrm"
        winrm_test_asset["port"] = 5985
        winrm_test_asset["domain"] = "example"
        winrm_test_asset["username"] = "winrm_user"
        winrm_test_asset["password_encrypted"] = "encrypted_winrm_password"
        self.mock_conn.fetchrow.return_value = winrm_test_asset
        
        # Test WinRM connection
        with patch.object(self.service, '_test_winrm_connection', return_value="connected"):
            winrm_test_response = self.client.post(f"/api/v1/assets/{asset_id}/test")
            assert winrm_test_response.status_code == 200
            winrm_test_data = winrm_test_response.json()
            assert winrm_test_data["data"]["connection_status"] == "connected"
        
        # 5. Delete the asset
        delete_response = self.client.delete(f"/api/v1/assets/{asset_id}")
        assert delete_response.status_code == 200


if __name__ == "__main__":
    unittest.main()