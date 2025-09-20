import React, { useState, useEffect } from 'react';
import { Role } from '../types';

interface RoleSpreadsheetFormProps {
  role?: Role;
  onSave: (roleData: any) => void;
  onCancel: () => void;
  mode: 'create' | 'edit' | 'view';
}

interface FieldDefinition {
  field: string;
  label: string;
  type: 'text' | 'textarea' | 'checkbox' | 'multiselect' | 'permission-matrix';
  options?: string[];
  required?: boolean;
  section: string;
  placeholder?: string;
  validation?: (value: any) => string | null;
  conditional?: (formData: any) => boolean;
}

// Permission matrix structure
const PERMISSION_MATRIX = {
  functionalAreas: [
    { key: 'users', label: 'Users', description: 'User account management' },
    { key: 'roles', label: 'Roles', description: 'Role and permission management' },
    { key: 'assets', label: 'Assets', description: 'Infrastructure asset management' },
    { key: 'jobs', label: 'Jobs', description: 'Job and task management' },
    { key: 'credentials', label: 'Credentials', description: 'Credential and secret management' },
    { key: 'settings', label: 'Settings', description: 'System configuration' },
    { key: 'monitoring', label: 'Monitoring', description: 'System monitoring and logs' }
    // Note: system admin row removed - it's represented by having all permissions checked
  ],
  permissionLevels: [
    { key: 'read', label: 'Read', description: 'View and list items' },
    { key: 'create', label: 'Create', description: 'Create new items' },
    { key: 'update', label: 'Update', description: 'Modify existing items' },
    { key: 'delete', label: 'Delete', description: 'Remove items' },
    { key: 'execute', label: 'Execute', description: 'Run or execute actions' }
  ],
  // Define which permissions are available for each functional area
  availablePermissions: {
    users: ['read', 'create', 'update', 'delete'],
    roles: ['read', 'create', 'update', 'delete'],
    assets: ['read', 'create', 'update', 'delete'],
    jobs: ['read', 'create', 'update', 'delete', 'execute'],
    credentials: ['read', 'create', 'update', 'delete'],
    settings: ['read', 'update'],
    monitoring: ['read']
    // Note: system admin removed - it's represented by having all permissions
  }
};

// Generate flat permission list for backward compatibility
const AVAILABLE_PERMISSIONS = [
  'users.read', 'users.create', 'users.update', 'users.delete',
  'roles.read', 'roles.create', 'roles.update', 'roles.delete',
  'assets.read', 'assets.create', 'assets.update', 'assets.delete',
  'jobs.read', 'jobs.create', 'jobs.update', 'jobs.delete', 'jobs.execute',
  'credentials.read', 'credentials.create', 'credentials.update', 'credentials.delete',
  'settings.read', 'settings.update',
  'monitoring.read'
  // Note: system.admin is excluded - it's represented by having all other permissions
];

// Legacy permission mapping (colon format to dot format)
const LEGACY_PERMISSION_MAP: Record<string, string> = {
  // Jobs permissions
  'jobs:read': 'jobs.read',
  'jobs:create': 'jobs.create',
  'jobs:update': 'jobs.update',
  'jobs:delete': 'jobs.delete',
  'jobs:execute': 'jobs.execute',
  
  // Targets/Assets permissions (targets -> assets)
  'targets:read': 'assets.read',
  'targets:create': 'assets.create',
  'targets:update': 'assets.update',
  'targets:delete': 'assets.delete',
  
  // Executions -> Monitoring
  'executions:read': 'monitoring.read',
  
  // Users permissions
  'users:read': 'users.read',
  'users:create': 'users.create',
  'users:update': 'users.update',
  'users:delete': 'users.delete',
  
  // Roles permissions
  'roles:read': 'roles.read',
  'roles:create': 'roles.create',
  'roles:update': 'roles.update',
  'roles:delete': 'roles.delete',
  
  // Credentials permissions
  'credentials:read': 'credentials.read',
  'credentials:create': 'credentials.create',
  'credentials:update': 'credentials.update',
  'credentials:delete': 'credentials.delete',
  
  // Settings permissions
  'settings:read': 'settings.read',
  'settings:update': 'settings.update',
  
  // System admin (wildcard)
  '*': 'system.admin'
};

