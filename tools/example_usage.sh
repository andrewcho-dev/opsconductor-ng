#!/bin/bash
# Example usage workflow for tools_upsert.py

set -e

echo "=========================================="
echo "Tool Catalog Upsert - Example Workflow"
echo "=========================================="
echo ""

# Check if DATABASE_URL is set
if [ -z "$DATABASE_URL" ]; then
    echo "⚠️  DATABASE_URL not set. Using dummy DSN for dry-run demo."
    export DATABASE_URL="postgresql://dummy:dummy@localhost/dummy"
fi

echo "Step 1: Validate tool definitions (dry-run)"
echo "--------------------------------------------"
python3 tools/tools_upsert.py --glob "config/tools/**/*.yaml" --dry-run
echo ""

echo "Step 2: Check what files were found"
echo "--------------------------------------------"
find config/tools -name "*.yaml" -type f | sort
echo ""

echo "Step 3: Show example YAML content"
echo "--------------------------------------------"
echo "=== config/tools/linux/grep.yaml ==="
cat config/tools/linux/grep.yaml
echo ""
echo "=== config/tools/windows/powershell.yaml ==="
cat config/tools/windows/powershell.yaml
echo ""

echo "Step 4: Actual sync (requires real database)"
echo "--------------------------------------------"
echo "To sync to database, run:"
echo "  python3 tools/tools_upsert.py --glob 'config/tools/**/*.yaml'"
echo ""
echo "Or use Make target:"
echo "  make tools.sync"
echo ""

echo "Step 5: Verify tools in database"
echo "--------------------------------------------"
echo "After syncing, verify with:"
echo "  psql \$DATABASE_URL -c 'SELECT key, name, platform, tags FROM tool;'"
echo ""

echo "=========================================="
echo "✅ Example workflow complete!"
echo "=========================================="