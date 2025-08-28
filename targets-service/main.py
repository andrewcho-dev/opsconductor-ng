#!/usr/bin/env python3
"""
Targets Service - Python FastAPI Implementation
Target management with WinRM connection testing
"""

import os
import json
import logging
from datetime import datetime
from typing import List, Optional, Dict, Any

import psycopg2
import psycopg2.extras
import requests
import winrm
from fastapi import FastAPI, HTTPException, Depends, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Logging setup
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# FastAPI app
app = FastAPI(title="Targets Service", version="1.0.0")

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
CREDENTIALS_SERVICE_URL = os.getenv("CREDENTIALS_SERVICE_URL", "http://credentials-service:3004")

# Database configuration
DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = os.getenv("DB_PORT", "5432")
DB_NAME = os.getenv("DB_NAME", "opsconductor")
DB_USER = os.getenv("DB_USER", "postgres")
DB_PASSWORD = os.getenv("DB_PASSWORD", "postgres")

# Pydantic models
class TargetCreate(BaseModel):
    name: str
    hostname: str
    protocol: str = "winrm"  # 'winrm', 'ssh', 'http'
    port: int = 5985
    credential_ref: int  # Reference to credentials table
    tags: Optional[List[str]] = []
    metadata: Optional[Dict[str, Any]] = {}
    depends_on: Optional[List[int]] = []

class TargetUpdate(BaseModel):
    name: Optional[str] = None
    hostname: Optional[str] = None
    protocol: Optional[str] = None
    port: Optional[int] = None
    credential_ref: Optional[int] = None
    tags: Optional[List[str]] = None
    metadata: Optional[Dict[str, Any]] = None
    depends_on: Optional[List[int]] = None

class TargetResponse(BaseModel):
    id: int
    name: str
    hostname: str
    protocol: str
    port: int
    credential_ref: int
    tags: List[str]
    metadata: Dict[str, Any]
    depends_on: List[int]
    created_at: datetime

class TargetListResponse(BaseModel):
    targets: List[TargetResponse]
    total: int

class WinRMTestResult(BaseModel):
    test: Dict[str, Any]
    note: str

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

# Helper functions
async def get_credential_data(credential_id: int, token: str) -> Dict[str, Any]:
    """Get decrypted credential data from credentials service"""
    try:
        headers = {"Authorization": f"Bearer {token}"}
        response = requests.get(
            f"{CREDENTIALS_SERVICE_URL}/credentials/{credential_id}/decrypt",
            headers=headers,
            timeout=10
        )
        
        if response.status_code != 200:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid credential reference"
            )
            
        return response.json()["credential_data"]
        
    except requests.RequestException:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Credentials service unavailable"
        )

# CRUD Operations
@app.post("/targets", response_model=TargetResponse, status_code=status.HTTP_201_CREATED)
async def create_target(
    target_data: TargetCreate,
    current_user: dict = Depends(require_admin_or_operator_role)
):
    """Create new target"""
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        
        # Check if target name already exists
        cursor.execute("SELECT id FROM targets WHERE name = %s", (target_data.name,))
        if cursor.fetchone():
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Target with this name already exists"
            )
        
        # Verify credential exists
        cursor.execute("SELECT id FROM credentials WHERE id = %s", (target_data.credential_ref,))
        if not cursor.fetchone():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid credential reference"
            )
        
        # Insert target
        cursor.execute(
            """INSERT INTO targets (name, hostname, protocol, port, credential_ref, tags, metadata, depends_on, created_at)
               VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
               RETURNING id, name, hostname, protocol, port, credential_ref, tags, metadata, depends_on, created_at""",
            (
                target_data.name,
                target_data.hostname,
                target_data.protocol,
                target_data.port,
                target_data.credential_ref,
                target_data.tags or [],  # PostgreSQL array type
                json.dumps(target_data.metadata or {}),  # JSONB type
                target_data.depends_on or [],  # PostgreSQL array type
                datetime.utcnow()
            )
        )
        
        new_target = cursor.fetchone()
        conn.commit()
        
        # Parse fields for response (only metadata needs JSON parsing)
        target_dict = dict(new_target)
        target_dict['tags'] = target_dict.get('tags', [])  # Already a list from PostgreSQL
        target_dict['metadata'] = target_dict.get('metadata', {})  # Already parsed by psycopg2 for JSONB
        target_dict['depends_on'] = target_dict.get('depends_on', [])  # Already a list from PostgreSQL
        
        return TargetResponse(**target_dict)
        
    except Exception as e:
        conn.rollback()
        logger.error(f"Target creation error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create target"
        )
    finally:
        conn.close()

