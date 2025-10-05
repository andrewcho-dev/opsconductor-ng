# 🐛 BUG CONFIRMED: Stage B Tool Selection Issue

## Summary
Stage B Selector is incorrectly selecting `prometheus` tool instead of `asset-service-query` tool for asset management queries.

## Bug Discovery
- **Discovered in:** Live E2E test (query: "Show me all assets")
- **Reproduced in:** Unit test `test_stage_b_asset_tool_selection.py`
- **Date:** 2025-01-27
- **Status:** ✅ CONFIRMED with real integration test (NO MOCKS)

## Test Evidence

### Test: `test_list_all_assets_query`
**Input Decision:**
```python
DecisionV1(
    decision_type=DecisionType.INFO,
    intent=IntentV1(
        category="asset_management",
        action="list_assets",
        confidence=0.95
    ),
    original_request="Show me all assets"
)
```

**Expected Behavior:**
- Should select: `asset-service-query` tool
- Tool has capabilities: `asset_query`, `infrastructure_info`, `resource_listing`

**Actual Behavior:**
- ❌ Selects: `prometheus` tool
- Justification: "Selected for comprehensive results. Provides complete coverage."
- Inputs needed: `['metric_type']`

## Root Cause Analysis

### Tool Registry Status
✅ **Asset tools ARE registered correctly:**
```
- asset-service-query: ['asset_query', 'infrastructure_info', 'resource_listing']
- asset-credentials-read: ['credential_access', 'secret_retrieval']
```

### Problem Location
The issue is in the tool selection logic, NOT the tool registry. The tools exist, but Stage B's Hybrid Orchestrator is selecting the wrong tool.

**Likely causes:**
1. **Capability matching logic** - Not properly matching `asset_management` intent to `asset_query` capability
2. **Scoring algorithm** - Prometheus may be scoring higher than asset tools
3. **LLM tie-breaking** - LLM may be preferring prometheus for ambiguous queries
4. **Profile optimization** - Optimization profiles may be biasing toward prometheus

## Impact

### Affected Queries
- "Show me all assets" → selects prometheus ❌
- "Show me all Linux servers" → likely selects prometheus ❌
- "How many assets do we have?" → likely selects prometheus ❌
- Any asset management query → wrong tool selection

### User Experience
- Users get wrong results or errors
- Asset queries fail because prometheus doesn't have asset data
- Confusing error messages about missing metrics when user asked for assets

## Test Suite Created

### File: `tests/test_stage_b_asset_tool_selection.py`
**Real integration tests (NO MOCKS):**
- ✅ `test_tool_registry_has_asset_tools` - PASSES (tools exist)
- ❌ `test_list_all_assets_query` - FAILS (wrong tool selected)
- ❌ `test_list_linux_servers_query` - Not yet run (likely fails)
- ❌ `test_count_assets_query` - Not yet run (likely fails)
- ⏳ `test_metrics_query_should_not_select_asset_tool` - Control test

## Next Steps

### 1. Investigate Hybrid Orchestrator
**File:** `pipeline/stages/stage_b/hybrid_orchestrator.py`
- Check capability matching logic
- Review scoring algorithm
- Examine how intent category maps to tool capabilities

### 2. Check Capability Matcher
**File:** `pipeline/stages/stage_b/capability_matcher.py`
- Verify `asset_management` intent maps to `asset_query` capability
- Check if prometheus is incorrectly matching asset queries

### 3. Review Tool Definitions
**File:** `pipeline/stages/stage_b/tool_registry.py`
- Verify prometheus tool definition doesn't claim asset capabilities
- Ensure asset-service-query has correct capability definitions

### 4. Test Scoring Logic
- Add debug logging to see tool scores
- Understand why prometheus scores higher than asset-service-query
- Check if LLM is being consulted and what it's deciding

### 5. Fix and Verify
- Implement fix in the identified component
- Re-run `test_stage_b_asset_tool_selection.py` - all tests should pass
- Re-run E2E test to verify fix in real environment
- Run full Stage B test suite to ensure no regressions

## Success Criteria
✅ All tests in `test_stage_b_asset_tool_selection.py` pass
✅ Asset queries select `asset-service-query` tool
✅ Metrics queries still select `prometheus` tool (don't break existing functionality)
✅ E2E test "Show me all assets" returns actual asset data
✅ No regressions in existing Stage B tests

## Related Files
- `tests/test_stage_b_asset_tool_selection.py` - New test suite
- `pipeline/stages/stage_b/selector.py` - Main selector
- `pipeline/stages/stage_b/hybrid_orchestrator.py` - Tool selection logic
- `pipeline/stages/stage_b/capability_matcher.py` - Capability matching
- `pipeline/stages/stage_b/tool_registry.py` - Tool definitions
- `tests/e2e/TESTING_SUMMARY.md` - Original E2E test results

## Testing Philosophy
**NO MOCKS!** All tests use:
- ✅ Real Ollama LLM client
- ✅ Real PostgreSQL database
- ✅ Real tool registry
- ✅ Real Stage B selector
- ✅ Tests run inside Docker with all services available

This ensures we catch real-world issues, not just test artifacts.