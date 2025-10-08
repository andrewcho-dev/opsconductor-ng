# Tool Catalog Quality Audit

**Date:** 2025-01-XX  
**Auditor:** AI Assistant  
**Scope:** All tool specifications in `/pipeline/config/tools/`

---

## Executive Summary

This audit reveals **systemic quality issues** across our tool catalog that directly impact LLM performance and user experience. The root cause of the "zoom in 2x" bug was not a missing capability, but **insufficient parameter descriptions** that failed to teach the LLM how to correctly use existing parameters.

### Key Findings

1. **~150+ tools** exist across 7 categories (linux, windows, network, container, database, cloud, monitoring, custom)
2. **Quality varies dramatically** - from excellent (systemctl) to minimal (curl, docker, mysql, kubectl)
3. **Parameter descriptions are often vague** - missing context, examples, and guidance
4. **Many tools lack examples** - making it hard for LLMs to learn correct usage patterns
5. **This is a systemic problem** - not isolated to one tool

### Impact

- **LLMs guess incorrectly** when parameter descriptions are vague
- **Users experience failures** even when the system reports success
- **Tool selection may be suboptimal** when use cases are generic
- **Maintenance burden increases** as we add band-aid fixes instead of improving quality

---

## Quality Standards

### Level 1: Minimal (Unacceptable)
- Generic capability/pattern names ("primary_capability", "execute")
- Vague parameter descriptions ("Target host", "Value")
- No examples
- Generic use cases ("use tool", "tool command")
- **Example:** curl.yaml, docker.yaml, mysql.yaml, kubectl.yaml

### Level 2: Basic (Needs Improvement)
- Specific pattern names but limited detail
- Parameter descriptions exist but lack context
- Few or no examples
- Use cases are somewhat specific
- **Example:** Most network analyzer tools

### Level 3: Good (Acceptable)
- Clear, specific pattern names
- Detailed parameter descriptions with validation
- Some examples provided
- Specific use cases
- **Example:** systemctl.yaml

### Level 4: Excellent (Target)
- Crystal-clear pattern names and descriptions
- **Rich parameter descriptions** that teach the LLM:
  - What the parameter does
  - When to use it vs alternatives
  - How to interpret natural language requests
  - Value ranges and their meanings
  - Concrete examples of common values
- **Comprehensive examples** showing:
  - Natural language request → parameter values
  - Edge cases and variations
  - Common patterns
- **Clear use cases** that match real user requests
- **Limitations and constraints** clearly documented
- **Example:** axis_vapix_ptz.yaml (after proper fixes)

---

## Audit Results by Category

### Network Tools (20 tools)

| Tool | Quality Level | Issues | Priority |
|------|---------------|--------|----------|
| axis_vapix_ptz.yaml | Level 2 → 3 | Parameter descriptions need enrichment (zoom, rzoom) | **HIGH** (active bug) |
| curl.yaml | Level 1 | Generic pattern, minimal parameters, no examples | HIGH |
| nmap.yaml | Level 1 | Generic pattern, minimal parameters | HIGH |
| tcpdump.yaml | Level 1 | Generic pattern, minimal parameters | MEDIUM |
| tshark.yaml | Level 1 | Generic pattern, minimal parameters | MEDIUM |
| *_analyzer.yaml (10 tools) | Level 1-2 | Varying quality, need review | MEDIUM |
| arp_scan.yaml | Level 1 | Generic pattern | LOW |
| masscan.yaml | Level 1 | Generic pattern | LOW |
| netdiscover.yaml | Level 1 | Generic pattern | LOW |

### Linux Tools (60+ tools)

| Tool | Quality Level | Issues | Priority |
|------|---------------|--------|----------|
| systemctl.yaml | Level 3 | Good example, minor improvements possible | LOW |
| curl.yaml | Level 1 | (duplicate - see Network) | HIGH |
| grep.yaml | Level 1 | Generic pattern, minimal parameters | HIGH |
| awk.yaml | Level 1 | Generic pattern, minimal parameters | HIGH |
| sed.yaml | Level 1 | Generic pattern, minimal parameters | HIGH |
| find.yaml | Level 1 | Generic pattern, minimal parameters | HIGH |
| ps.yaml | Level 1 | Generic pattern, minimal parameters | MEDIUM |
| netstat.yaml | Level 1 | Generic pattern, minimal parameters | MEDIUM |
| iptables.yaml | Level 1 | Generic pattern, minimal parameters | MEDIUM |
| **(50+ others)** | Level 1-2 | Need individual review | MEDIUM-LOW |

