#!/usr/bin/env python3
"""
Enhanced Notification Service - Phase 7.2
Multi-channel notifications with user preferences and advanced rules
"""

import os
import sys
import json
import logging
import asyncio
import smtplib
from datetime import datetime, timezone, time
from typing import List, Optional, Dict, Any, Union
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

# Add shared module to path
sys.path.append('/home/opsconductor')

import httpx
import psycopg2
from psycopg2.extras import RealDictCursor
from shared.database import get_db_cursor, check_database_health, cleanup_database_pool
from fastapi import FastAPI, HTTPException, Depends, status, BackgroundTasks, Request
from pydantic import BaseModel, Field, EmailStr
from jinja2 import Template, Environment
import re

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="Enhanced Notification Service", version="2.0.0")



# Service URLs
AUTH_SERVICE_URL = os.getenv("AUTH_SERVICE_URL", "http://auth-service:3001")

# SMTP Configuration
SMTP_CONFIG = {
    "host": os.getenv("SMTP_HOST", "localhost"),
    "port": int(os.getenv("SMTP_PORT", "587")),
    "username": os.getenv("SMTP_USERNAME", ""),
    "password": os.getenv("SMTP_PASSWORD", ""),
    "use_tls": os.getenv("SMTP_USE_TLS", "true").lower() == "true",
    "from_email": os.getenv("SMTP_FROM_EMAIL", "noreply@opsconductor.local"),
    "from_name": os.getenv("SMTP_FROM_NAME", "OpsConductor")
}

# Global notification worker state
notification_worker_running = False
notification_worker_task = None



# Enhanced Pydantic models
class NotificationPreferences(BaseModel):
    user_id: int
    email_enabled: bool = True
    email_address: Optional[EmailStr] = None
    webhook_enabled: bool = False
    webhook_url: Optional[str] = None
    slack_enabled: bool = False
    slack_webhook_url: Optional[str] = None
    slack_channel: Optional[str] = None
    teams_enabled: bool = False
    teams_webhook_url: Optional[str] = None
    notify_on_success: bool = True
    notify_on_failure: bool = True
    notify_on_start: bool = False
    quiet_hours_enabled: bool = False
    quiet_hours_start: Optional[time] = None
    quiet_hours_end: Optional[time] = None
    quiet_hours_timezone: str = "America/Los_Angeles"

class NotificationPreferencesResponse(NotificationPreferences):
    id: int
    created_at: datetime
    updated_at: datetime

class NotificationRule(BaseModel):
    user_id: int
    name: str
    description: Optional[str] = None
    is_active: bool = True
    conditions: Dict[str, Any]
    channels: List[str]
    escalation_delay_minutes: int = 0
    escalation_channels: Optional[List[str]] = None

class NotificationRuleResponse(NotificationRule):
    id: int
    created_at: datetime
    updated_at: datetime

class NotificationChannel(BaseModel):
    name: str
    display_name: str
    description: Optional[str] = None
    is_active: bool = True
    configuration_schema: Optional[Dict[str, Any]] = None

class NotificationChannelResponse(NotificationChannel):
    id: int
    created_at: datetime

class NotificationTemplate(BaseModel):
    channel: str
    event_type: str
    name: str
    description: Optional[str] = None
    subject_template: Optional[str] = None
    body_template: str
    is_default: bool = False
    is_active: bool = True

class NotificationTemplateResponse(NotificationTemplate):
    id: int
    created_at: datetime
    updated_at: datetime

class EnhancedNotificationCreate(BaseModel):
    job_run_id: int
    user_id: Optional[int] = None
    event_type: str = Field(..., description="Event type: job_success, job_failure, job_start")
    payload: Dict[str, Any] = Field(default_factory=dict)
    channels: Optional[List[str]] = None  # Override default channels

class NotificationResponse(BaseModel):
    id: int
    job_run_id: int
    user_id: Optional[int]
    channel: str
    dest: str
    payload: Dict[str, Any]
    status: str
    sent_at: Optional[datetime]
    retries: int
    is_escalation: bool = False
    escalation_level: int = 0

class NotificationListResponse(BaseModel):
    notifications: List[NotificationResponse]
    total: int

class NotificationWorkerStatus(BaseModel):
    worker_running: bool
    pending_notifications: int
    failed_notifications: int
    last_check: Optional[datetime]

class SMTPSettings(BaseModel):
    host: str = Field(..., description="SMTP server hostname")
    port: int = Field(..., description="SMTP server port", ge=1, le=65535)
    username: str = Field(default="", description="SMTP username")
    password: str = Field(default="", description="SMTP password")
    use_tls: bool = Field(default=True, description="Use TLS encryption")
    from_email: str = Field(..., description="From email address")
    from_name: str = Field(default="OpsConductor", description="From display name")

