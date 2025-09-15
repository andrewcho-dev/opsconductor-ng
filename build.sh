#!/bin/bash

echo "🏗️  Building OpsConductor - New Optimized Architecture"
echo "=================================================="

# Set up directory structure
echo "📁 Setting up directory structure..."

# Copy shared modules to each service
services=("api-gateway" "identity-service" "asset-service" "automation-service" "communication-service")

for service in "${services[@]}"; do
    echo "  Setting up $service..."
    mkdir -p "$service"
    
    # Copy shared base service
    cp -r shared "$service/"
    
    # Create Dockerfile if not exists
    if [ ! -f "$service/Dockerfile" ]; then
        cat > "$service/Dockerfile" << EOF
FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \\
    curl \\
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Expose port (will be overridden by docker-compose)
EXPOSE 3000

# Run the application
CMD ["python", "main.py"]
EOF
    fi
    
    # Create requirements.txt if not exists
    if [ ! -f "$service/requirements.txt" ]; then
        cat > "$service/requirements.txt" << EOF
fastapi==0.104.1
uvicorn[standard]==0.24.0
asyncpg==0.29.0
redis==5.0.1
structlog==23.2.0
pydantic[email]==2.5.0
PyJWT==2.8.0
bcrypt==4.1.2
httpx==0.25.2
python-multipart==0.0.6
cryptography==41.0.7
aiohttp==3.9.1
celery==5.3.4
email-validator==2.3.0
EOF
    fi
done

echo "✅ Directory structure complete"

# Create placeholder services for now
echo "📝 Creating placeholder services..."

# Asset Service
if [ ! -f "asset-service/main.py" ]; then
    cat > "asset-service/main.py" << 'EOF'
#!/usr/bin/env python3
"""
OpsConductor Asset Service
Handles targets and credentials
Consolidates: credentials-service + targets-service
"""

import sys
sys.path.append('/app/shared')
from base_service import BaseService

class AssetService(BaseService):
    def __init__(self):
        super().__init__("asset-service", "1.0.0", 3002)
        self._setup_routes()
    
    def _setup_routes(self):
        @self.app.get("/targets")
        async def list_targets():
            return {"message": "Asset Service - Targets endpoint"}
        
        @self.app.get("/credentials")
        async def list_credentials():
            return {"message": "Asset Service - Credentials endpoint"}
        


if __name__ == "__main__":
    service = AssetService()
    service.run()
EOF
fi

# Automation Service
if [ ! -f "automation-service/main.py" ]; then
    cat > "automation-service/main.py" << 'EOF'
#!/usr/bin/env python3
"""
OpsConductor Automation Service
Handles jobs, workflows, and execution
Consolidates: jobs-service + executor-service + step-libraries-service
"""

import sys
sys.path.append('/app/shared')
from base_service import BaseService

class AutomationService(BaseService):
    def __init__(self):
        super().__init__("automation-service", "1.0.0", 3003)
        self._setup_routes()
    
    def _setup_routes(self):
        @self.app.get("/jobs")
        async def list_jobs():
            return {"message": "Automation Service - Jobs endpoint"}
        
        @self.app.get("/workflows")
        async def list_workflows():
            return {"message": "Automation Service - Workflows endpoint"}
        
        @self.app.get("/executions")
        async def list_executions():
            return {"message": "Automation Service - Executions endpoint"}
        
        @self.app.get("/libraries")
        async def list_libraries():
            return {"message": "Automation Service - Libraries endpoint"}

if __name__ == "__main__":
    service = AutomationService()
    service.run()
EOF
fi

# Communication Service
if [ ! -f "communication-service/main.py" ]; then
    cat > "communication-service/main.py" << 'EOF'
#!/usr/bin/env python3
"""
OpsConductor Communication Service
Handles notifications and external integrations
Consolidates: notification-service
"""

import sys
sys.path.append('/app/shared')
from base_service import BaseService

class CommunicationService(BaseService):
    def __init__(self):
        super().__init__("communication-service", "1.0.0", 3004)
        self._setup_routes()
    
    def _setup_routes(self):
        @self.app.get("/notifications")
        async def list_notifications():
            return {"message": "Communication Service - Notifications endpoint"}
        
        @self.app.get("/templates")
        async def list_templates():
            return {"message": "Communication Service - Templates endpoint"}
        
        @self.app.get("/channels")
        async def list_channels():
            return {"message": "Communication Service - Channels endpoint"}
        
        @self.app.get("/audit")
        async def list_audit():
            return {"message": "Communication Service - Audit endpoint"}

if __name__ == "__main__":
    service = CommunicationService()
    service.run()
EOF
fi

echo "✅ Placeholder services created"

# Create frontend placeholder
echo "📱 Setting up frontend..."
mkdir -p frontend
if [ ! -f "frontend/Dockerfile" ]; then
    cat > "frontend/Dockerfile" << 'EOF'
FROM node:18-alpine

WORKDIR /app

# Copy package files
COPY package*.json ./

# Install dependencies
RUN npm install

# Copy source code
COPY . .

# Build the app
RUN npm run build

# Expose port
EXPOSE 3000

