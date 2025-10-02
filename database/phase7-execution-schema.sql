-- ============================================================================
-- PHASE 7: STAGE E EXECUTION SCHEMA
-- Production-hardened execution architecture with 7 critical safety features
-- ============================================================================

-- Create execution schema
CREATE SCHEMA IF NOT EXISTS execution;

-- ============================================================================
-- ENUMS (Create first, referenced by tables)
-- ============================================================================

-- Execution status with FSM legal transitions
CREATE TYPE execution.execution_status AS ENUM (
    'pending_approval',  -- Initial state for Level 1-3
    'approved',          -- Approved, ready to execute
    'rejected',          -- Rejected by approver
    'queued',            -- In background queue
    'running',           -- Currently executing
    'completed',         -- Successfully completed
    'failed',            -- Failed with error
    'cancelled',         -- Cancelled by user
    'timeout',           -- Exceeded timeout policy
    'partial'            -- Some steps succeeded, some failed
);

-- Execution mode (immediate vs background)
CREATE TYPE execution.execution_mode AS ENUM (
    'immediate',   -- Synchronous execution (<10s)
    'background'   -- Asynchronous execution (>30s, via queue)
);

-- SLA class for timeout policies
CREATE TYPE execution.sla_class AS ENUM (
    'fast',    -- <10s operations
    'medium',  -- 10-30s operations
    'long'     -- >30s operations
);

-- Approval state
CREATE TYPE execution.approval_state AS ENUM (
    'pending',   -- Awaiting approval
    'approved',  -- Approved
    'rejected',  -- Rejected
    'expired'    -- Approval window expired
);

-- ============================================================================
-- CORE TABLES
-- ============================================================================

-- Executions table (main execution records)
CREATE TABLE execution.executions (
    -- Primary Key
    id SERIAL PRIMARY KEY,
    execution_id UUID UNIQUE NOT NULL DEFAULT gen_random_uuid(),
    
    -- Tenant & Actor (for multi-tenancy)
    tenant_id VARCHAR(255) NOT NULL,
    actor_id INTEGER NOT NULL, -- Reference to identity.users(id)
    
    -- Idempotency
    idempotency_key VARCHAR(64) NOT NULL, -- sha256(canonical_json(plan) + tenant_id + actor_id)
    plan_snapshot JSONB NOT NULL, -- Immutable snapshot of the plan
    
    -- Execution Metadata
    execution_mode execution.execution_mode NOT NULL,
    sla_class execution.sla_class NOT NULL,
    approval_level INTEGER NOT NULL CHECK (approval_level BETWEEN 0 AND 3),
    
    -- Status & FSM
    status execution.execution_status NOT NULL DEFAULT 'pending_approval',
    previous_status execution.execution_status, -- For audit trail
    status_changed_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    
    -- Timing
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    started_at TIMESTAMP WITH TIME ZONE,
    completed_at TIMESTAMP WITH TIME ZONE,
    timeout_at TIMESTAMP WITH TIME ZONE, -- Calculated from timeout_policies
    
    -- Results
    result JSONB, -- Final execution result
    error_message TEXT,
    error_details JSONB,
    
    -- Observability
    trace_id UUID, -- For distributed tracing
    parent_execution_id UUID, -- For nested executions
    tags JSONB DEFAULT '[]',
    metadata JSONB DEFAULT '{}',
    
    -- Audit
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    
    -- Constraints
    CONSTRAINT unique_idempotency_per_tenant UNIQUE (tenant_id, idempotency_key),
    CONSTRAINT valid_approval_level CHECK (approval_level IN (0, 1, 2, 3))
);

