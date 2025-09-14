#!/usr/bin/env python3
"""
Connection Manager Library for OpsConductor Automation Service
Handles credential management, connection pooling, and target resolution
"""

import asyncio
import json
import structlog
from typing import Dict, Any, Optional, List
import os

try:
    import asyncpg
except ImportError:
    asyncpg = None

try:
    from cryptography.fernet import Fernet
except ImportError:
    Fernet = None

# Configure structured logging
logger = structlog.get_logger(__name__)

class ConnectionManagerError(Exception):
    """Raised when connection management fails"""
    pass

class ConnectionManager:
    """
    Manages connections, credentials, and target resolution for automation tasks
    """
    
    def __init__(self):
        self.db_url = os.getenv("DATABASE_URL", "postgresql://postgres:postgres123@postgres:5432/opsconductor")
        self.connection_cache = {}  # Simple in-memory cache
        self.cache_ttl = 300  # 5 minutes
        
        # Check dependencies
        self.dependencies_available = self._check_dependencies()
        
        logger.info("Connection Manager initialized", 
                   dependencies=self.dependencies_available)

    def _check_dependencies(self) -> Dict[str, bool]:
        """Check if required dependencies are available"""
        return {
            "asyncpg": asyncpg is not None,
            "cryptography": Fernet is not None
        }

    async def resolve_target_group(self, group_name: str) -> List[Dict[str, Any]]:
        """Resolve target group to list of target servers with connection details"""
        if not self.dependencies_available["asyncpg"]:
            logger.error("Database connection not available - asyncpg library missing")
            raise ConnectionManagerError("Database connection not available. Install with: pip install asyncpg")
        
        try:
            conn = await asyncpg.connect(self.db_url)
            try:
                # Get target group ID
                group_query = """
                    SELECT id FROM target_groups 
                    WHERE name = $1 AND is_active = true
                """
                group_row = await conn.fetchrow(group_query, group_name)
                
                if not group_row:
                    logger.warning("Target group not found", group_name=group_name)
                    return []
                
                group_id = group_row['id']
                
                # Get targets in the group with their credentials
                targets_query = """
                    SELECT 
                        t.id,
                        t.name,
                        t.hostname,
                        t.ip_address,
                        t.port,
                        t.target_type,
                        t.metadata,
                        c.id as credential_id,
                        c.username,
                        c.encrypted_password,
                        c.credential_type,
                        c.metadata as credential_metadata
                    FROM targets t
                    JOIN target_group_members tgm ON t.id = tgm.target_id
                    LEFT JOIN credentials c ON t.credential_id = c.id
                    WHERE tgm.target_group_id = $1 
                    AND t.is_active = true
                    ORDER BY t.name
                """
                
                rows = await conn.fetch(targets_query, group_id)
                
                targets = []
                for row in rows:
                    target = {
                        "id": row['id'],
                        "name": row['name'],
                        "hostname": row['hostname'],
                        "ip_address": row['ip_address'],
                        "port": row['port'],
                        "target_type": row['target_type'],
                        "metadata": row['metadata'] or {},
                        "credentials": None
                    }
                    
                    # Add credentials if available
                    if row['credential_id']:
                        target["credentials"] = {
                            "id": row['credential_id'],
                            "username": row['username'],
                            "credential_type": row['credential_type'],
                            "metadata": row['credential_metadata'] or {}
                            # Note: encrypted_password is not included for security
                        }
                    
                    targets.append(target)
                
                logger.info("Resolved target group", 
                           group_name=group_name, 
                           target_count=len(targets))
                return targets
                
            finally:
                await conn.close()
                
        except Exception as e:
            logger.error("Failed to resolve target group", 
                        group_name=group_name, 
                        error=str(e))
            raise ConnectionManagerError(f"Failed to resolve target group '{group_name}': {str(e)}")

    async def get_target_credentials(self, target_id: int) -> Optional[Dict[str, str]]:
        """Get decrypted credentials for a target"""
        if not self.dependencies_available["asyncpg"]:
            logger.error("Database connection not available - asyncpg library missing")
            raise ConnectionManagerError("Database connection not available. Install with: pip install asyncpg")
        
        if not self.dependencies_available["cryptography"]:
            logger.error("Encryption not available - cryptography library missing")
            raise ConnectionManagerError("Encryption not available. Install with: pip install cryptography")
        
        try:
            conn = await asyncpg.connect(self.db_url)
            try:
                # Get target with credentials
                query = """
                    SELECT 
                        t.name as target_name,
                        c.username,
                        c.encrypted_password,
                        c.credential_type,
                        c.metadata
                    FROM targets t
                    JOIN credentials c ON t.credential_id = c.id
                    WHERE t.id = $1 AND t.is_active = true
                """
                
                row = await conn.fetchrow(query, target_id)
                
                if not row:
                    logger.warning("Target or credentials not found", target_id=target_id)
                    return None
                
                # Decrypt password
                encryption_key = os.getenv("ENCRYPTION_KEY")
                if not encryption_key:
                    logger.error("Encryption key not configured")
                    raise ConnectionManagerError("Encryption key not configured")
                
                fernet = Fernet(encryption_key.encode())
                decrypted_password = fernet.decrypt(row['encrypted_password'].encode()).decode()
                
                credentials = {
                    "username": row['username'],
                    "password": decrypted_password,
                    "credential_type": row['credential_type'],
                    "metadata": row['metadata'] or {}
                }
                
                logger.info("Retrieved target credentials", 
                           target_id=target_id,
                           target_name=row['target_name'],
                           username=row['username'])
                return credentials
                
            finally:
                await conn.close()
                
        except Exception as e:
            logger.error("Failed to get target credentials", 
                        target_id=target_id, 
                        error=str(e))
            raise ConnectionManagerError(f"Failed to get credentials for target {target_id}: {str(e)}")

    async def test_target_connectivity(self, target: Dict[str, Any]) -> Dict[str, Any]:
        """Test connectivity to a target server"""
        logger.info("Testing target connectivity", target=target)
        
        hostname = target.get('hostname') or target.get('ip_address')
        port = target.get('port', 22)  # Default to SSH port
        
        if not hostname:
            return {
                "success": False,
                "error": "No hostname or IP address provided",
                "target": target
            }
        
        try:
            # Simple TCP connectivity test
            future = asyncio.open_connection(hostname, port)
            reader, writer = await asyncio.wait_for(future, timeout=10.0)
            
            writer.close()
            await writer.wait_closed()
            
            logger.info("Target connectivity test successful", 
                       hostname=hostname, port=port)
            return {
                "success": True,
                "message": f"Successfully connected to {hostname}:{port}",
                "target": target
            }
            
        except asyncio.TimeoutError:
            error_msg = f"Connection timeout to {hostname}:{port}"
            logger.warning("Target connectivity test failed", 
                          hostname=hostname, port=port, error="timeout")
            return {
                "success": False,
                "error": error_msg,
                "target": target
            }
        except Exception as e:
            error_msg = f"Connection failed to {hostname}:{port}: {str(e)}"
            logger.warning("Target connectivity test failed", 
                          hostname=hostname, port=port, error=str(e))
            return {
                "success": False,
                "error": error_msg,
                "target": target
            }

    async def get_all_targets(self) -> List[Dict[str, Any]]:
        """Get all active targets"""
        if not self.dependencies_available["asyncpg"]:
            logger.error("Database connection not available - asyncpg library missing")
            raise ConnectionManagerError("Database connection not available. Install with: pip install asyncpg")
        
        try:
            conn = await asyncpg.connect(self.db_url)
            try:
                query = """
                    SELECT 
                        t.id,
                        t.name,
                        t.hostname,
                        t.ip_address,
                        t.port,
                        t.target_type,
                        t.metadata,
                        c.id as credential_id,
                        c.username,
                        c.credential_type
                    FROM targets t
                    LEFT JOIN credentials c ON t.credential_id = c.id
                    WHERE t.is_active = true
                    ORDER BY t.name
                """
                
                rows = await conn.fetch(query)
                
                targets = []
                for row in rows:
                    target = {
                        "id": row['id'],
                        "name": row['name'],
                        "hostname": row['hostname'],
                        "ip_address": row['ip_address'],
                        "port": row['port'],
                        "target_type": row['target_type'],
                        "metadata": row['metadata'] or {},
                        "has_credentials": row['credential_id'] is not None
                    }
                    
                    if row['credential_id']:
                        target["credentials"] = {
                            "id": row['credential_id'],
                            "username": row['username'],
                            "credential_type": row['credential_type']
                        }
                    
                    targets.append(target)
                
                logger.info("Retrieved all targets", target_count=len(targets))
                return targets
                
            finally:
                await conn.close()
                
        except Exception as e:
            logger.error("Failed to get all targets", error=str(e))
            raise ConnectionManagerError(f"Failed to get all targets: {str(e)}")

    async def get_target_by_id(self, target_id: int) -> Optional[Dict[str, Any]]:
        """Get a specific target by ID"""
        if not self.dependencies_available["asyncpg"]:
            logger.error("Database connection not available - asyncpg library missing")
            raise ConnectionManagerError("Database connection not available. Install with: pip install asyncpg")
        
        try:
            conn = await asyncpg.connect(self.db_url)
            try:
                query = """
                    SELECT 
                        t.id,
                        t.name,
                        t.hostname,
                        t.ip_address,
                        t.port,
                        t.target_type,
                        t.metadata,
                        c.id as credential_id,
                        c.username,
                        c.credential_type,
                        c.metadata as credential_metadata
                    FROM targets t
                    LEFT JOIN credentials c ON t.credential_id = c.id
                    WHERE t.id = $1 AND t.is_active = true
                """
                
                row = await conn.fetchrow(query, target_id)
                
                if not row:
                    logger.warning("Target not found", target_id=target_id)
                    return None
                
                target = {
                    "id": row['id'],
                    "name": row['name'],
                    "hostname": row['hostname'],
                    "ip_address": row['ip_address'],
                    "port": row['port'],
                    "target_type": row['target_type'],
                    "metadata": row['metadata'] or {},
                    "credentials": None
                }
                
                if row['credential_id']:
                    target["credentials"] = {
                        "id": row['credential_id'],
                        "username": row['username'],
                        "credential_type": row['credential_type'],
                        "metadata": row['credential_metadata'] or {}
                    }
                
                logger.info("Retrieved target by ID", target_id=target_id, target_name=row['name'])
                return target
                
            finally:
                await conn.close()
                
        except Exception as e:
            logger.error("Failed to get target by ID", target_id=target_id, error=str(e))
            raise ConnectionManagerError(f"Failed to get target {target_id}: {str(e)}")

    def get_library_info(self) -> Dict[str, Any]:
        """Get library information"""
        return {
            "name": "Connection Manager Library",
            "version": "1.0.0",
            "description": "Manages connections, credentials, and target resolution",
            "capabilities": [
                "Target group resolution",
                "Credential encryption/decryption",
                "Connectivity testing",
                "Hostname resolution",
                "Connection caching",
                "Target management"
            ],
            "cache_ttl": self.cache_ttl,
            "dependencies": self.dependencies_available,
            "ready": all(self.dependencies_available.values())
        }