# Start the app
CMD ["npm", "start"]
EOF
fi

if [ ! -f "frontend/package.json" ]; then
    cat > "frontend/package.json" << 'EOF'
{
  "name": "opsconductor-frontend",
  "version": "1.0.0",
  "private": true,
  "dependencies": {
    "react": "^18.2.0",
    "react-dom": "^18.2.0",
    "react-scripts": "5.0.1"
  },
  "scripts": {
    "start": "react-scripts start",
    "build": "react-scripts build",
    "test": "react-scripts test",
    "eject": "react-scripts eject"
  },
  "eslintConfig": {
    "extends": [
      "react-app",
      "react-app/jest"
    ]
  },
  "browserslist": {
    "production": [
      ">0.2%",
      "not dead",
      "not op_mini all"
    ],
    "development": [
      "last 1 chrome version",
      "last 1 firefox version",
      "last 1 safari version"
    ]
  }
}
EOF
fi

# Create simple React app
mkdir -p frontend/src frontend/public
if [ ! -f "frontend/src/App.js" ]; then
    cat > "frontend/src/App.js" << 'EOF'
import React from 'react';

function App() {
  return (
    <div style={{ padding: '20px', fontFamily: 'Arial, sans-serif' }}>
      <h1>🚀 OpsConductor - New Architecture</h1>
      <p>Welcome to the rebuilt OpsConductor system!</p>
      <div style={{ marginTop: '20px' }}>
        <h3>Services Status:</h3>
        <ul>
          <li>✅ API Gateway (Port 3000)</li>
          <li>✅ Identity Service (Port 3001)</li>
          <li>✅ Asset Service (Port 3002)</li>
          <li>✅ Automation Service (Port 3003)</li>
          <li>✅ Communication Service (Port 3004)</li>
        </ul>
      </div>
    </div>
  );
}

export default App;
EOF
fi

if [ ! -f "frontend/src/index.js" ]; then
    cat > "frontend/src/index.js" << 'EOF'
import React from 'react';
import ReactDOM from 'react-dom/client';
import App from './App';

const root = ReactDOM.createRoot(document.getElementById('root'));
root.render(<App />);
EOF
fi

if [ ! -f "frontend/public/index.html" ]; then
    cat > "frontend/public/index.html" << 'EOF'
<!DOCTYPE html>
<html lang="en">
  <head>
    <meta charset="utf-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1" />
    <title>OpsConductor</title>
  </head>
  <body>
    <div id="root"></div>
  </body>
</html>
EOF
fi

echo "✅ Frontend setup complete"

# Initialize database schema
echo "🗄️  Initializing database schema..."
if [ -f "./database/init-db.sh" ]; then
    chmod +x ./database/init-db.sh
    echo "✅ Database initialization script ready"
else
    echo "⚠️  Database initialization script not found"
fi

# Create deployment script
cat > "deploy.sh" << 'EOF'
#!/bin/bash

echo "🚀 Deploying OpsConductor - New Architecture"
echo "============================================"

# Stop any existing containers
echo "🛑 Stopping existing containers..."
docker compose down --remove-orphans

# Build and start services
echo "🏗️  Building and starting services..."
docker compose up --build -d

# Initialize database
echo "🗄️  Initializing database..."
if [ -f "./database/init-db.sh" ]; then
    ./database/init-db.sh
else
    echo "⚠️  Database initialization script not found, using docker-entrypoint-initdb.d"
fi

# Wait for services to be healthy
echo "⏳ Waiting for services to be healthy..."
sleep 30

# Check service health
echo "🔍 Checking service health..."
services=("postgres" "redis" "api-gateway" "identity-service" "asset-service" "automation-service" "communication-service")

for service in "${services[@]}"; do
    if docker compose ps "$service" | grep -q "healthy\|Up"; then
        echo "  ✅ $service is running"
    else
        echo "  ❌ $service is not healthy"
    fi
done

echo ""
echo "🎉 Deployment complete!"
echo ""
echo "📊 Service URLs:"
echo "  API Gateway:        http://localhost:3000"
echo "  Identity Service:   http://localhost:3001"
echo "  Asset Service:      http://localhost:3002"
echo "  Automation Service: http://localhost:3003"
echo "  Communication:      http://localhost:3004"
echo "  Frontend:           http://localhost:3100"
echo "  Flower (Celery):    http://localhost:5555"
echo ""
echo "🔍 Health Checks:"
echo "  curl http://localhost:3000/health"
echo "  curl http://localhost:3001/health"
echo ""
echo "📝 View logs:"
echo "  docker compose logs -f [service-name]"
EOF

chmod +x deploy.sh

echo ""
echo "🎉 Build complete!"
echo ""
echo "📋 Next steps:"
echo "  1. Review the architecture: cat ARCHITECTURE_DESIGN.md"
echo "  2. Deploy the system: ./deploy.sh"
echo "  3. Test the services: curl http://localhost:3000/health"
echo ""
echo "🔧 Development:"
echo "  - Edit service code in respective directories"
echo "  - Restart specific service: docker compose restart [service-name]"
echo "  - View logs: docker compose logs -f [service-name]"
echo ""