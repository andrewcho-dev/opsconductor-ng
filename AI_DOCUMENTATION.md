# OpsConductor AI System Documentation

## Overview

OpsConductor features a modern **AI Brain architecture** that provides intelligent automation capabilities through natural language processing, machine learning, and advanced analytics. The AI system transforms complex infrastructure operations into simple conversational interfaces while continuously learning and improving from user interactions.

## 🏗️ AI Architecture

### Current Production Architecture

The AI system is built using a unified AI Brain service that integrates with external AI infrastructure for optimal performance:

```
┌─────────────────────────────────────────────────────────────────┐
│                        AI Brain Service                         │
│                        (Port 3005)                              │
│                                                                 │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐ │
│  │  Intent Engine  │  │ Knowledge Engine│  │   Job Engine    │ │
│  │                 │  │                 │  │                 │ │
│  │ • Classification│  │ • IT Knowledge  │  │ • Job Creation  │ │
│  │ • Entity Extract│  │ • Error Resolut.│  │ • Validation    │ │
│  │ • Context Aware │  │ • Learning Sys. │  │ • Optimization  │ │
│  └─────────────────┘  └─────────────────┘  └─────────────────┘ │
│                                                                 │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐ │
│  │ System Model    │  │  Integrations   │  │ Brain Engine    │ │
│  │                 │  │                 │  │                 │ │
│  │ • Asset Mapping │  │ • Asset Client  │  │ • Orchestration │ │
│  │ • Protocols     │  │ • Automation    │  │ • Conversation  │ │
│  │ • Capabilities  │  │ • Communication │  │ • LLM Handler   │ │
│  └─────────────────┘  └─────────────────┘  └─────────────────┘ │
└─────────────────────────────────────────────────────────────────┘
                                 │
                                 ▼
                    ┌─────────────────┐
                    │     Ollama      │
                    │  (Port 11434)   │
                    │                 │
                    │ • LLM Models    │
                    │ • GPU Support   │
                    │ • Local Serving │
                    └─────────────────┘
```

## 🧠 AI Brain Service (Port 3005)

**Unified AI service with modular engine architecture**

**Purpose**: Single AI service that handles all natural language processing, intent classification, job creation, and system intelligence through specialized engines.

**Key Features**:
- Modular engine architecture for specialized AI tasks
- Advanced intent classification and entity extraction
- Integrated knowledge base with IT expertise
- Intelligent job creation and workflow generation
- System model awareness for infrastructure operations
- Continuous learning and improvement capabilities
- Direct integration with all core services

**Core Architecture**:
```
ai-brain/
├── brain_engine.py              # Main AI orchestrator and coordinator
├── llm_conversation_handler.py  # LLM conversation management
├── main.py                      # FastAPI service entry point
├── intent_engine/               # Intent classification and processing
│   ├── intent_classifier.py     # ML-based intent classification
│   ├── entity_extractor.py      # Named entity recognition
│   └── context_manager.py       # Conversation context management
├── knowledge_engine/            # AI knowledge and learning systems
│   ├── it_knowledge_base.py     # IT operations knowledge
│   ├── error_resolution.py      # Error diagnosis and solutions
│   ├── learning_system.py       # Continuous learning engine
│   └── solution_patterns.py     # Common solution patterns
├── job_engine/                  # Intelligent job creation
│   ├── llm_job_creator.py       # LLM-powered job generation
│   ├── workflow_generator.py    # Workflow creation from NL
│   ├── job_validator.py         # Job validation and safety
│   ├── execution_planner.py     # Execution planning
│   ├── step_optimizer.py        # Step optimization
│   └── target_resolver.py       # Target resolution
├── system_model/                # System understanding and mapping
│   ├── asset_mapper.py          # Asset relationship mapping
│   ├── protocol_knowledge.py    # Protocol and service knowledge
│   ├── service_capabilities.py  # Service capability mapping
│   └── workflow_templates.py    # Workflow templates
├── integrations/                # External service integrations
│   ├── asset_client.py          # Asset service integration
│   ├── automation_client.py     # Automation service integration
│   ├── communication_client.py  # Communication service integration
│   ├── llm_client.py           # Ollama LLM integration
│   └── vector_client.py        # Vector database integration
└── legacy/                     # Legacy compatibility layer
    └── [legacy components for backward compatibility]
```

