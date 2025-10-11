# Stage AB v3.1 - Flow Diagrams

## Complete Pipeline Flow

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         USER REQUEST RECEIVED                                │
│                  "list all files on 192.168.50.211"                         │
└─────────────────────────────────────────────────────────────────────────────┘
                                      │
                                      ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│  STEP 1: EARLY ENTITY EXTRACTION (NEW!)                                     │
│  ─────────────────────────────────────────────────────────────────────────  │
│  • Quick LLM call to extract entities                                       │
│  • Extracts: hostnames, IPs, services, paths, ports                         │
│  • Result: [{"type": "ip_address", "value": "192.168.50.211"}]             │
└─────────────────────────────────────────────────────────────────────────────┘
                                      │
                                      ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│  STEP 2: ASSET ENRICHMENT (NEW!)                                            │
│  ─────────────────────────────────────────────────────────────────────────  │
│  • Query asset-service: GET /assets?search=192.168.50.211                  │
│  • Returns: {                                                                │
│      "id": 42,                                                               │
│      "name": "web-server-prod",                                             │
│      "os_type": "windows",                                                  │
│      "os_version": "Windows Server 2022",                                   │
│      "credentials": {...}                                                    │
│    }                                                                         │
└─────────────────────────────────────────────────────────────────────────────┘
                                      │
                                      ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│  STEP 3: PLATFORM DETECTION (NEW!)                                          │
│  ─────────────────────────────────────────────────────────────────────────  │
│  • Normalize OS type: "windows" → platform_filter = "windows"              │
│  • Store in context for downstream stages                                   │
└─────────────────────────────────────────────────────────────────────────────┘
                                      │
                                      ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│  STEP 4: GENERATE QUERY EMBEDDING                                           │
│  ─────────────────────────────────────────────────────────────────────────  │
│  • Embed user request: "list all files on 192.168.50.211"                  │
│  • Result: [0.123, -0.456, 0.789, ...] (384-dim vector)                    │
└─────────────────────────────────────────────────────────────────────────────┘
                                      │
                                      ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│  STEP 5: SEMANTIC RETRIEVAL (WITH PLATFORM FILTER!)                         │
│  ─────────────────────────────────────────────────────────────────────────  │
│  • Query: SELECT * FROM tool_index                                          │
│           WHERE (platform = 'windows' OR platform = 'multi-platform')       │
│           ORDER BY emb <=> query_embedding                                  │
│           LIMIT 50                                                           │
│  • Result: [Get-ChildItem, powershell, asset-query, ...]                   │
│  • ✅ ONLY Windows-compatible tools!                                        │
└─────────────────────────────────────────────────────────────────────────────┘
                                      │
                                      ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│  STEP 6: APPLY TOKEN BUDGET                                                 │
│  ─────────────────────────────────────────────────────────────────────────  │
│  • Calculate: 50 tools × 100 tokens/tool = 5,000 tokens                    │
│  • Budget: 10,000 tokens available                                          │
│  • Headroom: 50% remaining                                                  │
└─────────────────────────────────────────────────────────────────────────────┘
                                      │
                                      ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│  STEP 7: LLM TOOL SELECTION                                                 │
│  ─────────────────────────────────────────────────────────────────────────  │
│  • Send minimal index to LLM (id, name, desc, tags, platform, cost)        │
│  • LLM selects: [{"id": "get-childitem", "why": "lists files"}]            │
└─────────────────────────────────────────────────────────────────────────────┘
                                      │
                                      ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│  STEP 8: VALIDATE & BUILD EXECUTION POLICY                                  │
│  ─────────────────────────────────────────────────────────────────────────  │
│  • Validate tool IDs exist                                                  │
│  • Build execution policy (risk, approval, etc.)                            │
│  • Check for missing inputs                                                 │
└─────────────────────────────────────────────────────────────────────────────┘
                                      │
                                      ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│  STEP 9: RETURN SELECTION                                                   │
