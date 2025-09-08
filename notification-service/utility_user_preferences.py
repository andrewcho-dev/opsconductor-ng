"""
User preferences utility module
Handles user notification preferences management
"""

from typing import Dict, Any, Optional
from datetime import datetime, timezone
import logging

# Import database utilities - will be set from main module
get_db_cursor = None

logger = logging.getLogger(__name__)

def set_db_cursor_func(cursor_func):
    """Set database cursor function from main module"""
    global get_db_cursor
    get_db_cursor = cursor_func

async def get_user_preferences(user_id: int) -> Optional[Dict[str, Any]]:
    """Get user notification preferences"""
    try:
        with get_db_cursor(commit=False) as cursor:
            cursor.execute("""
                SELECT * FROM user_notification_preferences WHERE user_id = %s
            """, (user_id,))
            
            return cursor.fetchone()
        
    except Exception as e:
        logger.error(f"Error getting user preferences for user {user_id}: {e}")
        return None

async def update_user_preferences(user_id: int, preferences: Dict[str, Any]) -> Dict[str, Any]:
    """Update user notification preferences"""
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
                user_id, preferences.get('email_enabled', True), preferences.get('email_address'),
                preferences.get('webhook_enabled', False), preferences.get('webhook_url'),
                preferences.get('slack_enabled', False), preferences.get('slack_webhook_url'), preferences.get('slack_channel'),
                preferences.get('teams_enabled', False), preferences.get('teams_webhook_url'),
                preferences.get('notify_on_success', True), preferences.get('notify_on_failure', True), preferences.get('notify_on_start', False),
                preferences.get('quiet_hours_enabled', False), preferences.get('quiet_hours_start'), preferences.get('quiet_hours_end'),
                preferences.get('quiet_hours_timezone', 'America/Los_Angeles'), datetime.now(timezone.utc)
            ))
            
            return cursor.fetchone()
        
    except Exception as e:
        logger.error(f"Error updating user preferences for user {user_id}: {e}")
        raise

def get_user_notification_preferences(user_id: int) -> Optional[Dict[str, Any]]:
    """Get user notification preferences (synchronous version for compatibility)"""
    try:
        with get_db_cursor(commit=False) as cursor:
            cursor.execute("""
                SELECT unp.*, u.email as user_email 
                FROM user_notification_preferences unp
                LEFT JOIN users u ON unp.user_id = u.id
                WHERE unp.user_id = %s
            """, (user_id,))
            
            return cursor.fetchone()
        
    except Exception as e:
        logger.error(f"Error getting user notification preferences for user {user_id}: {e}")
        return None

def should_notify(preferences: Dict[str, Any], event_type: str) -> bool:
    """Check if user should be notified based on preferences and event type"""
    try:
        if event_type == "job_started":
            return preferences.get('notify_on_start', False)
        elif event_type == "job_succeeded":
            return preferences.get('notify_on_success', True)
        elif event_type == "job_failed":
            return preferences.get('notify_on_failure', True)
        else:
            # Default to notify for unknown event types
            return True
            
    except Exception as e:
        logger.error(f"Error checking notification preferences: {e}")
        return True  # Default to notify on error