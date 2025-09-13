#!/usr/bin/env python3
"""
Data Migration Script
Migrates data from old OpsConductor architecture to new optimized architecture
"""

import os
import sys
import asyncio
import asyncpg
from datetime import datetime
import json

async def migrate_data():
    """Migrate data from old to new architecture"""
    
    print("🔄 Starting data migration...")
    
    # Database connection
    db_url = "postgresql://postgres:postgres123@postgres:5432/opsconductor"
    
    try:
        conn = await asyncpg.connect(db_url)
        print("✅ Connected to database")
        
        # Check if old tables exist
        old_tables = await conn.fetch("""
            SELECT table_name FROM information_schema.tables 
            WHERE table_schema = 'public' 
            AND table_name IN ('users', 'targets', 'jobs', 'job_runs')
        """)
        
        if not old_tables:
            print("ℹ️  No old tables found - this appears to be a fresh installation")
            return
        
        print(f"📊 Found {len(old_tables)} old tables to migrate")
        
        # Migrate users (public.users -> identity.users)
        print("👥 Migrating users...")
        try:
            old_users = await conn.fetch("SELECT * FROM public.users")
            migrated_users = 0
            
            for user in old_users:
                try:
                    await conn.execute("""
                        INSERT INTO identity.users 
                        (id, username, email, password_hash, first_name, last_name, 
                         is_active, is_admin, last_login, created_at, updated_at)
                        VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11)
                        ON CONFLICT (id) DO NOTHING
                    """, 
                    user['id'], user['username'], user['email'], user['password_hash'],
                    user.get('first_name'), user.get('last_name'), 
                    user.get('is_active', True), user.get('is_admin', False),
                    user.get('last_login'), user.get('created_at', datetime.utcnow()),
                    user.get('updated_at', datetime.utcnow()))
                    migrated_users += 1
                except Exception as e:
                    print(f"  ⚠️  Failed to migrate user {user['username']}: {e}")
            
            print(f"  ✅ Migrated {migrated_users} users")
            
            # Update sequence
            await conn.execute("SELECT setval('identity.users_id_seq', (SELECT MAX(id) FROM identity.users))")
            
        except Exception as e:
            print(f"  ❌ User migration failed: {e}")
        
        
        # Migrate targets (public.targets -> assets.targets)
        print("🎯 Migrating targets...")
        try:
            old_targets = await conn.fetch("SELECT * FROM public.targets")
            migrated_targets = 0
            
            for target in old_targets:
                try:
                    # Map old target types
                    target_type = target.get('target_type', 'linux')
                    connection_type = target.get('connection_type', 'ssh')
                    
                    await conn.execute("""
                        INSERT INTO assets.targets 
                        (id, name, description, host, port, target_type, connection_type,
                         tags, metadata, is_active, created_by, created_at, updated_at)
                        VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13)
                        ON CONFLICT (id) DO NOTHING
                    """,
                    target['id'], target['name'], target.get('description'),
                    target['host'], target.get('port'), target_type, connection_type,
                    json.dumps(target.get('tags', [])),
                    json.dumps(target.get('metadata', {})),
                    target.get('is_active', True),
                    target.get('created_by', 1),
                    target.get('created_at', datetime.utcnow()),
                    target.get('updated_at', datetime.utcnow()))
                    migrated_targets += 1
                except Exception as e:
                    print(f"  ⚠️  Failed to migrate target {target['name']}: {e}")
            
            print(f"  ✅ Migrated {migrated_targets} targets")
            
            # Update sequence
            await conn.execute("SELECT setval('assets.targets_id_seq', (SELECT MAX(id) FROM assets.targets))")
            
        except Exception as e:
            print(f"  ❌ Target migration failed: {e}")
        
        # Migrate jobs (public.jobs -> automation.jobs)
        print("⚙️  Migrating jobs...")
        try:
            old_jobs = await conn.fetch("SELECT * FROM public.jobs")
            migrated_jobs = 0
            
            for job in old_jobs:
                try:
                    # Convert visual_workflow to workflow_definition
                    workflow_def = job.get('visual_workflow', {})
                    if isinstance(workflow_def, str):
                        workflow_def = json.loads(workflow_def)
                    
                    await conn.execute("""
                        INSERT INTO automation.jobs 
                        (id, name, description, workflow_definition, schedule_expression,
                         is_enabled, tags, metadata, created_by, updated_by, created_at, updated_at)
                        VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12)
                        ON CONFLICT (id) DO NOTHING
                    """,
                    job['id'], job['name'], job.get('description'),
                    json.dumps(workflow_def), job.get('schedule'),
                    job.get('enabled', True),
                    json.dumps(job.get('tags', [])),
                    json.dumps({}),
                    job.get('created_by', 1), job.get('updated_by', 1),
                    job.get('created_at', datetime.utcnow()),
                    job.get('updated_at', datetime.utcnow()))
                    migrated_jobs += 1
                except Exception as e:
                    print(f"  ⚠️  Failed to migrate job {job['name']}: {e}")
            
            print(f"  ✅ Migrated {migrated_jobs} jobs")
            
            # Update sequence
            await conn.execute("SELECT setval('automation.jobs_id_seq', (SELECT MAX(id) FROM automation.jobs))")
            
        except Exception as e:
            print(f"  ❌ Job migration failed: {e}")
        
        # Migrate job runs (public.job_runs -> automation.job_executions)
        print("📊 Migrating job executions...")
        try:
            old_job_runs = await conn.fetch("SELECT * FROM public.job_runs")
            migrated_executions = 0
            
            for run in old_job_runs:
                try:
                    await conn.execute("""
                        INSERT INTO automation.job_executions 
                        (id, job_id, status, trigger_type, input_data, output_data,
                         error_message, started_at, completed_at, started_by, created_at)
                        VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11)
                        ON CONFLICT (id) DO NOTHING
                    """,
                    run['id'], run['job_id'], run.get('status', 'completed'),
                    'manual',  # Default trigger type
                    json.dumps(run.get('input_data', {})),
                    json.dumps(run.get('output_data', {})),
                    run.get('error_message'),
                    run.get('started_at'), run.get('completed_at'),
                    run.get('started_by', 1),
                    run.get('created_at', datetime.utcnow()))
                    migrated_executions += 1
                except Exception as e:
                    print(f"  ⚠️  Failed to migrate job run {run['id']}: {e}")
            
            print(f"  ✅ Migrated {migrated_executions} job executions")
            
            # Update sequence
            await conn.execute("SELECT setval('automation.job_executions_id_seq', (SELECT MAX(id) FROM automation.job_executions))")
            
        except Exception as e:
            print(f"  ❌ Job execution migration failed: {e}")
        
        print("✅ Data migration completed successfully!")
        
    except Exception as e:
        print(f"❌ Migration failed: {e}")
        sys.exit(1)
    finally:
        if 'conn' in locals():
            await conn.close()

if __name__ == "__main__":
    asyncio.run(migrate_data())