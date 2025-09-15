"""
OpsConductor AI Engine - Enhanced with Vector Storage and Learning
"""
import asyncio
import logging
import json
import re
from datetime import datetime
from typing import Dict, List, Optional, Any
import spacy
import ollama
import asyncpg
import redis.asyncio as redis
from vector_store import OpsConductorVectorStore

logger = logging.getLogger(__name__)

class OpsConductorAI:
    """Main AI Engine for OpsConductor"""
    
    def __init__(self):
        self.nlp = None
        self.ollama_client = ollama.AsyncClient()
        self.vector_store = None
        self.db_pool = None
        self.redis_client = None
        self.system_knowledge = {}
        
    async def initialize(self):
        """Initialize all AI components"""
        try:
            # Initialize spaCy
            self.nlp = spacy.load("en_core_web_sm")
            logger.info("SpaCy model loaded successfully")
            
            # Initialize vector store
            import chromadb
            chroma_client = chromadb.Client()
            self.vector_store = OpsConductorVectorStore(chroma_client)
            await self.vector_store.initialize_collections()
            logger.info("Vector store initialized")
            
            # Initialize database connection
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
            
            # Initialize Redis connection
            self.redis_client = redis.Redis(
                host="redis",
                port=6379,
                decode_responses=True
            )
            logger.info("Redis client initialized")
            
            # Load system knowledge
            await self.load_system_knowledge()
            
            logger.info("AI Engine initialized successfully")
            return True
            
        except Exception as e:
            logger.error(f"Failed to initialize AI Engine: {e}")
            return False
    
    async def load_system_knowledge(self):
        """Load system knowledge from database"""
        try:
            async with self.db_pool.acquire() as conn:
                # Load target information
                targets = await conn.fetch("SELECT * FROM assets.targets LIMIT 100")
                self.system_knowledge['targets'] = [dict(t) for t in targets]
                
                # Load enhanced targets
                enhanced_targets = await conn.fetch("SELECT * FROM assets.enhanced_targets LIMIT 100")
                self.system_knowledge['enhanced_targets'] = [dict(t) for t in enhanced_targets]
                
                # Load automation jobs
                jobs = await conn.fetch("SELECT * FROM automation.jobs ORDER BY created_at DESC LIMIT 50")
                self.system_knowledge['recent_jobs'] = [dict(j) for j in jobs]
                
                logger.info(f"Loaded system knowledge: {len(targets)} targets, {len(enhanced_targets)} enhanced targets, {len(jobs)} recent jobs")
                
        except Exception as e:
            logger.error(f"Failed to load system knowledge: {e}")
    
    async def get_relevant_context(self, query: str, limit: int = 3) -> List[Dict]:
        """Get relevant context from vector store"""
        try:
            if self.vector_store:
                return await self.vector_store.search_knowledge(query, limit=limit)
            return []
        except Exception as e:
            logger.error(f"Failed to get relevant context: {e}")
            return []
    
    async def analyze_intent(self, message: str) -> str:
        """Analyze user intent from message"""
        message_lower = message.lower()
        
        # System queries
        if any(word in message_lower for word in ["how many", "count", "list", "show me", "which"]):
            return "system_query"
        
        # Troubleshooting
        if any(word in message_lower for word in ["problem", "issue", "error", "fail", "broken", "not working", "help with"]):
            return "troubleshooting"
        
        # Script generation
        if any(word in message_lower for word in ["create", "generate", "script", "automation"]):
            return "script_generation"
        
        # Greetings
        if any(word in message_lower for word in ["hello", "hi", "hey", "what can you", "what do you"]):
            return "greeting"
        
        return "general"
    
    async def query_system(self, query: str) -> Dict[str, Any]:
        """Handle system queries about targets, jobs, etc."""
        try:
            query_lower = query.lower()
            
            # Target queries
            if "targets" in query_lower or "servers" in query_lower:
                async with self.db_pool.acquire() as conn:
                    if "tagged with" in query_lower:
                        # Extract tag from query
                        tag_match = re.search(r'tagged with (\w+)', query_lower)
                        if tag_match:
                            tag = tag_match.group(1)
                            targets = await conn.fetch("""
                                SELECT hostname, ip_address, os_type 
                                FROM assets.enhanced_targets 
                                WHERE tags @> $1::jsonb
                            """, json.dumps([tag]))
                            
                            if targets:
                                target_list = "\n".join([
                                    f"• {t['hostname']} ({t['ip_address']}) - {t['os_type']}"
                                    for t in targets
                                ])
                                return {
                                    "answer": f"Found {len(targets)} targets tagged with '{tag}':\n\n{target_list}",
                                    "count": len(targets),
                                    "tag": tag
                                }
                            else:
                                return {
                                    "answer": f"No targets found with tag '{tag}'",
                                    "count": 0,
                                    "tag": tag
                                }
                    
                    elif "how many" in query_lower:
                        count = await conn.fetchval("SELECT COUNT(*) FROM assets.enhanced_targets")
                        return {
                            "answer": f"You have {count} targets in your system",
                            "count": count
                        }
                    
                    else:
                        # General target listing
                        targets = await conn.fetch("""
                            SELECT hostname, ip_address, os_type, status 
                            FROM assets.enhanced_targets 
                            ORDER BY hostname 
                            LIMIT 10
                        """)
                        
                        target_list = "\n".join([
                            f"• {t['hostname']} ({t['ip_address']}) - {t['os_type']} - {t['status']}"
                            for t in targets
                        ])
                        
                        total_count = await conn.fetchval("SELECT COUNT(*) FROM assets.enhanced_targets")
                        
                        return {
                            "answer": f"Here are your targets (showing first 10 of {total_count}):\n\n{target_list}",
                            "count": total_count,
                            "showing": len(targets)
                        }
            
            # Job queries
            elif "jobs" in query_lower:
                async with self.db_pool.acquire() as conn:
                    if "how many" in query_lower:
                        count = await conn.fetchval("SELECT COUNT(*) FROM automation.jobs")
                        return {
                            "answer": f"You have {count} automation jobs in your system",
                            "count": count
                        }
                    else:
                        jobs = await conn.fetch("""
                            SELECT name, status, created_at 
                            FROM automation.jobs 
                            ORDER BY created_at DESC 
                            LIMIT 10
                        """)
                        
                        job_list = "\n".join([
                            f"• {j['name']} - {j['status']} (created {j['created_at'].strftime('%Y-%m-%d %H:%M')})"
                            for j in jobs
                        ])
                        
                        return {
                            "answer": f"Recent automation jobs:\n\n{job_list}",
                            "count": len(jobs)
                        }
            
            return {"answer": "I can help you query targets, jobs, and system information. What would you like to know?"}
            
        except Exception as e:
            logger.error(f"System query failed: {e}")
            return {"error": f"System query failed: {e}"}
    
    async def handle_troubleshooting_query(self, query: str, context: List[Dict] = None) -> Dict[str, Any]:
        """Handle troubleshooting questions with context"""
        try:
            # Use context if available
            context_text = ""
            if context:
                context_text = "\n".join([item.get('content', '') for item in context[:2]])
            
            prompt = f"""
            You are an expert IT operations assistant. Help troubleshoot this issue:
            
            User Question: {query}
            
            Relevant Context:
            {context_text}
            
            Provide a helpful, specific response with:
            1. Likely causes
            2. Step-by-step troubleshooting steps
            3. Prevention tips
            
            Keep it practical and actionable.
            """
            
            response = await self.ollama_client.generate(
                model='llama3.2:3b',
                prompt=prompt
            )
            
            return {
                "answer": response['response'],
                "context_used": len(context) if context else 0,
                "suggestions": [
                    "Check system logs",
                    "Verify service status",
                    "Test connectivity",
                    "Review recent changes"
                ]
            }
            
        except Exception as e:
            logger.error(f"Troubleshooting query failed: {e}")
            return {"error": f"Troubleshooting failed: {e}"}
    
    async def generate_script(self, request: str, language: str = "powershell") -> Dict[str, Any]:
        """Generate automation scripts using Ollama"""
        try:
            if language.lower() == "powershell":
                model = 'codellama:7b'
                prompt = f"""
            Generate a production-ready PowerShell script for this request:
            
            {request}
            
            Requirements:
            - Include error handling with try/catch blocks
            - Add proper logging and output
            - Include parameter validation
            - Add comments explaining the logic
            - Make it modular and reusable
            - Include help documentation
            
            Request: {request}
            """
            else:  # bash
                model = 'codellama:7b'
                prompt = f"""
            Generate a production-ready Bash script for this request:
            
            {request}
            
            Requirements:
            - Include error handling
            - Add logging/output
            - Make it production-ready
            - Include comments explaining the logic
            
            Request: {request}
            """
            
            response = await self.ollama_client.generate(
                model='codellama:7b',
                prompt=prompt
            )
            
            return {
                "script": response['response'],
                "language": language,
                "request": request
            }
            
        except Exception as e:
            logger.error(f"Failed to generate script: {e}")
            return {"error": f"Script generation failed: {e}"}
    
    async def chat(self, message: str, user_id: Optional[int] = None) -> Dict[str, Any]:
        """Enhanced chat interface with vector storage"""
        try:
            message_lower = message.lower()
            
            # Get relevant context from previous interactions
            context = await self.get_relevant_context(message)
            similar_interactions = []
            if self.vector_store:
                similar_interactions = await self.vector_store.find_similar_interactions(message, limit=3)
            
            response = None
            intent = "unknown"
            
            # Check for greetings first
            if (any(phrase in message_lower for phrase in ["hello", "hi", "hey", "what can you", "what do you"]) or 
                ("help me" in message_lower and not any(word in message_lower for word in ["with", "fix", "solve", "restart", "service", "server"]))):
                intent = "greeting"
            
            # System queries
            elif any(word in message_lower for word in ["which", "how many", "show me", "list"]):
                if "targets" in message_lower or "servers" in message_lower:
                    response = await self.query_system(message)
                    intent = "system_query"
            
            # Troubleshooting questions (specific problems, not general greetings)
            elif (any(word in message_lower for word in ["problem", "issue", "error", "fail", "broken", "not working"]) or 
                  ("help" in message_lower and any(word in message_lower for word in ["with", "fix", "solve", "restart", "service", "server"]))):
                response = await self.handle_troubleshooting_query(message, context)
                intent = "troubleshooting"
            
            # Script generation requests
            elif any(word in message_lower for word in ["create", "generate", "script", "automation"]):
                language = "powershell" if "powershell" in message_lower else "bash"
                response = await self.generate_script(message, language)
                intent = "script_generation"
            
            # Knowledge queries (if we have relevant context)
            elif context and any(word in message_lower for word in ["docker", "container", "management", "best practices", "how to"]):
                response = {
                    "answer": f"Based on the system knowledge: {context[0]['content'][:500]}...",
                    "context": context,
                    "suggestions": [
                        "Create a Docker management script",
                        "Help with container issues",
                        "Show me Docker best practices"
                    ]
                }
                intent = "knowledge_query"
            
            # If no specific intent detected, treat as greeting
            if not response:
                intent = "greeting"
                base_response = "I'm your OpsConductor AI assistant! I can help you with:\n\n" \
                               "🔍 **System Queries**: 'Which targets are tagged with win10?'\n" \
                               "🛠️ **Script Generation**: 'Create a PowerShell script to restart IIS'\n" \
                               "📊 **System Status**: 'How many targets do I have?'\n" \
                               "🔧 **Troubleshooting**: 'Help with service restart issues'\n\n" \
                               "What would you like to do?"
                
                # Add context from similar interactions if available
                if similar_interactions:
                    base_response += f"\n\n💡 I notice you've asked similar questions before. Here's what worked:"
                    for interaction in similar_interactions[:2]:
                        base_response += f"\n- {interaction['metadata'].get('response', 'No response')[:100]}..."
                
                response = {
                    "response": base_response,
                    "intent": intent,
                    "suggestions": [
                        "Which targets are tagged with win10?",
                        "How many targets do I have?",
                        "Create a PowerShell script to check disk space",
                        "Help with service restart issues",
                        "Show me all target groups"
                    ]
                }
            
            # Store this interaction for future learning
            if self.vector_store and response:
                success = not response.get("error")
                await self.vector_store.store_user_interaction(
                    query=message,
                    response=str(response.get("response", response.get("answer", ""))),
                    success=success,
                    metadata={
                        "intent": intent,
                        "user_id": user_id,
                        "has_context": len(context) > 0
                    }
                )
            
            # Add intent and context to response
            if isinstance(response, dict):
                response["intent"] = intent
                if context:
                    response["context_used"] = len(context)
                
                # Normalize response format - ensure we always have a 'response' field
                if "answer" in response and "response" not in response:
                    response["response"] = response["answer"]
                elif "response" not in response and "answer" not in response:
                    response["response"] = "I processed your request but couldn't generate a proper response."
                
                # Add default fields expected by frontend
                if "confidence" not in response:
                    response["confidence"] = 0.8  # Default confidence
                if "execution_started" not in response:
                    response["execution_started"] = False
            
            return response or {"error": "No response generated"}
                
        except Exception as e:
            logger.error(f"Chat failed: {e}")
            return {"error": f"Chat failed: {e}"}

# Global AI instance
ai_engine = OpsConductorAI()