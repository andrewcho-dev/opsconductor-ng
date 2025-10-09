#!/usr/bin/env python3
"""
OpsConductor Communication Service
Handles notifications and external integrations
Consolidates: notification-service
"""

import sys
import os
import json
from typing import List, Optional, Dict, Any
from fastapi import Query, HTTPException, status
from pydantic import BaseModel
from datetime import datetime
sys.path.append('/app/shared')
from base_service import BaseService
from health_monitor import HealthMonitor, HealthCheckResult

# ============================================================================
# MODELS
# ============================================================================

class Notification(BaseModel):
    id: int
    notification_id: str
    template_id: Optional[int] = None
    channel_id: Optional[int] = None
    recipient: str
    subject: Optional[str] = None
    message: str
    status: str
    attempts: int
    max_attempts: int
    error_message: Optional[str] = None
    metadata: dict = {}
    scheduled_at: str
    sent_at: Optional[str] = None
    created_at: str

class NotificationCreate(BaseModel):
    template_id: Optional[int] = None
    channel_id: Optional[int] = None
    recipient: str
    subject: Optional[str] = None
    message: str
    metadata: dict = {}
    scheduled_at: Optional[str] = None

class NotificationUpdate(BaseModel):
    status: Optional[str] = None
    error_message: Optional[str] = None
    sent_at: Optional[str] = None

class NotificationListResponse(BaseModel):
    notifications: List[Notification]
    total: int
    skip: int
    limit: int

class NotificationTemplate(BaseModel):
    id: int
    name: str
    template_type: str
    subject_template: Optional[str] = None
    body_template: str
    metadata: dict = {}
    is_active: bool
    created_by: int
    created_at: str
    updated_at: str

class TemplateCreate(BaseModel):
    name: str
    template_type: str
    subject_template: Optional[str] = None
    body_template: str
    metadata: dict = {}
    is_active: bool = True

class TemplateUpdate(BaseModel):
    name: Optional[str] = None
    template_type: Optional[str] = None
    subject_template: Optional[str] = None
    body_template: Optional[str] = None
    metadata: Optional[dict] = None
    is_active: Optional[bool] = None

class TemplateListResponse(BaseModel):
    templates: List[NotificationTemplate]
    total: int
    skip: int
    limit: int

class NotificationChannel(BaseModel):
    id: int
    name: str
    channel_type: str
    configuration: dict = {}
    is_active: bool
    created_by: int
    created_at: str
    updated_at: str

class ChannelCreate(BaseModel):
    name: str
    channel_type: str
    configuration: dict = {}
    is_active: bool = True

class ChannelUpdate(BaseModel):
    name: Optional[str] = None
    channel_type: Optional[str] = None
    configuration: Optional[dict] = None
    is_active: Optional[bool] = None

class ChannelListResponse(BaseModel):
    channels: List[NotificationChannel]
    total: int
    skip: int
    limit: int

class NotificationPreferences(BaseModel):
    id: int
    user_id: int
    email_enabled: bool = True
    sms_enabled: bool = False
    push_enabled: bool = True
    job_success_notifications: bool = True
    job_failure_notifications: bool = True
    system_alerts: bool = True
    maintenance_notifications: bool = True
    email_frequency: str = "immediate"  # immediate, daily, weekly
    quiet_hours_start: Optional[str] = None  # HH:MM format
    quiet_hours_end: Optional[str] = None    # HH:MM format
    timezone: str = "UTC"
    created_at: str
    updated_at: str

class NotificationPreferencesUpdate(BaseModel):
    email_enabled: Optional[bool] = None
    sms_enabled: Optional[bool] = None
    push_enabled: Optional[bool] = None
    job_success_notifications: Optional[bool] = None
    job_failure_notifications: Optional[bool] = None
    system_alerts: Optional[bool] = None
    maintenance_notifications: Optional[bool] = None
    email_frequency: Optional[str] = None
    quiet_hours_start: Optional[str] = None
    quiet_hours_end: Optional[str] = None
    timezone: Optional[str] = None

class SMTPSettings(BaseModel):
    id: int
    host: str
    port: int
    username: Optional[str] = None
    password: Optional[str] = None
    use_tls: bool = True
    use_ssl: bool = False
    from_email: str
    from_name: Optional[str] = None
    is_active: bool = True
    created_at: str
    updated_at: str

class SMTPSettingsCreate(BaseModel):
    host: str
    port: int = 587
    username: Optional[str] = None
    password: Optional[str] = None
    use_tls: bool = True
    use_ssl: bool = False
    from_email: str
    from_name: Optional[str] = None
    is_active: bool = True

class SMTPSettingsUpdate(BaseModel):
    host: Optional[str] = None
    port: Optional[int] = None
    username: Optional[str] = None
    password: Optional[str] = None
    use_tls: Optional[bool] = None
    use_ssl: Optional[bool] = None
    from_email: Optional[str] = None
    from_name: Optional[str] = None
    is_active: Optional[bool] = None

class SMTPTestRequest(BaseModel):
    to_email: str
    subject: str = "Test Email from OpsConductor"
    message: str = "This is a test email to verify SMTP configuration."

class AuditLog(BaseModel):
    id: int
    event_type: str
    entity_type: str
    entity_id: str
    user_id: Optional[int] = None
    action: str
    details: dict = {}
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    created_at: str

class AuditListResponse(BaseModel):
    audit_logs: List[AuditLog]
    total: int
    skip: int
    limit: int

