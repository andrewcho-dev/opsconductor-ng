"""
Remote Analysis Agent
Handles deployment and management of network analysis agents on remote targets
"""

import asyncio
import json
import logging
import tempfile
import uuid
from typing import Dict, List, Optional, Any
from datetime import datetime

import structlog
import httpx

logger = structlog.get_logger(__name__)

class RemoteAnalysisAgent:
    """Manages remote network analysis agents"""
    
    def __init__(self):
        self.deployed_agents: Dict[str, Dict] = {}
        self.asset_service_url = "http://asset-service:3002"
        self.automation_service_url = "http://automation-service:3003"
        
        # Agent script templates
        self.agent_scripts = {
            "linux": self._get_linux_agent_script(),
            "windows": self._get_windows_agent_script()
        }
    
    async def deploy_agent(
        self,
        target_id: int,
        agent_config: Dict[str, Any]
    ) -> str:
        """Deploy network analysis agent to remote target"""
        try:
            agent_id = str(uuid.uuid4())
            
            logger.info("Deploying network analysis agent", 
                       agent_id=agent_id, 
                       target_id=target_id)
            
            # Get target information
            target_info = await self._get_target_info(target_id)
            if not target_info:
                raise ValueError(f"Target {target_id} not found")
            
            # Determine target OS
            target_os = self._detect_target_os(target_info)
            
            # Select appropriate agent script
            if target_os not in self.agent_scripts:
                raise ValueError(f"Unsupported target OS: {target_os}")
            
            agent_script = self.agent_scripts[target_os]
            
            # Customize agent script with configuration
            customized_script = self._customize_agent_script(agent_script, agent_config)
            
            # Deploy agent via automation service
            deployment_result = await self._deploy_via_automation(
                target_id, customized_script, agent_config
            )
            
            # Store agent information
            self.deployed_agents[agent_id] = {
                "agent_id": agent_id,
                "target_id": target_id,
                "target_info": target_info,
                "config": agent_config,
                "deployed_at": datetime.now(),
                "status": "deployed",
                "last_contact": datetime.now(),
                "deployment_result": deployment_result
            }
            
            logger.info("Successfully deployed network analysis agent", 
                       agent_id=agent_id, 
                       target_id=target_id)
            
            return agent_id
            
        except Exception as e:
            logger.error("Failed to deploy network analysis agent", 
                        target_id=target_id, error=str(e))
            raise
    
    async def execute_analysis(
        self,
        agent_id: str,
        analysis_type: str,
        parameters: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Execute network analysis on remote agent"""
        try:
            if agent_id not in self.deployed_agents:
                raise ValueError(f"Agent {agent_id} not found")
            
            agent_info = self.deployed_agents[agent_id]
            target_id = agent_info["target_id"]
            
            logger.info("Executing remote network analysis", 
                       agent_id=agent_id, 
                       analysis_type=analysis_type)
            
            # Build analysis command based on type
            analysis_command = self._build_analysis_command(analysis_type, parameters)
            
            # Execute command via automation service
            execution_result = await self._execute_remote_command(
                target_id, analysis_command
            )
            
            # Process and parse results
            analysis_results = self._parse_analysis_results(
                analysis_type, execution_result
            )
            
            # Update agent last contact
            agent_info["last_contact"] = datetime.now()
            
            logger.info("Completed remote network analysis", 
                       agent_id=agent_id, 
                       analysis_type=analysis_type)
            
            return analysis_results
            
        except Exception as e:
            logger.error("Failed to execute remote analysis", 
                        agent_id=agent_id, error=str(e))
            raise
    
    async def _get_target_info(self, target_id: int) -> Optional[Dict[str, Any]]:
        """Get target information from asset service"""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.asset_service_url}/api/v1/targets/{target_id}",
                    timeout=10.0
                )
                
                if response.status_code == 200:
                    return response.json()
                else:
                    logger.warning("Failed to get target info", 
                                 target_id=target_id, 
                                 status_code=response.status_code)
                    return None
        
        except Exception as e:
            logger.error("Error getting target info", 
                        target_id=target_id, error=str(e))
            return None
    
    def _detect_target_os(self, target_info: Dict[str, Any]) -> str:
        """Detect target operating system"""
        # Check if OS is specified in target info
        if "operating_system" in target_info:
            os_name = target_info["operating_system"].lower()
            if "windows" in os_name:
                return "windows"
            elif any(linux_os in os_name for linux_os in ["linux", "ubuntu", "centos", "rhel", "debian"]):
                return "linux"
        
        # Check service types for hints
        services = target_info.get("services", [])
        for service in services:
            service_type = service.get("service_type", "").lower()
            if service_type in ["ssh", "linux_ssh"]:
                return "linux"
            elif service_type in ["rdp", "winrm", "powershell"]:
                return "windows"
        
        # Default to linux if uncertain
        return "linux"
    
    def _get_linux_agent_script(self) -> str:
        """Get Linux network analysis agent script"""
        return '''#!/bin/bash
# OpsConductor Network Analysis Agent for Linux
# This script provides network analysis capabilities

AGENT_ID="{{AGENT_ID}}"
REPORT_INTERVAL={{REPORT_INTERVAL}}
CAPTURE_INTERFACES="{{CAPTURE_INTERFACES}}"

# Function to capture network statistics
capture_network_stats() {
    echo "=== Network Statistics ==="
    echo "Timestamp: $(date -Iseconds)"
    
    # Interface statistics
    echo "--- Interface Statistics ---"
    cat /proc/net/dev
    
    # Connection statistics
    echo "--- Connection Statistics ---"
    ss -tuln | wc -l
    
    # Traffic analysis
    echo "--- Traffic Analysis ---"
    for iface in $CAPTURE_INTERFACES; do
        if [ -d "/sys/class/net/$iface" ]; then
            echo "Interface: $iface"
            cat /sys/class/net/$iface/statistics/rx_bytes
            cat /sys/class/net/$iface/statistics/tx_bytes
            cat /sys/class/net/$iface/statistics/rx_packets
            cat /sys/class/net/$iface/statistics/tx_packets
        fi
    done
}

# Function to perform connectivity tests
test_connectivity() {
    local target=$1
    local port=$2
    
    echo "=== Connectivity Test ==="
    echo "Target: $target:$port"
    echo "Timestamp: $(date -Iseconds)"
    
    if command -v nc >/dev/null 2>&1; then
        timeout 5 nc -z -v "$target" "$port" 2>&1
    else
        timeout 5 telnet "$target" "$port" 2>&1
    fi
}

# Function to capture packets
capture_packets() {
    local interface=$1
    local count=${2:-100}
    local filter=${3:-""}
    
    echo "=== Packet Capture ==="
    echo "Interface: $interface"
    echo "Count: $count"
    echo "Filter: $filter"
    echo "Timestamp: $(date -Iseconds)"
    
    if command -v tcpdump >/dev/null 2>&1; then
        timeout 30 tcpdump -i "$interface" -c "$count" $filter 2>&1
    else
        echo "tcpdump not available"
    fi
}

# Function to analyze network performance
analyze_performance() {
    echo "=== Performance Analysis ==="
    echo "Timestamp: $(date -Iseconds)"
    
    # Bandwidth test (if iperf3 is available)
    if command -v iperf3 >/dev/null 2>&1; then
        echo "--- Bandwidth Test ---"
        # This would need an iperf3 server
        echo "iperf3 available but no server configured"
    fi
    
    # Latency test
    echo "--- Latency Test ---"
    ping -c 5 8.8.8.8 2>&1 | tail -1
    
    # DNS resolution test
    echo "--- DNS Resolution Test ---"
    time nslookup google.com 2>&1
}

# Main execution based on command
case "$1" in
    "stats")
        capture_network_stats
        ;;
    "connectivity")
        test_connectivity "$2" "$3"
        ;;
    "capture")
        capture_packets "$2" "$3" "$4"
        ;;
    "performance")
        analyze_performance
        ;;
    *)
        echo "Usage: $0 {stats|connectivity|capture|performance} [args...]"
        exit 1
        ;;
esac
'''
    
    def _get_windows_agent_script(self) -> str:
        """Get Windows network analysis agent script"""
        return '''@echo off
REM OpsConductor Network Analysis Agent for Windows
REM This script provides network analysis capabilities

set AGENT_ID={{AGENT_ID}}
set REPORT_INTERVAL={{REPORT_INTERVAL}}
set CAPTURE_INTERFACES={{CAPTURE_INTERFACES}}

if "%1"=="stats" goto stats
if "%1"=="connectivity" goto connectivity
if "%1"=="capture" goto capture
if "%1"=="performance" goto performance
goto usage

:stats
echo === Network Statistics ===
echo Timestamp: %date% %time%
echo --- Interface Statistics ---
netstat -e
echo --- Connection Statistics ---
netstat -an | find /c ":"
goto end

:connectivity
echo === Connectivity Test ===
echo Target: %2:%3
echo Timestamp: %date% %time%
telnet %2 %3
goto end

:capture
echo === Packet Capture ===
echo Interface: %2
echo Count: %3
echo Timestamp: %date% %time%
REM Windows packet capture would require additional tools
echo Packet capture requires additional tools on Windows
goto end

:performance
echo === Performance Analysis ===
echo Timestamp: %date% %time%
echo --- Latency Test ---
ping -n 5 8.8.8.8
echo --- DNS Resolution Test ---
nslookup google.com
goto end

:usage
echo Usage: %0 {stats^|connectivity^|capture^|performance} [args...]
exit /b 1

:end
'''
    
    def _customize_agent_script(
        self,
        script_template: str,
        agent_config: Dict[str, Any]
    ) -> str:
        """Customize agent script with configuration"""
        customized_script = script_template
        
        # Replace placeholders
        replacements = {
            "{{AGENT_ID}}": str(uuid.uuid4()),
            "{{REPORT_INTERVAL}}": str(agent_config.get("reporting_interval", 60)),
            "{{CAPTURE_INTERFACES}}": " ".join(agent_config.get("capture_interfaces", ["eth0"]))
        }
        
        for placeholder, value in replacements.items():
            customized_script = customized_script.replace(placeholder, value)
        
        return customized_script
    
    async def _deploy_via_automation(
        self,
        target_id: int,
        agent_script: str,
        agent_config: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Deploy agent script via automation service"""
        try:
            # Create a job to deploy the agent
            job_data = {
                "name": f"Deploy Network Analysis Agent - Target {target_id}",
                "description": "Deploy network analysis agent to remote target",
                "target_ids": [target_id],
                "steps": [
                    {
                        "name": "Create agent directory",
                        "step_type": "command",
                        "command": "mkdir -p /tmp/opsconductor-agent",
                        "timeout": 30
                    },
                    {
                        "name": "Deploy agent script",
                        "step_type": "file_transfer",
                        "source_content": agent_script,
                        "destination": "/tmp/opsconductor-agent/network-agent.sh",
                        "permissions": "755"
                    },
                    {
                        "name": "Test agent",
                        "step_type": "command",
                        "command": "/tmp/opsconductor-agent/network-agent.sh stats",
                        "timeout": 60
                    }
                ]
            }
            
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.automation_service_url}/api/v1/jobs",
                    json=job_data,
                    timeout=30.0
                )
                
                if response.status_code == 201:
                    job_info = response.json()
                    
                    # Execute the job
                    execute_response = await client.post(
                        f"{self.automation_service_url}/api/v1/jobs/{job_info['id']}/execute",
                        timeout=120.0
                    )
                    
                    if execute_response.status_code == 200:
                        execution_info = execute_response.json()
                        return {
                            "job_id": job_info["id"],
                            "execution_id": execution_info["execution_id"],
                            "status": "deployed"
                        }
                    else:
                        raise Exception(f"Job execution failed: {execute_response.status_code}")
                else:
                    raise Exception(f"Job creation failed: {response.status_code}")
        
        except Exception as e:
            logger.error("Failed to deploy agent via automation", 
                        target_id=target_id, error=str(e))
            raise
    
    def _build_analysis_command(
        self,
        analysis_type: str,
        parameters: Dict[str, Any]
    ) -> str:
        """Build analysis command based on type and parameters"""
        base_command = "/tmp/opsconductor-agent/network-agent.sh"
        
        if analysis_type == "network_stats":
            return f"{base_command} stats"
        
        elif analysis_type == "connectivity_test":
            target_host = parameters.get("target_host", "8.8.8.8")
            port = parameters.get("port", 80)
            return f"{base_command} connectivity {target_host} {port}"
        
        elif analysis_type == "packet_capture":
            interface = parameters.get("interface", "eth0")
            count = parameters.get("count", 100)
            filter_expr = parameters.get("filter", "")
            return f"{base_command} capture {interface} {count} '{filter_expr}'"
        
        elif analysis_type == "performance_analysis":
            return f"{base_command} performance"
        
        else:
            raise ValueError(f"Unsupported analysis type: {analysis_type}")
    
    async def _execute_remote_command(
        self,
        target_id: int,
        command: str
    ) -> Dict[str, Any]:
        """Execute command on remote target via automation service"""
        try:
            job_data = {
                "name": f"Network Analysis - Target {target_id}",
                "description": "Execute network analysis command",
                "target_ids": [target_id],
                "steps": [
                    {
                        "name": "Execute analysis",
                        "step_type": "command",
                        "command": command,
                        "timeout": 120
                    }
                ]
            }
            
            async with httpx.AsyncClient() as client:
                # Create job
                response = await client.post(
                    f"{self.automation_service_url}/api/v1/jobs",
                    json=job_data,
                    timeout=30.0
                )
                
                if response.status_code != 201:
                    raise Exception(f"Job creation failed: {response.status_code}")
                
                job_info = response.json()
                
                # Execute job
                execute_response = await client.post(
                    f"{self.automation_service_url}/api/v1/jobs/{job_info['id']}/execute",
                    timeout=180.0
                )
                
                if execute_response.status_code != 200:
                    raise Exception(f"Job execution failed: {execute_response.status_code}")
                
                execution_info = execute_response.json()
                
                # Wait for completion and get results
                execution_id = execution_info["execution_id"]
                
                # Poll for completion (simplified)
                for _ in range(30):  # Wait up to 5 minutes
                    await asyncio.sleep(10)
                    
                    status_response = await client.get(
                        f"{self.automation_service_url}/api/v1/executions/{execution_id}",
                        timeout=10.0
                    )
                    
                    if status_response.status_code == 200:
                        status_info = status_response.json()
                        
                        if status_info["status"] in ["completed", "failed"]:
                            return status_info
                
                # Timeout
                raise Exception("Command execution timeout")
        
        except Exception as e:
            logger.error("Failed to execute remote command", 
                        target_id=target_id, error=str(e))
            raise
    
    def _parse_analysis_results(
        self,
        analysis_type: str,
        execution_result: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Parse analysis results from execution output"""
        try:
            output = execution_result.get("output", "")
            error = execution_result.get("error", "")
            status = execution_result.get("status", "unknown")
            
            parsed_results = {
                "analysis_type": analysis_type,
                "status": status,
                "raw_output": output,
                "error": error,
                "timestamp": datetime.now().isoformat()
            }
            
            # Parse specific analysis types
            if analysis_type == "network_stats":
                parsed_results["parsed_data"] = self._parse_network_stats(output)
            
            elif analysis_type == "connectivity_test":
                parsed_results["parsed_data"] = self._parse_connectivity_test(output)
            
            elif analysis_type == "packet_capture":
                parsed_results["parsed_data"] = self._parse_packet_capture(output)
            
            elif analysis_type == "performance_analysis":
                parsed_results["parsed_data"] = self._parse_performance_analysis(output)
            
            return parsed_results
            
        except Exception as e:
            logger.error("Failed to parse analysis results", 
                        analysis_type=analysis_type, error=str(e))
            return {
                "analysis_type": analysis_type,
                "status": "parse_error",
                "error": str(e),
                "raw_output": execution_result.get("output", ""),
                "timestamp": datetime.now().isoformat()
            }
    
    def _parse_network_stats(self, output: str) -> Dict[str, Any]:
        """Parse network statistics output"""
        # Simplified parsing - would be more sophisticated in production
        return {
            "interfaces_detected": output.count("eth"),
            "connections_found": "connection" in output.lower(),
            "output_lines": len(output.split('\n'))
        }
    
    def _parse_connectivity_test(self, output: str) -> Dict[str, Any]:
        """Parse connectivity test output"""
        success = "connected" in output.lower() or "open" in output.lower()
        return {
            "connection_successful": success,
            "response_time": self._extract_response_time(output)
        }
    
    def _parse_packet_capture(self, output: str) -> Dict[str, Any]:
        """Parse packet capture output"""
        lines = output.split('\n')
        packet_count = len([line for line in lines if ">" in line])
        
        return {
            "packets_captured": packet_count,
            "capture_duration": self._extract_capture_duration(output)
        }
    
    def _parse_performance_analysis(self, output: str) -> Dict[str, Any]:
        """Parse performance analysis output"""
        return {
            "latency_ms": self._extract_latency(output),
            "dns_resolution_time": self._extract_dns_time(output)
        }
    
    def _extract_response_time(self, output: str) -> Optional[float]:
        """Extract response time from output"""
        # Simplified extraction
        import re
        match = re.search(r'time=(\d+\.?\d*)ms', output)
        return float(match.group(1)) if match else None
    
    def _extract_capture_duration(self, output: str) -> Optional[float]:
        """Extract capture duration from output"""
        # Simplified extraction
        return 30.0  # Default timeout
    
    def _extract_latency(self, output: str) -> Optional[float]:
        """Extract latency from ping output"""
        import re
        match = re.search(r'avg = (\d+\.?\d*)', output)
        return float(match.group(1)) if match else None
    
    def _extract_dns_time(self, output: str) -> Optional[float]:
        """Extract DNS resolution time"""
        # Simplified extraction
        return 0.1  # Default value
    
    def get_agent_status(self, agent_id: str) -> Optional[Dict[str, Any]]:
        """Get status of deployed agent"""
        if agent_id in self.deployed_agents:
            return self.deployed_agents[agent_id]
        return None
    
    def list_deployed_agents(self) -> List[Dict[str, Any]]:
        """List all deployed agents"""
        return list(self.deployed_agents.values())
    
    async def remove_agent(self, agent_id: str) -> bool:
        """Remove deployed agent"""
        try:
            if agent_id not in self.deployed_agents:
                return False
            
            agent_info = self.deployed_agents[agent_id]
            target_id = agent_info["target_id"]
            
            # Create cleanup job
            cleanup_command = "rm -rf /tmp/opsconductor-agent"
            await self._execute_remote_command(target_id, cleanup_command)
            
            # Remove from tracking
            del self.deployed_agents[agent_id]
            
            logger.info("Removed network analysis agent", 
                       agent_id=agent_id, 
                       target_id=target_id)
            
            return True
            
        except Exception as e:
            logger.error("Failed to remove agent", 
                        agent_id=agent_id, error=str(e))
            return False