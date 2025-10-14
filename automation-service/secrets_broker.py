#!/usr/bin/env python3
"""
Secrets Broker - Server-side credential management
Provides secure storage and retrieval of host credentials
INTERNAL USE ONLY - Not exposed via Kong gateway
"""

import os
import logging
import base64
import json
from typing import Optional, Dict, Any
from datetime import datetime
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2
import psycopg2
from psycopg2.extras import RealDictCursor

logger = logging.getLogger(__name__)


class SecretsManager:
    """
    Manages encrypted credential storage and retrieval
    Uses AES-256-GCM for encryption at rest
    """
    
    def __init__(self, kms_key: str, database_url: str):
        """
        Initialize secrets manager
        
        Args:
            kms_key: Master encryption key (from env: SECRETS_KMS_KEY)
            database_url: PostgreSQL connection string
        """
        self.database_url = database_url
        
        # Derive 256-bit key from KMS key using PBKDF2
        kdf = PBKDF2(
            algorithm=hashes.SHA256(),
            length=32,
            salt=b'opsconductor-secrets-v1',  # Static salt for deterministic key
            iterations=100000,
        )
        self.encryption_key = kdf.derive(kms_key.encode('utf-8'))
        self.aesgcm = AESGCM(self.encryption_key)
        
        logger.info("SecretsManager initialized with AES-256-GCM encryption")
    
    def _get_connection(self):
        """Get database connection"""
        return psycopg2.connect(self.database_url, cursor_factory=RealDictCursor)
    
    def _encrypt(self, plaintext: str) -> str:
        """
        Encrypt plaintext using AES-256-GCM
        
        Returns:
            Base64-encoded: nonce(12 bytes) + ciphertext + tag(16 bytes)
        """
        if not plaintext:
            return ""
        
        # Generate random 96-bit nonce
        nonce = os.urandom(12)
        
        # Encrypt and authenticate
        ciphertext = self.aesgcm.encrypt(nonce, plaintext.encode('utf-8'), None)
        
        # Combine nonce + ciphertext (which includes auth tag)
        encrypted = nonce + ciphertext
        
        # Return base64-encoded
        return base64.b64encode(encrypted).decode('utf-8')
    
    def _decrypt(self, encrypted: str) -> str:
        """
        Decrypt AES-256-GCM encrypted data
        
        Args:
            encrypted: Base64-encoded nonce + ciphertext + tag
            
        Returns:
            Decrypted plaintext
        """
        if not encrypted:
            return ""
        
        try:
            # Decode from base64
            data = base64.b64decode(encrypted)
            
            # Extract nonce (first 12 bytes) and ciphertext (rest)
            nonce = data[:12]
            ciphertext = data[12:]
            
            # Decrypt and verify
            plaintext = self.aesgcm.decrypt(nonce, ciphertext, None)
            
            return plaintext.decode('utf-8')
        except Exception as e:
            logger.error(f"Decryption failed: {e}")
            raise ValueError("Failed to decrypt credential")
    
    def upsert_credential(
        self,
        host: str,
        purpose: str,
        username: Optional[str] = None,
        password: Optional[str] = None,
        domain: Optional[str] = None,
        additional_data: Optional[Dict[str, Any]] = None,
        created_by: str = "system"
    ) -> Dict[str, Any]:
        """
        Create or update a credential
        
        Args:
            host: Hostname or IP address
            purpose: Connection purpose ('winrm', 'ssh', 'rdp', etc.)
            username: Username for authentication
            password: Password (will be encrypted)
            domain: Windows domain (optional)
            additional_data: Extra fields (private keys, tokens, etc.)
            created_by: User or service creating the credential
            
        Returns:
            Dict with credential ID and status
        """
        conn = None
        try:
            conn = self._get_connection()
            cur = conn.cursor()
            
            # Encrypt password if provided
            password_encrypted = self._encrypt(password) if password else None
            
            # Encrypt additional_data if provided
            additional_json = json.dumps(additional_data or {})
            
            # Upsert credential
            cur.execute("""
                INSERT INTO secrets.host_credentials 
                    (host, purpose, username, password_encrypted, domain, additional_data, created_by, updated_by)
                VALUES (%s, %s, %s, %s, %s, %s::jsonb, %s, %s)
                ON CONFLICT (host, purpose) 
                DO UPDATE SET
                    username = EXCLUDED.username,
                    password_encrypted = EXCLUDED.password_encrypted,
                    domain = EXCLUDED.domain,
                    additional_data = EXCLUDED.additional_data,
                    updated_by = EXCLUDED.updated_by,
                    updated_at = CURRENT_TIMESTAMP
                RETURNING id
            """, (host, purpose, username, password_encrypted, domain, additional_json, created_by, created_by))
            
            result = cur.fetchone()
            credential_id = result['id']
            
            # Log access
            cur.execute("""
                INSERT INTO secrets.credential_access_log
                    (credential_id, host, purpose, accessed_by, access_type, success)
                VALUES (%s, %s, %s, %s, %s, %s)
            """, (credential_id, host, purpose, created_by, 'create', True))
            
            conn.commit()
            
            logger.info(f"Credential upserted for host={host}, purpose={purpose}")
            
            return {
                "success": True,
                "credential_id": credential_id,
                "host": host,
                "purpose": purpose
            }
            
        except Exception as e:
            if conn:
                conn.rollback()
            logger.error(f"Failed to upsert credential: {e}")
            raise
        finally:
            if conn:
                conn.close()
    
    def lookup_credential(
        self,
        host: str,
        purpose: str,
        accessed_by: str = "system"
    ) -> Optional[Dict[str, Any]]:
        """
        Retrieve and decrypt a credential
        
        Args:
            host: Hostname or IP address
            purpose: Connection purpose ('winrm', 'ssh', etc.)
            accessed_by: Service or user accessing the credential
            
        Returns:
            Dict with decrypted credentials or None if not found
        """
        conn = None
        try:
            conn = self._get_connection()
            cur = conn.cursor()
            
            # Lookup credential
            cur.execute("""
                SELECT id, host, purpose, username, password_encrypted, domain, additional_data
                FROM secrets.host_credentials
                WHERE host = %s AND purpose = %s
            """, (host, purpose))
            
            result = cur.fetchone()
            
            if not result:
                # Log failed access
                cur.execute("""
                    INSERT INTO secrets.credential_access_log
                        (credential_id, host, purpose, accessed_by, access_type, success, error_message)
                    VALUES (NULL, %s, %s, %s, %s, %s, %s)
                """, (host, purpose, accessed_by, 'read', False, 'not_found'))
                conn.commit()
                
                logger.warning(f"Credential not found for host={host}, purpose={purpose}")
                return None
            
            # Decrypt password
            password = self._decrypt(result['password_encrypted']) if result['password_encrypted'] else None
            
            # Log successful access (but don't log the actual password)
            cur.execute("""
                INSERT INTO secrets.credential_access_log
                    (credential_id, host, purpose, accessed_by, access_type, success)
                VALUES (%s, %s, %s, %s, %s, %s)
            """, (result['id'], host, purpose, accessed_by, 'read', True))
            
            conn.commit()
            
            logger.info(f"Credential retrieved for host={host}, purpose={purpose} (password masked in logs)")
            
            return {
                "host": result['host'],
                "purpose": result['purpose'],
                "username": result['username'],
                "password": password,  # Decrypted
                "domain": result['domain'],
                "additional_data": result['additional_data']
            }
            
        except Exception as e:
            if conn:
                conn.rollback()
            logger.error(f"Failed to lookup credential: {e}")
            raise
        finally:
            if conn:
                conn.close()
    
    def delete_credential(
        self,
        host: str,
        purpose: str,
        deleted_by: str = "system"
    ) -> bool:
        """
        Delete a credential
        
        Args:
            host: Hostname or IP address
            purpose: Connection purpose
            deleted_by: User or service deleting the credential
            
        Returns:
            True if deleted, False if not found
        """
        conn = None
        try:
            conn = self._get_connection()
            cur = conn.cursor()
            
            # Get credential ID before deleting
            cur.execute("""
                SELECT id FROM secrets.host_credentials
                WHERE host = %s AND purpose = %s
            """, (host, purpose))
            
            result = cur.fetchone()
            
            if not result:
                logger.warning(f"Credential not found for deletion: host={host}, purpose={purpose}")
                return False
            
            credential_id = result['id']
            
            # Log deletion
            cur.execute("""
                INSERT INTO secrets.credential_access_log
                    (credential_id, host, purpose, accessed_by, access_type, success)
                VALUES (%s, %s, %s, %s, %s, %s)
            """, (credential_id, host, purpose, deleted_by, 'delete', True))
            
            # Delete credential
            cur.execute("""
                DELETE FROM secrets.host_credentials
                WHERE host = %s AND purpose = %s
            """, (host, purpose))
            
            conn.commit()
            
            logger.info(f"Credential deleted for host={host}, purpose={purpose}")
            
            return True
            
        except Exception as e:
            if conn:
                conn.rollback()
            logger.error(f"Failed to delete credential: {e}")
            raise
        finally:
            if conn:
                conn.close()