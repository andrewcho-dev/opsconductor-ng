#!/usr/bin/env python3
"""
Script to extract all capabilities from the tool registry
and generate the input mapping for selector.py
"""

import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from pipeline.stages.stage_b.tool_registry import ToolRegistry

def main():
    # Initialize tool registry
    registry = ToolRegistry()
    
    # Get all capabilities
    capabilities = registry.get_all_capabilities()
    
    print("=" * 80)
    print("ALL CAPABILITIES IN TOOL REGISTRY")
    print("=" * 80)
    print(f"\nTotal capabilities: {len(capabilities)}\n")
    
    for cap in capabilities:
        tools = registry.get_tools_by_capability(cap)
        print(f"  - {cap}")
        for tool in tools:
            # Find the capability details
            for tool_cap in tool.capabilities:
                if tool_cap.name == cap:
                    print(f"      Tool: {tool.name}")
                    print(f"      Required inputs: {tool_cap.required_inputs}")
                    print(f"      Optional inputs: {tool_cap.optional_inputs}")
                    break
        print()
    
    print("=" * 80)
    print("SUGGESTED INPUT MAPPING FOR selector.py")
    print("=" * 80)
    print("\ninput_mapping = {")
    
    for cap in capabilities:
        tools = registry.get_tools_by_capability(cap)
        if tools:
            tool = tools[0]  # Use first tool as reference
            for tool_cap in tool.capabilities:
                if tool_cap.name == cap:
                    # Use required inputs as the mapping
                    inputs = tool_cap.required_inputs if tool_cap.required_inputs else []
                    print(f'    "{cap}": {inputs},')
                    break
    
    print("}")

if __name__ == "__main__":
    main()