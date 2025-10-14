# Tool Registry & Runner

Complete guide to the Tool Registry and Runner system for OpsConductor.

## Overview

The Tool Registry & Runner provides a centralized system for managing and executing operational tools with full safety controls:

- **Tool Registry**: YAML-based catalog of tool specifications
- **Tool Runner**: Safe execution engine with timeouts, output limits, and redaction
- **Proxy Layer**: Kong → Automation Service → AI Pipeline routing
- **Metrics**: Prometheus metrics for monitoring tool usage

## Architecture

```
┌─────────────┐     ┌──────────────────┐     ┌─────────────┐     ┌──────────────┐
│   Frontend  │────▶│  Kong Gateway    │────▶│ Automation  │────▶│ AI Pipeline  │
│             │     │  (Port 3000)     │     │  Service    │     │              │
└─────────────┘     └──────────────────┘     └─────────────┘     └──────────────┘
                                                                          │
                                                                          ▼
                                                                  ┌──────────────┐
                                                                  │Tool Registry │
                                                                  │& Runner      │
                                                                  └──────────────┘
                                                                          │
                                                                          ▼
                                                                  ┌──────────────┐
                                                                  │ Tool Catalog │
                                                                  │ (YAML files) │
                                                                  └──────────────┘
```

## Tool Specification Format

Tools are defined in YAML files in `tools/catalog/`:

```yaml
name: dns_lookup
display_name: DNS Lookup
description: Perform DNS lookup for a domain name
category: network
platform: cross-platform  # windows, linux, or cross-platform
version: 1.0.0

# Execution configuration
command_template: "nslookup -type={record_type} {domain}"
timeout_seconds: 10
requires_admin: false

# Parameters
parameters:
  - name: domain
    type: string
    description: Domain name to lookup
    required: true
    pattern: "^[a-zA-Z0-9][a-zA-Z0-9-_.]*[a-zA-Z0-9]$"
  
  - name: record_type
    type: string
    description: DNS record type
    required: false
    default: "A"
    enum: ["A", "AAAA", "NS", "MX", "TXT", "CNAME", "SOA"]

# Safety controls
max_output_bytes: 8192
redact_patterns:
  - "(?i)(password|secret|token)=[^&\\s]+"

# Metadata
tags:
  - dns
  - network
  - troubleshooting

examples:
  - description: "Lookup A record for example.com"
    parameters:
      domain: "example.com"
      record_type: "A"
```

## Parameter Types

### String
```yaml
- name: domain
  type: string
  description: Domain name
  required: true
  pattern: "^[a-zA-Z0-9.-]+$"  # Optional regex validation
```

### Integer
```yaml
- name: port
  type: integer
  description: Port number
  required: true
  min_value: 1
  max_value: 65535
```

### Boolean
```yaml
- name: verbose
  type: boolean
  description: Enable verbose output
  required: false
  default: false
```

### Enum
```yaml
- name: method
  type: string
  description: HTTP method
  required: false
  default: "GET"
  enum: ["GET", "POST", "PUT", "DELETE"]
```

## API Endpoints

### List Tools

**GET** `/ai/tools/list`

Query parameters:
- `platform` (optional): Filter by platform (windows, linux, cross-platform)
- `category` (optional): Filter by category (network, system, database, etc.)
- `tags` (optional): Comma-separated list of tags

Response:
```json
{
  "success": true,
  "tools": [
    {
      "name": "dns_lookup",
      "display_name": "DNS Lookup",
      "description": "Perform DNS lookup for a domain name",
      "category": "network",
      "platform": "cross-platform",
      "parameters": [...],
      "tags": ["dns", "network"]
    }
  ],
  "total": 5,
  "filters": {
    "platform": null,
    "category": "network",
    "tags": null
  }
}
```

### Execute Tool

**POST** `/ai/tools/execute`

Request:
```json
{
  "name": "dns_lookup",
  "params": {
    "domain": "example.com",
    "record_type": "A"
  },
  "trace_id": "optional-trace-id"
}
```

