"""
OUIOE Phase 7: Conversation Memory Engine

Advanced conversation memory system with semantic search, intelligent retrieval,
and context-aware conversation history management.
"""

import asyncio
import logging
import json
import numpy as np
from typing import List, Dict, Any, Optional, Tuple, Set
from datetime import datetime, timedelta
from collections import defaultdict, deque
import hashlib

from conversation.conversation_models import (
    ConversationMessage, ConversationContext, ConversationSummary,
    ConversationMetrics, MessageRole, ContextDimension
)

# Import existing OUIOE components
from integrations.llm_client import LLMEngine
from integrations.vector_client import OpsConductorVectorStore
from streaming.redis_thinking_stream import RedisThinkingStreamManager


class ConversationMemoryEngine:
    """
    Advanced conversation memory engine with semantic search and intelligent retrieval.
    
    Capabilities:
    - Semantic conversation search and retrieval
    - Context-aware memory consolidation
    - Intelligent conversation summarization
    - Memory optimization and archival
    - Cross-conversation pattern recognition
    """
    
    def __init__(self, 
                 llm_client: LLMEngine,
                 vector_client: OpsConductorVectorStore,
                 redis_stream: RedisThinkingStreamManager,
                 max_active_conversations: int = 100,
                 memory_retention_days: int = 90):
        self.llm_client = llm_client
        self.vector_client = vector_client
        self.redis_stream = redis_stream
        self.max_active_conversations = max_active_conversations
        self.memory_retention_days = memory_retention_days
        
        # Memory storage
        self.active_conversations: Dict[str, List[ConversationMessage]] = {}
        self.conversation_contexts: Dict[str, ConversationContext] = {}
        self.conversation_summaries: Dict[str, ConversationSummary] = {}
        self.conversation_metrics: Dict[str, ConversationMetrics] = {}
        
        # Memory optimization
        self.memory_access_frequency: Dict[str, int] = defaultdict(int)
        self.last_access_time: Dict[str, datetime] = {}
        self.memory_importance_scores: Dict[str, float] = {}
        
        # Semantic search indices
        self.message_embeddings: Dict[str, List[float]] = {}
        self.conversation_embeddings: Dict[str, List[float]] = {}
        
        # Performance tracking
        self.search_performance_history: deque = deque(maxlen=1000)
        self.memory_usage_stats: Dict[str, Any] = {}
        
        self.logger = logging.getLogger(__name__)
    
    async def store_message(self, message: ConversationMessage) -> bool:
        """
        Store a conversation message with semantic indexing.
        
        Args:
            message: The conversation message to store
            
        Returns:
            bool: Success status
        """
        try:
            # Store message in active conversation
            if message.conversation_id not in self.active_conversations:
                self.active_conversations[message.conversation_id] = []
            
            self.active_conversations[message.conversation_id].append(message)
            
            # Generate semantic embedding
            if message.content and message.role != MessageRole.SYSTEM:
                embedding = await self._generate_message_embedding(message)
                self.message_embeddings[message.message_id] = embedding
                
                # Store in vector database
                await self.vector_client.store_embedding(
                    id=message.message_id,
                    embedding=embedding,
                    metadata={
                        "conversation_id": message.conversation_id,
                        "role": message.role.value,
                        "timestamp": message.timestamp.isoformat(),
                        "topics": message.topics,
                        "entities": message.entities
                    }
                )
            
            # Update conversation metrics
            await self._update_conversation_metrics(message.conversation_id)
            
            # Check if memory optimization is needed
            if len(self.active_conversations) > self.max_active_conversations:
                await self._optimize_memory()
            
            # Stream memory update
            await self.redis_stream.stream_thinking_step(
                session_id=message.conversation_id,
                step_type="memory_storage",
                content=f"Stored message in conversation memory",
                confidence=0.95
            )
            
            return True
            
        except Exception as e:
            self.logger.error(f"Error storing message: {str(e)}")
            return False
    
    async def retrieve_conversation_history(self, 
                                          conversation_id: str,
                                          limit: Optional[int] = None,
                                          include_context: bool = True) -> List[ConversationMessage]:
        """
        Retrieve conversation history with optional context.
        
        Args:
            conversation_id: Conversation identifier
            limit: Maximum number of messages to retrieve
            include_context: Whether to include context information
            
        Returns:
            List of conversation messages
        """
        try:
            # Update access tracking
            self.memory_access_frequency[conversation_id] += 1
            self.last_access_time[conversation_id] = datetime.now()
            
            # Get messages from active memory
            messages = self.active_conversations.get(conversation_id, [])
            
            # If not in active memory, try to load from archive
            if not messages:
                messages = await self._load_archived_conversation(conversation_id)
            
            # Apply limit if specified
            if limit and len(messages) > limit:
                messages = messages[-limit:]
            
            # Include context if requested
            if include_context and conversation_id in self.conversation_contexts:
                context = self.conversation_contexts[conversation_id]
                for message in messages:
                    message.context_snapshot = self._extract_relevant_context(
                        context, message.timestamp
                    )
            
            return messages
            
        except Exception as e:
            self.logger.error(f"Error retrieving conversation history: {str(e)}")
            return []
    
    async def semantic_search(self, 
                            query: str,
                            conversation_ids: Optional[List[str]] = None,
                            limit: int = 10,
                            similarity_threshold: float = 0.7) -> List[Tuple[ConversationMessage, float]]:
        """
        Perform semantic search across conversation history.
        
        Args:
            query: Search query
            conversation_ids: Optional list of conversation IDs to search within
            limit: Maximum number of results
            similarity_threshold: Minimum similarity score
            
        Returns:
            List of (message, similarity_score) tuples
        """
        start_time = datetime.now()
        
        try:
            # Generate query embedding
            query_embedding = await self._generate_text_embedding(query)
            
            # Search in vector database
            search_results = await self.vector_client.similarity_search(
                query_embedding=query_embedding,
                limit=limit * 2,  # Get more results for filtering
                threshold=similarity_threshold
            )
            
            # Filter by conversation IDs if specified
            if conversation_ids:
                search_results = [
                    result for result in search_results
                    if result.get('metadata', {}).get('conversation_id') in conversation_ids
                ]
            
            # Retrieve full messages and calculate final scores
            results = []
            for result in search_results[:limit]:
                message_id = result['id']
                similarity_score = result['score']
                
                # Find the message in active conversations
                message = await self._find_message_by_id(message_id)
                if message:
                    results.append((message, similarity_score))
            
            # Track search performance
            search_time = (datetime.now() - start_time).total_seconds()
            self.search_performance_history.append({
                'query': query,
                'results_count': len(results),
                'search_time': search_time,
                'timestamp': datetime.now()
            })
            
            return results
            
        except Exception as e:
            self.logger.error(f"Error in semantic search: {str(e)}")
            return []
    
    async def find_related_conversations(self, 
                                       conversation_id: str,
                                       similarity_threshold: float = 0.6,
                                       limit: int = 5) -> List[Tuple[str, float]]:
        """
        Find conversations related to the given conversation.
        
        Args:
            conversation_id: Source conversation ID
            similarity_threshold: Minimum similarity threshold
            limit: Maximum number of related conversations
            
        Returns:
            List of (conversation_id, similarity_score) tuples
        """
        try:
            # Get conversation embedding
            if conversation_id not in self.conversation_embeddings:
                await self._generate_conversation_embedding(conversation_id)
            
            source_embedding = self.conversation_embeddings.get(conversation_id)
            if not source_embedding:
                return []
            
            # Compare with other conversation embeddings
            similarities = []
            for other_id, other_embedding in self.conversation_embeddings.items():
                if other_id != conversation_id:
                    similarity = self._calculate_cosine_similarity(
                        source_embedding, other_embedding
                    )
                    if similarity >= similarity_threshold:
                        similarities.append((other_id, similarity))
            
            # Sort by similarity and return top results
            similarities.sort(key=lambda x: x[1], reverse=True)
            return similarities[:limit]
            
        except Exception as e:
            self.logger.error(f"Error finding related conversations: {str(e)}")
            return []
    
    async def generate_conversation_summary(self, 
                                          conversation_id: str,
                                          summary_type: str = "comprehensive") -> Optional[ConversationSummary]:
        """
        Generate an intelligent summary of a conversation.
        
        Args:
            conversation_id: Conversation to summarize
            summary_type: Type of summary ("brief", "comprehensive", "technical")
            
        Returns:
            ConversationSummary or None if failed
        """
        try:
            # Get conversation messages
            messages = await self.retrieve_conversation_history(conversation_id)
            if not messages:
                return None
            
            # Prepare conversation text
            conversation_text = self._format_conversation_for_summary(messages)
            
            # Generate summary using LLM
            summary_prompt = self._build_summary_prompt(conversation_text, summary_type)
            
            summary_response = await self.llm_client.generate_response(
                prompt=summary_prompt,
                max_tokens=1000,
                temperature=0.3
            )
            
            # Parse summary response
            summary_data = self._parse_summary_response(summary_response)
            
            # Create summary object
            summary = ConversationSummary(
                conversation_id=conversation_id,
                title=summary_data.get('title', 'Conversation Summary'),
                abstract=summary_data.get('abstract', ''),
                key_points=summary_data.get('key_points', []),
                decisions_made=summary_data.get('decisions_made', []),
                action_items=summary_data.get('action_items', []),
                message_range={
                    'first': messages[0].message_id,
                    'last': messages[-1].message_id
                },
                time_range={
                    'start': messages[0].timestamp,
                    'end': messages[-1].timestamp
                },
                participant_count=len(set(msg.role for msg in messages)),
                completeness_score=summary_data.get('completeness_score', 0.8),
                coherence_score=summary_data.get('coherence_score', 0.8),
                relevance_score=summary_data.get('relevance_score', 0.8)
            )
            
            # Store summary
            self.conversation_summaries[conversation_id] = summary
            
            return summary
            
        except Exception as e:
            self.logger.error(f"Error generating conversation summary: {str(e)}")
            return None
    
    async def update_conversation_context(self, 
                                        conversation_id: str,
                                        context_updates: Dict[ContextDimension, Dict[str, Any]]) -> bool:
        """
        Update conversation context with new information.
        
        Args:
            conversation_id: Conversation identifier
            context_updates: Updates for different context dimensions
            
        Returns:
            bool: Success status
        """
        try:
            # Get or create context
            if conversation_id not in self.conversation_contexts:
                self.conversation_contexts[conversation_id] = ConversationContext(
                    conversation_id=conversation_id,
                    user_id="unknown",  # Will be updated when available
                    session_id=conversation_id
                )
            
            context = self.conversation_contexts[conversation_id]
            
            # Update context dimensions
            for dimension, updates in context_updates.items():
                if dimension == ContextDimension.TEMPORAL:
                    context.temporal_context.update(updates)
                elif dimension == ContextDimension.TOPICAL:
                    context.topical_context.update(updates)
                elif dimension == ContextDimension.EMOTIONAL:
                    context.emotional_context.update(updates)
                elif dimension == ContextDimension.TECHNICAL:
                    context.technical_context.update(updates)
                elif dimension == ContextDimension.OPERATIONAL:
                    context.operational_context.update(updates)
                elif dimension == ContextDimension.PREFERENCE:
                    context.preference_context.update(updates)
                elif dimension == ContextDimension.HISTORICAL:
                    context.historical_context.update(updates)
                elif dimension == ContextDimension.ENVIRONMENTAL:
                    context.environmental_context.update(updates)
            
            # Update metadata
            context.last_updated = datetime.now()
            context.context_version += 1
            
            # Update active topics
            if ContextDimension.TOPICAL in context_updates:
                new_topics = context_updates[ContextDimension.TOPICAL].get('topics', [])
                context.active_topics.update(new_topics)
            
            return True
            
        except Exception as e:
            self.logger.error(f"Error updating conversation context: {str(e)}")
            return False
    
    async def get_memory_statistics(self) -> Dict[str, Any]:
        """
        Get comprehensive memory usage and performance statistics.
        
        Returns:
            Dictionary with memory statistics
        """
        try:
            total_messages = sum(len(msgs) for msgs in self.active_conversations.values())
            total_conversations = len(self.active_conversations)
            
            # Calculate average search performance
            recent_searches = list(self.search_performance_history)[-100:]
            avg_search_time = np.mean([s['search_time'] for s in recent_searches]) if recent_searches else 0
            
            # Memory usage by conversation
            conversation_sizes = {
                conv_id: len(messages) 
                for conv_id, messages in self.active_conversations.items()
            }
            
            # Most accessed conversations
            top_accessed = sorted(
                self.memory_access_frequency.items(),
                key=lambda x: x[1],
                reverse=True
            )[:10]
            
            return {
                'total_messages': total_messages,
                'total_conversations': total_conversations,
                'active_conversations': len(self.active_conversations),
                'archived_conversations': 0,  # TODO: Implement archival
                'average_messages_per_conversation': total_messages / max(total_conversations, 1),
                'total_embeddings': len(self.message_embeddings),
                'average_search_time': avg_search_time,
                'search_queries_processed': len(self.search_performance_history),
                'conversation_sizes': conversation_sizes,
                'most_accessed_conversations': top_accessed,
                'memory_retention_days': self.memory_retention_days,
                'last_optimization': getattr(self, 'last_optimization', None),
                'statistics_generated_at': datetime.now()
            }
            
        except Exception as e:
            self.logger.error(f"Error generating memory statistics: {str(e)}")
            return {}
    
    # Private helper methods
    
    async def _generate_message_embedding(self, message: ConversationMessage) -> List[float]:
        """Generate semantic embedding for a message."""
        # Combine content with context for richer embedding
        embedding_text = message.content
        if message.topics:
            embedding_text += f" Topics: {', '.join(message.topics)}"
        if message.entities:
            embedding_text += f" Entities: {', '.join(message.entities)}"
        
        return await self._generate_text_embedding(embedding_text)
    
    async def _generate_text_embedding(self, text: str) -> List[float]:
        """Generate embedding for arbitrary text."""
        try:
            # Use vector client to generate embedding
            embedding = await self.vector_client.generate_embedding(text)
            return embedding
        except Exception as e:
            self.logger.error(f"Error generating text embedding: {str(e)}")
            # Return zero vector as fallback
            return [0.0] * 384  # Assuming 384-dimensional embeddings
    
    async def _generate_conversation_embedding(self, conversation_id: str) -> List[float]:
        """Generate embedding for entire conversation."""
        try:
            messages = self.active_conversations.get(conversation_id, [])
            if not messages:
                return []
            
            # Combine all message content
            conversation_text = " ".join([
                msg.content for msg in messages 
                if msg.role in [MessageRole.USER, MessageRole.ASSISTANT]
            ])
            
            # Generate embedding
            embedding = await self._generate_text_embedding(conversation_text)
            self.conversation_embeddings[conversation_id] = embedding
            
            return embedding
            
        except Exception as e:
            self.logger.error(f"Error generating conversation embedding: {str(e)}")
            return []
    
    def _calculate_cosine_similarity(self, vec1: List[float], vec2: List[float]) -> float:
        """Calculate cosine similarity between two vectors."""
        try:
            vec1_np = np.array(vec1)
            vec2_np = np.array(vec2)
            
            dot_product = np.dot(vec1_np, vec2_np)
            norm1 = np.linalg.norm(vec1_np)
            norm2 = np.linalg.norm(vec2_np)
            
            if norm1 == 0 or norm2 == 0:
                return 0.0
            
            return dot_product / (norm1 * norm2)
            
        except Exception:
            return 0.0
    
    async def _find_message_by_id(self, message_id: str) -> Optional[ConversationMessage]:
        """Find a message by its ID across all conversations."""
        for messages in self.active_conversations.values():
            for message in messages:
                if message.message_id == message_id:
                    return message
        return None
    
    async def _update_conversation_metrics(self, conversation_id: str):
        """Update metrics for a conversation."""
        try:
            messages = self.active_conversations.get(conversation_id, [])
            if not messages:
                return
            
            # Calculate basic metrics
            message_count = len(messages)
            total_duration = 0
            response_times = []
            confidence_scores = []
            
            for i, message in enumerate(messages):
                if message.confidence_score > 0:
                    confidence_scores.append(message.confidence_score)
                
                if message.response_time:
                    response_times.append(message.response_time)
                
                if i > 0:
                    time_diff = (message.timestamp - messages[i-1].timestamp).total_seconds()
                    total_duration += time_diff
            
            # Create or update metrics
            metrics = ConversationMetrics(
                conversation_id=conversation_id,
                message_count=message_count,
                total_duration=total_duration,
                average_response_time=np.mean(response_times) if response_times else 0,
                average_confidence=np.mean(confidence_scores) if confidence_scores else 0,
                conversation_depth=self._calculate_conversation_depth(messages),
                topic_diversity=self._calculate_topic_diversity(messages)
            )
            
            self.conversation_metrics[conversation_id] = metrics
            
        except Exception as e:
            self.logger.error(f"Error updating conversation metrics: {str(e)}")
    
    def _calculate_conversation_depth(self, messages: List[ConversationMessage]) -> int:
        """Calculate the depth of conversation (number of back-and-forth exchanges)."""
        depth = 0
        current_role = None
        
        for message in messages:
            if message.role != current_role and current_role is not None:
                depth += 1
            current_role = message.role
        
        return depth // 2  # Each exchange involves two role changes
    
    def _calculate_topic_diversity(self, messages: List[ConversationMessage]) -> float:
        """Calculate topic diversity in the conversation."""
        all_topics = set()
        for message in messages:
            all_topics.update(message.topics)
        
        # Simple diversity measure: unique topics / total messages
        return len(all_topics) / max(len(messages), 1)
    
    async def _optimize_memory(self):
        """Optimize memory usage by archiving old conversations."""
        try:
            # Sort conversations by access frequency and recency
            conversation_scores = []
            
            for conv_id in self.active_conversations.keys():
                access_freq = self.memory_access_frequency.get(conv_id, 0)
                last_access = self.last_access_time.get(conv_id, datetime.min)
                importance = self.memory_importance_scores.get(conv_id, 0.5)
                
                # Calculate composite score
                recency_score = max(0, 1 - (datetime.now() - last_access).days / 30)
                composite_score = (access_freq * 0.4 + recency_score * 0.4 + importance * 0.2)
                
                conversation_scores.append((conv_id, composite_score))
            
            # Sort by score (lowest first for archival)
            conversation_scores.sort(key=lambda x: x[1])
            
            # Archive lowest-scoring conversations
            conversations_to_archive = conversation_scores[:len(conversation_scores) // 4]
            
            for conv_id, _ in conversations_to_archive:
                await self._archive_conversation(conv_id)
            
            self.last_optimization = datetime.now()
            
        except Exception as e:
            self.logger.error(f"Error optimizing memory: {str(e)}")
    
    async def _archive_conversation(self, conversation_id: str):
        """Archive a conversation to long-term storage."""
        try:
            # TODO: Implement actual archival to persistent storage
            # For now, just remove from active memory
            if conversation_id in self.active_conversations:
                del self.active_conversations[conversation_id]
            
            # Clean up related data
            if conversation_id in self.conversation_contexts:
                del self.conversation_contexts[conversation_id]
            
            # Keep embeddings for search
            # Keep summaries for quick access
            
            self.logger.info(f"Archived conversation {conversation_id}")
            
        except Exception as e:
            self.logger.error(f"Error archiving conversation {conversation_id}: {str(e)}")
    
    async def _load_archived_conversation(self, conversation_id: str) -> List[ConversationMessage]:
        """Load an archived conversation back into memory."""
        # TODO: Implement loading from persistent storage
        return []
    
    def _extract_relevant_context(self, context: ConversationContext, timestamp: datetime) -> Dict[str, Any]:
        """Extract context relevant to a specific timestamp."""
        # For now, return all context
        # TODO: Implement temporal context filtering
        return {
            'temporal': context.temporal_context,
            'topical': context.topical_context,
            'emotional': context.emotional_context,
            'technical': context.technical_context,
            'operational': context.operational_context
        }
    
    def _format_conversation_for_summary(self, messages: List[ConversationMessage]) -> str:
        """Format conversation messages for summary generation."""
        formatted_lines = []
        
        for message in messages:
            if message.role in [MessageRole.USER, MessageRole.ASSISTANT]:
                role_label = "User" if message.role == MessageRole.USER else "Assistant"
                formatted_lines.append(f"{role_label}: {message.content}")
        
        return "\n".join(formatted_lines)
    
    def _build_summary_prompt(self, conversation_text: str, summary_type: str) -> str:
        """Build prompt for conversation summarization."""
        base_prompt = f"""
        Please analyze the following conversation and provide a {summary_type} summary.
        
        Conversation:
        {conversation_text}
        
        Please provide a JSON response with the following structure:
        {{
            "title": "Brief title for the conversation",
            "abstract": "2-3 sentence summary",
            "key_points": ["list", "of", "key", "points"],
            "decisions_made": ["list", "of", "decisions"],
            "action_items": ["list", "of", "action", "items"],
            "completeness_score": 0.8,
            "coherence_score": 0.8,
            "relevance_score": 0.8
        }}
        """
        
        return base_prompt
    
    def _parse_summary_response(self, response: str) -> Dict[str, Any]:
        """Parse LLM response for summary generation."""
        try:
            # Try to extract JSON from response
            start_idx = response.find('{')
            end_idx = response.rfind('}') + 1
            
            if start_idx >= 0 and end_idx > start_idx:
                json_str = response[start_idx:end_idx]
                return json.loads(json_str)
            else:
                # Fallback parsing
                return {
                    'title': 'Conversation Summary',
                    'abstract': response[:200] + '...' if len(response) > 200 else response,
                    'key_points': [],
                    'decisions_made': [],
                    'action_items': [],
                    'completeness_score': 0.7,
                    'coherence_score': 0.7,
                    'relevance_score': 0.7
                }
                
        except Exception as e:
            self.logger.error(f"Error parsing summary response: {str(e)}")
            return {
                'title': 'Conversation Summary',
                'abstract': 'Summary generation failed',
                'key_points': [],
                'decisions_made': [],
                'action_items': [],
                'completeness_score': 0.5,
                'coherence_score': 0.5,
                'relevance_score': 0.5
            }