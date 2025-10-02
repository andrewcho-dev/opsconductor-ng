# OpsConductor Execution Architecture - Comprehensive Proposal

## 📋 Executive Summary

**Current State**: The OpsConductor pipeline successfully processes user requests through 4 stages (A→B→C→D), generating intelligent execution plans but **NOT executing them**. The system operates as a "planning assistant" that tells users what it *would* do, rather than an "execution assistant" that actually *does* it.

**Goal**: Design and implement a robust execution layer that can handle requests ranging from simple information queries to complex multi-step operations, while maintaining safety, observability, and user control.

---

## 🏗️ Current Architecture Analysis

### What We Have (Stages A-D)

```
User Request
    ↓
Stage A: Classifier (Intent Classification)
    ↓
Stage B: Selector (Tool Selection)
    ↓
Stage C: Planner (Execution Plan Generation)
    ↓
Stage D: Answerer (Response Generation)
    ↓
[EXECUTION GAP - Nothing happens here]
    ↓
User sees plan description, not results
```

### Existing Infrastructure

**Services Available:**
- ✅ **asset-service** (port 3001): Asset/server management, credential storage
- ✅ **automation-service** (port 3003): Direct command execution (SSH, PowerShell, local)
- ✅ **network-analyzer-service** (port 3004): Network analysis and monitoring
- ✅ **communication-service** (port 3006): Notifications and alerts
- ✅ **AI Pipeline** (port 3005): Current 4-stage pipeline

**Orchestration Options:**
- ⚠️ **Prefect**: Mentioned in docs but unclear if deployed/configured
- ✅ **Direct HTTP**: All services expose REST APIs
- ✅ **Automation Service**: Has workflow execution capability

**Data Storage:**
- ✅ **PostgreSQL**: Database for persistent storage
- ✅ **Redis**: Cache and session storage

---

## 🎯 Design Principles

Before proposing solutions, let's establish core principles:

### 1. **Safety First**
- Never execute destructive operations without explicit approval
- Always validate preconditions before execution
- Implement circuit breakers for cascading failures
- Provide rollback capabilities where possible

### 2. **Progressive Complexity**
- Simple queries should execute immediately (no approval needed)
- Medium-risk operations should show plan and ask for confirmation
- High-risk operations should require explicit approval at each step
- Critical operations should have multi-level approval

### 3. **Observability**
- Every execution should be tracked and logged
- Real-time progress updates for long-running operations
- Clear error messages and failure diagnostics
- Audit trail for compliance and debugging

### 4. **User Control**
- Users should understand what will happen before it happens
- Users should be able to stop execution at any point
- Users should receive clear feedback on execution status
- Users should be able to review execution history

### 5. **Scalability**
- Support both synchronous (immediate) and asynchronous (background) execution
- Handle parallel execution of independent steps
- Queue management for resource-constrained operations
- Graceful degradation under load

---

## 🔀 Execution Architecture Options

### **Option 1: Stage E - Direct Execution Layer** ⭐ **RECOMMENDED FOR PHASE 1**

**Concept**: Add a new Stage E that directly executes plans from Stage C, with built-in approval gates.

```
Stage A → Stage B → Stage C → Stage D → [Stage E: Executor] → Results
                                ↓
                          (Optional: Show plan
                           and request approval)
```

**Architecture:**
```
pipeline/stages/stage_e/
├── executor.py              # Main execution orchestrator
├── execution_engine.py      # Core execution logic
├── approval_manager.py      # Approval workflow handling
├── progress_tracker.py      # Real-time progress updates
├── result_aggregator.py     # Collect and format results
└── execution_context.py     # Execution state management
```

**Pros:**
- ✅ Natural extension of existing pipeline architecture
- ✅ Consistent with Stages A-D design patterns
- ✅ Easy to test and validate independently
- ✅ Clear separation of concerns (planning vs execution)
- ✅ Can reuse existing Stage C plans without modification
- ✅ Simple to implement approval gates at stage boundary

**Cons:**
- ❌ Synchronous execution may block for long-running operations
- ❌ No built-in job queuing or scheduling
- ❌ Limited scalability for parallel operations
- ❌ May need additional async handling for complex workflows

**Best For:**
- Simple to medium complexity operations
- Operations that complete in < 30 seconds
- Scenarios where immediate feedback is important
- MVP/Phase 1 implementation

**Implementation Complexity:** 🟢 Low (2-3 days)

---

### **Option 2: Hybrid - Stage E + Background Job Queue** ⭐ **RECOMMENDED FOR PHASE 2**

**Concept**: Stage E decides whether to execute immediately or queue for background processing.

