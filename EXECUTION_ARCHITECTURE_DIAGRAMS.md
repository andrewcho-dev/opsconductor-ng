# OpsConductor Execution Architecture - Visual Diagrams

## 📊 Current State vs Proposed State

### Current State: Planning Only (No Execution)

```
┌─────────────────────────────────────────────────────────────────┐
│                        USER REQUEST                              │
│                  "How many assets do we have?"                   │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│  STAGE A: CLASSIFIER                                             │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │ Intent: information/asset_count                           │  │
│  │ Confidence: 0.95                                          │  │
│  │ Entities: {}                                              │  │
│  └──────────────────────────────────────────────────────────┘  │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│  STAGE B: SELECTOR                                               │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │ Selected Tools: ["asset-service-query"]                  │  │
│  │ Risk Level: LOW                                           │  │
│  │ Requires Approval: false                                  │  │
│  └──────────────────────────────────────────────────────────┘  │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│  STAGE C: PLANNER                                                │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │ Step 1: Query asset-service for total count              │  │
│  │   Tool: asset-service-query                               │  │
│  │   Inputs: {query_type: "count"}                           │  │
│  │   Estimated Duration: 2s                                  │  │
│  └──────────────────────────────────────────────────────────┘  │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│  STAGE D: ANSWERER                                               │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │ Response: "I'll gather the total number of assets using  │  │
│  │ our asset-service-query tool, which will take just a     │  │
│  │ moment to process. You can expect an accurate count      │  │
│  │ shortly."                                                 │  │
│  └──────────────────────────────────────────────────────────┘  │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ▼
                    ┌────────────────┐
                    │  ❌ EXECUTION  │
                    │   GAP HERE     │
                    └────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│                      USER SEES RESPONSE                          │
│  "I'll gather the total number of assets using our              │
│   asset-service-query tool..."                                  │
│                                                                  │
│  ❌ NO ACTUAL COUNT PROVIDED                                    │
└─────────────────────────────────────────────────────────────────┘
```

---

### Proposed State: Full Execution (Phase 1)

```
┌─────────────────────────────────────────────────────────────────┐
│                        USER REQUEST                              │
│                  "How many assets do we have?"                   │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ▼
                    ┌────────────────┐
                    │   STAGE A-D    │
                    │  (Same as now) │
                    └────────┬───────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│  STAGE E: EXECUTOR (NEW!)                                        │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │ 1. Assess Execution Mode                                  │  │
│  │    → Immediate (estimated time: 2s)                       │  │
│  │                                                            │  │
│  │ 2. Check Approval Required                                │  │
│  │    → No (risk level: LOW, read-only)                      │  │
│  │                                                            │  │
│  │ 3. Execute Plan Steps                                     │  │
│  │    ┌────────────────────────────────────────────────┐    │  │
│  │    │ Step 1: Query asset-service                     │    │  │
│  │    │   HTTP POST → http://asset-service:3001/query   │    │  │
│  │    │   Status: ✅ SUCCESS                            │    │  │
│  │    │   Duration: 1.2s                                │    │  │
│  │    │   Result: {"total_count": 6}                    │    │  │
│  │    └────────────────────────────────────────────────┘    │  │
│  │                                                            │  │
│  │ 4. Aggregate Results                                      │  │
│  │    → Execution successful                                 │  │
│  │    → Total assets: 6                                      │  │
│  └──────────────────────────────────────────────────────────┘  │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│                      USER SEES RESPONSE                          │
│  "You have 6 assets in the system:                              │
│   - 6 Windows workstations                                      │
│                                                                  │
│  ✅ ACTUAL COUNT PROVIDED                                       │
└─────────────────────────────────────────────────────────────────┘
```

---

## 🔀 Execution Flow Decision Tree

