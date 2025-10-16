"""JSON logging utilities for OpsConductor NG."""

import json
import sys
from datetime import datetime, timezone
from typing import Any


def json_log(message: str, **fields: Any) -> None:
    """Write a JSON-formatted log line to stdout.
    
    Automatically injects trace_id and span_id from OpenTelemetry context if available.
    
    Args:
        message: The log message
        **fields: Additional fields to include in the log entry
    """
    # Try to inject OpenTelemetry trace context
    try:
        from opentelemetry import trace
        span = trace.get_current_span()
        if span and span.is_recording():
            ctx = span.get_span_context()
            if ctx.is_valid:
                # Only add if not already present in fields
                if "trace_id" not in fields:
                    fields["trace_id"] = format(ctx.trace_id, "032x")
                if "span_id" not in fields:
                    fields["span_id"] = format(ctx.span_id, "016x")
    except (ImportError, Exception):
        # OpenTelemetry not available or error getting context, continue without it
        pass
    
    log_entry = {
        "ts": datetime.now(timezone.utc).isoformat(),
        "level": fields.pop("level", "INFO"),
        "msg": message,
        **fields
    }
    print(json.dumps(log_entry), file=sys.stdout, flush=True)