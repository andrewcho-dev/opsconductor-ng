# Database Migration Guide

## Quick Reference

### Available Migrations

| Migration | File | Purpose | Make Target |
|-----------|------|---------|-------------|
| 001 | `001_tool_schema_pgvector.sql` | Create tool table with pgvector | `make selector.migrate` |
| 002 | `002_tool_reconcile_pgvector.sql` | Reconcile existing schema | `make selector.reconcile` |

### Common Workflows

#### Fresh Database Setup
```bash
# 1. Create tool table
make selector.migrate

# 2. Populate tools from database
# (Tools are managed through capability management system)

# 3. Verify
docker compose exec -T postgres psql -U $POSTGRES_USER -d $POSTGRES_DB -c "SELECT COUNT(*) FROM tool;"
```

#### Existing Database Reconciliation
```bash
# 1. Reconcile schema (idempotent)
make selector.reconcile

# 2. Update tools
# (Tools are managed through capability management system)

# 3. Verify
docker compose exec -T postgres psql -U $POSTGRES_USER -d $POSTGRES_DB -c "\d tool"
```

#### Development Workflow
```bash
# 1. Run migrations
make selector.migrate
make selector.reconcile

# 2. Tools are managed through capability management system

# 3. Test selector
make selector.smoke
```

## Migration Details

### Migration 001: Tool Schema Creation

**Purpose**: Create the `tool` table with pgvector support

**What it does**:
- Creates `tool` table with correct schema
- Adds pgvector extension
- Creates indexes for optimal performance

**When to use**:
- Fresh database setup
- Initial deployment
- After dropping the tool table

**Idempotent**: ✅ Yes (uses `IF NOT EXISTS`)

**Command**:
```bash
make selector.migrate
```

### Migration 002: Schema Reconciliation

**Purpose**: Reconcile existing `tool` table to selector requirements

**What it does**:
- Converts TEXT columns to TEXT[] (platform, tags)
- Adds missing columns (meta, usage_count, updated_at, embedding)
- Creates missing indexes
- Handles NULL values gracefully

**When to use**:
- Existing database with old schema
- After schema changes
- To ensure compatibility

**Idempotent**: ✅ Yes (checks before modifying)

**Command**:
```bash
make selector.reconcile
```

## Testing

### Run Migration Tests
```bash
# Install dependencies
pip install pytest pytest-asyncio asyncpg

# Run tests for migration 002
pytest database/test_002_reconcile.py -v

# Run all database tests
pytest database/ -v
```

### Verify Migration
```bash
# Run verification script
./database/verify_002_reconcile.sh

# Check schema manually
docker compose exec -T postgres psql -U $POSTGRES_USER -d $POSTGRES_DB -c "\d tool"

# Check data
docker compose exec -T postgres psql -U $POSTGRES_USER -d $POSTGRES_DB -c "SELECT * FROM tool LIMIT 5;"
```

## Troubleshooting

### Error: "relation 'tool' does not exist"
**Solution**: Run the base migration first
```bash
make selector.migrate
```

### Error: "extension 'vector' does not exist"
**Solution**: Install pgvector in PostgreSQL
```bash
docker compose exec -T postgres psql -U $POSTGRES_USER -d $POSTGRES_DB -c "CREATE EXTENSION vector;"
```

### Error: "column already exists"
**Solution**: This shouldn't happen with idempotent migrations, but if it does:
```bash
# Check current schema
docker compose exec -T postgres psql -U $POSTGRES_USER -d $POSTGRES_DB -c "\d tool"

# Run reconciliation (it will skip existing columns)
make selector.reconcile
```

### Error: "cannot cast type text to text[]"
**Solution**: Run the reconciliation migration which handles this conversion
```bash
make selector.reconcile
```

### Performance Issues
**Solution**: Run ANALYZE after migrations
```bash
docker compose exec -T postgres psql -U $POSTGRES_USER -d $POSTGRES_DB -c "ANALYZE tool;"
```

## Manual Migration

If you need to run migrations manually:

### Using psql inside container
```bash
docker compose exec -T postgres psql -U $POSTGRES_USER -d $POSTGRES_DB < database/migrations/001_tool_schema_pgvector.sql
docker compose exec -T postgres psql -U $POSTGRES_USER -d $POSTGRES_DB < database/migrations/002_tool_reconcile_pgvector.sql
```

### Using psql from host
```bash
psql -h localhost -U postgres -d opsconductor < database/migrations/001_tool_schema_pgvector.sql
psql -h localhost -U postgres -d opsconductor < database/migrations/002_tool_reconcile_pgvector.sql
```

## Schema Verification

### Check Table Structure
```sql
-- View table definition
\d tool

-- View column details
SELECT column_name, data_type, column_default
FROM information_schema.columns
WHERE table_name = 'tool'
ORDER BY ordinal_position;
```

### Check Indexes
```sql
-- View all indexes
\di

-- View indexes for tool table
SELECT indexname, indexdef
FROM pg_indexes
WHERE tablename = 'tool'
ORDER BY indexname;
```

### Check Data
```sql
-- Count rows
SELECT COUNT(*) FROM tool;

-- View sample data
SELECT key, name, platform, tags FROM tool LIMIT 5;

-- Check for NULL embeddings
SELECT COUNT(*) FROM tool WHERE embedding IS NULL;
```

## Best Practices

1. **Always run migrations in order**: 001 → 002
2. **Test migrations on a copy first**: Use a test database
3. **Backup before migrations**: Especially for production
4. **Run ANALYZE after migrations**: Updates query planner statistics
5. **Verify after migrations**: Check schema and data
6. **Use Make targets**: They handle container execution correctly
7. **Check logs**: Monitor for errors during migration

## Migration Checklist

- [ ] Backup database (if production)
- [ ] Run verification script: `./database/verify_002_reconcile.sh`
- [ ] Run migration: `make selector.reconcile`
- [ ] Check for errors in output
- [ ] Verify schema: `\d tool`
- [ ] Verify data: `SELECT * FROM tool LIMIT 5;`
- [ ] Run tests: `pytest database/test_002_reconcile.py -v`
- [ ] Tools managed through capability management system
- [ ] Test selector: `make selector.smoke`

## Rollback

If you need to rollback (not recommended):

### Rollback Migration 002
```sql
-- Convert arrays back to text (WARNING: loses multi-value data!)
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

## References

- **Task 04**: Tool Catalog Upsert with YAML Definitions
- **Migration 001**: `database/migrations/001_tool_schema_pgvector.sql`
- **Migration 002**: `database/migrations/002_tool_reconcile_pgvector.sql`
- **Migration 002 README**: `database/migrations/README_002_RECONCILE.md`
- **Test Suite**: `database/test_002_reconcile.py`
- **Verification Script**: `database/verify_002_reconcile.sh`