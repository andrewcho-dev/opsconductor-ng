# Phase 7: Database Schema - Production-Hardened DDL

## 📋 Overview

This document contains the complete database schema for Stage E (Execution) with all production-hardening features:

- ✅ **ENUMs** for type safety
- ✅ **timestamptz** for timezone awareness
- ✅ **Tenant-scoped uniqueness** for idempotency
- ✅ **Plan snapshots** for audit trail
- ✅ **Composite indexes** for query optimization
- ✅ **CHECK constraints** for invalid state prevention
- ✅ **Approval integrity** binding to plan hash

---

## 🗄️ Schema Components

### Tables (7 Total)

1. **executions** - Main execution tracking
2. **execution_steps** - Individual step tracking
3. **approvals** - Approval workflow
4. **execution_events** - Event log for timeline
5. **execution_queue** - Background job queue
6. **execution_dlq** - Dead letter queue
7. **execution_locks** - Mutex tracking

### ENUMs (4 Total)

1. **execution_status** - Execution lifecycle states
2. **execution_mode** - Immediate vs background
3. **sla_class** - Fast/medium/long
4. **approval_state** - Approval workflow states

---

## 📝 Migration Scripts

### Migration 1: ENUMs

**File**: `database/migrations/0XX_add_execution_enums.sql`

```sql
-- ============================================================================
-- Migration: Add Execution ENUMs
-- Description: Create ENUM types for execution system
-- Author: OpsConductor Team
-- Date: 2025-01-XX
-- ============================================================================

-- Execution statuses (lifecycle states)
-- FSM: Legal transitions enforced in application layer
--   pending → awaiting_approval | approved | running | cancelled
--   awaiting_approval → approved | rejected | cancelled
--   approved → running | cancelled
--   running → succeeded | failed | cancelled
--   succeeded, failed, cancelled → terminal (no transitions)
DO $$ BEGIN
  CREATE TYPE execution_status AS ENUM (
    'pending',           -- Created, not yet started
    'awaiting_approval', -- Waiting for user approval
    'approved',          -- Approved, ready to execute
    'running',           -- Currently executing
    'succeeded',         -- Completed successfully
    'failed',            -- Failed with error
    'cancelled',         -- Cancelled by user
    'rejected'           -- Approval rejected
  );
EXCEPTION WHEN duplicate_object THEN NULL; END $$;

-- Execution modes (immediate vs background)
DO $$ BEGIN
  CREATE TYPE execution_mode AS ENUM (
    'immediate',  -- Synchronous execution (<10s)
    'background'  -- Asynchronous execution (>30s)
  );
EXCEPTION WHEN duplicate_object THEN NULL; END $$;

-- SLA classes (performance expectations)
DO $$ BEGIN
  CREATE TYPE sla_class AS ENUM (
    'fast',    -- <10s operations (queries)
    'medium',  -- 10-30s operations (single server actions)
    'long'     -- >30s operations (multi-server deployments)
  );
EXCEPTION WHEN duplicate_object THEN NULL; END $$;

-- Approval states (workflow states)
DO $$ BEGIN
  CREATE TYPE approval_state AS ENUM (
    'pending',   -- Awaiting decision
    'approved',  -- Approved by authorized user
    'rejected',  -- Rejected by authorized user
    'expired'    -- Approval request expired
  );
EXCEPTION WHEN duplicate_object THEN NULL; END $$;

-- ============================================================================
-- Verification
-- ============================================================================

-- Verify ENUMs created
SELECT typname, typtype 
FROM pg_type 
WHERE typname IN (
  'execution_status', 
  'execution_mode', 
  'sla_class', 
  'approval_state'
);

-- Expected output: 4 rows with typtype = 'e' (enum)
```

---

### Migration 2: Executions Table

**File**: `database/migrations/0XX_add_executions_table.sql`

