#!/usr/bin/env python3
"""
Simple health check endpoints for infrastructure services
"""
import json
import sys
import subprocess
import time
import redis
import psycopg2
from celery import Celery

def check_redis():
    """Check Redis health"""
    try:
        r = redis.Redis(host='opsconductor-redis', port=6379, db=0, socket_timeout=5)
        r.ping()
        return {"service": "redis", "status": "healthy", "version": "1.0.0"}
    except Exception as e:
        return {"service": "redis", "status": "unhealthy", "error": str(e)}

def check_postgres():
    """Check PostgreSQL health"""
    try:
        conn = psycopg2.connect(
            host="opsconductor-postgres",
            port=5432,
            database="opsconductor",
            user="postgres",
            password="postgres123",
            connect_timeout=5
        )
        cursor = conn.cursor()
        cursor.execute("SELECT 1")
        cursor.fetchone()
        cursor.close()
        conn.close()
        return {"service": "postgres", "status": "healthy", "version": "1.0.0"}
    except Exception as e:
        return {"service": "postgres", "status": "unhealthy", "error": str(e)}

def check_celery_worker():
    """Check Celery worker health"""
    try:
        app = Celery('shared.celery_config')
        app.config_from_object('shared.celery_config')
        
        # Get worker stats
        inspect = app.control.inspect(timeout=5)
        stats = inspect.stats()
        
        if stats:
            return {"service": "celery-worker", "status": "healthy", "version": "1.0.0", "workers": len(stats)}
        else:
            return {"service": "celery-worker", "status": "unhealthy", "error": "No workers found"}
    except Exception as e:
        return {"service": "celery-worker", "status": "unhealthy", "error": str(e)}

def check_celery_beat():
    """Check Celery beat health"""
    try:
        # Check if celery beat process is running
        result = subprocess.run(['pgrep', '-f', 'celery.*beat'], capture_output=True, text=True, timeout=5)
        if result.returncode == 0:
            return {"service": "celery-beat", "status": "healthy", "version": "1.0.0"}
        else:
            return {"service": "celery-beat", "status": "unhealthy", "error": "Process not found"}
    except Exception as e:
        return {"service": "celery-beat", "status": "unhealthy", "error": str(e)}

def check_flower():
    """Check Flower health"""
    try:
        import requests
        response = requests.get('http://opsconductor-flower:5555/api/workers', timeout=5)
        if response.status_code in [200, 401]:  # 401 is OK, means service is up but needs auth
            return {"service": "flower", "status": "healthy", "version": "1.0.0"}
        else:
            return {"service": "flower", "status": "unhealthy", "error": f"HTTP {response.status_code}"}
    except Exception as e:
        return {"service": "flower", "status": "unhealthy", "error": str(e)}

def check_frontend():
    """Check Frontend health"""
    try:
        import requests
        response = requests.get('http://opsconductor-frontend:3000', timeout=5)
        if response.status_code == 200:
            return {"service": "frontend", "status": "healthy", "version": "1.0.0"}
        else:
            return {"service": "frontend", "status": "unhealthy", "error": f"HTTP {response.status_code}"}
    except Exception as e:
        return {"service": "frontend", "status": "unhealthy", "error": str(e)}

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python health_endpoints.py <service>")
        sys.exit(1)
    
    service = sys.argv[1]
    
    checks = {
        'redis': check_redis,
        'postgres': check_postgres,
        'celery-worker': check_celery_worker,
        'celery-beat': check_celery_beat,
        'flower': check_flower,
        'frontend': check_frontend
    }
    
    if service in checks:
        result = checks[service]()
        print(json.dumps(result))
    else:
        print(json.dumps({"service": service, "status": "unknown", "error": "Unknown service"}))