### Container Tools (20+ tools)

| Tool | Quality Level | Issues | Priority |
|------|---------------|--------|----------|
| docker.yaml | Level 1 | Generic pattern, minimal parameters, no examples | HIGH |
| kubectl.yaml | Level 1 | Generic pattern, minimal parameters, no examples | HIGH |
| helm.yaml | Level 1 | Generic pattern, minimal parameters | HIGH |
| docker_ps.yaml | Level 1 | Generic pattern | MEDIUM |
| docker_logs.yaml | Level 1 | Generic pattern | MEDIUM |
| kubectl_get.yaml | Level 1 | Generic pattern | MEDIUM |
| **(15+ others)** | Level 1-2 | Need individual review | MEDIUM-LOW |

### Database Tools (11 tools)

| Tool | Quality Level | Issues | Priority |
|------|---------------|--------|----------|
| mysql.yaml | Level 1 | Generic pattern, minimal parameters, no examples | HIGH |
| psql.yaml | Level 1 | Generic pattern, minimal parameters | HIGH |
| mongosh.yaml | Level 1 | Generic pattern, minimal parameters | HIGH |
| redis_cli.yaml | Level 1 | Generic pattern, minimal parameters | MEDIUM |
| **(7 others)** | Level 1-2 | Need individual review | MEDIUM |

### Cloud Tools (11 tools)

| Tool | Quality Level | Issues | Priority |
|------|---------------|--------|----------|
| aws.yaml | Level 1 | Generic pattern, minimal parameters | HIGH |
| gcloud.yaml | Level 1 | Generic pattern, minimal parameters | HIGH |
| az.yaml | Level 1 | Generic pattern, minimal parameters | HIGH |
| **(8 others)** | Level 1-2 | Need individual review | MEDIUM |

### Windows Tools (30+ tools)

| Tool | Quality Level | Issues | Priority |
|------|---------------|--------|----------|
| powershell.yaml | Level 1 | Generic pattern, minimal parameters | HIGH |
| **(30+ others)** | Level 1-2 | Need individual review | MEDIUM |

### Monitoring Tools (10 tools)

| Tool | Quality Level | Issues | Priority |
|------|---------------|--------|----------|
| prometheus.yaml | Level 1-2 | Need review | MEDIUM |
| **(9 others)** | Level 1-2 | Need individual review | MEDIUM-LOW |

### Custom Tools (9 tools)

| Tool | Quality Level | Issues | Priority |
|------|---------------|--------|----------|
| asset_*.yaml (5 tools) | Level 2 | Need review | MEDIUM |
| sendmail.yaml | Level 1-2 | Need review | MEDIUM |
| slack_cli.yaml | Level 1-2 | Need review | MEDIUM |
| teams_cli.yaml | Level 1-2 | Need review | MEDIUM |
| webhook_sender.yaml | Level 1-2 | Need review | LOW |

---

## Root Cause Analysis: The "Zoom In 2X" Bug

### What Happened

User said: "zoom in 2x"  
System sent: `GET http://192.168.10.90/axis-cgi/com/ptz.cgi?zoom=2`  
Camera responded: HTTP 204 No Content (success)  
**Result:** Camera did NOT zoom in (likely zoomed out to level 2)

### Why It Happened

The LLM saw two parameters in the tool specification:

1. **`zoom` (in absolute_move pattern):**
   ```yaml
   - name: zoom
     type: integer
     description: Zoom level (1-9999, optional)
     validation: ^[1-9][0-9]{0,3}$
     required: false
   ```

2. **`rzoom` (in relative_move pattern):**
   ```yaml
   - name: rzoom
     type: integer
     description: Relative zoom movement (optional)
     validation: ^-?[0-9]+$
     required: false
   ```

**The LLM guessed wrong** because:
- ❌ "Zoom level (1-9999, optional)" doesn't explain what 1 vs 9999 means
- ❌ "Relative zoom movement (optional)" doesn't explain positive vs negative
- ❌ No examples showing "zoom in 2x" → `rzoom=2000`
- ❌ No guidance on when to use `zoom` vs `rzoom`
- ❌ No typical value ranges (500-5000 for rzoom)

