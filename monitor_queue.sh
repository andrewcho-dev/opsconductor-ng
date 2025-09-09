#!/bin/bash

echo "=== OpsConductor Job Queue Monitor ==="
echo "Generated at: $(date)"
echo ""

echo "🔄 ACTIVE/QUEUED JOB RUNS:"
docker exec opsconductor-postgres psql -U postgres -d opsconductor -c "
SELECT 
    jr.id as run_id,
    j.name as job_name,
    jr.status,
    jr.queued_at::timestamp as queued_time,
    CASE 
        WHEN jr.status = 'queued' AND jr.queued_at + INTERVAL '1 minute' > NOW() 
        THEN 'Scheduled for: ' || (jr.queued_at + INTERVAL '1 minute')::timestamp
        WHEN jr.status = 'queued' AND jr.queued_at + INTERVAL '1 minute' <= NOW() 
        THEN '⚠️  OVERDUE - should have started!'
        WHEN jr.status = 'running' 
        THEN '🏃 Currently executing...'
        ELSE '✅ Completed'
    END as status_info
FROM job_runs jr
JOIN jobs j ON jr.job_id = j.id
WHERE jr.status IN ('queued', 'running') OR jr.queued_at > NOW() - INTERVAL '2 hours'
ORDER BY jr.id DESC
LIMIT 10;
" -t

echo ""
echo "📊 QUEUE SUMMARY:"
docker exec opsconductor-postgres psql -U postgres -d opsconductor -c "
SELECT 
    status,
    COUNT(*) as count,
    MIN(queued_at)::timestamp as oldest,
    MAX(queued_at)::timestamp as newest
FROM job_runs 
WHERE queued_at > NOW() - INTERVAL '24 hours'
GROUP BY status
ORDER BY 
    CASE status 
        WHEN 'queued' THEN 1 
        WHEN 'running' THEN 2 
        WHEN 'succeeded' THEN 3 
        WHEN 'failed' THEN 4 
    END;
" -t

echo ""
echo "🔧 CELERY WORKER STATUS:"
if docker exec opsconductor-celery-worker celery -A shared.tasks inspect active 2>/dev/null | grep -q "empty"; then
    echo "✅ Celery worker is idle (no active tasks)"
else
    echo "🏃 Celery worker has active tasks:"
    docker exec opsconductor-celery-worker celery -A shared.tasks inspect active 2>/dev/null
fi

echo ""
echo "📝 RECENT LOGS (last 5 lines):"
echo "Jobs Service:"
docker logs opsconductor-jobs --tail 3 2>/dev/null | grep -E "(Request|Job run|Error)" || echo "  No recent activity"

echo "Celery Worker:"
docker logs opsconductor-celery-worker --tail 3 2>/dev/null | grep -E "(Task|INFO|ERROR)" || echo "  No recent activity"