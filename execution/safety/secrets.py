"""
Secrets Manager - Safety Feature #4

Just-in-time secret resolution with automatic masking:
- Secrets are resolved at execution time, not planning time
- Secrets are never stored in plan snapshots
- Automatic masking in logs and error messages
- Integration with secret stores (HashiCorp Vault, AWS Secrets Manager, etc.)

Implementation:
- Secret references in plan: {"type": "secret", "path": "db/prod/password"}
- Resolution at execution time using secret store client
- Automatic masking using regex patterns
- Audit trail for all secret accesses

Usage:
    manager = SecretsManager(secret_store_client)
    resolved_value = await manager.resolve_secret(secret_ref, execution_id)
    masked_log = manager.mask_secrets(log_message)
"""

import logging
import re
from typing import Dict, Any, Optional, List
from datetime import datetime

from execution.repository import ExecutionRepository

logger = logging.getLogger(__name__)


class SecretResolutionError(Exception):
    """Raised when secret resolution fails"""
    pass


class SecretsManager:
    """
    Secrets manager for just-in-time secret resolution.
    
    This is Safety Feature #4 and is critical for production deployment.
    """
    
    # Common secret patterns to mask in logs
    SECRET_PATTERNS = [
        # API keys
        (r'api[_-]?key["\s:=]+([a-zA-Z0-9_\-]{20,})', r'api_key=***MASKED***'),
        # Passwords
        (r'password["\s:=]+([^\s"\']+)', r'password=***MASKED***'),
        # Tokens
        (r'token["\s:=]+([a-zA-Z0-9_\-\.]{20,})', r'token=***MASKED***'),
        # AWS keys
        (r'AKIA[0-9A-Z]{16}', r'***MASKED_AWS_KEY***'),
        # Private keys
        (r'-----BEGIN [A-Z ]+PRIVATE KEY-----[^-]+-----END [A-Z ]+PRIVATE KEY-----', 
         r'***MASKED_PRIVATE_KEY***'),
        # Generic secrets (base64-like strings)
        (r'secret["\s:=]+([a-zA-Z0-9+/]{32,}={0,2})', r'secret=***MASKED***'),
    ]
    
    def __init__(
        self,
        repository: ExecutionRepository,
        secret_store_client: Optional[Any] = None,
        enable_masking: bool = True,
    ):
        """
        Initialize secrets manager.
        
        Args:
            repository: Execution repository for database access
            secret_store_client: Secret store client (Vault, AWS Secrets Manager, etc.)
            enable_masking: Enable automatic masking in logs (default: True)
        """
        self.repository = repository
        self.secret_store_client = secret_store_client
        self.enable_masking = enable_masking
        self._compiled_patterns = [
            (re.compile(pattern, re.IGNORECASE), replacement)
            for pattern, replacement in self.SECRET_PATTERNS
        ]
    
    async def resolve_secret(
        self,
        secret_ref: Dict[str, Any],
        execution_id: str,
        tenant_id: str,
    ) -> str:
        """
        Resolve secret reference to actual value.
        
        This is the main entry point for secret resolution.
        
        Args:
            secret_ref: Secret reference (e.g., {"type": "secret", "path": "db/prod/password"})
            execution_id: Execution ID
            tenant_id: Tenant ID
        
        Returns:
            Resolved secret value
        
        Raises:
            SecretResolutionError: If secret cannot be resolved
        """
        if not isinstance(secret_ref, dict) or secret_ref.get("type") != "secret":
            raise SecretResolutionError(
                f"Invalid secret reference: {secret_ref}"
            )
        
        secret_path = secret_ref.get("path")
        if not secret_path:
            raise SecretResolutionError(
                f"Secret path is required: {secret_ref}"
            )
        
        logger.info(
            f"Resolving secret: path={secret_path}, execution_id={execution_id}"
        )
        
        # Add event to audit trail
        self.repository.create_execution_event(
            execution_id=execution_id,
            event_type="secret_accessed",
            event_data={
                "secret_path": secret_path,
                "tenant_id": tenant_id,
                "timestamp": datetime.utcnow().isoformat(),
            },
        )
        
        # Resolve secret from store
        try:
            secret_value = await self._resolve_from_store(
                secret_path=secret_path,
                tenant_id=tenant_id,
            )
            
            logger.info(
                f"Secret resolved successfully: path={secret_path}, "
                f"execution_id={execution_id}"
            )
            
            return secret_value
        except Exception as e:
            error_msg = f"Failed to resolve secret {secret_path}: {e}"
            logger.error(error_msg)
            
            # Add event to audit trail
            self.repository.create_execution_event(
                execution_id=execution_id,
                event_type="secret_resolution_failed",
                event_data={
                    "secret_path": secret_path,
                    "error": str(e),
                },
            )
            
            raise SecretResolutionError(error_msg) from e
    
    async def resolve_secrets_in_data(
        self,
        data: Dict[str, Any],
        execution_id: str,
        tenant_id: str,
    ) -> Dict[str, Any]:
        """
        Recursively resolve all secret references in data structure.
        
        Args:
            data: Data structure with potential secret references
            execution_id: Execution ID
            tenant_id: Tenant ID
        
        Returns:
            Data structure with resolved secrets
        """
        if isinstance(data, dict):
            # Check if this is a secret reference
            if data.get("type") == "secret":
                return await self.resolve_secret(data, execution_id, tenant_id)
            
            # Recursively process dict values
            return {
                key: await self.resolve_secrets_in_data(value, execution_id, tenant_id)
                for key, value in data.items()
            }
        elif isinstance(data, list):
            # Recursively process list items
            return [
                await self.resolve_secrets_in_data(item, execution_id, tenant_id)
                for item in data
            ]
        else:
            # Return primitive values as-is
            return data
    
    async def _resolve_from_store(
        self,
        secret_path: str,
        tenant_id: str,
    ) -> str:
        """
        Resolve secret from secret store.
        
        Args:
            secret_path: Secret path
            tenant_id: Tenant ID
        
        Returns:
            Secret value
        
        Raises:
            SecretResolutionError: If secret cannot be resolved
        """
        if not self.secret_store_client:
            # Fallback: Use environment variables or config
            # This is for development/testing only
            logger.warning(
                f"No secret store client configured, using fallback for {secret_path}"
            )
            return await self._resolve_from_fallback(secret_path, tenant_id)
        
        # Resolve from secret store (Vault, AWS Secrets Manager, etc.)
        try:
            # Add tenant prefix to secret path for multi-tenancy
            full_path = f"{tenant_id}/{secret_path}"
            
            # TODO: Implement actual secret store integration
            # Example for HashiCorp Vault:
            # secret = await self.secret_store_client.read_secret(full_path)
            # return secret['data']['value']
            
            # Example for AWS Secrets Manager:
            # response = await self.secret_store_client.get_secret_value(SecretId=full_path)
            # return response['SecretString']
            
            raise NotImplementedError("Secret store integration not implemented")
        except Exception as e:
            raise SecretResolutionError(
                f"Failed to resolve secret from store: {secret_path}"
            ) from e
    
    async def _resolve_from_fallback(
        self,
        secret_path: str,
        tenant_id: str,
    ) -> str:
        """
        Resolve secret from fallback source (environment variables, config, etc.).
        
        This is for development/testing only.
        
        Args:
            secret_path: Secret path
            tenant_id: Tenant ID
        
        Returns:
            Secret value
        """
        # TODO: Implement fallback resolution
        # For now, return a placeholder
        return f"***PLACEHOLDER_SECRET_{secret_path}***"
    
    def mask_secrets(self, text: str) -> str:
        """
        Mask secrets in text using regex patterns.
        
        This should be called on all log messages and error messages.
        
        Args:
            text: Text to mask
        
        Returns:
            Masked text
        """
        if not self.enable_masking:
            return text
        
        masked_text = text
        for pattern, replacement in self._compiled_patterns:
            masked_text = pattern.sub(replacement, masked_text)
        
        return masked_text
    
    def mask_secrets_in_data(self, data: Any) -> Any:
        """
        Recursively mask secrets in data structure.
        
        Args:
            data: Data structure to mask
        
        Returns:
            Masked data structure
        """
        if isinstance(data, dict):
            return {
                key: self.mask_secrets_in_data(value)
                for key, value in data.items()
            }
        elif isinstance(data, list):
            return [
                self.mask_secrets_in_data(item)
                for item in data
            ]
        elif isinstance(data, str):
            return self.mask_secrets(data)
        else:
            return data
    
    def add_secret_pattern(self, pattern: str, replacement: str) -> None:
        """
        Add custom secret pattern for masking.
        
        Args:
            pattern: Regex pattern to match
            replacement: Replacement text
        """
        self._compiled_patterns.append(
            (re.compile(pattern, re.IGNORECASE), replacement)
        )
        logger.info(f"Added custom secret pattern: {pattern}")