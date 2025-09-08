#!/usr/bin/env python3
"""
Shared Database Connection Pool Module
Provides connection pooling and database utilities for all OpsConductor services
"""

import os
import logging
import threading
import time
from contextlib import contextmanager
from typing import Optional, Dict, Any
import psycopg2
import psycopg2.extras
from psycopg2 import pool
from fastapi import status
from .errors import DatabaseError, ServiceCommunicationError

logger = logging.getLogger(__name__)

class DatabasePool:
    """Thread-safe database connection pool manager with enhanced monitoring"""
    
    _instance = None
    _lock = threading.Lock()
    
    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super(DatabasePool, cls).__new__(cls)
        return cls._instance
    
    def __init__(self):
        if hasattr(self, '_initialized'):
            return
            
        self._initialized = True
        self._pool = None
        self._config = self._load_config()
        self._metrics = {
            'connections_acquired': 0,
            'connections_released': 0,
            'connection_errors': 0,
            'pool_exhaustion_warnings': 0,
            'last_exhaustion_warning': 0
        }
        self._create_pool()
    
    def _load_config(self) -> Dict[str, Any]:
        """Load database configuration from environment variables"""
        return {
            'host': os.getenv("DB_HOST", "localhost"),
            'port': int(os.getenv("DB_PORT", "5432")),
            'database': os.getenv("DB_NAME", "opsconductor"),
            'user': os.getenv("DB_USER", "postgres"),
            'password': os.getenv("DB_PASSWORD", "postgres"),
            'minconn': int(os.getenv("DB_POOL_MIN", "2")),
            'maxconn': int(os.getenv("DB_POOL_MAX", "20")),
            'connection_timeout': int(os.getenv("DB_CONNECTION_TIMEOUT", "30")),
            'pool_exhaustion_threshold': float(os.getenv("DB_POOL_EXHAUSTION_THRESHOLD", "0.8")),
            'cursor_factory': psycopg2.extras.RealDictCursor
        }
    
    def _create_pool(self):
        """Create the connection pool"""
        try:
            self._pool = psycopg2.pool.ThreadedConnectionPool(
                minconn=self._config['minconn'],
                maxconn=self._config['maxconn'],
                host=self._config['host'],
                port=self._config['port'],
                database=self._config['database'],
                user=self._config['user'],
                password=self._config['password'],
                cursor_factory=self._config['cursor_factory']
            )
            logger.info(f"Database connection pool created: {self._config['minconn']}-{self._config['maxconn']} connections")
        except Exception as e:
            logger.error(f"Failed to create database connection pool: {e}")
            raise
    
    def get_connection(self):
        """Get a connection from the pool with enhanced monitoring"""
        if not self._pool:
            self._metrics['connection_errors'] += 1
            raise DatabaseError("Database pool not initialized")
        
        # Check for pool exhaustion and warn if necessary
        self._check_pool_exhaustion()
        
        try:
            start_time = time.time()
            conn = self._pool.getconn()
            acquisition_time = time.time() - start_time
            
            if conn:
                self._metrics['connections_acquired'] += 1
                
                # Log slow connection acquisition
                if acquisition_time > 1.0:
                    logger.warning(f"Slow database connection acquisition: {acquisition_time:.2f}s")
                
                return conn
            else:
                self._metrics['connection_errors'] += 1
                raise ServiceCommunicationError("database", "No database connections available")
        except Exception as e:
            self._metrics['connection_errors'] += 1
            logger.error(f"Failed to get database connection: {e}")
            raise DatabaseError("Database connection failed")
    
    def return_connection(self, conn):
        """Return a connection to the pool with metrics tracking"""
        if self._pool and conn:
            try:
                self._pool.putconn(conn)
                self._metrics['connections_released'] += 1
            except Exception as e:
                self._metrics['connection_errors'] += 1
                logger.error(f"Failed to return connection to pool: {e}")
    
    def close_all_connections(self):
        """Close all connections in the pool"""
        if self._pool:
            try:
                self._pool.closeall()
                logger.info("All database connections closed")
            except Exception as e:
                logger.error(f"Error closing database connections: {e}")
    
    def _check_pool_exhaustion(self):
        """Check for pool exhaustion and log warnings"""
        if not self._pool:
            return
            
        # Calculate estimated utilization based on acquisition/release metrics
        active_connections = self._metrics['connections_acquired'] - self._metrics['connections_released']
        utilization = active_connections / self._config['maxconn']
        
        # Warn if utilization exceeds threshold and enough time has passed since last warning
        if (utilization >= self._config['pool_exhaustion_threshold'] and 
            time.time() - self._metrics['last_exhaustion_warning'] > 300):  # 5 minutes
            
            self._metrics['pool_exhaustion_warnings'] += 1
            self._metrics['last_exhaustion_warning'] = time.time()
            
            logger.warning(
                f"Database pool utilization high: {utilization:.1%} "
                f"({active_connections}/{self._config['maxconn']} connections)"
            )
    
    def get_pool_status(self) -> Dict[str, Any]:
        """Get current pool status for monitoring with enhanced metrics"""
        if not self._pool:
            return {"status": "not_initialized"}
        
        # Calculate current utilization estimate
        active_connections = max(0, self._metrics['connections_acquired'] - self._metrics['connections_released'])
        utilization = active_connections / self._config['maxconn'] if self._config['maxconn'] > 0 else 0
        
        return {
            "status": "active",
            "configuration": {
                "min_connections": self._config['minconn'],
                "max_connections": self._config['maxconn'],
                "connection_timeout": self._config['connection_timeout'],
                "exhaustion_threshold": self._config['pool_exhaustion_threshold'],
                "host": self._config['host'],
                "database": self._config['database']
            },
            "metrics": {
                "connections_acquired": self._metrics['connections_acquired'],
                "connections_released": self._metrics['connections_released'],
                "active_connections_estimate": active_connections,
                "utilization_estimate": f"{utilization:.1%}",
                "connection_errors": self._metrics['connection_errors'],
                "pool_exhaustion_warnings": self._metrics['pool_exhaustion_warnings']
            },
            "health": {
                "status": "healthy" if self._metrics['connection_errors'] == 0 else "degraded",
                "high_utilization": utilization >= self._config['pool_exhaustion_threshold']
            }
        }
    
    def get_pool_metrics(self) -> Dict[str, Any]:
        """Get detailed pool metrics for monitoring endpoints"""
        return self.get_pool_status()

