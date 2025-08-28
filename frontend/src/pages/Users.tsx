import React, { useState, useEffect } from 'react';
import { userApi } from '../services/api';
import { User, UserCreate } from '../types';

const Users: React.FC = () => {
  const [users, setUsers] = useState<User[]>([]);
  const [loading, setLoading] = useState(true);
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [editingUser, setEditingUser] = useState<User | null>(null);
  const [formData, setFormData] = useState<UserCreate>({
    email: '',
    username: '',
    password: '',
    role: 'viewer'
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
      setUsers([]); // Set empty array on error
    } finally {
      setLoading(false);
    }
  };

  const handleCreate = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      if (editingUser) {
        // For updates, only send fields that have values
        const updateData: any = {};
        if (formData.email) updateData.email = formData.email;
        if (formData.username) updateData.username = formData.username;
        if (formData.password) updateData.password = formData.password;
        if (formData.role) updateData.role = formData.role;
        
        await userApi.update(editingUser.id, updateData);
      } else {
        await userApi.create(formData);
      }
      setShowCreateModal(false);
      setEditingUser(null);
      setFormData({ email: '', username: '', password: '', role: 'viewer' });
      fetchUsers();
    } catch (error) {
      console.error(`Failed to ${editingUser ? 'update' : 'create'} user:`, error);
    }
  };

  const resetForm = () => {
    setFormData({
      email: '',
      username: '',
      password: '',
      role: 'viewer'
    });
    setEditingUser(null);
  };

  const handleEdit = (user: User) => {
    setEditingUser(user);
    setFormData({
      email: user.email,
      username: user.username,
      password: '', // Don't pre-fill password for security
      role: user.role
    });
    setShowCreateModal(true);
  };

  const handleDelete = async (id: number) => {
    if (window.confirm('Are you sure you want to delete this user?')) {
      try {
        await userApi.delete(id);
        fetchUsers();
      } catch (error) {
        console.error('Failed to delete user:', error);
      }
    }
  };

  const handleRoleChange = async (id: number, role: string) => {
    try {
      await userApi.assignRole(id, role);
      fetchUsers();
    } catch (error) {
      console.error('Failed to update role:', error);
    }
  };

  if (loading) return <div>Loading users...</div>;

  return (
    <div>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '20px' }}>
        <h1>Users</h1>
        <button 
          className="btn btn-primary"
          onClick={() => {
            resetForm();
            setShowCreateModal(true);
          }}
        >
          Add User
        </button>
      </div>

      <div className="card">
        <table className="table">
          <thead>
            <tr>
              <th>ID</th>
              <th>Username</th>
              <th>Email</th>
              <th>Role</th>
              <th>Created</th>
              <th>Actions</th>
            </tr>
          </thead>
          <tbody>
            {(users || []).map(user => (
              <tr key={user.id}>
                <td>{user.id}</td>
                <td>{user.username}</td>
                <td>{user.email}</td>
                <td>
                  <select 
                    value={user.role} 
                    onChange={(e) => handleRoleChange(user.id, e.target.value)}
                    className="form-control"
                    style={{ width: 'auto' }}
                  >
                    <option value="viewer">Viewer</option>
                    <option value="operator">Operator</option>
                    <option value="admin">Admin</option>
                  </select>
                </td>
                <td>{new Date(user.created_at).toLocaleDateString()}</td>
                <td>
                  <div style={{ display: 'flex', gap: '5px' }}>
                    <button 
                      className="btn btn-secondary"
                      onClick={() => handleEdit(user)}
                      style={{ fontSize: '12px' }}
                    >
                      Edit
                    </button>
                    <button 
                      className="btn btn-danger"
                      onClick={() => handleDelete(user.id)}
                      style={{ fontSize: '12px' }}
                    >
                      Delete
                    </button>
                  </div>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {/* Create User Modal */}
      {showCreateModal && (
        <div style={{
          position: 'fixed',
          top: 0,
          left: 0,
          right: 0,
          bottom: 0,
          backgroundColor: 'rgba(0,0,0,0.5)',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          zIndex: 1000
        }}>
          <div className="card" style={{ width: '400px', margin: '20px' }}>
            <h3>{editingUser ? 'Edit User' : 'Add New User'}</h3>
            <form onSubmit={handleCreate}>
              <div className="form-group">
                <label>Email:</label>
                <input
                  type="email"
                  value={formData.email}
                  onChange={(e) => setFormData({...formData, email: e.target.value})}
                  required
                />
              </div>
              <div className="form-group">
                <label>Username:</label>
                <input
                  type="text"
                  value={formData.username}
                  onChange={(e) => setFormData({...formData, username: e.target.value})}
                  required
                />
              </div>
              <div className="form-group">
                <label>Password{editingUser ? ' (leave blank to keep current)' : ''}:</label>
                <input
                  type="password"
                  value={formData.password}
                  onChange={(e) => setFormData({...formData, password: e.target.value})}
                  required={!editingUser}
                />
              </div>
              <div className="form-group">
                <label>Role:</label>
                <select 
                  value={formData.role}
                  onChange={(e) => setFormData({...formData, role: e.target.value as any})}
                >
                  <option value="viewer">Viewer</option>
                  <option value="operator">Operator</option>
                  <option value="admin">Admin</option>
                </select>
              </div>
              <div style={{ display: 'flex', gap: '10px', marginTop: '20px' }}>
                <button type="submit" className="btn btn-primary">
                  {editingUser ? 'Update User' : 'Create User'}
                </button>
                <button 
                  type="button" 
                  className="btn btn-secondary"
                  onClick={() => {
                    setShowCreateModal(false);
                    resetForm();
                  }}
                >
                  Cancel
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};

export default Users;