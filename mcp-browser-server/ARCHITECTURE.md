# MCP Browser Server Architecture

## Overview

This document explains how the MCP Browser Server works and how it connects your Windows machine to your Linux-hosted frontend.

## Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────────┐
│                        Your Windows Machine                          │
│                                                                      │
│  ┌────────────────────────────────────────────────────────────┐    │
│  │                      VS Code                                │    │
│  │                                                             │    │
│  │  ┌──────────────────────────────────────────────────────┐  │    │
│  │  │              Zencoder (AI Assistant)                 │  │    │
│  │  │                                                      │  │    │
│  │  │  User: "Navigate to the frontend and test login"    │  │    │
│  │  └──────────────────┬───────────────────────────────────┘  │    │
│  │                     │                                       │    │
│  │                     │ MCP Protocol                          │    │
│  │                     │ (JSON-RPC over stdio)                 │    │
│  │                     ▼                                       │    │
│  │  ┌──────────────────────────────────────────────────────┐  │    │
│  │  │           MCP Browser Server (Node.js)               │  │    │
│  │  │                                                      │  │    │
│  │  │  - Receives tool requests                           │  │    │
│  │  │  - Translates to Playwright commands                │  │    │
│  │  │  - Manages browser lifecycle                        │  │    │
│  │  │  - Returns results (text, screenshots, etc.)        │  │    │
│  │  └──────────────────┬───────────────────────────────────┘  │    │
│  └────────────────────┼────────────────────────────────────────┘    │
│                       │                                             │
│                       │ Playwright API                              │
│                       │                                             │
│                       ▼                                             │
│  ┌──────────────────────────────────────────────────────────────┐  │
│  │                  Chromium Browser                             │  │
│  │                                                               │  │
│  │  ┌────────────────────────────────────────────────────────┐  │  │
│  │  │         OpsConductor Frontend (React)                  │  │  │
│  │  │                                                        │  │  │
│  │  │  - Login page                                         │  │  │
│  │  │  - Dashboard                                          │  │  │
│  │  │  - Assets page (AG Grid)                             │  │  │
│  │  │  - AI Chat                                            │  │  │
│  │  └────────────────────────────────────────────────────────┘  │  │
│  │                           │                                   │  │
│  │                           │ HTTP Requests                     │  │
│  └───────────────────────────┼───────────────────────────────────┘  │
│                              │                                      │
└──────────────────────────────┼──────────────────────────────────────┘
                               │
                               │ Network (HTTP)
                               │
┌──────────────────────────────▼──────────────────────────────────────┐
│                      Your Linux Server                               │
│                                                                      │
│  ┌────────────────────────────────────────────────────────────┐    │
│  │              OpsConductor Backend                           │    │
│  │                                                             │    │
│  │  - FastAPI server (port 3100)                              │    │
│  │  - Serves React frontend                                   │    │
│  │  - Handles API requests                                    │    │
│  │  - AI chat endpoints                                       │    │
│  │  - Asset management                                        │    │
│  └────────────────────────────────────────────────────────────┘    │
│                                                                      │
└──────────────────────────────────────────────────────────────────────┘
```

## Component Details

### 1. VS Code + Zencoder (Windows)

**Location**: Your Windows machine  
**Purpose**: User interface for AI-powered testing

- You type natural language commands
- Zencoder interprets them and calls MCP tools
- Results are displayed in the chat

**Example**:
```
You: "Navigate to the login page and take a screenshot"
Zencoder: [Calls browser_navigate and browser_screenshot tools]
Zencoder: "Here's the screenshot of the login page"
```

### 2. MCP Browser Server (Windows)

**Location**: Your Windows machine  
**Purpose**: Bridge between AI and browser

**Key Responsibilities**:
- Listens for MCP protocol messages on stdio
- Translates tool requests into Playwright commands
- Manages browser lifecycle (launch, close, cleanup)
- Captures screenshots and saves them locally
- Returns results back to VS Code

**Technology Stack**:
- Node.js + TypeScript
- Playwright (browser automation)
- MCP SDK (protocol implementation)

**Communication**:
- **Input**: JSON-RPC messages from VS Code via stdin
- **Output**: JSON-RPC responses via stdout

### 3. Chromium Browser (Windows)

**Location**: Your Windows machine  
**Purpose**: Actual browser that renders and interacts with the frontend

**Features**:
- Runs in headed mode (you can see it!)
- Controlled by Playwright
- Executes JavaScript
- Renders React components
- Handles user interactions (clicks, typing, etc.)

**Why Chromium?**:
- Consistent across platforms
- Excellent automation support
- Fast and reliable
- Bundled with Playwright

### 4. OpsConductor Frontend (Linux)

**Location**: Your Linux server  
**Purpose**: The application being tested

**Access**:
- Served by FastAPI on port 3100
- Accessible via HTTP from Windows
- URL: `http://YOUR-LINUX-SERVER-IP:3100`

