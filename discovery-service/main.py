#!/usr/bin/env python3
"""
Discovery Service - OpsConductor Microservice
Automated target discovery and network scanning
"""

import os
import sys
import asyncio
import uuid
import json
import ipaddress
import re
from typing import List, Optional, Dict, Any, Tuple
from datetime import datetime
from enum import Enum
import httpx

# Add shared module to path
sys.path.append('/home/opsconductor')

from fastapi import FastAPI, HTTPException, Depends, status, BackgroundTasks, Header
from pydantic import BaseModel, Field
import jwt
import nmap

# Import shared modules
from shared.database import get_db_cursor, check_database_health, cleanup_database_pool
from shared.logging import setup_service_logging, get_logger, log_startup, log_shutdown
from shared.middleware import add_standard_middleware
from shared.models import HealthResponse, HealthCheck, create_success_response
from shared.errors import DatabaseError, ValidationError, NotFoundError, PermissionError, handle_database_error
from shared.auth import get_current_user, require_admin
from shared.utils import get_service_client

# Setup structured logging
setup_service_logging("discovery-service", level=os.getenv("LOG_LEVEL", "INFO"))
logger = get_logger("discovery-service")

app = FastAPI(
    title="Discovery Service",
    description="Automated target discovery and network scanning for OpsConductor",
    version="1.0.0"
)

# Add standard middleware
add_standard_middleware(app, "discovery-service", version="1.0.0")

# Database configuration is now handled by shared.database module

JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", "your-secret-key")
AUTH_SERVICE_URL = os.getenv("AUTH_SERVICE_URL", "http://auth-service:3001")

# Enums
class JobStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"



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
class DiscoveryService(BaseModel):
    name: str
    port: int
    protocol: str = "tcp"
    category: str
    enabled: bool

class NetworkScanConfig(BaseModel):
    cidr_ranges: List[str] = Field(..., description="Network ranges to scan (supports CIDR, IP ranges, individual IPs, and mixed formats)")
    services: Optional[List[DiscoveryService]] = None
    ports: Optional[str] = None
    os_detection: bool = True
    enhanced_detection: bool = False
    credentials_id: Optional[int] = None
    timeout: int = 300

class DiscoveryJobCreate(BaseModel):
    name: str
    discovery_type: str
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



