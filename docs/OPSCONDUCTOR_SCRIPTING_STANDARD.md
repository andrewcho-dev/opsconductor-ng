# OpsConductor Universal Scripting Standard (OUSS)

## Executive Summary

The OpsConductor Universal Scripting Standard (OUSS) defines a comprehensive framework for AI-generated, cross-platform automation scripts that are secure, reliable, and maintainable. This standard enables the AI system to be a true "scripting polyglot" capable of generating enterprise-grade automation across Windows and Linux environments.

## Core Principles

### 1. **Script Reliability**
- Every script includes comprehensive error handling
- Built-in validation and verification steps
- Automatic rollback capabilities where applicable
- Timeout mechanisms for long-running operations

### 2. **Platform Intelligence**
- AI automatically selects optimal scripting language for each task
- Fallback methods for when primary approach fails
- Cross-platform compatibility where possible
- OS-specific optimizations

### 3. **Enterprise Security**
- No hardcoded credentials (always use OpsConductor credential system)
- Input validation and sanitization
- Audit logging for all operations
- Principle of least privilege

### 4. **Observability**
- Structured logging with timestamps
- Progress reporting for long operations
- Clear success/failure indicators
- Detailed error messages with context

## Scripting Language Matrix

### Windows Environments

| Language | Priority | Use Cases | Capabilities |
|----------|----------|-----------|--------------|
| **PowerShell** | 1 | Service management, file operations, registry, remote execution | Advanced object handling, .NET integration, rich error handling |
| **CMD/Batch** | 3 | Simple file operations, legacy system compatibility | Basic operations, wide compatibility |
| **WMI/CIM** | 2 | System information, remote management | Hardware queries, system configuration |
| **Registry Scripts** | 2 | Configuration management | Direct registry manipulation |
| **VBScript** | 4 | Legacy system support | COM object interaction |

### Linux Environments

| Language | Priority | Use Cases | Capabilities |
|----------|----------|-----------|--------------|
| **Bash** | 1 | System operations, file management, service control | Universal availability, system integration |
| **Python** | 1 | Complex logic, API integration, data processing | Advanced programming, library ecosystem |
| **systemctl** | 1 | Service management on systemd systems | Modern Linux service control |
| **Package Managers** | 2 | Software installation/updates | Distribution-specific package management |
| **AWK/SED** | 2 | Text processing, log analysis | Efficient text manipulation |

### Cross-Platform

| Language | Priority | Use Cases | Capabilities |
|----------|----------|-----------|--------------|
| **Python** | 1 | Complex automation, API calls, data processing | Cross-platform, extensive libraries |
| **PowerShell Core** | 2 | Cross-platform PowerShell operations | Unified scripting across OS |
| **Docker Scripts** | 2 | Containerized operations | Consistent execution environment |

## Script Structure Standard

### Universal Script Template
```bash
#!/bin/bash
# OpsConductor Generated Script
# Task: [TASK_DESCRIPTION]
# Target OS: [TARGET_OS]
# Generated: [TIMESTAMP]
# Job ID: [JOB_ID]

# OUSS Compliance: v1.0
set -euo pipefail  # Exit on error, undefined vars, pipe failures

# Global Configuration
SCRIPT_NAME="$(basename "$0")"
LOG_PREFIX="[OUSS][$(date '+%Y-%m-%d %H:%M:%S')]"
TEMP_DIR="/tmp/opsconductor_$$"
ROLLBACK_SCRIPT=""

# Logging Functions
log_info() {
    echo "$LOG_PREFIX [INFO] $1" | tee -a "$LOG_FILE"
}

log_error() {
    echo "$LOG_PREFIX [ERROR] $1" | tee -a "$LOG_FILE" >&2
}

log_success() {
    echo "$LOG_PREFIX [SUCCESS] $1" | tee -a "$LOG_FILE"
}

# Error Handling
cleanup() {
    local exit_code=$?
    log_info "Cleaning up temporary resources..."
    [ -d "$TEMP_DIR" ] && rm -rf "$TEMP_DIR"
    
    if [ $exit_code -ne 0 ] && [ -n "$ROLLBACK_SCRIPT" ]; then
        log_error "Script failed, executing rollback..."
        eval "$ROLLBACK_SCRIPT"
    fi
    
    exit $exit_code
}

trap cleanup EXIT

# Validation Functions
validate_prerequisites() {
    log_info "Validating prerequisites..."
    # Check required commands, permissions, etc.
}

validate_result() {
    log_info "Validating operation result..."
    # Verify the operation completed successfully
}

# Main Execution
main() {
    log_info "Starting $SCRIPT_NAME execution"
    
    validate_prerequisites
    
    # Main operation logic here
    
    validate_result
    
    log_success "Script completed successfully"
}

# Execute main function with all arguments
main "$@"
```

