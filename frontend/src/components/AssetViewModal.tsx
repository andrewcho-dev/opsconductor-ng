import React, { useState, useEffect } from 'react';
import { X, Server, Shield, Globe, Database, Mail, HardDrive, Eye, EyeOff, Copy, Check } from 'lucide-react';

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

interface AssetDetails {
  id: number;
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
  additional_services: AdditionalService[];
  is_active: boolean;
  connection_status?: string;
  last_tested_at?: string;
  notes?: string;
  created_by: number;
  updated_by?: number;
  created_at: string;
  updated_at: string;
}

interface AssetViewModalProps {
  assetId: number;
  onClose: () => void;
}

const AssetViewModal: React.FC<AssetViewModalProps> = ({ assetId, onClose }) => {
  const [asset, setAsset] = useState<AssetDetails | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [showCredentials, setShowCredentials] = useState<{ [key: string]: boolean }>({});
  const [copiedFields, setCopiedFields] = useState<{ [key: string]: boolean }>({});

  useEffect(() => {
    fetchAssetDetails();
  }, [assetId]);

  const fetchAssetDetails = async () => {
    try {
      setLoading(true);
      const response = await fetch(`/api/v1/assets/${assetId}`, {
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('access_token')}`,
        },
      });

      if (!response.ok) {
        throw new Error('Failed to fetch asset details');
      }

      const data = await response.json();
      setAsset(data.data);
      setError(null);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to fetch asset details');
    } finally {
      setLoading(false);
    }
  };

  const toggleCredentialVisibility = (field: string) => {
    setShowCredentials(prev => ({ ...prev, [field]: !prev[field] }));
  };

  const copyToClipboard = async (text: string, field: string) => {
    try {
      await navigator.clipboard.writeText(text);
      setCopiedFields(prev => ({ ...prev, [field]: true }));
      setTimeout(() => {
        setCopiedFields(prev => ({ ...prev, [field]: false }));
      }, 2000);
    } catch (err) {
      console.error('Failed to copy to clipboard:', err);
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

  const getOsIcon = (osType: string) => {
    const iconMap: { [key: string]: string } = {
      windows: '🪟',
      linux: '🐧',
      macos: '🍎',
      unix: '🖥️',
    };
    return iconMap[osType] || '💻';
  };

  const getStatusColor = (status?: string) => {
    switch (status) {
      case 'connected': return 'text-green-600 bg-green-100';
      case 'failed': return 'text-red-600 bg-red-100';
      case 'testing': return 'text-yellow-600 bg-yellow-100';
      default: return 'text-gray-600 bg-gray-100';
    }
  };

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleString();
  };

  const renderCredentialField = (
    label: string,
    value: string | undefined,
    fieldKey: string,
    isSecret: boolean = false
  ) => {
    if (!value) return null;

    return (
      <div className="space-y-1">
        <label className="block text-sm font-medium text-gray-700">{label}</label>
        <div className="flex items-center gap-2">
          <div className="flex-1 px-3 py-2 bg-gray-50 border border-gray-200 rounded-lg font-mono text-sm">
            {isSecret && !showCredentials[fieldKey] ? '••••••••••••' : value}
          </div>
          <div className="flex gap-1">
            {isSecret && (
              <button
                onClick={() => toggleCredentialVisibility(fieldKey)}
                className="p-2 text-gray-400 hover:text-gray-600 border border-gray-200 rounded-lg"
                title={showCredentials[fieldKey] ? 'Hide' : 'Show'}
              >
                {showCredentials[fieldKey] ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
              </button>
            )}
            <button
              onClick={() => copyToClipboard(value, fieldKey)}
              className="p-2 text-gray-400 hover:text-gray-600 border border-gray-200 rounded-lg"
              title="Copy to clipboard"
            >
              {copiedFields[fieldKey] ? <Check className="w-4 h-4 text-green-600" /> : <Copy className="w-4 h-4" />}
            </button>
          </div>
        </div>
      </div>
    );
  };

  const renderServiceCredentials = (service: AdditionalService, serviceIndex: number) => {
    if (!service.credential_type) return null;

    const prefix = `service_${serviceIndex}_`;

    return (
      <div className="mt-3 space-y-3">
        <h5 className="text-sm font-medium text-gray-700">Credentials</h5>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
          {service.username && renderCredentialField('Username', service.username, `${prefix}username`)}
          {service.domain && renderCredentialField('Domain', service.domain, `${prefix}domain`)}
          {service.api_key && renderCredentialField('API Key', service.api_key, `${prefix}api_key`, true)}
        </div>
      </div>
    );
  };

  if (loading) {
    return (
      <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
        <div className="bg-white rounded-lg p-6">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600 mx-auto"></div>
          <p className="text-center mt-2">Loading asset details...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
        <div className="bg-white rounded-lg p-6 max-w-md w-full mx-4">
          <div className="flex justify-between items-center mb-4">
            <h2 className="text-xl font-semibold text-red-600">Error</h2>
            <button onClick={onClose} className="text-gray-400 hover:text-gray-600">
              <X className="w-6 h-6" />
            </button>
          </div>
          <p className="text-gray-700 mb-4">{error}</p>
          <button
            onClick={onClose}
            className="w-full px-4 py-2 bg-gray-100 text-gray-700 rounded-lg hover:bg-gray-200"
          >
            Close
          </button>
        </div>
      </div>
    );
  }

  if (!asset) return null;

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
      <div className="bg-white rounded-lg max-w-4xl w-full max-h-[90vh] overflow-y-auto">
        <div className="sticky top-0 bg-white border-b px-6 py-4 flex justify-between items-center">
          <div className="flex items-center gap-3">
            <div className="text-2xl">{getOsIcon(asset.os_type)}</div>
            <div>
              <h2 className="text-xl font-semibold">{asset.name}</h2>
              <p className="text-gray-600">{asset.hostname}</p>
            </div>
          </div>
          <button
            onClick={onClose}
            className="text-gray-400 hover:text-gray-600"
          >
            <X className="w-6 h-6" />
          </button>
        </div>

        <div className="p-6 space-y-6">
          {/* Basic Information */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div className="space-y-4">
              <h3 className="text-lg font-medium text-gray-900">Basic Information</h3>
              
              <div className="space-y-3">
                <div>
                  <label className="block text-sm font-medium text-gray-700">Asset Name</label>
                  <p className="text-gray-900">{asset.name}</p>
                </div>
                
                <div>
                  <label className="block text-sm font-medium text-gray-700">Hostname</label>
                  <p className="text-gray-900 font-mono">{asset.hostname}</p>
                </div>
                
                {asset.ip_address && (
                  <div>
                    <label className="block text-sm font-medium text-gray-700">IP Address</label>
                    <p className="text-gray-900 font-mono">{asset.ip_address}</p>
                  </div>
                )}
                
                <div>
                  <label className="block text-sm font-medium text-gray-700">Operating System</label>
                  <p className="text-gray-900">{asset.os_type}{asset.os_version && ` (${asset.os_version})`}</p>
                </div>
                
                {asset.description && (
                  <div>
                    <label className="block text-sm font-medium text-gray-700">Description</label>
                    <p className="text-gray-900">{asset.description}</p>
                  </div>
                )}
              </div>
            </div>

            <div className="space-y-4">
              <h3 className="text-lg font-medium text-gray-900">Status & Metadata</h3>
              
              <div className="space-y-3">
                <div>
                  <label className="block text-sm font-medium text-gray-700">Status</label>
                  <div className="flex items-center gap-2">
                    <div className={`w-2 h-2 rounded-full ${asset.is_active ? 'bg-green-500' : 'bg-gray-400'}`}></div>
                    <span className="text-gray-900">{asset.is_active ? 'Active' : 'Inactive'}</span>
                  </div>
                </div>
                
                {asset.connection_status && (
                  <div>
                    <label className="block text-sm font-medium text-gray-700">Connection Status</label>
                    <span className={`px-2 py-1 text-xs rounded-full ${getStatusColor(asset.connection_status)}`}>
                      {asset.connection_status}
                    </span>
                  </div>
                )}
                
                {asset.last_tested_at && (
                  <div>
                    <label className="block text-sm font-medium text-gray-700">Last Tested</label>
                    <p className="text-gray-900">{formatDate(asset.last_tested_at)}</p>
                  </div>
                )}
                
                <div>
                  <label className="block text-sm font-medium text-gray-700">Created</label>
                  <p className="text-gray-900">{formatDate(asset.created_at)}</p>
                </div>
                
                <div>
                  <label className="block text-sm font-medium text-gray-700">Last Updated</label>
                  <p className="text-gray-900">{formatDate(asset.updated_at)}</p>
                </div>
              </div>
            </div>
          </div>

          {/* Tags */}
          {asset.tags.length > 0 && (
            <div>
              <h3 className="text-lg font-medium text-gray-900 mb-3">Tags</h3>
              <div className="flex flex-wrap gap-2">
                {asset.tags.map((tag, index) => (
                  <span
                    key={index}
                    className="px-2 py-1 bg-blue-100 text-blue-800 text-sm rounded-full"
                  >
                    {tag}
                  </span>
                ))}
              </div>
            </div>
          )}

          {/* Primary Service */}
          <div>
            <h3 className="text-lg font-medium text-gray-900 mb-4">Primary Service</h3>
            <div className="border border-gray-200 rounded-lg p-4">
              <div className="flex items-center gap-3 mb-4">
                {getServiceIcon(asset.service_type)}
                <div>
                  <h4 className="font-medium text-gray-900">{asset.service_type.toUpperCase()}</h4>
                  <p className="text-sm text-gray-600">Port {asset.port} {asset.is_secure && '(Secure)'}</p>
                </div>
              </div>

              {asset.credential_type && (
                <div className="space-y-3">
                  <h5 className="text-sm font-medium text-gray-700">Credentials ({asset.credential_type.replace('_', ' ')})</h5>
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                    {asset.username && renderCredentialField('Username', asset.username, 'primary_username')}
                    {asset.domain && renderCredentialField('Domain', asset.domain, 'primary_domain')}
                  </div>
                </div>
              )}
            </div>
          </div>

          {/* Additional Services */}
          {asset.additional_services.length > 0 && (
            <div>
              <h3 className="text-lg font-medium text-gray-900 mb-4">Additional Services</h3>
              <div className="space-y-4">
                {asset.additional_services.map((service, index) => (
                  <div key={index} className="border border-gray-200 rounded-lg p-4">
                    <div className="flex items-center gap-3 mb-3">
                      {getServiceIcon(service.service_type)}
                      <div>
                        <h4 className="font-medium text-gray-900">{service.service_type.toUpperCase()}</h4>
                        <p className="text-sm text-gray-600">Port {service.port} {service.is_secure && '(Secure)'}</p>
                      </div>
                    </div>

                    {service.notes && (
                      <div className="mb-3">
                        <label className="block text-sm font-medium text-gray-700">Notes</label>
                        <p className="text-gray-900">{service.notes}</p>
                      </div>
                    )}

                    {renderServiceCredentials(service, index)}
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Notes */}
          {asset.notes && (
            <div>
              <h3 className="text-lg font-medium text-gray-900 mb-3">Notes</h3>
              <div className="bg-gray-50 border border-gray-200 rounded-lg p-4">
                <p className="text-gray-900 whitespace-pre-wrap">{asset.notes}</p>
              </div>
            </div>
          )}
        </div>

        <div className="sticky bottom-0 bg-white border-t px-6 py-4">
          <div className="flex justify-end">
            <button
              onClick={onClose}
              className="px-4 py-2 bg-gray-100 text-gray-700 rounded-lg hover:bg-gray-200"
            >
              Close
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};

export default AssetViewModal;