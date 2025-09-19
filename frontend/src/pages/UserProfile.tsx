import React, { useState, useEffect } from 'react';
import { useAuth } from '../contexts/AuthContext';
import { userApi } from '../services/api';
import { User } from '../types';
import { Users, Mail, Phone, Calendar, Shield, Edit3, Check, X } from 'lucide-react';

const UserProfile: React.FC = () => {
  const { user: currentUser } = useAuth();
  const [userProfile, setUserProfile] = useState<User | null>(null);
  const [loading, setLoading] = useState(true);
  const [editing, setEditing] = useState(false);
  const [saving, setSaving] = useState(false);
  const [formData, setFormData] = useState({
    first_name: '',
    last_name: '',
    email: '',
    telephone: '',
    title: '',
    password: '',
    confirmPassword: ''
  });

  useEffect(() => {
    if (currentUser) {
      fetchUserProfile();
    }
  }, [currentUser]);

  const fetchUserProfile = async () => {
    try {
      setLoading(true);
      const response = await userApi.get(currentUser!.id);
      const userData = (response as any).data || response;
      setUserProfile(userData);
      setFormData({
        first_name: userData.first_name || '',
        last_name: userData.last_name || '',
        email: userData.email || '',
        telephone: userData.telephone || '',
        title: userData.title || '',
        password: '',
        confirmPassword: ''
      });
    } catch (error) {
      console.error('Failed to fetch user profile:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleSave = async () => {
    // Validation
    if (!formData.email.trim()) {
      alert('Email is required');
      return;
    }
    if (formData.password && formData.password !== formData.confirmPassword) {
      alert('Passwords do not match');
      return;
    }
    if (formData.password && formData.password.length < 6) {
      alert('Password must be at least 6 characters long');
      return;
    }

    try {
      setSaving(true);
      const updateData: any = {
        first_name: formData.first_name,
        last_name: formData.last_name,
        email: formData.email,
        telephone: formData.telephone,
        title: formData.title
      };
      
      // Only include password if it was changed
      if (formData.password) {
        updateData.password = formData.password;
      }
      
      await userApi.update(currentUser!.id, updateData);
      await fetchUserProfile();
      setEditing(false);
      setFormData(prev => ({ ...prev, password: '', confirmPassword: '' }));
    } catch (error) {
      console.error('Failed to update profile:', error);
      alert('Failed to update profile');
    } finally {
      setSaving(false);
    }
  };

  const handleCancel = () => {
    setEditing(false);
    if (userProfile) {
      setFormData({
        first_name: userProfile.first_name || '',
        last_name: userProfile.last_name || '',
        email: userProfile.email || '',
        telephone: userProfile.telephone || '',
        title: userProfile.title || '',
        password: '',
        confirmPassword: ''
      });
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
          .profile-container {
            max-width: 800px;
            margin: 0 auto;
            padding: 24px;
          }
          
          .profile-header {
            display: flex;
            align-items: center;
            justify-content: space-between;
            margin-bottom: 32px;
            padding-bottom: 16px;
            border-bottom: 1px solid var(--neutral-200);
          }
          
          .profile-title {
            display: flex;
            align-items: center;
            gap: 12px;
          }
          
          .profile-title h1 {
            font-size: 24px;
            font-weight: 600;
            margin: 0;
            color: var(--neutral-800);
          }
          
          .profile-actions {
            display: flex;
            gap: 8px;
          }
          
          .profile-card {
            background: white;
            border: 1px solid var(--neutral-200);
            border-radius: 8px;
            padding: 24px;
            margin-bottom: 24px;
          }
          
          .card-title {
            font-size: 18px;
            font-weight: 600;
            color: var(--neutral-800);
            margin-bottom: 16px;
            display: flex;
            align-items: center;
            gap: 8px;
          }
          
          .profile-grid {
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 24px;
          }
          
          .form-field {
            margin-bottom: 16px;
          }
          
          .form-label {
            display: block;
            font-size: 14px;
            font-weight: 600;
            color: var(--neutral-700);
            margin-bottom: 6px;
          }
          
          .form-input {
            width: 100%;
            padding: 10px 12px;
            border: 1px solid var(--neutral-300);
            border-radius: 6px;
            font-size: 14px;
            color: var(--neutral-900);
            transition: border-color 0.2s;
          }
          
          .form-input:focus {
            outline: none;
            border-color: var(--primary-blue);
            box-shadow: 0 0 0 3px var(--primary-blue-light);
          }
          
          .form-input[readonly] {
            background-color: var(--neutral-50);
            color: var(--neutral-700);
            cursor: default;
          }
          
          .profile-info {
            display: flex;
            flex-direction: column;
            gap: 16px;
          }
          
          .info-item {
            display: flex;
            align-items: center;
            gap: 12px;
            padding: 12px;
            background: var(--neutral-50);
            border-radius: 6px;
          }
          
          .info-icon {
            color: var(--neutral-500);
          }
          
          .info-content {
            flex: 1;
          }
          
          .info-label {
            font-size: 12px;
            font-weight: 600;
            color: var(--neutral-500);
            text-transform: uppercase;
            letter-spacing: 0.5px;
            margin-bottom: 2px;
          }
          
          .info-value {
            font-size: 14px;
            color: var(--neutral-800);
          }
          
          .btn {
            padding: 8px 16px;
            border: none;
            border-radius: 6px;
            font-size: 14px;
            font-weight: 500;
            cursor: pointer;
            transition: all 0.2s;
            display: inline-flex;
            align-items: center;
            gap: 6px;
          }
          
          .btn-primary {
            background: var(--primary-blue);
            color: white;
          }
          
          .btn-primary:hover {
            background: var(--primary-blue-dark);
          }
          
          .btn-secondary {
            background: var(--neutral-200);
            color: var(--neutral-700);
          }
          
          .btn-secondary:hover {
            background: var(--neutral-300);
          }
          
          .btn:disabled {
            opacity: 0.5;
            cursor: not-allowed;
          }
        `}
      </style>

      <div className="profile-container">
        <div className="profile-header">
          <div className="profile-title">
            <Users size={28} />
            <h1>My Profile</h1>
          </div>
          <div className="profile-actions">
            {editing ? (
              <>
                <button 
                  className="btn btn-primary"
                  onClick={handleSave}
                  disabled={saving}
                >
                  <Check size={16} />
                  {saving ? 'Saving...' : 'Save Changes'}
                </button>
                <button 
                  className="btn btn-secondary"
                  onClick={handleCancel}
                  disabled={saving}
                >
                  <X size={16} />
                  Cancel
                </button>
              </>
            ) : (
              <button 
                className="btn btn-primary"
                onClick={() => setEditing(true)}
              >
                <Edit3 size={16} />
                Edit Profile
              </button>
            )}
          </div>
        </div>

        {editing ? (
          <div className="profile-card">
            <div className="card-title">
              <Edit3 size={20} />
              Edit Profile Information
            </div>
            <div className="profile-grid">
              <div>
                <div className="form-field">
                  <label className="form-label">First Name</label>
                  <input
                    type="text"
                    className="form-input"
                    value={formData.first_name}
                    onChange={(e) => setFormData(prev => ({ ...prev, first_name: e.target.value }))}
                    placeholder="Enter first name"
                  />
                </div>
                <div className="form-field">
                  <label className="form-label">Last Name</label>
                  <input
                    type="text"
                    className="form-input"
                    value={formData.last_name}
                    onChange={(e) => setFormData(prev => ({ ...prev, last_name: e.target.value }))}
                    placeholder="Enter last name"
                  />
                </div>
                <div className="form-field">
                  <label className="form-label">Email Address</label>
                  <input
                    type="email"
                    className="form-input"
                    value={formData.email}
                    onChange={(e) => setFormData(prev => ({ ...prev, email: e.target.value }))}
                    placeholder="Enter email address"
                  />
                </div>
              </div>
              <div>
                <div className="form-field">
                  <label className="form-label">Phone Number</label>
                  <input
                    type="tel"
                    className="form-input"
                    value={formData.telephone}
                    onChange={(e) => setFormData(prev => ({ ...prev, telephone: e.target.value }))}
                    placeholder="Enter phone number"
                  />
                </div>
                <div className="form-field">
                  <label className="form-label">Job Title</label>
                  <input
                    type="text"
                    className="form-input"
                    value={formData.title}
                    onChange={(e) => setFormData(prev => ({ ...prev, title: e.target.value }))}
                    placeholder="Enter job title"
                  />
                </div>
                <div className="form-field">
                  <label className="form-label">New Password (leave blank to keep current)</label>
                  <input
                    type="password"
                    className="form-input"
                    value={formData.password}
                    onChange={(e) => setFormData(prev => ({ ...prev, password: e.target.value }))}
                    placeholder="Enter new password"
                  />
                </div>
                {formData.password && (
                  <div className="form-field">
                    <label className="form-label">Confirm New Password</label>
                    <input
                      type="password"
                      className="form-input"
                      value={formData.confirmPassword}
                      onChange={(e) => setFormData(prev => ({ ...prev, confirmPassword: e.target.value }))}
                      placeholder="Confirm new password"
                    />
                  </div>
                )}
              </div>
            </div>
          </div>
        ) : (
          <>
            <div className="profile-card">
              <div className="card-title">
                <Users size={20} />
                Profile Information
              </div>
              <div className="profile-info">
                <div className="info-item">
                  <Users className="info-icon" size={20} />
                  <div className="info-content">
                    <div className="info-label">Full Name</div>
                    <div className="info-value">
                      {userProfile?.first_name || userProfile?.last_name 
                        ? `${userProfile?.first_name || ''} ${userProfile?.last_name || ''}`.trim()
                        : 'Not specified'
                      }
                    </div>
                  </div>
                </div>
                <div className="info-item">
                  <Mail className="info-icon" size={20} />
                  <div className="info-content">
                    <div className="info-label">Email Address</div>
                    <div className="info-value">{userProfile?.email || 'Not specified'}</div>
                  </div>
                </div>
                <div className="info-item">
                  <Phone className="info-icon" size={20} />
                  <div className="info-content">
                    <div className="info-label">Phone Number</div>
                    <div className="info-value">{userProfile?.telephone || 'Not specified'}</div>
                  </div>
                </div>
                <div className="info-item">
                  <Shield className="info-icon" size={20} />
                  <div className="info-content">
                    <div className="info-label">Role</div>
                    <div className="info-value">
                      {userProfile?.role ? (userProfile.role.charAt(0).toUpperCase() + userProfile.role.slice(1)) : 'Not specified'}
                    </div>
                  </div>
                </div>
                <div className="info-item">
                  <Calendar className="info-icon" size={20} />
                  <div className="info-content">
                    <div className="info-label">Member Since</div>
                    <div className="info-value">
                      {userProfile?.created_at 
                        ? new Date(userProfile.created_at).toLocaleDateString('en-US', {
                            year: 'numeric',
                            month: 'long',
                            day: 'numeric'
                          })
                        : 'Not available'
                      }
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </>
        )}
      </div>
    </div>
  );
};

export default UserProfile;