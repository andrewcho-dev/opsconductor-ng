# Multi-Service Execution - Quick Reference Guide

## 🎯 Overview

The system now routes execution requests to different services based on tool metadata. This guide provides quick answers to common questions.

---

## 🔍 How Routing Works

```
User Request
    ↓
AI Pipeline (Stage E)
    ↓
Read tool's execution_location from YAML
    ↓
Route to appropriate service:
    • automation-service (Linux, Windows, DB, Cloud, etc.)
    • communication-service (Email, Slack, Teams, Webhooks)
    • asset-service (Asset CRUD operations)
    • network-analyzer-service (Network tools, packet capture)
    ↓
Service executes tool and returns result
```

---

## 📋 Quick Commands

### Test Routing Logic
```bash
cd /home/opsconductor/opsconductor-ng
python3 test_multi_service_routing.py
```

### Add execution_location to New Tools
```bash
cd /home/opsconductor/opsconductor-ng
python3 add_execution_location.py
```

### Check Tool's Execution Location
```bash
grep "execution_location" /home/opsconductor/opsconductor-ng/pipeline/config/tools/custom/sendmail.yaml
```

### Find All Tools for a Service
```bash
grep -r "execution_location: communication-service" /home/opsconductor/opsconductor-ng/pipeline/config/tools/
```

---

## 🛠️ Tool Configuration

### Example Tool YAML
```yaml
tool_name: sendmail
execution_location: communication-service  # ← ADD THIS FIELD
version: '1.0'
description: Send email messages
platform: custom
category: communication
# ... rest of configuration
```

### Valid execution_location Values
- `automation-service` (default)
- `communication-service`
- `asset-service`
- `network-service` (maps to network-analyzer-service)

---

## 🔧 Service Endpoints

All services implement the same endpoint contract:

### Request Format
```json
POST /execute-plan
{
  "execution_id": "exec-123",
  "plan": {
    "steps": [
      {
        "tool": "sendmail",
        "parameters": {
          "to": "user@example.com",
          "subject": "Test",
          "body": "Hello"
        }
      }
    ]
  },
  "tenant_id": "tenant-1",
  "actor_id": 1
}
```

### Response Format
```json
{
  "execution_id": "exec-123",
  "status": "completed",
  "result": {
    "success": true,
    "message": "Execution completed"
  },
  "step_results": [
    {
      "step": 1,
      "tool": "sendmail",
      "status": "success",
      "output": "Email sent successfully"
    }
  ],
  "completed_at": "2025-01-08T12:00:00Z",
  "error_message": null
}
```

---

## 🎯 Service Responsibilities

### Automation Service (Port 3003)
**Tools:** 134  
**Domains:** Linux, Windows, Database, Cloud, Container, Monitoring  
**Examples:** ping, ls, docker_ps, kubectl_get, mysql_query

### Communication Service (Port 3004)
**Tools:** 4  
**Domains:** Email, Chat, Webhooks  
**Examples:** sendmail, slack_cli, teams_cli, webhook_sender

### Asset Service (Port 3005)
**Tools:** 5  
**Domains:** Asset Management, Inventory  
**Examples:** asset_query, asset_create, asset_update, asset_delete, asset_list

### Network Analyzer Service (Port 3006)
**Tools:** 41  
**Domains:** Network Analysis, Packet Capture, VAPIX  
**Examples:** tcpdump, tshark, nmap, scapy, pyshark

---

## 🐛 Troubleshooting

### Tool Not Routing Correctly

**Check 1:** Does tool YAML have execution_location?
```bash
grep "execution_location" /path/to/tool.yaml
```

**Check 2:** Is the service name correct?
Valid values: `automation-service`, `communication-service`, `asset-service`, `network-service`

**Check 3:** Does the tool file exist?
```bash
find /home/opsconductor/opsconductor-ng/pipeline/config/tools/ -name "toolname.yaml"
```

**Check 4:** Check Stage E logs
Look for: `Routing execution to {service_name}`

### Tool File Not Found

**Problem:** Tool name uses hyphens but file uses underscores (or vice versa)

**Solution:** Stage E automatically handles both variants:
- Tries `asset-query.yaml` first
- Falls back to `asset_query.yaml`
- No action needed

### Service Not Responding

**Check 1:** Is the service running?
```bash
docker ps | grep service-name
```

**Check 2:** Is the service URL correct?
Check environment variables or default URLs in Stage E

**Check 3:** Does the service have /execute-plan endpoint?
```bash
curl -X POST http://service-name:port/execute-plan
```

---

## 📝 Adding a New Tool

### Step 1: Create Tool YAML
```yaml
tool_name: my-new-tool
execution_location: communication-service  # Choose appropriate service
version: '1.0'
description: My new tool description
platform: custom
category: communication
# ... add capabilities, parameters, etc.
```

### Step 2: Add Tool Handler (if needed)
If the service doesn't have a handler for this tool type, add one:

```python
async def _execute_my_new_tool(self, step: Dict[str, Any]) -> Dict[str, Any]:
    """Execute my-new-tool."""
    try:
        # Implementation here
        return {
            "status": "success",
            "output": "Tool executed successfully"
        }
    except Exception as e:
        return {
            "status": "failed",
            "error": str(e)
        }
```

### Step 3: Test Routing
```bash
python3 test_multi_service_routing.py
```

---

## 🚀 Adding a New Service

### Step 1: Create Service with Endpoint
```python
from fastapi import FastAPI
from typing import Dict, Any

app = FastAPI()

@app.post("/execute-plan")
async def execute_plan_from_pipeline(request: Dict[str, Any]):
    execution_id = request.get("execution_id")
    plan = request.get("plan", {})
    
    # Execute plan steps
    step_results = []
    for step in plan.get("steps", []):
        result = await execute_step(step)
        step_results.append(result)
    
    return {
        "execution_id": execution_id,
        "status": "completed",
        "result": {"success": True},
        "step_results": step_results,
        "completed_at": datetime.utcnow().isoformat(),
        "error_message": None
    }
```

### Step 2: Add Service to Stage E Mapping
Edit `/pipeline/stages/stage_e/executor.py`:

```python
service_urls = {
    "automation-service": os.getenv("AUTOMATION_SERVICE_URL", "http://automation-service:3003"),
    "communication-service": os.getenv("COMMUNICATION_SERVICE_URL", "http://communication-service:3004"),
    "asset-service": os.getenv("ASSET_SERVICE_URL", "http://asset-service:3005"),
    "network-service": os.getenv("NETWORK_SERVICE_URL", "http://network-analyzer-service:3006"),
    "my-new-service": os.getenv("MY_NEW_SERVICE_URL", "http://my-new-service:3007"),  # ADD THIS
}
```

### Step 3: Update Tool Definitions
Set `execution_location: my-new-service` in relevant tool YAMLs

### Step 4: Test
```bash
python3 test_multi_service_routing.py
```

---

## 🔐 Environment Variables

Override service URLs via environment variables:

```bash
export AUTOMATION_SERVICE_URL="http://automation-service:3003"
export COMMUNICATION_SERVICE_URL="http://communication-service:3004"
export ASSET_SERVICE_URL="http://asset-service:3005"
export NETWORK_SERVICE_URL="http://network-analyzer-service:3006"
```

---

## 📊 Monitoring

### Check Routing Logs
```bash
# Stage E logs show routing decisions
grep "Routing execution" /var/log/ai-pipeline.log

# Service logs show execution requests
grep "Received execution request" /var/log/communication-service.log
```

### Verify Service Health
```bash
curl http://automation-service:3003/health
curl http://communication-service:3004/health
curl http://asset-service:3005/health
curl http://network-analyzer-service:3006/health
```

---

## ⚡ Performance Tips

1. **Tool Metadata Caching**: Stage E loads tool YAML on every request. Consider caching for high-volume scenarios.

2. **Service Pooling**: Use connection pooling for HTTP requests to services.

3. **Async Execution**: All service endpoints use async/await for better concurrency.

4. **Batch Operations**: Group multiple tool executions in a single plan when possible.

---

## 🎓 Best Practices

### Tool Design
- ✅ Keep tools focused on single responsibility
- ✅ Use appropriate execution_location for tool's domain
- ✅ Include comprehensive error handling
- ✅ Document expected parameters and outputs

### Service Design
- ✅ Implement /execute-plan endpoint with standard contract
- ✅ Add tool-specific handlers for better organization
- ✅ Include comprehensive logging
- ✅ Return structured error messages

### Routing Logic
- ✅ Always specify execution_location in tool YAML
- ✅ Use fallback to automation-service for unknown tools
- ✅ Log routing decisions for debugging
- ✅ Handle both hyphenated and underscored tool names

---

## 📚 Related Documentation

- `MULTI_SERVICE_EXECUTION_IMPLEMENTATION.md` - Detailed implementation guide
- `IMPLEMENTATION_COMPLETE.md` - Executive summary
- `EXECUTION_ARCHITECTURE_AUDIT.md` - Original audit report
- `test_multi_service_routing.py` - Routing test script

---

## 🆘 Getting Help

### Common Issues
1. **Tool not routing correctly** → Check execution_location in YAML
2. **Service not found** → Check service name mapping in Stage E
3. **Tool file not found** → Check filename (hyphen vs underscore)
4. **Endpoint not responding** → Check service is running and has /execute-plan

### Debug Checklist
- [ ] Tool YAML exists and has execution_location field
- [ ] Service name is valid (automation, communication, asset, network)
- [ ] Service is running and accessible
- [ ] Service has /execute-plan endpoint
- [ ] Stage E logs show routing decision
- [ ] Service logs show execution request received

---

**Last Updated:** January 2025  
**Version:** 1.0  
**Status:** Production Ready (Routing), Stub Implementations (Execution)