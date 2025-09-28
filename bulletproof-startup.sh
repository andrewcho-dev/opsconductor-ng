#!/bin/bash

# OpsConductor Bulletproof Startup Script
# This script ensures services start in the correct order with proper dependency checking

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Configuration
COMPOSE_FILE="docker-compose.yml"
MAX_WAIT_TIME=300  # 5 minutes max wait
CHECK_INTERVAL=5   # Check every 5 seconds

# Logging function
log() {
    echo -e "${CYAN}[$(date +'%Y-%m-%d %H:%M:%S')]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[$(date +'%Y-%m-%d %H:%M:%S')] ✅ $1${NC}"
}

log_warning() {
    echo -e "${YELLOW}[$(date +'%Y-%m-%d %H:%M:%S')] ⚠️  $1${NC}"
}

log_error() {
    echo -e "${RED}[$(date +'%Y-%m-%d %H:%M:%S')] ❌ $1${NC}"
}

# Function to check if a service is healthy via HTTP
check_service_health() {
    local service_name=$1
    local port=$2
    local endpoint=${3:-"/health"}
    
    curl -s -f "http://localhost:${port}${endpoint}" > /dev/null 2>&1
    return $?
}

# Function to check infrastructure service health (non-HTTP)
check_infrastructure_health() {
    local service_name=$1
    local port=$2
    
    case $service_name in
        "postgres")
            # Check if PostgreSQL is accepting connections
            docker compose -f $COMPOSE_FILE exec -T postgres pg_isready -U postgres > /dev/null 2>&1
            return $?
            ;;
        "redis")
            # Check if Redis is responding to ping
            docker compose -f $COMPOSE_FILE exec -T redis redis-cli ping > /dev/null 2>&1
            return $?
            ;;
        "chromadb")
            # Check ChromaDB health endpoint
            curl -s -f "http://localhost:8000/api/v1/heartbeat" > /dev/null 2>&1
            return $?
            ;;
        "ollama")
            # Check if Ollama is responding
            curl -s -f "http://localhost:11434/api/tags" > /dev/null 2>&1
            return $?
            ;;
        *)
            # Default to port check
            nc -z localhost $port > /dev/null 2>&1
            return $?
            ;;
    esac
}

# Function to wait for a service to be ready
wait_for_service() {
    local service_name=$1
    local port=$2
    local endpoint=${3:-"/health"}
    local timeout=${4:-60}
    
    log "Waiting for ${service_name} to be ready..."
    
    local elapsed=0
    while [ $elapsed -lt $timeout ]; do
        if check_service_health "$service_name" "$port" "$endpoint"; then
            log_success "${service_name} is ready! (took ${elapsed}s)"
            return 0
        fi
        
        sleep $CHECK_INTERVAL
        elapsed=$((elapsed + CHECK_INTERVAL))
        
        if [ $((elapsed % 30)) -eq 0 ]; then
            log "Still waiting for ${service_name}... (${elapsed}s elapsed)"
        fi
    done
    
    log_error "${service_name} failed to become ready after ${timeout}s"
    return 1
}

# Function to wait for infrastructure services to be ready
wait_for_infrastructure() {
    local service_name=$1
    local port=$2
    local timeout=${3:-60}
    
    log "Waiting for ${service_name} to be ready..."
    
    local elapsed=0
    while [ $elapsed -lt $timeout ]; do
        if check_infrastructure_health "$service_name" "$port"; then
            log_success "${service_name} is ready! (took ${elapsed}s)"
            return 0
        fi
        
        sleep $CHECK_INTERVAL
        elapsed=$((elapsed + CHECK_INTERVAL))
        
        if [ $((elapsed % 30)) -eq 0 ]; then
            log "Still waiting for ${service_name}... (${elapsed}s elapsed)"
        fi
    done
    
    log_error "${service_name} failed to become ready after ${timeout}s"
    return 1
}

# Function to check Docker and Docker Compose
check_prerequisites() {
    log "Checking prerequisites..."
    
    if ! command -v docker &> /dev/null; then
        log_error "Docker is not installed or not in PATH"
        exit 1
    fi
    
    if ! command -v docker compose &> /dev/null && ! docker compose version &> /dev/null; then
        log_error "Docker Compose is not installed or not in PATH"
        exit 1
    fi
    
    if ! docker info &> /dev/null; then
        log_error "Docker daemon is not running"
        exit 1
    fi
    
    log_success "Prerequisites check passed"
}

# Function to clean up old containers if requested
cleanup_old_containers() {
    if [ "$1" = "--cleanup" ]; then
        log "Cleaning up old containers..."
        docker compose -f $COMPOSE_FILE down --remove-orphans
        docker system prune -f
        log_success "Cleanup completed"
    fi
}

