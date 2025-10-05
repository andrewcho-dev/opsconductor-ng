# OpsConductor Browser MCP Server

MCP (Model Context Protocol) server for browser automation and end-to-end testing of the OpsConductor frontend.

## Features

- **Browser Control**: Navigate, click, fill forms, and interact with web pages
- **Testing Support**: Take screenshots, evaluate JavaScript, wait for elements
- **Playwright Integration**: Uses Playwright for reliable browser automation
- **MCP Compatible**: Works with any MCP client (VS Code, Claude Desktop, etc.)
- **Cross-Platform**: Run on Linux, Windows, or macOS

## Platform-Specific Setup

### 🪟 Windows Setup (Recommended for Local Testing)

**Use this if you want to run the browser on your Windows machine to test a frontend hosted on a Linux server.**

See **[WINDOWS_SETUP.md](./WINDOWS_SETUP.md)** for detailed instructions, or use the quick start:

```powershell
# 1. Install Node.js from https://nodejs.org/
# 2. Copy this folder to Windows
# 3. Run setup
.\setup.bat
```

Quick guide: **[../WINDOWS_QUICK_START.md](../WINDOWS_QUICK_START.md)**

### 🐧 Linux Setup

```bash
cd mcp-browser-server
./setup.sh
```

See **[INSTALL.md](./INSTALL.md)** for Node.js installation on Linux.

### Manual Installation (Any Platform)

```bash
cd mcp-browser-server
npm install
npm run install-browsers
npm run build
```

## Available Tools

### Navigation
- `browser_navigate` - Navigate to a URL
- `browser_go_back` - Go back in history
- `browser_reload` - Reload current page
- `browser_get_url` - Get current URL

### Interaction
- `browser_click` - Click an element (CSS selector)
- `browser_fill` - Fill an input field
- `browser_wait_for_selector` - Wait for element to appear

### Inspection
- `browser_get_text` - Get text content from element
- `browser_evaluate` - Execute JavaScript in browser
- `browser_screenshot` - Take a screenshot

### Control
- `browser_close` - Close the browser

## VS Code Configuration

### On Windows

Add to your VS Code settings (`.vscode/settings.json`):

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

**Note**: Use double backslashes (`\\`) and replace with your actual path.

### On Linux

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

## Usage Examples

### Basic Navigation Test
```
1. Navigate to http://localhost:3100
2. Wait for login form
3. Fill username and password
4. Click login button
5. Verify dashboard loads
```

### E2E Test Flow
```
1. Navigate to OpsConductor frontend
2. Login with credentials
3. Navigate to Assets page
4. Click "Add Asset" button
5. Fill asset form
6. Submit and verify success
7. Take screenshot of result
```

## Testing OpsConductor Frontend

### Prerequisites
- Frontend accessible via URL (e.g., `http://192.168.1.100:3100` or `http://localhost:3100`)
- Valid login credentials
- MCP server running on the same machine as your browser

### Example Test Scenarios

#### 1. Login Flow
```javascript
// Navigate to login (replace with your server URL)
browser_navigate({ url: "http://192.168.1.100:3100" })

// Fill credentials
browser_fill({ selector: "input[name='username']", text: "admin" })
browser_fill({ selector: "input[name='password']", text: "password" })

// Submit
browser_click({ selector: "button[type='submit']" })

// Verify dashboard
browser_wait_for_selector({ selector: ".dashboard" })
```

#### 2. Asset Management
```javascript
// Navigate to assets
browser_click({ selector: "a[href='/assets']" })

// Wait for grid
browser_wait_for_selector({ selector: ".ag-grid" })

// Get asset count
browser_evaluate({ 
  script: "document.querySelectorAll('.ag-row').length" 
})
```

#### 3. AI Chat Interaction
```javascript
// Navigate to AI Chat
browser_click({ selector: "a[href='/ai-chat']" })

// Send message
browser_fill({ 
  selector: "textarea[placeholder*='message']", 
  text: "Show me all Linux servers" 
})
browser_click({ selector: "button[aria-label='Send']" })

// Wait for response
browser_wait_for_selector({ selector: ".ai-response" })

// Get response text
browser_get_text({ selector: ".ai-response" })
```

## Development

### Build
```bash
npm run build
```

### Run
```bash
npm start
```

### Development Mode
```bash
npm run dev
```

## Troubleshooting

### Browser doesn't launch
- Ensure Playwright browsers are installed: `npm run install-browsers`
- Check system dependencies for Chromium

### Connection issues
- Verify MCP server is running
- Check VS Code MCP configuration
- Look for errors in VS Code Output panel

### Selector not found
- Use browser DevTools to verify selectors
- Increase timeout if page is slow to load
- Use `browser_wait_for_selector` before interacting

## Architecture

```
┌─────────────────────────────────────────┐
│         VS Code / MCP Client            │
│                                         │
│  - Sends tool requests                  │
│  - Receives results                     │
└──────────────┬──────────────────────────┘
               │ MCP Protocol (stdio)
               │
┌──────────────▼──────────────────────────┐
│      Browser MCP Server                 │
│                                         │
│  - Manages browser lifecycle            │
│  - Executes Playwright commands         │
│  - Returns results                      │
└──────────────┬──────────────────────────┘
               │ Playwright API
               │
┌──────────────▼──────────────────────────┐
│         Chromium Browser                │
│                                         │
│  - Renders OpsConductor frontend        │
│  - Executes user interactions           │
│  - Provides page state                  │
└─────────────────────────────────────────┘
```

## License

MIT