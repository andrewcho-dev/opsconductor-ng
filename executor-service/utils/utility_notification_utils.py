"""
Notification Utilities
Handles job completion notifications with formatting and delivery
"""

import json

from typing import Dict, Any, Optional, List
from datetime import datetime
import sys
import os

# Add shared module to path
sys.path.append('/home/opsconductor')
from shared.logging import get_logger
from shared.errors import ServiceCommunicationError, ValidationError
import shared.utility_service_clients as service_clients_utility

logger = get_logger("executor.notifications")

class NotificationUtils:
    """Handles job completion notifications"""
    
    def __init__(self, notification_service_url: str = None):
        self.notification_service_url = notification_service_url or os.getenv(
            "NOTIFICATION_SERVICE_URL", "http://notification-service:3007"
        )
    
    def send_job_completion_notification(self, job_run_id: int, status: str, cursor) -> None:
        """
        Send notification for job completion
        
        Args:
            job_run_id: ID of the completed job run
            status: Final status of the job run
            cursor: Database cursor for queries
        """
        try:
            # Get job run details
            job_info = self._get_job_run_details(job_run_id, cursor)
            if not job_info or not job_info.get('user_email'):
                logger.info(f"No email address found for job run {job_run_id}, skipping notification")
                return
            
            # Prepare notification content
            notification_data = self._prepare_notification_content(job_info, status, cursor)
            
            # Send notification
            self._send_notification_request(notification_data)
            
            # Store notification record
            self._store_notification_record(job_run_id, notification_data, cursor)
            
            logger.info(f"Job completion notification sent for run {job_run_id}")
            
        except Exception as e:
            logger.error(f"Failed to send job completion notification for run {job_run_id}: {e}")
    
    def _get_job_run_details(self, job_run_id: int, cursor) -> Optional[Dict[str, Any]]:
        """Get detailed job run information"""
        cursor.execute("""
            SELECT 
                jr.id as run_id,
                jr.job_id,
                jr.status,
                jr.queued_at,
                jr.started_at,
                jr.finished_at,
                jr.requested_by,
                j.name as job_name,
                j.description as job_description,
                u.email as user_email,
                u.username,
                COUNT(jrs.id) as total_steps,
                COUNT(CASE WHEN jrs.status = 'succeeded' THEN 1 END) as succeeded_steps,
                COUNT(CASE WHEN jrs.status = 'failed' THEN 1 END) as failed_steps,
                COUNT(CASE WHEN jrs.status = 'skipped' THEN 1 END) as skipped_steps
            FROM job_runs jr
            JOIN jobs j ON jr.job_id = j.id
            LEFT JOIN users u ON jr.requested_by = u.id
            LEFT JOIN job_run_steps jrs ON jr.id = jrs.job_run_id
            WHERE jr.id = %s
            GROUP BY jr.id, j.name, j.description, u.email, u.username
        """, (job_run_id,))
        
        return cursor.fetchone()
    
    def _prepare_notification_content(self, job_info: Dict[str, Any], status: str, cursor) -> Dict[str, Any]:
        """Prepare notification content based on job status"""
        # Calculate execution duration
        duration = self._calculate_duration(job_info)
        
        # Get step summary
        step_summary = self._get_step_summary(job_info)
        
        # Prepare base notification data
        notification_data = {
            'type': 'job_completion',
            'recipients': [job_info['user_email']],
            'job_run_id': job_info['run_id'],
            'job_id': job_info['job_id'],
            'job_name': job_info['job_name'],
            'status': status,
            'duration': duration,
            'step_summary': step_summary,
            'requested_by': job_info['username'],
            'finished_at': job_info['finished_at'].isoformat() if job_info['finished_at'] else None
        }
        
        # Add status-specific content
        if status == 'succeeded':
            notification_data.update(self._prepare_success_content(job_info))
        elif status == 'failed':
            notification_data.update(self._prepare_failure_content(job_info, cursor))
        elif status == 'cancelled':
            notification_data.update(self._prepare_cancellation_content(job_info))
        
        return notification_data
    
    def _calculate_duration(self, job_info: Dict[str, Any]) -> str:
        """Calculate job execution duration"""
        if job_info['started_at'] and job_info['finished_at']:
            delta = job_info['finished_at'] - job_info['started_at']
            # Format duration nicely
            total_seconds = int(delta.total_seconds())
            hours, remainder = divmod(total_seconds, 3600)
            minutes, seconds = divmod(remainder, 60)
            
            if hours > 0:
                return f"{hours}h {minutes}m {seconds}s"
            elif minutes > 0:
                return f"{minutes}m {seconds}s"
            else:
                return f"{seconds}s"
        
        return "Unknown"
    
    def _get_step_summary(self, job_info: Dict[str, Any]) -> Dict[str, int]:
        """Get summary of step execution results"""
        return {
            'total': job_info['total_steps'] or 0,
            'succeeded': job_info['succeeded_steps'] or 0,
            'failed': job_info['failed_steps'] or 0,
            'skipped': job_info['skipped_steps'] or 0
        }
    
    def _prepare_success_content(self, job_info: Dict[str, Any]) -> Dict[str, Any]:
        """Prepare content for successful job completion"""
        return {
            'subject': f"✅ Job '{job_info['job_name']}' completed successfully",
            'template': 'job_success',
            'priority': 'normal'
        }
    
    def _prepare_failure_content(self, job_info: Dict[str, Any], cursor) -> Dict[str, Any]:
        """Prepare content for failed job completion"""
        # Get error details from failed steps
        error_details = self._get_failure_details(job_info['run_id'], cursor)
        
        return {
            'subject': f"❌ Job '{job_info['job_name']}' failed",
            'template': 'job_failure',
            'priority': 'high',
            'error_details': error_details
        }
    
    def _prepare_cancellation_content(self, job_info: Dict[str, Any]) -> Dict[str, Any]:
        """Prepare content for cancelled job"""
        return {
            'subject': f"⚠️ Job '{job_info['job_name']}' was cancelled",
            'template': 'job_cancelled',
            'priority': 'normal'
        }
    
    def _get_failure_details(self, job_run_id: int, cursor) -> List[Dict[str, Any]]:
        """Get detailed failure information from failed steps"""
        cursor.execute("""
            SELECT 
                idx,
                step_name,
                status,
                stderr,
                stdout,
                started_at,
                finished_at
            FROM job_run_steps 
            WHERE job_run_id = %s AND status = 'failed'
            ORDER BY idx
            LIMIT 5
        """, (job_run_id,))
        
        failed_steps = cursor.fetchall()
        error_details = []
        
        for step in failed_steps:
            error_info = {
                'step_index': step['idx'],
                'step_name': step['step_name'] or f"Step {step['idx']}",
                'error_message': self._extract_error_message(step['stderr'], step['stdout'])
            }
            error_details.append(error_info)
        
        return error_details
    
    def _extract_error_message(self, stderr: str, stdout: str) -> str:
        """Extract meaningful error message from step output"""
        # Prioritize stderr
        if stderr and stderr.strip():
            # Take first few lines of stderr
            lines = stderr.strip().split('\n')
            if len(lines) > 3:
                return '\n'.join(lines[:3]) + '\n...'
            return stderr.strip()
        
        # Fall back to stdout if stderr is empty
        if stdout and stdout.strip():
            lines = stdout.strip().split('\n')
            # Look for error-like patterns in stdout
            error_lines = [line for line in lines if any(keyword in line.lower() 
                          for keyword in ['error', 'failed', 'exception', 'traceback'])]
            
            if error_lines:
                return '\n'.join(error_lines[:3])
            
            # Return last few lines of stdout
            if len(lines) > 3:
                return '\n'.join(lines[-3:])
            return stdout.strip()
        
        return "No error details available"
    
    def _send_notification_request(self, notification_data: Dict[str, Any]) -> None:
        """Send notification request to notification service"""
        try:
            # Use standardized notification client
            notification_client = service_clients_utility.get_notification_client()
            
            # Convert to the expected format for our service client
            import asyncio
            result = asyncio.run(notification_client.send_notification(notification_data))
            
            logger.debug("Notification request sent successfully")
                
        except ValidationError as e:
            logger.error(f"Invalid notification data: {e}")
            raise
        except ServiceCommunicationError as e:
            logger.error(f"Failed to communicate with notification service: {e}")
            raise
        except Exception as e:
            logger.error(f"Failed to send notification request: {e}")
            raise
    
    def _store_notification_record(self, job_run_id: int, notification_data: Dict[str, Any], cursor) -> None:
        """Store notification record in database"""
        try:
            cursor.execute("""
                INSERT INTO job_notifications (
                    job_run_id, 
                    notification_type, 
                    recipients, 
                    subject, 
                    content, 
                    status,
                    created_at
                ) VALUES (%s, %s, %s, %s, %s, %s, %s)
            """, (
                job_run_id,
                notification_data['type'],
                json.dumps(notification_data['recipients']),
                notification_data.get('subject', ''),
                json.dumps(notification_data),
                'sent',
                datetime.utcnow()
            ))
            
            logger.debug(f"Notification record stored for job run {job_run_id}")
            
        except Exception as e:
            logger.error(f"Failed to store notification record: {e}")
            # Don't raise - notification was sent, storage failure is not critical
    
    def send_step_notification(self, step_id: int, notification_type: str, recipients: List[str], 
                              subject: str, content: str, cursor) -> None:
        """
        Send notification for individual step completion
        
        Args:
            step_id: ID of the step
            notification_type: Type of notification
            recipients: List of recipient email addresses
            subject: Notification subject
            content: Notification content
            cursor: Database cursor
        """
        try:
            notification_data = {
                'type': notification_type,
                'recipients': recipients,
                'subject': subject,
                'content': content,
                'step_id': step_id
            }
            
            # Send notification
            self._send_notification_request(notification_data)
            
            # Store record
            cursor.execute("""
                INSERT INTO step_notifications (
                    step_id, 
                    notification_type, 
                    recipients, 
                    subject, 
                    content, 
                    status,
                    created_at
                ) VALUES (%s, %s, %s, %s, %s, %s, %s)
            """, (
                step_id,
                notification_type,
                json.dumps(recipients),
                subject,
                content,
                'sent',
                datetime.utcnow()
            ))
            
            logger.info(f"Step notification sent for step {step_id}")
            
        except Exception as e:
            logger.error(f"Failed to send step notification for step {step_id}: {e}")
    
    def get_notification_preferences(self, user_id: int) -> Dict[str, Any]:
        """
        Get user notification preferences
        
        Args:
            user_id: User ID
            
        Returns:
            Dict containing notification preferences
        """
        try:
            # Use standardized user service client
            user_client = service_clients_utility.get_user_client()
            
            import asyncio
            preferences = asyncio.run(user_client.get_user_preferences(user_id))
            return preferences
                
        except ServiceCommunicationError as e:
            logger.warning(f"Error getting notification preferences: {e}")
            return self._get_default_preferences()
        except Exception as e:
            logger.warning(f"Error getting notification preferences: {e}")
            return self._get_default_preferences()
    
    def _get_default_preferences(self) -> Dict[str, Any]:
        """Get default notification preferences"""
        return {
            'job_completion': True,
            'job_failure': True,
            'job_success': True,
            'step_failure': False,
            'email_enabled': True,
            'teams_enabled': False
        }