#!/usr/bin/env python3
"""
Enhanced Notification Service - Phase 7.2
Multi-channel notifications with user preferences and advanced rules
"""

import os
import sys
import json
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
from fastapi import FastAPI, HTTPException, Depends, status, BackgroundTasks, Request
from pydantic import BaseModel, Field, EmailStr
from jinja2 import Template, Environment
import re

# Import shared modules
from shared.database import get_db_cursor, check_database_health, cleanup_database_pool
from shared.logging import setup_service_logging, get_logger, log_startup, log_shutdown
from shared.middleware import add_standard_middleware
from shared.models import HealthResponse, HealthCheck, create_success_response
from shared.errors import DatabaseError, ValidationError, NotFoundError, handle_database_error
from shared.auth import get_current_user, require_admin

# Import utility modules
import utility_email_sender as email_sender_utility
import utility_webhook_sender as webhook_sender_utility
import utility_notification_processor as notification_processor_utility
import utility_user_preferences as user_preferences_utility
import utility_template_renderer as template_renderer_utility

# Setup structured logging
setup_service_logging("notification-service", level=os.getenv("LOG_LEVEL", "INFO"))
logger = get_logger("notification-service")

app = FastAPI(
    title="Enhanced Notification Service", 
    version="2.0.0",
    description="Multi-channel notification service with user preferences"
)

# Add standard middleware
add_standard_middleware(app, "notification-service", version="2.0.0")



# Service URLs

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

# Initialize utility modules
email_sender_utility.set_smtp_config(SMTP_CONFIG)
user_preferences_utility.set_db_cursor_func(get_db_cursor)
notification_processor_utility.set_db_cursor_func(get_db_cursor)



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
async def verify_token_with_auth_service(authorization: str = None) -> Dict[str, Any]:
    """Verify JWT token with auth service"""
    if not authorization or not authorization.startswith("Bearer "):
        raise AuthError("Missing or invalid authorization header")
    
    token = authorization.split(" ")[1]
    
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.get(
                f"{AUTH_SERVICE_URL}/verify",
                headers={"Authorization": f"Bearer {token}"}
            )
            
            if response.status_code != 200:
                raise AuthError("Invalid token")
            
            return response.json()
    except httpx.RequestError:
        raise ServiceCommunicationError("unknown", "Auth service unavailable")

async def verify_token(request: Request) -> Dict[str, Any]:
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
    """Render Jinja2 template with payload data using utility module"""
    return template_renderer_utility.render_template(template_content, payload)

async def send_email_notification(notification_id: int, dest: str, payload: Dict[str, Any], template: Optional[Dict[str, Any]] = None) -> bool:
    """Send email notification using utility module"""
    return await email_sender_utility.send_email_notification(notification_id, dest, payload, template)

async def send_slack_notification(notification_id: int, webhook_url: str, payload: Dict[str, Any], template: Optional[Dict[str, Any]] = None) -> bool:
    """Send Slack notification using utility module"""
    return await webhook_sender_utility.send_slack_notification(notification_id, webhook_url, payload, template)

async def send_teams_notification(notification_id: int, webhook_url: str, payload: Dict[str, Any], template: Optional[Dict[str, Any]] = None) -> bool:
    """Send Microsoft Teams notification using utility module"""
    return await webhook_sender_utility.send_teams_notification(notification_id, webhook_url, payload, template)

async def send_webhook_notification(notification_id: int, webhook_url: str, payload: Dict[str, Any], template: Optional[Dict[str, Any]] = None) -> bool:
    """Send generic webhook notification using utility module"""
    return await webhook_sender_utility.send_webhook_notification(notification_id, webhook_url, payload, template)

async def process_notification(notification_id: int, channel: str, dest: str, payload: Dict[str, Any], template_id: Optional[int] = None) -> bool:
    """Process a single notification using utility module"""
    return await notification_processor_utility.process_notification(notification_id, channel, dest, payload, template_id)

async def create_notifications_for_job_run(job_run_id: int, event_type: str, payload: Dict[str, Any], user_id: Optional[int] = None) -> List[int]:
    """Create notifications for a job run using utility module"""
    return await notification_processor_utility.create_notifications_for_job_run(job_run_id, event_type, payload, user_id)

async def notification_worker() -> Dict[str, Any]:
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
async def health_check() -> HealthResponse:
    """Health check endpoint"""
    return {"status": "healthy", "service": "enhanced-notification", "version": "2.0.0"}

@app.get("/metrics/database")
async def database_metrics() -> Dict[str, Any]:
    """Database connection pool metrics endpoint"""
    metrics = get_database_metrics()
    return {
        "service": "notification-service",
        "timestamp": datetime.utcnow().isoformat(),
        "database": metrics
    }

@app.get("/status", response_model=NotificationWorkerStatus)
async def get_notification_status() -> Dict[str, Any]:
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
        raise DatabaseError("Failed to get notification status")

# User Notification Preferences Endpoints

@app.get("/preferences/{user_id}", response_model=NotificationPreferencesResponse)
async def get_user_preferences(user_id: int, request: Request) -> Dict[str, Any]:
    """Get user notification preferences using utility module"""
    await verify_token(request)
    
    preferences = await user_preferences_utility.get_user_preferences(user_id)
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

