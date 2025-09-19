# OpsConductor AI System Documentation

## Overview

OpsConductor features a modern **AI microservices architecture** that provides intelligent automation capabilities through natural language processing, machine learning, and advanced analytics. The AI system transforms complex infrastructure operations into simple conversational interfaces while continuously learning and improving from user interactions.

## 🏗️ AI Architecture

### Current Production Architecture

The AI system is built using a distributed microservices architecture for optimal scalability, maintainability, and performance:

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│  AI Command     │◄──►│ AI Orchestrator │    │  Vector Service │    │   LLM Service   │
│   (Port 3005)   │    │   (Port 3010)   │    │   (Port 3007)   │    │   (Port 3008)   │
│                 │    │                 │    │                 │    │                 │
│ • Intent Class. │    │ • Coordination  │    │ • Knowledge     │    │ • Text Gen.     │
│ • Entity Extract│    │ • Routing       │    │ • Vector Search │    │ • Chat Interface│
│ • NLP Processing│    │ • Integration   │    │ • ChromaDB      │    │ • Ollama        │
│ • Job Creation  │    │ • Workflows     │    │ • Embeddings    │    │ • Multi-Models  │
└─────────────────┘    └─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │                       │
         └───────────────────────┼───────────────────────┼───────────────────────┘
                                 ▼                       ▼
                    ┌─────────────────┐    ┌─────────────────┐
                    │     Ollama      │    │    ChromaDB     │
                    │  (Port 11434)   │    │   (Port 8000)   │
                    │                 │    │                 │
                    │ • LLM Models    │    │ • Vector Store  │
                    │ • GPU Support   │    │ • Embeddings    │
                    │ • Local Serving │    │ • Semantic Search│
                    └─────────────────┘    └─────────────────┘
```

## 🧠 AI Services

### 1. AI Command Service (Port 3005)
**Main AI interface with integrated NLP and intent classification**

**Purpose**: Primary AI service that handles natural language processing, intent classification, and job creation

**Key Features**:
- Integrated natural language processing (nlp_processor.py)
- Intent classification and entity extraction
- Direct integration with all core services
- Machine learning and predictive analytics
- Workflow generation from natural language
- Learning engine with continuous improvement
- Schema introspection for dynamic queries

**Core Components**:
```
ai-command/
├── ai_engine.py                 # Main AI orchestrator (601 lines)
├── nlp_processor.py             # Natural language processing
├── learning_engine.py           # Machine learning engine
├── predictive_analytics.py      # Predictive analytics
├── vector_store.py              # Vector embeddings storage
├── workflow_generator.py        # Workflow generation
├── schema_introspector.py       # Database schema analysis
├── query_handlers/              # Modular query handlers
│   ├── automation_queries.py    # Automation-related queries
│   ├── infrastructure_queries.py # Infrastructure queries
│   ├── communication_queries.py # Communication queries
│   └── dynamic_schema_queries.py # Dynamic schema queries
├── asset_client.py              # Asset service integration
├── automation_client.py         # Automation service integration
└── communication_client.py      # Communication service integration
```

**Core Endpoints**:
```
POST /ai/chat              - Natural language chat interface
POST /ai/create-job        - Create automation jobs from natural language
POST /ai/analyze           - Analyze text and generate insights
GET  /ai/capabilities      - Get AI system capabilities
POST /ai/learn             - Store learning patterns
GET  /health               - Service health check
```

**Example Usage**:
```json
// Chat Request
{
  "message": "restart nginx on web servers",
  "user_id": 1,
  "context": {}
}

