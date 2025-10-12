# Tool Catalog - Quick Reference

## Quick Start

```bash
# Validate tool definitions
make tools.seed

# Sync to database
make tools.sync
```

## Command Line Usage

```bash
# Dry-run (validate only)
python3 tools/tools_upsert.py --dry-run

# Sync to database
python3 tools/tools_upsert.py

# Custom glob pattern
python3 tools/tools_upsert.py --glob "config/tools/linux/*.yaml"

# Custom database
python3 tools/tools_upsert.py --dsn "postgresql://user:pass@host/db"
```

## YAML Template

```yaml
key: platform.toolname          # Required: Unique identifier
name: Tool Display Name         # Required: Human-readable name
short_desc: Brief description.  # Required: Max 160 chars (auto-truncated)
platform:                       # Optional: List of platforms
  - linux
  - docker
tags:                           # Optional: List of tags
  - diagnostics
  - network
meta:                           # Optional: Arbitrary metadata
  cmd: "command {{arg}}"
  requires_root: true
```

## Directory Structure

```
config/tools/
├── linux/          # Linux-specific tools
├── windows/        # Windows-specific tools
├── docker/         # Docker-specific tools
└── ...             # Other platforms
```

## Make Targets

| Target | Description |
|--------|-------------|
| `make tools.seed` | Validate tool definitions (dry-run) |
| `make tools.sync` | Sync tools to database |
| `make selector.migrate` | Create tool table (run first) |

## Workflow

```bash
# 1. Create tool table
make selector.migrate

# 2. Add/edit YAML files in config/tools/
vim config/tools/linux/mytool.yaml

# 3. Validate
make tools.seed

# 4. Sync
make tools.sync

# 5. Verify
docker compose exec -T postgres psql -U $POSTGRES_USER -d $POSTGRES_DB \
  -c "SELECT key, name FROM tool;"
```

## Common Tasks

### Add a new tool

```bash
cat > config/tools/linux/mytool.yaml <<EOF
key: linux.mytool
name: My Tool
short_desc: Does something useful.
platform: ["linux"]
tags: ["diagnostics"]
meta: {cmd: "mytool --help"}
EOF

make tools.sync
```

### Update an existing tool

```bash
vim config/tools/linux/grep.yaml
make tools.sync  # Idempotent - safe to run multiple times
```

### List all tools

```bash
find config/tools -name "*.yaml" | sort
```

### Validate YAML syntax

```bash
python3 -c "import yaml; yaml.safe_load(open('config/tools/linux/grep.yaml'))"
```

## Troubleshooting

### No YAML files found
```bash
ls -la config/tools/**/*.yaml
```

### Database connection failed
```bash
echo $DATABASE_URL
docker compose ps postgres
```

### YAML parse error
```bash
yamllint config/tools/linux/grep.yaml
```

## Integration

After syncing, tools are available for semantic search:

```python
from selector.dao import select_topk

results = await select_topk(
    conn,
    intent="search for text in files",
    platform=["linux"],
    k=5
)
# Returns: [{'key': 'linux.grep', ...}, ...]
```

## Performance

- ~16ms per tool (YAML + embedding + upsert)
- 100 tools: ~1.6 seconds
- Fully idempotent (safe to run repeatedly)

## Exit Codes

- `0` - Success
- `1` - Failure (partial or complete)

## Environment Variables

- `DATABASE_URL` - Database connection string
- `EMBED_MODEL` - Optional sentence-transformers model

## See Also

- `tools/README.md` - Full documentation
- `tools/TASK_04_SUMMARY.md` - Implementation details
- `selector/dao.py` - Tool selection DAO
- `selector/embeddings.py` - Embedding provider