```
                        ┌─────────────────┐
                        │  Plan from      │
                        │  Stage C        │
                        └────────┬────────┘
                                 │
                                 ▼
                    ┌────────────────────────┐
                    │ Determine Execution    │
                    │ Mode                   │
                    └────────┬───────────────┘
                             │
                ┌────────────┴────────────┐
                │                         │
                ▼                         ▼
    ┌───────────────────┐     ┌──────────────────┐
    │ Estimated Time    │     │ Estimated Time   │
    │ < 30 seconds      │     │ > 30 seconds     │
    └────────┬──────────┘     └────────┬─────────┘
             │                         │
             ▼                         ▼
    ┌───────────────────┐     ┌──────────────────┐
    │ IMMEDIATE         │     │ BACKGROUND       │
    │ EXECUTION         │     │ EXECUTION        │
    │ (Phase 1)         │     │ (Phase 2)        │
    └────────┬──────────┘     └────────┬─────────┘
             │                         │
             ▼                         ▼
    ┌───────────────────┐     ┌──────────────────┐
    │ Check Approval    │     │ Queue Job        │
    │ Required?         │     │ Return Job ID    │
    └────────┬──────────┘     └────────┬─────────┘
             │                         │
      ┌──────┴──────┐                 │
      │             │                 ▼
      ▼             ▼         ┌──────────────────┐
┌──────────┐  ┌──────────┐   │ Background       │
│ No       │  │ Yes      │   │ Worker Executes  │
│ Approval │  │ Request  │   │ Async            │
└────┬─────┘  │ Approval │   └────────┬─────────┘
     │        └────┬─────┘            │
     │             │                  │
     │             ▼                  ▼
     │    ┌──────────────┐   ┌──────────────────┐
     │    │ User         │   │ WebSocket        │
     │    │ Approves?    │   │ Progress Updates │
     │    └────┬─────────┘   └────────┬─────────┘
     │         │                       │
     │    ┌────┴────┐                 │
     │    │         │                 │
     │    ▼         ▼                 │
     │  ┌───┐    ┌────┐              │
     │  │Yes│    │ No │              │
     │  └─┬─┘    └──┬─┘              │
     │    │         │                 │
     │    │         ▼                 │
     │    │   ┌──────────┐           │
     │    │   │ Cancel   │           │
     │    │   │ Return   │           │
     │    │   └──────────┘           │
     │    │                           │
     └────┴───────────┬───────────────┘
                      │
                      ▼
            ┌──────────────────┐
            │ Execute Steps    │
            │ Sequentially     │
            └────────┬─────────┘
                     │
                     ▼
            ┌──────────────────┐
            │ Aggregate        │
            │ Results          │
            └────────┬─────────┘
                     │
                     ▼
            ┌──────────────────┐
            │ Return to User   │
            └──────────────────┘
```

---

## 🎯 Request Complexity Routing

```
┌─────────────────────────────────────────────────────────────────┐
│                        USER REQUESTS                             │
└─────────────────────────────────────────────────────────────────┘
                             │
                ┌────────────┼────────────┐
                │            │            │
                ▼            ▼            ▼
        ┌───────────┐  ┌──────────┐  ┌──────────┐
        │  SIMPLE   │  │  MEDIUM  │  │ COMPLEX  │
        │  INFO     │  │  ACTION  │  │ WORKFLOW │
        └─────┬─────┘  └────┬─────┘  └────┬─────┘
              │             │             │
              │             │             │
┌─────────────┼─────────────┼─────────────┼─────────────┐
│             │             │             │             │
│  ┌──────────▼──────────┐  │             │             │
│  │ "How many assets?"  │  │             │             │
│  │ "Show server X"     │  │             │             │
│  └──────────┬──────────┘  │             │             │
│             │             │             │             │
│             ▼             │             │             │
│  ┌─────────────────────┐  │             │             │
│  │ Immediate Execution │  │             │             │
│  │ No Approval         │  │             │             │
│  │ < 5 seconds         │  │             │             │
│  └─────────┬───────────┘  │             │             │
│            │              │             │             │
│            ▼              │             │             │
│  ┌─────────────────────┐  │             │             │
│  │ ✅ Direct Result    │  │             │             │
│  │ "You have 6 assets" │  │             │             │
│  └─────────────────────┘  │             │             │
│                           │             │             │
│             ┌─────────────▼──────────┐  │             │
│             │ "Restart service X"    │  │             │
│             │ "Check disk space"     │  │             │
│             └─────────────┬──────────┘  │             │
│                           │             │             │
│                           ▼             │             │
│             ┌─────────────────────────┐ │             │
│             │ Show Plan + Confirm     │ │             │
│             │ Immediate Execution     │ │             │
│             │ 5-30 seconds            │ │             │
│             └─────────────┬───────────┘ │             │
│                           │             │             │
│                           ▼             │             │
│             ┌─────────────────────────┐ │             │
│             │ ✅ Execution Result     │ │             │
│             │ "Service restarted"     │ │             │
│             └─────────────────────────┘ │             │
│                                         │             │
│                           ┌─────────────▼──────────┐  │
│                           │ "Deploy application"   │  │
│                           │ "Full health check"    │  │
│                           └─────────────┬──────────┘  │
│                                         │             │
│                                         ▼             │
│                           ┌─────────────────────────┐ │
│                           │ Queue Background Job    │ │
│                           │ Multi-step Approval     │ │
│                           │ 30s - 10 minutes        │ │
│                           └─────────────┬───────────┘ │
│                                         │             │
│                                         ▼             │
│                           ┌─────────────────────────┐ │
│                           │ 🔄 Job ID + Status URL  │ │
│                           │ WebSocket Updates       │ │
│                           └─────────────────────────┘ │
│                                                       │
└───────────────────────────────────────────────────────┘
```

