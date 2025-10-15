# Changelog

All notable changes to OpsConductor NG will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [Walking Skeleton v1.1.0] - 2025-01-XX

### Added - Walking Skeleton Release

This release establishes the **walking skeleton** for OpsConductor NG - a minimal end-to-end implementation that demonstrates the complete architecture from frontend to backend execution.

#### Core Features
- **AI Execution Proxy** (`/ai/execute`) - Automation service proxies execution requests to AI pipeline
- **Echo Tool Bypass** - Direct ping→pong execution without LLM overhead for testing
- **Frontend Exec Sandbox** - Interactive UI component for testing AI execution
- **Comprehensive Monitoring Stack** - Prometheus + Grafana with custom dashboards
- **Metrics & Observability** - Full OpenTelemetry instrumentation with trace_id propagation

#### Component Versions
- **automation-service**: 3.0.1
- **ai-pipeline**: 1.1.0
- **frontend**: 1.1.0

#### Monitoring & SLOs
- **Prometheus Metrics**:
  - `ai_requests_total` - Counter for all AI execution requests
  - `ai_request_duration_seconds` - Histogram for request latency
  - `ai_request_errors_total` - Counter for failed requests
  - `selector_*` - Tool selection metrics
  
- **Grafana Dashboards**:
  - Execution Dashboard - Real-time execution metrics and traces
  - Selector Dashboard - Tool selection performance and accuracy
  
- **SLO Targets**:
  - Availability: 99.9% (error rate < 0.1%)
  - Latency: p95 < 1000ms, p99 < 2000ms
  - Error Budget: 43.2 minutes/month downtime

#### CI/CD Gates
- Automated smoke tests for `/health` and `/metrics` endpoints
- Metric presence validation in CI pipeline
- Docker volume mount validation
- Selector endpoint smoke tests

#### Documentation
- `docs/PR-004-exec-sandbox.md` - AI execution proxy implementation
- `docs/PR-005-monitoring-slos-ci-gates.md` - Monitoring stack setup
- `docs/MONITORING_README.md` - Monitoring architecture and usage
- `docs/SLOS_AND_ALERTS.md` - SLO definitions and alerting rules
- `monitoring/ARCHITECTURE.md` - Detailed monitoring architecture
- `monitoring/DEPLOYMENT_CHECKLIST.md` - Deployment verification steps

### Changed
- Consolidated metrics collection across services
- Improved trace_id propagation through request chain
- Enhanced error handling with structured error responses
- Updated Docker Compose networking for monitoring stack

### Fixed
- Docker volume mount paths for Grafana dashboards
- Prometheus scrape configuration for all services
- Network configuration for monitoring containers
- Frontend TypeScript compilation warnings

### Technical Details

#### Architecture Flow
```
Frontend (Exec Sandbox)
    ↓ POST /ai/execute
Kong API Gateway (port 3000)
    ↓ /ai/execute → automation-service:3003
Automation Service (Proxy)
    ↓ HTTP client → ai-pipeline:8001
AI Pipeline (Echo Tool)
    ↓ Bypass LLM for "ping" → "pong"
    ↓ Return response
Automation Service
    ↓ Record metrics (ai_requests_total, duration)
    ↓ Return to frontend
Frontend displays result + trace_id
```

#### Metrics Collection Points
1. **Automation Service** (`/ai/execute`):
   - Request count, duration, errors
   - Trace ID generation and propagation
   
2. **AI Pipeline** (`/execute`):
   - Tool execution metrics
   - Selector performance metrics
   
3. **Prometheus** (scrapes every 15s):
   - automation-service:9091/metrics
   - ai-pipeline:9092/metrics
   
4. **Grafana** (visualizes):
   - Real-time dashboards
   - Alert rule evaluation

#### Feature Flags
- `FEATURE_BYPASS_LLM=true` - Enable echo tool bypass (canary only)
- `ENABLE_METRICS=true` - Enable Prometheus metrics collection

### Security
- No secrets in code; all credentials via environment variables
- Encrypted credential storage for execution contexts
- JWT-based authentication (Keycloak integration ready)

### Performance
- Echo tool bypass: < 50ms latency
- Full LLM path: < 1000ms p95 latency
- Metrics overhead: < 5ms per request

### Testing
- Unit tests for metrics collection
- Integration tests for `/ai/execute` proxy
- E2E tests for frontend → backend flow
- Smoke tests for monitoring stack

---

## [3.0.0] - 2024-12-XX

### Added
- Initial NEWIDEA.MD pipeline architecture (4-stage AI pipeline)
- Combined Stage AB for improved tool selection accuracy
- Unified execution framework
- PostgreSQL 17 with pgvector for semantic search
- Redis caching layer
- vLLM integration with Qwen2.5 models
- Kong API Gateway
- Keycloak identity provider

### Changed
- Complete rewrite from legacy AI Brain architecture
- Microservices architecture with Docker Compose
- Clean separation of concerns across services

---

## Release Notes

### Walking Skeleton v1.1.0 - Production Readiness

This release represents the **minimum viable production deployment** of OpsConductor NG. The walking skeleton demonstrates:

✅ **End-to-End Execution**: Frontend → Kong → Automation → AI Pipeline → Response  
✅ **Observability**: Full metrics, traces, and dashboards  
✅ **Reliability**: Health checks, error handling, and SLO monitoring  
✅ **Testability**: Automated smoke tests and CI gates  
✅ **Deployability**: Docker Compose with monitoring stack  

### Next Steps (Post-Walking Skeleton)

1. **LLM Integration**: Enable full AI pipeline with tool selection
2. **Authentication**: Activate Keycloak JWT validation
3. **Asset Integration**: Connect to asset service for real inventory
4. **Execution Libraries**: Enable SSH, PowerShell, and Impacket executors
5. **Advanced Features**: Multi-step workflows, approval gates, audit logging

### Rollback Plan

If issues are detected in production:

1. **Immediate**: Set `FEATURE_BYPASS_LLM=false` to disable echo tool
2. **Metrics Check**: Verify error rate < 1% in Grafana
3. **Full Rollback**: `docker compose down && git checkout <previous-tag> && docker compose up -d`
4. **Verification**: Run `scripts/release_smoke.sh` to confirm health

### Support

For issues or questions:
- Check `docs/RELEASE_RUNBOOK.md` for operational procedures
- Review Grafana dashboards for real-time metrics
- Examine Prometheus alerts for SLO violations
- Consult `monitoring/DEPLOYMENT_CHECKLIST.md` for verification steps