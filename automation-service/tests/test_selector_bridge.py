import os, types, importlib, json
import pytest

MODULE_PATH = "stage_a.selector_bridge"

class Stub:
    def __init__(self, name, desc):
        self.tool_name = name
        self.description = desc

@pytest.mark.asyncio
async def test_dedupe_and_cap(monkeypatch):
    os.environ["DATABASE_URL"] = "postgres://test:test@localhost:5432/testdb"
    os.environ["ALWAYS_INCLUDE_TOOLS"] = "asset-query,service-status,asset-query"

    sb = importlib.import_module(MODULE_PATH)

    async def fake_connect(dsn):
        class DummyConn:
            async def close(self): pass
        return DummyConn()
    monkeypatch.setattr(sb, "asyncpg", types.SimpleNamespace(connect=fake_connect))

    async def fake_candidate_tools_from_intent(conn, user_intent, k):
        return [
            Stub("service-status", "dup"),
            Stub("network-ping", "ping"),
            Stub("asset-query", "cmdb"),
            Stub("network-ping", "ping longer"),
            Stub("deploy", "run deployment"),
        ]
    monkeypatch.setattr(sb, "candidate_tools_from_intent", fake_candidate_tools_from_intent)

    out = await sb.select_candidates_for_prompt("restart app", k=3, trace_id="T-123")
    names = [o["name"] for o in out]
    assert names == ["asset-query", "service-status", "network-ping"]
    assert len(out) == 3

@pytest.mark.asyncio
async def test_json_log_line(monkeypatch, caplog):
    os.environ["DATABASE_URL"] = "postgres://test:test@localhost:5432/testdb"
    os.environ["ALWAYS_INCLUDE_TOOLS"] = ""

    sb = importlib.import_module(MODULE_PATH)

    async def fake_connect(dsn):
        class DummyConn:
            async def close(self): pass
        return DummyConn()
    monkeypatch.setattr(sb, "asyncpg", types.SimpleNamespace(connect=fake_connect))

    async def fake_candidate_tools_from_intent(conn, user_intent, k):
        return [Stub("a","A"), Stub("b","B")]
    monkeypatch.setattr(sb, "candidate_tools_from_intent", fake_candidate_tools_from_intent)

    with caplog.at_level("INFO"):
        out = await sb.select_candidates_for_prompt("restart app", k=2, trace_id="TRACE-1")
    found = False
    for rec in caplog.records:
        try:
            data = json.loads(rec.getMessage())
            if data.get("event") == "selector_candidates":
                assert data["trace_id"] == "TRACE-1"
                assert data["k_requested"] == 2
                assert data["k_returned"] == 2
                assert data["tool_names"] == ["a","b"]
                found = True
                break
        except Exception:
            pass
    assert found, "selector_candidates JSON log line not found"