@app.get("/targets", response_model=TargetListResponse)
async def list_targets(
    skip: int = 0,
    limit: int = 100,
    current_user: dict = Depends(verify_token_with_auth_service)
):
    """List all targets with pagination"""
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        
        # Get total count
        cursor.execute("SELECT COUNT(*) FROM targets")
        total = cursor.fetchone()["count"]
        
        # Get targets with pagination
        cursor.execute(
            """SELECT id, name, hostname, protocol, port, credential_ref, tags, metadata, depends_on, created_at
               FROM targets 
               ORDER BY created_at DESC 
               LIMIT %s OFFSET %s""",
            (limit, skip)
        )
        targets = cursor.fetchall()
        
        # Parse fields (PostgreSQL arrays are already lists, JSONB is already parsed)
        parsed_targets = []
        for target in targets:
            target_dict = dict(target)
            target_dict['tags'] = target_dict.get('tags', [])  # Already a list
            target_dict['metadata'] = target_dict.get('metadata', {})  # Already parsed 
            target_dict['depends_on'] = target_dict.get('depends_on', [])  # Already a list
            parsed_targets.append(target_dict)
        
        return TargetListResponse(
            targets=[TargetResponse(**target) for target in parsed_targets],
            total=total
        )
        
    except Exception as e:
        logger.error(f"Target listing error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve targets"
        )
    finally:
        conn.close()

@app.get("/targets/{target_id}", response_model=TargetResponse)
async def get_target(target_id: int, current_user: dict = Depends(verify_token_with_auth_service)):
    """Get target by ID"""
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT id, name, hostname, protocol, port, credential_ref, tags, metadata, depends_on, created_at FROM targets WHERE id = %s",
            (target_id,)
        )
        target_data = cursor.fetchone()
        
        if not target_data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Target not found"
            )
        
        # Parse fields for response
        target_dict = dict(target_data)
        target_dict['tags'] = target_dict.get('tags', [])  # Already a list
        target_dict['metadata'] = target_dict.get('metadata', {})  # Already parsed
        target_dict['depends_on'] = target_dict.get('depends_on', [])  # Already a list
        
        return TargetResponse(**target_dict)
        
    except Exception as e:
        logger.error(f"Target retrieval error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve target"
        )
    finally:
        conn.close()

