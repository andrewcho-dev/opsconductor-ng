"""
Echo Tool - Simple tool for testing execution path without LLM.

This tool echoes back the input, useful for:
- Testing the execution pipeline end-to-end
- Verifying tracing and metrics
- Development and debugging
"""

import time
from typing import Dict, Any
from datetime import datetime


class EchoTool:
    """Simple echo tool that returns the input."""
    
    def __init__(self):
        self.name = "echo"
        self.description = "Echo back the input (for testing)"
        self.version = "1.0.0"
    
    async def execute(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute the echo tool.
        
        Args:
            input_data: Dictionary containing:
                - input: The string to echo back
                - Any other fields to include in response
        
        Returns:
            Dictionary with:
                - output: The echoed input
                - tool: Tool name
                - timestamp: Execution timestamp
                - duration_ms: Execution duration
        """
        start_time = time.perf_counter()
        
        # Extract input
        input_text = input_data.get("input", "")
        
        # Special handling for "ping" -> "pong"
        if input_text.lower().strip() == "ping":
            output = "pong"
        else:
            output = input_text
        
        # Calculate duration
        duration_ms = (time.perf_counter() - start_time) * 1000
        
        return {
            "output": output,
            "tool": self.name,
            "version": self.version,
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "duration_ms": round(duration_ms, 2),
            "success": True
        }
    
    def get_info(self) -> Dict[str, Any]:
        """Get tool information."""
        return {
            "name": self.name,
            "description": self.description,
            "version": self.version,
            "requires_llm": False,
            "bypass_compatible": True
        }