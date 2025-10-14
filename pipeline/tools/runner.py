"""
Tool Runner - Executes tools with safety controls

This module handles the actual execution of tools with:
- Timeout enforcement
- Output size limits
- Credential redaction
- Platform-specific execution
- Structured error handling
"""

import asyncio
import subprocess
import logging
import time
import re
from typing import Dict, Any, Optional, List
from datetime import datetime
from pydantic import BaseModel

from .registry import ToolSpec, ToolParameter, get_tool_registry
from .metrics import record_tool_request, record_tool_error

logger = logging.getLogger(__name__)


# ============================================================================
# EXECUTION MODELS
# ============================================================================

class ToolExecutionRequest(BaseModel):
    """Request to execute a tool"""
    tool_name: str
    parameters: Dict[str, Any] = {}
    trace_id: Optional[str] = None
    timeout_override: Optional[int] = None


class ToolExecutionResult(BaseModel):
    """Result of tool execution"""
    success: bool
    tool_name: str
    output: Optional[str] = None
    error: Optional[str] = None
    exit_code: Optional[int] = None
    duration_ms: float
    timestamp: str
    trace_id: str
    truncated: bool = False
    redacted: bool = False


# ============================================================================
# TOOL RUNNER
# ============================================================================

class ToolRunner:
    """
    Executes tools with safety controls
    
    Features:
    - Command template rendering
    - Parameter validation
    - Timeout enforcement
    - Output truncation
    - Credential redaction
    - Platform detection
    """
    
    def __init__(self, max_output_bytes: Optional[int] = None):
        """
        Initialize tool runner
        
        Args:
            max_output_bytes: Maximum output size (default from env or 16KB)
        """
        import os
        self.max_output_bytes = max_output_bytes or int(
            os.getenv("TOOL_MAX_OUTPUT_BYTES", "16384")
        )
        self.registry = get_tool_registry()
        
        logger.info(f"[ToolRunner] Initialized with max_output_bytes={self.max_output_bytes}")
    
    async def execute(self, request: ToolExecutionRequest) -> ToolExecutionResult:
        """
        Execute a tool
        
        Args:
            request: Tool execution request
        
        Returns:
            ToolExecutionResult with execution outcome
        """
        start_time = time.perf_counter()
        trace_id = request.trace_id or self._generate_trace_id()
        
        logger.info(
            f"[ToolRunner] [{trace_id}] Executing tool={request.tool_name} "
            f"params={list(request.parameters.keys())}"
        )
        
        try:
            # Get tool spec
            tool_spec = self.registry.get(request.tool_name)
            if not tool_spec:
                return self._error_result(
                    request.tool_name,
                    f"Tool '{request.tool_name}' not found in registry",
                    trace_id,
                    start_time
                )
            
            # Validate parameters
            validation_error = self._validate_parameters(tool_spec, request.parameters)
            if validation_error:
                return self._error_result(
                    request.tool_name,
                    f"Parameter validation failed: {validation_error}",
                    trace_id,
                    start_time
                )
            
            # Build command
            command = self._build_command(tool_spec, request.parameters)
            logger.debug(f"[ToolRunner] [{trace_id}] Command: {command}")
            
            # Determine timeout
            timeout = request.timeout_override or tool_spec.timeout_seconds
            
            # Execute command
            result = await self._execute_command(
                command,
                timeout,
                tool_spec.max_output_bytes or self.max_output_bytes
            )
            
            # Redact sensitive data
            output, redacted = self._redact_output(result['stdout'], tool_spec.redact_patterns)
            
            # Calculate duration
            duration_ms = (time.perf_counter() - start_time) * 1000
            
            # Check for truncation
            truncated = result.get('truncated', False)
            
            # Record metrics
            success = result['exit_code'] == 0
            record_tool_request(request.tool_name, duration_ms / 1000, success)
            if not success:
                record_tool_error(request.tool_name, 'execution_failed')
            
            logger.info(
                f"[ToolRunner] [{trace_id}] Completed tool={request.tool_name} "
                f"exit_code={result['exit_code']} duration={duration_ms:.2f}ms "
                f"truncated={truncated} redacted={redacted}"
            )
            
            return ToolExecutionResult(
                success=success,
                tool_name=request.tool_name,
                output=output,
                error=result.get('stderr'),
                exit_code=result['exit_code'],
                duration_ms=round(duration_ms, 2),
                timestamp=datetime.utcnow().isoformat() + 'Z',
                trace_id=trace_id,
                truncated=truncated,
                redacted=redacted
            )
        
        except asyncio.TimeoutError:
            duration_ms = (time.perf_counter() - start_time) * 1000
            logger.error(f"[ToolRunner] [{trace_id}] Timeout after {timeout}s")
            
            # Record timeout metrics
            record_tool_request(request.tool_name, duration_ms / 1000, False)
            record_tool_error(request.tool_name, 'timeout')
            
            return ToolExecutionResult(
                success=False,
                tool_name=request.tool_name,
                error=f"Execution timed out after {timeout}s",
                duration_ms=round(duration_ms, 2),
                timestamp=datetime.utcnow().isoformat() + 'Z',
                trace_id=trace_id
            )
        
        except Exception as e:
            duration_ms = (time.perf_counter() - start_time) * 1000
            logger.error(f"[ToolRunner] [{trace_id}] Execution failed: {e}")
            
            # Record error metrics
            record_tool_request(request.tool_name, duration_ms / 1000, False)
            record_tool_error(request.tool_name, 'exception')
            
            return self._error_result(
                request.tool_name,
                str(e),
                trace_id,
                start_time
            )
    
    def _validate_parameters(
        self,
        tool_spec: ToolSpec,
        parameters: Dict[str, Any]
    ) -> Optional[str]:
        """
        Validate parameters against tool spec
        
        Returns:
            Error message if validation fails, None if valid
        """
        # Check required parameters
        for param in tool_spec.parameters:
            if param.required and param.name not in parameters:
                return f"Required parameter '{param.name}' is missing"
        
        # Validate parameter types and constraints
        for param_name, param_value in parameters.items():
            # Find parameter spec
            param_spec = next(
                (p for p in tool_spec.parameters if p.name == param_name),
                None
            )
            
            if not param_spec:
                # Unknown parameter - log warning but allow
                logger.warning(f"Unknown parameter '{param_name}' for tool {tool_spec.name}")
                continue
            
            # Type validation
            if param_spec.type == 'integer':
                if not isinstance(param_value, int):
                    return f"Parameter '{param_name}' must be an integer"
                
                if param_spec.min_value is not None and param_value < param_spec.min_value:
                    return f"Parameter '{param_name}' must be >= {param_spec.min_value}"
                
                if param_spec.max_value is not None and param_value > param_spec.max_value:
                    return f"Parameter '{param_name}' must be <= {param_spec.max_value}"
            
            elif param_spec.type == 'string':
                if not isinstance(param_value, str):
                    return f"Parameter '{param_name}' must be a string"
                
                if param_spec.pattern:
                    if not re.match(param_spec.pattern, param_value):
                        return f"Parameter '{param_name}' does not match required pattern"
            
            elif param_spec.type == 'boolean':
                if not isinstance(param_value, bool):
                    return f"Parameter '{param_name}' must be a boolean"
            
            # Enum validation
            if param_spec.enum and param_value not in param_spec.enum:
                return f"Parameter '{param_name}' must be one of {param_spec.enum}"
        
        return None
    
    def _build_command(self, tool_spec: ToolSpec, parameters: Dict[str, Any]) -> str:
        """
        Build command from template and parameters
        
        Args:
            tool_spec: Tool specification
            parameters: Parameter values
        
        Returns:
            Rendered command string
        """
        command = tool_spec.command_template
        
        # Apply defaults for missing optional parameters
        params_with_defaults = parameters.copy()
        for param in tool_spec.parameters:
            if param.name not in params_with_defaults and param.default is not None:
                params_with_defaults[param.name] = param.default
        
        # Replace placeholders
        for param_name, param_value in params_with_defaults.items():
            placeholder = f"{{{param_name}}}"
            command = command.replace(placeholder, str(param_value))
        
        return command
    
    async def _execute_command(
        self,
        command: str,
        timeout: int,
        max_output_bytes: int
    ) -> Dict[str, Any]:
        """
        Execute shell command with timeout and output limits
        
        Args:
            command: Command to execute
            timeout: Timeout in seconds
            max_output_bytes: Maximum output size
        
        Returns:
            Dict with stdout, stderr, exit_code, truncated
        """
        try:
            # Execute command
            process = await asyncio.create_subprocess_shell(
                command,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            # Wait with timeout
            stdout_bytes, stderr_bytes = await asyncio.wait_for(
                process.communicate(),
                timeout=timeout
            )
            
            # Decode output
            stdout = stdout_bytes.decode('utf-8', errors='replace')
            stderr = stderr_bytes.decode('utf-8', errors='replace')
            
            # Truncate if needed
            truncated = False
            if len(stdout) > max_output_bytes:
                stdout = stdout[:max_output_bytes] + "\n... [output truncated]"
                truncated = True
            
            if len(stderr) > max_output_bytes:
                stderr = stderr[:max_output_bytes] + "\n... [output truncated]"
                truncated = True
            
            return {
                'stdout': stdout,
                'stderr': stderr,
                'exit_code': process.returncode,
                'truncated': truncated
            }
        
        except asyncio.TimeoutError:
            # Kill process on timeout
            try:
                process.kill()
                await process.wait()
            except:
                pass
            raise
    
    def _redact_output(
        self,
        output: Optional[str],
        redact_patterns: List[str]
    ) -> tuple[Optional[str], bool]:
        """
        Redact sensitive data from output
        
        Args:
            output: Output text
            redact_patterns: List of regex patterns to redact
        
        Returns:
            Tuple of (redacted_output, was_redacted)
        """
        if not output or not redact_patterns:
            return output, False
        
        redacted = output
        was_redacted = False
        
        for pattern in redact_patterns:
            try:
                if re.search(pattern, redacted):
                    redacted = re.sub(pattern, '[REDACTED]', redacted)
                    was_redacted = True
            except re.error as e:
                logger.warning(f"Invalid redaction pattern '{pattern}': {e}")
        
        return redacted, was_redacted
    
    def _error_result(
        self,
        tool_name: str,
        error_message: str,
        trace_id: str,
        start_time: float
    ) -> ToolExecutionResult:
        """Create error result"""
        duration_ms = (time.perf_counter() - start_time) * 1000
        
        return ToolExecutionResult(
            success=False,
            tool_name=tool_name,
            error=error_message,
            duration_ms=round(duration_ms, 2),
            timestamp=datetime.utcnow().isoformat() + 'Z',
            trace_id=trace_id
        )
    
    def _generate_trace_id(self) -> str:
        """Generate trace ID"""
        import uuid
        return str(uuid.uuid4())


# ============================================================================
# GLOBAL RUNNER INSTANCE
# ============================================================================

_runner: Optional[ToolRunner] = None


def get_tool_runner() -> ToolRunner:
    """Get or create global tool runner singleton"""
    global _runner
    
    if _runner is None:
        _runner = ToolRunner()
    
    return _runner