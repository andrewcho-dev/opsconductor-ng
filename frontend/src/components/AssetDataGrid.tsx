import React, { useState, useEffect, forwardRef, useImperativeHandle, useCallback, useRef, useMemo } from 'react';
import { ReactGrid, Column, Row, Cell } from '@silevis/reactgrid';
import '@silevis/reactgrid/styles.css';

import { assetApi } from '../services/api';
import { Asset } from '../types/asset';

interface AssetDataGridProps {
  onSelectionChanged?: (selectedAssets: Asset[]) => void;
  onRowDoubleClicked?: (asset: Asset) => void;
  onDataLoaded?: (assets: Asset[]) => void;
}

export interface AssetDataGridRef {
  refresh: () => void;
}

const AssetDataGrid = forwardRef<AssetDataGridRef, AssetDataGridProps>((props, ref) => {
  const { onSelectionChanged, onRowDoubleClicked, onDataLoaded } = props;
  
  console.log('AssetDataGrid: Component rendering');
  
  const [assets, setAssets] = useState<Asset[]>([]);
  const [loading, setLoading] = useState(true);
  const [selectedRowIds, setSelectedRowIds] = useState<string[]>([]);
  const [focusedRowId, setFocusedRowId] = useState<string | null>(null);

  const [sortField, setSortField] = useState<string | null>(null);
  const [sortDirection, setSortDirection] = useState<'asc' | 'desc'>('asc');
  const hasLoadedRef = useRef(false);
  const gridRef = useRef<HTMLDivElement>(null);

  // Sort assets based on current sort field and direction
  const sortedAssets = useMemo(() => {
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

  // Auto-focus the grid when component first mounts and has data
  useEffect(() => {
    if (assets.length > 0 && !focusedRowId) {
      console.log('AssetDataGrid: Auto-focusing grid on first load');
      
      // Wait for ReactGrid to be fully rendered
      const autoFocus = () => {
        const gridContainer = gridRef.current;
        if (gridContainer) {
          // Focus the grid container to enable keyboard navigation
          gridContainer.focus();
          console.log('AssetDataGrid: Grid container focused');
          
          // Set the first asset as focused
          const firstAsset = sortedAssets[0];
          if (firstAsset) {
            const firstAssetId = firstAsset.id.toString();
            console.log('AssetDataGrid: Auto-selecting first asset:', firstAsset.name, 'ID:', firstAssetId);
            setFocusedRowId(firstAssetId);
          }
        } else {
          console.log('AssetDataGrid: Grid container not ready for auto-focus, retrying...');
          setTimeout(autoFocus, 100);
        }
      };
      
      // Delay to ensure ReactGrid is fully rendered
      setTimeout(autoFocus, 500);
    }
  }, [assets, focusedRowId, sortedAssets]);

  // Handle keyboard navigation
  useEffect(() => {
    console.log('AssetDataGrid: Setting up keyboard event listener');
    
    const handleKeyDown = (event: KeyboardEvent) => {
      console.log('AssetDataGrid: ANY KEY PRESSED:', event.key);
      
      // Only handle arrow keys
      if (event.key !== 'ArrowUp' && event.key !== 'ArrowDown') {
        return;
      }
      
      // Only handle arrow keys when not in an input field
      if (document.activeElement?.tagName === 'INPUT' || document.activeElement?.tagName === 'TEXTAREA') {
        console.log('AssetDataGrid: Ignoring key - focus is in input field');
        return;
      }
      
      console.log('AssetDataGrid: Processing arrow key:', event.key);
      
      const currentIndex = focusedRowId ? sortedAssets.findIndex(asset => asset.id.toString() === focusedRowId) : 0;
      console.log('AssetDataGrid: Current focusedRowId:', focusedRowId, 'currentIndex:', currentIndex);
      let newIndex = currentIndex;

      switch (event.key) {
        case 'ArrowDown':
          event.preventDefault();
          newIndex = Math.min(currentIndex + 1, sortedAssets.length - 1);
          console.log('AssetDataGrid: ArrowDown - newIndex:', newIndex);
          break;
        case 'ArrowUp':
          event.preventDefault();
          newIndex = Math.max(currentIndex - 1, 0);
          console.log('AssetDataGrid: ArrowUp - newIndex:', newIndex);
          break;
        case 'Home':
          event.preventDefault();
          newIndex = 0;
          console.log('AssetDataGrid: Home - newIndex:', newIndex);
          break;
        case 'End':
          event.preventDefault();
          newIndex = sortedAssets.length - 1;
          console.log('AssetDataGrid: End - newIndex:', newIndex);
          break;
        default:
          console.log('AssetDataGrid: Ignoring key:', event.key);
          return;
      }

      if (newIndex >= 0 && newIndex < sortedAssets.length) {
        const newFocusedRowId = sortedAssets[newIndex].id.toString();
        console.log('AssetDataGrid: Keyboard navigation - setting focusedRowId from', focusedRowId, 'to:', newFocusedRowId, 'for asset:', sortedAssets[newIndex].name);
        setFocusedRowId(newFocusedRowId);
      } else {
        console.log('AssetDataGrid: Invalid newIndex:', newIndex, 'sortedAssets.length:', sortedAssets.length);
      }
    };

    const gridContainer = gridRef.current;
    if (gridContainer) {
      gridContainer.addEventListener('keydown', handleKeyDown);
      console.log('AssetDataGrid: Keyboard event listener added to grid container');
      
      return () => {
        console.log('AssetDataGrid: Removing keyboard event listener from grid container');
        gridContainer.removeEventListener('keydown', handleKeyDown);
      };
    } else {
      console.log('AssetDataGrid: Grid container not found, cannot add keyboard listener');
    }
  }, [focusedRowId, sortedAssets]);

  // Update focused row styling and trigger selection change
  useEffect(() => {
    // Update focused row styling
    const updateFocusedRow = () => {
      console.log('AssetDataGrid: Updating focused row styling for focusedRowId:', focusedRowId);
      
      // Wait for ReactGrid to be fully rendered
      const waitForGrid = () => {
        const allCells = document.querySelectorAll('.rg-cell');
        const dataCells = document.querySelectorAll('.rg-cell:not(.rg-header-cell)');
        
        console.log('AssetDataGrid: Found', allCells.length, 'total cells,', dataCells.length, 'data cells');
        
        if (allCells.length === 0) {
          console.log('AssetDataGrid: Grid not ready, retrying in 100ms...');
          setTimeout(waitForGrid, 100);
          return;
        }
        
        // ReactGrid doesn't use row elements - it uses cell-based layout
        // We need to highlight cells by their row position instead
        console.log('AssetDataGrid: ReactGrid uses cell-based layout, no row elements found');
        
        // Remove previous focused classes from all cells
        const previousFocusedCells = document.querySelectorAll('.rg-cell.focused-row-cell');
        console.log('AssetDataGrid: Removing focused-row-cell class from', previousFocusedCells.length, 'cells');
        previousFocusedCells.forEach(cell => {
          cell.classList.remove('focused-row-cell');
        });
        
        // Continue with the rest of the highlighting logic
        highlightFocusedRow();
      };
      
      const highlightFocusedRow = () => {
        if (!focusedRowId) return;
        
        // Find the row index for the focused asset
        const rowIndex = sortedAssets.findIndex(asset => asset.id.toString() === focusedRowId);
        if (rowIndex < 0) {
          console.log('AssetDataGrid: Could not find asset with focusedRowId:', focusedRowId);
          return;
        }
        
        console.log('AssetDataGrid: Highlighting row index:', rowIndex, 'for asset ID:', focusedRowId);
        
        // ReactGrid uses CSS Grid layout - cells are positioned by grid-row and grid-column
        // We need to find all cells in the same row (same grid-row value)
        const allCells = document.querySelectorAll('.rg-cell:not(.rg-header-cell)');
        const cellsInRow: Element[] = [];
        
        // Calculate expected grid-row value (header is row 1, data starts at row 2)
        const expectedGridRow = rowIndex + 2;
        
        allCells.forEach(cell => {
          const computedStyle = window.getComputedStyle(cell);
          const gridRow = computedStyle.gridRow || computedStyle.gridRowStart;
          
          // Check if this cell is in our target row
          if (gridRow === expectedGridRow.toString() || 
              gridRow === `${expectedGridRow} / ${expectedGridRow + 1}` ||
              gridRow === `${expectedGridRow} / auto`) {
            cellsInRow.push(cell);
          }
        });
        
        if (cellsInRow.length === 0) {
          // Fallback: try to find cells by their position in the DOM
          // Assuming 4 columns (hostname, ip_address, device_type, tags), each row has 4 cells
          const columnsCount = 4;
          const startIndex = rowIndex * columnsCount;
          const endIndex = startIndex + columnsCount;
          
          console.log('AssetDataGrid: Fallback - looking for cells at indices', startIndex, 'to', endIndex - 1);
          
          for (let i = startIndex; i < endIndex && i < allCells.length; i++) {
            cellsInRow.push(allCells[i]);
          }
        }
        
        console.log('AssetDataGrid: Found', cellsInRow.length, 'cells in row', rowIndex);
        
        // Highlight all cells in the row
        cellsInRow.forEach(cell => {
          cell.classList.add('focused-row-cell');
        });
      };
      
      // Start waiting for grid to be ready
      waitForGrid();
    };

    // Longer delay to ensure ReactGrid has fully rendered
    const timer = setTimeout(updateFocusedRow, 300); // Much longer delay

    // Trigger selection change for focused row
    if (focusedRowId) {
      const focusedAsset = sortedAssets.find(asset => asset.id.toString() === focusedRowId);
      if (focusedAsset) {
        console.log('AssetDataGrid: Triggering selection change for:', focusedAsset.name, 'ID:', focusedAsset.id);
        onSelectionChanged?.([focusedAsset]);
      } else {
        console.log('AssetDataGrid: Could not find asset with focusedRowId:', focusedRowId);
      }
    } else {
      console.log('AssetDataGrid: No focusedRowId set');
    }

    return () => clearTimeout(timer);
  }, [focusedRowId, sortedAssets, onSelectionChanged]);

  // Set initial focus when assets load
  useEffect(() => {
    if (sortedAssets.length > 0 && !focusedRowId) {
      setFocusedRowId(sortedAssets[0].id.toString());
    }
  }, [sortedAssets, focusedRowId]);

  // Handle sorting
  const handleSort = (field: string) => {
    if (sortField === field) {
      setSortDirection(sortDirection === 'asc' ? 'desc' : 'asc');
    } else {
      setSortField(field);
      setSortDirection('asc');
    }
  };

  // Convert assets to ReactGrid format
  const getColumns = (): Column[] => [
    { columnId: 'hostname', width: 180 },
    { columnId: 'ip_address', width: 120 },
    { columnId: 'device_type', width: 100 },
    { columnId: 'tags', width: 150 }
  ];

  const getRows = (): Row[] => {
    const getSortIndicator = (field: string) => {
      if (sortField !== field) return ' ⇅';
      return sortDirection === 'asc' ? ' ↑' : ' ↓';
    };

    const headerRow: Row = {
      rowId: 'header',
      cells: [
        { type: 'header', text: `Hostname${getSortIndicator('hostname')}` },
        { type: 'header', text: `IP Address${getSortIndicator('ip_address')}` },
        { type: 'header', text: 'Device Type' },
        { type: 'header', text: 'Tags' }
      ]
    };

    const dataRows: Row[] = sortedAssets.map((asset) => ({
      rowId: asset.id.toString(),
      cells: [
        { type: 'text', text: asset.hostname },
        { type: 'text', text: asset.ip_address || '-' },
        { type: 'text', text: asset.device_type || '-' },
        { type: 'text', text: asset.tags.join(', ') }
      ]
    }));

    return [headerRow, ...dataRows];
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
    // Handle header row clicks for sorting
    if (rowId === 'header') {
      const target = event.target as HTMLElement;
      const cell = target.closest('.rg-cell');
      const columnIndex = Array.from(cell?.parentElement?.children || []).indexOf(cell as Element);
      const columnId = getColumns()[columnIndex]?.columnId || '';
      
      if (columnId === 'hostname' || columnId === 'ip_address') {
        handleSort(columnId);
      }
      return;
    }
    
    // Get column info for potential special handling
    const target = event.target as HTMLElement;
    const cell = target.closest('.rg-cell');
    const columnIndex = Array.from(cell?.parentElement?.children || []).indexOf(cell as Element);
    const columnId = getColumns()[columnIndex]?.columnId || '';
    
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
    setFocusedRowId(rowId); // Also update focused row when clicking
    const selectedAssets = sortedAssets.filter(asset => 
      newSelection.includes(asset.id.toString())
    );
    onSelectionChanged?.(selectedAssets);
  };

  // Handle cell click (for double-click detection)
  const handleCellClick = (rowId: string, columnId: string, event: React.MouseEvent) => {
    if (event.detail === 2) { // Double click
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
        ref={gridRef}
        className="reactgrid-wrapper"
        tabIndex={0}
        style={{ outline: 'none !important', border: 'none !important' }}
        onFocus={(e) => {
          // Immediately blur to prevent the blue outline, but keep keyboard events working
          e.target.style.outline = 'none';
          e.target.style.border = 'none';
        }}
        onClick={(e) => {
          console.log('AssetDataGrid: Grid container clicked');
          const target = e.target as HTMLElement;
          const cell = target.closest('.rg-cell');
          
          if (cell) {
            const rowIndex = parseInt(cell.getAttribute('data-cell-rowidx') || '0');
            const columnIndex = parseInt(cell.getAttribute('data-cell-colidx') || '0');
            const rows = getRows();
            const columns = getColumns();
            
            const rowId = rows[rowIndex]?.rowId || '';
            const columnId = columns[columnIndex]?.columnId || '';
            
            // Handle header clicks for sorting
            if (rowId === 'header' && (columnId === 'hostname' || columnId === 'ip_address')) {
              handleSort(columnId);
            }
            // Handle regular row clicks
            else if (rowId !== 'header') {
              handleRowClick(rowId, e);
            }
          }
        }}
      >
        <ReactGrid 
          rows={getRows()} 
          columns={getColumns()}
          enableRangeSelection={false}
          enableRowSelection={false}
          enableFillHandle={false}
          enableColumnSelection={false}
          onCellsChanged={() => {}} // Disable all cell changes
          onFocusLocationChanged={(location) => {
            console.log('AssetDataGrid: Focus location changed:', location);
            if (location && location.rowId !== 'header') {
              const rowId = location.rowId.toString();
              console.log('AssetDataGrid: Setting focusedRowId to:', rowId);
              setFocusedRowId(rowId);
              
              // Trigger selection change
              const asset = sortedAssets.find(a => a.id.toString() === rowId);
              if (asset) {
                console.log('AssetDataGrid: Triggering selection change for:', asset.name);
                onSelectionChanged?.([asset]);
              }
              
              // Try immediate row highlighting based on currently focused cell
              setTimeout(() => {
                const focusedCell = document.querySelector('.rg-cell-focus, .rg-cell:focus');
                if (focusedCell) {
                  console.log('AssetDataGrid: Found focused cell, trying to highlight its row using cell-based approach');
                  
                  // Remove previous highlights
                  document.querySelectorAll('.rg-cell.focused-row-cell').forEach(cell => {
                    cell.classList.remove('focused-row-cell');
                  });
                  
                  // Get the focused cell's grid position
                  const computedStyle = window.getComputedStyle(focusedCell);
                  const gridRow = computedStyle.gridRow || computedStyle.gridRowStart;
                  
                  if (gridRow) {
                    console.log('AssetDataGrid: Focused cell is in grid row:', gridRow);
                    
                    // Find all cells in the same row
                    const allCells = document.querySelectorAll('.rg-cell:not(.rg-header-cell)');
                    const cellsInSameRow: Element[] = [];
                    
                    allCells.forEach(cell => {
                      const cellStyle = window.getComputedStyle(cell);
                      const cellGridRow = cellStyle.gridRow || cellStyle.gridRowStart;
                      
                      if (cellGridRow === gridRow) {
                        cellsInSameRow.push(cell);
                      }
                    });
                    
                    console.log('AssetDataGrid: Found', cellsInSameRow.length, 'cells in same row');
                    
                    // Highlight all cells in the row
                    cellsInSameRow.forEach(cell => {
                      cell.classList.add('focused-row-cell');
                    });
                  } else {
                    console.log('AssetDataGrid: Could not determine grid row for focused cell');
                  }
                } else {
                  console.log('AssetDataGrid: Could not find focused cell');
                  
                  // Alternative approach - try to find any cell with focus-related classes
                  const alternativeCells = document.querySelectorAll('.rg-cell.rg-cell-focus, .rg-cell[tabindex="0"]');
                  console.log('AssetDataGrid: Found', alternativeCells.length, 'alternative focused cells');
                  
                  if (alternativeCells.length > 0) {
                    const cell = alternativeCells[0];
                    console.log('AssetDataGrid: Using alternative cell for row highlighting');
                    
                    // Get the alternative cell's grid position
                    const computedStyle = window.getComputedStyle(cell);
                    const gridRow = computedStyle.gridRow || computedStyle.gridRowStart;
                    
                    if (gridRow) {
                      console.log('AssetDataGrid: Alternative cell is in grid row:', gridRow);
                      
                      // Find all cells in the same row
                      const allCells = document.querySelectorAll('.rg-cell:not(.rg-header-cell)');
                      const cellsInSameRow: Element[] = [];
                      
                      allCells.forEach(cell => {
                        const cellStyle = window.getComputedStyle(cell);
                        const cellGridRow = cellStyle.gridRow || cellStyle.gridRowStart;
                        
                        if (cellGridRow === gridRow) {
                          cellsInSameRow.push(cell);
                        }
                      });
                      
                      console.log('AssetDataGrid: Found', cellsInSameRow.length, 'cells in same row (alternative)');
                      
                      // Highlight all cells in the row
                      cellsInSameRow.forEach(cell => {
                        cell.classList.add('focused-row-cell');
                      });
                    }
                  }
                }
              }, 100); // Increased delay to ensure DOM is ready
            }
          }}
        />
      </div>

      
      <style>{`
        .asset-data-grid {
          width: auto;
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
          width: 100%;
          outline: none; /* Remove focus outline */
        }
        
        .reactgrid-wrapper:focus {
          outline: 2px solid #0d6efd;
          outline-offset: 2px;
        }
        
        /* ReactGrid custom styling */
        .reactgrid {
          border: 1px solid #dee2e6;
          border-radius: 6px;
        }
        
        .reactgrid .rg-cell {
          border-right: 1px solid #dee2e6;
          border-bottom: 1px solid #dee2e6;
          padding: 8px 12px;
          overflow: hidden;
          text-overflow: ellipsis;
          white-space: nowrap;
        }
        
        /* Header cell styling */
        .reactgrid .rg-cell.rg-header-cell {
          background-color: #f8f9fa !important;
          font-weight: 600;
          color: #495057;
        }
        
        .reactgrid .rg-cell.rg-header-cell:nth-child(1):hover,
        .reactgrid .rg-cell.rg-header-cell:nth-child(2):hover {
          background-color: #e9ecef !important;
          color: #0d6efd;
          cursor: pointer;
        }
        
        .reactgrid .rg-row[data-row-id="header"] {
          background-color: #f8f9fa;
          font-weight: 600;
        }

        .reactgrid .rg-row[data-row-id="header"] .rg-cell:nth-child(1):hover,
        .reactgrid .rg-row[data-row-id="header"] .rg-cell:nth-child(2):hover {
          background-color: #e9ecef;
          color: #0d6efd;
          cursor: pointer;
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
        
        /* Custom row focus styling (for keyboard navigation) */
        .reactgrid .rg-row.focused-row {
          background-color: #f0f8ff !important;
          border-left: 3px solid #0d6efd;
        }
        
        .reactgrid .rg-row.focused-row:hover {
          background-color: #e6f3ff !important;
        }
        
        .reactgrid .rg-row.focused-row .rg-cell {
          background-color: inherit;
        }
        
        /* When a row is both selected and focused, prioritize selection styling */
        .reactgrid .rg-row.selected-row.focused-row {
          background-color: #e3f2fd !important;
          border-left: 3px solid #0d6efd;
        }
        
        /* Flexible column widths */
        .reactgrid .rg-cell:nth-child(1) {
          width: 25%;
        }
        
        .reactgrid .rg-cell:nth-child(2) {
          width: 20%;
        }
        
        .reactgrid .rg-cell:nth-child(3) {
          width: 15%;
        }
        
        .reactgrid .rg-cell:nth-child(4) {
          width: 40%;
        }
      `}</style>
    </div>
  );
});

AssetDataGrid.displayName = 'AssetDataGrid';

export default AssetDataGrid;