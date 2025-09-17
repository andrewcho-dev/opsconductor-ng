# OpsConductor AI System V2 Architecture

## Overview
The OpsConductor AI System V2 implements a comprehensive, microservices-based AI architecture with intelligent routing, centralized learning, and real-time monitoring capabilities. This document describes the complete architecture, components, and implementation details.

## Architecture Components

### 1. API Gateway with AI Router (`api-gateway/main.py`, `api-gateway/ai_router.py`)

The enhanced API Gateway now includes intelligent AI routing capabilities:

#### Features:
- **Unified AI Endpoint** (`/api/v1/ai/chat`): Single entry point for all AI requests
- **Intelligent Routing**: Routes requests to appropriate AI services based on query intent
- **Circuit Breakers**: Protects services from cascading failures
- **Load Balancing**: Multiple strategies (round-robin, least-response-time, weighted-random)
- **Response Caching**: Reduces load with intelligent caching
- **Monitoring Integration**: Real-time metrics and health checks

#### Endpoints:
```
POST /api/v1/ai/chat              - Unified AI chat interface
GET  /api/v1/ai/health            - AI services health status
POST /api/v1/ai/feedback          - Submit feedback for interactions
GET  /api/v1/ai/monitoring/dashboard     - Monitoring dashboard data
GET  /api/v1/ai/monitoring/service/{name} - Individual service metrics
POST /api/v1/ai/monitoring/health-check  - Manual health check (admin)
POST /api/v1/ai/circuit-breaker/reset/{service} - Reset circuit breaker (admin)
```

### 2. Centralized Vector Store Client (`shared/vector_client.py`)

Unified interface for all services to interact with the vector database:

#### Key Classes:
- **VectorStoreClient**: Low-level vector database operations
- **KnowledgeManager**: High-level knowledge management

#### Collections:
- `SYSTEM_KNOWLEDGE`: Core system documentation
- `AUTOMATION_PATTERNS`: Successful automation patterns
- `TROUBLESHOOTING`: Issue solutions
- `USER_INTERACTIONS`: User query history
- `SYSTEM_STATE`: Current system state
- `IT_KNOWLEDGE`: IT domain knowledge
- `PROTOCOL_KNOWLEDGE`: Protocol specifications

#### Features:
- Batch operations for efficiency
- Similarity search with configurable thresholds
- Collection statistics and management
- Automatic metadata handling

### 3. Learning Engine (`shared/learning_engine.py`)

Implements continuous learning and improvement:

#### Components:

##### LearningMetrics
- Tracks success rates, response times, confidence scores
- Maintains rolling averages
- Persists metrics to Redis
- Generates performance reports

##### PatternLearner
- Learns from successful interactions
- Groups similar queries
- Creates optimized patterns
- Stores patterns in vector database

##### FeedbackProcessor
- Processes user feedback and corrections
- Queues feedback for asynchronous processing
- Learns from user corrections
- Updates knowledge base

##### LearningOrchestrator
- Coordinates all learning components
- Records interactions with full context
- Triggers pattern consolidation
- Provides learning insights

### 4. AI Monitoring Dashboard (`shared/ai_monitoring.py`)

Real-time monitoring and analytics for AI services:

#### Components:

##### MetricsCollector
- Collects metrics from all AI services
- Maintains time-series data
- Stores metrics in Redis
- Tracks service availability

##### PerformanceAnalyzer
- Analyzes service performance
- Generates health scores
- Creates alerts for issues
- Provides recommendations

##### AIMonitoringDashboard
- Continuous monitoring with configurable intervals
- Dashboard data aggregation
- Service-specific details
- Manual health checks

### 5. Common AI Utilities (`shared/ai_common.py`)

Shared utilities for all AI services:

#### Features:
- **Intent Classification**: Standardized intent detection
- **Entity Extraction**: Extract targets, jobs, dates, IPs, etc.
- **Input Sanitization**: Prevent injection attacks
- **Response Formatting**: Standardized API responses
- **Context Management**: Maintain conversation context
- **Time Parsing**: Natural language time expressions
- **Confidence Scoring**: Calculate weighted confidence
- **Text Chunking**: Split text for processing
- **Response Builder**: Generate natural language responses

## System Flow

### 1. Request Processing Flow
```
User Request → API Gateway → AI Router → Service Selection → 
Target Service → Response Processing → Learning System → 
Cache Update → User Response
```

### 2. Learning Flow
```
Interaction → Record Metrics → Pattern Detection → 
Knowledge Update → Vector Store → Feedback Processing → 
Pattern Consolidation → Improved Responses
```

### 3. Monitoring Flow
```
Service Health Checks → Metrics Collection → 
Performance Analysis → Alert Generation → 
Dashboard Update → Recommendations
```

## Integration Points

### With Existing Services

1. **Identity Service**: User authentication and RBAC
2. **Asset Service**: Infrastructure management
3. **Automation Service**: Job execution and workflows
4. **Communication Service**: Notifications and alerts
5. **Vector Service**: Centralized vector storage
6. **Redis**: Session management and caching
7. **PostgreSQL**: Persistent data storage

