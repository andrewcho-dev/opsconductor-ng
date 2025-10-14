# Monitoring Documentation Index

Quick navigation for all monitoring-related documentation.

## 🚀 Getting Started

**Start here if you're new to the monitoring infrastructure:**

1. **[Quick Visual Guide](QUICK_VISUAL_GUIDE.txt)** - Visual overview of what was delivered
2. **[Quick Start (README)](README.md)** - 5-minute setup guide
3. **[Verification Script](verify-monitoring.sh)** - Automated verification

## 📚 Complete Documentation

### User Guides

- **[Complete Monitoring Guide](../docs/MONITORING_README.md)** (3,500 words)
  - Quick start for local development
  - Dashboard descriptions
  - Alert rule reference
  - Production deployment guide
  - Troubleshooting procedures

- **[SLOs and Alerts](../docs/SLOS_AND_ALERTS.md)** (4,000 words)
  - SLO definitions (99% success target)
  - Burn-rate alerting logic
  - Alert runbooks with investigation steps
  - On-call procedures
  - Post-incident review templates

### Technical Documentation

- **[Architecture](ARCHITECTURE.md)** (2,500 words)
  - System architecture diagrams
  - Metrics flow
  - Alert evaluation flow
  - SLO burn-rate logic
  - Dashboard architecture
  - Network topology
  - Security architecture
  - Scalability considerations

- **[Deployment Checklist](DEPLOYMENT_CHECKLIST.md)**
  - Pre-deployment verification
  - Development environment setup
  - Staging environment setup
  - Production environment setup
  - Post-deployment validation
  - Troubleshooting checklist

### PR Documentation

- **[PR Summary](../docs/PR-005-monitoring-slos-ci-gates.md)**
  - Objectives and deliverables
  - Acceptance criteria
  - Test results
  - File inventory
  - Deployment plan

- **[Final Summary](../PR-005-FINAL-SUMMARY.md)**
  - Complete file inventory
  - Metrics reference
  - Alert rules summary
  - Dashboard descriptions
  - Usage guide
  - Success criteria

- **[Completion Summary](../MONITORING_COMPLETE.md)**
  - What was delivered
  - Test results
  - Metrics verified
  - Quick start guide
  - Next steps

## 🔧 Configuration Files

### Prometheus

- **[prometheus.yml](prometheus/prometheus.yml)** - Scrape configuration
  - 3 scrape jobs (automation-service, ai-pipeline, prometheus)
  - 10-15 second scrape intervals
  - Service discovery via Docker network

- **[opsconductor.rules.yml](prometheus/opsconductor.rules.yml)** - Alert rules
  - 11 alert rules in 4 groups
  - AI execution alerts (error rate, latency)
  - Selector alerts (DB errors, latency, cache)
  - SLO burn-rate alerts (fast/slow)
  - System health alerts

### Grafana

- **[execution.json](grafana/dashboards/execution.json)** - AI execution dashboard
  - 6 panels: request rate, error rate, latency, heatmap, traces
  - Alert annotations
  - Trace ID links for debugging

- **[selector.json](grafana/dashboards/selector.json)** - Selector dashboard
  - 9 panels: request rate, cache hit rate, DB errors, latency, build info
  - Color-coded thresholds
  - Build metadata table

- **[datasources.yml](grafana/provisioning/datasources.yml)** - Prometheus datasource
- **[dashboards.yml](grafana/provisioning/dashboards.yml)** - Dashboard provisioning

### Docker Compose

- **[compose.monitoring.yml](compose.monitoring.yml)** - Prometheus container
  - Port 9090
  - 15-day retention
  - Volume mounts for config and data

- **[compose.grafana.yml](compose.grafana.yml)** - Grafana container
  - Port 3001
  - Auto-provisioning of datasources and dashboards
  - Volume mounts for config and data

## 🧪 Testing

### CI Tests

- **[test_metrics_presence.py](../tests/monitoring/test_metrics_presence.py)** - 9 comprehensive tests
  - Metrics endpoint reachable
  - Content type validation
  - AI metrics presence
  - Selector metrics presence
  - HELP/TYPE annotations
  - Histogram structure
  - Counter labels
  - Build info metric

### Verification

- **[verify-monitoring.sh](verify-monitoring.sh)** - Automated verification script
  - Checks metrics endpoint
  - Validates required metrics
  - Verifies annotations
  - Tests histogram structure
  - Checks Prometheus (if running)
  - Checks Grafana (if running)
  - Runs pytest tests

## 📊 Metrics Reference

### AI Execution Metrics

| Metric | Type | File |
|--------|------|------|
| `ai_requests_total` | Counter | automation-service/observability/metrics.py |
| `ai_request_errors_total` | Counter | automation-service/observability/metrics.py |
| `ai_request_duration_seconds` | Histogram | automation-service/observability/metrics.py |

### Selector Metrics

| Metric | Type | File |
|--------|------|------|
| `selector_requests_total` | Counter | automation-service/selector/metrics.py |
| `selector_request_duration_seconds` | Histogram | automation-service/selector/metrics.py |
| `selector_db_errors_total` | Counter | automation-service/selector/metrics.py |
| `selector_cache_evictions_total` | Counter | automation-service/selector/metrics.py |
| `selector_cache_entries` | Gauge | automation-service/selector/metrics.py |
| `selector_cache_ttl_seconds` | Gauge | automation-service/selector/metrics.py |
| `selector_build_info` | Gauge | automation-service/selector/metrics.py |

