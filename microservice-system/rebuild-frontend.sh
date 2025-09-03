#!/bin/bash

echo "🔥 FORCING COMPLETE FRONTEND REBUILD 🔥"

# Stop the frontend container
echo "Stopping frontend container..."
docker compose -f docker-compose-python.yml stop frontend

# Remove the frontend container
echo "Removing frontend container..."
docker compose -f docker-compose-python.yml rm -f frontend

# Remove the frontend image
echo "Removing frontend image..."
docker rmi microservice-system-frontend 2>/dev/null || echo "Image not found, continuing..."

# Remove build cache for frontend
echo "Removing build cache..."
docker builder prune -f --filter label=stage=build

# Rebuild with no cache
echo "Rebuilding frontend with no cache..."
docker compose -f docker-compose-python.yml build --no-cache frontend

# Start the frontend
echo "Starting frontend..."
docker compose -f docker-compose-python.yml up -d frontend

echo "✅ Frontend rebuild complete!"

# Show the new build hash
sleep 2
echo "New build hash:"
curl -k https://localhost:8443/ 2>/dev/null | grep -o 'main\.[a-f0-9]*\.js' || echo "Could not detect build hash"