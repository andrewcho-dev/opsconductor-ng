#!/bin/bash

# Pre-Build Compliance Check
# MANDATORY: Run before any docker build or deployment

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

echo "🔍 MANDATORY PRE-BUILD COMPLIANCE CHECK"
echo "========================================"

# Run compliance check
if ! "$SCRIPT_DIR/dockerfile-compliance-check.sh"; then
    echo
    echo "❌ BUILD BLOCKED: Compliance violations detected"
    echo "🚫 Fix all violations before building"
    echo "📋 See DOCKERFILE_STANDARDS.md for requirements"
    exit 1
fi

echo
echo "✅ COMPLIANCE CHECK PASSED"
echo "🚀 Build authorized to proceed"