-- Execution steps table (step-level tracking)
CREATE TABLE execution.execution_steps (
    -- Primary Key
    id SERIAL PRIMARY KEY,
    step_id UUID UNIQUE NOT NULL DEFAULT gen_random_uuid(),
    
    -- Foreign Key
    execution_id UUID NOT NULL REFERENCES execution.executions(execution_id) ON DELETE CASCADE,
    
    -- Step Metadata
    step_index INTEGER NOT NULL, -- Order in the plan
    step_name VARCHAR(255) NOT NULL,
    step_type VARCHAR(100) NOT NULL, -- 'ssh_command', 'api_call', 'file_transfer', etc.
    target_asset_id INTEGER, -- Reference to assets.assets(id)
    target_hostname VARCHAR(255),
    
    -- Status
    status execution.execution_status NOT NULL DEFAULT 'queued',
    
    -- Timing
    started_at TIMESTAMP WITH TIME ZONE,
    completed_at TIMESTAMP WITH TIME ZONE,
    duration_ms INTEGER,
    
    -- Input/Output
    input_data JSONB,
    output_data JSONB,
    artifacts JSONB, -- Limited to 10KB per step
    
    -- Error Handling
    error_message TEXT,
    error_details JSONB,
    retry_count INTEGER DEFAULT 0,
    max_retries INTEGER DEFAULT 3,
    
    -- Observability
    trace_id UUID,
    logs TEXT, -- Masked logs
    
    -- Audit
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    
    -- Constraints
    CONSTRAINT unique_step_per_execution UNIQUE (execution_id, step_index)
);

-- Approvals table (approval workflow)
CREATE TABLE execution.approvals (
    -- Primary Key
    id SERIAL PRIMARY KEY,
    approval_id UUID UNIQUE NOT NULL DEFAULT gen_random_uuid(),
    
    -- Foreign Key
    execution_id UUID NOT NULL REFERENCES execution.executions(execution_id) ON DELETE CASCADE,
    
    -- Approval Metadata
    approval_level INTEGER NOT NULL CHECK (approval_level BETWEEN 1 AND 3),
    plan_hash VARCHAR(64) NOT NULL, -- Bound to plan snapshot
    
    -- Approver
    approver_id INTEGER, -- Reference to identity.users(id), NULL if pending
    approver_comment TEXT,
    
    -- State
    state execution.approval_state NOT NULL DEFAULT 'pending',
    
    -- Timing
    requested_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    expires_at TIMESTAMP WITH TIME ZONE, -- Approval window
    responded_at TIMESTAMP WITH TIME ZONE,
    
    -- Audit
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    
    -- Constraints
    CONSTRAINT one_approval_per_execution UNIQUE (execution_id)
);

-- Execution events table (audit trail for FSM transitions)
CREATE TABLE execution.execution_events (
    -- Primary Key
    id SERIAL PRIMARY KEY,
    event_id UUID UNIQUE NOT NULL DEFAULT gen_random_uuid(),
    
    -- Foreign Key
    execution_id UUID NOT NULL REFERENCES execution.executions(execution_id) ON DELETE CASCADE,
    
    -- Event Metadata
    event_type VARCHAR(100) NOT NULL, -- 'status_change', 'approval', 'cancellation', 'timeout', etc.
    from_status execution.execution_status,
    to_status execution.execution_status,
    
    -- Actor
    actor_id INTEGER, -- Reference to identity.users(id)
    actor_type VARCHAR(50), -- 'user', 'system', 'worker'
    
    -- Details
    details JSONB,
    error_message TEXT,
    
    -- Timing
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    
    -- Observability
    trace_id UUID
);

-- ============================================================================
-- BACKGROUND QUEUE TABLES
-- ============================================================================

