"""
OpenTelemetry tracing initialization and helpers for automation-service.

Provides:
- Automatic instrumentation for FastAPI, httpx, asyncpg
- W3C trace context propagation
- Configurable OTLP export
- Graceful degradation when collector is unavailable
- Logging bridge to inject trace_id/span_id into logs

Environment variables:
- OTEL_ENABLE: Enable tracing (default: true)
- OTEL_EXPORTER_OTLP_ENDPOINT: OTLP endpoint (default: http://localhost:4317)
- OTEL_SERVICE_NAME: Service name (default: automation-service)
- OTEL_SAMPLER: Sampler type (default: parentbased_traceidratio)
- OTEL_SAMPLER_ARG: Sampler argument (default: 1.0)
"""

import os
import logging
from typing import Optional

# OpenTelemetry imports - fail gracefully if not installed
try:
    from opentelemetry import trace
    from opentelemetry.sdk.trace import TracerProvider
    from opentelemetry.sdk.trace.export import BatchSpanProcessor
    from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
    from opentelemetry.sdk.resources import Resource, SERVICE_NAME, SERVICE_VERSION
    from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
    from opentelemetry.instrumentation.httpx import HTTPXClientInstrumentor
    from opentelemetry.instrumentation.asyncpg import AsyncPGInstrumentor
    from opentelemetry.instrumentation.logging import LoggingInstrumentor
    from opentelemetry.sdk.trace.sampling import (
        ParentBasedTraceIdRatio,
        TraceIdRatioBased,
        ALWAYS_ON,
        ALWAYS_OFF
    )
    from opentelemetry.trace.propagation.tracecontext import TraceContextTextMapPropagator
    from opentelemetry.propagate import set_global_textmap
    
    OTEL_AVAILABLE = True
except ImportError:
    OTEL_AVAILABLE = False
    trace = None

logger = logging.getLogger(__name__)

# Global state
_tracer_provider: Optional[TracerProvider] = None
_is_initialized = False


def is_enabled() -> bool:
    """Check if OpenTelemetry is enabled."""
    return (
        OTEL_AVAILABLE and
        os.getenv("OTEL_ENABLE", "true").lower() in ("true", "1", "yes")
    )


def get_sampler():
    """Get configured sampler."""
    if not OTEL_AVAILABLE:
        return None
    
    sampler_type = os.getenv("OTEL_SAMPLER", "parentbased_traceidratio").lower()
    sampler_arg = float(os.getenv("OTEL_SAMPLER_ARG", "1.0"))
    
    if sampler_type == "always_on":
        return ALWAYS_ON
    elif sampler_type == "always_off":
        return ALWAYS_OFF
    elif sampler_type == "traceidratio":
        return TraceIdRatioBased(sampler_arg)
    elif sampler_type == "parentbased_traceidratio":
        return ParentBasedTraceIdRatio(sampler_arg)
    else:
        logger.warning(f"Unknown sampler type '{sampler_type}', using parentbased_traceidratio")
        return ParentBasedTraceIdRatio(sampler_arg)


def init_tracing(service_name: Optional[str] = None, service_version: str = "1.0.0") -> bool:
    """
    Initialize OpenTelemetry tracing.
    
    Args:
        service_name: Service name (defaults to OTEL_SERVICE_NAME env var or "automation-service")
        service_version: Service version
        
    Returns:
        True if tracing was initialized successfully, False otherwise
    """
    global _tracer_provider, _is_initialized
    
    if _is_initialized:
        logger.debug("OpenTelemetry already initialized")
        return True
    
    if not is_enabled():
        logger.info("OpenTelemetry tracing is disabled")
        return False
    
    if not OTEL_AVAILABLE:
        logger.warning("OpenTelemetry packages not installed, tracing disabled")
        return False
    
    try:
        # Get configuration
        service_name = service_name or os.getenv("OTEL_SERVICE_NAME", "automation-service")
        otlp_endpoint = os.getenv("OTEL_EXPORTER_OTLP_ENDPOINT", "http://localhost:4317")
        
        # Create resource
        resource = Resource.create({
            SERVICE_NAME: service_name,
            SERVICE_VERSION: service_version,
        })
        
        # Create tracer provider with sampler
        sampler = get_sampler()
        _tracer_provider = TracerProvider(resource=resource, sampler=sampler)
        
        # Configure OTLP exporter
        try:
            otlp_exporter = OTLPSpanExporter(endpoint=otlp_endpoint, insecure=True)
            span_processor = BatchSpanProcessor(otlp_exporter)
            _tracer_provider.add_span_processor(span_processor)
            logger.info(f"OpenTelemetry OTLP exporter configured: {otlp_endpoint}")
        except Exception as e:
            logger.warning(f"Failed to configure OTLP exporter (will continue without export): {e}")
        
        # Set global tracer provider
        trace.set_tracer_provider(_tracer_provider)
        
        # Set W3C trace context propagator
        set_global_textmap(TraceContextTextMapPropagator())
        
        # Initialize logging instrumentation (adds trace_id/span_id to logs)
        LoggingInstrumentor().instrument(set_logging_format=False)
        
        _is_initialized = True
        logger.info(f"OpenTelemetry tracing initialized for service: {service_name}")
        return True
        
    except Exception as e:
        logger.error(f"Failed to initialize OpenTelemetry tracing: {e}", exc_info=True)
        return False


