# Tool Catalog System - Implementation Plan
## Database-Backed Dynamic Tool Management for 200+ Tools

---

## 🎯 Executive Summary

**Goal**: Implement a scalable, database-backed tool catalog system that can:
- Manage 200+ tools across multiple platforms (Linux, Windows, Network, Scheduler, Custom)
- Support dynamic tool updates without system restart
- Provide tool versioning, A/B testing, and rollback capabilities
- Enable telemetry-driven optimization
- Offer admin UI for tool management
- Maintain backward compatibility with existing YAML-based profiles

**Timeline**: 4 phases over 6-8 weeks

**Key Benefits**:
- ✅ Dynamic tool registration and updates
- ✅ Multi-tenant tool catalogs
- ✅ Performance telemetry integration
- ✅ Tool versioning and rollback
- ✅ A/B testing for tool optimization
- ✅ Admin UI for non-technical users
- ✅ API-first design for automation

---

## 📐 Architecture Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                     Tool Catalog System                          │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  ┌──────────────┐      ┌──────────────┐      ┌──────────────┐ │
│  │ YAML Files   │─────▶│  PostgreSQL  │◀─────│  Admin UI    │ │
│  │ (Bootstrap)  │      │  (Runtime)   │      │  (Management)│ │
│  └──────────────┘      └──────────────┘      └──────────────┘ │
│         │                      │                      │         │
│         │                      ▼                      │         │
│         │         ┌─────────────────────────┐        │         │
│         └────────▶│  ToolCatalogService     │◀───────┘         │
│                   │  - CRUD operations      │                  │
│                   │  - Versioning           │                  │
│                   │  - Validation           │                  │
│                   │  - Hot reload           │                  │
│                   │  - Telemetry tracking   │                  │
│                   └─────────────────────────┘                  │
│                              │                                  │
│                              ▼                                  │
│                   ┌─────────────────────────┐                  │
│                   │  HybridOrchestrator     │                  │
│                   │  (Tool Selection)       │                  │
│                   └─────────────────────────┘                  │
│                              │                                  │
│                              ▼                                  │
│                   ┌─────────────────────────┐                  │
│                   │  TelemetryService       │                  │
│                   │  (Performance Tracking) │                  │
│                   └─────────────────────────┘                  │
└─────────────────────────────────────────────────────────────────┘
```

---

## 🗄️ Database Schema

### **Schema: `tool_catalog`**

#### **1. `tools` - Main tool registry**
```sql
CREATE TABLE tool_catalog.tools (
    -- Identity
    id SERIAL PRIMARY KEY,
    tool_name VARCHAR(100) NOT NULL,
    version VARCHAR(20) NOT NULL,
    
    -- Basic Info
    description TEXT NOT NULL,
    platform VARCHAR(50) NOT NULL, -- linux, windows, network, scheduler, custom
    category VARCHAR(50) NOT NULL, -- system, network, automation, monitoring, security
    
    -- Status
    status VARCHAR(20) DEFAULT 'active', -- active, deprecated, disabled, testing
    enabled BOOLEAN DEFAULT true,
    
    -- Defaults (JSONB for flexibility)
    defaults JSONB NOT NULL DEFAULT '{}',
    -- Example: {"accuracy_level": "real-time", "freshness": "live", "data_source": "direct"}
    
    -- Dependencies
    dependencies JSONB DEFAULT '[]',
    -- Example: [{"name": "docker_daemon", "type": "service", "required": true}]
    
    -- Metadata
    metadata JSONB DEFAULT '{}',
    -- Example: {"author": "...", "tags": [...], "documentation_url": "..."}
    
    -- Versioning
    parent_version_id INTEGER REFERENCES tool_catalog.tools(id),
    is_latest BOOLEAN DEFAULT true,
    
    -- Tracking
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    created_by VARCHAR(100),
    updated_by VARCHAR(100),
    
    -- Constraints
    UNIQUE(tool_name, version)
);

CREATE INDEX idx_tools_name ON tool_catalog.tools(tool_name);
CREATE INDEX idx_tools_platform ON tool_catalog.tools(platform);
CREATE INDEX idx_tools_category ON tool_catalog.tools(category);
CREATE INDEX idx_tools_status ON tool_catalog.tools(status);
CREATE INDEX idx_tools_enabled ON tool_catalog.tools(enabled);
CREATE INDEX idx_tools_is_latest ON tool_catalog.tools(is_latest);
CREATE INDEX idx_tools_metadata ON tool_catalog.tools USING GIN (metadata);
```

#### **2. `tool_capabilities` - Tool capabilities**
```sql
CREATE TABLE tool_catalog.tool_capabilities (
    id SERIAL PRIMARY KEY,
    tool_id INTEGER NOT NULL REFERENCES tool_catalog.tools(id) ON DELETE CASCADE,
    
    -- Capability Info
    capability_name VARCHAR(100) NOT NULL,
    description TEXT NOT NULL,
    
    -- Tracking
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    
    UNIQUE(tool_id, capability_name)
);

