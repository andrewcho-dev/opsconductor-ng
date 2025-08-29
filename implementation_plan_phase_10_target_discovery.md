# Phase 10: Target Discovery System

**Status:** 📋 PLANNED  
**Estimated Timeline:** 5 Weeks  
**Stack:** Python FastAPI, nmap-python, PostgreSQL, React TypeScript

---

## 🎯 **PHASE OVERVIEW**

Target Discovery will automatically find and catalog network devices, servers, and services across infrastructure, making it easy to onboard targets into OpsConductor without manual configuration. This system will provide automated network scanning, service detection, and bulk target import capabilities.

---

## 🏗️ **PROPOSED ARCHITECTURE**

### **Core Components**
- **Discovery Service** - New microservice for orchestrating discovery operations (Port 3010)
- **Discovery Engine** - Pluggable discovery methods (network scan, AD, cloud APIs)
- **Discovery Jobs** - Scheduled/on-demand discovery operations
- **Target Validation** - Automatic connection testing and capability detection
- **Discovery UI** - Frontend interface for managing discovery operations

---

## 📋 **IMPLEMENTATION PHASES**

### **PHASE 10.1: Discovery Service Foundation** (Week 1)

#### **New Service: `discovery-service` (Port 3010)**
```
discovery-service/
├── main.py                 # FastAPI service
├── discovery_engine.py     # Core discovery logic
├── network_scanner.py      # Network scanning capabilities
├── service_detector.py     # Service detection (WinRM, SSH, etc.)
├── target_validator.py     # Connection testing
├── discovery_models.py     # Data models
└── requirements.txt        # Dependencies (nmap-python, python-nmap, etc.)
```

#### **Database Schema Extensions**
```sql
-- Discovery operations tracking
CREATE TABLE discovery_jobs (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    discovery_type VARCHAR(50) NOT NULL, -- 'network_scan', 'ad_query', 'cloud_api'
    config JSONB NOT NULL,              -- Discovery configuration
    status VARCHAR(50) DEFAULT 'pending', -- 'pending', 'running', 'completed', 'failed'
    created_by INTEGER REFERENCES users(id),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    started_at TIMESTAMP,
    completed_at TIMESTAMP,
    results_summary JSONB                -- Summary of discovered targets
);

-- Discovered targets (before import to main targets table)
CREATE TABLE discovered_targets (
    id SERIAL PRIMARY KEY,
    discovery_job_id INTEGER REFERENCES discovery_jobs(id),
    hostname VARCHAR(255),
    ip_address INET NOT NULL,
    os_type VARCHAR(50),                 -- Detected OS
    os_version VARCHAR(255),
    services JSONB,                      -- Detected services (WinRM, SSH, etc.)
    preferred_service JSONB,             -- Auto-selected preferred service (HTTPS over HTTP)
    connection_test_results JSONB,       -- Test results for each service
    system_info JSONB,                   -- Additional system information
    duplicate_status VARCHAR(50) DEFAULT 'none', -- 'none', 'potential_duplicate', 'confirmed_duplicate'
    existing_target_id INTEGER REFERENCES targets(id), -- Reference to existing target if duplicate
    import_status VARCHAR(50) DEFAULT 'pending', -- 'pending', 'imported', 'ignored', 'duplicate_skipped'
    imported_target_id INTEGER REFERENCES targets(id),
    discovered_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Discovery templates for reusable configurations
CREATE TABLE discovery_templates (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    description TEXT,
    discovery_type VARCHAR(50) NOT NULL,
    config JSONB NOT NULL,
    created_by INTEGER REFERENCES users(id),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

#### **Core Discovery Service Implementation**
```python
from fastapi import FastAPI, BackgroundTasks
import nmap
import asyncio
from typing import List, Dict

class DiscoveryService:
    def __init__(self):
        self.nm = nmap.PortScanner()
        self.active_jobs = {}
    
    async def start_discovery_job(self, job_config: Dict) -> str:
        job_id = generate_job_id()
        self.active_jobs[job_id] = {
            'status': 'running',
            'config': job_config,
            'results': []
        }
        
        # Start discovery in background
        asyncio.create_task(self.run_discovery(job_id, job_config))
        return job_id
    
    async def run_discovery(self, job_id: str, config: Dict):
        try:
            if config['type'] == 'network_scan':
                await self.network_scan_discovery(job_id, config)
            elif config['type'] == 'ad_query':
                await self.active_directory_discovery(job_id, config)
            
            self.active_jobs[job_id]['status'] = 'completed'
        except Exception as e:
            self.active_jobs[job_id]['status'] = 'failed'
            self.active_jobs[job_id]['error'] = str(e)
