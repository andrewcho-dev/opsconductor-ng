"""
Phase 7: Progress Tracking & Monitoring Tests
Tests for progress tracker, metrics collector, event emitter, and monitoring service
"""

import asyncio
import pytest
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

from execution.models import ExecutionStatus, SLAClass, ExecutionMode
from execution.monitoring import (
    ProgressTracker,
    ExecutionProgress,
    MetricsCollector,
    ExecutionMetrics,
    EventEmitter,
    ExecutionEvent,
    EventType,
    MonitoringService,
    HealthStatus,
)


# ============================================================================
# FIXTURES
# ============================================================================

@pytest.fixture
def mock_repository():
    """Mock execution repository"""
    repo = AsyncMock()
    return repo


@pytest.fixture
def progress_tracker(mock_repository):
    """Progress tracker instance"""
    return ProgressTracker(mock_repository)


@pytest.fixture
def metrics_collector(mock_repository):
    """Metrics collector instance"""
    return MetricsCollector(mock_repository)


@pytest.fixture
def event_emitter():
    """Event emitter instance"""
    return EventEmitter(buffer_size=100)


@pytest.fixture
def monitoring_service(mock_repository, metrics_collector, progress_tracker, event_emitter):
    """Monitoring service instance"""
    return MonitoringService(
        repository=mock_repository,
        metrics_collector=metrics_collector,
        progress_tracker=progress_tracker,
        event_emitter=event_emitter,
    )


# ============================================================================
# PROGRESS TRACKER TESTS
# ============================================================================

@pytest.mark.asyncio
async def test_progress_tracker_get_progress(progress_tracker, mock_repository):
    """Test getting execution progress"""
    execution_id = uuid4()
    
    # Mock execution
    mock_execution = MagicMock()
    mock_execution.execution_id = execution_id
    mock_execution.status = ExecutionStatus.RUNNING
    mock_execution.started_at = datetime.utcnow() - timedelta(minutes=5)
    mock_execution.completed_at = None
    
    # Mock steps
    mock_steps = []
    for i in range(5):
        step = MagicMock()
        step.step_id = uuid4()
        step.step_index = i
        step.step_name = f"Step {i}"
        step.status = ExecutionStatus.COMPLETED if i < 3 else ExecutionStatus.RUNNING if i == 3 else ExecutionStatus.QUEUED
        step.started_at = datetime.utcnow() if i <= 3 else None
        step.completed_at = datetime.utcnow() if i < 3 else None
        step.duration_ms = 1000 if i < 3 else None
        step.error_message = None
        mock_steps.append(step)
    
    mock_repository.get_execution.return_value = mock_execution
    mock_repository.get_execution_steps.return_value = mock_steps
    
    # Get progress
    progress = await progress_tracker.get_progress(execution_id)
    
    assert progress is not None
    assert progress.execution_id == execution_id
    assert progress.status == ExecutionStatus.RUNNING
    assert progress.total_steps == 5
    assert progress.completed_steps == 3
    assert progress.running_steps == 1
    assert progress.pending_steps == 1
    assert progress.progress_percent == 60  # 3/5 = 60%
    assert progress.current_step is not None
    assert progress.current_step.step_index == 3


@pytest.mark.asyncio
async def test_progress_tracker_update_step_progress(progress_tracker, mock_repository):
    """Test updating step progress"""
    execution_id = uuid4()
    step_id = uuid4()
    
    mock_repository.update_step.return_value = True
    
    # Update step
    success = await progress_tracker.update_step_progress(
        execution_id=execution_id,
        step_id=step_id,
        status=ExecutionStatus.COMPLETED,
        progress_percent=100,
    )
    
    assert success is True
    mock_repository.update_step.assert_called_once()


@pytest.mark.asyncio
async def test_progress_tracker_mark_step_started(progress_tracker, mock_repository):
    """Test marking step as started"""
    execution_id = uuid4()
    step_id = uuid4()
    
    mock_repository.update_step.return_value = True
    
    # Mark started
    success = await progress_tracker.mark_step_started(execution_id, step_id)
    
    assert success is True
    mock_repository.update_step.assert_called_once()
    call_args = mock_repository.update_step.call_args[0]
    assert call_args[0] == step_id
    assert call_args[1]["status"] == ExecutionStatus.RUNNING


