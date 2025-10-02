"""
Phase 7: Service Integration Tests
Tests for Asset and Automation service clients
"""

import pytest
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

from execution.services.asset_service_client import (
    AssetServiceClient,
    AssetDetail,
    AssetCredentials,
)
from execution.services.automation_service_client import (
    AutomationServiceClient,
    CommandRequest,
    ExecutionResult,
    WorkflowRequest,
    WorkflowResult,
)


# ============================================================================
# ASSET SERVICE CLIENT TESTS
# ============================================================================

@pytest.mark.asyncio
async def test_asset_client_get_by_id():
    """Test fetching asset by ID"""
    client = AssetServiceClient(base_url="http://test:3001")
    
    # Mock HTTP response
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "success": True,
        "data": {
            "id": 1,
            "name": "test-server",
            "hostname": "test.example.com",
            "ip_address": "192.168.1.100",
            "device_type": "server",
            "os_type": "linux",
            "service_type": "ssh",
            "port": 22,
            "is_secure": True,
            "username": "admin",
            "password": "secret123",
            "status": "active",
            "environment": "production",
            "criticality": "high",
        }
    }
    
    with patch.object(client.client, 'get', return_value=mock_response) as mock_get:
        asset = await client.get_asset_by_id(1)
        
        assert asset is not None
        assert asset.id == 1
        assert asset.name == "test-server"
        assert asset.hostname == "test.example.com"
        assert asset.service_type == "ssh"
        assert asset.username == "admin"
        
        mock_get.assert_called_once_with("/1")
    
    await client.close()


@pytest.mark.asyncio
async def test_asset_client_get_by_hostname():
    """Test fetching asset by hostname"""
    client = AssetServiceClient(base_url="http://test:3001")
    
    # Mock HTTP response
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "success": True,
        "data": [
            {
                "id": 1,
                "name": "test-server",
                "hostname": "test.example.com",
                "ip_address": "192.168.1.100",
                "device_type": "server",
                "os_type": "linux",
                "service_type": "ssh",
                "port": 22,
                "is_secure": True,
                "status": "active",
                "environment": "production",
                "criticality": "high",
            }
        ]
    }
    
    with patch.object(client.client, 'get', return_value=mock_response) as mock_get:
        asset = await client.get_asset_by_hostname("test.example.com")
        
        assert asset is not None
        assert asset.hostname == "test.example.com"
        
        mock_get.assert_called_once()
    
    await client.close()


@pytest.mark.asyncio
async def test_asset_client_query_assets():
    """Test querying assets with filters"""
    client = AssetServiceClient(base_url="http://test:3001")
    
    # Mock HTTP response
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "success": True,
        "data": [
            {
                "id": 1,
                "name": "prod-server-1",
                "hostname": "prod1.example.com",
                "device_type": "server",
                "os_type": "linux",
                "service_type": "ssh",
                "port": 22,
                "status": "active",
                "environment": "production",
                "criticality": "high",
            },
            {
                "id": 2,
                "name": "prod-server-2",
                "hostname": "prod2.example.com",
                "device_type": "server",
                "os_type": "linux",
                "service_type": "ssh",
                "port": 22,
                "status": "active",
                "environment": "production",
                "criticality": "high",
            }
        ]
    }
    
    with patch.object(client.client, 'get', return_value=mock_response) as mock_get:
        assets = await client.query_assets(
            filters={"environment": "production"},
            limit=10
        )
        
        assert len(assets) == 2
        assert all(asset.environment == "production" for asset in assets)
        
        mock_get.assert_called_once()
    
    await client.close()


@pytest.mark.asyncio
async def test_asset_client_get_credentials():
    """Test fetching asset credentials"""
    client = AssetServiceClient(base_url="http://test:3001")
    
    # Mock HTTP response
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "success": True,
        "data": {
            "id": 1,
            "name": "test-server",
            "hostname": "test.example.com",
            "device_type": "server",
            "os_type": "linux",
            "service_type": "ssh",
            "port": 22,
            "credential_type": "password",
            "username": "admin",
            "password": "secret123",
            "status": "active",
            "environment": "production",
            "criticality": "high",
        }
    }
    
    with patch.object(client.client, 'get', return_value=mock_response):
        credentials = await client.get_asset_credentials(1)
        
        assert credentials is not None
        assert credentials.username == "admin"
        assert credentials.password == "secret123"
        assert credentials.credential_type == "password"
    
    await client.close()


