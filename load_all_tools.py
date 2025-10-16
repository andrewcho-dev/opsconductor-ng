#!/usr/bin/env python3
"""
Load all tools from YAML files into the database
"""
import yaml
import psycopg2
import json
import os
import glob
from pathlib import Path

DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://opsconductor:opsconductor_secure_2024@localhost:5432/opsconductor"
)

conn = psycopg2.connect(DATABASE_URL)
cur = conn.cursor()

tools_dir = Path('/home/opsconductor/opsconductor-ng/pipeline/config/tools')
yaml_files = list(tools_dir.rglob('*.yaml')) + list(tools_dir.rglob('*.yml'))

print(f"🔍 Found {len(yaml_files)} YAML tool files")

loaded_count = 0
skipped_count = 0
error_count = 0

for yaml_file in sorted(yaml_files):
    try:
        with open(yaml_file, 'r') as f:
            tool_data = yaml.safe_load(f)
        
        if not tool_data or 'tool_name' not in tool_data:
            print(f"⚠️  Skipping {yaml_file.name}: No tool_name found")
            skipped_count += 1
            continue
        
        tool_name = tool_data['tool_name']
        version = tool_data.get('version', '1.0')
        
        cur.execute("""
            SELECT id FROM tool_catalog.tools 
            WHERE tool_name = %s AND version = %s
        """, (tool_name, version))
        
        if cur.fetchone():
            print(f"⏭️  {tool_name} v{version} already exists")
            skipped_count += 1
            continue
        
        print(f"\n📦 Loading: {tool_name} v{version}")
        
        cur.execute("""
            INSERT INTO tool_catalog.tools (
                tool_name, version, description, platform, category,
                status, enabled, defaults, dependencies, metadata,
                is_latest, created_at, updated_at, created_by, updated_by
            ) VALUES (
                %s, %s, %s, %s, %s,
                'active', true, %s, %s, %s,
                true, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP, 'system', 'system'
            )
            RETURNING id
        """, (
            tool_name,
            version,
            tool_data.get('description', ''),
            tool_data.get('platform', 'linux'),
            tool_data.get('category', 'automation'),
            json.dumps(tool_data.get('defaults', {})),
            json.dumps(tool_data.get('dependencies', [])),
            json.dumps(tool_data.get('metadata', {}))
        ))
        
        tool_id = cur.fetchone()[0]
        print(f"  ✅ Tool ID: {tool_id}")
        
        for cap_name, cap_data in tool_data.get('capabilities', {}).items():
            cur.execute("""
                INSERT INTO tool_catalog.tool_capabilities (
                    tool_id, capability_name, description
                ) VALUES (%s, %s, %s)
                RETURNING id
            """, (
                tool_id,
                cap_name,
                cap_data.get('description', '')
            ))
            
            cap_id = cur.fetchone()[0]
            print(f"    ✅ Capability: {cap_name} (ID: {cap_id})")
            
            for pattern_name, pattern_data in cap_data.get('patterns', {}).items():
                required_inputs = pattern_data.get('required_inputs', [])
                optional_inputs = pattern_data.get('optional_inputs', [])
                all_inputs = required_inputs + optional_inputs
                
                for inp in all_inputs:
                    if isinstance(inp, dict):
                        if 'required' not in inp:
                            inp['required'] = inp in required_inputs
                
                cur.execute("""
                    INSERT INTO tool_catalog.tool_patterns (
                        capability_id, pattern_name, description,
                        typical_use_cases, time_estimate_ms, cost_estimate,
                        complexity_score, scope, completeness, policy,
                        preference_match, required_inputs, expected_outputs
                    ) VALUES (
                        %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
                    )
                    RETURNING id
                """, (
                    cap_id,
                    pattern_name,
                    pattern_data.get('description', ''),
                    json.dumps(pattern_data.get('typical_use_cases', [])),
                    str(pattern_data.get('time_estimate_ms', '0')),
                    str(pattern_data.get('cost_estimate', '0')),
                    float(pattern_data.get('complexity_score', 0)),
                    pattern_data.get('scope', 'single_item'),
                    pattern_data.get('completeness', 'complete'),
                    json.dumps(pattern_data.get('policy', {})),
                    json.dumps(pattern_data.get('preference_match', {})),
                    json.dumps(all_inputs),
                    json.dumps(pattern_data.get('expected_outputs', []))
                ))
                
                pattern_id = cur.fetchone()[0]
                print(f"      ✅ Pattern: {pattern_name} (ID: {pattern_id})")
        
        conn.commit()
        loaded_count += 1
        
    except Exception as e:
        conn.rollback()
        print(f"❌ Error loading {yaml_file.name}: {e}")
        error_count += 1
        continue

cur.close()
conn.close()

print(f"\n{'='*60}")
print(f"✅ Loaded: {loaded_count}")
print(f"⏭️  Skipped: {skipped_count}")
print(f"❌ Errors: {error_count}")
print(f"{'='*60}")
