import React, { useState, useEffect } from 'react';
import { stepLibraryService, LibraryInfo, LibraryInstallResult } from '../services/stepLibraryService';
import { X, BookOpen, Package, Calendar, Clock, Clipboard } from 'lucide-react';

interface LibraryManagerProps {
  onClose: () => void;
}

const LibraryManager: React.FC<LibraryManagerProps> = ({ onClose }) => {
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
      setLibraries(data);
    } catch (error) {
      setError('Failed to load libraries');
      console.error('Error loading libraries:', error);
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
        return '#28a745';
      case 'disabled':
        return '#6c757d';
      case 'error':
        return '#dc3545';
      case 'updating':
        return '#ffc107';
      default:
        return '#007bff';
    }
  };

  return (
    <div style={{
      position: 'fixed',
      top: 0,
      left: 0,
      right: 0,
      bottom: 0,
      backgroundColor: 'rgba(0, 0, 0, 0.5)',
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'center',
      zIndex: 1000
    }}>
      <div style={{
        backgroundColor: 'white',
        borderRadius: '8px',
        width: '90%',
        maxWidth: '1000px',
        height: '80%',
        display: 'flex',
        flexDirection: 'column',
        boxShadow: '0 4px 20px rgba(0, 0, 0, 0.15)'
      }}>
        {/* Header */}
        <div style={{
          padding: '20px',
          borderBottom: '1px solid #ddd',
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center'
        }}>
          <h2 style={{ margin: 0, color: '#333', display: 'flex', alignItems: 'center', gap: '8px' }}><BookOpen size={24} /> Step Library Manager</h2>
          <button
            onClick={onClose}
            style={{
              background: 'none',
              border: 'none',
              fontSize: '24px',
              cursor: 'pointer',
              color: '#666'
            }}
          >
            <X size={20} />
          </button>
        </div>

        {/* Tabs */}
        <div style={{
          display: 'flex',
          borderBottom: '1px solid #ddd'
        }}>
          <button
            onClick={() => setActiveTab('installed')}
            style={{
              padding: '12px 24px',
              border: 'none',
              background: activeTab === 'installed' ? '#007bff' : 'transparent',
              color: activeTab === 'installed' ? 'white' : '#666',
              cursor: 'pointer',
              borderBottom: activeTab === 'installed' ? '2px solid #007bff' : 'none'
            }}
          >
            Installed Libraries ({libraries.length})
          </button>
          <button
            onClick={() => setActiveTab('install')}
            style={{
              padding: '12px 24px',
              border: 'none',
              background: activeTab === 'install' ? '#007bff' : 'transparent',
              color: activeTab === 'install' ? 'white' : '#666',
              cursor: 'pointer',
              borderBottom: activeTab === 'install' ? '2px solid #007bff' : 'none'
            }}
          >
            Install New Library
          </button>
        </div>

        {/* Content */}
        <div style={{ flex: 1, padding: '20px', overflow: 'auto' }}>
          {/* Error/Success Messages */}
          {error && (
            <div style={{
              backgroundColor: '#f8d7da',
              color: '#721c24',
              padding: '12px',
              borderRadius: '4px',
              marginBottom: '16px',
              border: '1px solid #f5c6cb'
            }}>
              {error}
              <button
                onClick={() => setError(null)}
                style={{
                  float: 'right',
                  background: 'none',
                  border: 'none',
                  color: '#721c24',
                  cursor: 'pointer'
                }}
              >
                <X size={20} />
              </button>
            </div>
          )}

          {success && (
            <div style={{
              backgroundColor: '#d4edda',
              color: '#155724',
              padding: '12px',
              borderRadius: '4px',
              marginBottom: '16px',
              border: '1px solid #c3e6cb'
            }}>
              {success}
              <button
                onClick={() => setSuccess(null)}
                style={{
                  float: 'right',
                  background: 'none',
                  border: 'none',
                  color: '#155724',
                  cursor: 'pointer'
                }}
              >
                <X size={20} />
              </button>
            </div>
          )}

          {/* Installed Libraries Tab */}
          {activeTab === 'installed' && (
            <div>
              {loading ? (
                <div style={{ textAlign: 'center', padding: '40px' }}>
                  <div>Loading libraries...</div>
                </div>
              ) : libraries.length === 0 ? (
                <div style={{ textAlign: 'center', padding: '40px', color: '#666' }}>
                  <div style={{ marginBottom: '16px', display: 'flex', justifyContent: 'center' }}><BookOpen size={48} /></div>
                  <div>No libraries installed</div>
                  <div style={{ fontSize: '14px', marginTop: '8px' }}>
                    Switch to the "Install New Library" tab to add libraries
                  </div>
                </div>
              ) : (
                <div style={{ display: 'grid', gap: '16px' }}>
                  {libraries.map((library) => (
                    <div
                      key={library.id}
                      style={{
                        border: '1px solid #ddd',
                        borderRadius: '8px',
                        padding: '16px',
                        backgroundColor: library.is_enabled ? '#f8f9fa' : '#f5f5f5'
                      }}
                    >
                      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
                        <div style={{ flex: 1 }}>
                          <div style={{ display: 'flex', alignItems: 'center', gap: '12px', marginBottom: '8px' }}>
                            <h3 style={{ margin: 0, color: '#333' }}>
                              {library.display_name}
                              {library.is_premium && (
                                <span style={{
                                  marginLeft: '8px',
                                  backgroundColor: '#ffc107',
                                  color: '#212529',
                                  padding: '2px 6px',
                                  borderRadius: '4px',
                                  fontSize: '12px',
                                  fontWeight: 'bold'
                                }}>
                                  PREMIUM
                                </span>
                              )}
                            </h3>
                            <span style={{
                              backgroundColor: getStatusColor(library.status),
                              color: 'white',
                              padding: '2px 8px',
                              borderRadius: '12px',
                              fontSize: '12px',
                              textTransform: 'uppercase'
                            }}>
                              {library.status}
                            </span>
                          </div>
                          
                          <div style={{ color: '#666', marginBottom: '8px' }}>
                            v{library.version} by {library.author}
                          </div>
                          
                          <div style={{ color: '#666', marginBottom: '12px' }}>
                            {library.description}
                          </div>
                          
                          <div style={{ display: 'flex', gap: '16px', fontSize: '14px', color: '#666' }}>
                            <span style={{ display: 'flex', alignItems: 'center', gap: '4px' }}><Package size={14} /> {library.step_count} steps</span>
                            <span style={{ display: 'flex', alignItems: 'center', gap: '4px' }}><Calendar size={14} /> Installed {formatDate(library.installation_date)}</span>
                            {library.last_used && (
                              <span style={{ display: 'flex', alignItems: 'center', gap: '4px' }}><Clock size={14} /> Last used {formatDate(library.last_used)}</span>
                            )}
                          </div>
                        </div>
                        
                        <div style={{ display: 'flex', gap: '8px', marginLeft: '16px' }}>
                          <button
                            onClick={() => handleToggleLibrary(library.id, !library.is_enabled)}
                            style={{
                              padding: '6px 12px',
                              border: '1px solid #ddd',
                              borderRadius: '4px',
                              backgroundColor: library.is_enabled ? '#dc3545' : '#28a745',
                              color: 'white',
                              cursor: 'pointer',
                              fontSize: '12px'
                            }}
                          >
                            {library.is_enabled ? 'Disable' : 'Enable'}
                          </button>
                          
                          {library.name !== 'core' && (
                            <button
                              onClick={() => handleUninstall(library.id, library.display_name)}
                              style={{
                                padding: '6px 12px',
                                border: '1px solid #dc3545',
                                borderRadius: '4px',
                                backgroundColor: 'white',
                                color: '#dc3545',
                                cursor: 'pointer',
                                fontSize: '12px'
                              }}
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

          {/* Install New Library Tab */}
          {activeTab === 'install' && (
            <div style={{ maxWidth: '600px', margin: '0 auto' }}>
              <div style={{
                border: '2px dashed #ddd',
                borderRadius: '8px',
                padding: '40px',
                textAlign: 'center',
                marginBottom: '24px'
              }}>
                <div style={{ marginBottom: '16px', display: 'flex', justifyContent: 'center' }}><Package size={48} /></div>
                <h3 style={{ marginBottom: '16px' }}>Install Step Library</h3>
                <p style={{ color: '#666', marginBottom: '24px' }}>
                  Upload a ZIP file containing a step library package
                </p>
                
                <input
                  id="library-file"
                  type="file"
                  accept=".zip"
                  onChange={handleFileSelect}
                  style={{ marginBottom: '16px' }}
                />
                
                {selectedFile && (
                  <div style={{
                    backgroundColor: '#e7f3ff',
                    padding: '12px',
                    borderRadius: '4px',
                    marginBottom: '16px',
                    textAlign: 'left'
                  }}>
                    <strong>Selected file:</strong> {selectedFile.name}<br />
                    <strong>Size:</strong> {(selectedFile.size / 1024 / 1024).toFixed(2)} MB
                  </div>
                )}
                
                <div style={{ marginBottom: '16px' }}>
                  <input
                    type="text"
                    placeholder="License key (for premium libraries)"
                    value={licenseKey}
                    onChange={(e) => setLicenseKey(e.target.value)}
                    style={{
                      width: '100%',
                      padding: '8px 12px',
                      border: '1px solid #ddd',
                      borderRadius: '4px',
                      fontSize: '14px'
                    }}
                  />
                </div>
                
                <button
                  onClick={handleInstall}
                  disabled={!selectedFile || installing}
                  style={{
                    padding: '12px 24px',
                    backgroundColor: selectedFile && !installing ? '#007bff' : '#6c757d',
                    color: 'white',
                    border: 'none',
                    borderRadius: '4px',
                    cursor: selectedFile && !installing ? 'pointer' : 'not-allowed',
                    fontSize: '16px'
                  }}
                >
                  {installing ? 'Installing...' : 'Install Library'}
                </button>
              </div>
              
              <div style={{
                backgroundColor: '#f8f9fa',
                padding: '16px',
                borderRadius: '8px',
                fontSize: '14px',
                color: '#666'
              }}>
                <h4 style={{ marginTop: 0, color: '#333', display: 'flex', alignItems: 'center', gap: '6px' }}><Clipboard size={16} /> Installation Requirements</h4>
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

export default LibraryManager;