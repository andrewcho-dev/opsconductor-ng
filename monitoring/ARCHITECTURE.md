# Monitoring Architecture

## Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                     OpsConductor NG                              │
│                   Monitoring Architecture                        │
└─────────────────────────────────────────────────────────────────┘

┌──────────────────┐         ┌──────────────────┐
│  Automation      │         │   AI Pipeline    │
│  Service         │         │   (Port 8000)    │
│  (Port 8010)     │         │                  │
│                  │         │  /pipeline/      │
│  /metrics        │         │   metrics        │
│  - ai_*          │         │                  │
│  - selector_*    │         │                  │
└────────┬─────────┘         └────────┬─────────┘
         │                            │
         │ Scrape every 10s           │ Scrape every 15s
         │                            │
         └────────────┬───────────────┘
                      │
                      ▼
         ┌────────────────────────┐
         │     Prometheus         │
         │     (Port 9090)        │
         │                        │
         │  - Scrape metrics      │
         │  - Evaluate alerts     │
         │  - Store time series   │
         │  - 15 day retention    │
         └───────────┬────────────┘
                     │
                     │ PromQL queries
                     │
                     ▼
         ┌────────────────────────┐
         │      Grafana           │
         │      (Port 3001)       │
         │                        │
         │  - Execution dashboard │
         │  - Selector dashboard  │
         │  - Alert annotations   │
         └────────────────────────┘
```

## Metrics Flow

```
┌─────────────────────────────────────────────────────────────────┐
│                        Metrics Flow                              │
└─────────────────────────────────────────────────────────────────┘

1. Request arrives at automation-service
   │
   ▼
2. Metrics recorded:
   - ai_requests_total{status="success", tool="echo"}
   - ai_request_duration_seconds{tool="echo"} (histogram)
   │
   ▼
3. Prometheus scrapes /metrics endpoint
   │
   ▼
4. Metrics stored in time-series database
   │
   ▼
5. Alert rules evaluated every 30s
   │
   ├─▶ AIExecutionErrorRateHigh?
   ├─▶ AIExecutionLatencyP95High?
   ├─▶ SLOBurnRateFast?
   └─▶ SelectorErrorBurst?
   │
   ▼
6. Grafana queries Prometheus
   │
   ▼
7. Dashboards render visualizations
```

## Alert Evaluation Flow

```
┌─────────────────────────────────────────────────────────────────┐
│                    Alert Evaluation                              │
└─────────────────────────────────────────────────────────────────┘

Every 30 seconds:

1. Prometheus evaluates alert rules
   │
   ▼
2. Calculate metrics:
   - Error rate: rate(ai_request_errors_total[5m]) / rate(ai_requests_total[5m])
   - P95 latency: histogram_quantile(0.95, ai_request_duration_seconds_bucket[5m])
   │
   ▼
3. Compare to thresholds:
   - Error rate > 5%?
   - P95 latency > 1s?
   │
   ▼
4. Check duration:
   - Has condition been true for 2m?
   │
   ▼
5. Fire alert:
   - State: PENDING → FIRING
   - Annotations: summary, description, runbook
   │
   ▼
6. Send notifications:
   - Slack (warning)
   - PagerDuty (critical)
   - Email (info)
```

## SLO Burn-Rate Logic

```
┌─────────────────────────────────────────────────────────────────┐
│                  SLO Burn-Rate Alerting                          │
└─────────────────────────────────────────────────────────────────┘

Target: 99% success rate (30-day window)
Error Budget: 1% (7.2 hours/month)

Fast Burn Alert (Critical):
┌─────────────────────────────────────────────────────────────────┐
│  Short Window (5m)     Long Window (1h)                         │
│  Success < 99%    AND  Success < 99%                            │
│                                                                  │
│  Burn Rate: 14.4x                                               │
│  Budget Consumed: 2% in 1 hour                                  │
│  Time to Exhaustion: ~2 days                                    │
│                                                                  │
│  Action: IMMEDIATE investigation required                       │
└─────────────────────────────────────────────────────────────────┘

Slow Burn Alert (Warning):
┌─────────────────────────────────────────────────────────────────┐
│  Medium Window (30m)   Long Window (6h)                         │
│  Success < 99%    AND  Success < 99%                            │
│                                                                  │
│  Burn Rate: 6x                                                  │
│  Budget Consumed: 5% in 6 hours                                 │
│  Time to Exhaustion: ~5 days                                    │
│                                                                  │
│  Action: Investigate within 1 hour                              │
└─────────────────────────────────────────────────────────────────┘

