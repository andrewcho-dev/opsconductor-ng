#!/usr/bin/env python3
"""
Fix parameter structures in manifest files to match the StepParameter model
"""

import json
from pathlib import Path

def fix_parameters(manifest_path):
    """Fix parameter structures in a manifest file"""
    with open(manifest_path, 'r') as f:
        data = json.load(f)
    
    modified = False
    
    for step in data.get('steps', []):
        parameters = step.get('parameters', {})
        
        for param_name, param_def in parameters.items():
            # Keep only fields that match StepParameter model
            new_param = {}
            
            # Required field
            if 'type' in param_def:
                new_param['type'] = param_def['type']
            
            # Map 'textarea' to 'string' for compatibility
            if new_param.get('type') == 'textarea':
                new_param['type'] = 'string'
            elif new_param.get('type') == 'select':
                new_param['type'] = 'string'
            elif new_param.get('type') == 'checkbox':
                new_param['type'] = 'boolean'
            elif new_param.get('type') == 'text':
                new_param['type'] = 'string'
            
            # Optional fields that match the model
            if 'required' in param_def:
                new_param['required'] = param_def['required']
            
            if 'default' in param_def:
                new_param['default'] = param_def['default']
            
            if 'description' in param_def:
                new_param['description'] = param_def['description']
            
            if 'options' in param_def:
                new_param['options'] = param_def['options']
            
            # Create validation object for additional constraints
            validation = {}
            if 'min' in param_def:
                validation['min'] = param_def['min']
            if 'max' in param_def:
                validation['max'] = param_def['max']
            if 'placeholder' in param_def:
                validation['placeholder'] = param_def['placeholder']
            if 'label' in param_def:
                validation['label'] = param_def['label']
            
            if validation:
                new_param['validation'] = validation
            
            # Update the parameter
            parameters[param_name] = new_param
            modified = True
    
    if modified:
        with open(manifest_path, 'w') as f:
            json.dump(data, f, indent=2)
        print(f"✅ Fixed parameters in {manifest_path}")
    else:
        print(f"⏭️  No changes needed in {manifest_path}")

def main():
    starter_dir = Path(__file__).parent / "starter-libraries"
    
    for lib_dir in starter_dir.iterdir():
        if lib_dir.is_dir():
            manifest_path = lib_dir / "manifest.json"
            if manifest_path.exists():
                fix_parameters(manifest_path)

if __name__ == "__main__":
    main()