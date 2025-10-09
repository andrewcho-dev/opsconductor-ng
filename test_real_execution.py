#!/usr/bin/env python3
"""
Test Real Execution Logic
Tests the actual execution of communication and asset tools
"""

import asyncio
import json
from datetime import datetime
from typing import Dict, Any

# Mock the services for testing
class MockCommunicationService:
    """Mock communication service for testing"""
    
    def __init__(self):
        self.logger = self
        
    def info(self, msg):
        print(f"[INFO] {msg}")
    
    def error(self, msg, exc_info=False):
        print(f"[ERROR] {msg}")
    
    async def _execute_sendmail_tool(self, inputs: dict) -> dict:
        """Test sendmail execution"""
        print("\n" + "="*80)
        print("TESTING: Sendmail Tool")
        print("="*80)
        print(f"Inputs: {json.dumps(inputs, indent=2)}")
        
        # Simulate SMTP execution
        to_address = inputs.get("to") or inputs.get("recipient")
        subject = inputs.get("subject", "Test")
        body = inputs.get("body") or inputs.get("message", "")
        
        if not to_address:
            result = {
                "success": False,
                "message": "Missing required parameter: 'to' or 'recipient'",
                "error": "Missing recipient address"
            }
        else:
            result = {
                "success": True,
                "message": "Email sent successfully (simulated)",
                "details": {
                    "to": to_address,
                    "subject": subject,
                    "body_length": len(body)
                }
            }
        
        print(f"Result: {json.dumps(result, indent=2)}")
        return result
    
    async def _execute_slack_tool(self, inputs: dict) -> dict:
        """Test Slack execution"""
        print("\n" + "="*80)
        print("TESTING: Slack Tool")
        print("="*80)
        print(f"Inputs: {json.dumps(inputs, indent=2)}")
        
        message = inputs.get("message") or inputs.get("text", "")
        webhook_url = inputs.get("webhook_url", "https://hooks.slack.com/test")
        
        if not message:
            result = {
                "success": False,
                "message": "Missing required parameter: 'message' or 'text'",
                "error": "Missing message content"
            }
        else:
            result = {
                "success": True,
                "message": "Slack message sent successfully (simulated)",
                "details": {
                    "webhook_url": webhook_url[:50] + "...",
                    "message_length": len(message)
                }
            }
        
        print(f"Result: {json.dumps(result, indent=2)}")
        return result
    
    async def _execute_webhook_tool(self, inputs: dict) -> dict:
        """Test webhook execution"""
        print("\n" + "="*80)
        print("TESTING: Webhook Tool")
        print("="*80)
        print(f"Inputs: {json.dumps(inputs, indent=2)}")
        
        url = inputs.get("url") or inputs.get("webhook_url")
        method = inputs.get("method", "POST").upper()
        
        if not url:
            result = {
                "success": False,
                "message": "Missing required parameter: 'url' or 'webhook_url'",
                "error": "Missing URL"
            }
        else:
            result = {
                "success": True,
                "message": f"Webhook sent successfully (simulated)",
                "details": {
                    "url": url,
                    "method": method,
                    "status_code": 200
                }
            }
        
        print(f"Result: {json.dumps(result, indent=2)}")
        return result


