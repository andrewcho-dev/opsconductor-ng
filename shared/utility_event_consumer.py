"""
Event Consumer Utility for OpsConductor RabbitMQ

This module provides high-level functions for consuming messages from RabbitMQ
queues with proper acknowledgment, error handling, and retry logic.
"""

import asyncio
import logging
from typing import Callable, Dict, Any, Optional, Awaitable
from datetime import datetime
import aio_pika
from aio_pika.abc import AbstractIncomingMessage
import json

from .utility_message_queue import get_rabbitmq_connection
from .message_schemas import (
    BaseMessage, NotificationMessage, EmailNotificationMessage,
    SlackNotificationMessage, WebhookNotificationMessage,
    JobScheduleMessage, AuditLogMessage, QueueNames, create_message_from_dict
)

logger = logging.getLogger(__name__)

# Type alias for message handler functions
MessageHandler = Callable[[BaseMessage, Dict[str, Any]], Awaitable[bool]]


class EventConsumer:
    """High-level event consumer for RabbitMQ messages"""
    
    def __init__(self):
        self.connection = None
        self.handlers: Dict[str, MessageHandler] = {}
        self.running_consumers: Dict[str, asyncio.Task] = {}
    
    async def _ensure_connection(self):
        """Ensure RabbitMQ connection is available"""
        if not self.connection:
            self.connection = await get_rabbitmq_connection()
    
    def register_handler(self, message_type: str, handler: MessageHandler):
        """
        Register a message handler for a specific message type
        
        Args:
            message_type: Type of message to handle (e.g., 'email', 'slack', 'job_schedule')
            handler: Async function that processes the message
        """
        self.handlers[message_type] = handler
        logger.info(f"Registered handler for message type: {message_type}")
    
    async def _process_message(
        self,
        message: AbstractIncomingMessage,
        queue_name: str
    ) -> None:
        """
        Process an incoming message with error handling and acknowledgment
        
        Args:
            message: Incoming RabbitMQ message
            queue_name: Name of the queue the message came from
        """
        try:
            # Parse message body
            message_data = json.loads(message.body.decode('utf-8'))
            
            # Extract message type from headers or infer from queue
            message_type = message.headers.get('message_type', '').replace('Message', '').lower()
            if not message_type:
                message_type = self._infer_message_type_from_queue(queue_name)
            
            # Create message object
            message_obj = create_message_from_dict(message_type, message_data)
            
            # Get handler for this message type
            handler = self.handlers.get(message_type)
            if not handler:
                logger.warning(f"No handler registered for message type: {message_type}")
                await message.ack()  # Acknowledge to prevent redelivery
                return
            
            # Extract additional context from message headers
            context = {
                'queue_name': queue_name,
                'delivery_tag': message.delivery_tag,
                'redelivered': message.redelivered,
                'headers': dict(message.headers) if message.headers else {},
                'routing_key': message.routing_key,
                'timestamp': message.timestamp,
            }
            
            logger.info(
                f"Processing message {message_obj.message_id} of type {message_type} "
                f"from queue {queue_name}"
            )
            
            # Process message with handler
            success = await handler(message_obj, context)
            
            if success:
                await message.ack()
                logger.info(f"Successfully processed message {message_obj.message_id}")
            else:
                # Check retry count
                retry_count = message_obj.retry_count
                max_retries = 3  # Could be configurable
                
                if retry_count < max_retries:
                    # Reject and requeue for retry
                    await message.reject(requeue=True)
                    logger.warning(
                        f"Message {message_obj.message_id} failed, requeuing "
                        f"(retry {retry_count + 1}/{max_retries})"
                    )
                else:
                    # Max retries reached, send to dead letter queue
                    await message.reject(requeue=False)
                    logger.error(
                        f"Message {message_obj.message_id} failed after {max_retries} retries, "
                        f"sending to dead letter queue"
                    )
                    
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse message JSON: {e}")
            await message.reject(requeue=False)  # Don't retry malformed messages
            
        except Exception as e:
            logger.error(f"Unexpected error processing message: {e}")
            await message.reject(requeue=True)  # Retry on unexpected errors
    
    def _infer_message_type_from_queue(self, queue_name: str) -> str:
        """Infer message type from queue name"""
        queue_type_mapping = {
            QueueNames.EMAIL_NOTIFICATIONS: "email",
            QueueNames.SLACK_NOTIFICATIONS: "slack",
            QueueNames.WEBHOOK_NOTIFICATIONS: "webhook",
            QueueNames.JOB_SCHEDULER: "job_schedule",
            QueueNames.AUDIT_LOGS: "audit_log",
        }
        return queue_type_mapping.get(queue_name, "base")
    
    async def start_consuming(
        self,
        queue_name: str,
        prefetch_count: int = 10,
        consumer_tag: Optional[str] = None
    ) -> None:
        """
        Start consuming messages from a queue
        
        Args:
            queue_name: Name of the queue to consume from
            prefetch_count: Number of unacknowledged messages to prefetch
            consumer_tag: Optional consumer tag for identification
        """
        try:
            await self._ensure_connection()
            queue = await self.connection.get_queue(queue_name)
            
            # Set QoS for this consumer
            await self.connection.channel.set_qos(prefetch_count=prefetch_count)
            
            # Start consuming
            consumer_tag = consumer_tag or f"{queue_name}_consumer"
            
            async def message_processor(message: AbstractIncomingMessage):
                await self._process_message(message, queue_name)
            
            await queue.consume(message_processor, consumer_tag=consumer_tag)
            
            logger.info(f"Started consuming from queue: {queue_name}")
            
        except Exception as e:
            logger.error(f"Failed to start consuming from queue {queue_name}: {e}")
            raise
    
    async def start_consuming_multiple(
        self,
        queue_configs: Dict[str, Dict[str, Any]]
    ) -> None:
        """
        Start consuming from multiple queues concurrently
        
        Args:
            queue_configs: Dict mapping queue names to configuration options
                          e.g., {"queue_name": {"prefetch_count": 10, "consumer_tag": "tag"}}
        """
        tasks = []
        
        for queue_name, config in queue_configs.items():
            task = asyncio.create_task(
                self.start_consuming(
                    queue_name,
                    prefetch_count=config.get('prefetch_count', 10),
                    consumer_tag=config.get('consumer_tag')
                )
            )
            tasks.append(task)
            self.running_consumers[queue_name] = task
        
        # Wait for all consumers to start
        await asyncio.gather(*tasks, return_exceptions=True)
        logger.info(f"Started consuming from {len(queue_configs)} queues")
    
    async def stop_consuming(self, queue_name: Optional[str] = None) -> None:
        """
        Stop consuming from a specific queue or all queues
        
        Args:
            queue_name: Name of the queue to stop consuming from. If None, stops all.
        """
        if queue_name:
            task = self.running_consumers.get(queue_name)
            if task:
                task.cancel()
                del self.running_consumers[queue_name]
                logger.info(f"Stopped consuming from queue: {queue_name}")
        else:
            # Stop all consumers
            for queue_name, task in self.running_consumers.items():
                task.cancel()
                logger.info(f"Stopped consuming from queue: {queue_name}")
            self.running_consumers.clear()


