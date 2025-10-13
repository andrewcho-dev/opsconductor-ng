# selector/__init__.py
"""Selector public API (re-exports only)."""

from .candidates import candidate_tools_from_intent

# Make v3 module importable
from . import v3

__all__ = ["candidate_tools_from_intent", "v3"]
