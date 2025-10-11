"""Tests for shared.ids module."""

import pytest
from shared.ids import new_trace_id, new_run_id, new_plan_id


def test_trace_id_length():
    """Test that trace IDs are exactly 32 characters."""
    trace_id = new_trace_id()
    assert len(trace_id) == 32


def test_trace_id_is_hex():
    """Test that trace IDs are valid hexadecimal."""
    trace_id = new_trace_id()
    assert all(c in '0123456789abcdef' for c in trace_id)


def test_trace_id_uniqueness():
    """Test that trace IDs are unique."""
    ids = {new_trace_id() for _ in range(100)}
    assert len(ids) == 100


def test_run_id_format():
    """Test that run IDs have correct format."""
    run_id = new_run_id()
    assert run_id.startswith("run_")
    assert len(run_id) == 16  # "run_" (4) + 12 hex chars


def test_run_id_uniqueness():
    """Test that run IDs are unique."""
    ids = {new_run_id() for _ in range(100)}
    assert len(ids) == 100


def test_plan_id_format():
    """Test that plan IDs have correct format."""
    plan_id = new_plan_id()
    assert plan_id.startswith("plan_")
    assert len(plan_id) == 17  # "plan_" (5) + 12 hex chars


def test_plan_id_uniqueness():
    """Test that plan IDs are unique."""
    ids = {new_plan_id() for _ in range(100)}
    assert len(ids) == 100