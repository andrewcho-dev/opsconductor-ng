# Chat Wire-Up: End-to-End Execution

## Overview

The Chat Wire-Up system provides intelligent intent detection and routing for natural language commands in the AI Chat interface. It automatically detects user intent and routes requests to the appropriate backend service:

- **Echo Execution** - Simple echo/ping commands
- **Tool Execution** - Operational commands (DNS, HTTP, port checks, etc.)
- **Selector Search** - Natural language tool discovery

## Architecture

```
┌─────────────┐
│   User      │
│   Input     │
└──────┬──────┘
       │
       ▼
┌─────────────────────┐
│ ChatIntentRouter    │
│ (Intent Detection)  │
└──────┬──────────────┘
       │
       ├─────────────────┐─────────────────┐
       ▼                 ▼                 ▼
┌──────────────┐  ┌──────────────┐  ┌──────────────┐
│ exec.echo    │  │ tool.execute │  │selector.search│
│ /ai/execute  │  │/ai/tools/exec│  │/api/selector │
└──────────────┘  └──────────────┘  └──────────────┘
```

## Intent Detection Rules

### 1. Echo Execution (`exec.echo`)

**Triggers:**
- Exact match: `ping` (case-insensitive)
- Prefix match: `please echo this back exactly: <text>`

**Examples:**
```
ping                                    → exec.echo("ping")
PING                                    → exec.echo("ping")
Please echo this back exactly: test     → exec.echo("test")
```

**Endpoint:** `POST /ai/execute`

**Payload:**
```json
{
  "tool": "echo",
  "input": "<text>"
}
```

### 2. Tool Execution (`tool.execute`)

**Triggers:**
- Windows directory listing
- DNS lookup
- TCP port check
- HTTP health check
- Traceroute
- Network ping

#### Windows List Directory

**Pattern:** `(show|list) (directory|contents) of c drive on <host>`

**Examples:**
```
show directory of c drive on 192.168.50.211
list contents of c drive on win-server-01
```

**Tool:** `windows_list_directory`

**Parameters:**
```json
{
  "host": "192.168.50.211",
  "path": "C:\\",
  "username": "<prompted>",
  "password": "<prompted>"
}
```

#### DNS Lookup

**Pattern:** `dns (lookup|resolve) <domain>`

**Examples:**
```
dns lookup example.com
dns resolve google.com
```

**Tool:** `dns_lookup`

**Parameters:**
```json
{
  "domain": "example.com",
  "record_type": "A"
}
```

#### TCP Port Check

**Pattern:** `check port <port> on <host>`

**Examples:**
```
check port 80 on 127.0.0.1
check port 443 on example.com
```

**Tool:** `tcp_port_check`

**Parameters:**
```json
{
  "host": "127.0.0.1",
  "port": 80
}
```

#### HTTP Check

**Pattern:** `(http check|fetch|get|head) <url>`

**Examples:**
```
http check https://example.com
fetch http://localhost:3000
get https://api.example.com/health
```

**Tool:** `http_check`

**Parameters:**
```json
{
  "url": "https://example.com",
  "method": "GET"
}
```

#### Traceroute

**Pattern:** `traceroute <host>`

**Examples:**
```
traceroute google.com
traceroute 8.8.8.8
```

**Tool:** `traceroute`

**Parameters:**
```json
{
  "host": "google.com"
}
```

#### Network Ping

**Pattern:** `ping <host>`

**Examples:**
```
ping 8.8.8.8
ping google.com
```

**Tool:** `shell_ping`

**Parameters:**
```json
{
  "host": "8.8.8.8"
}
```

### 3. Selector Search (`selector.search`)

**Triggers:**
- Messages containing "tool" or "tools"
- Any message that doesn't match echo or tool execution patterns

**Examples:**
```
What tools can help troubleshoot DNS issues?
Show me network diagnostics tools for Windows
Find three tools for packet capture
```

**Endpoint:** `GET /api/selector/search`

**Query Parameters:**
- `query` - The search query
- `k` - Number of results (default: 3)
- `platform` - Optional platform filter (windows|linux)

#### Fallback to Tool Registry (PR #8)

When the Selector returns 0 results, the system automatically falls back to the Tool Registry:

**Flow:**
```
1. User Query → Selector Search
2. If Selector returns 0 results:
   a. Call GET /ai/tools/list (with platform filter if specified)
   b. Extract keywords from query (words > 2 chars)
   c. Filter tools by keywords in name/description/tags
   d. Convert to Selector format
   e. Return filtered results
3. Else: Return Selector results
```