### What Should Have Been There

**Better `zoom` description:**
```yaml
- name: zoom
  type: integer
  description: |
    Absolute zoom level (1-9999).
    - 1 = widest angle (fully zoomed out)
    - 9999 = maximum zoom (fully zoomed in)
    - Use this to set a specific zoom level
    - For relative zoom changes (zoom in/out), use rzoom instead
    Examples:
    - "set zoom to level 5000" → zoom=5000
    - "zoom to maximum" → zoom=9999
  validation: ^[1-9][0-9]{0,3}$
  required: false
```

**Better `rzoom` description:**
```yaml
- name: rzoom
  type: integer
  description: |
    Relative zoom movement (positive = zoom in, negative = zoom out).
    - Typical range: -5000 to +5000
    - Default increment: 1000
    - Use this for "zoom in" or "zoom out" requests
    Examples:
    - "zoom in" → rzoom=1000
    - "zoom in 2x" → rzoom=2000
    - "zoom out" → rzoom=-1000
    - "zoom out 3x" → rzoom=-3000
  validation: ^-?[0-9]+$
  required: false
```

---

## Remediation Plan

### Phase 1: Immediate Fixes (Week 1)

**Priority: HIGH - Active bugs and critical tools**

1. **Fix axis_vapix_ptz.yaml** (active bug)
   - Enrich `zoom` and `rzoom` parameter descriptions
   - Add concrete examples
   - Remove the band-aid `zoom_control` capability
   - Test with "zoom in 2x" command

2. **Fix critical command-line tools** (high usage)
   - curl.yaml
   - docker.yaml
   - kubectl.yaml
   - mysql.yaml
   - grep.yaml
   - awk.yaml
   - sed.yaml
   - find.yaml

### Phase 2: High-Impact Tools (Week 2-3)

**Priority: HIGH - Frequently used tools**

3. **Network tools**
   - nmap.yaml
   - tcpdump.yaml
   - tshark.yaml

4. **Cloud tools**
   - aws.yaml
   - gcloud.yaml
   - az.yaml

5. **Container tools**
   - helm.yaml
   - docker_ps.yaml
   - kubectl_get.yaml

### Phase 3: Comprehensive Audit (Week 4-6)

**Priority: MEDIUM - All remaining tools**

6. **Systematically review and improve:**
   - All Linux tools (60+)
   - All Windows tools (30+)
   - All network analyzer tools (10+)
   - All monitoring tools (10+)
   - All database tools (11)
   - All custom tools (9)

### Phase 4: Quality Assurance (Ongoing)

7. **Establish quality gates:**
   - Create validation script to check tool quality
   - Require Level 3+ quality for new tools
   - Regular audits (quarterly)
   - LLM testing framework to validate parameter understanding

---

## Guidelines for Improving Tool Quality

### 1. Parameter Descriptions Should Teach the LLM

**Bad:**
```yaml
- name: zoom
  type: integer
  description: Zoom level
```

**Good:**
```yaml
- name: zoom
  type: integer
  description: |
    Absolute zoom level (1-9999).
    - 1 = widest angle (fully zoomed out)
    - 9999 = maximum zoom (fully zoomed in)
    - Use this to set a specific zoom level
    - For relative zoom changes, use rzoom instead
    Examples:
    - "set zoom to level 5000" → zoom=5000
    - "zoom to maximum" → zoom=9999
```

### 2. Include Concrete Examples

**Bad:**
```yaml
typical_use_cases:
  - use docker
  - docker command
```

**Good:**
```yaml
typical_use_cases:
  - restart docker container
  - stop all containers
  - list running containers
  - remove unused images
examples:
  - request: "restart nginx container"
    parameters:
      container_name: "nginx"
      action: "restart"
  - request: "stop all containers"
    parameters:
      action: "stop"
      all: true
```

### 3. Explain When to Use Each Parameter

**Bad:**
```yaml
- name: mode
  type: string
  description: Mode
```

