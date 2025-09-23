# AI Event-Driven System - Development Setup Guide

## Overview

This guide provides step-by-step instructions for setting up a development environment for the AI Event-Driven System. It covers local development, testing, and integration with the existing OpsConductor platform.

## Prerequisites

### System Requirements
- **Operating System**: Linux (Ubuntu 20.04+), macOS (10.15+), or Windows 10+ with WSL2
- **Memory**: 16GB RAM minimum, 32GB recommended
- **Storage**: 50GB free space minimum
- **CPU**: 4 cores minimum, 8 cores recommended
- **GPU**: Optional NVIDIA GPU for enhanced AI performance

### Required Software
```bash
# Core development tools
- Docker 24.0+
- Docker Compose 2.20+
- Python 3.11+
- Node.js 18+
- Git 2.30+

# Database tools
- PostgreSQL 16+ (for local development)
- Redis 7+

# Development tools
- VS Code or PyCharm
- Postman or similar API testing tool
- curl and jq for command-line testing
```

## Development Environment Setup

### 1. Repository Setup

#### Clone and Initialize
```bash
# Clone the repository (if not already done)
git clone <repository-url>
cd opsconductor-ng

# Verify AI-EVENT-DRIVEN folder exists
ls -la AI-EVENT-DRIVEN/

# Create development branch
git checkout -b feature/ai-event-driven-development
```

#### Create Development Directory Structure
```bash
# Create service directories
mkdir -p AI-EVENT-DRIVEN/event-processing-service
mkdir -p AI-EVENT-DRIVEN/autonomous-response-service
mkdir -p AI-EVENT-DRIVEN/shared
mkdir -p AI-EVENT-DRIVEN/tests
mkdir -p AI-EVENT-DRIVEN/docs
mkdir -p AI-EVENT-DRIVEN/examples
mkdir -p AI-EVENT-DRIVEN/scripts

# Create subdirectories for each service
mkdir -p AI-EVENT-DRIVEN/event-processing-service/{src,tests,config,docker}
mkdir -p AI-EVENT-DRIVEN/autonomous-response-service/{src,tests,config,docker}
```

### 2. Database Setup

#### Enhanced Database Schema
```bash
# Create development database setup script
cat > AI-EVENT-DRIVEN/scripts/setup-dev-database.sh << 'EOF'
#!/bin/bash

# Setup development database for AI Event-Driven System
echo "Setting up AI Event-Driven development database..."

# Connect to PostgreSQL and create schemas
psql -h localhost -U postgres -d opsconductor << SQL
-- Create event-driven schemas
CREATE SCHEMA IF NOT EXISTS events;
CREATE SCHEMA IF NOT EXISTS rules;
CREATE SCHEMA IF NOT EXISTS autonomous;

-- Grant permissions
GRANT ALL PRIVILEGES ON SCHEMA events TO postgres;
GRANT ALL PRIVILEGES ON SCHEMA rules TO postgres;
GRANT ALL PRIVILEGES ON SCHEMA autonomous TO postgres;

-- Create development-specific tables
\i AI-EVENT-DRIVEN/database/dev-schema.sql

-- Insert test data
\i AI-EVENT-DRIVEN/database/dev-test-data.sql

SQL

echo "Database setup complete!"
EOF

chmod +x AI-EVENT-DRIVEN/scripts/setup-dev-database.sh
```

