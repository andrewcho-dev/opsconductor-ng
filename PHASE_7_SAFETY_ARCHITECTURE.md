# Phase 7: Safety Architecture - Production-Hardened Features

## 📋 Overview

This document details the 7 critical safety features that prevent production incidents in Stage E (Execution):

1. **Idempotency** - Prevent duplicate execution from browser refresh
2. **Mutex** - Prevent concurrent operations on same asset
3. **RBAC** - Enforce permissions at execution boundary (defense in depth)
4. **Secrets** - Never leak credentials in logs
5. **Cancellation** - Stop zombie jobs
6. **Timeout** - Prevent runaway executions
7. **Log Masking** - Automatic secret redaction

These are **non-negotiable for Phase 1** - they prevent 3am production incidents.

---

## 🔒 1. Idempotency

### Problem

**Browser refresh creates duplicate execution:**
- User submits "Deploy to 50 servers"
- Browser hangs, user hits refresh
- Second request creates duplicate deployment
- 100 servers deployed instead of 50 ❌

### Solution

**Tenant-scoped idempotency with plan hashing:**

```python
# Generate idempotency key
idempotency_key = sha256(
    canonical_json(plan) + tenant_id + actor_id
)

# Check for duplicate
existing = db.executions.get_by_idempotency_key(
    tenant_id=tenant_id,
    idempotency_key=idempotency_key
)

if existing and existing.status in ["running", "succeeded"]:
    # Return cached result
    return existing.to_result()
```

### Key Features

✅ **Tenant-scoped uniqueness** - Same plan from different tenants creates separate executions  
✅ **Canonical plan hashing** - Sorted keys, no whitespace, deterministic  
✅ **Plan snapshot storage** - Frozen audit trail for compliance  
✅ **Retry of failed executions** - Allow retry if previous execution failed  

### Database Schema

```sql
-- Tenant-scoped unique index
CREATE UNIQUE INDEX ux_exec_tenant_idem 
  ON executions (tenant_id, idempotency_key);

-- Plan snapshot for audit
ALTER TABLE executions ADD COLUMN plan_snapshot JSONB NOT NULL;
```

### Implementation

**File**: `pipeline/stages/stage_e/safety/idempotency.py`

```python
class IdempotencyManager:
    def generate_idempotency_key(
        self,
        plan: ExecutionPlanV1,
        tenant_id: str,
        actor_id: str
    ) -> str:
        """
        Generate idempotency key from plan + tenant + actor.
        
        Formula: sha256(canonical_json(plan) + tenant_id + actor_id)
        """
        # Canonicalize plan (sorted keys, no whitespace)
        canonical_plan = json.dumps(
            plan.dict(),
            sort_keys=True,
            separators=(',', ':')  # No whitespace
        )
        
        # Combine with tenant and actor
        combined = f"{canonical_plan}|{tenant_id}|{actor_id}"
        
        # Hash
        return hashlib.sha256(combined.encode()).hexdigest()[:32]
    
    async def check_duplicate(
        self,
        idempotency_key: str,
        tenant_id: str
    ) -> Optional[ExecutionResultV1]:
        """
        Check if request already executed (tenant-scoped).
        
        Returns cached result if found, None otherwise.
        """
        existing = await self.db.executions.get_by_idempotency_key(
            tenant_id=tenant_id,
            idempotency_key=idempotency_key
        )
        
        if not existing:
            return None
        
        # Return cached result if execution succeeded or is running
        if existing.status in ["running", "succeeded"]:
            logger.info(
                "Duplicate request detected",
                idempotency_key=idempotency_key,
                tenant_id=tenant_id,
                existing_execution_id=existing.id,
                existing_status=existing.status
            )
            return existing.to_result()
        
        # Allow retry of failed/cancelled executions
        if existing.status in ["failed", "cancelled"]:
            logger.info(
                "Retrying failed/cancelled execution",
                idempotency_key=idempotency_key,
                tenant_id=tenant_id,
                existing_execution_id=existing.id,
                existing_status=existing.status
            )
            return None
        
        return None
```

### Test Cases

```python
def test_idempotency_prevents_duplicate():
    """Browser refresh doesn't create duplicate execution"""
    plan = create_test_plan()
    
    # First request
    result1 = await executor.execute(plan, context)
    assert result1.execution_id == "exec-123"
    
    # Second request (browser refresh)
    result2 = await executor.execute(plan, context)
    assert result2.execution_id == "exec-123"  # Same execution
    assert result2.status == result1.status
    
    # Verify only one execution in database
    executions = await db.executions.find_by_plan_hash(plan_hash)
    assert len(executions) == 1

def test_idempotency_tenant_scoped():
    """Same plan from different tenants creates separate executions"""
    plan = create_test_plan()
    
    # Tenant 1
    result1 = await executor.execute(plan, context_tenant1)
    
    # Tenant 2 (same plan)
    result2 = await executor.execute(plan, context_tenant2)
    
    # Different executions
    assert result1.execution_id != result2.execution_id
```

