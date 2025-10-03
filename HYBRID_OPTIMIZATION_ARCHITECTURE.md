# Hybrid Optimization Architecture: Visual Guide

## System Overview

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         HYBRID OPTIMIZATION SYSTEM                           │
│                                                                               │
│  Two-Phase Architecture:                                                     │
│  1. Deterministic Pre-Selector (Source of Truth)                             │
│  2. LLM Tie-Breaker (Ambiguous Cases Only)                                   │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Complete Flow Diagram

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                              USER QUERY                                      │
│                  "Quick count of all Linux servers"                          │
└────────────────────────────────┬────────────────────────────────────────────┘
                                 │
                                 ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                         STAGE A: Intent Classification                       │
│  Output: required_capabilities = ["asset_query"]                            │
└────────────────────────────────┬────────────────────────────────────────────┘
                                 │
                                 ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                         STAGE B: Tool Selection                              │
│                      (HYBRID OPTIMIZATION)                                   │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                               │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │ PHASE 1: Preference Detection                                        │   │
│  │                                                                       │   │
│  │  Input: "Quick count of all Linux servers"                           │   │
│  │  Detected: mode="fast", speed=0.4, accuracy=0.2, cost=0.2, ...      │   │
│  │  Output: UserPreferences(mode="fast", speed=0.4, ...)                │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                 │                                             │
│                                 ▼                                             │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │ PHASE 2: Candidate Enumeration                                       │   │
│  │                                                                       │   │
│  │  Load Profiles: asset-service-query, asset-direct-poll, ...         │   │
│  │  Match Capabilities: "asset_query" → 6 patterns                      │   │
│  │  Estimate Context: N=100, pages=1, p95_latency=1000                  │   │
│  │  Evaluate Expressions:                                                │   │
│  │    - count_aggregate: time=122ms, cost=$0.15                          │   │
│  │    - parallel_poll: time=3200ms, cost=$6.00                           │   │
│  │    - list_summary: time=700ms, cost=$0.30                             │   │
│  │    - ...                                                              │   │
│  │  Output: List[ToolCandidate] (6 candidates)                          │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                 │                                             │
│                                 ▼                                             │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │ PHASE 3: Feature Normalization                                       │   │
│  │                                                                       │   │
│  │  Normalize time_ms to [0,1]:                                         │   │
│  │    - 122ms → 0.92 (fast)                                             │   │
│  │    - 3200ms → 0.35 (slow)                                            │   │
│  │  Normalize cost to [0,1]:                                            │   │
│  │    - $0.15 → 0.985 (cheap)                                           │   │
│  │    - $6.00 → 0.40 (expensive)                                        │   │
│  │  Normalize complexity (already [0,1])                                │   │
│  │  Output: All features in [0,1] where 1 is best                       │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                 │                                             │
│                                 ▼                                             │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │ PHASE 4: Policy Enforcement (HARD CONSTRAINTS)                       │   │
│  │                                                                       │   │
│  │  Check max_cost: Filter out tools > $10                              │   │
│  │  Check production_safe: Filter out non-production tools              │   │
│  │  Check requires_background_if: Evaluate "N > 50"                     │   │
│  │  Check requires_approval: Flag tools needing approval                │   │
│  │  Output: Filtered List[ToolCandidate] (4 candidates)                 │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                 │                                             │
│                                 ▼                                             │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │ PHASE 5: Deterministic Scoring                                       │   │
│  │                                                                       │   │
│  │  Compute weighted sum for each candidate:                            │   │
│  │    score = w_speed × norm_speed +                                    │   │
│  │            w_accuracy × norm_accuracy +                               │   │
│  │            w_cost × norm_cost +                                       │   │
│  │            w_complexity × norm_complexity +                           │   │
│  │            w_completeness × norm_completeness                         │   │
│  │                                                                       │   │
│  │  Example (fast mode: speed=0.4, accuracy=0.2, cost=0.2, ...):       │   │
│  │    - count_aggregate: 0.4×0.92 + 0.2×0.6 + 0.2×0.985 + ... = 0.85   │   │
│  │    - parallel_poll: 0.4×0.35 + 0.2×1.0 + 0.2×0.40 + ... = 0.52      │   │
│  │    - list_summary: 0.4×0.70 + 0.2×0.7 + 0.2×0.97 + ... = 0.72       │   │
│  │                                                                       │   │
│  │  Sort by score (descending):                                         │   │
│  │    1. count_aggregate (0.85)                                         │   │
│  │    2. list_summary (0.72)                                            │   │
│  │    3. parallel_poll (0.52)                                           │   │
│  │  Output: Ranked List[ToolCandidate]                                  │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                 │                                             │
│                                 ▼                                             │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │ PHASE 6: Ambiguity Detection                                         │   │
│  │                                                                       │   │
│  │  Compare top-2 scores:                                               │   │
│  │    |score_1 - score_2| = |0.85 - 0.72| = 0.13                       │   │
│  │                                                                       │   │
│  │  Is ambiguous? (threshold ε = 0.08)                                  │   │
│  │    0.13 > 0.08 → NO, CLEAR WINNER                                    │   │
│  │                                                                       │   │
│  │  Decision: Use deterministic winner (count_aggregate)                │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                 │                                             │
│                                 ▼                                             │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │ PHASE 7: Output Generation                                           │   │
│  │                                                                       │   │
│  │  Selected: asset-service-query (count_aggregate)                     │   │
│  │  Execution Mode: immediate                                           │   │
│  │  SLA Class: interactive                                              │   │
│  │  Justification: "Selected for fast response time (~122ms)"           │   │
│  │  Alternatives: [list_summary, parallel_poll]                         │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                 │                                             │
│                                 ▼                                             │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │ PHASE 8: Telemetry Logging                                           │   │
│  │                                                                       │   │
│  │  Log to database:                                                    │   │
│  │    - Query, preferences, selected tool                               │   │
│  │    - Predicted: time=122ms, cost=$0.15                               │   │
│  │    - Selection method: "deterministic"                               │   │
│  │    - Alternatives, scores                                            │   │
│  │  (Actuals filled in later by Stage E)                                │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                               │
└────────────────────────────────┬────────────────────────────────────────────┘
                                 │
                                 ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                         STAGE C: Parameter Extraction                        │
