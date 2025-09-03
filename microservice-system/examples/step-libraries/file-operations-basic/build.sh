#!/bin/bash

# Build script for file-operations-basic step library

set -e

LIBRARY_NAME="file-operations-basic"
VERSION="1.0.0"
OUTPUT_FILE="${LIBRARY_NAME}-${VERSION}.zip"

echo "🔨 Building ${LIBRARY_NAME} v${VERSION}..."

# Clean previous builds
rm -f "${OUTPUT_FILE}"

# Create ZIP package
zip -r "${OUTPUT_FILE}" \
    manifest.json \
    steps/ \
    executors/ \
    docs/ \
    -x "*.DS_Store" "*.git*" "build.sh"

echo "✅ Library packaged: ${OUTPUT_FILE}"
echo "📦 Package contents:"
unzip -l "${OUTPUT_FILE}"

echo ""
echo "🚀 To install this library:"
echo "  1. Start OpsConductor system"
echo "  2. Open the frontend at http://localhost"
echo "  3. Go to Visual Job Builder"
echo "  4. Click 'Manage' in the Step Library panel"
echo "  5. Upload the ${OUTPUT_FILE} file"