Response:
```json
{
  "success": true,
  "tool": "dns_lookup",
  "output": "Server:\t\t127.0.0.53\nAddress:\t127.0.0.53#53\n\nNon-authoritative answer:\nName:\texample.com\nAddress: 93.184.216.34\n",
  "error": null,
  "duration_ms": 358.81,
  "trace_id": "test-dns-001",
  "timestamp": "2025-01-13T10:30:45.123456Z",
  "exit_code": 0,
  "truncated": false,
  "redacted": false
}
```

## Safety Controls

### Timeouts
Each tool has a configurable timeout. Execution is terminated if it exceeds the limit.

```yaml
timeout_seconds: 30
```

### Output Limits
Output is truncated if it exceeds the maximum size:

```yaml
max_output_bytes: 16384  # 16KB default
```

Environment variable:
```bash
TOOL_MAX_OUTPUT_BYTES=16384
```

### Credential Redaction
Sensitive data is automatically redacted using regex patterns:

```yaml
redact_patterns:
  - "(?i)(api[_-]?key|token|password|secret)=[^&\\s]+"
  - "(?i)authorization:\\s*[^\\n]+"
```

### Parameter Validation
All parameters are validated before execution:
- Type checking (string, integer, boolean)
- Required field validation
- Range validation (min/max for integers)
- Pattern matching (regex for strings)
- Enum validation

## Built-in Tools

### 1. DNS Lookup
Perform DNS queries for domain names.

**Parameters:**
- `domain` (required): Domain name to lookup
- `record_type` (optional): DNS record type (A, AAAA, NS, MX, TXT, CNAME, SOA)

**Example:**
```bash
curl -X POST http://localhost:3000/ai/tools/execute \
  -H "Content-Type: application/json" \
  -d '{
    "name": "dns_lookup",
    "params": {
      "domain": "example.com",
      "record_type": "A"
    }
  }'
```

### 2. HTTP Check
Check HTTP endpoint availability and response time.

**Parameters:**
- `url` (required): URL to check
- `method` (optional): HTTP method (GET, HEAD, POST, PUT, DELETE)
- `timeout_s` (optional): Request timeout in seconds

**Example:**
```bash
curl -X POST http://localhost:3000/ai/tools/execute \
  -H "Content-Type: application/json" \
  -d '{
    "name": "http_check",
    "params": {
      "url": "https://www.google.com",
      "method": "GET",
      "timeout_s": 5
    }
  }'
```

### 3. TCP Port Check
Check if a TCP port is open and accepting connections.

**Parameters:**
- `host` (required): Target hostname or IP address
- `port` (required): TCP port number (1-65535)
- `timeout_s` (optional): Connection timeout in seconds

**Example:**
```bash
curl -X POST http://localhost:3000/ai/tools/execute \
  -H "Content-Type: application/json" \
  -d '{
    "name": "tcp_port_check",
    "params": {
      "host": "localhost",
      "port": 3000,
      "timeout_s": 3
    }
  }'
```

### 4. Traceroute
Trace network path to a destination host.

**Parameters:**
- `host` (required): Target hostname or IP address
- `max_hops` (optional): Maximum number of hops (1-30)
- `timeout_s` (optional): Timeout per hop in seconds

**Example:**
```bash
curl -X POST http://localhost:3000/ai/tools/execute \
  -H "Content-Type: application/json" \
  -d '{
    "name": "traceroute",
    "params": {
      "host": "8.8.8.8",
      "max_hops": 5,
      "timeout_s": 3
    }
  }'
```

### 5. Ping
Send ICMP echo requests to test network connectivity.

**Parameters:**
- `host` (required): Target hostname or IP address
- `count` (optional): Number of ping packets (1-10)
- `timeout_s` (optional): Timeout per packet in seconds

**Example:**
```bash
curl -X POST http://localhost:3000/ai/tools/execute \
  -H "Content-Type: application/json" \
  -d '{
    "name": "shell_ping",
    "params": {
      "host": "8.8.8.8",
      "count": 3,
      "timeout_s": 2
    }
  }'
```

