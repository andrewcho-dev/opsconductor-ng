# Prefect Conversion Strategy for OpsConductor NG

## Executive Summary

This document outlines a comprehensive strategy for migrating OpsConductor NG's custom automation service to Prefect, an open-source workflow orchestration platform. The migration will replace our custom Celery-based job execution engine while preserving all existing functionality and investments in protocol libraries, AI integration, and asset management.

**Key Benefits:**
- Reduced maintenance burden (~500 lines of custom orchestration code eliminated)
- Professional-grade monitoring and observability
- Industry-standard workflow orchestration
- Better scaling and resource management
- Stronger community support and ecosystem

**Migration Timeline:** 4-6 weeks with zero downtime
**Risk Level:** Medium (mitigated by parallel deployment strategy)

---

## Current Architecture Analysis

### What We Have Built
Our current automation service consists of:

1. **Custom Celery-based Orchestration Engine** (`worker.py` - 800+ lines)
   - Custom task execution with enhanced monitoring
   - Protocol-specific libraries (SSH, PowerShell, Network Analysis)
   - Custom error handling and retry logic
   - Real-time status tracking

2. **Job Management API** (`main.py` - 1000+ lines)
   - FastAPI-based REST endpoints
   - Custom workflow validation and limits
   - Job CRUD operations with PostgreSQL storage
   - Custom scheduling and execution tracking

3. **Protocol Libraries** (`/libraries/` - 2000+ lines)
   - `linux_ssh.py` - SSH connections and bash execution
   - `windows_powershell.py` - PowerShell remoting
   - `network_analyzer.py` - Network analysis tools
   - `connection_manager.py` - Connection pooling

4. **AI Integration** (`ai-brain/integrations/automation_client.py`)
   - Dynamic workflow generation from LLM reasoning
   - Service catalog integration
   - Real-time job submission and monitoring

5. **Monitoring & WebSocket System**
   - Custom Celery monitoring (`celery_monitor.py`)
   - Real-time WebSocket updates (`websocket_manager.py`)
   - Custom status tracking and reporting

### What Works Well
- **Protocol Libraries:** Robust, well-tested, domain-specific implementations
- **AI Integration:** Seamless LLM-to-automation workflow generation
- **Asset Service Integration:** Complete asset discovery and credential management
- **Custom Validation:** Workflow complexity limits and safety checks
- **Real-time Monitoring:** Custom WebSocket-based status updates

### Pain Points
- **Maintenance Overhead:** Custom orchestration code requires ongoing maintenance
- **Limited Observability:** Basic monitoring compared to modern platforms
- **Scaling Complexity:** Manual worker management and resource allocation
- **Testing Complexity:** Custom orchestration logic is difficult to test comprehensively

---

## Prefect Platform Analysis

### Why Prefect Over Alternatives

**Prefect vs. Apache Airflow:**
- **Simpler Setup:** No complex DAG configuration
- **Python-Native:** Better fit for our existing codebase
- **Dynamic Workflows:** Better support for AI-generated workflows
- **Modern Architecture:** Cloud-native design

**Prefect vs. Temporal:**
- **Lower Complexity:** Easier learning curve for IT operations
- **Better Fit:** Designed for data/automation workflows vs. business processes
- **Ecosystem:** More relevant integrations for our use case

**Prefect vs. n8n:**
- **Programmatic Control:** Better for complex logic and AI integration
- **Maturity:** More stable for production workloads
- **Customization:** Better support for custom protocol libraries

### Prefect Advantages for Our Use Case

1. **Python-Native Workflows**
   ```python
   @flow(name="firmware_check")
   def check_camera_firmware(camera_list: List[str]):
       results = []
       for camera in camera_list:
           result = ssh_command.submit(camera, "get_firmware_version")
           results.append(result)
       return results
   ```

2. **Built-in Observability**
   - Flow run visualization
   - Task-level logging and metrics
   - Automatic dependency tracking
   - Real-time status updates