│  Extract parameters for selected tool                                        │
└────────────────────────────────┬────────────────────────────────────────────┘
                                 │
                                 ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                         STAGE D: Plan Generation                             │
│  Generate execution plan                                                     │
└────────────────────────────────┬────────────────────────────────────────────┘
                                 │
                                 ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                         STAGE E: Execution                                   │
│  Execute tool, measure actual time/cost                                      │
│  Update telemetry with actuals                                               │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Ambiguous Case Flow (LLM Tie-Breaker)

```
┌─────────────────────────────────────────────────────────────────────────────┐
│  SCENARIO: Two tools have very similar scores                               │
│                                                                               │
│  Top-2 Candidates:                                                           │
│    1. count_aggregate: score=0.75                                            │
│    2. list_summary: score=0.72                                               │
│                                                                               │
│  Score difference: |0.75 - 0.72| = 0.03 < ε (0.08)                          │
│  → AMBIGUOUS!                                                                │
└────────────────────────────────┬────────────────────────────────────────────┘
                                 │
                                 ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│  OPTION 1: Ask Clarifying Question                                          │
│                                                                               │
│  Generate question based on largest difference:                              │
│    "Do you need results immediately, or can you wait for more accuracy?"    │
│                                                                               │
│  User responds → Re-run with updated preferences                             │
└─────────────────────────────────────────────────────────────────────────────┘
                                 │
                                 ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│  OPTION 2: LLM Tie-Breaker                                                  │
│                                                                               │
│  Generate compact prompt:                                                    │
│  ┌───────────────────────────────────────────────────────────────────────┐ │
│  │ USER QUERY: "Count of all Linux servers"                              │ │
│  │                                                                         │ │
│  │ OPTION A: count_aggregate                                              │ │
│  │   - Time: 122ms, Cost: $0.15, Accuracy: 0.6/1.0                       │ │
│  │   - Limitations: Cached data (may be stale)                            │ │
│  │                                                                         │ │
│  │ OPTION B: list_summary                                                 │ │
│  │   - Time: 700ms, Cost: $0.30, Accuracy: 0.7/1.0                       │ │
│  │   - Limitations: Paginated (may need multiple requests)                │ │
│  │                                                                         │ │
│  │ Choose: A or B + justification                                         │ │
│  └───────────────────────────────────────────────────────────────────────┘ │
│                                                                               │
│  LLM Response:                                                               │
│  {                                                                            │
│    "choice": "A",                                                             │
│    "justification": "User asked for 'quick' count, so prioritize speed"     │
│  }                                                                            │
│                                                                               │
│  Fallback: If LLM fails, use deterministic winner (Option A)                │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Data Flow: Phase 1 (Current Implementation)

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         YAML PROFILE (Source of Truth)                       │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                               │
│  tools:                                                                       │
│    asset-service-query:                                                      │
│      defaults:                                                                │
│        performance:                                                           │
│          complexity: 0.3                                                      │
│        policy:                                                                │
│          production_safe: true                                                │
│                                                                               │
│      capabilities:                                                            │
│        asset_query:                                                           │
│          patterns:                                                            │
│            count_aggregate:                                                   │
│              performance:                                                     │
│                time_ms_formula: "120 + 0.02 * N"                             │
│                cost_formula: "0.001 * N + 0.05"                              │
│              preference_scores:                                               │
│                speed: 0.95                                                    │
│                accuracy: 0.6                                                  │
│                cost: 0.95                                                     │
│              limitations:                                                     │
│                - "Cached data (may be stale)"                                │
└────────────────────────────────┬────────────────────────────────────────────┘
                                 │
                                 ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                         PROFILE LOADER                                       │
│  - Load YAML                                                                 │
│  - Validate with Pydantic                                                    │
│  - Apply inheritance (defaults → patterns)                                   │
│  - Validate expressions with SafeMathEvaluator                               │
│  - Cache for performance                                                     │
└────────────────────────────────┬────────────────────────────────────────────┘
                                 │
                                 ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                         PYDANTIC MODELS                                      │
│                                                                               │
│  OptimizationProfilesConfig                                                  │
│    └── tools: Dict[str, ToolProfile]                                         │
│          └── capabilities: Dict[str, CapabilityProfile]                      │
│                └── patterns: Dict[str, PatternProfile]                       │
│                      ├── performance: PerformanceProfile                     │
│                      │     ├── time_ms_formula: str                          │
│                      │     ├── cost_formula: str                             │
│                      │     └── complexity: float                             │
│                      ├── preference_scores: PreferenceMatchScores            │
│                      │     ├── speed: float [0,1]                            │
│                      │     ├── accuracy: float [0,1]                         │
│                      │     ├── cost: float [0,1]                             │
│                      │     ├── complexity: float [0,1]                       │
│                      │     └── completeness: float [0,1]                     │
│                      ├── policy: PolicyConfig                                │
│                      │     ├── max_cost: Optional[float]                     │
│                      │     ├── requires_approval: bool                       │
│                      │     ├── production_safe: bool                         │
│                      │     └── requires_background_if: Optional[str]         │
│                      └── limitations: List[str]                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Expression Evaluation Flow

```
┌─────────────────────────────────────────────────────────────────────────────┐
│  EXPRESSION: "120 + 0.02 * N"                                               │
│  CONTEXT: {"N": 100, "pages": 1, "p95_latency": 1000}                       │
└────────────────────────────────┬────────────────────────────────────────────┘
                                 │
                                 ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│  STEP 1: Parse Expression (AST)                                             │
