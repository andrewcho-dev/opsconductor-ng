"""
Command Builder Utility
Generates platform-specific commands with parameter templating and security validation
"""

from typing import Dict, Any, List, Optional
import re
import shlex
import sys
import os

# Add shared module to path
sys.path.append('/home/opsconductor')
from shared.logging import get_logger

logger = get_logger("executor.command_builder")

class CommandBuilder:
    """Builds and validates platform-specific commands"""
    
    # Security: Dangerous command patterns to block
    DANGEROUS_PATTERNS = [
        r'rm\s+-rf\s+/',
        r'del\s+/[sq]\s+\*',
        r'format\s+[a-z]:',
        r'shutdown\s+',
        r'reboot',
        r'halt',
        r'init\s+[06]',
        r'dd\s+if=.*of=/dev/',
        r'mkfs\.',
        r'fdisk',
        r'parted',
        r'>\s*/dev/sd[a-z]',
        r'cat\s+.*>\s*/etc/',
        r'echo\s+.*>\s*/etc/',
        r'chmod\s+777',
        r'chown\s+.*root',
        r'sudo\s+su',
        r'su\s+-',
    ]
    
    def __init__(self):
        self.windows_commands = WindowsCommandGenerator()
        self.linux_commands = LinuxCommandGenerator()
    
    def generate_command(self, platform: str, command_type: str, parameters: Dict[str, Any]) -> str:
        """
        Generate platform-specific command
        
        Args:
            platform: Target platform ('windows' or 'linux')
            command_type: Type of command to generate
            parameters: Command parameters
            
        Returns:
            Generated command string
            
        Raises:
            ValueError: If platform or command_type is unsupported
            SecurityError: If command contains dangerous patterns
        """
        try:
            if platform.lower() == 'windows':
                command = self.windows_commands.generate(command_type, parameters)
            elif platform.lower() == 'linux':
                command = self.linux_commands.generate(command_type, parameters)
            else:
                raise ValueError(f"Unsupported platform: {platform}")
            
            # Security validation
            self._validate_command_security(command)
            
            logger.info(f"Generated {platform} command for {command_type}")
            return command
            
        except Exception as e:
            logger.error(f"Command generation failed: {e}")
            raise
    
    def _validate_command_security(self, command: str) -> None:
        """Validate command for security risks"""
        command_lower = command.lower()
        
        for pattern in self.DANGEROUS_PATTERNS:
            if re.search(pattern, command_lower):
                raise SecurityError(f"Command contains dangerous pattern: {pattern}")
        
        # Additional checks
        if len(command) > 10000:
            raise SecurityError("Command too long, potential security risk")
        
        # Check for command injection attempts
        injection_patterns = [';', '&&', '||', '|', '`', '$()']
        for pattern in injection_patterns:
            if pattern in command and not self._is_safe_usage(command, pattern):
                logger.warning(f"Potentially unsafe command pattern detected: {pattern}")

    def _is_safe_usage(self, command: str, pattern: str) -> bool:
        """Check if pattern usage is safe in context"""
        # This is a simplified check - in production, you'd want more sophisticated analysis
        safe_contexts = {
            '|': ['Format-Table', 'Format-List', 'Select-Object', 'Where-Object'],
            '&&': ['echo', 'mkdir'],
        }
        
        if pattern in safe_contexts:
            return any(context in command for context in safe_contexts[pattern])
        
        return False

class SecurityError(Exception):
    """Raised when command contains security risks"""
    pass

