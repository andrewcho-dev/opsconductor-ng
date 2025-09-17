#!/usr/bin/env python3
"""
Comprehensive IT Knowledge Training Script for OpsConductor AI
Covers: Windows, PowerShell, Bash, Python, Networking, Linux, and more
"""

import asyncio
import aiohttp
import json
import time
from typing import List, Dict

# Configuration
AI_SERVICE_URL = "http://localhost:3005"

# Comprehensive IT Knowledge Base
IT_KNOWLEDGE = {
    "Windows OS Operations": [
        """
        Windows Command Line (CMD) Essential Commands:
        - dir: List directory contents (dir /s for subdirectories, dir /ah for hidden)
        - cd/chdir: Change directory (cd .. to go up, cd \ for root)
        - copy: Copy files (copy source.txt dest.txt, copy *.txt backup\)
        - xcopy: Extended copy with more options (xcopy /s /e /h for full directory copy)
        - robocopy: Robust file copy (robocopy source dest /MIR for mirroring)
        - del/erase: Delete files (del *.tmp, del /f /q for force quiet)
        - rd/rmdir: Remove directory (rd /s /q for recursive quiet removal)
        - md/mkdir: Make directory
        - ren/rename: Rename files or directories
        - type: Display file contents
        - more/less: Page through text
        - find: Search for text in files (find "error" *.log)
        - findstr: Advanced text search with regex (findstr /r /c:"[0-9]" file.txt)
        - attrib: Change file attributes (+r readonly, +h hidden, +s system)
        - tree: Display directory structure graphically
        """,
        
        """
        Windows System Administration Commands:
        - systeminfo: Display detailed system configuration
        - hostname: Show computer name
        - whoami: Display current user and groups
        - net user: Manage user accounts (net user username password /add)
        - net localgroup: Manage local groups (net localgroup administrators user /add)
        - net share: Manage network shares
        - net use: Map network drives (net use Z: \\\\server\\share)
        - gpupdate: Update group policy (gpupdate /force)
        - gpresult: Display group policy results
        - sfc /scannow: System file checker
        - dism: Deployment Image Service (dism /online /cleanup-image /restorehealth)
        - chkdsk: Check disk for errors (chkdsk C: /f /r)
        - diskpart: Disk partition management
        - format: Format drives
        - convert: Convert FAT to NTFS
        """,
        
        """
        Windows Process and Service Management:
        - tasklist: List running processes (tasklist /v for verbose)
        - taskkill: Kill processes (taskkill /f /im process.exe)
        - sc: Service control (sc query, sc start servicename, sc stop)
        - net start/stop: Start or stop services
        - wmic: Windows Management Instrumentation Command-line
        - wmic process list: List all processes with details
        - wmic service get name,state: List all services
        - wmic cpu get name,numberofcores: Get CPU info
        - shutdown: Shutdown/restart computer (shutdown /r /t 0)
        - logoff: Log off current user
        - runas: Run program as different user
        """,
        
        """
        Windows Registry Operations:
        - reg query: Query registry keys (reg query HKLM\\Software)
        - reg add: Add registry entries
        - reg delete: Delete registry entries
        - reg export: Export registry to file
        - reg import: Import registry from file
        - regedit: GUI registry editor
        Registry Hives:
        - HKEY_LOCAL_MACHINE (HKLM): System-wide settings
        - HKEY_CURRENT_USER (HKCU): Current user settings
        - HKEY_USERS (HKU): All user profiles
        - HKEY_CURRENT_CONFIG (HKCC): Hardware profiles
        - HKEY_CLASSES_ROOT (HKCR): File associations
        """
    ],
    
    "PowerShell Scripting": [
        """
        PowerShell Basics and Cmdlets:
        - Get-Command: Find available commands
        - Get-Help: Get help for cmdlets (Update-Help to download)
        - Get-Member: Explore object properties and methods
        - Get-Process: List processes
        - Get-Service: List services
        - Get-EventLog: Read event logs
        - Get-ChildItem (gci, ls, dir): List items
        - Set-Location (cd): Change directory
        - Get-Location (pwd): Current directory
        - New-Item: Create files/directories
        - Remove-Item (rm, del): Delete items
        - Copy-Item (cp): Copy items
        - Move-Item (mv): Move items
        - Rename-Item: Rename items
        - Get-Content (gc, cat): Read file content
        - Set-Content: Write to file
        - Add-Content: Append to file
        """,
        
        """
        PowerShell Advanced Features:
        Variables and Data Types:
        - $variable = value
        - [string], [int], [array], [hashtable]
        - $array = @(1,2,3)
        - $hash = @{key="value"; key2="value2"}
        
        Operators:
        - Comparison: -eq, -ne, -lt, -gt, -le, -ge
        - Logical: -and, -or, -not, -xor
        - Pattern: -like, -notlike, -match, -notmatch
        - Contains: -contains, -notcontains, -in, -notin
        
        Flow Control:
        - if/elseif/else statements
        - switch statements
        - for, foreach, while, do-while loops
        - break, continue statements
        
        Functions:
        function Get-Something {
            param(
                [Parameter(Mandatory=$true)]
                [string]$Name,
                [int]$Count = 1
            )
            # Function body
        }
        """,
        
        """
        PowerShell Remoting and Administration:
        - Enter-PSSession: Interactive remote session
        - New-PSSession: Create persistent session
        - Invoke-Command: Run commands remotely
        - Enable-PSRemoting: Enable WinRM
        - Test-WSMan: Test WinRM connectivity
        
        Active Directory Cmdlets:
        - Get-ADUser: Query AD users
        - New-ADUser: Create new user
        - Set-ADUser: Modify user properties
        - Get-ADGroup: Query AD groups
        - Add-ADGroupMember: Add users to groups
        - Get-ADComputer: Query computers
        - Get-ADDomain: Domain information
        - Get-ADForest: Forest information
        
        Exchange Management:
        - Get-Mailbox: List mailboxes
        - New-Mailbox: Create mailbox
        - Set-Mailbox: Modify mailbox
        - Get-MailboxStatistics: Mailbox stats
        """,
        
        """
        PowerShell Scripting Best Practices:
        Error Handling:
        try {
            # Risky operation
        }
        catch [System.Exception] {
            Write-Error $_.Exception.Message
        }
        finally {
            # Cleanup
        }
        
        Pipeline Usage:
        Get-Process | Where-Object {$_.CPU -gt 100} | 
            Sort-Object CPU -Descending | 
            Select-Object -First 10
        
        Module Creation:
        - New-ModuleManifest: Create module manifest
        - Export-ModuleMember: Export functions
        - Import-Module: Load modules
        
        Scheduled Tasks:
        - New-ScheduledTask: Create task
        - Register-ScheduledTask: Register task
        - Start-ScheduledTask: Run task
        """
    ],
    
    "Bash Scripting": [
        """
        Bash Fundamentals:
        Shebang and Script Basics:
        #!/bin/bash
        # Comments start with hash
        
        Variables:
        NAME="value"                    # No spaces around =
        readonly CONSTANT="fixed"       # Constant variable
        local var="local scope"        # Local to function
        export VAR="exported"           # Environment variable
        
        Special Variables:
        $0 - Script name
        $1, $2, $3... - Positional parameters
        $# - Number of arguments
        $@ - All arguments as separate words
        $* - All arguments as single word
        $? - Exit status of last command
        $$ - Current process ID
        $! - PID of last background process
        
        Arrays:
        arr=(one two three)
        ${arr[0]}                      # First element
        ${arr[@]}                      # All elements
        ${#arr[@]}                     # Array length
        """,
        
        """
        Bash Control Flow and Functions:
        Conditionals:
        if [[ condition ]]; then
            # commands
        elif [[ condition ]]; then
            # commands
        else
            # commands
        fi
        
        Test Operators:
        -f file     # File exists
        -d dir      # Directory exists
        -z string   # String is empty
        -n string   # String is not empty
        -eq, -ne    # Numeric equal/not equal
        -lt, -gt    # Less than/greater than
        -le, -ge    # Less/greater or equal
        
        Loops:
        for i in {1..10}; do
            echo $i
        done
        
        while [[ condition ]]; do
            # commands
        done
        
        Functions:
        function myfunc() {
            local param=$1
            echo "Parameter: $param"
            return 0
        }
        """,
        
        """
        Bash String Manipulation and Pattern Matching:
        String Operations:
        ${var:offset:length}    # Substring
        ${var#pattern}          # Remove shortest prefix
        ${var##pattern}         # Remove longest prefix
        ${var%pattern}          # Remove shortest suffix
        ${var%%pattern}         # Remove longest suffix
        ${var/old/new}          # Replace first occurrence
        ${var//old/new}         # Replace all occurrences
        ${var^}                 # Uppercase first char
        ${var^^}                # Uppercase all
        ${var,}                 # Lowercase first char
        ${var,,}                # Lowercase all
        ${#var}                 # String length
        
        Regular Expressions:
        [[ $string =~ regex ]]  # Regex matching
        grep -E 'pattern'       # Extended regex
        sed 's/old/new/g'      # Stream editing
        awk '{print $1}'        # Pattern processing
        """,
        
        """
        Bash Advanced Techniques:
        Process Substitution:
        diff <(command1) <(command2)
        
        Command Substitution:
        result=$(command)
        result=`command`        # Backticks (older style)
        
        Here Documents:
        cat <<EOF
        Multiple lines
        of text
        EOF
        
        Redirection:
        command > file          # Stdout to file
        command 2> file         # Stderr to file
        command &> file         # Both to file
        command >> file         # Append
        command < file          # Input from file
        command <<< "string"    # Here string
        
        Pipes and Filters:
        command1 | command2     # Pipe
        command1 && command2    # Run if success
        command1 || command2    # Run if failure
        command1; command2      # Run sequentially
        """
    ],
    
    "Python Scripting": [
        """
        Python Basics for System Administration:
        File Operations:
        import os, shutil, glob
        
        # File handling
        with open('file.txt', 'r') as f:
            content = f.read()
        
        # Directory operations
        os.makedirs('path/to/dir', exist_ok=True)
        os.listdir('.')
        os.walk('/path')        # Recursive directory traversal
        
        # Path manipulation
        from pathlib import Path
        p = Path('/path/to/file.txt')
        p.exists()
        p.is_file()
        p.is_dir()
        p.parent
        p.name
        p.suffix
        
        # File operations
        shutil.copy('src', 'dst')
        shutil.move('src', 'dst')
        shutil.rmtree('directory')
        glob.glob('*.txt')      # Pattern matching
        """,
        
        """
        Python System Administration:
        Process Management:
        import subprocess
        
        # Run commands
        result = subprocess.run(['ls', '-la'], 
                              capture_output=True, 
                              text=True)
        print(result.stdout)
        
        # Popen for more control
        proc = subprocess.Popen(['ping', 'google.com'],
                               stdout=subprocess.PIPE,
                               stderr=subprocess.PIPE)
        stdout, stderr = proc.communicate()
        
        System Information:
        import platform, socket, psutil
        
        platform.system()       # OS name
        platform.release()      # OS release
        socket.gethostname()    # Hostname
        socket.gethostbyname()  # DNS lookup
        
        # Using psutil
        psutil.cpu_percent()
        psutil.virtual_memory()
        psutil.disk_usage('/')
        psutil.net_connections()
        """,
        
        """
        Python Networking and Automation:
        HTTP Requests:
        import requests
        
        response = requests.get('https://api.example.com')
        response.json()
        
        # POST with data
        requests.post('https://api.example.com',
                     json={'key': 'value'},
                     headers={'Authorization': 'Bearer token'})
        
        SSH Automation with Paramiko:
        import paramiko
        
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh.connect('hostname', username='user', password='pass')
        stdin, stdout, stderr = ssh.exec_command('ls -la')
        print(stdout.read().decode())
        ssh.close()
        
        Configuration Management:
        import configparser, json, yaml
        
        # INI files
        config = configparser.ConfigParser()
        config.read('config.ini')
        
        # JSON
        with open('config.json') as f:
            config = json.load(f)
        
        # YAML
        with open('config.yaml') as f:
            config = yaml.safe_load(f)
        """,
        
        """
        Python Advanced Scripting:
        Async Operations:
        import asyncio
        import aiohttp
        
        async def fetch_url(session, url):
            async with session.get(url) as response:
                return await response.text()
        
        async def main():
            async with aiohttp.ClientSession() as session:
                tasks = [fetch_url(session, url) for url in urls]
                results = await asyncio.gather(*tasks)
        
        asyncio.run(main())
        
        Database Operations:
        import sqlite3
        import psycopg2  # PostgreSQL
        
        # SQLite
        conn = sqlite3.connect('database.db')
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM users')
        
        # PostgreSQL with context manager
        with psycopg2.connect(dsn) as conn:
            with conn.cursor() as cur:
                cur.execute('SELECT * FROM users')
                rows = cur.fetchall()
        
        Logging:
        import logging
        
        logging.basicConfig(level=logging.INFO,
                          format='%(asctime)s - %(levelname)s - %(message)s')
        logger = logging.getLogger(__name__)
        logger.info('Information message')
        """
    ],
    
    "Networking Fundamentals": [
        """
        TCP/IP Model and OSI Model:
        
        TCP/IP Model (4 layers):
        1. Network Access Layer (Link) - Physical transmission
        2. Internet Layer - IP addressing and routing
        3. Transport Layer - TCP/UDP, end-to-end delivery
        4. Application Layer - HTTP, FTP, SSH, DNS
        
        OSI Model (7 layers):
        1. Physical - Bits, electrical signals, cables
        2. Data Link - Frames, MAC addresses, switches
        3. Network - Packets, IP addresses, routers
        4. Transport - Segments, TCP/UDP, ports
        5. Session - Session establishment and management
        6. Presentation - Encryption, compression, encoding
        7. Application - User interface, network services
        
        Key Protocols by Layer:
        - Physical: Ethernet, WiFi, Fiber
        - Data Link: Ethernet, PPP, ARP
        - Network: IP, ICMP, OSPF, BGP
        - Transport: TCP, UDP, SCTP
        - Application: HTTP/HTTPS, FTP, SSH, Telnet, DNS, DHCP
        """,
        
        """
        IP Addressing and Subnetting:
        
        IPv4 Address Classes:
        Class A: 1.0.0.0 - 127.255.255.255 (255.0.0.0 or /8)
        Class B: 128.0.0.0 - 191.255.255.255 (255.255.0.0 or /16)
        Class C: 192.0.0.0 - 223.255.255.255 (255.255.255.0 or /24)
        Class D: 224.0.0.0 - 239.255.255.255 (Multicast)
        Class E: 240.0.0.0 - 255.255.255.255 (Reserved)
        
        Private IP Ranges (RFC 1918):
        10.0.0.0 - 10.255.255.255 (10.0.0.0/8)
        172.16.0.0 - 172.31.255.255 (172.16.0.0/12)
        192.168.0.0 - 192.168.255.255 (192.168.0.0/16)
        
        Subnet Calculation:
        Network: 192.168.1.0/24
        - Network Address: 192.168.1.0
        - Broadcast: 192.168.1.255
        - Usable Hosts: 192.168.1.1 - 192.168.1.254 (254 hosts)
        - Subnet Mask: 255.255.255.0
        
        CIDR Notation:
        /24 = 255.255.255.0 (256 addresses, 254 usable)
        /25 = 255.255.255.128 (128 addresses, 126 usable)
        /26 = 255.255.255.192 (64 addresses, 62 usable)
        /27 = 255.255.255.224 (32 addresses, 30 usable)
        /28 = 255.255.255.240 (16 addresses, 14 usable)
        /29 = 255.255.255.248 (8 addresses, 6 usable)
        /30 = 255.255.255.252 (4 addresses, 2 usable - point-to-point)
        """,
        
        """
        TCP vs UDP Protocols:
        
        TCP (Transmission Control Protocol):
        - Connection-oriented (3-way handshake: SYN, SYN-ACK, ACK)
        - Reliable delivery with acknowledgments
        - Flow control and congestion control
        - Ordered delivery
        - Error checking and retransmission
        - Higher overhead, slower
        - Used for: HTTP, HTTPS, FTP, SSH, Email
        
        TCP Header Fields:
        - Source/Destination Port (16 bits each)
        - Sequence Number (32 bits)
        - Acknowledgment Number (32 bits)
        - Flags: SYN, ACK, FIN, RST, PSH, URG
        - Window Size
        - Checksum
        
        UDP (User Datagram Protocol):
        - Connectionless
        - No reliability guarantees
        - No flow control
        - No ordered delivery
        - Minimal error checking
        - Low overhead, faster
        - Used for: DNS, DHCP, SNMP, VoIP, Video streaming
        
        Common Port Numbers:
        - 20/21: FTP
        - 22: SSH
        - 23: Telnet
        - 25: SMTP
        - 53: DNS
        - 67/68: DHCP
        - 80: HTTP
        - 443: HTTPS
        - 110: POP3
        - 143: IMAP
        - 161/162: SNMP
        - 389: LDAP
        - 3306: MySQL
        - 3389: RDP
        - 5432: PostgreSQL
        """,
        
        """
        Network Address Translation (NAT) and Port Forwarding:
        
        NAT Types:
        1. Static NAT: One-to-one mapping
        2. Dynamic NAT: Pool of public IPs
        3. PAT/NAT Overload: Many-to-one using ports
        
        Port Forwarding Configuration:
        - External Port -> Internal IP:Port
        - Example: 8080 -> 192.168.1.100:80
        
        DMZ (Demilitarized Zone):
        - Network segment between internal and external
        - Hosts public-facing services
        - Additional security layer
        """
    ],
    
    "Layer 2 and Layer 3 Networking": [
        """
        Layer 2 (Data Link) Concepts:
        
        Ethernet Frame Structure:
        - Preamble (7 bytes)
        - Start Frame Delimiter (1 byte)
        - Destination MAC (6 bytes)
        - Source MAC (6 bytes)
        - EtherType/Length (2 bytes)
        - Payload (46-1500 bytes)
        - FCS/CRC (4 bytes)
        
        MAC Addresses:
        - 48-bit (6 bytes) hardware address
        - Format: XX:XX:XX:XX:XX:XX
        - First 3 bytes: OUI (Organizationally Unique Identifier)
        - Last 3 bytes: Device specific
        - Broadcast: FF:FF:FF:FF:FF:FF
        
        Switch Operations:
        - MAC address learning
        - Forwarding table/CAM table
        - Store-and-forward vs cut-through
        - Broadcast domains
        - Collision domains
        
        Spanning Tree Protocol (STP):
        - Prevents loops in Layer 2 networks
        - Root bridge election
        - Port states: Blocking, Listening, Learning, Forwarding, Disabled
        - BPDU (Bridge Protocol Data Units)
        - Rapid STP (RSTP) - faster convergence
        """,
        
        """
        VLANs (Virtual LANs):
        
        VLAN Concepts:
        - Logical network segmentation
        - VLAN IDs: 1-4094 (1 default, 1002-1005 reserved)
        - Access ports: Single VLAN
        - Trunk ports: Multiple VLANs
        
        802.1Q Tagging:
        - 4-byte tag inserted in Ethernet frame
        - TPID (Tag Protocol Identifier): 0x8100
        - Priority (3 bits) - CoS
        - CFI (1 bit)
        - VLAN ID (12 bits)
        
        Inter-VLAN Routing:
        - Router-on-a-stick (single physical interface, subinterfaces)
        - Layer 3 switch (SVI - Switch Virtual Interface)
        - External router with multiple interfaces
        
        VLAN Configuration (Cisco):
        Switch(config)# vlan 10
        Switch(config-vlan)# name Sales
        Switch(config)# interface fa0/1
        Switch(config-if)# switchport mode access
        Switch(config-if)# switchport access vlan 10
        Switch(config)# interface fa0/24
        Switch(config-if)# switchport mode trunk
        Switch(config-if)# switchport trunk allowed vlan 10,20,30
        """,
        
        """
        Layer 3 (Network) Routing:
        
        Static Routing:
        - Manually configured routes
        - No overhead, predictable
        - Not scalable for large networks
        - Command: ip route [destination] [mask] [next-hop]
        
        Dynamic Routing Protocols:
        
        Distance Vector (RIP, EIGRP):
        - Routes based on distance (hop count)
        - Periodic updates
        - Bellman-Ford algorithm
        - Simple but slow convergence
        
        Link State (OSPF, IS-IS):
        - Complete network topology knowledge
        - Dijkstra's algorithm
        - Fast convergence
        - More complex, higher resource usage
        
        Path Vector (BGP):
        - Used for internet routing
        - AS (Autonomous System) path
        - Policy-based routing
        - Very scalable
        
        Routing Metrics:
        - Hop count (RIP)
        - Bandwidth (OSPF)
        - Composite (EIGRP): bandwidth, delay, load, reliability
        """,
        
        """
        Advanced Layer 2/3 Features:
        
        Link Aggregation (LAG/EtherChannel):
        - Combine multiple physical links
        - Increased bandwidth and redundancy
        - LACP (Link Aggregation Control Protocol)
        - Static or dynamic configuration
        
        QoS (Quality of Service):
        Layer 2 QoS:
        - 802.1p CoS (Class of Service)
        - 8 priority levels (0-7)
        
        Layer 3 QoS:
        - DSCP (Differentiated Services Code Point)
        - IP Precedence
        - Traffic shaping and policing
        
        First Hop Redundancy:
        - HSRP (Hot Standby Router Protocol) - Cisco
        - VRRP (Virtual Router Redundancy Protocol) - Standard
        - GLBP (Gateway Load Balancing Protocol) - Cisco
        - Virtual IP shared between routers
        - Active/Standby or load balancing
        """
    ],
    
    "VPN and Security": [
        """
        VPN Types and Technologies:
        
        Site-to-Site VPN:
        - Connects entire networks
        - Always-on connection
        - Router/firewall based
        - IPSec or MPLS based
        
        Remote Access VPN:
        - Individual users to network
        - On-demand connection
        - Client software required
        - SSL/TLS or IPSec
        
        VPN Protocols:
        1. IPSec (Internet Protocol Security):
           - AH (Authentication Header)
           - ESP (Encapsulating Security Payload)
           - IKE (Internet Key Exchange)
           - Tunnel mode vs Transport mode
        
        2. SSL/TLS VPN:
           - Browser-based or thin client
           - Works through firewalls
           - Application layer security
        
        3. OpenVPN:
           - Open source
           - SSL/TLS based
           - Cross-platform
           - UDP or TCP
        
        4. WireGuard:
           - Modern, lightweight
           - Kernel-level
           - Simple configuration
           - High performance
        """,
        
        """
        IPSec Deep Dive:
        
        IPSec Components:
        1. Security Associations (SA):
           - Unidirectional
           - Defines encryption/authentication
           - SPI (Security Parameter Index)
        
        2. IKE Phases:
           Phase 1 (Main Mode or Aggressive Mode):
           - Authenticate peers
           - Establish secure channel
           - Negotiate IKE SA
           
           Phase 2 (Quick Mode):
           - Negotiate IPSec SA
           - Establish tunnel
        
        3. Encryption Algorithms:
           - DES (56-bit) - deprecated
           - 3DES (168-bit) - legacy
           - AES-128, AES-192, AES-256 - current standard
           - ChaCha20-Poly1305 - modern
        
        4. Authentication:
           - MD5 - deprecated
           - SHA-1 - legacy
           - SHA-256, SHA-384, SHA-512 - current
           - HMAC variants
        
        5. DH (Diffie-Hellman) Groups:
           - Group 1 (768-bit) - deprecated
           - Group 2 (1024-bit) - weak
           - Group 14 (2048-bit) - minimum
           - Group 19-21 (ECC) - modern
        """,
        
        """
        Network Security Best Practices:
        
        Firewall Configuration:
        - Default deny policy
        - Least privilege principle
        - Regular rule audits
        - Logging and monitoring
        - Stateful inspection
        
        Network Segmentation:
        - DMZ for public services
        - Internal network zones
        - Management network isolation
        - Guest network separation
        - IoT device isolation
        
        Access Control Lists (ACLs):
        Standard ACL (source IP only):
        access-list 10 permit 192.168.1.0 0.0.0.255
        
        Extended ACL (source, dest, port, protocol):
        access-list 100 permit tcp 192.168.1.0 0.0.0.255 
                       any eq 80
        
        Security Protocols:
        - 802.1X: Port-based authentication
        - RADIUS: Central authentication
        - TACACS+: Device administration
        - LDAP: Directory services
        - Kerberos: Ticket-based auth
        """
    ],
    
    "Physical Network Media": [
        """
        Ethernet Cabling Standards:
        
        Copper Cables:
        Cat 5e:
        - 100 MHz bandwidth
        - 1 Gbps up to 100m
        - 4 twisted pairs
        
        Cat 6:
        - 250 MHz bandwidth
        - 1 Gbps up to 100m
        - 10 Gbps up to 55m
        - Better crosstalk protection
        
        Cat 6a:
        - 500 MHz bandwidth
        - 10 Gbps up to 100m
        - Shielded options available
        
        Cat 7:
        - 600 MHz bandwidth
        - 10 Gbps up to 100m
        - Fully shielded (S/FTP)
        
        Cat 8:
        - 2000 MHz bandwidth
        - 25/40 Gbps up to 30m
        - Data center use
        
        Cable Types:
        - UTP (Unshielded Twisted Pair)
        - STP (Shielded Twisted Pair)
        - FTP (Foiled Twisted Pair)
        - S/FTP (Shielded/Foiled)
        
        T568A vs T568B Wiring:
        T568A: G/W-G-O/W-Bl-Bl/W-O-Br/W-Br
        T568B: O/W-O-G/W-Bl-Bl/W-G-Br/W-Br
        Straight-through: Both ends same
        Crossover: One T568A, one T568B
        """,
        
        """
        Fiber Optic Technology:
        
        Fiber Types:
        Single-Mode Fiber (SMF):
        - Core: 8-10 microns
        - Light source: Laser
        - Distance: Up to 100km+
        - Wavelength: 1310nm, 1550nm
        - Higher cost
        - OS1 (indoor), OS2 (outdoor)
        
        Multi-Mode Fiber (MMF):
        - Core: 50 or 62.5 microns
        - Light source: LED or VCSEL
        - Distance: Up to 2km
        - Wavelength: 850nm, 1300nm
        - Lower cost
        - OM1, OM2, OM3, OM4, OM5 categories
        
        Connector Types:
        - LC (Lucent Connector): Small, common
        - SC (Subscriber Connector): Square, push-pull
        - ST (Straight Tip): Bayonet, older
        - FC (Ferrule Connector): Screw-on
        - MTP/MPO: Multi-fiber
        
        Fiber Standards:
        - 1000BASE-SX: 1 Gbps, MMF, 550m
        - 1000BASE-LX: 1 Gbps, SMF, 10km
        - 10GBASE-SR: 10 Gbps, MMF, 300m
        - 10GBASE-LR: 10 Gbps, SMF, 10km
        - 40GBASE-SR4: 40 Gbps, MMF, 150m
        - 100GBASE-SR4: 100 Gbps, MMF, 100m
        """,
        
        """
        DWDM (Dense Wavelength Division Multiplexing):
        
        DWDM Fundamentals:
        - Multiple wavelengths on single fiber
        - ITU-T grid: 50, 100, 200 GHz spacing
        - C-band: 1530-1565nm (most common)
        - L-band: 1565-1625nm (extended)
        - Up to 80+ channels per fiber
        
        DWDM Components:
        1. Transponder/Muxponder:
           - Converts client signal to DWDM wavelength
           - OEO (Optical-Electrical-Optical)
        
        2. Optical Amplifiers:
           - EDFA (Erbium Doped Fiber Amplifier)
           - Raman amplifiers
           - Boost, line, and pre-amplifiers
        
        3. ROADM (Reconfigurable Optical Add-Drop Multiplexer):
           - Add/drop wavelengths
           - Remote configuration
           - Wavelength routing
        
        4. DCM (Dispersion Compensation Module):
           - Compensates chromatic dispersion
           - Required for long distances
        
        CWDM vs DWDM:
        CWDM (Coarse WDM):
        - 20nm channel spacing
        - 18 channels max
        - Lower cost
        - Shorter distance
        
        DWDM:
        - 0.8nm or less spacing
        - 40-80+ channels
        - Higher cost
        - Long-haul capability
        """
    ],
    
    "Wireless and Specialized Networks": [
        """
        Wireless Standards (802.11):
        
        802.11 Evolution:
        802.11a:
        - 5 GHz band
        - 54 Mbps max
        - OFDM modulation
        
        802.11b:
        - 2.4 GHz band
        - 11 Mbps max
        - DSSS modulation
        
        802.11g:
        - 2.4 GHz band
        - 54 Mbps max
        - OFDM modulation
        
        802.11n (Wi-Fi 4):
        - 2.4/5 GHz dual band
        - 600 Mbps max
        - MIMO technology
        - 40 MHz channels
        
        802.11ac (Wi-Fi 5):
        - 5 GHz band
        - 3.46 Gbps max
        - MU-MIMO
        - 80/160 MHz channels
        
        802.11ax (Wi-Fi 6/6E):
        - 2.4/5/6 GHz bands
        - 9.6 Gbps max
        - OFDMA
        - Target Wake Time
        - WPA3 security
        
        Wireless Security:
        - WEP: Broken, never use
        - WPA: TKIP, deprecated
        - WPA2: AES-CCMP, current minimum
        - WPA3: SAE, enhanced security
        - Enterprise: 802.1X/RADIUS
        - Personal: Pre-shared key
        """,
        
        """
        Cradlepoint and Cellular Networks:
        
        Cradlepoint Features:
        - LTE/5G failover
        - SD-WAN capabilities
        - Cloud management (NetCloud)
        - Zero-touch deployment
        - Out-of-band management
        - Vehicle/IoT routers
        
        Cellular Technologies:
        3G: UMTS/HSPA
        - Up to 42 Mbps
        - Higher latency
        - Being phased out
        
        4G LTE:
        - Cat 4: 150 Mbps
        - Cat 6: 300 Mbps
        - Cat 12: 600 Mbps
        - Cat 18: 1.2 Gbps
        
        5G:
        - eMBB: Enhanced mobile broadband
        - URLLC: Ultra-reliable low latency
        - mMTC: Massive machine communication
        - Sub-6 GHz and mmWave
        - Up to 10 Gbps theoretical
        
        APN Configuration:
        - Access Point Name
        - Carrier specific
        - Public vs Private APN
        - Static IP options
        """,
        
        """
        Microwave Communications:
        
        Microwave Link Characteristics:
        - Point-to-point wireless
        - Line of sight required
        - Licensed and unlicensed bands
        - 1-40 GHz frequency range
        - Distance: 1-50+ km typical
        
        Frequency Bands:
        - 2.4 GHz: Unlicensed, high interference
        - 5.8 GHz: Unlicensed, less congestion
        - 6-8 GHz: Licensed, long range
        - 11 GHz: Common carrier band
        - 18-23 GHz: High capacity, short range
        - 60 GHz: Unlicensed, very high capacity
        - 70/80 GHz: E-band, multi-gigabit
        
        Link Planning:
        - Fresnel zone clearance
        - Path loss calculation
        - Rain fade consideration
        - Antenna alignment
        - Polarization (V/H)
        - Adaptive modulation
        
        Applications:
        - Cellular backhaul
        - Enterprise connectivity
        - Disaster recovery
        - Remote site access
        - Video surveillance networks
        """
    ],
    
    "Linux System Administration": [
        """
        Linux File System and Permissions:
        
        File System Hierarchy:
        /         Root directory
        /bin      Essential user binaries
        /boot     Boot loader files
        /dev      Device files
        /etc      System configuration
        /home     User home directories
        /lib      Shared libraries
        /media    Removable media mount points
        /mnt      Temporary mount points
        /opt      Optional software
        /proc     Process information (virtual)
        /root     Root user home
        /sbin     System binaries
        /srv      Service data
        /sys      Sysfs (virtual)
        /tmp      Temporary files
        /usr      User programs
        /var      Variable data (logs, mail, web)
        
        File Permissions:
        rwx rwx rwx (owner, group, other)
        r=4, w=2, x=1
        
        chmod 755 file    # rwxr-xr-x
        chmod u+x file    # Add execute for owner
        chmod g-w file    # Remove write for group
        chmod o=r file    # Set other to read only
        
        Special Permissions:
        SUID (4): Run as owner
        SGID (2): Run as group
        Sticky (1): Only owner can delete
        
        chmod 4755 file   # SUID
        chmod 2755 dir    # SGID
        chmod 1777 /tmp   # Sticky bit
        """,
        
        """
        Linux Process Management:
        
        Process Commands:
        ps aux            # All processes
        ps -ef            # Full format listing
        pstree            # Process tree
        top               # Real-time process viewer
        htop              # Enhanced top
        
        kill -15 PID      # SIGTERM (graceful)
        kill -9 PID       # SIGKILL (force)
        killall process   # Kill by name
        pkill pattern     # Kill by pattern
        
        nice -n 10 cmd    # Start with priority
        renice -5 PID     # Change priority
        
        Background/Foreground:
        command &         # Run in background
        jobs              # List jobs
        fg %1             # Bring to foreground
        bg %1             # Send to background
        Ctrl+Z            # Suspend
        nohup command &   # Immune to hangup
        
        System Services:
        systemctl start service
        systemctl stop service
        systemctl restart service
        systemctl status service
        systemctl enable service   # Start at boot
        systemctl disable service
        systemctl daemon-reload    # Reload configs
        journalctl -u service      # View logs
        journalctl -f              # Follow logs
        """,
        
        """
        Linux Package Management:
        
        Debian/Ubuntu (APT):
        apt update               # Update package list
        apt upgrade              # Upgrade packages
        apt install package      # Install package
        apt remove package       # Remove package
        apt purge package        # Remove with configs
        apt search keyword       # Search packages
        apt show package         # Package details
        apt autoremove          # Remove unused deps
        dpkg -i package.deb     # Install local package
        dpkg -l                 # List installed
        
        RHEL/CentOS/Fedora (YUM/DNF):
        yum update              # Update system
        yum install package     # Install package
        yum remove package      # Remove package
        yum search keyword      # Search packages
        yum info package        # Package info
        yum list installed      # List installed
        yum clean all           # Clean cache
        rpm -ivh package.rpm    # Install local
        rpm -qa                 # Query all installed
        
        Arch (Pacman):
        pacman -Syu             # Update system
        pacman -S package       # Install package
        pacman -R package       # Remove package
        pacman -Ss keyword      # Search packages
        pacman -Q               # List installed
        """,
        
        """
        Linux System Monitoring and Performance:
        
        Resource Monitoring:
        free -h                 # Memory usage
        df -h                   # Disk usage
        du -sh *                # Directory sizes
        iostat                  # I/O statistics
        vmstat                  # Virtual memory stats
        sar                     # System activity
        
        Network Monitoring:
        netstat -tuln          # Listening ports
        ss -tuln               # Modern netstat
        lsof -i                # Open network files
        iftop                  # Network bandwidth
        nethogs                # Per-process bandwidth
        tcpdump                # Packet capture
        
        Log Files:
        /var/log/syslog        # System log (Debian)
        /var/log/messages      # System log (RHEL)
        /var/log/auth.log      # Authentication
        /var/log/kern.log      # Kernel messages
        /var/log/boot.log      # Boot messages
        
        Performance Tuning:
        sysctl -a              # Kernel parameters
        ulimit -a              # User limits
        nice/renice            # Process priority
        ionice                 # I/O priority
        swappiness             # Swap usage tuning
        
        System Information:
        uname -a               # System info
        lsb_release -a         # Distribution info
        hostnamectl            # Hostname info
        timedatectl            # Time/date info
        lscpu                  # CPU info
        lspci                  # PCI devices
        lsusb                  # USB devices
        lsblk                  # Block devices
        """
    ]
}

