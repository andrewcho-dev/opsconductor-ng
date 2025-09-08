---
description: "Security and authentication patterns for OpsConductor services"
globs: ["**/main.py", "**/*service*/**.py", "**/shared/auth.py", "**/shared/encryption.py"]
alwaysApply: false
---

# OpsConductor Security Patterns

## 🔐 Security Architecture

### Core Security Features
- **JWT Authentication**: Stateless token-based authentication with refresh tokens
- **AES-GCM Encryption**: Enterprise-grade encryption for sensitive data
- **RBAC**: Role-based access control with admin/user roles
- **HTTPS/TLS**: SSL termination via NGINX reverse proxy
- **Input Validation**: Comprehensive validation using Pydantic models
- **SQL Injection Prevention**: Parameterized queries throughout

## 🎫 Authentication Patterns

### JWT Token Management
```python
from shared.auth import get_current_user, require_admin, verify_token
from shared.errors import AuthError, PermissionError

# Token verification in endpoints
@app.post("/protected-endpoint")
async def protected_endpoint(request: Request) -> Dict[str, Any]:
    """Protected endpoint requiring valid token"""
    await verify_token(request)  # Raises AuthError if invalid
    # Endpoint logic here
    return create_success_response("Operation completed")

# Get current user information
@app.get("/profile")
async def get_profile(current_user: dict = Depends(get_current_user)) -> Dict[str, Any]:
    """Get current user profile"""
    return create_success_response("Profile retrieved", {
        "user_id": current_user["user_id"],
        "username": current_user["username"],
        "is_admin": current_user["is_admin"]
    })

# Admin-only endpoints
@app.delete("/admin/users/{user_id}")
async def delete_user(user_id: int, current_user: dict = Depends(require_admin)) -> Dict[str, Any]:
    """Admin-only user deletion"""
    # Only admins can reach this point
    result = await user_utility.delete_user(user_id)
    if result:
        return create_success_response("User deleted")
    else:
        raise DatabaseError("Failed to delete user")
```

### Token Refresh Pattern
```python
@app.post("/auth/refresh")
async def refresh_token(request: Request) -> Dict[str, Any]:
    """Refresh JWT token using refresh token"""
    try:
        data = await request.json()
        refresh_token = data.get("refresh_token")
        
        if not refresh_token:
            raise AuthError("Refresh token required")
        
        # Verify refresh token and get new access token
        new_tokens = await auth_utility.refresh_access_token(refresh_token)
        
        if not new_tokens:
            raise AuthError("Invalid or expired refresh token")
        
        return create_success_response("Token refreshed", new_tokens)
        
    except Exception as e:
        logger.error(f"Token refresh failed: {e}")
        raise AuthError("Token refresh failed")
```

## 🔒 Encryption Patterns

### Credential Encryption
```python
from shared.encryption import encrypt_data, decrypt_data

def store_credential(name: str, username: str, password: str) -> Optional[int]:
    """Store credential with AES-GCM encryption"""
    try:
        encrypted_password = encrypt_data(password)
        
        with get_db_cursor() as cursor:
            cursor.execute("""
                INSERT INTO credentials (name, username, encrypted_password)
                VALUES (%s, %s, %s) RETURNING id
            """, (name, username, encrypted_password))
            
            result = cursor.fetchone()
            return result['id'] if result else None
            
    except Exception as e:
        logger.error(f"Failed to store credential: {e}")
        return None

def get_decrypted_credential(credential_id: int) -> Optional[Dict[str, Any]]:
    """Retrieve and decrypt credential"""
    try:
        with get_db_cursor(commit=False) as cursor:
            cursor.execute(
                "SELECT name, username, encrypted_password FROM credentials WHERE id = %s",
                (credential_id,)
            )
            result = cursor.fetchone()
            
            if not result:
                return None
            
            # Decrypt password
            decrypted_password = decrypt_data(result['encrypted_password'])
            
            return {
                'name': result['name'],
                'username': result['username'],
                'password': decrypted_password
            }
            
    except Exception as e:
        logger.error(f"Failed to decrypt credential: {e}")
        return None
```

### Secure Password Handling
```python
from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def hash_password(password: str) -> str:
    """Hash password using bcrypt"""
    return pwd_context.hash(password)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify password against hash"""
    return pwd_context.verify(plain_password, hashed_password)

def create_user_with_secure_password(user_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """Create user with securely hashed password"""
    try:
        # Hash the password
        password_hash = hash_password(user_data['password'])
        
        with get_db_cursor() as cursor:
            cursor.execute("""
                INSERT INTO users (username, email, password_hash, is_admin)
                VALUES (%s, %s, %s, %s) RETURNING id, username, email
            """, (
                user_data['username'],
                user_data['email'],
                password_hash,
                user_data.get('is_admin', False)
            ))
            
            return cursor.fetchone()
            
    except Exception as e:
        logger.error(f"Failed to create user: {e}")
        return None
```

