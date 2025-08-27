#!/bin/bash

echo "🧹 CLEANING DOCKER CACHE..."

# Remove all stopped containers
docker container prune -f

# Remove all unused images
docker image prune -a -f

# Remove all unused volumes
docker volume prune -f

# Remove all unused networks
docker network prune -f

# Remove build cache
docker builder prune -a -f

echo "✅ Docker cache cleaned!"

# Show disk space saved
echo "Docker system disk usage:"
docker system df