#### Development Database Schema
```sql
-- File: AI-EVENT-DRIVEN/database/dev-schema.sql
-- Development database schema for AI Event-Driven System

-- Events Schema Tables
CREATE TABLE IF NOT EXISTS events.raw_events (
    id BIGSERIAL PRIMARY KEY,
    source_system VARCHAR(100) NOT NULL,
    source_type VARCHAR(50) NOT NULL,
    raw_data JSONB NOT NULL,
    received_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    processed BOOLEAN DEFAULT FALSE,
    processing_errors TEXT[]
);

CREATE TABLE IF NOT EXISTS events.processed_events (
    id BIGSERIAL PRIMARY KEY,
    raw_event_id BIGINT REFERENCES events.raw_events(id),
    event_type VARCHAR(100) NOT NULL,
    severity VARCHAR(20) NOT NULL,
    source_host VARCHAR(255),
    source_service VARCHAR(100),
    title VARCHAR(500) NOT NULL,
    description TEXT,
    event_data JSONB,
    tags VARCHAR(50)[],
    occurred_at TIMESTAMP WITH TIME ZONE NOT NULL,
    processed_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    correlation_id UUID DEFAULT gen_random_uuid(),
    parent_event_id BIGINT REFERENCES events.processed_events(id)
);

CREATE TABLE IF NOT EXISTS events.event_correlations (
    id BIGSERIAL PRIMARY KEY,
    correlation_id UUID NOT NULL,
    correlation_type VARCHAR(50) NOT NULL,
    primary_event_id BIGINT REFERENCES events.processed_events(id),
    related_event_ids BIGINT[],
    correlation_score DECIMAL(3,2),
    correlation_reason TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Rules Schema Tables
CREATE TABLE IF NOT EXISTS rules.trigger_rules (
    id BIGSERIAL PRIMARY KEY,
    rule_name VARCHAR(200) NOT NULL,
    rule_description TEXT,
    event_conditions JSONB NOT NULL,
    severity_threshold VARCHAR(20),
    time_window_minutes INTEGER,
    max_triggers_per_hour INTEGER DEFAULT 10,
    active BOOLEAN DEFAULT TRUE,
    created_by INTEGER,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS rules.response_templates (
    id BIGSERIAL PRIMARY KEY,
    template_name VARCHAR(200) NOT NULL,
    template_type VARCHAR(50) NOT NULL,
    trigger_rule_id INTEGER REFERENCES rules.trigger_rules(id),
    response_definition JSONB NOT NULL,
    approval_required BOOLEAN DEFAULT FALSE,
    rollback_supported BOOLEAN DEFAULT FALSE,
    max_execution_time_minutes INTEGER DEFAULT 30,
    active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Autonomous Schema Tables
CREATE TABLE IF NOT EXISTS autonomous.decision_log (
    id BIGSERIAL PRIMARY KEY,
    event_id BIGINT REFERENCES events.processed_events(id),
    decision_type VARCHAR(50) NOT NULL,
    confidence_score DECIMAL(3,2) NOT NULL,
    reasoning TEXT NOT NULL,
    recommended_actions JSONB,
    human_override BOOLEAN DEFAULT FALSE,
    override_reason TEXT,
    decision_outcome VARCHAR(50),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create indexes for development performance
CREATE INDEX IF NOT EXISTS idx_events_correlation_id ON events.processed_events(correlation_id);
CREATE INDEX IF NOT EXISTS idx_events_severity_time ON events.processed_events(severity, occurred_at);
CREATE INDEX IF NOT EXISTS idx_rules_active ON rules.trigger_rules(active) WHERE active = true;
CREATE INDEX IF NOT EXISTS idx_autonomous_decisions_event ON autonomous.decision_log(event_id);
```

### 3. Python Development Environment