## 🛡️ Input Validation Patterns

### Pydantic Model Validation
```python
from pydantic import BaseModel, validator, EmailStr
from typing import Optional

class UserCreate(BaseModel):
    username: str
    email: EmailStr
    password: str
    is_admin: Optional[bool] = False
    
    @validator('username')
    def validate_username(cls, v):
        if len(v) < 3:
            raise ValueError('Username must be at least 3 characters')
        if not v.isalnum():
            raise ValueError('Username must be alphanumeric')
        return v
    
    @validator('password')
    def validate_password(cls, v):
        if len(v) < 8:
            raise ValueError('Password must be at least 8 characters')
        if not any(c.isupper() for c in v):
            raise ValueError('Password must contain at least one uppercase letter')
        if not any(c.islower() for c in v):
            raise ValueError('Password must contain at least one lowercase letter')
        if not any(c.isdigit() for c in v):
            raise ValueError('Password must contain at least one digit')
        return v

class TargetCreate(BaseModel):
    name: str
    host: str
    port: Optional[int] = None
    platform: str
    credential_id: int
    group_id: Optional[int] = None
    
    @validator('name')
    def validate_name(cls, v):
        if len(v) < 1:
            raise ValueError('Name is required')
        if len(v) > 255:
            raise ValueError('Name must be less than 255 characters')
        return v
    
    @validator('host')
    def validate_host(cls, v):
        import re
        # Basic IP address or hostname validation
        ip_pattern = r'^(?:[0-9]{1,3}\.){3}[0-9]{1,3}$'
        hostname_pattern = r'^[a-zA-Z0-9]([a-zA-Z0-9\-]{0,61}[a-zA-Z0-9])?(\.[a-zA-Z0-9]([a-zA-Z0-9\-]{0,61}[a-zA-Z0-9])?)*$'
        
        if not (re.match(ip_pattern, v) or re.match(hostname_pattern, v)):
            raise ValueError('Invalid host format')
        return v
    
    @validator('platform')
    def validate_platform(cls, v):
        if v not in ['windows', 'linux']:
            raise ValueError('Platform must be either "windows" or "linux"')
        return v
```

### Endpoint Validation
```python
@app.post("/users", response_model=Dict[str, Any])
async def create_user(user_data: UserCreate, request: Request) -> Dict[str, Any]:
    """Create user with comprehensive validation"""
    await verify_token(request)
    
    # Additional business logic validation
    existing_user = await user_utility.get_user_by_username(user_data.username)
    if existing_user:
        raise ValidationError("Username already exists", "username")
    
    existing_email = await user_utility.get_user_by_email(user_data.email)
    if existing_email:
        raise ValidationError("Email already exists", "email")
    
    # Create user
    result = await user_utility.create_user(user_data.dict())
    if result:
        return create_success_response("User created", result)
    else:
        raise DatabaseError("Failed to create user")
```

## 🔍 Authorization Patterns

### Role-Based Access Control
```python
def check_resource_ownership(user_id: int, resource_id: int, resource_type: str) -> bool:
    """Check if user owns the resource"""
    try:
        with get_db_cursor(commit=False) as cursor:
            if resource_type == "job":
                cursor.execute(
                    "SELECT created_by FROM jobs WHERE id = %s",
                    (resource_id,)
                )
            elif resource_type == "target":
                cursor.execute(
                    "SELECT created_by FROM targets WHERE id = %s",
                    (resource_id,)
                )
            else:
                return False
            
            result = cursor.fetchone()
            return result and result['created_by'] == user_id
            
    except Exception as e:
        logger.error(f"Failed to check resource ownership: {e}")
        return False

@app.delete("/jobs/{job_id}")
async def delete_job(job_id: int, current_user: dict = Depends(get_current_user)) -> Dict[str, Any]:
    """Delete job with ownership check"""
    # Admin can delete any job
    if not current_user['is_admin']:
        # Regular users can only delete their own jobs
        if not check_resource_ownership(current_user['user_id'], job_id, 'job'):
            raise PermissionError("You can only delete your own jobs")
    
    result = await job_utility.delete_job(job_id)
    if result:
        return create_success_response("Job deleted")
    else:
        raise DatabaseError("Failed to delete job")
```

## 🌐 HTTPS and SSL Patterns