# Network range parsing utilities
class NetworkRangeParser:
    """Utility class for parsing various network range formats"""
    
    @staticmethod
    def parse_network_ranges(range_input: str) -> List[str]:
        """
        Parse various network range formats and return a list of individual IP addresses or CIDR ranges.
        
        Supported formats:
        - CIDR: 192.168.1.0/24
        - IP Range: 192.168.1.100-120 or 192.168.1.100-192.168.1.120
        - Individual IPs: 192.168.1.20, 192.168.1.22, 192.168.1.25
        - Mixed: 192.168.1.23, 192.168.1.26-32, 10.0.0.0/24
        """
        if not range_input or not range_input.strip():
            return []
        
        # Split by commas first to handle multiple entries
        entries = [entry.strip() for entry in range_input.split(',') if entry.strip()]
        all_targets = []
        
        for entry in entries:
            try:
                targets = NetworkRangeParser._parse_single_entry(entry)
                all_targets.extend(targets)
            except Exception as e:
                logger.warning(f"Failed to parse network range entry '{entry}': {e}")
                continue
        
        return all_targets
    
    @staticmethod
    def _parse_single_entry(entry: str) -> List[str]:
        """Parse a single network range entry"""
        entry = entry.strip()
        
        # Check if it's a CIDR range
        if '/' in entry:
            return NetworkRangeParser._parse_cidr(entry)
        
        # Check if it's an IP range
        elif '-' in entry:
            return NetworkRangeParser._parse_ip_range(entry)
        
        # Check if it's a single IP
        else:
            return NetworkRangeParser._parse_single_ip(entry)
    
    @staticmethod
    def _parse_cidr(cidr: str) -> List[str]:
        """Parse CIDR notation (e.g., 192.168.1.0/24)"""
        try:
            network = ipaddress.ip_network(cidr, strict=False)
            # For large networks (>1000 hosts), return as CIDR for efficiency
            if network.num_addresses > 1000:
                return [str(network)]
            else:
                # For smaller networks, return individual IPs
                return [str(ip) for ip in network.hosts()]
        except ValueError as e:
            raise ValueError(f"Invalid CIDR format '{cidr}': {e}")
    
    @staticmethod
    def _parse_ip_range(ip_range: str) -> List[str]:
        """Parse IP range (e.g., 192.168.1.100-120 or 192.168.1.100-192.168.1.120)"""
        try:
            start_ip, end_part = ip_range.split('-', 1)
            start_ip = start_ip.strip()
            end_part = end_part.strip()
            
            # Validate start IP
            start_addr = ipaddress.ip_address(start_ip)
            
            # Check if end_part is just a number (short form) or full IP
            if '.' in end_part:
                # Full IP address
                end_addr = ipaddress.ip_address(end_part)
            else:
                # Short form - just the last octet
                if not end_part.isdigit():
                    raise ValueError(f"Invalid range end '{end_part}' - must be a number or full IP")
                
                end_octet = int(end_part)
                if end_octet < 0 or end_octet > 255:
                    raise ValueError(f"Invalid range end '{end_part}' - must be between 0-255")
                
                # Construct full end IP
                start_parts = str(start_addr).split('.')
                end_ip = f"{start_parts[0]}.{start_parts[1]}.{start_parts[2]}.{end_octet}"
                end_addr = ipaddress.ip_address(end_ip)
            
            # Generate IP list
            if start_addr > end_addr:
                raise ValueError(f"Start IP {start_addr} is greater than end IP {end_addr}")
            
            ips = []
            current = int(start_addr)
            end = int(end_addr)
            
            while current <= end:
                ips.append(str(ipaddress.ip_address(current)))
                current += 1
                
                # Safety limit to prevent memory issues
                if len(ips) > 10000:
                    raise ValueError(f"IP range too large (>10000 addresses): {ip_range}")
            
            return ips
            
        except ValueError as e:
            raise ValueError(f"Invalid IP range format '{ip_range}': {e}")
    
    @staticmethod
    def _parse_single_ip(ip: str) -> List[str]:
        """Parse and validate a single IP address"""
        try:
            ipaddress.ip_address(ip)
            return [ip]
        except ValueError as e:
            raise ValueError(f"Invalid IP address '{ip}': {e}")
    
    @staticmethod
    def optimize_targets_for_nmap(targets: List[str]) -> List[str]:
        """
        Optimize target list for nmap scanning by grouping consecutive IPs into ranges
        and keeping CIDR ranges as-is.
        """
        if not targets:
            return []
        
        # Separate CIDR ranges from individual IPs
        cidr_ranges = []
        individual_ips = []
        
        for target in targets:
            if '/' in target:
                cidr_ranges.append(target)
            else:
                try:
                    individual_ips.append(ipaddress.ip_address(target))
                except ValueError:
                    # If it's not a valid IP, keep it as-is (might be hostname)
                    cidr_ranges.append(target)
        
        # Sort individual IPs
        individual_ips.sort()
        
        # Group consecutive IPs into ranges
        optimized = cidr_ranges.copy()
        if individual_ips:
            optimized.extend(NetworkRangeParser._group_consecutive_ips(individual_ips))
        
        return optimized
    
    @staticmethod
    def _group_consecutive_ips(ips: List[ipaddress.IPv4Address]) -> List[str]:
        """Group consecutive IP addresses into ranges for efficient nmap scanning"""
        if not ips:
            return []
        
        groups = []
        current_group = [ips[0]]
        
        for i in range(1, len(ips)):
            if int(ips[i]) == int(current_group[-1]) + 1:
                current_group.append(ips[i])
            else:
                # End current group and start new one
                groups.append(current_group)
                current_group = [ips[i]]
        
        # Add the last group
        groups.append(current_group)
        
        # Convert groups to nmap-friendly format
        result = []
        for group in groups:
            if len(group) == 1:
                result.append(str(group[0]))
            elif len(group) == 2:
                result.extend([str(group[0]), str(group[1])])
            else:
                # Use nmap range format for 3+ consecutive IPs
                start_ip = str(group[0])
                end_ip = str(group[-1])
                
                # Check if they're in the same subnet for range notation
                start_parts = start_ip.split('.')
                end_parts = end_ip.split('.')
                
                if start_parts[:3] == end_parts[:3]:
                    # Same subnet - use short range notation
                    result.append(f"{start_ip}-{end_parts[3]}")
                else:
                    # Different subnets - use full range notation
                    result.append(f"{start_ip}-{end_ip}")
        
        return result

# Database connection is now handled by shared.database module

