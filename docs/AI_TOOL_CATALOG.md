# AI Tool Catalog - System Coherence Documentation

## Overview

The AI Tool Catalog provides a unified, hot-reloadable registry of tools available for AI chat execution. This system ensures that tools are always present, discoverable, and executable without service restarts.

## Architecture

### Components

1. **Tool Registry v2** (`automation-service/tool_registry.py`)
   - Single source of truth for all AI tools
   - Merges built-in code-defined tools with YAML catalog tools
   - Supports hot-reload without service restart
   - Emits Prometheus metrics

2. **Tool Runner v2** (`automation-service/tool_runner.py`)
   - Unified execution engine for local and pipeline tools
   - Routes execution based on tool source (local vs pipeline)
   - Applies asset intelligence (auto-resolve connection profiles and credentials)
   - Returns consistent response format

3. **Tool Router v2** (`automation-service/routes/tools.py`)
   - REST API for tool listing, execution, and reload
   - Integrates with registry and runner
   - Handles asset-aware execution server-side

4. **Chat Intent Router** (`frontend/src/services/chatIntentRouter.ts`)
   - Maps natural language queries to tool executions
   - Supports direct execution patterns
   - Falls back to selector search for complex queries

## Configuration

### Environment Variables

```bash
# Tool catalog directories (colon-separated)
AI_TOOL_CATALOG_DIRS="/workspace/automation-service/tools/catalog:/workspace/tools/catalog"

# Default if not set:
# /workspace/automation-service/tools/catalog:/workspace/tools/catalog
```

### Catalog Search Paths

The registry scans the following directories in order:
1. `/workspace/automation-service/tools/catalog` (service-specific tools)
2. `/workspace/tools/catalog` (shared tools)

**Deduplication**: If a tool with the same name exists in multiple directories, the later path wins (with a WARNING log).

## Tool Definition Format

### YAML Tool Definition

```yaml
name: my_tool
display_name: My Tool
description: Description of what the tool does
category: network  # network, system, database, asset, etc.
platform: cross-platform  # windows, linux, cross-platform
version: 1.0.0
source: pipeline  # local or pipeline

parameters:
  - name: param1
    type: string
    description: Parameter description
    required: true
  
  - name: param2
    type: integer
    description: Optional parameter
    required: false
    default: 10

timeout_seconds: 30
requires_admin: false

tags:
  - tag1
  - tag2

examples:
  - description: "Example usage"
    parameters:
      param1: "value1"
```

### Tool Source

- **`local`**: Tool executes directly in automation-service (fast, no network hop)
- **`pipeline`**: Tool executes via ai-pipeline service (for complex tools)

### Built-in Tools

The following tools are always available (code-defined):

1. **dns_lookup** - DNS lookup for a domain
2. **tcp_port_check** - Check if a TCP port is open
3. **http_check** - Check HTTP/HTTPS endpoint availability
4. **traceroute** - Trace network route to a host
5. **shell_ping** - Ping a host to check connectivity
6. **windows_list_directory** - List directory contents on Windows host

## Required Tools

The registry MUST contain these tools (hard requirement):

1. **asset_count** - Count assets matching filters
2. **asset_search** - Search and list assets
3. **windows_list_directory** - List Windows directory contents

If any required tool is missing, an ERROR is logged but the service continues (with the built-in version if available).

## API Endpoints

### GET /ai/tools/list

List all available tools with optional filtering.

**Query Parameters:**
- `platform` (optional): Filter by platform (windows, linux, cross-platform)
- `category` (optional): Filter by category (network, system, asset, etc.)
- `tags` (optional): Comma-separated tags (not yet implemented)

**Response:**
```json
{
  "success": true,
  "tools": [
    {
      "name": "asset_count",
      "display_name": "Asset Count",
      "description": "Count assets in inventory",
      "category": "asset",
      "platform": "cross-platform",
      "source": "local",
      "parameters": [...]
    }
  ],
  "total": 10,
  "filters": {
    "platform": null,
    "category": null,
    "tags": null
  }
}
```

### POST /ai/tools/reload

Reload tool registry from catalog directories (hot-reload).

**Response:**
```json
{
  "success": true,
  "count": 10,
  "tools": ["asset_count", "asset_search", ...],
  "missing_required": [],
  "catalog_dirs": [
    "/workspace/automation-service/tools/catalog",
    "/workspace/tools/catalog"
  ]
}
```

### POST /ai/tools/execute

Execute a tool with parameters.

**Request:**
```json
{
  "name": "asset_count",
  "params": {
    "os": "Windows 10"
  },
  "trace_id": "optional-trace-id"
}
```

**Response (Success):**
```json
{
  "success": true,
  "tool": "asset_count",
  "output": "42",
  "error": null,
  "duration_ms": 45.23,
  "trace_id": "trace-id",
  "timestamp": "2024-01-15T10:30:00Z",
  "exit_code": 0,
  "truncated": false,
  "redacted": false
}
```

**Response (Missing Credentials):**
```json
{
  "success": false,
  "tool": "windows_list_directory",
  "output": null,
  "error": "missing_credentials",
  "duration_ms": 12.34,
  "trace_id": "trace-id",
  "timestamp": "2024-01-15T10:30:00Z"
}
```

## Asset Intelligence

For asset-aware tools (windows_list_directory), the system automatically:

1. **Resolves connection profile** from asset database:
   - WinRM port (default: 5985)
   - SSL settings (default: false)
   - Windows domain (if applicable)

2. **Fetches credentials server-side**:
   - Username
   - Password (NEVER sent to browser)
   - Domain (if applicable)

3. **Merges parameters** before execution

