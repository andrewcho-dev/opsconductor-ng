from shared.telemetry import start_run, run_context

def test_start_run_logs(capfd):
    ctx = start_run(trace_id="t1", user="u")
    out, _ = capfd.readouterr()
    assert '"msg":"run_start"' in out
    assert '"trace_id":"t1"' in out
    assert '"run_id":"' in out
    assert isinstance(ctx["run_id"], str)

def test_run_context_logs_end(capfd):
    with run_context(trace_id="abc"):
        pass
    out, _ = capfd.readouterr()
    assert '"msg":"run_end"' in out and '"trace_id":"abc"' in out
