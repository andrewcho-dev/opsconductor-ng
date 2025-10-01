#!/usr/bin/env python3
"""
Shared credential utilities for OpsConductor services
Handles encryption and decryption of sensitive credential information
"""

import os
import logging
from typing import List, Dict, Any, Optional
from cryptography.fernet import Fernet, InvalidToken

class CredentialManager:
    """
    Manages encryption and decryption of credentials across services
    
    Features:
    - Service-specific encryption keys
    - Key rotation support
    - Secure handling of sensitive information
    """
    
    def __init__(self, encryption_key=None, previous_keys=None):
        """
        Initialize the credential manager with encryption keys
        
        Args:
            encryption_key: The primary encryption key to use. If None, will try to get from environment
            previous_keys: List of previous encryption keys for rotation support
        """
        self.logger = logging.getLogger(__name__)
        
        # Get primary encryption key from parameter or environment
        if not encryption_key:
            encryption_key = self._get_encryption_key_from_env()
            
        if isinstance(encryption_key, str):
            encryption_key = encryption_key.encode()
        
        # Initialize primary encryption object
        self.fernet = Fernet(encryption_key)
        
        # Initialize previous keys for rotation support
        self.previous_fernets = []
        if previous_keys:
            for key in previous_keys:
                if isinstance(key, str):
                    key = key.encode()
                self.previous_fernets.append(Fernet(key))
                
        # Try to load previous keys from environment
        self._load_previous_keys_from_env()
    
    def _get_encryption_key_from_env(self) -> bytes:
        """
        Get encryption key from environment variable
        
        Tries service-specific keys first, falls back to legacy key if needed
        """
        # Get service name from environment or use a default
        service_name = os.environ.get('SERVICE_NAME', '').lower()
        
        # Try service-specific key first (e.g., ASSET_SERVICE_ENCRYPTION_KEY)
        if service_name:
            service_key_name = f"{service_name.replace('-', '_').upper()}_ENCRYPTION_KEY"
            env_key = os.environ.get(service_key_name)
            if env_key and env_key != f'your-{service_name}-encryption-key-32-bytes-long':
                self.logger.info(f"Using service-specific encryption key: {service_key_name}")
                return env_key
        
        # Fall back to legacy key
        env_key = os.environ.get('ENCRYPTION_KEY')
        if not env_key or env_key == 'your-encryption-key-for-credentials-32-bytes-long':
            self.logger.error("No valid encryption key found in environment variables")
            raise ValueError("No valid encryption key found. Set either a service-specific key or ENCRYPTION_KEY")
        
        self.logger.warning("Using legacy ENCRYPTION_KEY. Consider migrating to service-specific keys.")
        return env_key
    
    def encrypt_field(self, value: str) -> Optional[str]:
        """
        Encrypt a field value
        
        Args:
            value: The string value to encrypt
            
        Returns:
            Encrypted string or None if value is empty
        """
        if not value:
            return None
        
        try:
            return self.fernet.encrypt(value.encode()).decode()
        except Exception as e:
            self.logger.error(f"Encryption error: {str(e)}")
            raise ValueError(f"Failed to encrypt value: {str(e)}")
    
    def _load_previous_keys_from_env(self):
        """Load previous encryption keys from environment variables for key rotation"""
        service_name = os.environ.get('SERVICE_NAME', '').lower()
        
        # Try to load previous keys (format: SERVICE_PREVIOUS_KEYS=key1,key2,key3)
        if service_name:
            prev_keys_var = f"{service_name.replace('-', '_').upper()}_PREVIOUS_KEYS"
            prev_keys_str = os.environ.get(prev_keys_var, '')
            
            if prev_keys_str:
                try:
                    # Split by comma and add each key
                    for key in prev_keys_str.split(','):
                        key = key.strip()
                        if key:
                            self.previous_fernets.append(Fernet(key.encode()))
                    
                    if self.previous_fernets:
                        self.logger.info(f"Loaded {len(self.previous_fernets)} previous keys for rotation")
                except Exception as e:
                    self.logger.error(f"Error loading previous keys: {str(e)}")
    
    def decrypt_field(self, encrypted_value: str) -> Optional[str]:
        """
        Decrypt a field value with key rotation support
        
        Args:
            encrypted_value: The encrypted string to decrypt
            
        Returns:
            Decrypted string or None if decryption fails
        """
        if not encrypted_value:
            return None
        
        # Try with current key first
        try:
            return self.fernet.decrypt(encrypted_value.encode()).decode()
        except InvalidToken:
            # If current key fails, try previous keys (key rotation)
            for prev_fernet in self.previous_fernets:
                try:
                    decrypted = prev_fernet.decrypt(encrypted_value.encode()).decode()
                    self.logger.info("Successfully decrypted with a previous key. Consider re-encrypting with current key.")
                    return decrypted
                except InvalidToken:
                    continue
                except Exception:
                    continue
            
            self.logger.error("Failed to decrypt with current or previous keys")
            return None
        except Exception as e:
            self.logger.error(f"Decryption error: {str(e)}")
            return None
    
    def _encrypt_sensitive_field(self, data: Dict[str, Any], field_name: str) -> Dict[str, Any]:
        """
        Helper method to encrypt a sensitive field
        
        Args:
            data: Dictionary containing the field
            field_name: Name of the field to encrypt
            
        Returns:
            Dictionary with the field encrypted (if present)
        """
        if field_name in data and data[field_name]:
            encrypted_field = f"{field_name}_encrypted"
            data[encrypted_field] = self.encrypt_field(data[field_name])
            del data[field_name]
        return data
    
    def encrypt_credential_fields(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Encrypt credential fields in a dictionary
        
        Args:
            data: Dictionary containing credential fields
            
        Returns:
            Dictionary with encrypted credential fields
        """
        encrypted_data = data.copy()
        
        # Fields that need encryption
        sensitive_fields = [
            'password', 'private_key', 'api_key', 
            'bearer_token', 'certificate', 'passphrase',
            'secondary_password'
        ]
        
        for field in sensitive_fields:
            self._encrypt_sensitive_field(encrypted_data, field)
        
        return encrypted_data
    
    def encrypt_additional_services(self, services: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Encrypt credential fields in additional services
        
        Args:
            services: List of service dictionaries with credential fields
            
        Returns:
            List of service dictionaries with encrypted credential fields
        """
        encrypted_services = []
        
        for service in services:
            encrypted_service = service.copy()
            
            # Fields that need encryption
            sensitive_fields = [
                'password', 'private_key', 'api_key', 
                'bearer_token', 'certificate', 'passphrase'
            ]
            
            # Encrypt each sensitive field
            for field in sensitive_fields:
                self._encrypt_sensitive_field(encrypted_service, field)
            
            encrypted_services.append(encrypted_service)
        
        return encrypted_services
    
    def _decrypt_sensitive_field(self, data: Dict[str, Any], field_name: str) -> Dict[str, Any]:
        """
        Helper method to decrypt a sensitive field
        
        Args:
            data: Dictionary containing the encrypted field
            field_name: Base name of the field to decrypt (without _encrypted suffix)
            
        Returns:
            Dictionary with the field decrypted (if present)
        """
        encrypted_field = f"{field_name}_encrypted"
        if encrypted_field in data and data[encrypted_field]:
            data[field_name] = self.decrypt_field(data[encrypted_field])
        return data
    
    def decrypt_additional_services(self, services: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Decrypt credential fields in additional services for display
        
        Args:
            services: List of service dictionaries with encrypted credential fields
            
        Returns:
            List of service dictionaries with decrypted credential fields
        """
        decrypted_services = []
        
        for service in services:
            decrypted_service = service.copy()
            
            # Fields that need decryption
            sensitive_fields = [
                'password', 'private_key', 'api_key', 
                'bearer_token', 'certificate', 'passphrase'
            ]
            
            # Decrypt each sensitive field
            for field in sensitive_fields:
                self._decrypt_sensitive_field(decrypted_service, field)
            
            decrypted_services.append(decrypted_service)
        
        return decrypted_services
        
    def reencrypt_with_current_key(self, encrypted_value: str) -> Optional[str]:
        """
        Re-encrypt a value with the current key (for key rotation)
        
        Args:
            encrypted_value: The encrypted string to re-encrypt
            
        Returns:
            Re-encrypted string with current key or None if decryption fails
        """
        if not encrypted_value:
            return None
            
        # First decrypt with any available key
        decrypted = self.decrypt_field(encrypted_value)
        if decrypted is None:
            self.logger.error("Failed to decrypt value during re-encryption attempt")
            return None
            
        # Then encrypt with current key
        try:
            re_encrypted = self.encrypt_field(decrypted)
            self.logger.info("Successfully re-encrypted value with current key")
            return re_encrypted
        except Exception as e:
            self.logger.error(f"Failed to re-encrypt value: {str(e)}")
            return None
        
    def needs_reencryption(self, encrypted_value: str) -> bool:
        """
        Check if a value needs re-encryption (was encrypted with a previous key)
        
        Args:
            encrypted_value: The encrypted string to check
            
        Returns:
            True if the value was encrypted with a previous key, False otherwise
        """
        if not encrypted_value:
            return False
            
        try:
            # Try to decrypt with current key
            self.fernet.decrypt(encrypted_value.encode())
            return False  # Current key worked, no need for re-encryption
        except InvalidToken:
            # Try with previous keys
            for i, prev_fernet in enumerate(self.previous_fernets):
                try:
                    prev_fernet.decrypt(encrypted_value.encode())
                    self.logger.info(f"Value was encrypted with previous key (index: {i}), needs re-encryption")
                    return True  # Previous key worked, needs re-encryption
                except Exception:
                    continue
                    
            # No key worked
            self.logger.warning("Could not decrypt value with any available key")
            return False
        except Exception as e:
            self.logger.error(f"Error checking if value needs re-encryption: {str(e)}")
            return False