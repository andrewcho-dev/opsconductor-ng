#!/bin/bash

# Check database schema
docker run --rm \
  --network opsconductor-ng_opsconductor \
  -e PGPASSWORD=opsconductor_secure_2024 \
  postgres:17-alpine \
  psql -h postgres -U opsconductor -d opsconductor -c "\dt tool_catalog.*"