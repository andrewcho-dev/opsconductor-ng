"""
Prefect Flow Registry Service

This service manages AI-generated Prefect flows, providing storage,
registration, and execution capabilities for the OpsConductor AI Brain.
"""

import os
import asyncio
import json
import uuid
from datetime import datetime
from typing import Dict, List, Optional, Any
from pathlib import Path

import structlog
from fastapi import FastAPI, HTTPException, BackgroundTasks
from pydantic import BaseModel
import asyncpg
import redis.asyncio as redis
from prefect import flow, task
from prefect.client.orchestration import PrefectClient
from prefect.deployments import Deployment
from prefect.server.schemas.actions import DeploymentCreate

# Configure structured logging
structlog.configure(
    processors=[
        structlog.stdlib.filter_by_level,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.processors.UnicodeDecoder(),
        structlog.processors.JSONRenderer()
    ],
    context_class=dict,
    logger_factory=structlog.stdlib.LoggerFactory(),
    cache_logger_on_first_use=True,
)

logger = structlog.get_logger()

# Configuration
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://postgres:postgres123@postgres:5432/opsconductor")
PREFECT_API_URL = os.getenv("PREFECT_API_URL", "http://prefect-server:4200/api")
REDIS_URL = os.getenv("REDIS_URL", "redis://redis:6379/10")
FLOWS_DIR = Path("/flows")

# Ensure flows directory exists
FLOWS_DIR.mkdir(exist_ok=True)

app = FastAPI(
    title="Prefect Flow Registry",
    description="AI-generated Prefect flow management service",
    version="1.0.0"
)

# Pydantic models
class FlowDefinition(BaseModel):
    name: str
    description: str
    python_code: str
    parameters: Dict[str, Any] = {}
    tags: List[str] = []
    created_by: str
    ai_generated: bool = True

class FlowRegistration(BaseModel):
    flow_id: str
    deployment_id: str
    status: str
    created_at: datetime

class FlowExecution(BaseModel):
    flow_id: str
    parameters: Dict[str, Any] = {}
    scheduled_for: Optional[datetime] = None

# Database connection pool
db_pool = None
redis_client = None

@app.on_event("startup")
async def startup():
    """Initialize database and Redis connections"""
    global db_pool, redis_client
    
    try:
        # Initialize database pool
        db_pool = await asyncpg.create_pool(DATABASE_URL)
        logger.info("Database connection pool created")
        
        # Initialize Redis client
        redis_client = redis.from_url(REDIS_URL)
        await redis_client.ping()
        logger.info("Redis connection established")
        
        # Create database tables if they don't exist
        await create_tables()
        
    except Exception as e:
        logger.error("Failed to initialize connections", error=str(e))
        raise

@app.on_event("shutdown")
async def shutdown():
    """Clean up connections"""
    global db_pool, redis_client
    
    if db_pool:
        await db_pool.close()
    if redis_client:
        await redis_client.close()

async def create_tables():
    """Create necessary database tables"""
    async with db_pool.acquire() as conn:
        await conn.execute("""
            CREATE SCHEMA IF NOT EXISTS prefect;
            
            CREATE TABLE IF NOT EXISTS prefect.flows (
                id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                name VARCHAR(255) NOT NULL,
                description TEXT,
                python_code TEXT NOT NULL,
                parameters JSONB DEFAULT '{}',
                tags TEXT[] DEFAULT '{}',
                created_by VARCHAR(255) NOT NULL,
                ai_generated BOOLEAN DEFAULT true,
                created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                UNIQUE(name)
            );
            
            CREATE TABLE IF NOT EXISTS prefect.flow_registrations (
                id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                flow_id UUID REFERENCES prefect.flows(id) ON DELETE CASCADE,
                deployment_id VARCHAR(255) NOT NULL,
                status VARCHAR(50) NOT NULL DEFAULT 'registered',
                created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                UNIQUE(flow_id)
            );
            
            CREATE TABLE IF NOT EXISTS prefect.flow_executions (
                id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                flow_id UUID REFERENCES prefect.flows(id) ON DELETE CASCADE,
                flow_run_id VARCHAR(255),
                parameters JSONB DEFAULT '{}',
                status VARCHAR(50) NOT NULL DEFAULT 'pending',
                scheduled_for TIMESTAMP WITH TIME ZONE,
                started_at TIMESTAMP WITH TIME ZONE,
                completed_at TIMESTAMP WITH TIME ZONE,
                result JSONB,
                error_message TEXT,
                created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
            );
            
            CREATE INDEX IF NOT EXISTS idx_flows_name ON prefect.flows(name);
            CREATE INDEX IF NOT EXISTS idx_flows_created_by ON prefect.flows(created_by);
            CREATE INDEX IF NOT EXISTS idx_flow_executions_status ON prefect.flow_executions(status);
        """)
    logger.info("Database tables created/verified")

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    try:
        # Check database
        async with db_pool.acquire() as conn:
            await conn.fetchval("SELECT 1")
        
        # Check Redis
        await redis_client.ping()
        
        # Check Prefect API
        async with PrefectClient(api=PREFECT_API_URL) as client:
            await client.hello()
        
        return {"status": "healthy", "timestamp": datetime.utcnow()}
    except Exception as e:
        logger.error("Health check failed", error=str(e))
        raise HTTPException(status_code=503, detail="Service unhealthy")

