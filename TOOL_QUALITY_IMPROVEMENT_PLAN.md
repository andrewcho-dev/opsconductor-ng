# Tool Quality Improvement Plan

**Date:** 2025-01-XX  
**Status:** APPROVED - READY TO EXECUTE  
**Priority:** CRITICAL

---

## Executive Summary

Our tool catalog audit revealed a **critical quality crisis**:

- **168 tools** audited
- **Average quality score: 15.6/100** (failing!)
- **97% of tools are "Level 1: Minimal"** quality
- **0 tools meet "Level 3: Good"** or higher standards

**Root Cause:** Parameter descriptions are too vague for LLMs to make correct decisions. This directly causes user-facing bugs like the "zoom in 2x" issue.

**Solution:** Systematically improve parameter descriptions and examples across all tools, starting with highest-impact tools.

---

## The Problem in Detail

### What We Found

Most tools have parameter descriptions like this:

```yaml
- name: zoom
  type: integer
  description: Zoom level
```

**This is insufficient because:**
- ❌ Doesn't explain what the values mean
- ❌ Doesn't explain when to use this parameter
- ❌ Doesn't provide examples
- ❌ Doesn't explain alternatives (zoom vs rzoom)
- ❌ Doesn't map natural language to parameter values

### What We Need

Parameter descriptions should look like this:

```yaml
- name: zoom
  type: integer
  description: |
    Absolute zoom level (1-9999).
    
    Value meanings:
    - 1 = widest angle (fully zoomed out)
    - 9999 = maximum zoom (fully zoomed in)
    - 5000 = middle zoom level
    
    When to use:
    - Use this to set a specific zoom level
    - For relative zoom changes (zoom in/out), use rzoom instead
    
    Natural language mapping:
    - "set zoom to level 5000" → zoom=5000
    - "zoom to maximum" → zoom=9999
    - "set to widest angle" → zoom=1
    
    Examples:
    - User: "set zoom to level 5000" → zoom=5000
    - User: "zoom to maximum" → zoom=9999
  validation: ^[1-9][0-9]{0,3}$
  required: false
```

---

## Improvement Strategy

### Phase 1: Immediate Fixes (Week 1) - HIGH PRIORITY

**Goal:** Fix the active bug and highest-impact tools

#### 1.1 Fix Axis VAPIX PTZ (Active Bug)

**Current state:** Score 27.6/100, Level 1  
**Target:** Score 80+/100, Level 3+

**Actions:**
- [ ] Remove the band-aid `zoom_control` capability
- [ ] Enrich `zoom` parameter description in `absolute_move` pattern
- [ ] Enrich `rzoom` parameter description in `relative_move` pattern
- [ ] Add concrete examples for each parameter
- [ ] Add natural language mapping
- [ ] Test with "zoom in 2x" command
- [ ] Verify score improvement with audit script

**Estimated time:** 2-3 hours  
**Owner:** AI Assistant  
**Deadline:** Today

#### 1.2 Fix Critical Command-Line Tools

**Tools to fix (8 tools):**
1. curl (score: 20.0)
2. docker (score: 14.0)
3. kubectl (score: 8.0)
4. mysql (score: 8.0)
5. grep (score: 50.0)
6. awk (score: 14.0)
7. sed (score: 14.0)
8. find (score: 14.0)

**Target:** Each tool scores 70+/100

**Estimated time:** 1-2 hours per tool = 8-16 hours total  
**Owner:** TBD  
**Deadline:** End of Week 1

### Phase 2: High-Impact Tools (Week 2-3) - HIGH PRIORITY

**Goal:** Fix frequently-used tools across all categories

#### 2.1 Network Tools (10 tools)
- nmap, tcpdump, tshark, ngrep
- *_analyzer tools (dns, http, tcp, udp, etc.)

**Target:** Average category score 70+/100

