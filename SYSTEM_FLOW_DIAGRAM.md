# OpsConductor System Flow - Visual Guide

## The Complete Picture

```
┌─────────────────────────────────────────────────────────────────────┐
│                         USER ASKS QUESTION                          │
│              "How many Windows assets do we have?"                  │
└────────────────────────────┬────────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────────┐
│                         STAGE A: CLASSIFIER                         │
│                                                                     │
│  ┌──────────────────────────────────────────────────────────────┐ │
│  │ LLM analyzes the question and extracts:                      │ │
│  │                                                               │ │
│  │ • Category: "asset_management"                                │ │
│  │ • Action: "count_assets"                                      │ │
│  │ • Entities: {"os": "windows"}                                 │ │
│  │ • Capabilities: ["asset_management"] ← CRITICAL!              │ │
│  │ • Confidence: 0.95                                            │ │
│  │ • Risk: "low"                                                 │ │
│  └──────────────────────────────────────────────────────────────┘ │
│                                                                     │
│  Output: DecisionV1 object                                          │
└────────────────────────────┬────────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────────┐
│                         STAGE B: SELECTOR                           │
│                                                                     │
│  Step 1: Extract capabilities from DecisionV1                       │
│  ┌──────────────────────────────────────────────────────────────┐ │
│  │ required_capabilities = ["asset_management"]                  │ │
│  └──────────────────────────────────────────────────────────────┘ │
│                             │                                       │
│                             ▼                                       │
│  Step 2: Query Database for matching tools                          │
│  ┌──────────────────────────────────────────────────────────────┐ │
│  │ SELECT * FROM tool_catalog.tools t                            │ │
│  │ JOIN tool_catalog.tool_capabilities c ON t.id = c.tool_id     │ │
│  │ WHERE c.capability_name = 'asset_management'                  │ │
│  └──────────────────────────────────────────────────────────────┘ │
│                             │                                       │
│                             ▼                                       │
│  Step 3: Database returns matching tools                            │
│  ┌──────────────────────────────────────────────────────────────┐ │
│  │ [                                                             │ │
│  │   {                                                           │ │
│  │     "tool_name": "asset-query",                               │ │
│  │     "capability": "asset_management",                         │ │
│  │     "pattern": "execute",                                     │ │
│  │     "time_estimate_ms": 500,                                  │ │
│  │     "cost_estimate": 1,                                       │ │
│  │     "typical_use_cases": [                                    │ │
│  │       "count assets",                                         │ │
│  │       "list assets",                                          │ │
│  │       "query asset inventory"                                 │ │
│  │     ]                                                         │ │
│  │   }                                                           │ │
│  │ ]                                                             │ │
│  └──────────────────────────────────────────────────────────────┘ │
│                             │                                       │
│                             ▼                                       │
│  Step 4: HybridOrchestrator scores and selects best tool            │
│  ┌──────────────────────────────────────────────────────────────┐ │
│  │ • Preference detection: "balanced"                            │ │
│  │ • Candidate enumeration: 1 candidate                          │ │
│  │ • Policy enforcement: PASS (production_safe=true)             │ │
│  │ • Deterministic scoring: score=0.85                           │ │
│  │ • Selected: asset-query                                       │ │
│  └──────────────────────────────────────────────────────────────┘ │
│                                                                     │
│  Output: SelectionV1 with selected_tools=["asset-query"]            │
└────────────────────────────┬────────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────────┐
│                         STAGE C: PLANNER                            │
│                                                                     │
│  Creates execution plan:                                            │
│  ┌──────────────────────────────────────────────────────────────┐ │
│  │ Step 1: Call asset-query API                                  │ │
│  │   - Endpoint: GET /api/assets                                 │ │
│  │   - Filter: os=windows                                        │ │
│  │   - Expected time: 500ms                                      │ │
│  │                                                               │ │
│  │ Step 2: Count results                                         │ │
│  │   - Total assets                                              │ │
│  │   - Windows assets                                            │ │
│  │                                                               │ │
│  │ Step 3: Format response                                       │ │
│  │   - Human-readable summary                                    │ │
│  └──────────────────────────────────────────────────────────────┘ │
│                                                                     │
│  Output: PlanV1 with execution steps                                │
└────────────────────────────┬────────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────────┐
│                         STAGE D: ANSWERER                           │
│                                                                     │
│  Step 1: Execute the plan                                           │
│  ┌──────────────────────────────────────────────────────────────┐ │
│  │ Calling: GET /api/assets?os=windows                           │ │
│  │ Response: [                                                   │ │
│  │   {"id": 1, "name": "server-01", "os": "windows"},            │ │
│  │   {"id": 2, "name": "server-02", "os": "windows"},            │ │
│  │   ... (23 total Windows assets)                               │ │
│  │ ]                                                             │ │
│  │                                                               │ │
│  │ Total assets: 47                                              │ │
│  │ Windows assets: 23                                            │ │
│  └──────────────────────────────────────────────────────────────┘ │
│                             │                                       │
│                             ▼                                       │
│  Step 2: Format response with LLM                                   │
│  ┌──────────────────────────────────────────────────────────────┐ │
│  │ LLM receives:                                                 │ │
│  │ • Original question                                           │ │
│  │ • Execution results (REAL DATA)                               │ │
│  │ • Context                                                     │ │
│  │                                                               │ │
│  │ LLM generates:                                                │ │
│  │ "You have a total of 47 assets. Out of these, 23 are         │ │
│  │  running Windows OS."                                         │ │
│  └──────────────────────────────────────────────────────────────┘ │
│                                                                     │
│  Output: AnswerV1 with formatted response                           │
└────────────────────────────┬────────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────────┐
│                         USER SEES ANSWER                            │
│     "You have a total of 47 assets. 23 are running Windows OS."    │
└─────────────────────────────────────────────────────────────────────┘
```

