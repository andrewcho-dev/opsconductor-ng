"""
Centralized Vector Store Client
Unified interface for all services to interact with the vector database
"""
import httpx
import structlog
import hashlib
import json
import time
from typing import Dict, List, Any, Optional
from enum import Enum

logger = structlog.get_logger()

class VectorCollection(Enum):
    """Standardized vector collections across the system"""
    SYSTEM_KNOWLEDGE = "system_knowledge"
    AUTOMATION_PATTERNS = "automation_patterns"
    TROUBLESHOOTING = "troubleshooting_solutions"
    USER_INTERACTIONS = "user_interactions"
    SYSTEM_STATE = "system_state"
    IT_KNOWLEDGE = "it_knowledge"
    PROTOCOL_KNOWLEDGE = "protocol_knowledge"

class VectorStoreClient:
    """Client for interacting with the centralized vector store service"""
    
    def __init__(self, vector_service_url: str = "http://ai-brain:3000"):
        self.vector_service_url = vector_service_url
        self.http_client = httpx.AsyncClient(timeout=30.0)
        
    async def store(
        self,
        content: str,
        collection: VectorCollection,
        metadata: Optional[Dict[str, Any]] = None
    ) -> bool:
        """Store content in vector database"""
        try:
            response = await self.http_client.post(
                f"{self.vector_service_url}/vector/store",
                json={
                    "content": content,
                    "category": collection.value,
                    "metadata": metadata or {}
                }
            )
            return response.status_code == 200
        except Exception as e:
            logger.error(f"Failed to store in vector database: {e}")
            return False
    
    async def search(
        self,
        query: str,
        collection: Optional[VectorCollection] = None,
        limit: int = 5,
        threshold: float = 0.7
    ) -> List[Dict[str, Any]]:
        """Search for similar content in vector database"""
        try:
            request_data = {
                "query": query,
                "limit": limit,
                "threshold": threshold
            }
            
            if collection:
                request_data["category"] = collection.value
            
            response = await self.http_client.post(
                f"{self.vector_service_url}/vector/search",
                json=request_data
            )
            
            if response.status_code == 200:
                data = response.json()
                return data.get("results", [])
            return []
            
        except Exception as e:
            logger.error(f"Failed to search vector database: {e}")
            return []
    
    async def batch_store(
        self,
        items: List[Dict[str, Any]],
        collection: VectorCollection
    ) -> Dict[str, Any]:
        """Store multiple items in vector database"""
        success_count = 0
        failed_count = 0
        
        for item in items:
            content = item.get("content", "")
            metadata = item.get("metadata", {})
            
            if await self.store(content, collection, metadata):
                success_count += 1
            else:
                failed_count += 1
        
        return {
            "success": success_count,
            "failed": failed_count,
            "total": len(items)
        }
    
    async def update(
        self,
        doc_id: str,
        content: str,
        collection: VectorCollection,
        metadata: Optional[Dict[str, Any]] = None
    ) -> bool:
        """Update existing document in vector database"""
        try:
            response = await self.http_client.put(
                f"{self.vector_service_url}/vector/update",
                json={
                    "id": doc_id,
                    "content": content,
                    "category": collection.value,
                    "metadata": metadata or {}
                }
            )
            return response.status_code == 200
        except Exception as e:
            logger.error(f"Failed to update vector database: {e}")
            return False
    
    async def delete(
        self,
        doc_id: str,
        collection: VectorCollection
    ) -> bool:
        """Delete document from vector database"""
        try:
            response = await self.http_client.delete(
                f"{self.vector_service_url}/vector/delete",
                json={
                    "id": doc_id,
                    "category": collection.value
                }
            )
            return response.status_code == 200
        except Exception as e:
            logger.error(f"Failed to delete from vector database: {e}")
            return False
    
    async def get_collection_stats(
        self,
        collection: VectorCollection
    ) -> Dict[str, Any]:
        """Get statistics for a specific collection"""
        try:
            response = await self.http_client.get(
                f"{self.vector_service_url}/vector/stats/{collection.value}"
            )
            
            if response.status_code == 200:
                return response.json()
            return {}
            
        except Exception as e:
            logger.error(f"Failed to get collection stats: {e}")
            return {}
    
    async def cleanup(self):
        """Cleanup resources"""
        await self.http_client.aclose()

class KnowledgeManager:
    """High-level knowledge management using vector store"""
    
    def __init__(self, vector_client: VectorStoreClient):
        self.vector_client = vector_client
    
    async def learn_from_interaction(
        self,
        user_query: str,
        ai_response: str,
        success: bool,
        user_id: str = "anonymous",
        feedback: Optional[str] = None
    ):
        """Learn from user interaction"""
        interaction_content = f"Q: {user_query}\nA: {ai_response}"
        
        metadata = {
            "user_id": user_id,
            "success": success,
            "timestamp": time.time()
        }
        
        if feedback:
            metadata["feedback"] = feedback
            interaction_content += f"\nFeedback: {feedback}"
        
        await self.vector_client.store(
            content=interaction_content,
            collection=VectorCollection.USER_INTERACTIONS,
            metadata=metadata
        )
    
    async def store_automation_pattern(
        self,
        workflow_name: str,
        workflow_definition: Dict[str, Any],
        success_rate: float,
        execution_count: int
    ):
        """Store successful automation pattern"""
        content = f"Workflow: {workflow_name}\n"
        content += f"Definition: {json.dumps(workflow_definition, indent=2)}\n"
        content += f"Success Rate: {success_rate:.2%}\n"
        content += f"Executions: {execution_count}"
        
        await self.vector_client.store(
            content=content,
            collection=VectorCollection.AUTOMATION_PATTERNS,
            metadata={
                "name": workflow_name,
                "success_rate": success_rate,
                "execution_count": execution_count,
                "last_updated": time.time()
            }
        )
    
    async def find_similar_issues(
        self,
        issue_description: str,
        limit: int = 3
    ) -> List[Dict[str, Any]]:
        """Find similar issues and their solutions"""
        return await self.vector_client.search(
            query=issue_description,
            collection=VectorCollection.TROUBLESHOOTING,
            limit=limit
        )
    
    async def get_relevant_context(
        self,
        query: str,
        collections: Optional[List[VectorCollection]] = None
    ) -> str:
        """Get relevant context from multiple collections"""
        if not collections:
            collections = [
                VectorCollection.SYSTEM_KNOWLEDGE,
                VectorCollection.IT_KNOWLEDGE,
                VectorCollection.PROTOCOL_KNOWLEDGE
            ]
        
        all_results = []
        for collection in collections:
            results = await self.vector_client.search(
                query=query,
                collection=collection,
                limit=2
            )
            all_results.extend(results)
        
        # Sort by relevance score and take top results
        all_results.sort(key=lambda x: x.get("score", 0), reverse=True)
        top_results = all_results[:5]
        
        # Combine content
        context_parts = []
        for result in top_results:
            content = result.get("content", "")
            if content:
                context_parts.append(content)
        
        return "\n---\n".join(context_parts)