# 🛡️ VOLUME MOUNT PROTECTION SYSTEM

## NEVER DEAL WITH VOLUME MOUNT ISSUES AGAIN!

This system **AUTOMATICALLY** prevents and fixes volume mount issues that cause:
- Python version mismatches
- Missing dependencies  
- Broken container environments
- Hours of debugging time

## 🚀 QUICK START

```bash
# Set up the protection system
make setup-dev

# Validate current setup
make validate-volumes

# When adding new files to a service
make update-volumes SVC=ai-service
```

## 🔧 WHAT'S INCLUDED

### 1. ZenRule Documentation
- **`.zenrules/selective-volume-mounts.md`** - Complete rule documentation
- **Current configurations for all services**
- **Examples and troubleshooting**

### 2. Automated Validation Scripts
- **`scripts/check-volume-mounts.sh`** - Validates all mounts are selective
- **`scripts/update-volume-mounts.sh`** - Generates mounts for new files
- **`scripts/pre-commit-hook.sh`** - Blocks dangerous commits

### 3. CI/CD Protection
- **`.github/workflows/validate-volume-mounts.yml`** - GitHub Actions validation
- **Automatic PR comments** when dangerous mounts are detected
- **Blocks merges** with full directory mounts

### 4. Developer Tools
- **`Makefile`** - Easy commands for all operations
- **Pre-commit hooks** - Catch issues before commit
- **Emergency fix commands** - Quick recovery tools

## 🎯 THE RULE

### ❌ NEVER DO THIS:
```yaml
volumes:
  - ./service:/app  # DESTROYS CONTAINER ENVIRONMENT
```

### ✅ ALWAYS DO THIS:
```yaml
volumes:
  - ./service/main.py:/app/main.py
  - ./service/other.py:/app/other.py
  - ./shared:/app/shared
```

## 🔄 WORKFLOW FOR ADDING NEW FILES

1. **Add your new Python file** to the service directory
2. **Generate new mounts**: `make update-volumes SVC=your-service`
3. **Copy output** to docker-compose.yml
4. **Update ZenRule**: Add to `.zenrules/selective-volume-mounts.md`
5. **Validate**: `make validate-volumes`
6. **Test**: `make restart-service SVC=your-service`

## 🚨 EMERGENCY COMMANDS

If you're stuck with broken mounts:

```bash
# Fix all services at once
make fix-all-mounts

# Check what's wrong
make validate-volumes

# Show the complete rule
make show-zenrule

# Get system status
make status
```

## 🛡️ PROTECTION LAYERS

1. **Pre-commit hooks** - Stop bad commits
2. **GitHub Actions** - Block bad PRs
3. **Makefile validation** - Check before Docker operations
4. **Automated scripts** - Generate correct configurations
5. **Documentation** - Always up-to-date examples

## 📊 CURRENT SERVICE CONFIGURATIONS

All services are configured with selective volume mounts:

- ✅ **kong** - kong.yml configuration
- ✅ **keycloak** - realm configuration + init scripts
- ✅ **identity-service** - main.py + keycloak_adapter.py + shared  
- ✅ **asset-service** - main.py + main_with_groups.py + data + shared
- ✅ **automation-service** - All Python files + libraries + shared
- ✅ **communication-service** - main.py + shared
- ✅ **ai-service** - All Python files + shared + ollama_models
- ✅ **frontend** - src + public + config files

## 🎉 BENEFITS

- **No more Python version mismatches**
- **No more missing dependencies**
- **Fast development** (files still sync)
- **Stable environments** (containers preserved)
- **Automatic validation** (catch issues early)
- **Zero manual work** (scripts do everything)

## 🔍 VALIDATION COMMANDS

```bash
# Check everything is correct
make validate-volumes

# Install protection hooks
make install-hooks

# Generate mounts for new service
make update-volumes SVC=new-service

# Emergency fix everything
make fix-all-mounts
```

## 📖 DOCUMENTATION LOCATIONS

- **Main rule**: `.zenrules/selective-volume-mounts.md`
- **Scripts**: `scripts/README.md`
- **This overview**: `VOLUME_MOUNT_SYSTEM.md`
- **Makefile help**: `make help`

---

## 🎯 REMEMBER

**This system is BULLETPROOF. Follow the workflow and you'll NEVER have volume mount issues again!**

**Selective volume mounts = Fast development + Stable environments**
**Full directory mounts = Broken environments + Wasted time**