│  ─────────────────────────────────────────────────────────────────────────  │
│  • SelectionV1 with:                                                        │
│    - selected_tools: [Get-ChildItem]                                        │
│    - platform: "windows"                                                    │
│    - asset_metadata: {...}                                                  │
│    - ready_for_execution: true                                              │
│    - next_stage: "stage_c"                                                  │
└─────────────────────────────────────────────────────────────────────────────┘
```

## Scenario Comparison

### Scenario A: Explicit Target (Success)

```
┌──────────────────────────────────────────────────────────────┐
│ USER: "list files on 192.168.50.211"                         │
└──────────────────────────────────────────────────────────────┘
                    │
                    ▼
┌──────────────────────────────────────────────────────────────┐
│ ENTITY EXTRACTION                                             │
│ Found: [{"type": "ip_address", "value": "192.168.50.211"}]  │
└──────────────────────────────────────────────────────────────┘
                    │
                    ▼
┌──────────────────────────────────────────────────────────────┐
│ ASSET LOOKUP                                                  │
│ Query: search_assets("192.168.50.211")                       │
│ Result: ✅ Found 1 asset (Windows Server 2022)              │
└──────────────────────────────────────────────────────────────┘
                    │
                    ▼
┌──────────────────────────────────────────────────────────────┐
│ PLATFORM DETECTION                                            │
│ platform_filter = "windows"                                   │
│ missing_target_info = False                                   │
└──────────────────────────────────────────────────────────────┘
                    │
                    ▼
┌──────────────────────────────────────────────────────────────┐
│ TOOL RETRIEVAL                                                │
│ WHERE platform = 'windows' OR platform = 'multi-platform'    │
│ Result: [Get-ChildItem, powershell, asset-query]            │
└──────────────────────────────────────────────────────────────┘
                    │
                    ▼
┌──────────────────────────────────────────────────────────────┐
│ SELECTION                                                     │
│ selected_tools: [Get-ChildItem]                              │
│ additional_inputs_needed: []                                  │
│ ready_for_execution: ✅ TRUE                                 │
└──────────────────────────────────────────────────────────────┘
```

### Scenario B: Ambiguous Target (Needs Clarification)

```
┌──────────────────────────────────────────────────────────────┐
│ USER: "list files in the current directory"                  │
└──────────────────────────────────────────────────────────────┘
                    │
                    ▼
┌──────────────────────────────────────────────────────────────┐
│ ENTITY EXTRACTION                                             │
│ Found: [] (no entities)                                       │
└──────────────────────────────────────────────────────────────┘
                    │
                    ▼
┌──────────────────────────────────────────────────────────────┐
│ AMBIGUITY DETECTION                                           │
│ Keywords found: "current directory"                           │
│ Result: ⚠️ Ambiguous target detected                         │
└──────────────────────────────────────────────────────────────┘
                    │
                    ▼
┌──────────────────────────────────────────────────────────────┐
│ PLATFORM DETECTION                                            │
│ platform_filter = None                                        │
│ missing_target_info = True ⚠️                                │
└──────────────────────────────────────────────────────────────┘
                    │
                    ▼
┌──────────────────────────────────────────────────────────────┐
│ TOOL RETRIEVAL                                                │
│ No platform filter (retrieves all platforms)                 │
│ Result: [ls, cat, Get-ChildItem, powershell, ...]           │
└──────────────────────────────────────────────────────────────┘
                    │
                    ▼
┌──────────────────────────────────────────────────────────────┐
│ SELECTION                                                     │
│ selected_tools: [ls, Get-ChildItem] (both platforms!)        │
│ additional_inputs_needed: ["target_asset"] ⚠️               │
│ ready_for_execution: ❌ FALSE                                │
└──────────────────────────────────────────────────────────────┘
                    │
                    ▼
┌──────────────────────────────────────────────────────────────┐
│ AI PROMPTS USER                                               │
│ "Which system would you like to list files on?"              │
│ Options: [list of available assets]                          │
└──────────────────────────────────────────────────────────────┘
```

### Scenario C: Context from Previous (Success)

```
┌──────────────────────────────────────────────────────────────┐
│ PREVIOUS: "connect to server-prod-01"                        │
│ Context stored: current_asset = {id: 1, os_type: "windows"} │
└──────────────────────────────────────────────────────────────┘
                    │
                    ▼
┌──────────────────────────────────────────────────────────────┐
│ USER: "list files in the current directory"                  │
└──────────────────────────────────────────────────────────────┘
                    │
                    ▼
