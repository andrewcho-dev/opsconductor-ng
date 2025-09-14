# Phase 2: Windows Management Libraries & AI Integration

## 🎯 **Objective**
Connect the AI Service's workflow generation to the Automation Service's execution engine by building Windows/Linux management libraries.

## 🏗️ **Architecture Overview**
```
AI Service (3005) → Automation Service (3003) → Target Servers
     ↓                      ↓                        ↓
1. Generate Workflow    2. Execute via Libraries   3. PowerShell/SSH
2. Submit Job          3. Track Progress          4. Return Results
```

## 📋 **Implementation Tasks**

### Task 1: Windows PowerShell Library
**File**: `/automation-service/libraries/windows_powershell.py`
- **WinRM Connection Management** - Connect to Windows servers
- **PowerShell Script Execution** - Run generated PowerShell scripts
- **Error Handling & Logging** - Comprehensive error management
- **Credential Management** - Secure credential handling

### Task 2: Linux SSH Library  
**File**: `/automation-service/libraries/linux_ssh.py`
- **SSH Connection Management** - Connect to Linux servers
- **Bash Script Execution** - Run generated bash scripts
- **Error Handling & Logging** - Comprehensive error management
- **Credential Management** - Secure credential handling

### Task 3: Connection Manager Library
**File**: `/automation-service/libraries/connection_manager.py`
- **Credential Storage** - Encrypted credential management
- **Connection Pooling** - Efficient connection reuse
- **Target Resolution** - Resolve hostnames to IPs
- **Health Checking** - Test connectivity before execution

### Task 4: AI Service Integration
**File**: `/ai-service/automation_client.py`
- **Job Submission** - Submit AI-generated workflows to automation service
- **Status Monitoring** - Track job execution progress
- **Result Retrieval** - Get execution results and logs

### Task 5: End-to-End Testing
- **Integration Tests** - Test full AI → Automation → Execution flow
- **Mock Target Testing** - Test without real Windows/Linux servers
- **Error Scenario Testing** - Test failure handling and recovery

## 🔧 **Technical Specifications**

### Windows PowerShell Library
```python
class WindowsPowerShellLibrary:
    def execute_powershell(self, target_host, script, credentials):
        # WinRM connection and PowerShell execution
        pass
    
    def test_connection(self, target_host, credentials):
        # Test WinRM connectivity
        pass
```

### Linux SSH Library  
```python
class LinuxSSHLibrary:
    def execute_bash(self, target_host, script, credentials):
        # SSH connection and bash execution
        pass
    
    def test_connection(self, target_host, credentials):
        # Test SSH connectivity
        pass
```

## 🎯 **Success Criteria**
1. ✅ AI Service can submit workflows to Automation Service
2. ✅ Automation Service can execute PowerShell scripts on Windows targets
3. ✅ Automation Service can execute bash scripts on Linux targets
4. ✅ Full error handling and logging throughout the pipeline
5. ✅ End-to-end demo: "update nginx on web servers" → actual execution

## 📊 **Progress Tracking**
- [ ] Task 1: Windows PowerShell Library (0%)
- [ ] Task 2: Linux SSH Library (0%)  
- [ ] Task 3: Connection Manager Library (0%)
- [ ] Task 4: AI Service Integration (0%)
- [ ] Task 5: End-to-End Testing (0%)

**Overall Phase 2 Progress**: 0% → Target: 100%

## 🚀 **Next Steps**
1. Start with Windows PowerShell Library (most complex)
2. Build Connection Manager for credential handling
3. Create AI Service integration
4. Test with mock targets first
5. Add Linux SSH support
6. End-to-end integration testing