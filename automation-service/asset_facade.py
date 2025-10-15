#!/usr/bin/env python3
"""
Asset Façade - Public API for asset queries and connection profiles
Provides fast, read-only access to asset information for tool execution
"""

import logging
import os
from typing import Optional, List, Dict, Any
import psycopg2
from psycopg2.extras import RealDictCursor
import httpx

logger = logging.getLogger(__name__)


class AssetFacade:
    """
    Façade for asset queries and connection profile resolution
    Backed by asset-service or direct database access
    """
    
    def __init__(self, database_url: str, asset_service_base: Optional[str] = None):
        """
        Initialize asset façade
        
        Args:
            database_url: PostgreSQL connection string
            asset_service_base: Optional asset-service URL (e.g., http://asset-service:8000)
        """
        self.database_url = database_url
        self.asset_service_base = asset_service_base
        self.use_service = asset_service_base is not None
        
        logger.info(f"AssetFacade initialized (mode: {'service' if self.use_service else 'direct-db'})")
    
    def _get_connection(self):
        """Get database connection"""
        return psycopg2.connect(self.database_url, cursor_factory=RealDictCursor)
    
    def _normalize_host(self, host: str) -> str:
        """Normalize host for case-insensitive matching"""
        return host.lower().strip()
    
    def _normalize_os(self, os_type: str) -> str:
        """Normalize OS type for matching"""
        os_lower = os_type.lower().strip()
        
        # Map common variations
        if 'win' in os_lower:
            return 'windows'
        elif 'lin' in os_lower:
            return 'linux'
        elif 'mac' in os_lower or 'darwin' in os_lower:
            return 'macos'
        elif 'unix' in os_lower:
            return 'unix'
        else:
            return os_lower
    
    async def count_assets(
        self,
        os: Optional[str] = None,
        hostname: Optional[str] = None,
        ip: Optional[str] = None,
        status: Optional[str] = None,
        environment: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Count assets matching filters
        
        Args:
            os: OS type filter (e.g., "Windows 10", "windows", "linux")
            hostname: Hostname filter (partial match)
            ip: IP address filter (exact match)
            status: Status filter (e.g., "active")
            environment: Environment filter (e.g., "production")
            
        Returns:
            Dict with count and filters applied
        """
        conn = None
        try:
            conn = self._get_connection()
            cur = conn.cursor()
            
            # Build query
            query = "SELECT COUNT(*) as count FROM assets.assets WHERE 1=1"
            params = []
            
            if os:
                # Match both os_type and os_version for flexibility
                normalized_os = self._normalize_os(os)
                query += " AND (LOWER(os_type) LIKE %s OR LOWER(os_version) LIKE %s)"
                params.extend([f"%{normalized_os}%", f"%{os.lower()}%"])
            
            if hostname:
                query += " AND LOWER(hostname) LIKE %s"
                params.append(f"%{hostname.lower()}%")
            
            if ip:
                query += " AND ip_address = %s"
                params.append(ip)
            
            if status:
                query += " AND LOWER(status) = %s"
                params.append(status.lower())
            
            if environment:
                query += " AND LOWER(environment) = %s"
                params.append(environment.lower())
            
            cur.execute(query, params)
            result = cur.fetchone()
            
            count = result['count'] if result else 0
            
            logger.info(f"Asset count query: {count} assets (filters: os={os}, hostname={hostname}, ip={ip})")
            
            return {
                "count": count,
                "filters": {
                    "os": os,
                    "hostname": hostname,
                    "ip": ip,
                    "status": status,
                    "environment": environment
                }
            }
            
        except Exception as e:
            logger.error(f"Failed to count assets: {e}")
            raise
        finally:
            if conn:
                conn.close()
    
    async def search_assets(
        self,
        os: Optional[str] = None,
        hostname: Optional[str] = None,
        ip: Optional[str] = None,
        status: Optional[str] = None,
        environment: Optional[str] = None,
        limit: int = 50
    ) -> Dict[str, Any]:
        """
        Search assets matching filters
        
        Args:
            os: OS type filter
            hostname: Hostname filter (partial match)
            ip: IP address filter (exact match)
            status: Status filter
            environment: Environment filter
            limit: Maximum number of results (default 50)
            
        Returns:
            Dict with items array and count
        """
        conn = None
        try:
            conn = self._get_connection()
            cur = conn.cursor()
            
            # Build query
            query = """
                SELECT id, name, hostname, ip_address, os_type, os_version, 
                       service_type, port, is_secure, status, environment,
                       created_at, updated_at
                FROM assets.assets 
                WHERE 1=1
            """
            params = []
            
            if os:
                normalized_os = self._normalize_os(os)
                query += " AND (LOWER(os_type) LIKE %s OR LOWER(os_version) LIKE %s)"
                params.extend([f"%{normalized_os}%", f"%{os.lower()}%"])
            
            if hostname:
                query += " AND LOWER(hostname) LIKE %s"
                params.append(f"%{hostname.lower()}%")
            
            if ip:
                query += " AND ip_address = %s"
                params.append(ip)
            
            if status:
                query += " AND LOWER(status) = %s"
                params.append(status.lower())
            
            if environment:
                query += " AND LOWER(environment) = %s"
                params.append(environment.lower())
            
            query += " ORDER BY hostname LIMIT %s"
            params.append(limit)
            
            cur.execute(query, params)
            results = cur.fetchall()
            
            items = [dict(row) for row in results]
            
            logger.info(f"Asset search: {len(items)} assets found (limit={limit})")
            
            return {
                "items": items,
                "count": len(items),
                "limit": limit
            }
            
        except Exception as e:
            logger.error(f"Failed to search assets: {e}")
            raise
        finally:
            if conn:
                conn.close()
    
    async def get_connection_profile(self, host: str, asset_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Get connection profile for a host
        Resolves host by IP, FQDN, or short hostname and returns connection parameters
        with credential references (not plaintext secrets)
        
        Args:
            host: Hostname, IP address, or short hostname
            asset_id: Optional asset UUID for disambiguation
            
        Returns:
            Dict with connection profile or {"found": False} if not found
            Returns {"error": "ambiguous_asset", "candidates": [...]} if multiple matches
        """
        conn = None
        try:
            conn = self._get_connection()
            cur = conn.cursor()
            
            # Try to find asset by multiple matching strategies
            # 1. Exact IP match (highest priority)
            # 2. Case-insensitive FQDN match
            # 3. Case-insensitive short hostname match
            
            if asset_id:
                # If asset_id provided, use it directly
                cur.execute("""
                    SELECT id, name, hostname, ip_address, os_type, os_version,
                           service_type, port, is_secure, domain,
                           credential_type, username
                    FROM assets.assets
                    WHERE id = %s
                    LIMIT 1
                """, (asset_id,))
            else:
                # Try multiple matching strategies
                cur.execute("""
                    SELECT id, name, hostname, ip_address, os_type, os_version,
                           service_type, port, is_secure, domain,
                           credential_type, username
                    FROM assets.assets
                    WHERE ip_address = %s 
                       OR LOWER(hostname) = %s
                       OR LOWER(SPLIT_PART(hostname, '.', 1)) = %s
                    ORDER BY 
                        CASE 
                            WHEN ip_address = %s THEN 1
                            WHEN LOWER(hostname) = %s THEN 2
                            ELSE 3
                        END
                """, (host, host.lower(), host.lower(), host, host.lower()))
            
            results = cur.fetchall()
            
            if not results:
                logger.warning(f"Connection profile not found for host: {host}")
                return {"found": False, "error": "asset_not_found", "host": host}
            
            # Check for ambiguous matches (multiple results with same priority)
            if len(results) > 1 and not asset_id:
                # Check if we have multiple matches at the same priority level
                candidates = [
                    {
                        "asset_id": str(row['id']),
                        "host": row['ip_address'],
                        "hostname": row['hostname'],
                        "os": row['os_version'] or row['os_type']
                    }
                    for row in results
                ]
                
                logger.warning(f"Ambiguous asset match for host: {host}, found {len(candidates)} candidates")
                return {
                    "found": False,
                    "error": "ambiguous_asset",
                    "host": host,
                    "candidates": candidates
                }
            
            result = results[0]
            
            # Build connection profile based on OS and service type
            asset_id_str = str(result['id'])
            canonical_host = result['ip_address'] or result['hostname']
            
            profile = {
                "found": True,
                "asset_id": asset_id_str,
                "host": result['hostname'] or result['ip_address'],
                "ip": result['ip_address'],
                "hostname": result['hostname'],
                "hostnames": [result['hostname']] if result['hostname'] else [],
                "os": result['os_version'] or result['os_type'],
                "os_type": result['os_type']
            }
            
            # Add service-specific connection parameters with credential_ref
            if result['os_type'] and 'windows' in result['os_type'].lower():
                # Windows host - provide WinRM defaults
                profile['winrm'] = {
                    "port": 5985 if result['service_type'] == 'winrm' else 5985,
                    "use_ssl": result['is_secure'] if result['service_type'] == 'winrm' else False,
                    "domain": result.get('domain'),
                    "username": result.get('username'),
                    "credential_ref": f"secret://secrets.winrm/{canonical_host}"
                }
                
                # Also provide RDP info if available
                if result['service_type'] == 'rdp':
                    profile['rdp'] = {
                        "port": result['port'],
                        "use_ssl": result['is_secure'],
                        "credential_ref": f"secret://secrets.rdp/{canonical_host}"
                    }
            
            if result['os_type'] and result['os_type'].lower() in ['linux', 'unix', 'macos']:
                # Unix-like host - provide SSH defaults
                profile['ssh'] = {
                    "port": result['port'] if result['service_type'] == 'ssh' else 22,
                    "key_based": result['credential_type'] == 'ssh_key' if result['credential_type'] else False,
                    "username": result.get('username'),
                    "credential_ref": f"secret://secrets.ssh/{canonical_host}"
                }
            
            # Add primary service info
            profile['primary_service'] = {
                "type": result['service_type'],
                "port": result['port'],
                "is_secure": result['is_secure']
            }
            
            logger.info(f"Connection profile resolved for host: {host} -> {result['hostname']} (asset_id={asset_id_str})")
            
            return profile
            
        except Exception as e:
            logger.error(f"Failed to get connection profile: {e}")
            raise
        finally:
            if conn:
                conn.close()