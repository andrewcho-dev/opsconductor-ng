#!/usr/bin/env python3
"""
Script to update all services to use the new database connection pool
"""

import os
import re
import sys

def update_service_file(service_path):
    """Update a service file to use the connection pool"""
    
    print(f"Updating {service_path}...")
    
    try:
        with open(service_path, 'r') as f:
            content = f.read()
        
        # Skip if already updated
        if 'from shared.database import' in content:
            print(f"  {service_path} already updated, skipping...")
            return
        
        # Add shared module import
        import_pattern = r'(import os\nimport logging)'
        import_replacement = r'\1\nimport sys\n\n# Add shared module to path\nsys.path.append(\'/home/opsconductor\')'
        content = re.sub(import_pattern, import_replacement, content)
        
        # Remove psycopg2 imports and add shared database import
        content = re.sub(r'import psycopg2.*\n', '', content)
        content = re.sub(r'import psycopg2\.extras.*\n', '', content)
        
        # Add shared database import after other imports
        fastapi_import_pattern = r'(from fastapi import.*\n)'
        fastapi_replacement = r'\1from shared.database import get_db_cursor, check_database_health, cleanup_database_pool\n'
        content = re.sub(fastapi_import_pattern, fastapi_replacement, content)
        
        # Remove database configuration variables
        db_config_pattern = r'# Database configuration\nDB_HOST = .*\nDB_PORT = .*\nDB_NAME = .*\nDB_USER = .*\nDB_PASSWORD = .*\n'
        content = re.sub(db_config_pattern, '# Database configuration is now handled by shared.database module\n', content)
        
        # Remove get_db_connection function
        get_db_conn_pattern = r'# Database connection\ndef get_db_connection\(\):.*?detail="Database connection failed"\s*\)\s*\n'
        content = re.sub(get_db_conn_pattern, '# Database connection is now handled by shared.database module\n\n', content, flags=re.DOTALL)
        
        # Update database operations - this is complex, so we'll do basic replacements
        # Replace conn = get_db_connection() patterns
        content = re.sub(r'conn = get_db_connection\(\)', 'with get_db_cursor() as cursor:', content)
        
        # Remove conn.close() calls
        content = re.sub(r'\s*conn\.close\(\)\s*\n', '', content)
        
        # Remove finally blocks that only close connections
        content = re.sub(r'\s*finally:\s*\n\s*conn\.close\(\)\s*\n', '', content)
        
        # Update health check endpoint
        health_pattern = r'@app\.get\("/health"\)\nasync def health_check\(\):\s*\n\s*""".*?"""\s*\n\s*return \{"status": "healthy", "service": ".*?"\}'
        health_replacement = '''@app.get("/health")
async def health_check():
    """Health check endpoint with database connectivity"""
    db_health = check_database_health()
    return {
        "status": "healthy" if db_health["status"] == "healthy" else "unhealthy",
        "service": os.path.basename(os.path.dirname(__file__)) + "-service",
        "database": db_health
    }

# Cleanup on shutdown
@app.on_event("shutdown")
async def shutdown_event():
    """Clean up database connections on shutdown"""
    cleanup_database_pool()'''
        
        content = re.sub(health_pattern, health_replacement, content, flags=re.DOTALL)
        
        # Write updated content
        with open(service_path, 'w') as f:
            f.write(content)
        
        print(f"  {service_path} updated successfully")
        
    except Exception as e:
        print(f"  Error updating {service_path}: {e}")

def main():
    """Update all service files"""
    
    services = [
        '/home/opsconductor/user-service/main.py',
        '/home/opsconductor/credentials-service/main.py',
        '/home/opsconductor/targets-service/main.py',
        '/home/opsconductor/jobs-service/main.py',
        '/home/opsconductor/executor-service/main.py',
        '/home/opsconductor/scheduler-service/main.py',
        '/home/opsconductor/notification-service/main.py',
        '/home/opsconductor/discovery-service/main.py',
        '/home/opsconductor/step-libraries-service/main.py'
    ]
    
    for service_path in services:
        if os.path.exists(service_path):
            update_service_file(service_path)
        else:
            print(f"Service file not found: {service_path}")
    
    print("\nAll services updated!")
    print("\nNext steps:")
    print("1. Test the services to ensure they work with connection pooling")
    print("2. Update docker-compose.yml to add DB_POOL_MIN and DB_POOL_MAX environment variables")
    print("3. Restart the services to apply changes")

if __name__ == "__main__":
    main()