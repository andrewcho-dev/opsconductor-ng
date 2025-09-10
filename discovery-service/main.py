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

from fastapi import FastAPI, HTTPException, Depends, status, BackgroundTasks, Header, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel, Field
import jwt
import nmap

# Import shared modules
from shared.database import get_db_cursor, check_database_health, cleanup_database_pool
from shared.logging import setup_service_logging, get_logger, log_startup, log_shutdown
from shared.middleware import add_standard_middleware
from shared.models import HealthResponse, HealthCheck, create_success_response
from shared.errors import DatabaseError, ValidationError, NotFoundError, PermissionError, AuthError, handle_database_error
from shared.auth import require_admin_role
from shared.utils import get_service_client

# Import utility modules
from utils.utility_network_scanner import NetworkScannerUtility
from utils.utility_discovery_job import DiscoveryJobUtility
from utils.utility_network_range_parser import NetworkRangeParserUtility

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

# Security
security = HTTPBearer()

JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", "your-secret-key")

# Helper functions for header-based authentication
def get_user_from_headers(request: Request):
    """Extract user info from nginx headers (set by gateway authentication)"""
    return {
        "id": request.headers.get("X-User-ID"),
        "username": request.headers.get("X-Username"),
        "email": request.headers.get("X-User-Email"),
        "role": request.headers.get("X-User-Role")
    }

# Auth is now handled at nginx gateway level - no internal auth checks needed

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



# Network range parsing is now handled by utility module

# Database connection is now handled by shared.database module

# Authentication is now handled by shared.auth module

# Network scanning is now handled by utility module

# Discovery Service Class
class DiscoveryService:
    def __init__(self):
        self.active_jobs = {}
        # Initialize utility modules
        self.network_scanner_utility = NetworkScannerUtility()
        self.network_range_parser = NetworkRangeParserUtility()
        self.discovery_job_utility = DiscoveryJobUtility(
            self.network_scanner_utility, 
            self.network_range_parser
        )
    
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
                raise ValidationError(f"Discovery type {job_config['discovery_type']} not implemented", "discovery_type")
            
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

    async def network_scan_discovery(self, job_id: int, config: Dict) -> Dict[str, Any]:
        """Execute network scan discovery using utility module"""
        return await self.discovery_job_utility.execute_network_scan_discovery(
            job_id, config, NetworkScanConfig
        )
    
    async def store_discovered_targets(self, job_id: int, discovered_hosts: List[Dict]) -> Dict[str, Any]:
        """Store discovered targets using utility module"""
        return await self.discovery_job_utility.store_discovered_targets(job_id, discovered_hosts)
    
    async def check_existing_discovered_target(self, ip_address: str, hostname: str = None) -> Optional[Dict]:
        """Check if target already exists using utility module"""
        return await self.discovery_job_utility.check_existing_discovered_target(ip_address, hostname)
    
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
async def health_check() -> HealthResponse:
    """Health check endpoint with database connectivity"""
    db_health = check_database_health()
    return {
        "status": "healthy" if db_health["status"] == "healthy" else "unhealthy",
        "service": "discovery-service",
        "database": db_health
    }

@app.get("/metrics/database")
async def database_metrics() -> Dict[str, Any]:
    """Database connection pool metrics endpoint"""
    metrics = get_database_metrics()
    return {
        "service": "discovery-service",
        "timestamp": datetime.utcnow().isoformat(),
        "database": metrics
    }

@app.get("/whoami")
def whoami(request: Request):
    """Simple test endpoint to check authentication"""
    current_user = get_user_from_headers(request)
    return create_success_response(
        data={"user": current_user},
        message="Authentication working"
    )

@app.post("/test-simple")
async def test_simple() -> Dict[str, Any]:
    """Simple test endpoint without dependencies"""
    return create_success_response(
        message="Simple endpoint working",
        data={"timestamp": datetime.now().isoformat()}
    )



@app.post("/validate-network-ranges")
async def validate_network_ranges(ranges: Dict[str, List[str]]) -> Dict[str, Any]:
    """Validate network range inputs and return parsed targets"""
    try:
        results = []
        total_targets = 0
        
        for range_input in ranges.get("ranges", []):
            try:
                parsed_targets = NetworkRangeParserUtility.parse_network_ranges(range_input)
                optimized_targets = NetworkRangeParserUtility.optimize_targets_for_nmap(parsed_targets)
                
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
        raise handle_database_error(e, "validate network ranges")



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
            raise AuthError(f"Authentication error: {e}")
        
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
        raise handle_database_error(e, "create discovery job")

@app.get("/discovery-jobs", response_model=DiscoveryJobListResponse)
async def get_discovery_jobs(request: Request, skip: int = 0, limit: int = 100):
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
        raise handle_database_error(e, "fetch discovery jobs")