async def train_knowledge(category: str, documents: List[str]):
    """Train the AI with knowledge from a specific category"""
    timeout = aiohttp.ClientTimeout(total=30)
    async with aiohttp.ClientSession(timeout=timeout) as session:
        for i, doc in enumerate(documents, 1):
            try:
                async with session.post(
                    f"{AI_SERVICE_URL}/ai/learn",
                    json={
                        "content": doc.strip(),
                        "category": category,
                        "source": f"{category}_doc_{i}",
                        "metadata": {
                            "type": "technical_documentation",
                            "category": category,
                            "importance": "high"
                        }
                    }
                ) as response:
                    if response.status == 200:
                        print(f"  ✓ Loaded {category} document {i}/{len(documents)}")
                    else:
                        print(f"  ✗ Failed to load {category} document {i}: {response.status}")
                    
            except Exception as e:
                print(f"  ✗ Error loading {category} document {i}: {str(e)}")
            
            await asyncio.sleep(0.1)  # Small delay between documents

async def main():
    """Main training function"""
    print("=" * 80)
    print("COMPREHENSIVE IT KNOWLEDGE TRAINING FOR OPSCONDUCTOR AI")
    print("=" * 80)
    print("\nThis script will train the AI with extensive knowledge in:")
    print("• Windows OS Operations & Commands")
    print("• PowerShell Scripting") 
    print("• Bash Scripting")
    print("• Python Scripting")
    print("• Networking (TCP/IP, Subnetting, VLANs, VPNs)")
    print("• Layer 2 & Layer 3 Networking")
    print("• Physical Media (Ethernet, Fiber, DWDM)")
    print("• Wireless & Specialized Networks")
    print("• Linux System Administration")
    print("\n" + "=" * 80)
    
    # Check AI service is running
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(f"{AI_SERVICE_URL}/health") as health:
                if health.status != 200:
                    print("❌ AI Service is not responding. Please ensure it's running.")
                    return
    except Exception as e:
        print(f"❌ Cannot connect to AI Service: {e}")
        print("Please ensure the service is running on port 3005")
        return
    
    print("\n✅ AI Service is running. Starting knowledge training...\n")
    
    # Train each category
    total_categories = len(IT_KNOWLEDGE)
    for idx, (category, documents) in enumerate(IT_KNOWLEDGE.items(), 1):
        print(f"\n[{idx}/{total_categories}] Training: {category}")
        print("-" * 50)
        await train_knowledge(category, documents)
        print(f"✓ Completed {category} ({len(documents)} documents)")
    
    print("\n" + "=" * 80)
    print("✅ TRAINING COMPLETE!")
    print("=" * 80)
    
    # Test the trained knowledge
    print("\n🧪 Testing trained knowledge with sample queries...\n")
    
    test_queries = [
        "What is the difference between TCP and UDP?",
        "How do I create a VLAN on a Cisco switch?",
        "Explain DWDM technology",
        "What PowerShell command lists all running services?",
        "How do I check disk usage in Linux?",
        "What is the difference between single-mode and multi-mode fiber?",
        "How does IPSec VPN work?",
        "What is CIDR notation and how do I calculate subnets?"
    ]
    
    async with httpx.AsyncClient(timeout=45.0) as client:
        for query in test_queries:
            print(f"Q: {query}")
            try:
                response = await client.post(
                    f"{AI_SERVICE_URL}/ai/chat",
                    json={"message": query, "user_id": 1}
                )
                
                if response.status_code == 200:
                    result = response.json()
                    answer = result.get('response', 'No response')
                    # Show first 200 chars of response
                    preview = answer[:200] + "..." if len(answer) > 200 else answer
                    print(f"A: {preview}\n")
                else:
                    print(f"Error: {response.status_code}\n")
                    
            except Exception as e:
                print(f"Error: {e}\n")
            
            await asyncio.sleep(1)
    
    print("=" * 80)
    print("The AI has been trained with comprehensive IT knowledge!")
    print("You can now ask questions about:")
    print("• Windows/Linux administration")
    print("• PowerShell/Bash/Python scripting")
    print("• Networking, routing, switching")
    print("• VLANs, VPNs, security")
    print("• Fiber optics, DWDM, wireless")
    print("• And much more!")
    print("=" * 80)

if __name__ == "__main__":
    asyncio.run(main())