#### Virtual Environment Setup
```bash
# Create Python virtual environment for AI Event-Driven development
cd AI-EVENT-DRIVEN
python3.11 -m venv venv
source venv/bin/activate

# Upgrade pip and install development tools
pip install --upgrade pip setuptools wheel

# Create requirements files
cat > requirements.txt << 'EOF'
# Core FastAPI and async dependencies
fastapi==0.104.1
uvicorn[standard]==0.24.0
pydantic[email]==2.5.0
python-multipart==0.0.6

# Database and caching
asyncpg==0.29.0
redis==5.0.1
sqlalchemy[asyncio]==2.0.23

# AI and ML libraries
openai==1.3.7
transformers==4.35.2
torch==2.1.1
scikit-learn==1.3.2
numpy==1.24.3
pandas==2.1.3

# HTTP and networking
httpx==0.25.2
aiohttp==3.9.1
websockets==12.0

# Logging and monitoring
structlog==23.2.0
prometheus-client==0.19.0

# Testing
pytest==7.4.3
pytest-asyncio==0.21.1
pytest-mock==3.12.0
httpx==0.25.2

# Development tools
black==23.11.0
flake8==6.1.0
mypy==1.7.1
pre-commit==3.5.0
EOF

cat > requirements-dev.txt << 'EOF'
# Include production requirements
-r requirements.txt

# Additional development tools
jupyter==1.0.0
ipython==8.17.2
pytest-cov==4.1.0
pytest-xdist==3.5.0
factory-boy==3.3.0
faker==20.1.0
debugpy==1.8.0
EOF

# Install dependencies
pip install -r requirements-dev.txt
```

#### Development Configuration
```python
# File: AI-EVENT-DRIVEN/shared/config.py
"""Development configuration for AI Event-Driven System"""

import os
from typing import Optional
from pydantic import BaseSettings

class DevelopmentConfig(BaseSettings):
    """Development configuration settings"""
    
    # Environment
    ENVIRONMENT: str = "development"
    DEBUG: bool = True
    LOG_LEVEL: str = "DEBUG"
    
    # Database
    DB_HOST: str = "localhost"
    DB_PORT: int = 5432
    DB_NAME: str = "opsconductor"
    DB_USER: str = "postgres"
    DB_PASSWORD: str = "postgres123"
    
    # Redis
    REDIS_URL: str = "redis://localhost:6379"
    
    # Service URLs (for local development)
    AI_BRAIN_URL: str = "http://localhost:3005"
    ASSET_SERVICE_URL: str = "http://localhost:3002"
    AUTOMATION_SERVICE_URL: str = "http://localhost:3003"
    COMMUNICATION_SERVICE_URL: str = "http://localhost:3004"
    
    # Event Processing Service
    EVENT_PROCESSING_PORT: int = 3009
    EVENT_PROCESSING_HOST: str = "0.0.0.0"
    
    # Autonomous Response Service
    AUTONOMOUS_RESPONSE_PORT: int = 3011
    AUTONOMOUS_RESPONSE_HOST: str = "0.0.0.0"
    
    # Development features
    ENABLE_DEBUG_ENDPOINTS: bool = True
    ENABLE_TEST_DATA_GENERATION: bool = True
    MOCK_EXTERNAL_SERVICES: bool = True
    
    # AI Configuration
    OPENAI_API_KEY: Optional[str] = None
    OLLAMA_HOST: str = "http://localhost:11434"
    
    class Config:
        env_file = ".env.development"
        case_sensitive = True

# Global configuration instance
config = DevelopmentConfig()
```

### 4. Service Development Setup

