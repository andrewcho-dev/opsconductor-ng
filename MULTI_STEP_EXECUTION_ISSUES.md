# Multi-Step Execution Issues and Fixes

## Problem Summary

User requested: **"give me a report showing the size of all C drives for all assets tagged as win10"**

The AI correctly generated a 2-step plan:
1. **Step 1:** Query assets with tag "win10" using `asset-query` tool
2. **Step 2:** Execute `Get-Volume` PowerShell command on each asset using `Invoke-Command` tool

However, execution failed with error: `❌ Execution failed: None`

## Root Cause Analysis

### Issue #1: Hardcoded Tool Path in Stage E Executor ✅ FIXED

**File:** `/home/opsconductor/opsconductor-ng/pipeline/stages/stage_e/executor.py` (line 216)

**Problem:**
```python
tools_dir = Path("/home/opsconductor/opsconductor-ng/pipeline/config/tools")
```

This hardcoded path is the **host path**, but the code runs inside a Docker container where the path is `/app/pipeline/config/tools`.

**Impact:**
- Tool routing failed to find tool definitions
- All executions defaulted to `automation-service` instead of routing to correct service
- `asset-query` should route to `asset-service` but was sent to `automation-service`

**Fix Applied:**
```python
# Use relative path from current file location to work in both dev and container environments
current_file = Path(__file__)
tools_dir = current_file.parent.parent.parent / "config" / "tools"
```

**Status:** ✅ **FIXED** - Container restarted, routing now works correctly

---

### Issue #2: Missing Template Variable Replacement ❌ NOT FIXED

**File:** `/home/opsconductor/opsconductor-ng/automation-service/main_clean.py`

**Problem:**
The LLM generated step 2 with template variables:
```json
{
  "tool": "Invoke-Command",
  "inputs": {
    "target_hosts": ["{{hostname}}", "{{ip_address}}"],
    "command": "Get-Volume -DriveLetter C | Select-Object Size"
  }
}
```

The automation service has **no logic** to:
1. Recognize template variables like `{{hostname}}`
2. Extract results from previous steps
3. Replace template variables with actual values

**Impact:**
- Template variables are passed as literal strings to the executor
- Commands fail because `{{hostname}}` is not a valid hostname

**Required Fix:**
Add template variable replacement logic in `automation-service/main_clean.py`:

```python
def resolve_template_variables(value: Any, context: Dict[str, Any]) -> Any:
    """
    Recursively resolve template variables in a value using context from previous steps.
    
    Args:
        value: Value that may contain template variables like {{hostname}}
        context: Dictionary of variable values from previous step results
    
    Returns:
        Value with template variables replaced
    """
    if isinstance(value, str):
        # Replace {{variable}} with actual value from context
        import re
        pattern = r'\{\{(\w+)\}\}'
        matches = re.findall(pattern, value)
        for var_name in matches:
            if var_name in context:
                value = value.replace(f'{{{{{var_name}}}}}', str(context[var_name]))
        return value
    elif isinstance(value, list):
        return [resolve_template_variables(item, context) for item in value]
    elif isinstance(value, dict):
        return {k: resolve_template_variables(v, context) for k, v in value.items()}
    else:
        return value
```

**Status:** ❌ **NOT FIXED** - Requires implementation

---

### Issue #3: Missing Step Dependency Resolution ❌ NOT FIXED

**Problem:**
The system has no logic to:
1. Execute step 1 (`asset-query`)
2. Parse the results from step 1
3. Extract relevant fields (hostname, ip_address)
4. Pass those values as context to step 2

**Current Behavior:**
- Steps are executed sequentially
- Each step is independent
- No data flows between steps

**Required Behavior:**
- Step 1 executes and returns: `[{"hostname": "WIN10-PC1", "ip_address": "192.168.50.211"}, ...]`
- Step 2 receives this data as context
- Template variables in step 2 are resolved using step 1 results

**Required Fix:**
Modify `automation-service/main_clean.py` to:

```python
# After executing each step, store results in context
step_context = {}

for i, step in enumerate(steps):
    # ... existing code ...
    
    result = await service.execute_command(cmd_request)
    
    # Store step results in context for next steps
    if result.status == "success" and result.stdout:
        # Parse JSON output if available
        try:
            step_output = json.loads(result.stdout)
            step_context[f"step_{i+1}_output"] = step_output
            
            # If this is asset-query, extract asset list
            if tool_name == "asset-query" and isinstance(step_output, list):
                step_context["assets"] = step_output
        except json.JSONDecodeError:
            # Not JSON, store as raw text
            step_context[f"step_{i+1}_output"] = result.stdout
    
    # Resolve template variables in next step using context
    if i + 1 < len(steps):
        next_step = steps[i + 1]
        next_step["inputs"] = resolve_template_variables(
            next_step["inputs"],
            step_context
        )
```

**Status:** ❌ **NOT FIXED** - Requires implementation

---

### Issue #4: Missing Loop Execution for Multiple Targets ❌ NOT FIXED

**Problem:**
When step 1 returns **multiple assets**, step 2 needs to execute **once for each asset**.

**Current Behavior:**
- Step 2 has `target_hosts: ["{{hostname}}", "{{ip_address}}"]`
- This is treated as a single execution with two invalid hostnames