```sql
-- ============================================================================
-- Migration: Add Executions Table
-- Description: Main execution tracking table with idempotency and audit trail
-- Author: OpsConductor Team
-- Date: 2025-01-XX
-- ============================================================================

CREATE TABLE executions (
  -- ============================================================================
  -- Primary Key
  -- ============================================================================
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  
  -- ============================================================================
  -- Identity (tenant-scoped)
  -- ============================================================================
  tenant_id UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
  actor_id UUID NOT NULL REFERENCES users(id) ON DELETE SET NULL,
  request_id UUID NOT NULL REFERENCES requests(id) ON DELETE CASCADE,
  
  -- ============================================================================
  -- Idempotency (tenant-scoped uniqueness)
  -- ============================================================================
  idempotency_key VARCHAR(255) NOT NULL,
  plan_hash VARCHAR(64) NOT NULL,
  
  -- ============================================================================
  -- Audit Trail (frozen plan snapshot)
  -- ============================================================================
  plan_snapshot JSONB NOT NULL,
  plan_size_bytes INT NOT NULL,
  step_count INT NOT NULL,
  target_count INT NOT NULL,
  
  -- ============================================================================
  -- Execution Details
  -- ============================================================================
  execution_mode execution_mode NOT NULL,
  approval_level INT NOT NULL CHECK (approval_level BETWEEN 0 AND 3),
  sla_class sla_class NOT NULL,
  status execution_status NOT NULL,
  
  -- ============================================================================
  -- Timing (server-side computed, timezone-aware)
  -- ============================================================================
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  started_at TIMESTAMPTZ,
  ended_at TIMESTAMPTZ,
  duration_ms INT,
  queue_wait_ms INT,  -- Time spent in queue before execution
  
  -- ============================================================================
  -- Cancellation
  -- ============================================================================
  cancelled_by UUID REFERENCES users(id) ON DELETE SET NULL,
  cancelled_at TIMESTAMPTZ,
  cancellation_reason TEXT,
  
  -- ============================================================================
  -- Timeout Enforcement
  -- ============================================================================
  timeout_ms INT,  -- Per-execution timeout based on SLA class
  timed_out BOOLEAN DEFAULT FALSE,
  
  -- ============================================================================
  -- Results
  -- ============================================================================
  result_summary JSONB,
  error_class VARCHAR(100),
  error_message TEXT,
  retries_total INT DEFAULT 0,
  
  -- ============================================================================
  -- Observability (enhanced for incident triage)
  -- ============================================================================
  ws_events_emitted INT DEFAULT 0,
  worker_id VARCHAR(100),           -- Worker that executed this job
  lease_renewals INT DEFAULT 0,     -- Number of lease renewals (long jobs)
  cancel_checks_performed INT DEFAULT 0,  -- Cancellation token checks
  
  -- ============================================================================
  -- State Machine Audit (FSM transition tracking)
  -- ============================================================================
  last_transition_at TIMESTAMPTZ,   -- When last state change occurred
  last_transition_by UUID REFERENCES users(id) ON DELETE SET NULL,  -- Who triggered it
  last_transition_from execution_status,  -- Previous state
  
  -- ============================================================================
  -- Timeout Policy (forensics)
  -- ============================================================================
  timeout_policy_id VARCHAR(50),    -- e.g., "fast_query", "medium_modify", "long_deploy"
  
  -- ============================================================================
  -- Metadata
  -- ============================================================================
  metadata JSONB,
  
  -- ============================================================================
  -- Constraints
  -- ============================================================================
  CONSTRAINT valid_timing CHECK (
    (started_at IS NULL OR started_at >= created_at) AND
    (ended_at IS NULL OR ended_at >= started_at)
  ),
  CONSTRAINT valid_duration CHECK (
    duration_ms IS NULL OR duration_ms >= 0
  ),
  CONSTRAINT valid_queue_wait CHECK (
    queue_wait_ms IS NULL OR queue_wait_ms >= 0
  ),
  CONSTRAINT valid_timeout CHECK (
    timeout_ms IS NULL OR timeout_ms > 0
  ),
  -- Cancellation fields must be set together (idempotent cancellation)
  CONSTRAINT valid_cancellation CHECK (
    (cancelled_by IS NULL AND cancelled_at IS NULL) OR
    (cancelled_by IS NOT NULL AND cancelled_at IS NOT NULL)
  ),
  -- Output summary capped at 10KB (prevent bloat, even without S3)
  CONSTRAINT valid_result_size CHECK (
    result_summary IS NULL OR 
    pg_column_size(result_summary) <= 10240
  )
);

-- ============================================================================
-- Indexes (created separately for Postgres compatibility)
-- ============================================================================

-- Tenant-scoped idempotency (prevents cross-tenant collisions)
CREATE UNIQUE INDEX ux_exec_tenant_idem 
  ON executions (tenant_id, idempotency_key);

-- Common query paths (tenant + status + created_at)
CREATE INDEX ix_exec_tenant_status_created 
  ON executions (tenant_id, status, created_at DESC);

-- Request lookup
CREATE INDEX ix_exec_request 
  ON executions (request_id);

-- Actor history
CREATE INDEX ix_exec_actor 
  ON executions (actor_id, created_at DESC);

-- Cancellation queries
CREATE INDEX ix_exec_cancelled 
  ON executions (cancelled_by, cancelled_at DESC) 
  WHERE cancelled_by IS NOT NULL;

-- Timeout monitoring
CREATE INDEX ix_exec_timeout 
  ON executions (status, created_at) 
  WHERE timed_out = TRUE;

-- SLA class performance tracking
CREATE INDEX ix_exec_sla_duration 
  ON executions (sla_class, duration_ms) 
  WHERE duration_ms IS NOT NULL;

-- ============================================================================
-- Comments
-- ============================================================================

COMMENT ON TABLE executions IS 'Main execution tracking table with idempotency and audit trail';
COMMENT ON COLUMN executions.idempotency_key IS 'Tenant-scoped idempotency key (sha256 of plan + tenant + actor)';
COMMENT ON COLUMN executions.plan_hash IS 'Hash of execution plan for approval integrity';
COMMENT ON COLUMN executions.plan_snapshot IS 'Frozen plan snapshot for audit trail';
COMMENT ON COLUMN executions.duration_ms IS 'Server-computed execution duration in milliseconds';
COMMENT ON COLUMN executions.queue_wait_ms IS 'Time spent in queue before worker picked up job';

-- ============================================================================
-- Verification
-- ============================================================================

-- Verify table created
SELECT table_name, table_type 
FROM information_schema.tables 
WHERE table_name = 'executions';

-- Verify indexes created
SELECT indexname, indexdef 
FROM pg_indexes 
WHERE tablename = 'executions';

-- Expected: 7 indexes (1 primary key + 6 custom)
```

---

### Migration 3: Execution Steps Table

**File**: `database/migrations/0XX_add_execution_steps_table.sql`

