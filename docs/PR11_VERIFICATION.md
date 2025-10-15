# PR #11 Verification Guide

## Quick Start

### 1. Apply Database Migration

```bash
# Apply the secrets broker schema
docker-compose exec postgres psql -U opsconductor -d opsconductor \
  -f /docker-entrypoint-initdb.d/011_secrets_broker.sql
```

### 2. Configure Environment

```bash
# Generate encryption keys
export SECRETS_KMS_KEY=$(openssl rand -base64 32)
export INTERNAL_KEY=$(openssl rand -base64 32)

# Add to .env file
echo "SECRETS_KMS_KEY=$SECRETS_KMS_KEY" >> .env
echo "INTERNAL_KEY=$INTERNAL_KEY" >> .env

# Restart services
docker-compose restart automation-service kong
```

### 3. Run Verification Script

```bash
./scripts/verify_pr11.sh
```

## Manual Verification

### Test 1: Asset Count (Direct)

**Query**: "How many Windows 10 assets do we have?"

```bash
curl "http://localhost:3003/assets/count?os=Windows%2010"
```

**Expected Response**:
```json
{
  "count": 5,
  "filters": {
    "os": "Windows 10",
    "hostname": null,
    "ip": null,
    "status": null,
    "environment": null
  }
}
```

### Test 2: Asset Count (via Kong)

```bash
curl "http://localhost:3000/assets/count?os=Windows%2010"
```

**Expected**: Same as Test 1

### Test 3: Asset Search

**Query**: "List Windows 10 machines"

```bash
curl "http://localhost:3000/assets/search?os=Windows%2010&limit=5"
```

**Expected Response**:
```json
{
  "items": [
    {
      "id": 1,
      "name": "Windows Server 01",
      "hostname": "win-server-01",
      "ip_address": "192.168.50.211",
      "os_type": "windows",
      "os_version": "Windows 10",
      "service_type": "winrm",
      "port": 5985,
      "is_secure": false,
      "status": "active",
      "environment": "production"
    }
  ],
  "count": 1,
  "limit": 5
}
```

### Test 4: Connection Profile

```bash
curl "http://localhost:3000/assets/connection-profile?host=192.168.50.211"
```

**Expected Response** (if host exists):
```json
{
  "found": true,
  "host": "win-server-01",
  "ip": "192.168.50.211",
  "hostname": "win-server-01",
  "os": "Windows 10",
  "os_type": "windows",
  "winrm": {
    "port": 5985,
    "use_ssl": false,
    "domain": null
  },
  "primary_service": {
    "type": "winrm",
    "port": 5985,
    "is_secure": false
  }
}
```

**Expected Response** (if host not found):
```json
{
  "found": false
}
```

### Test 5: Asset Count Tool

```bash
curl -X POST http://localhost:3000/ai/tools/execute \
  -H "Content-Type: application/json" \
  -d '{
    "name": "asset_count",
    "params": {
      "os": "Windows 10"
    }
  }'
```

**Expected Response**:
```json
{
  "success": true,
  "tool": "asset_count",
  "output": "{'count': 5, 'filters': {'os': 'Windows 10'}}",
  "duration_ms": 45.2,
  "trace_id": "abc123...",
  "timestamp": "2025-01-15T10:30:00Z"
}
```

### Test 6: Asset Search Tool

```bash
curl -X POST http://localhost:3000/ai/tools/execute \
  -H "Content-Type: application/json" \
  -d '{
    "name": "asset_search",
    "params": {
      "os": "windows",
      "limit": 5
    }
  }'
```

**Expected Response**:
```json
{
  "success": true,
  "tool": "asset_search",
  "output": "{'items': [...], 'count': 5, 'limit': 5}",
  "duration_ms": 67.8,
  "trace_id": "def456...",
  "timestamp": "2025-01-15T10:31:00Z"
}
```

### Test 7: Windows List Directory (No Credentials)

```bash
curl -X POST http://localhost:3000/ai/tools/execute \
  -H "Content-Type: application/json" \
  -d '{
    "name": "windows_list_directory",
    "params": {
      "host": "192.168.50.211",
      "path": "C:\\"
    }
  }'
```

