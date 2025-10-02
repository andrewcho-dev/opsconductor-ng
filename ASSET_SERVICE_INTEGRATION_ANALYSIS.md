# Asset-Service Integration Analysis & Optimization Plan

## Executive Summary

**Goal:** Make the AI-BRAIN intelligently aware of the asset-service as the primary source of infrastructure information, enabling it to reason about when to query asset data without hardcoded rules.

**Challenge:** Current prompts are already substantial (200-400 tokens each). Adding asset-service schema knowledge could bloat prompts further, impacting performance and cost.

**Solution:** Implement a **compact, schema-driven approach** that provides the LLM with just enough context to reason intelligently about asset-service capabilities without verbose descriptions.

---

## Current State Analysis

### Asset-Service Capabilities

The asset-service is a **comprehensive infrastructure inventory** containing:

#### Core Asset Information
- **Identity**: name, hostname, ip_address, description, tags
- **Hardware**: device_type, hardware_make, hardware_model, serial_number
- **Operating System**: os_type, os_version
- **Location**: physical_address, data_center, building, room, rack_position, gps_coordinates
- **Management**: status, environment, criticality, owner, support_contact, contract_number

#### Service & Connectivity
- **Primary Service**: service_type, port, is_secure, credential_type, username, domain
- **Additional Services**: JSON array of secondary services (each with own credentials)
- **Database Info**: database_type, database_name
- **Secondary Services**: FTP, monitoring, backup services

#### Status & Metadata
- **Operational**: is_active, connection_status, last_tested_at
- **Audit**: created_by, updated_by, created_at, updated_at

#### API Endpoints
```
GET  /                    - List assets (with filtering: search, os_type, service_type, is_active)
GET  /{id}                - Get asset details
POST /                    - Create asset
PUT  /{id}                - Update asset
DELETE /{id}              - Delete asset
GET  /metadata            - Get dropdown options (credential_types, service_types, os_types)
```

### Current AI-BRAIN Prompt Structure

#### Stage A (Classification) - ~400 tokens
- **Intent Classification**: 200 tokens (system prompt)
- **Entity Extraction**: 150 tokens (system prompt)
- **Confidence Scoring**: 120 tokens (system prompt)
- **Risk Assessment**: 130 tokens (system prompt)

#### Stage B (Selection) - ~350 tokens
- **Tool Selection**: 350 tokens (system prompt + tool list)

#### Stage C (Planning) - ~500 tokens
- **Planning**: 500 tokens (comprehensive safety/sequencing rules)

#### Stage D (Answering) - ~200 tokens
- **Response Generation**: 200 tokens (formatting guidelines)

**Total Prompt Budget per Request**: ~1,550 tokens (system prompts only)

---

## The Problem

### What Happens Without Asset-Service Awareness?

**Current Behavior:**
```
User: "What's the IP of server web-prod-01?"
AI-BRAIN: 
  Stage A → "information" category
  Stage B → No tools selected (doesn't know about asset-service)
  Stage D → "I don't have access to that information"
```

**Desired Behavior:**
```
User: "What's the IP of server web-prod-01?"
AI-BRAIN:
  Stage A → "information" category, entity: hostname="web-prod-01"
  Stage B → Selects "asset-service-query" tool
  Stage C → Plans: GET /assets?search=web-prod-01
  Stage D → "Server web-prod-01 has IP address 10.0.1.50"
```

### Why Hardcoding Won't Work

❌ **Bad Approach:**
```python
if "IP" in request and "server" in request:
    query_asset_service()
```

This is brittle, doesn't scale, and defeats the purpose of having an intelligent AI-BRAIN.

✅ **Good Approach:**
The LLM should **reason** that:
1. User is asking about infrastructure information
2. Asset-service contains infrastructure data
3. Therefore, query asset-service

---

## Proposed Solution: Compact Schema Injection

### Strategy: Minimal Context, Maximum Intelligence

Instead of verbose descriptions, provide the LLM with a **compact schema reference** that enables reasoning without bloat.

### Implementation Approach

#### 1. **Create Asset-Service Context Module** (New File)

