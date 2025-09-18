import React, { useState, useEffect } from 'react';
import { X, Plus, Trash2, Eye, EyeOff, Server, Shield, Globe, Database, Mail, HardDrive, Check } from 'lucide-react';

interface AdditionalService {
  service_type: string;
  port: number;
  is_secure: boolean;
  credential_type?: string;
  username?: string;
  domain?: string;
  api_key?: string;
  notes?: string;
}

interface AssetCreateData {
  name: string;
  hostname: string;
  ip_address?: string;
  description?: string;
  tags: string[];
  os_type: string;
  os_version?: string;
  service_type: string;
  port: number;
  is_secure: boolean;
  credential_type?: string;
  username?: string;
  domain?: string;
  password?: string;
  private_key?: string;
  api_key?: string;
  additional_services: AdditionalService[];
  notes?: string;
}

interface Metadata {
  os_types: (string | { value: string; label: string })[];
  service_types: (string | { value: string; label: string })[];
  credential_types: (string | { value: string; label: string })[];
}

interface AssetCreateFormProps {
  onCancel: () => void;
  onSuccess: () => void;
}

const AssetCreateForm: React.FC<AssetCreateFormProps> = ({ onCancel, onSuccess }) => {
  const [formData, setFormData] = useState<AssetCreateData>({
    name: '',
    hostname: '',
    ip_address: '',
    description: '',
    tags: [],
    os_type: 'linux',
    os_version: '',
    service_type: 'ssh',
    port: 22,
    is_secure: true,
    credential_type: '',
    username: '',
    domain: '',
    password: '',
    private_key: '',
    api_key: '',
    additional_services: [],
    notes: ''
  });

  const [metadata, setMetadata] = useState<Metadata>({
    os_types: ['linux', 'windows', 'macos', 'unix'],
    service_types: ['ssh', 'rdp', 'winrm', 'http', 'https', 'mysql', 'postgresql', 'smtp', 'ftp'],
    credential_types: ['password', 'private_key', 'api_key', 'certificate']
  });

  const [tagInput, setTagInput] = useState('');
  const [showPassword, setShowPassword] = useState(false);
  const [showPrivateKey, setShowPrivateKey] = useState(false);
  const [showApiKey, setShowApiKey] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    fetchMetadata();
  }, []);

  useEffect(() => {
    // Update default port when service type changes
    const defaultPorts: { [key: string]: number } = {
      ssh: 22,
      rdp: 3389,
      winrm: 5985,
      http: 80,
      https: 443,
      mysql: 3306,
      postgresql: 5432,
      smtp: 587,
      ftp: 21
    };
    
    if (defaultPorts[formData.service_type]) {
      setFormData(prev => ({ ...prev, port: defaultPorts[formData.service_type] }));
    }
  }, [formData.service_type]);

  const fetchMetadata = async () => {
    try {
      const response = await fetch('/api/v1/metadata', {
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('access_token')}`,
        },
      });

      if (response.ok) {
        const data = await response.json();
        setMetadata(data.data);
      }
    } catch (err) {
      console.error('Failed to fetch metadata:', err);
    }
  };

  const handleInputChange = (field: keyof AssetCreateData, value: any) => {
    setFormData(prev => ({ ...prev, [field]: value }));
  };

  const handleAddTag = () => {
    if (tagInput.trim() && !formData.tags.includes(tagInput.trim())) {
      setFormData(prev => ({
        ...prev,
        tags: [...prev.tags, tagInput.trim()]
      }));
      setTagInput('');
    }
  };

  const handleRemoveTag = (tagToRemove: string) => {
    setFormData(prev => ({
      ...prev,
      tags: prev.tags.filter(tag => tag !== tagToRemove)
    }));
  };

  const handleAddService = () => {
    const newService: AdditionalService = {
      service_type: 'ssh',
      port: 22,
      is_secure: true,
      credential_type: '',
      username: '',
      domain: '',
      api_key: '',
      notes: ''
    };
    
    setFormData(prev => ({
      ...prev,
      additional_services: [...prev.additional_services, newService]
    }));
  };

  const handleRemoveService = (index: number) => {
    setFormData(prev => ({
      ...prev,
      additional_services: prev.additional_services.filter((_, i) => i !== index)
    }));
  };

  const handleServiceChange = (index: number, field: keyof AdditionalService, value: any) => {
    setFormData(prev => ({
      ...prev,
      additional_services: prev.additional_services.map((service, i) =>
        i === index ? { ...service, [field]: value } : service
      )
    }));
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError(null);

    try {
      // Clean up the form data
      const submitData = { ...formData };
      
      // Remove empty optional fields
      if (!submitData.ip_address?.trim()) delete submitData.ip_address;
      if (!submitData.description?.trim()) delete submitData.description;
      if (!submitData.os_version?.trim()) delete submitData.os_version;
      if (!submitData.credential_type?.trim()) delete submitData.credential_type;
      if (!submitData.username?.trim()) delete submitData.username;
      if (!submitData.domain?.trim()) delete submitData.domain;
      if (!submitData.password?.trim()) delete submitData.password;
      if (!submitData.private_key?.trim()) delete submitData.private_key;
      if (!submitData.api_key?.trim()) delete submitData.api_key;
      if (!submitData.notes?.trim()) delete submitData.notes;

      // Clean up additional services
      submitData.additional_services = submitData.additional_services.map(service => {
        const cleanService = { ...service };
        if (!cleanService.credential_type?.trim()) delete cleanService.credential_type;
        if (!cleanService.username?.trim()) delete cleanService.username;
        if (!cleanService.domain?.trim()) delete cleanService.domain;
        if (!cleanService.api_key?.trim()) delete cleanService.api_key;
        if (!cleanService.notes?.trim()) delete cleanService.notes;
        return cleanService;
      });

      const response = await fetch('/api/v1/assets', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${localStorage.getItem('access_token')}`,
        },
        body: JSON.stringify(submitData),
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || 'Failed to create asset');
      }

      onSuccess();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to create asset');
    } finally {
      setLoading(false);
    }
  };

  const getServiceIcon = (serviceType: string) => {
    const iconMap: { [key: string]: React.ReactNode } = {
      ssh: <Server className="w-4 h-4" />,
      rdp: <Server className="w-4 h-4" />,
      winrm: <Server className="w-4 h-4" />,
      http: <Globe className="w-4 h-4" />,
      https: <Shield className="w-4 h-4" />,
      mysql: <Database className="w-4 h-4" />,
      postgresql: <Database className="w-4 h-4" />,
      smtp: <Mail className="w-4 h-4" />,
      ftp: <HardDrive className="w-4 h-4" />,
    };
    return iconMap[serviceType] || <Server className="w-4 h-4" />;
  };

  return (
    <>
      <style>
        {`
          /* Form styles matching user form */
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
            content: " *";
            color: var(--danger-red);
          }
          .form-input {
            width: 100%;
            padding: 8px 12px;
            border: 1px solid var(--neutral-300);
            border-radius: 4px;
            font-size: 13px;
            transition: border-color 0.2s;
          }
          .form-input:focus {
            outline: none;
            border-color: var(--primary-blue);
            box-shadow: 0 0 0 2px var(--primary-blue-light);
          }
          .six-column-grid {
            display: grid;
            grid-template-columns: 1fr 1fr 1fr 1fr 1fr 1fr;
            gap: 16px;
          }
          .four-column-grid {
            display: grid;
            grid-template-columns: 1fr 1fr 1fr 1fr;
            gap: 16px;
          }
          .three-column-grid {
            display: grid;
            grid-template-columns: 1fr 1fr 1fr;
            gap: 16px;
          }
          .two-column-grid {
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 16px;
          }
          .asset-details {
            padding: 8px;
          }
          .asset-details h3 {
            margin: 0 0 12px 0;
            font-size: 14px;
            font-weight: 600;
            color: var(--neutral-800);
          }
        `}
      </style>

      <div className="section-header">
        <span>Create New Asset</span>
        <div style={{ display: 'flex', gap: '4px' }}>
          <button 
            className="btn-icon btn-success"
            onClick={handleSubmit}
            disabled={loading}
            title="Create Asset"
            type="button"
          >
            <Check size={16} />
          </button>
          <button 
            className="btn-icon btn-ghost"
            onClick={onCancel}
            disabled={loading}
            title="Cancel"
            type="button"
          >
            <X size={16} />
          </button>
        </div>
      </div>

      <div className="compact-content asset-details">
        {error && (
          <div className="bg-red-50 border border-red-200 text-red-700 px-3 py-2 rounded text-sm mb-4">
            {error}
          </div>
        )}

        <form onSubmit={handleSubmit}>

          {/* Basic Information */}
          <div>
            <div className="section-header">Basic Information</div>
            <div className="four-column-grid">
              <div className="form-field">
                <label className="form-label required">Asset Name</label>
                <input
                  type="text"
                  required
                  value={formData.name}
                  onChange={(e) => handleInputChange('name', e.target.value)}
                  className="form-input"
                  placeholder="e.g., Production Web Server"
                />
              </div>

              <div className="form-field">
                <label className="form-label required">Hostname</label>
                <input
                  type="text"
                  required
                  value={formData.hostname}
                  onChange={(e) => handleInputChange('hostname', e.target.value)}
                  className="form-input"
                  placeholder="e.g., web01.example.com"
                />
              </div>

              <div className="form-field">
                <label className="form-label">IP Address</label>
                <input
                  type="text"
                  value={formData.ip_address}
                  onChange={(e) => handleInputChange('ip_address', e.target.value)}
                  className="form-input"
                  placeholder="e.g., 192.168.1.100"
                />
              </div>

              <div className="form-field">
                <label className="form-label">Description</label>
                <input
                  type="text"
                  value={formData.description}
                  onChange={(e) => handleInputChange('description', e.target.value)}
                  className="form-input"
                  placeholder="Brief description..."
                />
              </div>
            </div>
          </div>

          {/* System Information */}
          <div>
            <div className="section-header">System Information</div>
            <div className="three-column-grid">
              <div className="form-field">
                <label className="form-label required">Operating System</label>
                <select
                  required
                  value={formData.os_type}
                  onChange={(e) => handleInputChange('os_type', e.target.value)}
                  className="form-input"
                >
                  {metadata.os_types.map(osType => {
                    const value = typeof osType === 'string' ? osType : osType.value;
                    const label = typeof osType === 'string' ? osType.charAt(0).toUpperCase() + osType.slice(1) : osType.label;
                    return (
                      <option key={value} value={value}>
                        {label}
                      </option>
                    );
                  })}
                </select>
              </div>

              <div className="form-field">
                <label className="form-label">OS Version</label>
                <input
                  type="text"
                  value={formData.os_version}
                  onChange={(e) => handleInputChange('os_version', e.target.value)}
                  className="form-input"
                  placeholder="e.g., Ubuntu 22.04, Windows Server 2022"
                />
              </div>

              <div className="form-field">
                <label className="form-label">Tags</label>
                <div className="flex gap-2">
                  <input
                    type="text"
                    value={tagInput}
                    onChange={(e) => setTagInput(e.target.value)}
                    onKeyPress={(e) => e.key === 'Enter' && (e.preventDefault(), handleAddTag())}
                    className="form-input"
                    placeholder="Add a tag..."
                  />
                  <button
                    type="button"
                    onClick={handleAddTag}
                    className="px-3 py-2 bg-blue-600 text-white rounded text-sm hover:bg-blue-700"
                  >
                    Add
                  </button>
                </div>
                {formData.tags.length > 0 && (
                  <div className="flex flex-wrap gap-1 mt-2">
                    {formData.tags.map((tag, index) => (
                      <span
                        key={index}
                        className="inline-flex items-center gap-1 px-2 py-1 bg-blue-100 text-blue-800 text-xs rounded-full"
                      >
                        {tag}
                        <button
                          type="button"
                          onClick={() => handleRemoveTag(tag)}
                          className="text-blue-600 hover:text-blue-800"
                        >
                          <X className="w-3 h-3" />
                        </button>
                      </span>
                    ))}
                  </div>
                )}
              </div>
            </div>
          </div>

          {/* Primary Service */}
          <div>
            <div className="section-header">Primary Service</div>
            <div className="four-column-grid">
              <div className="form-field">
                <label className="form-label required">Service Type</label>
                <select
                  required
                  value={formData.service_type}
                  onChange={(e) => handleInputChange('service_type', e.target.value)}
                  className="form-input"
                >
                  {metadata.service_types.map(serviceType => {
                    const value = typeof serviceType === 'string' ? serviceType : serviceType.value;
                    const label = typeof serviceType === 'string' ? serviceType.toUpperCase() : serviceType.label;
                    return (
                      <option key={value} value={value}>
                        {label}
                      </option>
                    );
                  })}
                </select>
              </div>

              <div className="form-field">
                <label className="form-label required">Port</label>
                <input
                  type="number"
                  required
                  min="1"
                  max="65535"
                  value={formData.port}
                  onChange={(e) => handleInputChange('port', parseInt(e.target.value))}
                  className="form-input"
                />
              </div>

              <div className="form-field">
                <label className="form-label">Credential Type</label>
                <select
                  value={formData.credential_type || ''}
                  onChange={(e) => handleInputChange('credential_type', e.target.value || undefined)}
                  className="form-input"
                >
                  <option value="">None</option>
                  {metadata.credential_types.map(credType => {
                    const value = typeof credType === 'string' ? credType : credType.value;
                    const label = typeof credType === 'string' ? credType.replace('_', ' ').toUpperCase() : credType.label;
                    return (
                      <option key={value} value={value}>
                        {label}
                      </option>
                    );
                  })}
                </select>
              </div>

              <div className="form-field">
                <label className="form-label">Security</label>
                <div className="flex items-center pt-2">
                  <input
                    type="checkbox"
                    checked={formData.is_secure}
                    onChange={(e) => handleInputChange('is_secure', e.target.checked)}
                    className="mr-2"
                  />
                  <span className="text-sm">Secure Connection</span>
                </div>
              </div>
            </div>
          </div>

          {/* Credentials */}
          {formData.credential_type && (
            <div>
              <div className="section-header">Credentials</div>
              <div className="three-column-grid">
                {(formData.credential_type === 'password' || formData.credential_type === 'private_key') && (
                  <>
                    <div className="form-field">
                      <label className="form-label">Username</label>
                      <input
                        type="text"
                        value={formData.username}
                        onChange={(e) => handleInputChange('username', e.target.value)}
                        className="form-input"
                      />
                    </div>

                    <div className="form-field">
                      <label className="form-label">Domain</label>
                      <input
                        type="text"
                        value={formData.domain}
                        onChange={(e) => handleInputChange('domain', e.target.value)}
                        className="form-input"
                        placeholder="Optional domain"
                      />
                    </div>
                  </>
                )}

                {formData.credential_type === 'password' && (
                  <div className="form-field">
                    <label className="form-label">Password</label>
                    <div className="relative">
                      <input
                        type={showPassword ? 'text' : 'password'}
                        value={formData.password}
                        onChange={(e) => handleInputChange('password', e.target.value)}
                        className="form-input pr-10"
                      />
                      <button
                        type="button"
                        onClick={() => setShowPassword(!showPassword)}
                        className="absolute right-3 top-1/2 transform -translate-y-1/2 text-gray-400 hover:text-gray-600"
                      >
                        {showPassword ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
                      </button>
                    </div>
                  </div>
                )}

                {formData.credential_type === 'private_key' && (
                  <div className="form-field">
                    <label className="form-label">Private Key</label>
                    <div className="relative">
                      <textarea
                        value={formData.private_key}
                        onChange={(e) => handleInputChange('private_key', e.target.value)}
                        rows={3}
                        className="form-input pr-10 font-mono text-xs"
                        placeholder="-----BEGIN PRIVATE KEY-----"
                      />
                      <button
                        type="button"
                        onClick={() => setShowPrivateKey(!showPrivateKey)}
                        className="absolute right-3 top-3 text-gray-400 hover:text-gray-600"
                      >
                        {showPrivateKey ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
                      </button>
                    </div>
                  </div>
                )}

                {formData.credential_type === 'api_key' && (
                  <div className="form-field">
                    <label className="form-label">API Key</label>
                    <div className="relative">
                      <input
                        type={showApiKey ? 'text' : 'password'}
                        value={formData.api_key}
                        onChange={(e) => handleInputChange('api_key', e.target.value)}
                        className="form-input pr-10"
                      />
                      <button
                        type="button"
                        onClick={() => setShowApiKey(!showApiKey)}
                        className="absolute right-3 top-1/2 transform -translate-y-1/2 text-gray-400 hover:text-gray-600"
                      >
                        {showApiKey ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
                      </button>
                    </div>
                  </div>
                )}
              </div>
            </div>
          )}

          {/* Additional Services */}
          <div>
            <div className="section-header flex justify-between items-center">
              <span>Additional Services</span>
              <button
                type="button"
                onClick={handleAddService}
                className="flex items-center gap-2 px-3 py-1 bg-green-600 text-white rounded text-sm hover:bg-green-700"
              >
                <Plus className="w-4 h-4" />
                Add Service
              </button>
            </div>

            {formData.additional_services.map((service, index) => (
              <div key={index} className="border border-gray-200 rounded p-3 mb-4">
                <div className="flex justify-between items-center mb-3">
                  <div className="flex items-center gap-2">
                    {getServiceIcon(service.service_type)}
                    <span className="text-sm font-medium">Service {index + 1}</span>
                  </div>
                  <button
                    type="button"
                    onClick={() => handleRemoveService(index)}
                    className="text-red-600 hover:text-red-800"
                  >
                    <Trash2 className="w-4 h-4" />
                  </button>
                </div>

                <div className="four-column-grid">
                  <div className="form-field">
                    <label className="form-label">Service Type</label>
                    <select
                      value={service.service_type}
                      onChange={(e) => handleServiceChange(index, 'service_type', e.target.value)}
                      className="form-input"
                    >
                      {metadata.service_types.map(serviceType => {
                        const value = typeof serviceType === 'string' ? serviceType : serviceType.value;
                        const label = typeof serviceType === 'string' ? serviceType.toUpperCase() : serviceType.label;
                        return (
                          <option key={value} value={value}>
                            {label}
                          </option>
                        );
                      })}
                    </select>
                  </div>

                  <div className="form-field">
                    <label className="form-label">Port</label>
                    <input
                      type="number"
                      min="1"
                      max="65535"
                      value={service.port}
                      onChange={(e) => handleServiceChange(index, 'port', parseInt(e.target.value))}
                      className="form-input"
                    />
                  </div>

                  <div className="form-field">
                    <label className="form-label">Security</label>
                    <div className="flex items-center pt-2">
                      <input
                        type="checkbox"
                        checked={service.is_secure}
                        onChange={(e) => handleServiceChange(index, 'is_secure', e.target.checked)}
                        className="mr-2"
                      />
                      <span className="text-sm">Secure</span>
                    </div>
                  </div>

                  <div className="form-field">
                    <label className="form-label">Notes</label>
                    <input
                      type="text"
                      value={service.notes}
                      onChange={(e) => handleServiceChange(index, 'notes', e.target.value)}
                      className="form-input"
                      placeholder="Optional notes..."
                    />
                  </div>
                </div>
              </div>
            ))}
          </div>

          {/* Notes */}
          <div>
            <div className="section-header">Notes</div>
            <div className="form-field">
              <textarea
                value={formData.notes}
                onChange={(e) => handleInputChange('notes', e.target.value)}
                rows={3}
                className="form-input"
                placeholder="Additional notes about this asset..."
              />
            </div>
          </div>

          {/* Form Actions */}
          <div className="flex justify-end gap-3 pt-6 border-t border-gray-200">
            <button
              type="button"
              onClick={onCancel}
              className="px-4 py-2 text-gray-700 bg-gray-100 rounded hover:bg-gray-200 text-sm"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={loading}
              className="px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed text-sm"
            >
              {loading ? 'Creating...' : 'Create Asset'}
            </button>
          </div>
        </form>
      </div>
    </>
  );
};

export default AssetCreateForm;