-- Execution queue (Redis-backed, PostgreSQL for persistence)
CREATE TABLE execution.execution_queue (
    -- Primary Key
    id SERIAL PRIMARY KEY,
    queue_id UUID UNIQUE NOT NULL DEFAULT gen_random_uuid(),
    
    -- Foreign Key
    execution_id UUID NOT NULL REFERENCES execution.executions(execution_id) ON DELETE CASCADE,
    
    -- Queue Metadata
    priority INTEGER DEFAULT 5, -- 1 (highest) to 10 (lowest)
    sla_class execution.sla_class NOT NULL,
    
    -- Lease Management
    lease_token UUID, -- Worker lease token
    lease_expires_at TIMESTAMP WITH TIME ZONE, -- Lease timeout
    visibility_timeout_seconds INTEGER, -- Calculated from timeout_policies
    
    -- Retry Logic
    attempt_count INTEGER DEFAULT 0,
    max_attempts INTEGER DEFAULT 3, -- Based on SLA class
    last_error TEXT,
    
    -- Timing
    enqueued_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    dequeued_at TIMESTAMP WITH TIME ZONE,
    completed_at TIMESTAMP WITH TIME ZONE,
    
    -- Status
    status VARCHAR(50) DEFAULT 'pending', -- 'pending', 'processing', 'completed', 'failed'
    
    -- Audit
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    
    -- Constraints
    CONSTRAINT unique_execution_in_queue UNIQUE (execution_id)
);

-- Dead letter queue (DLQ for failed executions)
CREATE TABLE execution.execution_dlq (
    -- Primary Key
    id SERIAL PRIMARY KEY,
    dlq_id UUID UNIQUE NOT NULL DEFAULT gen_random_uuid(),
    
    -- Foreign Key
    execution_id UUID NOT NULL REFERENCES execution.executions(execution_id) ON DELETE CASCADE,
    
    -- Failure Metadata
    failure_reason TEXT NOT NULL,
    failure_details JSONB,
    attempt_count INTEGER NOT NULL,
    last_error TEXT,
    
    -- Original Queue Entry
    original_queue_id UUID,
    sla_class execution.sla_class NOT NULL,
    
    -- Timing
    failed_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    
    -- Retry/Requeue
    requeued BOOLEAN DEFAULT false,
    requeued_at TIMESTAMP WITH TIME ZONE,
    requeued_by INTEGER, -- Reference to identity.users(id)
    
    -- Audit
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    
    -- Constraints
    CONSTRAINT unique_execution_in_dlq UNIQUE (execution_id)
);

-- ============================================================================
-- SAFETY TABLES
-- ============================================================================

-- Execution locks (per-asset mutex)
CREATE TABLE execution.execution_locks (
    -- Primary Key
    id SERIAL PRIMARY KEY,
    lock_id UUID UNIQUE NOT NULL DEFAULT gen_random_uuid(),
    
    -- Lock Target
    asset_id INTEGER NOT NULL, -- Reference to assets.assets(id)
    tenant_id VARCHAR(255) NOT NULL,
    
    -- Lock Owner
    execution_id UUID NOT NULL REFERENCES execution.executions(execution_id) ON DELETE CASCADE,
    owner_tag VARCHAR(255) NOT NULL, -- Format: "execution:{execution_id}:worker:{worker_id}"
    
    -- Lock Metadata
    acquired_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    expires_at TIMESTAMP WITH TIME ZONE NOT NULL, -- TTL for stale lock reaper
    last_heartbeat_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    
    -- Status
    is_active BOOLEAN DEFAULT true,
    
    -- Audit
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    
    -- Constraints
    CONSTRAINT unique_lock_per_asset_tenant UNIQUE (asset_id, tenant_id)
);

-- Timeout policies (SLA class × action class matrix)
CREATE TABLE execution.timeout_policies (
    -- Primary Key
    id SERIAL PRIMARY KEY,
    
    -- Policy Key
    sla_class execution.sla_class NOT NULL,
    action_class VARCHAR(50) NOT NULL, -- 'read', 'modify', 'deploy'
    
    -- Timeout Values (in seconds)
    step_timeout_seconds INTEGER NOT NULL,
    execution_timeout_seconds INTEGER NOT NULL,
    lease_timeout_seconds INTEGER NOT NULL, -- For queue workers
    approval_timeout_seconds INTEGER, -- For approval workflows
    
    -- DLQ Thresholds
    max_attempts INTEGER NOT NULL,
    
    -- Metadata
    description TEXT,
    
    -- Audit
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    
    -- Constraints
    CONSTRAINT unique_timeout_policy UNIQUE (sla_class, action_class)
);

-- ============================================================================
-- INDEXES FOR PERFORMANCE
-- ============================================================================

