#!/usr/bin/env python3
"""
Test script for Tool Registry and Runner

Tests the backend implementation without starting the full service.
"""

import asyncio
import sys
import os

# Add paths
sys.path.append('/home/opsconductor/opsconductor-ng')
os.chdir('/home/opsconductor/opsconductor-ng')

from pipeline.tools.registry import ToolRegistry, ToolSpec
from pipeline.tools.runner import ToolRunner, ToolExecutionRequest


async def test_registry():
    """Test tool registry"""
    print("\n" + "="*60)
    print("TEST 1: Tool Registry")
    print("="*60)
    
    # Create registry
    registry = ToolRegistry(catalog_dir="/home/opsconductor/opsconductor-ng/tools/catalog")
    
    # Initialize and load tools
    await registry.initialize()
    
    # Check loaded tools
    tools = registry.list()
    print(f"\n✅ Loaded {len(tools)} tools:")
    for tool in tools:
        print(f"   - {tool.name}: {tool.description}")
    
    # Get specific tool
    dns_tool = registry.get("dns_lookup")
    if dns_tool:
        print(f"\n✅ Retrieved dns_lookup tool:")
        print(f"   Command: {dns_tool.command_template}")
        print(f"   Parameters: {[p.name for p in dns_tool.parameters]}")
    
    # Get stats
    stats = registry.get_stats()
    print(f"\n✅ Registry stats:")
    print(f"   Total tools: {stats['total_tools']}")
    print(f"   By platform: {stats['by_platform']}")
    print(f"   By category: {stats['by_category']}")
    
    return registry


async def test_runner(registry):
    """Test tool runner"""
    print("\n" + "="*60)
    print("TEST 2: Tool Runner")
    print("="*60)
    
    # The runner will use the global registry, so we need to set it
    from pipeline.tools import registry as registry_module
    registry_module._registry = registry
    
    runner = ToolRunner()
    
    # Test 1: DNS lookup
    print("\n📝 Test 2.1: DNS Lookup (example.com)")
    request = ToolExecutionRequest(
        tool_name="dns_lookup",
        parameters={
            "domain": "example.com",
            "record_type": "A"
        },
        trace_id="test-dns-001"
    )
    
    result = await runner.execute(request)
    print(f"   Success: {result.success}")
    print(f"   Duration: {result.duration_ms:.2f}ms")
    print(f"   Exit code: {result.exit_code}")
    if result.output:
        print(f"   Output (first 200 chars): {result.output[:200]}")
    if result.error:
        print(f"   Error: {result.error[:200]}")
    
    # Test 2: HTTP check
    print("\n📝 Test 2.2: HTTP Check (google.com)")
    request = ToolExecutionRequest(
        tool_name="http_check",
        parameters={
            "url": "https://www.google.com",
            "method": "GET",
            "timeout_s": 5
        },
        trace_id="test-http-001"
    )
    
    result = await runner.execute(request)
    print(f"   Success: {result.success}")
    print(f"   Duration: {result.duration_ms:.2f}ms")
    print(f"   Exit code: {result.exit_code}")
    if result.output:
        print(f"   Output: {result.output}")
    
    # Test 3: TCP port check (localhost:3000 - Kong)
    print("\n📝 Test 2.3: TCP Port Check (localhost:3000)")
    request = ToolExecutionRequest(
        tool_name="tcp_port_check",
        parameters={
            "host": "localhost",
            "port": 3000,
            "timeout_s": 3
        },
        trace_id="test-tcp-001"
    )
    
    result = await runner.execute(request)
    print(f"   Success: {result.success}")
    print(f"   Duration: {result.duration_ms:.2f}ms")
    print(f"   Exit code: {result.exit_code}")
    if result.output:
        print(f"   Output: {result.output}")
    
    # Test 4: Ping
    print("\n📝 Test 2.4: Ping (8.8.8.8)")
    request = ToolExecutionRequest(
        tool_name="shell_ping",
        parameters={
            "host": "8.8.8.8",
            "count": 2,
            "timeout_s": 2
        },
        trace_id="test-ping-001"
    )
    
    result = await runner.execute(request)
    print(f"   Success: {result.success}")
    print(f"   Duration: {result.duration_ms:.2f}ms")
    print(f"   Exit code: {result.exit_code}")
    if result.output:
        print(f"   Output (first 200 chars): {result.output[:200]}")
    
    # Test 5: Invalid tool
    print("\n📝 Test 2.5: Invalid Tool (should fail)")
    request = ToolExecutionRequest(
        tool_name="nonexistent_tool",
        parameters={},
        trace_id="test-invalid-001"
    )
    
    result = await runner.execute(request)
    print(f"   Success: {result.success}")
    print(f"   Error: {result.error}")


async def main():
    """Run all tests"""
    print("\n" + "="*60)
    print("TOOL REGISTRY & RUNNER BACKEND TESTS")
    print("="*60)
    
    try:
        # Test registry
        registry = await test_registry()
        
        # Test runner
        await test_runner(registry)
        
        print("\n" + "="*60)
        print("✅ ALL TESTS COMPLETED")
        print("="*60)
        
    except Exception as e:
        print(f"\n❌ TEST FAILED: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())