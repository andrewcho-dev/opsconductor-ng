"""Tests for shared.logging module."""

import json
import sys
from io import StringIO

import pytest
from shared.logging import json_log


def test_json_log_basic(capsys):
    """Test basic JSON log output."""
    json_log("hello", trace_id="t1")
    
    captured = capsys.readouterr()
    log_entry = json.loads(captured.out.strip())
    
    assert log_entry["msg"] == "hello"
    assert log_entry["trace_id"] == "t1"
    assert "ts" in log_entry
    assert "level" in log_entry


def test_json_log_contains_required_fields(capsys):
    """Test that JSON log contains all required fields."""
    json_log("test message", trace_id="trace123")
    
    captured = capsys.readouterr()
    log_entry = json.loads(captured.out.strip())
    
    assert "ts" in log_entry
    assert "level" in log_entry
    assert "msg" in log_entry
    assert log_entry["msg"] == "test message"
    assert log_entry["trace_id"] == "trace123"


def test_json_log_custom_level(capsys):
    """Test JSON log with custom level."""
    json_log("error message", level="ERROR", trace_id="t2")
    
    captured = capsys.readouterr()
    log_entry = json.loads(captured.out.strip())
    
    assert log_entry["level"] == "ERROR"
    assert log_entry["msg"] == "error message"


def test_json_log_multiple_fields(capsys):
    """Test JSON log with multiple custom fields."""
    json_log("complex log", trace_id="t3", user_id="u1", action="login", success=True)
    
    captured = capsys.readouterr()
    log_entry = json.loads(captured.out.strip())
    
    assert log_entry["msg"] == "complex log"
    assert log_entry["trace_id"] == "t3"
    assert log_entry["user_id"] == "u1"
    assert log_entry["action"] == "login"
    assert log_entry["success"] is True


def test_json_log_default_level(capsys):
    """Test that default level is INFO."""
    json_log("default level test")
    
    captured = capsys.readouterr()
    log_entry = json.loads(captured.out.strip())
    
    assert log_entry["level"] == "INFO"