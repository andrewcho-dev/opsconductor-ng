import React, { useState, useEffect } from 'react';
import { stepLibraryService, LibraryInfo, LibraryInstallResult } from '../services/stepLibraryService';
import { BookOpen, Package, Calendar, Clock, Upload, CheckCircle, XCircle, AlertTriangle } from 'lucide-react';

const StepLibrarySettings: React.FC = () => {
  const [libraries, setLibraries] = useState<LibraryInfo[]>([]);
  const [loading, setLoading] = useState(true);
  const [installing, setInstalling] = useState(false);
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [licenseKey, setLicenseKey] = useState('');
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);
  const [activeTab, setActiveTab] = useState<'installed' | 'install'>('installed');

  useEffect(() => {
    loadLibraries();
  }, []);

  const loadLibraries = async () => {
    try {
      setLoading(true);
      const data = await stepLibraryService.getInstalledLibraries();
      
      // Ensure data is always an array
      const librariesArray = Array.isArray(data) ? data : [];
      setLibraries(librariesArray);
    } catch (error) {
      setError('Failed to load libraries');
      console.error('Error loading libraries:', error);
      setLibraries([]); // Set empty array on error
    } finally {
      setLoading(false);
    }
  };

  const handleFileSelect = (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (file) {
      if (file.name.endsWith('.zip')) {
        setSelectedFile(file);
        setError(null);
      } else {
        setError('Please select a ZIP file');
        setSelectedFile(null);
      }
    }
  };

  const handleInstall = async () => {
    if (!selectedFile) {
      setError('Please select a library file');
      return;
    }

    try {
      setInstalling(true);
      setError(null);
      
      const result: LibraryInstallResult = await stepLibraryService.installLibrary(
        selectedFile,
        licenseKey || undefined
      );

      setSuccess(`Successfully installed ${result.name} v${result.version} with ${result.step_count} steps`);
      setSelectedFile(null);
      setLicenseKey('');
      
      // Reset file input
      const fileInput = document.getElementById('library-file') as HTMLInputElement;
      if (fileInput) fileInput.value = '';

      // Reload libraries
      await loadLibraries();
      
    } catch (error: any) {
      setError(error.message || 'Failed to install library');
    } finally {
      setInstalling(false);
    }
  };

  const handleToggleLibrary = async (libraryId: number, enabled: boolean) => {
    try {
      await stepLibraryService.toggleLibrary(libraryId, enabled);
      await loadLibraries();
      setSuccess(`Library ${enabled ? 'enabled' : 'disabled'} successfully`);
    } catch (error: any) {
      setError(error.message || 'Failed to toggle library');
    }
  };

  const handleUninstall = async (libraryId: number, libraryName: string) => {
    if (!window.confirm(`Are you sure you want to uninstall "${libraryName}"? This action cannot be undone.`)) {
      return;
    }

    try {
      await stepLibraryService.uninstallLibrary(libraryId);
      await loadLibraries();
      setSuccess(`Successfully uninstalled ${libraryName}`);
    } catch (error: any) {
      setError(error.message || 'Failed to uninstall library');
    }
  };

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    });
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'installed':
      case 'enabled':
        return 'var(--success-green)';
      case 'disabled':
        return 'var(--neutral-500)';
      case 'error':
        return 'var(--danger-red)';
      case 'updating':
        return 'var(--warning-yellow)';
      default:
        return 'var(--primary-blue)';
    }
  };

  return (
    <div className="space-y-6">
      <style>
        {`
          .library-section {
            background: white;
            border: 1px solid var(--neutral-200);
            border-radius: 6px;
            overflow: hidden;
          }
          .library-header {
            background: var(--neutral-50);
            padding: 12px 16px;
            border-bottom: 1px solid var(--neutral-200);
            font-weight: 600;
            font-size: 14px;
            color: var(--neutral-700);
            display: flex;
            align-items: center;
            gap: 8px;
          }
          .library-content {
            padding: 16px;
          }
          .tab-nav {
            display: flex;
            border-bottom: 1px solid var(--neutral-200);
            background: var(--neutral-50);
          }
          .tab-button {
            padding: 10px 16px;
            border: none;
            background: transparent;
            color: var(--neutral-600);
            cursor: pointer;
            font-size: 12px;
            font-weight: 500;
            border-bottom: 2px solid transparent;
            transition: all 0.2s;
          }
          .tab-button.active {
            color: var(--primary-blue);
            border-bottom-color: var(--primary-blue);
            background: white;
          }
          .tab-button:hover:not(.active) {
            color: var(--neutral-700);
            background: var(--neutral-100);
          }
          .library-card {
            border: 1px solid var(--neutral-200);
            border-radius: 6px;
            padding: 16px;
            margin-bottom: 12px;
            background: white;
          }
          .library-card.disabled {
            background: var(--neutral-50);
            opacity: 0.8;
          }
          .library-info {
            display: flex;
            justify-content: space-between;
            align-items: flex-start;
            gap: 16px;
          }
          .library-details {
            flex: 1;
          }
          .library-title {
            font-size: 14px;
            font-weight: 600;
            color: var(--neutral-800);
            margin-bottom: 4px;
            display: flex;
            align-items: center;
            gap: 8px;
          }
          .premium-badge {
            background: var(--warning-yellow);
            color: var(--neutral-800);
            padding: 2px 6px;
            border-radius: 3px;
            font-size: 10px;
            font-weight: 600;
          }
          .status-badge {
            padding: 2px 8px;
            border-radius: 10px;
            font-size: 10px;
            font-weight: 500;
            text-transform: uppercase;
            color: white;
          }
          .library-meta {
            font-size: 11px;
            color: var(--neutral-600);
            margin-bottom: 6px;
          }
          .library-description {
            font-size: 12px;
            color: var(--neutral-600);
            margin-bottom: 10px;
          }
          .library-stats {
            display: flex;
            gap: 16px;
            font-size: 11px;
            color: var(--neutral-500);
            margin-bottom: 8px;
          }
          .stat-item {
            display: flex;
            align-items: center;
            gap: 4px;
          }
          .library-actions {
            display: flex;
            gap: 8px;
            align-items: flex-start;
          }
          .action-button {
            padding: 6px 12px;
            border: 1px solid var(--neutral-300);
            border-radius: 4px;
            font-size: 11px;
            font-weight: 500;
            cursor: pointer;
            transition: all 0.2s;
          }
          .action-button.enable {
            background: var(--success-green);
            color: white;
            border-color: var(--success-green);
          }
          .action-button.disable {
            background: var(--warning-orange);
            color: white;
            border-color: var(--warning-orange);
          }
          .action-button.uninstall {
            background: white;
            color: var(--danger-red);
            border-color: var(--danger-red);
          }
          .action-button:hover {
            opacity: 0.8;
          }
          .install-section {
            max-width: 600px;
            margin: 0 auto;
          }
          .upload-area {
            border: 2px dashed var(--neutral-300);
            border-radius: 6px;
            padding: 32px;
            text-align: center;
            margin-bottom: 16px;
            transition: border-color 0.2s;
          }
          .upload-area:hover {
            border-color: var(--primary-blue);
          }
          .upload-icon {
            color: var(--neutral-400);
            margin-bottom: 12px;
          }
          .upload-title {
            font-size: 14px;
            font-weight: 600;
            color: var(--neutral-700);
            margin-bottom: 8px;
          }
          .upload-description {
            font-size: 11px;
            color: var(--neutral-500);
            margin-bottom: 16px;
          }
          .file-input {
            margin-bottom: 16px;
          }
          .file-preview {
            background: var(--primary-blue-light);
            padding: 12px;
            border-radius: 4px;
            margin-bottom: 16px;
            text-align: left;
            font-size: 11px;
          }
          .form-input {
            width: 100%;
            padding: 8px 12px;
            border: 1px solid var(--neutral-300);
            border-radius: 4px;
            font-size: 12px;
            margin-bottom: 16px;
          }
          .form-input:focus {
            outline: none;
            border-color: var(--primary-blue);
            box-shadow: 0 0 0 2px var(--primary-blue-light);
          }
          .install-button {
            background: var(--primary-blue);
            color: white;
            border: none;
            padding: 10px 20px;
            border-radius: 4px;
            font-size: 12px;
            font-weight: 500;
            cursor: pointer;
            display: flex;
            align-items: center;
            gap: 8px;
            margin: 0 auto;
          }
          .install-button:disabled {
            background: var(--neutral-400);
            cursor: not-allowed;
          }
          .install-button:hover:not(:disabled) {
            background: var(--primary-blue-hover);
          }
          .requirements-section {
            background: var(--neutral-50);
            padding: 16px;
            border-radius: 6px;
            font-size: 11px;
            color: var(--neutral-600);
          }
          .requirements-title {
            font-size: 12px;
            font-weight: 600;
            color: var(--neutral-700);
            margin-bottom: 8px;
            display: flex;
            align-items: center;
            gap: 6px;
          }
          .status-message {
            padding: 12px;
            border-radius: 4px;
            font-size: 12px;
            margin-bottom: 16px;
            display: flex;
            align-items: center;
            gap: 8px;
          }
          .status-success {
            background: var(--success-green-light);
            color: var(--success-green-dark);
            border: 1px solid var(--success-green);
          }
          .status-error {
            background: var(--danger-red-light);
            color: var(--danger-red);
            border: 1px solid var(--danger-red);
          }
          .empty-state {
            text-align: center;
            padding: 40px;
            color: var(--neutral-500);
          }
          .empty-icon {
            color: var(--neutral-300);
            margin-bottom: 16px;
          }
          .spinner {
            width: 14px;
            height: 14px;
            border: 2px solid transparent;
            border-top: 2px solid currentColor;
            border-radius: 50%;
            animation: spin 1s linear infinite;
          }
          @keyframes spin {
            to { transform: rotate(360deg); }
          }
        `}
      </style>

      {error && (
        <div className="status-message status-error">
          <XCircle size={14} />
          {error}
        </div>
      )}

      {success && (
        <div className="status-message status-success">
          <CheckCircle size={14} />
          {success}
        </div>
      )}

      <div className="library-section">
        <div className="library-header">
          <BookOpen size={16} />
          Step Library Management
        </div>
        
        <div className="tab-nav">
          <button
            onClick={() => setActiveTab('installed')}
            className={`tab-button ${activeTab === 'installed' ? 'active' : ''}`}
          >
            Installed Libraries ({libraries.length})
          </button>
          <button
            onClick={() => setActiveTab('install')}
            className={`tab-button ${activeTab === 'install' ? 'active' : ''}`}
          >
            Install New Library
          </button>
        </div>

        <div className="library-content">
          {activeTab === 'installed' && (
            <div>
              {loading ? (
                <div className="empty-state">
                  <div className="spinner"></div>
                  Loading libraries...
                </div>
              ) : libraries.length === 0 ? (
                <div className="empty-state">
                  <div className="empty-icon">
                    <BookOpen size={48} />
                  </div>
                  <div>No libraries installed</div>
                  <div style={{ fontSize: '11px', marginTop: '8px' }}>
                    Switch to "Install New Library" tab to add libraries
                  </div>
                </div>
              ) : (
                <div>
                  {libraries.map((library) => (
                    <div
                      key={library.id}
                      className={`library-card ${!library.is_active ? 'disabled' : ''}`}
                    >
                      <div className="library-info">
                        <div className="library-details">
                          <div className="library-title">
                            {library.display_name || library.name}
                            {library.is_premium && (
                              <span className="premium-badge">PREMIUM</span>
                            )}
                            <span 
                              className="status-badge" 
                              style={{ backgroundColor: getStatusColor(library.is_active ? 'active' : 'inactive') }}
                            >
                              {library.is_active ? 'Active' : 'Inactive'}
                            </span>
                          </div>
                          
                          <div className="library-meta">
                            v{library.version} by {library.author || 'Unknown'}
                          </div>
                          
                          <div className="library-description">
                            {library.description}
                          </div>
                          
                          <div className="library-stats">
                            <span className="stat-item">
                              <Package size={12} /> {library.step_count || 0} steps
                            </span>
                            <span className="stat-item">
                              <Calendar size={12} /> Installed {formatDate(library.installation_date || library.created_at)}
                            </span>
                            {library.last_used && (
                              <span className="stat-item">
                                <Clock size={12} /> Last used {formatDate(library.last_used)}
                              </span>
                            )}
                          </div>
                        </div>
                        
                        <div className="library-actions">
                          <button
                            onClick={() => handleToggleLibrary(library.id, !library.is_active)}
                            className={`action-button ${library.is_active ? 'disable' : 'enable'}`}
                          >
                            {library.is_active ? 'Disable' : 'Enable'}
                          </button>
                          
                          {library.name !== 'core' && (
                            <button
                              onClick={() => handleUninstall(library.id, library.display_name || library.name)}
                              className="action-button uninstall"
                            >
                              Uninstall
                            </button>
                          )}
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>
          )}

          {activeTab === 'install' && (
            <div className="install-section">
              <div className="upload-area">
                <div className="upload-icon">
                  <Upload size={48} />
                </div>
                <div className="upload-title">Install Step Library</div>
                <div className="upload-description">
                  Upload a ZIP file containing a step library package
                </div>
                
                <input
                  id="library-file"
                  type="file"
                  accept=".zip"
                  onChange={handleFileSelect}
                  className="file-input"
                />
                
                {selectedFile && (
                  <div className="file-preview">
                    <strong>Selected file:</strong> {selectedFile.name}<br />
                    <strong>Size:</strong> {(selectedFile.size / 1024 / 1024).toFixed(2)} MB
                  </div>
                )}
                
                <input
                  type="text"
                  placeholder="License key (for premium libraries)"
                  value={licenseKey}
                  onChange={(e) => setLicenseKey(e.target.value)}
                  className="form-input"
                />
                
                <button
                  onClick={handleInstall}
                  disabled={!selectedFile || installing}
                  className="install-button"
                >
                  {installing ? (
                    <>
                      <div className="spinner"></div>
                      Installing
                    </>
                  ) : (
                    <>
                      <Package size={14} />
                      Install Library
                    </>
                  )}
                </button>
              </div>
              
              <div className="requirements-section">
                <div className="requirements-title">
                  <AlertTriangle size={14} />
                  Installation Requirements
                </div>
                <ul style={{ marginBottom: 0, paddingLeft: '20px' }}>
                  <li>Library must be packaged as a ZIP file</li>
                  <li>Must contain a valid manifest.json file</li>
                  <li>Premium libraries require a valid license key</li>
                  <li>Library will be validated before installation</li>
                </ul>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default StepLibrarySettings;