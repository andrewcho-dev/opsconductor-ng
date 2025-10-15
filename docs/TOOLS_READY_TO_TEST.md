# TOOLS READY TO TEST - QUICK REFERENCE

**Last Updated:** 2025-01-XX  
**Status:** Ready for manual testing in AI frontend

---

## ✅ GUARANTEED TO WORK (Test These First)

These tools have been verified to have all required metadata and should work with the Unified Execution Framework.

### Prerequisites:
- Asset with proper credentials configured in asset-service
- Target host accessible from automation-service
- Proper network connectivity

---

## 🪟 WINDOWS POWERSHELL CMDLETS (33 tools)

**Connection Type:** PowerShell (WinRM)  
**Requires Credentials:** Yes (auto-fetched from asset-service)  
**Requires Target Host:** Yes

### System Information
| Tool Name | Description | Example Parameters |
|-----------|-------------|-------------------|
| `Get-ComputerInfo` | Get detailed computer information | `host: "192.168.1.100"` |
| `Get-Hotfix` | List installed Windows updates | `host: "192.168.1.100"` |
| `Get-WmiObject` | Query WMI objects | `host: "192.168.1.100", class: "Win32_OperatingSystem"` |

### Services
| Tool Name | Description | Example Parameters |
|-----------|-------------|-------------------|
| `Get-Service` | Query Windows services | `host: "192.168.1.100", name: "Spooler"` |

### Processes
| Tool Name | Description | Example Parameters |
|-----------|-------------|-------------------|
| `Get-Process` | List running processes | `host: "192.168.1.100"` |

### Event Logs
| Tool Name | Description | Example Parameters |
|-----------|-------------|-------------------|
| `Get-EventLog` | Read Windows event logs | `host: "192.168.1.100", log_name: "System"` |
| `Get-WinEvent` | Query Windows event logs (newer) | `host: "192.168.1.100", log_name: "Application"` |

### Disk & Storage
| Tool Name | Description | Example Parameters |
|-----------|-------------|-------------------|
| `Get-Disk` | List physical disks | `host: "192.168.1.100"` |
| `Get-Volume` | List volumes and partitions | `host: "192.168.1.100"` |

### Network
| Tool Name | Description | Example Parameters |
|-----------|-------------|-------------------|
| `Get-NetAdapter` | List network adapters | `host: "192.168.1.100"` |
| `Get-NetIPAddress` | List IP addresses | `host: "192.168.1.100"` |
| `Get-NetRoute` | List routing table | `host: "192.168.1.100"` |
| `Test-Connection` | Ping test | `host: "192.168.1.100", target: "8.8.8.8"` |
| `Test-NetConnection` | Advanced network test | `host: "192.168.1.100", computer_name: "google.com", port: 443` |

### Users & Groups
| Tool Name | Description | Example Parameters |
|-----------|-------------|-------------------|
| `Get-LocalUser` | List local users | `host: "192.168.1.100"` |
| `Get-LocalGroup` | List local groups | `host: "192.168.1.100"` |
| `Get-ADUser` | Query Active Directory users | `host: "192.168.1.100", identity: "jdoe"` |
| `Get-ADComputer` | Query AD computers | `host: "192.168.1.100", filter: "*"` |
| `Get-ADGroup` | Query AD groups | `host: "192.168.1.100", identity: "Domain Admins"` |
| `Get-ADGroupMember` | List AD group members | `host: "192.168.1.100", identity: "Domain Admins"` |

### Files & Security
| Tool Name | Description | Example Parameters |
|-----------|-------------|-------------------|
| `Get-FileHash` | Calculate file hash | `host: "192.168.1.100", path: "C:\\file.txt"` |
| `Get-Acl` | Get file/folder ACL | `host: "192.168.1.100", path: "C:\\folder"` |
| `Test-Path` | Check if path exists | `host: "192.168.1.100", path: "C:\\file.txt"` |

### Scheduled Tasks
| Tool Name | Description | Example Parameters |
|-----------|-------------|-------------------|
| `Get-ScheduledTask` | List scheduled tasks | `host: "192.168.1.100"` |
| `Register-ScheduledTask` | Create scheduled task | `host: "192.168.1.100", task_name: "MyTask"` |
| `schtasks` | Manage scheduled tasks (legacy) | `host: "192.168.1.100", command: "/Query"` |

### Performance
| Tool Name | Description | Example Parameters |
|-----------|-------------|-------------------|
| `Get-Counter` | Get performance counters | `host: "192.168.1.100", counter: "\\Processor(_Total)\\% Processor Time"` |
| `Measure-Command` | Measure command execution time | `host: "192.168.1.100", script_block: "Get-Process"` |

