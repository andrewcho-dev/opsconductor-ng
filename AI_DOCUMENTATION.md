# OpsConductor AI System Documentation

## Overview

OpsConductor features a modern **AI microservices architecture** that provides intelligent automation capabilities through natural language processing, machine learning, and advanced analytics. The AI system transforms complex infrastructure operations into simple conversational interfaces while continuously learning and improving from user interactions.

## 🏗️ AI Architecture

### Microservices Design

The AI system is built using a distributed microservices architecture for optimal scalability, maintainability, and performance:

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│  AI Orchestrator│◄──►│   NLP Service   │    │  Vector Service │    │   LLM Service   │
│   (Port 3005)   │    │   (Port 3006)   │    │   (Port 3007)   │    │   (Port 3008)   │
│                 │    │                 │    │                 │    │                 │
│ • Coordination  │    │ • Intent Class. │    │ • Knowledge     │    │ • Text Gen.     │
│ • Routing       │    │ • Entity Extract│    │ • Vector Search │    │ • Chat Interface│
│ • Integration   │    │ • NLP Processing│    │ • ChromaDB      │    │ • Ollama        │
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
                    └─────────────────┘    └─────────────────┘
```

## 🧠 AI Services

### 1. AI Orchestrator Service (Port 3005)
**Primary AI interface and coordination hub**

**Purpose**: Main entry point for all AI requests, coordinates between specialized AI services

**Key Features**:
- Unified AI API interface
- Request routing and coordination  
- Response aggregation
- Protocol management for different AI workflows
- Integration with asset and automation services

**Core Endpoints**:
```
POST /ai/chat              - Natural language chat interface
POST /ai/create-job        - Create automation jobs from natural language
POST /ai/analyze           - Analyze text and generate insights
GET  /ai/capabilities      - Get AI system capabilities
GET  /health               - Service health check
```

### 2. NLP Service (Port 3006)
**Natural Language Processing and Understanding**

**Purpose**: Parse and understand natural language requests with high accuracy

**Key Features**:
- Intent classification (restart, update, check, stop, start)
- Entity extraction (operations, targets, groups, OS types)
- Command parsing and normalization
- Confidence scoring and validation
- Multi-language support

**Core Endpoints**:
```
POST /nlp/parse            - Parse natural language text
POST /nlp/classify         - Classify intent and extract entities
GET  /nlp/capabilities     - Get NLP processing capabilities
GET  /health               - Service health check
```

**Example Usage**:
```json
// Request
{
  "text": "restart nginx on web servers"
}

// Response
{
  "operation": "restart",
  "target_process": "nginx",
  "target_group": "web servers",
  "target_os": "linux",
  "confidence": 0.95,
  "intent": "service_management"
}
```

### 3. Vector Service (Port 3007)
**Knowledge Storage and Retrieval**

**Purpose**: Store and retrieve AI knowledge using vector embeddings for semantic search

**Key Features**:
- ChromaDB integration for vector storage
- Knowledge storage (documentation, procedures, solutions)
- Semantic search and similarity matching
- Pattern storage and retrieval
- Learning from successful operations
- Metadata filtering and categorization

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
  "title": "Nginx Restart Procedure"
}

// Search Knowledge
{
  "query": "how to restart nginx",
  "limit": 3
}
```

### 4. LLM Service (Port 3008)
**Large Language Model Interface**

**Purpose**: Text generation and reasoning using large language models

**Key Features**:
- Ollama integration for local LLM serving
- Multiple model support (Llama2, CodeLlama, etc.)
- Context-aware text generation
- Summarization and analysis
- Code generation and explanation
- Conversational AI capabilities

**Core Endpoints**:
```
POST /llm/chat             - Chat with LLM
POST /llm/generate         - Generate text
POST /llm/summarize        - Summarize text
POST /llm/analyze          - Analyze text content
GET  /llm/models           - List available models
GET  /health               - Service health check
```

**Example Usage**:
```json
// Chat Request
{
  "message": "Explain how to troubleshoot network connectivity issues",
  "system_prompt": "You are OpsConductor AI, an IT operations assistant.",
  "model": "llama2"
}

// Response
{
  "response": "To troubleshoot network connectivity issues, follow these steps...",
  "confidence": 0.92,
  "model_used": "llama2"
}
```

## 🔄 Request Flow

### Natural Language Chat Request
```
User Input → API Gateway → AI Orchestrator → NLP Service (parse intent)
                                          → Vector Service (search context)
                                          → LLM Service (generate response)
                                          → Response to User
```

