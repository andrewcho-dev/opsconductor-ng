import React, { useState, useEffect, forwardRef, useImperativeHandle, useCallback, useRef, useMemo } from 'react';
import { AgGridReact } from 'ag-grid-react';
import { ColDef, GridReadyEvent, RowClickedEvent, RowDoubleClickedEvent, SortChangedEvent } from 'ag-grid-community';
import 'ag-grid-community/styles/ag-grid.css';
import 'ag-grid-community/styles/ag-theme-alpine.css';

import { assetApi } from '../services/api';
import { Asset } from '../types/asset';

interface AssetDataGridProps {
  onSelectionChanged?: (selectedAssets: Asset[]) => void;
  onRowDoubleClicked?: (asset: Asset) => void;
  onDataLoaded?: (assets: Asset[]) => void;
  className?: string;
}

export interface AssetDataGridRef {
  refresh: () => void;
}

const AssetDataGrid = forwardRef<AssetDataGridRef, AssetDataGridProps>((props, ref) => {
  const { onSelectionChanged, onRowDoubleClicked, onDataLoaded, className } = props;
  
  console.log('AssetDataGrid rendered with props:', { onSelectionChanged: !!onSelectionChanged, onRowDoubleClicked: !!onRowDoubleClicked, onDataLoaded: !!onDataLoaded });
  
  const [assets, setAssets] = useState<Asset[]>([]);
  const [loading, setLoading] = useState(true);
  const hasLoadedRef = useRef(false);
  const gridRef = useRef<AgGridReact>(null);

  // Load assets from API
  const loadAssets = useCallback(async () => {
    try {
      setLoading(true);
      const response = await assetApi.list();
      console.log('Assets loaded:', response);
      
      // Handle API response structure: {success: true, data: {assets: [...], total: 6}}
      const assetsData = response.data?.assets || response.assets || [];
      console.log('Assets data:', assetsData);
      
      // Ensure we have an array
      const assetsList = Array.isArray(assetsData) ? assetsData : [];
      setAssets(assetsList);
      
      if (onDataLoaded) {
        onDataLoaded(assetsList);
      }
      
      hasLoadedRef.current = true;
    } catch (error) {
      console.error('Error loading assets:', error);
      setAssets([]);
    } finally {
      setLoading(false);
    }
  }, [onDataLoaded]);

  // Load assets on mount
  useEffect(() => {
    if (!hasLoadedRef.current) {
      loadAssets();
    }
  }, [loadAssets]);

  // Expose refresh method
  useImperativeHandle(ref, () => ({
    refresh: loadAssets
  }));

  // Column definitions - showing hostname, ip address, device type, tags
  const columnDefs: ColDef[] = useMemo(() => [
    {
      field: 'hostname',
      headerName: 'Hostname',
      sortable: true,
      flex: 0.3,
      minWidth: 150,
    },
    {
      field: 'ip_address',
      headerName: 'IP Address',
      sortable: true,
      flex: 0.25,
      minWidth: 120,
    },
    {
      field: 'device_type',
      headerName: 'Device Type',
      sortable: true,
      flex: 0.2,
      minWidth: 100,
    },
    {
      field: 'tags',
      headerName: 'Tags',
      sortable: true,
      flex: 0.25,
      minWidth: 120,
      cellRenderer: (params: any) => {
        if (!params.value || !Array.isArray(params.value)) return '';
        return params.value.join(', ');
      }
    }
  ], []);

  // Handle row selection
  const onRowClicked = useCallback((event: RowClickedEvent) => {
    if (onSelectionChanged && event.data) {
      onSelectionChanged([event.data]);
    }
  }, [onSelectionChanged]);

  // Handle double click
  const onRowDoubleClick = useCallback((event: RowDoubleClickedEvent) => {
    if (onRowDoubleClicked && event.data) {
      onRowDoubleClicked(event.data);
    }
  }, [onRowDoubleClicked]);

  // Handle grid ready - select first row like ReactGrid did
  const onGridReady = useCallback((params: GridReadyEvent) => {
    if (assets.length > 0 && onSelectionChanged) {
      // Select first row on load, just like ReactGrid did
      onSelectionChanged([assets[0]]);
    }
  }, [assets, onSelectionChanged]);

  // Update selection when assets change
  useEffect(() => {
    if (assets.length > 0 && onSelectionChanged && !loading) {
      // Auto-select first asset when data loads
      onSelectionChanged([assets[0]]);
    }
  }, [assets.length, loading, onSelectionChanged]);

  if (loading) {
    return (
      <div className={`asset-data-grid loading ${className || ''}`}>
        <div className="loading-spinner">Loading assets...</div>
      </div>
    );
  }

  return (
    <div className={`asset-data-grid ${className || ''}`}>
      <div className="ag-theme-alpine ag-grid-wrapper">
        <AgGridReact
          ref={gridRef}
          rowData={assets}
          columnDefs={columnDefs}
          onRowClicked={onRowClicked}
          onRowDoubleClicked={onRowDoubleClick}
          onGridReady={onGridReady}
          suppressRowClickSelection={false}
          rowSelection="single"
          animateRows={true}
          suppressCellFocus={true}
          suppressRowHoverHighlight={false}
          headerHeight={28}
          rowHeight={32}
          domLayout="autoHeight"
        />
      </div>

      <style>{`
        .asset-data-grid {
          height: auto;
          width: 100%;
          overflow: visible;
          display: flex;
          flex-direction: column;
          border: none;
        }
        
        .asset-data-grid.loading {
          display: flex;
          align-items: center;
          justify-content: center;
          height: 200px;
          color: var(--neutral-600);
        }
        
        .loading-spinner {
          font-size: 14px;
        }
        
        .ag-grid-wrapper {
          height: auto;
          width: 100%;
          outline: none;
          background: transparent;
          border: none;
          overflow: visible;
        }
        
        .ag-grid-wrapper:focus {
          outline: none;
        }

        /* Custom AG-Grid theme using native border controls with high specificity */
        .asset-data-grid .ag-theme-alpine {
          --ag-background-color: transparent;
          --ag-header-background-color: #f6f8fa;
          --ag-header-foreground-color: #24292f;
          --ag-border-color: #d0d7de !important;
          --ag-borders: solid !important;
          --ag-row-hover-color: #f6f8fa;
          --ag-selected-row-background-color: var(--primary-blue-light);
          --ag-font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
          --ag-font-size: var(--font-size-sm);
          --ag-cell-horizontal-padding: 8px;
          --ag-header-height: 20px;
          --ag-row-height: 24px;
        }

        /* Table perimeter border using AG-Grid's native border system */
        .asset-data-grid .ag-theme-alpine .ag-root-wrapper {
          border: 1px solid var(--ag-border-color) !important;
          border-radius: 0 !important;
          overflow: visible !important;
          background: transparent !important;
        }

        /* Header row border using AG-Grid's native border system */
        .asset-data-grid .ag-theme-alpine .ag-header {
          border-bottom: 1px solid var(--ag-border-color) !important;
        }

        /* Header styling using AG-Grid's native system */
        .asset-data-grid .ag-theme-alpine .ag-header-cell {
          background: linear-gradient(135deg, #f6f8fa 0%, #e1e7ef 100%) !important;
          font-weight: 600 !important;
          color: #24292f !important;
          border-right: 1px solid #d0d7de !important;
          padding: 4px 8px !important;
          vertical-align: middle !important;
          line-height: 1.2 !important;
          font-size: var(--font-size-xs) !important;
          text-transform: uppercase !important;
          letter-spacing: 0.5px !important;
          display: flex !important;
          align-items: center !important;
        }

        /* Remove border from last header cell to avoid double border */
        .asset-data-grid .ag-theme-alpine .ag-header-cell:last-child {
          border-right: none !important;
        }

        .asset-data-grid .ag-theme-alpine .ag-header-cell:hover {
          background-color: #f1f3f4 !important;
          color: var(--primary-blue) !important;
          cursor: pointer !important;
        }

        .asset-data-grid .ag-theme-alpine .ag-cell {
          padding: 6px 8px !important;
          overflow: hidden !important;
          text-overflow: ellipsis !important;
          white-space: nowrap !important;
          cursor: pointer !important;
          user-select: none !important;
          vertical-align: middle !important;
          line-height: 1.4 !important;
          font-size: var(--font-size-sm) !important;
          color: #24292f !important;
          border-right: 1px solid #eaeef2 !important;
        }

        /* Remove border from last cell in each row to avoid double border */
        .asset-data-grid .ag-theme-alpine .ag-cell:last-child {
          border-right: none !important;
        }

        .asset-data-grid .ag-theme-alpine .ag-row:hover .ag-cell {
          background-color: #f6f8fa !important;
        }

        .asset-data-grid .ag-theme-alpine .ag-row-selected .ag-cell {
          background-color: var(--primary-blue-light) !important;
        }

        /* Ensure even rows have consistent styling with form */
        .asset-data-grid .ag-theme-alpine .ag-row:nth-child(even) .ag-cell {
          background-color: #f9fafb !important;
        }

        .asset-data-grid .ag-theme-alpine .ag-row:nth-child(even):hover .ag-cell {
          background-color: #f6f8fa !important;
        }

        /* Remove AG-Grid's default focus outline */
        .asset-data-grid .ag-theme-alpine .ag-cell:focus,
        .asset-data-grid .ag-theme-alpine .ag-header-cell:focus {
          outline: none !important;
        }

        /* Add fainter internal row borders using the same light gray as right panel */
        .asset-data-grid .ag-theme-alpine .ag-row {
          border-bottom: 1px solid #eaeef2 !important;
        }

        /* Remove border from last row to avoid double border with table perimeter */
        .asset-data-grid .ag-theme-alpine .ag-row:last-child {
          border-bottom: none !important;
        }

        /* Remove sorting icons to match ReactGrid */
        .asset-data-grid .ag-theme-alpine .ag-header-cell .ag-header-cell-comp-wrapper {
          justify-content: flex-start;
        }

        .asset-data-grid .ag-theme-alpine .ag-sort-indicator-container {
          display: none !important;
        }

        /* Ensure no selection checkboxes */
        .asset-data-grid .ag-theme-alpine .ag-selection-checkbox {
          display: none !important;
        }

        /* Match ReactGrid's column proportions exactly */
        .asset-data-grid .ag-theme-alpine .ag-header-viewport,
        .asset-data-grid .ag-theme-alpine .ag-body-viewport {
          overflow-x: hidden !important;
        }
      `}</style>
    </div>
  );
});

AssetDataGrid.displayName = 'AssetDataGrid';

export default AssetDataGrid;