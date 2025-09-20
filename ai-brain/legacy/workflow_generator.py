"""
Workflow generator for AI Orchestrator
Generates valid workflow JSON from parsed NLP requests
"""
from typing import Dict, List, Any, Optional
from datetime import datetime
import uuid
import structlog

logger = structlog.get_logger()

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

    def generate_workflow_from_parsed(self, parsed_data: Dict[str, Any]) -> Dict[str, Any]:
        """Generate complete workflow from parsed NLP data"""
        try:
            # Extract data from parsed response
            operation = parsed_data.get("operation", "check")
            target_process = parsed_data.get("target_process")
            target_service = parsed_data.get("target_service")
            target_group = parsed_data.get("target_group", "all servers")
            target_os = parsed_data.get("target_os", "windows")
            confidence = parsed_data.get("confidence", 0.5)
            raw_text = parsed_data.get("raw_text", "")
            
            # Determine OS type
            os_type = target_os or 'generic'
            
            # Get operation mapping
            if operation not in self.operation_mappings:
                operation = 'check'  # Default fallback
            
            # Generate steps based on operation and OS
            step_generator = self.operation_mappings[operation].get(
                os_type, 
                self.operation_mappings[operation]['generic']
            )
            
            steps = step_generator(parsed_data)
            
            # Build complete workflow
            workflow = {
                'id': str(uuid.uuid4()),
                'name': self._generate_workflow_name(parsed_data),
                'description': f"AI-generated workflow: {raw_text}",
                'created_at': datetime.utcnow().isoformat(),
                'created_by': 'ai-orchestrator',
                'ai_generated': True,
                'source_request': raw_text,
                'confidence': confidence,
                'target_groups': [target_group] if target_group else [],
                'steps': steps,
                'metadata': {
                    'parsed_operation': operation,
                    'parsed_process': target_process,
                    'parsed_service': target_service,
                    'parsed_group': target_group,
                    'parsed_os': target_os,
                    'nlp_confidence': confidence
                }
            }
            
            logger.info("Generated workflow", 
                       workflow_id=workflow['id'], 
                       operation=operation,
                       steps=len(steps))
            
            return workflow
            
        except Exception as e:
            logger.error("Failed to generate workflow", error=str(e))
            # Return a basic fallback workflow
            return {
                'id': str(uuid.uuid4()),
                'name': 'Basic Check Workflow',
                'description': 'Fallback workflow due to generation error',
                'created_at': datetime.utcnow().isoformat(),
                'created_by': 'ai-orchestrator',
                'ai_generated': True,
                'source_request': parsed_data.get("raw_text", ""),
                'confidence': 0.1,
                'target_groups': [],
                'steps': [{
                    'id': str(uuid.uuid4()),
                    'name': 'Basic System Check',
                    'type': 'powershell',
                    'script': 'Write-Output "System check completed"',
                    'timeout': 30
                }],
                'metadata': {'error': str(e)}
            }

    def _generate_workflow_name(self, parsed_data: Dict[str, Any]) -> str:
        """Generate a descriptive workflow name"""
        parts = []
        
        operation = parsed_data.get("operation", "unknown")
        target_process = parsed_data.get("target_process")
        target_service = parsed_data.get("target_service")
        target_group = parsed_data.get("target_group")
        
        if operation != 'unknown':
            parts.append(operation.title())
        
        if target_process:
            parts.append(target_process)
        elif target_service:
            parts.append(target_service)
        
        if target_group:
            parts.append(f"on {target_group}")
        
        if not parts:
            parts = ["AI Generated Task"]
        
        return " ".join(parts)

    # Windows-specific step generators
    def _generate_windows_update_steps(self, parsed_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Generate Windows update steps"""
        steps = []
        
        target = parsed_data.get("target_process") or parsed_data.get("target_service") or "application"
        
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
        
        return steps

    def _generate_windows_restart_steps(self, parsed_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Generate Windows restart steps"""
        target = parsed_data.get("target_process") or parsed_data.get("target_service") or "service"
        
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

    def _generate_windows_stop_steps(self, parsed_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Generate Windows stop steps"""
        target = parsed_data.get("target_process") or parsed_data.get("target_service") or "service"
        
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

    def _generate_windows_start_steps(self, parsed_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Generate Windows start steps"""
        target = parsed_data.get("target_process") or parsed_data.get("target_service") or "service"
        
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

    def _generate_windows_check_steps(self, parsed_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Generate Windows check steps"""
        target = parsed_data.get("target_process") or parsed_data.get("target_service") or "service"
        target_group = parsed_data.get("target_group") or "Virtual Machines"
        
        steps = []
        
        # Step 1: Resolve target group
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
        
        # Step 2: Execute check
        steps.append({
            'id': str(uuid.uuid4()),
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
                'max_concurrent': 5
            },
            'continue_on_failure': True
        })
        
        return steps

    # Linux-specific step generators
    def _generate_linux_update_steps(self, parsed_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Generate Linux update steps"""
        target = parsed_data.get("target_process") or parsed_data.get("target_service") or "service"
        
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

    def _generate_linux_restart_steps(self, parsed_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Generate Linux restart steps"""
        target = parsed_data.get("target_service") or parsed_data.get("target_process") or "service"
        
        return [{
            'id': str(uuid.uuid4()),
            'name': f'Restart {target} on Linux',
            'type': 'bash',
            'script': f'''
#!/bin/bash
echo "Restarting {target}..."
sudo systemctl restart {target}
echo "✓ {target} restarted"
            '''.strip(),
            'timeout': 120,
            'continue_on_failure': False
        }]

    def _generate_linux_stop_steps(self, parsed_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Generate Linux stop steps"""
        target = parsed_data.get("target_service") or parsed_data.get("target_process") or "service"
        
        return [{
            'id': str(uuid.uuid4()),
            'name': f'Stop {target} on Linux',
            'type': 'bash',
            'script': f'''
#!/bin/bash
echo "Stopping {target}..."
sudo systemctl stop {target}
echo "✓ {target} stopped"
            '''.strip(),
            'timeout': 60,
            'continue_on_failure': False
        }]

    def _generate_linux_start_steps(self, parsed_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Generate Linux start steps"""
        target = parsed_data.get("target_service") or parsed_data.get("target_process") or "service"
        
        return [{
            'id': str(uuid.uuid4()),
            'name': f'Start {target} on Linux',
            'type': 'bash',
            'script': f'''
#!/bin/bash
echo "Starting {target}..."
sudo systemctl start {target}
echo "✓ {target} started"
            '''.strip(),
            'timeout': 60,
            'continue_on_failure': False
        }]

    def _generate_linux_check_steps(self, parsed_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Generate Linux check steps"""
        target = parsed_data.get("target_service") or parsed_data.get("target_process") or "service"
        
        return [{
            'id': str(uuid.uuid4()),
            'name': f'Check {target} Status on Linux',
            'type': 'bash',
            'script': f'''
#!/bin/bash
echo "Checking {target} status..."
systemctl status {target}
            '''.strip(),
            'timeout': 30,
            'continue_on_failure': True
        }]

    # Generic step generators
    def _generate_generic_update_steps(self, parsed_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Generate generic update steps"""
        target = parsed_data.get("target_process") or parsed_data.get("target_service") or "application"
        
        return [{
            'id': str(uuid.uuid4()),
            'name': f'Update {target}',
            'type': 'generic',
            'description': f'Update {target} - implementation depends on target system',
            'timeout': 300,
            'continue_on_failure': False
        }]

    def _generate_generic_restart_steps(self, parsed_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Generate generic restart steps"""
        target = parsed_data.get("target_process") or parsed_data.get("target_service") or "service"
        
        return [{
            'id': str(uuid.uuid4()),
            'name': f'Restart {target}',
            'type': 'generic',
            'description': f'Restart {target} - implementation depends on target system',
            'timeout': 120,
            'continue_on_failure': False
        }]

    def _generate_generic_stop_steps(self, parsed_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Generate generic stop steps"""
        target = parsed_data.get("target_process") or parsed_data.get("target_service") or "service"
        
        return [{
            'id': str(uuid.uuid4()),
            'name': f'Stop {target}',
            'type': 'generic',
            'description': f'Stop {target} - implementation depends on target system',
            'timeout': 60,
            'continue_on_failure': False
        }]

    def _generate_generic_start_steps(self, parsed_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Generate generic start steps"""
        target = parsed_data.get("target_process") or parsed_data.get("target_service") or "service"
        
        return [{
            'id': str(uuid.uuid4()),
            'name': f'Start {target}',
            'type': 'generic',
            'description': f'Start {target} - implementation depends on target system',
            'timeout': 60,
            'continue_on_failure': False
        }]

    def _generate_generic_check_steps(self, parsed_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Generate generic check steps"""
        target = parsed_data.get("target_process") or parsed_data.get("target_service") or "service"
        
        return [{
            'id': str(uuid.uuid4()),
            'name': f'Check {target} Status',
            'type': 'generic',
            'description': f'Check {target} status - implementation depends on target system',
            'timeout': 30,
            'continue_on_failure': True
        }]