```sql
-- ============================================================================
-- Migration: Add Execution Steps Table
-- Description: Individual step tracking with retry and timeout support
-- Author: OpsConductor Team
-- Date: 2025-01-XX
-- ============================================================================

CREATE TABLE execution_steps (
  -- ============================================================================
  -- Primary Key
  -- ============================================================================
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  
  -- ============================================================================
  -- Parent Execution
  -- ============================================================================
  execution_id UUID NOT NULL REFERENCES executions(id) ON DELETE CASCADE,
  step_number INT NOT NULL,
  
  -- ============================================================================
  -- Step Details
  -- ============================================================================
  action VARCHAR(100) NOT NULL,
  target_type VARCHAR(50),
  target_ref VARCHAR(255),  -- Canonically sorted for determinism
  
  -- ============================================================================
  -- Status
  -- ============================================================================
  status execution_status NOT NULL,
  attempt INT NOT NULL DEFAULT 1,
  max_retries INT NOT NULL DEFAULT 3,
  
  -- ============================================================================
  -- Timing (server-side computed, timezone-aware)
  -- ============================================================================
  started_at TIMESTAMPTZ,
  ended_at TIMESTAMPTZ,
  duration_ms INT,
  
  -- ============================================================================
  -- Timeout Enforcement
  -- ============================================================================
  timeout_ms INT,
  timed_out BOOLEAN DEFAULT FALSE,
  
  -- ============================================================================
  -- Results
  -- ============================================================================
  output_ref VARCHAR(500),  -- S3/storage reference for large outputs
  output_summary JSONB,     -- Truncated output (max 10KB)
  output_size_bytes INT,    -- Full output size
  error_class VARCHAR(100),
  error_message TEXT,
  
  -- ============================================================================
  -- Metadata
  -- ============================================================================
  metadata JSONB,
  
  -- ============================================================================
  -- Constraints
  -- ============================================================================
  UNIQUE (execution_id, step_number),
  CONSTRAINT valid_step_timing CHECK (
    (started_at IS NULL OR ended_at IS NULL OR ended_at >= started_at)
  ),
  CONSTRAINT valid_attempt CHECK (
    attempt > 0 AND attempt <= max_retries + 1
  ),
  CONSTRAINT valid_step_duration CHECK (
    duration_ms IS NULL OR duration_ms >= 0
  ),
  CONSTRAINT valid_step_timeout CHECK (
    timeout_ms IS NULL OR timeout_ms > 0
  )
);

-- ============================================================================
-- Indexes
-- ============================================================================

-- Execution lookup (most common query)
CREATE INDEX ix_steps_exec 
  ON execution_steps (execution_id);

-- Execution + status (for progress tracking)
CREATE INDEX ix_steps_exec_status 
  ON execution_steps (execution_id, status);

-- Action analytics
CREATE INDEX ix_steps_action 
  ON execution_steps (action, status);

-- Target analytics
CREATE INDEX ix_steps_target 
  ON execution_steps (target_ref, action) 
  WHERE target_ref IS NOT NULL;

-- Timeout monitoring
CREATE INDEX ix_steps_timeout 
  ON execution_steps (execution_id, timed_out) 
  WHERE timed_out = TRUE;

-- ============================================================================
-- Comments
-- ============================================================================

COMMENT ON TABLE execution_steps IS 'Individual step tracking with retry and timeout support';
COMMENT ON COLUMN execution_steps.target_ref IS 'Canonically sorted target reference for determinism';
COMMENT ON COLUMN execution_steps.output_ref IS 'Reference to full output in artifact store (S3/minio)';
COMMENT ON COLUMN execution_steps.output_summary IS 'Truncated output (max 10KB) for quick display';

-- ============================================================================
-- Verification
-- ============================================================================

SELECT table_name FROM information_schema.tables WHERE table_name = 'execution_steps';
SELECT indexname FROM pg_indexes WHERE tablename = 'execution_steps';
```

---

### Migration 4: Approvals Table

**File**: `database/migrations/0XX_add_approvals_table.sql`