## 🔔 Alert Rules Reference

### AI Execution Alerts

| Alert | Severity | Threshold | File |
|-------|----------|-----------|------|
| AIExecutionErrorRateHigh | Warning | >5% for 2m | opsconductor.rules.yml:17 |
| AIExecutionLatencyP95High | Warning | >1s for 5m | opsconductor.rules.yml:31 |
| AIExecutionLatencyP99Critical | Critical | >5s for 3m | opsconductor.rules.yml:45 |

### Selector Alerts

| Alert | Severity | Threshold | File |
|-------|----------|-----------|------|
| SelectorErrorBurst | Warning | >0 errors in 5m | opsconductor.rules.yml:62 |
| SelectorLatencyHigh | Warning | P95 >500ms for 5m | opsconductor.rules.yml:76 |
| SelectorCacheEvictionRateHigh | Info | >10/sec for 5m | opsconductor.rules.yml:90 |

### SLO Burn-Rate Alerts

| Alert | Severity | Windows | File |
|-------|----------|---------|------|
| SLOBurnRateFast | Critical | 5m/1h both <99% | opsconductor.rules.yml:107 |
| SLOBurnRateSlow | Warning | 30m/6h both <99% | opsconductor.rules.yml:135 |

### System Health Alerts

| Alert | Severity | Threshold | File |
|-------|----------|-----------|------|
| MetricsEndpointDown | Critical | up==0 for 1m | opsconductor.rules.yml:166 |
| NoRequestsReceived | Info | 0 req/10m | opsconductor.rules.yml:180 |

## 📈 Dashboard Panels Reference

### Execution Dashboard

| Panel | Type | Query |
|-------|------|-------|
| Request Rate | Graph | `sum(rate(ai_requests_total[5m])) by (status)` |
| Error Rate | Graph | `sum(rate(ai_request_errors_total[5m])) by (reason)` |
| Request Duration | Graph | `histogram_quantile(0.95, sum by (le) (rate(ai_request_duration_seconds_bucket[5m])))` |
| Requests by Tool | Graph | `sum(rate(ai_requests_total[5m])) by (tool)` |
| Duration Heatmap | Heatmap | `sum(increase(ai_request_duration_seconds_bucket[1m])) by (le)` |
| Trace ID Links | Table | `ai_requests_total` |

### Selector Dashboard

| Panel | Type | Query |
|-------|------|-------|
| Request Rate by Status | Graph | `sum(rate(selector_requests_total[5m])) by (status)` |
| Request Rate by Source | Graph | `sum(rate(selector_requests_total[5m])) by (source)` |
| Cache Hit Rate | Stat | `(sum(rate(selector_requests_total{source="cache"}[5m])) / sum(rate(selector_requests_total[5m]))) * 100` |
| Database Errors | Stat | `increase(selector_db_errors_total[5m])` |
| Cache Entries | Stat | `selector_cache_entries` |
| Cache TTL | Stat | `selector_cache_ttl_seconds` |
| Request Duration | Graph | `histogram_quantile(0.95, sum by (le) (rate(selector_request_duration_seconds_bucket[5m])))` |
| Cache Eviction Rate | Graph | `rate(selector_cache_evictions_total[5m])` |
| Build Info | Table | `selector_build_info` |

## 🔗 Quick Links

### Local Development

- Prometheus: http://localhost:9090
- Grafana: http://localhost:3001 (admin/opsconductor)
- Metrics: http://localhost:8010/metrics
- Prometheus Targets: http://localhost:9090/targets
- Prometheus Rules: http://localhost:9090/rules
- Prometheus Alerts: http://localhost:9090/alerts

### Commands

```bash
# Start monitoring
docker compose -f docker-compose.yml \
  -f monitoring/compose.monitoring.yml \
  -f monitoring/compose.grafana.yml up -d

# Stop monitoring
docker compose -f docker-compose.yml \
  -f monitoring/compose.monitoring.yml \
  -f monitoring/compose.grafana.yml down

# Verify deployment
./monitoring/verify-monitoring.sh

# Run CI tests
pytest tests/monitoring/test_metrics_presence.py -v

# View metrics
curl http://localhost:8010/metrics

# Reload Prometheus config
docker exec opsconductor-prometheus kill -HUP 1

# Check alert rules
docker exec opsconductor-prometheus promtool check rules /etc/prometheus/opsconductor.rules.yml
```

## 📞 Support

For issues or questions:

1. Check [Troubleshooting](../docs/MONITORING_README.md#-troubleshooting) section
2. Review [Runbooks](../docs/SLOS_AND_ALERTS.md#-alert-runbooks)
3. Run verification script: `./monitoring/verify-monitoring.sh`
4. Check service logs: `docker logs opsconductor-automation-service`

---

**Last Updated**: 2024-01-20  
**Version**: 1.0.0 (PR #5)  
**Branch**: zenc/monitoring-slos-ci-gates