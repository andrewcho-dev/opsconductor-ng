import React, { useState, useEffect } from 'react';
import { User } from '../types';
import { rolesApi } from '../services/api';

interface UserSpreadsheetFormProps {
  user?: User; // For edit mode
  onSave: (userData: any) => void;
  onCancel: () => void;
  mode: 'create' | 'edit' | 'view';
}

interface FieldDefinition {
  field: string;
  label: string;
  type: 'text' | 'email' | 'password' | 'dropdown' | 'tel';
  options?: string[];
  required?: boolean;
  section: string;
  placeholder?: string;
  validation?: (value: any) => string | null;
}

const UserSpreadsheetForm: React.FC<UserSpreadsheetFormProps> = ({ user, onSave, onCancel, mode }) => {
  const [roles, setRoles] = useState<Array<{id: number, name: string, description: string}>>([]);
  
  const [formData, setFormData] = useState<Record<string, any>>({
    // Basic Information
    username: user?.username || '',
    email: user?.email || '',
    first_name: user?.first_name || '',
    last_name: user?.last_name || '',
    
    // Contact Information
    telephone: user?.telephone || '',
    title: user?.title || '',
    
    // Authentication
    role: user?.role || '',
    password: '', // Never pre-populate passwords for security
    confirmPassword: '',
    
    // Status
    is_active: user?.is_active !== undefined ? user.is_active : true,
  });

  // Field definitions organized by sections
  const fieldDefinitions: FieldDefinition[] = [
    // Basic Information Section
    { field: 'username', label: 'Username', type: 'text', required: true, section: 'Basic Information', placeholder: 'Enter username' },
    { field: 'email', label: 'Email Address', type: 'email', required: true, section: 'Basic Information', placeholder: 'user@company.com' },
    { field: 'first_name', label: 'First Name', type: 'text', required: false, section: 'Basic Information', placeholder: 'First name' },
    { field: 'last_name', label: 'Last Name', type: 'text', required: false, section: 'Basic Information', placeholder: 'Last name' },
    
    // Contact Information Section
    { field: 'telephone', label: 'Phone Number', type: 'tel', required: false, section: 'Contact Information', placeholder: '+1 (555) 123-4567' },
    { field: 'title', label: 'Job Title', type: 'text', required: false, section: 'Contact Information', placeholder: 'System Administrator' },
    
    // Authentication Section
    { field: 'role', label: 'Role', type: 'dropdown', required: true, section: 'Authentication', options: [] },
    { field: 'password', label: mode === 'edit' ? 'New Password (leave blank to keep current)' : 'Password', type: 'password', required: mode === 'create', section: 'Authentication', placeholder: mode === 'edit' ? 'Leave blank to keep current password' : 'Enter secure password' },
    { field: 'confirmPassword', label: 'Confirm Password', type: 'password', required: false, section: 'Authentication', placeholder: 'Confirm password' },
  ];

  // Load roles on component mount
  useEffect(() => {
    const fetchRoles = async () => {
      try {
        const response = await rolesApi.list();
        if (response.data.success) {
          setRoles(response.data.data || []);
        }
      } catch (error) {
        console.error('Failed to fetch roles:', error);
        // Fallback to default roles if API fails
        setRoles([
          { id: 1, name: 'admin', description: 'System Administrator' },
          { id: 2, name: 'manager', description: 'Manager' },
          { id: 3, name: 'operator', description: 'System Operator' },
          { id: 4, name: 'developer', description: 'Developer' },
          { id: 5, name: 'viewer', description: 'Read-only User' }
        ]);
      }
    };
    fetchRoles();
  }, []);

  // Update role options when roles are loaded
  useEffect(() => {
    const roleField = fieldDefinitions.find(f => f.field === 'role');
    if (roleField) {
      roleField.options = roles.map(role => `${role.name}:${role.name.charAt(0).toUpperCase() + role.name.slice(1)} - ${role.description}`);
    }
  }, [roles]);

  const handleInputChange = (field: string, value: any) => {
    setFormData(prev => ({
      ...prev,
      [field]: value
    }));
  };

  const validateForm = (): string[] => {
    const errors: string[] = [];
    
    // Check required fields
    fieldDefinitions.forEach(fieldDef => {
      if (fieldDef.required && !formData[fieldDef.field]?.toString().trim()) {
        errors.push(`${fieldDef.label} is required`);
      }
    });

    // Email validation
    if (formData.email && !/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(formData.email)) {
      errors.push('Please enter a valid email address');
    }

    // Password validation
    if (mode === 'create' || (mode === 'edit' && formData.password)) {
      if (formData.password && formData.password.length < 6) {
        errors.push('Password must be at least 6 characters long');
      }
      if (formData.password !== formData.confirmPassword) {
        errors.push('Passwords do not match');
      }
    }

    return errors;
  };

  const handleSave = () => {
    const errors = validateForm();
    if (errors.length > 0) {
      alert('Please fix the following errors:\n' + errors.join('\n'));
      return;
    }

    const saveData = { ...formData };
    
    // Extract role name from dropdown value
    if (saveData.role && saveData.role.includes(':')) {
      saveData.role = saveData.role.split(':')[0];
    }
    
    // Remove confirmPassword from save data
    delete saveData.confirmPassword;
    
    // Only include password if it was changed (for edit mode)
    if (mode === 'edit' && !saveData.password) {
      delete saveData.password;
    }

    onSave(saveData);
  };

  // Group fields by section
  const fieldsBySection = fieldDefinitions.reduce((acc, field) => {
    if (!acc[field.section]) {
      acc[field.section] = [];
    }
    acc[field.section].push(field);
    return acc;
  }, {} as Record<string, FieldDefinition[]>);

  const renderField = (fieldDef: FieldDefinition) => {
    const isReadOnly = mode === 'view';
    const value = formData[fieldDef.field] || '';

    return (
      <div key={fieldDef.field} className="form-field">
        <label className={`form-label ${fieldDef.required ? 'required' : ''}`}>
          {fieldDef.label}
        </label>
        
        {fieldDef.type === 'dropdown' ? (
          <select
            className="form-input"
            value={value}
            onChange={(e) => handleInputChange(fieldDef.field, e.target.value)}
            disabled={isReadOnly}
          >
            <option value="">Select {fieldDef.label.toLowerCase()}...</option>
            {(fieldDef.options || []).map((option, index) => {
              const [optionValue, optionLabel] = option.includes(':') ? option.split(':') : [option, option];
              return (
                <option key={index} value={optionValue}>
                  {optionLabel}
                </option>
              );
            })}
          </select>
        ) : fieldDef.type === 'password' ? (
          <input
            type="password"
            className="form-input"
            value={value}
            onChange={(e) => handleInputChange(fieldDef.field, e.target.value)}
            placeholder={fieldDef.placeholder}
            readOnly={isReadOnly}
          />
        ) : (
          <input
            type={fieldDef.type}
            className="form-input"
            value={value}
            onChange={(e) => handleInputChange(fieldDef.field, e.target.value)}
            placeholder={fieldDef.placeholder}
            readOnly={isReadOnly}
          />
        )}
      </div>
    );
  };

  return (
    <div className="user-spreadsheet-form">
      <style>
        {`
          .user-spreadsheet-form {
            padding: 12px;
            height: 100%;
            overflow-y: auto;
          }
          
          .form-section {
            margin-bottom: 24px;
          }
          
          .section-title {
            font-size: 13px;
            font-weight: 600;
            color: var(--neutral-700);
            margin-bottom: 12px;
            padding-bottom: 6px;
            border-bottom: 1px solid var(--neutral-200);
          }
          
          .form-grid {
            display: grid;
            grid-template-columns: 1fr 1fr 1fr;
            gap: 16px;
          }
          
          .form-field {
            margin-bottom: 16px;
          }
          
          .form-label {
            display: block;
            font-size: 12px;
            font-weight: 600;
            color: var(--neutral-700);
            margin-bottom: 4px;
          }
          
          .form-label.required::after {
            content: ' *';
            color: var(--danger-red);
          }
          
          .form-input {
            width: 100%;
            padding: 8px 12px;
            border: 1px solid var(--neutral-300);
            border-radius: 4px;
            font-size: 13px;
            color: var(--neutral-900);
            transition: border-color 0.2s;
          }
          
          .form-input:focus {
            outline: none;
            border-color: var(--primary-blue);
            box-shadow: 0 0 0 2px var(--primary-blue-light);
          }
          
          .form-input[readonly], .form-input:disabled {
            background-color: var(--neutral-50);
            color: var(--neutral-700);
            cursor: default;
          }
          
          .form-actions {
            display: flex;
            gap: 8px;
            margin-top: 24px;
            padding-top: 16px;
            border-top: 1px solid var(--neutral-200);
          }
          
          .btn {
            padding: 8px 16px;
            border: none;
            border-radius: 4px;
            font-size: 13px;
            font-weight: 500;
            cursor: pointer;
            transition: all 0.2s;
          }
          
          .btn-primary {
            background: var(--primary-blue);
            color: white;
          }
          
          .btn-primary:hover {
            background: var(--primary-blue-dark);
          }
          
          .btn-secondary {
            background: var(--neutral-200);
            color: var(--neutral-700);
          }
          
          .btn-secondary:hover {
            background: var(--neutral-300);
          }
        `}
      </style>

      {Object.entries(fieldsBySection).map(([sectionName, fields]) => (
        <div key={sectionName} className="form-section">
          <div className="section-title">{sectionName}</div>
          <div className="form-grid">
            {fields.map(renderField)}
          </div>
        </div>
      ))}

      {mode !== 'view' && (
        <div className="form-actions">
          <button className="btn btn-primary" onClick={handleSave}>
            {mode === 'create' ? 'Create User' : 'Update User'}
          </button>
          <button className="btn btn-secondary" onClick={onCancel}>
            Cancel
          </button>
        </div>
      )}
    </div>
  );
};

export default UserSpreadsheetForm;