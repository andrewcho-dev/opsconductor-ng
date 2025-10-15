# System Coherence Verification Guide

This document provides exact copy-paste commands to verify the system coherence implementation.

## Prerequisites

- Services running: automation-service, frontend, ai-pipeline, kong
- Base URL: `http://localhost:8010` (automation-service via Kong)
- Frontend URL: `http://localhost:3100`

## Verification Steps

### 1. Verify Tool Registry Contains Required Tools

**Command:**
```bash
curl -s http://localhost:8010/ai/tools/list | grep -o '"name":"[^"]*"' | cut -d'"' -f4
```

**Expected Output (should include):**
```
asset_count
asset_search
windows_list_directory
dns_lookup
tcp_port_check
http_check
traceroute
shell_ping
```

**Verification:**
```bash
./scripts/verify_tools.sh
```

**Expected:**
```
✅ SUCCESS: All required tools present
```

---

### 2. Verify Tool Hot-Reload Works

**Command:**
```bash
./scripts/hotreload_demo.sh
```

**Expected Output:**
```
✅ Hot-Reload Demo Complete
Initial count: 8
After add:     9
After remove:  8
```

**Manual Verification:**

1. Check initial count:
```bash
curl -s http://localhost:8010/ai/tools/list | grep -o '"total":[0-9]*' | cut -d':' -f2
```

2. Create temp tool:
```bash
cat > /workspace/tools/catalog/temp_test.yaml <<'EOF'
name: temp_test
display_name: Temp Test
description: Temporary test tool
category: test
platform: cross-platform
source: local
parameters: []
EOF
```

3. Reload registry:
```bash
curl -s -X POST http://localhost:8010/ai/tools/reload | grep -o '"count":[0-9]*' | cut -d':' -f2
```

4. Verify tool appears:
```bash
curl -s http://localhost:8010/ai/tools/list | grep -q '"name":"temp_test"' && echo "✅ FOUND" || echo "❌ NOT FOUND"
```

5. Remove temp tool:
```bash
rm /workspace/tools/catalog/temp_test.yaml
```

6. Reload again:
```bash
curl -s -X POST http://localhost:8010/ai/tools/reload | grep -o '"count":[0-9]*' | cut -d':' -f2
```

7. Verify tool removed:
```bash
curl -s http://localhost:8010/ai/tools/list | grep -q '"name":"temp_test"' && echo "❌ STILL FOUND" || echo "✅ REMOVED"
```

---

### 3. Verify Chat Query: "how many windows 10 os assets do we have?"

**Backend Test (Direct API):**
```bash
curl -s -X POST http://localhost:8010/ai/tools/execute \
  -H "Content-Type: application/json" \
  -d '{"name":"asset_count","params":{"os":"Windows 10"}}' \
  | grep -o '"success":[^,]*'
```

**Expected:**
```
"success":true
```

**Full Response:**
```bash
curl -s -X POST http://localhost:8010/ai/tools/execute \
  -H "Content-Type: application/json" \
  -d '{"name":"asset_count","params":{"os":"Windows 10"}}'
```

**Expected Output:**
```json
{
  "success": true,
  "tool": "asset_count",
  "output": "42",
  "error": null,
  "duration_ms": 45.23,
  "trace_id": "...",
  "timestamp": "2024-01-15T10:30:00Z"
}
```

**Frontend Test (Web Chat):**

1. Open browser: `http://localhost:3100`
2. Navigate to AI Chat
3. Type: `how many windows 10 os assets do we have?`
4. Press Enter
5. **Expected**: Returns actual count (e.g., "42 assets found")
6. **NOT Expected**: "No tools found" or canned response

---

### 4. Verify Chat Query: "show directory of the c drive on 192.168.50.211"

**Backend Test (Direct API):**
```bash
curl -s -X POST http://localhost:8010/ai/tools/execute \
  -H "Content-Type: application/json" \
  -d '{"name":"windows_list_directory","params":{"host":"192.168.50.211","path":"C:\\\\"}}' \
  | grep -o '"success":[^,]*'
```

