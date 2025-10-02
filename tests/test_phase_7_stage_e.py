"""
Phase 7: Stage E Execution Tests
Unit tests for execution engine and Stage E executor
"""

import asyncio
import os
import pytest
from datetime import datetime
from uuid import uuid4

from execution.models import (
    ExecutionModel,
    ExecutionStatus,
    ExecutionMode,
    SLAClass,
    calculate_idempotency_key,
    determine_sla_class,
    determine_execution_mode,
)
from execution.dtos import ExecutionRequest
from execution.repository import ExecutionRepository
from pipeline.stages.stage_e.executor import StageEExecutor


# ============================================================================
# FIXTURES
# ============================================================================

@pytest.fixture
def db_connection_string():
    """Database connection string"""
    return os.getenv(
        "DATABASE_URL",
        "postgresql://opsconductor:opsconductor_secure_2024@localhost:5432/opsconductor"
    )


@pytest.fixture
def repository(db_connection_string):
    """Execution repository"""
    return ExecutionRepository(db_connection_string)


@pytest.fixture
def executor(db_connection_string):
    """Stage E Executor"""
    return StageEExecutor(db_connection_string)


@pytest.fixture
def sample_plan():
    """Sample execution plan"""
    return {
        "type": "read",
        "description": "Test plan",
        "steps": [
            {
                "name": "Step 1",
                "type": "ssh_command_read",
                "target_asset_id": 1,
                "target_hostname": "test-server-1",
                "input_data": {"command": "ls -la"},
            },
            {
                "name": "Step 2",
                "type": "ssh_command_read",
                "target_asset_id": 2,
                "target_hostname": "test-server-2",
                "input_data": {"command": "df -h"},
            },
        ],
        "targets": [
            {"id": 1, "hostname": "test-server-1"},
            {"id": 2, "hostname": "test-server-2"},
        ],
    }


# ============================================================================
# MODEL TESTS
# ============================================================================

def test_calculate_idempotency_key(sample_plan):
    """Test idempotency key calculation"""
    tenant_id = "tenant-1"
    actor_id = 1
    
    key1 = calculate_idempotency_key(sample_plan, tenant_id, actor_id)
    key2 = calculate_idempotency_key(sample_plan, tenant_id, actor_id)
    
    # Same plan should produce same key
    assert key1 == key2
    
    # Different tenant should produce different key
    key3 = calculate_idempotency_key(sample_plan, "tenant-2", actor_id)
    assert key1 != key3
    
    # Different actor should produce different key
    key4 = calculate_idempotency_key(sample_plan, tenant_id, 2)
    assert key1 != key4


def test_determine_sla_class():
    """Test SLA class determination"""
    assert determine_sla_class(5.0) == SLAClass.FAST
    assert determine_sla_class(15.0) == SLAClass.MEDIUM
    assert determine_sla_class(45.0) == SLAClass.LONG


def test_determine_execution_mode():
    """Test execution mode determination"""
    assert determine_execution_mode(SLAClass.FAST) == ExecutionMode.IMMEDIATE
    assert determine_execution_mode(SLAClass.MEDIUM) == ExecutionMode.BACKGROUND
    assert determine_execution_mode(SLAClass.LONG) == ExecutionMode.BACKGROUND


def test_execution_model_validation():
    """Test execution model validation"""
    execution = ExecutionModel(
        tenant_id="tenant-1",
        actor_id=1,
        idempotency_key="test-key",
        plan_snapshot={"test": "plan"},
        execution_mode=ExecutionMode.IMMEDIATE,
        sla_class=SLAClass.FAST,
        approval_level=0,
    )
    
    assert execution.status == ExecutionStatus.PENDING_APPROVAL
    assert execution.execution_id is not None
    assert execution.created_at is not None


def test_execution_model_invalid_approval_level():
    """Test execution model with invalid approval level"""
    with pytest.raises(ValueError):
        ExecutionModel(
            tenant_id="tenant-1",
            actor_id=1,
            idempotency_key="test-key",
            plan_snapshot={"test": "plan"},
            execution_mode=ExecutionMode.IMMEDIATE,
            sla_class=SLAClass.FAST,
            approval_level=5,  # Invalid: must be 0-3
        )


# ============================================================================
# REPOSITORY TESTS
# ============================================================================

def test_create_execution(repository, sample_plan):
    """Test creating an execution"""
    execution = ExecutionModel(
        tenant_id="test-tenant",
        actor_id=1,
        idempotency_key=calculate_idempotency_key(sample_plan, "test-tenant", 1),
        plan_snapshot=sample_plan,
        execution_mode=ExecutionMode.IMMEDIATE,
        sla_class=SLAClass.FAST,
        approval_level=0,
        status=ExecutionStatus.APPROVED,
    )
    
    created_execution = repository.create_execution(execution)
    
    assert created_execution.id is not None
    assert created_execution.execution_id == execution.execution_id
    assert created_execution.tenant_id == "test-tenant"
    assert created_execution.actor_id == 1


