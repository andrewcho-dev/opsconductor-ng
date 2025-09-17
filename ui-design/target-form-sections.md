# Target Management Form - Collapsible Sections Design

## 🎨 **UI Organization Strategy**

The 200+ fields should be organized into **logical, collapsible sections** that users can expand only when needed. This creates a clean, manageable interface.

## 📋 **Section Layout**

### 🔧 **Always Visible (Core Section)**
```
┌─────────────────────────────────────────────────────────────┐
│ 📋 BASIC INFORMATION                                        │
├─────────────────────────────────────────────────────────────┤
│ • Name*                    • Display Name                   │
│ • Hostname*                • FQDN                          │
│ • IP Address*              • Description                    │
│ • Primary Connection*      • Is Active                      │
└─────────────────────────────────────────────────────────────┘
```

### 🖥️ **Collapsible Section 1: System Information**
```
┌─ 🖥️ SYSTEM INFORMATION ────────────────────────── [▼] ─────┐
│ OS & Platform:                                              │
│ • OS Type                  • OS Family                      │
│ • OS Version               • Architecture                   │
│ • Kernel Version           • OS Edition                     │
│                                                             │
│ Hardware Details:                                           │
│ • Manufacturer             • Model                          │
│ • Serial Number            • Asset Tag                      │
│ • CPU Count                • Memory (GB)                    │
│ • Storage (GB)             • CPU Model                      │
│                                                             │
│ Virtualization:                                             │
│ • Is Virtual               • Hypervisor                     │
│ • VM ID                    • Cluster Name                   │
└─────────────────────────────────────────────────────────────┘
```

### 🌐 **Collapsible Section 2: Network Information**
```
┌─ 🌐 NETWORK INFORMATION ──────────────────────── [▼] ─────┐
│ Network Configuration:                                      │
│ • Secondary IPs            • MAC Addresses                 │
│ • Domain                   • Workgroup                     │
│ • Default Gateway          • Subnet Mask                   │
│ • VLAN ID                  • DNS Servers                   │
│ • NTP Servers                                              │
└─────────────────────────────────────────────────────────────┘
```

### 🏢 **Collapsible Section 3: Organization & Location**
```
┌─ 🏢 ORGANIZATION & LOCATION ─────────────────── [▼] ─────┐
│ Location Details:                                          │
│ • Location                 • Datacenter                   │
│ • Rack Position                                           │
│                                                           │
│ Business Information:                                      │
│ • Business Unit            • Cost Center                  │
│ • Owner Email              • Technical Contact            │
└───────────────────────────────────────────────────────────┘
```

### 🔐 **Collapsible Section 4: SSH Connection**
```
┌─ 🔐 SSH CONNECTION ───────────────────────────── [▼] ─────┐
│ ☐ Enable SSH Connection                                    │
│                                                            │
│ Basic Settings:                                            │
│ • Port (22)                • Username                     │
│ • Password                 • Timeout (30s)                │
│                                                            │
│ Key-Based Authentication:                                  │
│ • Private Key              • Public Key                    │
│ • Passphrase               • Key Type (RSA/Ed25519)       │
│ • Key Bits                                                │
│                                                            │
│ Advanced Options: [▼]                                     │
│ • SSH Version              • Compression                  │
│ • Keep Alive               • Host Key Checking            │
│ • Proxy Jump               • Max Sessions                 │
│ • Tunnel Ports             • Custom Options (JSON)       │
└────────────────────────────────────────────────────────────┘
```

### 🪟 **Collapsible Section 5: WinRM Connection**
```
┌─ 🪟 WINRM CONNECTION ────────────────────────── [▼] ─────┐
│ ☐ Enable WinRM Connection                                 │
│                                                           │
│ Basic Settings:                                           │
│ • Port (5985/5986)         • Use SSL                     │
│ • Username                 • Password                    │
│ • Domain                   • Auth Type (Basic/NTLM)      │
│                                                           │
│ Advanced Options: [▼]                                    │
│ • Transport                • Timeout                     │
│ • Max Envelope Size        • Locale                      │
│ • Codepage                 • Allow Unencrypted           │
│ • Certificate Validation   • CA Trust Path               │
│ • Client Certificate       • Custom Options (JSON)      │
└───────────────────────────────────────────────────────────┘
```