CREATE INDEX idx_capabilities_tool_id ON tool_catalog.tool_capabilities(tool_id);
CREATE INDEX idx_capabilities_name ON tool_catalog.tool_capabilities(capability_name);
```

#### **3. `tool_patterns` - Usage patterns for capabilities**
```sql
CREATE TABLE tool_catalog.tool_patterns (
    id SERIAL PRIMARY KEY,
    capability_id INTEGER NOT NULL REFERENCES tool_catalog.tool_capabilities(id) ON DELETE CASCADE,
    
    -- Pattern Info
    pattern_name VARCHAR(100) NOT NULL,
    description TEXT NOT NULL,
    
    -- Use Cases
    typical_use_cases JSONB DEFAULT '[]',
    -- Example: ["restart service", "reload configuration"]
    
    -- Performance Metrics (expressions as strings)
    time_estimate_ms VARCHAR(500) NOT NULL, -- Expression: "2000 + 0.5 * N"
    cost_estimate VARCHAR(500) NOT NULL,    -- Expression: "ceil(N / 100)"
    complexity_score DECIMAL(3,2) NOT NULL CHECK (complexity_score >= 0 AND complexity_score <= 1),
    
    -- Quality Metrics
    scope VARCHAR(50) NOT NULL,
    completeness VARCHAR(50) NOT NULL,
    
    -- Limitations
    limitations JSONB DEFAULT '[]',
    
    -- Policy Constraints
    policy JSONB NOT NULL,
    -- Example: {"max_cost": 10, "requires_approval": true, "production_safe": true}
    
    -- Preference Matching
    preference_match JSONB NOT NULL,
    -- Example: {"speed": 0.9, "accuracy": 1.0, "cost": 0.8, "complexity": 0.7, "completeness": 1.0}
    
    -- Input/Output Schemas
    required_inputs JSONB DEFAULT '[]',
    optional_inputs JSONB DEFAULT '[]',
    output_schema JSONB DEFAULT '{}',
    
    -- Examples
    examples JSONB DEFAULT '[]',
    
    -- Tracking
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    
    UNIQUE(capability_id, pattern_name)
);

