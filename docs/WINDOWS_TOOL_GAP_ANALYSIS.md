# Windows Tool Gap Analysis
## Based on Windows CLI + PowerShell Cheat Sheet

**Date:** 2025-01-16  
**Current Windows Tools:** 63 tools in catalog

---

## ✅ RECENTLY ADDED (11 tools - Jan 2025)

These were identified as critical gaps and have been added:

1. **Get-Content** - Read file contents ✅
2. **Copy-Item** - Copy files/folders ✅
3. **Move-Item** - Move/rename ✅
4. **Remove-Item** - Delete ✅
5. **New-Item** - Create files/folders ✅
6. **Get-Item** - File properties ✅
7. **Select-String** - Search text ✅
8. **Stop-Process** - Kill processes ✅
9. **Start-Service** - Start services ✅
10. **Stop-Service** - Stop services ✅
11. **Restart-Service** - Restart services ✅

---

## 📊 COVERAGE ANALYSIS BY CATEGORY

### File & Directory Operations

| Command | Status | Priority | Notes |
|---------|--------|----------|-------|
| Get-ChildItem | ✅ EXISTS | - | List directory contents |
| Get-Content | ✅ ADDED | - | Read files |
| Set-Content | ❌ MISSING | **HIGH** | Write/overwrite file content |
| Add-Content | ❌ MISSING | **HIGH** | Append to files |
| Copy-Item | ✅ ADDED | - | Copy files/folders |
| Move-Item | ✅ ADDED | - | Move/rename |
| Remove-Item | ✅ ADDED | - | Delete |
| New-Item | ✅ ADDED | - | Create files/folders |
| Get-Item | ✅ ADDED | - | Get properties |
| Test-Path | ✅ EXISTS | - | Check if path exists |
| Select-String | ✅ ADDED | - | Search text (grep) |
| Get-FileHash | ✅ EXISTS | - | Calculate file hashes |

**Gap Summary:** Missing 2 critical file writing operations (Set-Content, Add-Content)

---

### Process Management

| Command | Status | Priority | Notes |
|---------|--------|----------|-------|
| Get-Process | ✅ EXISTS | - | List processes |
| Stop-Process | ✅ ADDED | - | Kill process |
| Start-Process | ❌ MISSING | **MEDIUM** | Start new process |
| Wait-Process | ❌ MISSING | LOW | Wait for process to exit |

**Gap Summary:** Missing Start-Process (needed for launching applications)

---

### Service Management

| Command | Status | Priority | Notes |
|---------|--------|----------|-------|
| Get-Service | ✅ EXISTS | - | List services |
| Start-Service | ✅ ADDED | - | Start service |
| Stop-Service | ✅ ADDED | - | Stop service |
| Restart-Service | ✅ ADDED | - | Restart service |
| Set-Service | ❌ MISSING | **MEDIUM** | Configure service properties |

**Gap Summary:** Missing Set-Service (for changing startup type, etc.)

---

### Networking

| Command | Status | Priority | Notes |
|---------|--------|----------|-------|
| Test-NetConnection | ✅ EXISTS | - | Test connectivity/ports |
| Resolve-DnsName | ❌ MISSING | **HIGH** | DNS lookups (nslookup) |
| Get-NetIPConfiguration | ❌ MISSING | **MEDIUM** | IP config (ipconfig) |
| Get-NetIPAddress | ✅ EXISTS | - | Get IP addresses |
| Get-NetAdapter | ✅ EXISTS | - | Network adapters |
| Get-NetRoute | ✅ EXISTS | - | Routing table |
| Get-NetTCPConnection | ❌ MISSING | **MEDIUM** | Active connections (netstat) |
| Invoke-WebRequest | ✅ EXISTS | - | HTTP requests |
| Invoke-RestMethod | ❌ MISSING | **MEDIUM** | REST API calls |
| New-NetFirewallRule | ❌ MISSING | LOW | Firewall rules (covered by manager) |

**Gap Summary:** Missing 5 networking tools, 2 are high priority (Resolve-DnsName, Get-NetTCPConnection)

---

### System Information

| Command | Status | Priority | Notes |
|---------|--------|----------|-------|
| Get-ComputerInfo | ✅ EXISTS | - | System information |
| Get-HotFix | ✅ EXISTS | - | Installed updates |
| Get-WmiObject | ✅ EXISTS | - | WMI queries |
| Get-CimInstance | ❌ MISSING | **MEDIUM** | CIM queries (modern WMI) |
| Get-WindowsFeature | ❌ MISSING | LOW | Server features |

**Gap Summary:** Missing Get-CimInstance (modern replacement for WMI)

---

### Event Logs

| Command | Status | Priority | Notes |
|---------|--------|----------|-------|
| Get-EventLog | ✅ EXISTS | - | Classic event logs |
| Get-WinEvent | ✅ EXISTS | - | Modern event logs |

**Gap Summary:** Complete coverage ✅