**Expected Response** (if credentials not stored):
```json
{
  "detail": {
    "success": false,
    "error": "missing_credentials",
    "missing_params": [
      {
        "name": "username",
        "type": "string",
        "secret": false,
        "description": "Windows username"
      },
      {
        "name": "password",
        "type": "string",
        "secret": true,
        "description": "Windows password"
      },
      {
        "name": "domain",
        "type": "string",
        "secret": false,
        "optional": true,
        "description": "Windows domain (optional)"
      }
    ],
    "hint": "Credentials not found for host 192.168.50.211. Please provide username and password.",
    "trace_id": "ghi789...",
    "duration_ms": 23.4
  }
}
```

### Test 8: Store Credentials (Internal API)

**Note**: This requires `INTERNAL_KEY` and should only be done from internal services.

```bash
curl -X POST http://automation-service:3003/internal/secrets/credential-upsert \
  -H "X-Internal-Key: $INTERNAL_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "host": "192.168.50.211",
    "purpose": "winrm",
    "username": "Administrator",
    "password": "YourSecurePassword",
    "domain": "CORP"
  }'
```

**Expected Response**:
```json
{
  "success": true,
  "credential_id": 1,
  "host": "192.168.50.211",
  "purpose": "winrm"
}
```

### Test 9: Windows List Directory (With Credentials)

After storing credentials in Test 8:

```bash
curl -X POST http://localhost:3000/ai/tools/execute \
  -H "Content-Type: application/json" \
  -d '{
    "name": "windows_list_directory",
    "params": {
      "host": "192.168.50.211",
      "path": "C:\\"
    }
  }'
```

**Expected Response** (if WinRM accessible):
```json
{
  "success": true,
  "tool": "windows_list_directory",
  "output": "{\"success\": true, \"path\": \"C:\\\\\", \"entries\": [\"Program Files\", \"Windows\", \"Users\"], \"count\": 3}",
  "duration_ms": 1234.5,
  "trace_id": "jkl012...",
  "timestamp": "2025-01-15T10:35:00Z"
}
```

### Test 10: Security - Internal API NOT Exposed

```bash
curl -X POST http://localhost:3000/internal/secrets/credential-lookup \
  -H "Content-Type: application/json" \
  -d '{
    "host": "192.168.50.211",
    "purpose": "winrm"
  }'
```

**Expected Response**: HTTP 404 (route not found)
```json
{
  "message": "no Route matched with those values"
}
```

This confirms that internal secrets API is NOT exposed via Kong gateway.

### Test 11: Security - Blocked Without Key

```bash
curl -X POST http://automation-service:3003/internal/secrets/credential-lookup \
  -H "Content-Type: application/json" \
  -d '{
    "host": "192.168.50.211",
    "purpose": "winrm"
  }'
```

**Expected Response**: HTTP 403 (forbidden)
```json
{
  "detail": "Invalid or missing X-Internal-Key header"
}
```

## Chat E2E Verification

### Test 12: Chat - Asset Count

1. Open chat at http://localhost:3100
2. Type: "how many windows 10 os assets do we have?"
3. **Expected**: Returns actual count from database (e.g., "You have 5 Windows 10 assets")

### Test 13: Chat - Asset List

1. Type: "list windows 10 assets"
2. **Expected**: Returns list of Windows 10 machines with details

### Test 14: Chat - Windows Directory (No Creds)

1. Type: "show directory of the c drive on 192.168.50.211"
2. **Expected**: 
   - If credentials stored: Shows directory listing
   - If credentials not stored: Shows modal asking for username/password

### Test 15: Chat - Windows Directory (With Creds)

1. After providing credentials in modal (or after storing via API)
2. Type: "show directory of the c drive on 192.168.50.211"
3. **Expected**: Shows directory listing without asking for credentials again

## Database Verification

### Check Secrets Schema

```bash
docker-compose exec postgres psql -U opsconductor -d opsconductor -c "
SELECT table_name 
FROM information_schema.tables 
WHERE table_schema = 'secrets'
ORDER BY table_name;
"
```

**Expected Output**:
```
       table_name        
-------------------------
 credential_access_log
 host_credentials
(2 rows)
```

### Check Stored Credentials

```bash
docker-compose exec postgres psql -U opsconductor -d opsconductor -c "
SELECT id, host, purpose, username, domain, created_at 
FROM secrets.host_credentials 
ORDER BY created_at DESC 
LIMIT 5;
"
```

**Expected Output** (if credentials stored):
```
 id |      host       | purpose |   username    | domain |         created_at         
----+-----------------+---------+---------------+--------+----------------------------
  1 | 192.168.50.211 | winrm   | Administrator | CORP   | 2025-01-15 10:30:00.123456
(1 row)
```

