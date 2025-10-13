"""Audit sinks for persisting AI query records to various backends."""

import os
import json
import asyncio
import logging
from abc import ABC, abstractmethod
from typing import Optional
from datetime import datetime, timezone

import httpx

from audit.models import AIQueryAuditRecord

logger = logging.getLogger(__name__)


class AuditSink(ABC):
    """Abstract base class for audit sinks."""
    
    @abstractmethod
    async def write(self, record: AIQueryAuditRecord) -> bool:
        """Write an audit record to the sink.
        
        Args:
            record: The audit record to persist
            
        Returns:
            True if write succeeded, False otherwise
        """
        pass


class StdoutSink(AuditSink):
    """Writes audit records to stdout as JSON."""
    
    async def write(self, record: AIQueryAuditRecord) -> bool:
        """Write audit record to stdout."""
        try:
            log_entry = {
                "audit_type": "ai_query",
                "timestamp": datetime.now(timezone.utc).isoformat(),
                **record.model_dump(mode='json')
            }
            print(json.dumps(log_entry), flush=True)
            return True
        except Exception as e:
            logger.error(f"Failed to write audit record to stdout: {e}")
            return False


class LokiSink(AuditSink):
    """Writes audit records to Grafana Loki."""
    
    def __init__(self, loki_url: str, max_retries: int = 3, retry_delay: float = 1.0):
        """Initialize Loki sink.
        
        Args:
            loki_url: Loki push API endpoint (e.g., http://localhost:3100/loki/api/v1/push)
            max_retries: Maximum number of retry attempts on 5xx errors
            retry_delay: Initial delay between retries (exponential backoff)
        """
        self.loki_url = loki_url
        self.max_retries = max_retries
        self.retry_delay = retry_delay
        self.client = httpx.AsyncClient(timeout=10.0)
    
    async def write(self, record: AIQueryAuditRecord) -> bool:
        """Write audit record to Loki with retry logic."""
        # Convert record to Loki format
        # Loki expects: {"streams": [{"stream": {...labels...}, "values": [[timestamp_ns, line]]}]}
        timestamp_ns = str(int(record.created_at.timestamp() * 1_000_000_000))
        
        labels = {
            "job": "audit",
            "type": "ai_query",
            "user_id": record.user_id,
            "trace_id": record.trace_id,
        }
        
        # Serialize the full record as the log line
        log_line = json.dumps(record.model_dump(mode='json'))
        
        payload = {
            "streams": [
                {
                    "stream": labels,
                    "values": [[timestamp_ns, log_line]]
                }
            ]
        }
        
        # Retry logic with exponential backoff
        for attempt in range(self.max_retries):
            try:
                response = await self.client.post(
                    self.loki_url,
                    json=payload,
                    headers={"Content-Type": "application/json"}
                )
                
                if response.status_code < 300:
                    logger.debug(f"Successfully wrote audit record to Loki: {record.trace_id}")
                    return True
                elif response.status_code >= 500:
                    # Server error - retry
                    delay = self.retry_delay * (2 ** attempt)
                    logger.warning(
                        f"Loki returned {response.status_code}, retrying in {delay}s "
                        f"(attempt {attempt + 1}/{self.max_retries})"
                    )
                    await asyncio.sleep(delay)
                else:
                    # Client error - don't retry
                    logger.error(
                        f"Loki returned {response.status_code}: {response.text}. "
                        f"Not retrying client error."
                    )
                    return False
                    
            except Exception as e:
                delay = self.retry_delay * (2 ** attempt)
                logger.warning(
                    f"Failed to write to Loki: {e}. "
                    f"Retrying in {delay}s (attempt {attempt + 1}/{self.max_retries})"
                )
                await asyncio.sleep(delay)
        
        logger.error(f"Failed to write audit record to Loki after {self.max_retries} attempts")
        return False
    
    async def close(self):
        """Close the HTTP client."""
        await self.client.aclose()


class PostgresSink(AuditSink):
    """Writes audit records to PostgreSQL."""
    
    def __init__(self, dsn: str):
        """Initialize Postgres sink.
        
        Args:
            dsn: PostgreSQL connection string (e.g., postgresql://user:pass@host:5432/db)
        """
        self.dsn = dsn
        self._pool: Optional[any] = None
    
    async def _ensure_pool(self):
        """Ensure connection pool is initialized."""
        if self._pool is None:
            import asyncpg
            self._pool = await asyncpg.create_pool(self.dsn, min_size=1, max_size=5)
    
    async def write(self, record: AIQueryAuditRecord) -> bool:
        """Write audit record to PostgreSQL."""
        try:
            await self._ensure_pool()
            
            # Serialize tools as JSONB
            tools_json = json.dumps([tool.model_dump() for tool in record.tools])
            
            async with self._pool.acquire() as conn:
                await conn.execute(
                    """
                    INSERT INTO audit_ai_queries 
                    (trace_id, user_id, input, output, tools, duration_ms, created_at)
                    VALUES ($1, $2, $3, $4, $5::jsonb, $6, $7)
                    """,
                    record.trace_id,
                    record.user_id,
                    record.input,
                    record.output,
                    tools_json,
                    record.duration_ms,
                    record.created_at
                )
            
            logger.debug(f"Successfully wrote audit record to Postgres: {record.trace_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to write audit record to Postgres: {e}")
            return False
    
    async def close(self):
        """Close the connection pool."""
        if self._pool:
            await self._pool.close()