class SMTPSettingsResponse(BaseModel):
    host: str
    port: int
    username: str
    password: str = Field(description="Password is masked for security")
    use_tls: bool
    from_email: str
    from_name: str
    is_configured: bool

class SMTPTestRequest(BaseModel):
    test_email: str = Field(..., description="Email address to send test to")
    
class SMTPTestResponse(BaseModel):
    success: bool
    message: str

# Auth verification
async def verify_token_with_auth_service(authorization: str = None):
    """Verify JWT token with auth service"""
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing or invalid authorization header"
        )
    
    token = authorization.split(" ")[1]
    
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.get(
                f"{AUTH_SERVICE_URL}/verify",
                headers={"Authorization": f"Bearer {token}"}
            )
            
            if response.status_code != 200:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid token"
                )
            
            return response.json()
    except httpx.RequestError:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Auth service unavailable"
        )

async def verify_token(request: Request):
    """Dependency for token verification"""
    authorization = request.headers.get("authorization")
    return await verify_token_with_auth_service(authorization)

# Enhanced notification processing functions

def get_user_notification_preferences(user_id: int) -> Optional[Dict[str, Any]]:
    """Get user notification preferences"""
    try:
        with get_db_cursor(commit=False) as cursor:
            cursor.execute("""
                SELECT * FROM user_notification_preferences_view 
                WHERE user_id = %s
            """, (user_id,))
            return cursor.fetchone()
    except Exception as e:
        logger.error(f"Error getting user preferences for user {user_id}: {e}")
        return None

def get_notification_template(channel: str, event_type: str) -> Optional[Dict[str, Any]]:
    """Get notification template for channel and event type"""
    try:
        with get_db_cursor(commit=False) as cursor:
            cursor.execute("""
                SELECT * FROM notification_templates 
                WHERE channel = %s AND event_type = %s AND is_active = true AND deleted_at IS NULL
                ORDER BY is_default DESC, id ASC
                LIMIT 1
            """, (channel, event_type))
            return cursor.fetchone()
    except Exception as e:
        logger.error(f"Error getting template for {channel}/{event_type}: {e}")
        return None

def is_in_quiet_hours(preferences: Dict[str, Any]) -> bool:
    """Check if current time is in user's quiet hours"""
    if not preferences.get('quiet_hours_enabled'):
        return False
    
    quiet_start = preferences.get('quiet_hours_start')
    quiet_end = preferences.get('quiet_hours_end')
    
    if not quiet_start or not quiet_end:
        return False
    
    # For simplicity, using UTC time - in production, would use user's timezone
    current_time = datetime.now(timezone.utc).time()
    
    # Handle quiet hours that span midnight
    if quiet_start <= quiet_end:
        return quiet_start <= current_time <= quiet_end
    else:
        return current_time >= quiet_start or current_time <= quiet_end

def should_notify(preferences: Dict[str, Any], event_type: str) -> bool:
    """Check if user should be notified for this event type"""
    if event_type == "job_success" and not preferences.get('notify_on_success', True):
        return False
    if event_type == "job_failure" and not preferences.get('notify_on_failure', True):
        return False
    if event_type == "job_start" and not preferences.get('notify_on_start', False):
        return False
    
    # Check quiet hours
    if is_in_quiet_hours(preferences):
        # Only notify for failures during quiet hours
        return event_type == "job_failure"
    
    return True

def render_template(template_content: str, payload: Dict[str, Any]) -> str:
    """Render Jinja2 template with payload data"""
    try:
        template = Template(template_content)
        return template.render(**payload)
    except Exception as e:
        logger.error(f"Template rendering error: {e}")
        return template_content

async def send_email_notification(notification_id: int, dest: str, payload: Dict[str, Any], template: Optional[Dict[str, Any]] = None):
    """Send email notification with template support"""
    try:
        # Use template if provided, otherwise fall back to basic template
        if template:
            subject = render_template(template.get('subject_template', 'OpsConductor Notification'), payload)
            html_content = render_template(template['body_template'], payload)
        else:
            # Fallback to basic template
            job_status = payload.get("status", "unknown")
            subject = f"OpsConductor: Job {payload.get('job_name', 'Unknown')} - {job_status.title()}"
            html_content = f"<html><body><h2>Job {job_status.title()}</h2><p>Job details: {json.dumps(payload, indent=2)}</p></body></html>"
        
        # Create email message
        msg = MIMEMultipart("alternative")
        msg["Subject"] = subject
        msg["From"] = f"{SMTP_CONFIG['from_name']} <{SMTP_CONFIG['from_email']}>"
        msg["To"] = dest
        
        # Add HTML content
        html_part = MIMEText(html_content, "html")
        msg.attach(html_part)
        
        # Send email
        with smtplib.SMTP(SMTP_CONFIG["host"], SMTP_CONFIG["port"]) as server:
            if SMTP_CONFIG["use_tls"]:
                server.starttls()
            
            if SMTP_CONFIG["username"] and SMTP_CONFIG["password"]:
                server.login(SMTP_CONFIG["username"], SMTP_CONFIG["password"])
            
            server.send_message(msg)
        
        logger.info(f"Email notification {notification_id} sent successfully to {dest}")
        return True
        
    except Exception as e:
        logger.error(f"Failed to send email notification {notification_id}: {e}")
        return False

