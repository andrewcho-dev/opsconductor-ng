// Example React Component for Collapsible Target Form
import React, { useState } from 'react';
import { ChevronDownIcon, ChevronRightIcon } from '@heroicons/react/24/outline';

interface CollapsibleSectionProps {
  title: string;
  icon: string;
  isExpanded: boolean;
  onToggle: () => void;
  badge?: 'valid' | 'partial' | 'error' | 'empty';
  children: React.ReactNode;
}

const CollapsibleSection: React.FC<CollapsibleSectionProps> = ({
  title,
  icon,
  isExpanded,
  onToggle,
  badge,
  children
}) => {
  const getBadgeColor = () => {
    switch (badge) {
      case 'valid': return 'bg-green-100 text-green-800';
      case 'partial': return 'bg-yellow-100 text-yellow-800';
      case 'error': return 'bg-red-100 text-red-800';
      case 'empty': return 'bg-gray-100 text-gray-500';
      default: return 'bg-gray-100 text-gray-500';
    }
  };

  const getBadgeSymbol = () => {
    switch (badge) {
      case 'valid': return '✓';
      case 'partial': return '⚠';
      case 'error': return '✗';
      case 'empty': return '○';
      default: return '○';
    }
  };

  return (
    <div className="border border-gray-200 rounded-lg mb-4">
      <button
        type="button"
        onClick={onToggle}
        className="w-full px-4 py-3 flex items-center justify-between bg-gray-50 hover:bg-gray-100 rounded-t-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
      >
        <div className="flex items-center space-x-3">
          <span className="text-lg">{icon}</span>
          <span className="font-medium text-gray-900">{title}</span>
          {badge && (
            <span className={`px-2 py-1 text-xs font-medium rounded-full ${getBadgeColor()}`}>
              {getBadgeSymbol()}
            </span>
          )}
        </div>
        {isExpanded ? (
          <ChevronDownIcon className="h-5 w-5 text-gray-500" />
        ) : (
          <ChevronRightIcon className="h-5 w-5 text-gray-500" />
        )}
      </button>
      
      {isExpanded && (
        <div className="p-4 border-t border-gray-200">
          {children}
        </div>
      )}
    </div>
  );
};

