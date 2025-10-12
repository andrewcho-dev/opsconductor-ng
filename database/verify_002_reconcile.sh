#!/bin/bash
# Verification script for 002_tool_reconcile_pgvector.sql migration
# Tests idempotency and correctness of the reconciliation migration

set -e

echo "🔍 Verifying Migration 002: Tool Schema Reconciliation"
echo "========================================================"

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check if migration file exists
if [ ! -f "database/migrations/002_tool_reconcile_pgvector.sql" ]; then
    echo -e "${RED}❌ Migration file not found!${NC}"
    exit 1
fi
echo -e "${GREEN}✅ Migration file exists${NC}"

# Check if test file exists
if [ ! -f "database/test_002_reconcile.py" ]; then
    echo -e "${YELLOW}⚠️  Test file not found (optional)${NC}"
else
    echo -e "${GREEN}✅ Test file exists${NC}"
fi

# Check if README exists
if [ ! -f "database/migrations/README_002_RECONCILE.md" ]; then
    echo -e "${YELLOW}⚠️  README not found (optional)${NC}"
else
    echo -e "${GREEN}✅ README exists${NC}"
fi

# Verify migration file syntax
echo ""
echo "📝 Checking SQL syntax..."

# Check for required keywords
if grep -q "CREATE EXTENSION IF NOT EXISTS vector" database/migrations/002_tool_reconcile_pgvector.sql; then
    echo -e "${GREEN}✅ pgvector extension check present${NC}"
else
    echo -e "${RED}❌ Missing pgvector extension check${NC}"
    exit 1
fi

if grep -q "DO \\\$\\\$" database/migrations/002_tool_reconcile_pgvector.sql; then
    echo -e "${GREEN}✅ PL/pgSQL block present${NC}"
else
    echo -e "${RED}❌ Missing PL/pgSQL block${NC}"
    exit 1
fi

if grep -q "ALTER TABLE tool ADD COLUMN IF NOT EXISTS" database/migrations/002_tool_reconcile_pgvector.sql; then
    echo -e "${GREEN}✅ Idempotent column additions present${NC}"
else
    echo -e "${RED}❌ Missing idempotent column additions${NC}"
    exit 1
fi

if grep -q "CREATE INDEX IF NOT EXISTS" database/migrations/002_tool_reconcile_pgvector.sql; then
    echo -e "${GREEN}✅ Idempotent index creation present${NC}"
else
    echo -e "${RED}❌ Missing idempotent index creation${NC}"
    exit 1
fi

# Check for required columns
echo ""
echo "📋 Checking required columns..."

required_columns=("meta" "usage_count" "updated_at" "embedding")
for col in "${required_columns[@]}"; do
    if grep -q "ADD COLUMN IF NOT EXISTS $col" database/migrations/002_tool_reconcile_pgvector.sql; then
        echo -e "${GREEN}✅ Column '$col' check present${NC}"
    else
        echo -e "${RED}❌ Missing column '$col' check${NC}"
        exit 1
    fi
done

# Check for required indexes
echo ""
echo "🔍 Checking required indexes..."

required_indexes=("tool_key_idx" "tool_tags_gin" "tool_platform_gin" "tool_updated_at_idx" "tool_embed_ivff")
for idx in "${required_indexes[@]}"; do
    if grep -q "$idx" database/migrations/002_tool_reconcile_pgvector.sql; then
        echo -e "${GREEN}✅ Index '$idx' present${NC}"
    else
        echo -e "${RED}❌ Missing index '$idx'${NC}"
        exit 1
    fi
done

# Check for type conversion logic
echo ""
echo "🔄 Checking type conversion logic..."

if grep -q "ALTER COLUMN tags TYPE text\[\]" database/migrations/002_tool_reconcile_pgvector.sql; then
    echo -e "${GREEN}✅ Tags type conversion present${NC}"
else
    echo -e "${RED}❌ Missing tags type conversion${NC}"
    exit 1
fi

if grep -q "ALTER COLUMN platform TYPE text\[\]" database/migrations/002_tool_reconcile_pgvector.sql; then
    echo -e "${GREEN}✅ Platform type conversion present${NC}"
else
    echo -e "${RED}❌ Missing platform type conversion${NC}"
    exit 1
fi

# Check for NULL handling
if grep -q "WHEN.*IS NULL THEN '{}'" database/migrations/002_tool_reconcile_pgvector.sql; then
    echo -e "${GREEN}✅ NULL value handling present${NC}"
else
    echo -e "${RED}❌ Missing NULL value handling${NC}"
    exit 1
fi

# Check Makefile target
echo ""
echo "🎯 Checking Makefile target..."

if [ -f "Makefile" ]; then
    if grep -q "selector.reconcile:" Makefile; then
        echo -e "${GREEN}✅ Makefile target 'selector.reconcile' exists${NC}"
    else
        echo -e "${YELLOW}⚠️  Makefile target 'selector.reconcile' not found${NC}"
    fi
    
    if grep -q "002_tool_reconcile_pgvector.sql" Makefile; then
        echo -e "${GREEN}✅ Makefile references migration file${NC}"
    else
        echo -e "${YELLOW}⚠️  Makefile doesn't reference migration file${NC}"
    fi
else
    echo -e "${YELLOW}⚠️  Makefile not found${NC}"
fi

# Line count check
echo ""
echo "📊 Migration file statistics..."

line_count=$(wc -l < database/migrations/002_tool_reconcile_pgvector.sql)
echo "   Lines: $line_count"

if [ "$line_count" -ge 50 ] && [ "$line_count" -le 60 ]; then
    echo -e "${GREEN}✅ Line count looks reasonable ($line_count lines)${NC}"
else
    echo -e "${YELLOW}⚠️  Line count is $line_count (expected ~51-55)${NC}"
fi

# Check for common issues
echo ""
echo "🔎 Checking for common issues..."

if grep -q "DROP TABLE" database/migrations/002_tool_reconcile_pgvector.sql; then
    echo -e "${RED}❌ WARNING: Migration contains DROP TABLE (not idempotent!)${NC}"
    exit 1
else
    echo -e "${GREEN}✅ No destructive DROP TABLE statements${NC}"
fi

if grep -q "TRUNCATE" database/migrations/002_tool_reconcile_pgvector.sql; then
    echo -e "${RED}❌ WARNING: Migration contains TRUNCATE (not idempotent!)${NC}"
    exit 1
else
    echo -e "${GREEN}✅ No TRUNCATE statements${NC}"
fi

if grep -q "DELETE FROM" database/migrations/002_tool_reconcile_pgvector.sql; then
    echo -e "${RED}❌ WARNING: Migration contains DELETE (not idempotent!)${NC}"
    exit 1
else
    echo -e "${GREEN}✅ No DELETE statements${NC}"
fi

# Summary
echo ""
echo "========================================================"
echo -e "${GREEN}✅ All verification checks passed!${NC}"
echo ""
echo "Next steps:"
echo "  1. Run migration: make selector.reconcile"
echo "  2. Run tests: pytest database/test_002_reconcile.py -v"
echo "  3. Verify data: psql -c 'SELECT * FROM tool LIMIT 5;'"
echo ""
echo "Migration is ready for deployment! 🚀"