async def send_slack_notification(notification_id: int, webhook_url: str, payload: Dict[str, Any], template: Optional[Dict[str, Any]] = None):
    """Send Slack notification"""
    try:
        if template:
            slack_payload = json.loads(render_template(template['body_template'], payload))
        else:
            # Fallback Slack message
            job_status = payload.get("status", "unknown")
            emoji = "✅" if job_status == "succeeded" else "❌"
            slack_payload = {
                "text": f"{emoji} Job {payload.get('job_name', 'Unknown')} - {job_status.title()}",
                "blocks": [
                    {
                        "type": "section",
                        "text": {
                            "type": "mrkdwn",
                            "text": f"*Job {payload.get('job_name', 'Unknown')}* has {job_status}"
                        }
                    }
                ]
            }
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                webhook_url,
                json=slack_payload,
                headers={"Content-Type": "application/json"}
            )
            
            if response.status_code < 400:
                logger.info(f"Slack notification {notification_id} sent successfully")
                return True
            else:
                logger.error(f"Slack notification {notification_id} failed with status {response.status_code}")
                return False
                
    except Exception as e:
        logger.error(f"Failed to send Slack notification {notification_id}: {e}")
        return False

async def send_teams_notification(notification_id: int, webhook_url: str, payload: Dict[str, Any], template: Optional[Dict[str, Any]] = None):
    """Send Microsoft Teams notification"""
    try:
        if template:
            teams_payload = json.loads(render_template(template['body_template'], payload))
        else:
            # Fallback Teams message
            job_status = payload.get("status", "unknown")
            color = "00FF00" if job_status == "succeeded" else "FF0000"
            teams_payload = {
                "@type": "MessageCard",
                "@context": "http://schema.org/extensions",
                "themeColor": color,
                "summary": f"Job {payload.get('job_name', 'Unknown')} {job_status}",
                "sections": [{
                    "activityTitle": f"Job {job_status.title()}",
                    "activitySubtitle": payload.get('job_name', 'Unknown'),
                    "facts": [
                        {"name": "Job ID", "value": str(payload.get('job_id', 'N/A'))},
                        {"name": "Status", "value": job_status.title()}
                    ]
                }]
            }
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                webhook_url,
                json=teams_payload,
                headers={"Content-Type": "application/json"}
            )
            
            if response.status_code < 400:
                logger.info(f"Teams notification {notification_id} sent successfully")
                return True
            else:
                logger.error(f"Teams notification {notification_id} failed with status {response.status_code}")
                return False
                
    except Exception as e:
        logger.error(f"Failed to send Teams notification {notification_id}: {e}")
        return False

async def send_webhook_notification(notification_id: int, webhook_url: str, payload: Dict[str, Any], template: Optional[Dict[str, Any]] = None):
    """Send generic webhook notification"""
    try:
        if template:
            webhook_payload = json.loads(render_template(template['body_template'], payload))
        else:
            # Use payload as-is for generic webhooks
            webhook_payload = payload
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                webhook_url,
                json=webhook_payload,
                headers={"Content-Type": "application/json"}
            )
            
            if response.status_code < 400:
                logger.info(f"Webhook notification {notification_id} sent successfully")
                return True
            else:
                logger.error(f"Webhook notification {notification_id} failed with status {response.status_code}")
                return False
                
    except Exception as e:
        logger.error(f"Failed to send webhook notification {notification_id}: {e}")
        return False

