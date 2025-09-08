# Pre-Implementation Checklist

## MANDATORY STEPS BEFORE ANY IMPLEMENTATION

### Step 1: Search for Existing Decisions
Run these commands and document results:

```bash
# Find analysis documents
find . -name "*ANALYSIS*" -o -name "*analysis*" -o -name "*DECISION*"

# Search for technology decisions
grep -r "Decision:\|APPROVED\|selected for" . --include="*.md"

# Search for specific technologies
grep -r "RabbitMQ\|Redis\|PostgreSQL\|Docker" . --include="*.md"
```

### Step 2: Document Findings
**REQUIRED TEMPLATE:**

```
EXISTING DOCUMENTATION CHECK:
□ Searched for analysis documents: [YES/NO]
□ Found relevant decisions: [YES/NO/NONE FOUND]
□ Technology choice documented: [TECHNOLOGY NAME or NONE]
□ Decision rationale reviewed: [YES/NO/N/A]

DOCUMENTED DECISION (if found):
File: [filename]
Quote: "[exact quote from documentation]"
Technology: [specific choice]
Date: [if available]

IMPLEMENTATION APPROACH:
□ Following documented decision: [YES/NO/N/A]
□ User confirmation obtained: [YES/NO/N/A]
□ Ready to proceed: [YES/NO]
```

### Step 3: Verification
Before writing ANY code:
- [ ] Completed documentation search
- [ ] Filled out required template above
- [ ] Confirmed technology choice matches documentation OR
- [ ] Obtained explicit user confirmation for new technology choice

## FAILURE PREVENTION

**If documentation exists but is ignored**: CRITICAL ERROR
**If uncertain about technology choice**: STOP and ASK USER
**If no documentation found**: PROCEED but document new decisions

This checklist is MANDATORY for all implementation work.