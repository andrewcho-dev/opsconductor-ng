# Tool Database Fix - Windows Impacket Executor

## Problem Identified

When you asked the AI to "launch notepad.exe on 192.168.50.210", the execution failed with:
```
❌ Execution failed: None
Error: credentials (username/password) are required for PowerShell execution
```

### Root Cause Analysis

1. **AI Selected Wrong Tool**: The AI selected `Invoke-Command` (PowerShell) instead of `windows-impacket-executor`
2. **Tool Not in Database**: The `windows-impacket-executor` tool was defined in the code registry but **NOT loaded into the database**
3. **Database Out of Sync**: The tool catalog database only had 114 tools, missing all 21 Windows tools from the registry

### Why This Happened

The OpsConductor AI pipeline uses a **database-backed tool catalog** for tool selection. The Windows tools were defined in:
- `/home/opsconductor/opsconductor-ng/pipeline/stages/stage_b/windows_tools_registry.py`

But they were **never loaded into the PostgreSQL database** at:
- `tool_catalog.tools` table

The AI could only see tools that were in the database, so it selected the closest match it could find: `Invoke-Command`.

## Solution Implemented

### 1. Created Tool Loading Script

Created `/home/opsconductor/opsconductor-ng/load_windows_tools.py` to:
- Load all Windows tools from the registry
- Insert them into the database with proper structure
- Create capabilities and patterns for each tool

### 2. Loaded All Windows Tools

Executed the script and successfully loaded **21 Windows tools**:
```
✅ windows-service-manager
✅ windows-process-manager
✅ windows-user-manager
✅ windows-registry-manager
✅ windows-filesystem-manager
✅ windows-disk-manager
✅ windows-network-manager
✅ windows-firewall-manager
✅ windows-eventlog-manager
✅ windows-performance-monitor
✅ windows-update-manager
✅ windows-task-scheduler
✅ windows-iis-manager
✅ windows-sql-manager
✅ windows-ad-manager
✅ windows-certificate-manager
✅ windows-powershell-executor
✅ windows-system-info
✅ windows-rdp-manager
✅ windows-printer-manager
✅ windows-impacket-executor  ← THE KEY ONE!
```

### 3. Disabled Broken Tool

Disabled the `Invoke-Command` tool that was causing confusion:
```sql
UPDATE tool_catalog.tools SET enabled = false WHERE tool_name = 'Invoke-Command';
```

### 4. Restarted AI Pipeline

Restarted the AI pipeline to reload tools from the database:
```bash
docker compose restart ai-pipeline
```

## Verification

### Database Check
```bash
$ docker compose exec -T postgres psql -U opsconductor -d opsconductor -c \
  "SELECT tool_name, description FROM tool_catalog.tools WHERE tool_name = 'windows-impacket-executor';"

         tool_name         |                                                        description                                                         
---------------------------+----------------------------------------------------------------------------------------------------------------------------
 windows-impacket-executor | Execute commands and GUI applications on remote Windows systems using Impacket WMI with support for non-blocking execution
```

### Capabilities Check
```bash
$ docker compose exec -T postgres psql -U opsconductor -d opsconductor -c \
  "SELECT tc.capability_name FROM tool_catalog.tool_capabilities tc JOIN tool_catalog.tools t ON tc.tool_id = t.id WHERE t.tool_name = 'windows-impacket-executor';"

   capability_name   
---------------------
 impacket_execute    
 impacket_gui_launch 
 impacket_background
```

### Tool Loading Test
```bash
$ python3 test_tool_loading.py

📚 Total tools loaded: 135
🪟 Windows tools: 21
✅ Found windows-impacket-executor!
   Description: Execute commands and GUI applications on remote Windows systems using Impacket WMI with support for non-blocking execution
   Capabilities: ['impacket_background', 'impacket_execute', 'impacket_gui_launch']
```

## What to Test Next

### 1. Try the Original Request Again

Ask the AI:
```
launch notepad.exe on 192.168.50.210
```

**Expected Behavior:**
- AI should now select `windows-impacket-executor` instead of `Invoke-Command`
- The tool should be recognized by the automation service
- Execution should proceed (though it may still fail if credentials are missing)

### 2. Check the Logs

Monitor the AI pipeline logs to see which tool is selected:
```bash
docker compose logs ai-pipeline --tail 100 | grep -A 5 "TOOLS SELECTED"
```

You should see:
```
🔧 TOOLS SELECTED BY LLM:
   1. windows-impacket-executor (confidence: 0.XX)
```

### 3. Verify Automation Service Recognizes the Tool

Check automation service logs:
```bash
docker compose logs automation-service --tail 50
```

You should NOT see:
```
WARNING - Tool definition not found for 'Invoke-Command'
```

## Important Notes

### Credentials Still Required

Even with the correct tool selected, you'll still need to provide credentials for the Windows machine. The error will change from:
```
❌ credentials (username/password) are required for PowerShell execution
```

To something like:
```
❌ credentials (username/password) are required for Impacket execution
```

This is expected! You need to either:
1. Add credentials to the asset database for 192.168.50.210
2. Provide credentials in the request
3. Configure default credentials

### Tool Examples

The `windows-impacket-executor` tool has these examples in the database:
1. **Launch notepad (non-blocking)**: target=192.168.1.100, command=notepad.exe, wait=false
2. Run command and get output: target=192.168.1.100, command='ipconfig /all', wait=true
3. Launch GUI app: target=192.168.1.100, command=calc.exe, wait=false
4. Execute with domain account: target=192.168.1.100, command=cmd.exe, domain=CORP, username=admin

The AI should now recognize that "launch notepad" matches example #1 perfectly!

## Files Created

1. `/home/opsconductor/opsconductor-ng/load_windows_tools.py` - Script to load Windows tools into database
2. `/home/opsconductor/opsconductor-ng/test_tool_loading.py` - Script to verify tools are loaded
3. `/home/opsconductor/opsconductor-ng/TOOL_DATABASE_FIX.md` - This documentation

## Next Steps for Development

### 1. Automate Tool Loading

Consider adding a startup script or migration that automatically loads tools from the registry into the database when the system starts.

### 2. Tool Sync Mechanism

Create a mechanism to keep the database in sync with the code registry:
- Detect when new tools are added to the registry
- Automatically update the database
- Version control for tool definitions

### 3. Tool Validation

Add validation to ensure:
- All tools in the database have corresponding implementations
- All tools in the code registry are in the database
- Tool metadata is consistent

### 4. Better Error Messages

When a tool is selected but not found in the automation service, provide a clearer error message that helps diagnose the issue.

## Summary

✅ **FIXED**: Windows tools (including `windows-impacket-executor`) are now in the database
✅ **FIXED**: AI can now see and select the correct tool for launching GUI applications
✅ **FIXED**: Disabled the broken `Invoke-Command` tool that was causing confusion
✅ **READY**: System is ready to test the original request again

The AI should now correctly select `windows-impacket-executor` when you ask it to launch notepad or other GUI applications on Windows machines!