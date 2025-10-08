# OpsConductor NG - IT Operations Automation Platform

## 🏗️ Architecture Overview

OpsConductor NG is a modern IT operations automation platform built with a clean architecture approach. The system uses a 4-stage AI pipeline powered by Ollama LLM for decision making, with specialized microservices for execution.

### Core Components

- **🧠 AI Pipeline**: 4-stage LLM-driven decision engine
- **🔧 Specialized Services**: Dedicated microservices for specific operations
- **🔐 Identity Management**: Keycloak-based authentication and authorization
- **🌐 API Gateway**: Kong for centralized routing and security
- **🖥️ Frontend**: React TypeScript web interface

### Execution Flow

```
User Request → AI Pipeline (4-Stage Processing) → Specialized Services → Response
```

## 🚀 Quick Start

### New Installation

**First time setting up OpsConductor NG?** Follow the complete installation guide:

📖 **[INSTALLATION.md](INSTALLATION.md)** - Complete step-by-step installation guide

This includes:
- Prerequisites and system requirements
- GPU configuration (RTX 3060, 3090 Ti, 4090)
- Docker and NVIDIA setup
- Environment configuration
- Troubleshooting common issues

### Existing Installation

```bash
# Standard deployment with development volume mounts
docker compose up -d

# Verify deployment
./verify-deployment.sh

# Check system status
./scripts/status.sh
```

### Access Services

- **Frontend**: http://localhost:3100
- **AI Pipeline API**: http://localhost:3005
- **Kong API Gateway**: http://localhost:3000
- **Keycloak Admin**: http://localhost:8090
- **vLLM API**: http://localhost:8000

### Test the System

```bash
# Run automated verification
./verify-deployment.sh

# Or test manually
curl -X POST http://localhost:3005/pipeline \
  -H "Content-Type: application/json" \
  -d '{
    "request": "Check system status",
    "context": {}
  }'
```

## 📋 System Architecture

### AI Pipeline (4-Stage Architecture)

The AI Pipeline processes user requests through four specialized stages:

1. **Stage A (Classifier)**: Analyzes and classifies user intent
2. **Stage B (Selector)**: Selects appropriate tools and services
3. **Stage C (Planner)**: Creates execution plan with detailed steps
4. **Stage D (Answerer)**: Formats final response to the user
5. **Stage E (Executor)**: Integrated execution (Phase 7)

### Specialized Services

- **Automation Service**: Command execution and workflow management
- **Asset Service**: Infrastructure asset management
- **Network Analyzer**: Network monitoring and analysis
- **Communication Service**: Notifications and alerts

### Infrastructure Components

- **PostgreSQL 17**: Primary database with multiple schemas
- **Redis 7**: Message queue and caching
- **Ollama 0.11**: Local LLM server with GPU acceleration
- **Kong 3.4**: API Gateway for routing and authentication
- **Keycloak 22**: Identity and access management

## 💻 Development

### Development Mode

For active development with live code reloading:

```bash
# Start in development mode with volume mounts
./scripts/dev-mode.sh

# View logs
./scripts/logs.sh

# Stop development environment
./scripts/stop-dev.sh
```

### Production Mode

For testing in a production-like environment:

```bash
# Start in production mode (no volume mounts)
./scripts/prod-mode.sh

# Stop production environment
./scripts/stop-prod.sh
```

## 🧪 Testing

The system includes comprehensive test suites:

```bash
# Run all tests
pytest tests/

# Run specific test phase
pytest tests/test_phase_1_stage_a.py
```

## 📁 Repository Structure

```
opsconductor-ng/
├── pipeline/                # 4-stage AI pipeline components
│   ├── stages/              # Individual pipeline stages
│   │   ├── stage_a/         # Intent classification
│   │   ├── stage_b/         # Tool selection
│   │   ├── stage_c/         # Execution planning
│   │   ├── stage_d/         # Response formatting
│   │   └── stage_e/         # Execution integration
│   ├── schemas/             # Data models for pipeline stages
│   └── orchestrator.py      # Main pipeline controller
├── automation-service/      # Command execution service
├── asset-service/           # Infrastructure management
├── network-analyzer-service/# Network monitoring and analysis
├── communication-service/   # Notifications and alerts
├── frontend/                # React TypeScript web interface
├── shared/                  # Common utilities and base classes
├── kong/                    # API Gateway configuration
├── keycloak/                # Identity provider configuration
├── scripts/                 # Utility scripts for operations
└── tests/                   # Comprehensive test suites
```

## 🔧 Technologies

- **Backend**: Python 3.12+, FastAPI, PostgreSQL, Redis
- **AI**: Ollama 0.11 with Qwen2.5 model, GPU acceleration
- **Frontend**: TypeScript 4.9, React 18.2, Bootstrap 5.3
- **Infrastructure**: Docker, Kong, Keycloak
- **Testing**: pytest, pytest-asyncio

## 📚 Documentation

### Getting Started
- **[INSTALLATION.md](INSTALLATION.md)** - Complete installation guide for new deployments
- **[DEPLOYMENT_CHECKLIST.md](DEPLOYMENT_CHECKLIST.md)** - Comprehensive deployment checklist
- **[RTX_3090Ti_SETUP.md](RTX_3090Ti_SETUP.md)** - GPU-specific setup guide

### Architecture & Development
- **[CLEAN_ARCHITECTURE.md](CLEAN_ARCHITECTURE.md)** - Detailed architecture overview
- **[PHASE_*_COMPLETION_REPORT.md](.)** - Implementation phase reports
- **[DOCKER_COMPOSE_CLEANUP.md](DOCKER_COMPOSE_CLEANUP.md)** - Infrastructure standardization

### Operations
- **[verify-deployment.sh](verify-deployment.sh)** - Automated deployment verification script
- **[start_vllm_3090ti.sh](start_vllm_3090ti.sh)** - vLLM startup helper with performance profiles

---

**OpsConductor NG: Clean architecture with clear separation of concerns and single responsibility per component.**