## Metrics

Tool execution metrics are exposed at `/metrics` endpoint:

### Tool Request Metrics
```
# Total tool requests
ai_tool_requests_total{tool="dns_lookup",status="success"} 42

# Tool request errors
ai_tool_request_errors_total{tool="dns_lookup",error_type="timeout"} 2

# Tool request duration (histogram)
ai_tool_request_duration_seconds_bucket{tool="dns_lookup",le="0.1"} 35
ai_tool_request_duration_seconds_bucket{tool="dns_lookup",le="0.5"} 40
ai_tool_request_duration_seconds_sum{tool="dns_lookup"} 12.5
ai_tool_request_duration_seconds_count{tool="dns_lookup"} 42
```

### Registry Metrics
```
# Number of registered tools
ai_tool_registry_size 5

# Registry operations
ai_tool_registry_operations_total{operation="load",status="success"} 1
ai_tool_registry_operations_total{operation="register",status="success"} 5
```

## Adding New Tools

1. Create a YAML file in `tools/catalog/`:

```yaml
name: my_custom_tool
display_name: My Custom Tool
description: Description of what the tool does
category: custom
platform: cross-platform
version: 1.0.0

command_template: "my-command {param1} {param2}"
timeout_seconds: 30
requires_admin: false

parameters:
  - name: param1
    type: string
    description: First parameter
    required: true

max_output_bytes: 8192
redact_patterns: []
tags:
  - custom
```

2. Restart the ai-pipeline service:

```bash
docker-compose restart ai-pipeline
```

3. Verify the tool is loaded:

```bash
curl http://localhost:3000/ai/tools/list | jq '.tools[] | select(.name=="my_custom_tool")'
```

## Environment Variables

```bash
# Enable tools feature
FEATURE_TOOLS_ENABLE=true

# Tool catalog directory
TOOLS_SEED_DIR=/app/tools/catalog

# Maximum output size (bytes)
TOOL_MAX_OUTPUT_BYTES=16384
```

## Error Handling

### Tool Not Found
```json
{
  "success": false,
  "tool": "nonexistent_tool",
  "error": "Tool 'nonexistent_tool' not found in registry",
  "duration_ms": 0.01,
  "trace_id": "test-001",
  "timestamp": "2025-01-13T10:30:45Z"
}
```

### Parameter Validation Error
```json
{
  "success": false,
  "tool": "dns_lookup",
  "error": "Parameter validation failed: Required parameter 'domain' is missing",
  "duration_ms": 0.02,
  "trace_id": "test-002",
  "timestamp": "2025-01-13T10:30:45Z"
}
```

### Timeout Error
```json
{
  "success": false,
  "tool": "traceroute",
  "error": "Execution timed out after 30s",
  "duration_ms": 30000.0,
  "trace_id": "test-003",
  "timestamp": "2025-01-13T10:30:45Z"
}
```

## Security Considerations

1. **No Shell Injection**: Parameters are validated and sanitized
2. **Timeout Enforcement**: All executions have hard timeouts
3. **Output Limits**: Output is truncated to prevent memory exhaustion
4. **Credential Redaction**: Sensitive data is automatically redacted
5. **Admin Privileges**: Tools requiring admin access are clearly marked
6. **Audit Trail**: All executions are logged with trace IDs

## Testing

Run integration tests:

```bash
./scripts/test_tools_integration.sh
```

Run backend unit tests:

```bash
python3 test_tools_backend.py
```

## Troubleshooting

### Tools not loading
Check ai-pipeline logs:
```bash
docker-compose logs ai-pipeline | grep ToolRegistry
```

### Tool execution fails
Check trace ID in logs:
```bash
docker-compose logs ai-pipeline | grep "trace_id=your-trace-id"
```

### Metrics not appearing
Verify Prometheus endpoint:
```bash
curl http://localhost:8000/metrics | grep ai_tool
```