**Required Behavior:**
- Step 1 returns: `[{"hostname": "WIN10-PC1", "ip": "192.168.50.211"}, {"hostname": "WIN10-PC2", "ip": "192.168.50.212"}]`
- Step 2 should execute **twice**:
  - Execution 1: `target_host: "WIN10-PC1"` (or `192.168.50.211`)
  - Execution 2: `target_host: "WIN10-PC2"` (or `192.168.50.212`)

**Required Fix:**
Add loop detection and expansion logic:

```python
# Detect if step depends on a list from previous step
if "{{" in json.dumps(step.get("inputs", {})):
    # Check if any template variable references a list
    if "assets" in step_context and isinstance(step_context["assets"], list):
        # Expand step into multiple executions
        for asset in step_context["assets"]:
            # Create a copy of the step with variables resolved for this asset
            expanded_step = copy.deepcopy(step)
            expanded_step["inputs"] = resolve_template_variables(
                expanded_step["inputs"],
                asset  # Use individual asset as context
            )
            
            # Execute the expanded step
            result = await service.execute_command(...)
            step_results.append(result)
    else:
        # Single execution with template resolution
        step["inputs"] = resolve_template_variables(step["inputs"], step_context)
        result = await service.execute_command(...)
        step_results.append(result)
```

**Status:** ❌ **NOT FIXED** - Requires implementation

---

### Issue #5: asset-query Tool Not Implemented ❌ NOT FIXED

**Problem:**
The `asset-query` tool is defined in YAML but has no implementation in `asset-service`.

**Impact:**
Even if routing works correctly, the asset-service doesn't know how to execute `asset-query`.

**Required Fix:**
Implement `/execute-plan` endpoint in `asset-service` that handles `asset-query` tool:

```python
@app.post("/execute-plan")
async def execute_plan_from_pipeline(request: PlanExecutionRequest):
    """Execute asset-query plan"""
    steps = request.plan.get("steps", [])
    step_results = []
    
    for step in steps:
        tool_name = step.get("tool")
        
        if tool_name == "asset-query":
            # Extract query parameters
            inputs = step.get("inputs", {})
            filters = inputs.get("filters", {})
            fields = inputs.get("fields", ["hostname", "ip_address"])
            
            # Query assets from database
            assets = await query_assets(filters=filters, fields=fields)
            
            # Return results as JSON
            step_results.append({
                "tool": tool_name,
                "status": "success",
                "stdout": json.dumps(assets),
                "exit_code": 0
            })
        else:
            step_results.append({
                "tool": tool_name,
                "status": "failed",
                "error": f"Unknown tool: {tool_name}"
            })
    
    return {
        "execution_id": request.execution_id,
        "status": "completed",
        "step_results": step_results
    }
```

**Status:** ❌ **NOT FIXED** - Requires implementation

---

## Immediate Workaround

Since issues #2-#5 require significant implementation work, here's a **workaround** for the user:

### Option 1: Manual Two-Step Process
1. First ask: **"list all assets tagged as win10"**
2. Then ask: **"get C drive size from 192.168.50.211"** (for each asset)

### Option 2: Direct Command with Known IPs
If you know the IPs of your Windows 10 machines:
- **"get C drive size from 192.168.50.211, 192.168.50.212, 192.168.50.213"**

### Option 3: Use Asset Service Directly
Query the asset database directly through the UI or API to get the list of Windows 10 assets, then run commands on each.

---

## Long-Term Solution

To fully support multi-step plans with dependencies, we need to implement:

1. ✅ **Tool routing fix** (DONE)
2. ❌ **Template variable resolution** (automation-service)
3. ❌ **Step dependency resolution** (automation-service)
4. ❌ **Loop execution for multiple targets** (automation-service)
5. ❌ **asset-query implementation** (asset-service)

**Estimated Effort:** 2-3 days of development + testing

**Priority:** HIGH - This is a common use case (query assets → operate on them)

---

## Testing Plan

Once all fixes are implemented, test with:

```
give me a report showing the size of all C drives for all assets tagged as win10
```

**Expected Result:**
```
✅ Execution completed successfully!

Step 1: asset-query
Status: completed
Output:
[
  {"hostname": "WIN10-PC1", "ip_address": "192.168.50.211"},
  {"hostname": "WIN10-PC2", "ip_address": "192.168.50.212"}
]

Step 2: Invoke-Command (WIN10-PC1)
Status: completed
Output:
Size: 250GB

Step 2: Invoke-Command (WIN10-PC2)
Status: completed
Output:
Size: 320GB

Total Duration: 8.5s
```

---

## Files Modified

1. ✅ `/home/opsconductor/opsconductor-ng/pipeline/stages/stage_e/executor.py` - Fixed hardcoded tool path

## Files That Need Modification

2. ❌ `/home/opsconductor/opsconductor-ng/automation-service/main_clean.py` - Add template resolution, dependency resolution, loop execution
3. ❌ `/home/opsconductor/opsconductor-ng/asset-service/main.py` - Implement asset-query execution

---

## Related Documentation

- [Impacket Callback Fix](./IMPACKET_GETFILE_FIX.md) - Previous fix for output retrieval
- [Prompt Optimization](./PROMPT_OPTIMIZATION_FIX.md) - Context window optimization