# Comprehensive Metrics Audit: Time, Cost, and Complexity

## Core Principle
**ALL metrics must represent the TOTAL resources needed to deliver complete results to the user:**
- **Time**: Total wall-clock time from request to final result
- **Cost**: Total API calls, SSH connections, or resource usage
- **Complexity**: Total orchestration complexity for the entire operation

---

## Pattern-by-Pattern Analysis

### 1. `count_aggregate` (asset-service-query)
**Description**: COUNT(*) query on database

**Current Metrics**:
```yaml
time_estimate_ms: "120 + 0.02 * N"
cost_estimate: 1
complexity_score: 0.1
```

**Analysis**:
- **Time**: ✅ Single DB query, scales with table scan - CORRECT
- **Cost**: ✅ Single API call regardless of N - CORRECT
- **Complexity**: ✅ Simple aggregation - CORRECT

**Verdict**: ✅ All metrics correct

---

### 2. `list_summary` (asset-service-query)
**Description**: List assets with basic fields (paginated)

**Current Metrics**:
```yaml
time_estimate_ms: "200 + 2 * N + 500 * pages"
cost_estimate: "1 + pages"
complexity_score: 0.3
```

**Analysis**:
- **Time**: ✅ Accounts for all pages - CORRECT
- **Cost**: ✅ One API call per page - CORRECT
- **Complexity**: ❓ Is 0.3 for the entire operation or per-page?
  - If N=100, pages=5 → 5 API calls
  - Complexity should account for pagination logic
  - **Verdict**: ✅ Probably correct (pagination is moderately complex)

**Verdict**: ✅ All metrics correct

---

### 3. `single_lookup` (asset-service-query) ⚠️
**Description**: "Fast lookup of single asset by ID/hostname"

**Current Metrics**:
```yaml
time_estimate_ms: "80 + 0.01 * N"
cost_estimate: 1
complexity_score: 0.1
```

**Analysis**:
- **Time**: ❌ **INCONSISTENT**
  - Formula includes N, but description says "single asset"
  - If truly single lookup: should be `80` (constant)
  - If N lookups: should be `80 * N` (linear)
  
- **Cost**: ❌ **WRONG IF N > 1**
  - Says `1` (single API call)
  - But if N=100 assets needed, requires 100 API calls
  - Should be: `N` or `1` (depending on API design)
  
- **Complexity**: ❌ **WRONG IF N > 1**
  - Says `0.1` (very simple)
  - But if N=100, need loop orchestration
  - Should be: `0.1` for N=1, higher for N>1

**Verdict**: ❌ **MAJOR BUG** - All three metrics are inconsistent

---

### 4. `detailed_lookup` (asset-service-query) ⚠️
**Description**: "Detailed asset information with all fields"

**Current Metrics**:
```yaml
time_estimate_ms: "300 + 5 * N"
cost_estimate: "1 + ceil(N / 100)"
complexity_score: 0.4
```

**Analysis**:
- **Time**: ❓ **AMBIGUOUS**
  - `300 + 5*N` suggests single call with N results
  - OR N calls with batching?
  
- **Cost**: ❓ **AMBIGUOUS**
  - `1 + ceil(N/100)` suggests batching (100 assets per call)
  - This implies: N=1-100 → 1 call, N=101-200 → 2 calls
  - **If batched**: Time should reflect multiple API calls
  - **If single call**: Cost should be `1` not `1 + ceil(N/100)`
  
- **Complexity**: ❓ **UNCLEAR**
  - `0.4` is moderate
  - Does this account for batching logic?

**Verdict**: ❌ **INCONSISTENT** - Time and cost formulas don't align

**Issue**: Cost formula suggests batching, but time formula doesn't account for multiple API calls!

---

### 5. `parallel_poll` (asset-direct-poll)
**Description**: Poll N assets in parallel via SSH/API

**Current Metrics**:
```yaml
time_estimate_ms: "3000 + 400 * log(max(N, 1)) + p95_latency * 1.2"
cost_estimate: "N"
complexity_score: 0.8
```

**Analysis**:
- **Time**: ✅ Logarithmic scaling for parallelization - CORRECT
- **Cost**: ✅ N SSH/API calls (one per asset) - CORRECT
- **Complexity**: ✅ High complexity (parallel orchestration) - CORRECT

**Verdict**: ✅ All metrics correct and consistent

---

### 6. `single_asset_poll` (asset-direct-poll)
**Description**: Poll single asset for current state

