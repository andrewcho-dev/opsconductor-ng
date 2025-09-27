# OpsConductor AI Brain - Prefect Integration

This document describes the Prefect integration implemented in Phase 2 of the OpsConductor Prefect implementation plan.

## Overview

The Prefect integration enhances the AI Brain's workflow execution capabilities by providing:

- **Intelligent Execution Routing**: Automatically chooses between Celery (simple workflows) and Prefect (complex workflows)
- **Advanced Flow Generation**: Converts OpsConductor workflows into Python Prefect flows
- **Unified API**: Single interface for both execution engines
- **Backward Compatibility**: Existing Celery workflows continue to work unchanged

## Architecture

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   AI Brain      │    │ Execution Router │    │ Prefect Client  │
│                 │    │                  │    │                 │
│ ┌─────────────┐ │    │ ┌──────────────┐ │    │ ┌─────────────┐ │
│ │ Workflow    │ │───▶│ │ Complexity   │ │───▶│ │ Flow        │ │
│ │ Generator   │ │    │ │ Analyzer     │ │    │ │ Registry    │ │
│ └─────────────┘ │    │ └──────────────┘ │    │ └─────────────┘ │
│                 │    │        │         │    │                 │
│ ┌─────────────┐ │    │        ▼         │    │ ┌─────────────┐ │
│ │ Fulfillment │ │    │ ┌──────────────┐ │    │ │ Prefect     │ │
│ │ Engine      │ │    │ │ Engine       │ │    │ │ Server      │ │
│ └─────────────┘ │    │ │ Selection    │ │    │ └─────────────┘ │
└─────────────────┘    │ └──────────────┘ │    └─────────────────┘
                       │        │         │
                       │        ▼         │
                       │ ┌──────────────┐ │
                       │ │ Celery       │ │
                       │ │ Coordinator  │ │
                       │ └──────────────┘ │
                       └──────────────────┘
```

## Components

### 1. Prefect Client (`integrations/prefect_client.py`)

Provides high-level interface for interacting with Prefect services:

- **Flow Management**: Create, register, and deploy flows
- **Execution Control**: Start, monitor, and cancel flow runs
- **Status Monitoring**: Real-time execution status and logs
- **Error Handling**: Comprehensive error handling and retry logic

```python
from integrations.prefect_client import PrefectClient, PrefectFlowDefinition

async with PrefectClient() as client:
    # Create flow
    flow_def = PrefectFlowDefinition(
        name="my_workflow",
        description="Example workflow",
        flow_code=python_code,
        parameters={"param1": "value1"}
    )
    
    result = await client.create_flow(flow_def)
    flow_id = result["flow_id"]
    
    # Execute flow
    execution = await client.execute_flow(flow_id, wait_for_completion=True)
```

### 2. Prefect Flow Generator (`job_engine/prefect_flow_generator.py`)

Converts OpsConductor workflows into executable Python Prefect flows:

- **Step Conversion**: Maps workflow steps to Prefect tasks
- **Dependency Management**: Handles task dependencies and execution order
- **Code Generation**: Generates clean, readable Python code
- **Error Handling**: Adds proper error handling and retry logic

```python
from job_engine.prefect_flow_generator import PrefectFlowGenerator

generator = PrefectFlowGenerator()
flow_definition = generator.generate_prefect_flow(workflow)
```

### 3. Execution Router (`job_engine/execution_router.py`)

Intelligently routes workflow execution between Celery and Prefect:

- **Complexity Analysis**: Analyzes workflow complexity factors
- **Engine Selection**: Chooses optimal execution engine
- **Unified Interface**: Provides consistent execution results
- **Fallback Logic**: Graceful fallback to Celery if Prefect unavailable

```python
from job_engine.execution_router import ExecutionRouter, ExecutionEngine

