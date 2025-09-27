# 📊 OpsConductor ELK Stack - Centralized Logging

## 🎯 Overview

The OpsConductor ELK Stack provides centralized logging, search, and analysis capabilities for all microservices in the platform. This implementation focuses on getting all service logs centralized and searchable quickly with a minimal but functional setup.

## 🏗️ Architecture

```
┌─────────────────┐    ┌──────────────┐    ┌─────────────────┐
│   Microservices │───▶│   Filebeat   │───▶│ Elasticsearch   │
│                 │    │              │    │                 │
│ • Identity      │    │ Log Shipping │    │ Search & Store  │
│ • Asset         │    │ & Processing │    │                 │
│ • Automation    │    │              │    │                 │
│ • Communication │    │              │    │                 │
│ • AI Brain      │    │              │    │                 │
│ • Network       │    │              │    │                 │
└─────────────────┘    └──────────────┘    └─────────────────┘
                                                     │
                                                     ▼
                                           ┌─────────────────┐
                                           │     Kibana      │
                                           │                 │
                                           │ Visualization   │
                                           │ & Analysis      │
                                           └─────────────────┘
```

## 🚀 Quick Start

### 1. Deploy ELK Stack
```bash
# Deploy the complete ELK stack
./deploy-elk.sh
```

### 2. Verify Installation
```bash
# Test all components
./test-elk.sh
```

### 3. Access Kibana
- **URL:** http://localhost:5601
- **Index Pattern:** `opsconductor-logs-*`
- **Time Field:** `@timestamp`

## 📋 Components

### Elasticsearch (Port 9200)
- **Purpose:** Search and analytics engine
- **Version:** 8.8.0
- **Configuration:** Single-node cluster
- **Memory:** 1GB heap size
- **Storage:** Persistent volume for data

### Kibana (Port 5601)
- **Purpose:** Visualization and analysis interface
- **Version:** 8.8.0
- **Features:** Log discovery, dashboards, visualizations
- **Access:** Web interface at http://localhost:5601

### Filebeat
- **Purpose:** Log shipping agent
- **Version:** 8.8.0
- **Source:** Docker container logs
- **Processing:** JSON log parsing, metadata enrichment

## 🔧 Configuration

### Filebeat Configuration
```yaml
# Location: elk/filebeat/filebeat.yml
filebeat.inputs:
- type: container
  paths:
    - '/var/lib/docker/containers/*/*.log'
  processors:
    - add_docker_metadata
    - decode_json_fields
```

### Index Template
- **Pattern:** `opsconductor-logs-*`
- **Shards:** 1 (single-node setup)
- **Replicas:** 0 (development environment)
- **Refresh:** 5 seconds

## 📊 Log Structure

### Standard Log Fields
```json
{
  "@timestamp": "2024-01-15T10:30:00.000Z",
  "level": "info",
  "message": "User authentication successful",
  "service": "identity-service",
  "docker": {
    "container": {
      "name": "opsconductor-identity",
      "image": "opsconductor/identity-service:latest"
    }
  },
  "opsconductor": {
    "environment": "development",
    "stack": "opsconductor-ng"
  }
}
```

### Service-Specific Fields
Each service adds contextual information:
- **User ID:** For user-related operations
- **Request ID:** For request tracing
- **Operation:** Specific action being performed
- **Duration:** Operation timing
- **Status:** Success/failure indicators

## 🔍 Using Kibana

### 1. Initial Setup
1. Open http://localhost:5601
2. Go to **Stack Management** > **Index Patterns**
3. Create pattern: `opsconductor-logs-*`
4. Select `@timestamp` as time field

### 2. Discover Logs
1. Go to **Discover** tab
2. Select `opsconductor-logs-*` index
3. Use filters and search queries
4. Analyze log patterns and trends

### 3. Common Queries
```
# Find errors
level:error

# Filter by service
service:identity-service

# Search message content
message:"authentication failed"

# Combine filters
level:error AND service:identity-service
```

### 4. Create Dashboards
1. Go to **Dashboard** tab
2. Create visualizations for:
   - Log volume by service
   - Error rates over time
   - Response time distributions
   - Service health metrics

## 🛠️ Management Commands

### Start ELK Stack
```bash
docker-compose -f docker-compose.elk.yml up -d
```

### Stop ELK Stack
```bash
docker-compose -f docker-compose.elk.yml down
```

### View Logs
```bash
# All ELK components
docker-compose -f docker-compose.elk.yml logs -f

# Specific component
docker-compose -f docker-compose.elk.yml logs -f elasticsearch
docker-compose -f docker-compose.elk.yml logs -f kibana
docker-compose -f docker-compose.elk.yml logs -f filebeat
```

### Restart Components
```bash
# Restart all
docker-compose -f docker-compose.elk.yml restart

# Restart specific component
docker-compose -f docker-compose.elk.yml restart elasticsearch
```

## 📈 Monitoring & Health

### Health Checks
```bash
# Elasticsearch cluster health
curl http://localhost:9200/_cluster/health

# Kibana status
curl http://localhost:5601/api/status

# Check indices
curl http://localhost:9200/_cat/indices/opsconductor-logs-*
```

### Performance Monitoring
- **Elasticsearch:** Monitor heap usage, query performance
- **Kibana:** Check response times, dashboard load times
- **Filebeat:** Monitor log ingestion rates, processing delays

## 🔧 Troubleshooting

### Common Issues

#### Elasticsearch Won't Start
```bash
# Check memory limits
docker stats opsconductor-elasticsearch

# Increase memory if needed
# Edit docker-compose.elk.yml: ES_JAVA_OPTS=-Xms2g -Xmx2g
```

#### No Logs Appearing
```bash
# Check Filebeat status
docker logs opsconductor-filebeat

# Verify log paths
docker exec opsconductor-filebeat ls -la /var/lib/docker/containers/
```

#### Kibana Connection Issues
```bash
# Check Elasticsearch connectivity
docker exec opsconductor-kibana curl http://elasticsearch:9200/_cluster/health
```

### Log Levels
- **DEBUG:** Detailed debugging information
- **INFO:** General operational messages
- **WARNING:** Warning conditions
- **ERROR:** Error conditions
- **CRITICAL:** Critical error conditions

## 🚀 Next Steps

### Phase 6.2: Enhanced Features
1. **Logstash Integration:** Advanced log processing
2. **Alerting:** Set up Watcher for critical alerts
3. **Security:** Enable X-Pack security features
4. **Performance:** Optimize for production workloads

### Phase 6.3: Advanced Analytics
1. **Machine Learning:** Anomaly detection
2. **APM Integration:** Application performance monitoring
3. **Metrics:** System and application metrics
4. **Dashboards:** Comprehensive monitoring dashboards

## 📚 Resources

- **Elasticsearch Documentation:** https://www.elastic.co/guide/en/elasticsearch/reference/8.8/
- **Kibana User Guide:** https://www.elastic.co/guide/en/kibana/8.8/
- **Filebeat Reference:** https://www.elastic.co/guide/en/beats/filebeat/8.8/

---

**🎉 ELK Stack is ready for centralized logging and analysis!**