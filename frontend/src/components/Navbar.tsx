import React from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { authApi } from '../services/api';
import { useAuth } from '../contexts/AuthContext';

const Navbar: React.FC = () => {
  const navigate = useNavigate();
  const { logout } = useAuth();

  const handleLogout = async () => {
    try {
      await authApi.logout();
      logout(); // Clear AuthContext
      navigate('/login');
    } catch (error) {
      console.error('Logout error:', error);
      // Still clear context and navigate to login even if logout call fails
      logout();
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
          <li><Link to="/user-management">Users</Link></li>
          <li><Link to="/credential-management">Credentials</Link></li>
          <li><Link to="/targets-management">Targets</Link></li>
          <li><Link to="/target-groups">Target Groups</Link></li>
          <li><Link to="/discovery">Discovery</Link></li>
          <li><Link to="/job-management">Jobs</Link></li>
          <li><Link to="/schedule-management">Schedules</Link></li>
          <li><Link to="/advanced-scheduler">Advanced Scheduler</Link></li>
          <li><Link to="/job-runs">Job Runs</Link></li>
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