async def process_notification(notification_id: int, channel: str, dest: str, payload: Dict[str, Any], template_id: Optional[int] = None):
    """Process a single notification with template support"""
    success = False
    template = None
    
    # Get template if specified
    if template_id:
        try:
            with get_db_cursor(commit=False) as cursor:
                cursor.execute("SELECT * FROM notification_templates WHERE id = %s", (template_id,))
                template = cursor.fetchone()
        except Exception as e:
            logger.error(f"Error getting template {template_id}: {e}")
    
    # Send notification based on channel
    if channel == "email":
        success = await send_email_notification(notification_id, dest, payload, template)
    elif channel == "slack":
        success = await send_slack_notification(notification_id, dest, payload, template)
    elif channel == "teams":
        success = await send_teams_notification(notification_id, dest, payload, template)
    elif channel == "webhook":
        success = await send_webhook_notification(notification_id, dest, payload, template)
    else:
        logger.error(f"Unknown notification channel: {channel}")
        return False
    
    # Update notification status in database
    try:
        with get_db_cursor() as cursor:
            if success:
                cursor.execute("""
                    UPDATE notifications 
                    SET status = 'sent', sent_at = %s 
                    WHERE id = %s
                """, (datetime.now(timezone.utc), notification_id))
            else:
                cursor.execute("""
                    UPDATE notifications 
                    SET retries = retries + 1 
                    WHERE id = %s
                """, (notification_id,))
                
                # Mark as failed after 3 retries
                cursor.execute("""
                    UPDATE notifications 
                    SET status = 'failed' 
                    WHERE id = %s AND retries >= 3
                """, (notification_id,))
        
    except Exception as e:
        logger.error(f"Failed to update notification {notification_id} status: {e}")
    
    return success

async def create_notifications_for_job_run(job_run_id: int, event_type: str, payload: Dict[str, Any], user_id: Optional[int] = None):
    """Create notifications for a job run based on user preferences"""
    try:
        with get_db_cursor() as cursor:
            # If user_id is provided, get their preferences
            if user_id:
                preferences = get_user_notification_preferences(user_id)
                if not preferences or not should_notify(preferences, event_type):
                    logger.info(f"User {user_id} preferences indicate no notification needed for {event_type}")
                    return []
            else:
                # Get job run details to find the user
                cursor.execute("""
                    SELECT requested_by FROM job_runs WHERE id = %s
                """, (job_run_id,))
                job_run = cursor.fetchone()
                if job_run and job_run['requested_by']:
                    user_id = job_run['requested_by']
                    preferences = get_user_notification_preferences(user_id)
                    if not preferences or not should_notify(preferences, event_type):
                        logger.info(f"User {user_id} preferences indicate no notification needed for {event_type}")
                        return []
                else:
                    # No user found, use default admin notification
                    preferences = None
            
            notifications_created = []
            
            if preferences:
                # Create notifications based on user preferences
                channels_to_notify = []
                
                if preferences.get('email_enabled', True):
                    email_addr = preferences.get('notification_email') or preferences.get('user_email')
                    if email_addr:
                        template = get_notification_template('email', event_type)
                        cursor.execute("""
                            INSERT INTO notifications (job_run_id, user_id, channel, dest, payload, template_id)
                            VALUES (%s, %s, %s, %s, %s, %s)
                            RETURNING id
                        """, (job_run_id, user_id, 'email', email_addr, json.dumps(payload), template['id'] if template else None))
                        notification_id = cursor.fetchone()['id']
                        notifications_created.append(notification_id)
                
                if preferences.get('slack_enabled', False) and preferences.get('slack_webhook_url'):
                    template = get_notification_template('slack', event_type)
                    cursor.execute("""
                        INSERT INTO notifications (job_run_id, user_id, channel, dest, payload, template_id)
                        VALUES (%s, %s, %s, %s, %s, %s)
                        RETURNING id
                    """, (job_run_id, user_id, 'slack', preferences['slack_webhook_url'], json.dumps(payload), template['id'] if template else None))
                    notification_id = cursor.fetchone()['id']
                    notifications_created.append(notification_id)
                
                if preferences.get('teams_enabled', False) and preferences.get('teams_webhook_url'):
                    template = get_notification_template('teams', event_type)
                    cursor.execute("""
                        INSERT INTO notifications (job_run_id, user_id, channel, dest, payload, template_id)
                        VALUES (%s, %s, %s, %s, %s, %s)
                        RETURNING id
                    """, (job_run_id, user_id, 'teams', preferences['teams_webhook_url'], json.dumps(payload), template['id'] if template else None))
                    notification_id = cursor.fetchone()['id']
                    notifications_created.append(notification_id)
                
                if preferences.get('webhook_enabled', False) and preferences.get('webhook_url'):
                    template = get_notification_template('webhook', event_type)
                    cursor.execute("""
                        INSERT INTO notifications (job_run_id, user_id, channel, dest, payload, template_id)
                        VALUES (%s, %s, %s, %s, %s, %s)
                        RETURNING id
                    """, (job_run_id, user_id, 'webhook', preferences['webhook_url'], json.dumps(payload), template['id'] if template else None))
                    notification_id = cursor.fetchone()['id']
                    notifications_created.append(notification_id)
            else:
                # Default notification to admin email
                template = get_notification_template('email', event_type)
                cursor.execute("""
                    INSERT INTO notifications (job_run_id, channel, dest, payload, template_id)
                    VALUES (%s, %s, %s, %s, %s)
                    RETURNING id
                """, (job_run_id, 'email', 'admin@opsconductor.local', json.dumps(payload), template['id'] if template else None))
                notification_id = cursor.fetchone()['id']
                notifications_created.append(notification_id)
            
            logger.info(f"Created {len(notifications_created)} notifications for job run {job_run_id}")
            return notifications_created
        
    except Exception as e:
        logger.error(f"Error creating notifications for job run {job_run_id}: {e}")
        return []

