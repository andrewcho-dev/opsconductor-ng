# Hybrid Optimization-Based Tool Selection: Complete Implementation Plan

## Executive Summary

This document outlines the complete implementation plan for a hybrid optimization-based tool selection system in OpsConductor. The system addresses the core challenge of making human-like trade-off decisions when selecting tools based on multiple competing factors: speed, accuracy, cost, complexity, and completeness.

### Core Architecture

**Two-Phase Hybrid Approach:**
1. **Deterministic Pre-Selector** (Phase 1): Mathematical scoring engine as source of truth
2. **LLM Tie-Breaker** (Phase 2): Used only for ambiguous cases and justification generation

This architecture ensures:
- Predictable, auditable decisions for clear-cut cases
- Human-like reasoning for edge cases
- No LLM hallucination in critical path
- Hard policy enforcement in code (never bypassable by LLM)

---

## Problem Statement

### Current State
OpsConductor's Stage B (Tool Selection) currently uses simple heuristics or LLM-only selection, which leads to:
- Inconsistent tool choices for similar queries
- No consideration of performance trade-offs
- Inability to respect user preferences (fast vs accurate)
- No cost awareness
- No policy enforcement (budget limits, approval requirements)

### Target State
A hybrid system that:
1. **Evaluates** all candidate tools against user preferences using mathematical scoring
2. **Normalizes** features (time, cost, complexity) to comparable scales
3. **Enforces** hard policy constraints (budget, approval, production safety)
4. **Detects** ambiguous cases where top candidates are too close to call
5. **Delegates** to LLM only for tie-breaking and justification
6. **Learns** from actual performance via telemetry feedback loop

---

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                         Stage B: Tool Selection                  │
├─────────────────────────────────────────────────────────────────┤
│                                                                   │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │  1. Preference Detection (from user query)                │  │
│  │     - Extract mode: fast/balanced/accurate/thorough       │  │
│  │     - Detect explicit preferences (cost-conscious, etc)   │  │
│  │     - Map to weight vector [speed, accuracy, cost, ...]   │  │
│  └──────────────────────────────────────────────────────────┘  │
│                              ↓                                   │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │  2. Candidate Enumeration                                 │  │
│  │     - Load tool profiles from YAML                        │  │
│  │     - Match capabilities to query intent                  │  │
│  │     - Estimate runtime context (N, pages, p95_latency)    │  │
│  │     - Evaluate expressions (time_ms, cost, etc)           │  │
│  └──────────────────────────────────────────────────────────┘  │
│                              ↓                                   │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │  3. Feature Normalization                                 │  │
│  │     - time_ms → [0,1] via bounded log transform           │  │
│  │     - cost → [0,1] via bounded linear transform           │  │
│  │     - complexity → [0,1] (already normalized)             │  │
│  │     - Invert where needed (lower is better)               │  │
│  └──────────────────────────────────────────────────────────┘  │
│                              ↓                                   │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │  4. Policy Gate Enforcement (HARD CONSTRAINTS)            │  │
│  │     - Filter out tools exceeding max_cost                 │  │
│  │     - Flag tools requiring approval                       │  │
│  │     - Check production_safe flag                          │  │
│  │     - Evaluate requires_background_if conditions          │  │
│  └──────────────────────────────────────────────────────────┘  │
│                              ↓                                   │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │  5. Deterministic Scoring                                 │  │
│  │     - Compute weighted sum: Σ(weight_i × feature_i)       │  │
│  │     - Sort candidates by score (descending)               │  │
│  │     - Identify top-2 candidates                           │  │
│  └──────────────────────────────────────────────────────────┘  │
│                              ↓                                   │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │  6. Ambiguity Detection                                   │  │
│  │     - If |score_1 - score_2| < ε (0.08):                 │  │
│  │       → AMBIGUOUS: delegate to LLM tie-breaker            │  │
│  │     - Else:                                               │  │
│  │       → CLEAR: select top candidate deterministically     │  │
│  └──────────────────────────────────────────────────────────┘  │
│                              ↓                                   │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │  7. LLM Tie-Breaker (only if ambiguous)                   │  │
│  │     - Compact prompt with top-2 candidates                │  │
│  │     - Include user query context                          │  │
│  │     - Request: choice + justification                     │  │
│  │     - Fallback: use deterministic winner if LLM fails     │  │
│  └──────────────────────────────────────────────────────────┘  │
│                              ↓                                   │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │  8. Output Generation                                     │  │
│  │     - Selected tool + pattern                             │  │
│  │     - execution_mode_hint (immediate/background/approval) │  │
│  │     - sla_class (interactive/batch/background)            │  │
│  │     - Justification (from LLM or deterministic reason)    │  │
│  │     - Telemetry metadata (scores, alternatives)           │  │
│  └──────────────────────────────────────────────────────────┘  │
│                              ↓                                   │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │  9. Telemetry Logging                                     │  │
│  │     - Log: predicted time_ms, cost, complexity            │  │
│  │     - Log: actual time_ms, cost (from Stage E)            │  │
│  │     - Log: user satisfaction (implicit/explicit)          │  │
│  │     - Enable nightly coefficient tuning                   │  │
│  └──────────────────────────────────────────────────────────┘  │
│                                                                   │
└─────────────────────────────────────────────────────────────────┘
```

---

## Phase Breakdown

### ✅ Phase 1: Foundation (COMPLETED)

**Status:** Complete and tested (40 tests passing)

**Components Implemented:**
1. **Safe Math Expression Evaluator** (`safe_math_eval.py`)
   - AST-based parser (no `eval()` vulnerabilities)
   - Whitelisted operations, functions, constants, variables
   - Security: max depth, exponent bounds, division-by-zero protection
   - Supports runtime context: N, pages, p95_latency, cost, time_ms

2. **Pydantic Schemas** (`optimization_schemas.py`)
   - `PolicyConfig`: Hard constraints (max_cost, approval, production_safe)
   - `PreferenceMatchScores`: Normalized scores [0,1] for 5 dimensions
   - `PatternProfile`: Complete profile for a usage pattern
   - `CapabilityProfile`: Container with max 5 patterns per capability
   - `ToolProfile`: Tool-level defaults with inheritance
   - `OptimizationProfilesConfig`: Root config with validation
   - `UserPreferences`: Preference weights with mode support
   - `ToolCandidate`: Evaluated candidate with scores and hints

3. **YAML Profile Loader** (`profile_loader.py`)
   - Loads from `/pipeline/config/tool_optimization_profiles.yaml`
   - Validates all expressions at load time
   - Applies inheritance: tool defaults → capability → pattern
   - Caching for performance

4. **Tool Profiles** (`tool_optimization_profiles.yaml`)
   - **asset-service-query**: 4 patterns (count, list, single, detailed)
   - **asset-direct-poll**: 2 patterns (parallel, single)
   - **info_display**: 1 pattern (general info)
   - Total: 3 tools, 7 patterns

5. **Comprehensive Tests**
   - `test_safe_math_eval.py`: 24 tests (functionality + security)
   - `test_profile_loader.py`: 16 tests (loading + validation + scenarios)

**Key Decisions:**
- AST-based evaluation for security
- Expression strings in YAML for flexibility
- Inheritance model to reduce duplication
- Pydantic validation at load time
- Pattern count limit (5 per capability)

---

### 🔄 Phase 2: Feature Normalization & Deterministic Scoring (NEXT)

**Goal:** Implement the mathematical scoring engine that serves as source of truth.

#### 2.1 Feature Normalization Module

**File:** `/pipeline/stages/stage_b/feature_normalizer.py`

**Responsibilities:**
- Normalize `time_ms` to [0,1] using bounded log transform
- Normalize `cost` to [0,1] using bounded linear transform
- Normalize `complexity` (already [0,1] in profiles)
- Invert features where lower is better (time, cost, complexity)
- Handle edge cases (zero values, missing data)

**Normalization Functions:**

```python
# Time normalization (log scale, lower is better)
# Range: 50ms (best) to 60000ms (worst)
def normalize_time(time_ms: float) -> float:
    """
    Normalize time to [0,1] where 1 is best (fastest).
    Uses log scale because humans perceive time logarithmically.
    """
    MIN_TIME = 50.0    # 50ms = instant (score 1.0)
    MAX_TIME = 60000.0 # 60s = very slow (score 0.0)
    
    if time_ms <= MIN_TIME:
        return 1.0
    if time_ms >= MAX_TIME:
        return 0.0
    
    # Log transform, then normalize to [0,1]
    log_time = math.log(time_ms)
    log_min = math.log(MIN_TIME)
    log_max = math.log(MAX_TIME)
    
    normalized = 1.0 - (log_time - log_min) / (log_max - log_min)
    return max(0.0, min(1.0, normalized))