---

### Pipeline & Data Processing

| Command | Status | Priority | Notes |
|---------|--------|----------|-------|
| Where-Object | ❌ MISSING | **HIGH** | Filter objects (critical for pipeline) |
| Sort-Object | ❌ MISSING | **HIGH** | Sort objects |
| Select-Object | ❌ MISSING | **HIGH** | Select properties |
| ForEach-Object | ❌ MISSING | **MEDIUM** | Loop through objects |
| Group-Object | ❌ MISSING | LOW | Group objects |
| Measure-Object | ❌ MISSING | LOW | Count/sum/average |
| Format-Table | ❌ MISSING | LOW | Format output |
| Format-List | ❌ MISSING | LOW | Format output |

**Gap Summary:** Missing ALL pipeline cmdlets - this is a **CRITICAL GAP** for PowerShell workflows

---

### Archives & Compression

| Command | Status | Priority | Notes |
|---------|--------|----------|-------|
| Compress-Archive | ❌ MISSING | **MEDIUM** | Create ZIP files |
| Expand-Archive | ❌ MISSING | **MEDIUM** | Extract ZIP files |

**Gap Summary:** Missing both archive operations

---

### Remoting

| Command | Status | Priority | Notes |
|---------|--------|----------|-------|
| Invoke-Command | ✅ EXISTS | - | Remote execution |
| Enter-PSSession | ❌ MISSING | LOW | Interactive remote session |
| New-PSSession | ❌ MISSING | LOW | Create session |

**Gap Summary:** Basic remoting covered with Invoke-Command

---

### Scheduled Tasks

| Command | Status | Priority | Notes |
|---------|--------|----------|-------|
| Get-ScheduledTask | ✅ EXISTS | - | List tasks |
| Register-ScheduledTask | ✅ EXISTS | - | Create tasks |
| schtasks | ✅ EXISTS | - | Legacy task scheduler |

**Gap Summary:** Complete coverage ✅

---

### Security & Permissions

| Command | Status | Priority | Notes |
|---------|--------|----------|-------|
| Get-Acl | ✅ EXISTS | - | Get permissions |
| Set-Acl | ❌ MISSING | **MEDIUM** | Set permissions |
| Get-ExecutionPolicy | ❌ MISSING | LOW | Check execution policy |
| Set-ExecutionPolicy | ❌ MISSING | LOW | Set execution policy |

**Gap Summary:** Missing Set-Acl (needed to modify permissions)

---

### Environment & Variables

| Command | Status | Priority | Notes |
|---------|--------|----------|-------|
| Get-Variable | ❌ MISSING | LOW | List variables |
| Set-Variable | ❌ MISSING | LOW | Set variables |
| Get-ChildItem Env: | ❌ MISSING | **MEDIUM** | List environment variables |

**Gap Summary:** Missing environment variable management

---

### CMD (Command Prompt) Tools

| Command | Status | Priority | Notes |
|---------|--------|----------|-------|
| ipconfig | ❌ MISSING | **HIGH** | Network configuration |
| ping | ❌ MISSING | **HIGH** | Network connectivity test |
| tracert | ❌ MISSING | **MEDIUM** | Trace route |
| nslookup | ❌ MISSING | **HIGH** | DNS lookup (use Resolve-DnsName) |
| netstat | ❌ MISSING | **HIGH** | Network statistics |
| tasklist | ❌ MISSING | **MEDIUM** | List processes (use Get-Process) |
| taskkill | ❌ MISSING | **MEDIUM** | Kill process (use Stop-Process) |
| sc | ❌ MISSING | **MEDIUM** | Service control |
| systeminfo | ❌ MISSING | **MEDIUM** | System info (use Get-ComputerInfo) |
| whoami | ❌ MISSING | **MEDIUM** | Current user info |
| net | ❌ MISSING | LOW | Network commands |
| reg | ❌ MISSING | LOW | Registry (covered by manager) |
| robocopy | ❌ MISSING | **MEDIUM** | Robust file copy |
| findstr | ❌ MISSING | **MEDIUM** | Search text (use Select-String) |
| sfc | ❌ MISSING | LOW | System file checker |
| dism | ❌ MISSING | LOW | Deployment image servicing |

**Gap Summary:** Missing 16 CMD tools, but many have PowerShell equivalents already in catalog

---

## 🎯 PRIORITY RECOMMENDATIONS

### **TIER 1 - CRITICAL (Must Add ASAP)**

These are fundamental operations that users will expect:

1. **Set-Content** - Write/overwrite file content
2. **Add-Content** - Append to files
3. **Where-Object** - Filter pipeline objects
4. **Sort-Object** - Sort pipeline objects
5. **Select-Object** - Select object properties
6. **Resolve-DnsName** - DNS lookups
7. **ipconfig** - Network configuration (or use Get-NetIPConfiguration)
8. **ping** - Basic connectivity test
9. **netstat** - Network connections (or use Get-NetTCPConnection)

