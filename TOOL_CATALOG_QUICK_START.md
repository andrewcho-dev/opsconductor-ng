# Tool Catalog System - Quick Start Guide
## Adding 200+ Tools to OpsConductor

---

## 🎯 What You Get

A **database-backed tool catalog system** that allows you to:

✅ **Manage 200+ tools** across Linux, Windows, Network, Scheduler, and Custom platforms  
✅ **Update tools dynamically** without system restart  
✅ **Track performance** with real-time telemetry  
✅ **Version tools** with rollback capability  
✅ **A/B test** tool optimizations  
✅ **Admin UI** for easy management  
✅ **REST API** for automation  

---

## 📊 Current Status

### ✅ **Completed**
- Database schema designed (`database/tool-catalog-schema.sql`)
- Implementation plan documented (`TOOL_CATALOG_IMPLEMENTATION_PLAN.md`)
- Tool template created (`pipeline/config/tools/templates/tool_template.yaml`)
- Example tools created (grep, powershell)

### 🚧 **Next Steps**
1. Create database schema
2. Build ToolCatalogService
3. Create migration script (YAML → Database)
4. Update HybridOrchestrator to use database
5. Build REST API
6. Create Admin UI

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────┐
│                  Tool Catalog System                     │
├─────────────────────────────────────────────────────────┤
│                                                          │
│  YAML Files (Bootstrap)                                 │
│       ↓                                                  │
│  PostgreSQL Database (Runtime)                          │
│       ↓                                                  │
│  ToolCatalogService (Business Logic)                    │
│       ↓                                                  │
│  HybridOrchestrator (Tool Selection)                    │
│       ↓                                                  │
│  TelemetryService (Performance Tracking)                │
│                                                          │
└─────────────────────────────────────────────────────────┘
```

---

## 📁 Database Schema

### **7 Tables**

1. **`tools`** - Main tool registry (200+ tools)
2. **`tool_capabilities`** - What each tool can do
3. **`tool_patterns`** - How to use each capability (with performance profiles)
4. **`tool_telemetry`** - Actual performance data
5. **`tool_ab_tests`** - A/B testing for optimization
6. **`tool_audit_log`** - Change tracking
7. **`tool_cache`** - Performance cache

### **Key Features**

- **Versioning**: Multiple versions of same tool
- **JSONB fields**: Flexible metadata storage
- **Indexes**: Fast lookups by name, platform, category, capability
- **Triggers**: Auto-update timestamps
- **Views**: Convenient data access
- **Functions**: Helper functions for common operations

---

## 🚀 How to Add Tools

### **Option 1: Use Template (Recommended for new tools)**

```bash
# 1. Copy template
cp pipeline/config/tools/templates/tool_template.yaml \
   pipeline/config/tools/linux/my_new_tool.yaml

# 2. Edit the file (replace all <PLACEHOLDER> values)

# 3. Validate
python scripts/validate_tool.py pipeline/config/tools/linux/my_new_tool.yaml

# 4. Import to database
python scripts/migrate_tools_to_db.py --file pipeline/config/tools/linux/my_new_tool.yaml
```

### **Option 2: Use Generator (Interactive)**

```bash
python scripts/generate_tool_definition.py

# Follow prompts:
# - Tool name: curl
# - Platform: linux
# - Category: network
# - Description: Transfer data with URLs
# ... etc
```

### **Option 3: Use API (Programmatic)**

```bash
curl -X POST http://localhost:8080/api/v1/tools \
  -H "Content-Type: application/json" \
  -d '{
    "tool_name": "curl",
    "version": "1.0",
    "description": "Transfer data with URLs",
    "platform": "linux",
    "category": "network",
    "capabilities": [...]
  }'
