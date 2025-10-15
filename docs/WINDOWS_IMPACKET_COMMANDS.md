# Windows Impacket Executor - Comprehensive Command Reference

This document provides a complete reference for all Windows commands that can be executed via the `windows-impacket-executor` tool in OpsConductor.

## Overview

The Windows Impacket Executor uses Impacket's WMI capabilities to execute commands on remote Windows systems. It supports both GUI applications and command-line operations.

## Common Parameters

All Windows Impacket commands require these parameters:

- **target_host**: IP address or hostname of the Windows machine
- **username**: Windows username for authentication
- **password**: Windows password for authentication
- **connection_type**: "impacket" (to explicitly mark as Impacket WMI execution)
- **domain**: Windows domain (optional, empty string "" for local accounts)
- **wait**: true/false (see specific command categories below)

## Command Categories

### 1. GUI Applications (wait: false, interactive: true)

Launch GUI applications that appear on the remote desktop. **CRITICAL**: Always use `wait: false` for GUI apps!

**Examples:**
```json
{
  "command": "notepad.exe",
  "wait": false,
  "interactive": true
}
```

**Common GUI Applications:**
- `notepad.exe` - Notepad text editor
- `calc.exe` - Calculator
- `mspaint.exe` - Paint
- `explorer.exe` - Windows Explorer
- `taskmgr` - Task Manager
- `regedit.exe` - Registry Editor
- `cmd.exe` - Command Prompt window
- `powershell.exe` - PowerShell window

---

### 2. Process Management (wait: true)

#### List Processes

```bash
# List all running processes
tasklist

# Filter by process name
tasklist /FI "IMAGENAME eq notepad.exe"

# Verbose output with window titles
tasklist /V

# Show services in each process
tasklist /SVC
```

#### Kill/Terminate Processes

```bash
# Kill by process name (force)
taskkill /F /IM processname.exe

# Kill by process ID
taskkill /F /PID 1234

# Kill process tree (parent and all children)
taskkill /F /T /IM processname.exe

# Kill gracefully (without /F flag)
taskkill /IM notepad.exe

# Kill multiple processes
taskkill /F /IM notepad.exe /IM calc.exe
```

**Common User Requests → Correct Commands:**
- "shutdown notepad" → `taskkill /F /IM notepad.exe`
- "stop notepad" → `taskkill /F /IM notepad.exe`
- "close notepad" → `taskkill /F /IM notepad.exe`
- "kill notepad" → `taskkill /F /IM notepad.exe`
- "terminate notepad" → `taskkill /F /IM notepad.exe`

---

### 3. File Operations (wait: true)

#### Directory Listing

```bash
# List directory contents
dir C:\Windows

# Recursive listing
dir /S C:\Temp

# Display directory tree
tree C:\Temp

# Show hidden files
dir /A C:\Windows

# Show only directories
dir /AD C:\Windows
```

#### File Manipulation

```bash
# Copy file
copy C:\source.txt C:\dest.txt

# Move file
move C:\source.txt D:\dest.txt

# Delete file
del C:\file.txt

# Rename file
ren C:\old.txt new.txt

# Display file contents
type C:\file.txt

# Create/overwrite file
echo Hello > C:\file.txt

# Append to file
echo Hello >> C:\file.txt
```

#### Directory Operations

```bash
# Create directory
mkdir C:\NewFolder

# Remove empty directory
rmdir C:\Folder

# Remove directory recursively (force)
rmdir /S /Q C:\Folder
```

#### Advanced Copy Operations

```bash
# Copy directories recursively
xcopy C:\Source D:\Dest /E /I

# Robust file copy with all attributes
robocopy C:\Source D:\Dest /E /COPYALL

# Mirror directories (delete files in dest not in source)
robocopy C:\Source D:\Dest /MIR
```

#### File Attributes

```bash
# Set read-only
attrib +R C:\file.txt

# Remove hidden attribute
attrib -H C:\file.txt

# Set system and hidden
attrib +S +H C:\file.txt
```

---

### 4. Network Commands (wait: true)

#### Network Diagnostics

```bash
# Test connectivity
ping 8.8.8.8

# Ping 10 times
ping -n 10 192.168.1.1

# Trace route to host
tracert google.com

# DNS lookup
nslookup google.com

# Combined ping and traceroute
pathping 192.168.1.1
```

#### Network Configuration

```bash
# Display IP configuration
ipconfig

# Detailed IP configuration
ipconfig /all

# Flush DNS cache
ipconfig /flushdns

# Release DHCP lease
ipconfig /release

# Renew DHCP lease
ipconfig /renew

# Show all connections with PIDs
netstat -ano

# Display routing table
netstat -r

# Display ARP cache
arp -a

# Display routing table (alternative)
route print

# Display computer name
hostname

# Display MAC addresses
getmac
```

#### Network Shares

```bash
# List network shares
net share

# Create share
net share ShareName=C:\Folder /GRANT:Everyone,FULL

# Remove share
net share ShareName /DELETE

# Map network drive
net use Z: \\server\share

# Disconnect network drive
net use Z: /DELETE

# Show all mapped drives
net use
```

