"""
Windows Tools Registry Extension
Comprehensive Windows operation tools for OpsConductor
"""

from pipeline.schemas.selection_v1 import Tool, ToolCapability, PermissionLevel


def register_windows_tools(registry):
    """
    Register comprehensive Windows operation tools
    
    This function adds all Windows-specific tools to the tool registry,
    covering all major Windows administration and automation scenarios.
    """
    
    # ============================================================================
    # WINDOWS SERVICE MANAGEMENT
    # ============================================================================
    
    windows_service_tool = Tool(
        name="windows-service-manager",
        description="Manage Windows services - start, stop, restart, configure, and query service status",
        capabilities=[
            ToolCapability(
                name="windows_service_management",
                description="Control Windows services (start, stop, restart, pause, resume)",
                required_inputs=["service_name", "action"],
                optional_inputs=["computer_name", "timeout", "force"]
            ),
            ToolCapability(
                name="service_status",
                description="Query Windows service status, startup type, and dependencies",
                required_inputs=["service_name"],
                optional_inputs=["computer_name", "include_dependencies"]
            ),
            ToolCapability(
                name="service_configuration",
                description="Configure service startup type, recovery options, and credentials",
                required_inputs=["service_name"],
                optional_inputs=["startup_type", "recovery_action", "service_account"]
            )
        ],
        required_inputs=["service_name"],
        permissions=PermissionLevel.ADMIN,
        production_safe=True,
        max_execution_time=120,
        dependencies=["winrm_connection"],
        examples=[
            "Restart the IIS service: Get-Service W3SVC | Restart-Service",
            "Check status of SQL Server: Get-Service MSSQLSERVER | Select-Object Status, StartType",
            "Set service to automatic startup: Set-Service -Name Spooler -StartupType Automatic"
        ]
    )
    registry.register_tool(windows_service_tool)
    
    # ============================================================================
    # WINDOWS PROCESS MANAGEMENT
    # ============================================================================
    
    windows_process_tool = Tool(
        name="windows-process-manager",
        description="Manage Windows processes - list, monitor, start, stop, and analyze process information",
        capabilities=[
            ToolCapability(
                name="process_management",
                description="Start, stop, and manage Windows processes",
                required_inputs=["action"],
                optional_inputs=["process_name", "process_id", "force", "arguments"]
            ),
            ToolCapability(
                name="process_monitoring",
                description="Monitor process CPU, memory, threads, and performance metrics",
                required_inputs=[],
                optional_inputs=["process_name", "sort_by", "top_n", "include_children"]
            ),
            ToolCapability(
                name="process_analysis",
                description="Analyze process details, modules, handles, and dependencies",
                required_inputs=["process_identifier"],
                optional_inputs=["include_modules", "include_threads", "include_handles"]
            )
        ],
        required_inputs=[],
        permissions=PermissionLevel.ADMIN,
        production_safe=True,
        max_execution_time=60,
        dependencies=["winrm_connection"],
        examples=[
            "List top 10 processes by CPU: Get-Process | Sort-Object CPU -Descending | Select-Object -First 10",
            "Stop a process by name: Stop-Process -Name notepad -Force",
            "Get detailed process info: Get-Process -Id 1234 | Select-Object *"
        ]
    )
    registry.register_tool(windows_process_tool)
    
    # ============================================================================
    # WINDOWS USER AND GROUP MANAGEMENT
    # ============================================================================
    
    windows_user_tool = Tool(
        name="windows-user-manager",
        description="Manage Windows local users and groups - create, modify, delete, and query user accounts",
        capabilities=[
            ToolCapability(
                name="user_management",
                description="Create, modify, delete, enable, disable Windows user accounts",
                required_inputs=["action"],
                optional_inputs=["username", "password", "full_name", "description", "groups"]
            ),
            ToolCapability(
                name="group_management",
                description="Manage Windows local groups and group memberships",
                required_inputs=["action"],
                optional_inputs=["group_name", "members", "description"]
            ),
            ToolCapability(
                name="user_query",
                description="Query user account information, group memberships, and properties",
                required_inputs=[],
                optional_inputs=["username", "group_name", "include_disabled"]
            )
        ],
        required_inputs=["action"],
        permissions=PermissionLevel.ADMIN,
        production_safe=False,  # User management requires careful handling
        max_execution_time=60,
        dependencies=["winrm_connection"],
        examples=[
            "Create new user: New-LocalUser -Name 'JohnDoe' -Password (ConvertTo-SecureString 'P@ssw0rd' -AsPlainText -Force)",
            "Add user to group: Add-LocalGroupMember -Group 'Administrators' -Member 'JohnDoe'",
            "List all local users: Get-LocalUser | Select-Object Name, Enabled, LastLogon"
        ]
    )
    registry.register_tool(windows_user_tool)
    
    # ============================================================================
    # WINDOWS REGISTRY MANAGEMENT
    # ============================================================================
    
    windows_registry_tool = Tool(
        name="windows-registry-manager",
        description="Manage Windows Registry - read, write, delete registry keys and values",
        capabilities=[
            ToolCapability(
                name="registry_read",
                description="Read Windows Registry keys and values",
                required_inputs=["key_path"],
                optional_inputs=["value_name", "recursive"]
            ),
            ToolCapability(
                name="registry_write",
                description="Create or modify Windows Registry keys and values",
                required_inputs=["key_path", "value_name", "value_data"],
                optional_inputs=["value_type", "force"]
            ),
            ToolCapability(
                name="registry_delete",
                description="Delete Windows Registry keys and values",
                required_inputs=["key_path"],
                optional_inputs=["value_name", "recursive", "force"]
            ),
            ToolCapability(
                name="registry_backup",
                description="Backup and restore Windows Registry keys",
                required_inputs=["key_path", "action"],
                optional_inputs=["backup_path"]
            )
        ],
        required_inputs=["key_path", "action"],
        permissions=PermissionLevel.ADMIN,
        production_safe=False,  # Registry changes are high-risk
        max_execution_time=60,
        dependencies=["winrm_connection"],
        examples=[
            "Read registry value: Get-ItemProperty -Path 'HKLM:\\Software\\Microsoft\\Windows\\CurrentVersion' -Name ProgramFilesDir",
            "Create registry key: New-Item -Path 'HKLM:\\Software\\MyApp' -Force",
            "Set registry value: Set-ItemProperty -Path 'HKLM:\\Software\\MyApp' -Name 'Version' -Value '1.0'"
        ]
    )
    registry.register_tool(windows_registry_tool)
    
    # ============================================================================
    # WINDOWS FILE SYSTEM MANAGEMENT
    # ============================================================================
    
    windows_filesystem_tool = Tool(
        name="windows-filesystem-manager",
        description="Manage Windows file system - files, folders, permissions, and attributes",
        capabilities=[
            ToolCapability(
                name="file_operations",
                description="Create, copy, move, delete files and folders",
                required_inputs=["action", "path"],
                optional_inputs=["destination", "force", "recursive"]
            ),
            ToolCapability(
                name="file_permissions",
                description="Manage NTFS permissions and ACLs",
                required_inputs=["path"],
                optional_inputs=["user", "permissions", "inheritance", "propagate"]
            ),
            ToolCapability(
                name="file_attributes",
                description="Get and set file attributes (hidden, readonly, system, archive)",
                required_inputs=["path"],
                optional_inputs=["attributes", "recursive"]
            ),
            ToolCapability(
                name="file_search",
                description="Search for files and folders with filters",
                required_inputs=["search_path"],
                optional_inputs=["pattern", "file_type", "modified_date", "size"]
            )
        ],
        required_inputs=["action", "path"],
        permissions=PermissionLevel.WRITE,
        production_safe=False,  # File operations can be destructive
        max_execution_time=300,
        dependencies=["winrm_connection"],
        examples=[
            "Copy file: Copy-Item -Path 'C:\\source\\file.txt' -Destination 'C:\\dest\\file.txt'",
            "Set file permissions: $acl = Get-Acl 'C:\\file.txt'; $acl.SetAccessRule($rule); Set-Acl 'C:\\file.txt' $acl",
            "Search for files: Get-ChildItem -Path 'C:\\' -Filter '*.log' -Recurse -ErrorAction SilentlyContinue"
        ]
    )
    registry.register_tool(windows_filesystem_tool)
    
    # ============================================================================
    # WINDOWS DISK MANAGEMENT
    # ============================================================================
    
    windows_disk_tool = Tool(
        name="windows-disk-manager",
        description="Manage Windows disks, volumes, and storage - partitions, formatting, and disk health",
        capabilities=[
            ToolCapability(
                name="disk_monitoring",
                description="Monitor disk space, usage, and performance",
                required_inputs=[],
                optional_inputs=["drive_letter", "include_network", "threshold"]
            ),
            ToolCapability(
                name="disk_management",
                description="Manage disks, partitions, and volumes",
                required_inputs=["action"],
                optional_inputs=["disk_number", "drive_letter", "size", "file_system"]
            ),
            ToolCapability(
                name="disk_health",
                description="Check disk health, SMART status, and errors",
                required_inputs=[],
                optional_inputs=["disk_number", "detailed"]
            )
        ],
        required_inputs=[],
        permissions=PermissionLevel.ADMIN,
        production_safe=True,
        max_execution_time=120,
        dependencies=["winrm_connection"],
        examples=[
            "Check disk space: Get-PSDrive -PSProvider FileSystem | Select-Object Name, Used, Free",
            "Get disk health: Get-PhysicalDisk | Select-Object FriendlyName, HealthStatus, OperationalStatus",
            "List volumes: Get-Volume | Select-Object DriveLetter, FileSystem, Size, SizeRemaining"
        ]
    )
    registry.register_tool(windows_disk_tool)
    
    # ============================================================================
    # WINDOWS NETWORK CONFIGURATION
    # ============================================================================
    
    windows_network_tool = Tool(
        name="windows-network-manager",
        description="Manage Windows network configuration - adapters, IP settings, DNS, firewall, and routing",
        capabilities=[
            ToolCapability(
                name="network_configuration",
                description="Configure network adapters, IP addresses, DNS, and gateways",
                required_inputs=["action"],
                optional_inputs=["adapter_name", "ip_address", "subnet_mask", "gateway", "dns_servers"]
            ),
            ToolCapability(
                name="network_info",
                description="Query network adapter information and configuration",
                required_inputs=[],
                optional_inputs=["adapter_name", "include_statistics"]
            ),
            ToolCapability(
                name="network_testing",
                description="Test network connectivity, DNS resolution, and routing",
                required_inputs=["target"],
                optional_inputs=["test_type", "count", "timeout"]
            )
        ],
        required_inputs=["action"],
        permissions=PermissionLevel.ADMIN,
        production_safe=False,  # Network changes can cause connectivity loss
        max_execution_time=60,
        dependencies=["winrm_connection"],
        examples=[
            "Get network adapters: Get-NetAdapter | Select-Object Name, Status, LinkSpeed",
            "Set static IP: New-NetIPAddress -InterfaceAlias 'Ethernet' -IPAddress '192.168.1.10' -PrefixLength 24",
            "Test connectivity: Test-NetConnection -ComputerName google.com -Port 443"
        ]
    )
    registry.register_tool(windows_network_tool)
    
    # ============================================================================
    # WINDOWS FIREWALL MANAGEMENT
    # ============================================================================
    
    windows_firewall_tool = Tool(
        name="windows-firewall-manager",
        description="Manage Windows Firewall - rules, profiles, and security settings",
        capabilities=[
            ToolCapability(
                name="firewall_rules",
                description="Create, modify, delete, enable, disable firewall rules",
                required_inputs=["action"],
                optional_inputs=["rule_name", "direction", "protocol", "port", "program", "action_type"]
            ),
            ToolCapability(
                name="firewall_profiles",
                description="Manage firewall profiles (Domain, Private, Public)",
                required_inputs=["action"],
                optional_inputs=["profile", "state"]
            ),
            ToolCapability(
                name="firewall_query",
                description="Query firewall status, rules, and configuration",
                required_inputs=[],
                optional_inputs=["rule_name", "profile", "enabled_only"]
            )
        ],
        required_inputs=["action"],
        permissions=PermissionLevel.ADMIN,
        production_safe=False,  # Firewall changes affect security
        max_execution_time=60,
        dependencies=["winrm_connection"],
        examples=[
            "List firewall rules: Get-NetFirewallRule | Select-Object Name, Enabled, Direction, Action",
            "Create firewall rule: New-NetFirewallRule -DisplayName 'Allow Port 8080' -Direction Inbound -LocalPort 8080 -Protocol TCP -Action Allow",
            "Get firewall profile status: Get-NetFirewallProfile | Select-Object Name, Enabled"
        ]
    )
    registry.register_tool(windows_firewall_tool)
    
    # ============================================================================
    # WINDOWS EVENT LOG MANAGEMENT
    # ============================================================================
    
    windows_eventlog_tool = Tool(
        name="windows-eventlog-manager",
        description="Query and manage Windows Event Logs - System, Application, Security, and custom logs",
        capabilities=[
            ToolCapability(
                name="log_access",
                description="Read Windows Event Logs with filtering",
                required_inputs=["log_name"],
                optional_inputs=["level", "source", "event_id", "start_time", "end_time", "max_events"]
            ),
            ToolCapability(
                name="log_analysis",
                description="Analyze event logs for errors, warnings, and patterns",
                required_inputs=["log_name"],
                optional_inputs=["analysis_type", "time_range", "group_by"]
            ),
            ToolCapability(
                name="log_management",
                description="Manage event log settings, size, and retention",
                required_inputs=["log_name", "action"],
                optional_inputs=["max_size", "retention_days", "overflow_action"]
            )
        ],
        required_inputs=["log_name"],
        permissions=PermissionLevel.READ,
        production_safe=True,
        max_execution_time=120,
        dependencies=["winrm_connection"],
        examples=[
            "Get recent errors: Get-EventLog -LogName System -EntryType Error -Newest 10",
            "Query specific event: Get-WinEvent -FilterHashtable @{LogName='Application'; ID=1000}",
            "Export event log: Get-EventLog -LogName System | Export-Csv 'C:\\logs\\system.csv'"
        ]
    )
    registry.register_tool(windows_eventlog_tool)
    
    # ============================================================================
    # WINDOWS PERFORMANCE MONITORING
    # ============================================================================
    
    windows_performance_tool = Tool(
        name="windows-performance-monitor",
        description="Monitor Windows system performance - CPU, memory, disk, network, and performance counters",
        capabilities=[
            ToolCapability(
                name="system_monitoring",
                description="Monitor system-wide performance metrics",
                required_inputs=[],
                optional_inputs=["duration", "interval", "counters"]
            ),
            ToolCapability(
                name="memory_monitoring",
                description="Monitor memory usage, page file, and memory pressure",
                required_inputs=[],
                optional_inputs=["detailed", "include_processes"]
            ),
            ToolCapability(
                name="performance_counters",
                description="Query specific Windows performance counters",
                required_inputs=["counter_path"],
                optional_inputs=["samples", "interval"]
            )
        ],
        required_inputs=[],
        permissions=PermissionLevel.READ,
        production_safe=True,
        max_execution_time=300,
        dependencies=["winrm_connection"],
        examples=[
            "Get CPU usage: Get-Counter '\\Processor(_Total)\\% Processor Time'",
            "Monitor memory: Get-Counter '\\Memory\\Available MBytes'",
            "Get disk performance: Get-Counter '\\PhysicalDisk(_Total)\\Disk Reads/sec'"
        ]
    )
    registry.register_tool(windows_performance_tool)
    
    # ============================================================================
    # WINDOWS UPDATE MANAGEMENT
    # ============================================================================
    
    windows_update_tool = Tool(
        name="windows-update-manager",
        description="Manage Windows Updates - check, install, and configure automatic updates",
        capabilities=[
            ToolCapability(
                name="update_query",
                description="Query available Windows updates and update history",
                required_inputs=[],
                optional_inputs=["category", "include_installed", "include_hidden"]
            ),
            ToolCapability(
                name="update_installation",
                description="Install Windows updates",
                required_inputs=["action"],
                optional_inputs=["update_ids", "category", "auto_reboot"]
            ),
            ToolCapability(
                name="update_configuration",
                description="Configure Windows Update settings",
                required_inputs=["action"],
                optional_inputs=["auto_update", "update_day", "update_time"]
            )
        ],
        required_inputs=["action"],
        permissions=PermissionLevel.ADMIN,
        production_safe=False,  # Updates can cause reboots
        max_execution_time=3600,  # Updates can take a long time
        dependencies=["winrm_connection"],
        examples=[
            "Check for updates: Get-WindowsUpdate",
            "Install updates: Install-WindowsUpdate -AcceptAll -AutoReboot",
            "Get update history: Get-WindowsUpdateLog"
        ]
    )
    registry.register_tool(windows_update_tool)
    
    # ============================================================================
    # WINDOWS SCHEDULED TASKS
    # ============================================================================
    
    windows_task_tool = Tool(
        name="windows-task-scheduler",
        description="Manage Windows Scheduled Tasks - create, modify, delete, and run scheduled tasks",
        capabilities=[
            ToolCapability(
                name="task_management",
                description="Create, modify, delete scheduled tasks",
                required_inputs=["action"],
                optional_inputs=["task_name", "task_path", "command", "arguments", "schedule", "user"]
            ),
            ToolCapability(
                name="task_execution",
                description="Run, stop, enable, disable scheduled tasks",
                required_inputs=["task_name", "action"],
                optional_inputs=["task_path"]
            ),
            ToolCapability(
                name="task_query",
                description="Query scheduled task information and history",
                required_inputs=[],
                optional_inputs=["task_name", "task_path", "state"]
            )
        ],
        required_inputs=["action"],
        permissions=PermissionLevel.ADMIN,
        production_safe=True,
        max_execution_time=60,
        dependencies=["winrm_connection"],
        examples=[
            "List scheduled tasks: Get-ScheduledTask | Select-Object TaskName, State, LastRunTime",
            "Run a task: Start-ScheduledTask -TaskName 'MyTask'",
            "Create a task: Register-ScheduledTask -TaskName 'Backup' -Action (New-ScheduledTaskAction -Execute 'backup.bat') -Trigger (New-ScheduledTaskTrigger -Daily -At 2am)"
        ]
    )
    registry.register_tool(windows_task_tool)
    
    # ============================================================================
    # WINDOWS IIS MANAGEMENT
    # ============================================================================
    
    windows_iis_tool = Tool(
        name="windows-iis-manager",
        description="Manage IIS (Internet Information Services) - websites, app pools, bindings, and configuration",
        capabilities=[
            ToolCapability(
                name="iis_website_management",
                description="Manage IIS websites - create, start, stop, delete",
                required_inputs=["action"],
                optional_inputs=["site_name", "physical_path", "bindings", "app_pool"]
            ),
            ToolCapability(
                name="iis_apppool_management",
                description="Manage IIS application pools",
                required_inputs=["action"],
                optional_inputs=["apppool_name", "runtime_version", "pipeline_mode", "identity"]
            ),
            ToolCapability(
                name="iis_configuration",
                description="Configure IIS settings, bindings, and SSL certificates",
                required_inputs=["action"],
                optional_inputs=["site_name", "setting", "value"]
            )
        ],
        required_inputs=["action"],
        permissions=PermissionLevel.ADMIN,
        production_safe=True,
        max_execution_time=120,
        dependencies=["winrm_connection", "iis_installed"],
        examples=[
            "List IIS sites: Get-IISSite | Select-Object Name, State, Bindings",
            "Start website: Start-IISSite -Name 'Default Web Site'",
            "List app pools: Get-IISAppPool | Select-Object Name, State, ManagedRuntimeVersion"
        ]
    )
    registry.register_tool(windows_iis_tool)
    
    # ============================================================================
    # WINDOWS SQL SERVER MANAGEMENT
    # ============================================================================
    
    windows_sql_tool = Tool(
        name="windows-sql-manager",
        description="Manage SQL Server - databases, backups, queries, and server configuration",
        capabilities=[
            ToolCapability(
                name="sql_query",
                description="Execute SQL queries and stored procedures",
                required_inputs=["query"],
                optional_inputs=["database", "timeout", "parameters"]
            ),
            ToolCapability(
                name="sql_backup",
                description="Backup and restore SQL Server databases",
                required_inputs=["action", "database"],
                optional_inputs=["backup_path", "backup_type", "compression"]
            ),
            ToolCapability(
                name="sql_management",
                description="Manage SQL Server databases and configuration",
                required_inputs=["action"],
                optional_inputs=["database", "setting", "value"]
            )
        ],
        required_inputs=["action"],
        permissions=PermissionLevel.ADMIN,
        production_safe=False,  # Database operations are high-risk
        max_execution_time=3600,
        dependencies=["winrm_connection", "sql_server_installed"],
        examples=[
            "Query database: Invoke-Sqlcmd -Query 'SELECT * FROM Users' -Database 'MyDB'",
            "Backup database: Backup-SqlDatabase -ServerInstance 'localhost' -Database 'MyDB' -BackupFile 'C:\\backup\\MyDB.bak'",
            "List databases: Get-SqlDatabase -ServerInstance 'localhost' | Select-Object Name, Size, Status"
        ]
    )
    registry.register_tool(windows_sql_tool)
    
    # ============================================================================
    # WINDOWS ACTIVE DIRECTORY MANAGEMENT
    # ============================================================================
    
    windows_ad_tool = Tool(
        name="windows-ad-manager",
        description="Manage Active Directory - users, groups, OUs, and domain objects",
        capabilities=[
            ToolCapability(
                name="ad_user_management",
                description="Manage Active Directory user accounts",
                required_inputs=["action"],
                optional_inputs=["username", "ou", "properties"]
            ),
            ToolCapability(
                name="ad_group_management",
                description="Manage Active Directory groups and memberships",
                required_inputs=["action"],
                optional_inputs=["group_name", "members", "scope", "type"]
            ),
            ToolCapability(
                name="ad_query",
                description="Query Active Directory objects and properties",
                required_inputs=["object_type"],
                optional_inputs=["filter", "properties", "search_base"]
            )
        ],
        required_inputs=["action"],
        permissions=PermissionLevel.ADMIN,
        production_safe=False,  # AD changes affect entire domain
        max_execution_time=120,
        dependencies=["winrm_connection", "domain_controller"],
        examples=[
            "Get AD user: Get-ADUser -Identity 'jdoe' -Properties *",
            "Create AD user: New-ADUser -Name 'John Doe' -SamAccountName 'jdoe' -UserPrincipalName 'jdoe@domain.com'",
            "Add user to group: Add-ADGroupMember -Identity 'Domain Admins' -Members 'jdoe'"
        ]
    )
    registry.register_tool(windows_ad_tool)
    
    # ============================================================================
    # WINDOWS CERTIFICATE MANAGEMENT
    # ============================================================================
    
    windows_certificate_tool = Tool(
        name="windows-certificate-manager",
        description="Manage Windows certificates - import, export, install, and query certificates",
        capabilities=[
            ToolCapability(
                name="certificate_query",
                description="Query installed certificates and certificate stores",
                required_inputs=[],
                optional_inputs=["store_location", "store_name", "thumbprint", "subject"]
            ),
            ToolCapability(
                name="certificate_management",
                description="Import, export, install, remove certificates",
                required_inputs=["action"],
                optional_inputs=["certificate_path", "store_location", "store_name", "password"]
            ),
            ToolCapability(
                name="certificate_validation",
                description="Validate certificate expiration and trust chain",
                required_inputs=["thumbprint"],
                optional_inputs=["check_revocation"]
            )
        ],
        required_inputs=["action"],
        permissions=PermissionLevel.ADMIN,
        production_safe=True,
        max_execution_time=60,
        dependencies=["winrm_connection"],
        examples=[
            "List certificates: Get-ChildItem -Path Cert:\\LocalMachine\\My | Select-Object Subject, Thumbprint, NotAfter",
            "Import certificate: Import-Certificate -FilePath 'C:\\cert.cer' -CertStoreLocation 'Cert:\\LocalMachine\\My'",
            "Check expiration: Get-ChildItem Cert:\\LocalMachine\\My | Where-Object {$_.NotAfter -lt (Get-Date).AddDays(30)}"
        ]
    )
    registry.register_tool(windows_certificate_tool)
    
    # ============================================================================
    # WINDOWS POWERSHELL SCRIPT EXECUTION
    # ============================================================================
    
    windows_powershell_tool = Tool(
        name="windows-powershell-executor",
        description="Execute PowerShell scripts and commands on Windows systems",
        capabilities=[
            ToolCapability(
                name="windows_automation",
                description="Execute PowerShell scripts for Windows automation",
                required_inputs=["script"],
                optional_inputs=["arguments", "timeout", "execution_policy"]
            ),
            ToolCapability(
                name="powershell_remoting",
                description="Execute PowerShell commands via WinRM remoting",
                required_inputs=["command"],
                optional_inputs=["computer_name", "credential", "timeout"]
            ),
            ToolCapability(
                name="script_validation",
                description="Validate PowerShell script syntax and security",
                required_inputs=["script"],
                optional_inputs=["check_signature"]
            )
        ],
        required_inputs=["script"],
        permissions=PermissionLevel.ADMIN,
        production_safe=False,  # Script execution is high-risk
        max_execution_time=600,
        dependencies=["winrm_connection"],
        examples=[
            "Execute script: Invoke-Command -ComputerName 'Server01' -ScriptBlock { Get-Service }",
            "Run script file: Invoke-Command -ComputerName 'Server01' -FilePath 'C:\\scripts\\backup.ps1'",
            "Execute with parameters: Invoke-Command -ComputerName 'Server01' -ScriptBlock { param($name) Get-Service $name } -ArgumentList 'W3SVC'"
        ]
    )
    registry.register_tool(windows_powershell_tool)
    
    # ============================================================================
    # WINDOWS SYSTEM INFORMATION
    # ============================================================================
    
    windows_sysinfo_tool = Tool(
        name="windows-system-info",
        description="Get comprehensive Windows system information - hardware, OS, configuration",
        capabilities=[
            ToolCapability(
                name="system_info",
                description="Get Windows system information and configuration",
                required_inputs=[],
                optional_inputs=["category", "detailed"]
            ),
            ToolCapability(
                name="hardware_info",
                description="Get hardware information - CPU, memory, disks, network adapters",
                required_inputs=[],
                optional_inputs=["component"]
            ),
            ToolCapability(
                name="software_inventory",
                description="List installed software and Windows features",
                required_inputs=[],
                optional_inputs=["include_updates", "publisher"]
            )
        ],
        required_inputs=[],
        permissions=PermissionLevel.READ,
        production_safe=True,
        max_execution_time=60,
        dependencies=["winrm_connection"],
        examples=[
            "Get system info: Get-ComputerInfo | Select-Object CsName, OsName, OsVersion, OsArchitecture",
            "Get hardware info: Get-WmiObject Win32_ComputerSystem | Select-Object Manufacturer, Model, TotalPhysicalMemory",
            "List installed software: Get-WmiObject Win32_Product | Select-Object Name, Version, Vendor"
        ]
    )
    registry.register_tool(windows_sysinfo_tool)
    
    # ============================================================================
    # WINDOWS REMOTE DESKTOP MANAGEMENT
    # ============================================================================
    
    windows_rdp_tool = Tool(
        name="windows-rdp-manager",
        description="Manage Windows Remote Desktop (RDP) configuration and sessions",
        capabilities=[
            ToolCapability(
                name="rdp_configuration",
                description="Configure Remote Desktop settings",
                required_inputs=["action"],
                optional_inputs=["enabled", "port", "network_level_auth"]
            ),
            ToolCapability(
                name="rdp_sessions",
                description="Query and manage RDP sessions",
                required_inputs=["action"],
                optional_inputs=["session_id", "username"]
            ),
            ToolCapability(
                name="rdp_users",
                description="Manage Remote Desktop users and permissions",
                required_inputs=["action"],
                optional_inputs=["username", "group"]
            )
        ],
        required_inputs=["action"],
        permissions=PermissionLevel.ADMIN,
        production_safe=True,
        max_execution_time=60,
        dependencies=["winrm_connection"],
        examples=[
            "Enable RDP: Set-ItemProperty -Path 'HKLM:\\System\\CurrentControlSet\\Control\\Terminal Server' -Name 'fDenyTSConnections' -Value 0",
            "List RDP sessions: qwinsta",
            "Disconnect session: logoff <session_id>"
        ]
    )
    registry.register_tool(windows_rdp_tool)
    
    # ============================================================================
    # WINDOWS PRINTER MANAGEMENT
    # ============================================================================
    
    windows_printer_tool = Tool(
        name="windows-printer-manager",
        description="Manage Windows printers - add, remove, configure, and query printer status",
        capabilities=[
            ToolCapability(
                name="printer_management",
                description="Add, remove, configure printers",
                required_inputs=["action"],
                optional_inputs=["printer_name", "port", "driver", "shared"]
            ),
            ToolCapability(
                name="printer_query",
                description="Query printer status and configuration",
                required_inputs=[],
                optional_inputs=["printer_name", "include_jobs"]
            ),
            ToolCapability(
                name="print_job_management",
                description="Manage print jobs - list, pause, resume, cancel",
                required_inputs=["action"],
                optional_inputs=["printer_name", "job_id"]
            )
        ],
        required_inputs=["action"],
        permissions=PermissionLevel.ADMIN,
        production_safe=True,
        max_execution_time=60,
        dependencies=["winrm_connection"],
        examples=[
            "List printers: Get-Printer | Select-Object Name, DriverName, PortName, Shared",
            "Add printer: Add-Printer -Name 'Office Printer' -DriverName 'HP LaserJet' -PortName 'IP_192.168.1.100'",
            "Get print jobs: Get-PrintJob -PrinterName 'Office Printer'"
        ]
    )
    registry.register_tool(windows_printer_tool)
    
    # ============================================================================
    # WINDOWS IMPACKET EXECUTOR - INTERACTIVE GUI APPLICATION EXECUTION
    # ============================================================================
    
    windows_impacket_executor_tool = Tool(
        name="windows-impacket-executor",
        description="Execute commands and GUI applications on remote Windows systems using Impacket WMI with support for non-blocking execution",
        capabilities=[
            ToolCapability(
                name="impacket_execute",
                description="Execute commands remotely via WMI, supporting GUI applications and non-blocking execution",
                required_inputs=["target_host", "command"],
                optional_inputs=["username", "password", "domain", "interactive", "session_id", "wait"]
            ),
            ToolCapability(
                name="impacket_gui_launch",
                description="Launch GUI applications on remote desktop without blocking (appears on remote screen)",
                required_inputs=["target_host", "application"],
                optional_inputs=["username", "password", "domain", "session_id", "arguments"]
            ),
            ToolCapability(
                name="impacket_background",
                description="Execute commands in background without waiting for completion",
                required_inputs=["target_host", "command"],
                optional_inputs=["username", "password", "domain", "interactive"]
            )
        ],
        required_inputs=["target_host", "command"],
        permissions=PermissionLevel.ADMIN,
        production_safe=False,  # Remote execution with admin privileges is high-risk
        max_execution_time=300,
        dependencies=["impacket"],
        examples=[
            "Launch notepad (non-blocking): target=192.168.1.100, command=notepad.exe, wait=false",
            "Run command and get output: target=192.168.1.100, command='ipconfig /all', wait=true",
            "Launch GUI app: target=192.168.1.100, command=calc.exe, wait=false",
            "Execute with domain account: target=192.168.1.100, command=cmd.exe, domain=CORP, username=admin"
        ],
        notes=[
            "Uses Impacket library for WMI-based remote execution (works from Linux to Windows)",
            "Requires: pip install impacket (already included in automation-service)",
            "Requires administrative credentials on target Windows system",
            "Requires SMB access (port 445) and DCOM/WMI access (port 135 + dynamic RPC ports)",
            "For GUI applications, set wait=false to launch without blocking",
            "GUI applications will appear on the remote computer's screen if a user is logged in",
            "For domain accounts, specify domain parameter (use empty string for local accounts)",
            "Non-blocking mode (wait=false) is ideal for GUI apps like notepad, calc, explorer, etc.",
            "Blocking mode (wait=true) captures command output but may timeout for long-running processes"
        ]
    )
    registry.register_tool(windows_impacket_executor_tool)