router = ExecutionRouter()
result = await router.route_execution(
    workflow=workflow,
    engine_preference=ExecutionEngine.AUTO
)
```

### 4. API Router (`api/prefect_router.py`)

REST API endpoints for Prefect integration:

- **Workflow Management**: Generate and execute workflows
- **Status Monitoring**: Check execution status and logs
- **Engine Information**: Get available execution engines
- **Health Checks**: Monitor Prefect service health

## Complexity Analysis

The execution router analyzes workflows based on several factors:

### Complexity Factors

| Factor | Weight | Description |
|--------|--------|-------------|
| Step Count | 20% | Number of workflow steps |
| Dependencies | 25% | Complexity of step dependencies |
| Parallel Execution | 15% | Number of parallel steps |
| Conditional Logic | 15% | Number of conditional steps |
| Error Handling | 10% | Retry logic and error handlers |
| Advanced Features | 15% | Network analysis, AI diagnosis, etc. |

### Complexity Levels

- **Simple** (≤30%): Basic workflows with few steps, minimal dependencies
- **Moderate** (31-60%): Standard workflows with some complexity
- **Complex** (61-80%): Advanced workflows with multiple dependencies
- **Advanced** (>80%): Highly complex workflows requiring Prefect features

### Engine Selection Logic

```
Simple Workflows → Celery (efficient for basic tasks)
Moderate Workflows → Celery or Prefect (based on features)
Complex/Advanced → Prefect (required for advanced features)
```

## API Endpoints

### Health and Status

```bash
# Check Prefect integration health
GET /prefect/health

# Get detailed integration status
GET /prefect/status

# List available execution engines
GET /prefect/engines
```

### Workflow Management

```bash
# Generate a workflow
POST /prefect/workflows/generate
{
  "intent_type": "system_maintenance",
  "requirements": {"action": "check_disk_space"},
  "target_systems": ["server1", "server2"]
}

# Generate and execute workflow
POST /prefect/workflows/generate-and-execute?engine_preference=auto
{
  "intent_type": "system_maintenance",
  "requirements": {"action": "check_disk_space"},
  "target_systems": ["server1", "server2"]
}

# Execute workflow asynchronously
POST /prefect/workflows/execute-async
```

### Execution Monitoring

```bash
# Get execution status
GET /prefect/executions/{execution_id}?engine=prefect

# Cancel execution
POST /prefect/executions/{execution_id}/cancel

# List Prefect flows
GET /prefect/flows
```

## Configuration

### Environment Variables

```bash
# Prefect integration
PREFECT_INTEGRATION_ENABLED=true
PREFECT_API_URL=http://prefect-server:4200/api
PREFECT_FLOW_REGISTRY_URL=http://prefect-flow-registry:4201

# AI Brain configuration
OLLAMA_HOST=http://ollama:11434
DEFAULT_MODEL=codellama:7b
```

### Docker Compose

The integration requires the Prefect services from Phase 1:

```yaml
services:
  ai-brain:
    environment:
      - PREFECT_INTEGRATION_ENABLED=true
      - PREFECT_API_URL=http://prefect-server:4200/api
      - PREFECT_FLOW_REGISTRY_URL=http://prefect-flow-registry:4201
    depends_on:
      - prefect-server
      - prefect-flow-registry
```

## Usage Examples

### Basic Workflow Execution

```python
from job_engine.workflow_generator import WorkflowGenerator

# Initialize generator
generator = WorkflowGenerator()

# Generate workflow
workflow = generator.generate_workflow(
    intent_type="system_maintenance",
    requirements={"action": "check_disk_space", "threshold": "80%"},
    target_systems=["server1", "server2"]
)

# Execute with automatic engine selection
result = await generator.execute_workflow(
    workflow=workflow,
    engine_preference="auto"
)

print(f"Executed with {result['engine_used']} engine")
print(f"Success: {result['success']}")
```

### Force Prefect Execution

```python
# Force Prefect execution for testing
result = await generator.execute_workflow(
    workflow=workflow,
    engine_preference="prefect",
    force_engine=True
)
```

### Monitor Execution

```python
from integrations.prefect_client import PrefectClient

async with PrefectClient() as client:
    execution = await client.get_flow_status(execution_id)
    
    print(f"Status: {execution.status.value}")
    print(f"Duration: {execution.duration_seconds}s")
    
    if execution.error_message:
        print(f"Error: {execution.error_message}")