```sql
-- ============================================================================
-- Migration: Add Approvals Table
-- Description: Approval workflow with plan integrity binding
-- Author: OpsConductor Team
-- Date: 2025-01-XX
-- ============================================================================

CREATE TABLE approvals (
  -- ============================================================================
  -- Primary Key
  -- ============================================================================
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  
  -- ============================================================================
  -- Parent Execution
  -- ============================================================================
  execution_id UUID NOT NULL REFERENCES executions(id) ON DELETE CASCADE,
  
  -- ============================================================================
  -- Approval Details
  -- ============================================================================
  approval_level INT NOT NULL CHECK (approval_level BETWEEN 0 AND 3),
  required_role VARCHAR(50),
  
  -- ============================================================================
  -- Plan Integrity (bind approval to specific plan version)
  -- ============================================================================
  plan_hash VARCHAR(64) NOT NULL,
  plan_snapshot_hash VARCHAR(64) NOT NULL,  -- Hash of plan_snapshot for integrity
  
  -- ============================================================================
  -- Approver Identity & Context (audit trail)
  -- ============================================================================
  approver_id UUID REFERENCES users(id) ON DELETE SET NULL,
  approver_principal VARCHAR(255),  -- Email or SSO principal
  auth_method VARCHAR(50),          -- 'password', 'sso', 'api_key', etc.
  source_ip INET,                   -- IP address of approver
  
  -- ============================================================================
  -- Decision
  -- ============================================================================
  state approval_state NOT NULL,
  decided_at TIMESTAMPTZ,
  reason TEXT,
  
  -- ============================================================================
  -- Runbook (required for Level 2/3)
  -- ============================================================================
  runbook_url VARCHAR(500),
  
  -- ============================================================================
  -- Timing
  -- ============================================================================
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  expires_at TIMESTAMPTZ,
  
  -- ============================================================================
  -- Auto-Approval Tracking
  -- ============================================================================
  auto_approved BOOLEAN DEFAULT FALSE,
  auto_approval_policy VARCHAR(100),  -- Policy that triggered auto-approval
  
  -- ============================================================================
  -- Metadata
  -- ============================================================================
  metadata JSONB,
  
  -- ============================================================================
  -- Constraints
  -- ============================================================================
  CONSTRAINT valid_approval_timing CHECK (
    decided_at IS NULL OR decided_at >= created_at
  ),
  CONSTRAINT runbook_required_for_high_level CHECK (
    approval_level < 2 OR runbook_url IS NOT NULL
  ),
  CONSTRAINT approver_required_for_decision CHECK (
    state = 'pending' OR approver_id IS NOT NULL OR auto_approved = TRUE
  )
);

-- ============================================================================
-- Indexes
-- ============================================================================

-- Execution lookup
CREATE INDEX ix_appr_exec 
  ON approvals (execution_id);

-- Pending approvals (for approval queue)
CREATE INDEX ix_appr_state 
  ON approvals (state, created_at DESC);

-- Approver history
CREATE INDEX ix_appr_approver 
  ON approvals (approver_id, decided_at DESC) 
  WHERE approver_id IS NOT NULL;

-- Plan integrity queries
CREATE INDEX ix_appr_plan_hash 
  ON approvals (plan_hash);

-- Expired approvals (for cleanup)
CREATE INDEX ix_appr_expired 
  ON approvals (expires_at) 
  WHERE state = 'pending' AND expires_at IS NOT NULL;

-- ============================================================================
-- Comments
-- ============================================================================

COMMENT ON TABLE approvals IS 'Approval workflow with plan integrity binding';
COMMENT ON COLUMN approvals.plan_hash IS 'Hash of execution plan - approval invalidated if plan changes';
COMMENT ON COLUMN approvals.plan_snapshot_hash IS 'Hash of frozen plan snapshot for integrity verification';
COMMENT ON COLUMN approvals.approver_principal IS 'Email or SSO principal for audit trail';
COMMENT ON COLUMN approvals.auth_method IS 'Authentication method used by approver';
COMMENT ON COLUMN approvals.source_ip IS 'IP address of approver for security audit';

-- ============================================================================
-- Verification
-- ============================================================================

SELECT table_name FROM information_schema.tables WHERE table_name = 'approvals';
SELECT indexname FROM pg_indexes WHERE tablename = 'approvals';
```

---

### Migration 5: Execution Events Table

**File**: `database/migrations/0XX_add_execution_events_table.sql`

```sql
-- ============================================================================
-- Migration: Add Execution Events Table
-- Description: Event log for timeline reconstruction and debugging
-- Author: OpsConductor Team
-- Date: 2025-01-XX
-- ============================================================================

CREATE TABLE execution_events (
  -- ============================================================================
  -- Primary Key
  -- ============================================================================
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  
  -- ============================================================================
  -- Parent References
  -- ============================================================================
  execution_id UUID NOT NULL REFERENCES executions(id) ON DELETE CASCADE,
  step_id UUID REFERENCES execution_steps(id) ON DELETE CASCADE,
  
  -- ============================================================================
  -- Event Details
  -- ============================================================================
  timestamp TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  event_kind VARCHAR(50) NOT NULL,
  
  -- ============================================================================
  -- Payload (masked for secrets)
  -- ============================================================================
  payload JSONB,
  
  -- ============================================================================
  -- Metadata
  -- ============================================================================
  metadata JSONB
);

-- ============================================================================
-- Indexes
-- ============================================================================

-- Execution timeline (most common query)
CREATE INDEX ix_events_exec_ts 
  ON execution_events (execution_id, timestamp DESC);

-- Event kind analytics
CREATE INDEX ix_events_kind 
  ON execution_events (event_kind, timestamp DESC);

-- Step events
CREATE INDEX ix_events_step 
  ON execution_events (step_id, timestamp DESC) 
  WHERE step_id IS NOT NULL;

-- ============================================================================
-- Comments
-- ============================================================================

COMMENT ON TABLE execution_events IS 'Event log for timeline reconstruction and debugging';
COMMENT ON COLUMN execution_events.event_kind IS 'Event type: started, progress, completed, failed, approval_requested, approved, rejected, cancelled';
COMMENT ON COLUMN execution_events.payload IS 'Event payload (secrets automatically masked)';

-- ============================================================================
-- Event Kinds (for reference)
-- ============================================================================

-- execution_started      - Execution began
-- execution_approved     - Execution approved
-- execution_running      - Execution started running
-- execution_completed    - Execution finished successfully
-- execution_failed       - Execution failed with error
-- execution_cancelled    - Execution cancelled by user
-- execution_timed_out    - Execution exceeded timeout
-- step_started           - Step N started
-- step_progress          - Step N progress update
-- step_completed         - Step N completed
-- step_failed            - Step N failed
-- step_retrying          - Step N retrying after failure
-- approval_requested     - Approval requested
-- approval_approved      - Approval granted
-- approval_rejected      - Approval rejected
-- approval_expired       - Approval request expired

-- ============================================================================
-- Verification
-- ============================================================================

SELECT table_name FROM information_schema.tables WHERE table_name = 'execution_events';
SELECT indexname FROM pg_indexes WHERE tablename = 'execution_events';
```

