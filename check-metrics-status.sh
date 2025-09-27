#!/bin/bash

# Check Metrics Status for All OpsConductor Services

echo "🔍 Checking metrics endpoints for all OpsConductor services..."
echo ""

# Services and their ports
declare -A SERVICES=(
    ["identity-service"]=3001
    ["asset-service"]=3002
    ["automation-service"]=3003
    ["communication-service"]=3004
    ["ai-brain"]=3005
    ["network-analyzer-service"]=3006
)

# Check each service
for service in "${!SERVICES[@]}"; do
    port=${SERVICES[$service]}
    echo -n "Testing $service (port $port): "
    
    if curl -s -f http://localhost:$port/metrics > /dev/null 2>&1; then
        echo "✅ WORKING"
    else
        echo "❌ NOT AVAILABLE"
    fi
done

echo ""
echo "🎯 Checking Prometheus targets..."

# Check Prometheus targets
if curl -s http://localhost:9090/api/v1/targets | grep -q '"health":"up"'; then
    echo "✅ Prometheus is scraping targets"
else
    echo "❌ Prometheus targets not responding"
fi

echo ""
echo "📊 Quick metrics sample from identity-service:"
curl -s http://localhost:3001/metrics | grep opsconductor_http_requests_total | head -3