### Utilities
| Tool Name | Description | Example Parameters |
|-----------|-------------|-------------------|
| `Invoke-Command` | Execute PowerShell command | `host: "192.168.1.100", script_block: "Get-Service"` |
| `Invoke-WebRequest` | HTTP request | `host: "192.168.1.100", uri: "https://example.com"` |
| `Start-Job` | Start background job | `host: "192.168.1.100", script_block: "Get-Process"` |
| `powershell` | Execute PowerShell script | `host: "192.168.1.100", command: "Get-Date"` |

---

## 🐧 LINUX COMMANDS (56 tools)

**Connection Type:** SSH  
**Requires Credentials:** Yes (auto-fetched from asset-service)  
**Requires Target Host:** Yes

### System Information
| Tool Name | Description | Example Parameters |
|-----------|-------------|-------------------|
| `uname` | System information | `host: "192.168.1.100", a: true` |
| `hostname` | Display hostname | `host: "192.168.1.100"` |
| `uptime` | System uptime | `host: "192.168.1.100"` |
| `whoami` | Current user | `host: "192.168.1.100"` |
| `id` | User ID information | `host: "192.168.1.100"` |
| `lsb_release` | Linux distribution info | `host: "192.168.1.100", a: true` |

### Process Management
| Tool Name | Description | Example Parameters |
|-----------|-------------|-------------------|
| `ps` | List processes | `host: "192.168.1.100", aux: true` |
| `top` | Process monitor | `host: "192.168.1.100", b: true, n: 1` |
| `pgrep` | Find process by name | `host: "192.168.1.100", pattern: "nginx"` |
| `pkill` | Kill process by name | `host: "192.168.1.100", pattern: "nginx"` |
| `kill` | Kill process by PID | `host: "192.168.1.100", pid: 1234` |
| `killall` | Kill all processes by name | `host: "192.168.1.100", name: "nginx"` |
| `nice` | Run with priority | `host: "192.168.1.100", n: 10, command: "script.sh"` |
| `renice` | Change process priority | `host: "192.168.1.100", priority: 10, pid: 1234` |

### Disk & Storage
| Tool Name | Description | Example Parameters |
|-----------|-------------|-------------------|
| `df` | Disk space usage | `host: "192.168.1.100", h: true` |
| `du` | Directory space usage | `host: "192.168.1.100", sh: true, path: "/var"` |
| `free` | Memory usage | `host: "192.168.1.100", h: true` |

### File Operations
| Tool Name | Description | Example Parameters |
|-----------|-------------|-------------------|
| `ls` | List files | `host: "192.168.1.100", l: true, path: "/etc"` |
| `cat` | Display file contents | `host: "192.168.1.100", file: "/etc/hosts"` |
| `head` | Display first lines | `host: "192.168.1.100", n: 10, file: "/var/log/syslog"` |
| `tail` | Display last lines | `host: "192.168.1.100", n: 10, file: "/var/log/syslog"` |
| `find` | Find files | `host: "192.168.1.100", path: "/var", name: "*.log"` |
| `grep` | Search text | `host: "192.168.1.100", pattern: "error", file: "/var/log/syslog"` |
| `awk` | Text processing | `host: "192.168.1.100", script: "{print $1}", file: "data.txt"` |
| `sed` | Stream editor | `host: "192.168.1.100", script: "s/old/new/g", file: "file.txt"` |
| `cut` | Cut columns | `host: "192.168.1.100", d: ":", f: 1, file: "/etc/passwd"` |
| `sort` | Sort lines | `host: "192.168.1.100", file: "data.txt"` |
| `uniq` | Remove duplicates | `host: "192.168.1.100", file: "data.txt"` |
| `chmod` | Change permissions | `host: "192.168.1.100", mode: "755", file: "script.sh"` |
| `chown` | Change ownership | `host: "192.168.1.100", owner: "user:group", file: "file.txt"` |

