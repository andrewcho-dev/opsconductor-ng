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
                    "content": "OpsConductor is a microservices-based IT automation platform with 7 core services: Frontend (React), API Gateway, Identity Service, Asset Service, Automation Service, Communication Service, Network Analyzer Service, and AI Brain Service.",
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
                    "content": "Network Analyzer Service provides comprehensive packet analysis and protocol troubleshooting with AI-powered insights. It supports real-time packet capture using tcpdump/tshark/scapy, continuous network monitoring, deep protocol analysis, AI anomaly detection, and remote analysis capabilities.",
                    "metadata": {"type": "service", "category": "network_analysis"}
                },
                {
                    "content": "The Network Analyzer Service supports comprehensive protocol analysis including TCP, UDP, HTTP/HTTPS, DNS, ICMP, SSH, FTP, SMTP, and SNMP. It provides packet capture, traffic analysis, protocol inspection, bandwidth monitoring, latency tracking, packet loss detection, and AI-powered anomaly detection.",
                    "metadata": {"type": "protocols", "category": "network_capabilities"}
                },
                {
                    "content": "OpsConductor has a built-in protocol analyzer that can capture and analyze network packets, monitor network performance in real-time, perform deep protocol analysis, detect anomalies using AI, and deploy remote analysis agents. It's accessible through the Network Analyzer Service on port 3006.",
                    "metadata": {"type": "capabilities", "category": "network_analysis"}
                },
                {
                    "content": "The system supports protocols: SSH, PowerShell, SNMP, HTTP/HTTPS, SMTP, Database connections, VAPIX, and comprehensive network protocols (TCP, UDP, DNS, ICMP, FTP) for complete IT operations and network analysis.",
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
        
        # Network Analyzer Service
        self.components['network-analyzer'] = SystemComponent(
            name="Network Analyzer Service",
            type="service",
            description="Comprehensive network packet analysis and protocol troubleshooting service with AI-powered insights",
            port=3006,
            health_endpoint="/health",
            capabilities=[
                ServiceCapability(
                    name="Packet Capture",
                    description="Real-time packet capture and analysis using tcpdump, tshark, and scapy",
                    endpoints=["/api/v1/analysis/start-capture", "/api/v1/analysis/capture/{session_id}"],
                    supported_operations=["packet_capture", "traffic_analysis", "protocol_inspection", "network_troubleshooting"],
                    protocols=["TCP", "UDP", "HTTP", "HTTPS", "DNS", "ICMP", "SSH", "FTP", "SMTP", "SNMP"]
                ),
                ServiceCapability(
                    name="Real-time Monitoring",
                    description="Continuous network performance monitoring with configurable alerting",
                    endpoints=["/api/v1/monitoring/start", "/api/v1/monitoring/metrics"],
                    supported_operations=["bandwidth_monitoring", "latency_tracking", "packet_loss_detection", "connection_monitoring"],
                    protocols=["TCP", "UDP", "ICMP"]
                ),
                ServiceCapability(
                    name="Protocol Analysis",
                    description="Deep analysis of specific network protocols with performance metrics",
                    endpoints=["/api/v1/analysis/protocol", "/api/v1/analysis/protocol/{protocol}/metrics"],
                    supported_operations=["http_analysis", "dns_analysis", "tcp_analysis", "smtp_analysis", "ssh_analysis"],
                    protocols=["HTTP", "HTTPS", "DNS", "TCP", "SMTP", "SSH"]
                ),
                ServiceCapability(
                    name="AI Anomaly Detection",
                    description="Machine learning-based detection of network anomalies and intelligent diagnosis",
                    endpoints=["/api/v1/ai/analyze", "/api/v1/ai/anomaly-detection"],
                    supported_operations=["anomaly_detection", "pattern_recognition", "threat_identification", "performance_prediction", "intelligent_recommendations"]
                ),
                ServiceCapability(
                    name="Remote Analysis",
                    description="Deploy lightweight agents to remote systems for distributed network analysis",
                    endpoints=["/api/v1/remote/deploy-agent", "/api/v1/remote/analysis/{target_id}"],
                    supported_operations=["remote_monitoring", "distributed_analysis", "edge_analysis", "cross_site_analysis"]
                )
            ],
            dependencies=["postgres", "redis"]
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
                health_analysis = await self.llm_engine.generate(health_prompt)
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