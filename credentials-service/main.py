#!/usr/bin/env python3
"""
Credentials Service - Python FastAPI Implementation
Encrypted credential storage with full CRUD operations
"""

import os
import sys
import json
import base64
from datetime import datetime
from typing import List, Optional, Dict, Any

# Add shared module to path
sys.path.append('/home/opsconductor')

from fastapi import FastAPI, HTTPException, Depends, status, Request
from pydantic import BaseModel
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography import x509
from cryptography.hazmat.primitives import serialization
from dotenv import load_dotenv

# Import shared modules
from shared.database import get_db_cursor, check_database_health, cleanup_database_pool, get_database_metrics
from shared.logging import setup_service_logging, get_logger, log_startup, log_shutdown
from shared.middleware import add_standard_middleware
from shared.models import HealthResponse, HealthCheck, PaginatedResponse, create_success_response
from shared.errors import DatabaseError, ValidationError, NotFoundError, PermissionError, handle_database_error
from shared.auth import require_admin_role

# Load environment variables
load_dotenv()

# Setup structured logging
setup_service_logging("credentials-service", level=os.getenv("LOG_LEVEL", "INFO"))
logger = get_logger("credentials-service")

# FastAPI app
app = FastAPI(
    title="Credentials Service", 
    version="1.0.0",
    description="Encrypted credential storage and management service"
)

# Add standard middleware
add_standard_middleware(app, "credentials-service", version="1.0.0")

# Helper functions for header-based authentication
def get_user_from_headers(request: Request):
    """Extract user info from nginx headers (set by gateway authentication)"""
    return {
        "id": request.headers.get("X-User-ID"),
        "username": request.headers.get("X-Username"),
        "email": request.headers.get("X-User-Email"),
        "role": request.headers.get("X-User-Role")
    }

async def require_admin_or_operator_role(request: Request):
    """Require admin or operator role (from nginx headers)"""
    current_user = get_user_from_headers(request)
    user_role = current_user.get("role")
    if user_role not in ["admin", "operator"]:
        raise PermissionError("Admin or operator role required")
    return current_user

# Configuration
MASTER_KEY = os.getenv("MASTER_KEY", "default-key-change-in-production")

# Database configuration is now handled by shared.database module

# Pydantic models
class CredentialCreate(BaseModel):
    name: str
    description: Optional[str] = None
    credential_type: str  # 'password', 'key', 'certificate'
    # Authentication fields
    username: Optional[str] = None
    password: Optional[str] = None
    domain: Optional[str] = None
    private_key: Optional[str] = None
    public_key: Optional[str] = None
    certificate: Optional[str] = None
    certificate_chain: Optional[str] = None
    passphrase: Optional[str] = None
    # Validity fields
    valid_from: Optional[datetime] = None
    valid_until: Optional[datetime] = None
    next_rotation_date: Optional[datetime] = None

class CredentialUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    credential_type: Optional[str] = None
    # Authentication fields
    username: Optional[str] = None
    password: Optional[str] = None
    domain: Optional[str] = None
    private_key: Optional[str] = None
    public_key: Optional[str] = None
    certificate: Optional[str] = None
    certificate_chain: Optional[str] = None
    passphrase: Optional[str] = None
    # Validity fields
    valid_from: Optional[datetime] = None
    valid_until: Optional[datetime] = None
    next_rotation_date: Optional[datetime] = None

class CredentialResponse(BaseModel):
    id: int
    name: str
    description: Optional[str]
    credential_type: str
    # Authentication fields (for viewing, sensitive data excluded)
    username: Optional[str] = None
    domain: Optional[str] = None
    # Validity fields
    valid_from: Optional[datetime] = None
    valid_until: Optional[datetime] = None
    next_rotation_date: Optional[datetime] = None
    # System fields
    created_at: datetime
    updated_at: Optional[datetime]

class CredentialDecrypted(CredentialResponse):
    # Sensitive authentication fields (only returned when explicitly decrypting)
    password: Optional[str] = None
    private_key: Optional[str] = None
    public_key: Optional[str] = None
    certificate: Optional[str] = None
    certificate_chain: Optional[str] = None
    passphrase: Optional[str] = None

class CredentialListResponse(BaseModel):
    credentials: List[CredentialResponse]
    total: int