# Function to start infrastructure services
start_infrastructure() {
    log "Starting infrastructure services..."
    
    # Start PostgreSQL
    log "Starting PostgreSQL..."
    docker compose -f $COMPOSE_FILE up -d postgres
    wait_for_infrastructure "postgres" "5432" 60
    
    # Start Redis
    log "Starting Redis..."
    docker compose -f $COMPOSE_FILE up -d redis
    wait_for_infrastructure "redis" "6379" 30
    
    # Start ChromaDB (Vector Database)
    log "Starting ChromaDB..."
    docker compose -f $COMPOSE_FILE up -d chromadb
    wait_for_infrastructure "chromadb" "8000" 60
    
    # Start Ollama (LLM Server)
    log "Starting Ollama..."
    docker compose -f $COMPOSE_FILE up -d ollama
    wait_for_infrastructure "ollama" "11434" 60
    
    log_success "Infrastructure services are ready"
}

# Function to start authentication services
start_auth_services() {
    log "Starting authentication services..."
    
    # Start Keycloak (optional, non-blocking)
    log "Starting Keycloak..."
    docker compose -f $COMPOSE_FILE up -d keycloak
    # Don't wait for Keycloak as it's not critical for startup and takes a long time
    
    log_success "Authentication services started"
}

# Function to start gateway services
start_gateway() {
    log "Starting API Gateway..."
    
    # Start Kong
    docker compose -f $COMPOSE_FILE up -d kong
    wait_for_service "kong" "8080" "/health" 60
    
    log_success "API Gateway is ready"
}

# Function to start core services in dependency order
start_core_services() {
    log "Starting core services..."
    
    # Start Identity Service first (other services depend on it)
    log "Starting Identity Service..."
    docker compose -f $COMPOSE_FILE up -d identity-service
    wait_for_service "identity-service" "3001" "/ready" 90
    
    # Start Asset Service and Communication Service in parallel (automation depends on asset)
    log "Starting Asset Service and Communication Service..."
    docker compose -f $COMPOSE_FILE up -d asset-service communication-service
    wait_for_service "asset-service" "3002" "/ready" 90
    wait_for_service "communication-service" "3004" "/ready" 90
    
    # Start Automation Service (depends on identity and asset services)
    log "Starting Automation Service..."
    docker compose -f $COMPOSE_FILE up -d automation-service
    wait_for_service "automation-service" "3003" "/ready" 120
    
    log_success "Core services are ready"
}

# Function to start AI services
start_ai_services() {
    log "Starting AI services..."
    
    # Start AI Brain Service
    if docker compose -f $COMPOSE_FILE config --services | grep -q "ai-brain"; then
        log "Starting AI Brain Service..."
        docker compose -f $COMPOSE_FILE up -d ai-brain
        wait_for_service "ai-brain" "3005" "/health" 120
    fi
    
    log_success "AI services started"
}

# Function to start network analysis services
start_network_services() {
    log "Starting network analysis services..."
    
    # Start Network Analyzer Service
    if docker compose -f $COMPOSE_FILE config --services | grep -q "network-analyzer-service"; then
        log "Starting Network Analyzer Service..."
        docker compose -f $COMPOSE_FILE up -d network-analyzer-service
        wait_for_service "network-analyzer-service" "3006" "/health" 90
    fi
    
    # Start Network Analytics Probe
    if docker compose -f $COMPOSE_FILE config --services | grep -q "network-analytics-probe"; then
        log "Starting Network Analytics Probe..."
        docker compose -f $COMPOSE_FILE up -d network-analytics-probe
        # Probe runs on host network, so we can't easily check its health
    fi
    
    log_success "Network analysis services started"
}

# Function to start workflow services
start_workflow_services() {
    log "Starting workflow services..."
    
    # Start Prefect Server
    if docker compose -f $COMPOSE_FILE config --services | grep -q "prefect-server"; then
        log "Starting Prefect Server..."
        docker compose -f $COMPOSE_FILE up -d prefect-server
        wait_for_service "prefect-server" "4200" "/api/health" 90
    fi
    
    # Start Prefect Worker and Registry
    if docker compose -f $COMPOSE_FILE config --services | grep -q "prefect-worker"; then
        docker compose -f $COMPOSE_FILE up -d prefect-worker prefect-flow-registry
    fi
    
    log_success "Workflow services started"
}

# Function to start worker services
start_workers() {
    log "Starting worker services..."
    
    # Start automation workers
    if docker compose -f $COMPOSE_FILE config --services | grep -q "automation-worker-1"; then
        docker compose -f $COMPOSE_FILE up -d automation-worker-1 automation-worker-2
    fi
    
    # Start scheduler
    if docker compose -f $COMPOSE_FILE config --services | grep -q "automation-scheduler"; then
        docker compose -f $COMPOSE_FILE up -d automation-scheduler
    fi
    
    # Start monitoring
    if docker compose -f $COMPOSE_FILE config --services | grep -q "celery-monitor"; then
        docker compose -f $COMPOSE_FILE up -d celery-monitor
    fi
    
    log_success "Worker services started"
}