# Cost normalization (linear scale, lower is better)
# Range: $0 (best) to $10 (worst)
def normalize_cost(cost: float) -> float:
    """
    Normalize cost to [0,1] where 1 is best (cheapest).
    Uses linear scale.
    """
    MIN_COST = 0.0   # Free (score 1.0)
    MAX_COST = 10.0  # $10 per query (score 0.0)
    
    if cost <= MIN_COST:
        return 1.0
    if cost >= MAX_COST:
        return 0.0
    
    normalized = 1.0 - (cost - MIN_COST) / (MAX_COST - MIN_COST)
    return max(0.0, min(1.0, normalized))

# Complexity normalization (already [0,1], lower is better)
def normalize_complexity(complexity: float) -> float:
    """
    Normalize complexity to [0,1] where 1 is best (simplest).
    Complexity in profiles is already [0,1], just invert.
    """
    return 1.0 - complexity
```

**Tests:** `test_feature_normalizer.py`
- Test boundary conditions (min, max, zero)
- Test log vs linear scaling
- Test inversion logic
- Test edge cases (negative, NaN, infinity)

#### 2.2 Deterministic Scorer Module

**File:** `/pipeline/stages/stage_b/deterministic_scorer.py`

**Responsibilities:**
- Accept list of `ToolCandidate` objects with evaluated metrics
- Accept `UserPreferences` with weights
- Normalize all features
- Compute weighted sum: `score = Σ(weight_i × normalized_feature_i)`
- Sort candidates by score (descending)
- Return ranked list with scores

**Scoring Algorithm:**

```python
def score_candidate(
    candidate: ToolCandidate,
    preferences: UserPreferences,
    normalizer: FeatureNormalizer
) -> float:
    """
    Compute weighted score for a candidate.
    
    Score = w_speed × norm_speed + 
            w_accuracy × norm_accuracy + 
            w_cost × norm_cost + 
            w_complexity × norm_complexity + 
            w_completeness × norm_completeness
    
    All normalized features are in [0,1] where 1 is best.
    """
    # Normalize features (invert where lower is better)
    norm_speed = normalizer.normalize_time(candidate.estimated_time_ms)
    norm_cost = normalizer.normalize_cost(candidate.estimated_cost)
    norm_complexity = normalizer.normalize_complexity(candidate.complexity)
    
    # These are already [0,1] in profiles
    norm_accuracy = candidate.preference_scores.accuracy
    norm_completeness = candidate.preference_scores.completeness
    
    # Weighted sum
    score = (
        preferences.speed * norm_speed +
        preferences.accuracy * norm_accuracy +
        preferences.cost * norm_cost +
        preferences.complexity * norm_complexity +
        preferences.completeness * norm_completeness
    )
    
    # Normalize by sum of weights (in case they don't sum to 1.0)
    total_weight = (
        preferences.speed + 
        preferences.accuracy + 
        preferences.cost + 
        preferences.complexity + 
        preferences.completeness
    )
    
    return score / total_weight if total_weight > 0 else 0.0
```

**Tests:** `test_deterministic_scorer.py`
- Test scoring with different preference profiles
- Test ranking (order preservation)
- Test edge cases (all zeros, all ones)
- Test weight normalization
- Test real-world scenarios (fast mode, accurate mode, balanced)

#### 2.3 Policy Enforcer Module

**File:** `/pipeline/stages/stage_b/policy_enforcer.py`

**Responsibilities:**
- Filter candidates that violate hard constraints
- Evaluate `requires_background_if` expressions
- Check `max_cost` limits
- Check `production_safe` flag
- Flag candidates requiring approval
- Return filtered list + policy violations

**Policy Checks:**

```python
class PolicyViolation(BaseModel):
    """Represents a policy violation."""
    candidate: ToolCandidate
    violation_type: str  # "max_cost", "not_production_safe", "requires_approval"
    message: str

