#!/usr/bin/env python3
"""
Credentials Service - Python FastAPI Implementation
Encrypted credential storage with full CRUD operations
"""

import os
import json
import base64
import logging
from datetime import datetime
from typing import List, Optional, Dict, Any

import psycopg2
import psycopg2.extras
import requests
from fastapi import FastAPI, HTTPException, Depends, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Logging setup
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# FastAPI app
app = FastAPI(title="Credentials Service", version="1.0.0")

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Security
security = HTTPBearer()

# Configuration
AUTH_SERVICE_URL = os.getenv("AUTH_SERVICE_URL", "http://auth-service:3001")
MASTER_KEY = os.getenv("MASTER_KEY", "default-key-change-in-production")

# Database configuration
DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = os.getenv("DB_PORT", "5432")
DB_NAME = os.getenv("DB_NAME", "opsconductor")
DB_USER = os.getenv("DB_USER", "postgres")
DB_PASSWORD = os.getenv("DB_PASSWORD", "postgres")

# Pydantic models
class CredentialCreate(BaseModel):
    name: str
    description: Optional[str] = None
    credential_type: str  # 'winrm', 'ssh', 'api_key', etc.
    credential_data: Dict[str, Any]  # Raw credential data to encrypt

class CredentialUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    credential_type: Optional[str] = None
    credential_data: Optional[Dict[str, Any]] = None

class CredentialResponse(BaseModel):
    id: int
    name: str
    description: Optional[str]
    credential_type: str
    created_at: datetime
    updated_at: Optional[datetime]

class CredentialDecrypted(CredentialResponse):
    credential_data: Dict[str, Any]

class CredentialListResponse(BaseModel):
    credentials: List[CredentialResponse]
    total: int

# Database connection
def get_db_connection():
    """Get database connection"""
    try:
        conn = psycopg2.connect(
            host=DB_HOST,
            port=DB_PORT,
            database=DB_NAME,
            user=DB_USER,
            password=DB_PASSWORD,
            cursor_factory=psycopg2.extras.RealDictCursor
        )
        return conn
    except Exception as e:
        logger.error(f"Database connection error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Database connection failed"
        )

# Authentication
def verify_token_with_auth_service(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Verify token with auth service"""
    try:
        headers = {"Authorization": f"Bearer {credentials.credentials}"}
        response = requests.get(f"{AUTH_SERVICE_URL}/verify", headers=headers, timeout=5)
        
        if response.status_code != 200:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token"
            )
            
        return response.json()["user"]
        
    except requests.RequestException:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Auth service unavailable"
        )

def require_admin_or_operator_role(current_user: dict = Depends(verify_token_with_auth_service)):
    """Require admin or operator role"""
    if current_user["role"] not in ["admin", "operator"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin or operator role required"
        )
    return current_user

# Encryption utilities
def get_encryption_key():
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
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to encrypt credential data"
        )

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
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to decrypt credential data"
        )

# CRUD Operations
@app.post("/credentials", response_model=CredentialResponse, status_code=status.HTTP_201_CREATED)
async def create_credential(
    cred_data: CredentialCreate, 
    current_user: dict = Depends(require_admin_or_operator_role)
):
    """Create new encrypted credential"""
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        
        # Check if credential name already exists
        cursor.execute(
            "SELECT id FROM credentials WHERE name = %s AND deleted_at IS NULL",
            (cred_data.name,)
        )
        if cursor.fetchone():
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Credential with this name already exists"
            )
        
        # Validate credential type and required fields
        valid_types = ["winrm", "ssh", "ssh_key", "api_key", "certificate", "database", "snmp"]
        if cred_data.credential_type not in valid_types:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid credential type. Must be one of: {valid_types}"
            )
        
        # Validate required fields based on credential type
        if cred_data.credential_type == "ssh_key":
            required_fields = ["username", "private_key"]
            for field in required_fields:
                if field not in cred_data.credential_data:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail=f"Missing required field for ssh_key credential: {field}"
                    )
        elif cred_data.credential_type == "api_key":
            required_fields = ["api_key"]
            for field in required_fields:
                if field not in cred_data.credential_data:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail=f"Missing required field for api_key credential: {field}"
                    )
        elif cred_data.credential_type == "certificate":
            required_fields = ["certificate"]
            for field in required_fields:
                if field not in cred_data.credential_data:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail=f"Missing required field for certificate credential: {field}"
                    )
        
        # Encrypt credential data and wrap in JSON structure
        encrypted_data = encrypt_data(cred_data.credential_data)
        credential_json = {"encrypted": encrypted_data}
        
        # Insert credential
        cursor.execute(
            """INSERT INTO credentials (name, description, credential_type, credential_data, created_at, updated_at)
               VALUES (%s, %s, %s, %s, %s, %s)
               RETURNING id, name, description, credential_type, created_at, updated_at""",
            (
                cred_data.name,
                cred_data.description,
                cred_data.credential_type,
                json.dumps(credential_json),
                datetime.utcnow(),
                datetime.utcnow()
            )
        )
        
        new_cred = cursor.fetchone()
        conn.commit()
        
        return CredentialResponse(**new_cred)
        
    except HTTPException:
        conn.rollback()
        raise  # Re-raise HTTP exceptions as-is
    except Exception as e:
        conn.rollback()
        logger.error(f"Credential creation error: {e}")
        import traceback
        logger.error(f"Full traceback: {traceback.format_exc()}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create credential: {str(e)}"
        )
    finally:
        conn.close()

@app.get("/credentials", response_model=CredentialListResponse)
async def list_credentials(
    skip: int = 0,
    limit: int = 100,
    current_user: dict = Depends(verify_token_with_auth_service)
):
    """List all credentials (metadata only, no decrypted data)"""
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        
        # Get total count (excluding soft-deleted)
        cursor.execute("SELECT COUNT(*) FROM credentials WHERE deleted_at IS NULL")
        total = cursor.fetchone()["count"]
        
        # Get credentials with pagination (excluding soft-deleted)
        cursor.execute(
            """SELECT id, name, description, credential_type, created_at, updated_at
               FROM credentials 
               WHERE deleted_at IS NULL
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
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve credentials"
        )
    finally:
        conn.close()

