# OpsConductor AI System V2 - Quick Start Guide

## 🚀 Quick Start (5 Minutes)

### 1. Deploy the System
```bash
# Make deployment script executable (if needed)
chmod +x deploy-ai-v2.sh

# Run deployment
./deploy-ai-v2.sh
```

### 2. Test Basic Functionality
```bash
# Quick test
curl -X POST http://localhost:3000/api/v1/ai/chat \
  -H "Content-Type: application/json" \
  -d '{"query": "Hello, what can you do?"}'

# Full test suite
python3 test_ai_system_v2.py
```

### 3. Access the Dashboard
```bash
# Get auth token
TOKEN=$(curl -s -X POST http://localhost:3000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"admin123"}' | \
  grep -o '"token":"[^"]*' | cut -d'"' -f4)

# Get dashboard data
curl -H "Authorization: Bearer $TOKEN" \
  http://localhost:3000/api/v1/ai/monitoring/dashboard | python3 -m json.tool
```

## 📝 Basic Usage Examples

### Chat with AI
```python
import httpx
import asyncio

async def chat_with_ai():
    # Login
    async with httpx.AsyncClient() as client:
        login = await client.post(
            "http://localhost:3000/api/v1/auth/login",
            json={"username": "admin", "password": "admin123"}
        )
        token = login.json()["data"]["token"]
        
        # Chat
        response = await client.post(
            "http://localhost:3000/api/v1/ai/chat",
            json={"query": "List all targets"},
            headers={"Authorization": f"Bearer {token}"}
        )
        print(response.json())

asyncio.run(chat_with_ai())
```

### Submit Feedback
```bash
curl -X POST http://localhost:3000/api/v1/ai/feedback \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "interaction_id": "int_123456",
    "rating": 5,
    "comment": "Very helpful response!"
  }'
```

### Check AI Health
```bash
curl -H "Authorization: Bearer $TOKEN" \
  http://localhost:3000/api/v1/ai/health
```

## 🎯 Common Use Cases

### 1. Infrastructure Management
```json
{
  "query": "Show me all Linux servers in production"
}
{
  "query": "Create a new target named 'web-server-01' with IP 192.168.1.100"
}
{
  "query": "Check SSH service on all database servers"
}
```

### 2. Automation & Jobs
```json
{
  "query": "Run the backup job on all database servers"
}
{
  "query": "Schedule maintenance job every Sunday at 2 AM"
}
{
  "query": "Show me failed job executions from last 24 hours"
}
```

### 3. Troubleshooting
```json
{
  "query": "Help me troubleshoot connection timeout issues"
}
{
  "query": "What's the health status of the automation service?"
}
{
  "query": "Show me recent error logs"
}
```

## 📊 Monitor Performance

### View Real-time Metrics
```bash
# Dashboard
curl -H "Authorization: Bearer $TOKEN" \
  http://localhost:3000/api/v1/ai/monitoring/dashboard

# Specific service
curl -H "Authorization: Bearer $TOKEN" \
  http://localhost:3000/api/v1/ai/monitoring/service/ai_command
```

### Check Circuit Breaker Status
Look for `circuit_breaker` field in health check:
```bash
curl -H "Authorization: Bearer $TOKEN" \
  http://localhost:3000/api/v1/ai/health | \
  python3 -c "import sys, json; data=json.load(sys.stdin); print(json.dumps(data['services'], indent=2))"
```

### Reset Circuit Breaker (Admin Only)
```bash
curl -X POST -H "Authorization: Bearer $TOKEN" \
  http://localhost:3000/api/v1/ai/circuit-breaker/reset/ai_command
```

## 🔧 Troubleshooting

### Service Not Responding
```bash
# Check service health
docker compose ps
docker compose logs api-gateway --tail 50
docker compose logs ai-command --tail 50

# Restart services
docker compose restart api-gateway ai-command
```

### Slow Responses
```bash
# Check cache hit rate
curl -H "Authorization: Bearer $TOKEN" \
  http://localhost:3000/api/v1/ai/monitoring/dashboard | \
  grep -o '"cache_hit_rate":[0-9.]*'
```

### High Error Rate
```bash
# Check circuit breaker status
curl -H "Authorization: Bearer $TOKEN" \
  http://localhost:3000/api/v1/ai/health | \
  grep -o '"circuit_breaker":"[^"]*"'

# View recent alerts
curl -H "Authorization: Bearer $TOKEN" \
  http://localhost:3000/api/v1/ai/monitoring/dashboard | \
  python3 -c "import sys, json; data=json.load(sys.stdin); [print(a['message']) for a in data.get('analysis',{}).get('alerts',[])]"
```

## 📚 Key Features

### ✨ Intelligent Routing
- Automatically routes queries to the right service
- Load balances between multiple instances
- Fails over when services are down

### 🛡️ Circuit Breakers
- Prevents cascading failures
- Automatically recovers when service is healthy
- Manual reset available for admins

### 📈 Continuous Learning
- Learns from successful interactions
- Improves responses over time
- Integrates user feedback

### 📊 Real-time Monitoring
- Dashboard with live metrics
- Alert generation for issues
- Performance recommendations

### 💾 Smart Caching
- Caches successful responses
- Reduces latency for common queries
- Configurable TTL

## 🔗 Useful Links

- **Architecture**: [AI_SYSTEM_V2_ARCHITECTURE.md](AI_SYSTEM_V2_ARCHITECTURE.md)
- **Implementation**: [AI_V2_IMPLEMENTATION_SUMMARY.md](AI_V2_IMPLEMENTATION_SUMMARY.md)
- **Test Suite**: [test_ai_system_v2.py](test_ai_system_v2.py)
- **Deployment**: [deploy-ai-v2.sh](deploy-ai-v2.sh)

## 💡 Tips

1. **Monitor regularly**: Check dashboard daily for insights
2. **Submit feedback**: Help the system learn and improve
3. **Use caching**: Repeat common queries to benefit from cache
4. **Check health**: Monitor service health before critical operations
5. **Review alerts**: Act on monitoring recommendations

## 🎉 Ready to Go!

Your AI System V2 is now ready. Start with simple queries and gradually explore more complex operations. The system will learn and improve as you use it!

Need help? Check the full documentation or run:
```json
{"query": "help"}
```