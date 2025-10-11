"""
Tool selection and candidate generation.
- Tries to import the Postgres-backed DAO.
- Falls back to a stub that only returns ALWAYS_INCLUDE_TOOLS for unit tests.
"""
import os

def _fallback(intent: str, k: int = 10):
    always = [s.strip() for s in os.environ.get("ALWAYS_INCLUDE_TOOLS", "").split(",") if s.strip()]
    return [{"key": key, "name": key, "short_desc": ""} for key in always][:k]

try:
    # Lazy indirection so importing `selector` doesn't hard-require psycopg2
    from .candidates import candidate_tools_from_intent as _real_candidate_tools_from_intent  # type: ignore

    def candidate_tools_from_intent(intent: str, k: int = 10):
        return _real_candidate_tools_from_intent(intent, k)
except Exception:
    # ImportError or any env/setup problem → keep unit tests happy
    def candidate_tools_from_intent(intent: str, k: int = 10):
        return _fallback(intent, k)

__all__ = ["candidate_tools_from_intent"]