**Current Metrics**:
```yaml
time_estimate_ms: "5000 + p95_latency"
cost_estimate: 1
complexity_score: 0.4
```

**Analysis**:
- **Time**: ✅ Single SSH connection - CORRECT
- **Cost**: ✅ Single API/SSH call - CORRECT
- **Complexity**: ✅ Moderate (SSH orchestration) - CORRECT

**Verdict**: ✅ All metrics correct

---

### 7. `general_info` (info_display)
**Description**: Display static documentation

**Current Metrics**:
```yaml
time_estimate_ms: 100
cost_estimate: 0
complexity_score: 0.1
```

**Analysis**:
- **Time**: ✅ Constant (no external calls) - CORRECT
- **Cost**: ✅ Free (no API calls) - CORRECT
- **Complexity**: ✅ Very simple - CORRECT

**Verdict**: ✅ All metrics correct

---

## Summary of Issues

### ✅ Correct Patterns (4/7)
1. `count_aggregate` - All metrics consistent
2. `list_summary` - All metrics consistent
3. `parallel_poll` - All metrics consistent
4. `single_asset_poll` - All metrics consistent
5. `general_info` - All metrics consistent

### ❌ Broken Patterns (2/7)

#### Pattern: `single_lookup`
**Issues**:
1. Time formula includes N but cost doesn't
2. Description says "single asset" but formula scales with N
3. Complexity doesn't account for iteration

**Impact**: System will choose this for N=100 queries thinking it's fast and cheap, but it's actually slow and expensive!

#### Pattern: `detailed_lookup`
**Issues**:
1. Cost formula suggests batching (ceil(N/100))
2. Time formula doesn't account for multiple batched API calls
3. If N=200, cost=2 calls, but time doesn't add 2× API overhead

**Impact**: System underestimates time for large N queries

---

## Root Cause Analysis

The issue stems from **unclear pattern semantics**:

1. **What does "single_lookup" mean?**
   - Option A: Pattern only valid for N=1 (single asset queries)
   - Option B: Pattern can handle N>1 by making N calls
   - Option C: Pattern can batch multiple lookups in one call

2. **What does "detailed_lookup" mean?**
   - Option A: Single call, returns N records
   - Option B: Batched calls (100 records per call)
   - Option C: N individual calls

**Without knowing the actual API design, we can't fix the formulas correctly!**

---

## Proposed Solution (Without API Knowledge)

Since we don't know the actual API behavior, I propose we make **reasonable assumptions** and document them clearly:

### Assumption Set A: "Conservative Realism"

**Assumption**: Most APIs support batch operations but have limits

**Fixes**:

#### `single_lookup` → Rename to `batch_lookup_small`
```yaml
description: "Fast lookup of assets by ID/hostname (batch up to 10)"
time_estimate_ms: "80 + 10 * ceil(N / 10)"  # 10 assets per batch, 10ms per batch
cost_estimate: "ceil(N / 10)"  # One API call per 10 assets
complexity_score: 0.2  # Slightly more complex due to batching
applicability:
  max_N: 50  # Not suitable for large queries
```

#### `detailed_lookup` → Keep name, fix formulas
```yaml
description: "Detailed asset information with all fields (batch up to 100)"
time_estimate_ms: "300 * ceil(N / 100) + 5 * N"  # 300ms per API call + 5ms per record
cost_estimate: "ceil(N / 100)"  # One call per 100 assets (already correct!)
complexity_score: 0.4  # Moderate (batching logic)
```

#### `list_summary` → Keep as-is
Already correct for paginated list queries

---

## Alternative Solution: Add Pattern Constraints

Add `applicability` field to limit when patterns can be used:

```yaml
single_lookup:
  applicability:
    min_N: 1
    max_N: 1  # ONLY for single asset queries
  time_estimate_ms: 80  # Constant (no N)
  cost_estimate: 1
  complexity_score: 0.1
```

This way, the system automatically excludes `single_lookup` for N>1 queries.

---

## Recommendation

**I propose we implement "Conservative Realism" assumptions:**

1. **Assume APIs support batching** (common in modern APIs)
2. **Use reasonable batch sizes** (10 for fast lookups, 100 for detailed)
3. **Fix all formulas** to be consistent across time/cost/complexity
4. **Add comments** documenting assumptions
5. **Add TODO** to update formulas when actual API behavior is known

**This will make the system functional NOW while allowing future refinement.**

Should I proceed with implementing these fixes?