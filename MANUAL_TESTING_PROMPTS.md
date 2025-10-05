# Manual Testing Prompts for Asset Query Bug Fix

This document contains the exact prompts you can use to manually test the asset query bug fix in the frontend.

---

## 🎯 **What We Fixed**

The system was incorrectly selecting **Prometheus** tools for asset inventory queries instead of **asset-query/asset-list** tools.

**Expected Behavior:**
- Asset queries → Select `asset-query` or `asset-list` tools
- Monitoring queries → Select `prometheus` tools

---

## 📋 **Test Queries - Asset Management (Should Select Asset Tools)**

### ✅ **Basic Asset Queries**

```
Show me all assets
```
**Expected:**
- **Stage A Category:** `asset_management`
- **Stage A Action:** `list_assets` or `search_assets`
- **Stage B Tool:** `asset-query` or `asset-list` (NOT prometheus)

---

```
Show me all Linux servers
```
**Expected:**
- **Stage A Category:** `asset_management`
- **Stage A Action:** `list_assets`
- **Stage B Tool:** `asset-query` or `asset-list`
- **Entities:** OS type = "Linux"

---

```
How many assets do we have?
```
**Expected:**
- **Stage A Category:** `asset_management`
- **Stage A Action:** `count_assets` or `list_assets`
- **Stage B Tool:** `asset-query` or `asset-list`

---

```
Find all Windows servers
```
**Expected:**
- **Stage A Category:** `asset_management`
- **Stage A Action:** `list_assets` or `search_assets`
- **Stage B Tool:** `asset-query` or `asset-list`
- **Entities:** OS type = "Windows"

---

```
List all database servers
```
**Expected:**
- **Stage A Category:** `asset_management`
- **Stage A Action:** `list_assets`
- **Stage B Tool:** `asset-query` or `asset-list`
- **Entities:** Service type = "database"

---

### ✅ **Specific Asset Queries**

```
Get asset info for server web-01
```
**Expected:**
- **Stage A Category:** `asset_management`
- **Stage A Action:** `get_asset` or `get_asset_info`
- **Stage B Tool:** `asset-query`
- **Entities:** hostname = "web-01"

---

```
Search for assets with IP 10.0.1.5
```
**Expected:**
- **Stage A Category:** `asset_management`
- **Stage A Action:** `search_assets` or `find_asset`
- **Stage B Tool:** `asset-query`
- **Entities:** IP address = "10.0.1.5"

---

```
Show me all production assets
```
**Expected:**
- **Stage A Category:** `asset_management`
- **Stage A Action:** `list_assets`
- **Stage B Tool:** `asset-query` or `asset-list`
- **Entities:** environment = "production"

---

```
How many Linux servers are there?
```
**Expected:**
- **Stage A Category:** `asset_management`
- **Stage A Action:** `count_assets`
- **Stage B Tool:** `asset-query` or `asset-list`
- **Entities:** OS type = "Linux"

---

### ✅ **Edge Cases - Ambiguous/Informal Phrasing**

```
What servers do we have?
```
**Expected:**
- **Stage A Category:** `asset_management`
- **Stage A Action:** `list_assets` or `list_servers`
- **Stage B Tool:** `asset-query` or `asset-list`

---

```
Gimme all the assets
```
**Expected:**
- **Stage A Category:** `asset_management`
- **Stage A Action:** `list_assets`
- **Stage B Tool:** `asset-query` or `asset-list`

---

```
Show me all Linux servers in production with more than 16GB RAM
```
**Expected:**
- **Stage A Category:** `asset_management`
- **Stage A Action:** `list_assets` or `search_assets`
- **Stage B Tool:** `asset-query` or `asset-list`
- **Entities:** OS = "Linux", environment = "production", RAM > 16GB

---

## ❌ **Negative Test - Should NOT Select Asset Tools**

