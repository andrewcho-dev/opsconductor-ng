#!/usr/bin/env python3
"""
Communication Service Client for AI Service
Handles notification queries and communication analytics
"""

import httpx
import asyncio
import structlog
from typing import Dict, Any, Optional, List
from datetime import datetime
import json

# Configure structured logging
logger = structlog.get_logger(__name__)

class CommunicationServiceError(Exception):
    """Raised when communication service operations fail"""
    pass

class CommunicationServiceClient:
    """
    Client for interacting with the OpsConductor Communication Service
    Handles notification queries, audit trails, and communication analytics
    """
    
    def __init__(self, communication_service_url: str = "http://communication-service:3004"):
        self.base_url = communication_service_url.rstrip('/')
        self.timeout = 30.0
        self.max_retries = 3
        
        logger.info("Communication Service Client initialized", 
                   base_url=self.base_url)

    async def health_check(self) -> bool:
        """Check if communication service is healthy"""
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(f"{self.base_url}/health")
                return response.status_code == 200
        except Exception as e:
            logger.warning("Communication service health check failed", error=str(e))
            return False

    async def get_notification_audit(self, limit: int = 100) -> List[Dict[str, Any]]:
        """Get notification audit trail"""
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(
                    f"{self.base_url}/audit",
                    params={'limit': limit, 'order': 'desc'}
                )
                
                if response.status_code != 200:
                    logger.warning("Failed to get notification audit", 
                                  status_code=response.status_code)
                    return []
                
                result = response.json()
                return result.get('audit_records', [])
                
        except Exception as e:
            logger.error("Failed to get notification audit", error=str(e))
            return []

    async def get_notification_templates(self) -> List[Dict[str, Any]]:
        """Get notification templates"""
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(f"{self.base_url}/templates")
                
                if response.status_code != 200:
                    logger.warning("Failed to get notification templates", 
                                  status_code=response.status_code)
                    return []
                
                result = response.json()
                return result.get('templates', [])
                
        except Exception as e:
            logger.error("Failed to get notification templates", error=str(e))
            return []

    async def get_notification_channels(self) -> List[Dict[str, Any]]:
        """Get notification channels"""
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(f"{self.base_url}/channels")
                
                if response.status_code != 200:
                    logger.warning("Failed to get notification channels", 
                                  status_code=response.status_code)
                    return []
                
                result = response.json()
                return result.get('channels', [])
                
        except Exception as e:
            logger.error("Failed to get notification channels", error=str(e))
            return []

    async def get_smtp_settings(self) -> List[Dict[str, Any]]:
        """Get SMTP configuration settings"""
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(f"{self.base_url}/smtp")
                
                if response.status_code != 200:
                    logger.warning("Failed to get SMTP settings", 
                                  status_code=response.status_code)
                    return []
                
                result = response.json()
                return result.get('smtp_settings', [])
                
        except Exception as e:
            logger.error("Failed to get SMTP settings", error=str(e))
            return []

    async def test_smtp_connection(self, smtp_id: int) -> Dict[str, Any]:
        """Test SMTP connection"""
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(
                    f"{self.base_url}/smtp/{smtp_id}/test",
                    json={"test_type": "connection"}
                )
                
                if response.status_code != 200:
                    return {
                        "success": False,
                        "error": f"SMTP test failed: {response.status_code}"
                    }
                
                return response.json()
                
        except Exception as e:
            logger.error("Failed to test SMTP connection", smtp_id=smtp_id, error=str(e))
            return {
                "success": False,
                "error": f"SMTP test error: {str(e)}"
            }

    async def get_notification_statistics(self) -> Dict[str, Any]:
        """Get notification delivery statistics"""
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(f"{self.base_url}/stats")
                
                if response.status_code != 200:
                    logger.warning("Failed to get notification statistics", 
                                  status_code=response.status_code)
                    return {}
                
                return response.json()
                
        except Exception as e:
            logger.error("Failed to get notification statistics", error=str(e))
            return {}

    def get_client_info(self) -> Dict[str, Any]:
        """Get client information"""
        return {
            'name': 'Communication Service Client',
            'version': '1.0.0',
            'description': 'Client for AI Service to Communication Service integration',
            'base_url': self.base_url,
            'capabilities': [
                'Notification audit queries',
                'Template management queries',
                'Channel configuration queries',
                'SMTP settings queries',
                'Delivery statistics',
                'Connection testing'
            ],
            'timeouts': {
                'request_timeout': self.timeout,
                'max_retries': self.max_retries
            }
        }


# Example usage
if __name__ == "__main__":
    async def demo():
        client = CommunicationServiceClient()
        
        print("Communication Service Client Demo")
        print("=" * 50)
        
        # Show client info
        info = client.get_client_info()
        print(f"Client: {info['name']} v{info['version']}")
        print(f"Base URL: {info['base_url']}")
        print(f"Capabilities: {', '.join(info['capabilities'])}")
        
        # Test health check
        healthy = await client.health_check()
        print(f"Communication Service Health: {'✓ Healthy' if healthy else '✗ Unhealthy'}")
        
        print("\nClient ready for AI service integration!")
    
    asyncio.run(demo())