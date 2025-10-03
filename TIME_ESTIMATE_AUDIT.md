# Time Estimate Audit & Fix Plan

## Problem Statement
Current `time_estimate_ms` formulas are inconsistent - some measure single operation time, others measure total end-to-end time. This causes incorrect tool selection decisions.

## Principle
**All time estimates MUST represent total end-to-end time to deliver results to the user**, including:
- All iterations/loops required
- Network round-trips
- Parallelization benefits
- Result aggregation
- Data transfer time

---

## Pattern Analysis

### ✅ **CORRECT** - Already measures total time

#### 1. `list_summary`
- **Formula**: `200 + 2 * N + 500 * pages`
- **Analysis**: Single API call returns all N results across pages
- **Breakdown**:
  - 200ms: Base API overhead
  - 2ms per asset: Database query + serialization
  - 500ms per page: Pagination overhead
- **Verdict**: ✅ Correct - measures total time for all results

#### 2. `parallel_poll`
- **Formula**: `3000 + 400 * log(max(N, 1)) + p95_latency * 1.2`
- **Analysis**: Polls N assets in parallel
- **Breakdown**:
  - 3000ms: Setup + orchestration overhead
  - 400 * log(N): Logarithmic scaling due to parallelization
  - p95_latency * 1.2: Slowest asset determines completion
- **Verdict**: ✅ Correct - accounts for parallel execution

#### 3. `single_asset_poll`
- **Formula**: `5000 + p95_latency`
- **Analysis**: Single SSH/API call to one asset
- **Breakdown**:
  - 5000ms: SSH connection setup
  - p95_latency: Command execution time
- **Verdict**: ✅ Correct - single operation only

#### 4. `general_info`
- **Formula**: `100`
- **Analysis**: Static documentation lookup
- **Verdict**: ✅ Correct - no iterations needed

---

### ❌ **INCORRECT** - Measures per-operation time, not total time

#### 5. `count_aggregate`
- **Current Formula**: `120 + 0.02 * N`
- **Analysis**: Database COUNT(*) query - single operation
- **Issue**: Formula is actually CORRECT! This is a single aggregation query.
- **Verdict**: ✅ Actually correct - COUNT is a single DB operation

#### 6. `single_lookup` ⚠️ **MAJOR BUG**
- **Current Formula**: `80 + 0.01 * N`
- **Analysis**: This pattern is for looking up ONE asset by ID/hostname
- **Issue**: The formula suggests it scales with N, but the description says "single asset"
- **Problem Scenarios**:
  - Query: "Get IP of server-01" → N=1 → 80ms ✅ Correct
  - Query: "Get IPs of all Linux servers" → N=100 → 81ms ❌ WRONG!
    - If used for multiple assets, needs 100 separate lookups
    - Real time: `(80 + 0.01 * 1) * 100 = 8,010ms`
- **Root Cause**: Pattern is designed for N=1 but formula includes N scaling
- **Fix Options**:
  1. Remove N from formula: `80` (assumes N=1 always)
  2. Add iteration penalty: `80 * N` (if used for multiple lookups)
  3. Add conditional: `80 if N==1 else 80*N` (not supported by SafeMathEvaluator)

#### 7. `detailed_lookup` ⚠️ **MAJOR BUG**
- **Current Formula**: `300 + 5 * N`
- **Analysis**: Detailed lookup with all fields
- **Issue**: Same as single_lookup - unclear if this is:
  - Single API call returning N records: `300 + 5*N` ✅
  - N separate API calls: `(300 + 5*1) * N = 305*N` ❌
- **Need to clarify**: Does the API support batch lookups?

---

## Decision Points

### Question 1: What is the intended behavior of `single_lookup` and `detailed_lookup`?

**Option A: Single API call, multiple results**
- API endpoint: `/assets?ids=1,2,3,...,N`
- Returns N records in one call
- Time: `base + per_record * N`
- Current formulas are CORRECT

**Option B: Multiple API calls (one per asset)**
- API endpoint: `/assets/{id}` called N times
- Returns 1 record per call
- Time: `(base + per_record) * N`
- Current formulas are WRONG

**Option C: Pattern only valid for N=1**
- Pattern should only be selected when N=1
- For N>1, use `list_summary` instead
- Time: `base` (constant)
- Current formulas should remove N

### Question 2: How should the system handle pattern applicability?

**Current behavior**: All patterns are candidates regardless of N

**Proposed behavior**: Add `applicability` constraints
```yaml
single_lookup:
  applicability:
    max_N: 1  # Only valid for single asset queries
```

---

## Recommended Fix Strategy

### Phase 1: Clarify Intent (Need User Input)
1. Determine actual API behavior for each pattern
2. Decide if patterns should have N constraints

### Phase 2: Fix Formulas
Based on user input, update formulas to reflect reality

### Phase 3: Add Documentation
Add comments explaining what each formula measures

### Phase 4: Add Validation
Add tests that verify time estimates match actual behavior

---

## Questions for User

1. **For `single_lookup` pattern**: 
   - Is this a single API call that can return multiple assets?
   - Or is it designed ONLY for N=1 scenarios?
   - If N>1, does it make N separate API calls?

2. **For `detailed_lookup` pattern**:
   - Same questions as above

3. **Should patterns have applicability constraints?**
   - E.g., `single_lookup` only valid when N=1
   - System would automatically exclude it for N>1 queries

4. **What's the actual API design?**
   - Does asset-service-query support batch lookups?
   - Or only single-asset endpoints?