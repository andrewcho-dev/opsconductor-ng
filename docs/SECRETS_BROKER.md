# Secrets Broker - Server-Side Credential Management

## Overview

The Secrets Broker provides secure, server-side storage and retrieval of host credentials for tool execution. It ensures that passwords and sensitive data **never reach the browser** while enabling seamless, automated tool execution.

## Architecture

```
┌──────────────────────────────────────────────────────────────┐
│                    Secrets Broker                            │
│                                                              │
│  ┌────────────────────────────────────────────────────────┐ │
│  │ SecretsManager (secrets_broker.py)                     │ │
│  │                                                        │ │
│  │  • AES-256-GCM encryption                             │ │
│  │  • PBKDF2 key derivation                              │ │
│  │  • Audit logging                                      │ │
│  └────────────────────────────────────────────────────────┘ │
│                                                              │
│  ┌────────────────────────────────────────────────────────┐ │
│  │ Internal API (routes/secrets.py)                       │ │
│  │                                                        │ │
│  │  POST /internal/secrets/credential-upsert             │ │
│  │  POST /internal/secrets/credential-lookup             │ │
│  │  DELETE /internal/secrets/credential-delete           │ │
│  │                                                        │ │
│  │  Requires: X-Internal-Key header                      │ │
│  └────────────────────────────────────────────────────────┘ │
└──────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌──────────────────────────────────────────────────────────────┐
│                PostgreSQL Database                           │
│                                                              │
│  secrets.host_credentials                                    │
│  • password_encrypted (AES-256-GCM)                         │
│  • Unique constraint: (host, purpose)                       │
│                                                              │
│  secrets.credential_access_log                              │
│  • Audit trail for all operations                           │
└──────────────────────────────────────────────────────────────┘
```

## Security Model

### Encryption

**Algorithm**: AES-256-GCM (Galois/Counter Mode)
- **Key Size**: 256 bits (32 bytes)
- **Nonce**: 96 bits (12 bytes), randomly generated per encryption
- **Authentication**: Built-in authentication tag (128 bits)

**Key Derivation**: PBKDF2-HMAC-SHA256
- **Iterations**: 100,000
- **Salt**: Static salt `opsconductor-secrets-v1` (for deterministic key derivation)
- **Input**: `SECRETS_KMS_KEY` environment variable
- **Output**: 256-bit encryption key

### Storage Format

Encrypted data is stored as base64-encoded string:
```
base64(nonce[12 bytes] + ciphertext + auth_tag[16 bytes])
```

### Access Control

**Internal-Only API**:
- NOT exposed via Kong gateway
- Requires `X-Internal-Key` header matching `INTERNAL_KEY` env var
- Only accessible from within the Docker network

**Audit Logging**:
- Every credential access is logged to `secrets.credential_access_log`
- Includes: timestamp, accessor, operation type, success/failure
- Passwords are NEVER logged in plaintext

## Configuration

### Environment Variables

```bash
# Required: Master encryption key (256-bit recommended)
SECRETS_KMS_KEY=your-256-bit-encryption-key-here

# Required: Internal service authentication key
INTERNAL_KEY=your-internal-service-key-here

# Database connection (existing)
DATABASE_URL=postgresql://opsconductor:opsconductor_secure_2024@postgres:5432/opsconductor
```

### Generating Keys

```bash
# Generate SECRETS_KMS_KEY (256-bit, base64-encoded)
openssl rand -base64 32

# Generate INTERNAL_KEY (256-bit, base64-encoded)
openssl rand -base64 32
```

### Docker Compose

Add to `docker-compose.yml`:

```yaml
services:
  automation-service:
    environment:
      - SECRETS_KMS_KEY=${SECRETS_KMS_KEY}
      - INTERNAL_KEY=${INTERNAL_KEY}
```

Add to `.env`:

```bash
SECRETS_KMS_KEY=<generated-key>
INTERNAL_KEY=<generated-key>
```

## API Reference

### Credential Upsert

**Endpoint**: `POST /internal/secrets/credential-upsert`