---

## 🔐 2. Mutex (Per-Asset Locking)

### Problem

**Concurrent operations on same asset cause conflicts:**
- User 1: "Restart nginx on server-01"
- User 2: "Deploy app to server-01" (at same time)
- Both operations run simultaneously
- Service crashes, deployment fails ❌

### Solution

**Redis-based per-asset mutex with owner tags:**

```python
# Acquire lock
async with mutex_manager.acquire_asset_lock(
    execution_id=exec_id,
    tenant_id=tenant_id,
    target_ref="server-01",
    action="restart_service",
    timeout=60
):
    # Execute operation (exclusive access)
    await automation_client.restart_service("server-01", "nginx")
# Lock automatically released
```

### Key Features

✅ **Per-asset granularity** - Lock specific asset, not entire system  
✅ **Owner tags** - Only owner can release lock (prevents accidental release)  
✅ **Stale lock reaper** - Cron job cleans up expired locks (edge case recovery)  
✅ **Database tracking** - Observability and debugging  

### Lock Key Format

```
lock:v1:{tenant_id}:{target_ref}:{action}

Examples:
- lock:v1:tenant-123:server-01:restart_service
- lock:v1:tenant-123:server-01:deploy
- lock:v1:tenant-456:db-prod:backup
```

### Database Schema

```sql
CREATE TABLE execution_locks (
  id UUID PRIMARY KEY,
  lock_key VARCHAR(500) NOT NULL UNIQUE,
  execution_id UUID NOT NULL REFERENCES executions(id),
  owner_tag VARCHAR(100) NOT NULL,  -- exec_id for verification
  acquired_at TIMESTAMPTZ NOT NULL,
  expires_at TIMESTAMPTZ NOT NULL,
  metadata JSONB
);

-- Stale lock detection
CREATE INDEX ix_locks_stale 
  ON execution_locks (acquired_at) 
  WHERE expires_at < NOW();
```

### Implementation

**File**: `pipeline/stages/stage_e/safety/mutex.py`

```python
class MutexManager:
    def _generate_lock_key(
        self,
        tenant_id: str,
        target_ref: str,
        action: str
    ) -> str:
        """
        Generate lock key with versioning.
        Format: lock:v1:{tenant}:{target}:{action}
        """
        return f"lock:v1:{tenant_id}:{target_ref}:{action}"
    
    @asynccontextmanager
    async def acquire_asset_lock(
        self,
        execution_id: str,
        tenant_id: str,
        target_ref: str,
        action: str,
        timeout: int = 60
    ):
        """
        Acquire exclusive lock on asset with owner tag.
        
        Raises:
            ResourceBusyError: If lock is held by another execution
        """
        lock_key = self._generate_lock_key(tenant_id, target_ref, action)
        owner_tag = execution_id
        
        # Try to acquire lock in Redis
        acquired = await self.redis.set(
            lock_key,
            owner_tag,
            nx=True,  # Only set if not exists
            ex=timeout  # TTL
        )
        
        if not acquired:
            # Lock is held by another execution
            current_owner = await self.redis.get(lock_key)
            
            logger.warning(
                "Resource is locked",
                lock_key=lock_key,
                current_owner=current_owner,
                requested_by=execution_id,
                tenant_id=tenant_id,
                target_ref=target_ref,
                action=action
            )
            
            raise ResourceBusyError(
                f"Asset {target_ref} is locked by execution {current_owner}. "
                f"Another {action} operation is in progress."
            )
        
        # Track lock in database for observability
        expires_at = datetime.utcnow() + timedelta(seconds=timeout)
        await self.db.execution_locks.create(
            lock_key=lock_key,
            execution_id=execution_id,
            owner_tag=owner_tag,
            acquired_at=datetime.utcnow(),
            expires_at=expires_at
        )
        
        try:
            yield  # Execute the operation
        finally:
            # Release lock (only if we still own it)
            await self._release_lock(lock_key, owner_tag, execution_id)
    
    async def _release_lock(
        self,
        lock_key: str,
        owner_tag: str,
        execution_id: str
    ):
        """
        Release lock only if we still own it.
        """
        # Lua script for atomic check-and-delete
        lua_script = """
        if redis.call("get", KEYS[1]) == ARGV[1] then
            return redis.call("del", KEYS[1])
        else
            return 0
        end
        """
        
        released = await self.redis.eval(
            lua_script,
            keys=[lock_key],
            args=[owner_tag]
        )
        
        if released:
            await self.db.execution_locks.delete_by_key(lock_key)
    
    async def reap_stale_locks(self):
        """
        Cron job to clean up stale locks (edge case recovery).
        
        Finds locks in DB that have expired but still exist in Redis.
        """
        stale_locks = await self.db.execution_locks.find_stale(
            threshold=datetime.utcnow()
        )
        
        for lock in stale_locks:
            # Force release
            await self.redis.delete(lock.lock_key)
            await self.db.execution_locks.delete(lock.id)
            
            logger.warning(
                "Reaped stale lock",
                lock_key=lock.lock_key,
                execution_id=lock.execution_id,
                acquired_at=lock.acquired_at,
                expires_at=lock.expires_at
            )
```

