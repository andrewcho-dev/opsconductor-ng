"""
Email notification utility module
Handles all email-related notification functionality
"""

import smtplib
import json
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from typing import Dict, Any, Optional
import logging

from utility_template_renderer import render_template

logger = logging.getLogger(__name__)

# Global SMTP configuration - will be imported from main
SMTP_CONFIG = {}

def set_smtp_config(config: Dict[str, Any]) -> None:
    """Set SMTP configuration from main module"""
    global SMTP_CONFIG
    SMTP_CONFIG.update(config)

async def send_email_notification(notification_id: int, dest: str, payload: Dict[str, Any], template: Optional[Dict[str, Any]] = None) -> bool:
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

async def test_smtp_connection(smtp_config: Dict[str, Any], test_email: str) -> tuple[bool, str]:
    """Test SMTP connection and send test email"""
    try:
        # Create test message
        msg = MIMEMultipart("alternative")
        msg["Subject"] = "OpsConductor SMTP Test"
        msg["From"] = f"{smtp_config['from_name']} <{smtp_config['from_email']}>"
        msg["To"] = test_email
        
        html_content = """
        <html>
        <body>
            <h2>SMTP Configuration Test</h2>
            <p>This is a test email to verify your SMTP configuration is working correctly.</p>
            <p>If you received this email, your SMTP settings are configured properly.</p>
        </body>
        </html>
        """
        
        html_part = MIMEText(html_content, "html")
        msg.attach(html_part)
        
        # Test connection and send
        with smtplib.SMTP(smtp_config["host"], smtp_config["port"]) as server:
            if smtp_config["use_tls"]:
                server.starttls()
            
            if smtp_config["username"] and smtp_config["password"]:
                server.login(smtp_config["username"], smtp_config["password"])
            
            server.send_message(msg)
        
        return True, "Test email sent successfully"
        
    except Exception as e:
        return False, f"SMTP test failed: {str(e)}"