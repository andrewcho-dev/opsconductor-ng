# Multi-Step Orchestration Fix

## Problem Summary

The AI was generating multi-step execution plans that failed with the error:
```
❌ Execution failed: One or more asset steps failed
```

### Root Cause

The system had a fundamental architectural flaw in how it handled multi-step plans that span multiple services:

1. **Incorrect Routing**: Stage E (executor) was routing the ENTIRE plan to a single service based on the FIRST tool
   - Example: Plan with `asset-query` + `Get-Volume` was sent entirely to asset-service
   - asset-service doesn't know how to execute `Get-Volume` (a PowerShell command)
   - Result: Second step failed silently

2. **Missing Orchestration**: The AI pipeline wasn't acting as a true orchestrator
   - It should route each step to the appropriate service
   - It should pass results between steps for variable resolution
   - Instead, it was delegating the entire plan to one service

3. **Credential Issues**: The LLM was generating hardcoded credentials
   - Generated: `username: "admin_user", password: "admin_password"`
   - Should use: Asset credentials from the database
   - The system had credential fetching logic but it wasn't being triggered

## Solution Implemented

### 1. Step-by-Step Orchestration (Stage E)

**File**: `pipeline/stages/stage_e/executor.py`

**Changes**:
- Modified `_execute_immediate()` to orchestrate steps individually
- Added `_get_service_url_for_tool()` to route each tool to the correct service
- Each step is now executed separately with its own service routing
- Previous step results are passed to subsequent steps for variable resolution

**Benefits**:
- Multi-service plans now work correctly
- Each tool goes to its specialized service
- Proper separation of concerns (orchestrator vs executor)

### 2. Previous Results Handling (Automation Service)

**File**: `automation-service/main_clean.py`

**Changes**:
- Added logic to load `previous_results` from the plan
- Previous results are loaded into the execution context
- Variables from previous steps (like assets) are available for template resolution

**Benefits**:
- Steps can reference data from previous steps
- Asset query results flow into subsequent commands
- Template variables like `{{item.ip_address}}` resolve correctly

### 3. Automatic Asset Credential Detection

**File**: `automation-service/execution_context.py`

**Changes**:
- Added automatic detection when looping over assets
- If no explicit credentials provided, automatically use asset credentials
- Sets `use_asset_credentials: true` and `asset_id` automatically

**Benefits**:
- No need for LLM to know about credential management
- Credentials are fetched securely from asset database
- Works even when LLM generates hardcoded credentials

## Architecture Pattern

The fix implements the **Orchestrator Pattern** - a best practice for AI automation systems:

```
┌─────────────────────────────────────────────────────────────┐
│                      AI Pipeline (Stage E)                   │
│                        ORCHESTRATOR                          │
│  - Receives multi-step plan                                  │
│  - Routes each step to appropriate service                   │
│  - Passes results between steps                              │
│  - Aggregates final results                                  │
└─────────────────────────────────────────────────────────────┘
                            │
        ┌───────────────────┼───────────────────┐
        │                   │                   │
        ▼                   ▼                   ▼
┌──────────────┐    ┌──────────────┐    ┌──────────────┐
│ Asset        │    │ Automation   │    │ Network      │
│ Service      │    │ Service      │    │ Service      │
│              │    │              │    │              │
│ - asset-query│    │ - Get-Volume │    │ - tcpdump    │
│ - asset-list │    │ - PowerShell │    │ - nmap       │
│ - asset-crud │    │ - SSH/WinRM  │    │ - tshark     │
└──────────────┘    └──────────────┘    └──────────────┘
```

## Example Flow

**User Request**: "Give me a report showing the size of all C drives for all assets tagged as win10"

**Generated Plan**:
```json
{
  "steps": [
    {
      "tool": "asset-query",
      "inputs": {
        "filters": {"tags": "win10"},
        "fields": ["ip_address", "hostname"]
      }
    },
    {
      "tool": "Get-Volume",
      "inputs": {
        "target_host": "{{item.ip_address}}",
        "command": "Get-Volume -DriveLetter C"
      }
    }
  ]
}
```

**Execution Flow**:

1. **Stage E receives plan** with 2 steps

2. **Step 1: asset-query**
   - Routes to: `asset-service`
   - Executes: Query for win10 assets
   - Returns: 4 assets with IPs and hostnames
   - Stores: Assets in context for next step

3. **Step 2: Get-Volume**
   - Routes to: `automation-service`
   - Receives: Previous results (4 assets)
   - Detects: Loop over assets (template variable `{{item.ip_address}}`)
   - Expands: 1 step → 4 steps (one per asset)
   - For each asset:
     - Resolves: `{{item.ip_address}}` → actual IP
     - Auto-detects: No credentials → use asset credentials
     - Fetches: Credentials from asset database
     - Executes: PowerShell command via WinRM
   - Returns: 4 results (one per asset)

4. **Stage E aggregates results**
   - Combines all step results
   - Updates execution status
   - Returns to user

## Testing

To test the fix:

```bash
# 1. Restart services
docker compose restart ai-pipeline automation-service

# 2. Send test request via frontend or API
curl -X POST http://localhost:3005/chat \
  -H "Content-Type: application/json" \
  -d '{
    "message": "give me a report showing the size of all C drives for all assets tagged as win10",
    "tenant_id": "default",
    "actor_id": 1
  }'
```

Expected result:
- Step 1 succeeds: Returns 4 assets
- Step 2 succeeds: Returns C drive size for each asset
- Overall status: `completed`

## Benefits

1. **Scalability**: Can handle plans with any number of steps across any services
2. **Maintainability**: Each service focuses on its domain
3. **Reliability**: Failures are isolated to individual steps
4. **Security**: Credentials are managed centrally and securely
5. **Flexibility**: Easy to add new services without changing orchestration logic

## Future Enhancements

1. **Parallel Execution**: Execute independent steps in parallel
2. **Conditional Steps**: Support if/else logic in plans
3. **Error Recovery**: Automatic retry with exponential backoff
4. **Result Caching**: Cache expensive operations
5. **Progress Tracking**: Real-time progress updates for long-running plans