**Expected (if credentials configured):**
```
"success":true
```

**Expected (if credentials NOT configured):**
```
"success":false
```

**Check for missing_credentials error:**
```bash
curl -s -X POST http://localhost:8010/ai/tools/execute \
  -H "Content-Type: application/json" \
  -d '{"name":"windows_list_directory","params":{"host":"192.168.50.211","path":"C:\\\\"}}' \
  | grep -o '"error":"[^"]*"'
```

**Expected (if no credentials):**
```
"error":"missing_credentials"
```

**Frontend Test (Web Chat):**

1. Open browser: `http://localhost:3100`
2. Navigate to AI Chat
3. Type: `show directory of the c drive on 192.168.50.211`
4. Press Enter
5. **Expected (if credentials configured)**: Returns directory listing
6. **Expected (if no credentials)**: Returns message "Credentials required on server for host 192.168.50.211 (WinRM). Ask admin to add them. No secrets were sent to your browser."
7. **NOT Expected**: 404 error, "Parameter validation failed", or "No tools found"

---

### 5. Verify No Secrets in Browser Logs

**Test:**

1. Open browser: `http://localhost:3100`
2. Open Developer Tools (F12)
3. Go to Console tab
4. Type in chat: `show directory of the c drive on 192.168.50.211`
5. Press Enter
6. Check console logs

**Expected:**
- No passwords visible in logs
- No credentials in network requests
- Trace IDs present for debugging

**Verification Command (check server logs):**
```bash
docker logs automation-service 2>&1 | grep -i password | grep -v "REDACTED" | grep -v "masked"
```

**Expected:**
- No plaintext passwords in logs
- All passwords should be "***REDACTED***" or "masked"

---

### 6. Verify Trace ID Propagation

**Test:**
```bash
TRACE_ID="test-trace-$(date +%s)"
curl -s -X POST http://localhost:8010/ai/tools/execute \
  -H "Content-Type: application/json" \
  -H "X-Trace-Id: $TRACE_ID" \
  -d '{"name":"shell_ping","params":{"host":"127.0.0.1","count":2}}' \
  | grep -o '"trace_id":"[^"]*"'
```

**Expected:**
```
"trace_id":"test-trace-1234567890"
```

**Verify in logs:**
```bash
docker logs automation-service 2>&1 | grep "$TRACE_ID"
```

**Expected:**
- Multiple log lines with the same trace ID
- Trace ID propagates through all components

---

### 7. Run Full E2E Smoke Test

**Command:**
```bash
./scripts/test_e2e_chat_smoke.sh
```

**Expected Output:**
```
========================================
✅ ALL TESTS PASSED
========================================

Summary:
  ✅ Tool registry contains required tools
  ✅ asset_count executes and returns data
  ✅ windows_list_directory handles missing credentials gracefully
  ✅ Local tools (shell_ping) execute correctly
```

---

## Acceptance Criteria Checklist

### ✅ Criterion 1: Tool List Contains Required Tools

**Command:**
```bash
curl -s http://localhost:8010/ai/tools/list | grep -E '"name":"(asset_count|asset_search|windows_list_directory)"' | wc -l
```

**Expected:** `3` (all three tools found)

---

### ✅ Criterion 2: Hot-Reload Works

**Command:**
```bash
./scripts/hotreload_demo.sh
```

**Expected:** Exit code 0, demo completes successfully

---

### ✅ Criterion 3: Chat Query "how many windows 10 os assets do we have?"

**Frontend Test:**
1. Open `http://localhost:3100`
2. Type query in chat
3. Verify returns real count (not canned message)

**Backend Test:**
```bash
curl -s -X POST http://localhost:8010/ai/tools/execute \
  -H "Content-Type: application/json" \
  -d '{"name":"asset_count","params":{"os":"Windows 10"}}' \
  | grep '"success":true'
```

**Expected:** Non-empty output (success:true found)

---

### ✅ Criterion 4: Chat Query "show directory of the c drive on 192.168.50.211"

