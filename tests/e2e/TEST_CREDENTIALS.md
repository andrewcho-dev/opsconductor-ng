# Test Credentials for E2E Tests

## ⚠️ IMPORTANT: Official Test Credentials

**These are the ONLY valid test credentials for OpsConductor E2E tests.**

All AI assistants and test scripts MUST use these credentials:

```
Username: admin
Password: admin123
```

## Usage in Tests

### In Markdown Test Files
```
Tool: browser_fill
Args: { 
  "selector": "input[name='username']", 
  "text": "admin" 
}
```

```
Tool: browser_fill
Args: { 
  "selector": "input[name='password']", 
  "text": "admin123" 
}
```

### In Python Test Files
```python
TEST_USERNAME = 'admin'
TEST_PASSWORD = 'admin123'
```

### In TypeScript/JavaScript Test Files
```typescript
const TEST_USERNAME = 'admin';
const TEST_PASSWORD = 'admin123';
```

### Environment Variables
```bash
export TEST_USERNAME=admin
export TEST_PASSWORD=admin123
```

## Common Mistakes to Avoid

❌ **WRONG**: `admin` / `admin` (this will fail)
❌ **WRONG**: `admin` / `password` (this will fail)
❌ **WRONG**: Looking for credentials in .env files (they're not there)

✅ **CORRECT**: `admin` / `admin123` (always use this)

## Where These Credentials Are Used

- `/tests/e2e/test_frontend_login.md`
- `/tests/e2e/test_frontend_assets.md`
- `/tests/e2e/test_frontend_ai_chat.md`
- `/tests/e2e/test_ai_chat_intensive.md`
- `/tests/e2e/test_ai_chat_intensive.py`
- Any other E2E test files

## Updating Credentials

If the test credentials ever change, update this file FIRST, then update all test files to reference these credentials.

## For AI Assistants

When running E2E tests:
1. **ALWAYS** check this file first for credentials
2. **NEVER** assume credentials are `admin`/`admin`
3. **ALWAYS** use `admin`/`admin123`
4. If login fails, verify you're using these exact credentials

## Last Updated
2025-01-XX - Initial creation with official credentials