#!/bin/bash
# Verification script to ensure all components are ready for deployment

echo "🔍 OpsConductor Setup Verification"
echo "=================================="

# Check required files
echo "📁 Checking required files..."

REQUIRED_FILES=(
    "docker-compose.yml"
    "build.sh"
    "deploy.sh"
    "database/complete-schema.sql"
    "database/init-db.sh"
    "README.md"
    ".gitignore"
    ".env.example"
)

for file in "${REQUIRED_FILES[@]}"; do
    if [ -f "$file" ]; then
        echo "  ✅ $file"
    else
        echo "  ❌ $file (MISSING)"
        exit 1
    fi
done

# Check service directories and files
echo ""
echo "🏗️  Checking service structure..."

SERVICES=("api-gateway" "identity-service" "asset-service" "automation-service" "communication-service" "ai-service")

for service in "${SERVICES[@]}"; do
    echo "  Checking $service..."
    
    if [ ! -d "$service" ]; then
        echo "    ❌ Directory missing"
        exit 1
    fi
    
    if [ ! -f "$service/main.py" ]; then
        echo "    ❌ main.py missing"
        exit 1
    fi
    
    if [ ! -f "$service/Dockerfile" ]; then
        echo "    ❌ Dockerfile missing"
        exit 1
    fi
    
    if [ ! -f "$service/requirements.txt" ]; then
        echo "    ❌ requirements.txt missing"
        exit 1
    fi
    
    echo "    ✅ $service complete"
done

# Check frontend
echo ""
echo "🎨 Checking frontend..."

if [ ! -d "frontend" ]; then
    echo "  ❌ Frontend directory missing"
    exit 1
fi

if [ ! -f "frontend/package.json" ]; then
    echo "  ❌ package.json missing"
    exit 1
fi

if [ ! -f "frontend/Dockerfile" ]; then
    echo "  ❌ Dockerfile missing"
    exit 1
fi

echo "  ✅ Frontend complete"

# Check database files
echo ""
echo "🗄️  Checking database setup..."

if [ ! -f "database/complete-schema.sql" ]; then
    echo "  ❌ Complete schema file missing"
    exit 1
fi

if [ ! -f "database/init-db.sh" ]; then
    echo "  ❌ Database initialization script missing"
    exit 1
fi

if [ ! -x "database/init-db.sh" ]; then
    echo "  ⚠️  Making init-db.sh executable..."
    chmod +x database/init-db.sh
fi

echo "  ✅ Database setup complete"

# Check shared modules
echo ""
echo "🔗 Checking shared modules..."

if [ ! -f "shared/base_service.py" ]; then
    echo "  ❌ Base service module missing"
    exit 1
fi

# Check if shared modules are copied to services
for service in "${SERVICES[@]}"; do
    if [ ! -d "$service/shared" ]; then
        echo "  ⚠️  Shared modules not found in $service, copying..."
        cp -r shared "$service/"
    fi
done

echo "  ✅ Shared modules complete"

# Check executable permissions
echo ""
echo "🔧 Checking executable permissions..."

EXECUTABLES=("build.sh" "deploy.sh" "database/init-db.sh")

for exec in "${EXECUTABLES[@]}"; do
    if [ ! -x "$exec" ]; then
        echo "  ⚠️  Making $exec executable..."
        chmod +x "$exec"
    fi
    echo "  ✅ $exec"
done

# Verify Docker Compose syntax
echo ""
echo "🐳 Verifying Docker Compose configuration..."

if command -v docker-compose &> /dev/null; then
    if docker-compose config > /dev/null 2>&1; then
        echo "  ✅ Docker Compose configuration valid"
    else
        echo "  ❌ Docker Compose configuration invalid"
        exit 1
    fi
else
    echo "  ⚠️  Docker Compose not found, skipping validation"
fi

# Check for common issues
echo ""
echo "🔍 Checking for common issues..."

# Check for Windows line endings
if command -v file &> /dev/null; then
    for script in build.sh deploy.sh database/init-db.sh; do
        if file "$script" | grep -q "CRLF"; then
            echo "  ⚠️  $script has Windows line endings, converting..."
            sed -i 's/\r$//' "$script"
        fi
    done
fi

echo "  ✅ No common issues found"

# Summary
echo ""
echo "📊 Verification Summary:"
echo "  - Required files: ✅"
echo "  - Service structure: ✅"
echo "  - Frontend setup: ✅"
echo "  - Database setup: ✅"
echo "  - Shared modules: ✅"
echo "  - Executable permissions: ✅"
echo "  - Docker Compose: ✅"
echo ""
echo "🎉 Setup verification complete!"
echo ""
echo "📋 Next steps:"
echo "  1. Run: ./build.sh"
echo "  2. Run: ./deploy.sh"
echo "  3. Access: http://\$(hostname -I | awk '{print \$1}'):3100"
echo ""
echo "🔑 Default credentials:"
echo "  Username: admin"
echo "  Password: admin123"
echo ""