**Headers**:
- `X-Internal-Key`: Internal service key (required)
- `Content-Type`: application/json

**Request Body**:
```json
{
  "host": "192.168.50.211",
  "purpose": "winrm",
  "username": "Administrator",
  "password": "SecurePass123",
  "domain": "CORP",
  "additional_data": {
    "notes": "Production server"
  }
}
```

**Response** (200 OK):
```json
{
  "success": true,
  "credential_id": 42,
  "host": "192.168.50.211",
  "purpose": "winrm"
}
```

**Purpose Values**:
- `winrm` - Windows Remote Management
- `ssh` - SSH connections
- `rdp` - Remote Desktop Protocol
- `http` - HTTP/HTTPS authentication
- `database` - Database connections
- Custom values supported

### Credential Lookup

**Endpoint**: `POST /internal/secrets/credential-lookup`

**Headers**:
- `X-Internal-Key`: Internal service key (required)
- `Content-Type`: application/json

**Request Body**:
```json
{
  "host": "192.168.50.211",
  "purpose": "winrm"
}
```

**Response** (200 OK):
```json
{
  "host": "192.168.50.211",
  "purpose": "winrm",
  "username": "Administrator",
  "password": "SecurePass123",
  "domain": "CORP",
  "additional_data": {
    "notes": "Production server"
  }
}
```

**Response** (404 Not Found):
```json
{
  "reason": "not_found"
}
```

### Credential Delete

**Endpoint**: `DELETE /internal/secrets/credential-delete?host=<host>&purpose=<purpose>`

**Headers**:
- `X-Internal-Key`: Internal service key (required)

**Query Parameters**:
- `host`: Hostname or IP address
- `purpose`: Credential purpose

**Response** (200 OK):
```json
{
  "success": true,
  "host": "192.168.50.211",
  "purpose": "winrm"
}
```

**Response** (404 Not Found):
```json
{
  "reason": "not_found"
}
```

## Usage Examples

### Python (Internal Service)

```python
from secrets_broker import SecretsManager

# Initialize
secrets_manager = SecretsManager(
    kms_key=os.getenv("SECRETS_KMS_KEY"),
    database_url=os.getenv("DATABASE_URL")
)

# Upsert credential
result = secrets_manager.upsert_credential(
    host="192.168.50.211",
    purpose="winrm",
    username="Administrator",
    password="SecurePass123",
    domain="CORP",
    created_by="admin-script"
)
print(f"Credential ID: {result['credential_id']}")

# Lookup credential
creds = secrets_manager.lookup_credential(
    host="192.168.50.211",
    purpose="winrm",
    accessed_by="automation-service"
)

if creds:
    print(f"Username: {creds['username']}")
    print(f"Password: {'*' * len(creds['password'])}")  # Mask in logs!
    print(f"Domain: {creds['domain']}")
else:
    print("Credentials not found")

# Delete credential
deleted = secrets_manager.delete_credential(
    host="192.168.50.211",
    purpose="winrm",
    deleted_by="admin-script"
)
print(f"Deleted: {deleted}")
```

### cURL (Internal API)

```bash
# Set internal key
INTERNAL_KEY="your-internal-key-here"

# Upsert credential
curl -X POST http://automation-service:3003/internal/secrets/credential-upsert \
  -H "X-Internal-Key: $INTERNAL_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "host": "192.168.50.211",
    "purpose": "winrm",
    "username": "Administrator",
    "password": "SecurePass123",
    "domain": "CORP"
  }'

# Lookup credential
curl -X POST http://automation-service:3003/internal/secrets/credential-lookup \
  -H "X-Internal-Key: $INTERNAL_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "host": "192.168.50.211",
    "purpose": "winrm"
  }'

# Delete credential
curl -X DELETE "http://automation-service:3003/internal/secrets/credential-delete?host=192.168.50.211&purpose=winrm" \
  -H "X-Internal-Key: $INTERNAL_KEY"
```

## Database Schema