// Response
{
  "response": "I'll restart nginx on your web servers. Let me create a job for that.",
  "intent": "service_management",
  "confidence": 0.95,
  "actions": [
    {
      "type": "job_creation",
      "target_group": "web servers",
      "operation": "restart",
      "service": "nginx"
    }
  ]
}
```

### 2. AI Orchestrator Service (Port 3010)
**AI workflow coordination and management**

**Purpose**: Coordinates complex AI workflows and manages multi-service AI operations

**Key Features**:
- AI workflow coordination
- Multi-service AI request routing
- Response aggregation and formatting
- Protocol management for AI workflows
- Knowledge management integration

**Core Components**:
```
ai-orchestrator/
├── orchestrator.py              # Core orchestration logic
├── protocol_manager.py          # AI workflow protocols
├── workflow_generator.py        # Workflow generation
└── knowledge_manager.py         # Knowledge management
```

**Core Endpoints**:
```
POST /orchestrate          - Orchestrate complex AI workflows
POST /workflow/generate    - Generate workflows from requirements
GET  /protocols            - List available AI protocols
GET  /health               - Service health check
```

### 3. Vector Service (Port 3007)
**Knowledge Storage and Retrieval using ChromaDB**

**Purpose**: Store and retrieve AI knowledge using vector embeddings for semantic search

**Key Features**:
- ChromaDB integration for vector storage
- Knowledge storage (documentation, procedures, solutions)
- Semantic search and similarity matching
- Pattern storage and retrieval
- Learning from successful operations
- GPU-accelerated embeddings

**Core Endpoints**:
```
POST /vector/store         - Store knowledge documents
POST /vector/search        - Search knowledge base semantically
GET  /vector/stats         - Get vector database statistics
POST /vector/store-pattern - Store automation patterns
DELETE /vector/clear       - Clear vector database
GET  /health               - Service health check
```

**Example Usage**:
```json
// Store Knowledge
{
  "content": "To restart nginx service, use 'sudo systemctl restart nginx' on Linux systems",
  "category": "system_administration",
  "title": "Nginx Restart Procedure",
  "metadata": {
    "os_type": "linux",
    "service": "nginx",
    "operation": "restart"
  }
}

// Search Knowledge
{
  "query": "how to restart nginx",
  "limit": 3,
  "filter": {"os_type": "linux"}
}
```

### 4. LLM Service (Port 3008)
**Large Language Model Interface with Ollama**

**Purpose**: Text generation and reasoning using large language models

**Key Features**:
- Ollama integration for local LLM serving
- Multiple model support (Llama2, CodeLlama, Mistral, etc.)
- Context-aware text generation
- Summarization and analysis
- Code generation and explanation
- GPU acceleration support

**Core Endpoints**:
```
POST /llm/chat             - Chat with LLM
POST /llm/generate         - Generate text
POST /llm/summarize        - Summarize text
POST /llm/analyze          - Analyze text content
GET  /llm/models           - List available models
POST /llm/pull             - Pull new models
GET  /health               - Service health check
```

**Example Usage**:
```json
// Chat Request
{
  "message": "Explain how to troubleshoot network connectivity issues",
  "system_prompt": "You are OpsConductor AI, an IT operations assistant.",
  "model": "llama2:latest",
  "temperature": 0.7
}

// Response
{
  "response": "To troubleshoot network connectivity issues, follow these systematic steps:\n\n1. Check physical connections...",
  "model_used": "llama2:latest",
  "tokens_used": 245,
  "response_time": 2.3
}
```

## 🔄 Request Flow

### Natural Language Chat Request
```
User Input → API Gateway → AI Command Service → NLP Processor (parse intent)
                                             → Vector Store (search context)
                                             → LLM Service (generate response)
                                             → Learning Engine (store patterns)
                                             → Response to User
```

### Automation Job Creation
```
User Request → API Gateway → AI Command Service → Intent Classification
                                               → Asset Service (get targets)
                                               → Workflow Generator (create workflow)
                                               → Automation Service (execute job)
                                               → Communication Service (notify)
```

### Complex AI Workflow
```
User Request → API Gateway → AI Orchestrator → AI Command Service
                                           → Vector Service (knowledge)
                                           → LLM Service (reasoning)
                                           → Multiple Core Services
                                           → Aggregated Response
```

## 🚀 Deployment

### Docker Compose Configuration

The AI services are deployed as part of the main docker-compose.yml:

```yaml
# AI Infrastructure
chromadb:
  image: chromadb/chroma:0.6.1
  ports: ["8000:8000"]
  volumes: [chromadb_data:/chroma/chroma]

ollama:
  image: ollama/ollama:0.11.11
  ports: ["11434:11434"]
  volumes: [ollama_models:/root/.ollama]
  deploy:
    resources:
      reservations:
        devices:
          - driver: nvidia
            count: 1
            capabilities: [gpu]

# AI Services
ai-command:
  build: ./ai-command
  ports: ["3005:3005"]
  environment:
    CHROMADB_URL: http://chromadb:8000
    OLLAMA_HOST: http://ollama:11434
  depends_on: [chromadb, ollama]

vector-service:
  build: ./vector-service
  ports: ["3007:3000"]
  environment:
    CHROMADB_URL: http://chromadb:8000
  depends_on: [chromadb]

