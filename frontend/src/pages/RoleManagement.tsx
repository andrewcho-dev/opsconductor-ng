import React, { useState, useEffect } from 'react';
import { useAuth } from '../contexts/AuthContext';
import { hasPermission, PERMISSIONS, PERMISSION_GROUPS, getRoleDisplayName } from '../utils/permissions';
import { Users, Plus, Edit3, Trash2, Shield, Check, X } from 'lucide-react';

interface Role {
  id: number;
  name: string;
  description: string;
  permissions: string[];
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

interface RoleFormData {
  name: string;
  description: string;
  permissions: string[];
  is_active: boolean;
}

const RoleManagement: React.FC = () => {
  const { user: currentUser } = useAuth();
  const [roles, setRoles] = useState<Role[]>([]);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);
  
  const [selectedRole, setSelectedRole] = useState<Role | null>(null);
  const [editingRole, setEditingRole] = useState<Role | null>(null);
  const [addingNew, setAddingNew] = useState(false);
  
  const [newRole, setNewRole] = useState<RoleFormData>({
    name: '',
    description: '',
    permissions: [],
    is_active: true
  });

  const [editRole, setEditRole] = useState<RoleFormData>({
    name: '',
    description: '',
    permissions: [],
    is_active: true
  });

  useEffect(() => {
    fetchRoles();
  }, []);

