"""
Service clients utility module

Provides service-specific client wrappers for common inter-service operations
within the OpsConductor platform. Each client handles authentication, error
handling, and provides typed methods for service-specific operations.

Features:
- Service-specific client classes with typed methods
- Automatic authentication header management
- Standardized error handling and retry logic
- Common operation patterns for each service

Example:
    import utility_service_clients as service_clients_utility
    
    # Initialize with service name
    service_clients_utility.set_service_name("scheduler-service")
    
    # Use service-specific clients
    jobs_client = service_clients_utility.get_jobs_client()
    result = await jobs_client.execute_job(job_id=123, payload={"scheduled": True})
    
    auth_client = service_clients_utility.get_auth_client()
    user = await auth_client.verify_token(token)
"""

import os
import logging
from typing import Dict, Any, Optional, List, Union
from datetime import datetime

from .utils import get_service_client
from .errors import (
    AuthError, ValidationError, NotFoundError, 
    ServiceCommunicationError, DatabaseError
)
from .logging import get_logger
# Service auth utility no longer needed with header-based auth

# Global configuration
CONFIG = {}
_current_service_name = None

logger = get_logger(__name__)

def set_config(config: Dict[str, Any]) -> None:
    """
    Set configuration for service clients
    
    Args:
        config: Configuration dictionary
    """
    global CONFIG
    CONFIG.update(config)
    logger.info("Service clients configuration updated")

def set_service_name(service_name: str) -> None:
    """
    Set the current service name for authentication
    
    Args:
        service_name: Name of the current service making requests
    """
    global _current_service_name
    _current_service_name = service_name
    logger.info(f"Service name set to: {service_name}")

def _get_service_name() -> str:
    """Get the current service name"""
    if not _current_service_name:
        raise ValueError("Service name not set. Call set_service_name() first.")
    return _current_service_name

async def _get_authenticated_headers(additional_headers: Optional[Dict[str, str]] = None) -> Dict[str, str]:
    """Get authentication headers for service calls - now using header-based auth"""
    headers = {
        "Content-Type": "application/json",
        "User-Agent": f"OpsConductor-{_get_service_name()}/1.0.0"
    }
    if additional_headers:
        headers.update(additional_headers)
    return headers

class AuthServiceClient:
    """Client for authentication service operations"""
    
    def __init__(self):
        self.service_url = os.getenv("AUTH_SERVICE_URL", "http://auth-service:3001")
        self.client = get_service_client("auth-service", self.service_url)
    
    async def verify_token(self, token: str) -> Dict[str, Any]:
        """
        Verify a user token
        
        Args:
            token: JWT token to verify
            
        Returns:
            Dict containing user information
            
        Raises:
            AuthError: If token is invalid
            ServiceCommunicationError: If auth service is unavailable
        """
        try:
            headers = {"Authorization": f"Bearer {token}"}
            response = await self.client.get("/verify", headers=headers)
            
            if response.status_code == 401:
                raise AuthError("Invalid or expired token")
            elif response.status_code != 200:
                raise ServiceCommunicationError("auth-service", f"Unexpected status: {response.status_code}")
            
            return response.json()["user"]
            
        except Exception as e:
            if isinstance(e, (AuthError, ServiceCommunicationError)):
                raise
            logger.error(f"Token verification failed: {e}")
            raise ServiceCommunicationError("auth-service", f"Token verification error: {str(e)}")
    
    async def login_service(self, username: str, password: str) -> Dict[str, Any]:
        """
        Login with service credentials
        
        Args:
            username: Service username
            password: Service password
            
        Returns:
            Dict containing access token and user info
        """
        try:
            response = await self.client.post_json("/login", {
                "username": username,
                "password": password
            })
            
            if "access_token" not in response:
                raise AuthError("Invalid credentials")
            
            return response
            
        except Exception as e:
            if isinstance(e, AuthError):
                raise
            logger.error(f"Service login failed: {e}")
            raise ServiceCommunicationError("auth-service", f"Login error: {str(e)}")

