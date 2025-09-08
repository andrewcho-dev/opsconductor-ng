"""
Event Publisher Utility for OpsConductor RabbitMQ

This module provides high-level functions for publishing messages to RabbitMQ
exchanges with proper routing, error handling, and retry logic.
"""

import asyncio
import logging
import uuid
from typing import Dict, Any, Optional
from datetime import datetime
import aio_pika
from aio_pika import Message, DeliveryMode
import json

from .utility_message_queue import get_rabbitmq_connection
from .message_schemas import (
    BaseMessage, NotificationMessage, EmailNotificationMessage, 
    SlackNotificationMessage, WebhookNotificationMessage,
    JobScheduleMessage, AuditLogMessage, RoutingKeys, ExchangeNames
)

logger = logging.getLogger(__name__)


class EventPublisher:
    """High-level event publisher for RabbitMQ messages"""
    
    def __init__(self):
        self.connection = None
    
    async def _ensure_connection(self):
        """Ensure RabbitMQ connection is available"""
        if not self.connection:
            self.connection = await get_rabbitmq_connection()
    
    async def _publish_message(
        self,
        exchange_name: str,
        routing_key: str,
        message: BaseMessage,
        priority: int = 0,
        expiration: Optional[int] = None
    ) -> bool:
        """
        Publish a message to RabbitMQ exchange
        
        Args:
            exchange_name: Name of the exchange
            routing_key: Routing key for message routing
            message: Message object to publish
            priority: Message priority (0-255)
            expiration: Message expiration in milliseconds
            
        Returns:
            bool: True if message was published successfully
        """
        try:
            await self._ensure_connection()
            exchange = await self.connection.get_exchange(exchange_name)
            
            # Create AMQP message
            amqp_message = Message(
                body=message.to_json().encode('utf-8'),
                delivery_mode=DeliveryMode.PERSISTENT,  # Survive broker restarts
                priority=priority,
                message_id=message.message_id,
                timestamp=message.timestamp,
                correlation_id=message.correlation_id,
                headers={
                    "source_service": message.source_service,
                    "message_type": message.__class__.__name__,
                    "retry_count": message.retry_count,
                }
            )
            
            if expiration:
                amqp_message.expiration = expiration
            
            # Publish message
            await exchange.publish(amqp_message, routing_key=routing_key)
            
            logger.info(
                f"Published message {message.message_id} to exchange {exchange_name} "
                f"with routing key {routing_key}"
            )
            return True
            
        except Exception as e:
            logger.error(
                f"Failed to publish message {message.message_id} to {exchange_name}: {e}"
            )
            return False
    
    async def publish_email_notification(
        self,
        to_email: str,
        subject: str,
        body: str,
        source_service: str,
        priority: str = "normal",
        from_email: Optional[str] = None,
        cc: Optional[list[str]] = None,
        bcc: Optional[list[str]] = None,
        correlation_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> bool:
        """
        Publish email notification message
        
        Args:
            to_email: Recipient email address
            subject: Email subject
            body: Email body content
            source_service: Service publishing the message
            priority: Message priority (low, normal, high, urgent)
            from_email: Sender email address
            cc: CC recipients
            bcc: BCC recipients
            correlation_id: Correlation ID for tracking
            metadata: Additional metadata
            
        Returns:
            bool: True if published successfully
        """
        message = EmailNotificationMessage(
            message_id=str(uuid.uuid4()),
            source_service=source_service,
            correlation_id=correlation_id,
            notification_type="email",
            recipient=to_email,
            subject=subject,
            body=body,
            priority=priority,
            to_email=to_email,
            from_email=from_email,
            cc=cc or [],
            bcc=bcc or [],
            metadata=metadata or {}
        )
        
        routing_key = RoutingKeys.get_notification_routing_key("email", priority)
        message_priority = 5 if priority in ["urgent", "high"] else 0
        
        return await self._publish_message(
            ExchangeNames.NOTIFICATIONS,
            routing_key,
            message,
            priority=message_priority
        )
    
    async def publish_slack_notification(
        self,
        channel: str,
        body: str,
        source_service: str,
        priority: str = "normal",
        subject: Optional[str] = None,
        username: Optional[str] = None,
        icon_emoji: Optional[str] = None,
        blocks: Optional[list[Dict[str, Any]]] = None,
        correlation_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> bool:
        """
        Publish Slack notification message
        
        Args:
            channel: Slack channel or user ID
            body: Message content
            source_service: Service publishing the message
            priority: Message priority (low, normal, high, urgent)
            subject: Message subject/title
            username: Bot username
            icon_emoji: Bot icon emoji
            blocks: Slack block kit format
            correlation_id: Correlation ID for tracking
            metadata: Additional metadata
            
        Returns:
            bool: True if published successfully
        """
        message = SlackNotificationMessage(
            message_id=str(uuid.uuid4()),
            source_service=source_service,
            correlation_id=correlation_id,
            notification_type="slack",
            recipient=channel,
            subject=subject,
            body=body,
            priority=priority,
            channel=channel,
            username=username,
            icon_emoji=icon_emoji,
            blocks=blocks,
            metadata=metadata or {}
        )
        
        routing_key = RoutingKeys.get_notification_routing_key("slack", priority)
        message_priority = 5 if priority in ["urgent", "high"] else 0
        
        return await self._publish_message(
            ExchangeNames.NOTIFICATIONS,
            routing_key,
            message,
            priority=message_priority
        )
    
    async def publish_webhook_notification(
        self,
        url: str,
        payload: Dict[str, Any],
        source_service: str,
        priority: str = "normal",
        method: str = "POST",
        headers: Optional[Dict[str, str]] = None,
        correlation_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> bool:
        """
        Publish webhook notification message
        
        Args:
            url: Webhook URL
            payload: Webhook payload
            source_service: Service publishing the message
            priority: Message priority (low, normal, high, urgent)
            method: HTTP method (POST, PUT, PATCH)
            headers: HTTP headers
            correlation_id: Correlation ID for tracking
            metadata: Additional metadata
            
        Returns:
            bool: True if published successfully
        """
        message = WebhookNotificationMessage(
            message_id=str(uuid.uuid4()),
            source_service=source_service,
            correlation_id=correlation_id,
            notification_type="webhook",
            recipient=url,
            subject=None,
            body=json.dumps(payload),
            priority=priority,
            url=url,
            method=method,
            headers=headers or {},
            payload=payload,
            metadata=metadata or {}
        )
        
        routing_key = RoutingKeys.get_notification_routing_key("webhook", priority)
        message_priority = 5 if priority in ["urgent", "high"] else 0
        
        return await self._publish_message(
            ExchangeNames.NOTIFICATIONS,
            routing_key,
            message,
            priority=message_priority
        )
    
    async def publish_job_schedule(
        self,
        job_id: str,
        job_type: str,
        user_id: str,
        source_service: str,
        target_id: Optional[str] = None,
        parameters: Optional[Dict[str, Any]] = None,
        scheduled_time: Optional[datetime] = None,
        priority: str = "normal",
        correlation_id: Optional[str] = None
    ) -> bool:
        """
        Publish job scheduling message
        
        Args:
            job_id: Job identifier
            job_type: Type of job to execute
            user_id: User who scheduled the job
            source_service: Service publishing the message
            target_id: Target system ID
            parameters: Job execution parameters
            scheduled_time: When to execute the job
            priority: Job priority (low, normal, high, urgent)
            correlation_id: Correlation ID for tracking
            
        Returns:
            bool: True if published successfully
        """
        message = JobScheduleMessage(
            message_id=str(uuid.uuid4()),
            source_service=source_service,
            correlation_id=correlation_id,
            job_id=job_id,
            job_type=job_type,
            user_id=user_id,
            target_id=target_id,
            parameters=parameters or {},
            scheduled_time=scheduled_time,
            priority=priority
        )
        
        routing_key = RoutingKeys.get_job_routing_key(priority)
        message_priority = 5 if priority in ["urgent", "high"] else 0
        
        return await self._publish_message(
            ExchangeNames.JOBS,
            routing_key,
            message,
            priority=message_priority
        )
    
    async def publish_audit_log(
        self,
        event_type: str,
        resource_type: str,
        resource_id: str,
        action: str,
        source_service: str,
        user_id: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
        correlation_id: Optional[str] = None
    ) -> bool:
        """
        Publish audit log message
        
        Args:
            event_type: Type of event being logged
            resource_type: Type of resource affected
            resource_id: ID of the resource affected
            action: Action performed
            source_service: Service publishing the message
            user_id: User associated with the event
            details: Additional event details
            ip_address: Client IP address
            user_agent: Client user agent
            correlation_id: Correlation ID for tracking
            
        Returns:
            bool: True if published successfully
        """
        message = AuditLogMessage(
            message_id=str(uuid.uuid4()),
            source_service=source_service,
            correlation_id=correlation_id,
            event_type=event_type,
            user_id=user_id,
            resource_type=resource_type,
            resource_id=resource_id,
            action=action,
            details=details or {},
            ip_address=ip_address,
            user_agent=user_agent
        )
        
        routing_key = RoutingKeys.AUDIT_USER_ACTION if user_id else RoutingKeys.AUDIT_SYSTEM_EVENT
        
        return await self._publish_message(
            ExchangeNames.AUDIT,
            routing_key,
            message,
            priority=0
        )


# Global publisher instance
_event_publisher: Optional[EventPublisher] = None


async def get_event_publisher() -> EventPublisher:
    """Get global event publisher instance"""
    global _event_publisher
    
    if _event_publisher is None:
        _event_publisher = EventPublisher()
    
    return _event_publisher


# Convenience functions for direct publishing
async def publish_email(
    to_email: str,
    subject: str,
    body: str,
    source_service: str,
    **kwargs
) -> bool:
    """Convenience function to publish email notification"""
    publisher = await get_event_publisher()
    return await publisher.publish_email_notification(
        to_email, subject, body, source_service, **kwargs
    )


async def publish_slack(
    channel: str,
    body: str,
    source_service: str,
    **kwargs
) -> bool:
    """Convenience function to publish Slack notification"""
    publisher = await get_event_publisher()
    return await publisher.publish_slack_notification(
        channel, body, source_service, **kwargs
    )


async def publish_webhook(
    url: str,
    payload: Dict[str, Any],
    source_service: str,
    **kwargs
) -> bool:
    """Convenience function to publish webhook notification"""
    publisher = await get_event_publisher()
    return await publisher.publish_webhook_notification(
        url, payload, source_service, **kwargs
    )


async def publish_job(
    job_id: str,
    job_type: str,
    user_id: str,
    source_service: str,
    **kwargs
) -> bool:
    """Convenience function to publish job scheduling message"""
    publisher = await get_event_publisher()
    return await publisher.publish_job_schedule(
        job_id, job_type, user_id, source_service, **kwargs
    )


async def publish_audit(
    event_type: str,
    resource_type: str,
    resource_id: str,
    action: str,
    source_service: str,
    **kwargs
) -> bool:
    """Convenience function to publish audit log message"""
    publisher = await get_event_publisher()
    return await publisher.publish_audit_log(
        event_type, resource_type, resource_id, action, source_service, **kwargs
    )