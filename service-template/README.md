# New Service Template

This is a template for creating new Python FastAPI microservices in the OpsConductor system.

## Quick Start

1. Copy this template directory:
   ```bash
   cp -r service-template your-new-service
   cd your-new-service
   ```

2. Update the service name in:
   - `main.py` - Change service name, description, and table names
   - `Dockerfile` - Update port if needed
   - `README.md` - Update this file
   - Database schema (if needed)

3. Choose an available port number (3010, 3011, 3012, etc.)

4. Add your business logic to `main.py`

5. Update `docker-compose-python.yml` to include your new service

6. Test your service:
   ```bash
   pip install -r requirements.txt
   python main.py
   ```

## Service Structure

```
your-new-service/
├── main.py           # Main FastAPI application
├── requirements.txt  # Python dependencies
├── Dockerfile        # Container configuration
├── test-service.sh   # Test script
└── README.md         # This file
```

## API Endpoints

- `GET /health` - Health check (no auth required)
- `GET /items` - Get all items (auth required)
- `POST /items` - Create new item (auth required)
- `GET /items/{id}` - Get item by ID (auth required)
- `PUT /items/{id}` - Update item (auth required)
- `DELETE /items/{id}` - Delete item (auth required)

## Environment Variables

- `PORT` - Service port (default: 3010)
- `DB_HOST` - Database host (default: postgres)
- `DB_PORT` - Database port (default: 5432)
- `DB_NAME` - Database name (default: opsconductor)
- `DB_USER` - Database user (default: opsconductor)
- `DB_PASSWORD` - Database password (default: opsconductor123)
- `JWT_SECRET_KEY` - JWT secret key for authentication

## Database Schema

Add your table schema to the main database schema file:
```sql
-- Example table for this template
CREATE TABLE IF NOT EXISTS items (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    description TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_items_name ON items(name);
```

## Authentication

This service uses JWT token authentication. All endpoints except `/health` require a valid JWT token in the Authorization header:
```
Authorization: Bearer <your-jwt-token>
```

## Testing

Run the test script:
```bash
./test-service.sh
```

## Docker

Build and run with Docker:
```bash
docker build -t your-new-service .
docker run -p 3010:3010 -e JWT_SECRET_KEY=your-secret your-new-service
```

## Integration with OpsConductor

1. Add service to `docker-compose-python.yml`
2. Add nginx routing in `nginx/nginx.conf`
3. Update frontend to call your service APIs
4. Add database migrations if needed
5. Update system documentation

## Features

- FastAPI with automatic OpenAPI/Swagger documentation
- JWT authentication integration
- PostgreSQL database integration with connection pooling
- Health check endpoint
- Structured logging
- Pydantic models for request/response validation
- Docker containerization
- Non-root user security

## Development

### Prerequisites
- Python 3.11+
- PostgreSQL 16+
- Docker & Docker Compose

### Local Development
```bash
# Install dependencies
pip install -r requirements.txt

# Start in development mode
python main.py

# Access API documentation
# http://localhost:3010/docs (Swagger UI)
# http://localhost:3010/redoc (ReDoc)
```

### Docker Development
```bash
# Build and start with docker-compose
docker-compose -f docker-compose-python.yml up --build -d

# View logs
docker-compose -f docker-compose-python.yml logs -f your-new-service

# Stop services
docker-compose -f docker-compose-python.yml down
```

## Security

- JWT token validation for protected endpoints
- Input validation with Pydantic models
- SQL injection prevention with parameterized queries
- Non-root Docker user
- Environment variable configuration
- HTTPS support through nginx proxy

## Contributing

1. Follow the existing code structure and patterns
2. Add tests for new functionality
3. Update documentation
4. Ensure health checks pass
5. Test integration with other services
6. Follow Python PEP 8 style guidelines