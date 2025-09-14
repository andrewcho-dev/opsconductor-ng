# Celery Job Monitoring & Management System

## Overview

This document describes the comprehensive real-time monitoring and management system for Celery jobs in the OpsConductor automation service. The system provides visibility into job execution, queue status, worker health, and task management capabilities.

## Architecture Components

### 1. Celery Monitoring Service (`celery_monitor.py`)
- **Real-time task tracking**: Monitors all Celery tasks across their lifecycle
- **Worker health monitoring**: Tracks worker status, load, and performance
- **Queue monitoring**: Monitors queue lengths and message flow
- **System statistics**: Provides comprehensive system metrics

### 2. Flower Integration (Port 5555)
- **Web-based monitoring**: Accessible at `http://localhost:5555`
- **Task inspection**: Detailed task information and history
- **Worker management**: View worker processes and statistics
- **Queue visualization**: Real-time queue status and metrics
- **Authentication**: Basic auth (admin:admin123)

### 3. WebSocket Real-time Updates
- **Endpoint**: `/api/automation/monitoring/ws`
- **Real-time data**: Live updates every 2 seconds
- **Auto-reconnection**: Automatic reconnection on connection loss

### 4. REST API Endpoints

#### Monitoring Endpoints
- `GET /api/automation/monitoring/stats` - System statistics
- `GET /api/automation/monitoring/tasks` - Task information
- `GET /api/automation/monitoring/workers` - Worker status
- `GET /api/automation/monitoring/queues` - Queue information
- `GET /api/automation/monitoring/tasks/{task_id}` - Task details

#### Task Management Endpoints
- `POST /api/automation/monitoring/tasks/{task_id}/cancel` - Cancel running task
- `POST /api/automation/monitoring/tasks/{task_id}/retry` - Retry failed task

## Features

### Real-time Visibility
1. **Task Status Tracking**
   - PENDING: Task queued but not started
   - RECEIVED: Task received by worker
   - STARTED: Task execution begun
   - SUCCESS: Task completed successfully
   - FAILURE: Task failed with error
   - RETRY: Task being retried
   - REVOKED: Task cancelled

2. **Queue Monitoring**
   - Queue lengths and backlogs
   - Message flow rates
   - Consumer counts
   - Ready vs unacknowledged messages

3. **Worker Health**
   - Online/offline status
   - Active task counts
   - Processed task statistics
   - System load averages
   - Memory usage
   - Pool concurrency settings

### Task Management Actions

#### Cancel Tasks
- **When**: Tasks in PENDING, RECEIVED, or STARTED states
- **How**: `POST /api/automation/monitoring/tasks/{task_id}/cancel`
- **Effect**: 
  - Revokes task from Celery
  - Updates database status to 'cancelled'
  - Terminates running processes

#### Retry Tasks
- **When**: Tasks in FAILURE or REVOKED states
- **How**: `POST /api/automation/monitoring/tasks/{task_id}/retry`
- **Effect**:
  - Creates new task with same parameters
  - Generates new task ID
  - Preserves original execution history

#### Task Details
- **Endpoint**: `GET /api/automation/monitoring/tasks/{task_id}`
- **Information**:
  - Complete task lifecycle timestamps
  - Arguments and keyword arguments
  - Result data or error information
  - Retry count and history
  - Worker assignment
  - Queue routing

## Frontend Integration

### Job Monitoring Dashboard
- **Location**: `/monitoring` in the frontend
- **Features**:
  - Real-time task grid with status indicators
  - Worker status overview
  - Queue length monitoring
  - System statistics dashboard
  - Task action buttons (Cancel/Retry/Details)

### WebSocket Connection
```typescript
// Automatic connection to monitoring WebSocket
const wsUrl = `${protocol}//${window.location.host}/api/automation/monitoring/ws`;
```

### Task Actions
```typescript
// Cancel task
await fetch(`/api/automation/monitoring/tasks/${taskId}/cancel`, { method: 'POST' });

// Retry task
await fetch(`/api/automation/monitoring/tasks/${taskId}/retry`, { method: 'POST' });
```

## Database Integration

### Execution Tracking
- **Table**: `automation.job_executions`
- **Key Change**: `execution_id` now uses Celery task ID for direct correlation
- **Benefits**: 
  - Direct mapping between Celery tasks and database records
  - Simplified status updates
  - Better error tracking

### Status Synchronization
- **Real-time updates**: Worker updates database as tasks progress
- **Status consistency**: Celery state matches database state
- **Error handling**: Failed tasks properly recorded with error messages

## Troubleshooting Common Issues

### Stuck Tasks
1. **Identification**: Tasks showing STARTED for extended periods
2. **Investigation**: Check worker logs and system resources
3. **Resolution**: Cancel and retry, or restart workers

### Queue Backlogs
1. **Identification**: High queue lengths with low processing rates
2. **Investigation**: Check worker availability and performance
3. **Resolution**: Scale workers or optimize task performance

### Worker Issues
1. **Identification**: Workers showing offline or high load
2. **Investigation**: Check system resources and worker logs
3. **Resolution**: Restart workers or adjust concurrency settings

## Configuration

### Docker Compose Services
```yaml
# Celery Worker
automation-worker:
  command: celery -A worker worker --loglevel=info --concurrency=4

# Celery Scheduler
automation-scheduler:
  command: celery -A worker beat --loglevel=info

# Flower Monitoring
celery-monitor:
  command: celery -A worker flower --port=5555 --broker=redis://redis:6379/3
  ports:
    - "5555:5555"
```

### Environment Variables
- `REDIS_URL`: Redis broker connection
- `DATABASE_URL`: PostgreSQL connection for execution tracking
- `FLOWER_BASIC_AUTH`: Flower authentication credentials

## Best Practices

### Task Design
1. **Idempotent tasks**: Design tasks to be safely retryable
2. **Timeout handling**: Set appropriate task timeouts
3. **Error handling**: Implement proper exception handling
4. **Progress reporting**: Update task progress for long-running operations

### Monitoring
1. **Regular checks**: Monitor queue lengths and worker health
2. **Alert thresholds**: Set up alerts for stuck tasks or high queue backlogs
3. **Performance tracking**: Monitor task execution times and success rates
4. **Resource monitoring**: Track worker memory and CPU usage

### Maintenance
1. **Worker restarts**: Regularly restart workers to prevent memory leaks
2. **Queue cleanup**: Monitor and clean up old task results
3. **Database maintenance**: Archive old execution records
4. **Log rotation**: Manage Celery and worker log files

## Security Considerations

### Access Control
- **Flower access**: Protected with basic authentication
- **API endpoints**: Require valid JWT tokens
- **WebSocket connections**: Authenticated connections only

### Task Isolation
- **Worker processes**: Isolated execution environments
- **Resource limits**: Memory and CPU constraints
- **Network access**: Controlled outbound connections

This monitoring system provides comprehensive visibility and control over the Celery job execution pipeline, enabling proactive management and troubleshooting of automation workflows.