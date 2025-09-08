---
description: "Testing standards and patterns for OpsConductor services"
globs: ["**/test_*.py", "**/tests/**/*.py", "**/*test*.py"]
alwaysApply: false
---

# OpsConductor Testing Standards

## 🧪 Testing Framework Stack

### End-to-End Testing
- **Framework**: Playwright with TypeScript
- **Location**: `/tests/e2e/`
- **Coverage**: 12 comprehensive test files covering all major functionality
- **Configuration**: `playwright.config.ts`

### Unit Testing (Python Services)
- **Framework**: pytest
- **Mocking**: unittest.mock
- **Database**: Test fixtures with isolated transactions
- **Async**: pytest-asyncio for async function testing

## 📁 Test Structure

```
tests/
├── e2e/                    # Playwright end-to-end tests
│   ├── auth.spec.ts       # Authentication flows
│   ├── targets.spec.ts    # Target management
│   ├── jobs.spec.ts       # Job creation and execution
│   └── ...
├── unit/                  # Python unit tests (per service)
│   ├── test_auth_service.py
│   ├── test_utility_modules.py
│   └── ...
└── fixtures/              # Test data and fixtures
```

## 🎯 Testing Patterns

### Utility Module Testing
```python
import pytest
from unittest.mock import Mock, patch, MagicMock
import utility_email_sender as email_utility

@pytest.fixture
def mock_db_cursor():
    """Mock database cursor for testing"""
    cursor = MagicMock()
    cursor.fetchone.return_value = {"id": 1, "email": "test@example.com"}
    cursor.fetchall.return_value = [{"id": 1}, {"id": 2}]
    return cursor

@pytest.fixture
def setup_email_utility(mock_db_cursor):
    """Setup email utility with mocked dependencies"""
    email_utility.set_smtp_config({
        "host": "smtp.test.com",
        "port": 587,
        "username": "test@example.com",
        "password": "testpass"
    })
    email_utility.set_db_cursor_func(lambda: mock_db_cursor)
    return email_utility

def test_send_email_notification_success(setup_email_utility):
    """Test successful email notification sending"""
    with patch('smtplib.SMTP') as mock_smtp:
        mock_server = Mock()
        mock_smtp.return_value.__enter__.return_value = mock_server
        
        result = await setup_email_utility.send_email_notification(
            notification_id=123,
            dest="user@example.com",
            payload={"job_name": "test_job", "status": "completed"}
        )
        
        assert result is True
        mock_server.send_message.assert_called_once()

def test_send_email_notification_failure(setup_email_utility):
    """Test email notification failure handling"""
    with patch('smtplib.SMTP') as mock_smtp:
        mock_smtp.side_effect = Exception("SMTP connection failed")
        
        result = await setup_email_utility.send_email_notification(
            notification_id=123,
            dest="user@example.com",
            payload={"job_name": "test_job", "status": "failed"}
        )
        
        assert result is False
```

### FastAPI Endpoint Testing
```python
import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock
from main import app

client = TestClient(app)

@pytest.fixture
def mock_auth_token():
    """Mock valid authentication token"""
    with patch('shared.auth.verify_token') as mock_verify:
        mock_verify.return_value = {"user_id": 1, "username": "testuser"}
        yield mock_verify

@pytest.fixture
def mock_db_cursor():
    """Mock database cursor"""
    with patch('shared.database.get_db_cursor') as mock_cursor:
        cursor_mock = MagicMock()
        mock_cursor.return_value.__enter__.return_value = cursor_mock
        yield cursor_mock

def test_create_target_success(mock_auth_token, mock_db_cursor):
    """Test successful target creation"""
    mock_db_cursor.fetchone.return_value = {"id": 1, "name": "test-target"}
    
    response = client.post(
        "/targets",
        json={
            "name": "test-target",
            "host": "192.168.1.100",
            "platform": "windows",
            "credential_id": 1
        },
        headers={"Authorization": "Bearer test-token"}
    )
    
    assert response.status_code == 200
    assert response.json()["success"] is True
    assert "test-target" in response.json()["message"]

def test_create_target_validation_error(mock_auth_token):
    """Test target creation with validation error"""
    response = client.post(
        "/targets",
        json={"name": ""},  # Missing required fields
        headers={"Authorization": "Bearer test-token"}
    )
    
    assert response.status_code == 400
    assert "error" in response.json()
    assert response.json()["error"]["type"] == "ValidationError"
```

