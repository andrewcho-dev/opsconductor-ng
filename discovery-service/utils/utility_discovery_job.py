#!/usr/bin/env python3
"""
Discovery Job Utility Module
Handles discovery job execution and management
"""

import asyncio
from typing import List, Dict, Any, Optional
from .logging import get_logger
from .database import get_db_cursor

logger = get_logger("discovery-service.discovery-job")


class DiscoveryJobUtility:
    """Utility class for discovery job operations"""
    
    def __init__(self, scanner_utility, network_range_parser):
        self.scanner_utility = scanner_utility
        self.network_range_parser = network_range_parser
    
    async def execute_network_scan_discovery(self, job_id: int, config: Dict, scan_config_class) -> Dict[str, Any]:
        """Execute network scan discovery"""
        scan_config = scan_config_class(**config)
        
        # Check if job was cancelled before starting
        if await self.check_job_cancelled(job_id):
            logger.info(f"Discovery job {job_id} was cancelled before starting")
            return {"status": "cancelled"}
        
        # Determine ports to scan
        ports = self._determine_scan_ports(scan_config)
        
        all_discovered_hosts = []
        failed_ranges = []
        successful_ranges = []
        
        # Parse and optimize network ranges
        all_targets = []
        for range_input in scan_config.cidr_ranges:
            try:
                parsed_targets = self.network_range_parser.parse_network_ranges(range_input)
                all_targets.extend(parsed_targets)
                logger.info(f"Parsed range '{range_input}' into {len(parsed_targets)} targets")
            except Exception as e:
                logger.error(f"Failed to parse range '{range_input}': {e}")
                failed_ranges.append({"range": range_input, "error": str(e)})
        
        if not all_targets and not failed_ranges:
            raise Exception("No valid targets found in provided ranges")
        
        # Optimize targets for efficient nmap scanning
        optimized_targets = self.network_range_parser.optimize_targets_for_nmap(all_targets)
        logger.info(f"Optimized {len(all_targets)} targets into {len(optimized_targets)} scan ranges")
        
        # Scan each optimized target/range
        for target_range in optimized_targets:
            # Check for cancellation before each range
            if await self.check_job_cancelled(job_id):
                logger.info(f"Discovery job {job_id} was cancelled during execution")
                return {"status": "cancelled"}
                
            try:
                discovered_hosts = await self.scanner_utility.scan_network_range(target_range, ports)
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
        
        return {
            "status": "completed",
            "discovered_hosts": len(all_discovered_hosts),
            "successful_ranges": len(successful_ranges),
            "failed_ranges": len(failed_ranges)
        }
    
    def _determine_scan_ports(self, scan_config) -> str:
        """Determine which ports to scan based on configuration"""
        if scan_config.services:
            # Use new services array - extract enabled services' ports
            enabled_ports = [str(service.port) for service in scan_config.services if service.enabled]
            return ",".join(enabled_ports) if enabled_ports else "22,3389,5985"  # fallback
        elif scan_config.ports:
            # Use explicit ports
            return scan_config.ports
        else:
            # Default fallback - common management ports
            return "22,3389,5985,5986"
    
    async def check_job_cancelled(self, job_id: int) -> bool:
        """Check if a job has been cancelled"""
        try:
            with get_db_cursor(commit=False) as cursor:
                cursor.execute("SELECT status FROM discovery_jobs WHERE id = %s", (job_id,))
                result = cursor.fetchone()
                if result and result[0] == "cancelled":  # Assuming JobStatus.CANCELLED maps to "cancelled"
                    return True
            return False
        except Exception as e:
            logger.error(f"Error checking job cancellation status: {e}")
            return False
    
    async def store_discovered_targets(self, job_id: int, discovered_hosts: List[Dict]) -> Dict[str, Any]:
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
                                last_discovered = CURRENT_TIMESTAMP,
                                discovery_job_id = %s
                            WHERE id = %s
                        """, (
                            hostname,
                            host.get('os_type'),
                            host.get('os_version'),
                            host.get('services', []),
                            host.get('preferred_service'),
                            job_id,
                            existing_discovered['id']
                        ))
                    else:
                        # Insert new discovered target
                        logger.info(f"Inserting new discovered target {ip_address}")
                        cursor.execute("""
                            INSERT INTO discovered_targets (
                                ip_address, hostname, os_type, os_version, 
                                services, preferred_service, discovery_job_id,
                                first_discovered, last_discovered
                            ) VALUES (%s, %s, %s, %s, %s, %s, %s, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
                        """, (
                            ip_address,
                            hostname,
                            host.get('os_type'),
                            host.get('os_version'),
                            host.get('services', []),
                            host.get('preferred_service'),
                            job_id
                        ))
                        
        except Exception as e:
            logger.error(f"Error storing discovered targets: {e}")
            raise
    
    async def check_existing_discovered_target(self, ip_address: str, hostname: str = None) -> Optional[Dict]:
        """Check if target already exists in discovered_targets table"""
        try:
            with get_db_cursor(commit=False) as cursor:
                if hostname:
                    cursor.execute("""
                        SELECT id, ip_address, hostname, os_type, os_version, services, preferred_service
                        FROM discovered_targets 
                        WHERE ip_address = %s OR hostname = %s
                        ORDER BY last_discovered DESC
                        LIMIT 1
                    """, (ip_address, hostname))
                else:
                    cursor.execute("""
                        SELECT id, ip_address, hostname, os_type, os_version, services, preferred_service
                        FROM discovered_targets 
                        WHERE ip_address = %s
                        ORDER BY last_discovered DESC
                        LIMIT 1
                    """, (ip_address,))
                
                result = cursor.fetchone()
                return dict(result) if result else None
                
        except Exception as e:
            logger.error(f"Error checking existing discovered target: {e}")
            return None