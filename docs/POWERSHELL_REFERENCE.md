# PowerShell Reference Guide for OpsConductor AI

## Table of Contents

1. [PowerShell Fundamentals](#powershell-fundamentals)
2. [Cmdlet Structure and Syntax](#cmdlet-structure-and-syntax)
3. [Core Cmdlets by Category](#core-cmdlets-by-category)
4. [Pipeline and Object Manipulation](#pipeline-and-object-manipulation)
5. [Scripting Constructs](#scripting-constructs)
6. [Error Handling](#error-handling)
7. [Remote Management](#remote-management)
8. [Common Patterns and Best Practices](#common-patterns-and-best-practices)

---

## PowerShell Fundamentals

### What is PowerShell?

PowerShell is a task automation and configuration management framework from Microsoft, consisting of a command-line shell and scripting language built on .NET.

### Key Concepts

- **Cmdlets**: Specialized .NET classes that perform specific operations
- **Objects**: PowerShell works with .NET objects, not text
- **Pipeline**: Pass objects between cmdlets using `|`
- **Verb-Noun**: Cmdlets follow a consistent Verb-Noun naming convention
- **Parameters**: Named arguments that modify cmdlet behavior

### PowerShell Versions

- **Windows PowerShell 5.1**: Built into Windows, .NET Framework-based
- **PowerShell 7+**: Cross-platform, .NET Core-based (recommended)

---

## Cmdlet Structure and Syntax

### Basic Syntax

```powershell
Verb-Noun -Parameter1 Value1 -Parameter2 Value2
```

### Common Verbs

| Verb | Purpose | Examples |
|------|---------|----------|
| `Get` | Retrieve information | `Get-Service`, `Get-Process` |
| `Set` | Modify configuration | `Set-Service`, `Set-ExecutionPolicy` |
| `Start` | Start a resource | `Start-Service`, `Start-Process` |
| `Stop` | Stop a resource | `Stop-Service`, `Stop-Process` |
| `Restart` | Restart a resource | `Restart-Service`, `Restart-Computer` |
| `New` | Create new resource | `New-Item`, `New-LocalUser` |
| `Remove` | Delete resource | `Remove-Item`, `Remove-LocalUser` |
| `Enable` | Enable a feature | `Enable-WindowsOptionalFeature` |
| `Disable` | Disable a feature | `Disable-WindowsOptionalFeature` |
| `Test` | Test a condition | `Test-Path`, `Test-Connection` |
| `Invoke` | Execute an action | `Invoke-Command`, `Invoke-WebRequest` |
| `Import` | Import data/module | `Import-Module`, `Import-Csv` |
| `Export` | Export data | `Export-Csv`, `Export-Clixml` |

### Parameter Types

```powershell
# Positional parameters (no parameter name needed)
Get-Service W3SVC

# Named parameters
Get-Service -Name W3SVC

# Switch parameters (boolean flags)
Get-ChildItem -Recurse

# Multiple values
Get-Service -Name W3SVC, MSSQLSERVER

# Pipeline input
Get-Process | Stop-Process
```

---

## Core Cmdlets by Category

### 1. Service Management

#### Get-Service
```powershell
# Get all services
Get-Service

# Get specific service
Get-Service -Name W3SVC

# Get services by status
Get-Service | Where-Object {$_.Status -eq 'Running'}

# Get services with wildcard
Get-Service -Name *SQL*
```

#### Start-Service / Stop-Service / Restart-Service
```powershell
# Start a service
Start-Service -Name W3SVC

# Stop a service
Stop-Service -Name W3SVC -Force

# Restart a service
Restart-Service -Name W3SVC

# Start multiple services
Start-Service -Name W3SVC, MSSQLSERVER
```

#### Set-Service
```powershell
# Set service startup type
Set-Service -Name W3SVC -StartupType Automatic

# Set service description
Set-Service -Name MyService -Description "My custom service"

# Change service credentials
Set-Service -Name MyService -Credential (Get-Credential)
```

### 2. Process Management

#### Get-Process
```powershell
# Get all processes
Get-Process

# Get specific process
Get-Process -Name chrome

# Get process by ID
Get-Process -Id 1234

# Sort by CPU usage
Get-Process | Sort-Object CPU -Descending | Select-Object -First 10

# Get process with memory info
Get-Process | Select-Object Name, CPU, @{Name="Memory(MB)";Expression={$_.WorkingSet / 1MB}}
```

#### Start-Process
```powershell
# Start a process
Start-Process notepad.exe

# Start with arguments
Start-Process powershell.exe -ArgumentList "-NoProfile", "-Command", "Get-Service"

# Start elevated (as administrator)
Start-Process powershell.exe -Verb RunAs

# Start and wait for completion
Start-Process myapp.exe -Wait
```

#### Stop-Process
```powershell
# Stop process by name
Stop-Process -Name notepad

# Stop process by ID
Stop-Process -Id 1234

# Force stop
Stop-Process -Name chrome -Force

# Stop all instances
Get-Process -Name chrome | Stop-Process
```

### 3. File System Operations

#### Get-ChildItem (alias: ls, dir)
```powershell
# List files in current directory
Get-ChildItem

# List files recursively
Get-ChildItem -Recurse

# List files with filter
Get-ChildItem -Filter *.log

# List hidden files
Get-ChildItem -Force

# List files modified in last 7 days
Get-ChildItem | Where-Object {$_.LastWriteTime -gt (Get-Date).AddDays(-7)}
```

#### New-Item
```powershell
# Create directory
New-Item -Path "C:\Temp\NewFolder" -ItemType Directory

# Create file
New-Item -Path "C:\Temp\file.txt" -ItemType File

# Create file with content
New-Item -Path "C:\Temp\file.txt" -ItemType File -Value "Hello World"
```

#### Copy-Item
```powershell
# Copy file
Copy-Item -Path "C:\Source\file.txt" -Destination "C:\Dest\file.txt"

# Copy directory recursively
Copy-Item -Path "C:\Source" -Destination "C:\Dest" -Recurse

# Copy with overwrite
Copy-Item -Path "C:\Source\file.txt" -Destination "C:\Dest\file.txt" -Force
```

#### Move-Item
```powershell
# Move file
Move-Item -Path "C:\Source\file.txt" -Destination "C:\Dest\file.txt"

# Move directory
Move-Item -Path "C:\Source\Folder" -Destination "C:\Dest\Folder"
```

#### Remove-Item
```powershell
# Delete file
Remove-Item -Path "C:\Temp\file.txt"

# Delete directory recursively
Remove-Item -Path "C:\Temp\Folder" -Recurse

# Delete with confirmation
Remove-Item -Path "C:\Temp\file.txt" -Confirm

# Delete without confirmation
Remove-Item -Path "C:\Temp\file.txt" -Force
```

#### Get-Content / Set-Content
```powershell
# Read file content
Get-Content -Path "C:\Temp\file.txt"

# Read last 10 lines
Get-Content -Path "C:\Temp\file.txt" -Tail 10

# Read and follow (like tail -f)
Get-Content -Path "C:\Temp\file.txt" -Wait

# Write content to file
Set-Content -Path "C:\Temp\file.txt" -Value "Hello World"

# Append content
Add-Content -Path "C:\Temp\file.txt" -Value "New line"
```

#### Test-Path
```powershell
# Check if file exists
Test-Path -Path "C:\Temp\file.txt"

# Check if directory exists
Test-Path -Path "C:\Temp" -PathType Container

# Check if file exists
Test-Path -Path "C:\Temp\file.txt" -PathType Leaf
```

### 4. Registry Operations

#### Get-ItemProperty
```powershell
# Read registry value
Get-ItemProperty -Path "HKLM:\SOFTWARE\Microsoft\Windows\CurrentVersion" -Name ProgramFilesDir

# Read all values in key
Get-ItemProperty -Path "HKLM:\SOFTWARE\Microsoft\Windows\CurrentVersion"
```

#### Set-ItemProperty
```powershell
# Set registry value
Set-ItemProperty -Path "HKLM:\SOFTWARE\MyApp" -Name "InstallPath" -Value "C:\MyApp"

# Create and set value
New-ItemProperty -Path "HKLM:\SOFTWARE\MyApp" -Name "Version" -Value "1.0" -PropertyType String
```

#### New-Item (Registry)
```powershell
# Create registry key
New-Item -Path "HKLM:\SOFTWARE\MyApp"

# Create key with value
New-Item -Path "HKLM:\SOFTWARE\MyApp" -Force
New-ItemProperty -Path "HKLM:\SOFTWARE\MyApp" -Name "InstallPath" -Value "C:\MyApp"
```

#### Remove-Item (Registry)
```powershell
# Delete registry key
Remove-Item -Path "HKLM:\SOFTWARE\MyApp"

# Delete registry value
Remove-ItemProperty -Path "HKLM:\SOFTWARE\MyApp" -Name "InstallPath"
```

### 5. User and Group Management

#### Get-LocalUser
```powershell
# Get all local users
Get-LocalUser

# Get specific user
Get-LocalUser -Name "Administrator"

# Get enabled users
Get-LocalUser | Where-Object {$_.Enabled -eq $true}
```

#### New-LocalUser
```powershell
# Create new user
New-LocalUser -Name "ServiceAccount" -Password (ConvertTo-SecureString "P@ssw0rd" -AsPlainText -Force) -FullName "Service Account"

# Create user with no password expiration
New-LocalUser -Name "ServiceAccount" -Password (ConvertTo-SecureString "P@ssw0rd" -AsPlainText -Force) -PasswordNeverExpires
```

#### Set-LocalUser
```powershell
# Enable user
Set-LocalUser -Name "ServiceAccount" -Enabled $true

# Disable user
Set-LocalUser -Name "ServiceAccount" -Enabled $false

# Change password
Set-LocalUser -Name "ServiceAccount" -Password (ConvertTo-SecureString "NewP@ssw0rd" -AsPlainText -Force)
```

#### Remove-LocalUser
```powershell
# Delete user
Remove-LocalUser -Name "ServiceAccount"
```

#### Get-LocalGroup
```powershell
# Get all local groups
Get-LocalGroup

# Get specific group
Get-LocalGroup -Name "Administrators"
```

#### Add-LocalGroupMember / Remove-LocalGroupMember
```powershell
# Add user to group
Add-LocalGroupMember -Group "Administrators" -Member "ServiceAccount"

# Remove user from group
Remove-LocalGroupMember -Group "Administrators" -Member "ServiceAccount"

# Get group members
Get-LocalGroupMember -Group "Administrators"
```

### 6. Network Operations

#### Test-Connection (alias: ping)
```powershell
# Ping host
Test-Connection -ComputerName google.com

# Ping with count
Test-Connection -ComputerName google.com -Count 4

# Quiet mode (returns boolean)
Test-Connection -ComputerName google.com -Quiet

# Ping multiple hosts
Test-Connection -ComputerName google.com, microsoft.com
```

#### Test-NetConnection
```powershell
# Test port connectivity
Test-NetConnection -ComputerName google.com -Port 443

# Test with detailed output
Test-NetConnection -ComputerName google.com -Port 443 -InformationLevel Detailed

# Trace route
Test-NetConnection -ComputerName google.com -TraceRoute
```

#### Get-NetIPAddress
```powershell
# Get all IP addresses
Get-NetIPAddress

# Get IPv4 addresses
Get-NetIPAddress -AddressFamily IPv4

# Get IP for specific adapter
Get-NetIPAddress -InterfaceAlias "Ethernet"
```

#### Set-NetIPAddress
```powershell
# Set static IP
New-NetIPAddress -InterfaceAlias "Ethernet" -IPAddress 192.168.1.100 -PrefixLength 24 -DefaultGateway 192.168.1.1

# Remove IP address
Remove-NetIPAddress -InterfaceAlias "Ethernet" -IPAddress 192.168.1.100
```

#### Get-NetAdapter
```powershell
# Get all network adapters
Get-NetAdapter

# Get enabled adapters
Get-NetAdapter | Where-Object {$_.Status -eq 'Up'}

# Get adapter by name
Get-NetAdapter -Name "Ethernet"
```

#### Set-DnsClientServerAddress
```powershell
# Set DNS servers
Set-DnsClientServerAddress -InterfaceAlias "Ethernet" -ServerAddresses 8.8.8.8, 8.8.4.4

# Set to DHCP
Set-DnsClientServerAddress -InterfaceAlias "Ethernet" -ResetServerAddresses
```

#### Resolve-DnsName (alias: nslookup)
```powershell
# Resolve hostname
Resolve-DnsName google.com

# Resolve specific record type
Resolve-DnsName google.com -Type MX

# Use specific DNS server
Resolve-DnsName google.com -Server 8.8.8.8
```

### 7. Firewall Management

#### Get-NetFirewallRule
```powershell
# Get all firewall rules
Get-NetFirewallRule

# Get enabled rules
Get-NetFirewallRule | Where-Object {$_.Enabled -eq $true}

# Get specific rule
Get-NetFirewallRule -Name "MyRule"

# Get rules by display name
Get-NetFirewallRule -DisplayName "*Remote Desktop*"
```

#### New-NetFirewallRule
```powershell
# Create inbound rule for port
New-NetFirewallRule -DisplayName "Allow Port 8080" -Direction Inbound -Protocol TCP -LocalPort 8080 -Action Allow

# Create outbound rule
New-NetFirewallRule -DisplayName "Block Port 445" -Direction Outbound -Protocol TCP -LocalPort 445 -Action Block

# Create rule for program
New-NetFirewallRule -DisplayName "Allow MyApp" -Direction Inbound -Program "C:\MyApp\app.exe" -Action Allow
```

#### Set-NetFirewallRule
```powershell
# Enable rule
Set-NetFirewallRule -Name "MyRule" -Enabled True

# Disable rule
Set-NetFirewallRule -Name "MyRule" -Enabled False

# Modify rule
Set-NetFirewallRule -Name "MyRule" -Action Block
```

#### Remove-NetFirewallRule
```powershell
# Delete rule
Remove-NetFirewallRule -Name "MyRule"

# Delete by display name
Remove-NetFirewallRule -DisplayName "Allow Port 8080"
```

### 8. Event Log Management

#### Get-EventLog (Windows PowerShell 5.1)
```powershell
# Get last 100 events from System log
Get-EventLog -LogName System -Newest 100

# Get errors from Application log
Get-EventLog -LogName Application -EntryType Error -Newest 50

# Get events after specific date
Get-EventLog -LogName System -After (Get-Date).AddDays(-7)

# Get events by source
Get-EventLog -LogName Application -Source "MyApp"
```

#### Get-WinEvent (PowerShell 7+)
```powershell
# Get events from System log
Get-WinEvent -LogName System -MaxEvents 100

# Filter by level (Error = 2, Warning = 3)
Get-WinEvent -LogName System | Where-Object {$_.LevelDisplayName -eq "Error"}

# Filter by event ID
Get-WinEvent -LogName System | Where-Object {$_.Id -eq 1074}

# Filter by time range
Get-WinEvent -LogName System | Where-Object {$_.TimeCreated -gt (Get-Date).AddHours(-24)}

# Use FilterHashtable for better performance
Get-WinEvent -FilterHashtable @{LogName='System'; Level=2; StartTime=(Get-Date).AddDays(-1)}
```

### 9. Disk and Volume Management

#### Get-Volume
```powershell
# Get all volumes
Get-Volume

# Get specific volume
Get-Volume -DriveLetter C

# Get volumes with low space
Get-Volume | Where-Object {$_.SizeRemaining / $_.Size -lt 0.1}
```

#### Get-Disk
```powershell
# Get all disks
Get-Disk

# Get disk by number
Get-Disk -Number 0

# Get disk health
Get-Disk | Select-Object Number, FriendlyName, HealthStatus, OperationalStatus
```

#### Get-Partition
```powershell
# Get all partitions
Get-Partition

# Get partitions on specific disk
Get-Partition -DiskNumber 0
```

#### Get-PSDrive
```powershell
# Get all drives
Get-PSDrive

# Get file system drives
Get-PSDrive -PSProvider FileSystem

# Get drive info with free space
Get-PSDrive -PSProvider FileSystem | Select-Object Name, @{Name="Used(GB)";Expression={[math]::Round($_.Used/1GB,2)}}, @{Name="Free(GB)";Expression={[math]::Round($_.Free/1GB,2)}}
```

### 10. Performance Monitoring

#### Get-Counter
```powershell
# Get CPU usage
Get-Counter '\Processor(_Total)\% Processor Time'

# Get memory usage
Get-Counter '\Memory\Available MBytes'

# Get multiple counters
Get-Counter '\Processor(_Total)\% Processor Time', '\Memory\Available MBytes'

# Continuous monitoring
Get-Counter '\Processor(_Total)\% Processor Time' -Continuous

# Sample multiple times
Get-Counter '\Processor(_Total)\% Processor Time' -SampleInterval 1 -MaxSamples 10
```

#### Get-CimInstance (replaces Get-WmiObject)
```powershell
# Get computer system info
Get-CimInstance -ClassName Win32_ComputerSystem

# Get OS info
Get-CimInstance -ClassName Win32_OperatingSystem

# Get CPU info
Get-CimInstance -ClassName Win32_Processor

# Get memory info
Get-CimInstance -ClassName Win32_PhysicalMemory

# Get disk info
Get-CimInstance -ClassName Win32_LogicalDisk

# Get network adapter info
Get-CimInstance -ClassName Win32_NetworkAdapter
```

### 11. Windows Update Management

#### Get-WindowsUpdate (requires PSWindowsUpdate module)
```powershell
# Install module
Install-Module PSWindowsUpdate -Force

# Get available updates
Get-WindowsUpdate

# Get specific category
Get-WindowsUpdate -Category "Security Updates"

# Get update history
Get-WUHistory
```

#### Install-WindowsUpdate
```powershell
# Install all updates
Install-WindowsUpdate -AcceptAll

# Install without reboot
Install-WindowsUpdate -AcceptAll -IgnoreReboot

# Install specific category
Install-WindowsUpdate -Category "Security Updates" -AcceptAll
```

### 12. Scheduled Tasks

#### Get-ScheduledTask
```powershell
# Get all scheduled tasks
Get-ScheduledTask

# Get specific task
Get-ScheduledTask -TaskName "MyTask"

# Get tasks in specific path
Get-ScheduledTask -TaskPath "\Microsoft\Windows\*"

# Get enabled tasks
Get-ScheduledTask | Where-Object {$_.State -eq 'Ready'}
```

#### Register-ScheduledTask
```powershell
# Create simple task
$action = New-ScheduledTaskAction -Execute "powershell.exe" -Argument "-File C:\Scripts\backup.ps1"
$trigger = New-ScheduledTaskTrigger -Daily -At 2am
Register-ScheduledTask -TaskName "DailyBackup" -Action $action -Trigger $trigger

# Create task with multiple triggers
$action = New-ScheduledTaskAction -Execute "powershell.exe" -Argument "-File C:\Scripts\monitor.ps1"
$trigger1 = New-ScheduledTaskTrigger -Daily -At 9am
$trigger2 = New-ScheduledTaskTrigger -Daily -At 5pm
Register-ScheduledTask -TaskName "Monitor" -Action $action -Trigger $trigger1,$trigger2
```

#### Start-ScheduledTask / Stop-ScheduledTask
```powershell
# Start task
Start-ScheduledTask -TaskName "MyTask"

# Stop task
Stop-ScheduledTask -TaskName "MyTask"
```

#### Unregister-ScheduledTask
```powershell
# Delete task
Unregister-ScheduledTask -TaskName "MyTask" -Confirm:$false
```

### 13. IIS Management (requires WebAdministration module)

#### Import-Module WebAdministration
```powershell
# Import IIS module
Import-Module WebAdministration
```

#### Get-Website
```powershell
# Get all websites
Get-Website

# Get specific website
Get-Website -Name "Default Web Site"

# Get website state
Get-Website | Select-Object Name, State, PhysicalPath
```

#### Start-Website / Stop-Website
```powershell
# Start website
Start-Website -Name "Default Web Site"

# Stop website
Stop-Website -Name "Default Web Site"
```

#### New-Website
```powershell
# Create new website
New-Website -Name "MyWebsite" -PhysicalPath "C:\inetpub\mywebsite" -Port 8080

# Create with bindings
New-Website -Name "MyWebsite" -PhysicalPath "C:\inetpub\mywebsite" -HostHeader "www.example.com" -Port 80
```

#### Get-WebAppPoolState / Restart-WebAppPool
```powershell
# Get app pool state
Get-WebAppPoolState -Name "DefaultAppPool"

# Restart app pool
Restart-WebAppPool -Name "DefaultAppPool"

# Stop app pool
Stop-WebAppPool -Name "DefaultAppPool"

# Start app pool
Start-WebAppPool -Name "DefaultAppPool"
```

### 14. Active Directory (requires ActiveDirectory module)

#### Import-Module ActiveDirectory
```powershell
# Import AD module
Import-Module ActiveDirectory
```

#### Get-ADUser
```powershell
# Get all users
Get-ADUser -Filter *

# Get specific user
Get-ADUser -Identity "jdoe"

# Get user with properties
Get-ADUser -Identity "jdoe" -Properties *

# Search users
Get-ADUser -Filter {Name -like "*John*"}

# Get users in OU
Get-ADUser -Filter * -SearchBase "OU=IT,DC=company,DC=com"
```

#### New-ADUser
```powershell
# Create new user
New-ADUser -Name "John Doe" -GivenName "John" -Surname "Doe" -SamAccountName "jdoe" -UserPrincipalName "jdoe@company.com" -Path "OU=IT,DC=company,DC=com" -AccountPassword (ConvertTo-SecureString "P@ssw0rd" -AsPlainText -Force) -Enabled $true
```

#### Set-ADUser
```powershell
# Modify user
Set-ADUser -Identity "jdoe" -Title "IT Manager" -Department "IT"

# Enable user
Set-ADUser -Identity "jdoe" -Enabled $true

# Disable user
Set-ADUser -Identity "jdoe" -Enabled $false
```

#### Get-ADGroup
```powershell
# Get all groups
Get-ADGroup -Filter *

# Get specific group
Get-ADGroup -Identity "IT_Admins"

# Get group members
Get-ADGroupMember -Identity "IT_Admins"
```

#### Add-ADGroupMember / Remove-ADGroupMember
```powershell
# Add user to group
Add-ADGroupMember -Identity "IT_Admins" -Members "jdoe"

# Remove user from group
Remove-ADGroupMember -Identity "IT_Admins" -Members "jdoe" -Confirm:$false
```

### 15. Certificate Management

#### Get-ChildItem Cert:\
```powershell
# List certificates in Personal store
Get-ChildItem -Path Cert:\LocalMachine\My

# List certificates in Trusted Root
Get-ChildItem -Path Cert:\LocalMachine\Root

# Find certificate by thumbprint
Get-ChildItem -Path Cert:\LocalMachine\My | Where-Object {$_.Thumbprint -eq "ABC123..."}

# Find expiring certificates
Get-ChildItem -Path Cert:\LocalMachine\My | Where-Object {$_.NotAfter -lt (Get-Date).AddDays(30)}
```

#### Import-Certificate
```powershell
# Import certificate
Import-Certificate -FilePath "C:\Certs\mycert.cer" -CertStoreLocation Cert:\LocalMachine\My

# Import PFX with password
$password = ConvertTo-SecureString -String "certpass" -AsPlainText -Force
Import-PfxCertificate -FilePath "C:\Certs\mycert.pfx" -CertStoreLocation Cert:\LocalMachine\My -Password $password
```

#### Export-Certificate
```powershell
# Export certificate
$cert = Get-ChildItem -Path Cert:\LocalMachine\My | Where-Object {$_.Thumbprint -eq "ABC123..."}
Export-Certificate -Cert $cert -FilePath "C:\Certs\exported.cer"
```

---

## Pipeline and Object Manipulation

### Pipeline Basics

```powershell
# Pass objects through pipeline
Get-Service | Where-Object {$_.Status -eq 'Running'} | Select-Object Name, DisplayName

# Multiple pipeline stages
Get-Process | Where-Object {$_.CPU -gt 10} | Sort-Object CPU -Descending | Select-Object -First 5
```

### Where-Object (alias: where, ?)
```powershell
# Filter objects
Get-Service | Where-Object {$_.Status -eq 'Running'}

# Multiple conditions (AND)
Get-Process | Where-Object {$_.CPU -gt 10 -and $_.WorkingSet -gt 100MB}

# Multiple conditions (OR)
Get-Service | Where-Object {$_.Status -eq 'Running' -or $_.Status -eq 'Paused'}

# Comparison operators
# -eq (equal), -ne (not equal), -gt (greater than), -lt (less than)
# -ge (greater or equal), -le (less or equal)
# -like (wildcard), -match (regex), -contains (array contains)
```

### Select-Object (alias: select)
```powershell
# Select specific properties
Get-Process | Select-Object Name, CPU, WorkingSet

# Select first N objects
Get-Process | Select-Object -First 10

# Select last N objects
Get-Process | Select-Object -Last 10

# Select unique values
Get-Process | Select-Object ProcessName -Unique

# Calculated properties
Get-Process | Select-Object Name, @{Name="Memory(MB)";Expression={$_.WorkingSet / 1MB}}
```

### Sort-Object (alias: sort)
```powershell
# Sort ascending
Get-Process | Sort-Object CPU

# Sort descending
Get-Process | Sort-Object CPU -Descending

# Sort by multiple properties
Get-Process | Sort-Object CPU, WorkingSet -Descending
```

### Group-Object (alias: group)
```powershell
# Group by property
Get-Service | Group-Object Status

# Group with count
Get-Process | Group-Object ProcessName | Select-Object Name, Count

# Group and sort
Get-Service | Group-Object Status | Sort-Object Count -Descending
```

### Measure-Object (alias: measure)
```powershell
# Count objects
Get-Service | Measure-Object

# Sum property
Get-Process | Measure-Object WorkingSet -Sum

# Average, Min, Max
Get-Process | Measure-Object CPU -Average -Minimum -Maximum
```

### ForEach-Object (alias: foreach, %)
```powershell
# Execute script block for each object
Get-Service | ForEach-Object {Write-Host $_.Name}

# Use $_ to reference current object
Get-Process | ForEach-Object {$_.Kill()}

# Multiple statements
Get-ChildItem | ForEach-Object {
    Write-Host "Processing: $($_.Name)"
    # Do something with $_
}
```

---

## Scripting Constructs

### Variables

```powershell
# Declare variable
$name = "John"
$age = 30
$isActive = $true

# Arrays
$servers = @("server1", "server2", "server3")
$numbers = 1..10

# Hash tables (dictionaries)
$user = @{
    Name = "John"
    Age = 30
    Department = "IT"
}

# Access hash table
$user.Name
$user["Age"]

# Automatic variables
$_ # Current pipeline object
$? # Success status of last command
$LASTEXITCODE # Exit code of last program
$PSScriptRoot # Directory of current script
$PSVersionTable # PowerShell version info
```

### Conditional Statements

```powershell
# If statement
if ($age -gt 18) {
    Write-Host "Adult"
}

# If-Else
if ($status -eq "Running") {
    Write-Host "Service is running"
} else {
    Write-Host "Service is not running"
}

# If-ElseIf-Else
if ($score -ge 90) {
    Write-Host "A"
} elseif ($score -ge 80) {
    Write-Host "B"
} elseif ($score -ge 70) {
    Write-Host "C"
} else {
    Write-Host "F"
}

# Switch statement
switch ($status) {
    "Running" { Write-Host "Service is running" }
    "Stopped" { Write-Host "Service is stopped" }
    "Paused" { Write-Host "Service is paused" }
    default { Write-Host "Unknown status" }
}
```

### Loops

```powershell
# ForEach loop
foreach ($server in $servers) {
    Write-Host "Processing: $server"
}

# For loop
for ($i = 0; $i -lt 10; $i++) {
    Write-Host "Count: $i"
}

# While loop
$i = 0
while ($i -lt 10) {
    Write-Host "Count: $i"
    $i++
}

# Do-While loop
$i = 0
do {
    Write-Host "Count: $i"
    $i++
} while ($i -lt 10)

# Break and Continue
foreach ($number in 1..10) {
    if ($number -eq 5) { continue }  # Skip 5
    if ($number -eq 8) { break }     # Stop at 8
    Write-Host $number
}
```

### Functions

```powershell
# Simple function
function Get-Greeting {
    Write-Host "Hello, World!"
}

# Function with parameters
function Get-Greeting {
    param(
        [string]$Name
    )
    Write-Host "Hello, $Name!"
}

# Function with return value
function Get-Sum {
    param(
        [int]$a,
        [int]$b
    )
    return $a + $b
}

# Advanced function with parameter validation
function Get-ServiceStatus {
    [CmdletBinding()]
    param(
        [Parameter(Mandatory=$true)]
        [ValidateNotNullOrEmpty()]
        [string]$ServiceName,
        
        [Parameter(Mandatory=$false)]
        [string]$ComputerName = "localhost"
    )
    
    Get-Service -Name $ServiceName -ComputerName $ComputerName
}
```

---

## Error Handling

### Try-Catch-Finally

```powershell
# Basic try-catch
try {
    Get-Service -Name "NonExistentService"
} catch {
    Write-Host "Error: $($_.Exception.Message)"
}

# Catch specific exception types
try {
    Get-Service -Name "NonExistentService"
} catch [Microsoft.PowerShell.Commands.ServiceCommandException] {
    Write-Host "Service not found"
} catch {
    Write-Host "Other error: $($_.Exception.Message)"
}

# Try-Catch-Finally
try {
    $file = Get-Content "C:\file.txt"
} catch {
    Write-Host "Error reading file: $($_.Exception.Message)"
} finally {
    Write-Host "Cleanup code here"
}
```

### Error Action Preference

```powershell
# Stop on error
$ErrorActionPreference = "Stop"

# Continue on error (default)
$ErrorActionPreference = "Continue"

# Silently continue
$ErrorActionPreference = "SilentlyContinue"

# Per-command error action
Get-Service -Name "NonExistent" -ErrorAction SilentlyContinue
```

### Error Variables

```powershell
# Last error
$Error[0]

# Error count
$Error.Count

# Clear errors
$Error.Clear()
```

---

## Remote Management

### PowerShell Remoting Basics

```powershell
# Enable remoting (run on remote computer)
Enable-PSRemoting -Force

# Test remoting
Test-WSMan -ComputerName SERVER01
```

### Invoke-Command

```powershell
# Execute command on remote computer
Invoke-Command -ComputerName SERVER01 -ScriptBlock {
    Get-Service
}

# Execute on multiple computers
Invoke-Command -ComputerName SERVER01, SERVER02 -ScriptBlock {
    Get-Service
}

# Execute with credentials
$cred = Get-Credential
Invoke-Command -ComputerName SERVER01 -Credential $cred -ScriptBlock {
    Get-Service
}

# Execute script file
Invoke-Command -ComputerName SERVER01 -FilePath "C:\Scripts\script.ps1"

# Pass arguments
Invoke-Command -ComputerName SERVER01 -ScriptBlock {
    param($ServiceName)
    Get-Service -Name $ServiceName
} -ArgumentList "W3SVC"
```

### Enter-PSSession / Exit-PSSession

```powershell
# Interactive remote session
Enter-PSSession -ComputerName SERVER01

# With credentials
$cred = Get-Credential
Enter-PSSession -ComputerName SERVER01 -Credential $cred

# Exit session
Exit-PSSession
```

### New-PSSession

```powershell
# Create persistent session
$session = New-PSSession -ComputerName SERVER01

# Use session
Invoke-Command -Session $session -ScriptBlock {
    Get-Service
}

# Remove session
Remove-PSSession -Session $session

# Get all sessions
Get-PSSession
```

---

## Common Patterns and Best Practices

### 1. Check if Service Exists Before Operating

```powershell
$serviceName = "W3SVC"
$service = Get-Service -Name $serviceName -ErrorAction SilentlyContinue

if ($service) {
    if ($service.Status -eq 'Running') {
        Write-Host "Service is already running"
    } else {
        Start-Service -Name $serviceName
        Write-Host "Service started"
    }
} else {
    Write-Host "Service not found"
}
```

### 2. Restart Service with Retry Logic

```powershell
function Restart-ServiceWithRetry {
    param(
        [string]$ServiceName,
        [int]$MaxRetries = 3,
        [int]$RetryDelay = 5
    )
    
    $retryCount = 0
    $success = $false
    
    while (-not $success -and $retryCount -lt $MaxRetries) {
        try {
            Restart-Service -Name $ServiceName -ErrorAction Stop
            $success = $true
            Write-Host "Service restarted successfully"
        } catch {
            $retryCount++
            Write-Host "Retry $retryCount of $MaxRetries failed: $($_.Exception.Message)"
            if ($retryCount -lt $MaxRetries) {
                Start-Sleep -Seconds $RetryDelay
            }
        }
    }
    
    return $success
}
```

### 3. Get Disk Space with Threshold Alert

```powershell
$threshold = 10  # 10% free space threshold

Get-Volume | Where-Object {$_.DriveLetter} | ForEach-Object {
    $percentFree = ($_.SizeRemaining / $_.Size) * 100
    
    if ($percentFree -lt $threshold) {
        Write-Warning "Drive $($_.DriveLetter): Low disk space - $([math]::Round($percentFree, 2))% free"
    } else {
        Write-Host "Drive $($_.DriveLetter): $([math]::Round($percentFree, 2))% free - OK"
    }
}
```

### 4. Export Results to CSV

```powershell
# Export services to CSV
Get-Service | Select-Object Name, Status, StartType | Export-Csv -Path "C:\Reports\services.csv" -NoTypeInformation

# Export processes to CSV
Get-Process | Select-Object Name, CPU, @{Name="Memory(MB)";Expression={[math]::Round($_.WorkingSet / 1MB, 2)}} | Export-Csv -Path "C:\Reports\processes.csv" -NoTypeInformation
```

### 5. Create Detailed Log Output

```powershell
function Write-Log {
    param(
        [string]$Message,
        [ValidateSet("INFO", "WARNING", "ERROR")]
        [string]$Level = "INFO"
    )
    
    $timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    $logMessage = "[$timestamp] [$Level] $Message"
    
    # Write to console
    switch ($Level) {
        "INFO" { Write-Host $logMessage }
        "WARNING" { Write-Warning $logMessage }
        "ERROR" { Write-Error $logMessage }
    }
    
    # Write to file
    Add-Content -Path "C:\Logs\script.log" -Value $logMessage
}

# Usage
Write-Log "Script started" -Level INFO
Write-Log "Service not found" -Level WARNING
Write-Log "Critical error occurred" -Level ERROR
```

### 6. Parallel Processing

```powershell
# PowerShell 7+ ForEach-Object -Parallel
$servers = @("SERVER01", "SERVER02", "SERVER03")

$servers | ForEach-Object -Parallel {
    $result = Test-Connection -ComputerName $_ -Count 1 -Quiet
    [PSCustomObject]@{
        Server = $_
        Online = $result
    }
} -ThrottleLimit 10
```

### 7. Measure Script Execution Time

```powershell
$stopwatch = [System.Diagnostics.Stopwatch]::StartNew()

# Your code here
Get-Service | Where-Object {$_.Status -eq 'Running'}

$stopwatch.Stop()
Write-Host "Execution time: $($stopwatch.Elapsed.TotalSeconds) seconds"
```

### 8. Secure Credential Handling

```powershell
# Prompt for credentials
$cred = Get-Credential

# Use credentials
Invoke-Command -ComputerName SERVER01 -Credential $cred -ScriptBlock {
    Get-Service
}

# Store encrypted credentials (user-specific)
$cred | Export-Clixml -Path "C:\Secure\cred.xml"

# Load credentials
$cred = Import-Clixml -Path "C:\Secure\cred.xml"
```

### 9. Progress Bars

```powershell
$servers = @("SERVER01", "SERVER02", "SERVER03", "SERVER04", "SERVER05")
$total = $servers.Count
$current = 0

foreach ($server in $servers) {
    $current++
    $percentComplete = ($current / $total) * 100
    
    Write-Progress -Activity "Processing Servers" -Status "Processing $server" -PercentComplete $percentComplete
    
    # Do work
    Test-Connection -ComputerName $server -Count 1 -Quiet
    Start-Sleep -Seconds 1
}

Write-Progress -Activity "Processing Servers" -Completed
```

### 10. JSON Output for API Integration

```powershell
# Create object
$result = [PSCustomObject]@{
    Status = "Success"
    Message = "Operation completed"
    Data = @{
        ServiceName = "W3SVC"
        Status = "Running"
        StartTime = Get-Date
    }
}

# Convert to JSON
$json = $result | ConvertTo-Json -Depth 10

# Output JSON
Write-Output $json

# Parse JSON
$parsed = $json | ConvertFrom-Json
```

---

## Quick Reference: Most Common Operations

### Service Management
```powershell
Get-Service -Name W3SVC
Start-Service -Name W3SVC
Stop-Service -Name W3SVC
Restart-Service -Name W3SVC
Set-Service -Name W3SVC -StartupType Automatic
```

### Process Management
```powershell
Get-Process -Name chrome
Stop-Process -Name chrome -Force
Get-Process | Sort-Object CPU -Descending | Select-Object -First 10
```

### File Operations
```powershell
Get-ChildItem -Path C:\Logs -Filter *.log
Copy-Item -Path C:\Source\file.txt -Destination C:\Dest\
Remove-Item -Path C:\Temp\file.txt -Force
Test-Path -Path C:\file.txt
```

### Network Operations
```powershell
Test-Connection -ComputerName google.com
Test-NetConnection -ComputerName google.com -Port 443
Get-NetIPAddress -AddressFamily IPv4
```

### System Information
```powershell
Get-CimInstance -ClassName Win32_ComputerSystem
Get-CimInstance -ClassName Win32_OperatingSystem
Get-Volume
Get-Disk
```

### Event Logs
```powershell
Get-WinEvent -LogName System -MaxEvents 100
Get-WinEvent -FilterHashtable @{LogName='System'; Level=2}
```

### Remote Execution
```powershell
Invoke-Command -ComputerName SERVER01 -ScriptBlock { Get-Service }
Enter-PSSession -ComputerName SERVER01
```

---

## PowerShell Best Practices for AI Script Generation

1. **Always use full cmdlet names** (not aliases) for clarity
2. **Include error handling** with Try-Catch blocks
3. **Validate inputs** before executing operations
4. **Use -ErrorAction** to control error behavior
5. **Add comments** to explain complex logic
6. **Use proper parameter types** and validation
7. **Return structured objects** (PSCustomObject) for easy parsing
8. **Include logging** for audit trails
9. **Test for prerequisites** (service exists, file exists, etc.)
10. **Use -WhatIf** and -Confirm for destructive operations

---

## Additional Resources

- **Official Documentation**: https://docs.microsoft.com/powershell
- **PowerShell Gallery**: https://www.powershellgallery.com
- **Get-Help**: Use `Get-Help <cmdlet-name> -Full` for detailed help
- **Get-Command**: Use `Get-Command -Verb Get -Noun *Service*` to discover cmdlets

---

**End of PowerShell Reference Guide**