```
Stage C → Stage D → Stage E (Decision Point)
                        ↓
                   ┌────┴────┐
                   ↓         ↓
            Immediate    Background
            Execution      Queue
                ↓            ↓
            Results    Job Tracker
                         ↓
                    Async Results
```

**Decision Logic:**
```python
def should_execute_immediately(plan: PlanV1) -> bool:
    """Decide execution mode based on plan characteristics"""
    
    # Execute immediately if:
    - Estimated time < 30 seconds
    - Single step with no dependencies
    - Read-only operation (info mode)
    - User explicitly requested immediate execution
    
    # Queue for background if:
    - Estimated time > 30 seconds
    - Multiple steps with complex dependencies
    - Requires approval (async approval workflow)
    - Resource-intensive operation
```

**Architecture:**
```
pipeline/stages/stage_e/
├── executor.py                    # Main orchestrator
├── immediate_executor.py          # Sync execution for simple ops
├── background_executor.py         # Async execution for complex ops
├── job_queue.py                   # Job queue management (Redis-based)
├── job_tracker.py                 # Track background job status
├── approval_workflow.py           # Async approval handling
└── execution_strategies/
    ├── simple_execution.py        # Single-step execution
    ├── sequential_execution.py    # Multi-step sequential
    └── parallel_execution.py      # Parallel step execution
```

**Pros:**
- ✅ Best of both worlds (immediate + background)
- ✅ Scalable for complex operations
- ✅ Non-blocking for long-running tasks
- ✅ Can handle approval workflows asynchronously
- ✅ Better user experience (no waiting for slow ops)
- ✅ Can leverage Redis for job queue

**Cons:**
- ❌ More complex implementation
- ❌ Requires job tracking and status polling
- ❌ Need WebSocket or polling for real-time updates
- ❌ More moving parts to test and debug

**Best For:**
- Production-ready system
- Mix of simple and complex operations
- Operations requiring approval workflows
- Scalable long-term solution

**Implementation Complexity:** 🟡 Medium (5-7 days)

---

### **Option 3: Prefect Integration - Full Orchestration** 

**Concept**: Use Prefect as the execution engine, converting Stage C plans into Prefect flows.

```
Stage C → Stage D → Prefect Flow Generator
                         ↓
                    Prefect Server
                         ↓
                    Flow Execution
                         ↓
                    Service Calls
                         ↓
                    Results
```

**Architecture:**
```
pipeline/integration/prefect/
├── flow_generator.py          # Convert PlanV1 to Prefect flows
├── task_definitions.py        # Prefect task wrappers for services
├── flow_executor.py           # Submit and monitor flows
├── result_collector.py        # Collect flow execution results
└── prefect_config.py          # Prefect server configuration
```

**Pros:**
- ✅ Enterprise-grade orchestration
- ✅ Built-in retry, failure handling, and monitoring
- ✅ Excellent observability and debugging
- ✅ Supports complex DAG execution
- ✅ Scalable and production-ready
- ✅ Already mentioned in architecture docs

**Cons:**
- ❌ Requires Prefect server deployment and configuration
- ❌ Additional infrastructure complexity
- ❌ Learning curve for Prefect concepts
- ❌ May be overkill for simple operations
- ❌ Adds external dependency

**Best For:**
- Complex multi-service workflows
- Enterprise production environments
- Operations requiring sophisticated orchestration
- Long-term scalability and maintainability

**Implementation Complexity:** 🔴 High (10-14 days)

---

### **Option 4: Service-Direct Execution**

**Concept**: Skip Stage E entirely, have Stage D directly call services based on plan.

```
Stage C → Stage D → Direct Service Calls → Results
```

**Pros:**
- ✅ Simplest possible implementation
- ✅ No new components needed
- ✅ Fast execution for simple operations

**Cons:**
- ❌ Violates separation of concerns
- ❌ Stage D becomes bloated with execution logic
- ❌ Hard to add approval workflows
- ❌ Difficult to track execution state
- ❌ No scalability for complex operations
- ❌ Mixes response generation with execution

**Best For:**
- Quick prototype/demo only
- **NOT RECOMMENDED** for production

**Implementation Complexity:** 🟢 Very Low (1 day) - but creates technical debt

---

## 🎯 Recommended Approach: Phased Implementation

### **Phase 1: Stage E - Simple Execution (Weeks 1-2)**

**Goal**: Get basic execution working for simple, safe operations.

**Scope:**
- Implement Stage E with immediate execution only
- Support information queries (read-only operations)
- Basic approval gates for medium-risk operations
- Simple progress tracking and result aggregation