---

## 🏗️ Stage E Architecture (Phase 1)

```
┌─────────────────────────────────────────────────────────────────┐
│                         STAGE E: EXECUTOR                        │
│                                                                  │
│  ┌────────────────────────────────────────────────────────────┐ │
│  │                    executor.py                              │ │
│  │              Main Orchestrator                              │ │
│  │                                                              │ │
│  │  async def execute_plan(plan, decision, context)            │ │
│  └────────────────────────┬───────────────────────────────────┘ │
│                           │                                      │
│         ┌─────────────────┼─────────────────┐                  │
│         │                 │                 │                  │
│         ▼                 ▼                 ▼                  │
│  ┌─────────────┐  ┌──────────────┐  ┌─────────────────┐      │
│  │ approval_   │  │ execution_   │  │ result_         │      │
│  │ manager.py  │  │ engine.py    │  │ aggregator.py   │      │
│  └──────┬──────┘  └──────┬───────┘  └────────┬────────┘      │
│         │                │                    │                │
│         │                │                    │                │
│  ┌──────▼──────────────────────────────────────▼──────┐       │
│  │                                                      │       │
│  │  Approval Workflow:                                 │       │
│  │  ┌────────────────────────────────────────────┐    │       │
│  │  │ 1. Determine approval level                │    │       │
│  │  │ 2. Generate approval request               │    │       │
│  │  │ 3. Send to frontend                        │    │       │
│  │  │ 4. Wait for user response                  │    │       │
│  │  │ 5. Log approval decision                   │    │       │
│  │  └────────────────────────────────────────────┘    │       │
│  │                                                      │       │
│  └──────────────────────────────────────────────────────┘      │
│                                                                  │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │                                                           │  │
│  │  Execution Engine:                                       │  │
│  │  ┌────────────────────────────────────────────────┐     │  │
│  │  │ 1. Validate preconditions                      │     │  │
│  │  │ 2. Execute steps sequentially                  │     │  │
│  │  │ 3. Check success criteria                      │     │  │
│  │  │ 4. Handle failures                             │     │  │
│  │  │ 5. Track progress                              │     │  │
│  │  └────────────────────────────────────────────────┘     │  │
│  │                                                           │  │
│  │  Service Integrations:                                   │  │
│  │  ┌─────────────────┐  ┌──────────────────┐             │  │
│  │  │ asset-service   │  │ automation-      │             │  │
│  │  │ HTTP client     │  │ service client   │             │  │
│  │  └─────────────────┘  └──────────────────┘             │  │
│  │                                                           │  │
│  └──────────────────────────────────────────────────────────┘  │
│                                                                  │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │                                                           │  │
│  │  Result Aggregator:                                      │  │
│  │  ┌────────────────────────────────────────────────┐     │  │
│  │  │ 1. Collect step results                        │     │  │
│  │  │ 2. Calculate success/failure counts            │     │  │
│  │  │ 3. Format output data                          │     │  │
│  │  │ 4. Generate execution summary                  │     │  │
│  │  │ 5. Create ExecutionResultV1                    │     │  │
│  │  └────────────────────────────────────────────────┘     │  │
│  │                                                           │  │
│  └──────────────────────────────────────────────────────────┘  │
│                                                                  │
└─────────────────────────────┬────────────────────────────────────┘
                              │
                              ▼
                    ┌──────────────────┐
                    │ ExecutionResultV1│
                    │ (Schema)         │
                    └──────────────────┘
```

