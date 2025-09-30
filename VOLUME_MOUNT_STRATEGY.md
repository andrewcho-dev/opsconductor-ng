# OpsConductor Volume Mount Strategy - SIMPLIFIED AND FIXED

## **THE PROBLEM WE'RE SOLVING**

The current volume mount system is broken and causes constant confusion because:

1. **Missing Scripts** - GitHub workflows reference non-existent validation scripts
2. **No Development Mounts** - docker-compose.clean.yml has no volume mounts for live development
3. **Inconsistent Rules** - Documentation doesn't match actual implementation
4. **No Refresh Capability** - Code changes require full container rebuilds
5. **Complex and Confusing** - Too many rules and exceptions

## **THE NEW SIMPLE STRATEGY**

### **CORE PRINCIPLE: DEVELOPMENT vs PRODUCTION**

We will have **TWO CLEAR MODES**:

1. **DEVELOPMENT MODE** - Live file mounting for fast iteration
2. **PRODUCTION MODE** - No volume mounts, everything baked into containers

### **DEVELOPMENT MODE IMPLEMENTATION**

For development, we mount **ONLY THE ESSENTIAL FILES** that change frequently:

```yaml
# DEVELOPMENT VOLUME MOUNTS (docker-compose.dev.yml)
services:
  ai-brain:
    volumes:
      - ./ai-brain/main_clean.py:/app/main_clean.py
      - ./ai-brain/orchestration:/app/orchestration
      - ./shared:/app/shared

  automation-service:
    volumes:
      - ./automation-service/main_clean.py:/app/main_clean.py
      - ./automation-service/libraries:/app/libraries
      - ./shared:/app/shared

  asset-service:
    volumes:
      - ./asset-service/main.py:/app/main.py
      - ./asset-service/data:/app/data
      - ./shared:/app/shared

  # ... etc for other services
```

### **PRODUCTION MODE IMPLEMENTATION**

For production, we use **NO VOLUME MOUNTS** - everything is baked into containers:

```yaml
# PRODUCTION (docker-compose.clean.yml) - NO VOLUME MOUNTS
services:
  ai-brain:
    build:
      context: ./ai-brain
      dockerfile: Dockerfile.clean
    # NO VOLUMES - everything copied during build

  automation-service:
    build:
      context: ./automation-service
      dockerfile: Dockerfile.clean
    # NO VOLUMES - everything copied during build
```

## **IMPLEMENTATION PLAN**

### **Step 1: Create Development Compose File**
- Create `docker-compose.dev.yml` with selective volume mounts
- Keep `docker-compose.clean.yml` for production (no mounts)

### **Step 2: Create Simple Scripts**
- `scripts/dev-mode.sh` - Start in development mode with volume mounts
- `scripts/prod-mode.sh` - Start in production mode without volume mounts
- `scripts/validate-mounts.sh` - Simple validation script

### **Step 3: Update Documentation**
- Clear, simple rules
- No complex exceptions
- Easy to understand and follow

### **Step 4: Fix GitHub Workflows**
- Update to use actual existing scripts
- Simple validation that works

## **USAGE**

### **For Development (Live File Changes)**
```bash
./scripts/dev-mode.sh
# Files are mounted, changes reflect immediately
```

### **For Production Testing (Container-Only)**
```bash
./scripts/prod-mode.sh
# No mounts, everything baked in containers
```

### **For Validation**
```bash
./scripts/validate-mounts.sh
# Check that development mounts are correct
```

## **BENEFITS OF THIS APPROACH**

1. **SIMPLE** - Two clear modes, easy to understand
2. **CONSISTENT** - Same approach for all services
3. **WORKING** - Scripts and workflows that actually exist
4. **FAST DEVELOPMENT** - Live file changes without rebuilds
5. **PRODUCTION READY** - Clean containers without host dependencies
6. **NO CONFUSION** - Clear separation between dev and prod

## **RULES (SIMPLIFIED)**

### **Development Mode Rules**
1. Mount only files that change frequently during development
2. Always mount `./shared:/app/shared` for all services
3. Mount main application files and directories
4. Never mount entire service directories

### **Production Mode Rules**
1. No volume mounts except for data persistence (postgres_data, etc.)
2. Everything copied into containers during build
3. Containers are self-contained and portable

### **File Change Workflow**
1. **Development**: Change file → See changes immediately
2. **Production**: Change file → Rebuild container → Deploy

This is **MUCH SIMPLER** and **ACTUALLY WORKS**!