## Platform-Specific Standards

### Windows PowerShell Standard
```powershell
# OpsConductor Generated PowerShell Script
# OUSS Compliance: v1.0

[CmdletBinding()]
param(
    [Parameter(Mandatory=$false)]
    [string]$LogPath = "$env:TEMP\opsconductor_$(Get-Date -Format 'yyyyMMdd_HHmmss').log"
)

# Error Handling
$ErrorActionPreference = "Stop"
$ProgressPreference = "SilentlyContinue"

# Logging Functions
function Write-OussLog {
    param(
        [Parameter(Mandatory=$true)]
        [string]$Message,
        
        [Parameter(Mandatory=$false)]
        [ValidateSet("INFO", "WARNING", "ERROR", "SUCCESS")]
        [string]$Level = "INFO"
    )
    
    $timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    $logEntry = "[$timestamp] [OUSS] [$Level] $Message"
    
    Write-Host $logEntry
    Add-Content -Path $LogPath -Value $logEntry
}

# Validation Functions
function Test-Prerequisites {
    Write-OussLog "Validating prerequisites..." -Level "INFO"
    
    # Check PowerShell version
    if ($PSVersionTable.PSVersion.Major -lt 3) {
        throw "PowerShell 3.0 or higher required"
    }
    
    # Check execution policy
    $executionPolicy = Get-ExecutionPolicy
    if ($executionPolicy -eq "Restricted") {
        throw "PowerShell execution policy is too restrictive"
    }
    
    Write-OussLog "Prerequisites validated successfully" -Level "SUCCESS"
}

function Test-OperationResult {
    param(
        [Parameter(Mandatory=$true)]
        [scriptblock]$ValidationScript
    )
    
    Write-OussLog "Validating operation result..." -Level "INFO"
    
    try {
        $result = & $ValidationScript
        if ($result) {
            Write-OussLog "Operation validation successful" -Level "SUCCESS"
            return $true
        } else {
            Write-OussLog "Operation validation failed" -Level "ERROR"
            return $false
        }
    } catch {
        Write-OussLog "Operation validation error: $($_.Exception.Message)" -Level "ERROR"
        return $false
    }
}

# Main Execution Block
try {
    Write-OussLog "Starting PowerShell script execution" -Level "INFO"
    
    Test-Prerequisites
    
    # Main operation logic here
    
    Write-OussLog "Script completed successfully" -Level "SUCCESS"
    
} catch {
    Write-OussLog "Script failed: $($_.Exception.Message)" -Level "ERROR"
    
    # Execute rollback if defined
    if ($RollbackScript) {
        Write-OussLog "Executing rollback operations..." -Level "INFO"
        try {
            & $RollbackScript
            Write-OussLog "Rollback completed successfully" -Level "SUCCESS"
        } catch {
            Write-OussLog "Rollback failed: $($_.Exception.Message)" -Level "ERROR"
        }
    }
    
    throw
} finally {
    # Cleanup operations
    Write-OussLog "Performing cleanup operations..." -Level "INFO"
}
```

## AI Script Generation Patterns

### 1. Service Management Pattern
```python
class ServiceManagementPattern:
    """Generates scripts for service start/stop/restart operations"""
    
    def generate_windows_service_script(self, service_name: str, operation: str):
        return {
            'type': 'powershell',
            'script': f'''
# Service Management: {operation} {service_name}
$serviceName = "{service_name}"
$operation = "{operation}"

try {{
    $service = Get-Service -Name $serviceName -ErrorAction Stop
    
    switch ($operation) {{
        "stop" {{
            if ($service.Status -eq "Running") {{
                Write-OussLog "Stopping service $serviceName..." -Level "INFO"
                Stop-Service -Name $serviceName -Force -ErrorAction Stop
                
                # Wait for service to stop
                $timeout = 30
                $timer = 0
                while ((Get-Service -Name $serviceName).Status -ne "Stopped" -and $timer -lt $timeout) {{
                    Start-Sleep -Seconds 1
                    $timer++
                }}
                
                if ((Get-Service -Name $serviceName).Status -eq "Stopped") {{
                    Write-OussLog "Service $serviceName stopped successfully" -Level "SUCCESS"
                }} else {{
                    throw "Service failed to stop within timeout"
                }}
            }} else {{
                Write-OussLog "Service $serviceName is already stopped" -Level "INFO"
            }}
        }}
        
        "start" {{
            if ($service.Status -eq "Stopped") {{
                Write-OussLog "Starting service $serviceName..." -Level "INFO"
                Start-Service -Name $serviceName -ErrorAction Stop
                
                # Wait for service to start
                $timeout = 30
                $timer = 0
                while ((Get-Service -Name $serviceName).Status -ne "Running" -and $timer -lt $timeout) {{
                    Start-Sleep -Seconds 1
                    $timer++
                }}
                
                if ((Get-Service -Name $serviceName).Status -eq "Running") {{
                    Write-OussLog "Service $serviceName started successfully" -Level "SUCCESS"
                }} else {{
                    throw "Service failed to start within timeout"
                }}
            }} else {{
                Write-OussLog "Service $serviceName is already running" -Level "INFO"
            }}
        }}
        
        "restart" {{
            Write-OussLog "Restarting service $serviceName..." -Level "INFO"
            Restart-Service -Name $serviceName -Force -ErrorAction Stop
            Write-OussLog "Service $serviceName restarted successfully" -Level "SUCCESS"
        }}
    }}
    
}} catch {{
    Write-OussLog "Service operation failed: $($_.Exception.Message)" -Level "ERROR"
    throw
}}
''',
            'validation': f'Get-Service -Name "{service_name}" | Select-Object Name, Status',
            'rollback': self.generate_service_rollback(service_name, operation)
        }
```

