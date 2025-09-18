import React, { useState, useEffect, forwardRef, useImperativeHandle, useCallback, useRef } from 'react';
import { Edit3, Trash2 } from 'lucide-react';
import { assetApi } from '../services/api';
import { Asset } from '../types/asset';

interface AssetTableListProps {
  onSelectionChanged?: (selectedAssets: Asset[]) => void;
  onRowDoubleClicked?: (asset: Asset) => void;
  onDataLoaded?: (assets: Asset[]) => void;
  onEditAsset?: (asset: Asset) => void;
  onDeleteAsset?: (assetId: number) => void;
}

export interface AssetTableListRef {
  refresh: () => void;
}

const AssetTableList = forwardRef<AssetTableListRef, AssetTableListProps>(({ 
  onSelectionChanged, 
  onRowDoubleClicked,
  onDataLoaded,
  onEditAsset,
  onDeleteAsset
}, ref) => {
  const [assets, setAssets] = useState<Asset[]>([]);
  const [loading, setLoading] = useState(true);
  const [selectedAssetId, setSelectedAssetId] = useState<number | null>(null);
  const hasLoadedRef = useRef(false);

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

  // Expose refresh method via ref
  useImperativeHandle(ref, () => ({
    refresh: loadAssets
  }));

  // Handle asset selection
  const handleAssetClick = (asset: Asset) => {
    setSelectedAssetId(asset.id);
    onSelectionChanged?.([asset]);
  };

  // Handle double click
  const handleDoubleClick = (asset: Asset) => {
    onRowDoubleClicked?.(asset);
  };

  // Handle edit action
  const handleEdit = (asset: Asset, event: React.MouseEvent) => {
    event.stopPropagation();
    onEditAsset?.(asset);
  };

  // Handle delete action
  const handleDelete = (assetId: number, event: React.MouseEvent) => {
    event.stopPropagation();
    onDeleteAsset?.(assetId);
  };

  // Get device type from service type
  const getDeviceType = (asset: Asset): string => {
    switch (asset.service_type?.toLowerCase()) {
      case 'ssh':
        return asset.os_type === 'windows' ? 'Server' : 'Server';
      case 'rdp':
        return 'Workstation';
      case 'http':
      case 'https':
        return 'Web Server';
      case 'database':
        return 'Database';
      case 'ftp':
      case 'sftp':
        return 'Storage';
      default:
        return 'Server';
    }
  };

  if (loading) {
    return (
      <div className="asset-table-container">
        <div className="loading">
          <div className="loading-spinner">Loading assets...</div>
        </div>
        <style>{tableStyles}</style>
      </div>
    );
  }

  if (assets.length === 0) {
    return (
      <div className="asset-table-container">
        <div className="empty-state">
          <h3>No assets found</h3>
          <p>Click "Add Asset" to create your first asset.</p>
        </div>
        <style>{tableStyles}</style>
      </div>
    );
  }

  return (
    <div className="asset-table-container">
      <div className="table-wrapper">
        <table className="asset-table">
          <thead>
            <tr>
              <th>Name</th>
              <th>IP Address</th>
              <th>Hostname</th>
              <th>Device Type</th>
              <th>Service</th>
              <th>Actions</th>
            </tr>
          </thead>
          <tbody>
            {assets.map((asset) => (
              <tr
                key={asset.id}
                className={`asset-row ${selectedAssetId === asset.id ? 'selected' : ''}`}
                onClick={() => handleAssetClick(asset)}
                onDoubleClick={() => handleDoubleClick(asset)}
              >
                <td className="name-cell">
                  {asset.name}
                </td>
                <td className="ip-cell">
                  {asset.ip_address || '-'}
                </td>
                <td className="hostname-cell">
                  {asset.hostname}
                </td>
                <td className="device-type-cell">
                  {asset.device_type || getDeviceType(asset)}
                </td>
                <td className="service-cell">
                  {asset.service_type}:{asset.port}
                </td>
                <td className="actions-cell">
                  <div className="action-buttons">
                    <button
                      className="btn-icon btn-ghost"
                      onClick={(e) => handleEdit(asset, e)}
                      title="Edit Asset"
                    >
                      <Edit3 size={16} />
                    </button>
                    <button
                      className="btn-icon btn-danger"
                      onClick={(e) => handleDelete(asset.id, e)}
                      title="Delete Asset"
                    >
                      <Trash2 size={16} />
                    </button>
                  </div>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      <style>{tableStyles}</style>
    </div>
  );
});

const tableStyles = `
  .asset-table-container {
    height: 100%;
    display: flex;
    flex-direction: column;
    background: white;
    border: 1px solid #d0d7de;
    overflow: hidden;
  }
  
  .table-wrapper {
    flex: 1;
    overflow: auto;
  }
  
  .asset-table {
    width: 100%;
    border-collapse: collapse;
    font-size: 12px;
    line-height: 1.2;
  }
  
  .asset-table thead {
    background-color: #f6f8fa;
    position: sticky;
    top: 0;
    z-index: 10;
  }
  
  .asset-table th {
    padding: 6px 8px;
    text-align: left;
    font-weight: 600;
    color: #24292f;
    border-bottom: 1px solid #d0d7de;
    border-right: 1px solid #d0d7de;
    white-space: nowrap;
    font-size: 11px;
  }
  
  .asset-table th:last-child {
    border-right: none;
  }
  
  .asset-table tbody tr {
    cursor: pointer;
    transition: background-color 0.1s ease;
  }
  
  .asset-table tbody tr:hover {
    background-color: #f6f8fa;
  }
  
  .asset-table tbody tr.selected {
    background-color: #dbeafe;
    border-left: 2px solid #2563eb;
  }
  
  .asset-table tbody tr:nth-child(even) {
    background-color: #f9fafb;
  }
  
  .asset-table tbody tr:nth-child(even):hover {
    background-color: #f6f8fa;
  }
  
  .asset-table tbody tr.selected:nth-child(even) {
    background-color: #dbeafe;
  }
  
  .asset-table td {
    padding: 6px 8px;
    border-bottom: 1px solid #eaeef2;
    border-right: 1px solid #eaeef2;
    vertical-align: middle;
    font-size: 12px;
  }
  
  .asset-table td:last-child {
    border-right: none;
  }
  
  .name-cell {
    min-width: 120px;
    font-weight: 600;
    color: #24292f;
  }

  .ip-cell {
    font-family: 'SF Mono', 'Monaco', 'Inconsolata', 'Roboto Mono', monospace;
    color: #0969da;
    min-width: 90px;
  }
  
  .hostname-cell {
    min-width: 140px;
    font-weight: 500;
    color: #24292f;
  }
  
  .device-type-cell {
    min-width: 80px;
    color: #24292f;
    font-weight: 500;
    text-transform: capitalize;
  }
  
  .environment-cell {
    min-width: 90px;
  }
  
  .status-cell {
    min-width: 80px;
  }
  
  .location-cell {
    min-width: 100px;
    color: #656d76;
    font-size: 11px;
  }
  
  .service-cell {
    min-width: 80px;
    font-family: 'SF Mono', 'Monaco', 'Inconsolata', 'Roboto Mono', monospace;
    color: #0969da;
    font-size: 11px;
  }
  
  .status-badge {
    display: inline-block;
    padding: 2px 6px;
    border-radius: 12px;
    font-size: 10px;
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 0.5px;
  }
  
  /* Environment badges */
  .env-production {
    background: #fef3c7;
    color: #92400e;
  }
  
  .env-staging {
    background: #e0e7ff;
    color: #3730a3;
  }
  
  .env-development {
    background: #dcfce7;
    color: #166534;
  }
  
  .env-testing {
    background: #fce7f3;
    color: #be185d;
  }
  
  .env-qa {
    background: #f3e8ff;
    color: #7c2d12;
  }
  
  .env-unknown {
    background: #f3f4f6;
    color: #6b7280;
  }
  
  /* Status badges */
  .status-active {
    background: #dcfce7;
    color: #166534;
  }
  
  .status-inactive {
    background: #fee2e2;
    color: #dc2626;
  }
  
  .status-maintenance {
    background: #fef3c7;
    color: #92400e;
  }
  
  .status-decommissioned {
    background: #f3f4f6;
    color: #6b7280;
  }
  
  .status-unknown {
    background: #f3f4f6;
    color: #6b7280;
  }
  
  .actions-cell {
    width: 60px;
    text-align: center;
  }
  
  .action-buttons {
    display: flex;
    gap: 4px;
    justify-content: center;
  }
  
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
  
  .btn-ghost {
    color: #6b7280;
  }
  
  .btn-ghost:hover:not(:disabled) {
    color: #374151;
  }
  
  .btn-danger {
    color: #dc2626;
  }
  
  .btn-danger:hover:not(:disabled) {
    color: #dc2626;
  }
  
  .loading {
    display: flex;
    align-items: center;
    justify-content: center;
    height: 120px;
    color: #656d76;
    font-size: 12px;
  }
  
  .empty-state {
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    height: 120px;
    color: #656d76;
    text-align: center;
  }
  
  .empty-state h3 {
    margin-bottom: 4px;
    color: #24292f;
    font-size: 14px;
  }
  
  .empty-state p {
    font-size: 12px;
  }
`;

AssetTableList.displayName = 'AssetTableList';

export default AssetTableList;