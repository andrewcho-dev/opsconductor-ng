#!/usr/bin/env python3
"""
Unit tests for tools_upsert.py

Tests YAML loading, validation, and upsert logic without requiring database.
"""

import asyncio
import sys
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from tools.tools_upsert import load_yaml_tool, upsert_tool


@pytest.mark.asyncio
async def test_load_yaml_tool_valid(tmp_path):
    """Test loading a valid YAML tool definition."""
    yaml_file = tmp_path / "test_tool.yaml"
    yaml_file.write_text("""
key: test.tool
name: Test Tool
short_desc: A test tool for testing purposes.
platform:
  - linux
  - docker
tags:
  - test
  - diagnostics
meta:
  cmd: "echo test"
""")
    
    tool = await load_yaml_tool(str(yaml_file))
    
    assert tool is not None
    assert tool['key'] == 'test.tool'
    assert tool['name'] == 'Test Tool'
    assert tool['short_desc'] == 'A test tool for testing purposes.'
    assert tool['platform'] == ['linux', 'docker']
    assert tool['tags'] == ['test', 'diagnostics']
    assert tool['meta'] == {'cmd': 'echo test'}


@pytest.mark.asyncio
async def test_load_yaml_tool_missing_required_field(tmp_path):
    """Test loading YAML with missing required field."""
    yaml_file = tmp_path / "invalid_tool.yaml"
    yaml_file.write_text("""
key: test.tool
name: Test Tool
# Missing short_desc
platform:
  - linux
""")
    
    tool = await load_yaml_tool(str(yaml_file))
    
    assert tool is None


@pytest.mark.asyncio
async def test_load_yaml_tool_truncates_long_desc(tmp_path):
    """Test that short_desc is truncated to 160 characters."""
    long_desc = "A" * 200
    yaml_file = tmp_path / "long_desc.yaml"
    yaml_file.write_text(f"""
key: test.tool
name: Test Tool
short_desc: {long_desc}
""")
    
    tool = await load_yaml_tool(str(yaml_file))
    
    assert tool is not None
    assert len(tool['short_desc']) == 160
    assert tool['short_desc'] == "A" * 160


@pytest.mark.asyncio
async def test_load_yaml_tool_defaults(tmp_path):
    """Test that optional fields get default values."""
    yaml_file = tmp_path / "minimal_tool.yaml"
    yaml_file.write_text("""
key: test.tool
name: Test Tool
short_desc: Minimal tool definition.
""")
    
    tool = await load_yaml_tool(str(yaml_file))
    
    assert tool is not None
    assert tool['platform'] == []
    assert tool['tags'] == []
    assert tool['meta'] == {}


@pytest.mark.asyncio
async def test_upsert_tool_dry_run():
    """Test upsert in dry-run mode."""
    mock_conn = MagicMock()
    mock_provider = MagicMock()
    mock_provider.embed = AsyncMock(return_value=[0.1] * 128)
    
    tool = {
        'key': 'test.tool',
        'name': 'Test Tool',
        'short_desc': 'Test description',
        'platform': ['linux'],
        'tags': ['test'],
        'meta': {'cmd': 'echo test'}
    }
    
    result = await upsert_tool(mock_conn, tool, mock_provider, dry_run=True)
    
    assert result is True
    # Verify embedding was generated
    mock_provider.embed.assert_called_once_with('test.tool :: Test description')
    # Verify no database call was made
    mock_conn.execute.assert_not_called()


@pytest.mark.asyncio
async def test_upsert_tool_actual():
    """Test actual upsert (mocked database)."""
    mock_conn = AsyncMock()
    mock_conn.execute = AsyncMock()
    
    mock_provider = MagicMock()
    mock_provider.embed = AsyncMock(return_value=[0.1, 0.2, 0.3] + [0.0] * 125)
    
    tool = {
        'key': 'test.tool',
        'name': 'Test Tool',
        'short_desc': 'Test description',
        'platform': ['linux'],
        'tags': ['test'],
        'meta': {'cmd': 'echo test'}
    }
    
    result = await upsert_tool(mock_conn, tool, mock_provider, dry_run=False)
    
    assert result is True
    # Verify embedding was generated
    mock_provider.embed.assert_called_once_with('test.tool :: Test description')
    # Verify database call was made
    mock_conn.execute.assert_called_once()
    
    # Verify SQL query structure
    call_args = mock_conn.execute.call_args
    query = call_args[0][0]
    assert 'INSERT INTO tool' in query
    assert 'ON CONFLICT (key) DO UPDATE' in query
    assert 'CAST($7 AS vector(128))' in query
    
    # Verify parameters
    params = call_args[0][1:]
    assert params[0] == 'test.tool'
    assert params[1] == 'Test Tool'
    assert params[2] == 'Test description'
    assert params[3] == ['linux']
    assert params[4] == ['test']
    assert params[5] == {'cmd': 'echo test'}
    # Vector literal should be a string
    assert params[6].startswith('[0.1,0.2,0.3')


@pytest.mark.asyncio
async def test_upsert_tool_handles_error():
    """Test that upsert handles database errors gracefully."""
    mock_conn = AsyncMock()
    mock_conn.execute = AsyncMock(side_effect=Exception("Database error"))
    
    mock_provider = MagicMock()
    mock_provider.embed = AsyncMock(return_value=[0.1] * 128)
    
    tool = {
        'key': 'test.tool',
        'name': 'Test Tool',
        'short_desc': 'Test description',
        'platform': [],
        'tags': [],
        'meta': {}
    }
    
    result = await upsert_tool(mock_conn, tool, mock_provider, dry_run=False)
    
    assert result is False


if __name__ == '__main__':
    pytest.main([__file__, '-v'])