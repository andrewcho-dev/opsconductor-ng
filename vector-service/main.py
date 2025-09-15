from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import structlog
import os
import sys
from datetime import datetime
from typing import List, Optional, Dict, Any
import chromadb
from chromadb.config import Settings

# Add shared directory to path
sys.path.append('/app/shared')
from base_service import BaseService

# Configure structured logging
structlog.configure(
    processors=[
        structlog.stdlib.filter_by_level,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.processors.UnicodeDecoder(),
        structlog.processors.JSONRenderer()
    ],
    context_class=dict,
    logger_factory=structlog.stdlib.LoggerFactory(),
    wrapper_class=structlog.stdlib.BoundLogger,
    cache_logger_on_first_use=True,
)

logger = structlog.get_logger()

class VectorService(BaseService):
    def __init__(self):
        super().__init__("vector-service")

app = FastAPI(
    title="OpsConductor Vector Service",
    description="Vector database service for AI knowledge storage and retrieval",
    version="1.0.0"
)

# Initialize service
service = VectorService()

# Import vector store after service initialization
from vector_store import OpsConductorVectorStore

# Initialize ChromaDB
chroma_client = None
vector_store = None

@app.on_event("startup")
async def startup_event():
    """Initialize vector database on startup"""
    global chroma_client, vector_store
    try:
        logger.info("Initializing ChromaDB...")
        
        # Configure ChromaDB
        chroma_client = chromadb.Client(Settings(
            chroma_db_impl="duckdb+parquet",
            persist_directory="/app/data/chroma"
        ))
        
        # Initialize vector store
        vector_store = OpsConductorVectorStore(chroma_client)
        success = await vector_store.initialize_collections()
        
        if success:
            logger.info("Vector database initialized successfully")
        else:
            logger.error("Failed to initialize vector database")
            
    except Exception as e:
        logger.error("Vector database initialization failed", error=str(e))

# Request/Response models
class StoreRequest(BaseModel):
    content: str
    category: str = "general"
    title: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None

class StoreResponse(BaseModel):
    success: bool
    document_id: Optional[str] = None
    message: str

class SearchRequest(BaseModel):
    query: str
    limit: int = 5
    category: Optional[str] = None

class SearchResponse(BaseModel):
    results: List[Dict[str, Any]]
    total_results: int

class PatternRequest(BaseModel):
    workflow: Dict[str, Any]
    success_rate: float
    execution_time: float
    metadata: Optional[Dict[str, Any]] = None

class SolutionRequest(BaseModel):
    problem: str
    solution: str
    success_count: int = 1
    metadata: Optional[Dict[str, Any]] = None

class InteractionRequest(BaseModel):
    query: str
    response: str
    success: bool
    metadata: Optional[Dict[str, Any]] = None

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "vector-service",
        "timestamp": datetime.utcnow().isoformat(),
        "chroma_initialized": chroma_client is not None
    }

@app.get("/info")
async def service_info():
    """Service information endpoint"""
    return {
        "service": "vector-service",
        "version": "1.0.0",
        "description": "Vector database service for AI knowledge storage and retrieval",
        "capabilities": [
            "Knowledge storage and retrieval",
            "Automation pattern storage",
            "Solution database",
            "User interaction learning",
            "Semantic search"
        ],
        "collections": [
            "system_knowledge",
            "automation_patterns", 
            "troubleshooting_solutions",
            "user_interactions",
            "system_state"
        ]
    }

@app.post("/vector/store", response_model=StoreResponse)
async def store_knowledge(request: StoreRequest):
    """Store knowledge in vector database"""
    try:
        if not vector_store:
            raise HTTPException(status_code=503, detail="Vector store not initialized")
        
        logger.info("Storing knowledge", category=request.category, content_length=len(request.content))
        
        title = request.title or f"{request.category} document"
        doc_id = await vector_store.store_knowledge(
            content=request.content,
            title=title,
            category=request.category,
            metadata=request.metadata
        )
        
        return StoreResponse(
            success=True,
            document_id=doc_id,
            message=f"Knowledge stored successfully in category '{request.category}'"
        )
        
    except Exception as e:
        logger.error("Failed to store knowledge", error=str(e))
        raise HTTPException(status_code=500, detail=f"Failed to store knowledge: {str(e)}")

@app.post("/vector/search", response_model=SearchResponse)
async def search_knowledge(request: SearchRequest):
    """Search knowledge in vector database"""
    try:
        if not vector_store:
            raise HTTPException(status_code=503, detail="Vector store not initialized")
        
        logger.info("Searching knowledge", query=request.query, limit=request.limit)
        
        # Search in knowledge collection
        results = await vector_store.search_knowledge(request.query, request.limit)
        
        return SearchResponse(
            results=results,
            total_results=len(results)
        )
        
    except Exception as e:
        logger.error("Failed to search knowledge", error=str(e))
        raise HTTPException(status_code=500, detail=f"Failed to search knowledge: {str(e)}")

