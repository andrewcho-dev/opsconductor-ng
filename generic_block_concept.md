# Generic Block Concept for OpsConductor

## Overview

This document outlines a revolutionary approach to workflow automation using **Generic Blocks** - a small set of highly flexible, connection-agnostic blocks that can handle infinite scenarios through configuration rather than proliferation of specific block types.

## Core Philosophy

### The Problem with Specific Blocks
Traditional workflow systems create specific blocks for every combination of:
- Protocol (SSH, WinRM, HTTP, etc.)
- Operation (file copy, command execution, service control, etc.)
- Target system (Windows, Linux, Docker, Kubernetes, etc.)

This leads to:
- **Block explosion**: Hundreds of specific blocks to maintain
- **Learning complexity**: Users must memorize many different block types
- **Maintenance burden**: Each block needs separate documentation, testing, and updates
- **Inconsistent interfaces**: Different blocks have different configuration patterns

### The Generic Block Solution
Instead of many specific blocks, we use a **small set of generic blocks** that:
- **Abstract the connection method** from the operation
- **Provide consistent interfaces** across all protocols
- **Scale infinitely** through configuration
- **Reduce cognitive load** - learn once, use everywhere

## Core Generic Block Types

### 1. `action.command`
**Purpose**: Execute commands on any target system using any connection method

**Key Features**:
- **Connection agnostic**: SSH, WinRM, local, Docker, Kubernetes
- **Shell flexibility**: cmd, powershell, bash, sh, zsh
- **Auto-detection**: Automatically choose connection method based on target OS
- **Unified result format**: Same output structure regardless of connection type

**Configuration Example**:
```json
{
  "type": "action.command",
  "config": {
    "target": "win-server-01",
    "connection_method": "winrm",  // or "ssh", "local", "auto"
    "command": "dir C:\\ /B",
    "shell": "cmd",                // or "powershell", "bash", "auto"
    "timeout_seconds": 30,
    "working_directory": "C:\\",
    "environment_variables": {
      "VAR1": "value1"
    },
    "winrm_options": {
      "operation_timeout": 60,
      "read_timeout": 90
    },
    "ssh_options": {
      "strict_host_key_checking": false
    }
  }
}
```

**Use Cases**:
- Windows directory listing via WinRM
- Linux process management via SSH
- Local script execution
- Docker container commands
- Kubernetes pod commands

### 2. `action.file_operation`
**Purpose**: Perform file operations on any target system using any connection method

**Supported Operations**:
- `read` - Read file contents
- `write` - Write file contents
- `copy` - Copy files between locations
- `move` - Move/rename files
- `delete` - Delete files
- `exists` - Check if file exists
- `get_info` - Get file metadata
- `list` - List directory contents
- `create_directory` - Create directories
- `set_permissions` - Set file permissions

**Configuration Example**:
```json
{
  "type": "action.file_operation",
  "config": {
    "target": "linux-server-01",
    "connection_method": "ssh",
    "operation": "write",
    "source_path": "/var/log/app.log",
    "file_content": "{{data.log_entry}}",
    "create_directories": true,
    "overwrite_existing": false,
    "encoding": "utf-8",
    "permissions": "644"
  }
}
```

### 3. `action.http_request`
**Purpose**: Make HTTP/HTTPS requests to any API or web service

**Key Features**:
- **All HTTP methods**: GET, POST, PUT, DELETE, PATCH, HEAD, OPTIONS
- **Authentication support**: Basic, Bearer, API Key, OAuth, Custom headers
- **Request/response handling**: JSON, XML, form data, raw text
- **Error handling**: Retry logic, timeout configuration
- **Certificate handling**: SSL verification, custom certificates

**Configuration Example**:
```json
{
  "type": "action.http_request",
  "config": {
    "method": "POST",
    "url": "http://192.168.1.101/axis-cgi/com/ptz.cgi",
    "headers": {
      "Content-Type": "application/x-www-form-urlencoded"
    },
    "authentication": {
      "type": "basic",
      "username": "admin",
      "password": "{{vault.camera_password}}"
    },
    "body": "autofocus=on",
    "timeout_seconds": 30,
    "retry_attempts": 2,
    "ssl_verify": true
  }
}
```

### 4. `action.service_control`
**Purpose**: Control system services on any target system

**Supported Actions**:
- `start` - Start service
- `stop` - Stop service
- `restart` - Restart service
- `status` - Get service status
- `enable` - Enable service (auto-start)
- `disable` - Disable service

**Configuration Example**:
```json
{
  "type": "action.service_control",
  "config": {
    "target": "win-server-01",
    "connection_method": "winrm",
    "service_name": "MyApplication",
    "action": "restart",
    "timeout_seconds": 60,
    "service_manager": "auto"  // auto-detect: systemd, service, net, sc
  }
}
```

### 5. `action.notification`
**Purpose**: Send notifications through various channels