### Network
| Tool Name | Description | Example Parameters |
|-----------|-------------|-------------------|
| `ping` | Network connectivity | `host: "192.168.1.100", c: 4, target: "8.8.8.8"` |
| `traceroute` | Trace network path | `host: "192.168.1.100", target: "google.com"` |
| `netstat` | Network statistics | `host: "192.168.1.100", tuln: true` |
| `ss` | Socket statistics | `host: "192.168.1.100", tuln: true` |
| `ifconfig` | Network interfaces | `host: "192.168.1.100"` |
| `ip` | IP configuration | `host: "192.168.1.100", command: "addr show"` |
| `iptables` | Firewall rules | `host: "192.168.1.100", L: true` |
| `dig` | DNS lookup | `host: "192.168.1.100", domain: "google.com"` |
| `nslookup` | DNS query | `host: "192.168.1.100", domain: "google.com"` |
| `host` | DNS lookup | `host: "192.168.1.100", domain: "google.com"` |
| `curl` | HTTP client | `host: "192.168.1.100", url: "https://example.com"` |

### Service Management
| Tool Name | Description | Example Parameters |
|-----------|-------------|-------------------|
| `systemctl` | Systemd service control | `host: "192.168.1.100", command: "status", service: "nginx"` |
| `service` | Service control (legacy) | `host: "192.168.1.100", service: "nginx", command: "status"` |
| `journalctl` | Systemd logs | `host: "192.168.1.100", u: "nginx", n: 100` |

### Scheduled Tasks
| Tool Name | Description | Example Parameters |
|-----------|-------------|-------------------|
| `crontab` | Cron jobs | `host: "192.168.1.100", l: true` |
| `at` | Schedule one-time task | `host: "192.168.1.100", time: "now + 1 hour", command: "script.sh"` |
| `systemd-timer` | Systemd timers | `host: "192.168.1.100", command: "list-timers"` |

### User Management
| Tool Name | Description | Example Parameters |
|-----------|-------------|-------------------|
| `useradd` | Add user | `host: "192.168.1.100", username: "newuser"` |
| `usermod` | Modify user | `host: "192.168.1.100", username: "user", option: "-aG sudo"` |
| `passwd` | Change password | `host: "192.168.1.100", username: "user"` |
| `sudo` | Execute as root | `host: "192.168.1.100", command: "systemctl restart nginx"` |

### Security
| Tool Name | Description | Example Parameters |
|-----------|-------------|-------------------|
| `openssl` | SSL/TLS toolkit | `host: "192.168.1.100", command: "version"` |
| `ssh-keygen` | Generate SSH keys | `host: "192.168.1.100", t: "rsa", b: 4096` |
| `fail2ban-client` | Fail2ban management | `host: "192.168.1.100", command: "status"` |

---

## 🌐 NETWORK TOOLS (20 tools)

**Connection Type:** Local (runs on automation-service container)  
**Requires Credentials:** No  
**Requires Target Host:** No (target specified in parameters)

**⚠️ Note:** These tools must be installed in the automation-service container.

### Port Scanning
| Tool Name | Description | Example Parameters |
|-----------|-------------|-------------------|
| `nmap` | Network scanner | `target: "192.168.1.0/24", p: "1-1000"` |
| `masscan` | Fast port scanner | `target: "192.168.1.0/24", p: "1-65535"` |
| `arp-scan` | ARP scanner | `interface: "eth0"` |
| `netdiscover` | Network discovery | `r: "192.168.1.0/24"` |

### Packet Capture
| Tool Name | Description | Example Parameters |
|-----------|-------------|-------------------|
| `tcpdump` | Packet capture | `i: "eth0", c: 100` |
| `tshark` | Wireshark CLI | `i: "eth0", c: 100` |
| `tcpflow` | TCP flow capture | `i: "eth0"` |
| `ngrep` | Network grep | `pattern: "GET", i: "eth0"` |

### Protocol Analyzers
| Tool Name | Description | Example Parameters |
|-----------|-------------|-------------------|
| `pyshark` | Python packet analysis | `interface: "eth0", count: 100` |
| `scapy` | Packet manipulation | `script: "sniff(count=10)"` |
| `dpkt` | Packet parsing | `file: "capture.pcap"` |
| `dns_analyzer` | DNS analysis | `pcap_file: "capture.pcap"` |
| `http_analyzer` | HTTP analysis | `pcap_file: "capture.pcap"` |
| `tcp_analyzer` | TCP analysis | `pcap_file: "capture.pcap"` |
| `udp_analyzer` | UDP analysis | `pcap_file: "capture.pcap"` |
| `ftp_analyzer` | FTP analysis | `pcap_file: "capture.pcap"` |
| `tls_analyzer` | TLS analysis | `pcap_file: "capture.pcap"` |
| `smtp_analyzer` | SMTP analysis | `pcap_file: "capture.pcap"` |
| `ssh_analyzer` | SSH analysis | `pcap_file: "capture.pcap"` |

