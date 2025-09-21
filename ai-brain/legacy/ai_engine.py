"""
OpsConductor AI Engine - Modular Architecture
Clean, maintainable AI system with separated query handlers
"""
import asyncio
import logging
import json
import re
from datetime import datetime
from typing import Dict, List, Optional, Any

# Import optional dependencies with fallbacks
try:
    import spacy
    SPACY_AVAILABLE = True
except ImportError:
    SPACY_AVAILABLE = False
    spacy = None

try:
    import ollama
    OLLAMA_AVAILABLE = True
except ImportError:
    OLLAMA_AVAILABLE = False
    ollama = None

try:
    import asyncpg
    ASYNCPG_AVAILABLE = True
except ImportError:
    ASYNCPG_AVAILABLE = False
    asyncpg = None

try:
    import redis.asyncio as redis
    REDIS_AVAILABLE = True
except ImportError:
    REDIS_AVAILABLE = False
    redis = None

# Import core components with fallbacks
try:
    from vector_store import OpsConductorVectorStore
    VECTOR_STORE_AVAILABLE = True
except ImportError:
    VECTOR_STORE_AVAILABLE = False
    OpsConductorVectorStore = None

# Import centralized components
try:
    import sys
    sys.path.append('/app/shared')
    from vector_client import VectorStoreClient, VectorCollection
    from learning_engine import LearningOrchestrator
    from ai_common import Intent, classify_intent
    CENTRALIZED_COMPONENTS = True
except ImportError:
    CENTRALIZED_COMPONENTS = False
    VectorStoreClient = None
    LearningOrchestrator = None

try:
    from protocol_manager import protocol_manager, ProtocolResult
    PROTOCOL_MANAGER_AVAILABLE = True
except ImportError:
    PROTOCOL_MANAGER_AVAILABLE = False
    protocol_manager = None
    ProtocolResult = None

# Import modular query handlers
try:
    from query_handlers import (
        InfrastructureQueryHandler,
        AutomationQueryHandler,
        CommunicationQueryHandler
    )
    QUERY_HANDLERS_AVAILABLE = True
except ImportError:
    QUERY_HANDLERS_AVAILABLE = False
    InfrastructureQueryHandler = None
    AutomationQueryHandler = None
    CommunicationQueryHandler = None

# Import service clients
try:
    from asset_client import AssetServiceClient
    from automation_client import AutomationServiceClient
    from communication_client import CommunicationServiceClient
    SERVICE_CLIENTS_AVAILABLE = True
except ImportError:
    SERVICE_CLIENTS_AVAILABLE = False
    AssetServiceClient = None
    AutomationServiceClient = None
    CommunicationServiceClient = None

# Import system capabilities
try:
    from system_capabilities import system_capabilities
    SYSTEM_CAPABILITIES_AVAILABLE = True
except ImportError:
    SYSTEM_CAPABILITIES_AVAILABLE = False
    system_capabilities = None

logger = logging.getLogger(__name__)