class MockAssetService:
    """Mock asset service for testing"""
    
    def __init__(self):
        self.logger = self
        self.mock_assets = {}
        self.next_id = 1
        
    def info(self, msg):
        print(f"[INFO] {msg}")
    
    def error(self, msg, exc_info=False):
        print(f"[ERROR] {msg}")
    
    async def _execute_asset_create_tool(self, inputs: dict) -> dict:
        """Test asset creation"""
        print("\n" + "="*80)
        print("TESTING: Asset Create Tool")
        print("="*80)
        print(f"Inputs: {json.dumps(inputs, indent=2)}")
        
        hostname = inputs.get("hostname")
        
        if not hostname:
            result = {
                "success": False,
                "message": "Missing required parameter: 'hostname'",
                "error": "Hostname is required"
            }
        else:
            asset_id = self.next_id
            self.next_id += 1
            
            asset = {
                "id": asset_id,
                "hostname": hostname,
                "ip_address": inputs.get("ip_address"),
                "type": inputs.get("type", "server"),
                "status": inputs.get("status", "active"),
                "environment": inputs.get("environment", "production")
            }
            
            self.mock_assets[asset_id] = asset
            
            result = {
                "success": True,
                "message": f"Asset '{hostname}' created successfully",
                "asset": asset,
                "asset_id": asset_id
            }
        
        print(f"Result: {json.dumps(result, indent=2)}")
        return result
    
    async def _execute_asset_query_tool(self, inputs: dict) -> dict:
        """Test asset query"""
        print("\n" + "="*80)
        print("TESTING: Asset Query Tool")
        print("="*80)
        print(f"Inputs: {json.dumps(inputs, indent=2)}")
        
        asset_id = inputs.get("asset_id") or inputs.get("id")
        hostname = inputs.get("hostname")
        
        if asset_id:
            asset = self.mock_assets.get(int(asset_id))
            if asset:
                result = {
                    "success": True,
                    "message": f"Found asset with ID {asset_id}",
                    "asset": asset,
                    "count": 1
                }
            else:
                result = {
                    "success": False,
                    "message": f"Asset with ID {asset_id} not found",
                    "count": 0
                }
        elif hostname:
            matching_assets = [a for a in self.mock_assets.values() if hostname.lower() in a["hostname"].lower()]
            result = {
                "success": True,
                "message": f"Found {len(matching_assets)} asset(s)",
                "assets": matching_assets,
                "count": len(matching_assets)
            }
        else:
            result = {
                "success": True,
                "message": f"Found {len(self.mock_assets)} asset(s)",
                "assets": list(self.mock_assets.values()),
                "count": len(self.mock_assets)
            }
        
        print(f"Result: {json.dumps(result, indent=2)}")
        return result
    
    async def _execute_asset_update_tool(self, inputs: dict) -> dict:
        """Test asset update"""
        print("\n" + "="*80)
        print("TESTING: Asset Update Tool")
        print("="*80)
        print(f"Inputs: {json.dumps(inputs, indent=2)}")
        
        asset_id = inputs.get("asset_id") or inputs.get("id")
        
        if not asset_id:
            result = {
                "success": False,
                "message": "Missing required parameter: 'asset_id' or 'id'",
                "error": "Asset identifier required"
            }
        else:
            asset = self.mock_assets.get(int(asset_id))
            if not asset:
                result = {
                    "success": False,
                    "message": f"Asset not found: {asset_id}",
                    "error": "Asset not found"
                }
            else:
                # Update fields
                for key in ["hostname", "ip_address", "type", "status", "environment"]:
                    if key in inputs:
                        asset[key] = inputs[key]
                
                result = {
                    "success": True,
                    "message": "Asset updated successfully",
                    "asset": asset,
                    "asset_id": asset_id
                }
        
        print(f"Result: {json.dumps(result, indent=2)}")
        return result
    
    async def _execute_asset_delete_tool(self, inputs: dict) -> dict:
        """Test asset deletion"""
        print("\n" + "="*80)
        print("TESTING: Asset Delete Tool")
        print("="*80)
        print(f"Inputs: {json.dumps(inputs, indent=2)}")
        
        asset_id = inputs.get("asset_id") or inputs.get("id")
        
        if not asset_id:
            result = {
                "success": False,
                "message": "Missing required parameter: 'asset_id' or 'id'",
                "error": "Asset identifier required"
            }
        else:
            asset = self.mock_assets.pop(int(asset_id), None)
            if asset:
                result = {
                    "success": True,
                    "message": f"Asset '{asset['hostname']}' deleted successfully",
                    "deleted_asset_id": asset["id"],
                    "deleted_hostname": asset["hostname"]
                }
            else:
                result = {
                    "success": False,
                    "message": f"Asset not found: {asset_id}",
                    "error": "Asset not found"
                }
        
        print(f"Result: {json.dumps(result, indent=2)}")
        return result
    
    async def _execute_asset_list_tool(self, inputs: dict) -> dict:
        """Test asset listing"""
        print("\n" + "="*80)
        print("TESTING: Asset List Tool")
        print("="*80)
        print(f"Inputs: {json.dumps(inputs, indent=2)}")
        
        limit = inputs.get("limit", 100)
        offset = inputs.get("offset", 0)
        
        assets = list(self.mock_assets.values())
        paginated_assets = assets[offset:offset+limit]
        
        result = {
            "success": True,
            "message": f"Retrieved {len(paginated_assets)} asset(s)",
            "assets": paginated_assets,
            "count": len(paginated_assets),
            "total": len(assets),
            "limit": limit,
            "offset": offset
        }
        
        print(f"Result: {json.dumps(result, indent=2)}")
        return result


