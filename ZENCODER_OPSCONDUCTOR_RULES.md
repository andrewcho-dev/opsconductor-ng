# ZENCODER OPSCONDUCTOR ARCHITECTURAL RULES

## 🚨 CRITICAL ARCHITECTURAL PRINCIPLE - AI-BRAIN DEPENDENCY

### **RULE #1: NO FALLBACK SYSTEMS - FAIL FAST WHEN LLM IS DOWN**

**FUNDAMENTAL PRINCIPLE**: The OpsConductor system is designed to be **AI-BRAIN DEPENDENT** and must **FAIL FAST** when the LLM (AI-BRAIN) is unavailable.

#### **CORE REQUIREMENTS:**
- ✅ **AI-BRAIN IS THE DECISION MAKER**: The LLM is the core decision-making system
- ❌ **NO FALLBACK PATTERNS**: Never implement pattern-based or rule-based fallback systems
- ❌ **NO DEGRADED SERVICE**: System should not function in any capacity without LLM
- ✅ **FAIL FAST**: Return clear errors when LLM is unavailable
- ✅ **STOP PROCESSING**: Do not attempt to continue pipeline processing without LLM

#### **WHAT THIS MEANS:**
- **WRONG**: "Smart pattern-based classification when LLM is down"
- **RIGHT**: "System ERROR and STOP when LLM is down"
- **WRONG**: "Fallback to simple rules when AI-BRAIN unavailable"
- **RIGHT**: "Return connection error and halt all processing"

#### **IMPLEMENTATION REQUIREMENTS:**
1. **Intent Classification**: Must use LLM - no pattern fallbacks
2. **Risk Assessment**: Must use LLM - no rule-based fallbacks  
3. **Decision Making**: Must use LLM - no hardcoded decision trees
4. **Response Generation**: Must use LLM - no template fallbacks
5. **Error Handling**: Clear error messages when LLM unavailable

#### **CODE PATTERNS TO AVOID:**
```python
# ❌ WRONG - Fallback patterns
if llm_unavailable:
    return pattern_based_classification(request)

# ❌ WRONG - Degraded service
try:
    result = llm.classify(request)
except:
    return simple_rule_classification(request)
```

#### **CODE PATTERNS TO USE:**
```python
# ✅ RIGHT - Fail fast
if not llm_available():
    raise LLMUnavailableError("AI-BRAIN unavailable - OpsConductor cannot function")

# ✅ RIGHT - No fallback
result = llm.classify(request)  # Let it fail if LLM is down
```

#### **WHY THIS MATTERS:**
- OpsConductor is an **AI-POWERED** system, not a traditional rule-based system
- The AI-BRAIN provides intelligent decision making that cannot be replicated by patterns
- Fallback systems would provide false confidence in degraded capabilities
- Users should know when the AI-BRAIN is down and fix it, not rely on inferior fallbacks

### **ENFORCEMENT:**
- All code reviews must check for fallback implementations
- Tests should verify system fails properly when LLM is unavailable
- Documentation must emphasize AI-BRAIN dependency
- Never implement "smart" fallbacks or pattern-based alternatives

---

**REMEMBER**: OpsConductor without AI-BRAIN is like a car without an engine - it should not pretend to work!