# Frontend compatibility endpoint - alias for discovery jobs list
@app.get("/jobs", response_model=DiscoveryJobListResponse)
async def get_jobs_alias(request: Request, skip: int = 0, limit: int = 100):
    """Get all discovery jobs (frontend compatibility endpoint)"""
    return await get_discovery_jobs(request, skip, limit)



@app.get("/discovery-jobs/{job_id}", response_model=DiscoveryJobResponse)
async def get_discovery_job(job_id: int, request: Request):
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
            raise NotFoundError("Discovery job", job_id)
        
        return job
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching discovery job {job_id}: {e}")
        raise DatabaseError("Failed to fetch discovery job")

@app.get("/discovery-jobs/{job_id}/summary")
async def get_discovery_job_summary(job_id: int, request: Request):
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
                raise NotFoundError("Discovery job not found")
            
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
        raise DatabaseError("Failed to fetch discovery job summary")

@app.get("/discovery/targets", response_model=DiscoveredTargetListResponse)
async def get_discovered_targets(
    request: Request,
    skip: int = 0,
    limit: int = 100,
    job_id: Optional[int] = None,
    import_status: Optional[ImportStatus] = None
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
        raise DatabaseError("Failed to fetch discovered targets")

# Frontend compatibility endpoint - alias for discovered targets
@app.get("/targets", response_model=DiscoveredTargetListResponse)
async def get_targets_alias(
    request: Request,
    skip: int = 0,
    limit: int = 100,
    job_id: Optional[int] = None,
    import_status: Optional[ImportStatus] = None
):
    """Get discovered targets (frontend compatibility endpoint)"""
    return await get_discovered_targets(request, skip, limit, job_id, import_status)

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
    request: Request
):
    """Import discovered targets into the main targets system"""
    # Auth handled at nginx gateway level
    return await _import_discovered_targets_impl(import_request, None)

@app.post("/discovery/import-targets")
async def import_discovered_targets_alt(
    import_request: TargetImportRequest,
    request: Request
):
    """Import discovered targets into the main targets system (alternative endpoint)"""
    # Check admin/operator role
    # Auth handled at nginx gateway level
    return await _import_discovered_targets_impl(import_request, None)

@app.post("/import-targets")
async def import_discovered_targets_root(
    import_request: TargetImportRequest,
    request: Request
):
    """Import discovered targets into the main targets system (root level endpoint)"""
    # Check admin/operator role
    # Auth handled at nginx gateway level
    return await _import_discovered_targets_impl(import_request, None)

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
        raise DatabaseError("Failed to import targets")

@app.post("/discovery/targets/ignore")
async def ignore_discovered_targets(
    ignore_request: TargetIgnoreRequest,
    request: Request
):
    """Mark discovered targets as ignored"""
    # Check admin/operator role
    # Auth handled at nginx gateway level
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
        raise DatabaseError("Failed to ignore targets")

@app.delete("/discovery/targets/bulk")
async def bulk_delete_discovered_targets(
    delete_request: TargetIgnoreRequest,  # Reuse the same model since it just needs target_ids
    request: Request
):
    """Bulk delete discovered targets"""
    # Check admin/operator role
    # Auth handled at nginx gateway level
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
        raise DatabaseError("Failed to bulk delete targets")

