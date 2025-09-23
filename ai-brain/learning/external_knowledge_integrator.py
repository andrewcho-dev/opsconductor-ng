"""
External Knowledge Integrator for Multi-Brain AI Architecture

This module integrates external knowledge sources to enhance
AI brain capabilities and keep the system up-to-date.
"""

import logging
import asyncio
from typing import Dict, List, Optional, Any, Set
from enum import Enum
from dataclasses import dataclass, field
from datetime import datetime, timedelta
import json

logger = logging.getLogger(__name__)

class KnowledgeSource(Enum):
    """Types of external knowledge sources."""
    DOCUMENTATION = "documentation"
    API_REFERENCE = "api_reference"
    BEST_PRACTICES = "best_practices"
    SECURITY_ADVISORIES = "security_advisories"
    PERFORMANCE_BENCHMARKS = "performance_benchmarks"
    COMMUNITY_KNOWLEDGE = "community_knowledge"
    VENDOR_UPDATES = "vendor_updates"

class IntegrationStatus(Enum):
    """Status of knowledge integration."""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    OUTDATED = "outdated"

@dataclass
class ExternalKnowledge:
    """External knowledge item."""
    knowledge_id: str
    source: KnowledgeSource
    title: str
    content: str
    source_url: Optional[str] = None
    relevance_score: float = 0.0
    confidence_score: float = 0.0
    applicable_domains: List[str] = field(default_factory=list)
    tags: List[str] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.now)
    last_updated: datetime = field(default_factory=datetime.now)
    metadata: Optional[Dict[str, Any]] = None

@dataclass
class IntegrationTask:
    """Knowledge integration task."""
    task_id: str
    source: KnowledgeSource
    target_brain_id: Optional[str] = None
    priority: int = 5  # 1-10, higher is more important
    status: IntegrationStatus = IntegrationStatus.PENDING
    progress: float = 0.0
    error_message: Optional[str] = None
    created_at: datetime = field(default_factory=datetime.now)
    completed_at: Optional[datetime] = None