---

### Migration 6: Queue Tables

**File**: `database/migrations/0XX_add_queue_tables.sql`

```sql
-- ============================================================================
-- Migration: Add Queue Tables
-- Description: Background job queue with priority, lease, and DLQ
-- Author: OpsConductor Team
-- Date: 2025-01-XX
-- ============================================================================

-- ============================================================================
-- Execution Queue (with priority and visibility timeout)
-- ============================================================================

CREATE TABLE execution_queue (
  -- ============================================================================
  -- Primary Key
  -- ============================================================================
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  
  -- ============================================================================
  -- Job Identity
  -- ============================================================================
  execution_id UUID NOT NULL REFERENCES executions(id) ON DELETE CASCADE,
  
  -- ============================================================================
  -- Queue Semantics
  -- ============================================================================
  priority INT NOT NULL DEFAULT 50,  -- 0=urgent, 50=normal, 100=bulk
  status VARCHAR(20) NOT NULL,       -- 'queued', 'leased', 'completed', 'failed'
  
  -- ============================================================================
  -- Visibility Timeout (lease mechanism)
  -- ============================================================================
  leased_by VARCHAR(100),            -- Worker ID that leased this job
  leased_at TIMESTAMPTZ,
  lease_expires_at TIMESTAMPTZ,
  lease_count INT DEFAULT 0,         -- Number of times leased
  
  -- ============================================================================
  -- Timing
  -- ============================================================================
  queued_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  started_at TIMESTAMPTZ,
  completed_at TIMESTAMPTZ,
  
  -- ============================================================================
  -- Retry Tracking
  -- ============================================================================
  attempt INT DEFAULT 0,
  max_attempts INT DEFAULT 3,
  last_error TEXT,
  
  -- ============================================================================
  -- Metadata
  -- ============================================================================
  metadata JSONB,
  
  -- ============================================================================
  -- Constraints
  -- ============================================================================
  CONSTRAINT valid_priority CHECK (priority BETWEEN 0 AND 100),
  CONSTRAINT valid_lease CHECK (
    (leased_by IS NULL AND leased_at IS NULL) OR
    (leased_by IS NOT NULL AND leased_at IS NOT NULL)
  ),
  CONSTRAINT valid_status CHECK (
    status IN ('queued', 'leased', 'completed', 'failed')
  )
);

-- ============================================================================
-- Indexes
-- ============================================================================

-- Dequeue query (get next job by priority)
CREATE INDEX ix_queue_status_priority 
  ON execution_queue (status, priority, queued_at) 
  WHERE status = 'queued';

-- Lease expiration (for reaping expired leases)
CREATE INDEX ix_queue_lease_expires 
  ON execution_queue (lease_expires_at) 
  WHERE status = 'leased' AND lease_expires_at IS NOT NULL;

-- Execution lookup
CREATE INDEX ix_queue_execution 
  ON execution_queue (execution_id);

-- Worker monitoring
CREATE INDEX ix_queue_worker 
  ON execution_queue (leased_by, leased_at DESC) 
  WHERE leased_by IS NOT NULL;

-- ============================================================================
-- Comments
-- ============================================================================

COMMENT ON TABLE execution_queue IS 'Background job queue with priority and visibility timeout';
COMMENT ON COLUMN execution_queue.priority IS 'Job priority: 0=urgent, 50=normal, 100=bulk';
COMMENT ON COLUMN execution_queue.leased_by IS 'Worker ID that leased this job';
COMMENT ON COLUMN execution_queue.lease_expires_at IS 'Lease expiration time (job becomes visible again after this)';
COMMENT ON COLUMN execution_queue.lease_count IS 'Number of times this job has been leased (for monitoring)';

-- ============================================================================
-- Dead Letter Queue (failed jobs after max retries)
-- ============================================================================

CREATE TABLE execution_dlq (
  -- ============================================================================
  -- Primary Key
  -- ============================================================================
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  
  -- ============================================================================
  -- Original Job
  -- ============================================================================
  execution_id UUID NOT NULL REFERENCES executions(id) ON DELETE CASCADE,
  original_queue_id UUID NOT NULL,
  
  -- ============================================================================
  -- Failure Details
  -- ============================================================================
  failed_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  attempt_count INT NOT NULL,
  last_error TEXT NOT NULL,
  
  -- ============================================================================
  -- Full Context (for debugging)
  -- ============================================================================
  plan_snapshot JSONB NOT NULL,
  execution_context JSONB NOT NULL,
  
  -- ============================================================================
  -- Metadata
  -- ============================================================================
  metadata JSONB
);

-- ============================================================================
-- Indexes
-- ============================================================================

-- Execution lookup
CREATE INDEX ix_dlq_execution 
  ON execution_dlq (execution_id);

-- Failed jobs timeline
CREATE INDEX ix_dlq_failed_at 
  ON execution_dlq (failed_at DESC);

-- ============================================================================
-- Comments
-- ============================================================================

COMMENT ON TABLE execution_dlq IS 'Dead letter queue for jobs that failed after max retries';
COMMENT ON COLUMN execution_dlq.plan_snapshot IS 'Frozen plan snapshot for debugging';
COMMENT ON COLUMN execution_dlq.execution_context IS 'Full execution context for manual retry';

-- ============================================================================
-- Verification
-- ============================================================================

SELECT table_name FROM information_schema.tables WHERE table_name IN ('execution_queue', 'execution_dlq');
SELECT indexname FROM pg_indexes WHERE tablename IN ('execution_queue', 'execution_dlq');
```

