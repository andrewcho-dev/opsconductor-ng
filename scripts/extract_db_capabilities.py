#!/usr/bin/env python3
"""
Extract all capabilities and their required inputs from the database.
This replaces the tool registry as the single source of truth.
"""

import os
import sys
import json
from typing import Dict, List, Set

# Add parent directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from pipeline.services.tool_catalog_service import ToolCatalogService


def extract_required_input_names(required_inputs_json: List) -> List[str]:
    """
    Extract just the input names from the required_inputs JSON.
    
    Handles two formats:
    1. Simple list: ["asset_id", "justification"]
    2. Complex objects: [{"name": "host", "type": "string", ...}]
    """
    if not required_inputs_json:
        return []
    
    result = []
    for item in required_inputs_json:
        if isinstance(item, str):
            # Simple format: just the name
            result.append(item)
        elif isinstance(item, dict) and 'name' in item:
            # Complex format: extract the name field
            result.append(item['name'])
    
    return result


def main():
    print("=" * 80)
    print("EXTRACTING CAPABILITIES FROM DATABASE")
    print("=" * 80)
    print()
    
    # Initialize service
    service = ToolCatalogService()
    
    # Query all capabilities with their patterns
    query = """
        SELECT DISTINCT 
            tc.capability_name,
            tc.description,
            tp.required_inputs,
            tp.pattern_name
        FROM tool_catalog.tool_capabilities tc
        LEFT JOIN tool_catalog.tool_patterns tp ON tc.id = tp.capability_id
        WHERE tc.capability_name != 'primary_capability'
        ORDER BY tc.capability_name, tp.pattern_name
    """
    
    conn = service._get_connection()
    try:
        cursor = conn.cursor()
        cursor.execute(query)
        rows = cursor.fetchall()
        
        # Group by capability
        capabilities: Dict[str, Dict] = {}
        
        for row in rows:
            cap_name = row[0]
            cap_desc = row[1]
            required_inputs_json = row[2]
            pattern_name = row[3]
            
            if cap_name not in capabilities:
                capabilities[cap_name] = {
                    'description': cap_desc,
                    'patterns': [],
                    'all_required_inputs': set()
                }
            
            if pattern_name:
                # Extract input names
                input_names = extract_required_input_names(required_inputs_json)
                
                capabilities[cap_name]['patterns'].append({
                    'pattern_name': pattern_name,
                    'required_inputs': input_names
                })
                
                # Collect all unique inputs across patterns
                capabilities[cap_name]['all_required_inputs'].update(input_names)
        
        cursor.close()
        
        print(f"Total capabilities found: {len(capabilities)}")
        print()
        
        # Display capabilities
        print("=" * 80)
        print("CAPABILITIES WITH PATTERNS")
        print("=" * 80)
        print()
        
        for cap_name in sorted(capabilities.keys()):
            cap_data = capabilities[cap_name]
            print(f"  {cap_name}")
            print(f"      Description: {cap_data['description']}")
            print(f"      Patterns: {len(cap_data['patterns'])}")
            
            if cap_data['patterns']:
                # Show unique inputs across all patterns
                all_inputs = sorted(cap_data['all_required_inputs'])
                print(f"      Required inputs: {all_inputs}")
                
                # Show pattern details
                for pattern in cap_data['patterns']:
                    print(f"        - {pattern['pattern_name']}: {pattern['required_inputs']}")
            else:
                print(f"      ⚠️  NO PATTERNS DEFINED")
            
            print()
        
        # Generate input mapping for selector.py
        print("=" * 80)
        print("SUGGESTED INPUT MAPPING FOR selector.py")
        print("=" * 80)
        print()
        print("input_mapping = {")
        
        for cap_name in sorted(capabilities.keys()):
            cap_data = capabilities[cap_name]
            
            # Use the union of all inputs from all patterns
            all_inputs = sorted(cap_data['all_required_inputs'])
            
            print(f'    "{cap_name}": {all_inputs},')
        
        print("}")
        print()
        
        # Generate capability list for Stage A prompt
        print("=" * 80)
        print("CAPABILITY LIST FOR STAGE A PROMPT")
        print("=" * 80)
        print()
        
        for cap_name in sorted(capabilities.keys()):
            cap_data = capabilities[cap_name]
            desc = cap_data['description'] or "No description"
            print(f'  - {cap_name}: {desc}')
        
        print()
        print(f"Total: {len(capabilities)} capabilities")
        
    finally:
        service._return_connection(conn)


if __name__ == "__main__":
    main()