### 2. File Operations Pattern
```python
class FileOperationsPattern:
    """Generates scripts for file copy, move, backup operations"""
    
    def generate_secure_file_copy(self, source: str, destination: str, backup: bool = True):
        return {
            'type': 'bash',
            'script': f'''#!/bin/bash
# Secure File Copy Operation
SOURCE="{source}"
DESTINATION="{destination}"
BACKUP_ENABLED={str(backup).lower()}

# Validate source file exists
if [ ! -f "$SOURCE" ]; then
    log_error "Source file does not exist: $SOURCE"
    exit 1
fi

# Create destination directory if needed
DEST_DIR=$(dirname "$DESTINATION")
if [ ! -d "$DEST_DIR" ]; then
    log_info "Creating destination directory: $DEST_DIR"
    mkdir -p "$DEST_DIR" || {{
        log_error "Failed to create destination directory"
        exit 1
    }}
fi

# Backup existing file if requested
if [ "$BACKUP_ENABLED" = "true" ] && [ -f "$DESTINATION" ]; then
    BACKUP_FILE="${{DESTINATION}}.backup.$(date +%Y%m%d_%H%M%S)"
    log_info "Creating backup: $BACKUP_FILE"
    cp "$DESTINATION" "$BACKUP_FILE" || {{
        log_error "Failed to create backup"
        exit 1
    }}
    ROLLBACK_SCRIPT="mv '$BACKUP_FILE' '$DESTINATION'"
fi

# Perform the copy
log_info "Copying file from $SOURCE to $DESTINATION"
cp "$SOURCE" "$DESTINATION" || {{
    log_error "File copy failed"
    exit 1
}}

# Verify copy
if [ -f "$DESTINATION" ]; then
    SOURCE_SIZE=$(stat -f%z "$SOURCE" 2>/dev/null || stat -c%s "$SOURCE" 2>/dev/null)
    DEST_SIZE=$(stat -f%z "$DESTINATION" 2>/dev/null || stat -c%s "$DESTINATION" 2>/dev/null)
    
    if [ "$SOURCE_SIZE" = "$DEST_SIZE" ]; then
        log_success "File copied successfully ($SOURCE_SIZE bytes)"
    else
        log_error "File size mismatch after copy"
        exit 1
    fi
else
    log_error "Destination file not found after copy"
    exit 1
fi
''',
            'validation': f'[ -f "{destination}" ] && echo "File exists" || echo "File missing"',
            'rollback': 'mv "$BACKUP_FILE" "$DESTINATION"' if backup else None
        }
```