#### 2.2 Cloud Tools (11 tools)
- aws, gcloud, az
- aws-ec2, aws-s3, aws-lambda, aws-rds
- gcloud-compute, gcloud-storage
- az-vm, az-storage

**Target:** Average category score 70+/100

#### 2.3 Container Tools (21 tools)
- helm, docker-compose
- docker-ps, docker-logs, docker-exec
- kubectl-get, kubectl-logs, kubectl-exec, kubectl-describe

**Target:** Average category score 70+/100

**Estimated time:** 30-40 hours total  
**Owner:** TBD  
**Deadline:** End of Week 3

### Phase 3: Comprehensive Improvement (Week 4-8) - MEDIUM PRIORITY

**Goal:** Bring all tools to acceptable quality level

#### 3.1 Linux Tools (54 tools)
**Current avg:** 17.2/100  
**Target avg:** 70+/100

**Prioritize:**
- System management: systemctl (already 55.7), service, systemd-timer
- File operations: ls, cat, tail, head, find, grep
- Network: ping, netstat, ss, dig, nslookup
- Process management: ps, top, kill, pkill
- User management: useradd, usermod, passwd

#### 3.2 Windows Tools (31 tools)
**Current avg:** 16.9/100  
**Target avg:** 70+/100

**Prioritize:**
- PowerShell (already 56.0)
- Get-Service, Get-Process
- Get-EventLog, Get-WinEvent
- Active Directory cmdlets

#### 3.3 Database Tools (12 tools)
**Current avg:** 12.5/100  
**Target avg:** 70+/100

**All tools:** mysql, psql, mongosh, redis-cli, sqlite3, etc.

#### 3.4 Monitoring Tools (10 tools)
**Current avg:** 14.0/100  
**Target avg:** 70+/100

**All tools:** prometheus, alertmanager, node_exporter, etc.

#### 3.5 Custom Tools (9 tools)
**Current avg:** 13.3/100  
**Target avg:** 70+/100

**All tools:** asset_*, sendmail, slack-cli, teams-cli, webhook-sender

**Estimated time:** 80-120 hours total  
**Owner:** TBD  
**Deadline:** End of Week 8

### Phase 4: Quality Assurance (Ongoing)

**Goal:** Maintain quality standards and prevent regression

#### 4.1 Establish Quality Gates
- [ ] Create pre-commit hook to run audit script
- [ ] Require minimum score of 70/100 for new tools
- [ ] Require minimum score of 60/100 for tool updates
- [ ] Add quality score to tool catalog UI

#### 4.2 Regular Audits
- [ ] Weekly: Run audit script and track progress
- [ ] Monthly: Review lowest-scoring tools
- [ ] Quarterly: Comprehensive audit and improvement cycle

#### 4.3 LLM Testing Framework
- [ ] Create test cases for common user requests
- [ ] Test LLM parameter extraction accuracy
- [ ] Measure improvement in success rate
- [ ] Track false positives (system says success but action failed)

**Estimated time:** 20 hours setup + ongoing  
**Owner:** TBD  
**Deadline:** End of Week 4

---

## Success Metrics

### Quantitative Metrics

**Current State:**
- Average score: 15.6/100
- Level 1 (Minimal): 97%
- Level 2 (Basic): 3%
- Level 3 (Good): 0%
- Level 4 (Excellent): 0%

**Target State (End of Phase 3):**
- Average score: 70+/100
- Level 1 (Minimal): <10%
- Level 2 (Basic): <30%
- Level 3 (Good): >50%
- Level 4 (Excellent): >10%

**Target State (End of Phase 4):**
- Average score: 80+/100
- Level 1 (Minimal): 0%
- Level 2 (Basic): <20%
- Level 3 (Good): >60%
- Level 4 (Excellent): >20%

### Qualitative Metrics

- **User satisfaction:** Fewer "it said success but nothing happened" reports
- **LLM accuracy:** Higher rate of correct parameter extraction
- **Developer confidence:** Easier to add new tools with clear examples
- **System reliability:** Fewer false positives in execution results

