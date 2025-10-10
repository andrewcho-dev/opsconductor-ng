# PSExec Integration for OpsConductor (Impacket-based)

## Overview

This document describes the integration of remote Windows execution capabilities using **Impacket's WMI** functionality to solve the problem of launching GUI applications on remote Windows systems.

## Problem Statement

When using PowerShell remoting (`Invoke-Command` via WinRM) to launch GUI applications like `notepad.exe` on remote Windows systems, the application hangs indefinitely because:

1. **Session 0 Isolation**: PowerShell remoting runs in Session 0, which is a non-interactive session with no desktop
2. **No GUI Support**: GUI applications cannot display in Session 0
3. **Process Blocking**: The automation service waits for the process to complete, causing a 300-second timeout
4. **No User Interaction**: Even if the GUI launches, there's no way for users to interact with it

## Solution: Impacket WMI Execution

Instead of using the native Windows PSExec tool (which only runs on Windows), we use **Impacket**, a Python library that implements Windows protocols and can execute commands remotely via WMI from Linux to Windows.

### Why Impacket?

- ✅ **Cross-platform**: Works from Linux to Windows (our automation service runs on Linux)
- ✅ **Pure Python**: Easy to install via pip, no external binaries needed
- ✅ **WMI-based**: Uses Windows Management Instrumentation for remote execution
- ✅ **Non-blocking**: Can launch processes without waiting for completion
- ✅ **GUI Support**: Processes appear on the remote desktop if a user is logged in
- ✅ **No Session 0**: Processes run in the user's session context

### How It Works

1. **DCOM Connection**: Establishes a DCOM connection to the target Windows system
2. **WMI Interface**: Creates a WMI interface to `Win32_Process` class
3. **Process Creation**: Uses `Win32_Process.Create()` to launch the command
4. **Non-blocking Mode**: Returns immediately without waiting for process completion
5. **GUI Display**: If a user is logged in, GUI applications appear on their desktop

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                     OpsConductor AI Pipeline                     │
│                        (Orchestration)                           │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             │ HTTP Request
                             │ (Plan Execution)
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│                   Automation Service (Linux)                     │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │              Windows PSExec Library                       │  │
│  │              (Impacket-based)                             │  │
│  │  ┌────────────────────────────────────────────────────┐  │  │
│  │  │  1. Establish DCOM connection                      │  │  │
│  │  │  2. Create WMI interface (Win32_Process)           │  │  │
│  │  │  3. Execute Win32_Process.Create(command)          │  │  │
│  │  │  4. Return immediately (non-blocking)              │  │  │
│  │  └────────────────────────────────────────────────────┘  │  │
│  └──────────────────────────────────────────────────────────┘  │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             │ SMB (445) + DCOM/WMI (135 + RPC)
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│                    Target Windows System                         │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │  Process launched in user session                         │  │
│  │  GUI appears on remote desktop                            │  │
│  │  (if user is logged in)                                   │  │
│  └──────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
```

## Implementation Details

### 1. Library: `automation-service/libraries/windows_psexec.py`

The library provides:
- `test_connection()`: Test WMI connectivity to target
- `execute_command()`: Execute commands with blocking or non-blocking mode

**Key Features:**
- Uses Impacket's `DCOMConnection` and `wmi` modules
- Supports both blocking (wait=True) and non-blocking (wait=False) execution
- Automatic retry logic (3 attempts with 5-second delays)
- Comprehensive error handling and logging
- Domain account support

### 2. Tool Definition: `pipeline/stages/stage_b/windows_tools_registry.py`

Registered as `windows-psexec` tool with capabilities:
- `psexec_execute`: Execute commands remotely
- `psexec_gui_launch`: Launch GUI applications
- `psexec_background`: Execute in background

### 3. Automation Service Integration: `automation-service/main_clean.py`

- Added PSExec connection manager initialization
- Implemented `_execute_psexec_command()` method
- Added `psexec` connection type to dispatcher
- Plan execution endpoint handles `windows-psexec` tool

## Usage Examples

### Example 1: Launch Notepad (Non-blocking)

**AI Request:**
```
"Launch notepad.exe on 192.168.50.210"
```

**Generated Plan:**
```json
{
  "steps": [
    {
      "tool": "windows-psexec",
      "inputs": {
        "target_host": "192.168.50.210",
        "command": "notepad.exe",
        "username": "administrator",
        "password": "password",
        "wait": false
      }
    }
  ]
}
```

**Result:**
- Notepad launches immediately on the remote desktop
- Command returns success without waiting
- User can interact with notepad on the remote screen

### Example 2: Run Command and Get Output (Blocking)

**AI Request:**
```
"Get IP configuration from 192.168.50.210"
```

**Generated Plan:**
```json
{
  "steps": [
    {
      "tool": "windows-psexec",
      "inputs": {
        "target_host": "192.168.50.210",
        "command": "ipconfig /all",
        "username": "administrator",
        "password": "password",
        "wait": true
      }
    }
  ]
}
```

**Result:**
- Command executes and waits for completion
- Output is captured and returned
- Exit code indicates success/failure

### Example 3: Domain Account

**AI Request:**
```
"Launch calculator on CORP\\workstation01 using domain admin"
```

**Generated Plan:**
```json
{
  "steps": [
    {
      "tool": "windows-psexec",
      "inputs": {
        "target_host": "workstation01",
        "command": "calc.exe",
        "username": "admin",
        "password": "password",
        "domain": "CORP",
        "wait": false
      }
    }
  ]
}
```

## Requirements

### Software Requirements

1. **Impacket Library** (Python)
   ```bash
   pip install impacket
   ```
   Already included in `automation-service/shared/requirements.txt`

2. **Network Access**
   - SMB: Port 445 (TCP)
   - DCOM: Port 135 (TCP)
   - Dynamic RPC: Ports 49152-65535 (TCP) - Windows firewall typically allows these

### Target System Requirements

1. **Administrative Credentials**: User must have admin rights on target
2. **SMB Enabled**: File sharing must be enabled
3. **WMI Enabled**: Windows Management Instrumentation service must be running
4. **Firewall Rules**: Allow SMB and DCOM/WMI traffic from automation service

### Network Requirements

- Direct network connectivity from automation service to target Windows systems
- No NAT or firewall blocking SMB/DCOM ports
- DNS resolution or IP address access

## Security Considerations

### Authentication

- **Credentials in Transit**: Impacket uses NTLM authentication (encrypted)
- **Credential Storage**: Credentials are passed in API requests (should use vault in production)
- **Domain Support**: Supports both local and domain accounts

### Authorization

- **Admin Required**: Target user must have administrative privileges
- **Permission Level**: Tool marked as `PermissionLevel.ADMIN`
- **Production Safety**: Marked as `production_safe=False` for extra caution

### Audit Trail

- All executions are logged with structured logging
- Execution history maintained in automation service
- Includes: timestamp, user, target, command, result

### Best Practices

1. **Use Service Accounts**: Create dedicated service accounts with minimal required privileges
2. **Credential Vaulting**: Store credentials in HashiCorp Vault or similar
3. **Network Segmentation**: Restrict automation service network access
4. **Monitoring**: Monitor for unusual WMI activity on target systems
5. **Least Privilege**: Only grant admin rights where absolutely necessary

## Troubleshooting

### Issue: "Impacket library not available"

**Cause**: Impacket not installed in automation service container

**Solution**:
```bash
# Rebuild automation service with updated requirements
docker compose build automation-service
docker compose up -d automation-service
```

### Issue: "WMI connection failed"

**Possible Causes:**
1. Firewall blocking SMB (445) or DCOM (135)
2. WMI service not running on target
3. Invalid credentials
4. Network connectivity issues

**Troubleshooting Steps:**
```bash
# Test SMB connectivity
smbclient -L //target_ip -U username