async def notification_worker():
    """Enhanced background worker that processes pending notifications"""
    global notification_worker_running
    
    logger.info("Enhanced notification worker started")
    
    while notification_worker_running:
        try:
            with get_db_cursor(commit=False) as cursor:
                # Get pending notifications (including retries)
                cursor.execute("""
                    SELECT id, job_run_id, user_id, channel, dest, payload, template_id
                    FROM notifications 
                    WHERE status = 'pending' AND retries < 3
                    ORDER BY id
                    LIMIT 10
                """)
                pending_notifications = cursor.fetchall()
            
            for notification in pending_notifications:
                await process_notification(
                    notification["id"],
                    notification["channel"],
                    notification["dest"],
                    notification["payload"],
                    notification["template_id"]
                )
            
        except Exception as e:
            logger.error(f"Notification worker error: {e}")
        
        # Wait 30 seconds before next check
        await asyncio.sleep(30)
    
    logger.info("Enhanced notification worker stopped")

# API Endpoints

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "service": "enhanced-notification", "version": "2.0.0"}

@app.get("/status", response_model=NotificationWorkerStatus)
async def get_notification_status():
    """Get notification worker status"""
    try:
        with get_db_cursor(commit=False) as cursor:
            # Count pending and failed notifications
            cursor.execute("SELECT COUNT(*) as count FROM notifications WHERE status = 'pending'")
            pending_count = cursor.fetchone()["count"]
            
            cursor.execute("SELECT COUNT(*) as count FROM notifications WHERE status = 'failed'")
            failed_count = cursor.fetchone()["count"]
            
            return NotificationWorkerStatus(
                worker_running=notification_worker_running,
                pending_notifications=pending_count,
                failed_notifications=failed_count,
                last_check=datetime.now(timezone.utc)
            )
        
    except Exception as e:
        logger.error(f"Error getting notification status: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get notification status"
        )

# User Notification Preferences Endpoints

@app.get("/preferences/{user_id}", response_model=NotificationPreferencesResponse)
async def get_user_preferences(user_id: int, request: Request):
    """Get user notification preferences"""
    await verify_token(request)
    
    try:
        with get_db_cursor(commit=False) as cursor:
            cursor.execute("""
                SELECT * FROM user_notification_preferences WHERE user_id = %s
            """, (user_id,))
            
            preferences = cursor.fetchone()
            if not preferences:
                # Return default preferences
                return NotificationPreferencesResponse(
                    id=0,
                user_id=user_id,
                email_enabled=True,
                webhook_enabled=False,
                slack_enabled=False,
                teams_enabled=False,
                notify_on_success=True,
                notify_on_failure=True,
                notify_on_start=False,
                quiet_hours_enabled=False,
                quiet_hours_timezone="America/Los_Angeles",
                created_at=datetime.now(timezone.utc),
                updated_at=datetime.now(timezone.utc)
            )
            
            return NotificationPreferencesResponse(**preferences)
        
    except Exception as e:
        logger.error(f"Error getting user preferences: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get user preferences"
        )