---

## Guidelines for Tool Improvement

### 1. Parameter Description Template

Use this template for all parameter descriptions:

```yaml
- name: <parameter_name>
  type: <type>
  description: |
    <One-line summary>
    
    Value meanings:
    - <value1> = <meaning>
    - <value2> = <meaning>
    
    When to use:
    - Use this when <condition>
    - Don't use this when <condition> (use <alternative> instead)
    
    Natural language mapping:
    - "<user request>" → <parameter_name>=<value>
    - "<user request>" → <parameter_name>=<value>
    
    Examples:
    - User: "<request>" → <parameter_name>=<value>
    - User: "<request>" → <parameter_name>=<value>
    
    Typical values:
    - <use case>: <value>
    - <use case>: <value>
  validation: <regex>
  default: <default_value>  # if optional
  required: <true|false>
```

### 2. Checklist for Each Parameter

Before marking a parameter as "done", verify:

- [ ] **One-line summary** clearly states what the parameter does
- [ ] **Value meanings** explain what different values mean (if applicable)
- [ ] **When to use** explains when to use this parameter vs alternatives
- [ ] **Natural language mapping** shows how user requests map to values
- [ ] **Examples** provide at least 2-3 concrete examples
- [ ] **Typical values** show common use cases and their values
- [ ] **Validation** regex is appropriate and documented
- [ ] **Default value** is specified (if optional)

### 3. Common Patterns to Address

#### Pattern 1: Absolute vs Relative Values

**Bad:**
```yaml
- name: zoom
  description: Zoom level
- name: rzoom
  description: Relative zoom
```

**Good:**
```yaml
- name: zoom
  description: |
    Absolute zoom level (1-9999).
    Use this to set a specific zoom level.
    For relative zoom changes, use rzoom instead.
    Examples:
    - "set zoom to 5000" → zoom=5000
    - "zoom to maximum" → zoom=9999

- name: rzoom
  description: |
    Relative zoom movement (positive = zoom in, negative = zoom out).
    Use this for "zoom in" or "zoom out" requests.
    Typical range: -5000 to +5000
    Examples:
    - "zoom in" → rzoom=1000
    - "zoom in 2x" → rzoom=2000
    - "zoom out" → rzoom=-1000
```

#### Pattern 2: Enums and Modes

**Bad:**
```yaml
- name: mode
  description: Mode
```

**Good:**
```yaml
- name: mode
  description: |
    Search mode (default: basic).
    
    Modes:
    - basic: Simple string matching (fast, exact matches)
    - regex: Regular expression matching (slower, patterns)
    - fuzzy: Fuzzy matching (slowest, approximate matches)
    
    When to use:
    - Use 'basic' for exact string searches
    - Use 'regex' for pattern matching
    - Use 'fuzzy' for typo-tolerant searches
    
    Natural language mapping:
    - "find files containing 'error'" → mode=basic
    - "find files matching pattern '^ERROR.*$'" → mode=regex
    - "find files similar to 'eror'" → mode=fuzzy
```

#### Pattern 3: Numeric Ranges

**Bad:**
```yaml
- name: timeout
  description: Timeout value
```

**Good:**
```yaml
- name: timeout
  description: |
    Request timeout in seconds (default: 30).
    
    Range: 1-300 seconds
    
    Typical values:
    - Fast APIs: 5-10 seconds
    - Standard APIs: 30 seconds
    - Slow operations: 60-120 seconds
    - Long-running queries: 180-300 seconds
    
    Natural language mapping:
    - "quick health check" → timeout=5
    - "standard API call" → timeout=30
    - "long-running query" → timeout=120
```

#### Pattern 4: Boolean Flags

**Bad:**
```yaml
- name: recursive
  description: Recursive flag
```

