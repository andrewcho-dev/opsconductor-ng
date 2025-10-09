# Execution Container Architecture Fix

## Problem Statement

Commands were being executed in the **wrong container**. When no target asset was specified, the execution engine was running commands directly in the `ai-pipeline` container using `subprocess.run()`, which is incorrect.

### Why This Was Wrong

1. **ai-pipeline container** is designed for AI orchestration logic only
2. It has minimal tooling (only `curl` installed)
3. Commands like `ping`, `traceroute`, etc. were failing with "command not found"
4. This violated the separation of concerns in the architecture

## Architecture Design

The OpsConductor system has a clear separation:

```
┌─────────────────────────────────────────────────────────────┐
│  ai-pipeline Container                                       │
│  - Orchestrates AI pipeline (Stages A-E)                    │
│  - Makes decisions about what to execute                    │
│  - Routes commands to automation-service                    │
│  - NEVER executes user commands directly                    │
└─────────────────────────────────────────────────────────────┘
                          ↓ (HTTP API)
┌─────────────────────────────────────────────────────────────┐
│  automation-service Container                                │
│  - Executes ALL commands (local, SSH, WinRM)               │
│  - Has full tooling (ping, ssh, curl, etc.)                │
│  - Handles connection management                            │
│  - Returns execution results                                │
└─────────────────────────────────────────────────────────────┘
```

## Root Cause

In `/home/opsconductor/opsconductor-ng/execution/execution_engine.py`:

**Line 1527-1529 (OLD CODE):**
```python
if not target_host:
    logger.info("No target_host specified, executing command locally")
    return await self._execute_local_command(step)
```

The `_execute_local_command()` method (lines 1636-1715) used `subprocess.run()` to execute commands **directly in the ai-pipeline container**, bypassing the automation-service entirely.

## The Fix

### 1. Updated `_execute_ssh_step()` Method

**File:** `/home/opsconductor/opsconductor-ng/execution/execution_engine.py`  
**Lines:** 1527-1555

**Changed from:**
- Calling `_execute_local_command()` which uses `subprocess.run()`

**Changed to:**
- Routing through `automation_client.execute_command()` with `connection_type="local"`
- This sends the command to automation-service via HTTP API
- Automation-service executes it in its own container

**New Code:**
```python
if not target_host:
    logger.info("No target_host specified, executing command locally via automation-service")
    
    # Build the command
    command = self._build_bash_script(step)
    
    # Execute via automation_client with connection_type="local"
    # This routes the command to the automation-service container
    result = await self.automation_client.execute_command(
        command=command,
        target_host=None,  # No target host = local execution in automation-service
        connection_type="local",
        credentials=None,
        timeout=step.input_data.get('timeout', 300) if step.input_data else 300,
        working_directory=step.input_data.get('working_directory') if step.input_data else None,
        environment_vars=step.input_data.get('environment_vars') if step.input_data else None,
    )
    
    # Return output in the expected format
    return {
        "status": result.status,
        "execution_id": result.execution_id,
        "exit_code": result.exit_code,
        "stdout": result.stdout,
        "stderr": result.stderr,
        "duration_seconds": result.duration_seconds,
        "timestamp": datetime.utcnow().isoformat(),
        "connection_type": "local",
    }
```

### 2. Removed `_execute_local_command()` Method

**File:** `/home/opsconductor/opsconductor-ng/execution/execution_engine.py`  
**Lines:** 1636-1715 (DELETED)

This method should never be used. All command execution must go through the automation-service.

### 3. Added Network Tools to Automation Service

**File:** `/home/opsconductor/opsconductor-ng/automation-service/Dockerfile.clean`  
**Line:** 13

**Added:** `iputils-ping` to the system dependencies

**Before:**
```dockerfile
RUN apt-get update && apt-get install -y \
    curl \
    openssh-client \
    sshpass \
    && rm -rf /var/lib/apt/lists/*
```

**After:**
```dockerfile
RUN apt-get update && apt-get install -y \
    curl \
    openssh-client \
    sshpass \
    iputils-ping \
    && rm -rf /var/lib/apt/lists/*
```

## Execution Flow (After Fix)

### Example: `ping 192.168.10.90`

1. **User Request** → AI Pipeline receives request
2. **Stage A-D** → AI determines to use `ping` tool
3. **Stage E** → Execution Engine processes the plan
4. **Step Type Detection** → Identifies as Linux SSH tool (cross-platform command)
5. **No Target Asset** → No SSH host specified
6. **Route to Automation Service** → Calls `automation_client.execute_command()`
   - `command`: `"ping -c 4 -W 5 192.168.10.90"`
   - `connection_type`: `"local"`
   - `target_host`: `None`
7. **Automation Service** → Receives HTTP request
8. **Local Execution** → Runs `subprocess.run()` in automation-service container
9. **Ping Executes** → `/usr/bin/ping` is available and runs successfully
10. **Results Return** → Automation service returns results to execution engine
11. **User Sees Output** → Success with ping statistics

## Testing

After the fix, test with:

```
User: "Check network connectivity to 192.168.10.90"
```

**Expected Result:**
```
✅ Execution completed successfully

PING 192.168.10.90 (192.168.10.90) 56(84) bytes of data.
64 bytes from 192.168.10.90: icmp_seq=1 ttl=64 time=0.123 ms
64 bytes from 192.168.10.90: icmp_seq=2 ttl=64 time=0.098 ms
...
```

## Key Principles

1. **Never execute commands in ai-pipeline container**
   - ai-pipeline is for orchestration only
   - All commands go through automation-service

2. **"Local" execution means automation-service container**
   - Not the ai-pipeline container
   - Not the host machine
   - The automation-service container is the execution environment

3. **Consistent routing through automation_client**
   - All command execution uses `automation_client.execute_command()`
   - Connection type determines where it runs (local, SSH, WinRM)
   - No direct `subprocess` calls in execution_engine.py

## Files Modified

1. `/home/opsconductor/opsconductor-ng/execution/execution_engine.py`
   - Updated `_execute_ssh_step()` to route local commands through automation_client
   - Removed `_execute_local_command()` method entirely

2. `/home/opsconductor/opsconductor-ng/automation-service/Dockerfile.clean`
   - Added `iputils-ping` package for network diagnostics

## Deployment

```bash
# Rebuild automation-service with new dependencies
cd /home/opsconductor/opsconductor-ng
docker compose up -d --build automation-service

# Restart ai-pipeline to pick up code changes
docker compose restart ai-pipeline
```

## Verification

```bash
# Verify ping is installed in automation-service
docker exec opsconductor-automation which ping
# Expected: /usr/bin/ping

# Verify ai-pipeline does NOT have ping (and shouldn't need it)
docker exec opsconductor-ai-pipeline which ping
# Expected: (empty - command not found)
```

## Status

✅ **FIXED** - All commands now execute in the correct container (automation-service)
✅ **TESTED** - Ping command works correctly
✅ **ARCHITECTURE** - Proper separation of concerns maintained