### Test Cases

```python
def test_mutex_prevents_concurrent_operations():
    """Concurrent operations on same asset blocked"""
    # Start execution 1
    exec1 = executor.execute(plan_restart_nginx, context1)
    
    # Try to start execution 2 (same asset)
    with pytest.raises(ResourceBusyError) as exc:
        exec2 = executor.execute(plan_deploy_app, context2)
    
    assert "server-01 is locked" in str(exc.value)
    assert "exec-123" in str(exc.value)  # Shows who owns lock

def test_mutex_released_after_execution():
    """Lock released after execution completes"""
    # Execute
    result = await executor.execute(plan, context)
    assert result.status == "succeeded"
    
    # Verify lock released
    lock_status = await mutex_manager.check_lock_status(
        tenant_id="tenant-123",
        target_ref="server-01",
        action="restart_service"
    )
    assert lock_status is None  # No lock

def test_stale_lock_reaper():
    """Stale locks cleaned up by cron job"""
    # Create expired lock
    await create_expired_lock("server-01")
    
    # Run reaper
    await mutex_manager.reap_stale_locks()
    
    # Verify lock removed
    lock_status = await mutex_manager.check_lock_status(
        tenant_id="tenant-123",
        target_ref="server-01",
        action="restart_service"
    )
    assert lock_status is None
```

---

## 🛡️ 3. RBAC (Defense in Depth)

### Problem

**API-only RBAC can be bypassed:**
- Attacker compromises background worker
- Worker executes operations without permission checks
- Privilege escalation ❌

### Solution

**Worker re-validates permissions (defense in depth):**

```python
# API tier validates
await rbac_validator.validate_execution(
    actor_id=actor_id,
    tenant_id=tenant_id,
    plan=plan
)

# Worker ALSO validates (defense in depth)
async def process_job(job):
    # Re-validate permissions
    await rbac_validator.validate_execution(
        actor_id=job.context.actor_id,
        tenant_id=job.context.tenant_id,
        plan=job.plan
    )
    
    # Execute
    await execution_engine.execute_plan(job.plan, job.context)
```

### Key Features

✅ **API tier validation** - First line of defense  
✅ **Worker validation** - Second line of defense (mandatory for both immediate + background)  
✅ **Tenant isolation** - Enforce tenant boundaries  
✅ **Action authorization** - Check specific action permissions  
✅ **SOC audit logging** - Distinct `rbac_violation` event kind for security queries  

### Implementation

**File**: `pipeline/stages/stage_e/safety/rbac_validator.py`

```python
class RBACValidator:
    async def validate_execution(
        self,
        actor_id: str,
        tenant_id: str,
        plan: ExecutionPlanV1
    ):
        """
        Validate actor has permission to execute plan.
        
        Raises:
            PermissionError: If actor lacks required permissions
        """
        # Get actor
        actor = await self.db.users.get(actor_id)
        if not actor:
            raise PermissionError(f"Actor {actor_id} not found")
        
        # Verify tenant membership
        if actor.tenant_id != tenant_id:
            # Log distinct rbac_violation event for SOC/audit queries
            await self.db.execution_events.create(
                execution_id=plan.execution_id,
                event_type="rbac_violation",
                event_data={
                    "violation_type": "tenant_isolation",
                    "actor_id": actor_id,
                    "actor_tenant": actor.tenant_id,
                    "requested_tenant": tenant_id,
                    "severity": "critical",
                }
            )
            logger.error(
                "Tenant isolation violation",
                actor_id=actor_id,
                actor_tenant=actor.tenant_id,
                requested_tenant=tenant_id,
                event_type="rbac_violation"
            )
            raise PermissionError(
                f"Actor {actor_id} does not belong to tenant {tenant_id}"
            )
        
        # Check action permissions
        for step in plan.steps:
            required_permission = self._get_required_permission(step.action)
            
            if not await self._has_permission(actor, required_permission):
                logger.error(
                    "Permission denied",
                    actor_id=actor_id,
                    action=step.action,
                    required_permission=required_permission
                )
                raise PermissionError(
                    f"Actor {actor_id} lacks permission: {required_permission}"
                )
    
    async def validate_approval(
        self,
        approver_id: str,
        required_role: str
    ):
        """
        Validate approver has required role.
        
        Raises:
            PermissionError: If approver lacks required role
        """
        approver = await self.db.users.get(approver_id)
        if not approver:
            raise PermissionError(f"Approver {approver_id} not found")
        
        if required_role not in approver.roles:
            logger.error(
                "Approval permission denied",
                approver_id=approver_id,
                required_role=required_role,
                approver_roles=approver.roles
            )
            raise PermissionError(
                f"Approver {approver_id} lacks required role: {required_role}"
            )
    
    def _get_required_permission(self, action: str) -> str:
        """Map action to required permission"""
        permission_map = {
            "query_assets": "asset:read",
            "get_asset_details": "asset:read",
            "execute_command": "automation:execute",
            "restart_service": "automation:execute",
            "deploy": "automation:deploy",
        }
        return permission_map.get(action, "automation:execute")
```

