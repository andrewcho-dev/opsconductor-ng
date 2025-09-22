# OpsConductor Network Analytics Remote Probe Deployment

This directory contains deployment packages for OpsConductor Network Analytics Remote Probes that can be deployed on remote Windows and Linux systems.

## Overview

The remote probe is a lightweight agent that:
- Captures network packets on remote systems
- Monitors network interfaces and traffic
- Reports back to the central OpsConductor analyzer
- Runs as a system service for reliability

## Supported Platforms

- **Linux**: Ubuntu 18.04+, CentOS 7+, RHEL 7+, Debian 9+
- **Windows**: Windows 10, Windows 11, Windows Server 2016+

## Quick Deployment

### Linux
```bash
# Download and extract the Linux package
wget https://your-server/opsconductor-probe-linux.tar.gz
tar -xzf opsconductor-probe-linux.tar.gz
cd opsconductor-probe-linux

# Run installation script
sudo ./install.sh

# Configure the probe
sudo nano /etc/opsconductor-probe/config.yaml

# Start the service
sudo systemctl start opsconductor-probe
sudo systemctl enable opsconductor-probe
```

### Windows
```powershell
# Download and extract the Windows package
# Extract opsconductor-probe-windows.zip

# Run installation script as Administrator
.\install.ps1

# Configure the probe
notepad "C:\Program Files\OpsConductor Probe\config.yaml"

# Start the service
Start-Service "OpsConductor Network Probe"
Set-Service "OpsConductor Network Probe" -StartupType Automatic
```

## Configuration

The probe requires minimal configuration:

```yaml
# Central analyzer connection
central_analyzer:
  url: "https://your-opsconductor-server.com:3006"
  api_key: "your-api-key"  # Optional for authentication

# Probe identification
probe:
  id: "remote-probe-001"
  name: "Office Network Probe"
  location: "Main Office - Floor 2"

# Network interfaces to monitor (optional - auto-detects if empty)
interfaces:
  - "eth0"
  - "wlan0"

# Logging
logging:
  level: "INFO"
  file: "/var/log/opsconductor-probe.log"  # Linux
  # file: "C:\\ProgramData\\OpsConductor\\probe.log"  # Windows
```

## Security Considerations

- The probe requires elevated privileges for packet capture
- Uses HTTPS for secure communication with central analyzer
- API keys can be used for authentication
- All captured data is encrypted in transit

## Troubleshooting

### Linux
```bash
# Check service status
sudo systemctl status opsconductor-probe

# View logs
sudo journalctl -u opsconductor-probe -f

# Test connectivity
curl -k https://your-server:3006/health
```

### Windows
```powershell
# Check service status
Get-Service "OpsConductor Network Probe"

# View logs
Get-EventLog -LogName Application -Source "OpsConductor Probe"

# Test connectivity
Invoke-WebRequest -Uri "https://your-server:3006/health" -SkipCertificateCheck
```

## Building from Source

See `build/` directory for build scripts and instructions.