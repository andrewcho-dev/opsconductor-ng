# Phase 7: GO/NO-GO Release Checklist

## 📋 Overview

This checklist ensures **all production-critical features** are implemented and tested before Phase 7 (Stage E Execution) goes live.

**Purpose**: Prevent 3am production incidents by validating safety features, database schema, queue semantics, and observability.

**Usage**: Check each item before release. All items must be ✅ **GO** before production deployment.

---

## 🗄️ 1. Database Schema

### 1.1 Tables & ENUMs

- [ ] **GO**: All 7 tables created (`executions`, `execution_steps`, `approvals`, `execution_events`, `execution_queue`, `execution_dlq`, `execution_locks`)
- [ ] **GO**: All 4 ENUMs created (`execution_status`, `execution_mode`, `sla_class`, `approval_state`)
- [ ] **GO**: `timeout_policies` table created with 6 seed rows (fast/medium/long × read/modify/deploy)
- [ ] **GO**: All tables have `timestamptz` (not `timestamp`) for timezone awareness
- [ ] **GO**: Indexes created separately (not inline with CREATE TABLE for Postgres compatibility)

**Verification**:
```sql
-- Check tables exist
SELECT table_name FROM information_schema.tables 
WHERE table_name IN ('executions', 'execution_steps', 'approvals', 'execution_events', 'execution_queue', 'execution_dlq', 'execution_locks', 'timeout_policies');
-- Expected: 8 rows

-- Check ENUMs exist
SELECT typname FROM pg_type 
WHERE typname IN ('execution_status', 'execution_mode', 'sla_class', 'approval_state');
-- Expected: 4 rows

-- Check timeout policies seeded
SELECT COUNT(*) FROM timeout_policies;
-- Expected: 6 rows
```

### 1.2 Idempotency & Uniqueness

- [ ] **GO**: Unique index `ux_exec_tenant_idem` on `(tenant_id, idempotency_key)` exists
- [ ] **GO**: `plan_snapshot` column stores frozen plan (JSONB)
- [ ] **GO**: `plan_hash` column stores canonical hash (VARCHAR(64))
- [ ] **GO**: Tenant-scoped uniqueness prevents cross-tenant collisions

**Verification**:
```sql
-- Check unique index exists
SELECT indexname FROM pg_indexes 
WHERE tablename = 'executions' AND indexname = 'ux_exec_tenant_idem';
-- Expected: 1 row

-- Check plan snapshot stored
SELECT id, plan_snapshot IS NOT NULL, plan_hash IS NOT NULL 
FROM executions LIMIT 1;
-- Expected: Both TRUE
```

### 1.3 Constraints & Validation

- [ ] **GO**: `valid_cancellation` CHECK constraint ensures `cancelled_by` + `cancelled_at` set together
- [ ] **GO**: `valid_result_size` CHECK constraint caps `result_summary` at 10KB
- [ ] **GO**: `valid_timing` CHECK constraint validates `started_at >= created_at` and `ended_at >= started_at`
- [ ] **GO**: `valid_timeout` CHECK constraint ensures `timeout_ms > 0`

**Verification**:
```sql
-- Check constraints exist
SELECT conname FROM pg_constraint 
WHERE conrelid = 'executions'::regclass 
AND conname IN ('valid_cancellation', 'valid_result_size', 'valid_timing', 'valid_timeout');
-- Expected: 4 rows
```

### 1.4 Observability Fields

- [ ] **GO**: `worker_id` column exists (VARCHAR(100))
- [ ] **GO**: `lease_renewals` column exists (INT DEFAULT 0)
- [ ] **GO**: `cancel_checks_performed` column exists (INT DEFAULT 0)
- [ ] **GO**: `last_transition_at`, `last_transition_by`, `last_transition_from` columns exist (FSM audit)
- [ ] **GO**: `timeout_policy_id` column exists (VARCHAR(50))

