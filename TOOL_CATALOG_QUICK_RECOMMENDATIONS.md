# Tool Catalog Quick Recommendations
**Immediate Action Items for Tool Catalog Expansion**

**Date**: 2025-01-28  
**Current Tools**: 5  
**Recommended Next**: 30 tools (Phase 1)

---

## 🎯 Executive Summary

You currently have **5 tools** loaded in your Tool Catalog, but your existing services already have the capability to execute **90+ tools**. This document provides immediate recommendations for the next 30 tools to add.

### Current State
- ✅ **automation-service**: Can execute SSH (Linux) and WinRM (Windows) commands
- ✅ **network-analyzer-service**: Can capture packets and analyze protocols (tcpdump, tshark, scapy)
- ✅ **asset-service**: Can query asset inventory
- ✅ **communication-service**: Can send notifications

### Gap
Your services can execute these tools, but they're **not registered in the Tool Catalog**, so Stage B (Selector) doesn't know they exist!

---

## 🚀 Phase 1: Critical Foundation (30 Tools)

### Priority 1: Windows System Tools (10 tools)
**Why**: You have 1 Windows tool (powershell) but automation-service can execute any PowerShell cmdlet

| Tool | Command | Use Case | Priority |
|------|---------|----------|----------|
| **Get-Service** | `Get-Service -Name <name>` | Query Windows service status | 🔴 CRITICAL |
| **Get-Process** | `Get-Process -Name <name>` | List Windows processes | 🔴 CRITICAL |
| **Get-EventLog** | `Get-EventLog -LogName System -Newest 100` | Query Windows Event Logs | 🔴 CRITICAL |
| **Get-ComputerInfo** | `Get-ComputerInfo` | Get system information | 🟡 HIGH |
| **Get-NetAdapter** | `Get-NetAdapter` | Query network adapters | 🟡 HIGH |
| **Get-NetIPAddress** | `Get-NetIPAddress` | Query IP configuration | 🟡 HIGH |
| **Test-NetConnection** | `Test-NetConnection -ComputerName <host> -Port <port>` | Test network connectivity | 🔴 CRITICAL |
| **Get-Counter** | `Get-Counter -Counter "\Processor(_Total)\% Processor Time"` | Query performance counters | 🟡 HIGH |
| **Get-HotFix** | `Get-HotFix` | List installed Windows updates | 🟢 MEDIUM |
| **Invoke-Command** | `Invoke-Command -ComputerName <host> -ScriptBlock {...}` | Execute remote commands | 🔴 CRITICAL |

**Implementation**: Create YAML files in `/pipeline/config/tools/windows/`

---

### Priority 2: Linux System Tools (10 tools)
**Why**: You have 2 Linux tools (grep, htop) but automation-service can execute any bash command

| Tool | Command | Use Case | Priority |
|------|---------|----------|----------|
| **ps** | `ps aux` | List processes | 🔴 CRITICAL |
| **df** | `df -h` | Check disk space | 🔴 CRITICAL |
| **free** | `free -h` | Check memory usage | 🔴 CRITICAL |
| **systemctl** | `systemctl status <service>` | Manage systemd services | 🔴 CRITICAL |
| **journalctl** | `journalctl -u <service> -n 100` | Query systemd logs | 🔴 CRITICAL |
| **netstat** | `netstat -tulpn` | List network connections | 🟡 HIGH |
| **ss** | `ss -tulpn` | List sockets (modern netstat) | 🟡 HIGH |
| **curl** | `curl -X GET <url>` | Make HTTP requests | 🔴 CRITICAL |
| **ping** | `ping -c 4 <host>` | Test connectivity | 🔴 CRITICAL |
| **dig** | `dig <domain>` | DNS lookup | 🟡 HIGH |

**Implementation**: Create YAML files in `/pipeline/config/tools/linux/`

---

### Priority 3: Network Analyzer Tools (10 tools)
**Why**: network-analyzer-service already has these capabilities but they're not in the catalog