@app.get("/credentials/{credential_id}", response_model=CredentialResponse)
async def get_credential(
    credential_id: int, 
    current_user: dict = Depends(verify_token_with_auth_service)
):
    """Get credential metadata by ID (no decrypted data)"""
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT id, name, description, credential_type, created_at, updated_at FROM credentials WHERE id = %s AND deleted_at IS NULL",
            (credential_id,)
        )
        cred_data = cursor.fetchone()
        
        if not cred_data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Credential not found"
            )
        
        return CredentialResponse(**cred_data)
        
    except Exception as e:
        logger.error(f"Credential retrieval error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve credential"
        )
    finally:
        conn.close()

@app.get("/credentials/{credential_id}/decrypt", response_model=CredentialDecrypted)
async def get_credential_decrypted(
    credential_id: int, 
    current_user: dict = Depends(require_admin_or_operator_role)
):
    """Get credential with decrypted data - ADMIN/OPERATOR ONLY"""
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT id, name, description, credential_type, created_at, updated_at, credential_data FROM credentials WHERE id = %s AND deleted_at IS NULL",
            (credential_id,)
        )
        cred_data = cursor.fetchone()
        
        if not cred_data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Credential not found"
            )
        
        # Decrypt credential data
        credential_json = cred_data.pop("credential_data")
        if isinstance(credential_json, str):
            credential_json = json.loads(credential_json)
        
        # Handle sample data that has placeholder values
        encrypted_data = credential_json.get("encrypted")
        if encrypted_data is True or encrypted_data == "" or not encrypted_data:
            # This is sample/placeholder data, return empty credential data
            decrypted_data = {"note": "This is sample data - no actual credentials stored"}
        else:
            # This is real encrypted data
            decrypted_data = decrypt_data(encrypted_data)
        
        return CredentialDecrypted(
            **cred_data,
            credential_data=decrypted_data
        )
        
    except Exception as e:
        logger.error(f"Credential decryption error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to decrypt credential"
        )
    finally:
        conn.close()

@app.put("/credentials/{credential_id}", response_model=CredentialResponse)
async def update_credential(
    credential_id: int,
    cred_data: CredentialUpdate,
    current_user: dict = Depends(require_admin_or_operator_role)
):
    """Update credential by ID"""
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        
        # Check if credential exists (excluding soft-deleted)
        cursor.execute("SELECT id FROM credentials WHERE id = %s AND deleted_at IS NULL", (credential_id,))
        if not cursor.fetchone():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Credential not found"
            )
        
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
        conn.commit()
        
        return CredentialResponse(**updated_cred)
        
    except Exception as e:
        conn.rollback()
        logger.error(f"Credential update error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update credential"
        )
    finally:
        conn.close()

@app.delete("/credentials/{credential_id}")
async def delete_credential(
    credential_id: int, 
    current_user: dict = Depends(require_admin_or_operator_role)
):
    """Delete credential by ID"""
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        
        # Soft delete credential (no need to check target references anymore)
        cursor.execute(
            "UPDATE credentials SET deleted_at = %s WHERE id = %s AND deleted_at IS NULL",
            (datetime.utcnow(), credential_id)
        )
        
        if cursor.rowcount == 0:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Credential not found or already deleted"
            )
        
        conn.commit()
        
        return {"message": "Credential deleted successfully"}
        
    except Exception as e:
        conn.rollback()
        logger.error(f"Credential deletion error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete credential"
        )
    finally:
        conn.close()

@app.post("/credentials/{credential_id}/rotate")
async def rotate_credential(
    credential_id: int,
    new_credential_data: Dict[str, Any],
    current_user: dict = Depends(require_admin_or_operator_role)
):
    """Rotate credential data"""
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        
        # Check if credential exists (excluding soft-deleted)
        cursor.execute("SELECT id FROM credentials WHERE id = %s AND deleted_at IS NULL", (credential_id,))
        if not cursor.fetchone():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Credential not found"
            )
        
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
        conn.commit()
        
        return {
            "message": "Credential rotated successfully",
            "rotated_at": rotated_at.isoformat() + "Z"
        }
        
    except Exception as e:
        conn.rollback()
        logger.error(f"Credential rotation error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to rotate credential"
        )
    finally:
        conn.close()

@app.delete("/credentials/by-name/{credential_name}")
async def delete_credential_by_name(
    credential_name: str,
    current_user: dict = Depends(require_admin_or_operator_role)
):
    """Delete credential by name"""
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        
        # Soft delete credential by name
        cursor.execute(
            "UPDATE credentials SET deleted_at = %s WHERE name = %s AND deleted_at IS NULL",
            (datetime.utcnow(), credential_name)
        )
        
        if cursor.rowcount == 0:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Credential not found or already deleted"
            )
        
        conn.commit()
        
        return {"message": "Credential deleted successfully"}
        
    except Exception as e:
        conn.rollback()
        logger.error(f"Credential deletion error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete credential"
        )
    finally:
        conn.close()

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "service": "credentials-service"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=3004)