---

### Migration 7: Mutex Table

**File**: `database/migrations/0XX_add_mutex_table.sql`

```sql
-- ============================================================================
-- Migration: Add Mutex Table
-- Description: Track active locks for observability and stale lock detection
-- Author: OpsConductor Team
-- Date: 2025-01-XX
-- ============================================================================

CREATE TABLE execution_locks (
  -- ============================================================================
  -- Primary Key
  -- ============================================================================
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  
  -- ============================================================================
  -- Lock Identity
  -- ============================================================================
  lock_key VARCHAR(500) NOT NULL UNIQUE,  -- lock:v1:{tenant}:{target}:{action}
  
  -- ============================================================================
  -- Owner
  -- ============================================================================
  execution_id UUID NOT NULL REFERENCES executions(id) ON DELETE CASCADE,
  owner_tag VARCHAR(100) NOT NULL,  -- exec_id for verification
  
  -- ============================================================================
  -- Timing
  -- ============================================================================
  acquired_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  expires_at TIMESTAMPTZ NOT NULL,
  
  -- ============================================================================
  -- Metadata
  -- ============================================================================
  metadata JSONB
);

-- ============================================================================
-- Indexes
-- ============================================================================

-- Active locks (for monitoring)
CREATE INDEX ix_locks_expires 
  ON execution_locks (expires_at) 
  WHERE expires_at > NOW();

-- Execution locks (for debugging)
CREATE INDEX ix_locks_execution 
  ON execution_locks (execution_id);

-- Stale lock detection (for reaper)
CREATE INDEX ix_locks_stale 
  ON execution_locks (acquired_at) 
  WHERE expires_at < NOW();

-- ============================================================================
-- Comments
-- ============================================================================

COMMENT ON TABLE execution_locks IS 'Track active locks for observability and stale lock detection';
COMMENT ON COLUMN execution_locks.lock_key IS 'Lock key format: lock:v1:{tenant}:{target}:{action}';
COMMENT ON COLUMN execution_locks.owner_tag IS 'Execution ID that owns this lock (for verification)';

-- ============================================================================
-- Verification
-- ============================================================================

SELECT table_name FROM information_schema.tables WHERE table_name = 'execution_locks';
SELECT indexname FROM pg_indexes WHERE tablename = 'execution_locks';
```

---

## ⏱️ Timeout Policy Configuration

**File**: `database/migrations/0XX_add_timeout_policies.sql`

Timeout policies derive `timeout_ms` per **SLA class × action class** (not just SLA alone).

```sql
-- ============================================================================
-- Migration: Timeout Policy Table
-- Description: Store timeout policies per SLA × action class
-- Author: OpsConductor Team
-- Date: 2025-01-XX
-- ============================================================================

CREATE TABLE timeout_policies (
  -- ============================================================================
  -- Primary Key
  -- ============================================================================
  id VARCHAR(50) PRIMARY KEY,  -- e.g., "fast_query", "medium_modify", "long_deploy"
  
  -- ============================================================================
  -- Policy Definition
  -- ============================================================================
  sla_class sla_class NOT NULL,
  action_class VARCHAR(20) NOT NULL,  -- 'read', 'modify', 'deploy'
  
  -- ============================================================================
  -- Timeouts (milliseconds)
  -- ============================================================================
  execution_timeout_ms INT NOT NULL,
  step_timeout_ms INT NOT NULL,
  
  -- ============================================================================
  -- Lease Configuration (for background queue)
  -- ============================================================================
  lease_timeout_ms INT NOT NULL,  -- max(step_timeout + buffer, 2× p95_step_duration)
  max_lease_renewals INT NOT NULL DEFAULT 3,
  
  -- ============================================================================
  -- Metadata
  -- ============================================================================
  description TEXT,
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  
  -- ============================================================================
  -- Constraints
  -- ============================================================================
  CONSTRAINT valid_action_class CHECK (action_class IN ('read', 'modify', 'deploy')),
  CONSTRAINT valid_timeouts CHECK (
    execution_timeout_ms > 0 AND
    step_timeout_ms > 0 AND
    lease_timeout_ms >= step_timeout_ms
  ),
  UNIQUE (sla_class, action_class)
);

-- ============================================================================
-- Seed Data (production-tested values)
-- ============================================================================

INSERT INTO timeout_policies (id, sla_class, action_class, execution_timeout_ms, step_timeout_ms, lease_timeout_ms, description) VALUES
  -- Fast operations (queries, status checks)
  ('fast_read', 'fast', 'read', 10000, 5000, 15000, 'Fast read operations (queries, status checks)'),
  
  -- Medium operations (single server actions)
  ('medium_read', 'medium', 'read', 30000, 15000, 45000, 'Medium read operations (multi-server queries)'),
  ('medium_modify', 'medium', 'modify', 30000, 20000, 60000, 'Medium modify operations (restart service, check disk)'),
  
  -- Long operations (multi-server deployments)
  ('long_read', 'long', 'read', 600000, 60000, 180000, 'Long read operations (compliance scans)'),
  ('long_modify', 'long', 'modify', 600000, 120000, 360000, 'Long modify operations (rolling restarts)'),
  ('long_deploy', 'long', 'deploy', 600000, 180000, 540000, 'Long deploy operations (multi-server deployments)');

-- ============================================================================
-- Indexes
-- ============================================================================

CREATE INDEX ix_timeout_policies_sla_action 
  ON timeout_policies (sla_class, action_class);

-- ============================================================================
-- Comments
-- ============================================================================

COMMENT ON TABLE timeout_policies IS 'Timeout configuration per SLA class × action class';
COMMENT ON COLUMN timeout_policies.lease_timeout_ms IS 'Worker lease duration = max(step_timeout + buffer, 2× p95_step_duration)';
COMMENT ON COLUMN timeout_policies.max_lease_renewals IS 'Maximum lease renewals before job pushed to DLQ';

-- ============================================================================
-- Verification
-- ============================================================================

SELECT id, sla_class, action_class, execution_timeout_ms, step_timeout_ms, lease_timeout_ms
FROM timeout_policies
ORDER BY sla_class, action_class;

-- Expected: 6 rows
```

