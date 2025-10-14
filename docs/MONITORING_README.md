# OpsConductor NG - Monitoring Guide

This guide covers the monitoring infrastructure for OpsConductor NG, including Prometheus metrics, Grafana dashboards, and alerting.

## 📊 Overview

OpsConductor NG exposes Prometheus metrics for:
- **AI Execution Path**: Request rates, error rates, latency distributions
- **Selector Path**: Search performance, cache efficiency, database health
- **SLO Tracking**: 99% success rate target with burn-rate alerts

## 🚀 Quick Start

### Local Development Setup

1. **Start monitoring stack** (Prometheus + Grafana):
   ```bash
   docker compose \
     -f docker-compose.yml \
     -f monitoring/compose.monitoring.yml \
     -f monitoring/compose.grafana.yml \
     up -d
   ```

2. **Access dashboards**:
   - **Prometheus**: http://localhost:9090
   - **Grafana**: http://localhost:3001 (admin/opsconductor)

3. **View metrics endpoint**:
   ```bash
   curl http://localhost:8010/metrics
   ```

### Stop Monitoring Stack

```bash
docker compose \
  -f docker-compose.yml \
  -f monitoring/compose.monitoring.yml \
  -f monitoring/compose.grafana.yml \
  down
```

## 📈 Available Dashboards

### 1. AI Execution Dashboard

**URL**: http://localhost:3001/d/ai-execution

**Panels**:
- **Request Rate**: Total requests/sec by status (success/error)
- **Error Rate**: Error percentage and breakdown by reason
- **Request Duration**: P50/P95/P99 latency percentiles
- **Requests by Tool**: Traffic distribution across tools
- **Duration Heatmap**: Visual latency distribution over time
- **Trace ID Links**: Click-through to logs for debugging

**Use Cases**:
- Monitor execution performance
- Identify slow tools
- Track error patterns
- Debug specific requests via trace IDs

### 2. Selector Dashboard

**URL**: http://localhost:3001/d/selector

**Panels**:
- **Request Rate by Status**: ok/error breakdown
- **Request Rate by Source**: fresh/cache/degraded breakdown
- **Cache Hit Rate**: Percentage of requests served from cache
- **Database Errors**: DB connectivity issues
- **Cache Entries**: Current cache size
- **Cache TTL**: Configured time-to-live
- **Request Duration**: P50/P95/P99 latency
- **Cache Eviction Rate**: Evictions per second
- **Build Info**: Version and deployment metadata

**Use Cases**:
- Monitor search performance
- Optimize cache configuration
- Track database health
- Identify degraded mode triggers

## 🔔 Alert Rules

### AI Execution Alerts

| Alert | Threshold | Duration | Severity | Description |
|-------|-----------|----------|----------|-------------|
| `AIExecutionErrorRateHigh` | >5% | 2m | warning | Error rate exceeds acceptable threshold |
| `AIExecutionLatencyP95High` | >1s | 5m | warning | P95 latency too high |
| `AIExecutionLatencyP99Critical` | >5s | 3m | critical | P99 latency critical |

### Selector Alerts

| Alert | Threshold | Duration | Severity | Description |
|-------|-----------|----------|----------|-------------|
| `SelectorErrorBurst` | >0 errors | 1m | warning | Database errors detected |
| `SelectorLatencyHigh` | P95 >500ms | 5m | warning | Search latency too high |
| `SelectorCacheEvictionRateHigh` | >10/sec | 5m | info | High cache churn |

### SLO Burn-Rate Alerts

| Alert | Windows | Severity | Description |
|-------|---------|----------|-------------|
| `SLOBurnRateFast` | 5m/1h | critical | Fast burn: <99% success in both windows |
| `SLOBurnRateSlow` | 30m/6h | warning | Slow burn: <99% success in both windows |

**SLO Target**: 99% success rate

**Burn-Rate Logic**:
- **Fast burn**: Short-term (5m) and medium-term (1h) both below target → immediate action
- **Slow burn**: Medium-term (30m) and long-term (6h) both below target → plan corrective action

### System Health Alerts

| Alert | Threshold | Duration | Severity | Description |
|-------|-----------|----------|----------|-------------|
| `MetricsEndpointDown` | up==0 | 1m | critical | Metrics scraping failed |
| `NoRequestsReceived` | 0 req/10m | 10m | info | No traffic detected |

## 🔧 Configuration

### Tuning Alert Thresholds

Edit `monitoring/prometheus/opsconductor.rules.yml`:

```yaml
# Example: Change error rate threshold from 5% to 10%
- alert: AIExecutionErrorRateHigh
  expr: |
    (rate(ai_request_errors_total[5m]) / rate(ai_requests_total[5m])) > 0.10  # Changed
  for: 2m
```

Reload Prometheus:
```bash
docker exec opsconductor-prometheus kill -HUP 1
```

### Disabling Alerts

Comment out the alert in `opsconductor.rules.yml`:

```yaml
# - alert: SelectorCacheEvictionRateHigh
#   expr: rate(selector_cache_evictions_total[5m]) > 10
#   ...
```

### Adjusting Scrape Intervals

Edit `monitoring/prometheus/prometheus.yml`:

```yaml
scrape_configs:
  - job_name: 'automation-service-selector'
    scrape_interval: 5s  # Changed from 10s
```

## 📊 Metrics Reference

### AI Execution Metrics