@pytest.mark.asyncio
async def test_asset_client_not_found():
    """Test handling asset not found"""
    client = AssetServiceClient(base_url="http://test:3001")
    
    # Mock HTTP response
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "success": False
    }
    
    with patch.object(client.client, 'get', return_value=mock_response):
        asset = await client.get_asset_by_id(999)
        
        assert asset is None
    
    await client.close()


# ============================================================================
# AUTOMATION SERVICE CLIENT TESTS
# ============================================================================

@pytest.mark.asyncio
async def test_automation_client_execute_command():
    """Test executing a command"""
    client = AutomationServiceClient(base_url="http://test:3003")
    
    # Mock HTTP response
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "execution_id": "exec-123",
        "status": "success",
        "command": "ls -la",
        "exit_code": 0,
        "stdout": "total 8\ndrwxr-xr-x 2 user user 4096 Jan 1 00:00 .\n",
        "stderr": "",
        "started_at": "2024-01-01T00:00:00",
        "completed_at": "2024-01-01T00:00:01",
        "duration_seconds": 1.0,
    }
    
    with patch.object(client.client, 'post', return_value=mock_response) as mock_post:
        result = await client.execute_command(
            command="ls -la",
            target_host="test.example.com",
            connection_type="ssh",
            credentials={"username": "admin", "password": "secret"},
        )
        
        assert result.execution_id == "exec-123"
        assert result.status == "success"
        assert result.exit_code == 0
        assert "total 8" in result.stdout
        
        mock_post.assert_called_once()
    
    await client.close()


@pytest.mark.asyncio
async def test_automation_client_execute_workflow():
    """Test executing a workflow"""
    client = AutomationServiceClient(base_url="http://test:3003")
    
    # Mock HTTP response
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "workflow_id": "workflow-123",
        "execution_id": "exec-456",
        "name": "Test Workflow",
        "status": "success",
        "steps_completed": 2,
        "total_steps": 2,
        "step_results": [
            {
                "execution_id": "step-1",
                "status": "success",
                "command": "echo 'step 1'",
                "exit_code": 0,
                "stdout": "step 1\n",
                "stderr": "",
                "started_at": "2024-01-01T00:00:00",
                "completed_at": "2024-01-01T00:00:01",
                "duration_seconds": 1.0,
            },
            {
                "execution_id": "step-2",
                "status": "success",
                "command": "echo 'step 2'",
                "exit_code": 0,
                "stdout": "step 2\n",
                "stderr": "",
                "started_at": "2024-01-01T00:00:01",
                "completed_at": "2024-01-01T00:00:02",
                "duration_seconds": 1.0,
            }
        ],
        "started_at": "2024-01-01T00:00:00",
        "completed_at": "2024-01-01T00:00:02",
        "duration_seconds": 2.0,
    }
    
    with patch.object(client.client, 'post', return_value=mock_response) as mock_post:
        steps = [
            CommandRequest(command="echo 'step 1'"),
            CommandRequest(command="echo 'step 2'"),
        ]
        
        result = await client.execute_workflow(
            workflow_id="workflow-123",
            name="Test Workflow",
            steps=steps,
        )
        
        assert result.workflow_id == "workflow-123"
        assert result.status == "success"
        assert result.steps_completed == 2
        assert result.total_steps == 2
        assert len(result.step_results) == 2
        
        mock_post.assert_called_once()
    
    await client.close()


