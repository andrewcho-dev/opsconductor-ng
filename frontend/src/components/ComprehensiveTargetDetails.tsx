import React, { useState, useEffect } from 'react';
import { ChevronDown, ChevronRight, Server, Network, Shield, Settings, Info, Monitor, Cloud, Database, Zap, Edit3, TestTube } from 'lucide-react';

interface ComprehensiveTarget {
  id: number;
  name: string;
  display_name?: string;
  hostname: string;
  fqdn?: string;
  ip_address?: string;
  secondary_ip_addresses?: string[];
  mac_addresses?: string[];
  description?: string;
  notes?: string;
  
  // Location & Organization
  location?: string;
  datacenter?: string;
  business_unit?: string;
  owner_email?: string;
  technical_contact?: string;
  
  // Device Information
  device_type?: string;
  os_type?: string;
  os_family?: string;
  os_version?: string;
  os_build?: string;
  os_edition?: string;
  architecture?: string;
  kernel_version?: string;
  
  // Hardware Information
  manufacturer?: string;
  model?: string;
  serial_number?: string;
  asset_tag?: string;
  cpu_count?: number;
  cpu_cores?: number;
  cpu_model?: string;
  memory_gb?: number;
  storage_gb?: number;
  
  // Virtualization
  is_virtual: boolean;
  hypervisor?: string;
  vm_id?: string;
  cluster_name?: string;
  
  // Network Configuration
  domain?: string;
  workgroup?: string;
  dns_servers?: string[];
  default_gateway?: string;
  subnet_mask?: string;
  vlan_id?: number;
  
  // Connection Management
  primary_connection?: string;
  fallback_connections?: string[];
  connection_status?: string;
  last_seen?: string;
  last_connection_test?: string;
  connection_error?: string;
  
  // SSH Configuration
  ssh_enabled: boolean;
  ssh_port?: number;
  ssh_username?: string;
  ssh_has_password: boolean;
  ssh_has_private_key: boolean;
  
  // WinRM Configuration
  winrm_enabled: boolean;
  winrm_port?: number;
  winrm_use_ssl: boolean;
  winrm_username?: string;
  winrm_has_password: boolean;
  winrm_domain?: string;
  
  // SNMP Configuration
  snmp_enabled: boolean;
  snmp_port?: number;
  snmp_version?: string;
  snmp_has_community: boolean;
  snmp_v3_username?: string;
  
  // HTTP Configuration
  http_enabled: boolean;
  http_port?: number;
  http_use_ssl: boolean;
  http_base_url?: string;
  http_auth_type?: string;
  http_username?: string;
  http_has_credentials: boolean;
  
  // System Fields
  is_active: boolean;
  version?: number;
  change_reason?: string;
  tags?: Array<{id: number, name: string, color: string, category: string}>;
  metadata?: Record<string, any>;
  custom_fields?: Record<string, any>;
  created_by?: number;
  updated_by?: number;
  created_at: string;
  updated_at?: string;
}

interface CollapsibleSectionProps {
  title: string;
  icon: React.ReactNode;
  isExpanded: boolean;
  onToggle: () => void;
  children: React.ReactNode;
  badge?: string | number;
}

const CollapsibleSection: React.FC<CollapsibleSectionProps> = ({
  title,
  icon,
  isExpanded,
  onToggle,
  children,
  badge
}) => (
  <div className="collapsible-section">
    <div 
      className="section-header-collapsible" 
      onClick={onToggle}
      style={{
        display: 'flex',
        alignItems: 'center',
        gap: '8px',
        padding: '12px 16px',
        backgroundColor: 'var(--neutral-50)',
        border: '1px solid var(--neutral-200)',
        borderRadius: '6px',
        cursor: 'pointer',
        marginBottom: isExpanded ? '0' : '8px',
        transition: 'all 0.2s ease'
      }}
    >
      {isExpanded ? <ChevronDown size={16} /> : <ChevronRight size={16} />}
      {icon}
      <span style={{ fontWeight: '600', fontSize: '14px', color: 'var(--neutral-800)' }}>
        {title}
      </span>
      {badge && (
        <span style={{
          backgroundColor: 'var(--primary-100)',
          color: 'var(--primary-700)',
          fontSize: '11px',
          fontWeight: '600',
          padding: '2px 6px',
          borderRadius: '10px',
          marginLeft: 'auto'
        }}>
          {badge}
        </span>
      )}
    </div>
    
    {isExpanded && (
      <div style={{
        border: '1px solid var(--neutral-200)',
        borderTop: 'none',
        borderRadius: '0 0 6px 6px',
        padding: '16px',
        backgroundColor: 'white',
        marginBottom: '8px'
      }}>
        {children}
      </div>
    )}
  </div>
);