**Note**: `password_encrypted` column contains encrypted data and should NOT be readable.

### Check Audit Log

```bash
docker-compose exec postgres psql -U opsconductor -d opsconductor -c "
SELECT host, purpose, accessed_by, access_type, success, accessed_at 
FROM secrets.credential_access_log 
ORDER BY accessed_at DESC 
LIMIT 10;
"
```

**Expected Output**:
```
      host       | purpose |    accessed_by     | access_type | success |         accessed_at         
-----------------+---------+--------------------+-------------+---------+-----------------------------
 192.168.50.211 | winrm   | tools-api          | read        | t       | 2025-01-15 10:35:00.123456
 192.168.50.211 | winrm   | automation-service | create      | t       | 2025-01-15 10:30:00.123456
(2 rows)
```

## Performance Verification

### Asset Count Performance

```bash
time curl -s "http://localhost:3000/assets/count?os=Windows%2010" > /dev/null
```

**Expected**: <100ms

### Asset Search Performance

```bash
time curl -s "http://localhost:3000/assets/search?os=windows&limit=50" > /dev/null
```

**Expected**: <100ms

### Connection Profile Performance

```bash
time curl -s "http://localhost:3000/assets/connection-profile?host=192.168.50.211" > /dev/null
```

**Expected**: <50ms

## Troubleshooting

### Issue: "SECRETS_KMS_KEY not set"

**Solution**:
```bash
export SECRETS_KMS_KEY=$(openssl rand -base64 32)
echo "SECRETS_KMS_KEY=$SECRETS_KMS_KEY" >> .env
docker-compose restart automation-service
```

### Issue: "Asset count returns 0"

**Cause**: No assets in database

**Solution**: Populate assets table with test data
```bash
docker-compose exec postgres psql -U opsconductor -d opsconductor -c "
INSERT INTO assets.assets (name, hostname, ip_address, os_type, os_version, service_type, port, status)
VALUES ('Test Windows Server', 'win-test-01', '192.168.50.211', 'windows', 'Windows 10', 'winrm', 5985, 'active');
"
```

### Issue: "Connection profile not found"

**Cause**: Host not in asset database

**Solution**: Add host to assets table (see above)

### Issue: "Windows tool fails with authentication error"

**Cause**: Credentials incorrect or WinRM not accessible

**Solution**:
1. Verify credentials are correct
2. Check WinRM is enabled on target host
3. Verify network connectivity
4. Check firewall rules

## Success Criteria Checklist

- [ ] Asset count returns actual data from database
- [ ] Asset search returns filtered results
- [ ] Connection profile resolves for existing hosts
- [ ] Connection profile returns `found: false` for non-existent hosts
- [ ] asset_count tool executes successfully
- [ ] asset_search tool executes successfully
- [ ] windows_list_directory returns missing_credentials error when creds not stored
- [ ] windows_list_directory executes successfully when creds stored
- [ ] Internal secrets API requires X-Internal-Key header
- [ ] Internal secrets API NOT exposed via Kong (404)
- [ ] Credentials never appear in logs
- [ ] Credentials never sent to browser
- [ ] Audit log records all credential access
- [ ] Performance targets met (<100ms for asset queries)
- [ ] Chat queries work end-to-end

## Deployment Checklist

- [ ] Database migration applied
- [ ] SECRETS_KMS_KEY generated and configured
- [ ] INTERNAL_KEY generated and configured
- [ ] Services restarted
- [ ] Verification script passes
- [ ] Manual tests pass
- [ ] Chat E2E tests pass
- [ ] Performance tests pass
- [ ] Security tests pass
- [ ] Documentation reviewed
- [ ] Rollback plan documented

## Next Steps

After verification:

1. **Seed Production Credentials**:
   - Use internal API to store credentials for production hosts
   - Test connectivity to each host
   - Document credential rotation schedule

2. **Monitor Metrics**:
   - Set up Prometheus alerts for credential lookup failures
   - Monitor asset query performance
   - Track tool execution success rates

3. **User Training**:
   - Document how to use asset queries in chat
   - Explain credential management workflow
   - Provide troubleshooting guide

4. **Future Enhancements**:
   - Implement credential rotation
   - Add credential management UI
   - Integrate with external KMS (Vault, AWS Secrets Manager)
   - Add asset discovery automation