# Multi-Step Execution System with Template Variables

## Overview

The OpsConductor multi-step execution system enables complex automation workflows with:
- **Template Variables**: Dynamic parameter resolution using `{{variable}}` syntax
- **Loop Execution**: Automatic expansion of steps to run across multiple targets
- **Dependency Resolution**: Steps can reference outputs from previous steps
- **Asset Integration**: Seamless integration with asset-query for dynamic target discovery

## Architecture

### Components

1. **ExecutionContext** (`automation-service/execution_context.py`)
   - Manages execution state and variable storage
   - Handles template variable detection and resolution
   - Implements loop detection and step expansion
   - Extracts variables from step results

2. **Automation Service** (`automation-service/main_clean.py`)
   - Executes multi-step plans
   - Integrates ExecutionContext for variable resolution
   - Handles asset-query tool via HTTP calls to asset-service
   - Manages loop execution for multiple targets

3. **Asset Service** (`asset-service/main.py`)
   - Provides asset-query tool for dynamic asset discovery
   - Returns structured asset data for variable extraction

## Template Variable System

### Syntax

Template variables use double curly braces: `{{variable_name}}`

**Supported patterns:**
- Simple variables: `{{hostname}}`
- Array access: `{{hostnames[0]}}`
- Nested access: `{{assets[0].hostname}}`

### Variable Sources

Variables are automatically extracted from step results:

#### Asset-Query Results
When an asset-query step completes, the following variables are automatically available:
- `assets`: Full list of asset objects
- `hostnames`: List of asset hostnames
- `ip_addresses`: List of asset IP addresses
- `asset_count`: Number of assets found

#### Custom Step Results
Each step's result is stored as `step_{index}_result` for manual access.

### Resolution Process

1. **Detection**: ExecutionContext scans step parameters for `{{...}}` patterns
2. **Lookup**: Variables are retrieved from the execution context
3. **Replacement**: Template strings are replaced with actual values
4. **Validation**: Missing variables log warnings but don't crash execution

## Loop Execution

### Automatic Loop Detection

The system automatically detects when a step should be executed in a loop:

**Conditions:**
1. Step parameters contain template variables (e.g., `{{hostname}}`)
2. The parameter name suggests multiple targets (e.g., `target_hosts`)
3. Assets exist in the execution context

**Example:**
```json
{
  "tool": "Invoke-Command",
  "inputs": {
    "target_hosts": ["{{hostname}}"],
    "command": "Get-Volume C"
  }
}
```

### Loop Expansion

When a loop is detected:

1. **Expansion**: Single step definition → N concrete steps (one per asset)
2. **Variable Resolution**: Each iteration gets its own resolved parameters
3. **Metadata Addition**: Loop metadata added to each iteration:
   - `_loop_index`: Current iteration (0-based)
   - `_loop_total`: Total iterations
   - `_loop_item`: Current asset object

4. **Parameter Transformation**:
   - `target_hosts` (plural) → `target_host` (singular)
   - Template variables → Concrete values

**Example Expansion:**

**Input (1 step):**
```json
{
  "tool": "Invoke-Command",
  "inputs": {
    "target_hosts": ["{{hostname}}"],
    "command": "Get-Volume C"
  }
}
```

**Output (4 steps for 4 assets):**
```json
[
  {
    "tool": "Invoke-Command",
    "inputs": {
      "target_host": "192.168.50.211",
      "command": "Get-Volume C"
    },
    "_loop_index": 0,
    "_loop_total": 4,
    "_loop_item": {"id": 21, "hostname": "win10-test02", ...}
  },
  {
    "tool": "Invoke-Command",
    "inputs": {
      "target_host": "192.168.50.212",
      "command": "Get-Volume C"
    },
    "_loop_index": 1,
    "_loop_total": 4,
    "_loop_item": {"id": 22, "hostname": "win10-test03", ...}
  },
  // ... 2 more iterations
]
```

### Execution Strategy

- **Sequential Execution**: Loop iterations execute one after another
- **Partial Success**: Individual iteration failures don't stop the loop
- **Result Aggregation**: Each iteration's result is stored separately

## Complete Workflow Example

### 1. Define Multi-Step Plan

```json
{
  "execution_id": "exec-12345",
  "plan": {
    "name": "Windows Disk Space Check",
    "steps": [
      {
        "tool": "asset-query",
        "inputs": {
          "tags": ["win10"],
          "limit": 100
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
  "tenant_id": "tenant-1",
  "actor_id": "user-1"
}
```

### 2. Execution Flow

**Step 1: Asset Query**
```
→ Call asset-service with tags=["win10"]
→ Receive 4 Windows 10 assets
→ Extract variables:
  - assets: [asset1, asset2, asset3, asset4]
  - hostnames: ["192.168.50.211", "192.168.50.212", "192.168.50.213", "192.168.50.215"]
  - ip_addresses: ["192.168.50.211", "192.168.50.212", "192.168.50.213", "192.168.50.215"]
  - asset_count: 4
```

