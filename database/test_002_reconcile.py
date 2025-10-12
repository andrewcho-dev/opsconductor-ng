#!/usr/bin/env python3
"""
Test suite for 002_tool_reconcile_pgvector.sql migration.

Tests that the reconciliation migration:
1. Is idempotent (can run multiple times safely)
2. Converts TEXT columns to TEXT[] correctly
3. Adds missing columns with correct defaults
4. Creates all required indexes
5. Preserves existing data during conversion
"""

import asyncio
import os
import asyncpg
import pytest


@pytest.fixture
async def db_connection():
    """Create a database connection for testing."""
    dsn = os.getenv(
        "DATABASE_URL",
        "postgresql://postgres:postgres@localhost:5432/postgres"
    )
    conn = await asyncpg.connect(dsn)
    yield conn
    await conn.close()


@pytest.fixture
async def clean_tool_table(db_connection):
    """Drop and recreate tool table for clean testing."""
    await db_connection.execute("DROP TABLE IF EXISTS tool CASCADE;")
    yield
    # Cleanup after test
    await db_connection.execute("DROP TABLE IF EXISTS tool CASCADE;")


async def run_migration(conn, migration_file):
    """Execute a migration file."""
    with open(migration_file, 'r') as f:
        sql = f.read()
    await conn.execute(sql)


@pytest.mark.asyncio
async def test_reconcile_creates_missing_table(db_connection, clean_tool_table):
    """Test that reconciliation creates tool table if it doesn't exist."""
    # First run the base migration to create the table
    await run_migration(db_connection, "database/migrations/001_tool_schema_pgvector.sql")
    
    # Verify table exists
    result = await db_connection.fetchval("""
        SELECT EXISTS (
            SELECT 1 FROM information_schema.tables 
            WHERE table_name = 'tool'
        );
    """)
    assert result is True


@pytest.mark.asyncio
async def test_reconcile_converts_text_to_array(db_connection, clean_tool_table):
    """Test that TEXT columns are converted to TEXT[] correctly."""
    # Create table with TEXT columns (old schema)
    await db_connection.execute("""
        CREATE TABLE tool (
            id BIGSERIAL PRIMARY KEY,
            key TEXT UNIQUE NOT NULL,
            name TEXT NOT NULL,
            short_desc TEXT NOT NULL,
            platform TEXT,
            tags TEXT
        );
    """)
    
    # Insert test data
    await db_connection.execute("""
        INSERT INTO tool (key, name, short_desc, platform, tags)
        VALUES ('test-tool', 'Test Tool', 'A test tool', 'linux', 'network');
    """)
    
    # Run reconciliation
    await run_migration(db_connection, "database/migrations/002_tool_reconcile_pgvector.sql")
    
    # Verify columns are now TEXT[]
    platform_type = await db_connection.fetchval("""
        SELECT data_type FROM information_schema.columns
        WHERE table_name = 'tool' AND column_name = 'platform';
    """)
    assert platform_type == 'ARRAY'
    
    tags_type = await db_connection.fetchval("""
        SELECT data_type FROM information_schema.columns
        WHERE table_name = 'tool' AND column_name = 'tags';
    """)
    assert tags_type == 'ARRAY'
    
    # Verify data was converted correctly
    row = await db_connection.fetchrow("SELECT platform, tags FROM tool WHERE key = 'test-tool';")
    assert row['platform'] == ['linux']
    assert row['tags'] == ['network']


@pytest.mark.asyncio
async def test_reconcile_handles_null_values(db_connection, clean_tool_table):
    """Test that NULL values are converted to empty arrays."""
    # Create table with TEXT columns
    await db_connection.execute("""
        CREATE TABLE tool (
            id BIGSERIAL PRIMARY KEY,
            key TEXT UNIQUE NOT NULL,
            name TEXT NOT NULL,
            short_desc TEXT NOT NULL,
            platform TEXT,
            tags TEXT
        );
    """)
    
    # Insert test data with NULL values
    await db_connection.execute("""
        INSERT INTO tool (key, name, short_desc, platform, tags)
        VALUES ('null-tool', 'Null Tool', 'Tool with nulls', NULL, NULL);
    """)
    
    # Run reconciliation
    await run_migration(db_connection, "database/migrations/002_tool_reconcile_pgvector.sql")
    
    # Verify NULL values became empty arrays
    row = await db_connection.fetchrow("SELECT platform, tags FROM tool WHERE key = 'null-tool';")
    assert row['platform'] == []
    assert row['tags'] == []


@pytest.mark.asyncio
async def test_reconcile_adds_missing_columns(db_connection, clean_tool_table):
    """Test that missing columns are added with correct defaults."""
    # Create minimal table
    await db_connection.execute("""
        CREATE TABLE tool (
            id BIGSERIAL PRIMARY KEY,
            key TEXT UNIQUE NOT NULL,
            name TEXT NOT NULL,
            short_desc TEXT NOT NULL
        );
    """)
    
    # Run reconciliation
    await run_migration(db_connection, "database/migrations/002_tool_reconcile_pgvector.sql")
    
    # Verify all required columns exist
    columns = await db_connection.fetch("""
        SELECT column_name, data_type, column_default
        FROM information_schema.columns
        WHERE table_name = 'tool'
        ORDER BY column_name;
    """)
    
    column_names = {row['column_name'] for row in columns}
    assert 'platform' in column_names
    assert 'tags' in column_names
    assert 'meta' in column_names
    assert 'usage_count' in column_names
    assert 'updated_at' in column_names
    assert 'embedding' in column_names