class OpsConductorAI:
    """Modular AI Engine for OpsConductor"""
    
    def __init__(self):
        # Core AI components
        self.nlp = None
        self.ollama_client = None
        self.vector_store = None
        self.db_pool = None
        self.redis_client = None
        self.model_name = "llama2:7b"  # Default Ollama model
        
        # Centralized components
        self.vector_client = None
        self.learning_orchestrator = None
        
        # Service clients
        self.asset_client = None
        self.automation_client = None
        self.communication_client = None
        
        # Query handlers
        self.query_handlers = {}
        
        # System state
        self.initialized = False
        
        # System capabilities
        self.system_capabilities = None
        
    async def initialize(self):
        """Initialize all AI components and handlers"""
        try:
            logger.info("Initializing OpsConductor AI Engine...")
            
            # Initialize NLP
            if SPACY_AVAILABLE:
                try:
                    self.nlp = spacy.load("en_core_web_sm")
                    logger.info("SpaCy model loaded")
                except Exception as e:
                    logger.warning(f"SpaCy initialization failed: {e}")
                    self.nlp = None
            else:
                logger.warning("SpaCy not available")
                self.nlp = None
            
            # Initialize Ollama
            if OLLAMA_AVAILABLE:
                try:
                    import os
                    ollama_host = os.getenv('OLLAMA_HOST', 'http://localhost:11434')
                    self.ollama_client = ollama.AsyncClient(host=ollama_host)
                    logger.info(f"Ollama client initialized with host: {ollama_host}")
                except Exception as e:
                    logger.warning(f"Ollama client initialization failed: {e}")
                    self.ollama_client = None
            else:
                logger.warning("Ollama not available")
                self.ollama_client = None
            
            # Initialize vector store
            if VECTOR_STORE_AVAILABLE:
                try:
                    import chromadb
                    from chromadb.config import Settings
                    # Use persistent storage
                    chroma_client = chromadb.PersistentClient(
                        path="/app/chromadb_data",
                        settings=Settings(anonymized_telemetry=False)
                    )
                    self.vector_store = OpsConductorVectorStore(chroma_client)
                    await self.vector_store.initialize_collections()
                    logger.info("Vector store initialized with persistent storage")
                except Exception as e:
                    logger.warning(f"Vector store initialization failed: {e}")
                    self.vector_store = None
            else:
                logger.warning("Vector store not available")
                self.vector_store = None
            
            # Initialize database connection
            if ASYNCPG_AVAILABLE:
                try:
                    self.db_pool = await asyncpg.create_pool(
                        host="postgres",
                        port=5432,
                        user="postgres",
                        password="postgres123",
                        database="opsconductor",
                        min_size=2,
                        max_size=10
                    )
                    logger.info("Database pool created")
                except Exception as e:
                    logger.warning(f"Database connection failed: {e}")
                    self.db_pool = None
            else:
                logger.warning("AsyncPG not available")
                self.db_pool = None
            
            # Initialize Redis connection
            if REDIS_AVAILABLE:
                try:
                    self.redis_client = redis.Redis(
                        host="redis",
                        port=6379,
                        decode_responses=True
                    )
                    await self.redis_client.ping()
                    logger.info("Redis connection established")
                except Exception as e:
                    logger.warning(f"Redis connection failed: {e}")
                    self.redis_client = None
            else:
                logger.warning("Redis not available")
                self.redis_client = None
            
            # Initialize centralized components
            if CENTRALIZED_COMPONENTS:
                try:
                    # Use centralized vector client instead of local store
                    self.vector_client = VectorStoreClient("http://ai-brain:3000")
                    logger.info("Centralized vector client initialized")
                    
                    # Initialize learning orchestrator
                    self.learning_orchestrator = LearningOrchestrator(
                        vector_service_url="http://ai-brain:3000",
                        redis_client=self.redis_client
                    )
                    await self.learning_orchestrator.start_background_tasks()
                    logger.info("Learning orchestrator initialized")
                except Exception as e:
                    logger.warning(f"Centralized components initialization failed: {e}")
            
            # Initialize service clients
            if SERVICE_CLIENTS_AVAILABLE:
                try:
                    self.asset_client = AssetServiceClient()
                    self.automation_client = AutomationServiceClient()
                    self.communication_client = CommunicationServiceClient()
                    logger.info("Service clients initialized")
                except Exception as e:
                    logger.warning(f"Service client initialization failed: {e}")
            else:
                logger.warning("Service clients not available")
            
            # Initialize query handlers
            await self._initialize_query_handlers()
            
            # Initialize system capabilities
            if SYSTEM_CAPABILITIES_AVAILABLE:
                try:
                    self.system_capabilities = system_capabilities
                    await self.system_capabilities.initialize()
                    logger.info("System capabilities initialized")
                except Exception as e:
                    logger.warning(f"System capabilities initialization failed: {e}")
            else:
                logger.warning("System capabilities not available")
            
            self.initialized = True
            logger.info("AI Engine initialization completed successfully")
            return True
            
        except Exception as e:
            logger.error(f"AI Engine initialization failed: {e}")
            self.initialized = False
            return False
    
    async def _initialize_query_handlers(self):
        """Initialize modular query handlers"""
        try:
            # Create shared context for all handlers
            shared_context = {
                'db_pool': self.db_pool,
                'redis_client': self.redis_client,
                'vector_store': self.vector_store,
                'asset_client': self.asset_client,
                'automation_client': self.automation_client,
                'communication_client': self.communication_client,
                'protocol_manager': protocol_manager if PROTOCOL_MANAGER_AVAILABLE else None
            }
            
            # Initialize handlers
            self.query_handlers = {}
            if QUERY_HANDLERS_AVAILABLE:
                self.query_handlers = {
                    'infrastructure': InfrastructureQueryHandler(shared_context),
                    'automation': AutomationQueryHandler(shared_context),
                    'communication': CommunicationQueryHandler(shared_context)
                }
            else:
                logger.warning("Query handlers not available, using fallback mode")
            
            # Initialize each handler
            for name, handler in self.query_handlers.items():
                try:
                    await handler.initialize()
                    logger.info(f"Query handler '{name}' initialized")
                except Exception as e:
                    logger.warning(f"Query handler '{name}' initialization failed: {e}")
            
            logger.info("All query handlers initialized")
            
        except Exception as e:
            logger.error(f"Query handler initialization failed: {e}")
            raise
    
    async def process_message(self, message: str, context: List[Dict] = None) -> Dict[str, Any]:
        """Process incoming message and route to appropriate handler"""
        try:
            if not self.initialized:
                await self.initialize()
            
            if context is None:
                context = []
            
            logger.info(f"Processing message: {message[:100]}...")
            
            # Classify intent using AI
            intent_result = await self.classify_intent(message)
            intent_action = intent_result.get("intent", "request_help")
            confidence = intent_result.get("confidence", 0.0)
            reasoning = intent_result.get("reasoning", "No reasoning provided")
            method = intent_result.get("method", "unknown")
            
            logger.info(f"Intent classified: {intent_action} (confidence: {confidence:.2f}) via {method}")
            logger.info(f"Reasoning: {reasoning}")
            
            # EXCEPTION TRACKING: Log low confidence classifications for review
            if confidence < 0.5:
                logger.warning(f"LOW CONFIDENCE intent classification: {intent_action} ({confidence:.2f}) for message: '{message[:100]}...'")
                logger.warning(f"Reasoning: {reasoning}")
                
            # Log successful AI classifications for monitoring
            if method == "ai_classification":
                logger.info(f"✅ AI successfully classified intent: {intent_action} with {confidence:.2f} confidence")
            
            # Route to appropriate handler
            response = await self._route_to_handler(message, context, intent_action)
            
            # Add metadata
            response["intent_classification"] = intent_result
            response["timestamp"] = datetime.now().isoformat()
            
            # Store interaction for learning
            await self.store_interaction(message, response, context)
            
            return response
            
        except Exception as e:
            logger.error(f"Message processing failed: {e}")
            return {
                "response": f"❌ **Processing Error**: {str(e)}",
                "intent": "error",
                "success": False,
                "error": str(e)
            }
    
    async def _route_to_handler(self, message: str, context: List[Dict], intent_action: str) -> Dict[str, Any]:
        """Route message to appropriate query handler"""
        try:
            # Infrastructure-related intents
            infrastructure_intents = [
                "query_targets", "create_target", "update_target", "delete_target",
                "query_target_groups", "query_targets_by_tag", "query_target_tags",
                "manage_target_tags", "query_connection_status", "test_connection",
                "manage_credentials", "query_schema_info", "query_table_structure",
                "query_database_search", "query_column_info", "query_relationships",
                "query_database_summary"
            ]
            
            # Automation-related intents
            automation_intents = [
                "query_jobs", "create_job", "execute_job", "stop_job",
                "query_workflows", "create_workflow", "query_task_queue",
                "query_schedules", "query_error_analysis", "execute_command",
                "execute_powershell", "execute_bash", "remote_execution",
                "manage_services", "query_system_info", "file_operations",
                "snmp_operations", "camera_operations", "generate_script",
                "generate_powershell_script", "generate_bash_script"
            ]
            
            # Communication-related intents
            communication_intents = [
                "query_notification_history", "send_notification", "query_notification_audit",
                "manage_templates", "manage_channels", "email_operations"
            ]
            
            # Self-awareness and system intents
            system_intents = [
                "system_capabilities", "system_status", "what_can_you_do", "help_general",
                "system_overview", "protocol_info", "component_info", "can_perform_operation"
            ]
            
            # Route to appropriate handler
            if intent_action in infrastructure_intents:
                handler = self.query_handlers.get('infrastructure')
                if handler:
                    return await handler.handle_query(intent_action, message, context)
            
            elif intent_action in automation_intents:
                handler = self.query_handlers.get('automation')
                if handler:
                    return await handler.handle_query(intent_action, message, context)
            
            elif intent_action in communication_intents:
                handler = self.query_handlers.get('communication')
                if handler:
                    return await handler.handle_query(intent_action, message, context)
            
            elif intent_action in system_intents:
                return await self._handle_system_query(message, context, intent_action)
            
            # Handle general queries and other intents
            return await self._handle_general_query(message, context, intent_action)
            
        except Exception as e:
            logger.error(f"Handler routing failed: {e}")
            return {
                "response": f"❌ **Routing Error**: {str(e)}",
                "intent": intent_action,
                "success": False
            }
    
    async def classify_intent(self, message: str) -> Dict[str, Any]:
        """Classify user intent using AI-powered analysis"""
        try:
            # Use AI-powered intent classification instead of regex patterns
            return await self._ai_classify_intent(message)
            
        except Exception as e:
            logger.error(f"Intent classification failed: {e}")
            # Fallback to basic classification
            return await self._fallback_classify_intent(message)
    
    async def _ai_classify_intent(self, message: str) -> Dict[str, Any]:
        """Use Ollama AI to classify user intent with high accuracy"""
        try:
            if not self.ollama_client or not OLLAMA_AVAILABLE:
                logger.warning("Ollama not available, using fallback classification")
                return await self._enhanced_fallback_classify_intent(message)
            
            # Define the available intents and their descriptions
            intent_definitions = {
                "knowledge_query": "User wants to learn something, get help, understand concepts, or get examples/scripts/code. Keywords: what, how, explain, help, write, create, show me, give me, example, script, code, tutorial, guide",
                "query_targets": "User wants to see available servers, machines, endpoints, or infrastructure targets",
                "create_target": "User wants to add/register a new server or target machine",
                "query_target_tags": "User wants to see tags, labels, or categories for organizing targets",
                "query_connection_status": "User wants to check connectivity, ping status, or if machines are online/offline",
                "query_jobs": "User wants to see automation jobs, tasks, executions, or their status (running, failed, completed)",
                "query_workflows": "User wants to see workflows, automation processes, or workflow definitions",
                "query_error_analysis": "User wants to analyze errors, failures, or troubleshoot issues",
                "execute_command": "User wants to run a specific command on a target machine (with target specified)",
                "execute_powershell": "User wants to execute PowerShell commands or scripts on Windows machines",
                "execute_bash": "User wants to execute bash/shell commands on Linux/Unix machines",
                "remote_execution": "User wants to execute commands remotely on specific IP addresses or hostnames",
                "create_job": "User wants to create a new automation job or task",
                "execute_job": "User wants to run/start an existing job",
                "stop_job": "User wants to stop/cancel a running job",
                "send_notification": "User wants to send notifications, alerts, or messages",
                "query_notification_history": "User wants to see notification history or logs",
                "query_schema_info": "User wants to see database schema, tables, or data structure information",
                "system_capabilities": "User wants to know what the AI system can do, its capabilities, or features",
                "system_status": "User wants to check system health, component status, or overall system state",
                "protocol_info": "User wants information about supported protocols (SSH, SNMP, HTTP, etc.)",
                "component_info": "User wants details about system components or services",
                "can_perform_operation": "User is asking if the system can perform a specific operation",
                "provide_greeting": "User is greeting or saying hello",
                "request_help": "User is asking for general help or assistance"
            }
            
            # Create a sophisticated AI prompt for intent classification
            prompt = f"""CRITICAL: You MUST respond with ONLY valid JSON. No explanations, no markdown, no extra text.

Analyze this message: "{message}"

Available intents:
- knowledge_query: User wants to learn, get help, scripts, code, examples
- query_targets: User wants to see servers/machines/endpoints
- create_target: User wants to add/register new server
- query_target_tags: User wants to see tags/labels/categories
- query_connection_status: User wants to check connectivity/ping status
- query_jobs: User wants to see automation jobs/tasks/status
- query_workflows: User wants to see workflows/automation processes
- query_error_analysis: User wants to analyze errors/troubleshoot
- execute_command: User wants to run command on specific target
- execute_powershell: User wants to execute PowerShell commands
- execute_bash: User wants to execute bash/shell commands
- remote_execution: User wants to execute on specific IP/hostname
- create_job: User wants to create new automation job
- execute_job: User wants to run/start existing job
- stop_job: User wants to stop/cancel running job
- send_notification: User wants to send notifications/alerts
- query_notification_history: User wants to see notification history
- query_schema_info: User wants database schema/table info
- system_capabilities: User asks "what can you do", capabilities, features
- system_status: User asks system health, component status, "system status"
- protocol_info: User wants protocol information (SSH, SNMP, HTTP, etc.)
- component_info: User wants system component/service details
- can_perform_operation: User asks "can you", "are you able", "do you support"
- provide_greeting: User greeting (hello, hi, thanks)
- request_help: User needs general help/assistance

Classification rules:
1. "what can you do", "capabilities", "features" → system_capabilities
2. "system status", "health", "component status" → system_status
3. "what is", "how to", "explain", "help understand" → knowledge_query
4. "show", "list", "display" + system resources → appropriate query_* intent

Respond with ONLY this JSON (no other text):
{{
    "intent": "exact_intent_name",
    "confidence": 0.85,
    "reasoning": "Brief reason"
}}"""

            # Get AI response
            if self.ollama_client:
                response = await self.ollama_client.chat(
                    model=self.model_name,
                    messages=[{"role": "user", "content": prompt}],
                    options={"temperature": 0.1}  # Low temperature for consistent classification
                )
                
                ai_response = response['message']['content'].strip()
                
                # Parse the JSON response
                import json
                try:
                    result = json.loads(ai_response)
                    intent = result.get("intent", "request_help")
                    confidence = result.get("confidence", 0.5)
                    reasoning = result.get("reasoning", "AI classification")
                    
                    # Validate intent exists
                    if intent not in intent_definitions:
                        logger.warning(f"AI returned unknown intent: {intent}, falling back to request_help")
                        intent = "request_help"
                        confidence = 0.3
                    
                    logger.info(f"AI Intent Classification: {intent} (confidence: {confidence}) - {reasoning}")
                    
                    return {
                        "intent": intent,
                        "confidence": confidence,
                        "reasoning": reasoning,
                        "method": "ai_classification"
                    }
                    
                except json.JSONDecodeError as e:
                    logger.error(f"Failed to parse AI response as JSON: {ai_response}")
                    
                    # Try to extract JSON from response if it contains extra text
                    import re
                    json_match = re.search(r'\{[^{}]*\}', ai_response)
                    if json_match:
                        try:
                            result = json.loads(json_match.group())
                            intent = result.get("intent", "request_help")
                            confidence = result.get("confidence", 0.5)
                            reasoning = result.get("reasoning", "Extracted JSON from response")
                            
                            if intent in intent_definitions:
                                logger.info(f"Extracted JSON Intent: {intent} (confidence: {confidence})")
                                return {
                                    "intent": intent,
                                    "confidence": confidence,
                                    "reasoning": reasoning,
                                    "method": "ai_classification_extracted"
                                }
                        except json.JSONDecodeError:
                            pass
                    
                    # Try to extract intent from response text based on keywords
                    message_lower = message.lower()
                    ai_response_lower = ai_response.lower()
                    
                    # Check for system-related queries first (highest priority)
                    if any(phrase in message_lower for phrase in ["what can you do", "capabilities", "features", "what are you capable", "system overview"]):
                        return {
                            "intent": "system_capabilities",
                            "confidence": 0.8,
                            "reasoning": "Detected system capabilities query",
                            "method": "keyword_fallback"
                        }
                    
                    if any(phrase in message_lower for phrase in ["system status", "health", "component status", "are services running"]):
                        return {
                            "intent": "system_status",
                            "confidence": 0.8,
                            "reasoning": "Detected system status query",
                            "method": "keyword_fallback"
                        }
                    
                    # Try to extract intent from response text
                    for intent_name in intent_definitions.keys():
                        if intent_name in ai_response_lower:
                            return {
                                "intent": intent_name,
                                "confidence": 0.6,
                                "reasoning": "Extracted from AI response text",
                                "method": "ai_classification_fallback"
                            }
                    
                    # Final fallback
                    return {
                        "intent": "request_help",
                        "confidence": 0.3,
                        "reasoning": "JSON parsing failed, using fallback",
                        "method": "error_fallback"
                    }
            
            # If no Ollama client, fall back
            return await self._fallback_classify_intent(message)
            
        except Exception as e:
            logger.error(f"AI intent classification failed: {e}")
            return await self._fallback_classify_intent(message)
    
    async def _enhanced_fallback_classify_intent(self, message: str) -> Dict[str, Any]:
        """Enhanced fallback intent classification with smart pattern matching"""
        try:
            message_lower = message.lower()
            
            # High-priority patterns (check these first)
            
            # 1. Script/Code requests (highest priority)
            script_indicators = ["write", "create", "show me", "give me"]
            script_targets = ["script", "code", "example", "powershell", "bash", "python"]
            if (any(indicator in message_lower for indicator in script_indicators) and 
                any(target in message_lower for target in script_targets)):
                return {
                    "intent": "knowledge_query",
                    "confidence": 0.95,
                    "reasoning": "Detected script/code creation request",
                    "method": "enhanced_fallback_pattern_matching"
                }
            
            # 2. Directory/file listing with specific target (remote execution)
            if (any(term in message_lower for term in ["get directory", "list directory", "show directory", "dir of", "ls of"]) and
                any(char.isdigit() for char in message)):  # Contains IP or numbers
                return {
                    "intent": "remote_execution",
                    "confidence": 0.90,
                    "reasoning": "Directory listing request with target specified",
                    "method": "enhanced_fallback_pattern_matching"
                }
            
            # 3. Knowledge queries
            knowledge_patterns = ["what is", "how to", "explain", "help me understand", "tell me about", "what does", "do you have knowledge", "do you know about", "knowledge of"]
            if any(pattern in message_lower for pattern in knowledge_patterns):
                return {
                    "intent": "knowledge_query",
                    "confidence": 0.85,
                    "reasoning": "Knowledge/learning request detected",
                    "method": "enhanced_fallback_pattern_matching"
                }
            
            # 4. Target queries
            target_patterns = ["show targets", "list targets", "available targets", "what targets", "show servers", "list servers"]
            if any(pattern in message_lower for pattern in target_patterns):
                return {
                    "intent": "query_targets",
                    "confidence": 0.90,
                    "reasoning": "Target listing request detected",
                    "method": "enhanced_fallback_pattern_matching"
                }
            
            # 5. Execution with specific target
            if (any(term in message_lower for term in ["run", "execute", "get", "invoke"]) and
                (any(char.isdigit() for char in message) or "server" in message_lower)):
                return {
                    "intent": "remote_execution",
                    "confidence": 0.85,
                    "reasoning": "Execution request with target detected",
                    "method": "enhanced_fallback_pattern_matching"
                }
            
            # 6. Job queries
            job_patterns = ["show jobs", "list jobs", "job status", "running jobs", "failed jobs"]
            if any(pattern in message_lower for pattern in job_patterns):
                return {
                    "intent": "query_jobs",
                    "confidence": 0.85,
                    "reasoning": "Job query request detected",
                    "method": "enhanced_fallback_pattern_matching"
                }
            
            # 7. Greetings
            greeting_patterns = ["hello", "hi", "hey", "good morning", "good afternoon", "thanks", "thank you"]
            if any(pattern in message_lower for pattern in greeting_patterns):
                return {
                    "intent": "provide_greeting",
                    "confidence": 0.95,
                    "reasoning": "Greeting detected",
                    "method": "enhanced_fallback_pattern_matching"
                }
            
            # 8. System capabilities
            capability_patterns = ["what can you do", "capabilities", "features", "what are you capable of", "system overview", "what do you support"]
            if any(pattern in message_lower for pattern in capability_patterns):
                return {
                    "intent": "system_capabilities",
                    "confidence": 0.90,
                    "reasoning": "System capabilities request detected",
                    "method": "enhanced_fallback_pattern_matching"
                }
            
            # 9. System status
            status_patterns = ["system status", "health check", "component status", "system health", "are services running", "service status"]
            if any(pattern in message_lower for pattern in status_patterns):
                return {
                    "intent": "system_status",
                    "confidence": 0.90,
                    "reasoning": "System status request detected",
                    "method": "enhanced_fallback_pattern_matching"
                }
            
            # 10. Protocol information
            protocol_patterns = ["protocol", "ssh", "snmp", "http", "powershell", "supported protocols", "what protocols"]
            if any(pattern in message_lower for pattern in protocol_patterns):
                return {
                    "intent": "protocol_info",
                    "confidence": 0.85,
                    "reasoning": "Protocol information request detected",
                    "method": "enhanced_fallback_pattern_matching"
                }
            
            # 11. Component information
            component_patterns = ["component", "service", "asset service", "automation service", "identity service", "component details"]
            if any(pattern in message_lower for pattern in component_patterns):
                return {
                    "intent": "component_info",
                    "confidence": 0.85,
                    "reasoning": "Component information request detected",
                    "method": "enhanced_fallback_pattern_matching"
                }
            
            # 12. Can perform operation
            capability_check_patterns = ["can you", "are you able", "do you support", "can i", "is it possible", "are you capable of"]
            if any(pattern in message_lower for pattern in capability_check_patterns):
                return {
                    "intent": "can_perform_operation",
                    "confidence": 0.85,
                    "reasoning": "Capability check request detected",
                    "method": "enhanced_fallback_pattern_matching"
                }
            
            # 13. General help requests
            help_patterns = ["help", "assistance", "how does this work", "guide me"]
            if any(pattern in message_lower for pattern in help_patterns):
                return {
                    "intent": "request_help",
                    "confidence": 0.80,
                    "reasoning": "General help request detected",
                    "method": "enhanced_fallback_pattern_matching"
                }
            
            # Default fallback
            return {
                "intent": "request_help",
                "confidence": 0.50,
                "reasoning": "No specific pattern matched, defaulting to help",
                "method": "enhanced_fallback_default"
            }
            
        except Exception as e:
            logger.error(f"Enhanced fallback classification error: {e}")
            return {
                "intent": "request_help",
                "confidence": 0.30,
                "reasoning": f"Error in enhanced fallback: {str(e)}",
                "method": "error_fallback"
            }

    async def _fallback_classify_intent(self, message: str) -> Dict[str, Any]:
        """Fallback intent classification using improved pattern matching"""
        try:
            message_lower = message.lower()
            
            # Improved pattern-based classification as fallback
            intent_patterns = {
                # Knowledge and Help Queries (Check FIRST for "what is", "how to", "explain", etc.)
                "knowledge_query": {
                    "patterns": [
                        r"what\s+(is|are)\s+", r"how\s+(to|do|does|can)\s+", r"explain\s+", r"tell\s+me\s+about",
                        r"describe\s+", r"define\s+", r"help\s+(with|me)", r"tutorial", r"guide\s+",
                        r"difference\s+between", r"when\s+should", r"why\s+(is|does|should)",
                        r"teach\s+me", r"learn\s+about", r"what.*subnet", r"subnet.*mask",
                        r"network.*address", r"ip.*address", r"cidr", r"netmask",
                        r"write\s+(me\s+)?a?\s*(powershell\s+)?script", r"create\s+(a\s+)?script", 
                        r"show\s+me\s+(a\s+)?script", r"give\s+me\s+(a\s+)?script", r"need\s+(a\s+)?script",
                        r"script\s+to", r"code\s+to", r"example\s+of", r"sample\s+script"
                    ],
                    "keywords": ["what", "how", "explain", "tell", "describe", "define", "help", "tutorial", 
                                "guide", "difference", "learn", "teach", "understand", "concept", "theory",
                                "subnet", "mask", "network", "cidr", "netmask", "ip", "address", "write", 
                                "create", "script", "code", "example", "sample", "show", "give", "need"],
                    "confidence": 0.98
                },
                # Infrastructure Management
                "query_targets": {
                    "patterns": [r"targets?", r"servers?", r"machines?", r"endpoints?", r"hosts?", r"show.*targets", r"list.*targets"],
                    "keywords": ["target", "server", "machine", "endpoint", "host", "windows", "linux", "macos", "show", "list"],
                    "confidence": 0.8
                },
                "create_target": {
                    "patterns": [r"create.*target", r"add.*target", r"new.*target", r"register.*target"],
                    "keywords": ["create", "add", "new", "register", "target", "server", "machine"],
                    "confidence": 0.9
                },
                "query_target_tags": {
                    "patterns": [r"tags?", r"labels?", r"categories?", r"tag.list", r"all.tags"],
                    "keywords": ["tag", "tags", "label", "labels", "category", "organize", "list", "show"],
                    "confidence": 0.8
                },
                "query_connection_status": {
                    "patterns": [r"connection", r"connectivity", r"reachable", r"ping", r"online", r"offline"],
                    "keywords": ["connection", "connectivity", "reachable", "ping", "online", "offline", "status"],
                    "confidence": 0.8
                },
                
                # Automation & Execution
                "query_jobs": {
                    "patterns": [r"jobs?", r"tasks?", r"executions?", r"runs?", r"show.*jobs", r"list.*jobs"],
                    "keywords": ["job", "task", "execution", "run", "automation", "failed", "completed", "running", "show", "list"],
                    "confidence": 0.8
                },
                "execute_command": {
                    "patterns": [r"get.*directory", r"list.*files?", r"run.*command", r"execute.*on", r"check.*on", r"get.*from", r"dir.*on", r"ls.*on", r"show.*files", r"directory.*of", r"c:.*drive", r"d:.*drive"],
                    "keywords": ["get", "run", "execute", "command", "directory", "files", "list", "check", "show", "drive", "folder", "path", "on", "for", "from"],
                    "confidence": 0.9
                },
                "execute_powershell": {
                    "patterns": [r"powershell", r"ps1", r"get-childitem", r"get-process", r"get-service", r"invoke-command", r"winrm"],
                    "keywords": ["powershell", "ps1", "get-childitem", "get-process", "get-service", "invoke-command", "windows", "winrm"],
                    "confidence": 0.9
                },
                "remote_execution": {
                    "patterns": [r"on.*\d+\.\d+\.\d+\.\d+", r"for.*\d+\.\d+\.\d+\.\d+", r"target.*\d+\.\d+\.\d+\.\d+", r"server.*\d+\.\d+\.\d+\.\d+"],
                    "keywords": ["on", "for", "target", "server", "remote", "machine", "host", "192.168", "10.0", "172.16"],
                    "confidence": 0.9
                },
                
                # Communication
                "send_notification": {
                    "patterns": [r"send.*notification", r"send.*alert", r"notify"],
                    "keywords": ["send", "notification", "alert", "notify", "message"],
                    "confidence": 0.9
                },
                
                # Database & Schema
                "query_schema_info": {
                    "patterns": [r"schema", r"database", r"tables?", r"structure", r"what.tables"],
                    "keywords": ["schema", "database", "table", "structure", "show", "list", "what"],
                    "confidence": 0.8
                },
                
                # General
                "provide_greeting": {
                    "patterns": [r"hello", r"hi", r"hey", r"greetings?"],
                    "keywords": ["hello", "hi", "hey", "greeting", "help"],
                    "confidence": 0.9
                },
                "request_help": {
                    "patterns": [r"help", r"assistance", r"how.*to", r"what.*can"],
                    "keywords": ["help", "assistance", "how", "what", "can", "do"],
                    "confidence": 0.8
                }
            }
            
            # Special priority check for knowledge queries
            knowledge_indicators = ["write", "create", "show me", "give me", "script", "code", "example", "what is", "how to", "explain", "help"]
            if any(indicator in message_lower for indicator in knowledge_indicators):
                return {
                    "intent": "knowledge_query",
                    "confidence": 0.95,
                    "reasoning": "Contains knowledge/help request indicators",
                    "method": "fallback_classification"
                }
            
            # Calculate confidence scores for each intent
            intent_scores = {}
            
            for intent, config in intent_patterns.items():
                score = 0.0
                
                # Pattern matching
                for pattern in config["patterns"]:
                    if re.search(pattern, message_lower):
                        score += 0.4
                
                # Keyword matching
                keyword_matches = sum(1 for keyword in config["keywords"] if keyword in message_lower)
                if keyword_matches > 0:
                    score += (keyword_matches / len(config["keywords"])) * 0.6
                
                # Apply base confidence
                if score > 0:
                    score *= config["confidence"]
                
                intent_scores[intent] = score
            
            # Find best intent
            if intent_scores:
                best_intent = max(intent_scores.items(), key=lambda x: x[1])
                if best_intent[1] > 0.3:  # Minimum confidence threshold
                    return {
                        "intent": best_intent[0],
                        "confidence": best_intent[1],
                        "reasoning": "Pattern and keyword matching",
                        "method": "fallback_classification"
                    }
            
            # Default to request_help if no specific intent found
            return {
                "intent": "request_help",
                "confidence": 0.5,
                "reasoning": "No specific pattern matched, defaulting to help",
                "method": "fallback_classification"
            }
            
        except Exception as e:
            logger.error(f"Intent classification error: {e}")
            return {
                "intent": "request_help",
                "confidence": 0.3,
                "reasoning": f"Error in classification: {str(e)}",
                "method": "error_fallback"
            }
    
    async def _handle_general_query(self, message: str, context: List[Dict], intent_action: str) -> Dict[str, Any]:
        """Handle general queries and help requests"""
        try:
            # Handle knowledge queries directly
            if intent_action == "knowledge_query":
                # Check if this is a script request
                message_lower = message.lower()
                script_indicators = ["write", "create", "script", "show me", "give me", "code", "example"]
                
                if any(indicator in message_lower for indicator in script_indicators):
                    # Handle script requests with AI
                    return await self._handle_script_request(message)
                
                # Try knowledge base first
                knowledge_response = await self._search_knowledge_base(message)
                if knowledge_response:
                    return {
                        "response": knowledge_response,
                        "intent": intent_action,
                        "success": True
                    }
                
                # If no knowledge found but Ollama is available, try general LLM response
                if self.ollama_client and OLLAMA_AVAILABLE:
                    try:
                        # Create specialized prompt based on question type
                        if any(term in message.lower() for term in ["subnet", "mask", "network", "ip", "cidr", "netmask"]):
                            general_prompt = f"""You are a networking expert. The user asked: {message}

IMPORTANT: You cannot determine a subnet mask from just an IP address alone.

Provide this response:
"I cannot determine the exact subnet mask for 192.168.0.34 without knowing the network configuration. The subnet mask depends on how the network administrator configured the network, not just the IP address.

Common subnet masks for 192.168.x.x networks:
• 255.255.255.0 (/24) - Most common for home/small office networks
• 255.255.0.0 (/16) - Larger networks
• 255.255.255.128 (/25) - Smaller subnets

To find the actual subnet mask:
• Windows: Run 'ipconfig' command
• Linux/Mac: Run 'ifconfig' or 'ip addr show'
• Check network settings in your device's network configuration"

Answer:"""
                        else:
                            general_prompt = f"""You are an expert IT operations assistant. 
                            The user has asked: {message}
                            
                            Provide a helpful, detailed response that answers their question. If it's about
                            a specific command or technology, explain it clearly and provide examples.
                            
                            Answer:"""
                        
                        response = await self.ollama_client.generate(
                            model="llama2:7b",
                            prompt=general_prompt,
                            options={"temperature": 0.7, "num_predict": 400}
                        )
                        
                        if response and response.get('response'):
                            return {
                                "response": response['response'],
                                "intent": intent_action,
                                "success": True
                            }
                    except Exception as e:
                        logger.warning(f"Ollama generation failed: {e}")
                
                # Fallback message
                return {
                    "response": "I'm still learning about that topic. Please ask me something else or try rephrasing your question.",
                    "intent": intent_action,
                    "success": False
                }
            
            elif intent_action in ["provide_greeting", "request_help"]:
                response = "👋 **Welcome to OpsConductor AI!**\n\n"
                response += "I'm your intelligent IT operations assistant with extensive knowledge in:\n"
                response += "• System Administration (Linux/Windows)\n"
                response += "• Networking, Cloud Platforms, DevOps\n"
                response += "• Containers, Kubernetes, Automation\n"
                response += "• Security, Monitoring, and more!\n\n"
                response += "**I can help you with:**\n\n"
                response += "🏗️ **Infrastructure Management**\n"
                response += "• *\"Show me all targets\"*\n"
                response += "• *\"Test connection to 192.168.1.100\"*\n\n"
                response += "⚙️ **Automation & Commands**\n"
                response += "• *\"List running jobs\"*\n"
                response += "• *\"Run PowerShell command on server\"*\n\n"
                response += "💡 **Technical Knowledge**\n"
                response += "• *\"How do I configure Docker networking?\"*\n"
                response += "• *\"Explain Kubernetes pods\"*\n"
                response += "• *\"What is VLAN tagging?\"*\n\n"
                response += "Just ask me anything! I'll provide detailed, helpful answers. 🚀"
                
                return {
                    "response": response,
                    "intent": intent_action,
                    "success": True
                }
            
            # For other general queries, search knowledge base first
            knowledge_response = await self._search_knowledge_base(message)
            if knowledge_response:
                return {
                    "response": knowledge_response,
                    "intent": "knowledge_query",
                    "success": True
                }
            
            # If no knowledge found but Ollama is available, try general LLM response
            if self.ollama_client and OLLAMA_AVAILABLE:
                try:
                    general_prompt = f"""You are an expert IT operations assistant. 
                    The user has asked: {message}
                    
                    Provide a helpful, informative response. If you don't have specific information,
                    explain general concepts or provide guidance on where to find more information.
                    Be conversational and helpful.
                    
                    Answer:"""
                    
                    response = await self.ollama_client.generate(
                        model="llama2:7b",
                        prompt=general_prompt,
                        options={"temperature": 0.7, "num_predict": 400}
                    )
                    
                    if response and response.get('response'):
                        return {
                            "response": response['response'],
                            "intent": "general_llm_response",
                            "success": True
                        }
                except Exception as e:
                    logger.warning(f"General LLM response failed: {e}")
            
            # Final fallback
            response = "I don't have specific information about that in my knowledge base yet. "
            response += "Try asking about:\n"
            response += "• System administration or Linux commands\n"
            response += "• Docker, Kubernetes, or container orchestration\n"
            response += "• Networking, routing, or security\n"
            response += "• Cloud platforms (AWS, Azure, GCP)\n"
            response += "• Or any OpsConductor-specific commands!"
            
            return {
                "response": response,
                "intent": "general_query",
                "success": True
            }
            
        except Exception as e:
            logger.error(f"General query error: {e}")
            return {
                "response": f"❌ Error processing general query: {str(e)}",
                "intent": "general_query",
                "success": False
            }
    
    async def store_interaction(self, message: str, response: Dict[str, Any], context: List[Dict]):
        """Store interaction for learning and analytics"""
        try:
            if self.redis_client:
                interaction = {
                    "timestamp": datetime.now().isoformat(),
                    "message": message,
                    "intent": response.get("intent"),
                    "success": response.get("success"),
                    "response_length": len(response.get("response", "")),
                    "context_size": len(context),
                    "confidence": response.get("intent_classification", {}).get("confidence", 0)
                }
                
                await self.redis_client.lpush(
                    "ai_interactions",
                    json.dumps(interaction)
                )
                
                # Keep only last 1000 interactions
                await self.redis_client.ltrim("ai_interactions", 0, 999)
                
        except Exception as e:
            logger.warning(f"Failed to store interaction: {e}")
    
    async def store_knowledge(self, content: str, category: str) -> bool:
        """Store knowledge in the vector store for retrieval"""
        try:
            if not self.vector_store:
                logger.warning("Vector store not available, trying to initialize...")
                # Try to initialize vector store
                try:
                    import chromadb
                    from chromadb.config import Settings
                    # Use persistent storage
                    chroma_client = chromadb.PersistentClient(
                        path="/app/chromadb_data",
                        settings=Settings(anonymized_telemetry=False)
                    )
                    self.vector_store = OpsConductorVectorStore(chroma_client)
                    await self.vector_store.initialize_collections()
                    logger.info("Vector store initialized successfully with persistent storage")
                except Exception as e:
                    logger.error(f"Failed to initialize vector store: {e}")
                    return False
            
            # Store the knowledge
            doc_id = await self.vector_store.store_knowledge(
                content=content,
                title=f"{category}_knowledge_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                category=category,
                metadata={"source": "manual_training", "timestamp": datetime.now().isoformat()}
            )
            
            logger.info(f"Successfully stored knowledge: {category} (ID: {doc_id})")
            return True
            
        except Exception as e:
            logger.error(f"Failed to store knowledge: {e}")
            return False
    
    async def _search_knowledge_base(self, query: str, limit: int = 5) -> Optional[str]:
        """Search the knowledge base and generate an intelligent response using LLM"""
        try:
            # First, search the vector store for relevant knowledge
            if self.vector_store:
                results = await self.vector_store.search_knowledge(
                    query=query,
                    limit=limit
                )
                
                if results:
                    # Compile knowledge context
                    knowledge_context = ""
                    for result in results:
                        if result and result.get('content'):
                            knowledge_context += f"{result['content']}\n\n"
                    
                    # Now use Ollama to generate an intelligent, conversational response
                    if self.ollama_client and OLLAMA_AVAILABLE:
                        try:
                            prompt = f"""You are an expert IT operations assistant. Answer the user's question using the provided knowledge.

User Question: {query}

Relevant Knowledge:
{knowledge_context[:2000]}

CRITICAL INSTRUCTIONS:
- NEVER state a specific subnet mask for an IP address without network configuration details
- If asked about subnet masks for specific IPs, explain that you cannot determine this without network configuration
- Use only the relevant information from the knowledge base
- If the knowledge doesn't contain the specific answer, say so clearly
- For networking questions, be technically accurate - don't guess or assume
- Keep responses focused and helpful

Answer:"""
                            
                            response = await self.ollama_client.generate(
                                model="llama2:7b",
                                prompt=prompt,
                                options={
                                    "temperature": 0.7,
                                    "num_predict": 500
                                }
                            )
                            
                            if response and response.get('response'):
                                return response['response']
                            
                        except Exception as ollama_error:
                            logger.warning(f"Ollama generation failed: {ollama_error}")
                            # Fall back to formatted knowledge if Ollama fails
                            pass
                    
                    # Fallback: If Ollama is not available, at least format the knowledge nicely
                    response = "📚 **Based on my knowledge base:**\n\n"
                    for i, result in enumerate(results[:3], 1):
                        if result and result.get('content'):
                            doc_text = result['content'][:500]
                            response += f"{doc_text}\n\n"
                            if i < min(3, len(results)):
                                response += "---\n\n"
                    return response
            
            return None
            
        except Exception as e:
            logger.error(f"Knowledge search failed: {e}")
            return None
    
    async def get_system_stats(self) -> Dict[str, Any]:
        """Get AI system statistics"""
        try:
            stats = {
                "handlers_registered": len(self.query_handlers),
                "components_initialized": {
                    "nlp": self.nlp is not None,
                    "vector_store": self.vector_store is not None,
                    "database": self.db_pool is not None,
                    "redis": self.redis_client is not None,
                    "ollama": self.ollama_client is not None
                },
                "service_clients": {
                    "asset_client": self.asset_client is not None,
                    "automation_client": self.automation_client is not None,
                    "communication_client": self.communication_client is not None
                },
                "dependencies_available": {
                    "spacy": SPACY_AVAILABLE,
                    "ollama": OLLAMA_AVAILABLE,
                    "asyncpg": ASYNCPG_AVAILABLE,
                    "redis": REDIS_AVAILABLE,
                    "vector_store": VECTOR_STORE_AVAILABLE
                }
            }
            
            # Get interaction count from Redis
            if self.redis_client:
                try:
                    interaction_count = await self.redis_client.llen("ai_interactions")
                    stats["total_interactions"] = interaction_count
                except:
                    stats["total_interactions"] = 0
            
            return stats
            
        except Exception as e:
            logger.error(f"Failed to get system stats: {e}")
            return {"error": str(e)}
    
    async def _handle_script_request(self, message: str) -> Dict[str, Any]:
        """Handle script writing requests using AI"""
        try:
            if not self.ollama_client or not OLLAMA_AVAILABLE:
                # Fallback to basic script templates
                return await self._provide_basic_script_help(message)
            
            # Create AI prompt for script generation
            prompt = f"""You are an expert system administrator and script writer. The user has requested: "{message}"

Generate a complete, working script based on their request. Follow these guidelines:

1. **Determine the script type** (PowerShell, Bash, Python, etc.) based on the request
2. **Include proper error handling** and logging
3. **Add helpful comments** explaining key sections
4. **Provide usage examples** after the script
5. **Include prerequisites** if any are needed
6. **Make it production-ready** with proper parameter validation

For PowerShell scripts:
- Use proper parameter blocks with validation
- Include error handling with try/catch
- Add progress indicators for long operations
- Use approved verbs and proper formatting

For Bash scripts:
- Include proper shebang
- Use set -e for error handling
- Add input validation
- Include usage function

For Python scripts:
- Use proper imports and structure
- Include docstrings
- Add argument parsing with argparse
- Include proper exception handling

Format your response as:
```[script_type]
[complete script code]
```

**Usage Examples:**
```[script_type]
[usage examples]
```

**Prerequisites:**
- [list any requirements]

**Notes:**
- [any important notes or warnings]

Generate the script now:"""

            response = await self.ollama_client.chat(
                model=self.model_name,
                messages=[{"role": "user", "content": prompt}],
                options={"temperature": 0.3, "num_predict": 1000}  # Lower temperature for more consistent code
            )
            
            ai_response = response['message']['content']
            
            # Format the response nicely
            formatted_response = f"📝 **AI-Generated Script**\n\n{ai_response}\n\n"
            formatted_response += "---\n*Generated by AI - Please review and test before using in production*"
            
            return {
                "response": formatted_response,
                "intent": "knowledge_query",
                "success": True,
                "script_generated": True
            }
            
        except Exception as e:
            logger.error(f"AI script generation failed: {e}")
            # Fallback to basic templates
            return await self._provide_basic_script_help(message)
    
    async def _provide_basic_script_help(self, message: str) -> Dict[str, Any]:
        """Provide basic script help when AI is not available"""
        message_lower = message.lower()
        
        if "powershell" in message_lower and ("winrm" in message_lower or "connect" in message_lower or "directory" in message_lower):
            script_content = '''# PowerShell script to connect via WinRM and list directory
param(
    [Parameter(Mandatory=$true)]
    [string]$ComputerName,
    
    [Parameter(Mandatory=$false)]
    [string]$Path = "C:\\"
)

try {
    Write-Host "Connecting to $ComputerName..." -ForegroundColor Yellow
    
    # Test connectivity first
    if (-not (Test-WSMan -ComputerName $ComputerName -ErrorAction SilentlyContinue)) {
        throw "WinRM is not accessible on $ComputerName"
    }
    
    # Get credentials
    $Credential = Get-Credential -Message "Enter credentials for $ComputerName"
    
    # Create session and execute command
    $Session = New-PSSession -ComputerName $ComputerName -Credential $Credential
    $Result = Invoke-Command -Session $Session -ScriptBlock {
        param($DirPath)
        Get-ChildItem -Path $DirPath | Select-Object Name, Mode, Length, LastWriteTime
    } -ArgumentList $Path
    
    # Display results
    $Result | Format-Table -AutoSize
    
} catch {
    Write-Error "Failed: $($_.Exception.Message)"
} finally {
    if ($Session) { Remove-PSSession $Session }
}'''
            
            response = f"📝 **PowerShell WinRM Script**\n\n"
            response += f"```powershell\n{script_content}\n```\n\n"
            response += f"**Usage:**\n"
            response += f"```powershell\n"
            response += f".\\script.ps1 -ComputerName \"192.168.1.100\"\n"
            response += f".\\script.ps1 -ComputerName \"server01\" -Path \"D:\\\"\n"
            response += f"```"
            
        else:
            # General script help
            response = f"📝 **Script Help**\n\n"
            response += f"I can help you create scripts for various tasks:\n\n"
            response += f"**Available Script Types:**\n"
            response += f"• PowerShell scripts for Windows automation\n"
            response += f"• Bash scripts for Linux/Unix systems\n"
            response += f"• Python scripts for cross-platform tasks\n\n"
            response += f"**To get specific help, try:**\n"
            response += f"• \"Write me a PowerShell script to connect via WinRM\"\n"
            response += f"• \"Create a bash script to check disk space\"\n"
            response += f"• \"Show me a Python script to ping hosts\"\n\n"
            response += f"*Note: AI script generation is currently unavailable, showing basic templates*"
        
        return {
            "response": response,
            "intent": "knowledge_query", 
            "success": True,
            "script_generated": True
        }
    
    async def _handle_system_query(self, message: str, context: List[Dict], intent_action: str) -> Dict[str, Any]:
        """Handle system capabilities and self-awareness queries"""
        try:
            if not self.system_capabilities:
                return {
                    "response": "❌ **System capabilities not available**\n\nSystem self-awareness is currently unavailable.",
                    "intent": intent_action,
                    "success": False
                }
            
            message_lower = message.lower()
            
            # System overview and capabilities
            if intent_action in ["system_capabilities", "what_can_you_do", "help_general", "system_overview"]:
                if any(word in message_lower for word in ["overview", "summary", "what can you do", "capabilities", "help"]):
                    capabilities_summary = self.system_capabilities.get_capabilities_summary()
                    return {
                        "response": capabilities_summary,
                        "intent": intent_action,
                        "success": True,
                        "data": {
                            "system_overview": self.system_capabilities.get_system_overview()
                        }
                    }
            
            # System status
            elif intent_action == "system_status":
                await self.system_capabilities.refresh_system_status()
                overview = self.system_capabilities.get_system_overview()
                
                response_parts = [
                    f"🔍 **System Status Report**",
                    f"",
                    f"**Overall Status:** {overview['system_status'].upper()}",
                    f"**Components:** {overview['healthy_components']}/{overview['total_components']} healthy",
                    f"**Last Updated:** {overview['last_updated']}",
                    f"",
                    f"**Service Status:**"
                ]
                
                for name, component in overview['components'].items():
                    if component['type'] == 'service':
                        status_emoji = "✅" if component['status'] == "healthy" else "❌"
                        response_parts.append(f"- {status_emoji} **{component['name']}** (Port {component['port']})")
                
                return {
                    "response": "\n".join(response_parts),
                    "intent": intent_action,
                    "success": True,
                    "data": overview
                }
            
            # Protocol information
            elif intent_action == "protocol_info":
                # Extract protocol name from message
                protocol_name = None
                for protocol in self.system_capabilities.protocols.keys():
                    if protocol.lower() in message_lower:
                        protocol_name = protocol
                        break
                
                if protocol_name:
                    protocol_details = self.system_capabilities.get_protocol_details(protocol_name)
                    if protocol_details:
                        response_parts = [
                            f"🔧 **{protocol_name} Protocol Details**",
                            f"",
                            f"**Description:** {protocol_details['description']}",
                            f"**Default Port:** {protocol_details['port']}",
                            f"**Platforms:** {', '.join(protocol_details['platforms'])}",
                            f"",
                            f"**Supported Operations:**"
                        ]
                        
                        for op in protocol_details['supported_operations']:
                            response_parts.append(f"- {op.replace('_', ' ').title()}")
                        
                        if 'authentication_methods' in protocol_details:
                            response_parts.extend([
                                f"",
                                f"**Authentication Methods:**"
                            ])
                            for auth in protocol_details['authentication_methods']:
                                response_parts.append(f"- {auth.replace('_', ' ').title()}")
                        
                        return {
                            "response": "\n".join(response_parts),
                            "intent": intent_action,
                            "success": True,
                            "data": protocol_details
                        }
                else:
                    # List all protocols
                    response_parts = [
                        f"🔧 **Supported Protocols**",
                        f"",
                        f"I support the following protocols for automation and monitoring:"
                    ]
                    
                    for protocol, details in self.system_capabilities.protocols.items():
                        response_parts.append(f"- **{protocol}**: {details['description']}")
                    
                    response_parts.extend([
                        f"",
                        f"💡 **Tip:** Ask about a specific protocol for detailed information.",
                        f"Example: \"Tell me about SSH protocol\""
                    ])
                    
                    return {
                        "response": "\n".join(response_parts),
                        "intent": intent_action,
                        "success": True,
                        "data": {"protocols": list(self.system_capabilities.protocols.keys())}
                    }
            
            # Component information
            elif intent_action == "component_info":
                # Extract component name from message
                component_name = None
                for name in self.system_capabilities.components.keys():
                    if name.lower() in message_lower or name.replace('-', ' ').lower() in message_lower:
                        component_name = name
                        break
                
                if component_name:
                    component_details = self.system_capabilities.get_component_details(component_name)
                    if component_details:
                        response_parts = [
                            f"🏗️ **{component_details['name']} Details**",
                            f"",
                            f"**Type:** {component_details['type'].title()}",
                            f"**Description:** {component_details['description']}",
                            f"**Port:** {component_details['port']}",
                            f"**Status:** {component_details['status'].upper()}",
                        ]
                        
                        if component_details.get('capabilities'):
                            response_parts.extend([
                                f"",
                                f"**Capabilities:**"
                            ])
                            for cap in component_details['capabilities']:
                                response_parts.append(f"- **{cap['name']}**: {cap['description']}")
                        
                        if component_details.get('dependencies'):
                            response_parts.extend([
                                f"",
                                f"**Dependencies:** {', '.join(component_details['dependencies'])}"
                            ])
                        
                        return {
                            "response": "\n".join(response_parts),
                            "intent": intent_action,
                            "success": True,
                            "data": component_details
                        }
                else:
                    # List all components
                    overview = self.system_capabilities.get_system_overview()
                    response_parts = [
                        f"🏗️ **System Components**",
                        f"",
                        f"**Services:**"
                    ]
                    
                    service_components = {name: comp for name, comp in overview['components'].items() if comp['type'] == 'service'}
                    for name, comp in service_components.items():
                        status_emoji = "✅" if comp['status'] == "healthy" else "❌"
                        response_parts.append(f"- {status_emoji} **{comp['name']}** (Port {comp['port']})")
                    
                    response_parts.extend([
                        f"",
                        f"**Infrastructure:**"
                    ])
                    
                    infra_components = {name: comp for name, comp in overview['components'].items() if comp['type'] != 'service'}
                    for name, comp in infra_components.items():
                        status_emoji = "✅" if comp['status'] == "healthy" else "❌"
                        response_parts.append(f"- {status_emoji} **{comp['name']}** ({comp['type'].title()})")
                    
                    response_parts.extend([
                        f"",
                        f"💡 **Tip:** Ask about a specific component for detailed information.",
                        f"Example: \"Tell me about the asset service\""
                    ])
                    
                    return {
                        "response": "\n".join(response_parts),
                        "intent": intent_action,
                        "success": True,
                        "data": {"components": list(overview['components'].keys())}
                    }
            
            # Can perform operation check
            elif intent_action == "can_perform_operation":
                # Extract operation from message
                operation_keywords = ["can you", "are you able", "do you support", "can i", "is it possible"]
                operation = message_lower
                
                for keyword in operation_keywords:
                    if keyword in operation:
                        operation = operation.split(keyword, 1)[1].strip()
                        break
                
                # Remove question marks and clean up
                operation = operation.replace("?", "").strip()
                
                if operation:
                    capability_check = self.system_capabilities.can_perform_operation(operation)
                    
                    if capability_check['can_perform']:
                        response_parts = [
                            f"✅ **Yes, I can help with: {operation}**",
                            f""
                        ]
                        
                        if capability_check['matching_capabilities']:
                            response_parts.append(f"**Available through these services:**")
                            for cap in capability_check['matching_capabilities']:
                                status_emoji = "✅" if cap['status'] == "healthy" else "❌"
                                response_parts.append(f"- {status_emoji} **{cap['component']}**: {cap['description']}")
                        
                        if capability_check['matching_protocols']:
                            response_parts.extend([f"", f"**Supported protocols:**"])
                            for proto in capability_check['matching_protocols']:
                                response_parts.append(f"- **{proto['protocol']}**: {proto['description']}")
                        
                        if capability_check['matching_tools']:
                            response_parts.extend([f"", f"**Available tools:**"])
                            for tool in capability_check['matching_tools']:
                                response_parts.append(f"- **{tool['tool'].replace('_', ' ').title()}**: {tool['description']}")
                        
                        if capability_check['recommendations']:
                            response_parts.extend([f"", f"**Recommendations:**"])
                            for rec in capability_check['recommendations']:
                                response_parts.append(f"- {rec}")
                        
                        return {
                            "response": "\n".join(response_parts),
                            "intent": intent_action,
                            "success": True,
                            "data": capability_check
                        }
                    else:
                        return {
                            "response": f"❌ **I cannot directly perform: {operation}**\n\nThis operation is not currently supported by the available system components and protocols.\n\n💡 **Tip:** Try asking \"What can you do?\" to see my full capabilities.",
                            "intent": intent_action,
                            "success": False,
                            "data": capability_check
                        }
                else:
                    return {
                        "response": f"❓ **Please specify what operation you'd like me to check**\n\nExample: \"Can you restart services on Windows servers?\"",
                        "intent": intent_action,
                        "success": False
                    }
            
            # Default system help
            else:
                capabilities_summary = self.system_capabilities.get_capabilities_summary()
                return {
                    "response": f"ℹ️ **System Information**\n\n{capabilities_summary}\n\n💡 **Ask me:**\n- \"What's the system status?\"\n- \"Tell me about SSH protocol\"\n- \"Can you restart services?\"\n- \"Show me the asset service details\"",
                    "intent": intent_action,
                    "success": True
                }
                
        except Exception as e:
            logger.error(f"System query handling failed: {e}")
            return {
                "response": f"❌ **System Query Error**: {str(e)}",
                "intent": intent_action,
                "success": False,
                "error": str(e)
            }

# Global AI instance
ai_engine = OpsConductorAI()

# Async initialization function
async def initialize_ai():
    """Initialize the AI engine"""
    await ai_engine.initialize()
    return ai_engine

if __name__ == "__main__":
    async def demo():
        print("OpsConductor AI Engine - Modular Version")
        print("=" * 50)
        
        # Initialize AI
        ai = await initialize_ai()
        
        # Test message
        test_message = "can you get the directory of the c drive for 192.168.50.210?"
        print(f"\nTest Message: {test_message}")
        
        # Process message
        result = await ai.process_message(test_message)
        print(f"\nResult: {result}")
    
    asyncio.run(demo())