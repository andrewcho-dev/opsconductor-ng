import React, { useState, useEffect } from 'react';
import { Target } from '../types';
import { targetApi } from '../services/api';
import { ChevronDown, Server, Monitor, HardDrive } from 'lucide-react';

interface TargetSelectorProps {
  value?: string;
  onChange: (targetId: string, targetInfo?: Target) => void;
  placeholder?: string;
  disabled?: boolean;
  allowOverride?: boolean; // Allow data input to override configured target
  className?: string;
}

const TargetSelector: React.FC<TargetSelectorProps> = ({
  value,
  onChange,
  placeholder = "Select target...",
  disabled = false,
  allowOverride = false,
  className = ""
}) => {
  const [targets, setTargets] = useState<Target[]>([]);
  const [loading, setLoading] = useState(true);
  const [isOpen, setIsOpen] = useState(false);
  const [searchTerm, setSearchTerm] = useState('');

  useEffect(() => {
    loadTargets();
  }, []);

  const loadTargets = async () => {
    try {
      setLoading(true);
      const response = await targetApi.list();
      setTargets(response.targets || []);
    } catch (error) {
      console.error('Failed to load targets:', error);
    } finally {
      setLoading(false);
    }
  };

  const filteredTargets = targets.filter(target =>
    target.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
    (target.hostname || target.ip_address || '').toLowerCase().includes(searchTerm.toLowerCase())
  );

  const selectedTarget = targets.find(t => t.id.toString() === value);

  const getPlatformIcon = (platform: string) => {
    switch (platform.toLowerCase()) {
      case 'windows':
        return <Monitor className="w-4 h-4 text-blue-500" />;
      case 'linux':
        return <Server className="w-4 h-4 text-green-500" />;
      default:
        return <HardDrive className="w-4 h-4 text-gray-500" />;
    }
  };

  const handleSelect = (target: Target) => {
    onChange(target.id.toString(), target);
    setIsOpen(false);
    setSearchTerm('');
  };

  return (
    <div className={`relative ${className}`}>
      <div
        className={`
          flex items-center justify-between px-3 py-2 border rounded-md cursor-pointer
          ${disabled ? 'bg-gray-100 cursor-not-allowed' : 'bg-white hover:border-blue-300'}
          ${isOpen ? 'border-blue-500 ring-1 ring-blue-500' : 'border-gray-300'}
        `}
        onClick={() => !disabled && setIsOpen(!isOpen)}
      >
        <div className="flex items-center gap-2 flex-1">
          {selectedTarget ? (
            <>
              {getPlatformIcon(selectedTarget.os_type)}
              <span className="font-medium">{selectedTarget.name}</span>
              <span className="text-sm text-gray-500">({selectedTarget.hostname || selectedTarget.ip_address})</span>
            </>
          ) : (
            <span className="text-gray-500">{placeholder}</span>
          )}
        </div>
        <ChevronDown className={`w-4 h-4 text-gray-400 transition-transform ${isOpen ? 'rotate-180' : ''}`} />
      </div>

      {isOpen && (
        <div className="absolute z-50 w-full mt-1 bg-white border border-gray-300 rounded-md shadow-lg max-h-60 overflow-hidden">
          {/* Search */}
          <div className="p-2 border-b">
            <input
              type="text"
              placeholder="Search targets..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="w-full px-2 py-1 text-sm border border-gray-300 rounded focus:outline-none focus:border-blue-500"
              autoFocus
            />
          </div>

          {/* Target List */}
          <div className="max-h-48 overflow-y-auto">
            {loading ? (
              <div className="p-3 text-center text-gray-500">Loading targets...</div>
            ) : filteredTargets.length === 0 ? (
              <div className="p-3 text-center text-gray-500">
                {searchTerm ? 'No targets found' : 'No targets available'}
              </div>
            ) : (
              filteredTargets.map((target) => (
                <div
                  key={target.id}
                  className="flex items-center gap-2 px-3 py-2 hover:bg-gray-50 cursor-pointer"
                  onClick={() => handleSelect(target)}
                >
                  {getPlatformIcon(target.os_type)}
                  <div className="flex-1">
                    <div className="font-medium">{target.name}</div>
                    <div className="text-sm text-gray-500">{target.hostname || target.ip_address}</div>
                  </div>

                </div>
              ))
            )}
          </div>

          {/* Override Notice */}
          {allowOverride && (
            <div className="p-2 border-t bg-gray-50 text-xs text-gray-600">
              💡 This target can be overridden by input data
            </div>
          )}
        </div>
      )}
    </div>
  );
};

export default TargetSelector;