---

### 5. Service Management (wait: true)

```bash
# List all services
sc query

# Query specific service status
sc query ServiceName

# Start a service
sc start ServiceName

# Stop a service
sc stop ServiceName

# Set service to auto-start
sc config ServiceName start= auto

# Disable service
sc config ServiceName start= disabled

# Start service (alternative using net)
net start ServiceName

# Stop service (alternative using net)
net stop ServiceName
```

**Common Services:**
- `Spooler` - Print Spooler
- `wuauserv` - Windows Update
- `MSSQLSERVER` - SQL Server
- `W3SVC` - IIS Web Server
- `WinRM` - Windows Remote Management

---

### 6. User Management (wait: true)

```bash
# List all users
net user

# Display user details
net user username

# Create new user
net user username password /ADD

# Delete user
net user username /DELETE

# Enable user account
net user username /ACTIVE:YES

# Disable user account
net user username /ACTIVE:NO

# List admin group members
net localgroup Administrators

# Add user to admins
net localgroup Administrators username /ADD

# Display current user
whoami

# Display user's groups
whoami /groups

# Display user privileges
whoami /priv
```

---

### 7. System Information (wait: true)

```bash
# Detailed system information
systeminfo

# Display computer name
hostname

# Display Windows version
ver

# Get OS info via WMI
wmic os get caption,version

# Get CPU info
wmic cpu get name,numberofcores

# Get RAM info
wmic memorychip get capacity

# Get disk info
wmic diskdrive get model,size

# List installed software
wmic product get name,version

# List processes via WMI
wmic process list brief

# Get BIOS info
wmic bios get serialnumber,manufacturer
```

---

### 8. Registry Operations (wait: true)

```bash
# Query registry key
reg query HKLM\Software\Microsoft

# Add registry value
reg add HKLM\Software\MyApp /v Setting /t REG_SZ /d Value

# Delete registry value
reg delete HKLM\Software\MyApp /v Setting /f

# Export registry key
reg export HKLM\Software\MyApp C:\backup.reg

# Import registry file
reg import C:\backup.reg

# Query specific value
reg query HKLM\Software\MyApp /v Setting
```

**Registry Hives:**
- `HKLM` - HKEY_LOCAL_MACHINE
- `HKCU` - HKEY_CURRENT_USER
- `HKCR` - HKEY_CLASSES_ROOT
- `HKU` - HKEY_USERS
- `HKCC` - HKEY_CURRENT_CONFIG

---

### 9. Scheduled Tasks (wait: true)

```bash
# List all scheduled tasks
schtasks /Query

# Query specific task (verbose)
schtasks /Query /TN TaskName /V

# Create daily task
schtasks /Create /TN MyTask /TR C:\script.bat /SC DAILY /ST 09:00

# Create task that runs at startup
schtasks /Create /TN MyTask /TR C:\script.bat /SC ONSTART

# Run task immediately
schtasks /Run /TN TaskName

# Stop running task
schtasks /End /TN TaskName

# Delete task
schtasks /Delete /TN TaskName /F
```

---

### 10. Event Logs (wait: true)

```bash
# Query last 10 System events
wevtutil qe System /c:10 /f:text

# Query Application log
wevtutil qe Application /c:20 /f:text

# Query Security log
wevtutil qe Security /c:10 /f:text

# Clear System event log
wevtutil cl System

# List all event logs
wevtutil el
```

---

### 11. System Maintenance (wait: true)

```bash
# Shutdown immediately
shutdown /s /t 0

# Restart immediately
shutdown /r /t 0

# Shutdown with 60 second delay
shutdown /s /t 60

# Abort shutdown
shutdown /a

# Log off current user
shutdown /l

# Force Group Policy update
gpupdate /force

# System file checker (requires admin)
sfc /scannow

# Check disk for errors
chkdsk C:

# Check and repair disk
chkdsk C: /F

# Disk partition tool (interactive - may not work well via WMI)
diskpart
```

---

### 12. Performance Monitoring (wait: true)

```bash
# Launch Performance Monitor (GUI - use wait: false)
perfmon

# Launch Task Manager (GUI - use wait: false)
taskmgr

# Get CPU usage
wmic cpu get loadpercentage

# Get available RAM
wmic path Win32_PerfFormattedData_PerfOS_Memory get AvailableMBytes

# Get disk space
wmic logicaldisk get name,freespace,size
```

---

## Important Notes

### Wait Parameter Guide

- **wait: false** → Use for GUI applications (notepad, calc, mspaint, explorer, taskmgr, etc.)
- **wait: true** → Use for ALL command-line commands that should return output

### Path Escaping in JSON

When specifying Windows paths in JSON, use double backslashes:
```json
{
  "command": "dir C:\\\\Windows\\\\System32"
}
```

### Administrative Commands

Some commands require administrative privileges:
- Service management (`sc`, `net start/stop`)
- User management (`net user /ADD`, `net localgroup`)
- System maintenance (`shutdown`, `sfc`, `chkdsk`)
- Registry operations (writing to `HKLM`)