@pytest.mark.asyncio
async def test_progress_tracker_mark_step_completed(progress_tracker, mock_repository):
    """Test marking step as completed"""
    execution_id = uuid4()
    step_id = uuid4()
    
    mock_repository.update_step.return_value = True
    
    # Mark completed
    success = await progress_tracker.mark_step_completed(
        execution_id=execution_id,
        step_id=step_id,
        status=ExecutionStatus.COMPLETED,
        duration_ms=1500,
        output_data={"result": "success"},
    )
    
    assert success is True
    mock_repository.update_step.assert_called_once()


@pytest.mark.asyncio
async def test_progress_tracker_get_active_executions(progress_tracker, mock_repository):
    """Test getting active executions"""
    # Mock executions
    mock_executions = []
    for i in range(3):
        execution = MagicMock()
        execution.execution_id = uuid4()
        execution.status = ExecutionStatus.RUNNING
        execution.started_at = datetime.utcnow()
        execution.completed_at = None
        mock_executions.append(execution)
    
    mock_repository.list_executions.return_value = mock_executions
    mock_repository.get_execution.side_effect = mock_executions
    mock_repository.get_execution_steps.return_value = []
    
    # Get active executions
    active = await progress_tracker.get_active_executions()
    
    assert len(active) == 3


# ============================================================================
# METRICS COLLECTOR TESTS
# ============================================================================

@pytest.mark.asyncio
async def test_metrics_collector_collect_metrics(metrics_collector, mock_repository):
    """Test collecting execution metrics"""
    # Mock executions
    mock_executions = []
    for i in range(10):
        execution = MagicMock()
        execution.execution_id = uuid4()
        execution.status = ExecutionStatus.COMPLETED if i < 7 else ExecutionStatus.FAILED
        execution.started_at = datetime.utcnow() - timedelta(minutes=10)
        execution.completed_at = datetime.utcnow() - timedelta(minutes=5)
        execution.queued_at = datetime.utcnow() - timedelta(minutes=11)
        mock_executions.append(execution)
    
    mock_repository.list_executions.return_value = mock_executions
    mock_repository.get_execution_steps.return_value = []
    
    # Collect metrics
    metrics = await metrics_collector.collect_metrics()
    
    assert metrics.total_executions == 10
    assert metrics.completed_executions == 7
    assert metrics.failed_executions == 3
    assert metrics.success_rate == 70.0
    assert metrics.avg_duration_ms is not None


@pytest.mark.asyncio
async def test_metrics_collector_collect_step_metrics(metrics_collector, mock_repository):
    """Test collecting step-level metrics"""
    # Mock executions
    mock_execution = MagicMock()
    mock_execution.execution_id = uuid4()
    
    # Mock steps
    mock_steps = []
    for i in range(5):
        step = MagicMock()
        step.step_id = uuid4()
        step.step_type = "ssh_command" if i < 3 else "api_call"
        step.status = ExecutionStatus.COMPLETED if i < 4 else ExecutionStatus.FAILED
        step.duration_ms = 1000 + (i * 100)
        mock_steps.append(step)
    
    mock_repository.list_executions.return_value = [mock_execution]
    mock_repository.get_execution_steps.return_value = mock_steps
    
    # Collect step metrics
    step_metrics = await metrics_collector.collect_step_metrics()
    
    assert len(step_metrics) == 2  # ssh_command and api_call
    ssh_metrics = next(m for m in step_metrics if m.step_type == "ssh_command")
    assert ssh_metrics.total_executions == 3
    assert ssh_metrics.success_count == 3


@pytest.mark.asyncio
async def test_metrics_collector_collect_system_metrics(metrics_collector, mock_repository):
    """Test collecting system metrics"""
    # Mock active executions
    mock_repository.list_executions.return_value = [MagicMock() for _ in range(5)]
    
    # Collect system metrics
    metrics = await metrics_collector.collect_system_metrics()
    
    assert metrics.active_executions == 5
    assert metrics.timestamp is not None


