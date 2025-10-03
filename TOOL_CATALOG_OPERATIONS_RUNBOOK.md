# Tool Catalog System - Operations Runbook

**Version**: 1.0  
**Last Updated**: 2025-10-03  
**Audience**: Operations Team, SRE, On-Call Engineers

---

## Table of Contents

1. [Quick Reference](#quick-reference)
2. [Common Operations](#common-operations)
3. [Incident Response](#incident-response)
4. [Maintenance Procedures](#maintenance-procedures)
5. [Performance Tuning](#performance-tuning)
6. [Disaster Recovery](#disaster-recovery)

---

## Quick Reference

### Service Information

| Property | Value |
|----------|-------|
| **Service Name** | Tool Catalog |
| **Port** | 3005 |
| **Health Check** | `http://localhost:3005/health` |
| **Metrics** | `http://localhost:3005/metrics` |
| **Logs** | `/var/log/tool-catalog/` or `journalctl -u tool-catalog` |
| **Config** | `/opt/opsconductor/.env` |
| **Database** | PostgreSQL (opsconductor) |

### Emergency Contacts

| Role | Contact | Response Time |
|------|---------|---------------|
| **On-Call Engineer** | PagerDuty | 15 minutes |
| **Platform Team Lead** | Slack: @platform-lead | 30 minutes |
| **Database Admin** | Slack: @dba-team | 1 hour |

### Quick Commands

```bash
# Check service status
sudo systemctl status tool-catalog

# View recent logs
sudo journalctl -u tool-catalog -n 100 -f

# Restart service
sudo systemctl restart tool-catalog

# Check health
curl http://localhost:3005/health

# View metrics
curl http://localhost:3005/api/v1/tools/metrics | jq
```

---

## Common Operations

### 1. Service Management

#### Start Service

```bash
# Using systemd
sudo systemctl start tool-catalog

# Verify startup
sleep 5
curl http://localhost:3005/health

# Expected: {"status": "healthy", "uptime": ...}
```

#### Stop Service

```bash
# Using systemd
sudo systemctl stop tool-catalog

# Verify stopped
ps aux | grep tool-catalog
# Should return no processes
```

#### Restart Service

```bash
# Graceful restart
sudo systemctl restart tool-catalog

# Wait for service to be ready
sleep 10
curl http://localhost:3005/health

# Check for errors
sudo journalctl -u tool-catalog -n 50
```

#### Reload Configuration (without restart)

```bash
# Trigger hot reload via API
curl -X POST http://localhost:3005/api/v1/tools/reload

# Verify reload success
curl http://localhost:3005/api/v1/tools/reload/status | jq

# Expected: {"status": "success", "last_reload": ...}
```

---

### 2. Health Checks

#### Basic Health Check

```bash
# Check service health
curl http://localhost:3005/health

# Expected response:
# {
#   "status": "healthy",
#   "uptime": 3600,
#   "version": "1.0.0",
#   "database": "connected",
#   "cache": "active"
# }
```

#### Detailed Health Check

```bash
# Check all components
curl http://localhost:3005/api/v1/tools/metrics | jq '{
  uptime: .uptime_seconds,
  tools_loaded: .tools_loaded_total,
  cache_hit_rate: .cache_hit_rate,
  db_query_time_avg: .db_query_time_avg_ms,
  error_rate: .error_rate
}'

# Verify all metrics are healthy:
# - uptime > 0
# - tools_loaded > 200
# - cache_hit_rate > 0.80
# - db_query_time_avg < 10
# - error_rate < 0.01
```

#### Database Health Check

```bash
# Check database connectivity
psql -d opsconductor -c "SELECT 1;"

# Check connection pool
psql -d opsconductor -c "
  SELECT count(*) as active_connections 
  FROM pg_stat_activity 
  WHERE datname='opsconductor';
"

# Expected: 5-20 connections

# Check for long-running queries
psql -d opsconductor -c "
  SELECT pid, now() - query_start as duration, query 
  FROM pg_stat_activity 
  WHERE state = 'active' AND now() - query_start > interval '1 minute';
"

# Expected: No results (no queries running >1 minute)
```

---

### 3. Monitoring and Metrics

#### View Current Metrics

```bash
# Get all metrics (JSON format)
curl http://localhost:3005/api/v1/tools/metrics | jq

# Get specific metrics
curl http://localhost:3005/api/v1/tools/metrics | jq '{
  cache_hit_rate,
  db_query_time_p95_ms,
  tools_loaded_total,
  error_rate
}'
```

#### View Performance Statistics

```bash
# Get performance stats
curl http://localhost:3005/api/v1/tools/performance/stats | jq

# Key metrics to monitor:
# - cache_hit_rate: Should be >80%
# - db_query_time_p95: Should be <50ms
# - connection_pool.available: Should be >0
# - cache_size: Should be <1000
```

#### Check Prometheus Metrics

```bash
# Get Prometheus format metrics
curl http://localhost:3005/metrics

# Check specific metric
curl http://localhost:3005/metrics | grep tool_catalog_cache_hit_rate
```

---

### 4. Log Management

#### View Recent Logs

```bash
# Last 100 lines
sudo journalctl -u tool-catalog -n 100

# Follow logs in real-time
sudo journalctl -u tool-catalog -f

# Filter by log level
sudo journalctl -u tool-catalog | grep ERROR

# Filter by time range
sudo journalctl -u tool-catalog --since "1 hour ago"
```

#### Search Logs for Errors

```bash
# Find all errors in last hour
sudo journalctl -u tool-catalog --since "1 hour ago" | grep -i error

# Find database errors
sudo journalctl -u tool-catalog | grep -i "database error"

# Find timeout errors
sudo journalctl -u tool-catalog | grep -i timeout

# Count errors by type
sudo journalctl -u tool-catalog | grep ERROR | awk '{print $NF}' | sort | uniq -c | sort -rn
```

#### Export Logs for Analysis

```bash
# Export last 24 hours to file
sudo journalctl -u tool-catalog --since "24 hours ago" > tool-catalog-logs-$(date +%Y%m%d).log

# Export errors only
sudo journalctl -u tool-catalog | grep ERROR > tool-catalog-errors-$(date +%Y%m%d).log
```

---

### 5. Tool Management

#### List All Tools

```bash
# Get all tools
curl http://localhost:3005/api/v1/tools | jq '.[] | {tool_name, version, enabled}'

# Count tools
curl http://localhost:3005/api/v1/tools | jq 'length'

# Expected: 200+
```

#### Get Tool Details

```bash
# Get specific tool
curl http://localhost:3005/api/v1/tools/name/ExecuteShellCommand | jq

# Get tool with version
curl http://localhost:3005/api/v1/tools/name/ExecuteShellCommand?version=1.0.0 | jq
```

#### Search Tools

```bash
# Search by name
curl "http://localhost:3005/api/v1/tools/search?name=shell" | jq

# Search enabled tools only
curl "http://localhost:3005/api/v1/tools/search?enabled=true" | jq

# Search by capability
curl "http://localhost:3005/api/v1/tools/search?capability=file_operations" | jq
```

#### Update Tool

```bash
# Update tool via API
curl -X PUT http://localhost:3005/api/v1/tools/123 \
  -H "Content-Type: application/json" \
  -d '{
    "enabled": false,
    "description": "Updated description"
  }'

# Verify update
curl http://localhost:3005/api/v1/tools/123 | jq
```

---

### 6. Cache Management

#### View Cache Statistics

```bash
# Get cache stats
curl http://localhost:3005/api/v1/tools/performance/stats | jq '.cache'

# Expected output:
# {
#   "size": 150,
#   "max_size": 1000,
#   "hit_rate": 0.9778,
#   "hits": 1234,
#   "misses": 28
# }
```

#### Clear Cache

```bash
# Clear cache via hot reload
curl -X POST http://localhost:3005/api/v1/tools/reload

# Verify cache cleared
curl http://localhost:3005/api/v1/tools/performance/stats | jq '.cache.size'

# Expected: 0 or small number
```

#### Warm Up Cache

```bash
# Load all tools to warm cache
curl http://localhost:3005/api/v1/tools > /dev/null

# Verify cache populated
curl http://localhost:3005/api/v1/tools/performance/stats | jq '.cache.size'

# Expected: >100
```

---

## Incident Response

### Incident: Service Down

**Severity**: P1 (Critical)  
**Response Time**: 15 minutes

#### Symptoms
- Health check returns 503 or times out
- Prometheus shows `up{job="tool-catalog"} == 0`
- Alert: `ToolCatalogServiceDown`

#### Diagnosis

```bash
# 1. Check if service is running
sudo systemctl status tool-catalog

# 2. Check recent logs
sudo journalctl -u tool-catalog -n 100

# 3. Check port availability
sudo netstat -tulpn | grep 3005

# 4. Check database connectivity
psql -d opsconductor -c "SELECT 1;"
```

#### Resolution

**Option 1: Service crashed**
```bash
# Restart service
sudo systemctl restart tool-catalog

# Wait for startup
sleep 10

# Verify health
curl http://localhost:3005/health
```

**Option 2: Port conflict**
```bash
# Find process using port
sudo lsof -i :3005

# Kill conflicting process
sudo kill -9 <PID>

# Start service
sudo systemctl start tool-catalog
```

**Option 3: Database connection failed**
```bash
# Check database status
sudo systemctl status postgresql

# Restart database if needed
sudo systemctl restart postgresql

# Restart service
sudo systemctl restart tool-catalog
```

#### Post-Incident

```bash
# 1. Verify service health
curl http://localhost:3005/health

# 2. Check metrics
curl http://localhost:3005/api/v1/tools/metrics | jq

# 3. Monitor for 15 minutes
watch -n 30 'curl -s http://localhost:3005/health | jq'

# 4. Document incident
# - Root cause
# - Resolution steps
# - Prevention measures
```

---

### Incident: High Response Time

**Severity**: P2 (High)  
**Response Time**: 30 minutes

#### Symptoms
- P95 response time >50ms
- Alert: `ToolCatalogHighResponseTime`
- Users reporting slow API responses

#### Diagnosis

```bash
# 1. Check current response times
curl http://localhost:3005/api/v1/tools/performance/stats | jq '{
  db_query_time_p95,
  cache_hit_rate,
  connection_pool
}'

# 2. Check database performance
psql -d opsconductor -c "
  SELECT query, mean_exec_time, calls 
  FROM pg_stat_statements 
  WHERE query LIKE '%tools%' 
  ORDER BY mean_exec_time DESC 
  LIMIT 10;
"

# 3. Check for slow queries
psql -d opsconductor -c "
  SELECT pid, now() - query_start as duration, query 
  FROM pg_stat_activity 
  WHERE state = 'active' 
  ORDER BY duration DESC;
"

# 4. Check cache effectiveness
curl http://localhost:3005/api/v1/tools/performance/stats | jq '.cache.hit_rate'
```

#### Resolution

**Option 1: Low cache hit rate**
```bash
# Increase cache size
# Edit .env file
sudo nano /opt/opsconductor/.env

# Change:
CACHE_MAX_SIZE=2000  # Increase from 1000

# Restart service
sudo systemctl restart tool-catalog
```

**Option 2: Slow database queries**
```bash
# Run ANALYZE on tables
psql -d opsconductor -c "ANALYZE tools;"
psql -d opsconductor -c "ANALYZE capabilities;"
psql -d opsconductor -c "ANALYZE patterns;"

# Check if indexes are being used
psql -d opsconductor -c "
  SELECT schemaname, tablename, indexname, idx_scan 
  FROM pg_stat_user_indexes 
  WHERE schemaname = 'public';
"
```

**Option 3: Connection pool exhausted**
```bash
# Increase connection pool size
# Edit .env file
sudo nano /opt/opsconductor/.env

# Change:
DB_POOL_MAX_SIZE=30  # Increase from 20

# Restart service
sudo systemctl restart tool-catalog
```

#### Post-Incident

```bash
# 1. Verify response times improved
curl http://localhost:3005/api/v1/tools/performance/stats | jq '.db_query_time_p95'

# Expected: <50ms

# 2. Run load test
bash scripts/simple_load_test.sh 2 60

# 3. Monitor for 1 hour
watch -n 60 'curl -s http://localhost:3005/api/v1/tools/performance/stats | jq .db_query_time_p95'
```

---

### Incident: High Error Rate

**Severity**: P2 (High)  
**Response Time**: 30 minutes

#### Symptoms
- Error rate >1%
- Alert: `ToolCatalogHighErrorRate`
- Errors in logs

#### Diagnosis

```bash
# 1. Check error rate
curl http://localhost:3005/api/v1/tools/metrics | jq '.error_rate'

# 2. Check error logs
sudo journalctl -u tool-catalog | grep ERROR | tail -50

# 3. Check error types
sudo journalctl -u tool-catalog | grep ERROR | awk '{print $NF}' | sort | uniq -c | sort -rn

# 4. Check database errors
psql -d opsconductor -c "
  SELECT datname, numbackends, xact_commit, xact_rollback 
  FROM pg_stat_database 
  WHERE datname='opsconductor';
"
```

#### Resolution

**Option 1: Database connection errors**
```bash
# Check connection pool
curl http://localhost:3005/api/v1/tools/performance/stats | jq '.connection_pool'

# If available == 0, increase pool size
sudo nano /opt/opsconductor/.env
# DB_POOL_MAX_SIZE=30

sudo systemctl restart tool-catalog
```

**Option 2: Timeout errors**
```bash
# Increase timeout
sudo nano /opt/opsconductor/.env
# DB_POOL_TIMEOUT=60  # Increase from 30

sudo systemctl restart tool-catalog
```

**Option 3: Application errors**
```bash
# Check for specific error patterns
sudo journalctl -u tool-catalog | grep ERROR | grep -i "traceback" -A 10

# If code issue, rollback to previous version
git checkout <previous-commit>
sudo systemctl restart tool-catalog
```

#### Post-Incident

```bash
# 1. Verify error rate decreased
curl http://localhost:3005/api/v1/tools/metrics | jq '.error_rate'

# Expected: <0.01

# 2. Monitor errors
watch -n 60 'curl -s http://localhost:3005/api/v1/tools/metrics | jq .error_rate'

# 3. Review error logs
sudo journalctl -u tool-catalog --since "1 hour ago" | grep ERROR
```

---

### Incident: Cache Not Working

**Severity**: P3 (Medium)  
**Response Time**: 1 hour

#### Symptoms
- Cache hit rate <50%
- Alert: `ToolCatalogLowCacheHitRate`
- High database query rate

#### Diagnosis

```bash
# 1. Check cache statistics
curl http://localhost:3005/api/v1/tools/performance/stats | jq '.cache'

# 2. Check cache configuration
grep CACHE /opt/opsconductor/.env

# 3. Check if cache is enabled
curl http://localhost:3005/api/v1/tools/metrics | jq '.cache_enabled'
```

#### Resolution

**Option 1: Cache disabled**
```bash
# Enable cache
sudo nano /opt/opsconductor/.env
# CACHE_ENABLED=true

sudo systemctl restart tool-catalog
```

**Option 2: Cache too small**
```bash
# Increase cache size
sudo nano /opt/opsconductor/.env
# CACHE_MAX_SIZE=2000

sudo systemctl restart tool-catalog
```

**Option 3: Cache TTL too short**
```bash
# Increase TTL
sudo nano /opt/opsconductor/.env
# CACHE_TTL_SECONDS=600  # 10 minutes

sudo systemctl restart tool-catalog
```

#### Post-Incident

```bash
# 1. Warm up cache
curl http://localhost:3005/api/v1/tools > /dev/null

# 2. Verify cache hit rate
sleep 60
curl http://localhost:3005/api/v1/tools/performance/stats | jq '.cache.hit_rate'

# Expected: >0.80

# 3. Monitor for 1 hour
watch -n 300 'curl -s http://localhost:3005/api/v1/tools/performance/stats | jq .cache.hit_rate'
```

---

## Maintenance Procedures

### 1. Routine Maintenance

#### Daily Tasks

```bash
# Check service health
curl http://localhost:3005/health

# Check error logs
sudo journalctl -u tool-catalog --since "24 hours ago" | grep ERROR | wc -l

# Expected: <10 errors per day

# Check disk space
df -h /var/log

# Expected: <80% usage
```

#### Weekly Tasks

```bash
# 1. Review performance metrics
curl http://localhost:3005/api/v1/tools/performance/stats | jq

# 2. Check database statistics
psql -d opsconductor -c "
  SELECT schemaname, tablename, n_live_tup, n_dead_tup 
  FROM pg_stat_user_tables;
"

# 3. Vacuum database if needed
psql -d opsconductor -c "VACUUM ANALYZE;"

# 4. Rotate logs
sudo journalctl --vacuum-time=30d

# 5. Review alerts
# Check Prometheus/Grafana for any alerts in past week
```

#### Monthly Tasks

```bash
# 1. Review capacity planning
curl http://localhost:3005/api/v1/tools/performance/stats | jq '{
  cache_size,
  connection_pool,
  tools_loaded_total
}'

# 2. Update dependencies
pip list --outdated

# 3. Review and update documentation

# 4. Backup database
pg_dump opsconductor > backup_$(date +%Y%m%d).sql

# 5. Test disaster recovery procedures
```

---

### 2. Database Maintenance

#### Vacuum Database

```bash
# Analyze tables
psql -d opsconductor -c "ANALYZE;"

# Vacuum tables
psql -d opsconductor -c "VACUUM;"

# Full vacuum (requires downtime)
sudo systemctl stop tool-catalog
psql -d opsconductor -c "VACUUM FULL;"
sudo systemctl start tool-catalog
```

#### Reindex Database

```bash
# Reindex all tables
psql -d opsconductor -c "REINDEX DATABASE opsconductor;"

# Reindex specific table
psql -d opsconductor -c "REINDEX TABLE tools;"
```

#### Update Statistics

```bash
# Update query planner statistics
psql -d opsconductor -c "ANALYZE tools;"
psql -d opsconductor -c "ANALYZE capabilities;"
psql -d opsconductor -c "ANALYZE patterns;"
```

---

### 3. Backup and Restore

#### Create Backup

```bash
# Full database backup
pg_dump opsconductor > backup_$(date +%Y%m%d_%H%M%S).sql

# Compressed backup
pg_dump opsconductor | gzip > backup_$(date +%Y%m%d_%H%M%S).sql.gz

# Backup specific tables
pg_dump -t tools -t capabilities -t patterns opsconductor > backup_tables_$(date +%Y%m%d).sql

# Verify backup
ls -lh backup_*.sql*
```

#### Restore from Backup

```bash
# Stop service
sudo systemctl stop tool-catalog

# Drop and recreate database
dropdb opsconductor
createdb opsconductor

# Restore from backup
psql -d opsconductor < backup_YYYYMMDD_HHMMSS.sql

# Or from compressed backup
gunzip -c backup_YYYYMMDD_HHMMSS.sql.gz | psql -d opsconductor

# Start service
sudo systemctl start tool-catalog

# Verify restoration
curl http://localhost:3005/api/v1/tools | jq 'length'
```

---

### 4. Configuration Updates

#### Update Environment Variables

```bash
# 1. Backup current configuration
cp /opt/opsconductor/.env /opt/opsconductor/.env.backup_$(date +%Y%m%d)

# 2. Edit configuration
sudo nano /opt/opsconductor/.env

# 3. Validate configuration
grep -v '^#' /opt/opsconductor/.env | grep -v '^$'

# 4. Restart service
sudo systemctl restart tool-catalog

# 5. Verify changes
curl http://localhost:3005/health
```

#### Update Database Connection

```bash
# 1. Test new connection string
psql "postgresql://newuser:newpass@newhost:5432/opsconductor" -c "SELECT 1;"

# 2. Update .env
sudo nano /opt/opsconductor/.env
# DATABASE_URL=postgresql://newuser:newpass@newhost:5432/opsconductor

# 3. Restart service
sudo systemctl restart tool-catalog

# 4. Verify connectivity
curl http://localhost:3005/health
```

---

## Performance Tuning

### 1. Cache Optimization

#### Increase Cache Size

```bash
# Current cache size
curl http://localhost:3005/api/v1/tools/performance/stats | jq '.cache.size'

# If cache is frequently full (size == max_size), increase it
sudo nano /opt/opsconductor/.env
# CACHE_MAX_SIZE=2000  # Increase from 1000

sudo systemctl restart tool-catalog

# Monitor cache hit rate
watch -n 60 'curl -s http://localhost:3005/api/v1/tools/performance/stats | jq .cache.hit_rate'
```

#### Adjust Cache TTL

```bash
# Increase TTL for more stable cache
sudo nano /opt/opsconductor/.env
# CACHE_TTL_SECONDS=600  # 10 minutes (from 5 minutes)

sudo systemctl restart tool-catalog
```

---

### 2. Database Optimization

#### Increase Connection Pool

```bash
# Check current pool usage
curl http://localhost:3005/api/v1/tools/performance/stats | jq '.connection_pool'

# If frequently exhausted (available == 0), increase pool
sudo nano /opt/opsconductor/.env
# DB_POOL_MAX_SIZE=30  # Increase from 20

sudo systemctl restart tool-catalog
```

#### Optimize Query Performance

```bash
# Identify slow queries
psql -d opsconductor -c "
  SELECT query, mean_exec_time, calls 
  FROM pg_stat_statements 
  WHERE query LIKE '%tools%' 
  ORDER BY mean_exec_time DESC 
  LIMIT 10;
"

# Add missing indexes if needed
psql -d opsconductor -c "
  CREATE INDEX IF NOT EXISTS idx_tools_custom 
  ON tools(column_name);
"

# Update statistics
psql -d opsconductor -c "ANALYZE tools;"
```

---

### 3. API Performance

#### Increase Worker Processes

```bash
# For high traffic, increase workers
sudo nano /opt/opsconductor/.env
# API_WORKERS=8  # Increase from 4

sudo systemctl restart tool-catalog

# Monitor CPU usage
top -p $(pgrep -f tool-catalog)
```

#### Enable Compression

```bash
# Enable gzip compression for API responses
sudo nano /opt/opsconductor/.env
# API_COMPRESSION=true

sudo systemctl restart tool-catalog
```

---

## Disaster Recovery

### Scenario 1: Complete Service Failure

**Recovery Time Objective (RTO)**: 30 minutes  
**Recovery Point Objective (RPO)**: 24 hours

#### Steps

```bash
# 1. Restore from backup
dropdb opsconductor
createdb opsconductor
psql -d opsconductor < /backups/latest_backup.sql

# 2. Restore configuration
cp /opt/opsconductor/.env.backup /opt/opsconductor/.env

# 3. Restore code
cd /opt/opsconductor
git checkout main
git pull origin main

# 4. Install dependencies
pip install -r requirements.txt

# 5. Start service
sudo systemctl start tool-catalog

# 6. Verify health
curl http://localhost:3005/health

# 7. Warm up cache
curl http://localhost:3005/api/v1/tools > /dev/null

# 8. Monitor for 1 hour
watch -n 60 'curl -s http://localhost:3005/health | jq'
```

---

### Scenario 2: Database Corruption

**RTO**: 1 hour  
**RPO**: 24 hours

#### Steps

```bash
# 1. Stop service
sudo systemctl stop tool-catalog

# 2. Backup corrupted database
pg_dump opsconductor > corrupted_backup_$(date +%Y%m%d).sql

# 3. Drop corrupted database
dropdb opsconductor

# 4. Recreate database
createdb opsconductor

# 5. Restore from last good backup
psql -d opsconductor < /backups/last_good_backup.sql

# 6. Verify data integrity
psql -d opsconductor -c "SELECT COUNT(*) FROM tools;"
# Expected: 200+

# 7. Rebuild indexes
psql -d opsconductor -c "REINDEX DATABASE opsconductor;"

# 8. Update statistics
psql -d opsconductor -c "ANALYZE;"

# 9. Start service
sudo systemctl start tool-catalog

# 10. Verify health
curl http://localhost:3005/health
```

---

### Scenario 3: Data Center Failover

**RTO**: 2 hours  
**RPO**: 1 hour

#### Steps

```bash
# 1. Promote standby database to primary
# (Database-specific procedure)

# 2. Update database connection string
sudo nano /opt/opsconductor/.env
# DATABASE_URL=postgresql://user:pass@new-primary:5432/opsconductor

# 3. Deploy service to new data center
# (Follow deployment guide)

# 4. Update DNS/load balancer
# Point tool-catalog.example.com to new IP

# 5. Verify health
curl http://new-ip:3005/health

# 6. Monitor for 2 hours
watch -n 300 'curl -s http://new-ip:3005/health | jq'
```

---

## Appendix

### A. Useful SQL Queries

```sql
-- Count tools by status
SELECT enabled, COUNT(*) 
FROM tools 
GROUP BY enabled;

-- Find tools with no capabilities
SELECT t.tool_name 
FROM tools t 
LEFT JOIN capabilities c ON t.id = c.tool_id 
WHERE c.id IS NULL;

-- Find most used tools (requires usage tracking)
SELECT tool_name, usage_count 
FROM tools 
ORDER BY usage_count DESC 
LIMIT 10;

-- Check database size
SELECT pg_size_pretty(pg_database_size('opsconductor'));

-- Check table sizes
SELECT 
  schemaname, 
  tablename, 
  pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) AS size
FROM pg_tables 
WHERE schemaname = 'public' 
ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC;
```

### B. Performance Baselines

| Metric | Baseline | Warning | Critical |
|--------|----------|---------|----------|
| P95 Response Time | <10ms | >50ms | >100ms |
| P99 Response Time | <20ms | >100ms | >200ms |
| Error Rate | <0.1% | >1% | >5% |
| Cache Hit Rate | >95% | <80% | <50% |
| DB Query Time (P95) | <5ms | >50ms | >100ms |
| Connection Pool Available | >10 | <5 | 0 |
| CPU Usage | <10% | >60% | >80% |
| Memory Usage | <30% | >70% | >90% |

### C. Escalation Matrix

| Severity | Response Time | Escalation Path |
|----------|---------------|-----------------|
| P1 (Critical) | 15 minutes | On-Call → Team Lead → VP Engineering |
| P2 (High) | 30 minutes | On-Call → Team Lead |
| P3 (Medium) | 1 hour | On-Call |
| P4 (Low) | 4 hours | Team backlog |

---

**End of Operations Runbook**