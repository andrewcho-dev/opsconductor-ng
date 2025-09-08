# Implementation Safeguards

## CRITICAL ERROR PREVENTION RULES

### Rule 1: ALWAYS Check Existing Decisions Before Implementation
Before implementing ANY new feature or system:

1. **MANDATORY**: Search for existing analysis documents
2. **MANDATORY**: Check for documented decisions 
3. **MANDATORY**: Verify technology choices in documentation
4. **MANDATORY**: Quote the specific decision from documentation

**Search Commands to Run:**
```bash
# Search for analysis documents
find . -name "*ANALYSIS*" -o -name "*analysis*"

# Search for decision documents  
grep -r "Decision:" . --include="*.md"
grep -r "APPROVED" . --include="*.md"
grep -r "selected" . --include="*.md"

# Search for technology mentions
grep -r "RabbitMQ\|Redis\|message queue" . --include="*.md"
```

### Rule 2: Quote Documented Decisions
When implementing something that has been analyzed:

**REQUIRED FORMAT:**
```
DOCUMENTED DECISION FOUND:
File: [filename]
Decision: [exact quote from documentation]
Technology: [specific technology chosen]
Rationale: [key reasons from analysis]

IMPLEMENTATION PLAN:
Following documented decision to use [technology] because [reasons from doc]
```

### Rule 3: Stop and Ask When Uncertain
If ANY doubt exists about technology choices:
- STOP implementation
- ASK user to confirm technology choice
- REFERENCE the specific documentation found
- GET explicit confirmation before proceeding

### Rule 4: Implementation Verification Checklist
Before writing any code:

- [ ] Searched for existing analysis documents
- [ ] Found and read relevant decision documents  
- [ ] Quoted the documented technology choice
- [ ] Verified implementation matches documented decision
- [ ] Asked for confirmation if any uncertainty exists

## RECENT FAILURE ANALYSIS

**Date**: 2024-01-15
**Error**: Implemented Redis Streams despite documented RabbitMQ decision
**Root Cause**: Failed to check existing documentation before implementation
**Impact**: Wasted user time and LLM calls, created wrong implementation
**Prevention**: This safeguard document and mandatory checks

## ENFORCEMENT

This document must be referenced before ANY implementation work.
Failure to follow these rules is a critical error that wastes user resources.