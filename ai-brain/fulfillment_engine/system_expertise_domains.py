#!/usr/bin/env python3
"""
System Expertise Knowledge Domains
Comprehensive knowledge about Linux, Windows, and PowerShell capabilities
"""

from typing import Dict, List, Optional, Any
from datetime import datetime
from dynamic_service_catalog import (
    KnowledgeDomain, 
    KnowledgeMetadata, 
    KnowledgeDomainType, 
    ContextPriority,
    APIDiscoveryResult
)

class LinuxExpertiseDomain(KnowledgeDomain):
    """Comprehensive Linux system administration expertise"""
    
    def __init__(self):
        metadata = KnowledgeMetadata(
            domain_id="linux_expertise",
            domain_type=KnowledgeDomainType.CORE_SERVICE,
            version="1.0.0",
            last_updated=datetime.now(),
            size_bytes=0,
            priority=ContextPriority.CRITICAL,
            keywords=["linux", "unix", "bash", "shell", "command", "system", "administration"],
            dependencies=[],
            performance_metrics={}
        )
        super().__init__("linux_expertise", metadata)
        self.knowledge = self._initialize_linux_knowledge()
    
    def _initialize_linux_knowledge(self) -> Dict[str, Any]:
        return {
            "system_info": {
                "description": "Expert knowledge of Linux/Unix system administration and commands",
                "distributions": ["Ubuntu", "CentOS", "RHEL", "Debian", "SUSE", "Alpine", "Amazon Linux"],
                "shells": ["bash", "zsh", "sh", "dash", "fish"],
                "package_managers": ["apt", "yum", "dnf", "zypper", "pacman", "apk"]
            },
            "capabilities": {
                "system_information": {
                    "description": "Commands to gather comprehensive system information",
                    "keywords": ["info", "system", "hardware", "status", "details"],
                    "commands": [
                        {
                            "command": "uname -a",
                            "description": "Complete system information (kernel, hostname, architecture)",
                            "example_output": "Linux web01 5.4.0-74-generic #83-Ubuntu SMP Sat May 8 02:35:39 UTC 2021 x86_64 x86_64 x86_64 GNU/Linux"
                        },
                        {
                            "command": "hostnamectl",
                            "description": "Detailed hostname and system information",
                            "example_output": "Static hostname: web01\\nIcon name: computer-vm\\nChassis: vm\\nOperating System: Ubuntu 20.04.2 LTS"
                        },
                        {
                            "command": "lscpu",
                            "description": "CPU architecture and specifications",
                            "example_output": "Architecture: x86_64\\nCPU(s): 4\\nModel name: Intel(R) Xeon(R) CPU E5-2676 v3 @ 2.40GHz"
                        },
                        {
                            "command": "free -h",
                            "description": "Memory usage in human-readable format",
                            "example_output": "total used free shared buff/cache available\\nMem: 7.8G 2.1G 3.2G 180M 2.5G 5.3G"
                        },
                        {
                            "command": "df -h",
                            "description": "Disk space usage for all mounted filesystems",
                            "example_output": "/dev/xvda1 20G 8.5G 11G 45% /"
                        },
                        {
                            "command": "lsblk",
                            "description": "List all block devices in tree format",
                            "example_output": "NAME MAJ:MIN RM SIZE RO TYPE MOUNTPOINT\\nxvda 202:0 0 20G 0 disk\\n└─xvda1 202:1 0 20G 0 part /"
                        },
                        {
                            "command": "ip addr show",
                            "description": "Network interface configuration",
                            "example_output": "2: eth0: <BROADCAST,MULTICAST,UP,LOWER_UP> mtu 9001\\ninet 172.31.32.45/20 brd 172.31.47.255 scope global dynamic eth0"
                        },
                        {
                            "command": "systemctl status",
                            "description": "Overall system status and failed services",
                            "example_output": "● web01\\nState: running\\nJobs: 0 queued\\nFailed: 0 units"
                        }
                    ],
                    "comprehensive_script": """#!/bin/bash
# Comprehensive Linux System Information Script
echo "=== SYSTEM INFORMATION ==="
echo "Hostname: $(hostname)"
echo "Uptime: $(uptime)"
echo "Kernel: $(uname -r)"
echo "Distribution: $(lsb_release -d 2>/dev/null | cut -f2 || cat /etc/os-release | grep PRETTY_NAME | cut -d'=' -f2 | tr -d '\"')"
echo ""
echo "=== HARDWARE INFORMATION ==="
echo "CPU: $(lscpu | grep 'Model name' | cut -d':' -f2 | xargs)"
echo "CPU Cores: $(nproc)"
echo "Memory: $(free -h | grep Mem | awk '{print $2}')"
echo "Architecture: $(uname -m)"
echo ""
echo "=== STORAGE INFORMATION ==="
df -h | grep -E '^/dev/'
echo ""
echo "=== NETWORK INFORMATION ==="
ip -4 addr show | grep inet | grep -v 127.0.0.1
echo ""
echo "=== SYSTEM LOAD ==="
cat /proc/loadavg
echo ""
echo "=== RUNNING SERVICES ==="
systemctl list-units --type=service --state=running | head -10"""
                },
                "process_management": {
                    "description": "Process monitoring, control, and management commands",
                    "keywords": ["process", "service", "daemon", "kill", "monitor"],
                    "commands": [
                        {
                            "command": "ps aux",
                            "description": "List all running processes with detailed information",
                            "example_output": "USER PID %CPU %MEM VSZ RSS TTY STAT START TIME COMMAND"
                        },
                        {
                            "command": "top -b -n 1",
                            "description": "Process activity snapshot (non-interactive)",
                            "example_output": "PID USER PR NI VIRT RES SHR S %CPU %MEM TIME+ COMMAND"
                        },
                        {
                            "command": "htop",
                            "description": "Interactive process viewer (if installed)",
                            "note": "More user-friendly than top, shows CPU/memory bars"
                        },
                        {
                            "command": "pgrep -f nginx",
                            "description": "Find process IDs by name pattern",
                            "example_output": "1234\\n5678"
                        },
                        {
                            "command": "systemctl status nginx",
                            "description": "Check service status",
                            "example_output": "● nginx.service - A high performance web server\\nLoaded: loaded\\nActive: active (running)"
                        },
                        {
                            "command": "systemctl start/stop/restart/reload nginx",
                            "description": "Control systemd services",
                            "note": "Use appropriate action: start, stop, restart, reload"
                        },
                        {
                            "command": "kill -9 1234",
                            "description": "Force kill process by PID",
                            "note": "Use -15 (TERM) first, -9 (KILL) as last resort"
                        },
                        {
                            "command": "killall nginx",
                            "description": "Kill all processes by name",
                            "note": "Be careful with this command"
                        }
                    ]
                },
                "file_operations": {
                    "description": "File and directory manipulation commands",
                    "keywords": ["file", "directory", "copy", "move", "delete", "permissions"],
                    "commands": [
                        {
                            "command": "ls -la",
                            "description": "List files with detailed information including hidden files",
                            "example_output": "drwxr-xr-x 2 user user 4096 Jan 15 10:30 directory"
                        },
                        {
                            "command": "find /path -name '*.log' -mtime -7",
                            "description": "Find files by name pattern modified in last 7 days",
                            "example_output": "/var/log/nginx/access.log\\n/var/log/nginx/error.log"
                        },
                        {
                            "command": "chmod 755 /path/to/file",
                            "description": "Change file permissions (rwxr-xr-x)",
                            "note": "755 = owner: rwx, group: r-x, others: r-x"
                        },
                        {
                            "command": "chown user:group /path/to/file",
                            "description": "Change file ownership",
                            "note": "Requires appropriate privileges"
                        },
                        {
                            "command": "cp -r /source /destination",
                            "description": "Copy files/directories recursively",
                            "note": "-r for directories, -p to preserve attributes"
                        },
                        {
                            "command": "rsync -av /source/ /destination/",
                            "description": "Efficient file synchronization",
                            "note": "Better than cp for large transfers, shows progress"
                        },
                        {
                            "command": "tar -czf backup.tar.gz /path/to/backup",
                            "description": "Create compressed archive",
                            "note": "-c create, -z gzip, -f file, -v verbose"
                        },
                        {
                            "command": "tar -xzf backup.tar.gz",
                            "description": "Extract compressed archive",
                            "note": "-x extract, -z gzip, -f file"
                        }
                    ]
                },
                "network_operations": {
                    "description": "Network configuration and troubleshooting commands",
                    "keywords": ["network", "ip", "route", "dns", "connectivity", "firewall"],
                    "commands": [
                        {
                            "command": "ip addr show",
                            "description": "Show network interface configuration",
                            "example_output": "2: eth0: <BROADCAST,MULTICAST,UP,LOWER_UP> inet 192.168.1.100/24"
                        },
                        {
                            "command": "ip route show",
                            "description": "Display routing table",
                            "example_output": "default via 192.168.1.1 dev eth0\\n192.168.1.0/24 dev eth0 proto kernel scope link"
                        },
                        {
                            "command": "ping -c 4 google.com",
                            "description": "Test connectivity with 4 packets",
                            "example_output": "PING google.com (172.217.164.110) 56(84) bytes of data."
                        },
                        {
                            "command": "nslookup google.com",
                            "description": "DNS lookup for domain",
                            "example_output": "Server: 8.8.8.8\\nAddress: 8.8.8.8#53\\nName: google.com\\nAddress: 172.217.164.110"
                        },
                        {
                            "command": "netstat -tulpn",
                            "description": "Show listening ports and connections",
                            "example_output": "tcp 0 0 0.0.0.0:22 0.0.0.0:* LISTEN 1234/sshd"
                        },
                        {
                            "command": "ss -tulpn",
                            "description": "Modern replacement for netstat",
                            "note": "Faster and more detailed than netstat"
                        },
                        {
                            "command": "iptables -L",
                            "description": "List firewall rules",
                            "note": "Requires root privileges"
                        },
                        {
                            "command": "ufw status",
                            "description": "Ubuntu firewall status (if using UFW)",
                            "example_output": "Status: active\\nTo Action From\\n22/tcp ALLOW Anywhere"
                        }
                    ]
                },
                "log_analysis": {
                    "description": "Log file analysis and monitoring commands",
                    "keywords": ["log", "analysis", "monitor", "tail", "grep", "journal"],
                    "commands": [
                        {
                            "command": "tail -f /var/log/syslog",
                            "description": "Follow log file in real-time",
                            "note": "Use Ctrl+C to stop following"
                        },
                        {
                            "command": "journalctl -u nginx -f",
                            "description": "Follow systemd service logs",
                            "note": "For systemd-based systems"
                        },
                        {
                            "command": "grep -i error /var/log/nginx/error.log",
                            "description": "Search for errors in log file (case-insensitive)",
                            "example_output": "2024/01/15 10:30:00 [error] 1234#0: connection refused"
                        },
                        {
                            "command": "awk '{print $1}' /var/log/nginx/access.log | sort | uniq -c | sort -nr",
                            "description": "Count unique IP addresses in access log",
                            "example_output": "150 192.168.1.100\\n75 192.168.1.101"
                        },
                        {
                            "command": "zcat /var/log/nginx/access.log.*.gz | grep '15/Jan/2024'",
                            "description": "Search compressed log files for specific date",
                            "note": "zcat for .gz files, bzcat for .bz2"
                        }
                    ]
                },
                "package_management": {
                    "description": "Software package management across different distributions",
                    "keywords": ["package", "install", "update", "software", "repository"],
                    "debian_ubuntu": [
                        {
                            "command": "apt update && apt upgrade",
                            "description": "Update package lists and upgrade installed packages",
                            "note": "Always update before installing new packages"
                        },
                        {
                            "command": "apt install nginx",
                            "description": "Install a package",
                            "note": "Use -y flag for non-interactive installation"
                        },
                        {
                            "command": "apt search nginx",
                            "description": "Search for packages",
                            "example_output": "nginx/focal 1.18.0-0ubuntu1.2 all\\nnginx-common/focal 1.18.0-0ubuntu1.2 all"
                        },
                        {
                            "command": "dpkg -l | grep nginx",
                            "description": "List installed packages matching pattern",
                            "example_output": "ii nginx 1.18.0-0ubuntu1.2 all high-performance web server"
                        }
                    ],
                    "rhel_centos": [
                        {
                            "command": "yum update",
                            "description": "Update all packages (CentOS 7 and older)",
                            "note": "Use dnf on CentOS 8+ and Fedora"
                        },
                        {
                            "command": "dnf install nginx",
                            "description": "Install package (CentOS 8+, Fedora)",
                            "note": "dnf is the modern replacement for yum"
                        },
                        {
                            "command": "rpm -qa | grep nginx",
                            "description": "List installed RPM packages",
                            "example_output": "nginx-1.20.1-9.el8.x86_64"
                        }
                    ]
                },
                "performance_monitoring": {
                    "description": "System performance monitoring and analysis",
                    "keywords": ["performance", "cpu", "memory", "disk", "io", "load"],
                    "commands": [
                        {
                            "command": "iostat -x 1",
                            "description": "I/O statistics every second",
                            "note": "Part of sysstat package, shows disk utilization"
                        },
                        {
                            "command": "vmstat 1",
                            "description": "Virtual memory statistics every second",
                            "example_output": "procs memory swap io system cpu\\nr b swpd free buff cache si so bi bo in cs us sy id wa st"
                        },
                        {
                            "command": "sar -u 1 10",
                            "description": "CPU utilization every second for 10 intervals",
                            "note": "Part of sysstat package"
                        },
                        {
                            "command": "iotop",
                            "description": "I/O usage by process (if installed)",
                            "note": "Shows which processes are using disk I/O"
                        },
                        {
                            "command": "nload",
                            "description": "Network bandwidth usage (if installed)",
                            "note": "Real-time network traffic monitor"
                        }
                    ]
                }
            },
            "scripting_patterns": [
                {
                    "name": "System Health Check Script",
                    "description": "Comprehensive system health monitoring",
                    "script": """#!/bin/bash
# System Health Check Script
echo "=== System Health Check - $(date) ==="
echo ""

# CPU Load
echo "CPU Load Average:"
uptime | awk -F'load average:' '{print $2}'

# Memory Usage
echo ""
echo "Memory Usage:"
free -h | grep -E 'Mem|Swap'

# Disk Usage
echo ""
echo "Disk Usage (>80% warning):"
df -h | awk '$5 > 80 {print $0}'

# Failed Services
echo ""
echo "Failed Services:"
systemctl --failed --no-legend

# Network Connectivity
echo ""
echo "Network Connectivity:"
ping -c 1 8.8.8.8 >/dev/null 2>&1 && echo "Internet: OK" || echo "Internet: FAILED"

echo ""
echo "=== Health Check Complete ==="
"""
                },
                {
                    "name": "Log Analysis Script",
                    "description": "Analyze system logs for errors and warnings",
                    "script": """#!/bin/bash
# Log Analysis Script
LOG_FILE=${1:-/var/log/syslog}
HOURS=${2:-24}

echo "=== Log Analysis for last $HOURS hours ==="
echo "Log file: $LOG_FILE"
echo ""

# Calculate time threshold
TIME_THRESHOLD=$(date -d "$HOURS hours ago" '+%b %d %H:%M')

# Error count
echo "Error Summary:"
grep -i error "$LOG_FILE" | grep -v "$TIME_THRESHOLD" | wc -l | awk '{print "Errors: " $1}'

# Warning count  
grep -i warning "$LOG_FILE" | grep -v "$TIME_THRESHOLD" | wc -l | awk '{print "Warnings: " $1}'

echo ""
echo "Recent Errors:"
grep -i error "$LOG_FILE" | tail -5

echo ""
echo "Recent Warnings:"
grep -i warning "$LOG_FILE" | tail -5
"""
                }
            ],
            "best_practices": [
                "Always test commands in non-production environments first",
                "Use sudo only when necessary, avoid running as root",
                "Make backups before making system changes",
                "Use package managers instead of compiling from source when possible",
                "Monitor system logs regularly for issues",
                "Keep systems updated with security patches",
                "Use configuration management tools for consistency",
                "Document system changes and configurations"
            ],
            "troubleshooting_workflows": [
                {
                    "issue": "High CPU Usage",
                    "steps": [
                        "Check current CPU usage: top or htop",
                        "Identify top CPU consumers: ps aux --sort=-%cpu | head",
                        "Check system load: uptime",
                        "Analyze process details: ps -p PID -o pid,ppid,cmd,%cpu,%mem",
                        "Check for runaway processes or infinite loops",
                        "Consider killing problematic processes: kill -15 PID"
                    ]
                },
                {
                    "issue": "High Memory Usage",
                    "steps": [
                        "Check memory usage: free -h",
                        "Identify memory consumers: ps aux --sort=-%mem | head",
                        "Check for memory leaks: watch -n 1 'ps aux --sort=-%mem | head'",
                        "Analyze swap usage: swapon -s",
                        "Clear caches if safe: echo 3 > /proc/sys/vm/drop_caches",
                        "Consider restarting memory-heavy services"
                    ]
                },
                {
                    "issue": "Disk Space Full",
                    "steps": [
                        "Check disk usage: df -h",
                        "Find large files: find / -type f -size +100M 2>/dev/null",
                        "Check directory sizes: du -sh /* | sort -hr",
                        "Clean log files: journalctl --vacuum-time=7d",
                        "Remove old packages: apt autoremove (Ubuntu/Debian)",
                        "Clear temporary files: rm -rf /tmp/*"
                    ]
                }
            ]
        }
    
    async def discover_capabilities(self) -> APIDiscoveryResult:
        return APIDiscoveryResult(
            endpoints=[],
            capabilities=list(self.knowledge["capabilities"].keys()),
            authentication_methods=[],
            rate_limits={},
            documentation_urls=[],
            examples=[]
        )
    
    def get_context_for_request(self, request_keywords: List[str]) -> Dict[str, Any]:
        keyword_set = set(word.lower() for word in request_keywords)
        relevant_capabilities = []
        
        if any(word in keyword_set for word in ["system", "info", "information", "details"]):
            relevant_capabilities.append(self.knowledge["capabilities"]["system_information"])
        
        if any(word in keyword_set for word in ["process", "service", "daemon", "running"]):
            relevant_capabilities.append(self.knowledge["capabilities"]["process_management"])
        
        if any(word in keyword_set for word in ["file", "directory", "copy", "move"]):
            relevant_capabilities.append(self.knowledge["capabilities"]["file_operations"])
        
        if any(word in keyword_set for word in ["network", "ip", "connectivity", "ping"]):
            relevant_capabilities.append(self.knowledge["capabilities"]["network_operations"])
        
        if any(word in keyword_set for word in ["log", "error", "warning", "analysis"]):
            relevant_capabilities.append(self.knowledge["capabilities"]["log_analysis"])
        
        if any(word in keyword_set for word in ["install", "package", "update", "software"]):
            relevant_capabilities.append(self.knowledge["capabilities"]["package_management"])
        
        if any(word in keyword_set for word in ["performance", "cpu", "memory", "load"]):
            relevant_capabilities.append(self.knowledge["capabilities"]["performance_monitoring"])
        
        return {
            "domain": "Linux System Administration Expertise",
            "system_info": self.knowledge["system_info"],
            "relevant_capabilities": relevant_capabilities,
            "scripting_patterns": self.knowledge["scripting_patterns"],
            "best_practices": self.knowledge["best_practices"],
            "troubleshooting_workflows": self.knowledge["troubleshooting_workflows"]
        }
    
    def update_knowledge(self, new_knowledge: Dict[str, Any]) -> bool:
        try:
            if "capabilities" in new_knowledge:
                self.knowledge["capabilities"].update(new_knowledge["capabilities"])
            self.metadata.last_updated = datetime.now()
            return True
        except Exception:
            return False