---

## 🔄 FSM: State Machine Transitions

**Legal state transitions** enforced in application layer (not DB triggers for performance):

```python
# File: pipeline/stages/stage_e/fsm.py

from enum import Enum
from typing import Dict, Set

class ExecutionStatus(str, Enum):
    PENDING = "pending"
    AWAITING_APPROVAL = "awaiting_approval"
    APPROVED = "approved"
    RUNNING = "running"
    SUCCEEDED = "succeeded"
    FAILED = "failed"
    CANCELLED = "cancelled"
    REJECTED = "rejected"

# Legal state transitions (FSM)
LEGAL_TRANSITIONS: Dict[ExecutionStatus, Set[ExecutionStatus]] = {
    ExecutionStatus.PENDING: {
        ExecutionStatus.AWAITING_APPROVAL,
        ExecutionStatus.APPROVED,
        ExecutionStatus.RUNNING,
        ExecutionStatus.CANCELLED,
    },
    ExecutionStatus.AWAITING_APPROVAL: {
        ExecutionStatus.APPROVED,
        ExecutionStatus.REJECTED,
        ExecutionStatus.CANCELLED,
    },
    ExecutionStatus.APPROVED: {
        ExecutionStatus.RUNNING,
        ExecutionStatus.CANCELLED,
    },
    ExecutionStatus.RUNNING: {
        ExecutionStatus.SUCCEEDED,
        ExecutionStatus.FAILED,
        ExecutionStatus.CANCELLED,
    },
    # Terminal states (no transitions)
    ExecutionStatus.SUCCEEDED: set(),
    ExecutionStatus.FAILED: set(),
    ExecutionStatus.CANCELLED: set(),
    ExecutionStatus.REJECTED: set(),
}

class FSMError(Exception):
    """Raised when illegal state transition attempted."""
    pass

async def transition_status(
    execution_id: str,
    from_status: ExecutionStatus,
    to_status: ExecutionStatus,
    actor_id: str,
    db: Database
) -> None:
    """
    Transition execution status with FSM validation.
    
    Raises:
        FSMError: If transition is illegal
    """
    # Validate transition
    if to_status not in LEGAL_TRANSITIONS.get(from_status, set()):
        raise FSMError(
            f"Illegal state transition: {from_status} → {to_status}. "
            f"Legal transitions from {from_status}: {LEGAL_TRANSITIONS[from_status]}"
        )
    
    # Update with audit trail
    await db.executions.update(
        execution_id=execution_id,
        status=to_status,
        last_transition_at=datetime.utcnow(),
        last_transition_by=actor_id,
        last_transition_from=from_status,
    )
    
    # Log transition for audit
    await db.execution_events.create(
        execution_id=execution_id,
        event_type="status_transition",
        event_data={
            "from": from_status,
            "to": to_status,
            "actor_id": actor_id,
        }
    )
```

**Test coverage** for illegal transitions:

```python
# File: tests/test_fsm.py

import pytest
from pipeline.stages.stage_e.fsm import transition_status, FSMError, ExecutionStatus

@pytest.mark.asyncio
async def test_illegal_transition_pending_to_succeeded():
    """Cannot jump from pending → succeeded (must go through running)."""
    with pytest.raises(FSMError, match="Illegal state transition"):
        await transition_status(
            execution_id="exec-123",
            from_status=ExecutionStatus.PENDING,
            to_status=ExecutionStatus.SUCCEEDED,
            actor_id="user-456",
            db=mock_db
        )

@pytest.mark.asyncio
async def test_terminal_state_no_transitions():
    """Terminal states (succeeded, failed, cancelled) cannot transition."""
    with pytest.raises(FSMError, match="Illegal state transition"):
        await transition_status(
            execution_id="exec-123",
            from_status=ExecutionStatus.SUCCEEDED,
            to_status=ExecutionStatus.RUNNING,
            actor_id="user-456",
            db=mock_db
        )

@pytest.mark.asyncio
async def test_legal_transition_with_audit():
    """Legal transitions persist audit trail."""
    await transition_status(
        execution_id="exec-123",
        from_status=ExecutionStatus.APPROVED,
        to_status=ExecutionStatus.RUNNING,
        actor_id="user-456",
        db=mock_db
    )
    
    # Verify audit trail
    execution = await mock_db.executions.get("exec-123")
    assert execution.status == ExecutionStatus.RUNNING
    assert execution.last_transition_from == ExecutionStatus.APPROVED
    assert execution.last_transition_by == "user-456"
    assert execution.last_transition_at is not None
```