│                                                                               │
│  ast.parse("120 + 0.02 * N") →                                              │
│    BinOp(                                                                    │
│      left=Constant(value=120),                                               │
│      op=Add(),                                                               │
│      right=BinOp(                                                            │
│        left=Constant(value=0.02),                                            │
│        op=Mult(),                                                            │
│        right=Name(id='N')                                                    │
│      )                                                                       │
│    )                                                                         │
└────────────────────────────────┬────────────────────────────────────────────┘
                                 │
                                 ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│  STEP 2: Validate AST (Security)                                            │
│                                                                               │
│  Check each node:                                                            │
│    ✓ Constant(120) → Allowed                                                │
│    ✓ BinOp(Add) → Allowed (whitelisted)                                     │
│    ✓ Constant(0.02) → Allowed                                               │
│    ✓ BinOp(Mult) → Allowed (whitelisted)                                    │
│    ✓ Name('N') → Allowed (whitelisted variable)                             │
│    ✓ Depth: 3 < 20 → OK                                                     │
│                                                                               │
│  No forbidden nodes (Import, Call to non-whitelisted, Attribute, etc.)      │
└────────────────────────────────┬────────────────────────────────────────────┘
                                 │
                                 ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│  STEP 3: Evaluate AST (Runtime)                                             │
│                                                                               │
│  Evaluate recursively:                                                       │
│    eval_node(Constant(120)) → 120                                           │
│    eval_node(Constant(0.02)) → 0.02                                         │
│    eval_node(Name('N')) → context['N'] → 100                                │
│    eval_node(BinOp(Mult, 0.02, 100)) → 0.02 * 100 → 2.0                    │
│    eval_node(BinOp(Add, 120, 2.0)) → 120 + 2.0 → 122.0                     │
│                                                                               │
│  Result: 122.0 ms                                                            │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Scoring Algorithm (Phase 2, Not Yet Implemented)

