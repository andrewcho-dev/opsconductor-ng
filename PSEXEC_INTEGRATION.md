# PSExec Integration for GUI Application Support

## Overview

PSExec support has been added to OpsConductor to enable launching GUI applications and interactive processes on remote Windows systems. This addresses the limitation where PowerShell remoting (`Invoke-Command`) cannot launch GUI applications because it runs in a non-interactive Session 0.

## Problem Statement

When using PowerShell remoting (WinRM) to execute commands like `notepad.exe`, the system would hang indefinitely because:

1. **GUI applications don't exit on their own** - They wait for user interaction
2. **PowerShell remoting runs in Session 0** - A non-interactive session with no desktop
3. **The automation service waits for completion** - Causing a timeout after 300 seconds

## Solution: PSExec with Interactive Session Support

PSExec is a Sysinternals tool that allows remote execution with interactive desktop support using the `-i` flag.

### Key Differences

| Feature | PowerShell Remoting | PSExec |
|---------|-------------------|---------|
| Session Type | Session 0 (non-interactive) | Can target any session (0, 1, 2, etc.) |
| GUI Support | ❌ No | ✅ Yes (with `-i` flag) |
| Desktop Interaction | ❌ No | ✅ Yes |
| Non-blocking Execution | ❌ No | ✅ Yes (with `-d` flag) |
| Use Case | Scripts, commands | GUI apps, interactive processes |

## Implementation

### 1. PSExec Library (`automation-service/libraries/windows_psexec.py`)

A new library that wraps PSExec functionality:

**Features:**
- Connection testing
- Interactive session support (`-i` flag)
- Session ID targeting (e.g., `-i 1` for first logged-in user)
- Non-blocking execution (`-d` flag for GUI apps)
- Retry logic and error handling
- Comprehensive logging

**Key Methods:**
- `test_connection()` - Test PSExec connectivity to target
- `execute_command()` - Execute commands with full PSExec options
- `get_library_info()` - Get library capabilities and status

### 2. Tool Definition (`pipeline/stages/stage_b/windows_tools_registry.py`)

A new tool `windows-psexec` registered in the tool catalog:

**Capabilities:**
- `psexec_execute` - Execute commands remotely with PSExec
- `psexec_gui_launch` - Launch GUI applications on remote desktop
- `psexec_background` - Execute commands in background without waiting

**Required Inputs:**
- `target_host` - Target Windows host (IP or hostname)
- `command` - Command or application to execute

**Optional Inputs:**
- `username` - Username for authentication
- `password` - Password for authentication
- `interactive` - Enable interactive mode (boolean)
- `session_id` - Session ID for interactive mode (integer)
- `wait` - Wait for process completion (boolean, default: true)

### 3. Automation Service Integration (`automation-service/main_clean.py`)

**Changes:**
1. Added PSExec connection manager initialization
2. Added `psexec` connection type support
3. Implemented `_execute_psexec_command()` method
4. Added PSExec tool handling in plan execution

**Environment Variables for PSExec Options:**
- `interactive` - "true" or "false"
- `session_id` - Session ID as string (e.g., "1")
- `wait` - "true" or "false"

## Usage Examples

### Example 1: Launch Notepad Interactively

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
        "username": "admin",
        "password": "password",
        "interactive": true,
        "session_id": 1,
        "wait": false
      }
    }
  ]
}
```

**PSExec Command:**
```bash
psexec \\192.168.50.210 -u admin -p password -accepteula -i 1 -d notepad.exe
```

### Example 2: Launch Calculator in Background

**AI Request:**
```
"Open calculator on 192.168.50.210 session 2"
```

**Generated Plan:**
```json
{
  "steps": [
    {
      "tool": "windows-psexec",
      "inputs": {
        "target_host": "192.168.50.210",
        "command": "calc.exe",
        "username": "admin",
        "password": "password",
        "interactive": true,
        "session_id": 2,
        "wait": false
      }
    }
  ]
}
```

### Example 3: Run Command and Wait for Result

**AI Request:**
```
"Run ipconfig on 192.168.50.210 using PSExec"
```

**Generated Plan:**
```json
{
  "steps": [
    {
      "tool": "windows-psexec",
      "inputs": {
        "target_host": "192.168.50.210",
        "command": "cmd /c ipconfig",
        "username": "admin",
        "password": "password",
        "wait": true
      }
    }
  ]
}
```

## Session IDs Explained

Windows has multiple sessions:

- **Session 0** - Console session (services, non-interactive)
- **Session 1** - First logged-in user (typically the active desktop)
- **Session 2+** - Additional logged-in users (RDP sessions, etc.)

**To find active sessions on target:**
```powershell
query user
```

**Output example:**
```
 USERNAME              SESSIONNAME        ID  STATE   IDLE TIME  LOGON TIME
>administrator         console             1  Active          .  1/15/2024 10:30 AM
 user1                 rdp-tcp#0           2  Active          5  1/15/2024 11:00 AM
