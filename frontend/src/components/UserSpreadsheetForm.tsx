import React, { useState, useEffect } from 'react';
import { User } from '../types';
import { rolesApi } from '../services/api';

interface UserSpreadsheetFormProps {
  user?: User;
  onSave: (userData: any) => void;
  onCancel: () => void;
  mode: 'create' | 'edit' | 'view';
}

interface FieldDefinition {
  field: string;
  label: string;
  type: 'text' | 'email' | 'password' | 'dropdown' | 'tel' | 'checkbox' | 'textarea';
  options?: string[];
  required?: boolean;
  section: string;
  placeholder?: string;
  validation?: (value: any) => string | null;
  conditional?: (formData: any) => boolean;
}

const UserSpreadsheetForm: React.FC<UserSpreadsheetFormProps> = ({ user, onSave, onCancel, mode }) => {
  const [roles, setRoles] = useState<Array<{id: number, name: string, description: string}>>([]);
  const [errors, setErrors] = useState<Record<string, string>>({});
  
  // Check if this is the admin user account
  const isAdminUser = user?.username === 'admin';
  
  const [formData, setFormData] = useState<Record<string, any>>({
    // Basic Information
    username: user?.username || '',
    email: user?.email || '',
    first_name: user?.first_name || '',
    last_name: user?.last_name || '',
    
    // Contact Information
    telephone: user?.telephone || '',
    title: user?.title || '',
    
    // Authentication & Access
    role: user?.role || '',
    password: '', // Never pre-populate passwords for security
    confirmPassword: '',
    is_active: user?.is_active !== undefined ? user.is_active : true,
    
    // System Information (view mode only)
    created_at: user?.created_at || '',
    updated_at: user?.updated_at || '',
    last_login: user?.last_login || '',
  });

  // Field definitions organized by sections (matching assets pattern)
  const fieldDefinitions: FieldDefinition[] = [
    // Basic Information Section
    { 
      field: 'username', 
      label: 'Username', 
      type: 'text', 
      required: true, 
      section: 'Basic Information', 
      placeholder: isAdminUser ? 'Admin username cannot be changed' : 'Enter a unique username for system access',
      validation: (value) => {
        if (!value || value.trim().length < 3) {
          return 'Username must be at least 3 characters';
        }
        if (!/^[a-zA-Z0-9._-]+$/.test(value)) {
          return 'Username can only contain letters, numbers, dots, underscores, and hyphens';
        }
        return null;
      }
    },
    { 
      field: 'email', 
      label: 'Email Address', 
      type: 'email', 
      required: true, 
      section: 'Basic Information', 
      placeholder: 'user@company.com',
      validation: (value) => {
        if (!value) return null;
        if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(value)) {
          return 'Please enter a valid email address';
        }
        return null;
      }
    },
    { 
      field: 'first_name', 
      label: 'First Name', 
      type: 'text', 
      required: false, 
      section: 'Basic Information', 
      placeholder: isAdminUser ? 'Admin first name cannot be changed' : 'John, Sarah, Michael, etc.'
    },
    { 
      field: 'last_name', 
      label: 'Last Name', 
      type: 'text', 
      required: false, 
      section: 'Basic Information', 
      placeholder: isAdminUser ? 'Admin last name cannot be changed' : 'Smith, Johnson, Williams, etc.'
    },
    { 
      field: 'telephone', 
      label: 'Phone Number', 
      type: 'tel', 
      required: false, 
      section: 'Basic Information', 
      placeholder: '+1 (555) 123-4567'
    },
    { 
      field: 'title', 
      label: 'Job Title', 
      type: 'text', 
      required: false, 
      section: 'Basic Information', 
      placeholder: isAdminUser ? 'Admin job title cannot be changed' : 'System Administrator'
    },
    
    // Authentication & Access Section
    { 
      field: 'role', 
      label: 'User Role', 
      type: 'dropdown', 
      required: true, 
      section: 'Authentication & Access', 
      options: roles.map(role => role.name)
    },
    { 
      field: 'password', 
      label: mode === 'edit' ? 'New Password' : 'Password', 
      type: 'password', 
      required: mode === 'create', 
      section: 'Authentication & Access', 
      placeholder: mode === 'edit' ? 'Leave blank to keep current password' : 'Enter secure password',
      conditional: (formData) => mode !== 'view',
      validation: (value) => {
        if (mode === 'create' && (!value || value.length < 6)) {
          return 'Password must be at least 6 characters';
        }
        if (mode === 'edit' && value && value.length < 6) {
          return 'Password must be at least 6 characters';
        }
        return null;
      }
    },
    { 
      field: 'confirmPassword', 
      label: 'Confirm Password', 
      type: 'password', 
      required: false, 
      section: 'Authentication & Access', 
      placeholder: 'Confirm password',
      conditional: (formData) => mode !== 'view' && (mode === 'create' || formData.password),
      validation: (value) => {
        if (formData.password && value !== formData.password) {
          return 'Passwords do not match';
        }
        return null;
      }
    },
    { 
      field: 'is_active', 
      label: 'Account Status', 
      type: 'checkbox', 
      required: false, 
      section: 'Authentication & Access'
    },
    
    // System Information Section (view mode only)
    { 
      field: 'created_at', 
      label: 'Created Date', 
      type: 'text', 
      required: false, 
      section: 'System Information',
      conditional: (formData) => mode === 'view'
    },
    { 
      field: 'updated_at', 
      label: 'Last Updated', 
      type: 'text', 
      required: false, 
      section: 'System Information',
      conditional: (formData) => mode === 'view'
    },
    { 
      field: 'last_login', 
      label: 'Last Login', 
      type: 'text', 
      required: false, 
      section: 'System Information',
      conditional: (formData) => mode === 'view'
    },
  ];

  // Load roles on component mount
  useEffect(() => {
    const fetchRoles = async () => {
      try {
        console.log('Fetching roles...');
        const response = await rolesApi.list();
        console.log('Roles API response:', response);
        if (response.data.success) {
          const rolesData = response.data.data || [];
          console.log('Setting roles:', rolesData);
          setRoles(rolesData);
        }
      } catch (error) {
        console.error('Failed to fetch roles:', error);
        // Fallback to default roles if API fails
        const fallbackRoles = [
          { id: 1, name: 'admin', description: 'System Administrator' },
          { id: 2, name: 'manager', description: 'Manager' },
          { id: 3, name: 'operator', description: 'System Operator' },
          { id: 4, name: 'developer', description: 'Developer' },
          { id: 5, name: 'viewer', description: 'Read-only User' }
        ];
        console.log('Using fallback roles:', fallbackRoles);
        setRoles(fallbackRoles);
      }
    };
    fetchRoles();
  }, []);



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
      if (fieldDef.required && (!value || value === '')) {
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
    
    // Remove confirmPassword from save data
    delete saveData.confirmPassword;
    
    // Remove system fields from save data
    delete saveData.created_at;
    delete saveData.updated_at;
    delete saveData.last_login;
    
    // Admin user restrictions: only allow saving email, telephone, and password
    if (isAdminUser && mode === 'edit') {
      const allowedFields = ['email', 'telephone', 'password'];
      const restrictedSaveData: Record<string, any> = {};
      
      // Only include allowed fields for admin user
      allowedFields.forEach(field => {
        if (saveData[field] !== undefined) {
          restrictedSaveData[field] = saveData[field];
        }
      });
      
      // Always include the user ID for updates
      if (user?.id) {
        restrictedSaveData.id = user.id;
      }
      
      // Only include password if it was changed (for edit mode)
      if (!restrictedSaveData.password) {
        delete restrictedSaveData.password;
      }
      
      onSave(restrictedSaveData);
      return;
    }
    
    // Only include password if it was changed (for edit mode)
    if (mode === 'edit' && !saveData.password) {
      delete saveData.password;
    }

    onSave(saveData);
  };

  const renderFieldValue = (fieldDef: FieldDefinition) => {
    const value = formData[fieldDef.field];
    const isReadOnly = mode === 'view';
    const hasError = errors[fieldDef.field];

    // Admin user restrictions: only allow editing email, telephone, and password
    const isAdminRestricted = isAdminUser && mode === 'edit' && 
      !['email', 'telephone', 'password', 'confirmPassword'].includes(fieldDef.field);

    // Format display values for view mode
    let displayValue = value;
    if (isReadOnly) {
      if (fieldDef.field === 'created_at' && value) {
        displayValue = new Date(value).toLocaleString();
      } else if (fieldDef.field === 'updated_at' && value) {
        displayValue = new Date(value).toLocaleString();
      } else if (fieldDef.field === 'last_login' && value) {
        displayValue = new Date(value).toLocaleString();
      } else if (fieldDef.field === 'is_active') {
        displayValue = value ? 'Active' : 'Inactive';
      }
    }

    switch (fieldDef.type) {
      case 'text':
      case 'email':
      case 'tel':
        return (
          <input
            type={fieldDef.type}
            value={displayValue || ''}
            onChange={(e) => handleFieldChange(fieldDef.field, e.target.value)}
            readOnly={isReadOnly || isAdminRestricted}
            className={`field-input ${hasError ? 'error' : ''} ${isAdminRestricted ? 'admin-restricted' : ''}`}
            placeholder={isReadOnly ? '' : fieldDef.placeholder}
          />
        );
      
      case 'password':
        return (
          <input
            type={isReadOnly ? 'text' : 'password'}
            value={displayValue || ''}
            onChange={(e) => handleFieldChange(fieldDef.field, e.target.value)}
            readOnly={isReadOnly || isAdminRestricted}
            className={`field-input ${hasError ? 'error' : ''} ${isAdminRestricted ? 'admin-restricted' : ''}`}
            placeholder={isReadOnly ? '' : fieldDef.placeholder}
          />
        );
      
      case 'textarea':
        return (
          <textarea
            value={displayValue || ''}
            onChange={(e) => handleFieldChange(fieldDef.field, e.target.value)}
            readOnly={isReadOnly || isAdminRestricted}
            className={`field-textarea ${hasError ? 'error' : ''} ${isAdminRestricted ? 'admin-restricted' : ''}`}
            placeholder={isReadOnly ? '' : fieldDef.placeholder}
            rows={3}
          />
        );
      
      case 'dropdown':
        if (isReadOnly || isAdminRestricted) {
          return (
            <input
              type="text"
              value={displayValue || ''}
              readOnly={true}
              className={`field-input ${isAdminRestricted ? 'admin-restricted' : ''}`}
            />
          );
        }
        console.log(`Dropdown for ${fieldDef.field}:`, fieldDef.options);
        return (
          <select
            value={displayValue || ''}
            onChange={(e) => handleFieldChange(fieldDef.field, e.target.value)}
            className={`field-input ${hasError ? 'error' : ''}`}
          >
            <option value="">Select {fieldDef.label.toLowerCase()}...</option>
            {(fieldDef.options || []).map((option, index) => (
              <option key={index} value={option}>
                {option.charAt(0).toUpperCase() + option.slice(1)}
              </option>
            ))}
          </select>
        );
      
      case 'checkbox':
        if (isReadOnly || isAdminRestricted) {
          return (
            <input
              type="text"
              value={displayValue}
              readOnly={true}
              className={`field-input ${isAdminRestricted ? 'admin-restricted' : ''}`}
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
      
      default:
        return (
          <input
            type="text"
            value={displayValue || ''}
            onChange={(e) => handleFieldChange(fieldDef.field, e.target.value)}
            readOnly={isReadOnly || isAdminRestricted}
            className={`field-input ${hasError ? 'error' : ''} ${isAdminRestricted ? 'admin-restricted' : ''}`}
            placeholder={isReadOnly ? '' : fieldDef.placeholder}
          />
        );
    }
  };

  // Organize sections into two columns
  const leftColumnSections = [
    'Basic Information',
    'Contact Information'
  ];
  const rightColumnSections = [
    'Authentication & Access',
    'System Information'
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
                <div key={fieldDef.field} className="field-row">
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
                </div>
              ))}
            </div>
          </div>
        );
      })}
    </div>
  );

  return (
    <div className="user-spreadsheet-form">
      {isAdminUser && mode === 'edit' && (
        <div className="admin-warning">
          <div className="admin-warning-icon">⚠️</div>
          <div className="admin-warning-text">
            <strong>Admin User Account</strong>
            <br />
            Only email address, phone number, and password can be modified for security reasons.
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
            {mode === 'create' ? 'Create User' : 'Save Changes'}
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
  .user-spreadsheet-form {
    display: flex;
    flex-direction: column;
    height: 100%;
    background: white;
  }

  .admin-warning {
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

  .admin-warning-icon {
    font-size: 20px;
    flex-shrink: 0;
  }

  .admin-warning-text {
    font-size: var(--font-size-sm);
    line-height: 1.4;
  }

  .admin-warning-text strong {
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
    align-items: center;
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
    align-items: center;
    padding: 4px 8px;
    position: relative;
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

  /* Admin restricted fields styling */
  .field-input.admin-restricted, .field-textarea.admin-restricted {
    background: #f8f9fa !important;
    color: #6c757d !important;
    cursor: not-allowed;
    border: 1px solid #e9ecef;
    border-radius: 2px;
    padding: 2px 4px;
  }

  .field-input.admin-restricted:focus, .field-textarea.admin-restricted:focus {
    background: #f8f9fa !important;
    outline: none;
    box-shadow: none;
  }

  /* Subtle placeholder styling - matching asset form */
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
`;

export default UserSpreadsheetForm;