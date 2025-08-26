const express = require('express');
const { Pool } = require('pg');
const bcrypt = require('bcryptjs');
const jwt = require('jsonwebtoken');
const cors = require('cors');

console.log('=== USER SERVICE STARTING - DEBUG VERSION ===');
const app = express();
const port = process.env.PORT || 3001;

// Database connection
const pool = new Pool({
  host: process.env.DB_HOST || 'postgres',
  port: process.env.DB_PORT || 5432,
  database: process.env.DB_NAME || 'opsconductor',
  user: process.env.DB_USER || 'opsconductor',
  password: process.env.DB_PASS || 'opsconductor123',
  max: 20,
  idleTimeoutMillis: 30000,
  connectionTimeoutMillis: 10000,
});

// Configuration
const JWT_SECRET = process.env.JWT_SECRET || 'your-super-secret-jwt-key';

// Middleware
app.use(cors());
app.use(express.json());

// JWT verification middleware
function verifyToken(req, res, next) {
  const authHeader = req.headers['authorization'];
  const token = authHeader && authHeader.split(' ')[1];

  if (!token) {
    return res.status(401).json({ error: 'Access token required' });
  }

  jwt.verify(token, JWT_SECRET, async (err, decoded) => {
    if (err) {
      return res.status(403).json({ error: 'Invalid or expired token' });
    }

    // Get user details including current token_version
    try {
      const result = await pool.query(
        'SELECT id, username, email, firstname, lastname, role, token_version FROM users WHERE id = $1',
        [decoded.userId]
      );

      if (result.rows.length === 0) {
        return res.status(403).json({ error: 'User not found' });
      }

      const user = result.rows[0];

      // Check if token version matches (for token revocation)
      if (decoded.tokenVersion !== undefined && decoded.tokenVersion !== user.token_version) {
        return res.status(403).json({ error: 'Token has been revoked' });
      }

      req.user = user;
      next();
    } catch (error) {
      console.error('Token verification error:', error);
      return res.status(500).json({ error: 'Internal server error' });
    }
  });
}

// Role-based authorization middleware
function requireRole(allowedRoles) {
  return (req, res, next) => {
    if (!req.user) {
      return res.status(401).json({ error: 'Authentication required' });
    }

    if (!allowedRoles.includes(req.user.role)) {
      return res.status(403).json({ error: 'Insufficient permissions' });
    }

    next();
  };
}

// Initialize database
async function initDatabase() {
  try {
    // Create users table with new OpsConductor fields
    await pool.query(`
      CREATE TABLE IF NOT EXISTS users (
        id BIGSERIAL PRIMARY KEY,
        username TEXT UNIQUE NOT NULL,
        email TEXT UNIQUE NOT NULL,
        firstname TEXT,
        lastname TEXT,
        pwd_hash TEXT NOT NULL,
        role TEXT DEFAULT 'operator' CHECK (role IN ('operator', 'admin', 'viewer')),
        token_version INTEGER DEFAULT 0,
        created_at TIMESTAMPTZ DEFAULT NOW()
      )
    `);

    // Migration: Add new columns if they don't exist (for existing installations)
    try {
      await pool.query(`ALTER TABLE users ADD COLUMN IF NOT EXISTS firstname TEXT`);
      await pool.query(`ALTER TABLE users ADD COLUMN IF NOT EXISTS lastname TEXT`);
      console.log('Database migration completed successfully');
    } catch (migrationError) {
      console.log('Migration skipped (columns may already exist):', migrationError.message);
    }

    console.log('Database initialized successfully');
  } catch (error) {
    console.error('Database initialization error:', error);
  }
}

// Routes

// Health check
app.get('/health', (req, res) => {
  res.json({ status: 'healthy', service: 'user-service' });
});

// Login endpoint (temporary solution)
app.post('/login', async (req, res) => {
  try {
    const { username, password } = req.body;
    
    if (!username || !password) {
      return res.status(400).json({ error: 'Username and password are required' });
    }

    // Get user from database
    const result = await pool.query(
      'SELECT id, username, email, firstname, lastname, pwd_hash, role, token_version FROM users WHERE username = $1',
      [username]
    );

    if (result.rows.length === 0) {
      return res.status(401).json({ error: 'Invalid credentials' });
    }

    const user = result.rows[0];

    // Verify password
    const isValidPassword = await bcrypt.compare(password, user.pwd_hash);
    if (!isValidPassword) {
      return res.status(401).json({ error: 'Invalid credentials' });
    }

    // Generate JWT token
    const tokenPayload = {
      userId: user.id,
      username: user.username,
      email: user.email,
      role: user.role,
      tokenVersion: user.token_version || 0
    };

    const accessToken = jwt.sign(tokenPayload, JWT_SECRET, { expiresIn: '15m' });
    const refreshToken = jwt.sign({ 
      userId: user.id, 
      tokenVersion: user.token_version || 0,
      type: 'refresh' 
    }, JWT_SECRET, { expiresIn: '7d' });

    res.json({
      accessToken,
      refreshToken,
      user: {
        id: user.id,
        username: user.username,
        email: user.email,
        firstname: user.firstname,
        lastname: user.lastname,
        role: user.role
      }
    });
  } catch (error) {
    console.error('Login error:', error);
    res.status(500).json({ error: 'Internal server error' });
  }
});

