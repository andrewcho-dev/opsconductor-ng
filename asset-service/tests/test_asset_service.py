#!/usr/bin/env python3
"""
Unit tests for the Asset Service
"""

import os
import unittest
from unittest.mock import patch, MagicMock, AsyncMock
import sys
import json
import asyncio
from datetime import datetime

# Add the parent directory to the path so we can import the module
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from main import ConsolidatedAssetService, AssetCreate, AssetUpdate

class TestAssetService(unittest.IsolatedAsyncioTestCase):
    """Test cases for the ConsolidatedAssetService class"""
    
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
    
    async def test_get_asset(self):
        """Test getting an asset by ID"""
        # Set up the mock to return our test asset
        self.mock_conn.fetchrow.return_value = self.test_asset
        
        # Create a mock request context
        with patch.object(self.service.app, 'state'):
            # Call the get_asset endpoint
            result = await self.service.app.routes[0].endpoint(self.test_asset_id)
            
            # Verify the database was queried with the correct parameters
            self.mock_conn.fetchrow.assert_called_once()
            self.assertEqual(self.mock_conn.fetchrow.call_args[0][1], self.test_asset_id)
            
            # Verify the result is correct
            self.assertTrue(result["success"])
            self.assertEqual(result["data"].id, self.test_asset_id)
            self.assertEqual(result["data"].name, self.test_asset["name"])
            self.assertEqual(result["data"].hostname, self.test_asset["hostname"])
    
    async def test_get_asset_not_found(self):
        """Test getting a non-existent asset"""
        # Set up the mock to return None
        self.mock_conn.fetchrow.return_value = None
        
        # Create a mock request context
        with patch.object(self.service.app, 'state'):
            # Call the get_asset endpoint and expect an exception
            with self.assertRaises(Exception) as context:
                await self.service.app.routes[0].endpoint(999)
            
            # Verify the exception is a 404
            self.assertEqual(context.exception.status_code, 404)
    
    async def test_create_asset(self):
        """Test creating a new asset"""
        # Set up the mock to return an asset ID
        self.mock_conn.fetchval.return_value = self.test_asset_id
        
        # Create a test asset
        asset_data = AssetCreate(
            name="Test Server",
            hostname="test-server.example.com",
            ip_address="192.168.1.100",
            description="Test server for unit tests",
            tags=["test", "server"],
            device_type="server",
            os_type="linux",
            os_version="Ubuntu 20.04",
            service_type="ssh",
            port=22,
            is_secure=True,
            credential_type="username_password",
            username="test_user",
            password="test_password"
        )
        
        # Create a mock request context
        with patch.object(self.service.app, 'state'):
            # Call the create_asset endpoint
            result = await self.service.app.routes[1].endpoint(asset_data)
            
            # Verify the database was called
            self.mock_conn.fetchval.assert_called_once()
            
            # Verify the result is correct
            self.assertTrue(result["success"])
            self.assertEqual(result["data"]["asset_id"], self.test_asset_id)
    
    async def test_basic_connection(self):
        """Test the basic connection test method"""
        # Mock the asyncio.open_connection function
        mock_reader = MagicMock()
        mock_writer = MagicMock()
        mock_writer.close = MagicMock()
        mock_writer.wait_closed = AsyncMock()
        
        with patch('asyncio.open_connection', return_value=(mock_reader, mock_writer)):
            # Test a successful connection
            result = await self.service._test_basic_connection("example.com", 80)
            self.assertEqual(result, "connected")
            
            # Test a failed connection
            with patch('asyncio.open_connection', side_effect=ConnectionRefusedError):
                result = await self.service._test_basic_connection("example.com", 80)
                self.assertEqual(result, "failed")


if __name__ == "__main__":
    unittest.main()