from contextlib import contextmanager
from typing import Optional, Dict
from .ids import new_trace_id, new_run_id
from .logging import json_log

def start_run(trace_id: Optional[str] = None, **fields) -> Dict[str, str]:
    """
    Emit 'run_start' JSON log and return {"trace_id","run_id"} context.
    """
    tid = trace_id or new_trace_id()
    rid = new_run_id()
    json_log("run_start", trace_id=tid, run_id=rid, **fields)
    return {"trace_id": tid, "run_id": rid}

@contextmanager
def run_context(trace_id: Optional[str] = None, **fields):
    """
    Usage:
        with run_context(user="andrew"):
            ... do work ...
    Emits 'run_start' on enter and 'run_end' on exit.
    """
    ctx = start_run(trace_id=trace_id, **fields)
    try:
        yield ctx
    finally:
        json_log("run_end", **ctx)