// Create user (both endpoints for compatibility)
app.post('/users', async (req, res) => {
  try {
    const { username, email, firstname, lastname, password, role = 'operator' } = req.body;
    
    if (!username || !email || !firstname || !lastname || !password) {
      return res.status(400).json({ error: 'Username, email, firstname, lastname, and password are required' });
    }

    // Validate email format
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    if (!emailRegex.test(email)) {
      return res.status(400).json({ error: 'Invalid email format' });
    }

    // Validate role
    const validRoles = ['operator', 'admin', 'viewer'];
    if (!validRoles.includes(role)) {
      return res.status(400).json({ error: 'Invalid role. Must be operator, admin, or viewer' });
    }

    // Hash password
    const hashedPassword = await bcrypt.hash(password, 10);

    const result = await pool.query(
      'INSERT INTO users (username, email, firstname, lastname, pwd_hash, role, token_version) VALUES ($1, $2, $3, $4, $5, $6, $7) RETURNING id, username, email, firstname, lastname, role, created_at',
      [username, email, firstname, lastname, hashedPassword, role, 0]
    );

    res.status(201).json(result.rows[0]);
  } catch (error) {
    if (error.code === '23505') { // Unique violation
      if (error.constraint && error.constraint.includes('email')) {
        res.status(409).json({ error: 'Email already exists' });
      } else {
        res.status(409).json({ error: 'Username already exists' });
      }
    } else {
      console.error('Create user error:', error);
      res.status(500).json({ error: 'Internal server error' });
    }
  }
});

// Register endpoint (alias for /users POST - for frontend compatibility)
app.post('/register', async (req, res) => {
  try {
    const { username, email, firstname, lastname, password, role = 'operator' } = req.body;
    
    if (!username || !email || !firstname || !lastname || !password) {
      return res.status(400).json({ error: 'Username, email, firstname, lastname, and password are required' });
    }

    // Validate email format
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    if (!emailRegex.test(email)) {
      return res.status(400).json({ error: 'Invalid email format' });
    }

    // Validate role
    const validRoles = ['operator', 'admin', 'viewer'];
    if (!validRoles.includes(role)) {
      return res.status(400).json({ error: 'Invalid role. Must be operator, admin, or viewer' });
    }

    // Hash password
    const hashedPassword = await bcrypt.hash(password, 10);

    const result = await pool.query(
      'INSERT INTO users (username, email, firstname, lastname, pwd_hash, role, token_version) VALUES ($1, $2, $3, $4, $5, $6, $7) RETURNING id, username, email, firstname, lastname, role, created_at',
      [username, email, firstname, lastname, hashedPassword, role, 0]
    );

    res.status(201).json(result.rows[0]);
  } catch (error) {
    if (error.code === '23505') { // Unique violation
      if (error.constraint && error.constraint.includes('email')) {
        res.status(409).json({ error: 'Email already exists' });
      } else {
        res.status(409).json({ error: 'Username already exists' });
      }
    } else {
      console.error('Create user error:', error);
      res.status(500).json({ error: 'Internal server error' });
    }
  }
});

// Get all users (for admin/management) - moved before :id route
app.get('/users', async (req, res) => {
  console.log('GET /users called with query:', req.query);
  try {
    const page = parseInt(req.query.page) || 1;
    const limit = parseInt(req.query.limit) || 10;
    const offset = (page - 1) * limit;
    const search = req.query.search || '';

    let query = 'SELECT id, username, email, firstname, lastname, role, created_at FROM users';
    let countQuery = 'SELECT COUNT(*) FROM users';
    let params = [];

    if (search) {
      query += ' WHERE username ILIKE $1 OR firstname ILIKE $1 OR lastname ILIKE $1 OR email ILIKE $1';
      countQuery += ' WHERE username ILIKE $1 OR firstname ILIKE $1 OR lastname ILIKE $1 OR email ILIKE $1';
      params.push(`%${search}%`);
    }

    query += ` ORDER BY created_at DESC LIMIT $${params.length + 1} OFFSET $${params.length + 2}`;
    params.push(limit, offset);

    const [users, count] = await Promise.all([
      pool.query(query, params),
      pool.query(countQuery, search ? [`%${search}%`] : [])
    ]);

    const totalUsers = parseInt(count.rows[0].count);
    const totalPages = Math.ceil(totalUsers / limit);

    res.json({
      users: users.rows,
      pagination: {
        currentPage: page,
        totalPages,
        totalUsers,
        hasNext: page < totalPages,
        hasPrev: page > 1
      }
    });
  } catch (error) {
    console.error('Get users error:', error);
    res.status(500).json({ error: 'Internal server error' });
  }
});

