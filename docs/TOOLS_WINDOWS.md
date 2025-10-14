# Windows Tools: WinRM Setup & Security

## Overview

OpsConductor supports remote Windows management via WinRM (Windows Remote Management). This enables tools like `windows_list_directory` to execute PowerShell commands on remote Windows hosts.

## Prerequisites

### Windows Host Requirements

1. **Windows Version:** Windows Server 2012 R2+ or Windows 8.1+
2. **PowerShell:** Version 5.1 or higher
3. **WinRM Service:** Enabled and configured
4. **Network Access:** Firewall rules for WinRM ports

### OpsConductor Requirements

1. **Python Package:** `pywinrm` installed
2. **Network Connectivity:** Access to WinRM ports (5985/5986)
3. **Credentials:** Valid Windows user account

## WinRM Setup on Windows Host

### Quick Setup (Development Only)

**⚠️ WARNING: This configuration is insecure and should only be used in isolated development environments.**

```powershell
# Run as Administrator

# Enable WinRM
Enable-PSRemoting -Force

# Allow unencrypted traffic (DEV ONLY)
Set-Item WSMan:\localhost\Service\AllowUnencrypted -Value $true

# Allow basic authentication (DEV ONLY)
Set-Item WSMan:\localhost\Service\Auth\Basic -Value $true

# Configure firewall
New-NetFirewallRule -Name "WinRM-HTTP" -DisplayName "WinRM HTTP" `
    -Enabled True -Direction Inbound -Protocol TCP -LocalPort 5985

# Verify configuration
winrm get winrm/config
```

### Production Setup (Recommended)

```powershell
# Run as Administrator

# Enable WinRM
Enable-PSRemoting -Force

# Configure HTTPS listener
$cert = New-SelfSignedCertificate -DnsName "your-server.domain.com" `
    -CertStoreLocation Cert:\LocalMachine\My

New-Item -Path WSMan:\localhost\Listener -Transport HTTPS `
    -Address * -CertificateThumbPrint $cert.Thumbprint -Force

# Configure authentication
Set-Item WSMan:\localhost\Service\Auth\Basic -Value $false
Set-Item WSMan:\localhost\Service\Auth\Kerberos -Value $true
Set-Item WSMan:\localhost\Service\Auth\Negotiate -Value $true

# Configure firewall
New-NetFirewallRule -Name "WinRM-HTTPS" -DisplayName "WinRM HTTPS" `
    -Enabled True -Direction Inbound -Protocol TCP -LocalPort 5986

# Verify configuration
winrm get winrm/config
```

### Verify WinRM is Working

```powershell
# Test from the Windows host itself
Test-WSMan -ComputerName localhost

# Test from another Windows machine
Test-WSMan -ComputerName <target-host> -Credential (Get-Credential)
```

## OpsConductor Configuration

### Environment Variables

```bash
# WinRM default port (HTTP)
WINRM_DEFAULT_PORT=5985

# Allow insecure connections (DEV ONLY)
WINRM_ALLOW_INSECURE=true  # Set to false in production

# Tool execution timeout
TOOL_TIMEOUT_SECONDS=30
```

### Python Dependencies

The `pywinrm` package is required:

```bash
# Install in ai-pipeline environment
cd pipeline
pip install pywinrm
```

Or add to `requirements.txt`:

```
pywinrm==0.4.3
```

## Using Windows Tools

### windows_list_directory

**Description:** List directory contents on a Windows host via WinRM

**Parameters:**

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| host | string | Yes | - | Windows host IP or hostname |
| path | string | No | `C:\` | Directory path to list |
| username | string | Yes | - | Windows username |
| password | string | Yes | - | Windows password |
| domain | string | No | `""` | Windows domain (optional) |
| port | integer | No | 5985 | WinRM port |
| use_ssl | boolean | No | false | Use HTTPS (port 5986) |
| timeout_s | integer | No | 15 | Operation timeout |

**Examples:**

```bash
# List C drive root
curl -X POST http://localhost:3000/ai/tools/execute \
  -H "Content-Type: application/json" \
  -d '{
    "name": "windows_list_directory",
    "params": {
      "host": "192.168.50.211",
      "path": "C:\\",
      "username": "Administrator",
      "password": "SecurePass123"
    }
  }'