CREATE INDEX idx_patterns_capability_id ON tool_catalog.tool_patterns(capability_id);
CREATE INDEX idx_patterns_name ON tool_catalog.tool_patterns(pattern_name);
CREATE INDEX idx_patterns_use_cases ON tool_catalog.tool_patterns USING GIN (typical_use_cases);
```

#### **4. `tool_telemetry` - Performance tracking**
```sql
CREATE TABLE tool_catalog.tool_telemetry (
    id SERIAL PRIMARY KEY,
    
    -- Tool Reference
    tool_id INTEGER NOT NULL REFERENCES tool_catalog.tools(id),
    capability_id INTEGER REFERENCES tool_catalog.tool_capabilities(id),
    pattern_id INTEGER REFERENCES tool_catalog.tool_patterns(id),
    
    -- Execution Context
    execution_id VARCHAR(100), -- Link to execution record
    user_id VARCHAR(100),
    environment VARCHAR(50), -- production, staging, development
    
    -- Performance Metrics
    actual_time_ms INTEGER NOT NULL,
    actual_cost DECIMAL(10,2),
    success BOOLEAN NOT NULL,
    error_message TEXT,
    
    -- Context Variables (for analysis)
    context_variables JSONB DEFAULT '{}',
    -- Example: {"N": 100, "file_size_kb": 5000}
    
    -- Tracking
    executed_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_telemetry_tool_id ON tool_catalog.tool_telemetry(tool_id);
CREATE INDEX idx_telemetry_pattern_id ON tool_catalog.tool_telemetry(pattern_id);
CREATE INDEX idx_telemetry_executed_at ON tool_catalog.tool_telemetry(executed_at);
CREATE INDEX idx_telemetry_success ON tool_catalog.tool_telemetry(success);
CREATE INDEX idx_telemetry_environment ON tool_catalog.tool_telemetry(environment);
```

#### **5. `tool_ab_tests` - A/B testing for optimization**
```sql
CREATE TABLE tool_catalog.tool_ab_tests (
    id SERIAL PRIMARY KEY,
    
    -- Test Info
    test_name VARCHAR(100) NOT NULL UNIQUE,
    description TEXT,
    
    -- Tool Versions Being Tested
    tool_a_id INTEGER NOT NULL REFERENCES tool_catalog.tools(id),
    tool_b_id INTEGER NOT NULL REFERENCES tool_catalog.tools(id),
    
    -- Test Configuration
    traffic_split DECIMAL(3,2) DEFAULT 0.5, -- 0.5 = 50/50 split
    target_environment VARCHAR(50), -- production, staging, etc.
    target_users JSONB DEFAULT '[]', -- Specific users or groups
    
    -- Test Status
    status VARCHAR(20) DEFAULT 'draft', -- draft, active, completed, cancelled
    
    -- Results
    winner_tool_id INTEGER REFERENCES tool_catalog.tools(id),
    results JSONB DEFAULT '{}',
    
    -- Tracking
    started_at TIMESTAMP WITH TIME ZONE,
    completed_at TIMESTAMP WITH TIME ZONE,
    created_by VARCHAR(100),
    
    CHECK (tool_a_id != tool_b_id)
);

CREATE INDEX idx_ab_tests_status ON tool_catalog.tool_ab_tests(status);
CREATE INDEX idx_ab_tests_started_at ON tool_catalog.tool_ab_tests(started_at);
```

#### **6. `tool_audit_log` - Change tracking**
```sql
CREATE TABLE tool_catalog.tool_audit_log (
    id SERIAL PRIMARY KEY,
    
    -- What Changed
    tool_id INTEGER REFERENCES tool_catalog.tools(id),
    action VARCHAR(50) NOT NULL, -- created, updated, deleted, enabled, disabled, deprecated
    
    -- Change Details
    changes JSONB NOT NULL,
    -- Example: {"field": "time_estimate_ms", "old_value": "1000", "new_value": "1200"}
    
    -- Who and When
    changed_by VARCHAR(100) NOT NULL,
    changed_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    
    -- Context
    reason TEXT,
    ip_address VARCHAR(45)
);

CREATE INDEX idx_audit_tool_id ON tool_catalog.tool_audit_log(tool_id);
CREATE INDEX idx_audit_changed_at ON tool_catalog.tool_audit_log(changed_at);
CREATE INDEX idx_audit_changed_by ON tool_catalog.tool_audit_log(changed_by);
```

---

## 🏗️ Implementation Phases

### **Phase 1: Database Foundation (Week 1-2)**

#### **Deliverables**:
1. ✅ Database schema creation
2. ✅ Migration scripts
3. ✅ YAML-to-Database import tool
4. ✅ Basic CRUD operations
5. ✅ Unit tests

#### **Tasks**:

**1.1 Create Database Schema**
```bash
/database/tool-catalog-schema.sql
```

**1.2 Create Migration Tool**
```bash
/scripts/migrate_tools_to_db.py
```
- Reads all YAML files from `/pipeline/config/tools/`
- Validates each tool definition
- Imports into PostgreSQL
- Handles conflicts and versioning

**1.3 Create ToolCatalogService**
```bash
/pipeline/services/tool_catalog_service.py
```
- CRUD operations for tools
- Version management
- Validation logic
- Cache management

**1.4 Update HybridOrchestrator**
- Add database backend support
- Maintain YAML fallback for testing
- Add caching layer for performance

---

### **Phase 2: API & Service Layer (Week 3-4)**

#### **Deliverables**:
1. ✅ REST API for tool management
2. ✅ Tool validation service
3. ✅ Hot reload mechanism
4. ✅ API documentation
5. ✅ Integration tests

#### **Tasks**:

**2.1 Create Tool Catalog API**
```bash
/api/tool_catalog_api.py
```

**Endpoints**:
```
GET    /api/v1/tools                    # List all tools
GET    /api/v1/tools/{name}             # Get tool by name
GET    /api/v1/tools/{name}/versions    # Get all versions
POST   /api/v1/tools                    # Create new tool
PUT    /api/v1/tools/{name}             # Update tool
DELETE /api/v1/tools/{name}             # Delete tool
PATCH  /api/v1/tools/{name}/enable      # Enable tool
PATCH  /api/v1/tools/{name}/disable     # Disable tool

GET    /api/v1/tools/search             # Search tools
GET    /api/v1/tools/platform/{platform} # Get by platform
GET    /api/v1/tools/category/{category} # Get by category

POST   /api/v1/tools/{name}/validate    # Validate tool definition
POST   /api/v1/tools/import             # Bulk import from YAML
POST   /api/v1/tools/export             # Export to YAML

GET    /api/v1/capabilities             # List all capabilities
GET    /api/v1/capabilities/{name}/tools # Get tools by capability
```

**2.2 Create Validation Service**
```bash
/pipeline/services/tool_validator.py
```
- Schema validation
- Expression validation (time_estimate_ms, cost_estimate)
- Policy constraint validation
- Dependency checking
- Performance testing

**2.3 Implement Hot Reload**
- Cache invalidation on tool updates
- Event-driven reload mechanism
- Zero-downtime updates

---

### **Phase 3: Telemetry & Optimization (Week 5-6)**

#### **Deliverables**:
1. ✅ Telemetry collection service
2. ✅ Performance analysis tools
3. ✅ Auto-optimization recommendations
4. ✅ A/B testing framework
5. ✅ Monitoring dashboards

#### **Tasks**:

**3.1 Create Telemetry Service**
```bash
/pipeline/services/tool_telemetry_service.py
```
- Capture actual execution metrics
- Compare with estimates
- Identify performance drift
- Generate optimization recommendations

**3.2 Create Analysis Tools**
```bash
/scripts/analyze_tool_performance.py
```
- Statistical analysis of tool performance
- Identify outliers and anomalies
- Generate optimization suggestions
- Update tool profiles automatically

**3.3 Implement A/B Testing**
```bash
/pipeline/services/tool_ab_testing_service.py
```
- Create A/B tests for tool versions
- Traffic splitting logic
- Results analysis
- Automatic winner selection

---

### **Phase 4: Admin UI & Tooling (Week 7-8)**

#### **Deliverables**:
1. ✅ Admin web UI for tool management
2. ✅ Tool definition generator
3. ✅ Bulk import/export tools
4. ✅ Performance dashboards
5. ✅ Documentation

#### **Tasks**:

**4.1 Create Admin UI**
```bash
/frontend/admin/tool-catalog/
```

**Features**:
- Tool CRUD interface
- Visual tool definition editor
- Performance metrics dashboard
- A/B test management
- Audit log viewer
- Bulk operations

**4.2 Create Tool Generator**
```bash
/scripts/generate_tool_definition.py
```
- Interactive CLI tool
- Guided tool creation
- Template selection
- Validation and testing
- Direct database import

**4.3 Create Bulk Tools**
```bash
/scripts/bulk_import_tools.py
/scripts/bulk_export_tools.py
/scripts/bulk_update_tools.py
```

---

## 📦 File Structure

```
/home/opsconductor/opsconductor-ng/
├── database/
│   └── tool-catalog-schema.sql          # Database schema
│
├── pipeline/
│   ├── config/
│   │   └── tools/                       # YAML tool definitions (bootstrap)
│   │       ├── linux/
│   │       ├── windows/
│   │       ├── network/
│   │       ├── scheduler/
│   │       ├── custom/
│   │       └── templates/
│   │
│   ├── services/
│   │   ├── tool_catalog_service.py      # Main service
│   │   ├── tool_validator.py            # Validation
│   │   ├── tool_telemetry_service.py    # Telemetry
│   │   └── tool_ab_testing_service.py   # A/B testing
│   │
│   └── stages/
│       └── stage_b/
│           └── hybrid_orchestrator.py   # Updated to use DB
│
├── api/
│   └── tool_catalog_api.py              # REST API
│
├── frontend/
│   └── admin/
│       └── tool-catalog/                # Admin UI
│
├── scripts/
│   ├── migrate_tools_to_db.py           # YAML → DB migration
│   ├── generate_tool_definition.py      # Tool generator
│   ├── validate_tool.py                 # Validation script
│   ├── analyze_tool_performance.py      # Performance analysis
│   ├── bulk_import_tools.py             # Bulk import
│   ├── bulk_export_tools.py             # Bulk export
│   └── bulk_update_tools.py             # Bulk update
│
└── tests/
    └── test_tool_catalog/
        ├── test_tool_catalog_service.py
        ├── test_tool_validator.py
        ├── test_tool_telemetry.py
        └── test_tool_api.py
```

---

## 🚀 Quick Start Guide

### **Step 1: Create Database Schema**
```bash
psql -U opsconductor -d opsconductor -f database/tool-catalog-schema.sql
```

### **Step 2: Import Existing YAML Tools**
```bash
python scripts/migrate_tools_to_db.py --source pipeline/config/tools/ --validate
```

### **Step 3: Start Tool Catalog Service**
```bash
# Service starts automatically with main application
# Or run standalone:
python -m pipeline.services.tool_catalog_service
```

### **Step 4: Access Admin UI**
```bash
# Navigate to:
http://localhost:8080/admin/tool-catalog
```

### **Step 5: Add New Tool**
```bash
# Option 1: Use generator
python scripts/generate_tool_definition.py

# Option 2: Use API
curl -X POST http://localhost:8080/api/v1/tools \
  -H "Content-Type: application/json" \
  -d @new_tool.json

# Option 3: Use Admin UI
# Navigate to UI and click "Add Tool"
```

---

## 🔄 Migration Strategy

### **Phase 1: Dual Mode (Weeks 1-2)**
- YAML files remain primary source
- Database populated from YAML
- Read from database, fallback to YAML
- No breaking changes

### **Phase 2: Database Primary (Weeks 3-4)**
- Database becomes primary source
- YAML used for bootstrap only
- Admin UI for tool management
- API for programmatic access

### **Phase 3: YAML Deprecated (Weeks 5-6)**
- YAML files archived
- All operations via database
- Export capability maintained
- Full telemetry integration

### **Phase 4: Advanced Features (Weeks 7-8)**
- A/B testing enabled
- Auto-optimization active
- Performance dashboards live
- Multi-tenant support

---

## 📊 Success Metrics

### **Performance**
- ✅ Tool lookup < 10ms (with caching)
- ✅ Tool update propagation < 1 second
- ✅ Support 200+ tools without degradation
- ✅ API response time < 100ms (p95)

### **Reliability**
- ✅ 99.9% uptime for tool catalog service
- ✅ Zero data loss during updates
- ✅ Automatic rollback on validation failure
- ✅ Audit trail for all changes

### **Usability**
- ✅ Add new tool in < 5 minutes (via UI)
- ✅ Bulk import 100 tools in < 1 minute
- ✅ Real-time validation feedback
- ✅ Self-service tool management

---

## 🔒 Security Considerations

### **Access Control**
- Role-based access control (RBAC)
- Tool creation: Admin only
- Tool updates: Admin + Tool Owner
- Tool viewing: All authenticated users
- Audit logging for all changes

### **Validation**
- Schema validation on all inputs
- Expression sandboxing (safe_math_eval)
- SQL injection prevention
- XSS protection in UI
- Rate limiting on API

### **Data Protection**
- Encrypted connections (TLS)
- Sensitive data encryption at rest
- Backup and recovery procedures
- Version control for rollback

---

## 🎯 Next Steps

1. **Review and approve this plan**
2. **Prioritize tool categories** (which 200+ tools to add first?)
3. **Assign resources** (developers, DBAs, etc.)
4. **Set up development environment**
5. **Begin Phase 1 implementation**

---

## 📝 Notes

- **Backward Compatibility**: YAML files will continue to work during migration
- **Zero Downtime**: All updates can be done without system restart
- **Scalability**: Database design supports 1000+ tools
- **Extensibility**: Easy to add new tool metadata fields
- **Observability**: Full telemetry and audit trail

---

## ❓ Questions to Answer

Before starting implementation, please clarify:

1. **Tool Categories Priority**: Which categories should we populate first?
   - Linux commands (systemctl, ps, grep, awk, sed, etc.)
   - Windows commands (PowerShell, sc, net, wmic, etc.)
   - Network tools (tcpdump, wireshark, nmap, etc.)
   - Scheduler tools (cron, at, task scheduler, etc.)
   - Custom APIs (your internal services)

2. **Tool Sources**: Where will tool definitions come from?
   - Manual creation via UI
   - Bulk import from existing documentation
   - Auto-discovery from systems
   - Third-party tool catalogs

3. **Telemetry Requirements**: What metrics do you want to track?
   - Execution time
   - Success/failure rates
   - Cost (API calls, resources)
   - User satisfaction
   - Error patterns

4. **Multi-tenancy**: Do you need per-tenant tool catalogs?
   - Shared catalog for all users
   - Per-organization tool catalogs
   - Per-environment tool catalogs

5. **Integration Points**: What systems need to integrate?
   - Existing automation tools
   - Monitoring systems
   - CMDB/asset management
   - Ticketing systems

---

**Ready to proceed?** Let me know which phase to start with, or if you need any clarifications!