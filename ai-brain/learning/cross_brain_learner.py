"""
Cross-Brain Learner for Multi-Brain AI Architecture

This module facilitates knowledge sharing and collaborative learning
between different AI brains in the multi-brain system.
"""

import logging
import asyncio
from typing import Dict, List, Optional, Any, Set, Tuple
from enum import Enum
from dataclasses import dataclass, field
from datetime import datetime, timedelta
import json

logger = logging.getLogger(__name__)

class KnowledgeType(Enum):
    """Types of knowledge that can be shared between brains."""
    PATTERN_RECOGNITION = "pattern_recognition"
    DECISION_STRATEGY = "decision_strategy"
    ERROR_HANDLING = "error_handling"
    OPTIMIZATION_TECHNIQUE = "optimization_technique"
    CONTEXT_UNDERSTANDING = "context_understanding"
    CONFIDENCE_CALIBRATION = "confidence_calibration"

class LearningPriority(Enum):
    """Priority levels for cross-brain learning."""
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"

@dataclass
class KnowledgeItem:
    """A piece of knowledge that can be shared between brains."""
    knowledge_id: str
    source_brain_id: str
    knowledge_type: KnowledgeType
    title: str
    description: str
    applicable_contexts: List[str]
    confidence_impact: float  # Expected impact on confidence
    success_rate: float  # Success rate when this knowledge is applied
    usage_count: int = 0
    created_at: datetime = field(default_factory=datetime.now)
    last_used: Optional[datetime] = None
    metadata: Optional[Dict[str, Any]] = None

@dataclass
class LearningRequest:
    """Request for cross-brain learning."""
    request_id: str
    requesting_brain_id: str
    knowledge_type: KnowledgeType
    context: str
    priority: LearningPriority
    specific_needs: Optional[List[str]] = None
    created_at: datetime = field(default_factory=datetime.now)

@dataclass
class LearningTransfer:
    """Record of knowledge transfer between brains."""
    transfer_id: str
    source_brain_id: str
    target_brain_id: str
    knowledge_item: KnowledgeItem
    transfer_success: bool
    effectiveness_score: Optional[float] = None
    feedback: Optional[str] = None
    transferred_at: datetime = field(default_factory=datetime.now)

