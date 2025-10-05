# E2E Test: AI Chat Intensive Testing Suite

## Test Objective
Comprehensive real-world testing of AI chat functionality with asset queries, performance metrics, and conversation flows. All tests run through the frontend with NO mocking - testing actual system performance.

## Prerequisites
- User is logged in with credentials: `admin` / `admin123` (see TEST_CREDENTIALS.md)
- AI Pipeline service is running
- Backend API is accessible
- At least some test assets exist in the database

## Test Categories

### Category 1: Asset Query Tests
Real asset queries testing the full AI pipeline integration.

### Category 2: Multi-Turn Conversations
Testing conversation context and follow-up queries.

### Category 3: Performance Tests
Measuring response times and system behavior under load.

### Category 4: Error Handling
Testing edge cases and error scenarios.

---

## TEST 1: List All Assets

### Objective
Verify AI can retrieve and display all assets.

### Steps

#### 1.1 Navigate to AI Chat
```
Tool: browser_click
Args: { "selector": "a[href='/ai-chat']" }
Expected: Navigation to AI chat page
```

#### 1.2 Wait for Chat Interface
```
Tool: browser_wait_for_selector
Args: { "selector": "textarea, input[type='text']", "timeout": 5000 }
Expected: Chat input ready
```

#### 1.3 Send Query
```
Tool: browser_fill
Args: { 
  "selector": "textarea, input[type='text']", 
  "text": "Show me all assets" 
}
```

#### 1.4 Click Send
```
Tool: browser_click
Args: { "selector": "button[aria-label='Send'], button:has-text('Send')" }
```

#### 1.5 Wait for Response (with timing)
```
Tool: browser_evaluate
Args: { 
  "script": "window.testStartTime = Date.now(); true" 
}
```

#### 1.6 Wait for AI Response
```
Tool: browser_wait_for_selector
Args: { 
  "selector": ".ai-message:last-child, .message.assistant:last-child",
  "timeout": 30000 
}
```

#### 1.7 Calculate Response Time
```
Tool: browser_evaluate
Args: { 
  "script": "Math.round(Date.now() - window.testStartTime)" 
}
Expected: Response time in milliseconds
```

#### 1.8 Get Response Text
```
Tool: browser_get_text
Args: { "selector": ".ai-message:last-child, .message.assistant:last-child" }
Expected: Asset list or count
```

#### 1.9 Take Screenshot
```
Tool: browser_screenshot
Args: { 
  "path": "/home/opsconductor/opsconductor-ng/tests/e2e/screenshots/intensive-list-all-assets.png",
  "fullPage": true
}
```

### Success Criteria
- ✅ Response received within 30 seconds
- ✅ Response contains asset information
- ✅ Response is not empty

---

## TEST 2: Filter by Operating System

### Objective
Test filtering assets by OS type.

### Steps

#### 2.1 Clear Input (if needed)
```
Tool: browser_evaluate
Args: { 
  "script": "document.querySelector('textarea, input[type=\"text\"]').value = ''; true" 
}
```

#### 2.2 Send Linux Filter Query
```
Tool: browser_fill
Args: { 
  "selector": "textarea, input[type='text']", 
  "text": "Show me all Linux servers" 
}
```

#### 2.3 Click Send
```
Tool: browser_click
Args: { "selector": "button[aria-label='Send'], button:has-text('Send')" }
```

#### 2.4 Start Timer
```
Tool: browser_evaluate
Args: { "script": "window.testStartTime = Date.now(); true" }
```

#### 2.5 Wait for Response
```
Tool: browser_wait_for_selector
Args: { 
  "selector": ".ai-message:last-child, .message.assistant:last-child",
  "timeout": 30000 
}
```

#### 2.6 Get Response Time
```
Tool: browser_evaluate
Args: { "script": "Math.round(Date.now() - window.testStartTime)" }
```

#### 2.7 Get Response Text
```
Tool: browser_get_text
Args: { "selector": ".ai-message:last-child, .message.assistant:last-child" }
```