**Example:**
```
User: "What tools can help troubleshoot DNS issues?"

Selector: 0 results (no embeddings match)
  ↓
Fallback to Tool Registry
  ↓
Keywords: ["tools", "help", "troubleshoot", "dns", "issues"]
  ↓
Filtered: dns_lookup, shell_ping, traceroute
  ↓
Return: 3 tools as Selector format
```

**Benefits:**
- Users always get useful suggestions
- No "No tools found" dead ends
- Leverages both semantic search (Selector) and keyword matching (Registry)
- Maintains consistent UI rendering

## Feature Flags

### Environment Variables

```bash
# Enable/disable chat direct execution
REACT_APP_CHAT_DIRECT_EXEC=true  # Default: true

# Automation service URL
REACT_APP_AUTOMATION_SERVICE_URL=http://localhost:3000

# Selector API base path
REACT_APP_SELECTOR_BASE_PATH=/api/selector
```

### Runtime Check

```typescript
import chatIntentRouter from './services/chatIntentRouter';

if (chatIntentRouter.isChatDirectExecEnabled()) {
  // Use direct execution
} else {
  // Fall back to legacy AI pipeline
}
```

## API Endpoints

### Echo Execution

**Endpoint:** `POST /ai/execute`

**Request:**
```json
{
  "tool": "echo",
  "input": "ping"
}
```

**Response:**
```json
{
  "success": true,
  "output": "pong",
  "error": null,
  "trace_id": "abc-123",
  "duration_ms": 5.2,
  "tool": "echo"
}
```

### Tool Execution

**Endpoint:** `POST /ai/tools/execute`

**Request:**
```json
{
  "name": "dns_lookup",
  "params": {
    "domain": "example.com",
    "record_type": "A"
  }
}
```

**Response:**
```json
{
  "success": true,
  "tool": "dns_lookup",
  "output": {
    "domain": "example.com",
    "records": ["93.184.216.34"]
  },
  "error": null,
  "trace_id": "def-456",
  "duration_ms": 125.8,
  "exit_code": 0
}
```

### Selector Search

**Endpoint:** `GET /api/selector/search?query=<query>&k=3&platform=<platform>`

**Response:**
```json
{
  "tools": [
    {
      "name": "nslookup",
      "description": "DNS lookup utility",
      "platform": "windows",
      "category": "network"
    }
  ],
  "query": "DNS troubleshooting",
  "count": 1,
  "trace_id": "ghi-789"
}
```

## Frontend Integration

### ChatIntentRouter Service

Located at: `frontend/src/services/chatIntentRouter.ts`

**Key Functions:**

```typescript
// Analyze user message and determine intent
analyzeIntent(message: string): ChatIntentResult

// Execute echo tool
executeEcho(input: string, traceId?: string): Promise<ExecResponse>

// Execute a tool
executeTool(toolName: string, params: Record<string, any>, traceId?: string): Promise<ToolExecutionResponse>

// Search for tools
searchTools(query: string, platform?: 'windows' | 'linux', k?: number, traceId?: string): Promise<SelectorResponse>

// Main router function
routeChatMessage(message: string): Promise<RouterResult>
```

### AIChat Component

Located at: `frontend/src/components/AIChat.tsx`

**Message Types:**

```typescript
interface Message {
  id: string;
  content: string;
  sender: 'user' | 'ai';
  timestamp: Date;
  intent?: 'exec.echo' | 'tool.execute' | 'selector.search' | 'legacy';
  tools?: SelectorTool[];
  toolResult?: any;
  toolName?: string;
  traceId?: string;
}
```

**Rendering:**

- **Echo results** - Displayed as plain text
- **Tool results** - Displayed in a formatted code block with JSON output
- **Selector results** - Displayed as cards with tool name, description, and platform badge

## Telemetry & Logging

### Console Logs

All operations log to the browser console with structured format:

```
[ChatExec] Executing echo tool: input="ping", trace_id=abc-123
[ChatExec] Echo completed: duration=5.20ms, trace_id=abc-123

[ChatTool] Executing tool: name="dns_lookup", params={"domain":"example.com"}, trace_id=def-456
[ChatTool] Tool execution completed: duration=125.80ms, success=true, trace_id=def-456

[ChatSelector] Searching tools: query="DNS troubleshooting", platform=any, k=3, trace_id=ghi-789
[ChatSelector] Search completed: duration=45.30ms, count=3, trace_id=ghi-789
```

### Trace ID Propagation

Every request includes an `X-Trace-Id` header for end-to-end tracing:

```
Frontend → Kong → Automation Service → AI Pipeline → Tool Runner
   │                                                        │
   └────────────────── X-Trace-Id: abc-123 ────────────────┘
```

## Troubleshooting

### Issue: Intent not detected correctly

**Symptoms:** Message routed to wrong service

**Solutions:**
1. Check regex patterns in `analyzeIntent()` function
2. Verify message format matches expected pattern
3. Check console logs for intent detection result

### Issue: Tool execution fails

**Symptoms:** Error message in chat

**Solutions:**
1. Check tool is registered: `GET /ai/tools/list`
2. Verify parameters match tool specification
3. Check backend logs for detailed error
4. Verify trace ID in console logs

### Issue: Selector search returns no results

**Symptoms:** "No tools found" message

**Solutions:**
1. Check selector service is running
2. Verify embeddings are loaded
3. Try broader search query
4. Check platform filter is correct

### Issue: Feature flag not working

**Symptoms:** Direct execution not enabled

**Solutions:**
1. Check `.env` file has `REACT_APP_CHAT_DIRECT_EXEC=true`
2. Restart frontend dev server after changing `.env`
3. Clear browser cache
4. Check console for feature flag status

### Issue: Network errors

**Symptoms:** "Connection refused" or timeout errors

**Solutions:**
1. Verify automation service is running on port 3000
2. Check Kong gateway is running on port 3100
3. Verify CORS configuration
4. Check firewall rules

## Testing

### Unit Tests

Located at: `frontend/src/services/chatIntentRouter.test.ts`

**Run tests:**
```bash
cd frontend
npm test chatIntentRouter
```

**Coverage:**
- Intent detection for all patterns
- Echo execution with mocked fetch
- Tool execution with mocked fetch
- Selector search with mocked fetch
- Error handling

### Integration Tests

Located at: `scripts/test_tools_integration.sh`

**Run tests:**
```bash
./scripts/test_tools_integration.sh
```

**Coverage:**
- Full stack: Kong → Automation → AI Pipeline
- Tool listing
- Tool execution (all 5 network tools)
- Error handling

### Manual Testing

**Test Scenarios:**

1. **Echo Test**
   ```
   Input: ping
   Expected: "pong" response in <2s
   ```

2. **Exact Echo Test**
   ```
   Input: Please echo this back exactly: OpsConductor is live
   Expected: "OpsConductor is live" response
   ```

3. **Tool Discovery Test**
   ```
   Input: What tools can help troubleshoot DNS issues?
   Expected: 2-5 tool cards with descriptions
   ```

4. **Port Check Test**
   ```
   Input: check port 80 on 127.0.0.1
   Expected: Tool execution result with connectivity status
   ```

5. **Windows Directory Test**
   ```
   Input: show me the directory of the c drive on 192.168.50.211
   Expected: Tool execution (may require credentials)
   ```

## Performance Targets

| Operation | Target | Actual |
|-----------|--------|--------|
| Echo | < 2s | ~5ms |
| DNS Lookup | < 2s | ~350ms |
| HTTP Check | < 2s | ~325ms |
| TCP Port Check | < 2s | ~9ms |
| Ping | < 2s | ~1000ms |
| Selector Search | < 2s | ~50ms |

## Security Considerations

### Credential Handling

- Windows tools requiring credentials should prompt user
- Passwords never logged or stored
- Redaction patterns applied to all tool output

### Input Validation

- All parameters validated before execution
- Regex patterns prevent injection attacks
- Tool runner enforces parameter types and ranges

### Output Sanitization

- Tool output truncated to max size (16KB default)
- Sensitive data redacted using patterns
- Exit codes checked for anomalies

## Future Enhancements

### Planned Features

1. **Tool Palette UI** - Visual tool browser with parameter forms
2. **Credential Manager** - Secure storage for Windows credentials
3. **History & Favorites** - Save frequently used commands
4. **Multi-step Workflows** - Chain multiple tools together
5. **Scheduled Execution** - Run tools on a schedule
6. **Result Export** - Download tool results as CSV/JSON

### Additional Tools

1. **Database Tools** - SQL query, connection test
2. **Cloud Tools** - AWS/Azure/GCP resource checks
3. **Security Tools** - SSL cert check, vulnerability scan
4. **Container Tools** - Docker/K8s status checks

## References

- [Tool Registry Documentation](./TOOLS_REGISTRY.md)
- [Windows WinRM Setup](./TOOLS_WINDOWS.md)
- [API Documentation](./API.md)
- [Integration Status](../INTEGRATION_STATUS.md)