### NGINX SSL Configuration
```nginx
# nginx/nginx.conf
server {
    listen 80;
    server_name localhost;
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name localhost;
    
    ssl_certificate /etc/nginx/ssl/cert.pem;
    ssl_certificate_key /etc/nginx/ssl/key.pem;
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers ECDHE-RSA-AES256-GCM-SHA512:DHE-RSA-AES256-GCM-SHA512;
    ssl_prefer_server_ciphers off;
    
    # Security headers
    add_header X-Frame-Options DENY;
    add_header X-Content-Type-Options nosniff;
    add_header X-XSS-Protection "1; mode=block";
    add_header Strict-Transport-Security "max-age=63072000; includeSubDomains; preload";
    
    location / {
        proxy_pass http://frontend:3000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

### Service-to-Service Authentication
```python
from shared.utils import get_service_client

async def call_auth_service(endpoint: str, data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """Make authenticated call to auth service"""
    try:
        client = get_service_client("auth-service")
        response = await client.post(endpoint, json=data)
        
        if response.status_code == 200:
            return response.json()
        else:
            logger.error(f"Auth service call failed: {response.status_code}")
            return None
            
    except Exception as e:
        logger.error(f"Failed to call auth service: {e}")
        return None
```

## 🧪 Security Testing Patterns

### Authentication Testing
```python
def test_protected_endpoint_without_token():
    """Test that protected endpoint rejects requests without token"""
    response = client.post("/protected-endpoint", json={"data": "test"})
    assert response.status_code == 401
    assert "error" in response.json()
    assert response.json()["error"]["type"] == "AuthError"

def test_protected_endpoint_with_invalid_token():
    """Test that protected endpoint rejects invalid tokens"""
    response = client.post(
        "/protected-endpoint",
        json={"data": "test"},
        headers={"Authorization": "Bearer invalid-token"}
    )
    assert response.status_code == 401

def test_admin_endpoint_with_regular_user():
    """Test that admin endpoint rejects regular users"""
    with patch('shared.auth.get_current_user') as mock_user:
        mock_user.return_value = {"user_id": 1, "username": "user", "is_admin": False}
        
        response = client.delete("/admin/users/2")
        assert response.status_code == 403
        assert response.json()["error"]["type"] == "PermissionError"
```

### Encryption Testing
```python
def test_credential_encryption_decryption():
    """Test credential encryption and decryption"""
    original_password = "test-password-123"
    
    # Store encrypted credential
    credential_id = store_credential("test-cred", "testuser", original_password)
    assert credential_id is not None
    
    # Retrieve and decrypt
    credential = get_decrypted_credential(credential_id)
    assert credential is not None
    assert credential['password'] == original_password
```

## 🚨 Security Best Practices

### Secure Coding Guidelines
- **Never log sensitive data** (passwords, tokens, encrypted data)
- **Use parameterized queries** to prevent SQL injection
- **Validate all input** using Pydantic models
- **Implement proper error handling** without exposing internal details
- **Use HTTPS for all communications**
- **Rotate encryption keys** regularly
- **Implement rate limiting** for authentication endpoints
- **Use secure session management** with proper token expiration

### Common Security Pitfalls to Avoid
```python
# ❌ WRONG: Logging sensitive data
logger.info(f"User password: {password}")

# ✅ CORRECT: Log without sensitive data
logger.info(f"User authentication attempt for: {username}")

# ❌ WRONG: SQL injection vulnerability
cursor.execute(f"SELECT * FROM users WHERE username = '{username}'")

# ✅ CORRECT: Parameterized query
cursor.execute("SELECT * FROM users WHERE username = %s", (username,))

# ❌ WRONG: Exposing internal errors
raise HTTPException(status_code=500, detail=str(e))

# ✅ CORRECT: Generic error message
raise DatabaseError("Operation failed")
```

## 📊 Security Monitoring

### Audit Logging
```python
def log_security_event(event_type: str, user_id: int, details: Dict[str, Any]):
    """Log security-related events for audit purposes"""
    try:
        with get_db_cursor() as cursor:
            cursor.execute("""
                INSERT INTO security_audit_log (event_type, user_id, details, timestamp)
                VALUES (%s, %s, %s, CURRENT_TIMESTAMP)
            """, (event_type, user_id, json.dumps(details)))
    except Exception as e:
        logger.error(f"Failed to log security event: {e}")

# Usage in authentication
async def authenticate_user(username: str, password: str) -> Optional[Dict[str, Any]]:
    """Authenticate user with audit logging"""
    user = await get_user_by_username(username)
    
    if user and verify_password(password, user['password_hash']):
        log_security_event("LOGIN_SUCCESS", user['id'], {"username": username})
        return user
    else:
        log_security_event("LOGIN_FAILURE", 0, {"username": username, "ip": get_client_ip()})
        return None
```

---

**Follow these security patterns to maintain enterprise-grade security across all OpsConductor services and protect sensitive automation credentials and data.**