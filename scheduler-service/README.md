# New Service

## Overview
This is a new microservice in the microservice system. Replace this description with details about your service's purpose and functionality.

## Features
- RESTful API endpoints
- JWT authentication integration
- PostgreSQL database integration
- Health check endpoint
- Structured logging
- Graceful shutdown handling
- Docker containerization

## API Endpoints

### Public Endpoints
- `GET /health` - Health check
- `GET /info` - Service information

### Protected Endpoints (require JWT token)
- `GET /data` - Get paginated data
- `POST /data` - Create new data
- `GET /user-info/:userId` - Get user information via service call

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| PORT | 3003 | Service port |
| DB_HOST | new-service-db | Database host |
| DB_PORT | 5432 | Database port |
| DB_NAME | newservicedb | Database name |
| DB_USER | newservice | Database user |
| DB_PASS | newservicepass123 | Database password |
| AUTH_SERVICE_URL | http://auth-service:3002 | Auth service URL |
| USER_SERVICE_URL | http://user-service:3001 | User service URL |

## Database Schema

### Tables
- `new_service_data` - Main data table
- `service_config` - Configuration settings
- `audit_log` - Audit trail

See `init.sql` for complete schema definition.

## Development

### Prerequisites
- Node.js 18+
- PostgreSQL 15+
- Docker & Docker Compose

### Local Development
```bash
# Install dependencies
npm install

# Start in development mode
npm run dev

# Run tests
npm test
```

### Docker Development
```bash
# Build and start with docker-compose
docker-compose up --build -d

# View logs
docker-compose logs -f new-service

# Stop services
docker-compose down
```

## Testing

### Manual Testing
```bash
# Health check
curl http://localhost:3003/health

# Service info
curl http://localhost:3003/info

# Protected endpoint (requires token)
curl -H "Authorization: Bearer YOUR_JWT_TOKEN" http://localhost:3003/data
```

### Automated Testing
```bash
# Run all tests
npm test

# Run tests in watch mode
npm run test:watch
```

## Integration with Main System

This service integrates with the main microservice system through:

1. **Authentication**: Uses JWT tokens from auth-service
2. **Service Discovery**: Communicates with other services via Docker DNS
3. **API Gateway**: Accessible through nginx reverse proxy
4. **Database Isolation**: Has its own PostgreSQL database

## Deployment

The service is deployed as part of the main docker-compose stack:

```yaml
# Add to docker-compose.yml
new-service-db:
  image: postgres:15
  environment:
    POSTGRES_DB: newservicedb
    POSTGRES_USER: newservice
    POSTGRES_PASSWORD: newservicepass123
  volumes:
    - new_service_data:/var/lib/postgresql/data
    - ./new-service/init.sql:/docker-entrypoint-initdb.d/init.sql

new-service:
  build: ./new-service
  depends_on:
    - new-service-db
  environment:
    DB_HOST: new-service-db
    # ... other environment variables
```

## Monitoring

### Health Checks
The service provides a comprehensive health check at `/health` that includes:
- Service status
- Database connectivity
- Memory usage
- Uptime information

### Logging
All logs are structured JSON format with:
- Timestamp
- Log level
- Service name
- Message
- Additional context data

### Metrics
Consider implementing metrics collection for:
- Request/response times
- Error rates
- Database query performance
- Custom business metrics

## Security

- JWT token validation for protected endpoints
- Input validation and sanitization
- SQL injection prevention with parameterized queries
- Non-root Docker user
- Environment variable configuration

## Contributing

1. Follow the existing code structure and patterns
2. Add tests for new functionality
3. Update documentation
4. Ensure health checks pass
5. Test integration with other services

## License

MIT License - see LICENSE file for details