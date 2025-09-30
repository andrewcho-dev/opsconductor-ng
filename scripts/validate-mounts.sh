#!/bin/bash

# Validate OpsConductor Volume Mounts
# Simple validation script that actually works

set -e

echo "🔍 Validating OpsConductor Volume Mounts"
echo "========================================"
echo ""

ERRORS=0
WARNINGS=0

# Check that required files exist
echo "📁 Checking required files..."

REQUIRED_FILES=(
    "docker-compose.dev.yml"
    "docker-compose.clean.yml"
)

for file in "${REQUIRED_FILES[@]}"; do
    if [ -f "$file" ]; then
        echo "   ✅ $file exists"
    else
        echo "   ❌ $file missing"
        ERRORS=$((ERRORS + 1))
    fi
done

echo ""

# Check development compose file for proper volume mounts
echo "🔧 Checking development volume mounts..."

if [ -f "docker-compose.dev.yml" ]; then
    # Check that dev file has volume mounts
    if grep -q "volumes:" docker-compose.dev.yml; then
        echo "   ✅ Development file has volume mounts"
        
        # Check for dangerous full directory mounts
        if grep -E "^\s*-\s*\./[^/]+:/app\s*$" docker-compose.dev.yml; then
            echo "   ❌ DANGER: Full directory volume mounts found in dev file!"
            echo "      These will override container environments."
            ERRORS=$((ERRORS + 1))
        else
            echo "   ✅ No dangerous full directory mounts in dev file"
        fi
        
        # Check that shared directory is mounted
        if grep -q "./shared:/app/shared" docker-compose.dev.yml; then
            echo "   ✅ Shared directory is properly mounted"
        else
            echo "   ⚠️  Shared directory mount not found"
            WARNINGS=$((WARNINGS + 1))
        fi
        
        # Check that volume mount sources exist
        echo "   📁 Checking volume mount source files/directories..."
        MOUNT_SOURCES=$(grep -E "^\s*-\s*\./[^:]+:" docker-compose.dev.yml | sed -E 's/^\s*-\s*([^:]+):.*/\1/' | sort -u)
        MISSING_SOURCES=0
        
        while IFS= read -r source; do
            if [ -n "$source" ]; then
                if [ -e "$source" ]; then
                    echo "      ✅ $source exists"
                else
                    echo "      ❌ $source missing"
                    MISSING_SOURCES=$((MISSING_SOURCES + 1))
                fi
            fi
        done <<< "$MOUNT_SOURCES"
        
        if [ $MISSING_SOURCES -gt 0 ]; then
            echo "   ⚠️  $MISSING_SOURCES volume mount sources are missing"
            echo "      System will create empty files/directories, but this may not be intended"
            WARNINGS=$((WARNINGS + MISSING_SOURCES))
        fi
        
    else
        echo "   ❌ Development file has no volume mounts!"
        echo "      Development mode should have volume mounts for live changes."
        ERRORS=$((ERRORS + 1))
    fi
fi

echo ""

# Check for port conflicts
echo "🔌 Checking port configurations..."

if [ -f "docker-compose.dev.yml" ]; then
    # Extract all port mappings
    PORTS=$(grep -E "^\s*-\s*\"[0-9]+:" docker-compose.dev.yml | sed -E 's/^\s*-\s*"([0-9]+):.*/\1/' | sort)
    DUPLICATE_PORTS=$(echo "$PORTS" | uniq -d)
    
    if [ -n "$DUPLICATE_PORTS" ]; then
        echo "   ❌ Port conflicts detected!"
        echo "      Duplicate ports: $DUPLICATE_PORTS"
        ERRORS=$((ERRORS + 1))
    else
        echo "   ✅ No port conflicts in development configuration"
    fi
    
    # Check for common port conflicts with system services
    SYSTEM_PORTS="22 25 53 80 443 3306 5432"
    for port in $PORTS; do
        if echo "$SYSTEM_PORTS" | grep -q "$port"; then
            echo "   ⚠️  Port $port may conflict with system services"
            WARNINGS=$((WARNINGS + 1))
        fi
    done
fi

echo ""

# Check production compose file
echo "🏭 Checking production configuration..."

if [ -f "docker-compose.clean.yml" ]; then
    # Check that production file has minimal volume mounts
    SERVICE_MOUNTS=$(grep -E "^\s*-\s*\./[^/]+:" docker-compose.clean.yml | grep -v "database\|data:" | wc -l)
    
    if [ "$SERVICE_MOUNTS" -eq 0 ]; then
        echo "   ✅ Production file has no service volume mounts (good!)"
    else
        echo "   ⚠️  Production file has $SERVICE_MOUNTS service volume mounts"
        echo "      Production should have minimal volume mounts."
        WARNINGS=$((WARNINGS + 1))
    fi
    
    # Check for data volume mounts (these are OK)
    if grep -q "postgres_data\|redis_data\|ollama_models\|prefect_data" docker-compose.clean.yml; then
        echo "   ✅ Data persistence volumes found (good!)"
    else
        echo "   ⚠️  No data persistence volumes found"
        WARNINGS=$((WARNINGS + 1))
    fi
fi

echo ""

# Check that scripts are executable
echo "🔧 Checking script permissions..."

SCRIPTS=(
    "scripts/dev-mode.sh"
    "scripts/prod-mode.sh"
    "scripts/status.sh"
    "scripts/logs.sh"
    "scripts/stop-dev.sh"
    "scripts/stop-prod.sh"
)

for script in "${SCRIPTS[@]}"; do
    if [ -f "$script" ]; then
        if [ -x "$script" ]; then
            echo "   ✅ $script is executable"
        else
            echo "   ⚠️  $script is not executable (fixing...)"
            chmod +x "$script"
            echo "   ✅ $script made executable"
        fi
    else
        echo "   ❌ $script missing"
        ERRORS=$((ERRORS + 1))
    fi
done

echo ""

# Summary
echo "📊 Validation Summary"
echo "===================="

if [ $ERRORS -eq 0 ] && [ $WARNINGS -eq 0 ]; then
    echo "   🎉 All checks passed! Volume mount configuration is correct."
elif [ $ERRORS -eq 0 ]; then
    echo "   ✅ No errors found, but $WARNINGS warning(s) detected."
    echo "   💡 System should work but consider addressing warnings."
else
    echo "   ❌ $ERRORS error(s) and $WARNINGS warning(s) found."
    echo "   🔧 Please fix errors before proceeding."
fi

echo ""
echo "🔧 Quick Commands:"
echo "   ./scripts/dev-mode.sh   - Start development mode (with volume mounts)"
echo "   ./scripts/prod-mode.sh  - Start production mode (no volume mounts)"
echo "   ./scripts/status.sh     - Check system status"
echo ""

# Exit with error code if there are errors
if [ $ERRORS -gt 0 ]; then
    exit 1
else
    exit 0
fi