@app.put("/preferences/{user_id}", response_model=NotificationPreferencesResponse)
async def update_user_preferences(user_id: int, preferences: NotificationPreferences, request: Request) -> Dict[str, Any]:
    """Update user notification preferences using utility module"""
    await verify_token(request)
    
    try:
        # Convert Pydantic model to dict for utility
        preferences_dict = preferences.dict()
        updated_preferences = await user_preferences_utility.update_user_preferences(user_id, preferences_dict)
        
        logger.info(f"Updated notification preferences for user {user_id}")
        return NotificationPreferencesResponse(**updated_preferences)
        
    except Exception as e:
        logger.error(f"Error updating user preferences: {e}")
        raise DatabaseError("Failed to update user preferences")

# Notification Channels Endpoints

@app.get("/channels", response_model=List[NotificationChannelResponse])
async def get_notification_channels(request: Request) -> Dict[str, Any]:
    """Get available notification channels"""
    await verify_token(request)
    
    try:
        with get_db_cursor(commit=False) as cursor:
            cursor.execute("SELECT * FROM notification_channels WHERE is_active = true ORDER BY name")
            channels = cursor.fetchall()
            
            return [NotificationChannelResponse(**channel) for channel in channels]
        
    except Exception as e:
        logger.error(f"Error getting notification channels: {e}")
        raise DatabaseError("Failed to get notification channels")

# Enhanced notification creation endpoint

@app.post("/notifications/enhanced", response_model=List[NotificationResponse])
async def create_enhanced_notification(
    notification_data: EnhancedNotificationCreate,
    request: Request
) -> Dict[str, Any]:
    """Create enhanced notifications with user preferences and templates"""
    await verify_token(request)
    
    notification_ids = await create_notifications_for_job_run(
        notification_data.job_run_id,
        notification_data.event_type,
        notification_data.payload,
        notification_data.user_id
    )
    
    if not notification_ids:
        raise ValidationError("No notifications created - check user preferences")
    
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
        raise DatabaseError("Notifications created but failed to retrieve details")

# Internal endpoint for service-to-service communication
@app.post("/internal/notifications/enhanced")
async def create_internal_enhanced_notification(notification: EnhancedNotificationCreate) -> Dict[str, Any]:
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
async def start_notification_worker(request: Request) -> Dict[str, Any]:
    """Start the notification worker"""
    await verify_token(request)
    
    global notification_worker_running, notification_worker_task
    
    if notification_worker_running:
        return create_success_response(
            message="Notification worker is already running",
            data={"status": "running"}
        )
    
    notification_worker_running = True
    notification_worker_task = asyncio.create_task(notification_worker())
    
    logger.info("Enhanced notification worker started via API")
    return create_success_response(
        message="Enhanced notification worker started",
        data={"status": "started"}
    )

@app.post("/worker/stop")
async def stop_notification_worker(request: Request) -> Dict[str, Any]:
    """Stop the notification worker"""
    await verify_token(request)
    
    global notification_worker_running, notification_worker_task
    
    if not notification_worker_running:
        return create_success_response(
            message="Notification worker is not running",
            data={"status": "stopped"}
        )
    
    notification_worker_running = False
    
    if notification_worker_task:
        notification_worker_task.cancel()
        try:
            await notification_worker_task
        except asyncio.CancelledError:
            pass
        notification_worker_task = None
    
    logger.info("Enhanced notification worker stopped via API")
    return create_success_response(
        message="Enhanced notification worker stopped",
        data={"status": "stopped"}
    )

# Legacy endpoints for backward compatibility
@app.get("/notifications", response_model=NotificationListResponse)
async def get_notifications(
    request: Request,
    limit: int = 50,
    offset: int = 0
) -> Dict[str, Any]:
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
        raise DatabaseError("Failed to get notifications")

# SMTP Settings endpoints (keeping existing functionality)
def get_smtp_settings_from_db() -> Any:
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

def save_smtp_settings_to_db(settings: SMTPSettings) -> None:
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

def update_smtp_config(settings: SMTPSettings) -> None:
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
async def get_smtp_settings(request: Request) -> Dict[str, Any]:
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
async def update_smtp_settings(settings: SMTPSettings, request: Request) -> Dict[str, Any]:
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
        raise DatabaseError("Failed to update SMTP settings")

@app.post("/smtp/test", response_model=SMTPTestResponse)
async def test_smtp_settings(test_request: SMTPTestRequest, request: Request) -> Dict[str, Any]:
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
@app.get("/health", response_model=HealthResponse)
async def health_check() -> HealthResponse:
    """Health check endpoint"""
    db_health = check_database_health()
    
    checks = [
        HealthCheck(
            name="database",
            status=db_health["status"],
            message=db_health.get("message", "Database connection check"),
            duration_ms=db_health.get("response_time_ms")
        ),
        HealthCheck(
            name="notification_worker",
            status="healthy" if notification_worker_running else "unhealthy",
            message="Notification worker status"
        )
    ]
    
    overall_status = "healthy" if db_health["status"] == "healthy" and notification_worker_running else "unhealthy"
    
    return HealthResponse(
        service="notification-service",
        status=overall_status,
        version="2.0.0",
        checks=checks
    )

@app.on_event("startup")
async def startup_event() -> None:
    """Start notification worker on service startup"""
    global notification_worker_running, notification_worker_task
    
    # Log service startup
    log_startup("notification-service", "2.0.0", 3009)
    
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
async def shutdown_event() -> None:
    """Stop notification worker on service shutdown"""
    global notification_worker_running, notification_worker_task
    
    notification_worker_running = False
    if notification_worker_task:
        notification_worker_task.cancel()
        try:
            await notification_worker_task
        except asyncio.CancelledError:
            pass
    
    log_shutdown("notification-service")
    cleanup_database_pool()
    logger.info("Enhanced notification service stopped")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=3009)