# Database connection is now handled by shared.database module

# Authentication is now handled by shared.auth module

# Encryption utilities
def get_encryption_key() -> bytes:
    """Derive encryption key from master key"""
    salt = b"opsconductor_credentials"  # Fixed salt for consistency
    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=32,
        salt=salt,
        iterations=100000,
    )
    key = base64.urlsafe_b64encode(kdf.derive(MASTER_KEY.encode()))
    return key

def encrypt_data(data: Dict[str, Any]) -> str:
    """Encrypt credential data"""
    try:
        key = get_encryption_key()
        f = Fernet(key)
        json_data = json.dumps(data).encode()
        encrypted_data = f.encrypt(json_data)
        return base64.b64encode(encrypted_data).decode()
    except Exception as e:
        logger.error(f"Encryption error: {e}")
        raise DatabaseError("Failed to encrypt credential data")

def decrypt_data(encrypted_data: str) -> Dict[str, Any]:
    """Decrypt credential data"""
    try:
        key = get_encryption_key()
        f = Fernet(key)
        encrypted_bytes = base64.b64decode(encrypted_data.encode())
        decrypted_data = f.decrypt(encrypted_bytes)
        return json.loads(decrypted_data.decode())
    except Exception as e:
        logger.error(f"Decryption error: {e}")
        raise DatabaseError("Failed to decrypt credential data")

def parse_certificate_validity(cert_content: str) -> tuple[Optional[datetime], Optional[datetime]]:
    """Parse certificate to extract validity dates"""
    try:
        # Try different certificate formats
        cert_bytes = cert_content.encode()
        
        # Try PEM format first
        try:
            cert = x509.load_pem_x509_certificate(cert_bytes)
        except:
            # Try DER format
            try:
                cert_bytes = base64.b64decode(cert_content)
                cert = x509.load_der_x509_certificate(cert_bytes)
            except:
                logger.warning("Could not parse certificate for validity dates")
                return None, None
        
        valid_from = cert.not_valid_before_utc
        valid_until = cert.not_valid_after_utc
        
        return valid_from, valid_until
        
    except Exception as e:
        logger.warning(f"Certificate parsing error: {e}")
        return None, None

def encrypt_sensitive_field(value: str) -> str:
    """Encrypt a single sensitive field"""
    if not value:
        return None
    try:
        key = get_encryption_key()
        f = Fernet(key)
        encrypted_data = f.encrypt(value.encode())
        return base64.b64encode(encrypted_data).decode()
    except Exception as e:
        logger.error(f"Field encryption error: {e}")
        raise DatabaseError("Failed to encrypt sensitive data")

def decrypt_sensitive_field(encrypted_value: str) -> str:
    """Decrypt a single sensitive field"""
    if not encrypted_value:
        return None
    try:
        key = get_encryption_key()
        f = Fernet(key)
        encrypted_bytes = base64.b64decode(encrypted_value.encode())
        decrypted_data = f.decrypt(encrypted_bytes)
        return decrypted_data.decode()
    except Exception as e:
        logger.error(f"Field decryption error: {e}")
        raise DatabaseError("Failed to decrypt sensitive data")

