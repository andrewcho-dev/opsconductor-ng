import React, { useState } from 'react';
import { Asset } from '../types/asset';

interface AssetGridFormProps {
  asset?: Asset; // For edit mode
  onSave: (assetData: any) => void;
  onCancel: () => void;
  mode: 'create' | 'edit' | 'view';
}

interface FieldDefinition {
  field: string;
  label: string;
  type: 'text' | 'number' | 'boolean' | 'dropdown' | 'tags';
  options?: string[];
  required?: boolean;
}

const AssetGridForm: React.FC<AssetGridFormProps> = ({ asset, onSave, onCancel, mode }) => {
  const [formData, setFormData] = useState<Record<string, any>>({
    name: asset?.name || '',
    hostname: asset?.hostname || '',
    ip_address: asset?.ip_address || '',
    description: asset?.description || '',
    tags: asset?.tags || [],
    os_type: asset?.os_type || 'linux',
    os_version: asset?.os_version || '',
    service_type: asset?.service_type || 'ssh',
    port: asset?.port || 22,
    is_secure: asset?.is_secure || false,
    has_credentials: asset?.has_credentials || false,
    is_active: asset?.is_active !== false, // Default to true
  });

  // Field definitions
  const fieldDefinitions: FieldDefinition[] = [
    { field: 'name', label: 'Asset Name', type: 'text' },
    { field: 'hostname', label: 'Hostname', type: 'text' },
    { field: 'ip_address', label: 'IP Address', type: 'text' },
    { field: 'description', label: 'Description', type: 'text' },
    { field: 'os_type', label: 'OS Type', type: 'dropdown', options: ['linux', 'windows', 'macos', 'unix'], required: true },
    { field: 'os_version', label: 'OS Version', type: 'text' },
    { field: 'service_type', label: 'Service Type', type: 'dropdown', options: ['ssh', 'rdp', 'http', 'https', 'ftp', 'database'], required: true },
    { field: 'port', label: 'Port', type: 'number', required: true },
    { field: 'is_secure', label: 'Secure Connection', type: 'boolean' },
    { field: 'has_credentials', label: 'Has Credentials', type: 'boolean' },
    { field: 'is_active', label: 'Active', type: 'boolean' },
    { field: 'tags', label: 'Tags', type: 'tags' },
  ];

  const handleFieldChange = (field: string, value: any) => {
    setFormData(prev => ({
      ...prev,
      [field]: value
    }));
  };

  const handleTagsChange = (field: string, value: string) => {
    const tags = value ? value.split(',').map(tag => tag.trim()).filter(Boolean) : [];
    handleFieldChange(field, tags);
  };

  const handleSave = () => {
    // Validate required fields
    const requiredFields = fieldDefinitions.filter(f => f.required);
    const missingFields = requiredFields.filter(f => !formData[f.field] || formData[f.field] === '');
    
    if (missingFields.length > 0) {
      alert(`Please fill in required fields: ${missingFields.map(f => f.label).join(', ')}`);
      return;
    }
    
    onSave(formData);
  };

  const renderFieldValue = (fieldDef: FieldDefinition) => {
    const value = formData[fieldDef.field];
    const isReadOnly = mode === 'view';

    switch (fieldDef.type) {
      case 'text':
        return (
          <input
            type="text"
            value={value || ''}
            onChange={(e) => handleFieldChange(fieldDef.field, e.target.value)}
            readOnly={isReadOnly}
            className="field-input"
            placeholder={isReadOnly ? '' : `Enter ${fieldDef.label.toLowerCase()}...`}
          />
        );
      
      case 'number':
        return (
          <input
            type="number"
            value={value || ''}
            onChange={(e) => handleFieldChange(fieldDef.field, parseInt(e.target.value) || 0)}
            readOnly={isReadOnly}
            className="field-input"
          />
        );
      
      case 'boolean':
        return (
          <div className="boolean-field">
            <input
              type="checkbox"
              checked={Boolean(value)}
              onChange={(e) => handleFieldChange(fieldDef.field, e.target.checked)}
              disabled={isReadOnly}
              className="field-checkbox"
            />
            <span className="boolean-label">{value ? 'Yes' : 'No'}</span>
          </div>
        );
      
      case 'dropdown':
        return (
          <select
            value={value || ''}
            onChange={(e) => handleFieldChange(fieldDef.field, e.target.value)}
            disabled={isReadOnly}
            className="field-select"
          >
            <option value="">Select {fieldDef.label}</option>
            {(fieldDef.options || []).map(option => (
              <option key={option} value={option}>{option}</option>
            ))}
          </select>
        );
      
      case 'tags':
        const tagsValue = Array.isArray(value) ? value.join(', ') : '';
        return (
          <input
            type="text"
            value={tagsValue}
            onChange={(e) => handleTagsChange(fieldDef.field, e.target.value)}
            readOnly={isReadOnly}
            className="field-input"
            placeholder={isReadOnly ? '' : 'Enter tags separated by commas...'}
          />
        );
      
      default:
        return (
          <input
            type="text"
            value={value || ''}
            onChange={(e) => handleFieldChange(fieldDef.field, e.target.value)}
            readOnly={isReadOnly}
            className="field-input"
          />
        );
    }
  };

  return (
    <div className="asset-grid-form">
      <div className="grid-container">
        <div className="grid-header">
          <div className="grid-header-cell">Field</div>
          <div className="grid-header-cell">Value</div>
        </div>
        
        <div className="grid-body">
          {fieldDefinitions.map((fieldDef) => (
            <div key={fieldDef.field} className="grid-row">
              <div className="grid-cell field-cell">
                <span className={`field-label ${fieldDef.required ? 'required' : ''}`}>
                  {fieldDef.label}
                  {fieldDef.required && <span className="required-asterisk">*</span>}
                </span>
              </div>
              <div className="grid-cell value-cell">
                {renderFieldValue(fieldDef)}
              </div>
            </div>
          ))}
        </div>
      </div>
      
      {mode !== 'view' && (
        <div className="form-actions">
          <button className="btn btn-primary" onClick={handleSave}>
            {mode === 'create' ? 'Create Asset' : 'Save Changes'}
          </button>
          <button className="btn btn-secondary" onClick={onCancel}>
            Cancel
          </button>
        </div>
      )}

      <style>{`
        .asset-grid-form {
          display: flex;
          flex-direction: column;
          height: 100%;
          gap: 16px;
        }
        
        .grid-container {
          flex: 1;
          border: 1px solid #dee2e6;
          border-radius: 6px;
          overflow: hidden;
          min-height: 400px;
          background: white;
        }
        
        .grid-header {
          display: grid;
          grid-template-columns: 200px 1fr;
          background-color: #f8f9fa;
          border-bottom: 2px solid #dee2e6;
        }
        
        .grid-header-cell {
          padding: 12px 16px;
          font-weight: 600;
          color: #495057;
          border-right: 1px solid #dee2e6;
        }
        
        .grid-header-cell:last-child {
          border-right: none;
        }
        
        .grid-body {
          max-height: 500px;
          overflow-y: auto;
        }
        
        .grid-row {
          display: grid;
          grid-template-columns: 200px 1fr;
          border-bottom: 1px solid #dee2e6;
        }
        
        .grid-row:hover {
          background-color: #f8f9fa;
        }
        
        .grid-cell {
          padding: 12px 16px;
          border-right: 1px solid #dee2e6;
          display: flex;
          align-items: center;
        }
        
        .grid-cell:last-child {
          border-right: none;
        }
        
        .field-cell {
          background-color: #f8f9fa;
        }
        
        .field-label {
          font-weight: 500;
          color: #495057;
        }
        
        .field-label.required {
          color: #212529;
        }
        
        .required-asterisk {
          color: #dc3545;
          margin-left: 4px;
        }
        
        .value-cell {
          padding: 8px 16px;
        }
        
        .field-input,
        .field-select {
          width: 100%;
          border: 1px solid #dee2e6;
          border-radius: 4px;
          padding: 8px 12px;
          font-size: 14px;
          background: white;
          transition: border-color 0.2s ease;
        }
        
        .field-input:focus,
        .field-select:focus {
          outline: none;
          border-color: #0d6efd;
          box-shadow: 0 0 0 2px rgba(13, 110, 253, 0.25);
        }
        
        .field-input[readonly] {
          background-color: #f8f9fa;
          border-color: #e9ecef;
        }
        
        .boolean-field {
          display: flex;
          align-items: center;
          gap: 8px;
        }
        
        .field-checkbox {
          width: auto;
          margin: 0;
        }
        
        .boolean-label {
          font-size: 14px;
          color: #495057;
        }
        
        .form-actions {
          display: flex;
          gap: 12px;
          justify-content: flex-end;
          padding: 16px 0;
          border-top: 1px solid #dee2e6;
        }
        
        .btn {
          padding: 8px 16px;
          border-radius: 6px;
          font-size: 14px;
          font-weight: 500;
          cursor: pointer;
          border: 1px solid transparent;
          transition: all 0.2s ease;
        }
        
        .btn-primary {
          background-color: #0d6efd;
          color: white;
          border-color: #0d6efd;
        }
        
        .btn-primary:hover {
          background-color: #0b5ed7;
          border-color: #0a58ca;
        }
        
        .btn-secondary {
          background-color: #6c757d;
          color: white;
          border-color: #6c757d;
        }
        
        .btn-secondary:hover {
          background-color: #5c636a;
          border-color: #565e64;
        }
      `}</style>
    </div>
  );
};

export default AssetGridForm;