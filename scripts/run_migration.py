#!/usr/bin/env python3
"""
Run database migration for pgvector tool index.
"""
import os
import sys
import psycopg2
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

def run_migration():
    """Run the pgvector migration."""
    # Get database URL from environment
    db_url = os.getenv('DATABASE_URL', 'postgresql://opsconductor:opsconductor_secure_2024@localhost:5432/opsconductor')
    
    # Read migration file
    migration_file = project_root / 'database' / 'migrations' / '001_add_pgvector_tool_index.sql'
    
    print(f"Reading migration from: {migration_file}")
    with open(migration_file, 'r') as f:
        migration_sql = f.read()
    
    # Connect and execute
    print(f"Connecting to database...")
    conn = psycopg2.connect(db_url)
    conn.autocommit = True
    
    try:
        with conn.cursor() as cur:
            print("Executing migration...")
            cur.execute(migration_sql)
            print("✅ Migration completed successfully!")
            
            # Verify tables were created
            cur.execute("""
                SELECT table_name 
                FROM information_schema.tables 
                WHERE table_schema = 'tool_catalog' 
                AND table_name IN ('tool_index', 'stage_ab_telemetry')
                ORDER BY table_name;
            """)
            tables = cur.fetchall()
            print(f"\nCreated tables: {[t[0] for t in tables]}")
            
    except Exception as e:
        print(f"❌ Migration failed: {e}")
        raise
    finally:
        conn.close()

if __name__ == '__main__':
    run_migration()