# Function to start frontend
start_frontend() {
    log "Starting frontend..."
    
    if docker compose -f $COMPOSE_FILE config --services | grep -q "frontend"; then
        docker compose -f $COMPOSE_FILE up -d frontend
        # Frontend doesn't have a health check endpoint, so we just wait a bit
        sleep 10
    fi
    
    log_success "Frontend is ready"
}

# Function to verify all services
verify_services() {
    log "Verifying all services..."
    
    # Get list of running services
    local running_services=$(docker compose -f $COMPOSE_FILE ps --services --filter "status=running")
    
    local services_to_check=()
    local failed_services=()
    
    # Check infrastructure services
    if echo "$running_services" | grep -q "postgres"; then
        services_to_check+=("postgres:5432:infrastructure")
    fi
    
    if echo "$running_services" | grep -q "redis"; then
        services_to_check+=("redis:6379:infrastructure")
    fi
    
    if echo "$running_services" | grep -q "chromadb"; then
        services_to_check+=("chromadb:8000:infrastructure")
    fi
    
    # Check gateway services
    if echo "$running_services" | grep -q "kong"; then
        # Kong doesn't have a standard health endpoint, just check if it's responding
        if nc -z localhost 8080 > /dev/null 2>&1; then
            log_success "kong is responding"
        else
            failed_services+=("kong")
        fi
    fi
    
    # Check core services
    if echo "$running_services" | grep -q "identity-service"; then
        services_to_check+=("identity-service:3001:/ready")
    fi
    
    if echo "$running_services" | grep -q "asset-service"; then
        services_to_check+=("asset-service:3002:/ready")
    fi
    
    if echo "$running_services" | grep -q "communication-service"; then
        services_to_check+=("communication-service:3004:/ready")
    fi
    
    if echo "$running_services" | grep -q "automation-service"; then
        services_to_check+=("automation-service:3003:/ready")
    fi
    
    # Check optional services only if they're running
    if echo "$running_services" | grep -q "ai-brain"; then
        services_to_check+=("ai-brain:3005:/health")
    fi
    
    if echo "$running_services" | grep -q "network-analyzer-service"; then
        services_to_check+=("network-analyzer-service:3006:/health")
    fi
    
    if echo "$running_services" | grep -q "prefect-server"; then
        services_to_check+=("prefect-server:4200:/api/health")
    fi
    
    # Verify each service
    for service_info in "${services_to_check[@]}"; do
        IFS=':' read -r service port endpoint <<< "$service_info"
        
        if [[ "$endpoint" == "infrastructure" ]]; then
            if check_infrastructure_health "$service" "$port"; then
                log_success "$service is healthy"
            else
                log_error "$service is unhealthy"
                failed_services+=("$service")
            fi
        else
            if check_service_health "$service" "$port" "${endpoint:-/health}"; then
                log_success "$service is healthy"
            else
                log_error "$service is unhealthy"
                failed_services+=("$service")
            fi
        fi
    done
    
    if [ ${#failed_services[@]} -eq 0 ]; then
        log_success "All running services are healthy!"
        return 0
    else
        log_error "Failed services: ${failed_services[*]}"
        return 1
    fi
}

# Function to show service status
show_status() {
    log "Service Status:"
    echo
    
    # Check if monitoring dashboard exists
    if [ -f "monitoring/advanced-dashboard.html" ]; then
        log "Advanced monitoring dashboard available at: monitoring/advanced-dashboard.html"
        log "Open it in a browser to see real-time service status"
    fi
    
    # Show Docker Compose status
    docker compose -f $COMPOSE_FILE ps
    
    echo
    log "Service Health Summary:"
    
    # Check core services
    local services=("identity-service:3001" "asset-service:3002" "automation-service:3003" "communication-service:3004")
    
    for service_info in "${services[@]}"; do
        IFS=':' read -r service port <<< "$service_info"
        if check_service_health "$service" "$port" "/health"; then
            echo -e "  ${GREEN}✅ $service${NC}"
        else
            echo -e "  ${RED}❌ $service${NC}"
        fi
    done
}

# Function to show helpful information
show_info() {
    echo
    log_success "🚀 OpsConductor is ready!"
    echo
    echo -e "${CYAN}Access URLs:${NC}"
    echo -e "  API Gateway:        ${GREEN}http://localhost:3000${NC}"
    echo -e "  Identity Service:   ${GREEN}http://localhost:3001${NC}"
    echo -e "  Asset Service:      ${GREEN}http://localhost:3002${NC}"
    echo -e "  Automation Service: ${GREEN}http://localhost:3003${NC}"
    echo -e "  Communication:      ${GREEN}http://localhost:3004${NC}"
    
    if docker compose -f $COMPOSE_FILE config --services | grep -q "ai-brain"; then
        echo -e "  AI Brain Service:   ${GREEN}http://localhost:3005${NC}"
    fi
    
    if docker compose -f $COMPOSE_FILE config --services | grep -q "network-analyzer-service"; then
        echo -e "  Network Analyzer:   ${GREEN}http://localhost:3006${NC}"
    fi
    
    echo -e "  Keycloak Admin:     ${GREEN}http://localhost:8090${NC}"
    echo -e "  ChromaDB:           ${GREEN}http://localhost:8000${NC}"
    echo -e "  Ollama:             ${GREEN}http://localhost:11434${NC}"
    
    if docker compose -f $COMPOSE_FILE config --services | grep -q "prefect-server"; then
        echo -e "  Prefect UI:         ${GREEN}http://localhost:4200${NC}"
    fi
    
    if docker compose -f $COMPOSE_FILE config --services | grep -q "celery-monitor"; then
        echo -e "  Celery Monitor:     ${GREEN}http://localhost:5555${NC}"
    fi
    
    if docker compose -f $COMPOSE_FILE config --services | grep -q "frontend"; then
        echo -e "  Frontend:           ${GREEN}http://localhost${NC}"
    fi
    
    echo
    echo -e "${CYAN}Monitoring:${NC}"
    if [ -f "monitoring/advanced-dashboard.html" ]; then
        echo -e "  Advanced Dashboard: ${GREEN}monitoring/advanced-dashboard.html${NC}"
    fi
    echo -e "  Service Health:     ${GREEN}curl http://localhost:3001/health${NC}"
    echo -e "  Docker Logs:        ${GREEN}docker compose logs -f [service]${NC}"
    echo
    echo -e "${CYAN}Useful Commands:${NC}"
    echo -e "  Stop all:           ${GREEN}docker compose down${NC}"
    echo -e "  Restart service:    ${GREEN}docker compose restart [service]${NC}"
    echo -e "  View logs:          ${GREEN}docker compose logs -f [service]${NC}"
    echo -e "  Check status:       ${GREEN}./bulletproof-startup.sh --status${NC}"
    echo
}

# Main execution
main() {
    echo -e "${BLUE}"
    echo "╔══════════════════════════════════════════════════════════════╗"
    echo "║                OpsConductor Bulletproof Startup             ║"
    echo "║                                                              ║"
    echo "║  This script will start all services in the correct order   ║"
    echo "║  with proper dependency checking and health verification.    ║"
    echo "╚══════════════════════════════════════════════════════════════╝"
    echo -e "${NC}"
    echo
    
    # Parse arguments
    CLEANUP=false
    VERIFY_ONLY=false
    SHOW_STATUS=false
    
    for arg in "$@"; do
        case $arg in
            --cleanup)
                CLEANUP=true
                ;;
            --verify)
                VERIFY_ONLY=true
                ;;
            --status)
                SHOW_STATUS=true
                ;;
            --help)
                echo "Usage: $0 [options]"
                echo "Options:"
                echo "  --cleanup    Clean up old containers before starting"
                echo "  --verify     Only verify services are running"
                echo "  --status     Show current service status"
                echo "  --help       Show this help message"
                exit 0
                ;;
        esac
    done
    
    # Handle special modes
    if [ "$SHOW_STATUS" = true ]; then
        show_status
        exit 0
    fi
    
    if [ "$VERIFY_ONLY" = true ]; then
        verify_services
        exit $?
    fi
    
    # Main startup sequence
    check_prerequisites
    
    if [ "$CLEANUP" = true ]; then
        cleanup_old_containers --cleanup
    fi
    
    log "Starting bulletproof startup sequence..."
    
    # Start services in dependency order
    start_infrastructure
    start_auth_services
    start_gateway
    start_core_services
    start_ai_services
    start_network_services
    start_workflow_services
    start_workers
    start_frontend
    
    # Verify everything is working
    if verify_services; then
        show_info
        
        # Offer to open monitoring dashboard
        if [ -f "monitoring/advanced-dashboard.html" ]; then
            echo -e "${CYAN}Would you like to open the monitoring dashboard? (y/n)${NC}"
            read -r response
            if [[ "$response" =~ ^[Yy]$ ]]; then
                if command -v xdg-open &> /dev/null; then
                    xdg-open "monitoring/advanced-dashboard.html"
                elif command -v open &> /dev/null; then
                    open "monitoring/advanced-dashboard.html"
                else
                    log "Please open monitoring/advanced-dashboard.html in your browser"
                fi
            fi
        fi
    else
        log_error "Some services failed to start properly"
        show_status
        exit 1
    fi
}

# Run main function with all arguments
main "$@"