interface FieldRowProps {
  label: string;
  value: any;
  type?: 'text' | 'boolean' | 'array' | 'date' | 'number';
  isEditing?: boolean;
  onChange?: (value: any) => void;
  field?: string;
}

const FieldRow: React.FC<FieldRowProps> = ({ label, value, type = 'text', isEditing = false, onChange, field }) => {
  const renderValue = () => {
    if (isEditing && onChange) {
      switch (type) {
        case 'boolean':
          return (
            <select
              value={value ? 'true' : 'false'}
              onChange={(e) => onChange(e.target.value === 'true')}
              style={{
                fontSize: '13px',
                padding: '4px 8px',
                border: '1px solid var(--neutral-300)',
                borderRadius: '4px',
                backgroundColor: 'white'
              }}
            >
              <option value="false">No</option>
              <option value="true">Yes</option>
            </select>
          );
        case 'number':
          return (
            <input
              type="number"
              value={value || ''}
              onChange={(e) => onChange(e.target.value ? parseInt(e.target.value) : null)}
              style={{
                fontSize: '13px',
                padding: '4px 8px',
                border: '1px solid var(--neutral-300)',
                borderRadius: '4px',
                backgroundColor: 'white',
                width: '100%'
              }}
            />
          );
        case 'array':
          return (
            <input
              type="text"
              value={Array.isArray(value) ? value.join(', ') : ''}
              onChange={(e) => onChange(e.target.value.split(',').map(s => s.trim()).filter(Boolean))}
              placeholder="Comma-separated values"
              style={{
                fontSize: '13px',
                padding: '4px 8px',
                border: '1px solid var(--neutral-300)',
                borderRadius: '4px',
                backgroundColor: 'white',
                width: '100%'
              }}
            />
          );
        default:
          return (
            <input
              type="text"
              value={value || ''}
              onChange={(e) => onChange(e.target.value)}
              style={{
                fontSize: '13px',
                padding: '4px 8px',
                border: '1px solid var(--neutral-300)',
                borderRadius: '4px',
                backgroundColor: 'white',
                width: '100%'
              }}
            />
          );
      }
    }

    // Read-only mode
    if (value === null || value === undefined || value === '') {
      return <span style={{ color: 'var(--neutral-400)', fontStyle: 'italic' }}>Not set</span>;
    }
    
    switch (type) {
      case 'boolean':
        return (
          <span style={{ 
            color: value ? 'var(--success-600)' : 'var(--neutral-500)',
            fontWeight: '500'
          }}>
            {value ? 'Yes' : 'No'}
          </span>
        );
      case 'array':
        return Array.isArray(value) && value.length > 0 
          ? value.join(', ') 
          : <span style={{ color: 'var(--neutral-400)', fontStyle: 'italic' }}>None</span>;
      case 'date':
        return value ? new Date(value).toLocaleString() : 
          <span style={{ color: 'var(--neutral-400)', fontStyle: 'italic' }}>Never</span>;
      case 'number':
        return value?.toLocaleString() || <span style={{ color: 'var(--neutral-400)', fontStyle: 'italic' }}>Not set</span>;
      default:
        return value;
    }
  };

  return (
    <div style={{
      display: 'grid',
      gridTemplateColumns: '1fr 2fr',
      gap: '12px',
      padding: '8px 0',
      borderBottom: '1px solid var(--neutral-100)'
    }}>
      <label style={{
        fontSize: '13px',
        fontWeight: '500',
        color: 'var(--neutral-700)'
      }}>
        {label}
      </label>
      <div style={{
        fontSize: '13px',
        color: 'var(--neutral-900)'
      }}>
        {renderValue()}
      </div>
    </div>
  );
};

