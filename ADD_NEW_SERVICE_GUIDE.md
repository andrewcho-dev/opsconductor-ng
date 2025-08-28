# 🚀 Adding New Services Guide

## 📋 Quick Start Checklist

Follow this step-by-step guide to add a new service to the OpsConductor microservice system.

### ✅ Prerequisites
- [ ] Docker and Docker Compose installed
- [ ] Basic understanding of Python and FastAPI
- [ ] PostgreSQL knowledge (if database needed)
- [ ] Understanding of JWT authentication

---

## 🛠️ Step-by-Step Implementation

### Step 1: Copy Service Template
```bash
# Navigate to the microservice system directory
cd /path/to/microservice-system

# Copy the service template
cp -r service-template your-new-service

# Navigate to your new service
cd your-new-service
```

### Step 2: Customize Service Files

#### 2.1 Update Service Configuration
- Rename files and update references
- Choose an available port number (next in sequence: 3010, 3011, etc.)
- Update service name throughout files

#### 2.2 Create `main.py` (FastAPI Service)
```python
from fastapi import FastAPI, HTTPException, Depends
from fastapi.security import HTTPBearer
import psycopg2
from psycopg2.extras import RealDictCursor
import os
from typing import List, Optional

app = FastAPI(title="Your New Service", version="1.0.0")
security = HTTPBearer()

# Database connection
def get_db_connection():
    return psycopg2.connect(
        host=os.getenv('DB_HOST', 'postgres'),
        port=os.getenv('DB_PORT', '5432'),
        database=os.getenv('DB_NAME', 'opsconductor'),
        user=os.getenv('DB_USER', 'opsconductor'),
        password=os.getenv('DB_PASSWORD', 'opsconductor123')
    )

@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": "your-new-service"}

@app.get("/your-endpoint")
async def your_endpoint():
    # Your business logic here
    return {"message": "Your new service is working!"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=3010)
```

#### 2.3 Create `requirements.txt`
```txt
fastapi==0.104.1
uvicorn==0.24.0
psycopg2-binary==2.9.9
python-jose[cryptography]==3.3.0
python-dotenv==1.0.0
```

#### 2.4 Update `Dockerfile`
```dockerfile
FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Expose port
EXPOSE 3010

# Run the application
CMD ["python", "main.py"]
```

### Step 3: Database Schema (if needed)

#### 3.1 Create Database Migration
Create a new SQL file in `database/` directory:
```sql
-- database/add-your-service-schema.sql
CREATE TABLE IF NOT EXISTS your_table (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    description TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Add indexes
CREATE INDEX IF NOT EXISTS idx_your_table_name ON your_table(name);
```

#### 3.2 Apply Migration
```bash
# Apply the migration
docker exec opsconductor-postgres psql -U opsconductor -d opsconductor -f /docker-entrypoint-initdb.d/add-your-service-schema.sql
```

### Step 4: Update Docker Compose

#### 4.1 Add Service to `docker-compose-python.yml`
```yaml
  your-new-service:
    build: ./your-new-service
    container_name: opsconductor-your-new-service
    ports:
      - "3010:3010"
    environment:
      - DB_HOST=postgres
      - DB_PORT=5432
      - DB_NAME=opsconductor
      - DB_USER=opsconductor
      - DB_PASSWORD=opsconductor123
      - JWT_SECRET_KEY=${JWT_SECRET_KEY}
    depends_on:
      - postgres
    networks:
      - opsconductor-net
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:3010/health"]
      interval: 30s
      timeout: 10s
      retries: 3
```

### Step 5: Update Nginx Configuration

#### 5.1 Add Route to `nginx/nginx.conf`
```nginx
# Add to the server block
location /api/v1/your-service/ {
    proxy_pass http://your-new-service:3010/;
    proxy_set_header Host $host;
    proxy_set_header X-Real-IP $remote_addr;
    proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    proxy_set_header X-Forwarded-Proto $scheme;
}
```

### Step 6: Frontend Integration (if needed)

#### 6.1 Add API Service
Create `frontend/src/services/yourNewService.ts`:
```typescript
import axios from 'axios';
import { getAuthToken } from './auth';

const API_BASE_URL = process.env.REACT_APP_API_URL || 'https://localhost:8443';

export const yourNewService = {
  async getItems() {
    const token = getAuthToken();
    const response = await axios.get(`${API_BASE_URL}/api/v1/your-service/items`, {
      headers: { Authorization: `Bearer ${token}` }
    });
    return response.data;
  },

  async createItem(data: any) {
    const token = getAuthToken();
    const response = await axios.post(`${API_BASE_URL}/api/v1/your-service/items`, data, {
      headers: { Authorization: `Bearer ${token}` }
    });
    return response.data;
  }
};
```