3. **Flexible Deployment Options**
   - Self-hosted server
   - Cloud-managed options
   - Hybrid deployments
   - Docker-native support

4. **AI-Friendly Architecture**
   - Dynamic task generation
   - Programmatic flow creation
   - REST API for external integration

### Prefect Limitations

1. **Learning Curve:** Team needs to learn Prefect concepts
2. **Migration Effort:** 4-6 weeks of development work
3. **Feature Gaps:** Some custom features may not have direct equivalents
4. **Dependency:** Reliance on external platform roadmap

---

## Migration Strategy

### Phase 1: Foundation Setup (Week 1)

#### 1.1 Prefect Infrastructure Deployment
```yaml
# docker-compose.prefect.yml
version: '3.8'
services:
  prefect-server:
    image: prefecthq/prefect:2-latest
    command: prefect server start --host 0.0.0.0
    ports:
      - "4200:4200"
    environment:
      PREFECT_API_URL: http://localhost:4200/api
      PREFECT_SERVER_API_HOST: 0.0.0.0
    volumes:
      - prefect_data:/root/.prefect
    networks:
      - opsconductor-net

  prefect-worker:
    image: prefecthq/prefect:2-latest
    command: prefect worker start --pool default-pool
    environment:
      PREFECT_API_URL: http://prefect-server:4200/api
    depends_on:
      - prefect-server
    volumes:
      - ./automation-service/libraries:/app/libraries
      - ./shared:/app/shared
    networks:
      - opsconductor-net
```

#### 1.2 Library Integration Testing
```python
# test_prefect_integration.py
from prefect import flow, task
from libraries.linux_ssh import LinuxSSHLibrary

@task
def test_ssh_connection(host: str):
    ssh_lib = LinuxSSHLibrary()
    return ssh_lib.test_connection(host)

@flow
def test_library_integration():
    result = test_ssh_connection("test-host")
    return result

# Verify all existing libraries work with Prefect
```

#### 1.3 Parallel Deployment Setup
- Deploy Prefect alongside existing automation service
- Configure separate database schema for Prefect jobs
- Set up routing logic to direct traffic appropriately

### Phase 2: Core Migration (Weeks 2-3)

#### 2.1 Protocol Library Adaptation
```python
# prefect_tasks.py - Wrapper tasks for existing libraries
from prefect import task
from libraries.linux_ssh import LinuxSSHLibrary
from libraries.windows_powershell import WindowsPowerShellLibrary
from libraries.network_analyzer import NetworkAnalyzer

@task(retries=3, retry_delay_seconds=5)
def execute_ssh_command(host: str, command: str, credentials: dict):
    """Execute SSH command using existing LinuxSSHLibrary"""
    ssh_lib = LinuxSSHLibrary()
    return ssh_lib.execute_command(host, command, credentials)

@task(retries=3, retry_delay_seconds=5)
def execute_powershell_script(host: str, script: str, credentials: dict):
    """Execute PowerShell script using existing WindowsPowerShellLibrary"""
    ps_lib = WindowsPowerShellLibrary()
    return ps_lib.execute_script(host, script, credentials)

@task(retries=2, retry_delay_seconds=10)
def analyze_network(target: str, analysis_type: str):
    """Perform network analysis using existing NetworkAnalyzer"""
    analyzer = NetworkAnalyzer()
    return analyzer.analyze(target, analysis_type)
```

#### 2.2 Workflow Engine Migration
```python
# prefect_workflows.py - AI-generated workflow execution
from prefect import flow
from typing import List, Dict, Any

@flow(name="ai_generated_workflow")
def execute_ai_workflow(workflow_definition: Dict[str, Any]):
    """Execute AI-generated workflow using Prefect"""
    results = []
    
    for step in workflow_definition.get("steps", []):
        step_type = step.get("type")
        
        if step_type == "ssh":
            result = execute_ssh_command(
                host=step["host"],
                command=step["command"],
                credentials=step["credentials"]
            )
        elif step_type == "powershell":
            result = execute_powershell_script(
                host=step["host"],
                script=step["script"],
                credentials=step["credentials"]
            )
        elif step_type == "network_analysis":
            result = analyze_network(
                target=step["target"],
                analysis_type=step["analysis_type"]
            )
        
        results.append({
            "step_id": step["id"],
            "step_name": step["name"],
            "result": result,
            "status": "completed"
        })
    
    return results
```