llm-service:
  build: ./llm-service
  ports: ["3008:3000"]
  environment:
    OLLAMA_HOST: http://ollama:11434
  depends_on: [ollama]

ai-orchestrator:
  build: ./ai-orchestrator
  ports: ["3010:3000"]
  depends_on: [vector-service, llm-service]
```

### GPU Acceleration

For enhanced AI performance, GPU acceleration is available:

```bash
# Deploy with GPU support
docker-compose -f docker-compose.yml -f docker-compose.gpu.yml up -d

# Verify GPU access
docker exec opsconductor-ai-command nvidia-smi
```

## 🧪 Testing

### AI System Testing

```bash
# Comprehensive AI system test
python test_ai_microservices.py

# Specific AI functionality tests
python test_ai_system_v2.py
python test_knowledge_storage.py
python test_tag_awareness.py
```

### Manual Testing

```bash
# Test AI chat interface
curl -X POST http://localhost:3005/ai/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "restart nginx on web servers", "user_id": 1}'

# Test vector search
curl -X POST http://localhost:3007/vector/search \
  -H "Content-Type: application/json" \
  -d '{"query": "nginx restart", "limit": 3}'

# Test LLM generation
curl -X POST http://localhost:3008/llm/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "Explain Docker containers", "model": "llama2:latest"}'
```

## 📊 AI Performance Metrics

### Response Times
- **Intent Classification**: < 500ms
- **Vector Search**: < 1 second
- **LLM Generation**: 2-5 seconds (depending on model and length)
- **End-to-End Chat**: < 10 seconds

### Accuracy Metrics
- **Intent Classification**: 95%+ accuracy
- **Entity Extraction**: 90%+ accuracy
- **Job Creation Success**: 85%+ success rate
- **User Satisfaction**: Based on feedback learning

### Resource Usage
- **CPU**: 2-4 cores per AI service
- **Memory**: 4-8GB per AI service
- **GPU**: Optional, significantly improves performance
- **Storage**: 10-50GB for models and knowledge base

## 🔧 Configuration

### Environment Variables

```bash
# AI Command Service
CHROMADB_URL=http://chromadb:8000
OLLAMA_HOST=http://ollama:11434
ASSET_SERVICE_URL=http://asset-service:3002
AUTOMATION_SERVICE_URL=http://automation-service:3003

# Vector Service
CHROMADB_URL=http://chromadb:8000
CUDA_VISIBLE_DEVICES=all

# LLM Service
OLLAMA_HOST=http://ollama:11434
DEFAULT_LLM_MODEL=llama2:latest
CUDA_VISIBLE_DEVICES=all

# AI Orchestrator
VECTOR_SERVICE_URL=http://vector-service:3000
LLM_SERVICE_URL=http://llm-service:3000
```

### Model Management

```bash
# Pull new models
curl -X POST http://localhost:3008/llm/pull \
  -H "Content-Type: application/json" \
  -d '{"model": "codellama:latest"}'

# List available models
curl http://localhost:3008/llm/models

# Set default model
export DEFAULT_LLM_MODEL=codellama:latest
```

## 🔮 AI Roadmap

### Current Capabilities (Production Ready)
- ✅ Natural language intent classification
- ✅ Entity extraction and command parsing
- ✅ Vector-based knowledge storage and retrieval
- ✅ Local LLM serving with GPU acceleration
- ✅ Automated job creation from natural language
- ✅ Learning engine with pattern storage
- ✅ Multi-service AI workflow orchestration

### Planned Enhancements
- **Multi-Model Support**: Support for multiple LLM providers (OpenAI, Anthropic, etc.)
- **Advanced RAG**: Retrieval-Augmented Generation with improved context
- **Fine-Tuning**: Custom model fine-tuning for IT operations
- **Voice Interface**: Speech-to-text and text-to-speech capabilities
- **Predictive Analytics**: Advanced anomaly detection and forecasting
- **Auto-Documentation**: Automatic procedure documentation generation

### Research Areas
- **Federated Learning**: Distributed learning across multiple deployments
- **Explainable AI**: Better transparency in AI decision-making
- **Multi-Agent Systems**: Collaborative AI agents for complex tasks
- **Edge AI**: Lightweight AI models for edge deployments

---

**The OpsConductor AI system represents a production-ready implementation of intelligent IT operations automation, combining the power of modern LLMs with practical infrastructure management needs.**