# Global pool instance
_db_pool = None

def get_database_pool() -> DatabasePool:
    """Get the global database pool instance"""
    global _db_pool
    if _db_pool is None:
        _db_pool = DatabasePool()
    return _db_pool

@contextmanager
def get_db_connection():
    """Context manager for database connections"""
    pool = get_database_pool()
    conn = None
    try:
        conn = pool.get_connection()
        yield conn
    except Exception as e:
        if conn:
            conn.rollback()
        logger.error(f"Database operation failed: {e}")
        raise
    finally:
        if conn:
            pool.return_connection(conn)

@contextmanager
def get_db_cursor(commit: bool = True):
    """Context manager for database cursors with automatic transaction handling"""
    with get_db_connection() as conn:
        cursor = None
        try:
            cursor = conn.cursor()
            yield cursor
            if commit:
                conn.commit()
        except Exception as e:
            conn.rollback()
            logger.error(f"Database cursor operation failed: {e}")
            raise
        finally:
            if cursor:
                cursor.close()

def execute_query(query: str, params: tuple = None, fetch_one: bool = False, fetch_all: bool = False):
    """Execute a database query with automatic connection management"""
    with get_db_cursor() as cursor:
        cursor.execute(query, params)
        
        if fetch_one:
            return cursor.fetchone()
        elif fetch_all:
            return cursor.fetchall()
        else:
            return cursor.rowcount

def execute_transaction(queries: list):
    """Execute multiple queries in a single transaction"""
    with get_db_connection() as conn:
        cursor = None
        try:
            cursor = conn.cursor()
            for query_data in queries:
                if isinstance(query_data, tuple):
                    query, params = query_data
                    cursor.execute(query, params)
                else:
                    cursor.execute(query_data)
            conn.commit()
            return True
        except Exception as e:
            conn.rollback()
            logger.error(f"Transaction failed: {e}")
            raise
        finally:
            if cursor:
                cursor.close()

def get_database_metrics() -> Dict[str, Any]:
    """Get detailed database pool metrics for monitoring endpoints"""
    try:
        pool = get_database_pool()
        return pool.get_pool_metrics()
    except Exception as e:
        logger.error(f"Failed to get database metrics: {e}")
        return {
            "status": "error",
            "error": str(e)
        }

def check_database_health() -> Dict[str, Any]:
    """Check database connectivity and pool health"""
    try:
        pool = get_database_pool()
        pool_status = pool.get_pool_status()
        
        # Test a simple query
        start_time = time.time()
        with get_db_cursor(commit=False) as cursor:
            cursor.execute("SELECT 1")
            result = cursor.fetchone()
        query_time = time.time() - start_time
        
        return {
            "status": "healthy",
            "pool": pool_status,
            "test_query": {
                "status": "passed" if result else "failed",
                "response_time_ms": round(query_time * 1000, 2)
            }
        }
    except Exception as e:
        logger.error(f"Database health check failed: {e}")
        return {
            "status": "unhealthy",
            "error": str(e)
        }

# Cleanup function for graceful shutdown
def cleanup_database_pool():
    """Clean up database pool on application shutdown"""
    global _db_pool
    if _db_pool:
        _db_pool.close_all_connections()
        _db_pool = None