class WindowsCommandGenerator:
    """Generates Windows PowerShell commands"""
    
    def generate(self, command_type: str, parameters: Dict[str, Any]) -> str:
        """Generate Windows PowerShell command"""
        generators = {
            'system_info': self._system_info,
            'disk_space': self._disk_space,
            'running_services': self._running_services,
            'installed_programs': self._installed_programs,
            'network_config': self._network_config,
            'event_logs': self._event_logs,
            'process_list': self._process_list,
            'performance_counters': self._performance_counters,
            'registry_query': self._registry_query,
            'file_operations': self._file_operations,
            'user_accounts': self._user_accounts,
            'scheduled_tasks': self._scheduled_tasks,
            'windows_features': self._windows_features,
            'iis_info': self._iis_info,
            'custom_script': self._custom_script
        }
        
        generator = generators.get(command_type)
        if not generator:
            raise ValueError(f"Unsupported Windows command type: {command_type}")
        
        return generator(parameters)
    
    def _system_info(self, params: Dict[str, Any]) -> str:
        """Generate system information command"""
        return """
Get-ComputerInfo | Select-Object WindowsProductName, WindowsVersion, TotalPhysicalMemory, 
CsProcessors, CsSystemType, TimeZone, LastBootUpTime | Format-List
"""
    
    def _disk_space(self, params: Dict[str, Any]) -> str:
        """Generate disk space command"""
        drive = params.get('drive', '')
        if drive:
            return f"""Get-WmiObject -Class Win32_LogicalDisk -Filter "DeviceID='{drive}'" | 
Select-Object DeviceID, Size, FreeSpace, 
@{{Name='UsedSpace';Expression={{$_.Size - $_.FreeSpace}}}}, 
@{{Name='PercentFree';Expression={{[math]::Round(($_.FreeSpace / $_.Size) * 100, 2)}}}} | 
Format-Table -AutoSize"""
        else:
            return """Get-WmiObject -Class Win32_LogicalDisk | 
Select-Object DeviceID, Size, FreeSpace, 
@{Name='UsedSpace';Expression={$_.Size - $_.FreeSpace}}, 
@{Name='PercentFree';Expression={[math]::Round(($_.FreeSpace / $_.Size) * 100, 2)}} | 
Format-Table -AutoSize"""
    
    def _running_services(self, params: Dict[str, Any]) -> str:
        """Generate running services command"""
        service_filter = params.get('service_filter', '')
        if service_filter:
            return f"""Get-Service | Where-Object {{$_.Name -like '*{service_filter}*' -and $_.Status -eq 'Running'}} | 
Select-Object Name, Status, StartType | Format-Table -AutoSize"""
        else:
            return """Get-Service | Where-Object {$_.Status -eq 'Running'} | 
Select-Object Name, Status, StartType | Format-Table -AutoSize"""
    
    def _installed_programs(self, params: Dict[str, Any]) -> str:
        """Generate installed programs command"""
        return """
Get-WmiObject -Class Win32_Product | Select-Object Name, Version, Vendor, InstallDate | 
Sort-Object Name | Format-Table -AutoSize
"""
    
    def _network_config(self, params: Dict[str, Any]) -> str:
        """Generate network configuration command"""
        return """
Get-NetIPConfiguration | Select-Object InterfaceAlias, IPv4Address, IPv6Address, 
DNSServer | Format-List
"""
    
    def _event_logs(self, params: Dict[str, Any]) -> str:
        """Generate event logs command"""
        log_name = params.get('log_name', 'System')
        max_events = params.get('max_events', 50)
        level = params.get('level', '')
        
        if level:
            return f"""Get-WinEvent -LogName '{log_name}' -MaxEvents {max_events} | 
Where-Object {{$_.LevelDisplayName -eq '{level}'}} | 
Select-Object TimeCreated, Id, LevelDisplayName, Message | Format-Table -Wrap"""
        else:
            return f"""Get-WinEvent -LogName '{log_name}' -MaxEvents {max_events} | 
Select-Object TimeCreated, Id, LevelDisplayName, Message | Format-Table -Wrap"""
    
    def _process_list(self, params: Dict[str, Any]) -> str:
        """Generate process list command"""
        process_filter = params.get('process_filter', '')
        if process_filter:
            return f"""Get-Process | Where-Object {{$_.ProcessName -like '*{process_filter}*'}} | 
Select-Object ProcessName, Id, CPU, WorkingSet, StartTime | Format-Table -AutoSize"""
        else:
            return """Get-Process | Select-Object ProcessName, Id, CPU, WorkingSet, StartTime | 
Format-Table -AutoSize"""
    
    def _performance_counters(self, params: Dict[str, Any]) -> str:
        """Generate performance counters command"""
        counter = params.get('counter', '\\Processor(_Total)\\% Processor Time')
        samples = params.get('samples', 5)
        interval = params.get('interval', 1)
        
        return f"""Get-Counter -Counter '{counter}' -SampleInterval {interval} -MaxSamples {samples} | 
Select-Object -ExpandProperty CounterSamples | Format-Table -AutoSize"""
    
    def _registry_query(self, params: Dict[str, Any]) -> str:
        """Generate registry query command"""
        path = params.get('path', 'HKLM:\\SOFTWARE\\Microsoft\\Windows\\CurrentVersion')
        property_name = params.get('property', '')
        
        if property_name:
            return f"Get-ItemProperty -Path '{path}' -Name '{property_name}'"
        else:
            return f"Get-ItemProperty -Path '{path}'"
    
    def _file_operations(self, params: Dict[str, Any]) -> str:
        """Generate file operations command"""
        operation = params.get('operation', 'list')
        path = params.get('path', 'C:\\')
        
        if operation == 'list':
            return f"Get-ChildItem -Path '{path}' | Format-Table -AutoSize"
        elif operation == 'size':
            return f"Get-ChildItem -Path '{path}' -Recurse | Measure-Object -Property Length -Sum"
        else:
            raise ValueError(f"Unsupported file operation: {operation}")
    
    def _user_accounts(self, params: Dict[str, Any]) -> str:
        """Generate user accounts command"""
        return """Get-LocalUser | Select-Object Name, Enabled, LastLogon, 
PasswordLastSet, PasswordExpires | Format-Table -AutoSize"""
    
    def _scheduled_tasks(self, params: Dict[str, Any]) -> str:
        """Generate scheduled tasks command"""
        return """Get-ScheduledTask | Where-Object {$_.State -eq 'Ready'} | 
Select-Object TaskName, State, LastRunTime, NextRunTime | Format-Table -AutoSize"""
    
    def _windows_features(self, params: Dict[str, Any]) -> str:
        """Generate Windows features command"""
        return """Get-WindowsFeature | Where-Object {$_.InstallState -eq 'Installed'} | 
Select-Object Name, DisplayName, InstallState | Format-Table -AutoSize"""
    
    def _iis_info(self, params: Dict[str, Any]) -> str:
        """Generate IIS information command"""
        return """Import-Module WebAdministration; 
Get-Website | Select-Object Name, State, PhysicalPath, Bindings | Format-Table -AutoSize"""
    
    def _custom_script(self, params: Dict[str, Any]) -> str:
        """Generate custom PowerShell script"""
        script = params.get('script', '')
        if not script:
            raise ValueError("Custom script requires 'script' parameter")
        return script

