"""
Tool Catalog Service
Database-backed tool management for 200+ tools

This service provides:
- CRUD operations for tools, capabilities, and patterns
- Tool versioning and rollback
- Performance telemetry tracking
- Hot reload without system restart
- Query optimization with caching
"""

import os
import json
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
import psycopg2
from psycopg2.extras import RealDictCursor, Json
from psycopg2.pool import ThreadedConnectionPool

logger = logging.getLogger(__name__)


class ToolCatalogService:
    """
    Service for managing tool catalog in PostgreSQL database
    """
    
    def __init__(self, database_url: Optional[str] = None):
        """
        Initialize the tool catalog service
        
        Args:
            database_url: PostgreSQL connection URL (defaults to env var)
        """
        self.database_url = database_url or os.getenv(
            "DATABASE_URL",
            "postgresql://opsconductor:opsconductor_secure_2024@postgres:5432/opsconductor"
        )
        
        # Connection pool for performance
        self.pool = ThreadedConnectionPool(
            minconn=2,
            maxconn=10,
            dsn=self.database_url
        )
        
        # In-memory cache for hot paths
        self._cache: Dict[str, Any] = {}
        self._cache_ttl = 300  # 5 minutes
        self._cache_timestamps: Dict[str, datetime] = {}
        
        logger.info("ToolCatalogService initialized")
    
    def _get_connection(self):
        """Get a connection from the pool"""
        return self.pool.getconn()
    
    def _return_connection(self, conn):
        """Return a connection to the pool"""
        self.pool.putconn(conn)
    
    def _is_cache_valid(self, key: str) -> bool:
        """Check if cache entry is still valid"""
        if key not in self._cache_timestamps:
            return False
        
        age = datetime.now() - self._cache_timestamps[key]
        return age.total_seconds() < self._cache_ttl
    
    def _get_from_cache(self, key: str) -> Optional[Any]:
        """Get value from cache if valid"""
        if self._is_cache_valid(key):
            return self._cache.get(key)
        return None
    
    def _set_cache(self, key: str, value: Any):
        """Set value in cache"""
        self._cache[key] = value
        self._cache_timestamps[key] = datetime.now()
    
    def _clear_cache(self, pattern: Optional[str] = None):
        """Clear cache entries matching pattern"""
        if pattern is None:
            self._cache.clear()
            self._cache_timestamps.clear()
        else:
            keys_to_remove = [k for k in self._cache.keys() if pattern in k]
            for key in keys_to_remove:
                self._cache.pop(key, None)
                self._cache_timestamps.pop(key, None)
    
    # ========================================================================
    # TOOL CRUD OPERATIONS
    # ========================================================================
    
    def create_tool(
        self,
        tool_name: str,
        version: str,
        description: str,
        platform: str,
        category: str,
        defaults: Dict[str, Any],
        dependencies: Optional[List[Dict[str, Any]]] = None,
        metadata: Optional[Dict[str, Any]] = None,
        created_by: Optional[str] = None
    ) -> int:
        """
        Create a new tool in the catalog
        
        Args:
            tool_name: Name of the tool (e.g., "systemctl", "powershell")
            version: Version string (e.g., "1.0", "2.1")
            description: Brief description of the tool
            platform: Platform (linux, windows, network, scheduler, custom)
            category: Category (system, network, automation, monitoring, security)
            defaults: Default configuration (accuracy_level, freshness, data_source)
            dependencies: List of dependencies
            metadata: Additional metadata (tags, author, documentation_url)
            created_by: Username of creator
        
        Returns:
            Tool ID
        """
        conn = self._get_connection()
        try:
            with conn.cursor() as cursor:
                cursor.execute("""
                    INSERT INTO tool_catalog.tools (
                        tool_name, version, description, platform, category,
                        defaults, dependencies, metadata, created_by
                    ) VALUES (
                        %s, %s, %s, %s, %s, %s, %s, %s, %s
                    )
                    RETURNING id
                """, (
                    tool_name, version, description, platform, category,
                    Json(defaults), Json(dependencies or []), Json(metadata or {}),
                    created_by
                ))
                
                tool_id = cursor.fetchone()[0]
                conn.commit()
                
                # Clear cache
                self._clear_cache(tool_name)
                
                logger.info(f"Created tool: {tool_name} v{version} (ID: {tool_id})")
                return tool_id
                
        except Exception as e:
            conn.rollback()
            logger.error(f"Error creating tool {tool_name}: {e}")
            raise
        finally:
            self._return_connection(conn)
    
    def get_tool_by_name(
        self,
        tool_name: str,
        version: Optional[str] = None,
        use_cache: bool = True
    ) -> Optional[Dict[str, Any]]:
        """
        Get tool by name (optionally specific version)
        
        Args:
            tool_name: Name of the tool
            version: Specific version (if None, returns latest)
            use_cache: Whether to use cache
        
        Returns:
            Tool data or None if not found
        """
        cache_key = f"tool:{tool_name}:{version or 'latest'}"
        
        # Check cache
        if use_cache:
            cached = self._get_from_cache(cache_key)
            if cached is not None:
                return cached
        
        conn = self._get_connection()
        try:
            with conn.cursor(cursor_factory=RealDictCursor) as cursor:
                if version:
                    cursor.execute("""
                        SELECT * FROM tool_catalog.tools
                        WHERE tool_name = %s AND version = %s
                        AND enabled = true
                    """, (tool_name, version))
                else:
                    cursor.execute("""
                        SELECT * FROM tool_catalog.tools
                        WHERE tool_name = %s AND is_latest = true
                        AND enabled = true
                    """, (tool_name,))
                
                result = cursor.fetchone()
                
                if result:
                    tool_data = dict(result)
                    self._set_cache(cache_key, tool_data)
                    return tool_data
                
                return None
                
        except Exception as e:
            logger.error(f"Error getting tool {tool_name}: {e}")
            raise
        finally:
            self._return_connection(conn)
    
    def get_tools_by_capability(
        self,
        capability_name: str,
        platform: Optional[str] = None,
        use_cache: bool = True
    ) -> List[Dict[str, Any]]:
        """
        Get all tools that have a specific capability
        
        Args:
            capability_name: Name of the capability (e.g., "service_control")
            platform: Filter by platform (optional)
            use_cache: Whether to use cache
        
        Returns:
            List of tools with their patterns for this capability
        """
        cache_key = f"capability:{capability_name}:{platform or 'all'}"
        
        # Check cache
        if use_cache:
            cached = self._get_from_cache(cache_key)
            if cached is not None:
                return cached
        
        conn = self._get_connection()
        try:
            with conn.cursor(cursor_factory=RealDictCursor) as cursor:
                query = """
                    SELECT 
                        t.id as tool_id,
                        t.tool_name,
                        t.version,
                        t.description as tool_description,
                        t.platform,
                        t.category,
                        t.defaults,
                        t.dependencies,
                        t.metadata,
                        c.id as capability_id,
                        c.capability_name,
                        c.description as capability_description,
                        p.id as pattern_id,
                        p.pattern_name,
                        p.description as pattern_description,
                        p.typical_use_cases,
                        p.time_estimate_ms,
                        p.cost_estimate,
                        p.complexity_score,
                        p.scope,
                        p.completeness,
                        p.limitations,
                        p.policy,
                        p.preference_match,
                        p.required_inputs,
                        p.expected_outputs
                    FROM tool_catalog.tools t
                    JOIN tool_catalog.tool_capabilities c ON t.id = c.tool_id
                    JOIN tool_catalog.tool_patterns p ON c.id = p.capability_id
                    WHERE 
                        t.enabled = true 
                        AND t.status = 'active'
                        AND t.is_latest = true
                        AND c.capability_name = %s
                """
                
                params = [capability_name]
                
                if platform:
                    query += " AND t.platform = %s"
                    params.append(platform)
                
                query += " ORDER BY t.tool_name, p.pattern_name"
                
                cursor.execute(query, params)
                results = cursor.fetchall()
                
                # Group by tool
                tools = {}
                for row in results:
                    tool_name = row['tool_name']
                    
                    if tool_name not in tools:
                        tools[tool_name] = {
                            'tool_id': row['tool_id'],
                            'tool_name': row['tool_name'],
                            'version': row['version'],
                            'description': row['tool_description'],
                            'platform': row['platform'],
                            'category': row['category'],
                            'defaults': row['defaults'],
                            'dependencies': row['dependencies'],
                            'metadata': row['metadata'],
                            'capabilities': {}
                        }
                    
                    capability_name_key = row['capability_name']
                    if capability_name_key not in tools[tool_name]['capabilities']:
                        tools[tool_name]['capabilities'][capability_name_key] = {
                            'capability_id': row['capability_id'],
                            'capability_name': row['capability_name'],
                            'description': row['capability_description'],
                            'patterns': []
                        }
                    
                    tools[tool_name]['capabilities'][capability_name_key]['patterns'].append({
                        'pattern_id': row['pattern_id'],
                        'pattern_name': row['pattern_name'],
                        'description': row['pattern_description'],
                        'typical_use_cases': row['typical_use_cases'],
                        'time_estimate_ms': row['time_estimate_ms'],
                        'cost_estimate': row['cost_estimate'],
                        'complexity_score': float(row['complexity_score']),
                        'scope': row['scope'],
                        'completeness': row['completeness'],
                        'limitations': row['limitations'],
                        'policy': row['policy'],
                        'preference_match': row['preference_match'],
                        'required_inputs': row['required_inputs'],
                        'expected_outputs': row['expected_outputs']
                    })
                
                result_list = list(tools.values())
                self._set_cache(cache_key, result_list)
                
                return result_list
                
        except Exception as e:
            logger.error(f"Error getting tools by capability {capability_name}: {e}")
            raise
        finally:
            self._return_connection(conn)
    
    def get_all_tools(
        self,
        platform: Optional[str] = None,
        category: Optional[str] = None,
        status: str = 'active'
    ) -> List[Dict[str, Any]]:
        """
        Get all tools with optional filters
        
        Args:
            platform: Filter by platform
            category: Filter by category
            status: Filter by status (default: active)
        
        Returns:
            List of tools
        """
        conn = self._get_connection()
        try:
            with conn.cursor(cursor_factory=RealDictCursor) as cursor:
                query = """
                    SELECT * FROM tool_catalog.tools
                    WHERE enabled = true AND is_latest = true
                """
                params = []
                
                if status:
                    query += " AND status = %s"
                    params.append(status)
                
                if platform:
                    query += " AND platform = %s"
                    params.append(platform)
                
                if category:
                    query += " AND category = %s"
                    params.append(category)
                
                query += " ORDER BY tool_name"
                
                cursor.execute(query, params)
                results = cursor.fetchall()
                
                return [dict(row) for row in results]
                
        except Exception as e:
            logger.error(f"Error getting all tools: {e}")
            raise
        finally:
            self._return_connection(conn)
    
    def update_tool(
        self,
        tool_id: int,
        updates: Dict[str, Any],
        updated_by: Optional[str] = None
    ) -> bool:
        """
        Update tool fields
        
        Args:
            tool_id: Tool ID
            updates: Dictionary of fields to update
            updated_by: Username of updater
        
        Returns:
            True if successful
        """
        conn = self._get_connection()
        try:
            # Build UPDATE query dynamically
            allowed_fields = [
                'description', 'platform', 'category', 'status', 'enabled',
                'defaults', 'dependencies', 'metadata'
            ]
            
            set_clauses = []
            params = []
            
            for field, value in updates.items():
                if field in allowed_fields:
                    if field in ['defaults', 'dependencies', 'metadata']:
                        set_clauses.append(f"{field} = %s")
                        params.append(Json(value))
                    else:
                        set_clauses.append(f"{field} = %s")
                        params.append(value)
            
            if not set_clauses:
                logger.warning("No valid fields to update")
                return False
            
            if updated_by:
                set_clauses.append("updated_by = %s")
                params.append(updated_by)
            
            params.append(tool_id)
            
            with conn.cursor() as cursor:
                query = f"""
                    UPDATE tool_catalog.tools
                    SET {', '.join(set_clauses)}
                    WHERE id = %s
                """
                
                cursor.execute(query, params)
                conn.commit()
                
                # Clear cache
                self._clear_cache()
                
                logger.info(f"Updated tool ID {tool_id}")
                return True
                
        except Exception as e:
            conn.rollback()
            logger.error(f"Error updating tool {tool_id}: {e}")
            raise
        finally:
            self._return_connection(conn)
    
    def delete_tool(self, tool_id: int) -> bool:
        """
        Soft delete a tool (sets enabled=false)
        
        Args:
            tool_id: Tool ID
        
        Returns:
            True if successful
        """
        return self.update_tool(tool_id, {'enabled': False})
    
    # ========================================================================
    # CAPABILITY OPERATIONS
    # ========================================================================
    
    def add_capability(
        self,
        tool_id: int,
        capability_name: str,
        description: str
    ) -> int:
        """
        Add a capability to a tool
        
        Args:
            tool_id: Tool ID
            capability_name: Name of the capability
            description: Description of the capability
        
        Returns:
            Capability ID
        """
        conn = self._get_connection()
        try:
            with conn.cursor() as cursor:
                cursor.execute("""
                    INSERT INTO tool_catalog.tool_capabilities (
                        tool_id, capability_name, description
                    ) VALUES (%s, %s, %s)
                    RETURNING id
                """, (tool_id, capability_name, description))
                
                capability_id = cursor.fetchone()[0]
                conn.commit()
                
                # Clear cache
                self._clear_cache(capability_name)
                
                logger.info(f"Added capability {capability_name} to tool ID {tool_id}")
                return capability_id
                
        except Exception as e:
            conn.rollback()
            logger.error(f"Error adding capability: {e}")
            raise
        finally:
            self._return_connection(conn)
    
    # ========================================================================
    # PATTERN OPERATIONS
    # ========================================================================
    
    def add_pattern(
        self,
        capability_id: int,
        pattern_name: str,
        description: str,
        typical_use_cases: List[str],
        time_estimate_ms: str,
        cost_estimate: str,
        complexity_score: float,
        scope: str,
        completeness: str,
        policy: Dict[str, Any],
        preference_match: Dict[str, float],
        required_inputs: List[Dict[str, Any]],
        expected_outputs: List[Dict[str, Any]],
        limitations: Optional[List[str]] = None
    ) -> int:
        """
        Add a pattern to a capability
        
        Args:
            capability_id: Capability ID
            pattern_name: Name of the pattern
            description: Description of the pattern
            typical_use_cases: List of use cases
            time_estimate_ms: Time estimate expression
            cost_estimate: Cost estimate expression
            complexity_score: Complexity score (0.0-1.0)
            scope: Scope (single_item, batch, exhaustive)
            completeness: Completeness (complete, partial, summary)
            policy: Policy constraints
            preference_match: Preference matching scores
            required_inputs: Required input schema
            expected_outputs: Expected output schema
            limitations: List of limitations (optional)
        
        Returns:
            Pattern ID
        """
        conn = self._get_connection()
        try:
            with conn.cursor() as cursor:
                cursor.execute("""
                    INSERT INTO tool_catalog.tool_patterns (
                        capability_id, pattern_name, description,
                        typical_use_cases, time_estimate_ms, cost_estimate,
                        complexity_score, scope, completeness, limitations,
                        policy, preference_match, required_inputs, expected_outputs
                    ) VALUES (
                        %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
                    )
                    RETURNING id
                """, (
                    capability_id, pattern_name, description,
                    Json(typical_use_cases), time_estimate_ms, cost_estimate,
                    complexity_score, scope, completeness, Json(limitations or []),
                    Json(policy), Json(preference_match),
                    Json(required_inputs), Json(expected_outputs)
                ))
                
                pattern_id = cursor.fetchone()[0]
                conn.commit()
                
                # Clear cache
                self._clear_cache()
                
                logger.info(f"Added pattern {pattern_name} to capability ID {capability_id}")
                return pattern_id
                
        except Exception as e:
            conn.rollback()
            logger.error(f"Error adding pattern: {e}")
            raise
        finally:
            self._return_connection(conn)
    
    # ========================================================================
    # TELEMETRY OPERATIONS
    # ========================================================================
    
    def record_telemetry(
        self,
        pattern_id: int,
        actual_time_ms: int,
        actual_cost: float,
        success: bool,
        context_variables: Optional[Dict[str, Any]] = None,
        error_message: Optional[str] = None
    ) -> str:
        """
        Record telemetry for a pattern execution
        
        Args:
            pattern_id: Pattern ID
            actual_time_ms: Actual execution time in milliseconds
            actual_cost: Actual cost
            success: Whether execution was successful
            context_variables: Context variables (N, file_size_kb, etc.)
            error_message: Error message if failed
        
        Returns:
            Execution ID (UUID)
        """
        conn = self._get_connection()
        try:
            with conn.cursor() as cursor:
                cursor.execute("""
                    INSERT INTO tool_catalog.tool_telemetry (
                        pattern_id, actual_time_ms, actual_cost, success,
                        context_variables, error_message
                    ) VALUES (
                        %s, %s, %s, %s, %s, %s
                    )
                    RETURNING execution_id
                """, (
                    pattern_id, actual_time_ms, actual_cost, success,
                    Json(context_variables or {}), error_message
                ))
                
                execution_id = cursor.fetchone()[0]
                conn.commit()
                
                logger.debug(f"Recorded telemetry for pattern ID {pattern_id}")
                return str(execution_id)
                
        except Exception as e:
            conn.rollback()
            logger.error(f"Error recording telemetry: {e}")
            raise
        finally:
            self._return_connection(conn)
    
    # ========================================================================
    # UTILITY METHODS
    # ========================================================================
    
    def health_check(self) -> bool:
        """
        Check if database connection is healthy
        
        Returns:
            True if healthy
        """
        try:
            conn = self._get_connection()
            with conn.cursor() as cursor:
                cursor.execute("SELECT 1")
                cursor.fetchone()
            self._return_connection(conn)
            return True
        except Exception as e:
            logger.error(f"Health check failed: {e}")
            return False
    
    def get_stats(self) -> Dict[str, Any]:
        """
        Get catalog statistics
        
        Returns:
            Statistics dictionary
        """
        conn = self._get_connection()
        try:
            with conn.cursor(cursor_factory=RealDictCursor) as cursor:
                cursor.execute("""
                    SELECT 
                        COUNT(*) as total_tools,
                        COUNT(DISTINCT platform) as platforms,
                        COUNT(DISTINCT category) as categories
                    FROM tool_catalog.tools
                    WHERE enabled = true AND is_latest = true
                """)
                
                stats = dict(cursor.fetchone())
                
                cursor.execute("""
                    SELECT COUNT(*) as total_capabilities
                    FROM tool_catalog.tool_capabilities
                """)
                
                stats.update(dict(cursor.fetchone()))
                
                cursor.execute("""
                    SELECT COUNT(*) as total_patterns
                    FROM tool_catalog.tool_patterns
                """)
                
                stats.update(dict(cursor.fetchone()))
                
                return stats
                
        except Exception as e:
            logger.error(f"Error getting stats: {e}")
            raise
        finally:
            self._return_connection(conn)
    
    def close(self):
        """Close all connections"""
        if self.pool:
            self.pool.closeall()
            logger.info("ToolCatalogService closed")