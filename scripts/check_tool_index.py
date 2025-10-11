#!/usr/bin/env python3
"""Check tool_index status."""
import os
import psycopg2

db_url = os.getenv('DATABASE_URL', 'postgresql://opsconductor:opsconductor_secure_2024@localhost:5432/opsconductor')
conn = psycopg2.connect(db_url)

try:
    with conn.cursor() as cur:
        cur.execute("SELECT COUNT(*) FROM tool_catalog.tool_index;")
        count = cur.fetchone()[0]
        print(f"✅ tool_index has {count} entries")
        
        if count > 0:
            cur.execute("SELECT id, name, platform FROM tool_catalog.tool_index LIMIT 5;")
            print("\nSample entries:")
            for row in cur.fetchall():
                print(f"  - {row[0]}: {row[1]} ({row[2]})")
finally:
    conn.close()