def get_windows_tools_summary():
    """
    Get summary of all Windows tools
    
    Returns:
        dict: Summary of Windows tools by category
    """
    return {
        "total_tools": 21,
        "categories": {
            "Service Management": ["windows-service-manager"],
            "Process Management": ["windows-process-manager"],
            "User & Group Management": ["windows-user-manager", "windows-ad-manager"],
            "Registry Management": ["windows-registry-manager"],
            "File System": ["windows-filesystem-manager"],
            "Disk Management": ["windows-disk-manager"],
            "Network Configuration": ["windows-network-manager", "windows-firewall-manager"],
            "Event Logs": ["windows-eventlog-manager"],
            "Performance Monitoring": ["windows-performance-monitor"],
            "Updates": ["windows-update-manager"],
            "Scheduled Tasks": ["windows-task-scheduler"],
            "IIS Management": ["windows-iis-manager"],
            "SQL Server": ["windows-sql-manager"],
            "Certificates": ["windows-certificate-manager"],
            "PowerShell": ["windows-powershell-executor"],
            "System Information": ["windows-system-info"],
            "Remote Desktop": ["windows-rdp-manager"],
            "Printer Management": ["windows-printer-manager"],
            "Impacket WMI Remote Execution": ["windows-impacket-executor"]
        },
        "capabilities": [
            "windows_automation",
            "windows_service_management",
            "process_management",
            "user_management",
            "registry_management",
            "file_operations",
            "disk_management",
            "network_configuration",
            "firewall_management",
            "log_access",
            "performance_monitoring",
            "update_management",
            "task_scheduling",
            "iis_management",
            "sql_management",
            "ad_management",
            "certificate_management",
            "rdp_management",
            "printer_management",
            "impacket_wmi_execution",
            "gui_application_launch"
        ]
    }