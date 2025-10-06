# Asset Context Flow Diagram

## Complete Architecture Flow

```
┌─────────────────────────────────────────────────────────────────────┐
│                        USER REQUEST                                  │
│              "How many Linux servers in production?"                 │
└────────────────────────────────┬────────────────────────────────────┘
                                 ↓
┌─────────────────────────────────────────────────────────────────────┐
│                    ASSET CONTEXT PROVIDER                            │
│                 (asset_service_context.py)                           │
│                                                                       │
│  ┌─────────────────────────────────────────────────────────────┐   │
│  │ 1. Injection Heuristic                                       │   │
│  │    should_inject_asset_context(query)                        │   │
│  │    → Detects: server, host, asset, database, vm, etc.       │   │
│  └─────────────────────────────────────────────────────────────┘   │
│                                 ↓                                     │
│  ┌─────────────────────────────────────────────────────────────┐   │
│  │ 2. Cache Check (60s TTL)                                     │   │
│  │    _asset_cache.get("all_assets_100")                        │   │
│  │    → HIT: Return cached data                                 │   │
│  │    → MISS: Fetch from API                                    │   │
│  └─────────────────────────────────────────────────────────────┘   │
│                                 ↓                                     │
│  ┌─────────────────────────────────────────────────────────────┐   │
│  │ 3. Live Data Fetching                                        │   │
│  │    fetch_all_assets(limit=100)                               │   │
│  │    → GET http://asset-service:3002/?limit=100                │   │
│  │    → Returns: [{id, name, hostname, ip, os_type, ...}, ...]  │   │
│  └─────────────────────────────────────────────────────────────┘   │
│                                 ↓                                     │
│  ┌─────────────────────────────────────────────────────────────┐   │
│  │ 4. Context Generation                                        │   │
│  │    get_comprehensive_asset_context()                         │   │
│  │    → Schema (50+ fields)                                     │   │
│  │    → Statistics (OS counts, env counts, status counts)       │   │
│  │    → Sample assets (first 10)                                │   │
│  └─────────────────────────────────────────────────────────────┘   │
└────────────────────────────────┬────────────────────────────────────┘
                                 ↓
        ┌────────────────────────┴────────────────────────┐
        ↓                                                  ↓
┌──────────────────────┐                    ┌──────────────────────┐
│    STAGE B           │                    │    STAGE D           │
│  (Tool Selector)     │                    │   (Answerer)         │
│                      │                    │                      │
│  Tie-Breaker:        │                    │  FAST PATH:          │
│  ┌────────────────┐  │                    │  ┌────────────────┐  │
│  │ Compact Schema │  │                    │  │ Comprehensive  │  │
│  │ (~150 tokens)  │  │                    │  │ Context        │  │
│  │                │  │                    │  │ (~500-2000     │  │
│  │ • 50+ fields   │  │                    │  │  tokens)       │  │
│  │ • Capabilities │  │                    │  │                │  │
│  │ • API info     │  │                    │  │ • Schema       │  │
│  └────────────────┘  │                    │  │ • Live data    │  │
│         ↓            │                    │  │ • Statistics   │  │
│  Better tool         │                    │  │ • Samples      │  │
│  selection!          │                    │  └────────────────┘  │
└──────────────────────┘                    │         ↓            │
                                            │  Accurate response   │
                                            │  with real data!     │
                                            └──────────────────────┘
```

## Example Flow: Asset Query

### User Request
```
"How many Linux servers do we have in production?"
```

### Step 1: Injection Heuristic
```python
should_inject_asset_context("How many Linux servers...")
→ Detects: "servers" (infrastructure keyword)
→ Returns: True
```

### Step 2: Cache Check
```python
_asset_cache.get("all_assets_100")
→ MISS (first request)
→ Proceed to fetch
```

### Step 3: Live Data Fetching
```python
fetch_all_assets(limit=100)
→ GET http://asset-service:3002/?limit=100
→ Returns: [
    {
        "id": 1,
        "name": "web-prod-01",
        "hostname": "web-prod-01.example.com",
        "ip_address": "10.0.1.10",
        "os_type": "linux",
        "os_version": "Ubuntu 22.04",
        "environment": "production",
        "status": "active",
        ...
    },
    ...
]
→ Cache for 60 seconds
```

