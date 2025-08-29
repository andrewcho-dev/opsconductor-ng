# Windows Commands Feature Implementation

## Overview
Added a new category of Windows commands to the job builder that provides pre-built PowerShell commands for common Windows administration tasks.

## Features Implemented

### 1. Frontend Changes (`frontend/src/pages/Jobs.tsx`)
- Added "Add Windows Command" button to the job builder
- Created comprehensive form fields for the `windows.command` step type
- Implemented dynamic parameter forms based on command type selection
- Added validation and user-friendly interfaces for all command types

### 2. Backend Changes

#### Jobs Service (`jobs-service/main.py`)
- Added JSON schema validation for `windows.command` step type
- Defined required fields: `type`, `target`, `command_type`
- Added optional `parameters` object with validation for all command-specific parameters
- Added `timeoutSec` parameter support

#### Executor Service (`executor-service/main.py`)
- Added `_execute_windows_command()` method to handle Windows command execution
- Added `_generate_windows_command()` method to convert command types to PowerShell scripts
- Integrated with existing WinRM infrastructure

## Available Command Types

### 1. System Information (`system_info`)
- **Description**: Retrieves basic system information
- **Parameters**: None
- **PowerShell**: `Get-ComputerInfo` with selected properties

### 2. Disk Space (`disk_space`)
- **Description**: Checks disk space usage
- **Parameters**: 
  - `drive` (optional): Specific drive letter (e.g., "C:")
- **PowerShell**: `Get-WmiObject -Class Win32_LogicalDisk`

### 3. Running Services (`running_services`)
- **Description**: Lists running Windows services
- **Parameters**:
  - `service_filter` (optional): Filter services by name pattern
- **PowerShell**: `Get-Service` with filtering

### 4. Installed Programs (`installed_programs`)
- **Description**: Lists installed software
- **Parameters**: None
- **PowerShell**: `Get-WmiObject -Class Win32_Product`

### 5. Network Configuration (`network_config`)
- **Description**: Shows network interface configuration
- **Parameters**: None
- **PowerShell**: `Get-NetIPConfiguration`

### 6. Event Logs (`event_logs`)
- **Description**: Retrieves Windows event logs
- **Parameters**:
  - `log_name`: System, Application, Security, Setup (default: System)
  - `max_events`: Number of events to retrieve (1-1000, default: 50)
  - `level` (optional): Error, Warning, Information
- **PowerShell**: `Get-WinEvent`

### 7. Process List (`process_list`)
- **Description**: Lists running processes
- **Parameters**:
  - `process_filter` (optional): Filter processes by name
- **PowerShell**: `Get-Process`

### 8. Windows Updates (`windows_updates`)
- **Description**: Checks for Windows updates
- **Parameters**: None
- **PowerShell**: `Get-WUList` or `Get-HotFix` (fallback)

### 9. User Accounts (`user_accounts`)
- **Description**: Lists local user accounts
- **Parameters**: None
- **PowerShell**: `Get-LocalUser`

### 10. System Uptime (`system_uptime`)
- **Description**: Shows system boot time and uptime
- **Parameters**: None
- **PowerShell**: Custom script using `Get-CimInstance`

### 11. Registry Query (`registry_query`)
- **Description**: Queries Windows registry
- **Parameters**:
  - `registry_path` (required): Registry path (e.g., "HKLM:\\SOFTWARE\\Microsoft\\Windows\\CurrentVersion")
  - `value_name` (optional): Specific value name
- **PowerShell**: `Get-ItemProperty`

### 12. File Operations (`file_operations`)
- **Description**: File system operations
- **Parameters**:
  - `operation` (required): list, check_exists, get_size, get_info
  - `path` (required): File or directory path
  - `filter` (optional): File filter for list operation (e.g., "*.exe")
- **PowerShell**: `Get-ChildItem`, `Test-Path`, `Get-Item`

## Usage

### Creating a Windows Command Job

1. **Via Frontend**:
   - Navigate to Jobs page
   - Click "Create New Job"
   - Click "Add Windows Command" button
   - Select command type from dropdown
   - Fill in required parameters
   - Set timeout if needed
   - Save the job

2. **Via API**:
   ```json
   {
     "name": "System Info Check",
     "version": 1,
     "definition": {
       "name": "System Info Check",
       "version": 1,
       "parameters": {},
       "steps": [
         {
           "type": "windows.command",
           "target": "windows-server-01",
           "command_type": "system_info",
           "parameters": {},
           "timeoutSec": 120
         }
       ]
     },
     "is_active": true
   }
   ```

### Example Jobs

#### Disk Space Monitoring
```json
{
  "type": "windows.command",
  "target": "windows-server-01",
  "command_type": "disk_space",
  "parameters": {
    "drive": "C:"
  },
  "timeoutSec": 60
}
```

#### Event Log Analysis
```json
{
  "type": "windows.command",
  "target": "windows-server-01",
  "command_type": "event_logs",
  "parameters": {
    "log_name": "System",
    "max_events": 50,
    "level": "Error"
  },
  "timeoutSec": 120
}
```

#### Registry Check
```json
{
  "type": "windows.command",
  "target": "windows-server-01",
  "command_type": "registry_query",
  "parameters": {
    "registry_path": "HKLM:\\SOFTWARE\\Microsoft\\Windows\\CurrentVersion",
    "value_name": "ProductName"
  },
  "timeoutSec": 30
}
```

## Technical Implementation Details

### Schema Validation
The jobs service validates Windows command steps using JSON Schema:
- Ensures required fields are present
- Validates command_type against allowed values
- Validates parameters based on command type requirements
- Enforces parameter constraints (e.g., max_events range)

### PowerShell Generation
The executor service dynamically generates PowerShell commands:
- Uses template-based approach for consistency
- Handles parameter injection safely
- Includes error handling and output formatting
- Supports both parameterized and parameter-free commands

### Error Handling
- Invalid command types return descriptive error messages
- Missing required parameters are caught during validation
- PowerShell execution errors are captured and returned
- Timeout handling prevents hung commands

## Testing

A test script (`test-windows-commands.py`) is provided that:
- Tests all command types
- Validates parameter handling
- Confirms job creation via API
- Demonstrates usage patterns

Run the test:
```bash
python3 test-windows-commands.py
```

## Future Enhancements

Potential improvements:
1. **Custom Commands**: Allow users to input custom PowerShell scripts
2. **Command Templates**: Pre-built command templates for common scenarios
3. **Output Parsing**: Structured parsing of command outputs
4. **Conditional Logic**: Execute commands based on previous step results
5. **Bulk Operations**: Execute commands across multiple targets
6. **Scheduling**: Built-in scheduling for monitoring commands

## Security Considerations

- All PowerShell commands are pre-defined and validated
- No arbitrary code execution from user input
- Parameters are properly escaped and validated
- WinRM connections use existing credential management
- Timeout limits prevent resource exhaustion

## Dependencies

- Existing WinRM infrastructure
- PowerShell 5.1+ on target Windows systems
- Appropriate WinRM permissions for target operations
- Network connectivity to Windows targets

This feature significantly enhances the platform's Windows management capabilities by providing easy-to-use, pre-built commands for common administrative tasks.