@app.put("/preferences/{user_id}", response_model=NotificationPreferencesResponse)
async def update_user_preferences(user_id: int, preferences: NotificationPreferences, request: Request):
    """Update user notification preferences"""
    await verify_token(request)
    
    try:
        with get_db_cursor() as cursor:
            # Upsert preferences
            cursor.execute("""
                INSERT INTO user_notification_preferences (
                    user_id, email_enabled, email_address, webhook_enabled, webhook_url,
                    slack_enabled, slack_webhook_url, slack_channel, teams_enabled, teams_webhook_url,
                    notify_on_success, notify_on_failure, notify_on_start,
                    quiet_hours_enabled, quiet_hours_start, quiet_hours_end, quiet_hours_timezone,
                    updated_at
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (user_id) DO UPDATE SET
                    email_enabled = EXCLUDED.email_enabled,
                    email_address = EXCLUDED.email_address,
                    webhook_enabled = EXCLUDED.webhook_enabled,
                    webhook_url = EXCLUDED.webhook_url,
                    slack_enabled = EXCLUDED.slack_enabled,
                    slack_webhook_url = EXCLUDED.slack_webhook_url,
                    slack_channel = EXCLUDED.slack_channel,
                    teams_enabled = EXCLUDED.teams_enabled,
                    teams_webhook_url = EXCLUDED.teams_webhook_url,
                    notify_on_success = EXCLUDED.notify_on_success,
                    notify_on_failure = EXCLUDED.notify_on_failure,
                    notify_on_start = EXCLUDED.notify_on_start,
                    quiet_hours_enabled = EXCLUDED.quiet_hours_enabled,
                    quiet_hours_start = EXCLUDED.quiet_hours_start,
                    quiet_hours_end = EXCLUDED.quiet_hours_end,
                    quiet_hours_timezone = EXCLUDED.quiet_hours_timezone,
                    updated_at = EXCLUDED.updated_at
                RETURNING *
            """, (
                user_id, preferences.email_enabled, preferences.email_address,
                preferences.webhook_enabled, preferences.webhook_url,
                preferences.slack_enabled, preferences.slack_webhook_url, preferences.slack_channel,
                preferences.teams_enabled, preferences.teams_webhook_url,
                preferences.notify_on_success, preferences.notify_on_failure, preferences.notify_on_start,
                preferences.quiet_hours_enabled, preferences.quiet_hours_start, preferences.quiet_hours_end,
                preferences.quiet_hours_timezone, datetime.now(timezone.utc)
            ))
            
            updated_preferences = cursor.fetchone()
            
            logger.info(f"Updated notification preferences for user {user_id}")
            return NotificationPreferencesResponse(**updated_preferences)
        
    except Exception as e:
        logger.error(f"Error updating user preferences: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update user preferences"
        )

# Notification Channels Endpoints

@app.get("/channels", response_model=List[NotificationChannelResponse])
async def get_notification_channels(request: Request):
    """Get available notification channels"""
    await verify_token(request)
    
    try:
        with get_db_cursor(commit=False) as cursor:
            cursor.execute("SELECT * FROM notification_channels WHERE is_active = true ORDER BY name")
            channels = cursor.fetchall()
            
            return [NotificationChannelResponse(**channel) for channel in channels]
        
    except Exception as e:
        logger.error(f"Error getting notification channels: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get notification channels"
        )

# Enhanced notification creation endpoint

@app.post("/notifications/enhanced", response_model=List[NotificationResponse])
async def create_enhanced_notification(
    notification_data: EnhancedNotificationCreate,
    request: Request
):
    """Create enhanced notifications with user preferences and templates"""
    await verify_token(request)
    
    notification_ids = await create_notifications_for_job_run(
        notification_data.job_run_id,
        notification_data.event_type,
        notification_data.payload,
        notification_data.user_id
    )
    
    if not notification_ids:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No notifications created - check user preferences"
        )
    
    # Return created notifications
    try:
        with get_db_cursor(commit=False) as cursor:
            cursor.execute("""
                SELECT id, job_run_id, user_id, channel, dest, payload, status, sent_at, retries, 
                       is_escalation, escalation_level
                FROM notifications 
                WHERE id = ANY(%s)
            """, (notification_ids,))
            
            notifications = cursor.fetchall()
            return [NotificationResponse(**notification) for notification in notifications]
        
    except Exception as e:
        logger.error(f"Error retrieving created notifications: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Notifications created but failed to retrieve details"
        )

# Internal endpoint for service-to-service communication
@app.post("/internal/notifications/enhanced")
async def create_internal_enhanced_notification(notification: EnhancedNotificationCreate):
    """Create enhanced notifications (internal service endpoint - no auth required)"""
    notification_ids = await create_notifications_for_job_run(
        notification.job_run_id,
        notification.event_type,
        notification.payload,
        notification.user_id
    )
    
    return {"notification_ids": notification_ids, "count": len(notification_ids)}

# Worker control endpoints

@app.post("/worker/start")
async def start_notification_worker(request: Request):
    """Start the notification worker"""
    await verify_token(request)
    
    global notification_worker_running, notification_worker_task
    
    if notification_worker_running:
        return {"message": "Notification worker is already running"}
    
    notification_worker_running = True
    notification_worker_task = asyncio.create_task(notification_worker())
    
    logger.info("Enhanced notification worker started via API")
    return {"message": "Enhanced notification worker started"}

@app.post("/worker/stop")
async def stop_notification_worker(request: Request):
    """Stop the notification worker"""
    await verify_token(request)
    
    global notification_worker_running, notification_worker_task
    
    if not notification_worker_running:
        return {"message": "Notification worker is not running"}
    
    notification_worker_running = False
    
    if notification_worker_task:
        notification_worker_task.cancel()
        try:
            await notification_worker_task
        except asyncio.CancelledError:
            pass
        notification_worker_task = None
    
    logger.info("Enhanced notification worker stopped via API")
    return {"message": "Enhanced notification worker stopped"}