**Request Types Supported:**
- ✅ "How many assets do we have?" → Execute asset-service query immediately
- ✅ "Show me server details for X" → Execute asset-service query immediately
- ✅ "Check disk space on server X" → Execute with approval confirmation
- ❌ Complex multi-step workflows (deferred to Phase 2)

**Implementation:**
```python
# pipeline/stages/stage_e/executor.py

class StageEExecutor:
    """Stage E: Execution Layer"""
    
    async def execute_plan(
        self, 
        plan: PlanV1, 
        decision: DecisionV1,
        context: Optional[Dict[str, Any]] = None
    ) -> ExecutionResultV1:
        """
        Execute a plan from Stage C.
        
        Phase 1: Simple immediate execution with approval gates.
        """
        
        # 1. Assess execution mode
        execution_mode = self._determine_execution_mode(plan, decision)
        
        # 2. Check if approval needed
        if self._requires_approval(plan, decision):
            approval_response = await self._request_approval(plan, decision)
            if not approval_response.approved:
                return self._create_approval_denied_result(approval_response)
        
        # 3. Execute plan steps
        results = await self._execute_steps(plan.plan.steps)
        
        # 4. Aggregate and return results
        return self._aggregate_results(results, plan, decision)
```

**Deliverables:**
- ✅ Stage E executor implementation
- ✅ Approval workflow for medium/high-risk operations
- ✅ Integration with asset-service and automation-service
- ✅ Basic progress tracking
- ✅ Unit tests and integration tests
- ✅ Updated pipeline orchestrator to call Stage E

**Success Criteria:**
- User asks "how many assets do we have?" → Gets actual count (6 Windows workstations)
- User asks "restart service X" → Sees plan, approves, service restarts
- All executions are logged and auditable

---

### **Phase 2: Background Execution + Job Queue (Weeks 3-4)**

**Goal**: Add support for long-running and complex operations.

**Scope:**
- Implement background job queue (Redis-based)
- Add job tracking and status polling
- Support multi-step sequential execution
- WebSocket support for real-time progress updates

**Request Types Supported:**
- ✅ All Phase 1 operations
- ✅ Long-running operations (> 30 seconds)
- ✅ Multi-step workflows with dependencies
- ✅ Parallel execution of independent steps
- ✅ Async approval workflows

**Implementation:**
```python
# pipeline/stages/stage_e/background_executor.py

class BackgroundExecutor:
    """Background execution for long-running operations"""
    
    async def queue_execution(
        self, 
        plan: PlanV1, 
        decision: DecisionV1
    ) -> JobReference:
        """Queue plan for background execution"""
        
        job_id = self._generate_job_id()
        
        # Store job in Redis
        await self.job_queue.enqueue(
            job_id=job_id,
            plan=plan,
            decision=decision,
            status="queued"
        )
        
        # Start background worker
        asyncio.create_task(self._execute_job(job_id))
        
        return JobReference(
            job_id=job_id,
            status_url=f"/execution/status/{job_id}",
            estimated_duration=plan.execution_metadata.total_estimated_time
        )
```

**Deliverables:**
- ✅ Background job queue implementation
- ✅ Job tracking and status API
- ✅ WebSocket support for real-time updates
- ✅ Sequential and parallel execution strategies
- ✅ Async approval workflow
- ✅ Job history and audit trail

---

### **Phase 3: Prefect Integration (Weeks 5-6) - Optional**

**Goal**: Replace custom execution engine with Prefect for enterprise-grade orchestration.

**Scope:**
- Deploy and configure Prefect server
- Convert Stage C plans to Prefect flows
- Implement Prefect task wrappers for all services
- Migrate existing executions to Prefect

**When to Implement:**
- Complex DAG execution requirements emerge
- Need for sophisticated retry and failure handling
- Enterprise production deployment
- Team has Prefect expertise

---

## 📊 Request Complexity Matrix

| Request Type | Execution Mode | Approval Required | Estimated Time | Phase |
|-------------|----------------|-------------------|----------------|-------|
| **Simple Info Query** | Immediate | No | < 5s | Phase 1 |
| "How many assets?" | Sync | No | 1-2s | ✅ |
| "Show server details" | Sync | No | 1-3s | ✅ |
| **Medium Info Query** | Immediate | Optional | 5-30s | Phase 1 |
| "Check disk space" | Sync | Yes (confirm) | 5-10s | ✅ |
| "Analyze logs" | Sync | No | 10-20s | ✅ |
| **Simple Action** | Immediate | Yes | 5-30s | Phase 1 |
| "Restart service" | Sync | Yes (confirm) | 10-15s | ✅ |
| "Update config" | Sync | Yes (confirm) | 5-10s | ✅ |
| **Complex Action** | Background | Yes | 30s-5m | Phase 2 |
| "Deploy application" | Async | Yes (multi-step) | 2-5m | Phase 2 |
| "Backup database" | Async | Yes (confirm) | 1-3m | Phase 2 |
| **Multi-Service Workflow** | Background | Yes | 1-10m | Phase 2 |
| "Full system health check" | Async | No | 2-5m | Phase 2 |
| "Disaster recovery" | Async | Yes (multi-level) | 5-10m | Phase 2 |