class LinuxCommandGenerator:
    """Generates Linux shell commands"""
    
    def generate(self, command_type: str, parameters: Dict[str, Any]) -> str:
        """Generate Linux shell command"""
        generators = {
            'system_info': self._system_info,
            'disk_space': self._disk_space,
            'running_services': self._running_services,
            'installed_packages': self._installed_packages,
            'network_config': self._network_config,
            'log_analysis': self._log_analysis,
            'process_list': self._process_list,
            'memory_usage': self._memory_usage,
            'file_operations': self._file_operations,
            'user_accounts': self._user_accounts,
            'cron_jobs': self._cron_jobs,
            'docker_info': self._docker_info,
            'custom_script': self._custom_script
        }
        
        generator = generators.get(command_type)
        if not generator:
            raise ValueError(f"Unsupported Linux command type: {command_type}")
        
        return generator(parameters)
    
    def _system_info(self, params: Dict[str, Any]) -> str:
        """Generate system information command"""
        return "uname -a && cat /etc/os-release && free -h && df -h"
    
    def _disk_space(self, params: Dict[str, Any]) -> str:
        """Generate disk space command"""
        path = params.get('path', '/')
        return f"df -h {shlex.quote(path)}"
    
    def _running_services(self, params: Dict[str, Any]) -> str:
        """Generate running services command"""
        service_filter = params.get('service_filter', '')
        if service_filter:
            return f"systemctl list-units --type=service --state=running | grep {shlex.quote(service_filter)}"
        else:
            return "systemctl list-units --type=service --state=running"
    
    def _installed_packages(self, params: Dict[str, Any]) -> str:
        """Generate installed packages command"""
        package_manager = params.get('package_manager', 'auto')
        
        if package_manager == 'auto':
            return """
if command -v dpkg >/dev/null 2>&1; then
    dpkg -l
elif command -v rpm >/dev/null 2>&1; then
    rpm -qa
elif command -v pacman >/dev/null 2>&1; then
    pacman -Q
else
    echo "No supported package manager found"
fi
"""
        elif package_manager == 'apt':
            return "dpkg -l"
        elif package_manager == 'yum':
            return "rpm -qa"
        elif package_manager == 'pacman':
            return "pacman -Q"
        else:
            raise ValueError(f"Unsupported package manager: {package_manager}")
    
    def _network_config(self, params: Dict[str, Any]) -> str:
        """Generate network configuration command"""
        return "ip addr show && ip route show && cat /etc/resolv.conf"
    
    def _log_analysis(self, params: Dict[str, Any]) -> str:
        """Generate log analysis command"""
        log_file = params.get('log_file', '/var/log/syslog')
        lines = params.get('lines', 100)
        pattern = params.get('pattern', '')
        
        if pattern:
            return f"tail -n {lines} {shlex.quote(log_file)} | grep {shlex.quote(pattern)}"
        else:
            return f"tail -n {lines} {shlex.quote(log_file)}"
    
    def _process_list(self, params: Dict[str, Any]) -> str:
        """Generate process list command"""
        process_filter = params.get('process_filter', '')
        if process_filter:
            return f"ps aux | grep {shlex.quote(process_filter)}"
        else:
            return "ps aux"
    
    def _memory_usage(self, params: Dict[str, Any]) -> str:
        """Generate memory usage command"""
        return "free -h && cat /proc/meminfo"
    
    def _file_operations(self, params: Dict[str, Any]) -> str:
        """Generate file operations command"""
        operation = params.get('operation', 'list')
        path = params.get('path', '/')
        
        if operation == 'list':
            return f"ls -la {shlex.quote(path)}"
        elif operation == 'size':
            return f"du -sh {shlex.quote(path)}"
        elif operation == 'find':
            name = params.get('name', '*')
            return f"find {shlex.quote(path)} -name {shlex.quote(name)}"
        else:
            raise ValueError(f"Unsupported file operation: {operation}")
    
    def _user_accounts(self, params: Dict[str, Any]) -> str:
        """Generate user accounts command"""
        return "cat /etc/passwd | cut -d: -f1,3,4,5,6,7"
    
    def _cron_jobs(self, params: Dict[str, Any]) -> str:
        """Generate cron jobs command"""
        user = params.get('user', '')
        if user:
            return f"crontab -u {shlex.quote(user)} -l"
        else:
            return "crontab -l"
    
    def _docker_info(self, params: Dict[str, Any]) -> str:
        """Generate Docker information command"""
        return "docker info && docker ps -a && docker images"
    
    def _custom_script(self, params: Dict[str, Any]) -> str:
        """Generate custom shell script"""
        script = params.get('script', '')
        if not script:
            raise ValueError("Custom script requires 'script' parameter")
        return script