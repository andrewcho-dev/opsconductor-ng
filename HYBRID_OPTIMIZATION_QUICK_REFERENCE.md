# Hybrid Optimization: Quick Reference Guide

## 📚 Documentation Index

| Document | Purpose | Status |
|----------|---------|--------|
| `HYBRID_OPTIMIZATION_IMPLEMENTATION_PLAN.md` | Complete implementation plan (all phases) | ✅ Complete |
| `HYBRID_OPTIMIZATION_PHASE1_COMPLETE.md` | Phase 1 summary and results | ✅ Complete |
| `HYBRID_OPTIMIZATION_ARCHITECTURE.md` | Visual diagrams and flow charts | ✅ Complete |
| `HYBRID_OPTIMIZATION_QUICK_REFERENCE.md` | This file - quick reference | ✅ Complete |

---

## 🎯 What Is This?

A **hybrid optimization-based tool selection system** that makes intelligent trade-offs between speed, accuracy, cost, complexity, and completeness when selecting tools.

**Two-Phase Architecture:**
1. **Deterministic Pre-Selector** (90%+ of cases): Mathematical scoring as source of truth
2. **LLM Tie-Breaker** (< 10% of cases): Human-like reasoning for ambiguous cases

---

## ✅ Phase 1: Complete (40 tests passing)

### What Was Built

| Component | File | Lines | Tests | Status |
|-----------|------|-------|-------|--------|
| Safe Math Evaluator | `safe_math_eval.py` | 217 | 24 | ✅ |
| Pydantic Schemas | `optimization_schemas.py` | 234 | - | ✅ |
| Profile Loader | `profile_loader.py` | 186 | 16 | ✅ |
| Tool Profiles (YAML) | `tool_optimization_profiles.yaml` | 318 | - | ✅ |
| **Total** | **4 files** | **955 lines** | **40 tests** | **✅** |

### Key Features

- ✅ **Security**: AST-based parser (no `eval()` vulnerabilities)
- ✅ **Validation**: All expressions validated at load time
- ✅ **Inheritance**: Tool defaults → capability → pattern
- ✅ **Flexibility**: Runtime context (N, pages, p95_latency)
- ✅ **Performance**: Cached profile loading

### Tool Profiles Created

| Tool | Patterns | Description |
|------|----------|-------------|
| `asset-service-query` | 4 | Fast cached database queries |
| `asset-direct-poll` | 2 | Real-time SSH/API polling |
| `info_display` | 1 | Static documentation |
| **Total** | **7** | **3 tools profiled** |

---

## 🔄 Phase 2: Next Steps

### What to Build

| Component | File | Estimated Lines | Tests | Priority |
|-----------|------|-----------------|-------|----------|
| Feature Normalizer | `feature_normalizer.py` | ~150 | 15 | 🔥 High |
| Deterministic Scorer | `deterministic_scorer.py` | ~200 | 20 | 🔥 High |
| Policy Enforcer | `policy_enforcer.py` | ~180 | 15 | 🔥 High |
| **Total** | **3 files** | **~530 lines** | **50 tests** | - |

### Normalization Functions

```python
# Time: 50ms (best) → 60s (worst)
normalize_time(time_ms: float) -> float  # [0,1], log scale

# Cost: $0 (best) → $10 (worst)
normalize_cost(cost: float) -> float  # [0,1], linear scale

# Complexity: 0 (simple) → 1 (complex)
normalize_complexity(complexity: float) -> float  # [0,1], inverted
```

### Scoring Formula

```python
score = (
    w_speed × normalize_time(time_ms) +
    w_accuracy × accuracy +
    w_cost × normalize_cost(cost) +
    w_complexity × normalize_complexity(complexity) +
    w_completeness × completeness
) / sum(weights)
```

---

## 📖 API Reference

### SafeMathEvaluator

```python
from pipeline.stages.stage_b.safe_math_eval import SafeMathEvaluator

# Create evaluator
evaluator = SafeMathEvaluator("120 + 0.02 * N")

# Evaluate with context
result = evaluator.evaluate({"N": 100})  # 122.0

# Whitelisted operations: +, -, *, /, //, %, **
# Whitelisted functions: log, sqrt, min, max, abs, ceil, floor, exp
# Whitelisted constants: pi, e
# Whitelisted variables: N, pages, p95_latency, cost, time_ms
```

