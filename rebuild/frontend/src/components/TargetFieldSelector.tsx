import React, { useState, useEffect } from 'react';
import { targetApi } from '../services/api';
import { Target } from '../types';
import { Server, Globe } from 'lucide-react';

interface TargetFieldSelectorProps {
  value: string;
  onChange: (value: string) => void;
  placeholder?: string;
}

const TargetFieldSelector: React.FC<TargetFieldSelectorProps> = ({
  value,
  onChange,
  placeholder = 'Select target or enter hostname'
}) => {
  const [targets, setTargets] = useState<Target[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [showDropdown, setShowDropdown] = useState(false);

  useEffect(() => {
    fetchTargets();
  }, []);

  const fetchTargets = async () => {
    try {
      setLoading(true);
      const response = await targetApi.list(0, 1000); // Get all targets
      setTargets(response.targets || []);
      setError(null);
    } catch (err) {
      console.error('Failed to fetch targets:', err);
      setError('Failed to load targets');
    } finally {
      setLoading(false);
    }
  };

  const handleTargetSelect = (target: Target) => {
    onChange(target.hostname || target.ip_address || target.name);
    setShowDropdown(false);
  };

  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    onChange(e.target.value);
  };

  const handleInputFocus = () => {
    if (!loading && targets.length > 0) {
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
          type="text"
          value={value}
          onChange={handleInputChange}
          placeholder="Loading targets..."
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
          <Server size={14} />
        </div>
      </div>
    );
  }

  return (
    <div style={{ position: 'relative' }}>
      <input
        type="text"
        value={value}
        onChange={handleInputChange}
        onFocus={handleInputFocus}
        onBlur={handleInputBlur}
        placeholder={placeholder}
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
        <Server size={14} />
      </div>

      {showDropdown && targets.length > 0 && (
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
            Available Targets
          </div>
          
          {targets.map((target) => (
            <div
              key={target.id}
              onClick={() => handleTargetSelect(target)}
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
                backgroundColor: '#f0f0f0',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                color: '#666'
              }}>
                <Server size={12} />
              </div>
              
              <div style={{ flex: 1 }}>
                <div style={{ fontWeight: '500' }}>{target.name}</div>
                <div style={{ fontSize: '11px', color: '#666' }}>
                  {target.hostname || target.ip_address}
                  {target.port && target.port !== 22 && target.port !== 3389 && ` :${target.port}`}
                </div>
              </div>
              
              <div style={{ fontSize: '11px', color: '#999' }}>
                {target.os_type || 'Unknown'}
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

export default TargetFieldSelector;