### Test Cases

```python
def test_rbac_enforces_tenant_isolation():
    """Cross-tenant access denied"""
    plan = create_test_plan()
    context = create_context(
        actor_id="user-123",  # Belongs to tenant-456
        tenant_id="tenant-789"  # Different tenant
    )
    
    with pytest.raises(PermissionError) as exc:
        await executor.execute(plan, context)
    
    assert "does not belong to tenant" in str(exc.value)

def test_rbac_enforces_action_permissions():
    """Actor without permission denied"""
    plan = create_plan_with_action("deploy")
    context = create_context(
        actor_id="user-123",  # Has "asset:read" only
        tenant_id="tenant-456"
    )
    
    with pytest.raises(PermissionError) as exc:
        await executor.execute(plan, context)
    
    assert "lacks permission: automation:deploy" in str(exc.value)

def test_worker_revalidates_rbac():
    """Worker re-validates permissions (defense in depth)"""
    # Enqueue job
    job_id = await queue.enqueue(plan, context)
    
    # Revoke actor permissions
    await db.users.update(actor_id, permissions=[])
    
    # Worker picks up job
    await worker.process_job(job_id)
    
    # Execution fails with permission error
    execution = await db.executions.get(execution_id)
    assert execution.status == "failed"
    assert "PermissionError" in execution.error_class
```

---

## 🔑 4. Secrets (Never Leak Credentials)

### Problem

**Credentials leak in logs:**
- Execution fails with error: "SSH connection failed: password='P@ssw0rd123'"
- Logs stored in Elasticsearch
- Attacker searches logs for "password="
- Credentials compromised ❌

### Solution

**Automatic log masking + just-in-time resolution:**

```python
# Resolve credentials just-in-time
credentials = await secrets_handler.resolve_credentials(asset_id)

# Execute with credentials
result = await ssh_client.execute(command, credentials)

# Zeroize credentials immediately
secrets_handler.zeroize(credentials)

# Logs automatically masked
logger.info(
    "Execution completed",
    asset_id=asset_id,
    credentials=credentials  # Automatically masked to "***REDACTED***"
)
```

### Key Features

✅ **Just-in-time resolution** - Credentials fetched only when needed  
✅ **Immediate zeroization** - Credentials wiped from memory after use  
✅ **Automatic masking** - Logs filtered before storage  
✅ **Denylist patterns** - password, token, key, private_key, secret, credential, api_key  

### Implementation

**File**: `pipeline/stages/stage_e/safety/log_masking.py`

```python
class LogMaskingFilter:
    """
    Automatically masks sensitive data in logs.
    
    Denylist: password, token, key, private_key, secret, credential, api_key, etc.
    """
    
    # Patterns to mask (case-insensitive)
    SENSITIVE_PATTERNS = [
        r'password',
        r'passwd',
        r'token',
        r'api[_-]?key',
        r'secret',
        r'credential',
        r'private[_-]?key',
        r'access[_-]?key',
        r'auth',
        r'bearer',
        r'session',
    ]
    
    MASK_VALUE = "***REDACTED***"
    
    def mask_dict(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Recursively mask sensitive fields in dictionary.
        """
        if not isinstance(data, dict):
            return data
        
        masked = {}
        for key, value in data.items():
            # Check if key matches sensitive pattern
            if self._is_sensitive_key(key):
                masked[key] = self.MASK_VALUE
            elif isinstance(value, dict):
                masked[key] = self.mask_dict(value)
            elif isinstance(value, list):
                masked[key] = [
                    self.mask_dict(item) if isinstance(item, dict) else item
                    for item in value
                ]
            else:
                masked[key] = value
        
        return masked
    
    def _is_sensitive_key(self, key: str) -> bool:
        """Check if key matches any sensitive pattern"""
        return any(pattern.search(key) for pattern in self.patterns)
```

**File**: `pipeline/stages/stage_e/safety/secrets_handler.py`

```python
class SecretsHandler:
    async def resolve_credentials(self, asset_id: str) -> dict:
        """
        Resolve credentials just-in-time.
        
        Returns short-lived session credentials where possible.
        """
        # Get credential reference from asset
        asset = await self.db.assets.get(asset_id)
        credential_ref = asset.credential_ref
        
        # Resolve from secrets backend (Vault/AWS Secrets Manager)
        credentials = await self.secrets_backend.get(credential_ref)
        
        logger.info(
            "Credentials resolved",
            asset_id=asset_id,
            credential_ref=credential_ref,
            # DO NOT log credentials
        )
        
        return credentials
    
    def zeroize(self, credentials: dict):
        """
        Zeroize credentials from memory.
        """
        for key in credentials:
            credentials[key] = None
        credentials.clear()
```

