# Test Queries for New Assets

## Quick Test Queries

Try these queries in the AI chat to test the new comprehensive assets:

### 1. Basic Count Query
```
How many assets do we have in total?
```
**Expected**: Should show 17 total assets

### 2. Environment-Based Query
```
Show me all production databases
```
**Expected**: Should list:
- prod-db-primary-01 (PostgreSQL)
- prod-cache-redis-01 (Redis)
- prod-search-elastic-01 (Elasticsearch)

### 3. Location-Based Query
```
What assets are in DC-West-01?
```
**Expected**: Should list 6 assets:
- prod-db-primary-01
- dev-web-apache-01
- staging-db-mysql-01
- dev-mongo-node-01
- staging-app-win-01
- dev-k8s-master-01

### 4. Service Type Query
```
Find all PostgreSQL servers
```
**Expected**: Should find prod-db-primary-01

### 5. OS-Based Query
```
List all Windows servers
```
**Expected**: Should list:
- prod-dc-primary-01 (Windows Server 2022)
- staging-app-win-01 (Windows Server 2019)

### 6. Hardware Query
```
Show me all Dell servers
```
**Expected**: Should list:
- prod-db-primary-01 (PowerEdge R740)
- prod-dc-primary-01 (PowerEdge R640)
- prod-cache-redis-01 (PowerEdge R740xd)
- prod-search-elastic-01 (PowerEdge R750)

### 7. Criticality Query
```
What are our critical assets?
```
**Expected**: Should list:
- prod-db-primary-01
- prod-dc-primary-01
- prod-api-gateway-01

### 8. Complex Query
```
Find production Linux databases in DC-East-01
```
**Expected**: Should find:
- prod-cache-redis-01
- prod-search-elastic-01

### 9. Tag-Based Query
```
Show assets tagged with 'critical'
```
**Expected**: Should list:
- prod-db-primary-01
- prod-dc-primary-01
- prod-api-gateway-01

### 10. Specific Asset Details
```
Tell me about the Redis cache server
```
**Expected**: Should provide details about prod-cache-redis-01

## Conversation History Tests

### Test 1: Follow-up Question
```
User: "What production databases do we have?"
AI: [Lists production databases]
User: "Tell me more about the Redis one"
```
**Expected**: AI should remember the previous context and provide details about prod-cache-redis-01

### Test 2: Reference Previous Answer
```
User: "Show me all assets in DC-West-01"
AI: [Lists 6 assets]
User: "Which of those are databases?"
```
**Expected**: AI should filter the previous list to show only databases

### Test 3: Multi-Turn Conversation
```
User: "What's our most critical database?"
AI: [Mentions prod-db-primary-01]
User: "What's its IP address?"
AI: [Should reference prod-db-primary-01 and say 10.20.30.100]
User: "What port does it use?"
AI: [Should say 5432]
```
**Expected**: AI maintains context throughout the conversation

### Test 4: Clarification
```
User: "Show me the Kubernetes server"
AI: [Shows dev-k8s-master-01]
User: "What version is it running?"
```
**Expected**: AI should reference the notes field and say "Kubernetes v1.28.3"

### Test 5: Comparison
```
User: "Compare the Windows servers"
AI: [Compares prod-dc-primary-01 and staging-app-win-01]
User: "Which one is more critical?"
```
**Expected**: AI should remember the comparison and say prod-dc-primary-01 (critical vs medium)

## Field Coverage Tests

### Test Hardware Information
```
What hardware model is the API gateway running on?
```
**Expected**: Cisco UCS C240 M5

### Test Location Information
```
Where is the MySQL staging database physically located?
```
**Expected**: DC-West-01, Building A, Server Room 2, Rack 8, U20-U22

### Test Service Configuration
```
What port does the Elasticsearch server use?
```
**Expected**: 9200 (secure)

### Test Notes Field
```
What's the backup schedule for the production PostgreSQL database?
```
**Expected**: Every 6 hours, RPO: 15 minutes, RTO: 1 hour

### Test Support Information
```
Who owns the domain controller?
```
**Expected**: Infrastructure Team (infra-support@company.com)

## Edge Cases

### Test Empty Results
```
Show me all assets in DC-South-01
```
**Expected**: No assets found (this datacenter doesn't exist)

### Test Multiple Criteria
```
Find critical production assets in DC-East-01
```
**Expected**: Should list:
- prod-dc-primary-01
- prod-api-gateway-01

### Test Partial Matches
```
Show me assets with 'prod' in the name
```
**Expected**: Should list all production assets (5 total)

## Performance Tests

### Test Large Result Set
```
List all assets with their IP addresses
```
**Expected**: Should list all 17 assets efficiently

### Test Complex Aggregation
```
How many assets do we have per environment and criticality?
```
**Expected**: Should provide breakdown:
- Production: 5 (3 critical, 2 high)
- Development: 3 (2 low, 1 medium)
- Staging: 2 (2 medium)

## Success Criteria

✅ All queries return accurate results
✅ Conversation history works across multiple turns
✅ AI can reference previous responses
✅ All fields are accessible and searchable
✅ Complex queries work correctly
✅ Follow-up questions maintain context
✅ No errors or timeouts
✅ Response times are reasonable (<5 seconds)

## Notes

- The assets are already in the database (IDs 8-17)
- No service restart required
- All fields are fully populated
- Tags are in JSONB format
- Credentials are encrypted (not visible in responses)