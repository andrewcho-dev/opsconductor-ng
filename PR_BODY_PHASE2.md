## Summary
Phase 2: Tool Catalog & Retrieval (pgvector)

This PR implements semantic tool search using pgvector to enable efficient tool selection in Stage B.

Closes #[issue_id_1] #[issue_id_2] #[issue_id_3] #[issue_id_4]

## Changes
- [x] Implements exactly one sub-issue/feature - Phase 2 tool catalog and retrieval
- [x] Uses `shared/contracts` models (no ad-hoc dicts) - Uses ToolStub from db.retrieval
- [x] Adds/updates JSON Schema if contracts changed - N/A (uses existing models)
- [x] Adds/updates tests (unit/contract/snapshot as applicable) - Added comprehensive unit and snapshot tests
- [x] Token budget respected (Stage A/B prompts with ≥30% headroom) - Snapshot test verifies ≥30% headroom
- [x] Structured JSON logs include `trace_id` (and `run_id`/`plan_id` if applicable) - Uses shared.logging.json_log
- [x] No full tool specs in Stage A prompts - Snapshot test verifies only stubs returned
- [x] Docs updated (if needed) - Migration includes comprehensive notes

## Evidence
- [x] CI green (lint, type check, tests) - All tests pass, mypy succeeds
- [ ] Prompt snapshot attached (Stage A/B if touched) - N/A for this PR
- [x] Example trace screenshot or log snippet with `trace_id` - Tests use json_log with trace context

## Risk/rollback
- Low risk: New infrastructure, no changes to existing code
- Migration is idempotent (CREATE IF NOT EXISTS)
- Backfill script can be run multiple times safely (UPSERT)
- No rollback needed - additive changes only

## Implementation Details

### Database Migration (0001_pgvector.sql)
**Purpose**: Enable semantic search for tool selection

**Components**:
- pgvector extension
- `tool_catalog.tool_embeddings` table:
  - `tool_id` (PK, FK to tools)
  - `embedding` (vector(768))
  - `embedding_model` (VARCHAR)
  - `embedding_provider` (VARCHAR)
  - Timestamps
- IVFFlat index for cosine similarity search (lists=100)
- `tools_with_embeddings` view for easy querying
- `updated_at` trigger

**Notes**:
- Supports 768-dimensional embeddings (standard for most models)
- Uses cosine distance operator `<=>`
- Index optimized for ~100-1000 tools

### Backfill Script (scripts/backfill_tool_embeddings.py)
**Purpose**: Generate and store embeddings for all enabled tools

**Features**:
- Environment-driven configuration:
  - `EMBEDDING_PROVIDER`: openai, huggingface, local
  - `EMBEDDING_MODEL`: model name (default: text-embedding-3-small)
  - `EMBEDDING_API_KEY`: API key for provider
  - `EMBEDDING_DIMENSION`: vector dimension (default: 768)
  - `DATABASE_URL`: PostgreSQL connection string
- Multi-provider support:
  - OpenAI API
  - HuggingFace Inference API
  - Local sentence-transformers
- UPSERT logic (safe to re-run)
- Automatic ANALYZE after completion
- Structured logging with json_log

**Usage**:
```bash
export EMBEDDING_PROVIDER=openai
export EMBEDDING_API_KEY=sk-...
export EMBEDDING_MODEL=text-embedding-3-small
python3 scripts/backfill_tool_embeddings.py
```

### Retrieval DAO (db/retrieval.py)
**Purpose**: Semantic search interface for tool selection

**API**:
```python
async def search_tools(
    conn: asyncpg.Connection,
    query_embedding: List[float],
    top_k: int = 50,
    platform: Optional[str] = None,
) -> List[ToolStub]
```

**Features**:
- Cosine similarity search using pgvector `<=>` operator
- Returns minimal `ToolStub` objects (id, name, description, platform, category)
- Optional platform filtering
- Converts cosine distance to similarity score (0-1 range)
- Ordered by similarity (most similar first)

### Selector Module (selector/candidates.py)
**Purpose**: Generate candidate tools from user intent

**API**:
```python
async def candidate_tools_from_intent(
    conn: asyncpg.Connection,
    text: str,
    k: int = 50,
    platform: Optional[str] = None,
) -> List[ToolStub]
```

**Features**:
- Semantic search using embeddings
- Always-include tools via `ALWAYS_INCLUDE_TOOLS` env var
- Fallback to always-include tools if embedding fails
- Returns minimal stubs (no full tool specs)
- Token budget aware (tested in snapshot tests)

**Environment Variables**:
- `ALWAYS_INCLUDE_TOOLS`: Comma-separated tool names to always include

### Tests

#### db/test_retrieval_order.py (5 tests)
Unit tests for retrieval logic using mock data:
- ✅ Results ordered by similarity
- ✅ Platform filter applied correctly
- ✅ top_k parameter respected
- ✅ Empty results handled gracefully
- ✅ Missing descriptions handled

#### selector/test_candidates_snapshot.py (3 tests)
Snapshot tests for candidate selection:
- ✅ Returns only minimal stubs (no full specs)
- ✅ Prompt size below token budget with ≥30% headroom
- ✅ Always-include tools are added

**Token Budget Verification**:
```
CTX_SIZE = 8192
HEADROOM = 0.30 (30%)
BASE_TOKENS = 900
Budget = 8192 - (8192 * 0.30) - 900 = 4,834 tokens

Test verifies:
- 50 tool stubs fit within budget
- At least 30% headroom remaining
```

### CI Updates
Updated `.github/workflows/ci.yml`:
- Added dependencies: `pytest-asyncio`, `asyncpg`
- Added Phase 2 type checking with mypy
- Added Phase 2 unit tests (no DB service required)
- All tests run without PostgreSQL (using mocks)

## Test Results

```bash
# Phase 2 tests
pytest db/test_retrieval_order.py selector/test_candidates_snapshot.py -v
# 8 passed in 0.30s

# Type checking
mypy --ignore-missing-imports db/retrieval.py selector/candidates.py
# Success: no issues found in 2 source files

# All tests (Phase 0 + Phase 2)
pytest tests/test_shared_*.py db/test_retrieval_order.py selector/test_candidates_snapshot.py -v
# 20 passed
```

## Next Steps
After this PR is merged:
1. Run database migration: `psql -f database/migrations/0001_pgvector.sql`
2. Run backfill script to generate embeddings
3. Configure `ALWAYS_INCLUDE_TOOLS` environment variable
4. Integrate with Stage B selector (Phase 3)

## Architecture Notes

**Why pgvector?**
- Native PostgreSQL extension (no external service)
- Efficient cosine similarity search
- Scales to thousands of tools
- Supports multiple index types (IVFFlat, HNSW)

**Why minimal stubs?**
- Token budget constraints (8192 ctx, 30% headroom)
- Stage B only needs basic info for selection
- Full specs loaded only for selected tools
- Enables 50+ candidates in prompt

**Why always-include tools?**
- Ensures critical tools are never missed
- Useful for common operations (asset-query, etc.)
- Configurable via environment variable
- Added after semantic search (no duplicates)