#### 2.8 Verify "Linux" in Response
```
Tool: browser_evaluate
Args: { 
  "script": "document.querySelector('.ai-message:last-child, .message.assistant:last-child')?.textContent?.toLowerCase().includes('linux')" 
}
Expected: true
```

#### 2.9 Screenshot
```
Tool: browser_screenshot
Args: { 
  "path": "/home/opsconductor/opsconductor-ng/tests/e2e/screenshots/intensive-filter-linux.png",
  "fullPage": true
}
```

---

## TEST 3: Search by Hostname

### Objective
Test searching assets by hostname pattern.

### Steps

#### 3.1 Send Hostname Search Query
```
Tool: browser_fill
Args: { 
  "selector": "textarea, input[type='text']", 
  "text": "Find assets with hostname containing 'server'" 
}
```

#### 3.2 Send and Time
```
Tool: browser_click
Args: { "selector": "button[aria-label='Send'], button:has-text('Send')" }
```

```
Tool: browser_evaluate
Args: { "script": "window.testStartTime = Date.now(); true" }
```

#### 3.3 Wait for Response
```
Tool: browser_wait_for_selector
Args: { 
  "selector": ".ai-message:last-child, .message.assistant:last-child",
  "timeout": 30000 
}
```

#### 3.4 Get Metrics
```
Tool: browser_evaluate
Args: { 
  "script": "({ responseTime: Math.round(Date.now() - window.testStartTime), responseLength: document.querySelector('.ai-message:last-child, .message.assistant:last-child')?.textContent?.length || 0 })" 
}
```

#### 3.5 Screenshot
```
Tool: browser_screenshot
Args: { 
  "path": "/home/opsconductor/opsconductor-ng/tests/e2e/screenshots/intensive-search-hostname.png",
  "fullPage": true
}
```

---

## TEST 4: Count Assets

### Objective
Test counting functionality.

### Steps

#### 4.1 Send Count Query
```
Tool: browser_fill
Args: { 
  "selector": "textarea, input[type='text']", 
  "text": "How many assets do we have?" 
}
```

#### 4.2 Send
```
Tool: browser_click
Args: { "selector": "button[aria-label='Send'], button:has-text('Send')" }
```

#### 4.3 Wait for Response
```
Tool: browser_wait_for_selector
Args: { 
  "selector": ".ai-message:last-child, .message.assistant:last-child",
  "timeout": 30000 
}
```

#### 4.4 Get Response
```
Tool: browser_get_text
Args: { "selector": ".ai-message:last-child, .message.assistant:last-child" }
```

#### 4.5 Verify Number in Response
```
Tool: browser_evaluate
Args: { 
  "script": "/\\d+/.test(document.querySelector('.ai-message:last-child, .message.assistant:last-child')?.textContent || '')" 
}
Expected: true (response should contain a number)
```

#### 4.6 Screenshot
```
Tool: browser_screenshot
Args: { 
  "path": "/home/opsconductor/opsconductor-ng/tests/e2e/screenshots/intensive-count-assets.png",
  "fullPage": true
}
```

---

## TEST 5: Filter by IP Range

### Objective
Test IP address filtering.

### Steps

#### 5.1 Send IP Filter Query
```
Tool: browser_fill
Args: { 
  "selector": "textarea, input[type='text']", 
  "text": "Show me assets with IP addresses in the 192.168 range" 
}
```

#### 5.2 Send and Wait
```
Tool: browser_click
Args: { "selector": "button[aria-label='Send'], button:has-text('Send')" }
```

```
Tool: browser_wait_for_selector
Args: { 
  "selector": ".ai-message:last-child, .message.assistant:last-child",
  "timeout": 30000 
}
```

#### 5.3 Get Response
```
Tool: browser_get_text
Args: { "selector": ".ai-message:last-child, .message.assistant:last-child" }
```

#### 5.4 Screenshot
```
Tool: browser_screenshot
Args: { 
  "path": "/home/opsconductor/opsconductor-ng/tests/e2e/screenshots/intensive-filter-ip.png",
  "fullPage": true
}
```

---

## TEST 6: Multi-Turn Conversation - Follow-up Query

### Objective
Test conversation context with follow-up questions.

