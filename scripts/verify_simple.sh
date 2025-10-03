#!/bin/bash
docker run --rm \
  --network opsconductor-ng_opsconductor \
  -v /home/opsconductor/opsconductor-ng:/app \
  -w /app \
  -e DATABASE_URL=postgresql://opsconductor:opsconductor_secure_2024@postgres:5432/opsconductor \
  python:3.11-slim \
  bash -c "pip install -q psycopg2-binary && python3 scripts/verify_db_tools_simple.py"