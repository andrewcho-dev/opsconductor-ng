#!/bin/bash
# Continuous Training Management Script

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
DAEMON_SCRIPT="$SCRIPT_DIR/continuous_training_daemon.py"
LOG_FILE="$SCRIPT_DIR/daemon.log"

case "$1" in
    start)
        echo "🚀 Starting continuous training system..."
        python3 "$DAEMON_SCRIPT" start
        ;;
    stop)
        echo "🛑 Stopping continuous training system..."
        python3 "$DAEMON_SCRIPT" stop
        ;;
    restart)
        echo "🔄 Restarting continuous training system..."
        python3 "$DAEMON_SCRIPT" restart
        ;;
    status)
        python3 "$DAEMON_SCRIPT" status
        ;;
    logs)
        if [ -f "$LOG_FILE" ]; then
            echo "📋 Recent logs:"
            tail -20 "$LOG_FILE"
        else
            echo "❌ No log file found"
        fi
        ;;
    follow)
        if [ -f "$LOG_FILE" ]; then
            echo "📋 Following logs (Ctrl+C to stop):"
            tail -f "$LOG_FILE"
        else
            echo "❌ No log file found"
        fi
        ;;
    stats)
        echo "📊 Training System Statistics:"
        echo "=============================="
        python3 -c "
import sys
sys.path.append('$SCRIPT_DIR')
from fixed_master_integration import FixedMasterIntegration
master = FixedMasterIntegration()
stats = master.get_training_stats()
print(f'📈 Total Examples: {stats[\"total_examples\"]}')
print(f'🌐 Internet Examples: {stats[\"internet_examples\"]}')
print(f'🤖 AI Examples: {stats[\"ai_examples\"]}')
print(f'⭐ Average Quality: {stats[\"avg_quality\"]:.2f}')
print(f'🎯 Average Confidence: {stats[\"avg_confidence\"]:.1f}%')
"
        ;;
    *)
        echo "Usage: $0 {start|stop|restart|status|logs|follow|stats}"
        echo ""
        echo "Commands:"
        echo "  start   - Start the continuous training daemon"
        echo "  stop    - Stop the continuous training daemon"
        echo "  restart - Restart the continuous training daemon"
        echo "  status  - Check if daemon is running"
        echo "  logs    - Show recent log entries"
        echo "  follow  - Follow log output in real-time"
        echo "  stats   - Show training data statistics"
        exit 1
        ;;
esac