### Test Cases

```python
def test_log_masking_filters_passwords():
    """Passwords masked in logs"""
    log_record = {
        "message": "SSH connection failed",
        "extra": {
            "password": "P@ssw0rd123",
            "username": "admin"
        }
    }
    
    masked = log_masker.mask_log_record(log_record)
    
    assert masked["extra"]["password"] == "***REDACTED***"
    assert masked["extra"]["username"] == "admin"  # Not masked

def test_secrets_never_stored_in_database():
    """Credentials not stored in execution records"""
    plan = create_plan_with_credentials()
    result = await executor.execute(plan, context)
    
    # Check database
    execution = await db.executions.get(result.execution_id)
    
    # Verify no credentials in plan_snapshot
    assert "password" not in json.dumps(execution.plan_snapshot)
    assert "token" not in json.dumps(execution.plan_snapshot)
```

---

## ⏹️ 5. Cancellation (Stop Zombie Jobs)

### Problem

**Long-running jobs can't be stopped:**
- User starts "Deploy to 1000 servers"
- Realizes wrong version selected
- No way to cancel
- Deployment continues for hours ❌

### Solution

**Cooperative cancellation with tokens:**

```python
# User requests cancellation
await cancellation_manager.request_cancellation(
    execution_id=exec_id,
    cancelled_by=user_id,
    reason="Wrong version selected"
)

# Worker checks token between steps
for step in plan.steps:
    # Check cancellation token
    await cancellation_manager.check_cancellation_token(execution_id)
    
    # Execute step
    await execute_step(step)
```

### Key Features

✅ **Cooperative cancellation** - Worker checks token between steps  
✅ **Fast Redis check** - Low latency cancellation detection  
✅ **Mutex release guaranteed** - Locks released even on exceptions  
✅ **Status tracking** - Cancelled status recorded in database  
✅ **Idempotent cancellation** - Multiple cancel requests safe (cancelled_by + cancelled_at set together)  
✅ **Best-effort semantics** - Steps in progress complete; future steps skipped  

### Cancellation Semantics

**What happens on cancel:**

1. **Steps in progress**: Complete current step (best-effort, no hard abort)
2. **Future steps**: Skipped entirely
3. **Mutex release**: **GUARANTEED** even on exceptions (via try/finally)
4. **Database update**: `cancelled_by` + `cancelled_at` set atomically
5. **Idempotency**: Multiple cancel requests return success (no-op if already cancelled)

**Handler guarantees:**

```python
# Worker execution loop with guaranteed mutex release
async def execute_with_cancellation(execution_id: str, plan: ExecutionPlanV1):
    mutex_acquired = False
    try:
        # Acquire mutex
        await mutex_manager.acquire(execution_id, plan.targets)
        mutex_acquired = True
        
        # Execute steps with cancellation checks
        for step in plan.steps:
            # Check cancellation token (raises ExecutionCancelledException)
            await cancellation_manager.check_cancellation_token(execution_id)
            
            # Execute step (best-effort, no hard abort mid-step)
            await execute_step(step)
    
    except ExecutionCancelledException:
        logger.info("Execution cancelled, cleaning up", execution_id=execution_id)
        # Mutex released in finally block
        raise
    
    finally:
        # GUARANTEE: Mutex always released, even on exceptions
        if mutex_acquired:
            await mutex_manager.release(execution_id, plan.targets)
```

### Implementation

**File**: `pipeline/stages/stage_e/cancellation_manager.py`

```python
class CancellationManager:
    async def request_cancellation(
        self,
        execution_id: str,
        cancelled_by: str,
        reason: str
    ) -> bool:
        """
        Request cancellation of running execution (idempotent).
        
        Returns True if cancellation requested, False if already completed.
        Multiple calls are safe (no-op if already cancelled).
        """
        execution = await self.db.executions.get(execution_id)
        
        # Idempotency: If already cancelled, return success (no-op)
        if execution.status == "cancelled":
            logger.info(
                "Execution already cancelled (idempotent no-op)",
                execution_id=execution_id,
                original_cancelled_by=execution.cancelled_by,
                original_cancelled_at=execution.cancelled_at
            )
            return True
        
        # Can only cancel pending/running executions
        if execution.status not in ["pending", "awaiting_approval", "approved", "running"]:
            return False
        
        # Set cancellation flag in Redis (for fast worker checks)
        await self.redis.set(
            f"cancel:{execution_id}",
            "true",
            ex=3600  # 1 hour TTL
        )
        
        # Update database (cancelled_by + cancelled_at set atomically)
        await self.db.executions.update(
            execution_id,
            status="cancelled",
            cancelled_by=cancelled_by,
            cancelled_at=datetime.utcnow(),
            cancellation_reason=reason,
            ended_at=datetime.utcnow()
        )
        
        # Log cancellation event
        await self.db.execution_events.create(
            execution_id=execution_id,
            event_type="cancellation_requested",
            event_data={
                "cancelled_by": cancelled_by,
                "reason": reason,
            }
        )
        
        return True
    
    async def is_cancelled(self, execution_id: str) -> bool:
        """
        Check if execution has been cancelled (fast Redis check).
        
        Workers should call this between steps.
        """
        cancelled = await self.redis.get(f"cancel:{execution_id}")
        return cancelled == "true"
    
    async def check_cancellation_token(self, execution_id: str):
        """
        Raise exception if execution has been cancelled.
        
        Workers should call this at the start of each step.
        """
        if await self.is_cancelled(execution_id):
            raise ExecutionCancelledException(
                f"Execution {execution_id} was cancelled"
            )
```

