import React, { useState, useEffect, useMemo } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import { Plus, Trash2, Check, X, Edit3, MonitorCheck, Zap } from 'lucide-react';
import { targetApi, automationApi } from '../services/api';
import { enhancedTargetApi, targetServiceApi, targetCredentialApi, metadataApi } from '../services/enhancedApi';
import { Target, TargetCreate, Credential } from '../types';
import { EnhancedTarget, TargetService, TargetCredential } from '../types/enhanced';

// Service type to credential type mapping
const SERVICE_CREDENTIAL_MAPPING: Record<string, string[]> = {
  'ssh': ['ssh_key', 'username_password'],
  'sftp': ['ssh_key', 'username_password'],
  'rdp': ['username_password'],
  'winrm': ['username_password'],
  'winrm_https': ['username_password'],
  'wmi': ['username_password'],
  'smb': ['username_password'],
  'http': ['api_key', 'username_password', 'bearer_token'],
  'https': ['api_key', 'username_password', 'bearer_token'],
  'http_alt': ['api_key', 'username_password', 'bearer_token'],
  'https_alt': ['api_key', 'username_password', 'bearer_token'],
  'mysql': ['username_password'],
  'postgresql': ['username_password'],
  'sql_server': ['username_password'],
  'oracle': ['username_password'],
  'mongodb': ['username_password'],
  'redis': ['username_password'],
  'smtp': ['username_password'],
  'smtps': ['username_password'],
  'smtp_submission': ['username_password'],
  'imap': ['username_password'],
  'imaps': ['username_password'],
  'pop3': ['username_password'],
  'pop3s': ['username_password'],
  'ftp': ['username_password'],
  'ftps': ['username_password'],
  'dns': ['username_password'],
  'snmp': ['username_password'],
  'ntp': ['username_password'],
  'telnet': ['username_password'],
  'vnc': ['username_password']
};

// Service type definitions with default ports (using backend service_type values)
const SERVICE_TYPES = {
  // Remote Access
  'ssh': 22,
  'rdp': 3389,
  'vnc': 5900,
  'telnet': 23,
  
  // Windows Management  
  'winrm': 5985,
  'winrm_https': 5986,
  'wmi': 135,
  'smb': 445,
  
  // Web Services
  'http': 80,
  'https': 443,
  'http_alt': 8080,
  'https_alt': 8443,
  
  // Database Services
  'mysql': 3306,
  'postgresql': 5432,
  'sql_server': 1433,
  'oracle': 1521,
  'mongodb': 27017,
  'redis': 6379,
  
  // Email Services
  'smtp': 25,
  'smtps': 465,
  'smtp_submission': 587,
  'imap': 143,
  'imaps': 993,
  'pop3': 110,
  'pop3s': 995,
  
  // File Transfer
  'ftp': 21,
  'ftps': 990,
  'sftp': 22,
  
  // Network Services
  'dns': 53,
  'snmp': 161,
  'ntp': 123,
} as const;

// Display names for service types
const SERVICE_DISPLAY_NAMES: Record<string, string> = {
  // Remote Access
  'ssh': 'SSH',
  'rdp': 'RDP',
  'vnc': 'VNC',
  'telnet': 'Telnet',
  
  // Windows Management
  'winrm': 'WinRM HTTP',
  'winrm_https': 'WinRM HTTPS',
  'wmi': 'WMI',
  'smb': 'SMB',
  
  // Web Services
  'http': 'HTTP',
  'https': 'HTTPS',
  'http_alt': 'HTTP Alt',
  'https_alt': 'HTTPS Alt',
  
  // Database Services
  'mysql': 'MySQL',
  'postgresql': 'PostgreSQL',
  'sql_server': 'SQL Server',
  'oracle': 'Oracle',
  'mongodb': 'MongoDB',
  'redis': 'Redis',
  
  // Email Services
  'smtp': 'SMTP',
  'smtps': 'SMTP SSL',
  'smtp_submission': 'SMTP TLS',
  'imap': 'IMAP',
  'imaps': 'IMAPS',
  'pop3': 'POP3',
  'pop3s': 'POP3S',
  
  // File Transfer
  'ftp': 'FTP',
  'ftps': 'FTPS',
  'sftp': 'SFTP',
  
  // Network Services
  'dns': 'DNS',
  'snmp': 'SNMP',
  'ntp': 'NTP',
};

// Helper function to format credential type display
const formatCredentialType = (credentialType: string): string => {
  if (!credentialType) return '';
  return credentialType
    .split('_')
    .map(word => word.charAt(0).toUpperCase() + word.slice(1))
    .join(' ');
};

// Helper function to get credential summary
const getCredentialSummary = (service: any): string => {
  if (!service.credential_type) return '';
  
  return formatCredentialType(service.credential_type);
};

interface NewTargetState {
  ip_address: string;
  os_type: string;
  tags: string[];
  description: string;
  services: Array<{
    service_type: string;
    port: number;
    credential_id?: number;
    notes?: string;
    is_default?: boolean;
    is_secure?: boolean;
    is_enabled?: boolean;
    credential_type?: string;
    username?: string;
    password?: string;
    private_key?: string;
    public_key?: string;
    api_key?: string;
    bearer_token?: string;
    certificate?: string;
    passphrase?: string;
    domain?: string;
  }>;
}

interface EditTargetState {
  ip_address: string;
  os_type: string;
  tags: string[];
  description: string;
  services: Array<{
    service_type: string;
    port: number | string;
    credential_id?: number | string;
    notes?: string;
    is_default?: boolean;
    is_secure?: boolean;
    is_enabled?: boolean;
    credential_type?: string;
    username?: string;
    password?: string;
    private_key?: string;
    public_key?: string;
    api_key?: string;
    bearer_token?: string;
    certificate?: string;
    passphrase?: string;
    domain?: string;
  }>;
}

