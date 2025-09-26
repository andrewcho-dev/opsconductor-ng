#!/usr/bin/env python3
"""
PowerShell Expertise Knowledge Domain
Comprehensive PowerShell scripting and administration capabilities
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

class PowerShellExpertiseDomain(KnowledgeDomain):
    """Comprehensive PowerShell scripting and administration expertise"""
    
    def __init__(self):
        metadata = KnowledgeMetadata(
            domain_id="powershell_expertise",
            domain_type=KnowledgeDomainType.CORE_SERVICE,
            version="1.0.0",
            last_updated=datetime.now(),
            size_bytes=0,
            priority=ContextPriority.CRITICAL,
            keywords=["powershell", "ps1", "script", "cmdlet", "pipeline", "automation"],
            dependencies=[],
            performance_metrics={}
        )
        super().__init__("powershell_expertise", metadata)
        self.knowledge = self._initialize_powershell_knowledge()
    
    def _initialize_powershell_knowledge(self) -> Dict[str, Any]:
        return {
            "system_info": {
                "description": "Expert knowledge of PowerShell scripting and Windows automation",
                "versions": ["PowerShell 5.1", "PowerShell 7.x", "PowerShell Core"],
                "execution_policies": ["Restricted", "AllSigned", "RemoteSigned", "Unrestricted", "Bypass"],
                "ise_alternatives": ["PowerShell ISE", "Visual Studio Code", "Windows Terminal"]
            },
            "capabilities": {
                "system_information": {
                    "description": "PowerShell cmdlets for comprehensive system information gathering",
                    "keywords": ["system", "info", "computer", "hardware", "get-computerinfo"],
                    "cmdlets": [
                        {
                            "cmdlet": "Get-ComputerInfo",
                            "description": "Comprehensive system information (PowerShell 5.1+)",
                            "example": "Get-ComputerInfo | Select-Object WindowsProductName, WindowsVersion, TotalPhysicalMemory",
                            "output_sample": "WindowsProductName: Windows Server 2019 Standard\\nWindowsVersion: 1809\\nTotalPhysicalMemory: 17179869184"
                        },
                        {
                            "cmdlet": "Get-WmiObject Win32_ComputerSystem",
                            "description": "Computer system information via WMI",
                            "example": "Get-WmiObject Win32_ComputerSystem | Select-Object Name, Manufacturer, Model, TotalPhysicalMemory",
                            "output_sample": "Name: WIN-SERVER01\\nManufacturer: Dell Inc.\\nModel: PowerEdge R740"
                        },
                        {
                            "cmdlet": "Get-WmiObject Win32_OperatingSystem",
                            "description": "Operating system details",
                            "example": "Get-WmiObject Win32_OperatingSystem | Select-Object Caption, Version, LastBootUpTime, FreePhysicalMemory",
                            "output_sample": "Caption: Microsoft Windows Server 2019 Standard\\nVersion: 10.0.17763"
                        },
                        {
                            "cmdlet": "Get-WmiObject Win32_Processor",
                            "description": "CPU information",
                            "example": "Get-WmiObject Win32_Processor | Select-Object Name, NumberOfCores, NumberOfLogicalProcessors, LoadPercentage",
                            "output_sample": "Name: Intel(R) Xeon(R) Silver 4214 CPU @ 2.20GHz\\nNumberOfCores: 12"
                        },
                        {
                            "cmdlet": "Get-WmiObject Win32_LogicalDisk",
                            "description": "Disk space information",
                            "example": "Get-WmiObject Win32_LogicalDisk | Select-Object DeviceID, Size, FreeSpace, @{Name='FreePercent';Expression={[math]::Round(($_.FreeSpace/$_.Size)*100,2)}}",
                            "output_sample": "DeviceID: C:\\nSize: 107374182400\\nFreeSpace: 85899345920\\nFreePercent: 80.0"
                        },
                        {
                            "cmdlet": "Get-NetAdapter",
                            "description": "Network adapter information",
                            "example": "Get-NetAdapter | Where-Object {$_.Status -eq 'Up'} | Select-Object Name, InterfaceDescription, LinkSpeed",
                            "output_sample": "Name: Ethernet\\nInterfaceDescription: Intel(R) 82574L Gigabit Network Connection"
                        }
                    ],
                    "comprehensive_script": """# Comprehensive PowerShell System Information Script