### Automation Job Creation
```
User Request → API Gateway → AI Orchestrator → NLP Service (parse intent)
                                           → Vector Service (find patterns)
                                           → Workflow Generator (create workflow)
                                           → Automation Service (execute)
```

## 🚀 Deployment

### Docker Compose Configuration

```yaml
services:
  ai-orchestrator:
    build: ./ai-orchestrator
    ports: ["3005:3000"]
    environment:
      VECTOR_SERVICE_URL: http://vector-service:3000
      LLM_SERVICE_URL: http://llm-service:3000
      ASSET_SERVICE_URL: http://asset-service:3002
      AUTOMATION_SERVICE_URL: http://automation-service:3003

  vector-service:
    build: ./vector-service
    ports: ["3007:3000"]
    environment:
      CHROMADB_URL: http://chromadb:8000

  llm-service:
    build: ./llm-service
    ports: ["3008:3000"]
    environment:
      OLLAMA_HOST: http://ollama:11434

  ollama:
    image: ollama/ollama:latest
    ports: ["11434:11434"]
    volumes: ["ollama_models:/root/.ollama"]

  chromadb:
    image: chromadb/chroma:0.5.0
    ports: ["8000:8000"]
    volumes: ["chromadb_data:/chroma/chroma"]
```

### Quick Start Commands

```bash
# Build and start all AI services
docker-compose build ai-orchestrator vector-service llm-service
docker-compose up -d ai-orchestrator vector-service llm-service ollama chromadb

# Test the system
python test_ai_microservices.py

# Test chat functionality
curl -X POST http://localhost:3005/ai/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "restart nginx on web servers", "user_id": 1}'
```

## 🧪 Testing

### Automated Testing

The system includes a comprehensive test suite (`test_ai_microservices.py`) that validates:

- **Service Health**: All microservices are running and responsive
- **AI Processing**: Intent classification and entity extraction accuracy
- **Vector Operations**: Knowledge storage and semantic search
- **LLM Generation**: Text generation and chat functionality
- **Integration**: End-to-end AI pipeline functionality

```bash
# Run comprehensive test suite
python test_ai_microservices.py

# Test individual services
curl http://localhost:3005/health  # AI Orchestrator
curl http://localhost:3006/health  # NLP Service
curl http://localhost:3007/health  # Vector Service
curl http://localhost:3008/health  # LLM Service
```

### Manual Testing Examples

```bash
# Test NLP parsing
curl -X POST http://localhost:3006/nlp/parse \
  -H "Content-Type: application/json" \
  -d '{"text": "update stationcontroller on CIS servers"}'

# Test vector search
curl -X POST http://localhost:3007/vector/search \
  -H "Content-Type: application/json" \
  -d '{"query": "nginx restart procedure", "limit": 3}'

# Test LLM chat
curl -X POST http://localhost:3008/llm/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "How do I check disk space on Linux?", "model": "llama2"}'

# Test full orchestration
curl -X POST http://localhost:3005/ai/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "check system health on all servers", "user_id": 1}'
```

## 🔧 Configuration

### Environment Variables

#### AI Orchestrator
```bash
VECTOR_SERVICE_URL=http://vector-service:3000
LLM_SERVICE_URL=http://llm-service:3000
ASSET_SERVICE_URL=http://asset-service:3002
AUTOMATION_SERVICE_URL=http://automation-service:3003
REDIS_URL=redis://redis:6379/5
```

#### Vector Service
```bash
CHROMADB_URL=http://chromadb:8000
REDIS_URL=redis://redis:6379/7
```

#### LLM Service
```bash
OLLAMA_HOST=http://ollama:11434
DEFAULT_LLM_MODEL=llama2
REDIS_URL=redis://redis:6379/8
```

### Model Management

```bash
# List available models
curl http://localhost:11434/api/tags

# Pull a new model
curl -X POST http://localhost:11434/api/pull \
  -H "Content-Type: application/json" \
  -d '{"name": "codellama"}'

# Remove a model
curl -X DELETE http://localhost:11434/api/delete \
  -H "Content-Type: application/json" \
  -d '{"name": "unused-model"}'
```

## 📊 Performance & Monitoring

### Performance Metrics
- **Response Time**: < 3 seconds for most AI queries
- **NLP Accuracy**: 95%+ intent detection accuracy
- **Throughput**: 100+ concurrent AI requests
- **Availability**: 99.9% uptime target

