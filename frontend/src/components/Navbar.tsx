import React, { useState, useRef, useEffect } from 'react';
import { Link, useNavigate, useLocation } from 'react-router-dom';
import { authApi } from '../services/api';
import { useAuth } from '../contexts/AuthContext';
import { hasPermission, PERMISSIONS } from '../utils/permissions';
import { 
  Target, 
  MessageSquare,
  LogOut,
  Menu,
  ChevronRight,
  Calendar,
  Settings,
  Search
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

              <Link 
                to="/selector" 
                className={`nav-menu-item ${location.pathname === '/selector' || location.pathname.startsWith('/selector/') ? 'active' : ''}`} 
                onClick={closeMenu}
              >
                <span className="nav-icon"><Search size={16} /></span>
                Tool Selector
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
              
              {/* Settings Section */}
              <div className="nav-section-header">System</div>
              
              <Link 
                to="/settings" 
                className={`nav-menu-item ${location.pathname === '/settings' || location.pathname.startsWith('/settings/') ? 'active' : ''}`} 
                onClick={closeMenu}
              >
                <span className="nav-icon"><Settings size={16} /></span>
                Settings
              </Link>

              <div className="nav-divider"></div>
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