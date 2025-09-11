import React, { useState, useEffect, useMemo, useCallback } from 'react';
import JobTargetSelector from './JobTargetSelector';
import CredentialSelector from './CredentialSelector';
import TargetFieldSelector from './TargetFieldSelector';
import ConnectionTypeSelector from './ConnectionTypeSelector';
import { targetApi } from '../services/api';
import { Target } from '../types';
import { X, Info, ChevronDown, ChevronRight, Settings, User, Lock } from 'lucide-react';

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

const StepConfigModal: React.FC<StepConfigModalProps> = React.memo(({
  isOpen,
  onClose,
  onSave,
  stepNode
}) => {
  const [config, setConfig] = useState<any>({});
  const [targets, setTargets] = useState<Target[]>([]);
  const [showConnectionOverride, setShowConnectionOverride] = useState(false);
  const [showCredentialOverride, setShowCredentialOverride] = useState(false);

  useEffect(() => {
    if (stepNode) {
      const initialConfig = { ...stepNode.config };
      // Ensure target_names is always a string
      if (initialConfig.target_names === undefined || initialConfig.target_names === null) {
        initialConfig.target_names = '';
      }
      // Ensure selection_mode has a default value
      if (!initialConfig.selection_mode) {
        initialConfig.selection_mode = 'specific';
      }
      setConfig(initialConfig);
    }
  }, [stepNode?.id]);

  useEffect(() => {
    fetchTargets();
  }, []);

  const fetchTargets = async () => {
    try {
      const response = await targetApi.list(0, 1000);
      setTargets(response.targets || []);
    } catch (err) {
      console.error('Failed to fetch targets:', err);
    }
  };

  const handleSave = () => {
    onSave(config);
    onClose();
  };

  const updateConfig = useCallback((key: string, value: any) => {
    setConfig((prev: any) => ({
      ...prev,
      [key]: value
    }));
  }, []);

  const handleTargetChange = useCallback((targets: string[]) => {
    // Store multiple targets
    updateConfig('targets', targets);
    // Also set the first target as primary for backward compatibility
    if (targets.length > 0) {
      updateConfig('target', targets[0]);
    } else {
      updateConfig('target', '');
    }
  }, [updateConfig]);

  const handleTargetSelection = (targetNames: string[]) => {
    const targetName = targetNames[0];
    if (!targetName) return;

    // Find the selected target
    const selectedTarget = targets.find(t => t.name === targetName);
    if (!selectedTarget) return;

    // Auto-populate fields based on target configuration
    const updates: any = {
      target: targetName,
      target_host: selectedTarget.hostname || selectedTarget.ip_address || targetName
    };

    // Auto-populate connection method based on target OS and available methods
    if (selectedTarget.os_type) {
      switch (selectedTarget.os_type.toLowerCase()) {
        case 'windows':
          updates.connection_method = 'winrm';
          updates.connection_type = 'winrm'; // Keep both for compatibility
          break;
        case 'linux':
        case 'unix':
          updates.connection_method = 'ssh';
          updates.connection_type = 'ssh'; // Keep both for compatibility
          break;
        default:
          updates.connection_method = 'ssh';
          updates.connection_type = 'ssh'; // Keep both for compatibility
      }
    }

    // Auto-populate port if available
    if (selectedTarget.port) {
      updates.port = selectedTarget.port;
    }

    // Auto-populate credentials if target has associated credentials
    if (selectedTarget.credential_ref) {
      // You could fetch credential details here and populate username
      updates.username = `{{credential:${selectedTarget.credential_ref}:username}}`;
      updates.password = `{{credential:${selectedTarget.credential_ref}:password}}`;
    }

    // Apply all updates at once
    setConfig((prev: any) => ({
      ...prev,
      ...updates
    }));
  };

  // Compact Target Selector Component
  const CompactTargetSelector = ({ selectedTargets, onTargetChange, availableTargets }: { 
    selectedTargets: string[], 
    onTargetChange: (targets: string[]) => void,
    availableTargets: Target[]
  }) => {
    const handleTargetToggle = (targetName: string) => {
      const isSelected = selectedTargets.includes(targetName);
      let newSelection: string[];
      
      if (isSelected) {
        // Remove target
        newSelection = selectedTargets.filter(t => t !== targetName);
      } else {
        // Add target
        newSelection = [...selectedTargets, targetName];
      }
      
      onTargetChange(newSelection);
    };
    
    return (
      <div style={{
        width: '100%',
        height: '120px',
        border: '1px solid #ddd',
        borderRadius: '4px',
        backgroundColor: 'white',
        overflowY: 'auto',
        padding: '4px'
      }}>
        {availableTargets.map(target => (
          <div 
            key={target.name}
            style={{
              display: 'flex',
              alignItems: 'center',
              padding: '2px 4px',
              fontSize: '12px',
              cursor: 'pointer',
              backgroundColor: selectedTargets.includes(target.name) ? '#e3f2fd' : 'transparent',
              borderRadius: '2px',
              marginBottom: '1px'
            }}
            onClick={() => handleTargetToggle(target.name)}
          >
            <input
              type="checkbox"
              checked={selectedTargets.includes(target.name)}
              onChange={() => {}} // Handled by div onClick
              style={{ marginRight: '6px', cursor: 'pointer' }}
            />
            <span style={{ whiteSpace: 'nowrap' }}>
              {target.name} ({target.hostname || target.ip_address}) - {target.os_type || 'Unknown'}
            </span>
          </div>
        ))}
      </div>
    );
  };

  // Collapsible Section Component
  const CollapsibleSection = ({ 
    title, 
    icon, 
    isOpen, 
    onToggle, 
    children 
  }: { 
    title: string, 
    icon: React.ReactNode, 
    isOpen: boolean, 
    onToggle: () => void, 
    children: React.ReactNode 
  }) => {
    return (
      <div style={{ marginBottom: '10px' }}>
        <button
          type="button"
          onClick={onToggle}
          style={{
            display: 'flex',
            alignItems: 'center',
            gap: '6px',
            width: '100%',
            padding: '6px 8px',
            backgroundColor: '#f8f9fa',
            border: '1px solid #e9ecef',
            borderRadius: '4px',
            fontSize: '12px',
            color: '#495057',
            cursor: 'pointer',
            textAlign: 'left'
          }}
        >
          {isOpen ? <ChevronDown size={14} /> : <ChevronRight size={14} />}
          {icon}
          <span>{title}</span>
        </button>
        {isOpen && (
          <div style={{ 
            padding: '10px', 
            border: '1px solid #e9ecef', 
            borderTop: 'none',
            borderRadius: '0 0 4px 4px',
            backgroundColor: '#fafbfc'
          }}>
            {children}
          </div>
        )}
      </div>
    );
  };

  // Function to determine field type and render appropriate selector
  const renderFieldInput = (key: string, value: any) => {
    const lowerKey = key.toLowerCase();
    
    // Target-related fields
    if (lowerKey.includes('target') && (lowerKey.includes('host') || lowerKey.includes('hostname') || lowerKey.includes('ip') || lowerKey.includes('address'))) {
      return (
        <TargetFieldSelector
          value={String(value)}
          onChange={(newValue) => updateConfig(key, newValue)}
          placeholder={`Enter ${key.replace(/_/g, ' ')}`}
        />
      );
    }
    
    // Username fields
    if (lowerKey.includes('username') || lowerKey.includes('user') || lowerKey === 'login') {
      return (
        <CredentialSelector
          value={String(value)}
          onChange={(newValue) => updateConfig(key, newValue)}
          fieldType="username"
          placeholder={`Select credential or enter ${key.replace(/_/g, ' ')}`}
        />
      );
    }
    
    // Password fields
    if (lowerKey.includes('password') || lowerKey.includes('passwd') || lowerKey.includes('secret')) {
      return (
        <CredentialSelector
          value={String(value)}
          onChange={(newValue) => updateConfig(key, newValue)}
          fieldType="password"
          placeholder={`Select credential or enter ${key.replace(/_/g, ' ')}`}
        />
      );
    }
    
    // Connection type fields
    if (lowerKey.includes('connection') && (lowerKey.includes('type') || lowerKey.includes('method') || lowerKey.includes('protocol'))) {
      return (
        <ConnectionTypeSelector
          value={String(value)}
          onChange={(newValue) => updateConfig(key, newValue)}
          targetType={config.os_type || config.target_type}
        />
      );
    }
    
    // Port fields
    if (lowerKey.includes('port') && typeof value === 'number') {
      return (
        <input
          type="number"
          value={value}
          onChange={(e) => updateConfig(key, parseInt(e.target.value) || 0)}
          min="1"
          max="65535"
          style={{
            width: '100%',
            padding: '8px',
            border: '1px solid #ddd',
            borderRadius: '4px',
            fontSize: '14px'
          }}
        />
      );
    }
    
    // Boolean fields
    if (typeof value === 'boolean') {
      return (
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
      );
    }
    
    // Number fields
    if (typeof value === 'number') {
      return (
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
      );
    }
    
    // Default text input
    return (
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
    );
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
            <X size={20} />
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
                selectedTargets={(() => {
                  const targets = typeof config.target_names === 'string' && config.target_names
                    ? config.target_names.split(',').map((t: string) => t.trim()).filter((t: string) => t)
                    : [];
                  console.log('Current config.target_names:', config.target_names, 'Parsed targets:', targets);
                  return targets;
                })()}
                onTargetChange={(targets) => {
                  console.log('Target selection changed:', targets);
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
                <Info size={14} className="inline mr-1" />This step will run on all available targets
              </div>
            )}
          </div>
        )}

        {/* Core Workflow Configuration */}
        {(stepNode.type.includes('core') || stepNode.type.includes('workflow') || 
          stepNode.type.startsWith('action.') ||
          ['powershell', 'bash', 'cmd', 'ssh', 'winrm'].some(t => stepNode.type.includes(t))) && (
          <div style={{ marginBottom: '15px' }}>
            {/* Compact Target Selection */}
            <div style={{ marginBottom: '10px' }}>
              <label style={{ 
                display: 'block', 
                marginBottom: '4px', 
                fontSize: '12px',
                fontWeight: 'bold',
                color: '#333'
              }}>
                Target(s):
              </label>
              <CompactTargetSelector
                selectedTargets={config.targets || (config.target ? [config.target] : [])}
                availableTargets={targets}
                onTargetChange={handleTargetChange}
              />
            </div>

            {/* Command Field - Larger */}
            <div style={{ marginBottom: '10px' }}>
              <label style={{ 
                display: 'block', 
                marginBottom: '4px', 
                fontSize: '12px',
                fontWeight: 'bold',
                color: '#333'
              }}>
                Command:
              </label>
              <textarea
                value={config.command || ''}
                onChange={(e) => updateConfig('command', e.target.value)}
                placeholder="Enter command to execute..."
                rows={2}
                style={{
                  width: '100%',
                  padding: '8px',
                  border: '1px solid #ddd',
                  borderRadius: '4px',
                  fontSize: '13px',
                  fontFamily: 'Monaco, Consolas, "Courier New", monospace',
                  resize: 'vertical',
                  minHeight: '50px'
                }}
              />
            </div>

            {/* Collapsible Connection Override */}
            <CollapsibleSection
              title="Connection Override"
              icon={<Settings size={12} />}
              isOpen={showConnectionOverride}
              onToggle={() => setShowConnectionOverride(!showConnectionOverride)}
            >
              <div style={{ marginBottom: '10px' }}>
                <label style={{ 
                  display: 'block', 
                  marginBottom: '4px', 
                  fontSize: '11px',
                  color: '#666'
                }}>
                  Connection Method:
                </label>
                <ConnectionTypeSelector
                  value={config.connection_method || config.connection_type || ''}
                  onChange={(value) => {
                    updateConfig('connection_method', value);
                    updateConfig('connection_type', value);
                  }}
                />
              </div>
              
              {config.port !== undefined && (
                <div>
                  <label style={{ 
                    display: 'block', 
                    marginBottom: '4px', 
                    fontSize: '11px',
                    color: '#666'
                  }}>
                    Port:
                  </label>
                  <input
                    type="number"
                    value={config.port || ''}
                    onChange={(e) => updateConfig('port', parseInt(e.target.value) || 22)}
                    min="1"
                    max="65535"
                    placeholder="22 (SSH) or 5985 (WinRM)"
                    style={{
                      width: '80px',
                      padding: '4px 6px',
                      border: '1px solid #ddd',
                      borderRadius: '4px',
                      fontSize: '12px'
                    }}
                  />
                </div>
              )}
            </CollapsibleSection>

            {/* Collapsible Credential Override */}
            <CollapsibleSection
              title="Credential Override"
              icon={<User size={12} />}
              isOpen={showCredentialOverride}
              onToggle={() => setShowCredentialOverride(!showCredentialOverride)}
            >
              <div style={{ marginBottom: '10px' }}>
                <label style={{ 
                  display: 'block', 
                  marginBottom: '4px', 
                  fontSize: '11px',
                  color: '#666'
                }}>
                  Username:
                </label>
                <CredentialSelector
                  value={config.username || ''}
                  onChange={(value) => updateConfig('username', value)}
                  fieldType="username"
                  placeholder="Override username"
                />
              </div>
              
              <div>
                <label style={{ 
                  display: 'block', 
                  marginBottom: '4px', 
                  fontSize: '11px',
                  color: '#666'
                }}>
                  Password:
                </label>
                <CredentialSelector
                  value={config.password || ''}
                  onChange={(value) => updateConfig('password', value)}
                  fieldType="password"
                  placeholder="Override password"
                />
              </div>
            </CollapsibleSection>
          </div>
        )}

        {/* Other step configurations */}
        {Object.entries(config).map(([key, value]) => {
          // Skip already handled fields
          if (['name', 'target_names', 'selection_mode', 'target_tags', 'target', 'targets', 'target_host', 'connection_type', 'connection_method', 'username', 'password', 'port', 'command', 'timeout', 'timeout_seconds'].includes(key)) {
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
              
              {renderFieldInput(key, value)}
            </div>
          );
        })}

        {/* Footer */}
        <div style={{
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
          marginTop: '20px',
          paddingTop: '15px',
          borderTop: '1px solid #eee'
        }}>
          {/* Compact Timeout Field */}
          {(stepNode.type.includes('core') || stepNode.type.includes('workflow') || 
            stepNode.type.startsWith('action.') ||
            ['powershell', 'bash', 'cmd', 'ssh', 'winrm'].some(t => stepNode.type.includes(t))) && (
            <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
              <label style={{ 
                fontSize: '11px',
                color: '#666',
                whiteSpace: 'nowrap'
              }}>
                Timeout:
              </label>
              <input
                type="number"
                value={config.timeout_seconds || config.timeout || 60}
                onChange={(e) => {
                  const timeout = parseInt(e.target.value) || 60;
                  updateConfig('timeout_seconds', timeout);
                  updateConfig('timeout', timeout); // Keep both for compatibility
                }}
                min="1"
                max="3600"
                style={{
                  width: '50px',
                  padding: '2px 4px',
                  border: '1px solid #ddd',
                  borderRadius: '3px',
                  fontSize: '11px',
                  textAlign: 'center'
                }}
              />
              <span style={{ fontSize: '11px', color: '#666' }}>sec</span>
            </div>
          )}
          
          {/* Action Buttons */}
          <div style={{ display: 'flex', gap: '10px' }}>
            <button
              onClick={onClose}
              style={{
                padding: '8px 16px',
                backgroundColor: '#6c757d',
                color: 'white',
                border: 'none',
                borderRadius: '4px',
                cursor: 'pointer',
                fontSize: '13px'
              }}
            >
              Cancel
            </button>
            <button
              onClick={handleSave}
              style={{
                padding: '8px 16px',
                backgroundColor: '#007bff',
                color: 'white',
                border: 'none',
                borderRadius: '4px',
                cursor: 'pointer',
                fontSize: '13px'
              }}
            >
              Save Configuration
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}, (prevProps, nextProps) => {
  // Custom comparison function for React.memo
  return (
    prevProps.isOpen === nextProps.isOpen &&
    prevProps.stepNode?.id === nextProps.stepNode?.id &&
    JSON.stringify(prevProps.stepNode?.config) === JSON.stringify(nextProps.stepNode?.config)
  );
});

export default StepConfigModal;