┌──────────────────────────────────────────────────────────────┐
│ ENTITY EXTRACTION                                             │
│ Found: [] (no entities)                                       │
└──────────────────────────────────────────────────────────────┘
                    │
                    ▼
┌──────────────────────────────────────────────────────────────┐
│ CONTEXT CHECK                                                 │
│ Found: context["current_asset"] = {id: 1, os_type: "windows"}│
│ Result: ✅ Use current asset from context                    │
└──────────────────────────────────────────────────────────────┘
                    │
                    ▼
┌──────────────────────────────────────────────────────────────┐
│ PLATFORM DETECTION                                            │
│ platform_filter = "windows" (from context)                    │
│ missing_target_info = False                                   │
└──────────────────────────────────────────────────────────────┘
                    │
                    ▼
┌──────────────────────────────────────────────────────────────┐
│ TOOL RETRIEVAL                                                │
│ WHERE platform = 'windows' OR platform = 'multi-platform'    │
│ Result: [Get-ChildItem, powershell, asset-query]            │
└──────────────────────────────────────────────────────────────┘
                    │
                    ▼
┌──────────────────────────────────────────────────────────────┐
│ SELECTION                                                     │
│ selected_tools: [Get-ChildItem]                              │
│ additional_inputs_needed: []                                  │
│ ready_for_execution: ✅ TRUE                                 │
└──────────────────────────────────────────────────────────────┘
```

## Decision Tree

```
                    ┌─────────────────────┐
                    │  User Request       │
                    └──────────┬──────────┘
                               │
                               ▼
                    ┌─────────────────────┐
                    │ Extract Entities    │
                    └──────────┬──────────┘
                               │
                ┌──────────────┴──────────────┐
                │                             │
                ▼                             ▼
    ┌───────────────────┐         ┌───────────────────┐
    │ Entities Found?   │         │ Context Has       │
    │ (hostname/IP)     │         │ current_asset?    │
    └────────┬──────────┘         └────────┬──────────┘
             │                              │
        YES  │  NO                     YES  │  NO
             │                              │
             ▼                              ▼
    ┌───────────────────┐         ┌───────────────────┐
    │ Query Asset       │         │ Ambiguous         │
    │ Service           │         │ Keywords?         │
    └────────┬──────────┘         └────────┬──────────┘
             │                              │
    ┌────────┴────────┐              YES   │   NO
    │                 │                    │
    ▼                 ▼                    ▼
┌────────┐      ┌────────┐         ┌─────────────┐
│ Found  │      │ Not    │         │ Set         │
│ Asset  │      │ Found  │         │ missing_    │
└───┬────┘      └───┬────┘         │ target_info │
    │               │              └──────┬──────┘
    ▼               ▼                     │
┌────────┐      ┌────────┐               │
│ Set    │      │ No     │               │
│ platform│     │ platform│              │
│ filter │      │ filter │               │
└───┬────┘      └───┬────┘               │
    │               │                    │
    └───────┬───────┴────────────────────┘
            │
            ▼
    ┌───────────────────┐
    │ Retrieve Tools    │
    │ (with/without     │
    │  platform filter) │
    └────────┬──────────┘
             │
             ▼
    ┌───────────────────┐
    │ LLM Selection     │
    └────────┬──────────┘
             │
             ▼
    ┌───────────────────┐
    │ Return Selection  │
    └───────────────────┘
```

## Key Improvements Visualized

### Before v3.1 (No Platform Awareness)

```
User Request → Semantic Retrieval → Tool Selection
                      ↓
              [All 500 tools]
                      ↓
              Similarity only
                      ↓
              May select wrong platform!
```

### After v3.1 (Platform-Aware)

```
User Request → Entity Extraction → Asset Lookup → Platform Detection
                                                          ↓
                                                   platform_filter
                                                          ↓
                                              Semantic Retrieval
                                                          ↓
                                              [Filtered tools]
                                                          ↓
                                              Tool Selection
                                                          ↓
                                              ✅ Correct platform!
```

---

**These diagrams illustrate the complete flow of Stage AB v3.1's asset enrichment architecture.**