# Chat Direct Execution - Feature Documentation

## Overview

The Chat Direct Execution feature replaces the legacy "canned response" autoresponder with direct calls to real backend services. This enables the chat interface to provide immediate, actionable results for common operations.

## Features

### 1. Echo Execution
Direct execution of the echo tool for testing and verification.

**Supported Patterns:**
- `ping` → Returns `pong`
- `Please echo this back exactly: <text>` → Returns `<text>` verbatim

**Example:**
```
User: ping
AI: pong
```

```
User: Please echo this back exactly: OpsConductor v1.1.0
AI: OpsConductor v1.1.0
```

### 2. Tool Selector Search
Natural language search for tools with automatic platform detection.

**Supported Patterns:**
- General queries: "Find tools for DNS troubleshooting"
- Windows-specific: "List packet capture utilities for Windows"
- Linux-specific: "Show network diagnostics tools for Linux"

**Example:**
```
User: Find three tools that can help troubleshoot DNS problems
AI: Found 3 tools matching your query:
    [Tool cards displayed with name, description, platform]
```

## Configuration

### Environment Variables

Add these to your `.env` file:

```bash
# Enable/disable chat direct execution (default: true)
REACT_APP_CHAT_DIRECT_EXEC=true

# Base URL for automation service (Kong gateway or direct)
REACT_APP_AUTOMATION_SERVICE_URL=http://localhost:3000

# Selector API base path
REACT_APP_SELECTOR_BASE_PATH=/api/selector
```

### Feature Flag

The feature can be toggled via `REACT_APP_CHAT_DIRECT_EXEC`:
- `true` (default): Use direct execution
- `false`: Fall back to legacy AI Pipeline behavior

## Architecture

### Components

1. **ChatIntentRouter** (`src/services/chatIntentRouter.ts`)
   - Analyzes user messages to determine intent
   - Routes to appropriate backend service
   - Handles responses and errors

2. **AIChat Component** (`src/components/AIChat.tsx`)
   - Integrates ChatIntentRouter into message handling
   - Renders tool cards for selector results
   - Displays trace IDs for debugging

### Intent Detection

```typescript
analyzeIntent(message: string): ChatIntentResult
```

**Logic:**
1. Exact match "ping" (case-insensitive) → `exec.echo`
2. Starts with "Please echo this back exactly:" → `exec.echo`
3. Contains "windows" → `selector.search` with `platform=windows`
4. Contains "linux" → `selector.search` with `platform=linux`
5. Default → `selector.search` with no platform filter

### API Endpoints

#### Echo Execution
```
POST {AUTOMATION_SERVICE_URL}/ai/execute
Content-Type: application/json
X-Trace-Id: <uuid>

{
  "tool": "echo",
  "input": "<user_input>"
}
```

**Response:**
```json
{
  "success": true,
  "output": "pong",
  "error": null,
  "trace_id": "abc-123",
  "duration_ms": 5.5,
  "tool": "echo"
}
```

#### Tool Selector Search
```
GET {AUTOMATION_SERVICE_URL}/api/selector/search?query=<query>&platform=<platform>&k=3
X-Trace-Id: <uuid>
```

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
  "query": "DNS tools",
  "count": 1
}
```

## Telemetry

### Console Logging

All operations log to console with structured format:

**Echo Execution:**
```
[ChatExec] Executing echo tool: input="ping", trace_id=abc-123
[ChatExec] Echo completed: duration=5.50ms, trace_id=abc-123
```

**Selector Search:**
```
[ChatSelector] Searching tools: query="DNS tools", platform=any, k=3, trace_id=def-456
[ChatSelector] Search completed: duration=125.30ms, count=3, trace_id=def-456
```

### Trace ID Propagation

Every request includes a unique trace ID:
- Generated using UUID v4
- Sent via `X-Trace-Id` header
- Displayed in UI for debugging
- Logged in console output

## UI Components

### Tool Cards

When selector search returns results, tools are displayed as cards:

```
┌─────────────────────────────────────┐
│ nslookup              [windows]     │
│ DNS lookup utility for Windows      │
└─────────────────────────────────────┘
```

**Features:**
- Tool name (bold)
- Platform badge (color-coded: blue=Windows, green=Linux)
- Description text
- Clean, card-based layout

### Trace ID Display

For debugging, trace IDs are shown below messages:
```
trace: abc-123-def-456-ghi-789
```

## Testing

### Unit Tests

Run tests with:
```bash
npm test chatIntentRouter.test.ts
```

**Test Coverage:**
- Intent detection (ping, echo prefix, platform detection)
- Echo execution (success, errors, network failures)
- Selector search (query params, platform filter, empty results)

### Manual Testing

#### Test Case 1: Ping
```
Input: ping
Expected: "pong" (< 2s response time)
```

#### Test Case 2: Exact Echo
```
Input: Please echo this back exactly: OpsConductor walking skeleton v1.1.0
Expected: "OpsConductor walking skeleton v1.1.0" (exact match)
```

#### Test Case 3: DNS Tools
```
Input: Find three tools that can help troubleshoot DNS problems
Expected: 2-5 tool cards with DNS-related tools
```

#### Test Case 4: Windows Tools
```
Input: List two packet capture utilities for Windows
Expected: Tool cards with platform=windows badge
```

#### Test Case 5: Linux Tools
```
Input: Show me network diagnostics tools for Linux
Expected: Tool cards with platform=linux badge
```

## Error Handling

### Network Errors
- Caught and logged to console
- User-friendly error message displayed
- Trace ID preserved for debugging

### API Errors
- HTTP status codes handled gracefully
- Error messages extracted from response
- Fallback to generic error message

### Empty Results
- Selector search with no results shows: "No tools found matching your query."
- Clear, actionable message for users

## Performance

### Target Metrics
- Echo execution: < 50ms (typical: 5-10ms)
- Selector search: < 500ms (typical: 100-200ms)
- Total response time: < 2s

### Optimization
- Direct HTTP calls (no streaming overhead)
- Minimal payload sizes
- Efficient intent detection (regex-free)

## Rollback

To disable the feature and revert to legacy behavior:

```bash
# In .env file
REACT_APP_CHAT_DIRECT_EXEC=false
```

Or remove the environment variable entirely (defaults to true).

## Future Enhancements

### Planned Features
1. Additional tool execution (beyond echo)
2. Multi-tool workflows
3. Caching for selector results
4. User preferences for platform defaults
5. Advanced intent detection (ML-based)

### API Extensions
1. Batch tool search
2. Tool favorites/bookmarks
3. Usage analytics
4. Personalized recommendations

## Troubleshooting

### Issue: "No tools found" for valid queries
**Solution:** Check that selector API is running and accessible at `REACT_APP_AUTOMATION_SERVICE_URL/api/selector/search`

### Issue: Echo returns error
**Solution:** Verify automation service is running and `/ai/execute` endpoint is accessible

### Issue: Trace IDs not showing
**Solution:** Check browser console for `[ChatExec]` and `[ChatSelector]` logs

### Issue: Feature not working
**Solution:** Verify `REACT_APP_CHAT_DIRECT_EXEC=true` in `.env` and restart dev server

## Support

For issues or questions:
- Check console logs for `[ChatExec]` and `[ChatSelector]` messages
- Verify environment variables are set correctly
- Ensure backend services are running and accessible
- Review trace IDs for request correlation

## References

- PR #7: Chat Wire-Up: Direct Exec & Selector
- Branch: `zenc/chat-direct-exec-v1`
- Related: Walking Skeleton v1.1.0 (PR #6)