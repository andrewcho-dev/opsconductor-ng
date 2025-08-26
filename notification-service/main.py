#!/usr/bin/env python3
"""
Notification Service - Email and Webhook Notifications
Handles job completion notifications via email and webhooks
"""

import os
import json
import logging
import asyncio
import smtplib
from datetime import datetime, timezone
from typing import List, Optional, Dict, Any
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

import httpx
import psycopg2
from psycopg2.extras import RealDictCursor
from fastapi import FastAPI, HTTPException, Depends, status, BackgroundTasks, Request
from pydantic import BaseModel, Field, EmailStr
from jinja2 import Template

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="Notification Service", version="1.0.0")

# Database configuration
DB_CONFIG = {
    "host": os.getenv("DB_HOST", "postgres"),
    "port": int(os.getenv("DB_PORT", "5432")),
    "database": os.getenv("DB_NAME", "opsconductor"),
    "user": os.getenv("DB_USER", "opsconductor"),
    "password": os.getenv("DB_PASSWORD", "opsconductor123")
}

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

def get_db_connection():
    """Get database connection with RealDictCursor"""
    return psycopg2.connect(
        cursor_factory=RealDictCursor,
        **DB_CONFIG
    )

# Pydantic models
class NotificationCreate(BaseModel):
    job_run_id: int
    channel: str = Field(..., description="Notification channel: 'email' or 'webhook'")
    dest: str = Field(..., description="Email address or webhook URL")
    payload: Dict[str, Any] = Field(default_factory=dict)

class NotificationResponse(BaseModel):
    id: int
    job_run_id: int
    channel: str
    dest: str
    payload: Dict[str, Any]
    status: str
    sent_at: Optional[datetime]
    retries: int

class NotificationListResponse(BaseModel):
    notifications: List[NotificationResponse]
    total: int

class NotificationPreferences(BaseModel):
    user_id: int
    email_enabled: bool = True
    email_address: Optional[EmailStr] = None
    webhook_enabled: bool = False
    webhook_url: Optional[str] = None
    notify_on_success: bool = True
    notify_on_failure: bool = True

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
        async with httpx.AsyncClient() as client:
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

# SMTP Settings Management
def get_smtp_settings_from_db():
    """Get SMTP settings from database"""
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
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
    finally:
        conn.close()

def save_smtp_settings_to_db(settings: SMTPSettings):
    """Save SMTP settings to database"""
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        
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
        
        conn.commit()
        logger.info("SMTP settings saved to database")
        
    except Exception as e:
        logger.error(f"Error saving SMTP settings to DB: {e}")
        conn.rollback()
        raise
    finally:
        conn.close()

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

async def test_smtp_connection(settings: SMTPSettings, test_email: str):
    """Test SMTP connection and send test email"""
    try:
        # Create test email
        msg = MIMEMultipart("alternative")
        msg["Subject"] = "OpsConductor SMTP Test"
        msg["From"] = f"{settings.from_name} <{settings.from_email}>"
        msg["To"] = test_email
        
        html_content = """
        <html>
        <body>
            <h2>SMTP Configuration Test</h2>
            <p>This is a test email to verify your SMTP configuration is working correctly.</p>
            <p><strong>Configuration Details:</strong></p>
            <ul>
                <li>SMTP Host: {host}</li>
                <li>SMTP Port: {port}</li>
                <li>TLS Enabled: {use_tls}</li>
                <li>From Email: {from_email}</li>
            </ul>
            <p>If you received this email, your SMTP configuration is working properly!</p>
        </body>
        </html>
        """.format(
            host=settings.host,
            port=settings.port,
            use_tls=settings.use_tls,
            from_email=settings.from_email
        )
        
        html_part = MIMEText(html_content, "html")
        msg.attach(html_part)
        
        # Send test email
        with smtplib.SMTP(settings.host, settings.port) as server:
            if settings.use_tls:
                server.starttls()
            
            if settings.username and settings.password:
                server.login(settings.username, settings.password)
            
            server.send_message(msg)
        
        return True, "Test email sent successfully!"
        
    except Exception as e:
        logger.error(f"SMTP test failed: {e}")
        return False, f"SMTP test failed: {str(e)}"

