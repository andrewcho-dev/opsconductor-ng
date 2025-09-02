#!/usr/bin/env python3
"""
Fix manifest.json files to have the correct structure expected by the service
"""

import json
import os
from pathlib import Path

def fix_manifest(manifest_path):
    """Fix a single manifest file"""
    with open(manifest_path, 'r') as f:
        data = json.load(f)
    
    # Check if already has metadata structure
    if 'metadata' in data:
        print(f"✅ {manifest_path} already has correct structure")
        return
    
    # Extract metadata fields
    metadata_fields = [
        'name', 'version', 'display_name', 'description', 'author', 
        'author_email', 'homepage', 'repository', 'license', 'categories',
        'tags', 'dependencies', 'min_opsconductor_version', 'is_premium'
    ]
    
    metadata = {}
    for field in metadata_fields:
        if field in data:
            metadata[field] = data.pop(field)
    
    # Restructure
    new_data = {
        'metadata': metadata,
        'steps': data.get('steps', [])
    }
    
    # Write back
    with open(manifest_path, 'w') as f:
        json.dump(new_data, f, indent=2)
    
    print(f"✅ Fixed {manifest_path}")

def main():
    starter_dir = Path(__file__).parent / "starter-libraries"
    
    for lib_dir in starter_dir.iterdir():
        if lib_dir.is_dir():
            manifest_path = lib_dir / "manifest.json"
            if manifest_path.exists():
                fix_manifest(manifest_path)

if __name__ == "__main__":
    main()