"""
OpsConductor AI Brain - Modern Knowledge API Router

This module provides REST API endpoints for the IT knowledge base,
replacing the legacy learning API with modern knowledge engine capabilities.
"""

import logging
from typing import List, Optional, Dict, Any
from datetime import datetime
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field

from knowledge_engine.it_knowledge_base import (
    ITKnowledgeBase, 
    KnowledgeCategory, 
    Severity, 
    KnowledgeType,
    KnowledgeEntry
)

logger = logging.getLogger(__name__)

# Initialize knowledge base
knowledge_base = ITKnowledgeBase()

# Create router
knowledge_router = APIRouter(prefix="/ai/knowledge", tags=["AI Knowledge"])

# Request/Response Models
class RecommendationRequest(BaseModel):
    issue_description: str = Field(..., description="Description of the issue or problem")
    system_type: Optional[str] = Field(None, description="Type of system (e.g., linux_server, web_service)")
    user_id: Optional[str] = Field(None, description="User ID for personalized recommendations")

class KnowledgeSearchRequest(BaseModel):
    keywords: List[str] = Field(..., description="Keywords to search for")
    category: Optional[str] = Field(None, description="Knowledge category filter")
    severity: Optional[str] = Field(None, description="Severity level filter")
    system_type: Optional[str] = Field(None, description="System type filter")

class KnowledgeEntryResponse(BaseModel):
    id: str
    title: str
    category: str
    knowledge_type: str
    description: str
    severity: str
    tags: List[str]
    applicable_systems: List[str]
    steps: List[Dict[str, Any]]
    related_entries: List[str]
    references: List[str]
    last_updated: Optional[str]
    author: str
    version: str

def _convert_knowledge_entry(entry: KnowledgeEntry) -> KnowledgeEntryResponse:
    """Convert KnowledgeEntry to response model"""
    return KnowledgeEntryResponse(
        id=entry.id,
        title=entry.title,
        category=entry.category.value,
        knowledge_type=entry.knowledge_type.value,
        description=entry.description,
        severity=entry.severity.value,
        tags=entry.tags,
        applicable_systems=entry.applicable_systems,
        steps=[{
            "step_number": step.step_number,
            "description": step.description,
            "command": step.command,
            "expected_result": step.expected_result,
            "troubleshooting_notes": step.troubleshooting_notes,
            "prerequisites": step.prerequisites
        } for step in entry.steps],
        related_entries=entry.related_entries,
        references=entry.references,
        last_updated=entry.last_updated,
        author=entry.author,
        version=entry.version
    )

