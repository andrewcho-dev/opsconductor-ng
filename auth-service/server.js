const express = require('express');
const { Pool } = require('pg');
const crypto = require('crypto');
const jwt = require('jsonwebtoken');
const axios = require('axios');
const cors = require('cors');

const app = express();
const port = process.env.PORT || 3002;

// Database connection
const pool = new Pool({
  host: process.env.DB_HOST || 'postgres',
  port: process.env.DB_PORT || 5432,
  database: process.env.DB_NAME || 'opsconductor',
  user: process.env.DB_USER || 'opsconductor',
  password: process.env.DB_PASS || 'opsconductor123',
  max: 20,
  idleTimeoutMillis: 30000,
  connectionTimeoutMillis: 2000,
});

// Configuration
const JWT_SECRET = process.env.JWT_SECRET || 'your-super-secret-jwt-key';
const REFRESH_SECRET = process.env.REFRESH_SECRET || 'your-super-secret-refresh-key';
const USER_SERVICE_URL = process.env.USER_SERVICE_URL || 'http://user-service:3001';

// Token configuration
const ACCESS_TOKEN_EXPIRY = '15m';
const REFRESH_TOKEN_EXPIRY = '7d';

// Middleware
app.use(cors());
app.use(express.json());

// Simple password verification - checking if password matches expected passwords
function verifyPassword(inputPassword, storedHash, username) {
  // For the demo users, use simple password verification
  const userPasswords = {
    'admin': 'admin123',
    'operator': 'operator123', 
    'viewer': 'viewer123'
  };
  
  return userPasswords[username] === inputPassword;
}

// Initialize database
async function initDatabase() {
  try {
    await pool.query(`
      CREATE TABLE IF NOT EXISTS auth_sessions (
        id SERIAL PRIMARY KEY,
        user_id INTEGER NOT NULL,
        token_hash VARCHAR(255) NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        expires_at TIMESTAMP NOT NULL
      )
    `);

    await pool.query(`
      CREATE TABLE IF NOT EXISTS refresh_tokens (
        id SERIAL PRIMARY KEY,
        user_id INTEGER NOT NULL,
        token_hash VARCHAR(255) UNIQUE NOT NULL,
        token_version INTEGER NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        expires_at TIMESTAMP NOT NULL,
        is_revoked BOOLEAN DEFAULT FALSE
      )
    `);

    console.log('Auth database initialized successfully');
  } catch (error) {
    console.error('Auth database initialization error:', error);
  }
}

// Middleware to verify JWT token
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

    if (decoded.tokenVersion !== undefined) {
      try {
        const tokenVersionResponse = await axios.get(`${USER_SERVICE_URL}/users/${decoded.userId}/token-version`);
        const currentTokenVersion = tokenVersionResponse.data.token_version;

        if (decoded.tokenVersion !== currentTokenVersion) {
          return res.status(403).json({ error: 'Token has been revoked' });
        }
      } catch (error) {
        console.error('Token version validation error:', error);
        return res.status(500).json({ error: 'Token validation failed' });
      }
    }

    req.user = decoded;
    next();
  });
}

// Helper function to generate tokens
async function generateTokens(user) {
  const accessTokenPayload = {
    userId: user.id,
    username: user.username,
    email: user.email,
    role: user.role,
    tokenVersion: user.token_version || 0
  };

  const refreshTokenPayload = {
    userId: user.id,
    tokenVersion: user.token_version || 0,
    type: 'refresh'
  };

  const accessToken = jwt.sign(accessTokenPayload, JWT_SECRET, { expiresIn: ACCESS_TOKEN_EXPIRY });
  const refreshToken = jwt.sign(refreshTokenPayload, REFRESH_SECRET, { expiresIn: REFRESH_TOKEN_EXPIRY });

  return { accessToken, refreshToken };
}

// Routes

// Health check
app.get('/health', (req, res) => {
  res.json({ status: 'healthy', service: 'auth-service' });
});

