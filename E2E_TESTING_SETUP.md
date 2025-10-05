# E2E Testing Setup Guide

## Overview

This guide will help you set up browser-based end-to-end testing for OpsConductor using the MCP (Model Context Protocol) Browser Server.

## What You'll Get

- **Browser Automation**: Control a real browser from VS Code
- **AI-Powered Testing**: Use AI to write and execute tests
- **Visual Verification**: Take screenshots and inspect pages
- **Interactive Testing**: Test your frontend in real-time

## Architecture

```
┌─────────────────────────────────────────┐
│         VS Code + Zencoder              │
│                                         │
│  You: "Test the login flow"            │
│  AI: Executes browser automation        │
└──────────────┬──────────────────────────┘
               │ MCP Protocol
               │
┌──────────────▼──────────────────────────┐
│      Browser MCP Server                 │
│      (Node.js + Playwright)             │
│                                         │
│  - browser_navigate                     │
│  - browser_click                        │
│  - browser_fill                         │
│  - browser_screenshot                   │
│  - etc.                                 │
└──────────────┬──────────────────────────┘
               │ Playwright API
               │
┌──────────────▼──────────────────────────┐
│         Chromium Browser                │
│                                         │
│  http://localhost:3100                  │
│  (OpsConductor Frontend)                │
└─────────────────────────────────────────┘
```

## Quick Start

### Step 1: Install MCP Browser Server

```bash
cd /home/opsconductor/opsconductor-ng/mcp-browser-server
chmod +x setup.sh
./setup.sh
```

This will:
- Install Node.js dependencies
- Download Chromium browser
- Build the TypeScript code
- Display configuration instructions

### Step 2: Verify Installation

```bash
cd /home/opsconductor/opsconductor-ng/mcp-browser-server
npm start
```

You should see: `OpsConductor Browser MCP Server running on stdio`

Press Ctrl+C to stop.

### Step 3: Configure VS Code

The setup script already added MCP configuration to `.vscode/settings.json`:

```json
{
  "mcp.servers": {
    "browser": {
      "command": "node",
      "args": ["/home/opsconductor/opsconductor-ng/mcp-browser-server/dist/index.js"],
      "env": {}
    }
  }
}
```

### Step 4: Restart VS Code

Reload VS Code to pick up the new MCP server configuration.

### Step 5: Test the Setup

In VS Code, ask Zencoder:

```
Can you navigate to http://localhost:3100 using the browser?
```

If configured correctly, a browser window should open and navigate to your frontend.

## Available Browser Tools

### Navigation
- `browser_navigate` - Go to a URL
- `browser_go_back` - Navigate back
- `browser_reload` - Reload page
- `browser_get_url` - Get current URL

### Interaction
- `browser_click` - Click an element
- `browser_fill` - Fill an input field
- `browser_wait_for_selector` - Wait for element

### Inspection
- `browser_get_text` - Get element text
- `browser_evaluate` - Run JavaScript
- `browser_screenshot` - Take screenshot

### Control
- `browser_close` - Close browser

## Example Test Flows

### 1. Simple Navigation Test

Ask Zencoder:
```
Navigate to http://localhost:3100 and take a screenshot
```

### 2. Login Flow Test

Ask Zencoder:
```
Test the login flow:
1. Navigate to http://localhost:3100
2. Fill username with "admin"
3. Fill password with "password"
4. Click the login button
5. Verify we're redirected to the dashboard
6. Take a screenshot
```

### 3. Assets Page Test

Ask Zencoder:
```
Test the assets page:
1. Navigate to http://localhost:3100/assets
2. Wait for the AG Grid to load
3. Count how many assets are displayed
4. Take a screenshot
```

### 4. AI Chat Test

Ask Zencoder:
```
Test the AI chat:
1. Navigate to http://localhost:3100/ai-chat
2. Type "Hello" in the chat input
3. Click send
4. Wait for the AI response
5. Get the response text
6. Take a screenshot
```

## Pre-Written Test Scenarios

We've created detailed test scenarios in `/tests/e2e/`:

1. **Login Flow** - `test_frontend_login.md`
2. **Assets Page** - `test_frontend_assets.md`
3. **AI Chat** - `test_frontend_ai_chat.md`

