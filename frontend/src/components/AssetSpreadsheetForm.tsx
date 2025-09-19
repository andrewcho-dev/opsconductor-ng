import React, { useState } from 'react';
import { Asset } from '../types/asset';

interface AssetSpreadsheetFormProps {
  asset?: Asset; // For edit mode
  onSave: (assetData: any) => void;
  onCancel: () => void;
  mode: 'create' | 'edit' | 'view';
}

interface FieldDefinition {
  field: string;
  label: string;
  type: 'text' | 'number' | 'boolean' | 'dropdown' | 'tags' | 'textarea' | 'password';
  options?: string[];
  required?: boolean;
  section: string;
  placeholder?: string;
  validation?: (value: any) => string | null;
  conditional?: (formData: any) => boolean;
}

const AssetSpreadsheetForm: React.FC<AssetSpreadsheetFormProps> = ({ asset, onSave, onCancel, mode }) => {
  // State to track existing credentials for visual indicators
  const [hasExistingCredentials, setHasExistingCredentials] = useState<{
    password?: boolean;
    private_key?: boolean;
    api_key?: boolean;
    bearer_token?: boolean;
    secondary_password?: boolean;
  }>({});

  // Helper function to derive device type from service type
  const getDeviceTypeFromService = (serviceType: string, osType: string): string => {
    switch (serviceType?.toLowerCase()) {
      case 'ssh':
        return osType === 'windows' ? 'server' : 'server';
      case 'rdp':
        return 'workstation';
      case 'http':
      case 'https':
        return 'web-server';
      case 'database':
        return 'database';
      case 'ftp':
      case 'sftp':
        return 'storage';
      default:
        return 'server';
    }
  };

  const [formData, setFormData] = useState<Record<string, any>>({
    // Basic Information (from database schema)
    name: asset?.name || '',
    hostname: asset?.hostname || '',
    ip_address: asset?.ip_address || '',
    description: asset?.description || '',
    tags: asset?.tags || [],
    
    // Device/Hardware Information (from our comprehensive schema)
    device_type: asset?.device_type || '',
    hardware_make: asset?.hardware_make || '',
    hardware_model: asset?.hardware_model || '',
    serial_number: asset?.serial_number || '',
    
    // System Information
    os_type: asset?.os_type || 'linux',
    os_version: asset?.os_version || '',
    
    // Location Information (from our comprehensive schema)
    physical_address: asset?.physical_address || '',
    data_center: asset?.data_center || '',
    building: asset?.building || '',
    room: asset?.room || '',
    rack_position: asset?.rack_position || '',
    rack_location: asset?.rack_location || '',
    gps_coordinates: asset?.gps_coordinates || '',
    
    // Status & Management (from our comprehensive schema)
    status: asset?.status || 'active',
    environment: asset?.environment || 'production',
    criticality: asset?.criticality || 'medium',
    owner: asset?.owner || '',
    support_contact: asset?.support_contact || '',
    contract_number: asset?.contract_number || '',
    
    // Primary Communication Service
    service_type: asset?.service_type || 'ssh',
    port: asset?.port || 22,
    is_secure: asset?.is_secure || false,
    
    // Primary Service Credentials
    credential_type: asset?.credential_type || '',
    username: asset?.username || '',
    password: '', // Never pre-populate passwords for security
    private_key: '', // Never pre-populate keys for security
    public_key: asset?.public_key || '',
    api_key: '', // Never pre-populate API keys for security
    bearer_token: '', // Never pre-populate tokens for security
    certificate: '', // Never pre-populate certificates for security
    passphrase: '', // Never pre-populate passphrases for security
    domain: asset?.domain || '',
    
    // Database-specific fields (from our comprehensive schema)
    database_type: asset?.database_type || '',
    database_name: asset?.database_name || '',
    
    // Secondary Communication (from our comprehensive schema)
    secondary_service_type: asset?.secondary_service_type || '',
    secondary_port: asset?.secondary_port || null,
    ftp_type: asset?.ftp_type || '',
    secondary_username: asset?.secondary_username || '',
    secondary_password: '', // Never pre-populate passwords for security
    
    // Additional Information
    additional_services: asset?.additional_services || [],
    notes: asset?.notes || '',
    
    // System fields
    is_active: asset?.is_active !== false, // Default to true
    
    // Legacy fields (for backward compatibility)
    has_credentials: asset?.has_credentials || false,
    additional_services_count: asset?.additional_services_count || 0,
  });

  const [errors, setErrors] = useState<Record<string, string>>({});

  // Detect existing credentials when asset data is loaded
  React.useEffect(() => {
    if (asset && (mode === 'edit' || mode === 'view')) {
      const credentialType = asset.credential_type;
      const secondaryCredentialType = (asset as any).secondary_credential_type;
      
      // Detect existing credentials based on credential_type being set
      const existingCreds: any = {};
      
      if (credentialType) {
        switch (credentialType) {
          case 'username_password':
            existingCreds.password = true;
            break;
          case 'ssh_key':
            existingCreds.private_key = true;
            break;
          case 'api_key':
            existingCreds.api_key = true;
            break;
          case 'bearer_token':
            existingCreds.bearer_token = true;
            break;
        }
      }
      
      if (secondaryCredentialType === 'username_password') {
        existingCreds.secondary_password = true;
      }
      
      setHasExistingCredentials(existingCreds);
    }
  }, [asset, mode]);

  // COMPREHENSIVE FIELD DEFINITIONS - RESTORED TO YOUR PERFECT ORGANIZATION
  const fieldDefinitions: FieldDefinition[] = [
    // ========== BASIC ASSET INFORMATION ==========
    { 
      field: 'name', 
      label: 'Asset Name', 
      type: 'text', 
      section: 'Basic Asset Information',
      placeholder: 'Enter a descriptive name for this asset'
    },
    { 
      field: 'ip_address', 
      label: 'IP Address', 
      type: 'text', 
      section: 'Basic Asset Information',
      placeholder: '192.168.1.100',
      validation: (value) => {
        if (!value) return null;
        const ipRegex = /^(?:(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)$/;
        return !ipRegex.test(value) ? 'Please enter a valid IP address' : null;
      }
    },
    { 
      field: 'hostname', 
      label: 'Hostname', 
      type: 'text', 
      section: 'Basic Asset Information',
      placeholder: 'server.example.com'
    },
    { 
      field: 'description', 
      label: 'Description', 
      type: 'textarea', 
      section: 'Basic Asset Information',
      placeholder: 'Brief description of this asset...'
    },
    { 
      field: 'device_type', 
      label: 'Device Type', 
      type: 'dropdown', 
      options: ['server', 'workstation', 'router', 'switch', 'firewall', 'database', 'web-server', 'application-server', 'storage', 'other'], 
      section: 'Basic Asset Information'
    },
    { 
      field: 'tags', 
      label: 'Tags', 
      type: 'tags', 
      section: 'Basic Asset Information',
      placeholder: 'production, web-server, critical (comma-separated)'
    },
    
    // ========== LOCATION INFORMATION ==========
    { 
      field: 'physical_address', 
      label: 'Physical Address', 
      type: 'textarea', 
      section: 'Location Information',
      placeholder: '123 Main St, City, State, ZIP'
    },
    { 
      field: 'data_center', 
      label: 'Data Center', 
      type: 'text', 
      section: 'Location Information',
      placeholder: 'DC-East-01, Primary Data Center, etc.'
    },
    { 
      field: 'building', 
      label: 'Building', 
      type: 'text', 
      section: 'Location Information',
      placeholder: 'Building A, Main Campus, etc.'
    },
    { 
      field: 'room', 
      label: 'Room', 
      type: 'text', 
      section: 'Location Information',
      placeholder: 'Server Room 101, Basement, etc.'
    },
    { 
      field: 'rack_position', 
      label: 'Rack Position', 
      type: 'text', 
      section: 'Location Information',
      placeholder: 'Rack 15, U24-U26'
    },
    { 
      field: 'gps_coordinates', 
      label: 'GPS Coordinates', 
      type: 'text', 
      section: 'Location Information',
      placeholder: '40.7128, -74.0060 (latitude, longitude)',
      validation: (value) => {
        if (!value) return null;
        const gpsRegex = /^-?\d+\.?\d*,\s*-?\d+\.?\d*$/;
        return !gpsRegex.test(value) ? 'Please enter coordinates as: latitude, longitude' : null;
      }
    },
    
    // ========== SYSTEM INFORMATION ==========
    { 
      field: 'hardware_make', 
      label: 'Hardware Make', 
      type: 'text', 
      section: 'System Information',
      placeholder: 'Dell, HP, Cisco, VMware, etc.'
    },
    { 
      field: 'hardware_model', 
      label: 'Hardware Model', 
      type: 'text', 
      section: 'System Information',
      placeholder: 'PowerEdge R740, ProLiant DL380, etc.'
    },
    { 
      field: 'serial_number', 
      label: 'Serial Number', 
      type: 'text', 
      section: 'System Information',
      placeholder: 'ABC123DEF456'
    },
    { 
      field: 'os_type', 
      label: 'OS Type', 
      type: 'dropdown', 
      options: ['linux', 'windows', 'macos', 'unix', 'freebsd', 'solaris', 'aix', 'other'], 
      section: 'System Information'
    },
    { 
      field: 'os_version', 
      label: 'OS Version', 
      type: 'text', 
      section: 'System Information',
      placeholder: 'Ubuntu 22.04, Windows Server 2019, etc.'
    },
    
    // ========== STATUS & MANAGEMENT ==========
    { 
      field: 'status', 
      label: 'Status', 
      type: 'dropdown', 
      options: ['active', 'inactive', 'maintenance', 'decommissioned'], 
      section: 'Status & Management'
    },
    { 
      field: 'environment', 
      label: 'Environment', 
      type: 'dropdown', 
      options: ['production', 'staging', 'development', 'testing', 'qa'], 
      section: 'Status & Management'
    },
    { 
      field: 'criticality', 
      label: 'Criticality', 
      type: 'dropdown', 
      options: ['low', 'medium', 'high', 'critical'], 
      section: 'Status & Management'
    },
    { 
      field: 'owner', 
      label: 'Owner', 
      type: 'text', 
      section: 'Status & Management',
      placeholder: 'IT Operations Team, John Doe, etc.'
    },
    { 
      field: 'support_contact', 
      label: 'Support Contact', 
      type: 'text', 
      section: 'Status & Management',
      placeholder: 'support@company.com, +1-555-123-4567'
    },
    { 
      field: 'contract_number', 
      label: 'Contract Number', 
      type: 'text', 
      section: 'Status & Management',
      placeholder: 'SUPP-2024-001'
    },
    
    // ========== PRIMARY SERVICE & CREDENTIALS ==========
    { 
      field: 'service_type', 
      label: 'Service Type', 
      type: 'dropdown', 
      options: ['ssh', 'winrm', 'api', 'database'], 
      required: true, 
      section: 'Primary Service & Credentials'
    },
    { 
      field: 'port', 
      label: 'Port', 
      type: 'number', 
      section: 'Primary Service & Credentials',
      placeholder: 'Auto-populated based on service type'
    },
    { 
      field: 'credential_type', 
      label: 'Credential Type', 
      type: 'dropdown', 
      options: [], // Will be populated dynamically based on service_type
      section: 'Primary Service & Credentials',
      conditional: (formData) => !!formData.service_type
    },
    { 
      field: 'username', 
      label: 'Username', 
      type: 'text', 
      section: 'Primary Service & Credentials',
      placeholder: 'Enter username',
      conditional: (formData) => ['username_password', 'ssh_key'].includes(formData.credential_type)
    },
    { 
      field: 'password', 
      label: 'Password', 
      type: 'password', 
      section: 'Primary Service & Credentials',
      placeholder: 'Enter password (will be encrypted)',
      conditional: (formData) => formData.credential_type === 'username_password'
    },
    { 
      field: 'private_key', 
      label: 'SSH Private Key', 
      type: 'textarea', 
      section: 'Primary Service & Credentials',
      placeholder: 'Paste SSH private key here (will be encrypted)',
      conditional: (formData) => formData.credential_type === 'ssh_key'
    },
    { 
      field: 'api_key', 
      label: 'API Key', 
      type: 'password', 
      section: 'Primary Service & Credentials',
      placeholder: 'Enter API key (will be encrypted)',
      conditional: (formData) => formData.credential_type === 'api_key'
    },
    { 
      field: 'bearer_token', 
      label: 'Bearer Token', 
      type: 'password', 
      section: 'Primary Service & Credentials',
      placeholder: 'Enter bearer token (will be encrypted)',
      conditional: (formData) => formData.credential_type === 'bearer_token'
    },
    
    // ========== DATABASE INFORMATION ==========
    { 
      field: 'database_type', 
      label: 'Database Type', 
      type: 'dropdown', 
      options: ['mysql', 'postgresql', 'mssql', 'oracle', 'mongodb', 'redis'], 
      section: 'Database Information',
      conditional: (formData) => formData.service_type === 'database'
    },
    { 
      field: 'database_name', 
      label: 'Database Name', 
      type: 'text', 
      section: 'Database Information',
      placeholder: 'production_db',
      conditional: (formData) => formData.service_type === 'database'
    },
    
    // ========== SECONDARY COMMUNICATION ==========
    { 
      field: 'secondary_service_type', 
      label: 'Secondary Service Type', 
      type: 'dropdown', 
      options: ['none', 'ftp', 'sftp', 'telnet', 'wmi', 'rdp', 'vnc'], 
      section: 'Secondary Communication'
    },
    { 
      field: 'secondary_port', 
      label: 'Secondary Port', 
      type: 'number', 
      section: 'Secondary Communication',
      placeholder: 'Auto-populated based on service type',
      conditional: (formData) => formData.secondary_service_type && formData.secondary_service_type !== 'none'
    },
    { 
      field: 'secondary_credential_type', 
      label: 'Secondary Credential Type', 
      type: 'dropdown', 
      options: [], // Will be populated dynamically based on secondary_service_type
      section: 'Secondary Communication',
      conditional: (formData) => formData.secondary_service_type && formData.secondary_service_type !== 'none'
    },
    { 
      field: 'secondary_username', 
      label: 'Secondary Username', 
      type: 'text', 
      section: 'Secondary Communication',
      placeholder: 'Enter username',
      conditional: (formData) => formData.secondary_credential_type === 'username_password'
    },
    { 
      field: 'secondary_password', 
      label: 'Secondary Password', 
      type: 'password', 
      section: 'Secondary Communication',
      placeholder: 'Enter password (will be encrypted)',
      conditional: (formData) => formData.secondary_credential_type === 'username_password'
    },

  ];

  // Group fields by section
  const fieldsBySection = fieldDefinitions.reduce((acc, field) => {
    if (!acc[field.section]) {
      acc[field.section] = [];
    }
    acc[field.section].push(field);
    return acc;
  }, {} as Record<string, FieldDefinition[]>);

  const getDefaultPort = (serviceType: string, databaseType?: string) => {
    switch (serviceType) {
      case 'ssh': return 22;
      case 'winrm': return 5985;
      case 'api': return 443; // HTTPS default
      case 'database':
        switch (databaseType) {
          case 'mysql': return 3306;
          case 'postgresql': return 5432;
          case 'mssql': return 1433;
          case 'oracle': return 1521;
          case 'mongodb': return 27017;
          case 'redis': return 6379;
          default: return 3306; // Default to MySQL port
        }
      // Secondary service ports
      case 'ftp': return 21;
      case 'sftp': return 22;
      case 'telnet': return 23;
      case 'wmi': return 135;
      case 'rdp': return 3389;
      case 'vnc': return 5900;
      default: return null;
    }
  };

  const getCredentialOptions = (serviceType: string) => {
    switch (serviceType) {
      case 'ssh': return ['username_password', 'ssh_key'];
      case 'winrm': return ['username_password'];
      case 'api': return ['api_key', 'bearer_token', 'username_password'];
      case 'database': return ['username_password'];
      // Secondary services
      case 'ftp':
      case 'sftp':
      case 'telnet':
      case 'wmi':
      case 'rdp':
      case 'vnc': return ['username_password'];
      default: return [];
    }
  };

  const handleFieldChange = (field: string, value: any) => {
    setFormData(prev => {
      const newData = {
        ...prev,
        [field]: value
      };
      
      // Auto-update device_type when service_type or os_type changes
      if (field === 'service_type' || field === 'os_type') {
        const serviceType = field === 'service_type' ? value : prev.service_type;
        const osType = field === 'os_type' ? value : prev.os_type;
        newData.device_type = getDeviceTypeFromService(serviceType, osType);
      }
      
      // Auto-populate port and reset credential type for primary service
      if (field === 'service_type') {
        const defaultPort = getDefaultPort(value, newData.database_type);
        if (defaultPort) {
          newData.port = defaultPort;
        }
        // Reset credential type when service type changes
        newData.credential_type = '';
      }
      
      // Auto-populate port for database type change
      if (field === 'database_type' && prev.service_type === 'database') {
        const defaultPort = getDefaultPort('database', value);
        if (defaultPort) {
          newData.port = defaultPort;
        }
      }
      
      // Auto-populate port and reset credential type for secondary service
      if (field === 'secondary_service_type') {
        if (value === 'none') {
          newData.secondary_port = '';
          newData.secondary_credential_type = '';
        } else {
          const defaultPort = getDefaultPort(value);
          if (defaultPort) {
            newData.secondary_port = defaultPort;
          }
          // Reset secondary credential type when service type changes
          newData.secondary_credential_type = '';
        }
      }
      
      return newData;
    });
    
    // Clear error when field is changed
    if (errors[field]) {
      setErrors(prev => ({
        ...prev,
        [field]: ''
      }));
    }
    
    // Clear either/or validation errors when ip_address or hostname is provided
    if (field === 'ip_address' || field === 'hostname') {
      const hasIpAddress = (field === 'ip_address' ? value : formData.ip_address) && 
                          (field === 'ip_address' ? value : formData.ip_address).trim() !== '';
      const hasHostname = (field === 'hostname' ? value : formData.hostname) && 
                         (field === 'hostname' ? value : formData.hostname).trim() !== '';
      
      if (hasIpAddress || hasHostname) {
        setErrors(prev => {
          const newErrors = { ...prev };
          delete newErrors.ip_address;
          delete newErrors.hostname;
          return newErrors;
        });
      }
    }
  };

  const handleTagsChange = (field: string, value: string) => {
    const tags = value ? value.split(',').map(tag => tag.trim()).filter(Boolean) : [];
    handleFieldChange(field, tags);
  };

  const validateForm = (): boolean => {
    const newErrors: Record<string, string> = {};
    
    fieldDefinitions.forEach(fieldDef => {
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
    
    // Custom validation: Either IP Address or Hostname must be provided
    const hasIpAddress = formData.ip_address && formData.ip_address.trim() !== '';
    const hasHostname = formData.hostname && formData.hostname.trim() !== '';
    
    if (!hasIpAddress && !hasHostname) {
      newErrors.ip_address = 'Either IP Address or Hostname must be provided';
      newErrors.hostname = 'Either IP Address or Hostname must be provided';
    }
    
    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const handleSave = () => {
    if (!validateForm()) {
      return;
    }
    
    onSave(formData);
  };

  const renderFieldValue = (fieldDef: FieldDefinition) => {
    const value = formData[fieldDef.field];
    const isReadOnly = mode === 'view';
    const hasError = errors[fieldDef.field];

    switch (fieldDef.type) {
      case 'text':
        return (
          <input
            type="text"
            value={value || ''}
            onChange={(e) => handleFieldChange(fieldDef.field, e.target.value)}
            readOnly={isReadOnly}
            className={`field-input ${hasError ? 'error' : ''}`}
            placeholder={isReadOnly ? '' : fieldDef.placeholder}
          />
        );
      
      case 'password':
        // Check if this field has existing credentials
        const hasExisting = hasExistingCredentials[fieldDef.field as keyof typeof hasExistingCredentials];
        const enhancedPlaceholder = hasExisting 
          ? "••••••••• (encrypted - leave empty to keep)" 
          : (isReadOnly ? '' : fieldDef.placeholder);
        
        return (
          <input
            type={isReadOnly ? 'text' : 'password'}
            value={value || ''}
            onChange={(e) => handleFieldChange(fieldDef.field, e.target.value)}
            readOnly={isReadOnly}
            className={`field-input ${hasError ? 'error' : ''} ${hasExisting ? 'has-existing-credential' : ''}`}
            placeholder={enhancedPlaceholder}
          />
        );
      
      case 'textarea':
        return (
          <textarea
            value={value || ''}
            onChange={(e) => handleFieldChange(fieldDef.field, e.target.value)}
            readOnly={isReadOnly}
            className={`field-textarea ${hasError ? 'error' : ''}`}
            placeholder={isReadOnly ? '' : fieldDef.placeholder}
            rows={3}
          />
        );
      
      case 'number':
        return (
          <input
            type="number"
            value={value || ''}
            onChange={(e) => handleFieldChange(fieldDef.field, parseInt(e.target.value) || 0)}
            readOnly={isReadOnly}
            className={`field-input ${hasError ? 'error' : ''}`}
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
        const getOptionLabel = (option: string) => {
          if (fieldDef.field === 'credential_type' || fieldDef.field === 'secondary_credential_type') {
            switch (option) {
              case 'username_password': return 'Username & Password';
              case 'ssh_key': return 'SSH Key';
              case 'api_key': return 'API Key';
              case 'bearer_token': return 'Bearer Token';
              default: return option;
            }
          }
          if (fieldDef.field === 'service_type') {
            switch (option) {
              case 'ssh': return 'SSH';
              case 'winrm': return 'WinRM';
              case 'api': return 'API (HTTP/HTTPS)';
              case 'database': return 'Database';
              default: return option;
            }
          }
          if (fieldDef.field === 'secondary_service_type') {
            switch (option) {
              case 'none': return 'None';
              case 'ftp': return 'FTP';
              case 'sftp': return 'SFTP';
              case 'telnet': return 'Telnet';
              case 'wmi': return 'WMI';
              case 'rdp': return 'RDP';
              case 'vnc': return 'VNC';
              default: return option;
            }
          }
          return option.charAt(0).toUpperCase() + option.slice(1).replace(/[-_]/g, ' ');
        };

        // Get dynamic options for credential fields
        let options = fieldDef.options || [];
        if (fieldDef.field === 'credential_type' && formData.service_type) {
          options = getCredentialOptions(formData.service_type);
        } else if (fieldDef.field === 'secondary_credential_type' && formData.secondary_service_type) {
          options = getCredentialOptions(formData.secondary_service_type);
        }
        
        return (
          <select
            value={value || ''}
            onChange={(e) => handleFieldChange(fieldDef.field, e.target.value)}
            disabled={isReadOnly}
            className={`field-select ${hasError ? 'error' : ''}`}
          >
            <option value="">Select {fieldDef.label}</option>
            {options.map(option => (
              <option key={option} value={option}>
                {getOptionLabel(option)}
              </option>
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
            className={`field-input ${hasError ? 'error' : ''}`}
            placeholder={isReadOnly ? '' : fieldDef.placeholder}
          />
        );
      
      default:
        return (
          <input
            type="text"
            value={value || ''}
            onChange={(e) => handleFieldChange(fieldDef.field, e.target.value)}
            readOnly={isReadOnly}
            className={`field-input ${hasError ? 'error' : ''}`}
          />
        );
    }
  };

  // Organize sections into two columns - CONSOLIDATED SYSTEM INFORMATION
  const leftColumnSections = [
    'Basic Asset Information',
    'Location Information', 
    'System Information'
  ];
  const rightColumnSections = [
    'Status & Management',
    'Primary Service & Credentials',
    'Database Information',
    'Secondary Communication'
  ];




  const renderColumn = (sectionNames: string[]) => (
    <div className="form-column">
      {sectionNames.map((sectionName) => {
        const fields = fieldsBySection[sectionName];
        if (!fields) return null;
        
        // Filter fields based on conditional logic
        const visibleFields = fields.filter((fieldDef) => {
          if (!fieldDef.conditional) return true;
          return fieldDef.conditional(formData);
        });
        
        if (visibleFields.length === 0) return null;
        
        return (
          <div key={sectionName} className="form-section">
            <div className="section-header" style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
              <h3>{sectionName}</h3>
              {/* Show credential badge for Primary Service & Credentials section */}
              {sectionName === 'Primary Service & Credentials' && Object.values(hasExistingCredentials).some(Boolean) && (
                <span style={{ 
                  padding: '2px 8px', 
                  backgroundColor: 'var(--success-green-light)', 
                  color: 'var(--success-green)', 
                  fontSize: 'var(--font-size-xs)', 
                  borderRadius: '12px',
                  fontWeight: 'bold'
                }}>
                  Stored: {formData.credential_type?.replace('_', ' ').toUpperCase()}
                </span>
              )}
            </div>
            <div className="section-grid">
              {visibleFields.map((fieldDef) => (
                <div key={fieldDef.field} className="field-row">
                  <div className="field-label-cell">
                    <label className={`field-label ${fieldDef.required ? 'required' : ''}`}>
                      {fieldDef.label}
                      {fieldDef.required && <span className="required-asterisk">*</span>}
                      {/* Show credential indicator for password fields */}
                      {fieldDef.type === 'password' && hasExistingCredentials[fieldDef.field as keyof typeof hasExistingCredentials] && (
                        <span className="credential-indicator" title="Encrypted credential stored">●</span>
                      )}
                      {/* Show indicator for username fields when they have values */}
                      {(fieldDef.field === 'username' || fieldDef.field === 'secondary_username') && formData[fieldDef.field] && (
                        <span className="username-indicator" title="Username stored">●</span>
                      )}
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
    <div className="asset-spreadsheet-form">
      <div className="form-container">
        {renderColumn(leftColumnSections)}
        {renderColumn(rightColumnSections)}
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

      <style>{formStyles}</style>
    </div>
  );
};

const formStyles = `
  .asset-spreadsheet-form {
    display: flex;
    flex-direction: column;
    height: 100%;
    background: white;
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
    font-size: 11px;
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
    grid-template-columns: 120px 1fr;
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
    font-size: 10px;
    text-transform: uppercase;
    letter-spacing: 0.3px;
  }
  
  .field-label.required {
    color: #24292f;
  }
  
  .required-asterisk {
    color: #cf222e;
    margin-left: 2px;
    font-size: 10px;
  }
  
  .field-value-cell {
    display: flex;
    flex-direction: column;
    justify-content: center;
    padding: 6px 8px;
    gap: 2px;
  }
  
  .field-input,
  .field-select,
  .field-textarea {
    width: 100%;
    border: none;
    border-radius: 0;
    padding: 0;
    font-size: 12px;
    background: transparent;
    transition: all 0.1s ease;
    line-height: 1.4;
    color: #24292f;
  }
  
  .field-textarea {
    resize: vertical;
    min-height: 36px;
    font-family: inherit;
  }
  
  .field-input:focus,
  .field-select:focus,
  .field-textarea:focus {
    outline: none;
    background-color: #f6f8fa;
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
  
  .field-input[readonly],
  .field-textarea[readonly] {
    background-color: transparent;
    color: #24292f;
  }
  
  .field-input.error,
  .field-select.error,
  .field-textarea.error {
    color: #cf222e;
    background-color: #ffebe9;
  }
  
  .boolean-field {
    display: flex;
    align-items: center;
    gap: 4px;
    padding: 2px 0;
  }
  
  .field-checkbox {
    width: auto;
    margin: 0;
    transform: scale(0.8);
  }
  
  .boolean-label {
    font-size: 10px;
    color: #24292f;
    font-weight: 500;
  }
  
  .field-error {
    color: #cf222e;
    font-size: 9px;
    margin-top: 1px;
  }
  
  .form-actions {
    display: flex;
    gap: 6px;
    justify-content: flex-end;
    padding: 8px;
    margin-top: 8px;
    border: 1px solid #d0d7de;
    background-color: #f6f8fa;
  }
  
  .btn {
    padding: 4px 12px;
    border-radius: 3px;
    font-size: 11px;
    font-weight: 500;
    cursor: pointer;
    border: 1px solid transparent;
    transition: all 0.1s ease;
  }
  
  .btn-primary {
    background-color: #2563eb;
    color: white;
    border-color: #2563eb;
  }
  
  .btn-primary:hover {
    background-color: #1d4ed8;
    border-color: #1e40af;
  }
  
  .btn-secondary {
    background-color: #6b7280;
    color: white;
    border-color: #6b7280;
  }
  
  .btn-secondary:hover {
    background-color: #4b5563;
    border-color: #374151;
  }
  
  /* Collapsible Sections */
  .collapsible-sections {
    margin: 20px 0;
    padding: 0 20px;
  }
  
  .collapsible-sections h2 {
    font-size: 16px;
    font-weight: 600;
    color: #24292f;
    margin-bottom: 16px;
    padding-bottom: 8px;
    border-bottom: 1px solid #d0d7de;
  }
  
  .form-section.collapsible {
    margin-bottom: 12px;
    border: 1px solid #d0d7de;
    border-radius: 6px;
    background: #f6f8fa;
  }
  
  .collapsible-header {
    cursor: pointer;
    padding: 12px 16px;
    background: #f6f8fa;
    border-radius: 6px 6px 0 0;
    transition: background-color 0.1s ease;
  }
  
  .collapsible-header:hover {
    background: #eaeef2;
  }
  
  .collapsible-header h3 {
    margin: 0;
    font-size: 14px;
    font-weight: 600;
    color: #24292f;
    display: flex;
    align-items: center;
  }
  
  .collapse-icon {
    margin-right: 8px;
    font-size: 10px;
    transition: transform 0.2s ease;
    display: inline-block;
  }
  
  .collapse-icon.collapsed {
    transform: rotate(-90deg);
  }
  
  .collapse-icon.expanded {
    transform: rotate(0deg);
  }
  
  .form-section.collapsible .section-grid {
    padding: 16px;
    background: white;
    border-radius: 0 0 6px 6px;
    border-top: 1px solid #d0d7de;
  }
`;

export default AssetSpreadsheetForm;