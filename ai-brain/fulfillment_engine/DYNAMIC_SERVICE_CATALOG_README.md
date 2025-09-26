# Dynamic Service Catalog System

## 🚀 **Revolutionary AI Knowledge Management**

The Dynamic Service Catalog is a groundbreaking system that transforms OpsConductor's AI from a pattern-matching system into a **knowledge-based reasoning engine**. It enables the AI to learn about new technical domains dynamically and provide intelligent automation solutions.

## 🎯 **Core Problem Solved**

**Before**: The AI used primitive keyword matching and hardcoded patterns, failing to understand complex requests like:
> "Connect to each Windows machine and get system information, email it to drewcho@hotmail.com every 15 minutes until 11:00pm tonight"

**After**: The AI uses comprehensive knowledge about services and APIs to reason through requirements:
- **"each Windows machine"** → Query asset service for `os_type="Windows"`
- **"get system information"** → Generate appropriate Windows/PowerShell commands
- **"email it to drewcho@hotmail.com"** → Use communication service notifications
- **"every 15 minutes until 11:00pm"** → Configure celery-beat scheduling

## 🏗️ **Architecture Overview**

### **Core Components**

1. **Dynamic Service Catalog** (`dynamic_service_catalog.py`)
   - Manages knowledge domains with intelligent context loading
   - Optimizes context size for AI reasoning
   - Provides performance monitoring and caching

2. **Knowledge Learner** (`knowledge_learner.py`)
   - Easy interface for adding new technical domains
   - Supports API discovery and manual documentation
   - Provides learning suggestions based on requests

3. **CLI Interface** (`learn_cli.py`)
   - Command-line tool for managing knowledge domains
   - Interactive learning sessions
   - Quick setup for common technologies

### **Knowledge Domain Types**

- **Core Services**: OpsConductor native services (asset, automation, communication, celery-beat)
- **Specialty APIs**: External APIs (VAPIX, AWS, Docker, Kubernetes, etc.)
- **Learned Capabilities**: AI-discovered patterns and workflows
- **Integration Patterns**: Cross-domain workflow templates

## 🔧 **Usage Examples**

### **Adding VAPIX Camera Knowledge**

```bash
# Quick setup
cd /home/opsconductor/opsconductor-ng/ai-brain/fulfillment_engine
python learn_cli.py quick vapix

# From documentation file
python learn_cli.py doc vapix_example.json "VAPIX Cameras" --keywords camera video surveillance

# From API URL (auto-discovery)
python learn_cli.py api http://192.168.1.100/axis-cgi/ "Camera System" --keywords camera ptz
```

### **Interactive Learning Session**

```bash
python learn_cli.py interactive
```

This guides you through:
1. Entering domain name and description
2. Adding relevant keywords
3. Choosing learning method (API discovery or manual)
4. Configuring capabilities and endpoints

### **Managing Knowledge Domains**

```bash
# List all known domains
python learn_cli.py list

# Export domain knowledge
python learn_cli.py export vapix_cameras --output vapix_backup.json

# Get learning suggestions for a request
python learn_cli.py suggest "monitor all docker containers"
```

## 📚 **Creating Knowledge Documentation**

### **Documentation Format**

Knowledge domains use a structured JSON format:

```json
{
  "description": "What this API/service does",
  "base_url": "Base URL pattern",
  "authentication": ["method1", "method2"],
  "capabilities": {
    "capability_name": {
      "description": "What this capability does",
      "keywords": ["keyword1", "keyword2"],
      "endpoints": [
        {
          "path": "/api/endpoint",
          "method": "GET",
          "description": "Endpoint description",
          "parameters": {"param": "description"},
          "examples": ["example usage"]
        }
      ],
      "use_cases": ["use case 1", "use case 2"]
    }
  },
  "integration_patterns": [
    {
      "name": "Pattern name",
      "description": "How to use with OpsConductor",
      "steps": ["step 1", "step 2"],
      "services_used": ["service1", "service2"]
    }
  ]
}
```

### **Example: Docker API Knowledge**

```json
{
  "description": "Docker Engine API for container management",
  "base_url": "http://localhost:2376/v1.41/",
  "authentication": ["none", "tls"],
  "capabilities": {
    "container_management": {
      "description": "Create, start, stop, and manage containers",
      "keywords": ["container", "docker", "run", "stop", "start"],
      "endpoints": [
        {
          "path": "/containers/json",
          "method": "GET",
          "description": "List containers",
          "parameters": {
            "all": "Show all containers (default false)",
            "filters": "JSON encoded filters"
          },
          "examples": ["GET /containers/json?all=true"]
        }
      ],
      "use_cases": ["Container monitoring", "Automated deployment"]
    }
  }
}
```

## 🧠 **AI Reasoning Enhancement**

### **Context Optimization**

The system intelligently manages context size:

1. **Request Analysis**: Analyzes user requests to identify relevant domains
2. **Priority Loading**: Loads core services first, then relevant specialty domains
3. **Size Management**: Stays within context limits while maximizing relevant information
4. **Caching**: Caches frequently used contexts for performance