@pytest.mark.asyncio
async def test_metrics_collector_get_metrics_summary(metrics_collector, mock_repository):
    """Test getting metrics summary"""
    mock_repository.list_executions.return_value = []
    mock_repository.get_execution_steps.return_value = []
    
    # Get summary
    summary = await metrics_collector.get_metrics_summary()
    
    assert "last_hour" in summary
    assert "last_24h" in summary
    assert "last_7d" in summary
    assert "step_metrics" in summary
    assert "system_metrics" in summary


# ============================================================================
# EVENT EMITTER TESTS
# ============================================================================

@pytest.mark.asyncio
async def test_event_emitter_emit(event_emitter):
    """Test emitting events"""
    execution_id = uuid4()
    
    # Emit event
    event = ExecutionEvent(
        event_type=EventType.EXECUTION_STARTED,
        execution_id=execution_id,
        data={"test": "data"},
    )
    await event_emitter.emit(event)
    
    # Check buffer
    events = await event_emitter.get_events()
    assert len(events) == 1
    assert events[0].event_type == EventType.EXECUTION_STARTED


@pytest.mark.asyncio
async def test_event_emitter_subscribe(event_emitter):
    """Test subscribing to events"""
    execution_id = uuid4()
    received_events = []
    
    # Subscribe
    async def callback(event: ExecutionEvent):
        received_events.append(event)
    
    await event_emitter.subscribe(callback, execution_id=execution_id)
    
    # Emit event
    await event_emitter.emit_execution_started(execution_id, test="data")
    
    # Wait for callback
    await asyncio.sleep(0.1)
    
    assert len(received_events) == 1
    assert received_events[0].execution_id == execution_id


@pytest.mark.asyncio
async def test_event_emitter_subscribe_by_type(event_emitter):
    """Test subscribing by event type"""
    received_events = []
    
    # Subscribe to specific event type
    async def callback(event: ExecutionEvent):
        received_events.append(event)
    
    await event_emitter.subscribe(callback, event_type=EventType.STEP_COMPLETED)
    
    # Emit different events
    await event_emitter.emit_step_started(uuid4(), uuid4(), "test")
    await event_emitter.emit_step_completed(uuid4(), uuid4(), 1000)
    
    # Wait for callbacks
    await asyncio.sleep(0.1)
    
    # Should only receive STEP_COMPLETED
    assert len(received_events) == 1
    assert received_events[0].event_type == EventType.STEP_COMPLETED


@pytest.mark.asyncio
async def test_event_emitter_unsubscribe(event_emitter):
    """Test unsubscribing from events"""
    execution_id = uuid4()
    received_events = []
    
    async def callback(event: ExecutionEvent):
        received_events.append(event)
    
    # Subscribe and unsubscribe
    await event_emitter.subscribe(callback, execution_id=execution_id)
    await event_emitter.unsubscribe(callback, execution_id=execution_id)
    
    # Emit event
    await event_emitter.emit_execution_started(execution_id)
    await asyncio.sleep(0.1)
    
    # Should not receive event
    assert len(received_events) == 0


@pytest.mark.asyncio
async def test_event_emitter_get_events_filtered(event_emitter):
    """Test getting filtered events"""
    execution_id_1 = uuid4()
    execution_id_2 = uuid4()
    
    # Emit events
    await event_emitter.emit_execution_started(execution_id_1)
    await event_emitter.emit_execution_started(execution_id_2)
    await event_emitter.emit_execution_completed(execution_id_1, 1000)
    
    # Get events for execution_id_1
    events = await event_emitter.get_events(execution_id=execution_id_1)
    assert len(events) == 2
    assert all(e.execution_id == execution_id_1 for e in events)
    
    # Get events by type
    events = await event_emitter.get_events(event_type=EventType.EXECUTION_STARTED)
    assert len(events) == 2
    assert all(e.event_type == EventType.EXECUTION_STARTED for e in events)


# ============================================================================
# MONITORING SERVICE TESTS
# ============================================================================

