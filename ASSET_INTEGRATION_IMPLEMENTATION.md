# Asset-Service Integration - Implementation Checklist

## 🎯 Goal
Make AI-BRAIN aware of asset-service as the primary infrastructure data source through **LLM reasoning**, not hardcoded rules.

## 📊 Impact Summary

### Prompt Size Impact
```
Stage A - Entity Extraction:  150 → 230 tokens (+53%, acceptable)
Stage B - Tool Selection:     350 → 450 tokens (+29%, acceptable)
Total Pipeline:              1,650 → 1,830 tokens (+11%, minimal impact)
```

### Expected Behavior Change

**BEFORE:**
```
User: "What's the IP of web-prod-01?"
AI: "I don't have access to that information."
```

**AFTER:**
```
User: "What's the IP of web-prod-01?"
AI: "Server web-prod-01 has IP address 10.0.1.50 and is running Ubuntu 22.04"
```

---

## 📋 Implementation Checklist

### Phase 1: Foundation (1-2 hours)

#### File 1: Create Asset-Service Context Module
- [ ] Create `/home/opsconductor/opsconductor-ng/pipeline/integration/asset_service_context.py`
- [ ] Define `ASSET_SERVICE_SCHEMA` dictionary
- [ ] Implement `get_compact_asset_context()` function (~80 tokens)
- [ ] Implement `should_inject_asset_context()` heuristic (optional optimization)

**Code Template:**
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
    ]
}

def get_compact_asset_context() -> str:
    """Generate compact asset-service context for LLM prompts (~80 tokens)"""
    return """
ASSET-SERVICE: Infrastructure inventory API
- Query assets by: name, hostname, IP, OS, service, environment, tags
- Get: server details, credentials, services, location, status
- Endpoints: GET /?search={term}, GET /{id}
- Use for: "What's the IP of X?", "Show servers in Y", "Get database info"
""".strip()

def should_inject_asset_context(user_request: str) -> bool:
    """Fast heuristic: should we inject asset-service context?"""
    keywords = ["server", "ip", "host", "database", "service", 
                "machine", "node", "instance", "asset", "infrastructure"]
    return any(kw in user_request.lower() for kw in keywords)
```

#### File 2: Register Asset-Service Tool
- [ ] Edit `/home/opsconductor/opsconductor-ng/pipeline/stages/stage_b/tool_registry.py`
- [ ] Add `ASSET_SERVICE_TOOL` definition to tool registry
- [ ] Register tool in `ToolRegistry.__init__()`

**Code Template:**
```python
# In tool_registry.py

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

# In ToolRegistry.__init__():
self.register_tool(ASSET_SERVICE_TOOL)
```

---

### Phase 2: Prompt Enhancement (1-2 hours)

#### File 3: Update Entity Extraction Prompt
- [ ] Edit `/home/opsconductor/opsconductor-ng/llm/prompt_manager.py`
- [ ] Locate `PromptType.ENTITY_EXTRACTION` system prompt
- [ ] Add compact asset-service context at the end
- [ ] Test prompt size (should be ~230 tokens)

**Code Change:**
```python
# In prompt_manager.py, ENTITY_EXTRACTION system prompt:

PromptType.ENTITY_EXTRACTION: {
    "system": """You are an expert at extracting technical entities from system administration requests.

Extract these types of entities:
- hostname: Server names, IP addresses
- service: Service names (nginx, apache, mysql, etc.)
- command: Specific commands to run
- file_path: File or directory paths
- port: Port numbers
- environment: Environment names (prod, staging, dev)
- application: Application names
- database: Database names

ASSET-SERVICE: Infrastructure inventory API
- Query assets by: name, hostname, IP, OS, service, environment, tags
- Get: server details, credentials, services, location, status
- Endpoints: GET /?search={term}, GET /{id}
- Use for: "What's the IP of X?", "Show servers in Y", "Get database info"

For each entity, provide the type, value, and confidence score.

Respond ONLY with valid JSON in this exact format:
[
    {{
        "type": "entity_type",
        "value": "entity_value", 
        "confidence": 0.95
    }}
]

If no entities found, return empty array: []""",
    
    "user": "Extract entities from: {user_request}"
}
```

#### File 4: Update Tool Selection Prompt
- [ ] Edit `/home/opsconductor/opsconductor-ng/llm/prompt_manager.py`
- [ ] Locate `PromptType.TOOL_SELECTION` system prompt
- [ ] Add asset-service awareness section after "CORE RESPONSIBILITIES"
- [ ] Test prompt size (should be ~450 tokens)

**Code Change:**
```python
# In prompt_manager.py, TOOL_SELECTION system prompt:

