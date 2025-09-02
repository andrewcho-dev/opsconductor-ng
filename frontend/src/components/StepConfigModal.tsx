import React, { useState, useEffect } from 'react';
import JobTargetSelector from './JobTargetSelector';

interface StepConfigModalProps {
  isOpen: boolean;
  onClose: () => void;
  onSave: (config: any) => void;
  stepNode: {
    id: string;
    name: string;
    type: string;
    config: any;
  } | null;
}

const StepConfigModal: React.FC<StepConfigModalProps> = ({
  isOpen,
  onClose,
  onSave,
  stepNode
}) => {
  const [config, setConfig] = useState<any>({});

  useEffect(() => {
    if (stepNode) {
      setConfig({ ...stepNode.config });
    }
  }, [stepNode]);

  const handleSave = () => {
    onSave(config);
    onClose();
  };

  const updateConfig = (key: string, value: any) => {
    setConfig((prev: any) => ({
      ...prev,
      [key]: value
    }));
  };

  if (!isOpen || !stepNode) {
    return null;
  }

  return (
    <div style={{
      position: 'fixed',
      top: 0,
      left: 0,
      right: 0,
      bottom: 0,
      backgroundColor: 'rgba(0, 0, 0, 0.5)',
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'center',
      zIndex: 1000
    }}>
      <div style={{
        backgroundColor: 'white',
        borderRadius: '8px',
        padding: '20px',
        width: '500px',
        maxHeight: '80vh',
        overflow: 'auto',
        boxShadow: '0 4px 20px rgba(0, 0, 0, 0.3)'
      }}>
        {/* Header */}
        <div style={{
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
          marginBottom: '20px',
          paddingBottom: '10px',
          borderBottom: '1px solid #eee'
        }}>
          <h3 style={{ margin: 0, color: '#333' }}>
            Configure: {stepNode.name}
          </h3>
          <button
            onClick={onClose}
            style={{
              background: 'none',
              border: 'none',
              fontSize: '24px',
              cursor: 'pointer',
              color: '#666',
              padding: '0',
              width: '30px',
              height: '30px',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center'
            }}
          >
            ×
          </button>
        </div>

        {/* Step Name */}
        <div style={{ marginBottom: '20px' }}>
          <label style={{ 
            display: 'block', 
            marginBottom: '8px', 
            fontWeight: 'bold',
            fontSize: '14px'
          }}>
            Step Name:
          </label>
          <input
            type="text"
            value={config.name || stepNode.name}
            onChange={(e) => updateConfig('name', e.target.value)}
            style={{
              width: '100%',
              padding: '10px',
              border: '1px solid #ddd',
              borderRadius: '4px',
              fontSize: '14px'
            }}
          />
        </div>

        {/* Target Assignment Configuration */}
        {stepNode.type === 'target.assign' && (
          <div style={{ marginBottom: '20px' }}>
            <label style={{ 
              display: 'block', 
              marginBottom: '8px', 
              fontWeight: 'bold',
              fontSize: '14px'
            }}>
              Target Selection:
            </label>
            
            {/* Selection Mode */}
            <div style={{ marginBottom: '15px' }}>
              <label style={{ 
                display: 'block', 
                marginBottom: '5px', 
                fontSize: '13px',
                color: '#666'
              }}>
                Selection Mode:
              </label>
              <select
                value={config.selection_mode || 'specific'}
                onChange={(e) => updateConfig('selection_mode', e.target.value)}
                style={{
                  width: '100%',
                  padding: '8px',
                  border: '1px solid #ddd',
                  borderRadius: '4px',
                  fontSize: '14px'
                }}
              >
                <option value="specific">Specific Targets</option>
                <option value="tag-based">Tag-based Selection</option>
                <option value="all">All Targets</option>
              </select>
            </div>

            {/* Target Selector for specific mode */}
            {config.selection_mode !== 'all' && config.selection_mode !== 'tag-based' && (
              <JobTargetSelector
                selectedTargets={
                  typeof config.target_names === 'string' && config.target_names
                    ? config.target_names.split(',').map(t => t.trim()).filter(t => t)
                    : []
                }
                onTargetChange={(targets) => {
                  updateConfig('target_names', targets.join(','));
                }}
                selectionMode="multiple"
              />
            )}

            {/* Tag-based selection */}
            {config.selection_mode === 'tag-based' && (
              <div>
                <label style={{ 
                  display: 'block', 
                  marginBottom: '5px', 
                  fontSize: '13px',
                  color: '#666'
                }}>
                  Tags (comma-separated):
                </label>
                <input
                  type="text"
                  value={config.target_tags || ''}
                  onChange={(e) => updateConfig('target_tags', e.target.value)}
                  placeholder="e.g., production, web-server, database"
                  style={{
                    width: '100%',
                    padding: '8px',
                    border: '1px solid #ddd',
                    borderRadius: '4px',
                    fontSize: '14px'
                  }}
                />
              </div>
            )}

            {/* All targets mode info */}
            {config.selection_mode === 'all' && (
              <div style={{
                padding: '10px',
                backgroundColor: '#e3f2fd',
                border: '1px solid #2196f3',
                borderRadius: '4px',
                fontSize: '13px',
                color: '#1976d2'
              }}>
                ℹ️ This step will run on all available targets
              </div>
            )}
          </div>
        )}

        {/* Other step configurations */}
        {Object.entries(config).map(([key, value]) => {
          // Skip already handled fields
          if (['name', 'target_names', 'selection_mode', 'target_tags'].includes(key)) {
            return null;
          }

          return (
            <div key={key} style={{ marginBottom: '15px' }}>
              <label style={{ 
                display: 'block', 
                marginBottom: '5px', 
                fontWeight: 'bold',
                fontSize: '13px'
              }}>
                {key.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase())}:
              </label>
              
              {typeof value === 'boolean' ? (
                <label style={{ display: 'flex', alignItems: 'center', cursor: 'pointer' }}>
                  <input
                    type="checkbox"
                    checked={value}
                    onChange={(e) => updateConfig(key, e.target.checked)}
                    style={{ marginRight: '8px' }}
                  />
                  <span style={{ fontSize: '14px' }}>
                    {value ? 'Enabled' : 'Disabled'}
                  </span>
                </label>
              ) : typeof value === 'number' ? (
                <input
                  type="number"
                  value={value}
                  onChange={(e) => updateConfig(key, parseInt(e.target.value) || 0)}
                  style={{
                    width: '100%',
                    padding: '8px',
                    border: '1px solid #ddd',
                    borderRadius: '4px',
                    fontSize: '14px'
                  }}
                />
              ) : (
                <input
                  type="text"
                  value={String(value)}
                  onChange={(e) => updateConfig(key, e.target.value)}
                  style={{
                    width: '100%',
                    padding: '8px',
                    border: '1px solid #ddd',
                    borderRadius: '4px',
                    fontSize: '14px'
                  }}
                />
              )}
            </div>
          );
        })}

        {/* Footer */}
        <div style={{
          display: 'flex',
          justifyContent: 'flex-end',
          gap: '10px',
          marginTop: '20px',
          paddingTop: '15px',
          borderTop: '1px solid #eee'
        }}>
          <button
            onClick={onClose}
            style={{
              padding: '10px 20px',
              backgroundColor: '#6c757d',
              color: 'white',
              border: 'none',
              borderRadius: '4px',
              cursor: 'pointer',
              fontSize: '14px'
            }}
          >
            Cancel
          </button>
          <button
            onClick={handleSave}
            style={{
              padding: '10px 20px',
              backgroundColor: '#007bff',
              color: 'white',
              border: 'none',
              borderRadius: '4px',
              cursor: 'pointer',
              fontSize: '14px'
            }}
          >
            Save Configuration
          </button>
        </div>
      </div>
    </div>
  );
};

export default StepConfigModal;