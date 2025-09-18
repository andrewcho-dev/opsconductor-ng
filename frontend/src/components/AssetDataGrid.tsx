import React, { useState, useEffect, forwardRef, useImperativeHandle, useCallback, useRef } from 'react';
import { ReactGrid, Column, Row, Cell } from '@silevis/reactgrid';
import '@silevis/reactgrid/styles.css';
import { assetApi } from '../services/api';
import { Asset } from '../types/asset';

interface AssetDataGridProps {
  onSelectionChanged?: (selectedAssets: Asset[]) => void;
  onRowDoubleClicked?: (asset: Asset) => void;
  onDataLoaded?: (assets: Asset[]) => void;
  onEditAsset?: (asset: Asset) => void;
  onDeleteAsset?: (assetId: number) => void;
  onTestConnection?: (assetId: number) => void;
}

export interface AssetDataGridRef {
  refresh: () => void;
}

const AssetDataGrid = forwardRef<AssetDataGridRef, AssetDataGridProps>(({ 
  onSelectionChanged, 
  onRowDoubleClicked,
  onDataLoaded,
  onEditAsset,
  onDeleteAsset,
  onTestConnection
}, ref) => {
  const [assets, setAssets] = useState<Asset[]>([]);
  const [loading, setLoading] = useState(true);
  const [selectedRowIds, setSelectedRowIds] = useState<string[]>([]);
  const [openDropdown, setOpenDropdown] = useState<string | null>(null);
  const [dropdownPosition, setDropdownPosition] = useState<{x: number, y: number} | null>(null);
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
  }, []);

  useEffect(() => {
    if (!hasLoadedRef.current) {
      loadAssets();
    }
  }, []);

  // Close dropdown when clicking outside
  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (dropdownRef.current && !dropdownRef.current.contains(event.target as Node)) {
        setOpenDropdown(null);
        setDropdownPosition(null);
      }
    };

    if (openDropdown) {
      document.addEventListener('mousedown', handleClickOutside);
      return () => document.removeEventListener('mousedown', handleClickOutside);
    }
  }, [openDropdown]);

  // Update row selection styling
  useEffect(() => {
    const updateRowSelection = () => {
      // Remove previous selection classes
      document.querySelectorAll('.rg-row.selected-row').forEach(row => {
        row.classList.remove('selected-row');
      });
      
      // Add selection class to selected rows
      selectedRowIds.forEach(rowId => {
        const rowElement = document.querySelector(`.rg-row[data-row-id="${rowId}"]`);
        if (rowElement) {
          rowElement.classList.add('selected-row');
        }
      });
    };

    // Small delay to ensure ReactGrid has rendered
    const timer = setTimeout(updateRowSelection, 10);
    return () => clearTimeout(timer);
  }, [selectedRowIds, assets]);

  // Expose refresh method via ref
  useImperativeHandle(ref, () => ({
    refresh: loadAssets
  }));

  // Handle dropdown toggle
  const handleDropdownToggle = (assetId: string, event: React.MouseEvent) => {
    event.stopPropagation();
    
    if (openDropdown === assetId) {
      setOpenDropdown(null);
      setDropdownPosition(null);
    } else {
      const rect = (event.target as HTMLElement).getBoundingClientRect();
      setDropdownPosition({
        x: rect.right - 120, // Align dropdown to the right of button
        y: rect.bottom + 5
      });
      setOpenDropdown(assetId);
    }
  };

  // Handle dropdown actions
  const handleDropdownAction = (action: string, assetId: number) => {
    const asset = assets.find(a => a.id === assetId);
    if (!asset) return;

    setOpenDropdown(null);
    setDropdownPosition(null);

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

  // Convert assets to ReactGrid format
  const getColumns = (): Column[] => [
    { columnId: 'name', width: 200 },
    { columnId: 'hostname', width: 180 },
    { columnId: 'ip_address', width: 120 },
    { columnId: 'os_type', width: 100 },
    { columnId: 'status', width: 100 },
    { columnId: 'tags', width: 150 },
    { columnId: 'actions', width: 80 }
  ];

  const getRows = (): Row[] => {
    const headerRow: Row = {
      rowId: 'header',
      cells: [
        { type: 'header', text: 'Name' },
        { type: 'header', text: 'Hostname' },
        { type: 'header', text: 'IP Address' },
        { type: 'header', text: 'OS Type' },
        { type: 'header', text: 'Status' },
        { type: 'header', text: 'Tags' },
        { type: 'header', text: 'Actions' }
      ]
    };

    const dataRows: Row[] = assets.map((asset) => ({
      rowId: asset.id.toString(),
      cells: [
        { type: 'text', text: asset.name },
        { type: 'text', text: asset.hostname },
        { type: 'text', text: asset.ip_address || '-' },
        { type: 'text', text: asset.os_type },
        { type: 'text', text: asset.status || 'unknown' },
        { type: 'text', text: asset.tags.join(', ') },
        { type: 'text', text: '⋮' }
      ]
    }));

    return [headerRow, ...dataRows];
  };

  // Handle cell changes
  const handleChanges = (changes: any[]) => {
    console.log('ReactGrid changes:', changes);
  };

  // Handle row selection
  const handleSelectionChange = (selectedRowIds: string[]) => {
    console.log('Selection changed:', selectedRowIds);
    setSelectedRowIds(selectedRowIds);
    
    const selectedAssets = assets.filter(asset => 
      selectedRowIds.includes(asset.id.toString())
    );
    onSelectionChanged?.(selectedAssets);
  };

  // Handle row click for selection
  const handleRowClick = (rowId: string, event: React.MouseEvent) => {
    // Skip header row
    if (rowId === 'header') return;
    
    // Don't interfere with action button clicks
    const target = event.target as HTMLElement;
    const cell = target.closest('.rg-cell');
    const columnIndex = Array.from(cell?.parentElement?.children || []).indexOf(cell as Element);
    const columnId = getColumns()[columnIndex]?.columnId || '';
    
    if (columnId === 'actions') return;
    
    // Handle selection
    let newSelection: string[];
    if (event.ctrlKey || event.metaKey) {
      // Multi-select with Ctrl/Cmd
      newSelection = selectedRowIds.includes(rowId)
        ? selectedRowIds.filter(id => id !== rowId)
        : [...selectedRowIds, rowId];
    } else {
      // Single select
      newSelection = [rowId];
    }
    
    setSelectedRowIds(newSelection);
    const selectedAssets = assets.filter(asset => 
      newSelection.includes(asset.id.toString())
    );
    onSelectionChanged?.(selectedAssets);
  };

  // Handle cell click (for action buttons)
  const handleCellClick = (rowId: string, columnId: string, event: React.MouseEvent) => {
    if (columnId === 'actions') {
      handleDropdownToggle(rowId, event);
    } else if (event.detail === 2) { // Double click
      const asset = assets.find(a => a.id.toString() === rowId);
      if (asset) {
        onRowDoubleClicked?.(asset);
      }
    }
  };

  if (loading) {
    return (
      <div className="asset-data-grid loading">
        <div className="loading-spinner">Loading assets...</div>
      </div>
    );
  }

  return (
    <div className="asset-data-grid">
      <div 
        className="reactgrid-wrapper"
        onClick={(e) => {
          const target = e.target as HTMLElement;
          const cell = target.closest('.rg-cell');
          if (cell) {
            const rowElement = cell.closest('.rg-row');
            const columnIndex = Array.from(cell.parentElement?.children || []).indexOf(cell);
            const rowId = rowElement?.getAttribute('data-row-id') || '';
            const columnId = getColumns()[columnIndex]?.columnId || '';
            
            if (columnId === 'actions') {
              handleCellClick(rowId, columnId, e);
            } else {
              handleRowClick(rowId, e);
            }
          }
        }}
        onDoubleClick={(e) => {
          const target = e.target as HTMLElement;
          const cell = target.closest('.rg-cell');
          if (cell) {
            const rowElement = cell.closest('.rg-row');
            const rowId = rowElement?.getAttribute('data-row-id') || '';
            const asset = assets.find(a => a.id.toString() === rowId);
            if (asset) {
              onRowDoubleClicked?.(asset);
            }
          }
        }}
      >
        <ReactGrid
          rows={getRows()}
          columns={getColumns()}
          onChanges={handleChanges}
        />
      </div>

      {/* Custom dropdown menu */}
      {openDropdown && dropdownPosition && (
        <div
          ref={dropdownRef}
          className="action-dropdown"
          style={{
            position: 'fixed',
            left: dropdownPosition.x,
            top: dropdownPosition.y,
            zIndex: 1000
          }}
        >
          <button
            className="dropdown-item"
            onClick={() => handleDropdownAction('edit', parseInt(openDropdown))}
          >
            <span className="dropdown-icon">✏️</span>
            Edit Asset
          </button>
          <button
            className="dropdown-item"
            onClick={() => handleDropdownAction('test', parseInt(openDropdown))}
          >
            <span className="dropdown-icon">🔗</span>
            Test Connection
          </button>
          <button
            className="dropdown-item delete"
            onClick={() => handleDropdownAction('delete', parseInt(openDropdown))}
          >
            <span className="dropdown-icon">🗑️</span>
            Delete Asset
          </button>
        </div>
      )}
      
      <style>{`
        .asset-data-grid {
          width: 100%;
          height: 100%;
          display: flex;
          flex-direction: column;
          position: relative;
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
        
        .reactgrid-wrapper {
          flex: 1;
          overflow: auto;
        }
        
        /* ReactGrid custom styling */
        .reactgrid {
          border: 1px solid #dee2e6;
          border-radius: 6px;
          overflow: hidden;
        }
        
        .reactgrid .rg-cell {
          border-right: 1px solid #dee2e6;
          border-bottom: 1px solid #dee2e6;
        }
        
        .reactgrid .rg-header-cell {
          background-color: #f8f9fa;
          font-weight: 600;
          color: #495057;
        }
        
        .reactgrid .rg-cell.rg-cell-focus {
          border: 2px solid #0d6efd;
        }
        
        .reactgrid .rg-row.rg-row-selected {
          background-color: #e3f2fd;
        }
        
        /* Custom row selection styling */
        .reactgrid .rg-row.selected-row {
          background-color: #e3f2fd !important;
        }
        
        .reactgrid .rg-row.selected-row:hover {
          background-color: #bbdefb !important;
        }
        
        .reactgrid .rg-row.selected-row .rg-cell {
          background-color: inherit;
        }
        
        /* Action column styling */
        .reactgrid .rg-cell:last-child {
          text-align: center;
          cursor: pointer;
          user-select: none;
        }
        
        .reactgrid .rg-cell:last-child:hover {
          background-color: #f8f9fa;
        }
        
        /* Custom dropdown styling */
        .action-dropdown {
          background: white;
          border: 1px solid #dee2e6;
          border-radius: 6px;
          box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
          min-width: 160px;
          overflow: hidden;
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
      `}</style>
    </div>
  );
});

AssetDataGrid.displayName = 'AssetDataGrid';

export default AssetDataGrid;