# CRUD Operations
@app.post("/credentials", response_model=CredentialResponse, status_code=status.HTTP_201_CREATED)
async def create_credential(
    cred_data: CredentialCreate, 
    request: Request
):
    """Create new encrypted credential"""
    # Check admin/operator role
    current_user = await require_admin_or_operator_role(request)
    try:
        with get_db_cursor() as cursor:
            # Check if credential name already exists
            cursor.execute(
                "SELECT id FROM credentials WHERE name = %s",
                (cred_data.name,)
            )
            if cursor.fetchone():
                raise ValidationError("Credential with this name already exists")
            
            # Validate credential type
            valid_types = ["password", "key", "certificate"]
            if cred_data.credential_type not in valid_types:
                raise ValidationError(f"Invalid credential type. Must be one of: {valid_types}", "credential_type")
            
            # Validate description length
            if cred_data.description and len(cred_data.description) > 20:
                raise ValidationError("Description must be 20 characters or less")
            
            # Validate required fields based on credential type
            if cred_data.credential_type == "password":
                if not cred_data.username or not cred_data.password:
                    raise ValidationError("Username and password are required for password credentials")
            elif cred_data.credential_type == "key":
                if not cred_data.username or not cred_data.private_key:
                    raise ValidationError("Username and private_key are required for key credentials")
            elif cred_data.credential_type == "certificate":
                if not cred_data.certificate:
                    raise ValidationError("Certificate is required for certificate credentials")
            
            # Parse certificate validity dates if certificate is provided
            valid_from = cred_data.valid_from
            valid_until = cred_data.valid_until
            if cred_data.certificate:
                cert_valid_from, cert_valid_until = parse_certificate_validity(cred_data.certificate)
                if cert_valid_from and cert_valid_until:
                    valid_from = cert_valid_from
                    valid_until = cert_valid_until
            
            # Encrypt sensitive fields
            encrypted_password = encrypt_sensitive_field(cred_data.password) if cred_data.password else None
            encrypted_private_key = encrypt_sensitive_field(cred_data.private_key) if cred_data.private_key else None
            encrypted_public_key = encrypt_sensitive_field(cred_data.public_key) if cred_data.public_key else None
            encrypted_certificate = encrypt_sensitive_field(cred_data.certificate) if cred_data.certificate else None
            encrypted_certificate_chain = encrypt_sensitive_field(cred_data.certificate_chain) if cred_data.certificate_chain else None
            encrypted_passphrase = encrypt_sensitive_field(cred_data.passphrase) if cred_data.passphrase else None
            
            # Insert credential
            cursor.execute(
                """INSERT INTO credentials (
                    name, description, credential_type, username, password, domain,
                    private_key, public_key, certificate, certificate_chain, passphrase,
                    valid_from, valid_until, next_rotation_date, created_at, updated_at
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                RETURNING id, name, description, credential_type, username, domain,
                         valid_from, valid_until, next_rotation_date, created_at, updated_at""",
                (
                    cred_data.name,
                    cred_data.description,
                    cred_data.credential_type,
                    cred_data.username,
                    encrypted_password,
                    cred_data.domain,
                    encrypted_private_key,
                    encrypted_public_key,
                    encrypted_certificate,
                    encrypted_certificate_chain,
                    encrypted_passphrase,
                    valid_from,
                    valid_until,
                    cred_data.next_rotation_date,
                    datetime.utcnow(),
                    datetime.utcnow()
                )
            )
            
            new_cred = cursor.fetchone()
            return CredentialResponse(**new_cred)
        
    except HTTPException:
        raise  # Re-raise HTTP exceptions as-is
    except Exception as e:
        logger.error(f"Credential creation error: {e}")
        import traceback
        logger.error(f"Full traceback: {traceback.format_exc()}")
        raise DatabaseError(f"Failed to create credential: {str(e)}")

@app.get("/credentials", response_model=CredentialListResponse)
async def get_credentials(
    request: Request,
    skip: int = 0,
    limit: int = 100
):
    """List all credentials (metadata only, no decrypted data)"""
    # Get user info from headers
    current_user = get_user_from_headers(request)
    try:
        with get_db_cursor(commit=False) as cursor:
            # Get total count
            cursor.execute("SELECT COUNT(*) FROM credentials")
            total = cursor.fetchone()["count"]
            
            # Get credentials with pagination (non-sensitive fields only)
            cursor.execute(
                """SELECT id, name, description, credential_type, username, domain,
                          valid_from, valid_until, next_rotation_date, created_at, updated_at
                   FROM credentials 
                   ORDER BY created_at DESC 
                   LIMIT %s OFFSET %s""",
                (limit, skip)
            )
            credentials = cursor.fetchall()
        
        return CredentialListResponse(
            credentials=[CredentialResponse(**cred) for cred in credentials],
            total=total
        )
        
    except Exception as e:
        logger.error(f"Credential listing error: {e}")
        raise DatabaseError("Failed to retrieve credentials")

