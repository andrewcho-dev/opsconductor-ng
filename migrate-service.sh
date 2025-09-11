#!/bin/bash
# Service Migration Script
# Usage: ./migrate-service.sh <service-name>

set -e

SERVICE_NAME=$1
if [ -z "$SERVICE_NAME" ]; then
    echo "Usage: $0 <service-name>"
    echo "Example: $0 auth-service"
    exit 1
fi

SERVICE_DIR="/home/opsconductor/$SERVICE_NAME"
TEMPLATES_DIR="/home/opsconductor/service-templates"

if [ ! -d "$SERVICE_DIR" ]; then
    echo "Error: Service directory $SERVICE_DIR does not exist"
    exit 1
fi

if [ ! -d "$TEMPLATES_DIR" ]; then
    echo "Error: Templates directory $TEMPLATES_DIR does not exist"
    exit 1
fi

echo "Migrating $SERVICE_NAME to self-contained microservice..."

# Create backup
echo "Creating backup..."
cp -r "$SERVICE_DIR" "${SERVICE_DIR}.backup.$(date +%Y%m%d_%H%M%S)"

# Copy template files to service directory
echo "Copying template files..."
cp "$TEMPLATES_DIR/database.py" "$SERVICE_DIR/"
cp "$TEMPLATES_DIR/errors.py" "$SERVICE_DIR/"
cp "$TEMPLATES_DIR/auth.py" "$SERVICE_DIR/"
cp "$TEMPLATES_DIR/models.py" "$SERVICE_DIR/"
cp "$TEMPLATES_DIR/logging_config.py" "$SERVICE_DIR/"
cp "$TEMPLATES_DIR/middleware.py" "$SERVICE_DIR/"

# Update imports in main.py
echo "Updating imports in main.py..."
if [ -f "$SERVICE_DIR/main.py" ]; then
    # Create a backup of main.py
    cp "$SERVICE_DIR/main.py" "$SERVICE_DIR/main.py.backup"
    
    # Replace shared imports with local imports
    sed -i 's/from shared\.database/from .database/g' "$SERVICE_DIR/main.py"
    sed -i 's/from shared\.errors/from .errors/g' "$SERVICE_DIR/main.py"
    sed -i 's/from shared\.auth/from .auth/g' "$SERVICE_DIR/main.py"
    sed -i 's/from shared\.models/from .models/g' "$SERVICE_DIR/main.py"
    sed -i 's/from shared\.logging/from .logging_config/g' "$SERVICE_DIR/main.py"
    sed -i 's/from shared\.middleware/from .middleware/g' "$SERVICE_DIR/main.py"
    
    # Remove the sys.path.append line
    sed -i '/sys\.path\.append.*opsconductor/d' "$SERVICE_DIR/main.py"
    
    echo "Updated imports in main.py"
else
    echo "Warning: main.py not found in $SERVICE_DIR"
fi

# Update any other Python files in the service directory
echo "Updating imports in other Python files..."
find "$SERVICE_DIR" -name "*.py" -not -name "main.py" -exec sed -i 's/from shared\./from ./g' {} \;

echo "Migration completed for $SERVICE_NAME"
echo "Backup created at: ${SERVICE_DIR}.backup.$(date +%Y%m%d_%H%M%S)"
echo ""
echo "Next steps:"
echo "1. Test the service: cd $SERVICE_DIR && python main.py"
echo "2. Check for any remaining shared imports"
echo "3. Customize template files as needed"
echo "4. Update docker-compose.yml if necessary"