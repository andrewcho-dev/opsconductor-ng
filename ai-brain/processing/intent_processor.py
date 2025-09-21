"""
Modern Intent Processing Engine
LLM-based natural language understanding replacing regex-based patterns
"""

import json
import logging
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict
import structlog

# Import AI Brain components
from integrations.llm_client import LLMEngine
from integrations.vector_client import OpsConductorVectorStore, VectorCollection

logger = structlog.get_logger()

@dataclass
class ParsedRequest:
    """Parsed natural language request with enhanced structure"""
    operation: str  # update, restart, stop, start, install, etc.
    target_process: Optional[str] = None  # stationcontroller.exe, nginx, apache
    target_service: Optional[str] = None  # IIS, Apache, MySQL
    target_group: Optional[str] = None  # CIS servers, web servers, database servers
    target_os: Optional[str] = None  # windows, linux
    package_name: Optional[str] = None  # for package operations
    confidence: float = 0.0
    raw_text: str = ""
    intent_category: str = "unknown"  # system_management, deployment, monitoring, etc.
    parameters: Dict[str, Any] = None  # Additional extracted parameters
    
    def __post_init__(self):
        if self.parameters is None:
            self.parameters = {}
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

@dataclass
class EntityExtraction:
    """Extracted entities from natural language"""
    operations: List[str]
    processes: List[str]
    services: List[str]
    groups: List[str]
    os_hints: List[str]
    parameters: Dict[str, List[str]]
    confidence_scores: Dict[str, float]
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