```

### **Option 4: Use Admin UI (Visual)**

```
1. Navigate to: http://localhost:8080/admin/tool-catalog
2. Click "Add Tool"
3. Fill in form
4. Click "Save"
```

---

## 📋 Tool Categories & Counts

Here's how to organize your 200+ tools:

### **Linux Commands (~60 tools)**
```
/pipeline/config/tools/linux/
├── systemctl.yaml       # Service control
├── ps.yaml              # Process monitoring
├── journalctl.yaml      # Log access
├── grep.yaml            # Text search
├── awk.yaml             # Text processing
├── sed.yaml             # Stream editor
├── find.yaml            # File search
├── tar.yaml             # Archive management
├── rsync.yaml           # File sync
├── ssh.yaml             # Remote access
├── scp.yaml             # Secure copy
├── curl.yaml            # HTTP client
├── wget.yaml            # Download utility
├── netstat.yaml         # Network statistics
├── iptables.yaml        # Firewall
├── top.yaml             # Process viewer
├── htop.yaml            # Interactive process viewer
├── df.yaml              # Disk usage
├── du.yaml              # Directory usage
├── free.yaml            # Memory usage
└── ... (40 more)
```

### **Windows Commands (~50 tools)**
```
/pipeline/config/tools/windows/
├── powershell.yaml      # PowerShell execution
├── sc.yaml              # Service control
├── net.yaml             # Network commands
├── wmic.yaml            # WMI command-line
├── tasklist.yaml        # Process list
├── taskkill.yaml        # Kill process
├── reg.yaml             # Registry editor
├── netsh.yaml           # Network shell
├── ipconfig.yaml        # IP configuration
├── ping.yaml            # Network test
├── tracert.yaml         # Trace route
├── nslookup.yaml        # DNS lookup
├── robocopy.yaml        # Robust file copy
├── xcopy.yaml           # Extended copy
└── ... (36 more)
```

### **Network Tools (~40 tools)**
```
/pipeline/config/tools/network/
├── network-analyzer.yaml    # Your custom analyzer
├── tcpdump.yaml             # Packet capture
├── wireshark.yaml           # Protocol analyzer
├── nmap.yaml                # Network scanner
├── netcat.yaml              # Network utility
├── telnet.yaml              # Remote access
├── ftp.yaml                 # File transfer
├── sftp.yaml                # Secure FTP
├── dig.yaml                 # DNS lookup
├── host.yaml                # DNS lookup
├── whois.yaml               # Domain info
├── mtr.yaml                 # Network diagnostic
├── iperf.yaml               # Bandwidth test
├── ethtool.yaml             # Ethernet settings
└── ... (26 more)
```

### **Scheduler Tools (~20 tools)**
```
/pipeline/config/tools/scheduler/
├── task-scheduler.yaml      # Your custom scheduler
├── cron.yaml                # Unix scheduler
├── at.yaml                  # One-time scheduler
├── systemd-timer.yaml       # Systemd timers
├── windows-task-scheduler.yaml  # Windows scheduler
├── jenkins.yaml             # CI/CD scheduler
├── airflow.yaml             # Workflow scheduler
└── ... (13 more)
```

### **Custom/API Tools (~30 tools)**
```
/pipeline/config/tools/custom/
├── asset-service-query.yaml     # Your asset service
├── asset-direct-poll.yaml       # Direct polling
├── api-gateway.yaml             # API gateway
├── data-processor.yaml          # Data processing
├── notification-service.yaml    # Notifications
├── backup-service.yaml          # Backups
├── monitoring-service.yaml      # Monitoring
└── ... (23 more)
```

---

## 🎯 Implementation Phases

### **Phase 1: Foundation (Weeks 1-2)** ⬅️ **START HERE**

**Goal**: Get database working with basic CRUD operations

**Tasks**:
1. ✅ Create database schema
2. ⬜ Create ToolCatalogService (Python)
3. ⬜ Create migration script (YAML → DB)
4. ⬜ Import existing tools (systemctl, ps, journalctl, etc.)
5. ⬜ Update HybridOrchestrator to read from DB
6. ⬜ Write unit tests

**Deliverables**:
- Database schema created
- 10-20 tools imported
- HybridOrchestrator using database
- All existing tests passing

---

### **Phase 2: API & Tooling (Weeks 3-4)**

**Goal**: Enable dynamic tool management

**Tasks**:
1. ⬜ Create REST API for tool CRUD
2. ⬜ Create tool generator script
3. ⬜ Create bulk import/export tools
4. ⬜ Add hot reload mechanism
5. ⬜ Write API tests

**Deliverables**:
- REST API operational
- Tool generator working
- 50-100 tools imported
- Documentation complete

---

### **Phase 3: Telemetry (Weeks 5-6)**

**Goal**: Track and optimize tool performance

**Tasks**:
1. ⬜ Create TelemetryService
2. ⬜ Integrate with HybridOrchestrator
3. ⬜ Create performance analysis tools
4. ⬜ Build A/B testing framework
5. ⬜ Create dashboards

**Deliverables**:
- Telemetry collection working
- Performance dashboards
- A/B testing framework
- 100-150 tools imported

---

### **Phase 4: Admin UI (Weeks 7-8)**

**Goal**: Make tool management accessible to non-developers

**Tasks**:
1. ⬜ Create admin UI
2. ⬜ Visual tool editor
3. ⬜ Performance dashboards
4. ⬜ A/B test management
5. ⬜ User documentation

**Deliverables**:
- Admin UI operational
- All 200+ tools imported
- Complete documentation
- Training materials

---

## 🔧 Tool Definition Example

Here's a complete example for the `curl` command:

```yaml
tool_name: "curl"
version: "1.0"
description: "Transfer data with URLs (HTTP, HTTPS, FTP, etc.)"
platform: "linux"
category: "network"

defaults:
  accuracy_level: "real-time"
  freshness: "live"
  data_source: "network"