class PolicyEnforcer:
    """Enforces hard policy constraints."""
    
    def enforce_policies(
        self,
        candidates: List[ToolCandidate],
        context: Dict[str, Any],
        environment: str = "production"
    ) -> Tuple[List[ToolCandidate], List[PolicyViolation]]:
        """
        Filter candidates based on policy constraints.
        
        Returns:
            (allowed_candidates, violations)
        """
        allowed = []
        violations = []
        
        for candidate in candidates:
            policy = candidate.policy
            
            # Check max_cost
            if policy.max_cost and candidate.estimated_cost > policy.max_cost:
                violations.append(PolicyViolation(
                    candidate=candidate,
                    violation_type="max_cost",
                    message=f"Cost ${candidate.estimated_cost:.2f} exceeds limit ${policy.max_cost:.2f}"
                ))
                continue
            
            # Check production_safe
            if environment == "production" and not policy.production_safe:
                violations.append(PolicyViolation(
                    candidate=candidate,
                    violation_type="not_production_safe",
                    message=f"Tool not approved for production use"
                ))
                continue
            
            # Check requires_background_if
            if policy.requires_background_if:
                try:
                    evaluator = SafeMathEvaluator(policy.requires_background_if)
                    should_background = evaluator.evaluate(context)
                    if should_background:
                        candidate.execution_mode_hint = "background"
                        candidate.sla_class = "background"
                except Exception as e:
                    # If evaluation fails, be conservative
                    candidate.execution_mode_hint = "background"
            
            # Check requires_approval
            if policy.requires_approval:
                candidate.execution_mode_hint = "approval_required"
            
            allowed.append(candidate)
        
        return allowed, violations
```

**Tests:** `test_policy_enforcer.py`
- Test max_cost filtering
- Test production_safe filtering
- Test requires_background_if evaluation
- Test requires_approval flagging
- Test multiple violations
- Test context-dependent policies

---

### 🔄 Phase 3: Preference Detection & Candidate Enumeration

**Goal:** Extract user preferences from query and enumerate candidate tools.

#### 3.1 Preference Detector Module

**File:** `/pipeline/stages/stage_b/preference_detector.py`

**Responsibilities:**
- Parse user query for preference signals
- Detect mode keywords: "quick", "fast", "accurate", "thorough", "detailed"
- Detect cost signals: "cheap", "expensive", "cost-effective"
- Detect complexity signals: "simple", "comprehensive"
- Map to `UserPreferences` object with weights
- Support explicit mode override

**Detection Heuristics:**

```python
class PreferenceDetector:
    """Detects user preferences from query text."""
    
    # Mode keywords
    FAST_KEYWORDS = ["quick", "fast", "rapid", "immediate", "asap"]
    ACCURATE_KEYWORDS = ["accurate", "precise", "exact", "verify", "double-check"]
    THOROUGH_KEYWORDS = ["thorough", "complete", "comprehensive", "detailed", "all"]
    BALANCED_KEYWORDS = ["balanced", "reasonable", "moderate"]
    
    # Cost keywords
    CHEAP_KEYWORDS = ["cheap", "free", "cost-effective", "economical"]
    EXPENSIVE_OK_KEYWORDS = ["expensive ok", "cost no object", "spare no expense"]
    
    # Complexity keywords
    SIMPLE_KEYWORDS = ["simple", "basic", "straightforward", "easy"]
    COMPLEX_OK_KEYWORDS = ["complex ok", "advanced", "sophisticated"]
    
    def detect_preferences(
        self,
        query: str,
        explicit_mode: Optional[str] = None
    ) -> UserPreferences:
        """
        Detect user preferences from query text.
        
        Args:
            query: User query text
            explicit_mode: Override mode ("fast", "balanced", "accurate", "thorough")
        
        Returns:
            UserPreferences object with detected weights
        """
        query_lower = query.lower()
        
        # Start with balanced defaults
        preferences = UserPreferences(mode="balanced")
        
        # Override with explicit mode if provided
        if explicit_mode:
            preferences = UserPreferences(mode=explicit_mode)
        
        # Adjust based on keywords
        if any(kw in query_lower for kw in self.FAST_KEYWORDS):
            preferences.speed = min(1.0, preferences.speed + 0.2)
        
        if any(kw in query_lower for kw in self.ACCURATE_KEYWORDS):
            preferences.accuracy = min(1.0, preferences.accuracy + 0.2)
        
        if any(kw in query_lower for kw in self.THOROUGH_KEYWORDS):
            preferences.completeness = min(1.0, preferences.completeness + 0.2)
        
        if any(kw in query_lower for kw in self.CHEAP_KEYWORDS):
            preferences.cost = min(1.0, preferences.cost + 0.2)
        
        if any(kw in query_lower for kw in self.SIMPLE_KEYWORDS):
            preferences.complexity = min(1.0, preferences.complexity + 0.2)
        
        # Normalize weights to sum to 1.0
        total = (preferences.speed + preferences.accuracy + 
                 preferences.cost + preferences.complexity + 
                 preferences.completeness)
        
        if total > 0:
            preferences.speed /= total
            preferences.accuracy /= total
            preferences.cost /= total
            preferences.complexity /= total
            preferences.completeness /= total
        
        return preferences
```

**Tests:** `test_preference_detector.py`
- Test mode detection (fast, accurate, thorough, balanced)
- Test keyword detection
- Test explicit mode override
- Test weight normalization
- Test real-world queries

#### 3.2 Candidate Enumerator Module

**File:** `/pipeline/stages/stage_b/candidate_enumerator.py`

**Responsibilities:**
- Load tool profiles from YAML
- Match capabilities to query intent (from Stage A)
- Estimate runtime context (N, pages, p95_latency)
- Evaluate all expressions (time_ms, cost, etc.)
- Build list of `ToolCandidate` objects
- Handle evaluation errors gracefully

**Enumeration Algorithm:**

```python
class CandidateEnumerator:
    """Enumerates candidate tools for a query."""
    
    def __init__(self, profile_loader: ProfileLoader):
        self.profile_loader = profile_loader
    
    def enumerate_candidates(
        self,
        required_capabilities: List[str],
        context: Dict[str, Any]
    ) -> List[ToolCandidate]:
        """
        Enumerate all candidate tools that match required capabilities.
        
        Args:
            required_capabilities: List of capability names (e.g., ["asset_query"])
            context: Runtime context (N, pages, p95_latency, etc.)
        
        Returns:
            List of ToolCandidate objects with evaluated metrics
        """
        candidates = []
        config = self.profile_loader.load_profiles()
        
        for tool_name, tool_profile in config.tools.items():
            for capability_name, capability in tool_profile.capabilities.items():
                # Check if this capability matches requirements
                if capability_name not in required_capabilities:
                    continue
                
                for pattern_name, pattern in capability.patterns.items():
                    try:
                        # Evaluate expressions
                        time_ms = self._evaluate_expression(
                            pattern.performance.time_ms_formula,
                            context
                        )
                        cost = self._evaluate_expression(
                            pattern.performance.cost_formula,
                            context
                        )
                        
                        # Build candidate
                        candidate = ToolCandidate(
                            tool_name=tool_name,
                            capability_name=capability_name,
                            pattern_name=pattern_name,
                            estimated_time_ms=time_ms,
                            estimated_cost=cost,
                            complexity=pattern.performance.complexity,
                            preference_scores=pattern.preference_scores,
                            policy=pattern.policy,
                            limitations=pattern.limitations,
                            score=0.0,  # Will be computed later
                            execution_mode_hint="immediate",
                            sla_class="interactive"
                        )
                        
                        candidates.append(candidate)
                    
                    except Exception as e:
                        # Log error but continue
                        logger.warning(
                            f"Failed to evaluate pattern {tool_name}.{capability_name}.{pattern_name}: {e}"
                        )
                        continue
        
        return candidates
    
    def _evaluate_expression(
        self,
        formula: str,
        context: Dict[str, Any]
    ) -> float:
        """Evaluate a formula with context."""
        evaluator = SafeMathEvaluator(formula)
        return evaluator.evaluate(context)