| Tool | Service Integration | Use Case | Priority |
|------|---------------------|----------|----------|
| **tcpdump** | ✅ PacketAnalyzer | Capture network packets | 🔴 CRITICAL |
| **tshark** | ✅ PacketAnalyzer | Terminal Wireshark | 🔴 CRITICAL |
| **http-analyzer** | ✅ ProtocolAnalyzer | Analyze HTTP traffic | 🔴 CRITICAL |
| **dns-analyzer** | ✅ ProtocolAnalyzer | Analyze DNS traffic | 🔴 CRITICAL |
| **tcp-analyzer** | ✅ ProtocolAnalyzer | Analyze TCP connections | 🟡 HIGH |
| **udp-analyzer** | ✅ ProtocolAnalyzer | Analyze UDP traffic | 🟡 HIGH |
| **ssh-analyzer** | ✅ ProtocolAnalyzer | Analyze SSH connections | 🟢 MEDIUM |
| **tls-analyzer** | ✅ ProtocolAnalyzer | Analyze TLS/SSL | 🟡 HIGH |
| **nmap** | 🔴 Not Implemented | Port scanning | 🟡 HIGH |
| **scapy** | ✅ PacketAnalyzer | Python packet manipulation | 🟢 MEDIUM |

**Implementation**: Create YAML files in `/pipeline/config/tools/network/`

---

## 📋 Quick Start: Add Your First 5 Tools

### Step 1: Create Tool Definitions

#### Tool 1: Get-Service (Windows)
```bash
cd /home/opsconductor/opsconductor-ng
python scripts/tool_from_template.py \
  --name "Get-Service" \
  --platform windows \
  --category system \
  --description "Query Windows service status"
```

#### Tool 2: ps (Linux)
```bash
python scripts/tool_from_template.py \
  --name "ps" \
  --platform linux \
  --category system \
  --description "List running processes"
```

#### Tool 3: systemctl (Linux)
```bash
python scripts/tool_from_template.py \
  --name "systemctl" \
  --platform linux \
  --category automation \
  --description "Manage systemd services"
```

#### Tool 4: tcpdump (Network)
```bash
python scripts/tool_from_template.py \
  --name "tcpdump" \
  --platform network \
  --category network \
  --description "Capture network packets"
```

#### Tool 5: curl (Multi-platform)
```bash
python scripts/tool_from_template.py \
  --name "curl" \
  --platform multi-platform \
  --category network \
  --description "Transfer data with URLs"
```

### Step 2: Customize Tool Definitions

Edit the generated YAML files to add:
1. **Capabilities**: What the tool can do
2. **Patterns**: Different usage patterns
3. **Performance Estimates**: Time, cost, complexity
4. **Preference Matching**: Speed, accuracy, cost scores

### Step 3: Migrate to Database

```bash
# Migrate individual tools
python scripts/migrate_tools_to_db.py --tool pipeline/config/tools/windows/get-service.yaml

# Or migrate all at once
python scripts/migrate_tools_to_db.py --directory pipeline/config/tools/windows/
python scripts/migrate_tools_to_db.py --directory pipeline/config/tools/linux/
python scripts/migrate_tools_to_db.py --directory pipeline/config/tools/network/
```

### Step 4: Verify Integration

```bash
# Check tool count
curl http://localhost:3005/api/v1/tools/health

# List all tools
curl http://localhost:3005/api/v1/tools | jq

# Test ProfileLoader
docker exec opsconductor-ai-pipeline python -c "
from pipeline.stages.stage_b.profile_loader import ProfileLoader
loader = ProfileLoader(use_database=True)
profiles = loader.load()
print(f'Loaded {len(profiles.tools)} tools')
"
```

---

## 🔧 Service Integration Mapping

### Automation Service → Tool Catalog

**Current**: automation-service can execute commands but tools aren't registered

**Solution**: Register these tools in the catalog