---

## 🗄️ CUSTOM TOOLS (5 tools)

**Connection Type:** API (calls other services)  
**Requires Credentials:** No (uses service-to-service auth)  
**Requires Target Host:** No

### Asset Management
| Tool Name | Description | Example Parameters |
|-----------|-------------|-------------------|
| `asset-query` | Query asset inventory | `query: "type:server"` |
| `asset-list` | List all assets | `limit: 100` |
| `asset-create` | Create new asset | `name: "server-01", type: "server"` |
| `asset-update` | Update asset | `asset_id: 123, name: "new-name"` |
| `asset-delete` | Delete asset | `asset_id: 123` |

---

## 📋 TESTING CHECKLIST

### Before Testing:
- [ ] Asset-service is running and accessible
- [ ] Target assets are configured with credentials
- [ ] Network connectivity is verified
- [ ] Automation-service can reach target hosts

### Test Sequence:

#### Phase 1: Basic Connectivity
1. [ ] Test `asset-query` to verify asset-service connection
2. [ ] Test `Test-Connection` on Windows host
3. [ ] Test `ping` on Linux host

#### Phase 2: System Information
4. [ ] Test `Get-ComputerInfo` on Windows
5. [ ] Test `uname -a` on Linux
6. [ ] Test `Get-Service` on Windows
7. [ ] Test `systemctl status` on Linux

#### Phase 3: Process Management
8. [ ] Test `Get-Process` on Windows
9. [ ] Test `ps aux` on Linux

#### Phase 4: Network Tools
10. [ ] Test `nmap` (if installed)
11. [ ] Test `tcpdump` (if installed)

### Expected Results:
- ✅ Command builds correctly
- ✅ Credentials are resolved
- ✅ Connection is established
- ✅ Command executes successfully
- ✅ Output is returned

### Common Failure Modes:
- ❌ Credentials not found → Check asset-service configuration
- ❌ Connection timeout → Check network connectivity
- ❌ Permission denied → Check credential permissions
- ❌ Command not found → Check tool installation
- ❌ Invalid parameters → Check parameter format

---

## 🔍 TOOL SEARCH API

The automation service now provides a vector similarity search endpoint for finding tools:

### Endpoint
```
GET /api/selector/search
```

### Parameters
- `query` (required): Search query text (e.g., "network scan", "list processes")
- `k` (optional): Number of results to return (default: 5, range: 1-20)
- `platform` (optional): Comma-separated platform filters (e.g., "linux", "windows", "linux,windows")

### Examples

**Search for network tools on Linux:**
```bash
curl "http://localhost:3003/api/selector/search?query=network&platform=linux&k=3"
```

**Search for process management tools:**
```bash
curl "http://localhost:3003/api/selector/search?query=list%20processes&k=5"
```

**Search for Windows service tools:**
```bash
curl "http://localhost:3003/api/selector/search?query=windows%20services&platform=windows&k=5"
```

### Response Format
```json
{
  "query": "network",
  "k": 3,
  "platform": ["linux"],
  "results": [
    {
      "key": "nmap",
      "name": "Nmap Network Scanner",
      "short_desc": "Scan network for open ports and services",
      "platform": ["linux", "windows"],
      "tags": ["network", "security", "scanning"]
    }
  ]
}
```

---

## 🚨 IMPORTANT NOTES

### 1. Credential Resolution
All Windows and Linux tools require credentials. The Unified Execution Framework will:
1. Look for `use_asset_credentials: true` in parameters
2. Extract `asset_id` from parameters
3. Call asset-service to fetch credentials
4. Use credentials for connection

**If credentials are not found, the tool will fail.**

### 2. Parameter Mapping
The executor automatically maps parameters to command flags:
- Windows: `name: "Spooler"` → `-Name Spooler`
- Linux: `c: 4` → `-c 4`
- Network: `target: "192.168.1.1"` → `192.168.1.1`

### 3. Connection Types
- **PowerShell**: Uses WinRM (port 5985/5986)
- **SSH**: Uses SSH (port 22)
- **Local**: Runs on automation-service container
- **API**: Calls other services via HTTP

### 4. Timeouts
Default timeout is 300 seconds (5 minutes). Long-running commands may need increased timeout.

---

## 📞 SUPPORT

If a tool doesn't work:
1. Check the logs in automation-service
2. Verify credentials are configured
3. Test network connectivity manually
4. Check if tool is installed (for network tools)
5. Report the specific error message

---

**Ready to test? Start with Phase 1 of the testing checklist!**