```

**Tests:** `test_candidate_enumerator.py`
- Test capability matching
- Test expression evaluation
- Test context estimation
- Test error handling
- Test real-world scenarios

---

### 🔄 Phase 4: Ambiguity Detection & LLM Tie-Breaker

**Goal:** Detect ambiguous cases and delegate to LLM for tie-breaking.

#### 4.1 Ambiguity Detector Module

**File:** `/pipeline/stages/stage_b/ambiguity_detector.py`

**Responsibilities:**
- Compare top-2 candidate scores
- Detect ambiguity: `|score_1 - score_2| < ε`
- Recommend clarifying question if needed
- Return decision: CLEAR or AMBIGUOUS

**Detection Algorithm:**

```python
class AmbiguityDetector:
    """Detects ambiguous tool selection cases."""
    
    EPSILON = 0.08  # Ambiguity threshold (8% difference)
    
    def detect_ambiguity(
        self,
        ranked_candidates: List[ToolCandidate]
    ) -> Tuple[bool, Optional[str]]:
        """
        Detect if top-2 candidates are too close to call.
        
        Args:
            ranked_candidates: List of candidates sorted by score (descending)
        
        Returns:
            (is_ambiguous, clarifying_question)
        """
        if len(ranked_candidates) < 2:
            return False, None
        
        top1 = ranked_candidates[0]
        top2 = ranked_candidates[1]
        
        score_diff = abs(top1.score - top2.score)
        
        if score_diff < self.EPSILON:
            # Ambiguous: generate clarifying question
            question = self._generate_clarifying_question(top1, top2)
            return True, question
        
        return False, None
    
    def _generate_clarifying_question(
        self,
        candidate1: ToolCandidate,
        candidate2: ToolCandidate
    ) -> str:
        """
        Generate a single clarifying question to help choose between candidates.
        
        Strategy: Find the dimension with the largest difference.
        """
        # Compare normalized features
        diffs = {
            "speed": abs(
                self._normalize_time(candidate1.estimated_time_ms) -
                self._normalize_time(candidate2.estimated_time_ms)
            ),
            "accuracy": abs(
                candidate1.preference_scores.accuracy -
                candidate2.preference_scores.accuracy
            ),
            "cost": abs(
                self._normalize_cost(candidate1.estimated_cost) -
                self._normalize_cost(candidate2.estimated_cost)
            ),
            "completeness": abs(
                candidate1.preference_scores.completeness -
                candidate2.preference_scores.completeness
            )
        }
        
        # Find dimension with largest difference
        max_dim = max(diffs, key=diffs.get)
        
        # Generate question based on dimension
        questions = {
            "speed": "Do you need results immediately, or can you wait a bit longer for more accuracy?",
            "accuracy": "Do you need highly accurate real-time data, or is cached data acceptable?",
            "cost": "Are you willing to pay more for better results?",
            "completeness": "Do you need all details, or is a summary sufficient?"
        }
        
        return questions.get(max_dim, "Do you prefer speed or accuracy?")
```

**Tests:** `test_ambiguity_detector.py`
- Test clear cases (large score difference)
- Test ambiguous cases (small score difference)
- Test clarifying question generation
- Test edge cases (single candidate, identical scores)

#### 4.2 LLM Tie-Breaker Module

**File:** `/pipeline/stages/stage_b/llm_tie_breaker.py`

**Responsibilities:**
- Accept top-2 candidates + user query
- Generate compact prompt for LLM
- Request: choice + justification
- Parse LLM response
- Fallback to deterministic winner if LLM fails
- Log LLM decision for telemetry

**Prompt Template:**

```python
TIEBREAKER_PROMPT = """
You are helping select the best tool for a user query. Two tools are equally viable based on mathematical scoring. Please choose the better option and explain why.

USER QUERY: {query}

OPTION A: {tool1_name} - {pattern1_name}
- Estimated time: {time1_ms}ms
- Estimated cost: ${cost1}
- Accuracy: {accuracy1}/1.0
- Completeness: {completeness1}/1.0
- Complexity: {complexity1}/1.0
- Limitations: {limitations1}

OPTION B: {tool2_name} - {pattern2_name}
- Estimated time: {time2_ms}ms
- Estimated cost: ${cost2}
- Accuracy: {accuracy2}/1.0
- Completeness: {completeness2}/1.0
- Complexity: {complexity2}/1.0
- Limitations: {limitations2}

Please respond in JSON format:
{{
  "choice": "A" or "B",
  "justification": "Brief explanation (1-2 sentences)"
}}
"""
```

**Implementation:**

```python
class LLMTieBreaker:
    """Uses LLM to break ties between top candidates."""
    
    def __init__(self, llm_client):
        self.llm_client = llm_client
    
    def break_tie(
        self,
        query: str,
        candidate1: ToolCandidate,
        candidate2: ToolCandidate
    ) -> Tuple[ToolCandidate, str]:
        """
        Use LLM to choose between two candidates.
        
        Args:
            query: User query
            candidate1: First candidate (deterministic winner)
            candidate2: Second candidate
        
        Returns:
            (chosen_candidate, justification)
        """
        try:
            # Generate prompt
            prompt = self._generate_prompt(query, candidate1, candidate2)
            
            # Call LLM
            response = self.llm_client.generate(
                prompt=prompt,
                temperature=0.3,  # Low temperature for consistency
                max_tokens=200
            )
            
            # Parse response
            result = json.loads(response)
            choice = result["choice"]
            justification = result["justification"]
            
            # Select winner
            if choice == "A":
                return candidate1, justification
            else:
                return candidate2, justification
        
        except Exception as e:
            # Fallback to deterministic winner
            logger.warning(f"LLM tie-breaker failed: {e}. Using deterministic winner.")
            return candidate1, "Selected based on mathematical scoring (LLM unavailable)"
    
    def _generate_prompt(
        self,
        query: str,
        candidate1: ToolCandidate,
        candidate2: ToolCandidate
    ) -> str:
        """Generate compact prompt for LLM."""
        return TIEBREAKER_PROMPT.format(
            query=query,
            tool1_name=candidate1.tool_name,
            pattern1_name=candidate1.pattern_name,
            time1_ms=candidate1.estimated_time_ms,
            cost1=candidate1.estimated_cost,
            accuracy1=candidate1.preference_scores.accuracy,
            completeness1=candidate1.preference_scores.completeness,
            complexity1=candidate1.complexity,
            limitations1=", ".join(candidate1.limitations) if candidate1.limitations else "None",
            tool2_name=candidate2.tool_name,
            pattern2_name=candidate2.pattern_name,
            time2_ms=candidate2.estimated_time_ms,
            cost2=candidate2.estimated_cost,
            accuracy2=candidate2.preference_scores.accuracy,
            completeness2=candidate2.preference_scores.completeness,
            complexity2=candidate2.complexity,
            limitations2=", ".join(candidate2.limitations) if candidate2.limitations else "None"
        )