PromptType.TOOL_SELECTION: {
    "system": """You are the Selector stage of OpsConductor's pipeline. Your role is to select appropriate tools based on classified decisions and available capabilities.

AVAILABLE DATA SOURCES:
- ASSET-SERVICE: Infrastructure inventory (servers, IPs, services, credentials, locations)
  * Query when user asks about: server info, IP addresses, service details, infrastructure
  * Endpoints: GET /?search={term}, GET /{id}
  * Queryable: name, hostname, IP, OS, service, environment, tags, location

CORE RESPONSIBILITIES:
1. Map decision intents to available tools
2. Consult asset-service for infrastructure information queries
3. Apply least-privilege principle in tool selection
4. Assess risk levels and approval requirements
5. Identify additional inputs needed for execution

SELECTION CRITERIA:
- Choose tools with minimum required permissions
- Prefer read-only tools for info mode requests
- Use asset-service for infrastructure queries BEFORE attempting other tools
- Ensure production_safe=true for production environments
- Select multiple tools if needed for complex requests
- Consider tool dependencies and execution order

... (rest of prompt unchanged)
```

---

### Phase 3: Integration Layer (2-3 hours)

#### File 5: Create Asset-Service Integration Module
- [ ] Create `/home/opsconductor/opsconductor-ng/pipeline/integration/asset_service_integration.py`
- [ ] Implement `AssetServiceIntegration` class
- [ ] Add methods: `query_assets()`, `get_asset_by_id()`, `generate_query_step()`
- [ ] Add error handling and circuit breaker

**Code Template:**
```python
# pipeline/integration/asset_service_integration.py

import aiohttp
import logging
from typing import Optional, Dict, List, Any
from datetime import datetime

logger = logging.getLogger(__name__)

class AssetServiceIntegration:
    """Integration layer for asset-service queries in execution plans."""
    
    def __init__(self, asset_service_url: str = "http://asset-service:3002"):
        self.base_url = asset_service_url
        self.timeout = aiohttp.ClientTimeout(total=10)
    
    async def query_assets(
        self, 
        search: Optional[str] = None,
        os_type: Optional[str] = None,
        service_type: Optional[str] = None,
        environment: Optional[str] = None,
        is_active: Optional[bool] = None,
        limit: int = 100
    ) -> Dict[str, Any]:
        """
        Query assets with search and filters.
        
        Returns:
            {"success": bool, "data": [...], "total": int}
        """
        try:
            params = {"limit": limit}
            if search:
                params["search"] = search
            if os_type:
                params["os_type"] = os_type
            if service_type:
                params["service_type"] = service_type
            if is_active is not None:
                params["is_active"] = is_active
            
            async with aiohttp.ClientSession(timeout=self.timeout) as session:
                async with session.get(f"{self.base_url}/", params=params) as response:
                    if response.status == 200:
                        data = await response.json()
                        logger.info(f"Asset query successful: {len(data.get('data', []))} results")
                        return data
                    else:
                        logger.error(f"Asset query failed: {response.status}")
                        return {"success": False, "error": f"HTTP {response.status}"}
        
        except Exception as e:
            logger.error(f"Asset service query error: {str(e)}")
            return {"success": False, "error": str(e)}
    
    async def get_asset_by_id(self, asset_id: int) -> Dict[str, Any]:
        """Get specific asset details by ID."""
        try:
            async with aiohttp.ClientSession(timeout=self.timeout) as session:
                async with session.get(f"{self.base_url}/{asset_id}") as response:
                    if response.status == 200:
                        return await response.json()
                    else:
                        return {"success": False, "error": f"HTTP {response.status}"}
        
        except Exception as e:
            logger.error(f"Asset get by ID error: {str(e)}")
            return {"success": False, "error": str(e)}
    
    def generate_query_step(self, query_params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generate execution step for asset-service query.
        
        Args:
            query_params: Query parameters (search, filters, etc.)
        
        Returns:
            Step definition for Stage C plan
        """
        import uuid
        
        return {
            "id": f"asset_query_{uuid.uuid4().hex[:8]}",
            "description": f"Query asset-service: {query_params}",
            "tool": "asset-service-query",
            "inputs": query_params,
            "preconditions": ["Asset-service is available"],
            "success_criteria": ["Response received", "Valid JSON returned"],
            "failure_handling": "Return empty result set and inform user",
            "estimated_duration": 2,  # seconds
            "depends_on": []
        }
```

#### File 6: Update Stage C to Use Asset-Service
- [ ] Edit `/home/opsconductor/opsconductor-ng/pipeline/stages/stage_c/step_generator.py`
- [ ] Import `AssetServiceIntegration`
- [ ] Add logic to generate asset-service query steps when tool is selected
- [ ] Handle asset-service responses in step execution

**Code Change:**
```python
# In step_generator.py

from pipeline.integration.asset_service_integration import AssetServiceIntegration

class StepGenerator:
    def __init__(self):
        self.asset_service = AssetServiceIntegration()
    
    def generate_steps(self, selection: SelectionV1) -> List[Dict[str, Any]]:
        """Generate execution steps from tool selection."""
        steps = []
        
        for tool in selection.selected_tools:
            if tool.tool_name == "asset-service-query":
                # Generate asset-service query step
                query_params = self._extract_query_params(tool)
                step = self.asset_service.generate_query_step(query_params)
                steps.append(step)
            else:
                # Handle other tools
                step = self._generate_generic_step(tool)
                steps.append(step)
        
        return steps
    
    def _extract_query_params(self, tool: SelectedTool) -> Dict[str, Any]:
        """Extract query parameters from tool inputs."""
        # Parse tool.inputs_needed and tool.justification
        # to determine search term and filters
        return {
            "search": tool.inputs_needed.get("search_term"),
            "os_type": tool.inputs_needed.get("os_type"),
            "service_type": tool.inputs_needed.get("service_type"),
            "environment": tool.inputs_needed.get("environment")
        }
```

---

### Phase 4: Response Formatting (1 hour)

#### File 7: Update Stage D to Format Asset Responses
- [ ] Edit `/home/opsconductor/opsconductor-ng/pipeline/stages/stage_d/response_formatter.py`
- [ ] Add `format_asset_service_response()` method
- [ ] Handle asset-service data in information responses

**Code Template:**
```python
# In response_formatter.py

def format_asset_service_response(self, assets: List[Dict[str, Any]]) -> str:
    """
    Format asset-service query results for user-friendly display.
    
    Args:
        assets: List of asset dictionaries from asset-service
    
    Returns:
        Formatted string for display
    """
    if not assets:
        return "No assets found matching your query."
    
    if len(assets) == 1:
        # Single asset - detailed view
        asset = assets[0]
        return f"""
**{asset['name']}**
- Hostname: {asset['hostname']}
- IP Address: {asset.get('ip_address', 'N/A')}
- OS: {asset.get('os_type', 'N/A')} {asset.get('os_version', '')}
- Service: {asset.get('service_type', 'N/A')} on port {asset.get('port', 'N/A')}
- Environment: {asset.get('environment', 'N/A')}
- Status: {asset.get('status', 'N/A')}
""".strip()
    
    else:
        # Multiple assets - summary view
        lines = [f"Found {len(assets)} assets:"]
        for asset in assets[:10]:  # Limit to 10
            lines.append(f"- {asset['name']} ({asset.get('ip_address', 'N/A')}) - {asset.get('os_type', 'N/A')}")
        
        if len(assets) > 10:
            lines.append(f"... and {len(assets) - 10} more")
        
        return "\n".join(lines)
```

---

### Phase 5: Testing (2-3 hours)

#### Test Cases

- [ ] **Test 1: Simple IP Lookup**
  ```
  User: "What's the IP of web-prod-01?"
  Expected: AI queries asset-service, returns IP address
  ```

- [ ] **Test 2: Server List**
  ```
  User: "Show me all Linux servers"
  Expected: AI queries with os_type=linux filter
  ```

- [ ] **Test 3: Environment Filter**
  ```
  User: "List production databases"
  Expected: AI queries with environment=production, service_type=database
  ```

- [ ] **Test 4: Combined Query**
  ```
  User: "Get details for server db-prod-01"
  Expected: AI queries by name, returns full asset details
  ```

- [ ] **Test 5: No Results**
  ```
  User: "Show me servers named xyz-nonexistent"
  Expected: AI queries, gracefully handles empty result
  ```

- [ ] **Test 6: Asset-Service Down**
  ```
  Scenario: Asset-service is unavailable
  Expected: AI handles error gracefully, informs user
  ```

#### Performance Tests

- [ ] **Measure prompt token count** before/after changes
- [ ] **Measure response time** for asset queries
- [ ] **Verify LLM selects asset-service** for appropriate queries
- [ ] **Check false positives** (queries asset-service when not needed)

---

### Phase 6: Optimization (1-2 hours)

#### Dynamic Context Injection (Optional)

- [ ] Implement `should_inject_asset_context()` in entity extractor
- [ ] Only inject asset-service context when request mentions infrastructure
- [ ] Measure token savings (expected: ~40% of requests don't need it)

**Code Change:**
```python
# In entity_extractor.py

from pipeline.integration.asset_service_context import (
    get_compact_asset_context,
    should_inject_asset_context
)

async def extract_entities(self, user_request: str):
    """Extract entities with optional asset-service context."""
    
    # Determine if we need asset-service context
    if should_inject_asset_context(user_request):
        # Use enhanced prompt with asset context
        system_prompt = self._get_entity_prompt_with_asset_context()
    else:
        # Use standard prompt
        system_prompt = self._get_standard_entity_prompt()
    
    # ... rest of extraction logic
```

#### Prompt Compression

- [ ] Review all prompts for redundancy
- [ ] Remove unnecessary examples
- [ ] Use more concise language where possible
- [ ] Target: Reduce total prompt size by 5-10%

---

## 🎯 Success Criteria

### Functional Success
- ✅ AI-BRAIN correctly identifies when to query asset-service
- ✅ Asset queries return accurate results
- ✅ Responses are formatted in user-friendly way
- ✅ Error handling works gracefully

### Performance Success
- ✅ Prompt size increase < 15% (target: 11%)
- ✅ Response time increase < 20%
- ✅ Asset-service query success rate > 95%

### Intelligence Success
- ✅ LLM reasons about asset-service usage (not hardcoded)
- ✅ No false positives (queries when not needed)
- ✅ No false negatives (misses opportunities to query)

---

## 📈 Metrics to Track

### Before/After Comparison

| Metric | Before | After | Target |
|--------|--------|-------|--------|
| Prompt tokens (avg) | 1,650 | 1,830 | < 1,900 |
| Response time (avg) | 7-9s | ? | < 11s |
| Asset query success | N/A | ? | > 95% |
| Infrastructure Q's answered | 0% | ? | > 90% |

### Ongoing Monitoring

- **Asset-service query frequency**: How often is it used?
- **Query type distribution**: Search vs. filter vs. get-by-id
- **Result quality**: Are responses helpful?
- **User satisfaction**: Feedback on asset-related queries

---

## 🚀 Deployment Plan

### Development Environment
1. Implement all changes in dev branch
2. Run test suite
3. Manual testing with diverse queries
4. Performance benchmarking

### Staging Environment
1. Deploy to staging
2. Run integration tests
3. Monitor for 24 hours
4. Collect metrics

### Production Environment
1. Deploy during low-traffic window
2. Enable feature flag (if implemented)
3. Monitor closely for first hour
4. Gradual rollout to all users

---

## 🔄 Rollback Plan

If issues arise:

1. **Immediate**: Revert prompt changes (restore old prompts)
2. **Quick**: Disable asset-service tool in tool registry
3. **Full**: Revert entire commit

**Rollback triggers:**
- Response time increase > 50%
- Error rate > 10%
- User complaints about incorrect responses
- Asset-service overload

---

## 📝 Documentation Updates

- [ ] Update `README.md` with asset-service integration info
- [ ] Document asset-service query syntax
- [ ] Add examples to user guide
- [ ] Update architecture diagrams
- [ ] Create troubleshooting guide

---

## ✅ Final Checklist

- [ ] All code changes implemented
- [ ] All tests passing
- [ ] Performance metrics acceptable
- [ ] Documentation updated
- [ ] Team review completed
- [ ] Deployment plan approved
- [ ] Rollback plan tested
- [ ] Monitoring dashboards updated

---

## 🎉 Expected Impact

**User Experience:**
- Users can now ask about infrastructure and get instant answers
- No more "I don't have access to that information"
- AI-BRAIN becomes truly infrastructure-aware

**System Intelligence:**
- LLM reasons about data sources, not hardcoded rules
- Scalable pattern for integrating other services
- Foundation for multi-service orchestration

**Operational Efficiency:**
- Faster infrastructure queries (no manual lookups)
- Reduced support tickets for basic info requests
- Better automation with asset context

---

**Ready to implement? Let's make the AI-BRAIN infrastructure-aware! 🧠🚀**