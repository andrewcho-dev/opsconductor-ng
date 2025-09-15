#!/bin/bash
# Automatically update the ZenRule with current volume mount configurations

set -e

ZENRULE_FILE=".zenrules/selective-volume-mounts.md"
TEMP_FILE="/tmp/zenrule_update.md"

echo "🔄 Auto-updating ZenRule with current configurations..."

# Create the header
cat > "$TEMP_FILE" << 'EOF'
# ZenRule: Selective Volume Mounts for Development

## CRITICAL RULE: NEVER USE FULL DIRECTORY VOLUME MOUNTS

**NEVER DO THIS:**
```yaml
volumes:
  - ./service-name:/app
```

**ALWAYS DO THIS:**
```yaml
volumes:
  - ./service-name/main.py:/app/main.py
  - ./service-name/other-file.py:/app/other-file.py
  - ./shared:/app/shared
```

## WHY THIS RULE EXISTS

Full directory mounts (`./service:/app`) override the ENTIRE container directory, including:
- Python virtual environments
- Installed packages
- Built dependencies
- Compiled binaries
- Node modules
- Any container-specific files

This causes:
- Wrong Python versions (host vs container)
- Missing dependencies
- Build failures
- Hours of debugging time
- Inconsistent environments

## CURRENT SELECTIVE VOLUME MOUNT CONFIGURATIONS

EOF

# Extract current configurations from docker-compose.yml
echo "🔍 Extracting current configurations from docker-compose.yml..."

# Function to extract volume mounts for a service
extract_service_volumes() {
    local service_name="$1"
    local display_name="$2"
    
    echo "### $display_name" >> "$TEMP_FILE"
    echo '```yaml' >> "$TEMP_FILE"
    echo 'volumes:' >> "$TEMP_FILE"
    
    # Extract volumes section for this service
    awk "
        /^  $service_name:/ { in_service=1; next }
        in_service && /^  [a-zA-Z]/ && !/^  $service_name/ { in_service=0 }
        in_service && /^    volumes:/ { in_volumes=1; next }
        in_volumes && /^    [a-zA-Z]/ && !/^    volumes/ { in_volumes=0 }
        in_volumes && /^      - / { print \"  \" \$0 }
    " docker-compose.yml >> "$TEMP_FILE"
    
    echo '```' >> "$TEMP_FILE"
    echo "" >> "$TEMP_FILE"
}

# Extract configurations for all services
extract_service_volumes "api-gateway" "API Gateway"
extract_service_volumes "identity-service" "Identity Service"
extract_service_volumes "asset-service" "Asset Service"
extract_service_volumes "automation-service" "Automation Service (Main + Workers + Monitor)"
extract_service_volumes "communication-service" "Communication Service"
extract_service_volumes "ai-service" "AI Service"
extract_service_volumes "frontend" "Frontend"

# Add the rest of the ZenRule
cat >> "$TEMP_FILE" << 'EOF'
## WHEN ADDING NEW FILES TO SERVICES

**MANDATORY STEPS:**

1. **Add the new file to the selective volume mount list**
2. **Update this ZenRule document**
3. **Update docker-compose.yml**
4. **Test that the container still works**

### Example: Adding a new file to AI Service

If you add `./ai-service/new_module.py`, you MUST:

1. Add to docker-compose.yml:
```yaml
- ./ai-service/new_module.py:/app/new_module.py
```

2. Update this ZenRule document in the AI Service section

3. Restart the service to test

## AUTOMATED CHECKING SCRIPT

Create this script to validate volume mounts:

```bash
#!/bin/bash
# File: scripts/check-volume-mounts.sh

echo "Checking for dangerous full directory volume mounts..."

# Check for full directory mounts in docker-compose.yml
if grep -E "^\s*-\s*\./[^/]+:/app\s*$" docker-compose.yml; then
    echo "❌ DANGER: Full directory volume mounts found!"
    echo "These will override container environments and cause issues."
    echo "Use selective file/directory mounts instead."
    exit 1
else
    echo "✅ All volume mounts are selective - good!"
fi

# Check that all Python files in services are mounted
echo "Checking that all Python files are mounted..."

for service in api-gateway identity-service asset-service automation-service communication-service ai-service; do
    echo "Checking $service..."
    
    # Find all Python files in service directory
    find "./$service" -name "*.py" -not -path "*/__pycache__/*" | while read file; do
        # Convert to container path
        container_path=$(echo "$file" | sed "s|^\./||" | sed "s|^$service/|/app/|")
        
        # Check if this file is mounted in docker-compose.yml
        if ! grep -q "$file:$container_path" docker-compose.yml; then
            echo "⚠️  WARNING: $file is not mounted in docker-compose.yml"
        fi
    done
done
```

## ENFORCEMENT

1. **Pre-commit hook**: Add volume mount validation
2. **CI/CD check**: Fail builds with full directory mounts
3. **Code review**: Always check volume mounts in docker-compose.yml changes
4. **Documentation**: Keep this ZenRule updated

## EXCEPTIONS

The ONLY acceptable full directory mounts are:
- Data volumes (postgres_data, redis_data, etc.)
- Shared directories that don't contain environments (./shared:/app/shared)
- Static asset directories that don't contain code

## TROUBLESHOOTING

If you see Python version mismatches or missing dependencies:

1. Check if there are full directory volume mounts
2. Convert to selective mounts
3. Rebuild the container: `docker compose build --no-cache service-name`
4. Restart: `docker compose up -d service-name`

## REMEMBER

**SELECTIVE VOLUME MOUNTS = FAST DEVELOPMENT + STABLE ENVIRONMENTS**
**FULL DIRECTORY MOUNTS = BROKEN ENVIRONMENTS + WASTED TIME**
EOF

# Replace the original file
mv "$TEMP_FILE" "$ZENRULE_FILE"

echo "✅ ZenRule updated with current configurations!"
echo "📖 Updated file: $ZENRULE_FILE"
echo ""
echo "🎯 The ZenRule now reflects your current docker-compose.yml configuration."
echo "🔄 Run this script whenever you update volume mounts to keep documentation in sync."