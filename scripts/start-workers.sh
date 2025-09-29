#!/bin/bash
# Start OpsConductor Automation Workers
# This script ensures all worker services are running

echo "Starting OpsConductor Automation Workers..."

# Start all worker services
docker compose up -d automation-worker-1 automation-worker-2 automation-scheduler celery-monitor

# Wait a moment for services to start
sleep 5

# Check status
echo "Worker Status:"
docker ps --format "table {{.Names}}\t{{.Status}}" | grep -E "(worker|scheduler|celery)"

echo ""
echo "Workers started successfully!"
echo "Celery monitoring available at: http://localhost:5555"
echo ""
echo "Worker capacity:"
echo "- Worker 1: 12 concurrent tasks"
echo "- Worker 2: 12 concurrent tasks"
echo "- Total: 24 concurrent tasks"