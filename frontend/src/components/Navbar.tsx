import React from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { authApi } from '../services/api';

const Navbar: React.FC = () => {
  const navigate = useNavigate();

  const handleLogout = async () => {
    try {
      await authApi.logout();
      navigate('/login');
    } catch (error) {
      console.error('Logout error:', error);
      // Still navigate to login even if logout call fails
      navigate('/login');
    }
  };

  return (
    <nav className="navbar">
      <div className="container" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <div className="nav-brand">
          <Link to="/" style={{ color: 'white', textDecoration: 'none' }}>
            OpsConductor
          </Link>
        </div>
        <ul className="nav-links">
          <li><Link to="/">Dashboard</Link></li>
          <li><Link to="/users">Users</Link></li>
          <li><Link to="/credentials">Credentials</Link></li>
          <li><Link to="/targets">Targets</Link></li>
          <li><Link to="/jobs">Jobs</Link></li>
          <li><Link to="/schedule-management">Schedules</Link></li>
          <li><Link to="/runs">Job Runs</Link></li>
          <li><Link to="/notifications">Notifications</Link></li>
          <li><Link to="/settings">Settings</Link></li>
          <li>
            <button
              onClick={handleLogout}
              className="btn btn-secondary"
              style={{ marginLeft: '20px' }}
            >
              Logout
            </button>
          </li>
        </ul>
      </div>
    </nav>
  );
};

export default Navbar;