**Good:**
```yaml
- name: mode
  type: string
  description: |
    Search mode (default: basic).
    - basic: Simple string matching (fast, use for exact matches)
    - regex: Regular expression matching (slower, use for patterns)
    - fuzzy: Fuzzy matching (slowest, use for approximate matches)
    Examples:
    - "find files containing 'error'" → mode=basic
    - "find files matching pattern '^ERROR.*$'" → mode=regex
    - "find files similar to 'eror'" → mode=fuzzy
```

### 4. Provide Value Ranges and Meanings

**Bad:**
```yaml
- name: timeout
  type: integer
  description: Timeout value
```

**Good:**
```yaml
- name: timeout
  type: integer
  description: |
    Request timeout in seconds (default: 30).
    - Minimum: 1 second
    - Maximum: 300 seconds (5 minutes)
    - Typical values:
      - Fast APIs: 5-10 seconds
      - Standard APIs: 30 seconds
      - Slow operations: 60-120 seconds
    Examples:
    - "quick health check" → timeout=5
    - "standard API call" → timeout=30
    - "long-running query" → timeout=120
```

### 5. Distinguish Between Similar Parameters

**Bad:**
```yaml
- name: count
  description: Count
- name: limit
  description: Limit
```

**Good:**
```yaml
- name: count
  description: |
    Number of items to process (affects execution).
    Use this when you want to limit how many items are processed.
    Example: "process first 10 files" → count=10

- name: limit
  description: |
    Number of results to return (affects output).
    Use this when you want to limit the output size.
    Example: "show top 5 results" → limit=5
```

### 6. Add Context for Natural Language Mapping

**Bad:**
```yaml
- name: direction
  type: string
  description: Direction
```

**Good:**
```yaml
- name: direction
  type: string
  description: |
    Sort direction (default: asc).
    - asc: Ascending order (A→Z, 0→9, oldest→newest)
    - desc: Descending order (Z→A, 9→0, newest→oldest)
    Natural language mapping:
    - "sort by name" → direction=asc
    - "sort by name descending" → direction=desc
    - "newest first" → direction=desc
    - "oldest first" → direction=asc
    - "highest to lowest" → direction=desc
```

---

## Validation Checklist

Before marking a tool as "Level 3" or higher, verify:

- [ ] **Pattern names** are specific and descriptive (not "execute" or "primary_capability")
- [ ] **Parameter descriptions** include:
  - [ ] What the parameter does
  - [ ] When to use it vs alternatives
  - [ ] Value ranges and their meanings
  - [ ] At least 2-3 concrete examples
- [ ] **Typical use cases** match real user requests (not "use tool")
- [ ] **Examples section** exists with at least 2 examples
- [ ] **Validation rules** are appropriate and documented
- [ ] **Limitations** are clearly stated
- [ ] **Natural language mapping** is clear (how user requests map to parameters)

---

## Next Steps

1. **Get approval** for this audit and remediation plan
2. **Start with Phase 1** - fix axis_vapix_ptz.yaml properly
3. **Create a validation script** to automatically check tool quality
4. **Establish a review process** for new/updated tools
5. **Track progress** - create a dashboard showing tool quality metrics

---

## Appendix: Tool Quality Metrics

We should track:

1. **Parameter Description Quality Score** (0-100)
   - Has examples: +25 points
   - Has value ranges: +25 points
   - Has natural language mapping: +25 points
   - Has "when to use" guidance: +25 points

2. **Tool Completeness Score** (0-100)
   - Has specific patterns (not "execute"): +20 points
   - Has examples section: +20 points
   - Has limitations documented: +20 points
   - Has validation rules: +20 points
   - Has typical use cases (not generic): +20 points

3. **LLM Usability Score** (0-100)
   - Parameter descriptions teach the LLM: +50 points
   - Examples show natural language → parameters: +50 points

**Target:** All tools should score 80+ on all three metrics.

---

## Conclusion

The "zoom in 2x" bug was a symptom of a much larger problem: **our tool catalog quality is inconsistent and often insufficient for LLMs to make correct decisions**. 

The solution is not to add more patterns or capabilities, but to **dramatically improve the quality of our parameter descriptions and examples** so that LLMs can learn how to use existing tools correctly.

This is a significant undertaking (~150 tools), but it's essential for system reliability and user satisfaction. The good news is that we have a clear path forward and can prioritize based on tool usage and impact.