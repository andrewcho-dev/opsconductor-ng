#!/bin/bash
# Migrate all tools to database using Docker network

echo "=========================================="
echo "Migrating All Tools to Database"
echo "=========================================="

# Run migration script with proper database connection
docker run --rm \
  --network opsconductor-ng_opsconductor \
  -v /home/opsconductor/opsconductor-ng:/app \
  -w /app \
  -e DATABASE_URL="postgresql://opsconductor:opsconductor_secure_2024@postgres:5432/opsconductor" \
  python:3.11-slim \
  bash -c "
    pip install -q psycopg2-binary pyyaml &&
    python3 scripts/migrate_tools_to_db.py --all
  "

echo ""
echo "=========================================="
echo "Migration Complete!"
echo "=========================================="