**Frontend Test:**
1. Open `http://localhost:3100`
2. Type query in chat
3. Verify returns either:
   - Directory listing (if credentials configured)
   - "Credentials required" message (if no credentials)
4. Verify does NOT return:
   - 404 error
   - "Parameter validation failed"
   - "No tools found"

**Backend Test:**
```bash
curl -s -X POST http://localhost:8010/ai/tools/execute \
  -H "Content-Type: application/json" \
  -d '{"name":"windows_list_directory","params":{"host":"192.168.50.211","path":"C:\\\\"}}' \
  | grep -E '"success":(true|false)'
```

**Expected:** Non-empty output (either success:true or success:false with missing_credentials)

---

### ✅ Criterion 5: No Secrets in Browser Logs

**Test:**
1. Open browser DevTools
2. Execute windows_list_directory query
3. Check Console and Network tabs

**Expected:**
- No passwords visible
- No credentials in request payloads
- Trace IDs present

---

### ✅ Criterion 6: Trace IDs Propagate End-to-End

**Test:**
```bash
TRACE_ID="verify-$(date +%s)"
curl -s -X POST http://localhost:8010/ai/tools/execute \
  -H "X-Trace-Id: $TRACE_ID" \
  -H "Content-Type: application/json" \
  -d '{"name":"shell_ping","params":{"host":"127.0.0.1"}}' \
  | grep "$TRACE_ID"
```

**Expected:** Trace ID appears in response

---

### ✅ Criterion 7: No Docker Down -v Required

**Test:**
```bash
# Restart automation-service only
docker-compose restart automation-service

# Wait for startup
sleep 5

# Verify tools still work
curl -s http://localhost:8010/ai/tools/list | grep -o '"total":[0-9]*'
```

**Expected:** Tool list returns successfully after restart

---

## Quick Verification (All-in-One)

**Run all verification steps:**
```bash
echo "=== 1. Verify Tools ==="
./scripts/verify_tools.sh

echo ""
echo "=== 2. E2E Smoke Test ==="
./scripts/test_e2e_chat_smoke.sh

echo ""
echo "=== 3. Hot-Reload Demo ==="
./scripts/hotreload_demo.sh

echo ""
echo "=== ALL VERIFICATION COMPLETE ==="
```

---

## Troubleshooting

### Tool List Returns Empty

**Check:**
```bash
docker logs automation-service 2>&1 | grep ToolRegistry
```

**Solution:**
- Verify catalog directories exist
- Check YAML files are valid
- Trigger manual reload

### Tool Execution Fails

**Check:**
```bash
docker logs automation-service 2>&1 | grep ToolRunner
```

**Solution:**
- Verify tool source is correct (local vs pipeline)
- Check ai-pipeline is running (for pipeline tools)
- Verify parameters are correct

### Frontend Chat Not Working

**Check:**
```bash
# Check frontend logs
docker logs frontend 2>&1 | tail -50

# Check automation-service is accessible
curl http://localhost:8010/health
```

**Solution:**
- Verify Kong routing is correct
- Check frontend can reach automation-service
- Verify chatIntentRouter is loaded

---

## Success Criteria

All of the following must pass:

- ✅ `./scripts/verify_tools.sh` exits with code 0
- ✅ `./scripts/test_e2e_chat_smoke.sh` exits with code 0
- ✅ `./scripts/hotreload_demo.sh` exits with code 0
- ✅ Frontend chat returns real data (not canned responses)
- ✅ No secrets visible in browser logs
- ✅ Trace IDs propagate end-to-end
- ✅ No docker down -v required

---

## Next Steps

After verification passes:

1. **Commit changes** to branch
2. **Create pull request** with verification results
3. **Deploy to staging** for integration testing
4. **Monitor metrics** (Prometheus)
5. **Review audit logs** for credential access
6. **Document any issues** encountered

---

## Support

For issues or questions:
- Check logs: `docker logs automation-service`
- Review documentation: `docs/AI_TOOL_CATALOG.md`
- Run verification scripts with verbose output
- Check Prometheus metrics at `http://localhost:9090`