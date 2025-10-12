# Migration 002: Tool Schema Reconciliation

## Purpose

This migration reconciles any existing `tool` table schema to be compatible with the selector requirements without renaming anything. It ensures that:

1. **pgvector extension** is enabled
2. **Column types** are correct (TEXT → TEXT[] for platform and tags)
3. **Required columns** exist (meta, usage_count, updated_at, embedding)
4. **Indexes** are created for optimal query performance

## Idempotency

This migration is **fully idempotent** and safe to run multiple times:

- ✅ Checks if columns exist before adding them
- ✅ Checks column types before converting them
- ✅ Uses `IF NOT EXISTS` for all index creation
- ✅ Preserves existing data during type conversions
- ✅ Handles NULL values gracefully (converts to empty arrays)

## What It Does

### 1. Extension Setup
```sql
CREATE EXTENSION IF NOT EXISTS vector;
```
Ensures pgvector is available for embedding storage.

### 2. Column Type Reconciliation

#### Tags Column
- **If TEXT**: Converts to TEXT[] using `ARRAY[tags]` for non-NULL values
- **If missing**: Adds as TEXT[] with default `'{}'::text[]`
- **If already TEXT[]**: No action needed

#### Platform Column
- **If TEXT**: Converts to TEXT[] using `ARRAY[platform]` for non-NULL values
- **If missing**: Adds as TEXT[] with default `'{}'::text[]`
- **If already TEXT[]**: No action needed

### 3. Additional Columns

Adds missing columns with appropriate defaults:

| Column | Type | Default | Purpose |
|--------|------|---------|---------|
| `meta` | jsonb | `'{}'::jsonb` | Arbitrary metadata storage |
| `usage_count` | integer | `0` | Track tool usage frequency |
| `updated_at` | timestamptz | `now()` | Last update timestamp |
| `embedding` | vector(128) | NULL | 128-dimensional embedding vector |

### 4. Index Creation

Creates indexes for optimal query performance:

| Index | Type | Purpose |
|-------|------|---------|
| `tool_key_idx` | B-tree | Fast lookup by unique key |
| `tool_tags_gin` | GIN | Array containment queries on tags |
| `tool_platform_gin` | GIN | Array containment queries on platform |
| `tool_updated_at_idx` | B-tree | Temporal queries and sorting |
| `tool_embed_ivff` | IVFFlat | Vector similarity search (cosine) |

## Usage

### Via Make Target (Recommended)

```bash
make selector.reconcile
```

This runs the migration inside the PostgreSQL container with proper credentials.

### Manual Execution

```bash
docker compose exec -T postgres psql -U $POSTGRES_USER -d $POSTGRES_DB < database/migrations/002_tool_reconcile_pgvector.sql
```

### Direct psql

```bash
psql -U postgres -d opsconductor < database/migrations/002_tool_reconcile_pgvector.sql
```

## Migration Scenarios

### Scenario 1: Fresh Database
If the `tool` table doesn't exist yet, run the base migration first:
```bash
make selector.migrate      # Creates table with correct schema
make selector.reconcile    # No-op, but safe to run
```

### Scenario 2: Existing Table with TEXT Columns
If you have an existing `tool` table with `platform TEXT` and `tags TEXT`:
```bash
make selector.reconcile    # Converts TEXT → TEXT[], preserves data
```

**Before:**
```sql
platform | tags
---------|----------
'linux'  | 'network'
NULL     | 'security'
```

**After:**
```sql
platform      | tags
--------------|-------------
['linux']     | ['network']
[]            | ['security']
```

### Scenario 3: Partial Schema
If you have some columns but not all:
```bash
make selector.reconcile    # Adds missing columns, converts types
```

### Scenario 4: Already Reconciled
If you've already run this migration:
```bash
make selector.reconcile    # Safe no-op, no changes made
```

## Testing

Run the comprehensive test suite:

```bash
# Install test dependencies
pip install pytest pytest-asyncio asyncpg

# Run tests
pytest database/test_002_reconcile.py -v
```

### Test Coverage

The test suite verifies:

1. ✅ **Creates missing table** - Works with fresh database
2. ✅ **Converts TEXT to TEXT[]** - Handles old schema
3. ✅ **Handles NULL values** - Converts to empty arrays
4. ✅ **Adds missing columns** - Ensures all required columns exist
5. ✅ **Creates indexes** - All indexes are created
6. ✅ **Is idempotent** - Safe to run multiple times
7. ✅ **Preserves data** - No data loss during conversion
8. ✅ **Works with arrays** - No-op when already correct type

## Integration with Task 04

This migration ensures compatibility with:

- **tools_upsert.py** - Expects TEXT[] for platform and tags
- **selector/dao.py** - Queries using array operators (`&&`, `@>`)
- **selector/embeddings.py** - Stores 128-dimensional vectors

## Troubleshooting

### Error: "column already exists"
This shouldn't happen due to `IF NOT EXISTS` checks, but if it does:
```sql
-- Check current schema
\d tool
```

### Error: "cannot cast type text to text[]"
This shouldn't happen due to the CASE statement in the migration, but if it does:
```sql
-- Manual conversion
ALTER TABLE tool ALTER COLUMN tags TYPE text[] 
  USING CASE WHEN tags IS NULL THEN '{}'::text[] ELSE ARRAY[tags] END;
```

### Error: "index already exists"
This is expected and safe - the migration uses `IF NOT EXISTS`.

### Verify Migration Success
```sql
-- Check column types
SELECT column_name, data_type, column_default
FROM information_schema.columns
WHERE table_name = 'tool'
ORDER BY column_name;

-- Check indexes
SELECT indexname, indexdef
FROM pg_indexes
WHERE tablename = 'tool'
ORDER BY indexname;

-- Check data conversion
SELECT key, platform, tags FROM tool LIMIT 5;
```

## Performance Considerations

### Type Conversion
- **Small tables (<1000 rows)**: Instant
- **Medium tables (1000-10000 rows)**: < 1 second
- **Large tables (>10000 rows)**: May take several seconds

The migration uses `ALTER TABLE ... USING` which rewrites the table. For very large tables, consider:
1. Running during maintenance window
2. Monitoring table locks
3. Testing on a copy first

### Index Creation
The IVFFlat index creation time depends on table size:
- **Empty table**: Instant
- **<1000 rows**: < 1 second
- **1000-10000 rows**: 1-5 seconds
- **>10000 rows**: May take longer

After migration, run `ANALYZE tool;` to update statistics (the Make target does this automatically).

## Rollback

If you need to rollback (not recommended):

```sql
-- Convert arrays back to text (loses multi-value data!)
ALTER TABLE tool ALTER COLUMN platform TYPE text 
  USING CASE WHEN array_length(platform, 1) > 0 THEN platform[1] ELSE NULL END;

ALTER TABLE tool ALTER COLUMN tags TYPE text 
  USING CASE WHEN array_length(tags, 1) > 0 THEN tags[1] ELSE NULL END;

-- Drop added columns
ALTER TABLE tool DROP COLUMN IF EXISTS meta;
ALTER TABLE tool DROP COLUMN IF EXISTS usage_count;
ALTER TABLE tool DROP COLUMN IF EXISTS updated_at;
ALTER TABLE tool DROP COLUMN IF EXISTS embedding;

-- Drop indexes
DROP INDEX IF EXISTS tool_key_idx;
DROP INDEX IF EXISTS tool_tags_gin;
DROP INDEX IF EXISTS tool_platform_gin;
DROP INDEX IF EXISTS tool_updated_at_idx;
DROP INDEX IF EXISTS tool_embed_ivff;
```

**Warning**: Rollback will lose data if tools have multiple platforms or tags!

## Next Steps

After running this migration:

1. **Populate tools**: `make tools.sync`
2. **Verify data**: `SELECT * FROM tool LIMIT 5;`
3. **Test selector**: `make selector.smoke`
4. **Run integration tests**: `make test.selector`

## References

- **Task 04**: Tool Catalog Upsert with YAML Definitions
- **Migration 001**: Initial tool schema creation
- **selector/dao.py**: ToolDAO implementation
- **tools/tools_upsert.py**: Tool population script