# Library registration function
def get_library():
    """Factory function to create library instance"""
    return ConnectionManager()


# Function mappings for the automation service worker
FUNCTION_MAPPINGS = {
    "resolve_target_group": "resolve_target_group",
    "get_target_credentials": "get_target_credentials",
    "test_target_connectivity": "test_target_connectivity",
    "get_all_targets": "get_all_targets",
    "get_target_by_id": "get_target_by_id",
    "get_info": "get_library_info"
}


# Example usage
if __name__ == "__main__":
    async def demo():
        manager = ConnectionManager()
        
        print("Connection Manager Library Demo")
        print("=" * 50)
        
        # Show library info
        info = manager.get_library_info()
        print(f"Library: {info['name']} v{info['version']}")
        print(f"Ready: {info['ready']}")
        print(f"Dependencies: {info['dependencies']}")
        print(f"Capabilities: {', '.join(info['capabilities'])}")
        
        print("\nLibrary ready for automation service integration!")
    
    asyncio.run(demo())

# Module-level functions for direct worker access
_library_instance = None

def _get_library_instance():
    """Get or create library instance"""
    global _library_instance
    if _library_instance is None:
        _library_instance = ConnectionManager()
    return _library_instance

def get_library_info():
    """Module-level function for get_library_info"""
    return _get_library_instance().get_library_info()

async def resolve_target_group(group_name):
    """Module-level function for resolve_target_group"""
    return await _get_library_instance().resolve_target_group(group_name)

async def get_target_credentials(target_id):
    """Module-level function for get_target_credentials"""
    return await _get_library_instance().get_target_credentials(target_id)

async def test_target_connectivity(target):
    """Module-level function for test_target_connectivity"""
    return await _get_library_instance().test_target_connectivity(target)

async def get_all_targets():
    """Module-level function for get_all_targets"""
    return await _get_library_instance().get_all_targets()

async def get_target_by_id(target_id):
    """Module-level function for get_target_by_id"""
    return await _get_library_instance().get_target_by_id(target_id)