**Supported Channels**:
- `email` - Email notifications
- `slack` - Slack messages
- `teams` - Microsoft Teams
- `webhook` - Generic webhook calls
- `sms` - SMS messages
- `push` - Push notifications

**Configuration Example**:
```json
{
  "type": "action.notification",
  "config": {
    "notification_type": "email",
    "recipients": ["admin@company.com"],
    "subject": "Process Monitor Alert - {{data.process_name}}",
    "message": "Process {{data.process_name}} status: {{data.status}}",
    "priority": "high",
    "attachments": ["{{data.log_file}}"]
  }
}
```

### 6. `data.transform`
**Purpose**: Transform, parse, and manipulate data between blocks

**Key Features**:
- **JavaScript execution**: Full JavaScript support for data processing
- **Template support**: Handlebars-style templating
- **JSON/XML parsing**: Built-in parsers
- **Data validation**: Schema validation
- **Aggregation**: Combine data from multiple sources

**Configuration Example**:
```json
{
  "type": "data.transform",
  "config": {
    "script": "// Parse process status\nconst isRunning = input.stdout.includes('MyApp.exe');\nreturn {\n  process_running: isRunning,\n  check_time: new Date().toISOString()\n};"
  }
}
```

### 7. `logic.if`
**Purpose**: Conditional branching based on data or conditions

**Configuration Example**:
```json
{
  "type": "logic.if",
  "config": {
    "condition": "{{data.process_running}} === true"
  }
}
```

### 8. `flow.delay`
**Purpose**: Add delays between operations

**Configuration Example**:
```json
{
  "type": "flow.delay",
  "config": {
    "delay_seconds": 5
  }
}
```

## Connection Management Architecture

### Target Configuration
Each target system is defined with connection details:

```json
{
  "id": "win-server-01",
  "name": "Windows Application Server",
  "hostname": "192.168.1.100",
  "os_type": "windows",
  "default_connection": "winrm",
  "auth_method": "password",
  "username": "administrator",
  "password": "{{vault.win_server_password}}",
  "winrm_port": 5985,
  "winrm_use_ssl": false,
  "winrm_transport": "ntlm"
}
```

### Connection Handlers
Each connection type has a dedicated handler:

- **WinRMConnectionHandler**: Windows Remote Management
- **SSHConnectionHandler**: SSH for Linux/Unix systems
- **LocalConnectionHandler**: Local command execution
- **DockerConnectionHandler**: Docker container operations
- **KubernetesConnectionHandler**: Kubernetes pod operations

### Auto-Detection Logic
1. **Explicit method**: Use `connection_method` if specified
2. **Target default**: Use target's `default_connection`
3. **OS-based detection**: 
   - `windows` → `winrm`
   - `linux`/`macos` → `ssh`
   - `localhost`/`127.0.0.1` → `local`
4. **Fallback**: Default to `ssh`

## Real-World Examples

### Example 1: Axis Camera Maintenance
**Scenario**: Every Monday morning, connect to multiple Axis cameras, perform autofocus, reset PTZ to home position, and log results.

**Generic Blocks Used**:
- `trigger.schedule` - Monday morning trigger
- `action.http_request` - Camera API calls (autofocus, PTZ)
- `action.file_operation` - Write logs via SSH
- `action.notification` - Email summary
- `data.transform` - Parse responses and format logs

**Key Benefits**:
- **Scalable**: Add cameras by updating configuration
- **Resilient**: Individual camera failures don't stop workflow
- **Comprehensive**: Detailed logging and error reporting

### Example 2: Windows Process Monitoring
**Scenario**: Check if a process is running on Windows, restart if needed, send notification.

**Generic Blocks Used**:
- `trigger.schedule` - Periodic checks
- `action.command` - WinRM commands (tasklist, taskkill, start process)
- `logic.if` - Decision logic based on process state
- `flow.delay` - Wait between stop and start
- `action.notification` - Email alerts
- `data.transform` - Parse process status

**Key Benefits**:
- **Connection agnostic**: Same pattern works for Linux processes via SSH
- **Flexible**: Easy to modify process names, schedules, notifications
- **Reliable**: Proper error handling and status tracking

## Implementation Architecture

### Core Components

#### 1. Connection Manager (`connection_manager.py`)
- **Purpose**: Manages connections to different target systems
- **Key Classes**:
  - `ConnectionManager`: Central coordinator
  - `ConnectionHandler`: Abstract base for connection types
  - `WinRMConnectionHandler`: Windows Remote Management
  - `SSHConnectionHandler`: SSH connections
  - `LocalConnectionHandler`: Local execution

#### 2. Generic Block Executor (`generic_block_executor.py`)
- **Purpose**: Executes generic blocks with appropriate connection methods
- **Key Methods**:
  - `execute_command_block()`: Handle action.command blocks
  - `execute_file_operation_block()`: Handle action.file_operation blocks
  - `execute_service_control_block()`: Handle action.service_control blocks

#### 3. Result Standardization
All operations return standardized result objects:

```python
@dataclass
class CommandResult:
    success: bool
    stdout: str
    stderr: str
    exit_code: int
    execution_time_ms: int
    target: str
    connection_type: str
    error_message: Optional[str] = None
```

### Configuration Schema

#### Block Configuration
```json
{
  "id": "unique-block-id",
  "type": "action.command",
  "position": {"x": 100, "y": 100},
  "config": {
    "target": "target-id",
    "connection_method": "auto",
    // ... block-specific configuration
  }
}
```

#### Connection Configuration
```json
{
  "from": {"blockId": "source-block", "output": "success"},
  "to": {"blockId": "target-block", "input": "trigger"},
  "type": "flow",
  "condition": "{{data.success}} === true"
}
```

## Benefits of the Generic Block Approach

### 1. **Reduced Complexity**
- **8 generic blocks** instead of hundreds of specific blocks
- **Consistent patterns** across all operations
- **Single learning curve** for all scenarios

### 2. **Infinite Scalability**
- **Any protocol** can be added as a connection handler
- **Any operation** can be configured within generic blocks
- **Any target system** can be supported

### 3. **Maintainability**
- **Centralized connection logic** in connection handlers
- **Consistent error handling** across all blocks
- **Single codebase** for similar operations

### 4. **User Experience**
- **Predictable interfaces** - same patterns everywhere
- **Auto-completion** - UI can provide intelligent suggestions
- **Validation** - consistent validation across all blocks

### 5. **Enterprise Features**
- **Credential management** - centralized vault integration
- **Audit logging** - consistent logging across all connections
- **Performance monitoring** - standardized metrics
- **Error handling** - unified retry and fallback logic

## UI Implications

### Dynamic Configuration Forms
The UI adapts based on selected options:

1. **Target Selection** → Shows available connection methods
2. **Connection Method** → Shows protocol-specific options
3. **Operation Type** → Shows operation-specific fields
4. **Auto-completion** → Suggests valid values based on context

### Example UI Flow:
1. User selects `action.command` block
2. User selects target "win-server-01"
3. UI detects Windows target, suggests WinRM
4. UI shows WinRM-specific options (port, transport, SSL)
5. User selects shell type (cmd/powershell)
6. UI provides shell-specific command examples

### Configuration Validation
- **Real-time validation** of configuration options
- **Connection testing** before workflow execution
- **Syntax highlighting** for commands and scripts
- **Template validation** for dynamic values

## Migration Strategy

### Phase 1: Core Implementation
1. Implement connection manager with WinRM, SSH, local handlers
2. Build generic block executor for command and file operations
3. Create standardized result objects and error handling
4. Develop basic UI for generic block configuration

### Phase 2: Extended Operations
1. Add HTTP request and service control blocks
2. Implement notification and data transformation blocks
3. Add Docker and Kubernetes connection handlers
4. Enhance UI with dynamic forms and validation

### Phase 3: Advanced Features
1. Connection pooling and caching
2. Advanced credential management
3. Performance monitoring and metrics
4. Workflow templates and best practices

### Phase 4: Migration Tools
1. Automatic migration from specific blocks to generic blocks
2. Configuration import/export tools
3. Workflow validation and optimization
4. Documentation and training materials

## Success Metrics

### Technical Metrics
- **Block count reduction**: From 200+ specific blocks to 8 generic blocks
- **Code maintainability**: Reduced codebase size by 70%
- **Test coverage**: Centralized testing of connection logic
- **Performance**: Consistent execution times across protocols

### User Experience Metrics
- **Learning curve**: Reduced onboarding time by 60%
- **Workflow creation speed**: Faster workflow development
- **Error rates**: Fewer configuration errors due to consistency
- **User satisfaction**: Higher satisfaction scores

### Business Metrics
- **Development velocity**: Faster feature development
- **Maintenance costs**: Reduced ongoing maintenance
- **Support burden**: Fewer support tickets due to consistency
- **Adoption rates**: Higher user adoption of advanced features

## Conclusion

The Generic Block Concept represents a paradigm shift from **specific, proliferating blocks** to **generic, configurable blocks**. This approach:

- **Reduces complexity** while **increasing capability**
- **Scales infinitely** through configuration rather than code
- **Provides consistency** across all operations and protocols
- **Improves maintainability** and user experience
- **Enables rapid development** of new scenarios

By implementing this concept, OpsConductor becomes a truly universal automation platform that can handle any scenario through intelligent configuration rather than endless block proliferation.

## Next Steps

1. **Validate concept** with additional real-world scenarios
2. **Design detailed API specifications** for each generic block
3. **Create implementation roadmap** with milestones
4. **Develop proof-of-concept** for core generic blocks
5. **Design UI mockups** for dynamic configuration forms
6. **Plan migration strategy** from existing specific blocks

This concept document serves as the foundation for implementing a revolutionary approach to workflow automation that will set OpsConductor apart from all other automation platforms.