**Step 2: Loop Detection**
```
→ Detect template variable: {{hostname}}
→ Detect plural parameter: target_hosts
→ Find assets in context: 4 assets
→ Decision: Execute in loop
```

**Step 3: Loop Expansion**
```
→ Expand 1 step → 4 iterations
→ Resolve {{hostname}} for each asset
→ Transform target_hosts → target_host
→ Add loop metadata
```

**Step 4: Execution**
```
Iteration 1/4: Execute on 192.168.50.211
Iteration 2/4: Execute on 192.168.50.212
Iteration 3/4: Execute on 192.168.50.213
Iteration 4/4: Execute on 192.168.50.215
```

### 3. Result Structure

```json
{
  "execution_id": "exec-12345",
  "status": "completed",
  "step_results": [
    {
      "step": 1,
      "tool": "asset-query",
      "status": "success",
      "output": {
        "assets": [...],
        "count": 4
      }
    },
    {
      "step": 2,
      "tool": "Invoke-Command",
      "status": "success",
      "loop_iteration": 1,
      "loop_total": 4,
      "stdout": "Size: 500GB, SizeRemaining: 200GB"
    },
    {
      "step": 2,
      "tool": "Invoke-Command",
      "status": "success",
      "loop_iteration": 2,
      "loop_total": 4,
      "stdout": "Size: 500GB, SizeRemaining: 150GB"
    },
    // ... 2 more iterations
  ]
}
```

## API Reference

### ExecutionContext Methods

#### `__init__(execution_id: str)`
Create a new execution context.

#### `find_template_variables(text: str) -> List[str]`
Find all template variables in a string.

**Example:**
```python
ctx.find_template_variables("Host: {{hostname}}, IP: {{ip_address}}")
# Returns: ["hostname", "ip_address"]
```

#### `resolve_template_string(text: str) -> str`
Resolve all template variables in a string.

**Example:**
```python
ctx.set_variable("hostname", "server01")
ctx.resolve_template_string("Connecting to {{hostname}}")
# Returns: "Connecting to server01"
```

#### `resolve_template_in_dict(data: Dict) -> Dict`
Recursively resolve template variables in a dictionary.

**Example:**
```python
ctx.set_variable("host", "192.168.1.100")
ctx.resolve_template_in_dict({
    "target": "{{host}}",
    "port": 22
})
# Returns: {"target": "192.168.1.100", "port": 22}
```

#### `detect_loop_execution(step: Dict) -> Tuple[bool, Optional[str], Optional[List[Any]]]`
Detect if a step should be executed in a loop.

**Returns:**
- `should_loop`: Boolean indicating if loop execution is needed
- `loop_variable_name`: Name of the variable to loop over (e.g., "hostname")
- `loop_items`: List of items to iterate over

**Example:**
```python
step = {
    "tool": "ping",
    "inputs": {"target_hosts": ["{{hostname}}"]}
}
should_loop, var_name, items = ctx.detect_loop_execution(step)
# Returns: (True, "hostname", ["192.168.1.1", "192.168.1.2", ...])
```

#### `expand_step_for_loop(step: Dict, loop_items: List[Any]) -> List[Dict]`
Expand a single step into multiple iterations.

**Example:**
```python
step = {
    "tool": "ping",
    "inputs": {"target_hosts": ["{{hostname}}"]}
}
expanded = ctx.expand_step_for_loop(step, ["host1", "host2"])
# Returns: [
#   {"tool": "ping", "inputs": {"target_host": "host1"}, "_loop_index": 0, ...},
#   {"tool": "ping", "inputs": {"target_host": "host2"}, "_loop_index": 1, ...}
# ]
```

#### `extract_variables_from_step_result(step_index: int, step_result: Dict)`
Extract variables from a step result.

**Example:**
```python
result = {
    "tool": "asset-query",
    "output": {
        "assets": [{"hostname": "server01", "ip_address": "192.168.1.1"}]
    }
}
ctx.extract_variables_from_step_result(0, result)
# Populates: assets, hostnames, ip_addresses, asset_count
```

## Testing

### Unit Tests

Run comprehensive unit tests:
```bash
python3 test_multistep_execution.py
```

**Test Coverage:**
- Template variable detection
- Variable extraction from asset-query
- Template resolution
- Loop detection
- Step expansion
- Full workflow simulation

### Integration Tests

Run end-to-end integration tests:
```bash
python3 test_e2e_multistep.py
```

**Test Coverage:**
- Service health checks
- Asset-query tool execution
- Multi-step plan execution
- Loop expansion verification

### Verify Loop Execution in Logs

```bash
docker logs opsconductor-automation --tail 100 | grep -E '(Loop|template|🔁)'
```

**Expected Output:**
```
🔁 Loop detected: Executing step 2 for 4 items
🔁 Loop iteration 1/4
🔁 Loop iteration 2/4
🔁 Loop iteration 3/4
🔁 Loop iteration 4/4
```

## Performance Considerations