**Verification**:
```sql
-- Check observability columns exist
SELECT column_name FROM information_schema.columns 
WHERE table_name = 'executions' 
AND column_name IN ('worker_id', 'lease_renewals', 'cancel_checks_performed', 'last_transition_at', 'last_transition_by', 'last_transition_from', 'timeout_policy_id');
-- Expected: 7 rows
```

---

## 🚀 2. Executor Paths

### 2.1 Immediate Execution

- [ ] **GO**: Immediate path handles operations <10s
- [ ] **GO**: Mode decision uses `estimate_duration(plan)` + `can_parallelize(plan)`
- [ ] **GO**: Returns results synchronously (1-10s response time)
- [ ] **GO**: Does NOT depend on Redis (works even if Redis down)

**Test**:
```python
# Test immediate execution
plan = create_simple_query_plan()  # <10s operation
result = await executor.execute(plan, context)
assert result.execution_mode == "immediate"
assert result.duration_ms < 10_000
```

### 2.2 Background Execution

- [ ] **GO**: Background path handles operations >30s
- [ ] **GO**: Enqueues to Redis queue with priority
- [ ] **GO**: Returns job ID immediately (not blocking)
- [ ] **GO**: Worker picks up job and executes asynchronously
- [ ] **GO**: Progress updates emitted via WebSocket/SSE/poll

**Test**:
```python
# Test background execution
plan = create_deploy_plan(target_count=50)  # >30s operation
result = await executor.execute(plan, context)
assert result.execution_mode == "background"
assert result.job_id is not None
assert result.status == "queued"
```

---

## 🔒 3. Safety Features

### 3.1 Idempotency

- [ ] **GO**: Duplicate submit returns same execution (no duplicate side-effects)
- [ ] **GO**: Idempotency key = `sha256(canonical_json(plan) + tenant_id + actor_id)`
- [ ] **GO**: Canonical JSON uses sorted keys, sorted targets, no whitespace
- [ ] **GO**: Test: Two logically identical plans with different target order yield identical `plan_hash`

**Test**:
```python
# Test idempotency
plan = create_plan()
exec1 = await executor.execute(plan, context)
exec2 = await executor.execute(plan, context)  # Duplicate submit
assert exec1.execution_id == exec2.execution_id  # Same execution
```

### 3.2 Mutex

- [ ] **GO**: Per-asset locking prevents concurrent operations
- [ ] **GO**: Lock key format: `lock:v1:{tenant_id}:{target_ref}:{action}`
- [ ] **GO**: Owner tags prevent unauthorized release
- [ ] **GO**: Stale lock reaper cleans up expired locks
- [ ] **GO**: Mutex released even on exceptions (try/finally)

**Test**:
```python
# Test mutex prevents concurrent operations
plan1 = create_restart_plan(target="server-01")
plan2 = create_restart_plan(target="server-01")

# Start first execution
exec1_task = asyncio.create_task(executor.execute(plan1, context))
await asyncio.sleep(0.1)  # Let it acquire lock

# Try second execution (should fail)
with pytest.raises(ResourceBusyError):
    await executor.execute(plan2, context)
```

### 3.3 RBAC (Defense in Depth)

- [ ] **GO**: API tier validates permissions (first line of defense)
- [ ] **GO**: Worker validates permissions (second line of defense, mandatory for both immediate + background)
- [ ] **GO**: Tenant isolation enforced (actor.tenant_id == requested.tenant_id)
- [ ] **GO**: Action authorization checked (actor has required permission)
- [ ] **GO**: `rbac_violation` events logged for SOC/audit queries

**Test**:
```python
# Test worker-side RBAC
plan = create_plan()
context = create_context(actor_id="attacker", tenant_id="victim-tenant")

# Worker should reject (defense in depth)
with pytest.raises(PermissionError):
    await worker.process_job(plan, context)

# Verify rbac_violation event logged
events = await db.execution_events.find(event_type="rbac_violation")
assert len(events) > 0
```

### 3.4 Secrets

- [ ] **GO**: Just-in-time credential resolution (not stored in plan)
- [ ] **GO**: Automatic log masking at sink level (handler, not call sites)
- [ ] **GO**: Denylist patterns: password, token, key, secret, credential, api_key, private_key
- [ ] **GO**: Unit test feeds known secret-shaped payloads and asserts redaction