```

---

### **PHASE 10.2: Network Discovery Engine** (Week 2)

#### **Discovery Methods**

**1. Network Range Scanning**
- CIDR range input (e.g., 192.168.1.0/24)
- Port scanning configuration (22/SSH, 5985-5986/WinRM, 3389/RDP)
- OS fingerprinting using nmap
- Service detection and connectivity testing

**2. Service Detection Logic**
```python
DETECTION_RULES = {
    "windows": {
        "indicators": [135, 445, 3389, 5985, 5986],
        "primary_service": "winrm",
        "test_ports": [5985, 5986]
    },
    "linux": {
        "indicators": [22],
        "primary_service": "ssh", 
        "test_ports": [22]
    }
}
```

#### **Network Scanner Implementation**
```python
class NetworkScanner:
    def __init__(self):
        self.nm = nmap.PortScanner()
    
    async def scan_network_range(self, cidr_range: str, ports: str = "22,135,445,3389,5985,5986"):
        """Scan network range for active hosts and services"""
        scan_result = self.nm.scan(hosts=cidr_range, ports=ports, arguments='-sS -O')
        
        discovered_hosts = []
        for host in scan_result['scan']:
            host_info = self.analyze_host(scan_result['scan'][host])
            if host_info:
                discovered_hosts.append(host_info)
        
        return discovered_hosts
    
    def analyze_host(self, host_data: Dict) -> Dict:
        """Analyze host data to determine OS and services"""
        if host_data['status']['state'] != 'up':
            return None
        
        host_info = {
            'ip_address': host_data.get('addresses', {}).get('ipv4'),
            'hostname': host_data.get('hostnames', [{}])[0].get('name', ''),
            'os_type': self.detect_os_type(host_data),
            'services': self.detect_services(host_data),
            'ports': host_data.get('tcp', {})
        }
        
        return host_info
    
    def detect_os_type(self, host_data: Dict) -> str:
        """Detect OS type based on open ports and OS fingerprinting"""
        open_ports = set(host_data.get('tcp', {}).keys())
        
        # Windows indicators
        if any(port in open_ports for port in [135, 445, 3389, 5985, 5986]):
            return 'windows'
        
        # Linux indicators
        if 22 in open_ports:
            return 'linux'
        
        # Check OS fingerprinting results
        os_matches = host_data.get('osmatch', [])
        if os_matches:
            os_name = os_matches[0].get('name', '').lower()
            if 'windows' in os_name:
                return 'windows'
            elif any(linux_dist in os_name for linux_dist in ['linux', 'ubuntu', 'centos', 'redhat']):
                return 'linux'
        
        return 'unknown'
    
    def detect_services(self, host_data: Dict) -> Tuple[List[Dict], Dict]:
        """Detect available services and determine preferred service"""
        services = []
        tcp_ports = host_data.get('tcp', {})
        
        # WinRM detection
        winrm_services = []
        if 5985 in tcp_ports and tcp_ports[5985]['state'] == 'open':
            winrm_http = {
                'type': 'winrm',
                'port': 5985,
                'transport': 'http',
                'confidence': 'high',
                'secure': False
            }
            services.append(winrm_http)
            winrm_services.append(winrm_http)
        
        if 5986 in tcp_ports and tcp_ports[5986]['state'] == 'open':
            winrm_https = {
                'type': 'winrm',
                'port': 5986,
                'transport': 'https',
                'confidence': 'high',
                'secure': True
            }
            services.append(winrm_https)
            winrm_services.append(winrm_https)
        
        # SSH detection
        if 22 in tcp_ports and tcp_ports[22]['state'] == 'open':
            ssh_service = {
                'type': 'ssh',
                'port': 22,
                'confidence': 'high',
                'secure': True
            }
            services.append(ssh_service)
        
        # Determine preferred service (HTTPS WinRM > SSH > HTTP WinRM)
        preferred_service = self.select_preferred_service(services)
        
        return services, preferred_service
    
    def select_preferred_service(self, services: List[Dict]) -> Dict:
        """Select preferred service based on security and availability"""
        if not services:
            return None
        
        # Priority: HTTPS WinRM > SSH > HTTP WinRM > Others
        winrm_https = next((s for s in services if s['type'] == 'winrm' and s['secure']), None)
        if winrm_https:
            return winrm_https
        
        ssh_service = next((s for s in services if s['type'] == 'ssh'), None)
        if ssh_service:
            return ssh_service
        
        winrm_http = next((s for s in services if s['type'] == 'winrm' and not s['secure']), None)
        if winrm_http:
            return winrm_http
        
        # Fallback to first available service
        return services[0]
