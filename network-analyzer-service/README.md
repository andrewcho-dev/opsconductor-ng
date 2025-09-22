# OpsConductor Network Analyzer Service

The Network Analyzer Service provides comprehensive packet analysis and network troubleshooting capabilities for the OpsConductor platform. This service enables deep network inspection, real-time monitoring, protocol analysis, and AI-driven network diagnostics.

## Features

### 🔍 Packet Analysis
- **Live Packet Capture**: Real-time packet sniffing using tcpdump, tshark, and scapy
- **BPF Filtering**: Advanced Berkeley Packet Filter support for targeted capture
- **Protocol Decoding**: Deep packet inspection with protocol-specific analysis
- **Traffic Statistics**: Comprehensive network traffic metrics and visualization

### 📊 Real-time Network Monitoring
- **Bandwidth Monitoring**: Track network utilization and throughput
- **Latency Analysis**: Monitor network latency and response times
- **Connection Tracking**: Active connection monitoring and analysis
- **Alert System**: Configurable thresholds with real-time notifications

### 🔬 Protocol Analysis
- **Multi-Protocol Support**: TCP, UDP, HTTP/HTTPS, DNS, ICMP, SSH, FTP, SMTP, SNMP
- **Performance Metrics**: Protocol-specific performance analysis
- **Issue Detection**: Automatic identification of protocol-level problems
- **Security Analysis**: Detection of suspicious protocol behavior

### 🤖 AI-Powered Analysis
- **Anomaly Detection**: Machine learning-based network anomaly identification
- **Intelligent Diagnosis**: AI-driven root cause analysis
- **Automated Remediation**: Smart suggestions for network issue resolution
- **Pattern Recognition**: Advanced traffic pattern analysis

### 🌐 Remote Analysis
- **Agent Deployment**: Deploy lightweight analysis agents to remote targets
- **Distributed Monitoring**: Monitor multiple network segments simultaneously
- **Cross-Platform Support**: Linux and Windows agent support
- **Centralized Management**: Unified control of all remote agents

## API Endpoints

### Packet Analysis
- `POST /api/v1/network/capture` - Start packet capture
- `GET /api/v1/network/capture/{session_id}` - Get capture results
- `DELETE /api/v1/network/capture/{session_id}` - Stop capture session

### Network Monitoring
- `POST /api/v1/monitoring/start` - Start network monitoring
- `GET /api/v1/monitoring/status/{session_id}` - Get monitoring status
- `POST /api/v1/monitoring/stop/{session_id}` - Stop monitoring session

### Protocol Analysis
- `POST /api/v1/analysis/protocol` - Analyze specific protocols
- `GET /api/v1/analysis/protocols` - List supported protocols
- `POST /api/v1/analysis/performance` - Performance analysis

### AI Analysis
- `POST /api/v1/analysis/ai/diagnose` - AI-powered network diagnosis
- `POST /api/v1/analysis/ai/anomaly` - Anomaly detection
- `GET /api/v1/analysis/ai/suggestions/{analysis_id}` - Get AI suggestions

### Remote Analysis
- `POST /api/v1/remote/deploy` - Deploy remote agent
- `GET /api/v1/remote/agents` - List active agents
- `POST /api/v1/remote/analyze` - Start remote analysis
- `DELETE /api/v1/remote/agent/{agent_id}` - Remove remote agent

### WebSocket Endpoints
- `WS /ws/monitoring/{session_id}` - Real-time monitoring updates
- `WS /ws/analysis/{session_id}` - Live analysis results

## Configuration

### Environment Variables
```bash
# Service Configuration
NETWORK_ANALYZER_PORT=3006
NETWORK_ANALYZER_HOST=0.0.0.0

# Database Configuration
DATABASE_URL=postgresql://user:password@postgres:5432/opsconductor
REDIS_URL=redis://redis:6379/0

# Service URLs
IDENTITY_SERVICE_URL=http://identity-service:3001
ASSET_SERVICE_URL=http://asset-service:3002
AUTOMATION_SERVICE_URL=http://automation-service:3003
COMMUNICATION_SERVICE_URL=http://communication-service:3004
AI_SERVICE_URL=http://ai-service:3005

# Analysis Configuration
MAX_CAPTURE_DURATION=3600  # Maximum capture duration in seconds
MAX_PACKET_COUNT=100000    # Maximum packets per capture
DEFAULT_INTERFACE=eth0     # Default network interface
ENABLE_AI_ANALYSIS=true    # Enable AI-powered analysis
```