@app.put("/targets/{target_id}", response_model=TargetResponse)
async def update_target(
    target_id: int,
    target_data: TargetUpdate,
    current_user: dict = Depends(require_admin_or_operator_role)
):
    """Update target by ID"""
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        
        # Check if target exists
        cursor.execute("SELECT id FROM targets WHERE id = %s", (target_id,))
        if not cursor.fetchone():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Target not found"
            )
        
        # Build update query
        update_fields = []
        update_values = []
        
        if target_data.name is not None:
            update_fields.append("name = %s")
            update_values.append(target_data.name)
            
        if target_data.hostname is not None:
            update_fields.append("hostname = %s")
            update_values.append(target_data.hostname)
            
        if target_data.protocol is not None:
            update_fields.append("protocol = %s")
            update_values.append(target_data.protocol)
            
        if target_data.port is not None:
            update_fields.append("port = %s")
            update_values.append(target_data.port)
            
        if target_data.credential_ref is not None:
            # Verify credential exists
            cursor.execute("SELECT id FROM credentials WHERE id = %s", (target_data.credential_ref,))
            if not cursor.fetchone():
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Invalid credential reference"
                )
            update_fields.append("credential_ref = %s")
            update_values.append(target_data.credential_ref)
            
        if target_data.tags is not None:
            update_fields.append("tags = %s")
            update_values.append(target_data.tags)  # PostgreSQL array type
            
        if target_data.metadata is not None:
            update_fields.append("metadata = %s")
            update_values.append(json.dumps(target_data.metadata))  # JSONB type
            
        if target_data.depends_on is not None:
            update_fields.append("depends_on = %s")
            update_values.append(target_data.depends_on)  # PostgreSQL array type
        
        if not update_fields:
            # No fields to update, just return current target
            cursor.execute(
                "SELECT id, name, hostname, protocol, port, credential_ref, tags, metadata, depends_on, created_at FROM targets WHERE id = %s",
                (target_id,)
            )
            target = cursor.fetchone()
            target_dict = dict(target)
            target_dict['tags'] = target_dict.get('tags', [])  # Already a list
            target_dict['metadata'] = target_dict.get('metadata', {})  # Already parsed
            target_dict['depends_on'] = target_dict.get('depends_on', [])  # Already a list
            return TargetResponse(**target_dict)
        
        # Execute update
        update_query = f"""
            UPDATE targets 
            SET {', '.join(update_fields)}
            WHERE id = %s
            RETURNING id, name, hostname, protocol, port, credential_ref, tags, metadata, depends_on, created_at
        """
        update_values.append(target_id)
        
        cursor.execute(update_query, update_values)
        updated_target = cursor.fetchone()
        conn.commit()
        
        # Parse fields for response
        target_dict = dict(updated_target)
        target_dict['tags'] = target_dict.get('tags', [])  # Already a list
        target_dict['metadata'] = target_dict.get('metadata', {})  # Already parsed
        target_dict['depends_on'] = target_dict.get('depends_on', [])  # Already a list
        
        return TargetResponse(**target_dict)
        
    except Exception as e:
        conn.rollback()
        logger.error(f"Target update error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update target"
        )
    finally:
        conn.close()

@app.delete("/targets/{target_id}")
async def delete_target(
    target_id: int,
    current_user: dict = Depends(require_admin_or_operator_role)
):
    """Delete target by ID"""
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        
        # Check if target exists
        cursor.execute("SELECT id FROM targets WHERE id = %s", (target_id,))
        if not cursor.fetchone():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Target not found"
            )
        
        # Check if target is referenced by jobs
        cursor.execute("SELECT id FROM job_run_steps WHERE target_id = %s LIMIT 1", (target_id,))
        if cursor.fetchone():
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Cannot delete target: it is referenced by jobs"
            )
        
        # Delete target
        cursor.execute("DELETE FROM targets WHERE id = %s", (target_id,))
        conn.commit()
        
        return {"message": "Target deleted successfully"}
        
    except Exception as e:
        conn.rollback()
        logger.error(f"Target deletion error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete target"
        )
    finally:
        conn.close()

@app.delete("/targets/by-name/{target_name}")
async def delete_target_by_name(
    target_name: str,
    current_user: dict = Depends(require_admin_or_operator_role)
):
    """Delete target by name"""
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        
        # Check if target exists
        cursor.execute("SELECT id FROM targets WHERE name = %s", (target_name,))
        target = cursor.fetchone()
        
        if not target:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Target not found"
            )
        
        target_id = target['id']
        
        # Check if target is referenced by jobs
        cursor.execute("SELECT id FROM job_run_steps WHERE target_id = %s LIMIT 1", (target_id,))
        if cursor.fetchone():
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Cannot delete target: it is referenced by jobs"
            )
        
        # Delete target
        cursor.execute("DELETE FROM targets WHERE name = %s", (target_name,))
        conn.commit()
        
        return {"message": "Target deleted successfully"}
        
    except HTTPException:
        conn.rollback()
        raise
    except Exception as e:
        conn.rollback()
        logger.error(f"Target deletion error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete target"
        )
    finally:
        conn.close()

