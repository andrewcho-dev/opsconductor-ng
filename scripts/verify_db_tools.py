#!/usr/bin/env python3
"""
Direct database verification of tool catalog deployment.
"""

import os
import psycopg2
from psycopg2.extras import RealDictCursor

def verify_tool_catalog():
    """Verify tool catalog deployment directly from database."""
    
    db_url = os.getenv('DATABASE_URL', 'postgresql://opsconductor:opsconductor@postgres:5432/opsconductor')
    
    print("=" * 80)
    print("TOOL CATALOG DATABASE VERIFICATION")
    print("=" * 80)
    print()
    
    try:
        # Connect to database
        print("1. Connecting to database...")
        conn = psycopg2.connect(db_url)
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        print("   ✅ Connected successfully")
        print()
        
        # Count total tools
        print("2. Counting total tools...")
        cursor.execute("SELECT COUNT(*) as count FROM tool_catalog.tools WHERE is_latest = true")
        total_count = cursor.fetchone()['count']
        print(f"   ✅ Total tools: {total_count}")
        print()
        
        # Count by platform
        print("3. Tools by platform:")
        cursor.execute("""
            SELECT platform, COUNT(*) as count 
            FROM tool_catalog.tools 
            WHERE is_latest = true 
            GROUP BY platform 
            ORDER BY count DESC
        """)
        for row in cursor.fetchall():
            print(f"   - {row['platform']}: {row['count']} tools")
        print()
        
        # Count by category
        print("4. Tools by category:")
        cursor.execute("""
            SELECT category, COUNT(*) as count 
            FROM tool_catalog.tools 
            WHERE is_latest = true 
            GROUP BY category 
            ORDER BY count DESC
        """)
        for row in cursor.fetchall():
            print(f"   - {row['category']}: {row['count']} tools")
        print()
        
        # Sample tools from each platform
        print("5. Sample tools from each platform:")
        cursor.execute("""
            SELECT DISTINCT ON (platform) 
                platform, tool_name, version, category
            FROM tool_catalog.tools 
            WHERE is_latest = true 
            ORDER BY platform, tool_name
        """)
        for row in cursor.fetchall():
            print(f"   - {row['platform']}: {row['tool_name']} v{row['version']} ({row['category']})")
        print()
        
        # Check for tools with capabilities
        print("6. Checking tool capabilities...")
        cursor.execute("""
            SELECT COUNT(*) as count 
            FROM tool_catalog.tools 
            WHERE is_latest = true 
            AND capabilities IS NOT NULL 
            AND capabilities != '{}'::jsonb
        """)
        with_caps = cursor.fetchone()['count']
        print(f"   ✅ Tools with capabilities: {with_caps}/{total_count}")
        print()
        
        # Check for tools with performance data
        print("7. Checking performance estimates...")
        cursor.execute("""
            SELECT COUNT(*) as count 
            FROM tool_catalog.tools 
            WHERE is_latest = true 
            AND time_estimate_ms IS NOT NULL
        """)
        with_perf = cursor.fetchone()['count']
        print(f"   ✅ Tools with time estimates: {with_perf}/{total_count}")
        print()
        
        # Check for tools with policy constraints
        print("8. Checking policy constraints...")
        cursor.execute("""
            SELECT 
                COUNT(*) FILTER (WHERE requires_approval = true) as requires_approval,
                COUNT(*) FILTER (WHERE production_safe = true) as production_safe,
                COUNT(*) FILTER (WHERE max_cost IS NOT NULL) as has_cost_limit
            FROM tool_catalog.tools 
            WHERE is_latest = true
        """)
        policy = cursor.fetchone()
        print(f"   - Requires approval: {policy['requires_approval']} tools")
        print(f"   - Production safe: {policy['production_safe']} tools")
        print(f"   - Has cost limits: {policy['has_cost_limit']} tools")
        print()
        
        # List some high-value tools
        print("9. Sample high-value tools:")
        cursor.execute("""
            SELECT tool_name, platform, category, description
            FROM tool_catalog.tools 
            WHERE is_latest = true 
            ORDER BY tool_name
            LIMIT 10
        """)
        for row in cursor.fetchall():
            desc = row['description'][:60] + "..." if len(row['description']) > 60 else row['description']
            print(f"   - {row['tool_name']} ({row['platform']}/{row['category']})")
            print(f"     {desc}")
        print()
        
        # Summary
        print("=" * 80)
        print("VERIFICATION SUMMARY")
        print("=" * 80)
        print(f"✅ Total tools deployed: {total_count}")
        print(f"✅ Tools with capabilities: {with_caps}")
        print(f"✅ Tools with performance data: {with_perf}")
        print(f"✅ Production-safe tools: {policy['production_safe']}")
        print()
        print("🎉 Tool catalog deployment successful!")
        print("=" * 80)
        
        cursor.close()
        conn.close()
        
    except Exception as e:
        print(f"   ❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0

if __name__ == '__main__':
    exit(verify_tool_catalog())