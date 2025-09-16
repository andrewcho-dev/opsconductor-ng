# LLM Service Build Success Documentation

## CRITICAL: Working Configuration That Took Hours to Figure Out

**Date**: September 16, 2025  
**Build Time**: ~3 minutes 10 seconds  
**Final Image Size**: 6.17GB  

## EXACT DOCKER BUILD COMMAND THAT WORKS
```bash
docker build --memory=16g --memory-swap=20g -t opsconductor-ng-llm-service /home/opsconductor/opsconductor-ng/llm-service/
```

**CRITICAL**: The memory limits are MANDATORY. Without them, the build fails with OOM errors.

## BASE IMAGE
```dockerfile
FROM python:3.12.11-slim
```

## SYSTEM DEPENDENCIES
```dockerfile
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    curl \
    && rm -rf /var/lib/apt/lists/*
```

## EXACT PYTHON PACKAGE VERSIONS THAT WORK

### Core ML/AI Packages (EXACT VERSIONS INSTALLED)
- **torch**: 2.5.1+cu121
- **torchvision**: 0.20.1+cu121
- **transformers**: 4.56.1
- **accelerate**: 1.10.1
- **numpy**: 1.26.4
- **pandas**: 2.3.2
- **scikit-learn**: 1.7.2
- **scipy**: 1.16.2

### Web Framework & API
- **fastapi**: 0.104.1
- **uvicorn**: 0.24.0
- **pydantic**: 2.11.9
- **pydantic_core**: 2.33.2
- **httpx**: 0.25.2
- **python-multipart**: 0.0.6

### Database & Cache
- **asyncpg**: 0.29.0
- **redis**: 5.0.1

### Utilities
- **structlog**: 23.2.0
- **requests**: 2.31.0
- **ollama**: 0.1.7
- **python-dotenv**: 1.0.0

## EXACT DOCKERFILE INSTALL SEQUENCE (CRITICAL ORDER)

```dockerfile
# 1. PyTorch with CUDA (MUST BE FIRST)
RUN pip install --no-cache-dir torch torchvision --index-url https://download.pytorch.org/whl/cu121

# 2. Core web framework
RUN pip install --no-cache-dir fastapi==0.104.1 uvicorn==0.24.0 pydantic>=2.8.0 httpx==0.25.2

# 3. Basic utilities
RUN pip install --no-cache-dir python-multipart==0.0.6
RUN pip install --no-cache-dir structlog==23.2.0 requests==2.31.0
RUN pip install --no-cache-dir ollama==0.1.7

# 4. NumPy with binary wheels (CRITICAL: --only-binary=all)
RUN pip install --no-cache-dir --only-binary=all "numpy>=1.19.0,<2.0"

# 5. Database/cache
RUN pip install --no-cache-dir asyncpg==0.29.0 redis==5.0.1 python-dotenv==1.0.0

# 6. ML packages with binary wheels (CRITICAL: --only-binary=all AND newer versions)
RUN pip install --no-cache-dir --only-binary=all pandas>=2.1.0
RUN pip install --no-cache-dir --only-binary=all scikit-learn>=1.3.0
RUN pip install --no-cache-dir --only-binary=all scipy>=1.11.0

# 7. Transformers last
RUN pip install --no-cache-dir transformers>=4.30.0
RUN pip install --no-cache-dir accelerate>=0.20.0
```

## CRITICAL SUCCESS FACTORS

### 1. Memory Limits (MANDATORY)
- **Docker Build Memory**: 16GB (`--memory=16g`)
- **Docker Build Swap**: 20GB (`--memory-swap=20g`)
- **Without these**: Build fails with OOM errors on pandas/scikit-learn

### 2. Package Version Requirements
- **pandas**: MUST be >=2.1.0 (2.0.3 has no Python 3.12 wheels)
- **scikit-learn**: MUST be >=1.3.0 for Python 3.12 compatibility
- **scipy**: MUST be >=1.11.0 for Python 3.12 compatibility
- **numpy**: MUST be <2.0 for compatibility with other packages

### 3. Binary Wheels (CRITICAL)
- **Flag**: `--only-binary=all` for numpy, pandas, scikit-learn, scipy
- **Purpose**: Prevents source compilation that causes OOM
- **Without this**: Build attempts compilation and fails

### 4. Installation Order
- **PyTorch first**: Establishes CUDA environment
- **ML packages after NumPy**: Ensures proper dependency resolution
- **Transformers last**: Depends on all other ML packages

## ENVIRONMENT SPECS
- **Host OS**: Ubuntu (Linux)
- **Docker Version**: Latest
- **Available RAM**: 47GB
- **Python Version**: 3.12.11
- **CUDA Version**: 12.1 (via PyTorch index)

## VERIFICATION COMMAND
```bash
docker run --rm opsconductor-ng-llm-service python -c "import pandas, sklearn, scipy, transformers; print('All packages imported successfully!')"
```

## TROUBLESHOOTING NOTES

### If Build Fails Again:
1. **Check memory limits**: Ensure `--memory=16g --memory-swap=20g`
2. **Verify package versions**: Use EXACT versions documented above
3. **Check binary wheels**: Ensure `--only-binary=all` for ML packages
4. **Python 3.12 compatibility**: Older package versions may not have wheels

### Common Failure Points:
- **pandas 2.0.3**: No Python 3.12 wheels, forces compilation
- **Missing memory limits**: OOM during pandas/scikit-learn installation
- **Wrong installation order**: Dependency conflicts
- **Missing --only-binary=all**: Attempts source compilation

## FINAL WORKING IMAGE
- **Name**: `opsconductor-ng-llm-service:latest`
- **Size**: 6.17GB
- **Build Time**: ~3 minutes
- **Status**: ✅ VERIFIED WORKING

**DO NOT CHANGE THESE VERSIONS OR BUILD PARAMETERS WITHOUT EXTENSIVE TESTING**