#### Event Processing Service Structure
```bash
# Create Event Processing Service structure
mkdir -p AI-EVENT-DRIVEN/event-processing-service/src/{api,core,adapters,processors}

# Main application file
cat > AI-EVENT-DRIVEN/event-processing-service/src/main.py << 'EOF'
"""
Event Processing Service - Main Application
Development version with enhanced debugging and testing features
"""

import logging
import uvicorn
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from api.events import events_router
from api.rules import rules_router
from api.debug import debug_router  # Development only
from core.config import config
from core.database import init_database
from core.redis_client import init_redis

# Configure logging for development
logging.basicConfig(
    level=getattr(logging, config.LOG_LEVEL),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Create FastAPI application
app = FastAPI(
    title="OpsConductor Event Processing Service",
    description="AI-powered event processing and correlation service",
    version="1.0.0-dev",
    debug=config.DEBUG
)

# Add CORS middleware for development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"] if config.DEBUG else ["http://localhost:3100"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(events_router, prefix="/api/v1/events", tags=["events"])
app.include_router(rules_router, prefix="/api/v1/rules", tags=["rules"])

# Include debug router in development
if config.ENABLE_DEBUG_ENDPOINTS:
    app.include_router(debug_router, prefix="/api/v1/debug", tags=["debug"])

@app.on_event("startup")
async def startup_event():
    """Initialize services on startup"""
    logger.info("Starting Event Processing Service in development mode")
    
    # Initialize database connection
    await init_database()
    logger.info("Database connection initialized")
    
    # Initialize Redis connection
    await init_redis()
    logger.info("Redis connection initialized")
    
    logger.info("Event Processing Service startup complete")

@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown"""
    logger.info("Shutting down Event Processing Service")

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "event-processing-service",
        "version": "1.0.0-dev",
        "environment": config.ENVIRONMENT
    }

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Global exception handler for development debugging"""
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={
            "error": "Internal server error",
            "detail": str(exc) if config.DEBUG else "An error occurred",
            "path": str(request.url.path)
        }
    )

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host=config.EVENT_PROCESSING_HOST,
        port=config.EVENT_PROCESSING_PORT,
        reload=True,  # Enable auto-reload in development
        log_level=config.LOG_LEVEL.lower()
    )
EOF
```

#### Autonomous Response Service Structure
```bash
# Create Autonomous Response Service structure
mkdir -p AI-EVENT-DRIVEN/autonomous-response-service/src/{api,core,engines,safety}

# Main application file
cat > AI-EVENT-DRIVEN/autonomous-response-service/src/main.py << 'EOF'
"""
Autonomous Response Service - Main Application
Development version with safety controls and debugging
"""

import logging
import uvicorn
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from api.autonomous import autonomous_router
from api.executions import executions_router
from api.debug import debug_router  # Development only
from core.config import config
from core.database import init_database
from core.redis_client import init_redis

# Configure logging for development
logging.basicConfig(
    level=getattr(logging, config.LOG_LEVEL),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Create FastAPI application
app = FastAPI(
    title="OpsConductor Autonomous Response Service",
    description="AI-powered autonomous response and safety control service",
    version="1.0.0-dev",
    debug=config.DEBUG
)

# Add CORS middleware for development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"] if config.DEBUG else ["http://localhost:3100"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(autonomous_router, prefix="/api/v1/autonomous", tags=["autonomous"])
app.include_router(executions_router, prefix="/api/v1/executions", tags=["executions"])

# Include debug router in development
if config.ENABLE_DEBUG_ENDPOINTS:
    app.include_router(debug_router, prefix="/api/v1/debug", tags=["debug"])

@app.on_event("startup")
async def startup_event():
    """Initialize services on startup"""
    logger.info("Starting Autonomous Response Service in development mode")
    
    # Initialize database connection
    await init_database()
    logger.info("Database connection initialized")
    
    # Initialize Redis connection
    await init_redis()
    logger.info("Redis connection initialized")
    
    logger.info("Autonomous Response Service startup complete")

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "autonomous-response-service",
        "version": "1.0.0-dev",
        "environment": config.ENVIRONMENT,
        "safety_mode": "enabled"  # Always enabled in development
    }

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host=config.AUTONOMOUS_RESPONSE_HOST,
        port=config.AUTONOMOUS_RESPONSE_PORT,
        reload=True,  # Enable auto-reload in development
        log_level=config.LOG_LEVEL.lower()
    )
EOF
```

### 5. Development Docker Setup

