"""
Tests for Windows Tools Registry
Validates that all Windows tools are properly registered and configured
"""

import pytest
from pipeline.stages.stage_b.tool_registry import ToolRegistry
from pipeline.schemas.selection_v1 import PermissionLevel


class TestWindowsToolsRegistry:
    """Test Windows tools registration and configuration"""
    
    @pytest.fixture
    def registry(self):
        """Create tool registry with Windows tools"""
        return ToolRegistry()
    
    def test_windows_tools_loaded(self, registry):
        """Test that Windows tools are loaded into registry"""
        all_tools = registry.get_all_tools()
        tool_names = [tool.name for tool in all_tools]
        
        # Verify Windows tools are present
        expected_windows_tools = [
            "windows-service-manager",
            "windows-process-manager",
            "windows-user-manager",
            "windows-registry-manager",
            "windows-filesystem-manager",
            "windows-disk-manager",
            "windows-network-manager",
            "windows-firewall-manager",
            "windows-eventlog-manager",
            "windows-performance-monitor",
            "windows-update-manager",
            "windows-task-scheduler",
            "windows-iis-manager",
            "windows-sql-manager",
            "windows-ad-manager",
            "windows-certificate-manager",
            "windows-powershell-executor",
            "windows-system-info",
            "windows-rdp-manager",
            "windows-printer-manager"
        ]
        
        for tool_name in expected_windows_tools:
            assert tool_name in tool_names, f"Windows tool '{tool_name}' not found in registry"
    
    def test_windows_service_manager_tool(self, registry):
        """Test windows-service-manager tool configuration"""
        tool = registry.get_tool("windows-service-manager")
        
        assert tool is not None
        assert tool.name == "windows-service-manager"
        assert "windows_service_management" in [cap.name for cap in tool.capabilities]
        assert "service_status" in [cap.name for cap in tool.capabilities]
        assert "service_configuration" in [cap.name for cap in tool.capabilities]
        assert tool.permissions == PermissionLevel.ADMIN
        assert tool.production_safe is True
        assert tool.max_execution_time == 120
        assert "winrm_connection" in tool.dependencies
        assert len(tool.examples) == 3
    
    def test_windows_process_manager_tool(self, registry):
        """Test windows-process-manager tool configuration"""
        tool = registry.get_tool("windows-process-manager")
        
        assert tool is not None
        assert "process_management" in [cap.name for cap in tool.capabilities]
        assert "process_monitoring" in [cap.name for cap in tool.capabilities]
        assert "process_analysis" in [cap.name for cap in tool.capabilities]
        assert tool.permissions == PermissionLevel.ADMIN
        assert tool.production_safe is True
    
    def test_windows_user_manager_tool(self, registry):
        """Test windows-user-manager tool configuration"""
        tool = registry.get_tool("windows-user-manager")
        
        assert tool is not None
        assert "user_management" in [cap.name for cap in tool.capabilities]
        assert "group_management" in [cap.name for cap in tool.capabilities]
        assert "user_query" in [cap.name for cap in tool.capabilities]
        assert tool.permissions == PermissionLevel.ADMIN
        assert tool.production_safe is False  # User management requires careful handling
    
    def test_windows_registry_manager_tool(self, registry):
        """Test windows-registry-manager tool configuration"""
        tool = registry.get_tool("windows-registry-manager")
        
        assert tool is not None
        assert "registry_read" in [cap.name for cap in tool.capabilities]
        assert "registry_write" in [cap.name for cap in tool.capabilities]
        assert "registry_delete" in [cap.name for cap in tool.capabilities]
        assert "registry_backup" in [cap.name for cap in tool.capabilities]
        assert tool.permissions == PermissionLevel.ADMIN
        assert tool.production_safe is False  # Registry changes are high-risk
    
    def test_windows_filesystem_manager_tool(self, registry):
        """Test windows-filesystem-manager tool configuration"""
        tool = registry.get_tool("windows-filesystem-manager")
        
        assert tool is not None
        assert "file_operations" in [cap.name for cap in tool.capabilities]
        assert "file_permissions" in [cap.name for cap in tool.capabilities]
        assert "file_attributes" in [cap.name for cap in tool.capabilities]
        assert "file_search" in [cap.name for cap in tool.capabilities]
        assert tool.permissions == PermissionLevel.WRITE
        assert tool.production_safe is False
    
    def test_windows_disk_manager_tool(self, registry):
        """Test windows-disk-manager tool configuration"""
        tool = registry.get_tool("windows-disk-manager")
        
        assert tool is not None
        assert "disk_monitoring" in [cap.name for cap in tool.capabilities]
        assert "disk_management" in [cap.name for cap in tool.capabilities]
        assert "disk_health" in [cap.name for cap in tool.capabilities]
        assert tool.permissions == PermissionLevel.ADMIN
        assert tool.production_safe is True
    
    def test_windows_network_manager_tool(self, registry):
        """Test windows-network-manager tool configuration"""
        tool = registry.get_tool("windows-network-manager")
        
        assert tool is not None
        assert "network_configuration" in [cap.name for cap in tool.capabilities]
        assert "network_info" in [cap.name for cap in tool.capabilities]
        assert "network_testing" in [cap.name for cap in tool.capabilities]
        assert tool.permissions == PermissionLevel.ADMIN
        assert tool.production_safe is False  # Network changes can cause connectivity loss
    
    def test_windows_firewall_manager_tool(self, registry):
        """Test windows-firewall-manager tool configuration"""
        tool = registry.get_tool("windows-firewall-manager")
        
        assert tool is not None
        assert "firewall_rules" in [cap.name for cap in tool.capabilities]
        assert "firewall_profiles" in [cap.name for cap in tool.capabilities]
        assert "firewall_query" in [cap.name for cap in tool.capabilities]
        assert tool.permissions == PermissionLevel.ADMIN
        assert tool.production_safe is False
    
    def test_windows_eventlog_manager_tool(self, registry):
        """Test windows-eventlog-manager tool configuration"""
        tool = registry.get_tool("windows-eventlog-manager")
        
        assert tool is not None
        assert "log_access" in [cap.name for cap in tool.capabilities]
        assert "log_analysis" in [cap.name for cap in tool.capabilities]
        assert "log_management" in [cap.name for cap in tool.capabilities]
        assert tool.permissions == PermissionLevel.READ
        assert tool.production_safe is True
    
    def test_windows_performance_monitor_tool(self, registry):
        """Test windows-performance-monitor tool configuration"""
        tool = registry.get_tool("windows-performance-monitor")
        
        assert tool is not None
        assert "system_monitoring" in [cap.name for cap in tool.capabilities]
        assert "memory_monitoring" in [cap.name for cap in tool.capabilities]
        assert "performance_counters" in [cap.name for cap in tool.capabilities]
        assert tool.permissions == PermissionLevel.READ
        assert tool.production_safe is True
    
    def test_windows_update_manager_tool(self, registry):
        """Test windows-update-manager tool configuration"""
        tool = registry.get_tool("windows-update-manager")
        
        assert tool is not None
        assert "update_query" in [cap.name for cap in tool.capabilities]
        assert "update_installation" in [cap.name for cap in tool.capabilities]
        assert "update_configuration" in [cap.name for cap in tool.capabilities]
        assert tool.permissions == PermissionLevel.ADMIN
        assert tool.production_safe is False  # Updates can cause reboots
        assert tool.max_execution_time == 3600
    
    def test_windows_task_scheduler_tool(self, registry):
        """Test windows-task-scheduler tool configuration"""
        tool = registry.get_tool("windows-task-scheduler")
        
        assert tool is not None
        assert "task_management" in [cap.name for cap in tool.capabilities]
        assert "task_execution" in [cap.name for cap in tool.capabilities]
        assert "task_query" in [cap.name for cap in tool.capabilities]
        assert tool.permissions == PermissionLevel.ADMIN
        assert tool.production_safe is True
    
    def test_windows_iis_manager_tool(self, registry):
        """Test windows-iis-manager tool configuration"""
        tool = registry.get_tool("windows-iis-manager")
        
        assert tool is not None
        assert "iis_website_management" in [cap.name for cap in tool.capabilities]
        assert "iis_apppool_management" in [cap.name for cap in tool.capabilities]
        assert "iis_configuration" in [cap.name for cap in tool.capabilities]
        assert tool.permissions == PermissionLevel.ADMIN
        assert tool.production_safe is True
        assert "iis_installed" in tool.dependencies
    
    def test_windows_sql_manager_tool(self, registry):
        """Test windows-sql-manager tool configuration"""
        tool = registry.get_tool("windows-sql-manager")
        
        assert tool is not None
        assert "sql_query" in [cap.name for cap in tool.capabilities]
        assert "sql_backup" in [cap.name for cap in tool.capabilities]
        assert "sql_management" in [cap.name for cap in tool.capabilities]
        assert tool.permissions == PermissionLevel.ADMIN
        assert tool.production_safe is False
        assert "sql_server_installed" in tool.dependencies
    
    def test_windows_ad_manager_tool(self, registry):
        """Test windows-ad-manager tool configuration"""
        tool = registry.get_tool("windows-ad-manager")
        
        assert tool is not None
        assert "ad_user_management" in [cap.name for cap in tool.capabilities]
        assert "ad_group_management" in [cap.name for cap in tool.capabilities]
        assert "ad_query" in [cap.name for cap in tool.capabilities]
        assert tool.permissions == PermissionLevel.ADMIN
        assert tool.production_safe is False
        assert "domain_controller" in tool.dependencies
    
    def test_windows_certificate_manager_tool(self, registry):
        """Test windows-certificate-manager tool configuration"""
        tool = registry.get_tool("windows-certificate-manager")
        
        assert tool is not None
        assert "certificate_query" in [cap.name for cap in tool.capabilities]
        assert "certificate_management" in [cap.name for cap in tool.capabilities]
        assert "certificate_validation" in [cap.name for cap in tool.capabilities]
        assert tool.permissions == PermissionLevel.ADMIN
        assert tool.production_safe is True
    
    def test_windows_powershell_executor_tool(self, registry):
        """Test windows-powershell-executor tool configuration"""
        tool = registry.get_tool("windows-powershell-executor")
        
        assert tool is not None
        assert "windows_automation" in [cap.name for cap in tool.capabilities]
        assert "powershell_remoting" in [cap.name for cap in tool.capabilities]
        assert "script_validation" in [cap.name for cap in tool.capabilities]
        assert tool.permissions == PermissionLevel.ADMIN
        assert tool.production_safe is False
        assert tool.max_execution_time == 600
    
    def test_windows_system_info_tool(self, registry):
        """Test windows-system-info tool configuration"""
        tool = registry.get_tool("windows-system-info")
        
        assert tool is not None
        assert "system_info" in [cap.name for cap in tool.capabilities]
        assert "hardware_info" in [cap.name for cap in tool.capabilities]
        assert "software_inventory" in [cap.name for cap in tool.capabilities]
        assert tool.permissions == PermissionLevel.READ
        assert tool.production_safe is True
    
    def test_windows_rdp_manager_tool(self, registry):
        """Test windows-rdp-manager tool configuration"""
        tool = registry.get_tool("windows-rdp-manager")
        
        assert tool is not None
        assert "rdp_configuration" in [cap.name for cap in tool.capabilities]
        assert "rdp_sessions" in [cap.name for cap in tool.capabilities]
        assert "rdp_users" in [cap.name for cap in tool.capabilities]
        assert tool.permissions == PermissionLevel.ADMIN
        assert tool.production_safe is True
    
    def test_windows_printer_manager_tool(self, registry):
        """Test windows-printer-manager tool configuration"""
        tool = registry.get_tool("windows-printer-manager")
        
        assert tool is not None
        assert "printer_management" in [cap.name for cap in tool.capabilities]
        assert "printer_query" in [cap.name for cap in tool.capabilities]
        assert "print_job_management" in [cap.name for cap in tool.capabilities]
        assert tool.permissions == PermissionLevel.ADMIN
        assert tool.production_safe is True
    
    def test_all_windows_tools_have_examples(self, registry):
        """Test that all Windows tools have usage examples"""
        all_tools = registry.get_all_tools()
        windows_tools = [tool for tool in all_tools if tool.name.startswith("windows-")]
        
        for tool in windows_tools:
            assert len(tool.examples) > 0, f"Tool '{tool.name}' has no examples"
            
            # Verify examples are strings
            for example in tool.examples:
                assert isinstance(example, str), f"Example should be a string, got {type(example)}"
                assert len(example) > 0, f"Example should not be empty"
    
    def test_windows_capabilities_registered(self, registry):
        """Test that Windows-specific capabilities are registered"""
        all_capabilities = registry.get_all_capabilities()
        
        expected_capabilities = [
            "windows_automation",
            "windows_service_management",
            "registry_read",
            "registry_write",
            "registry_delete",
            "registry_backup",
            "file_operations",
            "file_permissions",
            "file_attributes",
            "file_search",
            "disk_monitoring",
            "disk_management",
            "disk_health",
            "network_configuration",
            "firewall_rules",
            "firewall_profiles",
            "firewall_query",
            "log_management",
            "memory_monitoring",
            "performance_counters",
            "update_query",
            "update_installation",
            "update_configuration",
            "task_management",
            "task_execution",
            "task_query",
            "iis_website_management",
            "iis_apppool_management",
            "iis_configuration",
            "sql_query",
            "sql_backup",
            "sql_management",
            "ad_user_management",
            "ad_group_management",
            "ad_query",
            "certificate_query",
            "certificate_management",
            "certificate_validation",
            "powershell_remoting",
            "script_validation",
            "hardware_info",
            "software_inventory",
            "rdp_configuration",
            "rdp_sessions",
            "rdp_users",
            "printer_management",
            "printer_query",
            "print_job_management"
        ]
        
        for capability in expected_capabilities:
            assert capability in all_capabilities, f"Capability '{capability}' not registered"
    
    def test_windows_tools_by_capability(self, registry):
        """Test retrieving Windows tools by capability"""
        # Test windows_automation capability
        automation_tools = registry.get_tools_by_capability("windows_automation")
        assert len(automation_tools) > 0
        assert any(tool.name == "windows-powershell-executor" for tool in automation_tools)
        
        # Test windows_service_management capability
        service_tools = registry.get_tools_by_capability("windows_service_management")
        assert len(service_tools) > 0
        assert any(tool.name == "windows-service-manager" for tool in service_tools)
        
        # Test registry capabilities
        registry_tools = registry.get_tools_by_capability("registry_read")
        assert len(registry_tools) > 0
        assert any(tool.name == "windows-registry-manager" for tool in registry_tools)
    
    def test_windows_tools_permission_levels(self, registry):
        """Test that Windows tools have appropriate permission levels"""
        all_tools = registry.get_all_tools()
        windows_tools = [tool for tool in all_tools if tool.name.startswith("windows-")]
        
        # Count tools by permission level
        read_tools = [t for t in windows_tools if t.permissions == PermissionLevel.READ]
        write_tools = [t for t in windows_tools if t.permissions == PermissionLevel.WRITE]
        admin_tools = [t for t in windows_tools if t.permissions == PermissionLevel.ADMIN]
        
        # Verify we have tools at each level
        assert len(read_tools) > 0, "No READ permission Windows tools found"
        assert len(write_tools) > 0, "No WRITE permission Windows tools found"
        assert len(admin_tools) > 0, "No ADMIN permission Windows tools found"
        
        # Verify specific tools have correct permissions
        assert registry.get_tool("windows-eventlog-manager").permissions == PermissionLevel.READ
        assert registry.get_tool("windows-filesystem-manager").permissions == PermissionLevel.WRITE
        assert registry.get_tool("windows-service-manager").permissions == PermissionLevel.ADMIN
    
    def test_windows_tools_production_safety(self, registry):
        """Test that Windows tools have appropriate production safety flags"""
        all_tools = registry.get_all_tools()
        windows_tools = [tool for tool in all_tools if tool.name.startswith("windows-")]
        
        # Tools that should be production safe
        safe_tools = [
            "windows-service-manager",
            "windows-process-manager",
            "windows-disk-manager",
            "windows-eventlog-manager",
            "windows-performance-monitor",
            "windows-task-scheduler",
            "windows-iis-manager",
            "windows-certificate-manager",
            "windows-system-info",
            "windows-rdp-manager",
            "windows-printer-manager"
        ]
        
        for tool_name in safe_tools:
            tool = registry.get_tool(tool_name)
            assert tool.production_safe is True, f"Tool '{tool_name}' should be production safe"
        
        # Tools that should NOT be production safe
        unsafe_tools = [
            "windows-user-manager",
            "windows-registry-manager",
            "windows-filesystem-manager",
            "windows-network-manager",
            "windows-firewall-manager",
            "windows-update-manager",
            "windows-sql-manager",
            "windows-ad-manager",
            "windows-powershell-executor"
        ]
        
        for tool_name in unsafe_tools:
            tool = registry.get_tool(tool_name)
            assert tool.production_safe is False, f"Tool '{tool_name}' should NOT be production safe"
    
    def test_registry_stats_include_windows_tools(self, registry):
        """Test that registry statistics include Windows tools"""
        stats = registry.get_registry_stats()
        
        assert stats["total_tools"] >= 20  # At least 20 Windows tools
        assert "windows_automation" in stats["capability_distribution"]
        assert "windows_service_management" in stats["capability_distribution"]
    
    def test_windows_tools_have_dependencies(self, registry):
        """Test that Windows tools have appropriate dependencies"""
        # All Windows tools should depend on winrm_connection
        all_tools = registry.get_all_tools()
        windows_tools = [tool for tool in all_tools if tool.name.startswith("windows-")]
        
        for tool in windows_tools:
            assert "winrm_connection" in tool.dependencies, f"Tool '{tool.name}' missing winrm_connection dependency"
        
        # Specific tools should have additional dependencies
        iis_tool = registry.get_tool("windows-iis-manager")
        assert "iis_installed" in iis_tool.dependencies
        
        sql_tool = registry.get_tool("windows-sql-manager")
        assert "sql_server_installed" in sql_tool.dependencies
        
        ad_tool = registry.get_tool("windows-ad-manager")
        assert "domain_controller" in ad_tool.dependencies


