import React from 'react';
import { Wifi, Terminal, Shield, Globe } from 'lucide-react';

interface ConnectionTypeSelectorProps {
  value: string;
  onChange: (value: string) => void;
  targetType?: string; // 'windows', 'linux', 'network', etc.
}

const ConnectionTypeSelector: React.FC<ConnectionTypeSelectorProps> = ({
  value,
  onChange,
  targetType
}) => {
  // Define available connection types based on target type
  const getConnectionTypes = () => {
    const baseTypes = [
      { value: 'ssh', label: 'SSH', icon: <Terminal size={14} />, description: 'Secure Shell (Linux/Unix)' },
      { value: 'winrm', label: 'WinRM', icon: <Shield size={14} />, description: 'Windows Remote Management' },
      { value: 'rdp', label: 'RDP', icon: <Globe size={14} />, description: 'Remote Desktop Protocol' },
      { value: 'telnet', label: 'Telnet', icon: <Terminal size={14} />, description: 'Telnet (Legacy)' },
      { value: 'snmp', label: 'SNMP', icon: <Wifi size={14} />, description: 'Simple Network Management Protocol' },
      { value: 'http', label: 'HTTP', icon: <Globe size={14} />, description: 'HTTP/HTTPS API' },
      { value: 'powershell', label: 'PowerShell', icon: <Terminal size={14} />, description: 'PowerShell Remoting' }
    ];

    // Filter based on target type if provided
    if (targetType) {
      switch (targetType.toLowerCase()) {
        case 'windows':
          return baseTypes.filter(t => ['winrm', 'rdp', 'powershell', 'ssh'].includes(t.value));
        case 'linux':
        case 'unix':
          return baseTypes.filter(t => ['ssh', 'telnet', 'http'].includes(t.value));
        case 'network':
          return baseTypes.filter(t => ['snmp', 'ssh', 'telnet', 'http'].includes(t.value));
        default:
          return baseTypes;
      }
    }

    return baseTypes;
  };

  const connectionTypes = getConnectionTypes();

  return (
    <div>
      <select
        value={value}
        onChange={(e) => onChange(e.target.value)}
        style={{
          width: '100%',
          padding: '8px',
          border: '1px solid #ddd',
          borderRadius: '4px',
          fontSize: '14px',
          backgroundColor: 'white'
        }}
      >
        <option value="">Select connection type...</option>
        {connectionTypes.map((type) => (
          <option key={type.value} value={type.value}>
            {type.label} - {type.description}
          </option>
        ))}
      </select>

      {value && (
        <div style={{
          marginTop: '8px',
          padding: '8px',
          backgroundColor: '#f8f9fa',
          borderRadius: '4px',
          fontSize: '12px',
          color: '#666',
          display: 'flex',
          alignItems: 'center',
          gap: '6px'
        }}>
          {connectionTypes.find(t => t.value === value)?.icon}
          <span>
            <strong>{connectionTypes.find(t => t.value === value)?.label}:</strong>{' '}
            {connectionTypes.find(t => t.value === value)?.description}
          </span>
        </div>
      )}
    </div>
  );
};

export default ConnectionTypeSelector;