### Steps

#### 6.1 First Query
```
Tool: browser_fill
Args: { 
  "selector": "textarea, input[type='text']", 
  "text": "Show me all Linux servers" 
}
```

```
Tool: browser_click
Args: { "selector": "button[aria-label='Send'], button:has-text('Send')" }
```

```
Tool: browser_wait_for_selector
Args: { 
  "selector": ".ai-message:last-child, .message.assistant:last-child",
  "timeout": 30000 
}
```

#### 6.2 Follow-up Query (tests context)
```
Tool: browser_fill
Args: { 
  "selector": "textarea, input[type='text']", 
  "text": "How many are there?" 
}
```

```
Tool: browser_click
Args: { "selector": "button[aria-label='Send'], button:has-text('Send')" }
```

```
Tool: browser_wait_for_selector
Args: { 
  "selector": ".ai-message:last-child, .message.assistant:last-child",
  "timeout": 30000 
}
```

#### 6.3 Verify Context Maintained
```
Tool: browser_get_text
Args: { "selector": ".ai-message:last-child, .message.assistant:last-child" }
Expected: Should contain a count/number
```

#### 6.4 Count Total Messages
```
Tool: browser_evaluate
Args: { 
  "script": "document.querySelectorAll('.message, .user-message, .ai-message').length" 
}
Expected: Should be >= 4 (2 user + 2 AI)
```

#### 6.5 Screenshot
```
Tool: browser_screenshot
Args: { 
  "path": "/home/opsconductor/opsconductor-ng/tests/e2e/screenshots/intensive-multi-turn.png",
  "fullPage": true
}
```

---

## TEST 7: Complex Multi-Step Filtering

### Objective
Test complex conversation with multiple filtering steps.

### Steps

#### 7.1 Step 1: Get All Servers
```
Tool: browser_fill
Args: { 
  "selector": "textarea, input[type='text']", 
  "text": "Show me all servers" 
}
```

```
Tool: browser_click
Args: { "selector": "button[aria-label='Send'], button:has-text('Send')" }
```

```
Tool: browser_wait_for_selector
Args: { 
  "selector": ".ai-message:last-child, .message.assistant:last-child",
  "timeout": 30000 
}
```

#### 7.2 Step 2: Filter to Linux
```
Tool: browser_fill
Args: { 
  "selector": "textarea, input[type='text']", 
  "text": "Filter those to only Linux" 
}
```

```
Tool: browser_click
Args: { "selector": "button[aria-label='Send'], button:has-text('Send')" }
```

```
Tool: browser_wait_for_selector
Args: { 
  "selector": ".ai-message:last-child, .message.assistant:last-child",
  "timeout": 30000 
}
```

#### 7.3 Step 3: Show IP Addresses
```
Tool: browser_fill
Args: { 
  "selector": "textarea, input[type='text']", 
  "text": "Show me their IP addresses" 
}
```

```
Tool: browser_click
Args: { "selector": "button[aria-label='Send'], button:has-text('Send')" }
```

```
Tool: browser_wait_for_selector
Args: { 
  "selector": ".ai-message:last-child, .message.assistant:last-child",
  "timeout": 30000 
}
```

#### 7.4 Verify Conversation Length
```
Tool: browser_evaluate
Args: { 
  "script": "document.querySelectorAll('.message, .user-message, .ai-message').length" 
}
Expected: Should be >= 6 (3 user + 3 AI)
```

#### 7.5 Screenshot
```
Tool: browser_screenshot
Args: { 
  "path": "/home/opsconductor/opsconductor-ng/tests/e2e/screenshots/intensive-complex-filtering.png",
  "fullPage": true
}
```

---

## TEST 8: Performance - Simple Query Response Time

### Objective
Measure response time for simple queries.

### Steps

#### 8.1 Clear Chat (optional - start fresh)
```
Tool: browser_reload
```

```
Tool: browser_wait_for_selector
Args: { "selector": "textarea, input[type='text']", "timeout": 5000 }
```

#### 8.2 Send Simple Query with Precise Timing
```
Tool: browser_fill
Args: { 
  "selector": "textarea, input[type='text']", 
  "text": "List all assets" 
}
```