// Get user by ID (using same endpoint pattern as PUT/DELETE) - moved after /users route
app.get('/users/:id', async (req, res) => {
  try {
    const { id } = req.params;
    const userId = parseInt(id);
    
    if (isNaN(userId)) {
      return res.status(400).json({ error: 'Invalid user ID' });
    }
    
    const result = await pool.query(
      'SELECT id, username, email, firstname, lastname, role, created_at FROM users WHERE id = $1',
      [userId]
    );

    if (result.rows.length === 0) {
      return res.status(404).json({ error: 'User not found' });
    }

    res.json(result.rows[0]);
  } catch (error) {
    console.error('Get user by ID error:', error);
    res.status(500).json({ error: 'Internal server error' });
  }
});

// Get user by username (for auth service) - moved after numeric ID route
app.get('/users/by-username/:username', async (req, res) => {
  try {
    const { username } = req.params;
    
    const result = await pool.query(
      'SELECT id, username, email, firstname, lastname, pwd_hash as password, role, token_version, created_at FROM users WHERE username = $1',
      [username]
    );

    if (result.rows.length === 0) {
      return res.status(404).json({ error: 'User not found' });
    }

    res.json(result.rows[0]);
  } catch (error) {
    console.error('Get user error:', error);
    res.status(500).json({ error: 'Internal server error' });
  }
});

// Update user
app.put('/users/:id', async (req, res) => {
  try {
    const { id } = req.params;
    const { firstname, lastname, username, email, role } = req.body;
    
    if (!firstname || !lastname || !username || !email) {
      return res.status(400).json({ error: 'Username, email, firstname, and lastname are required' });
    }

    // Validate email format
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    if (!emailRegex.test(email)) {
      return res.status(400).json({ error: 'Invalid email format' });
    }

    // Validate role if provided
    if (role) {
      const validRoles = ['operator', 'admin', 'viewer'];
      if (!validRoles.includes(role)) {
        return res.status(400).json({ error: 'Invalid role. Must be operator, admin, or viewer' });
      }
    }

    const result = await pool.query(
      'UPDATE users SET username = $1, email = $2, firstname = $3, lastname = $4' + (role ? ', role = $6' : '') + ' WHERE id = $5 RETURNING id, username, email, firstname, lastname, role, created_at',
      role ? [username, email, firstname, lastname, id, role] : [username, email, firstname, lastname, id]
    );

    if (result.rows.length === 0) {
      return res.status(404).json({ error: 'User not found' });
    }

    res.json(result.rows[0]);
  } catch (error) {
    if (error.code === '23505') { // Unique violation
      if (error.constraint && error.constraint.includes('email')) {
        res.status(409).json({ error: 'Email already exists' });
      } else {
        res.status(409).json({ error: 'Username already exists' });
      }
    } else {
      console.error('Update user error:', error);
      res.status(500).json({ error: 'Internal server error' });
    }
  }
});

// Delete user
app.delete('/users/:id', async (req, res) => {
  try {
    const { id } = req.params;
    
    const result = await pool.query(
      'DELETE FROM users WHERE id = $1 RETURNING id, username, firstname, lastname',
      [id]
    );

    if (result.rows.length === 0) {
      return res.status(404).json({ error: 'User not found' });
    }

    res.json({ message: 'User deleted successfully', user: result.rows[0] });
  } catch (error) {
    console.error('Delete user error:', error);
    res.status(500).json({ error: 'Internal server error' });
  }
});

// Revoke all tokens for a user (increment token_version)
app.post('/users/:id/revoke-tokens', verifyToken, async (req, res) => {
  try {
    const { id } = req.params;
    const targetUserId = parseInt(id);

    // Check permissions: admins can revoke any user's tokens, users can only revoke their own
    if (req.user.role !== 'admin' && req.user.id !== targetUserId) {
      return res.status(403).json({ error: 'You can only revoke your own tokens' });
    }

    const result = await pool.query(
      'UPDATE users SET token_version = token_version + 1 WHERE id = $1 RETURNING id, username, token_version',
      [targetUserId]
    );

    if (result.rows.length === 0) {
      return res.status(404).json({ error: 'User not found' });
    }

    res.json({ 
      message: 'All tokens revoked successfully', 
      user: result.rows[0] 
    });
  } catch (error) {
    console.error('Revoke tokens error:', error);
    res.status(500).json({ error: 'Internal server error' });
  }
});

// Get user token version (for auth service validation)
app.get('/users/:id/token-version', async (req, res) => {
  try {
    const { id } = req.params;

    const result = await pool.query(
      'SELECT id, token_version FROM users WHERE id = $1',
      [id]
    );

    if (result.rows.length === 0) {
      return res.status(404).json({ error: 'User not found' });
    }

    res.json(result.rows[0]);
  } catch (error) {
    console.error('Get token version error:', error);
    res.status(500).json({ error: 'Internal server error' });
  }
});

// Start server
app.listen(port, async () => {
  console.log(`User service running on port ${port}`);
  await initDatabase();
});

// Graceful shutdown
process.on('SIGTERM', () => {
  console.log('SIGTERM received, shutting down gracefully');
  pool.end();
  process.exit(0);
});