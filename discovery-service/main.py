#!/usr/bin/env python3
"""
Discovery Service - OpsConductor Microservice
Automated target discovery and network scanning
"""

import os
import logging
import asyncio
import uuid
import json
from typing import List, Optional, Dict, Any, Tuple
from datetime import datetime
from enum import Enum

import psycopg2
from psycopg2.extras import RealDictCursor, Json
from fastapi import FastAPI, HTTPException, Depends, status, BackgroundTasks
from fastapi.security import HTTPBearer
from pydantic import BaseModel, Field
import jwt
import nmap

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Discovery Service",
    description="Automated target discovery and network scanning for OpsConductor",
    version="1.0.0"
)

security = HTTPBearer()

# Database configuration
DB_CONFIG = {
    "host": os.getenv("DB_HOST", "postgres"),
    "port": int(os.getenv("DB_PORT", "5432")),
    "database": os.getenv("DB_NAME", "opsconductor"),
    "user": os.getenv("DB_USER", "opsconductor"),
    "password": os.getenv("DB_PASSWORD", "opsconductor123")
}

JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", "your-secret-key")

# Enums
class DiscoveryType(str, Enum):
    NETWORK_SCAN = "network_scan"
    AD_QUERY = "ad_query"
    CLOUD_API = "cloud_api"

class JobStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"

class ScanIntensity(str, Enum):
    LIGHT = "light"
    STANDARD = "standard"
    DEEP = "deep"

class ImportStatus(str, Enum):
    PENDING = "pending"
    IMPORTED = "imported"
    IGNORED = "ignored"
    DUPLICATE_SKIPPED = "duplicate_skipped"

class DuplicateStatus(str, Enum):
    NONE = "none"
    POTENTIAL_DUPLICATE = "potential_duplicate"
    CONFIRMED_DUPLICATE = "confirmed_duplicate"

# Pydantic models
class NetworkScanConfig(BaseModel):
    cidr_ranges: List[str] = Field(..., description="CIDR ranges to scan")
    scan_intensity: ScanIntensity = ScanIntensity.STANDARD
    ports: Optional[str] = None
    os_detection: bool = True
    service_detection: bool = True
    connection_testing: bool = False
    enhanced_detection: bool = False
    credentials_id: Optional[int] = None
    timeout: int = 300

class DiscoveryJobCreate(BaseModel):
    name: str
    discovery_type: DiscoveryType
    config: Dict[str, Any]

class DiscoveryJobUpdate(BaseModel):
    name: Optional[str] = None
    config: Optional[Dict[str, Any]] = None

class DiscoveryJobResponse(BaseModel):
    id: int
    name: str
    discovery_type: str
    config: Dict[str, Any]
    status: str
    created_by: int
    created_at: datetime
    started_at: Optional[datetime]
    completed_at: Optional[datetime]
    results_summary: Optional[Dict[str, Any]]

class DiscoveryJobListResponse(BaseModel):
    jobs: List[DiscoveryJobResponse]
    total: int

class DiscoveredTargetResponse(BaseModel):
    id: int
    discovery_job_id: int
    hostname: Optional[str]
    ip_address: str
    os_type: Optional[str]
    os_version: Optional[str]
    services: List[Dict[str, Any]]
    preferred_service: Optional[Dict[str, Any]]
    connection_test_results: Optional[Dict[str, Any]]
    system_info: Optional[Dict[str, Any]]
    duplicate_status: str
    existing_target_id: Optional[int]
    import_status: str
    discovered_at: datetime

class DiscoveredTargetListResponse(BaseModel):
    targets: List[DiscoveredTargetResponse]
    total: int

class DiscoveredTargetUpdate(BaseModel):
    hostname: Optional[str] = None
    os_type: Optional[str] = None
    os_version: Optional[str] = None
    import_status: Optional[ImportStatus] = None

class ServiceInfo(BaseModel):
    type: str
    port: int
    transport: Optional[str] = None
    confidence: str
    secure: bool = False

# Port configurations for different scan intensities
SCAN_PORTS = {
    ScanIntensity.LIGHT: "22,3389,5985",
    ScanIntensity.STANDARD: "22,3389,5985,5986",
    ScanIntensity.DEEP: "22,135,445,3389,5985,5986,80,443"
}

# Database connection
def get_db_connection():
    """Get database connection"""
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        return conn
    except Exception as e:
        logger.error(f"Database connection failed: {e}")
        raise HTTPException(status_code=500, detail="Database connection failed")

# Authentication
async def verify_token(token: str = Depends(security)):
    """Verify JWT token"""
    try:
        payload = jwt.decode(token.credentials, JWT_SECRET_KEY, algorithms=["HS256"])
        return payload
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid token")

