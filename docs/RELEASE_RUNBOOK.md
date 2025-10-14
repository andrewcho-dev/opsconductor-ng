# OpsConductor Release Runbook

## Walking Skeleton v1.1.0 - Production Deployment Guide

This runbook provides step-by-step instructions for deploying the OpsConductor walking skeleton to production using a canary rollout strategy.

---

## Table of Contents

1. [Pre-Deployment Checklist](#pre-deployment-checklist)
2. [Canary Deployment](#canary-deployment)
3. [Verification & Monitoring](#verification--monitoring)
4. [Promotion to Production](#promotion-to-production)
5. [Rollback Procedures](#rollback-procedures)
6. [Post-Deployment](#post-deployment)
7. [Troubleshooting](#troubleshooting)

---

## Pre-Deployment Checklist

### 1. Environment Preparation

- [ ] **Staging environment is healthy**
  ```bash
  ./scripts/release_smoke.sh staging
  ```

- [ ] **All containers are running**
  ```bash
  docker compose ps
  # Expected: 13 containers (all healthy)
  ```

- [ ] **Database migrations applied**
  ```bash
  docker compose exec postgres psql -U opsconductor -d opsconductor -c "\dt"
  # Verify all tables exist
  ```

- [ ] **Monitoring stack operational**
  ```bash
  curl http://localhost:9090/-/healthy  # Prometheus
  curl http://localhost:3200/api/health # Grafana
  ```

### 2. Version Verification

- [ ] **Verify version bumps**
  ```bash
  # automation-service: 3.0.1
  grep "__version__" automation-service/__init__.py
  
  # ai-pipeline: 1.1.0
  grep "__version__" pipeline/__init__.py
  
  # frontend: 1.1.0
  grep "version" frontend/package.json
  ```

- [ ] **Git tags created**
  ```bash
  git tag -a v1.1.0-automation-service -m "Release automation-service 3.0.1"
  git tag -a v1.1.0-ai-pipeline -m "Release ai-pipeline 1.1.0"
  git tag -a v1.1.0-frontend -m "Release frontend 1.1.0"
  git tag -a v1.1.0-walking-skeleton -m "Release walking skeleton v1.1.0"
  ```

### 3. Backup Current State

- [ ] **Backup database**
  ```bash
  docker compose exec postgres pg_dump -U opsconductor opsconductor > backup_$(date +%Y%m%d_%H%M%S).sql
  ```

- [ ] **Tag current production state**
  ```bash
  git tag -a pre-v1.1.0-rollback -m "Pre-v1.1.0 rollback point"
  git push origin pre-v1.1.0-rollback
  ```

- [ ] **Document current container versions**
  ```bash
  docker compose images > container_versions_$(date +%Y%m%d_%H%M%S).txt
  ```

---

## Canary Deployment

### Phase 1: Deploy Canary Instance (10% Traffic)

#### 1.1 Create Canary Configuration

Create `docker-compose.canary.yml`:

```yaml
services:
  automation-service-canary:
    build:
      context: .
      dockerfile: automation-service/Dockerfile.clean
    container_name: opsconductor-automation-canary
    environment:
      - FEATURE_BYPASS_LLM=true  # Enable echo tool bypass
      - CANARY_INSTANCE=true
      - SERVICE_VERSION=3.0.1
    ports:
      - "3013:3003"  # Different port for canary
    networks:
      - opsconductor
    depends_on:
      - postgres
      - redis
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:3003/health"]
      interval: 10s
      timeout: 5s
      retries: 3

  ai-pipeline-canary:
    build:
      context: .
      dockerfile: Dockerfile
    container_name: opsconductor-ai-pipeline-canary
    environment:
      - FEATURE_BYPASS_LLM=true  # Enable echo tool bypass
      - CANARY_INSTANCE=true
      - PIPELINE_VERSION=1.1.0
    ports:
      - "8011:8001"  # Different port for canary
    networks:
      - opsconductor
    depends_on:
      - postgres
      - redis
      - vllm
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8001/health"]
      interval: 10s
      timeout: 5s
      retries: 3
```

#### 1.2 Deploy Canary

```bash
# Build and start canary instances
docker compose -f docker-compose.yml -f docker-compose.canary.yml up -d automation-service-canary ai-pipeline-canary

# Wait for health checks
sleep 30

# Verify canary health
curl http://localhost:3013/health
curl http://localhost:8011/health
```

#### 1.3 Configure Traffic Split (Kong)

Update `kong/kong.yml` to route 10% traffic to canary:

```yaml
services:
  - name: automation-service
    url: http://automation-service:3003
    routes:
      - name: automation-route
        paths:
          - /ai
    plugins:
      - name: request-transformer
        config:
          add:
            headers:
              - X-Canary-Weight:90

  - name: automation-service-canary
    url: http://automation-service-canary:3003
    routes:
      - name: automation-canary-route
        paths:
          - /ai
    plugins:
      - name: request-transformer
        config:
          add:
            headers:
              - X-Canary-Weight:10
```

Reload Kong configuration:

```bash
docker compose restart kong
```

---

## Verification & Monitoring

### Phase 2: Canary Burn-In (30 minutes)

#### 2.1 Run Smoke Tests

```bash
# Test canary directly
./scripts/release_smoke.sh local

# Test via Kong (mixed traffic)
for i in {1..100}; do
  curl -X POST http://localhost:3000/ai/execute \
    -H "Content-Type: application/json" \
    -d '{"input":"ping","tool":"echo"}' \
    -w "\n"
  sleep 1
done
```

#### 2.2 Monitor Metrics

**Open Grafana Dashboard:**
```
http://localhost:3200/d/execution/execution-dashboard
```

**Key Metrics to Watch:**

1. **Error Rate** (must be < 1%)
   ```promql
   rate(ai_request_errors_total{instance="canary"}[5m]) / 
   rate(ai_requests_total{instance="canary"}[5m])
   ```

2. **P95 Latency** (must be < 1000ms)
   ```promql
   histogram_quantile(0.95, 
     rate(ai_request_duration_seconds_bucket{instance="canary"}[5m])
   )
   ```

3. **P99 Latency** (must be < 2000ms)
   ```promql
   histogram_quantile(0.99, 
     rate(ai_request_duration_seconds_bucket{instance="canary"}[5m])
   )
   ```

4. **Request Rate**
   ```promql
   rate(ai_requests_total{instance="canary"}[1m])
   ```

#### 2.3 Run Metrics Gate

```bash
# Monitor for 5 minutes
./scripts/release_metrics_gate.sh local 5

# If passed, continue to 10 minutes
./scripts/release_metrics_gate.sh local 10
```

**Expected Output:**
```
✓ All SLO checks passed!
🎉 METRICS GATE PASSED - READY FOR PROMOTION 🎉
```

#### 2.4 Verify Trace Propagation

```bash
# Send request with trace ID
TRACE_ID="manual-test-$(date +%s)"
curl -X POST http://localhost:3000/ai/execute \
  -H "Content-Type: application/json" \
  -H "X-Trace-Id: $TRACE_ID" \
  -d '{"input":"ping","tool":"echo"}' | jq

# Verify trace_id in response
# Expected: "trace_id": "$TRACE_ID"
```

#### 2.5 Check Logs

```bash
# Canary logs
docker compose logs -f automation-service-canary | grep -i error
docker compose logs -f ai-pipeline-canary | grep -i error

# No critical errors should appear
```

---

## Promotion to Production

### Phase 3: Gradual Rollout

#### 3.1 Increase Canary Traffic to 50%

Update Kong configuration:
```yaml
# automation-service: 50%
# automation-service-canary: 50%
```

```bash
docker compose restart kong
./scripts/release_metrics_gate.sh local 10
```

#### 3.2 Increase Canary Traffic to 100%

Update Kong configuration:
```yaml
# automation-service: 0%
# automation-service-canary: 100%
```

```bash
docker compose restart kong
./scripts/release_metrics_gate.sh local 10
```

#### 3.3 Promote Canary to Production

```bash
# Stop old instances
docker compose stop automation-service ai-pipeline

# Rename canary to production
docker rename opsconductor-automation-canary opsconductor-automation-service
docker rename opsconductor-ai-pipeline-canary opsconductor-ai-pipeline

# Update docker-compose.yml to use new versions
# Remove canary configuration

# Restart with new configuration
docker compose up -d

# Verify all services healthy
docker compose ps
```

#### 3.4 Final Verification

```bash
# Run full smoke test suite
./scripts/release_smoke.sh local

# Run frontend checks
./scripts/release_frontend_check.sh local

# Run metrics gate (30 minutes)
./scripts/release_metrics_gate.sh local 30
```

---

## Rollback Procedures

### Emergency Rollback (< 5 minutes)

#### Option 1: Disable Feature Flag

```bash
# Disable echo tool bypass
docker compose exec automation-service sh -c 'export FEATURE_BYPASS_LLM=false'
docker compose restart automation-service

# Verify
curl http://localhost:3003/health
```

#### Option 2: Route Traffic to Old Version

```bash
# Update Kong to route 100% to old version
# Edit kong/kong.yml
docker compose restart kong
```

#### Option 3: Full Rollback

```bash
# Stop all services
docker compose down

# Checkout previous version
git checkout pre-v1.1.0-rollback

# Rebuild and restart
docker compose build --no-cache
docker compose up -d

# Verify
./scripts/release_smoke.sh local
```

### Rollback Verification

```bash
# Check all services healthy
docker compose ps

# Run smoke tests
./scripts/release_smoke.sh local

# Verify metrics
curl http://localhost:3003/metrics | grep ai_requests_total

# Check Grafana dashboards
open http://localhost:3200
```

---

## Post-Deployment

### Phase 4: Monitoring & Validation (24 hours)

#### 4.1 Continuous Monitoring

**Set up alerts in Prometheus:**

```yaml
# prometheus/opsconductor.rules.yml
groups:
  - name: walking_skeleton_alerts
    interval: 1m
    rules:
      - alert: HighErrorRate
        expr: rate(ai_request_errors_total[5m]) / rate(ai_requests_total[5m]) > 0.01
        for: 5m
        labels:
          severity: critical
        annotations:
          summary: "High error rate detected"
          
      - alert: HighLatency
        expr: histogram_quantile(0.95, rate(ai_request_duration_seconds_bucket[5m])) > 1.0
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "High P95 latency detected"
```

#### 4.2 Daily Health Checks

```bash
# Run daily smoke tests
0 8 * * * /path/to/scripts/release_smoke.sh production

# Run daily metrics gate
0 9 * * * /path/to/scripts/release_metrics_gate.sh production 10
```

#### 4.3 Performance Baseline

Collect baseline metrics for future comparisons:

```bash
# Export metrics
curl http://localhost:9090/api/v1/query?query=ai_requests_total > baseline_metrics.json

# Document in release notes
echo "Baseline established: $(date)" >> docs/RELEASE_NOTES_v1.1.0.md
```

#### 4.4 User Acceptance Testing

- [ ] Frontend Exec Sandbox accessible
- [ ] Ping→pong execution works
- [ ] Trace IDs propagate correctly
- [ ] Metrics visible in Grafana
- [ ] No critical errors in logs

---

## Troubleshooting

### Common Issues

#### Issue 1: Canary Health Check Fails

**Symptoms:**
```
curl http://localhost:3013/health
# Returns 503 or timeout
```

**Resolution:**
```bash
# Check container logs
docker compose logs automation-service-canary

# Check dependencies
docker compose ps postgres redis

# Restart canary
docker compose restart automation-service-canary
```

#### Issue 2: High Error Rate

**Symptoms:**
```
Error rate > 1% in Grafana
```

**Resolution:**
```bash
# Check error logs
docker compose logs automation-service | grep ERROR

# Check AI pipeline
docker compose logs ai-pipeline | grep ERROR

# Verify LLM service
curl http://localhost:8000/health

# Rollback if persistent
# See "Emergency Rollback" section
```

#### Issue 3: High Latency

**Symptoms:**
```
P95 latency > 1000ms
```

**Resolution:**
```bash
# Check resource usage
docker stats

# Check database connections
docker compose exec postgres psql -U opsconductor -c "SELECT count(*) FROM pg_stat_activity;"

# Check Redis
docker compose exec redis redis-cli INFO stats

# Scale if needed
docker compose up -d --scale automation-service=2
```

#### Issue 4: Metrics Not Appearing

**Symptoms:**
```
Grafana dashboards show no data
```

**Resolution:**
```bash
# Check Prometheus targets
curl http://localhost:9090/api/v1/targets | jq

# Verify metrics endpoints
curl http://localhost:3003/metrics | grep ai_requests_total

# Check Prometheus scrape config
docker compose exec prometheus cat /etc/prometheus/prometheus.yml

# Restart Prometheus
docker compose restart prometheus
```

#### Issue 5: Frontend Not Loading

**Symptoms:**
```
http://localhost:3100 returns 502 or blank page
```

**Resolution:**
```bash
# Check frontend container
docker compose logs frontend

# Check build errors
docker compose exec frontend npm run build

# Verify static files
docker compose exec frontend ls -la /app/build

# Restart frontend
docker compose restart frontend
```

---

## Contact & Escalation

### On-Call Contacts

- **Primary:** DevOps Team - devops@opsconductor.local
- **Secondary:** Platform Engineering - platform@opsconductor.local
- **Escalation:** CTO - cto@opsconductor.local

### Incident Response

1. **Severity 1 (Critical):** Error rate > 5% or complete outage
   - Immediate rollback
   - Page on-call engineer
   - Create incident ticket

2. **Severity 2 (High):** Error rate 1-5% or degraded performance
   - Investigate within 15 minutes
   - Consider rollback if not resolved in 30 minutes
   - Create incident ticket

3. **Severity 3 (Medium):** Minor issues, no user impact
   - Investigate within 1 hour
   - Document in release notes
   - Create bug ticket

---

## Appendix

### A. Environment Variables

```bash
# Feature Flags
FEATURE_BYPASS_LLM=true          # Enable echo tool bypass
CANARY_INSTANCE=true             # Mark as canary instance

# Monitoring
ENABLE_METRICS=true              # Enable Prometheus metrics
METRICS_PORT=9091                # Metrics endpoint port

# Service URLs
AI_PIPELINE_BASE_URL=http://ai-pipeline:8001
AUTOMATION_SERVICE_URL=http://automation-service:3003
```

### B. Useful Commands

```bash
# View all container logs
docker compose logs -f

# Check container resource usage
docker stats

# Restart specific service
docker compose restart <service-name>

# View Prometheus targets
curl http://localhost:9090/api/v1/targets | jq

# Query Prometheus
curl -G http://localhost:9090/api/v1/query \
  --data-urlencode 'query=ai_requests_total'

# Export Grafana dashboard
curl http://localhost:3200/api/dashboards/uid/execution \
  -H "Authorization: Bearer <token>"
```

### C. Release Checklist Summary

- [ ] Pre-deployment checks complete
- [ ] Canary deployed and healthy
- [ ] Smoke tests passed
- [ ] Metrics gate passed (30 min)
- [ ] Traffic gradually increased
- [ ] Full promotion complete
- [ ] Post-deployment monitoring active
- [ ] Documentation updated
- [ ] Team notified
- [ ] Release notes published

---

**Document Version:** 1.0  
**Last Updated:** 2025-01-XX  
**Maintained By:** Platform Engineering Team