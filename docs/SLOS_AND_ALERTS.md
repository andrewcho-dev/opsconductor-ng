# OpsConductor NG - SLOs and Alerting Strategy

This document defines Service Level Objectives (SLOs), alerting strategy, and runbook procedures for OpsConductor NG.

## 📋 Table of Contents

- [SLO Definitions](#-slo-definitions)
- [Burn-Rate Alerting](#-burn-rate-alerting)
- [Alert Runbooks](#-alert-runbooks)
- [On-Call Procedures](#-on-call-procedures)

## 🎯 SLO Definitions

### Primary SLO: Execution Success Rate

**Target**: 99% of AI execution requests succeed  
**Measurement Window**: 30 days  
**Error Budget**: 1% (allows ~7.2 hours of errors per month)

**Success Criteria**:
- HTTP 200 response
- `success: true` in response body
- No unhandled exceptions

**Failure Criteria**:
- HTTP 5xx errors
- HTTP 4xx errors (except 429 rate limiting)
- `success: false` in response body
- Timeout (>60s)

**Metric**: `ai_requests_total{status="success"}` / `ai_requests_total`

### Secondary SLOs

#### Execution Latency (P95)

**Target**: 95% of requests complete within 1 second  
**Measurement Window**: 7 days  
**Metric**: `histogram_quantile(0.95, ai_request_duration_seconds_bucket)`

#### Selector Latency (P95)

**Target**: 95% of selector requests complete within 500ms  
**Measurement Window**: 7 days  
**Metric**: `histogram_quantile(0.95, selector_request_duration_seconds_bucket)`

#### Selector Availability

**Target**: 99.9% uptime (allows ~43 minutes downtime per month)  
**Measurement Window**: 30 days  
**Metric**: `up{job="automation-service-selector"}`

## 🔥 Burn-Rate Alerting

### What is Burn-Rate Alerting?

Burn-rate alerting detects when you're consuming your error budget faster than expected. Instead of alerting on absolute thresholds, it alerts on the *rate* at which you're burning through your SLO budget.

### Why Burn-Rate?

- **Early Warning**: Detect problems before SLO is breached
- **Actionable**: Different severities for different burn rates
- **Context-Aware**: Considers both short-term spikes and long-term trends

### Burn-Rate Windows

We use **multi-window, multi-burn-rate** alerting (Google SRE Workbook pattern):

| Alert | Short Window | Long Window | Burn Rate | Budget Consumed | Severity | Response Time |
|-------|--------------|-------------|-----------|-----------------|----------|---------------|
| Fast Burn | 5 minutes | 1 hour | 14.4x | 2% in 1 hour | Critical | Immediate |
| Slow Burn | 30 minutes | 6 hours | 6x | 5% in 6 hours | Warning | 1 hour |

### Fast Burn Alert

**Trigger**: Success rate <99% in BOTH 5m AND 1h windows

**Meaning**: You're burning error budget 14.4x faster than sustainable rate. At this rate, you'll exhaust your monthly budget in ~2 days.

**Action**: Immediate investigation required. Likely ongoing incident.

**Example Scenarios**:
- Recent deployment causing errors
- Downstream service outage
- Resource exhaustion (CPU, memory, connections)

### Slow Burn Alert

**Trigger**: Success rate <99% in BOTH 30m AND 6h windows

**Meaning**: You're burning error budget 6x faster than sustainable rate. At this rate, you'll exhaust your monthly budget in ~5 days.

**Action**: Investigation within 1 hour. Plan corrective action.

**Example Scenarios**:
- Gradual degradation
- Increased error rate from specific tool
- Cache inefficiency causing timeouts

### Calculating Burn Rate

```
Burn Rate = (1 - Current Success Rate) / (1 - SLO Target)

Example:
- SLO Target: 99% (0.99)
- Current Success Rate: 95% (0.95)
- Burn Rate = (1 - 0.95) / (1 - 0.99) = 0.05 / 0.01 = 5x
```

At 5x burn rate, you'll consume your monthly error budget in ~6 days.

## 📖 Alert Runbooks

### AIExecutionErrorRateHigh

**Severity**: Warning  
**Threshold**: >5% error rate for 2 minutes  
**Impact**: Degraded user experience, potential SLO breach

#### Investigation Steps

1. **Check error distribution**:
   ```promql
   sum by (reason) (rate(ai_request_errors_total[5m]))
   ```

2. **Identify affected tools**:
   ```promql
   sum by (tool) (rate(ai_request_errors_total[5m]))
   ```

3. **Review recent changes**:
   - Check deployment history
   - Review recent configuration changes
   - Check for infrastructure changes

4. **Check dependencies**:
   - LLM service health (vLLM)
   - Database connectivity
   - Redis availability

#### Common Causes

| Error Pattern | Likely Cause | Fix |
|---------------|--------------|-----|
| `tool_not_found` | Tool registry issue | Verify tool catalog sync |
| `execution_timeout` | Slow tool or resource contention | Check tool performance, scale resources |
| `llm_error` | LLM service issue | Check vLLM logs, restart if needed |
| `validation_error` | Invalid input | Check input validation logic |

#### Mitigation

- **Immediate**: If specific tool causing errors, disable it temporarily
- **Short-term**: Increase timeouts if appropriate
- **Long-term**: Fix root cause, add retry logic, improve error handling

### AIExecutionLatencyP95High

**Severity**: Warning  
**Threshold**: P95 >1s for 5 minutes  
**Impact**: Slow user experience

#### Investigation Steps

1. **Check latency by tool**:
   ```promql
   histogram_quantile(0.95, sum by (tool, le) (rate(ai_request_duration_seconds_bucket[5m])))
   ```

2. **Check for resource contention**:
   - CPU usage
   - Memory usage
   - Disk I/O
   - Network latency

3. **Review tool execution times**:
   - Check tool-specific logs
   - Identify slow operations

#### Common Causes

- Slow database queries
- LLM inference delays
- Network latency to external services
- Resource exhaustion

#### Mitigation

- Optimize slow queries
- Add caching where appropriate
- Scale resources if needed
- Set aggressive timeouts for slow tools

### SelectorErrorBurst

**Severity**: Warning  
**Threshold**: >0 database errors in 5 minutes  
**Impact**: Degraded search, potential fallback to cache

#### Investigation Steps

1. **Check database connectivity**:
   ```bash
   docker exec opsconductor-postgres pg_isready
   ```

2. **Review database logs**:
   ```bash
   docker logs opsconductor-postgres --tail 100
   ```

3. **Check connection pool**:
   - Pool exhaustion
   - Connection leaks
   - Timeout settings

4. **Verify cache fallback**:
   ```promql
   sum by (source) (rate(selector_requests_total[5m]))
   ```

#### Common Causes

- Database connection pool exhaustion
- PostgreSQL restart or maintenance
- Network issues
- Query timeout
- Deadlocks

#### Mitigation

- Verify database health
- Check connection pool configuration
- Review slow queries
- Ensure cache is populated (graceful degradation)

### SLOBurnRateFast

**Severity**: Critical  
**Threshold**: <99% success in both 5m and 1h windows  
**Impact**: Rapid error budget consumption, potential SLO breach

#### Investigation Steps

1. **Assess scope**:
   ```promql
   sum(rate(ai_requests_total{status="success"}[5m])) / sum(rate(ai_requests_total[5m]))
   ```

2. **Identify error spike**:
   ```promql
   sum by (reason) (rate(ai_request_errors_total[5m]))
   ```

3. **Check recent deployments**:
   - Review deployment timeline
   - Check for correlation with error spike

4. **Assess impact**:
   - Number of affected users
   - Affected tools/features
   - Business impact

#### Response Actions

**Immediate (0-15 minutes)**:
1. Page on-call engineer
2. Assess if rollback needed
3. Check for ongoing incidents
4. Communicate to stakeholders

**Short-term (15-60 minutes)**:
1. Implement mitigation (rollback, disable feature, scale resources)
2. Verify mitigation effectiveness
3. Update incident status

**Long-term (post-incident)**:
1. Root cause analysis
2. Implement permanent fix
3. Update runbooks
4. Add preventive monitoring

### SLOBurnRateSlow

**Severity**: Warning  
**Threshold**: <99% success in both 30m and 6h windows  
**Impact**: Gradual error budget consumption

#### Investigation Steps

1. **Identify trend**:
   ```promql
   sum(rate(ai_requests_total{status="success"}[30m])) / sum(rate(ai_requests_total[30m]))
   ```

2. **Compare to baseline**:
   - Check historical success rate
   - Identify when degradation started

3. **Analyze error patterns**:
   - Specific tools affected?
   - Time-of-day correlation?
   - User segment affected?

#### Response Actions

**Within 1 hour**:
1. Investigate root cause
2. Assess if immediate action needed
3. Plan corrective action

**Within 4 hours**:
1. Implement fix or mitigation
2. Monitor for improvement
3. Document findings

## 🚨 On-Call Procedures

### Severity Levels

| Severity | Response Time | Escalation | Examples |
|----------|---------------|------------|----------|
| Critical | Immediate | Page on-call | SLOBurnRateFast, MetricsEndpointDown |
| Warning | 1 hour | Slack notification | AIExecutionErrorRateHigh, SelectorErrorBurst |
| Info | Next business day | Email | SelectorCacheEvictionRateHigh |

### Escalation Path

1. **Primary On-Call**: Responds within 15 minutes
2. **Secondary On-Call**: Escalate after 30 minutes if no response
3. **Engineering Manager**: Escalate for critical incidents >1 hour

### Communication

**Incident Channels**:
- **Slack**: #opsconductor-incidents
- **Status Page**: status.opsconductor.example.com
- **Email**: incidents@opsconductor.example.com

**Update Frequency**:
- Critical: Every 15 minutes
- Warning: Every hour
- Info: Daily summary

### Post-Incident Review

**Required for**:
- All critical incidents
- SLO breaches
- Incidents >1 hour duration

**Template**:
1. Timeline of events
2. Root cause analysis
3. Impact assessment
4. Mitigation actions taken
5. Lessons learned
6. Action items (with owners and due dates)

## 📊 SLO Reporting

### Weekly Report

- Current error budget remaining
- Burn rate trend
- Top error reasons
- Latency trends

### Monthly Report

- SLO compliance (met/missed)
- Error budget consumption
- Incident summary
- Improvement recommendations

### Dashboards

- **SLO Dashboard**: http://localhost:3001/d/slo-overview
- **Error Budget**: http://localhost:3001/d/error-budget
- **Incident Timeline**: http://localhost:3001/d/incidents

## 🔧 Tuning SLOs

### When to Adjust SLOs

- **Too Strict**: Constant alerts, team burnout, unrealistic expectations
- **Too Loose**: Poor user experience, no actionable alerts

### Adjustment Process

1. Analyze historical data (3+ months)
2. Calculate achievable target (e.g., 95th percentile of historical performance)
3. Propose new SLO with justification
4. Get stakeholder approval
5. Update monitoring and alerts
6. Communicate changes

### Example Adjustment

**Current**: 99% success rate  
**Historical**: 98.5% average over 3 months  
**Proposed**: 98% success rate (more achievable)  
**Justification**: Current SLO too strict, causing alert fatigue

## 📚 References

- [Google SRE Book - SLOs](https://sre.google/sre-book/service-level-objectives/)
- [Google SRE Workbook - Alerting on SLOs](https://sre.google/workbook/alerting-on-slos/)
- [Prometheus Alerting Best Practices](https://prometheus.io/docs/practices/alerting/)

---

**Last Updated**: 2024-01-20  
**Version**: 1.0.0 (PR #5)  
**Owner**: SRE Team