# Network Scanner Class
class NetworkScanner:
    def __init__(self):
        self.nm = nmap.PortScanner()
    
    async def scan_network_range(self, cidr_range: str, ports: str = "22,3389,5985,5986") -> List[Dict]:
        """Scan network range for active hosts and services"""
        try:
            logger.info(f"Starting network scan for {cidr_range} on ports {ports}")
            # Use TCP connect scan with service detection
            # Use -PS to do TCP SYN ping on common ports instead of ICMP ping
            # This helps discover Windows hosts that block ICMP but have services running
            scan_result = self.nm.scan(hosts=cidr_range, ports=ports, arguments='-sT -sV --version-intensity 3 -PS22,80,135,139,443,445,3389,5985')
            
            discovered_hosts = []
            for host in scan_result['scan']:
                host_info = self.analyze_host(scan_result['scan'][host])
                if host_info:
                    # Debug logging
                    logger.info(f"Host {host}: Found services {host_info.get('services', [])}")
                    discovered_hosts.append(host_info)
            
            logger.info(f"Discovered {len(discovered_hosts)} hosts in {cidr_range}")
            return discovered_hosts
        except Exception as e:
            logger.error(f"Network scan failed for {cidr_range}: {e}")
            raise
    
    def analyze_host(self, host_data: Dict) -> Optional[Dict]:
        """Analyze host data to determine OS and services"""
        if host_data['status']['state'] != 'up':
            return None
        
        services, preferred_service = self.detect_services(host_data)
        
        host_info = {
            'ip_address': host_data.get('addresses', {}).get('ipv4'),
            'hostname': host_data.get('hostnames', [{}])[0].get('name', ''),
            'os_type': self.detect_os_type(host_data),
            'os_version': self.detect_os_version(host_data),
            'services': services,
            'preferred_service': preferred_service,
            'ports': host_data.get('tcp', {})
        }
        
        return host_info
    
    def detect_os_type(self, host_data: Dict) -> str:
        """Detect OS type based on open ports and OS fingerprinting"""
        tcp_ports = host_data.get('tcp', {})
        
        # Only consider ports that are actually "open", not "filtered" or "closed"
        open_ports = set()
        for port, port_info in tcp_ports.items():
            if port_info.get('state') == 'open':
                open_ports.add(port)
        
        # Windows indicators (only if ports are actually open)
        windows_ports = {135, 445, 3389, 5985, 5986}
        if any(port in open_ports for port in windows_ports):
            return 'Windows'
        
        # Linux indicators (SSH is typically Linux/Unix)
        if 22 in open_ports:
            return 'Linux'
        
        # Check OS fingerprinting results
        os_matches = host_data.get('osmatch', [])
        if os_matches:
            os_name = os_matches[0].get('name', '').lower()
            if 'windows' in os_name:
                return 'Windows'
            elif any(linux_dist in os_name for linux_dist in ['linux', 'ubuntu', 'centos', 'redhat']):
                return 'Linux'
        
        return 'Unknown'
    
    def detect_os_version(self, host_data: Dict) -> Optional[str]:
        """Detect OS version from fingerprinting"""
        os_matches = host_data.get('osmatch', [])
        if os_matches:
            return os_matches[0].get('name', '')
        return None
    
    def detect_services(self, host_data: Dict) -> Tuple[List[Dict], Optional[Dict]]:
        """Detect available services and determine preferred service"""
        services = []
        tcp_ports = host_data.get('tcp', {})
        
        # Debug logging
        ip_address = host_data.get('addresses', {}).get('ipv4', 'unknown')
        logger.info(f"Detecting services for {ip_address}. Open TCP ports: {list(tcp_ports.keys())}")
        
        # Detailed port state debugging
        for port, port_info in tcp_ports.items():
            logger.info(f"Port {port}: state={port_info.get('state')}, name={port_info.get('name')}, product={port_info.get('product')}, version={port_info.get('version')}")
        
        # WinRM detection
        if 5985 in tcp_ports and tcp_ports[5985]['state'] == 'open':
            winrm_http = {
                'type': 'winrm',
                'port': 5985,
                'transport': 'http',
                'confidence': 'high',
                'secure': False
            }
            services.append(winrm_http)
            logger.info(f"Found WinRM HTTP on {ip_address}:5985")
        
        if 5986 in tcp_ports and tcp_ports[5986]['state'] == 'open':
            winrm_https = {
                'type': 'winrm',
                'port': 5986,
                'transport': 'https',
                'confidence': 'high',
                'secure': True
            }
            services.append(winrm_https)
            logger.info(f"Found WinRM HTTPS on {ip_address}:5986")
        
        # SSH detection
        if 22 in tcp_ports and tcp_ports[22]['state'] == 'open':
            ssh_service = {
                'type': 'ssh',
                'port': 22,
                'confidence': 'high',
                'secure': True
            }
            services.append(ssh_service)
        
        # RDP detection
        if 3389 in tcp_ports and tcp_ports[3389]['state'] == 'open':
            rdp_service = {
                'type': 'rdp',
                'port': 3389,
                'confidence': 'high',
                'secure': False
            }
            services.append(rdp_service)
        
        # Determine preferred service
        preferred_service = self.select_preferred_service(services)
        
        return services, preferred_service
    
    def select_preferred_service(self, services: List[Dict]) -> Optional[Dict]:
        """Select preferred service based on security and availability"""
        if not services:
            return None
        
        # Priority: HTTPS WinRM > SSH > HTTP WinRM > RDP > Others
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