Why Multi-Window?
- Short window: Detects spikes
- Long window: Confirms trend (not just noise)
- Both must fail: Reduces false positives
```

## Dashboard Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                  Execution Dashboard                             │
└─────────────────────────────────────────────────────────────────┘

Row 1: Request Overview
┌──────────────────────┐  ┌──────────────────────┐
│  Request Rate        │  │  Error Rate          │
│  (by status)         │  │  (by reason + %)     │
│                      │  │                      │
│  ▲ success           │  │  ▲ 5% threshold      │
│  │ error             │  │  │ current rate      │
│  └─────────▶ time    │  │  └─────────▶ time    │
└──────────────────────┘  └──────────────────────┘

Row 2: Latency Analysis
┌──────────────────────┐  ┌──────────────────────┐
│  Request Duration    │  │  Requests by Tool    │
│  (P50/P95/P99)       │  │                      │
│                      │  │  ▲ echo              │
│  ▲ P99               │  │  │ ssh               │
│  │ P95               │  │  │ powershell        │
│  │ P50               │  │  └─────────▶ time    │
│  └─────────▶ time    │  │                      │
└──────────────────────┘  └──────────────────────┘

Row 3: Distribution
┌──────────────────────────────────────────────────┐
│  Duration Heatmap                                │
│                                                  │
│  Time ▶                                          │
│  ▲                                               │
│  │ [████████░░░░░░░░] 0.1s                      │
│  │ [██████████████░░] 0.5s                      │
│  │ [████░░░░░░░░░░░░] 1.0s                      │
│  │ [██░░░░░░░░░░░░░░] 5.0s                      │
│  Duration                                        │
└──────────────────────────────────────────────────┘

Row 4: Debugging
┌──────────────────────────────────────────────────┐
│  Trace ID Links                                  │
│                                                  │
│  Status  Tool      Trace ID         [View Logs] │
│  ✓       echo      abc123           [→]         │
│  ✗       ssh       def456           [→]         │
│  ✓       ps        ghi789           [→]         │
└──────────────────────────────────────────────────┘
```

```
┌─────────────────────────────────────────────────────────────────┐
│                   Selector Dashboard                             │
└─────────────────────────────────────────────────────────────────┘

Row 1: Request Overview
┌──────────────────────┐  ┌──────────────────────┐
│  Request Rate        │  │  Request Rate        │
│  (by status)         │  │  (by source)         │
│                      │  │                      │
│  ▲ ok                │  │  ▲ fresh             │
│  │ error             │  │  │ cache             │
│  └─────────▶ time    │  │  │ degraded          │
│                      │  │  └─────────▶ time    │
└──────────────────────┘  └──────────────────────┘

Row 2: Health Metrics
┌─────────┐  ┌─────────┐  ┌─────────┐  ┌─────────┐
│ Cache   │  │ DB      │  │ Cache   │  │ Cache   │
│ Hit     │  │ Errors  │  │ Entries │  │ TTL     │
│ Rate    │  │         │  │         │  │         │
│  85%    │  │    0    │  │   142   │  │  600s   │
│ [████░] │  │ [    ]  │  │ [███░]  │  │ [███░]  │
└─────────┘  └─────────┘  └─────────┘  └─────────┘

Row 3: Performance
┌──────────────────────┐  ┌──────────────────────┐
│  Request Duration    │  │  Cache Eviction Rate │
│  (P50/P95/P99)       │  │                      │
│                      │  │  ▲                   │
│  ▲ P99               │  │  │                   │
│  │ P95               │  │  │                   │
│  │ P50               │  │  └─────────▶ time    │
│  └─────────▶ time    │  │                      │
└──────────────────────┘  └──────────────────────┘

Row 4: Build Info
┌──────────────────────────────────────────────────┐
│  Version  Git Commit  Built At                   │
│  3.0.0    abc123def   2024-01-20T10:00:00Z       │
└──────────────────────────────────────────────────┘
```

## Metric Cardinality

