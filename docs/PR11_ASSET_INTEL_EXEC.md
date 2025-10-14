## PR #11 — Asset-Intelligent Execution: Host Resolution, Server-Side Credential Injection, and Always-Executable Chat

### Overview

This PR implements asset-intelligent tool execution that makes the AI chat **always executable** by:

1. **Resolving hosts + OS via the Asset DB** - Automatically looks up connection profiles
2. **Prefilling connection profiles** - Auto-configures ports, SSL, domain from asset data
3. **Securely fetching credentials server-side** - Never exposes passwords to the browser
4. **Executing tools with merged values** - Combines user params + asset profile + credentials
5. **Falling back to schema-driven prompts** - Returns structured `missing_params` error when data is truly missing

### Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                         AI Chat (Frontend)                          │
│  "how many windows 10 os assets do we have?"                       │
│  "show directory of the c drive on 192.168.50.211"                 │
└────────────────────────────┬────────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────────┐
│                      Kong Gateway (Port 3000)                       │
│  Routes:                                                            │
│  - /assets/*          → automation-service (PUBLIC)                 │
│  - /ai/tools/*        → automation-service (PUBLIC)                 │
│  - /internal/secrets/* → NOT EXPOSED (blocked)                      │
└────────────────────────────┬────────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────────┐
│              Automation Service (Port 3003)                         │
│                                                                     │
│  ┌─────────────────────────────────────────────────────────────┐  │
│  │ Asset Façade (PUBLIC)                                       │  │
│  │ - GET /assets/count?os=Windows%2010                         │  │
│  │ - GET /assets/search?os=windows&limit=50                    │  │
│  │ - GET /assets/connection-profile?host=192.168.50.211        │  │
│  └─────────────────────────────────────────────────────────────┘  │
│                                                                     │
│  ┌─────────────────────────────────────────────────────────────┐  │
│  │ Secrets Broker (INTERNAL ONLY - X-Internal-Key required)   │  │
│  │ - POST /internal/secrets/credential-upsert                  │  │
│  │ - POST /internal/secrets/credential-lookup                  │  │
│  │ - DELETE /internal/secrets/credential-delete                │  │
│  └─────────────────────────────────────────────────────────────┘  │
│                                                                     │
│  ┌─────────────────────────────────────────────────────────────┐  │
│  │ AI Tools Router (Enhanced with Asset Intelligence)         │  │
│  │ - POST /ai/tools/execute                                    │  │
│  │   • asset_count → direct execution                          │  │
│  │   • asset_search → direct execution                         │  │
│  │   • windows_list_directory → asset profile + creds lookup  │  │
│  └─────────────────────────────────────────────────────────────┘  │
└────────────────────────────┬────────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────────┐
│                    PostgreSQL Database                              │
│                                                                     │
│  assets.assets                                                      │
│  - id, hostname, ip_address, os_type, os_version                   │
│  - service_type, port, is_secure, domain                           │
│  - username, password_encrypted (for primary service)              │
│                                                                     │
│  secrets.host_credentials (NEW)                                    │
│  - id, host, purpose, username, password_encrypted, domain         │
│  - AES-256-GCM encryption at rest                                  │
│                                                                     │
│  secrets.credential_access_log (NEW)                               │
│  - Audit trail for all credential access                           │
└─────────────────────────────────────────────────────────────────────┘
```

### Components

#### 1. Asset Façade (`automation-service/asset_facade.py`)

**Purpose**: Fast, read-only access to asset information for tool execution

**Endpoints**:
- `GET /assets/count` - Count assets matching filters
- `GET /assets/search` - Search assets with detailed information
- `GET /assets/connection-profile` - Get connection parameters for a host

**Features**:
- Case-insensitive OS matching (handles "Windows 10", "windows", "win")
- Hostname or IP lookup
- Auto-generates connection profiles (WinRM, SSH, RDP)
- Performance target: <100ms p50

**Example**:
```bash
curl "http://localhost:3000/assets/count?os=Windows%2010"
# {"count": 5, "filters": {"os": "Windows 10"}}

curl "http://localhost:3000/assets/connection-profile?host=192.168.50.211"
# {
#   "found": true,
#   "host": "win-server-01",
#   "os": "Windows 10",
#   "winrm": {"port": 5985, "use_ssl": false, "domain": null}
# }
```

#### 2. Secrets Broker (`automation-service/secrets_broker.py`)

**Purpose**: Secure server-side credential storage and retrieval

**Security**:
- AES-256-GCM encryption at rest
- PBKDF2 key derivation from master key
- Audit logging for all access
- INTERNAL USE ONLY - requires `X-Internal-Key` header

**Endpoints** (NOT exposed via Kong):
- `POST /internal/secrets/credential-upsert` - Create/update credential
- `POST /internal/secrets/credential-lookup` - Retrieve decrypted credential
- `DELETE /internal/secrets/credential-delete` - Delete credential

**Environment Variables**:
- `SECRETS_KMS_KEY` - Master encryption key (required)
- `INTERNAL_KEY` - Service-to-service authentication key (required)

**Example** (internal use only):
```python
# Upsert credential
secrets_manager.upsert_credential(
    host="192.168.50.211",
    purpose="winrm",
    username="Administrator",
    password="SecurePass123",
    domain="CORP"
)

# Lookup credential
creds = secrets_manager.lookup_credential(
    host="192.168.50.211",
    purpose="winrm"
)
# Returns: {"username": "Administrator", "password": "SecurePass123", "domain": "CORP"}
```

#### 3. Asset-Aware Tools

**New Tools**:

1. **asset_count** (`tools/catalog/asset_count.yaml`)
   - Counts assets matching filters
   - Parameters: os, hostname, ip, status, environment
   - Executes directly in automation-service (no ai-pipeline needed)

2. **asset_search** (`tools/catalog/asset_search.yaml`)
   - Searches and lists assets
   - Parameters: os, hostname, ip, status, environment, limit
   - Returns detailed asset information

**Enhanced Tools**:

3. **windows_list_directory** (enhanced with asset intelligence)
   - Auto-resolves connection profile from asset DB
   - Auto-fetches credentials server-side
   - Returns `missing_credentials` error if creds not found
   - Never exposes passwords to client

**Execution Flow**:
```
1. User: "show directory of the c drive on 192.168.50.211"
2. Frontend → POST /ai/tools/execute {name: "windows_list_directory", params: {host: "192.168.50.211", path: "C:\\"}}
3. Automation Service:
   a. Lookup connection profile for 192.168.50.211
   b. Found: {winrm: {port: 5985, use_ssl: false, domain: "CORP"}}
   c. Lookup credentials for 192.168.50.211 + winrm
   d. Found: {username: "Administrator", password: "***"}
   e. Merge params: {host, path, port: 5985, use_ssl: false, domain: "CORP", username, password}
   f. Execute via ai-pipeline with merged params
4. Return directory listing (password never sent to client)
```

**Missing Credentials Flow**:
```
1. User: "show directory of the c drive on 192.168.50.211"
2. Frontend → POST /ai/tools/execute {name: "windows_list_directory", params: {host: "192.168.50.211", path: "C:\\"}}
3. Automation Service:
   a. Lookup connection profile for 192.168.50.211
   b. Found: {winrm: {port: 5985, use_ssl: false}}
   c. Lookup credentials for 192.168.50.211 + winrm
   d. NOT FOUND
   e. Return 400 with structured error:
      {
        "error": "missing_credentials",
        "missing_params": [
          {"name": "username", "type": "string", "secret": false},
          {"name": "password", "type": "string", "secret": true},
          {"name": "domain", "type": "string", "optional": true}
        ],
        "hint": "Credentials not found for host 192.168.50.211. Please provide username and password."
      }
4. Frontend displays schema-driven modal for credential input
5. User provides credentials
6. Frontend → POST /ai/tools/execute {name: "windows_list_directory", params: {host, path, username, password, domain}}
7. Execute with provided credentials (one-time use, not stored in browser)
```

### Database Schema

**New Tables**:

```sql
-- Secrets schema
CREATE SCHEMA IF NOT EXISTS secrets;

-- Host credentials table
CREATE TABLE secrets.host_credentials (
    id SERIAL PRIMARY KEY,
    host VARCHAR(255) NOT NULL,
    purpose VARCHAR(50) NOT NULL,  -- 'winrm', 'ssh', 'rdp', etc.
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

-- Credential access audit log
CREATE TABLE secrets.credential_access_log (
    id SERIAL PRIMARY KEY,
    credential_id INTEGER REFERENCES secrets.host_credentials(id),
    host VARCHAR(255) NOT NULL,
    purpose VARCHAR(50) NOT NULL,
    accessed_by VARCHAR(100),
    access_type VARCHAR(50) NOT NULL,  -- 'read', 'create', 'update', 'delete'
    success BOOLEAN DEFAULT true,
    error_message TEXT,
    ip_address INET,
    accessed_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);
```

**Migration**: `database/migrations/011_secrets_broker.sql`

### Configuration

**Environment Variables**:

```bash
# Secrets Broker (required for credential management)
SECRETS_KMS_KEY=your-256-bit-encryption-key-here
INTERNAL_KEY=your-internal-service-key-here

# Asset Façade (optional - defaults to direct DB access)
ASSET_SERVICE_BASE=http://asset-service:3002

# Database (existing)
DATABASE_URL=postgresql://opsconductor:opsconductor_secure_2024@postgres:5432/opsconductor
```

**Generating Keys**:
```bash
# Generate SECRETS_KMS_KEY (256-bit)
openssl rand -base64 32

# Generate INTERNAL_KEY
openssl rand -base64 32
```

### Security Model

**Principles**:
1. **Never expose credentials to browser** - All credential operations happen server-side
2. **Encrypt at rest** - AES-256-GCM with PBKDF2 key derivation
3. **Audit all access** - Every credential read/write is logged
4. **Internal-only secrets API** - Requires X-Internal-Key header, NOT exposed via Kong
5. **Mask in logs** - Passwords never appear in plaintext logs

**Threat Model**:
- ✅ Browser compromise - Credentials never sent to client
- ✅ Log exposure - Passwords masked in all logs
- ✅ Database dump - Credentials encrypted at rest
- ✅ Unauthorized API access - Internal key required
- ⚠️ Memory dump - Decrypted credentials exist in memory during execution
- ⚠️ Master key compromise - All credentials can be decrypted

**Best Practices**:
1. Store `SECRETS_KMS_KEY` in a proper KMS (AWS KMS, HashiCorp Vault, etc.)
2. Rotate `INTERNAL_KEY` regularly
3. Monitor `credential_access_log` for suspicious activity
4. Use short-lived credentials when possible
5. Implement rate limiting on credential lookups

### Testing

**Unit Tests**: `tests/test_pr11_asset_intel.py`

**Test Coverage**:
- ✅ Asset count (all, filtered by OS)
- ✅ Asset search (Windows, Linux, with limits)
- ✅ Connection profile (found, not found)
- ✅ Secrets broker (blocked without key)
- ✅ Asset tools (asset_count, asset_search)
- ✅ Windows tool (missing credentials error)
- ✅ Kong routes (public exposed, internal blocked)

**Running Tests**:
```bash
# Run all PR #11 tests
pytest tests/test_pr11_asset_intel.py -v

# Run specific test class
pytest tests/test_pr11_asset_intel.py::TestAssetFacade -v

# Run with coverage
pytest tests/test_pr11_asset_intel.py --cov=automation-service --cov-report=html
```

**Manual Testing**:

```bash
# 1. Count Windows 10 assets
curl "http://localhost:3000/assets/count?os=Windows%2010"

# 2. Search for Windows assets
curl "http://localhost:3000/assets/search?os=windows&limit=5"

# 3. Get connection profile
curl "http://localhost:3000/assets/connection-profile?host=192.168.50.211"

# 4. Execute asset_count tool
curl -X POST http://localhost:3000/ai/tools/execute \
  -H "Content-Type: application/json" \
  -d '{"name": "asset_count", "params": {"os": "Windows 10"}}'

# 5. Execute asset_search tool
curl -X POST http://localhost:3000/ai/tools/execute \
  -H "Content-Type: application/json" \
  -d '{"name": "asset_search", "params": {"os": "windows", "limit": 5}}'

# 6. Execute windows_list_directory (will return missing_credentials if not configured)
curl -X POST http://localhost:3000/ai/tools/execute \
  -H "Content-Type: application/json" \
  -d '{"name": "windows_list_directory", "params": {"host": "192.168.50.211", "path": "C:\\"}}'

# 7. Verify internal secrets NOT exposed via Kong (should return 404)
curl -X POST http://localhost:3000/internal/secrets/credential-lookup \
  -H "Content-Type: application/json" \
  -d '{"host": "test", "purpose": "winrm"}'
```

### Acceptance Criteria

**From Chat (port 3100)**:
- ✅ "how many windows 10 os assets do we have?" → returns a number (not a canned reply)
- ✅ "list windows 10 assets" → returns list of assets
- ✅ "show directory of the c drive on 192.168.50.211" → executes using asset profile + server-side creds; if creds absent, prompts once via schema modal and then executes

**From Gateway (port 3000)**:
- ✅ `curl http://localhost:3000/assets/count?os=Windows%2010` → 200 with count
- ✅ `curl -X POST http://localhost:3000/ai/tools/execute -d '{"name":"asset_count","params":{"os":"Windows 10"}}'` → 200 with count
- ✅ `curl -X POST http://localhost:3000/internal/secrets/credential-lookup` → 404 (not exposed)

**Security**:
- ✅ No credentials are ever returned to the browser
- ✅ Passwords never logged in plaintext
- ✅ Credentials never stored in localStorage
- ✅ Internal secrets API requires X-Internal-Key header
- ✅ Prometheus metrics `ai_tool_*` reflect these calls

### Rollback Plan

**If issues arise**:

1. **Disable asset intelligence** (keeps existing functionality):
   ```bash
   # Remove SECRETS_KMS_KEY and INTERNAL_KEY from environment
   # Asset façade will still work, but credential lookup will be disabled
   ```

2. **Revert Kong routes**:
   ```bash
   # Remove asset-facade-routes from kong/kong.yml
   # Restart Kong
   docker-compose restart kong
   ```

3. **Revert database migration**:
   ```sql
   DROP TABLE IF EXISTS secrets.credential_access_log;
   DROP TABLE IF EXISTS secrets.host_credentials;
   DROP SCHEMA IF EXISTS secrets;
   ```

4. **Revert code changes**:
   ```bash
   git revert <commit-hash>
   docker-compose restart automation-service
   ```

### Future Enhancements

1. **Credential Rotation**:
   - Automatic credential rotation on schedule
   - Integration with password vaults (HashiCorp Vault, AWS Secrets Manager)

2. **Multi-Factor Authentication**:
   - Support for certificate-based auth
   - SSH key management
   - API token rotation

3. **Advanced Asset Intelligence**:
   - Automatic discovery and profiling
   - Health checks and connectivity testing
   - Performance metrics collection

4. **Frontend Enhancements**:
   - Credential management UI
   - Asset browser with connection testing
   - Bulk credential import

5. **Monitoring & Alerting**:
   - Alert on failed credential lookups
   - Dashboard for credential usage
   - Anomaly detection for unusual access patterns

### References

- **Database Migration**: `database/migrations/011_secrets_broker.sql`
- **Asset Façade**: `automation-service/asset_facade.py`
- **Secrets Broker**: `automation-service/secrets_broker.py`
- **Asset Routes**: `automation-service/routes/assets.py`
- **Secrets Routes**: `automation-service/routes/secrets.py`
- **Enhanced Tools Router**: `automation-service/routes/tools.py`
- **Asset Tools**: `tools/catalog/asset_count.yaml`, `tools/catalog/asset_search.yaml`
- **Tests**: `tests/test_pr11_asset_intel.py`
- **Kong Config**: `kong/kong.yml`