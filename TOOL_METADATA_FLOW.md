# Tool Metadata Flow - Complete Architecture

## Problem Statement
The automation service needs to know which tools require credentials for multi-machine execution. Previously, we tried to import the tool registry directly into the automation service, but this failed due to dependency conflicts (the registry imports LLM clients and other pipeline-specific modules).

## Solution: Metadata Enrichment at Planning Time

Instead of the automation service trying to look up tool metadata, **the planner enriches execution steps with tool metadata when creating the plan**. This follows the principle that all information needed for execution should be determined during planning, not during execution.

## Architecture Flow

```
┌─────────────────────────────────────────────────────────────────┐
│ 1. STAGE B (Selector)                                           │
│    - Selects tools from registry                                │
│    - Tools have execution metadata defined                      │
└────────────────────┬────────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────────┐
│ 2. STAGE C (Planner)                                            │
│    - Creates execution steps from LLM response                  │
│    - **ENRICHES each step with tool metadata from registry**    │
│    - Adds: requires_credentials, execution_location, etc.       │
└────────────────────┬────────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────────┐
│ 3. STAGE E (Executor)                                           │
│    - Routes execution to automation service                     │
│    - Passes enriched plan with metadata                         │
└────────────────────┬────────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────────┐
│ 4. AUTOMATION SERVICE                                           │
│    - Receives plan with enriched steps                          │
│    - Uses metadata from plan (no registry lookup needed)        │
│    - Resolves credentials based on requires_credentials flag    │
│    - Executes commands on target machines                       │
└─────────────────────────────────────────────────────────────────┘
```

## Implementation Details

### 1. ExecutionStep Schema Enhancement
**File:** `pipeline/schemas/plan_v1.py`

Added fields to ExecutionStep:
```python
class ExecutionStep(BaseModel):
    # ... existing fields ...
    
    # Tool execution metadata (enriched from tool registry)
    requires_credentials: bool = Field(default=False)
    execution_location: str = Field(default="automation-service")
    tool_metadata: Optional[Dict[str, Any]] = Field(default=None)
```

### 2. Planner Enrichment
**File:** `pipeline/stages/stage_c/planner.py`

Added method to enrich steps:
```python
def _enrich_step_with_tool_metadata(self, step, selection: SelectionV1):
    """
    Enrich execution step with tool metadata from the tool registry.
    This ensures the automation service has all the information it needs.
    """
    from ..stage_b.windows_tools_registry import WINDOWS_TOOLS_REGISTRY
    
    tool_registry = {tool.name: tool for tool in WINDOWS_TOOLS_REGISTRY}
    tool_def = tool_registry.get(step.tool)
    
    if tool_def and tool_def.execution:
        step.requires_credentials = tool_def.execution.get("requires_credentials", False)
        step.execution_location = tool_def.execution.get("execution_location", "automation-service")
        step.tool_metadata = tool_def.execution
```

Called after creating each step:
```python
for idx, step_data in enumerate(steps_data):
    step = ExecutionStep(...)
    
    # Enrich step with tool metadata from registry
    self._enrich_step_with_tool_metadata(step, selection)
    
    steps.append(step)
```

### 3. Automation Service Usage
**File:** `automation-service/main_clean.py`

Extract metadata from step:
```python
tool_definition = {
    "tool_name": tool_name,
    "platform": step.get("platform", ""),
    "category": step.get("category", ""),
    # Use metadata from the plan (enriched by planner)
    "requires_credentials": step.get("requires_credentials", False),
    "execution_location": step.get("execution_location", "automation-service"),
    "tool_metadata": step.get("tool_metadata", {})
}
```

### 4. Unified Executor Priority
**File:** `automation-service/unified_executor.py`

Updated to check metadata in priority order:
```python
def parse_execution_config(self, tool_definition: Dict[str, Any]) -> ExecutionConfig:
    """
    Priority order:
    1. Check for simplified metadata from plan (requires_credentials, tool_metadata)
    2. Check for full execution metadata structure
    3. Fall back to inference from platform/category/name
    """
    
    # PRIORITY 1: Use metadata from plan (enriched by planner)
    if "requires_credentials" in tool_definition or "tool_metadata" in tool_definition:
        # Use the metadata provided by the planner
        ...
    
    # PRIORITY 2: Check for full execution metadata structure
    elif tool_definition.get("execution"):
        ...
    
    # PRIORITY 3: Fall back to inference (LAST RESORT)
    else:
        return self._infer_execution_config(tool_definition)
```

## Benefits

1. **Separation of Concerns**: Planning determines what to execute, execution service just executes
2. **No Dependency Conflicts**: Automation service doesn't need to import pipeline modules
3. **Single Source of Truth**: Tool registry is the authoritative source, enriched once at planning time
4. **Backward Compatible**: Falls back to inference if metadata not available
5. **Extensible**: Easy to add more metadata fields in the future

## Example Flow

### Tool Definition (Stage B Registry)
```python
Tool(
    name="windows-filesystem-manager",
    description="Manage Windows filesystem operations",
    execution={
        "requires_credentials": True,
        "execution_location": "automation-service",
        "connection": {
            "type": "powershell",
            "requires_credentials": True,
            "requires_target_host": True
        },
        ...
    }
)
```

### Enriched Step (Stage C Output)
```json
{
  "id": "step_abc123",
  "tool": "windows-filesystem-manager",
  "inputs": {
    "path": "C:\\Temp",
    "operation": "list"
  },
  "requires_credentials": true,
  "execution_location": "automation-service",
  "tool_metadata": {
    "requires_credentials": true,
    "connection": {
      "type": "powershell",
      "requires_credentials": true,
      "requires_target_host": true
    }
  }
}
```

### Automation Service Execution
```python
# Extract metadata from step (no registry lookup needed!)
requires_credentials = step.get("requires_credentials", False)

if requires_credentials:
    # Resolve credentials for each target machine
    credentials = await resolve_credentials(target_host)
    # Execute with credentials
```

## Testing

To verify the solution works:

1. **Check planner enrichment**: Look for log message "✅ Enriched step 'step_xxx' with tool metadata"
2. **Check automation service**: Look for log message "✅ Using tool metadata from plan (enriched by planner)"
3. **Verify credential resolution**: Check that credentials are fetched for Windows tools
4. **Test multi-machine execution**: Ensure commands execute on all target machines with proper credentials

## Future Enhancements

1. Add more metadata fields (timeout, retry policy, etc.)
2. Support for tool-specific credential types (API keys, certificates, etc.)
3. Validation of metadata completeness at planning time
4. Metadata versioning for backward compatibility