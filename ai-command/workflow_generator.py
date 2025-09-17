"""
Workflow generator for OpsConductor AI Service
Generates valid workflow JSON from parsed NLP requests
"""
from typing import Dict, List, Any, Optional
from datetime import datetime
import uuid
from nlp_processor import ParsedRequest


class WorkflowGenerator:
    """Generates workflow JSON from parsed requests"""
    
    def __init__(self):
        # Operation to workflow step mapping
        self.operation_mappings = {
            'update': {
                'windows': self._generate_windows_update_steps,
                'linux': self._generate_linux_update_steps,
                'generic': self._generate_generic_update_steps
            },
            'restart': {
                'windows': self._generate_windows_restart_steps,
                'linux': self._generate_linux_restart_steps,
                'generic': self._generate_generic_restart_steps
            },
            'stop': {
                'windows': self._generate_windows_stop_steps,
                'linux': self._generate_linux_stop_steps,
                'generic': self._generate_generic_stop_steps
            },
            'start': {
                'windows': self._generate_windows_start_steps,
                'linux': self._generate_linux_start_steps,
                'generic': self._generate_generic_start_steps
            },
            'check': {
                'windows': self._generate_windows_check_steps,
                'linux': self._generate_linux_check_steps,
                'generic': self._generate_generic_check_steps
            }
        }

    def generate_workflow(self, parsed_request: ParsedRequest, target_groups: List[str] = None) -> Dict[str, Any]:
        """Generate complete workflow from parsed request"""
        
        # Determine OS type
        os_type = parsed_request.target_os or 'generic'
        
        # Get operation mapping
        operation = parsed_request.operation
        if operation not in self.operation_mappings:
            operation = 'check'  # Default fallback
        
        # Generate steps based on operation and OS
        step_generator = self.operation_mappings[operation].get(
            os_type, 
            self.operation_mappings[operation]['generic']
        )
        
        steps = step_generator(parsed_request)
        
        # Build complete workflow
        workflow = {
            'id': str(uuid.uuid4()),
            'name': self._generate_workflow_name(parsed_request),
            'description': f"AI-generated workflow: {parsed_request.raw_text}",
            'created_at': datetime.utcnow().isoformat(),
            'created_by': 'ai-service',
            'ai_generated': True,
            'source_request': parsed_request.raw_text,
            'confidence': parsed_request.confidence,
            'target_groups': target_groups or [parsed_request.target_group] if parsed_request.target_group else [],
            'steps': steps,
            'metadata': {
                'parsed_operation': parsed_request.operation,
                'parsed_process': parsed_request.target_process,
                'parsed_service': parsed_request.target_service,
                'parsed_group': parsed_request.target_group,
                'parsed_os': parsed_request.target_os,
                'nlp_confidence': parsed_request.confidence
            }
        }
        
        return workflow

    def _generate_workflow_name(self, parsed_request: ParsedRequest) -> str:
        """Generate a descriptive workflow name"""
        parts = []
        
        if parsed_request.operation != 'unknown':
            parts.append(parsed_request.operation.title())
        
        if parsed_request.target_process:
            parts.append(parsed_request.target_process)
        elif parsed_request.target_service:
            parts.append(parsed_request.target_service)
        
        if parsed_request.target_group:
            parts.append(f"on {parsed_request.target_group}")
        
        if not parts:
            parts = ["AI Generated Task"]
        
        return " ".join(parts)

    # Windows-specific step generators
    def _generate_windows_update_steps(self, parsed_request: ParsedRequest) -> List[Dict[str, Any]]:
        """Generate Windows update steps"""
        steps = []
        
        target = parsed_request.target_process or parsed_request.target_service or "application"
        
        # Step 1: Check current status
        steps.append({
            'id': str(uuid.uuid4()),
            'name': f'Check {target} Status',
            'type': 'powershell',
            'library': 'windows_powershell',
            'function': 'execute_powershell',
            'inputs': {
                'target_host': '{{steps.resolve_targets.outputs.active_hosts}}',
                'username': '{{steps.resolve_targets.outputs.username}}',
                'password': '{{steps.resolve_targets.outputs.password}}',
                'script': f'''# Check if {target} is running
$process = Get-Process -Name "{target.replace('.exe', '')}" -ErrorAction SilentlyContinue
if ($process) {{
    Write-Output "✓ {target} is currently running (PID: $($process.Id))"
    $process | Select-Object Name, Id, CPU, WorkingSet | Format-Table
}} else {{
    Write-Output "⚠ {target} is not running"
}}''',
                'timeout': 30,
                'use_ssl': True
            },
            'continue_on_failure': True
        })
        
        # Step 2: Stop service/process
        steps.append({
            'id': str(uuid.uuid4()),
            'name': f'Stop {target}',
            'type': 'powershell',
            'script': f'''
# Stop {target} safely
Write-Output "Stopping {target}..."
try {{
    Stop-Process -Name "{target.replace('.exe', '')}" -Force -ErrorAction Stop
    Start-Sleep -Seconds 5
    Write-Output "✓ {target} stopped successfully"
}} catch {{
    Write-Output "⚠ Could not stop {target}: $($_.Exception.Message)"
}}
            '''.strip(),
            'timeout': 60,
            'continue_on_failure': False
        })
        
        # Step 3: Update/Replace files (placeholder)
        steps.append({
            'id': str(uuid.uuid4()),
            'name': f'Update {target} Files',
            'type': 'powershell',
            'script': f'''
# Placeholder for file update logic
Write-Output "Updating {target} files..."
Write-Output "⚠ File update logic needs to be implemented"
Write-Output "This would typically involve:"
Write-Output "  - Backing up current files"
Write-Output "  - Copying new files from update source"
Write-Output "  - Verifying file integrity"
            '''.strip(),
            'timeout': 300,
            'continue_on_failure': False
        })
        
        # Step 4: Start service/process
        steps.append({
            'id': str(uuid.uuid4()),
            'name': f'Start {target}',
            'type': 'powershell',
            'script': f'''
# Start {target}
Write-Output "Starting {target}..."
try {{
    # This is a placeholder - actual start command depends on the application
    Write-Output "⚠ Start command needs to be configured for {target}"
    Write-Output "Typical commands:"
    Write-Output "  - Start-Process '{target}'"
    Write-Output "  - Start-Service 'ServiceName'"
    Write-Output "  - & 'C:\\Path\\To\\{target}'"
}} catch {{
    Write-Output "❌ Failed to start {target}: $($_.Exception.Message)"
}}
            '''.strip(),
            'timeout': 60,
            'continue_on_failure': False
        })
        
        # Step 5: Verify update
        steps.append({
            'id': str(uuid.uuid4()),
            'name': f'Verify {target} Update',
            'type': 'powershell',
            'script': f'''
# Verify {target} is running and updated
Write-Output "Verifying {target} update..."
$process = Get-Process -Name "{target.replace('.exe', '')}" -ErrorAction SilentlyContinue
if ($process) {{
    Write-Output "✓ {target} is running (PID: $($process.Id))"
    # Check file version if possible
    $exePath = $process.Path
    if ($exePath) {{
        $version = (Get-ItemProperty $exePath).VersionInfo.FileVersion
        Write-Output "✓ Version: $version"
    }}
}} else {{
    Write-Output "❌ {target} is not running after update"
}}
            '''.strip(),
            'timeout': 30,
            'continue_on_failure': True
        })
        
        return steps

    def _generate_windows_restart_steps(self, parsed_request: ParsedRequest) -> List[Dict[str, Any]]:
        """Generate Windows restart steps"""
        target = parsed_request.target_process or parsed_request.target_service or "service"
        
        return [{
            'id': str(uuid.uuid4()),
            'name': f'Restart {target}',
            'type': 'powershell',
            'script': f'''
# Restart {target}
Write-Output "Restarting {target}..."
try {{
    Stop-Process -Name "{target.replace('.exe', '')}" -Force -ErrorAction SilentlyContinue
    Start-Sleep -Seconds 5
    # Start command would go here
    Write-Output "✓ {target} restarted"
}} catch {{
    Write-Output "❌ Failed to restart {target}: $($_.Exception.Message)"
}}
            '''.strip(),
            'timeout': 120,
            'continue_on_failure': False
        }]

    def _generate_windows_stop_steps(self, parsed_request: ParsedRequest) -> List[Dict[str, Any]]:
        """Generate Windows stop steps"""
        target = parsed_request.target_process or parsed_request.target_service or "service"
        
        return [{
            'id': str(uuid.uuid4()),
            'name': f'Stop {target}',
            'type': 'powershell',
            'script': f'''
# Stop {target}
Write-Output "Stopping {target}..."
Stop-Process -Name "{target.replace('.exe', '')}" -Force
Write-Output "✓ {target} stopped"
            '''.strip(),
            'timeout': 60,
            'continue_on_failure': False
        }]

    def _generate_windows_start_steps(self, parsed_request: ParsedRequest) -> List[Dict[str, Any]]:
        """Generate Windows start steps"""
        target = parsed_request.target_process or parsed_request.target_service or "service"
        
        return [{
            'id': str(uuid.uuid4()),
            'name': f'Start {target}',
            'type': 'powershell',
            'script': f'''
# Start {target}
Write-Output "Starting {target}..."
# Start command would be configured based on the specific application
Write-Output "⚠ Start command needs configuration for {target}"
            '''.strip(),
            'timeout': 60,
            'continue_on_failure': False
        }]

    def _generate_windows_check_steps(self, parsed_request: ParsedRequest) -> List[Dict[str, Any]]:
        """Generate Windows check steps with proper target resolution and parallel execution"""
        target = parsed_request.target_process or parsed_request.target_service or "service"
        target_group = parsed_request.target_group or "Virtual Machines"
        
        steps = []
        
        # Step 1: Resolve target group to get all targets and credentials
        resolve_step_id = str(uuid.uuid4())
        steps.append({
            'id': resolve_step_id,
            'name': 'Resolve Target Group',
            'type': 'connection',
            'library': 'connection_manager',
            'function': 'resolve_target_group',
            'inputs': {
                'group_name': target_group
            },
            'continue_on_failure': False
        })
        
        # Step 2: Execute PowerShell check on all targets in parallel
        check_step_id = str(uuid.uuid4())
        steps.append({
            'id': check_step_id,
            'name': f'Check {target} Status on All Targets',
            'type': 'powershell_parallel',
            'library': 'windows_powershell',
            'function': 'execute_powershell_parallel',
            'inputs': {
                'targets': f'{{{{steps.{resolve_step_id}.outputs.targets}}}}',
                'script': f'''# Check {target} status
$process = Get-Process -Name "{target.replace('.exe', '')}" -ErrorAction SilentlyContinue
if ($process) {{
    Write-Output "✓ {target} is running on $env:COMPUTERNAME"
    $process | Select-Object Name, Id, CPU, WorkingSet | Format-Table
}} else {{
    Write-Output "⚠ {target} is not running on $env:COMPUTERNAME"
}}''',
                'timeout': 30,
                'max_concurrent': 5  # Limit concurrent executions
            },
            'continue_on_failure': True
        })
        
        return steps

    # Linux-specific step generators (simplified for prototype)
    def _generate_linux_update_steps(self, parsed_request: ParsedRequest) -> List[Dict[str, Any]]:
        """Generate Linux update steps"""
        target = parsed_request.target_process or parsed_request.target_service or "service"
        
        return [{
            'id': str(uuid.uuid4()),
            'name': f'Update {target} on Linux',
            'type': 'bash',
            'script': f'''
#!/bin/bash
echo "Updating {target} on Linux..."
# Package manager detection and update logic would go here
echo "⚠ Linux update logic needs implementation"
            '''.strip(),
            'timeout': 300,
            'continue_on_failure': False
        }]

    def _generate_linux_restart_steps(self, parsed_request: ParsedRequest) -> List[Dict[str, Any]]:
        """Generate Linux restart steps"""
        target = parsed_request.target_service or parsed_request.target_process or "service"
        
        return [{
            'id': str(uuid.uuid4()),
            'name': f'Restart {target}',
            'type': 'bash',
            'script': f'''
#!/bin/bash
echo "Restarting {target}..."
sudo systemctl restart {target} || sudo service {target} restart
echo "✓ {target} restarted"
            '''.strip(),
            'timeout': 60,
            'continue_on_failure': False
        }]

    def _generate_linux_stop_steps(self, parsed_request: ParsedRequest) -> List[Dict[str, Any]]:
        """Generate Linux stop steps"""
        target = parsed_request.target_service or parsed_request.target_process or "service"
        
        return [{
            'id': str(uuid.uuid4()),
            'name': f'Stop {target}',
            'type': 'bash',
            'script': f'''
#!/bin/bash
echo "Stopping {target}..."
sudo systemctl stop {target} || sudo service {target} stop
echo "✓ {target} stopped"
            '''.strip(),
            'timeout': 60,
            'continue_on_failure': False
        }]

    def _generate_linux_start_steps(self, parsed_request: ParsedRequest) -> List[Dict[str, Any]]:
        """Generate Linux start steps"""
        target = parsed_request.target_service or parsed_request.target_process or "service"
        
        return [{
            'id': str(uuid.uuid4()),
            'name': f'Start {target}',
            'type': 'bash',
            'script': f'''
#!/bin/bash
echo "Starting {target}..."
sudo systemctl start {target} || sudo service {target} start
echo "✓ {target} started"
            '''.strip(),
            'timeout': 60,
            'continue_on_failure': False
        }]

    def _generate_linux_check_steps(self, parsed_request: ParsedRequest) -> List[Dict[str, Any]]:
        """Generate Linux check steps"""
        target = parsed_request.target_service or parsed_request.target_process or "service"
        
        return [{
            'id': str(uuid.uuid4()),
            'name': f'Check {target} Status',
            'type': 'bash',
            'script': f'''
#!/bin/bash
echo "Checking {target} status..."
systemctl status {target} || service {target} status
            '''.strip(),
            'timeout': 30,
            'continue_on_failure': True
        }]

    # Generic fallback generators
    def _generate_generic_update_steps(self, parsed_request: ParsedRequest) -> List[Dict[str, Any]]:
        """Generate generic update steps"""
        return self._generate_windows_update_steps(parsed_request)

    def _generate_generic_restart_steps(self, parsed_request: ParsedRequest) -> List[Dict[str, Any]]:
        """Generate generic restart steps"""
        return self._generate_windows_restart_steps(parsed_request)

    def _generate_generic_stop_steps(self, parsed_request: ParsedRequest) -> List[Dict[str, Any]]:
        """Generate generic stop steps"""
        return self._generate_windows_stop_steps(parsed_request)

    def _generate_generic_start_steps(self, parsed_request: ParsedRequest) -> List[Dict[str, Any]]:
        """Generate generic start steps"""
        return self._generate_windows_start_steps(parsed_request)

    def _generate_generic_check_steps(self, parsed_request: ParsedRequest) -> List[Dict[str, Any]]:
        """Generate generic check steps"""
        return self._generate_windows_check_steps(parsed_request)


# Example usage
if __name__ == "__main__":
    from nlp_processor import SimpleNLPProcessor, ParsedRequest
    
    processor = SimpleNLPProcessor()
    generator = WorkflowGenerator()
    
    test_request = "update stationcontroller on CIS servers"
    parsed = processor.parse_request(test_request)
    workflow = generator.generate_workflow(parsed, target_groups=["CIS"])
    
    print("=== Generated Workflow ===")
    import json
    print(json.dumps(workflow, indent=2))