# Global consumer instance
_event_consumer: Optional[EventConsumer] = None


async def get_event_consumer() -> EventConsumer:
    """Get global event consumer instance"""
    global _event_consumer
    
    if _event_consumer is None:
        _event_consumer = EventConsumer()
    
    return _event_consumer


# Decorator for registering message handlers
def message_handler(message_type: str):
    """
    Decorator to register a function as a message handler
    
    Args:
        message_type: Type of message this handler processes
    
    Usage:
        @message_handler("email")
        async def handle_email(message: EmailNotificationMessage, context: Dict[str, Any]) -> bool:
            # Process email notification
            return True
    """
    def decorator(func: MessageHandler):
        async def wrapper():
            consumer = await get_event_consumer()
            consumer.register_handler(message_type, func)
        
        # Register the handler immediately
        asyncio.create_task(wrapper())
        return func
    
    return decorator


# Convenience functions for common consumer patterns
async def start_notification_consumer(
    email_handler: Optional[MessageHandler] = None,
    slack_handler: Optional[MessageHandler] = None,
    webhook_handler: Optional[MessageHandler] = None
) -> None:
    """
    Start consuming notification messages with provided handlers
    
    Args:
        email_handler: Handler for email notifications
        slack_handler: Handler for Slack notifications
        webhook_handler: Handler for webhook notifications
    """
    consumer = await get_event_consumer()
    
    if email_handler:
        consumer.register_handler("email", email_handler)
    if slack_handler:
        consumer.register_handler("slack", slack_handler)
    if webhook_handler:
        consumer.register_handler("webhook", webhook_handler)
    
    queue_configs = {}
    if email_handler:
        queue_configs[QueueNames.EMAIL_NOTIFICATIONS] = {"prefetch_count": 5}
    if slack_handler:
        queue_configs[QueueNames.SLACK_NOTIFICATIONS] = {"prefetch_count": 10}
    if webhook_handler:
        queue_configs[QueueNames.WEBHOOK_NOTIFICATIONS] = {"prefetch_count": 5}
    
    if queue_configs:
        await consumer.start_consuming_multiple(queue_configs)


async def start_job_consumer(job_handler: MessageHandler) -> None:
    """
    Start consuming job scheduling messages
    
    Args:
        job_handler: Handler for job scheduling messages
    """
    consumer = await get_event_consumer()
    consumer.register_handler("job_schedule", job_handler)
    
    await consumer.start_consuming(QueueNames.JOB_SCHEDULER, prefetch_count=3)


async def start_audit_consumer(audit_handler: MessageHandler) -> None:
    """
    Start consuming audit log messages
    
    Args:
        audit_handler: Handler for audit log messages
    """
    consumer = await get_event_consumer()
    consumer.register_handler("audit_log", audit_handler)
    
    await consumer.start_consuming(QueueNames.AUDIT_LOGS, prefetch_count=20)