# List Program Files with domain authentication
curl -X POST http://localhost:3000/ai/tools/execute \
  -H "Content-Type: application/json" \
  -d '{
    "name": "windows_list_directory",
    "params": {
      "host": "win-server-01",
      "path": "C:\\Program Files",
      "username": "admin",
      "password": "P@ssw0rd",
      "domain": "CORP"
    }
  }'

# List directory over HTTPS
curl -X POST http://localhost:3000/ai/tools/execute \
  -H "Content-Type: application/json" \
  -d '{
    "name": "windows_list_directory",
    "params": {
      "host": "192.168.1.100",
      "path": "C:\\Users",
      "username": "sysadmin",
      "password": "SecretPass",
      "port": 5986,
      "use_ssl": true
    }
  }'
```

**Success Response:**

```json
{
  "success": true,
  "tool": "windows_list_directory",
  "output": {
    "success": true,
    "path": "C:\\",
    "entries": [
      "Program Files",
      "Program Files (x86)",
      "Users",
      "Windows",
      "PerfLogs"
    ],
    "count": 5
  },
  "error": null,
  "trace_id": "abc-123",
  "duration_ms": 1250,
  "exit_code": 0
}
```

**Error Response:**

```json
{
  "success": false,
  "tool": "windows_list_directory",
  "output": {
    "success": false,
    "error": "Authentication failed",
    "error_type": "InvalidCredentialsError"
  },
  "error": "Tool execution failed",
  "trace_id": "def-456",
  "duration_ms": 500,
  "exit_code": 1
}
```

## Security Best Practices

### 1. Use HTTPS in Production

Always use HTTPS (port 5986) with valid SSL certificates in production:

```yaml
# Tool configuration
port: 5986
use_ssl: true
```

### 2. Credential Management

**Never hardcode credentials:**

```typescript
// ❌ BAD - Hardcoded credentials
const params = {
  host: "192.168.1.100",
  username: "admin",
  password: "P@ssw0rd123"  // Never do this!
};

// ✅ GOOD - Prompt user for credentials
const username = prompt("Enter Windows username:");
const password = prompt("Enter Windows password:");
const params = {
  host: "192.168.1.100",
  username,
  password
};
```

**Use environment variables for service accounts:**

```bash
# .env (for automated tasks only)
WINDOWS_SERVICE_USER=svc_opsconductor
WINDOWS_SERVICE_PASS=<encrypted-password>
```

### 3. Least Privilege

Create dedicated service accounts with minimal permissions:

```powershell
# Create service account
New-LocalUser -Name "svc_opsconductor" -Description "OpsConductor Service Account"

# Grant only necessary permissions
Add-LocalGroupMember -Group "Remote Management Users" -Member "svc_opsconductor"

# Restrict to specific directories
$acl = Get-Acl "C:\Monitoring"
$rule = New-Object System.Security.AccessControl.FileSystemAccessRule(
    "svc_opsconductor", "ReadAndExecute", "Allow"
)
$acl.SetAccessRule($rule)
Set-Acl "C:\Monitoring" $acl
```

### 4. Network Segmentation

Restrict WinRM access using firewall rules:

```powershell
# Allow WinRM only from specific IP ranges
New-NetFirewallRule -Name "WinRM-HTTPS-Restricted" `
    -DisplayName "WinRM HTTPS (Restricted)" `
    -Enabled True -Direction Inbound -Protocol TCP -LocalPort 5986 `
    -RemoteAddress 10.0.0.0/8, 192.168.0.0/16
```

### 5. Audit Logging

Enable WinRM audit logging:

```powershell
# Enable WinRM logging
wevtutil sl Microsoft-Windows-WinRM/Operational /e:true

# View WinRM logs
Get-WinEvent -LogName Microsoft-Windows-WinRM/Operational -MaxEvents 50
```

### 6. Password Redaction

OpsConductor automatically redacts passwords in logs:

```python
# Redaction patterns in tool specification
redact_patterns:
  - "(?i)(password|pwd|secret|token|key)\\s*[=:]\\s*[^\\s&]+"
  - "(?i)password=[^&\\s]+"
  - "(?i)auth[^\\s]*\\s*[=:]\\s*[^\\s]+"
```

