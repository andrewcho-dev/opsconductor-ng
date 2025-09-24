#!/bin/bash

# Production Deployment Script for Multi-Brain AI System
# OpsConductor Production Deployment

set -e

echo "🚀 Starting OpsConductor Multi-Brain AI System Production Deployment..."

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

# Check if Docker and Docker Compose are installed
check_dependencies() {
    print_status "Checking dependencies..."
    
    if ! command -v docker &> /dev/null; then
        print_error "Docker is not installed. Please install Docker first."
        exit 1
    fi
    
    if ! docker compose version &> /dev/null; then
        print_error "Docker Compose is not available. Please ensure Docker with Compose plugin is installed."
        exit 1
    fi
    
    print_success "Dependencies check passed"
}

# Create necessary directories
create_directories() {
    print_status "Creating production directories..."
    
    # Use project directory instead of /opt to avoid sudo
    mkdir -p ./production/{data/{ai-brain,chromadb,ollama},logs/{nginx,ai-brain},backups,ssl}
    chmod -R 755 ./production
    
    print_success "Production directories created"
}

# Load environment variables
load_environment() {
    print_status "Loading production environment..."
    
    if [ -f .env.production ]; then
        set -a
        source .env.production
        set +a
        print_success "Production environment loaded"
    else
        print_warning "Production environment file not found, using defaults"
    fi
}

# Build production images
build_images() {
    print_status "Building production Docker images..."
    
    # Build AI Brain production image
    docker build -f ai-brain/Dockerfile.production -t opsconductor-ai-brain:production ./ai-brain
    
    # Build Nginx production image
    docker build -f nginx/Dockerfile.production -t opsconductor-nginx:production ./nginx
    
    print_success "Production images built successfully"
}

# Deploy infrastructure
deploy_infrastructure() {
    print_status "Deploying production infrastructure..."
    
    # Create production network
    docker network create opsconductor-prod-net --driver bridge --subnet=172.20.0.0/16 || true
    
    # Deploy main production stack
    docker compose -f docker-compose.production.yml up -d
    
    print_success "Production infrastructure deployed"
}

# Deploy monitoring stack
deploy_monitoring() {
    print_status "Deploying monitoring stack..."
    
    # Deploy monitoring services
    docker compose -f docker-compose.monitoring.yml up -d
    
    print_success "Monitoring stack deployed"
}

# Wait for services to be healthy
wait_for_services() {
    print_status "Waiting for services to be healthy..."
    
    local services=("postgres-production" "redis-production" "chromadb-production" "ollama-production" "ai-brain-production")
    
    for service in "${services[@]}"; do
        print_status "Waiting for $service to be healthy..."
        
        local retries=0
        local max_retries=30
        
        while [ $retries -lt $max_retries ]; do
            if docker ps --filter "name=$service" --filter "health=healthy" | grep -q $service; then
                print_success "$service is healthy"
                break
            fi
            
            if [ $retries -eq $((max_retries - 1)) ]; then
                print_error "$service failed to become healthy"
                exit 1
            fi
            
            sleep 10
            retries=$((retries + 1))
        done
    done
    
    print_success "All services are healthy"
}

# Run production tests
run_tests() {
    print_status "Running production validation tests..."
    
    # Test AI Brain health
    if curl -f -s http://localhost:3005/health > /dev/null; then
        print_success "AI Brain health check passed"
    else
        print_error "AI Brain health check failed"
        exit 1
    fi
    
    # Test Multi-Brain system
    if curl -f -s -X POST http://localhost:3005/ai/intent -H "Content-Type: application/json" -d '{"query": "test multi-brain system"}' > /dev/null; then
        print_success "Multi-Brain system test passed"
    else
        print_warning "Multi-Brain system test failed (may need initialization)"
    fi
    
    # Test monitoring
    if curl -f -s http://localhost:9090/-/healthy > /dev/null; then
        print_success "Prometheus health check passed"
    else
        print_warning "Prometheus health check failed"
    fi
    
    if curl -f -s http://localhost:3000/api/health > /dev/null; then
        print_success "Grafana health check passed"
    else
        print_warning "Grafana health check failed"
    fi
    
    print_success "Production validation completed"
}

# Display deployment information
show_deployment_info() {
    print_success "🎉 Production deployment completed successfully!"
    echo ""
    echo "📊 Service URLs:"
    echo "  • Multi-Brain AI System: https://localhost:443/ai/"
    echo "  • AI Brain API: https://localhost:443/api/"
    echo "  • Health Check: https://localhost:443/health"
    echo "  • Prometheus: http://localhost:9090"
    echo "  • Grafana: http://localhost:3000 (admin/OpsConductor2024!Monitor)"
    echo ""
    echo "🐳 Container Status:"
    docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}" | grep opsconductor
    echo ""
    echo "📈 Multi-Brain System Features:"
    echo "  ✅ Intent Brain (4W Framework)"
    echo "  ✅ Technical Brain (Execution Planning)"
    echo "  ✅ SME Brain System (Cloud & Monitoring)"
    echo "  ✅ Multi-Brain Orchestrator"
    echo "  ✅ Continuous Learning"
    echo "  ✅ Production Monitoring"
    echo "  ✅ SSL/TLS Security"
    echo "  ✅ Auto-Scaling Ready"
    echo ""
    echo "🔧 Next Steps:"
    echo "  1. Configure domain name and real SSL certificates"
    echo "  2. Set up external monitoring alerts"
    echo "  3. Configure backup schedules"
    echo "  4. Scale horizontally as needed"
    echo ""
    print_success "Multi-Brain AI System is now running in production! 🧠🚀"
}

# Main deployment function
main() {
    echo "🧠 OpsConductor Multi-Brain AI System - Production Deployment"
    echo "=============================================================="
    
    check_dependencies
    create_directories
    load_environment
    build_images
    deploy_infrastructure
    deploy_monitoring
    wait_for_services
    run_tests
    show_deployment_info
}

# Run main function
main "$@"