# Email templates
EMAIL_TEMPLATES = {
    "job_success": """
<html>
<body>
    <h2>Job Completed Successfully</h2>
    <p>Your job <strong>{{ job_name }}</strong> has completed successfully.</p>
    
    <h3>Job Details:</h3>
    <ul>
        <li><strong>Job ID:</strong> {{ job_id }}</li>
        <li><strong>Run ID:</strong> {{ run_id }}</li>
        <li><strong>Started:</strong> {{ started_at }}</li>
        <li><strong>Finished:</strong> {{ finished_at }}</li>
        <li><strong>Duration:</strong> {{ duration }}</li>
    </ul>
    
    {% if steps_summary %}
    <h3>Steps Summary:</h3>
    <ul>
        <li>Total Steps: {{ steps_summary.total }}</li>
        <li>Successful: {{ steps_summary.succeeded }}</li>
        <li>Failed: {{ steps_summary.failed }}</li>
    </ul>
    {% endif %}
    
    <p>You can view the full details in the OpsConductor dashboard.</p>
</body>
</html>
    """,
    
    "job_failure": """
<html>
<body>
    <h2 style="color: #d32f2f;">Job Failed</h2>
    <p>Your job <strong>{{ job_name }}</strong> has failed.</p>
    
    <h3>Job Details:</h3>
    <ul>
        <li><strong>Job ID:</strong> {{ job_id }}</li>
        <li><strong>Run ID:</strong> {{ run_id }}</li>
        <li><strong>Started:</strong> {{ started_at }}</li>
        <li><strong>Failed:</strong> {{ finished_at }}</li>
        <li><strong>Duration:</strong> {{ duration }}</li>
    </ul>
    
    {% if steps_summary %}
    <h3>Steps Summary:</h3>
    <ul>
        <li>Total Steps: {{ steps_summary.total }}</li>
        <li>Successful: {{ steps_summary.succeeded }}</li>
        <li>Failed: {{ steps_summary.failed }}</li>
    </ul>
    {% endif %}
    
    {% if error_details %}
    <h3>Error Details:</h3>
    <pre style="background-color: #f5f5f5; padding: 10px; border-radius: 4px;">{{ error_details }}</pre>
    {% endif %}
    
    <p>Please check the OpsConductor dashboard for detailed error information.</p>
</body>
</html>
    """
}

async def send_email_notification(notification_id: int, dest: str, payload: Dict[str, Any]):
    """Send email notification"""
    try:
        # Determine template based on job status
        job_status = payload.get("status", "unknown")
        template_name = "job_success" if job_status == "succeeded" else "job_failure"
        
        # Render email template
        template = Template(EMAIL_TEMPLATES[template_name])
        html_content = template.render(**payload)
        
        # Create email message
        msg = MIMEMultipart("alternative")
        msg["Subject"] = f"OpsConductor: Job {payload.get('job_name', 'Unknown')} - {job_status.title()}"
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

async def send_webhook_notification(notification_id: int, dest: str, payload: Dict[str, Any]):
    """Send webhook notification"""
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                dest,
                json=payload,
                headers={"Content-Type": "application/json"}
            )
            
            if response.status_code < 400:
                logger.info(f"Webhook notification {notification_id} sent successfully to {dest}")
                return True
            else:
                logger.error(f"Webhook notification {notification_id} failed with status {response.status_code}")
                return False
                
    except Exception as e:
        logger.error(f"Failed to send webhook notification {notification_id}: {e}")
        return False

async def process_notification(notification_id: int, channel: str, dest: str, payload: Dict[str, Any]):
    """Process a single notification"""
    success = False
    
    if channel == "email":
        success = await send_email_notification(notification_id, dest, payload)
    elif channel == "webhook":
        success = await send_webhook_notification(notification_id, dest, payload)
    else:
        logger.error(f"Unknown notification channel: {channel}")
        return False
    
    # Update notification status in database
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        
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
        
        conn.commit()
        
    except Exception as e:
        logger.error(f"Failed to update notification {notification_id} status: {e}")
        conn.rollback()
    finally:
        conn.close()
    
    return success

async def notification_worker():
    """Background worker that processes pending notifications"""
    global notification_worker_running
    
    logger.info("Notification worker started")
    
    while notification_worker_running:
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            
            # Get pending notifications (including retries)
            cursor.execute("""
                SELECT id, job_run_id, channel, dest, payload
                FROM notifications 
                WHERE status = 'pending' AND retries < 3
                ORDER BY id
                LIMIT 10
            """)
            
            pending_notifications = cursor.fetchall()
            conn.close()
            
            for notification in pending_notifications:
                await process_notification(
                    notification["id"],
                    notification["channel"],
                    notification["dest"],
                    notification["payload"]
                )
            
        except Exception as e:
            logger.error(f"Notification worker error: {e}")
        
        # Wait 30 seconds before next check
        await asyncio.sleep(30)
    
    logger.info("Notification worker stopped")

