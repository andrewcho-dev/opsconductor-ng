#!/bin/bash

# View OpsConductor Service Logs

set -e

# Check which mode is running
DEV_RUNNING=$(docker compose -f docker-compose.dev.yml ps --services --filter "status=running" 2>/dev/null | wc -l)
PROD_RUNNING=$(docker compose -f docker-compose.clean.yml ps --services --filter "status=running" 2>/dev/null | wc -l)

if [ "$DEV_RUNNING" -gt 0 ]; then
    COMPOSE_FILE="docker-compose.dev.yml"
    MODE="DEVELOPMENT"
elif [ "$PROD_RUNNING" -gt 0 ]; then
    COMPOSE_FILE="docker-compose.clean.yml"
    MODE="PRODUCTION"
else
    echo "❌ No OpsConductor services are running!"
    echo "   Start with: ./scripts/dev-mode.sh or ./scripts/prod-mode.sh"
    exit 1
fi

echo "📋 OpsConductor $MODE Mode Logs"
echo "================================"
echo ""

# If specific service provided as argument
if [ $# -eq 1 ]; then
    SERVICE=$1
    echo "📝 Showing logs for: $SERVICE"
    echo "Press Ctrl+C to exit"
    echo ""
    docker compose -f "$COMPOSE_FILE" logs -f "$SERVICE"
else
    # Show menu of services
    echo "Select a service to view logs:"
    echo ""
    echo "1) ai-brain           - AI Brain service"
    echo "2) automation-service - Automation service"
    echo "3) asset-service      - Asset service"
    echo "4) network-service    - Network analyzer service"
    echo "5) communication-service - Communication service"
    echo "6) identity-service   - Identity service"
    if [ "$DEV_RUNNING" -gt 0 ]; then
        echo "7) frontend           - Frontend (development)"
    fi
    echo "8) postgres           - PostgreSQL database"
    echo "9) redis              - Redis cache"
    echo "10) ollama            - Ollama LLM service"
    echo "11) prefect-server    - Prefect orchestration"
    echo "12) all               - All services"
    echo ""
    read -p "Enter choice (1-12): " choice

    case $choice in
        1) SERVICE="ai-brain" ;;
        2) SERVICE="automation-service" ;;
        3) SERVICE="asset-service" ;;
        4) SERVICE="network-service" ;;
        5) SERVICE="communication-service" ;;
        6) SERVICE="identity-service" ;;
        7) 
            if [ "$DEV_RUNNING" -gt 0 ]; then
                SERVICE="frontend"
            else
                echo "❌ Frontend only available in development mode"
                exit 1
            fi
            ;;
        8) SERVICE="postgres" ;;
        9) SERVICE="redis" ;;
        10) SERVICE="ollama" ;;
        11) SERVICE="prefect-server" ;;
        12) SERVICE="" ;;  # All services
        *)
            echo "❌ Invalid choice"
            exit 1
            ;;
    esac

    if [ -z "$SERVICE" ]; then
        echo "📝 Showing logs for ALL services"
        echo "Press Ctrl+C to exit"
        echo ""
        docker compose -f "$COMPOSE_FILE" logs -f
    else
        echo "📝 Showing logs for: $SERVICE"
        echo "Press Ctrl+C to exit"
        echo ""
        docker compose -f "$COMPOSE_FILE" logs -f "$SERVICE"
    fi
fi