# Monitoring Deployment Checklist

Use this checklist to verify monitoring deployment at each stage.

## 📋 Pre-Deployment Verification

### Code Review
- [ ] All files reviewed and approved
- [ ] No hardcoded credentials or secrets
- [ ] No high-cardinality labels (trace_id, user_id)
- [ ] Alert thresholds appropriate for environment
- [ ] Documentation complete and accurate

### Local Testing
- [ ] `pytest tests/monitoring/test_metrics_presence.py -v` passes (9/9)
- [ ] `./monitoring/verify-monitoring.sh` passes all checks
- [ ] Metrics endpoint reachable: `curl http://localhost:8010/metrics`
- [ ] All required metrics present (ai_*, selector_*)
- [ ] HELP and TYPE annotations present

### Docker Compose
- [ ] `docker compose -f docker-compose.yml -f monitoring/compose.monitoring.yml up -d` succeeds
- [ ] Prometheus container healthy: `docker ps | grep prometheus`
- [ ] Grafana container healthy: `docker ps | grep grafana`
- [ ] No errors in logs: `docker logs opsconductor-prometheus`

## 🚀 Development Environment

### Prometheus Setup
- [ ] Prometheus accessible at http://localhost:9090
- [ ] Targets page shows all services UP: http://localhost:9090/targets
- [ ] Rules page shows all alert groups: http://localhost:9090/rules
- [ ] No evaluation errors in rules
- [ ] Test query works: `ai_requests_total`

### Grafana Setup
- [ ] Grafana accessible at http://localhost:3001
- [ ] Login successful (admin/opsconductor)
- [ ] Prometheus datasource configured
- [ ] Execution dashboard loads
- [ ] Selector dashboard loads
- [ ] All panels render (no "No data" errors after traffic)

### Generate Test Traffic
```bash
# Generate some requests to populate metrics
curl -X POST http://localhost:8010/ai/execute \
  -H "Content-Type: application/json" \
  -d '{"input": "ping", "tool": "echo"}'

# Verify metrics updated
curl http://localhost:8010/metrics | grep ai_requests_total
```

- [ ] Metrics increment after requests
- [ ] Dashboards show data
- [ ] Latency histograms populate

## 🧪 Staging Environment

### Infrastructure
- [ ] Prometheus server deployed
- [ ] Grafana server deployed
- [ ] Network connectivity verified
- [ ] DNS/service discovery configured
- [ ] Firewall rules allow scraping

### Configuration
- [ ] Prometheus config updated with staging targets
- [ ] Alert rules loaded: `promtool check rules opsconductor.rules.yml`
- [ ] Grafana datasource points to staging Prometheus
- [ ] Dashboards imported successfully

### Alerting
- [ ] Slack webhook configured
- [ ] Test alert fires: `curl -X POST http://prometheus:9090/-/reload`
- [ ] Alert notification received in Slack
- [ ] Alert resolves when condition clears

### Monitoring
- [ ] Scrape targets all UP
- [ ] Metrics flowing (check Prometheus graph)
- [ ] Dashboards show staging data
- [ ] No scrape errors in Prometheus logs

## 🏭 Production Environment

### Pre-Production
- [ ] Change management ticket approved
- [ ] Deployment window scheduled
- [ ] Rollback plan documented
- [ ] On-call engineer notified
- [ ] Stakeholders informed

### Infrastructure
- [ ] Prometheus HA setup (if required)
- [ ] Grafana HA setup (if required)
- [ ] Load balancer configured
- [ ] TLS certificates installed
- [ ] Backup strategy implemented

### Security
- [ ] Authentication enabled on Prometheus
- [ ] LDAP/SAML configured on Grafana
- [ ] TLS enabled for all endpoints
- [ ] Network policies applied
- [ ] Audit logging enabled
- [ ] Security scan passed

### Configuration
- [ ] Production targets configured
- [ ] Alert thresholds tuned for prod traffic
- [ ] Retention period set (15 days)
- [ ] Storage capacity verified
- [ ] Backup schedule configured

