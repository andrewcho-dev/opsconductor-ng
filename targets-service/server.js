const express = require('express');
const { Pool } = require('pg');
const cors = require('cors');
const axios = require('axios');

const app = express();
const port = process.env.PORT || 3005;

// Environment variables
const DB_HOST = process.env.DB_HOST || 'postgres';
const DB_PORT = process.env.DB_PORT || 5432;
const DB_NAME = process.env.DB_NAME || 'microservices_db';
const DB_USER = process.env.DB_USER || 'postgres';
const DB_PASS = process.env.DB_PASS || 'postgres123';

// Service URLs for inter-service communication
const AUTH_SERVICE_URL = process.env.AUTH_SERVICE_URL || 'http://auth-service:3002';
const CREDENTIALS_SERVICE_URL = process.env.CREDENTIALS_SERVICE_URL || 'http://credentials-service:3004';

// Middleware
app.use(cors());
app.use(express.json());

// Database connection pool
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
      service: 'targets-service',
      ...data
    }));
  },
  error: (message, error = {}) => {
    console.error(JSON.stringify({
      level: 'error',
      message,
      timestamp: new Date().toISOString(),
      service: 'targets-service',
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
    log.info('Token validated', { userId: req.user.id, email: req.user.email });
    next();
  } catch (error) {
    log.error('Token validation failed', error);
    res.status(401).json({ error: 'Invalid token' });
  }
}

// Role-based authorization middleware
function requireRole(roles) {
  return (req, res, next) => {
    if (!req.user) {
      return res.status(401).json({ error: 'Authentication required' });
    }
    
    if (!roles.includes(req.user.role)) {
      log.info('Access denied - insufficient role', { 
        userId: req.user.id, 
        userRole: req.user.role, 
        requiredRoles: roles 
      });
      return res.status(403).json({ error: 'Insufficient permissions' });
    }
    
    next();
  };
}

// Validate target data
function validateTargetData(data) {
  const { name, protocol, hostname, port, winrm_use_https, winrm_validate_cert, domain, credential_ref, tags, depends_on } = data;

  if (!name || !hostname || !credential_ref) {
    throw new Error('Name, hostname, and credential_ref are required');
  }

  if (protocol && !['winrm', 'ssh'].includes(protocol)) {
    throw new Error('Protocol must be either "winrm" or "ssh"');
  }

  if (port && (port < 1 || port > 65535)) {
    throw new Error('Port must be between 1 and 65535');
  }

  if (winrm_use_https !== undefined && typeof winrm_use_https !== 'boolean') {
    throw new Error('winrm_use_https must be a boolean');
  }

  if (winrm_validate_cert !== undefined && typeof winrm_validate_cert !== 'boolean') {
    throw new Error('winrm_validate_cert must be a boolean');
  }

  if (tags && typeof tags !== 'object') {
    throw new Error('Tags must be a JSON object');
  }

  if (depends_on && !Array.isArray(depends_on)) {
    throw new Error('depends_on must be an array of target IDs');
  }
}

// Health check endpoint
app.get('/health', async (req, res) => {
  try {
    let dbStatus = 'healthy';
    try {
      await pool.query('SELECT 1');
    } catch (dbError) {
      dbStatus = 'unhealthy';
      log.error('Database health check failed', dbError);
    }

    const healthData = {
      status: dbStatus === 'healthy' ? 'healthy' : 'unhealthy',
      service: 'targets-service',
      timestamp: new Date().toISOString(),
      uptime: process.uptime(),
      memory: process.memoryUsage(),
      version: process.env.npm_package_version || '1.0.0',
      database: dbStatus
    };

    res.json(healthData);
    log.info('Health check requested', { status: healthData.status });
  } catch (error) {
    log.error('Health check failed', error);
    res.status(500).json({
      status: 'unhealthy',
      service: 'targets-service',
      timestamp: new Date().toISOString(),
      error: error.message
    });
  }
});

// Service info endpoint
app.get('/info', (req, res) => {
  try {
    res.json({
      service: 'targets-service',
      description: 'Target management service for WinRM and SSH connections',
      version: '1.0.0',
      supportedProtocols: ['winrm', 'ssh'],
      endpoints: [
        'GET /health - Health check',
        'GET /info - Service information',
        'POST /targets - Create target (admin/operator)',
        'GET /targets - List targets (admin/operator/viewer)',
        'GET /targets/:id - Get target details (admin/operator/viewer)',
        'PUT /targets/:id - Update target (admin/operator)',
        'DELETE /targets/:id - Delete target (admin)',
        'POST /targets/:id/test-winrm - Test WinRM connection (admin/operator)'
      ]
    });
    log.info('Service info requested');
  } catch (error) {
    log.error('Error serving info', error);
    res.status(500).json({ error: 'Internal server error' });
  }
});

// Create target endpoint
app.post('/targets', validateToken, requireRole(['admin', 'operator']), async (req, res) => {
  try {
    const targetData = {
      protocol: 'winrm', // default
      port: 5986, // default for WinRM HTTPS
      winrm_use_https: true, // default
      winrm_validate_cert: true, // default
      tags: {}, // default
      depends_on: [], // default
      ...req.body
    };

    // Validate input data
    try {
      validateTargetData(targetData);
    } catch (validationError) {
      return res.status(400).json({ error: validationError.message });
    }

    // Check if target name already exists
    const existingTarget = await pool.query(
      'SELECT id FROM targets WHERE name = $1',
      [targetData.name]
    );

    if (existingTarget.rows.length > 0) {
      return res.status(409).json({ error: 'Target name already exists' });
    }

    // Verify credential exists (call credentials service)
    try {
      await axios.get(`${CREDENTIALS_SERVICE_URL}/credentials/${targetData.credential_ref}`, {
        headers: { 'Authorization': req.headers.authorization }
      });
    } catch (credError) {
      if (credError.response?.status === 404) {
        return res.status(400).json({ error: 'Referenced credential not found' });
      }
      throw credError;
    }

    // Insert target
    const result = await pool.query(
      `INSERT INTO targets (name, protocol, hostname, port, winrm_use_https, winrm_validate_cert, domain, credential_ref, tags, depends_on, created_at) 
       VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, NOW()) 
       RETURNING id, name, protocol, hostname, port, winrm_use_https, winrm_validate_cert, domain, credential_ref, tags, depends_on, created_at`,
      [
        targetData.name,
        targetData.protocol,
        targetData.hostname,
        targetData.port,
        targetData.winrm_use_https,
        targetData.winrm_validate_cert,
        targetData.domain,
        targetData.credential_ref,
        JSON.stringify(targetData.tags),
        targetData.depends_on
      ]
    );

    const newTarget = result.rows[0];
    res.status(201).json(newTarget);
    
    log.info('Target created', { 
      userId: req.user.id, 
      targetId: newTarget.id, 
      name: newTarget.name,
      protocol: newTarget.protocol,
      hostname: newTarget.hostname
    });
  } catch (error) {
    log.error('Error creating target', error);
    res.status(500).json({ error: 'Internal server error' });
  }
});

// List targets endpoint
app.get('/targets', validateToken, requireRole(['admin', 'operator', 'viewer']), async (req, res) => {
  try {
    const page = parseInt(req.query.page) || 1;
    const limit = parseInt(req.query.limit) || 20;
    const offset = (page - 1) * limit;
    const protocol = req.query.protocol;
    const tags = req.query.tags;

    let query = 'SELECT id, name, protocol, hostname, port, winrm_use_https, winrm_validate_cert, domain, credential_ref, tags, depends_on, created_at FROM targets';
    let countQuery = 'SELECT COUNT(*) FROM targets';
    const queryParams = [];
    const conditions = [];

    // Add protocol filter
    if (protocol) {
      conditions.push(`protocol = $${queryParams.length + 1}`);
      queryParams.push(protocol);
    }

    // Add tags filter (simple JSON containment)
    if (tags) {
      try {
        const tagsObj = JSON.parse(tags);
        conditions.push(`tags @> $${queryParams.length + 1}`);
        queryParams.push(JSON.stringify(tagsObj));
      } catch (e) {
        return res.status(400).json({ error: 'Invalid tags JSON format' });
      }
    }

    // Apply conditions
    if (conditions.length > 0) {
      const whereClause = ' WHERE ' + conditions.join(' AND ');
      query += whereClause;
      countQuery += whereClause;
    }

    // Add ordering and pagination
    query += ' ORDER BY created_at DESC LIMIT $' + (queryParams.length + 1) + ' OFFSET $' + (queryParams.length + 2);
    queryParams.push(limit, offset);

    const [result, countResult] = await Promise.all([
      pool.query(query, queryParams),
      pool.query(countQuery, queryParams.slice(0, -2)) // Remove limit and offset for count
    ]);

    const totalItems = parseInt(countResult.rows[0].count);
    const totalPages = Math.ceil(totalItems / limit);

    const responseData = {
      targets: result.rows,
      pagination: {
        currentPage: page,
        totalPages,
        totalItems,
        hasNext: page < totalPages,
        hasPrev: page > 1
      }
    };

    res.json(responseData);
    
    log.info('Targets listed', { 
      userId: req.user.id, 
      page, 
      limit, 
      totalItems: result.rows.length,
      filters: { protocol, tags }
    });
  } catch (error) {
    log.error('Error listing targets', error);
    res.status(500).json({ error: 'Internal server error' });
  }
});

// Get target details endpoint
app.get('/targets/:id', validateToken, requireRole(['admin', 'operator', 'viewer']), async (req, res) => {
  try {
    const { id } = req.params;

    const result = await pool.query(
      'SELECT id, name, protocol, hostname, port, winrm_use_https, winrm_validate_cert, domain, credential_ref, tags, depends_on, created_at FROM targets WHERE id = $1',
      [id]
    );

    if (result.rows.length === 0) {
      return res.status(404).json({ error: 'Target not found' });
    }

    res.json(result.rows[0]);
    
    log.info('Target details retrieved', { 
      userId: req.user.id, 
      targetId: id 
    });
  } catch (error) {
    log.error('Error retrieving target', error);
    res.status(500).json({ error: 'Internal server error' });
  }
});

// Update target endpoint
app.put('/targets/:id', validateToken, requireRole(['admin', 'operator']), async (req, res) => {
  try {
    const { id } = req.params;
    const updates = req.body;

    // Get existing target
    const existingResult = await pool.query(
      'SELECT * FROM targets WHERE id = $1',
      [id]
    );

    if (existingResult.rows.length === 0) {
      return res.status(404).json({ error: 'Target not found' });
    }

    const existingTarget = existingResult.rows[0];
    const updatedData = { ...existingTarget, ...updates };

    // Validate updated data
    try {
      validateTargetData(updatedData);
    } catch (validationError) {
      return res.status(400).json({ error: validationError.message });
    }

    // Check if new name conflicts with existing targets (if name is being changed)
    if (updates.name && updates.name !== existingTarget.name) {
      const nameCheck = await pool.query(
        'SELECT id FROM targets WHERE name = $1 AND id != $2',
        [updates.name, id]
      );

      if (nameCheck.rows.length > 0) {
        return res.status(409).json({ error: 'Target name already exists' });
      }
    }

    // Verify credential exists if credential_ref is being updated
    if (updates.credential_ref && updates.credential_ref !== existingTarget.credential_ref) {
      try {
        await axios.get(`${CREDENTIALS_SERVICE_URL}/credentials/${updates.credential_ref}`, {
          headers: { 'Authorization': req.headers.authorization }
        });
      } catch (credError) {
        if (credError.response?.status === 404) {
          return res.status(400).json({ error: 'Referenced credential not found' });
        }
        throw credError;
      }
    }

    // Update target
    const result = await pool.query(
      `UPDATE targets SET 
       name = $1, protocol = $2, hostname = $3, port = $4, 
       winrm_use_https = $5, winrm_validate_cert = $6, domain = $7, 
       credential_ref = $8, tags = $9, depends_on = $10
       WHERE id = $11 
       RETURNING id, name, protocol, hostname, port, winrm_use_https, winrm_validate_cert, domain, credential_ref, tags, depends_on, created_at`,
      [
        updatedData.name,
        updatedData.protocol,
        updatedData.hostname,
        updatedData.port,
        updatedData.winrm_use_https,
        updatedData.winrm_validate_cert,
        updatedData.domain,
        updatedData.credential_ref,
        JSON.stringify(updatedData.tags),
        updatedData.depends_on,
        id
      ]
    );

    res.json(result.rows[0]);
    
    log.info('Target updated', { 
      userId: req.user.id, 
      targetId: id,
      name: updatedData.name,
      changes: Object.keys(updates)
    });
  } catch (error) {
    log.error('Error updating target', error);
    res.status(500).json({ error: 'Internal server error' });
  }
});

// Delete target endpoint
app.delete('/targets/:id', validateToken, requireRole(['admin']), async (req, res) => {
  try {
    const { id } = req.params;

    const result = await pool.query(
      'DELETE FROM targets WHERE id = $1 RETURNING id, name, protocol, hostname',
      [id]
    );

    if (result.rows.length === 0) {
      return res.status(404).json({ error: 'Target not found' });
    }

    const deletedTarget = result.rows[0];
    res.json({ message: 'Target deleted successfully', target: deletedTarget });
    
    log.info('Target deleted', { 
      userId: req.user.id, 
      targetId: id,
      name: deletedTarget.name,
      hostname: deletedTarget.hostname
    });
  } catch (error) {
    log.error('Error deleting target', error);
    res.status(500).json({ error: 'Internal server error' });
  }
});

// Test WinRM connection endpoint (mock for Sprint 1)
app.post('/targets/:id/test-winrm', validateToken, requireRole(['admin', 'operator']), async (req, res) => {
  try {
    const { id } = req.params;

    // Get target details
    const targetResult = await pool.query(
      'SELECT id, name, protocol, hostname, port, winrm_use_https, winrm_validate_cert, domain, credential_ref FROM targets WHERE id = $1',
      [id]
    );

    if (targetResult.rows.length === 0) {
      return res.status(404).json({ error: 'Target not found' });
    }

    const target = targetResult.rows[0];

    // For Sprint 1, return a mock response
    // In Sprint 2, this will actually test the WinRM connection
    const mockResponse = {
      target: {
        id: target.id,
        name: target.name,
        hostname: target.hostname,
        port: target.port,
        protocol: target.protocol,
        useHttps: target.winrm_use_https,
        validateCert: target.winrm_validate_cert
      },
      test: {
        status: 'success',
        message: 'Mock WinRM test - connection would be tested here',
        timestamp: new Date().toISOString(),
        details: {
          whoami: 'MOCK\\Administrator',
          powershellVersion: '5.1.19041.1682',
          transport: target.winrm_use_https ? 'HTTPS' : 'HTTP',
          authMethod: 'NTLM',
          responseTime: Math.floor(Math.random() * 500) + 100 // Mock response time
        }
      },
      note: 'This is a mock response for Sprint 1. Actual WinRM testing will be implemented in Sprint 2.'
    };

    res.json(mockResponse);
    
    log.info('WinRM test requested (mock)', { 
      userId: req.user.id, 
      targetId: id,
      targetName: target.name,
      hostname: target.hostname
    });
  } catch (error) {
    log.error('Error testing WinRM connection', error);
    res.status(500).json({ error: 'Internal server error' });
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
  
  if (pool) {
    await pool.end();
    log.info('Database connections closed');
  }
  
  process.exit(0);
});

process.on('SIGINT', async () => {
  log.info('SIGINT received, shutting down gracefully');
  
  if (pool) {
    await pool.end();
    log.info('Database connections closed');
  }
  
  process.exit(0);
});

// Start server
app.listen(port, () => {
  log.info('Targets service started', { port, service: 'targets-service' });
});

module.exports = app;