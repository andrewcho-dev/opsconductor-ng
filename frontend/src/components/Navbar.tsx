import React, { useState, useRef, useEffect } from 'react';
import { Link, useNavigate, useLocation } from 'react-router-dom';
import { authApi } from '../services/api';
import { useAuth } from '../contexts/AuthContext';
import { hasPermission, PERMISSIONS } from '../utils/permissions';
import { 
  Users, 
  Target, 
  Settings, 
  Play, 
  MessageSquare,
  LogOut,
  Menu,
  ChevronRight,
  Mail,
  History,
  GitBranch,
  Server,
  Shield
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
                <span className="nav-icon"><MessageSquare size={16} /></span>
                AI Assistant
              </Link>

              <div className="nav-divider"></div>
              
              {/* Operations Section */}
              <div className="nav-section-header">Operations</div>
              
              <div className="nav-menu-item-group">
                <div className="nav-menu-item">
                  <span className="nav-icon"><GitBranch size={16} /></span>
                  Workflows
                  <span className="nav-chevron">
                    <ChevronRight size={14} />
                  </span>
                </div>
                <div className="nav-submenu">
                  <Link 
                    to="/workflows" 
                    className={`nav-submenu-item ${location.pathname === '/workflows' || location.pathname.startsWith('/workflows/') ? 'active' : ''}`} 
                    onClick={closeMenu}
                  >
                    <span className="nav-icon"><GitBranch size={14} /></span>
                    Flow Management
                  </Link>
                  <Link 
                    to="/workflows/runs" 
                    className={`nav-submenu-item ${location.pathname === '/workflows/runs' || location.pathname.startsWith('/workflows/runs/') ? 'active' : ''}`} 
                    onClick={closeMenu}
                  >
                    <span className="nav-icon"><Play size={14} /></span>
                    Flow Runs
                  </Link>
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
                    Legacy Job Runs
                  </Link>
                </div>
              </div>

              <div className="nav-divider"></div>
              
              {/* Infrastructure Section */}
              <div className="nav-section-header">Infrastructure</div>
              
              <Link 
                to="/infrastructure" 
                className={`nav-menu-item ${isActive('/infrastructure') ? 'active' : ''}`} 
                onClick={closeMenu}
              >
                <span className="nav-icon"><Server size={16} /></span>
                Infrastructure Monitoring
              </Link>



              <div className="nav-divider"></div>
              
              {/* Identity & Access Section */}
              <div className="nav-section-header">Identity & Access</div>
              
              <div className="nav-menu-item-group">
                <div className="nav-menu-item">
                  <span className="nav-icon"><Users size={16} /></span>
                  Users & Roles
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
                      <span className="nav-icon"><Shield size={14} /></span>
                      Role Management
                    </Link>
                  )}
                </div>
              </div>
              <div className="nav-divider"></div>
              
              {/* Settings Section */}
              <div className="nav-section-header">Settings</div>
              
              <div className="nav-menu-item-group">
                <div className="nav-menu-item">
                  <span className="nav-icon"><Settings size={16} /></span>
                  System
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