**Components**:
- React + TypeScript
- AG Grid for asset tables
- AI chat interface
- Authentication system

### 5. OpsConductor Backend (Linux)

**Location**: Your Linux server  
**Purpose**: API server and frontend host

**Responsibilities**:
- Serves the React frontend
- Handles API requests
- Manages authentication
- Processes AI chat messages
- Asset CRUD operations

## Data Flow Example

Let's trace a complete test scenario:

### Scenario: Test Login Flow

```
1. User types in VS Code:
   "Navigate to http://192.168.1.100:3100 and test the login"

2. Zencoder interprets this and calls:
   browser_navigate({ url: "http://192.168.1.100:3100" })

3. MCP Browser Server receives the request:
   {
     "jsonrpc": "2.0",
     "method": "tools/call",
     "params": {
       "name": "browser_navigate",
       "arguments": { "url": "http://192.168.1.100:3100" }
     }
   }

4. MCP Server translates to Playwright:
   await page.goto("http://192.168.1.100:3100")

5. Chromium browser on Windows:
   - Makes HTTP request to Linux server
   - Receives HTML/JS/CSS
   - Renders the login page

6. Linux server:
   - Receives HTTP request
   - Serves React frontend files
   - Returns HTML/JS/CSS

7. Browser renders the page

8. MCP Server returns success:
   {
     "jsonrpc": "2.0",
     "result": {
       "content": [
         {
           "type": "text",
           "text": "Navigated to http://192.168.1.100:3100"
         }
       ]
     }
   }

9. Zencoder shows result to user:
   "Successfully navigated to the login page"

10. Zencoder continues with next steps:
    browser_fill({ selector: "input[name='username']", text: "admin" })
    browser_fill({ selector: "input[name='password']", text: "password" })
    browser_click({ selector: "button[type='submit']" })
    browser_screenshot({ filename: "login-success.png" })
```

## Network Requirements

### Ports

- **3100**: OpsConductor frontend/backend (Linux)
- **No inbound ports needed on Windows**

### Firewall Rules

**On Linux**:
```bash
sudo ufw allow 3100
```

**On Windows**:
- No special rules needed (outbound HTTP is allowed by default)

### Network Connectivity

The Windows machine must be able to reach the Linux server:

```
Windows → Linux (port 3100) ✓ Required
Linux → Windows              ✗ Not needed
```

Test connectivity:
```powershell
# On Windows
curl http://YOUR-LINUX-SERVER-IP:3100
```

## File Locations

### On Windows

```
C:\Users\YourName\Projects\mcp-browser-server\
├── dist\
│   └── index.js              # Compiled MCP server
├── src\
│   └── index.ts              # Source code
├── screenshots\              # Screenshots saved here
├── package.json
├── tsconfig.json
└── setup.bat                 # Setup script
```

### On Linux

```
/home/opsconductor/opsconductor-ng/
├── mcp-browser-server/       # Source (can be copied to Windows)
├── tests/e2e/                # Test scenarios
│   ├── test_frontend_login.md
│   ├── test_frontend_assets.md
│   └── test_frontend_ai_chat.md
└── frontend/                 # React app (served by backend)
```

## MCP Protocol Details

### Tool Request Format

```json
{
  "jsonrpc": "2.0",
  "id": 1,
  "method": "tools/call",
  "params": {
    "name": "browser_navigate",
    "arguments": {
      "url": "http://192.168.1.100:3100"
    }
  }
}
```

### Tool Response Format

```json
{
  "jsonrpc": "2.0",
  "id": 1,
  "result": {
    "content": [
      {
        "type": "text",
        "text": "Navigated to http://192.168.1.100:3100"
      }
    ]
  }
}
```

### Available Tools

1. **browser_navigate** - Go to URL
2. **browser_click** - Click element
3. **browser_fill** - Fill input field
4. **browser_get_text** - Get text content
5. **browser_screenshot** - Take screenshot
6. **browser_wait_for_selector** - Wait for element
7. **browser_evaluate** - Run JavaScript
8. **browser_get_url** - Get current URL
9. **browser_go_back** - Go back
10. **browser_reload** - Reload page
11. **browser_close** - Close browser

