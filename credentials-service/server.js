const express = require('express');
const { Pool } = require('pg');
const cors = require('cors');
const axios = require('axios');
const crypto = require('crypto');

const app = express();
const port = process.env.PORT || 3004;

// Environment variables
const DB_HOST = process.env.DB_HOST || 'postgres';
const DB_PORT = process.env.DB_PORT || 5432;
const DB_NAME = process.env.DB_NAME || 'microservices_db';
const DB_USER = process.env.DB_USER || 'postgres';
const DB_PASS = process.env.DB_PASS || 'postgres123';

// Master key for encryption (simplified for demo)
const MASTER_KEY = crypto.scryptSync(process.env.MASTER_KEY || 'default-master-key-change-in-production', 'salt', 32);

// Service URLs for inter-service communication
const AUTH_SERVICE_URL = process.env.AUTH_SERVICE_URL || 'http://auth-service:3002';

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
      service: 'credentials-service',
      ...data
    }));
  },
  error: (message, error = {}) => {
    console.error(JSON.stringify({
      level: 'error',
      message,
      timestamp: new Date().toISOString(),
      service: 'credentials-service',
      error: error.message || error,
      stack: error.stack
    }));
  }
};

// AES encryption utilities (simplified for demo)
const encryption = {
  encrypt: (jsonPayload) => {
    try {
      const plaintext = JSON.stringify(jsonPayload);
      const iv = crypto.randomBytes(16);
      const cipher = crypto.createCipher('aes-256-ctr', MASTER_KEY.toString('hex'));
      let encrypted = cipher.update(plaintext, 'utf8', 'hex');
      encrypted += cipher.final('hex');
      const encBlob = Buffer.concat([iv, Buffer.from(encrypted, 'hex')]);
      return encBlob;
    } catch (error) {
      log.error('Encryption failed', error);
      throw new Error('Encryption failed');
    }
  },

  decrypt: (encBlob) => {
    try {
      if (encBlob.length < 16) {
        throw new Error('Invalid encrypted blob length');
      }
      const iv = encBlob.slice(0, 16);
      const encrypted = encBlob.slice(16).toString('hex');
      const decipher = crypto.createDecipher('aes-256-ctr', MASTER_KEY.toString('hex'));
      let decrypted = decipher.update(encrypted, 'hex', 'utf8');
      decrypted += decipher.final('utf8');
      return JSON.parse(decrypted);
    } catch (error) {
      log.error('Decryption failed', error);
      throw new Error('Decryption failed');
    }
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

// Validate credential payload based on type
function validateCredentialPayload(type, payload) {
  const validTypes = ['winrm_ntlm', 'winrm_basic', 'winrm_kerberos', 'ssh_key'];
  
  if (!validTypes.includes(type)) {
    throw new Error(`Invalid credential type. Must be one of: ${validTypes.join(', ')}`);
  }

  switch (type) {
    case 'winrm_ntlm':
    case 'winrm_basic':
      if (!payload.username || !payload.password) {
        throw new Error('WinRM credentials require username and password');
      }
      break;
    case 'winrm_kerberos':
      if (!payload.username) {
        throw new Error('Kerberos credentials require username');
      }
      break;
    case 'ssh_key':
      if (!payload.username || !payload.private_key) {
        throw new Error('SSH key credentials require username and private_key');
      }
      break;
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
      service: 'credentials-service',
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
      service: 'credentials-service',
      timestamp: new Date().toISOString(),
      error: error.message
    });
  }
});

// Service info endpoint
app.get('/info', (req, res) => {
  try {
    res.json({
      service: 'credentials-service',
      description: 'Secure credential storage with AES-GCM envelope encryption',
      version: '1.0.0',
      supportedTypes: ['winrm_ntlm', 'winrm_basic', 'winrm_kerberos', 'ssh_key'],
      endpoints: [
        'GET /health - Health check',
        'GET /info - Service information',
        'POST /credentials - Create encrypted credential (admin only)',
        'GET /credentials - List credentials (admin only)',
        'GET /credentials/:id - Get credential metadata (admin only)',
        'POST /credentials/:id/rotate - Rotate credential (admin only)',
        'DELETE /credentials/:id - Delete credential (admin only)'
      ]
    });
    log.info('Service info requested');
  } catch (error) {
    log.error('Error serving info', error);
    res.status(500).json({ error: 'Internal server error' });
  }
});

// Create credential endpoint
app.post('/credentials', validateToken, requireRole(['admin']), async (req, res) => {
  try {
    const { name, type, payload } = req.body;

    // Input validation
    if (!name || !type || !payload) {
      return res.status(400).json({ error: 'Name, type, and payload are required' });
    }

    // Validate credential payload
    try {
      validateCredentialPayload(type, payload);
    } catch (validationError) {
      return res.status(400).json({ error: validationError.message });
    }

    // Check if credential name already exists
    const existingCred = await pool.query(
      'SELECT id FROM credentials WHERE name = $1',
      [name]
    );

    if (existingCred.rows.length > 0) {
      return res.status(409).json({ error: 'Credential name already exists' });
    }

    // Encrypt the payload
    const encBlob = encryption.encrypt(payload);

    // Insert credential
    const result = await pool.query(
      'INSERT INTO credentials (name, type, enc_blob, created_at) VALUES ($1, $2, $3, NOW()) RETURNING id, name, type, created_at',
      [name, type, encBlob]
    );

    const newCredential = result.rows[0];
    res.status(201).json(newCredential);
    
    log.info('Credential created', { 
      userId: req.user.id, 
      credentialId: newCredential.id, 
      name: newCredential.name,
      type: newCredential.type
    });
  } catch (error) {
    log.error('Error creating credential', error);
    res.status(500).json({ error: 'Internal server error' });
  }
});

