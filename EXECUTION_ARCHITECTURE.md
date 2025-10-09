# OpsConductor Execution Architecture

## 🔒 SECURITY PRINCIPLE: SEPARATION OF ORCHESTRATION AND EXECUTION

**CRITICAL ARCHITECTURAL DECISION:**
The AI-pipeline container **NEVER** executes commands directly. It only orchestrates.
All command execution happens in the `automation-service` container.

---

## 🏗️ Architecture Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                         USER REQUEST                             │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│                      AI-PIPELINE CONTAINER                       │
│                    (ORCHESTRATION ONLY)                          │
├─────────────────────────────────────────────────────────────────┤
│  Stage A: Intent Classification & Entity Extraction             │
│  Stage B: Tool Selection                                         │
│  Stage C: Planning & Step Generation                            │
│  Stage D: Approval Workflow                                      │
│  Stage E: Execution Routing (delegates to automation-service)   │
│                                                                   │
│  ❌ NO SSH libraries (paramiko removed)                         │
│  ❌ NO WinRM libraries (pywinrm removed)                        │
│  ❌ NO execution engine                                          │
│  ✅ ONLY orchestration logic                                    │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             │ HTTP POST /execute-plan
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│                  AUTOMATION-SERVICE CONTAINER                    │
│                   (EXECUTION ONLY)                               │
├─────────────────────────────────────────────────────────────────┤
│  ✅ Execution Engine                                            │
│  ✅ SSH Client (openssh-client, paramiko)                      │
│  ✅ WinRM Client (pywinrm)                                      │
│  ✅ Network Tools (ping, traceroute)                           │
│  ✅ HTTP Client (requests, httpx)                              │
│                                                                   │
│  Executes commands on:                                           │
│  - Local container (bash commands)                              │
│  - Remote Linux hosts (SSH)                                     │
│  - Remote Windows hosts (WinRM)                                 │
│  - HTTP APIs (REST calls)                                       │
│  - Databases (PostgreSQL, etc.)                                 │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             │ Results
                             │
                             ▼
                    ┌────────────────────┐
                    │  TARGET SYSTEMS    │
                    │  - Linux Servers   │
                    │  - Windows Servers │
                    │  - Network Devices │
                    │  - APIs            │
                    │  - Databases       │
                    └────────────────────┘
```

---

## 📦 Container Responsibilities

### **ai-pipeline** (Port 3005)
**Role:** Orchestration & Intelligence
**Responsibilities:**
- ✅ Understand user intent
- ✅ Select appropriate tools
- ✅ Generate execution plans
- ✅ Route execution requests
- ✅ Track execution status
- ❌ **NEVER execute commands**

**Installed Libraries:**
- FastAPI, Pydantic (API framework)
- httpx (HTTP client for service communication)
- asyncpg, SQLAlchemy (database access)
- Redis (caching)
- ❌ **NO paramiko** (SSH removed)
- ❌ **NO pywinrm** (WinRM removed)
- ❌ **NO requests** (execution library removed)

---

### **automation-service** (Port 8010)
**Role:** Command Execution
**Responsibilities:**
- ✅ Execute commands locally (bash)
- ✅ Execute commands on remote Linux hosts (SSH)
- ✅ Execute commands on remote Windows hosts (WinRM)
- ✅ Execute HTTP API calls
- ✅ Execute database queries
- ✅ Manage connections and credentials
- ❌ **NO orchestration logic**

**Installed Libraries:**
- paramiko (SSH connections)
- pywinrm (WinRM connections)
- openssh-client, sshpass (SSH binaries)
- iputils-ping (network tools)
- requests, httpx (HTTP clients)
- asyncpg, SQLAlchemy (database access)

**Installed System Tools:**
- `ping` - Network connectivity checks
- `ssh` - SSH client
- `sshpass` - Non-interactive SSH authentication
- `curl` - HTTP requests

---

## 🔄 Execution Flow

### **1. User Request**
```
User: "Check disk space on web-server-01"
```

### **2. AI-Pipeline Orchestration**
```python
# Stage A: Extract intent and entities
intent = "check_disk_space"
target_host = "web-server-01"

# Stage B: Select tool
tool = "check_disk_space"

