DB_SERVICE ?= postgres
POSTGRES_USER ?= opsconductor
POSTGRES_DB ?= opsconductor

.PHONY: seed index smoke all

seed:
	@CID=$$(docker compose ps -q $(DB_SERVICE)); \
	docker run --rm --network=container:$$CID -v "$$(pwd)":/work:ro -w /work python:3.11 bash -lc '\
	  python -m venv /tmp/venv && . /tmp/venv/bin/activate && \
	  pip install -q asyncpg pyyaml && \
	  python tools/tools_upsert.py --glob "config/tools/**/*.yaml" --dsn "postgresql://$(POSTGRES_USER)@127.0.0.1:5432/$(POSTGRES_DB)"'

index:
	docker compose exec -T $(DB_SERVICE) psql -U $(POSTGRES_USER) -d $(POSTGRES_DB) -c "DROP INDEX IF EXISTS tool_embed_ivff;"
	docker compose exec -T $(DB_SERVICE) psql -U $(POSTGRES_USER) -d $(POSTGRES_DB) -c "CREATE INDEX tool_embed_ivff ON tool USING ivfflat (embedding vector_cosine_ops) WITH (lists = 100);"
	docker compose exec -T $(DB_SERVICE) psql -U $(POSTGRES_USER) -d $(POSTGRES_DB) -c "ANALYZE tool;"

smoke:
	@curl -sS "http://localhost:8010/api/selector/search?query=network&platform=linux&k=3" | grep -q '"results"' || (echo "FAIL: linux query"; exit 1)
	@curl -sS "http://localhost:8010/api/selector/search?query=windows%20networking&platform=windows&k=3" | grep -q '"results"' || (echo "FAIL: windows query"; exit 1)
	@echo "selector.smoke OK"

all: seed index smoke
