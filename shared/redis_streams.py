"""
Redis Streams Implementation for OpsConductor
Provides enterprise-grade message streaming with consumer groups, acknowledgments, and dead letter queues.
"""

import asyncio
import json
import time
import uuid
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Callable, Union
from dataclasses import dataclass, asdict
from enum import Enum
import structlog
import redis.asyncio as redis

logger = structlog.get_logger()

class MessagePriority(Enum):
    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"
    CRITICAL = "critical"

class MessageStatus(Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    DEAD_LETTER = "dead_letter"

@dataclass
class StreamMessage:
    """Structured message for Redis Streams"""
    id: str
    stream: str
    event_type: str
    service: str
    data: Dict[str, Any]
    priority: MessagePriority = MessagePriority.NORMAL
    timestamp: float = None
    retry_count: int = 0
    max_retries: int = 3
    correlation_id: Optional[str] = None
    user_id: Optional[str] = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = time.time()
        if self.correlation_id is None:
            self.correlation_id = str(uuid.uuid4())

    def to_dict(self) -> Dict[str, str]:
        """Convert to Redis-compatible string dictionary"""
        return {
            "id": self.id,
            "stream": self.stream,
            "event_type": self.event_type,
            "service": self.service,
            "data": json.dumps(self.data),
            "priority": self.priority.value,
            "timestamp": str(self.timestamp),
            "retry_count": str(self.retry_count),
            "max_retries": str(self.max_retries),
            "correlation_id": self.correlation_id or "",
            "user_id": self.user_id or ""
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, str], stream_id: str = None) -> 'StreamMessage':
        """Create from Redis stream data"""
        return cls(
            id=stream_id or data.get("id", ""),
            stream=data.get("stream", ""),
            event_type=data.get("event_type", ""),
            service=data.get("service", ""),
            data=json.loads(data.get("data", "{}")),
            priority=MessagePriority(data.get("priority", "normal")),
            timestamp=float(data.get("timestamp", time.time())),
            retry_count=int(data.get("retry_count", "0")),
            max_retries=int(data.get("max_retries", "3")),
            correlation_id=data.get("correlation_id") or None,
            user_id=data.get("user_id") or None
        )