async def test_communication_service():
    """Test communication service tools"""
    print("\n" + "🔵"*40)
    print("COMMUNICATION SERVICE TESTS")
    print("🔵"*40)
    
    service = MockCommunicationService()
    
    # Test 1: Sendmail with valid parameters
    await service._execute_sendmail_tool({
        "to": "admin@example.com",
        "subject": "Test Alert",
        "body": "This is a test email from OpsConductor"
    })
    
    # Test 2: Sendmail with missing recipient
    await service._execute_sendmail_tool({
        "subject": "Test Alert",
        "body": "This should fail"
    })
    
    # Test 3: Slack with valid parameters
    await service._execute_slack_tool({
        "message": "Deployment completed successfully",
        "channel": "#deployments",
        "webhook_url": "https://hooks.slack.com/services/TEST/WEBHOOK/URL"
    })
    
    # Test 4: Slack with missing message
    await service._execute_slack_tool({
        "channel": "#deployments"
    })
    
    # Test 5: Webhook with valid parameters
    await service._execute_webhook_tool({
        "url": "https://api.example.com/notify",
        "method": "POST",
        "payload": {"event": "test", "status": "success"}
    })
    
    # Test 6: Webhook with missing URL
    await service._execute_webhook_tool({
        "method": "POST"
    })


async def test_asset_service():
    """Test asset service tools"""
    print("\n" + "🟢"*40)
    print("ASSET SERVICE TESTS")
    print("🟢"*40)
    
    service = MockAssetService()
    
    # Test 1: Create asset with valid parameters
    result1 = await service._execute_asset_create_tool({
        "hostname": "web-server-01",
        "ip_address": "192.168.1.100",
        "type": "server",
        "environment": "production"
    })
    asset_id_1 = result1.get("asset_id")
    
    # Test 2: Create another asset
    result2 = await service._execute_asset_create_tool({
        "hostname": "db-server-01",
        "ip_address": "192.168.1.101",
        "type": "database",
        "environment": "production"
    })
    asset_id_2 = result2.get("asset_id")
    
    # Test 3: Create asset with missing hostname
    await service._execute_asset_create_tool({
        "ip_address": "192.168.1.102"
    })
    
    # Test 4: Query asset by ID
    await service._execute_asset_query_tool({
        "asset_id": asset_id_1
    })
    
    # Test 5: Query asset by hostname
    await service._execute_asset_query_tool({
        "hostname": "web-server"
    })
    
    # Test 6: Query non-existent asset
    await service._execute_asset_query_tool({
        "asset_id": 999
    })
    
    # Test 7: Update asset
    await service._execute_asset_update_tool({
        "asset_id": asset_id_1,
        "status": "maintenance",
        "environment": "staging"
    })
    
    # Test 8: Update non-existent asset
    await service._execute_asset_update_tool({
        "asset_id": 999,
        "status": "active"
    })
    
    # Test 9: List all assets
    await service._execute_asset_list_tool({
        "limit": 10,
        "offset": 0
    })
    
    # Test 10: Delete asset
    await service._execute_asset_delete_tool({
        "asset_id": asset_id_2
    })
    
    # Test 11: Delete non-existent asset
    await service._execute_asset_delete_tool({
        "asset_id": 999
    })
    
    # Test 12: List assets after deletion
    await service._execute_asset_list_tool({})


async def main():
    """Run all tests"""
    print("\n" + "="*80)
    print("REAL EXECUTION LOGIC TESTS")
    print("="*80)
    print(f"Started at: {datetime.now().isoformat()}")
    print("="*80)
    
    # Test communication service
    await test_communication_service()
    
    # Test asset service
    await test_asset_service()
    
    print("\n" + "="*80)
    print("ALL TESTS COMPLETED")
    print("="*80)
    print(f"Completed at: {datetime.now().isoformat()}")
    print("="*80)
    
    print("\n✅ Summary:")
    print("  • Communication Service: 6 tests (3 tools × 2 scenarios)")
    print("  • Asset Service: 12 tests (5 tools × various scenarios)")
    print("  • Total: 18 test scenarios")
    print("\n📝 Note: These are mock tests. Real tests require:")
    print("  • SMTP server for sendmail")
    print("  • Slack webhook for slack_cli")
    print("  • Teams webhook for teams_cli")
    print("  • Database connection for asset tools")


if __name__ == "__main__":
    asyncio.run(main())