"""
OpsConductor Learning Engine
Implements feedback loops and continuous improvement
"""
import asyncio
import json
import time
import structlog
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime, timedelta
from collections import defaultdict
import redis.asyncio as redis

from vector_client import VectorStoreClient, VectorCollection, KnowledgeManager

logger = structlog.get_logger()

class LearningMetrics:
    """Track learning metrics and performance"""
    
    def __init__(self, redis_client: Optional[redis.Redis] = None):
        self.redis_client = redis_client
        self.metrics = defaultdict(lambda: {
            "success_count": 0,
            "failure_count": 0,
            "total_count": 0,
            "feedback_positive": 0,
            "feedback_negative": 0,
            "avg_confidence": 0.0,
            "avg_response_time": 0.0
        })
    
    async def record_interaction(
        self,
        intent: str,
        success: bool,
        confidence: float,
        response_time: float,
        feedback: Optional[str] = None
    ):
        """Record interaction metrics"""
        metric = self.metrics[intent]
        metric["total_count"] += 1
        
        if success:
            metric["success_count"] += 1
        else:
            metric["failure_count"] += 1
        
        # Update rolling averages
        metric["avg_confidence"] = (
            (metric["avg_confidence"] * (metric["total_count"] - 1) + confidence) 
            / metric["total_count"]
        )
        metric["avg_response_time"] = (
            (metric["avg_response_time"] * (metric["total_count"] - 1) + response_time)
            / metric["total_count"]
        )
        
        # Process feedback
        if feedback:
            if feedback in ["positive", "good", "helpful", "correct"]:
                metric["feedback_positive"] += 1
            elif feedback in ["negative", "bad", "unhelpful", "incorrect"]:
                metric["feedback_negative"] += 1
        
        # Store in Redis for persistence
        if self.redis_client:
            await self._persist_metric(intent, metric)
    
    async def _persist_metric(self, intent: str, metric: Dict[str, Any]):
        """Persist metric to Redis"""
        try:
            key = f"learning:metrics:{intent}"
            await self.redis_client.setex(
                key,
                86400,  # 24 hours TTL
                json.dumps(metric)
            )
        except Exception as e:
            logger.error(f"Failed to persist metric: {e}")
    
    async def get_performance_report(self) -> Dict[str, Any]:
        """Generate performance report"""
        report = {
            "overall": {
                "total_interactions": 0,
                "success_rate": 0.0,
                "avg_confidence": 0.0,
                "avg_response_time": 0.0
            },
            "by_intent": {}
        }
        
        total_success = 0
        total_count = 0
        total_confidence = 0.0
        total_response_time = 0.0
        
        for intent, metric in self.metrics.items():
            if metric["total_count"] > 0:
                success_rate = metric["success_count"] / metric["total_count"]
                
                report["by_intent"][intent] = {
                    "success_rate": success_rate,
                    "total_count": metric["total_count"],
                    "avg_confidence": metric["avg_confidence"],
                    "avg_response_time": metric["avg_response_time"],
                    "feedback_score": self._calculate_feedback_score(metric)
                }
                
                total_success += metric["success_count"]
                total_count += metric["total_count"]
                total_confidence += metric["avg_confidence"] * metric["total_count"]
                total_response_time += metric["avg_response_time"] * metric["total_count"]
        
        if total_count > 0:
            report["overall"]["total_interactions"] = total_count
            report["overall"]["success_rate"] = total_success / total_count
            report["overall"]["avg_confidence"] = total_confidence / total_count
            report["overall"]["avg_response_time"] = total_response_time / total_count
        
        return report
    
    def _calculate_feedback_score(self, metric: Dict[str, Any]) -> float:
        """Calculate feedback score from positive/negative feedback"""
        total_feedback = metric["feedback_positive"] + metric["feedback_negative"]
        if total_feedback == 0:
            return 0.5  # Neutral
        return metric["feedback_positive"] / total_feedback

