#!/usr/bin/env python3
"""
Script to add execution_location field to all tool YAML files.

Mapping:
- linux, windows, database, cloud, container, monitoring -> automation-service
- custom (sendmail, slack_cli, teams_cli, webhook_sender) -> communication-service
- custom (asset_*) -> asset-service
- network -> network-service
"""

import os
import yaml
from pathlib import Path

# Define the tools directory
TOOLS_DIR = Path("/home/opsconductor/opsconductor-ng/pipeline/config/tools")

# Mapping rules
COMMUNICATION_TOOLS = ["sendmail", "slack_cli", "teams_cli", "webhook_sender"]
ASSET_TOOLS = ["asset_create", "asset_delete", "asset_list", "asset_query", "asset_update"]

def determine_execution_location(file_path: Path) -> str:
    """Determine which service should execute this tool."""
    
    # Get relative path from tools directory
    rel_path = file_path.relative_to(TOOLS_DIR)
    parts = rel_path.parts
    
    # Get tool name (filename without extension)
    tool_name = file_path.stem
    
    # Network tools -> network-service
    if parts[0] == "network":
        return "network-service"
    
    # Custom tools need special handling
    if parts[0] == "custom":
        if tool_name in COMMUNICATION_TOOLS:
            return "communication-service"
        elif tool_name in ASSET_TOOLS:
            return "asset-service"
        else:
            # Default custom tools to automation-service
            return "automation-service"
    
    # All other categories -> automation-service
    # (linux, windows, database, cloud, container, monitoring)
    return "automation-service"

def add_execution_location(file_path: Path):
    """Add execution_location field to a tool YAML file."""
    
    # Skip template files
    if "template" in str(file_path):
        print(f"⏭️  SKIP: {file_path.relative_to(TOOLS_DIR)} (template)")
        return
    
    try:
        # Read the file
        with open(file_path, 'r') as f:
            content = f.read()
        
        # Parse YAML
        data = yaml.safe_load(content)
        
        if not data:
            print(f"⚠️  SKIP: {file_path.relative_to(TOOLS_DIR)} (empty file)")
            return
        
        # Check if execution_location already exists
        if "execution_location" in data:
            print(f"✅ EXISTS: {file_path.relative_to(TOOLS_DIR)} -> {data['execution_location']}")
            return
        
        # Determine execution location
        execution_location = determine_execution_location(file_path)
        
        # Add execution_location field after tool_name
        lines = content.split('\n')
        new_lines = []
        added = False
        
        for line in lines:
            new_lines.append(line)
            # Add after tool_name line
            if not added and line.strip().startswith('tool_name:'):
                new_lines.append(f"execution_location: {execution_location}")
                added = True
        
        # Write back
        with open(file_path, 'w') as f:
            f.write('\n'.join(new_lines))
        
        print(f"✅ ADDED: {file_path.relative_to(TOOLS_DIR)} -> {execution_location}")
        
    except Exception as e:
        print(f"❌ ERROR: {file_path.relative_to(TOOLS_DIR)} - {e}")

def main():
    """Process all tool YAML files."""
    
    print("=" * 80)
    print("ADDING execution_location TO ALL TOOL DEFINITIONS")
    print("=" * 80)
    print()
    
    # Find all YAML files
    yaml_files = list(TOOLS_DIR.rglob("*.yaml"))
    
    print(f"Found {len(yaml_files)} YAML files\n")
    
    # Process each file
    for yaml_file in sorted(yaml_files):
        add_execution_location(yaml_file)
    
    print()
    print("=" * 80)
    print("COMPLETE!")
    print("=" * 80)

if __name__ == "__main__":
    main()