Write-Host "=== POWERSHELL SYSTEM INFORMATION ===" -ForegroundColor Green
Write-Host "Computer: $env:COMPUTERNAME" -ForegroundColor Yellow
Write-Host "User: $env:USERNAME" -ForegroundColor Yellow
Write-Host "Date/Time: $(Get-Date)" -ForegroundColor Yellow
Write-Host ""

Write-Host "=== OPERATING SYSTEM ===" -ForegroundColor Green
$OS = Get-WmiObject Win32_OperatingSystem
Write-Host "OS Name: $($OS.Caption)"
Write-Host "Version: $($OS.Version)"
Write-Host "Architecture: $($OS.OSArchitecture)"
Write-Host "Last Boot: $($OS.ConvertToDateTime($OS.LastBootUpTime))"
Write-Host "Uptime: $((Get-Date) - $OS.ConvertToDateTime($OS.LastBootUpTime))"
Write-Host ""

Write-Host "=== HARDWARE INFORMATION ===" -ForegroundColor Green
$Computer = Get-WmiObject Win32_ComputerSystem
Write-Host "Manufacturer: $($Computer.Manufacturer)"
Write-Host "Model: $($Computer.Model)"
Write-Host "Total RAM: $([math]::Round($Computer.TotalPhysicalMemory/1GB,2)) GB"

$CPU = Get-WmiObject Win32_Processor | Select-Object -First 1
Write-Host "CPU: $($CPU.Name)"
Write-Host "Cores: $($CPU.NumberOfCores)"
Write-Host "Logical Processors: $($CPU.NumberOfLogicalProcessors)"
Write-Host ""

Write-Host "=== MEMORY USAGE ===" -ForegroundColor Green
$Memory = Get-WmiObject Win32_OperatingSystem
$TotalRAM = [math]::Round($Memory.TotalVisibleMemorySize/1MB,2)
$FreeRAM = [math]::Round($Memory.FreePhysicalMemory/1MB,2)
$UsedRAM = $TotalRAM - $FreeRAM
Write-Host "Total RAM: $TotalRAM GB"
Write-Host "Used RAM: $UsedRAM GB"
Write-Host "Free RAM: $FreeRAM GB"
Write-Host "Usage: $([math]::Round(($UsedRAM/$TotalRAM)*100,2))%"
Write-Host ""

Write-Host "=== DISK INFORMATION ===" -ForegroundColor Green
Get-WmiObject Win32_LogicalDisk | Where-Object {$_.DriveType -eq 3} | ForEach-Object {
    $Size = [math]::Round($_.Size/1GB,2)
    $Free = [math]::Round($_.FreeSpace/1GB,2)
    $Used = $Size - $Free
    $Percent = [math]::Round(($Used/$Size)*100,2)
    Write-Host "Drive $($_.DeviceID) - Size: $Size GB, Used: $Used GB, Free: $Free GB, Usage: $Percent%"
}
Write-Host ""

Write-Host "=== NETWORK INFORMATION ===" -ForegroundColor Green
Get-NetAdapter | Where-Object {$_.Status -eq 'Up'} | ForEach-Object {
    $IP = (Get-NetIPAddress -InterfaceIndex $_.InterfaceIndex -AddressFamily IPv4 -ErrorAction SilentlyContinue).IPAddress
    Write-Host "Interface: $($_.Name) - IP: $IP - Speed: $($_.LinkSpeed)"
}
Write-Host ""