#### 6.2 Add React Component
Create `frontend/src/components/YourNewComponent.tsx`:
```typescript
import React, { useState, useEffect } from 'react';
import { yourNewService } from '../services/yourNewService';

const YourNewComponent: React.FC = () => {
  const [items, setItems] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadItems();
  }, []);

  const loadItems = async () => {
    try {
      const data = await yourNewService.getItems();
      setItems(data);
    } catch (error) {
      console.error('Error loading items:', error);
    } finally {
      setLoading(false);
    }
  };

  if (loading) return <div>Loading...</div>;

  return (
    <div>
      <h2>Your New Service</h2>
      {/* Your component UI here */}
    </div>
  );
};

export default YourNewComponent;
```

### Step 7: Testing

#### 7.1 Create Test Script
Create `test-your-service.sh`:
```bash
#!/bin/bash

echo "🧪 Testing Your New Service"
echo "=========================="

# Test service health
echo "1. Testing service health..."
HEALTH_RESPONSE=$(curl -s http://localhost:3010/health)
if [[ "$HEALTH_RESPONSE" == *"healthy"* ]]; then
    echo "✅ Service is healthy"
else
    echo "❌ Service health check failed"
    exit 1
fi

# Test your endpoints
echo "2. Testing your endpoints..."
# Add your specific tests here

echo "✅ All tests passed!"
```

#### 7.2 Make Script Executable
```bash
chmod +x test-your-service.sh
```

### Step 8: Deployment

#### 8.1 Build and Start Service
```bash
# Build the new service
docker-compose -f docker-compose-python.yml build your-new-service

# Start the service
docker-compose -f docker-compose-python.yml up -d your-new-service

# Check logs
docker-compose -f docker-compose-python.yml logs -f your-new-service
```

#### 8.2 Verify Deployment
```bash
# Test the service
./test-your-service.sh

# Check system status
./system-status.sh
```

---

## 📋 Service Development Best Practices

### 1. API Design
- Follow RESTful conventions
- Use consistent error responses
- Implement proper HTTP status codes
- Add OpenAPI/Swagger documentation

### 2. Security
- Validate JWT tokens for protected endpoints
- Sanitize all input data
- Use parameterized queries for database operations
- Implement proper error handling

### 3. Database
- Use connection pooling
- Implement proper indexing
- Handle database errors gracefully
- Use transactions for multi-step operations

### 4. Monitoring
- Implement health check endpoints
- Add structured logging
- Include metrics collection
- Handle graceful shutdown

### 5. Testing
- Write unit tests for business logic
- Create integration tests for API endpoints
- Test error scenarios
- Validate database operations

---

## 🔧 Common Patterns

### Authentication Middleware
```python
from fastapi import HTTPException, Depends
from fastapi.security import HTTPBearer
import jwt
import os

security = HTTPBearer()

async def verify_token(token: str = Depends(security)):
    try:
        payload = jwt.decode(token.credentials, os.getenv('JWT_SECRET_KEY'), algorithms=['HS256'])
        return payload
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid token")
```

### Database Connection Pool
```python
from psycopg2 import pool
import os

# Create connection pool
db_pool = psycopg2.pool.SimpleConnectionPool(
    1, 20,  # min and max connections
    host=os.getenv('DB_HOST'),
    port=os.getenv('DB_PORT'),
    database=os.getenv('DB_NAME'),
    user=os.getenv('DB_USER'),
    password=os.getenv('DB_PASSWORD')
)

def get_db_connection():
    return db_pool.getconn()

def return_db_connection(conn):
    db_pool.putconn(conn)
```

### Error Handling
```python
from fastapi import HTTPException
import logging

logger = logging.getLogger(__name__)

@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    logger.error(f"Global exception: {exc}")
    return HTTPException(status_code=500, detail="Internal server error")
```

---

## 📚 Additional Resources

- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [PostgreSQL Documentation](https://www.postgresql.org/docs/)
- [Docker Compose Documentation](https://docs.docker.com/compose/)
- [JWT Authentication](https://jwt.io/)

---

**Happy coding!** 🚀 Your new service should now be fully integrated into the OpsConductor system.