# Stage C: Generate plan
plan = {
    "steps": [
        {
            "tool": "check_disk_space",
            "parameters": {
                "target_host": "web-server-01",
                "path": "/"
            }
        }
    ]
}

# Stage E: Delegate to automation-service
response = await httpx.post(
    "http://automation-service:3003/execute-plan",
    json={
        "execution_id": "...",
        "plan": plan,
        "tenant_id": "...",
        "actor_id": ...
    }
)
```

### **3. Automation-Service Execution**
```python
# Receive plan from ai-pipeline
@app.post("/execute-plan")
async def execute_plan(request):
    # Load execution engine
    engine = ExecutionEngine()
    
    # Execute plan
    result = await engine.execute(execution)
    
    # Return result to ai-pipeline
    return {
        "status": "success",
        "result": {...},
        "step_results": [...]
    }
```

### **4. Execution Engine**
```python
# Determine execution method from tool definition
tool_def = load_tool("check_disk_space")

if tool_def.execution.method == "ssh":
    # SSH to target host
    ssh_client = SSHClient()
    ssh_client.connect("web-server-01", username="...", password="...")
    result = ssh_client.exec_command("df -h /")
```

---

## 🎯 Global Execution Assumption

**ALL COMMANDS ORIGINATE FROM OPSCONDUCTOR SYSTEM**

This means:
- ✅ User says: "Ping 192.168.1.100"
- ✅ System assumes: Execute FROM automation-service TO 192.168.1.100
- ✅ User says: "Check disk on web-server-01"
- ✅ System assumes: SSH FROM automation-service TO web-server-01

**No need to specify source host - it's always automation-service!**

---

## 🛠️ Tool Execution Specification

Tools define WHERE and HOW they execute:

```yaml
name: "ping"
description: "Check network connectivity"

execution:
  location: "automation-service"  # Always from OpsConductor
  method: "local-command"  # Run ping locally in container
  requires_target: true  # Needs IP/hostname
  target_type: "host"

parameters:
  - name: "target"
    description: "IP or hostname to ping"
    required: true

command_template: "ping -c 4 {target}"
```

**Execution Methods:**
- `local-command` - Run command in automation-service container
- `ssh` - SSH to remote Linux host
- `winrm` - WinRM to remote Windows host
- `http` - HTTP API call
- `database` - Database query

---

## 🔐 Security Benefits

### **Separation of Concerns**
- AI logic isolated from execution
- Execution isolated from AI
- Clear security boundaries

### **Attack Surface Reduction**
- AI-pipeline cannot execute arbitrary commands
- Compromised AI logic cannot directly access systems
- Execution requires explicit delegation

### **Audit Trail**
- All execution requests logged at ai-pipeline
- All actual executions logged at automation-service
- Clear chain of custody

### **Credential Isolation**
- AI-pipeline never handles credentials
- Credentials only stored in automation-service
- Reduced credential exposure

---

## 📊 Monitoring & Observability

### **AI-Pipeline Metrics**
- Requests received
- Plans generated
- Execution requests sent
- Execution results received

### **Automation-Service Metrics**
- Execution requests received
- Commands executed
- Success/failure rates
- Execution duration

### **Health Checks**
- AI-Pipeline: `http://localhost:3005/health`
- Automation-Service: `http://localhost:8010/health`

---

## 🚀 Deployment

### **Development**
```bash
docker-compose up ai-pipeline automation-service
```

### **Production**
- Scale automation-service independently
- Multiple automation-service instances for load balancing
- AI-pipeline remains single instance (orchestration)

---

## 📝 Summary

| Aspect | AI-Pipeline | Automation-Service |
|--------|-------------|-------------------|
| **Role** | Orchestration | Execution |
| **SSH** | ❌ No | ✅ Yes |
| **WinRM** | ❌ No | ✅ Yes |
| **Network Tools** | ❌ No | ✅ Yes (ping, etc.) |
| **Execution Engine** | ❌ No | ✅ Yes |
| **Credentials** | ❌ No | ✅ Yes |
| **Tool Selection** | ✅ Yes | ❌ No |
| **Planning** | ✅ Yes | ❌ No |
| **LLM Access** | ✅ Yes | ❌ No |

**REMEMBER: AI-pipeline orchestrates, automation-service executes. ALWAYS.**