class CrossBrainLearner:
    """
    Facilitates knowledge sharing and collaborative learning
    between different AI brains in the multi-brain system.
    """
    
    def __init__(self):
        """Initialize the cross-brain learner."""
        self.logger = logging.getLogger(__name__)
        self.knowledge_base: Dict[str, KnowledgeItem] = {}
        self.learning_requests: List[LearningRequest] = []
        self.transfer_history: List[LearningTransfer] = []
        self.brain_specializations: Dict[str, Set[KnowledgeType]] = {}
        self.logger.info("Cross-Brain Learner initialized")
    
    async def register_brain_specialization(
        self,
        brain_id: str,
        specializations: List[KnowledgeType]
    ):
        """
        Register a brain's specializations for targeted learning.
        
        Args:
            brain_id: ID of the brain
            specializations: List of knowledge types the brain specializes in
        """
        self.brain_specializations[brain_id] = set(specializations)
        self.logger.info(f"Registered specializations for {brain_id}: {[s.value for s in specializations]}")
    
    async def share_knowledge(
        self,
        source_brain_id: str,
        knowledge_item: KnowledgeItem
    ) -> bool:
        """
        Share knowledge from one brain to the knowledge base.
        
        Args:
            source_brain_id: ID of the brain sharing knowledge
            knowledge_item: Knowledge item to share
            
        Returns:
            True if knowledge was successfully shared
        """
        try:
            # Validate knowledge item
            if not knowledge_item.knowledge_id:
                knowledge_item.knowledge_id = f"{source_brain_id}_{datetime.now().timestamp()}"
            
            knowledge_item.source_brain_id = source_brain_id
            
            # Store in knowledge base
            self.knowledge_base[knowledge_item.knowledge_id] = knowledge_item
            
            self.logger.info(f"Knowledge shared by {source_brain_id}: {knowledge_item.title}")
            
            # Check for pending learning requests that this knowledge might fulfill
            await self._match_knowledge_to_requests(knowledge_item)
            
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to share knowledge from {source_brain_id}: {e}")
            return False
    
    async def request_learning(
        self,
        learning_request: LearningRequest
    ) -> List[KnowledgeItem]:
        """
        Request learning assistance from other brains.
        
        Args:
            learning_request: Learning request details
            
        Returns:
            List of relevant knowledge items
        """
        self.learning_requests.append(learning_request)
        
        # Find relevant knowledge items
        relevant_knowledge = await self._find_relevant_knowledge(learning_request)
        
        self.logger.info(f"Learning request from {learning_request.requesting_brain_id}: "
                        f"found {len(relevant_knowledge)} relevant items")
        
        return relevant_knowledge
    
    async def transfer_knowledge(
        self,
        source_brain_id: str,
        target_brain_id: str,
        knowledge_id: str
    ) -> LearningTransfer:
        """
        Transfer specific knowledge from one brain to another.
        
        Args:
            source_brain_id: ID of the source brain
            target_brain_id: ID of the target brain
            knowledge_id: ID of the knowledge to transfer
            
        Returns:
            LearningTransfer record
        """
        if knowledge_id not in self.knowledge_base:
            raise ValueError(f"Knowledge item {knowledge_id} not found")
        
        knowledge_item = self.knowledge_base[knowledge_id]
        
        # Create transfer record
        transfer = LearningTransfer(
            transfer_id=f"transfer_{datetime.now().timestamp()}",
            source_brain_id=source_brain_id,
            target_brain_id=target_brain_id,
            knowledge_item=knowledge_item,
            transfer_success=True  # Assume success for now
        )
        
        # Update knowledge usage
        knowledge_item.usage_count += 1
        knowledge_item.last_used = datetime.now()
        
        # Store transfer record
        self.transfer_history.append(transfer)
        
        self.logger.info(f"Knowledge transferred from {source_brain_id} to {target_brain_id}: {knowledge_item.title}")
        
        return transfer
    
    async def get_brain_learning_summary(
        self,
        brain_id: str,
        time_window: Optional[timedelta] = None
    ) -> Dict[str, Any]:
        """
        Get learning summary for a specific brain.
        
        Args:
            brain_id: ID of the brain
            time_window: Time window for analysis (default: last 30 days)
            
        Returns:
            Learning summary dictionary
        """
        if time_window is None:
            time_window = timedelta(days=30)
        
        cutoff_time = datetime.now() - time_window
        
        # Knowledge shared by this brain
        shared_knowledge = [
            item for item in self.knowledge_base.values()
            if item.source_brain_id == brain_id and item.created_at >= cutoff_time
        ]
        
        # Knowledge received by this brain
        received_transfers = [
            transfer for transfer in self.transfer_history
            if transfer.target_brain_id == brain_id and transfer.transferred_at >= cutoff_time
        ]
        
        # Learning requests made by this brain
        learning_requests = [
            req for req in self.learning_requests
            if req.requesting_brain_id == brain_id and req.created_at >= cutoff_time
        ]
        
        # Calculate learning metrics
        knowledge_shared_count = len(shared_knowledge)
        knowledge_received_count = len(received_transfers)
        learning_requests_count = len(learning_requests)
        
        # Average success rate of shared knowledge
        avg_success_rate = 0.0
        if shared_knowledge:
            avg_success_rate = sum(item.success_rate for item in shared_knowledge) / len(shared_knowledge)
        
        # Most common knowledge types
        knowledge_types = {}
        for item in shared_knowledge:
            knowledge_types[item.knowledge_type.value] = knowledge_types.get(item.knowledge_type.value, 0) + 1
        
        return {
            "brain_id": brain_id,
            "time_window_days": time_window.days,
            "knowledge_shared": knowledge_shared_count,
            "knowledge_received": knowledge_received_count,
            "learning_requests": learning_requests_count,
            "average_success_rate": avg_success_rate,
            "specializations": [s.value for s in self.brain_specializations.get(brain_id, set())],
            "top_knowledge_types": sorted(knowledge_types.items(), key=lambda x: x[1], reverse=True)[:3],
            "learning_activity_score": self._calculate_learning_activity_score(
                knowledge_shared_count, knowledge_received_count, learning_requests_count
            )
        }
    
    async def get_system_learning_insights(self) -> Dict[str, Any]:
        """
        Get system-wide learning insights.
        
        Returns:
            System learning insights dictionary
        """
        total_knowledge_items = len(self.knowledge_base)
        total_transfers = len(self.transfer_history)
        total_requests = len(self.learning_requests)
        
        # Most active brains
        brain_activity = {}
        for item in self.knowledge_base.values():
            brain_activity[item.source_brain_id] = brain_activity.get(item.source_brain_id, 0) + 1
        
        # Most valuable knowledge types
        knowledge_type_usage = {}
        for item in self.knowledge_base.values():
            knowledge_type_usage[item.knowledge_type.value] = knowledge_type_usage.get(item.knowledge_type.value, 0) + item.usage_count
        
        # Transfer success rate
        successful_transfers = len([t for t in self.transfer_history if t.transfer_success])
        transfer_success_rate = successful_transfers / max(total_transfers, 1)
        
        return {
            "total_knowledge_items": total_knowledge_items,
            "total_transfers": total_transfers,
            "total_requests": total_requests,
            "transfer_success_rate": transfer_success_rate,
            "most_active_brains": sorted(brain_activity.items(), key=lambda x: x[1], reverse=True)[:5],
            "most_valuable_knowledge_types": sorted(knowledge_type_usage.items(), key=lambda x: x[1], reverse=True)[:5],
            "registered_brain_count": len(self.brain_specializations),
            "average_knowledge_usage": sum(item.usage_count for item in self.knowledge_base.values()) / max(total_knowledge_items, 1)
        }
    
    async def _match_knowledge_to_requests(self, knowledge_item: KnowledgeItem):
        """Match new knowledge to pending learning requests."""
        matching_requests = [
            req for req in self.learning_requests
            if req.knowledge_type == knowledge_item.knowledge_type
            and any(context in knowledge_item.applicable_contexts for context in [req.context])
        ]
        
        for request in matching_requests:
            self.logger.info(f"Knowledge {knowledge_item.knowledge_id} matches request {request.request_id}")
            # In a real implementation, we would notify the requesting brain
    
    async def _find_relevant_knowledge(
        self,
        learning_request: LearningRequest
    ) -> List[KnowledgeItem]:
        """Find knowledge items relevant to a learning request."""
        relevant_items = []
        
        for item in self.knowledge_base.values():
            # Match knowledge type
            if item.knowledge_type != learning_request.knowledge_type:
                continue
            
            # Match context
            context_match = any(
                context.lower() in learning_request.context.lower()
                for context in item.applicable_contexts
            )
            
            if context_match:
                relevant_items.append(item)
        
        # Sort by success rate and usage count
        relevant_items.sort(key=lambda x: (x.success_rate, x.usage_count), reverse=True)
        
        return relevant_items[:10]  # Return top 10 most relevant items
    
    def _calculate_learning_activity_score(
        self,
        shared_count: int,
        received_count: int,
        request_count: int
    ) -> float:
        """Calculate a learning activity score for a brain."""
        # Weighted score: sharing knowledge is most valuable, receiving is good, requesting shows engagement
        score = (shared_count * 3) + (received_count * 2) + (request_count * 1)
        
        # Normalize to 0-100 scale (arbitrary scaling)
        normalized_score = min(score * 2, 100)
        
        return normalized_score
    
    async def cleanup_old_data(self):
        """Clean up old learning data to prevent memory bloat."""
        cutoff_time = datetime.now() - timedelta(days=180)  # Keep 6 months of data
        
        # Clean up old requests
        self.learning_requests = [
            req for req in self.learning_requests
            if req.created_at >= cutoff_time
        ]
        
        # Clean up old transfers
        self.transfer_history = [
            transfer for transfer in self.transfer_history
            if transfer.transferred_at >= cutoff_time
        ]
        
        # Clean up unused knowledge items
        active_knowledge = {}
        for item_id, item in self.knowledge_base.items():
            if item.created_at >= cutoff_time or item.usage_count > 0:
                active_knowledge[item_id] = item
        
        removed_count = len(self.knowledge_base) - len(active_knowledge)
        self.knowledge_base = active_knowledge
        
        self.logger.debug(f"Cleaned up old learning data, removed {removed_count} unused knowledge items")

# Global instance for easy access
cross_brain_learner = CrossBrainLearner()