Write-Host "=== SYSTEM INFORMATION COMPLETE ===" -ForegroundColor Green"""
                },
                "process_management": {
                    "description": "PowerShell process and service management cmdlets",
                    "keywords": ["process", "service", "get-process", "start-service", "stop-service"],
                    "cmdlets": [
                        {
                            "cmdlet": "Get-Process",
                            "description": "List running processes with detailed information",
                            "example": "Get-Process | Sort-Object CPU -Descending | Select-Object -First 10 Name, Id, CPU, WorkingSet",
                            "output_sample": "Name: svchost\\nId: 1234\\nCPU: 45.67\\nWorkingSet: 52428800"
                        },
                        {
                            "cmdlet": "Stop-Process",
                            "description": "Stop processes by name or ID",
                            "example": "Stop-Process -Name 'notepad' -Force",
                            "note": "Use -Force to forcefully terminate"
                        },
                        {
                            "cmdlet": "Start-Process",
                            "description": "Start new processes",
                            "example": "Start-Process -FilePath 'notepad.exe' -ArgumentList 'C:\\temp\\file.txt'",
                            "note": "Can specify working directory and credentials"
                        },
                        {
                            "cmdlet": "Get-Service",
                            "description": "List Windows services and their status",
                            "example": "Get-Service | Where-Object {$_.Status -eq 'Stopped'} | Select-Object Name, Status, StartType",
                            "output_sample": "Name: Spooler\\nStatus: Running\\nStartType: Automatic"
                        },
                        {
                            "cmdlet": "Start-Service / Stop-Service / Restart-Service",
                            "description": "Control Windows services",
                            "example": "Restart-Service -Name 'Spooler' -Force",
                            "note": "Use -Force to stop dependent services"
                        },
                        {
                            "cmdlet": "Set-Service",
                            "description": "Configure service properties",
                            "example": "Set-Service -Name 'Spooler' -StartupType 'Manual'",
                            "note": "StartupType: Automatic, Manual, Disabled"
                        },
                        {
                            "cmdlet": "Get-WmiObject Win32_Service",
                            "description": "Detailed service information via WMI",
                            "example": "Get-WmiObject Win32_Service | Where-Object {$_.State -eq 'Running'} | Select-Object Name, ProcessId, StartMode",
                            "output_sample": "Name: Spooler\\nProcessId: 1234\\nStartMode: Auto"
                        }
                    ]
                },
                "file_operations": {
                    "description": "PowerShell file and directory manipulation cmdlets",
                    "keywords": ["file", "directory", "copy-item", "move-item", "get-childitem"],
                    "cmdlets": [
                        {
                            "cmdlet": "Get-ChildItem",
                            "description": "List files and directories (ls/dir equivalent)",
                            "example": "Get-ChildItem -Path C:\\temp -Recurse -Include '*.log' | Select-Object Name, Length, LastWriteTime",
                            "output_sample": "Name: app.log\\nLength: 1048576\\nLastWriteTime: 1/15/2024 10:30:00 AM"
                        },
                        {
                            "cmdlet": "Copy-Item",
                            "description": "Copy files and directories",
                            "example": "Copy-Item -Path 'C:\\source\\*' -Destination 'C:\\destination' -Recurse -Force",
                            "note": "-Recurse for directories, -Force to overwrite"
                        },
                        {
                            "cmdlet": "Move-Item",
                            "description": "Move or rename files and directories",
                            "example": "Move-Item -Path 'C:\\temp\\oldname.txt' -Destination 'C:\\temp\\newname.txt'",
                            "note": "Can move across drives and rename simultaneously"
                        },
                        {
                            "cmdlet": "Remove-Item",
                            "description": "Delete files and directories",
                            "example": "Remove-Item -Path 'C:\\temp\\*.log' -Force -Recurse",
                            "note": "-Recurse for directories, -Force for read-only files"
                        },
                        {
                            "cmdlet": "New-Item",
                            "description": "Create new files and directories",
                            "example": "New-Item -Path 'C:\\temp\\newfile.txt' -ItemType File -Value 'Initial content'",
                            "note": "ItemType: File, Directory, SymbolicLink, etc."
                        },
                        {
                            "cmdlet": "Get-Content / Set-Content",
                            "description": "Read and write file content",
                            "example": "Get-Content -Path 'C:\\temp\\file.txt' | Where-Object {$_ -match 'error'}",
                            "note": "Set-Content overwrites, Add-Content appends"
                        },
                        {
                            "cmdlet": "Test-Path",
                            "description": "Check if file or directory exists",
                            "example": "if (Test-Path 'C:\\temp\\file.txt') { Write-Host 'File exists' }",
                            "output_sample": "True or False"
                        },
                        {
                            "cmdlet": "Get-Acl / Set-Acl",
                            "description": "Get and set file permissions",
                            "example": "Get-Acl -Path 'C:\\temp\\file.txt' | Format-List",
                            "note": "Use Set-Acl to modify permissions"
                        }
                    ]
                },
                "network_operations": {
                    "description": "PowerShell network configuration and troubleshooting cmdlets",
                    "keywords": ["network", "test-connection", "get-netadapter", "invoke-webrequest"],
                    "cmdlets": [
                        {
                            "cmdlet": "Test-Connection",
                            "description": "Ping hosts (ping equivalent)",
                            "example": "Test-Connection -ComputerName 'google.com' -Count 4 | Select-Object Source, Destination, ResponseTime",
                            "output_sample": "Source: WIN-SERVER01\\nDestination: google.com\\nResponseTime: 15"
                        },
                        {
                            "cmdlet": "Test-NetConnection",
                            "description": "Advanced network connectivity testing",
                            "example": "Test-NetConnection -ComputerName 'google.com' -Port 443 | Select-Object ComputerName, RemotePort, TcpTestSucceeded",
                            "output_sample": "ComputerName: google.com\\nRemotePort: 443\\nTcpTestSucceeded: True"
                        },
                        {
                            "cmdlet": "Get-NetAdapter",
                            "description": "Network adapter information",
                            "example": "Get-NetAdapter | Where-Object {$_.Status -eq 'Up'} | Select-Object Name, InterfaceDescription, LinkSpeed",
                            "output_sample": "Name: Ethernet\\nLinkSpeed: 1 Gbps"
                        },
                        {
                            "cmdlet": "Get-NetIPAddress",
                            "description": "IP address configuration",
                            "example": "Get-NetIPAddress -AddressFamily IPv4 | Where-Object {$_.IPAddress -ne '127.0.0.1'} | Select-Object InterfaceAlias, IPAddress, PrefixLength",
                            "output_sample": "InterfaceAlias: Ethernet\\nIPAddress: 192.168.1.100\\nPrefixLength: 24"
                        },
                        {
                            "cmdlet": "Get-NetRoute",
                            "description": "Routing table information",
                            "example": "Get-NetRoute -DestinationPrefix '0.0.0.0/0' | Select-Object DestinationPrefix, NextHop, InterfaceAlias",
                            "output_sample": "DestinationPrefix: 0.0.0.0/0\\nNextHop: 192.168.1.1"
                        },
                        {
                            "cmdlet": "Resolve-DnsName",
                            "description": "DNS name resolution",
                            "example": "Resolve-DnsName -Name 'google.com' -Type A | Select-Object Name, IPAddress",
                            "output_sample": "Name: google.com\\nIPAddress: 172.217.164.110"
                        },
                        {
                            "cmdlet": "Get-NetTCPConnection",
                            "description": "TCP connection information",
                            "example": "Get-NetTCPConnection -State Established | Select-Object LocalAddress, LocalPort, RemoteAddress, RemotePort, OwningProcess",
                            "output_sample": "LocalAddress: 192.168.1.100\\nLocalPort: 3389\\nRemoteAddress: 192.168.1.50"
                        },
                        {
                            "cmdlet": "Invoke-WebRequest",
                            "description": "HTTP web requests",
                            "example": "Invoke-WebRequest -Uri 'https://api.github.com' | Select-Object StatusCode, StatusDescription",
                            "output_sample": "StatusCode: 200\\nStatusDescription: OK"
                        }
                    ]
                },
                "event_log_management": {
                    "description": "PowerShell Event Log analysis and management cmdlets",
                    "keywords": ["event", "log", "get-eventlog", "get-winevent", "error", "warning"],
                    "cmdlets": [
                        {
                            "cmdlet": "Get-EventLog",
                            "description": "Get events from classic event logs",
                            "example": "Get-EventLog -LogName System -EntryType Error -Newest 10 | Select-Object TimeGenerated, Source, EventID, Message",
                            "output_sample": "TimeGenerated: 1/15/2024 10:30:00 AM\\nSource: Service Control Manager\\nEventID: 7034"
                        },
                        {
                            "cmdlet": "Get-WinEvent",
                            "description": "Get events from Windows Event Log (newer method)",
                            "example": "Get-WinEvent -LogName 'Application' -MaxEvents 10 | Where-Object {$_.LevelDisplayName -eq 'Error'}",
                            "note": "More powerful than Get-EventLog, supports newer log formats"
                        },
                        {
                            "cmdlet": "Get-WinEvent with FilterHashtable",
                            "description": "Efficient event filtering",
                            "example": "Get-WinEvent -FilterHashtable @{LogName='Security'; ID=4624; StartTime=(Get-Date).AddDays(-1)}",
                            "note": "Much faster than Where-Object filtering"
                        },
                        {
                            "cmdlet": "Write-EventLog",
                            "description": "Write custom events to event log",
                            "example": "Write-EventLog -LogName Application -Source 'MyApp' -EventId 1001 -EntryType Information -Message 'Application started successfully'",
                            "note": "Source must be registered first with New-EventLog"
                        },
                        {
                            "cmdlet": "Clear-EventLog",
                            "description": "Clear event log entries",
                            "example": "Clear-EventLog -LogName Application",
                            "note": "Use with caution, creates backup before clearing"
                        }
                    ]
                },
                "registry_management": {
                    "description": "PowerShell Registry manipulation cmdlets",
                    "keywords": ["registry", "get-itemproperty", "set-itemproperty", "new-item"],
                    "cmdlets": [
                        {
                            "cmdlet": "Get-ItemProperty",
                            "description": "Read registry values",
                            "example": "Get-ItemProperty -Path 'HKLM:\\SOFTWARE\\Microsoft\\Windows\\CurrentVersion' -Name 'ProductName'",
                            "output_sample": "ProductName: Windows Server 2019 Standard"
                        },
                        {
                            "cmdlet": "Set-ItemProperty",
                            "description": "Set registry values",
                            "example": "Set-ItemProperty -Path 'HKLM:\\SOFTWARE\\MyApp' -Name 'Setting1' -Value 'NewValue'",
                            "note": "Creates the value if it doesn't exist"
                        },
                        {
                            "cmdlet": "New-Item",
                            "description": "Create new registry keys",
                            "example": "New-Item -Path 'HKLM:\\SOFTWARE\\MyApp' -Force",
                            "note": "-Force creates parent keys if they don't exist"
                        },
                        {
                            "cmdlet": "Remove-Item / Remove-ItemProperty",
                            "description": "Delete registry keys and values",
                            "example": "Remove-ItemProperty -Path 'HKLM:\\SOFTWARE\\MyApp' -Name 'Setting1'",
                            "note": "Remove-Item deletes entire keys"
                        },
                        {
                            "cmdlet": "Test-Path",
                            "description": "Check if registry key exists",
                            "example": "if (Test-Path 'HKLM:\\SOFTWARE\\MyApp') { Write-Host 'Key exists' }",
                            "output_sample": "True or False"
                        }
                    ]
                },
                "advanced_scripting": {
                    "description": "Advanced PowerShell scripting concepts and patterns",
                    "keywords": ["function", "parameter", "pipeline", "object", "foreach", "where-object"],
                    "concepts": [
                        {
                            "concept": "Functions and Parameters",
                            "description": "Creating reusable functions with parameters",
                            "example": """function Get-SystemInfo {
    [CmdletBinding()]
    param(
        [Parameter(Mandatory=$true)]
        [string]$ComputerName,
        
        [Parameter()]
        [switch]$IncludeServices
    )
    
    $Computer = Get-WmiObject Win32_ComputerSystem -ComputerName $ComputerName
    $OS = Get-WmiObject Win32_OperatingSystem -ComputerName $ComputerName
    
    $Result = [PSCustomObject]@{
        ComputerName = $ComputerName
        Manufacturer = $Computer.Manufacturer
        Model = $Computer.Model
        OS = $OS.Caption
        TotalRAM = [math]::Round($Computer.TotalPhysicalMemory/1GB,2)
        LastBoot = $OS.ConvertToDateTime($OS.LastBootUpTime)
    }
    
    if ($IncludeServices) {
        $Result | Add-Member -MemberType NoteProperty -Name 'RunningServices' -Value (Get-Service | Where-Object {$_.Status -eq 'Running'}).Count
    }
    
    return $Result
}"""
                        },
                        {
                            "concept": "Pipeline Processing",
                            "description": "Efficient data processing through PowerShell pipeline",
                            "example": """# Process large datasets efficiently