### ProfileLoader

```python
from pipeline.stages.stage_b.profile_loader import ProfileLoader

# Load profiles (cached)
loader = ProfileLoader()
config = loader.load_profiles()

# Get specific tool
tool = loader.get_tool_profile("asset-service-query")

# Get all tools
all_tools = loader.get_all_tools()

# Validate expressions
context = {"N": 100, "pages": 1, "p95_latency": 1000}
loader.validate_all_expressions(context)  # Raises if any fail

# Force reload (for testing)
config = loader.load_profiles(force_reload=True)
```

### UserPreferences

```python
from pipeline.stages.stage_b.optimization_schemas import UserPreferences

# Create with mode
prefs = UserPreferences(mode="fast")
# speed=0.4, accuracy=0.2, cost=0.2, complexity=0.1, completeness=0.1

# Available modes: "fast", "balanced", "accurate", "thorough"

# Custom weights
prefs = UserPreferences(
    mode="custom",
    speed=0.5,
    accuracy=0.3,
    cost=0.1,
    complexity=0.05,
    completeness=0.05
)
```

---

## 🧪 Testing

### Run All Tests

```bash
# Phase 1 tests (40 tests)
pytest tests/test_safe_math_eval.py -v      # 24 tests
pytest tests/test_profile_loader.py -v      # 16 tests

# All tests
pytest tests/test_safe_math_eval.py tests/test_profile_loader.py -v
```

### Test Coverage

```bash
# With coverage report
pytest tests/test_safe_math_eval.py tests/test_profile_loader.py --cov=pipeline/stages/stage_b --cov-report=html
```

### Real-World Scenarios

```python
# Test: Fast count query
loader = ProfileLoader()
tool = loader.get_tool_profile("asset-service-query")
pattern = tool.capabilities["asset_query"].patterns["count_aggregate"]

context = {"N": 100, "pages": 1, "p95_latency": 1000}
evaluator = SafeMathEvaluator(pattern.performance.time_ms_formula)
time_ms = evaluator.evaluate(context)  # 122ms

assert time_ms < 200  # Fast enough
assert pattern.preference_scores.speed >= 0.9  # High speed score
```

---

## 📝 YAML Profile Format

### Structure

```yaml
tools:
  tool-name:
    defaults:  # Optional tool-level defaults
      performance:
        complexity: 0.3
      policy:
        production_safe: true
    
    capabilities:
      capability-name:
        patterns:
          pattern-name:
            performance:
              time_ms_formula: "120 + 0.02 * N"
              cost_formula: "0.001 * N + 0.05"
              complexity: 0.3  # [0,1]
            
            preference_scores:
              speed: 0.95      # [0,1]
              accuracy: 0.6    # [0,1]
              cost: 0.95       # [0,1]
              complexity: 0.7  # [0,1]
              completeness: 0.5  # [0,1]
            
            policy:
              max_cost: 10.0
              requires_approval: false
              production_safe: true
              requires_background_if: "N > 50"
            
            limitations:
              - "Cached data (may be stale)"
```

### Expression Variables

| Variable | Type | Description | Example |
|----------|------|-------------|---------|
| `N` | int | Number of assets | 100 |
| `pages` | int | Number of pages | 2 |
| `p95_latency` | float | P95 latency (ms) | 1000 |
| `cost` | float | Cost per unit | 0.05 |
| `time_ms` | float | Time in milliseconds | 122 |

### Expression Examples

```yaml
# Linear scaling
time_ms_formula: "120 + 0.02 * N"

# Log scaling (for large N)
time_ms_formula: "3000 + 400 * log(N) + p95_latency * 1.2"

# Paginated
time_ms_formula: "200 + 2 * N + 500 * pages"

# Constant
time_ms_formula: "100"

# Complex
time_ms_formula: "min(5000, 100 + 0.5 * N + 200 * sqrt(pages))"
```

---

## 🔒 Security Features

### What's Protected

✅ **No code injection**: AST-based parsing, no `eval()`  
✅ **Whitelisted operations**: Only safe math operations  
✅ **Whitelisted functions**: Only safe math functions  
✅ **Whitelisted variables**: Only known context variables  
✅ **Depth limits**: Max AST depth of 20  
✅ **Exponent bounds**: Exponents limited to ±100  
✅ **Division-by-zero**: Protected with error handling  

