"""
RabbitMQ Message Queue Utility for OpsConductor

This module provides core RabbitMQ connection management, queue setup,
and exchange configuration for OpsConductor services.
"""

import asyncio
import logging
from typing import Optional, Dict, Any, Callable
from contextlib import asynccontextmanager
import aio_pika
from aio_pika import Connection, Channel, Exchange, Queue, ExchangeType
from aio_pika.abc import AbstractRobustConnection
import os
from .message_schemas import ExchangeNames, QueueNames, RoutingKeys

logger = logging.getLogger(__name__)


class RabbitMQConnection:
    """Manages RabbitMQ connection and provides queue/exchange setup"""
    
    def __init__(self, connection_url: Optional[str] = None):
        """
        Initialize RabbitMQ connection manager
        
        Args:
            connection_url: RabbitMQ connection URL. If None, uses environment variables.
        """
        self.connection_url = connection_url or self._build_connection_url()
        self.connection: Optional[AbstractRobustConnection] = None
        self.channel: Optional[Channel] = None
        self.exchanges: Dict[str, Exchange] = {}
        self.queues: Dict[str, Queue] = {}
        self._is_connected = False
    
    def _build_connection_url(self) -> str:
        """Build RabbitMQ connection URL from environment variables"""
        host = os.getenv("RABBITMQ_HOST", "rabbitmq")
        port = os.getenv("RABBITMQ_PORT", "5672")
        username = os.getenv("RABBITMQ_USER", "opsconductor")
        password = os.getenv("RABBITMQ_PASSWORD", "opsconductor123")
        vhost = os.getenv("RABBITMQ_VHOST", "/")
        
        return f"amqp://{username}:{password}@{host}:{port}{vhost}"
    
    async def connect(self) -> None:
        """Establish connection to RabbitMQ"""
        try:
            logger.info(f"Connecting to RabbitMQ at {self.connection_url}")
            self.connection = await aio_pika.connect_robust(
                self.connection_url,
                heartbeat=600,
                blocked_connection_timeout=300,
            )
            self.channel = await self.connection.channel()
            await self.channel.set_qos(prefetch_count=10)  # Limit unacknowledged messages
            self._is_connected = True
            logger.info("Successfully connected to RabbitMQ")
        except Exception as e:
            logger.error(f"Failed to connect to RabbitMQ: {e}")
            raise
    
    async def disconnect(self) -> None:
        """Close RabbitMQ connection"""
        try:
            if self.connection and not self.connection.is_closed:
                await self.connection.close()
                self._is_connected = False
                logger.info("Disconnected from RabbitMQ")
        except Exception as e:
            logger.error(f"Error disconnecting from RabbitMQ: {e}")
    
    async def ensure_connected(self) -> None:
        """Ensure connection is established"""
        if not self._is_connected or not self.connection or self.connection.is_closed:
            await self.connect()
    
    async def setup_exchanges(self) -> None:
        """Set up all required exchanges"""
        await self.ensure_connected()
        
        exchange_configs = [
            (ExchangeNames.NOTIFICATIONS, ExchangeType.TOPIC),
            (ExchangeNames.JOBS, ExchangeType.TOPIC),
            (ExchangeNames.AUDIT, ExchangeType.TOPIC),
        ]
        
        for exchange_name, exchange_type in exchange_configs:
            try:
                exchange = await self.channel.declare_exchange(
                    exchange_name,
                    exchange_type,
                    durable=True  # Survive broker restarts
                )
                self.exchanges[exchange_name] = exchange
                logger.info(f"Declared exchange: {exchange_name}")
            except Exception as e:
                logger.error(f"Failed to declare exchange {exchange_name}: {e}")
                raise
    
    async def setup_queues(self) -> None:
        """Set up all required queues with bindings"""
        await self.ensure_connected()
        await self.setup_exchanges()
        
        # Queue configurations: (queue_name, exchange_name, routing_patterns, dlq_name)
        queue_configs = [
            # Notification queues
            (QueueNames.EMAIL_NOTIFICATIONS, ExchangeNames.NOTIFICATIONS, ["notify.email.*"], QueueNames.EMAIL_DLQ),
            (QueueNames.SLACK_NOTIFICATIONS, ExchangeNames.NOTIFICATIONS, ["notify.slack.*"], QueueNames.SLACK_DLQ),
            (QueueNames.WEBHOOK_NOTIFICATIONS, ExchangeNames.NOTIFICATIONS, ["notify.webhook.*"], QueueNames.WEBHOOK_DLQ),
            
            # Job queues
            (QueueNames.JOB_SCHEDULER, ExchangeNames.JOBS, ["jobs.schedule.*"], QueueNames.JOB_DLQ),
            
            # Audit queues
            (QueueNames.AUDIT_LOGS, ExchangeNames.AUDIT, ["audit.log.*"], QueueNames.AUDIT_DLQ),
        ]
        
        for queue_name, exchange_name, routing_patterns, dlq_name in queue_configs:
            try:
                # Create dead letter queue first
                dlq = await self.channel.declare_queue(
                    dlq_name,
                    durable=True,
                    arguments={
                        "x-message-ttl": 86400000,  # 24 hours TTL for DLQ messages
                    }
                )
                
                # Create main queue with DLQ configuration
                queue = await self.channel.declare_queue(
                    queue_name,
                    durable=True,
                    arguments={
                        "x-dead-letter-exchange": "",  # Default exchange for DLQ
                        "x-dead-letter-routing-key": dlq_name,
                        "x-max-retries": 3,  # Maximum retry attempts
                    }
                )
                
                # Bind queue to exchange with routing patterns
                exchange = self.exchanges[exchange_name]
                for pattern in routing_patterns:
                    await queue.bind(exchange, routing_key=pattern)
                    logger.info(f"Bound queue {queue_name} to exchange {exchange_name} with pattern {pattern}")
                
                self.queues[queue_name] = queue
                self.queues[dlq_name] = dlq
                
            except Exception as e:
                logger.error(f"Failed to setup queue {queue_name}: {e}")
                raise
    
    async def get_exchange(self, exchange_name: str) -> Exchange:
        """Get exchange by name"""
        if exchange_name not in self.exchanges:
            await self.setup_exchanges()
        return self.exchanges[exchange_name]
    
    async def get_queue(self, queue_name: str) -> Queue:
        """Get queue by name"""
        if queue_name not in self.queues:
            await self.setup_queues()
        return self.queues[queue_name]
    
    @asynccontextmanager
    async def get_channel(self):
        """Context manager for getting a channel"""
        await self.ensure_connected()
        try:
            yield self.channel
        except Exception as e:
            logger.error(f"Channel operation failed: {e}")
            raise


# Global connection instance
_rabbitmq_connection: Optional[RabbitMQConnection] = None


async def get_rabbitmq_connection() -> RabbitMQConnection:
    """Get global RabbitMQ connection instance"""
    global _rabbitmq_connection
    
    if _rabbitmq_connection is None:
        _rabbitmq_connection = RabbitMQConnection()
        await _rabbitmq_connection.connect()
        await _rabbitmq_connection.setup_exchanges()
        await _rabbitmq_connection.setup_queues()
    
    return _rabbitmq_connection


async def close_rabbitmq_connection() -> None:
    """Close global RabbitMQ connection"""
    global _rabbitmq_connection
    
    if _rabbitmq_connection:
        await _rabbitmq_connection.disconnect()
        _rabbitmq_connection = None


# Health check function
async def check_rabbitmq_health() -> Dict[str, Any]:
    """Check RabbitMQ connection health"""
    try:
        connection = await get_rabbitmq_connection()
        await connection.ensure_connected()
        
        return {
            "status": "healthy",
            "connected": connection._is_connected,
            "exchanges": len(connection.exchanges),
            "queues": len(connection.queues),
        }
    except Exception as e:
        return {
            "status": "unhealthy",
            "error": str(e),
            "connected": False,
        }