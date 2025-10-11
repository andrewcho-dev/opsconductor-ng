# Stage AB Semantic Retrieval - Deployment Checklist

## Pre-Deployment

- [ ] Review implementation documentation (`docs/STAGE_AB_SEMANTIC_RETRIEVAL.md`)
- [ ] Backup current database
- [ ] Backup current code (already done: `combined_selector.py.backup`)
- [ ] Verify Python dependencies available

## Deployment Steps

### 1. Install Python Dependencies
```bash
pip install sentence-transformers psycopg2-binary pgvector
```

**Expected Output:**
```
Successfully installed sentence-transformers-X.X.X psycopg2-binary-X.X.X pgvector-X.X.X
```

- [ ] Dependencies installed successfully

### 2. Run Database Migration
```bash
psql -U opsconductor -d opsconductor -f /home/opsconductor/opsconductor-ng/database/migrations/001_add_pgvector_tool_index.sql
```

**Expected Output:**
```
CREATE EXTENSION
CREATE TABLE
CREATE INDEX
...
CREATE VIEW
```

- [ ] Migration completed without errors
- [ ] Verify tables created:
  ```sql
  \dt tool_catalog.tool_index
  \dt tool_catalog.stage_ab_telemetry
  ```

**If HNSW Index Fails:**
```sql
-- Run this manually
CREATE INDEX tool_index_emb_ivf
  ON tool_catalog.tool_index USING ivfflat (emb vector_cosine_ops) WITH (lists = 128);
ANALYZE tool_catalog.tool_index;
```

- [ ] HNSW index created OR IVFFLAT fallback created

### 3. Backfill Tool Index
```bash
cd /home/opsconductor/opsconductor-ng
python scripts/backfill_tool_index.py
```

**Expected Output:**
```
================================================================================
TOOL INDEX BACKFILL
================================================================================
🔧 Initializing services...
📚 Loading tools from database...
   Found 134 tools
🔄 Generating embeddings and preparing entries...
📦 Loading embedding model: BAAI/bge-base-en-v1.5
✅ Embedding model loaded successfully (dim=768)
🔄 Generating embeddings for 134 texts (batch_size=32)
✅ Generated 134 embeddings
💾 Inserting entries into tool_index...
✅ Bulk inserted 134 entries
================================================================================
✅ BACKFILL COMPLETE
   Tools processed: 134
   Entries inserted: 134
================================================================================
```

- [ ] Backfill completed successfully
- [ ] All tools have embeddings
- [ ] Verify data:
  ```sql
  SELECT COUNT(*) FROM tool_catalog.tool_index;
  -- Should return 134 (or your tool count)
  ```

### 4. Restart Services
```bash
# Stop pipeline service
sudo systemctl stop opsconductor-pipeline

# Clear Redis cache
redis-cli FLUSHALL

# Start pipeline service
sudo systemctl start opsconductor-pipeline

# Check status
sudo systemctl status opsconductor-pipeline
```

- [ ] Pipeline service restarted successfully
- [ ] Redis cache cleared
- [ ] Service status shows "active (running)"

### 5. Verify Health
```bash
curl http://localhost:8001/health
```

**Expected Output:**
```json
{
  "status": "healthy",
  "version": "3.0.0",
  ...
}
```

- [ ] Health check passes
- [ ] Version shows 3.0.0

### 6. Test Basic Request
```bash
curl -X POST http://localhost:8001/api/v1/pipeline/process \
  -H "Content-Type: application/json" \
  -d '{"user_request": "get C drive directory for all win10 machines"}'
```

**Expected Behavior:**
- [ ] Request completes without errors
- [ ] Stage AB logs show semantic retrieval
- [ ] Tool selection works correctly
- [ ] No truncation errors

**Check Logs:**
```bash
tail -f /var/log/opsconductor/pipeline.log | grep "Stage AB"
```

Look for:
```
🧠 Stage AB (v3.0): Processing request: get C drive directory...
✅ Generated query embedding (768d)
📊 Token budget: 5400 tokens, max_rows=120
🔍 Retrieved 120 candidates in XXms
🤖 Stage AB: Calling LLM for tool selection...
✅ Stage AB: Parsed response - intent=system/query, tools=2
🔧 TOOLS SELECTED BY LLM:
   1. asset-query - find win10 machines
   2. windows-filesystem-manager - list C:\ directory
✅ VALIDATED TOOLS:
   1. asset-query (order: 1)
   2. windows-filesystem-manager (order: 2)
```

- [ ] Logs show semantic retrieval working
- [ ] Token budget calculated correctly
- [ ] Tools selected and validated

### 7. Check Telemetry
```sql
SELECT 
    request_id,
    user_intent,
    rows_sent,
    headroom_left,
    total_time_ms
FROM tool_catalog.stage_ab_telemetry
ORDER BY created_at DESC
LIMIT 1;
```

**Expected:**
- [ ] Telemetry logged
- [ ] `headroom_left` > 15%
- [ ] `rows_sent` ≤ 120
- [ ] No truncation events

### 8. Check for Alerts
```sql
SELECT * FROM tool_catalog.stage_ab_alerts
ORDER BY created_at DESC
LIMIT 10;
```

- [ ] No critical alerts (or investigate if any)

## Post-Deployment Monitoring

### First Hour
- [ ] Monitor logs for errors
- [ ] Check telemetry every 15 minutes
- [ ] Verify no truncation events
- [ ] Confirm headroom > 15%

### First Day
- [ ] Review telemetry summary:
  ```sql
  SELECT 
      COUNT(*) as requests,
      AVG(headroom_left) as avg_headroom,
      AVG(total_time_ms) as avg_time_ms,
      SUM(truncation_events) as total_truncations
  FROM tool_catalog.stage_ab_telemetry
  WHERE created_at > NOW() - INTERVAL '24 hours';
  ```
- [ ] Investigate any alerts
- [ ] Verify recall metrics (when available)

### First Week
- [ ] Analyze performance trends
- [ ] Tune token budget if needed
- [ ] Adjust top-K values if recall is low
- [ ] Document any issues/improvements

## Rollback Procedure

If critical issues occur:

1. **Restore Old Code:**
   ```bash
   cp /home/opsconductor/opsconductor-ng/pipeline/stages/stage_ab/combined_selector.py.backup \
      /home/opsconductor/opsconductor-ng/pipeline/stages/stage_ab/combined_selector.py
   ```

2. **Restart Service:**
   ```bash
   sudo systemctl restart opsconductor-pipeline
   redis-cli FLUSHALL
   ```

3. **Verify:**
   ```bash
   curl http://localhost:8001/health
   ```

4. **Document Issue:**
   - What went wrong?
   - Error messages?
   - Telemetry data?

- [ ] Rollback procedure tested and documented

## Success Criteria

- [ ] ✅ Zero truncation events
- [ ] ✅ Headroom consistently > 15%
- [ ] ✅ Tool selection accuracy maintained
- [ ] ✅ Performance acceptable (< 2s per request)
- [ ] ✅ No increase in error rate
- [ ] ✅ Telemetry logging working

## Sign-Off

- [ ] Deployment completed by: _______________
- [ ] Date: _______________
- [ ] Issues encountered: _______________
- [ ] Resolution: _______________
- [ ] Approved for production: _______________

---

**Notes:**
- Keep this checklist updated with actual deployment results
- Document any deviations from expected behavior
- Share learnings with the team