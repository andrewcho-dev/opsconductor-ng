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

### API Gateway
```yaml
volumes:
        - ./api-gateway/main.py:/app/main.py
        - ./shared:/app/shared
```

### Identity Service
```yaml
volumes:
        - ./identity-service/main.py:/app/main.py
        - ./shared:/app/shared
```

### Asset Service
```yaml
volumes:
        - ./asset-service/main.py:/app/main.py
        - ./asset-service/main_with_groups.py:/app/main_with_groups.py
        - ./asset-service/data:/app/data
        - ./shared:/app/shared
```

### Automation Service (Main + Workers + Monitor)
```yaml
volumes:
        - ./automation-service/main.py:/app/main.py
        - ./automation-service/worker.py:/app/worker.py
        - ./automation-service/celery_monitor.py:/app/celery_monitor.py
        - ./automation-service/websocket_manager.py:/app/websocket_manager.py
        - ./automation-service/libraries:/app/libraries
        - ./shared:/app/shared
```

### Communication Service
```yaml
volumes:
        - ./communication-service/main.py:/app/main.py
        - ./shared:/app/shared
```

### AI Service
```yaml
volumes:
        - ./ai-service/main.py:/app/main.py
        - ./ai-service/ai_engine.py:/app/ai_engine.py
        - ./ai-service/ai_engine_broken.py:/app/ai_engine_broken.py
        - ./ai-service/asset_client.py:/app/asset_client.py
        - ./ai-service/automation_client.py:/app/automation_client.py
        - ./ai-service/nlp_processor.py:/app/nlp_processor.py
        - ./ai-service/protocol_manager.py:/app/protocol_manager.py
        - ./ai-service/vector_store.py:/app/vector_store.py
        - ./ai-service/workflow_generator.py:/app/workflow_generator.py
        - ./shared:/app/shared
        - ollama_models:/root/.ollama
```

### Frontend
```yaml
volumes:
        - ./frontend/src:/app/src
        - ./frontend/public:/app/public
        - ./frontend/package.json:/app/package.json
        - ./frontend/package-lock.json:/app/package-lock.json
        - ./frontend/tsconfig.json:/app/tsconfig.json
        - ./frontend/.env:/app/.env
```

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