#### 2.3 API Layer Adaptation
```python
# prefect_api_adapter.py - Adapter for existing API endpoints
from prefect.client.orchestration import PrefectClient
from prefect.deployments import run_deployment
import asyncio

class PrefectAutomationAdapter:
    """Adapter to maintain existing API compatibility"""
    
    def __init__(self):
        self.prefect_client = PrefectClient()
    
    async def create_job(self, job_data: dict) -> dict:
        """Create job using Prefect deployment"""
        # Convert our job format to Prefect deployment
        deployment_name = f"ai_generated_workflow/{job_data['name']}"
        
        flow_run = await run_deployment(
            name=deployment_name,
            parameters={
                "workflow_definition": job_data["workflow_definition"]
            }
        )
        
        return {
            "success": True,
            "job_id": flow_run.id,
            "message": "Job created successfully"
        }
    
    async def get_job_status(self, job_id: str) -> dict:
        """Get job status from Prefect"""
        flow_run = await self.prefect_client.read_flow_run(job_id)
        
        return {
            "job_id": job_id,
            "status": flow_run.state.type.value,
            "started_at": flow_run.start_time,
            "completed_at": flow_run.end_time,
            "result": flow_run.state.result() if flow_run.state.is_completed() else None
        }
```

### Phase 3: AI Integration (Week 3)

#### 3.1 AI Brain Output Format Adaptation
```python
# In ai-brain/fulfillment_engine/direct_executor.py
def _parse_reasoning_response(self, response_text: str) -> Dict[str, Any]:
    """Parse LLM response and generate Prefect-compatible workflow"""
    
    # Extract workflow steps from LLM response (existing logic)
    steps = self._extract_workflow_steps(response_text)
    
    # Convert to Prefect format instead of custom format
    prefect_workflow = {
        "flow_name": "ai_generated_workflow",
        "parameters": {
            "workflow_definition": {
                "name": f"AI Workflow {datetime.now().strftime('%Y%m%d_%H%M%S')}",
                "description": "AI-generated automation workflow",
                "steps": []
            }
        }
    }
    
    for i, step in enumerate(steps):
        prefect_step = {
            "id": f"step_{i+1}",
            "name": step.get("step_name", f"Step {i+1}"),
            "type": self._determine_step_type(step),
            "host": step.get("target_systems", ["localhost"])[0],
            "command": step.get("commands", ["echo 'No command specified'"])[0],
            "credentials": self._get_credentials_for_step(step),
            "timeout": 300
        }
        prefect_workflow["parameters"]["workflow_definition"]["steps"].append(prefect_step)
    
    return prefect_workflow
```

#### 3.2 Automation Client Update
```python
# In ai-brain/integrations/automation_client.py
class PrefectAutomationClient:
    """Updated automation client for Prefect integration"""
    
    def __init__(self, prefect_api_url: str = "http://prefect-server:4200/api"):
        self.prefect_api_url = prefect_api_url
        self.adapter = PrefectAutomationAdapter()
    
    async def submit_ai_workflow(self, workflow: Dict[str, Any], job_name: str = None) -> Dict[str, Any]:
        """Submit AI-generated workflow to Prefect"""
        try:
            # Use the adapter to maintain compatibility
            result = await self.adapter.create_job({
                "name": job_name or f"ai_workflow_{int(time.time())}",
                "workflow_definition": workflow["parameters"]["workflow_definition"]
            })
            
            logger.info("AI workflow submitted to Prefect", 
                       job_id=result["job_id"], 
                       workflow_name=job_name)
            
            return result
            
        except Exception as e:
            logger.error("Failed to submit AI workflow to Prefect", error=str(e))
            raise AutomationServiceError(f"Workflow submission failed: {str(e)}")
```