# Test WMI connectivity (from Linux)
impacket-wmiexec username:password@target_ip "whoami"

# Check firewall rules on target (from Windows)
netsh advfirewall firewall show rule name=all | findstr WMI
```

### Issue: "GUI application doesn't appear"

**Possible Causes:**
1. No user logged in to remote system
2. Process launched in Session 0 (shouldn't happen with WMI)
3. Application requires elevation (UAC prompt)

**Solution:**
- Ensure a user is logged in to the remote desktop
- Check Task Manager on remote system for the process
- Disable UAC or use pre-elevated account

### Issue: "Command times out"

**Cause**: Blocking mode (wait=True) used with long-running or GUI application

**Solution**: Use non-blocking mode (wait=False) for GUI applications
```json
{
  "wait": false
}
```

## Comparison: PowerShell Remoting vs Impacket WMI

| Feature | PowerShell Remoting (WinRM) | Impacket WMI |
|---------|----------------------------|--------------|
| **Session** | Session 0 (non-interactive) | User session (interactive) |
| **GUI Support** | ❌ No | ✅ Yes (if user logged in) |
| **Output Capture** | ✅ Excellent | ⚠️ Limited (blocking mode only) |
| **Non-blocking** | ❌ Difficult | ✅ Easy |
| **Ports** | 5985/5986 (HTTP/HTTPS) | 445, 135, RPC |
| **Protocol** | WinRM/SOAP | SMB/DCOM/WMI |
| **From Linux** | ✅ Yes (pywinrm) | ✅ Yes (impacket) |
| **Best For** | Scripts, commands, automation | GUI apps, interactive tools |

## Future Enhancements

1. **Session Discovery**: Automatically detect active user sessions
2. **GUI Detection**: Auto-detect GUI applications and set wait=false
3. **Credential Vaulting**: Integration with HashiCorp Vault
4. **Output Streaming**: Real-time output for blocking mode
5. **Process Monitoring**: Track launched processes and their status
6. **Alternative Protocols**: Support for other Impacket tools (smbexec, atexec)

## References

- [Impacket GitHub](https://github.com/fortra/impacket)
- [Impacket Documentation](https://www.coresecurity.com/core-labs/impacket)
- [WMI Win32_Process Class](https://docs.microsoft.com/en-us/windows/win32/cimwin32prov/win32-process)
- [DCOM Protocol](https://docs.microsoft.com/en-us/openspecs/windows_protocols/ms-dcom/)

## Support

For issues or questions:
1. Check automation service logs: `docker compose logs automation-service`
2. Verify Impacket installation: `docker compose exec automation-service pip list | grep impacket`
3. Test connectivity manually: `impacket-wmiexec username:password@target "whoami"`