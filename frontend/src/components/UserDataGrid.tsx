import React, { useState, useEffect, forwardRef, useImperativeHandle, useCallback } from 'react';
import { AgGridReact } from 'ag-grid-react';
import { ColDef, GridReadyEvent, RowClickedEvent, RowDoubleClickedEvent } from 'ag-grid-community';
import 'ag-grid-community/styles/ag-grid.css';
import 'ag-grid-community/styles/ag-theme-alpine.css';
import { userApi } from '../services/api';
import { User } from '../types';

interface UserDataGridProps {
  onSelectionChanged?: (selectedUsers: User[]) => void;
  onRowDoubleClicked?: (user: User) => void;
  onDataLoaded?: (users: User[]) => void;
  className?: string;
}

export interface UserDataGridRef {
  refresh: () => void;
  getSelectedRows: () => User[];
}

const UserDataGrid = forwardRef<UserDataGridRef, UserDataGridProps>(({ 
  onSelectionChanged, 
  onRowDoubleClicked,
  onDataLoaded,
  className
}, ref) => {
  const [users, setUsers] = useState<User[]>([]);
  const [loading, setLoading] = useState(true);
  const [gridApi, setGridApi] = useState<any>(null);

  // Column definitions matching the assets pattern
  const columnDefs: ColDef[] = [
    {
      field: 'username',
      headerName: 'Username',
      flex: 1.2,
      minWidth: 150,
      sortable: true,
      filter: true,
      cellStyle: { fontWeight: '500' }
    },
    {
      field: 'full_name',
      headerName: 'Name',
      flex: 1.5,
      minWidth: 180,
      sortable: true,
      filter: true,
      valueGetter: (params) => {
        const firstName = params.data?.first_name || '';
        const lastName = params.data?.last_name || '';
        return `${firstName} ${lastName}`.trim() || '-';
      }
    },
    {
      field: 'role',
      headerName: 'Role',
      flex: 1,
      minWidth: 120,
      sortable: true,
      filter: true,
      cellRenderer: (params: any) => {
        const role = params.value;
        if (!role) return '-';
        
        const roleColors: Record<string, { bg: string; text: string }> = {
          admin: { bg: '#fee2e2', text: '#dc2626' },
          manager: { bg: '#fef3c7', text: '#d97706' },
          operator: { bg: '#f0f9ff', text: '#0369a1' },
          developer: { bg: '#f0fdf4', text: '#16a34a' },
          viewer: { bg: '#f8fafc', text: '#64748b' }
        };
        
        const colors = roleColors[role] || roleColors.viewer;
        
        return (
          <span style={{
            padding: '2px 8px',
            borderRadius: '12px',
            fontSize: '11px',
            fontWeight: '500',
            backgroundColor: colors.bg,
            color: colors.text,
            textTransform: 'capitalize'
          }}>
            {role}
          </span>
        );
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

  // Load users data
  const loadUsers = useCallback(async () => {
    try {
      setLoading(true);
      const response = await userApi.list();
      const usersData = response.data || [];
      setUsers(usersData);
      onDataLoaded?.(usersData);
    } catch (error) {
      console.error('Failed to load users:', error);
      setUsers([]);
      onDataLoaded?.([]);
    } finally {
      setLoading(false);
    }
  }, [onDataLoaded]); // Include onDataLoaded but ensure it's memoized in parent

  useEffect(() => {
    loadUsers();
  }, [loadUsers]); // Depend on loadUsers

  // Expose methods via ref
  useImperativeHandle(ref, () => ({
    refresh: loadUsers,
    getSelectedRows: () => {
      if (!gridApi) return [];
      return gridApi.getSelectedRows();
    }
  }));

  // Grid event handlers
  const onGridReady = (params: GridReadyEvent) => {
    setGridApi(params.api);
    
    // Auto-select first row when data loads
    if (users.length > 0) {
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

  // Auto-select first row when users data changes
  useEffect(() => {
    if (gridApi && users.length > 0) {
      setTimeout(() => {
        const firstNode = gridApi.getRowNode('0');
        if (firstNode && !gridApi.getSelectedRows().length) {
          firstNode.setSelected(true);
        }
      }, 100);
    }
  }, [users, gridApi]);

  if (loading) {
    return (
      <div className={`user-data-grid loading ${className || ''}`}>
        <div className="loading-spinner">Loading users...</div>
      </div>
    );
  }

  return (
    <div className={`user-data-grid ${className || ''}`}>
      <div 
        className="ag-theme-alpine ag-grid-wrapper"
        style={{ 
          height: users.length === 0 
            ? '60px' 
            : `${28 + (users.length * 32) + 3}px` // header + (rows * rowHeight) + padding
        }}
      >
        <AgGridReact
          rowData={users}
          columnDefs={columnDefs}
          onGridReady={onGridReady}
          onRowClicked={onRowClickedHandler}
          onRowDoubleClicked={onRowDoubleClickedHandler}
          suppressRowClickSelection={false}
          rowSelection="single"
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
        .user-data-grid {
          height: auto;
          width: 100%;
          overflow: visible;
          display: flex;
          flex-direction: column;
          border: none;
        }
        
        .user-data-grid.loading {
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
        .user-data-grid .ag-theme-alpine {
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
        .user-data-grid .ag-theme-alpine .ag-root-wrapper {
          border: 1px solid var(--ag-border-color) !important;
          border-radius: 0 !important;
          overflow: visible !important;
          background: transparent !important;
          min-height: 0 !important;
        }

        /* Override AG-Grid's default minimum heights */
        .user-data-grid .ag-theme-alpine .ag-body {
          min-height: 0 !important;
        }

        .user-data-grid .ag-theme-alpine .ag-body-viewport {
          min-height: 0 !important;
        }

        /* Header row border using AG-Grid's native border system */
        .user-data-grid .ag-theme-alpine .ag-header {
          border-bottom: 1px solid var(--ag-border-color) !important;
        }

        /* Header styling using AG-Grid's native system */
        .user-data-grid .ag-theme-alpine .ag-header-cell {
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
        .user-data-grid .ag-theme-alpine .ag-header-cell:last-child {
          border-right: none !important;
        }

        .user-data-grid .ag-theme-alpine .ag-header-cell:hover {
          background-color: #f1f3f4 !important;
          color: var(--primary-blue) !important;
          cursor: pointer !important;
        }

        .user-data-grid .ag-theme-alpine .ag-cell {
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
        .user-data-grid .ag-theme-alpine .ag-cell:last-child {
          border-right: none !important;
        }

        .user-data-grid .ag-theme-alpine .ag-row:hover .ag-cell {
          background-color: #f6f8fa !important;
        }

        .user-data-grid .ag-theme-alpine .ag-row-selected .ag-cell {
          background-color: var(--primary-blue-light) !important;
        }

        /* Ensure even rows have consistent styling with form */
        .user-data-grid .ag-theme-alpine .ag-row:nth-child(even) .ag-cell {
          background-color: #f9fafb !important;
        }

        .user-data-grid .ag-theme-alpine .ag-row:nth-child(even):hover .ag-cell {
          background-color: #f6f8fa !important;
        }

        /* Remove AG-Grid's default focus outline */
        .user-data-grid .ag-theme-alpine .ag-cell:focus,
        .user-data-grid .ag-theme-alpine .ag-header-cell:focus {
          outline: none !important;
        }

        /* Add fainter internal row borders using the same light gray as right panel */
        .user-data-grid .ag-theme-alpine .ag-row {
          border-bottom: 1px solid #eaeef2 !important;
        }

        /* Remove border from last row to avoid double border with table perimeter */
        .user-data-grid .ag-theme-alpine .ag-row:last-child {
          border-bottom: none !important;
        }

        /* Remove sorting icons to match ReactGrid */
        .user-data-grid .ag-theme-alpine .ag-header-cell .ag-header-cell-comp-wrapper {
          justify-content: flex-start;
        }

        .user-data-grid .ag-theme-alpine .ag-sort-indicator-container {
          display: none !important;
        }

        /* Ensure no selection checkboxes */
        .user-data-grid .ag-theme-alpine .ag-selection-checkbox {
          display: none !important;
        }

        /* Match ReactGrid's column proportions exactly */
        .user-data-grid .ag-theme-alpine .ag-header-viewport,
        .user-data-grid .ag-theme-alpine .ag-body-viewport {
          overflow-x: hidden !important;
        }
      `}</style>
    </div>
  );
});

UserDataGrid.displayName = 'UserDataGrid';

export default UserDataGrid;