# RabbitMQ to Celery Migration Plan

## Executive Summary

This document outlines the complete migration from RabbitMQ-based job execution to Celery for the OpsConductor platform. The current system has multiple confusing execution paths and scheduling mechanisms. Celery will provide a unified, robust job queue system that handles immediate execution, scheduled jobs, and recurring tasks in one cohesive framework.

## Current System Problems

### 1. Multiple Execution Paths
- **Direct execution**: Jobs bypass queuing entirely
- **RabbitMQ immediate**: Jobs sent to RabbitMQ for immediate consumption
- **RabbitMQ scheduled**: Jobs sent with scheduled_time but consumed immediately
- **Scheduler service**: Only handles recurring cron jobs in database

### 2. Architectural Confusion
- Scheduler service only processes recurring jobs from database
- RabbitMQ messages for scheduled jobs are consumed immediately (no delay)
- No unified job management or monitoring
- Complex message routing and queue management

### 3. Missing Features
- No built-in retry mechanisms
- Limited job monitoring and status tracking
- No workflow orchestration capabilities
- Difficult to scale job processing

## Target Celery Architecture

### 1. Unified Job Flow
```
Job Request → Jobs Service → Celery Task → Celery Worker → Execution
```

### 2. Single Responsibility Components
- **Jobs Service**: Creates and submits Celery tasks
- **Celery Workers**: Execute all job types (WinRM, SSH, HTTP, etc.)
- **Celery Beat**: Handles all scheduling (immediate, future, recurring)
- **Redis/Database**: Task queue and result storage

### 3. Job Types Mapping
- **Immediate jobs**: `task.delay()`
- **Scheduled jobs**: `task.apply_async(eta=datetime)`
- **Recurring jobs**: Celery Beat with cron expressions

## Components to Replace/Remove

### Services to Modify
1. **Jobs Service** (`/jobs-service/`)
   - Remove RabbitMQ publishing code
   - Replace with Celery task submission
   - Keep job run database management

2. **Executor Service** (`/executor-service/`)
   - Convert to Celery workers
   - Remove RabbitMQ consumer code
   - Keep all execution logic (WinRM, SSH, HTTP, etc.)

### Services to Remove/Simplify
1. **Scheduler Service** (`/scheduler-service/`)
   - **REMOVE ENTIRELY** - Celery Beat replaces this
   - Migrate existing schedules to Celery Beat configuration

