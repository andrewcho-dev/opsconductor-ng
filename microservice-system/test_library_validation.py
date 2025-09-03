#!/usr/bin/env python3

import json
import sys
from pathlib import Path

def test_library_validation():
    """Test library validation logic"""
    
    # Load the manifest
    manifest_path = Path("starter-libraries/windows-core/manifest.json")
    if not manifest_path.exists():
        print(f"Manifest not found: {manifest_path}")
        return False
    
    with open(manifest_path, 'r') as f:
        manifest_data = json.load(f)
    
    print("=== MANIFEST STRUCTURE ===")
    print(f"Metadata: {manifest_data['metadata']['name']}")
    print(f"Steps count: {len(manifest_data['steps'])}")
    
    # Test the first step
    first_step = manifest_data['steps'][0]
    print(f"\n=== FIRST STEP: {first_step['name']} ===")
    print(f"Parameters count: {len(first_step['parameters'])}")
    
    # Show parameter structure
    for param_name, param_data in first_step['parameters'].items():
        print(f"\nParameter: {param_name}")
        print(f"  Type: {param_data.get('type', 'MISSING')}")
        print(f"  Required: {param_data.get('required', 'MISSING')}")
        print(f"  Description: {param_data.get('description', 'MISSING')}")
        
        # Check if this matches StepParameter model
        required_fields = ['type']
        missing_fields = [field for field in required_fields if field not in param_data]
        if missing_fields:
            print(f"  ❌ Missing required fields: {missing_fields}")
        else:
            print(f"  ✅ Has all required fields")
    
    return True

if __name__ == "__main__":
    test_library_validation()