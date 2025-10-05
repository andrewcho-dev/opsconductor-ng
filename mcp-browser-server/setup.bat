@echo off
REM MCP Browser Server - Windows Setup Script
REM This script sets up the MCP browser server on Windows

echo ========================================
echo MCP Browser Server - Windows Setup
echo ========================================
echo.

REM Check if Node.js is installed
where node >nul 2>nul
if %ERRORLEVEL% NEQ 0 (
    echo [ERROR] Node.js is not installed!
    echo.
    echo Please install Node.js 18 or higher from:
    echo https://nodejs.org/
    echo.
    echo Or use one of these methods:
    echo   - Chocolatey: choco install nodejs-lts
    echo   - Winget: winget install OpenJS.NodeJS.LTS
    echo.
    pause
    exit /b 1
)

REM Check Node.js version
echo [1/5] Checking Node.js version...
node --version
npm --version
echo.

REM Install dependencies
echo [2/5] Installing dependencies...
call npm install
if %ERRORLEVEL% NEQ 0 (
    echo [ERROR] Failed to install dependencies
    pause
    exit /b 1
)
echo.

REM Install Playwright browsers
echo [3/5] Installing Playwright Chromium browser...
echo This may take a few minutes...
call npx playwright install chromium
if %ERRORLEVEL% NEQ 0 (
    echo [ERROR] Failed to install Playwright browsers
    pause
    exit /b 1
)
echo.

REM Build TypeScript
echo [4/5] Building TypeScript...
call npm run build
if %ERRORLEVEL% NEQ 0 (
    echo [ERROR] Failed to build TypeScript
    pause
    exit /b 1
)
echo.

REM Create screenshots directory
echo [5/5] Creating screenshots directory...
if not exist "screenshots" mkdir screenshots
echo.

REM Get the current directory
set CURRENT_DIR=%CD%

echo ========================================
echo Setup Complete! ✓
echo ========================================
echo.
echo Next steps:
echo.
echo 1. Configure VS Code settings.json:
echo.
echo    {
echo      "mcp.servers": {
echo        "browser": {
echo          "command": "node",
echo          "args": [
echo            "%CURRENT_DIR:\=\\%\\dist\\index.js"
echo          ]
echo        }
echo      }
echo    }
echo.
echo 2. Restart VS Code
echo.
echo 3. Test by asking Zencoder:
echo    "Navigate to http://YOUR-SERVER:3100 and take a screenshot"
echo.
echo For detailed instructions, see WINDOWS_SETUP.md
echo.
pause