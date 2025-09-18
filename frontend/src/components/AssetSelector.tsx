import React, { useState, useEffect } from 'react';
import { assetApi } from '../services/api';
import { ChevronDown, Server, Monitor, HardDrive } from 'lucide-react';

interface Asset {
  id: number;
  name: string;
  hostname: string;
  ip_address?: string;
  os_type: string;
}

interface AssetSelectorProps {
  value?: string;
  onChange: (assetId: string, asset: Asset) => void;
  placeholder?: string;
  disabled?: boolean;
  allowOverride?: boolean;
  className?: string;
}

const AssetSelector: React.FC<AssetSelectorProps> = ({
  value,
  onChange,
  placeholder = "Select an asset...",
  disabled = false,
  allowOverride = false,
  className = ""
}) => {
  const [assets, setAssets] = useState<Asset[]>([]);
  const [loading, setLoading] = useState(true);
  const [isOpen, setIsOpen] = useState(false);
  const [searchTerm, setSearchTerm] = useState('');

  useEffect(() => {
    loadAssets();
  }, []);

  const loadAssets = async () => {
    try {
      setLoading(true);
      const response = await assetApi.list();
      setAssets(response.data?.assets || []);
    } catch (error) {
      console.error('Failed to load assets:', error);
    } finally {
      setLoading(false);
    }
  };

  const filteredAssets = assets.filter(asset =>
    asset.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
    (asset.hostname || asset.ip_address || '').toLowerCase().includes(searchTerm.toLowerCase())
  );

  const selectedAsset = assets.find(a => a.id.toString() === value);

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

  const handleSelect = (asset: Asset) => {
    onChange(asset.id.toString(), asset);
    setIsOpen(false);
    setSearchTerm('');
  };

  return (
    <div className={`relative ${className}`}>
      <div
        className={`
          w-full px-3 py-2 border border-gray-300 rounded-lg cursor-pointer
          flex items-center justify-between
          ${disabled ? 'bg-gray-100 cursor-not-allowed' : 'bg-white hover:border-gray-400'}
          ${isOpen ? 'border-blue-500 ring-1 ring-blue-500' : ''}
        `}
        onClick={() => !disabled && setIsOpen(!isOpen)}
      >
        <div className="flex items-center space-x-2 flex-1 min-w-0">
          {selectedAsset ? (
            <>
              {getPlatformIcon(selectedAsset.os_type)}
              <div className="flex-1 min-w-0">
                <div className="text-sm font-medium text-gray-900 truncate">
                  {selectedAsset.name}
                </div>
                <div className="text-xs text-gray-500 truncate">
                  {selectedAsset.hostname}
                  {selectedAsset.ip_address && ` (${selectedAsset.ip_address})`}
                </div>
              </div>
            </>
          ) : (
            <span className="text-gray-500">{placeholder}</span>
          )}
        </div>
        <ChevronDown className={`w-4 h-4 text-gray-400 transition-transform ${isOpen ? 'rotate-180' : ''}`} />
      </div>

      {/* Dropdown */}
      {isOpen && !disabled && (
        <div className="absolute z-50 w-full mt-1 bg-white border border-gray-300 rounded-lg shadow-lg max-h-60 overflow-hidden">
          {/* Search */}
          <div className="p-2 border-b border-gray-200">
            <input
              type="text"
              placeholder="Search assets..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="w-full px-2 py-1 text-sm border border-gray-300 rounded focus:outline-none focus:border-blue-500"
              onClick={(e) => e.stopPropagation()}
            />
          </div>

          {/* Asset List */}
          <div className="max-h-48 overflow-y-auto">
            {loading ? (
              <div className="p-3 text-center text-gray-500">Loading assets...</div>
            ) : filteredAssets.length === 0 ? (
              <div className="p-3 text-center text-gray-500">
                {searchTerm ? 'No assets found' : 'No assets available'}
              </div>
            ) : (
              filteredAssets.map((asset) => (
                <div
                  key={asset.id}
                  className={`
                    px-3 py-2 cursor-pointer flex items-center space-x-2
                    hover:bg-gray-50
                    ${selectedAsset?.id === asset.id ? 'bg-blue-50 text-blue-700' : 'text-gray-900'}
                  `}
                  onClick={() => handleSelect(asset)}
                >
                  {getPlatformIcon(asset.os_type)}
                  <div className="flex-1 min-w-0">
                    <div className="text-sm font-medium truncate">
                      {asset.name}
                    </div>
                    <div className="text-xs text-gray-500 truncate">
                      {asset.hostname}
                      {asset.ip_address && ` (${asset.ip_address})`}
                    </div>
                  </div>
                </div>
              ))
            )}
          </div>
        </div>
      )}

      {/* Click outside to close */}
      {isOpen && (
        <div
          className="fixed inset-0 z-40"
          onClick={() => setIsOpen(false)}
        />
      )}
    </div>
  );
};

export default AssetSelector;