@app.get("/credentials/{credential_id}", response_model=CredentialResponse)
async def get_credential(
    credential_id: int, 
    request: Request
):
    """Get credential metadata by ID (no decrypted data)"""
    # Get user info from headers
    current_user = get_user_from_headers(request)
    try:
        with get_db_cursor(commit=False) as cursor:
            cursor.execute(
                """SELECT id, name, description, credential_type, username, domain,
                          valid_from, valid_until, next_rotation_date, created_at, updated_at 
                   FROM credentials WHERE id = %s""",
                (credential_id,)
            )
            cred_data = cursor.fetchone()
            
            if not cred_data:
                raise NotFoundError("Credential not found")
            
            return CredentialResponse(**cred_data)
        
    except Exception as e:
        logger.error(f"Credential retrieval error: {e}")
        raise DatabaseError("Failed to retrieve credential")

@app.get("/credentials/{credential_id}/decrypt", response_model=CredentialDecrypted)
async def get_credential_decrypted(
    credential_id: int, 
    request: Request
):
    """Get credential with decrypted data - ADMIN/OPERATOR ONLY"""
    # Check admin/operator role
    current_user = await require_admin_or_operator_role(request)
    try:
        with get_db_cursor(commit=False) as cursor:
            cursor.execute(
                """SELECT id, name, description, credential_type, username, domain,
                          password, private_key, public_key, certificate, certificate_chain, passphrase,
                          valid_from, valid_until, next_rotation_date, created_at, updated_at 
                   FROM credentials WHERE id = %s""",
                (credential_id,)
            )
            cred_data = cursor.fetchone()
            
            if not cred_data:
                raise NotFoundError("Credential not found")
            
            # Decrypt sensitive fields
            result = dict(cred_data)
            result['password'] = decrypt_sensitive_field(result['password']) if result['password'] else None
            result['private_key'] = decrypt_sensitive_field(result['private_key']) if result['private_key'] else None
            result['public_key'] = decrypt_sensitive_field(result['public_key']) if result['public_key'] else None
            result['certificate'] = decrypt_sensitive_field(result['certificate']) if result['certificate'] else None
            result['certificate_chain'] = decrypt_sensitive_field(result['certificate_chain']) if result['certificate_chain'] else None
            result['passphrase'] = decrypt_sensitive_field(result['passphrase']) if result['passphrase'] else None
            
            return CredentialDecrypted(**result)
        
    except Exception as e:
        logger.error(f"Credential decryption error: {e}")
        raise DatabaseError("Failed to decrypt credential")

@app.put("/credentials/{credential_id}", response_model=CredentialResponse)
async def update_credential(
    credential_id: int,
    cred_data: CredentialUpdate,
    request: Request
):
    """Update credential by ID"""
    # Check admin/operator role
    current_user = await require_admin_or_operator_role(request)
    try:
        with get_db_cursor() as cursor:
            # Check if credential exists (excluding soft-deleted)
            cursor.execute("SELECT id FROM credentials WHERE id = %s AND deleted_at IS NULL", (credential_id,))
            if not cursor.fetchone():
                raise NotFoundError("Credential not found")
            
            # Build update query
            update_fields = []
            update_values = []
            
            if cred_data.name is not None:
                update_fields.append("name = %s")
                update_values.append(cred_data.name)
                
            if cred_data.description is not None:
                update_fields.append("description = %s")
                update_values.append(cred_data.description)
                
            if cred_data.credential_type is not None:
                update_fields.append("credential_type = %s")
                update_values.append(cred_data.credential_type)
                
            if cred_data.credential_data is not None:
                encrypted_data = encrypt_data(cred_data.credential_data)
                credential_json = {"encrypted": encrypted_data}
                update_fields.append("credential_data = %s")
                update_values.append(json.dumps(credential_json))
            
            if not update_fields:
                # No fields to update, just return current credential
                cursor.execute(
                    "SELECT id, name, description, credential_type, created_at, updated_at FROM credentials WHERE id = %s",
                    (credential_id,)
                )
                return CredentialResponse(**cursor.fetchone())
            
            # Add updated_at
            update_fields.append("updated_at = %s")
            update_values.append(datetime.utcnow())
            
            # Execute update
            update_query = f"""
                UPDATE credentials 
                SET {', '.join(update_fields)}
                WHERE id = %s
                RETURNING id, name, description, credential_type, created_at, updated_at
            """
            update_values.append(credential_id)
            
            cursor.execute(update_query, update_values)
            updated_cred = cursor.fetchone()
            
            return CredentialResponse(**updated_cred)
        
    except Exception as e:
        logger.error(f"Credential update error: {e}")
        raise DatabaseError("Failed to update credential")

