# Unified Execution Framework - Architecture

## System Overview

```
┌─────────────────────────────────────────────────────────────────────┐
│                         AI PIPELINE                                  │
│  - Selects tools based on user intent                               │
│  - Creates execution plan                                            │
│  - Sends to automation-service                                       │
└────────────────────────────┬────────────────────────────────────────┘
                             │
                             │ Execution Request
                             │ {tool: "Get-ComputerInfo", inputs: {...}}
                             ▼
┌─────────────────────────────────────────────────────────────────────┐
│                    AUTOMATION SERVICE                                │
│                                                                       │
│  ┌───────────────────────────────────────────────────────────────┐  │
│  │              UNIFIED EXECUTOR                                  │  │
│  │                                                                │  │
│  │  Stage 1: Parse Tool Metadata (or infer)                      │  │
│  │           ↓                                                    │  │
│  │  Stage 2: Resolve Parameters                                  │  │
│  │           ↓                                                    │  │
│  │  Stage 3: Build Command/Request                               │  │
│  │           ↓                                                    │  │
│  │  Stage 4: Resolve Credentials                                 │  │
│  │           ↓                                                    │  │
│  │  Stage 5: Execute                                              │  │
│  └───────────────────────────────────────────────────────────────┘  │
│                             │                                         │
│                             │ Command + Connection Info               │
│                             ▼                                         │
│  ┌───────────────────────────────────────────────────────────────┐  │
│  │           CONNECTION MANAGERS                                  │  │
│  │                                                                │  │
│  │  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐     │  │
│  │  │PowerShell│  │   SSH    │  │  Local   │  │ Impacket │     │  │
│  │  │  WinRM   │  │  Linux   │  │  Exec    │  │   WMI    │     │  │
│  │  └──────────┘  └──────────┘  └──────────┘  └──────────┘     │  │
│  │                                                                │  │
│  │  ┌──────────┐  ┌──────────┐  ┌──────────┐                    │  │
│  │  │   HTTP   │  │ Database │  │   gRPC   │                    │  │
│  │  │   REST   │  │  Queries │  │   APIs   │                    │  │
│  │  └──────────┘  └──────────┘  └──────────┘                    │  │
│  └───────────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────────┘
                             │
                             │ Execution Result
                             ▼
┌─────────────────────────────────────────────────────────────────────┐
│                      TARGET SYSTEMS                                  │
│                                                                       │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐           │
│  │ Windows  │  │  Linux   │  │ Database │  │   APIs   │           │
│  │ Servers  │  │ Servers  │  │ Servers  │  │ Services │           │
│  └──────────┘  └──────────┘  └──────────┘  └──────────┘           │
└─────────────────────────────────────────────────────────────────────┘
```

## Execution Flow

### Example: Windows PowerShell Cmdlet

```
User Request: "Get system info for 192.168.50.211"
                    ↓
AI Pipeline: Selects "Get-ComputerInfo" tool
                    ↓
Automation Service receives:
{
  "tool": "Get-ComputerInfo",
  "inputs": {"host": "192.168.50.211"}
}
                    ↓
┌─────────────────────────────────────────────────────────────┐
│ UNIFIED EXECUTOR                                             │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│ Stage 1: Parse Tool Metadata                                │
│   - Tool name: "Get-ComputerInfo"                           │
│   - Infer: Windows PowerShell cmdlet                        │
│   - Config: {                                               │
│       execution_type: "command",                            │
│       connection_type: "powershell",                        │
│       command_strategy: "cmdlet",                           │
│       parameter_format: "powershell"                        │
│     }                                                        │
│                                                              │
│ Stage 2: Resolve Parameters                                 │
│   - Extract target_host: "192.168.50.211"                   │
│   - Normalize parameters                                    │
│                                                              │
│ Stage 3: Build Command                                      │
│   - Strategy: cmdlet                                        │
│   - Command: "Get-ComputerInfo"                             │
│   - Format: PowerShell                                      │
│                                                              │
│ Stage 4: Resolve Credentials                                │
│   - Auto-fetch by IP: 192.168.50.211                        │
│   - Query asset-service for asset                           │
│   - Fetch credentials for asset                             │
│   - Result: {username: "admin", password: "***"}            │
│                                                              │
│ Stage 5: Execute                                             │
│   - Connection: PowerShell/WinRM                            │
│   - Target: 192.168.50.211                                  │
│   - Command: "Get-ComputerInfo"                             │
│   - Credentials: admin/***                                  │
│                                                              │
└─────────────────────────────────────────────────────────────┘
                    ↓
PowerShell Connection Manager
                    ↓
WinRM to 192.168.50.211
                    ↓
Execute: Get-ComputerInfo
                    ↓
Return: System information
```

### Example: Linux Command

