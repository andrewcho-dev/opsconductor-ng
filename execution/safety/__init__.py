"""
Safety Layer for Stage E Execution

This module provides production-hardened safety features to prevent 3am incidents:
1. Idempotency - Duplicate prevention with SHA256-based detection
2. Mutex - Per-asset locking to prevent concurrent modifications
3. RBAC - Worker-side RBAC validation
4. Secrets - Just-in-time secret resolution with masking
5. Cancellation - Cooperative cancellation with cleanup
6. Timeout - SLA-based timeout enforcement
7. Log Masking - Sink-level log masking for sensitive data

All safety features are non-negotiable for Phase 1 production deployment.
"""

from .idempotency import IdempotencyGuard
from .mutex import MutexGuard
from .rbac import RBACValidator
from .secrets import SecretsManager
from .cancellation import CancellationManager
from .timeout import TimeoutEnforcer
from .log_masking import LogMasker

__all__ = [
    "IdempotencyGuard",
    "MutexGuard",
    "RBACValidator",
    "SecretsManager",
    "CancellationManager",
    "TimeoutEnforcer",
    "LogMasker",
]