---

## 🔄 Phase 2: Background Execution Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                    STAGE E: EXECUTOR (Phase 2)                   │
│                                                                  │
│  ┌────────────────────────────────────────────────────────────┐ │
│  │                    executor.py                              │ │
│  │              Main Orchestrator                              │ │
│  └────────────────────────┬───────────────────────────────────┘ │
│                           │                                      │
│         ┌─────────────────┼─────────────────┐                  │
│         │                 │                 │                  │
│         ▼                 ▼                 ▼                  │
│  ┌─────────────┐  ┌──────────────┐  ┌─────────────────┐      │
│  │ immediate_  │  │ background_  │  │ job_tracker.py  │      │
│  │ executor.py │  │ executor.py  │  │                 │      │
│  └──────┬──────┘  └──────┬───────┘  └────────┬────────┘      │
│         │                │                    │                │
│         │                │                    │                │
│         │                ▼                    │                │
│         │       ┌─────────────────┐           │                │
│         │       │  job_queue.py   │           │                │
│         │       │  (Redis-based)  │           │                │
│         │       └────────┬────────┘           │                │
│         │                │                    │                │
│         │                ▼                    │                │
│         │       ┌─────────────────┐           │                │
│         │       │ Background      │           │                │
│         │       │ Worker Pool     │           │                │
│         │       └────────┬────────┘           │                │
│         │                │                    │                │
│         │                └────────────────────┘                │
│         │                                                       │
│         └───────────────────┬───────────────────────────────────┘
│                             │
│                             ▼
│  ┌──────────────────────────────────────────────────────────┐  │
│  │              Execution Strategies                         │  │
│  │                                                            │  │
│  │  ┌──────────────┐  ┌────────────────┐  ┌──────────────┐ │  │
│  │  │ simple_      │  │ sequential_    │  │ parallel_    │ │  │
│  │  │ execution.py │  │ execution.py   │  │ execution.py │ │  │
│  │  └──────────────┘  └────────────────┘  └──────────────┘ │  │
│  │                                                            │  │
│  └──────────────────────────────────────────────────────────┘  │
│                                                                  │
└─────────────────────────────┬────────────────────────────────────┘
                              │
                              ▼
                    ┌──────────────────┐
                    │ WebSocket        │
                    │ Progress Updates │
                    └──────────────────┘
```

---

## 📊 Data Flow: Simple Query Example

```
User: "How many assets do we have?"
│
├─► Stage A: Classify
│   └─► Intent: information/asset_count
│       Confidence: 0.95
│
├─► Stage B: Select Tools
│   └─► Tools: ["asset-service-query"]
│       Risk: LOW
│       Approval: false
│
├─► Stage C: Create Plan
│   └─► Step 1: Query asset-service
│       Tool: asset-service-query
│       Inputs: {query_type: "count"}
│       Duration: 2s
│
├─► Stage D: Generate Response Template
│   └─► Response: "I'll gather the total number..."
│
├─► Stage E: EXECUTE (NEW!)
│   │
│   ├─► 1. Assess Mode
│   │   └─► Immediate (2s < 30s threshold)
│   │
│   ├─► 2. Check Approval
│   │   └─► Not required (LOW risk, read-only)
│   │
│   ├─► 3. Execute Steps
│   │   │
│   │   └─► Step 1: Query asset-service
│   │       │
│   │       ├─► HTTP POST http://asset-service:3001/query
│   │       │   Body: {
│   │       │     "query_type": "count",
│   │       │     "filters": {}
│   │       │   }
│   │       │
│   │       ├─► Response: {
│   │       │     "success": true,
│   │       │     "total_count": 6,
│   │       │     "breakdown": {
│   │       │       "windows_workstation": 6
│   │       │     }
│   │       │   }
│   │       │
│   │       └─► Status: ✅ SUCCESS
│   │           Duration: 1.2s
│   │
│   └─► 4. Aggregate Results
│       └─► ExecutionResultV1 {
│             execution_id: "exec_123",
│             status: "completed",
│             output: {
│               total_count: 6,
│               breakdown: {...}
│             }
│           }
│
└─► Return to User
    └─► "You have 6 assets in the system:
         - 6 Windows workstations"
