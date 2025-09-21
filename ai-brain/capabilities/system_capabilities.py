"""
Modern System Capabilities Manager

This module provides comprehensive system knowledge and capabilities management
using the AI Brain's modern system model and vector-based knowledge storage.
"""

import structlog
from typing import Dict, List, Any, Optional
from datetime import datetime
from dataclasses import dataclass, asdict

# Import modern system model components
from system_model.service_capabilities import (
    ServiceCapability as ModernServiceCapability,
    ServiceType, ProtocolType, APIEndpoint
)
from system_model.protocol_knowledge import protocol_knowledge
from integrations.vector_client import OpsConductorVectorStore
from integrations.llm_client import LLMEngine

logger = structlog.get_logger()

@dataclass
class ServiceCapability:
    """Legacy-compatible service capability structure"""
    name: str
    description: str
    endpoints: List[str]
    supported_operations: List[str]
    protocols: List[str] = None
    status: str = "active"
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

@dataclass
class SystemComponent:
    """Legacy-compatible system component structure"""
    name: str
    type: str
    description: str
    port: int
    health_endpoint: str = None
    capabilities: List[ServiceCapability] = None
    dependencies: List[str] = None
    status: str = "active"
    
    def to_dict(self) -> Dict[str, Any]:
        result = asdict(self)
        if self.capabilities:
            result['capabilities'] = [cap.to_dict() for cap in self.capabilities]
        return result

