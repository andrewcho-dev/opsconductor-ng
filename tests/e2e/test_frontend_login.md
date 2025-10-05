# E2E Test: Frontend Login Flow

## Test Objective
Verify that users can successfully log in to the OpsConductor frontend.

## Prerequisites
- Frontend running on http://localhost:3100
- Valid test credentials available

## Test Steps

### 1. Navigate to Login Page
```
Tool: browser_navigate
Args: { "url": "http://localhost:3100" }
Expected: Page loads successfully
```

### 2. Verify Login Form Exists
```
Tool: browser_wait_for_selector
Args: { "selector": "input[name='username']", "timeout": 5000 }
Expected: Username field is visible
```

### 3. Fill Username
```
Tool: browser_fill
Args: { 
  "selector": "input[name='username']", 
  "text": "admin" 
}
Expected: Username field contains "admin"
```

### 4. Fill Password
```
Tool: browser_fill
Args: { 
  "selector": "input[name='password']", 
  "text": "admin123" 
}
Expected: Password field is filled
```

### 5. Click Login Button
```
Tool: browser_click
Args: { "selector": "button[type='submit']" }
Expected: Form submits
```

### 6. Wait for Dashboard
```
Tool: browser_wait_for_selector
Args: { "selector": ".dashboard, .navbar", "timeout": 10000 }
Expected: Dashboard or navbar appears
```

### 7. Verify URL Changed
```
Tool: browser_get_url
Expected: URL is not /login (redirected to dashboard)
```

### 8. Take Success Screenshot
```
Tool: browser_screenshot
Args: { 
  "path": "/home/opsconductor/opsconductor-ng/tests/e2e/screenshots/login-success.png",
  "fullPage": false
}
Expected: Screenshot saved
```

## Success Criteria
- ✅ Login form loads
- ✅ Credentials can be entered
- ✅ Login button works
- ✅ Redirect to dashboard occurs
- ✅ No error messages displayed

## Failure Scenarios
- ❌ Login form doesn't load (check frontend is running)
- ❌ Invalid credentials (verify test user exists)
- ❌ No redirect after login (check authentication logic)
- ❌ Error message appears (check backend logs)