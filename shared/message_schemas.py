"""
Message Schema Definitions for OpsConductor Celery Implementation

This module defines the message schemas and task parameters for all
Celery task operations in OpsConductor.
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


# Celery Task Names
class TaskNames:
    """Celery task name constants"""
    
    # Job execution tasks
    EXECUTE_JOB_RUN = "shared.tasks.execute_job_run"
    EXECUTE_JOB_STEP = "shared.tasks.execute_job_step"
    PROCESS_JOB_REQUEST = "shared.tasks.process_job_request"
    
    # Notification tasks
    SEND_EMAIL = "shared.tasks.send_email_notification"
    SEND_SLACK = "shared.tasks.send_slack_notification"
    SEND_WEBHOOK = "shared.tasks.send_webhook_notification"
    
    # Test task
    TEST_TASK = "shared.tasks.test_task"


# Celery Queue Names
class CeleryQueues:
    """Celery queue name constants"""
    
    # Job execution queues
    EXECUTION = "execution"
    JOBS = "jobs"
    
    # Notification queues  
    NOTIFICATIONS = "notifications"
    
    # Default queue
    CELERY = "celery"
    
    @classmethod
    def get_queue_for_task(cls, task_name: str) -> str:
        """Get appropriate queue for a task"""
        if "execute_job" in task_name or "execute_step" in task_name:
            return cls.EXECUTION
        elif "process_job" in task_name:
            return cls.JOBS
        elif "notification" in task_name or "send_" in task_name:
            return cls.NOTIFICATIONS
        else:
            return cls.CELERY


# Task Priority Levels
class TaskPriority:
    """Task priority constants for Celery"""
    
    LOW = 1
    NORMAL = 5
    HIGH = 8
    URGENT = 10
    
    @classmethod
    def get_priority(cls, priority_str: str) -> int:
        """Convert priority string to numeric value"""
        priority_map = {
            "low": cls.LOW,
            "normal": cls.NORMAL,
            "high": cls.HIGH,
            "urgent": cls.URGENT
        }
        return priority_map.get(priority_str.lower(), cls.NORMAL)


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