### Interactive Commands

Some commands are interactive and may not work well via WMI:
- `diskpart` (disk partition tool)
- `bcdedit` (boot configuration)
- Commands that require user input

### Common User Request Patterns

Users often use informal language. The LLM must translate these to correct Windows commands:

| User Says | Correct Command |
|-----------|----------------|
| "shutdown notepad" | `taskkill /F /IM notepad.exe` |
| "stop notepad" | `taskkill /F /IM notepad.exe` |
| "close notepad" | `taskkill /F /IM notepad.exe` |
| "kill notepad" | `taskkill /F /IM notepad.exe` |
| "list processes" | `tasklist` |
| "show running programs" | `tasklist` |
| "list files in C:\" | `dir C:\` |
| "check if service is running" | `sc query ServiceName` |
| "restart service" | `sc stop ServiceName` then `sc start ServiceName` |
| "get IP address" | `ipconfig` |
| "test connectivity to X" | `ping X` |
| "show system info" | `systeminfo` |
| "list users" | `net user` |
| "shutdown computer" | `shutdown /s /t 0` |
| "restart computer" | `shutdown /r /t 0` |

---

## Example JSON Plans

### Launch GUI Application

```json
{
  "tool": "windows-impacket-executor",
  "description": "Launch Notepad on Windows machine",
  "inputs": {
    "target_host": "192.168.50.211",
    "username": "stationadmin",
    "password": "password123",
    "command": "notepad.exe",
    "connection_type": "impacket",
    "wait": false,
    "interactive": true,
    "domain": ""
  }
}
```

### Kill Process

```json
{
  "tool": "windows-impacket-executor",
  "description": "Kill all Notepad instances",
  "inputs": {
    "target_host": "192.168.50.211",
    "username": "stationadmin",
    "password": "password123",
    "command": "taskkill /F /IM notepad.exe",
    "connection_type": "impacket",
    "wait": true,
    "domain": ""
  }
}
```

### List Directory

```json
{
  "tool": "windows-impacket-executor",
  "description": "List contents of Windows directory",
  "inputs": {
    "target_host": "192.168.50.211",
    "username": "stationadmin",
    "password": "password123",
    "command": "dir C:\\\\Windows",
    "connection_type": "impacket",
    "wait": true,
    "domain": ""
  }
}
```

### Network Diagnostics

```json
{
  "tool": "windows-impacket-executor",
  "description": "Test network connectivity",
  "inputs": {
    "target_host": "192.168.50.211",
    "username": "stationadmin",
    "password": "password123",
    "command": "ping -n 4 8.8.8.8",
    "connection_type": "impacket",
    "wait": true,
    "domain": ""
  }
}
```

### Service Management

```json
{
  "tool": "windows-impacket-executor",
  "description": "Query Print Spooler service status",
  "inputs": {
    "target_host": "192.168.50.211",
    "username": "stationadmin",
    "password": "password123",
    "command": "sc query Spooler",
    "connection_type": "impacket",
    "wait": true,
    "domain": ""
  }
}
```

### System Information

```json
{
  "tool": "windows-impacket-executor",
  "description": "Get detailed system information",
  "inputs": {
    "target_host": "192.168.50.211",
    "username": "stationadmin",
    "password": "password123",
    "command": "systeminfo",
    "connection_type": "impacket",
    "wait": true,
    "domain": ""
  }
}
```

---

## Troubleshooting

### WMI Error Codes

- **Error 0**: Success
- **Error 2**: Access denied (check credentials and permissions)
- **Error 8**: Unknown failure
- **Error 9**: Invalid object or path not found (command doesn't exist)
- **Error 21**: Invalid parameter

### Common Issues

1. **Command not found (Error 9)**
   - Verify the command exists on the target system
   - Check spelling and syntax
   - Ensure the command is in the system PATH

2. **Access denied (Error 2)**
   - Verify credentials are correct
   - Ensure user has administrative privileges for admin commands
   - Check Windows Firewall settings

3. **Timeout**
   - Increase timeout value for long-running commands
   - Check network connectivity
   - Verify WMI service is running on target

4. **GUI application doesn't appear**
   - Ensure a user is logged in on the remote desktop
   - Verify `wait: false` is set
   - Check if the application requires admin privileges

---

## Security Considerations

1. **Credentials**: Always use secure credential storage and transmission
2. **Administrative Access**: Many commands require admin privileges
3. **Firewall**: Ensure ports 135, 445, and dynamic RPC ports are open
4. **Audit Logging**: All commands are logged for security auditing
5. **Least Privilege**: Use accounts with minimum required privileges

---

## References

- [Microsoft Windows Commands Documentation](https://learn.microsoft.com/en-us/windows-server/administration/windows-commands/windows-commands)
- [Impacket Documentation](https://github.com/fortra/impacket)
- [WMI Reference](https://learn.microsoft.com/en-us/windows/win32/wmisdk/wmi-reference)