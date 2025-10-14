# OpsConductor NG - Monitoring Stack

Quick reference for the monitoring infrastructure.

## 🚀 Quick Start

```bash
# Start monitoring (Prometheus + Grafana)
docker compose -f docker-compose.yml \
  -f monitoring/compose.monitoring.yml \
  -f monitoring/compose.grafana.yml \
  up -d

# Stop monitoring
docker compose -f docker-compose.yml \
  -f monitoring/compose.monitoring.yml \
  -f monitoring/compose.grafana.yml \
  down
```

## 🔗 Access Points

- **Prometheus**: http://localhost:9090
- **Grafana**: http://localhost:3001 (admin/opsconductor)
- **Metrics Endpoint**: http://localhost:8010/metrics

## 📊 Dashboards

1. **AI Execution**: Request rates, errors, latency, traces
2. **Selector**: Search performance, cache efficiency, DB health

## 🔔 Alerts

- **AI Execution**: Error rate, latency (P95/P99)
- **Selector**: DB errors, latency, cache evictions
- **SLO**: Fast/slow burn-rate alerts (99% target)
- **System**: Endpoint health, traffic monitoring

## 📁 Directory Structure

```
monitoring/
├── prometheus/
│   ├── prometheus.yml          # Scrape config
│   └── opsconductor.rules.yml  # Alert rules
├── grafana/
│   ├── dashboards/
│   │   ├── execution.json      # AI execution dashboard
│   │   └── selector.json       # Selector dashboard
│   └── provisioning/
│       ├── datasources.yml     # Prometheus datasource
│       └── dashboards.yml      # Dashboard provisioning
├── compose.monitoring.yml      # Prometheus compose override
├── compose.grafana.yml         # Grafana compose override
└── README.md                   # This file
```

## 🧪 CI Tests

```bash
# Run metrics presence tests
pytest tests/monitoring/test_metrics_presence.py -v

# Quick check
curl -fsS http://localhost:8010/metrics | grep -E "^(ai_|selector_)"
```

## 📚 Documentation

- **[MONITORING_README.md](../docs/MONITORING_README.md)**: Complete monitoring guide
- **[SLOS_AND_ALERTS.md](../docs/SLOS_AND_ALERTS.md)**: SLO definitions and runbooks

## 🔧 Common Tasks

### Reload Prometheus Config

```bash
docker exec opsconductor-prometheus kill -HUP 1
```

### Check Alert Rules

```bash
docker exec opsconductor-prometheus promtool check rules /etc/prometheus/opsconductor.rules.yml
```

### View Prometheus Targets

http://localhost:9090/targets

### View Active Alerts

http://localhost:9090/alerts

## 🐛 Troubleshooting

### No metrics in Grafana

1. Check Prometheus targets: http://localhost:9090/targets
2. Verify automation-service is running: `docker ps | grep automation`
3. Test metrics endpoint: `curl http://localhost:8010/metrics`

### Alert rules not loading

1. Check syntax: `docker exec opsconductor-prometheus promtool check rules /etc/prometheus/opsconductor.rules.yml`
2. Check Prometheus logs: `docker logs opsconductor-prometheus`
3. Reload config: `docker exec opsconductor-prometheus kill -HUP 1`

---

**PR #5**: Monitoring, SLOs & CI Gates  
**Branch**: zenc/monitoring-slos-ci-gates