### Infrastructure to Replace
1. **RabbitMQ**
   - Remove RabbitMQ container from docker-compose
   - Replace with Redis (Celery's preferred broker)

2. **Message Schemas** (`/shared/message_schemas.py`)
   - Remove RabbitMQ-specific schemas
   - Replace with Celery task parameter schemas

3. **Event Publisher/Consumer** (`/shared/utility_event_*.py`)
   - Remove RabbitMQ utilities
   - Replace with Celery task utilities

## Detailed Migration Steps

### Phase 1: Infrastructure Setup

#### 1.1 Add Celery Dependencies
```bash
# Add to requirements.txt
celery[redis]==5.3.4
redis==5.0.1
flower==2.0.1  # For monitoring
```

#### 1.2 Replace RabbitMQ with Redis
```yaml
# docker-compose.yml changes
# Remove rabbitmq service
# Add redis service
redis:
  image: redis:7-alpine
  ports:
    - "6379:6379"
  volumes:
    - redis_data:/data
```

#### 1.3 Create Celery Configuration
```python
# /shared/celery_config.py
from celery import Celery

celery_app = Celery(
    'opsconductor',
    broker='redis://redis:6379/0',
    backend='redis://redis:6379/0',
    include=[
        'executor_service.tasks',
        'jobs_service.tasks'
    ]
)

celery_app.conf.update(
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    timezone='UTC',
    enable_utc=True,
    task_track_started=True,
    task_time_limit=30 * 60,  # 30 minutes
    task_soft_time_limit=25 * 60,  # 25 minutes
    worker_prefetch_multiplier=1,
    task_acks_late=True,
    worker_max_tasks_per_child=1000,
)
```

### Phase 2: Convert Executor Service to Celery Workers

#### 2.1 Create Task Definitions
```python
# /executor-service/tasks.py
from shared.celery_config import celery_app
from .main import JobExecutor

job_executor = JobExecutor()

@celery_app.task(bind=True, max_retries=3)
def execute_job_run(self, job_run_id: int):
    """Execute a complete job run with all steps"""
    try:
        return job_executor.execute_job_run(job_run_id)
    except Exception as exc:
        # Retry with exponential backoff
        raise self.retry(exc=exc, countdown=60 * (2 ** self.request.retries))

@celery_app.task(bind=True, max_retries=3)
def execute_job_step(self, job_run_id: int, step_id: int):
    """Execute a single job step"""
    try:
        return job_executor.execute_step(job_run_id, step_id)
    except Exception as exc:
        raise self.retry(exc=exc, countdown=30 * (2 ** self.request.retries))
```

#### 2.2 Remove RabbitMQ Consumer
- Delete `/executor-service/rabbitmq_job_consumer.py`
- Remove RabbitMQ imports from main.py
- Remove consumer startup/shutdown code

#### 2.3 Create Celery Worker Startup
```python
# /executor-service/celery_worker.py
from shared.celery_config import celery_app

if __name__ == '__main__':
    celery_app.start()
```

### Phase 3: Modify Jobs Service

#### 3.1 Replace RabbitMQ with Celery Tasks
```python
# /jobs-service/main.py - Modified job execution
from executor_service.tasks import execute_job_run
from datetime import datetime, timedelta

@app.post("/jobs/{job_id}/run")
async def run_job(job_id: int, run_request: JobRunRequest):
    # Create job_run record (existing code)
    job_run = await create_job_run_record(job_id, run_request)
    
    # Submit to Celery instead of RabbitMQ
    if run_request.scheduled_time:
        # Scheduled execution
        task = execute_job_run.apply_async(
            args=[job_run["id"]],
            eta=run_request.scheduled_time
        )
    else:
        # Immediate execution (but still 1 minute delay as requested)
        scheduled_time = datetime.now(timezone.utc) + timedelta(minutes=1)
        task = execute_job_run.apply_async(
            args=[job_run["id"]],
            eta=scheduled_time
        )
    
    # Store Celery task ID for tracking
    await update_job_run_task_id(job_run["id"], task.id)
    
    return JobRunResponse(...)
```

#### 3.2 Add Task Tracking
```python
# Add celery_task_id column to job_runs table
ALTER TABLE job_runs ADD COLUMN celery_task_id VARCHAR(255);

# Add task status endpoint
@app.get("/jobs/runs/{run_id}/status")
async def get_job_run_status(run_id: int):
    job_run = await get_job_run(run_id)
    if job_run["celery_task_id"]:
        from shared.celery_config import celery_app
        task = celery_app.AsyncResult(job_run["celery_task_id"])
        return {
            "status": task.status,
            "result": task.result,
            "traceback": task.traceback
        }
```

### Phase 4: Replace Scheduler Service with Celery Beat

#### 4.1 Remove Scheduler Service
- Delete entire `/scheduler-service/` directory
- Remove from docker-compose.yml
- Remove from nginx routing

#### 4.2 Migrate Existing Schedules
```python
# Migration script: migrate_schedules_to_celery.py
from shared.database import get_db_cursor
from shared.celery_config import celery_app

def migrate_schedules():
    with get_db_cursor() as cursor:
        cursor.execute("SELECT * FROM schedules WHERE is_active = true")
        schedules = cursor.fetchall()
        
        beat_schedule = {}
        for schedule in schedules:
            beat_schedule[f"job_{schedule['job_id']}_schedule_{schedule['id']}"] = {
                'task': 'executor_service.tasks.execute_job_run',
                'schedule': crontab_from_string(schedule['cron']),
                'args': (schedule['job_id'],),
                'options': {'timezone': schedule['timezone']}
            }
        
        # Update Celery configuration
        celery_app.conf.beat_schedule = beat_schedule
```

#### 4.3 Create Celery Beat Service
```yaml
# docker-compose.yml
celery-beat:
  build: ./executor-service
  command: celery -A shared.celery_config beat --loglevel=info
  depends_on:
    - redis
    - postgres
  environment:
    - DATABASE_URL=postgresql://postgres:postgres@postgres:5432/opsconductor
    - REDIS_URL=redis://redis:6379/0
```

### Phase 5: Clean Up Shared Components

#### 5.1 Remove RabbitMQ Utilities
- Delete `/shared/utility_message_queue.py`
- Delete `/shared/utility_event_publisher.py`
- Delete `/shared/utility_event_consumer.py`
- Delete `/shared/message_schemas.py`

#### 5.2 Create Celery Utilities
```python
# /shared/celery_utils.py
from .celery_config import celery_app
from typing import Dict, Any, Optional
from datetime import datetime

def submit_job(job_run_id: int, scheduled_time: Optional[datetime] = None):
    """Submit job for execution"""
    from executor_service.tasks import execute_job_run
    
    if scheduled_time:
        return execute_job_run.apply_async(
            args=[job_run_id],
            eta=scheduled_time
        )
    else:
        return execute_job_run.delay(job_run_id)

def get_task_status(task_id: str):
    """Get task status and result"""
    task = celery_app.AsyncResult(task_id)
    return {
        'status': task.status,
        'result': task.result,
        'traceback': task.traceback
    }
```

### Phase 6: Update Docker Configuration

#### 6.1 New Docker Compose Structure
```yaml
version: '3.8'
services:
  # Remove rabbitmq service entirely
  
  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
    volumes:
      - redis_data:/data
  
  celery-worker:
    build: ./executor-service
    command: celery -A shared.celery_config worker --loglevel=info --concurrency=4
    depends_on:
      - redis
      - postgres
    environment:
      - DATABASE_URL=postgresql://postgres:postgres@postgres:5432/opsconductor
      - REDIS_URL=redis://redis:6379/0
    volumes:
      - ./shared:/home/opsconductor/shared
      - ./executor-service:/home/opsconductor/executor-service
  
  celery-beat:
    build: ./executor-service
    command: celery -A shared.celery_config beat --loglevel=info
    depends_on:
      - redis
      - postgres
    environment:
      - DATABASE_URL=postgresql://postgres:postgres@postgres:5432/opsconductor
      - REDIS_URL=redis://redis:6379/0
    volumes:
      - ./shared:/home/opsconductor/shared
      - ./executor-service:/home/opsconductor/executor-service
  
  flower:
    build: ./executor-service
    command: celery -A shared.celery_config flower --port=5555
    ports:
      - "5555:5555"
    depends_on:
      - redis
    environment:
      - REDIS_URL=redis://redis:6379/0

volumes:
  redis_data:
```

#### 6.2 Remove Scheduler Service References
- Remove from nginx.conf
- Remove from any service discovery
- Update health check endpoints

### Phase 7: Monitoring and Management

#### 7.1 Flower Dashboard
- Access at http://localhost:5555
- Real-time task monitoring
- Worker management
- Task history and statistics

#### 7.2 Update Health Checks
```python
# Add Celery health checks to jobs service
@app.get("/health")
async def health_check():
    # Check Celery connection
    from shared.celery_config import celery_app
    try:
        # Check if workers are available
        stats = celery_app.control.inspect().stats()
        celery_healthy = bool(stats)
    except:
        celery_healthy = False
    
    return {
        "status": "healthy" if celery_healthy else "unhealthy",
        "celery_workers": len(stats) if celery_healthy else 0
    }
```

## Benefits After Migration

### 1. Simplified Architecture
- Single job execution path through Celery
- No confusion between immediate/scheduled/recurring jobs
- Unified monitoring and management

### 2. Better Reliability
- Built-in retry mechanisms with exponential backoff
- Task result storage and tracking
- Dead letter queue handling

### 3. Enhanced Monitoring
- Real-time task monitoring with Flower
- Task history and performance metrics
- Worker health and capacity monitoring

### 4. Improved Scalability
- Easy horizontal scaling by adding workers
- Task routing to specialized workers
- Load balancing across workers

### 5. Advanced Features
- Task chaining and workflows
- Conditional task execution
- Priority queues
- Rate limiting

## Migration Timeline

### Week 1: Infrastructure
- Set up Redis and Celery configuration
- Create basic task definitions
- Test basic job execution

### Week 2: Jobs Service
- Modify job submission to use Celery
- Add task tracking and status endpoints
- Test immediate and scheduled jobs

### Week 3: Scheduler Migration
- Migrate existing schedules to Celery Beat
- Remove scheduler service
- Test recurring job execution

### Week 4: Cleanup and Testing
- Remove RabbitMQ and related code
- Comprehensive testing
- Performance optimization
- Documentation updates

## Rollback Plan

If issues arise during migration:

1. **Keep RabbitMQ running** during initial phases
2. **Dual execution** - run both systems temporarily
3. **Feature flags** to switch between systems
4. **Database backups** before schedule migration
5. **Quick revert** capability for each phase

## Testing Strategy

### 1. Unit Tests
- Test individual Celery tasks
- Mock external dependencies
- Verify retry mechanisms

### 2. Integration Tests
- End-to-end job execution
- Scheduled job processing
- Error handling and recovery

### 3. Performance Tests
- Load testing with multiple concurrent jobs
- Memory and CPU usage monitoring
- Task throughput measurement

### 4. Migration Tests
- Schedule migration accuracy
- Data integrity verification
- Backward compatibility

## Conclusion

This migration will transform the OpsConductor job execution system from a complex, multi-path architecture to a clean, unified Celery-based system. The result will be more reliable, scalable, and maintainable job processing with better monitoring and management capabilities.

The key success factors are:
1. **Phased approach** - migrate incrementally
2. **Preserve existing logic** - wrap, don't rewrite
3. **Comprehensive testing** - verify each phase
4. **Rollback capability** - maintain safety nets

This plan provides the roadmap for a successful migration that will significantly improve the platform's job execution capabilities.