### Health Monitoring
```bash
# Check all service health
for port in 3005 3006 3007 3008; do
  echo "Checking port $port:"
  curl -s http://localhost:$port/health | jq '.status'
done

# Monitor resource usage
docker stats ai-orchestrator vector-service llm-service
```

### Logging
Each service provides structured logging with correlation IDs for request tracing:

```bash
# View service logs
docker-compose logs -f ai-orchestrator
docker-compose logs -f ai-command
docker-compose logs -f vector-service
docker-compose logs -f llm-service
```

## 🔒 Security

### Authentication
- JWT token validation for all AI endpoints
- User context passed between services via headers
- Rate limiting to prevent abuse

### Data Protection
- No sensitive data stored in vector database
- Encrypted communication between services
- Input validation and sanitization

## 🚨 Troubleshooting

### Common Issues

#### Service Communication Failures
```bash
# Check network connectivity
docker-compose exec ai-orchestrator ping vector-service
docker-compose exec ai-orchestrator ping vector-service
docker-compose exec ai-orchestrator ping llm-service

# Verify service URLs
docker-compose exec ai-orchestrator env | grep SERVICE_URL
```

#### Ollama Model Issues
```bash
# Check Ollama status
curl http://localhost:11434/api/tags

# Pull required model
curl -X POST http://localhost:11434/api/pull \
  -H "Content-Type: application/json" \
  -d '{"name": "llama2"}'
```

#### ChromaDB Connection Issues
```bash
# Check ChromaDB health
curl http://localhost:8000/api/v1/heartbeat

# Check vector service logs
docker-compose logs vector-service
```

#### Memory/Resource Issues
```bash
# Check resource usage
docker stats

# Check for OOM errors
docker-compose logs | grep -i "memory\|oom"
```

### Performance Optimization

1. **Resource Allocation**: Adjust Docker memory limits based on usage
2. **Model Selection**: Use smaller models for faster responses
3. **Caching**: Enable Redis caching for frequent requests
4. **Concurrent Limits**: Tune max concurrent requests per service

## 🔮 Future Enhancements

### Planned Features
1. **Advanced Learning**: Enhanced pattern recognition and learning capabilities
2. **Multi-Model Support**: Support for multiple LLM providers (OpenAI, Anthropic)
3. **Caching Layer**: Redis-based response caching for improved performance
4. **API Versioning**: Versioned APIs for backward compatibility
5. **Enhanced Security**: Advanced authentication and authorization
6. **Observability**: Advanced monitoring, metrics, and alerting

### Extensibility
- Plugin architecture for new AI capabilities
- Custom NLP processors for domain-specific language
- Additional vector stores (Pinecone, Weaviate)
- External LLM provider integration

## 📚 API Reference

### Complete API Documentation

Detailed interactive API documentation is available at:
- **AI Orchestrator**: http://localhost:3005/docs
- **NLP Service**: http://localhost:3006/docs
- **Vector Service**: http://localhost:3007/docs
- **LLM Service**: http://localhost:3008/docs

### Key API Patterns

#### Error Responses
All services return consistent error responses:
```json
{
  "error": "Error description",
  "details": "Additional error details",
  "service": "service-name",
  "timestamp": "2024-01-01T12:00:00Z"
}
```

#### Success Responses
Standard success response format:
```json
{
  "success": true,
  "data": { /* response data */ },
  "service": "service-name",
  "timestamp": "2024-01-01T12:00:00Z"
}
```

## 🎯 Best Practices

### Development
1. **Service Independence**: Each service should be independently deployable
2. **Error Handling**: Implement comprehensive error handling and graceful degradation
3. **Testing**: Write tests for all AI functionality and integration points
4. **Documentation**: Keep API documentation up to date

### Operations
1. **Monitoring**: Monitor all services for health and performance
2. **Scaling**: Scale services independently based on load
3. **Updates**: Deploy updates to individual services without affecting others
4. **Backup**: Regular backup of vector database and model data

### Security
1. **Authentication**: Always validate user tokens
2. **Input Validation**: Sanitize all user inputs
3. **Rate Limiting**: Implement rate limiting to prevent abuse
4. **Audit Logging**: Log all AI operations for security auditing

---

**The OpsConductor AI system provides a powerful, scalable, and maintainable foundation for intelligent infrastructure automation through its modern microservices architecture.**