capabilities:
  http_request:
    description: "Make HTTP/HTTPS requests"
    
    patterns:
      get_request:
        description: "Perform HTTP GET request"
        
        typical_use_cases:
          - "download file"
          - "test api"
          - "check endpoint"
          - "fetch data"
        
        time_estimate_ms: "1000 + response_size_kb * 10"
        cost_estimate: 1
        complexity_score: 0.2
        
        scope: "single_request"
        completeness: "complete"
        
        limitations:
          - "Requires network access"
          - "May timeout on slow connections"
        
        policy:
          max_cost: 5
          requires_approval: false
          production_safe: true
          max_execution_time: 30
        
        preference_match:
          speed: 0.8
          accuracy: 1.0
          cost: 0.9
          complexity: 0.9
          completeness: 1.0
        
        required_inputs:
          - name: "url"
            type: "string"
            description: "Target URL"
            validation: "^https?://.*"
        
        optional_inputs:
          - name: "method"
            type: "string"
            description: "HTTP method"
            default: "GET"
          - name: "headers"
            type: "object"
            description: "HTTP headers"
            default: {}
          - name: "timeout"
            type: "integer"
            description: "Request timeout in seconds"
            default: "30"

dependencies:
  - name: "network_access"
    type: "network"
    required: true

metadata:
  author: "OpsConductor Team"
  created: "2025-01-01"
  tags:
    - "http"
    - "network"
    - "download"
  documentation_url: "https://curl.se/docs/"

examples:
  - name: "Download file"
    description: "Download a file from URL"
    inputs:
      url: "https://example.com/file.txt"
      method: "GET"
    expected_time_ms: 1500
    expected_cost: 1
```

---

## 📊 Success Metrics

### **Performance**
- Tool lookup: < 10ms (with caching)
- Tool update propagation: < 1 second
- API response time: < 100ms (p95)
- Support 200+ tools without degradation

### **Reliability**
- 99.9% uptime for tool catalog service
- Zero data loss during updates
- Automatic rollback on validation failure
- Complete audit trail

### **Usability**
- Add new tool: < 5 minutes (via UI)
- Bulk import 100 tools: < 1 minute
- Real-time validation feedback
- Self-service tool management

---

## 🔒 Security

- **Access Control**: Role-based (RBAC)
- **Validation**: Schema + expression sandboxing
- **Audit**: Complete change tracking
- **Encryption**: TLS + data at rest
- **Rate Limiting**: API protection

---

## 📝 Next Actions

### **Immediate (This Week)**

1. **Review and approve** the implementation plan
2. **Create database schema**:
   ```bash
   psql -U opsconductor -d opsconductor -f database/tool-catalog-schema.sql
   ```
3. **Prioritize tool categories** - which to add first?
4. **Assign resources** - who will work on this?

### **Short-term (Next 2 Weeks)**

1. Build ToolCatalogService
2. Create migration script
3. Import first 20 tools
4. Update HybridOrchestrator
5. Run tests

### **Medium-term (Next 4-6 Weeks)**

1. Build REST API
2. Create tool generator
3. Import 100+ tools
4. Add telemetry
5. Build dashboards

### **Long-term (Next 8 Weeks)**

1. Build Admin UI
2. Complete all 200+ tools
3. Enable A/B testing
4. Production deployment
5. User training

---

## ❓ Questions to Answer

Before starting Phase 1, please clarify:

### **1. Tool Priority**
Which categories should we populate first?
- [ ] Linux commands (most common: systemctl, ps, grep, etc.)
- [ ] Windows commands (PowerShell, sc, net, etc.)
- [ ] Network tools (your analyzer, tcpdump, nmap, etc.)
- [ ] Scheduler tools (your scheduler, cron, etc.)
- [ ] Custom APIs (your internal services)

### **2. Tool Sources**
Where will tool definitions come from?
- [ ] Manual creation (using templates)
- [ ] Bulk import from documentation
- [ ] Auto-discovery from systems
- [ ] Third-party catalogs

### **3. Team Resources**
Who will work on this?
- Backend developer (ToolCatalogService, API)
- Database admin (schema, optimization)
- Frontend developer (Admin UI)
- DevOps (deployment, monitoring)
- Tool experts (define 200+ tools)

### **4. Timeline**
What's the target completion date?
- [ ] 4 weeks (basic functionality)
- [ ] 8 weeks (full implementation)
- [ ] 12 weeks (with UI and all tools)

---

## 📚 Documentation

- **Full Plan**: `TOOL_CATALOG_IMPLEMENTATION_PLAN.md`
- **Database Schema**: `database/tool-catalog-schema.sql`
- **Tool Template**: `pipeline/config/tools/templates/tool_template.yaml`
- **Example Tools**: `pipeline/config/tools/linux/grep.yaml`, `pipeline/config/tools/windows/powershell.yaml`

---

## 🎉 Benefits

Once complete, you'll have:

✅ **200+ tools** ready to use  
✅ **Dynamic updates** without restart  
✅ **Performance tracking** with telemetry  
✅ **Optimization** via A/B testing  
✅ **Easy management** via Admin UI  
✅ **Automation** via REST API  
✅ **Scalability** to 1000+ tools  
✅ **Observability** with full audit trail  

---

**Ready to start?** Let me know which phase to begin with!