#!/bin/bash
# Script to automatically generate selective volume mounts for a service

SERVICE_NAME="$1"

if [ -z "$SERVICE_NAME" ]; then
    echo "Usage: $0 <service-name>"
    echo "Example: $0 ai-service"
    exit 1
fi

if [ ! -d "./$SERVICE_NAME" ]; then
    echo "Error: Service directory ./$SERVICE_NAME does not exist"
    exit 1
fi

echo "🔍 Generating selective volume mounts for $SERVICE_NAME..."
echo ""
echo "Add these lines to docker-compose.yml under the $SERVICE_NAME volumes section:"
echo ""

# Find all Python files and generate mount lines
find "./$SERVICE_NAME" -name "*.py" -not -path "*/__pycache__/*" | sort | while read file; do
    container_path=$(echo "$file" | sed "s|^\./||" | sed "s|^$SERVICE_NAME/|/app/|")
    echo "      - $file:$container_path"
done

# Find directories that should be mounted entirely (like libraries, data, etc.)
for dir in libraries data config templates static; do
    if [ -d "./$SERVICE_NAME/$dir" ]; then
        echo "      - ./$SERVICE_NAME/$dir:/app/$dir"
    fi
done

# Always include shared
echo "      - ./shared:/app/shared"

echo ""
echo "🎯 Don't forget to:"
echo "1. Update .zenrules/selective-volume-mounts.md"
echo "2. Test the service: docker compose up -d $SERVICE_NAME"
echo "3. Run validation: ./scripts/check-volume-mounts.sh"