# Unit Test Plan: Stage A & B Focus

## Context
Based on live E2E testing, we discovered critical issues in Stage A (Classifier) and Stage B (Selector):

### Issues Discovered
1. **Stage A Performance**: 125 seconds processing time (EXTREMELY SLOW)
2. **Stage B Tool Selection**: Wrong tool selected (prometheus instead of asset tools for "Show me all assets")
3. **Missing Tool Implementation**: Selected tools don't exist in execution engine

## Testing Strategy

### Phase 1: Run Existing Unit Tests
First, verify current state of existing unit tests:
```bash
# Run Stage A tests
pytest tests/test_phase_1_stage_a.py -v

# Run Stage B tests
pytest tests/test_phase_2_stage_b.py -v
```

### Phase 2: Add Specific Test Cases for Discovered Issues

#### Stage A Performance Tests
**File**: `tests/test_stage_a_performance.py`

Test cases:
1. **test_classification_speed_simple_query**
   - Input: "Show me all assets"
   - Expected: < 5 seconds total processing time
   - Measure: Each sub-component timing (intent, entity, confidence, risk)

2. **test_classification_speed_complex_query**
   - Input: "Restart nginx on all production Linux servers in us-east-1"
   - Expected: < 10 seconds total processing time

3. **test_intent_classifier_caching**
   - Verify similar queries use cached results
   - Expected: Second call < 1 second

4. **test_parallel_classification**
   - Run multiple classifications in parallel
   - Verify no blocking issues

#### Stage B Tool Selection Tests
**File**: `tests/test_stage_b_tool_selection.py`

Test cases:
1. **test_asset_query_tool_selection**
   - Input: Decision with intent="information", action="list", entities=[{type:"asset"}]
   - Expected: Select asset service tool (NOT prometheus)
   - Query: "Show me all assets"

2. **test_asset_filter_tool_selection**
   - Input: Decision with intent="information", action="filter", entities=[{type:"os", value:"Linux"}]
   - Expected: Select asset service tool with filter capability
   - Query: "Show me all Linux servers"

3. **test_monitoring_query_tool_selection**
   - Input: Decision with intent="monitoring", action="get_metrics"
   - Expected: Select prometheus tool
   - Query: "Show me CPU metrics"

4. **test_tool_registry_completeness**
   - Verify all tools in registry are implemented in executor
   - Expected: No orphaned tool definitions

5. **test_capability_matching_accuracy**
   - Test capability matcher with various queries
   - Verify correct tool-to-capability mapping

#### Integration Tests
**File**: `tests/test_stage_a_b_integration.py`

Test cases:
1. **test_end_to_end_asset_query**
   - Full pipeline: "Show me all assets" → Stage A → Stage B
   - Verify: Correct intent, correct tool selection, < 10 seconds

2. **test_end_to_end_monitoring_query**
   - Full pipeline: "Show me metrics" → Stage A → Stage B
   - Verify: Correct intent, correct tool selection

3. **test_ambiguous_query_handling**
   - Input: "Show me servers" (could be assets or monitoring)
   - Verify: Proper disambiguation or reasonable default

## Test Execution Plan

### Step 1: Baseline Assessment
```bash
# Run all existing tests and capture results
pytest tests/test_phase_1_stage_a.py -v --tb=short > test_results_stage_a_baseline.txt
pytest tests/test_phase_2_stage_b.py -v --tb=short > test_results_stage_b_baseline.txt
```

### Step 2: Identify Failing Tests
- Review baseline results
- Document which tests are failing
- Categorize failures by root cause

### Step 3: Create New Focused Tests
- Implement performance tests for Stage A
- Implement tool selection accuracy tests for Stage B
- Add integration tests for common queries

### Step 4: Fix Issues
Priority order:
1. **Fix Stage B tool selection logic** (highest impact - wrong results)
2. **Optimize Stage A performance** (high impact - user experience)
3. **Add missing tool implementations** (medium impact - execution failures)
4. **Improve error handling** (low impact - edge cases)

### Step 5: Regression Testing
- Re-run all tests after each fix
- Verify no new issues introduced
- Update test expectations as needed

## Success Criteria

### Stage A (Classifier)
- ✅ All existing unit tests pass
- ✅ Simple queries process in < 5 seconds
- ✅ Complex queries process in < 10 seconds
- ✅ Intent classification accuracy > 90%
- ✅ Entity extraction accuracy > 85%

### Stage B (Selector)
- ✅ All existing unit tests pass
- ✅ Asset queries select asset service tools (100% accuracy)
- ✅ Monitoring queries select monitoring tools (100% accuracy)
- ✅ All selected tools exist in executor
- ✅ Tool selection time < 2 seconds

### Integration
- ✅ End-to-end "Show me all assets" completes in < 15 seconds
- ✅ Correct tool selected for 95% of test queries
- ✅ No execution failures due to missing tools

## Test Data

### Sample Queries for Testing

#### Asset Queries (Should select asset service tools)
1. "Show me all assets"
2. "List all servers"
3. "Show me Linux servers"
4. "How many Windows machines do we have?"
5. "Show me assets in production"

#### Monitoring Queries (Should select monitoring tools)
1. "Show me CPU metrics"
2. "What's the memory usage?"
3. "Show me prometheus metrics"
4. "Get system metrics for web-01"

#### Automation Queries (Should select automation tools)
1. "Restart nginx"
2. "Deploy application to production"
3. "Run health check on all servers"

#### Ambiguous Queries (Need disambiguation)
1. "Show me servers" (could be assets or monitoring)
2. "Check status" (what status?)
3. "Get information" (what information?)

## Next Steps

1. ✅ Create this test plan document
2. ⏳ Run existing unit tests and capture baseline
3. ⏳ Analyze failures and categorize issues
4. ⏳ Create new focused test cases
5. ⏳ Fix Stage B tool selection logic
6. ⏳ Optimize Stage A performance
7. ⏳ Verify all fixes with regression testing
8. ⏳ Update documentation with findings

## Notes

- Focus on **correctness first, performance second**
- Use **real LLM calls** for integration tests (not mocks)
- Use **mocks** for unit tests to ensure speed and reliability
- Document all timing measurements for performance tracking
- Keep test queries realistic and based on actual user needs