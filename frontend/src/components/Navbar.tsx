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
  GitBranch,
  Server,
  Shield,
  Bell,
  FileText,
  Network,
  Calendar,
  Brain
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
              
              <Link 
                to="/schedules" 
                className={`nav-menu-item ${location.pathname === '/schedules' || location.pathname.startsWith('/schedules/') ? 'active' : ''}`} 
                onClick={closeMenu}
              >
                <span className="nav-icon"><Calendar size={16} /></span>
                Schedules
              </Link>

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

              <div className="nav-divider"></div>
              
              {/* Infrastructure Section */}
              <div className="nav-section-header">Infrastructure</div>
              
              <div className="nav-menu-item-group">
                <div className="nav-menu-item">
                  <span className="nav-icon"><Server size={16} /></span>
                  Infrastructure
                  <span className="nav-chevron">
                    <ChevronRight size={14} />
                  </span>
                </div>
                <div className="nav-submenu">
                  <Link 
                    to="/infrastructure" 
                    className={`nav-submenu-item ${isActive('/infrastructure') ? 'active' : ''}`} 
                    onClick={closeMenu}
                  >
                    <span className="nav-icon"><Server size={14} /></span>
                    System Monitoring
                  </Link>
                  <Link 
                    to="/network-analysis" 
                    className={`nav-submenu-item ${isActive('/network-analysis') ? 'active' : ''}`} 
                    onClick={closeMenu}
                  >
                    <span className="nav-icon"><Network size={14} /></span>
                    Network Analysis
                  </Link>
                  <Link 
                    to="/ai-monitoring" 
                    className={`nav-submenu-item ${isActive('/ai-monitoring') ? 'active' : ''}`} 
                    onClick={closeMenu}
                  >
                    <span className="nav-icon"><Brain size={14} /></span>
                    AI Monitoring
                  </Link>
                </div>
              </div>



              <div className="nav-divider"></div>
              
              {/* Communication Section */}
              <div className="nav-section-header">Communication</div>
              
              <div className="nav-menu-item-group">
                <div className="nav-menu-item">
                  <span className="nav-icon"><MessageSquare size={16} /></span>
                  Notifications
                  <span className="nav-chevron">
                    <ChevronRight size={14} />
                  </span>
                </div>
                <div className="nav-submenu">
                  <Link 
                    to="/notifications" 
                    className={`nav-submenu-item ${isActive('/notifications') ? 'active' : ''}`} 
                    onClick={closeMenu}
                  >
                    <span className="nav-icon"><Bell size={14} /></span>
                    Notifications
                  </Link>
                  <Link 
                    to="/templates" 
                    className={`nav-submenu-item ${isActive('/templates') ? 'active' : ''}`} 
                    onClick={closeMenu}
                  >
                    <span className="nav-icon"><FileText size={14} /></span>
                    Templates
                  </Link>
                  <Link 
                    to="/audit-logs" 
                    className={`nav-submenu-item ${isActive('/audit-logs') ? 'active' : ''}`} 
                    onClick={closeMenu}
                  >
                    <span className="nav-icon"><Shield size={14} /></span>
                    Audit Logs
                  </Link>
                </div>
              </div>

              <div className="nav-divider"></div>
              
              {/* Identity & Access Section */}
              <div className="nav-section-header">Identity & Access</div>

              
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