# Authentication
def verify_token_with_auth_service(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Verify token with auth service"""
    try:
        headers = {"Authorization": f"Bearer {credentials.credentials}"}
        response = requests.get(f"{AUTH_SERVICE_URL}/verify", headers=headers, timeout=10)
        
        if response.status_code != 200:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token"
            )
            
        return response.json()["user"]
        
    except requests.RequestException as e:
        logger.error(f"Auth service request failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Auth service unavailable"
        )

def verify_token_manual(credentials: HTTPAuthorizationCredentials):
    """Verify token with auth service (manual call)"""
    try:
        headers = {"Authorization": f"Bearer {credentials.credentials}"}
        response = requests.get(f"{AUTH_SERVICE_URL}/verify", headers=headers, timeout=10)
        
        if response.status_code != 200:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token"
            )
            
        return response.json()["user"]
        
    except requests.RequestException as e:
        logger.error(f"Auth service request failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Auth service unavailable"
        )

async def require_admin_or_operator_role(current_user: dict = Depends(verify_token_with_auth_service)):
    """Require admin or operator role"""
    if current_user["role"] not in ["admin", "operator"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin or operator role required"
        )
    return current_user

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
            return 'windows'  # lowercase to match database constraint
        
        # Linux indicators (SSH is typically Linux/Unix)
        if 22 in open_ports:
            return 'linux'  # lowercase to match database constraint
        
        # Check OS fingerprinting results
        os_matches = host_data.get('osmatch', [])
        if os_matches:
            os_name = os_matches[0].get('name', '').lower()
            if 'windows' in os_name:
                return 'windows'  # lowercase to match database constraint
            elif any(linux_dist in os_name for linux_dist in ['linux', 'ubuntu', 'centos', 'redhat']):
                return 'linux'  # lowercase to match database constraint
            elif 'macos' in os_name or 'mac os' in os_name:
                return 'macos'  # lowercase to match database constraint
            elif any(unix_type in os_name for unix_type in ['unix', 'solaris', 'aix', 'bsd']):
                return 'unix'  # lowercase to match database constraint
        
        return 'other'  # use 'other' instead of 'Unknown' to match database constraint
    
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
            with get_db_cursor() as cursor:
                cursor.execute("""
                    UPDATE discovery_jobs 
                    SET status = %s, started_at = CURRENT_TIMESTAMP 
                    WHERE id = %s
                """, (JobStatus.RUNNING, job_id))
            
            # Execute discovery based on type
            if job_config['discovery_type'] == "network_scan":
                await self.network_scan_discovery(job_id, job_config['config'])
            else:
                raise HTTPException(status_code=400, detail=f"Discovery type {job_config['discovery_type']} not implemented")
            
            # Update job status to completed with detailed results summary
            with get_db_cursor() as cursor:
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
                """, (JobStatus.COMPLETED, json.dumps(results_summary), job_id))
            
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
            with get_db_cursor() as cursor:
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
                """, (JobStatus.FAILED, json.dumps(results_summary), job_id))
            raise
    
    async def check_job_cancelled(self, job_id: int) -> bool:
        """Check if a job has been cancelled"""
        try:
            with get_db_cursor(commit=False) as cursor:
                cursor.execute("SELECT status FROM discovery_jobs WHERE id = %s", (job_id,))
                result = cursor.fetchone()
                if result and result[0] == JobStatus.CANCELLED:
                    return True
            return False
        except Exception as e:
            logger.error(f"Error checking job cancellation status: {e}")
            return False

    async def network_scan_discovery(self, job_id: int, config: Dict):
        """Execute network scan discovery"""
        scan_config = NetworkScanConfig(**config)
        
        # Check if job was cancelled before starting
        if await self.check_job_cancelled(job_id):
            logger.info(f"Discovery job {job_id} was cancelled before starting")
            return
        
        # Determine ports to scan
        if scan_config.services:
            # Use new services array - extract enabled services' ports
            enabled_ports = [str(service.port) for service in scan_config.services if service.enabled]
            ports = ",".join(enabled_ports) if enabled_ports else "22,3389,5985"  # fallback
        elif scan_config.ports:
            # Use explicit ports
            ports = scan_config.ports
        else:
            # Default fallback - common management ports
            ports = "22,3389,5985,5986"
        
        all_discovered_hosts = []
        failed_ranges = []
        successful_ranges = []
        
        # Parse and optimize network ranges
        all_targets = []
        for range_input in scan_config.cidr_ranges:
            try:
                parsed_targets = NetworkRangeParser.parse_network_ranges(range_input)
                all_targets.extend(parsed_targets)
                logger.info(f"Parsed range '{range_input}' into {len(parsed_targets)} targets")
            except Exception as e:
                logger.error(f"Failed to parse range '{range_input}': {e}")
                failed_ranges.append({"range": range_input, "error": str(e)})
        
        if not all_targets and not failed_ranges:
            raise Exception("No valid targets found in provided ranges")
        
        # Optimize targets for efficient nmap scanning
        optimized_targets = NetworkRangeParser.optimize_targets_for_nmap(all_targets)
        logger.info(f"Optimized {len(all_targets)} targets into {len(optimized_targets)} scan ranges")
        
        # Scan each optimized target/range
        for target_range in optimized_targets:
            # Check for cancellation before each range
            if await self.check_job_cancelled(job_id):
                logger.info(f"Discovery job {job_id} was cancelled during execution")
                return
                
            try:
                discovered_hosts = await self.scanner.scan_network_range(target_range, ports)
                all_discovered_hosts.extend(discovered_hosts)
                successful_ranges.append(target_range)
                logger.info(f"Successfully scanned {target_range}: found {len(discovered_hosts)} hosts")
            except Exception as e:
                logger.error(f"Failed to scan {target_range}: {e}")
                failed_ranges.append({"range": target_range, "error": str(e)})
        
        # Check if ALL scans failed
        if len(failed_ranges) > 0 and len(successful_ranges) == 0:
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
        try:
            with get_db_cursor() as cursor:
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
                            json.dumps(host.get('services', [])),
                            json.dumps(host.get('preferred_service')),
                            json.dumps(host.get('ports', {})),
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
                        json.dumps(host.get('services', [])),
                        json.dumps(host.get('preferred_service')),
                        json.dumps(host.get('ports', {})),
                        duplicate_status,
                        existing_target_id
                    ))
        except Exception as e:
            logger.error(f"Failed to store discovered targets: {e}")
            raise
    
    async def check_existing_discovered_target(self, ip_address: str, hostname: str = None) -> Optional[Dict]:
        """Check if target already exists in discovered_targets table"""
        try:
            with get_db_cursor(commit=False) as cursor:
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
                
            return existing
        except Exception as e:
            logger.error(f"Error checking existing discovered target: {e}")
            return None
    
    async def check_for_duplicates(self, ip_address: str, hostname: str = None) -> Tuple[str, Optional[int]]:
        """Check if target already exists by IP address or hostname"""
        try:
            with get_db_cursor(commit=False) as cursor:
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
    """Health check endpoint with database connectivity"""
    db_health = check_database_health()
    return {
        "status": "healthy" if db_health["status"] == "healthy" else "unhealthy",
        "service": "discovery-service",
        "database": db_health
    }

@app.get("/whoami")
def whoami(current_user: dict = Depends(verify_token_with_auth_service)):
    """Simple test endpoint to check authentication"""
    return {"user": current_user, "message": "Authentication working"}

@app.post("/test-simple")
async def test_simple():
    """Simple test endpoint without dependencies"""
    return {"message": "Simple endpoint working", "timestamp": datetime.now().isoformat()}



@app.post("/validate-network-ranges")
async def validate_network_ranges(ranges: Dict[str, List[str]]):
    """Validate network range inputs and return parsed targets"""
    try:
        results = []
        total_targets = 0
        
        for range_input in ranges.get("ranges", []):
            try:
                parsed_targets = NetworkRangeParser.parse_network_ranges(range_input)
                optimized_targets = NetworkRangeParser.optimize_targets_for_nmap(parsed_targets)
                
                results.append({
                    "input": range_input,
                    "valid": True,
                    "parsed_count": len(parsed_targets),
                    "optimized_ranges": optimized_targets,
                    "sample_targets": parsed_targets[:10] if len(parsed_targets) <= 10 else parsed_targets[:10] + [f"... and {len(parsed_targets) - 10} more"]
                })
                total_targets += len(parsed_targets)
                
            except Exception as e:
                results.append({
                    "input": range_input,
                    "valid": False,
                    "error": str(e)
                })
        
        return {
            "results": results,
            "total_targets": total_targets,
            "valid_ranges": len([r for r in results if r["valid"]]),
            "invalid_ranges": len([r for r in results if not r["valid"]])
        }
        
    except Exception as e:
        logger.error(f"Error validating network ranges: {e}")
        raise HTTPException(status_code=500, detail="Failed to validate network ranges")



# Discovery job endpoints
@app.post("/discovery-jobs", response_model=DiscoveryJobResponse)
async def create_discovery_job(
    job: DiscoveryJobCreate, 
    background_tasks: BackgroundTasks,
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """Create and start a discovery job"""
    try:
        # Manually verify token
        logger.info("About to verify token...")
        current_user = verify_token_manual(credentials)
        logger.info(f"Token verified. Creating discovery job with user: {type(current_user)} - {current_user}")
        
        # Extract user ID first to catch any issues early
        try:
            logger.info("About to extract user ID...")
            user_id = current_user['id']
            logger.info(f"Extracted user ID: {user_id}")
        except Exception as e:
            logger.error(f"Failed to extract user ID: {e}")
            logger.error(f"current_user type: {type(current_user)}")
            logger.error(f"current_user value: {current_user}")
            raise HTTPException(status_code=500, detail=f"Authentication error: {e}")
        
        with get_db_cursor() as cursor:
            cursor.execute("""
                INSERT INTO discovery_jobs (name, discovery_type, config, created_by, created_at)
                VALUES (%s, %s, %s, %s, CURRENT_TIMESTAMP)
                RETURNING id, name, discovery_type, config, status, created_by, created_at, started_at, completed_at, results_summary
            """, (job.name, job.discovery_type, json.dumps(job.config), user_id))
            new_job = cursor.fetchone()
        
        # Start discovery job in background
        background_tasks.add_task(
            discovery_service.start_discovery_job,
            new_job['id'],
            {'discovery_type': job.discovery_type, 'config': job.config},
            user_id
        )
        
        logger.info(f"Created discovery job: {new_job['id']}")
        return new_job
    except Exception as e:
        logger.error(f"Error creating discovery job: {e}")
        raise HTTPException(status_code=500, detail="Failed to create discovery job")

@app.get("/discovery-jobs", response_model=DiscoveryJobListResponse)
async def get_discovery_jobs(skip: int = 0, limit: int = 100, current_user: dict = Depends(verify_token_with_auth_service)):
    """Get all discovery jobs"""
    try:
        with get_db_cursor(commit=False) as cursor:
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
        
        return DiscoveryJobListResponse(jobs=jobs, total=total)
    except Exception as e:
        logger.error(f"Error fetching discovery jobs: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch discovery jobs")

# Frontend compatibility endpoint - alias for discovery jobs list
@app.get("/jobs", response_model=DiscoveryJobListResponse)
async def get_jobs_alias(skip: int = 0, limit: int = 100, current_user: dict = Depends(verify_token_with_auth_service)):
    """Get all discovery jobs (frontend compatibility endpoint)"""
    return await get_discovery_jobs(skip, limit, current_user)



@app.get("/discovery-jobs/{job_id}", response_model=DiscoveryJobResponse)
async def get_discovery_job(job_id: int, current_user: dict = Depends(verify_token_with_auth_service)):
    """Get discovery job by ID"""
    try:
        with get_db_cursor(commit=False) as cursor:
            cursor.execute("""
                SELECT id, name, discovery_type, config, status, created_by,
                       created_at, started_at, completed_at, results_summary
                FROM discovery_jobs 
                WHERE id = %s
            """, (job_id,))
            job = cursor.fetchone()
        
        if not job:
            raise HTTPException(status_code=404, detail="Discovery job not found")
        
        return job
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching discovery job {job_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch discovery job")

@app.get("/discovery-jobs/{job_id}/summary")
async def get_discovery_job_summary(job_id: int, current_user: dict = Depends(verify_token_with_auth_service)):
    """Get detailed discovery job results summary"""
    try:
        with get_db_cursor(commit=False) as cursor:
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
                    COUNT(CASE WHEN os_type = 'windows' THEN 1 END) as windows_count,
                    COUNT(CASE WHEN os_type = 'linux' THEN 1 END) as linux_count,
                    COUNT(CASE WHEN os_type IS NULL OR os_type = 'other' THEN 1 END) as unknown_count,
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
    current_user: dict = Depends(verify_token_with_auth_service)
):
    """Get discovered targets"""
    try:
        with get_db_cursor(commit=False) as cursor:
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
        
        return DiscoveredTargetListResponse(targets=targets, total=total)
    except Exception as e:
        logger.error(f"Error fetching discovered targets: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch discovered targets")

# Frontend compatibility endpoint - alias for discovered targets
@app.get("/targets", response_model=DiscoveredTargetListResponse)
async def get_targets_alias(
    skip: int = 0,
    limit: int = 100,
    job_id: Optional[int] = None,
    import_status: Optional[ImportStatus] = None,
    current_user: dict = Depends(verify_token_with_auth_service)
):
    """Get discovered targets (frontend compatibility endpoint)"""
    return await get_discovered_targets(skip, limit, job_id, import_status, current_user)

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
    current_user: dict = Depends(require_admin_or_operator_role)
):
    """Import discovered targets into the main targets system"""
    return await _import_discovered_targets_impl(import_request, current_user)

@app.post("/discovery/import-targets")
async def import_discovered_targets_alt(
    import_request: TargetImportRequest,
    current_user: dict = Depends(require_admin_or_operator_role)
):
    """Import discovered targets into the main targets system (alternative endpoint)"""
    return await _import_discovered_targets_impl(import_request, current_user)

@app.post("/import-targets")
async def import_discovered_targets_root(
    import_request: TargetImportRequest,
    current_user: dict = Depends(require_admin_or_operator_role)
):
    """Import discovered targets into the main targets system (root level endpoint)"""
    return await _import_discovered_targets_impl(import_request, current_user)

async def _import_discovered_targets_impl(
    import_request: TargetImportRequest,
    current_user: dict
):
    """Import discovered targets into the main targets system"""
    try:
        imported_count = 0
        failed_count = 0
        details = []
        
        with get_db_cursor() as cursor:
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
                    
                    # Insert new target (using current database schema)
                    cursor.execute("""
                        INSERT INTO targets (
                            name, hostname, ip_address, os_type, description, created_at
                        ) VALUES (%s, %s, %s, %s, %s, CURRENT_TIMESTAMP)
                        RETURNING id
                    """, (
                        target_name,
                        hostname,
                        ip_address,
                        os_type,
                        f"Imported from discovery - {discovered_target['os_type']} system"
                    ))
                    
                    new_target = cursor.fetchone()
                    target_id_new = new_target['id']
                    
                    # Add services to the target
                    if discovered_target['services']:
                        for service in discovered_target['services']:
                            try:
                                # Map service types to known service definitions
                                service_type_mapping = {
                                    'ssh': 'ssh',
                                    'winrm': 'winrm',
                                    'winrm_https': 'winrm_https', 
                                    'http': 'http',
                                    'https': 'https',
                                    'rdp': 'rdp',
                                    'ftp': 'ftp',
                                    'smb': 'smb'
                                }
                                
                                service_type = service_type_mapping.get(service['type'], service['type'])
                                
                                # Insert target service
                                cursor.execute("""
                                    INSERT INTO target_services (
                                        target_id, service_type, port, is_enabled, 
                                        discovery_method, created_at
                                    ) VALUES (%s, %s, %s, %s, %s, CURRENT_TIMESTAMP)
                                    ON CONFLICT (target_id, service_type) DO UPDATE SET
                                        port = EXCLUDED.port,
                                        is_enabled = EXCLUDED.is_enabled,
                                        discovery_method = EXCLUDED.discovery_method,
                                        updated_at = CURRENT_TIMESTAMP
                                """, (
                                    target_id_new,
                                    service_type,
                                    service['port'],
                                    True,
                                    'import'
                                ))
                            except Exception as service_error:
                                logger.warning(f"Failed to add service {service} to target {target_id_new}: {service_error}")
                    
                    # Add credential association if provided
                    if credential_id:
                        try:
                            cursor.execute("""
                                INSERT INTO target_credentials (
                                    target_id, credential_id, service_types, is_primary, created_at
                                ) VALUES (%s, %s, %s, %s, CURRENT_TIMESTAMP)
                                ON CONFLICT (target_id, credential_id) DO NOTHING
                            """, (
                                target_id_new,
                                credential_id,
                                [protocol] if protocol else ['ssh', 'winrm'],  # Default service types
                                True
                            ))
                        except Exception as cred_error:
                            logger.warning(f"Failed to add credential to target {target_id_new}: {cred_error}")
                    
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
    current_user: dict = Depends(require_admin_or_operator_role)
):
    """Mark discovered targets as ignored"""
    try:
        ignored_count = 0
        
        with get_db_cursor() as cursor:
            for target_id in ignore_request.target_ids:
                cursor.execute("""
                    DELETE FROM discovered_targets 
                    WHERE id = %s AND import_status = %s
                """, (target_id, ImportStatus.PENDING))
                
                if cursor.rowcount > 0:
                    ignored_count += 1
        
        logger.info(f"Ignored {ignored_count} targets")
        return {"ignored": ignored_count}
        
    except Exception as e:
        logger.error(f"Error ignoring targets: {e}")
        raise HTTPException(status_code=500, detail="Failed to ignore targets")

@app.delete("/discovery/targets/bulk")
async def bulk_delete_discovered_targets(
    delete_request: TargetIgnoreRequest,  # Reuse the same model since it just needs target_ids
    current_user: dict = Depends(require_admin_or_operator_role)
):
    """Bulk delete discovered targets"""
    try:
        deleted_count = 0
        
        with get_db_cursor() as cursor:
            for target_id in delete_request.target_ids:
                cursor.execute("""
                    DELETE FROM discovered_targets WHERE id = %s
                """, (target_id,))
                
                if cursor.rowcount > 0:
                    deleted_count += 1
        
        logger.info(f"Bulk deleted {deleted_count} targets")
        return {"deleted": deleted_count}
        
    except Exception as e:
        logger.error(f"Error bulk deleting targets: {e}")
        raise HTTPException(status_code=500, detail="Failed to bulk delete targets")

@app.post("/discovery-jobs/{job_id}/run")
async def run_discovery_job(
    job_id: int, 
    background_tasks: BackgroundTasks,
    current_user: dict = Depends(verify_token_with_auth_service)
):
    """Run/start a discovery job"""
    try:
        with get_db_cursor() as cursor:
            cursor.execute("""
                SELECT id, name, discovery_type, config, status, created_by
                FROM discovery_jobs WHERE id = %s
            """, (job_id,))
            job = cursor.fetchone()
            
            if not job:
                raise HTTPException(status_code=404, detail="Discovery job not found")
            
            if job['status'] not in [JobStatus.PENDING, JobStatus.FAILED]:
                raise HTTPException(
                    status_code=400,
                    detail=f"Cannot run job with status '{job['status']}'. Only pending or failed jobs can be run."
                )
            
            # Reset job status to pending and clear previous results
            cursor.execute("""
                UPDATE discovery_jobs 
                SET status = %s, started_at = NULL, completed_at = NULL, results_summary = NULL
                WHERE id = %s
            """, (JobStatus.PENDING, job_id))
        
        # Start discovery job in background
        background_tasks.add_task(
            discovery_service.start_discovery_job,
            job_id,
            {'discovery_type': job['discovery_type'], 'config': job['config']},
            job['created_by']
        )
        
        logger.info(f"Started discovery job {job_id}")
        return {"message": f"Discovery job {job_id} has been started"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error starting discovery job {job_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to start discovery job")

@app.post("/discovery-jobs/{job_id}/cancel")
async def cancel_discovery_job_new(job_id: int, current_user: dict = Depends(verify_token_with_auth_service)):
    """Cancel a running discovery job"""
    try:
        with get_db_cursor() as cursor:
            cursor.execute("SELECT id, status FROM discovery_jobs WHERE id = %s", (job_id,))
            job = cursor.fetchone()
            
            if not job:
                raise HTTPException(status_code=404, detail="Discovery job not found")
            
            if job['status'] != JobStatus.RUNNING:
                raise HTTPException(
                    status_code=400, 
                    detail=f"Cannot cancel job with status '{job['status']}'. Only running jobs can be cancelled."
                )
            
            cursor.execute("""
                UPDATE discovery_jobs 
                SET status = %s, completed_at = CURRENT_TIMESTAMP 
                WHERE id = %s
            """, (JobStatus.CANCELLED, job_id))
        
        logger.info(f"Cancelled discovery job {job_id}")
        return {"message": "Discovery job cancelled successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error cancelling discovery job {job_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to cancel discovery job")

@app.delete("/discovery-jobs/{job_id}")
async def delete_discovery_job(job_id: int, current_user: dict = Depends(require_admin_or_operator_role)):
    """Delete a discovery job and its associated targets"""
    try:
        with get_db_cursor() as cursor:
            # First check if job exists and get current status
            cursor.execute("SELECT id, status FROM discovery_jobs WHERE id = %s", (job_id,))
            job = cursor.fetchone()
            
            if not job:
                raise HTTPException(status_code=404, detail="Discovery job not found")
            
            # If job is running, cancel it first
            if job['status'] == JobStatus.RUNNING:
                logger.info(f"Cancelling running discovery job {job_id} before deletion")
                cursor.execute("""
                    UPDATE discovery_jobs 
                    SET status = %s, completed_at = CURRENT_TIMESTAMP 
                    WHERE id = %s
                """, (JobStatus.CANCELLED, job_id))
                
                # Give a moment for any running processes to notice the cancellation
                await asyncio.sleep(1)
            
            # Delete associated discovered targets first
            cursor.execute("DELETE FROM discovered_targets WHERE discovery_job_id = %s", (job_id,))
            targets_deleted = cursor.rowcount
            
            # Delete the job
            cursor.execute("DELETE FROM discovery_jobs WHERE id = %s", (job_id,))
        
        logger.info(f"Deleted discovery job {job_id} (cancelled if running, deleted {targets_deleted} associated targets)")
        return {
            "message": "Discovery job deleted successfully",
            "targets_deleted": targets_deleted,
            "was_running": job['status'] == JobStatus.RUNNING
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting discovery job {job_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to delete discovery job")



@app.put("/discovery-jobs/{job_id}", response_model=DiscoveryJobResponse)
async def update_discovery_job(
    job_id: int, 
    job_update: DiscoveryJobUpdate, 
    current_user: dict = Depends(require_admin_or_operator_role)
):
    """Update a discovery job (only if not running/completed)"""
    try:
        with get_db_cursor() as cursor:
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
                update_values.append(json.dumps(job_update.config))
            
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
        
        logger.info(f"Updated discovery job {job_id}")
        return updated_job
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating discovery job {job_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to update discovery job")

@app.get("/discovery/targets/{target_id}", response_model=DiscoveredTargetResponse)
async def get_discovered_target(target_id: int, current_user: dict = Depends(verify_token_with_auth_service)):
    """Get a specific discovered target by ID"""
    try:
        with get_db_cursor(commit=False) as cursor:
            cursor.execute("""
                SELECT id, discovery_job_id, hostname, ip_address, os_type, os_version,
                       services, preferred_service, connection_test_results, system_info,
                       duplicate_status, existing_target_id, import_status, discovered_at
                FROM discovered_targets 
                WHERE id = %s
            """, (target_id,))
            target = cursor.fetchone()
        
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
    current_user: dict = Depends(require_admin_or_operator_role)
):
    """Update a discovered target"""
    try:
        with get_db_cursor() as cursor:
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
        
        logger.info(f"Updated discovered target {target_id}")
        return updated_target
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating discovered target {target_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to update discovered target")

@app.delete("/discovery/targets/{target_id}")
async def delete_discovered_target(target_id: int, current_user: dict = Depends(require_admin_or_operator_role)):
    """Delete a discovered target"""
    try:
        with get_db_cursor() as cursor:
            cursor.execute("DELETE FROM discovered_targets WHERE id = %s", (target_id,))
            
            if cursor.rowcount == 0:
                raise HTTPException(status_code=404, detail="Discovered target not found")
        
        logger.info(f"Deleted discovered target {target_id}")
        return {"message": "Discovered target deleted successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting discovered target {target_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to delete discovered target")

# Additional frontend compatibility endpoints - aliases for discovery jobs
@app.post("/jobs", response_model=DiscoveryJobResponse)
async def create_job_alias(
    job_data: DiscoveryJobCreate, 
    background_tasks: BackgroundTasks,
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """Create discovery job (frontend compatibility endpoint)"""
    try:
        # Manually verify token
        logger.info("About to verify token...")
        current_user = verify_token_manual(credentials)
        logger.info(f"Token verified. Creating discovery job with user: {type(current_user)} - {current_user}")
        
        # Extract user ID first to catch any issues early
        try:
            logger.info("About to extract user ID...")
            user_id = current_user['id']
            logger.info(f"Extracted user ID: {user_id}")
        except Exception as e:
            logger.error(f"Failed to extract user ID: {e}")
            logger.error(f"current_user type: {type(current_user)}")
            logger.error(f"current_user value: {current_user}")
            raise HTTPException(status_code=500, detail=f"Authentication error: {e}")
        
        with get_db_cursor() as cursor:
            cursor.execute("""
                INSERT INTO discovery_jobs (name, discovery_type, config, created_by, created_at)
                VALUES (%s, %s, %s, %s, CURRENT_TIMESTAMP)
                RETURNING id, name, discovery_type, config, status, created_by, created_at, started_at, completed_at, results_summary
            """, (job_data.name, job_data.discovery_type, json.dumps(job_data.config), user_id))
            new_job = cursor.fetchone()
        
        # Start discovery job in background
        background_tasks.add_task(
            discovery_service.start_discovery_job,
            new_job['id'],
            {'discovery_type': job_data.discovery_type, 'config': job_data.config},
            user_id
        )
        
        logger.info(f"Created discovery job: {new_job['id']}")
        return new_job
    except Exception as e:
        logger.error(f"Error creating discovery job: {e}")
        raise HTTPException(status_code=500, detail="Failed to create discovery job")

@app.get("/jobs/{job_id}", response_model=DiscoveryJobResponse)
async def get_job_alias(job_id: int, current_user: dict = Depends(verify_token_with_auth_service)):
    """Get discovery job by ID (frontend compatibility endpoint)"""
    return await get_discovery_job(job_id, current_user)

@app.put("/jobs/{job_id}", response_model=DiscoveryJobResponse)
async def update_job_alias(job_id: int, job_data: DiscoveryJobUpdate, current_user: dict = Depends(verify_token_with_auth_service)):
    """Update discovery job (frontend compatibility endpoint)"""
    return await update_discovery_job(job_id, job_data, current_user)

@app.delete("/jobs/{job_id}")
async def delete_job_alias(job_id: int, current_user: dict = Depends(verify_token_with_auth_service)):
    """Delete discovery job (frontend compatibility endpoint)"""
    return await delete_discovery_job(job_id, current_user)

@app.post("/jobs/{job_id}/cancel")
async def cancel_job_alias(job_id: int, current_user: dict = Depends(verify_token_with_auth_service)):
    """Cancel discovery job (frontend compatibility endpoint)"""
    return await cancel_discovery_job_new(job_id, current_user)

@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint"""
    db_health = check_database_health()
    
    checks = [
        HealthCheck(
            name="database",
            status=db_health["status"],
            message=db_health.get("message", "Database connection check"),
            duration_ms=db_health.get("response_time_ms")
        )
    ]
    
    overall_status = "healthy" if db_health["status"] == "healthy" else "unhealthy"
    
    return HealthResponse(
        service="discovery-service",
        status=overall_status,
        version="1.0.0",
        checks=checks
    )

@app.on_event("startup")
async def startup_event():
    """Log service startup"""
    log_startup("discovery-service", "1.0.0", 3010)

@app.on_event("shutdown")
async def shutdown_event():
    """Clean up database connections on shutdown"""
    log_shutdown("discovery-service")
    cleanup_database_pool()

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", "3010"))
    uvicorn.run(app, host="0.0.0.0", port=port)