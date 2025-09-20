import React, { useState, useEffect, useRef, useCallback } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import { Link } from 'react-router-dom';
import { Plus, X, Shield, Target, Settings, Play, MessageSquare, Edit3, Trash2 } from 'lucide-react';
import { rolesApi } from '../services/api';
import RoleDataGrid, { RoleDataGridRef } from '../components/RoleDataGrid';
import RoleSpreadsheetForm from '../components/RoleSpreadsheetForm';
import { Role } from '../types';

const Roles: React.FC = () => {
  const navigate = useNavigate();
  const { action, id } = useParams<{ action?: string; id?: string }>();
  
  const [roles, setRoles] = useState<Role[]>([]);
  const [loading, setLoading] = useState(true);
  const [selectedRole, setSelectedRole] = useState<Role | null>(null);
  const [editingRole, setEditingRole] = useState<Role | null>(null);
  const [addingNew, setAddingNew] = useState(false);
  const [loadingRoleDetails, setLoadingRoleDetails] = useState(false);
  const roleListRef = useRef<RoleDataGridRef>(null);
  const debounceTimeoutRef = useRef<NodeJS.Timeout | null>(null);

  // Fetch detailed role data
  const fetchDetailedRoleData = useCallback(async (roleId: number): Promise<Role | null> => {
    try {
      setLoadingRoleDetails(true);
      const roleData = await rolesApi.get(roleId);
      
      return roleData;
    } catch (error) {
      return null;
    } finally {
      setLoadingRoleDetails(false);
    }
  }, []);

  // Debounced function to fetch detailed role data
  const debouncedFetchRoleDetails = useCallback((role: Role) => {
    // Immediately set the basic role data to prevent flashing
    setSelectedRole(role);
    
    // Clear any existing timeout
    if (debounceTimeoutRef.current) {
      clearTimeout(debounceTimeoutRef.current);
    }

    // Set a new timeout for detailed data
    debounceTimeoutRef.current = setTimeout(() => {
      fetchDetailedRoleData(role.id).then(detailedRole => {
        if (detailedRole) {
          // Only update if we're still looking at the same role
          setSelectedRole(currentRole => {
            if (currentRole && currentRole.id === detailedRole.id) {
              return detailedRole;
            }
            return currentRole;
          });
        }
      });
    }, 300); // 300ms delay
  }, [fetchDetailedRoleData]);

  // Cleanup timeout on unmount
  useEffect(() => {
    return () => {
      if (debounceTimeoutRef.current) {
        clearTimeout(debounceTimeoutRef.current);
      }
    };
  }, []);

  // Memoized selection change handler to prevent infinite re-renders
  const handleSelectionChange = useCallback((selectedRoles: Role[]) => {
    if (selectedRoles.length > 0) {
      const role = selectedRoles[0];
      // Use debounced fetch to prevent too many API calls during keyboard navigation
      debouncedFetchRoleDetails(role);
    } else {
      setSelectedRole(null);
    }
  }, [debouncedFetchRoleDetails]);

  // Memoized data loaded handler to prevent infinite re-renders
  const handleDataLoaded = useCallback((loadedRoles: Role[]) => {
    setRoles(loadedRoles);
    setLoading(false);
  }, []);

  // Handle URL-based actions
  useEffect(() => {
    if (action === 'create') {
      setAddingNew(true);
      setSelectedRole(null);
      setEditingRole(null);
    } else if (action === 'edit' && id) {
      const role = roles.find(r => r.id.toString() === id);
      if (role) {
        // Fetch detailed role data for editing
        fetchDetailedRoleData(parseInt(id)).then(detailedRole => {
          if (detailedRole) {
            setEditingRole(detailedRole);
          } else {
            // Fallback to list data if detailed fetch fails
            setEditingRole(role);
          }
        });
        setSelectedRole(null);
        setAddingNew(false);
      }
    } else if (action === 'view' && id) {
      const role = roles.find(r => r.id.toString() === id);
      if (role) {
        // Fetch detailed role data for viewing
        fetchDetailedRoleData(parseInt(id)).then(detailedRole => {
          if (detailedRole) {
            setSelectedRole(detailedRole);
          } else {
            // Fallback to list data if detailed fetch fails
            setSelectedRole(role);
          }
        });
        setEditingRole(null);
        setAddingNew(false);
      }
    } else {
      setAddingNew(false);
      setSelectedRole(null);
      setEditingRole(null);
    }
  }, [action, id, roles, fetchDetailedRoleData]);

  const handleDeleteRole = async (roleId?: number) => {
    const targetRole = roleId ? roles.find(r => r.id === roleId) : selectedRole;
    if (!targetRole) return;
    
    const confirmDelete = window.confirm(
      `Are you sure you want to delete the role "${targetRole.name}"?\n\nThis action cannot be undone.`
    );
    
    if (!confirmDelete) return;
    
    try {
      await rolesApi.delete(targetRole.id);
      roleListRef.current?.refresh();
      if (selectedRole?.id === targetRole.id) {
        setSelectedRole(null);
        navigate('/roles');
      }
    } catch (error) {
      alert('Failed to delete role. Please try again.');
    }
  };

  return (
    <div className="dense-dashboard">
      <style>
        {`
          .dashboard-grid {
            height: calc(100vh - 110px);
          }
          .dashboard-section {
            height: 100%;
          }
          .roles-table-section {
            grid-column: 1;
            height: 100%;
          }
          .detail-grid-2col {
            grid-column: 2 / 4;
          }
          .dropdown {
            position: relative;
            display: inline-block;
          }
          
          .dropdown:hover .dropdown-menu {
            display: block;
          }
          
          .dropdown-menu {
            display: none;
            position: absolute;
            top: 100%;
            right: 0;
            background: white;
            border: 1px solid var(--neutral-200);
            border-radius: 4px;
            box-shadow: 0 2px 8px rgba(0,0,0,0.1);
            z-index: 1000;
            min-width: 160px;
          }
          
          .dropdown-item {
            display: block;
            width: 100%;
            padding: 8px 12px;
            border: none;
            background: none;
            text-align: left;
            font-size: 14px;
            cursor: pointer;
            color: var(--neutral-700);
          }
          
          .dropdown-item:hover {
            background: var(--neutral-50);
          }
          
          /* Fix dropdown-toggle icon sizing */
          .dropdown-toggle::after {
            display: none !important;
          }
          
          .dropdown-toggle {
            position: relative;
          }
          
          /* Delete button styling */
          .btn-danger {
            color: #dc2626;
          }
          
          .btn-danger:hover {
            background-color: #fee2e2;
            color: #dc2626;
          }
          
          /* Enhanced header icon buttons */
          .header-stats .btn-icon {
            width: 32px;
            height: 32px;
            padding: 6px;
            display: flex;
            align-items: center;
            justify-content: center;
            border-radius: 4px;
          }
          
          .header-stats .btn-icon svg {
            width: 18px;
            height: 18px;
          }
          
          /* Apply same spacing to roles table as form container */
          .roles-table-section .role-data-grid {
            width: 100%;
            box-sizing: border-box;
            border: none;
          }
          
          /* Make AG-Grid components respect the container with proper spacing */
          .roles-table-section .ag-grid-wrapper {
            width: calc(100% - 16px) !important;
            margin: 8px !important;
            box-sizing: border-box !important;
            border: none !important;
          }
          
          .roles-table-section .ag-root-wrapper,
          .roles-table-section .ag-root,
          .roles-table-section .ag-body-viewport {
            width: 100% !important;
            max-width: 100% !important;
            box-sizing: border-box !important;
            overflow-x: hidden !important;
          }
          
          /* Override AG-Grid CSS variables to remove any shadow effects */
          .roles-table-section .ag-theme-custom {
            --ag-wrapper-border-radius: 0;
            --ag-borders: none;
            --ag-border-color: transparent;
            --ag-wrapper-border: none;
            /* Explicitly disable any shadow variables */
            --ag-card-shadow: none;
            --ag-popup-shadow: none;
            --ag-header-column-separator-color: transparent;
          }
          
          /* Match header styling with subcard headers */
          .roles-table-section .ag-header-cell {
            font-size: 11px !important;
            font-weight: 600 !important;
            color: #24292f !important;
            text-transform: uppercase !important;
            letter-spacing: 0.5px !important;
          }
          
          /* Remove any 3D effects and ensure clean borders */
          .roles-table-section .ag-root-wrapper {
            border: none !important;
            border-radius: 0 !important;
            box-shadow: none !important;
            background: #ffffff !important;
            /* Remove any potential 3D effects */
            filter: none !important;
            transform: none !important;
          }
          
          .roles-table-section .ag-root,
          .roles-table-section .ag-body-viewport,
          .roles-table-section .ag-grid-wrapper {
            background: transparent !important;
            border: none !important;
            box-shadow: none !important;
            border-radius: 0 !important;
            /* Remove any potential 3D effects */
            filter: none !important;
            transform: none !important;
          }
          
          /* Remove border radius from all table cells and headers */
          .roles-table-section .ag-cell,
          .roles-table-section .ag-header-cell {
            border-radius: 0 !important;
          }
        `}
      </style>

      {/* Header */}
      <div className="dashboard-header">
        <div className="header-left">
          <h1>Role Management</h1>
        </div>
        <div className="header-stats">
          <button 
            className="btn-icon"
            onClick={() => navigate('/roles/create')}
            title="Add new role"
            disabled={addingNew || !!editingRole}
          >
            <Plus size={18} />
          </button>
          {selectedRole && !addingNew && !editingRole && (
            <button 
              className="btn-icon"
              onClick={() => navigate(`/roles/edit/${selectedRole.id}`)}
              title="Edit selected role"
            >
              <Edit3 size={18} />
            </button>
          )}
          {selectedRole && !addingNew && !editingRole && (
            <button 
              className="btn-icon btn-danger"
              onClick={() => handleDeleteRole()}
              title="Delete selected role"
            >
              <Trash2 size={18} />
            </button>
          )}

          <Link to="/roles" className="stat-pill">
            <Shield size={14} />
            <span>{roles.length} Roles</span>
          </Link>
          <Link to="/assets" className="stat-pill">
            <Target size={14} />
            <span>Assets</span>
          </Link>
          <Link to="/jobs" className="stat-pill">
            <Settings size={14} />
            <span>Jobs</span>
          </Link>
          <Link to="/monitoring" className="stat-pill">
            <Play size={14} />
            <span>Runs</span>
          </Link>
          <Link to="/ai-chat" className="stat-pill">
            <MessageSquare size={14} />
            <span>AI Assistant</span>
          </Link>
        </div>
      </div>

      {/* 3-column dashboard grid */}
      <div className="dashboard-grid">
        {/* Column 1: Roles Data Grid */}
        <div className="dashboard-section roles-table-section">
          <div className="section-header">
            Roles ({roles.length})
          </div>
          <RoleDataGrid
            className="role-data-grid"
            ref={roleListRef}
            onSelectionChanged={handleSelectionChange}
            onRowDoubleClicked={(role) => {
                navigate(`/roles/edit/${role.id}`);
              }}
              onDataLoaded={handleDataLoaded}
            />
        </div>

        {/* Columns 2-3: Role Details/Form Panel */}
        <div className="dashboard-section detail-grid-2col">
          {addingNew ? (
            <>
              <div className="section-header">
                <span>Create New Role</span>
                <div style={{ display: 'flex', gap: '4px' }}>

                  <button 
                    className="btn-icon btn-ghost"
                    onClick={() => navigate('/roles')}
                    title="Cancel"
                  >
                    <X size={16} />
                  </button>
                </div>
              </div>
              <RoleSpreadsheetForm
                mode="create"
                onCancel={() => navigate('/roles')}
                onSave={async (roleData) => {
                  try {
                    await rolesApi.create(roleData);
                    roleListRef.current?.refresh();
                    navigate('/roles');
                  } catch (error) {
                    alert('Failed to create role. Please try again.');
                  }
                }}
              />
            </>
          ) : editingRole ? (
            <>
              <div className="section-header">
                <span>Edit Role: {editingRole.name}</span>
                <div style={{ display: 'flex', gap: '4px' }}>
                  <button 
                    className="btn-icon btn-ghost"
                    onClick={() => navigate('/roles')}
                    title="Cancel"
                  >
                    <X size={16} />
                  </button>
                </div>
              </div>
              <RoleSpreadsheetForm
                mode="edit"
                role={editingRole}
                onCancel={() => navigate('/roles')}
                onSave={async (roleData) => {
                  try {
                    await rolesApi.update(editingRole.id, roleData);
                    roleListRef.current?.refresh();
                    navigate('/roles');
                  } catch (error) {
                    alert('Failed to update role. Please try again.');
                  }
                }}
              />
            </>
          ) : selectedRole ? (
            <>
              <div className="section-header">
                <span>Role Details: {selectedRole.name || 'Unknown'}</span>
              </div>
              {loadingRoleDetails ? (
                <div className="loading-state">
                  <p>Loading role details...</p>
                </div>
              ) : (
                <RoleSpreadsheetForm
                  mode="view"
                  role={selectedRole}
                  onCancel={() => {}}
                  onSave={() => {}}
                />
              )}
            </>
          ) : loadingRoleDetails ? (
            <>
              <div className="section-header">
                Role Details
              </div>
              <div className="loading-state">
                <p>Loading role details...</p>
              </div>
            </>
          ) : (
            <>
              <div className="section-header">
                Role Details
              </div>
              <div className="compact-content">
                <div className="empty-state">
                  <h3>Select a role</h3>
                  <p>Choose a role from the table to view its details.</p>
                </div>
              </div>
            </>
          )}
        </div>
      </div>

    </div>
  );
};

export default Roles;