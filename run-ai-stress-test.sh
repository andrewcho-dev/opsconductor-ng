#!/bin/bash

# OpsConductor AI Chat Stress Test Runner
# This script will bombard the AI chat system for hours with progressively complex questions

echo "🤖 OpsConductor AI Chat Stress Test Framework"
echo "============================================="

# Check if Python is available
if ! command -v python3 &> /dev/null; then
    echo "❌ Python3 is required but not installed."
    exit 1
fi

# Install required Python packages
echo "📦 Installing required Python packages..."
pip3 install aiohttp --break-system-packages --quiet 2>/dev/null || echo "⚠️  Note: Some packages may already be installed"

# Get the base URL for the AI chat
BASE_URL="http://localhost:3000"
if [ ! -z "$1" ]; then
    BASE_URL="$1"
fi

# Get duration (default 4 hours)
DURATION="4.0"
if [ ! -z "$2" ]; then
    DURATION="$2"
fi

echo ""
echo "🎯 Target URL: $BASE_URL"
echo "⏱️  Duration: $DURATION hours"
echo "📈 Progressive Complexity: Level 1 → 5"
echo "🚀 Starting bombardment test..."
echo ""

# Create logs directory
mkdir -p logs

# Run different test scenarios
case "${3:-default}" in
    "quick")
        echo "🏃‍♂️ Running QUICK test (30 minutes, fast interval)"
        python3 ai_chat_stress_test.py --url "$BASE_URL" --duration 0.5 --interval 1000
        ;;
    "moderate")
        echo "🚶‍♂️ Running MODERATE test (2 hours)"
        python3 ai_chat_stress_test.py --url "$BASE_URL" --duration 2.0 --interval 2000
        ;;
    "intensive")
        echo "🏃‍♂️ Running INTENSIVE test (8 hours, aggressive)"
        python3 ai_chat_stress_test.py --url "$BASE_URL" --duration 8.0 --interval 1500
        ;;
    "extreme")
        echo "💥 Running EXTREME test (12 hours, very aggressive)"
        python3 ai_chat_stress_test.py --url "$BASE_URL" --duration 12.0 --interval 1000
        ;;
    *)
        echo "🎯 Running DEFAULT test ($DURATION hours)"
        python3 ai_chat_stress_test.py --url "$BASE_URL" --duration "$DURATION" --interval 3000
        ;;
esac

echo ""
echo "✅ Stress test completed!"
echo "📁 Check the logs/ directory for detailed results"
echo "📊 Log files contain response times, success rates, and full conversation traces"