**Test**:
```python
# Test log masking at sink level
logger.info("Auth failed", extra={"password": "P@ssw0rd123"})
log_output = capture_logs()
assert "P@ssw0rd123" not in log_output  # Secret masked
assert "***REDACTED***" in log_output  # Redaction marker present
```

### 3.5 Cancellation

- [ ] **GO**: Cancel request is idempotent (multiple calls safe)
- [ ] **GO**: `cancelled_by` + `cancelled_at` set atomically (CHECK constraint)
- [ ] **GO**: Mutex released even on cancellation (try/finally)
- [ ] **GO**: Steps in progress complete (best-effort), future steps skipped
- [ ] **GO**: Cancellation token checked between steps

**Test**:
```python
# Test cancellation mid-run
plan = create_long_plan(steps=10)
exec_task = asyncio.create_task(executor.execute(plan, context))
await asyncio.sleep(1)  # Let it start

# Cancel
await cancellation_manager.request_cancellation(exec_id, user_id, "User requested")

# Wait for completion
result = await exec_task
assert result.status == "cancelled"
assert result.cancelled_by == user_id

# Verify mutex released
lock_status = await mutex_manager.check_lock_status(tenant_id, target_ref, action)
assert lock_status is None  # Lock released
```

### 3.6 Timeout

- [ ] **GO**: SLA-based timeout enforcement (fast: 10s, medium: 30s, long: 10min)
- [ ] **GO**: Timeout policy table stores `execution_timeout_ms` + `step_timeout_ms` per SLA × action class
- [ ] **GO**: `timed_out` flag set in database
- [ ] **GO**: `timeout_policy_id` stored for forensics

**Test**:
```python
# Test timeout enforced
plan = create_slow_plan(duration=20)  # 20 seconds
context = create_context(sla_class="fast")  # 10 second timeout

with pytest.raises(asyncio.TimeoutError):
    await executor.execute(plan, context)

# Verify timeout recorded
execution = await db.executions.get(exec_id)
assert execution.timed_out == True
assert execution.timeout_policy_id == "fast_read"
```

### 3.7 Log Masking

- [ ] **GO**: Masking enforced at logger handler (sink level, not call sites)
- [ ] **GO**: Recursive masking handles nested dictionaries
- [ ] **GO**: Exception messages containing secrets are masked
- [ ] **GO**: Unit test verifies secrets never appear in log output

**Test**:
```python
# Test sink-level masking
try:
    raise ValueError("Auth failed with password: P@ssw0rd123")
except ValueError:
    logger.exception("Error occurred")

log_output = capture_logs()
assert "P@ssw0rd123" not in log_output  # Secret masked in exception
```

---

## 🔄 4. FSM & State Transitions

### 4.1 Legal Transitions

- [ ] **GO**: FSM enforces legal state transitions (e.g., `pending → running`, not `pending → succeeded`)
- [ ] **GO**: Terminal states (`succeeded`, `failed`, `cancelled`, `rejected`) cannot transition
- [ ] **GO**: `last_transition_at`, `last_transition_by`, `last_transition_from` persisted for audit
- [ ] **GO**: `FSMError` raised on illegal transition

**Test**:
```python
# Test illegal transition rejected
with pytest.raises(FSMError, match="Illegal state transition"):
    await transition_status(
        execution_id=exec_id,
        from_status="pending",
        to_status="succeeded",  # Illegal: must go through running
        actor_id=user_id,
        db=db
    )
```

---

## 📦 5. Queue & Background Jobs

### 5.1 Queue Semantics

- [ ] **GO**: Priority-based dequeue (0=urgent, 50=normal, 100=bulk)
- [ ] **GO**: Visibility timeout (lease mechanism) prevents duplicate execution
- [ ] **GO**: Lease timeout = `max(step_timeout + buffer, 2× p95_step_duration)`
- [ ] **GO**: Lease renewal supported for long-running jobs
- [ ] **GO**: Graceful shutdown requeues in-progress jobs