```
┌─────────────────────────────────────────────────────────────────┐
│                    Metric Cardinality                            │
└─────────────────────────────────────────────────────────────────┘

Low Cardinality (Good):
✓ ai_requests_total{status, tool}
  - status: 2 values (success, error)
  - tool: ~20 values (echo, ssh, powershell, ...)
  - Total series: 2 × 20 = 40

✓ selector_requests_total{status, source}
  - status: 2 values (ok, error)
  - source: 3 values (fresh, cache, degraded)
  - Total series: 2 × 3 = 6

High Cardinality (Avoid):
✗ ai_requests_total{trace_id}
  - trace_id: unlimited unique values
  - Total series: unbounded (BAD!)

✗ ai_requests_total{user_id}
  - user_id: thousands of unique values
  - Total series: thousands (BAD!)

Best Practice:
- Use labels for dimensions with <100 unique values
- Use links/annotations for high-cardinality data (trace_id, user_id)
- Aggregate high-cardinality data in application logs
```

## Storage and Retention

```
┌─────────────────────────────────────────────────────────────────┐
│                  Storage and Retention                           │
└─────────────────────────────────────────────────────────────────┘

Prometheus Storage:
┌────────────────────────────────────────────────────────────────┐
│  Retention: 15 days                                            │
│  Scrape Interval: 10-15s                                       │
│  Evaluation Interval: 15s                                      │
│                                                                │
│  Estimated Storage:                                            │
│  - Metrics: ~50 families                                       │
│  - Series: ~500 time series                                    │
│  - Samples: ~3M samples/day                                    │
│  - Storage: ~100MB/day, ~1.5GB total                           │
└────────────────────────────────────────────────────────────────┘

Grafana Storage:
┌────────────────────────────────────────────────────────────────┐
│  Dashboards: Stored in JSON files                             │
│  Provisioning: Auto-imported on startup                       │
│  User Data: SQLite database                                   │
│  Storage: ~50MB                                                │
└────────────────────────────────────────────────────────────────┘

Backup Strategy:
- Prometheus: Volume snapshots (optional)
- Grafana: Dashboard JSON files in git
- Alerts: Rules YAML files in git
```

## Network Topology

```
┌─────────────────────────────────────────────────────────────────┐
│                     Network Topology                             │
└─────────────────────────────────────────────────────────────────┘

Docker Network: opsconductor
┌────────────────────────────────────────────────────────────────┐
│                                                                │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────┐   │
│  │ Automation   │    │ AI Pipeline  │    │ Prometheus   │   │
│  │ Service      │    │              │    │              │   │
│  │ :8010        │◀───┤ :8000        │◀───┤ :9090        │   │
│  │ :3003        │    │              │    │              │   │
│  └──────────────┘    └──────────────┘    └──────┬───────┘   │
│                                                   │           │
│                                                   │           │
│                                          ┌────────▼───────┐   │
│                                          │ Grafana        │   │
│                                          │ :3000          │   │
│                                          └────────────────┘   │
│                                                                │
└────────────────────────────────────────────────────────────────┘
         │                                              │
         │ Port Mapping                                 │
         ▼                                              ▼
    localhost:8010                               localhost:3001
    localhost:9090
```

## Security Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                    Security Architecture                         │
└─────────────────────────────────────────────────────────────────┘

Development:
┌────────────────────────────────────────────────────────────────┐
│  - No authentication on Prometheus                             │
│  - Basic auth on Grafana (admin/opsconductor)                  │
│  - Metrics endpoint public (no sensitive data)                 │
│  - All services on internal Docker network                     │
└────────────────────────────────────────────────────────────────┘

Production:
┌────────────────────────────────────────────────────────────────┐
│  ✓ Basic auth on Prometheus                                    │
│  ✓ LDAP/SAML on Grafana                                        │
│  ✓ TLS for all endpoints                                       │
│  ✓ Network policies (firewall rules)                           │
│  ✓ No PII in metrics                                           │
│  ✓ Audit logging enabled                                       │
│  ✓ Regular security updates                                    │
└────────────────────────────────────────────────────────────────┘
```

## Scalability Considerations

```
┌─────────────────────────────────────────────────────────────────┐
│                    Scalability                                   │
└─────────────────────────────────────────────────────────────────┘

Current Scale:
- Services: 2 (automation-service, ai-pipeline)
- Metrics: ~50 families, ~500 series
- Scrape Rate: ~30 samples/sec
- Storage: ~100MB/day

Scale to 10x:
- Services: 20 (multiple instances)
- Metrics: ~500 families, ~5000 series
- Scrape Rate: ~300 samples/sec
- Storage: ~1GB/day

Solutions:
1. Prometheus Federation (hierarchical)
2. Thanos (long-term storage)
3. Cortex (multi-tenant)
4. Recording rules (pre-aggregation)
5. Metric relabeling (drop unused metrics)
```

---

**Last Updated**: 2024-01-20  
**Version**: 1.0.0 (PR #5)