```

## Testing

### Run Integration Tests

```bash
# Run the comprehensive test suite
cd /home/opsconductor/opsconductor-ng/ai-brain
python test_prefect_integration.py
```

### Test Scenarios

The test script covers:

1. **Prefect Service Availability**: Checks if Prefect services are running
2. **Workflow Generation**: Tests workflow creation from intents
3. **Flow Generation**: Tests conversion to Prefect flows
4. **Execution Routing**: Tests complexity analysis and engine selection
5. **Flow Creation**: Tests actual flow creation in Prefect
6. **Full Integration**: End-to-end workflow execution

### Expected Output

```
🚀 Starting Prefect integration tests...
✅ Prefect services are available
✅ Generated workflow: System Maintenance Workflow
✅ Generated Prefect flow: systemmaintenance_system_maintenance_workflow
✅ Execution routing decision: auto (reason: Simple workflow, using Celery for efficiency)
✅ Created Prefect flow: flow_12345
✅ Execution result for auto: Engine used: celery
🎉 All tests passed! Prefect integration is working correctly.
```

## Troubleshooting

### Common Issues

1. **Prefect Services Not Available**
   - Check if Prefect containers are running
   - Verify network connectivity
   - Check environment variables

2. **Flow Generation Errors**
   - Check workflow step types are supported
   - Verify Python code generation
   - Check for syntax errors in generated code

3. **Execution Failures**
   - Check execution logs
   - Verify target system connectivity
   - Check command/script syntax

### Debug Mode

Enable debug logging:

```python
import logging
logging.getLogger("job_engine").setLevel(logging.DEBUG)
logging.getLogger("integrations.prefect_client").setLevel(logging.DEBUG)
```

### Health Checks

```bash
# Check AI Brain health
curl http://localhost:3001/health

# Check Prefect integration health
curl http://localhost:3001/prefect/health

# Check Prefect server directly
curl http://localhost:4200/api/health
```

## Migration Guide

### From Celery-Only to Hybrid

1. **No Code Changes Required**: Existing workflows continue to work
2. **Gradual Migration**: Complex workflows automatically use Prefect
3. **Feature Flags**: Use `PREFECT_INTEGRATION_ENABLED` to control rollout
4. **Monitoring**: Monitor execution engine usage via logs and metrics

### Workflow Compatibility

- **Simple Workflows**: Continue using Celery (no change)
- **Complex Workflows**: Automatically upgraded to Prefect
- **Custom Workflows**: May require manual review for Prefect compatibility

## Performance Considerations

### Celery vs Prefect

| Aspect | Celery | Prefect |
|--------|--------|---------|
| Startup Time | Fast | Moderate |
| Memory Usage | Low | Moderate |
| Feature Set | Basic | Advanced |
| Monitoring | Limited | Comprehensive |
| Error Handling | Basic | Advanced |
| Scalability | Good | Excellent |

### Recommendations

- **Simple Tasks**: Use Celery for better performance
- **Complex Workflows**: Use Prefect for better reliability
- **High Volume**: Monitor resource usage and adjust thresholds
- **Critical Workflows**: Use Prefect for better error handling

## Future Enhancements

### Phase 3 Planned Features

- **Advanced Monitoring**: Metrics and alerting integration
- **Flow Templates**: Pre-built flow templates for common tasks
- **Dynamic Scaling**: Auto-scaling based on workload
- **Multi-Tenant**: Support for multiple organizations

### Phase 4 Planned Features

- **ML Integration**: Machine learning for workflow optimization
- **Advanced Scheduling**: Complex scheduling and triggers
- **External Integrations**: Third-party service integrations
- **Performance Optimization**: Advanced caching and optimization

## Support

For issues and questions:

1. Check the troubleshooting section above
2. Review the test script output
3. Check service logs for detailed error messages
4. Verify configuration and environment variables

The Prefect integration is designed to be backward compatible and non-disruptive to existing workflows while providing enhanced capabilities for complex automation tasks.