const Targets: React.FC = () => {
  const navigate = useNavigate();
  const { action, id } = useParams<{ action?: string; id?: string }>();
  const [targets, setTargets] = useState<EnhancedTarget[]>([]);
  const [credentials, setCredentials] = useState<Credential[]>([]);
  const [metadata, setMetadata] = useState<{
    credential_types: Array<{value: string, label: string}>,
    service_types: Array<{value: string, label: string, default_port: number}>,
    os_types: Array<{value: string, label: string}>
  } | null>(null);

  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [testingConnections, setTestingConnections] = useState<Set<number>>(new Set());

  const [selectedTarget, setSelectedTarget] = useState<EnhancedTarget | null>(null);
  const [addingNew, setAddingNew] = useState(false);
  const [editingTarget, setEditingTarget] = useState<EnhancedTarget | null>(null);
  const [retryCount, setRetryCount] = useState(0);
  
  // Sorting state
  const [sortField, setSortField] = useState<string>('ip_address');
  const [sortDirection, setSortDirection] = useState<'asc' | 'desc'>('asc');
  
  const [newTarget, setNewTarget] = useState<NewTargetState>({
    ip_address: '',
    os_type: '',
    tags: [],
    description: '',
    services: []
  });

  const [editTarget, setEditTarget] = useState<EditTargetState>({
    ip_address: '',
    os_type: '',
    tags: [],
    description: '',
    services: []
  });

  useEffect(() => {
    fetchTargets();
    fetchCredentials();
    fetchMetadata();
  }, []);

  // Add a retry mechanism for initial load
  useEffect(() => {
    if (!loading && targets.length === 0 && retryCount < 2) {
      const delay = (retryCount + 1) * 1000;
      const timer = setTimeout(() => {
        console.log(`Retrying targets fetch (attempt ${retryCount + 1}) after initial empty result`);
        setRetryCount(prev => prev + 1);
        fetchTargets();
      }, delay);
      
      return () => clearTimeout(timer);
    }
  }, [loading, targets.length, retryCount]);

  const fetchTargets = async () => {
    try {
      console.log('Fetching targets...');
      const response = await enhancedTargetApi.list();
      console.log('Targets response:', response);
      const targetsList = response.targets || [];
      
      // Debug: Log service data for each target
      targetsList.forEach(target => {
        console.log(`Target ${target.id} (${target.ip_address}) services:`, target.services);
        target.services?.forEach(service => {
          console.log(`  - Service: ${service.service_type}:${service.port}, default: ${service.is_default}, cred_type: ${service.credential_type}`);
        });
      });
      
      setTargets([...targetsList]); // Force new array reference
      
      if (targetsList.length > 0) {
        setRetryCount(0);
      }
      
      return targetsList;
    } catch (error: any) {
      console.error('Failed to fetch targets:', error);
      
      // Log detailed error information for debugging
      if (error.response) {
        console.error('Error response status:', error.response.status);
        console.error('Error response data:', error.response.data);
        console.error('Error response headers:', error.response.headers);
      } else if (error.request) {
        console.error('No response received:', error.request);
      } else {
        console.error('Error message:', error.message);
      }
      
      if (error.response?.status === 401 || error.response?.status === 403) {
        console.log('Authentication error, targets will be empty until token refresh');
      } else if (error.response?.status === 500) {
        console.error('Server error (500): Backend service may be down or misconfigured');
      } else if (error.code === 'ECONNREFUSED' || error.code === 'ERR_NETWORK') {
        console.error('Network error: Unable to connect to backend service');
      }
      
      setTargets([]);
      return [];
    } finally {
      setLoading(false);
    }
  };

  const fetchCredentials = async () => {
    try {
      console.log('Fetching credentials...');
      // TODO: Implement credentials API endpoint
      // const response = await targetApi.listCredentials();
      // console.log('Credentials response:', response);
      // setCredentials(response.credentials || []);
      setCredentials([]);
    } catch (error: any) {
      console.error('Failed to fetch credentials:', error);
      setCredentials([]);
    }
  };

  const fetchTargetCredentials = async (targetId: number) => {
    try {
      console.log('Fetching target credentials for target:', targetId);
      const response = await targetCredentialApi.getForEditing(targetId);
      console.log('Target credentials response:', response);
      
      if (response.success && response.services) {
        // Update the editTarget state with the credential data
        setEditTarget(prev => ({
          ...prev,
          services: response.services.map(service => ({
            ...service,
            // Ensure all credential fields are present
            username: service.username || '',
            password: service.password || '',
            domain: service.domain || '',
            private_key: service.private_key || '',
            public_key: service.public_key || '',
            api_key: service.api_key || '',
            bearer_token: service.bearer_token || '',
            certificate: service.certificate || '',
            passphrase: service.passphrase || ''
          }))
        }));
      }
    } catch (error: any) {
      console.error('Failed to fetch target credentials:', error);
      // Don't throw error, just log it - the form should still work without credentials
    }
  };

  const fetchMetadata = async () => {
    try {
      console.log('Fetching metadata...');
      const response = await metadataApi.get();
      console.log('Metadata response:', response);
      console.log('Available credential types:', response.credential_types);
      setMetadata(response);
    } catch (error: any) {
      console.error('Failed to fetch metadata:', error);
      // Fallback to empty metadata
      setMetadata({
        credential_types: [],
        service_types: [],
        os_types: []
      });
    }
  };

  const startAddingNew = () => {
    setAddingNew(true);
    setEditingTarget(null);
    setSelectedTarget(null);
    setNewTarget({
      ip_address: '',
      os_type: '',
      tags: [],
      description: '',
      services: []
    });
    fetchCredentials(); // Fetch credentials when adding new target
  };

  const cancelAddingNew = () => {
    setAddingNew(false);
    setNewTarget({
      ip_address: '',
      os_type: '',
      tags: [],
      description: '',
      services: []
    });
  };

  const handleEdit = async (target: EnhancedTarget) => {
    console.log('Editing target:', target);
    console.log('Target services:', target.services);
    target.services?.forEach((service, index) => {
      console.log(`Service ${index} credential_type:`, service.credential_type);
    });
    setEditingTarget(target);
    setEditTarget({
      ip_address: target.ip_address || '',
      os_type: target.os_type || '',
      tags: target.tags || [],
      description: target.description || '',
      services: target.services || []
    });
    setAddingNew(false);
    setSelectedTarget(null);
    
    // Fetch the actual credentials for this target
    await fetchTargetCredentials(target.id);
  };

  const handleCancelEdit = () => {
    setEditingTarget(null);
    setEditTarget({
      ip_address: '',
      os_type: '',
      tags: [],
      description: '',
      services: []
    });
  };

  const handleSaveEdit = async () => {
    if (!editingTarget) return;

    // Validation
    if (!editTarget.ip_address.trim()) {
      alert('IP Address or FQDN is required');
      return;
    }

    try {
      setSaving(true);
      const updateData: any = {
        name: editTarget.ip_address,
        hostname: editTarget.ip_address,
        ip_address: editTarget.ip_address,
        os_type: editTarget.os_type || 'other',
        tags: editTarget.tags,
        description: editTarget.description,
        services: editTarget.services
          .filter(service => service.service_type && service.service_type.trim())
          .map(service => ({
            service_type: service.service_type,
            port: parseInt(service.port.toString()) || 22,
            is_default: service.is_default || false,
            is_secure: service.is_secure || false,
            is_enabled: service.is_enabled !== false, // Default to true unless explicitly false
            credential_type: service.credential_type,
            username: service.username || '',
            password: service.password || '',
            domain: service.domain || '',
            private_key: service.private_key || '',
            public_key: service.public_key || '',
            api_key: service.api_key || '',
            bearer_token: service.bearer_token || '',
            certificate: service.certificate || '',
            passphrase: service.passphrase || '',
            notes: service.notes || ''
          }))
      };
      
      await enhancedTargetApi.update(editingTarget.id, updateData);
      await fetchTargets();
      handleCancelEdit();
    } catch (error) {
      console.error('Failed to update target:', error);
      alert('Failed to update target');
    } finally {
      setSaving(false);
    }
  };

  // Service management functions
  const addService = () => {
    const isFirstService = newTarget.services.length === 0;
    const newService = {
      service_type: '',
      port: 22,
      is_default: isFirstService, // First service is default
      is_secure: false,
      is_enabled: true,
      notes: '',
      credential_type: '',
      username: '',
      password: '',
      private_key: '',
      public_key: '',
      api_key: '',
      bearer_token: '',
      certificate: '',
      passphrase: '',
      domain: ''
    };
    setNewTarget(prev => ({
      ...prev,
      services: [...prev.services, newService]
    }));
  };

  const updateService = (index: number, field: string, value: any) => {
    setNewTarget(prev => ({
      ...prev,
      services: prev.services.map((service, i) => {
        if (i === index) {
          const updatedService = { ...service, [field]: value };
          
          // If service_type is being updated, automatically set the default port and clear credentials
          if (field === 'service_type' && value && SERVICE_TYPES[value as keyof typeof SERVICE_TYPES]) {
            updatedService.port = SERVICE_TYPES[value as keyof typeof SERVICE_TYPES];
            // Clear credential fields when service type changes
            updatedService.credential_type = '';
            updatedService.username = '';
            updatedService.password = '';
            updatedService.private_key = '';
            updatedService.public_key = '';
            updatedService.api_key = '';
            updatedService.bearer_token = '';
            updatedService.certificate = '';
            updatedService.passphrase = '';
            updatedService.domain = '';
          }
          
          // If credential_type is being updated, clear irrelevant credential fields
          if (field === 'credential_type') {
            if (value !== 'username_password') {
              updatedService.username = '';
              updatedService.password = '';
              updatedService.domain = '';
            }
            if (value !== 'ssh_key') {
              updatedService.private_key = '';
              updatedService.public_key = '';
              updatedService.passphrase = '';
            }
            if (value !== 'api_key') {
              updatedService.api_key = '';
            }
            if (value !== 'bearer_token') {
              updatedService.bearer_token = '';
            }
            if (value !== 'certificate') {
              updatedService.certificate = '';
            }
          }
          
          return updatedService;
        }
        return service;
      })
    }));
  };

  const removeService = (index: number) => {
    setNewTarget(prev => {
      const remainingServices = prev.services.filter((_, i) => i !== index);
      const removedService = prev.services[index];
      
      // If we're removing the default service and there are other services, make the first one default
      if (removedService.is_default && remainingServices.length > 0) {
        remainingServices[0] = { ...remainingServices[0], is_default: true };
      }
      
      return {
        ...prev,
        services: remainingServices
      };
    });
  };

  const saveNewTarget = async () => {
    if (!newTarget.ip_address.trim()) {
      alert('IP Address or FQDN is required');
      return;
    }

    // Validate services
    const validServices = newTarget.services.filter(service => service.service_type && service.service_type.trim());
    if (validServices.length === 0) {
      alert('At least one service is required');
      return;
    }

    const defaultServices = validServices.filter(service => service.is_default);
    if (defaultServices.length === 0) {
      alert('Exactly one service must be marked as default');
      return;
    }
    if (defaultServices.length > 1) {
      alert('Only one service can be marked as default');
      return;
    }

    try {
      setSaving(true);
      const targetToCreate = {
        name: newTarget.ip_address,
        hostname: newTarget.ip_address,
        ip_address: newTarget.ip_address,
        os_type: (newTarget.os_type as 'windows' | 'linux' | 'unix' | 'macos' | 'other') || 'other',
        tags: newTarget.tags,
        description: newTarget.description,
        services: newTarget.services
          .filter(service => service.service_type && service.service_type.trim())
          .map(service => ({
            service_type: service.service_type,
            port: parseInt(service.port.toString()) || 22,
            is_default: service.is_default || false,
            is_secure: service.is_secure || false,
            is_enabled: service.is_enabled !== false, // Default to true
            notes: service.notes || '',
            credential_type: service.credential_type || undefined,
            username: service.username || undefined,
            password: service.password || undefined,
            private_key: service.private_key || undefined,
            public_key: service.public_key || undefined,
            api_key: service.api_key || undefined,
            bearer_token: service.bearer_token || undefined,
            certificate: service.certificate || undefined,
            passphrase: service.passphrase || undefined,
            domain: service.domain || undefined
          }))
      };
      
      await enhancedTargetApi.create(targetToCreate);
      await fetchTargets();
      cancelAddingNew();
    } catch (error) {
      console.error('Failed to create target:', error);
      alert('Failed to create target');
    } finally {
      setSaving(false);
    }
  };

  const handleDelete = async (targetId: number) => {
    if (window.confirm('Delete this target? This action cannot be undone.')) {
      try {
        await targetApi.delete(targetId);
        fetchTargets();
        if (selectedTarget?.id === targetId) {
          setSelectedTarget(null);
        }
      } catch (error) {
        console.error('Failed to delete target:', error);
      }
    }
  };

  const handleTargetClick = (target: EnhancedTarget) => {
    // The enhanced API list already returns all target data including services
    setSelectedTarget(target);
    setAddingNew(false);
    setEditingTarget(null);
  };

  const testServiceConnection = async (serviceId: number) => {
    setTestingConnections(prev => new Set(prev).add(serviceId));
    
    try {
      // Find the service details from the selected target
      const service = selectedTarget?.services?.find(s => s.id === serviceId);
      if (!service || !selectedTarget) {
        throw new Error('Service or target not found');
      }

      // Prepare connection data for automation service
      const connectionData = {
        host: selectedTarget.ip_address || selectedTarget.hostname || '',
        port: service.port,
        service_type: service.service_type,
        credential_type: service.credential_type,
        username: service.username,
        service_id: serviceId,
        target_id: selectedTarget.id
      };

      if (!connectionData.host) {
        throw new Error('No host or IP address available for target');
      }

      // Call the automation service test connection endpoint
      const result = await automationApi.testConnection(connectionData);
      
      // Refresh the target data to get updated connection status
      const updatedTargets = await fetchTargets();
      
      // Update the selected target with fresh data
      if (selectedTarget) {
        const updatedTarget = updatedTargets.find(t => t.id === selectedTarget.id);
        if (updatedTarget) {
          setSelectedTarget(updatedTarget);
        }
      }
      
      // Show success/failure message
      if (result.success) {
        alert(`Connection test successful: Service is reachable`);
      } else {
        alert(`Connection test failed: ${result.error || 'Service is not reachable'}`);
      }
    } catch (error) {
      console.error('Failed to test service connection:', error);
      alert(`Failed to test connection: ${error instanceof Error ? error.message : 'Unknown error'}`);
    } finally {
      setTestingConnections(prev => {
        const newSet = new Set(prev);
        newSet.delete(serviceId);
        return newSet;
      });
    }
  };

  // Sorting functions
  const handleSort = (field: string) => {
    if (sortField === field) {
      setSortDirection(sortDirection === 'asc' ? 'desc' : 'asc');
    } else {
      setSortField(field);
      setSortDirection('asc');
    }
  };

  const sortedTargets = useMemo(() => {
    console.log('Recalculating sortedTargets with', targets.length, 'targets');
    return [...targets].sort((a, b) => {
      let aValue: any = a[sortField as keyof EnhancedTarget];
      let bValue: any = b[sortField as keyof EnhancedTarget];
      
      // Handle special cases
      if (sortField === 'ip_address') {
        aValue = a.ip_address || a.hostname || '';
        bValue = b.ip_address || b.hostname || '';
      }
      
      // Convert to strings for comparison
      aValue = String(aValue || '').toLowerCase();
      bValue = String(bValue || '').toLowerCase();
      
      if (sortDirection === 'asc') {
        return aValue.localeCompare(bValue);
      } else {
        return bValue.localeCompare(aValue);
      }
    });
  }, [targets, sortField, sortDirection]);

  const getSortIcon = (field: string) => {
    if (sortField !== field) {
      return '↕️'; // Both arrows when not sorted
    }
    return sortDirection === 'asc' ? '↑' : '↓';
  };

  const getTargetStatus = (target: EnhancedTarget) => {
    if (target.services && target.services.length > 0) {
      const connectedServices = target.services.filter(s => s.connection_status === 'connected');
      const failedServices = target.services.filter(s => s.connection_status === 'failed');
      
      if (connectedServices.length === target.services.length) {
        return 'Online';
      } else if (failedServices.length === target.services.length) {
        return 'Offline';
      } else if (connectedServices.length > 0) {
        return 'Partial';
      }
    }
    return 'Unknown';
  };

  if (loading) {
    return (
      <div className="loading-overlay">
        <div className="loading-spinner"></div>
      </div>
    );
  }

  return (
    <div className="dense-dashboard">
      <style>
        {`
          /* Dashboard-style layout - EXACT MATCH */
          .dense-dashboard {
            padding: 8px 12px;
            max-width: 100%;
            font-size: 13px;
          }
          .dashboard-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 12px;
            padding-bottom: 8px;
            border-bottom: 1px solid var(--neutral-200);
          }
          .header-left h1 {
            font-size: 18px;
            font-weight: 600;
            margin: 0;
            color: var(--neutral-800);
          }
          .dashboard-grid {
            display: grid;
            grid-template-columns: 1fr 1fr 1fr;
            gap: 12px;
            align-items: stretch;
            height: calc(100vh - 110px);
          }
          .dashboard-section {
            background: white;
            border: 1px solid var(--neutral-200);
            border-radius: 6px;
            overflow: hidden;
            display: flex;
            flex-direction: column;
            height: 100%;
          }
          .section-header {
            background: var(--neutral-50);
            padding: 8px 12px;
            font-weight: 600;
            font-size: 13px;
            color: var(--neutral-700);
            border-bottom: 1px solid var(--neutral-200);
            display: flex;
            justify-content: space-between;
            align-items: center;
          }
          .compact-content {
            padding: 16px;
            flex: 1;
            display: flex;
            flex-direction: column;
            overflow: auto;
          }
          .table-container {
            flex: 1;
            overflow: auto;
          }
          
          /* Targets table styles */
          .targets-table-section {
            grid-column: 1 / 3;
          }
          .targets-table {
            width: 100%;
            border-collapse: collapse;
            font-size: 12px;
          }
          .targets-table th {
            background: var(--neutral-50);
            padding: 6px 8px;
            text-align: left;
            font-weight: 600;
            color: var(--neutral-700);
            border-bottom: 1px solid var(--neutral-200);
            font-size: 11px;
          }
          .targets-table td {
            padding: 6px 8px;
            border-bottom: 1px solid var(--neutral-100);
            vertical-align: middle;
            font-size: 12px;
          }
          .targets-table tr:hover {
            background: var(--neutral-50);
          }
          .targets-table tr.selected {
            background: var(--primary-blue-light);
            border-left: 3px solid var(--primary-blue);
          }
          .targets-table tr {
            cursor: pointer;
          }
          .sortable-header {
            cursor: pointer;
            user-select: none;
            transition: background-color 0.2s ease;
          }
          .sortable-header:hover {
            background: var(--neutral-100) !important;
          }
          
          /* Form styles - UNIFIED PATTERN */
          .form-field {
            display: flex;
            flex-direction: column;
            gap: 4px;
            margin-bottom: 16px;
          }
          .form-label {
            font-size: 12px;
            font-weight: 600;
            color: var(--neutral-700);
          }
          .form-label.required::after {
            content: ' *';
            color: var(--danger-red);
          }
          .form-input {
            width: 100%;
            padding: 8px 12px;
            border: 1px solid var(--neutral-200);
            background: white;
            border-radius: 4px;
            font-size: 13px;
            color: var(--neutral-900);
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
          .form-select {
            width: 100%;
            padding: 8px 12px;
            border: 1px solid var(--neutral-200);
            background: white;
            border-radius: 4px;
            font-size: 13px;
            color: var(--neutral-900);
            cursor: pointer;
          }
          .form-select:focus {
            outline: none;
            border-color: var(--primary-blue);
            box-shadow: 0 0 0 2px var(--primary-blue-light);
          }
          .form-select:disabled {
            background: var(--neutral-50);
            color: var(--neutral-600);
            cursor: not-allowed;
          }
          
          /* Button styles */
          .btn-icon {
            display: inline-flex;
            align-items: center;
            justify-content: center;
            width: 24px;
            height: 24px;
            border: none;
            background: none;
            cursor: pointer;
            transition: all 0.15s;
            margin: 0 1px;
            padding: 2px;
          }
          .btn-icon:hover {
            opacity: 0.7;
          }
          .btn-icon:disabled {
            opacity: 0.3;
            cursor: not-allowed;
          }
          .btn-success {
            color: var(--success-green);
          }
          .btn-success:hover:not(:disabled) {
            color: var(--success-green-dark);
          }
          .btn-danger {
            color: var(--danger-red);
          }
          .btn-danger:hover:not(:disabled) {
            color: var(--danger-red);
          }
          .btn-ghost {
            color: var(--neutral-500);
          }
          .btn-ghost:hover:not(:disabled) {
            color: var(--neutral-700);
          }
          
          .empty-state {
            display: flex;
            flex-direction: column;
            align-items: center;
            justify-content: center;
            padding: 48px 24px;
            text-align: center;
            color: var(--neutral-500);
          }
          
          .status-badge {
            padding: 2px 6px;
            border-radius: 3px;
            font-size: 10px;
            font-weight: 600;
            text-transform: uppercase;
          }
          .status-badge-success {
            background: var(--success-green-light);
            color: var(--success-green-dark);
          }
          .status-badge-danger {
            background: var(--danger-red-light);
            color: var(--danger-red-dark);
          }
          .status-badge-warning {
            background: var(--warning-yellow-light);
            color: var(--warning-yellow-dark);
          }
          .status-badge-neutral {
            background: var(--neutral-100);
            color: var(--neutral-600);
          }
          @keyframes spin {
            0% { transform: rotate(0deg); }
            100% { transform: rotate(360deg); }
          }
        `}
      </style>

      {/* Dashboard-style header */}
      <div className="dashboard-header">
        <div className="header-left">
          <h1>Target Management</h1>
        </div>
        <div className="header-actions">
          <button 
            className="btn-icon btn-success"
            onClick={startAddingNew}
            title="Add new target"
            disabled={addingNew}
          >
            <Plus size={16} />
          </button>
        </div>
      </div>

      {/* 3-column dashboard grid */}
      <div className="dashboard-grid">
        {/* Column 1-2: Targets Table */}
        <div className="dashboard-section targets-table-section">
          <div className="section-header">
            Targets ({targets.length})
          </div>
          <div className="compact-content">
            {loading ? (
              <div>Loading targets...</div>
            ) : targets.length === 0 ? (
              <div className="empty-state">
                <h3>No targets found</h3>
                <p>Create your first target to start managing infrastructure.</p>
                <button 
                  className="btn-icon btn-success"
                  onClick={startAddingNew}
                  title="Create first target"
                >
                  <Plus size={16} />
                </button>
              </div>
            ) : (
              <div className="table-container">
                <table className="targets-table">
                  <thead>
                    <tr>
                      <th 
                        className="sortable-header" 
                        onClick={() => handleSort('ip_address')}
                        title="Click to sort by IP Address/FQDN"
                      >
                        IP Address/FQDN {getSortIcon('ip_address')}
                      </th>
                      <th>OS</th>
                      <th>Default Service</th>
                      <th>Credential Type</th>
                      <th>Status</th>
                      <th>Tags</th>
                      <th>Actions</th>
                    </tr>
                  </thead>
                  <tbody>
                    {sortedTargets.map((target) => (
                      <tr 
                        key={`${target.id}-${target.updated_at}-${target.services?.length || 0}`} 
                        className={selectedTarget?.id === target.id ? 'selected' : ''}
                        onClick={() => handleTargetClick(target)}
                      >
                        <td>{target.ip_address}</td>
                        <td>{target.os_type}</td>
                        <td>
                          {(() => {
                            console.log(`Target ${target.id} all services:`, target.services);
                            const defaultService = target.services?.find(s => {
                              console.log(`  Checking service: ${s.service_type}, is_default: ${s.is_default} (${typeof s.is_default})`);
                              return s.is_default === true;
                            });
                            console.log(`Target ${target.id} found default service:`, defaultService);
                            if (defaultService) {
                              const displayName = SERVICE_DISPLAY_NAMES[defaultService.service_type] || defaultService.service_type;
                              console.log(`Target ${target.id} display name: ${displayName}`);
                              return (
                                <div style={{ fontSize: '12px', fontWeight: '500' }}>
                                  {displayName}:{defaultService.port}
                                </div>
                              );
                            }
                            return <span style={{ color: 'var(--neutral-500)', fontSize: '12px' }}>No default</span>;
                          })()}
                        </td>
                        <td>
                          {(() => {
                            const defaultService = target.services?.find(s => s.is_default);
                            console.log(`Target ${target.id} credential type:`, defaultService?.credential_type);
                            if (defaultService && defaultService.credential_type) {
                              return (
                                <div style={{ fontSize: '12px', color: 'var(--primary-700)' }}>
                                  {getCredentialSummary(defaultService)}
                                </div>
                              );
                            }
                            return <span style={{ color: 'var(--neutral-500)', fontSize: '12px' }}>None</span>;
                          })()}
                        </td>
                        <td>
                          {(() => {
                            const defaultService = target.services?.find(s => s.is_default);
                            if (defaultService) {
                              const status = defaultService.connection_status || 'unknown';
                              return (
                                <span className={`status-badge ${
                                  status === 'connected' ? 'status-badge-success' : 
                                  status === 'failed' ? 'status-badge-danger' : 
                                  'status-badge-neutral'
                                }`}>
                                  {status === 'connected' ? 'Connected' : 
                                   status === 'failed' ? 'Failed' : 
                                   'Unknown'}
                                </span>
                              );
                            }
                            return <span className="status-badge status-badge-neutral">Unknown</span>;
                          })()}
                        </td>
                        <td>{target.tags?.join(', ') || '-'}</td>
                        <td>
                          <div style={{ display: 'flex', gap: '4px' }}>
                            <button 
                              className="btn-icon btn-ghost"
                              onClick={(e) => {
                                e.stopPropagation();
                                handleEdit(target);
                              }}
                              title="Edit target details"
                            >
                              <Edit3 size={14} />
                            </button>
                            <button 
                              className="btn-icon btn-danger"
                              onClick={(e) => {
                                e.stopPropagation();
                                handleDelete(target.id);
                              }}
                              title="Delete target"
                            >
                              <Trash2 size={14} />
                            </button>
                          </div>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </div>
        </div>

        {/* Column 3: Target Details/Form - UNIFIED PATTERN */}
        <div className="dashboard-section">
          {addingNew ? (
            <>
              <div className="section-header" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <span>Create New Target</span>
                <div style={{ display: 'flex', gap: '8px' }}>
                  <button 
                    onClick={saveNewTarget}
                    className="btn-icon btn-success"
                    disabled={saving}
                    title="Create Target"
                  >
                    <Check size={16} />
                  </button>
                  <button 
                    onClick={cancelAddingNew}
                    className="btn-icon btn-ghost"
                    title="Cancel"
                  >
                    <X size={16} />
                  </button>
                </div>
              </div>
              <div className="compact-content">
                <div className="target-details">
                  <style>{`
                    .subtle-input {
                      width: 100%;
                      padding: 8px 12px;
                      border: 1px solid var(--neutral-200);
                      background: white;
                      border-radius: 4px;
                      font-size: 13px;
                      color: var(--neutral-900);
                    }
                    .subtle-input:focus {
                      outline: none;
                    }
                    .subtle-input::placeholder {
                      color: var(--neutral-400);
                    }
                    .subtle-select {
                      width: 100%;
                      padding: 8px 12px;
                      border: 1px solid var(--neutral-200);
                      background: white;
                      border-radius: 4px;
                      font-size: 13px;
                      color: var(--neutral-900);
                      cursor: pointer;
                    }
                    .subtle-select:focus {
                      outline: none;
                    }
                    .target-form-grid {
                      display: grid;
                      grid-template-columns: 2fr 1fr 1fr;
                      gap: 20px;
                      margin-bottom: 20px;
                    }
                    .form-field {
                      display: flex;
                      flex-direction: column;
                      gap: 2px;
                    }
                    .form-label {
                      font-size: 12px;
                      font-weight: 600;
                      color: var(--neutral-700);
                    }
                    .form-label.required::after {
                      content: ' *';
                      color: var(--primary-red);
                    }
                    .char-counter {
                      font-size: 11px;
                      color: var(--neutral-500);
                      text-align: right;
                      margin-top: 2px;
                    }
                  `}</style>
                  <div className="target-form-grid">
                    {/* Column 1 - Primary Field */}
                    <div>
                      <div className="form-field">
                        <label className="form-label required">IP Address / FQDN</label>
                        <input
                          type="text"
                          value={newTarget.ip_address}
                          onChange={(e) => setNewTarget({...newTarget, ip_address: e.target.value})}
                          className="subtle-input"
                          autoFocus
                        />
                      </div>

                      <div className="form-field">
                        <label className="form-label">Tags</label>
                        <input
                          type="text"
                          value={newTarget.tags.join(', ')}
                          onChange={(e) => setNewTarget({...newTarget, tags: e.target.value.split(',').map(t => t.trim()).filter(t => t)})}
                          className="subtle-input"
                        />
                      </div>
                    </div>

                    {/* Column 2 */}
                    <div>
                      <div className="form-field">
                        <label className="form-label">Operating System</label>
                        <select 
                          value={newTarget.os_type} 
                          onChange={(e) => setNewTarget({...newTarget, os_type: e.target.value})}
                          className="subtle-select"
                        >
                          <option value="">Select OS</option>
                          <option value="windows">Windows</option>
                          <option value="linux">Linux</option>
                          <option value="macos">macOS</option>
                        </select>
                      </div>
                    </div>

                    {/* Column 3 */}
                    <div>
                      <div className="form-field">
                        <label className="form-label">Description</label>
                        <input
                          type="text"
                          value={newTarget.description}
                          onChange={(e) => {
                            const value = e.target.value;
                            if (value.length <= 20) {
                              setNewTarget({...newTarget, description: value});
                            }
                          }}
                          className="subtle-input"
                          maxLength={20}
                        />
                      </div>
                    </div>
                  </div>

                  {/* Services Section */}
                  <div style={{ marginTop: '20px' }}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '8px' }}>
                      <label className="form-label" style={{ margin: 0 }}>Services & Communication Types</label>
                      <button 
                        onClick={addService}
                        className="btn-icon btn-success"
                        title="Add Service"
                        type="button"
                      >
                        <Plus size={14} />
                      </button>
                    </div>

                    {newTarget.services.length === 0 ? (
                      <div style={{ 
                        padding: '12px 0', 
                        color: 'var(--neutral-500)',
                        fontSize: '13px',
                        textAlign: 'center',
                        fontStyle: 'italic'
                      }}>
                        No services configured. Click + to add a service.
                      </div>
                    ) : (
                      <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
                        {newTarget.services.map((service, index) => (
                          <div key={index} style={{ 
                            border: '1px solid var(--neutral-200)',
                            borderRadius: '8px',
                            padding: '16px',
                            marginBottom: '16px',
                            backgroundColor: service.is_default ? 'var(--primary-50)' : 'var(--neutral-25)'
                          }}>
                            {/* Service Header */}
                            <div style={{ 
                              display: 'flex', 
                              justifyContent: 'space-between', 
                              alignItems: 'center',
                              marginBottom: '16px'
                            }}>
                              <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                                <h4 style={{ margin: 0, fontSize: '14px', fontWeight: '600' }}>
                                  Service {index + 1}
                                </h4>
                                {service.is_default && (
                                  <span style={{ 
                                    fontSize: '10px', 
                                    padding: '2px 6px', 
                                    backgroundColor: 'var(--primary-100)', 
                                    color: 'var(--primary-700)',
                                    borderRadius: '4px',
                                    fontWeight: '500'
                                  }}>
                                    DEFAULT
                                  </span>
                                )}
                              </div>
                              <div style={{ display: 'flex', gap: '4px' }}>
                                <button 
                                  className="btn-icon btn-ghost"
                                  title="Test Connection"
                                  type="button"
                                >
                                  <MonitorCheck size={14} />
                                </button>
                                <button 
                                  onClick={() => removeService(index)}
                                  className="btn-icon btn-ghost"
                                  title="Remove Service"
                                  type="button"
                                >
                                  <Trash2 size={14} />
                                </button>
                              </div>
                            </div>

                            {/* Basic Service Info */}
                            <div style={{ 
                              display: 'grid', 
                              gridTemplateColumns: '2fr 1fr 1fr', 
                              gap: '12px',
                              marginBottom: '16px'
                            }}>
                              <div style={{ display: 'flex', flexDirection: 'column', gap: '2px' }}>
                                <label style={{ fontSize: '11px', color: 'var(--neutral-600)', fontWeight: '500', margin: 0 }}>Service Type</label>
                                <select
                                  value={service.service_type}
                                  onChange={(e) => updateService(index, 'service_type', e.target.value)}
                                  className="subtle-select"
                                  style={{ fontSize: '12px' }}
                                >
                                  <option value="">Select Service</option>
                                  {Object.entries(SERVICE_TYPES).map(([type, port]) => (
                                    <option key={type} value={type}>
                                      {SERVICE_DISPLAY_NAMES[type] || type} ({port})
                                    </option>
                                  ))}
                                </select>
                              </div>

                              <div style={{ display: 'flex', flexDirection: 'column', gap: '2px' }}>
                                <label style={{ fontSize: '11px', color: 'var(--neutral-600)', fontWeight: '500', margin: 0 }}>Port</label>
                                <input
                                  type="number"
                                  value={service.port}
                                  onChange={(e) => updateService(index, 'port', parseInt(e.target.value) || 22)}
                                  className="subtle-input"
                                  style={{ fontSize: '12px' }}
                                  min="1"
                                  max="65535"
                                />
                              </div>

                              <div style={{ display: 'flex', flexDirection: 'column', gap: '2px' }}>
                                <label style={{ fontSize: '11px', color: 'var(--neutral-600)', fontWeight: '500', margin: 0 }}>Default Service</label>
                                <label style={{ display: 'flex', alignItems: 'center', gap: '6px', fontSize: '12px' }}>
                                  <input
                                    type="radio"
                                    name="defaultService"
                                    checked={service.is_default || false}
                                    onChange={() => {
                                      // Set this service as default and unset others
                                      const updatedServices = newTarget.services.map((s, i) => ({
                                        ...s,
                                        is_default: i === index
                                      }));
                                      setNewTarget({ ...newTarget, services: updatedServices });
                                    }}
                                  />
                                  Use as default
                                </label>
                              </div>
                            </div>

                            {/* Credentials Section */}
                            {service.service_type && (
                              <div style={{ 
                                borderTop: '1px solid var(--neutral-200)',
                                paddingTop: '16px'
                              }}>
                                <h5 style={{ margin: '0 0 12px 0', fontSize: '12px', fontWeight: '600', color: 'var(--neutral-700)' }}>
                                  Credentials (Optional)
                                </h5>
                                
                                <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
                                  {/* Credential Type */}
                                  <div style={{ display: 'flex', flexDirection: 'column', gap: '2px' }}>
                                    <label style={{ fontSize: '11px', color: 'var(--neutral-600)', fontWeight: '500', margin: 0 }}>Credential Type</label>
                                    <select
                                      value={service.credential_type || ''}
                                      onChange={(e) => updateService(index, 'credential_type', e.target.value)}
                                      className="subtle-select"
                                      style={{ fontSize: '12px' }}
                                    >
                                      <option value="">No Credentials</option>
                                      {metadata?.credential_types?.map(credType => (
                                        <option key={credType.value} value={credType.value}>
                                          {credType.label}
                                        </option>
                                      )) || [
                                        <option key="username_password" value="username_password">Username/Password</option>,
                                        <option key="ssh_key" value="ssh_key">SSH Key</option>,
                                        <option key="api_key" value="api_key">API Key</option>,
                                        <option key="bearer_token" value="bearer_token">Bearer Token</option>
                                      ]}
                                    </select>
                                  </div>

                                  {/* Credential Fields based on type */}
                                  {service.credential_type === 'username_password' && (
                                    <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr 1fr', gap: '12px' }}>
                                      <div style={{ display: 'flex', flexDirection: 'column', gap: '2px' }}>
                                        <label style={{ fontSize: '11px', color: 'var(--neutral-600)', fontWeight: '500', margin: 0 }}>Username</label>
                                        <input
                                          type="text"
                                          value={service.username || ''}
                                          onChange={(e) => updateService(index, 'username', e.target.value)}
                                          className="subtle-input"
                                          style={{ fontSize: '12px' }}
                                          placeholder="Enter username"
                                        />
                                      </div>
                                      <div style={{ display: 'flex', flexDirection: 'column', gap: '2px' }}>
                                        <label style={{ fontSize: '11px', color: 'var(--neutral-600)', fontWeight: '500', margin: 0 }}>Password</label>
                                        <input
                                          type="password"
                                          value={service.password || ''}
                                          onChange={(e) => updateService(index, 'password', e.target.value)}
                                          className="subtle-input"
                                          style={{ fontSize: '12px' }}
                                          placeholder="Enter password"
                                        />
                                      </div>
                                      <div style={{ display: 'flex', flexDirection: 'column', gap: '2px' }}>
                                        <label style={{ fontSize: '11px', color: 'var(--neutral-600)', fontWeight: '500', margin: 0 }}>Domain (Optional)</label>
                                        <input
                                          type="text"
                                          value={service.domain || ''}
                                          onChange={(e) => updateService(index, 'domain', e.target.value)}
                                          className="subtle-input"
                                          style={{ fontSize: '12px' }}
                                          placeholder="Windows domain"
                                        />
                                      </div>
                                    </div>
                                  )}

                                  {service.credential_type === 'ssh_key' && (
                                    <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '12px' }}>
                                      <div style={{ display: 'flex', flexDirection: 'column', gap: '2px' }}>
                                        <label style={{ fontSize: '11px', color: 'var(--neutral-600)', fontWeight: '500', margin: 0 }}>Username</label>
                                        <input
                                          type="text"
                                          value={service.username || ''}
                                          onChange={(e) => updateService(index, 'username', e.target.value)}
                                          className="subtle-input"
                                          style={{ fontSize: '12px' }}
                                          placeholder="Enter username"
                                        />
                                      </div>
                                      <div style={{ display: 'flex', flexDirection: 'column', gap: '2px' }}>
                                        <label style={{ fontSize: '11px', color: 'var(--neutral-600)', fontWeight: '500', margin: 0 }}>Passphrase (Optional)</label>
                                        <input
                                          type="password"
                                          value={service.passphrase || ''}
                                          onChange={(e) => updateService(index, 'passphrase', e.target.value)}
                                          className="subtle-input"
                                          style={{ fontSize: '12px' }}
                                          placeholder="Key passphrase"
                                        />
                                      </div>
                                      <div style={{ gridColumn: '1 / -1', display: 'flex', flexDirection: 'column', gap: '2px' }}>
                                        <label style={{ fontSize: '11px', color: 'var(--neutral-600)', fontWeight: '500', margin: 0 }}>Private Key</label>
                                        <textarea
                                          value={service.private_key || ''}
                                          onChange={(e) => updateService(index, 'private_key', e.target.value)}
                                          className="subtle-input"
                                          style={{ fontSize: '12px', minHeight: '80px', fontFamily: 'monospace' }}
                                          placeholder="-----BEGIN PRIVATE KEY-----"
                                        />
                                      </div>
                                    </div>
                                  )}

                                  {service.credential_type === 'api_key' && (
                                    <div style={{ display: 'flex', flexDirection: 'column', gap: '2px' }}>
                                      <label style={{ fontSize: '11px', color: 'var(--neutral-600)', fontWeight: '500', margin: 0 }}>API Key</label>
                                      <input
                                        type="password"
                                        value={service.api_key || ''}
                                        onChange={(e) => updateService(index, 'api_key', e.target.value)}
                                        className="subtle-input"
                                        style={{ fontSize: '12px' }}
                                        placeholder="Enter API key"
                                      />
                                    </div>
                                  )}

                                  {service.credential_type === 'bearer_token' && (
                                    <div style={{ display: 'flex', flexDirection: 'column', gap: '2px' }}>
                                      <label style={{ fontSize: '11px', color: 'var(--neutral-600)', fontWeight: '500', margin: 0 }}>Bearer Token</label>
                                      <input
                                        type="password"
                                        value={service.bearer_token || ''}
                                        onChange={(e) => updateService(index, 'bearer_token', e.target.value)}
                                        className="subtle-input"
                                        style={{ fontSize: '12px' }}
                                        placeholder="Enter bearer token"
                                      />
                                    </div>
                                  )}
                                </div>
                              </div>
                            )}

                            {/* Notes */}
                            <div style={{ 
                              borderTop: '1px solid var(--neutral-200)',
                              paddingTop: '12px',
                              marginTop: '12px'
                            }}>
                              <div style={{ display: 'flex', flexDirection: 'column', gap: '2px' }}>
                                <label style={{ fontSize: '11px', color: 'var(--neutral-600)', fontWeight: '500', margin: 0 }}>Notes (Optional)</label>
                                <input
                                  type="text"
                                  value={service.notes || ''}
                                  onChange={(e) => updateService(index, 'notes', e.target.value)}
                                  className="subtle-input"
                                  style={{ fontSize: '12px' }}
                                  placeholder="Additional notes about this service"
                                />
                              </div>
                            </div>
                          </div>
                        ))}
                      </div>
                    )}
                  </div>
                </div>
              </div>
            </>
          ) : editingTarget ? (
            <>
              <div className="section-header">
                <span>Edit Target: {editingTarget.ip_address}</span>
                <div style={{ display: 'flex', gap: '4px' }}>
                  <button 
                    className="btn-icon btn-success"
                    onClick={handleSaveEdit}
                    disabled={saving}
                    title="Update Target"
                  >
                    <Check size={16} />
                  </button>
                  <button 
                    className="btn-icon btn-ghost"
                    onClick={handleCancelEdit}
                    disabled={saving}
                    title="Cancel"
                  >
                    <X size={16} />
                  </button>
                </div>
              </div>
              <div className="compact-content">
                <div className="target-form">
                  <style>{`
                    .target-form-grid {
                      display: grid;
                      grid-template-columns: 2fr 1fr 1fr;
                      gap: 20px;
                      margin-bottom: 20px;
                    }
                    .form-field {
                      display: flex;
                      flex-direction: column;
                      gap: 2px;
                    }
                    .form-label {
                      font-size: 12px;
                      font-weight: 600;
                      color: var(--neutral-700);
                    }
                    .form-label.required::after {
                      content: ' *';
                      color: var(--primary-red);
                    }
                    .form-input {
                      width: 100%;
                      padding: 8px 12px;
                      border: 1px solid var(--neutral-300);
                      background: white;
                      border-radius: 4px;
                      font-size: 13px;
                      color: var(--neutral-900);
                    }
                    .form-input:focus {
                      outline: none;
                      border-color: var(--primary-blue);
                      box-shadow: 0 0 0 2px rgba(59, 130, 246, 0.1);
                    }
                    .form-input::placeholder {
                      color: var(--neutral-400);
                    }
                    .form-select {
                      width: 100%;
                      padding: 8px 12px;
                      border: 1px solid var(--neutral-300);
                      background: white;
                      border-radius: 4px;
                      font-size: 13px;
                      color: var(--neutral-900);
                      cursor: pointer;
                    }
                    .form-select:focus {
                      outline: none;
                      border-color: var(--primary-blue);
                      box-shadow: 0 0 0 2px rgba(59, 130, 246, 0.1);
                    }
                    .char-counter {
                      font-size: 11px;
                      color: var(--neutral-500);
                      text-align: right;
                      margin-top: 2px;
                    }
                  `}</style>
                  <div className="target-form-grid">
                    {/* Column 1 - Primary Field */}
                    <div>
                      <div className="form-field">
                        <label className="form-label required">IP Address / FQDN</label>
                        <input
                          type="text"
                          value={editTarget.ip_address}
                          onChange={(e) => setEditTarget(prev => ({ ...prev, ip_address: e.target.value }))}
                          className="form-input"
                          autoFocus
                        />
                      </div>

                      <div className="form-field">
                        <label className="form-label">Tags</label>
                        <input
                          type="text"
                          value={editTarget.tags.join(', ')}
                          onChange={(e) => {
                            const tags = e.target.value.split(',').map(t => t.trim()).filter(t => t);
                            setEditTarget(prev => ({ ...prev, tags }));
                          }}
                          className="form-input"
                          placeholder="Comma-separated tags (e.g. web,production,database)"
                        />
                      </div>
                    </div>

                    {/* Column 2 */}
                    <div>
                      <div className="form-field">
                        <label className="form-label">Operating System</label>
                        <select 
                          value={editTarget.os_type}
                          onChange={(e) => setEditTarget(prev => ({ ...prev, os_type: e.target.value }))}
                          className="form-select"
                        >
                          <option value="">Select OS</option>
                          <option value="windows">Windows</option>
                          <option value="linux">Linux</option>
                          <option value="macos">macOS</option>
                        </select>
                      </div>
                    </div>

                    {/* Column 3 */}
                    <div>
                      <div className="form-field">
                        <label className="form-label">Description</label>
                        <input
                          type="text"
                          value={editTarget.description}
                          onChange={(e) => {
                            const value = e.target.value;
                            if (value.length <= 20) {
                              setEditTarget(prev => ({ ...prev, description: value }));
                            }
                          }}
                          className="form-input"
                          maxLength={20}
                        />
                        <div className="char-counter">
                          {editTarget.description.length}/20
                        </div>
                      </div>
                    </div>
                  </div>

                  {/* Services Section */}
                  <div style={{ marginTop: '20px' }}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '8px' }}>
                      <label className="form-label" style={{ margin: 0 }}>Services & Communication Types</label>
                      <span style={{ 
                        fontSize: '12px', 
                        color: 'var(--neutral-500)',
                        fontWeight: 'normal'
                      }}>
                        ({editTarget.services?.length || 0} configured)
                      </span>
                      <button 
                        onClick={() => {
                          const newService = {
                            service_type: '',
                            port: '',
                            credential_id: ''
                          };
                          setEditTarget(prev => ({
                            ...prev,
                            services: [...(prev.services || []), newService]
                          }));
                        }}
                        className="btn-icon btn-primary"
                        title="Add Service"
                        type="button"
                        style={{ marginLeft: 'auto' }}
                      >
                        <Plus size={14} />
                      </button>
                    </div>

                    {!editTarget.services || editTarget.services.length === 0 ? (
                      <div style={{ 
                        padding: '12px 0', 
                        color: 'var(--neutral-500)',
                        fontSize: '13px',
                        textAlign: 'center',
                        fontStyle: 'italic'
                      }}>
                        No services configured. Click + to add a service.
                      </div>
                    ) : (
                      <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
                        {editTarget.services.map((service, index) => (
                          <div key={index} style={{ 
                            display: 'grid', 
                            gridTemplateColumns: '2fr 1fr 2fr auto auto', 
                            gap: '12px', 
                            alignItems: 'end',
                            padding: '8px',
                            backgroundColor: 'var(--neutral-50)',
                            borderRadius: '4px',
                            border: '1px solid var(--neutral-200)'
                          }}>
                            {/* Service Type */}
                            <div style={{ display: 'flex', flexDirection: 'column', gap: '2px' }}>
                              <label style={{ fontSize: '11px', color: 'var(--neutral-600)', fontWeight: '500', margin: 0 }}>Service Type</label>
                              <select
                                value={service.service_type || ''}
                                onChange={(e) => {
                                  const newServices = [...editTarget.services];
                                  newServices[index] = { ...service, service_type: e.target.value };
                                  // Auto-fill port if available
                                  const defaultPort = SERVICE_TYPES[e.target.value as keyof typeof SERVICE_TYPES];
                                  if (defaultPort) {
                                    newServices[index].port = defaultPort.toString();
                                  }
                                  setEditTarget(prev => ({ ...prev, services: newServices }));
                                }}
                                className="form-select"
                                style={{ fontSize: '12px', padding: '6px 8px' }}
                              >
                                <option value="">Select Service</option>
                                {Object.entries(SERVICE_TYPES).map(([type, port]) => (
                                  <option key={type} value={type}>
                                    {SERVICE_DISPLAY_NAMES[type] || type} ({port})
                                  </option>
                                ))}
                              </select>
                            </div>

                            {/* Port */}
                            <div style={{ display: 'flex', flexDirection: 'column', gap: '2px' }}>
                              <label style={{ fontSize: '11px', color: 'var(--neutral-600)', fontWeight: '500', margin: 0 }}>Port</label>
                              <input
                                type="number"
                                value={service.port || ''}
                                onChange={(e) => {
                                  const newServices = [...editTarget.services];
                                  newServices[index] = { ...service, port: parseInt(e.target.value) || '' };
                                  setEditTarget(prev => ({ ...prev, services: newServices }));
                                }}
                                className="form-input"
                                style={{ fontSize: '12px', padding: '6px 8px' }}
                                placeholder="Port"
                              />
                            </div>

                            {/* Credential Type */}
                            <div style={{ display: 'flex', flexDirection: 'column', gap: '2px' }}>
                              <label style={{ fontSize: '11px', color: 'var(--neutral-600)', fontWeight: '500', margin: 0 }}>Credential Type</label>
                              <select
                                value={service.credential_type || ''}
                                onChange={(e) => {
                                  const newServices = [...editTarget.services];
                                  newServices[index] = { ...service, credential_type: e.target.value };
                                  setEditTarget(prev => ({ ...prev, services: newServices }));
                                }}
                                className="form-select"
                                style={{ fontSize: '12px', padding: '6px 8px' }}
                              >
                                <option value="">No Credentials</option>
                                {metadata?.credential_types?.map(credType => (
                                  <option key={credType.value} value={credType.value}>
                                    {credType.label}
                                  </option>
                                )) || [
                                  <option key="username_password" value="username_password">Username/Password</option>,
                                  <option key="ssh_key" value="ssh_key">SSH Key</option>,
                                  <option key="api_key" value="api_key">API Key</option>,
                                  <option key="bearer_token" value="bearer_token">Bearer Token</option>
                                ]}
                              </select>
                            </div>

                            {/* Credential Input Fields */}
                            {service.credential_type && (
                              <div style={{ 
                                gridColumn: '1 / -1',
                                marginTop: '12px',
                                padding: '12px',
                                backgroundColor: 'var(--neutral-25)',
                                borderRadius: '4px',
                                border: '1px solid var(--neutral-200)'
                              }}>
                                {service.credential_type === 'username_password' && (
                                  <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr 1fr', gap: '12px' }}>
                                    <div style={{ display: 'flex', flexDirection: 'column', gap: '2px' }}>
                                      <label style={{ fontSize: '11px', color: 'var(--neutral-600)', fontWeight: '500', margin: 0 }}>Username</label>
                                      <input
                                        type="text"
                                        value={service.username || ''}
                                        onChange={(e) => {
                                          const newServices = [...editTarget.services];
                                          newServices[index] = { ...service, username: e.target.value };
                                          setEditTarget(prev => ({ ...prev, services: newServices }));
                                        }}
                                        className="form-input"
                                        style={{ fontSize: '12px', padding: '6px 8px' }}
                                        placeholder="Enter username"
                                      />
                                    </div>
                                    <div style={{ display: 'flex', flexDirection: 'column', gap: '2px' }}>
                                      <label style={{ fontSize: '11px', color: 'var(--neutral-600)', fontWeight: '500', margin: 0 }}>Password</label>
                                      <input
                                        type="password"
                                        value={service.password || ''}
                                        onChange={(e) => {
                                          const newServices = [...editTarget.services];
                                          newServices[index] = { ...service, password: e.target.value };
                                          setEditTarget(prev => ({ ...prev, services: newServices }));
                                        }}
                                        className="form-input"
                                        style={{ fontSize: '12px', padding: '6px 8px' }}
                                        placeholder="Enter password"
                                      />
                                    </div>
                                    <div style={{ display: 'flex', flexDirection: 'column', gap: '2px' }}>
                                      <label style={{ fontSize: '11px', color: 'var(--neutral-600)', fontWeight: '500', margin: 0 }}>Domain (Optional)</label>
                                      <input
                                        type="text"
                                        value={service.domain || ''}
                                        onChange={(e) => {
                                          const newServices = [...editTarget.services];
                                          newServices[index] = { ...service, domain: e.target.value };
                                          setEditTarget(prev => ({ ...prev, services: newServices }));
                                        }}
                                        className="form-input"
                                        style={{ fontSize: '12px', padding: '6px 8px' }}
                                        placeholder="Domain name"
                                      />
                                    </div>
                                  </div>
                                )}

                                {service.credential_type === 'ssh_key' && (
                                  <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '12px' }}>
                                    <div style={{ display: 'flex', flexDirection: 'column', gap: '2px' }}>
                                      <label style={{ fontSize: '11px', color: 'var(--neutral-600)', fontWeight: '500', margin: 0 }}>Username</label>
                                      <input
                                        type="text"
                                        value={service.username || ''}
                                        onChange={(e) => {
                                          const newServices = [...editTarget.services];
                                          newServices[index] = { ...service, username: e.target.value };
                                          setEditTarget(prev => ({ ...prev, services: newServices }));
                                        }}
                                        className="form-input"
                                        style={{ fontSize: '12px', padding: '6px 8px' }}
                                        placeholder="Enter username"
                                      />
                                    </div>
                                    <div style={{ display: 'flex', flexDirection: 'column', gap: '2px' }}>
                                      <label style={{ fontSize: '11px', color: 'var(--neutral-600)', fontWeight: '500', margin: 0 }}>Passphrase (Optional)</label>
                                      <input
                                        type="password"
                                        value={service.passphrase || ''}
                                        onChange={(e) => {
                                          const newServices = [...editTarget.services];
                                          newServices[index] = { ...service, passphrase: e.target.value };
                                          setEditTarget(prev => ({ ...prev, services: newServices }));
                                        }}
                                        className="form-input"
                                        style={{ fontSize: '12px', padding: '6px 8px' }}
                                        placeholder="Key passphrase"
                                      />
                                    </div>
                                    <div style={{ gridColumn: '1 / -1', display: 'flex', flexDirection: 'column', gap: '2px' }}>
                                      <label style={{ fontSize: '11px', color: 'var(--neutral-600)', fontWeight: '500', margin: 0 }}>Private Key</label>
                                      <textarea
                                        value={service.private_key || ''}
                                        onChange={(e) => {
                                          const newServices = [...editTarget.services];
                                          newServices[index] = { ...service, private_key: e.target.value };
                                          setEditTarget(prev => ({ ...prev, services: newServices }));
                                        }}
                                        className="form-input"
                                        style={{ fontSize: '12px', padding: '6px 8px', minHeight: '80px', fontFamily: 'monospace' }}
                                        placeholder="-----BEGIN PRIVATE KEY-----&#10;...&#10;-----END PRIVATE KEY-----"
                                      />
                                    </div>
                                  </div>
                                )}

                                {service.credential_type === 'api_key' && (
                                  <div style={{ display: 'flex', flexDirection: 'column', gap: '2px' }}>
                                    <label style={{ fontSize: '11px', color: 'var(--neutral-600)', fontWeight: '500', margin: 0 }}>API Key</label>
                                    <input
                                      type="password"
                                      value={service.api_key || ''}
                                      onChange={(e) => {
                                        const newServices = [...editTarget.services];
                                        newServices[index] = { ...service, api_key: e.target.value };
                                        setEditTarget(prev => ({ ...prev, services: newServices }));
                                      }}
                                      className="form-input"
                                      style={{ fontSize: '12px', padding: '6px 8px' }}
                                      placeholder="Enter API key"
                                    />
                                  </div>
                                )}

                                {service.credential_type === 'bearer_token' && (
                                  <div style={{ display: 'flex', flexDirection: 'column', gap: '2px' }}>
                                    <label style={{ fontSize: '11px', color: 'var(--neutral-600)', fontWeight: '500', margin: 0 }}>Bearer Token</label>
                                    <input
                                      type="password"
                                      value={service.bearer_token || ''}
                                      onChange={(e) => {
                                        const newServices = [...editTarget.services];
                                        newServices[index] = { ...service, bearer_token: e.target.value };
                                        setEditTarget(prev => ({ ...prev, services: newServices }));
                                      }}
                                      className="form-input"
                                      style={{ fontSize: '12px', padding: '6px 8px' }}
                                      placeholder="Enter bearer token"
                                    />
                                  </div>
                                )}
                              </div>
                            )}

                            {/* Test Connection Button */}
                            <div style={{ paddingTop: '14px' }}>
                              <button 
                                className="btn-icon btn-ghost"
                                title="Test Connection"
                                type="button"
                              >
                                <MonitorCheck size={14} />
                              </button>
                            </div>

                            {/* Remove Button */}
                            <div style={{ paddingTop: '14px' }}>
                              <button 
                                onClick={() => {
                                  const newServices = editTarget.services.filter((_, i) => i !== index);
                                  setEditTarget(prev => ({ ...prev, services: newServices }));
                                }}
                                className="btn-icon btn-ghost"
                                title="Remove Service"
                                type="button"
                              >
                                <Trash2 size={14} />
                              </button>
                            </div>
                          </div>
                        ))}
                      </div>
                    )}
                  </div>
                </div>
              </div>
            </>
          ) : selectedTarget ? (
            <>
              <div className="section-header" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <span>Target Details: {selectedTarget.name}</span>
                <div style={{ display: 'flex', gap: '8px' }}>
                  <button 
                    onClick={() => handleEdit(selectedTarget)}
                    className="btn-icon btn-secondary"
                    title="Edit Target"
                  >
                    <Edit3 size={16} />
                  </button>
                  <button 
                    onClick={() => handleDelete(selectedTarget.id)}
                    className="btn-icon btn-danger"
                    title="Delete Target"
                  >
                    <Trash2 size={16} />
                  </button>
                </div>
              </div>
              <div className="compact-content">
                <div className="target-details">
                  <style>{`
                    .subtle-input {
                      width: 100%;
                      padding: 8px 12px;
                      border: 1px solid var(--neutral-200);
                      background: white;
                      border-radius: 4px;
                      font-size: 13px;
                      color: var(--neutral-900);
                    }
                    .subtle-input:focus {
                      outline: none;
                    }
                    .subtle-input::placeholder {
                      color: var(--neutral-400);
                    }
                    .subtle-select {
                      width: 100%;
                      padding: 8px 12px;
                      border: 1px solid var(--neutral-200);
                      background: white;
                      border-radius: 4px;
                      font-size: 13px;
                      color: var(--neutral-900);
                      cursor: pointer;
                    }
                    .subtle-select:focus {
                      outline: none;
                    }
                    .target-form-grid {
                      display: grid;
                      grid-template-columns: 2fr 1fr 1fr;
                      gap: 20px;
                      margin-bottom: 20px;
                    }
                    .form-field {
                      display: flex;
                      flex-direction: column;
                      gap: 2px;
                    }
                    .form-label {
                      font-size: 12px;
                      font-weight: 600;
                      color: var(--neutral-700);
                    }
                    .form-label.required::after {
                      content: ' *';
                      color: var(--primary-red);
                    }
                    .char-counter {
                      font-size: 11px;
                      color: var(--neutral-500);
                      text-align: right;
                      margin-top: 2px;
                    }
                    .readonly-input {
                      background: var(--neutral-50) !important;
                      color: var(--neutral-600) !important;
                      cursor: not-allowed;
                    }
                  `}</style>
                  <div className="target-form-grid">
                    {/* Column 1 - Primary Field */}
                    <div>
                      <div className="form-field">
                        <label className="form-label required">IP Address / FQDN</label>
                        <input
                          type="text"
                          value={selectedTarget.ip_address || ''}
                          className="subtle-input readonly-input"
                          readOnly
                        />
                      </div>

                      <div className="form-field">
                        <label className="form-label">Tags</label>
                        <input
                          type="text"
                          value={selectedTarget.tags?.join(', ') || ''}
                          className="subtle-input readonly-input"
                          readOnly
                        />
                      </div>
                    </div>

                    {/* Column 2 */}
                    <div>
                      <div className="form-field">
                        <label className="form-label">Operating System</label>
                        <select 
                          value={selectedTarget.os_type || ''} 
                          className="subtle-select readonly-input"
                          disabled
                        >
                          <option value="">Select OS</option>
                          <option value="windows">Windows</option>
                          <option value="linux">Linux</option>
                          <option value="macos">macOS</option>
                        </select>
                      </div>
                    </div>

                    {/* Column 3 */}
                    <div>
                      <div className="form-field">
                        <label className="form-label">Description</label>
                        <input
                          type="text"
                          value={selectedTarget.description || ''}
                          className="subtle-input readonly-input"
                          readOnly
                        />
                      </div>
                    </div>
                  </div>

                  {/* Services Section */}
                  <div style={{ marginTop: '20px' }}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '8px' }}>
                      <label className="form-label" style={{ margin: 0 }}>Services & Communication Types</label>
                      <span style={{ 
                        fontSize: '12px', 
                        color: 'var(--neutral-500)',
                        fontWeight: 'normal'
                      }}>
                        ({selectedTarget.services?.length || 0} configured)
                      </span>
                    </div>

                    {!selectedTarget.services || selectedTarget.services.length === 0 ? (
                      <div style={{ 
                        padding: '12px 0', 
                        color: 'var(--neutral-500)',
                        fontSize: '13px',
                        textAlign: 'center',
                        fontStyle: 'italic'
                      }}>
                        No services configured for this target.
                      </div>
                    ) : (
                      <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
                        {selectedTarget.services.map((service, index) => (
                          <div key={service.id || index} style={{ 
                            display: 'grid', 
                            gridTemplateColumns: '2fr 1fr 2fr auto auto', 
                            gap: '12px', 
                            alignItems: 'center',
                            padding: '8px',
                            backgroundColor: service.is_default ? 'var(--primary-50)' : 'var(--neutral-50)',
                            borderRadius: '4px',
                            border: service.is_default ? '2px solid var(--primary-200)' : '1px solid var(--neutral-200)'
                          }}>
                            {/* Service Type */}
                            <div style={{ display: 'flex', flexDirection: 'column', gap: '2px' }}>
                              <label style={{ fontSize: '11px', color: 'var(--neutral-600)', fontWeight: '500', margin: 0 }}>
                                Service Type {service.is_default && <span style={{ color: 'var(--primary-600)', fontWeight: '600' }}>(Default)</span>}
                              </label>
                              <div style={{ fontSize: '13px', fontWeight: '500', color: 'var(--neutral-900)' }}>
                                {SERVICE_DISPLAY_NAMES[service.service_type] || service.service_type || 'Unknown'}
                              </div>
                            </div>

                            {/* Port */}
                            <div style={{ display: 'flex', flexDirection: 'column', gap: '2px' }}>
                              <label style={{ fontSize: '11px', color: 'var(--neutral-600)', fontWeight: '500', margin: 0 }}>Port</label>
                              <div style={{ fontSize: '13px', color: 'var(--neutral-900)' }}>
                                {service.port || 'N/A'}
                              </div>
                            </div>

                            {/* Credential */}
                            <div style={{ display: 'flex', flexDirection: 'column', gap: '2px' }}>
                              <label style={{ fontSize: '11px', color: 'var(--neutral-600)', fontWeight: '500', margin: 0 }}>Credential Type</label>
                              <div style={{ fontSize: '13px', color: 'var(--neutral-900)' }}>
                                {service.credential_type ? (
                                  <div style={{ display: 'flex', flexDirection: 'column', gap: '1px' }}>
                                    <div style={{ fontWeight: '500', color: 'var(--primary-700)' }}>
                                      {formatCredentialType(service.credential_type)}
                                    </div>
                                    {service.notes && (
                                      <div style={{ fontSize: '10px', color: 'var(--neutral-500)', fontStyle: 'italic' }}>
                                        {service.notes}
                                      </div>
                                    )}
                                  </div>
                                ) : (
                                  <span style={{ color: 'var(--neutral-500)', fontStyle: 'italic' }}>No Credential</span>
                                )}
                              </div>
                            </div>

                            {/* Status */}
                            <div style={{ display: 'flex', flexDirection: 'column', gap: '2px', alignItems: 'center' }}>
                              <label style={{ fontSize: '11px', color: 'var(--neutral-600)', fontWeight: '500', margin: 0 }}>Status</label>
                              <span className={`status-badge ${
                                service.connection_status === 'connected' ? 'status-badge-success' : 
                                service.connection_status === 'failed' ? 'status-badge-danger' : 
                                'status-badge-neutral'
                              }`}>
                                {service.connection_status || 'Unknown'}
                              </span>
                            </div>

                            {/* Test Connection */}
                            <div style={{ display: 'flex', flexDirection: 'column', gap: '2px', alignItems: 'center' }}>
                              <label style={{ fontSize: '11px', color: 'var(--neutral-600)', fontWeight: '500', margin: 0 }}>Test</label>
                              <button
                                onClick={() => testServiceConnection(service.id)}
                                disabled={testingConnections.has(service.id)}
                                className="btn-icon btn-primary"
                                title="Test Connection"
                                style={{ 
                                  fontSize: '12px',
                                  padding: '4px',
                                  minWidth: '28px',
                                  height: '28px'
                                }}
                              >
                                {testingConnections.has(service.id) ? (
                                  <div style={{ 
                                    width: '12px', 
                                    height: '12px', 
                                    border: '2px solid transparent',
                                    borderTop: '2px solid currentColor',
                                    borderRadius: '50%',
                                    animation: 'spin 1s linear infinite'
                                  }} />
                                ) : (
                                  <Zap size={12} />
                                )}
                              </button>
                            </div>
                          </div>
                        ))}
                      </div>
                    )}
                  </div>
                </div>
              </div>
            </>
          ) : (
            <>
              <div className="section-header">
                Select Target
              </div>
              <div className="compact-content">
                <div className="empty-state">
                  <p>Select a target from the table to view details and manage services</p>
                </div>
              </div>
            </>
          )}
        </div>
      </div>
    </div>
  );
};

export default Targets;