### Docker Configuration
The service requires special network capabilities for packet capture:
```yaml
cap_add:
  - NET_RAW
  - NET_ADMIN
```

## Usage Examples

### Basic Packet Capture
```python
import httpx

# Start packet capture
response = httpx.post("http://localhost:3006/api/v1/network/capture", json={
    "interface": "eth0",
    "filter": "tcp port 80",
    "duration": 60,
    "max_packets": 1000
})
session_id = response.json()["session_id"]

# Get results
results = httpx.get(f"http://localhost:3006/api/v1/network/capture/{session_id}")
```

### Real-time Monitoring
```python
import websockets
import json

async def monitor_network():
    uri = "ws://localhost:3006/ws/monitoring/session123"
    async with websockets.connect(uri) as websocket:
        async for message in websocket:
            data = json.loads(message)
            print(f"Bandwidth: {data['bandwidth_mbps']} Mbps")
            print(f"Latency: {data['latency_ms']} ms")
```

### AI-Powered Diagnosis
```python
# Submit network data for AI analysis
response = httpx.post("http://localhost:3006/api/v1/analysis/ai/diagnose", json={
    "symptoms": ["high latency", "packet loss"],
    "network_data": {
        "interface": "eth0",
        "duration": 300
    }
})

diagnosis = response.json()
print(f"Issue: {diagnosis['issue']}")
print(f"Confidence: {diagnosis['confidence']}")
print(f"Suggestions: {diagnosis['suggestions']}")
```

### Remote Agent Deployment
```python
# Deploy agent to remote target
response = httpx.post("http://localhost:3006/api/v1/remote/deploy", json={
    "target_id": "server-001",
    "analysis_type": "comprehensive",
    "duration": 1800
})

agent_id = response.json()["agent_id"]
print(f"Agent deployed: {agent_id}")
```

## Security Considerations

### Network Permissions
- The service requires `NET_RAW` and `NET_ADMIN` capabilities for packet capture
- Consider using `network_mode: host` for enhanced packet capture capabilities
- Implement proper firewall rules to restrict access

### Data Privacy
- Packet data may contain sensitive information
- Implement data retention policies
- Consider encryption for stored packet data
- Ensure compliance with privacy regulations

### Access Control
- All endpoints are protected by OpsConductor's RBAC system
- Requires appropriate permissions for network analysis operations
- Audit all network analysis activities

## Troubleshooting

### Common Issues

**Permission Denied for Packet Capture**
```bash
# Ensure container has required capabilities
docker run --cap-add=NET_RAW --cap-add=NET_ADMIN ...
```

**No Network Interface Found**
```bash
# List available interfaces
ip link show
# Update DEFAULT_INTERFACE environment variable
```

**High Memory Usage**
```bash
# Reduce packet capture limits
MAX_PACKET_COUNT=10000
MAX_CAPTURE_DURATION=300
```

### Logs and Debugging
```bash
# View service logs
docker logs opsconductor-network-analyzer

# Enable debug logging
export LOG_LEVEL=DEBUG
```

## Integration with OpsConductor

The Network Analyzer Service integrates seamlessly with other OpsConductor services:

- **Identity Service**: Authentication and authorization
- **Asset Service**: Target asset management for remote analysis
- **Automation Service**: Automated remediation based on analysis results
- **Communication Service**: Alert notifications and reporting
- **AI Service**: Enhanced AI-powered analysis capabilities

## Performance Considerations

### Resource Requirements
- **CPU**: 2+ cores recommended for real-time analysis
- **Memory**: 4GB+ RAM for large packet captures
- **Storage**: SSD recommended for packet data storage
- **Network**: Dedicated network interface for monitoring

### Optimization Tips
- Use BPF filters to reduce capture overhead
- Implement packet sampling for high-traffic environments
- Configure appropriate buffer sizes for your network load
- Monitor service resource usage regularly

## Contributing

When contributing to the Network Analyzer Service:

1. Follow OpsConductor coding standards
2. Add comprehensive tests for new features
3. Update documentation for API changes
4. Consider security implications of network analysis features
5. Test with various network configurations

## License

This service is part of the OpsConductor platform and follows the same licensing terms.