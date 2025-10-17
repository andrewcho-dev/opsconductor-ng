# OpsConductor NG

**AI-Powered IT Operations Automation Platform**

OpsConductor NG is a modern IT operations automation platform that uses AI to understand natural language requests and execute complex IT operations across your infrastructure.

## 🚀 Quick Start

### New Installation

**First time setup?** Follow the complete installation guide:

📖 **[INSTALLATION.md](INSTALLATION.md)** - Complete step-by-step installation guide

### Existing Installation

```bash
# Start all services
docker compose up -d

# Check status
docker compose ps

# View logs
docker compose logs -f
```

### Access the Platform

- **Frontend**: http://localhost:8000
- **AI Pipeline API**: http://localhost:8006
- **Kong API Gateway**: http://localhost:8008
- **Keycloak Admin**: http://localhost:8080
- **Ollama API**: http://localhost:11434

## 📋 What is OpsConductor NG?

OpsConductor NG automates IT operations using a 4-stage AI pipeline:

1. **Understand & Select** - Combined Stage AB analyzes intent and selects tools
2. **Plan** - Creates detailed execution plan
3. **Answer** - Formats responses for human readability
4. **Execute** - Runs operations through specialized services

### Example Use Cases

- "Check the status of all web servers"
- "Restart the database service on prod-db-01"
- "Show me network connectivity to 10.0.1.50"
- "List all Linux servers in the datacenter"

## 🏗️ Architecture

OpsConductor NG uses a clean microservices architecture:

### Core Components

- **AI Pipeline** - 4-stage LLM-powered decision engine (merged Stage A+B)
- **Automation Service** - Command execution and workflow management
- **Asset Service** - Infrastructure asset management
- **Network Analyzer** - Network monitoring and analysis
- **Communication Service** - Notifications and alerts

### Infrastructure

- **PostgreSQL 17** - Primary database with pgvector
- **Redis 7** - Message queue and caching
- **Ollama 0.11** - Local LLM inference with GPU acceleration
- **Kong 3.4** - API Gateway
- **Keycloak 22** - Identity and access management
- **React Frontend** - Modern web interface

For detailed architecture information, see **[ARCHITECTURE.md](ARCHITECTURE.md)**

## 💻 System Requirements

### Hardware

- **CPU**: 4+ cores (8+ recommended)
- **RAM**: 16 GB minimum (32 GB recommended)
- **Storage**: 100 GB free space (SSD recommended)
- **GPU**: NVIDIA GPU with 8GB+ VRAM (24GB recommended)

### Software

- **OS**: Ubuntu 22.04 LTS or later
- **Docker**: 24.0+ with Compose V2
- **NVIDIA Driver**: 535+
- **NVIDIA Container Toolkit**: Latest

### Tested GPU Configurations

| GPU | VRAM | Status | Notes |
|-----|------|--------|-------|
| RTX 3060 | 12 GB | ✅ Works | Limited context (8K tokens) |
| RTX 3090 Ti | 24 GB | ✅ Recommended | 32K context, optimal performance |
| RTX 4090 | 24 GB | ✅ Best | 64K context with FP8 support |

## 📚 Documentation

- **[INSTALLATION.md](INSTALLATION.md)** - Complete installation guide
- **[ARCHITECTURE.md](ARCHITECTURE.md)** - System architecture and design
- **[.env.example](.env.example)** - Environment configuration template

## 🔧 Development

### Project Structure

```
opsconductor-ng/
├── pipeline/                # 4-stage AI pipeline
│   ├── stages/              # Individual pipeline stages
│   └── orchestrator_v2.py   # Main pipeline controller (Combined Stage AB)
├── automation-service/      # Command execution
├── asset-service/           # Asset management
├── network-analyzer-service/# Network monitoring
├── communication-service/   # Notifications
├── frontend/                # React web interface
├── shared/                  # Common utilities
├── database/                # Database schema
│   └── init-schema.sql      # Complete database schema
├── kong/                    # API Gateway config
├── keycloak/                # Identity provider config
├── tests/                   # Test suite
│   ├── e2e/                 # End-to-end tests
│   └── test_phase_*.py      # Pipeline stage tests
└── docker-compose.yml       # Service orchestration
```

### Technologies

- **Backend**: Python 3.11, FastAPI 0.104.1, PostgreSQL 17, Redis 7
- **AI**: Ollama 0.11.11 with Qwen2.5-7B-Instruct model
- **Frontend**: TypeScript 4.9.5, React 18.2.0, Bootstrap 5.3.8
- **Data Visualization**: AG Grid 32.3.9
- **Infrastructure**: Docker, Kong 3.4, Keycloak 22.0.1
- **Testing**: pytest 7.4.3, pytest-asyncio 0.21.1, Playwright

## 🧪 Testing

```bash
# Run backend tests
pytest tests/

# Run E2E tests
pytest tests/e2e/
```

## 📝 License

[Your License Here]

## 🤝 Contributing

[Your Contributing Guidelines Here]

---

**OpsConductor NG** - Bringing AI-powered automation to IT operations.