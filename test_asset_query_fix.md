# Quick Test Guide - Asset Query Fix

## Test in the UI

1. **Open the AI Chat interface:**
   - Navigate to http://localhost:3000
   - Go to the AI Chat page

2. **Run these test queries:**

### Test 1: List All Assets
```
list all assets
```

**Expected Result:**
- Should mention 17 assets total
- Should show diverse OS types (Linux: Ubuntu, CentOS, RHEL, Debian; Windows: Server 2022, Server 2019, 10, 11)
- Should mention multiple environments (production, development, staging)
- Should list various services (PostgreSQL, MySQL, MongoDB, Redis, Elasticsearch, NGINX, Apache, etc.)

**❌ Old Incorrect Behavior:**
- "All assets are Windows 10 workstations"
- "All in production with medium criticality"
- Only mentions 6-7 assets

---

### Test 2: Count Assets
```
how many assets do we have?
```

**Expected Result:**
- "17 assets" or "We have 17 assets"

---

### Test 3: Production Assets
```
show me all production assets
```

**Expected Result:**
- Should list 12 production assets
- Should include the new comprehensive ones:
  - prod-db-primary-01 (PostgreSQL)
  - prod-dc-primary-01 (Windows Domain Controller)
  - prod-api-gateway-01 (NGINX)
  - prod-cache-redis-01 (Redis)
  - prod-search-elastic-01 (Elasticsearch)

---

### Test 4: Linux Servers
```
what Linux servers do we have?
```

**Expected Result:**
- Should list 8 Linux servers
- Should mention different distributions:
  - Ubuntu 22.04 LTS
  - CentOS 7
  - RHEL 8.5
  - Debian 11

---

### Test 5: Database Servers
```
list all database servers
```

**Expected Result:**
- Should list 5 database servers:
  - prod-db-primary-01 (PostgreSQL)
  - staging-db-mysql-01 (MySQL)
  - dev-mongo-node-01 (MongoDB)
  - prod-cache-redis-01 (Redis)
  - prod-search-elastic-01 (Elasticsearch)

---

### Test 6: Data Center Location
```
show me assets in DC-West-01
```

**Expected Result:**
- Should list 6 assets in Silicon Valley datacenter
- Should include:
  - prod-db-primary-01
  - dev-web-apache-01
  - dev-mongo-node-01
  - prod-api-gateway-01
  - staging-app-win-01
  - dev-k8s-master-01

---

### Test 7: OS Types
```
what are the different operating systems?
```

**Expected Result:**
- Should list:
  - Linux: Ubuntu 22.04 LTS, CentOS 7, RHEL 8.5, Debian 11
  - Windows: Server 2022, Server 2019, Windows 10, Windows 11

---

### Test 8: Critical Assets
```
show me critical assets
```

**Expected Result:**
- Should list 3 critical assets:
  - prod-db-primary-01 (PostgreSQL database)
  - prod-dc-primary-01 (Domain Controller)
  - prod-api-gateway-01 (API Gateway)

---

### Test 9: Development Environment
```
list development environment assets
```

**Expected Result:**
- Should list 3 development assets:
  - dev-web-apache-01 (Apache web server)
  - dev-mongo-node-01 (MongoDB)
  - dev-k8s-master-01 (Kubernetes master)

---

### Test 10: Specific Service Type
```
show me all Redis servers
```

**Expected Result:**
- Should list prod-cache-redis-01
- Should mention:
  - Environment: production
  - Criticality: high
  - Location: DC-East-01 (New York)
  - Database: session_cache

---

## Verification Checklist

After running the tests, verify:

- [ ] AI reports 17 total assets (not 6-7)
- [ ] AI identifies both Linux and Windows systems (not just Windows 10)
- [ ] AI recognizes multiple environments (not just production)
- [ ] AI lists various service types (databases, web servers, infrastructure)
- [ ] AI provides accurate details from the new comprehensive assets
- [ ] AI doesn't claim "all assets are Windows 10 workstations"
- [ ] AI doesn't claim "all assets have medium criticality"
- [ ] AI correctly identifies critical, high, medium, and low priority assets
- [ ] AI correctly identifies assets in different data centers

---

## If Tests Fail

If the AI still provides incorrect information:

1. **Check the logs:**
   ```bash
   docker logs opsconductor-ai-pipeline --tail 100
   ```
   Look for: "🔍 ORCHESTRATOR: Detected asset query, injecting asset schema context"

2. **Verify the service restarted:**
   ```bash
   docker ps | grep ai-pipeline
   ```
   Check the "STATUS" column - should show "Up X minutes" (not hours)

3. **Check the execution results:**
   ```bash
   docker exec opsconductor-postgres psql -U opsconductor -d opsconductor -c "SELECT execution_id, status FROM execution.executions ORDER BY created_at DESC LIMIT 5;"
   ```
   Verify executions are completing successfully

4. **Restart the service again:**
   ```bash
   docker restart opsconductor-ai-pipeline
   sleep 5
   docker logs opsconductor-ai-pipeline --tail 20
   ```

---

## Success Indicators

✅ **The fix is working if you see:**
- Accurate asset counts
- Diverse OS types mentioned
- Multiple environments recognized
- Various service types listed
- Detailed information from the new comprehensive assets
- No more "all Windows 10 workstations" responses

🎉 **Congratulations!** The AI can now accurately analyze and report on your infrastructure assets!