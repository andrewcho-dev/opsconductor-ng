"""
Protocol Manager for AI Orchestrator
Simplified version that delegates to automation service for actual protocol operations
"""
import structlog
from typing import Dict, Any, Optional
import httpx
import os

logger = structlog.get_logger()

class ProtocolManager:
    """Manages protocol operations by delegating to automation service"""
    
    def __init__(self):
        self.automation_service_url = os.getenv("AUTOMATION_SERVICE_URL", "http://automation-service:3003")
        
        # Protocol capabilities
        self.capabilities = {
            "snmp": {
                "name": "SNMP",
                "description": "Network device monitoring and management",
                "operations": [
                    "get_system_info",
                    "get_interface_stats", 
                    "get_cpu_usage",
                    "get_memory_usage",
                    "walk_oid"
                ]
            },
            "smtp": {
                "name": "SMTP",
                "description": "Email notifications and alerts",
                "operations": [
                    "send_email",
                    "send_alert",
                    "test_connection"
                ]
            },
            "ssh": {
                "name": "SSH",
                "description": "Remote command execution",
                "operations": [
                    "execute_command",
                    "upload_file",
                    "download_file",
                    "check_service_status"
                ]
            },
            "vapix": {
                "name": "VAPIX",
                "description": "Axis camera management",
                "operations": [
                    "get_device_info",
                    "capture_image",
                    "get_video_stream",
                    "configure_settings"
                ]
            }
        }
    
    async def execute_protocol_operation(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """Execute protocol operation via automation service"""
        try:
            protocol = request.get("protocol", "")
            target = request.get("target", {})
            command = request.get("command", "")
            credentials = request.get("credentials", {})
            parameters = request.get("parameters", {})
            
            if not protocol or not target or not command:
                return {
                    "success": False,
                    "error": "Protocol, target, and command are required"
                }
            
            logger.info("Executing protocol operation", 
                       protocol=protocol, 
                       target=target.get("hostname", "unknown"),
                       command=command)
            
            # Delegate to automation service
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.automation_service_url}/protocol/execute",
                    json={
                        "protocol": protocol,
                        "target": target,
                        "command": command,
                        "credentials": credentials,
                        "parameters": parameters
                    }
                )
                
                if response.status_code == 200:
                    return response.json()
                else:
                    return {
                        "success": False,
                        "error": f"Automation service error: {response.status_code}"
                    }
                    
        except Exception as e:
            logger.error("Protocol operation failed", error=str(e))
            return {
                "success": False,
                "error": f"Protocol operation failed: {str(e)}"
            }
    
    async def execute_query(self, parsed_data: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a system query based on parsed NLP data"""
        try:
            operation = parsed_data.get("operation", "check")
            target_process = parsed_data.get("target_process")
            target_service = parsed_data.get("target_service")
            target_group = parsed_data.get("target_group", "all servers")
            target_os = parsed_data.get("target_os", "windows")
            
            # Determine what kind of query to execute
            if operation in ["check", "status"]:
                if target_process or target_service:
                    return await self._execute_service_check(target_process or target_service, target_group, target_os)
                else:
                    return await self._execute_system_health_check(target_group)
            else:
                return {
                    "success": False,
                    "message": f"Query operation '{operation}' not supported",
                    "error": "Unsupported operation"
                }
                
        except Exception as e:
            logger.error("Query execution failed", error=str(e))
            return {
                "success": False,
                "message": f"Query failed: {str(e)}",
                "error": str(e)
            }
    
    async def _execute_service_check(self, service_name: str, target_group: str, target_os: str) -> Dict[str, Any]:
        """Execute a service status check"""
        try:
            # Create a simple job to check service status
            job_data = {
                "name": f"Check {service_name} Status",
                "description": f"Check status of {service_name} on {target_group}",
                "workflow": {
                    "steps": [{
                        "name": f"Check {service_name}",
                        "type": "powershell" if target_os == "windows" else "bash",
                        "script": self._generate_check_script(service_name, target_os),
                        "timeout": 30
                    }]
                },
                "target_group": target_group
            }
            
            # Execute via automation service
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.automation_service_url}/jobs/execute-immediate",
                    json=job_data
                )
                
                if response.status_code == 200:
                    result = response.json()
                    return {
                        "success": True,
                        "message": f"Service check for {service_name} completed",
                        "data": result
                    }
                else:
                    return {
                        "success": False,
                        "message": f"Failed to execute service check",
                        "error": f"HTTP {response.status_code}"
                    }
                    
        except Exception as e:
            logger.error("Service check failed", error=str(e))
            return {
                "success": False,
                "message": f"Service check failed: {str(e)}",
                "error": str(e)
            }
    
    async def _execute_system_health_check(self, target_group: str) -> Dict[str, Any]:
        """Execute a general system health check"""
        try:
            job_data = {
                "name": "System Health Check",
                "description": f"General health check for {target_group}",
                "workflow": {
                    "steps": [{
                        "name": "System Health",
                        "type": "powershell",
                        "script": """
# System Health Check
Write-Output "=== System Health Check ==="
Write-Output "Computer: $env:COMPUTERNAME"
Write-Output "Date: $(Get-Date)"

# CPU Usage
$cpu = Get-WmiObject -Class Win32_Processor | Measure-Object -Property LoadPercentage -Average
Write-Output "CPU Usage: $($cpu.Average)%"

# Memory Usage
$mem = Get-WmiObject -Class Win32_OperatingSystem
$memUsed = [math]::Round((($mem.TotalVisibleMemorySize - $mem.FreePhysicalMemory) / $mem.TotalVisibleMemorySize) * 100, 2)
Write-Output "Memory Usage: $memUsed%"

# Disk Space
Get-WmiObject -Class Win32_LogicalDisk | Where-Object {$_.DriveType -eq 3} | ForEach-Object {
    $freeSpace = [math]::Round($_.FreeSpace / 1GB, 2)
    $totalSpace = [math]::Round($_.Size / 1GB, 2)
    $usedPercent = [math]::Round((($totalSpace - $freeSpace) / $totalSpace) * 100, 2)
    Write-Output "Drive $($_.DeviceID) - Used: $usedPercent% ($freeSpace GB free of $totalSpace GB)"
}
                        """.strip(),
                        "timeout": 60
                    }]
                },
                "target_group": target_group
            }
            
            # Execute via automation service
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.automation_service_url}/jobs/execute-immediate",
                    json=job_data
                )
                
                if response.status_code == 200:
                    result = response.json()
                    return {
                        "success": True,
                        "message": f"System health check completed for {target_group}",
                        "data": result
                    }
                else:
                    return {
                        "success": False,
                        "message": "Failed to execute system health check",
                        "error": f"HTTP {response.status_code}"
                    }
                    
        except Exception as e:
            logger.error("System health check failed", error=str(e))
            return {
                "success": False,
                "message": f"System health check failed: {str(e)}",
                "error": str(e)
            }
    
    def _generate_check_script(self, service_name: str, target_os: str) -> str:
        """Generate appropriate check script based on service and OS"""
        if target_os == "windows":
            return f"""
# Check {service_name} status
$process = Get-Process -Name "{service_name.replace('.exe', '')}" -ErrorAction SilentlyContinue
if ($process) {{
    Write-Output "✓ {service_name} is running (PID: $($process.Id))"
    $process | Select-Object Name, Id, CPU, WorkingSet | Format-Table
}} else {{
    Write-Output "⚠ {service_name} is not running"
}}
            """.strip()
        else:
            return f"""
#!/bin/bash
# Check {service_name} status
if pgrep -x "{service_name}" > /dev/null; then
    echo "✓ {service_name} is running"
    ps aux | grep {service_name} | grep -v grep
else
    echo "⚠ {service_name} is not running"
fi
            """.strip()
    
    def get_protocol_capabilities(self) -> Dict[str, Any]:
        """Get all supported protocol capabilities"""
        return {
            "status": "success",
            "protocols": self.capabilities,
            "total_protocols": len(self.capabilities),
            "supported_operations": sum(len(p["operations"]) for p in self.capabilities.values())
        }