---

## The Tool Database Structure

```
PostgreSQL Database: opsconductor
│
└── Schema: tool_catalog
    │
    ├── Table: tools
    │   ├── id (primary key)
    │   ├── tool_name          "asset-query"
    │   ├── version            "1.0"
    │   ├── description        "Query asset inventory"
    │   ├── platform           "custom"
    │   ├── category           "asset"
    │   ├── defaults           {...}
    │   ├── dependencies       [...]
    │   ├── metadata           {...}
    │   ├── enabled            true
    │   ├── is_latest          true
    │   └── status             "active"
    │
    ├── Table: tool_capabilities
    │   ├── id (primary key)
    │   ├── tool_id            → tools.id
    │   ├── capability_name    "asset_management"
    │   └── description        "Query and manage asset inventory"
    │
    └── Table: tool_patterns
        ├── id (primary key)
        ├── capability_id      → tool_capabilities.id
        ├── pattern_name       "execute"
        ├── description        "Execute asset-query command"
        ├── typical_use_cases  ["count assets", "list assets", ...]
        ├── time_estimate_ms   500
        ├── cost_estimate      1
        ├── complexity_score   0.2
        ├── scope              "single_item"
        ├── completeness       "complete"
        ├── policy             {...}
        ├── preference_match   {...}
        ├── required_inputs    [...]
        └── expected_outputs   [...]
```

---

## How Tools Get Into Database

```
┌─────────────────────────────────────────────────────────────────────┐
│                    TOOL DEFINITION (YAML FILE)                      │
│                                                                     │
│  File: pipeline/config/tools/custom/asset_query.yaml                │
│  ┌──────────────────────────────────────────────────────────────┐ │
│  │ tool_name: asset-query                                        │ │
│  │ version: '1.0'                                                │ │
│  │ description: Query asset inventory                            │ │
│  │ platform: custom                                              │ │
│  │ category: asset                                               │ │
│  │                                                               │ │
│  │ capabilities:                                                 │ │
│  │   asset_management:                                           │ │
│  │     description: Query and manage asset inventory             │ │
│  │     patterns:                                                 │ │
│  │       execute:                                                │ │
│  │         typical_use_cases:                                    │ │
│  │           - "count assets"                                    │ │
│  │           - "list assets"                                     │ │
│  │         time_estimate_ms: 500                                 │ │
│  │         cost_estimate: 1                                      │ │
│  └──────────────────────────────────────────────────────────────┘ │
└────────────────────────────┬────────────────────────────────────────┘
                             │
                             │ python3 scripts/migrate_tools_to_db.py
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────────┐
│                      MIGRATION SCRIPT                               │
│                                                                     │
│  ┌──────────────────────────────────────────────────────────────┐ │
│  │ 1. Read YAML file                                             │ │
│  │ 2. Validate structure                                         │ │
│  │ 3. Parse capabilities and patterns                            │ │
│  │ 4. Insert into database:                                      │ │
│  │    - INSERT INTO tools (...)                                  │ │
│  │    - INSERT INTO tool_capabilities (...)                      │ │
│  │    - INSERT INTO tool_patterns (...)                          │ │
│  │ 5. Commit transaction                                         │ │
│  └──────────────────────────────────────────────────────────────┘ │
└────────────────────────────┬────────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────────┐
│                      POSTGRESQL DATABASE                            │
│                                                                     │
│  Tool is now available for AI to query and use!                     │
│                                                                     │
│  ┌──────────────────────────────────────────────────────────────┐ │
│  │ tools table:                                                  │ │
│  │   id=1, tool_name='asset-query', platform='custom'            │ │
│  │                                                               │ │
│  │ tool_capabilities table:                                      │ │
│  │   id=1, tool_id=1, capability_name='asset_management'         │ │
│  │                                                               │ │
│  │ tool_patterns table:                                          │ │
│  │   id=1, capability_id=1, pattern_name='execute'               │ │
│  │   typical_use_cases=['count assets', 'list assets']           │ │
│  └──────────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────────┘
```

---

## The Current Problem (Visualized)

### **What's Happening Now (BROKEN):**

```
User: "How many assets?"
    ↓
Stage A: 
    category = "asset_management" ✅
    capabilities = []  ❌ EMPTY!
    ↓
Stage B:
    if capabilities == []:
        return "information_only" ❌
    (skips database query)
    (skips tool selection)
    ↓
Stage C:
    (skipped - no tools)
    ↓
Stage D:
    No tools to execute ❌
    LLM makes up answer: "You have 25 assets" ❌
    ↓
User sees: HALLUCINATED DATA ❌
```