```

Use the `ID` column value for `session_id` parameter.

## Installation Requirements

### On Automation Service Host

PSExec must be installed on the machine running the automation service:

1. **Download PSExec:**
   - https://docs.microsoft.com/en-us/sysinternals/downloads/psexec
   - Or download entire Sysinternals Suite

2. **Install PSExec:**
   ```bash
   # Extract psexec.exe to a directory in PATH
   # For example: /usr/local/bin/ or C:\Windows\System32\
   ```

3. **Verify Installation:**
   ```bash
   psexec -?
   ```

### On Target Windows Systems

No special installation required, but:

1. **Enable File and Printer Sharing** (for admin$ share access)
2. **Ensure admin credentials** are available
3. **Firewall rules** must allow SMB (port 445)

## Security Considerations

⚠️ **Important Security Notes:**

1. **Admin Privileges Required** - PSExec requires administrative credentials
2. **Credentials in Transit** - Credentials are passed as command-line arguments
3. **Production Safety** - Tool is marked as `production_safe=False`
4. **Permission Level** - Requires `PermissionLevel.ADMIN`
5. **Audit Logging** - All PSExec executions are logged

**Best Practices:**
- Use PSExec only when PowerShell remoting is insufficient
- Prefer PowerShell remoting for non-GUI tasks
- Implement credential vaulting for production use
- Monitor and audit PSExec usage
- Restrict PSExec tool access to authorized users

## Troubleshooting

### PSExec Not Available

**Error:**
```
PSExec not available. Download from https://docs.microsoft.com/en-us/sysinternals/downloads/psexec
```

**Solution:**
1. Download and install PSExec on automation service host
2. Ensure `psexec` is in system PATH
3. Restart automation service

### Access Denied

**Error:**
```
Access is denied
```

**Solutions:**
1. Verify admin credentials are correct
2. Ensure target has File and Printer Sharing enabled
3. Check firewall allows SMB (port 445)
4. Verify user has admin rights on target

### GUI Not Appearing

**Issue:** Command succeeds but GUI doesn't appear

**Solutions:**
1. Verify `interactive=true` is set
2. Check `session_id` matches active user session
3. Use `query user` on target to find correct session
4. Ensure user is logged in to target desktop

### Process Exits Immediately

**Issue:** Process exits quickly when launched

**Solutions:**
1. Verify the application path is correct
2. Check if application requires arguments
3. Ensure application is installed on target
4. Review stderr output for error messages

## Files Modified

1. **`automation-service/libraries/windows_psexec.py`** (NEW)
   - PSExec library implementation

2. **`pipeline/stages/stage_b/windows_tools_registry.py`**
   - Added `windows-psexec` tool definition
   - Updated tool summary (20 → 21 tools)
   - Added PSExec capabilities

3. **`automation-service/main_clean.py`**
   - Added PSExec connection manager
   - Added `_execute_psexec_command()` method
   - Added PSExec support in plan execution
   - Added `psexec` connection type

## Testing

### Manual Test

```bash
# Test PSExec connectivity
curl -X POST http://localhost:3003/execute \
  -H "Content-Type: application/json" \
  -d '{
    "command": "notepad.exe",
    "target_host": "192.168.50.210",
    "connection_type": "psexec",
    "credentials": {
      "username": "admin",
      "password": "password"
    },
    "environment_vars": {
      "interactive": "true",
      "session_id": "1",
      "wait": "false"
    }
  }'
```

### Expected Result

```json
{
  "execution_id": "uuid-here",
  "status": "completed",
  "command": "notepad.exe",
  "exit_code": 0,
  "stdout": "Process launched successfully on 192.168.50.210",
  "stderr": "",
  "duration_seconds": 2.5,
  "details": {
    "interactive": true,
    "session_id": 1,
    "non_blocking": true,
    "message": "Process launched in background. GUI should appear on remote desktop."
  }
}
```

## Future Enhancements

1. **Session Discovery** - Automatically detect active user sessions
2. **GUI Detection** - Automatically detect if command is a GUI application
3. **Process Monitoring** - Track launched GUI processes
4. **Screenshot Capture** - Capture screenshots of launched GUI apps
5. **Credential Vaulting** - Integrate with secure credential storage
6. **PSExec Alternatives** - Support for other remote execution tools

## References

- [PSExec Documentation](https://docs.microsoft.com/en-us/sysinternals/downloads/psexec)
- [Windows Sessions Explained](https://docs.microsoft.com/en-us/windows/win32/termserv/terminal-services-sessions)
- [PowerShell Remoting Limitations](https://docs.microsoft.com/en-us/powershell/scripting/learn/remoting/running-remote-commands)

## Summary

PSExec integration provides a robust solution for launching GUI applications and interactive processes on remote Windows systems, addressing the limitations of PowerShell remoting. The implementation includes comprehensive error handling, logging, and security considerations while maintaining consistency with the existing automation service architecture.