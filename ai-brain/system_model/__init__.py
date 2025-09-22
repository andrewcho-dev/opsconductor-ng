"""
OpsConductor System Model - Complete system knowledge and capabilities

This module provides comprehensive knowledge about OpsConductor's architecture,
services, protocols, and operational capabilities for AI-driven automation.
"""

from .service_capabilities import ServiceCapabilitiesManager
from .protocol_knowledge import ProtocolKnowledgeManager  
from .resource_mapper import ResourceMapper
from .workflow_templates import WorkflowTemplateManager
from .asset_mapper import AssetMapper

# Initialize global instances for easy import
service_capabilities = ServiceCapabilitiesManager()
protocol_knowledge = ProtocolKnowledgeManager()
resource_mapper = ResourceMapper()
workflow_templates = WorkflowTemplateManager()
asset_mapper = AssetMapper()

__all__ = [
    'service_capabilities',
    'protocol_knowledge', 
    'resource_mapper',
    'workflow_templates',
    'asset_mapper',
    'ServiceCapabilitiesManager',
    'ProtocolKnowledgeManager',
    'ResourceMapper', 
    'WorkflowTemplateManager',
    'AssetMapper'
]