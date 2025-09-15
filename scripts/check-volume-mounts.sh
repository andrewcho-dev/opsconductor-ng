#!/bin/bash
# Automated Volume Mount Validation Script
# This script ensures we never use dangerous full directory volume mounts

set -e

echo "🔍 Checking for dangerous full directory volume mounts..."

# Check for full directory mounts in docker-compose.yml
DANGEROUS_MOUNTS=$(grep -E "^\s*-\s*\./[^/]+:/app\s*$" docker-compose.yml || true)

if [ ! -z "$DANGEROUS_MOUNTS" ]; then
    echo "❌ DANGER: Full directory volume mounts found!"
    echo "These will override container environments and cause issues:"
    echo "$DANGEROUS_MOUNTS"
    echo ""
    echo "🔧 FIX: Use selective file/directory mounts instead."
    echo "See .zenrules/selective-volume-mounts.md for examples."
    exit 1
else
    echo "✅ All volume mounts are selective - good!"
fi

echo ""
echo "🔍 Checking that all Python files are properly mounted..."

# Services to check
SERVICES=("api-gateway" "identity-service" "asset-service" "automation-service" "communication-service" "ai-service")

WARNINGS=0

for service in "${SERVICES[@]}"; do
    if [ -d "./$service" ]; then
        echo "Checking $service..."
        
        # Find all Python files in service directory (excluding __pycache__ and shared)
        while IFS= read -r -d '' file; do
            # Skip files in shared directory (handled by ./shared:/app/shared mount)
            if [[ "$file" == *"/shared/"* ]]; then
                continue
            fi
            
            # Skip files in directories that are mounted entirely
            skip_file=false
            for mounted_dir in libraries data config templates static; do
                if [[ "$file" == *"/$mounted_dir/"* ]] && grep -q "./$service/$mounted_dir:/app/$mounted_dir" docker-compose.yml; then
                    skip_file=true
                    break
                fi
            done
            
            if [ "$skip_file" = true ]; then
                continue
            fi
            
            # Convert to relative path from service directory
            rel_path=${file#./$service/}
            container_path="/app/$rel_path"
            
            # Check if this file is mounted in docker-compose.yml
            if ! grep -q "$file:$container_path" docker-compose.yml; then
                echo "⚠️  WARNING: $file is not mounted in docker-compose.yml"
                ((WARNINGS++))
            fi
        done < <(find "./$service" -name "*.py" -not -path "*/__pycache__/*" -print0)
    fi
done

echo ""
echo "🔍 Checking that all TypeScript/JavaScript files are properly mounted for frontend..."

if [ -d "./frontend/src" ]; then
    # Check if src directory is mounted
    if grep -q "./frontend/src:/app/src" docker-compose.yml; then
        echo "✅ Frontend src directory is properly mounted"
    else
        echo "⚠️  WARNING: Frontend src directory is not mounted"
        ((WARNINGS++))
    fi
fi

echo ""
if [ $WARNINGS -eq 0 ]; then
    echo "✅ All checks passed! Volume mounts are properly configured."
else
    echo "⚠️  Found $WARNINGS warnings. Consider updating docker-compose.yml"
    echo "📖 See .zenrules/selective-volume-mounts.md for guidance"
fi

echo ""
echo "🎯 Remember: Selective volume mounts = Fast development + Stable environments"
echo "🚫 Full directory mounts = Broken environments + Wasted time"