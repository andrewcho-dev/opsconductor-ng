#!/usr/bin/env python3
"""
Load Windows tools from the registry into the database
"""
import psycopg2
import json
import sys
from datetime import datetime

# Add the project root to the path
sys.path.insert(0, '/home/opsconductor/opsconductor-ng')

from pipeline.stages.stage_b.tool_registry import ToolRegistry

# Database connection
conn = psycopg2.connect(
    host="localhost",
    port=5432,
    database="opsconductor",
    user="opsconductor",
    password="opsconductor_secure_2024"
)

print("🔧 Loading Windows tools from registry...")

# Create tool registry and load Windows tools
registry = ToolRegistry()

# Get all Windows tools
windows_tools = [tool for tool in registry.tools.values() if tool.name.startswith('windows-')]

print(f"📚 Found {len(windows_tools)} Windows tools to load")

cur = conn.cursor()

try:
    for tool in windows_tools:
        print(f"\n📦 Loading tool: {tool.name}")
        
        # Check if tool already exists
        cur.execute("""
            SELECT id FROM tool_catalog.tools 
            WHERE tool_name = %s AND version = '1.0'
        """, (tool.name,))
        
        existing = cur.fetchone()
        
        if existing:
            print(f"  ⚠️  Tool '{tool.name}' already exists, skipping...")
            continue
        
        # Determine platform from tool name
        platform = 'windows'
        
        # Determine category from tool description
        category = 'automation'
        if 'service' in tool.description.lower():
            category = 'system'
        elif 'network' in tool.description.lower():
            category = 'network'
        elif 'monitor' in tool.description.lower():
            category = 'monitoring'
        elif 'security' in tool.description.lower() or 'firewall' in tool.description.lower():
            category = 'security'
        
        # Build defaults
        defaults = {
            "accuracy_level": "high",
            "freshness": "real_time",
            "data_source": "direct"
        }
        
        # Build dependencies
        dependencies = []
        for dep in tool.dependencies:
            dependencies.append({"name": dep, "type": "library"})
        
        # Build metadata
        metadata = {
            "permissions": tool.permissions.value,
            "production_safe": tool.production_safe,
            "max_execution_time": tool.max_execution_time,
            "examples": tool.examples,
            "notes": tool.notes if hasattr(tool, 'notes') else []
        }
        
        # Insert tool
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
            tool.name,
            '1.0',
            tool.description,
            platform,
            category,
            json.dumps(defaults),
            json.dumps(dependencies),
            json.dumps(metadata)
        ))
        
        tool_id = cur.fetchone()[0]
        print(f"  ✅ Tool inserted with ID: {tool_id}")
        
        # Insert capabilities
        for capability in tool.capabilities:
            cur.execute("""
                INSERT INTO tool_catalog.tool_capabilities (
                    tool_id, capability_name, description
                ) VALUES (%s, %s, %s)
                RETURNING id
            """, (
                tool_id,
                capability.name,
                capability.description
            ))
            
            cap_id = cur.fetchone()[0]
            print(f"    ✅ Capability '{capability.name}' inserted with ID: {cap_id}")
            
            # Create a default pattern for this capability
            # Build required inputs from capability
            required_inputs = []
            for inp in capability.required_inputs:
                required_inputs.append({
                    "name": inp,
                    "type": "string",
                    "description": f"Required input: {inp}",
                    "required": True
                })
            
            # Add optional inputs
            for inp in capability.optional_inputs:
                required_inputs.append({
                    "name": inp,
                    "type": "string",
                    "description": f"Optional input: {inp}",
                    "required": False
                })
            
            # Build typical use cases from tool examples
            typical_use_cases = tool.examples[:3] if tool.examples else [f"Use {capability.name}"]
            
            # Insert pattern
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
                f"{capability.name}_default",
                capability.description,
                json.dumps(typical_use_cases),
                str(tool.max_execution_time * 1000),  # Convert to ms
                '0',
                1.0,
                'single_item',
                'complete',
                json.dumps({"requires_approval": not tool.production_safe}),
                json.dumps({}),
                json.dumps(required_inputs)
            ))
            
            pattern_id = cur.fetchone()[0]
            print(f"      ✅ Pattern '{capability.name}_default' inserted with ID: {pattern_id}")
    
    conn.commit()
    print("\n🎉 All Windows tools loaded successfully!")
    
except Exception as e:
    conn.rollback()
    print(f"\n❌ Error: {e}")
    import traceback
    traceback.print_exc()
    raise
finally:
    cur.close()
    conn.close()