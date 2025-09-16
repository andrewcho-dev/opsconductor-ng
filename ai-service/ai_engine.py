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
                    chroma_client = chromadb.Client()
                    self.vector_store = OpsConductorVectorStore(chroma_client)
                    await self.vector_store.initialize_collections()
                    logger.info("Vector store initialized")
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
            if intent_action in ["provide_greeting", "request_help"]:
                response = "👋 **Welcome to OpsConductor AI!**\n\n"
                response += "I can help you with:\n\n"
                response += "🏗️ **Infrastructure Management**\n"
                response += "• *\"Show me all targets\"*\n"
                response += "• *\"What targets are tagged as production?\"*\n"
                response += "• *\"Test connection to 192.168.1.100\"*\n\n"
                response += "⚙️ **Automation & Commands**\n"
                response += "• *\"Get directory of C: drive for 192.168.50.210\"*\n"
                response += "• *\"List running jobs\"*\n"
                response += "• *\"Run PowerShell command on server\"*\n\n"
                response += "📧 **Communication**\n"
                response += "• *\"Send notification to admin team\"*\n"
                response += "• *\"Show notification history\"*\n\n"
                response += "🗄️ **Database Queries**\n"
                response += "• *\"What tables are in the database?\"*\n"
                response += "• *\"Show me the schema structure\"*\n\n"
                response += "Just ask me anything in natural language! 🚀"
                
                return {
                    "response": response,
                    "intent": intent_action,
                    "success": True
                }
            
            # For other general queries, provide a helpful response
            response = "🤔 **I'm not sure how to help with that specific request.**\n\n"
            response += "Here are some things you can try:\n\n"
            response += "• *\"Show me all targets\"*\n"
            response += "• *\"Get directory of C: drive for 192.168.50.210\"*\n"
            response += "• *\"List running jobs\"*\n"
            response += "• *\"What jobs are running?\"*\n"
            response += "• *\"Show failed notifications\"*\n"
            response += "• *\"Analyze recent errors\"*"
            
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