"""Error codes for OpsConductor NG."""


class ErrorCategory:
    """Container for error codes in a specific category."""
    
    def __init__(self, prefix: str):
        self._prefix = prefix
        self._codes: dict[str, str] = {}
    
    def __getattr__(self, name: str) -> str:
        if name.startswith('_'):
            raise AttributeError(f"'{type(self).__name__}' object has no attribute '{name}'")
        code = f"{self._prefix}.{name}"
        self._codes[name] = code
        return code


class ErrorCodes:
    """Error code registry for OpsConductor NG.
    
    Usage:
        EC.SELECT.BUDGET_OVERFLOW
        EC.PLAN.INVALID_PLAN
        EC.EXEC.TIMEOUT
        EC.EXEC.NONZERO_EXIT
        EC.OBS.TRACE_EXPORT_FAIL
    """
    
    def __init__(self):
        self.SELECT = ErrorCategory("SELECT")
        self.PLAN = ErrorCategory("PLAN")
        self.EXEC = ErrorCategory("EXEC")
        self.OBS = ErrorCategory("OBS")


# Global error codes instance
EC = ErrorCodes()