```
Show me CPU usage
```
**Expected:**
- **Stage A Category:** `monitoring` (NOT asset_management)
- **Stage A Action:** `get_metrics` or `check_status`
- **Stage B Tool:** `prometheus` (NOT asset tools)

This query should select Prometheus because it's asking for real-time metrics, not asset inventory.

---

## 🔍 **How to Verify Results in Frontend**

### **1. Check Stage A Output (Intent Classification)**

Look for the classification result:
```json
{
  "category": "asset_management",  // ✅ Should be this for asset queries
  "action": "list_assets",         // ✅ Or other asset actions
  "confidence": 0.95
}
```

**❌ WRONG (Bug Present):**
```json
{
  "category": "information",  // ❌ Wrong category
  "action": "get_info"
}
```

---

### **2. Check Stage B Output (Tool Selection)**

Look for the selected tools:
```json
{
  "selected_tools": [
    {
      "tool_name": "asset-query",  // ✅ Correct!
      "justification": "...",
      "inputs_needed": [...]
    }
  ]
}
```

**❌ WRONG (Bug Present):**
```json
{
  "selected_tools": [
    {
      "tool_name": "prometheus-query",  // ❌ Wrong tool!
      "justification": "..."
    }
  ]
}
```

---

### **3. Check Stage C Output (Execution Plan)**

Look for the execution steps:
```json
{
  "steps": [
    {
      "id": "step-1",
      "tool": "asset-query",  // ✅ Should match Stage B selection
      "description": "Query assets from inventory",
      "inputs": {...}
    }
  ]
}
```

---

## 🧪 **Quick Test Matrix**

| Query | Expected Category | Expected Tool | Bug Would Select |
|-------|------------------|---------------|------------------|
| "Show me all assets" | `asset_management` | `asset-query` | ❌ `prometheus` |
| "Show me all Linux servers" | `asset_management` | `asset-query` | ❌ `prometheus` |
| "How many assets?" | `asset_management` | `asset-query` | ❌ `prometheus` |
| "Get asset info for web-01" | `asset_management` | `asset-query` | ❌ `prometheus` |
| "Show me CPU usage" | `monitoring` | `prometheus` | ✅ `prometheus` |

---

## 📊 **What Changed in the Fix**

### **Stage A Changes (Intent Classification)**

**Added to System Prompt:**
```
- asset_management: Requests to query, list, search, count, or retrieve 
  information about infrastructure assets (servers, hosts, VMs, containers, 
  network devices)

ASSET MANAGEMENT: Use this category for infrastructure inventory queries:
- "show me all assets", "list servers", "find hosts", "what servers do we have"
- "show Linux servers", "find Windows machines", "list database servers"
- "how many assets", "count servers", "total hosts"
- "get asset info for X", "what's the IP of server Y", "find asset by hostname"
- These should be "asset_management" category, NOT "information" or "monitoring"
```

**Added Examples:**
```
- "show me all assets" -> {"category": "asset_management", "action": "list_assets", "confidence": 0.95}
- "find Linux servers" -> {"category": "asset_management", "action": "list_assets", "confidence": 0.92}
- "how many servers" -> {"category": "asset_management", "action": "count_assets", "confidence": 0.90}
- "get asset info for web-01" -> {"category": "asset_management", "action": "get_asset", "confidence": 0.93}
```

---

### **Stage B Changes (Tool Selection)**

**Added Capability Mappings:**
```python
# CapabilityMatcher - Intent to Capability
"asset_management_list_assets" → ["asset_query", "infrastructure_info", "resource_listing"]
"asset_management_search_assets" → ["asset_query", "infrastructure_info"]
"asset_management_count_assets" → ["asset_query", "resource_listing"]
"asset_management_get_asset" → ["asset_query", "infrastructure_info"]
"asset_management_find_asset" → ["asset_query", "infrastructure_info"]
"asset_management_query_assets" → ["asset_query", "infrastructure_info"]

# Selector - Action to Capability
"list_assets" → ["asset_query", "infrastructure_info", "resource_listing"]
"search_assets" → ["asset_query", "infrastructure_info"]
"count_assets" → ["asset_query", "resource_listing"]
"get_asset" → ["asset_query", "infrastructure_info"]
"find_asset" → ["asset_query", "infrastructure_info"]
"query_assets" → ["asset_query", "infrastructure_info"]

# Selector - Capability to Required Inputs
"asset_query" → ["search_term", "filters"]
"infrastructure_info" → ["asset_id", "hostname"]
"resource_listing" → ["resource_type", "filters"]
```