# Legacy endpoints for backward compatibility
@app.get("/notifications", response_model=NotificationListResponse)
async def get_notifications(
    request: Request,
    limit: int = 50,
    offset: int = 0
):
    """Get notifications with pagination"""
    await verify_token(request)
    
    try:
        with get_db_cursor(commit=False) as cursor:
            # Get total count
            cursor.execute("SELECT COUNT(*) as count FROM notifications")
            total = cursor.fetchone()["count"]
            
            # Get notifications with pagination
            cursor.execute("""
                SELECT id, job_run_id, user_id, channel, dest, payload, status, sent_at, retries,
                       is_escalation, escalation_level
                FROM notifications 
                ORDER BY id DESC 
                LIMIT %s OFFSET %s
            """, (limit, offset))
            
            notifications = cursor.fetchall()
            
            return NotificationListResponse(
                notifications=[NotificationResponse(**notification) for notification in notifications],
                total=total
            )
        
    except Exception as e:
        logger.error(f"Error getting notifications: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get notifications"
        )

# SMTP Settings endpoints (keeping existing functionality)
def get_smtp_settings_from_db():
    """Get SMTP settings from database"""
    try:
        with get_db_cursor(commit=False) as cursor:
            cursor.execute("""
                SELECT setting_key, setting_value 
                FROM system_settings 
                WHERE setting_key LIKE 'smtp_%'
            """)
            settings = cursor.fetchall()
            
            # Convert to dict
            smtp_dict = {}
            for setting in settings:
                key = setting['setting_key'].replace('smtp_', '')
                smtp_dict[key] = setting['setting_value']
            
            return smtp_dict
    except Exception as e:
        logger.error(f"Error getting SMTP settings from DB: {e}")
        return {}

