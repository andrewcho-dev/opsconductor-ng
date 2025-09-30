#!/bin/bash

# Stop OpsConductor Development Mode

set -e

echo "🛑 Stopping OpsConductor DEVELOPMENT MODE..."

docker compose -f docker-compose.dev.yml down

echo "✅ Development mode stopped!"
echo ""
echo "🔧 Next steps:"
echo "   ./scripts/dev-mode.sh   - Start development mode again"
echo "   ./scripts/prod-mode.sh  - Start production mode"
echo ""