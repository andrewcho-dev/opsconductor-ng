# Tool Catalog Upsert Utility

Utility for syncing tool definitions from YAML files to the database with automatic embedding generation.

## Overview

The `tools_upsert.py` script:
1. Reads YAML tool definitions from `config/tools/`
2. Validates required fields (key, name, short_desc)
3. Generates embeddings using the EmbeddingProvider
4. Upserts tools into the database (idempotent)

## Usage

### Command Line

```bash
# Dry-run (validate without writing)
python3 tools/tools_upsert.py --dry-run

# Sync to database
python3 tools/tools_upsert.py

# Custom glob pattern
python3 tools/tools_upsert.py --glob "config/tools/linux/*.yaml"

# Custom database connection
python3 tools/tools_upsert.py --dsn "postgresql://user:pass@host/db"
```

### Make Targets (Container-Safe)

```bash
# Validate tool definitions (dry-run)
make tools.seed

# Sync tools to database
make tools.sync
```

## YAML Format

### Required Fields

- `key`: Unique tool identifier (e.g., `linux.grep`)
- `name`: Human-readable tool name
- `short_desc`: Brief description (auto-truncated to 160 chars)

### Optional Fields

- `platform`: List of platforms (e.g., `["linux", "docker"]`)
- `tags`: List of tags (e.g., `["diagnostics", "search"]`)
- `meta`: Arbitrary metadata dict (e.g., `{cmd: "grep ..."}`)

### Example

```yaml
key: linux.grep
name: Linux Grep
short_desc: Search text in files on Linux using grep with regex support.
platform:
  - linux
tags:
  - diagnostics
  - search
  - text
meta:
  cmd: "grep -Rni '{{pattern}}' '{{path}}'"
```

## Embedding Generation

Embeddings are generated from: `{key} :: {short_desc}`

Example:
```
"linux.grep :: Search text in files on Linux using grep with regex support."
```

This produces a 128-dimensional vector stored in the `embedding` column.

## Database Schema

Tools are upserted into the `tool` table:

```sql
CREATE TABLE tool (
  id BIGSERIAL PRIMARY KEY,
  key TEXT UNIQUE NOT NULL,
  name TEXT NOT NULL,
  short_desc TEXT NOT NULL,
  platform TEXT[] DEFAULT '{}'::TEXT[],
  tags TEXT[] DEFAULT '{}'::TEXT[],
  meta JSONB DEFAULT '{}'::JSONB,
  embedding VECTOR(128),
  usage_count INTEGER DEFAULT 0,
  updated_at TIMESTAMPTZ DEFAULT now()
);
```

## Upsert Logic

The script uses PostgreSQL's `ON CONFLICT` for idempotent upserts:

```sql
INSERT INTO tool (key, name, short_desc, platform, tags, meta, embedding, updated_at)
VALUES ($1, $2, $3, $4, $5, $6, CAST($7 AS vector(128)), now())
ON CONFLICT (key) DO UPDATE
SET 
    name = EXCLUDED.name,
    short_desc = EXCLUDED.short_desc,
    platform = EXCLUDED.platform,
    tags = EXCLUDED.tags,
    meta = EXCLUDED.meta,
    embedding = EXCLUDED.embedding,
    updated_at = now()
```

**Key behaviors:**
- First run: Inserts new tools
- Subsequent runs: Updates existing tools (idempotent)
- `usage_count` is preserved on updates
- `updated_at` is refreshed on every upsert

## Directory Structure

```
config/tools/
├── linux/
│   ├── grep.yaml
│   ├── netstat.yaml
│   └── ...
├── windows/
│   ├── powershell.yaml
│   ├── netsh.yaml
│   └── ...
└── docker/
    └── ...
```

## Error Handling

The script handles errors gracefully:

- **Missing required fields**: Skips file with warning
- **Invalid YAML**: Skips file with parse error
- **Database errors**: Reports error but continues with other tools
- **Embedding errors**: Uses fallback deterministic embeddings

## Testing

Run unit tests:

```bash
python3 -m pytest tools/test_tools_upsert.py -v
```

Test coverage:
- ✅ YAML loading and validation
- ✅ Required field checking
- ✅ Description truncation
- ✅ Default value handling
- ✅ Dry-run mode
- ✅ Actual upsert logic
- ✅ Error handling

## Integration with Selector

After running `tools.sync`, tools are immediately available for semantic search:

```python
from selector.dao import select_topk

results = await select_topk(
    conn,
    intent="search for text in files",
    platform=["linux"],
    k=5
)
# Returns: [{'key': 'linux.grep', 'name': 'Linux Grep', ...}, ...]
```

## Performance

- **Embedding generation**: ~10ms per tool (deterministic fallback)
- **Database upsert**: ~5ms per tool
- **Total time**: ~15ms per tool

For 100 tools: ~1.5 seconds total

## Environment Variables

- `DATABASE_URL`: Default database connection string
- `EMBED_MODEL`: Optional sentence-transformers model name

## Exit Codes

- `0`: Success (all tools processed)
- `1`: Partial failure (some tools failed) or no database connection

## Idempotency

The script is fully idempotent:
- Running multiple times produces the same result
- Safe to run in CI/CD pipelines
- No duplicate tools created
- Existing tools are updated, not duplicated

## Example Workflow

```bash
# 1. Run migration to create table
make selector.migrate

# 2. Validate tool definitions
make tools.seed

# 3. Sync to database
make tools.sync

# 4. Verify tools are loaded
docker compose exec -T postgres psql -U $POSTGRES_USER -d $POSTGRES_DB -c "SELECT key, name FROM tool;"
```

## Troubleshooting

### No YAML files found

Check glob pattern matches your directory structure:
```bash
ls -la config/tools/**/*.yaml
```

### Database connection failed

Verify `DATABASE_URL` is set:
```bash
echo $DATABASE_URL
```

### Embedding errors

The script automatically falls back to deterministic embeddings if sentence-transformers is unavailable.

### YAML parse errors

Validate YAML syntax:
```bash
python3 -c "import yaml; yaml.safe_load(open('config/tools/linux/grep.yaml'))"
```

## See Also

- `selector/dao.py` - Database access layer for tool selection
- `selector/embeddings.py` - Embedding provider implementation
- `database/migrations/001_tool_schema_pgvector.sql` - Database schema