import React, { useState, useEffect } from 'react';
import { targetApi } from '../services/api';
import { Target } from '../types';

interface TargetSelectorProps {
  selectedTargets: string[];
  onTargetChange: (targets: string[]) => void;
  selectionMode: 'single' | 'multiple';
}

const TargetSelector: React.FC<TargetSelectorProps> = ({
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

  const handleTargetClick = (targetName: string) => {
    console.log('Target clicked:', targetName);
    console.log('Current selection:', selectedTargets);
    console.log('Selection mode:', selectionMode);

    if (selectionMode === 'single') {
      onTargetChange([targetName]);
    } else {
      const isSelected = selectedTargets.includes(targetName);
      if (isSelected) {
        // Remove from selection
        const newSelection = selectedTargets.filter(t => t !== targetName);
        onTargetChange(newSelection);
      } else {
        // Add to selection
        const newSelection = [...selectedTargets, targetName];
        onTargetChange(newSelection);
      }
    }
  };

  if (loading) {
    return <div>Loading targets...</div>;
  }

  if (error) {
    return (
      <div style={{ color: 'red' }}>
        {error}
        <button onClick={fetchTargets} style={{ marginLeft: '10px' }}>
          Retry
        </button>
      </div>
    );
  }

  if (targets.length === 0) {
    return <div>No targets available. Please add targets first.</div>;
  }

  return (
    <div style={{ 
      border: '1px solid #ccc', 
      borderRadius: '4px', 
      maxHeight: '300px', 
      overflowY: 'auto',
      padding: '5px'
    }}>
      {targets.map((target) => {
        const isSelected = selectedTargets.includes(target.name);
        return (
          <div
            key={target.id}
            onClick={() => handleTargetClick(target.name)}
            style={{
              padding: '10px',
              margin: '2px 0',
              backgroundColor: isSelected ? '#e3f2fd' : '#f9f9f9',
              border: isSelected ? '2px solid #2196f3' : '1px solid #ddd',
              borderRadius: '4px',
              cursor: 'pointer',
              display: 'flex',
              alignItems: 'center'
            }}
          >
            <input
              type={selectionMode === 'single' ? 'radio' : 'checkbox'}
              checked={isSelected}
              readOnly
              style={{ marginRight: '10px', pointerEvents: 'none' }}
            />
            <div>
              <div style={{ fontWeight: 'bold', fontSize: '14px' }}>
                {target.name}
              </div>
              <div style={{ fontSize: '12px', color: '#666' }}>
                {target.hostname} ({target.ip_address})
              </div>
              <div style={{ fontSize: '11px', color: '#4caf50' }}>
                Active
              </div>
            </div>
          </div>
        );
      })}
    </div>
  );
};

export default TargetSelector;