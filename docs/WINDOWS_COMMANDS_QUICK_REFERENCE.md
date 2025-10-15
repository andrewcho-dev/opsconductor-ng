# Windows Impacket Commands - Quick Reference Card

## Most Common Commands

### Process Management

| Task | Command | Wait |
|------|---------|------|
| Launch Notepad | `notepad.exe` | false |
| Launch Calculator | `calc.exe` | false |
| List all processes | `tasklist` | true |
| Kill process by name | `taskkill /F /IM notepad.exe` | true |
| Kill process by PID | `taskkill /F /PID 1234` | true |
| Kill process tree | `taskkill /F /T /IM notepad.exe` | true |

### File Operations

| Task | Command | Wait |
|------|---------|------|
| List directory | `dir C:\Windows` | true |
| List recursively | `dir /S C:\Temp` | true |
| Show directory tree | `tree C:\Temp` | true |
| Copy file | `copy C:\source.txt C:\dest.txt` | true |
| Move file | `move C:\source.txt D:\dest.txt` | true |
| Delete file | `del C:\file.txt` | true |
| Rename file | `ren C:\old.txt new.txt` | true |
| Show file contents | `type C:\file.txt` | true |
| Create directory | `mkdir C:\NewFolder` | true |
| Remove directory | `rmdir /S /Q C:\Folder` | true |

### Network Commands

| Task | Command | Wait |
|------|---------|------|
| Ping host | `ping 8.8.8.8` | true |
| Ping 10 times | `ping -n 10 192.168.1.1` | true |
| Trace route | `tracert google.com` | true |
| DNS lookup | `nslookup google.com` | true |
| Show IP config | `ipconfig` | true |
| Show detailed IP | `ipconfig /all` | true |
| Flush DNS | `ipconfig /flushdns` | true |
| Show connections | `netstat -ano` | true |
| Show routing table | `route print` | true |
| Show hostname | `hostname` | true |
| Show MAC address | `getmac` | true |

### Service Management

| Task | Command | Wait |
|------|---------|------|
| List all services | `sc query` | true |
| Query service | `sc query Spooler` | true |
| Start service | `sc start Spooler` | true |
| Stop service | `sc stop Spooler` | true |
| Set auto-start | `sc config Spooler start= auto` | true |
| Disable service | `sc config Spooler start= disabled` | true |

### User Management

| Task | Command | Wait |
|------|---------|------|
| List all users | `net user` | true |
| Show user details | `net user username` | true |
| Create user | `net user username password /ADD` | true |
| Delete user | `net user username /DELETE` | true |
| Enable user | `net user username /ACTIVE:YES` | true |
| Disable user | `net user username /ACTIVE:NO` | true |
| List admins | `net localgroup Administrators` | true |
| Show current user | `whoami` | true |

### System Information

| Task | Command | Wait |
|------|---------|------|
| System info | `systeminfo` | true |
| OS version | `ver` | true |
| Computer name | `hostname` | true |
| CPU info | `wmic cpu get name,numberofcores` | true |
| RAM info | `wmic memorychip get capacity` | true |
| Disk info | `wmic diskdrive get model,size` | true |
| Installed software | `wmic product get name,version` | true |

### System Maintenance

| Task | Command | Wait |
|------|---------|------|
| Shutdown now | `shutdown /s /t 0` | true |
| Restart now | `shutdown /r /t 0` | true |
| Shutdown in 60s | `shutdown /s /t 60` | true |
| Cancel shutdown | `shutdown /a` | true |
| Log off user | `shutdown /l` | true |
| Update Group Policy | `gpupdate /force` | true |

## User Language → Command Translation

| User Says | Correct Command |
|-----------|----------------|
| "shutdown notepad" | `taskkill /F /IM notepad.exe` |
| "stop notepad" | `taskkill /F /IM notepad.exe` |
| "close notepad" | `taskkill /F /IM notepad.exe` |
| "kill notepad" | `taskkill /F /IM notepad.exe` |
| "list processes" | `tasklist` |
| "show running programs" | `tasklist` |
| "list files in C:\" | `dir C:\` |
| "get IP address" | `ipconfig` |
| "test connectivity" | `ping <target>` |
| "show system info" | `systeminfo` |
| "list users" | `net user` |
| "shutdown computer" | `shutdown /s /t 0` |
| "restart computer" | `shutdown /r /t 0` |

## Wait Parameter Rules

### wait: false
- **ONLY** for GUI applications
- Examples: notepad.exe, calc.exe, mspaint.exe, explorer.exe, taskmgr

### wait: true
- **ALL** command-line commands
- Examples: tasklist, taskkill, dir, ping, ipconfig, sc, net, systeminfo, etc.

## JSON Template

```json
{
  "tool": "windows-impacket-executor",
  "description": "Brief description",
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

## Path Escaping

In JSON, use double backslashes for Windows paths:
```json
"command": "dir C:\\\\Windows\\\\System32"
```

## Common WMI Error Codes

- **0**: Success
- **2**: Access denied (check credentials)
- **8**: Unknown failure
- **9**: Invalid object/path (command doesn't exist)
- **21**: Invalid parameter

## Tips

1. **Always use `wait: true` for commands that return output**
2. **Always use `wait: false` for GUI applications**
3. **Use `/F` flag with taskkill to force termination**
4. **Use double backslashes in JSON for Windows paths**
5. **Admin commands require admin credentials**
6. **Test with simple commands first (like `hostname` or `ver`)**