# API Endpoints

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "service": "notification"}

@app.get("/status", response_model=NotificationWorkerStatus)
async def get_notification_status():
    """Get notification worker status"""
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        
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
    finally:
        conn.close()

@app.post("/notifications", response_model=NotificationResponse)
async def create_notification(
    notification_data: NotificationCreate,
    request: Request
):
    """Create a new notification"""
    # Verify authentication
    await verify_token(request)
    
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        
        # Create notification
        cursor.execute("""
            INSERT INTO notifications (job_run_id, channel, dest, payload)
            VALUES (%s, %s, %s, %s)
            RETURNING id, job_run_id, channel, dest, payload, status, sent_at, retries
        """, (
            notification_data.job_run_id,
            notification_data.channel,
            notification_data.dest,
            json.dumps(notification_data.payload)
        ))
        
        notification = cursor.fetchone()
        conn.commit()
        
        logger.info(f"Created notification {notification['id']} for job run {notification_data.job_run_id}")
        return NotificationResponse(**notification)
        
    except Exception as e:
        logger.error(f"Error creating notification: {e}")
        conn.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create notification"
        )
    finally:
        conn.close()

@app.get("/notifications", response_model=NotificationListResponse)
async def list_notifications(
    request: Request,
    skip: int = 0,
    limit: int = 10,
    job_run_id: Optional[int] = None,
    status: Optional[str] = None
):
    """List notifications with pagination"""
    # Verify authentication
    await verify_token(request)
    
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        
        # Build query with optional filters
        where_clauses = []
        params = []
        
        if job_run_id is not None:
            where_clauses.append("job_run_id = %s")
            params.append(job_run_id)
        
        if status is not None:
            where_clauses.append("status = %s")
            params.append(status)
        
        where_clause = ""
        if where_clauses:
            where_clause = "WHERE " + " AND ".join(where_clauses)
        
        # Get total count
        count_query = f"SELECT COUNT(*) as count FROM notifications {where_clause}"
        cursor.execute(count_query, params)
        total = cursor.fetchone()["count"]
        
        # Get notifications with pagination
        query = f"""
            SELECT id, job_run_id, channel, dest, payload, status, sent_at, retries
            FROM notifications {where_clause}
            ORDER BY id DESC 
            LIMIT %s OFFSET %s
        """
        params.extend([limit, skip])
        cursor.execute(query, params)
        notifications = cursor.fetchall()
        
        return NotificationListResponse(
            notifications=[NotificationResponse(**notification) for notification in notifications],
            total=total
        )
        
    except Exception as e:
        logger.error(f"Error listing notifications: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve notifications"
        )
    finally:
        conn.close()

# SMTP Settings API Endpoints

@app.get("/smtp/settings", response_model=SMTPSettingsResponse)
async def get_smtp_settings(request: Request):
    """Get current SMTP settings"""
    # Verify authentication
    await verify_token(request)
    
    try:
        # Try to get settings from database first
        db_settings = get_smtp_settings_from_db()
        
        # Fall back to environment variables if no DB settings
        if not db_settings:
            db_settings = {
                'host': SMTP_CONFIG['host'],
                'port': str(SMTP_CONFIG['port']),
                'username': SMTP_CONFIG['username'],
                'password': SMTP_CONFIG['password'],
                'use_tls': str(SMTP_CONFIG['use_tls']).lower(),
                'from_email': SMTP_CONFIG['from_email'],
                'from_name': SMTP_CONFIG['from_name']
            }
        
        # Mask password for security
        masked_password = "••••••••" if db_settings.get('password') else ""
        
        return SMTPSettingsResponse(
            host=db_settings.get('host', 'localhost'),
            port=int(db_settings.get('port', 587)),
            username=db_settings.get('username', ''),
            password=masked_password,
            use_tls=db_settings.get('use_tls', 'true').lower() == 'true',
            from_email=db_settings.get('from_email', 'noreply@opsconductor.local'),
            from_name=db_settings.get('from_name', 'OpsConductor'),
            is_configured=bool(db_settings.get('host') and db_settings.get('from_email'))
        )
        
    except Exception as e:
        logger.error(f"Error getting SMTP settings: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve SMTP settings"
        )

@app.post("/smtp/settings")
async def update_smtp_settings(settings: SMTPSettings, request: Request):
    """Update SMTP settings"""
    # Verify authentication
    await verify_token(request)
    
    try:
        # Save to database
        save_smtp_settings_to_db(settings)
        
        # Update in-memory configuration
        update_smtp_config(settings)
        
        logger.info("SMTP settings updated successfully")
        return {"message": "SMTP settings updated successfully", "status": "success"}
        
    except Exception as e:
        logger.error(f"Error updating SMTP settings: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update SMTP settings"
        )

