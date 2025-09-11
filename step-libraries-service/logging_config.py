#!/usr/bin/env python3
"""
Service Logging Template
Self-contained logging configuration for microservices
Copy this file to your service directory and customize as needed
"""

import os
import sys
import logging
import logging.config
from datetime import datetime
from typing import Dict, Any

def setup_service_logging(service_name: str, level: str = "INFO"):
    """Setup structured logging for the service"""
    
    log_level = getattr(logging, level.upper(), logging.INFO)
    
    logging_config = {
        'version': 1,
        'disable_existing_loggers': False,
        'formatters': {
            'standard': {
                'format': f'%(asctime)s - {service_name} - %(name)s - %(levelname)s - %(message)s',
                'datefmt': '%Y-%m-%d %H:%M:%S'
            },
            'detailed': {
                'format': f'%(asctime)s - {service_name} - %(name)s - %(levelname)s - %(funcName)s:%(lineno)d - %(message)s',
                'datefmt': '%Y-%m-%d %H:%M:%S'
            }
        },
        'handlers': {
            'console': {
                'class': 'logging.StreamHandler',
                'level': log_level,
                'formatter': 'standard',
                'stream': sys.stdout
            }
        },
        'loggers': {
            '': {  # root logger
                'handlers': ['console'],
                'level': log_level,
                'propagate': False
            },
            'uvicorn': {
                'handlers': ['console'],
                'level': 'INFO',
                'propagate': False
            },
            'uvicorn.access': {
                'handlers': ['console'],
                'level': 'INFO',
                'propagate': False
            }
        }
    }
    
    logging.config.dictConfig(logging_config)

def get_logger(name: str) -> logging.Logger:
    """Get a logger instance"""
    return logging.getLogger(name)

def log_startup(service_name: str, version: str = "1.0.0", port: int = None):
    """Log service startup information"""
    logger = get_logger(service_name)
    logger.info(f"Starting {service_name} v{version}")
    if port:
        logger.info(f"Service will be available on port {port}")
    logger.info(f"Log level: {logging.getLogger().level}")

def log_shutdown(service_name: str):
    """Log service shutdown information"""
    logger = get_logger(service_name)
    logger.info(f"Shutting down {service_name}")

def log_request(method: str, path: str, status_code: int, duration_ms: float = None):
    """Log HTTP request information"""
    logger = get_logger("http")
    message = f"{method} {path} - {status_code}"
    if duration_ms:
        message += f" - {duration_ms:.2f}ms"
    logger.info(message)