4. **Returns structured error** if credentials not found:
   - Error code: `missing_credentials`
   - Frontend can display appropriate message

## Chat Intent Patterns

The frontend chat automatically routes these patterns to tool execution:

1. **"ping"** → `echo` tool
2. **"please echo this back exactly: <text>"** → `echo` tool
3. **"how many <os> os assets do we have?"** → `asset_count` tool
4. **"show directory of the c drive on <host>"** → `windows_list_directory` tool
5. **"dns lookup <domain>"** → `dns_lookup` tool
6. **"check port <port> on <host>"** → `tcp_port_check` tool
7. **"http check <url>"** → `http_check` tool
8. **"traceroute <host>"** → `traceroute` tool
9. **"ping <host>"** → `shell_ping` tool

All other queries fall back to selector search.

## Adding New Tools

### Step 1: Create YAML Definition

Create a new YAML file in `/workspace/tools/catalog/`:

```bash
cat > /workspace/tools/catalog/my_new_tool.yaml <<EOF
name: my_new_tool
display_name: My New Tool
description: Does something useful
category: system
platform: cross-platform
version: 1.0.0
source: pipeline

parameters:
  - name: target
    type: string
    description: Target host or resource
    required: true

timeout_seconds: 30
requires_admin: false

tags:
  - custom
  - utility
EOF
```

### Step 2: Trigger Hot-Reload

```bash
curl -X POST http://localhost:8010/ai/tools/reload
```

### Step 3: Verify Tool is Loaded

```bash
curl http://localhost:8010/ai/tools/list | grep my_new_tool
```

### Step 4: Test Execution

```bash
curl -X POST http://localhost:8010/ai/tools/execute \
  -H "Content-Type: application/json" \
  -d '{"name":"my_new_tool","params":{"target":"example.com"}}'
```

## Observability

### Logs

The registry emits INFO-level logs on startup and reload:

```
[ToolRegistry] Initialized with catalog dirs: ['/workspace/automation-service/tools/catalog', '/workspace/tools/catalog']
[ToolRegistry] Scanning catalog directory: /workspace/tools/catalog
[ToolRegistry] Loaded 8 YAML tools
[ToolRegistry] Registry loaded with 14 tools: ['asset_count', 'asset_search', 'dns_lookup', ...]
```

### Prometheus Metrics

- `ai_tools_loaded_total` - Total number of tools loaded into registry
- `ai_tools_reload_total` - Total number of registry reload operations
- `ai_tools_reload_errors_total` - Total number of registry reload errors
- `ai_tools_count` - Current number of tools in registry (gauge)

## Troubleshooting

### Tool Not Found

**Symptom**: Tool execution returns "Tool not found: <name>"

**Solutions**:
1. Check if tool exists in catalog directory:
   ```bash
   ls -la /workspace/tools/catalog/
   ```

2. Verify YAML syntax is valid:
   ```bash
   cat /workspace/tools/catalog/my_tool.yaml
   ```

3. Check registry logs for errors:
   ```bash
   docker logs automation-service 2>&1 | grep ToolRegistry
   ```

4. Trigger manual reload:
   ```bash
   curl -X POST http://localhost:8010/ai/tools/reload
   ```

### Tool Execution Fails

**Symptom**: Tool execution returns error

**Solutions**:
1. Check tool definition has correct `source` field
2. For `pipeline` tools, verify ai-pipeline is running
3. For `local` tools, check if implementation exists in tool_runner.py
4. Check trace ID in logs for detailed error

### Missing Required Tools

**Symptom**: ERROR log: "Required tool '<name>' not found in registry!"

**Solutions**:
1. Verify YAML files exist in catalog directories
2. Check YAML syntax is valid
3. Ensure catalog directories are mounted correctly in Docker
4. Trigger manual reload

### Hot-Reload Not Working

**Symptom**: New tools don't appear after adding YAML file

**Solutions**:
1. Verify file is in correct catalog directory
2. Check file has `.yaml` or `.yml` extension
3. Trigger manual reload via API
4. Check registry logs for errors
5. Verify catalog directory is writable

## Best Practices

1. **Use descriptive tool names**: Use snake_case, be specific
2. **Provide clear descriptions**: Help users understand what the tool does
3. **Set appropriate timeouts**: Balance between functionality and responsiveness
4. **Use sensible defaults**: Make parameters optional when possible
5. **Tag appropriately**: Use tags for discoverability
6. **Test before deploying**: Use hot-reload to test in development
7. **Document examples**: Provide usage examples in YAML
8. **Choose correct source**: Use `local` for simple tools, `pipeline` for complex ones

## Security Considerations

1. **Credentials never exposed**: Passwords are fetched server-side only
2. **Parameter validation**: All parameters are validated before execution
3. **Timeout enforcement**: All tools have maximum execution time
4. **Audit logging**: All executions are logged with trace IDs
5. **Redaction**: Secrets are redacted from logs automatically

## Performance

- **Tool list**: <10ms (in-memory lookup)
- **Tool reload**: <100ms (filesystem scan + YAML parsing)
- **Local tool execution**: <50ms (direct execution)
- **Pipeline tool execution**: <500ms (network hop + execution)
- **Asset intelligence**: <100ms (database lookup + credential fetch)

## Future Enhancements

1. **Tool versioning**: Support multiple versions of the same tool
2. **Tool dependencies**: Define dependencies between tools
3. **Tool permissions**: Role-based access control for tools
4. **Tool metrics**: Per-tool execution metrics
5. **Tool validation**: Validate tool definitions on load
6. **Tool testing**: Automated testing framework for tools
7. **Tool marketplace**: Share tools across organizations