### Test Cases

```python
def test_cancellation_stops_execution():
    """Cancelled execution stops after current step"""
    # Start long execution (10 steps)
    exec_id = await executor.execute_background(plan_10_steps, context)
    
    # Wait for step 3 to complete
    await wait_for_step(exec_id, step_number=3)
    
    # Cancel
    await cancellation_manager.request_cancellation(
        execution_id=exec_id,
        cancelled_by=user_id,
        reason="Test cancellation"
    )
    
    # Wait for worker to process
    await asyncio.sleep(2)
    
    # Verify execution stopped
    execution = await db.executions.get(exec_id)
    assert execution.status == "cancelled"
    
    # Verify steps 4-10 never ran
    steps = await db.execution_steps.find_by_execution(exec_id)
    completed_steps = [s for s in steps if s.status == "succeeded"]
    assert len(completed_steps) <= 3  # Only steps 1-3 completed

def test_cancellation_releases_mutex():
    """Mutex released when execution cancelled"""
    # Start execution with mutex
    exec_id = await executor.execute(plan_with_mutex, context)
    
    # Verify lock acquired
    lock = await mutex_manager.check_lock_status(
        tenant_id=tenant_id,
        target_ref="server-01",
        action="deploy"
    )
    assert lock == exec_id
    
    # Cancel
    await cancellation_manager.request_cancellation(exec_id, user_id, "Test")
    
    # Verify lock released
    lock = await mutex_manager.check_lock_status(
        tenant_id=tenant_id,
        target_ref="server-01",
        action="deploy"
    )
    assert lock is None
```

---

## ⏱️ 6. Timeout (Prevent Runaway Executions)

### Problem

**Executions run forever:**
- Worker starts "Check disk space on server-01"
- Server is down, SSH hangs indefinitely
- Worker stuck forever
- Queue backs up ❌

### Solution

**SLA-based timeout enforcement:**

```python
# Execution-level timeout
result = await timeout_manager.execute_with_timeout(
    execution_engine.execute_plan(plan, context),
    timeout_ms=timeout_manager.get_execution_timeout(sla_class),
    execution_id=exec_id
)

# Step-level timeout
result = await timeout_manager.execute_with_timeout(
    execute_step(step),
    timeout_ms=timeout_manager.get_step_timeout(sla_class),
    execution_id=exec_id,
    step_id=step.id
)
```

### Key Features

✅ **SLA-based timeouts** - Fast/medium/long operations have different limits  
✅ **Execution-level timeout** - Entire execution times out  
✅ **Step-level timeout** - Individual steps time out  
✅ **Timeout recording** - Timed-out flag set in database  

### Timeout Configuration

| SLA Class | Execution Timeout | Step Timeout |
|-----------|-------------------|--------------|
| Fast | 10 seconds | 5 seconds |
| Medium | 30 seconds | 15 seconds |
| Long | 10 minutes | 2 minutes |

### Implementation

**File**: `pipeline/stages/stage_e/timeout_manager.py`

```python
class TimeoutManager:
    # Timeout configuration by SLA class
    SLA_TIMEOUTS = {
        "fast": {
            "execution_timeout_ms": 10_000,   # 10 seconds
            "step_timeout_ms": 5_000          # 5 seconds
        },
        "medium": {
            "execution_timeout_ms": 30_000,   # 30 seconds
            "step_timeout_ms": 15_000         # 15 seconds
        },
        "long": {
            "execution_timeout_ms": 600_000,  # 10 minutes
            "step_timeout_ms": 120_000        # 2 minutes
        }
    }
    
    async def execute_with_timeout(
        self,
        coro,
        timeout_ms: int,
        execution_id: str,
        step_id: Optional[str] = None
    ):
        """
        Execute coroutine with timeout enforcement.
        
        Raises asyncio.TimeoutError if timeout exceeded.
        """
        timeout_seconds = timeout_ms / 1000.0
        
        try:
            result = await asyncio.wait_for(coro, timeout=timeout_seconds)
            return result
        except asyncio.TimeoutError:
            logger.error(
                "Execution timed out",
                execution_id=execution_id,
                step_id=step_id,
                timeout_ms=timeout_ms
            )
            
            # Mark as timed out in database
            if step_id:
                await self.db.execution_steps.update(
                    step_id,
                    timed_out=True,
                    status="failed",
                    error_class="TimeoutError",
                    error_message=f"Step exceeded timeout of {timeout_ms}ms"
                )
            else:
                await self.db.executions.update(
                    execution_id,
                    timed_out=True,
                    status="failed",
                    error_class="TimeoutError",
                    error_message=f"Execution exceeded timeout of {timeout_ms}ms"
                )
            
            raise
```