**Test**:
```python
# Test lease prevents duplicate execution
job = await queue.enqueue(plan, context, priority=50)
job1 = await queue.dequeue(worker_id="worker-01", lease_duration=300)
job2 = await queue.dequeue(worker_id="worker-02", lease_duration=300)
assert job2 is None  # Job leased to worker-01, not visible to worker-02
```

### 5.2 Dead Letter Queue (DLQ)

- [ ] **GO**: Jobs pushed to DLQ after max attempts (fast: 3, medium: 5, long: 3)
- [ ] **GO**: Exponential backoff on retry (2^attempt seconds)
- [ ] **GO**: DLQ metrics tracked (alert on growth)
- [ ] **GO**: Max lease renewals enforced (fast: 1, medium: 3, long: 10)

**Test**:
```python
# Test DLQ after max attempts
job = await queue.enqueue(plan, context, max_attempts=3)
for i in range(3):
    await queue.fail_job(job.id, error="Connection timeout")

# Verify pushed to DLQ
dlq_jobs = await db.execution_dlq.find(execution_id=exec_id)
assert len(dlq_jobs) == 1
```

### 5.3 Worker Crash Recovery

- [ ] **GO**: Worker crash → job becomes visible after lease expiration
- [ ] **GO**: Job requeued automatically (no manual intervention)
- [ ] **GO**: No duplicate side-effects (idempotency prevents)
- [ ] **GO**: Lease expiration reaper runs every 60s

**Test**:
```python
# Test worker crash recovery
job = await queue.enqueue(plan, context)
job_data = await queue.dequeue(worker_id="worker-01", lease_duration=5)  # 5 second lease

# Simulate worker crash (don't complete job)
await asyncio.sleep(6)  # Wait for lease to expire

# Job should be visible again
job_data2 = await queue.dequeue(worker_id="worker-02", lease_duration=300)
assert job_data2 is not None  # Job reappeared
assert job_data2.execution_id == job_data.execution_id
```

---

## ✅ 6. Approval Workflow

### 6.1 Approval Levels

- [ ] **GO**: Level 0 (auto-execute) works for read-only operations
- [ ] **GO**: Level 1 (confirmation) requires user click
- [ ] **GO**: Level 2 (plan review) requires runbook URL
- [ ] **GO**: Level 3 (step-by-step) requires approval per step
- [ ] **GO**: Approval records include `principal`, `auth_method`, `source_ip`

**Test**:
```python
# Test approval levels
plan_readonly = create_query_plan()
assert determine_approval_level(plan_readonly) == 0  # Auto-execute

plan_modify = create_restart_plan()
assert determine_approval_level(plan_modify) == 1  # Confirmation

plan_deploy = create_deploy_plan()
assert determine_approval_level(plan_deploy) == 2  # Plan review
```

### 6.2 Approval Integrity

- [ ] **GO**: Approval bound to `plan_hash` + `plan_snapshot_hash`
- [ ] **GO**: Plan change invalidates approval (automatic detection)
- [ ] **GO**: `ApprovalInvalidatedError` raised if plan changed
- [ ] **GO**: Requires re-approval after plan change

**Test**:
```python
# Test approval invalidation on plan change
approval = await approval_manager.request_approval(plan, context)
await approval_manager.approve(approval.id, approver_id)

# Modify plan
plan.steps.append(new_step)

# Try to execute (should fail)
with pytest.raises(ApprovalInvalidatedError):
    await executor.execute(plan, context)
```

---

## 📊 7. Progress & Observability

### 7.1 Progress Tracking

- [ ] **GO**: WebSocket live updates work
- [ ] **GO**: SSE fallback works (WebSocket unavailable)
- [ ] **GO**: Long-poll fallback works (SSE unavailable)
- [ ] **GO**: Transport selection order: WS → SSE → poll
- [ ] **GO**: UI shows which transport is used (for debugging)
- [ ] **GO**: Database-backed progress (survives reconnects)

