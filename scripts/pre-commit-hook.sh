#!/bin/bash
# Pre-commit hook to validate volume mounts
# To install: cp scripts/pre-commit-hook.sh .git/hooks/pre-commit && chmod +x .git/hooks/pre-commit

echo "🔍 Validating volume mounts before commit..."

# Run the volume mount checker
if ! ./scripts/check-volume-mounts.sh; then
    echo ""
    echo "❌ Commit blocked due to dangerous volume mount configuration!"
    echo "🔧 Fix the volume mounts and try again."
    echo "📖 See .zenrules/selective-volume-mounts.md for guidance."
    exit 1
fi

echo "✅ Volume mounts validation passed!"