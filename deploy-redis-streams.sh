#!/bin/bash

# Redis Streams Deployment Script for OpsConductor
# Deploys enhanced Redis Streams with consumer groups, monitoring, and dead letter queues

set -euo pipefail

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Configuration
COMPOSE_FILE="docker-compose.redis-streams.yml"
PROJECT_NAME="opsconductor-streams"
REDIS_STREAMS_PORT=6380
MONITOR_PORT=8090
HEALTH_CHECK_TIMEOUT=60
DEPLOYMENT_LOG="redis-streams-deployment.log"

# Logging function
log() {
    echo -e "${BLUE}[$(date +'%Y-%m-%d %H:%M:%S')]${NC} $1" | tee -a "$DEPLOYMENT_LOG"
}

error() {
    echo -e "${RED}[ERROR]${NC} $1" | tee -a "$DEPLOYMENT_LOG"
}

success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1" | tee -a "$DEPLOYMENT_LOG"
}

warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1" | tee -a "$DEPLOYMENT_LOG"
}

info() {
    echo -e "${CYAN}[INFO]${NC} $1" | tee -a "$DEPLOYMENT_LOG"
}

# Function to check if command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Function to check if port is available
check_port() {
    local port=$1
    if lsof -Pi :$port -sTCP:LISTEN -t >/dev/null 2>&1; then
        return 1
    else
        return 0
    fi
}

# Function to wait for service health
wait_for_service() {
    local service_name=$1
    local health_check_cmd=$2
    local timeout=${3:-60}
    local interval=5
    local elapsed=0

    log "Waiting for $service_name to be healthy..."
    
    while [ $elapsed -lt $timeout ]; do
        if eval "$health_check_cmd" >/dev/null 2>&1; then
            success "$service_name is healthy!"
            return 0
        fi
        
        sleep $interval
        elapsed=$((elapsed + interval))
        echo -n "."
    done
    
    error "$service_name failed to become healthy within ${timeout}s"
    return 1
}

# Function to check Redis Streams connectivity
check_redis_streams() {
    docker exec opsconductor-redis-streams redis-cli -a "opsconductor-streams-2024" ping 2>/dev/null | grep -q "PONG"
}

# Function to check monitor dashboard
check_monitor() {
    curl -f http://localhost:$MONITOR_PORT/health >/dev/null 2>&1
}

# Function to display deployment banner
show_banner() {
    echo -e "${PURPLE}"
    echo "╔══════════════════════════════════════════════════════════════╗"
    echo "║                                                              ║"
    echo "║           🚀 PHASE 7: REDIS STREAMS DEPLOYMENT 🚀           ║"
    echo "║                                                              ║"
    echo "║  Enterprise Message Streaming with Consumer Groups          ║"
    echo "║  • Redis Streams with persistence and durability            ║"
    echo "║  • Consumer groups for load balancing                       ║"
    echo "║  • Message acknowledgments and retry logic                  ║"
    echo "║  • Dead letter queues for failed messages                   ║"
    echo "║  • Real-time monitoring dashboard                           ║"
    echo "║                                                              ║"
    echo "╚══════════════════════════════════════════════════════════════╝"
    echo -e "${NC}"
}

# Function to check prerequisites
check_prerequisites() {
    log "Checking prerequisites..."
    
    # Check if Docker is installed and running
    if ! command_exists docker; then
        error "Docker is not installed. Please install Docker first."
        exit 1
    fi
    
    if ! docker info >/dev/null 2>&1; then
        error "Docker is not running. Please start Docker first."
        exit 1
    fi
    
    # Check if Docker Compose is available
    if ! command_exists docker-compose && ! docker compose version >/dev/null 2>&1; then
        error "Docker Compose is not available. Please install Docker Compose."
        exit 1
    fi
    
    # Check if required files exist
    if [[ ! -f "$COMPOSE_FILE" ]]; then
        error "Docker Compose file $COMPOSE_FILE not found!"
        exit 1
    fi
    
    if [[ ! -d "redis-streams" ]]; then
        error "Redis Streams directory not found!"
        exit 1
    fi
    
    if [[ ! -f "shared/redis_streams.py" ]]; then
        error "Redis Streams library not found!"
        exit 1
    fi
    
    # Check if ports are available
    if ! check_port $REDIS_STREAMS_PORT; then
        warning "Port $REDIS_STREAMS_PORT is already in use. Redis Streams may conflict."
    fi
    
    if ! check_port $MONITOR_PORT; then
        warning "Port $MONITOR_PORT is already in use. Monitor dashboard may conflict."
    fi
    
    # Check if OpsConductor network exists
    if ! docker network ls | grep -q "opsconductor-net"; then
        log "Creating OpsConductor network..."
        docker network create opsconductor-net
    fi
    
    success "Prerequisites check completed"
}

