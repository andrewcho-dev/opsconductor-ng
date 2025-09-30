#!/bin/bash

# OpsConductor Complete Clean
# Nuclear option - removes everything and starts fresh

set -e

echo "☢️  OpsConductor COMPLETE CLEAN (Nuclear Option)"
echo "================================================"
echo ""
echo "⚠️  WARNING: This will remove ALL OpsConductor containers, images, and non-persistent data!"
echo "⚠️  Persistent data (postgres_data, redis_data, etc.) will be preserved."
echo ""

# Confirmation prompt
read -p "Are you sure you want to proceed? (type 'yes' to continue): " confirm
if [ "$confirm" != "yes" ]; then
    echo "❌ Operation cancelled."
    exit 1
fi

echo ""
echo "🧹 Starting complete clean..."

# Stop all containers
echo "🛑 Stopping all containers..."
docker compose -f docker-compose.dev.yml down 2>/dev/null || true
docker compose -f docker-compose.clean.yml down 2>/dev/null || true

# Remove all OpsConductor containers
echo "🗑️  Removing all OpsConductor containers..."
docker ps -a --format "{{.Names}}" | grep opsconductor | xargs -r docker rm -f 2>/dev/null || true

# Remove all OpsConductor images
echo "🗑️  Removing all OpsConductor images..."
docker images --format "{{.Repository}}:{{.Tag}}" | grep -E "(opsconductor|opsconductor-ng)" | xargs -r docker rmi -f 2>/dev/null || true

# Remove all build cache
echo "🧹 Cleaning all Docker build cache..."
docker builder prune -a -f 2>/dev/null || true

# Remove orphaned volumes (preserve data volumes)
echo "🧹 Cleaning orphaned volumes (preserving data)..."
PRESERVE_VOLUMES="postgres_data redis_data ollama_models prefect_data"
ALL_VOLUMES=$(docker volume ls -q)

for volume in $ALL_VOLUMES; do
    if echo "$PRESERVE_VOLUMES" | grep -q "$volume"; then
        echo "   💾 Preserving data volume: $volume"
    else
        echo "   🗑️  Removing volume: $volume"
        docker volume rm "$volume" 2>/dev/null || true
    fi
done

# Clean up dangling images and containers
echo "🧹 Cleaning up dangling resources..."
docker system prune -f 2>/dev/null || true

# Remove any leftover networks
echo "🧹 Cleaning up networks..."
docker network ls --format "{{.Name}}" | grep opsconductor | xargs -r docker network rm 2>/dev/null || true

echo ""
echo "✅ COMPLETE CLEAN FINISHED!"
echo ""
echo "📋 What was cleaned:"
echo "   🗑️  All OpsConductor containers"
echo "   🗑️  All OpsConductor images"
echo "   🗑️  All build cache"
echo "   🗑️  All orphaned volumes"
echo "   🗑️  All OpsConductor networks"
echo ""
echo "💾 What was preserved:"
echo "   ✅ postgres_data volume"
echo "   ✅ redis_data volume"
echo "   ✅ ollama_models volume"
echo "   ✅ prefect_data volume"
echo ""
echo "🚀 To start fresh:"
echo "   ./scripts/dev-mode.sh   - Start development mode"
echo "   ./scripts/prod-mode.sh  - Start production mode"
echo ""
echo "💡 The system will rebuild everything from scratch on next start."