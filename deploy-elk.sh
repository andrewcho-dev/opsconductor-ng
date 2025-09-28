#!/bin/bash

# OpsConductor ELK Stack Deployment Script
# Phase 6: Centralized Logging Implementation

set -e

echo "🚀 Starting ELK Stack Deployment for OpsConductor..."

# Get host IP dynamically
HOST_IP=$(hostname -I | awk '{print $1}')
if [ -z "$HOST_IP" ]; then
    HOST_IP="127.0.0.1"
    echo "⚠️  Warning: Could not detect host IP, using fallback: $HOST_IP"
else
    echo "🌐 Detected host IP: $HOST_IP"
fi

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    print_error "Docker is not running. Please start Docker first."
    exit 1
fi

# Check if network exists
if ! docker network ls | grep -q "opsconductor-network"; then
    print_warning "OpsConductor network not found. Creating it..."
    docker network create opsconductor-network
    print_success "Created opsconductor-network"
fi

# Set proper permissions for Filebeat configuration
print_status "Setting up Filebeat configuration permissions..."
chmod 644 elk/filebeat/filebeat.yml

# Deploy ELK Stack
print_status "Deploying ELK Stack (Elasticsearch + Kibana + Filebeat)..."
docker-compose -f docker-compose.elk.yml up -d

# Wait for Elasticsearch to be ready
print_status "Waiting for Elasticsearch to be ready..."
timeout=300
counter=0
while ! curl -s http://$HOST_IP:9200/_cluster/health > /dev/null; do
    if [ $counter -ge $timeout ]; then
        print_error "Elasticsearch failed to start within $timeout seconds"
        exit 1
    fi
    echo -n "."
    sleep 5
    counter=$((counter + 5))
done
echo ""
print_success "Elasticsearch is ready!"

# Wait for Kibana to be ready
print_status "Waiting for Kibana to be ready..."
counter=0
while ! curl -s http://$HOST_IP:5601/api/status > /dev/null; do
    if [ $counter -ge $timeout ]; then
        print_error "Kibana failed to start within $timeout seconds"
        exit 1
    fi
    echo -n "."
    sleep 5
    counter=$((counter + 5))
done
echo ""
print_success "Kibana is ready!"

# Create index template for OpsConductor logs
print_status "Creating Elasticsearch index template..."
curl -X PUT "$HOST_IP:9200/_index_template/opsconductor-logs" \
  -H "Content-Type: application/json" \
  -d '{
    "index_patterns": ["opsconductor-logs-*"],
    "template": {
      "settings": {
        "number_of_shards": 1,
        "number_of_replicas": 0,
        "index.refresh_interval": "5s"
      },
      "mappings": {
        "properties": {
          "@timestamp": {
            "type": "date"
          },
          "message": {
            "type": "text",
            "analyzer": "standard"
          },
          "level": {
            "type": "keyword"
          },
          "service": {
            "type": "keyword"
          },
          "docker": {
            "properties": {
              "container": {
                "properties": {
                  "name": {
                    "type": "keyword"
                  },
                  "image": {
                    "type": "keyword"
                  }
                }
              }
            }
          }
        }
      }
    }
  }' > /dev/null 2>&1

print_success "Index template created!"

# Check ELK Stack status
print_status "Checking ELK Stack status..."
echo ""
echo "📊 ELK Stack Status:"
echo "==================="

# Elasticsearch
if curl -s http://$HOST_IP:9200/_cluster/health | grep -q "green\|yellow"; then
    print_success "✅ Elasticsearch: Running (http://$HOST_IP:9200)"
else
    print_error "❌ Elasticsearch: Not responding"
fi

# Kibana
if curl -s http://$HOST_IP:5601/api/status | grep -q "available"; then
    print_success "✅ Kibana: Running (http://$HOST_IP:5601)"
else
    print_error "❌ Kibana: Not responding"
fi

# Filebeat
if docker ps | grep -q "opsconductor-filebeat"; then
    print_success "✅ Filebeat: Running (log shipping active)"
else
    print_error "❌ Filebeat: Not running"
fi

echo ""
print_success "🎉 ELK Stack deployment completed!"
echo ""
echo "📋 Next Steps:"
echo "=============="
echo "1. 🌐 Access Kibana Dashboard: http://$HOST_IP:5601"
echo "2. 🔍 Create index pattern: opsconductor-logs-*"
echo "3. 📊 View logs in Discover tab"
echo "4. 📈 Create dashboards for service monitoring"
echo ""
echo "🔧 Useful Commands:"
echo "=================="
echo "• View logs: docker-compose -f docker-compose.elk.yml logs -f"
echo "• Stop ELK: docker-compose -f docker-compose.elk.yml down"
echo "• Restart: docker-compose -f docker-compose.elk.yml restart"
echo ""
print_status "ELK Stack is ready for centralized logging! 🚀"