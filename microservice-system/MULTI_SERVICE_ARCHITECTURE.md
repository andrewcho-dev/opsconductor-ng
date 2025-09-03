# OpsConductor Multi-Service Target Architecture

## Overview

OpsConductor has been enhanced with a new multi-service target architecture that allows each target (machine/device) to have multiple services configured, providing more flexibility and better organization.

## Key Changes

### Before (Single-Service)
- Each target had one protocol, one port, and one credential
- Limited to one communication method per target
- Difficult to manage machines with multiple services

### After (Multi-Service)
- Each target can have multiple services (SSH, WinRM, RDP, HTTP, etc.)
- Multiple credentials can be assigned to different services
- Better organization and more realistic representation of infrastructure

## New Database Schema

### Core Tables

#### `targets`
- Stores basic target information (hostname, IP, OS, etc.)
- No longer contains port/protocol information

#### `target_services`
- Multiple services per target
- Each service has: type, port, security flag, enabled status
- Connection status tracking

#### `target_credentials`
- Many-to-many relationship between targets and credentials
- Service-specific credential assignments
- Primary credential designation

#### `service_definitions`
- Master list of available service types
- Default ports and security settings
- Extensible for new service types

## Migration Process

### Automatic Migration
The system includes automatic migration from the old schema:

```bash
# Run migration script
python migrate-to-multiservice.py

# Or use the API endpoint (admin only)
curl -X POST http://localhost:8080/api/v1/migrate-schema \
  -H "Authorization: Bearer YOUR_TOKEN"
```

### Manual Migration Steps

1. **Backup your data**
   ```bash
   pg_dump opsconductor > backup_before_migration.sql
   ```

2. **Update the database schema**
   ```bash
   psql -d opsconductor -f database/init-schema.sql
   ```

3. **Run the migration function**
   ```sql
   SELECT migrate_old_targets_to_new_schema();
   ```

4. **Verify the migration**
   ```sql
   SELECT COUNT(*) FROM targets;
   SELECT COUNT(*) FROM target_services;
   SELECT COUNT(*) FROM target_credentials;
   ```

## API Changes

### New Endpoints

#### Multi-Service API (Recommended)
```
GET    /api/v1/targets              # List targets with services
POST   /api/v1/targets              # Create target with services
GET    /api/v1/targets/{id}         # Get target with services
PUT    /api/v1/targets/{id}         # Update target with services
DELETE /api/v1/targets/{id}         # Delete target

GET    /api/v1/service-definitions  # List available service types
```

#### Legacy API (Backward Compatibility)
```
GET    /api/v1/targets              # Returns legacy format
POST   /api/v1/targets              # Accepts legacy format
# ... other legacy endpoints remain unchanged
```

### Request/Response Examples

#### Create Multi-Service Target
```json
POST /api/v1/targets
{
  "name": "Web Server 01",
  "hostname": "web01.company.com",
  "ip_address": "192.168.1.100",
  "os_type": "linux",
  "os_version": "Ubuntu 20.04",
  "description": "Production web server",
  "tags": ["production", "web", "frontend"],
  "services": [
    {
      "service_type": "ssh",
      "port": 22,
      "is_secure": true,
      "is_enabled": true
    },
    {
      "service_type": "http",
      "port": 80,
      "is_secure": false,
      "is_enabled": true
    },
    {
      "service_type": "https",
      "port": 443,
      "is_secure": true,
      "is_enabled": true
    }
  ],
  "credentials": [
    {
      "credential_id": 1,
      "service_types": ["ssh"],
      "is_primary": true
    }
  ]
}
```