# Discovery Service Class
class DiscoveryService:
    def __init__(self):
        self.scanner = NetworkScanner()
        self.active_jobs = {}
    
    async def start_discovery_job(self, job_id: int, job_config: Dict, user_id: int) -> str:
        """Start a discovery job"""
        try:
            logger.info(f"Starting discovery job {job_id}")
            
            # Update job status to running
            conn = get_db_connection()
            with conn.cursor() as cursor:
                cursor.execute("""
                    UPDATE discovery_jobs 
                    SET status = %s, started_at = CURRENT_TIMESTAMP 
                    WHERE id = %s
                """, (JobStatus.RUNNING, job_id))
                conn.commit()
            conn.close()
            
            # Execute discovery based on type
            if job_config['discovery_type'] == DiscoveryType.NETWORK_SCAN:
                await self.network_scan_discovery(job_id, job_config['config'])
            else:
                raise HTTPException(status_code=400, detail=f"Discovery type {job_config['discovery_type']} not implemented")
            
            # Update job status to completed with detailed results summary
            conn = get_db_connection()
            with conn.cursor() as cursor:
                # Get total count of discovered targets for this job
                cursor.execute("SELECT COUNT(*) FROM discovered_targets WHERE discovery_job_id = %s", (job_id,))
                result = cursor.fetchone()
                target_count = result[0] if result else 0
                
                # Get breakdown by OS type
                cursor.execute("""
                    SELECT os_type, COUNT(*) 
                    FROM discovered_targets 
                    WHERE discovery_job_id = %s 
                    GROUP BY os_type
                """, (job_id,))
                os_breakdown_result = cursor.fetchall()
                os_breakdown = dict(os_breakdown_result) if os_breakdown_result else {}
                
                # Get breakdown by preferred service type
                cursor.execute("""
                    SELECT preferred_service->>'type' as service_type, COUNT(*) 
                    FROM discovered_targets 
                    WHERE discovery_job_id = %s AND preferred_service IS NOT NULL
                    GROUP BY preferred_service->>'type'
                """, (job_id,))
                service_breakdown_result = cursor.fetchall()
                service_breakdown = dict(service_breakdown_result) if service_breakdown_result else {}
                
                # Get count of targets with specific services - simplified approach
                service_counts_result = (0, 0, 0, 0)  # Default values for winrm, rdp, ssh, http
                try:
                    cursor.execute("""
                        SELECT 
                            COUNT(CASE WHEN services::text LIKE '%winrm%' THEN 1 END) as winrm_count,
                            COUNT(CASE WHEN services::text LIKE '%rdp%' THEN 1 END) as rdp_count,
                            COUNT(CASE WHEN services::text LIKE '%ssh%' THEN 1 END) as ssh_count,
                            COUNT(CASE WHEN services::text LIKE '%http%' THEN 1 END) as http_count
                        FROM discovered_targets 
                        WHERE discovery_job_id = %s
                    """, (job_id,))
                    result = cursor.fetchone()
                    if result:
                        service_counts_result = result
                except Exception as e:
                    logger.error(f"Error getting service counts: {e}")
                    service_counts_result = (0, 0, 0, 0)
                
                results_summary = {
                    "targets_found": target_count,
                    "status": "success",
                    "os_breakdown": os_breakdown,
                    "service_breakdown": service_breakdown,
                    "service_counts": {
                        "winrm": service_counts_result[0] if service_counts_result and len(service_counts_result) > 0 else 0,
                        "rdp": service_counts_result[1] if service_counts_result and len(service_counts_result) > 1 else 0,
                        "ssh": service_counts_result[2] if service_counts_result and len(service_counts_result) > 2 else 0,
                        "http": service_counts_result[3] if service_counts_result and len(service_counts_result) > 3 else 0
                    }
                }
                
                cursor.execute("""
                    UPDATE discovery_jobs 
                    SET status = %s, completed_at = CURRENT_TIMESTAMP, results_summary = %s
                    WHERE id = %s
                """, (JobStatus.COMPLETED, Json(results_summary), job_id))
                conn.commit()
            conn.close()
            
            # Enhanced logging with breakdown
            logger.info(f"Discovery job {job_id} completed successfully:")
            logger.info(f"  Total targets: {target_count}")
            logger.info(f"  OS breakdown: {os_breakdown}")
            logger.info(f"  Service breakdown: {service_breakdown}")
            logger.info(f"  WinRM hosts: {results_summary['service_counts']['winrm']}")
            logger.info(f"  RDP hosts: {results_summary['service_counts']['rdp']}")
            logger.info(f"  SSH hosts: {results_summary['service_counts']['ssh']}")
            
        except Exception as e:
            logger.error(f"Discovery job {job_id} failed: {e}")
            
            # Update job status to failed with error details and partial results
            conn = get_db_connection()
            with conn.cursor() as cursor:
                # Get count of any targets that were discovered before failure
                cursor.execute("SELECT COUNT(*) FROM discovered_targets WHERE discovery_job_id = %s", (job_id,))
                partial_count = cursor.fetchone()[0]
                
                results_summary = {
                    "targets_found": partial_count,
                    "status": "failed",
                    "error": str(e),
                    "partial_results": partial_count > 0
                }
                
                cursor.execute("""
                    UPDATE discovery_jobs 
                    SET status = %s, completed_at = CURRENT_TIMESTAMP, results_summary = %s
                    WHERE id = %s
                """, (JobStatus.FAILED, Json(results_summary), job_id))
                conn.commit()
            conn.close()
            raise
    
    async def network_scan_discovery(self, job_id: int, config: Dict):
        """Execute network scan discovery"""
        scan_config = NetworkScanConfig(**config)
        
        # Determine ports to scan
        ports = scan_config.ports or SCAN_PORTS[scan_config.scan_intensity]
        
        all_discovered_hosts = []
        failed_ranges = []
        successful_ranges = []
        
        # Scan each CIDR range
        for cidr_range in scan_config.cidr_ranges:
            try:
                discovered_hosts = await self.scanner.scan_network_range(cidr_range, ports)
                all_discovered_hosts.extend(discovered_hosts)
                successful_ranges.append(cidr_range)
                logger.info(f"Successfully scanned {cidr_range}: found {len(discovered_hosts)} hosts")
            except Exception as e:
                logger.error(f"Failed to scan {cidr_range}: {e}")
                failed_ranges.append({"range": cidr_range, "error": str(e)})
        
        # Check if ALL scans failed
        if len(failed_ranges) == len(scan_config.cidr_ranges):
            error_details = "; ".join([f"{fr['range']}: {fr['error']}" for fr in failed_ranges])
            raise Exception(f"All network scans failed. Errors: {error_details}")
        
        # Check if we found any targets at all
        if len(all_discovered_hosts) == 0 and len(successful_ranges) > 0:
            logger.warning(f"Network scan completed but found no targets in ranges: {successful_ranges}")
        
        # Store discovered targets in database
        await self.store_discovered_targets(job_id, all_discovered_hosts)
        
        # Log summary
        if failed_ranges:
            logger.warning(f"Network scan partially completed. Found {len(all_discovered_hosts)} targets. Failed ranges: {[fr['range'] for fr in failed_ranges]}")
        else:
            logger.info(f"Network scan discovery completed successfully. Found {len(all_discovered_hosts)} targets")
        
        # If some ranges failed but we got some results, that's still a partial success
        # Only fail completely if ALL ranges failed (handled above)
    
    async def store_discovered_targets(self, job_id: int, discovered_hosts: List[Dict]):
        """Store discovered targets in database with deduplication"""
        conn = get_db_connection()
        
        try:
            with conn.cursor() as cursor:
                for host in discovered_hosts:
                    ip_address = host['ip_address']
                    hostname = host.get('hostname')
                    
                    # Check if this target already exists in discovered_targets
                    existing_discovered = await self.check_existing_discovered_target(ip_address, hostname)
                    
                    if existing_discovered:
                        # Update existing discovered target with latest info
                        logger.info(f"Updating existing discovered target {ip_address} (ID: {existing_discovered['id']})")
                        cursor.execute("""
                            UPDATE discovered_targets 
                            SET hostname = COALESCE(%s, hostname),
                                os_type = COALESCE(%s, os_type),
                                os_version = COALESCE(%s, os_version),
                                services = %s,
                                preferred_service = %s,
                                system_info = %s,
                                discovery_job_id = %s,
                                discovered_at = CURRENT_TIMESTAMP
                            WHERE id = %s
                        """, (
                            hostname,
                            host.get('os_type'),
                            host.get('os_version'),
                            Json(host.get('services', [])),
                            Json(host.get('preferred_service')),
                            Json(host.get('ports', {})),
                            job_id,
                            existing_discovered['id']
                        ))
                        continue
                    
                    # Check for duplicates against registered targets
                    duplicate_status, existing_target_id = await self.check_for_duplicates(
                        ip_address, hostname
                    )
                    
                    # Insert new discovered target
                    cursor.execute("""
                        INSERT INTO discovered_targets (
                            discovery_job_id, hostname, ip_address, os_type, os_version,
                            services, preferred_service, system_info, duplicate_status,
                            existing_target_id, discovered_at
                        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, CURRENT_TIMESTAMP)
                    """, (
                        job_id,
                        hostname,
                        ip_address,
                        host.get('os_type'),
                        host.get('os_version'),
                        Json(host.get('services', [])),
                        Json(host.get('preferred_service')),
                        Json(host.get('ports', {})),
                        duplicate_status,
                        existing_target_id
                    ))
                
                conn.commit()
        except Exception as e:
            conn.rollback()
            logger.error(f"Failed to store discovered targets: {e}")
            raise
        finally:
            conn.close()
    
    async def check_existing_discovered_target(self, ip_address: str, hostname: str = None) -> Optional[Dict]:
        """Check if target already exists in discovered_targets table"""
        try:
            conn = get_db_connection()
            with conn.cursor(cursor_factory=RealDictCursor) as cursor:
                # Check by IP address first (primary key for uniqueness)
                cursor.execute("""
                    SELECT id, hostname, ip_address, import_status 
                    FROM discovered_targets 
                    WHERE ip_address = %s AND import_status = 'pending'
                """, (ip_address,))
                existing = cursor.fetchone()
                
                # If not found by IP and we have hostname, check by hostname
                if not existing and hostname:
                    cursor.execute("""
                        SELECT id, hostname, ip_address, import_status 
                        FROM discovered_targets 
                        WHERE hostname = %s AND import_status = 'pending'
                    """, (hostname,))
                    existing = cursor.fetchone()
                
            conn.close()
            return existing
        except Exception as e:
            logger.error(f"Error checking existing discovered target: {e}")
            return None
    
    async def check_for_duplicates(self, ip_address: str, hostname: str = None) -> Tuple[str, Optional[int]]:
        """Check if target already exists by IP address or hostname"""
        try:
            conn = get_db_connection()
            with conn.cursor() as cursor:
                # Check for duplicate by IP address OR hostname
                if hostname:
                    cursor.execute("""
                        SELECT id FROM targets WHERE hostname = %s OR hostname = %s
                    """, (ip_address, hostname))
                else:
                    cursor.execute("""
                        SELECT id FROM targets WHERE hostname = %s
                    """, (ip_address,))
                existing_target = cursor.fetchone()
            conn.close()
            
            if existing_target:
                return DuplicateStatus.POTENTIAL_DUPLICATE, existing_target[0]
            else:
                return DuplicateStatus.NONE, None
        except Exception as e:
            logger.error(f"Error checking for duplicates: {e}")
            return DuplicateStatus.NONE, None