#### Development Docker Compose
```yaml
# File: AI-EVENT-DRIVEN/docker-compose.dev.yml
# Development environment for AI Event-Driven System

version: '3.8'

services:
  # Development Event Processing Service
  event-processing-service-dev:
    build:
      context: ./event-processing-service
      dockerfile: Dockerfile.dev
    container_name: opsconductor-event-processing-dev
    ports:
      - "3009:3009"
      - "5678:5678"  # Debug port
    environment:
      ENVIRONMENT: development
      DEBUG: "true"
      LOG_LEVEL: DEBUG
      DB_HOST: postgres
      REDIS_URL: redis://redis:6379/10
      ENABLE_DEBUG_ENDPOINTS: "true"
      ENABLE_TEST_DATA_GENERATION: "true"
    volumes:
      - ./event-processing-service/src:/app/src
      - ./shared:/app/shared
      - ./tests:/app/tests
    depends_on:
      - postgres
      - redis
    networks:
      - opsconductor-net
    command: ["python", "-m", "debugpy", "--listen", "0.0.0.0:5678", "--wait-for-client", "src/main.py"]

  # Development Autonomous Response Service
  autonomous-response-service-dev:
    build:
      context: ./autonomous-response-service
      dockerfile: Dockerfile.dev
    container_name: opsconductor-autonomous-response-dev
    ports:
      - "3011:3011"
      - "5679:5679"  # Debug port
    environment:
      ENVIRONMENT: development
      DEBUG: "true"
      LOG_LEVEL: DEBUG
      DB_HOST: postgres
      REDIS_URL: redis://redis:6379/11
      ENABLE_DEBUG_ENDPOINTS: "true"
      MOCK_EXTERNAL_SERVICES: "true"
    volumes:
      - ./autonomous-response-service/src:/app/src
      - ./shared:/app/shared
      - ./tests:/app/tests
    depends_on:
      - postgres
      - redis
      - event-processing-service-dev
    networks:
      - opsconductor-net
    command: ["python", "-m", "debugpy", "--listen", "0.0.0.0:5679", "--wait-for-client", "src/main.py"]

  # Development Database with test data
  postgres-dev:
    image: postgres:16-alpine
    container_name: opsconductor-postgres-dev
    environment:
      POSTGRES_DB: opsconductor_dev
      POSTGRES_USER: postgres
      POSTGRES_PASSWORD: postgres123
    ports:
      - "5433:5432"  # Different port for development
    volumes:
      - postgres_dev_data:/var/lib/postgresql/data
      - ./database:/docker-entrypoint-initdb.d
    networks:
      - opsconductor-net

  # Development Redis
  redis-dev:
    image: redis:7.4-alpine
    container_name: opsconductor-redis-dev
    ports:
      - "6380:6379"  # Different port for development
    volumes:
      - redis_dev_data:/data
    networks:
      - opsconductor-net
    command: redis-server --appendonly yes

volumes:
  postgres_dev_data:
  redis_dev_data:

networks:
  opsconductor-net:
    external: true
```

### 6. Testing Framework Setup

#### Test Structure
```bash
# Create comprehensive test structure
mkdir -p AI-EVENT-DRIVEN/tests/{unit,integration,e2e,fixtures,mocks}

# Unit tests
mkdir -p AI-EVENT-DRIVEN/tests/unit/{event_processing,autonomous_response,shared}

# Integration tests
mkdir -p AI-EVENT-DRIVEN/tests/integration/{database,redis,services}

# End-to-end tests
mkdir -p AI-EVENT-DRIVEN/tests/e2e/{workflows,scenarios}
```

