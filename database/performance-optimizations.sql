-- ============================================================================
-- PERFORMANCE OPTIMIZATIONS FOR TOOL CATALOG
-- Phase 3, Task 3.2: Performance Optimization
-- ============================================================================

-- ============================================================================
-- 1. COMPOSITE INDEXES - Optimize common query patterns
-- ============================================================================

-- Most common query: Get tool by name + latest version + enabled
-- This covers: get_tool_by_name() with no version specified
CREATE INDEX IF NOT EXISTS idx_tools_name_latest_enabled 
ON tool_catalog.tools(tool_name, is_latest, enabled) 
WHERE is_latest = true AND enabled = true;

-- Query: Get tool by name + specific version + enabled
-- This covers: get_tool_by_name() with version specified
CREATE INDEX IF NOT EXISTS idx_tools_name_version_enabled 
ON tool_catalog.tools(tool_name, version, enabled) 
WHERE enabled = true;

-- Query: Get all enabled latest tools (most common list query)
-- This covers: get_all_tools() default behavior
CREATE INDEX IF NOT EXISTS idx_tools_enabled_latest 
ON tool_catalog.tools(enabled, is_latest) 
WHERE enabled = true AND is_latest = true;

-- Query: Filter by platform + enabled + latest
-- This covers: get_all_tools(platform='linux')
CREATE INDEX IF NOT EXISTS idx_tools_platform_enabled_latest 
ON tool_catalog.tools(platform, enabled, is_latest) 
WHERE enabled = true AND is_latest = true;

-- Query: Filter by category + enabled + latest
-- This covers: get_all_tools(category='network')
CREATE INDEX IF NOT EXISTS idx_tools_category_enabled_latest 
ON tool_catalog.tools(category, enabled, is_latest) 
WHERE enabled = true AND is_latest = true;

-- Query: Filter by status + enabled + latest
-- This covers: get_all_tools(status='active')
CREATE INDEX IF NOT EXISTS idx_tools_status_enabled_latest 
ON tool_catalog.tools(status, enabled, is_latest) 
WHERE enabled = true AND is_latest = true;

-- ============================================================================
-- 2. COVERING INDEXES - Avoid table lookups for common queries
-- ============================================================================

-- Covering index for tool list queries (includes commonly selected columns)
-- This allows index-only scans without touching the main table
CREATE INDEX IF NOT EXISTS idx_tools_list_covering 
ON tool_catalog.tools(tool_name, version, platform, category, status) 
WHERE enabled = true AND is_latest = true;

-- ============================================================================
-- 3. JOIN OPTIMIZATION - Speed up capability and pattern lookups
-- ============================================================================

-- Composite index for tool_capabilities JOIN queries
CREATE INDEX IF NOT EXISTS idx_capabilities_tool_id_name 
ON tool_catalog.tool_capabilities(tool_id, capability_name);

-- Composite index for tool_patterns JOIN queries
CREATE INDEX IF NOT EXISTS idx_patterns_capability_id_name 
ON tool_catalog.tool_patterns(capability_id, pattern_name);

-- ============================================================================
-- 4. TELEMETRY QUERY OPTIMIZATION
-- ============================================================================

-- Composite index for telemetry queries by tool + time range
CREATE INDEX IF NOT EXISTS idx_telemetry_tool_time 
ON tool_catalog.tool_telemetry(tool_id, executed_at DESC);

-- Composite index for telemetry queries by pattern + success
CREATE INDEX IF NOT EXISTS idx_telemetry_pattern_success 
ON tool_catalog.tool_telemetry(pattern_id, success, executed_at DESC);

-- Composite index for telemetry queries by environment + time
CREATE INDEX IF NOT EXISTS idx_telemetry_env_time 
ON tool_catalog.tool_telemetry(environment, executed_at DESC) 
WHERE success = true;

-- ============================================================================
-- 5. AUDIT LOG OPTIMIZATION
-- ============================================================================

-- Composite index for audit queries by entity + time
CREATE INDEX IF NOT EXISTS idx_audit_entity_time 
ON tool_catalog.tool_audit_log(entity_type, entity_id, changed_at DESC);

-- Composite index for audit queries by user + time
CREATE INDEX IF NOT EXISTS idx_audit_user_time 
ON tool_catalog.tool_audit_log(changed_by, changed_at DESC);

-- ============================================================================
-- 6. CACHE TABLE OPTIMIZATION
-- ============================================================================

-- Composite index for cache cleanup queries
CREATE INDEX IF NOT EXISTS idx_cache_expires_accessed 
ON tool_catalog.tool_cache(expires_at, last_accessed_at);

-- ============================================================================
-- 7. STATISTICS UPDATE - Ensure query planner has accurate data
-- ============================================================================

-- Update statistics for all tool_catalog tables
ANALYZE tool_catalog.tools;
ANALYZE tool_catalog.tool_capabilities;
ANALYZE tool_catalog.tool_patterns;
ANALYZE tool_catalog.tool_telemetry;
ANALYZE tool_catalog.tool_ab_tests;
ANALYZE tool_catalog.tool_audit_log;
ANALYZE tool_catalog.tool_cache;

-- ============================================================================
-- 8. VACUUM - Reclaim space and update visibility map
-- ============================================================================

-- Vacuum all tables to optimize storage and performance
VACUUM ANALYZE tool_catalog.tools;
VACUUM ANALYZE tool_catalog.tool_capabilities;
VACUUM ANALYZE tool_catalog.tool_patterns;
VACUUM ANALYZE tool_catalog.tool_telemetry;
VACUUM ANALYZE tool_catalog.tool_ab_tests;
VACUUM ANALYZE tool_catalog.tool_audit_log;
VACUUM ANALYZE tool_catalog.tool_cache;

