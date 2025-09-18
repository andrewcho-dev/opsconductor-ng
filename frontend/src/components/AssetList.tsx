import React, { useState, useEffect, forwardRef, useImperativeHandle, useCallback, useRef } from 'react';
import { ChevronUp, ChevronDown } from 'lucide-react';
import { assetApi } from '../services/api';
import { Asset } from '../types/asset';

interface AssetListProps {
  onSelectionChanged?: (selectedAssets: Asset[]) => void;
  onRowDoubleClicked?: (asset: Asset) => void;
  onDataLoaded?: (assets: Asset[]) => void;
  onEditAsset?: (asset: Asset) => void;
  onDeleteAsset?: (assetId: number) => void;
  onTestConnection?: (assetId: number) => void;
}

export interface AssetListRef {
  refresh: () => void;
}

const AssetList = forwardRef<AssetListRef, AssetListProps>(({ 
  onSelectionChanged, 
  onRowDoubleClicked,
  onDataLoaded,
  onEditAsset,
  onDeleteAsset,
  onTestConnection
}, ref) => {
  const [assets, setAssets] = useState<Asset[]>([]);
  const [loading, setLoading] = useState(true);
  const [selectedAssetId, setSelectedAssetId] = useState<number | null>(null);
  const [openDropdown, setOpenDropdown] = useState<number | null>(null);
  const [sortField, setSortField] = useState<string | null>(null);
  const [sortDirection, setSortDirection] = useState<'asc' | 'desc'>('asc');
  const hasLoadedRef = useRef(false);
  const dropdownRef = useRef<HTMLDivElement>(null);

  // Load assets
  const loadAssets = useCallback(async () => {
    try {
      setLoading(true);
      const response = await assetApi.list(0, 1000);
      const assetsData = response.data?.assets || [];
      setAssets(assetsData);
      
      // Only call onDataLoaded once to prevent infinite loops
      if (!hasLoadedRef.current) {
        hasLoadedRef.current = true;
        onDataLoaded?.(assetsData);
      }
    } catch (error) {
      console.error('Failed to load assets:', error);
    } finally {
      setLoading(false);
    }
  }, [onDataLoaded]);

  useEffect(() => {
    if (!hasLoadedRef.current) {
      loadAssets();
    }
  }, [loadAssets]);

  // Close dropdown when clicking outside
  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (dropdownRef.current && !dropdownRef.current.contains(event.target as Node)) {
        setOpenDropdown(null);
      }
    };

    if (openDropdown) {
      document.addEventListener('mousedown', handleClickOutside);
      return () => document.removeEventListener('mousedown', handleClickOutside);
    }
  }, [openDropdown]);

  // Expose refresh method via ref
  useImperativeHandle(ref, () => ({
    refresh: loadAssets
  }));

  // Handle asset selection
  const handleAssetClick = (asset: Asset) => {
    setSelectedAssetId(asset.id);
    onSelectionChanged?.([asset]);
  };

  // Handle dropdown toggle
  const handleDropdownToggle = (assetId: number, event: React.MouseEvent) => {
    event.stopPropagation();
    setOpenDropdown(openDropdown === assetId ? null : assetId);
  };

  // Handle dropdown actions
  const handleDropdownAction = (action: string, assetId: number) => {
    const asset = assets.find(a => a.id === assetId);
    if (!asset) return;

    setOpenDropdown(null);

    switch (action) {
      case 'edit':
        onEditAsset?.(asset);
        break;
      case 'test':
        onTestConnection?.(assetId);
        break;
      case 'delete':
        onDeleteAsset?.(assetId);
        break;
    }
  };

  // Handle sorting
  const handleSort = (field: string) => {
    if (sortField === field) {
      setSortDirection(sortDirection === 'asc' ? 'desc' : 'asc');
    } else {
      setSortField(field);
      setSortDirection('asc');
    }
  };

  // Sort assets
  const sortedAssets = React.useMemo(() => {
    if (!sortField) return assets;

    return [...assets].sort((a, b) => {
      let aValue = '';
      let bValue = '';

      if (sortField === 'ip_address') {
        aValue = a.ip_address || '';
        bValue = b.ip_address || '';
      } else if (sortField === 'hostname') {
        aValue = a.hostname || '';
        bValue = b.hostname || '';
      }

      if (sortDirection === 'asc') {
        return aValue.localeCompare(bValue);
      } else {
        return bValue.localeCompare(aValue);
      }
    });
  }, [assets, sortField, sortDirection]);

  if (loading) {
    return (
      <div className="asset-list loading">
        <div className="loading-spinner">Loading assets...</div>
      </div>
    );
  }

  return (
    <div className="asset-list">
      <div className="sort-header">
        <div className="sort-controls">
          <button 
            className={`sort-button ${sortField === 'ip_address' ? 'active' : ''}`}
            onClick={() => handleSort('ip_address')}
          >
            <span>Sort by IP Address</span>
            <div className="sort-indicators">
              <ChevronUp 
                size={12} 
                className={`sort-icon ${sortField === 'ip_address' && sortDirection === 'asc' ? 'active' : ''}`} 
              />
              <ChevronDown 
                size={12} 
                className={`sort-icon ${sortField === 'ip_address' && sortDirection === 'desc' ? 'active' : ''}`} 
              />
            </div>
          </button>
          <button 
            className={`sort-button ${sortField === 'hostname' ? 'active' : ''}`}
            onClick={() => handleSort('hostname')}
          >
            <span>Sort by Hostname</span>
            <div className="sort-indicators">
              <ChevronUp 
                size={12} 
                className={`sort-icon ${sortField === 'hostname' && sortDirection === 'asc' ? 'active' : ''}`} 
              />
              <ChevronDown 
                size={12} 
                className={`sort-icon ${sortField === 'hostname' && sortDirection === 'desc' ? 'active' : ''}`} 
              />
            </div>
          </button>
        </div>
      </div>
      <div className="asset-list-container">
        {sortedAssets.map((asset) => (
          <div
            key={asset.id}
            className={`asset-item ${selectedAssetId === asset.id ? 'selected' : ''}`}
            onClick={() => handleAssetClick(asset)}
            onDoubleClick={() => onRowDoubleClicked?.(asset)}
          >
            <div className="asset-main-info">
              <div className="asset-name">{asset.name}</div>
              <div className="asset-hostname">{asset.hostname}</div>
              <div className="asset-details">
                <span className="asset-ip">{asset.ip_address || 'No IP'}</span>
                <span className="asset-os">{asset.os_type}</span>
                <span className={`asset-status ${asset.status?.toLowerCase() || 'unknown'}`}>
                  {asset.status || 'Unknown'}
                </span>
              </div>
              {asset.tags && asset.tags.length > 0 && (
                <div className="asset-tags">
                  {asset.tags.slice(0, 3).map((tag, index) => (
                    <span key={index} className="tag">{tag}</span>
                  ))}
                  {asset.tags.length > 3 && (
                    <span className="tag-more">+{asset.tags.length - 3}</span>
                  )}
                </div>
              )}
            </div>
            
            <div className="asset-actions">
              <button
                className="action-btn"
                onClick={(e) => handleDropdownToggle(asset.id, e)}
              >
                ⋮
              </button>
              
              {openDropdown === asset.id && (
                <div ref={dropdownRef} className="action-dropdown">
                  <button
                    className="dropdown-item"
                    onClick={() => handleDropdownAction('edit', asset.id)}
                  >
                    <span className="dropdown-icon">✏️</span>
                    Edit Asset
                  </button>
                  <button
                    className="dropdown-item"
                    onClick={() => handleDropdownAction('test', asset.id)}
                  >
                    <span className="dropdown-icon">🔗</span>
                    Test Connection
                  </button>
                  <button
                    className="dropdown-item delete"
                    onClick={() => handleDropdownAction('delete', asset.id)}
                  >
                    <span className="dropdown-icon">🗑️</span>
                    Delete Asset
                  </button>
                </div>
              )}
            </div>
          </div>
        ))}
        
        {sortedAssets.length === 0 && (
          <div className="empty-state">
            <h3>No assets found</h3>
            <p>Create your first asset to get started.</p>
          </div>
        )}
      </div>

      <style>{`
        .asset-list {
          height: 100%;
          display: flex;
          flex-direction: column;
        }

        .sort-header {
          padding: 8px 12px;
          border-bottom: 1px solid #dee2e6;
          background-color: #f8f9fa;
        }

        .sort-controls {
          display: flex;
          gap: 8px;
        }

        .sort-button {
          display: flex;
          align-items: center;
          gap: 4px;
          padding: 4px 8px;
          border: 1px solid #dee2e6;
          border-radius: 4px;
          background: white;
          color: #6c757d;
          font-size: 12px;
          cursor: pointer;
          transition: all 0.2s ease;
        }

        .sort-button:hover {
          border-color: #0d6efd;
          color: #0d6efd;
        }

        .sort-button.active {
          border-color: #0d6efd;
          background-color: #e3f2fd;
          color: #0d6efd;
        }

        .sort-indicators {
          display: flex;
          flex-direction: column;
          gap: 0;
          opacity: 0.5;
        }

        .sort-button:hover .sort-indicators {
          opacity: 0.8;
        }

        .sort-button.active .sort-indicators {
          opacity: 1;
        }

        .sort-icon {
          color: inherit;
          transition: color 0.2s ease;
        }

        .sort-icon.active {
          color: #0d6efd;
        }
        
        .loading {
          display: flex;
          align-items: center;
          justify-content: center;
          height: 200px;
        }
        
        .loading-spinner {
          color: #6c757d;
          font-size: 14px;
        }
        
        .asset-list-container {
          flex: 1;
          overflow-y: auto;
          padding: 8px;
          gap: 8px;
          display: flex;
          flex-direction: column;
        }
        
        .asset-item {
          display: flex;
          align-items: center;
          justify-content: space-between;
          padding: 12px 16px;
          border: 1px solid #dee2e6;
          border-radius: 6px;
          cursor: pointer;
          transition: all 0.2s ease;
          background: white;
          position: relative;
        }
        
        .asset-item:hover {
          border-color: #0d6efd;
          box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
        }
        
        .asset-item.selected {
          border-color: #0d6efd;
          background-color: #e3f2fd;
          box-shadow: 0 2px 8px rgba(13, 110, 253, 0.2);
        }
        
        .asset-main-info {
          flex: 1;
          min-width: 0;
        }
        
        .asset-name {
          font-weight: 600;
          font-size: 16px;
          color: #212529;
          margin-bottom: 4px;
        }
        
        .asset-hostname {
          font-size: 14px;
          color: #6c757d;
          margin-bottom: 6px;
        }
        
        .asset-details {
          display: flex;
          gap: 12px;
          font-size: 12px;
          margin-bottom: 6px;
        }
        
        .asset-ip {
          color: #495057;
        }
        
        .asset-os {
          color: #495057;
          background-color: #f8f9fa;
          padding: 2px 6px;
          border-radius: 4px;
        }
        
        .asset-status {
          padding: 2px 6px;
          border-radius: 4px;
          font-weight: 500;
          text-transform: uppercase;
        }
        
        .asset-status.active {
          background-color: #d1e7dd;
          color: #0f5132;
        }
        
        .asset-status.inactive {
          background-color: #f8d7da;
          color: #721c24;
        }
        
        .asset-status.unknown {
          background-color: #fff3cd;
          color: #664d03;
        }
        
        .asset-tags {
          display: flex;
          gap: 4px;
          flex-wrap: wrap;
        }
        
        .tag {
          background-color: #e9ecef;
          color: #495057;
          padding: 2px 6px;
          border-radius: 8px;
          font-size: 11px;
        }
        
        .tag-more {
          background-color: #6c757d;
          color: white;
          padding: 2px 6px;
          border-radius: 8px;
          font-size: 11px;
        }
        
        .asset-actions {
          position: relative;
          margin-left: 12px;
        }
        
        .action-btn {
          background: none;
          border: none;
          font-size: 18px;
          color: #6c757d;
          cursor: pointer;
          padding: 4px 8px;
          border-radius: 4px;
          transition: all 0.2s ease;
        }
        
        .action-btn:hover {
          background-color: #f8f9fa;
          color: #495057;
        }
        
        .action-dropdown {
          position: absolute;
          top: 100%;
          right: 0;
          background: white;
          border: 1px solid #dee2e6;
          border-radius: 6px;
          box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
          min-width: 160px;
          overflow: hidden;
          z-index: 1000;
        }
        
        .dropdown-item {
          width: 100%;
          padding: 8px 12px;
          border: none;
          background: none;
          text-align: left;
          cursor: pointer;
          font-size: 14px;
          display: flex;
          align-items: center;
          gap: 8px;
          transition: background-color 0.2s ease;
        }
        
        .dropdown-item:hover {
          background-color: #f8f9fa;
        }
        
        .dropdown-item.delete:hover {
          background-color: #f8d7da;
          color: #721c24;
        }
        
        .dropdown-icon {
          font-size: 12px;
          width: 16px;
          text-align: center;
        }
        
        .empty-state {
          text-align: center;
          padding: 40px 20px;
          color: #6c757d;
        }
        
        .empty-state h3 {
          margin-bottom: 8px;
          color: #495057;
        }
      `}</style>
    </div>
  );
});

AssetList.displayName = 'AssetList';

export default AssetList;