// Login
app.post('/login', async (req, res) => {
  try {
    const { username, password } = req.body;
    
    if (!username || !password) {
      return res.status(400).json({ error: 'Username and password are required' });
    }

    // Get user from user service
    const userResponse = await axios.get(`${USER_SERVICE_URL}/users/${username}`);
    const user = userResponse.data;

    // Verify password
    if (!verifyPassword(password, user.password, username)) {
      return res.status(401).json({ error: 'Invalid credentials' });
    }

    // Generate access and refresh tokens
    const { accessToken, refreshToken } = await generateTokens(user);

    // Store refresh token in database
    const refreshTokenHash = crypto.createHash('sha256').update(refreshToken).digest('hex');
    const refreshExpiresAt = new Date(Date.now() + 7 * 24 * 60 * 60 * 1000);

    await pool.query(
      'INSERT INTO refresh_tokens (user_id, token_hash, token_version, expires_at) VALUES ($1, $2, $3, $4)',
      [user.id, refreshTokenHash, user.token_version || 0, refreshExpiresAt]
    );

    // Store access token session
    const accessTokenHash = crypto.createHash('sha256').update(accessToken).digest('hex');
    const accessExpiresAt = new Date(Date.now() + 15 * 60 * 1000);

    await pool.query(
      'INSERT INTO auth_sessions (user_id, token_hash, expires_at) VALUES ($1, $2, $3)',
      [user.id, accessTokenHash, accessExpiresAt]
    );

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
    if (error.response && error.response.status === 404) {
      res.status(401).json({ error: 'Invalid credentials' });
    } else {
      console.error('Login error:', error);
      res.status(500).json({ error: 'Internal server error' });
    }
  }
});

// Verify token
app.post('/verify', verifyToken, async (req, res) => {
  try {
    const userResponse = await axios.get(`${USER_SERVICE_URL}/users/id/${req.user.userId}`);
    const user = userResponse.data;

    res.json({
      valid: true,
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
    console.error('Token verification error:', error);
    res.status(500).json({ error: 'Internal server error' });
  }
});

// Refresh token endpoint
app.post('/refresh', async (req, res) => {
  try {
    const { refreshToken } = req.body;

    if (!refreshToken) {
      return res.status(401).json({ error: 'Refresh token required' });
    }

    let decoded;
    try {
      decoded = jwt.verify(refreshToken, REFRESH_SECRET);
    } catch (err) {
      return res.status(403).json({ error: 'Invalid or expired refresh token' });
    }

    // Check if refresh token exists in database
    const refreshTokenHash = crypto.createHash('sha256').update(refreshToken).digest('hex');
    const storedTokenResult = await pool.query(
      'SELECT * FROM refresh_tokens WHERE user_id = $1 AND token_hash = $2 AND token_version = $3 AND is_revoked = FALSE AND expires_at > NOW()',
      [decoded.userId, refreshTokenHash, decoded.tokenVersion]
    );

    if (storedTokenResult.rows.length === 0) {
      return res.status(403).json({ error: 'Refresh token not found or revoked' });
    }

    // Get current user data
    const userResponse = await axios.get(`${USER_SERVICE_URL}/users/id/${decoded.userId}`);
    const user = userResponse.data;

    // Check token version
    if (decoded.tokenVersion !== (user.token_version || 0)) {
      await pool.query(
        'UPDATE refresh_tokens SET is_revoked = TRUE WHERE user_id = $1 AND token_version = $2',
        [decoded.userId, decoded.tokenVersion]
      );
      return res.status(403).json({ error: 'Refresh token has been revoked' });
    }

    // Generate new tokens
    const { accessToken, refreshToken: newRefreshToken } = await generateTokens(user);

    // Revoke old refresh token
    await pool.query(
      'UPDATE refresh_tokens SET is_revoked = TRUE WHERE user_id = $1 AND token_version = $2',
      [decoded.userId, decoded.tokenVersion]
    );

    // Store new refresh token
    const newRefreshTokenHash = crypto.createHash('sha256').update(newRefreshToken).digest('hex');
    const refreshExpiresAt = new Date(Date.now() + 7 * 24 * 60 * 60 * 1000);

    await pool.query(
      'INSERT INTO refresh_tokens (user_id, token_hash, token_version, expires_at) VALUES ($1, $2, $3, $4)',
      [user.id, newRefreshTokenHash, user.token_version || 0, refreshExpiresAt]
    );

    res.json({
      accessToken,
      refreshToken: newRefreshToken,
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
    console.error('Refresh token error:', error);
    res.status(500).json({ error: 'Internal server error' });
  }
});

// Logout
app.post('/logout', verifyToken, async (req, res) => {
  try {
    const { refreshToken } = req.body;

    if (refreshToken) {
      try {
        const decoded = jwt.verify(refreshToken, REFRESH_SECRET);
        await pool.query(
          'UPDATE refresh_tokens SET is_revoked = TRUE WHERE user_id = $1 AND token_version = $2',
          [decoded.userId, decoded.tokenVersion]
        );
      } catch (err) {
        console.log('Invalid refresh token during logout:', err.message);
      }
    }

    res.json({ message: 'Logged out successfully' });
  } catch (error) {
    console.error('Logout error:', error);
    res.status(500).json({ error: 'Internal server error' });
  }
});

// Start server
app.listen(port, async () => {
  console.log(`Auth service running on port ${port}`);
  await initDatabase();
});

// Graceful shutdown
process.on('SIGTERM', () => {
  console.log('SIGTERM received, shutting down gracefully');
  pool.end();
  process.exit(0);
});