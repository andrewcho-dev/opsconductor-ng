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
import time
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
        
        # Optimized connection pool for performance
        # Settings based on workload analysis:
        # - minconn=5: Keep warm connections ready
        # - maxconn=20: Support higher concurrency
        # - Connection reuse reduces overhead
        self.pool = ThreadedConnectionPool(
            minconn=5,
            maxconn=20,
            dsn=self.database_url
        )
        
        # LRU cache for hot paths (memory-bounded)
        # - max_size=1000: Limit memory usage
        # - default_ttl=300: 5-minute cache lifetime
        # - Automatic LRU eviction prevents unbounded growth
        try:
            from pipeline.services.lru_cache import get_tool_cache
            self._cache = get_tool_cache(max_size=1000, default_ttl=300)
        except Exception as e:
            logger.warning(f"Failed to initialize LRU cache, using simple dict: {e}")
            # Fallback to simple cache
            self._cache: Dict[str, Any] = {}
            self._cache_ttl = 300
            self._cache_timestamps: Dict[str, datetime] = {}
        
        # Initialize metrics collector
        try:
            from pipeline.services.metrics_collector import get_metrics_collector
            self.metrics = get_metrics_collector()
        except Exception as e:
            logger.warning(f"Failed to initialize metrics collector: {e}")
            self.metrics = None
        
        logger.info("ToolCatalogService initialized with optimized connection pool and LRU cache")
    
    def _get_connection(self):
        """Get a connection from the pool"""
        return self.pool.getconn()
    
    def _return_connection(self, conn):
        """Return a connection to the pool"""
        self.pool.putconn(conn)
    
    def _is_cache_valid(self, key: str) -> bool:
        """Check if cache entry is still valid"""
        # LRU cache handles expiration automatically
        if hasattr(self._cache, 'get'):
            return key in self._cache
        
        # Fallback for simple dict cache
        if key not in self._cache_timestamps:
            return False
        age = datetime.now() - self._cache_timestamps[key]
        return age.total_seconds() < self._cache_ttl
    
    def _get_from_cache(self, key: str) -> Optional[Any]:
        """Get value from cache if valid"""
        # LRU cache handles expiration and LRU ordering
        if hasattr(self._cache, 'get'):
            return self._cache.get(key)
        
        # Fallback for simple dict cache
        if self._is_cache_valid(key):
            return self._cache.get(key)
        return None
    
    def _set_cache(self, key: str, value: Any):
        """Set value in cache"""
        # LRU cache handles eviction automatically
        if hasattr(self._cache, 'set'):
            self._cache.set(key, value)
        else:
            # Fallback for simple dict cache
            self._cache[key] = value
            self._cache_timestamps[key] = datetime.now()
    
    def _clear_cache(self, pattern: Optional[str] = None):
        """Clear cache entries matching pattern"""
        if hasattr(self._cache, 'clear_pattern'):
            if pattern is None:
                self._cache.clear()
            else:
                self._cache.clear_pattern(pattern)
        else:
            # Fallback for simple dict cache
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
        start_time = time.time()
        cache_key = f"tool:{tool_name}:{version or 'latest'}"
        
        # Check cache
        if use_cache:
            cached = self._get_from_cache(cache_key)
            if cached is not None:
                if self.metrics:
                    self.metrics.record_cache_hit(tool_name)
                return cached
        
        if use_cache and self.metrics:
            self.metrics.record_cache_miss(tool_name)
        
        conn = self._get_connection()
        try:
            with conn.cursor(cursor_factory=RealDictCursor) as cursor:
                query_start = time.time()
                
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
                
                # Record database query metrics
                if self.metrics:
                    query_duration = (time.time() - query_start) * 1000  # Convert to ms
                    self.metrics.record_db_query('SELECT', query_duration, success=True)
                
                if result:
                    tool_data = dict(result)
                    self._set_cache(cache_key, tool_data)
                    return tool_data
                
                return None
                
        except Exception as e:
            # Record database error
            if self.metrics:
                query_duration = (time.time() - start_time) * 1000
                self.metrics.record_db_query('SELECT', query_duration, success=False)
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
                query_start = time.time()
                
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
                
                # Record database query metrics
                if self.metrics:
                    query_duration = (time.time() - query_start) * 1000  # Convert to ms
                    self.metrics.record_db_query('SELECT', query_duration, success=True)
                
                return [dict(row) for row in results]
                
        except Exception as e:
            # Record database error
            if self.metrics:
                query_duration = (time.time() - query_start) * 1000
                self.metrics.record_db_query('SELECT', query_duration, success=False)
            logger.error(f"Error getting all tools: {e}")
            raise
        finally:
            self._return_connection(conn)
    
    def get_all_tools_with_structure(
        self,
        platform: Optional[str] = None,
        category: Optional[str] = None,
        status: str = 'active',
        use_cache: bool = True
    ) -> List[Dict[str, Any]]:
        """
        Get all tools with full nested structure (tools → capabilities → patterns)
        
        This method returns tools in a format suitable for ProfileLoader transformation.
        Each tool includes all its capabilities and patterns in a nested structure.
        
        Args:
            platform: Filter by platform
            category: Filter by category
            status: Filter by status (default: active)
            use_cache: Whether to use cache
        
        Returns:
            List of tools with nested capabilities and patterns
        """
        cache_key = f"all_tools_structure:{platform or 'all'}:{category or 'all'}:{status}"
        
        # Check cache
        if use_cache:
            cached = self._get_from_cache(cache_key)
            if cached is not None:
                return cached
        
        conn = self._get_connection()
        try:
            with conn.cursor(cursor_factory=RealDictCursor) as cursor:
                # Build query with joins
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
                    LEFT JOIN tool_catalog.tool_capabilities c ON t.id = c.tool_id
                    LEFT JOIN tool_catalog.tool_patterns p ON c.id = p.capability_id
                    WHERE 
                        t.enabled = true 
                        AND t.is_latest = true
                """
                
                params = []
                
                if status:
                    query += " AND t.status = %s"
                    params.append(status)
                
                if platform:
                    query += " AND t.platform = %s"
                    params.append(platform)
                
                if category:
                    query += " AND t.category = %s"
                    params.append(category)
                
                query += " ORDER BY t.tool_name, c.capability_name, p.pattern_name"
                
                cursor.execute(query, params)
                results = cursor.fetchall()
                
                # Group by tool → capability → pattern
                tools = {}
                for row in results:
                    tool_name = row['tool_name']
                    
                    # Initialize tool if not exists
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
                    
                    # Skip if no capability (tool without capabilities)
                    if row['capability_id'] is None:
                        continue
                    
                    capability_name = row['capability_name']
                    
                    # Initialize capability if not exists
                    if capability_name not in tools[tool_name]['capabilities']:
                        tools[tool_name]['capabilities'][capability_name] = {
                            'capability_id': row['capability_id'],
                            'capability_name': row['capability_name'],
                            'description': row['capability_description'],
                            'patterns': []
                        }
                    
                    # Skip if no pattern (capability without patterns)
                    if row['pattern_id'] is None:
                        continue
                    
                    # Add pattern
                    tools[tool_name]['capabilities'][capability_name]['patterns'].append({
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
                
                logger.debug(f"Retrieved {len(result_list)} tools with full structure")
                return result_list
                
        except Exception as e:
            logger.error(f"Error getting all tools with structure: {e}")
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
    
    def get_performance_stats(self) -> Dict[str, Any]:
        """
        Get performance statistics including cache and connection pool metrics
        
        Returns:
            Performance statistics dictionary
        """
        stats = {
            "connection_pool": {
                "min_connections": self.pool.minconn,
                "max_connections": self.pool.maxconn,
                "status": "healthy" if self.health_check() else "unhealthy"
            },
            "cache": {}
        }
        
        # Get cache statistics
        if hasattr(self._cache, 'get_stats'):
            stats["cache"] = self._cache.get_stats()
        else:
            # Fallback for simple dict cache
            stats["cache"] = {
                "size": len(self._cache),
                "type": "simple_dict"
            }
        
        # Get database statistics
        try:
            conn = self._get_connection()
            try:
                with conn.cursor(cursor_factory=RealDictCursor) as cursor:
                    # Get table sizes
                    cursor.execute("""
                        SELECT 
                            schemaname,
                            tablename,
                            pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) AS size,
                            pg_total_relation_size(schemaname||'.'||tablename) AS size_bytes
                        FROM pg_tables
                        WHERE schemaname = 'tool_catalog'
                        ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC
                        LIMIT 5
                    """)
                    
                    stats["database"] = {
                        "top_tables": [dict(row) for row in cursor.fetchall()]
                    }
                    
                    # Get cache hit ratio
                    cursor.execute("""
                        SELECT 
                            sum(heap_blks_read) as heap_read,
                            sum(heap_blks_hit) as heap_hit,
                            CASE 
                                WHEN sum(heap_blks_hit) + sum(heap_blks_read) > 0 
                                THEN sum(heap_blks_hit)::float / (sum(heap_blks_hit) + sum(heap_blks_read)) * 100
                                ELSE 0
                            END AS cache_hit_ratio
                        FROM pg_statio_user_tables
                        WHERE schemaname = 'tool_catalog'
                    """)
                    
                    db_cache = dict(cursor.fetchone())
                    stats["database"]["cache_hit_ratio"] = round(db_cache.get("cache_hit_ratio", 0), 2)
                    
            finally:
                self._return_connection(conn)
                
        except Exception as e:
            logger.error(f"Error getting database stats: {e}")
            stats["database"] = {"error": str(e)}
        
        return stats
    
    # ========================================================================
    # ADDITIONAL API SUPPORT METHODS
    # ========================================================================
    
    def get_tool_versions(self, tool_name: str) -> List[Dict[str, Any]]:
        """
        Get all versions of a tool
        
        Args:
            tool_name: Name of the tool
        
        Returns:
            List of tool versions
        """
        conn = self._get_connection()
        try:
            with conn.cursor(cursor_factory=RealDictCursor) as cursor:
                cursor.execute("""
                    SELECT id, tool_name, version, status, enabled, 
                           created_at, updated_at, is_latest
                    FROM tool_catalog.tools
                    WHERE tool_name = %s
                    ORDER BY created_at DESC
                """, (tool_name,))
                
                return [dict(row) for row in cursor.fetchall()]
                
        except Exception as e:
            logger.error(f"Error getting tool versions for {tool_name}: {e}")
            raise
        finally:
            self._return_connection(conn)
    
    def get_tool_capabilities(self, tool_id: int) -> List[Dict[str, Any]]:
        """
        Get all capabilities for a tool
        
        Args:
            tool_id: Tool ID
        
        Returns:
            List of capabilities
        """
        conn = self._get_connection()
        try:
            with conn.cursor(cursor_factory=RealDictCursor) as cursor:
                cursor.execute("""
                    SELECT id, tool_id, capability_name, description, created_at
                    FROM tool_catalog.tool_capabilities
                    WHERE tool_id = %s
                """, (tool_id,))
                
                return [dict(row) for row in cursor.fetchall()]
                
        except Exception as e:
            logger.error(f"Error getting capabilities for tool {tool_id}: {e}")
            raise
        finally:
            self._return_connection(conn)
    
    def update_tool_by_name(
        self,
        tool_name: str,
        description: Optional[str] = None,
        status: Optional[str] = None,
        enabled: Optional[bool] = None,
        defaults: Optional[Dict[str, Any]] = None,
        dependencies: Optional[List[Dict[str, Any]]] = None,
        metadata: Optional[Dict[str, Any]] = None,
        updated_by: Optional[str] = None
    ) -> bool:
        """
        Update a tool by name (updates latest version)
        
        Args:
            tool_name: Tool name
            description: New description
            status: New status
            enabled: New enabled state
            defaults: New defaults
            dependencies: New dependencies
            metadata: New metadata
            updated_by: Username of updater
        
        Returns:
            True if successful
        """
        # Get tool ID
        tool = self.get_tool_by_name(tool_name)
        if not tool:
            return False
        
        # Build updates dict
        updates = {}
        if description is not None:
            updates['description'] = description
        if status is not None:
            updates['status'] = status
        if enabled is not None:
            updates['enabled'] = enabled
        if defaults is not None:
            updates['defaults'] = defaults
        if dependencies is not None:
            updates['dependencies'] = dependencies
        if metadata is not None:
            updates['metadata'] = metadata
        
        return self.update_tool(tool['id'], updates, updated_by)
    
    def delete_tool_by_name(self, tool_name: str, version: Optional[str] = None) -> bool:
        """
        Delete a tool by name
        
        Args:
            tool_name: Tool name
            version: Specific version (if None, deletes all versions)
        
        Returns:
            True if successful
        """
        conn = self._get_connection()
        try:
            with conn.cursor() as cursor:
                if version:
                    # Delete specific version
                    cursor.execute("""
                        DELETE FROM tool_catalog.tools
                        WHERE tool_name = %s AND version = %s
                    """, (tool_name, version))
                else:
                    # Delete all versions
                    cursor.execute("""
                        DELETE FROM tool_catalog.tools
                        WHERE tool_name = %s
                    """, (tool_name,))
                
                conn.commit()
                self._clear_cache()
                
                logger.info(f"Deleted tool {tool_name}" + (f" version {version}" if version else ""))
                return True
                
        except Exception as e:
            conn.rollback()
            logger.error(f"Error deleting tool {tool_name}: {e}")
            raise
        finally:
            self._return_connection(conn)
    
    def close(self):
        """Close all connections"""
        if self.pool:
            self.pool.closeall()
            logger.info("ToolCatalogService closed")