---

## 🔐 Approval Workflow Design

### Approval Levels

**Level 0: No Approval (Auto-Execute)**
- Read-only operations
- Information queries
- Status checks
- Risk level: LOW
- Examples: "how many assets?", "show server details"

**Level 1: Confirmation Required**
- Single-step operations
- Reversible actions
- Medium risk
- Examples: "restart service", "check disk space"

**Level 2: Plan Review + Approval**
- Multi-step operations
- Potentially destructive
- High risk
- Examples: "deploy application", "update production config"

**Level 3: Step-by-Step Approval**
- Critical operations
- Irreversible actions
- Very high risk
- Examples: "delete database", "modify security rules"

### Approval Flow

```python
class ApprovalManager:
    """Manage approval workflows for execution"""
    
    def determine_approval_level(self, plan: PlanV1, decision: DecisionV1) -> ApprovalLevel:
        """Determine required approval level"""
        
        # Check risk level from Stage B
        if decision.risk_level == RiskLevel.LOW:
            return ApprovalLevel.NONE
        
        # Check if production environment
        if plan.execution_metadata.approval_points:
            if len(plan.execution_metadata.approval_points) > 1:
                return ApprovalLevel.STEP_BY_STEP
            else:
                return ApprovalLevel.PLAN_REVIEW
        
        # Default to confirmation for medium risk
        return ApprovalLevel.CONFIRMATION
    
    async def request_approval(
        self, 
        plan: PlanV1, 
        level: ApprovalLevel
    ) -> ApprovalResponse:
        """Request approval from user"""
        
        if level == ApprovalLevel.NONE:
            return ApprovalResponse(approved=True, auto_approved=True)
        
        # Generate approval request
        approval_request = self._generate_approval_request(plan, level)
        
        # Send to frontend for user decision
        # (In Phase 1: synchronous, Phase 2: async with timeout)
        response = await self._wait_for_user_approval(approval_request)
        
        return response
```

---

## 🎨 Frontend Integration

### Phase 1: Simple Approval Dialog

```typescript
// Frontend approval flow for Phase 1

interface ExecutionPlan {
  steps: ExecutionStep[];
  estimatedTime: number;
  riskLevel: 'low' | 'medium' | 'high';
  requiresApproval: boolean;
}

async function handleUserQuery(query: string) {
  // 1. Send to pipeline
  const response = await fetch('/pipeline', {
    method: 'POST',
    body: JSON.stringify({ request: query })
  });
  
  const result = await response.json();
  
  // 2. Check if approval needed
  if (result.requires_approval) {
    // Show approval dialog
    const approved = await showApprovalDialog({
      plan: result.execution_plan,
      estimatedTime: result.estimated_time,
      riskLevel: result.risk_level
    });
    
    if (!approved) {
      return { status: 'cancelled' };
    }
    
    // 3. Execute with approval
    const executionResult = await fetch('/pipeline/execute', {
      method: 'POST',
      body: JSON.stringify({
        plan_id: result.plan_id,
        approved: true
      })
    });
    
    return executionResult.json();
  }
  
  // 4. Auto-executed, show results
  return result;
}
```

### Phase 2: Real-Time Progress Tracking

```typescript
// WebSocket connection for real-time updates

function trackExecution(jobId: string) {
  const ws = new WebSocket(`ws://localhost:3005/execution/track/${jobId}`);
  
  ws.onmessage = (event) => {
    const update = JSON.parse(event.data);
    
    switch (update.type) {
      case 'progress':
        updateProgressBar(update.progress);
        break;
      case 'step_complete':
        markStepComplete(update.step_id);
        break;
      case 'approval_required':
        showApprovalDialog(update.approval_request);
        break;
      case 'complete':
        showResults(update.results);
        break;
      case 'error':
        showError(update.error);
        break;
    }
  };
}
```

---

## 📈 Execution Result Schema

```python
# pipeline/schemas/execution_result_v1.py