### What's Blocked

❌ **Imports**: `import os` → Error  
❌ **Exec/Eval**: `eval("...")` → Error  
❌ **File access**: `open("file")` → Error  
❌ **Attribute access**: `obj.attr` → Error  
❌ **Arbitrary functions**: `custom_func()` → Error  
❌ **Undefined variables**: `unknown_var` → Error  

---

## 🎨 Preference Modes

| Mode | Speed | Accuracy | Cost | Complexity | Completeness | Use Case |
|------|-------|----------|------|------------|--------------|----------|
| **fast** | 0.4 | 0.2 | 0.2 | 0.1 | 0.1 | Quick queries, dashboards |
| **balanced** | 0.25 | 0.25 | 0.2 | 0.15 | 0.15 | General purpose |
| **accurate** | 0.15 | 0.4 | 0.15 | 0.15 | 0.15 | Verification, audits |
| **thorough** | 0.1 | 0.2 | 0.1 | 0.1 | 0.5 | Reports, analysis |

---

## 🚀 Performance Targets

| Metric | Target | Current | Status |
|--------|--------|---------|--------|
| Profile loading (cached) | < 100ms | ~50ms | ✅ |
| Expression evaluation | < 1ms | ~0.1ms | ✅ |
| Selection latency (deterministic) | < 50ms | TBD | 🔄 |
| Selection latency (LLM) | < 500ms | TBD | 🔄 |
| Test suite runtime | < 5s | ~2s | ✅ |

---

## 📊 Telemetry Schema (Phase 6)

```sql
CREATE TABLE tool_selection_telemetry (
    id SERIAL PRIMARY KEY,
    timestamp TIMESTAMP NOT NULL DEFAULT NOW(),
    query TEXT NOT NULL,
    
    -- Preferences
    preference_mode VARCHAR(50),
    preference_speed FLOAT,
    preference_accuracy FLOAT,
    preference_cost FLOAT,
    preference_complexity FLOAT,
    preference_completeness FLOAT,
    
    -- Selection
    selected_tool VARCHAR(255) NOT NULL,
    selected_pattern VARCHAR(255) NOT NULL,
    selection_method VARCHAR(50) NOT NULL,  -- "deterministic" or "llm_tiebreaker"
    is_ambiguous BOOLEAN NOT NULL,
    
    -- Predictions
    predicted_time_ms FLOAT,
    predicted_cost FLOAT,
    
    -- Actuals (filled by Stage E)
    actual_time_ms FLOAT,
    actual_cost FLOAT,
    actual_success BOOLEAN,
    
    -- User feedback
    user_satisfaction INT,  -- 1-5
    
    -- Metadata
    alternatives JSONB,
    context JSONB
);
```

---

## 🐛 Troubleshooting

### Expression Validation Fails

```python
# Error: "Undefined variable: X"
# Solution: Use only whitelisted variables (N, pages, p95_latency, cost, time_ms)

# Error: "Unsupported operation: Import"
# Solution: Remove imports, use only whitelisted operations

# Error: "Maximum depth exceeded"
# Solution: Simplify expression (max depth: 20)
```

### Profile Loading Fails

```python
# Error: "Pattern count exceeds limit"
# Solution: Max 5 patterns per capability

# Error: "Preference score out of range"
# Solution: All scores must be in [0,1]

# Error: "Invalid YAML syntax"
# Solution: Check YAML indentation and syntax
```

### Test Failures

```bash
# Run specific test
pytest tests/test_safe_math_eval.py::TestSafeMathEvaluator::test_basic_arithmetic -v

# Run with verbose output
pytest tests/test_safe_math_eval.py -vv

# Run with print statements
pytest tests/test_safe_math_eval.py -s
```

---

## 📦 Dependencies

### Python Packages

```txt
pydantic>=2.0.0      # Schema validation
pyyaml>=6.0          # YAML parsing
pytest>=7.0.0        # Testing
```

### Internal Dependencies

```
SafeMathEvaluator
  └── (no dependencies)

ProfileLoader
  ├── SafeMathEvaluator
  └── optimization_schemas (Pydantic models)

optimization_schemas
  └── pydantic
```

---

## 🔮 Future Phases

