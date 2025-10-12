INTENT ?= restart app
dc ?= docker compose
DB_SERVICE ?= postgres
MIGRATIONS_DIR ?= /docker-entrypoint-initdb.d

.PHONY: selector.health selector.preview selector.logs selector.smoke test.selector compose.rebuild selector.migrate selector.reconcile tools.seed tools.sync

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

tools.seed:
	@echo "Validating tool definitions (dry-run)..."
	@$(dc) exec -T $(DB_SERVICE) python3 tools/tools_upsert.py --glob "config/tools/**/*.yaml" --dry-run

tools.sync:
	@echo "Syncing tool definitions to database..."
	@$(dc) exec -T $(DB_SERVICE) python3 tools/tools_upsert.py --glob "config/tools/**/*.yaml"