```sql
-- Host credentials table
CREATE TABLE secrets.host_credentials (
    id SERIAL PRIMARY KEY,
    host VARCHAR(255) NOT NULL,
    purpose VARCHAR(50) NOT NULL,
    username VARCHAR(255),
    password_encrypted TEXT,  -- AES-256-GCM encrypted
    domain VARCHAR(255),
    additional_data JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    created_by VARCHAR(100),
    updated_by VARCHAR(100),
    UNIQUE(host, purpose)
);

-- Indexes
CREATE INDEX idx_host_credentials_host ON secrets.host_credentials(host);
CREATE INDEX idx_host_credentials_purpose ON secrets.host_credentials(purpose);
CREATE INDEX idx_host_credentials_host_purpose ON secrets.host_credentials(host, purpose);

-- Audit log
CREATE TABLE secrets.credential_access_log (
    id SERIAL PRIMARY KEY,
    credential_id INTEGER REFERENCES secrets.host_credentials(id) ON DELETE CASCADE,
    host VARCHAR(255) NOT NULL,
    purpose VARCHAR(50) NOT NULL,
    accessed_by VARCHAR(100),
    access_type VARCHAR(50) NOT NULL,  -- 'read', 'create', 'update', 'delete'
    success BOOLEAN DEFAULT true,
    error_message TEXT,
    ip_address INET,
    accessed_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Indexes
CREATE INDEX idx_credential_access_log_credential_id ON secrets.credential_access_log(credential_id);
CREATE INDEX idx_credential_access_log_accessed_at ON secrets.credential_access_log(accessed_at);
CREATE INDEX idx_credential_access_log_host ON secrets.credential_access_log(host);
```

## Security Best Practices

### Key Management

1. **Store KMS Key Securely**:
   - Use a proper KMS (AWS KMS, HashiCorp Vault, Azure Key Vault)
   - Never commit keys to version control
   - Rotate keys regularly (requires re-encryption of all credentials)

2. **Protect Internal Key**:
   - Generate strong, random keys (256-bit minimum)
   - Rotate regularly (monthly recommended)
   - Monitor for unauthorized access attempts

3. **Environment Isolation**:
   - Use different keys for dev/staging/production
   - Never share keys between environments

### Access Control

1. **Network Isolation**:
   - Secrets API should only be accessible within Docker network
   - Never expose via Kong or public gateway
   - Use firewall rules to restrict access

2. **Service Authentication**:
   - Only trusted services should have `INTERNAL_KEY`
   - Implement service-specific keys if needed
   - Log all access attempts

3. **Audit Monitoring**:
   - Monitor `credential_access_log` for suspicious activity
   - Alert on:
     - Failed access attempts
     - Unusual access patterns
     - Access from unexpected services
     - Bulk credential reads

### Operational Security

1. **Logging**:
   - NEVER log passwords in plaintext
   - Mask sensitive data in all logs
   - Use structured logging for audit trails

2. **Backup & Recovery**:
   - Backup encrypted credentials regularly
   - Store backups securely (encrypted at rest)
   - Test recovery procedures

3. **Incident Response**:
   - Have a key rotation procedure ready
   - Plan for credential compromise scenarios
   - Document emergency access procedures

## Monitoring & Alerting

### Metrics

Monitor these metrics:
- `secrets_credential_lookups_total` - Total credential lookups
- `secrets_credential_lookup_failures_total` - Failed lookups
- `secrets_credential_upserts_total` - Total credential creates/updates
- `secrets_encryption_errors_total` - Encryption/decryption failures

### Alerts

Set up alerts for:
- **High failure rate**: >10% of lookups failing
- **Unusual access patterns**: Spike in credential reads
- **Encryption errors**: Any encryption/decryption failures
- **Unauthorized access**: Requests without valid `INTERNAL_KEY`

### Audit Queries