@app.post("/vector/store-pattern", response_model=StoreResponse)
async def store_automation_pattern(request: PatternRequest):
    """Store automation pattern in vector database"""
    try:
        if not vector_store:
            raise HTTPException(status_code=503, detail="Vector store not initialized")
        
        logger.info("Storing automation pattern", workflow_id=request.workflow.get("id"))
        
        pattern_id = await vector_store.store_automation_pattern(
            workflow=request.workflow,
            success_rate=request.success_rate,
            execution_time=request.execution_time,
            metadata=request.metadata
        )
        
        return StoreResponse(
            success=True,
            document_id=pattern_id,
            message="Automation pattern stored successfully"
        )
        
    except Exception as e:
        logger.error("Failed to store automation pattern", error=str(e))
        raise HTTPException(status_code=500, detail=f"Failed to store pattern: {str(e)}")

@app.post("/vector/search-patterns", response_model=SearchResponse)
async def search_automation_patterns(request: SearchRequest):
    """Search automation patterns in vector database"""
    try:
        if not vector_store:
            raise HTTPException(status_code=503, detail="Vector store not initialized")
        
        logger.info("Searching automation patterns", query=request.query)
        
        results = await vector_store.search_patterns(request.query, limit=request.limit)
        
        return SearchResponse(
            results=results,
            total_results=len(results)
        )
        
    except Exception as e:
        logger.error("Failed to search patterns", error=str(e))
        raise HTTPException(status_code=500, detail=f"Failed to search patterns: {str(e)}")

@app.post("/vector/store-solution", response_model=StoreResponse)
async def store_solution(request: SolutionRequest):
    """Store troubleshooting solution in vector database"""
    try:
        if not vector_store:
            raise HTTPException(status_code=503, detail="Vector store not initialized")
        
        logger.info("Storing solution", problem_length=len(request.problem))
        
        solution_id = await vector_store.store_solution(
            problem=request.problem,
            solution=request.solution,
            success_count=request.success_count,
            metadata=request.metadata
        )
        
        return StoreResponse(
            success=True,
            document_id=solution_id,
            message="Solution stored successfully"
        )
        
    except Exception as e:
        logger.error("Failed to store solution", error=str(e))
        raise HTTPException(status_code=500, detail=f"Failed to store solution: {str(e)}")

@app.post("/vector/search-solutions", response_model=SearchResponse)
async def search_solutions(request: SearchRequest):
    """Search troubleshooting solutions in vector database"""
    try:
        if not vector_store:
            raise HTTPException(status_code=503, detail="Vector store not initialized")
        
        logger.info("Searching solutions", query=request.query)
        
        results = await vector_store.search_solutions(request.query, limit=request.limit)
        
        return SearchResponse(
            results=results,
            total_results=len(results)
        )
        
    except Exception as e:
        logger.error("Failed to search solutions", error=str(e))
        raise HTTPException(status_code=500, detail=f"Failed to search solutions: {str(e)}")

@app.post("/vector/store-interaction", response_model=StoreResponse)
async def store_user_interaction(request: InteractionRequest):
    """Store user interaction for learning"""
    try:
        if not vector_store:
            raise HTTPException(status_code=503, detail="Vector store not initialized")
        
        logger.info("Storing user interaction", success=request.success)
        
        interaction_id = await vector_store.store_user_interaction(
            query=request.query,
            response=request.response,
            success=request.success,
            metadata=request.metadata
        )
        
        return StoreResponse(
            success=True,
            document_id=interaction_id,
            message="User interaction stored successfully"
        )
        
    except Exception as e:
        logger.error("Failed to store interaction", error=str(e))
        raise HTTPException(status_code=500, detail=f"Failed to store interaction: {str(e)}")

@app.post("/vector/search-interactions", response_model=SearchResponse)
async def search_user_interactions(request: SearchRequest):
    """Search similar user interactions"""
    try:
        if not vector_store:
            raise HTTPException(status_code=503, detail="Vector store not initialized")
        
        logger.info("Searching user interactions", query=request.query)
        
        results = await vector_store.find_similar_interactions(request.query, limit=request.limit)
        
        return SearchResponse(
            results=results,
            total_results=len(results)
        )
        
    except Exception as e:
        logger.error("Failed to search interactions", error=str(e))
        raise HTTPException(status_code=500, detail=f"Failed to search interactions: {str(e)}")

@app.get("/vector/stats")
async def get_vector_stats():
    """Get vector database statistics"""
    try:
        if not vector_store:
            raise HTTPException(status_code=503, detail="Vector store not initialized")
        
        stats = await vector_store.get_collection_stats()
        
        return {
            "status": "success",
            "collections": stats,
            "total_documents": sum(s.get("document_count", 0) for s in stats.values()),
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error("Failed to get vector stats", error=str(e))
        raise HTTPException(status_code=500, detail=f"Failed to get stats: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=3000)