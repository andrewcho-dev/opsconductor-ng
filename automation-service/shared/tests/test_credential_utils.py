#!/usr/bin/env python3
"""
Unit tests for the shared credential utilities
"""

import os
import unittest
from unittest.mock import patch, MagicMock
import sys
import logging

# Use package-relative import
from shared.credential_utils import CredentialManager

class TestCredentialManager(unittest.TestCase):
    """Test cases for the CredentialManager class"""
    
    def setUp(self):
        """Set up test fixtures"""
        # Disable logging during tests
        logging.disable(logging.CRITICAL)
        
        # Create a test encryption key
        self.test_key = "Uup6urR_7deaT0yKl9fI5qhohKmPRjvSQt_MCGXSLQw="
        
        # Create a test previous key
        self.test_prev_key = "cKmPRjvSQt_MCGXSLQw=Uup6urR_7deaT0yKl9fI5qhoh"
        
        # Create a test credential manager with the test key
        self.credential_manager = CredentialManager(encryption_key=self.test_key)
        
        # Test data
        self.test_password = "test_password"
        self.test_api_key = "test_api_key"
        
    def tearDown(self):
        """Tear down test fixtures"""
        # Re-enable logging
        logging.disable(logging.NOTSET)
    
    def test_encrypt_decrypt_field(self):
        """Test encrypting and decrypting a field"""
        # Encrypt the test password
        encrypted = self.credential_manager.encrypt_field(self.test_password)
        
        # Verify it's not the same as the original
        self.assertNotEqual(encrypted, self.test_password)
        
        # Decrypt the encrypted password
        decrypted = self.credential_manager.decrypt_field(encrypted)
        
        # Verify it matches the original
        self.assertEqual(decrypted, self.test_password)
    
    def test_encrypt_decrypt_none(self):
        """Test encrypting and decrypting None values"""
        # Encrypt None
        encrypted = self.credential_manager.encrypt_field(None)
        
        # Verify it's None
        self.assertIsNone(encrypted)
        
        # Decrypt None
        decrypted = self.credential_manager.decrypt_field(None)
        
        # Verify it's None
        self.assertIsNone(decrypted)
    
    def test_encrypt_decrypt_additional_services(self):
        """Test encrypting and decrypting additional services"""
        # Create test services
        services = [
            {
                "service_type": "ssh",
                "port": 22,
                "username": "test_user",
                "password": "test_password"
            },
            {
                "service_type": "http",
                "port": 80,
                "api_key": "test_api_key"
            }
        ]
        
        # Encrypt the services
        encrypted_services = self.credential_manager.encrypt_additional_services(services)
        
        # Verify the password is encrypted
        self.assertNotIn("password", encrypted_services[0])
        self.assertIn("password_encrypted", encrypted_services[0])
        
        # Verify the API key is encrypted
        self.assertNotIn("api_key", encrypted_services[1])
        self.assertIn("api_key_encrypted", encrypted_services[1])
        
        # Decrypt the services
        decrypted_services = self.credential_manager.decrypt_additional_services(encrypted_services)
        
        # Verify the password is decrypted
        self.assertEqual(decrypted_services[0]["password"], "test_password")
        
        # Verify the API key is decrypted
        self.assertEqual(decrypted_services[1]["api_key"], "test_api_key")
    
    @patch.dict(os.environ, {"SERVICE_NAME": "test-service", "TEST_SERVICE_ENCRYPTION_KEY": "Uup6urR_7deaT0yKl9fI5qhohKmPRjvSQt_MCGXSLQw="})
    def test_get_encryption_key_from_env_service_specific(self):
        """Test getting the encryption key from environment variables (service-specific)"""
        # Create a credential manager without specifying a key
        cm = CredentialManager()
        
        # Encrypt and decrypt to verify the key works
        encrypted = cm.encrypt_field(self.test_password)
        decrypted = cm.decrypt_field(encrypted)
        
        # Verify it matches the original
        self.assertEqual(decrypted, self.test_password)
    
    @patch.dict(os.environ, {"ENCRYPTION_KEY": "Uup6urR_7deaT0yKl9fI5qhohKmPRjvSQt_MCGXSLQw="})
    def test_get_encryption_key_from_env_legacy(self):
        """Test getting the encryption key from environment variables (legacy)"""
        # Create a credential manager without specifying a key
        cm = CredentialManager()
        
        # Encrypt and decrypt to verify the key works
        encrypted = cm.encrypt_field(self.test_password)
        decrypted = cm.decrypt_field(encrypted)
        
        # Verify it matches the original
        self.assertEqual(decrypted, self.test_password)
    
    def test_key_rotation(self):
        """Test key rotation support"""
        # Create a credential manager with the previous key
        old_cm = CredentialManager(encryption_key=self.test_prev_key)
        
        # Encrypt with the old key
        encrypted_with_old_key = old_cm.encrypt_field(self.test_password)
        
        # Create a credential manager with the current key and previous keys
        new_cm = CredentialManager(
            encryption_key=self.test_key,
            previous_keys=[self.test_prev_key]
        )
        
        # Decrypt with the new credential manager
        decrypted = new_cm.decrypt_field(encrypted_with_old_key)
        
        # Verify it matches the original
        self.assertEqual(decrypted, self.test_password)
        
        # Check if it needs re-encryption
        self.assertTrue(new_cm.needs_reencryption(encrypted_with_old_key))
        
        # Re-encrypt with the current key
        reencrypted = new_cm.reencrypt_with_current_key(encrypted_with_old_key)
        
        # Verify it's different from the old encrypted value
        self.assertNotEqual(reencrypted, encrypted_with_old_key)
        
        # Verify it decrypts to the original
        decrypted_after_reencryption = new_cm.decrypt_field(reencrypted)
        self.assertEqual(decrypted_after_reencryption, self.test_password)
        
        # Verify it no longer needs re-encryption
        self.assertFalse(new_cm.needs_reencryption(reencrypted))


if __name__ == "__main__":
    unittest.main()