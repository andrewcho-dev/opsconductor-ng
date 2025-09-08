"""
Webhook notification utility module
Handles Slack, Teams, and generic webhook notifications
"""

import httpx
import json
from typing import Dict, Any, Optional
import logging

from utility_template_renderer import render_template

logger = logging.getLogger(__name__)

async def send_slack_notification(notification_id: int, webhook_url: str, payload: Dict[str, Any], template: Optional[Dict[str, Any]] = None) -> bool:
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

async def send_teams_notification(notification_id: int, webhook_url: str, payload: Dict[str, Any], template: Optional[Dict[str, Any]] = None) -> bool:
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

async def send_webhook_notification(notification_id: int, webhook_url: str, payload: Dict[str, Any], template: Optional[Dict[str, Any]] = None) -> bool:
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

async def test_webhook_connection(webhook_url: str, webhook_type: str = "generic") -> tuple[bool, str]:
    """Test webhook connection"""
    try:
        # Create test payload based on webhook type
        if webhook_type == "slack":
            test_payload = {
                "text": "🧪 OpsConductor Webhook Test",
                "blocks": [
                    {
                        "type": "section",
                        "text": {
                            "type": "mrkdwn",
                            "text": "*Webhook Test*\nThis is a test message to verify your Slack webhook is working correctly."
                        }
                    }
                ]
            }
        elif webhook_type == "teams":
            test_payload = {
                "@type": "MessageCard",
                "@context": "http://schema.org/extensions",
                "themeColor": "0078D4",
                "summary": "OpsConductor Webhook Test",
                "sections": [{
                    "activityTitle": "Webhook Test",
                    "activitySubtitle": "OpsConductor",
                    "text": "This is a test message to verify your Teams webhook is working correctly."
                }]
            }
        else:
            test_payload = {
                "message": "OpsConductor webhook test",
                "timestamp": "2024-01-01T00:00:00Z",
                "test": True
            }
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                webhook_url,
                json=test_payload,
                headers={"Content-Type": "application/json"}
            )
            
            if response.status_code < 400:
                return True, f"Webhook test successful (HTTP {response.status_code})"
            else:
                return False, f"Webhook test failed with HTTP {response.status_code}: {response.text}"
                
    except Exception as e:
        return False, f"Webhook test failed: {str(e)}"