class CommunicationService(BaseService):
    def __init__(self):
        super().__init__("communication-service", "1.0.0", 3004)
        self.worker_status = {
            "running": True,
            "started_at": datetime.utcnow().isoformat(),
            "processed_count": 0,
            "last_activity": datetime.utcnow().isoformat()
        }
        self.health_monitor = HealthMonitor()
        self._setup_health_checks()
    
    async def setup_service_dependencies(self):
        """Setup communication service specific dependencies"""
        # Identity service dependency
        identity_url = os.getenv("IDENTITY_SERVICE_URL", "http://identity-service:3001")
        self.startup_manager.add_service_dependency(
            "identity-service",
            identity_url,
            endpoint="/ready",
            timeout=60,
            critical=True
        )
    
    def _get_current_user_id(self) -> int:
        """Get current user ID from authentication context
        For now returns 1, but should be replaced with proper auth"""
        # TODO: Implement proper authentication context
        return 1
    
    def _setup_health_checks(self):
        """Setup health checks for all system services"""
        # Get current host dynamically
        current_host = os.getenv("HOST_IP", "localhost")
        
        # Database
        self.health_monitor.add_postgres(
            "PostgreSQL Database",
            host=os.getenv("DB_HOST", "postgres"),
            port=int(os.getenv("DB_PORT", "5432")),
            database=os.getenv("DB_NAME", "opsconductor"),
            user=os.getenv("DB_USER", "postgres"),
            password=os.getenv("DB_PASSWORD", "postgres123")
        )
        
        # Redis Cache
        redis_url = f"redis://{os.getenv('REDIS_HOST', 'redis')}:{os.getenv('REDIS_PORT', '6379')}"
        self.health_monitor.add_redis("Redis Cache", redis_url)
        
        # Kong Gateway
        self.health_monitor.add_http_service(
            "Kong Gateway",
            f"http://{os.getenv('KONG_HOST', 'kong')}:8001/status"
        )
        
        # Keycloak
        self.health_monitor.add_http_service(
            "Keycloak",
            f"http://{os.getenv('KEYCLOAK_HOST', 'keycloak')}:{os.getenv('KEYCLOAK_PORT', '8080')}/"
        )
        
        # Identity Service
        self.health_monitor.add_http_service(
            "Identity Service",
            f"http://{os.getenv('IDENTITY_SERVICE_HOST', 'identity-service')}:{os.getenv('IDENTITY_SERVICE_PORT', '3001')}/ready"
        )
        
        # Asset Service
        self.health_monitor.add_http_service(
            "Asset Service",
            f"http://{os.getenv('ASSET_SERVICE_HOST', 'asset-service')}:{os.getenv('ASSET_SERVICE_PORT', '3002')}/ready"
        )
        
        # Automation Service
        self.health_monitor.add_http_service(
            "Automation Service",
            f"http://{os.getenv('AUTOMATION_SERVICE_HOST', 'automation-service')}:{os.getenv('AUTOMATION_SERVICE_PORT', '3003')}/ready"
        )
        
        # AI Brain
        self.health_monitor.add_http_service(
            "AI Brain",
            f"http://{os.getenv('AI_BRAIN_HOST', 'ai-brain')}:{os.getenv('AI_BRAIN_PORT', '3005')}/health"
        )
        
        # Network Analyzer
        self.health_monitor.add_http_service(
            "Network Analyzer",
            f"http://{os.getenv('NETWORK_ANALYZER_HOST', 'network-analyzer-service')}:{os.getenv('NETWORK_ANALYZER_PORT', '3006')}/health"
        )
        
        # Ollama LLM Server
        self.health_monitor.add_http_service(
            "Ollama LLM Server",
            f"http://{os.getenv('OLLAMA_HOST', 'ollama')}:{os.getenv('OLLAMA_PORT', '11434')}/api/tags"
        )
    
    async def on_startup(self):
        """Set the database schema to communication"""
        os.environ["DB_SCHEMA"] = "communication"
        self._setup_routes()
        self._setup_execution_routes()
    
    def _setup_routes(self):
        @self.app.get("/notifications", response_model=NotificationListResponse)
        async def list_notifications(
            skip: int = Query(0, ge=0),
            limit: int = Query(100, ge=1, le=1000)
        ):
            """List all notifications"""
            try:
                async with self.db.pool.acquire() as conn:
                    # Get total count
                    total = await conn.fetchval("SELECT COUNT(*) FROM communication.notifications")
                    
                    # Get notifications with pagination
                    rows = await conn.fetch("""
                        SELECT id, notification_id, template_id, channel_id, recipient,
                               subject, message, status, attempts, max_attempts, error_message,
                               metadata, scheduled_at, sent_at, created_at
                        FROM communication.notifications 
                        ORDER BY created_at DESC 
                        LIMIT $1 OFFSET $2
                    """, limit, skip)
                    
                    notifications = []
                    for row in rows:

                        notifications.append(Notification(
                            id=row['id'],
                            notification_id=str(row['notification_id']),
                            template_id=row['template_id'],
                            channel_id=row['channel_id'],
                            recipient=row['recipient'],
                            subject=row['subject'],
                            message=row['message'],
                            status=row['status'],
                            attempts=row['attempts'],
                            max_attempts=row['max_attempts'],
                            error_message=row['error_message'],
                            metadata=json.loads(row['metadata']) if row['metadata'] else {},
                            scheduled_at=row['scheduled_at'].isoformat(),
                            sent_at=row['sent_at'].isoformat() if row['sent_at'] else None,
                            created_at=row['created_at'].isoformat()
                        ))
                    
                    return NotificationListResponse(
                        notifications=notifications,
                        total=total,
                        skip=skip,
                        limit=limit
                    )
            except Exception as e:
                self.logger.error("Failed to fetch notifications", error=str(e))
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Failed to fetch notifications"
                )
        
        @self.app.get("/templates", response_model=TemplateListResponse)
        async def list_templates(
            skip: int = Query(0, ge=0),
            limit: int = Query(100, ge=1, le=1000)
        ):
            """List all notification templates"""
            try:
                async with self.db.pool.acquire() as conn:
                    # Get total count
                    total = await conn.fetchval("SELECT COUNT(*) FROM communication.notification_templates")
                    
                    # Get templates with pagination
                    rows = await conn.fetch("""
                        SELECT id, name, template_type, subject_template, body_template,
                               metadata, is_active, created_by, created_at, updated_at
                        FROM communication.notification_templates 
                        ORDER BY created_at DESC 
                        LIMIT $1 OFFSET $2
                    """, limit, skip)
                    
                    templates = []
                    for row in rows:
                        templates.append(NotificationTemplate(
                            id=row['id'],
                            name=row['name'],
                            template_type=row['template_type'],
                            subject_template=row['subject_template'],
                            body_template=row['body_template'],
                            metadata=row['metadata'] if isinstance(row['metadata'], dict) else {},
                            is_active=row['is_active'],
                            created_by=row['created_by'],
                            created_at=row['created_at'].isoformat(),
                            updated_at=row['updated_at'].isoformat() if row['updated_at'] else None
                        ))
                    
                    return TemplateListResponse(
                        templates=templates,
                        total=total,
                        skip=skip,
                        limit=limit
                    )
            except Exception as e:
                self.logger.error("Failed to fetch templates", error=str(e))
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Failed to fetch templates"
                )
        
        @self.app.get("/channels", response_model=ChannelListResponse)
        async def list_channels(
            skip: int = Query(0, ge=0),
            limit: int = Query(100, ge=1, le=1000)
        ):
            """List all notification channels"""
            try:
                async with self.db.pool.acquire() as conn:
                    # Get total count
                    total = await conn.fetchval("SELECT COUNT(*) FROM communication.notification_channels")
                    
                    # Get channels with pagination
                    rows = await conn.fetch("""
                        SELECT id, name, channel_type, configuration, is_active,
                               created_by, created_at, updated_at
                        FROM communication.notification_channels 
                        ORDER BY created_at DESC 
                        LIMIT $1 OFFSET $2
                    """, limit, skip)
                    
                    channels = []
                    for row in rows:

                        channels.append(NotificationChannel(
                            id=row['id'],
                            name=row['name'],
                            channel_type=row['channel_type'],
                            configuration=json.loads(row['configuration']) if row['configuration'] else {},
                            is_active=row['is_active'],
                            created_by=row['created_by'],
                            created_at=row['created_at'].isoformat(),
                            updated_at=row['updated_at'].isoformat() if row['updated_at'] else None
                        ))
                    
                    return ChannelListResponse(
                        channels=channels,
                        total=total,
                        skip=skip,
                        limit=limit
                    )
            except Exception as e:
                self.logger.error("Failed to fetch channels", error=str(e))
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Failed to fetch channels"
                )
        
        @self.app.get("/audit", response_model=AuditListResponse)
        async def list_audit(
            skip: int = Query(0, ge=0),
            limit: int = Query(100, ge=1, le=1000)
        ):
            """List all audit logs"""
            try:
                async with self.db.pool.acquire() as conn:
                    # Get total count
                    total = await conn.fetchval("SELECT COUNT(*) FROM audit_logs")
                    
                    # Get audit logs with pagination
                    rows = await conn.fetch("""
                        SELECT id, event_type, entity_type, entity_id, user_id, action,
                               details, ip_address, user_agent, created_at
                        FROM audit_logs 
                        ORDER BY created_at DESC 
                        LIMIT $1 OFFSET $2
                    """, limit, skip)
                    
                    audit_logs = []
                    for row in rows:
                        audit_logs.append(AuditLog(
                            id=row['id'],
                            event_type=row['event_type'],
                            entity_type=row['entity_type'],
                            entity_id=row['entity_id'],
                            user_id=row['user_id'],
                            action=row['action'],
                            details=row['details'] or {},
                            ip_address=str(row['ip_address']) if row['ip_address'] else None,
                            user_agent=row['user_agent'],
                            created_at=row['created_at'].isoformat()
                        ))
                    
                    return AuditListResponse(
                        audit_logs=audit_logs,
                        total=total,
                        skip=skip,
                        limit=limit
                    )
            except Exception as e:
                self.logger.error("Failed to fetch audit logs", error=str(e))
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Failed to fetch audit logs"
                )

        # ============================================================================
        # NOTIFICATION CRUD ENDPOINTS
        # ============================================================================
        
        @self.app.post("/notifications", response_model=dict)
        async def create_notification(notification_data: NotificationCreate):
            """Create a new notification"""
            try:
                async with self.db.pool.acquire() as conn:
                    import uuid
                    notification_id = str(uuid.uuid4())
                    
                    import json
                    row = await conn.fetchrow("""
                        INSERT INTO communication.notifications (notification_id, template_id, channel_id, 
                                                                recipient, subject, message, status, attempts, 
                                                                max_attempts, metadata, scheduled_at)
                        VALUES ($1, $2, $3, $4, $5, $6, 'pending', 0, 3, $7, $8)
                        RETURNING id, notification_id, template_id, channel_id, recipient, subject, 
                                  message, status, attempts, max_attempts, error_message, metadata, 
                                  scheduled_at, sent_at, created_at
                    """, notification_id, notification_data.template_id, notification_data.channel_id,
                         notification_data.recipient, notification_data.subject, notification_data.message,
                         json.dumps(notification_data.metadata or {}), 
                         datetime.fromisoformat(notification_data.scheduled_at) if notification_data.scheduled_at else datetime.utcnow())
                    
                    notification = Notification(
                        id=row['id'],
                        notification_id=str(row['notification_id']),
                        template_id=row['template_id'],
                        channel_id=row['channel_id'],
                        recipient=row['recipient'],
                        subject=row['subject'],
                        message=row['message'],
                        status=row['status'],
                        attempts=row['attempts'],
                        max_attempts=row['max_attempts'],
                        error_message=row['error_message'],
                        metadata=json.loads(row['metadata']) if row['metadata'] else {},
                        scheduled_at=row['scheduled_at'].isoformat(),
                        sent_at=row['sent_at'].isoformat() if row['sent_at'] else None,
                        created_at=row['created_at'].isoformat()
                    )
                    
                    return {"success": True, "message": "Notification created", "data": notification}
            except Exception as e:
                self.logger.error("Failed to create notification", error=str(e))
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Failed to create notification"
                )

        # ============================================================================
        # NOTIFICATION PREFERENCES ENDPOINTS (must come before generic {notification_id})
        # ============================================================================
        
        @self.app.get("/notifications/preferences/{user_id}", response_model=dict)
        async def get_notification_preferences(user_id: int):
            """Get notification preferences for a user"""
            try:
                async with self.db.pool.acquire() as conn:
                    row = await conn.fetchrow("""
                        SELECT id, user_id, email_enabled, sms_enabled, push_enabled,
                               job_success_notifications, job_failure_notifications, 
                               system_alerts, maintenance_notifications, email_frequency,
                               quiet_hours_start, quiet_hours_end, timezone, created_at, updated_at
                        FROM communication.notification_preferences 
                        WHERE user_id = $1
                    """, user_id)
                    
                    if not row:
                        # Create default preferences if none exist
                        row = await conn.fetchrow("""
                            INSERT INTO communication.notification_preferences (user_id)
                            VALUES ($1)
                            RETURNING id, user_id, email_enabled, sms_enabled, push_enabled,
                                     job_success_notifications, job_failure_notifications, 
                                     system_alerts, maintenance_notifications, email_frequency,
                                     quiet_hours_start, quiet_hours_end, timezone, created_at, updated_at
                        """, user_id)
                    
                    preferences = NotificationPreferences(
                        id=row['id'],
                        user_id=row['user_id'],
                        email_enabled=row['email_enabled'],
                        sms_enabled=row['sms_enabled'],
                        push_enabled=row['push_enabled'],
                        job_success_notifications=row['job_success_notifications'],
                        job_failure_notifications=row['job_failure_notifications'],
                        system_alerts=row['system_alerts'],
                        maintenance_notifications=row['maintenance_notifications'],
                        email_frequency=row['email_frequency'],
                        quiet_hours_start=row['quiet_hours_start'],
                        quiet_hours_end=row['quiet_hours_end'],
                        timezone=row['timezone'],
                        created_at=row['created_at'].isoformat(),
                        updated_at=row['updated_at'].isoformat() if row['updated_at'] else None
                    )
                    
                    return {"success": True, "data": preferences}
            except Exception as e:
                self.logger.error("Failed to fetch notification preferences", error=str(e))
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Failed to fetch notification preferences"
                )

        @self.app.put("/notifications/preferences/{user_id}", response_model=dict)
        async def update_notification_preferences(user_id: int, preferences_data: NotificationPreferencesUpdate):
            """Update notification preferences for a user"""
            try:
                async with self.db.pool.acquire() as conn:
                    # Build dynamic update query
                    update_fields = []
                    values = []
                    param_count = 1
                    
                    for field, value in preferences_data.dict(exclude_unset=True).items():
                        if value is not None:
                            update_fields.append(f"{field} = ${param_count}")
                            values.append(value)
                            param_count += 1
                    
                    if not update_fields:
                        raise HTTPException(
                            status_code=status.HTTP_400_BAD_REQUEST,
                            detail="No fields to update"
                        )
                    
                    update_fields.append(f"updated_at = ${param_count}")
                    values.append(datetime.now())
                    values.append(user_id)  # for WHERE clause
                    
                    query = f"""
                        UPDATE communication.notification_preferences 
                        SET {', '.join(update_fields)}
                        WHERE user_id = ${param_count + 1}
                        RETURNING id, user_id, email_enabled, sms_enabled, push_enabled,
                                 job_success_notifications, job_failure_notifications, 
                                 system_alerts, maintenance_notifications, email_frequency,
                                 quiet_hours_start, quiet_hours_end, timezone, created_at, updated_at
                    """
                    
                    row = await conn.fetchrow(query, *values)
                    
                    if not row:
                        raise HTTPException(
                            status_code=status.HTTP_404_NOT_FOUND,
                            detail="Notification preferences not found"
                        )
                    
                    preferences = NotificationPreferences(
                        id=row['id'],
                        user_id=row['user_id'],
                        email_enabled=row['email_enabled'],
                        sms_enabled=row['sms_enabled'],
                        push_enabled=row['push_enabled'],
                        job_success_notifications=row['job_success_notifications'],
                        job_failure_notifications=row['job_failure_notifications'],
                        system_alerts=row['system_alerts'],
                        maintenance_notifications=row['maintenance_notifications'],
                        email_frequency=row['email_frequency'],
                        quiet_hours_start=row['quiet_hours_start'],
                        quiet_hours_end=row['quiet_hours_end'],
                        timezone=row['timezone'],
                        created_at=row['created_at'].isoformat(),
                        updated_at=row['updated_at'].isoformat() if row['updated_at'] else None
                    )
                    
                    return {"success": True, "message": "Preferences updated", "data": preferences}
            except HTTPException:
                raise
            except Exception as e:
                self.logger.error("Failed to update notification preferences", error=str(e))
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Failed to update notification preferences"
                )

        # ============================================================================
        # SMTP CONFIGURATION ENDPOINTS (must come before generic {notification_id})
        # ============================================================================
        
        @self.app.get("/notifications/smtp", response_model=dict)
        async def get_smtp_settings():
            """Get SMTP configuration"""
            try:
                async with self.db.pool.acquire() as conn:
                    row = await conn.fetchrow("""
                        SELECT id, host, port, username, use_tls, use_ssl, from_email, 
                               from_name, is_active, created_at, updated_at
                        FROM communication.smtp_settings 
                        WHERE is_active = true
                        ORDER BY created_at DESC
                        LIMIT 1
                    """)
                    
                    if not row:
                        return {"success": True, "data": None, "message": "No SMTP configuration found"}
                    
                    settings = SMTPSettings(
                        id=row['id'],
                        host=row['host'],
                        port=row['port'],
                        username=row['username'],
                        password="***" if row.get('password') else None,  # Don't expose password
                        use_tls=row['use_tls'],
                        use_ssl=row['use_ssl'],
                        from_email=row['from_email'],
                        from_name=row['from_name'],
                        is_active=row['is_active'],
                        created_at=row['created_at'].isoformat(),
                        updated_at=row['updated_at'].isoformat() if row['updated_at'] else None
                    )
                    
                    return {"success": True, "data": settings}
            except Exception as e:
                self.logger.error("Failed to fetch SMTP settings", error=str(e))
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Failed to fetch SMTP settings"
                )

        @self.app.post("/notifications/smtp", response_model=dict)
        async def create_smtp_settings(smtp_data: SMTPSettingsCreate):
            """Create or update SMTP configuration"""
            try:
                async with self.db.pool.acquire() as conn:
                    # Deactivate existing settings
                    await conn.execute("""
                        UPDATE communication.smtp_settings SET is_active = false
                    """)
                    
                    # Create new settings
                    row = await conn.fetchrow("""
                        INSERT INTO communication.smtp_settings 
                        (host, port, username, password, use_tls, use_ssl, from_email, from_name, is_active)
                        VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9)
                        RETURNING id, host, port, username, use_tls, use_ssl, from_email, 
                                 from_name, is_active, created_at, updated_at
                    """, smtp_data.host, smtp_data.port, smtp_data.username, smtp_data.password,
                         smtp_data.use_tls, smtp_data.use_ssl, smtp_data.from_email, 
                         smtp_data.from_name, smtp_data.is_active)
                    
                    settings = SMTPSettings(
                        id=row['id'],
                        host=row['host'],
                        port=row['port'],
                        username=row['username'],
                        password="***" if smtp_data.password else None,
                        use_tls=row['use_tls'],
                        use_ssl=row['use_ssl'],
                        from_email=row['from_email'],
                        from_name=row['from_name'],
                        is_active=row['is_active'],
                        created_at=row['created_at'].isoformat(),
                        updated_at=row['updated_at'].isoformat() if row['updated_at'] else None
                    )
                    
                    return {"success": True, "message": "SMTP settings created", "data": settings}
            except Exception as e:
                self.logger.error("Failed to create SMTP settings", error=str(e))
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Failed to create SMTP settings"
                )

        @self.app.put("/notifications/smtp/{smtp_id}", response_model=dict)
        async def update_smtp_settings(smtp_id: int, smtp_data: SMTPSettingsUpdate):
            """Update SMTP configuration"""
            try:
                async with self.db.pool.acquire() as conn:
                    # Build dynamic update query
                    update_fields = []
                    values = []
                    param_count = 1
                    
                    for field, value in smtp_data.dict(exclude_unset=True).items():
                        if value is not None:
                            update_fields.append(f"{field} = ${param_count}")
                            values.append(value)
                            param_count += 1
                    
                    if not update_fields:
                        raise HTTPException(
                            status_code=status.HTTP_400_BAD_REQUEST,
                            detail="No fields to update"
                        )
                    
                    update_fields.append(f"updated_at = ${param_count}")
                    values.append(datetime.now())
                    values.append(smtp_id)  # for WHERE clause
                    
                    query = f"""
                        UPDATE communication.smtp_settings 
                        SET {', '.join(update_fields)}
                        WHERE id = ${param_count + 1}
                        RETURNING id, host, port, username, use_tls, use_ssl, from_email, 
                                 from_name, is_active, created_at, updated_at
                    """
                    
                    row = await conn.fetchrow(query, *values)
                    
                    if not row:
                        raise HTTPException(
                            status_code=status.HTTP_404_NOT_FOUND,
                            detail="SMTP settings not found"
                        )
                    
                    settings = SMTPSettings(
                        id=row['id'],
                        host=row['host'],
                        port=row['port'],
                        username=row['username'],
                        password="***",  # Don't expose password
                        use_tls=row['use_tls'],
                        use_ssl=row['use_ssl'],
                        from_email=row['from_email'],
                        from_name=row['from_name'],
                        is_active=row['is_active'],
                        created_at=row['created_at'].isoformat(),
                        updated_at=row['updated_at'].isoformat() if row['updated_at'] else None
                    )
                    
                    return {"success": True, "message": "SMTP settings updated", "data": settings}
            except HTTPException:
                raise
            except Exception as e:
                self.logger.error("Failed to update SMTP settings", error=str(e))
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Failed to update SMTP settings"
                )

        @self.app.post("/notifications/smtp/test", response_model=dict)
        async def test_smtp_settings(test_request: SMTPTestRequest):
            """Test SMTP configuration by sending a test email"""
            try:
                async with self.db.pool.acquire() as conn:
                    # Get active SMTP settings from smtp_settings table
                    row = await conn.fetchrow("""
                        SELECT host, port, username, password, use_tls, use_ssl, 
                               from_email, from_name
                        FROM communication.smtp_settings 
                        WHERE is_active = true
                        ORDER BY created_at DESC
                        LIMIT 1
                    """)
                    
                    if not row:
                        raise HTTPException(
                            status_code=status.HTTP_404_NOT_FOUND,
                            detail="No active SMTP configuration found"
                        )
                    
                    # Build config from row data
                    config = {
                        'host': row['host'],
                        'port': row['port'],
                        'username': row['username'],
                        'password': row['password'],
                        'use_tls': row['use_tls'],
                        'use_ssl': row['use_ssl'],
                        'from_email': row['from_email'],
                        'from_name': row['from_name']
                    }
                    
                    # Test SMTP connection
                    import smtplib
                    from email.mime.text import MIMEText
                    from email.mime.multipart import MIMEMultipart
                    
                    try:
                        # Create message
                        msg = MIMEMultipart()
                        msg['From'] = f"{config.get('from_name', '')} <{config.get('from_email', '')}>" if config.get('from_name') else config.get('from_email', '')
                        msg['To'] = test_request.to_email
                        msg['Subject'] = test_request.subject
                        msg.attach(MIMEText(test_request.message, 'plain'))
                        
                        # Connect to SMTP server
                        if config.get('use_ssl', False):
                            server = smtplib.SMTP_SSL(config.get('host', ''), config.get('port', 587))
                        else:
                            server = smtplib.SMTP(config.get('host', ''), config.get('port', 587))
                            if config.get('use_tls', False):
                                server.starttls()
                        
                        if config.get('username') and config.get('password'):
                            server.login(config.get('username'), config.get('password'))
                        
                        # Send email
                        server.send_message(msg)
                        server.quit()
                        
                        return {"success": True, "message": "Test email sent successfully"}
                    
                    except Exception as smtp_error:
                        return {"success": False, "message": f"SMTP test failed: {str(smtp_error)}"}
                    
            except HTTPException:
                raise
            except Exception as e:
                self.logger.error("Failed to test SMTP settings", error=str(e))
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Failed to test SMTP settings"
                )

        @self.app.post("/channels/test/{channel_type}", response_model=dict)
        async def test_communication_channel(channel_type: str, test_request: dict):
            """Test communication channel configuration"""
            try:
                # Get channel configuration
                async with self.db.pool.acquire() as conn:
                    channel_config = await conn.fetchrow(
                        "SELECT * FROM communication.channels WHERE channel_type = $1 AND is_active = true ORDER BY created_at DESC LIMIT 1",
                        channel_type
                    )
                    
                    if not channel_config:
                        raise HTTPException(
                            status_code=status.HTTP_404_NOT_FOUND,
                            detail=f"No {channel_type} configuration found"
                        )
                    
                    config = channel_config['configuration']
                    test_message = test_request.get('test_message', 'This is a test message from OpsConductor!')
                    
                    if channel_type == 'slack':
                        return await self._test_slack(config, test_message)
                    elif channel_type == 'teams':
                        return await self._test_teams(config, test_message)
                    elif channel_type == 'discord':
                        return await self._test_discord(config, test_message)
                    elif channel_type == 'webhook':
                        return await self._test_webhook(config, test_message)
                    else:
                        raise HTTPException(
                            status_code=status.HTTP_400_BAD_REQUEST,
                            detail=f"Unsupported channel type: {channel_type}"
                        )
                    
            except HTTPException:
                raise
            except Exception as e:
                self.logger.error(f"Failed to test {channel_type} settings", error=str(e))
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail=f"Failed to test {channel_type} settings"
                )

        # ============================================================================
        # WORKER STATUS AND CONTROL ENDPOINTS (must come before generic {notification_id})
        # ============================================================================

        @self.app.get("/notifications/status", response_model=dict)
        async def get_worker_status():
            """Get notification worker status"""
            try:
                async with self.db.pool.acquire() as conn:
                    # Get pending notifications count
                    pending_count = await conn.fetchval(
                        "SELECT COUNT(*) FROM communication.notifications WHERE status = 'pending'"
                    )
                    
                    # Get failed notifications count
                    failed_count = await conn.fetchval(
                        "SELECT COUNT(*) FROM communication.notifications WHERE status = 'failed'"
                    )
                    
                    # Check actual worker status
                    worker_running = self.worker_status["running"]
                    
                    return {
                        "success": True,
                        "data": {
                            "worker_running": worker_running,
                            "pending_notifications": pending_count,
                            "failed_notifications": failed_count,
                            "processed_count": self.worker_status["processed_count"],
                            "started_at": self.worker_status["started_at"],
                            "last_activity": self.worker_status["last_activity"],
                            "last_check": datetime.utcnow().isoformat()
                        }
                    }
            except Exception as e:
                self.logger.error("Failed to get worker status", error=str(e))
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Failed to get worker status"
                )

        @self.app.post("/notifications/worker/{action}", response_model=dict)
        async def control_worker(action: str):
            """Control notification worker (start/stop)"""
            try:
                if action not in ["start", "stop"]:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail="Invalid action. Use 'start' or 'stop'"
                    )
                
                # Update worker status based on action
                if action == "start":
                    if self.worker_status["running"]:
                        return {
                            "success": False,
                            "message": "Worker is already running",
                            "data": {
                                "action": action,
                                "current_status": "running",
                                "timestamp": datetime.utcnow().isoformat()
                            }
                        }
                    else:
                        self.worker_status["running"] = True
                        self.worker_status["started_at"] = datetime.utcnow().isoformat()
                        self.worker_status["last_activity"] = datetime.utcnow().isoformat()
                        return {
                            "success": True,
                            "message": "Worker started successfully",
                            "data": {
                                "action": action,
                                "status": "running",
                                "timestamp": datetime.utcnow().isoformat()
                            }
                        }
                elif action == "stop":
                    if not self.worker_status["running"]:
                        return {
                            "success": False,
                            "message": "Worker is already stopped",
                            "data": {
                                "action": action,
                                "current_status": "stopped",
                                "timestamp": datetime.utcnow().isoformat()
                            }
                        }
                    else:
                        self.worker_status["running"] = False
                        self.worker_status["last_activity"] = datetime.utcnow().isoformat()
                        return {
                            "success": True,
                            "message": "Worker stopped successfully",
                            "data": {
                                "action": action,
                                "status": "stopped",
                                "timestamp": datetime.utcnow().isoformat()
                            }
                        }
            except HTTPException:
                raise
            except Exception as e:
                self.logger.error(f"Failed to {action} worker", error=str(e))
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail=f"Failed to {action} worker"
                )

        @self.app.get("/notifications/{notification_id}", response_model=dict)
        async def get_notification(notification_id: int):
            """Get notification by ID"""
            try:
                async with self.db.pool.acquire() as conn:
                    row = await conn.fetchrow("""
                        SELECT id, notification_id, template_id, channel_id, recipient, subject,
                               message, status, attempts, max_attempts, error_message, metadata,
                               scheduled_at, sent_at, created_at
                        FROM communication.notifications WHERE id = $1
                    """, notification_id)
                    
                    if not row:
                        raise HTTPException(status_code=404, detail="Notification not found")
                    
                    notification = Notification(
                        id=row['id'],
                        notification_id=str(row['notification_id']),
                        template_id=row['template_id'],
                        channel_id=row['channel_id'],
                        recipient=row['recipient'],
                        subject=row['subject'],
                        message=row['message'],
                        status=row['status'],
                        attempts=row['attempts'],
                        max_attempts=row['max_attempts'],
                        error_message=row['error_message'],
                        metadata=json.loads(row['metadata']) if row['metadata'] else {},
                        scheduled_at=row['scheduled_at'].isoformat(),
                        sent_at=row['sent_at'].isoformat() if row['sent_at'] else None,
                        created_at=row['created_at'].isoformat()
                    )
                    
                    return {"success": True, "data": notification}
            except HTTPException:
                raise
            except Exception as e:
                self.logger.error("Failed to get notification", error=str(e))
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Failed to get notification"
                )

        @self.app.put("/notifications/{notification_id}", response_model=dict)
        async def update_notification(notification_id: int, notification_data: NotificationUpdate):
            """Update notification"""
            try:
                async with self.db.pool.acquire() as conn:
                    # Build dynamic update query
                    updates = []
                    values = []
                    param_count = 1
                    
                    if notification_data.status is not None:
                        updates.append(f"status = ${param_count}")
                        values.append(notification_data.status)
                        param_count += 1
                    
                    if notification_data.error_message is not None:
                        updates.append(f"error_message = ${param_count}")
                        values.append(notification_data.error_message)
                        param_count += 1
                    
                    if notification_data.sent_at is not None:
                        updates.append(f"sent_at = ${param_count}")
                        values.append(datetime.fromisoformat(notification_data.sent_at))
                        param_count += 1
                    
                    if not updates:
                        raise HTTPException(status_code=400, detail="No fields to update")
                    
                    values.append(notification_id)
                    
                    query = f"""
                        UPDATE communication.notifications 
                        SET {', '.join(updates)}
                        WHERE id = ${param_count}
                        RETURNING id, notification_id, template_id, channel_id, recipient, subject,
                                  message, status, attempts, max_attempts, error_message, metadata,
                                  scheduled_at, sent_at, created_at
                    """
                    
                    row = await conn.fetchrow(query, *values)
                    
                    if not row:
                        raise HTTPException(status_code=404, detail="Notification not found")
                    
                    notification = Notification(
                        id=row['id'],
                        notification_id=str(row['notification_id']),
                        template_id=row['template_id'],
                        channel_id=row['channel_id'],
                        recipient=row['recipient'],
                        subject=row['subject'],
                        message=row['message'],
                        status=row['status'],
                        attempts=row['attempts'],
                        max_attempts=row['max_attempts'],
                        error_message=row['error_message'],
                        metadata=json.loads(row['metadata']) if row['metadata'] else {},
                        scheduled_at=row['scheduled_at'].isoformat(),
                        sent_at=row['sent_at'].isoformat() if row['sent_at'] else None,
                        created_at=row['created_at'].isoformat()
                    )
                    
                    return {"success": True, "message": "Notification updated", "data": notification}
            except HTTPException:
                raise
            except Exception as e:
                self.logger.error("Failed to update notification", error=str(e))
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Failed to update notification"
                )

        @self.app.delete("/notifications/{notification_id}", response_model=dict)
        async def delete_notification(notification_id: int):
            """Delete notification"""
            try:
                async with self.db.pool.acquire() as conn:
                    result = await conn.execute(
                        "DELETE FROM communication.notifications WHERE id = $1", notification_id
                    )
                    
                    if result == "DELETE 0":
                        raise HTTPException(status_code=404, detail="Notification not found")
                    
                    return {"success": True, "message": "Notification deleted"}
            except HTTPException:
                raise
            except Exception as e:
                self.logger.error("Failed to delete notification", error=str(e))
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Failed to delete notification"
                )

        # ============================================================================
        # TEMPLATE CRUD ENDPOINTS
        # ============================================================================
        
        @self.app.post("/templates", response_model=dict)
        async def create_template(template_data: TemplateCreate):
            """Create a new template"""
            try:
                async with self.db.pool.acquire() as conn:
                    import json
                    row = await conn.fetchrow("""
                        INSERT INTO communication.notification_templates (name, template_type, subject_template, 
                                                                         body_template, metadata, is_active, created_by)
                        VALUES ($1, $2, $3, $4, $5, $6, 1)
                        RETURNING id, name, template_type, subject_template, body_template, metadata,
                                  is_active, created_by, created_at, updated_at
                    """, template_data.name, template_data.template_type, template_data.subject_template,
                         template_data.body_template, json.dumps(template_data.metadata or {}), template_data.is_active)
                    
                    template = NotificationTemplate(
                        id=row['id'],
                        name=row['name'],
                        template_type=row['template_type'],
                        subject_template=row['subject_template'],
                        body_template=row['body_template'],
                        metadata=json.loads(row['metadata']) if row['metadata'] else {},
                        is_active=row['is_active'],
                        created_by=row['created_by'],
                        created_at=row['created_at'].isoformat(),
                        updated_at=row['updated_at'].isoformat() if row['updated_at'] else None
                    )
                    
                    return {"success": True, "message": "Template created", "data": template}
            except Exception as e:
                self.logger.error("Failed to create template", error=str(e))
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Failed to create template"
                )

        @self.app.get("/templates/{template_id}", response_model=dict)
        async def get_template(template_id: int):
            """Get template by ID"""
            try:
                async with self.db.pool.acquire() as conn:
                    row = await conn.fetchrow("""
                        SELECT id, name, template_type, subject_template, body_template, metadata,
                               is_active, created_by, created_at, updated_at
                        FROM communication.notification_templates WHERE id = $1
                    """, template_id)
                    
                    if not row:
                        raise HTTPException(status_code=404, detail="Template not found")
                    
                    template = NotificationTemplate(
                        id=row['id'],
                        name=row['name'],
                        template_type=row['template_type'],
                        subject_template=row['subject_template'],
                        body_template=row['body_template'],
                        metadata=json.loads(row['metadata']) if row['metadata'] else {},
                        is_active=row['is_active'],
                        created_by=row['created_by'],
                        created_at=row['created_at'].isoformat(),
                        updated_at=row['updated_at'].isoformat() if row['updated_at'] else None
                    )
                    
                    return {"success": True, "data": template}
            except HTTPException:
                raise
            except Exception as e:
                self.logger.error("Failed to get template", error=str(e))
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Failed to get template"
                )

        @self.app.put("/templates/{template_id}", response_model=dict)
        async def update_template(template_id: int, template_data: TemplateUpdate):
            """Update template"""
            try:
                async with self.db.pool.acquire() as conn:
                    # Build dynamic update query
                    updates = []
                    values = []
                    param_count = 1
                    
                    if template_data.name is not None:
                        updates.append(f"name = ${param_count}")
                        values.append(template_data.name)
                        param_count += 1
                    if template_data.template_type is not None:
                        updates.append(f"template_type = ${param_count}")
                        values.append(template_data.template_type)
                        param_count += 1
                    if template_data.subject_template is not None:
                        updates.append(f"subject_template = ${param_count}")
                        values.append(template_data.subject_template)
                        param_count += 1
                    if template_data.body_template is not None:
                        updates.append(f"body_template = ${param_count}")
                        values.append(template_data.body_template)
                        param_count += 1
                    if template_data.metadata is not None:

                        updates.append(f"metadata = ${param_count}")
                        values.append(json.dumps(template_data.metadata))
                        param_count += 1
                    if template_data.is_active is not None:
                        updates.append(f"is_active = ${param_count}")
                        values.append(template_data.is_active)
                        param_count += 1
                    
                    if not updates:
                        raise HTTPException(status_code=400, detail="No fields to update")
                    
                    updates.append(f"updated_at = ${param_count}")
                    values.append(datetime.utcnow())
                    param_count += 1
                    values.append(template_id)
                    
                    query = f"""
                        UPDATE communication.notification_templates 
                        SET {', '.join(updates)}
                        WHERE id = ${param_count}
                        RETURNING id, name, template_type, subject_template, body_template, metadata,
                                  is_active, created_by, created_at, updated_at
                    """
                    
                    row = await conn.fetchrow(query, *values)
                    
                    if not row:
                        raise HTTPException(status_code=404, detail="Template not found")
                    
                    import json
                    template = NotificationTemplate(
                        id=row['id'],
                        name=row['name'],
                        template_type=row['template_type'],
                        subject_template=row['subject_template'],
                        body_template=row['body_template'],
                        metadata=json.loads(row['metadata']) if row['metadata'] else {},
                        is_active=row['is_active'],
                        created_by=row['created_by'],
                        created_at=row['created_at'].isoformat(),
                        updated_at=row['updated_at'].isoformat() if row['updated_at'] else None
                    )
                    
                    return {"success": True, "message": "Template updated", "data": template}
            except HTTPException:
                raise
            except Exception as e:
                self.logger.error("Failed to update template", error=str(e))
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Failed to update template"
                )

        # ============================================================================
        # NOTIFICATION CHANNEL MANAGEMENT
        # ============================================================================

        @self.app.post("/channels", response_model=dict)
        async def create_channel(channel_data: ChannelCreate):
            """Create a new notification channel"""
            try:
                async with self.db.pool.acquire() as conn:
                    import json
                    row = await conn.fetchrow("""
                        INSERT INTO communication.notification_channels (name, channel_type, configuration, is_active, created_by)
                        VALUES ($1, $2, $3, $4, $5)
                        RETURNING id, name, channel_type, configuration, is_active, created_by, created_at, updated_at
                    """, channel_data.name, channel_data.channel_type, 
                         json.dumps(channel_data.configuration), channel_data.is_active, 1)
                    
                    channel = NotificationChannel(
                        id=row['id'],
                        name=row['name'],
                        channel_type=row['channel_type'],
                        configuration=json.loads(row['configuration']) if row['configuration'] else {},
                        is_active=row['is_active'],
                        created_by=row['created_by'],
                        created_at=row['created_at'].isoformat(),
                        updated_at=row['updated_at'].isoformat() if row['updated_at'] else None
                    )
                    
                    return {"success": True, "message": "Channel created", "data": channel}
            except Exception as e:
                self.logger.error("Failed to create channel", error=str(e))
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Failed to create channel"
                )

        @self.app.put("/channels/{channel_id}", response_model=dict)
        async def update_channel(channel_id: int, channel_data: ChannelUpdate):
            """Update an existing notification channel"""
            try:
                async with self.db.pool.acquire() as conn:
                    import json
                    
                    # Build update query dynamically based on provided fields
                    update_fields = []
                    update_values = []
                    param_count = 1
                    
                    if channel_data.name is not None:
                        update_fields.append(f"name = ${param_count}")
                        update_values.append(channel_data.name)
                        param_count += 1
                    
                    if channel_data.channel_type is not None:
                        update_fields.append(f"channel_type = ${param_count}")
                        update_values.append(channel_data.channel_type)
                        param_count += 1
                    
                    if channel_data.configuration is not None:
                        update_fields.append(f"configuration = ${param_count}")
                        update_values.append(json.dumps(channel_data.configuration))
                        param_count += 1
                    
                    if channel_data.is_active is not None:
                        update_fields.append(f"is_active = ${param_count}")
                        update_values.append(channel_data.is_active)
                        param_count += 1
                    
                    if not update_fields:
                        raise HTTPException(
                            status_code=status.HTTP_400_BAD_REQUEST,
                            detail="No fields to update"
                        )
                    
                    # Add updated_at field
                    update_fields.append(f"updated_at = NOW()")
                    
                    # Add channel_id for WHERE clause
                    update_values.append(channel_id)
                    
                    query = f"""
                        UPDATE communication.notification_channels 
                        SET {', '.join(update_fields)}
                        WHERE id = ${param_count}
                        RETURNING id, name, channel_type, configuration, is_active, created_by, created_at, updated_at
                    """
                    
                    row = await conn.fetchrow(query, *update_values)
                    
                    if not row:
                        raise HTTPException(
                            status_code=status.HTTP_404_NOT_FOUND,
                            detail="Channel not found"
                        )
                    
                    channel = NotificationChannel(
                        id=row['id'],
                        name=row['name'],
                        channel_type=row['channel_type'],
                        configuration=json.loads(row['configuration']) if row['configuration'] else {},
                        is_active=row['is_active'],
                        created_by=row['created_by'],
                        created_at=row['created_at'].isoformat(),
                        updated_at=row['updated_at'].isoformat() if row['updated_at'] else None
                    )
                    
                    return {"success": True, "message": "Channel updated", "data": channel}
            except HTTPException:
                raise
            except Exception as e:
                self.logger.error("Failed to update channel", error=str(e))
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Failed to update channel"
                )
        
        # Health monitoring endpoints
        @self.app.get("/health/services")
        async def get_services_health():
            """Get health status of all services"""
            try:
                results = await self.health_monitor.check_all()
                
                services = []
                for name, result in results.items():
                    # Map health status to service status
                    if result.status.value == "healthy":
                        status = "running"
                    elif result.status.value == "degraded":
                        status = "warning"
                    else:
                        status = "error"
                    
                    # Calculate uptime (mock for now, should be tracked properly)
                    uptime = 0 if status == "error" else 86400  # 1 day if healthy
                    
                    service_data = {
                        "id": str(hash(name) % 1000),  # Generate consistent ID
                        "name": name,
                        "type": self._get_service_type(name),
                        "status": status,
                        "uptime": uptime,
                        "responseTime": result.metrics.response_time,
                        "lastCheck": result.timestamp.isoformat(),
                        "url": self._get_service_url(name),
                        "errorMessage": result.error_message
                    }
                    services.append(service_data)
                
                return {"services": services}
            except Exception as e:
                self.logger.error("Failed to get services health", error=str(e))
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Failed to get services health"
                )
        
        @self.app.get("/health/metrics")
        async def get_system_metrics():
            """Get system metrics"""
            try:
                # For now, return basic system metrics
                # In production, this should integrate with actual system monitoring
                import psutil
                
                metrics = [
                    {
                        "id": "1",
                        "name": "CPU Usage",
                        "value": psutil.cpu_percent(interval=1),
                        "unit": "%",
                        "status": "healthy" if psutil.cpu_percent() < 80 else "warning",
                        "trend": "stable",
                        "lastUpdated": datetime.utcnow().isoformat()
                    },
                    {
                        "id": "2", 
                        "name": "Memory Usage",
                        "value": psutil.virtual_memory().percent,
                        "unit": "%",
                        "status": "healthy" if psutil.virtual_memory().percent < 80 else "warning",
                        "trend": "stable",
                        "lastUpdated": datetime.utcnow().isoformat()
                    },
                    {
                        "id": "3",
                        "name": "Disk Usage", 
                        "value": psutil.disk_usage('/').percent,
                        "unit": "%",
                        "status": "healthy" if psutil.disk_usage('/').percent < 80 else "warning",
                        "trend": "stable",
                        "lastUpdated": datetime.utcnow().isoformat()
                    }
                ]
                
                return {"metrics": metrics}
            except Exception as e:
                self.logger.error("Failed to get system metrics", error=str(e))
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Failed to get system metrics"
                )
        
        @self.app.get("/health/alerts")
        async def get_health_alerts():
            """Get health alerts"""
            try:
                results = await self.health_monitor.check_all()
                
                alerts = []
                for name, result in results.items():
                    if result.status.value != "healthy":
                        alert = {
                            "id": str(hash(f"{name}_{result.timestamp}") % 10000),
                            "severity": "error" if result.status.value == "unhealthy" else "warning",
                            "title": f"{name} Service Issue",
                            "message": result.error_message or f"{name} is {result.status.value}",
                            "timestamp": result.timestamp.isoformat(),
                            "acknowledged": False,
                            "source": "Health Monitor"
                        }
                        alerts.append(alert)
                
                return {"alerts": alerts}
            except Exception as e:
                self.logger.error("Failed to get health alerts", error=str(e))
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Failed to get health alerts"
                )

    def _get_service_type(self, service_name: str) -> str:
        """Map service name to service type"""
        if "Database" in service_name or "PostgreSQL" in service_name:
            return "database"
        elif "Cache" in service_name or "Redis" in service_name:
            return "cache"
        elif "Gateway" in service_name or "Kong" in service_name:
            return "api"
        elif "Service" in service_name:
            return "api"
        elif "Brain" in service_name or "AI" in service_name:
            return "worker"
        else:
            return "api"
    
    def _get_service_url(self, service_name: str) -> str:
        """Get service URL for display - using Docker DNS names and internal ports"""
        
        if "PostgreSQL" in service_name:
            return "postgresql://opsconductor:opsconductor_secure_2024@postgres:5432/opsconductor"
        elif "Redis" in service_name:
            return "redis://redis:6379"
        elif "Kong" in service_name:
            return "http://kong:8001"  # Kong admin API port
        elif "Keycloak" in service_name:
            return "http://keycloak:8080"  # Keycloak internal port
        elif "Identity" in service_name:
            return "http://identity-service:3001"
        elif "Asset" in service_name:
            return "http://asset-service:3002"
        elif "Automation" in service_name:
            return "http://automation-service:3003"
        elif "Communication" in service_name:
            return "http://communication-service:3004"
        elif "AI Brain" in service_name:
            return "http://ai-brain:3005"
        elif "Network" in service_name:
            return "http://network-analyzer-service:3006"
        elif "Ollama" in service_name:
            return "http://ollama:11434"
        else:
            return ""

    async def _test_slack(self, config: dict, message: str) -> dict:
        """Test Slack webhook configuration"""
        import aiohttp
        
        webhook_url = config.get('webhook_url')
        if not webhook_url:
            return {"success": False, "message": "Webhook URL is required"}
        
        payload = {
            "text": message,
            "username": config.get('username', 'OpsConductor'),
            "icon_emoji": config.get('icon_emoji', ':robot_face:')
        }
        
        if config.get('channel'):
            payload['channel'] = config['channel']
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(webhook_url, json=payload) as response:
                    if response.status == 200:
                        return {"success": True, "message": "Slack test message sent successfully"}
                    else:
                        error_text = await response.text()
                        return {"success": False, "message": f"Slack webhook failed: {error_text}"}
        except Exception as e:
            return {"success": False, "message": f"Failed to send Slack message: {str(e)}"}

    async def _test_teams(self, config: dict, message: str) -> dict:
        """Test Microsoft Teams webhook configuration"""
        import aiohttp
        
        webhook_url = config.get('webhook_url')
        if not webhook_url:
            return {"success": False, "message": "Webhook URL is required"}
        
        payload = {
            "@type": "MessageCard",
            "@context": "http://schema.org/extensions",
            "themeColor": config.get('theme_color', '0078D4'),
            "title": config.get('title', 'OpsConductor Notification'),
            "text": message
        }
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(webhook_url, json=payload) as response:
                    if response.status == 200:
                        return {"success": True, "message": "Teams test message sent successfully"}
                    else:
                        error_text = await response.text()
                        return {"success": False, "message": f"Teams webhook failed: {error_text}"}
        except Exception as e:
            return {"success": False, "message": f"Failed to send Teams message: {str(e)}"}

    async def _test_discord(self, config: dict, message: str) -> dict:
        """Test Discord webhook configuration"""
        import aiohttp
        
        webhook_url = config.get('webhook_url')
        if not webhook_url:
            return {"success": False, "message": "Webhook URL is required"}
        
        payload = {
            "content": message,
            "username": config.get('username', 'OpsConductor')
        }
        
        if config.get('avatar_url'):
            payload['avatar_url'] = config['avatar_url']
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(webhook_url, json=payload) as response:
                    if response.status in [200, 204]:
                        return {"success": True, "message": "Discord test message sent successfully"}
                    else:
                        error_text = await response.text()
                        return {"success": False, "message": f"Discord webhook failed: {error_text}"}
        except Exception as e:
            return {"success": False, "message": f"Failed to send Discord message: {str(e)}"}

    async def _test_webhook(self, config: dict, message: str) -> dict:
        """Test generic webhook configuration"""
        import aiohttp
        from datetime import datetime
        
        url = config.get('url')
        if not url:
            return {"success": False, "message": "Webhook URL is required"}
        
        method = config.get('method', 'POST').upper()
        headers = config.get('headers', {}).copy()
        auth_type = config.get('auth_type', 'none')
        auth_config = config.get('auth_config', {})
        content_type = config.get('content_type', 'application/json')
        payload_template = config.get('payload_template', '{"message": "{{message}}", "timestamp": "{{timestamp}}"}')
        
        # Set content type header
        headers['Content-Type'] = content_type
        
        # Handle authentication
        if auth_type == 'basic' and auth_config.get('username') and auth_config.get('password'):
            import base64
            credentials = base64.b64encode(f"{auth_config['username']}:{auth_config['password']}".encode()).decode()
            headers['Authorization'] = f'Basic {credentials}'
        elif auth_type == 'bearer' and auth_config.get('token'):
            headers['Authorization'] = f'Bearer {auth_config["token"]}'
        elif auth_type == 'api_key' and auth_config.get('api_key') and auth_config.get('api_key_header'):
            headers[auth_config['api_key_header']] = auth_config['api_key']
        
        # Prepare payload
        try:
            # Replace template variables
            payload_str = payload_template.replace('{{message}}', message)
            payload_str = payload_str.replace('{{timestamp}}', datetime.utcnow().isoformat())
            payload_str = payload_str.replace('{{subject}}', 'Test Message')
            
            if content_type == 'application/json':
                import json
                payload = json.loads(payload_str)
            else:
                payload = payload_str
        except Exception as e:
            return {"success": False, "message": f"Invalid payload template: {str(e)}"}
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.request(method, url, json=payload if content_type == 'application/json' else None, 
                                         data=payload if content_type != 'application/json' else None, 
                                         headers=headers) as response:
                    if 200 <= response.status < 300:
                        return {"success": True, "message": f"Webhook test successful (HTTP {response.status})"}
                    else:
                        error_text = await response.text()
                        return {"success": False, "message": f"Webhook failed (HTTP {response.status}): {error_text}"}
        except Exception as e:
            return {"success": False, "message": f"Failed to send webhook request: {str(e)}"}
    
    def _setup_execution_routes(self):
        """Setup execution routes for AI-pipeline integration"""
        
        @self.app.post("/execute-plan")
        async def execute_plan_from_pipeline(request: Dict[str, Any]):
            """
            Execute a communication plan from AI-pipeline
            
            Handles communication-specific tools:
            - sendmail: Send email messages
            - slack_cli: Send Slack notifications
            - teams_cli: Send Microsoft Teams messages
            - webhook_sender: Send webhook notifications
            
            Args:
                request: {
                    "execution_id": str,
                    "plan": dict,
                    "tenant_id": str,
                    "actor_id": int
                }
            
            Returns:
                Execution result with status, output, and timing
            """
            try:
                self.logger.info(f"Received communication execution request from ai-pipeline: {request.get('execution_id')}")
                
                execution_id = request.get("execution_id")
                plan = request.get("plan", {})
                steps = plan.get("steps", [])
                
                if not steps:
                    return {
                        "execution_id": execution_id,
                        "status": "failed",
                        "result": {},
                        "step_results": [],
                        "completed_at": datetime.utcnow().isoformat(),
                        "error_message": "No steps in plan"
                    }
                
                # Execute each communication step
                step_results = []
                overall_success = True
                
                for idx, step in enumerate(steps):
                    tool = step.get("tool", "unknown")
                    inputs = step.get("inputs", {})
                    
                    self.logger.info(f"Executing communication step {idx + 1}/{len(steps)}: {tool}")
                    
                    try:
                        # Route to appropriate communication handler
                        if tool == "sendmail":
                            result = await self._execute_sendmail_tool(inputs)
                        elif tool == "slack_cli":
                            result = await self._execute_slack_tool(inputs)
                        elif tool == "teams_cli":
                            result = await self._execute_teams_tool(inputs)
                        elif tool == "webhook_sender":
                            result = await self._execute_webhook_tool(inputs)
                        else:
                            result = {
                                "success": False,
                                "message": f"Unknown communication tool: {tool}"
                            }
                        
                        step_results.append({
                            "step_index": idx,
                            "tool": tool,
                            "status": "completed" if result.get("success") else "failed",
                            "output": result,
                            "completed_at": datetime.utcnow().isoformat()
                        })
                        
                        if not result.get("success"):
                            overall_success = False
                    
                    except Exception as e:
                        self.logger.error(f"Communication step {idx + 1} failed: {e}", exc_info=True)
                        step_results.append({
                            "step_index": idx,
                            "tool": tool,
                            "status": "failed",
                            "error": str(e),
                            "completed_at": datetime.utcnow().isoformat()
                        })
                        overall_success = False
                
                # Return result to ai-pipeline
                return {
                    "execution_id": execution_id,
                    "status": "completed" if overall_success else "failed",
                    "result": {
                        "total_steps": len(steps),
                        "successful_steps": sum(1 for r in step_results if r.get("status") == "completed"),
                        "failed_steps": sum(1 for r in step_results if r.get("status") == "failed")
                    },
                    "step_results": step_results,
                    "completed_at": datetime.utcnow().isoformat(),
                    "error_message": None if overall_success else "One or more communication steps failed"
                }
            
            except Exception as e:
                self.logger.error(f"Communication plan execution failed: {e}", exc_info=True)
                raise HTTPException(status_code=500, detail=str(e))
    
    async def _execute_sendmail_tool(self, inputs: dict) -> dict:
        """Execute sendmail command - Send email via SMTP"""
        import smtplib
        from email.mime.text import MIMEText
        from email.mime.multipart import MIMEMultipart
        
        try:
            # Extract parameters
            to_address = inputs.get("to") or inputs.get("recipient")
            subject = inputs.get("subject", "Notification from OpsConductor")
            body = inputs.get("body") or inputs.get("message", "")
            from_address = inputs.get("from", os.getenv("SMTP_FROM", "noreply@opsconductor.local"))
            
            # Validate required fields
            if not to_address:
                return {
                    "success": False,
                    "message": "Missing required parameter: 'to' or 'recipient'",
                    "error": "Missing recipient address"
                }
            
            # Get SMTP configuration from environment
            smtp_host = os.getenv("SMTP_HOST", "localhost")
            smtp_port = int(os.getenv("SMTP_PORT", "25"))
            smtp_user = os.getenv("SMTP_USER")
            smtp_password = os.getenv("SMTP_PASSWORD")
            smtp_use_tls = os.getenv("SMTP_USE_TLS", "false").lower() == "true"
            
            # Create message
            msg = MIMEMultipart()
            msg['From'] = from_address
            msg['To'] = to_address
            msg['Subject'] = subject
            msg.attach(MIMEText(body, 'plain'))
            
            # Send email
            self.logger.info(f"Sending email to {to_address} via {smtp_host}:{smtp_port}")
            
            try:
                if smtp_use_tls:
                    server = smtplib.SMTP(smtp_host, smtp_port, timeout=10)
                    server.starttls()
                else:
                    server = smtplib.SMTP(smtp_host, smtp_port, timeout=10)
                
                if smtp_user and smtp_password:
                    server.login(smtp_user, smtp_password)
                
                server.send_message(msg)
                server.quit()
                
                self.logger.info(f"Email sent successfully to {to_address}")
                return {
                    "success": True,
                    "message": "Email sent successfully",
                    "details": {
                        "to": to_address,
                        "subject": subject,
                        "from": from_address,
                        "smtp_host": smtp_host
                    }
                }
            
            except smtplib.SMTPException as e:
                self.logger.error(f"SMTP error sending email: {e}")
                return {
                    "success": False,
                    "message": f"SMTP error: {str(e)}",
                    "error": str(e)
                }
            except Exception as e:
                self.logger.error(f"Error sending email: {e}")
                return {
                    "success": False,
                    "message": f"Failed to send email: {str(e)}",
                    "error": str(e)
                }
        
        except Exception as e:
            self.logger.error(f"Error in sendmail tool: {e}", exc_info=True)
            return {
                "success": False,
                "message": f"Error executing sendmail: {str(e)}",
                "error": str(e)
            }
    
    async def _execute_slack_tool(self, inputs: dict) -> dict:
        """Execute Slack notification via webhook"""
        import httpx
        
        try:
            # Extract parameters
            webhook_url = inputs.get("webhook_url") or os.getenv("SLACK_WEBHOOK_URL")
            message = inputs.get("message") or inputs.get("text", "")
            channel = inputs.get("channel")
            username = inputs.get("username", "OpsConductor")
            icon_emoji = inputs.get("icon_emoji", ":robot_face:")
            
            # Validate required fields
            if not webhook_url:
                return {
                    "success": False,
                    "message": "Missing required parameter: 'webhook_url' or SLACK_WEBHOOK_URL env var",
                    "error": "Missing webhook URL"
                }
            
            if not message:
                return {
                    "success": False,
                    "message": "Missing required parameter: 'message' or 'text'",
                    "error": "Missing message content"
                }
            
            # Build Slack message payload
            payload = {
                "text": message,
                "username": username,
                "icon_emoji": icon_emoji
            }
            
            if channel:
                payload["channel"] = channel
            
            # Add attachments if provided
            if "attachments" in inputs:
                payload["attachments"] = inputs["attachments"]
            
            # Add blocks if provided (for rich formatting)
            if "blocks" in inputs:
                payload["blocks"] = inputs["blocks"]
            
            # Send to Slack
            self.logger.info(f"Sending Slack message to webhook: {webhook_url[:50]}...")
            
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.post(
                    webhook_url,
                    json=payload,
                    headers={"Content-Type": "application/json"}
                )
                
                if response.status_code == 200:
                    self.logger.info("Slack message sent successfully")
                    return {
                        "success": True,
                        "message": "Slack message sent successfully",
                        "details": {
                            "channel": channel,
                            "username": username,
                            "message_length": len(message)
                        }
                    }
                else:
                    self.logger.error(f"Slack API error: {response.status_code} - {response.text}")
                    return {
                        "success": False,
                        "message": f"Slack API error: {response.status_code}",
                        "error": response.text
                    }
        
        except httpx.TimeoutException:
            self.logger.error("Slack webhook request timed out")
            return {
                "success": False,
                "message": "Slack webhook request timed out",
                "error": "Request timeout"
            }
        except Exception as e:
            self.logger.error(f"Error in Slack tool: {e}", exc_info=True)
            return {
                "success": False,
                "message": f"Error executing Slack notification: {str(e)}",
                "error": str(e)
            }
    
    async def _execute_teams_tool(self, inputs: dict) -> dict:
        """Execute Microsoft Teams notification via webhook"""
        import httpx
        
        try:
            # Extract parameters
            webhook_url = inputs.get("webhook_url") or os.getenv("TEAMS_WEBHOOK_URL")
            title = inputs.get("title", "Notification from OpsConductor")
            message = inputs.get("message") or inputs.get("text", "")
            theme_color = inputs.get("theme_color", "0078D4")  # Microsoft blue
            
            # Validate required fields
            if not webhook_url:
                return {
                    "success": False,
                    "message": "Missing required parameter: 'webhook_url' or TEAMS_WEBHOOK_URL env var",
                    "error": "Missing webhook URL"
                }
            
            if not message:
                return {
                    "success": False,
                    "message": "Missing required parameter: 'message' or 'text'",
                    "error": "Missing message content"
                }
            
            # Build Teams message card payload
            payload = {
                "@type": "MessageCard",
                "@context": "https://schema.org/extensions",
                "summary": title,
                "themeColor": theme_color,
                "title": title,
                "text": message
            }
            
            # Add sections if provided
            if "sections" in inputs:
                payload["sections"] = inputs["sections"]
            
            # Add potential actions if provided
            if "actions" in inputs:
                payload["potentialAction"] = inputs["actions"]
            
            # Send to Teams
            self.logger.info(f"Sending Teams message to webhook: {webhook_url[:50]}...")
            
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.post(
                    webhook_url,
                    json=payload,
                    headers={"Content-Type": "application/json"}
                )
                
                if response.status_code == 200:
                    self.logger.info("Teams message sent successfully")
                    return {
                        "success": True,
                        "message": "Teams message sent successfully",
                        "details": {
                            "title": title,
                            "message_length": len(message)
                        }
                    }
                else:
                    self.logger.error(f"Teams API error: {response.status_code} - {response.text}")
                    return {
                        "success": False,
                        "message": f"Teams API error: {response.status_code}",
                        "error": response.text
                    }
        
        except httpx.TimeoutException:
            self.logger.error("Teams webhook request timed out")
            return {
                "success": False,
                "message": "Teams webhook request timed out",
                "error": "Request timeout"
            }
        except Exception as e:
            self.logger.error(f"Error in Teams tool: {e}", exc_info=True)
            return {
                "success": False,
                "message": f"Error executing Teams notification: {str(e)}",
                "error": str(e)
            }
    
    async def _execute_webhook_tool(self, inputs: dict) -> dict:
        """Execute generic webhook - Send HTTP request to any URL"""
        import httpx
        
        try:
            # Extract parameters
            url = inputs.get("url") or inputs.get("webhook_url")
            method = inputs.get("method", "POST").upper()
            headers = inputs.get("headers", {})
            payload = inputs.get("payload") or inputs.get("data") or inputs.get("body")
            timeout = inputs.get("timeout", 10.0)
            
            # Validate required fields
            if not url:
                return {
                    "success": False,
                    "message": "Missing required parameter: 'url' or 'webhook_url'",
                    "error": "Missing URL"
                }
            
            # Ensure Content-Type header is set
            if "Content-Type" not in headers and "content-type" not in headers:
                headers["Content-Type"] = "application/json"
            
            # Send webhook request
            self.logger.info(f"Sending {method} webhook to: {url}")
            
            async with httpx.AsyncClient(timeout=timeout) as client:
                if method == "GET":
                    response = await client.get(url, headers=headers)
                elif method == "POST":
                    response = await client.post(url, json=payload, headers=headers)
                elif method == "PUT":
                    response = await client.put(url, json=payload, headers=headers)
                elif method == "PATCH":
                    response = await client.patch(url, json=payload, headers=headers)
                elif method == "DELETE":
                    response = await client.delete(url, headers=headers)
                else:
                    return {
                        "success": False,
                        "message": f"Unsupported HTTP method: {method}",
                        "error": f"Method {method} not supported"
                    }
                
                # Check response
                success = 200 <= response.status_code < 300
                
                if success:
                    self.logger.info(f"Webhook sent successfully: {response.status_code}")
                    return {
                        "success": True,
                        "message": f"Webhook sent successfully",
                        "details": {
                            "url": url,
                            "method": method,
                            "status_code": response.status_code,
                            "response": response.text[:500] if response.text else None
                        }
                    }
                else:
                    self.logger.warning(f"Webhook returned non-success status: {response.status_code}")
                    return {
                        "success": False,
                        "message": f"Webhook returned status {response.status_code}",
                        "error": response.text[:500] if response.text else f"HTTP {response.status_code}",
                        "status_code": response.status_code
                    }
        
        except httpx.TimeoutException:
            self.logger.error(f"Webhook request timed out: {url}")
            return {
                "success": False,
                "message": "Webhook request timed out",
                "error": "Request timeout"
            }
        except httpx.RequestError as e:
            self.logger.error(f"Webhook request error: {e}")
            return {
                "success": False,
                "message": f"Webhook request error: {str(e)}",
                "error": str(e)
            }
        except Exception as e:
            self.logger.error(f"Error in webhook tool: {e}", exc_info=True)
            return {
                "success": False,
                "message": f"Error executing webhook: {str(e)}",
                "error": str(e)
            }


if __name__ == "__main__":
    service = CommunicationService()
    service.run()
