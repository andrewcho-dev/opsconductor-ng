import React, { useState, useEffect } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import { Plus, Trash2, Check, X, Edit3 } from 'lucide-react';
import { userApi } from '../services/api';
import { User, UserCreate } from '../types';

interface EditingState {
  userId: number;
  field: 'username' | 'email' | 'role' | 'first_name' | 'last_name' | 'telephone' | 'title' | 'password';
  value: string;
  confirmPassword?: string;
}


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

const Users: React.FC = () => {
  const navigate = useNavigate();
  const { action, id } = useParams<{ action?: string; id?: string }>();
  const [users, setUsers] = useState<User[]>([]);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [editing, setEditing] = useState<EditingState | null>(null);

  const [addingNew, setAddingNew] = useState(false);
  const [selectedUser, setSelectedUser] = useState<User | null>(null);
  const [newUser, setNewUser] = useState<NewUserState>({
    email: '',
    username: '',
    password: '',
    confirmPassword: '',
    role: 'viewer',
    first_name: '',
    last_name: '',
    telephone: '',
    title: ''
  });

  useEffect(() => {
    fetchUsers();
  }, []);

  const fetchUsers = async () => {
    try {
      const response = await userApi.list();
      setUsers(response.users || []);
    } catch (error) {
      console.error('Failed to fetch users:', error);
      setUsers([]);
    } finally {
      setLoading(false);
    }
  };

  const startAddingNew = () => {
    setAddingNew(true);
    setEditing(null);
  };

  const startEditing = (userId: number, field: 'username' | 'email' | 'role' | 'first_name' | 'last_name' | 'telephone' | 'title' | 'password', currentValue: string = '') => {
    setEditing({
      userId,
      field,
      value: field === 'password' ? '' : currentValue,
      confirmPassword: field === 'password' ? '' : undefined
    });
    setAddingNew(false);
  };

  const cancelEditing = () => {
    setEditing(null);
  };

  const saveEdit = async () => {
    if (!editing) return;

    if (editing.field === 'password') {
      if (!editing.value) {
        alert('Password cannot be empty');
        return;
      }
      if (editing.value !== editing.confirmPassword) {
        alert('Passwords do not match');
        return;
      }
      if (editing.value.length < 6) {
        alert('Password must be at least 6 characters long');
        return;
      }
    }

    if ((editing.field === 'email' || editing.field === 'username') && !editing.value.trim()) {
      alert(`${editing.field} cannot be empty`);
      return;
    }

    try {
      setSaving(true);
      await userApi.update(editing.userId, { [editing.field]: editing.value });
      await fetchUsers();
      
      if (selectedUser?.id === editing.userId) {
        setSelectedUser({...selectedUser, [editing.field]: editing.value});
      }
      
      setEditing(null);
    } catch (error) {
      console.error(`Failed to update ${editing.field}:`, error);
      alert(`Failed to update ${editing.field}`);
    } finally {
      setSaving(false);
    }
  };

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter') {
      saveEdit();
    } else if (e.key === 'Escape') {
      cancelEditing();
    }
  };

  const cancelAddingNew = () => {
    setAddingNew(false);
    setNewUser({
      email: '',
      username: '',
      password: '',
      confirmPassword: '',
      role: 'viewer',
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



  const handleNewUserKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter') {
      saveNewUser();
    } else if (e.key === 'Escape') {
      cancelAddingNew();
    }
  };

  if (loading) {
    return (
      <div className="loading-overlay">
        <div className="loading-spinner"></div>
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
        `}
      </style>
      
      {/* Dashboard-style header */}
      <div className="dashboard-header">
        <div className="header-left">
          <h1>User Management</h1>
        </div>
        <div className="header-actions">
          <button 
            className="btn-icon btn-success"
            onClick={startAddingNew}
            title="Add new user"
            disabled={addingNew}
          >
            <Plus size={16} />
          </button>
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
                <button 
                  className="btn-icon btn-success"
                  onClick={startAddingNew}
                  title="Create first user"
                >
                  <Plus size={16} />
                </button>
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
                  {/* New User Row */}
                  {addingNew && (
                    <tr style={{ background: '#f0f9ff', border: '2px solid #10b981' }}>
                      <td>
                        <input
                          type="text"
                          value={newUser.username}
                          onChange={(e) => setNewUser({...newUser, username: e.target.value})}
                          onKeyDown={handleNewUserKeyPress}
                          placeholder="Username"
                          style={{ width: '100%', border: 'none', background: 'transparent', padding: '4px' }}
                          autoFocus
                        />
                      </td>
                      <td>
                        <input
                          type="email"
                          value={newUser.email}
                          onChange={(e) => setNewUser({...newUser, email: e.target.value})}
                          onKeyDown={handleNewUserKeyPress}
                          placeholder="Email"
                          style={{ width: '100%', border: 'none', background: 'transparent', padding: '4px' }}
                        />
                      </td>
                      <td>
                        {newUser.first_name} {newUser.last_name}
                        <div style={{ fontSize: '11px', color: '#64748b' }}>
                          <input
                            type="text"
                            value={newUser.first_name}
                            onChange={(e) => setNewUser({...newUser, first_name: e.target.value})}
                            placeholder="First"
                            style={{ width: '45%', border: 'none', background: 'transparent', padding: '2px' }}
                          />
                          <input
                            type="text"
                            value={newUser.last_name}
                            onChange={(e) => setNewUser({...newUser, last_name: e.target.value})}
                            placeholder="Last"
                            style={{ width: '45%', border: 'none', background: 'transparent', padding: '2px' }}
                          />
                        </div>
                      </td>
                      <td>
                        <select 
                          value={newUser.role} 
                          onChange={(e) => setNewUser({...newUser, role: e.target.value})}
                          style={{ width: '100%', border: 'none', background: 'transparent', padding: '4px' }}
                        >
                          <option value="viewer">Viewer</option>
                          <option value="operator">Operator</option>
                          <option value="admin">Admin</option>
                        </select>
                      </td>
                      <td style={{ color: '#64748b', fontSize: '12px' }}>New</td>
                      <td>
                        <button onClick={saveNewUser} className="btn-icon btn-success" title="Save" disabled={saving}>
                          <Check size={16} />
                        </button>
                        <button onClick={cancelAddingNew} className="btn-icon btn-ghost" title="Cancel">
                          <X size={16} />
                        </button>
                      </td>
                    </tr>
                  )}

                  {/* Existing Users */}
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
                          value={user.role} 
                          onChange={(e) => {
                            e.stopPropagation();
                            handleRoleChange(user.id, e.target.value);
                          }}
                          style={{ border: 'none', background: 'transparent', fontSize: '13px' }}
                        >
                          <option value="viewer">Viewer</option>
                          <option value="operator">Operator</option>
                          <option value="admin">Admin</option>
                        </select>
                      </td>
                      <td style={{ color: '#64748b', fontSize: '12px' }}>
                        {new Date(user.created_at).toLocaleDateString()}
                      </td>
                      <td>
                        <div style={{ display: 'flex', gap: '4px' }}>
                          <button 
                            className="btn-icon btn-ghost"
                            onClick={(e) => {
                              e.stopPropagation();
                              setSelectedUser(user);
                            }}
                            title="Edit user details"
                          >
                            <Edit3 size={16} />
                          </button>
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

        {/* Column 3: User Details Panel */}
        <div className="dashboard-section">
          <div className="section-header">
            {selectedUser ? `User Details` : 'Select User'}
          </div>
          <div className="compact-content">
            {selectedUser ? (
              <div className="user-details">
                <h3>{selectedUser.username}</h3>
                
                <div className="detail-group">
                  <div className="detail-label">Email</div>
                  <div className="detail-value">
                    {editing?.userId === selectedUser.id && editing?.field === 'email' ? (
                      <div>
                        <input
                          type="email"
                          value={editing.value}
                          onChange={(e) => setEditing({...editing, value: e.target.value})}
                          onKeyDown={handleKeyPress}
                          className="detail-input"
                          autoFocus
                        />
                        <div className="action-buttons">
                          <button onClick={saveEdit} className="btn-icon btn-success" title="Save" disabled={saving}>
                            <Check size={16} />
                          </button>
                          <button onClick={cancelEditing} className="btn-icon btn-ghost" title="Cancel">
                            <X size={16} />
                          </button>
                        </div>
                      </div>
                    ) : (
                      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                        <span>{selectedUser.email}</span>
                        <button 
                          className="btn-icon btn-ghost btn-sm"
                          onClick={() => startEditing(selectedUser.id, 'email', selectedUser.email)}
                          title="Edit email"
                        >
                          <Edit3 size={14} />
                        </button>
                      </div>
                    )}
                  </div>
                </div>

                <div className="detail-group">
                  <div className="detail-label">First Name</div>
                  <div className="detail-value">
                    {editing?.userId === selectedUser.id && editing?.field === 'first_name' ? (
                      <div>
                        <input
                          type="text"
                          value={editing.value}
                          onChange={(e) => setEditing({...editing, value: e.target.value})}
                          onKeyDown={handleKeyPress}
                          className="detail-input"
                          autoFocus
                        />
                        <div className="action-buttons">
                          <button onClick={saveEdit} className="btn-icon btn-success" title="Save" disabled={saving}>
                            <Check size={16} />
                          </button>
                          <button onClick={cancelEditing} className="btn-icon btn-ghost" title="Cancel">
                            <X size={16} />
                          </button>
                        </div>
                      </div>
                    ) : (
                      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                        <span>{selectedUser.first_name || '-'}</span>
                        <button 
                          className="btn-icon btn-ghost btn-sm"
                          onClick={() => startEditing(selectedUser.id, 'first_name', selectedUser.first_name || '')}
                          title="Edit first name"
                        >
                          <Edit3 size={14} />
                        </button>
                      </div>
                    )}
                  </div>
                </div>

                <div className="detail-group">
                  <div className="detail-label">Last Name</div>
                  <div className="detail-value">
                    {editing?.userId === selectedUser.id && editing?.field === 'last_name' ? (
                      <div>
                        <input
                          type="text"
                          value={editing.value}
                          onChange={(e) => setEditing({...editing, value: e.target.value})}
                          onKeyDown={handleKeyPress}
                          className="detail-input"
                          autoFocus
                        />
                        <div className="action-buttons">
                          <button onClick={saveEdit} className="btn-icon btn-success" title="Save" disabled={saving}>
                            <Check size={16} />
                          </button>
                          <button onClick={cancelEditing} className="btn-icon btn-ghost" title="Cancel">
                            <X size={16} />
                          </button>
                        </div>
                      </div>
                    ) : (
                      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                        <span>{selectedUser.last_name || '-'}</span>
                        <button 
                          className="btn-icon btn-ghost btn-sm"
                          onClick={() => startEditing(selectedUser.id, 'last_name', selectedUser.last_name || '')}
                          title="Edit last name"
                        >
                          <Edit3 size={14} />
                        </button>
                      </div>
                    )}
                  </div>
                </div>

                <div className="detail-group">
                  <div className="detail-label">Telephone</div>
                  <div className="detail-value">
                    {editing?.userId === selectedUser.id && editing?.field === 'telephone' ? (
                      <div>
                        <input
                          type="text"
                          value={editing.value}
                          onChange={(e) => setEditing({...editing, value: e.target.value})}
                          onKeyDown={handleKeyPress}
                          className="detail-input"
                          autoFocus
                        />
                        <div className="action-buttons">
                          <button onClick={saveEdit} className="btn-icon btn-success" title="Save" disabled={saving}>
                            <Check size={16} />
                          </button>
                          <button onClick={cancelEditing} className="btn-icon btn-ghost" title="Cancel">
                            <X size={16} />
                          </button>
                        </div>
                      </div>
                    ) : (
                      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                        <span>{selectedUser.telephone || '-'}</span>
                        <button 
                          className="btn-icon btn-ghost btn-sm"
                          onClick={() => startEditing(selectedUser.id, 'telephone', selectedUser.telephone || '')}
                          title="Edit telephone"
                        >
                          <Edit3 size={14} />
                        </button>
                      </div>
                    )}
                  </div>
                </div>

                <div className="detail-group">
                  <div className="detail-label">Title</div>
                  <div className="detail-value">
                    {editing?.userId === selectedUser.id && editing?.field === 'title' ? (
                      <div>
                        <input
                          type="text"
                          value={editing.value}
                          onChange={(e) => setEditing({...editing, value: e.target.value})}
                          onKeyDown={handleKeyPress}
                          className="detail-input"
                          autoFocus
                        />
                        <div className="action-buttons">
                          <button onClick={saveEdit} className="btn-icon btn-success" title="Save" disabled={saving}>
                            <Check size={16} />
                          </button>
                          <button onClick={cancelEditing} className="btn-icon btn-ghost" title="Cancel">
                            <X size={16} />
                          </button>
                        </div>
                      </div>
                    ) : (
                      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                        <span>{selectedUser.title || '-'}</span>
                        <button 
                          className="btn-icon btn-ghost btn-sm"
                          onClick={() => startEditing(selectedUser.id, 'title', selectedUser.title || '')}
                          title="Edit title"
                        >
                          <Edit3 size={14} />
                        </button>
                      </div>
                    )}
                  </div>
                </div>

                <div className="detail-group">
                  <div className="detail-label">Password</div>
                  <div className="detail-value">
                    {editing?.userId === selectedUser.id && editing?.field === 'password' ? (
                      <div>
                        <input
                          type="password"
                          placeholder="New password"
                          value={editing.value}
                          onChange={(e) => setEditing({...editing, value: e.target.value})}
                          onKeyDown={handleKeyPress}
                          className="detail-input"
                          autoFocus
                        />
                        <input
                          type="password"
                          placeholder="Confirm password"
                          value={editing.confirmPassword || ''}
                          onChange={(e) => setEditing({...editing, confirmPassword: e.target.value})}
                          onKeyDown={handleKeyPress}
                          className="detail-input"
                          style={{ marginTop: '8px' }}
                        />
                        <div className="action-buttons">
                          <button onClick={saveEdit} className="btn-icon btn-success" title="Save" disabled={saving}>
                            <Check size={16} />
                          </button>
                          <button onClick={cancelEditing} className="btn-icon btn-ghost" title="Cancel">
                            <X size={16} />
                          </button>
                        </div>
                      </div>
                    ) : (
                      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                        <span>••••••••</span>
                        <button 
                          className="btn-icon btn-ghost btn-sm"
                          onClick={() => startEditing(selectedUser.id, 'password')}
                          title="Change password"
                        >
                          <Edit3 size={14} />
                        </button>
                      </div>
                    )}
                  </div>
                </div>

                <div className="detail-group">
                  <div className="detail-label">Role</div>
                  <div className="detail-value">
                    <select 
                      value={selectedUser.role} 
                      onChange={(e) => handleRoleChange(selectedUser.id, e.target.value)}
                      className="detail-input"
                    >
                      <option value="viewer">Viewer</option>
                      <option value="operator">Operator</option>
                      <option value="admin">Admin</option>
                    </select>
                  </div>
                </div>

                <div className="detail-group">
                  <div className="detail-label">Created</div>
                  <div className="detail-value">
                    {new Date(selectedUser.created_at).toLocaleString()}
                  </div>
                </div>

                <div className="action-buttons">
                  <button 
                    className="btn-icon btn-danger"
                    onClick={() => handleDelete(selectedUser.id)}
                    title="Delete user"
                  >
                    <Trash2 size={16} />
                  </button>
                </div>
              </div>
            ) : (
              <div className="empty-state">
                <p>Select a user from the table to view and edit details</p>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};

export default Users;