Get-Process | 
    Where-Object {$_.WorkingSet -gt 100MB} |
    Sort-Object WorkingSet -Descending |
    Select-Object Name, Id, @{Name='MemoryMB';Expression={[math]::Round($_.WorkingSet/1MB,2)}} |
    Export-Csv -Path 'C:\\temp\\high-memory-processes.csv' -NoTypeInformation"""
                        },
                        {
                            "concept": "Error Handling",
                            "description": "Robust error handling with try/catch",
                            "example": """function Test-ServiceStatus {
    param([string]$ServiceName)
    
    try {
        $Service = Get-Service -Name $ServiceName -ErrorAction Stop
        Write-Host "Service '$ServiceName' is $($Service.Status)" -ForegroundColor Green
        return $Service.Status
    }
    catch [Microsoft.PowerShell.Commands.ServiceCommandException] {
        Write-Warning "Service '$ServiceName' not found"
        return $null
    }
    catch {
        Write-Error "Unexpected error: $($_.Exception.Message)"
        return $null
    }
}"""
                        },
                        {
                            "concept": "Remote Execution",
                            "description": "Execute commands on remote computers",
                            "example": """# Enable PowerShell Remoting (run once on target)
Enable-PSRemoting -Force

# Execute commands remotely
Invoke-Command -ComputerName 'Server01', 'Server02' -ScriptBlock {
    Get-Service | Where-Object {$_.Status -eq 'Stopped'} | Select-Object Name, Status
} -Credential (Get-Credential)

