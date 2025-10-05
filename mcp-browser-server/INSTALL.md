# Installation Guide - MCP Browser Server

## Prerequisites

The MCP Browser Server requires Node.js 18+ to be installed on your system.

## Step 1: Install Node.js

### Option A: Using NodeSource (Recommended)

```bash
# Install Node.js 20.x LTS
curl -fsSL https://deb.nodesource.com/setup_20.x | sudo -E bash -
sudo apt-get install -y nodejs

# Verify installation
node --version  # Should show v20.x.x
npm --version   # Should show 10.x.x
```

### Option B: Using NVM (Node Version Manager)

```bash
# Install NVM
curl -o- https://raw.githubusercontent.com/nvm-sh/nvm/v0.39.0/install.sh | bash

# Reload shell
source ~/.bashrc

# Install Node.js
nvm install 20
nvm use 20

# Verify installation
node --version
npm --version
```

### Option C: Using apt (Ubuntu/Debian)

```bash
# Note: This may install an older version
sudo apt update
sudo apt install -y nodejs npm

# Verify installation
node --version
npm --version
```

## Step 2: Install MCP Browser Server

Once Node.js is installed:

```bash
cd /home/opsconductor/opsconductor-ng/mcp-browser-server
./setup.sh
```

This will:
1. Install npm dependencies
2. Download Playwright browsers
3. Build TypeScript code
4. Display configuration instructions

## Step 3: Verify Installation

```bash
cd /home/opsconductor/opsconductor-ng/mcp-browser-server
npm start
```

You should see:
```
OpsConductor Browser MCP Server running on stdio
```

Press Ctrl+C to stop.

## Step 4: Configure VS Code

The MCP server configuration has already been added to `.vscode/settings.json`.

Restart VS Code to load the new configuration.

## Step 5: Test

In VS Code, ask Zencoder:
```
Can you use the browser to navigate to http://localhost:3100?
```

A browser window should open and navigate to your frontend.

## Troubleshooting

### Node.js Not Found After Installation

If `node` command is not found after installation:

```bash
# Reload your shell configuration
source ~/.bashrc
# or
source ~/.profile
```

### Permission Errors

If you get permission errors during npm install:

```bash
# Fix npm permissions
mkdir -p ~/.npm-global
npm config set prefix '~/.npm-global'
echo 'export PATH=~/.npm-global/bin:$PATH' >> ~/.bashrc
source ~/.bashrc
```

### Playwright Browser Installation Fails

If browser installation fails:

```bash
# Install system dependencies
sudo apt-get install -y \
    libnss3 \
    libnspr4 \
    libatk1.0-0 \
    libatk-bridge2.0-0 \
    libcups2 \
    libdrm2 \
    libdbus-1-3 \
    libxkbcommon0 \
    libxcomposite1 \
    libxdamage1 \
    libxfixes3 \
    libxrandr2 \
    libgbm1 \
    libpango-1.0-0 \
    libcairo2 \
    libasound2

# Then retry browser installation
cd /home/opsconductor/opsconductor-ng/mcp-browser-server
npm run install-browsers
```

### VS Code Can't Find MCP Server

1. Verify the build completed: `ls -la dist/index.js`
2. Check VS Code settings: `.vscode/settings.json`
3. Restart VS Code completely
4. Check VS Code Output panel for MCP errors

## System Requirements

- **OS**: Linux (Ubuntu 20.04+), macOS, or Windows with WSL2
- **Node.js**: 18.x or 20.x LTS
- **RAM**: 2GB minimum (4GB recommended)
- **Disk**: 500MB for Chromium browser

## Next Steps

Once installed, see:
- [E2E Testing Setup Guide](../E2E_TESTING_SETUP.md)
- [E2E Test Documentation](../tests/e2e/README.md)
- [MCP Browser Server README](./README.md)