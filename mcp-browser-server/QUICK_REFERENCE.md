# MCP Browser Server - Quick Reference

## Setup (Windows)

```powershell
# 1. Install Node.js from https://nodejs.org/

# 2. Copy mcp-browser-server folder to Windows

# 3. Run setup
cd C:\path\to\mcp-browser-server
.\setup.bat

# 4. Add to VS Code settings.json:
{
  "mcp.servers": {
    "browser": {
      "command": "node",
      "args": ["C:\\path\\to\\mcp-browser-server\\dist\\index.js"]
    }
  }
}

# 5. Restart VS Code
```

## Available Tools

| Tool | Description | Example |
|------|-------------|---------|
| `browser_navigate` | Go to URL | Navigate to http://192.168.1.100:3100 |
| `browser_click` | Click element | Click button with selector ".login-btn" |
| `browser_fill` | Fill input | Fill "input[name='username']" with "admin" |
| `browser_get_text` | Get text | Get text from ".error-message" |
| `browser_screenshot` | Take screenshot | Take screenshot named "login.png" |
| `browser_wait_for_selector` | Wait for element | Wait for ".dashboard" to appear |
| `browser_evaluate` | Run JavaScript | Evaluate "document.title" |
| `browser_get_url` | Get current URL | Get the current URL |
| `browser_go_back` | Go back | Go back to previous page |
| `browser_reload` | Reload page | Reload the current page |
| `browser_close` | Close browser | Close the browser |

## Common Test Patterns

### Login Test
```
Navigate to http://192.168.1.100:3100
Fill "input[name='username']" with "admin"
Fill "input[name='password']" with "password"
Click "button[type='submit']"
Wait for ".dashboard" to appear
Take screenshot named "logged-in.png"
```

### Check Page Loaded
```
Navigate to http://192.168.1.100:3100/assets
Wait for ".ag-grid" with timeout 10000
Take screenshot
```

### Test Form Submission
```
Navigate to http://192.168.1.100:3100/assets/new
Fill "input[name='hostname']" with "server01"
Fill "input[name='ip']" with "192.168.1.50"
Click "button[type='submit']"
Wait for ".success-message"
Take screenshot
```

### Test AI Chat
```
Navigate to http://192.168.1.100:3100/chat
Fill "textarea[placeholder*='message']" with "Show me all servers"
Click "button[aria-label='Send']"
Wait for ".ai-response" with timeout 30000
Get text from ".ai-response"
Take screenshot
```

## CSS Selector Tips

### By ID
```css
#login-button
```

### By Class
```css
.submit-btn
```

### By Attribute
```css
input[name='username']
button[type='submit']
a[href='/assets']
```

### By Text Content
```css
button:has-text("Login")
```

### Combining Selectors
```css
form.login-form button[type='submit']
```

### AG Grid Specific
```css
.ag-grid                    /* Grid container */
.ag-row                     /* Grid row */
.ag-cell                    /* Grid cell */
.ag-header-cell             /* Header cell */
input.ag-input-field-input  /* Search input */
```

## Troubleshooting

### Issue: "node is not recognized"
**Fix**: Restart terminal after installing Node.js

### Issue: "Cannot connect to server"
**Fix**: 
```powershell
# Test connectivity
curl http://YOUR-SERVER-IP:3100

# On Linux, allow port
sudo ufw allow 3100
```

### Issue: "Selector not found"
**Fix**: 
- Use browser DevTools to verify selector
- Add wait before clicking:
  ```
  Wait for ".my-button" to appear
  Click ".my-button"
  ```