from pydantic import BaseModel
from typing import List, Dict, Any, Optional
from datetime import datetime
from enum import Enum

class ExecutionStatus(str, Enum):
    """Execution status"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    APPROVAL_REQUIRED = "approval_required"

class StepResult(BaseModel):
    """Result of a single execution step"""
    step_id: str
    status: ExecutionStatus
    started_at: datetime
    completed_at: Optional[datetime] = None
    duration_seconds: Optional[float] = None
    output: Optional[Dict[str, Any]] = None
    error: Optional[str] = None

class ExecutionResultV1(BaseModel):
    """Complete execution result"""
    execution_id: str
    plan_id: str
    status: ExecutionStatus
    started_at: datetime
    completed_at: Optional[datetime] = None
    total_duration_seconds: Optional[float] = None
    
    step_results: List[StepResult]
    
    # Aggregated results
    success_count: int
    failure_count: int
    
    # Final output
    output: Optional[Dict[str, Any]] = None
    error_message: Optional[str] = None
    
    # Metadata
    approved_by: Optional[str] = None
    approval_timestamp: Optional[datetime] = None
```

---

## 🧪 Testing Strategy

### Unit Tests
- ✅ Stage E executor logic
- ✅ Approval workflow
- ✅ Step execution strategies
- ✅ Result aggregation
- ✅ Error handling

### Integration Tests
- ✅ End-to-end pipeline (A→B→C→D→E)
- ✅ Service integration (asset-service, automation-service)
- ✅ Approval flow with user interaction
- ✅ Background job execution (Phase 2)

### Live Tests
- ✅ Real asset-service queries
- ✅ Real automation-service commands (safe operations only)
- ✅ Multi-step workflows
- ✅ Failure scenarios and rollback

---

## 🚀 Implementation Roadmap

### Week 1: Stage E Foundation
- [ ] Create Stage E directory structure
- [ ] Implement basic executor
- [ ] Add approval manager
- [ ] Integrate with pipeline orchestrator
- [ ] Unit tests

### Week 2: Service Integration
- [ ] Asset-service integration
- [ ] Automation-service integration
- [ ] Result aggregation
- [ ] Error handling
- [ ] Integration tests

### Week 3: Background Execution (Phase 2)
- [ ] Redis job queue
- [ ] Background executor
- [ ] Job tracking API
- [ ] Status polling

### Week 4: Real-Time Updates (Phase 2)
- [ ] WebSocket support
- [ ] Progress tracking
- [ ] Frontend integration
- [ ] Live testing

---

## 💡 Key Decisions Needed

1. **Immediate vs Phased**: Should we implement Phase 1 only, or commit to Phase 2 from the start?
   - **Recommendation**: Start with Phase 1, validate with real usage, then decide on Phase 2

2. **Approval UX**: Synchronous (blocking) or asynchronous (notification-based) approval?
   - **Recommendation**: Phase 1 synchronous, Phase 2 add async option

3. **Prefect Integration**: Should we plan for Prefect from the start, or keep it optional?
   - **Recommendation**: Keep optional, implement if complexity demands it

4. **Execution Persistence**: Should we store all execution history in PostgreSQL?
   - **Recommendation**: Yes, for audit trail and debugging

5. **Rollback Support**: Should we implement automatic rollback for failed operations?
   - **Recommendation**: Phase 1 manual rollback instructions, Phase 2 automatic where possible

---

## 📝 Summary & Recommendation

**Recommended Approach**: **Phased Implementation starting with Stage E**

**Phase 1 (Weeks 1-2)**: 
- Implement Stage E with immediate execution
- Support simple information queries and basic actions
- Add approval gates for medium/high-risk operations
- Get "how many assets?" working end-to-end

**Phase 2 (Weeks 3-4)**: 
- Add background job queue for long-running operations
- Implement real-time progress tracking
- Support complex multi-step workflows

**Phase 3 (Optional)**: 
- Prefect integration if complexity demands it

**Why This Approach:**
1. ✅ **Incremental value**: Phase 1 delivers immediate user value
2. ✅ **Risk mitigation**: Test with simple operations before complex ones
3. ✅ **Learn and adapt**: Real usage informs Phase 2 design
4. ✅ **Clear milestones**: Each phase has concrete deliverables
5. ✅ **Maintainable**: Builds on existing architecture patterns

**Next Steps:**
1. Review and approve this proposal
2. Create detailed Phase 1 implementation plan
3. Set up Stage E directory structure
4. Begin implementation

---

**Document Version**: 1.0  
**Date**: 2025-01-XX  
**Status**: Proposal - Awaiting Approval