### 📊 **Collapsible Section 6: SNMP Connection**
```
┌─ 📊 SNMP CONNECTION ─────────────────────────── [▼] ─────┐
│ ☐ Enable SNMP Connection                                  │
│                                                           │
│ Basic Settings:                                           │
│ • Port (161)               • Version (v1/v2c/v3)         │
│ • Timeout (10s)            • Retries (3)                 │
│                                                           │
│ v1/v2c Settings:                                         │
│ • Read Community           • Write Community             │
│                                                           │
│ v3 Authentication: [▼]                                   │
│ • Username                 • Context Name                │
│ • Security Level           • Auth Protocol               │
│ • Auth Key                 • Privacy Protocol            │
│ • Privacy Key              • Engine ID                   │
│                                                           │
│ Advanced Options: [▼]                                    │
│ • Bulk Max Repetitions     • Bulk Non-Repeaters         │
│ • Custom Options (JSON)                                  │
└───────────────────────────────────────────────────────────┘
```

### 🌐 **Collapsible Section 7: HTTP/REST API**
```
┌─ 🌐 HTTP/REST API ───────────────────────────── [▼] ─────┐
│ ☐ Enable HTTP/HTTPS Connection                            │
│                                                           │
│ Basic Settings:                                           │
│ • Port (80/443)            • Use SSL                     │
│ • Base URL                 • Timeout (30s)               │
│ • Verify SSL               • Follow Redirects            │
│                                                           │
│ Authentication: [▼]                                       │
│ • Auth Type (None/Basic/Bearer/API Key/OAuth2)           │
│ • Username/Password        • API Key                     │
│ • Bearer Token             • API Key Header              │
│                                                           │
│ OAuth2 Settings: [▼]                                     │
│ • Client ID                • Client Secret               │
│ • Token URL                • Scope                       │
│                                                           │
│ Client Certificates: [▼]                                 │
│ • Client Certificate       • Client Key                  │
│ • Certificate Passphrase                                 │
│                                                           │
│ Advanced Options: [▼]                                    │
│ • Custom Headers (JSON)    • User Agent                 │
│ • Max Redirects            • Custom Options (JSON)      │
└───────────────────────────────────────────────────────────┘
```

### 🖥️ **Collapsible Section 8: Remote Desktop (RDP)**
```
┌─ 🖥️ REMOTE DESKTOP (RDP) ────────────────────── [▼] ─────┐
│ ☐ Enable RDP Connection                                   │
│                                                           │
│ Basic Settings:                                           │
│ • Port (3389)              • Username                    │
│ • Password                 • Domain                      │
│ • Security (Auto/RDP/TLS/NLA)                           │
│                                                           │
│ Display Settings: [▼]                                    │
│ • Width (1024)             • Height (768)               │
│ • Color Depth (32)         • DPI (96)                   │
│                                                           │
│ Advanced Options: [▼]                                    │
│ • Ignore Certificate      • Disable Auth                │
│ • Enable Drive Redirect    • Enable Audio               │
│ • Keyboard Layout          • Timezone                   │
│ • Custom Options (JSON)                                  │
└───────────────────────────────────────────────────────────┘
```

### 🗄️ **Collapsible Section 9: Database Connections**
```
┌─ 🗄️ DATABASE CONNECTIONS ───────────────────── [▼] ─────┐
│ PostgreSQL: [▼]                                          │
│ ☐ Enable PostgreSQL  • Port (5432)  • Database         │
│ • Username            • Password     • SSL Mode         │
│                                                          │
│ MySQL/MariaDB: [▼]                                      │
│ ☐ Enable MySQL       • Port (3306)  • Database         │
│ • Username            • Password     • SSL Mode         │
│                                                          │
│ SQL Server: [▼]                                         │
│ ☐ Enable SQL Server  • Port (1433)  • Database         │
│ • Username            • Password     • Instance         │
│ • Encrypt Connection  • Trust Certificate               │
│                                                          │
│ Oracle: [▼]                                             │
│ ☐ Enable Oracle      • Port (1521)  • Service Name     │
│ • Username            • Password     • SID              │
└─────────────────────────────────────────────────────────┘
```

### ☁️ **Collapsible Section 10: Cloud Provider Credentials**
```
┌─ ☁️ CLOUD PROVIDER CREDENTIALS ─────────────── [▼] ─────┐
│ Amazon Web Services (AWS): [▼]                          │
│ ☐ Enable AWS         • Region (us-east-1)              │
│ • Access Key ID       • Secret Access Key              │
│ • Session Token       • Role ARN                       │
│ • Profile                                               │
│                                                         │
│ Microsoft Azure: [▼]                                   │
│ ☐ Enable Azure       • Tenant ID                       │
│ • Client ID           • Client Secret                  │
│ • Subscription ID     • Resource Group                 │
│                                                         │
│ Google Cloud Platform (GCP): [▼]                       │
│ ☐ Enable GCP         • Project ID                      │
│ • Service Account Key • Region                         │
│ • Zone                                                  │
└─────────────────────────────────────────────────────────┘
```

