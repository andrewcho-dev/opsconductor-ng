# Tool Catalog Workflow

## Visual Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                     Tool Catalog Workflow                        │
└─────────────────────────────────────────────────────────────────┘

1. YAML Definition
   ┌──────────────────────────────────────┐
   │ config/tools/linux/grep.yaml         │
   │                                      │
   │ key: linux.grep                      │
   │ name: Linux Grep                     │
   │ short_desc: Search text in files...  │
   │ platform: ["linux"]                  │
   │ tags: ["diagnostics", "search"]      │
   │ meta: {cmd: "grep ..."}              │
   └──────────────────────────────────────┘
                    │
                    ▼
2. Load & Validate (tools_upsert.py)
   ┌──────────────────────────────────────┐
   │ • Parse YAML                         │
   │ • Validate required fields           │
   │ • Truncate short_desc to 160 chars   │
   │ • Set defaults for optional fields   │
   └──────────────────────────────────────┘
                    │
                    ▼
3. Generate Embedding (EmbeddingProvider)
   ┌──────────────────────────────────────┐
   │ Input: "linux.grep :: Search text    │
   │         in files on Linux..."        │
   │                                      │
   │ Output: [0.1, -0.2, 0.3, ... ]       │
   │         (128 dimensions)             │
   └──────────────────────────────────────┘
                    │
                    ▼
4. UPSERT to Database
   ┌──────────────────────────────────────┐
   │ INSERT INTO tool (...)               │
   │ VALUES (...)                         │
   │ ON CONFLICT (key) DO UPDATE          │
   │ SET name=EXCLUDED.name, ...          │
   └──────────────────────────────────────┘
                    │
                    ▼
5. Tool Available for Search
   ┌──────────────────────────────────────┐
   │ SELECT key, name, short_desc         │
   │ FROM tool                            │
   │ WHERE platform && $1                 │
   │ ORDER BY embedding <=> $2            │
   │ LIMIT $3                             │
   └──────────────────────────────────────┘
```

## Command Flow

### Dry-Run Mode (Validation)

```
$ make tools.seed
    │
    ├─> docker compose exec -T postgres python3 tools/tools_upsert.py --dry-run
    │
    ├─> Find YAML files (config/tools/**/*.yaml)
    │
    ├─> Load each YAML file
    │   ├─> Validate required fields
    │   ├─> Truncate short_desc
    │   └─> Set defaults
    │
    ├─> Generate embeddings
    │   └─> EmbeddingProvider.embed()
    │
    └─> Print preview (no database writes)
        ├─> 📝 Would upsert: linux.grep
        ├─>    name: Linux Grep
        ├─>    short_desc: ...
        ├─>    platform: ['linux']
        ├─>    tags: ['diagnostics', 'search']
        ├─>    meta: {...}
        └─>    embedding: [-0.1064, 0.1488, ... 128 dims]
```

### Sync Mode (Actual Write)

```
$ make tools.sync
    │
    ├─> docker compose exec -T postgres python3 tools/tools_upsert.py
    │
    ├─> Find YAML files (config/tools/**/*.yaml)
    │
    ├─> Load each YAML file
    │   ├─> Validate required fields
    │   ├─> Truncate short_desc
    │   └─> Set defaults
    │
    ├─> Connect to database
    │   └─> asyncpg.connect(DATABASE_URL)
    │
    ├─> For each tool:
    │   ├─> Generate embedding
    │   │   └─> EmbeddingProvider.embed()
    │   │
    │   ├─> Convert to vector literal
    │   │   └─> "[0.1,0.2,0.3,...]"
    │   │
    │   └─> Execute UPSERT
    │       ├─> INSERT ... ON CONFLICT (key) DO UPDATE
    │       └─> ✅ Upserted: linux.grep
    │
    └─> Summary
        └─> ✅ Upsert complete: 5/5 tools written
```

## Data Flow

```
┌─────────────┐
│ YAML File   │
│             │
│ key: X      │
│ name: Y     │
│ short_desc: │
│   Z         │
└──────┬──────┘
       │
       ▼
┌─────────────┐
│ Python Dict │
│             │
│ {           │
│   'key': X, │
│   'name': Y,│
│   'short_   │
│    desc': Z │
│ }           │
└──────┬──────┘
       │
       ▼
┌─────────────┐
│ Embedding   │
│ Generator   │
│             │
│ Input:      │
│ "X :: Z"    │
│             │
│ Output:     │
│ [128 floats]│
└──────┬──────┘
       │
       ▼
┌─────────────┐
│ Vector      │
│ Literal     │
│             │
│ "[0.1,0.2,  │
│   0.3,...]" │
└──────┬──────┘
       │
       ▼
┌─────────────┐
│ PostgreSQL  │
│ Database    │
│             │
│ tool table  │
│ ┌─────────┐ │
│ │ key: X  │ │
│ │ name: Y │ │
│ │ short_  │ │
│ │  desc: Z│ │
│ │ embed:  │ │
│ │  vector │ │
│ │  (128)  │ │
│ └─────────┘ │
└─────────────┘
```

## Idempotency Flow

```
First Run:
┌──────────┐     ┌──────────┐     ┌──────────┐
│ YAML     │────▶│ UPSERT   │────▶│ INSERT   │
│ (new)    │     │          │     │ new row  │
└──────────┘     └──────────┘     └──────────┘

