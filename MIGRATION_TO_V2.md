# Migration Guide: Pipeline V1 → V2

## What Changed?

### Old Architecture (V1):
```
User Request
    ↓
Stage A (Classifier) - Extracts intent + capabilities
    ↓ (DecisionV1)
Stage B (Selector) - Selects tools based on capabilities
    ↓ (SelectionV1)
Stage C (Planner) - Creates execution plan
    ↓ (PlanV1)
Stage D (Answerer) - Generates response
    ↓ (ResponseV1)
Stage E (Executor) - Executes plan
    ↓
Response
```

**Problem:** The Stage A → Stage B handoff was fragile. If Stage A didn't extract capabilities correctly, Stage B couldn't find tools, leading to hallucinations.

### New Architecture (V2):
```
User Request
    ↓
Stage AB (Combined) - Understands intent + selects tools IN ONE PASS
    ↓ (SelectionV1)
Stage C (Planner) - Creates execution plan
    ↓ (PlanV1)
Stage D (Answerer) - Generates response
    ↓ (ResponseV1)
Stage E (Executor) - Executes plan
    ↓
Response
```

**Solution:** Stage AB sees the full context (user request + available tools) in ONE LLM call, making tool selection more reliable.

---

## Benefits of V2

1. **More Reliable**: No capability extraction failures
2. **Simpler**: One less stage to debug
3. **Faster**: One less LLM call (Stage A + Stage B → Stage AB)
4. **Better Context**: LLM sees everything at once
5. **Easier to Maintain**: Less code, fewer failure points

---

## How to Migrate

### Option 1: Switch Completely to V2 (Recommended)

**Step 1:** Update your main application to use `PipelineOrchestratorV2`:

```python
# OLD (V1)
from pipeline.orchestrator import PipelineOrchestrator
orchestrator = PipelineOrchestrator(llm_client)

# NEW (V2)
from pipeline.orchestrator_v2 import PipelineOrchestratorV2
orchestrator = PipelineOrchestratorV2(llm_client)
```

**Step 2:** Test with your common queries:

```bash
python3 scripts/test_pipeline_v2.py
```

**Step 3:** If everything works, you're done! 🎉

### Option 2: Run Both in Parallel (Safe Migration)

Keep V1 running while testing V2:

```python
from pipeline.orchestrator import PipelineOrchestrator
from pipeline.orchestrator_v2 import PipelineOrchestratorV2

# Initialize both
orchestrator_v1 = PipelineOrchestrator(llm_client)
orchestrator_v2 = PipelineOrchestratorV2(llm_client)

# Route based on feature flag
if use_v2:
    result = await orchestrator_v2.process_request(user_request)
else:
    result = await orchestrator_v1.process_request(user_request)
```

### Option 3: Gradual Migration by Request Type

Route specific request types to V2:

```python
# Asset queries use V2 (more reliable)
if "asset" in user_request.lower() or "how many" in user_request.lower():
    result = await orchestrator_v2.process_request(user_request)
else:
    result = await orchestrator_v1.process_request(user_request)
```

---

## Testing V2

### Quick Test

```bash
# Test asset query (the problematic case)
python3 -c "
import asyncio
from pipeline.orchestrator_v2 import PipelineOrchestratorV2
from llm.factory import get_default_llm_client

async def test():
    llm = get_default_llm_client()
    await llm.connect()
    
    orchestrator = PipelineOrchestratorV2(llm)
    await orchestrator.initialize()
    
    result = await orchestrator.process_request('How many assets do we have?')
    print(f'Response: {result.response.message}')
    print(f'Success: {result.success}')
    print(f'Tools selected: {len(result.intermediate_results[\"stage_ab\"].selected_tools)}')

asyncio.run(test())
"
```

### Comprehensive Test

```bash
python3 scripts/test_pipeline_v2.py
```

This will test:
- Asset queries (how many assets?)
- Service management (restart nginx)
- Information requests (what is Kubernetes?)
- Complex queries (show me Windows servers)

---

## What to Watch For

### 1. Tool Selection Accuracy

**V1 Problem:**
```
User: "How many assets do we have?"
Stage A: capabilities = []  ❌ (missed it!)
Stage B: No tools selected
Stage D: Hallucinates answer
```

**V2 Solution:**
```
User: "How many assets do we have?"
Stage AB: Sees "asset-query" tool in database
Stage AB: Selects "asset-query" tool ✅
Stage D: Uses real data
```

### 2. Performance

V2 should be **faster** because:
- One less LLM call (A + B → AB)
- One less stage transition
- Less data serialization

Expected improvement: **20-30% faster**

### 3. Error Messages

V2 has clearer error messages:

```
# V1 (confusing)
"Tool selection failed: No capabilities provided"

# V2 (clear)
"Combined understanding + selection failed: LLM could not parse available tools"
```

---

## Rollback Plan

If V2 doesn't work, you can instantly rollback:

```python
# Just switch back to V1
from pipeline.orchestrator import PipelineOrchestrator
orchestrator = PipelineOrchestrator(llm_client)
```

**V1 is still there!** We didn't delete anything.

---

## API Compatibility

### ✅ Compatible (No Changes Needed)

Both V1 and V2 have the same interface:

```python
result = await orchestrator.process_request(
    user_request="How many assets?",
    request_id="optional-id",
    context={"key": "value"},
    session_id="session-123",
    progress_callback=my_callback
)

# Result structure is identical
print(result.response.message)
print(result.metrics.total_duration_ms)
print(result.success)
```

### ⚠️ Internal Structure Changed

If you're accessing intermediate results:

```python
# V1
decision = result.intermediate_results["stage_a"]  # DecisionV1
selection = result.intermediate_results["stage_b"]  # SelectionV1

# V2
selection = result.intermediate_results["stage_ab"]  # SelectionV1 (no DecisionV1)
```

---

## Configuration

V2 uses the same environment variables as V1:

```bash
# LLM Configuration
LLM_PROVIDER=ollama
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=llama3.2:latest

# Database Configuration
DATABASE_URL=postgresql://user:pass@localhost:5432/opsconductor

# Cache Configuration (optional)
CACHE_ENABLED=true
REDIS_URL=redis://localhost:6379
```

No new configuration needed!

---

## Monitoring

### Health Check

```python
health = await orchestrator.health_check()
print(health)
```

**V1 Output:**
```json
{
  "orchestrator": "healthy",
  "stages": {
    "stage_a": "healthy",
    "stage_b": "healthy",
    "stage_c": "healthy",
    "stage_d": "healthy"
  }
}
```

**V2 Output:**
```json
{
  "orchestrator": "healthy",
  "version": "2.0.0",
  "stages": {
    "stage_ab": {
      "stage_ab": "healthy",
      "components": {
        "llm_client": "healthy",
        "tool_catalog": "healthy (170 tools)"
      }
    }
  },
  "metrics": {
    "success_rate": 0.95
  }
}
```

### Metrics

```python
metrics = orchestrator.get_metrics()
print(metrics)
```

**V2 Output:**
```json
{
  "total_requests": 100,
  "average_duration_ms": 2500,
  "stage_averages": {
    "stage_ab": 800,
    "stage_c": 600,
    "stage_d": 900,
    "stage_e": 200
  },
  "success_rate": 0.95
}
```

---

## Troubleshooting

### Issue: "No tools selected for asset query"

**V1:** Stage A didn't extract capabilities
**V2:** Check if tools are in database

```bash
# Verify tools are loaded
python3 -c "
import asyncio
from pipeline.services.tool_catalog_service import ToolCatalogService

async def check():
    catalog = ToolCatalogService()
    tools = await catalog.get_all_tools()
    print(f'Total tools: {len(tools)}')
    
    # Check for asset-query tool
    asset_tools = [t for t in tools if 'asset' in t['tool_name'].lower()]
    print(f'Asset tools: {[t[\"tool_name\"] for t in asset_tools]}')

asyncio.run(check())
"
```

### Issue: "LLM response parsing failed"

The LLM might not be returning valid JSON. Check the prompt:

```python
# Enable debug logging
import logging
logging.basicConfig(level=logging.DEBUG)

# Run request
result = await orchestrator.process_request("test query")
```

Look for the LLM response in logs and verify it's valid JSON.

### Issue: "Stage AB slower than Stage A + B"

This shouldn't happen, but if it does:

1. Check if you're loading too many tools (>500)
2. Reduce tool descriptions in the prompt
3. Increase LLM timeout

---

## FAQ

### Q: Can I use V1 and V2 at the same time?

**A:** Yes! They're completely independent. You can run both and compare results.

### Q: Will V2 work with my custom tools?

**A:** Yes! V2 uses the same database tool catalog as V1. Any tools you've added will work.

### Q: Do I need to retrain anything?

**A:** No! V2 uses the same LLM and prompts. No training needed.

### Q: What if V2 breaks something?

**A:** Just switch back to V1. Nothing is deleted or modified.

### Q: Is V2 production-ready?

**A:** Yes! It's simpler and more reliable than V1. But test thoroughly first.

### Q: Will you remove V1?

**A:** Not immediately. V1 will stay for at least 3 months to allow gradual migration.

---

## Next Steps

1. **Test V2** with your common queries
2. **Compare results** with V1
3. **Switch to V2** if results are better
4. **Report issues** if you find any

---

## Support

If you encounter issues:

1. Check logs: `tail -f logs/pipeline.log`
2. Run health check: `python3 scripts/health_check_v2.py`
3. Compare with V1: `python3 scripts/compare_v1_v2.py`

---

## Summary

**V2 is simpler, faster, and more reliable than V1.**

The key improvement: **Stage AB combines understanding + selection in ONE pass**, eliminating the fragile capability extraction that was causing hallucinations.

**Recommended action:** Test V2 with asset queries and switch if it works better.