### New AI Services

1. **AI Command** (`ai-command`): Main AI processing engine
2. **AI Orchestrator** (`ai-orchestrator`): Workflow generation
3. **NLP Service** (`nlp-service`): Natural language processing
4. **LLM Service** (`llm-service`): Large language model interface
5. **Vector Service** (`vector-service`): Vector database management

## Configuration

### Environment Variables
```bash
# AI Service URLs
AI_COMMAND_URL=http://ai-command:3005
AI_ORCHESTRATOR_URL=http://ai-orchestrator:3000
NLP_SERVICE_URL=http://nlp-service:3000
VECTOR_SERVICE_URL=http://vector-service:3000
LLM_SERVICE_URL=http://llm-service:3000

# Redis Configuration
REDIS_URL=redis://redis:6379/0

# Monitoring Configuration
AI_MONITORING_INTERVAL=30  # seconds
AI_CACHE_TTL=300           # seconds
```

### Circuit Breaker Settings
```python
failure_threshold = 5      # Failures before opening
timeout = 60.0            # Seconds before retry
half_open_requests = 3    # Test requests in half-open state
```

## Testing

### Test Suite (`test_ai_system_v2.py`)

Comprehensive test suite covering:
1. Unified AI chat functionality
2. Health check system
3. Monitoring dashboard
4. Feedback submission
5. Service monitoring
6. Circuit breaker functionality
7. Stress testing

Run tests:
```bash
python test_ai_system_v2.py
```

## Performance Considerations

### Caching Strategy
- 5-minute TTL for successful responses
- Cache key based on query, user, and context
- Redis-backed for persistence
- Cache hit tracking for metrics

### Load Balancing
- Multiple strategies available
- Health-aware routing
- Circuit breaker protection
- Automatic failover

### Resource Management
- Connection pooling for HTTP clients
- Async/await for non-blocking operations
- Background task management
- Graceful shutdown handling

## Security Features

1. **Input Sanitization**: Prevents injection attacks
2. **Authentication**: JWT-based with user context
3. **RBAC Integration**: Role-based access control
4. **Rate Limiting**: Prevents abuse
5. **Audit Logging**: Tracks all interactions

## Monitoring & Observability

### Metrics Tracked
- Request count and success rate
- Response times (min, max, average)
- Cache hit rates
- Circuit breaker states
- Service availability
- Error rates and types

### Alerts
- Service unavailability
- High error rates
- Slow response times
- Circuit breaker activations

### Dashboard Features
- Real-time service status
- Historical metrics (24 hours)
- Performance analysis
- Recommendations for improvement

## Future Enhancements

### Planned Features
1. **Multi-model Support**: Integration with multiple LLM providers
2. **A/B Testing**: Test different AI models/prompts
3. **Custom Training**: Fine-tuning on organization data
4. **Workflow Templates**: Pre-built automation patterns
5. **Predictive Analytics**: Proactive issue detection
6. **Natural Language Scheduling**: Schedule jobs via chat
7. **Multi-language Support**: Internationalization
8. **Voice Interface**: Speech-to-text integration

### Scalability Improvements
1. **Horizontal Scaling**: Add more service instances
2. **GPU Support**: For model inference
3. **Distributed Caching**: Redis cluster
4. **Message Queuing**: For async processing
5. **Event Streaming**: Real-time updates

## Deployment

### Docker Compose Integration
```yaml
# Add to docker-compose.yml
ai-router:
  build: ./api-gateway
  environment:
    - AI_ROUTER_ENABLED=true
    - AI_MONITORING_ENABLED=true
  depends_on:
    - redis
    - ai-command
    - vector-service
```

### Health Checks
```yaml
healthcheck:
  test: ["CMD", "curl", "-f", "http://localhost:3000/api/v1/ai/health"]
  interval: 30s
  timeout: 10s
  retries: 3
```

## Troubleshooting

### Common Issues

1. **Service Unavailable**
   - Check service health: `GET /api/v1/ai/health`
   - Review circuit breaker state
   - Check Redis connectivity

2. **Slow Response Times**
   - Review monitoring dashboard
   - Check cache hit rates
   - Analyze service metrics

3. **Learning Not Working**
   - Verify Redis connectivity
   - Check vector service status
   - Review feedback processing logs

### Debug Endpoints
```
GET /api/v1/ai/monitoring/dashboard    # Full system overview
GET /api/v1/ai/monitoring/service/{name} # Service details
POST /api/v1/ai/monitoring/health-check # Manual health check
```

## Conclusion

The OpsConductor AI System V2 provides a robust, scalable, and intelligent AI infrastructure with:
- Centralized routing and load balancing
- Continuous learning and improvement
- Real-time monitoring and alerting
- Production-ready resilience patterns
- Comprehensive observability

This architecture ensures high availability, optimal performance, and continuous improvement of AI capabilities across the OpsConductor platform.