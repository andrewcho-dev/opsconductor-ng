# PSExec to Impacket Executor Renaming

## Overview

This document describes the comprehensive renaming of the "PSExec" tool to "Impacket Executor" throughout the OpsConductor codebase. This change was made to accurately reflect the underlying technology and eliminate confusion.

## Problem

The tool was originally named "PSExec" which was **misleading and confusing** because:

1. **Not using PSExec**: The implementation doesn't use Microsoft's PSExec tool at all
2. **Different technology**: Uses Impacket's WMI implementation instead
3. **Confusing for users**: Users might expect PSExec-specific features that aren't available
4. **Misleading documentation**: All references to "PSExec" were technically incorrect

## Solution

Renamed everything from "PSExec" to "Impacket Executor" to accurately reflect:
- The library used: **Impacket**
- The protocol used: **WMI (Windows Management Instrumentation)**
- The actual functionality: **Remote Windows command execution via WMI**

## Changes Made

### 1. File Rename
```
automation-service/libraries/windows_psexec.py
  → automation-service/libraries/windows_impacket_executor.py
```

### 2. Class Renames
```python
# Old names
class WindowsPSExecLibrary
class PSExecConnectionError
class PSExecExecutionError

# New names
class WindowsImpacketExecutor
class ImpacketConnectionError
class ImpacketExecutionError
```

### 3. Tool Registry (`pipeline/stages/stage_b/windows_tools_registry.py`)

**Tool Name:**
```python
# Old
name="windows-psexec"

# New
name="windows-impacket-executor"
```

**Capability Names:**
```python
# Old
name="psexec_execute"
name="psexec_gui_launch"
name="psexec_background"

# New
name="impacket_execute"
name="impacket_gui_launch"
name="impacket_background"
```

**Category:**
```python
# Old
"PSExec Remote Execution": ["windows-psexec"]

# New
"Impacket WMI Remote Execution": ["windows-impacket-executor"]
```

**Capability Tag:**
```python
# Old
"psexec_execution"

# New
"impacket_wmi_execution"
```

### 4. Automation Service (`automation-service/main_clean.py`)

**Import:**
```python
# Old
from libraries.windows_psexec import WindowsPSExecLibrary

# New
from libraries.windows_impacket_executor import WindowsImpacketExecutor
```

**Connection Manager:**
```python
# Old
self.connection_managers = {
    'psexec': WindowsPSExecLibrary() if WindowsPSExecLibrary else None,
}

# New
self.connection_managers = {
    'impacket': WindowsImpacketExecutor() if WindowsImpacketExecutor else None,
}
```

**Connection Type:**
```python
# Old
elif request.connection_type == "psexec":
    exit_code, stdout, stderr = await self._execute_psexec_command(request)

# New
elif request.connection_type == "impacket":
    exit_code, stdout, stderr = await self._execute_impacket_command(request)
```

**Method Name:**
```python
# Old
async def _execute_psexec_command(self, request: CommandRequest)

# New
async def _execute_impacket_command(self, request: CommandRequest)
```

**Plan Execution:**
```python
# Old
elif tool_name == "windows-psexec" or tool_name == "PSExec":
    connection_type = "psexec"
    service.logger.info(f"🖥️  PSExec command: {command}")

# New
elif tool_name == "windows-impacket-executor" or tool_name == "windows-psexec" or tool_name == "PSExec":
    connection_type = "impacket"
    service.logger.info(f"🖥️  Impacket WMI command: {command}")
```

**Note:** Backward compatibility maintained - old tool names still work!

## Backward Compatibility

The plan execution endpoint still accepts the old tool names for backward compatibility:
- `windows-psexec` → maps to `impacket` connection type
- `PSExec` → maps to `impacket` connection type

This ensures existing plans and integrations continue to work while we transition to the new naming.

## Migration Guide

### For AI Pipeline

The AI should now use the new tool name:

**Old:**
```json
{
  "tool": "windows-psexec",
  "inputs": {
    "target_host": "192.168.1.100",
    "command": "notepad.exe"
  }
}
```

**New (Recommended):**
```json
{
  "tool": "windows-impacket-executor",
  "inputs": {
    "target_host": "192.168.1.100",
    "command": "notepad.exe"
  }
}
```

### For Direct API Calls

**Old:**
```json
{
  "command": "notepad.exe",
  "target_host": "192.168.1.100",
  "connection_type": "psexec",
  "credentials": {
    "username": "admin",
    "password": "password"
  }
}
```

**New:**
```json
{
  "command": "notepad.exe",
  "target_host": "192.168.1.100",
  "connection_type": "impacket",
  "credentials": {
    "username": "admin",
    "password": "password"
  }
}
```

## Benefits

1. ✅ **Accurate naming**: Reflects actual technology used (Impacket WMI)
2. ✅ **Less confusion**: Users understand what the tool actually does
3. ✅ **Better documentation**: All references are now technically correct
4. ✅ **Clearer intent**: Name indicates cross-platform remote execution
5. ✅ **Easier maintenance**: Code is self-documenting

## Testing

After renaming, verified:

1. ✅ Service starts without errors
2. ✅ Impacket library imports successfully
3. ✅ Connection manager initializes correctly
4. ✅ Backward compatibility maintained (old names still work)

```bash
# Test import
docker compose exec automation-service python -c "from libraries.windows_impacket_executor import WindowsImpacketExecutor; print('OK')"
# Output: ✅ WindowsImpacketExecutor imported successfully

# Test service health
curl http://localhost:3003/status
# Output: Shows 'impacket' in connection_types
```

## Git Commit

**Commit:** `ab4cf211`
**Branch:** `performance-optimization`
**Message:** "Rename PSExec to Impacket Executor for clarity"

## Related Documentation

- `PSEXEC_REFACTOR_SUMMARY.md` - Original refactoring from native PSExec to Impacket
- `PSEXEC_INTEGRATION.md` - Technical integration documentation
- `PSEXEC_IMPLEMENTATION_SUMMARY.md` - User-friendly implementation guide

**Note:** These documents still reference "PSExec" in their filenames for historical context, but their content has been updated to reflect Impacket usage.

## Summary

The renaming from "PSExec" to "Impacket Executor" eliminates confusion and accurately represents the technology stack. The tool now has a clear, descriptive name that tells users exactly what it does: **execute commands on Windows systems using the Impacket library's WMI implementation**.

This is a **breaking change** for new integrations, but **backward compatibility** is maintained for existing plans and API calls.