# Function to build images
build_images() {
    log "Building Redis Streams images..."
    
    # Build processor image
    log "Building message processor image..."
    docker build -t opsconductor-streams-processor:latest -f redis-streams/Dockerfile .
    
    # Build monitor image
    log "Building monitor dashboard image..."
    docker build -t opsconductor-streams-monitor:latest -f redis-streams/Dockerfile.monitor .
    
    success "Images built successfully"
}

# Function to deploy services
deploy_services() {
    log "Deploying Redis Streams services..."
    
    # Deploy using Docker Compose
    if command_exists docker-compose; then
        docker-compose -f "$COMPOSE_FILE" -p "$PROJECT_NAME" up -d
    else
        docker compose -f "$COMPOSE_FILE" -p "$PROJECT_NAME" up -d
    fi
    
    success "Services deployed"
}

# Function to verify deployment
verify_deployment() {
    log "Verifying Redis Streams deployment..."
    
    # Wait for Redis Streams to be healthy
    if ! wait_for_service "Redis Streams" "check_redis_streams" $HEALTH_CHECK_TIMEOUT; then
        error "Redis Streams deployment failed"
        return 1
    fi
    
    # Wait for monitor dashboard
    if ! wait_for_service "Monitor Dashboard" "check_monitor" $HEALTH_CHECK_TIMEOUT; then
        warning "Monitor dashboard is not responding, but Redis Streams is operational"
    fi
    
    # Check if processor is running
    if docker ps | grep -q "opsconductor-streams-processor"; then
        success "Message processor is running"
    else
        warning "Message processor may not be running properly"
    fi
    
    success "Deployment verification completed"
}

# Function to test Redis Streams functionality
test_streams() {
    log "Testing Redis Streams functionality..."
    
    # Test basic Redis operations
    log "Testing Redis connectivity..."
    if docker exec opsconductor-redis-streams redis-cli -a "opsconductor-streams-2024" ping | grep -q "PONG"; then
        success "Redis connectivity test passed"
    else
        error "Redis connectivity test failed"
        return 1
    fi
    
    # Test stream creation
    log "Testing stream creation..."
    docker exec opsconductor-redis-streams redis-cli -a "opsconductor-streams-2024" XADD "test:stream" "*" "event" "test" "timestamp" "$(date +%s)" >/dev/null
    
    # Test stream reading
    log "Testing stream reading..."
    local stream_length=$(docker exec opsconductor-redis-streams redis-cli -a "opsconductor-streams-2024" XLEN "test:stream")
    if [[ "$stream_length" -gt 0 ]]; then
        success "Stream operations test passed"
    else
        error "Stream operations test failed"
        return 1
    fi
    
    # Cleanup test stream
    docker exec opsconductor-redis-streams redis-cli -a "opsconductor-streams-2024" DEL "test:stream" >/dev/null
    
    success "Redis Streams functionality tests completed"
}