class IntentProcessor:
    """Modern LLM-based intent processing engine"""
    
    def __init__(self):
        """Initialize the intent processor"""
        self.llm_engine = LLMEngine()
        self.vector_store = OpsConductorVectorStore()
        self.intent_patterns_initialized = False
        
        # Intent categories for classification
        self.intent_categories = {
            'system_management': ['restart', 'stop', 'start', 'status', 'health'],
            'deployment': ['deploy', 'install', 'update', 'upgrade', 'patch'],
            'monitoring': ['check', 'monitor', 'alert', 'report', 'analyze'],
            'maintenance': ['backup', 'cleanup', 'optimize', 'repair', 'maintain'],
            'security': ['scan', 'audit', 'secure', 'encrypt', 'authenticate'],
            'configuration': ['configure', 'setup', 'modify', 'change', 'adjust']
        }
        
        logger.info("Modern Intent Processor initialized")
    
    async def initialize(self):
        """Initialize intent processing patterns"""
        if self.intent_patterns_initialized:
            return
            
        try:
            # Initialize vector store
            await self.vector_store.initialize()
            
            # Load or create intent patterns
            await self._initialize_intent_patterns()
            
            self.intent_patterns_initialized = True
            logger.info("Intent processing patterns initialized")
            
        except Exception as e:
            logger.error("Failed to initialize Intent Processor", error=str(e))
            raise
    
    async def _initialize_intent_patterns(self):
        """Initialize intent patterns in vector store"""
        try:
            # Common IT operations patterns
            intent_patterns = [
                {
                    "pattern": "restart stationcontroller service on CIS servers",
                    "operation": "restart",
                    "target_service": "stationcontroller",
                    "target_group": "CIS servers",
                    "intent_category": "system_management"
                },
                {
                    "pattern": "update all Windows servers with security patches",
                    "operation": "update",
                    "target_os": "windows",
                    "target_group": "all servers",
                    "intent_category": "deployment"
                },
                {
                    "pattern": "install nginx on web servers",
                    "operation": "install",
                    "target_service": "nginx",
                    "target_group": "web servers",
                    "intent_category": "deployment"
                },
                {
                    "pattern": "check status of database services",
                    "operation": "status",
                    "target_group": "database servers",
                    "intent_category": "monitoring"
                },
                {
                    "pattern": "stop Apache service on production servers",
                    "operation": "stop",
                    "target_service": "apache",
                    "target_group": "production servers",
                    "intent_category": "system_management"
                },
                {
                    "pattern": "deploy application to staging environment",
                    "operation": "deploy",
                    "target_group": "staging servers",
                    "intent_category": "deployment"
                },
                {
                    "pattern": "backup database on primary server",
                    "operation": "backup",
                    "target_service": "database",
                    "target_group": "primary server",
                    "intent_category": "maintenance"
                },
                {
                    "pattern": "monitor CPU usage on all Linux servers",
                    "operation": "monitor",
                    "target_os": "linux",
                    "target_group": "all servers",
                    "intent_category": "monitoring"
                },
                {
                    "pattern": "configure firewall rules for web servers",
                    "operation": "configure",
                    "target_group": "web servers",
                    "intent_category": "security"
                },
                {
                    "pattern": "cleanup log files on application servers",
                    "operation": "cleanup",
                    "target_group": "application servers",
                    "intent_category": "maintenance"
                }
            ]
            
            # Store intent patterns in vector store
            for i, pattern in enumerate(intent_patterns):
                await self.vector_store.store_automation_pattern(
                    pattern_id=f"intent_pattern_{i}",
                    pattern_name=f"intent_{pattern['operation']}_{i}",
                    description=pattern['pattern'],
                    metadata={
                        "operation": pattern['operation'],
                        "target_service": pattern.get('target_service'),
                        "target_group": pattern.get('target_group'),
                        "target_os": pattern.get('target_os'),
                        "intent_category": pattern['intent_category'],
                        "type": "intent_pattern"
                    }
                )
            
            logger.info(f"Stored {len(intent_patterns)} intent patterns in vector store")
            
        except Exception as e:
            logger.error("Failed to initialize intent patterns", error=str(e))
            raise
    
    async def parse_request(self, text: str) -> ParsedRequest:
        """Parse natural language request using LLM and vector search"""
        try:
            await self.initialize()
            
            # First, search for similar patterns in vector store
            similar_patterns = await self.vector_store.search_patterns(
                query=text,
                collection=VectorCollection.AUTOMATION_PATTERNS,
                limit=3
            )
            
            # Create LLM prompt with context from similar patterns
            context_patterns = []
            for pattern in similar_patterns:
                if pattern.get('metadata', {}).get('type') == 'intent_pattern':
                    context_patterns.append({
                        "example": pattern.get('content', ''),
                        "operation": pattern.get('metadata', {}).get('operation'),
                        "target_service": pattern.get('metadata', {}).get('target_service'),
                        "target_group": pattern.get('metadata', {}).get('target_group'),
                        "target_os": pattern.get('metadata', {}).get('target_os'),
                        "intent_category": pattern.get('metadata', {}).get('intent_category')
                    })
            
            prompt = f"""
            Parse the following IT operations request and extract structured information:
            
            Request: "{text}"
            
            Similar patterns for context:
            {json.dumps(context_patterns, indent=2)}
            
            Extract the following information:
            1. operation: The main action (restart, stop, start, install, update, deploy, backup, monitor, etc.)
            2. target_process: Specific process name (e.g., stationcontroller.exe, nginx.exe)
            3. target_service: Service name (e.g., IIS, Apache, MySQL, nginx, stationcontroller)
            4. target_group: Server group or environment (e.g., CIS servers, web servers, production servers)
            5. target_os: Operating system hint (windows, linux, or null)
            6. package_name: Package/software name for install operations
            7. intent_category: Category from [system_management, deployment, monitoring, maintenance, security, configuration]
            8. confidence: Confidence score 0.0-1.0
            9. parameters: Additional parameters as key-value pairs
            
            Respond in JSON format:
            {{
                "operation": "<operation>",
                "target_process": "<process_name_or_null>",
                "target_service": "<service_name_or_null>",
                "target_group": "<group_name_or_null>",
                "target_os": "<os_or_null>",
                "package_name": "<package_or_null>",
                "intent_category": "<category>",
                "confidence": <0.0-1.0>,
                "parameters": {{
                    "key": "value"
                }}
            }}
            """
            
            response = await self.llm_engine.generate_response(prompt)
            
            try:
                parsed_data = json.loads(response)
                
                return ParsedRequest(
                    operation=parsed_data.get('operation', 'unknown'),
                    target_process=parsed_data.get('target_process'),
                    target_service=parsed_data.get('target_service'),
                    target_group=parsed_data.get('target_group'),
                    target_os=parsed_data.get('target_os'),
                    package_name=parsed_data.get('package_name'),
                    confidence=float(parsed_data.get('confidence', 0.7)),
                    raw_text=text,
                    intent_category=parsed_data.get('intent_category', 'unknown'),
                    parameters=parsed_data.get('parameters', {})
                )
                
            except (json.JSONDecodeError, ValueError) as e:
                logger.warning("Failed to parse LLM response, using fallback", error=str(e))
                return await self._fallback_parse(text)
                
        except Exception as e:
            logger.error("Failed to parse request", error=str(e))
            return await self._fallback_parse(text)
    
    async def _fallback_parse(self, text: str) -> ParsedRequest:
        """Fallback parsing using simple keyword matching"""
        try:
            text_lower = text.lower()
            
            # Simple operation detection
            operation = "unknown"
            confidence = 0.3
            
            if any(word in text_lower for word in ['restart', 'reboot']):
                operation = "restart"
                confidence = 0.6
            elif any(word in text_lower for word in ['stop', 'kill']):
                operation = "stop"
                confidence = 0.6
            elif any(word in text_lower for word in ['start', 'launch']):
                operation = "start"
                confidence = 0.6
            elif any(word in text_lower for word in ['install', 'deploy']):
                operation = "install"
                confidence = 0.6
            elif any(word in text_lower for word in ['update', 'upgrade']):
                operation = "update"
                confidence = 0.6
            
            # Simple target detection
            target_service = None
            if 'stationcontroller' in text_lower:
                target_service = 'stationcontroller'
                confidence += 0.2
            elif 'nginx' in text_lower:
                target_service = 'nginx'
                confidence += 0.2
            elif 'apache' in text_lower:
                target_service = 'apache'
                confidence += 0.2
            
            # Simple group detection
            target_group = None
            if 'cis servers' in text_lower:
                target_group = 'CIS servers'
                confidence += 0.2
            elif 'web servers' in text_lower:
                target_group = 'web servers'
                confidence += 0.2
            elif 'all servers' in text_lower:
                target_group = 'all servers'
                confidence += 0.2
            
            # Simple OS detection
            target_os = None
            if any(word in text_lower for word in ['windows', 'win']):
                target_os = 'windows'
                confidence += 0.1
            elif any(word in text_lower for word in ['linux', 'ubuntu']):
                target_os = 'linux'
                confidence += 0.1
            
            # Determine intent category
            intent_category = "system_management"
            if operation in ['install', 'deploy', 'update']:
                intent_category = "deployment"
            elif operation in ['monitor', 'check']:
                intent_category = "monitoring"
            
            return ParsedRequest(
                operation=operation,
                target_service=target_service,
                target_group=target_group,
                target_os=target_os,
                confidence=min(confidence, 1.0),
                raw_text=text,
                intent_category=intent_category
            )
            
        except Exception as e:
            logger.error("Fallback parsing failed", error=str(e))
            return ParsedRequest(
                operation="unknown",
                confidence=0.1,
                raw_text=text,
                intent_category="unknown"
            )
    
    async def extract_entities(self, text: str) -> EntityExtraction:
        """Extract all entities from text using LLM analysis"""
        try:
            await self.initialize()
            
            prompt = f"""
            Extract all IT operations entities from the following text:
            
            Text: "{text}"
            
            Extract and categorize:
            1. operations: All action words (restart, stop, start, install, update, etc.)
            2. processes: Process names (stationcontroller.exe, nginx, apache, etc.)
            3. services: Service names (IIS, Apache, MySQL, etc.)
            4. groups: Server groups or environments (CIS servers, web servers, etc.)
            5. os_hints: Operating system references (windows, linux, ubuntu, etc.)
            6. parameters: Additional parameters like versions, paths, configurations
            
            Also provide confidence scores for each category (0.0-1.0).
            
            Respond in JSON format:
            {{
                "operations": ["operation1", "operation2"],
                "processes": ["process1", "process2"],
                "services": ["service1", "service2"],
                "groups": ["group1", "group2"],
                "os_hints": ["os1", "os2"],
                "parameters": {{
                    "versions": ["version1"],
                    "paths": ["path1"],
                    "configs": ["config1"]
                }},
                "confidence_scores": {{
                    "operations": 0.9,
                    "processes": 0.8,
                    "services": 0.7,
                    "groups": 0.6,
                    "os_hints": 0.5
                }}
            }}
            """
            
            response = await self.llm_engine.generate_response(prompt)
            
            try:
                entities_data = json.loads(response)
                
                return EntityExtraction(
                    operations=entities_data.get('operations', []),
                    processes=entities_data.get('processes', []),
                    services=entities_data.get('services', []),
                    groups=entities_data.get('groups', []),
                    os_hints=entities_data.get('os_hints', []),
                    parameters=entities_data.get('parameters', {}),
                    confidence_scores=entities_data.get('confidence_scores', {})
                )
                
            except (json.JSONDecodeError, ValueError) as e:
                logger.warning("Failed to parse entity extraction response", error=str(e))
                return await self._fallback_extract_entities(text)
                
        except Exception as e:
            logger.error("Failed to extract entities", error=str(e))
            return await self._fallback_extract_entities(text)
    
    async def _fallback_extract_entities(self, text: str) -> EntityExtraction:
        """Fallback entity extraction using keyword matching"""
        try:
            text_lower = text.lower()
            
            # Simple keyword-based extraction
            operations = []
            if any(word in text_lower for word in ['restart', 'reboot']):
                operations.append('restart')
            if any(word in text_lower for word in ['stop', 'kill']):
                operations.append('stop')
            if any(word in text_lower for word in ['start', 'launch']):
                operations.append('start')
            if any(word in text_lower for word in ['install', 'deploy']):
                operations.append('install')
            if any(word in text_lower for word in ['update', 'upgrade']):
                operations.append('update')
            
            processes = []
            if 'stationcontroller' in text_lower:
                processes.append('stationcontroller')
            if 'nginx' in text_lower:
                processes.append('nginx')
            if 'apache' in text_lower:
                processes.append('apache')
            
            services = processes.copy()  # For simplicity
            
            groups = []
            if 'cis servers' in text_lower:
                groups.append('CIS servers')
            if 'web servers' in text_lower:
                groups.append('web servers')
            if 'all servers' in text_lower:
                groups.append('all servers')
            
            os_hints = []
            if any(word in text_lower for word in ['windows', 'win']):
                os_hints.append('windows')
            if any(word in text_lower for word in ['linux', 'ubuntu']):
                os_hints.append('linux')
            
            return EntityExtraction(
                operations=operations,
                processes=processes,
                services=services,
                groups=groups,
                os_hints=os_hints,
                parameters={},
                confidence_scores={
                    "operations": 0.6 if operations else 0.0,
                    "processes": 0.6 if processes else 0.0,
                    "services": 0.6 if services else 0.0,
                    "groups": 0.6 if groups else 0.0,
                    "os_hints": 0.6 if os_hints else 0.0
                }
            )
            
        except Exception as e:
            logger.error("Fallback entity extraction failed", error=str(e))
            return EntityExtraction(
                operations=[],
                processes=[],
                services=[],
                groups=[],
                os_hints=[],
                parameters={},
                confidence_scores={}
            )
    
    async def classify_intent(self, text: str) -> Dict[str, Any]:
        """Classify the intent category and confidence"""
        try:
            await self.initialize()
            
            prompt = f"""
            Classify the intent category for this IT operations request:
            
            Request: "{text}"
            
            Categories:
            - system_management: restart, stop, start, status, health checks
            - deployment: deploy, install, update, upgrade, patch operations
            - monitoring: check, monitor, alert, report, analyze activities
            - maintenance: backup, cleanup, optimize, repair, maintain tasks
            - security: scan, audit, secure, encrypt, authenticate operations
            - configuration: configure, setup, modify, change, adjust settings
            
            Respond in JSON format:
            {{
                "intent_category": "<category>",
                "confidence": <0.0-1.0>,
                "reasoning": "<explanation>",
                "secondary_categories": ["<category1>", "<category2>"]
            }}
            """
            
            response = await self.llm_engine.generate_response(prompt)
            
            try:
                classification = json.loads(response)
                return classification
            except (json.JSONDecodeError, ValueError):
                # Fallback classification
                return await self._fallback_classify_intent(text)
                
        except Exception as e:
            logger.error("Failed to classify intent", error=str(e))
            return await self._fallback_classify_intent(text)
    
    async def _fallback_classify_intent(self, text: str) -> Dict[str, Any]:
        """Fallback intent classification"""
        text_lower = text.lower()
        
        # Simple keyword-based classification
        for category, keywords in self.intent_categories.items():
            if any(keyword in text_lower for keyword in keywords):
                return {
                    "intent_category": category,
                    "confidence": 0.6,
                    "reasoning": f"Matched keywords: {keywords}",
                    "secondary_categories": []
                }
        
        return {
            "intent_category": "unknown",
            "confidence": 0.1,
            "reasoning": "No matching keywords found",
            "secondary_categories": []
        }
    
    async def enhance_request_context(self, parsed_request: ParsedRequest) -> Dict[str, Any]:
        """Enhance parsed request with additional context using vector search"""
        try:
            await self.initialize()
            
            # Search for similar requests and their outcomes
            query = f"{parsed_request.operation} {parsed_request.target_service or ''} {parsed_request.target_group or ''}"
            
            similar_patterns = await self.vector_store.search_patterns(
                query=query,
                collection=VectorCollection.AUTOMATION_PATTERNS,
                limit=5
            )
            
            # Extract context from similar patterns
            context = {
                "similar_requests": [],
                "common_parameters": {},
                "success_patterns": [],
                "risk_factors": [],
                "recommendations": []
            }
            
            for pattern in similar_patterns:
                metadata = pattern.get('metadata', {})
                if metadata.get('type') == 'intent_pattern':
                    context["similar_requests"].append({
                        "pattern": pattern.get('content', ''),
                        "operation": metadata.get('operation'),
                        "target": metadata.get('target_service') or metadata.get('target_group')
                    })
            
            # Use LLM to analyze context and provide recommendations
            if context["similar_requests"]:
                prompt = f"""
                Analyze the following request and similar patterns to provide enhanced context:
                
                Current Request:
                - Operation: {parsed_request.operation}
                - Target Service: {parsed_request.target_service}
                - Target Group: {parsed_request.target_group}
                - OS: {parsed_request.target_os}
                
                Similar Patterns:
                {json.dumps(context["similar_requests"], indent=2)}
                
                Provide:
                1. Common parameters needed for this operation
                2. Success patterns and best practices
                3. Potential risk factors to consider
                4. Specific recommendations for execution
                
                Respond in JSON format:
                {{
                    "common_parameters": {{"param1": "value1"}},
                    "success_patterns": ["pattern1", "pattern2"],
                    "risk_factors": ["risk1", "risk2"],
                    "recommendations": ["rec1", "rec2"]
                }}
                """
                
                response = await self.llm_engine.generate_response(prompt)
                
                try:
                    enhanced_context = json.loads(response)
                    context.update(enhanced_context)
                except (json.JSONDecodeError, ValueError):
                    logger.warning("Failed to parse context enhancement response")
            
            return context
            
        except Exception as e:
            logger.error("Failed to enhance request context", error=str(e))
            return {
                "similar_requests": [],
                "common_parameters": {},
                "success_patterns": [],
                "risk_factors": [],
                "recommendations": []
            }

# Global intent processor instance
intent_processor = IntentProcessor()