# Persistent sessions for multiple commands
$Session = New-PSSession -ComputerName 'Server01' -Credential (Get-Credential)
Invoke-Command -Session $Session -ScriptBlock { Get-Process }
Remove-PSSession $Session"""
                        },
                        {
                            "concept": "Custom Objects and Output",
                            "description": "Creating structured output objects",
                            "example": """function Get-DiskSpaceReport {
    param([string[]]$ComputerName = $env:COMPUTERNAME)
    
    foreach ($Computer in $ComputerName) {
        try {
            $Disks = Get-WmiObject Win32_LogicalDisk -ComputerName $Computer -Filter "DriveType=3"
            
            foreach ($Disk in $Disks) {
                [PSCustomObject]@{
                    ComputerName = $Computer
                    Drive = $Disk.DeviceID
                    Label = $Disk.VolumeName
                    SizeGB = [math]::Round($Disk.Size/1GB,2)
                    FreeGB = [math]::Round($Disk.FreeSpace/1GB,2)
                    UsedGB = [math]::Round(($Disk.Size - $Disk.FreeSpace)/1GB,2)
                    PercentFree = [math]::Round(($Disk.FreeSpace/$Disk.Size)*100,2)
                    Status = if (($Disk.FreeSpace/$Disk.Size) -lt 0.1) { 'Critical' } 
                            elseif (($Disk.FreeSpace/$Disk.Size) -lt 0.2) { 'Warning' } 
                            else { 'OK' }
                }
            }
        }
        catch {
            Write-Warning "Failed to get disk info from $Computer`: $($_.Exception.Message)"
        }
    }
}"""
                        }
                    ]
                },
                "automation_patterns": {
                    "description": "Common PowerShell automation patterns and best practices",
                    "keywords": ["automation", "scheduled", "task", "monitoring", "maintenance"],
                    "patterns": [
                        {
                            "name": "System Health Monitoring Script",
                            "description": "Comprehensive system health check with email alerts",
                            "script": """# System Health Monitoring Script
