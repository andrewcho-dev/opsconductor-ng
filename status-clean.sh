#!/bin/bash

# OpsConductor Clean Architecture Status Check

echo "🔍 OpsConductor Clean Architecture Status"
echo "========================================="

# Check if containers are running
echo ""
echo "📦 Container Status:"
docker compose -f docker-compose.clean.yml ps

echo ""
echo "🔍 Service Health Checks:"

services=(
    "http://localhost:3005/health:AI Brain"
    "http://localhost:8001/health:Automation Service" 
    "http://localhost:8002/health:Asset Service"
    "http://localhost:8003/health:Network Service"
    "http://localhost:8004/health:Communication Service"
)

for service in "${services[@]}"; do
    url=$(echo $service | cut -d: -f1-2)
    name=$(echo $service | cut -d: -f3)
    
    if curl -f -s "$url" > /dev/null; then
        echo "✅ $name: Healthy"
    else
        echo "❌ $name: Not responding"
    fi
done

echo ""
echo "🏗️ Architecture Overview:"
if curl -f -s "http://localhost:3005/architecture" > /dev/null; then
    curl -s "http://localhost:3005/architecture" | python3 -m json.tool 2>/dev/null || echo "Architecture endpoint available"
else
    echo "❌ Architecture endpoint not available"
fi

echo ""
echo "📊 Quick Commands:"
echo "  View logs: docker compose -f docker-compose.clean.yml logs"
echo "  Stop system: docker compose -f docker-compose.clean.yml down"
echo "  Test intent: curl -X POST http://localhost:3005/process -H 'Content-Type: application/json' -d '{\"intent\": \"test\"}'"