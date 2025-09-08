"""
Notification processing utility module
Handles notification creation, processing, and database operations
"""

import json
from typing import Dict, Any, Optional, List
from datetime import datetime, timezone
import logging

# Import utilities
from utility_email_sender import send_email_notification
from utility_webhook_sender import send_slack_notification, send_teams_notification, send_webhook_notification
from utility_user_preferences import get_user_notification_preferences, should_notify

# Database utilities - will be set from main module
get_db_cursor = None

logger = logging.getLogger(__name__)

def set_db_cursor_func(cursor_func):
    """Set database cursor function from main module"""
    global get_db_cursor
    get_db_cursor = cursor_func

def get_notification_template(channel: str, event_type: str) -> Optional[Dict[str, Any]]:
    """Get notification template for channel and event type"""
    try:
        with get_db_cursor(commit=False) as cursor:
            cursor.execute("""
                SELECT * FROM notification_templates 
                WHERE channel = %s AND event_type = %s AND is_active = true
                ORDER BY created_at DESC LIMIT 1
            """, (channel, event_type))
            
            return cursor.fetchone()
        
    except Exception as e:
        logger.error(f"Error getting notification template for {channel}/{event_type}: {e}")
        return None

async def process_notification(notification_id: int, channel: str, dest: str, payload: Dict[str, Any], template_id: Optional[int] = None) -> bool:
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

async def create_notifications_for_job_run(job_run_id: int, event_type: str, payload: Dict[str, Any], user_id: Optional[int] = None) -> List[int]:
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

async def get_pending_notifications(limit: int = 50) -> List[Dict[str, Any]]:
    """Get pending notifications for processing"""
    try:
        with get_db_cursor(commit=False) as cursor:
            cursor.execute("""
                SELECT id, job_run_id, user_id, channel, dest, payload, template_id, retries
                FROM notifications 
                WHERE status = 'pending' AND retries < 3
                ORDER BY id ASC 
                LIMIT %s
            """, (limit,))
            
            return cursor.fetchall()
        
    except Exception as e:
        logger.error(f"Error getting pending notifications: {e}")
        return []

async def get_notification_stats() -> Dict[str, int]:
    """Get notification statistics"""
    try:
        with get_db_cursor(commit=False) as cursor:
            # Get pending count
            cursor.execute("SELECT COUNT(*) as count FROM notifications WHERE status = 'pending'")
            pending_count = cursor.fetchone()["count"]
            
            # Get failed count
            cursor.execute("SELECT COUNT(*) as count FROM notifications WHERE status = 'failed'")
            failed_count = cursor.fetchone()["count"]
            
            # Get sent count (last 24 hours)
            cursor.execute("""
                SELECT COUNT(*) as count FROM notifications 
                WHERE status = 'sent' AND sent_at > NOW() - INTERVAL '24 hours'
            """)
            sent_24h_count = cursor.fetchone()["count"]
            
            return {
                "pending": pending_count,
                "failed": failed_count,
                "sent_24h": sent_24h_count
            }
        
    except Exception as e:
        logger.error(f"Error getting notification stats: {e}")
        return {"pending": 0, "failed": 0, "sent_24h": 0}