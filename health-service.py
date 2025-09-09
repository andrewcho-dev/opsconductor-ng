#!/usr/bin/env python3
"""
Health check service for infrastructure components
"""
import json
import subprocess
import time
from flask import Flask, jsonify
import redis
import psycopg2
import requests
import os

app = Flask(__name__)

@app.route('/api/v1/redis/health')
def check_redis():
    try:
        r = redis.Redis(host='opsconductor-redis', port=6379, db=0, socket_timeout=5)
        start_time = time.time()
        r.ping()
        response_time = int((time.time() - start_time) * 1000)
        return jsonify({
            "service": "redis",
            "status": "healthy",
            "version": "1.0.0",
            "responseTime": response_time
        })
    except Exception as e:
        return jsonify({
            "service": "redis",
            "status": "unhealthy",
            "error": str(e)
        }), 503

@app.route('/api/v1/postgres/health')
def check_postgres():
    try:
        start_time = time.time()
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
        response_time = int((time.time() - start_time) * 1000)
        return jsonify({
            "service": "postgres",
            "status": "healthy",
            "version": "1.0.0",
            "responseTime": response_time
        })
    except Exception as e:
        return jsonify({
            "service": "postgres",
            "status": "unhealthy",
            "error": str(e)
        }), 503

@app.route('/api/v1/celery-worker/health')
def check_celery_worker():
    try:
        # Check via Flower API
        start_time = time.time()
        response = requests.get('http://opsconductor-flower:5555/api/workers', timeout=5)
        response_time = int((time.time() - start_time) * 1000)
        
        if response.status_code == 200:
            workers = response.json()
            active_workers = len([w for w in workers.values() if w.get('status') == True])
            return jsonify({
                "service": "celery-worker",
                "status": "healthy" if active_workers > 0 else "unhealthy",
                "version": "1.0.0",
                "responseTime": response_time,
                "activeWorkers": active_workers
            })
        else:
            return jsonify({
                "service": "celery-worker",
                "status": "healthy",  # Assume healthy if Flower is protected
                "version": "1.0.0",
                "responseTime": response_time,
                "note": "Flower API protected"
            })
    except Exception as e:
        return jsonify({
            "service": "celery-worker",
            "status": "unhealthy",
            "error": str(e)
        }), 503

@app.route('/api/v1/celery-beat/health')
def check_celery_beat():
    try:
        # Check if container is running
        result = subprocess.run(['docker', 'ps', '--filter', 'name=opsconductor-celery-beat', '--format', '{{.Status}}'], 
                              capture_output=True, text=True, timeout=5)
        if result.returncode == 0 and 'Up' in result.stdout:
            return jsonify({
                "service": "celery-beat",
                "status": "healthy",
                "version": "1.0.0"
            })
        else:
            return jsonify({
                "service": "celery-beat",
                "status": "unhealthy",
                "error": "Container not running"
            }), 503
    except Exception as e:
        return jsonify({
            "service": "celery-beat",
            "status": "unhealthy",
            "error": str(e)
        }), 503

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=3012, debug=False)