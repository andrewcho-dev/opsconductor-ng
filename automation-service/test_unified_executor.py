#!/usr/bin/env python3
"""
Test script for Unified Execution Framework

This script tests the unified executor with various tool types to ensure
the refactoring works correctly.
"""

import asyncio
import sys
import logging
from unified_executor import UnifiedExecutor, ExecutionConfig, ExecutionType, ConnectionType

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)

class MockService:
    """Mock service for testing"""
    def __init__(self):
        self.logger = logger

async def test_powershell_cmdlet():
    """Test Windows PowerShell cmdlet"""
    print("\n" + "="*80)
    print("TEST 1: Windows PowerShell Cmdlet (Get-Service)")
    print("="*80)
    
    service = MockService()
    executor = UnifiedExecutor(logger)
    
    tool_definition = {
        "tool_name": "Get-Service",
        "platform": "windows",
        "category": "system"
    }
    
    parameters = {
        "name": "wuauserv",
        "target_host": "192.168.1.100"
    }
    
    try:
        command, target_host, connection_type, credentials = await executor.execute_tool(
            tool_definition=tool_definition,
            parameters=parameters,
            service_instance=service
        )
        
        print(f"✅ Command: {command}")
        print(f"✅ Target Host: {target_host}")
        print(f"✅ Connection Type: {connection_type}")
        print(f"✅ Credentials: {credentials}")
        
        assert command == "Get-Service -Name wuauserv", f"Expected 'Get-Service -Name wuauserv', got '{command}'"
        assert connection_type == "powershell", f"Expected 'powershell', got '{connection_type}'"
        print("✅ TEST PASSED")
        return True
    except Exception as e:
        print(f"❌ TEST FAILED: {e}")
        return False

async def test_linux_command():
    """Test Linux CLI command"""
    print("\n" + "="*80)
    print("TEST 2: Linux CLI Command (ping)")
    print("="*80)
    
    service = MockService()
    executor = UnifiedExecutor(logger)
    
    tool_definition = {
        "tool_name": "ping",
        "platform": "linux",
        "category": "network"
    }
    
    parameters = {
        "target_host": "8.8.8.8",
        "count": 4
    }
    
    try:
        command, target_host, connection_type, credentials = await executor.execute_tool(
            tool_definition=tool_definition,
            parameters=parameters,
            service_instance=service
        )
        
        print(f"✅ Command: {command}")
        print(f"✅ Target Host: {target_host}")
        print(f"✅ Connection Type: {connection_type}")
        print(f"✅ Credentials: {credentials}")
        
        assert "ping" in command, f"Expected 'ping' in command, got '{command}'"
        assert connection_type == "ssh", f"Expected 'ssh', got '{connection_type}'"
        print("✅ TEST PASSED")
        return True
    except Exception as e:
        print(f"❌ TEST FAILED: {e}")
        return False

async def test_impacket_tool():
    """Test Impacket tool"""
    print("\n" + "="*80)
    print("TEST 3: Impacket Tool (windows-impacket-executor)")
    print("="*80)
    
    service = MockService()
    executor = UnifiedExecutor(logger)
    
    tool_definition = {
        "tool_name": "windows-impacket-executor",
        "platform": "windows",
        "category": "remote_execution"
    }
    
    parameters = {
        "command": "notepad.exe",
        "target_host": "192.168.1.100",
        "interactive": True
    }
    
    try:
        command, target_host, connection_type, credentials = await executor.execute_tool(
            tool_definition=tool_definition,
            parameters=parameters,
            service_instance=service
        )
        
        print(f"✅ Command: {command}")
        print(f"✅ Target Host: {target_host}")
        print(f"✅ Connection Type: {connection_type}")
        print(f"✅ Credentials: {credentials}")
        
        assert command == "notepad.exe", f"Expected 'notepad.exe', got '{command}'"
        assert connection_type == "impacket", f"Expected 'impacket', got '{connection_type}'"
        print("✅ TEST PASSED")
        return True
    except Exception as e:
        print(f"❌ TEST FAILED: {e}")
        return False

async def test_generic_command():
    """Test generic command"""
    print("\n" + "="*80)
    print("TEST 4: Generic Command")
    print("="*80)
    
    service = MockService()
    executor = UnifiedExecutor(logger)
    
    tool_definition = {
        "tool_name": "custom-script",
        "platform": "",
        "category": ""
    }
    
    parameters = {
        "command": "ls -la /tmp",
        "target_host": "192.168.1.50"
    }
    
    try:
        command, target_host, connection_type, credentials = await executor.execute_tool(
            tool_definition=tool_definition,
            parameters=parameters,
            service_instance=service
        )
        
        print(f"✅ Command: {command}")
        print(f"✅ Target Host: {target_host}")
        print(f"✅ Connection Type: {connection_type}")
        print(f"✅ Credentials: {credentials}")
        
        assert command == "ls -la /tmp", f"Expected 'ls -la /tmp', got '{command}'"
        print("✅ TEST PASSED")
        return True
    except Exception as e:
        print(f"❌ TEST FAILED: {e}")
        return False

async def test_inference():
    """Test intelligent inference"""
    print("\n" + "="*80)
    print("TEST 5: Intelligent Inference (Set-Service)")
    print("="*80)
    
    service = MockService()
    executor = UnifiedExecutor(logger)
    
    # No platform specified - should infer from tool name
    tool_definition = {
        "tool_name": "Set-Service",
        "platform": "",
        "category": ""
    }
    
    parameters = {
        "name": "wuauserv",
        "status": "Running",
        "target_host": "192.168.1.100"
    }
    
    try:
        command, target_host, connection_type, credentials = await executor.execute_tool(
            tool_definition=tool_definition,
            parameters=parameters,
            service_instance=service
        )
        
        print(f"✅ Command: {command}")
        print(f"✅ Target Host: {target_host}")
        print(f"✅ Connection Type: {connection_type}")
        print(f"✅ Credentials: {credentials}")
        
        assert "Set-Service" in command, f"Expected 'Set-Service' in command, got '{command}'"
        assert connection_type == "powershell", f"Expected 'powershell', got '{connection_type}'"
        print("✅ TEST PASSED - Inference worked!")
        return True
    except Exception as e:
        print(f"❌ TEST FAILED: {e}")
        return False

async def main():
    """Run all tests"""
    print("\n" + "="*80)
    print("UNIFIED EXECUTION FRAMEWORK - TEST SUITE")
    print("="*80)
    
    results = []
    
    # Run all tests
    results.append(await test_powershell_cmdlet())
    results.append(await test_linux_command())
    results.append(await test_impacket_tool())
    results.append(await test_generic_command())
    results.append(await test_inference())
    
    # Summary
    print("\n" + "="*80)
    print("TEST SUMMARY")
    print("="*80)
    passed = sum(results)
    total = len(results)
    print(f"Passed: {passed}/{total}")
    
    if passed == total:
        print("✅ ALL TESTS PASSED!")
        return 0
    else:
        print(f"❌ {total - passed} TEST(S) FAILED")
        return 1

if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)