const TargetForm: React.FC = () => {
  // State for managing which sections are expanded
  const [expandedSections, setExpandedSections] = useState<Set<string>>(
    new Set(['basic']) // Only basic info expanded by default
  );

  const toggleSection = (sectionId: string) => {
    const newExpanded = new Set(expandedSections);
    if (newExpanded.has(sectionId)) {
      newExpanded.delete(sectionId);
    } else {
      newExpanded.add(sectionId);
    }
    setExpandedSections(newExpanded);
  };

  // Form state (simplified example)
  const [formData, setFormData] = useState({
    name: '',
    hostname: '',
    ip_address: '',
    primary_connection: 'ssh',
    ssh_enabled: false,
    ssh_port: 22,
    ssh_username: '',
    winrm_enabled: false,
    winrm_port: 5985,
    // ... other fields
  });

  // Auto-expand primary connection section when selected
  const handlePrimaryConnectionChange = (value: string) => {
    setFormData({ ...formData, primary_connection: value });
    
    // Auto-expand the selected connection section
    const newExpanded = new Set(expandedSections);
    newExpanded.add(value);
    setExpandedSections(newExpanded);
  };

  return (
    <div className="max-w-4xl mx-auto p-6">
      <h1 className="text-2xl font-bold text-gray-900 mb-6">Target Configuration</h1>
      
      <form className="space-y-4">
        {/* BASIC INFORMATION - Always visible */}
        <div className="bg-white border border-gray-200 rounded-lg p-4">
          <h2 className="text-lg font-medium text-gray-900 mb-4 flex items-center">
            <span className="mr-2">📋</span>
            Basic Information
          </h2>
          
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Name *
              </label>
              <input
                type="text"
                value={formData.name}
                onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                placeholder="web-server-01"
              />
            </div>
            
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Hostname *
              </label>
              <input
                type="text"
                value={formData.hostname}
                onChange={(e) => setFormData({ ...formData, hostname: e.target.value })}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                placeholder="web01.company.com"
              />
            </div>
            
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                IP Address *
              </label>
              <input
                type="text"
                value={formData.ip_address}
                onChange={(e) => setFormData({ ...formData, ip_address: e.target.value })}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                placeholder="192.168.1.100"
              />
            </div>
            
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Primary Connection *
              </label>
              <select
                value={formData.primary_connection}
                onChange={(e) => handlePrimaryConnectionChange(e.target.value)}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
              >
                <option value="ssh">SSH</option>
                <option value="winrm">WinRM</option>
                <option value="snmp">SNMP</option>
                <option value="http">HTTP/HTTPS</option>
                <option value="rdp">RDP</option>
              </select>
            </div>
          </div>
        </div>

        {/* SYSTEM INFORMATION - Collapsible */}
        <CollapsibleSection
          title="System Information"
          icon="🖥️"
          isExpanded={expandedSections.has('system')}
          onToggle={() => toggleSection('system')}
          badge="empty"
        >
          <div className="space-y-4">
            <h3 className="font-medium text-gray-900">OS & Platform</h3>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">OS Type</label>
                <select className="w-full px-3 py-2 border border-gray-300 rounded-md">
                  <option value="">Select OS</option>
                  <option value="linux">Linux</option>
                  <option value="windows">Windows</option>
                  <option value="unix">Unix</option>
                  <option value="macos">macOS</option>
                </select>
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">OS Family</label>
                <input type="text" className="w-full px-3 py-2 border border-gray-300 rounded-md" placeholder="debian, rhel, etc." />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Architecture</label>
                <select className="w-full px-3 py-2 border border-gray-300 rounded-md">
                  <option value="x86_64">x86_64</option>
                  <option value="arm64">ARM64</option>
                  <option value="i386">i386</option>
                </select>
              </div>
            </div>
            
            <h3 className="font-medium text-gray-900 mt-6">Hardware Details</h3>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Manufacturer</label>
                <input type="text" className="w-full px-3 py-2 border border-gray-300 rounded-md" placeholder="Dell, HP, etc." />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Model</label>
                <input type="text" className="w-full px-3 py-2 border border-gray-300 rounded-md" placeholder="PowerEdge R740" />
              </div>
            </div>
          </div>
        </CollapsibleSection>

        {/* SSH CONNECTION - Collapsible */}
        <CollapsibleSection
          title="SSH Connection"
          icon="🔐"
          isExpanded={expandedSections.has('ssh')}
          onToggle={() => toggleSection('ssh')}
          badge={formData.ssh_enabled ? 'valid' : 'empty'}
        >
          <div className="space-y-4">
            <div className="flex items-center">
              <input
                type="checkbox"
                id="ssh_enabled"
                checked={formData.ssh_enabled}
                onChange={(e) => setFormData({ ...formData, ssh_enabled: e.target.checked })}
                className="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded"
              />
              <label htmlFor="ssh_enabled" className="ml-2 block text-sm font-medium text-gray-900">
                Enable SSH Connection
              </label>
            </div>
            
            {formData.ssh_enabled && (
              <>
                <h3 className="font-medium text-gray-900">Basic Settings</h3>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">Port</label>
                    <input
                      type="number"
                      value={formData.ssh_port}
                      onChange={(e) => setFormData({ ...formData, ssh_port: parseInt(e.target.value) })}
                      className="w-full px-3 py-2 border border-gray-300 rounded-md"
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">Username</label>
                    <input
                      type="text"
                      value={formData.ssh_username}
                      onChange={(e) => setFormData({ ...formData, ssh_username: e.target.value })}
                      className="w-full px-3 py-2 border border-gray-300 rounded-md"
                      placeholder="admin"
                    />
                  </div>
                </div>
                
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Password</label>
                  <input
                    type="password"
                    className="w-full px-3 py-2 border border-gray-300 rounded-md"
                    placeholder="Enter password"
                  />
                </div>
                
                {/* Advanced SSH options would be in another collapsible subsection */}
                <CollapsibleSection
                  title="Advanced SSH Options"
                  icon="⚙️"
                  isExpanded={expandedSections.has('ssh-advanced')}
                  onToggle={() => toggleSection('ssh-advanced')}
                  badge="empty"
                >
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-1">SSH Version</label>
                      <select className="w-full px-3 py-2 border border-gray-300 rounded-md">
                        <option value="2">SSH v2</option>
                        <option value="1">SSH v1</option>
                        <option value="auto">Auto</option>
                      </select>
                    </div>
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-1">Timeout (seconds)</label>
                      <input type="number" defaultValue="30" className="w-full px-3 py-2 border border-gray-300 rounded-md" />
                    </div>
                  </div>
                </CollapsibleSection>
              </>
            )}
          </div>
        </CollapsibleSection>

        {/* WINRM CONNECTION - Collapsible */}
        <CollapsibleSection
          title="WinRM Connection"
          icon="🪟"
          isExpanded={expandedSections.has('winrm')}
          onToggle={() => toggleSection('winrm')}
          badge={formData.winrm_enabled ? 'valid' : 'empty'}
        >
          <div className="space-y-4">
            <div className="flex items-center">
              <input
                type="checkbox"
                id="winrm_enabled"
                checked={formData.winrm_enabled}
                onChange={(e) => setFormData({ ...formData, winrm_enabled: e.target.checked })}
                className="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded"
              />
              <label htmlFor="winrm_enabled" className="ml-2 block text-sm font-medium text-gray-900">
                Enable WinRM Connection
              </label>
            </div>
            
            {formData.winrm_enabled && (
              <>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">Port</label>
                    <input
                      type="number"
                      value={formData.winrm_port}
                      onChange={(e) => setFormData({ ...formData, winrm_port: parseInt(e.target.value) })}
                      className="w-full px-3 py-2 border border-gray-300 rounded-md"
                    />
                  </div>
                  <div className="flex items-center">
                    <input type="checkbox" id="winrm_ssl" className="h-4 w-4 text-blue-600" />
                    <label htmlFor="winrm_ssl" className="ml-2 text-sm text-gray-700">Use SSL</label>
                  </div>
                </div>
                
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">Username</label>
                    <input type="text" className="w-full px-3 py-2 border border-gray-300 rounded-md" placeholder="administrator" />
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">Domain</label>
                    <input type="text" className="w-full px-3 py-2 border border-gray-300 rounded-md" placeholder="COMPANY" />
                  </div>
                </div>
              </>
            )}
          </div>
        </CollapsibleSection>

        {/* More sections would follow the same pattern... */}
        
        {/* SAVE BUTTONS */}
        <div className="flex justify-end space-x-3 pt-6 border-t border-gray-200">
          <button
            type="button"
            className="px-4 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-md hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-blue-500"
          >
            Cancel
          </button>
          <button
            type="submit"
            className="px-4 py-2 text-sm font-medium text-white bg-blue-600 border border-transparent rounded-md hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500"
          >
            Save Target
          </button>
        </div>
      </form>
    </div>
  );
};

export default TargetForm;