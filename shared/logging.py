"""JSON logging utilities for OpsConductor NG."""

import json
import sys
from datetime import datetime, timezone
from typing import Any


def json_log(message: str, **fields: Any) -> None:
    """Write a JSON-formatted log line to stdout.
    
    Args:
        message: The log message
        **fields: Additional fields to include in the log entry
    """
    log_entry = {
        "ts": datetime.now(timezone.utc).isoformat(),
        "level": fields.pop("level", "INFO"),
        "msg": message,
        **fields
    }
    print(json.dumps(log_entry), file=sys.stdout, flush=True)