### 3. Package Management Pattern
```python
class PackageManagementPattern:
    """Generates scripts for software installation and updates"""
    
    def generate_universal_package_install(self, package_name: str):
        return {
            'type': 'bash',
            'script': f'''#!/bin/bash
# Universal Package Installation
PACKAGE_NAME="{package_name}"

# Detect package manager
detect_package_manager() {{
    if command -v apt-get >/dev/null 2>&1; then
        echo "apt"
    elif command -v yum >/dev/null 2>&1; then
        echo "yum"
    elif command -v dnf >/dev/null 2>&1; then
        echo "dnf"
    elif command -v zypper >/dev/null 2>&1; then
        echo "zypper"
    elif command -v pacman >/dev/null 2>&1; then
        echo "pacman"
    else
        echo "unknown"
    fi
}}

# Check if package is installed
is_package_installed() {{
    local pkg="$1"
    local pm="$2"
    
    case "$pm" in
        "apt")
            dpkg -l | grep -q "^ii  $pkg "
            ;;
        "yum"|"dnf")
            rpm -qa | grep -q "^$pkg-"
            ;;
        "zypper")
            zypper se -i | grep -q "^i | $pkg"
            ;;
        "pacman")
            pacman -Q "$pkg" >/dev/null 2>&1
            ;;
        *)
            return 1
            ;;
    esac
}}

# Install package
install_package() {{
    local pkg="$1"
    local pm="$2"
    
    log_info "Installing $pkg using $pm..."
    
    case "$pm" in
        "apt")
            apt-get update -qq && apt-get install -y "$pkg"
            ;;
        "yum")
            yum install -y "$pkg"
            ;;
        "dnf")
            dnf install -y "$pkg"
            ;;
        "zypper")
            zypper install -y "$pkg"
            ;;
        "pacman")
            pacman -S --noconfirm "$pkg"
            ;;
        *)
            log_error "Unsupported package manager: $pm"
            return 1
            ;;
    esac
}}

# Main execution
main() {{
    log_info "Starting package installation for $PACKAGE_NAME"
    
    # Detect package manager
    PACKAGE_MANAGER=$(detect_package_manager)
    if [ "$PACKAGE_MANAGER" = "unknown" ]; then
        log_error "No supported package manager found"
        exit 1
    fi
    
    log_info "Detected package manager: $PACKAGE_MANAGER"
    
    # Check if already installed
    if is_package_installed "$PACKAGE_NAME" "$PACKAGE_MANAGER"; then
        log_info "Package $PACKAGE_NAME is already installed"
        exit 0
    fi
    
    # Install the package
    if install_package "$PACKAGE_NAME" "$PACKAGE_MANAGER"; then
        log_success "Package $PACKAGE_NAME installed successfully"
        
        # Verify installation
        if is_package_installed "$PACKAGE_NAME" "$PACKAGE_MANAGER"; then
            log_success "Installation verified"
        else
            log_error "Installation verification failed"
            exit 1
        fi
    else
        log_error "Package installation failed"
        exit 1
    fi
}}

main "$@"
''',
            'validation': f'command -v {package_name} >/dev/null 2>&1 && echo "Package available" || echo "Package not found"'
        }
```

## Script Security Standards

### 1. Credential Handling
```python
# NEVER do this in generated scripts:
# password = "hardcoded_password"  # ❌ FORBIDDEN

# ALWAYS do this:
# Credentials retrieved from OpsConductor credential system
def get_secure_credentials(target_id: int, credential_type: str):
    """Retrieve credentials from OpsConductor secure storage"""
    # Implementation calls asset service API
    pass
```

### 2. Input Validation
```bash
# Always validate inputs
validate_input() {
    local input="$1"
    local pattern="$2"
    
    if [[ ! "$input" =~ $pattern ]]; then
        log_error "Invalid input: $input"
        exit 1
    fi
}

# Example usage
validate_input "$SERVICE_NAME" '^[a-zA-Z0-9_-]+$'
```

### 3. Privilege Escalation
```bash
# Check if running with appropriate privileges
check_privileges() {
    if [ "$EUID" -ne 0 ] && [ "$REQUIRE_ROOT" = "true" ]; then
        log_error "This script requires root privileges"
        exit 1
    fi
}
```

## Integration with OpsConductor

### Script Execution Flow
1. **AI Analysis**: Analyze user request and determine required scripts
2. **Script Generation**: Generate platform-specific scripts using OUSS patterns
3. **Validation**: Validate generated scripts against security and syntax rules
4. **Deployment**: Deploy scripts to target systems via existing communication channels
5. **Execution**: Execute scripts with real-time progress monitoring
6. **Verification**: Run validation scripts to confirm success
7. **Cleanup**: Remove temporary files and perform cleanup operations

### Progress Reporting Integration
```python
# Scripts automatically report progress back to OpsConductor
def report_progress(job_id: int, step: str, progress: float, message: str):
    """Report script execution progress"""
    progress_data = {
        'job_id': job_id,
        'step': step,
        'progress': progress,
        'message': message,
        'timestamp': datetime.utcnow().isoformat()
    }
    
    # Send to OpsConductor progress broadcaster
    requests.post(f"{OPSCONDUCTOR_API}/jobs/{job_id}/progress", json=progress_data)
```

## Future Enhancements

### 1. Machine Learning Integration
- Learn from successful script patterns
- Optimize script generation based on historical performance
- Predict potential failure points and add preventive measures

### 2. Advanced Validation
- Static analysis of generated scripts
- Security vulnerability scanning
- Performance impact assessment

### 3. Template Evolution
- Community-contributed script patterns
- Industry-specific automation templates
- Compliance-focused script variants (SOX, HIPAA, etc.)

---

**The OpsConductor Universal Scripting Standard represents a new paradigm in automation where AI systems can generate enterprise-grade, secure, and reliable scripts across any platform, making complex system administration tasks as simple as describing them in natural language.**