# Function to display deployment summary
show_summary() {
    echo -e "\n${GREEN}╔══════════════════════════════════════════════════════════════╗${NC}"
    echo -e "${GREEN}║                    🎉 DEPLOYMENT COMPLETE! 🎉                ║${NC}"
    echo -e "${GREEN}╚══════════════════════════════════════════════════════════════╝${NC}"
    
    echo -e "\n${CYAN}📊 REDIS STREAMS SERVICES:${NC}"
    echo -e "  🔴 Redis Streams:     http://localhost:$REDIS_STREAMS_PORT"
    echo -e "  📊 Monitor Dashboard: http://localhost:$MONITOR_PORT"
    echo -e "  ⚙️  Message Processor: Running in background"
    
    echo -e "\n${CYAN}🔧 SERVICE STATUS:${NC}"
    docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}" | grep -E "(redis-streams|streams-processor|streams-monitor)"
    
    echo -e "\n${CYAN}📈 QUICK STATS:${NC}"
    
    # Get Redis info
    local redis_info=$(docker exec opsconductor-redis-streams redis-cli -a "opsconductor-streams-2024" INFO server 2>/dev/null | grep -E "(redis_version|uptime_in_seconds)" || echo "redis_version:unknown")
    local redis_version=$(echo "$redis_info" | grep "redis_version" | cut -d: -f2 | tr -d '\r')
    local uptime=$(echo "$redis_info" | grep "uptime_in_seconds" | cut -d: -f2 | tr -d '\r')
    
    echo -e "  📦 Redis Version: ${redis_version:-unknown}"
    echo -e "  ⏱️  Uptime: ${uptime:-0} seconds"
    
    # Get stream count
    local stream_count=$(docker exec opsconductor-redis-streams redis-cli -a "opsconductor-streams-2024" --scan --pattern "*:events" 2>/dev/null | wc -l || echo "0")
    echo -e "  🌊 Active Streams: $stream_count"
    
    echo -e "\n${CYAN}🚀 NEXT STEPS:${NC}"
    echo -e "  1. Visit the monitor dashboard: ${YELLOW}http://localhost:$MONITOR_PORT${NC}"
    echo -e "  2. Check service logs: ${YELLOW}docker logs opsconductor-streams-processor${NC}"
    echo -e "  3. Test message publishing: ${YELLOW}./test-redis-streams.sh${NC}"
    echo -e "  4. Integrate with OpsConductor services"
    
    echo -e "\n${CYAN}📚 DOCUMENTATION:${NC}"
    echo -e "  • Redis Streams Guide: redis-streams/README.md"
    echo -e "  • API Documentation: shared/redis_streams.py"
    echo -e "  • Monitoring Guide: Monitor dashboard help section"
    
    echo -e "\n${GREEN}✅ Redis Streams deployment completed successfully!${NC}"
    echo -e "${GREEN}✅ Enterprise message streaming is now operational!${NC}"
}

# Function to handle cleanup on failure
cleanup_on_failure() {
    error "Deployment failed. Cleaning up..."
    
    # Stop services
    if command_exists docker-compose; then
        docker-compose -f "$COMPOSE_FILE" -p "$PROJECT_NAME" down --remove-orphans 2>/dev/null || true
    else
        docker compose -f "$COMPOSE_FILE" -p "$PROJECT_NAME" down --remove-orphans 2>/dev/null || true
    fi
    
    # Remove volumes if they exist
    docker volume rm "${PROJECT_NAME}_redis_streams_data" 2>/dev/null || true
    
    error "Cleanup completed"
    exit 1
}

# Function to handle script interruption
handle_interrupt() {
    echo -e "\n${YELLOW}Deployment interrupted by user${NC}"
    cleanup_on_failure
}

# Main deployment function
main() {
    # Set up signal handlers
    trap handle_interrupt SIGINT SIGTERM
    
    # Clear previous log
    > "$DEPLOYMENT_LOG"
    
    # Show banner
    show_banner
    
    # Start deployment
    log "Starting Redis Streams deployment..."
    log "Deployment log: $DEPLOYMENT_LOG"
    
    # Run deployment steps
    check_prerequisites || cleanup_on_failure
    build_images || cleanup_on_failure
    deploy_services || cleanup_on_failure
    
    # Give services time to start
    sleep 10
    
    verify_deployment || cleanup_on_failure
    test_streams || cleanup_on_failure
    
    # Show summary
    show_summary
    
    success "Redis Streams deployment completed successfully!"
    log "Deployment finished at $(date)"
}

# Script entry point
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    main "$@"
fi