@app.post("/smtp/test", response_model=SMTPTestResponse)
async def test_smtp_settings(test_request: SMTPTestRequest, request: Request):
    """Test SMTP configuration by sending a test email"""
    # Verify authentication
    await verify_token(request)
    
    try:
        # Get current SMTP settings
        db_settings = get_smtp_settings_from_db()
        
        if not db_settings:
            # Use current environment settings
            current_settings = SMTPSettings(
                host=SMTP_CONFIG['host'],
                port=SMTP_CONFIG['port'],
                username=SMTP_CONFIG['username'],
                password=SMTP_CONFIG['password'],
                use_tls=SMTP_CONFIG['use_tls'],
                from_email=SMTP_CONFIG['from_email'],
                from_name=SMTP_CONFIG['from_name']
            )
        else:
            # Use database settings
            current_settings = SMTPSettings(
                host=db_settings.get('host', 'localhost'),
                port=int(db_settings.get('port', 587)),
                username=db_settings.get('username', ''),
                password=db_settings.get('password', ''),
                use_tls=db_settings.get('use_tls', 'true').lower() == 'true',
                from_email=db_settings.get('from_email', 'noreply@opsconductor.local'),
                from_name=db_settings.get('from_name', 'OpsConductor')
            )
        
        # Test the connection
        success, message = await test_smtp_connection(current_settings, test_request.test_email)
        
        return SMTPTestResponse(success=success, message=message)
        
    except Exception as e:
        logger.error(f"Error testing SMTP settings: {e}")
        return SMTPTestResponse(success=False, message=f"Test failed: {str(e)}")

@app.post("/worker/start")
async def start_notification_worker(request: Request):
    """Start notification worker"""
    # Verify authentication
    await verify_token(request)
    
    global notification_worker_running, notification_worker_task
    
    if notification_worker_running:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Notification worker is already running"
        )
    
    notification_worker_running = True
    notification_worker_task = asyncio.create_task(notification_worker())
    
    logger.info("Notification worker started")
    return {"message": "Notification worker started", "status": "running"}

@app.post("/worker/stop")
async def stop_notification_worker(request: Request):
    """Stop notification worker"""
    # Verify authentication
    await verify_token(request)
    
    global notification_worker_running, notification_worker_task
    
    if not notification_worker_running:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Notification worker is not running"
        )
    
    notification_worker_running = False
    
    if notification_worker_task:
        notification_worker_task.cancel()
        try:
            await notification_worker_task
        except asyncio.CancelledError:
            pass
        notification_worker_task = None
    
    logger.info("Notification worker stopped")
    return {"message": "Notification worker stopped", "status": "stopped"}

# Auto-start notification worker on startup
@app.on_event("startup")
async def startup_event():
    """Start notification worker on service startup"""
    global notification_worker_running, notification_worker_task, SMTP_CONFIG
    
    # Load SMTP settings from database if available
    try:
        db_settings = get_smtp_settings_from_db()
        if db_settings:
            SMTP_CONFIG.update({
                'host': db_settings.get('host', SMTP_CONFIG['host']),
                'port': int(db_settings.get('port', SMTP_CONFIG['port'])),
                'username': db_settings.get('username', SMTP_CONFIG['username']),
                'password': db_settings.get('password', SMTP_CONFIG['password']),
                'use_tls': db_settings.get('use_tls', 'true').lower() == 'true',
                'from_email': db_settings.get('from_email', SMTP_CONFIG['from_email']),
                'from_name': db_settings.get('from_name', SMTP_CONFIG['from_name'])
            })
            logger.info("SMTP settings loaded from database")
    except Exception as e:
        logger.warning(f"Could not load SMTP settings from database: {e}")
    
    if not notification_worker_running:
        notification_worker_running = True
        notification_worker_task = asyncio.create_task(notification_worker())
        logger.info("Notification worker auto-started")

@app.on_event("shutdown")
async def shutdown_event():
    """Stop notification worker on service shutdown"""
    global notification_worker_running, notification_worker_task
    
    if notification_worker_running:
        notification_worker_running = False
        if notification_worker_task:
            notification_worker_task.cancel()
            try:
                await notification_worker_task
            except asyncio.CancelledError:
                pass
        logger.info("Notification worker stopped on shutdown")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=3009)