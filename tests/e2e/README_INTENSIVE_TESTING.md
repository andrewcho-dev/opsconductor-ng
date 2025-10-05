# AI Chat Intensive Testing Suite

## Overview

This test suite performs comprehensive, real-world testing of the AI Chat functionality with full system integration. All tests run through the frontend with **no mocking** - testing actual system performance and behavior.

## Test Categories

### 1. Asset Query Tests
- **List all assets**: Basic query to retrieve all assets
- **Filter by OS**: Query for specific operating systems (Linux, Windows)
- **Search by hostname**: Find assets by hostname patterns
- **Count assets**: Aggregate queries for asset counts
- **Filter by IP**: Query assets by IP address ranges

### 2. Multi-Turn Conversation Tests
- **Follow-up queries**: Test context retention across messages
- **Complex filtering**: Progressive refinement of queries
- **Context understanding**: Verify AI maintains conversation context

### 3. Performance Tests
- **Response time**: Measure AI response times for various queries
- **Multiple rapid queries**: Test system behavior under rapid message load
- **Load testing**: Verify system remains responsive

### 4. Error Handling Tests
- **Empty queries**: Verify empty messages are handled correctly
- **Very long queries**: Test with extremely long input
- **Invalid queries**: Test error handling for malformed queries

## Prerequisites

### 1. System Requirements
- Node.js 18+ installed
- Playwright installed
- OpsConductor backend services running
- Frontend running on http://localhost:3000 (or configured BASE_URL)

### 2. Environment Setup

Create a `.env.test` file in the project root:

```bash
BASE_URL=http://localhost:3000
TEST_USERNAME=admin
TEST_PASSWORD=admin123
```

### 3. Install Dependencies

```bash
# Install Playwright
npm install -D @playwright/test

# Install Playwright browsers
npx playwright install chromium
```

## Running the Tests

### Run All Intensive Tests

```bash
npx playwright test tests/e2e/test_ai_chat_intensive.spec.ts
```

### Run Specific Test Category

```bash
# Asset query tests only
npx playwright test tests/e2e/test_ai_chat_intensive.spec.ts -g "Asset Query"

# Performance tests only
npx playwright test tests/e2e/test_ai_chat_intensive.spec.ts -g "Performance"

# Multi-turn conversation tests
npx playwright test tests/e2e/test_ai_chat_intensive.spec.ts -g "Multi-turn"

# Error handling tests
npx playwright test tests/e2e/test_ai_chat_intensive.spec.ts -g "Error Handling"
```

### Run with UI Mode (Interactive)

```bash
npx playwright test tests/e2e/test_ai_chat_intensive.spec.ts --ui
```

### Run in Debug Mode

```bash
npx playwright test tests/e2e/test_ai_chat_intensive.spec.ts --debug
```

### Run with Headed Browser (Watch Tests Execute)

```bash
npx playwright test tests/e2e/test_ai_chat_intensive.spec.ts --headed
```

## Test Reports

### Report Locations

All test artifacts are saved in the following locations:

```
tests/e2e/
├── screenshots/
│   └── ai-chat-intensive/     # Screenshots from each test
├── reports/
│   ├── html/                  # HTML test report
│   ├── results.json           # JSON test results
│   ├── ai-chat-intensive-*.json  # Individual test reports
│   └── ai-chat-intensive-summary-*.json  # Summary reports
└── videos/                    # Videos of failed tests
```

### Viewing Reports

#### HTML Report (Recommended)

```bash
npx playwright show-report tests/e2e/reports/html
```

This opens an interactive HTML report in your browser with:
- Test results and status
- Screenshots and videos
- Timing information
- Error details

#### JSON Reports

Detailed JSON reports include:
- Test name and status
- Query sent
- Response time
- Response length
- Full conversation log
- Screenshots taken
- Error details (if failed)

Example report structure:

```json
{
  "testName": "Asset Query: List all assets",
  "timestamp": "2024-01-15T10:30:00.000Z",
  "duration": 5234,
  "status": "passed",
  "query": "Show me all assets",
  "responseTime": 4521,
  "responseLength": 1234,
  "conversationLog": [
    {
      "role": "user",
      "content": "Show me all assets",
      "timestamp": "2024-01-15T10:30:00.000Z"
    },
    {
      "role": "ai",
      "content": "Here are all the assets...",
      "timestamp": "2024-01-15T10:30:04.521Z"
    }
  ],
  "screenshots": ["list-all-assets-2024-01-15T10-30-04.png"]
}
```

#### Summary Report

The summary report provides aggregate statistics:

```json
{
  "totalTests": 15,
  "passed": 14,
  "failed": 1,
  "averageResponseTime": 4523.5,
  "totalDuration": 67852,
  "timestamp": "2024-01-15T10:35:00.000Z",
  "reports": [...]
}
```

## Performance Metrics

### Expected Performance

- **Simple queries**: < 10 seconds
- **Complex queries**: < 30 seconds
- **Multi-turn conversations**: < 60 seconds total
- **System should remain responsive** during all operations

### Performance Assertions

Tests include performance assertions:
- Response time < 30 seconds (configurable)
- UI remains responsive
- No console errors
- Proper loading states

## Troubleshooting

### Tests Timing Out

If tests are timing out:

1. **Increase timeout in playwright.config.ts**:
   ```typescript
   timeout: 180 * 1000, // 3 minutes
   ```

2. **Check backend services**:
   ```bash
   docker-compose ps
   ```

3. **Check LLM service**:
   - Verify LLM service is running
   - Check LLM service logs for errors

### Tests Failing to Find Elements

If tests can't find UI elements:

1. **Run in headed mode** to see what's happening:
   ```bash
   npx playwright test --headed
   ```

2. **Check selectors** in the test file match your UI
3. **Update selectors** if UI has changed

### Authentication Issues

If login is failing:

1. **Verify credentials** in `.env.test`
2. **Check authentication service** is running
3. **Try manual login** to verify credentials work

### Slow Performance

If tests are running very slowly:

1. **Check system resources** (CPU, memory)
2. **Verify LLM service** is responding quickly
3. **Check network latency** if using remote services
4. **Review backend logs** for performance issues

## Customization

### Adding New Test Scenarios

To add new test scenarios, follow this pattern:

```typescript
test('Your Test Name', async ({ page }) => {
  const testName = 'Your Test Name';
  const query = 'Your query here';
  const startTime = Date.now();
  
  try {
    const { responseText, responseTime } = await sendMessageAndWaitForResponse(page, query);
    
    // Your assertions
    expect(responseText.length).toBeGreaterThan(0);
    
    // Take screenshot
    const screenshot = await takeTimestampedScreenshot(page, 'your-test-name');
    
    // Extract conversation
    const conversationLog = await extractConversationLog(page);
    
    // Save report
    saveTestReport({
      testName,
      timestamp: new Date().toISOString(),
      duration: Date.now() - startTime,
      status: 'passed',
      query,
      responseTime,
      responseLength: responseText.length,
      conversationLog,
      screenshots: [screenshot]
    });
    
    console.log(`✅ ${testName}`);
    
  } catch (error) {
    saveTestReport({
      testName,
      timestamp: new Date().toISOString(),
      duration: Date.now() - startTime,
      status: 'failed',
      query,
      error: error instanceof Error ? error.message : String(error)
    });
    throw error;
  }
});
```

### Modifying Timeouts

Adjust timeouts in the helper function:

```typescript
await sendMessageAndWaitForResponse(page, query, 90000); // 90 seconds
```

### Changing Report Format

Modify the `saveTestReport` function to include additional metrics or change the format.

## CI/CD Integration

### GitHub Actions Example

```yaml
name: AI Chat E2E Tests

on:
  push:
    branches: [ main ]
  pull_request:
    branches: [ main ]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      
      - name: Setup Node.js
        uses: actions/setup-node@v3
        with:
          node-version: '18'
      
      - name: Install dependencies
        run: npm ci
      
      - name: Install Playwright
        run: npx playwright install --with-deps chromium
      
      - name: Start services
        run: docker-compose up -d
      
      - name: Wait for services
        run: sleep 30
      
      - name: Run tests
        run: npx playwright test tests/e2e/test_ai_chat_intensive.spec.ts
        env:
          BASE_URL: http://localhost:3000
          TEST_USERNAME: admin
          TEST_PASSWORD: admin123
      
      - name: Upload test results
        if: always()
        uses: actions/upload-artifact@v3
        with:
          name: playwright-report
          path: tests/e2e/reports/
```

## Best Practices

1. **Run tests sequentially** - AI tests can be resource-intensive
2. **Monitor system resources** during test execution
3. **Review conversation logs** to understand AI behavior
4. **Keep screenshots** for debugging and documentation
5. **Update tests** when UI or functionality changes
6. **Run regularly** to catch regressions early
7. **Analyze performance trends** over time

## Support

For issues or questions:
1. Check the troubleshooting section above
2. Review test logs and screenshots
3. Check backend service logs
4. Verify system requirements are met