### Test Cases

```python
def test_timeout_enforced_on_slow_execution():
    """Slow execution times out"""
    plan = create_slow_plan(duration=20)  # 20 seconds
    context = create_context(sla_class="fast")  # 10 second timeout
    
    with pytest.raises(asyncio.TimeoutError):
        await executor.execute(plan, context)
    
    # Verify timeout recorded
    execution = await db.executions.get(execution_id)
    assert execution.timed_out == True
    assert execution.status == "failed"
    assert "TimeoutError" in execution.error_class

def test_timeout_per_step():
    """Individual steps time out"""
    plan = create_plan_with_slow_step(step_duration=10)  # 10 seconds
    context = create_context(sla_class="fast")  # 5 second step timeout
    
    result = await executor.execute(plan, context)
    
    # Verify step timed out
    steps = await db.execution_steps.find_by_execution(result.execution_id)
    slow_step = steps[0]
    assert slow_step.timed_out == True
    assert slow_step.status == "failed"
```

---

## 🎭 7. Log Masking (Automatic Secret Redaction)

### Problem

**Secrets leak in structured logs:**
```json
{
  "message": "Execution failed",
  "execution_id": "exec-123",
  "error": "SSH authentication failed",
  "credentials": {
    "username": "admin",
    "password": "P@ssw0rd123",
    "private_key": "-----BEGIN RSA PRIVATE KEY-----..."
  }
}
```

### Solution

**Automatic masking filter:**

```json
{
  "message": "Execution failed",
  "execution_id": "exec-123",
  "error": "SSH authentication failed",
  "credentials": {
    "username": "admin",
    "password": "***REDACTED***",
    "private_key": "***REDACTED***"
  }
}
```

### Key Features

✅ **Sink-level enforcement** - Masking at logger handler (not call sites)  
✅ **Automatic filtering** - No manual masking required  
✅ **Recursive masking** - Handles nested dictionaries  
✅ **Pattern-based** - Matches password, token, key, secret, etc.  
✅ **JSON-aware** - Parses JSON strings and masks fields  
✅ **Unit tested** - Feeds known secret-shaped payloads and asserts redaction  

### Denylist Patterns

```python
SENSITIVE_PATTERNS = [
    r'password',
    r'passwd',
    r'token',
    r'api[_-]?key',
    r'secret',
    r'credential',
    r'private[_-]?key',
    r'access[_-]?key',
    r'auth',
    r'bearer',
    r'session',
]
```

### Integration (Sink-Level Enforcement)

**Logging Handler** (not call sites):

```python
# File: pipeline/logging/masking_handler.py

import logging
import json
from pipeline.stages.stage_e.safety.log_masking import log_masker

class MaskingHandler(logging.Handler):
    """
    Logging handler that masks sensitive fields at sink level.
    
    This ensures ALL logs are masked, even if developers forget
    to manually redact secrets at call sites.
    """
    
    def __init__(self, base_handler: logging.Handler):
        super().__init__()
        self.base_handler = base_handler
    
    def emit(self, record: logging.LogRecord):
        """Mask sensitive fields before emitting to base handler."""
        # Mask message
        if isinstance(record.msg, str):
            record.msg = log_masker.mask_string(record.msg)
        
        # Mask args
        if record.args:
            record.args = tuple(
                log_masker.mask_value(arg) for arg in record.args
            )
        
        # Mask extra fields (structured logging)
        if hasattr(record, 'extra') and isinstance(record.extra, dict):
            record.extra = log_masker.mask_dict(record.extra)
        
        # Mask exception info
        if record.exc_info:
            # Mask exception message
            exc_type, exc_value, exc_tb = record.exc_info
            if exc_value:
                exc_value.args = tuple(
                    log_masker.mask_value(arg) for arg in exc_value.args
                )
        
        # Emit to base handler
        self.base_handler.emit(record)

# Configure logging with masking handler
def setup_logging():
    """Setup logging with automatic secret masking."""
    # Base handler (stdout)
    base_handler = logging.StreamHandler()
    base_handler.setFormatter(
        logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    )
    
    # Wrap with masking handler
    masking_handler = MaskingHandler(base_handler)
    
    # Add to root logger
    root_logger = logging.getLogger()
    root_logger.addHandler(masking_handler)
    root_logger.setLevel(logging.INFO)
```

### Test Cases (Unit Tests for Redaction)

