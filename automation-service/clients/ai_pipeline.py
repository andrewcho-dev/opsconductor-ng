"""
AI Pipeline Client
Typed async client for communicating with ai-pipeline service
"""
import httpx
import logging
from typing import Dict, Any, Optional
from datetime import datetime
import uuid


logger = logging.getLogger(__name__)


class AIPipelineError(Exception):
    """Base exception for AI Pipeline client errors"""
    pass


class AIPipelineTimeoutError(AIPipelineError):
    """Raised when AI Pipeline request times out"""
    pass


class AIPipelineBadGatewayError(AIPipelineError):
    """Raised when AI Pipeline returns non-2xx response"""
    pass


class AIPipelineClient:
    """
    Async client for AI Pipeline service
    
    Handles:
    - POST /execute endpoint
    - Trace ID propagation
    - Timeout handling
    - Structured error responses
    """
    
    def __init__(self, base_url: str, timeout_seconds: float = 5.0):
        """
        Initialize AI Pipeline client
        
        Args:
            base_url: Base URL of ai-pipeline service (e.g., http://ai-pipeline:8000)
            timeout_seconds: Request timeout in seconds
        """
        self.base_url = base_url.rstrip('/')
        self.timeout_seconds = timeout_seconds
        self.client = httpx.AsyncClient(timeout=timeout_seconds)
        
        logger.info(f"[AIPipelineClient] Initialized with base_url={base_url}, timeout={timeout_seconds}s")
    
    async def close(self):
        """Close the HTTP client"""
        await self.client.aclose()
    
    async def execute(
        self,
        tool: str,
        input_text: str,
        trace_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Execute a tool via AI Pipeline /execute endpoint
        
        Args:
            tool: Tool name (e.g., "echo")
            input_text: Input text for the tool
            trace_id: Optional trace ID for request tracking
        
        Returns:
            Dict with parsed JSON response from ai-pipeline
        
        Raises:
            AIPipelineTimeoutError: Request timed out
            AIPipelineBadGatewayError: Non-2xx response from ai-pipeline
            AIPipelineError: Other errors
        """
        # Generate trace_id if not provided
        if not trace_id:
            trace_id = str(uuid.uuid4())
        
        url = f"{self.base_url}/execute"
        headers = {
            "X-Trace-Id": trace_id,
            "Content-Type": "application/json"
        }
        payload = {
            "tool": tool,
            "input": input_text,
            "trace_id": trace_id
        }
        
        logger.info(f"[{trace_id}] Calling ai-pipeline: tool={tool}, input={input_text[:50]}")
        
        try:
            response = await self.client.post(
                url,
                json=payload,
                headers=headers
            )
            
            # Check for non-2xx status
            if response.status_code >= 400:
                error_detail = response.text
                logger.error(
                    f"[{trace_id}] AI Pipeline error: status={response.status_code}, "
                    f"detail={error_detail[:200]}"
                )
                raise AIPipelineBadGatewayError(
                    f"AI Pipeline returned {response.status_code}: {error_detail[:200]}"
                )
            
            # Parse JSON response
            result = response.json()
            
            logger.info(
                f"[{trace_id}] AI Pipeline success: "
                f"success={result.get('success')}, "
                f"duration={result.get('duration_ms')}ms"
            )
            
            return result
            
        except httpx.TimeoutException as e:
            logger.error(f"[{trace_id}] AI Pipeline timeout after {self.timeout_seconds}s")
            raise AIPipelineTimeoutError(
                f"AI Pipeline request timed out after {self.timeout_seconds}s"
            ) from e
        
        except httpx.HTTPError as e:
            logger.error(f"[{trace_id}] AI Pipeline HTTP error: {e}")
            raise AIPipelineError(f"HTTP error communicating with AI Pipeline: {e}") from e
        
        except Exception as e:
            logger.error(f"[{trace_id}] AI Pipeline unexpected error: {e}")
            raise AIPipelineError(f"Unexpected error: {e}") from e
    
    async def health_check(self) -> bool:
        """
        Check if AI Pipeline is healthy
        
        Returns:
            True if healthy, False otherwise
        """
        try:
            response = await self.client.get(
                f"{self.base_url}/health",
                timeout=2.0
            )
            return response.status_code == 200
        except Exception as e:
            logger.warning(f"AI Pipeline health check failed: {e}")
            return False