param(
    [string]$SMTPServer = 'smtp.company.com',
    [string]$EmailTo = 'admin@company.com',
    [string]$EmailFrom = 'monitoring@company.com'
)

function Send-HealthAlert {
    param([string]$Subject, [string]$Body)
    
    try {
        Send-MailMessage -SmtpServer $SMTPServer -To $EmailTo -From $EmailFrom -Subject $Subject -Body $Body -BodyAsHtml
        Write-Host "Alert sent: $Subject" -ForegroundColor Yellow
    }
    catch {
        Write-Error "Failed to send email: $($_.Exception.Message)"
    }
}

# Check CPU Usage
$CPU = Get-WmiObject Win32_Processor | Measure-Object -Property LoadPercentage -Average
if ($CPU.Average -gt 80) {
    Send-HealthAlert "High CPU Usage Alert" "CPU usage is $($CPU.Average)% on $env:COMPUTERNAME"
}

# Check Memory Usage
$OS = Get-WmiObject Win32_OperatingSystem
$MemoryUsage = [math]::Round((($OS.TotalVisibleMemorySize - $OS.FreePhysicalMemory) / $OS.TotalVisibleMemorySize) * 100, 2)
if ($MemoryUsage -gt 85) {
    Send-HealthAlert "High Memory Usage Alert" "Memory usage is $MemoryUsage% on $env:COMPUTERNAME"
}