class AuditSinkFactory:
    """Factory for creating audit sinks based on configuration."""
    
    @staticmethod
    def create_sink(sink_type: Optional[str] = None) -> AuditSink:
        """Create an audit sink based on environment configuration.
        
        Args:
            sink_type: Override sink type (loki|postgres|stdout). 
                      If None, reads from AUDIT_SINK env var.
        
        Returns:
            Configured audit sink instance
        """
        sink_type = sink_type or os.getenv("AUDIT_SINK", "stdout").lower()
        
        if sink_type == "loki":
            loki_url = os.getenv("LOKI_URL", "http://localhost:3100/loki/api/v1/push")
            logger.info(f"Initializing Loki audit sink: {loki_url}")
            return LokiSink(loki_url)
        
        elif sink_type == "postgres":
            postgres_dsn = os.getenv("POSTGRES_DSN")
            if not postgres_dsn:
                logger.warning("POSTGRES_DSN not set, falling back to stdout sink")
                return StdoutSink()
            logger.info(f"Initializing Postgres audit sink")
            return PostgresSink(postgres_dsn)
        
        else:
            logger.info("Using stdout audit sink")
            return StdoutSink()


# Global sink instance and queue for non-blocking writes
_audit_queue: Optional[asyncio.Queue] = None
_audit_worker_task: Optional[asyncio.Task] = None
_audit_sink: Optional[AuditSink] = None


async def _audit_worker():
    """Background worker that processes audit records from the queue."""
    global _audit_sink
    
    while True:
        try:
            record = await _audit_queue.get()
            if record is None:  # Shutdown signal
                break
            
            # Write to sink (non-blocking from caller's perspective)
            await _audit_sink.write(record)
            
        except Exception as e:
            logger.error(f"Audit worker error: {e}")
        finally:
            _audit_queue.task_done()


def init_audit_queue(sink: Optional[AuditSink] = None):
    """Initialize the audit queue and background worker.
    
    Args:
        sink: Optional sink instance. If None, creates one from environment config.
    
    Note:
        This function must be called from within an async context (e.g., startup event)
        to properly create the background worker task.
    """
    global _audit_queue, _audit_worker_task, _audit_sink
    
    if _audit_queue is not None:
        logger.warning("Audit queue already initialized")
        return
    
    _audit_sink = sink or AuditSinkFactory.create_sink()
    _audit_queue = asyncio.Queue(maxsize=1000)  # Bounded queue to prevent memory issues
    
    # Try to create worker task if event loop is running
    try:
        _audit_worker_task = asyncio.create_task(_audit_worker())
        logger.info("Audit queue and worker initialized")
    except RuntimeError as e:
        # No event loop running yet - will be started later via start_audit_worker()
        logger.info(f"Audit queue initialized (worker will start with event loop): {e}")


def start_audit_worker():
    """Start the audit worker task if not already running.
    
    This should be called from an async startup event to ensure the worker
    task is created within a running event loop.
    """
    global _audit_worker_task, _audit_queue, _audit_sink
    
    if _audit_worker_task is not None and not _audit_worker_task.done():
        logger.warning("Audit worker already running")
        return
    
    if _audit_queue is None or _audit_sink is None:
        logger.error("Audit queue not initialized, call init_audit_queue() first")
        return
    
    try:
        _audit_worker_task = asyncio.create_task(_audit_worker())
        logger.info("Audit worker started")
    except Exception as e:
        logger.error(f"Failed to start audit worker: {e}")


async def enqueue_audit_record(record: AIQueryAuditRecord) -> bool:
    """Enqueue an audit record for non-blocking write.
    
    Args:
        record: The audit record to persist
        
    Returns:
        True if enqueued successfully, False if queue is full
    """
    global _audit_queue
    
    if _audit_queue is None:
        logger.error("Audit queue not initialized")
        return False
    
    try:
        _audit_queue.put_nowait(record)
        return True
    except asyncio.QueueFull:
        logger.error("Audit queue is full, dropping record")
        return False


async def shutdown_audit_queue():
    """Shutdown the audit queue and worker gracefully."""
    global _audit_queue, _audit_worker_task, _audit_sink
    
    if _audit_queue is None:
        return
    
    # Send shutdown signal
    await _audit_queue.put(None)
    
    # Wait for worker to finish
    if _audit_worker_task:
        await _audit_worker_task
    
    # Close sink if it has a close method
    if _audit_sink and hasattr(_audit_sink, 'close'):
        await _audit_sink.close()
    
    _audit_queue = None
    _audit_worker_task = None
    _audit_sink = None
    
    logger.info("Audit queue shutdown complete")