## Security Considerations

### Local Network

- Browser runs on your local Windows machine
- All data stays on your network
- No external services involved

### Credentials

- Test credentials are sent over HTTP (not HTTPS by default)
- Use test accounts, not production credentials
- Consider using HTTPS if testing with sensitive data

### Screenshots

- Saved locally on Windows
- May contain sensitive information
- Review before sharing

## Performance

### Typical Response Times

- **Navigate**: 1-3 seconds
- **Click**: 100-500ms
- **Fill**: 100-300ms
- **Screenshot**: 500ms-2s
- **AI Chat response**: 5-30 seconds (depends on LLM)

### Resource Usage

- **Memory**: ~200-500 MB (Chromium + Node.js)
- **CPU**: Low (idle), Medium (during interactions)
- **Disk**: ~200 MB (Chromium) + screenshots

## Troubleshooting

### Connection Issues

**Symptom**: "Failed to navigate" or "Connection refused"

**Diagnosis**:
```powershell
# Test from Windows
curl http://YOUR-LINUX-SERVER-IP:3100
```

**Solutions**:
- Check Linux firewall: `sudo ufw allow 3100`
- Verify frontend is running: `ps aux | grep uvicorn`
- Check network connectivity: `ping YOUR-LINUX-SERVER-IP`

### MCP Server Not Starting

**Symptom**: Tools not available in VS Code

**Diagnosis**:
- Check VS Code Output → MCP Logs
- Run manually: `node C:\path\to\mcp-browser-server\dist\index.js`

**Solutions**:
- Verify path in settings.json (use `\\`)
- Rebuild: `npm run build`
- Check Node.js version: `node --version` (need 18+)

### Browser Not Launching

**Symptom**: "Browser not found" or "Failed to launch"

**Diagnosis**:
```powershell
npx playwright install chromium
```

**Solutions**:
- Reinstall browsers: `npx playwright install chromium`
- Check system dependencies
- Try running manually: `npm start`

## Extending the System

### Adding New Tools

Edit `src/index.ts`:

```typescript
server.setRequestHandler(ListToolsRequestSchema, async () => ({
  tools: [
    // ... existing tools ...
    {
      name: "browser_hover",
      description: "Hover over an element",
      inputSchema: {
        type: "object",
        properties: {
          selector: { type: "string", description: "CSS selector" }
        },
        required: ["selector"]
      }
    }
  ]
}));

// Add handler
if (params.name === "browser_hover") {
  const { selector } = params.arguments as { selector: string };
  await page.hover(selector);
  return { content: [{ type: "text", text: `Hovered over ${selector}` }] };
}
```

### Supporting Multiple Browsers

Playwright supports Firefox and WebKit:

```typescript
// In src/index.ts
import { firefox, webkit } from 'playwright';

// Launch Firefox instead
browser = await firefox.launch({ headless: false });

// Or WebKit (Safari)
browser = await webkit.launch({ headless: false });
```

### Headless Mode

For CI/CD or background testing:

```typescript
browser = await chromium.launch({ 
  headless: true  // No visible window
});
```

## Best Practices

### 1. Use Specific Selectors

❌ Bad:
```javascript
browser_click({ selector: "button" })
```

✅ Good:
```javascript
browser_click({ selector: "button[type='submit'][aria-label='Login']" })
```

### 2. Wait for Elements

❌ Bad:
```javascript
browser_click({ selector: ".submit-button" })
```

✅ Good:
```javascript
browser_wait_for_selector({ selector: ".submit-button", timeout: 5000 })
browser_click({ selector: ".submit-button" })
```

### 3. Take Screenshots

Always capture screenshots for debugging:

```javascript
browser_screenshot({ filename: "before-action.png" })
// ... perform action ...
browser_screenshot({ filename: "after-action.png" })
```

### 4. Handle Timeouts

For slow operations (like AI chat):

```javascript
browser_wait_for_selector({ 
  selector: ".ai-response", 
  timeout: 30000  // 30 seconds
})
```

### 5. Clean Up

Close the browser when done:

```javascript
browser_close()
```

## Summary

The MCP Browser Server creates a seamless bridge between:
- Your AI assistant (Zencoder) on Windows
- A real browser (Chromium) on Windows
- Your frontend application on Linux

This architecture allows you to:
- Test with natural language
- See the browser in action
- Capture screenshots locally
- Maintain full control over your data
- Work across your network

All while keeping your code on Linux and your testing environment on Windows! 🎉