class PatternLearner:
    """Learn patterns from successful interactions"""
    
    def __init__(self, vector_client: VectorStoreClient):
        self.vector_client = vector_client
        self.patterns = defaultdict(list)
    
    async def learn_pattern(
        self,
        query: str,
        response: str,
        intent: str,
        success: bool,
        metadata: Optional[Dict[str, Any]] = None
    ):
        """Learn from a query-response pattern"""
        if success:
            pattern = {
                "query": query,
                "response": response,
                "intent": intent,
                "timestamp": time.time(),
                "metadata": metadata or {}
            }
            
            self.patterns[intent].append(pattern)
            
            # Store successful pattern in vector database
            content = f"Intent: {intent}\nQuery: {query}\nSuccessful Response: {response}"
            await self.vector_client.store(
                content=content,
                collection=VectorCollection.AUTOMATION_PATTERNS,
                metadata={
                    "intent": intent,
                    "success": True,
                    "timestamp": pattern["timestamp"],
                    **(metadata or {})
                }
            )
    
    async def find_similar_patterns(
        self,
        query: str,
        intent: str,
        limit: int = 3
    ) -> List[Dict[str, Any]]:
        """Find similar successful patterns"""
        # Search in vector database
        results = await self.vector_client.search(
            query=f"Intent: {intent}\nQuery: {query}",
            collection=VectorCollection.AUTOMATION_PATTERNS,
            limit=limit
        )
        
        # Also check recent patterns in memory
        recent_patterns = self.patterns.get(intent, [])[-10:]  # Last 10 patterns
        
        return {
            "vector_results": results,
            "recent_patterns": recent_patterns
        }
    
    async def consolidate_patterns(self):
        """Consolidate and optimize learned patterns"""
        for intent, patterns in self.patterns.items():
            if len(patterns) >= 10:  # Enough patterns to analyze
                # Group similar queries
                similar_groups = self._group_similar_queries(patterns)
                
                # Create optimized patterns
                for group in similar_groups:
                    if len(group) >= 3:  # At least 3 similar patterns
                        optimized = self._create_optimized_pattern(group)
                        
                        # Store optimized pattern
                        await self.vector_client.store(
                            content=json.dumps(optimized),
                            collection=VectorCollection.AUTOMATION_PATTERNS,
                            metadata={
                                "type": "optimized",
                                "intent": intent,
                                "pattern_count": len(group),
                                "created": time.time()
                            }
                        )
    
    def _group_similar_queries(self, patterns: List[Dict[str, Any]]) -> List[List[Dict[str, Any]]]:
        """Group patterns with similar queries"""
        # Simple grouping based on query length and common words
        # In production, use more sophisticated clustering
        groups = []
        used = set()
        
        for i, pattern in enumerate(patterns):
            if i in used:
                continue
            
            group = [pattern]
            used.add(i)
            
            for j, other in enumerate(patterns[i+1:], i+1):
                if j not in used:
                    similarity = self._calculate_similarity(
                        pattern["query"],
                        other["query"]
                    )
                    if similarity > 0.7:
                        group.append(other)
                        used.add(j)
            
            groups.append(group)
        
        return groups
    
    def _calculate_similarity(self, query1: str, query2: str) -> float:
        """Calculate similarity between two queries"""
        # Simple word overlap similarity
        words1 = set(query1.lower().split())
        words2 = set(query2.lower().split())
        
        if not words1 or not words2:
            return 0.0
        
        intersection = len(words1 & words2)
        union = len(words1 | words2)
        
        return intersection / union if union > 0 else 0.0
    
    def _create_optimized_pattern(self, group: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Create an optimized pattern from a group of similar patterns"""
        # Find common elements
        common_words = None
        for pattern in group:
            words = set(pattern["query"].lower().split())
            if common_words is None:
                common_words = words
            else:
                common_words &= words
        
        # Create template
        template = {
            "query_template": " ".join(common_words) if common_words else "",
            "response_template": group[0]["response"],  # Use most common response
            "intent": group[0]["intent"],
            "variations": [p["query"] for p in group],
            "success_count": len(group)
        }
        
        return template

class FeedbackProcessor:
    """Process user feedback and corrections"""
    
    def __init__(
        self,
        vector_client: VectorStoreClient,
        redis_client: Optional[redis.Redis] = None
    ):
        self.vector_client = vector_client
        self.redis_client = redis_client
        self.feedback_queue = asyncio.Queue()
    
    async def submit_feedback(
        self,
        interaction_id: str,
        user_id: str,
        rating: int,  # 1-5 scale
        comment: Optional[str] = None,
        correction: Optional[str] = None
    ):
        """Submit user feedback for an interaction"""
        feedback = {
            "interaction_id": interaction_id,
            "user_id": user_id,
            "rating": rating,
            "comment": comment,
            "correction": correction,
            "timestamp": time.time()
        }
        
        # Queue for processing
        await self.feedback_queue.put(feedback)
        
        # Store immediately in Redis for persistence
        if self.redis_client:
            key = f"feedback:{interaction_id}"
            await self.redis_client.setex(
                key,
                86400 * 7,  # 7 days TTL
                json.dumps(feedback)
            )
        
        return feedback
    
    async def process_feedback_queue(self):
        """Process feedback queue continuously"""
        while True:
            try:
                feedback = await asyncio.wait_for(
                    self.feedback_queue.get(),
                    timeout=1.0
                )
                
                await self._process_single_feedback(feedback)
                
            except asyncio.TimeoutError:
                continue
            except Exception as e:
                logger.error(f"Error processing feedback: {e}")
    
    async def _process_single_feedback(self, feedback: Dict[str, Any]):
        """Process a single feedback item"""
        # Store in vector database for learning
        content = f"Feedback for interaction {feedback['interaction_id']}:\n"
        content += f"Rating: {feedback['rating']}/5\n"
        
        if feedback.get("comment"):
            content += f"Comment: {feedback['comment']}\n"
        
        if feedback.get("correction"):
            content += f"Correction: {feedback['correction']}\n"
        
        # Determine if this is positive or negative feedback
        is_positive = feedback["rating"] >= 4
        
        await self.vector_client.store(
            content=content,
            collection=VectorCollection.USER_INTERACTIONS,
            metadata={
                "type": "feedback",
                "interaction_id": feedback["interaction_id"],
                "user_id": feedback["user_id"],
                "rating": feedback["rating"],
                "is_positive": is_positive,
                "has_correction": feedback.get("correction") is not None,
                "timestamp": feedback["timestamp"]
            }
        )
        
        # If there's a correction, learn from it
        if feedback.get("correction"):
            await self._learn_from_correction(
                feedback["interaction_id"],
                feedback["correction"]
            )
    
    async def _learn_from_correction(self, interaction_id: str, correction: str):
        """Learn from user corrections"""
        # Retrieve original interaction if available
        if self.redis_client:
            original_key = f"interaction:{interaction_id}"
            original_data = await self.redis_client.get(original_key)
            
            if original_data:
                original = json.loads(original_data)
                
                # Store the correction as a learning point
                learning_content = f"Original Query: {original.get('query', 'N/A')}\n"
                learning_content += f"Original Response: {original.get('response', 'N/A')}\n"
                learning_content += f"Correction: {correction}"
                
                await self.vector_client.store(
                    content=learning_content,
                    collection=VectorCollection.TROUBLESHOOTING,
                    metadata={
                        "type": "correction",
                        "interaction_id": interaction_id,
                        "learned_at": time.time()
                    }
                )

class LearningOrchestrator:
    """Orchestrate all learning components"""
    
    def __init__(
        self,
        vector_service_url: str = "http://vector-service:3000",
        redis_client: Optional[redis.Redis] = None
    ):
        self.vector_client = VectorStoreClient(vector_service_url)
        self.knowledge_manager = KnowledgeManager(self.vector_client)
        self.metrics = LearningMetrics(redis_client)
        self.pattern_learner = PatternLearner(self.vector_client)
        self.feedback_processor = FeedbackProcessor(self.vector_client, redis_client)
        self.redis_client = redis_client
    
    async def record_interaction(
        self,
        query: str,
        response: str,
        intent: str,
        success: bool,
        confidence: float,
        response_time: float,
        user_id: str = "anonymous",
        metadata: Optional[Dict[str, Any]] = None
    ) -> str:
        """Record and learn from an interaction"""
        # Generate interaction ID
        interaction_id = f"int_{int(time.time() * 1000)}_{user_id[:8]}"
        
        # Store interaction for future reference
        if self.redis_client:
            interaction_data = {
                "id": interaction_id,
                "query": query,
                "response": response,
                "intent": intent,
                "success": success,
                "confidence": confidence,
                "response_time": response_time,
                "user_id": user_id,
                "timestamp": time.time(),
                "metadata": metadata or {}
            }
            
            await self.redis_client.setex(
                f"interaction:{interaction_id}",
                86400 * 7,  # 7 days TTL
                json.dumps(interaction_data)
            )
        
        # Record metrics
        await self.metrics.record_interaction(
            intent=intent,
            success=success,
            confidence=confidence,
            response_time=response_time
        )
        
        # Learn from interaction
        await self.knowledge_manager.learn_from_interaction(
            user_query=query,
            ai_response=response,
            success=success,
            user_id=user_id
        )
        
        # Learn pattern if successful
        if success:
            await self.pattern_learner.learn_pattern(
                query=query,
                response=response,
                intent=intent,
                success=success,
                metadata=metadata
            )
        
        return interaction_id
    
    async def get_learning_insights(self) -> Dict[str, Any]:
        """Get insights from learning system"""
        performance_report = await self.metrics.get_performance_report()
        
        insights = {
            "performance": performance_report,
            "patterns": {
                intent: len(patterns)
                for intent, patterns in self.pattern_learner.patterns.items()
            },
            "recommendations": []
        }
        
        # Generate recommendations based on performance
        for intent, metrics in performance_report["by_intent"].items():
            if metrics["success_rate"] < 0.7:
                insights["recommendations"].append({
                    "type": "improvement_needed",
                    "intent": intent,
                    "current_success_rate": metrics["success_rate"],
                    "suggestion": f"Intent '{intent}' has low success rate. Consider reviewing patterns and responses."
                })
            
            if metrics["avg_confidence"] < 0.5:
                insights["recommendations"].append({
                    "type": "low_confidence",
                    "intent": intent,
                    "current_confidence": metrics["avg_confidence"],
                    "suggestion": f"Intent '{intent}' has low confidence. More training data may be needed."
                })
        
        return insights
    
    async def trigger_pattern_consolidation(self):
        """Manually trigger pattern consolidation"""
        await self.pattern_learner.consolidate_patterns()
        logger.info("Pattern consolidation completed")
    
    async def start_background_tasks(self):
        """Start background learning tasks"""
        # Start feedback processor
        asyncio.create_task(self.feedback_processor.process_feedback_queue())
        
        # Schedule periodic pattern consolidation
        asyncio.create_task(self._periodic_consolidation())
        
        logger.info("Learning background tasks started")
    
    async def _periodic_consolidation(self):
        """Periodically consolidate patterns"""
        while True:
            await asyncio.sleep(3600)  # Every hour
            try:
                await self.trigger_pattern_consolidation()
            except Exception as e:
                logger.error(f"Pattern consolidation failed: {e}")
    
    async def cleanup(self):
        """Cleanup resources"""
        await self.vector_client.cleanup()