### Playwright E2E Testing
```typescript
import { test, expect } from '@playwright/test';

test.describe('Job Management', () => {
  test.beforeEach(async ({ page }) => {
    // Login before each test
    await page.goto('/login');
    await page.fill('[data-testid="username"]', 'admin');
    await page.fill('[data-testid="password"]', 'admin123');
    await page.click('[data-testid="login-button"]');
    await expect(page).toHaveURL('/dashboard');
  });

  test('should create a new job successfully', async ({ page }) => {
    // Navigate to jobs page
    await page.click('[data-testid="nav-jobs"]');
    await expect(page).toHaveURL('/jobs');

    // Create new job
    await page.click('[data-testid="create-job-button"]');
    await page.fill('[data-testid="job-name"]', 'Test Job');
    await page.selectOption('[data-testid="job-target"]', '1');
    
    // Add job step
    await page.click('[data-testid="add-step-button"]');
    await page.selectOption('[data-testid="step-type"]', 'command');
    await page.fill('[data-testid="step-command"]', 'echo "Hello World"');
    
    // Save job
    await page.click('[data-testid="save-job-button"]');
    
    // Verify success
    await expect(page.locator('[data-testid="success-message"]')).toBeVisible();
    await expect(page.locator('text=Test Job')).toBeVisible();
  });

  test('should execute job and show results', async ({ page }) => {
    // Navigate to existing job
    await page.goto('/jobs/1');
    
    // Execute job
    await page.click('[data-testid="execute-job-button"]');
    
    // Wait for execution to complete
    await expect(page.locator('[data-testid="execution-status"]')).toHaveText('completed', { timeout: 30000 });
    
    // Verify results
    await expect(page.locator('[data-testid="execution-output"]')).toContainText('Hello World');
  });
});
```

## 🔧 Test Configuration

### Playwright Configuration
```typescript
// playwright.config.ts
import { defineConfig, devices } from '@playwright/test';

export default defineConfig({
  testDir: './e2e',
  fullyParallel: true,
  forbidOnly: !!process.env.CI,
  retries: process.env.CI ? 2 : 0,
  workers: process.env.CI ? 1 : undefined,
  reporter: 'html',
  use: {
    baseURL: 'http://localhost:3000',
    trace: 'on-first-retry',
    screenshot: 'only-on-failure',
  },
  projects: [
    {
      name: 'chromium',
      use: { ...devices['Desktop Chrome'] },
    },
    {
      name: 'firefox',
      use: { ...devices['Desktop Firefox'] },
    },
  ],
  webServer: {
    command: 'npm start',
    url: 'http://localhost:3000',
    reuseExistingServer: !process.env.CI,
  },
});
```

### Pytest Configuration
```ini
# pytest.ini
[tool:pytest]
testpaths = tests/unit
python_files = test_*.py
python_classes = Test*
python_functions = test_*
addopts = 
    -v
    --tb=short
    --strict-markers
    --disable-warnings
    --cov=.
    --cov-report=html
    --cov-report=term-missing
markers =
    unit: Unit tests
    integration: Integration tests
    slow: Slow running tests
```

## 📊 Test Coverage Requirements

### Unit Tests
- **Utility Modules**: 90%+ coverage
- **Core Functions**: 100% coverage for critical paths
- **Error Handling**: All error conditions tested
- **Database Operations**: Mocked with transaction isolation

### E2E Tests
- **User Workflows**: Complete user journeys tested
- **Cross-Service Integration**: Service communication verified
- **UI Components**: All interactive elements tested
- **Error Scenarios**: User-facing error handling verified

## 🚀 Running Tests

### E2E Tests
```bash
cd tests
npm install
npx playwright test                    # Run all tests
npx playwright test --headed          # Run with browser visible
npx playwright test --debug           # Debug mode
npx playwright show-report           # View test report
```

### Unit Tests
```bash
# From service directory
pytest                                # Run all unit tests
pytest -v                            # Verbose output
pytest --cov=.                       # With coverage
pytest -k "test_email"               # Run specific tests
pytest --markers slow                # Run only slow tests
```

## 🎯 Testing Best Practices

### Test Organization
- **One test file per utility module**
- **Group related tests in classes**
- **Use descriptive test names**
- **Include both success and failure scenarios**

### Mocking Strategy
- **Mock external dependencies** (SMTP, HTTP requests, file system)
- **Use real database** with test transactions
- **Mock time-dependent operations**
- **Isolate tests from each other**

### Data Management
- **Use fixtures for test data**
- **Clean up after tests**
- **Use realistic test data**
- **Test edge cases and boundary conditions**

### Continuous Integration
- **Run tests on every commit**
- **Fail builds on test failures**
- **Generate coverage reports**
- **Test against multiple environments**

## 🔍 Test Debugging

### Common Issues
- **Async test failures**: Use `pytest-asyncio` and proper await syntax
- **Database state**: Ensure proper cleanup between tests
- **Mock configuration**: Verify mocks are properly configured
- **Timing issues**: Use appropriate timeouts in E2E tests

### Debugging Tools
- **Playwright Inspector**: Visual debugging for E2E tests
- **pytest --pdb**: Drop into debugger on failures
- **Coverage reports**: Identify untested code paths
- **Test logs**: Comprehensive logging for troubleshooting

---

**Comprehensive testing ensures OpsConductor reliability and maintainability across all services and user workflows.**