---

## 🔍 Query Examples

### Get Execution Status

```sql
SELECT 
  e.id,
  e.status,
  e.execution_mode,
  e.sla_class,
  e.created_at,
  e.started_at,
  e.ended_at,
  e.duration_ms,
  e.step_count,
  COUNT(es.id) FILTER (WHERE es.status = 'succeeded') as steps_succeeded,
  COUNT(es.id) FILTER (WHERE es.status = 'failed') as steps_failed,
  COUNT(es.id) FILTER (WHERE es.status = 'running') as steps_running
FROM executions e
LEFT JOIN execution_steps es ON es.execution_id = e.id
WHERE e.id = 'exec-123'
GROUP BY e.id;
```

---

### Get Execution Timeline

```sql
SELECT 
  ee.timestamp,
  ee.event_kind,
  ee.payload,
  es.step_number,
  es.action,
  es.target_ref
FROM execution_events ee
LEFT JOIN execution_steps es ON es.id = ee.step_id
WHERE ee.execution_id = 'exec-123'
ORDER BY ee.timestamp ASC;
```

---

### Get Pending Approvals

```sql
SELECT 
  a.id,
  a.approval_level,
  a.required_role,
  a.created_at,
  a.expires_at,
  e.plan_snapshot,
  e.actor_id,
  u.email as actor_email
FROM approvals a
JOIN executions e ON e.id = a.execution_id
JOIN users u ON u.id = e.actor_id
WHERE a.state = 'pending'
  AND a.tenant_id = 'tenant-123'
  AND (a.expires_at IS NULL OR a.expires_at > NOW())
ORDER BY a.created_at ASC;
```

---

### Get Queue Depth

```sql
SELECT 
  priority,
  COUNT(*) as job_count,
  MIN(queued_at) as oldest_job
FROM execution_queue
WHERE status = 'queued'
GROUP BY priority
ORDER BY priority ASC;
```

---

### Get Active Locks

```sql
SELECT 
  el.lock_key,
  el.owner_tag,
  el.acquired_at,
  el.expires_at,
  e.status as execution_status,
  e.actor_id
FROM execution_locks el
JOIN executions e ON e.id = el.execution_id
WHERE el.expires_at > NOW()
ORDER BY el.acquired_at ASC;
```

---

### Get DLQ Jobs

```sql
SELECT 
  dlq.id,
  dlq.execution_id,
  dlq.failed_at,
  dlq.attempt_count,
  dlq.last_error,
  e.plan_snapshot,
  e.actor_id
FROM execution_dlq dlq
JOIN executions e ON e.id = dlq.execution_id
WHERE dlq.failed_at > NOW() - INTERVAL '7 days'
ORDER BY dlq.failed_at DESC;
```

---

## 📊 Performance Considerations

### Index Strategy

1. **Composite indexes** for common query paths (tenant + status + created_at)
2. **Partial indexes** for filtered queries (WHERE status = 'queued')
3. **Covering indexes** to avoid table lookups (include all SELECT columns)

### Partitioning Strategy (Future)

If `executions` table grows >10M rows:

```sql
-- Partition by created_at (monthly)
CREATE TABLE executions_2025_01 PARTITION OF executions
  FOR VALUES FROM ('2025-01-01') TO ('2025-02-01');

CREATE TABLE executions_2025_02 PARTITION OF executions
  FOR VALUES FROM ('2025-02-01') TO ('2025-03-01');
```

### Archival Strategy

Archive old executions (>90 days) to separate table:

```sql
-- Archive table (same schema, no indexes)
CREATE TABLE executions_archive (LIKE executions INCLUDING ALL);

-- Move old executions
INSERT INTO executions_archive
SELECT * FROM executions
WHERE created_at < NOW() - INTERVAL '90 days'
  AND status IN ('succeeded', 'failed', 'cancelled');

-- Delete from main table
DELETE FROM executions
WHERE created_at < NOW() - INTERVAL '90 days'
  AND status IN ('succeeded', 'failed', 'cancelled');
```

---

## 🔒 Security Considerations

### Row-Level Security (RLS)

Enable RLS for tenant isolation:

```sql
-- Enable RLS on executions table
ALTER TABLE executions ENABLE ROW LEVEL SECURITY;

-- Policy: Users can only see their tenant's executions
CREATE POLICY tenant_isolation ON executions
  FOR ALL
  USING (tenant_id = current_setting('app.current_tenant_id')::UUID);

-- Set tenant context in application
SET app.current_tenant_id = 'tenant-123';
```

### Sensitive Data

- ✅ **plan_snapshot**: May contain sensitive data (mask in logs)
- ✅ **result_summary**: May contain sensitive data (mask in logs)
- ✅ **error_message**: May contain sensitive data (mask in logs)
- ✅ **metadata**: May contain sensitive data (mask in logs)

**Mitigation**: Use `LogMaskingFilter` before storing in database.

---

## 📚 Related Documentation

- **Implementation Plan**: See `PHASE_7_IMPLEMENTATION_PLAN.md`
- **Safety Architecture**: See `PHASE_7_SAFETY_ARCHITECTURE.md`

---

**Document Version**: 1.0  
**Last Updated**: 2025-01-XX  
**Status**: Ready for Implementation