```python
# File: tests/test_log_masking.py

import logging
from pipeline.logging.masking_handler import MaskingHandler, setup_logging

def test_log_masking_recursive():
    """Nested sensitive fields masked"""
    data = {
        "user": "admin",
        "auth": {
            "password": "secret123",
            "api_key": "key-abc-123"
        },
        "metadata": {
            "nested": {
                "token": "bearer-xyz"
            }
        }
    }
    
    masked = log_masker.mask_dict(data)
    
    assert masked["user"] == "admin"
    assert masked["auth"]["password"] == "***REDACTED***"
    assert masked["auth"]["api_key"] == "***REDACTED***"
    assert masked["metadata"]["nested"]["token"] == "***REDACTED***"

def test_log_masking_at_sink_level():
    """
    Feed known secret-shaped payloads to logging and assert redaction.
    
    This tests that masking happens at sink level (handler), not call sites.
    """
    # Setup logging with masking handler
    setup_logging()
    logger = logging.getLogger("test")
    
    # Capture log output
    import io
    log_stream = io.StringIO()
    handler = logging.StreamHandler(log_stream)
    logger.addHandler(handler)
    
    # Log message with secrets (developer forgot to mask!)
    logger.info(
        "Execution failed",
        extra={
            "execution_id": "exec-123",
            "credentials": {
                "password": "P@ssw0rd123",
                "api_key": "key-abc-123",
                "token": "bearer-xyz-789"
            }
        }
    )
    
    # Verify secrets were masked at sink level
    log_output = log_stream.getvalue()
    assert "P@ssw0rd123" not in log_output  # Password masked
    assert "key-abc-123" not in log_output  # API key masked
    assert "bearer-xyz-789" not in log_output  # Token masked
    assert "***REDACTED***" in log_output  # Redaction marker present
    assert "exec-123" in log_output  # Non-sensitive data preserved

def test_log_masking_exception_messages():
    """Exception messages containing secrets are masked."""
    setup_logging()
    logger = logging.getLogger("test")
    
    # Capture log output
    import io
    log_stream = io.StringIO()
    handler = logging.StreamHandler(log_stream)
    logger.addHandler(handler)
    
    # Log exception with secret in message
    try:
        raise ValueError("Authentication failed with password: P@ssw0rd123")
    except ValueError:
        logger.exception("Error occurred")
    
    # Verify secret masked in exception message
    log_output = log_stream.getvalue()
    assert "P@ssw0rd123" not in log_output
    assert "***REDACTED***" in log_output
```

---

## 📊 Safety Metrics

### Idempotency Violations

**Metric**: `idempotency_violations_total`  
**Alert**: Any violation detected  
**Query**: Count executions with duplicate idempotency_key

### Mutex Conflicts

**Metric**: `mutex_conflicts_total`  
**Alert**: >10 conflicts/hour  
**Query**: Count ResourceBusyError exceptions

### RBAC Violations

**Metric**: `rbac_violations_total`  
**Alert**: Any violation detected  
**Query**: Count PermissionError exceptions

### Secret Leaks

**Metric**: `secret_leaks_total`  
**Alert**: Any leak detected  
**Query**: Scan logs for unmasked sensitive patterns

### Cancellation Rate

**Metric**: `execution_cancellation_rate`  
**Alert**: >20% cancellation rate  
**Query**: `cancelled / total * 100`

### Timeout Rate

**Metric**: `execution_timeout_rate`  
**Alert**: >10% timeout rate  
**Query**: `timed_out / total * 100`

---

## 🔍 Debugging Guide

### Idempotency Issues

**Symptom**: Duplicate executions created

**Debug**:
```sql
-- Find duplicate idempotency keys
SELECT idempotency_key, COUNT(*) as count
FROM executions
WHERE tenant_id = 'tenant-123'
GROUP BY idempotency_key
HAVING COUNT(*) > 1;
```

**Fix**: Check canonical JSON generation (sorted keys, no whitespace)

---

### Mutex Issues

**Symptom**: "Resource is locked" errors

**Debug**:
```sql
-- Find active locks
SELECT * FROM execution_locks
WHERE expires_at > NOW()
ORDER BY acquired_at ASC;
```

**Fix**: Run stale lock reaper, check lock TTL

---

### RBAC Issues

**Symptom**: PermissionError exceptions

**Debug**:
```python
# Check actor permissions
actor = await db.users.get(actor_id)
print(f"Actor roles: {actor.roles}")
print(f"Actor permissions: {actor.permissions}")

# Check required permission
required = rbac_validator._get_required_permission(action)
print(f"Required permission: {required}")
```

**Fix**: Grant missing permissions to actor

---

### Secret Leaks

**Symptom**: Credentials in logs

**Debug**:
```bash
# Search logs for sensitive patterns
grep -E "(password|token|key|secret)" /var/log/opsconductor/*.log
```

**Fix**: Verify log masking filter enabled, check denylist patterns

---

## 📚 Related Documentation

- **Implementation Plan**: See `PHASE_7_IMPLEMENTATION_PLAN.md`
- **Database Schema**: See `PHASE_7_DATABASE_SCHEMA.md`

---

**Document Version**: 1.0  
**Last Updated**: 2025-01-XX  
**Status**: Ready for Implementation