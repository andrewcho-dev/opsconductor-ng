#!/usr/bin/env python3
"""
Add top-level examples to all tool YAML files that don't have them.
This will dramatically improve LLM usability scores.
"""

import os
import yaml
from pathlib import Path
from typing import Dict, List, Any

def load_yaml_preserving_comments(file_path: Path) -> tuple[Dict, str]:
    """Load YAML and preserve the original content for appending."""
    with open(file_path, 'r') as f:
        content = f.read()
        data = yaml.safe_load(content)
    return data, content

def generate_examples_from_patterns(tool_spec: Dict) -> List[Dict]:
    """Generate examples from the tool's patterns."""
    examples = []
    
    capabilities = tool_spec.get('capabilities', {})
    for cap_name, cap_data in capabilities.items():
        patterns = cap_data.get('patterns', {})
        
        # Take first 3 patterns to create examples
        for i, (pattern_name, pattern_data) in enumerate(patterns.items()):
            if i >= 3:  # Limit to 3 examples per tool
                break
                
            # Get pattern description
            pattern_desc = pattern_data.get('description', '')
            
            # Get required inputs
            required_inputs = pattern_data.get('required_inputs', [])
            
            # Build example inputs
            example_inputs = {}
            for param in required_inputs:
                param_name = param.get('name', '')
                param_type = param.get('type', 'string')
                
                # Generate example value based on parameter name and type
                if param_type == 'boolean':
                    example_inputs[param_name] = True
                elif param_type == 'integer':
                    example_inputs[param_name] = 100
                elif 'ip' in param_name.lower() or 'host' in param_name.lower():
                    example_inputs[param_name] = "192.168.1.100"
                elif 'user' in param_name.lower():
                    example_inputs[param_name] = "admin"
                elif 'pass' in param_name.lower():
                    example_inputs[param_name] = "secure_password"
                elif 'port' in param_name.lower():
                    example_inputs[param_name] = "80"
                elif 'name' in param_name.lower():
                    example_inputs[param_name] = "example_name"
                elif 'path' in param_name.lower() or 'file' in param_name.lower():
                    example_inputs[param_name] = "/path/to/file"
                elif 'command' in param_name.lower():
                    example_inputs[param_name] = "Get-Service"
                elif 'service' in param_name.lower():
                    example_inputs[param_name] = "wuauserv"
                elif 'process' in param_name.lower():
                    example_inputs[param_name] = "notepad"
                else:
                    example_inputs[param_name] = f"example_{param_name}"
            
            # Get time and cost estimates
            time_estimate = pattern_data.get('time_estimate_ms', '1000')
            cost_estimate = pattern_data.get('cost_estimate', '1')
            
            # Try to evaluate simple expressions
            try:
                if isinstance(time_estimate, str) and time_estimate.isdigit():
                    time_ms = int(time_estimate)
                else:
                    time_ms = 1000
            except:
                time_ms = 1000
                
            try:
                if isinstance(cost_estimate, str) and cost_estimate.isdigit():
                    cost = int(cost_estimate)
                else:
                    cost = 1
            except:
                cost = 1
            
            # Create example
            example = {
                'name': pattern_name.replace('_', ' ').title(),
                'description': pattern_desc if pattern_desc else f"Example of {pattern_name}",
                'inputs': example_inputs,
                'expected_time_ms': time_ms,
                'expected_cost': cost
            }
            
            examples.append(example)
    
    return examples

def add_examples_to_tool(file_path: Path) -> bool:
    """Add examples section to a tool YAML file if it doesn't have one."""
    try:
        tool_spec, original_content = load_yaml_preserving_comments(file_path)
        
        # Skip if already has examples
        if 'examples' in tool_spec and tool_spec['examples']:
            return False
        
        # Generate examples
        examples = generate_examples_from_patterns(tool_spec)
        
        if not examples:
            print(f"  ⚠️  No patterns found to generate examples for {file_path.name}")
            return False
        
        # Add examples to the YAML
        tool_spec['examples'] = examples
        
        # Write back to file
        with open(file_path, 'w') as f:
            # Write original content first (to preserve comments)
            # Then append examples section
            
            # Check if file ends with newline
            if not original_content.endswith('\n'):
                original_content += '\n'
            
            # Check if examples section already exists (shouldn't, but just in case)
            if 'examples:' not in original_content:
                f.write(original_content)
                f.write('\n# === EXAMPLES ===\n')
                f.write('examples:\n')
                
                for example in examples:
                    f.write(f"  - name: \"{example['name']}\"\n")
                    f.write(f"    description: \"{example['description']}\"\n")
                    f.write(f"    inputs:\n")
                    for key, value in example['inputs'].items():
                        if isinstance(value, str):
                            f.write(f"      {key}: \"{value}\"\n")
                        else:
                            f.write(f"      {key}: {value}\n")
                    f.write(f"    expected_time_ms: {example['expected_time_ms']}\n")
                    f.write(f"    expected_cost: {example['expected_cost']}\n")
            else:
                # Just write the updated spec
                yaml.dump(tool_spec, f, default_flow_style=False, sort_keys=False)
        
        return True
        
    except Exception as e:
        print(f"  ❌ Error processing {file_path.name}: {e}")
        return False

def main():
    tools_dir = Path('/home/opsconductor/opsconductor-ng/pipeline/config/tools')
    
    print("🔍 Scanning for tools without examples...")
    print()
    
    tools_updated = 0
    tools_skipped = 0
    tools_failed = 0
    
    for yaml_file in sorted(tools_dir.rglob('*.yaml')):
        if yaml_file.name == 'tool_template.yaml':
            continue
        
        relative_path = yaml_file.relative_to(tools_dir)
        
        result = add_examples_to_tool(yaml_file)
        
        if result:
            print(f"  ✅ Added examples to: {relative_path}")
            tools_updated += 1
        elif result is False:
            tools_skipped += 1
        else:
            tools_failed += 1
    
    print()
    print("=" * 80)
    print(f"📊 Summary:")
    print(f"  ✅ Tools updated: {tools_updated}")
    print(f"  ⏭️  Tools skipped (already have examples): {tools_skipped}")
    print(f"  ❌ Tools failed: {tools_failed}")
    print("=" * 80)

if __name__ == '__main__':
    main()