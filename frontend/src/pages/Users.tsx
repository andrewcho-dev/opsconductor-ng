import React, { useState, useEffect, useRef } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import { Plus, Users as UsersIcon, Target, Settings, Play, MessageSquare, Upload, Download, X, Check, Edit3 } from 'lucide-react';
import { Link } from 'react-router-dom';
import { userApi } from '../services/api';
import UserTableList, { UserTableListRef } from '../components/UserTableList';
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
  const userListRef = useRef<UserTableListRef>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  // Fetch detailed user data
  const fetchDetailedUserData = async (userId: number): Promise<User | null> => {
    try {
      setLoadingUserDetails(true);
      console.log('Fetching detailed user data for ID:', userId);
      const response = await userApi.get(userId);
      console.log('Raw API response:', response);
      
      const userData = (response as any).data || response;
      console.log('Extracted user data:', userData);
      
      return userData;
    } catch (error) {
      console.error('Failed to fetch detailed user data:', error);
      return null;
    } finally {
      setLoadingUserDetails(false);
    }
  };

  // CSV field definitions for user import/export
  const csvFields = [
    // Basic Information
    { field: 'username', label: 'Username' },
    { field: 'email', label: 'Email Address' },
    { field: 'first_name', label: 'First Name' },
    { field: 'last_name', label: 'Last Name' },
    
    // Contact Information
    { field: 'telephone', label: 'Phone Number' },
    { field: 'title', label: 'Job Title' },
    
    // Authentication
    { field: 'role', label: 'Role' },
    { field: 'password', label: 'Password' },
    
    // Status
    { field: 'is_active', label: 'Active Status' }
  ];

  const [pagination, setPagination] = useState({
    page: 1,
    limit: 20,
    total: 0,
    totalPages: 0
  });

  // Export CSV template
  const handleExportTemplate = () => {
    const headers = csvFields.map(field => field.label);
    
    // Example row with sample data
    const exampleRow = csvFields.map(field => {
      switch (field.field) {
        case 'username': return 'john.doe';
        case 'email': return 'john.doe@company.com';
        case 'first_name': return 'John';
        case 'last_name': return 'Doe';
        case 'telephone': return '+1 (555) 123-4567';
        case 'title': return 'System Administrator';
        case 'role': return 'operator';
        case 'password': return 'secure_password_123';
        case 'is_active': return 'true';
        default: return '';
      }
    });
    
    // Comments row explaining valid values
    const commentsRow = csvFields.map(field => {
      switch (field.field) {
        case 'username': return 'REQUIRED - Unique username for login';
        case 'email': return 'REQUIRED - Valid email address';
        case 'first_name': return 'Optional - User\'s first name';
        case 'last_name': return 'Optional - User\'s last name';
        case 'telephone': return 'Optional - Phone number';
        case 'title': return 'Optional - Job title or position';
        case 'role': return 'REQUIRED - Valid roles: admin, manager, operator, developer, viewer';
        case 'password': return 'REQUIRED - Minimum 6 characters (will be encrypted)';
        case 'is_active': return 'Optional - true/false, default: true';
        default: return 'Optional field';
      }
    });
    
    // Build CSV content with headers, example, and comments
    const csvLines = [
      headers.join(','),
      '# EXAMPLE ROW (delete this line and add your data below):',
      '#' + exampleRow.map(value => {
        // Escape commas and quotes in CSV
        if (typeof value === 'string' && (value.includes(',') || value.includes('"'))) {
          return `"${value.replace(/"/g, '""')}"`;
        }
        return value;
      }).join(','),
      '',
      '# FIELD VALIDATION RULES AND EXAMPLES:',
      '#' + commentsRow.map(comment => `"${comment}"`).join(','),
      '',
      '# DELETE ALL LINES STARTING WITH # AND ADD YOUR USER DATA BELOW:'
    ];
    
    const csvContent = csvLines.join('\n');
    
    const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' });
    const link = document.createElement('a');
    const url = URL.createObjectURL(blob);
    link.setAttribute('href', url);
    link.setAttribute('download', 'user_import_template.csv');
    link.style.visibility = 'hidden';
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  };

  // Export current users
  const handleExportUsers = () => {
    const headers = csvFields.map(field => field.label);
    const rows = users.map(user => {
      return csvFields.map(field => {
        let value = user[field.field as keyof User] || '';
        
        // Handle special formatting
        if (field.field === 'password') {
          value = '••••••••'; // Don't export actual passwords
        }
        
        // Escape commas and quotes in CSV
        if (typeof value === 'string' && (value.includes(',') || value.includes('"'))) {
          value = `"${value.replace(/"/g, '""')}"`;
        }
        
        return value;
      });
    });
    
    const csvContent = [headers, ...rows].map(row => row.join(',')).join('\n');
    
    const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' });
    const link = document.createElement('a');
    const url = URL.createObjectURL(blob);
    link.setAttribute('href', url);
    link.setAttribute('download', `users_export_${new Date().toISOString().split('T')[0]}.csv`);
    link.style.visibility = 'hidden';
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  };

  // Import CSV file
  const handleImportClick = () => {
    fileInputRef.current?.click();
  };

  const handleFileImport = (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (!file) return;

    const reader = new FileReader();
    reader.onload = async (e) => {
      try {
        const csvContent = e.target?.result as string;
        const lines = csvContent.split('\n').filter(line => line.trim() && !line.startsWith('#'));
        
        if (lines.length < 2) {
          alert('CSV file must contain at least a header row and one data row');
          return;
        }

        const headers = lines[0].split(',').map(h => h.trim().replace(/"/g, ''));
        const dataLines = lines.slice(1);

        const importedUsers: any[] = [];
        const errors: string[] = [];

        for (let i = 0; i < dataLines.length; i++) {
          const values = dataLines[i].split(',').map(v => v.trim().replace(/"/g, ''));
          
          if (values.length !== headers.length) {
            errors.push(`Row ${i + 1}: Column count mismatch`);
            continue;
          }

          const userData: any = {};
          headers.forEach((header, index) => {
            const field = csvFields.find(f => f.label === header);
            if (field) {
              let value = values[index];
              
              // Handle boolean fields
              if (field.field === 'is_active') {
                userData[field.field] = value.toLowerCase() === 'true';
              } else {
                userData[field.field] = value;
              }
            }
          });

          // Validation
          if (!userData.username?.trim()) {
            errors.push(`Row ${i + 1}: Username is required`);
            continue;
          }
          if (!userData.email?.trim()) {
            errors.push(`Row ${i + 1}: Email is required`);
            continue;
          }
          if (!userData.password?.trim()) {
            errors.push(`Row ${i + 1}: Password is required`);
            continue;
          }
          if (!userData.role?.trim()) {
            errors.push(`Row ${i + 1}: Role is required`);
            continue;
          }

          // Email validation
          if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(userData.email)) {
            errors.push(`Row ${i + 1}: Invalid email format`);
            continue;
          }

          // Role validation
          const validRoles = ['admin', 'manager', 'operator', 'developer', 'viewer'];
          if (!validRoles.includes(userData.role.toLowerCase())) {
            errors.push(`Row ${i + 1}: Invalid role. Must be one of: ${validRoles.join(', ')}`);
            continue;
          }

          importedUsers.push(userData);
        }

        if (errors.length > 0) {
          alert(`Import errors:\n${errors.join('\n')}`);
          return;
        }

        // Import users
        let successCount = 0;
        for (const userData of importedUsers) {
          try {
            await userApi.create(userData);
            successCount++;
          } catch (error) {
            console.error('Failed to import user:', error);
          }
        }

        alert(`Successfully imported ${successCount} out of ${importedUsers.length} users`);
        userListRef.current?.refresh(); // Refresh the list
        
      } catch (error) {
        console.error('Import error:', error);
        alert('Failed to parse CSV file. Please check the format.');
      }
    };

    reader.readAsText(file);
    event.target.value = ''; // Reset file input
  };

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
  }, [action, id, users]);

  const handleDeleteUser = async (userId: number) => {
    if (!window.confirm('Are you sure you want to delete this user?')) return;
    
    try {
      await userApi.delete(userId);
      userListRef.current?.refresh();
      if (selectedUser?.id === userId) {
        setSelectedUser(null);
        navigate('/users');
      }
    } catch (error) {
      console.error('Failed to delete user:', error);
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
          }
          .detail-grid-2col {
            grid-column: 2 / 4;
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
            <Plus size={16} />
          </button>
          {selectedUser && !addingNew && !editingUser && (
            <button 
              className="btn-icon"
              onClick={() => navigate(`/users/edit/${selectedUser.id}`)}
              title="Edit selected user"
            >
              <Edit3 size={16} />
            </button>
          )}
          <div className="dropdown">
            <button 
              className="btn-icon dropdown-toggle"
              title="Export options"
              disabled={addingNew || !!editingUser}
            >
              <Upload size={16} />
            </button>
            <div className="dropdown-menu">
              <button onClick={handleExportTemplate} className="dropdown-item">
                Export Template
              </button>
              <button onClick={handleExportUsers} className="dropdown-item">
                Export Current Users
              </button>
            </div>
          </div>
          <button 
            className="btn-icon"
            onClick={handleImportClick}
            title="Import from CSV"
            disabled={addingNew || !!editingUser}
          >
            <Download size={16} />
          </button>
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
          <div className="compact-content">
            <UserTableList
              ref={userListRef}
              onSelectionChanged={(selectedUsers) => {
                if (selectedUsers.length > 0) {
                  const user = selectedUsers[0];
                  console.log('User selection changed to:', user.username, 'ID:', user.id);
                  
                  // Fetch detailed user data when selecting from list
                  fetchDetailedUserData(user.id).then(detailedUser => {
                    console.log('Detailed user data loaded for:', detailedUser?.username);
                    if (detailedUser) {
                      setSelectedUser(detailedUser);
                    } else {
                      // Fallback to list data if detailed fetch fails
                      setSelectedUser(user);
                    }
                  });
                } else {
                  console.log('User selection cleared');
                  setSelectedUser(null);
                }
              }}
              onRowDoubleClicked={(user) => {
                navigate(`/users/edit/${user.id}`);
              }}
              onDataLoaded={(loadedUsers) => {
                setUsers(loadedUsers);
                setLoading(false);
              }}
              onEditUser={(user) => {
                navigate(`/users/edit/${user.id}`);
              }}
              onDeleteUser={handleDeleteUser}
            />
          </div>
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
              <div className="compact-content">
                <UserSpreadsheetForm
                  mode="create"
                  onCancel={() => navigate('/users')}
                  onSave={async (userData) => {
                    try {
                      await userApi.create(userData);
                      userListRef.current?.refresh();
                      navigate('/users');
                    } catch (error) {
                      console.error('Failed to create user:', error);
                      alert('Failed to create user. Please try again.');
                    }
                  }}
                />
              </div>
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
              <div className="compact-content">
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
                      console.error('Failed to update user:', error);
                      alert('Failed to update user. Please try again.');
                    }
                  }}
                />
              </div>
            </>
          ) : selectedUser ? (
            <>
              <div className="section-header">
                User Details: {selectedUser.username}
              </div>
              <div className="compact-content">
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
              </div>
            </>
          ) : loadingUserDetails ? (
            <>
              <div className="section-header">
                User Details
              </div>
              <div className="compact-content">
                <div className="loading-state">
                  <p>Loading user details...</p>
                </div>
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
      
      {/* Hidden file input for CSV import */}
      <input
        type="file"
        ref={fileInputRef}
        onChange={handleFileImport}
        accept=".csv"
        style={{ display: 'none' }}
      />
    </div>
  );
};

export default Users;