```

---

### **PHASE 10.3: Discovery Job Management** (Week 3)

#### **Discovery Job Types**

**1. Network Scan Jobs**
```json
{
  "type": "network_scan",
  "name": "Office Network Discovery",
  "config": {
    "cidr_ranges": ["192.168.1.0/24", "10.0.0.0/16"],
    "scan_intensity": "standard",
    "ports": "22,3389,5985,5986",
    "os_detection": true,
    "service_detection": true,
    "connection_testing": false,
    "enhanced_detection": false,
    "credentials_id": null,
    "timeout": 300
  }
}
```

**Scan Intensity Options:**
- **light**: Common ports only (22, 3389, 5985)
- **standard**: Recommended ports (22, 3389, 5985, 5986) - Default
- **deep**: Extended port range (22, 135, 445, 3389, 5985, 5986, 80, 443)

**2. Active Directory Query Jobs**
```json
{
  "type": "ad_query",
  "name": "AD Computer Discovery",
  "config": {
    "domain": "company.local",
    "ldap_server": "dc01.company.local",
    "base_dn": "OU=Computers,DC=company,DC=local",
    "filter": "(&(objectClass=computer)(operatingSystem=Windows*))",
    "credentials_id": 123
  }
}
```

**3. Cloud API Discovery Jobs**
```json
{
  "type": "cloud_api",
  "name": "AWS EC2 Discovery",
  "config": {
    "provider": "aws",
    "regions": ["us-east-1", "us-west-2"],
    "instance_filters": {
      "state": "running",
      "tags": {"Environment": "production"}
    },
    "credentials_id": 456
  }
}
```

#### **Discovery Job Scheduler Integration**
```python
class DiscoveryScheduler:
    def __init__(self, scheduler_service):
        self.scheduler = scheduler_service
    
    def schedule_discovery_job(self, job_config: Dict, cron_expression: str):
        """Schedule recurring discovery jobs"""
        schedule_config = {
            'job_type': 'discovery',
            'job_config': job_config,
            'cron_expression': cron_expression,
            'timezone': job_config.get('timezone', 'UTC')
        }
        
        return self.scheduler.create_schedule(schedule_config)
    
    def execute_scheduled_discovery(self, schedule_id: str):
        """Execute a scheduled discovery job"""
        schedule = self.scheduler.get_schedule(schedule_id)
        discovery_service = DiscoveryService()
        return discovery_service.start_discovery_job(schedule['job_config'])