def instrument_fastapi(app):
    """
    Instrument FastAPI application with OpenTelemetry.
    
    Args:
        app: FastAPI application instance
    """
    if not is_enabled() or not OTEL_AVAILABLE:
        return
    
    try:
        FastAPIInstrumentor.instrument_app(app)
        logger.info("FastAPI instrumented with OpenTelemetry")
    except Exception as e:
        logger.error(f"Failed to instrument FastAPI: {e}", exc_info=True)


def instrument_httpx():
    """Instrument httpx client with OpenTelemetry."""
    if not is_enabled() or not OTEL_AVAILABLE:
        return
    
    try:
        HTTPXClientInstrumentor().instrument()
        logger.info("httpx instrumented with OpenTelemetry")
    except Exception as e:
        logger.error(f"Failed to instrument httpx: {e}", exc_info=True)


def instrument_asyncpg():
    """Instrument asyncpg with OpenTelemetry."""
    if not is_enabled() or not OTEL_AVAILABLE:
        return
    
    try:
        # Ensure tracer provider is set before instrumenting
        if not _is_initialized:
            logger.warning("Cannot instrument asyncpg: tracing not initialized")
            return
        
        # Verify tracer provider is available
        provider = trace.get_tracer_provider()
        if provider is None or not hasattr(provider, 'get_tracer'):
            logger.warning("Cannot instrument asyncpg: tracer provider not available")
            return
        
        AsyncPGInstrumentor().instrument()
        logger.info("asyncpg instrumented with OpenTelemetry")
    except Exception as e:
        logger.error(f"Failed to instrument asyncpg: {e}", exc_info=True)


def get_tracer(name: str = __name__):
    """
    Get a tracer instance.
    
    Args:
        name: Tracer name (typically __name__)
        
    Returns:
        Tracer instance or None if tracing is disabled
    """
    if not is_enabled() or not OTEL_AVAILABLE or not _is_initialized:
        return None
    
    return trace.get_tracer(name)


def get_current_span():
    """
    Get the current active span.
    
    Returns:
        Current span or None if no active span
    """
    if not is_enabled() or not OTEL_AVAILABLE:
        return None
    
    return trace.get_current_span()


def add_span_attributes(**attributes):
    """
    Add attributes to the current span.
    
    Args:
        **attributes: Key-value pairs to add as span attributes
    """
    if not is_enabled() or not OTEL_AVAILABLE:
        return
    
    span = get_current_span()
    if span and span.is_recording():
        for key, value in attributes.items():
            span.set_attribute(key, value)


def get_trace_context() -> dict:
    """
    Get current trace context for logging.
    
    Returns:
        Dictionary with trace_id and span_id (empty if no active span)
    """
    if not is_enabled() or not OTEL_AVAILABLE:
        return {}
    
    span = get_current_span()
    if not span or not span.is_recording():
        return {}
    
    ctx = span.get_span_context()
    if not ctx.is_valid:
        return {}
    
    return {
        "trace_id": format(ctx.trace_id, "032x"),
        "span_id": format(ctx.span_id, "016x"),
    }


def shutdown():
    """Shutdown tracing and flush pending spans."""
    global _tracer_provider, _is_initialized
    
    if not _is_initialized or not _tracer_provider:
        return
    
    try:
        _tracer_provider.shutdown()
        logger.info("OpenTelemetry tracing shutdown complete")
    except Exception as e:
        logger.error(f"Error during OpenTelemetry shutdown: {e}", exc_info=True)
    finally:
        _is_initialized = False
        _tracer_provider = None