#### Response
```json
{
  "id": 1,
  "name": "Web Server 01",
  "hostname": "web01.company.com",
  "ip_address": "192.168.1.100",
  "os_type": "linux",
  "os_version": "Ubuntu 20.04",
  "description": "Production web server",
  "tags": ["production", "web", "frontend"],
  "services": [
    {
      "id": 1,
      "service_type": "ssh",
      "port": 22,
      "is_secure": true,
      "is_enabled": true,
      "discovery_method": "manual",
      "connection_status": "unknown"
    },
    {
      "id": 2,
      "service_type": "http",
      "port": 80,
      "is_secure": false,
      "is_enabled": true,
      "discovery_method": "manual",
      "connection_status": "unknown"
    },
    {
      "id": 3,
      "service_type": "https",
      "port": 443,
      "is_secure": true,
      "is_enabled": true,
      "discovery_method": "manual",
      "connection_status": "unknown"
    }
  ],
  "credentials": [
    {
      "id": 1,
      "credential_id": 1,
      "service_types": ["ssh"],
      "is_primary": true
    }
  ],
  "created_at": "2024-01-15T10:30:00Z"
}
```

## Frontend Changes

### New Enhanced Targets Page
- `TargetsEnhanced.tsx` - New multi-service interface
- Service management within target details
- Credential assignment per service type
- Filtering by OS type and service type

### Legacy Compatibility
- Original `Targets.tsx` continues to work
- Automatically converts between formats
- Gradual migration path for users

## Service Types

### Built-in Service Types
- `ssh` - Secure Shell (Linux/Unix)
- `winrm` - Windows Remote Management (HTTP)
- `winrm_https` - Windows Remote Management (HTTPS)
- `rdp` - Remote Desktop Protocol
- `snmp` - Simple Network Management Protocol
- `http` - HTTP Web Service
- `https` - HTTPS Web Service
- `smb` - Server Message Block
- `wmi` - Windows Management Instrumentation
- `sql_server` - Microsoft SQL Server
- `mysql` - MySQL Database
- `postgresql` - PostgreSQL Database

### Adding Custom Service Types
```sql
INSERT INTO service_definitions 
(service_type, display_name, default_port, is_secure_by_default, description)
VALUES 
('custom_service', 'Custom Service', 8080, false, 'Custom application service');
```

## Discovery Integration

The discovery service has been updated to work with the new architecture:

- Discovered targets can have multiple services
- Automatic service detection and classification
- Import process creates appropriate service records
- Duplicate detection considers all services

## Job Execution

Job execution remains compatible:
- Jobs can target specific services on a target
- Automatic service selection based on job requirements
- Credential resolution per service type

## Benefits

### For Administrators
- More accurate representation of infrastructure
- Better credential management
- Flexible service configuration
- Easier troubleshooting

### For Operations
- Multiple communication methods per target
- Service-specific monitoring
- Granular access control
- Better automation possibilities

## Troubleshooting

### Migration Issues

1. **Migration fails with constraint errors**
   ```bash
   # Check for duplicate hostnames
   SELECT hostname, COUNT(*) FROM targets GROUP BY hostname HAVING COUNT(*) > 1;
   ```

2. **Services not created during migration**
   ```bash
   # Check migration function output
   SELECT migrate_old_targets_to_new_schema();
   ```

3. **Frontend shows empty targets**
   - Clear browser cache
   - Check API endpoints are responding
   - Verify authentication tokens

### Performance Considerations

- Indexes are created on key columns
- Service queries are optimized
- Pagination works with filters

## Rollback Plan

If you need to rollback:

1. **Restore from backup**
   ```bash
   psql -d opsconductor < backup_before_migration.sql
   ```

2. **Use legacy endpoints**
   - Frontend can use legacy API calls
   - No code changes required

3. **Revert service files**
   ```bash
   cp targets-service/main_old_backup.py targets-service/main.py
   ```

## Future Enhancements

- Service health monitoring
- Automatic service discovery
- Service dependency mapping
- Performance metrics per service
- Custom service type plugins

## Support

For issues or questions:
1. Check the migration logs
2. Verify database schema
3. Test with legacy endpoints first
4. Check service health endpoints