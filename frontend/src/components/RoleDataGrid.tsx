import React, { useState, useEffect, forwardRef, useImperativeHandle, useCallback } from 'react';
import { AgGridReact } from 'ag-grid-react';
import { ColDef, GridReadyEvent, RowClickedEvent, RowDoubleClickedEvent } from 'ag-grid-community';
import 'ag-grid-community/styles/ag-grid.css';
import 'ag-grid-community/styles/ag-theme-alpine.css';
import { rolesApi } from '../services/api';
import { Role } from '../types';

interface RoleDataGridProps {
  onSelectionChanged?: (selectedRoles: Role[]) => void;
  onRowDoubleClicked?: (role: Role) => void;
  onDataLoaded?: (roles: Role[]) => void;
  className?: string;
}

export interface RoleDataGridRef {
  refresh: () => void;
  getSelectedRows: () => Role[];
}

const RoleDataGrid = forwardRef<RoleDataGridRef, RoleDataGridProps>(({ 
  onSelectionChanged, 
  onRowDoubleClicked,
  onDataLoaded,
  className
}, ref) => {
  const [roles, setRoles] = useState<Role[]>([]);
  const [loading, setLoading] = useState(true);
  const [gridApi, setGridApi] = useState<any>(null);

  // Column definitions matching the users pattern
  const columnDefs: ColDef[] = [
    {
      field: 'name',
      headerName: 'Role Name',
      flex: 1.2,
      minWidth: 150,
      sortable: true,
      filter: true,
      cellStyle: { fontWeight: '500' }
    },
    {
      field: 'description',
      headerName: 'Description',
      flex: 2.5,
      minWidth: 250,
      sortable: true,
      filter: true,
      valueGetter: (params) => {
        return params.data?.description || '-';
      }
    },
    {
      field: 'is_active',
      headerName: 'Status',
      flex: 0.8,
      minWidth: 100,
      sortable: true,
      filter: true,
      cellRenderer: (params: any) => {
        const isActive = params.value;
        return (
          <span style={{
            padding: '2px 8px',
            borderRadius: '12px',
            fontSize: '11px',
            fontWeight: '500',
            backgroundColor: isActive ? '#f0fdf4' : '#fef2f2',
            color: isActive ? '#16a34a' : '#dc2626'
          }}>
            {isActive ? 'Active' : 'Inactive'}
          </span>
        );
      }
    }
  ];

  // Load roles data
  const loadRoles = useCallback(async () => {
    try {
      setLoading(true);
      const response = await rolesApi.list();
      const rolesData = response.data || [];
      setRoles(rolesData);
      onDataLoaded?.(rolesData);
    } catch (error) {
      console.error('Failed to load roles:', error);
      setRoles([]);
      onDataLoaded?.([]);
    } finally {
      setLoading(false);
    }
  }, [onDataLoaded]); // Include onDataLoaded but ensure it's memoized in parent

  useEffect(() => {
    loadRoles();
  }, [loadRoles]); // Depend on loadRoles

  // Expose methods via ref
  useImperativeHandle(ref, () => ({
    refresh: loadRoles,
    getSelectedRows: () => {
      if (!gridApi) return [];
      return gridApi.getSelectedRows();
    }
  }));

  // Grid event handlers
  const onGridReady = (params: GridReadyEvent) => {
    setGridApi(params.api);
    
    // Auto-select first row when data loads
    if (roles.length > 0) {
      setTimeout(() => {
        params.api.getRowNode('0')?.setSelected(true);
      }, 100);
    }
  };

  const onRowClickedHandler = (event: RowClickedEvent) => {
    onSelectionChanged?.([event.data]);
  };

  const onRowDoubleClickedHandler = (event: RowDoubleClickedEvent) => {
    onRowDoubleClicked?.(event.data);
  };

  // Auto-select first row when roles data changes
  useEffect(() => {
    if (gridApi && roles.length > 0) {
      setTimeout(() => {
        const firstNode = gridApi.getRowNode('0');
        if (firstNode && !gridApi.getSelectedRows().length) {
          firstNode.setSelected(true);
        }
      }, 100);
    }
  }, [roles, gridApi]);

  if (loading) {
    return (
      <div className={`role-data-grid loading ${className || ''}`}>
        <div className="loading-spinner">Loading roles...</div>
      </div>
    );
  }

  return (
    <div className={`role-data-grid ${className || ''}`}>
      <div 
        className="ag-theme-alpine ag-grid-wrapper"
        style={{ 
          height: roles.length === 0 
            ? '60px' 
            : `${28 + (roles.length * 32) + 3}px` // header + (rows * rowHeight) + padding
        }}
      >
        <AgGridReact
          rowData={roles}
          columnDefs={columnDefs}
          onGridReady={onGridReady}
          onRowClicked={onRowClickedHandler}
          onRowDoubleClicked={onRowDoubleClickedHandler}
          rowSelection={{
            mode: 'singleRow',
            enableClickSelection: true,
            checkboxes: false
          }}
          animateRows={true}
          suppressCellFocus={true}
          suppressRowHoverHighlight={false}
          headerHeight={28}
          rowHeight={32}
          domLayout="normal"
          getRowId={(params) => params.data.id.toString()}
        />
      </div>

      <style>{`
        .role-data-grid {
          height: auto;
          width: 100%;
          overflow: visible;
          display: flex;
          flex-direction: column;
          border: none;
        }
        
        .role-data-grid.loading {
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
        .role-data-grid .ag-theme-alpine {
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
          min-height: 0 !important;
        }

        /* Table perimeter border using AG-Grid's native border system */
        .role-data-grid .ag-theme-alpine .ag-root-wrapper {
          border: 1px solid var(--ag-border-color) !important;
          border-radius: 0 !important;
          overflow: visible !important;
          background: transparent !important;
          min-height: 0 !important;
        }

        /* Override AG-Grid's default minimum heights */
        .role-data-grid .ag-theme-alpine .ag-body {
          min-height: 0 !important;
        }

        .role-data-grid .ag-theme-alpine .ag-body-viewport {
          min-height: 0 !important;
        }

        /* Header row border using AG-Grid's native border system */
        .role-data-grid .ag-theme-alpine .ag-header {
          border-bottom: 1px solid var(--ag-border-color) !important;
        }

        /* Header styling using AG-Grid's native system */
        .role-data-grid .ag-theme-alpine .ag-header-cell {
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
        .role-data-grid .ag-theme-alpine .ag-header-cell:last-child {
          border-right: none !important;
        }

        .role-data-grid .ag-theme-alpine .ag-header-cell:hover {
          background-color: #f1f3f4 !important;
          color: var(--primary-blue) !important;
          cursor: pointer !important;
        }

        .role-data-grid .ag-theme-alpine .ag-cell {
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
        .role-data-grid .ag-theme-alpine .ag-cell:last-child {
          border-right: none !important;
        }

        .role-data-grid .ag-theme-alpine .ag-row:hover .ag-cell {
          background-color: #f6f8fa !important;
        }

        .role-data-grid .ag-theme-alpine .ag-row-selected .ag-cell {
          background-color: var(--primary-blue-light) !important;
        }

        /* Ensure even rows have consistent styling with form */
        .role-data-grid .ag-theme-alpine .ag-row:nth-child(even) .ag-cell {
          background-color: #f9fafb !important;
        }

        .role-data-grid .ag-theme-alpine .ag-row:nth-child(even):hover .ag-cell {
          background-color: #f6f8fa !important;
        }

        /* Remove AG-Grid's default focus outline */
        .role-data-grid .ag-theme-alpine .ag-cell:focus,
        .role-data-grid .ag-theme-alpine .ag-header-cell:focus {
          outline: none !important;
        }

        /* Add fainter internal row borders using the same light gray as right panel */
        .role-data-grid .ag-theme-alpine .ag-row {
          border-bottom: 1px solid #eaeef2 !important;
        }

        /* Remove border from last row to avoid double border with table perimeter */
        .role-data-grid .ag-theme-alpine .ag-row:last-child {
          border-bottom: none !important;
        }

        /* Remove sorting icons to match ReactGrid */
        .role-data-grid .ag-theme-alpine .ag-header-cell .ag-header-cell-comp-wrapper {
          justify-content: flex-start;
        }

        .role-data-grid .ag-theme-alpine .ag-sort-indicator-container {
          display: none !important;
        }

        /* Ensure no selection checkboxes */
        .role-data-grid .ag-theme-alpine .ag-selection-checkbox {
          display: none !important;
        }

        /* Match ReactGrid's column proportions exactly */
        .role-data-grid .ag-theme-alpine .ag-header-viewport,
        .role-data-grid .ag-theme-alpine .ag-body-viewport {
          overflow-x: hidden !important;
        }
      `}</style>
    </div>
  );
});

RoleDataGrid.displayName = 'RoleDataGrid';

export default RoleDataGrid;