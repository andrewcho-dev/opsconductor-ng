const express = require('express');
const jwt = require('jsonwebtoken');
const cors = require('cors');

const app = express();
const port = process.env.PORT || 3002;

const JWT_SECRET = process.env.JWT_SECRET || 'your-super-secret-jwt-key';

// Middleware
app.use(cors());
app.use(express.json());

// Built-in users for demo (matches database)
const DEMO_USERS = {
  'admin': {
    id: 1,
    username: 'admin', 
    email: 'admin@opsconductor.local',
    firstname: 'Admin',
    lastname: 'User',
    password: 'admin123',
    role: 'admin',
    token_version: 0
  },
  'operator': {
    id: 2,
    username: 'operator',
    email: 'operator@opsconductor.local', 
    firstname: 'Operator',
    lastname: 'User',
    password: 'operator123',
    role: 'operator',
    token_version: 0
  },
  'viewer': {
    id: 3,
    username: 'viewer',
    email: 'viewer@opsconductor.local',
    firstname: 'Viewer', 
    lastname: 'User',
    password: 'viewer123',
    role: 'viewer',
    token_version: 0
  }
};

// Routes
app.get('/health', (req, res) => {
  res.json({ status: 'healthy', service: 'auth-service' });
});

app.post('/login', async (req, res) => {
  try {
    const { username, password } = req.body;
    
    if (!username || !password) {
      return res.status(400).json({ error: 'Username and password are required' });
    }

    // Check demo users first
    const user = DEMO_USERS[username];
    if (!user || user.password !== password) {
      return res.status(401).json({ error: 'Invalid credentials' });
    }

    // Generate tokens
    const accessTokenPayload = {
      userId: user.id,
      username: user.username,
      email: user.email,
      role: user.role,
      tokenVersion: user.token_version
    };

    const accessToken = jwt.sign(accessTokenPayload, JWT_SECRET, { expiresIn: '15m' });
    const refreshToken = jwt.sign({
      userId: user.id,
      tokenVersion: user.token_version,
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

app.post('/verify', (req, res) => {
  try {
    const authHeader = req.headers['authorization'];
    const token = authHeader && authHeader.split(' ')[1];

    if (!token) {
      return res.status(401).json({ error: 'Access token required' });
    }

    jwt.verify(token, JWT_SECRET, (err, decoded) => {
      if (err) {
        return res.status(403).json({ error: 'Invalid or expired token' });
      }

      const user = DEMO_USERS[decoded.username];
      if (!user) {
        return res.status(403).json({ error: 'User not found' });
      }

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
    });
  } catch (error) {
    console.error('Verify error:', error);
    res.status(500).json({ error: 'Internal server error' });
  }
});

app.listen(port, () => {
  console.log(`Simple auth service running on port ${port}`);
});