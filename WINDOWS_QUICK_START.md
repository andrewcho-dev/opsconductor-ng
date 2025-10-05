# Windows Quick Start - MCP Browser Testing

Get browser automation running on your Windows machine in 5 minutes!

## What This Does

- Runs a browser on your **Windows machine**
- Controls it from VS Code using AI (Zencoder)
- Tests your frontend running on your **Linux server**

## Quick Setup

### 1. Install Node.js (if not already installed)

Download and install from: **https://nodejs.org/** (LTS version)

Verify:
```powershell
node --version
npm --version
```

### 2. Copy `mcp-browser-server` folder to Windows

Choose one method:

**Option A - Git Clone** (if repo is accessible):
```powershell
git clone <your-repo-url>
cd opsconductor-ng\mcp-browser-server
```

**Option B - Download ZIP**:
1. On Linux: `cd /home/opsconductor/opsconductor-ng && zip -r mcp-browser-server.zip mcp-browser-server/`
2. Transfer to Windows and extract

**Option C - Network Copy** (if you have network access):
```powershell
# Using SCP or network share
scp -r user@server:/home/opsconductor/opsconductor-ng/mcp-browser-server C:\Projects\
```

### 3. Run Setup Script

Open PowerShell in the `mcp-browser-server` folder:

```powershell
cd C:\path\to\mcp-browser-server
.\setup.bat
```

This will:
- Install npm packages
- Download Chromium browser
- Build TypeScript
- Show you the VS Code configuration

### 4. Configure VS Code

1. Open VS Code on Windows
2. Open Settings (Ctrl+,) → Search for "settings.json"
3. Click "Edit in settings.json"
4. Add this configuration:

```json
{
  "mcp.servers": {
    "browser": {
      "command": "node",
      "args": [
        "C:\\Users\\YourName\\Projects\\mcp-browser-server\\dist\\index.js"
      ]
    }
  }
}
```

**Replace the path** with your actual path (use `\\` not `\`)!

### 5. Restart VS Code

Close and reopen VS Code completely.

### 6. Test It!

Ask Zencoder in VS Code:

```
Navigate to http://YOUR-SERVER-IP:3100 and take a screenshot
```

Replace `YOUR-SERVER-IP` with your Linux server's IP address (e.g., `192.168.1.100`).

## Finding Your Server IP

On your Linux server, run:
```bash
hostname -I
```

Or check your network settings.

## Example Commands

Once working, try these:

**Test login**:
```
Navigate to http://192.168.1.100:3100, fill username with "admin", 
fill password with "password", click login, and screenshot
```

**Check assets page**:
```
Go to http://192.168.1.100:3100/assets and take a screenshot
```

**Test AI chat**:
```
Navigate to http://192.168.1.100:3100/chat, type "Hello" in the 
message box, click send, wait 5 seconds, and screenshot
```

## Troubleshooting

### "node is not recognized"
- Restart PowerShell/VS Code after installing Node.js
- Or add Node.js to PATH manually

### "Cannot connect to server"
- Check if your Linux server port 3100 is accessible from Windows
- Test in a regular browser first: `http://YOUR-SERVER-IP:3100`
- Check Linux firewall: `sudo ufw allow 3100`

### MCP server not starting
- Check VS Code Output → MCP Logs
- Verify the path in settings.json (use `\\`)
- Test manually: `node C:\path\to\mcp-browser-server\dist\index.js`

## Screenshots

Screenshots are saved to:
```
C:\path\to\mcp-browser-server\screenshots\
```

## Need More Help?

See the detailed guide: `mcp-browser-server/WINDOWS_SETUP.md`

---

**That's it!** You now have AI-powered browser automation running on Windows! 🎉