### Issue: "MCP server not starting"
**Fix**:
- Check VS Code Output → MCP Logs
- Verify path uses `\\` not `\`
- Test manually: `node C:\path\to\dist\index.js`

### Issue: "Browser not found"
**Fix**:
```powershell
npx playwright install chromium
```

## File Locations

### Windows
```
C:\path\to\mcp-browser-server\
├── dist\index.js           # Compiled server
├── screenshots\            # Screenshots saved here
└── package.json
```

### Linux
```
/home/opsconductor/opsconductor-ng/
├── mcp-browser-server/     # Source code
└── tests/e2e/              # Test scenarios
```

## Network Setup

### Find Linux Server IP
```bash
# On Linux
hostname -I
```

### Test Connectivity
```powershell
# On Windows
curl http://YOUR-SERVER-IP:3100
```

### Using SSH Tunnel
```powershell
# On Windows
ssh -L 3100:localhost:3100 user@linux-server

# Then use
http://localhost:3100
```

## Natural Language Examples

### Simple Commands
```
"Navigate to the login page"
"Click the submit button"
"Take a screenshot"
"Fill the username field with admin"
```

### Complex Workflows
```
"Test the login flow: navigate to the frontend, 
login as admin/password, verify the dashboard loads, 
and take a screenshot"
```

```
"Go to the assets page, wait for the grid to load, 
search for 'server', and screenshot the results"
```

```
"Test the AI chat: navigate to chat, send the message 
'Show me all Linux servers', wait for the response, 
and screenshot it"
```

## Timeouts

| Operation | Default | Recommended |
|-----------|---------|-------------|
| Navigate | 30s | 30s |
| Click | 30s | 5s |
| Fill | 30s | 5s |
| Wait | 30s | 5-10s |
| AI Response | 30s | 30s |

Specify timeout:
```
Wait for ".slow-element" with timeout 60000
```

## Screenshot Tips

### Naming Convention
```
login-page.png
dashboard-loaded.png
assets-grid.png
error-state.png
before-action.png
after-action.png
```

### Location
Screenshots are saved to:
```
C:\path\to\mcp-browser-server\screenshots\
```

### Best Practices
- Take screenshots before and after actions
- Use descriptive names
- Capture error states
- Review before sharing (may contain sensitive data)

## Performance Tips

### Reduce Wait Times
```
# Instead of fixed delays
Wait 5 seconds

# Use conditional waits
Wait for ".element" to appear
```

### Reuse Browser
The browser stays open between commands. No need to close/reopen.

### Headless Mode
For faster testing (no visible window):
```typescript
// Edit src/index.ts
headless: true
```

## Common Selectors for OpsConductor

### Login Page
```css
input[name='username']
input[name='password']
button[type='submit']
.error-message
```

### Dashboard
```css
.dashboard
.welcome-message
nav a[href='/assets']
nav a[href='/chat']
```

### Assets Page
```css
.ag-grid
.ag-row
input.ag-input-field-input    /* Search */
button:has-text("Add Asset")
```

### AI Chat
```css
textarea[placeholder*='message']
button[aria-label='Send']
.ai-response
.message-list
```

## Useful Commands

### Rebuild After Changes
```powershell
npm run build
```

### Run Manually (for debugging)
```powershell
node dist\index.js
```

### Reinstall Browsers
```powershell
npx playwright install chromium
```

### Check Node Version
```powershell
node --version    # Should be 18+
npm --version
```

## Documentation

- **Quick Start**: `../WINDOWS_QUICK_START.md`
- **Detailed Setup**: `WINDOWS_SETUP.md`
- **Architecture**: `ARCHITECTURE.md`
- **Full README**: `README.md`
- **Test Scenarios**: `../tests/e2e/`

## Support

### Check Logs
VS Code → Output → MCP Logs

### Test Manually
```powershell
node C:\path\to\mcp-browser-server\dist\index.js
```

### Verify Setup
```powershell
node --version          # Check Node.js
npm list playwright     # Check Playwright
dir screenshots         # Check screenshots folder
```

## Quick Checklist

- [ ] Node.js 18+ installed
- [ ] mcp-browser-server folder copied to Windows
- [ ] `setup.bat` completed successfully
- [ ] VS Code settings.json configured
- [ ] VS Code restarted
- [ ] Can navigate to frontend URL in regular browser
- [ ] Test command works in Zencoder

---

**Ready to test!** 🚀