#### Test Configuration
```python
# File: AI-EVENT-DRIVEN/tests/conftest.py
"""Pytest configuration and fixtures for AI Event-Driven System tests"""

import asyncio
import pytest
import pytest_asyncio
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

from shared.config import config
from shared.database import Base

# Test database URL
TEST_DATABASE_URL = f"postgresql+asyncpg://{config.DB_USER}:{config.DB_PASSWORD}@{config.DB_HOST}:{config.DB_PORT}/opsconductor_test"

@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()

@pytest_asyncio.fixture(scope="session")
async def test_engine():
    """Create test database engine"""
    engine = create_async_engine(TEST_DATABASE_URL, echo=True)
    
    # Create all tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    yield engine
    
    # Cleanup
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    
    await engine.dispose()

@pytest_asyncio.fixture
async def test_session(test_engine):
    """Create test database session"""
    async_session = sessionmaker(
        test_engine, class_=AsyncSession, expire_on_commit=False
    )
    
    async with async_session() as session:
        yield session

@pytest_asyncio.fixture
async def event_processing_client():
    """Create test client for Event Processing Service"""
    from event_processing_service.src.main import app
    
    async with AsyncClient(app=app, base_url="http://test") as client:
        yield client

@pytest_asyncio.fixture
async def autonomous_response_client():
    """Create test client for Autonomous Response Service"""
    from autonomous_response_service.src.main import app
    
    async with AsyncClient(app=app, base_url="http://test") as client:
        yield client

# Test data fixtures
@pytest.fixture
def sample_event_data():
    """Sample event data for testing"""
    return {
        "source": "test_monitoring",
        "source_type": "test",
        "event_type": "threshold_breach",
        "severity": "critical",
        "host": "test-server-01",
        "service": "nginx",
        "title": "High CPU Usage",
        "description": "CPU usage exceeded 95% threshold",
        "timestamp": "2024-12-20T10:30:00Z",
        "metadata": {
            "cpu_usage": 95.5,
            "threshold": 95.0,
            "duration": "5m"
        },
        "tags": ["production", "web-server"]
    }

@pytest.fixture
def sample_trigger_rule():
    """Sample trigger rule for testing"""
    return {
        "rule_name": "Test High CPU Rule",
        "rule_description": "Test rule for high CPU usage",
        "event_conditions": {
            "event_type": "threshold_breach",
            "severity": ["critical", "high"],
            "metadata.cpu_usage": {"$gt": 90}
        },
        "time_window_minutes": 5,
        "max_triggers_per_hour": 3,
        "active": True
    }
```

### 7. Development Scripts

#### Development Startup Script
```bash
# File: AI-EVENT-DRIVEN/scripts/start-dev.sh
#!/bin/bash

echo "🚀 Starting AI Event-Driven System Development Environment"

# Check prerequisites
echo "📋 Checking prerequisites..."
command -v docker >/dev/null 2>&1 || { echo "❌ Docker is required but not installed."; exit 1; }
command -v docker-compose >/dev/null 2>&1 || { echo "❌ Docker Compose is required but not installed."; exit 1; }
command -v python3.11 >/dev/null 2>&1 || { echo "❌ Python 3.11 is required but not installed."; exit 1; }

# Setup Python virtual environment
echo "🐍 Setting up Python virtual environment..."
if [ ! -d "venv" ]; then
    python3.11 -m venv venv
fi
source venv/bin/activate
pip install -r requirements-dev.txt

# Setup database
echo "🗄️ Setting up development database..."
./scripts/setup-dev-database.sh

# Start development services
echo "🐳 Starting development services..."
docker-compose -f docker-compose.dev.yml up -d

# Wait for services to be ready
echo "⏳ Waiting for services to be ready..."
sleep 10

# Run health checks
echo "🏥 Running health checks..."
curl -f http://localhost:3009/health || echo "❌ Event Processing Service not ready"
curl -f http://localhost:3011/health || echo "❌ Autonomous Response Service not ready"

echo "✅ Development environment is ready!"
echo ""
echo "📊 Service URLs:"
echo "  Event Processing Service: http://localhost:3009"
echo "  Autonomous Response Service: http://localhost:3011"
echo "  Event Processing API Docs: http://localhost:3009/docs"
echo "  Autonomous Response API Docs: http://localhost:3011/docs"
echo ""
echo "🧪 To run tests:"
echo "  pytest tests/"
echo ""
echo "🐛 To debug:"
echo "  Attach debugger to port 5678 (Event Processing) or 5679 (Autonomous Response)"
```