```
Tool: browser_evaluate
Args: { "script": "window.perfTestStart = performance.now(); true" }
```

```
Tool: browser_click
Args: { "selector": "button[aria-label='Send'], button:has-text('Send')" }
```

#### 8.3 Wait for Response
```
Tool: browser_wait_for_selector
Args: { 
  "selector": ".ai-message:last-child, .message.assistant:last-child",
  "timeout": 30000 
}
```

#### 8.4 Get Precise Response Time
```
Tool: browser_evaluate
Args: { 
  "script": "Math.round(performance.now() - window.perfTestStart)" 
}
Expected: < 30000ms (30 seconds)
```

#### 8.5 Screenshot
```
Tool: browser_screenshot
Args: { 
  "path": "/home/opsconductor/opsconductor-ng/tests/e2e/screenshots/intensive-performance-simple.png",
  "fullPage": true
}
```

---

## TEST 9: Performance - Multiple Rapid Queries

### Objective
Test system behavior with rapid consecutive queries.

### Steps

#### 9.1 Query 1
```
Tool: browser_fill
Args: { "selector": "textarea, input[type='text']", "text": "How many assets?" }
```

```
Tool: browser_click
Args: { "selector": "button[aria-label='Send'], button:has-text('Send')" }
```

```
Tool: browser_wait_for_selector
Args: { 
  "selector": ".ai-message:last-child, .message.assistant:last-child",
  "timeout": 30000 
}
```

#### 9.2 Query 2 (immediate)
```
Tool: browser_fill
Args: { "selector": "textarea, input[type='text']", "text": "Show Linux servers" }
```

```
Tool: browser_click
Args: { "selector": "button[aria-label='Send'], button:has-text('Send')" }
```

```
Tool: browser_wait_for_selector
Args: { 
  "selector": ".ai-message:last-child, .message.assistant:last-child",
  "timeout": 30000 
}
```

#### 9.3 Query 3 (immediate)
```
Tool: browser_fill
Args: { "selector": "textarea, input[type='text']", "text": "What about Windows?" }
```

```
Tool: browser_click
Args: { "selector": "button[aria-label='Send'], button:has-text('Send')" }
```

```
Tool: browser_wait_for_selector
Args: { 
  "selector": ".ai-message:last-child, .message.assistant:last-child",
  "timeout": 30000 
}
```

#### 9.4 Verify All Responses Present
```
Tool: browser_evaluate
Args: { 
  "script": "document.querySelectorAll('.ai-message, .message.assistant').length >= 3" 
}
Expected: true
```

#### 9.5 Screenshot
```
Tool: browser_screenshot
Args: { 
  "path": "/home/opsconductor/opsconductor-ng/tests/e2e/screenshots/intensive-rapid-queries.png",
  "fullPage": true
}
```

---

## TEST 10: Error Handling - Very Long Query

### Objective
Test system behavior with very long input.

### Steps

#### 10.1 Send Very Long Query
```
Tool: browser_fill
Args: { 
  "selector": "textarea, input[type='text']", 
  "text": "Show me all assets with the following criteria: operating system is Linux and hostname contains server and IP address is in the 192.168 range and status is active and location is datacenter and environment is production and owner is IT department and created date is within the last year and has tags including critical and important and high-priority" 
}
```

#### 10.2 Send
```
Tool: browser_click
Args: { "selector": "button[aria-label='Send'], button:has-text('Send')" }
```

#### 10.3 Wait for Response (longer timeout)
```
Tool: browser_wait_for_selector
Args: { 
  "selector": ".ai-message:last-child, .message.assistant:last-child",
  "timeout": 60000 
}
```

#### 10.4 Verify Response Received
```
Tool: browser_get_text
Args: { "selector": ".ai-message:last-child, .message.assistant:last-child" }
Expected: Some response (even if error message)
```

#### 10.5 Screenshot
```
Tool: browser_screenshot
Args: { 
  "path": "/home/opsconductor/opsconductor-ng/tests/e2e/screenshots/intensive-long-query.png",
  "fullPage": true
}
```