**Test**:
```python
# Test progress updates
plan = create_deploy_plan(target_count=10)
exec_task = asyncio.create_task(executor.execute(plan, context))

# Subscribe to progress
events = []
async for event in progress_tracker.subscribe(exec_id):
    events.append(event)
    if event["type"] == "execution_completed":
        break

# Verify events received
assert len(events) > 0
assert events[0]["type"] == "execution_started"
assert events[-1]["type"] == "execution_completed"
```

### 7.2 Structured Logging

- [ ] **GO**: All executions logged with required fields:
  - `request_id`, `plan_hash`, `exec_id`, `actor_id`, `tenant_id`
  - `action`, `targets`, `approval_level`, `timing`, `status`
  - `error_class`, `duration_ms`, `retries_total`, `queue_wait_ms`
  - `worker_id`, `lease_renewals`, `cancel_checks_performed`
- [ ] **GO**: Correlation IDs propagate to downstream services
- [ ] **GO**: User cancellations separated from system failures in metrics

**Verification**:
```bash
# Check logs contain required fields
grep "execution_started" logs/app.log | jq '.request_id, .plan_hash, .exec_id, .actor_id, .tenant_id'
# Expected: All fields present
```

### 7.3 Dashboards & Alerts

- [ ] **GO**: Grafana dashboard shows p95 by action & SLA class
- [ ] **GO**: Alert on `timed_out=TRUE` (timeout rate >10%)
- [ ] **GO**: Alert on DLQ growth (>10 jobs)
- [ ] **GO**: Alert on lease expirations (worker crashes)
- [ ] **GO**: Alert on mutex reaper activity (stale locks)
- [ ] **GO**: Alert on `rbac_violation` events (security)

**Verification**:
```bash
# Check Grafana dashboards exist
curl -s http://grafana:3000/api/dashboards/db/phase-7-execution | jq '.dashboard.title'
# Expected: "Phase 7: Execution Metrics"
```

---

## 🧪 8. Testing

### 8.1 Unit Tests

- [ ] **GO**: Idempotency tests (duplicate detection, tenant isolation)
- [ ] **GO**: Mutex tests (concurrent operations, stale lock reaper)
- [ ] **GO**: RBAC tests (tenant isolation, action authorization)
- [ ] **GO**: Cancellation tests (idempotent cancel, mutex release)
- [ ] **GO**: Timeout tests (SLA enforcement, timeout recording)
- [ ] **GO**: Log masking tests (sink-level redaction, exception messages)
- [ ] **GO**: FSM tests (illegal transitions, terminal states)
- [ ] **GO**: Plan hash stability tests (reordered targets yield same hash)

**Coverage Target**: 90%+ for all safety features

### 8.2 Integration Tests

- [ ] **GO**: Immediate execution (simple query)
- [ ] **GO**: Immediate execution with approval
- [ ] **GO**: Background execution (deploy)
- [ ] **GO**: Cancellation mid-run (releases lock, halts steps)
- [ ] **GO**: Worker crash → job reappears after lease
- [ ] **GO**: Redis outage → background returns "queue unavailable", immediate path unaffected
- [ ] **GO**: Approval after plan change → invalidation error

### 8.3 High-Impact Scenarios

- [ ] **GO**: Browser refresh duplicates → same execution returned
- [ ] **GO**: Worker crashes mid-job → job requeued, no duplicate side-effects
- [ ] **GO**: Redis outage → immediate path works, background fails gracefully
- [ ] **GO**: Approval after plan change → requires re-approval
- [ ] **GO**: Cancellation during execution → mutex released, steps halted

---

## 🚀 9. Rollout Strategy

### 9.1 Dark Launch

- [ ] **GO**: Stage E behind feature flag (disabled by default)
- [ ] **GO**: Enable for internal tenant first (not production)
- [ ] **GO**: Record-only mode for 24h (write executions/events, short-circuit automation calls)
- [ ] **GO**: Compare plans vs expected (validate correctness)

### 9.2 Gradual Enablement

