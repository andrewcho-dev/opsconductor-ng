# Chat Direct Execution - Test Plan

## Test Environment Setup

### Prerequisites
1. All Docker services running
2. Frontend dev server running (`npm start`)
3. Kong gateway accessible at `http://localhost:3000`
4. Automation service accessible at `http://localhost:8010`

### Environment Variables
Verify `.env` file contains:
```bash
REACT_APP_CHAT_DIRECT_EXEC=true
REACT_APP_AUTOMATION_SERVICE_URL=http://localhost:3000
REACT_APP_SELECTOR_BASE_PATH=/api/selector
```

## Manual Test Cases

### Test 1: Ping → Pong
**Objective:** Verify echo tool execution with "ping" input

**Steps:**
1. Open chat interface at `http://localhost:3100`
2. Type: `ping`
3. Press Enter

**Expected Result:**
- Response appears within 2 seconds
- AI responds with: `pong`
- Console shows: `[ChatExec] Executing echo tool: input="ping", trace_id=...`
- Console shows: `[ChatExec] Echo completed: duration=...ms, trace_id=...`
- Trace ID displayed below message (small gray text)

**Acceptance Criteria:**
✅ Response time < 2s  
✅ Output exactly matches "pong"  
✅ Console logs present  
✅ Trace ID visible  

---

### Test 2: Exact Echo
**Objective:** Verify echo tool with exact text reproduction

**Steps:**
1. Type: `Please echo this back exactly: OpsConductor walking skeleton v1.1.0`
2. Press Enter

**Expected Result:**
- Response appears within 2 seconds
- AI responds with: `OpsConductor walking skeleton v1.1.0`
- No additional text or formatting
- Console logs show full input text (truncated if > 50 chars)

**Acceptance Criteria:**
✅ Response time < 2s  
✅ Output exactly matches input text  
✅ No extra characters or formatting  
✅ Console logs present  

---

### Test 3: DNS Tools Search (No Platform)
**Objective:** Verify selector search without platform filter

**Steps:**
1. Type: `Find three tools that can help troubleshoot DNS problems`
2. Press Enter

**Expected Result:**
- Response appears within 2 seconds
- AI responds with: `Found X tools matching your query:` (where X = 0-5)
- If tools found: Display 2-5 tool cards with:
  - Tool name (bold)
  - Description text
  - Optional platform badge
- If no tools: Display "No tools found matching your query."
- Console shows: `[ChatSelector] Searching tools: query="Find three...", platform=any, k=3, trace_id=...`
- Console shows: `[ChatSelector] Search completed: duration=...ms, count=X, trace_id=...`

**Acceptance Criteria:**
✅ Response time < 2s  
✅ Tool cards rendered (if results exist)  
✅ Clear "no tools" message (if no results)  
✅ Console logs present  
✅ Trace ID visible  

---

### Test 4: Windows Platform Detection
**Objective:** Verify platform detection for Windows

**Steps:**
1. Type: `List two packet capture utilities for Windows`
2. Press Enter

**Expected Result:**
- Selector API called with `platform=windows` parameter
- Tool cards show blue "windows" badge
- Console shows: `[ChatSelector] Searching tools: query="...", platform=windows, k=3, trace_id=...`

**Acceptance Criteria:**
✅ Platform parameter sent correctly  
✅ Windows badge displayed (blue background)  
✅ Console logs show platform=windows  

---

### Test 5: Linux Platform Detection
**Objective:** Verify platform detection for Linux

**Steps:**
1. Type: `Show me network diagnostics tools for Linux`
2. Press Enter

**Expected Result:**
- Selector API called with `platform=linux` parameter
- Tool cards show green "linux" badge
- Console shows: `[ChatSelector] Searching tools: query="...", platform=linux, k=3, trace_id=...`

**Acceptance Criteria:**
✅ Platform parameter sent correctly  
✅ Linux badge displayed (green background)  
✅ Console logs show platform=linux  

---

## Automated Test Cases

### Unit Tests
Run with: `npm test chatIntentRouter.test.ts`

**Coverage:**
- Intent detection (9 tests)
- Echo execution (4 tests)
- Selector search (4 tests)

**Expected:** All 17 tests pass

---

## API Endpoint Tests

### Echo Endpoint Test
```bash
curl -X POST http://localhost:3000/ai/execute \
  -H "Content-Type: application/json" \
  -H "X-Trace-Id: test-123" \
  -d '{"tool":"echo","input":"ping"}'
```

**Expected Response:**
```json
{
  "success": true,
  "output": "pong",
  "error": null,
  "trace_id": "test-123",
  "duration_ms": 5.5,
  "tool": "echo"
}
```

### Selector Endpoint Test
```bash
curl "http://localhost:3000/api/selector/search?query=DNS&platform=windows&k=3" \
  -H "X-Trace-Id: test-456"
```

