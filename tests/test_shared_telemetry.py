import json
from shared.telemetry import start_run, run_context

def _parse_lines(out: str):
    return [json.loads(line) for line in out.strip().splitlines() if line.strip()]

def test_start_run_logs(capfd):
    ctx = start_run(trace_id="t1", user="u")
    out, _ = capfd.readouterr()
    recs = _parse_lines(out)
    assert recs[-1]["msg"] == "run_start"
    assert recs[-1]["trace_id"] == "t1"
    assert recs[-1]["run_id"].startswith("run_")
    assert isinstance(ctx["run_id"], str)

def test_run_context_logs_end(capfd):
    with run_context(trace_id="abc"):
        pass
    out, _ = capfd.readouterr()
    recs = _parse_lines(out)
    # Expect two lines: run_start then run_end
    assert any(r.get("msg") == "run_start" and r.get("trace_id") == "abc" for r in recs)
    assert any(r.get("msg") == "run_end"   and r.get("trace_id") == "abc" for r in recs)