// Helper function to normalize permissions from legacy format
const normalizePermissions = (permissions: string[]): string[] => {
  if (!Array.isArray(permissions)) return [];
  
  const normalized = permissions.map(permission => {
    // If it's already in dot format, return as-is
    if (permission.includes('.')) {
      return permission;
    }
    
    // Map legacy colon format to dot format
    return LEGACY_PERMISSION_MAP[permission] || permission;
  }).filter(Boolean); // Remove any undefined mappings
  
  // If the role has system.admin or wildcard (*), translate to all permissions
  if (normalized.includes('system.admin') || permissions.includes('*')) {
    // Return all available permissions except system.admin
    return AVAILABLE_PERMISSIONS.filter(p => p !== 'system.admin');
  }
  
  return normalized;
};

const RoleSpreadsheetForm: React.FC<RoleSpreadsheetFormProps> = ({ role, onSave, onCancel, mode }) => {
  const [errors, setErrors] = useState<Record<string, string>>({});
  
  // Debug: Log the role prop when component mounts or role changes
  console.log('🔍 RoleSpreadsheetForm received role prop:', role);
  console.log('🔍 Role permissions:', role?.permissions);
  console.log('🔍 Permissions type:', typeof role?.permissions, 'Is array:', Array.isArray(role?.permissions));
  
  // Check if this is a system role that shouldn't be modified
  const isSystemRole = role?.name === 'admin';
  
  const [formData, setFormData] = useState<Record<string, any>>({
    // Basic Information
    name: role?.name || '',
    description: role?.description || '',
    is_active: role?.is_active !== undefined ? role.is_active : true,
    
    // Permissions - normalize from legacy format
    permissions: Array.isArray(role?.permissions) ? normalizePermissions(role?.permissions || []) : [],
  });

  // Update formData when role prop changes (important for edit mode)
  useEffect(() => {
    console.log('🔄 useEffect triggered with role:', role);
    if (role) {
      const normalizedPermissions = Array.isArray(role.permissions) ? normalizePermissions(role.permissions) : [];
      const newFormData = {
        name: role.name || '',
        description: role.description || '',
        is_active: role.is_active !== undefined ? role.is_active : true,
        permissions: normalizedPermissions,
      };
      console.log('🔄 Setting new formData:', newFormData);
      console.log('🔄 Original permissions:', role.permissions);
      console.log('🔄 Normalized permissions:', normalizedPermissions);
      setFormData(newFormData);
    }
  }, [role]);

  // Field definitions organized by sections
  const fieldDefinitions: FieldDefinition[] = [
    // Basic Information Section
    { 
      field: 'name', 
      label: 'Role Name', 
      type: 'text', 
      required: true, 
      section: 'Basic Information', 
      placeholder: isSystemRole ? 'System role name cannot be changed' : 'Enter a unique role name (e.g., manager, operator)',
      validation: (value) => {
        if (!value || value.trim().length < 2) {
          return 'Role name must be at least 2 characters';
        }
        if (!/^[a-zA-Z0-9._-]+$/.test(value)) {
          return 'Role name can only contain letters, numbers, dots, underscores, and hyphens';
        }
        return null;
      }
    },
    { 
      field: 'description', 
      label: 'Description', 
      type: 'textarea', 
      required: true, 
      section: 'Basic Information', 
      placeholder: isSystemRole ? 'System role description cannot be changed' : 'Describe the role\'s purpose and responsibilities',
      validation: (value) => {
        if (!value || value.trim().length < 10) {
          return 'Description must be at least 10 characters';
        }
        return null;
      }
    },
    { 
      field: 'is_active', 
      label: 'Role Status', 
      type: 'checkbox', 
      required: false, 
      section: 'Basic Information'
    },
    
    // Permissions Section
    { 
      field: 'permissions', 
      label: 'Permissions Matrix', 
      type: 'permission-matrix', 
      required: false, 
      section: 'Permissions & Access'
    },
  ];

  // Group fields by section
  const fieldsBySection = fieldDefinitions.reduce((acc, field) => {
    if (field.conditional && !field.conditional(formData)) {
      return acc;
    }
    
    if (!acc[field.section]) {
      acc[field.section] = [];
    }
    acc[field.section].push(field);
    return acc;
  }, {} as Record<string, FieldDefinition[]>);

  const handleFieldChange = (field: string, value: any) => {
    setFormData(prev => ({
      ...prev,
      [field]: value
    }));
    
    // Clear error when field is changed
    if (errors[field]) {
      setErrors(prev => ({
        ...prev,
        [field]: ''
      }));
    }
  };

  const validateForm = (): boolean => {
    const newErrors: Record<string, string> = {};
    
    fieldDefinitions.forEach(fieldDef => {
      if (fieldDef.conditional && !fieldDef.conditional(formData)) {
        return;
      }
      
      const value = formData[fieldDef.field];
      
      // Check required fields
      if (fieldDef.required && (!value || value === '' || (Array.isArray(value) && value.length === 0))) {
        newErrors[fieldDef.field] = `${fieldDef.label} is required`;
      }
      
      // Run custom validation
      if (fieldDef.validation && value) {
        const validationError = fieldDef.validation(value);
        if (validationError) {
          newErrors[fieldDef.field] = validationError;
        }
      }
    });
    
    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const handleSave = () => {
    if (!validateForm()) {
      return;
    }
    
    const saveData = { ...formData };
    
    // Convert permissions back to backend format
    if (saveData.permissions && Array.isArray(saveData.permissions)) {
      // If all available permissions are selected, save as wildcard "*"
      const hasAllPermissions = AVAILABLE_PERMISSIONS.every(permission => 
        saveData.permissions.includes(permission)
      );
      
      if (hasAllPermissions && saveData.permissions.length === AVAILABLE_PERMISSIONS.length) {
        // Save as wildcard for full admin access
        saveData.permissions = ['*'];
      } else {
        // Keep the individual permissions in dot format
        saveData.permissions = saveData.permissions;
      }
    }
    
    // System role restrictions: only allow saving description and is_active
    if (isSystemRole && mode === 'edit') {
      const allowedFields = ['description', 'is_active'];
      const restrictedSaveData: Record<string, any> = {};
      
      // Only include allowed fields for system role
      allowedFields.forEach(field => {
        if (saveData[field] !== undefined) {
          restrictedSaveData[field] = saveData[field];
        }
      });
      
      // Always include the role ID for updates
      if (role?.id) {
        restrictedSaveData.id = role.id;
      }
      
      onSave(restrictedSaveData);
      return;
    }

    console.log('💾 Saving role data:', saveData);
    onSave(saveData);
  };

  const renderFieldValue = (fieldDef: FieldDefinition) => {
    const value = formData[fieldDef.field];
    const isReadOnly = mode === 'view';
    const hasError = errors[fieldDef.field];

    // System role restrictions: only allow editing description and is_active
    const isSystemRestricted = isSystemRole && mode === 'edit' && 
      !['description', 'is_active'].includes(fieldDef.field);

    // Format display values for view mode
    let displayValue = value;
    if (isReadOnly) {
      if (fieldDef.field === 'is_active') {
        displayValue = value ? 'Active' : 'Inactive';
      } else if (fieldDef.field === 'permissions' && Array.isArray(value)) {
        displayValue = value.length > 0 ? value.join(', ') : 'No permissions assigned';
      }
    }

    switch (fieldDef.type) {
      case 'text':
        return (
          <input
            type="text"
            value={displayValue || ''}
            onChange={(e) => handleFieldChange(fieldDef.field, e.target.value)}
            readOnly={isReadOnly || isSystemRestricted}
            className={`field-input ${hasError ? 'error' : ''} ${isSystemRestricted ? 'system-restricted' : ''}`}
            placeholder={isReadOnly ? '' : fieldDef.placeholder}
          />
        );
      
      case 'textarea':
        return (
          <textarea
            value={displayValue || ''}
            onChange={(e) => handleFieldChange(fieldDef.field, e.target.value)}
            readOnly={isReadOnly || isSystemRestricted}
            className={`field-textarea ${hasError ? 'error' : ''} ${isSystemRestricted ? 'system-restricted' : ''}`}
            placeholder={isReadOnly ? '' : fieldDef.placeholder}
            rows={3}
          />
        );
      
      case 'multiselect':
        if (isReadOnly || isSystemRestricted) {
          return (
            <textarea
              value={Array.isArray(displayValue) ? displayValue.join('\n') : displayValue || ''}
              readOnly={true}
              className={`field-textarea ${isSystemRestricted ? 'system-restricted' : ''}`}
              rows={Math.min(Math.max(Array.isArray(value) ? value.length : 1, 3), 8)}
            />
          );
        }
        
        return (
          <div className="multiselect-container">
            <div className="multiselect-header">
              <span>Select permissions for this role:</span>
              <div className="multiselect-actions">
                <button 
                  type="button" 
                  className="btn-link"
                  onClick={() => handleFieldChange(fieldDef.field, [...AVAILABLE_PERMISSIONS])}
                >
                  Select All
                </button>
                <button 
                  type="button" 
                  className="btn-link"
                  onClick={() => handleFieldChange(fieldDef.field, [])}
                >
                  Clear All
                </button>
              </div>
            </div>
            <div className="multiselect-options">
              {(fieldDef.options || []).map((option) => (
                <label key={option} className="multiselect-option">
                  <input
                    type="checkbox"
                    checked={Array.isArray(value) && value.includes(option)}
                    onChange={(e) => {
                      const currentValues = Array.isArray(value) ? value : [];
                      if (e.target.checked) {
                        handleFieldChange(fieldDef.field, [...currentValues, option]);
                      } else {
                        handleFieldChange(fieldDef.field, currentValues.filter(v => v !== option));
                      }
                    }}
                  />
                  <span className="multiselect-label">{option}</span>
                </label>
              ))}
            </div>
            <div className="multiselect-summary">
              Selected: {Array.isArray(value) ? value.length : 0} of {fieldDef.options?.length || 0} permissions
            </div>
          </div>
        );
      
      case 'checkbox':
        if (isReadOnly || isSystemRestricted) {
          return (
            <input
              type="text"
              value={displayValue}
              readOnly={true}
              className={`field-input ${isSystemRestricted ? 'system-restricted' : ''}`}
            />
          );
        }
        return (
          <div className="checkbox-container">
            <input
              type="checkbox"
              checked={!!value}
              onChange={(e) => handleFieldChange(fieldDef.field, e.target.checked)}
              className="field-checkbox"
            />
            <span className="checkbox-label">
              {value ? 'Active' : 'Inactive'}
            </span>
          </div>
        );
      
      case 'permission-matrix':
        console.log('🎯 Permission matrix rendering with value:', value);
        console.log('🎯 Value type:', typeof value, 'Is array:', Array.isArray(value));
        console.log('🎯 Current formData.permissions:', formData.permissions);
        console.log('🎯 isReadOnly:', isReadOnly, 'isSystemRestricted:', isSystemRestricted);
        
        return (
          <div className={`permission-matrix-container ${isReadOnly || isSystemRestricted ? 'read-only' : ''}`}>
            <div className="permission-matrix-header">
              <span>{isReadOnly || isSystemRestricted ? 'Role permissions by functional area:' : 'Configure permissions by functional area:'}</span>
              {!(isReadOnly || isSystemRestricted) && (
                <div className="permission-matrix-actions">
                  <button 
                    type="button" 
                    className="btn-link"
                    onClick={() => handleFieldChange(fieldDef.field, [...AVAILABLE_PERMISSIONS])}
                  >
                    Grant All
                  </button>
                  <button 
                    type="button" 
                    className="btn-link"
                    onClick={() => handleFieldChange(fieldDef.field, [])}
                  >
                    Revoke All
                  </button>
                </div>
              )}
            </div>
            
            <div className="permission-matrix">
              <div className="matrix-header-row">
                <div className="matrix-area-header">Functional Area</div>
                {PERMISSION_MATRIX.permissionLevels.map((level) => (
                  <div key={level.key} className="matrix-permission-header" title={level.description}>
                    {level.label}
                  </div>
                ))}
              </div>
              
              {PERMISSION_MATRIX.functionalAreas.map((area) => (
                <div key={area.key} className="matrix-row">
                  <div className="matrix-area-cell" title={area.description}>
                    <span className="area-label">{area.label}</span>
                    <span className="area-description">{area.description}</span>
                  </div>
                  
                  {PERMISSION_MATRIX.permissionLevels.map((level) => {
                    const permissionKey = `${area.key}.${level.key}`;
                    const isAvailable = (PERMISSION_MATRIX.availablePermissions as any)[area.key]?.includes(level.key);
                    const isChecked = Array.isArray(value) && value.includes(permissionKey);
                    
                    // Debug specific permission checks
                    if (permissionKey === 'users.read') {
                      console.log(`🔍 Checking ${permissionKey}:`, {
                        permissionKey,
                        value,
                        includes: Array.isArray(value) ? value.includes(permissionKey) : 'not array',
                        isChecked
                      });
                    }
                    
                    return (
                      <div key={level.key} className="matrix-permission-cell">
                        {isAvailable ? (
                          <input
                            type="checkbox"
                            checked={isChecked}
                            disabled={isReadOnly || isSystemRestricted}
                            onChange={(e) => {
                              if (isReadOnly || isSystemRestricted) return;
                              const currentValues = Array.isArray(value) ? value : [];
                              if (e.target.checked) {
                                handleFieldChange(fieldDef.field, [...currentValues, permissionKey]);
                              } else {
                                handleFieldChange(fieldDef.field, currentValues.filter(v => v !== permissionKey));
                              }
                            }}
                            className={`matrix-checkbox ${isReadOnly || isSystemRestricted ? 'read-only' : ''}`}
                            title={`${level.description} for ${area.label}`}
                          />
                        ) : (
                          <span className="matrix-unavailable">—</span>
                        )}
                      </div>
                    );
                  })}
                </div>
              ))}
            </div>
            
            <div className="permission-matrix-summary">
              Selected: {Array.isArray(value) ? value.length : 0} of {AVAILABLE_PERMISSIONS.length} permissions
            </div>
          </div>
        );
      
      default:
        return (
          <input
            type="text"
            value={displayValue || ''}
            onChange={(e) => handleFieldChange(fieldDef.field, e.target.value)}
            readOnly={isReadOnly || isSystemRestricted}
            className={`field-input ${hasError ? 'error' : ''} ${isSystemRestricted ? 'system-restricted' : ''}`}
            placeholder={isReadOnly ? '' : fieldDef.placeholder}
          />
        );
    }
  };

  // Organize sections into two columns
  const leftColumnSections = [
    'Basic Information'
  ];
  const rightColumnSections = [
    'Permissions & Access'
  ];

  const renderColumn = (sectionNames: string[]) => (
    <div className="form-column">
      {sectionNames.map((sectionName) => {
        const fields = fieldsBySection[sectionName];
        if (!fields || fields.length === 0) return null;
        
        return (
          <div key={sectionName} className="form-section">
            <div className="section-header">
              <h3>{sectionName}</h3>
            </div>
            <div className="section-grid">
              {fields.map((fieldDef) => (
                <div key={fieldDef.field} className={`field-row ${fieldDef.type === 'multiselect' || fieldDef.type === 'permission-matrix' ? 'field-row-multiselect' : ''}`}>
                  {fieldDef.type === 'permission-matrix' ? (
                    // Full-width layout for permission matrix
                    <div className="field-full-width">
                      {renderFieldValue(fieldDef)}
                      {errors[fieldDef.field] && (
                        <div className="field-error">{errors[fieldDef.field]}</div>
                      )}
                    </div>
                  ) : (
                    // Standard two-column layout for other fields
                    <>
                      <div className="field-label-cell">
                        <label className={`field-label ${fieldDef.required ? 'required' : ''}`}>
                          {fieldDef.label}
                          {fieldDef.required && <span className="required-asterisk">*</span>}
                        </label>
                      </div>
                      <div className="field-value-cell">
                        {renderFieldValue(fieldDef)}
                        {errors[fieldDef.field] && (
                          <div className="field-error">{errors[fieldDef.field]}</div>
                        )}
                      </div>
                    </>
                  )}
                </div>
              ))}
            </div>
          </div>
        );
      })}
    </div>
  );

  return (
    <div className="role-spreadsheet-form">
      {isSystemRole && mode === 'edit' && (
        <div className="system-warning">
          <div className="system-warning-icon">🔒</div>
          <div className="system-warning-text">
            <strong>System Role</strong>
            <br />
            Only description and status can be modified for system roles to maintain security.
          </div>
        </div>
      )}
      <div className="form-container">
        {renderColumn(leftColumnSections)}
        {renderColumn(rightColumnSections)}
      </div>
      
      {mode !== 'view' && (
        <div className="form-actions">
          <button className="btn btn-primary" onClick={handleSave}>
            {mode === 'create' ? 'Create Role' : 'Save Changes'}
          </button>
          <button className="btn btn-secondary" onClick={onCancel}>
            Cancel
          </button>
        </div>
      )}

      <style>{formStyles}</style>
    </div>
  );
};

const formStyles = `
  .role-spreadsheet-form {
    display: flex;
    flex-direction: column;
    height: 100%;
    background: white;
  }

  .system-warning {
    display: flex;
    align-items: center;
    gap: 12px;
    background: #fff3cd;
    border: 1px solid #ffeaa7;
    border-radius: 4px;
    padding: 12px 16px;
    margin: 8px;
    color: #856404;
  }

  .system-warning-icon {
    font-size: 20px;
    flex-shrink: 0;
  }

  .system-warning-text {
    font-size: var(--font-size-sm);
    line-height: 1.4;
  }

  .system-warning-text strong {
    color: #664d03;
  }
  
  .form-container {
    flex: 1;
    overflow-y: auto;
    padding: 8px;
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 8px;
    border: none;
    box-shadow: none;
    background: transparent;
  }
  
  .form-column {
    display: flex;
    flex-direction: column;
    gap: 8px;
  }
  
  .form-section {
    margin: 0;
    border: 1px solid #d0d7de;
    overflow: hidden;
  }
  
  .section-header {
    background: linear-gradient(135deg, #f6f8fa 0%, #e1e7ef 100%);
    padding: 6px 8px;
    border-bottom: 1px solid #d0d7de;
    box-shadow: inset 0 1px 0 rgba(255, 255, 255, 0.5);
  }
  
  .section-header h3 {
    margin: 0;
    font-size: var(--font-size-xs);
    font-weight: 600;
    color: #24292f;
    text-transform: uppercase;
    letter-spacing: 0.5px;
  }
  
  .section-grid {
    padding: 0;
  }
  
  .field-row {
    display: grid;
    grid-template-columns: 160px 1fr;
    border-bottom: 1px solid #eaeef2;
    min-height: 24px;
  }

  .field-row-multiselect {
    min-height: auto;
  }
  
  .field-row:last-child {
    border-bottom: none;
  }
  
  .field-row:nth-child(even) {
    background-color: #f9fafb;
  }
  
  .field-row:hover {
    background-color: #f6f8fa;
  }
  
  .field-label-cell {
    display: flex;
    align-items: flex-start;
    padding: 6px 8px;
    background-color: #f6f8fa;
    border-right: 1px solid #d0d7de;
  }
  
  .field-row:nth-child(even) .field-label-cell {
    background-color: #f1f3f4;
  }
  
  .field-label {
    font-weight: 500;
    color: #24292f;
    font-size: var(--font-size-xs);
    text-transform: uppercase;
    letter-spacing: 0.3px;
  }
  
  .field-label.required {
    color: #24292f;
  }
  
  .required-asterisk {
    color: #dc2626;
    margin-left: 2px;
  }
  
  .field-value-cell {
    display: flex;
    align-items: flex-start;
    padding: 4px 8px;
    position: relative;
  }
  
  .field-full-width {
    grid-column: 1 / -1;
    padding: 8px;
  }
  
  .field-input, .field-textarea {
    width: 100%;
    border: none;
    background: transparent;
    font-size: var(--font-size-sm);
    color: #24292f;
    padding: 2px 0;
    outline: none;
    resize: none;
  }
  
  .field-input:focus, .field-textarea:focus {
    background: rgba(255, 255, 255, 0.8);
    border-radius: 2px;
    padding: 2px 4px;
  }
  
  .field-input[readonly], .field-textarea[readonly] {
    color: #656d76;
    cursor: default;
  }
  
  .field-input.error, .field-textarea.error {
    background: #fef2f2;
    border: 1px solid #dc2626;
    border-radius: 2px;
    padding: 2px 4px;
  }

  /* System restricted fields styling */
  .field-input.system-restricted, .field-textarea.system-restricted {
    background: #f8f9fa !important;
    color: #6c757d !important;
    cursor: not-allowed;
    border: 1px solid #e9ecef;
    border-radius: 2px;
    padding: 2px 4px;
  }

  .field-input.system-restricted:focus, .field-textarea.system-restricted:focus {
    background: #f8f9fa !important;
    outline: none;
    box-shadow: none;
  }

  /* Multiselect styling */
  .multiselect-container {
    width: 100%;
    border: 1px solid #d0d7de;
    border-radius: 4px;
    background: white;
  }

  .multiselect-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 8px 12px;
    background: #f6f8fa;
    border-bottom: 1px solid #d0d7de;
    font-size: var(--font-size-xs);
    font-weight: 500;
  }

  .multiselect-actions {
    display: flex;
    gap: 8px;
  }

  .btn-link {
    background: none;
    border: none;
    color: var(--primary-blue);
    font-size: var(--font-size-xs);
    cursor: pointer;
    text-decoration: underline;
  }

  .btn-link:hover {
    color: var(--primary-blue-dark);
  }

  .multiselect-options {
    max-height: 200px;
    overflow-y: auto;
    padding: 4px;
  }

  .multiselect-option {
    display: flex;
    align-items: center;
    gap: 8px;
    padding: 4px 8px;
    cursor: pointer;
    border-radius: 2px;
    font-size: var(--font-size-sm);
  }

  .multiselect-option:hover {
    background: #f6f8fa;
  }

  .multiselect-option input[type="checkbox"] {
    margin: 0;
  }

  .multiselect-label {
    flex: 1;
    user-select: none;
  }

  .multiselect-summary {
    padding: 8px 12px;
    background: #f6f8fa;
    border-top: 1px solid #d0d7de;
    font-size: var(--font-size-xs);
    color: #656d76;
    text-align: center;
  }

  /* Subtle placeholder styling */
  .field-input::placeholder,
  .field-textarea::placeholder {
    color: #d0d7de !important;
    opacity: 1;
    font-style: italic;
  }
  
  .field-input::-webkit-input-placeholder,
  .field-textarea::-webkit-input-placeholder {
    color: #d0d7de !important;
    opacity: 1;
    font-style: italic;
  }
  
  .field-input::-moz-placeholder,
  .field-textarea::-moz-placeholder {
    color: #d0d7de !important;
    opacity: 1;
    font-style: italic;
  }
  
  /* Hide placeholder when field is focused or has content */
  .field-input:focus::placeholder,
  .field-textarea:focus::placeholder {
    opacity: 0;
    transition: opacity 0.2s ease;
  }
  
  .field-input:focus::-webkit-input-placeholder,
  .field-textarea:focus::-webkit-input-placeholder {
    opacity: 0;
    transition: opacity 0.2s ease;
  }
  
  .field-input:focus::-moz-placeholder,
  .field-textarea:focus::-moz-placeholder {
    opacity: 0;
    transition: opacity 0.2s ease;
  }
  
  .checkbox-container {
    display: flex;
    align-items: center;
    gap: 6px;
  }
  
  .field-checkbox {
    width: 14px;
    height: 14px;
    accent-color: var(--primary-blue);
  }
  
  .checkbox-label {
    font-size: var(--font-size-sm);
    color: #24292f;
    font-weight: 500;
  }
  
  .field-error {
    position: absolute;
    top: 100%;
    left: 8px;
    right: 8px;
    font-size: var(--font-size-xs);
    color: #dc2626;
    background: #fef2f2;
    padding: 2px 4px;
    border: 1px solid #dc2626;
    border-top: none;
    border-radius: 0 0 2px 2px;
    z-index: 10;
  }
  
  .form-actions {
    display: flex;
    gap: 8px;
    padding: 12px 8px 8px 8px;
    border-top: 1px solid #d0d7de;
    background: white;
    margin-top: auto;
  }
  
  .btn {
    padding: 6px 12px;
    border: 1px solid #d0d7de;
    border-radius: 4px;
    font-size: var(--font-size-sm);
    font-weight: 500;
    cursor: pointer;
    transition: all 0.15s ease;
    background: white;
  }
  
  .btn-primary {
    background: var(--primary-blue);
    color: white;
    border-color: var(--primary-blue);
  }
  
  .btn-primary:hover {
    background: var(--primary-blue-dark);
    border-color: var(--primary-blue-dark);
  }
  
  .btn-secondary {
    background: #f6f8fa;
    color: #24292f;
    border-color: #d0d7de;
  }
  
  .btn-secondary:hover {
    background: #f1f3f4;
    border-color: #afb8c1;
  }
  
  /* Permission Matrix Styles */
  .permission-matrix-container {
    border: 1px solid #d0d7de;
    border-radius: 4px;
    background: white;
    overflow: hidden;
  }

  .permission-matrix-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 8px 12px;
    background: #f6f8fa;
    border-bottom: 1px solid #d0d7de;
    font-size: var(--font-size-xs);
    font-weight: 500;
  }

  .permission-matrix-actions {
    display: flex;
    gap: 8px;
  }

  .permission-matrix {
    display: grid;
    grid-template-columns: 160px repeat(5, 1fr);
    background: white;
    font-size: var(--font-size-xs);
  }

  .matrix-header-row {
    display: contents;
  }

  .matrix-area-header {
    padding: 8px 12px;
    background: #f6f8fa;
    border-bottom: 1px solid #d0d7de;
    border-right: 1px solid #d0d7de;
    font-weight: 600;
    font-size: var(--font-size-xs);
    color: #24292f;
    display: flex;
    align-items: center;
  }

  .matrix-permission-header {
    padding: 6px 4px;
    background: #f6f8fa;
    border-bottom: 1px solid #d0d7de;
    border-right: 1px solid #d0d7de;
    font-weight: 600;
    font-size: 10px;
    color: #24292f;
    text-align: center;
    display: flex;
    align-items: center;
    justify-content: center;
    cursor: help;
    line-height: 1.2;
  }

  .matrix-permission-header:last-child {
    border-right: none;
  }

  .matrix-row {
    display: contents;
  }

  .matrix-row:nth-child(even) .matrix-area-cell,
  .matrix-row:nth-child(even) .matrix-permission-cell {
    background: #f8f9fa;
  }

  .matrix-area-cell {
    padding: 6px 12px;
    border-bottom: 1px solid #d0d7de;
    border-right: 1px solid #d0d7de;
    display: flex;
    flex-direction: column;
    gap: 1px;
    cursor: help;
  }

  .area-label {
    font-weight: 600;
    font-size: var(--font-size-xs);
    color: #24292f;
    line-height: 1.3;
  }

  .area-description {
    font-size: 10px;
    color: #656d76;
    line-height: 1.2;
  }

  .matrix-permission-cell {
    padding: 6px 4px;
    border-bottom: 1px solid #d0d7de;
    border-right: 1px solid #d0d7de;
    display: flex;
    align-items: center;
    justify-content: center;
  }

  .matrix-permission-cell:last-child {
    border-right: none;
  }

  .matrix-checkbox {
    width: 14px;
    height: 14px;
    accent-color: var(--primary-blue);
    cursor: pointer;
  }

  .matrix-checkbox:hover {
    transform: scale(1.1);
    transition: transform 0.1s ease;
  }

  .matrix-unavailable {
    color: #d0d7de;
    font-size: 12px;
    font-weight: bold;
    user-select: none;
  }

  .permission-matrix-summary {
    padding: 6px 12px;
    background: #f6f8fa;
    border-top: 1px solid #d0d7de;
    font-size: 10px;
    color: #656d76;
    text-align: center;
  }

  /* Responsive adjustments for smaller screens */
  @media (max-width: 768px) {
    .permission-matrix {
      grid-template-columns: 120px repeat(5, 1fr);
      font-size: 10px;
    }
    
    .matrix-area-header,
    .matrix-permission-header {
      padding: 4px 2px;
      font-size: 9px;
    }
    
    .matrix-area-cell {
      padding: 4px 8px;
    }
    
    .matrix-permission-cell {
      padding: 4px 2px;
    }
    
    .matrix-checkbox {
      width: 12px;
      height: 12px;
    }
    
    .area-description {
      display: none; /* Hide descriptions on small screens */
    }
  }
`;

export default RoleSpreadsheetForm;