**Expected Response:**
```json
{
  "query": "DNS",
  "k": 3,
  "platform": ["windows"],
  "results": [
    {
      "name": "nslookup",
      "description": "DNS lookup utility",
      "platform": "windows"
    }
  ],
  "from_cache": false,
  "duration_ms": 125.5
}
```

**Note:** If database is empty, results array will be empty. This is expected for initial testing.

---

## Browser Console Verification

### Expected Log Format

**Echo Execution:**
```
[ChatExec] Executing echo tool: input="ping", trace_id=abc-123-def-456
[ChatExec] Echo completed: duration=5.50ms, trace_id=abc-123-def-456
```

**Selector Search:**
```
[ChatSelector] Searching tools: query="DNS tools", platform=any, k=3, trace_id=def-456-ghi-789
[ChatSelector] Search completed: duration=125.30ms, count=3, trace_id=def-456-ghi-789
```

### Trace ID Format
- UUID v4 format: `xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx`
- Consistent across request/response
- Visible in UI and console logs

---

## Error Scenarios

### Test: Network Error
**Steps:**
1. Stop automation service: `docker compose stop opsconductor-automation`
2. Type: `ping`
3. Press Enter

**Expected:**
- Error message displayed
- Console shows error log
- User-friendly message (not raw error)

**Cleanup:**
```bash
docker compose start opsconductor-automation
```

### Test: Invalid Input
**Steps:**
1. Type empty message
2. Press Enter

**Expected:**
- Message not sent
- No API call made
- Input field remains focused

---

## Feature Flag Test

### Test: Disable Direct Exec
**Steps:**
1. Edit `.env`: Set `REACT_APP_CHAT_DIRECT_EXEC=false`
2. Restart dev server
3. Type: `ping`
4. Press Enter

**Expected:**
- Legacy AI Pipeline behavior
- No `[ChatExec]` or `[ChatSelector]` logs
- Streaming progress updates
- Full AI analysis response

**Cleanup:**
```bash
# Restore .env
REACT_APP_CHAT_DIRECT_EXEC=true
# Restart dev server
```

---

## Performance Benchmarks

### Target Metrics
| Operation | Target | Typical | Max Acceptable |
|-----------|--------|---------|----------------|
| Echo (ping) | < 10ms | 5-8ms | 50ms |
| Echo (long text) | < 20ms | 10-15ms | 100ms |
| Selector search | < 200ms | 100-150ms | 500ms |
| Total response | < 500ms | 200-300ms | 2000ms |

### Measurement
Use browser DevTools Network tab:
1. Open DevTools (F12)
2. Go to Network tab
3. Filter by "Fetch/XHR"
4. Send chat message
5. Check request timing

---

## Troubleshooting

### Issue: No response from chat
**Check:**
1. Browser console for errors
2. Network tab for failed requests
3. Backend services status: `docker compose ps`
4. Environment variables in `.env`

### Issue: "No tools found" always
**Cause:** Selector database is empty (expected for initial testing)
**Solution:** This is normal. The selector search functionality works, but returns empty results.

### Issue: Trace IDs not showing
**Check:**
1. Browser console for `[ChatExec]` / `[ChatSelector]` logs
2. Verify `REACT_APP_CHAT_DIRECT_EXEC=true`
3. Clear browser cache and reload

### Issue: Feature flag not working
**Solution:**
1. Verify `.env` file changes
2. Restart dev server (`npm start`)
3. Hard refresh browser (Ctrl+Shift+R)

---

## Success Criteria Summary

All 5 manual test cases must pass:
- ✅ Test 1: Ping → Pong (< 2s)
- ✅ Test 2: Exact Echo (exact match)
- ✅ Test 3: DNS Tools Search (renders correctly)
- ✅ Test 4: Windows Platform (badge shown)
- ✅ Test 5: Linux Platform (badge shown)

All console logs must be present:
- ✅ `[ChatExec]` logs for echo operations
- ✅ `[ChatSelector]` logs for search operations
- ✅ Trace IDs in logs and UI

All unit tests must pass:
- ✅ 17/17 tests passing

---

## Next Steps After Testing

1. Take screenshots of successful test cases
2. Document any issues or edge cases found
3. Update README with actual performance metrics
4. Create PR with test results
5. Request code review

---

## Test Report Template

```markdown
## Test Execution Report

**Date:** YYYY-MM-DD
**Tester:** [Name]
**Environment:** Local Development

### Manual Tests
- [ ] Test 1: Ping → Pong
- [ ] Test 2: Exact Echo
- [ ] Test 3: DNS Tools Search
- [ ] Test 4: Windows Platform
- [ ] Test 5: Linux Platform

### Unit Tests
- [ ] All 17 tests passing

### Performance
- Echo (ping): __ms
- Echo (long): __ms
- Selector: __ms

### Issues Found
1. [Issue description]
2. [Issue description]

### Screenshots
- [Attach screenshots]

### Conclusion
[ ] All tests passed - Ready for PR
[ ] Issues found - Needs fixes
```