// List credentials endpoint (metadata only, no decrypted payloads)
app.get('/credentials', validateToken, requireRole(['admin']), async (req, res) => {
  try {
    const result = await pool.query(
      'SELECT id, name, type, created_at, rotated_at FROM credentials ORDER BY created_at DESC'
    );

    res.json({
      credentials: result.rows,
      total: result.rows.length
    });
    
    log.info('Credentials listed', { 
      userId: req.user.id, 
      count: result.rows.length 
    });
  } catch (error) {
    log.error('Error listing credentials', error);
    res.status(500).json({ error: 'Internal server error' });
  }
});

// Get credential metadata endpoint
app.get('/credentials/:id', validateToken, requireRole(['admin']), async (req, res) => {
  try {
    const { id } = req.params;

    const result = await pool.query(
      'SELECT id, name, type, created_at, rotated_at FROM credentials WHERE id = $1',
      [id]
    );

    if (result.rows.length === 0) {
      return res.status(404).json({ error: 'Credential not found' });
    }

    res.json(result.rows[0]);
    
    log.info('Credential metadata retrieved', { 
      userId: req.user.id, 
      credentialId: id 
    });
  } catch (error) {
    log.error('Error retrieving credential', error);
    res.status(500).json({ error: 'Internal server error' });
  }
});

// Rotate credential endpoint
app.post('/credentials/:id/rotate', validateToken, requireRole(['admin']), async (req, res) => {
  try {
    const { id } = req.params;
    const { payload } = req.body;

    if (!payload) {
      return res.status(400).json({ error: 'New payload is required' });
    }

    // Get existing credential to validate type
    const existingResult = await pool.query(
      'SELECT id, name, type FROM credentials WHERE id = $1',
      [id]
    );

    if (existingResult.rows.length === 0) {
      return res.status(404).json({ error: 'Credential not found' });
    }

    const existingCred = existingResult.rows[0];

    // Validate new payload
    try {
      validateCredentialPayload(existingCred.type, payload);
    } catch (validationError) {
      return res.status(400).json({ error: validationError.message });
    }

    // Encrypt the new payload
    const encBlob = encryption.encrypt(payload);

    // Update credential
    const result = await pool.query(
      'UPDATE credentials SET enc_blob = $1, rotated_at = NOW() WHERE id = $2 RETURNING id, name, type, created_at, rotated_at',
      [encBlob, id]
    );

    res.json(result.rows[0]);
    
    log.info('Credential rotated', { 
      userId: req.user.id, 
      credentialId: id,
      name: existingCred.name,
      type: existingCred.type
    });
  } catch (error) {
    log.error('Error rotating credential', error);
    res.status(500).json({ error: 'Internal server error' });
  }
});

// Delete credential endpoint
app.delete('/credentials/:id', validateToken, requireRole(['admin']), async (req, res) => {
  try {
    const { id } = req.params;

    const result = await pool.query(
      'DELETE FROM credentials WHERE id = $1 RETURNING id, name, type',
      [id]
    );

    if (result.rows.length === 0) {
      return res.status(404).json({ error: 'Credential not found' });
    }

    const deletedCred = result.rows[0];
    res.json({ message: 'Credential deleted successfully', credential: deletedCred });
    
    log.info('Credential deleted', { 
      userId: req.user.id, 
      credentialId: id,
      name: deletedCred.name,
      type: deletedCred.type
    });
  } catch (error) {
    log.error('Error deleting credential', error);
    res.status(500).json({ error: 'Internal server error' });
  }
});

// Internal endpoint for other services to decrypt credentials (service-to-service only)
app.post('/internal/decrypt/:id', async (req, res) => {
  try {
    // This endpoint should only be accessible from within the Docker network
    // In production, add additional security measures like service tokens
    
    const { id } = req.params;

    const result = await pool.query(
      'SELECT id, name, type, enc_blob FROM credentials WHERE id = $1',
      [id]
    );

    if (result.rows.length === 0) {
      return res.status(404).json({ error: 'Credential not found' });
    }

    const credential = result.rows[0];
    const decryptedPayload = encryption.decrypt(credential.enc_blob);

    res.json({
      id: credential.id,
      name: credential.name,
      type: credential.type,
      payload: decryptedPayload
    });
    
    log.info('Credential decrypted for internal service', { 
      credentialId: id,
      name: credential.name,
      type: credential.type
    });
  } catch (error) {
    log.error('Error decrypting credential', error);
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
  log.info('Credentials service started', { port, service: 'credentials-service' });
});

module.exports = app;