@pytest.mark.asyncio
async def test_monitoring_service_check_health(monitoring_service, mock_repository):
    """Test health check"""
    mock_repository.list_executions.return_value = []
    mock_repository.get_execution_steps.return_value = []
    
    # Check health
    health = await monitoring_service.check_health()
    
    assert health.status in [HealthStatus.HEALTHY, HealthStatus.DEGRADED, HealthStatus.UNHEALTHY]
    assert len(health.components) > 0


@pytest.mark.asyncio
async def test_monitoring_service_check_sla_violations(monitoring_service, mock_repository):
    """Test SLA violation detection"""
    # Mock executions with high timeout rate
    mock_executions = []
    for i in range(10):
        execution = MagicMock()
        execution.execution_id = uuid4()
        execution.status = ExecutionStatus.TIMEOUT if i < 3 else ExecutionStatus.COMPLETED
        execution.started_at = datetime.utcnow() - timedelta(minutes=10)
        execution.completed_at = datetime.utcnow() - timedelta(minutes=5)
        execution.queued_at = datetime.utcnow() - timedelta(minutes=11)
        mock_executions.append(execution)
    
    mock_repository.list_executions.return_value = mock_executions
    mock_repository.get_execution_steps.return_value = []
    
    # Check violations
    alerts = await monitoring_service.check_sla_violations()
    
    # Should have timeout alert (30% > 10% threshold)
    assert len(alerts) > 0
    assert any("Timeout" in alert.title for alert in alerts)


@pytest.mark.asyncio
async def test_monitoring_service_get_alerts(monitoring_service):
    """Test getting alerts"""
    # Add some alerts
    from execution.monitoring.monitoring_service import Alert
    alert1 = Alert(
        alert_id="test1",
        severity="warning",
        title="Test Alert 1",
        message="Test message 1",
    )
    alert2 = Alert(
        alert_id="test2",
        severity="error",
        title="Test Alert 2",
        message="Test message 2",
    )
    
    await monitoring_service._add_alert(alert1)
    await monitoring_service._add_alert(alert2)
    
    # Get all alerts
    alerts = await monitoring_service.get_alerts()
    assert len(alerts) == 2
    
    # Get by severity
    error_alerts = await monitoring_service.get_alerts(severity="error")
    assert len(error_alerts) == 1
    assert error_alerts[0].severity == "error"


@pytest.mark.asyncio
async def test_monitoring_service_start_stop(monitoring_service):
    """Test starting and stopping monitoring service"""
    # Start service
    await monitoring_service.start()
    assert monitoring_service._health_check_task is not None
    
    # Stop service
    await monitoring_service.stop()
    assert monitoring_service._health_check_task is None


# ============================================================================
# INTEGRATION TESTS
# ============================================================================

@pytest.mark.asyncio
async def test_monitoring_integration(mock_repository):
    """Test full monitoring integration"""
    # Create all components
    progress_tracker = ProgressTracker(mock_repository)
    metrics_collector = MetricsCollector(mock_repository)
    event_emitter = EventEmitter()
    monitoring_service = MonitoringService(
        repository=mock_repository,
        metrics_collector=metrics_collector,
        progress_tracker=progress_tracker,
        event_emitter=event_emitter,
    )
    
    execution_id = uuid4()
    
    # Mock execution
    mock_execution = MagicMock()
    mock_execution.execution_id = execution_id
    mock_execution.status = ExecutionStatus.RUNNING
    mock_execution.started_at = datetime.utcnow()
    mock_execution.completed_at = None
    
    mock_repository.get_execution.return_value = mock_execution
    mock_repository.get_execution_steps.return_value = []
    mock_repository.list_executions.return_value = [mock_execution]
    
    # Track progress
    progress = await progress_tracker.get_progress(execution_id)
    assert progress is not None
    
    # Collect metrics
    metrics = await metrics_collector.collect_metrics()
    assert metrics is not None
    
    # Emit event
    await event_emitter.emit_execution_started(execution_id)
    events = await event_emitter.get_events()
    assert len(events) == 1
    
    # Check health
    health = await monitoring_service.check_health()
    assert health is not None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])