### Current Implementation

- **Loop Expansion**: Synchronous (happens before execution)
- **Loop Execution**: Sequential (one iteration at a time)
- **Suitable For**: Small to medium asset lists (1-50 assets)

### Future Optimizations

For large-scale deployments (100+ assets):

1. **Parallel Execution**
   - Execute loop iterations concurrently
   - Configurable concurrency limit
   - Resource pooling for connections

2. **Batching**
   - Group assets into batches
   - Execute batches in parallel
   - Aggregate results per batch

3. **Streaming Results**
   - Stream results as iterations complete
   - Don't wait for all iterations to finish
   - Enable real-time monitoring

4. **Caching**
   - Cache asset-query results
   - Reuse connections to same hosts
   - Cache credential lookups

## Error Handling

### Loop Execution Errors

- **Individual Failure**: Loop continues to next iteration
- **Partial Success**: Some iterations succeed, some fail
- **Result Tracking**: Each iteration's status tracked separately

### Template Resolution Errors

- **Missing Variable**: Logs warning, resolves to empty string
- **Invalid Syntax**: Logs error, leaves template unchanged
- **Type Mismatch**: Logs warning, converts to string

### Asset-Query Errors

- **No Assets Found**: Loop not executed, step continues
- **Service Unavailable**: Step fails, execution stops
- **Invalid Query**: Step fails with error message

## Best Practices

### 1. Use Descriptive Variable Names

**Good:**
```json
{"target_hosts": ["{{hostname}}"]}
```

**Bad:**
```json
{"hosts": ["{{h}}"]}
```

### 2. Validate Asset Queries

Always check asset-query results before using in loops:
```json
{
  "steps": [
    {
      "tool": "asset-query",
      "inputs": {"tags": ["production", "web"]}
    },
    {
      "tool": "conditional-check",
      "inputs": {"condition": "{{asset_count}} > 0"}
    },
    {
      "tool": "Invoke-Command",
      "inputs": {"target_hosts": ["{{hostname}}"]}
    }
  ]
}
```

### 3. Use Appropriate Timeouts

For loop execution, set timeouts per iteration:
```json
{
  "tool": "Invoke-Command",
  "inputs": {
    "target_hosts": ["{{hostname}}"],
    "command": "long-running-task",
    "timeout": 600
  }
}
```

### 4. Handle Credentials Securely

Never hardcode credentials in plans:
```json
{
  "tool": "Invoke-Command",
  "inputs": {
    "target_hosts": ["{{hostname}}"],
    "command": "Get-Service",
    "username": "{{vault.windows_admin_user}}",
    "password": "{{vault.windows_admin_pass}}"
  }
}
```

### 5. Monitor Loop Progress

Use logging to track loop execution:
```bash
# Watch loop execution in real-time
docker logs -f opsconductor-automation | grep -E '(Loop|🔁)'
```

## Troubleshooting

### Issue: Template Variables Not Resolved

**Symptoms:**
- Literal `{{variable}}` appears in execution
- "Template variable not found" warnings in logs

**Solutions:**
1. Verify asset-query step executed successfully
2. Check variable extraction in logs
3. Ensure variable names match exactly (case-sensitive)

### Issue: Loop Not Executing

**Symptoms:**
- Single execution instead of multiple
- No "Loop detected" message in logs

**Solutions:**
1. Verify template variables in step parameters
2. Check parameter name is plural (e.g., `target_hosts`)
3. Ensure assets exist in context

### Issue: Loop Iterations Failing

**Symptoms:**
- All iterations show "failed" status
- Same error for each iteration

**Solutions:**
1. Check credentials are provided
2. Verify network connectivity to targets
3. Test command on single host first
4. Check timeout settings

## Future Enhancements

### Planned Features

1. **Conditional Execution**
   - Skip steps based on previous results
   - Branch execution based on conditions

2. **Parallel Loop Execution**
   - Execute iterations concurrently
   - Configurable concurrency limits

3. **Result Aggregation**
   - Combine loop iteration results
   - Statistical analysis of results

4. **Advanced Template Functions**
   - String manipulation: `{{hostname | upper}}`
   - Filtering: `{{assets | filter(status='active')}}`
   - Transformations: `{{ip_addresses | join(',')}}`

5. **Error Recovery**
   - Retry failed iterations
   - Fallback strategies
   - Circuit breakers

6. **Performance Monitoring**
   - Execution time per iteration
   - Resource usage tracking
   - Bottleneck identification

## Contributing

When adding new features to the multi-step execution system:

1. **Update ExecutionContext**: Add new methods to `execution_context.py`
2. **Update Integration**: Modify `main_clean.py` to use new features
3. **Add Tests**: Create unit and integration tests
4. **Update Documentation**: Keep this file current
5. **Log Appropriately**: Use structured logging for debugging

## Support

For issues or questions:
- Check logs: `docker logs opsconductor-automation`
- Run tests: `python3 test_multistep_execution.py`
- Review examples in `test_e2e_multistep.py`