### Phase 4: Testing & Validation (Week 4)

#### 4.1 Comprehensive Testing Strategy
```python
# tests/test_prefect_migration.py
import pytest
from prefect.testing.utilities import prefect_test_harness

class TestPrefectMigration:
    
    def test_library_compatibility(self):
        """Test that all existing libraries work with Prefect tasks"""
        with prefect_test_harness():
            # Test SSH library
            result = execute_ssh_command.fn("test-host", "echo 'test'", {})
            assert result is not None
            
            # Test PowerShell library
            result = execute_powershell_script.fn("test-host", "Write-Host 'test'", {})
            assert result is not None
    
    def test_workflow_execution(self):
        """Test complete workflow execution"""
        workflow_def = {
            "steps": [
                {
                    "id": "step_1",
                    "name": "Test SSH",
                    "type": "ssh",
                    "host": "test-host",
                    "command": "echo 'test'",
                    "credentials": {}
                }
            ]
        }
        
        with prefect_test_harness():
            result = execute_ai_workflow.fn(workflow_def)
            assert len(result) == 1
            assert result[0]["status"] == "completed"
    
    def test_ai_integration(self):
        """Test AI brain integration with Prefect"""
        # Test workflow generation and submission
        pass
```

#### 4.2 Performance Comparison
```python
# performance_comparison.py
import time
import asyncio
from concurrent.futures import ThreadPoolExecutor

async def benchmark_current_system():
    """Benchmark current Celery-based system"""
    start_time = time.time()
    # Execute test workflows using current system
    end_time = time.time()
    return end_time - start_time

async def benchmark_prefect_system():
    """Benchmark Prefect-based system"""
    start_time = time.time()
    # Execute same test workflows using Prefect
    end_time = time.time()
    return end_time - start_time

# Compare execution times, resource usage, etc.
```

### Phase 5: Gradual Cutover (Weeks 5-6)

#### 5.1 Traffic Routing Strategy
```python
# traffic_router.py - Route traffic between old and new systems
class AutomationTrafficRouter:
    """Route automation requests between current and Prefect systems"""
    
    def __init__(self):
        self.prefect_enabled_percentage = 0  # Start with 0%
        self.current_automation_client = CurrentAutomationClient()
        self.prefect_automation_client = PrefectAutomationClient()
    
    async def submit_workflow(self, workflow_data: dict) -> dict:
        """Route workflow submission based on configuration"""
        import random
        
        if random.randint(1, 100) <= self.prefect_enabled_percentage:
            logger.info("Routing to Prefect system")
            return await self.prefect_automation_client.submit_ai_workflow(workflow_data)
        else:
            logger.info("Routing to current system")
            return await self.current_automation_client.submit_ai_workflow(workflow_data)
    
    def increase_prefect_traffic(self, percentage: int):
        """Gradually increase traffic to Prefect"""
        self.prefect_enabled_percentage = min(100, percentage)
        logger.info(f"Prefect traffic increased to {self.prefect_enabled_percentage}%")
```

#### 5.2 Rollout Schedule
- **Week 5 Day 1:** 10% traffic to Prefect
- **Week 5 Day 3:** 25% traffic to Prefect
- **Week 5 Day 5:** 50% traffic to Prefect
- **Week 6 Day 2:** 75% traffic to Prefect
- **Week 6 Day 4:** 100% traffic to Prefect
- **Week 6 Day 5:** Remove old system

#### 5.3 Monitoring & Rollback Plan
```python
# monitoring.py - Monitor both systems during migration
class MigrationMonitor:
    """Monitor system health during migration"""
    
    def __init__(self):
        self.error_threshold = 5  # Max errors per hour
        self.performance_threshold = 2.0  # Max 2x slower than current
    
    async def check_system_health(self):
        """Check health of both systems"""
        current_errors = await self.get_current_system_errors()
        prefect_errors = await self.get_prefect_system_errors()
        
        if prefect_errors > self.error_threshold:
            logger.error("Prefect system error threshold exceeded")
            await self.trigger_rollback()
    
    async def trigger_rollback(self):
        """Rollback to current system if issues detected"""
        router = AutomationTrafficRouter()
        router.increase_prefect_traffic(0)  # Route all traffic back
        logger.critical("ROLLBACK TRIGGERED - All traffic routed to current system")
```

