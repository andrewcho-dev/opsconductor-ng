# Understanding Your Tool System

## You're Feeling Lost - Let's Fix That

You've been working on this for months and feel like you have nothing to show. **I get it.** But here's the truth: **you've actually built something sophisticated** - you just don't understand how it works yet. Let me explain it simply.

---

## The Big Picture: How AI Knows About Tools

### **The Simple Answer:**

Your AI doesn't "know" about tools magically. Here's the flow:

```
1. You define tools in YAML files (pipeline/config/tools/)
2. You import them into PostgreSQL database (using migrate_tools_to_db.py)
3. AI queries the database when it needs to select a tool
4. AI picks the best tool based on what the user asked for
```

**That's it.** No magic. Just: YAML → Database → AI queries it.

---

## Your Tool System (Explained Simply)

### **What You Have:**

You have **170+ tools** defined in YAML files:

- **Linux tools**: systemctl, grep, ps, netstat, etc. (60+ tools)
- **Windows tools**: Get-Service, Get-Process, PowerShell cmdlets (30+ tools)
- **Network tools**: tcpdump, nmap, wireshark, etc. (20+ tools)
- **Cloud tools**: aws, gcloud, az (Azure) (10+ tools)
- **Container tools**: docker, kubectl, helm (20+ tools)
- **Database tools**: psql, mysql, mongosh (10+ tools)
- **Custom tools**: asset-query, asset-list, slack, email (10+ tools)

### **Where They Live:**

```
/home/opsconductor/opsconductor-ng/pipeline/config/tools/
├── linux/          (systemctl.yaml, grep.yaml, ps.yaml, etc.)
├── windows/        (get_service.yaml, powershell.yaml, etc.)
├── network/        (tcpdump.yaml, nmap.yaml, etc.)
├── cloud/          (aws.yaml, gcloud.yaml, az.yaml)
├── container/      (docker.yaml, kubectl.yaml, helm.yaml)
├── database/       (psql.yaml, mysql.yaml, mongosh.yaml)
├── custom/         (asset_query.yaml, slack_cli.yaml, etc.)
└── monitoring/     (prometheus.yaml, grafana.yaml, etc.)
```

---

## How a Tool is Defined (Example)

Let's look at `asset_query.yaml` - the tool that SHOULD be used for "how many assets":

```yaml
tool_name: asset-query
version: '1.0'
description: Query asset inventory
platform: custom
category: asset

# What this tool is good at
capabilities:
  asset_management:
    description: Query and manage asset inventory
    
    patterns:
      execute:
        description: Execute asset-query command
        
        # These phrases should trigger this tool
        typical_use_cases:
          - "query asset inventory"
          - "count assets"
          - "list assets"
          - "get asset information"
        
        # Performance characteristics
        time_estimate_ms: 500      # Fast (0.5 seconds)
        cost_estimate: 1           # Cheap
        complexity_score: 0.2      # Simple
        
        # What it needs to run
        required_inputs:
          - name: host
            type: string
            description: Target host
```

**Key Parts:**

1. **`capabilities`**: What the tool can do (`asset_management`)
2. **`typical_use_cases`**: Phrases that should trigger this tool
3. **`time_estimate_ms`**: How long it takes
4. **`cost_estimate`**: How expensive it is
5. **`required_inputs`**: What parameters it needs

---

## How AI Selects Tools (The Flow)

Here's what happens when you ask "How many assets do we have?":

### **Current Flow (4 Stages - BROKEN):**

```
User: "How many assets do we have?"
    ↓
Stage A (Classifier):
- Analyzes question
- Should extract: capabilities = ["asset_management"]
- BUT: Returns capabilities = [] ❌
    ↓
Stage B (Selector):
- Queries database for tools with "asset_management" capability
- Finds: asset-query tool
- BUT: No capabilities from Stage A, so skips tool selection ❌
    ↓
Stage C (Planner):
- Skipped (no tools selected) ❌
    ↓
Stage D (Answerer):
- No tools to execute
- LLM makes up answer: "You have 25 assets" ❌ HALLUCINATION
```

### **What SHOULD Happen:**

```
User: "How many assets do we have?"
    ↓
Stage A (Classifier):
- Analyzes question
- Extracts: capabilities = ["asset_management"] ✅
    ↓
Stage B (Selector):
- Queries database: "Give me tools with 'asset_management' capability"
- Database returns: asset-query tool
- AI selects: asset-query ✅
    ↓
Stage C (Planner):
- Creates execution plan:
  1. Call asset-query API
  2. Count results
  3. Filter by OS if needed ✅
    ↓
Stage D (Answerer):
- Executes asset-query
- Gets REAL data: 47 assets, 23 Windows
- Formats response: "You have 47 assets. 23 are Windows." ✅
```

---

## How to Add a New Tool

Let's say you want to add a tool to check disk space on Windows servers.

### **Step 1: Create YAML File**

Create: `pipeline/config/tools/windows/get_disk_space.yaml`

