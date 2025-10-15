# Multi-Step Execution Quick Start Guide

## What is Multi-Step Execution?

Multi-step execution allows you to create complex automation workflows that:
- **Discover targets dynamically** using asset queries
- **Execute commands across multiple hosts** automatically
- **Use template variables** to reference data from previous steps
- **Handle loops automatically** when targeting multiple assets

## Quick Example

Here's a simple workflow that finds all Windows 10 servers and checks their disk space:

```json
{
  "execution_id": "health-check-001",
  "plan": {
    "name": "Windows Disk Space Check",
    "steps": [
      {
        "tool": "asset-query",
        "inputs": {
          "tags": ["win10"]
        }
      },
      {
        "tool": "Invoke-Command",
        "inputs": {
          "target_hosts": ["{{hostname}}"],
          "command": "Get-Volume C | Select-Object Size, SizeRemaining",
          "username": "admin",
          "password": "secret"
        }
      }
    ]
  },
  "tenant_id": "my-tenant",
  "actor_id": "my-user"
}
```

**What happens:**
1. Asset-query finds all Windows 10 hosts (e.g., 4 hosts)
2. System extracts variables: `hostnames`, `ip_addresses`, `assets`, `asset_count`
3. System detects `{{hostname}}` template variable in `target_hosts`
4. System expands step 2 into 4 separate executions (one per host)
5. Each execution runs on a different host automatically

## Installation & Setup

### 1. Ensure Services are Running

```bash
cd /home/opsconductor/opsconductor-ng
docker compose up -d
```

### 2. Verify Services are Healthy

```bash
# Check automation service
curl http://localhost:8010/health

# Check asset service
curl http://localhost:8002/health
```

### 3. Verify Test Data Exists

```bash
# Check for Windows 10 test assets
curl -X POST http://localhost:8002/execute-plan \
  -H "Content-Type: application/json" \
  -d '{
    "execution_id": "test-001",
    "plan": {
      "steps": [{
        "tool": "asset-query",
        "inputs": {"tags": ["win10"]}
      }]
    },
    "tenant_id": "test",
    "actor_id": "test"
  }'
```

## Running the Demos

### Interactive Demo

```bash
python3 demo_multistep_execution.py
```

This will show you a menu of demos:
1. Simple Asset Query
2. Template Variable Resolution
3. Loop Execution
4. Complex Workflow
5. Real-World Scenario

### Run All Tests

```bash
# Unit tests
python3 test_multistep_execution.py

# Integration tests
python3 test_e2e_multistep.py
```

## Key Concepts

### 1. Template Variables

Use `{{variable}}` to reference data from previous steps:

```json
{
  "command": "ping {{hostname}}",
  "target_host": "{{ip_address}}"
}
```

**Available variables after asset-query:**
- `{{hostname}}` - Asset hostname
- `{{ip_address}}` - Asset IP address
- `{{asset_count}}` - Number of assets found
- `{{assets}}` - Full asset list

### 2. Loop Execution

When you use template variables with plural parameter names, the system automatically creates a loop:

**Triggers loop execution:**
- Parameter name is plural: `target_hosts`, `hostnames`, `servers`
- Parameter contains template variable: `["{{hostname}}"]`
- Assets exist in context

**Example:**
```json
{
  "tool": "Invoke-Command",
  "inputs": {
    "target_hosts": ["{{hostname}}"],  // Plural + template = loop
    "command": "Get-Service"
  }
}
```

**Result:** If 5 assets found, this step executes 5 times (once per asset).

### 3. Step Dependencies

Steps execute sequentially. Each step can use data from previous steps:

```json
{
  "steps": [
    {
      "tool": "asset-query",
      "inputs": {"tags": ["web-servers"]}
    },
    {
      "tool": "Invoke-Command",
      "inputs": {
        "target_hosts": ["{{hostname}}"],  // Uses data from step 1
        "command": "Get-Process"
      }
    }
  ]
}
```

## Common Use Cases

### 1. Health Check Across All Servers

```json
{
  "steps": [
    {
      "tool": "asset-query",
      "inputs": {"tags": ["production"]}
    },
    {
      "tool": "ping",
      "inputs": {"target_hosts": ["{{hostname}}"]}
    },
    {
      "tool": "Invoke-Command",
      "inputs": {
        "target_hosts": ["{{hostname}}"],
        "command": "Get-Service | Where-Object {$_.Status -eq 'Running'}"
      }
    }
  ]
}
```

### 2. Patch Deployment

```json
{
  "steps": [
    {
      "tool": "asset-query",
      "inputs": {"tags": ["windows", "patch-group-1"]}
    },
    {
      "tool": "Invoke-Command",
      "inputs": {
        "target_hosts": ["{{hostname}}"],
        "command": "Install-WindowsUpdate -AcceptAll -AutoReboot",
        "username": "{{vault.admin_user}}",
        "password": "{{vault.admin_pass}}"
      }
    }
  ]
}
```

### 3. Configuration Audit