---

## TEST 11: Error Handling - Invalid Query

### Objective
Test handling of queries with invalid field names.

### Steps

#### 11.1 Send Invalid Query
```
Tool: browser_fill
Args: { 
  "selector": "textarea, input[type='text']", 
  "text": "Show me assets where nonexistent_field equals 'value'" 
}
```

#### 11.2 Send
```
Tool: browser_click
Args: { "selector": "button[aria-label='Send'], button:has-text('Send')" }
```

#### 11.3 Wait for Response
```
Tool: browser_wait_for_selector
Args: { 
  "selector": ".ai-message:last-child, .message.assistant:last-child",
  "timeout": 30000 
}
```

#### 11.4 Get Response
```
Tool: browser_get_text
Args: { "selector": ".ai-message:last-child, .message.assistant:last-child" }
Expected: Error message or graceful handling
```

#### 11.5 Screenshot
```
Tool: browser_screenshot
Args: { 
  "path": "/home/opsconductor/opsconductor-ng/tests/e2e/screenshots/intensive-invalid-query.png",
  "fullPage": true
}
```

---

## TEST 12: Extract Full Conversation Log

### Objective
Extract complete conversation for analysis.

### Steps

#### 12.1 Extract All Messages
```
Tool: browser_evaluate
Args: { 
  "script": "Array.from(document.querySelectorAll('.message, .user-message, .ai-message')).map((msg, idx) => ({ index: idx, role: msg.classList.contains('user') || msg.classList.contains('user-message') ? 'user' : 'ai', content: msg.textContent?.trim() || '', length: msg.textContent?.length || 0 }))" 
}
```

#### 12.2 Get Conversation Statistics
```
Tool: browser_evaluate
Args: { 
  "script": "({ totalMessages: document.querySelectorAll('.message, .user-message, .ai-message').length, userMessages: document.querySelectorAll('.user-message, .message.user').length, aiMessages: document.querySelectorAll('.ai-message, .message.assistant').length })" 
}
```

#### 12.3 Final Screenshot
```
Tool: browser_screenshot
Args: { 
  "path": "/home/opsconductor/opsconductor-ng/tests/e2e/screenshots/intensive-final-conversation.png",
  "fullPage": true
}
```

---

## Success Criteria Summary

### Asset Query Tests
- ✅ All asset queries return responses
- ✅ Filtering by OS works correctly
- ✅ Hostname search functions
- ✅ Count queries return numbers
- ✅ IP filtering works

### Multi-Turn Conversations
- ✅ Follow-up queries maintain context
- ✅ Complex multi-step filtering works
- ✅ Conversation history preserved

### Performance Tests
- ✅ Simple queries respond < 30 seconds
- ✅ Multiple rapid queries handled correctly
- ✅ System remains responsive

### Error Handling
- ✅ Long queries handled gracefully
- ✅ Invalid queries don't crash system
- ✅ Error messages are clear

## Performance Expectations

- **Simple queries**: < 10 seconds
- **Complex queries**: < 30 seconds
- **Multi-turn conversations**: < 60 seconds total
- **System responsiveness**: UI never freezes

## Failure Scenarios

### Common Issues
- ❌ **Timeout**: AI service not responding (check logs)
- ❌ **Empty response**: Backend API issue
- ❌ **Selector not found**: UI structure changed
- ❌ **Context lost**: Session management issue

### Debugging Steps
1. Check browser console for errors
2. Verify AI pipeline service is running
3. Check backend API logs
4. Verify database connectivity
5. Review screenshots for UI state

## Notes

- All tests run through actual frontend (no mocking)
- Response times include full round-trip (UI → API → LLM → API → UI)
- Screenshots saved for each test for debugging
- Conversation logs extracted for analysis
- Tests can be run individually or as a suite

## Running This Test Suite

Execute these tests using the MCP browser tools in your AI assistant. The assistant will:
1. Navigate through each test
2. Execute all steps
3. Capture metrics and screenshots
4. Report results

Simply say: "Run the AI Chat Intensive Test Suite" and provide the path to this file.