```python
# pipeline/integration/asset_service_context.py

ASSET_SERVICE_SCHEMA = {
    "service_name": "asset-service",
    "purpose": "Infrastructure inventory and asset management",
    "base_url": "http://asset-service:3002",
    "capabilities": [
        "query_asset_by_name",
        "query_asset_by_ip", 
        "query_asset_by_hostname",
        "list_assets_by_type",
        "get_asset_credentials",
        "get_asset_services"
    ],
    "queryable_fields": [
        "name", "hostname", "ip_address", "os_type", "service_type",
        "environment", "status", "tags", "location", "owner"
    ],
    "common_queries": {
        "server_info": "GET /?search={name}",
        "ip_lookup": "GET /?search={hostname}",
        "environment_list": "GET /?environment={env}",
        "service_list": "GET /?service_type={type}"
    }
}

def get_compact_asset_context() -> str:
    """
    Generate compact asset-service context for LLM prompts.
    
    Returns ~80 tokens instead of 300+ tokens for full schema.
    """
    return """
ASSET-SERVICE: Infrastructure inventory API
- Query assets by: name, hostname, IP, OS, service, environment, tags
- Get: server details, credentials, services, location, status
- Endpoints: GET /?search={term}, GET /{id}
- Use for: "What's the IP of X?", "Show servers in Y", "Get database info"
""".strip()
```

#### 2. **Inject into Stage A (Entity Extraction)**

**Current Entity Extraction Prompt** (150 tokens):
```
Extract these types of entities:
- hostname: Server names, IP addresses
- service: Service names (nginx, apache, mysql, etc.)
- command: Specific commands to run
...
```

**Enhanced Entity Extraction Prompt** (+80 tokens = 230 tokens):
```
Extract these types of entities:
- hostname: Server names, IP addresses
- service: Service names (nginx, apache, mysql, etc.)
- command: Specific commands to run
...

ASSET-SERVICE: Infrastructure inventory API
- Query assets by: name, hostname, IP, OS, service, environment, tags
- Get: server details, credentials, services, location, status
- Use for: "What's the IP of X?", "Show servers in Y", "Get database info"
```

**Impact**: +80 tokens (53% increase, but still reasonable at 230 tokens total)

#### 3. **Inject into Stage B (Tool Selection)**

**Current Tool Selection Prompt** (350 tokens):
```
You are the Selector stage of OpsConductor's pipeline...
CORE RESPONSIBILITIES:
1. Map decision intents to available tools
2. Apply least-privilege principle
...
```

**Enhanced Tool Selection Prompt** (+100 tokens = 450 tokens):
```
You are the Selector stage of OpsConductor's pipeline...

AVAILABLE DATA SOURCES:
- ASSET-SERVICE: Infrastructure inventory (servers, IPs, services, credentials)
  Query when user asks about: server info, IP addresses, service details, infrastructure

CORE RESPONSIBILITIES:
1. Map decision intents to available tools
2. Consult asset-service for infrastructure information
3. Apply least-privilege principle
...
```

**Impact**: +100 tokens (29% increase, total 450 tokens - acceptable)

#### 4. **Register Asset-Service as a Tool in Stage B**

```python
# pipeline/stages/stage_b/tool_registry.py

ASSET_SERVICE_TOOL = {
    "tool_name": "asset-service-query",
    "category": "information",
    "description": "Query infrastructure inventory for asset information",
    "capabilities": [
        "get_server_info",
        "lookup_ip_address",
        "list_servers",
        "get_service_details",
        "get_credentials"
    ],
    "inputs": {
        "query_type": "search|filter|get_by_id",
        "search_term": "optional",
        "filters": {
            "os_type": "optional",
            "service_type": "optional",
            "environment": "optional",
            "is_active": "optional"
        }
    },
    "outputs": ["asset_list", "asset_details"],
    "risk_level": "low",
    "requires_approval": False,
    "production_safe": True
}
```

#### 5. **Create Asset-Service Integration in Stage C**

