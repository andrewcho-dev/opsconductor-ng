"""
Phase 7: Service Integration
Client libraries for Asset and Automation services
"""

from execution.services.asset_service_client import AssetServiceClient
from execution.services.automation_service_client import AutomationServiceClient

__all__ = [
    "AssetServiceClient",
    "AutomationServiceClient",
]