**Good:**
```yaml
- name: recursive
  description: |
    Search recursively through subdirectories (default: false).
    
    Values:
    - true: Search all subdirectories recursively
    - false: Search only the specified directory
    
    When to use:
    - Use true when user says "search all subdirectories", "recursive", "deep search"
    - Use false when user says "only this directory", "non-recursive", "shallow search"
    
    Natural language mapping:
    - "search all subdirectories" → recursive=true
    - "search recursively" → recursive=true
    - "only this directory" → recursive=false
```

---

## Tools and Automation

### 1. Audit Script

**Location:** `/scripts/audit_tool_quality.py`

**Usage:**
```bash
# Audit all tools
python3 scripts/audit_tool_quality.py --report --output TOOL_QUALITY_REPORT.txt

# Audit specific tool
python3 scripts/audit_tool_quality.py --tool axis_vapix_ptz

# Audit specific category
python3 scripts/audit_tool_quality.py --category network --report
```

### 2. Validation Script (To Be Created)

**Location:** `/scripts/validate_tool.py`

**Features:**
- Check parameter descriptions for required elements
- Validate examples are present
- Check for natural language mapping
- Verify validation regexes
- Ensure minimum quality score

### 3. Pre-Commit Hook (To Be Created)

**Location:** `.git/hooks/pre-commit`

**Features:**
- Run audit script on changed tools
- Reject commits if quality score drops below threshold
- Provide feedback on what needs improvement

---

## Progress Tracking

### Weekly Scorecard

| Week | Tools Fixed | Avg Score | Level 3+ % | Notes |
|------|-------------|-----------|------------|-------|
| Baseline | 0 | 15.6 | 0% | Initial audit |
| Week 1 | 9 | TBD | TBD | Axis + 8 critical tools |
| Week 2 | TBD | TBD | TBD | Network + Cloud tools |
| Week 3 | TBD | TBD | TBD | Container tools |
| Week 4 | TBD | TBD | TBD | Linux tools (part 1) |
| Week 5 | TBD | TBD | TBD | Linux tools (part 2) |
| Week 6 | TBD | TBD | TBD | Windows tools |
| Week 7 | TBD | TBD | TBD | Database + Monitoring |
| Week 8 | TBD | TBD | TBD | Custom tools + cleanup |

### Category Progress

| Category | Tools | Current Avg | Target Avg | Status |
|----------|-------|-------------|------------|--------|
| Network | 20 | 17.1 | 70+ | 🔴 Not Started |
| Linux | 54 | 17.2 | 70+ | 🔴 Not Started |
| Container | 21 | 13.1 | 70+ | 🔴 Not Started |
| Database | 12 | 12.5 | 70+ | 🔴 Not Started |
| Cloud | 11 | 12.9 | 70+ | 🔴 Not Started |
| Custom | 9 | 13.3 | 70+ | 🔴 Not Started |
| Monitoring | 10 | 14.0 | 70+ | 🔴 Not Started |
| Windows | 31 | 16.9 | 70+ | 🔴 Not Started |

---

## Next Steps

1. **Get approval** for this plan from stakeholders
2. **Start Phase 1.1** - Fix Axis VAPIX PTZ tool (TODAY)
3. **Assign owners** for Phase 1.2 and Phase 2
4. **Set up weekly check-ins** to track progress
5. **Create validation script** (Week 1)
6. **Set up pre-commit hook** (Week 2)
7. **Begin Phase 2** (Week 2)

---

## Conclusion

This is a **critical quality issue** that affects system reliability and user satisfaction. The "zoom in 2x" bug was just one symptom of a much larger problem.

The good news: We have a clear path forward, automated tools to track progress, and a systematic approach to improvement.

**The investment is significant (~150-200 hours), but the payoff is enormous:**
- Fewer user-facing bugs
- Higher LLM accuracy
- Better system reliability
- Easier tool development
- Improved user satisfaction

**Let's start with Phase 1.1 today and fix the Axis VAPIX PTZ tool properly!**