def save_smtp_settings_to_db(settings: SMTPSettings):
    """Save SMTP settings to database"""
    try:
        with get_db_cursor() as cursor:
            # Create system_settings table if it doesn't exist
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS system_settings (
                    setting_key VARCHAR(255) PRIMARY KEY,
                    setting_value TEXT NOT NULL,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Save each setting
            settings_dict = {
                'smtp_host': settings.host,
                'smtp_port': str(settings.port),
                'smtp_username': settings.username,
                'smtp_password': settings.password,
                'smtp_use_tls': str(settings.use_tls).lower(),
                'smtp_from_email': settings.from_email,
                'smtp_from_name': settings.from_name
            }
            
            for key, value in settings_dict.items():
                cursor.execute("""
                    INSERT INTO system_settings (setting_key, setting_value, updated_at)
                    VALUES (%s, %s, CURRENT_TIMESTAMP)
                    ON CONFLICT (setting_key) 
                    DO UPDATE SET setting_value = EXCLUDED.setting_value, 
                                 updated_at = CURRENT_TIMESTAMP
                """, (key, value))
            
            logger.info("SMTP settings saved to database")
        
    except Exception as e:
        logger.error(f"Error saving SMTP settings to DB: {e}")
        raise

def update_smtp_config(settings: SMTPSettings):
    """Update global SMTP_CONFIG with new settings"""
    global SMTP_CONFIG
    SMTP_CONFIG.update({
        'host': settings.host,
        'port': settings.port,
        'username': settings.username,
        'password': settings.password,
        'use_tls': settings.use_tls,
        'from_email': settings.from_email,
        'from_name': settings.from_name
    })
    logger.info("SMTP configuration updated in memory")

@app.get("/smtp/settings", response_model=SMTPSettingsResponse)
async def get_smtp_settings(request: Request):
    """Get SMTP settings"""
    await verify_token(request)
    
    # Try to get from database first, fall back to environment
    db_settings = get_smtp_settings_from_db()
    
    if db_settings:
        return SMTPSettingsResponse(
            host=db_settings.get('host', SMTP_CONFIG['host']),
            port=int(db_settings.get('port', SMTP_CONFIG['port'])),
            username=db_settings.get('username', SMTP_CONFIG['username']),
            password="***masked***" if db_settings.get('password') else "",
            use_tls=db_settings.get('use_tls', 'true').lower() == 'true',
            from_email=db_settings.get('from_email', SMTP_CONFIG['from_email']),
            from_name=db_settings.get('from_name', SMTP_CONFIG['from_name']),
            is_configured=bool(db_settings.get('host'))
        )
    else:
        return SMTPSettingsResponse(
            host=SMTP_CONFIG['host'],
            port=SMTP_CONFIG['port'],
            username=SMTP_CONFIG['username'],
            password="***masked***" if SMTP_CONFIG['password'] else "",
            use_tls=SMTP_CONFIG['use_tls'],
            from_email=SMTP_CONFIG['from_email'],
            from_name=SMTP_CONFIG['from_name'],
            is_configured=bool(SMTP_CONFIG['host'] and SMTP_CONFIG['host'] != 'localhost')
        )

@app.post("/smtp/settings", response_model=SMTPSettingsResponse)
async def update_smtp_settings(settings: SMTPSettings, request: Request):
    """Update SMTP settings"""
    await verify_token(request)
    
    try:
        # Save to database
        save_smtp_settings_to_db(settings)
        
        # Update in-memory config
        update_smtp_config(settings)
        
        return SMTPSettingsResponse(
            host=settings.host,
            port=settings.port,
            username=settings.username,
            password="***masked***",
            use_tls=settings.use_tls,
            from_email=settings.from_email,
            from_name=settings.from_name,
            is_configured=True
        )
        
    except Exception as e:
        logger.error(f"Error updating SMTP settings: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update SMTP settings"
        )

@app.post("/smtp/test", response_model=SMTPTestResponse)
async def test_smtp_settings(test_request: SMTPTestRequest, request: Request):
    """Test SMTP configuration"""
    await verify_token(request)
    
    # Get current settings
    db_settings = get_smtp_settings_from_db()
    
    if db_settings:
        settings = SMTPSettings(
            host=db_settings.get('host', SMTP_CONFIG['host']),
            port=int(db_settings.get('port', SMTP_CONFIG['port'])),
            username=db_settings.get('username', SMTP_CONFIG['username']),
            password=db_settings.get('password', SMTP_CONFIG['password']),
            use_tls=db_settings.get('use_tls', 'true').lower() == 'true',
            from_email=db_settings.get('from_email', SMTP_CONFIG['from_email']),
            from_name=db_settings.get('from_name', SMTP_CONFIG['from_name'])
        )
    else:
        settings = SMTPSettings(**SMTP_CONFIG)
    
    try:
        # Create test email
        msg = MIMEMultipart("alternative")
        msg["Subject"] = "OpsConductor Enhanced SMTP Test"
        msg["From"] = f"{settings.from_name} <{settings.from_email}>"
        msg["To"] = test_request.test_email
        
        html_content = f"""
        <html>
        <body>
            <h2>Enhanced SMTP Configuration Test</h2>
            <p>This is a test email to verify your enhanced SMTP configuration is working correctly.</p>
            <p><strong>Configuration Details:</strong></p>
            <ul>
                <li>SMTP Host: {settings.host}</li>
                <li>SMTP Port: {settings.port}</li>
                <li>TLS Enabled: {settings.use_tls}</li>
                <li>From Email: {settings.from_email}</li>
            </ul>
            <p>If you received this email, your enhanced notification system is working properly!</p>
            <p><em>OpsConductor Enhanced Notification Service v2.0.0</em></p>
        </body>
        </html>
        """
        
        html_part = MIMEText(html_content, "html")
        msg.attach(html_part)
        
        # Send test email
        with smtplib.SMTP(settings.host, settings.port) as server:
            if settings.use_tls:
                server.starttls()
            
            if settings.username and settings.password:
                server.login(settings.username, settings.password)
            
            server.send_message(msg)
        
        return SMTPTestResponse(success=True, message="Test email sent successfully!")
        
    except Exception as e:
        logger.error(f"SMTP test failed: {e}")
        return SMTPTestResponse(success=False, message=f"SMTP test failed: {str(e)}")

# Initialize worker on startup
@app.on_event("startup")
async def startup_event():
    """Start notification worker on service startup"""
    global notification_worker_running, notification_worker_task
    
    # Load SMTP settings from database on startup
    db_settings = get_smtp_settings_from_db()
    if db_settings:
        try:
            settings = SMTPSettings(
                host=db_settings.get('host', SMTP_CONFIG['host']),
                port=int(db_settings.get('port', SMTP_CONFIG['port'])),
                username=db_settings.get('username', SMTP_CONFIG['username']),
                password=db_settings.get('password', SMTP_CONFIG['password']),
                use_tls=db_settings.get('use_tls', 'true').lower() == 'true',
                from_email=db_settings.get('from_email', SMTP_CONFIG['from_email']),
                from_name=db_settings.get('from_name', SMTP_CONFIG['from_name'])
            )
            update_smtp_config(settings)
            logger.info("SMTP settings loaded from database")
        except Exception as e:
            logger.error(f"Error loading SMTP settings from database: {e}")
    
    # Start notification worker
    notification_worker_running = True
    notification_worker_task = asyncio.create_task(notification_worker())
    logger.info("Enhanced notification service started with worker")

@app.on_event("shutdown")
async def shutdown_event():
    """Stop notification worker on service shutdown"""
    global notification_worker_running, notification_worker_task
    
    notification_worker_running = False
    if notification_worker_task:
        notification_worker_task.cancel()
        try:
            await notification_worker_task
        except asyncio.CancelledError:
            pass
    
    logger.info("Enhanced notification service stopped")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=3009)