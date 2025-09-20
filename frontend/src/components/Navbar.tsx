import React, { useState, useRef, useEffect } from 'react';
import { Link, useNavigate, useLocation } from 'react-router-dom';
import { authApi } from '../services/api';
import { useAuth } from '../contexts/AuthContext';
import { hasPermission, PERMISSIONS } from '../utils/permissions';
import { 
  BarChart3, 
  Users, 
  Target, 
  Search, 
  Settings, 
  Calendar, 
  Play, 
  MessageSquare,
  LogOut,
  Menu,
  ChevronRight,
  Code,
  Mail,

  History,

  List,
  Activity
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
        <Link to="/" className="nav-brand" onClick={closeMenu}>
          <img 
            src="/OpsConductor hat light on dark.svg" 
            alt="OpsConductor" 
            className="nav-logo"
          />
          <span className="nav-brand-text">OpsConductor</span>
        </Link>
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
                to="/ai-chat" 
                className={`nav-menu-item ${isActive('/ai-chat') ? 'active' : ''}`} 
                onClick={closeMenu}
              >
                <span className="nav-icon"><MessageSquare size={16} /></span>
                AI Assistant
              </Link>

              <div className="nav-menu-item-group">
                <div className="nav-menu-item">
                  <span className="nav-icon"><Users size={16} /></span>
                  Users
                  <span className="nav-chevron">
                    <ChevronRight size={14} />
                  </span>
                </div>
                <div className="nav-submenu">
                  <Link 
                    to="/users" 
                    className={`nav-submenu-item ${location.pathname === '/users' || location.pathname.startsWith('/users/') ? 'active' : ''}`} 
                    onClick={closeMenu}
                  >
                    <span className="nav-icon"><Users size={14} /></span>
                    User Management
                  </Link>
                  {hasPermission(user, PERMISSIONS.ROLES_READ) && (
                    <Link 
                      to="/roles" 
                      className={`nav-submenu-item ${location.pathname === '/roles' || location.pathname.startsWith('/roles/') ? 'active' : ''}`} 
                      onClick={closeMenu}
                    >
                      <span className="nav-icon"><Settings size={14} /></span>
                      Role Management
                    </Link>
                  )}
                </div>
              </div>

              <div className="nav-menu-item-group">
                <div className="nav-menu-item">
                  <span className="nav-icon"><Target size={16} /></span>
                  Assets
                  <span className="nav-chevron">
                    <ChevronRight size={14} />
                  </span>
                </div>
                <div className="nav-submenu">
                  <Link 
                    to="/assets" 
                    className={`nav-submenu-item ${location.pathname === '/assets' || location.pathname.startsWith('/assets/') ? 'active' : ''}`} 
                    onClick={closeMenu}
                  >
                    <span className="nav-icon"><Target size={14} /></span>
                    Asset Management
                  </Link>

                </div>
              </div>
              <div className="nav-menu-item-group">
                <div className="nav-menu-item">
                  <span className="nav-icon"><Settings size={16} /></span>
                  Jobs
                  <span className="nav-chevron">
                    <ChevronRight size={14} />
                  </span>
                </div>
                <div className="nav-submenu">
                  <Link 
                    to="/job-management" 
                    className={`nav-submenu-item ${location.pathname === '/job-management' ? 'active' : ''}`} 
                    onClick={closeMenu}
                  >
                    <span className="nav-icon"><List size={14} /></span>
                    Manage Jobs
                  </Link>
                  <Link 
                    to="/job-monitoring" 
                    className={`nav-submenu-item ${location.pathname === '/job-monitoring' ? 'active' : ''}`} 
                    onClick={closeMenu}
                  >
                    <span className="nav-icon"><Activity size={14} /></span>
                    Job Monitoring
                  </Link>

                </div>
              </div>

              <div className="nav-menu-item-group">
                <div className="nav-menu-item">
                  <span className="nav-icon"><History size={16} /></span>
                  History
                  <span className="nav-chevron">
                    <ChevronRight size={14} />
                  </span>
                </div>
                <div className="nav-submenu">
                  <Link 
                    to="/history/job-runs" 
                    className={`nav-submenu-item ${location.pathname === '/history/job-runs' || location.pathname.startsWith('/history/job-runs/') ? 'active' : ''}`} 
                    onClick={closeMenu}
                  >
                    <span className="nav-icon"><Play size={14} /></span>
                    Job Runs
                  </Link>


                </div>
              </div>
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
                    to="/settings/smtp" 
                    className={`nav-submenu-item ${location.pathname === '/settings/smtp' ? 'active' : ''} ${!hasPermission(user, PERMISSIONS.SMTP_CONFIG) ? 'disabled' : ''}`} 
                    onClick={closeMenu}
                  >
                    <span className="nav-icon"><Mail size={14} /></span>
                    System Settings
                    {!hasPermission(user, PERMISSIONS.SMTP_CONFIG) && <span className="admin-badge">Admin</span>}
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