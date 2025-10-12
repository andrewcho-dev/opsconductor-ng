# Selector DAO - Vector-Based Tool Selection

## Overview

The `selector/dao.py` module provides database access functions for semantic tool selection using pgvector. It enables efficient similarity search over tool embeddings with optional platform filtering.

## Features

- **Vector Similarity Search**: Uses pgvector's cosine distance operator (`<=>`) for semantic matching
- **Platform Filtering**: Optional array overlap filtering using PostgreSQL's `&&` operator
- **NULL Handling**: Gracefully handles tools without embeddings (sorted last)
- **Tie-Breaking**: Secondary sorting by `usage_count DESC, updated_at DESC`
- **Asyncpg-Based**: Pure asyncpg implementation (no ORM overhead)
- **Pluggable Embeddings**: Works with any EmbeddingProvider (ML models or deterministic fallback)

## API

### `_vec_literal(vec: list[float]) -> str`

Converts a Python list of floats to PostgreSQL vector literal format.

```python
>>> _vec_literal([0.1, 0.2, 0.3])
'[0.1,0.2,0.3]'
```

### `select_topk(conn, intent, platform=None, k=8, provider=None) -> list[dict]`

Select top-k tools using vector similarity search.

**Parameters:**
- `conn` (asyncpg.Connection): Active database connection
- `intent` (str): User intent text to embed and search for
- `platform` (list[str] | None): Optional platform filter (e.g., `['linux', 'docker']`)
- `k` (int): Maximum number of results (default: 8)
- `provider` (EmbeddingProvider | None): Optional embedding provider

**Returns:**
- List of dicts with keys: `key`, `name`, `short_desc`, `platform`, `tags`

**Example:**
```python
import asyncpg
from selector.dao import select_topk

conn = await asyncpg.connect(dsn=DATABASE_URL)
results = await select_topk(
    conn,
    "scan network for vulnerabilities",
    platform=["linux"],
    k=5
)

for tool in results:
    print(f"{tool['key']}: {tool['short_desc']}")
```

## SQL Query Structure

The function executes the following query:

```sql
WITH q AS (SELECT CAST($1 AS vector(128)) AS v)
SELECT 
    key,
    name,
    LEFT(short_desc, 160) AS short_desc,
    platform,
    tags
FROM tool, q
WHERE ($2::text[] = '{}'::text[] OR platform && $2::text[])
ORDER BY embedding <=> q.v NULLS LAST, usage_count DESC, updated_at DESC
LIMIT $3
```

**Key Features:**
- `$1`: Vector literal string (e.g., `'[0.1,0.2,...]'`)
- `$2`: Platform array (empty array `[]` = no filter)
- `$3`: Limit (k)
- `<=>`: Cosine distance operator (pgvector)
- `NULLS LAST`: Tools without embeddings sorted last
- `platform &&`: Array overlap for platform filtering

## Platform Filtering Logic

The WHERE clause implements efficient platform filtering:

```sql
WHERE ($2::text[] = '{}'::text[] OR platform && $2::text[])
```

- If `platform=None` or `platform=[]`: Pass empty array → no filtering (all tools)
- If `platform=['linux', 'docker']`: Only tools with overlapping platforms

## Testing

### Unit Tests
```bash
pytest selector/test_dao.py -v
```

Tests cover:
- Vector literal formatting
- SQL query structure
- Platform filtering
- NULL embedding handling
- Multiple results
- Default provider creation

### Integration Tests
```bash
DATABASE_URL=postgresql://user:pass@localhost/db pytest selector/test_dao_integration.py -v
```

Requires:
1. Running PostgreSQL with pgvector
2. Migrated schema: `make selector.migrate`
3. Populated tool table

### Example Usage
```bash
export DATABASE_URL="postgresql://opsconductor:opsconductor_secure_2024@localhost/opsconductor"
python3 selector/example_dao_usage.py
```

## Dependencies

- `asyncpg`: PostgreSQL async driver
- `selector.embeddings`: EmbeddingProvider and embed_intent
- PostgreSQL with pgvector extension

## Performance Considerations

1. **Index Usage**: The IVFFlat index on `embedding` column enables fast similarity search
2. **Platform Filter**: GIN index on `platform` array speeds up overlap checks
3. **Tie-Breakers**: B-tree indexes on `usage_count` and `updated_at` optimize secondary sorting
4. **LIMIT**: Applied early to minimize result set processing

## Error Handling

- **NULL Embeddings**: Handled via `NULLS LAST` in ORDER BY
- **Empty Results**: Returns empty list (no exceptions)
- **Connection Errors**: Propagated to caller (asyncpg exceptions)
- **Invalid Platform**: No error - empty array treated as "no filter"

## Future Enhancements

Potential improvements:
- Distance/similarity scores in results
- Hybrid search (vector + full-text)
- Query result caching
- Batch embedding support
- Custom distance metrics (L2, inner product)