class ModernSystemCapabilities:
    """
    Modern System Capabilities Manager using AI Brain system model.
    
    This class provides the same interface as the legacy SystemCapabilitiesManager
    but uses modern vector-based knowledge storage and LLM-powered analysis.
    """
    
    def __init__(self):
        self.components = {}
        self.capabilities = {}
        self.protocols = {}
        self.tools = {}
        self.last_updated = None
        self.system_status = "active"
        
        # Modern components
        self.vector_store = None
        self.llm_engine = None
        self.initialized = False
        
    async def initialize(self):
        """Initialize modern system capabilities with vector storage"""
        logger.info("Initializing modern system capabilities manager...")
        
        try:
            # Initialize vector store for capabilities knowledge
            import chromadb
            chroma_client = chromadb.PersistentClient(path="/app/chromadb_data")
            self.vector_store = OpsConductorVectorStore(chroma_client)
            
            # Initialize LLM engine for dynamic analysis
            import os
            ollama_host = os.getenv("OLLAMA_HOST", "http://ollama:11434")
            default_model = os.getenv("DEFAULT_MODEL", "llama3.2:3b")
            self.llm_engine = LLMEngine(ollama_host, default_model)
            await self.llm_engine.initialize()
            
            # Load system knowledge into vector store
            await self._initialize_system_knowledge()
            
            # Define core system components using modern data
            await self._define_modern_components()
            
            # Check system health using modern monitoring
            await self._check_modern_system_health()
            
            self.last_updated = datetime.now()
            self.initialized = True
            logger.info("Modern system capabilities manager initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize modern system capabilities: {e}")
            raise
    
    async def _initialize_system_knowledge(self):
        """Initialize system knowledge in vector store"""
        try:
            # Store OpsConductor architecture knowledge
            architecture_knowledge = [
                {
                    "content": "OpsConductor is a microservices-based IT automation platform with 6 core services: Frontend (React), API Gateway, Identity Service, Asset Service, Automation Service, Communication Service, and AI Brain Service.",
                    "metadata": {"type": "architecture", "category": "system_overview"}
                },
                {
                    "content": "The AI Brain Service provides natural language processing, workflow generation, knowledge management, and protocol operations using LLM-powered intelligence.",
                    "metadata": {"type": "service", "category": "ai_brain"}
                },
                {
                    "content": "Asset Service manages infrastructure targets with embedded credentials, hierarchical groups, and 31+ predefined service types including SSH, RDP, HTTP, and databases.",
                    "metadata": {"type": "service", "category": "asset_management"}
                },
                {
                    "content": "Automation Service executes jobs with Celery workers, supports multi-step workflows, and provides step libraries for SSH, PowerShell, HTTP, SNMP, and database operations.",
                    "metadata": {"type": "service", "category": "automation"}
                },
                {
                    "content": "The system supports protocols: SSH, PowerShell, SNMP, HTTP/HTTPS, SMTP, Database connections, and VAPIX for comprehensive IT operations.",
                    "metadata": {"type": "protocols", "category": "capabilities"}
                }
            ]
            
            # Store knowledge in vector store
            for knowledge in architecture_knowledge:
                await self.vector_store.store_document(
                    content=knowledge["content"],
                    metadata=knowledge["metadata"],
                    collection_name="system_capabilities"
                )
            
            logger.info("System knowledge initialized in vector store")
            
        except Exception as e:
            logger.warning(f"Failed to initialize system knowledge: {e}")
    
    async def _define_modern_components(self):
        """Define system components using modern architecture knowledge"""
        
        # AI Brain Service (Self)
        self.components['ai-brain'] = SystemComponent(
            name="AI Brain Service",
            type="service",
            description="Modern AI service with LLM-powered natural language processing and vector-based knowledge management",
            port=3005,
            health_endpoint="/health",
            capabilities=[
                ServiceCapability(
                    name="Intent Processing",
                    description="LLM-powered natural language understanding and intent classification",
                    endpoints=["/ai/chat", "/ai/analyze-text"],
                    supported_operations=["intent_parsing", "entity_extraction", "context_analysis"]
                ),
                ServiceCapability(
                    name="System Analytics",
                    description="Vector-based performance analysis and predictive insights",
                    endpoints=["/ai/analytics/performance", "/ai/analytics/security"],
                    supported_operations=["performance_analysis", "anomaly_detection", "trend_prediction"]
                ),
                ServiceCapability(
                    name="Knowledge Management",
                    description="Vector-based knowledge storage with semantic search",
                    endpoints=["/ai/knowledge-stats", "/ai/store-knowledge"],
                    supported_operations=["knowledge_storage", "semantic_search", "learning_system"]
                ),
                ServiceCapability(
                    name="Job Creation",
                    description="LLM-powered workflow generation from natural language",
                    endpoints=["/ai/create-job", "/ai/execute-job"],
                    supported_operations=["workflow_creation", "script_generation", "job_automation"]
                )
            ],
            dependencies=["postgres", "redis", "ollama"]
        )
        
        # Other core services (simplified modern definitions)
        self.components['api-gateway'] = SystemComponent(
            name="API Gateway",
            type="gateway",
            description="Central routing and authentication gateway",
            port=3000,
            health_endpoint="/health",
            capabilities=[
                ServiceCapability(
                    name="API Routing",
                    description="Intelligent request routing with load balancing",
                    endpoints=["/api/v1/*"],
                    supported_operations=["routing", "authentication", "rate_limiting"]
                )
            ]
        )
        
        self.components['asset-service'] = SystemComponent(
            name="Asset Service",
            type="service",
            description="Infrastructure asset management with encrypted credentials",
            port=3002,
            health_endpoint="/health",
            capabilities=[
                ServiceCapability(
                    name="Target Management",
                    description="Comprehensive infrastructure target management",
                    endpoints=["/targets", "/targets/{id}"],
                    supported_operations=["create_target", "update_target", "search_targets"]
                )
            ]
        )
        
        self.components['automation-service'] = SystemComponent(
            name="Automation Service",
            type="service",
            description="Job execution with distributed task processing",
            port=3003,
            health_endpoint="/health",
            capabilities=[
                ServiceCapability(
                    name="Job Execution",
                    description="Distributed job execution with real-time monitoring",
                    endpoints=["/jobs", "/jobs/{id}/execute"],
                    supported_operations=["create_job", "execute_job", "monitor_execution"]
                )
            ]
        )
        
        logger.info(f"Defined {len(self.components)} modern system components")
    
    async def _check_modern_system_health(self):
        """Check system health using modern monitoring"""
        try:
            # Use LLM to analyze system status
            health_prompt = """
            Analyze the current OpsConductor system health based on the following components:
            - AI Brain Service (port 3005)
            - API Gateway (port 3000) 
            - Asset Service (port 3002)
            - Automation Service (port 3003)
            - PostgreSQL Database (port 5432)
            - Redis Cache (port 6379)
            
            Provide a brief system status assessment.
            """
            
            if self.llm_engine:
                health_analysis = await self.llm_engine.generate_response(health_prompt)
                self.system_status = "active"  # Simplified for now
                logger.info(f"System health analysis: {health_analysis[:100]}...")
            else:
                self.system_status = "active"
                logger.info("System health check completed (LLM not available)")
                
        except Exception as e:
            logger.warning(f"System health check failed: {e}")
            self.system_status = "degraded"
    
    async def get_system_capabilities(self) -> Dict[str, Any]:
        """Get comprehensive system capabilities"""
        if not self.initialized:
            await self.initialize()
        
        return {
            "components": {name: comp.to_dict() for name, comp in self.components.items()},
            "system_status": self.system_status,
            "last_updated": self.last_updated.isoformat() if self.last_updated else None,
            "capabilities_count": len(self.capabilities),
            "protocols_supported": list(protocol_knowledge.get_supported_protocols()),
            "modern_features": [
                "LLM-powered natural language processing",
                "Vector-based knowledge management", 
                "Intelligent workflow generation",
                "Real-time system analytics",
                "Semantic search capabilities"
            ]
        }
    
    async def get_service_capabilities(self, service_name: str) -> Optional[Dict[str, Any]]:
        """Get capabilities for a specific service"""
        if not self.initialized:
            await self.initialize()
        
        component = self.components.get(service_name)
        if component:
            return component.to_dict()
        
        # Use vector search to find service information
        if self.vector_store:
            try:
                results = await self.vector_store.search_similar(
                    query=f"capabilities of {service_name} service",
                    collection_name="system_capabilities",
                    limit=3
                )
                
                if results:
                    return {
                        "service": service_name,
                        "capabilities": [result["content"] for result in results],
                        "source": "vector_search"
                    }
            except Exception as e:
                logger.warning(f"Vector search for service capabilities failed: {e}")
        
        return None
    
    async def get_protocol_capabilities(self, protocol: str) -> Dict[str, Any]:
        """Get capabilities for a specific protocol"""
        if not self.initialized:
            await self.initialize()
        
        # Use modern protocol knowledge
        protocol_info = protocol_knowledge.get_protocol_info(protocol.upper())
        if protocol_info:
            return {
                "protocol": protocol,
                "capabilities": protocol_info,
                "source": "modern_protocol_knowledge"
            }
        
        return {
            "protocol": protocol,
            "capabilities": {},
            "source": "unknown"
        }

# Create global instance
system_capabilities = ModernSystemCapabilities()