@app.delete("/credentials/{credential_id}")
async def delete_credential(
    credential_id: int, 
    request: Request
):
    """Delete credential by ID"""
    # Check admin/operator role
    current_user = await require_admin_or_operator_role(request)
    try:
        with get_db_cursor() as cursor:
            # Hard delete credential
            cursor.execute(
                "DELETE FROM credentials WHERE id = %s",
                (credential_id,)
            )
            
            if cursor.rowcount == 0:
                raise NotFoundError("Credential not found or already deleted")
            
            return create_success_response(
                message="Credential deleted successfully",
                data={"credential_id": credential_id}
            )
        
    except Exception as e:
        logger.error(f"Credential deletion error: {e}")
        raise DatabaseError("Failed to delete credential")

@app.post("/credentials/{credential_id}/rotate")
async def rotate_credential(
    credential_id: int,
    new_credential_data: Dict[str, Any],
    request: Request
):
    """Rotate credential data"""
    # Check admin/operator role
    current_user = await require_admin_or_operator_role(request)
    try:
        with get_db_cursor() as cursor:
            # Check if credential exists (excluding soft-deleted)
            cursor.execute("SELECT id FROM credentials WHERE id = %s AND deleted_at IS NULL", (credential_id,))
            if not cursor.fetchone():
                raise NotFoundError("Credential not found")
            
            # Encrypt new credential data and wrap in JSON structure
            encrypted_data = encrypt_data(new_credential_data)
            credential_json = {"encrypted": encrypted_data}
            
            # Update credential
            rotated_at = datetime.utcnow()
            cursor.execute(
                """UPDATE credentials 
                   SET credential_data = %s, updated_at = %s
                   WHERE id = %s""",
                (json.dumps(credential_json), rotated_at, credential_id)
            )
            
            return {
                "message": "Credential rotated successfully",
                "rotated_at": rotated_at.isoformat() + "Z"
            }
        
    except Exception as e:
        logger.error(f"Credential rotation error: {e}")
        raise DatabaseError("Failed to rotate credential")

@app.delete("/credentials/by-name/{credential_name}")
async def delete_credential_by_name(
    credential_name: str,
    request: Request
):
    """Delete credential by name"""
    # Check admin/operator role
    current_user = await require_admin_or_operator_role(request)
    try:
        with get_db_cursor() as cursor:
            # Soft delete credential by name
            cursor.execute(
                "UPDATE credentials SET deleted_at = %s WHERE name = %s AND deleted_at IS NULL",
                (datetime.utcnow(), credential_name)
            )
            
            if cursor.rowcount == 0:
                raise NotFoundError("Credential not found or already deleted")
            
            return create_success_response(
                message="Credential deleted successfully",
                data={"credential_id": credential_id}
            )
        
    except Exception as e:
        logger.error(f"Credential deletion error: {e}")
        raise DatabaseError("Failed to delete credential")

@app.get("/health", response_model=HealthResponse)
async def health_check() -> HealthResponse:
    """Health check endpoint with database connectivity"""
    db_health = check_database_health()
    
    checks = [
        HealthCheck(
            name="database",
            status=db_health["status"],
            message=db_health.get("message", "Database connection check"),
            duration_ms=db_health.get("response_time_ms")
        )
    ]
    
    overall_status = "healthy" if db_health["status"] == "healthy" else "unhealthy"
    
    return HealthResponse(
        service="credentials-service",
        status=overall_status,
        version="1.0.0",
        checks=checks
    )

@app.get("/metrics/database")
async def database_metrics() -> Dict[str, Any]:
    """Database connection pool metrics endpoint"""
    metrics = get_database_metrics()
    return {
        "service": "credentials-service",
        "timestamp": datetime.utcnow().isoformat(),
        "database": metrics
    }

@app.on_event("startup")
async def startup_event() -> None:
    """Log service startup"""
    log_startup("credentials-service", "1.0.0", 3004)

@app.on_event("shutdown")
async def shutdown_event() -> None:
    """Clean up database connections on shutdown"""
    log_shutdown("credentials-service")
    cleanup_database_pool()

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=3004)