| Service Capability | Tools to Register | Count |
|-------------------|-------------------|-------|
| LinuxSSHLibrary | All Linux CLI tools | 30+ |
| WindowsPowerShellLibrary | All PowerShell cmdlets | 30+ |
| NetworkAnalyzerLibrary | Protocol analyzers | 10+ |

**Example**: When user asks "check if nginx is running on server1"
- ❌ **Before**: Stage B doesn't know `systemctl` exists → Falls back to generic SSH
- ✅ **After**: Stage B finds `systemctl status` tool → Optimized execution

---

### Network Analyzer Service → Tool Catalog

**Current**: network-analyzer-service has PacketAnalyzer, ProtocolAnalyzer but tools aren't registered

**Solution**: Register these tools in the catalog

| Service Component | Tools to Register | Count |
|------------------|-------------------|-------|
| PacketAnalyzer | tcpdump, tshark, scapy, pyshark | 4 |
| ProtocolAnalyzer | http, dns, tcp, udp, ssh, ftp, smtp, snmp, icmp, tls | 10 |
| NetworkMonitor | Network monitoring tools | 5 |

**Example**: When user asks "analyze HTTP traffic on eth0"
- ❌ **Before**: Stage B doesn't know `http-analyzer` exists → Generic approach
- ✅ **After**: Stage B finds `http-analyzer` tool → Direct protocol analysis

---

### Asset Service → Tool Catalog

**Current**: asset-service has REST API but tools aren't registered

**Solution**: Register these tools in the catalog

| Service Endpoint | Tools to Register | Count |
|-----------------|-------------------|-------|
| GET /api/v1/assets | asset-query, asset-list, asset-count | 3 |
| GET /api/v1/assets/{id} | asset-get, asset-details | 2 |
| POST /api/v1/assets | asset-create, asset-register | 2 |
| PUT /api/v1/assets/{id} | asset-update, asset-modify | 2 |
| DELETE /api/v1/assets/{id} | asset-delete, asset-remove | 2 |

**Example**: When user asks "how many Linux servers do we have?"
- ❌ **Before**: Stage B doesn't know asset-service exists → Can't answer
- ✅ **After**: Stage B finds `asset-count` tool → Fast database query

---

## 📊 Expected Impact

### Before Tool Expansion (Current State)
- **Tool Count**: 5 tools
- **Coverage**: 10% of operational needs
- **Stage B Selection**: Limited options, often falls back to generic approaches
- **User Experience**: Many queries can't be optimized

### After Phase 1 (30 Tools)
- **Tool Count**: 35 tools (5 + 30)
- **Coverage**: 60% of operational needs
- **Stage B Selection**: Rich tool selection, optimized execution paths
- **User Experience**: Most common queries optimized

### After Full Expansion (150+ Tools)
- **Tool Count**: 150+ tools
- **Coverage**: 95% of operational needs
- **Stage B Selection**: Comprehensive tool selection
- **User Experience**: Nearly all queries optimized

---

## 🎯 Recommended Approach

### Week 1: Windows Tools (10 tools)
**Focus**: Enable Windows operations
- Day 1-2: Create 10 Windows tool definitions
- Day 3-4: Test with automation-service
- Day 5: Migrate to database and validate

### Week 2: Linux Tools (10 tools)
**Focus**: Enable Linux operations
- Day 1-2: Create 10 Linux tool definitions
- Day 3-4: Test with automation-service
- Day 5: Migrate to database and validate

### Week 3: Network Tools (10 tools)
**Focus**: Enable network analysis
- Day 1-2: Create 10 network tool definitions
- Day 3-4: Test with network-analyzer-service
- Day 5: Migrate to database and validate

---

## 🔍 Tool Definition Example

Here's a complete example for `systemctl`:

```yaml
tool_name: "systemctl"
version: "1.0"
description: "Control systemd services on Linux systems"
platform: "linux"
category: "automation"

defaults:
  timeout: 30
  retry_count: 3
  
dependencies:
  - package: "systemd"
    version: ">=230"

capabilities:
  service_control:
    patterns:
      check_status:
        description: "Check service status"
        typical_use_cases:
          - "is nginx running"
          - "check apache status"
          - "status of mysql"
        
        time_estimate_ms: 500
        cost_estimate: 1
        complexity_score: 0.1
        
        scope: "single_service"
        completeness: "complete"
        
        limitations:
          - "Requires systemd (not available on SysV init systems)"
          - "Requires appropriate permissions"
        
        policy:
          max_cost: 5
          requires_approval: false
          production_safe: true
        
        preference_match:
          speed: 0.95
          accuracy: 1.0
          cost: 0.95
          complexity: 0.95
          completeness: 1.0
      
      restart_service:
        description: "Restart a service"
        typical_use_cases:
          - "restart nginx"
          - "reload apache"
          - "restart mysql"
        
        time_estimate_ms: 2000
        cost_estimate: 1
        complexity_score: 0.3
        
        scope: "single_service"
        completeness: "complete"
        
        limitations:
          - "Requires root/sudo permissions"
          - "May cause service downtime"
        
        policy:
          max_cost: 5
          requires_approval: true
          production_safe: true
        
        preference_match:
          speed: 0.8
          accuracy: 1.0
          cost: 0.9
          complexity: 0.7
          completeness: 1.0
      
      enable_service:
        description: "Enable service to start on boot"
        typical_use_cases:
          - "enable nginx on boot"
          - "auto-start apache"
        
        time_estimate_ms: 1000
        cost_estimate: 1
        complexity_score: 0.2
        
        scope: "single_service"
        completeness: "complete"
        
        limitations:
          - "Requires root/sudo permissions"
        
        policy:
          max_cost: 5
          requires_approval: true
          production_safe: true
        
        preference_match:
          speed: 0.9
          accuracy: 1.0
          cost: 0.95
          complexity: 0.8
          completeness: 1.0
```

---

## 📚 Resources

### Documentation
- **Full Expansion Plan**: `TOOL_CATALOG_EXPANSION_PLAN.md` (214 tools planned)
- **Tool Template**: `pipeline/config/tools/templates/tool_template.yaml`
- **Migration Script**: `scripts/migrate_tools_to_db.py`
- **Tool Generator**: `scripts/tool_from_template.py`

### API Endpoints
- **Health Check**: `http://localhost:3005/api/v1/tools/health`
- **List Tools**: `http://localhost:3005/api/v1/tools`
- **Get Tool**: `http://localhost:3005/api/v1/tools/{id}`
- **Metrics**: `http://localhost:3005/api/v1/tools/metrics`

### Database
- **Schema**: `tool_catalog` (7 tables)
- **Connection**: `postgresql://opsconductor:***@postgres:5432/opsconductor`
- **Current Tools**: 5 (powershell, grep, htop, prometheus, github_api)

---

## ✅ Next Actions

1. **Review Recommendations**: Review the 30 tools recommended for Phase 1
2. **Prioritize**: Decide which 5-10 tools to add first
3. **Create Definitions**: Use `tool_from_template.py` to generate YAML files
4. **Customize**: Edit YAML files to add capabilities and patterns
5. **Test**: Test tool definitions with validation script
6. **Migrate**: Use `migrate_tools_to_db.py` to load into database
7. **Verify**: Check tool count and test ProfileLoader integration
8. **Iterate**: Repeat for next batch of tools

---

## 🎉 Quick Win

**Add these 5 tools in the next hour**:

1. ✅ **systemctl** (Linux) - Most requested Linux service management
2. ✅ **Get-Service** (Windows) - Most requested Windows service management
3. ✅ **ps** (Linux) - Most requested process listing
4. ✅ **curl** (Multi-platform) - Most requested HTTP client
5. ✅ **tcpdump** (Network) - Most requested packet capture

These 5 tools will immediately improve Stage B selection for the most common operational queries!

---

**Document Status**: ✅ Complete  
**Last Updated**: 2025-01-28  
**Next Review**: After first 5 tools added