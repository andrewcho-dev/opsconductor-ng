import React, { useState, useEffect } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import { Plus, Trash2, Check, X } from 'lucide-react';
import { userApi } from '../services/api';
import { User, UserCreate } from '../types';

interface EditingState {
  userId: number;
  field: 'username' | 'email' | 'password' | 'first_name' | 'last_name' | 'telephone' | 'title';
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
    setEditing(null); // Cancel any existing edits
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
    // Validation
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
      } catch (error) {
        console.error('Failed to delete user:', error);
      }
    }
  };

  const handleRoleChange = async (userId: number, role: string) => {
    try {
      await userApi.assignRole(userId, role);
      fetchUsers();
    } catch (error) {
      console.error('Failed to update role:', error);
    }
  };

  const startEditing = (userId: number, field: 'username' | 'email' | 'password' | 'first_name' | 'last_name' | 'telephone' | 'title', currentValue: string = '') => {
    setEditing({
      userId,
      field,
      value: field === 'password' ? '' : currentValue,
      confirmPassword: field === 'password' ? '' : undefined
    });
  };

  const cancelEditing = () => {
    setEditing(null);
  };

  const saveEdit = async () => {
    if (!editing) return;

    // Password validation
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

    // Other field validation
    if (editing.field !== 'password' && !editing.value.trim()) {
      alert(`${editing.field} cannot be empty`);
      return;
    }

    try {
      setSaving(true);
      const updateData: any = {};
      updateData[editing.field] = editing.value;
      
      await userApi.update(editing.userId, updateData);
      await fetchUsers();
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
    <div className="main-content">
      <style>
        {`
          .new-user-row {
            background-color: #f8fafc;
            border: 2px solid #10b981;
          }
          .new-user-row .table-input {
            border: none;
            background: transparent;
            padding: 4px 2px;
            font-size: 13px;
            width: 100%;
            min-width: 80px;
            outline: none;
          }
          .new-user-row .table-input:focus {
            background: white;
            border: 1px solid #10b981;
            border-radius: 2px;
            box-shadow: none;
          }
          .password-inputs {
            display: flex;
            flex-direction: column;
            gap: 4px;
          }
          .password-inputs .table-input {
            margin: 0;
          }
          .btn-icon {
            display: inline-flex;
            align-items: center;
            justify-content: center;
            width: 32px;
            height: 32px;
            border: none;
            background: none;
            cursor: pointer;
            transition: all 0.2s;
            margin: 0 2px;
            padding: 4px;
          }
          .btn-icon:hover {
            opacity: 0.7;
          }
          .btn-icon:disabled {
            opacity: 0.3;
            cursor: not-allowed;
          }
          .btn-success {
            color: #10b981;
          }
          .btn-success:hover:not(:disabled) {
            color: #059669;
          }
          .btn-danger {
            color: #ef4444;
          }
          .btn-danger:hover:not(:disabled) {
            color: #dc2626;
          }
          .btn-ghost {
            color: #6b7280;
          }
          .btn-ghost:hover:not(:disabled) {
            color: #374151;
          }
        `}
      </style>
      <div className="page-header">
        <h1 className="page-title">Users</h1>
        <div className="page-actions">
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

      {users.length === 0 && !addingNew ? (
        <div className="empty-state">
          <h3 className="empty-state-title">No users found</h3>
          <p className="empty-state-description">
            Get started by creating your first user account.
          </p>
          <button 
            className="btn-icon btn-success"
            onClick={startAddingNew}
            title="Create first user"
          >
            <Plus size={16} />
          </button>
        </div>
      ) : (
        <div className="data-table-container">
          <table className="data-table">
            <thead>
              <tr>
                <th>ID</th>
                <th>Username</th>
                <th>Email</th>
                <th>First Name</th>
                <th>Last Name</th>
                <th>Telephone</th>
                <th>Title</th>
                <th>Password</th>
                <th>Role</th>
                <th>Created</th>
                <th className="text-right">Actions</th>
              </tr>
            </thead>
            <tbody>
              {/* New User Row */}
              {addingNew && (
                <tr className="new-user-row">
                  <td className="text-neutral-500">New</td>
                  
                  {/* Username */}
                  <td>
                    <input
                      type="text"
                      value={newUser.username}
                      onChange={(e) => setNewUser({...newUser, username: e.target.value})}
                      onKeyDown={handleNewUserKeyPress}
                      className="table-input"
                      placeholder="Username"
                      autoFocus
                    />
                  </td>

                  {/* Email */}
                  <td>
                    <input
                      type="email"
                      value={newUser.email}
                      onChange={(e) => setNewUser({...newUser, email: e.target.value})}
                      onKeyDown={handleNewUserKeyPress}
                      className="table-input"
                      placeholder="Email"
                    />
                  </td>

                  {/* First Name */}
                  <td>
                    <input
                      type="text"
                      value={newUser.first_name}
                      onChange={(e) => setNewUser({...newUser, first_name: e.target.value})}
                      onKeyDown={handleNewUserKeyPress}
                      className="table-input"
                      placeholder="First Name"
                    />
                  </td>

                  {/* Last Name */}
                  <td>
                    <input
                      type="text"
                      value={newUser.last_name}
                      onChange={(e) => setNewUser({...newUser, last_name: e.target.value})}
                      onKeyDown={handleNewUserKeyPress}
                      className="table-input"
                      placeholder="Last Name"
                    />
                  </td>

                  {/* Telephone */}
                  <td>
                    <input
                      type="tel"
                      value={newUser.telephone}
                      onChange={(e) => setNewUser({...newUser, telephone: e.target.value})}
                      onKeyDown={handleNewUserKeyPress}
                      className="table-input"
                      placeholder="Phone"
                    />
                  </td>

                  {/* Title */}
                  <td>
                    <input
                      type="text"
                      value={newUser.title}
                      onChange={(e) => setNewUser({...newUser, title: e.target.value})}
                      onKeyDown={handleNewUserKeyPress}
                      className="table-input"
                      placeholder="Title"
                    />
                  </td>

                  {/* Password */}
                  <td>
                    <div className="password-inputs">
                      <input
                        type="password"
                        value={newUser.password}
                        onChange={(e) => setNewUser({...newUser, password: e.target.value})}
                        onKeyDown={handleNewUserKeyPress}
                        className="table-input"
                        placeholder="Password"
                      />
                      <input
                        type="password"
                        value={newUser.confirmPassword}
                        onChange={(e) => setNewUser({...newUser, confirmPassword: e.target.value})}
                        onKeyDown={handleNewUserKeyPress}
                        className="table-input"
                        placeholder="Confirm"
                        style={{ marginTop: '4px' }}
                      />
                    </div>
                  </td>

                  {/* Role */}
                  <td>
                    <select 
                      value={newUser.role} 
                      onChange={(e) => setNewUser({...newUser, role: e.target.value})}
                      className="table-select"
                    >
                      <option value="viewer">Viewer</option>
                      <option value="operator">Operator</option>
                      <option value="admin">Admin</option>
                    </select>
                  </td>

                  <td className="text-neutral-500">-</td>

                  {/* Actions */}
                  <td>
                    <div className="table-actions">
                      <button 
                        className="btn-icon btn-success"
                        onClick={saveNewUser}
                        title="Save new user"
                        disabled={saving}
                      >
                        {saving ? <span className="loading-spinner"></span> : <Check size={16} />}
                      </button>
                      <button 
                        className="btn-icon btn-ghost"
                        onClick={cancelAddingNew}
                        title="Cancel"
                      >
                        <X size={16} />
                      </button>
                    </div>
                  </td>
                </tr>
              )}

              {users.map(user => (
                <tr key={user.id}>
                  <td className="text-neutral-500">{user.id}</td>
                  
                  {/* Username - Inline Editable */}
                  <td className="font-medium">
                    {editing?.userId === user.id && editing?.field === 'username' ? (
                      <div className="inline-edit">
                        <input
                          type="text"
                          value={editing.value}
                          onChange={(e) => setEditing({...editing, value: e.target.value})}
                          onKeyDown={handleKeyPress}
                          className="table-input"
                          autoFocus
                        />
                        <div className="inline-edit-actions">
                          <button onClick={saveEdit} className="btn-icon btn-success" title="Save" disabled={saving}>
                            <Check size={16} />
                          </button>
                          <button onClick={cancelEditing} className="btn-icon btn-ghost" title="Cancel">
                            <X size={16} />
                          </button>
                        </div>
                      </div>
                    ) : (
                      <span 
                        onClick={() => startEditing(user.id, 'username', user.username)}
                        className="editable-field"
                        title="Click to edit username"
                      >
                        {user.username}
                      </span>
                    )}
                  </td>

                  {/* Email - Inline Editable */}
                  <td>
                    {editing?.userId === user.id && editing?.field === 'email' ? (
                      <div className="inline-edit">
                        <input
                          type="email"
                          value={editing.value}
                          onChange={(e) => setEditing({...editing, value: e.target.value})}
                          onKeyDown={handleKeyPress}
                          className="table-input"
                          autoFocus
                        />
                        <div className="inline-edit-actions">
                          <button onClick={saveEdit} className="btn-icon btn-success" title="Save" disabled={saving}>
                            <Check size={16} />
                          </button>
                          <button onClick={cancelEditing} className="btn-icon btn-ghost" title="Cancel">
                            <X size={16} />
                          </button>
                        </div>
                      </div>
                    ) : (
                      <span 
                        onClick={() => startEditing(user.id, 'email', user.email)}
                        className="editable-field"
                        title="Click to edit email"
                      >
                        {user.email}
                      </span>
                    )}
                  </td>

                  {/* First Name - Inline Editable */}
                  <td>
                    {editing?.userId === user.id && editing?.field === 'first_name' ? (
                      <div className="inline-edit">
                        <input
                          type="text"
                          value={editing.value}
                          onChange={(e) => setEditing({...editing, value: e.target.value})}
                          onKeyDown={handleKeyPress}
                          className="table-input"
                          autoFocus
                        />
                        <div className="inline-edit-actions">
                          <button onClick={saveEdit} className="btn-icon btn-success" title="Save" disabled={saving}>
                            <Check size={16} />
                          </button>
                          <button onClick={cancelEditing} className="btn-icon btn-ghost" title="Cancel">
                            <X size={16} />
                          </button>
                        </div>
                      </div>
                    ) : (
                      <span 
                        onClick={() => startEditing(user.id, 'first_name', user.first_name || '')}
                        className="editable-field"
                        title="Click to edit first name"
                      >
                        {user.first_name || <span className="text-neutral-400">-</span>}
                      </span>
                    )}
                  </td>

                  {/* Last Name - Inline Editable */}
                  <td>
                    {editing?.userId === user.id && editing?.field === 'last_name' ? (
                      <div className="inline-edit">
                        <input
                          type="text"
                          value={editing.value}
                          onChange={(e) => setEditing({...editing, value: e.target.value})}
                          onKeyDown={handleKeyPress}
                          className="table-input"
                          autoFocus
                        />
                        <div className="inline-edit-actions">
                          <button onClick={saveEdit} className="btn-icon btn-success" title="Save" disabled={saving}>
                            <Check size={16} />
                          </button>
                          <button onClick={cancelEditing} className="btn-icon btn-ghost" title="Cancel">
                            <X size={16} />
                          </button>
                        </div>
                      </div>
                    ) : (
                      <span 
                        onClick={() => startEditing(user.id, 'last_name', user.last_name || '')}
                        className="editable-field"
                        title="Click to edit last name"
                      >
                        {user.last_name || <span className="text-neutral-400">-</span>}
                      </span>
                    )}
                  </td>

                  {/* Telephone - Inline Editable */}
                  <td>
                    {editing?.userId === user.id && editing?.field === 'telephone' ? (
                      <div className="inline-edit">
                        <input
                          type="tel"
                          value={editing.value}
                          onChange={(e) => setEditing({...editing, value: e.target.value})}
                          onKeyDown={handleKeyPress}
                          className="table-input"
                          autoFocus
                        />
                        <div className="inline-edit-actions">
                          <button onClick={saveEdit} className="btn-icon btn-success" title="Save" disabled={saving}>
                            <Check size={16} />
                          </button>
                          <button onClick={cancelEditing} className="btn-icon btn-ghost" title="Cancel">
                            <X size={16} />
                          </button>
                        </div>
                      </div>
                    ) : (
                      <span 
                        onClick={() => startEditing(user.id, 'telephone', user.telephone || '')}
                        className="editable-field"
                        title="Click to edit telephone"
                      >
                        {user.telephone || <span className="text-neutral-400">-</span>}
                      </span>
                    )}
                  </td>

                  {/* Title - Inline Editable */}
                  <td>
                    {editing?.userId === user.id && editing?.field === 'title' ? (
                      <div className="inline-edit">
                        <input
                          type="text"
                          value={editing.value}
                          onChange={(e) => setEditing({...editing, value: e.target.value})}
                          onKeyDown={handleKeyPress}
                          className="table-input"
                          autoFocus
                        />
                        <div className="inline-edit-actions">
                          <button onClick={saveEdit} className="btn-icon btn-success" title="Save" disabled={saving}>
                            <Check size={16} />
                          </button>
                          <button onClick={cancelEditing} className="btn-icon btn-ghost" title="Cancel">
                            <X size={16} />
                          </button>
                        </div>
                      </div>
                    ) : (
                      <span 
                        onClick={() => startEditing(user.id, 'title', user.title || '')}
                        className="editable-field"
                        title="Click to edit title"
                      >
                        {user.title || <span className="text-neutral-400">-</span>}
                      </span>
                    )}
                  </td>

                  {/* Password - Inline Editable with Confirmation */}
                  <td>
                    {editing?.userId === user.id && editing?.field === 'password' ? (
                      <div className="inline-edit password-edit">
                        <div className="password-inputs">
                          <input
                            type="password"
                            placeholder="New password"
                            value={editing.value}
                            onChange={(e) => setEditing({...editing, value: e.target.value})}
                            onKeyDown={handleKeyPress}
                            className="table-input"
                            autoFocus
                          />
                          <input
                            type="password"
                            placeholder="Confirm password"
                            value={editing.confirmPassword || ''}
                            onChange={(e) => setEditing({...editing, confirmPassword: e.target.value})}
                            onKeyDown={handleKeyPress}
                            className="table-input"
                          />
                        </div>
                        <div className="inline-edit-actions">
                          <button onClick={saveEdit} className="btn-icon btn-success" title="Save" disabled={saving}>
                            <Check size={16} />
                          </button>
                          <button onClick={cancelEditing} className="btn-icon btn-ghost" title="Cancel">
                            <X size={16} />
                          </button>
                        </div>
                      </div>
                    ) : (
                      <span 
                        onClick={() => startEditing(user.id, 'password')}
                        className="editable-field password-field"
                        title="Click to change password"
                      >
                        ••••••••
                      </span>
                    )}
                  </td>

                  {/* Role - Already Inline Editable */}
                  <td>
                    <select 
                      value={user.role} 
                      onChange={(e) => handleRoleChange(user.id, e.target.value)}
                      className="table-select"
                    >
                      <option value="viewer">Viewer</option>
                      <option value="operator">Operator</option>
                      <option value="admin">Admin</option>
                    </select>
                  </td>

                  <td className="text-neutral-500">
                    {new Date(user.created_at).toLocaleDateString()}
                  </td>

                  {/* Actions - Only Delete Now */}
                  <td>
                    <div className="table-actions">
                      <button 
                        className="btn-icon btn-danger"
                        onClick={() => handleDelete(user.id)}
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
  );
};

export default Users;