```
User Request: "Check if web-server-01 is reachable"
                    ↓
AI Pipeline: Selects "ping" tool
                    ↓
Automation Service receives:
{
  "tool": "ping",
  "inputs": {"target": "web-server-01", "host": "bastion-host"}
}
                    ↓
┌─────────────────────────────────────────────────────────────┐
│ UNIFIED EXECUTOR                                             │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│ Stage 1: Parse Tool Metadata                                │
│   - Tool name: "ping"                                       │
│   - Platform: "linux"                                       │
│   - Config: {                                               │
│       execution_type: "command",                            │
│       connection_type: "ssh",                               │
│       command_strategy: "cli",                              │
│       parameter_format: "posix"                             │
│     }                                                        │
│                                                              │
│ Stage 2: Resolve Parameters                                 │
│   - Extract target_host: "bastion-host"                     │
│   - Extract target: "web-server-01"                         │
│                                                              │
│ Stage 3: Build Command                                      │
│   - Strategy: cli                                           │
│   - Command: "ping -c 4 web-server-01"                      │
│   - Format: POSIX                                           │
│                                                              │
│ Stage 4: Resolve Credentials                                │
│   - Auto-fetch for bastion-host                             │
│   - Result: {username: "ops", password: "***"}              │
│                                                              │
│ Stage 5: Execute                                             │
│   - Connection: SSH                                         │
│   - Target: bastion-host                                    │
│   - Command: "ping -c 4 web-server-01"                      │
│                                                              │
└─────────────────────────────────────────────────────────────┘
                    ↓
SSH Connection Manager
                    ↓
SSH to bastion-host
                    ↓
Execute: ping -c 4 web-server-01
                    ↓
Return: Ping statistics
```

### Example: Database Query

```
User Request: "Show me all users in the database"
                    ↓
AI Pipeline: Selects "psql" tool
                    ↓
Automation Service receives:
{
  "tool": "psql",
  "inputs": {
    "host": "db-server-01",
    "query": "SELECT * FROM users;"
  }
}
                    ↓
┌─────────────────────────────────────────────────────────────┐
│ UNIFIED EXECUTOR                                             │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│ Stage 1: Parse Tool Metadata                                │
│   - Tool name: "psql"                                       │
│   - Platform: "database"                                    │
│   - Config: {                                               │
│       execution_type: "query",                              │
│       connection_type: "database",                          │
│       command_strategy: "query",                            │
│       parameter_format: "custom"                            │
│     }                                                        │
│                                                              │
│ Stage 2: Resolve Parameters                                 │
│   - Extract target_host: "db-server-01"                     │
│   - Extract query: "SELECT * FROM users;"                   │
│                                                              │
│ Stage 3: Build Command                                      │
│   - Strategy: query                                         │
│   - Command: "SELECT * FROM users;"                         │
│                                                              │
│ Stage 4: Resolve Credentials                                │
│   - Auto-fetch for db-server-01                             │
│   - Result: {username: "postgres", password: "***"}         │
│                                                              │
│ Stage 5: Execute                                             │
│   - Connection: PostgreSQL                                  │
│   - Target: db-server-01                                    │
│   - Query: "SELECT * FROM users;"                           │
│                                                              │
└─────────────────────────────────────────────────────────────┘
                    ↓
Database Connection Manager
                    ↓
Connect to PostgreSQL on db-server-01
                    ↓
Execute: SELECT * FROM users;
                    ↓
Return: Query results
```

## Tool Type Matrix

```
┌──────────────────────┬──────────────┬─────────────────┬──────────────────┬──────────────────┐
│ Tool Type            │ Exec Type    │ Connection      │ Strategy         │ Format           │
├──────────────────────┼──────────────┼─────────────────┼──────────────────┼──────────────────┤
│ Windows PowerShell   │ command      │ powershell      │ cmdlet           │ powershell       │
│ Linux CLI            │ command      │ ssh             │ cli              │ posix            │
│ Database             │ query        │ database        │ query            │ custom           │
│ REST API             │ api          │ http/https      │ api_call         │ custom           │
│ Cloud CLI            │ command      │ local           │ cli              │ posix            │
│ Network Tools        │ command      │ local           │ cli              │ posix            │
│ Container Tools      │ command      │ local           │ cli              │ posix            │
│ Custom Scripts       │ script       │ local/ssh       │ script           │ posix            │
│ Windows Impacket     │ command      │ impacket        │ cli              │ windows          │
└──────────────────────┴──────────────┴─────────────────┴──────────────────┴──────────────────┘
```

## Command Building Strategies

### 1. Cmdlet Strategy (PowerShell)

```
Input:
  tool_name: "Get-Service"
  parameters: {name: "Spooler", status: "Running"}

Output:
  "Get-Service -Name Spooler -Status Running"

Rules:
  - Start with cmdlet name
  - Convert parameters to -ParameterName format
  - Handle booleans as switches
  - Quote strings with spaces
  - Join arrays with commas
```

### 2. CLI Strategy (POSIX)

```
Input:
  tool_name: "ping"
  parameters: {c: 4, target: "google.com"}

Output:
  "ping -c 4 google.com"

Rules:
  - Start with command name
  - Short params: -p value
  - Long params: --parameter-name value
  - Booleans as flags
  - Positional args at end
```