# Global discovery service instance
discovery_service = DiscoveryService()

# Health check endpoint (no auth required)
@app.get("/health")
async def health_check():
    """Health check endpoint"""
    try:
        conn = get_db_connection()
        with conn.cursor() as cursor:
            cursor.execute("SELECT 1")
        conn.close()
        return {"status": "healthy", "service": "discovery-service"}
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return {"status": "unhealthy", "service": "discovery-service", "error": str(e)}

# Discovery job endpoints
@app.post("/discovery/jobs", response_model=DiscoveryJobResponse)
async def create_discovery_job(
    job: DiscoveryJobCreate, 
    background_tasks: BackgroundTasks,
    user: dict = Depends(verify_token)
):
    """Create and start a discovery job"""
    try:
        conn = get_db_connection()
        with conn.cursor(cursor_factory=RealDictCursor) as cursor:
            cursor.execute("""
                INSERT INTO discovery_jobs (name, discovery_type, config, created_by, created_at)
                VALUES (%s, %s, %s, %s, CURRENT_TIMESTAMP)
                RETURNING id, name, discovery_type, config, status, created_by, created_at, started_at, completed_at, results_summary
            """, (job.name, job.discovery_type, Json(job.config), user['user_id']))
            new_job = cursor.fetchone()
            conn.commit()
        conn.close()
        
        # Start discovery job in background
        background_tasks.add_task(
            discovery_service.start_discovery_job,
            new_job['id'],
            {'discovery_type': job.discovery_type, 'config': job.config},
            user['user_id']
        )
        
        logger.info(f"Created discovery job: {new_job['id']}")
        return new_job
    except Exception as e:
        logger.error(f"Error creating discovery job: {e}")
        raise HTTPException(status_code=500, detail="Failed to create discovery job")

