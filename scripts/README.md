# Volume Mount Management Scripts

This directory contains scripts to manage and validate selective volume mounts.

## Scripts

### `check-volume-mounts.sh`
Validates that all volume mounts are selective and properly configured.

```bash
./scripts/check-volume-mounts.sh
```

**What it checks:**
- No dangerous full directory mounts (e.g., `./service:/app`)
- All Python files are properly mounted
- Frontend files are properly mounted

### `update-volume-mounts.sh`
Generates selective volume mount configuration for a service.

```bash
./scripts/update-volume-mounts.sh <service-name>
```

**Example:**
```bash
./scripts/update-volume-mounts.sh ai-service
```

### `pre-commit-hook.sh`
Pre-commit hook that validates volume mounts before allowing commits.

**To install:**
```bash
cp scripts/pre-commit-hook.sh .git/hooks/pre-commit
chmod +x .git/hooks/pre-commit
```

## Quick Setup

To set up all validation tools:

```bash
# Make scripts executable
chmod +x scripts/*.sh

# Install pre-commit hook
cp scripts/pre-commit-hook.sh .git/hooks/pre-commit
chmod +x .git/hooks/pre-commit

# Run initial validation
./scripts/check-volume-mounts.sh
```

## Adding New Files

When you add new Python files to a service:

1. **Generate new mounts:**
   ```bash
   ./scripts/update-volume-mounts.sh your-service
   ```

2. **Update docker-compose.yml** with the generated mounts

3. **Update `.zenrules/selective-volume-mounts.md`**

4. **Validate:**
   ```bash
   ./scripts/check-volume-mounts.sh
   ```

5. **Test the service:**
   ```bash
   docker compose up -d your-service
   ```

## Why This Matters

**Selective volume mounts preserve container environments while enabling development.**

❌ **Bad:** `./service:/app` (overwrites everything)
✅ **Good:** `./service/main.py:/app/main.py` (preserves environment)

See `.zenrules/selective-volume-mounts.md` for complete documentation.