class WindowsExpertiseDomain(KnowledgeDomain):
    """Comprehensive Windows system administration expertise"""
    
    def __init__(self):
        metadata = KnowledgeMetadata(
            domain_id="windows_expertise",
            domain_type=KnowledgeDomainType.CORE_SERVICE,
            version="1.0.0",
            last_updated=datetime.now(),
            size_bytes=0,
            priority=ContextPriority.CRITICAL,
            keywords=["windows", "cmd", "command", "system", "administration", "server"],
            dependencies=[],
            performance_metrics={}
        )
        super().__init__("windows_expertise", metadata)
        self.knowledge = self._initialize_windows_knowledge()
    
    def _initialize_windows_knowledge(self) -> Dict[str, Any]:
        return {
            "system_info": {
                "description": "Expert knowledge of Windows system administration and commands",
                "versions": ["Windows Server 2019", "Windows Server 2022", "Windows 10", "Windows 11"],
                "shells": ["Command Prompt (cmd)", "PowerShell", "Windows Terminal"],
                "management_tools": ["MMC", "Server Manager", "Computer Management", "Event Viewer"]
            },
            "capabilities": {
                "system_information": {
                    "description": "Commands to gather comprehensive Windows system information",
                    "keywords": ["info", "system", "hardware", "status", "details"],
                    "commands": [
                        {
                            "command": "systeminfo",
                            "description": "Comprehensive system configuration information",
                            "example_output": "Host Name: WIN-SERVER01\\nOS Name: Microsoft Windows Server 2019 Standard\\nOS Version: 10.0.17763 N/A Build 17763"
                        },
                        {
                            "command": "hostname",
                            "description": "Display computer name",
                            "example_output": "WIN-SERVER01"
                        },
                        {
                            "command": "wmic computersystem get model,name,manufacturer",
                            "description": "Hardware manufacturer and model information",
                            "example_output": "Manufacturer Model Name\\nDell Inc. PowerEdge R740 WIN-SERVER01"
                        },
                        {
                            "command": "wmic cpu get name,numberofcores,numberoflogicalprocessors",
                            "description": "CPU information including cores and threads",
                            "example_output": "Name NumberOfCores NumberOfLogicalProcessors\\nIntel(R) Xeon(R) Silver 4214 CPU @ 2.20GHz 12 24"
                        },
                        {
                            "command": "wmic memorychip get capacity,speed,manufacturer",
                            "description": "Memory module details",
                            "example_output": "Capacity Manufacturer Speed\\n17179869184 Samsung 2666"
                        },
                        {
                            "command": "wmic logicaldisk get size,freespace,caption",
                            "description": "Disk space information for all drives",
                            "example_output": "Caption FreeSpace Size\\nC: 85899345920 107374182400\\nD: 214748364800 322122547200"
                        },
                        {
                            "command": "ipconfig /all",
                            "description": "Complete network configuration",
                            "example_output": "Windows IP Configuration\\nHost Name: WIN-SERVER01\\nEthernet adapter Ethernet:\\nIPv4 Address: 192.168.1.100"
                        },
                        {
                            "command": "ver",
                            "description": "Windows version information",
                            "example_output": "Microsoft Windows [Version 10.0.17763.1697]"
                        }
                    ],
                    "comprehensive_script": """@echo off
REM Comprehensive Windows System Information Script
echo === WINDOWS SYSTEM INFORMATION ===
echo Computer Name: %COMPUTERNAME%
echo User: %USERNAME%
echo Date/Time: %DATE% %TIME%
echo.

echo === OPERATING SYSTEM ===
systeminfo | findstr /B /C:"OS Name" /C:"OS Version" /C:"System Boot Time" /C:"System Uptime"
echo.

echo === HARDWARE INFORMATION ===
wmic computersystem get manufacturer,model,totalpysicalmemory /format:list | findstr "="
wmic cpu get name,numberofcores,numberoflogicalprocessors /format:list | findstr "="
echo.

echo === MEMORY INFORMATION ===
wmic OS get TotalVisibleMemorySize,FreePhysicalMemory /format:list | findstr "="
echo.

echo === DISK INFORMATION ===
wmic logicaldisk get caption,size,freespace,filesystem /format:table
echo.

echo === NETWORK INFORMATION ===
ipconfig | findstr /C:"IPv4 Address" /C:"Subnet Mask" /C:"Default Gateway"
echo.

echo === RUNNING SERVICES ===
sc query state= running | findstr "SERVICE_NAME"
echo.

echo === SYSTEM INFORMATION COMPLETE ==="""
                },
                "process_management": {
                    "description": "Process monitoring, control, and service management",
                    "keywords": ["process", "service", "task", "kill", "monitor"],
                    "commands": [
                        {
                            "command": "tasklist",
                            "description": "List all running processes",
                            "example_output": "Image Name PID Session Name Session# Mem Usage\\nsvchost.exe 1234 Services 0 12,345 K"
                        },
                        {
                            "command": "tasklist /svc",
                            "description": "List processes with associated services",
                            "example_output": "Image Name PID Services\\nsvchost.exe 1234 AudioEndpointBuilder,AudioSrv"
                        },
                        {
                            "command": "taskkill /PID 1234",
                            "description": "Kill process by Process ID",
                            "note": "Use /F flag to force termination"
                        },
                        {
                            "command": "taskkill /IM notepad.exe",
                            "description": "Kill process by image name",
                            "note": "Kills all instances of the specified process"
                        },
                        {
                            "command": "sc query",
                            "description": "List all services and their status",
                            "example_output": "SERVICE_NAME: Spooler\\nDISPLAY_NAME: Print Spooler\\nSTATE: 4 RUNNING"
                        },
                        {
                            "command": "sc start/stop/restart servicename",
                            "description": "Control Windows services",
                            "note": "Replace servicename with actual service name"
                        },
                        {
                            "command": "net start/stop servicename",
                            "description": "Alternative service control method",
                            "example_output": "The Print Spooler service was started successfully."
                        },
                        {
                            "command": "wmic process where name='notepad.exe' get processid,commandline",
                            "description": "Get detailed process information",
                            "example_output": "CommandLine ProcessId\\nC:\\Windows\\System32\\notepad.exe 5678"
                        }
                    ]
                },
                "file_operations": {
                    "description": "File and directory manipulation commands",
                    "keywords": ["file", "directory", "copy", "move", "delete", "permissions"],
                    "commands": [
                        {
                            "command": "dir /a",
                            "description": "List all files including hidden and system files",
                            "example_output": "01/15/2024 10:30 AM <DIR> Documents\\n01/15/2024 10:31 AM 1,024 file.txt"
                        },
                        {
                            "command": "tree /f",
                            "description": "Display directory structure with files",
                            "note": "Shows hierarchical view of directories and files"
                        },
                        {
                            "command": "copy source destination",
                            "description": "Copy files",
                            "example": "copy C:\\temp\\file.txt D:\\backup\\"
                        },
                        {
                            "command": "xcopy /s /e source destination",
                            "description": "Copy directories and subdirectories",
                            "note": "/s copies subdirectories, /e includes empty directories"
                        },
                        {
                            "command": "robocopy source destination /MIR",
                            "description": "Robust file copy with mirroring",
                            "note": "More reliable than copy/xcopy for large operations"
                        },
                        {
                            "command": "attrib +h filename",
                            "description": "Set file attributes (hidden, read-only, etc.)",
                            "note": "+h hides file, -h unhides, +r read-only, -r removes read-only"
                        },
                        {
                            "command": "icacls filename /grant user:F",
                            "description": "Modify file permissions",
                            "note": "F=Full, M=Modify, R=Read, W=Write"
                        },
                        {
                            "command": "forfiles /p C:\\logs /s /m *.log /d -7 /c \"cmd /c del @path\"",
                            "description": "Delete log files older than 7 days",
                            "note": "Powerful command for bulk file operations"
                        }
                    ]
                },
                "network_operations": {
                    "description": "Network configuration and troubleshooting commands",
                    "keywords": ["network", "ip", "route", "dns", "connectivity", "firewall"],
                    "commands": [
                        {
                            "command": "ipconfig /all",
                            "description": "Complete network adapter configuration",
                            "example_output": "Ethernet adapter Ethernet:\\nConnection-specific DNS Suffix: company.local\\nIPv4 Address: 192.168.1.100"
                        },
                        {
                            "command": "ipconfig /release && ipconfig /renew",
                            "description": "Release and renew DHCP lease",
                            "note": "Useful for network troubleshooting"
                        },
                        {
                            "command": "ipconfig /flushdns",
                            "description": "Clear DNS resolver cache",
                            "example_output": "Successfully flushed the DNS Resolver Cache."
                        },
                        {
                            "command": "ping -t google.com",
                            "description": "Continuous ping (Ctrl+C to stop)",
                            "note": "Use -n 4 for 4 packets instead of continuous"
                        },
                        {
                            "command": "tracert google.com",
                            "description": "Trace route to destination",
                            "example_output": "1 <1 ms <1 ms <1 ms 192.168.1.1\\n2 15 ms 14 ms 15 ms 10.0.0.1"
                        },
                        {
                            "command": "nslookup google.com",
                            "description": "DNS lookup for domain",
                            "example_output": "Server: 8.8.8.8\\nAddress: 8.8.8.8\\nName: google.com\\nAddress: 172.217.164.110"
                        },
                        {
                            "command": "netstat -an",
                            "description": "Show all network connections and listening ports",
                            "example_output": "TCP 0.0.0.0:80 0.0.0.0:0 LISTENING\\nTCP 192.168.1.100:3389 192.168.1.50:54321 ESTABLISHED"
                        },
                        {
                            "command": "netsh advfirewall show allprofiles",
                            "description": "Show Windows Firewall status",
                            "example_output": "Domain Profile Settings:\\nState ON\\nFirewall Policy BlockInbound,AllowOutbound"
                        },
                        {
                            "command": "arp -a",
                            "description": "Display ARP table",
                            "example_output": "Interface: 192.168.1.100\\n192.168.1.1 00-1a-2b-3c-4d-5e dynamic"
                        }
                    ]
                },
                "event_log_analysis": {
                    "description": "Windows Event Log analysis and monitoring",
                    "keywords": ["event", "log", "error", "warning", "audit", "security"],
                    "commands": [
                        {
                            "command": "wevtutil qe System /c:10 /rd:true /f:text",
                            "description": "Query last 10 System events in text format",
                            "note": "/rd:true for reverse order (newest first)"
                        },
                        {
                            "command": "wevtutil qe Application /q:\"*[System[Level=2]]\" /c:5 /f:text",
                            "description": "Query last 5 Application errors (Level=2)",
                            "note": "Level 1=Critical, 2=Error, 3=Warning, 4=Information"
                        },
                        {
                            "command": "wevtutil qe Security /q:\"*[System[EventID=4624]]\" /c:10 /f:text",
                            "description": "Query successful logon events (Event ID 4624)",
                            "note": "4625 for failed logons, 4634 for logoffs"
                        },
                        {
                            "command": "wevtutil el",
                            "description": "List all available event logs",
                            "example_output": "Application\\nSecurity\\nSystem\\nWindows PowerShell"
                        },
                        {
                            "command": "eventcreate /T ERROR /ID 999 /L APPLICATION /SO \"MyApp\" /D \"Test error message\"",
                            "description": "Create custom event log entry",
                            "note": "Useful for application logging and testing"
                        }
                    ]
                },
                "registry_operations": {
                    "description": "Windows Registry query and modification commands",
                    "keywords": ["registry", "reg", "key", "value", "configuration"],
                    "commands": [
                        {
                            "command": "reg query HKLM\\SOFTWARE\\Microsoft\\Windows\\CurrentVersion",
                            "description": "Query registry key for Windows version info",
                            "example_output": "ProductName REG_SZ Windows Server 2019 Standard\\nCurrentVersion REG_SZ 6.3"
                        },
                        {
                            "command": "reg add HKLM\\SOFTWARE\\MyApp /v Setting1 /t REG_SZ /d \"Value1\"",
                            "description": "Add registry value",
                            "note": "REG_SZ for string, REG_DWORD for number"
                        },
                        {
                            "command": "reg delete HKLM\\SOFTWARE\\MyApp /v Setting1 /f",
                            "description": "Delete registry value (/f for force)",
                            "note": "Be very careful with registry deletions"
                        },
                        {
                            "command": "reg export HKLM\\SOFTWARE\\MyApp C:\\backup\\myapp.reg",
                            "description": "Export registry key to file",
                            "note": "Always backup before making changes"
                        },
                        {
                            "command": "reg import C:\\backup\\myapp.reg",
                            "description": "Import registry from file",
                            "note": "Restores previously exported settings"
                        }
                    ]
                },
                "performance_monitoring": {
                    "description": "System performance monitoring and analysis",
                    "keywords": ["performance", "cpu", "memory", "disk", "counter"],
                    "commands": [
                        {
                            "command": "typeperf \"\\Processor(_Total)\\% Processor Time\" -sc 10",
                            "description": "Monitor CPU usage for 10 samples",
                            "example_output": "\"01/15/2024 10:30:00.000\",\"25.123456\""
                        },
                        {
                            "command": "typeperf \"\\Memory\\Available MBytes\" -sc 5",
                            "description": "Monitor available memory for 5 samples",
                            "example_output": "\"01/15/2024 10:30:00.000\",\"4096.000000\""
                        },
                        {
                            "command": "wmic cpu get loadpercentage /value",
                            "description": "Get current CPU load percentage",
                            "example_output": "LoadPercentage=25"
                        },
                        {
                            "command": "wmic OS get FreePhysicalMemory,TotalVisibleMemorySize /value",
                            "description": "Get memory statistics",
                            "example_output": "FreePhysicalMemory=4194304\\nTotalVisibleMemorySize=8388608"
                        },
                        {
                            "command": "perfmon",
                            "description": "Launch Performance Monitor GUI",
                            "note": "Graphical tool for detailed performance analysis"
                        }
                    ]
                }
            },
            "scripting_patterns": [
                {
                    "name": "System Health Check Batch Script",
                    "description": "Comprehensive Windows system health monitoring",
                    "script": """@echo off
REM Windows System Health Check Script
echo === WINDOWS SYSTEM HEALTH CHECK ===
echo Date/Time: %DATE% %TIME%
echo Computer: %COMPUTERNAME%
echo.

echo === CPU USAGE ===
wmic cpu get loadpercentage /value | findstr "LoadPercentage"

echo.
echo === MEMORY USAGE ===
wmic OS get FreePhysicalMemory,TotalVisibleMemorySize /format:list | findstr "="

echo.
echo === DISK SPACE ===
wmic logicaldisk get caption,size,freespace,filesystem /format:table

echo.
echo === RUNNING SERVICES (STOPPED) ===
sc query state= stopped | findstr "SERVICE_NAME"

echo.
echo === RECENT ERRORS ===
wevtutil qe System /q:"*[System[Level=2]]" /c:5 /f:text | findstr "Error"

echo.
echo === NETWORK CONNECTIVITY ===
ping -n 1 8.8.8.8 >nul 2>&1 && echo Internet: OK || echo Internet: FAILED

echo.
echo === HEALTH CHECK COMPLETE ===
pause"""
                },
                {
                    "name": "Service Management Script",
                    "description": "Manage Windows services with error handling",
                    "script": """@echo off
setlocal enabledelayedexpansion

REM Service Management Script
set SERVICE_NAME=%1
if "%SERVICE_NAME%"=="" (
    echo Usage: %0 ^<service_name^> [start^|stop^|restart^|status]
    exit /b 1
)

set ACTION=%2
if "%ACTION%"=="" set ACTION=status

echo Managing service: %SERVICE_NAME%
echo Action: %ACTION%
echo.

if /i "%ACTION%"=="start" (
    echo Starting service...
    sc start "%SERVICE_NAME%"
    if !errorlevel! equ 0 (
        echo Service started successfully.
    ) else (
        echo Failed to start service. Error code: !errorlevel!
    )
) else if /i "%ACTION%"=="stop" (
    echo Stopping service...
    sc stop "%SERVICE_NAME%"
    if !errorlevel! equ 0 (
        echo Service stopped successfully.
    ) else (
        echo Failed to stop service. Error code: !errorlevel!
    )
) else if /i "%ACTION%"=="restart" (
    echo Restarting service...
    sc stop "%SERVICE_NAME%"
    timeout /t 5 /nobreak >nul
    sc start "%SERVICE_NAME%"
) else (
    echo Service status:
    sc query "%SERVICE_NAME%"
)

echo.
echo Operation complete."""
                }
            ],
            "best_practices": [
                "Run Command Prompt as Administrator for system operations",
                "Always backup registry before making changes",
                "Use robocopy instead of copy/xcopy for large file operations",
                "Monitor Event Logs regularly for system issues",
                "Use Windows Update to keep system secure",
                "Implement proper user account control (UAC)",
                "Use Group Policy for enterprise configuration management",
                "Regular system file checks with sfc /scannow"
            ],
            "troubleshooting_workflows": [
                {
                    "issue": "High CPU Usage",
                    "steps": [
                        "Check current CPU usage: wmic cpu get loadpercentage",
                        "Identify top CPU consumers: tasklist /fo table | sort /r /+5",
                        "Get detailed process info: wmic process where name='process.exe' get processid,commandline",
                        "Check for Windows Updates: sconfig (Server Core) or Windows Update GUI",
                        "Consider restarting problematic services: sc restart servicename",
                        "Use Performance Monitor for detailed analysis: perfmon"
                    ]
                },
                {
                    "issue": "High Memory Usage",
                    "steps": [
                        "Check memory usage: wmic OS get FreePhysicalMemory,TotalVisibleMemorySize",
                        "Identify memory consumers: tasklist /fo table | sort /r /+5",
                        "Check for memory leaks: monitor specific processes over time",
                        "Clear system cache: Clear-DnsClientCache (PowerShell)",
                        "Restart memory-intensive services if safe",
                        "Consider adding more RAM if consistently high"
                    ]
                },
                {
                    "issue": "Disk Space Low",
                    "steps": [
                        "Check disk usage: wmic logicaldisk get caption,size,freespace",
                        "Find large files: forfiles /p C:\\ /s /m *.* /c \"cmd /c if @fsize gtr 104857600 echo @path @fsize\"",
                        "Clean temporary files: del /q /f /s %TEMP%\\*",
                        "Run Disk Cleanup: cleanmgr /sagerun:1",
                        "Check Windows Update cleanup: dism /online /cleanup-image /startcomponentcleanup",
                        "Analyze directory sizes: dir /s C:\\ | find \"Directory\""
                    ]
                }
            ]
        }
    
    async def discover_capabilities(self) -> APIDiscoveryResult:
        return APIDiscoveryResult(
            endpoints=[],
            capabilities=list(self.knowledge["capabilities"].keys()),
            authentication_methods=[],
            rate_limits={},
            documentation_urls=[],
            examples=[]
        )
    
    def get_context_for_request(self, request_keywords: List[str]) -> Dict[str, Any]:
        keyword_set = set(word.lower() for word in request_keywords)
        relevant_capabilities = []
        
        if any(word in keyword_set for word in ["system", "info", "information", "details"]):
            relevant_capabilities.append(self.knowledge["capabilities"]["system_information"])
        
        if any(word in keyword_set for word in ["process", "service", "task", "running"]):
            relevant_capabilities.append(self.knowledge["capabilities"]["process_management"])
        
        if any(word in keyword_set for word in ["file", "directory", "copy", "move"]):
            relevant_capabilities.append(self.knowledge["capabilities"]["file_operations"])
        
        if any(word in keyword_set for word in ["network", "ip", "connectivity", "ping"]):
            relevant_capabilities.append(self.knowledge["capabilities"]["network_operations"])
        
        if any(word in keyword_set for word in ["event", "log", "error", "warning"]):
            relevant_capabilities.append(self.knowledge["capabilities"]["event_log_analysis"])
        
        if any(word in keyword_set for word in ["registry", "reg", "configuration"]):
            relevant_capabilities.append(self.knowledge["capabilities"]["registry_operations"])
        
        if any(word in keyword_set for word in ["performance", "cpu", "memory", "monitor"]):
            relevant_capabilities.append(self.knowledge["capabilities"]["performance_monitoring"])
        
        return {
            "domain": "Windows System Administration Expertise",
            "system_info": self.knowledge["system_info"],
            "relevant_capabilities": relevant_capabilities,
            "scripting_patterns": self.knowledge["scripting_patterns"],
            "best_practices": self.knowledge["best_practices"],
            "troubleshooting_workflows": self.knowledge["troubleshooting_workflows"]
        }
    
    def update_knowledge(self, new_knowledge: Dict[str, Any]) -> bool:
        try:
            if "capabilities" in new_knowledge:
                self.knowledge["capabilities"].update(new_knowledge["capabilities"])
            self.metadata.last_updated = datetime.now()
            return True
        except Exception:
            return False

def register_system_expertise_domains(catalog):
    """Register all system expertise domains with the catalog"""
    catalog.register_domain(LinuxExpertiseDomain())
    catalog.register_domain(WindowsExpertiseDomain())