You can ask Zencoder to execute these:
```
Execute the login flow test from tests/e2e/test_frontend_login.md
```

## Screenshots

Screenshots are saved to:
```
/home/opsconductor/opsconductor-ng/tests/e2e/screenshots/
```

You can view them in VS Code or any image viewer.

## Troubleshooting

### MCP Server Not Found

**Problem**: VS Code can't find the MCP server

**Solution**:
1. Verify the server is built: `cd mcp-browser-server && npm run build`
2. Check the path in `.vscode/settings.json` is correct
3. Restart VS Code

### Browser Doesn't Launch

**Problem**: Browser window doesn't open

**Solution**:
1. Install browsers: `cd mcp-browser-server && npm run install-browsers`
2. Check system dependencies: `playwright install-deps chromium`
3. Try headless mode (edit `src/index.ts`, set `headless: true`)

### Selectors Not Found

**Problem**: Elements can't be found on the page

**Solution**:
1. Use browser DevTools to inspect elements
2. Verify the selector is correct
3. Add wait time: `browser_wait_for_selector` before interacting
4. Increase timeout values

### Frontend Not Running

**Problem**: Can't connect to http://localhost:3100

**Solution**:
```bash
cd /home/opsconductor/opsconductor-ng
docker-compose up -d frontend
docker-compose logs -f frontend
```

### AI Pipeline Not Responding

**Problem**: AI chat tests timeout

**Solution**:
```bash
docker-compose up -d ai-pipeline
docker-compose logs -f ai-pipeline
# Verify Ollama is running and model is loaded
```

## Advanced Usage

### Custom Selectors

You can use any CSS selector:
```
browser_click({ selector: "button[aria-label='Submit']" })
browser_fill({ selector: "input[name='username']", text: "admin" })
```

### JavaScript Execution

Run custom JavaScript in the browser:
```
browser_evaluate({ 
  script: "return document.querySelectorAll('.ag-row').length" 
})
```

### Full Page Screenshots

Capture the entire page:
```
browser_screenshot({ 
  path: "./screenshots/full-page.png",
  fullPage: true 
})
```

### Waiting for Dynamic Content

Wait for elements that load asynchronously:
```
browser_wait_for_selector({ 
  selector: ".loading-complete",
  timeout: 30000 
})
```

## Best Practices

### 1. Always Wait for Elements
```
browser_wait_for_selector({ selector: ".my-button" })
browser_click({ selector: ".my-button" })
```

### 2. Use Specific Selectors
- ✅ `button[aria-label='Send']`
- ✅ `input[name='username']`
- ❌ `button` (too generic)

### 3. Take Screenshots on Failure
```
browser_screenshot({ path: "./screenshots/error-state.png" })
```

### 4. Close Browser When Done
```
browser_close()
```

### 5. Verify State
```
browser_evaluate({ 
  script: "document.querySelector('.success') !== null" 
})
```

## Integration with CI/CD

You can automate these tests in your CI/CD pipeline:

```yaml
# .github/workflows/e2e-tests.yml
name: E2E Tests

on: [push, pull_request]

jobs:
  e2e:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      
      - name: Start services
        run: docker-compose up -d
      
      - name: Setup MCP Browser Server
        run: |
          cd mcp-browser-server
          npm install
          npm run install-browsers
          npm run build
      
      - name: Run E2E tests
        run: |
          # Run your test scripts here
          node run-e2e-tests.js
      
      - name: Upload screenshots
        uses: actions/upload-artifact@v3
        with:
          name: screenshots
          path: tests/e2e/screenshots/
```

## Next Steps

1. **Run the example tests** in `/tests/e2e/`
2. **Create custom tests** for your specific workflows
3. **Automate tests** in your CI/CD pipeline
4. **Add visual regression testing** with screenshot comparison

## Resources

- [MCP Browser Server README](./mcp-browser-server/README.md)
- [E2E Test Documentation](./tests/e2e/README.md)
- [Playwright Documentation](https://playwright.dev/)
- [MCP Protocol Spec](https://modelcontextprotocol.io/)

## Support

If you encounter issues:
1. Check the troubleshooting section above
2. Review the MCP server logs
3. Inspect browser console for errors
4. Verify all services are running

---

**Happy Testing! 🎉**