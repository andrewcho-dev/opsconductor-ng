"""
Unit tests for Tool Registry v2
"""

import pytest
import tempfile
import os
from pathlib import Path
from tool_registry import ToolRegistry


class TestToolRegistry:
    """Test suite for ToolRegistry"""
    
    def test_init_with_default_dirs(self):
        """Test registry initialization with default directories"""
        registry = ToolRegistry()
        assert registry is not None
        assert len(registry.catalog_dirs) >= 0  # May be empty if dirs don't exist
    
    def test_init_with_custom_dirs(self):
        """Test registry initialization with custom directories"""
        with tempfile.TemporaryDirectory() as tmpdir:
            registry = ToolRegistry(catalog_dirs=tmpdir)
            assert tmpdir in registry.catalog_dirs
    
    def test_load_builtin_tools(self):
        """Test that built-in tools are loaded"""
        registry = ToolRegistry(catalog_dirs="/nonexistent")
        
        # Check built-in tools are present
        assert registry.has_tool('dns_lookup')
        assert registry.has_tool('tcp_port_check')
        assert registry.has_tool('http_check')
        assert registry.has_tool('traceroute')
        assert registry.has_tool('shell_ping')
        assert registry.has_tool('windows_list_directory')
    
    def test_load_yaml_tool(self):
        """Test loading a tool from YAML file"""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create a test YAML tool
            yaml_path = Path(tmpdir) / "test_tool.yaml"
            yaml_path.write_text("""
name: test_tool
display_name: Test Tool
description: A test tool
category: test
platform: cross-platform
version: 1.0.0
source: local
parameters:
  - name: param1
    type: string
    required: true
""")
            
            registry = ToolRegistry(catalog_dirs=tmpdir)
            
            # Verify tool is loaded
            assert registry.has_tool('test_tool')
            tool = registry.get_tool('test_tool')
            assert tool['name'] == 'test_tool'
            assert tool['display_name'] == 'Test Tool'
            assert tool['source'] == 'local'
    
    def test_yaml_overrides_builtin(self):
        """Test that YAML tools can override built-in tools"""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create a YAML tool with same name as built-in
            yaml_path = Path(tmpdir) / "dns_lookup.yaml"
            yaml_path.write_text("""
name: dns_lookup
display_name: Custom DNS Lookup
description: Custom DNS lookup tool
category: network
platform: cross-platform
version: 2.0.0
source: pipeline
parameters: []
""")
            
            registry = ToolRegistry(catalog_dirs=tmpdir)
            
            # Verify YAML version overrides built-in
            tool = registry.get_tool('dns_lookup')
            assert tool['display_name'] == 'Custom DNS Lookup'
            assert tool['version'] == '2.0.0'
            assert tool['source'] == 'pipeline'
    
    def test_deduplication_later_wins(self):
        """Test that later catalog directory wins on duplicate tools"""
        with tempfile.TemporaryDirectory() as tmpdir1:
            with tempfile.TemporaryDirectory() as tmpdir2:
                # Create same tool in both directories
                yaml1 = Path(tmpdir1) / "dup_tool.yaml"
                yaml1.write_text("""
name: dup_tool
display_name: First Version
version: 1.0.0
source: local
parameters: []
""")
                
                yaml2 = Path(tmpdir2) / "dup_tool.yaml"
                yaml2.write_text("""
name: dup_tool
display_name: Second Version
version: 2.0.0
source: pipeline
parameters: []
""")
                
                # Load with tmpdir1 first, then tmpdir2
                catalog_dirs = f"{tmpdir1}:{tmpdir2}"
                registry = ToolRegistry(catalog_dirs=catalog_dirs)
                
                # Verify second version wins
                tool = registry.get_tool('dup_tool')
                assert tool['display_name'] == 'Second Version'
                assert tool['version'] == '2.0.0'
    
    def test_required_tools_check(self):
        """Test that required tools are checked"""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create only some required tools
            yaml_path = Path(tmpdir) / "asset_count.yaml"
            yaml_path.write_text("""
name: asset_count
display_name: Asset Count
description: Count assets
category: asset
platform: cross-platform
source: local
parameters: []
""")
            
            registry = ToolRegistry(catalog_dirs=tmpdir)
            
            # Verify asset_count is present
            assert registry.has_tool('asset_count')
            
            # Note: windows_list_directory should be present from built-ins
            assert registry.has_tool('windows_list_directory')
    
    def test_list_tools_no_filter(self):
        """Test listing all tools without filters"""
        registry = ToolRegistry(catalog_dirs="/nonexistent")
        tools = registry.list_tools()
        
        assert len(tools) > 0
        assert all('name' in tool for tool in tools)
    
    def test_list_tools_with_platform_filter(self):
        """Test listing tools with platform filter"""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create tools with different platforms
            yaml1 = Path(tmpdir) / "win_tool.yaml"
            yaml1.write_text("""
name: win_tool
platform: windows
source: local
parameters: []
""")
            
            yaml2 = Path(tmpdir) / "linux_tool.yaml"
            yaml2.write_text("""
name: linux_tool
platform: linux
source: local
parameters: []
""")
            
            registry = ToolRegistry(catalog_dirs=tmpdir)
            
            # Filter by platform
            win_tools = registry.list_tools(platform='windows')
            linux_tools = registry.list_tools(platform='linux')
            
            assert any(t['name'] == 'win_tool' for t in win_tools)
            assert any(t['name'] == 'linux_tool' for t in linux_tools)
            assert not any(t['name'] == 'linux_tool' for t in win_tools)
    
    def test_list_tools_with_category_filter(self):
        """Test listing tools with category filter"""
        registry = ToolRegistry(catalog_dirs="/nonexistent")
        
        # Filter by category
        network_tools = registry.list_tools(category='network')
        
        assert len(network_tools) > 0
        assert all(t['category'] == 'network' for t in network_tools)
    
    def test_reload(self):
        """Test registry reload"""
        with tempfile.TemporaryDirectory() as tmpdir:
            registry = ToolRegistry(catalog_dirs=tmpdir)
            initial_count = registry.get_tool_count()
            
            # Add a new tool
            yaml_path = Path(tmpdir) / "new_tool.yaml"
            yaml_path.write_text("""
name: new_tool
display_name: New Tool
source: local
parameters: []
""")
            
            # Reload registry
            result = registry.reload()
            
            assert result['success'] is True
            assert registry.get_tool_count() > initial_count
            assert registry.has_tool('new_tool')
    
    def test_invalid_yaml_handling(self):
        """Test that invalid YAML files are handled gracefully"""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create invalid YAML file
            yaml_path = Path(tmpdir) / "invalid.yaml"
            yaml_path.write_text("invalid: yaml: content: [")
            
            # Should not crash
            registry = ToolRegistry(catalog_dirs=tmpdir)
            
            # Should still have built-in tools
            assert registry.get_tool_count() > 0
    
    def test_missing_name_field(self):
        """Test that YAML without name field is rejected"""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create YAML without name field
            yaml_path = Path(tmpdir) / "no_name.yaml"
            yaml_path.write_text("""
display_name: No Name Tool
description: Missing name field
source: local
parameters: []
""")
            
            registry = ToolRegistry(catalog_dirs=tmpdir)
            
            # Tool should not be loaded
            assert not registry.has_tool('no_name')
    
    def test_get_tool_count(self):
        """Test getting tool count"""
        registry = ToolRegistry(catalog_dirs="/nonexistent")
        count = registry.get_tool_count()
        
        assert count > 0
        assert count == len(registry.tools)
    
    def test_get_tool_not_found(self):
        """Test getting non-existent tool"""
        registry = ToolRegistry(catalog_dirs="/nonexistent")
        tool = registry.get_tool('nonexistent_tool')
        
        assert tool is None
    
    def test_recursive_yaml_scan(self):
        """Test that YAML files are found recursively"""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create nested directory structure
            subdir = Path(tmpdir) / "subdir"
            subdir.mkdir()
            
            yaml_path = subdir / "nested_tool.yaml"
            yaml_path.write_text("""
name: nested_tool
display_name: Nested Tool
source: local
parameters: []
""")
            
            registry = ToolRegistry(catalog_dirs=tmpdir)
            
            # Verify nested tool is found
            assert registry.has_tool('nested_tool')


if __name__ == '__main__':
    pytest.main([__file__, '-v'])