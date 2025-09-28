# OpsConductor Grafana Dashboards

This directory contains comprehensive Grafana dashboards for monitoring the OpsConductor V3 platform.

## 🎯 Dashboard Overview

### 1. **OpsConductor Services Overview** 
- **URL**: http://YOUR_HOST_IP:3200/d/opsconductor-services-overview/opsconductor-services-overview
- **Purpose**: High-level overview of all OpsConductor services
- **Key Metrics**:
  - HTTP request rates across all services
  - Service health status (UP/DOWN)
  - Request duration percentiles (95th, 50th)
  - Request distribution by service (pie chart)
  - Service uptime tracking
  - Database and Redis health monitoring

### 2. **OpsConductor Service Details**
- **URL**: http://YOUR_HOST_IP:3200/d/opsconductor-service-details/opsconductor-service-details
- **Purpose**: Deep-dive monitoring for individual services
- **Features**:
  - Service selector dropdown (templated dashboard)
  - Detailed endpoint-level metrics
  - HTTP status code breakdown (2xx, 4xx, 5xx)
  - Service health components (overall, database, redis)
  - Database query performance analysis
  - Redis operation success/failure rates
- **Usage**: Select a service from the dropdown to view detailed metrics

### 3. **OpsConductor Infrastructure**
- **URL**: http://YOUR_HOST_IP:3200/d/opsconductor-infrastructure/opsconductor-infrastructure
- **Purpose**: System-level infrastructure monitoring
- **Key Metrics**:
  - CPU usage percentage
  - Memory utilization
  - Disk usage monitoring
  - Network I/O (receive/transmit)
  - Service availability status
  - Service instance counts

## 🔧 Access Information

- **Grafana URL**: http://YOUR_HOST_IP:3200
- **Username**: admin
- **Password**: admin123
- **Prometheus Datasource**: Automatically configured and connected

## 📊 Custom OpsConductor Metrics

All dashboards utilize custom `opsconductor_*` metrics:

### HTTP Metrics
- `opsconductor_http_requests_total` - Total HTTP requests with labels (service, method, endpoint, status_code)
- `opsconductor_http_request_duration_seconds` - HTTP request duration histogram

### Service Health Metrics
- `opsconductor_service_health` - Service health status (overall, database, redis components)
- `opsconductor_service_uptime_seconds` - Service uptime in seconds

### Database Metrics
- `opsconductor_database_query_duration_seconds` - Database query duration histogram

### Redis Metrics
- `opsconductor_redis_operations_total` - Redis operations with success/error tracking

## 🚀 Services Monitored

All 6 OpsConductor services are fully monitored:

1. **identity-service** (port 3001)
2. **asset-service** (port 3002) 
3. **automation-service** (port 3003)
4. **communication-service** (port 3004)
5. **ai-brain** (port 3005)
6. **network-analyzer-service** (port 3006)

## 📈 Dashboard Features

### Real-time Monitoring
- 5-second refresh rate for live monitoring
- Auto-refreshing panels with current data
- Time range selector (default: last 1 hour)

### Interactive Elements
- Service selector in Service Details dashboard
- Drill-down capabilities between dashboards
- Hover tooltips with detailed metric information
- Legend controls for showing/hiding specific metrics

### Visual Indicators
- Color-coded health status (Green=UP, Red=DOWN)
- Threshold-based alerting colors
- Percentage-based visualizations for resource usage
- Histogram visualizations for performance metrics

## 🔍 Troubleshooting

### Dashboard Not Loading Data
1. Verify Prometheus is running: http://YOUR_HOST_IP:9090
2. Check service metrics endpoints: http://YOUR_HOST_IP:300X/metrics
3. Verify Prometheus is scraping targets: http://YOUR_HOST_IP:9090/targets

### Missing Metrics
1. Ensure all services have `prometheus_client==0.19.0` installed
2. Check service logs for metrics initialization errors
3. Verify BaseService integration in each service

### Performance Issues
1. Adjust time ranges for better performance
2. Reduce refresh rates if needed
3. Check Prometheus query performance in Explore tab

## 🎨 Customization

### Adding New Panels
1. Edit dashboard JSON files in this directory
2. Re-import using Grafana API or UI
3. Use existing metric patterns for consistency

### Creating Alerts
1. Use Grafana alerting features
2. Set thresholds based on OpsConductor SLAs
3. Configure notification channels as needed

## 📝 Maintenance

### Dashboard Updates
- Dashboard JSON files are version controlled
- Use `import-dashboard.sh` script for bulk imports
- Backup existing dashboards before major changes

### Metric Retention
- Prometheus retention configured in monitoring stack
- Consider long-term storage for historical analysis
- Regular cleanup of old dashboard versions

---

**Phase 4 Status**: ✅ **COMPLETE** - All OpsConductor dashboards successfully deployed and operational!