```sql
-- Recent credential access
SELECT 
    host, 
    purpose, 
    accessed_by, 
    access_type, 
    success, 
    accessed_at
FROM secrets.credential_access_log
ORDER BY accessed_at DESC
LIMIT 100;

-- Failed access attempts
SELECT 
    host, 
    purpose, 
    accessed_by, 
    error_message, 
    accessed_at
FROM secrets.credential_access_log
WHERE success = false
ORDER BY accessed_at DESC;

-- Access by service
SELECT 
    accessed_by, 
    COUNT(*) as access_count,
    SUM(CASE WHEN success THEN 1 ELSE 0 END) as successful,
    SUM(CASE WHEN NOT success THEN 1 ELSE 0 END) as failed
FROM secrets.credential_access_log
WHERE accessed_at > NOW() - INTERVAL '24 hours'
GROUP BY accessed_by
ORDER BY access_count DESC;
```

## Troubleshooting

### "SECRETS_KMS_KEY not set"

**Symptom**: Secrets manager fails to initialize

**Solution**:
```bash
# Generate and set key
export SECRETS_KMS_KEY=$(openssl rand -base64 32)
# Add to .env file
echo "SECRETS_KMS_KEY=$SECRETS_KMS_KEY" >> .env
# Restart service
docker-compose restart automation-service
```

### "Invalid or missing X-Internal-Key header"

**Symptom**: 403 Forbidden when calling secrets API

**Solution**:
- Verify `INTERNAL_KEY` is set in environment
- Ensure `X-Internal-Key` header matches `INTERNAL_KEY` value
- Check that request is coming from internal service, not external client

### "Failed to decrypt credential"

**Symptom**: Decryption errors when looking up credentials

**Possible Causes**:
1. **Key changed**: `SECRETS_KMS_KEY` was rotated without re-encrypting data
2. **Data corruption**: Database corruption or manual modification
3. **Wrong key**: Using different key than was used for encryption

**Solution**:
- Verify `SECRETS_KMS_KEY` hasn't changed
- Check database integrity
- Re-encrypt credentials if key was rotated

### "Credential not found"

**Symptom**: 404 when looking up credential

**Solution**:
- Verify host and purpose match exactly (case-sensitive)
- Check if credential was created: `SELECT * FROM secrets.host_credentials WHERE host = '...'`
- Upsert credential if missing

## Migration & Rollback

### Initial Setup

```bash
# 1. Apply database migration
psql -U opsconductor -d opsconductor -f database/migrations/011_secrets_broker.sql

# 2. Generate keys
export SECRETS_KMS_KEY=$(openssl rand -base64 32)
export INTERNAL_KEY=$(openssl rand -base64 32)

# 3. Add to .env
echo "SECRETS_KMS_KEY=$SECRETS_KMS_KEY" >> .env
echo "INTERNAL_KEY=$INTERNAL_KEY" >> .env

# 4. Restart services
docker-compose restart automation-service
```

### Key Rotation

```bash
# 1. Generate new key
NEW_KEY=$(openssl rand -base64 32)

# 2. Re-encrypt all credentials (Python script)
python3 scripts/rotate_secrets_key.py --old-key "$SECRETS_KMS_KEY" --new-key "$NEW_KEY"

# 3. Update environment
export SECRETS_KMS_KEY="$NEW_KEY"
echo "SECRETS_KMS_KEY=$NEW_KEY" >> .env

# 4. Restart services
docker-compose restart automation-service
```

### Rollback

```sql
-- Remove secrets tables
DROP TABLE IF EXISTS secrets.credential_access_log;
DROP TABLE IF EXISTS secrets.host_credentials;
DROP SCHEMA IF EXISTS secrets;
```

```bash
# Remove environment variables
unset SECRETS_KMS_KEY
unset INTERNAL_KEY

# Restart services
docker-compose restart automation-service
```

## Future Enhancements

1. **External KMS Integration**:
   - AWS KMS
   - HashiCorp Vault
   - Azure Key Vault
   - Google Cloud KMS

2. **Advanced Features**:
   - Credential expiration and rotation
   - Multi-factor authentication support
   - Certificate-based authentication
   - SSH key management

3. **Compliance**:
   - PCI-DSS compliance features
   - SOC 2 audit trails
   - GDPR data handling

4. **Performance**:
   - Credential caching (with TTL)
   - Batch operations
   - Read replicas for high availability