```

---

## 🔐 Approval Flow Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│                    APPROVAL DECISION TREE                        │
└─────────────────────────────────────────────────────────────────┘
                             │
                             ▼
                    ┌────────────────┐
                    │ Check Risk     │
                    │ Level          │
                    └────────┬───────┘
                             │
                ┌────────────┼────────────┐
                │            │            │
                ▼            ▼            ▼
        ┌───────────┐  ┌──────────┐  ┌──────────┐
        │  LOW      │  │  MEDIUM  │  │  HIGH    │
        │  RISK     │  │  RISK    │  │  RISK    │
        └─────┬─────┘  └────┬─────┘  └────┬─────┘
              │             │             │
              ▼             ▼             ▼
     ┌────────────────┐ ┌──────────────┐ ┌──────────────┐
     │ Level 0:       │ │ Level 1:     │ │ Level 2:     │
     │ NO APPROVAL    │ │ CONFIRMATION │ │ PLAN REVIEW  │
     │                │ │              │ │              │
     │ Auto-execute   │ │ Show plan    │ │ Show full    │
     │ immediately    │ │ Ask confirm  │ │ plan details │
     │                │ │              │ │ Multi-step   │
     │ Examples:      │ │ Examples:    │ │ approval     │
     │ - Info queries │ │ - Restart    │ │              │
     │ - Status check │ │ - Config     │ │ Examples:    │
     │                │ │   update     │ │ - Deploy     │
     │                │ │              │ │ - Delete DB  │
     └────────┬───────┘ └──────┬───────┘ └──────┬───────┘
              │                │                │
              │                ▼                │
              │       ┌─────────────────┐       │
              │       │ Frontend Dialog │       │
              │       │                 │       │
              │       │ ┌─────────────┐ │       │
              │       │ │ Plan:       │ │       │
              │       │ │ - Step 1... │ │       │
              │       │ │ - Step 2... │ │       │
              │       │ │             │ │       │
              │       │ │ Risk: MED   │ │       │
              │       │ │ Time: 15s   │ │       │
              │       │ │             │ │       │
              │       │ │ [Approve]   │ │       │
              │       │ │ [Cancel]    │ │       │
              │       │ └─────────────┘ │       │
              │       └────────┬────────┘       │
              │                │                │
              │         ┌──────┴──────┐         │
              │         │             │         │
              │         ▼             ▼         │
              │    ┌─────────┐  ┌─────────┐    │
              │    │Approved │  │Cancelled│    │
              │    └────┬────┘  └────┬────┘    │
              │         │            │         │
              └─────────┼────────────┘         │
                        │                      │
                        └──────────┬───────────┘
                                   │
                                   ▼
                          ┌─────────────────┐
                          │ Execute Plan    │
                          │ (Stage E)       │
                          └─────────────────┘
```

---

## 🎨 Frontend Integration Flow

