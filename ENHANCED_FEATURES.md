# OpsConductor Enhanced Features Documentation

## 🚀 Overview

This document describes the comprehensive enhancements made to the OpsConductor system, including the visual job builder, modular step libraries, enhanced target management, and advanced execution capabilities.

## 📋 Table of Contents

1. [Visual Job Builder](#visual-job-builder)
2. [Modular Step Libraries](#modular-step-libraries)
3. [Enhanced Target Management](#enhanced-target-management)
4. [Advanced Job Execution](#advanced-job-execution)
5. [Security Operations](#security-operations)
6. [Database Operations](#database-operations)
7. [System Integration](#system-integration)
8. [API Enhancements](#api-enhancements)
9. [Frontend Components](#frontend-components)
10. [Testing & Validation](#testing--validation)

---

## 🎨 Visual Job Builder

### Features
- **Drag-and-Drop Interface**: Intuitive visual workflow creation
- **Node-Based Architecture**: Modular step components with visual connections
- **Real-Time Validation**: Immediate feedback on job configuration
- **Flow Execution**: Visual representation of job execution paths
- **Template System**: Pre-built job templates for common tasks

### Components
- **EnhancedVisualJobBuilder.tsx**: Main visual builder component
- **Node Templates**: Pre-configured step templates for all libraries
- **Connection System**: Visual flow connections between steps
- **Configuration Panels**: Dynamic configuration forms for each step type

### Supported Node Types
- **File Operations**: Read, write, copy, move, delete files
- **Windows Operations**: Registry, services, system management
- **System Operations**: Process management, performance monitoring
- **Network Operations**: HTTP requests, email, file transfers
- **Logic Control**: Conditions, loops, branching
- **Database Operations**: Queries, connections, data management
- **Security Operations**: Encryption, vulnerability scanning

### Usage
```typescript
// Access the visual job builder
<EnhancedVisualJobBuilder
  onJobCreate={handleJobCreate}
  onCancel={handleCancel}
  editingJob={existingJob}
/>
```

---

## 🔧 Modular Step Libraries

### Architecture
The system now uses a modular, pluggable architecture for step libraries:

```
shared/
├── step_library.py              # Core registry system
├── file_operations_library.py   # File system operations
├── windows_operations_library.py # Windows-specific operations
├── system_operations_library.py  # Cross-platform system ops
├── network_operations_library.py # Network and HTTP operations
├── logic_control_library.py     # Control flow operations
├── database_operations_library.py # Database operations
├── security_operations_library.py # Security operations
└── enhanced_job_executor.py     # Enhanced execution engine
```

### File Operations Library
```python
# Available operations
- file.read              # Read file contents
- file.write             # Write to file
- file.copy              # Copy files
- file.move              # Move/rename files
- file.delete            # Delete files
- file.exists            # Check file existence
- directory.create       # Create directories
- directory.list         # List directory contents
- directory.delete       # Delete directories
- file.permissions.set   # Set file permissions
- file.permissions.get   # Get file permissions
- file.compress          # Compress files/directories
```

### Windows Operations Library
```python
# Available operations
- windows.registry.read     # Read registry values
- windows.registry.write    # Write registry values
- windows.registry.delete   # Delete registry keys
- windows.service.status    # Get service status
- windows.service.start     # Start service
- windows.service.stop      # Stop service
- windows.service.restart   # Restart service
- windows.process.list      # List processes
- windows.process.kill      # Kill process
- windows.eventlog.read     # Read event logs
- windows.wmi.query         # Execute WMI queries
- windows.powershell.exec   # Execute PowerShell
- windows.cmd.exec          # Execute CMD commands
- windows.firewall.rule     # Manage firewall rules
- windows.user.create       # Create user accounts
```

### System Operations Library
```python
# Available operations
- system.info.get           # Get system information
- system.performance.cpu    # CPU performance metrics
- system.performance.memory # Memory performance metrics
- system.performance.disk   # Disk performance metrics
- system.performance.network # Network performance metrics
- system.process.list       # List running processes
- system.process.kill       # Kill processes
- system.process.start      # Start processes
- system.service.list       # List system services
- system.service.status     # Get service status
- system.service.control    # Control services
- system.user.list          # List system users
- system.group.list         # List system groups
- system.disk.usage         # Get disk usage
- system.network.interfaces # List network interfaces
- system.environment.get    # Get environment variables
- system.environment.set    # Set environment variables
- system.reboot             # Reboot system
```

### Network Operations Library
```python
# Available operations
- network.http.get          # HTTP GET request
- network.http.post         # HTTP POST request
- network.http.put          # HTTP PUT request
- network.http.delete       # HTTP DELETE request
- network.http.patch        # HTTP PATCH request
- network.download.file     # Download files
- network.upload.file       # Upload files
- network.email.send        # Send emails
- network.ping              # Ping hosts
- network.port.scan         # Port scanning
```

### Logic Control Library
```python
# Available operations
- logic.if                  # Conditional branching
- logic.switch              # Multi-way branching
- logic.loop.for            # For loops
- logic.loop.while          # While loops
- logic.loop.foreach        # Foreach loops
- logic.wait                # Wait/delay
- logic.parallel            # Parallel execution
- logic.sequence            # Sequential execution
```

### Database Operations Library
```python
# Available operations
- database.connect          # Connect to database
- database.disconnect       # Disconnect from database
- database.query            # Execute SELECT queries
- database.execute          # Execute INSERT/UPDATE/DELETE
- database.transaction      # Transaction management
- database.backup           # Create database backups
```

### Security Operations Library
```python
# Available operations
- security.encrypt_data     # Encrypt sensitive data
- security.decrypt_data     # Decrypt encrypted data
- security.generate_hash    # Generate data hashes
- security.verify_hash      # Verify hash integrity
- security.generate_key     # Generate encryption keys
- security.vulnerability_scan # Vulnerability scanning
- security.check_certificate # SSL certificate validation
- security.compliance_check  # Compliance assessment
```

---

## 🎯 Enhanced Target Management

### Features
- **Advanced Filtering**: Filter by platform, environment, status, tags
- **Bulk Operations**: Select and operate on multiple targets
- **Target Groups**: Organize targets into logical groups
- **Real-Time Status**: Live status monitoring and health checks
- **Enhanced Metadata**: Rich target information and tagging

### TargetSelector Component
```typescript
<TargetSelector
  selectedTargets={selectedTargets}
  onTargetsChange={setSelectedTargets}
  multiSelect={true}
  showDetails={true}
  filterByPlatform="windows"
  filterByStatus="online"
/>
```

### Target Properties
```typescript
interface Target {
  id: number;
  name: string;
  host: string;
  port: number;
  platform: string;        // windows, linux, macos, docker
  environment: string;     // production, staging, development
  status: string;          // online, offline, warning
  tags: string[];          // Custom tags for organization
  description?: string;    // Target description
  metadata?: any;          // Additional metadata
  last_seen?: string;      // Last health check
  created_at: string;
  updated_at: string;
}
```

---

## ⚡ Advanced Job Execution

### Enhanced Job Executor
The new `EnhancedJobExecutor` provides:
- **Visual Flow Execution**: Execute node-based workflows
- **Traditional Step Support**: Backward compatibility with step-based jobs
- **State Management**: Comprehensive execution state tracking
- **Error Handling**: Advanced error handling and recovery
- **Variable Passing**: Dynamic variable passing between steps
- **Connection Pooling**: Efficient resource management

### Execution Features
```python
class EnhancedJobExecutor:
    async def execute_job(self, job_definition, target_info)
    async def validate_job_definition(self, job_definition)
    def get_supported_step_types(self)
    def get_library_info(self)
```

### Job Definition Format
```json
{
  "name": "Enhanced Job",
  "description": "Job with visual flow",
  "flow": {
    "nodes": [
      {
        "id": "node-1",
        "type": "file.read",
        "name": "Read Config",
        "x": 100, "y": 100,
        "config": {
          "file_path": "/etc/config.json"
        },
        "inputs": 1,
        "outputs": 1
      }
    ],
    "connections": [
      {
        "id": "conn-1",
        "source_node_id": "node-1",
        "source_port": 0,
        "target_node_id": "node-2",
        "target_port": 0
      }
    ]
  }
}
```

---

## 🔒 Security Operations

### Encryption & Decryption
```python
# Encrypt sensitive data
{
  "type": "security.encrypt_data",
  "config": {
    "data": "sensitive information",
    "algorithm": "AES-256",
    "key": "encryption-key",
    "output_format": "base64"
  }
}

# Decrypt data
{
  "type": "security.decrypt_data",
  "config": {
    "encrypted_data": "base64-encrypted-data",
    "algorithm": "AES-256",
    "key": "encryption-key"
  }
}
```

### Vulnerability Scanning
```python
{
  "type": "security.vulnerability_scan",
  "config": {
    "target": "https://example.com",
    "scan_type": "comprehensive",
    "include_cve_check": true
  }
}
```

### Compliance Checking
```python
{
  "type": "security.compliance_check",
  "config": {
    "framework": "CIS",
    "target_system": "linux",
    "check_categories": ["access_control", "logging", "network"]
  }
}
```

---

## 🗄️ Database Operations

### Connection Management
```python
{
  "type": "database.connect",
  "config": {
    "connection_string": "postgresql://user:pass@host:5432/db",
    "database_type": "postgresql",
    "timeout_seconds": 30
  }
}
```

### Query Execution
```python
{
  "type": "database.query",
  "config": {
    "connection_id": "main_db",
    "sql": "SELECT * FROM users WHERE active = %(active)s",
    "parameters": {"active": true},
    "fetch_mode": "all"
  }
}
```

### Data Manipulation
```python
{
  "type": "database.execute",
  "config": {
    "connection_id": "main_db",
    "sql": "UPDATE users SET last_login = NOW() WHERE id = %(user_id)s",
    "parameters": {"user_id": 123}
  }
}
```

---

## 🔗 System Integration

### Service Architecture
```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Frontend      │    │  Step Library   │    │   Enhanced      │
│   Components    │◄──►│    Service      │◄──►│   Executor      │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
         ▼                       ▼                       ▼
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Job Service   │    │  Target Service │    │  Auth Service   │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

### API Endpoints
```
# Step Library Service
GET    /api/step-library/libraries
GET    /api/step-library/steps
POST   /api/step-library/execute
GET    /api/step-library/health

# Enhanced Job Management
POST   /api/jobs (with flow support)
GET    /api/jobs/:id/flow
POST   /api/jobs/:id/execute (enhanced)
GET    /api/jobs/:id/validate

# Enhanced Target Management
GET    /api/targets?platform=windows&status=online
POST   /api/targets/bulk-action
GET    /api/targets/groups
```

---

## 🎨 Frontend Components

### New Components
1. **EnhancedVisualJobBuilder**: Main visual job builder
2. **TargetSelector**: Advanced target selection with filtering
3. **JobManagement**: Comprehensive job management interface
4. **StepLibraryRegistry**: Step library browser and manager

### Component Features
- **Responsive Design**: Works on desktop and tablet devices
- **Real-Time Updates**: Live status updates and notifications
- **Drag & Drop**: Intuitive drag-and-drop interfaces
- **Advanced Filtering**: Multi-criteria filtering and search
- **Bulk Operations**: Select and operate on multiple items

### Navigation Updates
```typescript
// New routes added
/enhanced-jobs     // Enhanced job management
/step-library      // Step library registry
```

---

## 🧪 Testing & Validation

### Test Script
Run the comprehensive test suite:
```bash
./test-enhanced-system.sh
```

### Test Coverage
- ✅ Authentication system
- ✅ Step library functionality
- ✅ Visual job builder
- ✅ Enhanced job execution
- ✅ Database operations
- ✅ Security operations
- ✅ Target management
- ✅ Frontend components
- ✅ System integration

### Manual Testing
1. **Visual Job Builder**:
   - Navigate to `/enhanced-jobs`
   - Create a new job using the visual builder
   - Add nodes from different libraries
   - Connect nodes to create a workflow
   - Execute the job on selected targets

2. **Step Library Registry**:
   - Navigate to `/step-library`
   - Browse available libraries and steps
   - View step documentation and examples
   - Test step execution

3. **Enhanced Target Management**:
   - Navigate to `/targets-management`
   - Use advanced filtering options
   - Select multiple targets
   - Perform bulk operations

---

## 🚀 Getting Started

### 1. Start the System
```bash
./start-python-system.sh
```

### 2. Access the Enhanced Features
- **Enhanced Jobs**: http://localhost:8080/enhanced-jobs
- **Step Library**: http://localhost:8080/step-library
- **Target Management**: http://localhost:8080/targets-management

### 3. Create Your First Visual Job
1. Go to Enhanced Jobs
2. Click "Create New Job"
3. Drag nodes from the palette
4. Connect nodes to create a workflow
5. Configure each node
6. Select targets
7. Execute the job

### 4. Explore Step Libraries
1. Go to Step Library
2. Browse available libraries
3. View step definitions and examples
4. Test individual steps

---

## 📚 Additional Resources

### Documentation
- [API Documentation](./API_DOCUMENTATION.md)
- [Step Library Development Guide](./STEP_LIBRARY_GUIDE.md)
- [Visual Job Builder Guide](./VISUAL_BUILDER_GUIDE.md)

### Examples
- [Example Visual Jobs](./examples/visual-jobs/)
- [Custom Step Libraries](./examples/custom-libraries/)
- [Integration Examples](./examples/integrations/)

### Support
- GitHub Issues: [Report bugs and request features]
- Documentation: [Comprehensive guides and tutorials]
- Community: [Join our community discussions]

---

## 🎉 Conclusion

The enhanced OpsConductor system now provides:

1. **Visual Job Builder**: Intuitive drag-and-drop job creation
2. **Modular Architecture**: Pluggable step libraries for extensibility
3. **Enhanced Execution**: Advanced job execution with flow support
4. **Comprehensive Operations**: File, system, network, database, and security operations
5. **Advanced Target Management**: Sophisticated target selection and management
6. **Modern UI**: Responsive, user-friendly interface components
7. **Robust Testing**: Comprehensive test coverage and validation

The system is now ready for production use with enterprise-grade features and capabilities!