---

## Detailed Component Mapping

### What Stays Exactly the Same ✅

#### 1. Protocol Libraries (100% Reusable)
```
automation-service/libraries/
├── linux_ssh.py          ✅ No changes needed
├── windows_powershell.py ✅ No changes needed
├── network_analyzer.py   ✅ No changes needed
└── connection_manager.py ✅ No changes needed
```

#### 2. Asset Service Integration (100% Unchanged)
```python
# Asset client calls remain identical
asset_client = AssetServiceClient()
cameras = await asset_client.get_assets_by_type("axis_camera")
credentials = await asset_client.get_asset_credentials(camera_id)
```

#### 3. AI Brain Core Logic (95% Unchanged)
- Service catalog and discovery
- LLM reasoning and decision making
- Dynamic service orchestration
- Only output format changes

#### 4. Database Schema (Optional Migration)
- Can keep existing job tables for historical data
- Prefect uses its own schema for new jobs
- Migration scripts available if full consolidation desired

### What Gets Replaced 🔄

#### 1. Job Orchestration Engine
**Before:** Custom Celery worker (`worker.py` - 800 lines)
**After:** Prefect flows and tasks (~100 lines)

#### 2. Job Management API
**Before:** Custom FastAPI endpoints (`main.py` - 1000 lines)
**After:** Prefect API + thin adapter layer (~200 lines)

#### 3. Monitoring System
**Before:** Custom monitoring (`celery_monitor.py` - 400 lines)
**After:** Built-in Prefect UI and API

#### 4. WebSocket Management
**Before:** Custom WebSocket manager (`websocket_manager.py` - 300 lines)
**After:** Prefect's built-in real-time updates

### What Gets Enhanced 📈

#### 1. Workflow Visualization
**Before:** No visual representation
**After:** Automatic flow graphs and dependency visualization

#### 2. Error Handling
**Before:** Custom retry logic
**After:** Declarative retry policies with exponential backoff

#### 3. Scaling
**Before:** Manual worker management
**After:** Automatic scaling based on workload

#### 4. Observability
**Before:** Basic logging and status tracking
**After:** Rich metrics, tracing, and performance monitoring

---

## Risk Assessment & Mitigation

### High Risk Items

#### 1. **Migration Complexity**
**Risk:** Complex migration could introduce bugs or downtime
**Mitigation:** 
- Parallel deployment strategy
- Comprehensive testing at each phase
- Gradual traffic cutover with rollback capability

#### 2. **Performance Regression**
**Risk:** Prefect might be slower than optimized Celery setup
**Mitigation:**
- Thorough performance benchmarking
- Load testing before full cutover
- Performance monitoring during migration

#### 3. **Feature Loss**
**Risk:** Some custom features might not have Prefect equivalents
**Mitigation:**
- Detailed feature mapping and gap analysis
- Custom Prefect extensions where needed
- Maintain critical features through adapter layer

### Medium Risk Items

#### 1. **Learning Curve**
**Risk:** Team unfamiliarity with Prefect concepts
**Mitigation:**
- Prefect training for development team
- Comprehensive documentation
- Gradual introduction of Prefect concepts

#### 2. **Integration Issues**
**Risk:** Unexpected integration problems with existing services
**Mitigation:**
- Extensive integration testing
- Staged rollout with monitoring
- Maintain current system as fallback

### Low Risk Items

#### 1. **Library Compatibility**
**Risk:** Existing libraries might not work with Prefect
**Mitigation:** Libraries are pure Python and will work seamlessly