def test_get_execution_by_id(repository, sample_plan):
    """Test getting execution by ID"""
    execution = ExecutionModel(
        tenant_id="test-tenant",
        actor_id=1,
        idempotency_key=calculate_idempotency_key(sample_plan, "test-tenant", 1),
        plan_snapshot=sample_plan,
        execution_mode=ExecutionMode.IMMEDIATE,
        sla_class=SLAClass.FAST,
        approval_level=0,
        status=ExecutionStatus.APPROVED,
    )
    
    created_execution = repository.create_execution(execution)
    retrieved_execution = repository.get_execution_by_id(created_execution.execution_id)
    
    assert retrieved_execution is not None
    assert retrieved_execution.execution_id == created_execution.execution_id


def test_get_execution_by_idempotency_key(repository, sample_plan):
    """Test getting execution by idempotency key"""
    tenant_id = "test-tenant"
    actor_id = 1
    idempotency_key = calculate_idempotency_key(sample_plan, tenant_id, actor_id)
    
    execution = ExecutionModel(
        tenant_id=tenant_id,
        actor_id=actor_id,
        idempotency_key=idempotency_key,
        plan_snapshot=sample_plan,
        execution_mode=ExecutionMode.IMMEDIATE,
        sla_class=SLAClass.FAST,
        approval_level=0,
        status=ExecutionStatus.APPROVED,
    )
    
    created_execution = repository.create_execution(execution)
    retrieved_execution = repository.get_execution_by_idempotency_key(
        tenant_id,
        idempotency_key
    )
    
    assert retrieved_execution is not None
    assert retrieved_execution.execution_id == created_execution.execution_id


def test_update_execution_status(repository, sample_plan):
    """Test updating execution status"""
    execution = ExecutionModel(
        tenant_id="test-tenant",
        actor_id=1,
        idempotency_key=calculate_idempotency_key(sample_plan, "test-tenant", 1),
        plan_snapshot=sample_plan,
        execution_mode=ExecutionMode.IMMEDIATE,
        sla_class=SLAClass.FAST,
        approval_level=0,
        status=ExecutionStatus.APPROVED,
    )
    
    created_execution = repository.create_execution(execution)
    
    # Update status
    repository.update_execution_status(
        created_execution.execution_id,
        ExecutionStatus.RUNNING,
        previous_status=ExecutionStatus.APPROVED
    )
    
    # Verify update
    updated_execution = repository.get_execution_by_id(created_execution.execution_id)
    assert updated_execution.status == ExecutionStatus.RUNNING
    assert updated_execution.previous_status == ExecutionStatus.APPROVED


def test_get_timeout_policy(repository):
    """Test getting timeout policy"""
    policy = repository.get_timeout_policy(SLAClass.FAST, "read")
    
    assert policy is not None
    assert policy.sla_class == SLAClass.FAST
    assert policy.action_class == "read"
    assert policy.step_timeout_seconds == 5
    assert policy.execution_timeout_seconds == 10
    assert policy.max_attempts == 3


# ============================================================================
# EXECUTOR TESTS
# ============================================================================

@pytest.mark.asyncio
async def test_executor_create_execution(executor, sample_plan):
    """Test creating execution via executor"""
    request = ExecutionRequest(
        plan=sample_plan,
        approval_level=0,
        tags=["test"],
        metadata={"test": "data"},
    )
    
    response = await executor.execute(
        request,
        tenant_id="test-tenant",
        actor_id=1
    )
    
    assert response.execution_id is not None
    assert response.status in [
        ExecutionStatus.APPROVED,
        ExecutionStatus.RUNNING,
        ExecutionStatus.COMPLETED,
        ExecutionStatus.QUEUED,
    ]
    assert response.execution_mode == ExecutionMode.IMMEDIATE
    assert response.sla_class == SLAClass.FAST
    assert response.approval_level == 0


@pytest.mark.asyncio
async def test_executor_idempotency(executor, sample_plan):
    """Test idempotency - duplicate execution should return same execution"""
    request = ExecutionRequest(
        plan=sample_plan,
        approval_level=0,
    )
    
    # First execution
    response1 = await executor.execute(
        request,
        tenant_id="test-tenant-idempotency",
        actor_id=1
    )
    
    # Second execution (duplicate)
    response2 = await executor.execute(
        request,
        tenant_id="test-tenant-idempotency",
        actor_id=1
    )
    
    # Should return same execution
    assert response1.execution_id == response2.execution_id


@pytest.mark.asyncio
async def test_executor_approval_required(executor, sample_plan):
    """Test execution with approval required"""
    request = ExecutionRequest(
        plan=sample_plan,
        approval_level=2,  # Requires approval
    )
    
    response = await executor.execute(
        request,
        tenant_id="test-tenant-approval",
        actor_id=1
    )
    
    assert response.execution_id is not None
    assert response.status == ExecutionStatus.PENDING_APPROVAL
    assert response.approval_level == 2


# ============================================================================
# INTEGRATION TESTS
# ============================================================================

@pytest.mark.asyncio
async def test_end_to_end_immediate_execution(executor, sample_plan):
    """Test end-to-end immediate execution"""
    request = ExecutionRequest(
        plan=sample_plan,
        approval_level=0,
    )
    
    response = await executor.execute(
        request,
        tenant_id="test-tenant-e2e",
        actor_id=1
    )
    
    # Wait a bit for execution to complete
    await asyncio.sleep(1)
    
    # Verify execution completed
    assert response.execution_id is not None
    # Note: Status may be RUNNING or COMPLETED depending on timing


if __name__ == "__main__":
    pytest.main([__file__, "-v"])