### **Intelligent Service Selection**

The AI now receives comprehensive knowledge:

```
AUTOMATED REQUEST ANALYSIS:
Services Identified: asset-service, automation-service, vapix-cameras
Reasoning: Request mentions cameras - need VAPIX domain; Request involves automation - need automation service
Suggested Workflow: 1. Query asset service for cameras; 2. Use VAPIX API for control; 3. Use automation service for scheduling

VAPIX CAMERAS DOMAIN:
Purpose: Axis Camera VAPIX API for video surveillance and camera control
Capabilities: PTZ control, video streaming, event management
Integration Patterns: Security patrol automation, motion detection alerts
```

## 🚀 **Performance Features**

### **Scalable Architecture**

- **Modular Domains**: Each technical area is a separate, loadable module
- **Intelligent Caching**: Context caching with TTL and size management
- **Lazy Loading**: Domains loaded only when needed
- **Performance Monitoring**: Tracks context generation time and cache hit rates

### **Context Size Management**

```python
# Configure context limits
catalog.max_context_size = 50000  # 50KB max context
catalog.context_ttl = timedelta(hours=1)  # 1 hour cache TTL
```

### **Performance Metrics**

```python
metrics = catalog.get_performance_metrics()
# Returns:
# {
#   "total_domains": 15,
#   "average_context_generation_time": 0.045,
#   "cache_hit_rate": 0.85,
#   "domain_types": {"core_service": 4, "specialty_api": 8, ...}
# }
```

## 🔮 **Future Enhancements**

### **Planned Features**

1. **Dynamic API Discovery**
   - Automatic discovery of new service endpoints
   - Real-time capability updates
   - API versioning support

2. **Machine Learning Integration**
   - Learn from successful automation patterns
   - Optimize context selection based on usage
   - Predict required services for requests

3. **Collaborative Knowledge**
   - Share knowledge domains across OpsConductor instances
   - Community-contributed domain libraries
   - Automatic knowledge synchronization

4. **Advanced Integration Patterns**
   - Workflow templates for complex scenarios
   - Cross-domain dependency management
   - Automated testing of integration patterns

## 🛠️ **Development Guide**

### **Adding a New Domain Type**

1. **Create Domain Class**:
```python
class MyCustomDomain(KnowledgeDomain):
    def __init__(self):
        # Initialize metadata
        pass
    
    async def discover_capabilities(self):
        # Implement API discovery
        pass
    
    def get_context_for_request(self, keywords):
        # Return relevant context
        pass
```

2. **Register Domain**:
```python
catalog = get_dynamic_catalog()
catalog.register_domain(MyCustomDomain())
```

### **Extending the Learning Interface**

Add new learning methods to `knowledge_learner.py`:

```python
def learn_from_swagger(self, swagger_url: str, domain_name: str):
    """Learn from Swagger/OpenAPI specification"""
    # Implementation here
```

## 📊 **Monitoring and Debugging**

### **Performance Monitoring**

```python
# Get performance metrics
metrics = catalog.get_performance_metrics()
logger.info(f"Context generation time: {metrics['average_context_generation_time']:.3f}s")
logger.info(f"Cache hit rate: {metrics['cache_hit_rate']:.2%}")
```

### **Debug Context Generation**

```python
# Analyze what context would be generated
analysis = catalog.analyze_request_context_needs("monitor all cameras")
print(f"Relevant domains: {analysis['relevant_domains']}")
print(f"Estimated size: {analysis['estimated_context_size']} bytes")
```

## 🎉 **Benefits**

### **For Users**
- **Natural Language**: Speak naturally about technical requirements
- **Comprehensive Solutions**: AI understands complex, multi-service workflows
- **Extensible**: Easily add knowledge about new technologies

### **For Developers**
- **Maintainable**: No more hardcoded patterns or regex matching
- **Scalable**: Add new domains without modifying core AI logic
- **Intelligent**: AI reasons about requirements instead of pattern matching

### **For Operations**
- **Flexible**: Adapt to new technologies and APIs quickly
- **Reliable**: Comprehensive knowledge reduces automation failures
- **Efficient**: Optimized context loading for fast response times

---

## 🚀 **Getting Started**

1. **Initialize the system**:
```bash
cd /home/opsconductor/opsconductor-ng/ai-brain/fulfillment_engine
python -c "from dynamic_service_catalog import get_dynamic_catalog; catalog = get_dynamic_catalog(); print('Dynamic catalog initialized!')"
```

2. **Add your first specialty domain**:
```bash
python learn_cli.py quick vapix
```

3. **Test with a complex request**:
```
"Set up motion detection on all lobby cameras and email alerts to security@company.com"
```

The AI will now reason through this request using comprehensive knowledge of VAPIX APIs, asset management, and communication services!

---

**This system transforms OpsConductor from a simple automation tool into an intelligent infrastructure reasoning engine.** 🧠✨