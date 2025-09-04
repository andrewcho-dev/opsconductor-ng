import React, { useState, useRef, useEffect } from 'react';
import { Link, useNavigate, useLocation } from 'react-router-dom';
import { authApi } from '../services/api';
import { useAuth } from '../contexts/AuthContext';
import { 
  BarChart3, 
  Users, 
  Shield, 
  Target, 
  Search, 
  Settings, 
  Calendar, 
  Play, 
  Bell, 
  LogOut,
  Menu,
  ChevronRight,
  Code,
  Mail,
  ClipboardList
} from 'lucide-react';

const Navbar: React.FC = () => {
  const navigate = useNavigate();
  const location = useLocation();
  const { logout, user } = useAuth();
  const [isMenuOpen, setIsMenuOpen] = useState(false);
  const menuRef = useRef<HTMLDivElement>(null);

  const handleLogout = async () => {
    try {
      await authApi.logout();
      logout();
      navigate('/login');
    } catch (error) {
      console.error('Logout error:', error);
      logout();
      navigate('/login');
    }
  };

  const isActive = (path: string) => {
    return location.pathname === path || location.pathname.startsWith(path + '/');
  };

  const toggleMenu = () => {
    setIsMenuOpen(!isMenuOpen);
  };

  const closeMenu = () => {
    setIsMenuOpen(false);
  };

  // Close menu when clicking outside
  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (menuRef.current && !menuRef.current.contains(event.target as Node)) {
        setIsMenuOpen(false);
      }
    };

    if (isMenuOpen) {
      document.addEventListener('mousedown', handleClickOutside);
    }

    return () => {
      document.removeEventListener('mousedown', handleClickOutside);
    };
  }, [isMenuOpen]);

  return (
    <nav className="nodered-nav">
      <div className="nav-header">
        <Link to="/" className="nav-brand" onClick={closeMenu}>OpsConductor</Link>
        <div className="nav-menu-container" ref={menuRef}>
          <button className="nav-hamburger" onClick={toggleMenu}>
            <Menu size={20} />
          </button>
          {isMenuOpen && (
            <div className="nav-dropdown">
              <Link 
                to="/" 
                className={`nav-menu-item ${isActive('/') && location.pathname === '/' ? 'active' : ''}`} 
                onClick={closeMenu}
              >
                <span className="nav-icon"><BarChart3 size={16} /></span>
                Dashboard
              </Link>
              <Link 
                to="/user-management" 
                className={`nav-menu-item ${isActive('/user-management') ? 'active' : ''}`} 
                onClick={closeMenu}
              >
                <span className="nav-icon"><Users size={16} /></span>
                Users
              </Link>
              <Link 
                to="/credential-management" 
                className={`nav-menu-item ${isActive('/credential-management') ? 'active' : ''}`} 
                onClick={closeMenu}
              >
                <span className="nav-icon"><Shield size={16} /></span>
                Credentials
              </Link>
              <Link 
                to="/targets-management" 
                className={`nav-menu-item ${isActive('/targets-management') ? 'active' : ''}`} 
                onClick={closeMenu}
              >
                <span className="nav-icon"><Target size={16} /></span>
                Targets
              </Link>
              <Link 
                to="/discovery" 
                className={`nav-menu-item ${isActive('/discovery') ? 'active' : ''}`} 
                onClick={closeMenu}
              >
                <span className="nav-icon"><Search size={16} /></span>
                Discovery
              </Link>
              <Link 
                to="/job-management" 
                className={`nav-menu-item ${isActive('/job-management') ? 'active' : ''}`} 
                onClick={closeMenu}
              >
                <span className="nav-icon"><Settings size={16} /></span>
                Jobs
              </Link>
              <Link 
                to="/schedule-management" 
                className={`nav-menu-item ${isActive('/schedule-management') ? 'active' : ''}`} 
                onClick={closeMenu}
              >
                <span className="nav-icon"><Calendar size={16} /></span>
                Schedules
              </Link>
              <Link 
                to="/job-runs" 
                className={`nav-menu-item ${isActive('/job-runs') ? 'active' : ''}`} 
                onClick={closeMenu}
              >
                <span className="nav-icon"><Play size={16} /></span>
                Job Runs
              </Link>
              <div className="nav-divider"></div>
              <div className="nav-menu-item-group">
                <div className="nav-menu-item">
                  <span className="nav-icon"><Settings size={16} /></span>
                  Settings
                  <span className="nav-chevron">
                    <ChevronRight size={14} />
                  </span>
                </div>
                <div className="nav-submenu">
                  <Link 
                    to="/settings/step-library" 
                    className={`nav-submenu-item ${location.pathname === '/settings/step-library' ? 'active' : ''} ${user?.role !== 'admin' ? 'disabled' : ''}`} 
                    onClick={closeMenu}
                  >
                    <span className="nav-icon"><Code size={14} /></span>
                    Step Library
                    {user?.role !== 'admin' && <span className="admin-badge">Admin</span>}
                  </Link>
                  <Link 
                    to="/settings/smtp" 
                    className={`nav-submenu-item ${location.pathname === '/settings/smtp' ? 'active' : ''} ${user?.role !== 'admin' ? 'disabled' : ''}`} 
                    onClick={closeMenu}
                  >
                    <span className="nav-icon"><Mail size={14} /></span>
                    SMTP Config
                    {user?.role !== 'admin' && <span className="admin-badge">Admin</span>}
                  </Link>
                  <Link 
                    to="/settings/notification-preferences" 
                    className={`nav-submenu-item ${location.pathname === '/settings/notification-preferences' ? 'active' : ''}`} 
                    onClick={closeMenu}
                  >
                    <span className="nav-icon"><Bell size={14} /></span>
                    Notifications
                  </Link>
                  <Link 
                    to="/settings/notification-history" 
                    className={`nav-submenu-item ${location.pathname === '/settings/notification-history' ? 'active' : ''} ${user?.role !== 'admin' ? 'disabled' : ''}`} 
                    onClick={closeMenu}
                  >
                    <span className="nav-icon"><ClipboardList size={14} /></span>
                    Notification History
                    {user?.role !== 'admin' && <span className="admin-badge">Admin</span>}
                  </Link>
                </div>
              </div>
              <button onClick={handleLogout} className="nav-menu-item logout">
                <span className="nav-icon"><LogOut size={16} /></span>
                Logout
              </button>
            </div>
          )}
        </div>
      </div>
    </nav>
  );
};

export default Navbar;