### 3. Query Strategy (Database)

```
Input:
  tool_name: "psql"
  parameters: {query: "SELECT * FROM users;"}

Output:
  "SELECT * FROM users;"

Rules:
  - Extract query parameter
  - Pass directly to database
  - No transformation needed
```

### 4. API Call Strategy (REST)

```
Input:
  tool_name: "api-call"
  parameters: {
    method: "GET",
    endpoint: "/api/v1/users",
    headers: {...}
  }

Output:
  {
    method: "GET",
    url: "https://api.example.com/api/v1/users",
    headers: {...}
  }

Rules:
  - Build HTTP request
  - Add authentication
  - Set headers
  - Format body
```

## Credential Resolution Flow

```
┌─────────────────────────────────────────────────────────────┐
│ Credential Resolution (3 Fallback Mechanisms)               │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│ 1. Explicit asset_id                                        │
│    ├─ Check: use_asset_credentials=true AND asset_id set   │
│    ├─ Action: Fetch from asset-service by asset_id         │
│    └─ Result: {username, password, domain}                  │
│                                                              │
│ 2. Auto-fetch by target_host                                │
│    ├─ Check: target_host set AND no explicit credentials   │
│    ├─ Action: Query asset-service for asset by IP          │
│    ├─ Action: Fetch credentials for found asset            │
│    └─ Result: {username, password, domain}                  │
│                                                              │
│ 3. Explicit credentials                                     │
│    ├─ Check: username/password in parameters               │
│    └─ Result: {username, password}                          │
│                                                              │
│ If all fail: credentials = None                             │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

## Parameter Format Examples

### PowerShell Format

```
-ParameterName Value
-Name "Print Spooler"
-Status Running
-Force
-ComputerName server01,server02
```

### POSIX Format

```
--parameter-name value
--name "Print Spooler"
--status running
--force
-c 4
-v
```

### Windows Format

```
/ParameterName Value
/Name "Print Spooler"
/Status Running
/Force
```

## Extension Points

### Adding a New Execution Type

```python
class ExecutionType(str, Enum):
    COMMAND = "command"
    API = "api"
    QUERY = "query"
    SCRIPT = "script"
    GRAPHQL = "graphql"  # NEW
```

### Adding a New Connection Type

```python
class ConnectionType(str, Enum):
    POWERSHELL = "powershell"
    SSH = "ssh"
    LOCAL = "local"
    HTTP = "http"
    DATABASE = "database"
    GRPC = "grpc"
    IMPACKET = "impacket"
    WEBSOCKET = "websocket"  # NEW
```

### Adding a New Command Strategy

```python
class CommandStrategy(str, Enum):
    CMDLET = "cmdlet"
    CLI = "cli"
    SCRIPT = "script"
    TEMPLATE = "template"
    API_CALL = "api_call"
    QUERY = "query"
    GRAPHQL_QUERY = "graphql_query"  # NEW
```

### Adding a New Parameter Format

```python
class ParameterFormat(str, Enum):
    POWERSHELL = "powershell"
    POSIX = "posix"
    WINDOWS = "windows"
    CUSTOM = "custom"
    JSON = "json"  # NEW
```

## Benefits Visualization

```
BEFORE (Hardcoded):
┌─────────────────────────────────────────────────────────────┐
│ if tool == "ping":                                           │
│     command = f"ping -c 4 {host}"                            │
│ elif tool.startswith("Get-"):                                │
│     # 50 lines of PowerShell logic                           │
│ elif tool == "psql":                                         │
│     # 30 lines of database logic                             │
│ elif tool == "api-call":                                     │
│     # 40 lines of API logic                                  │
│ else:                                                         │
│     # Generic fallback                                       │
│                                                              │
│ Total: 500+ lines of hardcoded logic                        │
│ Maintainability: LOW                                         │
│ Extensibility: LOW                                           │
│ Testability: LOW                                             │
└─────────────────────────────────────────────────────────────┘

AFTER (Unified):
┌─────────────────────────────────────────────────────────────┐
│ command, target, connection, creds =                         │
│     await unified_executor.execute_tool(                     │
│         tool_definition, parameters, service                 │
│     )                                                         │
│                                                              │
│ Total: 5 lines of unified logic                             │
│ Maintainability: HIGH                                        │
│ Extensibility: HIGH                                          │
│ Testability: HIGH                                            │
└─────────────────────────────────────────────────────────────┘
```

## Conclusion

The Unified Execution Framework provides:

1. ✅ **Systematic execution** - Same steps for all tools
2. ✅ **Consistent flavors** - Defined by metadata, not code
3. ✅ **No hardcoded logic** - Data-driven execution
4. ✅ **Easy to extend** - Add new types without code changes
5. ✅ **Maintainable** - One place to fix bugs, add features
6. ✅ **Testable** - Test once, applies to all tools

This is the **systematic, principled approach** you asked for.