## Troubleshooting

### Issue: Connection Refused

**Symptoms:**
```
Connection refused: 192.168.1.100:5985
```

**Solutions:**
1. Verify WinRM service is running:
   ```powershell
   Get-Service WinRM
   ```
2. Check firewall rules:
   ```powershell
   Get-NetFirewallRule -Name "WinRM-*"
   ```
3. Test connectivity:
   ```bash
   telnet 192.168.1.100 5985
   ```

### Issue: Authentication Failed

**Symptoms:**
```
Authentication failed: Invalid credentials
```

**Solutions:**
1. Verify username/password are correct
2. Check domain is specified if using domain account
3. Verify user has WinRM permissions:
   ```powershell
   Get-LocalGroupMember -Group "Remote Management Users"
   ```
4. Check authentication methods:
   ```powershell
   Get-Item WSMan:\localhost\Service\Auth\*
   ```

### Issue: Access Denied

**Symptoms:**
```
Access denied: Insufficient permissions
```

**Solutions:**
1. Verify user has read permissions on target directory
2. Check UAC settings (may need admin account)
3. Verify user is in correct groups:
   ```powershell
   whoami /groups
   ```

### Issue: SSL Certificate Error

**Symptoms:**
```
SSL certificate verification failed
```

**Solutions:**
1. Use `use_ssl: false` for development (HTTP)
2. Install valid SSL certificate on Windows host
3. Configure certificate validation in OpsConductor

### Issue: Timeout

**Symptoms:**
```
Operation timed out after 15 seconds
```

**Solutions:**
1. Increase timeout parameter:
   ```json
   {
     "timeout_s": 30
   }
   ```
2. Check network latency
3. Verify Windows host is not overloaded

## Testing

### Test WinRM Connectivity

```bash
# Test from OpsConductor host
python3 -c "
import winrm
session = winrm.Session(
    'http://192.168.1.100:5985/wsman',
    auth=('username', 'password')
)
result = session.run_cmd('echo', ['Hello'])
print(result.std_out.decode())
"
```

### Test windows_list_directory Tool

```bash
# Test via API
curl -X POST http://localhost:3000/ai/tools/execute \
  -H "Content-Type: application/json" \
  -d '{
    "name": "windows_list_directory",
    "params": {
      "host": "192.168.50.211",
      "path": "C:\\",
      "username": "Administrator",
      "password": "YourPassword"
    }
  }' | jq
```

### Test via Chat Interface

```
show directory of c drive on 192.168.50.211
```

Expected: Prompt for credentials, then display directory listing

## Performance Considerations

### Typical Latencies

| Operation | Latency | Notes |
|-----------|---------|-------|
| WinRM connection | 100-500ms | Depends on network |
| Directory listing | 200-1000ms | Depends on file count |
| Total execution | 500-2000ms | Within 2s target |

### Optimization Tips

1. **Use local accounts** - Faster than domain authentication
2. **Limit directory depth** - Don't list recursive directories
3. **Use specific paths** - Avoid listing large directories like `C:\Windows`
4. **Connection pooling** - Reuse WinRM sessions (future enhancement)

## Future Enhancements

### Planned Windows Tools

1. **windows_service_status** - Check Windows service status
2. **windows_process_list** - List running processes
3. **windows_event_log** - Query Windows Event Log
4. **windows_disk_space** - Check disk space
5. **windows_registry_read** - Read registry values
6. **windows_run_script** - Execute PowerShell scripts

### Credential Management

1. **Credential Vault** - Secure storage for Windows credentials
2. **SSO Integration** - Use Active Directory authentication
3. **Certificate-based Auth** - Use client certificates instead of passwords

## References

- [Microsoft WinRM Documentation](https://docs.microsoft.com/en-us/windows/win32/winrm/portal)
- [pywinrm Documentation](https://github.com/diyan/pywinrm)
- [PowerShell Remoting Guide](https://docs.microsoft.com/en-us/powershell/scripting/learn/remoting/running-remote-commands)
- [WinRM Security Best Practices](https://docs.microsoft.com/en-us/windows/win32/winrm/installation-and-configuration-for-windows-remote-management)