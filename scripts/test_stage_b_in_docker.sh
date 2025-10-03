#!/bin/bash

# Test Stage B with new tools inside Docker container
docker run --rm \
  --network opsconductor-ng_opsconductor \
  -v /home/opsconductor/opsconductor-ng:/app \
  -w /app \
  -e DATABASE_URL=postgresql://opsconductor:opsconductor_secure_2024@postgres:5432/opsconductor \
  -e PYTHONPATH=/app \
  python:3.11-slim \
  bash -c "pip install -q psycopg2-binary pyyaml pydantic && python3 scripts/test_stage_b_with_new_tools.py"