```

**Tests:** `test_llm_tie_breaker.py`
- Test successful LLM response
- Test LLM failure (fallback to deterministic)
- Test prompt generation
- Test JSON parsing
- Test real-world scenarios

---

### 🔄 Phase 5: Integration with Stage B

**Goal:** Integrate all modules into Stage B selector.

#### 5.1 Hybrid Selector Module

**File:** `/pipeline/stages/stage_b/hybrid_selector.py`

**Responsibilities:**
- Orchestrate all modules
- Accept Stage A output (intent, capabilities)
- Detect preferences from query
- Enumerate candidates
- Enforce policies
- Score candidates
- Detect ambiguity
- Break ties with LLM if needed
- Generate Stage B output

**Main Algorithm:**

```python
class HybridSelector:
    """Hybrid optimization-based tool selector."""
    
    def __init__(
        self,
        profile_loader: ProfileLoader,
        llm_client,
        telemetry_logger
    ):
        self.profile_loader = profile_loader
        self.preference_detector = PreferenceDetector()
        self.candidate_enumerator = CandidateEnumerator(profile_loader)
        self.feature_normalizer = FeatureNormalizer()
        self.policy_enforcer = PolicyEnforcer()
        self.deterministic_scorer = DeterministicScorer()
        self.ambiguity_detector = AmbiguityDetector()
        self.llm_tie_breaker = LLMTieBreaker(llm_client)
        self.telemetry_logger = telemetry_logger
    
    def select_tool(
        self,
        query: str,
        required_capabilities: List[str],
        context: Dict[str, Any],
        explicit_mode: Optional[str] = None
    ) -> ToolSelectionResult:
        """
        Select the best tool for a query using hybrid approach.
        
        Args:
            query: User query text
            required_capabilities: List of required capabilities (from Stage A)
            context: Runtime context (N, pages, p95_latency, etc.)
            explicit_mode: Optional explicit preference mode
        
        Returns:
            ToolSelectionResult with selected tool and metadata
        """
        # 1. Detect preferences
        preferences = self.preference_detector.detect_preferences(
            query, explicit_mode
        )
        
        # 2. Enumerate candidates
        candidates = self.candidate_enumerator.enumerate_candidates(
            required_capabilities, context
        )
        
        if not candidates:
            raise NoViableToolError("No tools match required capabilities")
        
        # 3. Enforce policies
        allowed_candidates, violations = self.policy_enforcer.enforce_policies(
            candidates, context
        )
        
        if not allowed_candidates:
            raise PolicyViolationError(
                f"All candidates violate policies: {violations}"
            )
        
        # 4. Score candidates
        scored_candidates = self.deterministic_scorer.score_candidates(
            allowed_candidates, preferences, self.feature_normalizer
        )
        
        # 5. Detect ambiguity
        is_ambiguous, clarifying_question = self.ambiguity_detector.detect_ambiguity(
            scored_candidates
        )
        
        # 6. Break tie if ambiguous
        if is_ambiguous:
            winner, justification = self.llm_tie_breaker.break_tie(
                query, scored_candidates[0], scored_candidates[1]
            )
            selection_method = "llm_tiebreaker"
        else:
            winner = scored_candidates[0]
            justification = self._generate_deterministic_justification(
                winner, preferences
            )
            selection_method = "deterministic"
        
        # 7. Log telemetry
        self.telemetry_logger.log_selection(
            query=query,
            preferences=preferences,
            candidates=scored_candidates,
            winner=winner,
            selection_method=selection_method,
            is_ambiguous=is_ambiguous
        )
        
        # 8. Return result
        return ToolSelectionResult(
            tool_name=winner.tool_name,
            capability_name=winner.capability_name,
            pattern_name=winner.pattern_name,
            execution_mode_hint=winner.execution_mode_hint,
            sla_class=winner.sla_class,
            justification=justification,
            estimated_time_ms=winner.estimated_time_ms,
            estimated_cost=winner.estimated_cost,
            alternatives=[c.tool_name for c in scored_candidates[1:3]],
            selection_method=selection_method,
            is_ambiguous=is_ambiguous,
            clarifying_question=clarifying_question
        )
    
    def _generate_deterministic_justification(
        self,
        winner: ToolCandidate,
        preferences: UserPreferences
    ) -> str:
        """Generate justification for deterministic selection."""
        # Find dominant preference
        pref_values = {
            "speed": preferences.speed,
            "accuracy": preferences.accuracy,
            "cost": preferences.cost,
            "complexity": preferences.complexity,
            "completeness": preferences.completeness
        }
        dominant = max(pref_values, key=pref_values.get)
        
        justifications = {
            "speed": f"Selected for fast response time (~{winner.estimated_time_ms:.0f}ms)",
            "accuracy": f"Selected for high accuracy ({winner.preference_scores.accuracy:.1f}/1.0)",
            "cost": f"Selected for low cost (${winner.estimated_cost:.2f})",
            "complexity": f"Selected for simplicity",
            "completeness": f"Selected for comprehensive results ({winner.preference_scores.completeness:.1f}/1.0)"
        }
        
        return justifications.get(dominant, "Selected based on overall score")
