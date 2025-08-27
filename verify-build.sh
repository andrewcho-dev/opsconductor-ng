#!/bin/bash

echo "🔍 Verifying build changes..."

# Get current build hash
CURRENT_HASH=$(curl -k https://localhost:8443/ 2>/dev/null | grep -o 'main\.[a-f0-9]*\.js' | cut -d'.' -f2)

if [ -z "$CURRENT_HASH" ]; then
    echo "❌ Could not detect build hash - frontend may not be running"
    exit 1
fi

echo "Current build hash: $CURRENT_HASH"

# Store hash for comparison
echo "$CURRENT_HASH" > /tmp/last-build-hash

echo "✅ Build verification complete"