```python
# pipeline/stages/stage_c/integrations/asset_service_integration.py

class AssetServiceIntegration:
    """
    Integration layer for asset-service queries in execution plans.
    """
    
    def __init__(self, asset_service_url: str = "http://asset-service:3002"):
        self.base_url = asset_service_url
    
    async def query_assets(self, search: str = None, filters: dict = None):
        """Query assets with search and filters"""
        # Implementation
        pass
    
    async def get_asset_by_id(self, asset_id: int):
        """Get specific asset details"""
        # Implementation
        pass
    
    def generate_query_step(self, query_params: dict) -> dict:
        """
        Generate execution step for asset-service query.
        
        Returns step definition for Stage C plan.
        """
        return {
            "id": f"asset_query_{uuid.uuid4().hex[:8]}",
            "description": f"Query asset-service: {query_params}",
            "tool": "asset-service-query",
            "inputs": query_params,
            "estimated_duration": 2,  # seconds
            "success_criteria": ["Response received", "Valid JSON returned"],
            "failure_handling": "Return empty result set"
        }
```

---

## Optimization Strategy: Keep Prompts Lean

### Prompt Size Budget

| Stage | Current | After Asset Context | Increase | Status |
|-------|---------|---------------------|----------|--------|
| Stage A - Intent | 200 | 200 | 0 | ✅ No change needed |
| Stage A - Entity | 150 | 230 | +80 | ⚠️ Acceptable |
| Stage A - Confidence | 120 | 120 | 0 | ✅ No change needed |
| Stage A - Risk | 130 | 130 | 0 | ✅ No change needed |
| Stage B - Selection | 350 | 450 | +100 | ⚠️ Acceptable |
| Stage C - Planning | 500 | 500 | 0 | ✅ No change needed |
| Stage D - Response | 200 | 200 | 0 | ✅ No change needed |
| **TOTAL** | **1,650** | **1,830** | **+180** | **✅ 11% increase** |

### Why This Works

1. **Targeted Injection**: Only add context where it matters (Entity Extraction, Tool Selection)
2. **Compact Format**: 80-100 tokens vs. 300+ for full schema
3. **Reasoning-Focused**: Give LLM enough to reason, not memorize
4. **No Duplication**: Don't repeat asset-service info in every prompt

### Alternative: Dynamic Context Injection

For even better optimization, inject asset-service context **only when relevant**:

```python
def should_inject_asset_context(user_request: str) -> bool:
    """
    Determine if asset-service context is relevant for this request.
    
    Fast heuristic check before LLM call.
    """
    infrastructure_keywords = [
        "server", "ip", "host", "database", "service",
        "machine", "node", "instance", "asset", "infrastructure"
    ]
    return any(keyword in user_request.lower() for keyword in infrastructure_keywords)

# In Stage A Entity Extractor:
if should_inject_asset_context(user_request):
    prompts = get_entity_extraction_prompt_with_asset_context()
else:
    prompts = get_entity_extraction_prompt()  # Standard prompt
```

**Benefit**: Only pay the +80 token cost when needed (~40% of requests)

---

## Implementation Plan

### Phase 1: Foundation (1-2 hours)
1. ✅ Create `pipeline/integration/asset_service_context.py`
2. ✅ Define compact schema and context generator
3. ✅ Add asset-service tool to Stage B tool registry

### Phase 2: Prompt Enhancement (1-2 hours)
4. ✅ Update Stage A entity extraction prompt
5. ✅ Update Stage B tool selection prompt
6. ✅ Add dynamic context injection logic (optional optimization)

### Phase 3: Integration (2-3 hours)
7. ✅ Create asset-service integration module for Stage C
8. ✅ Add asset-service query step generation
9. ✅ Update Stage D to format asset-service responses

### Phase 4: Testing (2-3 hours)
10. ✅ Test asset-service queries: "What's the IP of server X?"
11. ✅ Test filtering: "Show all Linux servers in production"
12. ✅ Test combined queries: "Get database credentials for prod-db-01"
13. ✅ Verify prompt size impact on performance

### Phase 5: Optimization (1-2 hours)
14. ✅ Measure token usage before/after
15. ✅ Implement dynamic context injection if needed
16. ✅ Fine-tune compact schema based on real usage

**Total Estimated Time**: 7-12 hours

---

## Expected Outcomes