```
┌─────────────────────────────────────────────────────────────────────────────┐
│  INPUT: ToolCandidate + UserPreferences                                     │
│                                                                               │
│  Candidate:                                                                  │
│    - estimated_time_ms: 122                                                  │
│    - estimated_cost: 0.15                                                    │
│    - complexity: 0.3                                                         │
│    - preference_scores: {speed: 0.95, accuracy: 0.6, cost: 0.95, ...}       │
│                                                                               │
│  Preferences (fast mode):                                                    │
│    - speed: 0.4                                                              │
│    - accuracy: 0.2                                                           │
│    - cost: 0.2                                                               │
│    - complexity: 0.1                                                         │
│    - completeness: 0.1                                                       │
└────────────────────────────────┬────────────────────────────────────────────┘
                                 │
                                 ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│  STEP 1: Normalize Features                                                 │
│                                                                               │
│  Time (log scale, 50ms-60s):                                                │
│    norm_time = 1 - (log(122) - log(50)) / (log(60000) - log(50))           │
│              = 1 - (4.80 - 3.91) / (10.99 - 3.91)                           │
│              = 1 - 0.89 / 7.08                                               │
│              = 1 - 0.126 = 0.874 ≈ 0.87                                     │
│                                                                               │
│  Cost (linear scale, $0-$10):                                               │
│    norm_cost = 1 - (0.15 - 0) / (10 - 0)                                    │
│              = 1 - 0.015 = 0.985                                             │
│                                                                               │
│  Complexity (already [0,1], invert):                                         │
│    norm_complexity = 1 - 0.3 = 0.7                                           │
│                                                                               │
│  Accuracy (already [0,1]):                                                   │
│    norm_accuracy = 0.6                                                       │
│                                                                               │
│  Completeness (already [0,1]):                                               │
│    norm_completeness = 0.8                                                   │
└────────────────────────────────┬────────────────────────────────────────────┘
                                 │
                                 ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│  STEP 2: Compute Weighted Sum                                               │
│                                                                               │
│  score = w_speed × norm_speed +                                              │
│          w_accuracy × norm_accuracy +                                        │
│          w_cost × norm_cost +                                                │
│          w_complexity × norm_complexity +                                    │
│          w_completeness × norm_completeness                                  │
│                                                                               │
│        = 0.4 × 0.87 +                                                        │
│          0.2 × 0.6 +                                                         │
│          0.2 × 0.985 +                                                       │
│          0.1 × 0.7 +                                                         │
│          0.1 × 0.8                                                           │
│                                                                               │
│        = 0.348 + 0.12 + 0.197 + 0.07 + 0.08                                 │
│        = 0.815                                                               │
│                                                                               │
│  Final Score: 0.815 / 1.0 (weights sum to 1.0)                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Policy Enforcement (Phase 2, Not Yet Implemented)

```
┌─────────────────────────────────────────────────────────────────────────────┐
│  INPUT: List[ToolCandidate] + Context + Environment                         │
│                                                                               │
│  Candidates:                                                                 │
│    1. count_aggregate: cost=$0.15, production_safe=true                      │
│    2. parallel_poll: cost=$6.00, production_safe=true, max_N_immediate=50   │
│    3. experimental_tool: cost=$0.10, production_safe=false                   │
│                                                                               │
│  Context: {"N": 100, "pages": 1, "p95_latency": 1000}                       │
│  Environment: "production"                                                   │
└────────────────────────────────┬────────────────────────────────────────────┘
                                 │
                                 ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│  CHECK 1: max_cost                                                           │
