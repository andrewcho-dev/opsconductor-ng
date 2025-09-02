import React, { useState, useEffect } from 'react';
import { targetApi } from '../services/api';
import { Target } from '../types';

interface JobTargetSelectorProps {
  selectedTargets: string[];
  onTargetChange: (targets: string[]) => void;
  selectionMode: 'single' | 'multiple';
}

const JobTargetSelector: React.FC<JobTargetSelectorProps> = ({
  selectedTargets,
  onTargetChange,
  selectionMode
}) => {
  const [targets, setTargets] = useState<Target[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    fetchTargets();
  }, []);

  const fetchTargets = async () => {
    try {
      setLoading(true);
      const response = await targetApi.list();
      setTargets(response.targets || []);
      setError(null);
    } catch (err) {
      console.error('Failed to fetch targets:', err);
      setError('Failed to load targets');
    } finally {
      setLoading(false);
    }
  };

  const handleTargetToggle = (targetName: string) => {
    if (selectionMode === 'single') {
      // Single mode: replace selection
      onTargetChange([targetName]);
    } else {
      // Multiple mode: toggle selection
      if (selectedTargets.includes(targetName)) {
        // Remove from selection
        onTargetChange(selectedTargets.filter(t => t !== targetName));
      } else {
        // Add to selection
        onTargetChange([...selectedTargets, targetName]);
      }
    }
  };

  const handleSelectAll = () => {
    if (selectionMode === 'multiple') {
      const allTargetNames = targets.map(t => t.name);
      onTargetChange(allTargetNames);
    }
  };

  const handleSelectNone = () => {
    onTargetChange([]);
  };

  if (loading) {
    return (
      <div style={{ padding: '20px', textAlign: 'center' }}>
        <div>Loading targets...</div>
      </div>
    );
  }

  if (error) {
    return (
      <div style={{ padding: '20px', color: 'red' }}>
        <div>{error}</div>
        <button 
          onClick={fetchTargets}
          style={{ 
            marginTop: '10px',
            padding: '5px 10px',
            backgroundColor: '#007bff',
            color: 'white',
            border: 'none',
            borderRadius: '4px',
            cursor: 'pointer'
          }}
        >
          Retry
        </button>
      </div>
    );
  }

  if (targets.length === 0) {
    return (
      <div style={{ padding: '20px', textAlign: 'center', color: '#666' }}>
        No targets available. Please add targets first.
      </div>
    );
  }

  return (
    <div style={{ 
      border: '1px solid #ddd', 
      borderRadius: '4px', 
      backgroundColor: '#f9f9f9'
    }}>
      {/* Header with selection controls */}
      <div style={{ 
        padding: '10px', 
        borderBottom: '1px solid #ddd',
        backgroundColor: '#f1f1f1',
        display: 'flex',
        justifyContent: 'space-between',
        alignItems: 'center'
      }}>
        <div style={{ fontSize: '14px', fontWeight: 'bold' }}>
          Select Targets ({selectedTargets.length} selected)
        </div>
        {selectionMode === 'multiple' && (
          <div>
            <button
              onClick={handleSelectAll}
              style={{
                padding: '4px 8px',
                marginRight: '5px',
                fontSize: '12px',
                backgroundColor: '#28a745',
                color: 'white',
                border: 'none',
                borderRadius: '3px',
                cursor: 'pointer'
              }}
            >
              Select All
            </button>
            <button
              onClick={handleSelectNone}
              style={{
                padding: '4px 8px',
                fontSize: '12px',
                backgroundColor: '#6c757d',
                color: 'white',
                border: 'none',
                borderRadius: '3px',
                cursor: 'pointer'
              }}
            >
              Clear
            </button>
          </div>
        )}
      </div>

      {/* Target list */}
      <div style={{ 
        maxHeight: '300px', 
        overflowY: 'auto',
        padding: '5px'
      }}>
        {targets.map((target) => {
          const isSelected = selectedTargets.includes(target.name);
          return (
            <div
              key={target.id}
              onClick={() => handleTargetToggle(target.name)}
              style={{
                padding: '10px',
                margin: '2px 0',
                backgroundColor: isSelected ? '#e3f2fd' : 'white',
                border: isSelected ? '2px solid #2196f3' : '1px solid #ddd',
                borderRadius: '4px',
                cursor: 'pointer',
                display: 'flex',
                alignItems: 'center',
                transition: 'all 0.2s ease'
              }}
              onMouseEnter={(e) => {
                if (!isSelected) {
                  e.currentTarget.style.backgroundColor = '#f5f5f5';
                }
              }}
              onMouseLeave={(e) => {
                if (!isSelected) {
                  e.currentTarget.style.backgroundColor = 'white';
                }
              }}
            >
              <input
                type={selectionMode === 'single' ? 'radio' : 'checkbox'}
                checked={isSelected}
                onChange={() => {}} // Handled by parent div onClick
                style={{ 
                  marginRight: '12px',
                  pointerEvents: 'none' // Prevent double-click handling
                }}
              />
              <div style={{ flex: 1 }}>
                <div style={{ 
                  fontWeight: 'bold', 
                  fontSize: '14px',
                  color: isSelected ? '#1976d2' : '#333'
                }}>
                  {target.name}
                </div>
                <div style={{ 
                  fontSize: '12px', 
                  color: '#666',
                  marginTop: '2px'
                }}>
                  {target.hostname} • {target.ip_address}
                </div>
                <div style={{ 
                  fontSize: '11px', 
                  color: '#4caf50',
                  marginTop: '2px'
                }}>
                  ✓ Active
                </div>
              </div>
            </div>
          );
        })}
      </div>

      {/* Footer with summary */}
      <div style={{ 
        padding: '8px 10px', 
        borderTop: '1px solid #ddd',
        backgroundColor: '#f8f9fa',
        fontSize: '12px',
        color: '#666'
      }}>
        {selectionMode === 'single' 
          ? `Single target selection mode`
          : `Multiple target selection mode • ${selectedTargets.length} of ${targets.length} targets selected`
        }
      </div>
    </div>
  );
};

export default JobTargetSelector;