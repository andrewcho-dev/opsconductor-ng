import React, { useState, useEffect, useRef, useCallback } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import { Link } from 'react-router-dom';
import { Plus, X, Users as UsersIcon, Target, Settings, Play, MessageSquare, Edit3, Trash2 } from 'lucide-react';
import { userApi } from '../services/api';
import UserDataGrid, { UserDataGridRef } from '../components/UserDataGrid';
import UserSpreadsheetForm from '../components/UserSpreadsheetForm';
import { User } from '../types';

const Users: React.FC = () => {
  const navigate = useNavigate();
  const { action, id } = useParams<{ action?: string; id?: string }>();
  
  const [users, setUsers] = useState<User[]>([]);
  const [loading, setLoading] = useState(true);
  const [selectedUser, setSelectedUser] = useState<User | null>(null);
  const [editingUser, setEditingUser] = useState<User | null>(null);
  const [addingNew, setAddingNew] = useState(false);
  const [loadingUserDetails, setLoadingUserDetails] = useState(false);
  const userListRef = useRef<UserDataGridRef>(null);
  const debounceTimeoutRef = useRef<NodeJS.Timeout | null>(null);

  // Fetch detailed user data
  const fetchDetailedUserData = useCallback(async (userId: number): Promise<User | null> => {
    try {
      setLoadingUserDetails(true);
      const response = await userApi.get(userId);
      
      // The API returns {success: true, data: {...}}, so we need response.data
      const userData = (response as any).data || response;
      
      return userData;
    } catch (error) {
      return null;
    } finally {
      setLoadingUserDetails(false);
    }
  }, []);

  // Debounced function to fetch detailed user data
  const debouncedFetchUserDetails = useCallback((user: User) => {
    // Immediately set the basic user data to prevent flashing
    setSelectedUser(user);
    
    // Clear any existing timeout
    if (debounceTimeoutRef.current) {
      clearTimeout(debounceTimeoutRef.current);
    }

    // Set a new timeout for detailed data
    debounceTimeoutRef.current = setTimeout(() => {
      fetchDetailedUserData(user.id).then(detailedUser => {
        if (detailedUser) {
          // Only update if we're still looking at the same user
          setSelectedUser(currentUser => {
            if (currentUser && currentUser.id === detailedUser.id) {
              return detailedUser;
            }
            return currentUser;
          });
        }
      });
    }, 300); // 300ms delay
  }, [fetchDetailedUserData]);

  // Cleanup timeout on unmount
  useEffect(() => {
    return () => {
      if (debounceTimeoutRef.current) {
        clearTimeout(debounceTimeoutRef.current);
      }
    };
  }, []);

  // Memoized selection change handler to prevent infinite re-renders
  const handleSelectionChange = useCallback((selectedUsers: User[]) => {
    if (selectedUsers.length > 0) {
      const user = selectedUsers[0];
      // Use debounced fetch to prevent too many API calls during keyboard navigation
      debouncedFetchUserDetails(user);
    } else {
      setSelectedUser(null);
    }
  }, [debouncedFetchUserDetails]);

  // Memoized data loaded handler to prevent infinite re-renders
  const handleDataLoaded = useCallback((loadedUsers: User[]) => {
    setUsers(loadedUsers);
    setLoading(false);
  }, []);

  // Handle URL-based actions
  useEffect(() => {
    if (action === 'create') {
      setAddingNew(true);
      setSelectedUser(null);
      setEditingUser(null);
    } else if (action === 'edit' && id) {
      const user = users.find(u => u.id.toString() === id);
      if (user) {
        // Fetch detailed user data for editing
        fetchDetailedUserData(parseInt(id)).then(detailedUser => {
          if (detailedUser) {
            setEditingUser(detailedUser);
          } else {
            // Fallback to list data if detailed fetch fails
            setEditingUser(user);
          }
        });
        setSelectedUser(null);
        setAddingNew(false);
      }
    } else if (action === 'view' && id) {
      const user = users.find(u => u.id.toString() === id);
      if (user) {
        // Fetch detailed user data for viewing
        fetchDetailedUserData(parseInt(id)).then(detailedUser => {
          if (detailedUser) {
            setSelectedUser(detailedUser);
          } else {
            // Fallback to list data if detailed fetch fails
            setSelectedUser(user);
          }
        });
        setEditingUser(null);
        setAddingNew(false);
      }
    } else {
      setAddingNew(false);
      setSelectedUser(null);
      setEditingUser(null);
    }
  }, [action, id, users, fetchDetailedUserData]);

  const handleDeleteUser = async (userId?: number) => {
    const targetUser = userId ? users.find(u => u.id === userId) : selectedUser;
    if (!targetUser) return;
    
    const confirmDelete = window.confirm(
      `Are you sure you want to delete the user "${targetUser.username}"?\n\nThis action cannot be undone.`
    );
    
    if (!confirmDelete) return;
    
    try {
      await userApi.delete(targetUser.id);
      userListRef.current?.refresh();
      if (selectedUser?.id === targetUser.id) {
        setSelectedUser(null);
        navigate('/users');
      }
    } catch (error) {
      alert('Failed to delete user. Please try again.');
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
          .users-table-section {
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
          
          /* Apply same spacing to users table as form container */
          .users-table-section .user-data-grid {
            width: 100%;
            box-sizing: border-box;
            border: none;
          }
          
          /* Make AG-Grid components respect the container with proper spacing */
          .users-table-section .ag-grid-wrapper {
            width: calc(100% - 16px) !important;
            margin: 8px !important;
            box-sizing: border-box !important;
            border: none !important;
          }
          
          .users-table-section .ag-root-wrapper,
          .users-table-section .ag-root,
          .users-table-section .ag-body-viewport {
            width: 100% !important;
            max-width: 100% !important;
            box-sizing: border-box !important;
            overflow-x: hidden !important;
          }
          
          /* Override AG-Grid CSS variables to remove any shadow effects */
          .users-table-section .ag-theme-custom {
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
          .users-table-section .ag-header-cell {
            font-size: 11px !important;
            font-weight: 600 !important;
            color: #24292f !important;
            text-transform: uppercase !important;
            letter-spacing: 0.5px !important;
          }
          
          /* Remove any 3D effects and ensure clean borders */
          .users-table-section .ag-root-wrapper {
            border: none !important;
            border-radius: 0 !important;
            box-shadow: none !important;
            background: #ffffff !important;
            /* Remove any potential 3D effects */
            filter: none !important;
            transform: none !important;
          }
          
          .users-table-section .ag-root,
          .users-table-section .ag-body-viewport,
          .users-table-section .ag-grid-wrapper {
            background: transparent !important;
            border: none !important;
            box-shadow: none !important;
            border-radius: 0 !important;
            /* Remove any potential 3D effects */
            filter: none !important;
            transform: none !important;
          }
          
          /* Remove border radius from all table cells and headers */
          .users-table-section .ag-cell,
          .users-table-section .ag-header-cell {
            border-radius: 0 !important;
          }
        `}
      </style>

      {/* Header */}
      <div className="dashboard-header">
        <div className="header-left">
          <h1>User Management</h1>
        </div>
        <div className="header-stats">
          <button 
            className="btn-icon"
            onClick={() => navigate('/users/create')}
            title="Add new user"
            disabled={addingNew || !!editingUser}
          >
            <Plus size={18} />
          </button>
          {selectedUser && !addingNew && !editingUser && (
            <button 
              className="btn-icon"
              onClick={() => navigate(`/users/edit/${selectedUser.id}`)}
              title="Edit selected user"
            >
              <Edit3 size={18} />
            </button>
          )}
          {selectedUser && !addingNew && !editingUser && (
            <button 
              className="btn-icon btn-danger"
              onClick={() => handleDeleteUser()}
              title="Delete selected user"
            >
              <Trash2 size={18} />
            </button>
          )}

          <Link to="/users" className="stat-pill">
            <UsersIcon size={14} />
            <span>{users.length} Users</span>
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
        {/* Column 1: Users Data Grid */}
        <div className="dashboard-section users-table-section">
          <div className="section-header">
            Users ({users.length})
          </div>
          <UserDataGrid
            className="user-data-grid"
            ref={userListRef}
            onSelectionChanged={handleSelectionChange}
            onRowDoubleClicked={(user) => {
                navigate(`/users/edit/${user.id}`);
              }}
              onDataLoaded={handleDataLoaded}
            />
        </div>

        {/* Columns 2-3: User Details/Form Panel */}
        <div className="dashboard-section detail-grid-2col">
          {addingNew ? (
            <>
              <div className="section-header">
                <span>Create New User</span>
                <div style={{ display: 'flex', gap: '4px' }}>

                  <button 
                    className="btn-icon btn-ghost"
                    onClick={() => navigate('/users')}
                    title="Cancel"
                  >
                    <X size={16} />
                  </button>
                </div>
              </div>
              <UserSpreadsheetForm
                mode="create"
                onCancel={() => navigate('/users')}
                onSave={async (userData) => {
                  try {
                    await userApi.create(userData);
                    userListRef.current?.refresh();
                    navigate('/users');
                  } catch (error) {
                    alert('Failed to create user. Please try again.');
                  }
                }}
              />
            </>
          ) : editingUser ? (
            <>
              <div className="section-header">
                <span>Edit User: {editingUser.username}</span>
                <div style={{ display: 'flex', gap: '4px' }}>
                  <button 
                    className="btn-icon btn-ghost"
                    onClick={() => navigate('/users')}
                    title="Cancel"
                  >
                    <X size={16} />
                  </button>
                </div>
              </div>
              <UserSpreadsheetForm
                mode="edit"
                user={editingUser}
                onCancel={() => navigate('/users')}
                onSave={async (userData) => {
                  try {
                    await userApi.update(editingUser.id, userData);
                    userListRef.current?.refresh();
                    navigate('/users');
                  } catch (error) {
                    alert('Failed to update user. Please try again.');
                  }
                }}
              />
            </>
          ) : selectedUser ? (
            <>
              <div className="section-header">
                <span>User Details: {selectedUser.username || 'Unknown'}</span>
              </div>
              {loadingUserDetails ? (
                <div className="loading-state">
                  <p>Loading user details...</p>
                </div>
              ) : (
                <UserSpreadsheetForm
                  mode="view"
                  user={selectedUser}
                  onCancel={() => {}}
                  onSave={() => {}}
                />
              )}
            </>
          ) : loadingUserDetails ? (
            <>
              <div className="section-header">
                User Details
              </div>
              <div className="loading-state">
                <p>Loading user details...</p>
              </div>
            </>
          ) : (
            <>
              <div className="section-header">
                User Details
              </div>
              <div className="compact-content">
                <div className="empty-state">
                  <h3>Select a user</h3>
                  <p>Choose a user from the table to view their details.</p>
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