│                                                                               │
│  ✓ count_aggregate: $0.15 < $10 → PASS                                      │
│  ✓ parallel_poll: $6.00 < $10 → PASS                                        │
│  ✓ experimental_tool: $0.10 < $10 → PASS                                    │
└────────────────────────────────┬────────────────────────────────────────────┘
                                 │
                                 ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│  CHECK 2: production_safe                                                    │
│                                                                               │
│  ✓ count_aggregate: production_safe=true → PASS                             │
│  ✓ parallel_poll: production_safe=true → PASS                               │
│  ✗ experimental_tool: production_safe=false → FAIL (filter out)             │
└────────────────────────────────┬────────────────────────────────────────────┘
                                 │
                                 ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│  CHECK 3: requires_background_if                                             │
│                                                                               │
│  ✓ count_aggregate: no condition → PASS (immediate)                         │
│  ✓ parallel_poll: "N > 50" → Evaluate with context                          │
│      SafeMathEvaluator("N > 50").evaluate({"N": 100}) → True                │
│      → Set execution_mode_hint="background"                                  │
└────────────────────────────────┬────────────────────────────────────────────┘
                                 │
                                 ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│  OUTPUT: Filtered Candidates                                                │
│                                                                               │
│  Allowed:                                                                    │
│    1. count_aggregate (immediate)                                            │
│    2. parallel_poll (background)                                             │
│                                                                               │
│  Violations:                                                                 │
│    - experimental_tool: Not production-safe                                  │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Telemetry & Learning Loop (Phase 6, Not Yet Implemented)

