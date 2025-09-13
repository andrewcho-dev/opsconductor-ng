#!/usr/bin/env python3

import re

# Read the file
with open('/home/opsconductor/asset-service/main.py', 'r') as f:
    content = f.read()

# Replace all references to enhanced_targets with targets
content = content.replace('assets.enhanced_targets', 'assets.targets')

# Replace the column references from enhanced_targets schema to targets schema
# enhanced_targets has: hostname, ip_address, os_type, os_version, description, tags
# targets has: host, target_type, connection_type, description, tags, metadata

# Replace SELECT statements that use enhanced_targets columns
content = re.sub(
    r'SELECT id, name, hostname, ip_address, os_type, os_version,\s*description, tags, created_at, updated_at',
    'SELECT id, name, description, host, target_type, connection_type, tags, metadata, is_active, created_by, created_at, updated_at',
    content
)

content = re.sub(
    r'SELECT id, name, hostname, ip_address, os_type, os_version,\s*description, tags, created_at',
    'SELECT id, name, description, host, target_type, connection_type, tags, metadata, is_active, created_by, created_at',
    content
)

# Replace INSERT statements
content = re.sub(
    r'INSERT INTO assets\.targets\s*\(name, hostname, ip_address, os_type, os_version, description, tags\)',
    'INSERT INTO assets.targets (name, description, host, target_type, connection_type, tags, created_by)',
    content
)

# Replace UPDATE statements
content = re.sub(
    r'UPDATE assets\.targets\s*SET.*hostname.*ip_address.*os_type.*os_version.*description.*tags.*updated_at',
    'UPDATE assets.targets SET name = $1, description = $2, host = $3, target_type = $4, connection_type = $5, tags = $6, updated_at = $7',
    content,
    flags=re.DOTALL
)

# Replace field references in JOIN statements
content = re.sub(
    r't\.name as target_name, t\.hostname, t\.ip_address, t\.os_type',
    't.name as target_name, t.host, t.target_type',
    content
)

# Write the file back
with open('/home/opsconductor/asset-service/main.py', 'w') as f:
    f.write(content)

print("Fixed all enhanced_targets references!")