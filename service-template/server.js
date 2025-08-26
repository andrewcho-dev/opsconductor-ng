const express = require('express');
const { Pool } = require('pg');
const cors = require('cors');
const axios = require('axios');

const app = express();
const port = process.env.PORT || 3003; // Change this to next available port

// Environment variables
const DB_HOST = process.env.DB_HOST || 'new-service-db';
const DB_PORT = process.env.DB_PORT || 5432;
const DB_NAME = process.env.DB_NAME || 'newservicedb';
const DB_USER = process.env.DB_USER || 'newservice';
const DB_PASS = process.env.DB_PASS || 'newservicepass123';

// Service URLs for inter-service communication
const AUTH_SERVICE_URL = process.env.AUTH_SERVICE_URL || 'http://auth-service:3002';
const USER_SERVICE_URL = process.env.USER_SERVICE_URL || 'http://user-service:3001';

// Middleware
app.use(cors());
app.use(express.json());

// Database connection pool (remove if no database needed)
const pool = new Pool({
  host: DB_HOST,
  port: DB_PORT,
  database: DB_NAME,
  user: DB_USER,
  password: DB_PASS,
  max: 20,
  idleTimeoutMillis: 30000,
  connectionTimeoutMillis: 2000,
});

// Structured logging
const log = {
  info: (message, data = {}) => {
    console.log(JSON.stringify({
      level: 'info',
      message,
      timestamp: new Date().toISOString(),
      service: 'new-service', // Change this to your service name
      ...data
    }));
  },
  error: (message, error = {}) => {
    console.error(JSON.stringify({
      level: 'error',
      message,
      timestamp: new Date().toISOString(),
      service: 'new-service', // Change this to your service name
      error: error.message || error,
      stack: error.stack
    }));
  }
};

// Authentication middleware
async function validateToken(req, res, next) {
  try {
    const token = req.headers.authorization?.replace('Bearer ', '');
    if (!token) {
      return res.status(401).json({ error: 'No token provided' });
    }

    // Verify token with auth service
    const response = await axios.post(`${AUTH_SERVICE_URL}/verify`, {}, {
      headers: { 'Authorization': `Bearer ${token}` }
    });

    req.user = response.data.user;
    log.info('Token validated', { userId: req.user.id, username: req.user.username });
    next();
  } catch (error) {
    log.error('Token validation failed', error);
    res.status(401).json({ error: 'Invalid token' });
  }
}

// Health check endpoint (required for all services)
app.get('/health', async (req, res) => {
  try {
    // Test database connection if applicable
    let dbStatus = 'not-applicable';
    if (pool) {
      try {
        await pool.query('SELECT 1');
        dbStatus = 'healthy';
      } catch (dbError) {
        dbStatus = 'unhealthy';
        log.error('Database health check failed', dbError);
      }
    }

    const healthData = {
      status: 'healthy',
      service: 'new-service', // Change this to your service name
      timestamp: new Date().toISOString(),
      uptime: process.uptime(),
      memory: process.memoryUsage(),
      version: process.env.npm_package_version || '1.0.0',
      database: dbStatus
    };

    res.json(healthData);
    log.info('Health check requested', { status: 'healthy' });
  } catch (error) {
    log.error('Health check failed', error);
    res.status(500).json({
      status: 'unhealthy',
      service: 'new-service',
      timestamp: new Date().toISOString(),
      error: error.message
    });
  }
});

// Example public endpoint (no authentication required)
app.get('/info', (req, res) => {
  try {
    res.json({
      service: 'new-service',
      description: 'This is a new microservice',
      version: '1.0.0',
      endpoints: [
        'GET /health - Health check',
        'GET /info - Service information',
        'GET /data - Get data (requires authentication)',
        'POST /data - Create data (requires authentication)'
      ]
    });
    log.info('Service info requested');
  } catch (error) {
    log.error('Error serving info', error);
    res.status(500).json({ error: 'Internal server error' });
  }
});

// Example protected endpoint (requires authentication)
app.get('/data', validateToken, async (req, res) => {
  try {
    const page = parseInt(req.query.page) || 1;
    const limit = parseInt(req.query.limit) || 10;
    const offset = (page - 1) * limit;

    // Example database query (modify based on your needs)
    const result = await pool.query(
      'SELECT id, name, description, created_at FROM new_service_data ORDER BY created_at DESC LIMIT $1 OFFSET $2',
      [limit, offset]
    );

    const countResult = await pool.query('SELECT COUNT(*) FROM new_service_data');
    const totalItems = parseInt(countResult.rows[0].count);
    const totalPages = Math.ceil(totalItems / limit);

    const responseData = {
      data: result.rows,
      pagination: {
        currentPage: page,
        totalPages,
        totalItems,
        hasNext: page < totalPages,
        hasPrev: page > 1
      }
    };

    res.json(responseData);
    log.info('Data retrieved', { 
      userId: req.user.id, 
      page, 
      limit, 
      totalItems: result.rows.length 
    });
  } catch (error) {
    log.error('Error retrieving data', error);
    res.status(500).json({ error: 'Internal server error' });
  }
});

// Example POST endpoint (requires authentication)
app.post('/data', validateToken, async (req, res) => {
  try {
    const { name, description } = req.body;

    // Input validation
    if (!name || !description) {
      return res.status(400).json({ error: 'Name and description are required' });
    }

    // Insert data
    const result = await pool.query(
      'INSERT INTO new_service_data (name, description) VALUES ($1, $2) RETURNING id, name, description, created_at',
      [name, description]
    );

    const newItem = result.rows[0];
    res.status(201).json(newItem);
    log.info('Data created', { 
      userId: req.user.id, 
      itemId: newItem.id, 
      name: newItem.name 
    });
  } catch (error) {
    log.error('Error creating data', error);
    res.status(500).json({ error: 'Internal server error' });
  }
});

// Example service-to-service communication
app.get('/user-info/:userId', validateToken, async (req, res) => {
  try {
    const { userId } = req.params;

    // Call user service to get user information
    const userResponse = await axios.get(`${USER_SERVICE_URL}/users/id/${userId}`, {
      headers: {
        'Authorization': req.headers.authorization
      }
    });

    res.json({
      message: 'User information retrieved from user service',
      user: userResponse.data
    });

    log.info('User info retrieved via service call', { 
      requestedUserId: userId, 
      requestingUserId: req.user.id 
    });
  } catch (error) {
    log.error('Error retrieving user info', error);
    if (error.response) {
      res.status(error.response.status).json(error.response.data);
    } else {
      res.status(500).json({ error: 'Internal server error' });
    }
  }
});

// Error handling middleware
app.use((error, req, res, next) => {
  log.error('Unhandled error', error);
  res.status(500).json({ error: 'Internal server error' });
});

// 404 handler
app.use('*', (req, res) => {
  res.status(404).json({ error: 'Endpoint not found' });
});

// Graceful shutdown handling
process.on('SIGTERM', async () => {
  log.info('SIGTERM received, shutting down gracefully');
  
  // Close database connections
  if (pool) {
    await pool.end();
    log.info('Database connections closed');
  }
  
  process.exit(0);
});

process.on('SIGINT', async () => {
  log.info('SIGINT received, shutting down gracefully');
  
  // Close database connections
  if (pool) {
    await pool.end();
    log.info('Database connections closed');
  }
  
  process.exit(0);
});

// Start server
app.listen(port, () => {
  log.info('Service started', { port, service: 'new-service' });
});

module.exports = app; // For testing purposes