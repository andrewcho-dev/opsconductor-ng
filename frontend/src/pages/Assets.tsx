import React, { useState, useEffect, useRef } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import { Plus, Server, Monitor, HardDrive, Wifi, WifiOff, Eye, Edit3, Trash2, X, Check, Users, Target, Settings, Play, MessageSquare, Upload, Download } from 'lucide-react';
import { Link } from 'react-router-dom';
import { assetApi } from '../services/api';
import AssetTableList, { AssetTableListRef } from '../components/AssetTableList';
import AssetSpreadsheetForm from '../components/AssetSpreadsheetForm';
import { Asset } from '../types/asset';



const Assets: React.FC = () => {
  const navigate = useNavigate();
  const { action, id } = useParams<{ action?: string; id?: string }>();
  
  const [assets, setAssets] = useState<Asset[]>([]);
  const [loading, setLoading] = useState(true);
  const [selectedAsset, setSelectedAsset] = useState<Asset | null>(null);
  const [editingAsset, setEditingAsset] = useState<Asset | null>(null);
  const [addingNew, setAddingNew] = useState(false);
  const [loadingAssetDetails, setLoadingAssetDetails] = useState(false);
  const assetListRef = useRef<AssetTableListRef>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  // Fetch detailed asset data (includes credential information)
  const fetchDetailedAssetData = async (assetId: number): Promise<Asset | null> => {
    try {
      setLoadingAssetDetails(true);
      console.log('Fetching detailed asset data for ID:', assetId);
      const response = await assetApi.get(assetId);
      console.log('Raw API response:', response);
      
      // The API returns {success: true, data: {...}}, so we need response.data
      const assetData = response.data || response;
      console.log('Extracted asset data:', assetData);
      console.log('Asset credential_type:', assetData.credential_type);
      
      return assetData;
    } catch (error) {
      console.error('Failed to fetch detailed asset data:', error);
      return null;
    } finally {
      setLoadingAssetDetails(false);
    }
  };

  // CSV field definitions in import/export order (ALL fields supported by backend)
  const csvFields = [
    // Basic Information
    { field: 'name', label: 'Asset Name' },
    { field: 'hostname', label: 'Hostname' },
    { field: 'ip_address', label: 'IP Address' },
    { field: 'description', label: 'Description' },
    { field: 'device_type', label: 'Device Type' },
    { field: 'tags', label: 'Tags' },
    
    // Location Information
    { field: 'physical_address', label: 'Physical Address' },
    { field: 'data_center', label: 'Data Center' },
    { field: 'building', label: 'Building' },
    { field: 'room', label: 'Room' },
    { field: 'rack_position', label: 'Rack Position' },
    { field: 'rack_location', label: 'Rack Location' },
    { field: 'gps_coordinates', label: 'GPS Coordinates' },
    
    // Hardware Information
    { field: 'hardware_make', label: 'Hardware Make' },
    { field: 'hardware_model', label: 'Hardware Model' },
    { field: 'serial_number', label: 'Serial Number' },
    
    // System Information
    { field: 'os_type', label: 'OS Type' },
    { field: 'os_version', label: 'OS Version' },
    
    // Status & Management
    { field: 'status', label: 'Status' },
    { field: 'environment', label: 'Environment' },
    { field: 'criticality', label: 'Criticality' },
    { field: 'owner', label: 'Owner' },
    { field: 'support_contact', label: 'Support Contact' },
    { field: 'contract_number', label: 'Contract Number' },
    
    // Primary Communication Service
    { field: 'service_type', label: 'Service Type' },
    { field: 'port', label: 'Port' },
    { field: 'is_secure', label: 'Is Secure' },
    
    // Primary Service Credentials
    { field: 'credential_type', label: 'Credential Type' },
    { field: 'username', label: 'Username' },
    { field: 'password', label: 'Password' },
    { field: 'private_key', label: 'Private Key' },
    { field: 'public_key', label: 'Public Key' },
    { field: 'api_key', label: 'API Key' },
    { field: 'bearer_token', label: 'Bearer Token' },
    { field: 'certificate', label: 'Certificate' },
    { field: 'passphrase', label: 'Passphrase' },
    { field: 'domain', label: 'Domain' },
    
    // Database-specific fields
    { field: 'database_type', label: 'Database Type' },
    { field: 'database_name', label: 'Database Name' },
    
    // Secondary Communication
    { field: 'secondary_service_type', label: 'Secondary Service Type' },
    { field: 'secondary_port', label: 'Secondary Port' },
    { field: 'ftp_type', label: 'FTP Type' },
    { field: 'secondary_username', label: 'Secondary Username' },
    { field: 'secondary_password', label: 'Secondary Password' },
    
    // Additional Information
    { field: 'notes', label: 'Notes' }
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
        case 'name': return 'Example Web Server';
        case 'hostname': return 'webserver01.company.com';
        case 'ip_address': return '192.168.1.100';
        case 'description': return 'Production web server hosting main application';
        case 'device_type': return 'server';
        case 'tags': return 'production, web-server, critical';
        case 'physical_address': return '123 Main St, Data Center A, City, State 12345';
        case 'data_center': return 'DC-East-01';
        case 'building': return 'Building A';
        case 'room': return 'Server Room 101';
        case 'rack_position': return 'Rack 15, U24-U26';
        case 'rack_location': return 'Rack 42, Row 3, Position 15U';
        case 'gps_coordinates': return '40.7128, -74.0060';
        case 'hardware_make': return 'Dell';
        case 'hardware_model': return 'PowerEdge R740';
        case 'serial_number': return 'ABC123XYZ789';
        case 'os_type': return 'linux';
        case 'os_version': return 'Ubuntu 22.04 LTS';
        case 'status': return 'active';
        case 'environment': return 'production';
        case 'criticality': return 'high';
        case 'owner': return 'IT Operations Team';
        case 'support_contact': return 'support@company.com';
        case 'contract_number': return 'SUPP-2024-001';
        case 'service_type': return 'ssh';
        case 'port': return '22';
        case 'is_secure': return 'true';
        case 'credential_type': return 'username_password';
        case 'username': return 'admin';
        case 'password': return 'secure_password_123';
        case 'private_key': return '';
        case 'public_key': return '';
        case 'api_key': return '';
        case 'bearer_token': return '';
        case 'certificate': return '';
        case 'passphrase': return '';
        case 'domain': return '';
        case 'database_type': return '';
        case 'database_name': return '';
        case 'secondary_service_type': return 'none';
        case 'secondary_port': return '';
        case 'ftp_type': return '';
        case 'secondary_username': return '';
        case 'secondary_password': return '';
        case 'notes': return 'Production server - handle with care';
        default: return '';
      }
    });
    
    // Comments row explaining valid values
    const commentsRow = csvFields.map(field => {
      switch (field.field) {
        case 'name': return 'REQUIRED - Descriptive name for the asset';
        case 'hostname': return 'REQUIRED - Fully qualified domain name or hostname';
        case 'ip_address': return 'Optional - IPv4 or IPv6 address';
        case 'description': return 'Optional - Brief description of the asset';
        case 'device_type': return 'Valid: server, workstation, router, switch, firewall, database, web-server, application-server, storage, other';
        case 'tags': return 'Optional - Comma-separated values, e.g: production, web-server, critical';
        case 'physical_address': return 'Optional - Physical location address';
        case 'data_center': return 'Optional - Data center identifier';
        case 'building': return 'Optional - Building name or identifier';
        case 'room': return 'Optional - Room number or identifier';
        case 'rack_position': return 'Optional - Rack position details';
        case 'rack_location': return 'Optional - Rack location in format: Rack X, Row Y, Position ZU';
        case 'gps_coordinates': return 'Optional - GPS coordinates in format: latitude, longitude';
        case 'hardware_make': return 'Optional - Hardware manufacturer (Dell, HP, Cisco, etc.)';
        case 'hardware_model': return 'Optional - Hardware model number';
        case 'serial_number': return 'Optional - Hardware serial number';
        case 'os_type': return 'Valid: linux, windows, macos, unix, other (default: other)';
        case 'os_version': return 'Optional - Operating system version';
        case 'status': return 'Valid: active, inactive, maintenance, decommissioned (default: active)';
        case 'environment': return 'Valid: production, staging, development, testing, qa (default: production)';
        case 'criticality': return 'Valid: low, medium, high, critical (default: medium)';
        case 'owner': return 'Optional - Asset owner or responsible team';
        case 'support_contact': return 'Optional - Support contact information';
        case 'contract_number': return 'Optional - Support contract number';
        case 'service_type': return 'REQUIRED - Primary service type (ssh, winrm, http, https, etc.)';
        case 'port': return 'REQUIRED - Port number for primary service';
        case 'is_secure': return 'Optional - true/false, whether connection uses encryption';
        case 'credential_type': return 'Optional - username_password, ssh_key, api_key, bearer_token, certificate';
        case 'username': return 'Required when credential_type=username_password';
        case 'password': return 'Required when credential_type=username_password (will be encrypted)';
        case 'private_key': return 'Required when credential_type=ssh_key (paste full private key)';
        case 'public_key': return 'Optional - SSH public key';
        case 'api_key': return 'Required when credential_type=api_key (will be encrypted)';
        case 'bearer_token': return 'Required when credential_type=bearer_token (will be encrypted)';
        case 'certificate': return 'Required when credential_type=certificate (will be encrypted)';
        case 'passphrase': return 'Optional - Passphrase for encrypted keys/certificates';
        case 'domain': return 'Optional - Windows domain for authentication';
        case 'database_type': return 'Valid: mysql, postgresql, mssql, oracle, mongodb, redis (only when service_type=database)';
        case 'database_name': return 'Required when service_type=database';
        case 'secondary_service_type': return 'Valid: none, telnet, ftp_sftp (default: none)';
        case 'secondary_port': return 'Optional - Port for secondary service';
        case 'ftp_type': return 'Valid: ftp, ftps, sftp (only when secondary_service_type=ftp_sftp)';
        case 'secondary_username': return 'Optional - Username for secondary service';
        case 'secondary_password': return 'Optional - Password for secondary service (will be encrypted)';
        case 'notes': return 'Optional - Additional notes about the asset';
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
      '# DELETE ALL LINES STARTING WITH # AND ADD YOUR ASSET DATA BELOW:'
    ];
    
    const csvContent = csvLines.join('\n');
    
    const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' });
    const link = document.createElement('a');
    const url = URL.createObjectURL(blob);
    link.setAttribute('href', url);
    link.setAttribute('download', 'asset_import_template.csv');
    link.style.visibility = 'hidden';
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  };

  // Export current assets
  const handleExportAssets = () => {
    const headers = csvFields.map(field => field.label);
    const rows = assets.map(asset => {
      return csvFields.map(field => {
        let value = asset[field.field as keyof Asset] || '';
        
        // Handle special formatting
        if (field.field === 'tags' && Array.isArray(value)) {
          value = value.join(', ');
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
    link.setAttribute('download', `assets_export_${new Date().toISOString().split('T')[0]}.csv`);
    link.style.visibility = 'hidden';
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  };

  // Import CSV
  const handleImportClick = () => {
    fileInputRef.current?.click();
  };

  const handleFileImport = async (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (!file) return;

    const reader = new FileReader();
    reader.onload = async (e) => {
      try {
        const csv = e.target?.result as string;
        const lines = csv.split('\n').filter(line => line.trim());
        
        if (lines.length < 2) {
          alert('CSV file must contain at least a header row and one data row');
          return;
        }

        const headers = lines[0].split(',').map(h => h.trim().replace(/"/g, ''));
        const expectedHeaders = csvFields.map(f => f.label);
        
        // Validate headers
        const missingHeaders = expectedHeaders.filter(h => !headers.includes(h));
        if (missingHeaders.length > 0) {
          alert(`Missing required headers: ${missingHeaders.join(', ')}`);
          return;
        }

        const importedAssets = [];
        const errors = [];

        for (let i = 1; i < lines.length; i++) {
          const line = lines[i].trim();
          
          // Skip comment lines and empty lines
          if (line.startsWith('#') || line === '') {
            continue;
          }
          
          const values = line.split(',').map(v => v.trim().replace(/^"|"$/g, ''));
          const assetData: any = {};

          headers.forEach((header, index) => {
            const fieldDef = csvFields.find(f => f.label === header);
            if (fieldDef) {
              let value = values[index] || '';
              
              // Handle special field types
              if (fieldDef.field === 'tags' && value) {
                assetData[fieldDef.field] = value.split(',').map(t => t.trim()).filter(Boolean);
              } else if (fieldDef.field === 'port' || fieldDef.field === 'secondary_port') {
                assetData[fieldDef.field] = value ? parseInt(value) : null;
              } else if (fieldDef.field === 'is_secure') {
                assetData[fieldDef.field] = value.toLowerCase() === 'true';
              } else {
                assetData[fieldDef.field] = value;
              }
            }
          });

          // Validate required fields (based on backend AssetCreate model)
          if (!assetData.name || assetData.name.trim() === '') {
            errors.push(`Row ${i + 1}: Asset Name is required`);
            continue;
          }

          if (!assetData.hostname || assetData.hostname.trim() === '') {
            errors.push(`Row ${i + 1}: Hostname is required`);
            continue;
          }

          if (!assetData.service_type || assetData.service_type.trim() === '') {
            errors.push(`Row ${i + 1}: Service Type is required`);
            continue;
          }

          if (!assetData.port || isNaN(parseInt(assetData.port))) {
            errors.push(`Row ${i + 1}: Port is required and must be a valid number`);
            continue;
          }

          // Validate credential-specific requirements
          if (assetData.credential_type) {
            if (assetData.credential_type === 'username_password') {
              if (!assetData.username) {
                errors.push(`Row ${i + 1}: Username is required when credential_type is username_password`);
                continue;
              }
              if (!assetData.password) {
                errors.push(`Row ${i + 1}: Password is required when credential_type is username_password`);
                continue;
              }
            } else if (assetData.credential_type === 'ssh_key') {
              if (!assetData.private_key) {
                errors.push(`Row ${i + 1}: Private Key is required when credential_type is ssh_key`);
                continue;
              }
            } else if (assetData.credential_type === 'api_key') {
              if (!assetData.api_key) {
                errors.push(`Row ${i + 1}: API Key is required when credential_type is api_key`);
                continue;
              }
            } else if (assetData.credential_type === 'bearer_token') {
              if (!assetData.bearer_token) {
                errors.push(`Row ${i + 1}: Bearer Token is required when credential_type is bearer_token`);
                continue;
              }
            } else if (assetData.credential_type === 'certificate') {
              if (!assetData.certificate) {
                errors.push(`Row ${i + 1}: Certificate is required when credential_type is certificate`);
                continue;
              }
            }
          }

          // Validate database-specific requirements
          if (assetData.service_type === 'database') {
            if (!assetData.database_type) {
              errors.push(`Row ${i + 1}: Database Type is required when service_type is database`);
              continue;
            }
            if (!assetData.database_name) {
              errors.push(`Row ${i + 1}: Database Name is required when service_type is database`);
              continue;
            }
          }

          // Validate secondary service requirements
          if (assetData.secondary_service_type && assetData.secondary_service_type !== 'none') {
            if (assetData.secondary_service_type === 'ftp_sftp' && !assetData.ftp_type) {
              errors.push(`Row ${i + 1}: FTP Type is required when secondary_service_type is ftp_sftp`);
              continue;
            }
          }

          importedAssets.push(assetData);
        }

        if (errors.length > 0) {
          alert(`Import errors:\n${errors.join('\n')}`);
          return;
        }

        // Import assets
        let successCount = 0;
        for (const assetData of importedAssets) {
          try {
            await assetApi.create(assetData);
            successCount++;
          } catch (error) {
            console.error('Failed to import asset:', error);
          }
        }

        alert(`Successfully imported ${successCount} out of ${importedAssets.length} assets`);
        assetListRef.current?.refresh(); // Refresh the list
        
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
      setSelectedAsset(null);
      setEditingAsset(null);
    } else if (action === 'edit' && id) {
      const asset = assets.find(a => a.id.toString() === id);
      if (asset) {
        // Fetch detailed asset data for editing (includes credential_type)
        fetchDetailedAssetData(parseInt(id)).then(detailedAsset => {
          if (detailedAsset) {
            setEditingAsset(detailedAsset);
          } else {
            // Fallback to list data if detailed fetch fails
            setEditingAsset(asset);
          }
        });
        setSelectedAsset(null);
        setAddingNew(false);
      }
    } else if (action === 'view' && id) {
      const asset = assets.find(a => a.id.toString() === id);
      if (asset) {
        // Fetch detailed asset data for viewing (includes credential_type)
        fetchDetailedAssetData(parseInt(id)).then(detailedAsset => {
          if (detailedAsset) {
            setSelectedAsset(detailedAsset);
          } else {
            // Fallback to list data if detailed fetch fails
            setSelectedAsset(asset);
          }
        });
        setEditingAsset(null);
        setAddingNew(false);
      }
    } else {
      setAddingNew(false);
      setSelectedAsset(null);
      setEditingAsset(null);
    }
  }, [action, id, assets]);



  const handleDeleteAsset = async (assetId: number) => {
    if (!window.confirm('Are you sure you want to delete this asset?')) return;
    
    try {
      await assetApi.delete(assetId);
      assetListRef.current?.refresh();
      if (selectedAsset?.id === assetId) {
        setSelectedAsset(null);
        navigate('/assets');
      }
    } catch (error) {
      console.error('Failed to delete asset:', error);
    }
  };

  const handleTestConnection = async (assetId: number) => {
    try {
      const result = await assetApi.test(assetId);
      alert(result.success ? 'Connection successful!' : `Connection failed: ${result.error}`);
    } catch (error) {
      console.error('Connection test failed:', error);
      alert('Connection test failed');
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
          .assets-table-section {
            grid-column: 1;
          }
          .detail-grid-2col {
            grid-column: 2 / 4;
          }
          .assets-table {
            width: 100%;
            border-collapse: collapse;
            font-size: 12px;
          }
          .assets-table th {
            background: var(--neutral-50);
            padding: 6px 8px;
            text-align: left;
            font-weight: 600;
            color: var(--neutral-700);
            border-bottom: 1px solid var(--neutral-200);
            font-size: 11px;
          }
          .assets-table td {
            padding: 6px 8px;
            border-bottom: 1px solid var(--neutral-100);
            vertical-align: middle;
            font-size: 12px;
          }
          .assets-table tr:hover {
            background: var(--neutral-50);
          }
          .assets-table tr.selected {
            background: var(--primary-blue-light);
            border-left: 3px solid var(--primary-blue);
          }
          .assets-table tr {
            cursor: pointer;
          }

          .asset-details h3 {
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
          <h1>Asset Management</h1>
        </div>
        <div className="header-stats">
          <button 
            className="btn-icon"
            onClick={() => navigate('/assets/create')}
            title="Add new asset"
            disabled={addingNew || !!editingAsset}
          >
            <Plus size={16} />
          </button>
          {selectedAsset && !addingNew && !editingAsset && (
            <button 
              className="btn-icon"
              onClick={() => navigate(`/assets/edit/${selectedAsset.id}`)}
              title="Edit selected asset"
            >
              <Edit3 size={16} />
            </button>
          )}
          <div className="dropdown">
            <button 
              className="btn-icon dropdown-toggle"
              title="Export options"
              disabled={addingNew || !!editingAsset}
            >
              <Upload size={16} />
            </button>
            <div className="dropdown-menu">
              <button onClick={handleExportTemplate} className="dropdown-item">
                Export Template
              </button>
              <button onClick={handleExportAssets} className="dropdown-item">
                Export Current Assets
              </button>
            </div>
          </div>
          <button 
            className="btn-icon"
            onClick={handleImportClick}
            title="Import from CSV"
            disabled={addingNew || !!editingAsset}
          >
            <Download size={16} />
          </button>
          <Link to="/users" className="stat-pill">
            <Users size={14} />
            <span>Users</span>
          </Link>
          <Link to="/assets" className="stat-pill">
            <Target size={14} />
            <span>{assets.length} Assets</span>
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
        {/* Column 1: Assets Data Grid */}
        <div className="dashboard-section assets-table-section">
          <div className="section-header">
            Assets ({assets.length})
          </div>
          <div className="compact-content">
            <AssetTableList
              ref={assetListRef}
              onSelectionChanged={(selectedAssets) => {
                if (selectedAssets.length > 0) {
                  const asset = selectedAssets[0];
                  console.log('Asset selection changed to:', asset.name, 'ID:', asset.id);
                  
                  // Fetch detailed asset data when selecting from list
                  fetchDetailedAssetData(asset.id).then(detailedAsset => {
                    console.log('Detailed asset data loaded for:', detailedAsset?.name);
                    if (detailedAsset) {
                      setSelectedAsset(detailedAsset);
                    } else {
                      // Fallback to list data if detailed fetch fails
                      setSelectedAsset(asset);
                    }
                  });
                } else {
                  console.log('Asset selection cleared');
                  setSelectedAsset(null);
                }
              }}
              onRowDoubleClicked={(asset) => {
                navigate(`/assets/edit/${asset.id}`);
              }}
              onDataLoaded={(loadedAssets) => {
                setAssets(loadedAssets);
                setLoading(false);
              }}
              onEditAsset={(asset) => {
                navigate(`/assets/edit/${asset.id}`);
              }}
              onDeleteAsset={handleDeleteAsset}
            />
          </div>
        </div>

        {/* Columns 2-3: Asset Details/Form Panel */}
        <div className="dashboard-section detail-grid-2col">
          {addingNew ? (
            <>
              <div className="section-header">
                <span>Create New Asset</span>
                <div style={{ display: 'flex', gap: '4px' }}>

                  <button 
                    className="btn-icon btn-ghost"
                    onClick={() => navigate('/assets')}
                    title="Cancel"
                  >
                    <X size={16} />
                  </button>
                </div>
              </div>
              <div className="compact-content">
                <AssetSpreadsheetForm
                  mode="create"
                  onCancel={() => navigate('/assets')}
                  onSave={async (assetData) => {
                    try {
                      await assetApi.create(assetData);
                      assetListRef.current?.refresh();
                      navigate('/assets');
                    } catch (error) {
                      console.error('Failed to create asset:', error);
                      alert('Failed to create asset. Please try again.');
                    }
                  }}
                />
              </div>
            </>
          ) : editingAsset ? (
            <>
              <div className="section-header">
                <span>Edit Asset: {editingAsset.name}</span>
                <div style={{ display: 'flex', gap: '4px' }}>
                  <button 
                    className="btn-icon btn-ghost"
                    onClick={() => navigate('/assets')}
                    title="Cancel"
                  >
                    <X size={16} />
                  </button>
                </div>
              </div>
              <div className="compact-content">
                <AssetSpreadsheetForm
                  mode="edit"
                  asset={editingAsset}
                  onCancel={() => navigate('/assets')}
                  onSave={async (assetData) => {
                    try {
                      await assetApi.update(editingAsset.id, assetData);
                      assetListRef.current?.refresh();
                      navigate('/assets');
                    } catch (error) {
                      console.error('Failed to update asset:', error);
                      alert('Failed to update asset. Please try again.');
                    }
                  }}
                />
              </div>
            </>
          ) : selectedAsset ? (
            <>
              <div className="section-header">
                Asset Details: {selectedAsset.name}
              </div>
              <div className="compact-content">
                {loadingAssetDetails ? (
                  <div className="loading-state">
                    <p>Loading asset details...</p>
                  </div>
                ) : (
                  <AssetSpreadsheetForm
                    mode="view"
                    asset={selectedAsset}
                    onCancel={() => {}}
                    onSave={() => {}}
                  />
                )}
              </div>
            </>
          ) : loadingAssetDetails ? (
            <>
              <div className="section-header">
                Asset Details
              </div>
              <div className="compact-content">
                <div className="loading-state">
                  <p>Loading asset details...</p>
                </div>
              </div>
            </>
          ) : (
            <>
              <div className="section-header">
                Asset Details
              </div>
              <div className="compact-content">
                <div className="empty-state">
                  <h3>Select an asset</h3>
                  <p>Choose an asset from the table to view its details.</p>
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

export default Assets;