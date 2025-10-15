#!/usr/bin/env python3
"""
Test that tools are being loaded correctly from the database
"""
import sys
sys.path.insert(0, '/home/opsconductor/opsconductor-ng')

from pipeline.services.tool_catalog_service import ToolCatalogService

# Create service
service = ToolCatalogService()

# Get all tools
tools = service.get_all_tools_with_structure()

print(f"📚 Total tools loaded: {len(tools)}")

# Find Windows tools
windows_tools = [t for t in tools if t['tool_name'].startswith('windows-')]
print(f"\n🪟 Windows tools: {len(windows_tools)}")

# Find impacket tool
impacket_tool = next((t for t in tools if 'impacket' in t['tool_name']), None)

if impacket_tool:
    print(f"\n✅ Found windows-impacket-executor!")
    print(f"   Description: {impacket_tool['description']}")
    print(f"   Capabilities: {list(impacket_tool.get('capabilities', {}).keys())}")
else:
    print(f"\n❌ windows-impacket-executor NOT FOUND!")

# List all Windows tools
print(f"\n📋 All Windows tools:")
for tool in sorted(windows_tools, key=lambda t: t['tool_name']):
    print(f"   - {tool['tool_name']}")