# Check Disk Space
Get-WmiObject Win32_LogicalDisk -Filter "DriveType=3" | ForEach-Object {
    $FreePercent = [math]::Round(($_.FreeSpace / $_.Size) * 100, 2)
    if ($FreePercent -lt 10) {
        Send-HealthAlert "Low Disk Space Alert" "Drive $($_.DeviceID) has only $FreePercent% free space on $env:COMPUTERNAME"
    }
}

# Check Failed Services
$FailedServices = Get-Service | Where-Object {$_.Status -eq 'Stopped' -and $_.StartType -eq 'Automatic'}
if ($FailedServices) {
    $ServiceList = ($FailedServices | Select-Object -ExpandProperty Name) -join ', '
    Send-HealthAlert "Failed Services Alert" "The following automatic services are stopped on $env:COMPUTERNAME`: $ServiceList"
}

Write-Host "Health check completed at $(Get-Date)" -ForegroundColor Green"""
                        },
                        {
                            "name": "Log Cleanup and Archival Script",
                            "description": "Automated log file cleanup with archival",
                            "script": """# Log Cleanup and Archival Script
param(
    [string]$LogPath = 'C:\\Logs',
    [int]$DaysToKeep = 30,
    [string]$ArchivePath = 'C:\\LogArchive',
    [switch]$CompressArchive
)

function Write-Log {
    param([string]$Message, [string]$Level = 'INFO')
    $Timestamp = Get-Date -Format 'yyyy-MM-dd HH:mm:ss'
    Write-Host "[$Timestamp] [$Level] $Message"
}

# Create archive directory if it doesn't exist
if (!(Test-Path $ArchivePath)) {
    New-Item -Path $ArchivePath -ItemType Directory -Force
    Write-Log "Created archive directory: $ArchivePath"
}

# Find old log files
$CutoffDate = (Get-Date).AddDays(-$DaysToKeep)
$OldLogs = Get-ChildItem -Path $LogPath -Recurse -Include '*.log', '*.txt' | Where-Object {$_.LastWriteTime -lt $CutoffDate}

Write-Log "Found $($OldLogs.Count) log files older than $DaysToKeep days"

foreach ($LogFile in $OldLogs) {
    try {
        # Create archive subdirectory structure
        $RelativePath = $LogFile.FullName.Substring($LogPath.Length + 1)
        $ArchiveDir = Split-Path (Join-Path $ArchivePath $RelativePath) -Parent
        
        if (!(Test-Path $ArchiveDir)) {
            New-Item -Path $ArchiveDir -ItemType Directory -Force
        }
        
        # Move file to archive
        $ArchiveFile = Join-Path $ArchivePath $RelativePath
        Move-Item -Path $LogFile.FullName -Destination $ArchiveFile -Force
        Write-Log "Archived: $($LogFile.Name)"
        
        # Compress if requested
        if ($CompressArchive) {
            Compress-Archive -Path $ArchiveFile -DestinationPath "$ArchiveFile.zip" -Force
            Remove-Item -Path $ArchiveFile -Force
            Write-Log "Compressed: $($LogFile.Name).zip"
        }
    }
    catch {
        Write-Log "Failed to archive $($LogFile.Name): $($_.Exception.Message)" -Level 'ERROR'
    }
}