@pytest.mark.asyncio
async def test_reconcile_creates_indexes(db_connection, clean_tool_table):
    """Test that all required indexes are created."""
    # Create minimal table
    await db_connection.execute("""
        CREATE TABLE tool (
            id BIGSERIAL PRIMARY KEY,
            key TEXT UNIQUE NOT NULL,
            name TEXT NOT NULL,
            short_desc TEXT NOT NULL
        );
    """)
    
    # Run reconciliation
    await run_migration(db_connection, "database/migrations/002_tool_reconcile_pgvector.sql")
    
    # Verify indexes exist
    indexes = await db_connection.fetch("""
        SELECT indexname FROM pg_indexes
        WHERE tablename = 'tool'
        ORDER BY indexname;
    """)
    
    index_names = {row['indexname'] for row in indexes}
    assert 'tool_key_idx' in index_names
    assert 'tool_tags_gin' in index_names
    assert 'tool_platform_gin' in index_names
    assert 'tool_updated_at_idx' in index_names
    assert 'tool_embed_ivff' in index_names


@pytest.mark.asyncio
async def test_reconcile_is_idempotent(db_connection, clean_tool_table):
    """Test that running reconciliation multiple times is safe."""
    # Run base migration
    await run_migration(db_connection, "database/migrations/001_tool_schema_pgvector.sql")
    
    # Insert test data
    await db_connection.execute("""
        INSERT INTO tool (key, name, short_desc, platform, tags)
        VALUES ('idempotent-test', 'Idempotent Test', 'Testing idempotency', 
                ARRAY['linux'], ARRAY['test']);
    """)
    
    # Run reconciliation first time
    await run_migration(db_connection, "database/migrations/002_tool_reconcile_pgvector.sql")
    
    # Get data after first run
    row1 = await db_connection.fetchrow("SELECT * FROM tool WHERE key = 'idempotent-test';")
    
    # Run reconciliation second time
    await run_migration(db_connection, "database/migrations/002_tool_reconcile_pgvector.sql")
    
    # Get data after second run
    row2 = await db_connection.fetchrow("SELECT * FROM tool WHERE key = 'idempotent-test';")
    
    # Verify data is unchanged
    assert row1['key'] == row2['key']
    assert row1['name'] == row2['name']
    assert row1['short_desc'] == row2['short_desc']
    assert row1['platform'] == row2['platform']
    assert row1['tags'] == row2['tags']
    
    # Run reconciliation third time to be extra sure
    await run_migration(db_connection, "database/migrations/002_tool_reconcile_pgvector.sql")
    
    # Verify still works
    row3 = await db_connection.fetchrow("SELECT * FROM tool WHERE key = 'idempotent-test';")
    assert row3['key'] == row1['key']


@pytest.mark.asyncio
async def test_reconcile_preserves_existing_data(db_connection, clean_tool_table):
    """Test that existing data is preserved during reconciliation."""
    # Create table with old schema
    await db_connection.execute("""
        CREATE TABLE tool (
            id BIGSERIAL PRIMARY KEY,
            key TEXT UNIQUE NOT NULL,
            name TEXT NOT NULL,
            short_desc TEXT NOT NULL,
            platform TEXT,
            tags TEXT
        );
    """)
    
    # Insert multiple rows
    test_data = [
        ('tool1', 'Tool One', 'First tool', 'linux', 'network'),
        ('tool2', 'Tool Two', 'Second tool', 'windows', 'security'),
        ('tool3', 'Tool Three', 'Third tool', 'both', 'monitoring'),
    ]
    
    for key, name, desc, platform, tags in test_data:
        await db_connection.execute("""
            INSERT INTO tool (key, name, short_desc, platform, tags)
            VALUES ($1, $2, $3, $4, $5);
        """, key, name, desc, platform, tags)
    
    # Run reconciliation
    await run_migration(db_connection, "database/migrations/002_tool_reconcile_pgvector.sql")
    
    # Verify all data is preserved and converted
    for key, name, desc, platform, tags in test_data:
        row = await db_connection.fetchrow("SELECT * FROM tool WHERE key = $1;", key)
        assert row['name'] == name
        assert row['short_desc'] == desc
        assert row['platform'] == [platform]
        assert row['tags'] == [tags]


@pytest.mark.asyncio
async def test_reconcile_with_already_array_columns(db_connection, clean_tool_table):
    """Test that reconciliation works when columns are already TEXT[]."""
    # Run base migration (creates table with TEXT[] columns)
    await run_migration(db_connection, "database/migrations/001_tool_schema_pgvector.sql")
    
    # Insert test data
    await db_connection.execute("""
        INSERT INTO tool (key, name, short_desc, platform, tags)
        VALUES ('array-test', 'Array Test', 'Testing with arrays', 
                ARRAY['linux', 'windows'], ARRAY['network', 'security']);
    """)
    
    # Run reconciliation (should be no-op for platform/tags)
    await run_migration(db_connection, "database/migrations/002_tool_reconcile_pgvector.sql")
    
    # Verify data is unchanged
    row = await db_connection.fetchrow("SELECT * FROM tool WHERE key = 'array-test';")
    assert row['platform'] == ['linux', 'windows']
    assert row['tags'] == ['network', 'security']


if __name__ == "__main__":
    pytest.main([__file__, "-v"])