### Before Integration
```
User: "What's the IP of web-prod-01?"
AI-BRAIN: "I don't have access to that information."
```

### After Integration
```
User: "What's the IP of web-prod-01?"
AI-BRAIN: 
  Stage A: Classified as "information", extracted entity: hostname="web-prod-01"
  Stage B: Selected tool: "asset-service-query"
  Stage C: Plan: GET /assets?search=web-prod-01
  Stage D: "Server web-prod-01 has IP address 10.0.1.50 and is running Ubuntu 22.04"
```

### Advanced Queries
```
User: "Show me all production databases"
AI-BRAIN: Queries asset-service with filters: environment=production, service_type=database

User: "Restart the database on server db-prod-01"
AI-BRAIN: 
  1. Queries asset-service for db-prod-01 details
  2. Gets credentials and service info
  3. Plans restart action with proper credentials
  4. Executes with safety checks
```

---

## Prompt Optimization Best Practices

### 1. **Use Structured Formats**
❌ Verbose:
```
The asset-service is a comprehensive infrastructure inventory system that allows you to query information about servers, databases, and other infrastructure components. You can search by name, hostname, IP address, operating system type, service type, environment, and many other fields.
```

✅ Compact:
```
ASSET-SERVICE: Infrastructure inventory
Query by: name, hostname, IP, OS, service, environment
Endpoints: GET /?search={term}, GET /{id}
```

### 2. **Avoid Redundancy**
- Don't repeat asset-service info in every stage
- Inject only where decision-making happens (Entity Extraction, Tool Selection)

### 3. **Use Examples Sparingly**
- 1-2 examples max per prompt section
- Focus on edge cases, not obvious ones

### 4. **Leverage LLM's Existing Knowledge**
- LLMs already understand concepts like "server", "IP address", "database"
- Don't explain basic concepts, just provide API structure

### 5. **Dynamic Context Loading**
- Only inject asset-service context when request mentions infrastructure
- Saves tokens on non-infrastructure requests (math, general questions, etc.)

---

## Metrics to Track

### Performance Metrics
- **Prompt Token Count**: Before/after comparison
- **Response Time**: Impact of larger prompts on LLM latency
- **Token Cost**: Increased cost per request (if using paid LLM)

### Accuracy Metrics
- **Asset Query Success Rate**: % of asset-related questions answered correctly
- **False Positives**: Queries to asset-service when not needed
- **False Negatives**: Missed opportunities to query asset-service

### Usage Metrics
- **Asset-Service Query Frequency**: How often is it selected?
- **Query Types**: Search vs. filter vs. get-by-id distribution
- **Integration Success**: % of queries that return useful results

---

## Risks & Mitigations

### Risk 1: Prompt Bloat
**Impact**: Slower responses, higher costs
**Mitigation**: 
- Use compact schema format (80 tokens vs. 300+)
- Implement dynamic context injection
- Monitor token usage and optimize

### Risk 2: LLM Confusion
**Impact**: LLM might over-use or under-use asset-service
**Mitigation**:
- Clear guidelines in prompts ("Use for: X, Y, Z")
- Test with diverse queries
- Iterate on prompt wording based on results

### Risk 3: Integration Complexity
**Impact**: More moving parts, more failure points
**Mitigation**:
- Graceful degradation (if asset-service down, inform user)
- Comprehensive error handling
- Circuit breaker pattern for asset-service calls

---

## Next Steps

1. **Review this analysis** with the team
2. **Approve the compact schema approach**
3. **Begin Phase 1 implementation**
4. **Test with real queries**
5. **Iterate based on results**

---

## Conclusion

By injecting a **compact, schema-driven context** into Stage A (Entity Extraction) and Stage B (Tool Selection), we can make the AI-BRAIN intelligently aware of the asset-service without significant prompt bloat.

**Key Wins:**
- ✅ Only +180 tokens (11% increase) across all prompts
- ✅ LLM can reason about when to query asset-service
- ✅ No hardcoded rules or pattern matching
- ✅ Scalable approach for future service integrations
- ✅ Optional dynamic injection for further optimization

**The AI-BRAIN will finally know about its infrastructure!** 🧠🚀