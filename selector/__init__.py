"""
Tool selection and candidate generation.

Default: stub mode (no DB). To use the DB-backed selector set BOTH:
  USE_SELECTOR_DB=1  and DATABASE_URL=postgres://...
"""

import os

def _fallback(intent: str, k: int = 10):
    always = [s.strip() for s in os.environ.get("ALWAYS_INCLUDE_TOOLS", "").split(",") if s.strip()]
    if not always:
        always = ["asset-query", "service-status", "network-ping"]
    return [{"key": key, "name": key, "short_desc": ""} for key in always][:k]

USE_DB = os.environ.get("USE_SELECTOR_DB") == "1"

if USE_DB:
    try:
        from .candidates import candidate_tools_from_intent as _real
        def candidate_tools_from_intent(intent: str, k: int = 10):
            return _real(intent, k)
    except Exception:
        def candidate_tools_from_intent(intent: str, k: int = 10):
            return _fallback(intent, k)
else:
    def candidate_tools_from_intent(intent: str, k: int = 10):
        return _fallback(intent, k)

__all__ = ["candidate_tools_from_intent"]