@app.post("/targets/{target_id}/test-winrm", response_model=WinRMTestResult)
async def test_winrm_connection(
    target_id: int,
    credentials: HTTPAuthorizationCredentials = Depends(security),
    current_user: dict = Depends(verify_token_with_auth_service)
):
    """Test WinRM connection to target"""
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        
        # Get target info
        cursor.execute(
            "SELECT hostname, port, credential_ref, protocol FROM targets WHERE id = %s",
            (target_id,)
        )
        target_data = cursor.fetchone()
        
        if not target_data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Target not found"
            )
        
        if target_data["protocol"] != "winrm":
            return WinRMTestResult(
                test={
                    "status": "error",
                    "details": {
                        "message": "Target is not configured for WinRM protocol"
                    }
                },
                note="Target protocol is not WinRM"
            )
        
        # Get credential data for the connection
        try:
            credential_data = await get_credential_data(
                target_data["credential_ref"], 
                credentials.credentials
            )
        except Exception as e:
            return WinRMTestResult(
                test={
                    "status": "error",
                    "details": {
                        "message": f"Failed to retrieve credentials: {str(e)}"
                    }
                },
                note="Credential retrieval failed"
            )
        
        # Perform actual WinRM connection test
        try:
            # Use HTTP for port 5985, HTTPS for port 5986
            protocol = 'https' if target_data['port'] == 5986 else 'http'
            winrm_url = f"{protocol}://{target_data['hostname']}:{target_data['port']}/wsman"
            
            logger.info(f"Testing WinRM connection to: {winrm_url}")
            
            # Create WinRM session
            session = winrm.Session(
                target=winrm_url,
                auth=(credential_data['username'], credential_data['password']),
                transport='ntlm',
                server_cert_validation='ignore'
            )
            
            # Test connection with a simple command
            result = session.run_ps("$PSVersionTable.PSVersion.ToString(); whoami; hostname")
            
            if result.status_code == 0:
                # Parse output for details
                output_lines = result.std_out.decode('utf-8', errors='replace').strip().split('\n')
                ps_version = output_lines[0].strip() if len(output_lines) > 0 else "Unknown"
                whoami = output_lines[1].strip() if len(output_lines) > 1 else "Unknown"
                hostname = output_lines[2].strip() if len(output_lines) > 2 else target_data['hostname']
                
                return WinRMTestResult(
                    test={
                        "status": "success",
                        "details": {
                            "whoami": whoami,
                            "powershellVersion": ps_version,
                            "hostname": hostname,
                            "port": target_data["port"],
                            "transport": "ntlm",
                            "protocol": protocol,
                            "connection_time": "< 1s"
                        }
                    },
                    note="WinRM connection test successful"
                )
            else:
                # Connection failed
                stderr = result.std_err.decode('utf-8', errors='replace') if result.std_err else "Unknown error"
                return WinRMTestResult(
                    test={
                        "status": "error",
                        "details": {
                            "message": f"WinRM command failed with exit code {result.status_code}",
                            "stderr": stderr,
                            "hostname": target_data['hostname'],
                            "port": target_data['port']
                        }
                    },
                    note="WinRM connection established but command execution failed"
                )
                
        except Exception as winrm_error:
            logger.error(f"WinRM connection test failed: {winrm_error}")
            return WinRMTestResult(
                test={
                    "status": "error",
                    "details": {
                        "message": f"WinRM connection failed: {str(winrm_error)}",
                        "hostname": target_data['hostname'],
                        "port": target_data['port'],
                        "protocol": protocol if 'protocol' in locals() else 'unknown'
                    }
                },
                note="WinRM connection test failed - check network connectivity, credentials, and WinRM configuration"
            )
            
    except Exception as e:
        logger.error(f"Target test error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to test target connection"
        )
    finally:
        conn.close()

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "service": "targets-service"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=3005)