Write-Log "Log cleanup completed\""""
                        }
                    ]
                }
            },
            "best_practices": [
                "Use approved verbs for function names (Get-, Set-, New-, Remove-, etc.)",
                "Always include parameter validation and help documentation",
                "Use try/catch blocks for error handling",
                "Prefer pipeline processing over foreach loops for large datasets",
                "Use Write-Verbose, Write-Warning, and Write-Error for appropriate output",
                "Test scripts with -WhatIf parameter before execution",
                "Use PowerShell ISE or VS Code for script development",
                "Follow PowerShell naming conventions (PascalCase for functions, camelCase for variables)"
            ],
            "security_considerations": [
                "Set appropriate execution policy (RemoteSigned recommended)",
                "Sign scripts in production environments",
                "Use credential objects instead of plain text passwords",
                "Validate all user input to prevent injection attacks",
                "Use least privilege principle for script execution",
                "Audit PowerShell script execution in enterprise environments",
                "Encrypt sensitive data in scripts using ConvertTo-SecureString",
                "Use PowerShell Constrained Language Mode in restricted environments"
            ],
            "performance_tips": [
                "Use Where-Object in pipeline instead of filtering after collection",
                "Prefer Get-WmiObject over legacy commands when possible",
                "Use -Filter parameter instead of Where-Object for WMI queries",
                "Avoid using Write-Host in functions (use Write-Output instead)",
                "Use ArrayList instead of arrays for dynamic collections",
                "Cache expensive operations in variables",
                "Use background jobs for long-running operations",
                "Profile scripts with Measure-Command for optimization"
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
        
        if any(word in keyword_set for word in ["system", "info", "computer", "hardware"]):
            relevant_capabilities.append(self.knowledge["capabilities"]["system_information"])
        
        if any(word in keyword_set for word in ["process", "service", "get-process", "start-service"]):
            relevant_capabilities.append(self.knowledge["capabilities"]["process_management"])
        
        if any(word in keyword_set for word in ["file", "directory", "copy-item", "get-childitem"]):
            relevant_capabilities.append(self.knowledge["capabilities"]["file_operations"])
        
        if any(word in keyword_set for word in ["network", "test-connection", "ping", "web"]):
            relevant_capabilities.append(self.knowledge["capabilities"]["network_operations"])
        
        if any(word in keyword_set for word in ["event", "log", "get-eventlog", "error"]):
            relevant_capabilities.append(self.knowledge["capabilities"]["event_log_management"])
        
        if any(word in keyword_set for word in ["registry", "reg", "get-itemproperty"]):
            relevant_capabilities.append(self.knowledge["capabilities"]["registry_management"])
        
        if any(word in keyword_set for word in ["function", "script", "advanced", "automation"]):
            relevant_capabilities.append(self.knowledge["capabilities"]["advanced_scripting"])
            relevant_capabilities.append(self.knowledge["capabilities"]["automation_patterns"])
        
        return {
            "domain": "PowerShell Scripting and Administration Expertise",
            "system_info": self.knowledge["system_info"],
            "relevant_capabilities": relevant_capabilities,
            "best_practices": self.knowledge["best_practices"],
            "security_considerations": self.knowledge["security_considerations"],
            "performance_tips": self.knowledge["performance_tips"]
        }
    
    def update_knowledge(self, new_knowledge: Dict[str, Any]) -> bool:
        try:
            if "capabilities" in new_knowledge:
                self.knowledge["capabilities"].update(new_knowledge["capabilities"])
            self.metadata.last_updated = datetime.now()
            return True
        except Exception:
            return False

def register_powershell_expertise_domain(catalog):
    """Register PowerShell expertise domain with the catalog"""
    catalog.register_domain(PowerShellExpertiseDomain())