"""ID generation utilities for OpsConductor NG."""

import secrets


def new_trace_id() -> str:
    """Generate a new trace ID (32-character hex string).
    
    Returns:
        str: A 32-character hexadecimal trace ID
    """
    return secrets.token_hex(16)


def new_run_id() -> str:
    """Generate a new run ID with 'run_' prefix.
    
    Returns:
        str: A run ID in format 'run_' + 12-character hex
    """
    return f"run_{secrets.token_hex(6)}"


def new_plan_id() -> str:
    """Generate a new plan ID with 'plan_' prefix.
    
    Returns:
        str: A plan ID in format 'plan_' + 12-character hex
    """
    return f"plan_{secrets.token_hex(6)}"