**Core Endpoints**:
```
POST /ai/chat              - Natural language chat interface
POST /ai/create-job        - Create automation jobs from natural language
POST /ai/analyze           - Analyze text and generate insights
GET  /ai/capabilities      - Get AI system capabilities
POST /ai/learn             - Store learning patterns
GET  /health               - Service health check
POST /ai/intent            - Intent classification endpoint
GET  /ai/knowledge         - Knowledge base queries
```

**Engine Responsibilities**:

**Intent Engine**:
- Classifies user intents from natural language
- Extracts entities and parameters
- Manages conversation context and state
- Handles multi-turn conversations

**Knowledge Engine**:
- Maintains IT operations knowledge base
- Provides error resolution guidance
- Learns from successful operations
- Stores and retrieves solution patterns

**Job Engine**:
- Creates automation jobs from natural language
- Generates complex workflows
- Validates job safety and feasibility
- Optimizes execution plans
- Resolves target systems and dependencies

**System Model**:
- Maps infrastructure assets and relationships
- Understands service capabilities and protocols
- Provides workflow templates
- Maintains system topology awareness

## 🔧 External AI Infrastructure

### Ollama (Port 11434)
**Local LLM serving infrastructure**

**Purpose**: Provides local large language model serving with GPU acceleration support

**Key Features**:
- Multiple model support (Llama2, CodeLlama, etc.)
- GPU acceleration for enhanced performance
- Local deployment for data privacy
- REST API for model interactions
- Model management and switching

**Supported Models**:
- `llama2:latest` - General purpose conversational AI
- `codellama:latest` - Code generation and analysis
- `mistral:latest` - Efficient general purpose model
- Custom fine-tuned models for specific tasks

**Configuration**:
```bash
# Pull models
docker exec opsconductor-ollama ollama pull llama2:latest
docker exec opsconductor-ollama ollama pull codellama:latest

# List available models
curl http://localhost:11434/api/tags

# Test model interaction
curl http://localhost:11434/api/generate -d '{
  "model": "llama2",
  "prompt": "Explain Docker containers",
  "stream": false
}'
```

## 🚀 Deployment Configuration

### Standard Deployment
```yaml
ai-brain:
  build: ./ai-brain
  ports:
    - "3005:3005"
  environment:
    - OLLAMA_URL=http://ollama:11434
    - REDIS_URL=redis://redis:6379
    - POSTGRES_URL=postgresql://postgres:password@postgres:5432/opsconductor
  depends_on: [ollama, redis, postgres]
  volumes:
    - ./shared:/app/shared

ollama:
  image: ollama/ollama:latest
  ports:
    - "11434:11434"
  volumes:
    - ollama_data:/root/.ollama
```

### GPU-Accelerated Deployment
```yaml
ai-brain:
  build: ./ai-brain
  ports:
    - "3005:3005"
  environment:
    - OLLAMA_URL=http://ollama:11434
    - CUDA_VISIBLE_DEVICES=0
  deploy:
    resources:
      reservations:
        devices:
          - driver: nvidia
            count: 1
            capabilities: [gpu]

ollama:
  image: ollama/ollama:latest
  ports:
    - "11434:11434"
  deploy:
    resources:
      reservations:
        devices:
          - driver: nvidia
            count: 1
            capabilities: [gpu]
```

## 🔍 AI System Monitoring

### Health Checks
```bash
# AI Brain service health
curl http://localhost:3005/health

# Ollama service health
curl http://localhost:11434/api/tags

# Test AI functionality
curl -X POST http://localhost:3005/ai/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "show me all servers", "user_id": "test"}'
```

### Performance Monitoring
```bash
# Check GPU utilization (if using GPU)
docker exec opsconductor-ai-brain nvidia-smi

# Monitor AI Brain logs
docker logs opsconductor-ai-brain -f

# Monitor Ollama logs
docker logs opsconductor-ollama -f
```

## 🎯 AI Capabilities

### Natural Language Processing
- **Intent Classification**: Automatically classifies user intents from natural language
- **Entity Extraction**: Identifies and extracts relevant entities (servers, services, etc.)
- **Context Management**: Maintains conversation context across multiple interactions
- **Multi-turn Conversations**: Supports complex, multi-step conversations

### Infrastructure Intelligence
- **Asset Awareness**: Understands infrastructure topology and relationships
- **Protocol Knowledge**: Knows how to interact with different systems and protocols
- **Service Capabilities**: Understands what each service can do and how to use it
- **Workflow Generation**: Creates complex automation workflows from simple requests

