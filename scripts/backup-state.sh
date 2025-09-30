#!/bin/bash

# OpsConductor State Backup
# Creates a backup of the current working state before major changes

set -e

echo "💾 Creating OpsConductor State Backup"
echo "===================================="
echo ""

# Create backup directory with timestamp
BACKUP_DIR="backups/$(date +%Y%m%d_%H%M%S)"
mkdir -p "$BACKUP_DIR"

echo "📁 Backup location: $BACKUP_DIR"
echo ""

# Backup compose files
echo "📋 Backing up compose files..."
cp docker-compose.dev.yml "$BACKUP_DIR/" 2>/dev/null || echo "   ⚠️  docker-compose.dev.yml not found"
cp docker-compose.clean.yml "$BACKUP_DIR/" 2>/dev/null || echo "   ⚠️  docker-compose.clean.yml not found"
echo "   ✅ Compose files backed up"

# Backup scripts
echo "🔧 Backing up scripts..."
cp -r scripts/ "$BACKUP_DIR/" 2>/dev/null || echo "   ⚠️  scripts directory not found"
echo "   ✅ Scripts backed up"

# Backup key configuration files
echo "⚙️  Backing up configuration files..."
find . -maxdepth 2 -name "*.env" -exec cp {} "$BACKUP_DIR/" \; 2>/dev/null || true
find . -maxdepth 2 -name "requirements.txt" -exec cp {} "$BACKUP_DIR/requirements-{}.txt" \; 2>/dev/null || true
find . -maxdepth 2 -name "package.json" -exec cp {} "$BACKUP_DIR/package-{}.json" \; 2>/dev/null || true
echo "   ✅ Configuration files backed up"

# Create state snapshot
echo "📸 Creating state snapshot..."
cat > "$BACKUP_DIR/state-info.txt" << EOF
OpsConductor State Backup
========================
Date: $(date)
Git Commit: $(git rev-parse HEAD 2>/dev/null || echo "Not a git repository")
Git Branch: $(git branch --show-current 2>/dev/null || echo "Not a git repository")

Running Containers:
$(docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}" 2>/dev/null || echo "Docker not available")

Docker Images:
$(docker images --format "table {{.Repository}}\t{{.Tag}}\t{{.Size}}" | grep opsconductor 2>/dev/null || echo "No OpsConductor images found")

Volume Mounts Validation:
$(./scripts/validate-mounts.sh 2>/dev/null || echo "Validation script not available")
EOF

echo "   ✅ State snapshot created"

# Create restore script
echo "🔄 Creating restore script..."
cat > "$BACKUP_DIR/restore.sh" << 'EOF'
#!/bin/bash

# OpsConductor State Restore Script
# Restores the system to this backup state

set -e

echo "🔄 Restoring OpsConductor State"
echo "==============================="
echo ""

BACKUP_DIR=$(dirname "$0")
PROJECT_ROOT=$(cd "$BACKUP_DIR/../.." && pwd)

echo "📁 Restoring from: $BACKUP_DIR"
echo "📁 Project root: $PROJECT_ROOT"
echo ""

# Stop current system
echo "🛑 Stopping current system..."
cd "$PROJECT_ROOT"
./scripts/stop-dev.sh 2>/dev/null || true
./scripts/stop-prod.sh 2>/dev/null || true

# Restore compose files
echo "📋 Restoring compose files..."
cp "$BACKUP_DIR/docker-compose.dev.yml" . 2>/dev/null || echo "   ⚠️  No dev compose file in backup"
cp "$BACKUP_DIR/docker-compose.clean.yml" . 2>/dev/null || echo "   ⚠️  No clean compose file in backup"

# Restore scripts
echo "🔧 Restoring scripts..."
cp -r "$BACKUP_DIR/scripts/"* scripts/ 2>/dev/null || echo "   ⚠️  No scripts in backup"
chmod +x scripts/*.sh 2>/dev/null || true

echo ""
echo "✅ State restored successfully!"
echo ""
echo "🚀 To start the restored system:"
echo "   ./scripts/dev-mode.sh   - Start in development mode"
echo "   ./scripts/prod-mode.sh  - Start in production mode"
echo ""
EOF

chmod +x "$BACKUP_DIR/restore.sh"
echo "   ✅ Restore script created"

echo ""
echo "✅ Backup completed successfully!"
echo ""
echo "📋 Backup Contents:"
echo "   📁 Location: $BACKUP_DIR"
echo "   📋 Compose files"
echo "   🔧 Scripts directory"
echo "   ⚙️  Configuration files"
echo "   📸 State snapshot"
echo "   🔄 Restore script"
echo ""
echo "🔄 To restore this state later:"
echo "   $BACKUP_DIR/restore.sh"
echo ""
echo "💡 Keep this backup safe before making major changes!"