@app.post("/flows", response_model=Dict[str, str])
async def create_flow(flow_def: FlowDefinition):
    """Create and store a new AI-generated flow"""
    try:
        flow_id = str(uuid.uuid4())
        
        # Store flow in database
        async with db_pool.acquire() as conn:
            await conn.execute("""
                INSERT INTO prefect.flows (id, name, description, python_code, parameters, tags, created_by, ai_generated)
                VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
            """, flow_id, flow_def.name, flow_def.description, flow_def.python_code, 
                json.dumps(flow_def.parameters), flow_def.tags, flow_def.created_by, flow_def.ai_generated)
        
        # Save flow code to file
        flow_file = FLOWS_DIR / f"{flow_id}.py"
        flow_file.write_text(flow_def.python_code)
        
        # Cache flow metadata in Redis
        await redis_client.hset(f"flow:{flow_id}", mapping={
            "name": flow_def.name,
            "description": flow_def.description,
            "created_by": flow_def.created_by,
            "created_at": datetime.utcnow().isoformat()
        })
        
        logger.info("Flow created", flow_id=flow_id, name=flow_def.name)
        return {"flow_id": flow_id, "status": "created"}
        
    except Exception as e:
        logger.error("Failed to create flow", error=str(e))
        raise HTTPException(status_code=500, detail=f"Failed to create flow: {str(e)}")

@app.post("/flows/{flow_id}/register")
async def register_flow(flow_id: str, background_tasks: BackgroundTasks):
    """Register a flow with Prefect for execution"""
    try:
        # Get flow from database
        async with db_pool.acquire() as conn:
            flow_data = await conn.fetchrow("""
                SELECT name, python_code, parameters FROM prefect.flows WHERE id = $1
            """, flow_id)
        
        if not flow_data:
            raise HTTPException(status_code=404, detail="Flow not found")
        
        # Register flow with Prefect in background
        background_tasks.add_task(register_flow_with_prefect, flow_id, flow_data)
        
        return {"flow_id": flow_id, "status": "registration_started"}
        
    except Exception as e:
        logger.error("Failed to register flow", flow_id=flow_id, error=str(e))
        raise HTTPException(status_code=500, detail=f"Failed to register flow: {str(e)}")

async def register_flow_with_prefect(flow_id: str, flow_data):
    """Background task to register flow with Prefect"""
    try:
        # Execute the flow code to create the flow object
        flow_code = flow_data['python_code']
        flow_name = flow_data['name']
        
        # Create a temporary module to execute the flow code
        exec_globals = {
            'flow': flow,
            'task': task,
            '__name__': '__main__'
        }
        
        exec(flow_code, exec_globals)
        
        # Find the flow function (assumes it's decorated with @flow)
        flow_func = None
        for name, obj in exec_globals.items():
            if hasattr(obj, '_is_flow') and obj._is_flow:
                flow_func = obj
                break
        
        if not flow_func:
            raise Exception("No flow function found in code")
        
        # Create deployment
        deployment = Deployment.build_from_flow(
            flow=flow_func,
            name=f"{flow_name}-deployment",
            work_pool_name="default-pool"
        )
        
        deployment_id = await deployment.apply()
        
        # Store registration in database
        async with db_pool.acquire() as conn:
            await conn.execute("""
                INSERT INTO prefect.flow_registrations (flow_id, deployment_id, status)
                VALUES ($1, $2, 'registered')
                ON CONFLICT (flow_id) DO UPDATE SET
                    deployment_id = EXCLUDED.deployment_id,
                    status = 'registered'
            """, flow_id, str(deployment_id))
        
        logger.info("Flow registered with Prefect", flow_id=flow_id, deployment_id=str(deployment_id))
        
    except Exception as e:
        logger.error("Failed to register flow with Prefect", flow_id=flow_id, error=str(e))
        
        # Update status to failed
        async with db_pool.acquire() as conn:
            await conn.execute("""
                INSERT INTO prefect.flow_registrations (flow_id, deployment_id, status)
                VALUES ($1, '', 'failed')
                ON CONFLICT (flow_id) DO UPDATE SET status = 'failed'
            """, flow_id)