@knowledge_router.post("/recommendations")
async def get_recommendations(request: RecommendationRequest):
    """Get knowledge-based recommendations for an issue (replaces /ai/learning/recommendations/{user_id})"""
    try:
        # Get recommendations from knowledge base
        recommendations = knowledge_base.get_recommendations_for_issue(
            issue_description=request.issue_description,
            system_type=request.system_type
        )
        
        # Convert to response format
        recommendation_responses = [_convert_knowledge_entry(entry) for entry in recommendations]
        
        return {
            "success": True,
            "user_id": request.user_id,
            "issue_description": request.issue_description,
            "system_type": request.system_type,
            "recommendations": recommendation_responses,
            "count": len(recommendation_responses),
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Failed to get recommendations: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@knowledge_router.get("/troubleshooting")
async def get_troubleshooting_procedures(
    keywords: List[str] = Query(..., description="Keywords describing the issue"),
    system_type: Optional[str] = Query(None, description="System type filter")
):
    """Get troubleshooting procedures (replaces /ai/learning/system-health)"""
    try:
        # Get troubleshooting procedures
        procedures = knowledge_base.get_troubleshooting_procedures(keywords)
        
        # Filter by system type if provided
        if system_type:
            procedures = [p for p in procedures if system_type in p.applicable_systems]
        
        # Convert to response format
        procedure_responses = [_convert_knowledge_entry(entry) for entry in procedures]
        
        return {
            "success": True,
            "keywords": keywords,
            "system_type": system_type,
            "troubleshooting_procedures": procedure_responses,
            "count": len(procedure_responses),
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Failed to get troubleshooting procedures: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@knowledge_router.get("/security-guidelines")
async def get_security_guidelines(
    system_type: Optional[str] = Query(None, description="System type filter"),
    severity: Optional[str] = Query(None, description="Minimum severity level")
):
    """Get security guidelines and alerts (replaces /ai/learning/anomalies)"""
    try:
        # Get security guidelines
        guidelines = knowledge_base.get_security_guidelines(system_type)
        
        # Filter by severity if provided
        if severity:
            try:
                min_severity = Severity(severity)
                severity_order = {
                    Severity.INFO: 0,
                    Severity.LOW: 1,
                    Severity.MEDIUM: 2,
                    Severity.HIGH: 3,
                    Severity.CRITICAL: 4
                }
                min_level = severity_order[min_severity]
                guidelines = [g for g in guidelines if severity_order[g.severity] >= min_level]
            except ValueError:
                raise HTTPException(status_code=400, detail=f"Invalid severity level: {severity}")
        
        # Convert to response format
        guideline_responses = [_convert_knowledge_entry(entry) for entry in guidelines]
        
        return {
            "success": True,
            "system_type": system_type,
            "severity_filter": severity,
            "security_guidelines": guideline_responses,
            "count": len(guideline_responses),
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Failed to get security guidelines: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@knowledge_router.get("/best-practices")
async def get_best_practices(
    system_type: str = Query(..., description="System type to get best practices for")
):
    """Get best practices for a system type"""
    try:
        # Get best practices
        practices = knowledge_base.get_best_practices_for_system(system_type)
        
        # Convert to response format
        practice_responses = [_convert_knowledge_entry(entry) for entry in practices]
        
        return {
            "success": True,
            "system_type": system_type,
            "best_practices": practice_responses,
            "count": len(practice_responses),
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Failed to get best practices: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@knowledge_router.post("/search")
async def search_knowledge(request: KnowledgeSearchRequest):
    """Search knowledge base by keywords and filters"""
    try:
        # Start with keyword search
        results = knowledge_base.search_by_keywords(request.keywords)
        
        # Apply filters
        if request.category:
            try:
                category_filter = KnowledgeCategory(request.category)
                results = [r for r in results if r.category == category_filter]
            except ValueError:
                raise HTTPException(status_code=400, detail=f"Invalid category: {request.category}")
        
        if request.severity:
            try:
                severity_filter = Severity(request.severity)
                results = [r for r in results if r.severity == severity_filter]
            except ValueError:
                raise HTTPException(status_code=400, detail=f"Invalid severity: {request.severity}")
        
        if request.system_type:
            results = [r for r in results if request.system_type in r.applicable_systems]
        
        # Convert to response format
        result_responses = [_convert_knowledge_entry(entry) for entry in results]
        
        return {
            "success": True,
            "search_criteria": {
                "keywords": request.keywords,
                "category": request.category,
                "severity": request.severity,
                "system_type": request.system_type
            },
            "results": result_responses,
            "count": len(result_responses),
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Failed to search knowledge base: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@knowledge_router.get("/entry/{entry_id}")
async def get_knowledge_entry(entry_id: str):
    """Get a specific knowledge entry by ID"""
    try:
        entry = knowledge_base.get_knowledge_entry(entry_id)
        
        if not entry:
            raise HTTPException(status_code=404, detail=f"Knowledge entry not found: {entry_id}")
        
        return {
            "success": True,
            "entry": _convert_knowledge_entry(entry),
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get knowledge entry: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@knowledge_router.get("/related/{entry_id}")
async def get_related_knowledge(entry_id: str):
    """Get knowledge entries related to a specific entry"""
    try:
        related_entries = knowledge_base.get_related_knowledge(entry_id)
        
        # Convert to response format
        related_responses = [_convert_knowledge_entry(entry) for entry in related_entries]
        
        return {
            "success": True,
            "entry_id": entry_id,
            "related_entries": related_responses,
            "count": len(related_responses),
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Failed to get related knowledge: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@knowledge_router.get("/statistics")
async def get_knowledge_statistics():
    """Get knowledge base statistics (replaces /ai/learning/stats)"""
    try:
        stats = knowledge_base.get_knowledge_statistics()
        
        return {
            "success": True,
            "statistics": stats,
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Failed to get knowledge statistics: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@knowledge_router.get("/categories")
async def get_available_categories():
    """Get all available knowledge categories"""
    try:
        categories = [category.value for category in KnowledgeCategory]
        severities = [severity.value for severity in Severity]
        knowledge_types = [ktype.value for ktype in KnowledgeType]
        
        return {
            "success": True,
            "categories": categories,
            "severities": severities,
            "knowledge_types": knowledge_types,
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Failed to get categories: {e}")
        raise HTTPException(status_code=500, detail=str(e))