interface ComprehensiveTargetDetailsProps {
  target: ComprehensiveTarget;
  onTestConnection?: (connectionType: string, config: any) => Promise<void>;
  testingConnections?: Set<string | number>;
  onEdit?: (target: ComprehensiveTarget) => void;
  isEditing?: boolean;
  onSave?: (updatedTarget: ComprehensiveTarget) => Promise<void>;
  onCancelEdit?: () => void;
}

const ComprehensiveTargetDetails: React.FC<ComprehensiveTargetDetailsProps> = ({ 
  target, 
  onTestConnection, 
  testingConnections = new Set(), 
  onEdit,
  isEditing = false,
  onSave,
  onCancelEdit
}) => {
  const [editedTarget, setEditedTarget] = useState<ComprehensiveTarget>(target);

  // Update editedTarget when target changes
  useEffect(() => {
    setEditedTarget(target);
  }, [target]);

  const handleFieldChange = (field: keyof ComprehensiveTarget, value: any) => {
    setEditedTarget(prev => ({ ...prev, [field]: value }));
  };

  const handleSave = async () => {
    if (onSave) {
      await onSave(editedTarget);
    }
  };

  // Helper function to create editable field rows
  const EditableFieldRow: React.FC<{
    label: string;
    field: keyof ComprehensiveTarget;
    type?: 'text' | 'boolean' | 'array' | 'date' | 'number';
  }> = ({ label, field, type = 'text' }) => (
    <FieldRow 
      label={label}
      value={isEditing ? editedTarget[field] : target[field]}
      type={type}
      isEditing={isEditing}
      onChange={(value) => handleFieldChange(field, value)}
    />
  );
  const [expandedSections, setExpandedSections] = useState<Set<string>>(
    new Set(['basic']) // Basic info expanded by default
  );

  const toggleSection = (sectionId: string) => {
    setExpandedSections(prev => {
      const newSet = new Set(prev);
      if (newSet.has(sectionId)) {
        newSet.delete(sectionId);
      } else {
        newSet.add(sectionId);
      }
      return newSet;
    });
  };

  const getConnectionCount = () => {
    let count = 0;
    if (target.ssh_enabled) count++;
    if (target.winrm_enabled) count++;
    if (target.snmp_enabled) count++;
    if (target.http_enabled) count++;
    return count;
  };

  const hasAnyConnectionMethod = () => {
    return target.ssh_enabled || target.winrm_enabled || target.snmp_enabled || target.http_enabled;
  };

  const getHardwareFieldCount = () => {
    const fields = [
      target.manufacturer, target.model, target.serial_number, target.asset_tag,
      target.cpu_count, target.cpu_cores, target.cpu_model, target.memory_gb, target.storage_gb
    ];
    return fields.filter(field => field !== null && field !== undefined && field !== '').length;
  };

  const getNetworkFieldCount = () => {
    const fields = [
      target.domain, target.workgroup, target.dns_servers?.length,
      target.default_gateway, target.subnet_mask, target.vlan_id
    ];
    return fields.filter(field => field !== null && field !== undefined && field !== '' && field !== 0).length;
  };

  return (
    <div className="comprehensive-target-details">
      {/* Editing Controls */}
      {isEditing && (
        <div style={{
          display: 'flex',
          justifyContent: 'flex-end',
          gap: '8px',
          marginBottom: '16px',
          padding: '12px',
          backgroundColor: 'var(--warning-50)',
          border: '1px solid var(--warning-200)',
          borderRadius: '6px'
        }}>
          <span style={{ 
            fontSize: '13px', 
            color: 'var(--warning-800)', 
            marginRight: 'auto',
            fontWeight: '500'
          }}>
            Editing mode - Make your changes and click Save
          </span>
          <button
            onClick={handleSave}
            className="btn-sm btn-success"
            style={{ fontSize: '12px', padding: '6px 12px' }}
          >
            Save Changes
          </button>
          <button
            onClick={onCancelEdit}
            className="btn-sm btn-ghost"
            style={{ fontSize: '12px', padding: '6px 12px' }}
          >
            Cancel
          </button>
        </div>
      )}
      
      <style>{`
        .collapsible-section:last-child {
          margin-bottom: 0;
        }
        .section-header-collapsible:hover {
          background-color: var(--neutral-100) !important;
        }
        .comprehensive-target-details {
          max-height: calc(100vh - 200px);
          overflow-y: auto;
          padding-right: 8px;
        }
        .comprehensive-target-details::-webkit-scrollbar {
          width: 6px;
        }
        .comprehensive-target-details::-webkit-scrollbar-track {
          background: var(--neutral-100);
          border-radius: 3px;
        }
        .comprehensive-target-details::-webkit-scrollbar-thumb {
          background: var(--neutral-300);
          border-radius: 3px;
        }
        .comprehensive-target-details::-webkit-scrollbar-thumb:hover {
          background: var(--neutral-400);
        }
        @keyframes spin {
          0% { transform: rotate(0deg); }
          100% { transform: rotate(360deg); }
        }
      `}</style>

      {/* Basic Information - Always visible */}
      <CollapsibleSection
        title="Basic Information"
        icon={<Info size={16} />}
        isExpanded={expandedSections.has('basic')}
        onToggle={() => toggleSection('basic')}
      >
        <EditableFieldRow label="Name" field="name" />
        <EditableFieldRow label="Display Name" field="display_name" />
        <EditableFieldRow label="Hostname" field="hostname" />
        <EditableFieldRow label="FQDN" field="fqdn" />
        <EditableFieldRow label="IP Address" field="ip_address" />
        <EditableFieldRow label="Secondary IPs" field="secondary_ip_addresses" type="array" />
        <EditableFieldRow label="MAC Addresses" field="mac_addresses" type="array" />
        <EditableFieldRow label="Description" field="description" />
        <EditableFieldRow label="Notes" field="notes" />
        <EditableFieldRow label="Active" field="is_active" type="boolean" />
      </CollapsibleSection>

      {/* Location & Organization */}
      <CollapsibleSection
        title="Location & Organization"
        icon={<Server size={16} />}
        isExpanded={expandedSections.has('location')}
        onToggle={() => toggleSection('location')}
      >
        <EditableFieldRow label="Location" field="location" />
        <EditableFieldRow label="Datacenter" field="datacenter" />
        <EditableFieldRow label="Business Unit" field="business_unit" />
        <EditableFieldRow label="Owner Email" field="owner_email" />
        <EditableFieldRow label="Technical Contact" field="technical_contact" />
      </CollapsibleSection>

      {/* System Information */}
      <CollapsibleSection
        title="System Information"
        icon={<Monitor size={16} />}
        isExpanded={expandedSections.has('system')}
        onToggle={() => toggleSection('system')}
      >
        <EditableFieldRow label="Device Type" field="device_type" />
        <EditableFieldRow label="OS Type" field="os_type" />
        <EditableFieldRow label="OS Family" field="os_family" />
        <EditableFieldRow label="OS Version" field="os_version" />
        <EditableFieldRow label="OS Build" field="os_build" />
        <EditableFieldRow label="OS Edition" field="os_edition" />
        <EditableFieldRow label="Architecture" field="architecture" />
        <EditableFieldRow label="Kernel Version" field="kernel_version" />
      </CollapsibleSection>

      {/* Hardware Information */}
      <CollapsibleSection
        title="Hardware Information"
        icon={<Settings size={16} />}
        isExpanded={expandedSections.has('hardware')}
        onToggle={() => toggleSection('hardware')}
        badge={getHardwareFieldCount() > 0 ? getHardwareFieldCount() : undefined}
      >
        <EditableFieldRow label="Manufacturer" field="manufacturer" />
        <EditableFieldRow label="Model" field="model" />
        <EditableFieldRow label="Serial Number" field="serial_number" />
        <EditableFieldRow label="Asset Tag" field="asset_tag" />
        <EditableFieldRow label="CPU Count" field="cpu_count" type="number" />
        <EditableFieldRow label="CPU Cores" field="cpu_cores" type="number" />
        <EditableFieldRow label="CPU Model" field="cpu_model" />
        <EditableFieldRow label="Memory (GB)" field="memory_gb" type="number" />
        <EditableFieldRow label="Storage (GB)" field="storage_gb" type="number" />
      </CollapsibleSection>

      {/* Virtualization */}
      <CollapsibleSection
        title="Virtualization"
        icon={<Cloud size={16} />}
        isExpanded={expandedSections.has('virtualization')}
        onToggle={() => toggleSection('virtualization')}
      >
        <EditableFieldRow label="Is Virtual" field="is_virtual" type="boolean" />
        <EditableFieldRow label="Hypervisor" field="hypervisor" />
        <EditableFieldRow label="VM ID" field="vm_id" />
        <EditableFieldRow label="Cluster Name" field="cluster_name" />
      </CollapsibleSection>

      {/* Network Configuration */}
      <CollapsibleSection
        title="Network Configuration"
        icon={<Network size={16} />}
        isExpanded={expandedSections.has('network')}
        onToggle={() => toggleSection('network')}
        badge={getNetworkFieldCount() > 0 ? getNetworkFieldCount() : undefined}
      >
        <EditableFieldRow label="Domain" field="domain" />
        <EditableFieldRow label="Workgroup" field="workgroup" />
        <EditableFieldRow label="DNS Servers" field="dns_servers" type="array" />
        <EditableFieldRow label="Default Gateway" field="default_gateway" />
        <EditableFieldRow label="Subnet Mask" field="subnet_mask" />
        <EditableFieldRow label="VLAN ID" field="vlan_id" type="number" />
      </CollapsibleSection>

      {/* Connection Methods */}
      <CollapsibleSection
        title="Connection Methods"
        icon={<Shield size={16} />}
        isExpanded={expandedSections.has('connections')}
        onToggle={() => toggleSection('connections')}
        badge={getConnectionCount()}
      >
        <div style={{ marginBottom: '16px' }}>
          <EditableFieldRow label="Primary Connection" field="primary_connection" />
          <EditableFieldRow label="Fallback Connections" field="fallback_connections" type="array" />
          <FieldRow label="Connection Status" value={target.connection_status} />
          <FieldRow label="Last Seen" value={target.last_seen} type="date" />
          <FieldRow label="Last Connection Test" value={target.last_connection_test} type="date" />
          <FieldRow label="Connection Error" value={target.connection_error} />
        </div>

        {!hasAnyConnectionMethod() && (
          <div style={{
            padding: '16px',
            backgroundColor: 'var(--warning-50)',
            border: '1px solid var(--warning-200)',
            borderRadius: '6px',
            textAlign: 'center',
            color: 'var(--warning-800)',
            fontSize: '13px',
            fontStyle: 'italic'
          }}>
            No connection methods are currently enabled for this target.
          </div>
        )}

        {/* SSH Configuration */}
        {target.ssh_enabled && (
          <div style={{ 
            backgroundColor: 'var(--success-50)', 
            padding: '12px', 
            borderRadius: '4px', 
            marginBottom: '12px',
            border: '1px solid var(--success-200)'
          }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '8px' }}>
              <h4 style={{ margin: 0, fontSize: '13px', fontWeight: '600', color: 'var(--success-800)' }}>
                SSH Configuration
              </h4>
              {onTestConnection && (
                <button
                  onClick={() => onTestConnection('ssh', {
                    host: target.ip_address || target.hostname,
                    port: target.ssh_port || 22,
                    username: target.ssh_username
                  })}
                  disabled={testingConnections.has('ssh')}
                  className="btn-icon btn-success"
                  title="Test SSH Connection"
                  style={{ fontSize: '11px', padding: '4px 8px', height: '24px' }}
                >
                  {testingConnections.has('ssh') ? (
                    <div style={{ 
                      width: '10px', 
                      height: '10px', 
                      border: '2px solid transparent',
                      borderTop: '2px solid currentColor',
                      borderRadius: '50%',
                      animation: 'spin 1s linear infinite'
                    }} />
                  ) : (
                    <Zap size={10} />
                  )}
                </button>
              )}
            </div>
            <FieldRow label="Port" value={target.ssh_port} type="number" />
            <FieldRow label="Username" value={target.ssh_username} />
            <FieldRow label="Has Password" value={target.ssh_has_password} type="boolean" />
            <FieldRow label="Has Private Key" value={target.ssh_has_private_key} type="boolean" />
          </div>
        )}

        {/* WinRM Configuration */}
        {target.winrm_enabled && (
          <div style={{ 
            backgroundColor: 'var(--info-50)', 
            padding: '12px', 
            borderRadius: '4px', 
            marginBottom: '12px',
            border: '1px solid var(--info-200)'
          }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '8px' }}>
              <h4 style={{ margin: 0, fontSize: '13px', fontWeight: '600', color: 'var(--info-800)' }}>
                WinRM Configuration
              </h4>
              {onTestConnection && (
                <button
                  onClick={() => onTestConnection('winrm', {
                    host: target.ip_address || target.hostname,
                    port: target.winrm_port || (target.winrm_use_ssl ? 5986 : 5985),
                    username: target.winrm_username,
                    use_ssl: target.winrm_use_ssl,
                    domain: target.winrm_domain
                  })}
                  disabled={testingConnections.has('winrm')}
                  className="btn-icon btn-info"
                  title="Test WinRM Connection"
                  style={{ fontSize: '11px', padding: '4px 8px', height: '24px' }}
                >
                  {testingConnections.has('winrm') ? (
                    <div style={{ 
                      width: '10px', 
                      height: '10px', 
                      border: '2px solid transparent',
                      borderTop: '2px solid currentColor',
                      borderRadius: '50%',
                      animation: 'spin 1s linear infinite'
                    }} />
                  ) : (
                    <Zap size={10} />
                  )}
                </button>
              )}
            </div>
            <FieldRow label="Port" value={target.winrm_port} type="number" />
            <FieldRow label="Use SSL" value={target.winrm_use_ssl} type="boolean" />
            <FieldRow label="Username" value={target.winrm_username} />
            <FieldRow label="Has Password" value={target.winrm_has_password} type="boolean" />
            <FieldRow label="Domain" value={target.winrm_domain} />
          </div>
        )}

        {/* SNMP Configuration */}
        {target.snmp_enabled && (
          <div style={{ 
            backgroundColor: 'var(--warning-50)', 
            padding: '12px', 
            borderRadius: '4px', 
            marginBottom: '12px',
            border: '1px solid var(--warning-200)'
          }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '8px' }}>
              <h4 style={{ margin: 0, fontSize: '13px', fontWeight: '600', color: 'var(--warning-800)' }}>
                SNMP Configuration
              </h4>
              {onTestConnection && (
                <button
                  onClick={() => onTestConnection('snmp', {
                    host: target.ip_address || target.hostname,
                    port: target.snmp_port || 161,
                    version: target.snmp_version,
                    username: target.snmp_v3_username
                  })}
                  disabled={testingConnections.has('snmp')}
                  className="btn-icon btn-warning"
                  title="Test SNMP Connection"
                  style={{ fontSize: '11px', padding: '4px 8px', height: '24px' }}
                >
                  {testingConnections.has('snmp') ? (
                    <div style={{ 
                      width: '10px', 
                      height: '10px', 
                      border: '2px solid transparent',
                      borderTop: '2px solid currentColor',
                      borderRadius: '50%',
                      animation: 'spin 1s linear infinite'
                    }} />
                  ) : (
                    <Zap size={10} />
                  )}
                </button>
              )}
            </div>
            <FieldRow label="Port" value={target.snmp_port} type="number" />
            <FieldRow label="Version" value={target.snmp_version} />
            <FieldRow label="Has Community" value={target.snmp_has_community} type="boolean" />
            <FieldRow label="V3 Username" value={target.snmp_v3_username} />
          </div>
        )}

        {/* HTTP Configuration */}
        {target.http_enabled && (
          <div style={{ 
            backgroundColor: 'var(--purple-50)', 
            padding: '12px', 
            borderRadius: '4px', 
            marginBottom: '12px',
            border: '1px solid var(--purple-200)'
          }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '8px' }}>
              <h4 style={{ margin: 0, fontSize: '13px', fontWeight: '600', color: 'var(--purple-800)' }}>
                HTTP Configuration
              </h4>
              {onTestConnection && (
                <button
                  onClick={() => onTestConnection('http', {
                    host: target.ip_address || target.hostname,
                    port: target.http_port || (target.http_use_ssl ? 443 : 80),
                    use_ssl: target.http_use_ssl,
                    base_url: target.http_base_url,
                    auth_type: target.http_auth_type,
                    username: target.http_username
                  })}
                  disabled={testingConnections.has('http')}
                  className="btn-icon btn-secondary"
                  title="Test HTTP Connection"
                  style={{ fontSize: '11px', padding: '4px 8px', height: '24px', backgroundColor: 'var(--purple-600)', color: 'white' }}
                >
                  {testingConnections.has('http') ? (
                    <div style={{ 
                      width: '10px', 
                      height: '10px', 
                      border: '2px solid transparent',
                      borderTop: '2px solid currentColor',
                      borderRadius: '50%',
                      animation: 'spin 1s linear infinite'
                    }} />
                  ) : (
                    <Zap size={10} />
                  )}
                </button>
              )}
            </div>
            <FieldRow label="Port" value={target.http_port} type="number" />
            <FieldRow label="Use SSL" value={target.http_use_ssl} type="boolean" />
            <FieldRow label="Base URL" value={target.http_base_url} />
            <FieldRow label="Auth Type" value={target.http_auth_type} />
            <FieldRow label="Username" value={target.http_username} />
            <FieldRow label="Has Credentials" value={target.http_has_credentials} type="boolean" />
          </div>
        )}
      </CollapsibleSection>

      {/* Tags */}
      {target.tags && target.tags.length > 0 && (
        <CollapsibleSection
          title="Tags"
          icon={<Database size={16} />}
          isExpanded={expandedSections.has('tags')}
          onToggle={() => toggleSection('tags')}
          badge={target.tags.length}
        >
          <div style={{ display: 'flex', flexWrap: 'wrap', gap: '8px' }}>
            {target.tags.map((tag, index) => (
              <span
                key={tag.id || index}
                style={{
                  backgroundColor: tag.color || 'var(--neutral-200)',
                  color: 'white',
                  fontSize: '11px',
                  fontWeight: '600',
                  padding: '4px 8px',
                  borderRadius: '12px',
                  textShadow: '0 1px 2px rgba(0,0,0,0.3)'
                }}
              >
                {tag.name}
              </span>
            ))}
          </div>
        </CollapsibleSection>
      )}

      {/* System Metadata */}
      <CollapsibleSection
        title="System Metadata"
        icon={<Settings size={16} />}
        isExpanded={expandedSections.has('metadata')}
        onToggle={() => toggleSection('metadata')}
      >
        <FieldRow label="Version" value={target.version} type="number" />
        <FieldRow label="Change Reason" value={target.change_reason} />
        <FieldRow label="Created By" value={target.created_by} type="number" />
        <FieldRow label="Updated By" value={target.updated_by} type="number" />
        <FieldRow label="Created At" value={target.created_at} type="date" />
        <FieldRow label="Updated At" value={target.updated_at} type="date" />
      </CollapsibleSection>
    </div>
  );
};

export default ComprehensiveTargetDetails;