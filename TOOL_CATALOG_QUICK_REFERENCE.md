# Tool Catalog Quick Reference Card

## 📊 Current Status
- **Tools Loaded**: 5 (powershell, grep, htop, prometheus, github_api)
- **Target**: 150+ tools
- **Progress**: 3.3%

## 🎯 Top 5 Tools to Add First (Quick Win)

| # | Tool | Platform | Why Critical |
|---|------|----------|--------------|
| 1 | **systemctl** | Linux | Most requested Linux service management |
| 2 | **Get-Service** | Windows | Most requested Windows service management |
| 3 | **ps** | Linux | Most requested process listing |
| 4 | **curl** | Multi-platform | Most requested HTTP client |
| 5 | **tcpdump** | Network | Most requested packet capture |

**Time to implement**: ~1 hour  
**Impact**: Immediate improvement in Stage B tool selection

## 🚀 Quick Commands

### Check Current Status
```bash
# Check tool count
curl http://localhost:3005/api/v1/tools/health

# List all tools
curl http://localhost:3005/api/v1/tools | jq

# Check database
docker exec opsconductor-postgres psql -U opsconductor -d opsconductor \
  -c "SELECT tool_name, platform, category FROM tool_catalog.tools;"
```

### Generate New Tool
```bash
# From template
python scripts/tool_from_template.py \
  --name "systemctl" \
  --platform linux \
  --category automation \
  --description "Manage systemd services"
```

### Migrate Tool to Database
```bash
# Single tool
python scripts/migrate_tools_to_db.py \
  --tool pipeline/config/tools/linux/systemctl.yaml

# All tools in directory
python scripts/migrate_tools_to_db.py \
  --directory pipeline/config/tools/linux/
```

### Verify Integration
```bash
# Test ProfileLoader
docker exec opsconductor-ai-pipeline python -c "
from pipeline.stages.stage_b.profile_loader import ProfileLoader
loader = ProfileLoader(use_database=True)
profiles = loader.load()
print(f'Loaded {len(profiles.tools)} tools')
for tool_name in list(profiles.tools.keys())[:10]:
    print(f'  - {tool_name}')
"
```

## 📋 Phase 1 Breakdown (30 Tools)

### Windows (10 tools)
- Get-Service, Get-Process, Get-EventLog
- Get-ComputerInfo, Get-NetAdapter, Get-NetIPAddress
- Test-NetConnection, Get-Counter, Get-HotFix
- Invoke-Command

### Linux (10 tools)
- ps, df, free, systemctl, journalctl
- curl, ping, netstat, ss, dig

### Network (10 tools)
- tcpdump, tshark, http-analyzer, dns-analyzer
- tcp-analyzer, udp-analyzer, tls-analyzer
- nmap, ssh-analyzer, scapy

## 🔧 Service Integration

| Service | Port | Current | Planned | Gap |
|---------|------|---------|---------|-----|
| automation-service | 8010 | 1 | 40 | 39 |
| network-analyzer-service | 8006 | 1 | 25 | 24 |
| asset-service | 8002 | 0 | 15 | 15 |
| communication-service | 8004 | 0 | 10 | 10 |

## 📚 Documentation

- **TOOL_CATALOG_EXPANSION_PLAN.md** - Full 214-tool plan
- **TOOL_CATALOG_QUICK_RECOMMENDATIONS.md** - Phase 1 details
- **TOOL_CATALOG_INTEGRATION_STATUS.md** - Integration verification
- **TOOL_CATALOG_OPERATIONS_RUNBOOK.md** - Operations guide
- **TOOL_CATALOG_DEPLOYMENT_GUIDE.md** - Deployment guide

## 🎯 Success Metrics

### Coverage
- Platform: Windows ✅ Linux ✅ Network ✅ Multi-platform ✅
- Category: System, Network, Automation, Monitoring, Security, Database, Cloud, Container
- Services: 4 services integrated

### Performance
- Tool Loading: < 500ms
- Tool Selection: < 100ms
- Cache Hit Rate: > 95%
- DB Query Time: < 5ms (P95)

## 📅 Timeline

| Phase | Duration | Tools | Focus |
|-------|----------|-------|-------|
| Phase 1 | Week 1-2 | 30 | Critical Foundation |
| Phase 2 | Week 3-4 | 25 | Service Integration |
| Phase 3 | Week 5-6 | 20 | Security & Compliance |
| Phase 4 | Week 7-8 | 35 | Database & Cloud |
| Phase 5 | Week 9-10 | 30 | Containers & Monitoring |

**Total**: 10 weeks, 140 tools

## ✅ Next Steps

1. Review expansion plan documents
2. Decide which 5-10 tools to add first
3. Generate tool definitions with `tool_from_template.py`
4. Customize YAML files
5. Migrate to database with `migrate_tools_to_db.py`
6. Verify with ProfileLoader
7. Test Stage B tool selection
8. Iterate!

---

**Quick Start**: Add the top 5 tools in the next hour for immediate impact! 🚀
