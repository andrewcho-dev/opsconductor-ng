#!/bin/bash

SERVICE=${1:-frontend}

echo "🚀 DEVELOPMENT REBUILD: $SERVICE"

# Add timestamp to force cache invalidation
echo "export const BUILD_TIMESTAMP = '$(date +%s)';" > ./frontend/src/build-timestamp.ts

# Use development override
docker compose -f docker-compose-python.yml -f docker-compose.dev.yml up -d --build $SERVICE

echo "✅ Development rebuild complete for $SERVICE"