---

### **Database Changes**

**Updated Tool Capabilities:**
```sql
-- asset-query tool
UPDATE tool_catalog.tools 
SET capabilities = '["asset_query", "infrastructure_info"]'
WHERE name = 'asset-query';

-- asset-list tool
UPDATE tool_catalog.tools 
SET capabilities = '["asset_query", "infrastructure_info", "resource_listing"]'
WHERE name = 'asset-list';
```

**Before (Bug):**
```json
{
  "name": "asset-query",
  "capabilities": ["primary_capability"]  // ❌ Generic, doesn't match
}
```

**After (Fixed):**
```json
{
  "name": "asset-query",
  "capabilities": ["asset_query", "infrastructure_info"]  // ✅ Specific
}
```

---

## 🎯 **Success Criteria**

### ✅ **All Asset Queries Should:**
1. Be classified as `asset_management` category in Stage A
2. Select `asset-query` or `asset-list` tools in Stage B (NOT prometheus)
3. Create valid execution plans in Stage C
4. Have proper entity extraction (hostnames, IPs, OS types, etc.)

### ✅ **Monitoring Queries Should Still:**
1. Be classified as `monitoring` category in Stage A
2. Select `prometheus` tools in Stage B
3. NOT be affected by the asset management changes

---

## 🚀 **Testing in Frontend**

1. **Open the OpsConductor frontend**
2. **Enter each test query** from the sections above
3. **Check the pipeline output** for each stage
4. **Verify the selected tools** match expectations
5. **Confirm execution plans** are created correctly

---

## 📝 **Expected Test Results**

**All 13 E2E tests passed:**
- ✅ Show me all assets
- ✅ Show me all Linux servers
- ✅ How many assets do we have?
- ✅ Find all Windows servers
- ✅ List all database servers
- ✅ Get asset info for server web-01
- ✅ Search for assets with IP 10.0.1.5
- ✅ Show me all production assets
- ✅ How many Linux servers are there?
- ✅ Show me CPU usage (negative test - should use prometheus)
- ✅ What servers do we have? (ambiguous)
- ✅ Gimme all the assets (informal)
- ✅ Show me all Linux servers in production with more than 16GB RAM (complex)

---

## 🔧 **Troubleshooting**

### **If asset queries still select Prometheus:**

1. **Check database was updated:**
   ```sql
   SELECT name, capabilities 
   FROM tool_catalog.tools 
   WHERE name IN ('asset-query', 'asset-list');
   ```
   Should show `["asset_query", "infrastructure_info", ...]` NOT `["primary_capability"]`

2. **Check Stage A classification:**
   - Should be `asset_management` category
   - If not, check LLM prompt includes asset_management examples

3. **Check Stage B mappings:**
   - CapabilityMatcher should map `asset_management_*` intents
   - Selector should map asset actions to capabilities

4. **Check LLM model:**
   - Ensure using `qwen2.5:14b-instruct-q4_k_m` or similar capable model
   - Smaller models may not follow instructions correctly

---

## 📚 **Related Documentation**

- Full bug fix summary: `ASSET_QUERY_BUG_FIX_SUMMARY.md`
- Database fix script: `database/fix_asset_tool_capabilities.sql`
- E2E test suite: `tests/test_e2e_asset_queries_intensive.py`
- Stage B test suite: `tests/test_stage_b_asset_tool_selection.py`

---

**Last Updated:** 2025-01-XX  
**Status:** ✅ All tests passing - Production ready