@pytest.mark.asyncio
async def test_automation_client_get_active_executions():
    """Test fetching active executions"""
    client = AutomationServiceClient(base_url="http://test:3003")
    
    # Mock HTTP response
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "active_executions": [
            {
                "execution_id": "exec-123",
                "status": "running",
                "command": "long-running-command",
                "started_at": "2024-01-01T00:00:00",
            }
        ]
    }
    
    with patch.object(client.client, 'get', return_value=mock_response) as mock_get:
        executions = await client.get_active_executions()
        
        assert len(executions) == 1
        assert executions[0].execution_id == "exec-123"
        assert executions[0].status == "running"
        
        mock_get.assert_called_once_with("/executions/active")
    
    await client.close()


@pytest.mark.asyncio
async def test_automation_client_determine_connection_type():
    """Test determining connection type"""
    client = AutomationServiceClient(base_url="http://test:3003")
    
    # Linux systems
    assert client.determine_connection_type("linux", "ssh") == "ssh"
    assert client.determine_connection_type("ubuntu", "ssh") == "ssh"
    
    # Windows systems
    assert client.determine_connection_type("windows", "winrm") == "powershell"
    assert client.determine_connection_type("windows", "ssh") == "ssh"
    
    # Default
    assert client.determine_connection_type("other", "unknown") == "ssh"
    
    await client.close()


@pytest.mark.asyncio
async def test_automation_client_build_credentials():
    """Test building credentials dictionary"""
    client = AutomationServiceClient(base_url="http://test:3003")
    
    # Password credentials
    creds = client.build_credentials_dict(
        username="admin",
        password="secret123"
    )
    assert creds["username"] == "admin"
    assert creds["password"] == "secret123"
    
    # SSH key credentials
    creds = client.build_credentials_dict(
        username="admin",
        private_key="-----BEGIN RSA PRIVATE KEY-----\n..."
    )
    assert creds["username"] == "admin"
    assert creds["private_key"] == "-----BEGIN RSA PRIVATE KEY-----\n..."
    
    # API key credentials
    creds = client.build_credentials_dict(
        api_key="api-key-123"
    )
    assert creds["api_key"] == "api-key-123"
    
    await client.close()


# ============================================================================
# INTEGRATION TESTS
# ============================================================================

@pytest.mark.asyncio
async def test_service_integration_end_to_end():
    """Test end-to-end service integration"""
    asset_client = AssetServiceClient(base_url="http://test:3001")
    automation_client = AutomationServiceClient(base_url="http://test:3003")
    
    # Mock asset fetch
    mock_asset_response = MagicMock()
    mock_asset_response.status_code = 200
    mock_asset_response.json.return_value = {
        "success": True,
        "data": {
            "id": 1,
            "name": "test-server",
            "hostname": "test.example.com",
            "device_type": "server",
            "os_type": "linux",
            "service_type": "ssh",
            "port": 22,
            "username": "admin",
            "password": "secret123",
            "status": "active",
            "environment": "production",
            "criticality": "high",
        }
    }
    
    # Mock command execution
    mock_exec_response = MagicMock()
    mock_exec_response.status_code = 200
    mock_exec_response.json.return_value = {
        "execution_id": "exec-123",
        "status": "success",
        "command": "uptime",
        "exit_code": 0,
        "stdout": "up 10 days",
        "stderr": "",
        "started_at": "2024-01-01T00:00:00",
        "completed_at": "2024-01-01T00:00:01",
        "duration_seconds": 1.0,
    }
    
    with patch.object(asset_client.client, 'get', return_value=mock_asset_response):
        with patch.object(automation_client.client, 'post', return_value=mock_exec_response):
            # Step 1: Fetch asset
            asset = await asset_client.get_asset_by_id(1)
            assert asset is not None
            
            # Step 2: Build credentials
            credentials = automation_client.build_credentials_dict(
                username=asset.username,
                password=asset.password,
            )
            
            # Step 3: Determine connection type
            connection_type = automation_client.determine_connection_type(
                asset.os_type,
                asset.service_type
            )
            assert connection_type == "ssh"
            
            # Step 4: Execute command
            result = await automation_client.execute_command(
                command="uptime",
                target_host=asset.hostname,
                connection_type=connection_type,
                credentials=credentials,
            )
            
            assert result.status == "success"
            assert result.exit_code == 0
            assert "up 10 days" in result.stdout
    
    await asset_client.close()
    await automation_client.close()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])