```json
{
  "steps": [
    {
      "tool": "asset-query",
      "inputs": {"os_type": "Windows"}
    },
    {
      "tool": "Invoke-Command",
      "inputs": {
        "target_hosts": ["{{hostname}}"],
        "command": "Get-ItemProperty -Path 'HKLM:\\Software\\Company\\Config'"
      }
    }
  ]
}
```

### 4. Log Collection

```json
{
  "steps": [
    {
      "tool": "asset-query",
      "inputs": {"tags": ["app-servers"]}
    },
    {
      "tool": "Invoke-Command",
      "inputs": {
        "target_hosts": ["{{hostname}}"],
        "command": "Get-EventLog -LogName Application -Newest 100"
      }
    }
  ]
}
```

## Debugging

### View Execution Logs

```bash
# View all logs
docker logs opsconductor-automation --tail 100

# View only loop execution
docker logs opsconductor-automation | grep -E '(Loop|🔁)'

# View template resolution
docker logs opsconductor-automation | grep template

# Follow logs in real-time
docker logs -f opsconductor-automation
```

### Common Issues

#### Issue: Template variables not resolved

**Symptoms:** Literal `{{hostname}}` appears in execution

**Solution:**
1. Verify asset-query step executed successfully
2. Check logs for "Extracting variables from asset-query"
3. Ensure variable names match exactly (case-sensitive)

#### Issue: Loop not executing

**Symptoms:** Only one execution instead of multiple

**Solution:**
1. Use plural parameter name: `target_hosts` not `target_host`
2. Ensure template variable syntax: `["{{hostname}}"]`
3. Verify assets exist in context (check asset-query results)

#### Issue: All iterations fail with same error

**Symptoms:** Every loop iteration fails identically

**Solution:**
1. Check credentials are provided
2. Verify network connectivity
3. Test command on single host first
4. Check timeout settings

## API Reference

### Execute Plan Endpoint

```bash
POST http://localhost:8010/execute-plan
Content-Type: application/json

{
  "execution_id": "unique-id",
  "plan": {
    "name": "Plan Name",
    "steps": [...]
  },
  "tenant_id": "tenant-id",
  "actor_id": "user-id"
}
```

### Response Format

```json
{
  "execution_id": "unique-id",
  "status": "completed",
  "step_results": [
    {
      "step": 1,
      "tool": "asset-query",
      "status": "success",
      "output": {...}
    },
    {
      "step": 2,
      "tool": "Invoke-Command",
      "status": "success",
      "loop_iteration": 1,
      "loop_total": 4,
      "stdout": "..."
    }
  ],
  "duration_seconds": 12.5
}
```

## Performance Tips

### For Small Deployments (1-10 hosts)
- Current implementation works great
- Sequential execution is fine
- No special configuration needed

### For Medium Deployments (10-50 hosts)
- Consider increasing timeouts
- Monitor execution duration
- Use specific asset queries to limit scope

### For Large Deployments (50+ hosts)
- Use batching (split into multiple executions)
- Consider implementing parallel execution
- Use asset tags to create smaller groups
- Monitor resource usage

## Next Steps

1. **Read Full Documentation**: See `MULTISTEP_EXECUTION.md` for complete details
2. **Run Demos**: Execute `python3 demo_multistep_execution.py`
3. **Run Tests**: Execute `python3 test_multistep_execution.py`
4. **Try Your Own Workflow**: Create a custom multi-step plan
5. **Monitor Logs**: Watch execution in real-time

## Getting Help

- **Documentation**: `MULTISTEP_EXECUTION.md`
- **Examples**: `demo_multistep_execution.py`
- **Tests**: `test_multistep_execution.py`, `test_e2e_multistep.py`
- **Logs**: `docker logs opsconductor-automation`

## Example: Complete Workflow

Here's a complete example you can run right now:

```bash
curl -X POST http://localhost:8010/execute-plan \
  -H "Content-Type: application/json" \
  -d '{
    "execution_id": "demo-'$(date +%s)'",
    "plan": {
      "name": "Windows Health Check",
      "steps": [
        {
          "tool": "asset-query",
          "inputs": {
            "tags": ["win10"],
            "limit": 5
          }
        },
        {
          "tool": "ping",
          "inputs": {
            "target_hosts": ["{{hostname}}"],
            "count": 2
          }
        }
      ]
    },
    "tenant_id": "demo",
    "actor_id": "demo-user"
  }'
```

This will:
1. Find up to 5 Windows 10 hosts
2. Ping each host 2 times
3. Return results for all executions

Check the logs to see loop execution:
```bash
docker logs opsconductor-automation --tail 50 | grep -E '(Loop|🔁)'
```

You should see:
```
🔁 Loop detected: Executing step 2 for 4 items
🔁 Loop iteration 1/4
🔁 Loop iteration 2/4
🔁 Loop iteration 3/4
🔁 Loop iteration 4/4
```

## Success!

You're now ready to use the multi-step execution system! Start with the demos and work your way up to custom workflows.