### Alerting
- [ ] PagerDuty integration configured
- [ ] Escalation policies defined
- [ ] On-call schedule populated
- [ ] Runbooks linked in alerts
- [ ] Test page sent and acknowledged

### Validation
- [ ] All targets UP and scraping
- [ ] Metrics flowing correctly
- [ ] Dashboards render production data
- [ ] Alerts evaluate without errors
- [ ] No performance impact on services

### Documentation
- [ ] Production URLs documented
- [ ] Access procedures documented
- [ ] On-call procedures updated
- [ ] Runbooks reviewed and approved
- [ ] Team trained on dashboards

## 📊 Post-Deployment

### Immediate (0-24 hours)
- [ ] Monitor Prometheus resource usage
- [ ] Monitor Grafana resource usage
- [ ] Verify scrape success rate >99%
- [ ] Check for alert storms
- [ ] Validate dashboard accuracy

### Week 1
- [ ] Review alert frequency
- [ ] Tune thresholds if needed
- [ ] Collect team feedback
- [ ] Document any issues
- [ ] Update runbooks based on incidents

### Week 2
- [ ] SLO compliance review
- [ ] Error budget calculation
- [ ] Alert effectiveness review
- [ ] Dashboard usage metrics
- [ ] Performance optimization

## 🔧 Troubleshooting Checklist

### Metrics Not Appearing
- [ ] Service is running: `docker ps`
- [ ] Metrics endpoint accessible: `curl http://service:port/metrics`
- [ ] Prometheus scraping: Check targets page
- [ ] No scrape errors in Prometheus logs
- [ ] Firewall allows traffic

### Dashboards Show "No Data"
- [ ] Prometheus datasource configured
- [ ] Prometheus has data: Test query in Explore
- [ ] Time range appropriate (not too far in past)
- [ ] Metric names correct in queries
- [ ] Labels match actual metrics

### Alerts Not Firing
- [ ] Alert rules loaded: Check rules page
- [ ] Alert condition actually met: Test query
- [ ] Alert duration passed (e.g., "for: 2m")
- [ ] Alertmanager configured (if using)
- [ ] Notification channels configured

### High Resource Usage
- [ ] Check metric cardinality: `prometheus_tsdb_symbol_table_size_bytes`
- [ ] Review scrape intervals (too frequent?)
- [ ] Check retention period (too long?)
- [ ] Look for high-cardinality labels
- [ ] Consider recording rules for expensive queries

## 📝 Sign-Off

### Development
- [ ] Deployed by: _________________ Date: _________
- [ ] Verified by: _________________ Date: _________
- [ ] Issues: _____________________________________

### Staging
- [ ] Deployed by: _________________ Date: _________
- [ ] Verified by: _________________ Date: _________
- [ ] Issues: _____________________________________

### Production
- [ ] Deployed by: _________________ Date: _________
- [ ] Verified by: _________________ Date: _________
- [ ] Approved by: _________________ Date: _________
- [ ] Issues: _____________________________________

## 🎯 Success Criteria

### Metrics
- ✅ All required metrics present (ai_*, selector_*)
- ✅ Scrape success rate >99%
- ✅ No scrape timeouts
- ✅ Metric cardinality <10,000 series

### Alerts
- ✅ All alert rules loaded
- ✅ No evaluation errors
- ✅ Test alerts fire correctly
- ✅ Notifications delivered <1 minute

### Dashboards
- ✅ All panels render data
- ✅ Query response time <5s
- ✅ No "No data" errors
- ✅ Annotations show alerts

### Performance
- ✅ Prometheus CPU <50%
- ✅ Prometheus memory <2GB
- ✅ Grafana response time <2s
- ✅ No impact on service performance

## 📚 References

- [Monitoring README](../docs/MONITORING_README.md)
- [SLOs and Alerts](../docs/SLOS_AND_ALERTS.md)
- [Architecture](./ARCHITECTURE.md)
- [Verification Script](./verify-monitoring.sh)

---

**Version**: 1.0.0  
**Last Updated**: 2024-01-20  
**Owner**: SRE Team