@app.get("/discovery/jobs", response_model=DiscoveryJobListResponse)
async def get_discovery_jobs(skip: int = 0, limit: int = 100, user: dict = Depends(verify_token)):
    """Get all discovery jobs"""
    try:
        conn = get_db_connection()
        with conn.cursor(cursor_factory=RealDictCursor) as cursor:
            # Get total count
            cursor.execute("SELECT COUNT(*) FROM discovery_jobs")
            total = cursor.fetchone()['count']
            
            # Get jobs with pagination
            cursor.execute("""
                SELECT id, name, discovery_type, config, status, created_by, 
                       created_at, started_at, completed_at, results_summary
                FROM discovery_jobs 
                ORDER BY created_at DESC
                LIMIT %s OFFSET %s
            """, (limit, skip))
            jobs = cursor.fetchall()
        conn.close()
        
        return DiscoveryJobListResponse(jobs=jobs, total=total)
    except Exception as e:
        logger.error(f"Error fetching discovery jobs: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch discovery jobs")

@app.get("/discovery/jobs/{job_id}", response_model=DiscoveryJobResponse)
async def get_discovery_job(job_id: int, user: dict = Depends(verify_token)):
    """Get discovery job by ID"""
    try:
        conn = get_db_connection()
        with conn.cursor(cursor_factory=RealDictCursor) as cursor:
            cursor.execute("""
                SELECT id, name, discovery_type, config, status, created_by,
                       created_at, started_at, completed_at, results_summary
                FROM discovery_jobs 
                WHERE id = %s
            """, (job_id,))
            job = cursor.fetchone()
        conn.close()
        
        if not job:
            raise HTTPException(status_code=404, detail="Discovery job not found")
        
        return job
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching discovery job {job_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch discovery job")

@app.get("/discovery/jobs/{job_id}/summary")
async def get_discovery_job_summary(job_id: int, user: dict = Depends(verify_token)):
    """Get detailed discovery job results summary"""
    try:
        conn = get_db_connection()
        with conn.cursor(cursor_factory=RealDictCursor) as cursor:
            # Get job basic info
            cursor.execute("""
                SELECT id, name, discovery_type, status, results_summary, created_at, completed_at
                FROM discovery_jobs 
                WHERE id = %s
            """, (job_id,))
            job = cursor.fetchone()
            
            if not job:
                raise HTTPException(status_code=404, detail="Discovery job not found")
            
            # Get detailed target breakdown
            cursor.execute("""
                SELECT 
                    COUNT(*) as total_targets,
                    COUNT(CASE WHEN os_type = 'Windows' THEN 1 END) as windows_count,
                    COUNT(CASE WHEN os_type = 'Linux' THEN 1 END) as linux_count,
                    COUNT(CASE WHEN os_type IS NULL OR os_type = 'Unknown' THEN 1 END) as unknown_count,
                    COUNT(CASE WHEN preferred_service = 'winrm' THEN 1 END) as winrm_preferred,
                    COUNT(CASE WHEN preferred_service = 'rdp' THEN 1 END) as rdp_preferred,
                    COUNT(CASE WHEN preferred_service = 'ssh' THEN 1 END) as ssh_preferred
                FROM discovered_targets 
                WHERE discovery_job_id = %s
            """, (job_id,))
            stats = cursor.fetchone()
            
            # Get sample targets for preview
            cursor.execute("""
                SELECT ip_address, hostname, os_type, preferred_service, services
                FROM discovered_targets 
                WHERE discovery_job_id = %s
                ORDER BY ip_address
                LIMIT 10
            """, (job_id,))
            sample_targets = cursor.fetchall()
            
            return {
                "job_id": job['id'],
                "name": job['name'],
                "discovery_type": job['discovery_type'],
                "status": job['status'],
                "results_summary": job['results_summary'],
                "created_at": job['created_at'],
                "completed_at": job['completed_at'],
                "detailed_stats": {
                    "total_targets": stats['total_targets'] or 0,
                    "os_breakdown": {
                        "windows": stats['windows_count'] or 0,
                        "linux": stats['linux_count'] or 0,
                        "unknown": stats['unknown_count'] or 0
                    },
                    "preferred_service_breakdown": {
                        "winrm": stats['winrm_preferred'] or 0,
                        "rdp": stats['rdp_preferred'] or 0,
                        "ssh": stats['ssh_preferred'] or 0
                    }
                },
                "sample_targets": [
                    {
                        "ip_address": target['ip_address'],
                        "hostname": target['hostname'],
                        "os_type": target['os_type'],
                        "preferred_service": target['preferred_service'],
                        "services": target['services']
                    }
                    for target in sample_targets
                ]
            }
        conn.close()
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching discovery job summary {job_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch discovery job summary")

@app.get("/discovery/targets", response_model=DiscoveredTargetListResponse)
async def get_discovered_targets(
    skip: int = 0,
    limit: int = 100,
    job_id: Optional[int] = None,
    import_status: Optional[ImportStatus] = None,
    user: dict = Depends(verify_token)
):
    """Get discovered targets"""
    try:
        conn = get_db_connection()
        with conn.cursor(cursor_factory=RealDictCursor) as cursor:
            # Build base query and params
            base_query = "FROM discovered_targets WHERE 1=1"
            params = []
            
            if job_id:
                base_query += " AND discovery_job_id = %s"
                params.append(job_id)
            
            if import_status:
                base_query += " AND import_status = %s"
                params.append(import_status)
            
            # Get total count
            cursor.execute(f"SELECT COUNT(*) {base_query}", params)
            total = cursor.fetchone()['count']
            
            # Get targets with pagination
            query = f"""
                SELECT id, discovery_job_id, hostname, ip_address, os_type, os_version,
                       services, preferred_service, connection_test_results, system_info,
                       duplicate_status, existing_target_id, import_status, discovered_at
                {base_query}
                ORDER BY discovered_at DESC
                LIMIT %s OFFSET %s
            """
            
            cursor.execute(query, params + [limit, skip])
            targets = cursor.fetchall()
        conn.close()
        
        return DiscoveredTargetListResponse(targets=targets, total=total)
    except Exception as e:
        logger.error(f"Error fetching discovered targets: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch discovered targets")

# Target import/ignore models
class TargetImportRequest(BaseModel):
    target_ids: List[int]
    credential_id: Optional[int] = None
    group_id: Optional[int] = None

class TargetIgnoreRequest(BaseModel):
    target_ids: List[int]

@app.post("/discovery/targets/import")
async def import_discovered_targets(
    import_request: TargetImportRequest,
    user: dict = Depends(verify_token)
):
    """Import discovered targets into the main targets system"""
    try:
        conn = get_db_connection()
        imported_count = 0
        failed_count = 0
        details = []
        
        with conn.cursor(cursor_factory=RealDictCursor) as cursor:
            for target_id in import_request.target_ids:
                try:
                    # Get discovered target details
                    cursor.execute("""
                        SELECT * FROM discovered_targets WHERE id = %s
                    """, (target_id,))
                    discovered_target = cursor.fetchone()
                    
                    if not discovered_target:
                        failed_count += 1
                        details.append({"target_id": target_id, "error": "Target not found"})
                        continue
                    
                    # Check if already imported or is duplicate
                    if discovered_target['import_status'] == ImportStatus.IMPORTED:
                        details.append({"target_id": target_id, "status": "already_imported"})
                        continue
                    
                    # Create target exactly as if adding from scratch
                    # Clean field mapping from discovered target to target table
                    
                    # Map basic fields
                    target_name = discovered_target['hostname'] or str(discovered_target['ip_address'])
                    hostname = discovered_target['hostname'] or str(discovered_target['ip_address'])
                    ip_address = discovered_target['ip_address']
                    
                    # Map protocol and port from preferred service
                    if discovered_target['preferred_service']:
                        protocol = discovered_target['preferred_service']['type']
                        port = discovered_target['preferred_service']['port']
                    else:
                        # Default based on OS type
                        if discovered_target['os_type'] and discovered_target['os_type'].lower() in ['linux', 'unix', 'macos']:
                            protocol = 'ssh'
                            port = 22
                        else:
                            protocol = 'winrm'
                            port = 5985
                    
                    # Map OS type to allowed values
                    os_type_mapping = {
                        'Linux': 'linux',
                        'Windows': 'windows', 
                        'Unix': 'unix',
                        'MacOS': 'macos',
                        'Darwin': 'macos'
                    }
                    os_type = os_type_mapping.get(discovered_target['os_type'], 'windows')
                    
                    # Ensure unique target name
                    base_name = target_name
                    counter = 1
                    while True:
                        cursor.execute("SELECT id FROM targets WHERE name = %s", (target_name,))
                        if not cursor.fetchone():
                            break
                        target_name = f"{base_name}-{counter}"
                        counter += 1
                    
                    # Get credential (required field)
                    credential_id = import_request.credential_id
                    if not credential_id:
                        cursor.execute("SELECT id FROM credentials LIMIT 1")
                        cred_result = cursor.fetchone()
                        credential_id = cred_result['id'] if cred_result else None
                        
                    if not credential_id:
                        raise Exception("No credentials available for import")
                    
                    # Build metadata with discovery context (optional additional data)
                    metadata = {
                        'imported_from_discovery': True,
                        'discovery_job_id': discovered_target['discovery_job_id'],
                        'discovered_at': discovered_target['discovered_at'].isoformat() if discovered_target['discovered_at'] else None,
                        'all_services': discovered_target['services'],
                        'os_version': discovered_target['os_version']
                    }
                    
                    # Insert new target (exactly like manual creation)
                    cursor.execute("""
                        INSERT INTO targets (
                            name, hostname, ip_address, protocol, port, 
                            credential_ref, os_type, metadata, created_at
                        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, CURRENT_TIMESTAMP)
                        RETURNING id
                    """, (
                        target_name,
                        hostname,
                        ip_address,
                        protocol,
                        port,
                        credential_id,
                        os_type,
                        json.dumps(metadata)
                    ))
                    
                    new_target = cursor.fetchone()
                    
                    # Delete discovered target after successful import
                    cursor.execute("""
                        DELETE FROM discovered_targets WHERE id = %s
                    """, (target_id,))
                    
                    imported_count += 1
                    details.append({
                        "target_id": target_id, 
                        "new_target_id": new_target['id'],
                        "status": "imported_and_removed"
                    })
                    
                except Exception as e:
                    failed_count += 1
                    details.append({"target_id": target_id, "error": str(e)})
                    logger.error(f"Failed to import target {target_id}: {e}")
            
            conn.commit()
        conn.close()
        
        logger.info(f"Import completed: {imported_count} imported, {failed_count} failed")
        return {
            "imported": imported_count,
            "failed": failed_count,
            "details": details
        }
        
    except Exception as e:
        logger.error(f"Error importing targets: {e}")
        raise HTTPException(status_code=500, detail="Failed to import targets")

@app.post("/discovery/targets/ignore")
async def ignore_discovered_targets(
    ignore_request: TargetIgnoreRequest,
    user: dict = Depends(verify_token)
):
    """Mark discovered targets as ignored"""
    try:
        conn = get_db_connection()
        ignored_count = 0
        
        with conn.cursor() as cursor:
            for target_id in ignore_request.target_ids:
                cursor.execute("""
                    DELETE FROM discovered_targets 
                    WHERE id = %s AND import_status = %s
                """, (target_id, ImportStatus.PENDING))
                
                if cursor.rowcount > 0:
                    ignored_count += 1
            
            conn.commit()
        conn.close()
        
        logger.info(f"Ignored {ignored_count} targets")
        return {"ignored": ignored_count}
        
    except Exception as e:
        logger.error(f"Error ignoring targets: {e}")
        raise HTTPException(status_code=500, detail="Failed to ignore targets")

@app.delete("/discovery/targets/bulk")
async def bulk_delete_discovered_targets(
    delete_request: TargetIgnoreRequest,  # Reuse the same model since it just needs target_ids
    user: dict = Depends(verify_token)
):
    """Bulk delete discovered targets"""
    try:
        conn = get_db_connection()
        deleted_count = 0
        
        with conn.cursor() as cursor:
            for target_id in delete_request.target_ids:
                cursor.execute("""
                    DELETE FROM discovered_targets WHERE id = %s
                """, (target_id,))
                
                if cursor.rowcount > 0:
                    deleted_count += 1
            
            conn.commit()
        conn.close()
        
        logger.info(f"Bulk deleted {deleted_count} targets")
        return {"deleted": deleted_count}
        
    except Exception as e:
        logger.error(f"Error bulk deleting targets: {e}")
        raise HTTPException(status_code=500, detail="Failed to bulk delete targets")

@app.delete("/discovery/jobs/{job_id}")
async def delete_discovery_job(job_id: int, user: dict = Depends(verify_token)):
    """Delete a discovery job and its associated targets"""
    try:
        conn = get_db_connection()
        with conn.cursor() as cursor:
            # Delete associated discovered targets first
            cursor.execute("DELETE FROM discovered_targets WHERE discovery_job_id = %s", (job_id,))
            
            # Delete the job
            cursor.execute("DELETE FROM discovery_jobs WHERE id = %s", (job_id,))
            
            if cursor.rowcount == 0:
                raise HTTPException(status_code=404, detail="Discovery job not found")
            
            conn.commit()
        conn.close()
        
        logger.info(f"Deleted discovery job {job_id}")
        return {"message": "Discovery job deleted successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting discovery job {job_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to delete discovery job")

@app.put("/discovery/jobs/{job_id}", response_model=DiscoveryJobResponse)
async def update_discovery_job(
    job_id: int, 
    job_update: DiscoveryJobUpdate, 
    user: dict = Depends(verify_token)
):
    """Update a discovery job (only if not running/completed)"""
    try:
        conn = get_db_connection()
        with conn.cursor(cursor_factory=RealDictCursor) as cursor:
            # First check if job exists and get current status
            cursor.execute("""
                SELECT id, name, discovery_type, config, status, created_by,
                       created_at, started_at, completed_at, results_summary
                FROM discovery_jobs 
                WHERE id = %s
            """, (job_id,))
            current_job = cursor.fetchone()
            
            if not current_job:
                raise HTTPException(status_code=404, detail="Discovery job not found")
            
            # Only allow updates if job is pending or failed
            if current_job['status'] not in [JobStatus.PENDING, JobStatus.FAILED]:
                raise HTTPException(
                    status_code=400, 
                    detail=f"Cannot update job with status '{current_job['status']}'. Only pending or failed jobs can be updated."
                )
            
            # Build update query dynamically
            update_fields = []
            update_values = []
            
            if job_update.name is not None:
                update_fields.append("name = %s")
                update_values.append(job_update.name)
            
            if job_update.config is not None:
                update_fields.append("config = %s")
                update_values.append(Json(job_update.config))
            
            if not update_fields:
                # No updates provided, return current job
                return current_job
            
            # Add job_id to values for WHERE clause
            update_values.append(job_id)
            
            # Execute update
            cursor.execute(f"""
                UPDATE discovery_jobs 
                SET {', '.join(update_fields)}
                WHERE id = %s
                RETURNING id, name, discovery_type, config, status, created_by,
                         created_at, started_at, completed_at, results_summary
            """, update_values)
            
            updated_job = cursor.fetchone()
            conn.commit()
        conn.close()
        
        logger.info(f"Updated discovery job {job_id}")
        return updated_job
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating discovery job {job_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to update discovery job")

@app.get("/discovery/targets/{target_id}", response_model=DiscoveredTargetResponse)
async def get_discovered_target(target_id: int, user: dict = Depends(verify_token)):
    """Get a specific discovered target by ID"""
    try:
        conn = get_db_connection()
        with conn.cursor(cursor_factory=RealDictCursor) as cursor:
            cursor.execute("""
                SELECT id, discovery_job_id, hostname, ip_address, os_type, os_version,
                       services, preferred_service, connection_test_results, system_info,
                       duplicate_status, existing_target_id, import_status, discovered_at
                FROM discovered_targets 
                WHERE id = %s
            """, (target_id,))
            target = cursor.fetchone()
        conn.close()
        
        if not target:
            raise HTTPException(status_code=404, detail="Discovered target not found")
        
        return target
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching discovered target {target_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch discovered target")

@app.put("/discovery/targets/{target_id}", response_model=DiscoveredTargetResponse)
async def update_discovered_target(
    target_id: int, 
    target_update: DiscoveredTargetUpdate, 
    user: dict = Depends(verify_token)
):
    """Update a discovered target"""
    try:
        conn = get_db_connection()
        with conn.cursor(cursor_factory=RealDictCursor) as cursor:
            # First check if target exists
            cursor.execute("""
                SELECT id FROM discovered_targets WHERE id = %s
            """, (target_id,))
            
            if not cursor.fetchone():
                raise HTTPException(status_code=404, detail="Discovered target not found")
            
            # Build update query dynamically
            update_fields = []
            update_values = []
            
            if target_update.hostname is not None:
                update_fields.append("hostname = %s")
                update_values.append(target_update.hostname)
            
            if target_update.os_type is not None:
                update_fields.append("os_type = %s")
                update_values.append(target_update.os_type)
            
            if target_update.os_version is not None:
                update_fields.append("os_version = %s")
                update_values.append(target_update.os_version)
            
            if target_update.import_status is not None:
                update_fields.append("import_status = %s")
                update_values.append(target_update.import_status)
            
            if not update_fields:
                # No updates provided, fetch and return current target
                cursor.execute("""
                    SELECT id, discovery_job_id, hostname, ip_address, os_type, os_version,
                           services, preferred_service, connection_test_results, system_info,
                           duplicate_status, existing_target_id, import_status, discovered_at
                    FROM discovered_targets 
                    WHERE id = %s
                """, (target_id,))
                return cursor.fetchone()
            
            # Add target_id to values for WHERE clause
            update_values.append(target_id)
            
            # Execute update
            cursor.execute(f"""
                UPDATE discovered_targets 
                SET {', '.join(update_fields)}
                WHERE id = %s
                RETURNING id, discovery_job_id, hostname, ip_address, os_type, os_version,
                         services, preferred_service, connection_test_results, system_info,
                         duplicate_status, existing_target_id, import_status, discovered_at
            """, update_values)
            
            updated_target = cursor.fetchone()
            conn.commit()
        conn.close()
        
        logger.info(f"Updated discovered target {target_id}")
        return updated_target
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating discovered target {target_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to update discovered target")

@app.delete("/discovery/targets/{target_id}")
async def delete_discovered_target(target_id: int, user: dict = Depends(verify_token)):
    """Delete a discovered target"""
    try:
        conn = get_db_connection()
        with conn.cursor() as cursor:
            cursor.execute("DELETE FROM discovered_targets WHERE id = %s", (target_id,))
            
            if cursor.rowcount == 0:
                raise HTTPException(status_code=404, detail="Discovered target not found")
            
            conn.commit()
        conn.close()
        
        logger.info(f"Deleted discovered target {target_id}")
        return {"message": "Discovered target deleted successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting discovered target {target_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to delete discovered target")

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", "3010"))
    uvicorn.run(app, host="0.0.0.0", port=port)