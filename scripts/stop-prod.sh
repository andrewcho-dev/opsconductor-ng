#!/bin/bash

# Stop OpsConductor Production Mode

set -e

echo "🛑 Stopping OpsConductor PRODUCTION MODE..."

docker compose -f docker-compose.clean.yml down

echo "✅ Production mode stopped!"
echo ""
echo "🔧 Next steps:"
echo "   ./scripts/prod-mode.sh  - Start production mode again"
echo "   ./scripts/dev-mode.sh   - Start development mode"
echo ""