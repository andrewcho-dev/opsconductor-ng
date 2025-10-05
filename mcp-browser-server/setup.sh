#!/bin/bash

# OpsConductor Browser MCP Server Setup Script

set -e

echo "🚀 Setting up OpsConductor Browser MCP Server..."

# Check if Node.js is installed
if ! command -v node &> /dev/null; then
    echo "❌ Node.js is not installed."
    echo ""
    echo "Please install Node.js 18+ first:"
    echo ""
    echo "  curl -fsSL https://deb.nodesource.com/setup_20.x | sudo -E bash -"
    echo "  sudo apt-get install -y nodejs"
    echo ""
    echo "Or see INSTALL.md for other installation methods."
    exit 1
fi

echo "✅ Node.js version: $(node --version)"

# Check if npm is installed
if ! command -v npm &> /dev/null; then
    echo "❌ npm is not installed."
    echo "Please install npm (usually comes with Node.js)"
    exit 1
fi

echo "✅ npm version: $(npm --version)"

# Install dependencies
echo "📦 Installing dependencies..."
cd "$(dirname "$0")"
npm install

# Install Playwright browsers
echo "🌐 Installing Playwright browsers..."
npm run install-browsers

# Build TypeScript
echo "🔨 Building TypeScript..."
npm run build

echo ""
echo "✅ Setup complete!"
echo ""
echo "Next steps:"
echo "1. Configure VS Code MCP settings (see README.md)"
echo "2. Start the server: npm start"
echo "3. Or use in development mode: npm run dev"
echo ""
echo "For VS Code integration, add this to .vscode/settings.json:"
echo ""
echo '{
  "mcp.servers": {
    "browser": {
      "command": "node",
      "args": ["'$(pwd)'/dist/index.js"],
      "env": {}
    }
  }
}'