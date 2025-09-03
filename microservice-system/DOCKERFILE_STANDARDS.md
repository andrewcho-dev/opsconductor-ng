# Dockerfile Standards - MANDATORY COMPLIANCE

## Overview
ALL Python microservices MUST follow these exact standards. NO EXCEPTIONS.

## Standard Template
```dockerfile
FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    curl \
    [additional-deps-if-needed] \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create non-root user
RUN addgroup --gid 1001 --system python
RUN adduser --system --uid 1001 --gid 1001 python

# Change ownership of the app directory
RUN chown -R python:python /app
USER python

# Expose port
EXPOSE [SERVICE_PORT]

# Health check
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
  CMD curl -f http://localhost:[SERVICE_PORT]/health || exit 1

# Run the application
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "[SERVICE_PORT]"]
```

## Mandatory Requirements

### 1. Base Image
- **MUST**: Use `python:3.11-slim`
- **REASON**: Consistency, security, size optimization

### 2. System Dependencies
- **MUST**: Include `gcc` (for Python package compilation)
- **MUST**: Include `curl` (for health checks)
- **MAY**: Include additional dependencies if service-specific
- **MUST**: Clean apt cache with `rm -rf /var/lib/apt/lists/*`

### 3. Security - Non-Root User
- **MUST**: Create group with GID 1001: `addgroup --gid 1001 --system python`
- **MUST**: Create user with UID 1001: `adduser --system --uid 1001 --gid 1001 python`
- **MUST**: Change ownership: `chown -R python:python /app`
- **MUST**: Run as non-root: `USER python`
- **REASON**: Security best practices, container security

### 4. Health Checks
- **MUST**: Include HEALTHCHECK directive
- **MUST**: Use curl: `curl -f http://localhost:[PORT]/health`
- **MUST**: Use standard timing: `--interval=30s --timeout=3s --start-period=5s --retries=3`
- **REASON**: Container orchestration, monitoring, reliability

### 5. Application Startup
- **MUST**: Use uvicorn for FastAPI services
- **MUST**: Bind to all interfaces: `--host 0.0.0.0`
- **MUST**: Use correct port for service

## Service-Specific Variations

### Services Requiring Additional Dependencies
- **targets-service**: Requires `libkrb5-dev`, `libssl-dev`, `libffi-dev` for WinRM
- **executor-service**: Requires `libkrb5-dev`, `libssl-dev`, `libffi-dev` for WinRM
- **discovery-service**: Requires `nmap` for network discovery
- **All others**: Use base dependencies only

### Port Assignments
- auth-service: 3001
- user-service: 3002
- credentials-service: 3004
- targets-service: 3005
- jobs-service: 3006
- executor-service: 3007
- scheduler-service: 3008
- notification-service: 3009
- discovery-service: 3010

## Compliance Checking

### Automated Validation
Run compliance check before any deployment:
```bash
./scripts/dockerfile-compliance-check.sh
```

### Pre-Build Hook
Add to CI/CD pipeline:
```bash
# Fail build if not compliant
./scripts/dockerfile-compliance-check.sh || exit 1
```

## Enforcement Policy

### Zero Tolerance
- **NO** services deploy without compliance
- **NO** exceptions without architectural review
- **NO** custom implementations without approval

### Violation Response
1. **Immediate**: Fix violation
2. **Document**: Why standard was violated
3. **Review**: Architectural approval for any deviations
4. **Update**: Standards if legitimate need identified

## Creating New Services

### Process
1. **Copy** service-template directory
2. **Modify** only service-specific code
3. **Update** port number in Dockerfile
4. **Verify** compliance with checker script
5. **Deploy** only after compliance confirmed

### Never Start From Scratch
- **Always** use service-template as base
- **Never** create custom Dockerfile without template
- **Always** run compliance check before commit

## Maintenance

### Regular Audits
- **Weekly**: Automated compliance scans
- **Monthly**: Manual architecture review
- **Quarterly**: Standards review and updates

### Standards Updates
- **Process**: Architectural review required
- **Implementation**: Update template first, then all services
- **Validation**: Full compliance check after updates

---

**REMEMBER: These standards exist to prevent security vulnerabilities, ensure consistency, and reduce maintenance overhead. Compliance is not optional.**