-- Executions indexes
CREATE INDEX idx_executions_tenant_id ON execution.executions(tenant_id);
CREATE INDEX idx_executions_actor_id ON execution.executions(actor_id);
CREATE INDEX idx_executions_status ON execution.executions(status);
CREATE INDEX idx_executions_execution_mode ON execution.executions(execution_mode);
CREATE INDEX idx_executions_sla_class ON execution.executions(sla_class);
CREATE INDEX idx_executions_created_at ON execution.executions(created_at);
CREATE INDEX idx_executions_idempotency_key ON execution.executions(tenant_id, idempotency_key);
CREATE INDEX idx_executions_trace_id ON execution.executions(trace_id);

-- Execution steps indexes
CREATE INDEX idx_execution_steps_execution_id ON execution.execution_steps(execution_id);
CREATE INDEX idx_execution_steps_status ON execution.execution_steps(status);
CREATE INDEX idx_execution_steps_target_asset_id ON execution.execution_steps(target_asset_id);
CREATE INDEX idx_execution_steps_step_index ON execution.execution_steps(execution_id, step_index);

-- Approvals indexes
CREATE INDEX idx_approvals_execution_id ON execution.approvals(execution_id);
CREATE INDEX idx_approvals_state ON execution.approvals(state);
CREATE INDEX idx_approvals_approver_id ON execution.approvals(approver_id);
CREATE INDEX idx_approvals_expires_at ON execution.approvals(expires_at);

-- Execution events indexes
CREATE INDEX idx_execution_events_execution_id ON execution.execution_events(execution_id);
CREATE INDEX idx_execution_events_event_type ON execution.execution_events(event_type);
CREATE INDEX idx_execution_events_created_at ON execution.execution_events(created_at);
CREATE INDEX idx_execution_events_trace_id ON execution.execution_events(trace_id);

-- Execution queue indexes
CREATE INDEX idx_execution_queue_execution_id ON execution.execution_queue(execution_id);
CREATE INDEX idx_execution_queue_status ON execution.execution_queue(status);
CREATE INDEX idx_execution_queue_priority ON execution.execution_queue(priority, enqueued_at);
CREATE INDEX idx_execution_queue_lease_expires_at ON execution.execution_queue(lease_expires_at);
CREATE INDEX idx_execution_queue_sla_class ON execution.execution_queue(sla_class);

-- Execution DLQ indexes
CREATE INDEX idx_execution_dlq_execution_id ON execution.execution_dlq(execution_id);
CREATE INDEX idx_execution_dlq_failed_at ON execution.execution_dlq(failed_at);
CREATE INDEX idx_execution_dlq_requeued ON execution.execution_dlq(requeued);

-- Execution locks indexes
CREATE INDEX idx_execution_locks_asset_id ON execution.execution_locks(asset_id);
CREATE INDEX idx_execution_locks_tenant_id ON execution.execution_locks(tenant_id);
CREATE INDEX idx_execution_locks_execution_id ON execution.execution_locks(execution_id);
CREATE INDEX idx_execution_locks_expires_at ON execution.execution_locks(expires_at);
CREATE INDEX idx_execution_locks_is_active ON execution.execution_locks(is_active);

-- Timeout policies indexes
CREATE INDEX idx_timeout_policies_sla_class ON execution.timeout_policies(sla_class);
CREATE INDEX idx_timeout_policies_action_class ON execution.timeout_policies(action_class);

-- ============================================================================
-- INITIAL DATA: TIMEOUT POLICIES
-- ============================================================================

