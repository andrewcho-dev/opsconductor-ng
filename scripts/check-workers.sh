#!/bin/bash
# Check OpsConductor Automation Workers Status

echo "=== OpsConductor Worker Status ==="
echo ""

echo "Docker Container Status:"
docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}" | grep -E "(worker|scheduler|celery|automation)"

echo ""
echo "Worker Logs (last 3 lines each):"
echo ""

echo "Worker 1:"
docker logs opsconductor-worker-1 --tail 3 2>/dev/null || echo "Worker 1 not running"

echo ""
echo "Worker 2:"
docker logs opsconductor-worker-2 --tail 3 2>/dev/null || echo "Worker 2 not running"

echo ""
echo "Scheduler:"
docker logs opsconductor-scheduler --tail 3 2>/dev/null || echo "Scheduler not running"

echo ""
echo "=== Quick Health Check ==="

# Check if workers are processing tasks
WORKER1_ACTIVE=$(docker logs opsconductor-worker-1 --tail 10 2>/dev/null | grep -c "Task.*succeeded\|Task.*failed" || echo "0")
WORKER2_ACTIVE=$(docker logs opsconductor-worker-2 --tail 10 2>/dev/null | grep -c "Task.*succeeded\|Task.*failed" || echo "0")

echo "Recent task activity:"
echo "- Worker 1: $WORKER1_ACTIVE recent tasks"
echo "- Worker 2: $WORKER2_ACTIVE recent tasks"

echo ""
echo "Celery Monitoring: http://localhost:5555"
echo "Total Worker Capacity: 24 concurrent tasks (2 workers × 12 each)"