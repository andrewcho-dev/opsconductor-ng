import React, { useState, useRef, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { Eye, EyeOff } from 'lucide-react';
import { authApi, setSessionToken } from '../services/api';
import { useAuth } from '../contexts/AuthContext';

const Login: React.FC = () => {
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [showPassword, setShowPassword] = useState(false);
  const navigate = useNavigate();
  const { login } = useAuth();
  
  // Refs for input fields
  const usernameRef = useRef<HTMLInputElement>(null);
  const passwordRef = useRef<HTMLInputElement>(null);

  // Auto-focus username field on component mount
  useEffect(() => {
    if (usernameRef.current) {
      usernameRef.current.focus();
    }
  }, []);

  // Handle clicks outside form to maintain focus on input fields
  const handleContainerClick = (e: React.MouseEvent) => {
    const target = e.target as HTMLElement;
    
    // If click is outside the form inputs and not on the show/hide password button
    if (!target.closest('input') && !target.closest('button[type="button"]')) {
      // Focus on username if it's empty, otherwise focus on password
      if (!username && usernameRef.current) {
        usernameRef.current.focus();
      } else if (passwordRef.current) {
        passwordRef.current.focus();
      }
    }
  };

  // Handle keyboard navigation
  const handleUsernameKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && username && passwordRef.current) {
      e.preventDefault();
      passwordRef.current.focus();
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError('');

    try {
      const response = await authApi.login({ username, password });
      setSessionToken(response.access_token);
      
      // Store refresh token for logout
      if (response.refresh_token) {
        localStorage.setItem('refresh_token', response.refresh_token);
      }
      
      // Update the AuthContext with session token
      login(response.access_token, response.user);
      
      navigate('/');
    } catch (error: any) {
      setError(error.response?.data?.detail || error.response?.data?.error_description || 'Login failed');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div 
      style={{
        minHeight: '100vh',
        backgroundImage: 'url(/faint_background.png)',
        backgroundSize: 'cover',
        backgroundPosition: '70% center',
        backgroundRepeat: 'no-repeat',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        padding: '20px',
        position: 'relative'
      }}
      onClick={handleContainerClick}
    >
      {/* Subtle overlay to ensure modal visibility */}
      <div style={{
        position: 'absolute',
        top: 0,
        left: 0,
        right: 0,
        bottom: 0,
        backgroundColor: 'rgba(176, 190, 197, 0.3)',
        backdropFilter: 'blur(1px)'
      }} />
      
      <div className="container" style={{ 
        maxWidth: '400px', 
        position: 'relative', 
        zIndex: 1
      }}>
        <div className="card" style={{
          backgroundColor: 'rgba(255, 255, 255, 0.95)',
          backdropFilter: 'blur(10px)',
          boxShadow: '0 8px 32px rgba(0, 0, 0, 0.1)',
          border: '1px solid rgba(255, 255, 255, 0.2)'
        }}>
        <div style={{ textAlign: 'center', marginBottom: '-20px' }}>
          <img 
            src="/OpsConductor dark on light 480.svg" 
            alt="OpsConductor" 
            style={{ 
              height: '300px', 
              width: 'auto',
              maxWidth: '100%',
              imageRendering: 'crisp-edges',
              shapeRendering: 'geometricPrecision'
            }}
          />
        </div>
        
        {error && (
          <div style={{ 
            backgroundColor: '#f8d7da', 
            color: '#721c24', 
            padding: '10px', 
            borderRadius: '4px', 
            marginBottom: '20px' 
          }}>
            {error}
          </div>
        )}

        <form onSubmit={handleSubmit} style={{ marginTop: '0px' }}>
          <div className="form-group" style={{ marginTop: '0px' }}>
            <label>Username:</label>
            <input
              ref={usernameRef}
              type="text"
              value={username}
              onChange={(e) => setUsername(e.target.value)}
              onKeyDown={handleUsernameKeyDown}
              required
              disabled={loading}
              style={{
                height: '45px',
                padding: '12px 15px',
                fontSize: '16px'
              }}
            />
          </div>

          <div className="form-group">
            <label>Password:</label>
            <div style={{ position: 'relative' }}>
              <input
                ref={passwordRef}
                type={showPassword ? "text" : "password"}
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                required
                disabled={loading}
                style={{
                  height: '45px',
                  padding: '12px 45px 12px 15px',
                  fontSize: '16px',
                  width: '100%'
                }}
              />
              <button
                type="button"
                onClick={() => setShowPassword(!showPassword)}
                disabled={loading}
                style={{
                  position: 'absolute',
                  right: '12px',
                  top: '50%',
                  transform: 'translateY(-50%)',
                  background: 'none',
                  border: 'none',
                  cursor: 'pointer',
                  fontSize: '18px',
                  color: '#666',
                  padding: '0',
                  width: '24px',
                  height: '24px',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center'
                }}
                title={showPassword ? "Hide password" : "Show password"}
              >
                {showPassword ? <EyeOff size={18} /> : <Eye size={18} />}
              </button>
            </div>
          </div>

          <button 
            type="submit" 
            className="btn btn-primary" 
            style={{ 
              width: '100%',
              height: '45px',
              fontSize: '16px'
            }}
            disabled={loading}
          >
            {loading ? 'Signing In...' : 'Sign In'}
          </button>
        </form>

        </div>
      </div>
    </div>
  );
};

export default Login;