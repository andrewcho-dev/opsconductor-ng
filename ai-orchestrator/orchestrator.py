"""
AI Service Orchestrator
Coordinates communication between NLP, Vector, and LLM services
"""
import httpx
import structlog
from typing import Dict, Any, Optional

logger = structlog.get_logger()

class AIServiceOrchestrator:
    """Orchestrates communication between AI microservices"""
    
    def __init__(self, nlp_url: str, vector_url: str, llm_url: str):
        self.nlp_url = nlp_url
        self.vector_url = vector_url
        self.llm_url = llm_url
        
    async def process_message(self, message: str, user_id: str = "system") -> Dict[str, Any]:
        """Process a message through the AI pipeline"""
        try:
            # Step 1: Parse with NLP service
            parsed_data = await self._parse_message(message)
            
            # Step 2: Search for relevant context in vector database
            context = await self._search_context(message)
            
            # Step 3: Generate response with LLM service
            response = await self._generate_response(message, context, parsed_data)
            
            # Step 4: Store interaction for learning
            await self._store_interaction(message, response, user_id)
            
            return {
                "response": response.get("response", ""),
                "intent": parsed_data.get("intent", "unknown"),
                "confidence": parsed_data.get("confidence", 0.5),
                "parsed_data": parsed_data,
                "success": True
            }
            
        except Exception as e:
            logger.error("Failed to process message", error=str(e))
            return {
                "response": "I encountered an error processing your request.",
                "intent": "error",
                "confidence": 0.0,
                "success": False,
                "error": str(e)
            }
    
    async def _parse_message(self, message: str) -> Dict[str, Any]:
        """Parse message using NLP service"""
        try:
            async with httpx.AsyncClient() as client:
                # Get both parsing and classification
                parse_response = await client.post(
                    f"{self.nlp_url}/nlp/parse",
                    json={"text": message}
                )
                classify_response = await client.post(
                    f"{self.nlp_url}/nlp/classify",
                    json={"text": message}
                )
                
                parsed_data = parse_response.json()
                classified_data = classify_response.json()
                
                # Combine results
                return {
                    **parsed_data,
                    "intent": classified_data.get("intent", "unknown"),
                    "category": classified_data.get("category", "general")
                }
                
        except Exception as e:
            logger.error("Failed to parse message", error=str(e))
            return {
                "operation": "unknown",
                "intent": "unknown",
                "confidence": 0.0,
                "raw_text": message
            }
    
    async def _search_context(self, message: str, limit: int = 3) -> str:
        """Search for relevant context in vector database"""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.vector_url}/vector/search",
                    json={"query": message, "limit": limit}
                )
                
                data = response.json()
                results = data.get("results", [])
                
                if results:
                    context_parts = []
                    for result in results:
                        content = result.get("content", "")
                        if content:
                            context_parts.append(content)
                    
                    return "\n".join(context_parts)
                
                return ""
                
        except Exception as e:
            logger.warning("Failed to search context", error=str(e))
            return ""
    
    async def _generate_response(self, message: str, context: str, parsed_data: Dict[str, Any]) -> Dict[str, Any]:
        """Generate response using LLM service"""
        try:
            # Prepare system prompt based on intent
            intent = parsed_data.get("intent", "unknown")
            system_prompt = self._get_system_prompt(intent)
            
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.llm_url}/llm/chat",
                    json={
                        "message": message,
                        "context": context,
                        "system_prompt": system_prompt,
                        "parsed_data": parsed_data
                    }
                )
                
                return response.json()
                
        except Exception as e:
            logger.error("Failed to generate response", error=str(e))
            return {
                "response": "I'm having trouble generating a response. Please try again.",
                "confidence": 0.1
            }
    
    async def _store_interaction(self, message: str, response: Dict[str, Any], user_id: str):
        """Store interaction in vector database for learning"""
        try:
            interaction_content = f"User ({user_id}): {message}\nAI: {response.get('response', '')}"
            
            async with httpx.AsyncClient() as client:
                await client.post(
                    f"{self.vector_url}/vector/store",
                    json={
                        "content": interaction_content,
                        "category": "interaction",
                        "metadata": {
                            "user_id": user_id,
                            "intent": response.get("intent", "unknown"),
                            "confidence": response.get("confidence", 0.0)
                        }
                    }
                )
                
        except Exception as e:
            logger.warning("Failed to store interaction", error=str(e))
    
    def _get_system_prompt(self, intent: str) -> str:
        """Get appropriate system prompt based on intent"""
        prompts = {
            "automation": """You are OpsConductor AI, an IT operations automation assistant. 
            The user wants to automate something. Be helpful in creating or explaining automation workflows.
            If you need more information to create a proper automation, ask specific questions.""",
            
            "question": """You are OpsConductor AI, an IT operations expert. 
            Answer the user's question clearly and concisely. Use any provided context to give accurate information.""",
            
            "query": """You are OpsConductor AI, helping with system queries and monitoring. 
            Explain what information can be gathered and how to interpret results.""",
            
            "unknown": """You are OpsConductor AI, an IT operations assistant. 
            The user's intent is unclear. Ask clarifying questions to better understand what they need."""
        }
        
        return prompts.get(intent, prompts["unknown"])
    
    async def health_check(self) -> Dict[str, Any]:
        """Check health of all connected services"""
        services = {
            "nlp_service": self.nlp_url,
            "vector_service": self.vector_url,
            "llm_service": self.llm_url
        }
        
        health_status = {}
        
        for service_name, service_url in services.items():
            try:
                async with httpx.AsyncClient() as client:
                    response = await client.get(f"{service_url}/health", timeout=5.0)
                    health_status[service_name] = {
                        "status": "healthy" if response.status_code == 200 else "unhealthy",
                        "url": service_url,
                        "response_time": response.elapsed.total_seconds()
                    }
            except Exception as e:
                health_status[service_name] = {
                    "status": "unhealthy",
                    "url": service_url,
                    "error": str(e)
                }
        
        overall_healthy = all(s["status"] == "healthy" for s in health_status.values())
        
        return {
            "overall_status": "healthy" if overall_healthy else "degraded",
            "services": health_status
        }