```yaml
tool_name: "Get-PSDrive"
version: "1.0"
description: "Check disk space on Windows"
platform: "windows"
category: "system"

defaults:
  accuracy_level: "real-time"
  freshness: "live"
  data_source: "direct"

capabilities:
  disk_management:
    description: "Check disk space and usage"
    
    patterns:
      check_disk_space:
        description: "Check available disk space"
        
        typical_use_cases:
          - "check disk space"
          - "how much disk space"
          - "disk usage"
          - "free space on disk"
        
        time_estimate_ms: "1000"
        cost_estimate: "1"
        complexity_score: 0.2
        
        scope: "single_item"
        completeness: "complete"
        
        policy:
          max_cost: 5
          requires_approval: false
          production_safe: true
          max_execution_time: 30
        
        preference_match:
          speed: 0.9
          accuracy: 1.0
          cost: 0.95
          complexity: 0.9
          completeness: 1.0
        
        required_inputs:
          - name: "host"
            type: "string"
            description: "Target Windows host"
            validation: ".*"
        
        optional_inputs:
          - name: "drive_letter"
            type: "string"
            description: "Specific drive to check (e.g., C:)"
            default: "all"

metadata:
  author: "Your Name"
  created: "2025-01-20"
  tags:
    - "windows"
    - "disk"
    - "storage"
  documentation_url: "https://docs.microsoft.com/powershell/module/microsoft.powershell.management/get-psdrive"
```

### **Step 2: Import to Database**

```bash
# Start your system (so database is running)
cd /home/opsconductor/opsconductor-ng
docker-compose up -d

# Import the tool
python3 scripts/migrate_tools_to_db.py --file pipeline/config/tools/windows/get_disk_space.yaml

# Verify it was imported
python3 scripts/verify_tool_catalog.py
```

### **Step 3: Test It**

Ask the AI: "How much disk space is left on server-01?"

The AI should now:
1. Extract capability: `disk_management`
2. Query database for tools with that capability
3. Find your new `Get-PSDrive` tool
4. Execute it
5. Return real results

---

## The Database Structure

Your tools are stored in PostgreSQL with this structure:

```
tool_catalog schema:
├── tools                    (Main tool definitions)
│   ├── id
│   ├── tool_name           (e.g., "systemctl")
│   ├── version
│   ├── description
│   ├── platform            (linux, windows, network, etc.)
│   ├── category            (system, network, automation, etc.)
│   └── defaults
│
├── tool_capabilities        (What each tool can do)
│   ├── id
│   ├── tool_id
│   ├── capability_name     (e.g., "service_management")
│   └── description
│
└── tool_patterns           (Specific use cases)
    ├── id
    ├── capability_id
    ├── pattern_name        (e.g., "start_service")
    ├── typical_use_cases   (phrases that trigger this)
    ├── time_estimate_ms
    ├── cost_estimate
    └── required_inputs
```

### **How AI Queries It:**

When Stage B needs to select a tool:

```python
# Stage B asks database:
"Give me all tools that have 'asset_management' capability"

# Database returns:
[
  {
    "tool_name": "asset-query",
    "capability": "asset_management",
    "pattern": "execute",
    "typical_use_cases": ["count assets", "list assets"],
    "time_estimate_ms": 500,
    "cost_estimate": 1
  }
]

# AI picks the best match
```

---

## Why Your System Isn't Working

### **The Problem:**

Stage A (Classifier) isn't extracting the right capabilities. When you ask "How many assets?", it should return:

```json
{
  "category": "asset_management",
  "capabilities": ["asset_management"]  ← This is empty!
}
```

But it's returning:

```json
{
  "category": "asset_management",
  "capabilities": []  ← EMPTY!
}
```

### **Why This Breaks Everything:**

- Stage B sees `capabilities = []`
- Stage B thinks: "No tools needed, this is just a question"
- Stage B skips tool selection
- Stage D has no tools to execute
- Stage D's LLM makes up an answer → **HALLUCINATION**

---

## The Fix (3 Options)

### **Option 1: Fix Stage A Prompt (Quick - 30 min)**

Make Stage A's prompt explicitly map questions to capabilities:

```
If user asks about assets → return ["asset_management"]
If user asks about services → return ["service_management"]
If user asks about disk space → return ["disk_management"]
```

**Pros:** Quick fix, keeps architecture
**Cons:** Still fragile, might miss edge cases

### **Option 2: Merge Stage A + B (Better - 3 hours)**

Combine "understanding" and "tool selection" into one stage:

```
User question → AI understands + selects tools → Execute → Answer
```

**Pros:** More reliable, simpler, less information loss
**Cons:** Requires refactoring

### **Option 3: Add Safety Net (Safest - 1 hour)**

Add validation in Stage B:

```python
# If Stage A says "asset_management" but no capabilities
if decision.category == "asset_management" and not decision.capabilities:
    # Force the capability
    decision.capabilities = ["asset_management"]
```

**Pros:** Catches mistakes, works with current architecture
**Cons:** Band-aid solution, doesn't fix root cause

---

## What You Should Do RIGHT NOW

### **Immediate Action (Get Something Working):**

1. **Fix Stage A prompt** (30 min) - Add explicit capability mapping
2. **Add Stage B safety net** (15 min) - Catch asset queries that slip through
3. **Test with asset queries** (15 min) - Verify it works

**Total time: 1 hour to working system**

### **After That Works:**

1. **Simplify architecture** - Consider merging stages
2. **Add more tools** - Now you know how!
3. **Build confidence** - One working feature beats 10 broken ones

---

## Key Takeaways

1. **Tools are just YAML files** - You define them, import to database
2. **AI queries database** - No magic, just SQL queries
3. **Capabilities are the key** - They connect user questions → tools
4. **Your system is close** - Just needs capability extraction fixed
5. **You're not failing** - You built something complex, just need to debug it

---

## Next Steps

**Want me to implement the fixes?** I can:

1. Fix Stage A prompt to extract capabilities correctly
2. Add Stage B safety net to catch missed capabilities
3. Remove Stage D fast path to prevent hallucinations
4. Test with your exact failing query

**This will take 1 hour and you'll have working asset queries.**

Say the word and I'll do it.