### Learning and Adaptation
- **Continuous Learning**: Learns from successful operations and user feedback
- **Error Resolution**: Provides intelligent error diagnosis and resolution suggestions
- **Pattern Recognition**: Identifies common patterns and optimizes responses
- **Solution Storage**: Stores and retrieves proven solution patterns

### Job Creation Intelligence
- **Natural Language to Jobs**: Converts natural language requests into executable jobs
- **Safety Validation**: Validates job safety and prevents destructive operations
- **Execution Planning**: Creates optimal execution plans for complex operations
- **Target Resolution**: Intelligently resolves target systems and dependencies

## 🔧 Configuration

### Environment Variables
```bash
# AI Brain Configuration
OLLAMA_URL=http://ollama:11434
REDIS_URL=redis://redis:6379
POSTGRES_URL=postgresql://postgres:password@postgres:5432/opsconductor

# AI Model Configuration
DEFAULT_MODEL=llama2:latest
EMBEDDING_MODEL=all-MiniLM-L6-v2
MAX_CONTEXT_LENGTH=4096

# Learning Configuration
ENABLE_LEARNING=true
LEARNING_RATE=0.001
CONFIDENCE_THRESHOLD=0.8

# Performance Configuration
MAX_CONCURRENT_REQUESTS=10
REQUEST_TIMEOUT=30
CACHE_TTL=3600
```

### Model Configuration
```python
# Configure available models
AVAILABLE_MODELS = {
    "llama2": {
        "name": "llama2:latest",
        "type": "general",
        "context_length": 4096
    },
    "codellama": {
        "name": "codellama:latest", 
        "type": "code",
        "context_length": 16384
    }
}
```

## 🚨 Troubleshooting

### Common Issues

#### AI Brain Not Responding
```bash
# Check service status
docker ps | grep ai-brain

# Check logs
docker logs opsconductor-ai-brain

# Restart service
docker-compose restart ai-brain
```

#### Ollama Connection Issues
```bash
# Check Ollama status
curl http://localhost:11434/api/tags

# Check if models are loaded
docker exec opsconductor-ollama ollama list

# Restart Ollama
docker-compose restart ollama
```

#### Performance Issues
```bash
# Check resource usage
docker stats opsconductor-ai-brain opsconductor-ollama

# Check GPU usage (if applicable)
docker exec opsconductor-ai-brain nvidia-smi

# Monitor memory usage
docker exec opsconductor-ai-brain free -h
```

### Performance Optimization

#### GPU Acceleration
- Ensure NVIDIA Docker runtime is installed
- Configure GPU access in docker-compose.gpu.yml
- Monitor GPU utilization and memory usage
- Use appropriate model sizes for available GPU memory

#### Memory Management
- Configure appropriate memory limits for containers
- Monitor memory usage during peak loads
- Use model quantization for memory-constrained environments
- Implement request queuing for high-load scenarios

#### Response Time Optimization
- Use model caching for frequently accessed models
- Implement response caching for common queries
- Configure appropriate timeout values
- Use streaming responses for long-running operations

## 📊 Metrics and Analytics

### AI Performance Metrics
- **Response Time**: Average time to process AI requests
- **Intent Accuracy**: Accuracy of intent classification
- **Job Success Rate**: Success rate of generated automation jobs
- **Learning Effectiveness**: Improvement in responses over time

### System Metrics
- **Request Volume**: Number of AI requests per time period
- **Model Usage**: Usage statistics for different AI models
- **Resource Utilization**: CPU, memory, and GPU usage
- **Error Rates**: Error rates for different AI operations

### Monitoring Dashboard
The AI system provides comprehensive monitoring through the OpsConductor dashboard:
- Real-time AI performance metrics
- Model usage statistics
- Learning progress indicators
- System health status
- Resource utilization graphs

## 🔮 Future Enhancements

### Planned Features
- **Multi-modal AI**: Support for image and document analysis
- **Advanced RAG**: Retrieval-Augmented Generation for enhanced knowledge
- **Custom Model Training**: Fine-tuning models on organization-specific data
- **Federated Learning**: Distributed learning across multiple deployments
- **Advanced Analytics**: Predictive analytics and anomaly detection

### Integration Roadmap
- **External AI Services**: Integration with cloud AI services
- **Knowledge Graphs**: Advanced knowledge representation
- **Workflow Optimization**: AI-powered workflow optimization
- **Automated Documentation**: AI-generated documentation and runbooks