### **What Should Happen (FIXED):**

```
User: "How many assets?"
    ↓
Stage A: 
    category = "asset_management" ✅
    capabilities = ["asset_management"] ✅
    ↓
Stage B:
    Query database for "asset_management" capability ✅
    Find: asset-query tool ✅
    Select: asset-query ✅
    ↓
Stage C:
    Plan: Call asset-query API ✅
    ↓
Stage D:
    Execute: GET /api/assets ✅
    Get REAL data: 47 assets ✅
    Format: "You have 47 assets" ✅
    ↓
User sees: REAL DATA ✅
```

---

## The Three Fixes

### **Fix 1: Stage A Prompt Enhancement**

```
┌─────────────────────────────────────────────────────────────────────┐
│                         STAGE A PROMPT                              │
│                                                                     │
│  OLD PROMPT:                                                        │
│  ┌──────────────────────────────────────────────────────────────┐ │
│  │ "Extract capabilities from the user's request"                │ │
│  │ (LLM sometimes returns empty list)                            │ │
│  └──────────────────────────────────────────────────────────────┘ │
│                                                                     │
│  NEW PROMPT:                                                        │
│  ┌──────────────────────────────────────────────────────────────┐ │
│  │ "Extract capabilities from the user's request"                │ │
│  │                                                               │ │
│  │ RULES:                                                        │ │
│  │ - If user asks about assets → ["asset_management"]            │ │
│  │ - If user asks about services → ["service_management"]        │ │
│  │ - If user asks about disk → ["disk_management"]               │ │
│  │ - If user asks about network → ["network_diagnostics"]        │ │
│  │                                                               │ │
│  │ NEVER return empty capabilities for data questions!           │ │
│  └──────────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────────┘
```

### **Fix 2: Stage B Safety Net**

```
┌─────────────────────────────────────────────────────────────────────┐
│                         STAGE B SELECTOR                            │
│                                                                     │
│  Step 1: Extract capabilities                                       │
│  ┌──────────────────────────────────────────────────────────────┐ │
│  │ required_capabilities = decision.capabilities                 │ │
│  └──────────────────────────────────────────────────────────────┘ │
│                             │                                       │
│                             ▼                                       │
│  NEW: Safety net validation                                         │
│  ┌──────────────────────────────────────────────────────────────┐ │
│  │ if decision.category == "asset_management" and                │ │
│  │    not required_capabilities:                                 │ │
│  │     # Force the capability                                    │ │
│  │     required_capabilities = ["asset_management"]              │ │
│  │     logger.warning("Forced asset_management capability")      │ │
│  └──────────────────────────────────────────────────────────────┘ │
│                             │                                       │
│                             ▼                                       │
│  Step 2: Query database (now has capabilities!)                     │
└─────────────────────────────────────────────────────────────────────┘
```

### **Fix 3: Remove Fast Path**

```
┌─────────────────────────────────────────────────────────────────────┐
│                         STAGE D ANSWERER                            │
│                                                                     │
│  OLD CODE:                                                          │
│  ┌──────────────────────────────────────────────────────────────┐ │
│  │ if no tools selected:                                         │ │
│  │     # Fast path - try to answer without tools                 │ │
│  │     return _generate_direct_information_response()            │ │
│  │     # ↑ This can hallucinate!                                 │ │
│  └──────────────────────────────────────────────────────────────┘ │
│                                                                     │
│  NEW CODE:                                                          │
│  ┌──────────────────────────────────────────────────────────────┐ │
│  │ if no tools selected:                                         │ │
│  │     # No fast path - require tools for data questions         │ │
│  │     if is_data_question(request):                             │ │
│  │         return "I need to query the system for that data,     │ │
│  │                 but no tools were selected. Please rephrase." │ │
│  │     else:                                                     │ │
│  │         # OK for general knowledge questions                  │ │
│  │         return llm_answer()                                   │ │
│  └──────────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────────┘
```

---

## Data Flow Summary

```
YAML Files → Migration Script → PostgreSQL Database
                                        ↓
User Question → Stage A (Extract Capabilities)
                                        ↓
                Stage B (Query Database for Tools)
                                        ↓
                Stage C (Plan Execution)
                                        ↓
                Stage D (Execute & Format)
                                        ↓
                User Gets Answer
```

---

## Key Takeaways

1. **Tools live in YAML files** → imported to database
2. **Capabilities are the bridge** between user questions and tools
3. **Stage A must extract capabilities** or the whole system fails
4. **Stage B queries database** to find matching tools
5. **Stage D executes tools** and formats results
6. **No tools = potential hallucination** (current problem)

---

## Next Steps

1. **Fix Stage A** - Ensure it extracts capabilities
2. **Add Stage B safety net** - Catch missed capabilities
3. **Remove Stage D fast path** - Prevent hallucinations
4. **Test with asset queries** - Verify it works
5. **Add more tools** - Now you know how!

---

Ready to implement these fixes? Say the word and I'll make the changes.