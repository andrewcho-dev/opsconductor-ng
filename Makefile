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
# --- selector helpers ---
DB_SERVICE ?= postgres
POSTGRES_USER ?= opsconductor
POSTGRES_DB ?= opsconductor

selector.seed:
	@CID=$$(docker compose ps -q $(DB_SERVICE)); \
	docker run --rm --network=container:$$CID -v "$$(pwd)":/work:ro -w /work python:3.11 bash -lc '\
	  python -m venv /tmp/venv && . /tmp/venv/bin/activate && \
	  pip install -q asyncpg pyyaml && \
	  python tools/tools_upsert.py --glob "config/tools/**/*.yaml" --dsn "postgresql://$(POSTGRES_USER)@127.0.0.1:5432/$(POSTGRES_DB)"'

selector.index:
	docker compose exec -T $(DB_SERVICE) psql -U $(POSTGRES_USER) -d $(POSTGRES_DB) -c "DROP INDEX IF EXISTS tool_embed_ivff;"
	docker compose exec -T $(DB_SERVICE) psql -U $(POSTGRES_USER) -d $(POSTGRES_DB) -c "CREATE INDEX tool_embed_ivff ON tool USING ivfflat (embedding vector_cosine_ops) WITH (lists = 100);"
	docker compose exec -T $(DB_SERVICE) psql -U $(POSTGRES_USER) -d $(POSTGRES_DB) -c "ANALYZE tool;"

selector.smoke:
	@python3 - <<'PY'
import json,sys,urllib.request
def ok(url):
  try:
    with urllib.request.urlopen(url, timeout=5) as r:
      j=json.load(r)
      assert isinstance(j.get("results"), list) and len(j["results"])>=1
      return True
  except Exception as e:
    print("FAIL:", url, e); return False
ok1=ok("http://localhost:8010/api/selector/search?query=network&platform=linux&k=3")
ok2=ok("http://localhost:8010/api/selector/search?query=windows%20networking&platform=windows&k=3")
if not (ok1 and ok2): sys.exit(1)
print("selector.smoke OK")
PY

selector.all: selector.seed selector.index selector.smoke