```

---

### **PHASE 10.4: Frontend Integration** (Week 4)

#### **Discovery Management UI**

**Discovery Dashboard**
```typescript
const DiscoveryDashboard = () => {
  const [discoveryJobs, setDiscoveryJobs] = useState([]);
  const [discoveredTargets, setDiscoveredTargets] = useState([]);
  
  return (
    <div className="discovery-dashboard">
      <DiscoveryJobList 
        jobs={discoveryJobs}
        onJobStart={startDiscoveryJob}
        onJobCancel={cancelDiscoveryJob}
      />
      <DiscoveredTargetsList 
        targets={discoveredTargets}
        onTargetImport={importTarget}
        onBulkImport={bulkImportTargets}
      />
    </div>
  );
};
```

**Network Scan Configuration**
```typescript
const NetworkScanConfig = () => {
  const [scanConfig, setScanConfig] = useState({
    cidr_ranges: [''],
    ports: '22,135,445,3389,5985,5986',
    os_detection: true,
    service_detection: true,
    connection_testing: true
  });
  
  const handleScanStart = async () => {
    const job = await discoveryAPI.startNetworkScan(scanConfig);
    // Handle job start
  };
  
  return (
    <form onSubmit={handleScanStart}>
      <CIDRRangeInput 
        ranges={scanConfig.cidr_ranges}
        onChange={updateCIDRRanges}
      />
      <PortConfiguration 
        ports={scanConfig.ports}
        onChange={updatePorts}
      />
      <ScanOptions 
        config={scanConfig}
        onChange={updateScanConfig}
      />
      <button type="submit">Start Discovery</button>
    </form>
  );
};
```

**Target Import Interface**
```typescript
const TargetImportWizard = ({ discoveredTargets }) => {
  const [selectedTargets, setSelectedTargets] = useState([]);
  const [importConfig, setImportConfig] = useState({});
  const [duplicateHandling, setDuplicateHandling] = useState('ask'); // 'ask', 'skip', 'update'
  
  const handleBulkImport = async () => {
    const importResults = await Promise.all(
      selectedTargets.map(target => 
        targetsAPI.importDiscoveredTarget(target, {
          ...importConfig,
          duplicateHandling: target.duplicate_status !== 'none' ? duplicateHandling : 'import'
        })
      )
    );
    // Handle import results
  };
  
  return (
    <div className="import-wizard">
      <TargetSelectionGrid 
        targets={discoveredTargets}
        selectedTargets={selectedTargets}
        onSelectionChange={setSelectedTargets}
        showDuplicateStatus={true}
      />
      <DuplicateHandlingOptions 
        handling={duplicateHandling}
        onChange={setDuplicateHandling}
        duplicateCount={selectedTargets.filter(t => t.duplicate_status !== 'none').length}
      />
      <ImportConfiguration 
        config={importConfig}
        onChange={setImportConfig}
      />
      <ImportPreview 
        targets={selectedTargets}
        config={importConfig}
        duplicateHandling={duplicateHandling}
      />
      <button onClick={handleBulkImport}>
        Import {selectedTargets.length} Targets
      </button>
    </div>
  );
};
```

---

### **PHASE 10.5: Testing & Integration** (Week 5)

#### **Discovery Testing Framework**
```python
class DiscoveryTestSuite:
    def test_network_scan_accuracy(self):
        """Test network scanning accuracy against known hosts"""
        known_hosts = self.setup_test_environment()
        scanner = NetworkScanner()
        
        results = scanner.scan_network_range("192.168.100.0/24")
        
        # Verify all known hosts were discovered
        discovered_ips = {host['ip_address'] for host in results}
        expected_ips = {host['ip'] for host in known_hosts}
        
        assert discovered_ips >= expected_ips, "Not all known hosts discovered"
    
    def test_service_detection_accuracy(self):
        """Test service detection accuracy"""
        test_targets = [
            {'ip': '192.168.100.10', 'expected_services': ['winrm']},
            {'ip': '192.168.100.20', 'expected_services': ['ssh']},
        ]
        
        scanner = NetworkScanner()
        for target in test_targets:
            result = scanner.analyze_host_services(target['ip'])
            detected_services = {svc['type'] for svc in result['services']}
            expected_services = set(target['expected_services'])
            
            assert detected_services >= expected_services
    
    def test_bulk_import_performance(self):
        """Test bulk target import performance"""
        large_discovery_result = self.generate_large_discovery_result(1000)
        
        start_time = time.time()
        import_results = bulk_import_targets(large_discovery_result)
        end_time = time.time()
        
        # Should complete within reasonable time
        assert end_time - start_time < 60, "Bulk import too slow"
        assert len(import_results['successful']) > 950, "Too many import failures"
```

---

## 🔧 **API ENDPOINTS**

### **Discovery Management**
```
POST   /api/v1/discovery/jobs           # Start discovery job
GET    /api/v1/discovery/jobs           # List discovery jobs
GET    /api/v1/discovery/jobs/:id       # Get discovery job details
DELETE /api/v1/discovery/jobs/:id       # Cancel discovery job
GET    /api/v1/discovery/jobs/:id/results # Get discovery results
```

### **Target Import**
```
GET    /api/v1/discovery/targets        # List discovered targets
POST   /api/v1/discovery/targets/import # Import discovered targets
POST   /api/v1/discovery/targets/bulk-import # Bulk import targets
DELETE /api/v1/discovery/targets/:id    # Remove discovered target
```

### **Discovery Templates**
```
POST   /api/v1/discovery/templates      # Create discovery template
GET    /api/v1/discovery/templates      # List discovery templates
GET    /api/v1/discovery/templates/:id  # Get template details
PUT    /api/v1/discovery/templates/:id  # Update template
DELETE /api/v1/discovery/templates/:id  # Delete template
```

### **Duplicate Detection**
```
POST   /api/v1/discovery/targets/check-duplicates  # Check for duplicate targets
GET    /api/v1/discovery/targets/duplicates        # List potential duplicates
```

---

## 🎯 **EXPECTED BENEFITS**

### **Operational Benefits**
- **Automated Onboarding**: Eliminate manual target configuration
- **Network Visibility**: Complete visibility into network infrastructure
- **Bulk Operations**: Import hundreds of targets simultaneously
- **Scheduled Discovery**: Keep target inventory up-to-date automatically

### **Time Savings**
- **95% Reduction**: In target onboarding time
- **Automated Detection**: Automatic service and OS detection
- **Bulk Import**: Mass target import with validation
- **Template Reuse**: Reusable discovery configurations

### **Accuracy Improvements**
- **Consistent Discovery**: Standardized target discovery process
- **Validation**: Automatic connection testing and validation
- **Error Reduction**: Eliminate manual configuration errors
- **Up-to-date Inventory**: Automated inventory maintenance

---

This phase will transform OpsConductor's target management from manual configuration to automated discovery, significantly reducing onboarding time and improving infrastructure visibility while maintaining security and accuracy standards.