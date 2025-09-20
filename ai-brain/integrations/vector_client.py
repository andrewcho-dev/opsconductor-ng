"""
OpsConductor AI Vector Store - GPU-accelerated ChromaDB integration
"""
import asyncio
import json
import logging
import hashlib
import torch
from typing import Dict, List, Optional, Any, Tuple
import chromadb
from chromadb.config import Settings
import numpy as np
from datetime import datetime, timedelta
import uuid
from sentence_transformers import SentenceTransformer
import structlog

logger = structlog.get_logger()

class OpsConductorVectorStore:
    """Enhanced vector storage for AI knowledge and patterns"""
    
    def __init__(self, chroma_client):
        self.client = chroma_client
        self.collections = {}
        
        # Initialize GPU-accelerated embedding model
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        logger.info(f"Vector Store using device: {self.device}")
        
        try:
            # Load sentence transformer with GPU support
            self.embedding_model_name = "all-MiniLM-L6-v2"
            self.embedding_model = SentenceTransformer(
                self.embedding_model_name, 
                device=self.device
            )
            
            if torch.cuda.is_available():
                gpu_memory = torch.cuda.get_device_properties(0).total_memory / 1024**3
                logger.info(f"GPU memory available: {gpu_memory:.2f} GB")
                logger.info(f"Embedding model loaded on {self.device}")
            
        except Exception as e:
            logger.error(f"Failed to load embedding model: {e}")
            self.embedding_model = None
        
    async def initialize_collections(self):
        """Initialize all required collections"""
        try:
            # Collection for system knowledge (documentation, procedures)
            self.collections['knowledge'] = await self._get_or_create_collection(
                name="system_knowledge",
                metadata={"description": "System documentation and procedures"}
            )
            
            # Collection for automation patterns
            self.collections['patterns'] = await self._get_or_create_collection(
                name="automation_patterns", 
                metadata={"description": "Successful automation workflows and patterns"}
            )
            
            # Collection for troubleshooting solutions
            self.collections['solutions'] = await self._get_or_create_collection(
                name="troubleshooting_solutions",
                metadata={"description": "Problem-solution pairs and fixes"}
            )
            
            # Collection for user interactions and feedback
            self.collections['interactions'] = await self._get_or_create_collection(
                name="user_interactions",
                metadata={"description": "User queries and successful responses"}
            )
            
            # Collection for system state snapshots
            self.collections['system_state'] = await self._get_or_create_collection(
                name="system_state",
                metadata={"description": "Historical system state information"}
            )
            
            logger.info(f"Initialized {len(self.collections)} vector collections")
            return True
            
        except Exception as e:
            logger.error(f"Failed to initialize collections: {e}")
            return False
    
    async def _get_or_create_collection(self, name: str, metadata: Dict = None):
        """Get existing collection or create new one"""
        try:
            # Try to get existing collection
            collection = self.client.get_collection(name=name)
            logger.info(f"Found existing collection: {name}")
            return collection
        except Exception:
            # Create new collection
            collection = self.client.create_collection(
                name=name,
                metadata=metadata or {}
            )
            logger.info(f"Created new collection: {name}")
            return collection
    
    async def store_knowledge(self, content: str, title: str, category: str, 
                            metadata: Dict = None) -> str:
        """Store system knowledge/documentation"""
        try:
            doc_id = str(uuid.uuid4())
            
            # Prepare metadata (ensure all values are strings, ints, floats, or bools)
            doc_metadata = {
                "title": str(title),
                "category": str(category),
                "timestamp": datetime.utcnow().isoformat(),
                "content_hash": hashlib.md5(content.encode()).hexdigest()
            }
            
            # Add additional metadata, ensuring proper types
            if metadata:
                for key, value in metadata.items():
                    if value is not None and isinstance(value, (str, int, float, bool)):
                        doc_metadata[key] = value
                    elif value is not None:
                        doc_metadata[key] = str(value)
            
            # Store in knowledge collection
            self.collections['knowledge'].add(
                documents=[content],
                metadatas=[doc_metadata],
                ids=[doc_id]
            )
            
            logger.info(f"Stored knowledge document: {title} ({category})")
            return doc_id
            
        except Exception as e:
            logger.error(f"Failed to store knowledge: {e}")
            raise
    
    async def store_automation_pattern(self, workflow: Dict, success_rate: float,
                                     execution_time: float, metadata: Dict = None) -> str:
        """Store successful automation patterns"""
        try:
            pattern_id = str(uuid.uuid4())
            
            # Create searchable content from workflow
            content = self._workflow_to_text(workflow)
            
            # Prepare metadata
            pattern_metadata = {
                "workflow_id": str(workflow.get('id', '')),
                "operation": str(workflow.get('operation', '')),
                "target_type": str(workflow.get('target_type', '')),
                "success_rate": float(success_rate),
                "execution_time": float(execution_time),
                "timestamp": datetime.utcnow().isoformat(),
                "step_count": int(len(workflow.get('steps', [])))
            }
            
            # Add additional metadata, ensuring proper types
            if metadata:
                for key, value in metadata.items():
                    if value is not None and isinstance(value, (str, int, float, bool)):
                        pattern_metadata[key] = value
                    elif value is not None:
                        pattern_metadata[key] = str(value)
            
            # Store in patterns collection
            self.collections['patterns'].add(
                documents=[content],
                metadatas=[pattern_metadata],
                ids=[pattern_id]
            )
            
            logger.info(f"Stored automation pattern: {workflow.get('operation', 'unknown')} "
                       f"(success: {success_rate:.2f})")
            return pattern_id
            
        except Exception as e:
            logger.error(f"Failed to store automation pattern: {e}")
            raise
    
    async def store_solution(self, problem: str, solution: str, 
                           success_count: int = 1, metadata: Dict = None) -> str:
        """Store troubleshooting solutions"""
        try:
            solution_id = str(uuid.uuid4())
            
            # Combine problem and solution for better search
            content = f"Problem: {problem}\n\nSolution: {solution}"
            
            # Prepare metadata
            solution_metadata = {
                "problem": str(problem),
                "solution": str(solution),
                "success_count": int(success_count),
                "timestamp": datetime.utcnow().isoformat(),
                "problem_hash": hashlib.md5(problem.encode()).hexdigest()
            }
            
            # Add additional metadata, ensuring proper types
            if metadata:
                for key, value in metadata.items():
                    if value is not None and isinstance(value, (str, int, float, bool)):
                        solution_metadata[key] = value
                    elif value is not None:
                        solution_metadata[key] = str(value)
            
            # Store in solutions collection
            self.collections['solutions'].add(
                documents=[content],
                metadatas=[solution_metadata],
                ids=[solution_id]
            )
            
            logger.info(f"Stored solution for problem: {problem[:50]}...")
            return solution_id
            
        except Exception as e:
            logger.error(f"Failed to store solution: {e}")
            raise
    
    async def store_user_interaction(self, query: str, response: str, 
                                   success: bool, metadata: Dict = None) -> str:
        """Store user interactions for learning"""
        try:
            interaction_id = str(uuid.uuid4())
            
            # Create searchable content
            content = f"Query: {query}\n\nResponse: {response}"
            
            # Prepare metadata
            interaction_metadata = {
                "query": str(query),
                "response": str(response),
                "success": bool(success),
                "timestamp": datetime.utcnow().isoformat(),
                "query_hash": hashlib.md5(query.encode()).hexdigest()
            }
            
            # Add additional metadata, ensuring proper types
            if metadata:
                for key, value in metadata.items():
                    if value is not None and isinstance(value, (str, int, float, bool)):
                        interaction_metadata[key] = value
                    elif value is not None:
                        interaction_metadata[key] = str(value)
            
            # Store in interactions collection
            self.collections['interactions'].add(
                documents=[content],
                metadatas=[interaction_metadata],
                ids=[interaction_id]
            )
            
            logger.debug(f"Stored user interaction: {query[:30]}...")
            return interaction_id
            
        except Exception as e:
            logger.error(f"Failed to store user interaction: {e}")
            raise
    
    async def search_knowledge(self, query: str, limit: int = 5) -> List[Dict]:
        """Search system knowledge"""
        try:
            results = self.collections['knowledge'].query(
                query_texts=[query],
                n_results=limit
            )
            
            return self._format_search_results(results)
            
        except Exception as e:
            logger.error(f"Failed to search knowledge: {e}")
            return []
    
    async def search_patterns(self, query: str, min_success_rate: float = 0.7,
                            limit: int = 5) -> List[Dict]:
        """Search automation patterns"""
        try:
            results = self.collections['patterns'].query(
                query_texts=[query],
                n_results=limit,
                where={"success_rate": {"$gte": min_success_rate}}
            )
            
            return self._format_search_results(results)
            
        except Exception as e:
            logger.error(f"Failed to search patterns: {e}")
            return []
    
    async def search_solutions(self, problem: str, limit: int = 3) -> List[Dict]:
        """Search for similar problems and solutions"""
        try:
            results = self.collections['solutions'].query(
                query_texts=[problem],
                n_results=limit
            )
            
            return self._format_search_results(results)
            
        except Exception as e:
            logger.error(f"Failed to search solutions: {e}")
            return []
    
    async def find_similar_interactions(self, query: str, 
                                      successful_only: bool = True,
                                      limit: int = 5) -> List[Dict]:
        """Find similar successful user interactions"""
        try:
            where_clause = {"success": True} if successful_only else None
            
            results = self.collections['interactions'].query(
                query_texts=[query],
                n_results=limit,
                where=where_clause
            )
            
            return self._format_search_results(results)
            
        except Exception as e:
            logger.error(f"Failed to find similar interactions: {e}")
            return []
    
    async def get_collection_stats(self) -> Dict[str, Any]:
        """Get statistics about all collections"""
        try:
            stats = {}
            
            for name, collection in self.collections.items():
                count = collection.count()
                stats[name] = {
                    "document_count": count,
                    "collection_name": collection.name
                }
            
            return stats
            
        except Exception as e:
            logger.error(f"Failed to get collection stats: {e}")
            return {}
    
    def _workflow_to_text(self, workflow: Dict) -> str:
        """Convert workflow to searchable text"""
        text_parts = []
        
        # Add basic info
        text_parts.append(f"Operation: {workflow.get('operation', 'unknown')}")
        text_parts.append(f"Target: {workflow.get('target_type', 'unknown')}")
        
        # Add steps
        steps = workflow.get('steps', [])
        for i, step in enumerate(steps, 1):
            step_text = f"Step {i}: {step.get('name', 'unnamed')}"
            if step.get('command'):
                step_text += f" - Command: {step['command']}"
            text_parts.append(step_text)
        
        # Add description if available
        if workflow.get('description'):
            text_parts.append(f"Description: {workflow['description']}")
        
        return "\n".join(text_parts)
    
    def _format_search_results(self, results: Dict) -> List[Dict]:
        """Format ChromaDB search results"""
        formatted_results = []
        
        if not results or not results.get('documents'):
            return formatted_results
        
        documents = results['documents'][0] if results['documents'] else []
        metadatas = results['metadatas'][0] if results.get('metadatas') else []
        distances = results['distances'][0] if results.get('distances') else []
        ids = results['ids'][0] if results.get('ids') else []
        
        for i, doc in enumerate(documents):
            result = {
                "id": ids[i] if i < len(ids) else None,
                "content": doc,
                "metadata": metadatas[i] if i < len(metadatas) else {},
                "distance": distances[i] if i < len(distances) else None,
                "similarity": 1 - distances[i] if i < len(distances) else None
            }
            formatted_results.append(result)
        
        return formatted_results
    
    def get_gpu_status(self) -> Dict[str, Any]:
        """Get current GPU status and memory usage"""
        try:
            if not torch.cuda.is_available():
                return {
                    "gpu_available": False,
                    "device": "cpu",
                    "message": "No GPU available"
                }
            
            device_count = torch.cuda.device_count()
            current_device = torch.cuda.current_device()
            device_name = torch.cuda.get_device_name(current_device)
            
            # Get memory info
            memory_allocated = torch.cuda.memory_allocated(current_device) / 1024**3  # GB
            memory_reserved = torch.cuda.memory_reserved(current_device) / 1024**3   # GB
            memory_total = torch.cuda.get_device_properties(current_device).total_memory / 1024**3  # GB
            
            return {
                "gpu_available": True,
                "device": f"cuda:{current_device}",
                "device_name": device_name,
                "device_count": device_count,
                "memory_allocated_gb": round(memory_allocated, 2),
                "memory_reserved_gb": round(memory_reserved, 2),
                "memory_total_gb": round(memory_total, 2),
                "memory_free_gb": round(memory_total - memory_reserved, 2),
                "cuda_version": torch.version.cuda,
                "embedding_model": self.embedding_model_name if self.embedding_model else "None",
                "embedding_device": str(self.device)
            }
            
        except Exception as e:
            logger.error(f"Failed to get GPU status: {e}")
            return {
                "gpu_available": False,
                "device": "cpu",
                "error": str(e)
            }