class JobsServiceClient:
    """Client for jobs service operations"""
    
    def __init__(self):
        self.service_url = os.getenv("JOBS_SERVICE_URL", "http://jobs-service:3006")
        self.client = get_service_client("jobs-service", self.service_url)
    
    async def execute_job(self, job_id: int, payload: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Execute a job
        
        Args:
            job_id: ID of the job to execute
            payload: Optional payload data for the job
            
        Returns:
            Dict containing execution result
            
        Raises:
            NotFoundError: If job is not found
            ValidationError: If job data is invalid
            ServiceCommunicationError: If jobs service is unavailable
        """
        try:
            headers = await _get_authenticated_headers()
            
            request_data = payload or {}
            response = await self.client.post_json(f"/jobs/{job_id}/run", request_data, headers=headers)
            
            return response
            
        except Exception as e:
            if isinstance(e, (NotFoundError, ValidationError, ServiceCommunicationError)):
                raise
            logger.error(f"Job execution failed for job {job_id}: {e}")
            raise ServiceCommunicationError("jobs-service", f"Job execution error: {str(e)}")
    
    async def get_job(self, job_id: int) -> Dict[str, Any]:
        """
        Get job information
        
        Args:
            job_id: ID of the job
            
        Returns:
            Dict containing job information
        """
        try:
            headers = await _get_authenticated_headers()
            response = await self.client.get_json(f"/jobs/{job_id}", headers=headers)
            
            return response
            
        except Exception as e:
            if isinstance(e, (NotFoundError, ServiceCommunicationError)):
                raise
            logger.error(f"Failed to get job {job_id}: {e}")
            raise ServiceCommunicationError("jobs-service", f"Get job error: {str(e)}")
    
    async def get_job_status(self, job_id: int) -> Dict[str, Any]:
        """
        Get job execution status
        
        Args:
            job_id: ID of the job
            
        Returns:
            Dict containing job status information
        """
        try:
            headers = await _get_authenticated_headers()
            response = await self.client.get_json(f"/jobs/{job_id}/status", headers=headers)
            
            return response
            
        except Exception as e:
            if isinstance(e, (NotFoundError, ServiceCommunicationError)):
                raise
            logger.error(f"Failed to get job status {job_id}: {e}")
            raise ServiceCommunicationError("jobs-service", f"Get job status error: {str(e)}")

class NotificationServiceClient:
    """Client for notification service operations"""
    
    def __init__(self):
        self.service_url = os.getenv("NOTIFICATION_SERVICE_URL", "http://notification-service:3007")
        self.client = get_service_client("notification-service", self.service_url)
    
    async def send_notification(self, notification_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Send a notification
        
        Args:
            notification_data: Notification data including type, destination, and payload
            
        Returns:
            Dict containing notification result
        """
        try:
            headers = await _get_authenticated_headers()
            response = await self.client.post_json("/notifications", notification_data, headers=headers)
            
            return response
            
        except Exception as e:
            if isinstance(e, (ValidationError, ServiceCommunicationError)):
                raise
            logger.error(f"Failed to send notification: {e}")
            raise ServiceCommunicationError("notification-service", f"Send notification error: {str(e)}")
    
    async def send_email(self, to: str, subject: str, body: str, template_id: Optional[int] = None) -> Dict[str, Any]:
        """
        Send email notification
        
        Args:
            to: Email recipient
            subject: Email subject
            body: Email body
            template_id: Optional template ID
            
        Returns:
            Dict containing send result
        """
        notification_data = {
            "type": "email",
            "destination": to,
            "payload": {
                "subject": subject,
                "body": body
            }
        }
        
        if template_id:
            notification_data["template_id"] = template_id
        
        return await self.send_notification(notification_data)
    
    async def send_slack(self, webhook_url: str, message: str, payload: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Send Slack notification
        
        Args:
            webhook_url: Slack webhook URL
            message: Message text
            payload: Optional additional payload data
            
        Returns:
            Dict containing send result
        """
        notification_data = {
            "type": "slack",
            "destination": webhook_url,
            "payload": {
                "message": message,
                **(payload or {})
            }
        }
        
        return await self.send_notification(notification_data)

class CredentialsServiceClient:
    """Client for credentials service operations"""
    
    def __init__(self):
        self.service_url = os.getenv("CREDENTIALS_SERVICE_URL", "http://credentials-service:3004")
        self.client = get_service_client("credentials-service", self.service_url)
    
    async def get_credential(self, credential_id: int) -> Dict[str, Any]:
        """
        Get credential by ID
        
        Args:
            credential_id: ID of the credential
            
        Returns:
            Dict containing credential data
        """
        try:
            headers = await _get_authenticated_headers()
            response = await self.client.get_json(f"/credentials/{credential_id}", headers=headers)
            
            return response
            
        except Exception as e:
            if isinstance(e, (NotFoundError, ServiceCommunicationError)):
                raise
            logger.error(f"Failed to get credential {credential_id}: {e}")
            raise ServiceCommunicationError("credentials-service", f"Get credential error: {str(e)}")
    
    async def get_credentials_by_target(self, target_id: int) -> List[Dict[str, Any]]:
        """
        Get credentials for a target
        
        Args:
            target_id: ID of the target
            
        Returns:
            List of credential dictionaries
        """
        try:
            headers = await _get_authenticated_headers()
            response = await self.client.get_json(f"/targets/{target_id}/credentials", headers=headers)
            
            return response.get("credentials", [])
            
        except Exception as e:
            if isinstance(e, (NotFoundError, ServiceCommunicationError)):
                raise
            logger.error(f"Failed to get credentials for target {target_id}: {e}")
            raise ServiceCommunicationError("credentials-service", f"Get target credentials error: {str(e)}")

class UserServiceClient:
    """Client for user service operations"""
    
    def __init__(self):
        self.service_url = os.getenv("USER_SERVICE_URL", "http://user-service:3002")
        self.client = get_service_client("user-service", self.service_url)
    
    async def get_user(self, user_id: int) -> Dict[str, Any]:
        """
        Get user by ID
        
        Args:
            user_id: ID of the user
            
        Returns:
            Dict containing user data
        """
        try:
            headers = await _get_authenticated_headers()
            response = await self.client.get_json(f"/users/{user_id}", headers=headers)
            
            return response
            
        except Exception as e:
            if isinstance(e, (NotFoundError, ServiceCommunicationError)):
                raise
            logger.error(f"Failed to get user {user_id}: {e}")
            raise ServiceCommunicationError("user-service", f"Get user error: {str(e)}")
    
    async def get_user_preferences(self, user_id: int) -> Dict[str, Any]:
        """
        Get user notification preferences
        
        Args:
            user_id: ID of the user
            
        Returns:
            Dict containing user preferences
        """
        try:
            headers = await _get_authenticated_headers()
            response = await self.client.get_json(f"/users/{user_id}/preferences", headers=headers)
            
            return response
            
        except Exception as e:
            if isinstance(e, (NotFoundError, ServiceCommunicationError)):
                raise
            logger.error(f"Failed to get user preferences {user_id}: {e}")
            raise ServiceCommunicationError("user-service", f"Get user preferences error: {str(e)}")

# Client factory functions
_auth_client = None
_jobs_client = None
_notification_client = None
_credentials_client = None
_user_client = None

def get_auth_client() -> AuthServiceClient:
    """Get or create auth service client"""
    global _auth_client
    if _auth_client is None:
        _auth_client = AuthServiceClient()
    return _auth_client

def get_jobs_client() -> JobsServiceClient:
    """Get or create jobs service client"""
    global _jobs_client
    if _jobs_client is None:
        _jobs_client = JobsServiceClient()
    return _jobs_client

def get_notification_client() -> NotificationServiceClient:
    """Get or create notification service client"""
    global _notification_client
    if _notification_client is None:
        _notification_client = NotificationServiceClient()
    return _notification_client

def get_credentials_client() -> CredentialsServiceClient:
    """Get or create credentials service client"""
    global _credentials_client
    if _credentials_client is None:
        _credentials_client = CredentialsServiceClient()
    return _credentials_client

def get_user_client() -> UserServiceClient:
    """Get or create user service client"""
    global _user_client
    if _user_client is None:
        _user_client = UserServiceClient()
    return _user_client

def reset_clients() -> None:
    """Reset all client instances (useful for testing)"""
    global _auth_client, _jobs_client, _notification_client, _credentials_client, _user_client
    _auth_client = None
    _jobs_client = None
    _notification_client = None
    _credentials_client = None
    _user_client = None
    logger.info("All service clients reset")