```

**Tests:** `test_hybrid_selector.py`
- Test end-to-end selection (deterministic)
- Test end-to-end selection (ambiguous → LLM)
- Test policy violations
- Test no viable tools
- Test real-world scenarios

#### 5.2 Update Stage B Selector

**File:** `/pipeline/stages/stage_b/selector.py`

**Changes:**
- Add feature flag: `USE_HYBRID_OPTIMIZATION` (default: False)
- If enabled, use `HybridSelector` instead of current logic
- If disabled, use existing logic (backward compatibility)
- Add telemetry logging

**Integration:**

```python
class ToolSelector:
    """Stage B: Tool Selection"""
    
    def __init__(self, llm_client, telemetry_logger):
        self.llm_client = llm_client
        self.telemetry_logger = telemetry_logger
        
        # Feature flag
        self.use_hybrid = os.getenv("USE_HYBRID_OPTIMIZATION", "false").lower() == "true"
        
        if self.use_hybrid:
            profile_loader = ProfileLoader()
            self.hybrid_selector = HybridSelector(
                profile_loader, llm_client, telemetry_logger
            )
    
    def select_tools(
        self,
        stage_a_output: StageAOutput
    ) -> StageBOutput:
        """Select tools for query."""
        
        if self.use_hybrid:
            # Use hybrid optimization
            result = self.hybrid_selector.select_tool(
                query=stage_a_output.query,
                required_capabilities=stage_a_output.required_capabilities,
                context=self._estimate_context(stage_a_output),
                explicit_mode=stage_a_output.preference_mode
            )
            
            return StageBOutput(
                selected_tools=[result.tool_name],
                execution_mode_hint=result.execution_mode_hint,
                sla_class=result.sla_class,
                justification=result.justification,
                alternatives=result.alternatives
            )
        else:
            # Use existing logic (backward compatibility)
            return self._legacy_select_tools(stage_a_output)
    
    def _estimate_context(self, stage_a_output: StageAOutput) -> Dict[str, Any]:
        """Estimate runtime context for optimization."""
        # TODO: Implement context estimation
        # For now, use defaults
        return {
            "N": 100,  # Assume 100 assets
            "pages": 1,
            "p95_latency": 1000  # 1s p95 latency
        }
```

---

### 🔄 Phase 6: Telemetry & Learning Loop

**Goal:** Log predictions vs actuals for nightly coefficient tuning.

#### 6.1 Telemetry Logger Module

**File:** `/pipeline/stages/stage_b/telemetry_logger.py`

**Responsibilities:**
- Log selection decisions to database
- Log predicted metrics (time_ms, cost)
- Log actual metrics (from Stage E)
- Log user satisfaction (implicit/explicit)
- Support nightly batch analysis

**Schema:**

```sql
CREATE TABLE tool_selection_telemetry (
    id SERIAL PRIMARY KEY,
    timestamp TIMESTAMP NOT NULL DEFAULT NOW(),
    query TEXT NOT NULL,
    user_id VARCHAR(255),
    
    -- Preferences
    preference_mode VARCHAR(50),
    preference_speed FLOAT,
    preference_accuracy FLOAT,
    preference_cost FLOAT,
    preference_complexity FLOAT,
    preference_completeness FLOAT,
    
    -- Selection
    selected_tool VARCHAR(255) NOT NULL,
    selected_capability VARCHAR(255) NOT NULL,
    selected_pattern VARCHAR(255) NOT NULL,
    selection_method VARCHAR(50) NOT NULL,  -- "deterministic" or "llm_tiebreaker"
    is_ambiguous BOOLEAN NOT NULL,
    
    -- Predictions
    predicted_time_ms FLOAT,
    predicted_cost FLOAT,
    predicted_complexity FLOAT,
    
    -- Actuals (filled in by Stage E)
    actual_time_ms FLOAT,
    actual_cost FLOAT,
    actual_success BOOLEAN,
    actual_error TEXT,
    
    -- User feedback
    user_satisfaction INT,  -- 1-5 scale
    user_feedback TEXT,
    
    -- Alternatives
    alternatives JSONB,  -- List of other candidates
    
    -- Metadata
    context JSONB,  -- Runtime context (N, pages, etc.)
    environment VARCHAR(50)  -- "production", "staging", "dev"
);

CREATE INDEX idx_telemetry_timestamp ON tool_selection_telemetry(timestamp);
CREATE INDEX idx_telemetry_tool ON tool_selection_telemetry(selected_tool);
CREATE INDEX idx_telemetry_method ON tool_selection_telemetry(selection_method);
```

**Implementation:**

```python
class TelemetryLogger:
    """Logs tool selection telemetry for learning."""
    
    def __init__(self, db_connection):
        self.db = db_connection
    
    def log_selection(
        self,
        query: str,
        preferences: UserPreferences,
        candidates: List[ToolCandidate],
        winner: ToolCandidate,
        selection_method: str,
        is_ambiguous: bool,
        context: Dict[str, Any] = None,
        user_id: Optional[str] = None
    ) -> int:
        """
        Log a tool selection decision.
        
        Returns:
            telemetry_id for later updates
        """
        alternatives = [
            {
                "tool": c.tool_name,
                "pattern": c.pattern_name,
                "score": c.score,
                "time_ms": c.estimated_time_ms,
                "cost": c.estimated_cost
            }
            for c in candidates[1:5]  # Top 5 alternatives
        ]
        
        query = """
            INSERT INTO tool_selection_telemetry (
                query, user_id, preference_mode,
                preference_speed, preference_accuracy, preference_cost,
                preference_complexity, preference_completeness,
                selected_tool, selected_capability, selected_pattern,
                selection_method, is_ambiguous,
                predicted_time_ms, predicted_cost, predicted_complexity,
                alternatives, context, environment
            ) VALUES (
                %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
            ) RETURNING id
        """
        
        result = self.db.execute(
            query,
            (
                query, user_id, preferences.mode,
                preferences.speed, preferences.accuracy, preferences.cost,
                preferences.complexity, preferences.completeness,
                winner.tool_name, winner.capability_name, winner.pattern_name,
                selection_method, is_ambiguous,
                winner.estimated_time_ms, winner.estimated_cost, winner.complexity,
                json.dumps(alternatives), json.dumps(context or {}),
                os.getenv("ENVIRONMENT", "production")
            )
        )
        
        return result[0]["id"]
    
    def update_actuals(
        self,
        telemetry_id: int,
        actual_time_ms: float,
        actual_cost: float,
        actual_success: bool,
        actual_error: Optional[str] = None
    ):
        """Update telemetry with actual metrics from Stage E."""
        query = """
            UPDATE tool_selection_telemetry
            SET actual_time_ms = %s,
                actual_cost = %s,
                actual_success = %s,
                actual_error = %s
            WHERE id = %s
        """
        
        self.db.execute(
            query,
            (actual_time_ms, actual_cost, actual_success, actual_error, telemetry_id)
        )
    
    def update_user_feedback(
        self,
        telemetry_id: int,
        satisfaction: int,
        feedback: Optional[str] = None
    ):
        """Update telemetry with user feedback."""
        query = """
            UPDATE tool_selection_telemetry
            SET user_satisfaction = %s,
                user_feedback = %s
            WHERE id = %s
        """
        
        self.db.execute(query, (satisfaction, feedback, telemetry_id))
