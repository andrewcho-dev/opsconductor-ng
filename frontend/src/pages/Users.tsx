import React, { useState, useEffect } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import { Plus, Trash2, Check, X, Edit3, Shield } from 'lucide-react';
import { userApi, rolesApi } from '../services/api';
import { User, UserCreate } from '../types';
import { useAuth } from '../contexts/AuthContext';
import { hasPermission, PERMISSIONS } from '../utils/permissions';




interface NewUserState {
  email: string;
  username: string;
  password: string;
  confirmPassword: string;
  role: string;
  first_name: string;
  last_name: string;
  telephone: string;
  title: string;
}

interface EditUserState {
  email: string;
  username: string;
  password: string;
  confirmPassword: string;
  role: string;
  first_name: string;
  last_name: string;
  telephone: string;
  title: string;
}

const Users: React.FC = () => {
  const navigate = useNavigate();
  const { action, id } = useParams<{ action?: string; id?: string }>();
  const { user: currentUser } = useAuth();
  const [users, setUsers] = useState<User[]>([]);
  const [roles, setRoles] = useState<Array<{id: number, name: string, description: string}>>([]);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);

  const [addingNew, setAddingNew] = useState(false);
  const [editingUser, setEditingUser] = useState<User | null>(null);
  const [selectedUser, setSelectedUser] = useState<User | null>(null);
  const [newUser, setNewUser] = useState<NewUserState>({
    email: '',
    username: '',
    password: '',
    confirmPassword: '',
    role: '',
    first_name: '',
    last_name: '',
    telephone: '',
    title: ''
  });

  const [editUser, setEditUser] = useState<EditUserState>({
    email: '',
    username: '',
    password: '',
    confirmPassword: '',
    role: '',
    first_name: '',
    last_name: '',
    telephone: '',
    title: ''
  });

  useEffect(() => {
    fetchUsers();
    fetchRoles();
  }, []);

  const fetchUsers = async () => {
    try {
      const response = await userApi.list();
      setUsers(response.data || []);
    } catch (error) {
      console.error('Failed to fetch users:', error);
      setUsers([]);
    } finally {
      setLoading(false);
    }
  };

  const fetchRoles = async () => {
    try {
      const response = await rolesApi.list();
      if (response.data.success) {
        setRoles(response.data.data || []);
      }
    } catch (error) {
      console.error('Failed to fetch roles:', error);
      // Fallback to default roles if API fails
      setRoles([
        { id: 1, name: 'admin', description: 'System Administrator' },
        { id: 2, name: 'operator', description: 'System Operator' },
        { id: 3, name: 'viewer', description: 'Read-only User' }
      ]);
    }
  };

  const startAddingNew = () => {
    setAddingNew(true);
    setEditingUser(null);
    setSelectedUser(null);
    // Set default role to viewer if available
    const defaultRole = roles.find(r => r.name === 'viewer') || roles[0];
    setNewUser(prev => ({ ...prev, role: defaultRole?.name || '' }));
  };

  const handleEdit = (user: User) => {
    setEditingUser(user);
    setEditUser({
      email: user.email,
      username: user.username,
      password: '',
      confirmPassword: '',
      role: user.role,
      first_name: user.first_name || '',
      last_name: user.last_name || '',
      telephone: user.telephone || '',
      title: user.title || ''
    });
    setAddingNew(false);
    setSelectedUser(null);
  };

  const handleCancelEdit = () => {
    setEditingUser(null);
    setEditUser({
      email: '',
      username: '',
      password: '',
      confirmPassword: '',
      role: '',
      first_name: '',
      last_name: '',
      telephone: '',
      title: ''
    });
  };

  const handleSaveEdit = async () => {
    if (!editingUser) return;

    // Validation
    if (!editUser.email.trim()) {
      alert('Email is required');
      return;
    }
    if (!editUser.username.trim()) {
      alert('Username is required');
      return;
    }
    if (editUser.password && editUser.password !== editUser.confirmPassword) {
      alert('Passwords do not match');
      return;
    }
    if (editUser.password && editUser.password.length < 6) {
      alert('Password must be at least 6 characters long');
      return;
    }
    if (!editUser.role.trim()) {
      alert('Role is required');
      return;
    }

    try {
      setSaving(true);
      const updateData: any = {
        email: editUser.email,
        username: editUser.username,
        role: editUser.role,
        first_name: editUser.first_name,
        last_name: editUser.last_name,
        telephone: editUser.telephone,
        title: editUser.title
      };
      
      // Only include password if it was changed
      if (editUser.password) {
        updateData.password = editUser.password;
      }
      
      await userApi.update(editingUser.id, updateData);
      await fetchUsers();
      handleCancelEdit();
    } catch (error) {
      console.error('Failed to update user:', error);
      alert('Failed to update user');
    } finally {
      setSaving(false);
    }
  };



  const cancelAddingNew = () => {
    setAddingNew(false);
    setNewUser({
      email: '',
      username: '',
      password: '',
      confirmPassword: '',
      role: '',
      first_name: '',
      last_name: '',
      telephone: '',
      title: ''
    });
  };

  const saveNewUser = async () => {
    if (!newUser.email.trim()) {
      alert('Email is required');
      return;
    }
    if (!newUser.username.trim()) {
      alert('Username is required');
      return;
    }
    if (!newUser.password) {
      alert('Password is required');
      return;
    }
    if (newUser.password !== newUser.confirmPassword) {
      alert('Passwords do not match');
      return;
    }
    if (newUser.password.length < 6) {
      alert('Password must be at least 6 characters long');
      return;
    }
    if (!newUser.role.trim()) {
      alert('Role is required');
      return;
    }

    try {
      setSaving(true);
      const userData: UserCreate = {
        email: newUser.email,
        username: newUser.username,
        password: newUser.password,
        role: newUser.role as any,
        first_name: newUser.first_name,
        last_name: newUser.last_name,
        telephone: newUser.telephone,
        title: newUser.title
      };
      
      await userApi.create(userData);
      await fetchUsers();
      cancelAddingNew();
    } catch (error) {
      console.error('Failed to create user:', error);
      alert('Failed to create user');
    } finally {
      setSaving(false);
    }
  };

  const handleDelete = async (userId: number) => {
    if (window.confirm('Delete this user? This action cannot be undone.')) {
      try {
        await userApi.delete(userId);
        fetchUsers();
        if (selectedUser?.id === userId) {
          setSelectedUser(null);
        }
      } catch (error) {
        console.error('Failed to delete user:', error);
      }
    }
  };

  const handleRoleChange = async (userId: number, role: string) => {
    try {
      await userApi.assignRole(userId, role);
      fetchUsers();
      if (selectedUser?.id === userId) {
        setSelectedUser({...selectedUser, role: role as any});
      }
    } catch (error) {
      console.error('Failed to update role:', error);
    }
  };





  if (loading) {
    return (
      <div className="loading-overlay">
        <div className="loading-spinner"></div>
      </div>
    );
  }

  // Check if user has permission to access user management
  if (!hasPermission(currentUser, PERMISSIONS.USERS_READ)) {
    return (
      <div className="dense-dashboard">
        <div className="bg-red-50 border border-red-200 rounded-lg p-6 text-center">
          <Shield className="mx-auto h-12 w-12 text-red-400 mb-4" />
          <h2 className="text-xl font-semibold text-red-800 mb-2">Access Denied</h2>
          <p className="text-red-600">You don't have permission to access user management.</p>
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
          
          /* Users table styles */
          .users-table-section {
            grid-column: 1 / 3;
          }
          .users-table {
            width: 100%;
            border-collapse: collapse;
            font-size: 12px;
          }
          .users-table th {
            background: var(--neutral-50);
            padding: 6px 8px;
            text-align: left;
            font-weight: 600;
            color: var(--neutral-700);
            border-bottom: 1px solid var(--neutral-200);
            font-size: 11px;
          }
          .users-table td {
            padding: 6px 8px;
            border-bottom: 1px solid var(--neutral-100);
            vertical-align: middle;
            font-size: 12px;
          }
          .users-table tr:hover {
            background: var(--neutral-50);
          }
          .users-table tr.selected {
            background: var(--primary-blue-light);
            border-left: 3px solid var(--primary-blue);
          }
          .users-table tr {
            cursor: pointer;
          }
          
          /* User details panel */
          .user-details {
            padding: 8px;
          }
          .user-details h3 {
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
          .detail-value.editable {
            cursor: pointer;
            transition: background 0.2s;
          }
          .detail-value.editable:hover {
            background: var(--neutral-50);
            padding: 6px;
            margin: 0 -6px;
            border-radius: 3px;
          }
          
          /* Form styles */
          .detail-input {
            width: 100%;
            padding: 6px;
            border: 1px solid var(--neutral-300);
            border-radius: 3px;
            font-size: 12px;
          }
          .detail-input:focus {
            outline: none;
            border-color: var(--primary-blue);
            box-shadow: 0 0 0 2px var(--primary-blue-light);
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
          
          .action-buttons {
            display: flex;
            gap: 4px;
            margin-top: 12px;
            padding-top: 12px;
            border-top: 1px solid var(--neutral-200);
          }
          
          .empty-state {
            display: flex;
            flex-direction: column;
            align-items: center;
            justify-content: center;
            height: 150px;
            color: var(--neutral-500);
            text-align: center;
          }
          .empty-state h3 {
            margin: 0 0 6px 0;
            font-size: 14px;
            font-weight: 600;
          }
          .empty-state p {
            margin: 0 0 12px 0;
            font-size: 12px;
          }
          
          /* Form styles */
          .form-field {
            margin-bottom: 16px;
          }
          .form-label {
            display: block;
            font-size: 12px;
            font-weight: 600;
            color: var(--neutral-700);
            margin-bottom: 4px;
          }
          .form-label.required::after {
            content: " *";
            color: var(--danger-red);
          }
          .form-input {
            width: 100%;
            padding: 8px 12px;
            border: 1px solid var(--neutral-300);
            border-radius: 4px;
            font-size: 13px;
            transition: border-color 0.2s;
          }
          .form-input:focus {
            outline: none;
            border-color: var(--primary-blue);
            box-shadow: 0 0 0 2px var(--primary-blue-light);
          }
          
          /* Three-column layout */
          .three-column-grid {
            display: grid;
            grid-template-columns: 1fr 1fr 1fr;
            gap: 16px;
          }
          
          /* User details styling to match credentials */
          .user-details {
            padding: 8px;
          }
          .user-details h3 {
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
          
          /* Form styling to match credentials */
          .form-field {
            margin-bottom: 16px;
          }
          
          .form-label {
            display: block;
            font-size: 12px;
            font-weight: 600;
            color: var(--neutral-700);
            margin-bottom: 4px;
          }
          
          .form-label.required::after {
            content: ' *';
            color: var(--red-600);
          }
          
          .form-input {
            width: 100%;
            padding: 8px 12px;
            border: 1px solid var(--neutral-300);
            border-radius: 4px;
            font-size: 14px;
            color: var(--neutral-900);
          }
          
          .form-input:focus {
            outline: none;
            border-color: var(--primary-blue);
            box-shadow: 0 0 0 2px var(--blue-100);
          }
          
          .form-input[readonly], .form-input:disabled {
            background-color: var(--neutral-50);
            color: var(--neutral-700);
            cursor: default;
          }
        `}
      </style>
      
      {/* Dashboard-style header */}
      <div className="dashboard-header">
        <div className="header-left">
          <h1>User Management</h1>
        </div>
        <div className="header-actions">
          {hasPermission(currentUser, PERMISSIONS.USERS_CREATE) && (
            <button 
              className="btn-icon btn-success"
              onClick={startAddingNew}
              title="Add new user"
              disabled={addingNew || !!editingUser}
            >
              <Plus size={16} />
            </button>
          )}
        </div>
      </div>

      {/* 3-column dashboard grid */}
      <div className="dashboard-grid">
        {/* Columns 1-2: Users Table */}
        <div className="dashboard-section users-table-section">
          <div className="section-header">
            Users ({users.length})
          </div>
          <div className="compact-content">
            {users.length === 0 && !addingNew ? (
              <div className="empty-state">
                <h3>No users found</h3>
                <p>Get started by creating your first user account.</p>
                {hasPermission(currentUser, PERMISSIONS.USERS_CREATE) && (
                  <button 
                    className="btn-icon btn-success"
                    onClick={startAddingNew}
                    title="Create first user"
                  >
                    <Plus size={16} />
                  </button>
                )}
              </div>
            ) : (
              <div className="table-container">
                <table className="users-table">
                <thead>
                  <tr>
                    <th>Username</th>
                    <th>Email</th>
                    <th>Name</th>
                    <th>Role</th>
                    <th>Created</th>
                    <th>Actions</th>
                  </tr>
                </thead>
                <tbody>
                  {users.map((user) => (
                    <tr 
                      key={user.id} 
                      className={selectedUser?.id === user.id ? 'selected' : ''}
                      onClick={() => setSelectedUser(user)}
                    >
                      <td>{user.username}</td>
                      <td>{user.email}</td>
                      <td>{user.first_name} {user.last_name}</td>
                      <td>
                        <select 
                          value={user.role || ''} 
                          onChange={(e) => {
                            e.stopPropagation();
                            handleRoleChange(user.id, e.target.value);
                          }}
                          style={{ border: 'none', background: 'transparent', fontSize: '13px' }}
                        >
                          {roles.map(role => (
                            <option key={role.id} value={role.name}>
                              {role.name.charAt(0).toUpperCase() + role.name.slice(1)}
                            </option>
                          ))}
                        </select>
                      </td>
                      <td style={{ color: '#64748b', fontSize: '12px' }}>
                        {new Date(user.created_at).toLocaleDateString()}
                      </td>
                      <td>
                        <div style={{ display: 'flex', gap: '4px' }}>
                          {hasPermission(currentUser, PERMISSIONS.USERS_UPDATE) && (
                            <button 
                              className="btn-icon btn-ghost"
                              onClick={(e) => {
                                e.stopPropagation();
                                handleEdit(user);
                              }}
                              title="Edit user details"
                            >
                              <Edit3 size={16} />
                            </button>
                          )}
                          {hasPermission(currentUser, PERMISSIONS.USERS_DELETE) && (
                            <button 
                              className="btn-icon btn-danger"
                              onClick={(e) => {
                                e.stopPropagation();
                                handleDelete(user.id);
                              }}
                              title="Delete user"
                            >
                              <Trash2 size={16} />
                            </button>
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

        {/* Column 3: User Details/Form Panel */}
        <div className="dashboard-section">
          {addingNew || editingUser ? (
            <>
              <div className="section-header">
                <span>{editingUser ? `Edit User: ${editingUser.username}` : 'Create New User'}</span>
                <div style={{ display: 'flex', gap: '4px' }}>
                  <button 
                    className="btn-icon btn-success"
                    onClick={editingUser ? handleSaveEdit : saveNewUser}
                    disabled={saving}
                    title={editingUser ? "Update User" : "Create User"}
                  >
                    <Check size={16} />
                  </button>
                  <button 
                    className="btn-icon btn-ghost"
                    onClick={editingUser ? handleCancelEdit : cancelAddingNew}
                    disabled={saving}
                    title="Cancel"
                  >
                    <X size={16} />
                  </button>
                </div>
              </div>
              <div className="compact-content user-details">
                <div className="three-column-grid">
                  {/* Row 1: username, firstname, lastname */}
                  <div className="form-field">
                    <label className="form-label required">Username</label>
                    <input
                      type="text"
                      className="form-input"
                      value={editingUser ? editUser.username : newUser.username}
                      onChange={(e) => editingUser 
                        ? setEditUser(prev => ({ ...prev, username: e.target.value }))
                        : setNewUser(prev => ({ ...prev, username: e.target.value }))
                      }
                    />
                  </div>

                  <div className="form-field">
                    <label className="form-label">First Name</label>
                    <input
                      type="text"
                      className="form-input"
                      value={editingUser ? editUser.first_name : newUser.first_name}
                      onChange={(e) => editingUser 
                        ? setEditUser(prev => ({ ...prev, first_name: e.target.value }))
                        : setNewUser(prev => ({ ...prev, first_name: e.target.value }))
                      }
                    />
                  </div>

                  <div className="form-field">
                    <label className="form-label">Last Name</label>
                    <input
                      type="text"
                      className="form-input"
                      value={editingUser ? editUser.last_name : newUser.last_name}
                      onChange={(e) => editingUser 
                        ? setEditUser(prev => ({ ...prev, last_name: e.target.value }))
                        : setNewUser(prev => ({ ...prev, last_name: e.target.value }))
                      }
                    />
                  </div>

                  {/* Row 2: role, title, telephone */}
                  <div className="form-field">
                    <label className="form-label">Role</label>
                    <select
                      className="form-input"
                      value={editingUser ? editUser.role : newUser.role}
                      onChange={(e) => editingUser 
                        ? setEditUser(prev => ({ ...prev, role: e.target.value }))
                        : setNewUser(prev => ({ ...prev, role: e.target.value }))
                      }
                    >
                      <option value="">Select a role...</option>
                      {roles.map(role => (
                        <option key={role.id} value={role.name}>
                          {role.name.charAt(0).toUpperCase() + role.name.slice(1)} - {role.description}
                        </option>
                      ))}
                    </select>
                  </div>

                  <div className="form-field">
                    <label className="form-label">Title</label>
                    <input
                      type="text"
                      className="form-input"
                      value={editingUser ? editUser.title : newUser.title}
                      onChange={(e) => editingUser 
                        ? setEditUser(prev => ({ ...prev, title: e.target.value }))
                        : setNewUser(prev => ({ ...prev, title: e.target.value }))
                      }
                    />
                  </div>

                  <div className="form-field">
                    <label className="form-label">Telephone</label>
                    <input
                      type="text"
                      className="form-input"
                      value={editingUser ? editUser.telephone : newUser.telephone}
                      onChange={(e) => editingUser 
                        ? setEditUser(prev => ({ ...prev, telephone: e.target.value }))
                        : setNewUser(prev => ({ ...prev, telephone: e.target.value }))
                      }
                    />
                  </div>

                  {/* Row 3: password, confirm password, email */}
                  <div className="form-field">
                    <label className="form-label required">Password</label>
                    <input
                      type="password"
                      className="form-input"
                      placeholder={editingUser ? "Leave blank to keep current password" : "Enter password"}
                      value={editingUser ? editUser.password : newUser.password}
                      onChange={(e) => editingUser 
                        ? setEditUser(prev => ({ ...prev, password: e.target.value }))
                        : setNewUser(prev => ({ ...prev, password: e.target.value }))
                      }
                    />
                  </div>

                  <div className="form-field">
                    <label className="form-label required">Confirm Password</label>
                    <input
                      type="password"
                      className="form-input"
                      placeholder="Confirm password"
                      value={editingUser ? editUser.confirmPassword : newUser.confirmPassword}
                      onChange={(e) => editingUser 
                        ? setEditUser(prev => ({ ...prev, confirmPassword: e.target.value }))
                        : setNewUser(prev => ({ ...prev, confirmPassword: e.target.value }))
                      }
                    />
                  </div>

                  <div className="form-field">
                    <label className="form-label required">Email</label>
                    <input
                      type="email"
                      className="form-input"
                      value={editingUser ? editUser.email : newUser.email}
                      onChange={(e) => editingUser 
                        ? setEditUser(prev => ({ ...prev, email: e.target.value }))
                        : setNewUser(prev => ({ ...prev, email: e.target.value }))
                      }
                    />
                  </div>
                </div>
              </div>
            </>
          ) : selectedUser ? (
            <>
              <div className="section-header">
                User Details
              </div>
              <div className="compact-content user-details">
                <div className="three-column-grid">
                  {/* Row 1: username, firstname, lastname */}
                  <div className="form-field">
                    <label className="form-label required">Username</label>
                    <input
                      type="text"
                      className="form-input"
                      value={selectedUser.username}
                      readOnly
                    />
                  </div>

                  <div className="form-field">
                    <label className="form-label">First Name</label>
                    <input
                      type="text"
                      className="form-input"
                      value={selectedUser.first_name || ''}
                      readOnly
                    />
                  </div>

                  <div className="form-field">
                    <label className="form-label">Last Name</label>
                    <input
                      type="text"
                      className="form-input"
                      value={selectedUser.last_name || ''}
                      readOnly
                    />
                  </div>

                  {/* Row 2: role, title, telephone */}
                  <div className="form-field">
                    <label className="form-label">Role</label>
                    <select className="form-input" value={selectedUser.role || ''} disabled>
                      {roles.map(role => (
                        <option key={role.id} value={role.name}>
                          {role.name.charAt(0).toUpperCase() + role.name.slice(1)}
                        </option>
                      ))}
                    </select>
                  </div>

                  <div className="form-field">
                    <label className="form-label">Title</label>
                    <input
                      type="text"
                      className="form-input"
                      value={selectedUser.title || ''}
                      readOnly
                    />
                  </div>

                  <div className="form-field">
                    <label className="form-label">Telephone</label>
                    <input
                      type="text"
                      className="form-input"
                      value={selectedUser.telephone || ''}
                      readOnly
                    />
                  </div>

                  {/* Row 3: password, confirm password, email */}
                  <div className="form-field">
                    <label className="form-label required">Password</label>
                    <input
                      type="password"
                      className="form-input"
                      value="••••••••"
                      readOnly
                    />
                  </div>

                  <div className="form-field">
                    <label className="form-label">Created</label>
                    <input
                      type="text"
                      className="form-input"
                      value={new Date(selectedUser.created_at).toLocaleString()}
                      readOnly
                    />
                  </div>

                  <div className="form-field">
                    <label className="form-label required">Email</label>
                    <input
                      type="email"
                      className="form-input"
                      value={selectedUser.email}
                      readOnly
                    />
                  </div>
                </div>
              </div>
            </>
          ) : (
            <>
              <div className="section-header">
                Select User
              </div>
              <div className="compact-content">
                <div className="empty-state">
                  <p>Select a user from the table to view details</p>
                </div>
              </div>
            </>
          )}
        </div>
      </div>
    </div>
  );
};

export default Users;