@app.post("/discovery-jobs/{job_id}/run")
async def run_discovery_job(
    job_id: int, 
    background_tasks: BackgroundTasks,
    request: Request
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
                raise NotFoundError("Discovery job not found")
            
            if job['status'] not in [JobStatus.PENDING, JobStatus.FAILED]:
                raise ValidationError(f"Cannot run job with status '{job['status']}'. Only pending or failed jobs can be run.", "status")
            
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
        return create_success_response(
            message=f"Discovery job {job_id} has been started",
            data={"job_id": job_id}
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error starting discovery job {job_id}: {e}")
        raise DatabaseError("Failed to start discovery job")

@app.post("/discovery-jobs/{job_id}/cancel")
async def cancel_discovery_job_new(job_id: int, request: Request):
    """Cancel a running discovery job"""
    try:
        with get_db_cursor() as cursor:
            cursor.execute("SELECT id, status FROM discovery_jobs WHERE id = %s", (job_id,))
            job = cursor.fetchone()
            
            if not job:
                raise NotFoundError("Discovery job not found")
            
            if job['status'] != JobStatus.RUNNING:
                raise ValidationError(f"Cannot cancel job with status '{job['status']}'. Only running jobs can be cancelled.", "status")
            
            cursor.execute("""
                UPDATE discovery_jobs 
                SET status = %s, completed_at = CURRENT_TIMESTAMP 
                WHERE id = %s
            """, (JobStatus.CANCELLED, job_id))
        
        logger.info(f"Cancelled discovery job {job_id}")
        return create_success_response(
            message="Discovery job cancelled successfully",
            data={"job_id": job_id}
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error cancelling discovery job {job_id}: {e}")
        raise DatabaseError("Failed to cancel discovery job")

@app.delete("/discovery-jobs/{job_id}")
async def delete_discovery_job(job_id: int, request: Request):
    """Delete a discovery job and its associated targets"""
    # Check admin/operator role
    # Auth handled at nginx gateway level
    try:
        with get_db_cursor() as cursor:
            # First check if job exists and get current status
            cursor.execute("SELECT id, status FROM discovery_jobs WHERE id = %s", (job_id,))
            job = cursor.fetchone()
            
            if not job:
                raise NotFoundError("Discovery job not found")
            
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
        raise DatabaseError("Failed to delete discovery job")



@app.put("/discovery-jobs/{job_id}", response_model=DiscoveryJobResponse)
async def update_discovery_job(
    job_id: int, 
    job_update: DiscoveryJobUpdate, 
    request: Request
):
    """Update a discovery job (only if not running/completed)"""
    # Check admin/operator role
    # Auth handled at nginx gateway level
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
                raise NotFoundError("Discovery job not found")
            
            # Only allow updates if job is pending or failed
            if current_job['status'] not in [JobStatus.PENDING, JobStatus.FAILED]:
                raise ValidationError(f"Cannot update job with status '{current_job['status']}'. Only pending or failed jobs can be updated.", "status")
            
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
        raise DatabaseError("Failed to update discovery job")

@app.get("/discovery/targets/{target_id}", response_model=DiscoveredTargetResponse)
async def get_discovered_target(target_id: int, request: Request):
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
            raise NotFoundError("Discovered target", target_id)
        
        return target
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching discovered target {target_id}: {e}")
        raise DatabaseError("Failed to fetch discovered target")

@app.put("/discovery/targets/{target_id}", response_model=DiscoveredTargetResponse)
async def update_discovered_target(
    target_id: int, 
    target_update: DiscoveredTargetUpdate, 
    request: Request
):
    """Update a discovered target"""
    # Check admin/operator role
    # Auth handled at nginx gateway level
    try:
        with get_db_cursor() as cursor:
            # First check if target exists
            cursor.execute("""
                SELECT id FROM discovered_targets WHERE id = %s
            """, (target_id,))
            
            if not cursor.fetchone():
                raise NotFoundError("Discovered target", target_id)
            
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
        raise DatabaseError("Failed to update discovered target")

@app.delete("/discovery/targets/{target_id}")
async def delete_discovered_target(target_id: int, request: Request):
    """Delete a discovered target"""
    # Check admin/operator role
    # Auth handled at nginx gateway level
    try:
        with get_db_cursor() as cursor:
            cursor.execute("DELETE FROM discovered_targets WHERE id = %s", (target_id,))
            
            if cursor.rowcount == 0:
                raise NotFoundError("Discovered target", target_id)
        
        logger.info(f"Deleted discovered target {target_id}")
        return create_success_response(
            message="Discovered target deleted successfully",
            data={"target_id": target_id}
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting discovered target {target_id}: {e}")
        raise DatabaseError("Failed to delete discovered target")

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
            raise AuthError(f"Authentication error: {e}")
        
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
        raise handle_database_error(e, "create discovery job")

@app.get("/jobs/{job_id}", response_model=DiscoveryJobResponse)
async def get_job_alias(job_id: int, request: Request):
    """Get discovery job by ID (frontend compatibility endpoint)"""
    return await get_discovery_job(job_id, request)

@app.put("/jobs/{job_id}", response_model=DiscoveryJobResponse)
async def update_job_alias(job_id: int, job_data: DiscoveryJobUpdate, request: Request):
    """Update discovery job (frontend compatibility endpoint)"""
    return await update_discovery_job(job_id, job_data, request)

@app.delete("/jobs/{job_id}")
async def delete_job_alias(job_id: int, request: Request):
    """Delete discovery job (frontend compatibility endpoint)"""
    return await delete_discovery_job(job_id, request)

@app.post("/jobs/{job_id}/cancel")
async def cancel_job_alias(job_id: int, request: Request):
    """Cancel discovery job (frontend compatibility endpoint)"""
    return await cancel_discovery_job_new(job_id, request)

@app.get("/health", response_model=HealthResponse)
async def health_check() -> HealthResponse:
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
async def startup_event() -> None:
    """Log service startup"""
    log_startup("discovery-service", "1.0.0", 3010)

@app.on_event("shutdown")
async def shutdown_event() -> None:
    """Clean up database connections on shutdown"""
    log_shutdown("discovery-service")
    cleanup_database_pool()

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", "3010"))
    uvicorn.run(app, host="0.0.0.0", port=port)