```

#### 6.2 Nightly Analysis Script

**File:** `/scripts/analyze_tool_selection_telemetry.py`

**Responsibilities:**
- Run nightly batch analysis
- Compare predicted vs actual metrics
- Identify systematic biases
- Recommend coefficient adjustments
- Generate report

**Analysis:**

```python
def analyze_prediction_accuracy():
    """Analyze prediction accuracy over last 7 days."""
    
    query = """
        SELECT
            selected_tool,
            selected_pattern,
            AVG(predicted_time_ms) as avg_predicted_time,
            AVG(actual_time_ms) as avg_actual_time,
            AVG(predicted_cost) as avg_predicted_cost,
            AVG(actual_cost) as avg_actual_cost,
            COUNT(*) as sample_count,
            AVG(user_satisfaction) as avg_satisfaction
        FROM tool_selection_telemetry
        WHERE timestamp > NOW() - INTERVAL '7 days'
          AND actual_time_ms IS NOT NULL
        GROUP BY selected_tool, selected_pattern
        HAVING COUNT(*) >= 10  -- Minimum sample size
        ORDER BY sample_count DESC
    """
    
    results = db.execute(query)
    
    for row in results:
        time_error = (row["avg_actual_time"] - row["avg_predicted_time"]) / row["avg_predicted_time"]
        cost_error = (row["avg_actual_cost"] - row["avg_predicted_cost"]) / row["avg_predicted_cost"]
        
        if abs(time_error) > 0.2:  # 20% error threshold
            print(f"WARNING: {row['selected_tool']}.{row['selected_pattern']}")
            print(f"  Time prediction error: {time_error*100:.1f}%")
            print(f"  Recommended adjustment: multiply time coefficient by {1 + time_error:.2f}")
        
        if abs(cost_error) > 0.2:
            print(f"WARNING: {row['selected_tool']}.{row['selected_pattern']}")
            print(f"  Cost prediction error: {cost_error*100:.1f}%")
            print(f"  Recommended adjustment: multiply cost coefficient by {1 + cost_error:.2f}")
        
        if row["avg_satisfaction"] < 3.0:
            print(f"WARNING: {row['selected_tool']}.{row['selected_pattern']}")
            print(f"  Low user satisfaction: {row['avg_satisfaction']:.1f}/5.0")
            print(f"  Consider adjusting preference scores")
```

---

### 🔄 Phase 7: UI Integration & Feature Flags

**Goal:** Expose optimization controls in UI and enable gradual rollout.

#### 7.1 Feature Flags

**Environment Variables:**
- `USE_HYBRID_OPTIMIZATION`: Enable hybrid optimization (default: false)
- `HYBRID_AMBIGUITY_THRESHOLD`: Ambiguity threshold ε (default: 0.08)
- `HYBRID_USE_LLM_TIEBREAKER`: Enable LLM tie-breaker (default: true)
- `HYBRID_LOG_TELEMETRY`: Enable telemetry logging (default: true)

**Gradual Rollout:**
1. **Week 1**: Enable for 10% of queries (A/B test)
2. **Week 2**: Enable for 50% of queries
3. **Week 3**: Enable for 100% of queries
4. **Week 4**: Make default, remove feature flag

#### 7.2 UI Controls

**User Preferences Panel:**
- Mode selector: Fast / Balanced / Accurate / Thorough
- Advanced sliders: Speed, Accuracy, Cost, Complexity, Completeness
- "Show me why" button: Display selection justification
- "I prefer X" feedback: Update user profile

**Selection Justification Display:**
```
✓ Selected: asset-service-query (count_aggregate)
  Estimated time: 122ms
  Estimated cost: $0.01
  
  Why this tool?
  Selected for fast response time based on your "quick" preference.
  
  Alternatives considered:
  • asset-direct-poll (parallel_poll) - More accurate but slower (3.2s)
  • info_display (general_info) - Faster but less complete
