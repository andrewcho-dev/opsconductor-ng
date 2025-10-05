# OpsConductor E2E Tests

End-to-end tests for the OpsConductor frontend using the Browser MCP Server.

## Overview

These tests verify the complete user workflows in the OpsConductor web interface, from login to complex operations like asset management and AI chat interactions.

## Test Structure

Each test is documented in a separate markdown file with:
- **Test Objective**: What the test validates
- **Prerequisites**: Required system state
- **Test Steps**: Detailed steps with MCP tool calls
- **Success Criteria**: What constitutes a pass
- **Failure Scenarios**: Common failure modes

## Available Tests

### 1. Login Flow (`test_frontend_login.md`)
Tests the authentication flow from login page to dashboard.

**Key Validations:**
- Login form renders
- Credentials can be entered
- Authentication succeeds
- Redirect to dashboard works

### 2. Assets Page (`test_frontend_assets.md`)
Tests the asset management interface.

**Key Validations:**
- Asset grid loads
- Data displays correctly
- Search/filter works
- Grid interactions function

### 3. AI Chat (`test_frontend_ai_chat.md`)
Tests the AI chat interface and message flow.

**Key Validations:**
- Chat interface loads
- Messages can be sent
- AI responds appropriately
- Chat history works

## Running Tests

### Prerequisites

1. **Start OpsConductor services:**
   ```bash
   cd /home/opsconductor/opsconductor-ng
   docker-compose up -d
   ```

2. **Verify frontend is accessible:**
   ```bash
   curl http://localhost:3100
   ```

3. **Setup MCP Browser Server:**
   ```bash
   cd mcp-browser-server
   ./setup.sh
   ```

### Using VS Code with MCP

1. **Configure VS Code** (add to `.vscode/settings.json`):
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

2. **Open test file** in VS Code

3. **Use AI assistant** to execute test steps:
   - Copy test steps from markdown
   - Ask AI to execute them using MCP tools
   - Review results and screenshots

### Manual Execution

You can also run the MCP server standalone and call tools programmatically:

```bash
cd mcp-browser-server
npm start
```

Then use an MCP client to send tool requests.

## Test Data

### Test Credentials
⚠️ **IMPORTANT**: Always use these exact credentials for E2E tests:
- Username: `admin`
- Password: `admin123`

See `/tests/e2e/TEST_CREDENTIALS.md` for the official credentials reference.

### Test Assets
Ensure at least one asset exists in the database for asset tests.

## Screenshots

Screenshots are saved to `/home/opsconductor/opsconductor-ng/tests/e2e/screenshots/`

Create the directory:
```bash
mkdir -p /home/opsconductor/opsconductor-ng/tests/e2e/screenshots
```

## Troubleshooting

### Browser doesn't launch
```bash
cd mcp-browser-server
npm run install-browsers
```

### Frontend not accessible
```bash
docker-compose ps
docker-compose logs frontend
```

### AI Chat not responding
```bash
docker-compose logs ai-pipeline
# Check if Ollama is running and model is loaded
```

### Selectors not found
- Use browser DevTools to inspect elements
- Update selectors in test files
- Increase timeout values if needed

## Best Practices

### 1. Wait for Elements
Always use `browser_wait_for_selector` before interacting:
```
browser_wait_for_selector({ selector: ".my-element" })
browser_click({ selector: ".my-element" })
```

### 2. Use Specific Selectors
Prefer specific selectors over generic ones:
- ✅ `button[aria-label='Send']`
- ❌ `button`

### 3. Take Screenshots on Failure
Capture state when tests fail:
```
browser_screenshot({ 
  path: "./screenshots/failure-state.png",
  fullPage: true 
})
```

### 4. Clean Up
Close browser after tests:
```
browser_close()
```

### 5. Verify State
Check actual state, don't assume:
```
browser_evaluate({ 
  script: "document.querySelector('.success-message') !== null" 
})
```

## Adding New Tests

1. Create new markdown file: `test_frontend_<feature>.md`
2. Follow the template structure
3. Document all steps with MCP tool calls
4. Include success criteria and failure scenarios
5. Add to this README

## CI/CD Integration

These tests can be automated in CI/CD pipelines:

```yaml
# Example GitHub Actions
- name: Run E2E Tests
  run: |
    docker-compose up -d
    cd mcp-browser-server
    npm install
    npm run build
    # Run tests via MCP client
```

## Contributing

When adding tests:
- Keep tests focused on one feature
- Document expected behavior clearly
- Include error scenarios
- Add screenshots for visual verification
- Update this README

## Resources

- [Playwright Documentation](https://playwright.dev/)
- [MCP Protocol Spec](https://modelcontextprotocol.io/)
- [OpsConductor Architecture](../../README.md)