**Rationale:** These are used in almost every PowerShell workflow. Without Where-Object, Sort-Object, and Select-Object, users cannot effectively use the PowerShell pipeline.

---

### **TIER 2 - HIGH PRIORITY (Add Soon)**

Important for common administrative tasks:

10. **Get-NetTCPConnection** - Active network connections
11. **Invoke-RestMethod** - REST API calls
12. **Start-Process** - Launch applications
13. **Compress-Archive** - Create ZIP files
14. **Expand-Archive** - Extract ZIP files
15. **Set-Service** - Configure service properties
16. **Set-Acl** - Modify permissions
17. **Get-CimInstance** - Modern WMI queries
18. **robocopy** - Robust file copy for large operations

---

### **TIER 3 - MEDIUM PRIORITY (Nice to Have)**

Useful but less frequently needed:

19. **ForEach-Object** - Loop through pipeline
20. **tracert** - Trace network route
21. **whoami** - Current user information
22. **Get-ChildItem Env:** - Environment variables
23. **nslookup** - DNS lookup (legacy, prefer Resolve-DnsName)
24. **tasklist** - List processes (legacy, prefer Get-Process)
25. **taskkill** - Kill process (legacy, prefer Stop-Process)
26. **systeminfo** - System info (legacy, prefer Get-ComputerInfo)
27. **sc** - Service control (legacy, prefer *-Service cmdlets)

---

### **TIER 4 - LOW PRIORITY (Future Enhancement)**

Specialized or covered by existing managers:

- Format-Table, Format-List (output formatting)
- Group-Object, Measure-Object (data aggregation)
- Get-ExecutionPolicy, Set-ExecutionPolicy
- Enter-PSSession, New-PSSession
- Get-WindowsFeature
- New-NetFirewallRule (covered by firewall manager)
- reg, net (covered by registry/network managers)
- sfc, dism (system maintenance)

---

## 📈 STATISTICS

- **Total Commands in Cheat Sheet:** ~80 unique commands
- **Currently in Catalog:** 63 tools (including 11 just added)
- **Missing Commands:** ~35 commands
- **Critical Gaps (Tier 1):** 9 commands
- **High Priority (Tier 2):** 9 commands
- **Medium Priority (Tier 3):** 9 commands
- **Low Priority (Tier 4):** ~8 commands

---

## 🔍 KEY INSIGHTS

### 1. **Pipeline Cmdlets Are Missing**
The most critical gap is the absence of Where-Object, Sort-Object, and Select-Object. These are **fundamental to PowerShell** and are used in virtually every non-trivial command. Without them, users cannot:
- Filter results: `Get-Process | Where-Object CPU -gt 100`
- Sort data: `Get-Service | Sort-Object Status`
- Select specific properties: `Get-ChildItem | Select-Object Name, Length`

### 2. **File Writing Operations Missing**
We added Get-Content (read) but not Set-Content (write) or Add-Content (append). This is like having a read-only filesystem.

### 3. **CMD vs PowerShell Overlap**
Many CMD commands (tasklist, taskkill, systeminfo) have PowerShell equivalents already in the catalog. We should:
- Prioritize PowerShell cmdlets
- Add CMD commands only if they offer unique functionality (like robocopy, ipconfig, ping)

### 4. **Network Diagnostics Gap**
Basic network troubleshooting tools (ping, tracert, nslookup/Resolve-DnsName, netstat/Get-NetTCPConnection) are partially missing.

### 5. **Archive Operations Missing**
No ZIP file support (Compress-Archive, Expand-Archive) - common need for log collection, backups, etc.

---

## 🎬 NEXT STEPS

### Immediate Action (This Week)
1. Add Tier 1 critical tools (9 tools)
2. Test pipeline cmdlets integration
3. Verify file writing operations

### Short Term (This Month)
1. Add Tier 2 high priority tools (9 tools)
2. Add archive operations
3. Complete network diagnostics suite

### Medium Term (Next Quarter)
1. Add Tier 3 medium priority tools
2. Consider Tier 4 based on user feedback
3. Implement automated coverage testing

---

## 📝 LESSONS LEARNED

1. **Start with fundamentals:** Pipeline cmdlets should have been in from day one
2. **Think in workflows:** Users don't just read files, they write them too
3. **CMD vs PowerShell:** Need both - CMD for quick diagnostics, PowerShell for automation
4. **Cheat sheets are gold:** Real-world usage patterns reveal gaps better than feature lists

---

## 🔗 RELATED DOCUMENTS

- [MISSING_BASIC_WINDOWS_TOOLS.md](./MISSING_BASIC_WINDOWS_TOOLS.md) - Original gap analysis
- [Windows CLI + PowerShell Cheat Sheet](../tmp/zencoder/pasted/text/20251016020653-zfh4a1.txt) - Source reference

---

**Last Updated:** 2025-01-16  
**Next Review:** After Tier 1 tools are added