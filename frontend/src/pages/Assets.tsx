import React, { useState, useEffect, useRef, useCallback } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import { Link } from 'react-router-dom';
import { Plus, X, Upload, Download, Target, MessageSquare, Edit3, Trash2 } from 'lucide-react';
import { assetApi } from '../services/api';
import AssetDataGrid, { AssetDataGridRef } from '../components/AssetDataGrid';
import AssetSpreadsheetForm from '../components/AssetSpreadsheetForm';
import { Asset, AssetCreate } from '../types/asset';

const Assets: React.FC = () => {
  const navigate = useNavigate();
  const { action, id } = useParams<{ action?: string; id?: string }>();
  
  const [assets, setAssets] = useState<Asset[]>([]);
  const [loading, setLoading] = useState(true);
  const [selectedAsset, setSelectedAsset] = useState<Asset | null>(null);
  const [editingAsset, setEditingAsset] = useState<Asset | null>(null);
  const [addingNew, setAddingNew] = useState(false);
  const [loadingAssetDetails, setLoadingAssetDetails] = useState(false);
  const [isImporting, setIsImporting] = useState(false);
  const [importStatus, setImportStatus] = useState<string>('');
  const assetListRef = useRef<AssetDataGridRef>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);
  const debounceTimeoutRef = useRef<NodeJS.Timeout | null>(null);

  // Fetch detailed asset data (includes credential information)
  const fetchDetailedAssetData = useCallback(async (assetId: number): Promise<Asset | null> => {
    try {
      setLoadingAssetDetails(true);
      const response = await assetApi.get(assetId);
      
      // The API returns {success: true, data: {...}}, so we need response.data
      const assetData = response.data || response;
      
      return assetData;
    } catch (error) {
      return null;
    } finally {
      setLoadingAssetDetails(false);
    }
  }, []);

  // Debounced function to fetch detailed asset data
  const debouncedFetchAssetDetails = useCallback((asset: Asset) => {
    // Immediately set the basic asset data to prevent flashing
    setSelectedAsset(asset);
    
    // Clear any existing timeout
    if (debounceTimeoutRef.current) {
      clearTimeout(debounceTimeoutRef.current);
    }

    // Set a new timeout for detailed data
    debounceTimeoutRef.current = setTimeout(() => {
      fetchDetailedAssetData(asset.id).then(detailedAsset => {
        if (detailedAsset) {
          // Only update if we're still looking at the same asset
          setSelectedAsset(currentAsset => {
            if (currentAsset && currentAsset.id === detailedAsset.id) {
              return detailedAsset;
            }
            return currentAsset;
          });
        }
      });
    }, 300); // 300ms delay
  }, [fetchDetailedAssetData]);

  // Cleanup timeout on unmount
  useEffect(() => {
    return () => {
      if (debounceTimeoutRef.current) {
        clearTimeout(debounceTimeoutRef.current);
      }
    };
  }, []);

  // Memoized selection change handler to prevent infinite re-renders
  const handleSelectionChange = useCallback((selectedAssets: Asset[]) => {
    if (selectedAssets.length > 0) {
      const asset = selectedAssets[0];
      // Use debounced fetch to prevent too many API calls during keyboard navigation
      debouncedFetchAssetDetails(asset);
    } else {
      setSelectedAsset(null);
    }
  }, [debouncedFetchAssetDetails]);

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
    { field: 'secondary_credential_type', label: 'Secondary Credential Type' },
    
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
    
    // Multiple example rows for different service/credential combinations
    const exampleRows = [
      // Example 1: SSH Server with Username/Password
      csvFields.map(field => {
        switch (field.field) {
          case 'name': return 'Linux Web Server';
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
          case 'secondary_credential_type': return '';
          case 'notes': return 'Production server - handle with care';
          default: return '';
        }
      }),
      
      // Example 2: SSH Server with SSH Key
      csvFields.map(field => {
        switch (field.field) {
          case 'name': return 'Development Server';
          case 'hostname': return 'devserver01.company.com';
          case 'ip_address': return '192.168.1.101';
          case 'description': return 'Development environment server';
          case 'device_type': return 'server';
          case 'tags': return 'development, testing';
          case 'os_type': return 'linux';
          case 'os_version': return 'CentOS 8';
          case 'status': return 'active';
          case 'environment': return 'development';
          case 'criticality': return 'medium';
          case 'service_type': return 'ssh';
          case 'port': return '22';
          case 'is_secure': return 'true';
          case 'credential_type': return 'ssh_key';
          case 'username': return 'devuser';
          case 'password': return '';
          case 'private_key': return '-----BEGIN OPENSSH PRIVATE KEY-----\nb3BlbnNzaC1rZXktdjEAAAAABG5vbmUAAAAEbm9uZQAAAAAAAAABAAAAFwAAAAdzc2gtcnNh\n[... rest of private key ...]\n-----END OPENSSH PRIVATE KEY-----';
          case 'public_key': return 'ssh-rsa AAAAB3NzaC1yc2EAAAADAQABAAABAQC... devuser@company.com';
          case 'api_key': return '';
          case 'bearer_token': return '';
          case 'certificate': return '';
          case 'passphrase': return 'key_passphrase_if_needed';
          case 'domain': return '';
          case 'database_type': return '';
          case 'database_name': return '';
          case 'secondary_service_type': return 'none';
          case 'secondary_port': return '';
          case 'ftp_type': return '';
          case 'secondary_username': return '';
          case 'secondary_password': return '';
          case 'secondary_credential_type': return '';
          case 'notes': return 'Development server with SSH key authentication';
          default: return '';
        }
      }),
      
      // Example 3: Database Server
      csvFields.map(field => {
        switch (field.field) {
          case 'name': return 'MySQL Database Server';
          case 'hostname': return 'db01.company.com';
          case 'ip_address': return '192.168.1.102';
          case 'description': return 'Primary MySQL database server';
          case 'device_type': return 'database';
          case 'tags': return 'production, database, mysql';
          case 'os_type': return 'linux';
          case 'os_version': return 'Ubuntu 22.04 LTS';
          case 'status': return 'active';
          case 'environment': return 'production';
          case 'criticality': return 'critical';
          case 'service_type': return 'database';
          case 'port': return '3306';
          case 'is_secure': return 'true';
          case 'credential_type': return 'username_password';
          case 'username': return 'dbadmin';
          case 'password': return 'db_secure_password_456';
          case 'private_key': return '';
          case 'public_key': return '';
          case 'api_key': return '';
          case 'bearer_token': return '';
          case 'certificate': return '';
          case 'passphrase': return '';
          case 'domain': return '';
          case 'database_type': return 'mysql';
          case 'database_name': return 'production_db';
          case 'secondary_service_type': return 'none';
          case 'secondary_port': return '';
          case 'ftp_type': return '';
          case 'secondary_username': return '';
          case 'secondary_password': return '';
          case 'secondary_credential_type': return '';
          case 'notes': return 'Primary production database - critical system';
          default: return '';
        }
      }),
      
      // Example 4: API Server with Bearer Token
      csvFields.map(field => {
        switch (field.field) {
          case 'name': return 'REST API Server';
          case 'hostname': return 'api.company.com';
          case 'ip_address': return '192.168.1.103';
          case 'description': return 'REST API service endpoint';
          case 'device_type': return 'application-server';
          case 'tags': return 'production, api, rest';
          case 'os_type': return 'linux';
          case 'os_version': return 'Ubuntu 22.04 LTS';
          case 'status': return 'active';
          case 'environment': return 'production';
          case 'criticality': return 'high';
          case 'service_type': return 'https';
          case 'port': return '443';
          case 'is_secure': return 'true';
          case 'credential_type': return 'bearer_token';
          case 'username': return '';
          case 'password': return '';
          case 'private_key': return '';
          case 'public_key': return '';
          case 'api_key': return '';
          case 'bearer_token': return 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxMjM0NTY3ODkwIiwibmFtZSI6IkpvaG4gRG9lIiwiaWF0IjoxNTE2MjM5MDIyfQ.SflKxwRJSMeKKF2QT4fwpMeJf36POk6yJV_adQssw5c';
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
          case 'secondary_credential_type': return '';
          case 'notes': return 'API server with JWT bearer token authentication';
          default: return '';
        }
      }),
      
      // Example 5: Windows Server with WinRM
      csvFields.map(field => {
        switch (field.field) {
          case 'name': return 'Windows Domain Controller';
          case 'hostname': return 'dc01.company.local';
          case 'ip_address': return '192.168.1.104';
          case 'description': return 'Primary Windows domain controller';
          case 'device_type': return 'server';
          case 'tags': return 'production, windows, domain-controller';
          case 'os_type': return 'windows';
          case 'os_version': return 'Windows Server 2022';
          case 'status': return 'active';
          case 'environment': return 'production';
          case 'criticality': return 'critical';
          case 'service_type': return 'winrm';
          case 'port': return '5986';
          case 'is_secure': return 'true';
          case 'credential_type': return 'username_password';
          case 'username': return 'Administrator';
          case 'password': return 'Windows_Admin_Pass_789';
          case 'private_key': return '';
          case 'public_key': return '';
          case 'api_key': return '';
          case 'bearer_token': return '';
          case 'certificate': return '';
          case 'passphrase': return '';
          case 'domain': return 'COMPANY';
          case 'database_type': return '';
          case 'database_name': return '';
          case 'secondary_service_type': return 'none';
          case 'secondary_port': return '';
          case 'ftp_type': return '';
          case 'secondary_username': return '';
          case 'secondary_password': return '';
          case 'secondary_credential_type': return '';
          case 'notes': return 'Windows domain controller - critical infrastructure';
          default: return '';
        }
      })
    ];
    
    // Comments row explaining valid values
    const commentsRow = csvFields.map(field => {
      switch (field.field) {
        case 'name': return 'Optional - Descriptive name for the asset';
        case 'hostname': return 'REQUIRED* - Fully qualified domain name or hostname (*either hostname or IP address must be provided)';
        case 'ip_address': return 'REQUIRED* - IPv4 or IPv6 address (*either IP address or hostname must be provided)';
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
        case 'secondary_credential_type': return 'Optional - username_password, ssh_key, api_key, bearer_token, certificate';
        case 'notes': return 'Optional - Additional notes about the asset';
        default: return 'Optional field';
      }
    });
    
    // Helper function to escape CSV values
    const escapeCSVValue = (value: string) => {
      if (typeof value === 'string' && (value.includes(',') || value.includes('"') || value.includes('\n'))) {
        return `"${value.replace(/"/g, '""')}"`;
      }
      return value;
    };

    // Build comprehensive CSV content with headers, multiple examples, and validation rules
    const csvLines = [
      headers.join(','),
      '',
      '# ============================================================================',
      '# OPSCONDUCTOR ASSET IMPORT TEMPLATE',
      '# ============================================================================',
      '# This template contains comprehensive examples for different asset types',
      '# and service/credential combinations. Delete all comment lines (starting with #)',
      '# and replace with your actual asset data.',
      '#',
      '# REQUIRED FIELDS:',
      '# - Service Type: Primary communication service (ssh, winrm, http, etc.)',
      '# - Port: Port number for the primary service',
      '# - Either IP Address OR Hostname (or both) must be provided',
      '#',
      '# IMPORTANT: All credential fields (passwords, keys, tokens) will be encrypted',
      '# automatically when imported into the system.',
      '# ============================================================================',
      '',
      '# EXAMPLE 1: Linux SSH Server with Username/Password Authentication',
      '#' + exampleRows[0].map(escapeCSVValue).join(','),
      '',
      '# EXAMPLE 2: Linux SSH Server with SSH Key Authentication',
      '#' + exampleRows[1].map(escapeCSVValue).join(','),
      '',
      '# EXAMPLE 3: Database Server (MySQL)',
      '#' + exampleRows[2].map(escapeCSVValue).join(','),
      '',
      '# EXAMPLE 4: API Server with Bearer Token Authentication',
      '#' + exampleRows[3].map(escapeCSVValue).join(','),
      '',
      '# EXAMPLE 5: Windows Server with WinRM',
      '#' + exampleRows[4].map(escapeCSVValue).join(','),
      '',
      '# ============================================================================',
      '# FIELD VALIDATION RULES AND REQUIREMENTS:',
      '# ============================================================================',
      '#' + commentsRow.map(comment => `"${comment}"`).join(','),
      '',
      '# ============================================================================',
      '# VALID VALUES FOR ENUM FIELDS:',
      '# ============================================================================',
      '# device_type: server, workstation, router, switch, firewall, database, web-server, application-server, storage, other',
      '# os_type: linux, windows, macos, unix, other',
      '# status: active, inactive, maintenance, decommissioned',
      '# environment: production, staging, development, testing, qa',
      '# criticality: low, medium, high, critical',
      '# service_type: ssh, winrm, http, https, telnet, database, ftp, sftp, snmp, rdp, vnc, other',
      '# credential_type: username_password, ssh_key, api_key, bearer_token, certificate',
      '# database_type: mysql, postgresql, mssql, oracle, mongodb, redis',
      '# secondary_service_type: none, telnet, ftp_sftp',
      '# ftp_type: ftp, ftps, sftp',
      '# is_secure: true, false',
      '',
      '# ============================================================================',
      '# DELETE ALL LINES STARTING WITH # AND ADD YOUR ASSET DATA BELOW:',
      '# ============================================================================'
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

  // Helper function to parse CSV line properly handling quoted fields
  const parseCSVLine = (line: string): string[] => {
    const result = [];
    let current = '';
    let inQuotes = false;
    let i = 0;
    
    while (i < line.length) {
      const char = line[i];
      
      if (char === '"') {
        if (inQuotes && line[i + 1] === '"') {
          // Escaped quote
          current += '"';
          i += 2;
        } else {
          // Toggle quote state
          inQuotes = !inQuotes;
          i++;
        }
      } else if (char === ',' && !inQuotes) {
        // Field separator
        result.push(current.trim());
        current = '';
        i++;
      } else {
        current += char;
        i++;
      }
    }
    
    // Add the last field
    result.push(current.trim());
    return result;
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
        setIsImporting(true);
        setImportStatus('Processing CSV file...');
        const csv = e.target?.result as string;
        const lines = csv.split('\n').filter(line => line.trim());
        
        if (lines.length < 2) {
          alert('CSV file must contain at least a header row and one data row');
          setIsImporting(false);
          setImportStatus('');
          return;
        }

        // Parse CSV headers properly
        const headers = parseCSVLine(lines[0]);
        const expectedHeaders = csvFields.map(f => f.label);
        
        // Validate headers (allow partial headers for flexibility)
        const missingRequiredHeaders = ['Service Type', 'Port'].filter(h => !headers.includes(h));
        const hasIpOrHostname = headers.includes('IP Address') || headers.includes('Hostname');
        
        if (missingRequiredHeaders.length > 0) {
          alert(`Missing required headers: ${missingRequiredHeaders.join(', ')}`);
          setIsImporting(false);
          setImportStatus('');
          return;
        }
        
        if (!hasIpOrHostname) {
          alert('Missing required headers: Must have either "IP Address" or "Hostname" (or both)');
          setIsImporting(false);
          setImportStatus('');
          return;
        }

        const importedAssets: AssetCreate[] = [];
        const errors: string[] = [];

        for (let i = 1; i < lines.length; i++) {
          const line = lines[i].trim();
          
          // Skip comment lines and empty lines
          if (line.startsWith('#') || line === '') {
            continue;
          }
          
          const values = parseCSVLine(line);
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
              } else if (value !== '') {
                // Only set non-empty values to avoid overriding defaults
                assetData[fieldDef.field] = value;
              }
            }
          });



          // Validate required fields (based on backend AssetCreate model)
          // Either IP Address or Hostname must be present (backend requires hostname field)
          const hasIpAddress = assetData.ip_address && assetData.ip_address.trim() !== '';
          const hasHostname = assetData.hostname && assetData.hostname.trim() !== '';
          
          if (!hasIpAddress && !hasHostname) {
            errors.push(`Row ${i + 1}: Either IP Address or Hostname (or both) must be provided`);
            continue;
          }
          
          // Note: Backend requires hostname field, so we'll use IP as hostname fallback during data cleaning

          if (!assetData.service_type || assetData.service_type.trim() === '') {
            errors.push(`Row ${i + 1}: Service Type is required`);
            continue;
          }

          if (!assetData.port || isNaN(parseInt(String(assetData.port)))) {
            errors.push(`Row ${i + 1}: Port is required and must be a valid number`);
            continue;
          }

          // Validate enum fields
          const validDeviceTypes = ['server', 'workstation', 'router', 'switch', 'firewall', 'database', 'web-server', 'application-server', 'storage', 'other'];
          if (assetData.device_type && !validDeviceTypes.includes(assetData.device_type)) {
            errors.push(`Row ${i + 1}: Invalid device_type '${assetData.device_type}'. Valid values: ${validDeviceTypes.join(', ')}`);
            continue;
          }

          const validOsTypes = ['linux', 'windows', 'macos', 'unix', 'other'];
          if (assetData.os_type && !validOsTypes.includes(assetData.os_type)) {
            errors.push(`Row ${i + 1}: Invalid os_type '${assetData.os_type}'. Valid values: ${validOsTypes.join(', ')}`);
            continue;
          }

          const validStatuses = ['active', 'inactive', 'maintenance', 'decommissioned'];
          if (assetData.status && !validStatuses.includes(assetData.status)) {
            errors.push(`Row ${i + 1}: Invalid status '${assetData.status}'. Valid values: ${validStatuses.join(', ')}`);
            continue;
          }

          const validEnvironments = ['production', 'staging', 'development', 'testing', 'qa'];
          if (assetData.environment && !validEnvironments.includes(assetData.environment)) {
            errors.push(`Row ${i + 1}: Invalid environment '${assetData.environment}'. Valid values: ${validEnvironments.join(', ')}`);
            continue;
          }

          const validCriticalities = ['low', 'medium', 'high', 'critical'];
          if (assetData.criticality && !validCriticalities.includes(assetData.criticality)) {
            errors.push(`Row ${i + 1}: Invalid criticality '${assetData.criticality}'. Valid values: ${validCriticalities.join(', ')}`);
            continue;
          }

          const validServiceTypes = ['ssh', 'winrm', 'http', 'https', 'telnet', 'database', 'ftp', 'sftp', 'snmp', 'rdp', 'vnc', 'other'];
          if (!validServiceTypes.includes(assetData.service_type)) {
            errors.push(`Row ${i + 1}: Invalid service_type '${assetData.service_type}'. Valid values: ${validServiceTypes.join(', ')}`);
            continue;
          }

          const validCredentialTypes = ['username_password', 'ssh_key', 'api_key', 'bearer_token', 'certificate'];
          if (assetData.credential_type && !validCredentialTypes.includes(assetData.credential_type)) {
            errors.push(`Row ${i + 1}: Invalid credential_type '${assetData.credential_type}'. Valid values: ${validCredentialTypes.join(', ')}`);
            continue;
          }

          const validDatabaseTypes = ['mysql', 'postgresql', 'mssql', 'oracle', 'mongodb', 'redis'];
          if (assetData.database_type && !validDatabaseTypes.includes(assetData.database_type)) {
            errors.push(`Row ${i + 1}: Invalid database_type '${assetData.database_type}'. Valid values: ${validDatabaseTypes.join(', ')}`);
            continue;
          }

          const validSecondaryServiceTypes = ['none', 'telnet', 'ftp_sftp'];
          if (assetData.secondary_service_type && !validSecondaryServiceTypes.includes(assetData.secondary_service_type)) {
            errors.push(`Row ${i + 1}: Invalid secondary_service_type '${assetData.secondary_service_type}'. Valid values: ${validSecondaryServiceTypes.join(', ')}`);
            continue;
          }

          const validFtpTypes = ['ftp', 'ftps', 'sftp'];
          if (assetData.ftp_type && !validFtpTypes.includes(assetData.ftp_type)) {
            errors.push(`Row ${i + 1}: Invalid ftp_type '${assetData.ftp_type}'. Valid values: ${validFtpTypes.join(', ')}`);
            continue;
          }

          if (assetData.secondary_credential_type && !validCredentialTypes.includes(assetData.secondary_credential_type)) {
            errors.push(`Row ${i + 1}: Invalid secondary_credential_type '${assetData.secondary_credential_type}'. Valid values: ${validCredentialTypes.join(', ')}`);
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

          // Clean up the asset data and ensure it matches AssetCreate interface
          const cleanedAssetData: AssetCreate = {
            // Only include fields that are defined in AssetCreate interface
            ...(assetData.name && { name: assetData.name }),
            // Ensure hostname is always provided - use IP address as fallback
            hostname: assetData.hostname || assetData.ip_address || '',
            ...(assetData.ip_address && { ip_address: assetData.ip_address }),
            ...(assetData.description && { description: assetData.description }),
            ...(assetData.tags && Array.isArray(assetData.tags) && { tags: assetData.tags }),
            
            // Device/Hardware Information
            ...(assetData.device_type && { device_type: assetData.device_type }),
            ...(assetData.hardware_make && { hardware_make: assetData.hardware_make }),
            ...(assetData.hardware_model && { hardware_model: assetData.hardware_model }),
            ...(assetData.serial_number && { serial_number: assetData.serial_number }),
            
            // System Information
            ...(assetData.os_type && { os_type: assetData.os_type }),
            ...(assetData.os_version && { os_version: assetData.os_version }),
            
            // Location Information
            ...(assetData.physical_address && { physical_address: assetData.physical_address }),
            ...(assetData.data_center && { data_center: assetData.data_center }),
            ...(assetData.building && { building: assetData.building }),
            ...(assetData.room && { room: assetData.room }),
            ...(assetData.rack_position && { rack_position: assetData.rack_position }),
            ...(assetData.rack_location && { rack_location: assetData.rack_location }),
            ...(assetData.gps_coordinates && { gps_coordinates: assetData.gps_coordinates }),
            
            // Status & Management
            ...(assetData.status && { status: assetData.status }),
            ...(assetData.environment && { environment: assetData.environment }),
            ...(assetData.criticality && { criticality: assetData.criticality }),
            ...(assetData.owner && { owner: assetData.owner }),
            ...(assetData.support_contact && { support_contact: assetData.support_contact }),
            ...(assetData.contract_number && { contract_number: assetData.contract_number }),
            
            // Primary Communication Service (required)
            service_type: assetData.service_type,
            port: typeof assetData.port === 'string' ? parseInt(assetData.port, 10) : assetData.port,
            is_secure: assetData.is_secure !== undefined ? assetData.is_secure : false,
            
            // Primary Service Credentials - Auto-detect credential type if not specified
            ...(() => {
              let credentialType = assetData.credential_type;
              
              // Auto-detect credential type based on provided credentials
              if (!credentialType) {
                if (assetData.private_key) {
                  credentialType = 'ssh_key';
                } else if (assetData.api_key) {
                  credentialType = 'api_key';
                } else if (assetData.bearer_token) {
                  credentialType = 'bearer_token';
                } else if (assetData.certificate) {
                  credentialType = 'certificate';
                } else if (assetData.username && assetData.password) {
                  credentialType = 'username_password';
                }
              }
              
              return {
                ...(credentialType && { credential_type: credentialType }),
                ...(assetData.username && { username: assetData.username }),
                ...(assetData.password && { password: assetData.password }),
                ...(assetData.private_key && { private_key: assetData.private_key }),
                ...(assetData.public_key && { public_key: assetData.public_key }),
                ...(assetData.api_key && { api_key: assetData.api_key }),
                ...(assetData.bearer_token && { bearer_token: assetData.bearer_token }),
                ...(assetData.certificate && { certificate: assetData.certificate }),
                ...(assetData.passphrase && { passphrase: assetData.passphrase }),
                ...(assetData.domain && { domain: assetData.domain }),
              };
            })(),
            
            // Database-specific fields
            ...(assetData.database_type && { database_type: assetData.database_type }),
            ...(assetData.database_name && { database_name: assetData.database_name }),
            
            // Secondary Communication
            ...(assetData.secondary_service_type && { secondary_service_type: assetData.secondary_service_type }),
            ...(assetData.secondary_port && { secondary_port: typeof assetData.secondary_port === 'string' ? parseInt(assetData.secondary_port, 10) : assetData.secondary_port }),
            ...(assetData.ftp_type && { ftp_type: assetData.ftp_type }),
            ...(assetData.secondary_username && { secondary_username: assetData.secondary_username }),
            ...(assetData.secondary_password && { secondary_password: assetData.secondary_password }),
            ...(assetData.secondary_credential_type && { secondary_credential_type: assetData.secondary_credential_type }),
            
            // Additional Information
            ...(assetData.notes && { notes: assetData.notes })
          };
          
          importedAssets.push(cleanedAssetData);
        }

        if (errors.length > 0) {
          alert(`Import errors:\n${errors.join('\n')}`);
          setIsImporting(false);
          setImportStatus('');
          return;
        }

        // Check for potential duplicates before importing
        const duplicateWarnings = [];
        let existingAssetsData = [];
        
        try {
          const existingAssets = await assetApi.list(0, 1000); // Get existing assets
          existingAssetsData = existingAssets.data || existingAssets.assets || existingAssets || [];
          
          // Ensure it's an array
          if (!Array.isArray(existingAssetsData)) {
            existingAssetsData = [];
          }
        } catch (error) {
          existingAssetsData = [];
        }
        
        for (let i = 0; i < importedAssets.length; i++) {
          const assetData = importedAssets[i];
          const potentialDuplicates = existingAssetsData.filter((existing: any) => {
            // Check for duplicates based on name, hostname, or IP address
            return (
              (assetData.name && existing.name === assetData.name) ||
              (assetData.hostname && existing.hostname === assetData.hostname) ||
              (assetData.ip_address && existing.ip_address === assetData.ip_address)
            );
          });
          
          if (potentialDuplicates.length > 0) {
            const assetIdentifier = assetData.name || assetData.hostname || assetData.ip_address;
            duplicateWarnings.push({
              index: i,
              asset: assetData,
              identifier: assetIdentifier,
              existing: potentialDuplicates
            });
          }
        }
        
        // Show duplicate warnings if any found
        if (duplicateWarnings.length > 0) {
          const duplicateMessage = duplicateWarnings.map(dup => 
            `• ${dup.identifier} (matches ${dup.existing.length} existing asset${dup.existing.length > 1 ? 's' : ''})`
          ).join('\n');
          
          const userChoice = window.confirm(
            `Found ${duplicateWarnings.length} potential duplicate(s):\n\n${duplicateMessage}\n\n` +
            `Click OK to import anyway (may create duplicates)\n` +
            `Click Cancel to skip duplicate assets`
          );
          
          if (!userChoice) {
            // Remove duplicates from import list
            const indicesToRemove = duplicateWarnings.map(dup => dup.index).sort((a, b) => b - a);
            indicesToRemove.forEach(index => {
              importedAssets.splice(index, 1);
            });
            
            if (importedAssets.length === 0) {
              setImportStatus('All assets were identified as potential duplicates and skipped.');
              setIsImporting(false);
              return;
            }
            
            setImportStatus(`Skipping ${duplicateWarnings.length} potential duplicate(s). Importing ${importedAssets.length} new assets...`);
          } else {
            setImportStatus(`Importing ${importedAssets.length} assets (including ${duplicateWarnings.length} potential duplicates)...`);
          }
        }

        // Import assets
        let successCount = 0;
        const importErrors = [];
        
        for (let i = 0; i < importedAssets.length; i++) {
          const assetData = importedAssets[i];
          try {
            await assetApi.create(assetData);
            successCount++;
          } catch (error: any) {
            
            // Extract detailed error message from API response
            let errorMessage = 'Unknown error';
            if (error.response?.data) {
              const errorData = error.response.data;
              if (errorData.detail) {
                // FastAPI validation error format
                if (Array.isArray(errorData.detail)) {
                  errorMessage = errorData.detail.map((err: any) => 
                    `${err.loc?.join('.')} - ${err.msg}`
                  ).join('; ');
                } else {
                  errorMessage = errorData.detail;
                }
              } else if (errorData.message) {
                errorMessage = errorData.message;
              } else if (typeof errorData === 'string') {
                errorMessage = errorData;
              } else {
                errorMessage = JSON.stringify(errorData);
              }
            } else if (error.message) {
              errorMessage = error.message;
            }
            
            const assetIdentifier = assetData.name || assetData.hostname || assetData.ip_address || 'Unknown asset';
            importErrors.push(`Asset "${assetIdentifier}": ${errorMessage}`);
          }
        }

        // Show detailed results
        let resultMessage = `Successfully imported ${successCount} out of ${importedAssets.length} assets`;
        if (importErrors.length > 0) {
          resultMessage += `\n\nImport errors:\n${importErrors.join('\n')}`;
        }
        
        alert(resultMessage);
        assetListRef.current?.refresh(); // Refresh the list
        
      } catch (error) {
        alert(`Failed to parse CSV file. Error: ${error instanceof Error ? error.message : 'Unknown error'}\n\nPlease check the format and try again.`);
      } finally {
        setIsImporting(false);
        setImportStatus('');
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

  const handleDeleteAsset = async (assetId?: number) => {
    const targetAsset = assetId ? assets.find(a => a.id === assetId) : selectedAsset;
    if (!targetAsset) return;
    
    const confirmDelete = window.confirm(
      `Are you sure you want to delete the asset "${targetAsset.name}"?\n\nThis action cannot be undone.`
    );
    
    if (!confirmDelete) return;
    
    try {
      await assetApi.delete(targetAsset.id);
      assetListRef.current?.refresh();
      if (selectedAsset?.id === targetAsset.id) {
        setSelectedAsset(null);
        navigate('/assets');
      }
    } catch (error) {
      alert('Failed to delete asset. Please try again.');
    }
  };

  const handleTestConnection = async (assetId: number) => {
    try {
      const result = await assetApi.test(assetId);
      alert(result.success ? 'Connection successful!' : `Connection failed: ${result.error}`);
    } catch (error) {
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
            height: 100%;
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
          .assets-table tr {
            cursor: pointer;
            transition: background-color 0.15s ease;
            background: transparent;
          }
          
          .assets-table tr:hover:not(.selected) {
            background: var(--neutral-50);
          }
          
          .assets-table tr.selected {
            background: var(--primary-blue-light) !important;
            border-left: 3px solid var(--primary-blue);
          }
          
          /* Prevent flickering during selection changes */
          .assets-table tr:not(.selected) {
            background: transparent !important;
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
          
          /* Apply same spacing to assets table as form container */
          .assets-table-section .asset-data-grid {
            width: 100%;
            box-sizing: border-box;
            border: none;
          }
          
          /* Make AG-Grid components respect the container with proper spacing */
          .assets-table-section .ag-grid-wrapper {
            width: calc(100% - 16px) !important;
            margin: 8px !important;
            box-sizing: border-box !important;
            border: none !important;
          }
          
          .assets-table-section .ag-root-wrapper,
          .assets-table-section .ag-root,
          .assets-table-section .ag-body-viewport {
            width: 100% !important;
            max-width: 100% !important;
            box-sizing: border-box !important;
            overflow-x: hidden !important;
          }
          
          /* Override AG-Grid CSS variables to remove any shadow effects */
          .assets-table-section .ag-theme-custom {
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
          .assets-table-section .ag-header-cell {
            font-size: 11px !important;
            font-weight: 600 !important;
            color: #24292f !important;
            text-transform: uppercase !important;
            letter-spacing: 0.5px !important;
          }
          
          /* Remove any 3D effects and ensure clean borders */
          .assets-table-section .ag-root-wrapper {
            border: none !important;
            border-radius: 0 !important;
            box-shadow: none !important;
            background: #ffffff !important;
            /* Remove any potential 3D effects */
            filter: none !important;
            transform: none !important;
          }
          
          .assets-table-section .ag-root,
          .assets-table-section .ag-body-viewport,
          .assets-table-section .ag-grid-wrapper {
            background: transparent !important;
            border: none !important;
            box-shadow: none !important;
            border-radius: 0 !important;
            /* Remove any potential 3D effects */
            filter: none !important;
            transform: none !important;
          }
          
          /* Remove border radius from all table cells and headers */
          .assets-table-section .ag-cell,
          .assets-table-section .ag-header-cell {
            border-radius: 0 !important;
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
            <Plus size={18} />
          </button>
          {selectedAsset && !addingNew && !editingAsset && (
            <button 
              className="btn-icon"
              onClick={() => navigate(`/assets/edit/${selectedAsset.id}`)}
              title="Edit selected asset"
            >
              <Edit3 size={18} />
            </button>
          )}
          {selectedAsset && !addingNew && !editingAsset && (
            <button 
              className="btn-icon btn-danger"
              onClick={() => handleDeleteAsset()}
              title="Delete selected asset"
            >
              <Trash2 size={18} />
            </button>
          )}
          <div className="dropdown">
            <button 
              className="btn-icon dropdown-toggle"
              title="Export options"
              disabled={addingNew || !!editingAsset}
            >
              <Upload size={18} />
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
            disabled={addingNew || !!editingAsset || isImporting}
          >
            <Download size={18} />
          </button>
          {isImporting && (
            <div className="import-status" style={{ fontSize: '12px', color: 'var(--primary-blue)', marginLeft: '8px' }}>
              {importStatus}
            </div>
          )}
          <Link to="/assets" className="stat-pill">
            <Target size={14} />
            <span>{assets.length} Assets</span>
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
          <AssetDataGrid
            className="asset-data-grid"
            ref={assetListRef}
            onSelectionChanged={handleSelectionChange}
            onRowDoubleClicked={(asset) => {
                navigate(`/assets/edit/${asset.id}`);
              }}
              onDataLoaded={(loadedAssets) => {
                setAssets(loadedAssets);
                setLoading(false);
              }}
            />
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
              <AssetSpreadsheetForm
                mode="create"
                onCancel={() => navigate('/assets')}
                onSave={async (assetData) => {
                  try {
                    await assetApi.create(assetData);
                    assetListRef.current?.refresh();
                    navigate('/assets');
                  } catch (error) {
                    alert('Failed to create asset. Please try again.');
                  }
                }}
              />
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
                    alert('Failed to update asset. Please try again.');
                  }
                }}
              />
            </>
          ) : selectedAsset ? (
            <>
              <div className="section-header">
                <span>Asset Details: {selectedAsset.ip_address || selectedAsset.hostname || 'Unknown'}</span>
              </div>
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
            </>
          ) : loadingAssetDetails ? (
            <>
              <div className="section-header">
                Asset Details
              </div>
              <div className="loading-state">
                <p>Loading asset details...</p>
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