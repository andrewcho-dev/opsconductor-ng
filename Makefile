INTENT ?= restart app

.PHONY: selector.health selector.preview selector.logs selector.smoke test.selector compose.rebuild

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
