#!/bin/bash

# Run verification script inside Docker container with access to postgres
docker run --rm \
  --network opsconductor-ng_opsconductor \
  -v /home/opsconductor/opsconductor-ng:/app \
  -w /app \
  -e DATABASE_URL=postgresql://opsconductor:opsconductor@postgres:5432/opsconductor \
  python:3.11-slim \
  bash -c "pip install -q psycopg2-binary pyyaml && python3 scripts/verify_tool_catalog.py"