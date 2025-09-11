#!/usr/bin/env python3
"""
OpsConductor Communication Service
Handles notifications and external integrations
Consolidates: notification-service
"""

import sys
import os
import json
from typing import List, Optional
from fastapi import Query, HTTPException, status
from pydantic import BaseModel
from datetime import datetime
sys.path.append('/app/shared')
from base_service import BaseService

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
        self._setup_routes()
    
    async def on_startup(self):
        """Set the database schema to communication"""
        os.environ["DB_SCHEMA"] = "communication"
        await super().on_startup()
    
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
                        import json
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
                    total = await conn.fetchval("SELECT COUNT(*) FROM notification_templates")
                    
                    # Get templates with pagination
                    rows = await conn.fetch("""
                        SELECT id, name, template_type, subject_template, body_template,
                               metadata, is_active, created_by, created_at, updated_at
                        FROM notification_templates 
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
                        import json
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
                        import json
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

if __name__ == "__main__":
    service = CommunicationService()
    service.run()
