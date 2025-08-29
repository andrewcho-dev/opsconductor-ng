#!/bin/bash

# System Health Check
# Verifies all services are running and healthy

set -e

echo "🏥 SYSTEM HEALTH CHECK"
echo "====================="

# Check Docker containers
echo "📋 Container Status:"
docker ps --format "table {{.Names}}\t{{.Status}}" | grep opsconductor

echo
echo "🔍 Health Endpoint Tests:"

# Test all service health endpoints
services=(
    "3001:auth-service"
    "3002:user-service" 
    "3004:credentials-service"
    "3005:targets-service"
    "3006:jobs-service"
    "3007:executor-service"
    "3008:scheduler-service"
    "3009:notification-service"
    "3010:discovery-service"
)

healthy_count=0
total_count=${#services[@]}

for service in "${services[@]}"; do
    port="${service%%:*}"
    name="${service##*:}"
    
    if response=$(curl -s --max-time 3 "http://localhost:$port/health" 2>/dev/null); then
        if echo "$response" | grep -q '"status":"healthy"'; then
            echo "✅ $name (port $port): HEALTHY"
            healthy_count=$((healthy_count + 1))
        else
            echo "⚠️  $name (port $port): UNHEALTHY - $response"
        fi
    else
        echo "❌ $name (port $port): UNREACHABLE"
    fi
done

echo
echo "📊 Health Summary:"
echo "Healthy Services: $healthy_count/$total_count"

if [[ $healthy_count -eq $total_count ]]; then
    echo "🎉 ALL SERVICES HEALTHY!"
    exit 0
else
    echo "⚠️  Some services are unhealthy"
    exit 1
fi