  const fetchRoles = async () => {
    try {
      const token = localStorage.getItem('access_token');
      const response = await fetch('/api/v1/roles', {
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        }
      });

      if (!response.ok) {
        throw new Error('Failed to fetch roles');
      }

      const data = await response.json();
      
      // Process roles to ensure permissions are always arrays
      const processedRoles = (data.data || []).map((role: any) => {
        let permissions: string[] = [];
        if (Array.isArray(role.permissions)) {
          permissions = role.permissions;
        } else if (typeof role.permissions === 'string') {
          try {
            permissions = JSON.parse(role.permissions);
          } catch (e) {
            console.warn('Failed to parse permissions string for role:', role.name, role.permissions);
            permissions = [];
          }
        }
        return { ...role, permissions };
      });
      
      // Sort roles by permission count (most powerful first)
      const sortedRoles = processedRoles.sort((a: Role, b: Role) => {
        // Wildcard permissions are considered as having infinite permissions
        const aPermCount = a.permissions?.includes('*') ? 999999 : (a.permissions?.length || 0);
        const bPermCount = b.permissions?.includes('*') ? 999999 : (b.permissions?.length || 0);
        return bPermCount - aPermCount;
      });
      setRoles(sortedRoles);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to fetch roles');
    } finally {
      setLoading(false);
    }
  };

  const startAddingNew = () => {
    setAddingNew(true);
    setEditingRole(null);
    setSelectedRole(null);
    setNewRole({
      name: '',
      description: '',
      permissions: [],
      is_active: true
    });
  };

  const cancelAddingNew = () => {
    setAddingNew(false);
    setNewRole({
      name: '',
      description: '',
      permissions: [],
      is_active: true
    });
  };

  const handleEdit = (role: Role) => {
    setEditingRole(role);
    setSelectedRole(role);
    setAddingNew(false);
    
    // Handle permissions - ensure it's always an array
    let permissions: string[] = [];
    if (Array.isArray(role.permissions)) {
      permissions = role.permissions;
    } else if (typeof role.permissions === 'string') {
      try {
        permissions = JSON.parse(role.permissions);
      } catch (e) {
        console.warn('Failed to parse permissions string:', role.permissions);
        permissions = [];
      }
    }
    
    setEditRole({
      name: role.name,
      description: role.description,
      permissions: permissions,
      is_active: role.is_active
    });
  };

  const handleCancelEdit = () => {
    setEditingRole(null);
    setEditRole({
      name: '',
      description: '',
      permissions: [],
      is_active: true
    });
  };

  const saveNewRole = async () => {
    if (!hasPermission(currentUser, PERMISSIONS.ROLES_CREATE)) {
      alert('You don\'t have permission to create roles');
      return;
    }

    if (!newRole.name.trim()) {
      alert('Role name is required');
      return;
    }

    try {
      setSaving(true);
      const token = localStorage.getItem('access_token');
      const response = await fetch('/api/v1/roles', {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify(newRole)
      });

      if (!response.ok) {
        throw new Error('Failed to create role');
      }

      await fetchRoles();
      cancelAddingNew();
    } catch (error) {
      console.error('Failed to create role:', error);
      alert('Failed to create role');
    } finally {
      setSaving(false);
    }
  };

  const handleSaveEdit = async () => {
    if (!editingRole || !hasPermission(currentUser, PERMISSIONS.ROLES_UPDATE)) {
      alert('You don\'t have permission to update roles');
      return;
    }

    if (!editRole.name.trim()) {
      alert('Role name is required');
      return;
    }

    try {
      setSaving(true);
      const token = localStorage.getItem('access_token');
      const response = await fetch(`/api/v1/roles/${editingRole.id}`, {
        method: 'PUT',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify(editRole)
      });

      if (!response.ok) {
        throw new Error('Failed to update role');
      }

      await fetchRoles();
      handleCancelEdit();
    } catch (error) {
      console.error('Failed to update role:', error);
      alert('Failed to update role');
    } finally {
      setSaving(false);
    }
  };

  const handleDelete = async (roleId: number) => {
    if (!hasPermission(currentUser, PERMISSIONS.ROLES_DELETE)) {
      alert('You don\'t have permission to delete roles');
      return;
    }

    if (window.confirm('Delete this role? This action cannot be undone.')) {
      try {
        const token = localStorage.getItem('access_token');
        const response = await fetch(`/api/v1/roles/${roleId}`, {
          method: 'DELETE',
          headers: {
            'Authorization': `Bearer ${token}`,
            'Content-Type': 'application/json'
          }
        });

        if (!response.ok) {
          throw new Error('Failed to delete role');
        }

        await fetchRoles();
        if (selectedRole?.id === roleId) {
          setSelectedRole(null);
        }
        if (editingRole?.id === roleId) {
          setEditingRole(null);
          handleCancelEdit();
        }
      } catch (error) {
        console.error('Failed to delete role:', error);
        alert('Failed to delete role');
      }
    }
  };

  const togglePermission = (permission: string, isEditing: boolean = false) => {
    if (isEditing) {
      setEditRole(prev => ({
        ...prev,
        permissions: prev.permissions.includes(permission)
          ? prev.permissions.filter(p => p !== permission)
          : [...prev.permissions, permission]
      }));
    } else {
      setNewRole(prev => ({
        ...prev,
        permissions: prev.permissions.includes(permission)
          ? prev.permissions.filter(p => p !== permission)
          : [...prev.permissions, permission]
      }));
    }
  };

  const selectAllPermissions = (isEditing: boolean = false) => {
    const allPermissions = Object.values(PERMISSION_GROUPS).flat();
    if (isEditing) {
      setEditRole(prev => ({ ...prev, permissions: allPermissions }));
    } else {
      setNewRole(prev => ({ ...prev, permissions: allPermissions }));
    }
  };

  const clearAllPermissions = (isEditing: boolean = false) => {
    if (isEditing) {
      setEditRole(prev => ({ ...prev, permissions: [] }));
    } else {
      setNewRole(prev => ({ ...prev, permissions: [] }));
    }
  };

  if (loading) {
    return (
      <div className="loading-overlay">
        <div className="loading-spinner"></div>
      </div>
    );
  }

  // Check if user has permission to access role management
  if (!hasPermission(currentUser, PERMISSIONS.ROLES_READ)) {
    return (
      <div className="dense-dashboard">
        <div className="bg-red-50 border border-red-200 rounded-lg p-6 text-center">
          <Shield className="mx-auto h-12 w-12 text-red-400 mb-4" />
          <h2 className="text-xl font-semibold text-red-800 mb-2">Access Denied</h2>
          <p className="text-red-600">You don't have permission to access role management.</p>
        </div>
      </div>
    );
  }

  return (
    <div className="dense-dashboard">
      <style>
        {`
          /* Dashboard-style layout - EXACT MATCH */
          .dense-dashboard {
            padding: 8px 12px;
            max-width: 100%;
            font-size: 13px;
          }
          .dashboard-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 12px;
            padding-bottom: 8px;
            border-bottom: 1px solid var(--neutral-200);
          }
          .header-left h1 {
            font-size: 18px;
            font-weight: 600;
            margin: 0;
            color: var(--neutral-800);
          }
          .dashboard-grid {
            display: grid;
            grid-template-columns: 1fr 1fr 1fr;
            gap: 12px;
            align-items: stretch;
            height: calc(100vh - 110px);
          }
          .dashboard-section {
            background: white;
            border: 1px solid var(--neutral-200);
            border-radius: 6px;
            overflow: hidden;
            display: flex;
            flex-direction: column;
            height: 100%;
          }
          .section-header {
            background: var(--neutral-50);
            padding: 8px 12px;
            font-weight: 600;
            font-size: 13px;
            color: var(--neutral-700);
            border-bottom: 1px solid var(--neutral-200);
            display: flex;
            justify-content: space-between;
            align-items: center;
          }
          .compact-content {
            padding: 0;
            flex: 1;
            display: flex;
            flex-direction: column;
            overflow: auto;
          }
          .table-container {
            flex: 1;
            overflow: auto;
          }
          
          /* Roles table styles */
          .roles-table-section {
            grid-column: 1 / 3;
          }
          .roles-table {
            width: 100%;
            border-collapse: collapse;
            font-size: 12px;
          }
          .roles-table th {
            background: var(--neutral-50);
            padding: 6px 8px;
            text-align: left;
            font-weight: 600;
            color: var(--neutral-700);
            border-bottom: 1px solid var(--neutral-200);
            font-size: 11px;
          }
          .roles-table td {
            padding: 6px 8px;
            border-bottom: 1px solid var(--neutral-100);
            vertical-align: middle;
            font-size: 12px;
          }
          .roles-table tr:hover {
            background: var(--neutral-50);
          }
          .roles-table tr.selected {
            background: var(--primary-blue-light);
            border-left: 3px solid var(--primary-blue);
          }
          .roles-table tr {
            cursor: pointer;
          }
          
          /* Role details panel */
          .role-details {
            padding: 8px;
          }
          .role-details h3 {
            margin: 0 0 12px 0;
            font-size: 14px;
            font-weight: 600;
            color: var(--neutral-800);
          }
          .detail-group {
            margin-bottom: 12px;
          }
          .detail-label {
            font-size: 10px;
            font-weight: 600;
            color: var(--neutral-500);
            margin-bottom: 3px;
            text-transform: uppercase;
            letter-spacing: 0.5px;
          }
          .detail-value {
            font-size: 12px;
            color: var(--neutral-800);
            padding: 6px 0;
            border-bottom: 1px solid var(--neutral-100);
          }
          
          /* Form styles */
          .form-field {
            margin-bottom: 12px;
          }
          .form-label {
            display: block;
            font-size: 10px;
            font-weight: 600;
            color: var(--neutral-500);
            margin-bottom: 3px;
            text-transform: uppercase;
            letter-spacing: 0.5px;
          }
          .form-label.required::after {
            content: ' *';
            color: var(--danger-red);
          }
          .form-input, .form-textarea {
            width: 100%;
            padding: 6px;
            border: 1px solid var(--neutral-300);
            border-radius: 3px;
            font-size: 12px;
          }
          .form-input:focus, .form-textarea:focus {
            outline: none;
            border-color: var(--primary-blue);
            box-shadow: 0 0 0 2px var(--primary-blue-light);
          }
          .form-textarea {
            resize: vertical;
            min-height: 60px;
          }
          
          /* Button styles */
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
          .btn-success {
            color: var(--success-green);
          }
          .btn-success:hover:not(:disabled) {
            color: var(--success-green-dark);
          }
          .btn-danger {
            color: var(--danger-red);
          }
          .btn-danger:hover:not(:disabled) {
            color: var(--danger-red);
          }
          .btn-ghost {
            color: var(--neutral-500);
          }
          .btn-ghost:hover:not(:disabled) {
            color: var(--neutral-700);
          }
          
          .empty-state {
            display: flex;
            flex-direction: column;
            align-items: center;
            justify-content: center;
            height: 100%;
            color: var(--neutral-500);
            text-align: center;
          }
          .empty-state h3 {
            margin: 12px 0 6px 0;
            font-size: 14px;
            color: var(--neutral-700);
          }
          .empty-state p {
            margin: 0 0 12px 0;
            font-size: 12px;
          }

          /* Permissions styles */
          .permissions-section {
            margin-top: 12px;
          }
          .permissions-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 8px;
          }
          .permission-actions {
            display: flex;
            gap: 8px;
          }
          .permission-action {
            background: none;
            border: none;
            cursor: pointer;
            font-size: 10px;
            font-weight: 500;
            padding: 4px 8px;
            border-radius: 3px;
            transition: all 0.15s;
            color: var(--primary-blue);
          }
          .permission-action:hover {
            background: var(--primary-blue-light);
          }
          .permission-action.clear {
            color: var(--danger-red);
          }
          .permission-action.clear:hover {
            background: var(--danger-light);
          }
          .permissions-container {
            max-height: 300px;
            overflow-y: auto;
            border: 1px solid var(--neutral-200);
            border-radius: 4px;
            background: white;
          }
          .permission-group {
            border-bottom: 1px solid var(--neutral-100);
          }
          .permission-group:last-child {
            border-bottom: none;
          }
          .permission-group-header {
            padding: 6px 8px;
            background: var(--neutral-50);
            border-bottom: 1px solid var(--neutral-200);
            font-size: 10px;
            font-weight: 600;
            color: var(--neutral-700);
            text-transform: uppercase;
            letter-spacing: 0.5px;
          }
          .permission-items {
            padding: 6px 8px;
          }
          .permission-item {
            display: flex;
            align-items: center;
            margin-bottom: 4px;
            cursor: pointer;
          }
          .permission-item:last-child {
            margin-bottom: 0;
          }
          .permission-checkbox {
            margin-right: 6px;
            cursor: pointer;
          }
          .permission-label {
            font-size: 11px;
            color: var(--neutral-700);
            cursor: pointer;
          }
          .checkbox-field {
            display: flex;
            align-items: center;
            margin-bottom: 12px;
          }
          .checkbox-text {
            font-size: 11px;
            font-weight: 500;
            color: var(--neutral-700);
            margin-left: 6px;
            text-transform: uppercase;
            letter-spacing: 0.5px;
          }

          /* Status badge */
          .status-badge {
            font-size: 10px;
            padding: 2px 6px;
            border-radius: 10px;
            font-weight: 500;
          }
          .status-badge.active {
            background: var(--success-light);
            color: var(--success);
          }
          .status-badge.inactive {
            background: var(--danger-light);
            color: var(--danger);
          }

          /* Permission count badge */
          .permission-count {
            font-size: 10px;
            padding: 2px 6px;
            border-radius: 10px;
            background: var(--neutral-100);
            color: var(--neutral-700);
            font-weight: 500;
          }

          /* Readonly permissions display */
          .readonly-permissions {
            max-height: 300px;
            overflow-y: auto;
            border: 1px solid var(--neutral-200);
            border-radius: 4px;
            background: white;
          }
          .readonly-permission-group {
            border-bottom: 1px solid var(--neutral-100);
          }
          .readonly-permission-group:last-child {
            border-bottom: none;
          }
          .readonly-permission-items {
            padding: 6px 8px;
          }
          .readonly-permission-item {
            font-size: 11px;
            color: var(--neutral-700);
            margin-bottom: 3px;
            padding-left: 12px;
            position: relative;
          }
          .readonly-permission-item:last-child {
            margin-bottom: 0;
          }
          .readonly-permission-item:before {
            content: '•';
            position: absolute;
            left: 0;
            color: var(--primary-blue);
          }
        `}
      </style>
      
      {/* Dashboard-style header */}
      <div className="dashboard-header">
        <div className="header-left">
          <h1>Role Management</h1>
        </div>
        <div className="header-actions">
          {hasPermission(currentUser, PERMISSIONS.ROLES_CREATE) && (
            <button 
              className="btn-icon btn-success"
              onClick={startAddingNew}
              title="Add new role"
              disabled={addingNew || !!editingRole}
            >
              <Plus size={16} />
            </button>
          )}
        </div>
      </div>

      {/* 3-column dashboard grid */}
      <div className="dashboard-grid">
        {/* Columns 1-2: Roles Table */}
        <div className="dashboard-section roles-table-section">
          <div className="section-header">
            Roles ({roles.length}) • Sorted by permissions (most powerful first)
          </div>
          <div className="compact-content">
            {roles.length === 0 && !addingNew ? (
              <div className="empty-state">
                <h3>No roles found</h3>
                <p>Get started by creating your first role.</p>
                {hasPermission(currentUser, PERMISSIONS.ROLES_CREATE) && (
                  <button 
                    className="btn-icon btn-success"
                    onClick={startAddingNew}
                    title="Create first role"
                  >
                    <Plus size={16} />
                  </button>
                )}
              </div>
            ) : (
              <div className="table-container">
                <table className="roles-table">
                <thead>
                  <tr>
                    <th>Role Name</th>
                    <th>Description</th>
                    <th>Permissions</th>
                    <th>Status</th>
                    <th>Created</th>
                    <th>Actions</th>
                  </tr>
                </thead>
                <tbody>
                  {roles.map((role) => (
                    <tr 
                      key={role.id} 
                      className={selectedRole?.id === role.id ? 'selected' : ''}
                      onClick={() => setSelectedRole(role)}
                    >
                      <td style={{ fontWeight: '600' }}>{role.name}</td>
                      <td style={{ color: '#64748b', fontSize: '11px' }}>
                        {role.description || 'No description'}
                      </td>
                      <td>
                        <span className="permission-count">
                          {role.name === 'admin' || role.permissions?.includes('*') ? 
                            `All Permissions (${Object.values(PERMISSION_GROUPS).flat().length})` : 
                            `${role.permissions?.length || 0} permission${(role.permissions?.length || 0) !== 1 ? 's' : ''}`
                          }
                        </span>
                      </td>
                      <td>
                        <span className={`status-badge ${role.is_active ? 'active' : 'inactive'}`}>
                          {role.is_active ? 'Active' : 'Inactive'}
                        </span>
                      </td>
                      <td style={{ color: '#64748b', fontSize: '12px' }}>
                        {new Date(role.created_at).toLocaleDateString()}
                      </td>
                      <td>
                        <div style={{ display: 'flex', gap: '4px' }}>
                          {hasPermission(currentUser, PERMISSIONS.ROLES_UPDATE) && role.name !== 'admin' && (
                            <button 
                              className="btn-icon btn-ghost"
                              onClick={(e) => {
                                e.stopPropagation();
                                handleEdit(role);
                              }}
                              title="Edit role"
                            >
                              <Edit3 size={16} />
                            </button>
                          )}
                          {hasPermission(currentUser, PERMISSIONS.ROLES_DELETE) && role.name !== 'admin' && (
                            <button 
                              className="btn-icon btn-danger"
                              onClick={(e) => {
                                e.stopPropagation();
                                handleDelete(role.id);
                              }}
                              title="Delete role"
                            >
                              <Trash2 size={16} />
                            </button>
                          )}
                          {role.name === 'admin' && (
                            <span style={{ fontSize: '10px', color: 'var(--neutral-500)', fontStyle: 'italic', padding: '4px' }}>
                              System Role
                            </span>
                          )}
                        </div>
                      </td>
                    </tr>
                  ))}
                </tbody>
                </table>
              </div>
            )}
          </div>
        </div>

        {/* Column 3: Role Details/Form Panel */}
        <div className="dashboard-section">
          {addingNew || editingRole ? (
            <>
              <div className="section-header">
                <span>{editingRole ? `Edit Role: ${editingRole.name}` : 'Create New Role'}</span>
                <div style={{ display: 'flex', gap: '4px' }}>
                  <button 
                    className="btn-icon btn-success"
                    onClick={editingRole ? handleSaveEdit : saveNewRole}
                    disabled={saving}
                    title={editingRole ? "Update Role" : "Create Role"}
                  >
                    <Check size={16} />
                  </button>
                  <button 
                    className="btn-icon btn-ghost"
                    onClick={editingRole ? handleCancelEdit : cancelAddingNew}
                    disabled={saving}
                    title="Cancel"
                  >
                    <X size={16} />
                  </button>
                </div>
              </div>
              <div className="compact-content role-details">
                <div className="form-field">
                  <label className="form-label required">Role Name</label>
                  <input
                    type="text"
                    className="form-input"
                    value={editingRole ? editRole.name : newRole.name}
                    onChange={(e) => editingRole 
                      ? setEditRole(prev => ({ ...prev, name: e.target.value }))
                      : setNewRole(prev => ({ ...prev, name: e.target.value }))
                    }
                    placeholder="Enter role name"
                  />
                </div>

                <div className="form-field">
                  <label className="form-label">Description</label>
                  <textarea
                    className="form-textarea"
                    value={editingRole ? editRole.description : newRole.description}
                    onChange={(e) => editingRole 
                      ? setEditRole(prev => ({ ...prev, description: e.target.value }))
                      : setNewRole(prev => ({ ...prev, description: e.target.value }))
                    }
                    placeholder="Enter role description"
                    rows={3}
                  />
                </div>

                <div className="checkbox-field">
                  <input
                    type="checkbox"
                    className="permission-checkbox"
                    checked={editingRole ? editRole.is_active : newRole.is_active}
                    onChange={(e) => editingRole 
                      ? setEditRole(prev => ({ ...prev, is_active: e.target.checked }))
                      : setNewRole(prev => ({ ...prev, is_active: e.target.checked }))
                    }
                  />
                  <span className="checkbox-text">Active</span>
                </div>

                <div className="permissions-section">
                  <div className="permissions-header">
                    <label className="form-label">Permissions</label>
                    <div className="permission-actions">
                      <button
                        type="button"
                        onClick={() => selectAllPermissions(!!editingRole)}
                        className="permission-action"
                      >
                        Select All
                      </button>
                      <button
                        type="button"
                        onClick={() => clearAllPermissions(!!editingRole)}
                        className="permission-action clear"
                      >
                        Clear All
                      </button>
                    </div>
                  </div>

                  <div className="permissions-container">
                    {Object.entries(PERMISSION_GROUPS).map(([groupName, permissions]) => (
                      <div key={groupName} className="permission-group">
                        <div className="permission-group-header">
                          {groupName.replace('_', ' ').toLowerCase().replace(/\b\w/g, l => l.toUpperCase())}
                        </div>
                        <div className="permission-items">
                          {permissions.map((permission) => {
                            const currentPermissions = editingRole ? editRole.permissions : newRole.permissions;
                            return (
                              <label key={permission} className="permission-item">
                                <input
                                  type="checkbox"
                                  checked={currentPermissions.includes(permission)}
                                  onChange={() => togglePermission(permission, !!editingRole)}
                                  className="permission-checkbox"
                                />
                                <span className="permission-label">
                                  {permission.replace(':', ' ').replace(/\b\w/g, (l: string) => l.toUpperCase())}
                                </span>
                              </label>
                            );
                          })}
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              </div>
            </>
          ) : selectedRole ? (
            <>
              <div className="section-header">
                Role Details: {selectedRole.name}
                {selectedRole.name === 'admin' && (
                  <span style={{ fontSize: '10px', color: 'var(--warning)', fontWeight: '500', marginLeft: '8px', padding: '2px 6px', background: 'var(--warning-light)', borderRadius: '10px' }}>
                    SYSTEM ROLE
                  </span>
                )}
              </div>
              <div className="compact-content role-details">
                <div className="detail-group">
                  <div className="detail-label">Role Name</div>
                  <div className="detail-value" style={{ fontWeight: '600' }}>
                    {selectedRole.name}
                  </div>
                </div>

                <div className="detail-group">
                  <div className="detail-label">Description</div>
                  <div className="detail-value">
                    {selectedRole.description || 'No description provided'}
                  </div>
                </div>

                <div className="detail-group">
                  <div className="detail-label">Status</div>
                  <div className="detail-value">
                    <span className={`status-badge ${selectedRole.is_active ? 'active' : 'inactive'}`}>
                      {selectedRole.is_active ? 'Active' : 'Inactive'}
                    </span>
                  </div>
                </div>

                <div className="permissions-section">
                  <div className="permissions-header">
                    <label className="form-label">
                      Permissions ({selectedRole.name === 'admin' || selectedRole.permissions?.includes('*') ? 
                        `All ${Object.values(PERMISSION_GROUPS).flat().length} Permissions` : 
                        selectedRole.permissions?.length || 0})
                    </label>
                  </div>

                  <div className="readonly-permissions">
                    {Object.entries(PERMISSION_GROUPS).map(([groupName, permissions]) => {
                      const rolePermissions = selectedRole.permissions || [];
                      // For admin role or wildcard, show all permissions in each group
                      const isAdminOrWildcard = selectedRole.name === 'admin' || rolePermissions.includes('*');
                      const groupPermissions = isAdminOrWildcard ? permissions : (permissions as unknown as string[]).filter(p => rolePermissions.includes(p));
                      
                      if (groupPermissions.length === 0) return null;
                      
                      return (
                        <div key={groupName} className="readonly-permission-group">
                          <div className="permission-group-header">
                            {groupName.replace('_', ' ').toLowerCase().replace(/\b\w/g, (l: string) => l.toUpperCase())} ({groupPermissions.length})
                            {isAdminOrWildcard && (
                              <span style={{ fontSize: '9px', color: 'var(--success)', fontWeight: '500', marginLeft: '6px' }}>
                                (All)
                              </span>
                            )}
                          </div>
                          <div className="readonly-permission-items">
                            {groupPermissions.map((permission: string) => (
                              <div key={permission} className="readonly-permission-item">
                                {permission.replace(':', ' ').replace(/\b\w/g, (l: string) => l.toUpperCase())}
                              </div>
                            ))}
                          </div>
                        </div>
                      );
                    })}
                  </div>
                </div>

                <div style={{ marginTop: '16px', fontSize: '10px', color: 'var(--neutral-500)', borderTop: '1px solid var(--neutral-200)', paddingTop: '8px' }}>
                  Created: {new Date(selectedRole.created_at).toLocaleDateString()}
                  {selectedRole.updated_at && (
                    <> • Updated: {new Date(selectedRole.updated_at).toLocaleDateString()}</>
                  )}
                </div>
              </div>
            </>
          ) : (
            <div className="empty-state">
              <Shield size={32} />
              <h3>Select a Role</h3>
              <p>Choose a role from the table to view its details and permissions</p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default RoleManagement;