class ExternalKnowledgeIntegrator:
    """
    Integrates external knowledge sources to enhance AI brain capabilities.
    
    This component fetches, processes, and integrates knowledge from various
    external sources to keep the multi-brain system current and effective.
    """
    
    def __init__(self):
        """Initialize the external knowledge integrator."""
        self.logger = logging.getLogger(__name__)
        self.knowledge_cache: Dict[str, ExternalKnowledge] = {}
        self.integration_tasks: List[IntegrationTask] = []
        self.source_configurations: Dict[KnowledgeSource, Dict] = {}
        self.brain_subscriptions: Dict[str, Set[KnowledgeSource]] = {}
        self.logger.info("External Knowledge Integrator initialized")
    
    async def configure_knowledge_source(
        self,
        source: KnowledgeSource,
        configuration: Dict[str, Any]
    ):
        """
        Configure a knowledge source.
        
        Args:
            source: Knowledge source type
            configuration: Source-specific configuration
        """
        self.source_configurations[source] = configuration
        self.logger.info(f"Configured knowledge source: {source.value}")
    
    async def subscribe_brain_to_source(
        self,
        brain_id: str,
        sources: List[KnowledgeSource]
    ):
        """
        Subscribe a brain to specific knowledge sources.
        
        Args:
            brain_id: ID of the brain
            sources: List of knowledge sources to subscribe to
        """
        if brain_id not in self.brain_subscriptions:
            self.brain_subscriptions[brain_id] = set()
        
        self.brain_subscriptions[brain_id].update(sources)
        self.logger.info(f"Brain {brain_id} subscribed to {len(sources)} knowledge sources")
    
    async def fetch_external_knowledge(
        self,
        source: KnowledgeSource,
        query: Optional[str] = None,
        limit: int = 10
    ) -> List[ExternalKnowledge]:
        """
        Fetch knowledge from an external source.
        
        Args:
            source: Knowledge source to fetch from
            query: Optional search query
            limit: Maximum number of items to fetch
            
        Returns:
            List of external knowledge items
        """
        self.logger.info(f"Fetching knowledge from {source.value}")
        
        # Simulate fetching external knowledge
        # In a real implementation, this would connect to actual external sources
        knowledge_items = []
        
        if source == KnowledgeSource.DOCUMENTATION:
            knowledge_items = await self._fetch_documentation(query, limit)
        elif source == KnowledgeSource.API_REFERENCE:
            knowledge_items = await self._fetch_api_reference(query, limit)
        elif source == KnowledgeSource.BEST_PRACTICES:
            knowledge_items = await self._fetch_best_practices(query, limit)
        elif source == KnowledgeSource.SECURITY_ADVISORIES:
            knowledge_items = await self._fetch_security_advisories(query, limit)
        elif source == KnowledgeSource.PERFORMANCE_BENCHMARKS:
            knowledge_items = await self._fetch_performance_benchmarks(query, limit)
        elif source == KnowledgeSource.COMMUNITY_KNOWLEDGE:
            knowledge_items = await self._fetch_community_knowledge(query, limit)
        elif source == KnowledgeSource.VENDOR_UPDATES:
            knowledge_items = await self._fetch_vendor_updates(query, limit)
        
        # Cache the knowledge items
        for item in knowledge_items:
            self.knowledge_cache[item.knowledge_id] = item
        
        self.logger.info(f"Fetched {len(knowledge_items)} items from {source.value}")
        return knowledge_items
    
    async def integrate_knowledge_for_brain(
        self,
        brain_id: str,
        knowledge_items: List[ExternalKnowledge]
    ) -> Dict[str, Any]:
        """
        Integrate external knowledge for a specific brain.
        
        Args:
            brain_id: ID of the target brain
            knowledge_items: Knowledge items to integrate
            
        Returns:
            Integration results
        """
        self.logger.info(f"Integrating {len(knowledge_items)} knowledge items for brain {brain_id}")
        
        integrated_count = 0
        failed_count = 0
        
        for item in knowledge_items:
            try:
                # Process and validate the knowledge item
                processed_item = await self._process_knowledge_item(item, brain_id)
                
                if processed_item:
                    # In a real implementation, this would update the brain's knowledge base
                    integrated_count += 1
                    self.logger.debug(f"Integrated knowledge: {item.title}")
                else:
                    failed_count += 1
                    
            except Exception as e:
                failed_count += 1
                self.logger.error(f"Failed to integrate knowledge {item.knowledge_id}: {e}")
        
        results = {
            "brain_id": brain_id,
            "total_items": len(knowledge_items),
            "integrated": integrated_count,
            "failed": failed_count,
            "success_rate": integrated_count / len(knowledge_items) if knowledge_items else 0.0
        }
        
        self.logger.info(f"Integration completed for {brain_id}: {integrated_count}/{len(knowledge_items)} successful")
        return results
    
    async def schedule_knowledge_update(
        self,
        source: KnowledgeSource,
        brain_id: Optional[str] = None,
        priority: int = 5
    ) -> str:
        """
        Schedule a knowledge update task.
        
        Args:
            source: Knowledge source to update from
            brain_id: Optional specific brain to update
            priority: Task priority (1-10)
            
        Returns:
            Task ID
        """
        task_id = f"task_{datetime.now().timestamp()}"
        
        task = IntegrationTask(
            task_id=task_id,
            source=source,
            target_brain_id=brain_id,
            priority=priority
        )
        
        self.integration_tasks.append(task)
        self.logger.info(f"Scheduled knowledge update task: {task_id}")
        
        return task_id
    
    async def process_integration_tasks(self) -> Dict[str, Any]:
        """
        Process pending integration tasks.
        
        Returns:
            Processing results
        """
        pending_tasks = [task for task in self.integration_tasks if task.status == IntegrationStatus.PENDING]
        
        if not pending_tasks:
            return {"processed": 0, "message": "No pending tasks"}
        
        # Sort by priority (higher first)
        pending_tasks.sort(key=lambda x: x.priority, reverse=True)
        
        processed_count = 0
        failed_count = 0
        
        for task in pending_tasks[:5]:  # Process up to 5 tasks at a time
            try:
                task.status = IntegrationStatus.IN_PROGRESS
                
                # Fetch knowledge from the source
                knowledge_items = await self.fetch_external_knowledge(task.source)
                
                if task.target_brain_id:
                    # Integrate for specific brain
                    await self.integrate_knowledge_for_brain(task.target_brain_id, knowledge_items)
                else:
                    # Integrate for all subscribed brains
                    for brain_id, sources in self.brain_subscriptions.items():
                        if task.source in sources:
                            await self.integrate_knowledge_for_brain(brain_id, knowledge_items)
                
                task.status = IntegrationStatus.COMPLETED
                task.completed_at = datetime.now()
                processed_count += 1
                
            except Exception as e:
                task.status = IntegrationStatus.FAILED
                task.error_message = str(e)
                failed_count += 1
                self.logger.error(f"Task {task.task_id} failed: {e}")
        
        return {
            "processed": processed_count,
            "failed": failed_count,
            "remaining": len([t for t in self.integration_tasks if t.status == IntegrationStatus.PENDING])
        }
    
    async def get_knowledge_summary(
        self,
        brain_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Get summary of available knowledge.
        
        Args:
            brain_id: Optional brain ID to filter by subscriptions
            
        Returns:
            Knowledge summary
        """
        total_items = len(self.knowledge_cache)
        
        # Filter by brain subscriptions if specified
        relevant_items = list(self.knowledge_cache.values())
        if brain_id and brain_id in self.brain_subscriptions:
            subscribed_sources = self.brain_subscriptions[brain_id]
            relevant_items = [
                item for item in relevant_items
                if item.source in subscribed_sources
            ]
        
        # Calculate statistics
        source_breakdown = {}
        for item in relevant_items:
            source_breakdown[item.source.value] = source_breakdown.get(item.source.value, 0) + 1
        
        avg_relevance = sum(item.relevance_score for item in relevant_items) / len(relevant_items) if relevant_items else 0.0
        avg_confidence = sum(item.confidence_score for item in relevant_items) / len(relevant_items) if relevant_items else 0.0
        
        return {
            "total_knowledge_items": total_items,
            "relevant_items": len(relevant_items),
            "source_breakdown": source_breakdown,
            "average_relevance_score": avg_relevance,
            "average_confidence_score": avg_confidence,
            "configured_sources": len(self.source_configurations),
            "subscribed_brains": len(self.brain_subscriptions),
            "pending_tasks": len([t for t in self.integration_tasks if t.status == IntegrationStatus.PENDING])
        }
    
    # Simulated fetch methods (in real implementation, these would connect to actual sources)
    
    async def _fetch_documentation(self, query: Optional[str], limit: int) -> List[ExternalKnowledge]:
        """Simulate fetching documentation."""
        return [
            ExternalKnowledge(
                knowledge_id=f"doc_{i}",
                source=KnowledgeSource.DOCUMENTATION,
                title=f"Documentation Item {i}",
                content=f"Sample documentation content for {query or 'general topics'}",
                relevance_score=0.8,
                confidence_score=0.9,
                applicable_domains=["general", "documentation"],
                tags=["docs", "reference"]
            )
            for i in range(min(limit, 3))
        ]
    
    async def _fetch_api_reference(self, query: Optional[str], limit: int) -> List[ExternalKnowledge]:
        """Simulate fetching API reference."""
        return [
            ExternalKnowledge(
                knowledge_id=f"api_{i}",
                source=KnowledgeSource.API_REFERENCE,
                title=f"API Reference {i}",
                content=f"API documentation for {query or 'various endpoints'}",
                relevance_score=0.7,
                confidence_score=0.95,
                applicable_domains=["api", "development"],
                tags=["api", "reference", "endpoints"]
            )
            for i in range(min(limit, 2))
        ]
    
    async def _fetch_best_practices(self, query: Optional[str], limit: int) -> List[ExternalKnowledge]:
        """Simulate fetching best practices."""
        return [
            ExternalKnowledge(
                knowledge_id=f"bp_{i}",
                source=KnowledgeSource.BEST_PRACTICES,
                title=f"Best Practice {i}",
                content=f"Best practice guidelines for {query or 'system operations'}",
                relevance_score=0.85,
                confidence_score=0.8,
                applicable_domains=["operations", "best_practices"],
                tags=["best_practices", "guidelines"]
            )
            for i in range(min(limit, 2))
        ]
    
    async def _fetch_security_advisories(self, query: Optional[str], limit: int) -> List[ExternalKnowledge]:
        """Simulate fetching security advisories."""
        return [
            ExternalKnowledge(
                knowledge_id=f"sec_{i}",
                source=KnowledgeSource.SECURITY_ADVISORIES,
                title=f"Security Advisory {i}",
                content=f"Security advisory regarding {query or 'system vulnerabilities'}",
                relevance_score=0.9,
                confidence_score=0.95,
                applicable_domains=["security", "vulnerabilities"],
                tags=["security", "advisory", "vulnerability"]
            )
            for i in range(min(limit, 1))
        ]
    
    async def _fetch_performance_benchmarks(self, query: Optional[str], limit: int) -> List[ExternalKnowledge]:
        """Simulate fetching performance benchmarks."""
        return [
            ExternalKnowledge(
                knowledge_id=f"perf_{i}",
                source=KnowledgeSource.PERFORMANCE_BENCHMARKS,
                title=f"Performance Benchmark {i}",
                content=f"Performance data for {query or 'system components'}",
                relevance_score=0.75,
                confidence_score=0.85,
                applicable_domains=["performance", "benchmarks"],
                tags=["performance", "benchmarks", "metrics"]
            )
            for i in range(min(limit, 1))
        ]
    
    async def _fetch_community_knowledge(self, query: Optional[str], limit: int) -> List[ExternalKnowledge]:
        """Simulate fetching community knowledge."""
        return [
            ExternalKnowledge(
                knowledge_id=f"comm_{i}",
                source=KnowledgeSource.COMMUNITY_KNOWLEDGE,
                title=f"Community Knowledge {i}",
                content=f"Community insights about {query or 'common issues'}",
                relevance_score=0.6,
                confidence_score=0.7,
                applicable_domains=["community", "troubleshooting"],
                tags=["community", "insights", "troubleshooting"]
            )
            for i in range(min(limit, 2))
        ]
    
    async def _fetch_vendor_updates(self, query: Optional[str], limit: int) -> List[ExternalKnowledge]:
        """Simulate fetching vendor updates."""
        return [
            ExternalKnowledge(
                knowledge_id=f"vendor_{i}",
                source=KnowledgeSource.VENDOR_UPDATES,
                title=f"Vendor Update {i}",
                content=f"Vendor update information for {query or 'product updates'}",
                relevance_score=0.8,
                confidence_score=0.9,
                applicable_domains=["vendor", "updates"],
                tags=["vendor", "updates", "releases"]
            )
            for i in range(min(limit, 1))
        ]
    
    async def _process_knowledge_item(
        self,
        item: ExternalKnowledge,
        brain_id: str
    ) -> Optional[ExternalKnowledge]:
        """
        Process and validate a knowledge item for integration.
        
        Args:
            item: Knowledge item to process
            brain_id: Target brain ID
            
        Returns:
            Processed knowledge item or None if invalid
        """
        # Simulate processing and validation
        if item.relevance_score < 0.5:
            return None  # Too low relevance
        
        if item.confidence_score < 0.6:
            return None  # Too low confidence
        
        # In a real implementation, this would perform more sophisticated processing
        return item
    
    async def cleanup_old_knowledge(self):
        """Clean up old knowledge items to prevent memory bloat."""
        cutoff_time = datetime.now() - timedelta(days=30)  # Keep 30 days of knowledge
        
        old_items = [
            item_id for item_id, item in self.knowledge_cache.items()
            if item.last_updated < cutoff_time
        ]
        
        for item_id in old_items:
            del self.knowledge_cache[item_id]
        
        # Clean up old tasks
        self.integration_tasks = [
            task for task in self.integration_tasks
            if task.created_at >= cutoff_time or task.status == IntegrationStatus.PENDING
        ]
        
        self.logger.debug(f"Cleaned up {len(old_items)} old knowledge items")

# Global instance for easy access
external_knowledge_integrator = ExternalKnowledgeIntegrator()