#### 2. **Database Migration**
**Risk:** Data loss during database migration
**Mitigation:** Optional migration - can run parallel schemas

---

## Success Metrics

### Technical Metrics
- **Code Reduction:** Target 60% reduction in orchestration code
- **Performance:** Maintain current performance levels (±10%)
- **Reliability:** Maintain 99.9% uptime during migration
- **Error Rate:** No increase in job failure rates

### Operational Metrics
- **Deployment Time:** Reduce deployment complexity by 50%
- **Monitoring:** Improve observability with rich UI and metrics
- **Scaling:** Automatic scaling vs. manual worker management
- **Maintenance:** Reduce maintenance overhead by 70%

### Business Metrics
- **Feature Velocity:** Faster development of new automation features
- **System Reliability:** Improved error handling and recovery
- **Operational Efficiency:** Better resource utilization
- **Team Productivity:** Less time spent on infrastructure maintenance

---

## Implementation Timeline

### Week 1: Foundation
- [ ] Deploy Prefect infrastructure
- [ ] Test library compatibility
- [ ] Set up parallel deployment
- [ ] Create basic Prefect tasks

### Week 2: Core Migration
- [ ] Migrate protocol libraries to Prefect tasks
- [ ] Implement workflow execution engine
- [ ] Create API adapter layer
- [ ] Basic integration testing

### Week 3: AI Integration
- [ ] Update AI brain output format
- [ ] Modify automation client
- [ ] End-to-end testing
- [ ] Performance benchmarking

### Week 4: Testing & Validation
- [ ] Comprehensive test suite
- [ ] Load testing
- [ ] Security validation
- [ ] Documentation updates

### Week 5: Gradual Cutover
- [ ] 10% → 25% → 50% traffic migration
- [ ] Monitor system health
- [ ] Performance validation
- [ ] Issue resolution

### Week 6: Full Migration
- [ ] 75% → 100% traffic migration
- [ ] Remove old system
- [ ] Final validation
- [ ] Team training and handover

---

## Rollback Strategy

### Immediate Rollback (< 5 minutes)
```python
# Emergency rollback - route all traffic to current system
router = AutomationTrafficRouter()
router.increase_prefect_traffic(0)
```

### Partial Rollback (< 30 minutes)
- Reduce Prefect traffic percentage
- Investigate and fix issues
- Gradually increase traffic again

### Full Rollback (< 2 hours)
- Completely disable Prefect system
- Restore all traffic to current system
- Preserve Prefect data for later analysis

### Rollback Triggers
- Error rate > 5% above baseline
- Performance degradation > 50%
- Critical functionality failure
- Manual trigger by operations team

---

## Post-Migration Benefits

### Immediate Benefits (Week 1-4)
- **Reduced Maintenance:** No more custom orchestration code to maintain
- **Better Monitoring:** Rich UI for workflow visualization and debugging
- **Improved Reliability:** Built-in error handling and retry mechanisms

### Medium-term Benefits (Month 2-6)
- **Faster Development:** Easier to create and modify workflows
- **Better Scaling:** Automatic resource management
- **Enhanced Observability:** Detailed metrics and performance tracking

### Long-term Benefits (6+ Months)
- **Community Support:** Access to Prefect ecosystem and community
- **Future-proofing:** Industry-standard platform with active development
- **Reduced Technical Debt:** Less custom code to maintain and update

---

## Conclusion

The migration to Prefect represents a strategic investment in OpsConductor NG's future. While requiring significant upfront effort (4-6 weeks), the migration will:

1. **Preserve all existing investments** in protocol libraries, AI integration, and asset management
2. **Reduce long-term maintenance burden** by eliminating custom orchestration code
3. **Improve system reliability and observability** through professional-grade tooling
4. **Enable faster feature development** with industry-standard workflow patterns

The parallel deployment strategy minimizes risk while the gradual cutover ensures system stability. With proper execution, this migration will position OpsConductor NG for scalable growth while maintaining all current functionality.

**Recommendation:** Proceed with migration using the phased approach outlined in this document.