Second Run (same YAML):
┌──────────┐     ┌──────────┐     ┌──────────┐
│ YAML     │────▶│ UPSERT   │────▶│ UPDATE   │
│ (same)   │     │          │     │ existing │
└──────────┘     └──────────┘     └──────────┘

Second Run (modified YAML):
┌──────────┐     ┌──────────┐     ┌──────────┐
│ YAML     │────▶│ UPSERT   │────▶│ UPDATE   │
│ (changed)│     │          │     │ with new │
│          │     │          │     │ values   │
└──────────┘     └──────────┘     └──────────┘

Key Behavior:
• ON CONFLICT (key) DO UPDATE
• No duplicates created
• usage_count preserved
• updated_at refreshed
```

## Error Handling Flow

```
┌─────────────────────────────────────────────────────────┐
│                    Error Scenarios                       │
└─────────────────────────────────────────────────────────┘

1. Missing Required Field
   YAML ──▶ Validate ──▶ ⚠️  Skip file, continue
                          Print warning

2. Invalid YAML Syntax
   YAML ──▶ Parse ──▶ ⚠️  Skip file, continue
                       Print parse error

3. Database Connection Failed
   Connect ──▶ ❌ Exit with code 1
                  Print error message

4. Database Query Error
   UPSERT ──▶ ⚠️  Skip tool, continue
                  Print error, try next tool

5. Embedding Generation Error
   Embed ──▶ 🔄 Use fallback
              Continue with deterministic embedding
```

## Integration Flow

```
┌─────────────────────────────────────────────────────────┐
│              Integration with Other Tasks                │
└─────────────────────────────────────────────────────────┘

Task 01: Database Schema
   ┌──────────────────────────────────────┐
   │ 001_tool_schema_pgvector.sql         │
   │                                      │
   │ CREATE TABLE tool (                  │
   │   key TEXT UNIQUE,                   │
   │   embedding VECTOR(128),             │
   │   ...                                │
   │ )                                    │
   └──────────────────────────────────────┘
                    │
                    ▼
Task 04: Tool Upsert (this task)
   ┌──────────────────────────────────────┐
   │ tools_upsert.py                      │
   │                                      │
   │ INSERT INTO tool (...)               │
   │ VALUES (...)                         │
   │ ON CONFLICT (key) DO UPDATE          │
   └──────────────────────────────────────┘
                    │
                    ▼
Task 02: Embedding Provider
   ┌──────────────────────────────────────┐
   │ selector/embeddings.py               │
   │                                      │
   │ EmbeddingProvider.embed()            │
   │ → [128 floats]                       │
   └──────────────────────────────────────┘
                    │
                    ▼
Task 03: DAO select_topk
   ┌──────────────────────────────────────┐
   │ selector/dao.py                      │
   │                                      │
   │ SELECT ... FROM tool                 │
   │ WHERE platform && $1                 │
   │ ORDER BY embedding <=> $2            │
   │ LIMIT $3                             │
   └──────────────────────────────────────┘
```

## Complete Workflow Example

```bash
# Step 1: Create database table
$ make selector.migrate
Running tool schema migration...
✅ Migration complete.

# Step 2: Create tool definition
$ cat > config/tools/linux/mytool.yaml <<EOF
key: linux.mytool
name: My Tool
short_desc: Does something useful.
platform: ["linux"]
tags: ["diagnostics"]
meta: {cmd: "mytool --help"}
EOF

# Step 3: Validate (dry-run)
$ make tools.seed
📂 Found 6 YAML file(s)
✅ Loaded 6 valid tool definition(s)

🔍 DRY RUN MODE:
============================================================
📄 config/tools/linux/mytool.yaml
  📝 Would upsert: linux.mytool
     name: My Tool
     short_desc: Does something useful.
     platform: ['linux']
     tags: ['diagnostics']
     meta: {'cmd': 'mytool --help'}
     embedding: [0.1234, -0.5678, ... 128 dims]
...
✅ Dry run complete: 6/6 tools validated

# Step 4: Sync to database
$ make tools.sync
📂 Found 6 YAML file(s)
✅ Loaded 6 valid tool definition(s)
🔌 Connected to database

💾 UPSERTING TOOLS:
============================================================
📄 config/tools/linux/mytool.yaml
  ✅ Upserted: linux.mytool
...
✅ Upsert complete: 6/6 tools written

# Step 5: Verify in database
$ docker compose exec -T postgres psql -U $POSTGRES_USER -d $POSTGRES_DB \
  -c "SELECT key, name FROM tool WHERE key = 'linux.mytool';"

      key       |   name   
----------------+----------
 linux.mytool   | My Tool
(1 row)

# Step 6: Use in semantic search
$ python3 -c "
import asyncio
import asyncpg
from selector.dao import select_topk

async def test():
    conn = await asyncpg.connect(dsn='...')
    results = await select_topk(
        conn,
        intent='diagnostic tools for linux',
        platform=['linux'],
        k=5
    )
    for tool in results:
        print(f'{tool[\"key\"]}: {tool[\"short_desc\"]}')
    await conn.close()

asyncio.run(test())
"

linux.mytool: Does something useful.
linux.grep: Search text in files on Linux...
linux.netstat: Display network connections...
...
```

## Summary

This workflow demonstrates:
- ✅ YAML-based tool definitions
- ✅ Validation before database writes
- ✅ Automatic embedding generation
- ✅ Idempotent upserts
- ✅ Container-safe execution
- ✅ Integration with semantic search
- ✅ Error handling at every step
- ✅ Complete observability (dry-run mode)