### 📁 **Collapsible Section 11: File Transfer (FTP/SFTP)**
```
┌─ 📁 FILE TRANSFER (FTP/SFTP) ────────────────── [▼] ─────┐
│ FTP: [▼]                                                 │
│ ☐ Enable FTP          • Port (21)    • Use SSL (FTPS)   │
│ • Username             • Password     • Passive Mode     │
│ • Timeout              • Encoding                        │
│                                                          │
│ SFTP: [▼]                                               │
│ ☐ Enable SFTP         • Port (22)    • Username         │
│ • Password             • Private Key  • Passphrase      │
│ • Timeout              • Compression                     │
└─────────────────────────────────────────────────────────┘
```

### 📞 **Collapsible Section 12: Legacy Protocols**
```
┌─ 📞 LEGACY PROTOCOLS ────────────────────────── [▼] ─────┐
│ Telnet: [▼]                                             │
│ ☐ Enable Telnet       • Port (23)    • Username        │
│ • Password             • Timeout      • Prompt Regex   │
│ • Login Prompt         • Password Prompt               │
└─────────────────────────────────────────────────────────┘
```

### 🛡️ **Collapsible Section 13: Security & Compliance**
```
┌─ 🛡️ SECURITY & COMPLIANCE ──────────────────── [▼] ─────┐
│ Classification:                                          │
│ • Security Classification  • Compliance Frameworks      │
│ • Encryption Required      • Backup Required            │
│                                                          │
│ Access Control:                                          │
│ • Privileged Access Req.   • MFA Required              │
│ • Session Recording Req.   • Access Approval Req.      │
│                                                          │
│ Vulnerability Management:                                │
│ • Vulnerability Scan       • Last Scan Date            │
│ • Vulnerability Score      • Critical Count            │
│ • High Vulnerabilities                                  │
└─────────────────────────────────────────────────────────┘
```

### 📊 **Collapsible Section 14: Monitoring & Discovery**
```
┌─ 📊 MONITORING & DISCOVERY ──────────────────── [▼] ─────┐
│ Discovery Settings:                                      │
│ • Auto Discovery           • Discovery Methods          │
│ • Discovery Schedule       • Last Discovery Scan       │
│                                                          │
│ Health Monitoring:                                       │
│ • Monitoring Enabled       • Monitoring Interval       │
│ • Health Check Enabled     • Health Check URL          │
│ • Expected Status Code     • Health Check Timeout      │
│                                                          │
│ Performance Alerts:                                      │
│ • Collect Metrics          • CPU Alert (90%)           │
│ • Memory Alert (90%)       • Disk Alert (90%)          │
│ • Performance Retention (30 days)                       │
└─────────────────────────────────────────────────────────┘
```

### 🔄 **Collapsible Section 15: Lifecycle & Maintenance**
```
┌─ 🔄 LIFECYCLE & MAINTENANCE ─────────────────── [▼] ─────┐
│ Lifecycle Information:                                   │
│ • Lifecycle Stage          • Provisioning Status        │
│ • Installation Date        • Warranty Expiry           │
│ • End of Life Date         • End of Support Date       │
│                                                          │
│ Maintenance:                                             │
│ • Patch Group              • Maintenance Window         │
│ • Change Freeze            • Next Maintenance           │
│ • Decommission Date                                      │
└─────────────────────────────────────────────────────────┘
```

### ⚙️ **Collapsible Section 16: Advanced Settings**
```
┌─ ⚙️ ADVANCED SETTINGS ───────────────────────── [▼] ─────┐
│ Connection Management:                                   │
│ • Fallback Connections    • Connection Pool Size        │
│ • Retry Attempts          • Retry Delay                 │
│ • Circuit Breaker         • Connection Timeout          │
│                                                          │
│ Custom Data:                                             │
│ • Metadata (JSON)         • Custom Fields (JSON)       │
│ • Integration Data (JSON)                               │
└─────────────────────────────────────────────────────────┘
```

## 🎯 **UI Behavior**

### **Default State:**
- Only **Basic Information** is expanded
- All other sections are **collapsed** by default
- Show **connection count badges** next to collapsed sections

### **Smart Expansion:**
- When user selects a **Primary Connection**, auto-expand that section
- Show **validation indicators** on collapsed sections
- **Badge indicators** show if section has data: `SSH (✓)`, `WinRM (○)`, `SNMP (✓)`

### **Progressive Disclosure:**
- **Beginner Mode**: Show only basic options in each section
- **Advanced Mode**: Show all options with sub-collapsible groups
- **Expert Mode**: Show everything expanded

### **Visual Cues:**
- ✅ **Green badge**: Section has valid configuration
- ⚠️ **Yellow badge**: Section has partial/warning configuration  
- ❌ **Red badge**: Section has errors
- ○ **Gray badge**: Section is empty/disabled

This design makes the form **manageable and intuitive** while keeping all the comprehensive functionality available when needed! 🎨