### Phase 3: Preference Detection & Candidate Enumeration
- Detect user preferences from query text
- Enumerate candidate tools matching capabilities
- Estimate runtime context (N, pages, p95_latency)

### Phase 4: Ambiguity Detection & LLM Tie-Breaker
- Detect ambiguous cases (score difference < ε)
- Generate clarifying questions
- Use LLM for tie-breaking

### Phase 5: Stage B Integration
- Integrate hybrid selector into Stage B
- Feature flag for gradual rollout
- Backward compatibility with legacy logic

### Phase 6: Telemetry & Learning Loop
- Log predictions vs actuals
- Nightly analysis script
- Coefficient tuning recommendations

### Phase 7: UI Integration
- User preference controls
- Selection justification display
- A/B testing framework

---

## 📞 Support

### Questions?

1. **Implementation Plan**: See `HYBRID_OPTIMIZATION_IMPLEMENTATION_PLAN.md`
2. **Architecture Diagrams**: See `HYBRID_OPTIMIZATION_ARCHITECTURE.md`
3. **Phase 1 Summary**: See `HYBRID_OPTIMIZATION_PHASE1_COMPLETE.md`
4. **Code Documentation**: Check inline docstrings in modules

### Common Questions

**Q: Why AST-based evaluation instead of `eval()`?**  
A: Security. `eval()` can execute arbitrary code, AST parsing is safe.

**Q: Why YAML instead of Python for profiles?**  
A: Easier for non-developers to edit, Git-friendly, supports inheritance.

**Q: Why max 5 patterns per capability?**  
A: Prevent sprawl, keep profiles manageable, faster enumeration.

**Q: Why log scale for time normalization?**  
A: Humans perceive time logarithmically (100ms vs 200ms feels bigger than 5s vs 5.1s).

**Q: Why ε = 0.08 for ambiguity threshold?**  
A: Balance between avoiding excessive LLM calls and catching genuinely ambiguous cases.

---

## 🎯 Quick Start

### 1. Load Profiles

```python
from pipeline.stages.stage_b.profile_loader import ProfileLoader

loader = ProfileLoader()
config = loader.load_profiles()
print(f"Loaded {len(config.tools)} tools")
```

### 2. Evaluate Expression

```python
from pipeline.stages.stage_b.safe_math_eval import SafeMathEvaluator

evaluator = SafeMathEvaluator("120 + 0.02 * N")
result = evaluator.evaluate({"N": 100})
print(f"Estimated time: {result}ms")
```

### 3. Run Tests

```bash
pytest tests/test_safe_math_eval.py tests/test_profile_loader.py -v
```

### 4. Add New Tool Profile

```yaml
# Edit: pipeline/config/tool_optimization_profiles.yaml

tools:
  my-new-tool:
    defaults:
      policy:
        production_safe: true
    capabilities:
      my_capability:
        patterns:
          my_pattern:
            performance:
              time_ms_formula: "100 + 0.01 * N"
              cost_formula: "0.001 * N"
              complexity: 0.2
            preference_scores:
              speed: 0.9
              accuracy: 0.8
              cost: 0.95
              complexity: 0.8
              completeness: 0.7
```

### 5. Validate New Profile

```python
loader = ProfileLoader()
context = {"N": 100, "pages": 1, "p95_latency": 1000}
loader.validate_all_expressions(context)  # Raises if invalid
print("✅ All expressions valid!")
```

---

## 📈 Success Metrics

### Phase 1 (Complete)
- ✅ 40/40 tests passing
- ✅ 3 tools profiled with 7 patterns
- ✅ Zero security vulnerabilities
- ✅ Profile loading < 100ms

### Phase 2 (Target)
- 🎯 50 additional tests
- 🎯 Feature normalization working
- 🎯 Deterministic scoring < 50ms
- 🎯 Policy enforcement 100% effective

### Overall (Target)
- 🎯 180 total tests passing
- 🎯 10+ tools profiled
- 🎯 90%+ deterministic selection rate
- 🎯 < 10% LLM tie-breaker usage
- 🎯 20% cost savings
- 🎯 30% speed improvement
- 🎯 4.0/5.0 user satisfaction

---

**Document Version:** 1.0  
**Last Updated:** 2025-01-XX  
**Status:** Phase 1 Complete ✅  
**Next Phase:** Phase 2 (Feature Normalization & Scoring) 🔄