#### Test Runner Script
```bash
# File: AI-EVENT-DRIVEN/scripts/run-tests.sh
#!/bin/bash

echo "🧪 Running AI Event-Driven System Tests"

# Activate virtual environment
source venv/bin/activate

# Set test environment variables
export ENVIRONMENT=test
export DB_NAME=opsconductor_test
export REDIS_URL=redis://localhost:6380/15

# Run different test suites
echo "📝 Running unit tests..."
pytest tests/unit/ -v --cov=src --cov-report=html --cov-report=term

echo "🔗 Running integration tests..."
pytest tests/integration/ -v

echo "🎭 Running end-to-end tests..."
pytest tests/e2e/ -v

echo "📊 Test coverage report generated in htmlcov/"
echo "✅ All tests completed!"
```

### 8. IDE Configuration

#### VS Code Configuration
```json
// File: AI-EVENT-DRIVEN/.vscode/settings.json
{
    "python.defaultInterpreterPath": "./venv/bin/python",
    "python.linting.enabled": true,
    "python.linting.pylintEnabled": false,
    "python.linting.flake8Enabled": true,
    "python.formatting.provider": "black",
    "python.testing.pytestEnabled": true,
    "python.testing.pytestArgs": [
        "tests"
    ],
    "files.exclude": {
        "**/__pycache__": true,
        "**/*.pyc": true,
        "**/venv": true,
        "**/.pytest_cache": true
    },
    "editor.formatOnSave": true,
    "editor.codeActionsOnSave": {
        "source.organizeImports": true
    }
}
```

```json
// File: AI-EVENT-DRIVEN/.vscode/launch.json
{
    "version": "0.2.0",
    "configurations": [
        {
            "name": "Debug Event Processing Service",
            "type": "python",
            "request": "attach",
            "connect": {
                "host": "localhost",
                "port": 5678
            },
            "pathMappings": [
                {
                    "localRoot": "${workspaceFolder}/event-processing-service/src",
                    "remoteRoot": "/app/src"
                }
            ]
        },
        {
            "name": "Debug Autonomous Response Service",
            "type": "python",
            "request": "attach",
            "connect": {
                "host": "localhost",
                "port": 5679
            },
            "pathMappings": [
                {
                    "localRoot": "${workspaceFolder}/autonomous-response-service/src",
                    "remoteRoot": "/app/src"
                }
            ]
        },
        {
            "name": "Run Tests",
            "type": "python",
            "request": "launch",
            "program": "${workspaceFolder}/venv/bin/pytest",
            "args": ["tests/", "-v"],
            "console": "integratedTerminal",
            "cwd": "${workspaceFolder}"
        }
    ]
}
```

## Development Workflow

### Daily Development Process
1. **Start Development Environment**
   ```bash
   cd AI-EVENT-DRIVEN
   ./scripts/start-dev.sh
   ```

2. **Make Code Changes**
   - Services auto-reload on file changes
   - Use debugger for complex issues
   - Write tests for new functionality

3. **Run Tests**
   ```bash
   ./scripts/run-tests.sh
   ```

4. **Test Integration**
   ```bash
   # Test event processing
   curl -X POST http://localhost:3009/api/v1/events/webhook \
     -H "Content-Type: application/json" \
     -d '{"source": "test", "event_type": "test", "severity": "info", "title": "Test Event"}'
   
   # Test autonomous response
   curl -X POST http://localhost:3011/api/v1/autonomous/analyze \
     -H "Content-Type: application/json" \
     -d '{"event_id": 1, "context": {"business_hours": true}}'
   ```

5. **Commit Changes**
   ```bash
   git add .
   git commit -m "feat: implement event correlation algorithm"
   git push origin feature/ai-event-driven-development
   ```

### Debugging Tips
- Use VS Code debugger with remote attach for containerized services
- Check service logs: `docker-compose -f docker-compose.dev.yml logs -f service-name`
- Use Redis CLI to inspect queues: `redis-cli -p 6380`
- Use PostgreSQL client to inspect data: `psql -h localhost -p 5433 -U postgres -d opsconductor_dev`

---

**Document Version**: 1.0  
**Last Updated**: December 2024  
**Next Review**: Monthly during development