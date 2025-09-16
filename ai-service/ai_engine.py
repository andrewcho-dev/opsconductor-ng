"""
OpsConductor AI Engine - Refactored Modular Version
Clean, maintainable AI system with modular query handlers
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

try:
    from learning_engine import learning_engine, PredictionResult
    LEARNING_ENGINE_AVAILABLE = True
except ImportError:
    LEARNING_ENGINE_AVAILABLE = False
    learning_engine = None
    PredictionResult = None

# Import service clients
from asset_client import AssetServiceClient
from automation_client import AutomationServiceClient
from communication_client import CommunicationServiceClient

# Import modular query handlers
from query_handlers import (
    InfrastructureQueryHandler,
    AutomationQueryHandler,
    CommunicationQueryHandler
)
from query_handlers.dynamic_schema_queries import DynamicSchemaQueryHandler

logger = logging.getLogger(__name__)

class OpsConductorAI:
    """Refactored AI Engine with Modular Query Handlers"""
    
    def __init__(self):
        self.nlp = None
        self.ollama_client = None
        self.vector_store = None
        self.db_pool = None
        self.redis_client = None
        self.protocol_manager = protocol_manager if PROTOCOL_MANAGER_AVAILABLE else None
        self.learning_engine = learning_engine if LEARNING_ENGINE_AVAILABLE else None
        self.system_knowledge = {}
        
        # Initialize service clients
        self.asset_client = AssetServiceClient()
        self.automation_client = AutomationServiceClient()
        self.communication_client = CommunicationServiceClient()
        
        # Initialize modular query handlers
        self.query_handlers = {}
        self._init_query_handlers()
        
    def _init_query_handlers(self):
        """Initialize modular query handlers"""
        service_clients = {
            'asset_client': self.asset_client,
            'automation_client': self.automation_client,
            'communication_client': self.communication_client
        }
        
        self.infrastructure_handler = InfrastructureQueryHandler(service_clients)
        self.automation_handler = AutomationQueryHandler(service_clients)
        self.communication_handler = CommunicationQueryHandler(service_clients)
        self.schema_handler = DynamicSchemaQueryHandler(service_clients)
        
        logger.info("Query handlers initialized")
        
    async def _register_handlers(self):
        """Register all query handlers with their supported intents"""
        handlers = [
            self.infrastructure_handler,
            self.automation_handler,
            self.communication_handler,
            self.schema_handler
        ]
        
        for handler in handlers:
            supported_intents = await handler.get_supported_intents()
            for intent in supported_intents:
                self.query_handlers[intent] = handler
                
        logger.info(f"Registered {len(self.query_handlers)} query handlers")
    
    async def initialize(self):
        """Initialize all AI components"""
        try:
            # Initialize spaCy (optional)
            if SPACY_AVAILABLE:
                try:
                    self.nlp = spacy.load("en_core_web_sm")
                    logger.info("SpaCy model loaded successfully")
                except OSError:
                    logger.warning("SpaCy model not found, using basic NLP")
                    self.nlp = None
            else:
                logger.warning("SpaCy not available, using basic NLP")
                self.nlp = None
            
            # Initialize Ollama client (optional)
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
            
            # Initialize vector store (optional)
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
            
            # Initialize database connection (optional)
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
            
            # Initialize Redis connection (optional)
            if REDIS_AVAILABLE:
                try:
                    self.redis_client = redis.Redis(
                        host="redis",
                        port=6379,
                        decode_responses=True
                    )
                    logger.info("Redis client initialized")
                except Exception as e:
                    logger.warning(f"Redis connection failed: {e}")
                    self.redis_client = None
            else:
                logger.warning("Redis not available")
                self.redis_client = None
            
            # Register query handlers
            await self._register_handlers()
            
            # Load system knowledge
            await self.load_system_knowledge()
            
            logger.info("OpsConductor AI Engine initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize AI engine: {e}")
            raise
    
    async def load_system_knowledge(self):
        """Load system knowledge from various sources"""
        try:
            # Load from database
            if self.db_pool:
                try:
                    async with self.db_pool.acquire() as conn:
                        # Load system configuration
                        config_rows = await conn.fetch("SELECT key, value FROM system_config")
                        self.system_knowledge['config'] = {row['key']: row['value'] for row in config_rows}
                        
                        # Load common patterns
                        pattern_rows = await conn.fetch("SELECT pattern, description FROM common_patterns")
                        self.system_knowledge['patterns'] = {row['pattern']: row['description'] for row in pattern_rows}
                except Exception as e:
                    logger.warning(f"Failed to load from database: {e}")
            
            # Load from vector store
            if self.vector_store:
                try:
                    # Store common OpsConductor concepts
                    concepts = [
                        "OpsConductor is an automation platform for IT operations",
                        "Targets are managed endpoints like servers and workstations",
                        "Jobs are automation tasks that run on targets",
                        "Workflows are sequences of jobs with dependencies",
                        "Notifications are sent via email, Slack, or other channels"
                    ]
                    
                    for concept in concepts:
                        await self.vector_store.add_document(
                            collection="system_knowledge",
                            document=concept,
                            metadata={"type": "concept", "source": "system"}
                        )
                except Exception as e:
                    logger.warning(f"Failed to load vector concepts: {e}")
            
            logger.info("System knowledge loaded successfully")
            
        except Exception as e:
            logger.warning(f"Failed to load system knowledge: {e}")
    
    async def classify_intent(self, message: str) -> Dict[str, Any]:
        """Classify user intent using NLP and patterns"""
        try:
            message_lower = message.lower()
            doc = self.nlp(message) if self.nlp else None
            
            # Define intent patterns with confidence scores
            intent_patterns = {
                # Infrastructure queries
                "query_targets": {
                    "patterns": [r"targets?", r"servers?", r"machines?", r"endpoints?", r"hosts?"],
                    "keywords": ["target", "server", "machine", "endpoint", "host", "windows", "linux", "macos"],
                    "confidence": 0.8
                },
                "query_target_groups": {
                    "patterns": [r"groups?", r"target.groups?", r"collections?"],
                    "keywords": ["group", "collection", "organize", "category"],
                    "confidence": 0.8
                },
                "query_connection_status": {
                    "patterns": [r"connection", r"connectivity", r"reachable", r"ping", r"online", r"offline"],
                    "keywords": ["connection", "connectivity", "reachable", "ping", "online", "offline", "status"],
                    "confidence": 0.8
                },
                "query_target_tags": {
                    "patterns": [r"tags?", r"labels?", r"categories?", r"tag.list", r"all.tags"],
                    "keywords": ["tag", "tags", "label", "labels", "category", "organize", "list", "show"],
                    "confidence": 0.8
                },
                "query_targets_by_tag": {
                    "patterns": [r"tagged", r"with.tag", r"tag:", r"labeled", r"find.*tag", r"filter.*tag"],
                    "keywords": ["tagged", "tag", "label", "filter", "find", "with", "production", "development", "staging"],
                    "confidence": 0.8
                },
                "query_tag_statistics": {
                    "patterns": [r"tag.stats", r"tag.usage", r"tag.analytics", r"tag.distribution"],
                    "keywords": ["statistics", "stats", "usage", "analytics", "distribution", "coverage", "popular"],
                    "confidence": 0.8
                },
                
                # Automation queries
                "query_jobs": {
                    "patterns": [r"jobs?", r"tasks?", r"executions?", r"runs?"],
                    "keywords": ["job", "task", "execution", "run", "automation", "failed", "completed", "running"],
                    "confidence": 0.8
                },
                "query_workflows": {
                    "patterns": [r"workflows?", r"processes?", r"pipelines?"],
                    "keywords": ["workflow", "process", "pipeline", "sequence", "steps"],
                    "confidence": 0.8
                },
                "query_task_queue": {
                    "patterns": [r"queue", r"pending", r"workers?", r"backlog"],
                    "keywords": ["queue", "pending", "worker", "backlog", "waiting", "active"],
                    "confidence": 0.8
                },
                "query_error_analysis": {
                    "patterns": [r"errors?", r"failures?", r"problems?", r"issues?"],
                    "keywords": ["error", "failure", "problem", "issue", "analysis", "critical"],
                    "confidence": 0.8
                },
                
                # Communication queries
                "query_notification_history": {
                    "patterns": [r"notifications?", r"alerts?", r"messages?", r"emails?"],
                    "keywords": ["notification", "alert", "message", "email", "sent", "history"],
                    "confidence": 0.8
                },
                "query_notification_audit": {
                    "patterns": [r"audit", r"delivery", r"tracking", r"logs?"],
                    "keywords": ["audit", "delivery", "tracking", "log", "trace", "failed", "success"],
                    "confidence": 0.8
                },
                
                # Schema and database queries
                "query_schema_info": {
                    "patterns": [r"schema", r"database", r"tables?", r"structure", r"what.tables"],
                    "keywords": ["schema", "database", "table", "structure", "show", "list", "what"],
                    "confidence": 0.8
                },
                "query_table_structure": {
                    "patterns": [r"describe", r"table.structure", r"columns?", r"fields?", r"what's.in"],
                    "keywords": ["describe", "structure", "column", "field", "table", "show", "explain"],
                    "confidence": 0.8
                },
                "query_database_search": {
                    "patterns": [r"search", r"find", r"look.for", r"related.to"],
                    "keywords": ["search", "find", "look", "related", "database", "table", "column"],
                    "confidence": 0.7
                },
                "query_column_info": {
                    "patterns": [r"column", r"field", r"which.table", r"where.is"],
                    "keywords": ["column", "field", "which", "where", "table", "has", "contains"],
                    "confidence": 0.8
                },
                "query_relationships": {
                    "patterns": [r"relationships?", r"foreign.key", r"references?", r"related.tables"],
                    "keywords": ["relationship", "foreign", "key", "reference", "related", "join", "connection"],
                    "confidence": 0.8
                },
                "query_database_summary": {
                    "patterns": [r"database.summary", r"overview", r"what.tables", r"schema.overview"],
                    "keywords": ["summary", "overview", "database", "schema", "all", "tables", "structure"],
                    "confidence": 0.8
                },
                
                # General intents
                "provide_greeting": {
                    "patterns": [r"hello", r"hi", r"hey", r"greetings?"],
                    "keywords": ["hello", "hi", "hey", "greeting", "help"],
                    "confidence": 0.9
                },
                "generate_script": {
                    "patterns": [r"script", r"generate", r"create", r"write"],
                    "keywords": ["script", "generate", "create", "write", "automation", "powershell", "bash"],
                    "confidence": 0.7
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
    
    async def process_message(self, message: str, context: List[Dict] = None) -> Dict[str, Any]:
        """Process user message and return response"""
        try:
            if context is None:
                context = []
            
            # Classify intent
            intent_result = await self.classify_intent(message)
            intent_action = intent_result.get("action")
            
            logger.info(f"Processing message with intent: {intent_action} (confidence: {intent_result.get('confidence', 0):.2f})")
            
            # Route to appropriate handler
            if intent_action in self.query_handlers:
                handler = self.query_handlers[intent_action]
                response = await handler.handle_query(intent_action, message, context)
            elif intent_action == "provide_greeting":
                response = await self.handle_greeting(message, context)
            elif intent_action == "generate_script":
                response = await self.handle_script_generation(message, context)
            else:
                response = await self.handle_general_query(message, context)
            
            # Add intent information to response
            response["intent_classification"] = intent_result
            
            # Store interaction for learning
            await self.store_interaction(message, response, context)
            
            return response
            
        except Exception as e:
            logger.error(f"Message processing error: {e}")
            return {
                "response": f"❌ I encountered an error processing your request: {str(e)}",
                "intent": "error",
                "success": False,
                "error": str(e)
            }
    
    async def handle_greeting(self, message: str, context: List[Dict]) -> Dict[str, Any]:
        """Handle greeting messages"""
        greetings = [
            "👋 Hello! I'm your OpsConductor AI assistant.",
            "🤖 Hi there! I'm here to help with your automation needs.",
            "✨ Greetings! Ready to assist with OpsConductor operations."
        ]
        
        import random
        greeting = random.choice(greetings)
        
        response = f"{greeting}\n\n"
        response += "**I can help you with:**\n"
        response += "• 🎯 Target and infrastructure queries\n"
        response += "• 🏷️ Target tags and organization\n"
        response += "• ⚙️ Job and workflow management\n"
        response += "• 📧 Notification and communication tracking\n"
        response += "• 📊 System monitoring and analytics\n"
        response += "• 🗄️ Database schema and structure exploration\n"
        response += "• 🔧 Script generation and automation\n\n"
        response += "**Try asking:**\n"
        response += "• *\"Show me Windows targets\"*\n"
        response += "• *\"List all target tags\"*\n"
        response += "• *\"Show production targets\"*\n"
        response += "• *\"What jobs failed today?\"*\n"
        response += "• *\"Show task queue status\"*\n"
        response += "• *\"Show notification history\"*\n"
        response += "• *\"What tables are in the database?\"*\n"
        response += "• *\"Describe the targets table\"*\n"
        response += "• *\"Find column named email\"*\n"
        response += "• *\"Database schema overview\"*\n"
        response += "• *\"Tag usage statistics\"*"
        
        return {
            "response": response,
            "intent": "provide_greeting",
            "success": True
        }
    
    async def handle_script_generation(self, message: str, context: List[Dict]) -> Dict[str, Any]:
        """Handle script generation requests"""
        response = "🔧 **Script Generation**\n\n"
        response += "Script generation functionality is available! I can help you create:\n\n"
        response += "• **PowerShell scripts** for Windows automation\n"
        response += "• **Bash scripts** for Linux/Unix systems\n"
        response += "• **Python scripts** for cross-platform tasks\n"
        response += "• **Batch files** for Windows batch operations\n\n"
        response += "**Example requests:**\n"
        response += "• *\"Generate a PowerShell script to check disk space\"*\n"
        response += "• *\"Create a bash script to restart services\"*\n"
        response += "• *\"Write a Python script to monitor processes\"*\n\n"
        response += "Please specify what type of script you'd like me to generate!"
        
        return {
            "response": response,
            "intent": "generate_script",
            "success": True
        }
    
    async def handle_general_query(self, message: str, context: List[Dict]) -> Dict[str, Any]:
        """Handle general queries using vector search and LLM"""
        try:
            # Search vector store for relevant information
            if self.vector_store:
                try:
                    search_results = await self.vector_store.search(
                        collection="system_knowledge",
                        query=message,
                        limit=5
                    )
                    
                    if search_results and self.ollama_client:
                        context_info = "\n".join([doc["document"] for doc in search_results])
                        
                        # Use LLM to generate response
                        prompt = f"""
                        Based on the following OpsConductor system information:
                        {context_info}
                        
                        User question: {message}
                        
                        Provide a helpful response about OpsConductor operations.
                        """
                        
                        llm_response = await self.ollama_client.generate(
                            model="llama3.2",
                            prompt=prompt
                        )
                        
                        return {
                            "response": llm_response["response"],
                            "intent": "general_query",
                            "success": True,
                            "sources": [doc["metadata"] for doc in search_results]
                        }
                except Exception as e:
                    logger.warning(f"Vector search failed: {e}")
            
            # Fallback response
            response = "🤔 I'm not sure how to help with that specific request.\n\n"
            response += "**I can help you with:**\n"
            response += "• **Infrastructure**: Targets, groups, connections\n"
            response += "• **Automation**: Jobs, workflows, task queues\n"
            response += "• **Communication**: Notifications, audit trails\n"
            response += "• **Analysis**: Errors, performance, statistics\n\n"
            response += "**Try asking:**\n"
            response += "• *\"Show me all targets\"*\n"
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
        print("OpsConductor AI Engine - Refactored Version")
        print("=" * 50)
        
        # Initialize AI
        ai = await initialize_ai()
        
        # Show system stats
        stats = await ai.get_system_stats()
        print(f"📊 System Stats: {json.dumps(stats, indent=2)}")
        
        # Test queries
        test_queries = [
            "Hello!",
            "Show me Windows targets",
            "What jobs failed today?",
            "Show task queue status",
            "Show notification history",
            "Analyze connection status"
        ]
        
        for query in test_queries:
            print(f"\n🔍 Query: {query}")
            response = await ai.process_message(query)
            print(f"✅ Response: {response['response'][:100]}...")
            print(f"📊 Intent: {response.get('intent', 'unknown')} (confidence: {response.get('intent_classification', {}).get('confidence', 0):.2f})")
    
    asyncio.run(demo())