| Metric | Type | Labels | Description |
|--------|------|--------|-------------|
| `ai_requests_total` | Counter | status, tool | Total AI execution requests |
| `ai_request_errors_total` | Counter | reason, tool | Total AI execution errors |
| `ai_request_duration_seconds` | Histogram | tool | Request duration distribution |

**Buckets**: 0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0, 30.0, 60.0 seconds

### Selector Metrics

| Metric | Type | Labels | Description |
|--------|------|--------|-------------|
| `selector_requests_total` | Counter | status, source | Total selector requests |
| `selector_request_duration_seconds` | Histogram | - | Request duration distribution |
| `selector_db_errors_total` | Counter | - | Database errors |
| `selector_cache_evictions_total` | Counter | - | Cache evictions |
| `selector_cache_entries` | Gauge | - | Current cache size |
| `selector_cache_ttl_seconds` | Gauge | - | Cache TTL |
| `selector_build_info` | Gauge | version, git_commit, built_at | Build metadata |

**Buckets**: 0.01, 0.05, 0.1, 0.25, 0.5, 1, 2, 5, 10 seconds

## 🎯 Production Deployment

### Prerequisites

- Prometheus server (v2.48+)
- Grafana server (v10.2+)
- Network access to automation-service:8010

### Step 1: Deploy Prometheus

1. Copy alert rules to Prometheus server:
   ```bash
   scp monitoring/prometheus/opsconductor.rules.yml prometheus-server:/etc/prometheus/
   ```

2. Update Prometheus config with scrape targets:
   ```yaml
   scrape_configs:
     - job_name: 'automation-service-selector'
       static_configs:
         - targets: ['automation-service.prod.example.com:8010']
   ```

3. Reload Prometheus:
   ```bash
   curl -X POST http://prometheus-server:9090/-/reload
   ```

### Step 2: Import Grafana Dashboards

1. Login to Grafana
2. Navigate to **Dashboards** → **Import**
3. Upload `monitoring/grafana/dashboards/execution.json`
4. Upload `monitoring/grafana/dashboards/selector.json`
5. Select Prometheus datasource

### Step 3: Configure Alerting

1. In Grafana, go to **Alerting** → **Contact points**
2. Add notification channels (Slack, PagerDuty, email)
3. Create notification policies for severity levels:
   - **critical** → PagerDuty
   - **warning** → Slack
   - **info** → Email

### Step 4: Verify Metrics

```bash
# Check metrics endpoint
curl -fsS https://automation-service.prod.example.com:8010/metrics | grep -E "^(ai_|selector_)"

# Verify Prometheus scraping
curl http://prometheus-server:9090/api/v1/targets | jq '.data.activeTargets[] | select(.labels.job | contains("automation"))'
```

## 🐛 Troubleshooting

### Metrics Endpoint Returns 404

**Symptom**: `curl http://localhost:8010/metrics` returns 404

**Solution**:
1. Verify automation-service is running: `docker ps | grep automation`
2. Check service logs: `docker logs opsconductor-automation-service`
3. Ensure port 8010 is exposed in docker-compose.yml

### No Data in Grafana Dashboards

**Symptom**: Dashboards show "No data"

**Solution**:
1. Check Prometheus targets: http://localhost:9090/targets
2. Verify scrape is successful (State: UP)
3. Check Prometheus logs: `docker logs opsconductor-prometheus`
4. Test query in Prometheus: `ai_requests_total`

### Alert Rules Not Loading

**Symptom**: Prometheus UI shows no rules

**Solution**:
1. Check rules file syntax:
   ```bash
   docker exec opsconductor-prometheus promtool check rules /etc/prometheus/opsconductor.rules.yml
   ```
2. Verify volume mount in compose file
3. Reload Prometheus: `docker exec opsconductor-prometheus kill -HUP 1`

### High Cardinality Warnings

**Symptom**: Prometheus logs show "high cardinality" warnings

**Solution**:
1. Review label usage - avoid high-cardinality labels (e.g., trace_id, user_id)
2. Use recording rules to pre-aggregate high-cardinality metrics
3. Adjust retention period if needed

## 📚 Additional Resources

- [Prometheus Documentation](https://prometheus.io/docs/)
- [Grafana Documentation](https://grafana.com/docs/)
- [SLO Burn Rate Alerting](https://sre.google/workbook/alerting-on-slos/)
- [OpsConductor SLOs and Alerts](./SLOS_AND_ALERTS.md)

## 🔐 Security Considerations

### Production Checklist

- [ ] Enable authentication on Prometheus (basic auth or OAuth)
- [ ] Enable authentication on Grafana (LDAP/SAML)
- [ ] Use TLS for metrics endpoints
- [ ] Restrict network access to monitoring ports
- [ ] Rotate Grafana admin password
- [ ] Enable audit logging
- [ ] Set up backup for Grafana dashboards
- [ ] Configure retention policies

### Sensitive Data

Metrics should NOT contain:
- User credentials
- API keys
- Personal identifiable information (PII)
- Full trace IDs in labels (use links instead)

## 📞 Support

For issues or questions:
1. Check [Troubleshooting](#-troubleshooting) section
2. Review service logs: `docker logs opsconductor-automation-service`
3. Check Prometheus targets: http://localhost:9090/targets
4. Verify alert rules: http://localhost:9090/rules

---

**Last Updated**: 2024-01-20  
**Version**: 1.0.0 (PR #5)