```
┌─────────────────────────────────────────────────────────────────┐
│                        FRONTEND (React)                          │
└─────────────────────────────────────────────────────────────────┘
                             │
                             │ User types query
                             ▼
                    ┌────────────────┐
                    │ Chat Input     │
                    │ Component      │
                    └────────┬───────┘
                             │
                             │ POST /pipeline
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│                    BACKEND (Pipeline API)                        │
│                                                                  │
│  Stages A → B → C → D → E                                       │
│                         │                                        │
│                         └─► Execution Result                    │
└─────────────────────────────┬───────────────────────────────────┘
                              │
                              │ Response
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                        FRONTEND                                  │
│                                                                  │
│  ┌────────────────────────────────────────────────────────────┐ │
│  │ Response Handler                                            │ │
│  │                                                              │ │
│  │ if (response.requires_approval) {                           │ │
│  │   // Show approval dialog                                   │ │
│  │   showApprovalDialog(response.plan);                        │ │
│  │                                                              │ │
│  │   if (userApproves) {                                       │ │
│  │     // Execute with approval                                │ │
│  │     POST /pipeline/execute                                  │ │
│  │   }                                                          │ │
│  │ } else if (response.execution_result) {                     │ │
│  │   // Show execution results                                 │ │
│  │   displayResults(response.execution_result);                │ │
│  │ } else {                                                     │ │
│  │   // Show response text                                     │ │
│  │   displayMessage(response.message);                         │ │
│  │ }                                                            │ │
│  └────────────────────────────────────────────────────────────┘ │
│                                                                  │
│  ┌────────────────────────────────────────────────────────────┐ │
│  │ Approval Dialog Component                                   │ │
│  │                                                              │ │
│  │  ┌──────────────────────────────────────────────────────┐  │ │
│  │  │ Execution Plan                                        │  │ │
│  │  │                                                        │  │ │
│  │  │ Steps:                                                │  │ │
│  │  │ 1. Query asset-service for count                     │  │ │
│  │  │    Tool: asset-service-query                         │  │ │
│  │  │    Duration: ~2s                                      │  │ │
│  │  │                                                        │  │ │
│  │  │ Risk Level: LOW                                       │  │ │
│  │  │ Estimated Time: 2 seconds                            │  │ │
│  │  │                                                        │  │ │
│  │  │ [Approve & Execute]  [Cancel]                        │  │ │
│  │  └──────────────────────────────────────────────────────┘  │ │
│  └────────────────────────────────────────────────────────────┘ │
│                                                                  │
│  ┌────────────────────────────────────────────────────────────┐ │
│  │ Results Display Component                                   │ │
│  │                                                              │ │
│  │  ┌──────────────────────────────────────────────────────┐  │ │
│  │  │ Execution Results                                     │  │ │
│  │  │                                                        │  │ │
│  │  │ ✅ Completed in 1.2s                                  │  │ │
│  │  │                                                        │  │ │
│  │  │ You have 6 assets in the system:                     │  │ │
│  │  │ - 6 Windows workstations                             │  │ │
│  │  │                                                        │  │ │
│  │  │ [View Details]  [Export]                             │  │ │
│  │  └──────────────────────────────────────────────────────┘  │ │
│  └────────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────┘
```

---

## 📈 Scalability: Phase 1 vs Phase 2

### Phase 1: Immediate Execution Only

```
┌──────────────┐
│ User Request │
└──────┬───────┘
       │
       ▼
┌──────────────┐
│ Pipeline     │
│ (A→B→C→D→E)  │
└──────┬───────┘
       │
       │ Synchronous
       │ (Blocks until complete)
       │
       ▼
┌──────────────┐
│ Service Call │
│ (HTTP)       │
└──────┬───────┘
       │
       │ < 30 seconds
       │
       ▼
┌──────────────┐
│ Results      │
└──────────────┘

Limitations:
- ❌ Blocks for long operations
- ❌ No parallel execution
- ❌ Single request at a time
- ✅ Simple and predictable
```

### Phase 2: Background + Queue

```
┌──────────────┐
│ User Request │
└──────┬───────┘
       │
       ▼
┌──────────────┐
│ Pipeline     │
│ (A→B→C→D→E)  │
└──────┬───────┘
       │
       ├─────────────┬─────────────┐
       │             │             │
       ▼             ▼             ▼
┌──────────┐  ┌──────────┐  ┌──────────┐
│Immediate │  │Background│  │Background│
│Execution │  │Job Queue │  │Job Queue │
└────┬─────┘  └────┬─────┘  └────┬─────┘
     │             │             │
     │             ▼             ▼
     │      ┌──────────┐  ┌──────────┐
     │      │ Worker 1 │  │ Worker 2 │
     │      └────┬─────┘  └────┬─────┘
     │           │             │
     │           ▼             ▼
     │      ┌──────────┐  ┌──────────┐
     │      │Service   │  │Service   │
     │      │Calls     │  │Calls     │
     │      └────┬─────┘  └────┬─────┘
     │           │             │
     └───────────┴─────────────┘
                 │
                 ▼
          ┌──────────────┐
          │ Results      │
          │ Aggregation  │
          └──────────────┘

Benefits:
- ✅ Non-blocking for long ops
- ✅ Parallel execution
- ✅ Multiple concurrent requests
- ✅ Scalable worker pool
```

---

**Document Version**: 1.0  
**Date**: 2025-01-XX  
**Companion to**: EXECUTION_ARCHITECTURE_PROPOSAL.md