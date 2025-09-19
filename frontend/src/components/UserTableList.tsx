import React, { useState, useEffect, forwardRef, useImperativeHandle, useCallback, useRef } from 'react';
import { Edit3, Trash2, ChevronUp, ChevronDown } from 'lucide-react';
import { userApi } from '../services/api';
import { User } from '../types';

interface UserTableListProps {
  onSelectionChanged?: (selectedUsers: User[]) => void;
  onRowDoubleClicked?: (user: User) => void;
  onDataLoaded?: (users: User[]) => void;
  onEditUser?: (user: User) => void;
  onDeleteUser?: (userId: number) => void;
}

export interface UserTableListRef {
  refresh: () => void;
}

const UserTableList = forwardRef<UserTableListRef, UserTableListProps>(({ 
  onSelectionChanged, 
  onRowDoubleClicked,
  onDataLoaded,
  onEditUser,
  onDeleteUser
}, ref) => {
  const [users, setUsers] = useState<User[]>([]);
  const [loading, setLoading] = useState(true);
  const [selectedUserId, setSelectedUserId] = useState<number | null>(null);
  const [sortField, setSortField] = useState<string | null>(null);
  const [sortDirection, setSortDirection] = useState<'asc' | 'desc'>('asc');
  const hasLoadedRef = useRef(false);

  // Load users
  const loadUsers = useCallback(async () => {
    try {
      setLoading(true);
      const response = await userApi.list();
      const usersData = response.data || [];
      setUsers(usersData);
      
      // Only call onDataLoaded once to prevent infinite loops
      if (!hasLoadedRef.current) {
        hasLoadedRef.current = true;
        onDataLoaded?.(usersData);
      }
    } catch (error) {
      console.error('Failed to load users:', error);
    } finally {
      setLoading(false);
    }
  }, [onDataLoaded]);

  useEffect(() => {
    if (!hasLoadedRef.current) {
      loadUsers();
    }
  }, [loadUsers]);

  // Expose refresh method via ref
  useImperativeHandle(ref, () => ({
    refresh: loadUsers
  }));

  // Handle user selection
  const handleUserClick = (user: User) => {
    setSelectedUserId(user.id);
    onSelectionChanged?.([user]);
  };

  // Handle double click
  const handleDoubleClick = (user: User) => {
    onRowDoubleClicked?.(user);
  };

  // Handle edit action
  const handleEdit = (user: User, event: React.MouseEvent) => {
    event.stopPropagation();
    onEditUser?.(user);
  };

  // Handle delete action
  const handleDelete = (userId: number, event: React.MouseEvent) => {
    event.stopPropagation();
    onDeleteUser?.(userId);
  };

  // Handle sorting
  const handleSort = (field: string) => {
    if (sortField === field) {
      setSortDirection(sortDirection === 'asc' ? 'desc' : 'asc');
    } else {
      setSortField(field);
      setSortDirection('asc');
    }
  };

  // Sort users
  const sortedUsers = React.useMemo(() => {
    if (!sortField) return users;

    return [...users].sort((a, b) => {
      const aValue = a[sortField as keyof User];
      const bValue = b[sortField as keyof User];

      if (aValue === null || aValue === undefined) return 1;
      if (bValue === null || bValue === undefined) return -1;

      let comparison = 0;
      if (typeof aValue === 'string' && typeof bValue === 'string') {
        comparison = aValue.toLowerCase().localeCompare(bValue.toLowerCase());
      } else if (typeof aValue === 'number' && typeof bValue === 'number') {
        comparison = aValue - bValue;
      } else {
        comparison = String(aValue).localeCompare(String(bValue));
      }

      return sortDirection === 'asc' ? comparison : -comparison;
    });
  }, [users, sortField, sortDirection]);

  const getSortIcon = (field: string) => {
    if (sortField !== field) return null;
    return sortDirection === 'asc' ? <ChevronUp size={12} /> : <ChevronDown size={12} />;
  };

  if (loading) {
    return (
      <div className="loading-state">
        <p>Loading users...</p>
      </div>
    );
  }

  return (
    <div className="table-container">
      <table className="users-table">
        <thead>
          <tr>
            <th onClick={() => handleSort('username')} style={{ cursor: 'pointer' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '4px' }}>
                Username {getSortIcon('username')}
              </div>
            </th>
            <th onClick={() => handleSort('email')} style={{ cursor: 'pointer' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '4px' }}>
                Email {getSortIcon('email')}
              </div>
            </th>
            <th onClick={() => handleSort('first_name')} style={{ cursor: 'pointer' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '4px' }}>
                Name {getSortIcon('first_name')}
              </div>
            </th>
            <th onClick={() => handleSort('role')} style={{ cursor: 'pointer' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '4px' }}>
                Role {getSortIcon('role')}
              </div>
            </th>
            <th onClick={() => handleSort('created_at')} style={{ cursor: 'pointer' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '4px' }}>
                Created {getSortIcon('created_at')}
              </div>
            </th>
            <th>Actions</th>
          </tr>
        </thead>
        <tbody>
          {sortedUsers.map((user) => (
            <tr 
              key={user.id} 
              className={selectedUserId === user.id ? 'selected' : ''}
              onClick={() => handleUserClick(user)}
              onDoubleClick={() => handleDoubleClick(user)}
            >
              <td>{user.username}</td>
              <td>{user.email}</td>
              <td>{user.first_name} {user.last_name}</td>
              <td>
                <span style={{ 
                  padding: '2px 6px', 
                  borderRadius: '3px', 
                  fontSize: '11px',
                  backgroundColor: user.role === 'admin' ? '#fee2e2' : user.role === 'operator' ? '#fef3c7' : '#f0f9ff',
                  color: user.role === 'admin' ? '#dc2626' : user.role === 'operator' ? '#d97706' : '#0369a1'
                }}>
                  {user.role?.charAt(0).toUpperCase() + user.role?.slice(1)}
                </span>
              </td>
              <td style={{ color: '#64748b', fontSize: '12px' }}>
                {new Date(user.created_at).toLocaleDateString()}
              </td>
              <td>
                <div style={{ display: 'flex', gap: '4px' }}>
                  <button 
                    className="btn-icon btn-ghost"
                    onClick={(e) => handleEdit(user, e)}
                    title="Edit user"
                  >
                    <Edit3 size={14} />
                  </button>
                  <button 
                    className="btn-icon btn-danger"
                    onClick={(e) => handleDelete(user.id, e)}
                    title="Delete user"
                  >
                    <Trash2 size={14} />
                  </button>
                </div>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
});

UserTableList.displayName = 'UserTableList';

export default UserTableList;