```

---

## Testing Strategy

### Unit Tests
- ✅ `test_safe_math_eval.py` (24 tests) - COMPLETE
- ✅ `test_profile_loader.py` (16 tests) - COMPLETE
- 🔄 `test_feature_normalizer.py` (15 tests) - TODO
- 🔄 `test_deterministic_scorer.py` (20 tests) - TODO
- 🔄 `test_policy_enforcer.py` (15 tests) - TODO
- 🔄 `test_preference_detector.py` (20 tests) - TODO
- 🔄 `test_candidate_enumerator.py` (15 tests) - TODO
- 🔄 `test_ambiguity_detector.py` (10 tests) - TODO
- 🔄 `test_llm_tie_breaker.py` (10 tests) - TODO
- 🔄 `test_hybrid_selector.py` (25 tests) - TODO
- 🔄 `test_telemetry_logger.py` (10 tests) - TODO

**Total: 180 tests (40 complete, 140 TODO)**

### Integration Tests
- 🔄 End-to-end selection (deterministic path)
- 🔄 End-to-end selection (ambiguous → LLM path)
- 🔄 Policy enforcement integration
- 🔄 Telemetry logging integration
- 🔄 Stage B integration

### Real-World Scenarios
- 🔄 "Quick count of all Linux servers" → asset-service-query (count_aggregate)
- 🔄 "Verify exact uptime of server-123" → asset-direct-poll (single_asset_poll)
- 🔄 "Detailed report of all assets" → asset-service-query (detailed_lookup)
- 🔄 "Fast summary of top 10 assets" → asset-service-query (list_summary)

### Performance Tests
- 🔄 Selection latency < 50ms (deterministic path)
- 🔄 Selection latency < 500ms (LLM path)
- 🔄 Profile loading < 100ms (cached)
- 🔄 Expression evaluation < 1ms per formula

### A/B Testing
- 🔄 Compare hybrid vs legacy selection
- 🔄 Measure user satisfaction
- 🔄 Measure prediction accuracy
- 🔄 Measure LLM tie-breaker usage rate

---

## Success Metrics

### Accuracy Metrics
- **Prediction accuracy**: Predicted time_ms within 20% of actual
- **Cost accuracy**: Predicted cost within 20% of actual
- **User satisfaction**: Average rating ≥ 4.0/5.0

### Performance Metrics
- **Selection latency**: < 50ms (deterministic), < 500ms (LLM)
- **LLM usage rate**: < 10% of queries (most should be deterministic)
- **Policy violation rate**: 0% (hard constraints enforced)

### Business Metrics
- **Cost savings**: Reduce average query cost by 20%
- **Speed improvement**: Reduce average query time by 30%
- **User engagement**: Increase query volume by 15%

---

## Rollout Plan

### Phase 1: Foundation (COMPLETE)
- ✅ Safe math evaluator
- ✅ Pydantic schemas
- ✅ YAML profile loader
- ✅ Initial tool profiles
- ✅ Comprehensive tests

### Phase 2: Scoring Engine (Week 1)
- 🔄 Feature normalization
- 🔄 Deterministic scorer
- 🔄 Policy enforcer
- 🔄 Unit tests

### Phase 3: Preference Detection (Week 2)
- 🔄 Preference detector
- 🔄 Candidate enumerator
- 🔄 Context estimation
- 🔄 Unit tests

### Phase 4: LLM Integration (Week 3)
- 🔄 Ambiguity detector
- 🔄 LLM tie-breaker
- 🔄 Prompt templates
- 🔄 Unit tests

### Phase 5: Stage B Integration (Week 4)
- 🔄 Hybrid selector
- 🔄 Feature flag
- 🔄 Integration tests
- 🔄 Real-world scenarios

### Phase 6: Telemetry (Week 5)
- 🔄 Telemetry logger
- 🔄 Database schema
- 🔄 Nightly analysis script
- 🔄 Monitoring dashboard

### Phase 7: UI & Rollout (Week 6)
- 🔄 UI controls
- 🔄 Justification display
- 🔄 A/B testing
- 🔄 Gradual rollout (10% → 50% → 100%)

---

## Risk Mitigation

### Risk: LLM Hallucination
**Mitigation:** LLM only used for tie-breaking, never for critical decisions. Deterministic scorer is source of truth.

### Risk: Expression Injection
**Mitigation:** AST-based parser with whitelisted operations. No `eval()` or `exec()`.

### Risk: Policy Bypass
**Mitigation:** Hard constraints enforced in code, never bypassable by LLM.

### Risk: Prediction Inaccuracy
**Mitigation:** Telemetry feedback loop with nightly coefficient tuning.

### Risk: Performance Regression
**Mitigation:** Feature flag for gradual rollout. Fallback to legacy logic if needed.

### Risk: Profile Sprawl
**Mitigation:** Max 5 patterns per capability. Inheritance reduces duplication.

---

## Future Enhancements

### Phase 8: Advanced Features (Future)
- **Multi-tool orchestration**: Select multiple tools for complex queries
- **Dynamic context estimation**: Use historical data to estimate N, p95_latency
- **User-specific profiles**: Learn individual user preferences over time
- **Cost budgets**: Per-user or per-team cost limits
- **SLA-aware routing**: Route to different execution modes based on SLA class
- **Confidence scores**: Expose confidence in selection decision
- **Explainability**: Detailed breakdown of scoring factors

### Phase 9: Machine Learning (Future)
- **Learned coefficients**: Use ML to tune time/cost formulas
- **Preference learning**: Learn user preferences from implicit feedback
- **Anomaly detection**: Detect when predictions are systematically wrong
- **Reinforcement learning**: Optimize for long-term user satisfaction

---

## Appendix: Key Design Decisions

### Why Hybrid (Deterministic + LLM)?
- **Predictability**: Deterministic for clear-cut cases (90%+ of queries)
- **Flexibility**: LLM for edge cases where human judgment needed
- **Auditability**: Mathematical scoring is explainable and debuggable
- **Safety**: Hard constraints enforced in code, not LLM

### Why AST-based Expression Evaluation?
- **Security**: No `eval()` vulnerabilities
- **Validation**: Catch errors at load time, not runtime
- **Flexibility**: Support complex formulas with runtime context
- **Performance**: Compiled once, evaluated many times

### Why YAML Profiles?
- **Readability**: Easy for humans to read and edit
- **Inheritance**: Reduce duplication with defaults
- **Validation**: Pydantic catches errors at load time
- **Versioning**: Git-friendly format

### Why Bounded Normalization?
- **Comparability**: All features on same [0,1] scale
- **Robustness**: Outliers don't dominate scoring
- **Interpretability**: 0 = worst, 1 = best

### Why ε = 0.08 for Ambiguity?
- **Balance**: Not too sensitive (avoid excessive LLM calls)
- **Not too insensitive**: Catch genuinely ambiguous cases
- **Tunable**: Can adjust based on telemetry

### Why Max 5 Patterns per Capability?
- **Simplicity**: Avoid overwhelming users with choices
- **Performance**: Faster enumeration and scoring
- **Maintainability**: Easier to keep profiles up-to-date

---

## Conclusion

This implementation plan provides a complete roadmap for building a hybrid optimization-based tool selection system in OpsConductor. The system balances predictability (deterministic scoring) with flexibility (LLM tie-breaking), while maintaining security (no eval), auditability (telemetry), and performance (< 50ms selection).

**Current Status:** Phase 1 complete (40/180 tests passing)
**Next Steps:** Implement Phase 2 (Feature Normalization & Scoring)
**Timeline:** 6-7 weeks to full production rollout
**Success Criteria:** 20% cost savings, 30% speed improvement, 4.0/5.0 user satisfaction

---

**Document Version:** 1.0  
**Last Updated:** 2025-01-XX  
**Author:** OpsConductor Team  
**Status:** Phase 1 Complete, Phase 2 Ready to Start