-- Insert default timeout policies (SLA class × action class matrix)
INSERT INTO execution.timeout_policies (sla_class, action_class, step_timeout_seconds, execution_timeout_seconds, lease_timeout_seconds, approval_timeout_seconds, max_attempts, description) VALUES
    -- Fast SLA (read operations)
    ('fast', 'read', 5, 10, 15, 300, 3, 'Fast read operations: <5s per step, <10s total'),
    -- Fast SLA (modify operations)
    ('fast', 'modify', 8, 15, 20, 600, 3, 'Fast modify operations: <8s per step, <15s total'),
    -- Fast SLA (deploy operations)
    ('fast', 'deploy', 10, 20, 30, 900, 3, 'Fast deploy operations: <10s per step, <20s total'),
    
    -- Medium SLA (read operations)
    ('medium', 'read', 15, 30, 45, 600, 5, 'Medium read operations: <15s per step, <30s total'),
    -- Medium SLA (modify operations)
    ('medium', 'modify', 20, 45, 60, 900, 5, 'Medium modify operations: <20s per step, <45s total'),
    -- Medium SLA (deploy operations)
    ('medium', 'deploy', 30, 60, 90, 1800, 5, 'Medium deploy operations: <30s per step, <60s total'),
    
    -- Long SLA (read operations)
    ('long', 'read', 60, 300, 360, 1800, 3, 'Long read operations: <60s per step, <5min total'),
    -- Long SLA (modify operations)
    ('long', 'modify', 120, 600, 720, 3600, 3, 'Long modify operations: <120s per step, <10min total'),
    -- Long SLA (deploy operations)
    ('long', 'deploy', 300, 1800, 2160, 7200, 3, 'Long deploy operations: <5min per step, <30min total');

-- ============================================================================
-- COMMENTS FOR DOCUMENTATION
-- ============================================================================

COMMENT ON SCHEMA execution IS 'Phase 7: Stage E Execution schema with production-hardened safety features';

COMMENT ON TABLE execution.executions IS 'Main execution records with tenant-scoped idempotency and FSM state machine';
COMMENT ON TABLE execution.execution_steps IS 'Step-level tracking with retry logic and artifact storage (10KB cap)';
COMMENT ON TABLE execution.approvals IS 'Approval workflow with plan hash binding and expiration';
COMMENT ON TABLE execution.execution_events IS 'Audit trail for FSM transitions and execution events';
COMMENT ON TABLE execution.execution_queue IS 'Background execution queue with lease management and retry logic';
COMMENT ON TABLE execution.execution_dlq IS 'Dead letter queue for failed executions requiring manual intervention';
COMMENT ON TABLE execution.execution_locks IS 'Per-asset mutex locks with TTL and stale lock reaper support';
COMMENT ON TABLE execution.timeout_policies IS 'SLA class × action class timeout matrix with DLQ thresholds';

COMMENT ON COLUMN execution.executions.idempotency_key IS 'sha256(canonical_json(plan) + tenant_id + actor_id) for duplicate prevention';
COMMENT ON COLUMN execution.executions.plan_snapshot IS 'Immutable snapshot of the execution plan with deterministic target ordering';
COMMENT ON COLUMN execution.execution_steps.artifacts IS 'Step artifacts limited to 10KB per step';
COMMENT ON COLUMN execution.approvals.plan_hash IS 'Bound to plan snapshot to prevent approval tampering';
COMMENT ON COLUMN execution.execution_locks.owner_tag IS 'Format: execution:{execution_id}:worker:{worker_id}';
COMMENT ON COLUMN execution.timeout_policies.lease_timeout_seconds IS 'Formula: max(step_timeout + buffer, 2× p95_step_duration)';

-- ============================================================================
-- VERIFICATION QUERIES (for GO/NO-GO checklist)
-- ============================================================================

-- Verify ENUMs
DO $$
BEGIN
    RAISE NOTICE 'Verifying ENUMs...';
    ASSERT (SELECT COUNT(*) FROM pg_type WHERE typname = 'execution_status' AND typnamespace = 'execution'::regnamespace) = 1, 'execution_status ENUM not found';
    ASSERT (SELECT COUNT(*) FROM pg_type WHERE typname = 'execution_mode' AND typnamespace = 'execution'::regnamespace) = 1, 'execution_mode ENUM not found';
    ASSERT (SELECT COUNT(*) FROM pg_type WHERE typname = 'sla_class' AND typnamespace = 'execution'::regnamespace) = 1, 'sla_class ENUM not found';
    ASSERT (SELECT COUNT(*) FROM pg_type WHERE typname = 'approval_state' AND typnamespace = 'execution'::regnamespace) = 1, 'approval_state ENUM not found';
    RAISE NOTICE 'ENUMs verified successfully';
