#!/usr/bin/env python3

from cryptography.fernet import Fernet

# Test decryption
encryption_key = "Uup6urR_7deaT0yKl9fI5qhohKmPRjvSQt_MCGXSLQw="
encrypted_password = "gAAAAABozvMtbqjXExlCELeclm79Dz71ub4UNTWg3dpwHAplguqoeQpHHDHgHKty15iVI5tbBHrPNl4V8mydmbWShipdNArURg=="

print(f"Encryption key: {encryption_key}")
print(f"Encrypted password: {encrypted_password}")

try:
    # Convert key to bytes if needed
    if isinstance(encryption_key, str):
        encryption_key = encryption_key.encode()
    
    cipher_suite = Fernet(encryption_key)
    
    # Try to decrypt
    decrypted = cipher_suite.decrypt(encrypted_password.encode()).decode()
    print(f"Decrypted password: {decrypted}")
    
except Exception as e:
    print(f"Decryption failed: {type(e).__name__}: {e}")
    
    # Let's also try with base64 decoding first (old method)
    import base64
    try:
        print("Trying old method (base64 + Fernet)...")
        decrypted_old = cipher_suite.decrypt(base64.b64decode(encrypted_password.encode())).decode()
        print(f"Decrypted with old method: {decrypted_old}")
    except Exception as e2:
        print(f"Old method also failed: {type(e2).__name__}: {e2}")