class RedisStreamsClient:
    """Enterprise Redis Streams client with consumer groups and dead letter queues"""
    
    def __init__(self, redis_url: str = "redis://redis:6379/0", password: str = None):
        self.redis_url = redis_url
        self.password = password
        self.redis_client: Optional[redis.Redis] = None
        self.consumer_groups: Dict[str, str] = {}
        self.message_handlers: Dict[str, Callable] = {}
        self.running = False
        
        # Stream naming conventions
        self.MAIN_STREAMS = {
            "identity": "opsconductor:identity:events",
            "assets": "opsconductor:assets:events", 
            "automation": "opsconductor:automation:events",
            "communication": "opsconductor:communication:events",
            "ai_brain": "opsconductor:ai:events",
            "network_analyzer": "opsconductor:network:events",
            "system": "opsconductor:system:events"
        }
        
        self.DEAD_LETTER_STREAM = "opsconductor:dead_letter:events"
        self.METRICS_STREAM = "opsconductor:metrics:events"
        
    async def initialize(self):
        """Initialize Redis connection and create streams/consumer groups"""
        try:
            # Create Redis connection
            self.redis_client = redis.from_url(
                self.redis_url,
                password=self.password,
                decode_responses=True,
                retry_on_timeout=True,
                socket_keepalive=True,
                socket_keepalive_options={}
            )
            
            # Test connection
            await self.redis_client.ping()
            logger.info("Redis Streams client connected successfully")
            
            # Initialize streams and consumer groups
            await self._initialize_streams()
            await self._initialize_consumer_groups()
            
            logger.info("Redis Streams initialization completed", 
                       streams=list(self.MAIN_STREAMS.values()),
                       consumer_groups=list(self.consumer_groups.keys()))
            
        except Exception as e:
            logger.error("Failed to initialize Redis Streams client", error=str(e))
            raise
    
    async def _initialize_streams(self):
        """Create streams if they don't exist"""
        for service, stream_name in self.MAIN_STREAMS.items():
            try:
                # Create stream with initial message if it doesn't exist
                await self.redis_client.xadd(
                    stream_name,
                    {"event_type": "stream_initialized", "service": service, "timestamp": str(time.time())},
                    id="0-1"
                )
                logger.debug("Stream initialized", stream=stream_name, service=service)
            except redis.ResponseError as e:
                if "BUSYGROUP" not in str(e):
                    logger.debug("Stream already exists", stream=stream_name)
        
        # Initialize dead letter stream
        try:
            await self.redis_client.xadd(
                self.DEAD_LETTER_STREAM,
                {"event_type": "dead_letter_initialized", "timestamp": str(time.time())},
                id="0-1"
            )
        except redis.ResponseError:
            logger.debug("Dead letter stream already exists")
    
    async def _initialize_consumer_groups(self):
        """Create consumer groups for each stream"""
        for service, stream_name in self.MAIN_STREAMS.items():
            group_name = f"{service}_processors"
            try:
                await self.redis_client.xgroup_create(
                    stream_name, group_name, id="0", mkstream=True
                )
                self.consumer_groups[service] = group_name
                logger.debug("Consumer group created", stream=stream_name, group=group_name)
            except redis.ResponseError as e:
                if "BUSYGROUP" in str(e):
                    self.consumer_groups[service] = group_name
                    logger.debug("Consumer group already exists", group=group_name)
                else:
                    logger.error("Failed to create consumer group", error=str(e))
    
    async def publish_message(self, 
                            stream: str, 
                            event_type: str, 
                            service: str,
                            data: Dict[str, Any],
                            priority: MessagePriority = MessagePriority.NORMAL,
                            user_id: Optional[str] = None,
                            correlation_id: Optional[str] = None) -> str:
        """Publish message to Redis Stream"""
        try:
            message = StreamMessage(
                id="",  # Will be set by Redis
                stream=stream,
                event_type=event_type,
                service=service,
                data=data,
                priority=priority,
                user_id=user_id,
                correlation_id=correlation_id
            )
            
            # Get stream name
            stream_name = self.MAIN_STREAMS.get(stream, f"opsconductor:{stream}:events")
            
            # Publish to Redis Stream
            message_id = await self.redis_client.xadd(
                stream_name,
                message.to_dict(),
                maxlen=10000  # Keep last 10k messages per stream
            )
            
            # Update message ID
            message.id = message_id
            
            # Publish metrics
            await self._publish_metrics("message_published", {
                "stream": stream_name,
                "event_type": event_type,
                "service": service,
                "priority": priority.value,
                "message_id": message_id
            })
            
            logger.info("Message published to stream", 
                       stream=stream_name, 
                       event_type=event_type,
                       message_id=message_id,
                       correlation_id=correlation_id)
            
            return message_id
            
        except Exception as e:
            logger.error("Failed to publish message", 
                        stream=stream, 
                        event_type=event_type, 
                        error=str(e))
            raise
    
    async def consume_messages(self, 
                             streams: List[str], 
                             consumer_name: str,
                             batch_size: int = 10,
                             block_time: int = 1000) -> List[StreamMessage]:
        """Consume messages from multiple streams"""
        try:
            # Build stream mapping for consumer group reading
            stream_mapping = {}
            for stream in streams:
                stream_name = self.MAIN_STREAMS.get(stream, f"opsconductor:{stream}:events")
                stream_mapping[stream_name] = ">"
            
            # Read from streams using consumer groups
            messages = []
            for stream in streams:
                stream_name = self.MAIN_STREAMS.get(stream, f"opsconductor:{stream}:events")
                group_name = self.consumer_groups.get(stream, f"{stream}_processors")
                
                try:
                    result = await self.redis_client.xreadgroup(
                        group_name,
                        consumer_name,
                        {stream_name: ">"},
                        count=batch_size,
                        block=block_time
                    )
                    
                    for stream_data in result:
                        stream_name, stream_messages = stream_data
                        for message_id, fields in stream_messages:
                            message = StreamMessage.from_dict(fields, message_id)
                            messages.append(message)
                            
                except redis.ResponseError as e:
                    if "NOGROUP" in str(e):
                        logger.warning("Consumer group not found, creating", 
                                     stream=stream_name, group=group_name)
                        await self._initialize_consumer_groups()
                    else:
                        logger.error("Error reading from stream", 
                                   stream=stream_name, error=str(e))
            
            return messages
            
        except Exception as e:
            logger.error("Failed to consume messages", streams=streams, error=str(e))
            return []
    
    async def acknowledge_message(self, stream: str, group: str, message_id: str):
        """Acknowledge message processing completion"""
        try:
            stream_name = self.MAIN_STREAMS.get(stream, f"opsconductor:{stream}:events")
            await self.redis_client.xack(stream_name, group, message_id)
            
            await self._publish_metrics("message_acknowledged", {
                "stream": stream_name,
                "group": group,
                "message_id": message_id
            })
            
            logger.debug("Message acknowledged", 
                        stream=stream_name, 
                        group=group, 
                        message_id=message_id)
            
        except Exception as e:
            logger.error("Failed to acknowledge message", 
                        stream=stream, 
                        message_id=message_id, 
                        error=str(e))
    
    async def retry_message(self, message: StreamMessage) -> bool:
        """Retry failed message or send to dead letter queue"""
        try:
            if message.retry_count >= message.max_retries:
                # Send to dead letter queue
                await self._send_to_dead_letter(message)
                return False
            
            # Increment retry count and republish
            message.retry_count += 1
            message.timestamp = time.time()
            
            stream_name = self.MAIN_STREAMS.get(message.stream, f"opsconductor:{message.stream}:events")
            new_message_id = await self.redis_client.xadd(stream_name, message.to_dict())
            
            await self._publish_metrics("message_retried", {
                "original_id": message.id,
                "new_id": new_message_id,
                "retry_count": message.retry_count,
                "stream": stream_name
            })
            
            logger.info("Message retried", 
                       original_id=message.id,
                       new_id=new_message_id,
                       retry_count=message.retry_count)
            
            return True
            
        except Exception as e:
            logger.error("Failed to retry message", message_id=message.id, error=str(e))
            await self._send_to_dead_letter(message)
            return False
    
    async def _send_to_dead_letter(self, message: StreamMessage):
        """Send message to dead letter queue"""
        try:
            dead_letter_data = message.to_dict()
            dead_letter_data.update({
                "original_stream": message.stream,
                "failed_at": str(time.time()),
                "status": MessageStatus.DEAD_LETTER.value
            })
            
            await self.redis_client.xadd(self.DEAD_LETTER_STREAM, dead_letter_data)
            
            await self._publish_metrics("message_dead_lettered", {
                "original_id": message.id,
                "stream": message.stream,
                "retry_count": message.retry_count
            })
            
            logger.warning("Message sent to dead letter queue", 
                          message_id=message.id,
                          stream=message.stream,
                          retry_count=message.retry_count)
            
        except Exception as e:
            logger.error("Failed to send message to dead letter queue", 
                        message_id=message.id, error=str(e))
    
    async def _publish_metrics(self, metric_type: str, data: Dict[str, Any]):
        """Publish metrics to metrics stream"""
        try:
            metrics_data = {
                "metric_type": metric_type,
                "timestamp": str(time.time()),
                "data": json.dumps(data)
            }
            
            await self.redis_client.xadd(
                self.METRICS_STREAM, 
                metrics_data,
                maxlen=50000  # Keep more metrics
            )
            
        except Exception as e:
            logger.debug("Failed to publish metrics", metric_type=metric_type, error=str(e))
    
    async def get_stream_info(self, stream: str) -> Dict[str, Any]:
        """Get stream information and statistics"""
        try:
            stream_name = self.MAIN_STREAMS.get(stream, f"opsconductor:{stream}:events")
            info = await self.redis_client.xinfo_stream(stream_name)
            
            # Get consumer group info
            groups = await self.redis_client.xinfo_groups(stream_name)
            
            return {
                "stream": stream_name,
                "length": info.get("length", 0),
                "first_entry": info.get("first-entry"),
                "last_entry": info.get("last-entry"),
                "consumer_groups": groups
            }
            
        except Exception as e:
            logger.error("Failed to get stream info", stream=stream, error=str(e))
            return {}
    
    async def get_pending_messages(self, stream: str, group: str) -> List[Dict[str, Any]]:
        """Get pending messages for a consumer group"""
        try:
            stream_name = self.MAIN_STREAMS.get(stream, f"opsconductor:{stream}:events")
            pending = await self.redis_client.xpending(stream_name, group)
            
            if pending and pending[0] > 0:
                # Get detailed pending info
                detailed = await self.redis_client.xpending_range(
                    stream_name, group, "-", "+", count=100
                )
                return detailed
            
            return []
            
        except Exception as e:
            logger.error("Failed to get pending messages", 
                        stream=stream, group=group, error=str(e))
            return []
    
    async def cleanup_old_messages(self, max_age_hours: int = 24):
        """Clean up old messages from streams"""
        try:
            cutoff_time = time.time() - (max_age_hours * 3600)
            cutoff_id = f"{int(cutoff_time * 1000)}-0"
            
            for stream_name in self.MAIN_STREAMS.values():
                try:
                    # Trim stream to remove old messages
                    await self.redis_client.xtrim(stream_name, minid=cutoff_id)
                    logger.debug("Cleaned up old messages", 
                               stream=stream_name, 
                               cutoff_hours=max_age_hours)
                except Exception as e:
                    logger.warning("Failed to cleanup stream", 
                                 stream=stream_name, error=str(e))
            
            # Cleanup dead letter queue
            await self.redis_client.xtrim(self.DEAD_LETTER_STREAM, minid=cutoff_id)
            
        except Exception as e:
            logger.error("Failed to cleanup old messages", error=str(e))
    
    async def close(self):
        """Close Redis connection"""
        if self.redis_client:
            await self.redis_client.close()
            logger.info("Redis Streams client closed")

# Convenience functions for common operations
async def publish_event(client: RedisStreamsClient,
                       service: str,
                       event_type: str, 
                       data: Dict[str, Any],
                       priority: MessagePriority = MessagePriority.NORMAL,
                       user_id: Optional[str] = None) -> str:
    """Publish an event to the appropriate service stream"""
    return await client.publish_message(
        stream=service,
        event_type=event_type,
        service=service,
        data=data,
        priority=priority,
        user_id=user_id
    )

async def create_streams_client(redis_url: str = None, password: str = None) -> RedisStreamsClient:
    """Create and initialize a Redis Streams client"""
    if redis_url is None:
        redis_url = "redis://redis:6380/0"  # Default to streams Redis
    
    client = RedisStreamsClient(redis_url, password)
    await client.initialize()
    return client