### Step 4: Context Generation
```python
get_comprehensive_asset_context()
→ Generates:
"""
=== ASSET INVENTORY KNOWLEDGE ===

ASSET-SERVICE: Infrastructure inventory with 50+ fields per asset

QUERYABLE FIELDS (organized by category):
• Identity: name, hostname, ip_address, description, tags
• OS: os_type, os_version
...

=== CURRENT INFRASTRUCTURE ===
Total Assets: 47

By Operating System:
  • linux: 23
  • windows: 15
  • macos: 9

By Environment:
  • production: 28
  • staging: 12
  • development: 7

Sample Assets (showing 10 of 47):
  1. web-prod-01 (10.0.1.10) - linux [production]
  2. web-prod-02 (10.0.1.11) - linux [production]
  ...
"""
```

### Step 5: Stage D Processing
```python
# Inject into system prompt
system_prompt = f"""You are a helpful assistant with complete knowledge of our infrastructure assets.

{asset_context}

IMPORTANT INSTRUCTIONS:
- Use the asset data above to answer questions accurately
- When counting or listing assets, use the EXACT data provided
..."""

# Generate response
LLM generates: "We have 23 Linux servers: 15 in production, 8 in staging..."
```

## Example Flow: Tool Selection

### User Request
```
"Restart nginx on all production servers"
```

### Step 1: Stage B Tie-Breaking
```python
# Two tools equally scored
candidate1 = ssh-executor.remote_command
candidate2 = ansible-runner.playbook_execution

# Build prompt with asset context
prompt = await _build_prompt(query, candidate1, candidate2)
→ Injects compact asset schema
→ LLM sees: "50+ fields available, production environment exists"
→ Chooses: ansible-runner (better for multi-server operations)
```

## Example Flow: Hybrid (Asset + Ad-hoc)

### User Request
```
"Deploy app to web-prod-01 AND the new server at 192.168.1.100"
```

### Step 1: Target Enrichment
```python
# Check web-prod-01
ctx1 = await get_asset_context_for_target("web-prod-01")
→ Returns: {
    "is_asset": True,
    "asset_data": {...},  # Full 50+ fields
    "target_type": "asset"
}

# Check 192.168.1.100
ctx2 = await get_asset_context_for_target("192.168.1.100")
→ Returns: {
    "is_asset": False,
    "asset_data": None,
    "target_type": "ad_hoc"
}
```

### Step 2: Execution Planning
```python
# For web-prod-01 (known asset)
→ Use stored credentials
→ Use known OS type (linux)
→ Use known environment (production)

# For 192.168.1.100 (ad-hoc)
→ Ask user for credentials
→ Ask user for OS type
→ Proceed with provided info
```

## Performance Characteristics

### Cache Hit Scenario
```
Request 1: "How many Linux servers?"
  → Fetch from API (200ms)
  → Cache result
  → Total: 200ms

Request 2: "Show all production servers" (within 60s)
  → Cache HIT (1ms)
  → Total: 1ms
  
Savings: 199ms (99.5% faster)
```

### Conditional Injection
```
Infrastructure query: "Show all servers"
  → should_inject = True
  → Inject context (+500 tokens)
  → Total: 2000 tokens

Non-infrastructure query: "What is 2+2?"
  → should_inject = False
  → No context injection
  → Total: 50 tokens
  
Savings: 1950 tokens (97.5% reduction)
```

## Error Handling

### Asset Service Unavailable
```
fetch_all_assets()
  → HTTP Error / Timeout
  → Log error
  → Return empty list []
  → Continue with schema-only context
  → Graceful degradation ✓
```

### Invalid Target
```
get_asset_context_for_target("invalid-host")
  → Not found in database
  → Return ad_hoc context
  → System continues normally ✓
```

## Summary

**Key Points:**
1. ✅ Centralized asset context provider
2. ✅ Smart caching (60s TTL)
3. ✅ Conditional injection (keyword-based)
4. ✅ Comprehensive context (schema + live data)
5. ✅ Hybrid approach (assets + ad-hoc)
6. ✅ Graceful error handling
7. ✅ Performance optimized

**Result:**
- AI has complete asset knowledge
- Works with both assets and ad-hoc targets
- Fast and efficient
- Production-ready

---

**Version:** 2.0.0  
**Status:** Production-Ready