# Quick Start: E2E Testing with MCP Browser Server

## What This Does

Enables you to test your OpsConductor frontend using AI-powered browser automation directly from VS Code.

## Installation (5 minutes)

### 1. Install Node.js

```bash
# Install Node.js 20 LTS
curl -fsSL https://deb.nodesource.com/setup_20.x | sudo -E bash -
sudo apt-get install -y nodejs

# Verify
node --version  # Should show v20.x.x
npm --version   # Should show 10.x.x
```

### 2. Setup MCP Browser Server

```bash
cd /home/opsconductor/opsconductor-ng/mcp-browser-server
./setup.sh
```

### 3. Restart VS Code

Close and reopen VS Code to load the MCP configuration.

## Usage

### Test 1: Simple Navigation

Ask Zencoder:
```
Navigate to http://localhost:3100 using the browser and take a screenshot
```

### Test 2: Login Flow

Ask Zencoder:
```
Test the login:
1. Navigate to http://localhost:3100
2. Fill username "admin" and password "your_password"
3. Click login
4. Verify dashboard loads
5. Take screenshot
```

### Test 3: Assets Page

Ask Zencoder:
```
Test the assets page:
1. Go to http://localhost:3100/assets
2. Wait for the grid to load
3. Count the assets
4. Take a screenshot
```

### Test 4: AI Chat

Ask Zencoder:
```
Test AI chat:
1. Go to http://localhost:3100/ai-chat
2. Send message "Hello"
3. Wait for response
4. Get the response text
5. Screenshot
```

## Available Commands

- `browser_navigate` - Go to URL
- `browser_click` - Click element
- `browser_fill` - Fill input
- `browser_get_text` - Get text
- `browser_screenshot` - Take screenshot
- `browser_wait_for_selector` - Wait for element
- `browser_evaluate` - Run JavaScript
- `browser_close` - Close browser

## Screenshots Location

```
/home/opsconductor/opsconductor-ng/tests/e2e/screenshots/
```

## Troubleshooting

### Node.js not found
```bash
source ~/.bashrc
node --version
```

### Browser doesn't launch
```bash
cd mcp-browser-server
npm run install-browsers
```

### VS Code can't find MCP server
1. Check `.vscode/settings.json` has MCP config
2. Verify build: `ls mcp-browser-server/dist/index.js`
3. Restart VS Code completely

### Frontend not running
```bash
docker-compose up -d frontend
curl http://localhost:3100
```

## Full Documentation

- [Complete Setup Guide](./E2E_TESTING_SETUP.md)
- [Installation Details](./mcp-browser-server/INSTALL.md)
- [Test Examples](./tests/e2e/README.md)
- [MCP Server Docs](./mcp-browser-server/README.md)

## Example Session

```
You: "Test the login flow"

Zencoder: I'll test the login flow for you.

[Uses browser_navigate to go to http://localhost:3100]
[Uses browser_fill to enter credentials]
[Uses browser_click to submit]
[Uses browser_wait_for_selector to verify dashboard]
[Uses browser_screenshot to capture result]

Zencoder: Login test completed successfully! 
Screenshot saved to tests/e2e/screenshots/login-success.png
```

---

**That's it! You're ready to do AI-powered E2E testing! 🎉**