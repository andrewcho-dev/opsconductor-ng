#!/usr/bin/env python3
"""
Load Axis VAPIX PTZ tool into the database
"""
import yaml
import psycopg2
import json
from datetime import datetime

# Database connection
conn = psycopg2.connect(
    host="localhost",
    port=5432,
    database="opsconductor",
    user="opsconductor",
    password="opsconductor_secure_2024"
)

# Load YAML file
with open('/home/opsconductor/opsconductor-ng/pipeline/config/tools/network/axis_vapix_ptz.yaml', 'r') as f:
    tool_data = yaml.safe_load(f)

print(f"Loading tool: {tool_data['tool_name']} v{tool_data['version']}")

# Insert tool
cur = conn.cursor()

try:
    cur.execute("""
        INSERT INTO tool_catalog.tools (
            tool_name, version, description, platform, category,
            status, enabled, defaults, dependencies, metadata,
            is_latest, created_at, updated_at, created_by, updated_by
        ) VALUES (
            %s, %s, %s, %s, %s,
            'active', true, %s, '[]'::jsonb, %s,
            true, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP, 'system', 'system'
        )
        RETURNING id
    """, (
        tool_data['tool_name'],
        tool_data['version'],
        tool_data['description'],
        tool_data['platform'],
        tool_data['category'],
        json.dumps(tool_data.get('defaults', {})),
        json.dumps(tool_data.get('metadata', {}))
    ))
    
    tool_id = cur.fetchone()[0]
    print(f"✅ Tool inserted with ID: {tool_id}")
    
    # Insert capabilities
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
        print(f"  ✅ Capability '{cap_name}' inserted with ID: {cap_id}")
        
        # Insert patterns
        for pattern_name, pattern_data in cap_data.get('patterns', {}).items():
            # Store API parameters in required_inputs metadata
            required_inputs = pattern_data.get('required_inputs', [])
            for inp in required_inputs:
                if 'metadata' not in inp:
                    inp['metadata'] = {}
                inp['metadata']['api_parameters'] = pattern_data.get('api_parameters', {})
                inp['metadata']['example_request'] = pattern_data.get('example_request', '')
            
            cur.execute("""
                INSERT INTO tool_catalog.tool_patterns (
                    capability_id, pattern_name, description,
                    typical_use_cases, time_estimate_ms, cost_estimate,
                    complexity_score, scope, completeness, policy,
                    preference_match, required_inputs
                ) VALUES (
                    %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
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
                json.dumps(required_inputs)
            ))
            
            pattern_id = cur.fetchone()[0]
            print(f"    ✅ Pattern '{pattern_name}' inserted with ID: {pattern_id}")
    
    conn.commit()
    print("\n🎉 Axis VAPIX PTZ tool loaded successfully!")
    
except Exception as e:
    conn.rollback()
    print(f"\n❌ Error: {e}")
    raise
finally:
    cur.close()
    conn.close()