END $$;

-- Verify tables
DO $$
BEGIN
    RAISE NOTICE 'Verifying tables...';
    ASSERT (SELECT COUNT(*) FROM information_schema.tables WHERE table_schema = 'execution' AND table_name = 'executions') = 1, 'executions table not found';
    ASSERT (SELECT COUNT(*) FROM information_schema.tables WHERE table_schema = 'execution' AND table_name = 'execution_steps') = 1, 'execution_steps table not found';
    ASSERT (SELECT COUNT(*) FROM information_schema.tables WHERE table_schema = 'execution' AND table_name = 'approvals') = 1, 'approvals table not found';
    ASSERT (SELECT COUNT(*) FROM information_schema.tables WHERE table_schema = 'execution' AND table_name = 'execution_events') = 1, 'execution_events table not found';
    ASSERT (SELECT COUNT(*) FROM information_schema.tables WHERE table_schema = 'execution' AND table_name = 'execution_queue') = 1, 'execution_queue table not found';
    ASSERT (SELECT COUNT(*) FROM information_schema.tables WHERE table_schema = 'execution' AND table_name = 'execution_dlq') = 1, 'execution_dlq table not found';
    ASSERT (SELECT COUNT(*) FROM information_schema.tables WHERE table_schema = 'execution' AND table_name = 'execution_locks') = 1, 'execution_locks table not found';
    ASSERT (SELECT COUNT(*) FROM information_schema.tables WHERE table_schema = 'execution' AND table_name = 'timeout_policies') = 1, 'timeout_policies table not found';
    RAISE NOTICE 'Tables verified successfully';
END $$;

-- Verify indexes
DO $$
BEGIN
    RAISE NOTICE 'Verifying indexes...';
    ASSERT (SELECT COUNT(*) FROM pg_indexes WHERE schemaname = 'execution' AND tablename = 'executions') >= 8, 'Missing indexes on executions table';
    ASSERT (SELECT COUNT(*) FROM pg_indexes WHERE schemaname = 'execution' AND tablename = 'execution_steps') >= 4, 'Missing indexes on execution_steps table';
    ASSERT (SELECT COUNT(*) FROM pg_indexes WHERE schemaname = 'execution' AND tablename = 'approvals') >= 4, 'Missing indexes on approvals table';
    ASSERT (SELECT COUNT(*) FROM pg_indexes WHERE schemaname = 'execution' AND tablename = 'execution_events') >= 3, 'Missing indexes on execution_events table';
    ASSERT (SELECT COUNT(*) FROM pg_indexes WHERE schemaname = 'execution' AND tablename = 'execution_queue') >= 5, 'Missing indexes on execution_queue table';
    ASSERT (SELECT COUNT(*) FROM pg_indexes WHERE schemaname = 'execution' AND tablename = 'execution_dlq') >= 3, 'Missing indexes on execution_dlq table';
    ASSERT (SELECT COUNT(*) FROM pg_indexes WHERE schemaname = 'execution' AND tablename = 'execution_locks') >= 5, 'Missing indexes on execution_locks table';
    ASSERT (SELECT COUNT(*) FROM pg_indexes WHERE schemaname = 'execution' AND tablename = 'timeout_policies') >= 2, 'Missing indexes on timeout_policies table';
    RAISE NOTICE 'Indexes verified successfully';
END $$;

-- Verify timeout policies data
DO $$
BEGIN
    RAISE NOTICE 'Verifying timeout policies data...';
    ASSERT (SELECT COUNT(*) FROM execution.timeout_policies) = 9, 'Expected 9 timeout policies (3 SLA classes × 3 action classes)';
    RAISE NOTICE 'Timeout policies data verified successfully';
END $$;

RAISE NOTICE '✅ Phase 7 database schema created successfully!';