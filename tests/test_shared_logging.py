import json
from shared.logging import json_log

def test_json_log_smoke(capfd):
    json_log("hello", trace_id="t1", level="DEBUG")
    out, _ = capfd.readouterr()
    # take the last line and parse JSON
    rec = json.loads(out.strip().splitlines()[-1])
    assert rec["msg"] == "hello"
    assert rec["trace_id"] == "t1"
    assert rec["level"] in ("DEBUG", "INFO")  # allow defaulting