@app.post("/flows/{flow_id}/execute")
async def execute_flow(flow_id: str, execution: FlowExecution):
    """Execute a registered flow"""
    try:
        # Get flow registration
        async with db_pool.acquire() as conn:
            registration = await conn.fetchrow("""
                SELECT deployment_id, status FROM prefect.flow_registrations WHERE flow_id = $1
            """, flow_id)
        
        if not registration or registration['status'] != 'registered':
            raise HTTPException(status_code=400, detail="Flow not registered or registration failed")
        
        # Create flow run via Prefect API
        async with PrefectClient(api=PREFECT_API_URL) as client:
            flow_run = await client.create_flow_run_from_deployment(
                deployment_id=registration['deployment_id'],
                parameters=execution.parameters,
                scheduled_start_time=execution.scheduled_for
            )
        
        # Store execution record
        async with db_pool.acquire() as conn:
            execution_id = await conn.fetchval("""
                INSERT INTO prefect.flow_executions (flow_id, flow_run_id, parameters, scheduled_for, status)
                VALUES ($1, $2, $3, $4, 'submitted')
                RETURNING id
            """, flow_id, str(flow_run.id), json.dumps(execution.parameters), execution.scheduled_for)
        
        logger.info("Flow execution submitted", flow_id=flow_id, flow_run_id=str(flow_run.id))
        
        return {
            "execution_id": str(execution_id),
            "flow_run_id": str(flow_run.id),
            "status": "submitted"
        }
        
    except Exception as e:
        logger.error("Failed to execute flow", flow_id=flow_id, error=str(e))
        raise HTTPException(status_code=500, detail=f"Failed to execute flow: {str(e)}")

@app.get("/flows")
async def list_flows(created_by: Optional[str] = None, limit: int = 50, offset: int = 0):
    """List stored flows"""
    try:
        query = "SELECT id, name, description, created_by, ai_generated, created_at FROM prefect.flows"
        params = []
        
        if created_by:
            query += " WHERE created_by = $1"
            params.append(created_by)
        
        query += " ORDER BY created_at DESC LIMIT $" + str(len(params) + 1) + " OFFSET $" + str(len(params) + 2)
        params.extend([limit, offset])
        
        async with db_pool.acquire() as conn:
            rows = await conn.fetch(query, *params)
        
        flows = [dict(row) for row in rows]
        return {"flows": flows, "total": len(flows)}
        
    except Exception as e:
        logger.error("Failed to list flows", error=str(e))
        raise HTTPException(status_code=500, detail=f"Failed to list flows: {str(e)}")

@app.get("/flows/{flow_id}")
async def get_flow(flow_id: str):
    """Get flow details"""
    try:
        async with db_pool.acquire() as conn:
            flow_data = await conn.fetchrow("""
                SELECT * FROM prefect.flows WHERE id = $1
            """, flow_id)
        
        if not flow_data:
            raise HTTPException(status_code=404, detail="Flow not found")
        
        # Get registration status
        async with db_pool.acquire() as conn:
            registration = await conn.fetchrow("""
                SELECT deployment_id, status, created_at FROM prefect.flow_registrations WHERE flow_id = $1
            """, flow_id)
        
        flow_dict = dict(flow_data)
        if registration:
            flow_dict['registration'] = dict(registration)
        
        return flow_dict
        
    except Exception as e:
        logger.error("Failed to get flow", flow_id=flow_id, error=str(e))
        raise HTTPException(status_code=500, detail=f"Failed to get flow: {str(e)}")

@app.get("/flows/{flow_id}/executions")
async def get_flow_executions(flow_id: str, limit: int = 20):
    """Get flow execution history"""
    try:
        async with db_pool.acquire() as conn:
            executions = await conn.fetch("""
                SELECT * FROM prefect.flow_executions 
                WHERE flow_id = $1 
                ORDER BY created_at DESC 
                LIMIT $2
            """, flow_id, limit)
        
        return {"executions": [dict(row) for row in executions]}
        
    except Exception as e:
        logger.error("Failed to get flow executions", flow_id=flow_id, error=str(e))
        raise HTTPException(status_code=500, detail=f"Failed to get flow executions: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)