- [ ] **GO**: Level-0 only (read-only, auto-execute) for 48h
- [ ] **GO**: Level-1 (confirmation) after clean burn-in
- [ ] **GO**: Level-2/3 (plan review, step-by-step) after 1 week
- [ ] **GO**: Production tenants after 2 weeks

### 9.3 Rollback Plan

- [ ] **GO**: Feature flag can disable Stage E instantly
- [ ] **GO**: In-flight executions complete gracefully
- [ ] **GO**: Database schema supports rollback (no breaking changes)
- [ ] **GO**: Runbook documents rollback procedure

---

## 📝 10. Documentation

### 10.1 Runbooks

- [ ] **GO**: Runbook for common operations (restart worker, drain queue, inspect DLQ)
- [ ] **GO**: Runbook for incident response (execution stuck, mutex deadlock, Redis outage)
- [ ] **GO**: Runbook for rollback (disable feature flag, drain queue)
- [ ] **GO**: Runbook links embedded in approval dialogs (Level 2/3)

### 10.2 Monitoring

- [ ] **GO**: Metrics exported to Prometheus (execution_duration, queue_length, dlq_size, timeout_rate, cancellation_rate)
- [ ] **GO**: Dashboards created in Grafana (execution metrics, queue metrics, safety metrics)
- [ ] **GO**: Alerts configured in Alertmanager (timeouts, DLQ growth, RBAC violations)

---

## ✅ Final Verdict

### Pre-Flight Checklist

- [ ] **GO**: All 7 tables + 4 ENUMs + timeout_policies table created
- [ ] **GO**: Unique index `(tenant_id, idempotency_key)` present
- [ ] **GO**: Plan snapshot stored, constraints enforced
- [ ] **GO**: Immediate + background paths wired
- [ ] **GO**: All 7 safety features implemented (idempotency, mutex, RBAC, secrets, cancellation, timeout, log masking)
- [ ] **GO**: Queue + DLQ + lease mechanism working
- [ ] **GO**: Approval workflow (Level 0-3) enforced
- [ ] **GO**: Progress tracking (WS + SSE + poll) working
- [ ] **GO**: Structured logging with all required fields
- [ ] **GO**: Dashboards + alerts configured
- [ ] **GO**: Unit tests (90%+ coverage) passing
- [ ] **GO**: Integration tests (high-impact scenarios) passing
- [ ] **GO**: Dark launch plan ready
- [ ] **GO**: Rollback plan documented

### Release Decision

**If all items above are ✅ GO**: **APPROVED FOR PRODUCTION RELEASE** 🚀

**If any item is ❌ NO-GO**: **BLOCK RELEASE** until resolved.

---

## 🎯 Success Criteria (Post-Launch)

### Week 1

- [ ] No 3am pages (safety features prevent incidents)
- [ ] Idempotency violations: 0
- [ ] RBAC violations: 0
- [ ] Secret leaks: 0
- [ ] Timeout rate: <10%
- [ ] Cancellation rate: <20%
- [ ] DLQ size: <10 jobs
- [ ] Worker crash recovery: 100% (all jobs requeued)

### Week 2

- [ ] p95 execution duration within SLA (fast: <10s, medium: <30s, long: <10min)
- [ ] Queue wait time: <5s (p95)
- [ ] WebSocket connection success rate: >90%
- [ ] Approval workflow adoption: >50% of high-risk operations
- [ ] User satisfaction: >80% (survey)

### Month 1

- [ ] Zero production incidents caused by Stage E
- [ ] Execution success rate: >95%
- [ ] Background job completion rate: >98%
- [ ] DLQ jobs resolved: >90%
- [ ] Gradual enablement complete (all approval levels, all tenants)

---

## 📞 Contacts

**On-Call**: [Your on-call rotation]  
**Slack Channel**: #phase-7-execution  
**Runbook**: [Link to runbook]  
**Dashboards**: [Link to Grafana]  
**Alerts**: [Link to Alertmanager]

---

**Last Updated**: 2025-01-XX  
**Version**: 1.0  
**Owner**: OpsConductor Team