```
┌─────────────────────────────────────────────────────────────────────────────┐
│  SELECTION TIME: Log Predictions                                            │
│                                                                               │
│  INSERT INTO tool_selection_telemetry:                                       │
│    - query: "Quick count of all Linux servers"                              │
│    - selected_tool: "asset-service-query"                                    │
│    - selected_pattern: "count_aggregate"                                     │
│    - predicted_time_ms: 122                                                  │
│    - predicted_cost: 0.15                                                    │
│    - selection_method: "deterministic"                                       │
│    - alternatives: [list_summary, parallel_poll]                             │
│    - timestamp: 2025-01-15 10:30:00                                          │
└────────────────────────────────┬────────────────────────────────────────────┘
                                 │
                                 ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│  EXECUTION TIME: Update Actuals (from Stage E)                              │
│                                                                               │
│  UPDATE tool_selection_telemetry:                                            │
│    - actual_time_ms: 135 (10% slower than predicted)                        │
│    - actual_cost: 0.16 (7% more expensive)                                  │
│    - actual_success: true                                                    │
│    - timestamp: 2025-01-15 10:30:01                                          │
└────────────────────────────────┬────────────────────────────────────────────┘
                                 │
                                 ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│  NIGHTLY ANALYSIS: Compare Predictions vs Actuals                           │
│                                                                               │
│  Query last 7 days:                                                          │
│    SELECT                                                                    │
│      selected_tool, selected_pattern,                                        │
│      AVG(predicted_time_ms) as avg_pred_time,                                │
│      AVG(actual_time_ms) as avg_actual_time,                                 │
│      AVG(predicted_cost) as avg_pred_cost,                                   │
│      AVG(actual_cost) as avg_actual_cost                                     │
│    FROM tool_selection_telemetry                                             │
│    WHERE timestamp > NOW() - INTERVAL '7 days'                               │
│    GROUP BY selected_tool, selected_pattern                                  │
│                                                                               │
│  Results:                                                                    │
│    count_aggregate:                                                          │
│      - Predicted time: 122ms, Actual: 135ms (10% error)                     │
│      - Predicted cost: $0.15, Actual: $0.16 (7% error)                      │
│      - Recommendation: Adjust time coefficient by 1.10                       │
└────────────────────────────────┬────────────────────────────────────────────┘
                                 │
                                 ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│  MANUAL TUNING: Update YAML Profiles                                        │
│                                                                               │
│  OLD: time_ms_formula: "120 + 0.02 * N"                                     │
│  NEW: time_ms_formula: "132 + 0.022 * N"  (10% adjustment)                  │
│                                                                               │
│  Commit to Git → Deploy → Monitor for 7 days → Repeat                       │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Component Dependencies

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         DEPENDENCY GRAPH                                     │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                               │
│  ┌──────────────────────┐                                                    │
│  │  SafeMathEvaluator   │ ◄─────────────────────┐                           │
│  │  (Phase 1 ✅)        │                        │                           │
│  └──────────┬───────────┘                        │                           │
│             │                                     │                           │
│             ▼                                     │                           │
│  ┌──────────────────────┐                        │                           │
│  │  ProfileLoader       │                        │                           │
│  │  (Phase 1 ✅)        │                        │                           │
│  └──────────┬───────────┘                        │                           │
│             │                                     │                           │
│             ▼                                     │                           │
│  ┌──────────────────────┐                        │                           │
│  │  CandidateEnumerator │                        │                           │
│  │  (Phase 3 🔄)        │                        │                           │
│  └──────────┬───────────┘                        │                           │
│             │                                     │                           │
│             ▼                                     │                           │
│  ┌──────────────────────┐     ┌─────────────────┴──────┐                    │
│  │  PolicyEnforcer      │ ──► │  SafeMathEvaluator     │                    │
│  │  (Phase 2 🔄)        │     │  (for condition eval)  │                    │
│  └──────────┬───────────┘     └────────────────────────┘                    │
│             │                                                                 │
│             ▼                                                                 │
│  ┌──────────────────────┐                                                    │
│  │  FeatureNormalizer   │                                                    │
│  │  (Phase 2 🔄)        │                                                    │
│  └──────────┬───────────┘                                                    │
│             │                                                                 │
│             ▼                                                                 │
│  ┌──────────────────────┐                                                    │
│  │  DeterministicScorer │                                                    │
│  │  (Phase 2 🔄)        │                                                    │
│  └──────────┬───────────┘                                                    │
│             │                                                                 │
│             ▼                                                                 │
│  ┌──────────────────────┐                                                    │
│  │  AmbiguityDetector   │                                                    │
│  │  (Phase 4 🔄)        │                                                    │
│  └──────────┬───────────┘                                                    │
│             │                                                                 │
│             ▼                                                                 │
│  ┌──────────────────────┐                                                    │
│  │  LLMTieBreaker       │                                                    │
│  │  (Phase 4 🔄)        │                                                    │
│  └──────────┬───────────┘                                                    │
│             │                                                                 │
│             ▼                                                                 │
│  ┌──────────────────────┐                                                    │
│  │  HybridSelector      │ ◄── Orchestrates all modules                      │
│  │  (Phase 5 🔄)        │                                                    │
│  └──────────┬───────────┘                                                    │
│             │                                                                 │
│             ▼                                                                 │
│  ┌──────────────────────┐                                                    │
│  │  TelemetryLogger     │                                                    │
│  │  (Phase 6 🔄)        │                                                    │
│  └──────────────────────┘                                                    │
│                                                                               │
│  ┌──────────────────────┐                                                    │
│  │  PreferenceDetector  │ ◄── Independent module                            │
│  │  (Phase 3 🔄)        │                                                    │
│  └──────────────────────┘                                                    │
│                                                                               │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## File Structure

```
/home/opsconductor/opsconductor-ng/
│
├── pipeline/
│   ├── stages/
│   │   └── stage_b/
│   │       ├── safe_math_eval.py              ✅ Phase 1 (217 lines)
│   │       ├── optimization_schemas.py        ✅ Phase 1 (234 lines)
│   │       ├── profile_loader.py              ✅ Phase 1 (186 lines)
│   │       ├── feature_normalizer.py          🔄 Phase 2 (TODO)
│   │       ├── deterministic_scorer.py        🔄 Phase 2 (TODO)
│   │       ├── policy_enforcer.py             🔄 Phase 2 (TODO)
│   │       ├── preference_detector.py         🔄 Phase 3 (TODO)
│   │       ├── candidate_enumerator.py        🔄 Phase 3 (TODO)
│   │       ├── ambiguity_detector.py          🔄 Phase 4 (TODO)
│   │       ├── llm_tie_breaker.py             🔄 Phase 4 (TODO)
│   │       ├── hybrid_selector.py             🔄 Phase 5 (TODO)
│   │       ├── telemetry_logger.py            🔄 Phase 6 (TODO)
│   │       └── selector.py                    🔄 Phase 5 (Update existing)
│   │
│   └── config/
│       └── tool_optimization_profiles.yaml    ✅ Phase 1 (318 lines)
│
├── tests/
│   ├── test_safe_math_eval.py                 ✅ Phase 1 (24 tests)
│   ├── test_profile_loader.py                 ✅ Phase 1 (16 tests)
│   ├── test_feature_normalizer.py             🔄 Phase 2 (TODO)
│   ├── test_deterministic_scorer.py           🔄 Phase 2 (TODO)
│   ├── test_policy_enforcer.py                🔄 Phase 2 (TODO)
│   ├── test_preference_detector.py            🔄 Phase 3 (TODO)
│   ├── test_candidate_enumerator.py           🔄 Phase 3 (TODO)
│   ├── test_ambiguity_detector.py             🔄 Phase 4 (TODO)
│   ├── test_llm_tie_breaker.py                🔄 Phase 4 (TODO)
│   ├── test_hybrid_selector.py                🔄 Phase 5 (TODO)
│   └── test_telemetry_logger.py               🔄 Phase 6 (TODO)
│
├── scripts/
│   └── analyze_tool_selection_telemetry.py    🔄 Phase 6 (TODO)
│
└── docs/
    ├── HYBRID_OPTIMIZATION_IMPLEMENTATION_PLAN.md      ✅ Complete
    ├── HYBRID_OPTIMIZATION_PHASE1_COMPLETE.md          ✅ Complete
    └── HYBRID_OPTIMIZATION_ARCHITECTURE.md             ✅ This file
```

---

## Summary

This document provides visual diagrams and flow charts for the hybrid optimization-based tool selection system. Key takeaways:

1. **Two-Phase Architecture**: Deterministic scoring (90%+) + LLM tie-breaking (< 10%)
2. **Phase 1 Complete**: Safe evaluator, schemas, loader, profiles (40 tests passing)
3. **Phase 2 Next**: Feature normalization, scoring, policy enforcement
4. **Security First**: AST-based parsing, no eval(), hard policy constraints
5. **Learning Loop**: Telemetry feedback for continuous improvement

**Status:** Phase 1 Complete ✅, Ready for Phase 2 🔄

---

**Document Version:** 1.0  
**Last Updated:** 2025-01-XX  
**Related Docs:**
- `/HYBRID_OPTIMIZATION_IMPLEMENTATION_PLAN.md` (Complete plan)
- `/HYBRID_OPTIMIZATION_PHASE1_COMPLETE.md` (Phase 1 summary)