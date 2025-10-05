# 🚀 Quick Test Prompts - Copy & Paste

## ✅ Asset Queries (Should Select Asset Tools, NOT Prometheus)

```
Show me all assets
```

```
Show me all Linux servers
```

```
How many assets do we have?
```

```
Find all Windows servers
```

```
List all database servers
```

```
Get asset info for server web-01
```

```
Search for assets with IP 10.0.1.5
```

```
Show me all production assets
```

```
How many Linux servers are there?
```

```
What servers do we have?
```

```
Gimme all the assets
```

```
Show me all Linux servers in production with more than 16GB RAM
```

---

## ❌ Negative Test (Should Select Prometheus, NOT Asset Tools)

```
Show me CPU usage
```

---

## 🎯 Expected Results

### For Asset Queries:
- **Stage A Category:** `asset_management`
- **Stage A Action:** `list_assets`, `search_assets`, `count_assets`, `get_asset`, etc.
- **Stage B Tool:** `asset-query` or `asset-list` ✅
- **Stage B Tool:** NOT `prometheus` ❌

### For Monitoring Query:
- **Stage A Category:** `monitoring`
- **Stage A Action:** `get_metrics`, `check_status`
- **Stage B Tool:** `prometheus` ✅

---

## 🔍 Quick Visual Check

**✅ CORRECT (Bug Fixed):**
```
User: "Show me all assets"
Stage A: category="asset_management", action="list_assets"
Stage B: tool="asset-query"
Stage C: plan created with asset-query
```

**❌ WRONG (Bug Present):**
```
User: "Show me all assets"
Stage A: category="information", action="get_info"
Stage B: tool="prometheus-query"  ← WRONG!
Stage C: plan created with prometheus
```

---

## 📊 Test Matrix

| Query | Expected Tool | Bug Would Select |
|-------|--------------|------------------|
| Show me all assets | `asset-query` ✅ | `prometheus` ❌ |
| Show me all Linux servers | `asset-query` ✅ | `prometheus` ❌ |
| How many assets? | `asset-query` ✅ | `prometheus` ❌ |
| Get asset info for web-01 | `asset-query` ✅ | `prometheus` ❌ |
| **Show me CPU usage** | `prometheus` ✅ | `prometheus` ✅ |

---

**Status:** ✅ All 18 tests passing (5 Stage B + 13 E2E)