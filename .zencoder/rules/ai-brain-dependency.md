# AI-BRAIN DEPENDENCY RULE

## 🚨 CRITICAL ARCHITECTURAL PRINCIPLE

**OpsConductor is AI-BRAIN DEPENDENT and must FAIL FAST when LLM is unavailable.**

### FUNDAMENTAL REQUIREMENTS

- ✅ **AI-BRAIN IS THE DECISION MAKER**: The LLM is the core decision-making system
- ❌ **NO FALLBACK PATTERNS**: Never implement pattern-based or rule-based fallback systems
- ❌ **NO DEGRADED SERVICE**: System should not function in any capacity without LLM
- ✅ **FAIL FAST**: Return clear errors when LLM is unavailable
- ✅ **STOP PROCESSING**: Do not attempt to continue pipeline processing without LLM

### WHAT THIS MEANS FOR DEVELOPMENT

#### ❌ NEVER IMPLEMENT:
- Pattern-based classification fallbacks
- Rule-based decision making when LLM is down
- "Smart" fallback systems
- Degraded service modes
- Template-based responses when LLM unavailable

#### ✅ ALWAYS IMPLEMENT:
- Clear error messages when LLM is unavailable
- Fail-fast error handling
- Proper exception propagation
- System halt when AI-BRAIN is down

### CODE PATTERNS

#### ❌ WRONG - Fallback patterns:
```python
if llm_unavailable:
    return pattern_based_classification(request)

try:
    result = llm.classify(request)
except:
    return simple_rule_classification(request)
```

#### ✅ RIGHT - Fail fast:
```python
if not llm_available():
    raise LLMUnavailableError("AI-BRAIN unavailable - OpsConductor cannot function")

result = llm.classify(request)  # Let it fail if LLM is down
```

### ENFORCEMENT

- All code reviews must check for fallback implementations
- Tests should verify system fails properly when LLM is unavailable
- Documentation must emphasize AI-BRAIN dependency
- Never implement "smart" fallbacks or pattern-based alternatives

**REMEMBER**: OpsConductor without AI-BRAIN is like a car without an engine - it should not pretend to work!