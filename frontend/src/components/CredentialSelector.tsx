import React, { useState, useEffect } from 'react';
import { credentialApi } from '../services/api';
import { Credential } from '../types';
import { Key, User, Lock } from 'lucide-react';

interface CredentialSelectorProps {
  value: string;
  onChange: (value: string) => void;
  fieldType: 'username' | 'password' | 'credential';
  placeholder?: string;
}

const CredentialSelector: React.FC<CredentialSelectorProps> = ({
  value,
  onChange,
  fieldType,
  placeholder
}) => {
  const [credentials, setCredentials] = useState<Credential[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [showDropdown, setShowDropdown] = useState(false);

  useEffect(() => {
    fetchCredentials();
  }, []);

  const fetchCredentials = async () => {
    try {
      setLoading(true);
      const response = await credentialApi.list(0, 1000); // Get all credentials
      setCredentials(response.credentials || []);
      setError(null);
    } catch (err) {
      console.error('Failed to fetch credentials:', err);
      setError('Failed to load credentials');
    } finally {
      setLoading(false);
    }
  };

  const getFieldIcon = () => {
    switch (fieldType) {
      case 'username': return <User size={14} />;
      case 'password': return <Lock size={14} />;
      default: return <Key size={14} />;
    }
  };

  const getPlaceholderText = () => {
    if (placeholder) return placeholder;
    switch (fieldType) {
      case 'username': return 'Select credential or enter username';
      case 'password': return 'Select credential or enter password';
      default: return 'Select credential';
    }
  };

  const handleCredentialSelect = (credential: Credential) => {
    switch (fieldType) {
      case 'username':
        onChange(credential.username || `{{credential:${credential.name}:username}}`);
        break;
      case 'password':
        onChange(`{{credential:${credential.name}:password}}`);
        break;
      default:
        onChange(`{{credential:${credential.name}}}`);
        break;
    }
    setShowDropdown(false);
  };

  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    onChange(e.target.value);
  };

  const handleInputFocus = () => {
    if (!loading && credentials.length > 0) {
      setShowDropdown(true);
    }
  };

  const handleInputBlur = () => {
    // Delay hiding dropdown to allow for clicks
    setTimeout(() => setShowDropdown(false), 200);
  };

  if (loading) {
    return (
      <div style={{ position: 'relative' }}>
        <input
          type={fieldType === 'password' ? 'password' : 'text'}
          value={value}
          onChange={handleInputChange}
          placeholder="Loading credentials..."
          disabled
          style={{
            width: '100%',
            padding: '8px 35px 8px 8px',
            border: '1px solid #ddd',
            borderRadius: '4px',
            fontSize: '14px',
            backgroundColor: '#f5f5f5'
          }}
        />
        <div style={{
          position: 'absolute',
          right: '10px',
          top: '50%',
          transform: 'translateY(-50%)',
          color: '#666'
        }}>
          {getFieldIcon()}
        </div>
      </div>
    );
  }

  return (
    <div style={{ position: 'relative' }}>
      <input
        type={fieldType === 'password' ? 'password' : 'text'}
        value={value}
        onChange={handleInputChange}
        onFocus={handleInputFocus}
        onBlur={handleInputBlur}
        placeholder={getPlaceholderText()}
        style={{
          width: '100%',
          padding: '8px 35px 8px 8px',
          border: '1px solid #ddd',
          borderRadius: '4px',
          fontSize: '14px'
        }}
      />
      
      <div style={{
        position: 'absolute',
        right: '10px',
        top: '50%',
        transform: 'translateY(-50%)',
        color: '#666',
        cursor: 'pointer'
      }}
      onClick={() => setShowDropdown(!showDropdown)}
      >
        {getFieldIcon()}
      </div>

      {showDropdown && credentials.length > 0 && (
        <div style={{
          position: 'absolute',
          top: '100%',
          left: 0,
          right: 0,
          backgroundColor: 'white',
          border: '1px solid #ddd',
          borderTop: 'none',
          borderRadius: '0 0 4px 4px',
          maxHeight: '200px',
          overflowY: 'auto',
          zIndex: 1000,
          boxShadow: '0 2px 8px rgba(0,0,0,0.1)'
        }}>
          <div style={{
            padding: '8px 12px',
            fontSize: '12px',
            color: '#666',
            backgroundColor: '#f8f9fa',
            borderBottom: '1px solid #eee'
          }}>
            Available Credentials
          </div>
          
          {credentials.map((credential) => (
            <div
              key={credential.id}
              onClick={() => handleCredentialSelect(credential)}
              style={{
                padding: '8px 12px',
                cursor: 'pointer',
                borderBottom: '1px solid #f0f0f0',
                fontSize: '13px',
                display: 'flex',
                alignItems: 'center',
                gap: '8px'
              }}
              onMouseEnter={(e) => {
                e.currentTarget.style.backgroundColor = '#f8f9fa';
              }}
              onMouseLeave={(e) => {
                e.currentTarget.style.backgroundColor = 'white';
              }}
            >
              <div style={{
                width: '20px',
                height: '20px',
                borderRadius: '3px',
                backgroundColor: credential.credential_type === 'password' ? '#e3f2fd' : 
                                credential.credential_type === 'key' ? '#f3e5f5' : '#e8f5e8',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                color: credential.credential_type === 'password' ? '#1976d2' : 
                       credential.credential_type === 'key' ? '#7b1fa2' : '#388e3c'
              }}>
                {credential.credential_type === 'password' ? <Lock size={12} /> :
                 credential.credential_type === 'key' ? <Key size={12} /> : <Key size={12} />}
              </div>
              
              <div style={{ flex: 1 }}>
                <div style={{ fontWeight: '500' }}>{credential.name}</div>
                {credential.username && (
                  <div style={{ fontSize: '11px', color: '#666' }}>
                    {credential.username}{credential.domain ? `@${credential.domain}` : ''}
                  </div>
                )}
              </div>
              
              <div style={{ fontSize: '11px', color: '#999' }}>
                {credential.credential_type}
              </div>
            </div>
          ))}
        </div>
      )}

      {error && (
        <div style={{
          fontSize: '11px',
          color: '#dc2626',
          marginTop: '4px'
        }}>
          {error}
        </div>
      )}
    </div>
  );
};

export default CredentialSelector;