class TestWindowsToolsIntegration:
    """Test Windows tools integration with tool registry"""
    
    @pytest.fixture
    def registry(self):
        """Create tool registry"""
        return ToolRegistry()
    
    def test_windows_tools_count(self, registry):
        """Test that exactly 20 Windows tools are registered"""
        all_tools = registry.get_all_tools()
        windows_tools = [tool for tool in all_tools if tool.name.startswith("windows-")]
        
        assert len(windows_tools) == 20, f"Expected 20 Windows tools, found {len(windows_tools)}"
    
    def test_no_duplicate_windows_tools(self, registry):
        """Test that there are no duplicate Windows tool registrations"""
        all_tools = registry.get_all_tools()
        windows_tool_names = [tool.name for tool in all_tools if tool.name.startswith("windows-")]
        
        # Check for duplicates
        assert len(windows_tool_names) == len(set(windows_tool_names)), "Duplicate Windows tools found"
    
    def test_windows_tools_searchable(self, registry):
        """Test that Windows tools are searchable"""
        # Search by keyword
        service_tools = registry.search_tools("service")
        assert any(tool.name == "windows-service-manager" for tool in service_tools)
        
        network_tools = registry.search_tools("network")
        assert any(tool.name == "windows-network-manager" for tool in network_tools)
        
        firewall_tools = registry.search_tools("firewall")
        assert any(tool.name == "windows-firewall-manager" for tool in firewall_tools)
    
    def test_windows_tools_exportable(self, registry):
        """Test that Windows tools can be exported to config"""
        import tempfile
        import json
        import os
        
        # Export to temporary file
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.json') as f:
            temp_path = f.name
        
        try:
            registry.export_config(temp_path)
            
            # Verify file was created and contains Windows tools
            assert os.path.exists(temp_path)
            
            with open(temp_path, 'r') as f:
                config = json.load(f)
            
            assert "tools" in config
            tool_names = [tool["name"] for tool in config["tools"]]
            
            # Verify Windows tools are in export
            assert "windows-service-manager" in tool_names
            assert "windows-process-manager" in tool_names
            
        finally:
            # Cleanup
            if os.path.exists(temp_path):
                os.remove(temp_path)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])