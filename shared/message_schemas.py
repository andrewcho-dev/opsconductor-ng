"""
Message Schema Definitions for OpsConductor RabbitMQ Implementation

This module defines the message schemas and routing patterns for all
message queue operations in OpsConductor.
"""

from typing import Dict, Any, Optional, Literal
from pydantic import BaseModel, Field
from datetime import datetime
import json


class BaseMessage(BaseModel):
    """Base message schema with common fields"""
    message_id: str = Field(..., description="Unique message identifier")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Message creation timestamp")
    source_service: str = Field(..., description="Service that created the message")
    correlation_id: Optional[str] = Field(None, description="Correlation ID for tracking related messages")
    retry_count: int = Field(default=0, description="Number of retry attempts")
    
    def to_json(self) -> str:
        """Convert message to JSON string"""
        return self.model_dump_json()
    
    @classmethod
    def from_json(cls, json_str: str) -> "BaseMessage":
        """Create message from JSON string"""
        return cls.model_validate_json(json_str)


class NotificationMessage(BaseMessage):
    """Schema for notification messages"""
    notification_type: Literal["email", "slack", "teams", "webhook"] = Field(..., description="Type of notification")
    recipient: str = Field(..., description="Notification recipient")
    subject: Optional[str] = Field(None, description="Notification subject")
    body: str = Field(..., description="Notification body/content")
    priority: Literal["low", "normal", "high", "urgent"] = Field(default="normal", description="Message priority")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional notification metadata")


class EmailNotificationMessage(NotificationMessage):
    """Schema for email notifications"""
    notification_type: Literal["email"] = "email"
    to_email: str = Field(..., description="Recipient email address")
    from_email: Optional[str] = Field(None, description="Sender email address")
    cc: Optional[list[str]] = Field(None, description="CC recipients")
    bcc: Optional[list[str]] = Field(None, description="BCC recipients")
    attachments: Optional[list[str]] = Field(None, description="File paths for attachments")


class SlackNotificationMessage(NotificationMessage):
    """Schema for Slack notifications"""
    notification_type: Literal["slack"] = "slack"
    channel: str = Field(..., description="Slack channel or user ID")
    username: Optional[str] = Field(None, description="Bot username")
    icon_emoji: Optional[str] = Field(None, description="Bot icon emoji")
    blocks: Optional[list[Dict[str, Any]]] = Field(None, description="Slack block kit format")


class WebhookNotificationMessage(NotificationMessage):
    """Schema for webhook notifications"""
    notification_type: Literal["webhook"] = "webhook"
    url: str = Field(..., description="Webhook URL")
    method: Literal["POST", "PUT", "PATCH"] = Field(default="POST", description="HTTP method")
    headers: Dict[str, str] = Field(default_factory=dict, description="HTTP headers")
    payload: Dict[str, Any] = Field(..., description="Webhook payload")


class JobScheduleMessage(BaseMessage):
    """Schema for job scheduling messages"""
    job_id: str = Field(..., description="Job identifier")
    job_type: str = Field(..., description="Type of job to execute")
    user_id: str = Field(..., description="User who scheduled the job")
    target_id: Optional[str] = Field(None, description="Target system ID")
    parameters: Dict[str, Any] = Field(default_factory=dict, description="Job execution parameters")
    scheduled_time: Optional[datetime] = Field(None, description="When to execute the job")
    priority: Literal["low", "normal", "high", "urgent"] = Field(default="normal", description="Job priority")


class AuditLogMessage(BaseMessage):
    """Schema for audit log messages"""
    event_type: str = Field(..., description="Type of event being logged")
    user_id: Optional[str] = Field(None, description="User associated with the event")
    resource_type: str = Field(..., description="Type of resource affected")
    resource_id: str = Field(..., description="ID of the resource affected")
    action: str = Field(..., description="Action performed")
    details: Dict[str, Any] = Field(default_factory=dict, description="Additional event details")
    ip_address: Optional[str] = Field(None, description="Client IP address")
    user_agent: Optional[str] = Field(None, description="Client user agent")


# Routing Key Patterns
class RoutingKeys:
    """Routing key patterns for message routing"""
    
    # Notification routing keys
    EMAIL_NOTIFICATION = "notify.email"
    EMAIL_URGENT = "notify.email.urgent"
    EMAIL_NORMAL = "notify.email.normal"
    
    SLACK_NOTIFICATION = "notify.slack"
    SLACK_URGENT = "notify.slack.urgent"
    SLACK_NORMAL = "notify.slack.normal"
    
    WEBHOOK_NOTIFICATION = "notify.webhook"
    WEBHOOK_URGENT = "notify.webhook.urgent"
    WEBHOOK_NORMAL = "notify.webhook.normal"
    
    # Job scheduling routing keys
    JOB_SCHEDULE = "jobs.schedule"
    JOB_SCHEDULE_URGENT = "jobs.schedule.urgent"
    JOB_SCHEDULE_NORMAL = "jobs.schedule.normal"
    
    # Audit logging routing keys
    AUDIT_LOG = "audit.log"
    AUDIT_USER_ACTION = "audit.log.user"
    AUDIT_SYSTEM_EVENT = "audit.log.system"
    
    @classmethod
    def get_notification_routing_key(cls, notification_type: str, priority: str = "normal") -> str:
        """Get routing key for notification messages"""
        base_key = f"notify.{notification_type}"
        if priority in ["urgent", "high"]:
            return f"{base_key}.urgent"
        return f"{base_key}.normal"
    
    @classmethod
    def get_job_routing_key(cls, priority: str = "normal") -> str:
        """Get routing key for job messages"""
        if priority in ["urgent", "high"]:
            return cls.JOB_SCHEDULE_URGENT
        return cls.JOB_SCHEDULE_NORMAL


# Queue Names
class QueueNames:
    """Queue name constants"""
    
    # Notification queues
    EMAIL_NOTIFICATIONS = "notifications.email"
    SLACK_NOTIFICATIONS = "notifications.slack"
    WEBHOOK_NOTIFICATIONS = "notifications.webhook"
    
    # Job queues
    JOB_SCHEDULER = "jobs.scheduled"
    
    # Audit queues
    AUDIT_LOGS = "audit.logs"
    
    # Dead letter queues
    EMAIL_DLQ = "notifications.email.dlq"
    SLACK_DLQ = "notifications.slack.dlq"
    WEBHOOK_DLQ = "notifications.webhook.dlq"
    JOB_DLQ = "jobs.scheduled.dlq"
    AUDIT_DLQ = "audit.logs.dlq"


# Exchange Names
class ExchangeNames:
    """Exchange name constants"""
    
    NOTIFICATIONS = "notifications"
    JOBS = "jobs"
    AUDIT = "audit"


def create_message_from_dict(message_type: str, data: Dict[str, Any]) -> BaseMessage:
    """Factory function to create message objects from dictionaries"""
    message_classes = {
        "email": EmailNotificationMessage,
        "slack": SlackNotificationMessage,
        "webhook": WebhookNotificationMessage,
        "job_schedule": JobScheduleMessage,
        "audit_log": AuditLogMessage,
    }
    
    message_class = message_classes.get(message_type, BaseMessage)
    return message_class(**data)