"""
Base Query Handler
Common functionality for all query handlers
"""

import logging
from typing import Dict, List, Any
from abc import ABC, abstractmethod

logger = logging.getLogger(__name__)

class BaseQueryHandler(ABC):
    """Base class for all query handlers"""
    
    def __init__(self, service_clients: Dict[str, Any]):
        """
        Initialize with service clients
        
        Args:
            service_clients: Dictionary containing service client instances
                - asset_client: AssetServiceClient
                - automation_client: AutomationServiceClient  
                - communication_client: CommunicationServiceClient
        """
        self.asset_client = service_clients.get('asset_client')
        self.automation_client = service_clients.get('automation_client')
        self.communication_client = service_clients.get('communication_client')
        
    def create_error_response(self, intent: str, error: Exception) -> Dict[str, Any]:
        """Create standardized error response"""
        logger.error(f"{intent} error: {error}")
        return {
            "response": f"❌ Error processing query: {str(error)}",
            "intent": intent,
            "success": False
        }
    
    def create_success_response(self, intent: str, response: str, data: Dict[str, Any] = None) -> Dict[str, Any]:
        """Create standardized success response"""
        return {
            "response": response,
            "intent": intent,
            "success": True,
            "data": data or {}
        }
    
    @abstractmethod
    async def get_supported_intents(self) -> List[str]:
        """Return list of supported intent actions"""
        pass
    
    async def initialize(self):
        """Initialize the handler (optional override)"""
        pass
    
    @abstractmethod
    async def handle_query(self, intent: str, message: str, context: List[Dict]) -> Dict[str, Any]:
        """Handle query based on intent"""
        pass