# MCP Browser Server - Windows Setup Guide

This guide will help you set up the MCP Browser Server on your **Windows machine** to control a local browser for testing your OpsConductor frontend.

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    Your Windows Machine                      │
│                                                              │
│  ┌──────────────┐      ┌─────────────────┐                 │
│  │   VS Code    │◄────►│  MCP Browser    │                 │
│  │  (Zencoder)  │ MCP  │     Server      │                 │
│  └──────────────┘      └────────┬────────┘                 │
│                                  │                           │
│                         ┌────────▼────────┐                 │
│                         │   Chromium      │                 │
│                         │   Browser       │                 │
│                         └────────┬────────┘                 │
│                                  │                           │
│                                  │ HTTP                      │
└──────────────────────────────────┼───────────────────────────┘
                                   │
                                   ▼
                    http://your-linux-server:3100
                         (OpsConductor Frontend)
```

## Prerequisites

- **Windows 10/11**
- **VS Code** installed on Windows
- **Git for Windows** (to clone the repo)
- **Node.js 18+** (we'll install this)

## Step 1: Install Node.js on Windows

### Option A: Using Official Installer (Recommended)

1. Download Node.js LTS from: https://nodejs.org/
2. Run the installer (e.g., `node-v20.x.x-x64.msi`)
3. Follow the installation wizard (accept defaults)
4. Verify installation:
   ```powershell
   node --version
   npm --version
   ```

### Option B: Using Chocolatey

If you have Chocolatey installed:
```powershell
choco install nodejs-lts
```

### Option C: Using Winget

```powershell
winget install OpenJS.NodeJS.LTS
```

## Step 2: Copy MCP Browser Server to Windows

You need to get the `mcp-browser-server` folder onto your Windows machine.

### Option A: Clone the Repository

If your repository is accessible from Windows:
```powershell
git clone <your-repo-url>
cd opsconductor-ng\mcp-browser-server
```

### Option B: Copy via Network Share/SCP

If you have network access to your Linux server:
```powershell
# Using SCP (if you have Git Bash or WSL)
scp -r user@linux-server:/home/opsconductor/opsconductor-ng/mcp-browser-server C:\Projects\
```

### Option C: Manual Copy

1. On Linux, create a zip:
   ```bash
   cd /home/opsconductor/opsconductor-ng
   zip -r mcp-browser-server.zip mcp-browser-server/
   ```

2. Transfer the zip to Windows and extract it

## Step 3: Install Dependencies

Open **PowerShell** or **Command Prompt** in the `mcp-browser-server` directory:

```powershell
cd C:\path\to\mcp-browser-server

# Install dependencies
npm install

# Install Playwright browsers (downloads Chromium)
npx playwright install chromium

# Build TypeScript
npm run build
```

## Step 4: Test the Server

Run a quick test to ensure everything works:

```powershell
npm start
```

You should see:
```
MCP Browser Server running on stdio
Browser automation tools ready
```

Press `Ctrl+C` to stop it.

## Step 5: Configure VS Code on Windows

1. Open VS Code on Windows
2. Open your project folder (or any folder)
3. Create or edit `.vscode/settings.json`:

```json
{
  "mcp.servers": {
    "browser": {
      "command": "node",
      "args": [
        "C:\\path\\to\\mcp-browser-server\\dist\\index.js"
      ],
      "env": {}
    }
  }
}
```

**Important**: Replace `C:\\path\\to\\mcp-browser-server` with the actual path on your Windows machine. Use double backslashes (`\\`) in JSON.

### Example:
```json
{
  "mcp.servers": {
    "browser": {
      "command": "node",
      "args": [
        "C:\\Users\\YourName\\Projects\\mcp-browser-server\\dist\\index.js"
      ],
      "env": {}
    }
  }
}
```

## Step 6: Restart VS Code

1. Close VS Code completely
2. Reopen VS Code
3. The MCP server should start automatically

## Step 7: Test Browser Automation

In VS Code, ask Zencoder (or your MCP client):

```
Navigate to http://your-linux-server:3100 and take a screenshot
```

Replace `your-linux-server` with:
- The IP address of your Linux server (e.g., `192.168.1.100`)
- Or the hostname (e.g., `dev-server.local`)
- Or `localhost` if you're using port forwarding

## Troubleshooting

### Issue: "node is not recognized"

**Solution**: Node.js is not in your PATH. Restart your terminal/VS Code after installing Node.js.

### Issue: "Cannot find module"

**Solution**: Make sure you ran `npm install` and `npm run build` in the mcp-browser-server directory.

### Issue: "Browser not found"

**Solution**: Run `npx playwright install chromium` to download the browser.

### Issue: "Connection refused" when navigating

**Solution**: 
- Verify your Linux server is accessible from Windows
- Check firewall settings on Linux (port 3100 must be open)
- Test in a regular browser first: `http://your-linux-server:3100`

### Issue: MCP server not starting in VS Code

**Solution**:
1. Check VS Code Output panel → MCP Logs
2. Verify the path in settings.json is correct (use `\\` not `\`)
3. Test manually: `node C:\path\to\mcp-browser-server\dist\index.js`

## Network Configuration

### If using IP address:
```
http://192.168.1.100:3100
```

### If using SSH port forwarding:
On Windows, create an SSH tunnel:
```powershell
ssh -L 3100:localhost:3100 user@linux-server
```

Then use:
```
http://localhost:3100
```

### If using WSL2:
If your Linux server is actually WSL2 on the same Windows machine:
```
http://localhost:3100
```

## Available Browser Tools

Once set up, you can use these tools through Zencoder:

- **navigate** - Go to a URL
- **click** - Click an element
- **fill** - Fill a form field
- **get_text** - Get text from an element
- **screenshot** - Take a screenshot
- **wait_for_selector** - Wait for an element
- **evaluate** - Run JavaScript
- **get_url** - Get current URL
- **go_back** - Go back in history
- **reload** - Reload the page
- **close** - Close the browser

## Example Test Commands

Ask Zencoder:

1. **Test login flow**:
   ```
   Navigate to http://192.168.1.100:3100, fill the username field with "admin", 
   fill the password field with "password", click the login button, and take a screenshot
   ```

2. **Check assets page**:
   ```
   Navigate to http://192.168.1.100:3100/assets and wait for the AG Grid to load, 
   then take a screenshot
   ```

3. **Test AI chat**:
   ```
   Navigate to http://192.168.1.100:3100/chat, type "Hello" in the message input, 
   click send, wait 5 seconds, and screenshot the response
   ```

## Screenshots Location

Screenshots are saved to:
```
C:\path\to\mcp-browser-server\screenshots\
```

## Next Steps

- Review the test scenarios in `tests/e2e/` (on Linux server)
- Adapt them for your Windows setup
- Create your own test scenarios
- Integrate with your development workflow

## Advanced: Headless Mode

To run tests without showing the browser window, edit `dist/index.js` and change:
```javascript
headless: false  // Change to true
```

Then rebuild:
```powershell
npm run build
```

## Support

If you encounter issues:
1. Check the VS Code Output panel → MCP Logs
2. Run the server manually to see errors: `node dist\index.js`
3. Verify network connectivity to your Linux server
4. Check firewall settings on both Windows and Linux

---

**You're all set!** The browser will now run on your Windows machine while testing your Linux-hosted frontend. 🎉