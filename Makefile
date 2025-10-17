INTENT ?= restart app
dc ?= docker compose
DB_SERVICE ?= postgres
MIGRATIONS_DIR ?= /docker-entrypoint-initdb.d

.PHONY: selector.health selector.preview selector.logs selector.smoke test.selector compose.rebuild selector.migrate selector.reconcile

selector.health:
	@docker compose exec -T automation-service python scripts/selector_healthz.py

selector.preview:
	@docker compose exec -T automation-service python scripts/preview_selector_from_executor.py "$(INTENT)"

selector.logs:
	@docker compose logs --since=10m automation-service | egrep 'selector_candidates|selector_bridge_call|selector_healthz' || true

selector.smoke:
	@docker compose exec -T automation-service bash -lc 'scripts/smoke_selector.sh "$(INTENT)"'

test.selector:
	@docker compose exec -T automation-service sh -lc 'python -m pip install -q pytest pytest-asyncio asyncpg && python -m pytest -q db selector tests'

compose.rebuild:
	@docker compose up -d --build automation-service

selector.migrate:
	@echo "Running tool schema migration inside $(DB_SERVICE) container..."
	@$(dc) exec -T $(DB_SERVICE) psql -U $$POSTGRES_USER -d $$POSTGRES_DB < database/migrations/001_tool_schema_pgvector.sql
	@$(dc) exec -T $(DB_SERVICE) psql -U $$POSTGRES_USER -d $$POSTGRES_DB -c "ANALYZE tool;"
	@echo "Migration complete."

selector.reconcile:
	@echo "Running tool schema reconciliation inside $(DB_SERVICE) container..."
	@$(dc) exec -T $(DB_SERVICE) psql -U $$POSTGRES_USER -d $$POSTGRES_DB < database/migrations/002_tool_reconcile_pgvector.sql
	@$(dc) exec -T $(DB_SERVICE) psql -U $$POSTGRES_USER -d $$POSTGRES_DB -c "ANALYZE tool;"
	@echo "Reconciliation complete."


# --- selector helpers ---
DB_SERVICE ?= postgres
POSTGRES_USER ?= opsconductor
POSTGRES_DB ?= opsconductor



selector.index:
	docker compose exec -T $(DB_SERVICE) psql -U $(POSTGRES_USER) -d $(POSTGRES_DB) -c "DROP INDEX IF EXISTS tool_embed_ivff;"
	docker compose exec -T $(DB_SERVICE) psql -U $(POSTGRES_USER) -d $(POSTGRES_DB) -c "CREATE INDEX tool_embed_ivff ON tool USING ivfflat (embedding vector_cosine_ops) WITH (lists = 100);"
	docker compose exec -T $(DB_SERVICE) psql -U $(POSTGRES_USER) -d $(POSTGRES_DB) -c "ANALYZE tool;"

selector.smoke:
	@echo "Running selector v3 smoke tests..."
	@docker compose exec -T automation-service python -m pytest tests/selector/test_smoke.py -v || \
	SELECTOR_URL=http://localhost:3003 python3 automation-service/tests/selector/test_smoke.py

smoke-automation-service:
	@echo "Running automation-service smoke tests..."
	@SELECTOR_URL=http://localhost:3003 python3 automation-service/tests/selector/test_smoke.py

selector.all: selector.index selector.smoke