-- ============================================================================
-- 9. MATERIALIZED VIEW - Pre-compute expensive aggregations
-- ============================================================================

-- Materialized view for tool statistics (refreshed periodically)
CREATE MATERIALIZED VIEW IF NOT EXISTS tool_catalog.mv_tool_statistics AS
SELECT 
    t.id,
    t.tool_name,
    t.version,
    t.platform,
    t.category,
    t.status,
    COUNT(DISTINCT tc.id) as capability_count,
    COUNT(DISTINCT tp.id) as pattern_count,
    COUNT(DISTINCT tt.id) as execution_count,
    AVG(tt.actual_time_ms) as avg_execution_time_ms,
    SUM(CASE WHEN tt.success THEN 1 ELSE 0 END)::FLOAT / NULLIF(COUNT(tt.id), 0) as success_rate,
    MAX(tt.executed_at) as last_executed_at
FROM tool_catalog.tools t
LEFT JOIN tool_catalog.tool_capabilities tc ON t.id = tc.tool_id
LEFT JOIN tool_catalog.tool_patterns tp ON tc.id = tp.capability_id
LEFT JOIN tool_catalog.tool_telemetry tt ON t.id = tt.tool_id
WHERE t.enabled = true AND t.is_latest = true
GROUP BY t.id, t.tool_name, t.version, t.platform, t.category, t.status;

-- Index on materialized view
CREATE UNIQUE INDEX IF NOT EXISTS idx_mv_tool_stats_id 
ON tool_catalog.mv_tool_statistics(id);

CREATE INDEX IF NOT EXISTS idx_mv_tool_stats_name 
ON tool_catalog.mv_tool_statistics(tool_name);

-- ============================================================================
-- 10. FUNCTION - Refresh materialized view
-- ============================================================================

CREATE OR REPLACE FUNCTION tool_catalog.refresh_tool_statistics()
RETURNS void AS $$
BEGIN
    REFRESH MATERIALIZED VIEW CONCURRENTLY tool_catalog.mv_tool_statistics;
END;
$$ LANGUAGE plpgsql;

-- ============================================================================
-- 11. QUERY PERFORMANCE TRACKING
-- ============================================================================

-- Enable query statistics tracking (if not already enabled)
-- Note: This requires superuser privileges
-- ALTER SYSTEM SET track_activities = on;
-- ALTER SYSTEM SET track_counts = on;
-- ALTER SYSTEM SET track_io_timing = on;
-- SELECT pg_reload_conf();

-- View to monitor slow queries
CREATE OR REPLACE VIEW tool_catalog.v_slow_queries AS
SELECT 
    query,
    calls,
    total_exec_time,
    mean_exec_time,
    max_exec_time,
    stddev_exec_time
FROM pg_stat_statements
WHERE query LIKE '%tool_catalog%'
ORDER BY mean_exec_time DESC
LIMIT 20;

-- ============================================================================
-- 12. CONNECTION POOL RECOMMENDATIONS
-- ============================================================================

-- Recommended PostgreSQL settings for connection pooling:
-- max_connections = 100
-- shared_buffers = 256MB (25% of RAM for dedicated DB server)
-- effective_cache_size = 1GB (50-75% of RAM)
-- maintenance_work_mem = 64MB
-- checkpoint_completion_target = 0.9
-- wal_buffers = 16MB
-- default_statistics_target = 100
-- random_page_cost = 1.1 (for SSD)
-- effective_io_concurrency = 200 (for SSD)
-- work_mem = 4MB (adjust based on concurrent queries)
-- min_wal_size = 1GB
-- max_wal_size = 4GB

-- ============================================================================
-- VERIFICATION QUERIES
-- ============================================================================

-- Check index usage
SELECT 
    schemaname,
    tablename,
    indexname,
    idx_scan as index_scans,
    idx_tup_read as tuples_read,
    idx_tup_fetch as tuples_fetched
FROM pg_stat_user_indexes
WHERE schemaname = 'tool_catalog'
ORDER BY idx_scan DESC;

-- Check table sizes
SELECT 
    schemaname,
    tablename,
    pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) AS size
FROM pg_tables
WHERE schemaname = 'tool_catalog'
ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC;

-- Check cache hit ratio (should be > 99%)
SELECT 
    sum(heap_blks_read) as heap_read,
    sum(heap_blks_hit) as heap_hit,
    sum(heap_blks_hit) / NULLIF(sum(heap_blks_hit) + sum(heap_blks_read), 0) * 100 AS cache_hit_ratio
FROM pg_statio_user_tables
WHERE schemaname = 'tool_catalog';

-- ============================================================================
-- MAINTENANCE SCHEDULE
-- ============================================================================

-- Recommended maintenance tasks:
-- 1. VACUUM ANALYZE - Daily (automated by autovacuum)
-- 2. REINDEX - Weekly (if heavy write load)
-- 3. Refresh materialized views - Every 5 minutes
-- 4. Check slow queries - Daily
-- 5. Monitor index usage - Weekly
-- 6. Update statistics - After bulk data changes

-- Example cron job for materialized view refresh:
-- */5 * * * * psql -U opsconductor -d opsconductor -c "SELECT tool_catalog.refresh_tool_statistics();"

COMMENT ON SCHEMA tool_catalog IS 'Tool Catalog System - Performance Optimized';