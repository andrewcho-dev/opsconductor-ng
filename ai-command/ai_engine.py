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
from query_handlers import (
    InfrastructureQueryHandler,
    AutomationQueryHandler,
    CommunicationQueryHandler
)

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
                    self.ollama_client = ollama.AsyncClient()
                    logger.info("Ollama client initialized")
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
                    self.vector_client = VectorStoreClient("http://vector-service:3000")
                    logger.info("Centralized vector client initialized")
                    
                    # Initialize learning orchestrator
                    self.learning_orchestrator = LearningOrchestrator(
                        vector_service_url="http://vector-service:3000",
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
            
            self.initialized = True
            logger.info("AI Engine initialization completed successfully")
            
        except Exception as e:
            logger.error(f"AI Engine initialization failed: {e}")
            raise
    
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
            self.query_handlers = {
                'infrastructure': InfrastructureQueryHandler(shared_context),
                'automation': AutomationQueryHandler(shared_context),
                'communication': CommunicationQueryHandler(shared_context)
            }
            
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
            
            # Classify intent
            intent_result = await self.classify_intent(message)
            intent_action = intent_result.get("action", "general_query")
            confidence = intent_result.get("confidence", 0.0)
            
            logger.info(f"Intent classified: {intent_action} (confidence: {confidence:.2f})")
            
            # DEBUG: Log all intent scores for troubleshooting
            all_scores = intent_result.get("all_scores", {})
            logger.debug(f"All intent scores: {all_scores}")
            
            # EXCEPTION TRACKING: Log low confidence classifications for review
            if confidence < 0.5:
                logger.warning(f"LOW CONFIDENCE intent classification: {intent_action} ({confidence:.2f}) for message: '{message[:100]}...'")
                logger.warning(f"Top 3 scores: {sorted(all_scores.items(), key=lambda x: x[1], reverse=True)[:3]}")
            
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
        """Classify user intent with comprehensive patterns"""
        try:
            message_lower = message.lower()
            doc = self.nlp(message) if self.nlp else None
            
            # Define comprehensive intent patterns covering ALL system capabilities
            intent_patterns = {
                # Knowledge and Help Queries (Check FIRST for "what is", "how to", "explain", etc.)
                "knowledge_query": {
                    "patterns": [
                        r"what\s+(is|are)\s+", r"how\s+(to|do|does|can)\s+", r"explain\s+", r"tell\s+me\s+about",
                        r"describe\s+", r"define\s+", r"help\s+(with|me)", r"tutorial", r"guide\s+",
                        r"difference\s+between", r"when\s+should", r"why\s+(is|does|should)",
                        r"teach\s+me", r"learn\s+about"
                    ],
                    "keywords": ["what", "how", "explain", "tell", "describe", "define", "help", "tutorial", 
                                "guide", "difference", "learn", "teach", "understand", "concept", "theory"],
                    "confidence": 0.95
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
                        "action": best_intent[0],
                        "confidence": best_intent[1],
                        "all_scores": intent_scores
                    }
            
            # Default to general query if no specific intent found
            return {
                "action": "general_query",
                "confidence": 0.5,
                "all_scores": intent_scores
            }
            
        except Exception as e:
            logger.error(f"Intent classification error: {e}")
            return {
                "action": "general_query",
                "confidence": 0.3,
                "error": str(e)
            }
    
    async def _handle_general_query(self, message: str, context: List[Dict], intent_action: str) -> Dict[str, Any]:
        """Handle general queries and help requests"""
        try:
            # Handle knowledge queries directly
            if intent_action == "knowledge_query":
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
                            prompt = f"""You are an expert IT operations assistant. Based on the following knowledge base information, 
                            provide a clear, helpful, and conversational answer to the user's question.
                            
                            User Question: {query}
                            
                            Relevant Knowledge:
                            {knowledge_context[:3000]}  
                            
                            Instructions:
                            1. Answer the specific question directly and conversationally
                            2. Be helpful and informative but concise
                            3. Use the knowledge to provide accurate information
                            4. If the question asks "what is X", explain what X is
                            5. If the question asks "how to", provide step-by-step instructions
                            6. Format your response nicely with markdown when appropriate
                            7. Don't just dump information - answer the actual question
                            
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