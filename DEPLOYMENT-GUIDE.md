# 🚀 Deployment Guide: New Core Target Schema

## 📋 **Overview**
This guide walks you through deploying the new single-table target schema that replaces the old multi-table system.

## ⚠️ **IMPORTANT WARNINGS**
- **DATA LOSS**: All existing targets will be lost (fresh start approach)
- **DOWNTIME**: Brief service interruption during deployment
- **BACKUP**: Consider backing up existing data if needed for reference

## 🎯 **What's Being Deployed**

### ✅ **New Features**
- **Single Table Design** - `assets.targets` with 230+ fields
- **Device Type Field** - Prominent device categorization
- **OS Information** - Enhanced OS type, family, version fields
- **All Connection Methods** - SSH, WinRM, SNMP, HTTP, RDP, etc. in one record
- **Enhanced Tags** - 50+ pre-loaded system tags with categories
- **Better Performance** - No JOINs needed, comprehensive indexing

### 🗑️ **Removed Tables**
- `assets.enhanced_targets` (replaced by `assets.targets`)
- `assets.target_services` (embedded in `assets.targets`)
- `assets.target_groups` (replaced by tag system)
- `assets.target_group_memberships` (replaced by tag system)
- `assets.service_definitions` (no longer needed)

## 🚀 **Deployment Steps**

### **Step 1: Stop Services**
```bash
cd /home/opsconductor/opsconductor-ng
docker-compose down
```

### **Step 2: Backup Current Database (Optional)**
```bash
# Create backup of current database
docker-compose up -d postgres
docker exec opsconductor-postgres pg_dump -U postgres opsconductor > backup-$(date +%Y%m%d).sql
docker-compose down
```

### **Step 3: Deploy New Schema**
The new schema is already in place in `database/complete-schema.sql`. When you start the containers, PostgreSQL will automatically initialize with the new schema.

### **Step 4: Start Services**
```bash
# Start all services
docker-compose up -d

# Check logs to ensure everything started correctly
docker-compose logs -f asset-service
```

### **Step 5: Verify Deployment**
```bash
# Check if new tables exist
docker exec opsconductor-postgres psql -U postgres -d opsconductor -c "
SELECT table_name FROM information_schema.tables 
WHERE table_schema = 'assets' 
ORDER BY table_name;"

# Check if system tags were loaded
docker exec opsconductor-postgres psql -U postgres -d opsconductor -c "
SELECT COUNT(*) as tag_count FROM assets.tags WHERE is_system = true;"

# Test API endpoint
curl http://localhost:3000/api/assets/targets
```

## 🧪 **Testing the New System**

### **Test 1: Create a Target**
```bash
curl -X POST http://localhost:3000/api/assets/targets \
  -H "Content-Type: application/json" \
  -d '{
    "name": "test-server-01",
    "hostname": "test-server-01.local",
    "ip_address": "192.168.1.100",
    "device_type": "server",
    "os_type": "linux",
    "os_family": "ubuntu",
    "os_version": "20.04",
    "description": "Test server for new schema",
    "location": "datacenter-primary",
    "ssh_enabled": true,
    "ssh_port": 22,
    "ssh_username": "admin",
    "primary_connection": "ssh",
    "tag_ids": [1, 2, 3]
  }'
```

### **Test 2: List Targets**
```bash
curl http://localhost:3000/api/assets/targets
```

### **Test 3: Get Target Details**
```bash
curl http://localhost:3000/api/assets/targets/1
```

### **Test 4: List Tags**
```bash
curl http://localhost:3000/api/assets/tags
```

## 📊 **Expected Results**

### **Database Tables**
After deployment, you should see these tables in the `assets` schema:
- ✅ `targets` - Main target table (230+ fields)
- ✅ `tags` - Tag system (50+ pre-loaded tags)
- ✅ `target_tags` - Target-tag relationships

### **System Tags**
The system should have 50+ pre-loaded tags including:
- **Environment**: production, staging, development, testing
- **Device Types**: server, workstation, router, switch, firewall
- **OS Types**: windows, linux, unix, macos
- **OS Families**: ubuntu, debian, centos, rhel, windows-server
- **Functions**: web-server, database, app-server, api-gateway
- **Locations**: datacenter-primary, cloud-aws, cloud-azure, cloud-gcp

### **API Endpoints**
All existing endpoints should work with enhanced data:
- `GET /api/assets/targets` - List targets (enhanced fields)
- `POST /api/assets/targets` - Create target (comprehensive form)
- `GET /api/assets/targets/{id}` - Get target (full details)
- `PUT /api/assets/targets/{id}` - Update target
- `DELETE /api/assets/targets/{id}` - Delete target
- `GET /api/assets/tags` - List tags
- `POST /api/assets/tags` - Create custom tags
- `GET /api/assets/stats` - Get statistics

## 🎨 **Frontend Updates Needed**

The frontend will need updates to take advantage of the new schema:

### **Target Form Enhancements**
- **Collapsible Sections** (14 sections planned)
- **Device Type Dropdown** with predefined options
- **OS Information** prominently displayed
- **Enhanced Tag System** with categories and colors
- **Connection Method Sections** for each protocol

### **Target List Improvements**
- **Device Type Column** for better categorization
- **OS Information** in list view
- **Tag Display** with colors and categories
- **Connection Status** indicators

## 🔧 **Troubleshooting**

### **Issue: Services Won't Start**
```bash
# Check logs
docker-compose logs asset-service

# Common fix: Rebuild containers
docker-compose build --no-cache
docker-compose up -d
```

### **Issue: Database Connection Errors**
```bash
# Check PostgreSQL status
docker-compose logs postgres

# Verify database exists
docker exec opsconductor-postgres psql -U postgres -l
```

### **Issue: Missing Tables**
```bash
# Check if schema was applied
docker exec opsconductor-postgres psql -U postgres -d opsconductor -c "
SELECT table_name FROM information_schema.tables 
WHERE table_schema = 'assets';"

# If tables missing, manually apply schema
docker exec -i opsconductor-postgres psql -U postgres -d opsconductor < database/complete-schema.sql
```

### **Issue: API Errors**
```bash
# Check asset service logs
docker-compose logs -f asset-service

# Test database connection
docker exec opsconductor-postgres psql -U postgres -d opsconductor -c "SELECT COUNT(*) FROM assets.targets;"
```

## 🎉 **Success Indicators**

You'll know the deployment was successful when:

1. ✅ **Services Start Clean** - No errors in logs
2. ✅ **Database Schema** - New tables exist, old tables removed
3. ✅ **System Tags Loaded** - 50+ tags in database
4. ✅ **API Responds** - All endpoints return data
5. ✅ **Target Creation** - Can create targets with new fields
6. ✅ **Enhanced Data** - Targets show device type, OS info, etc.

## 📞 **Support**

If you encounter issues:
1. Check the logs: `docker-compose logs -f`
2. Verify database: `docker exec opsconductor-postgres psql -U postgres -d opsconductor`
3. Test API: `curl http://localhost:3000/api/assets/targets`
4. Review this guide for troubleshooting steps

## 🎯 **Next Steps**

After successful deployment:
1. **Update Frontend** - Implement collapsible form sections
2. **Create Targets** - Start adding targets with rich information
3. **Use Tags** - Organize targets with the enhanced tag system
4. **Monitor Performance** - Enjoy faster queries with single-table design

**Your target management system is now enterprise-grade! 🚀**