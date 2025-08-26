const { Pool } = require('pg');

const pool = new Pool({
  user: 'opsconductor',
  host: 'localhost',
  database: 'opsconductor',
  password: 'opsconductor123',
  port: 5432,
});

async function testDatabase() {
  try {
    console.log('Testing database connection...');
    const result = await pool.query('SELECT username, email, role FROM users WHERE username = $1', ['admin']);
    console.log('Query result:', result.rows);
    
    if (result.rows.length > 0) {
      const user = result.rows[0];
      console.log('Admin user found:', user);
    } else {
      console.log('Admin user not found');
    }
  } catch (error) {
    console.error('Database error:', error);
  } finally {
    await pool.end();
  }
}

testDatabase();