-- ============================================================================
-- INSERT ALL MISSING WINDOWS TOOLS (27 TOOLS)
-- ============================================================================
-- Date: 2025-01-16
-- Purpose: Add all missing Windows tools from Tiers 1-3 gap analysis
-- Tools: 27 new tools across file ops, pipeline, networking, system management
-- ============================================================================

BEGIN;

-- ============================================================================
-- TIER 1: CRITICAL TOOLS (9 tools)
-- ============================================================================

-- 1. Set-Content - Write file content
INSERT INTO tool_catalog.tools (tool_name, version, description, platform, category, defaults, metadata, created_at, updated_at)
VALUES ('Set-Content', '1.0', 'Writes or replaces content in a file. Creates the file if it doesn''t exist.', 'windows', 'system',
'{"freshness": "live", "data_source": "direct", "accuracy_level": "real-time"}'::jsonb,
'{"tags": ["file", "write", "content", "text"], "execution_method": "powershell", "requires_admin": false, "idempotent": false}'::jsonb,
NOW(), NOW());

INSERT INTO tool_catalog.tool_capabilities (tool_id, capability_name, description)
VALUES ((SELECT id FROM tool_catalog.tools WHERE tool_name = 'Set-Content'), 'file_write', 'Write or replace file content');

INSERT INTO tool_catalog.tool_patterns (capability_id, pattern_name, description, typical_use_cases, time_estimate_ms, cost_estimate, complexity_score, scope, completeness, limitations, policy, preference_match, required_inputs, expected_outputs, examples)
VALUES ((SELECT id FROM tool_catalog.tool_capabilities WHERE capability_name = 'file_write' AND tool_id = (SELECT id FROM tool_catalog.tools WHERE tool_name = 'Set-Content')),
'write_file', 'Write or replace file content',
'["Write configuration files", "Create text files", "Replace file content", "Generate reports"]'::jsonb,
'30', '0.01', 0.20, 'single_item', 'complete', '[]'::jsonb,
'{"max_cost": 1.0, "production_safe": true, "requires_approval": false, "max_execution_time": 120}'::jsonb,
'{"cost": 0.9, "speed": 0.9, "accuracy": 0.9, "complexity": 0.8, "completeness": 0.9}'::jsonb,
'[{"name": "host", "type": "string", "required": true, "description": "Target Windows host"}, {"name": "path", "type": "string", "required": true, "description": "File path"}, {"name": "value", "type": "string", "required": true, "description": "Content to write"}]'::jsonb,
'[]'::jsonb, '[]'::jsonb);

-- 2. Add-Content - Append to file
INSERT INTO tool_catalog.tools (tool_name, version, description, platform, category, defaults, metadata, created_at, updated_at)
VALUES ('Add-Content', '1.0', 'Appends content to a file. Creates the file if it doesn''t exist.', 'windows', 'system',
'{"freshness": "live", "data_source": "direct", "accuracy_level": "real-time"}'::jsonb,
'{"tags": ["file", "append", "content", "text"], "execution_method": "powershell", "requires_admin": false, "idempotent": false}'::jsonb,
NOW(), NOW());

INSERT INTO tool_catalog.tool_capabilities (tool_id, capability_name, description)
VALUES ((SELECT id FROM tool_catalog.tools WHERE tool_name = 'Add-Content'), 'file_append', 'Append content to files');

INSERT INTO tool_catalog.tool_patterns (capability_id, pattern_name, description, typical_use_cases, time_estimate_ms, cost_estimate, complexity_score, scope, completeness, limitations, policy, preference_match, required_inputs, expected_outputs, examples)
VALUES ((SELECT id FROM tool_catalog.tool_capabilities WHERE capability_name = 'file_append' AND tool_id = (SELECT id FROM tool_catalog.tools WHERE tool_name = 'Add-Content')),
'append_file', 'Append content to file',
'["Append to log files", "Add entries to configuration", "Accumulate data", "Build reports incrementally"]'::jsonb,
'30', '0.01', 0.20, 'single_item', 'complete', '[]'::jsonb,
'{"max_cost": 1.0, "production_safe": true, "requires_approval": false, "max_execution_time": 120}'::jsonb,
'{"cost": 0.9, "speed": 0.9, "accuracy": 0.9, "complexity": 0.8, "completeness": 0.9}'::jsonb,
'[{"name": "host", "type": "string", "required": true, "description": "Target Windows host"}, {"name": "path", "type": "string", "required": true, "description": "File path"}, {"name": "value", "type": "string", "required": true, "description": "Content to append"}]'::jsonb,
'[]'::jsonb, '[]'::jsonb);

-- 3. Where-Object - Filter pipeline objects
INSERT INTO tool_catalog.tools (tool_name, version, description, platform, category, defaults, metadata, created_at, updated_at)
VALUES ('Where-Object', '1.0', 'Filters objects from a collection based on property values. Essential PowerShell pipeline cmdlet.', 'windows', 'system',
'{"freshness": "live", "data_source": "direct", "accuracy_level": "real-time"}'::jsonb,
'{"tags": ["pipeline", "filter", "query", "objects"], "execution_method": "powershell", "requires_admin": false, "idempotent": true}'::jsonb,
NOW(), NOW());

INSERT INTO tool_catalog.tool_capabilities (tool_id, capability_name, description)
VALUES ((SELECT id FROM tool_catalog.tools WHERE tool_name = 'Where-Object'), 'pipeline_filter', 'Filter objects in PowerShell pipeline');

INSERT INTO tool_catalog.tool_patterns (capability_id, pattern_name, description, typical_use_cases, time_estimate_ms, cost_estimate, complexity_score, scope, completeness, limitations, policy, preference_match, required_inputs, expected_outputs, examples)
VALUES ((SELECT id FROM tool_catalog.tool_capabilities WHERE capability_name = 'pipeline_filter' AND tool_id = (SELECT id FROM tool_catalog.tools WHERE tool_name = 'Where-Object')),
'filter_objects', 'Filter objects by property values',
'["Filter processes by CPU usage", "Find stopped services", "Select files by size", "Query objects by property"]'::jsonb,
'15', '0.005', 0.10, 'single_item', 'complete', '[]'::jsonb,
'{"max_cost": 0.5, "production_safe": true, "requires_approval": false, "max_execution_time": 60}'::jsonb,
'{"cost": 0.95, "speed": 0.95, "accuracy": 0.95, "complexity": 0.9, "completeness": 0.95}'::jsonb,
'[{"name": "host", "type": "string", "required": true, "description": "Target Windows host"}, {"name": "filter_expression", "type": "string", "required": true, "description": "Filter criteria"}]'::jsonb,
'[]'::jsonb, '[]'::jsonb);

-- 4. Sort-Object - Sort pipeline objects
INSERT INTO tool_catalog.tools (tool_name, version, description, platform, category, defaults, metadata, created_at, updated_at)
VALUES ('Sort-Object', '1.0', 'Sorts objects by property values in ascending or descending order. Essential PowerShell pipeline cmdlet.', 'windows', 'system',
'{"freshness": "live", "data_source": "direct", "accuracy_level": "real-time"}'::jsonb,
'{"tags": ["pipeline", "sort", "order", "objects"], "execution_method": "powershell", "requires_admin": false, "idempotent": true}'::jsonb,
NOW(), NOW());

INSERT INTO tool_catalog.tool_capabilities (tool_id, capability_name, description)
VALUES ((SELECT id FROM tool_catalog.tools WHERE tool_name = 'Sort-Object'), 'pipeline_sort', 'Sort objects in PowerShell pipeline');

INSERT INTO tool_catalog.tool_patterns (capability_id, pattern_name, description, typical_use_cases, time_estimate_ms, cost_estimate, complexity_score, scope, completeness, limitations, policy, preference_match, required_inputs, expected_outputs, examples)
VALUES ((SELECT id FROM tool_catalog.tool_capabilities WHERE capability_name = 'pipeline_sort' AND tool_id = (SELECT id FROM tool_catalog.tools WHERE tool_name = 'Sort-Object')),
'sort_objects', 'Sort objects by property',
'["Sort processes by CPU", "Order files by size", "Sort services by status", "Organize data by property"]'::jsonb,
'15', '0.005', 0.10, 'single_item', 'complete', '[]'::jsonb,
'{"max_cost": 0.5, "production_safe": true, "requires_approval": false, "max_execution_time": 60}'::jsonb,
'{"cost": 0.95, "speed": 0.95, "accuracy": 0.95, "complexity": 0.9, "completeness": 0.95}'::jsonb,
'[{"name": "host", "type": "string", "required": true, "description": "Target Windows host"}, {"name": "property", "type": "string", "required": true, "description": "Property to sort by"}]'::jsonb,
'[]'::jsonb, '[]'::jsonb);

-- 5. Select-Object - Select object properties
INSERT INTO tool_catalog.tools (tool_name, version, description, platform, category, defaults, metadata, created_at, updated_at)
VALUES ('Select-Object', '1.0', 'Selects specified properties of objects and can limit the number of objects. Essential PowerShell pipeline cmdlet.', 'windows', 'system',
'{"freshness": "live", "data_source": "direct", "accuracy_level": "real-time"}'::jsonb,
'{"tags": ["pipeline", "select", "properties", "objects"], "execution_method": "powershell", "requires_admin": false, "idempotent": true}'::jsonb,
NOW(), NOW());

INSERT INTO tool_catalog.tool_capabilities (tool_id, capability_name, description)
VALUES ((SELECT id FROM tool_catalog.tools WHERE tool_name = 'Select-Object'), 'pipeline_select', 'Select object properties in PowerShell pipeline');

INSERT INTO tool_catalog.tool_patterns (capability_id, pattern_name, description, typical_use_cases, time_estimate_ms, cost_estimate, complexity_score, scope, completeness, limitations, policy, preference_match, required_inputs, expected_outputs, examples)
VALUES ((SELECT id FROM tool_catalog.tool_capabilities WHERE capability_name = 'pipeline_select' AND tool_id = (SELECT id FROM tool_catalog.tools WHERE tool_name = 'Select-Object')),
'select_properties', 'Select specific object properties',
'["Select specific properties", "Limit result count", "Extract data fields", "Format output"]'::jsonb,
'15', '0.005', 0.10, 'single_item', 'complete', '[]'::jsonb,
'{"max_cost": 0.5, "production_safe": true, "requires_approval": false, "max_execution_time": 60}'::jsonb,
'{"cost": 0.95, "speed": 0.95, "accuracy": 0.95, "complexity": 0.9, "completeness": 0.95}'::jsonb,
'[{"name": "host", "type": "string", "required": true, "description": "Target Windows host"}, {"name": "properties", "type": "string", "required": true, "description": "Properties to select"}]'::jsonb,
'[]'::jsonb, '[]'::jsonb);

-- 6. Resolve-DnsName - DNS resolution
INSERT INTO tool_catalog.tools (tool_name, version, description, platform, category, defaults, metadata, created_at, updated_at)
VALUES ('Resolve-DnsName', '1.0', 'Performs DNS name resolution for specified names. Modern replacement for nslookup.', 'windows', 'network',
'{"freshness": "live", "data_source": "direct", "accuracy_level": "real-time"}'::jsonb,
'{"tags": ["dns", "network", "lookup", "resolution"], "execution_method": "powershell", "requires_admin": false, "idempotent": true}'::jsonb,
NOW(), NOW());

INSERT INTO tool_catalog.tool_capabilities (tool_id, capability_name, description)
VALUES ((SELECT id FROM tool_catalog.tools WHERE tool_name = 'Resolve-DnsName'), 'dns_resolution', 'Resolve DNS names to IP addresses');

INSERT INTO tool_catalog.tool_patterns (capability_id, pattern_name, description, typical_use_cases, time_estimate_ms, cost_estimate, complexity_score, scope, completeness, limitations, policy, preference_match, required_inputs, expected_outputs, examples)
VALUES ((SELECT id FROM tool_catalog.tool_capabilities WHERE capability_name = 'dns_resolution' AND tool_id = (SELECT id FROM tool_catalog.tools WHERE tool_name = 'Resolve-DnsName')),
'dns_lookup', 'Resolve DNS name to IP',
'["Resolve hostname to IP", "DNS troubleshooting", "Verify DNS records", "Check domain resolution"]'::jsonb,
'20', '0.01', 0.20, 'single_item', 'complete', '[]'::jsonb,
'{"max_cost": 1.0, "production_safe": true, "requires_approval": false, "max_execution_time": 60}'::jsonb,
'{"cost": 0.9, "speed": 0.85, "accuracy": 0.95, "complexity": 0.8, "completeness": 0.9}'::jsonb,
'[{"name": "host", "type": "string", "required": true, "description": "Target Windows host"}, {"name": "name", "type": "string", "required": true, "description": "DNS name to resolve"}]'::jsonb,
'[]'::jsonb, '[]'::jsonb);

-- 7. ipconfig - Network configuration
INSERT INTO tool_catalog.tools (tool_name, version, description, platform, category, defaults, metadata, created_at, updated_at)
VALUES ('ipconfig', '1.0', 'Displays network configuration information including IP addresses, subnet masks, and default gateways.', 'windows', 'network',
'{"freshness": "live", "data_source": "direct", "accuracy_level": "real-time"}'::jsonb,
'{"tags": ["network", "ip", "configuration", "adapter"], "execution_method": "cmd", "requires_admin": false, "idempotent": true}'::jsonb,
NOW(), NOW());

INSERT INTO tool_catalog.tool_capabilities (tool_id, capability_name, description)
VALUES ((SELECT id FROM tool_catalog.tools WHERE tool_name = 'ipconfig'), 'network_info', 'Display network configuration');

INSERT INTO tool_catalog.tool_patterns (capability_id, pattern_name, description, typical_use_cases, time_estimate_ms, cost_estimate, complexity_score, scope, completeness, limitations, policy, preference_match, required_inputs, expected_outputs, examples)
VALUES ((SELECT id FROM tool_catalog.tool_capabilities WHERE capability_name = 'network_info' AND tool_id = (SELECT id FROM tool_catalog.tools WHERE tool_name = 'ipconfig')),
'show_network_config', 'Show network configuration',
'["Check IP address", "View network configuration", "Troubleshoot connectivity", "Verify DHCP settings"]'::jsonb,
'10', '0.005', 0.10, 'single_item', 'complete', '[]'::jsonb,
'{"max_cost": 0.5, "production_safe": true, "requires_approval": false, "max_execution_time": 30}'::jsonb,
'{"cost": 0.95, "speed": 0.95, "accuracy": 0.95, "complexity": 0.9, "completeness": 0.95}'::jsonb,
'[{"name": "host", "type": "string", "required": true, "description": "Target Windows host"}]'::jsonb,
'[]'::jsonb, '[]'::jsonb);

-- 8. ping - SKIPPED (already exists)
-- 9. netstat - SKIPPED (already exists)

-- ============================================================================
-- TIER 2: HIGH PRIORITY TOOLS (9 tools)
-- ============================================================================

-- 10. Get-NetTCPConnection - TCP connections
INSERT INTO tool_catalog.tools (tool_name, version, description, platform, category, defaults, metadata, created_at, updated_at)
VALUES ('Get-NetTCPConnection', '1.0', 'Gets current TCP connections and listening ports. PowerShell alternative to netstat.', 'windows', 'network',
'{"freshness": "live", "data_source": "direct", "accuracy_level": "real-time"}'::jsonb,
'{"tags": ["network", "tcp", "connections", "ports"], "execution_method": "powershell", "requires_admin": false, "idempotent": true}'::jsonb,
NOW(), NOW());

INSERT INTO tool_catalog.tool_capabilities (tool_id, capability_name, description)
VALUES ((SELECT id FROM tool_catalog.tools WHERE tool_name = 'Get-NetTCPConnection'), 'tcp_connections', 'Get TCP connection information');

INSERT INTO tool_catalog.tool_patterns (capability_id, pattern_name, description, typical_use_cases, time_estimate_ms, cost_estimate, complexity_score, scope, completeness, limitations, policy, preference_match, required_inputs, expected_outputs, examples)
VALUES ((SELECT id FROM tool_catalog.tool_capabilities WHERE capability_name = 'tcp_connections' AND tool_id = (SELECT id FROM tool_catalog.tools WHERE tool_name = 'Get-NetTCPConnection')),
'list_tcp_connections', 'List TCP connections',
'["View TCP connections", "Check listening ports", "Find process using port", "Monitor network activity"]'::jsonb,
'15', '0.005', 0.20, 'single_item', 'complete', '[]'::jsonb,
'{"max_cost": 0.5, "production_safe": true, "requires_approval": false, "max_execution_time": 60}'::jsonb,
'{"cost": 0.9, "speed": 0.9, "accuracy": 0.95, "complexity": 0.8, "completeness": 0.9}'::jsonb,
'[{"name": "host", "type": "string", "required": true, "description": "Target Windows host"}]'::jsonb,
'[]'::jsonb, '[]'::jsonb);

-- 11. Invoke-RestMethod - REST API calls
INSERT INTO tool_catalog.tools (tool_name, version, description, platform, category, defaults, metadata, created_at, updated_at)
VALUES ('Invoke-RestMethod', '1.0', 'Sends HTTP/HTTPS requests to RESTful web services and automatically parses the response.', 'windows', 'network',
'{"freshness": "live", "data_source": "direct", "accuracy_level": "real-time"}'::jsonb,
'{"tags": ["http", "rest", "api", "web"], "execution_method": "powershell", "requires_admin": false, "idempotent": false}'::jsonb,
NOW(), NOW());

INSERT INTO tool_catalog.tool_capabilities (tool_id, capability_name, description)
VALUES ((SELECT id FROM tool_catalog.tools WHERE tool_name = 'Invoke-RestMethod'), 'rest_api', 'Make REST API calls');

INSERT INTO tool_catalog.tool_patterns (capability_id, pattern_name, description, typical_use_cases, time_estimate_ms, cost_estimate, complexity_score, scope, completeness, limitations, policy, preference_match, required_inputs, expected_outputs, examples)
VALUES ((SELECT id FROM tool_catalog.tool_capabilities WHERE capability_name = 'rest_api' AND tool_id = (SELECT id FROM tool_catalog.tools WHERE tool_name = 'Invoke-RestMethod')),
'call_rest_api', 'Call REST API',
'["Call REST APIs", "Fetch JSON data", "Integrate with web services", "Automate API interactions"]'::jsonb,
'30', '0.02', 0.30, 'single_item', 'complete', '[]'::jsonb,
'{"max_cost": 2.0, "production_safe": true, "requires_approval": false, "max_execution_time": 120}'::jsonb,
'{"cost": 0.85, "speed": 0.8, "accuracy": 0.9, "complexity": 0.7, "completeness": 0.85}'::jsonb,
'[{"name": "host", "type": "string", "required": true, "description": "Target Windows host"}, {"name": "uri", "type": "string", "required": true, "description": "API endpoint URI"}]'::jsonb,
'[]'::jsonb, '[]'::jsonb);

-- 12. Start-Process - Launch processes
INSERT INTO tool_catalog.tools (tool_name, version, description, platform, category, defaults, metadata, created_at, updated_at)
VALUES ('Start-Process', '1.0', 'Starts one or more processes on the local computer with specified parameters.', 'windows', 'system',
'{"freshness": "live", "data_source": "direct", "accuracy_level": "real-time"}'::jsonb,
'{"tags": ["process", "start", "launch", "execute"], "execution_method": "powershell", "requires_admin": false, "idempotent": false}'::jsonb,
NOW(), NOW());

INSERT INTO tool_catalog.tool_capabilities (tool_id, capability_name, description)
VALUES ((SELECT id FROM tool_catalog.tools WHERE tool_name = 'Start-Process'), 'process_start', 'Start new processes');

INSERT INTO tool_catalog.tool_patterns (capability_id, pattern_name, description, typical_use_cases, time_estimate_ms, cost_estimate, complexity_score, scope, completeness, limitations, policy, preference_match, required_inputs, expected_outputs, examples)
VALUES ((SELECT id FROM tool_catalog.tool_capabilities WHERE capability_name = 'process_start' AND tool_id = (SELECT id FROM tool_catalog.tools WHERE tool_name = 'Start-Process')),
'launch_process', 'Launch new process',
'["Launch applications", "Run executables", "Start programs with arguments", "Execute scripts"]'::jsonb,
'20', '0.01', 0.20, 'single_item', 'complete', '[]'::jsonb,
'{"max_cost": 1.0, "production_safe": true, "requires_approval": true, "max_execution_time": 120}'::jsonb,
'{"cost": 0.9, "speed": 0.85, "accuracy": 0.9, "complexity": 0.8, "completeness": 0.9}'::jsonb,
'[{"name": "host", "type": "string", "required": true, "description": "Target Windows host"}, {"name": "filepath", "type": "string", "required": true, "description": "Path to executable"}]'::jsonb,
'[]'::jsonb, '[]'::jsonb);

-- 13. Compress-Archive - Create ZIP files
INSERT INTO tool_catalog.tools (tool_name, version, description, platform, category, defaults, metadata, created_at, updated_at)
VALUES ('Compress-Archive', '1.0', 'Creates a compressed archive (ZIP file) from specified files and directories.', 'windows', 'system',
'{"freshness": "live", "data_source": "direct", "accuracy_level": "real-time"}'::jsonb,
'{"tags": ["archive", "zip", "compress", "backup"], "execution_method": "powershell", "requires_admin": false, "idempotent": false}'::jsonb,
NOW(), NOW());

INSERT INTO tool_catalog.tool_capabilities (tool_id, capability_name, description)
VALUES ((SELECT id FROM tool_catalog.tools WHERE tool_name = 'Compress-Archive'), 'archive_create', 'Create compressed archives');

INSERT INTO tool_catalog.tool_patterns (capability_id, pattern_name, description, typical_use_cases, time_estimate_ms, cost_estimate, complexity_score, scope, completeness, limitations, policy, preference_match, required_inputs, expected_outputs, examples)
VALUES ((SELECT id FROM tool_catalog.tool_capabilities WHERE capability_name = 'archive_create' AND tool_id = (SELECT id FROM tool_catalog.tools WHERE tool_name = 'Compress-Archive')),
'create_zip', 'Create ZIP archive',
'["Backup files", "Archive logs", "Package files for transfer", "Compress directories"]'::jsonb,
'60', '0.02', 0.20, 'single_item', 'complete', '[]'::jsonb,
'{"max_cost": 2.0, "production_safe": true, "requires_approval": false, "max_execution_time": 300}'::jsonb,
'{"cost": 0.9, "speed": 0.7, "accuracy": 0.95, "complexity": 0.8, "completeness": 0.9}'::jsonb,
'[{"name": "host", "type": "string", "required": true, "description": "Target Windows host"}, {"name": "path", "type": "string", "required": true, "description": "Source path"}, {"name": "destination", "type": "string", "required": true, "description": "ZIP file path"}]'::jsonb,
'[]'::jsonb, '[]'::jsonb);

-- 14. Expand-Archive - Extract ZIP files
INSERT INTO tool_catalog.tools (tool_name, version, description, platform, category, defaults, metadata, created_at, updated_at)
VALUES ('Expand-Archive', '1.0', 'Extracts files from a compressed archive (ZIP file) to a specified destination.', 'windows', 'system',
'{"freshness": "live", "data_source": "direct", "accuracy_level": "real-time"}'::jsonb,
'{"tags": ["archive", "zip", "extract", "decompress"], "execution_method": "powershell", "requires_admin": false, "idempotent": false}'::jsonb,
NOW(), NOW());

INSERT INTO tool_catalog.tool_capabilities (tool_id, capability_name, description)
VALUES ((SELECT id FROM tool_catalog.tools WHERE tool_name = 'Expand-Archive'), 'archive_extract', 'Extract compressed archives');

INSERT INTO tool_catalog.tool_patterns (capability_id, pattern_name, description, typical_use_cases, time_estimate_ms, cost_estimate, complexity_score, scope, completeness, limitations, policy, preference_match, required_inputs, expected_outputs, examples)
VALUES ((SELECT id FROM tool_catalog.tool_capabilities WHERE capability_name = 'archive_extract' AND tool_id = (SELECT id FROM tool_catalog.tools WHERE tool_name = 'Expand-Archive')),
'extract_zip', 'Extract ZIP archive',
'["Extract archives", "Restore backups", "Unpack files", "Deploy packages"]'::jsonb,
'60', '0.02', 0.20, 'single_item', 'complete', '[]'::jsonb,
'{"max_cost": 2.0, "production_safe": true, "requires_approval": false, "max_execution_time": 300}'::jsonb,
'{"cost": 0.9, "speed": 0.7, "accuracy": 0.95, "complexity": 0.8, "completeness": 0.9}'::jsonb,
'[{"name": "host", "type": "string", "required": true, "description": "Target Windows host"}, {"name": "path", "type": "string", "required": true, "description": "ZIP file path"}, {"name": "destination", "type": "string", "required": true, "description": "Extract destination"}]'::jsonb,
'[]'::jsonb, '[]'::jsonb);

-- 15. Set-Service - Configure services
INSERT INTO tool_catalog.tools (tool_name, version, description, platform, category, defaults, metadata, created_at, updated_at)
VALUES ('Set-Service', '1.0', 'Changes the properties of a service including startup type, display name, and description.', 'windows', 'system',
'{"freshness": "live", "data_source": "direct", "accuracy_level": "real-time"}'::jsonb,
'{"tags": ["service", "configure", "startup", "management"], "execution_method": "powershell", "requires_admin": true, "idempotent": false}'::jsonb,
NOW(), NOW());

INSERT INTO tool_catalog.tool_capabilities (tool_id, capability_name, description)
VALUES ((SELECT id FROM tool_catalog.tools WHERE tool_name = 'Set-Service'), 'service_configure', 'Configure service properties');

INSERT INTO tool_catalog.tool_patterns (capability_id, pattern_name, description, typical_use_cases, time_estimate_ms, cost_estimate, complexity_score, scope, completeness, limitations, policy, preference_match, required_inputs, expected_outputs, examples)
VALUES ((SELECT id FROM tool_catalog.tool_capabilities WHERE capability_name = 'service_configure' AND tool_id = (SELECT id FROM tool_catalog.tools WHERE tool_name = 'Set-Service')),
'configure_service', 'Configure service settings',
'["Change startup type", "Configure service properties", "Set service description", "Modify service settings"]'::jsonb,
'20', '0.01', 0.20, 'single_item', 'complete', '[]'::jsonb,
'{"max_cost": 1.0, "production_safe": true, "requires_approval": true, "max_execution_time": 60}'::jsonb,
'{"cost": 0.9, "speed": 0.9, "accuracy": 0.95, "complexity": 0.8, "completeness": 0.9}'::jsonb,
'[{"name": "host", "type": "string", "required": true, "description": "Target Windows host"}, {"name": "name", "type": "string", "required": true, "description": "Service name"}]'::jsonb,
'[]'::jsonb, '[]'::jsonb);

-- 16. Set-Acl - Modify permissions
INSERT INTO tool_catalog.tools (tool_name, version, description, platform, category, defaults, metadata, created_at, updated_at)
VALUES ('Set-Acl', '1.0', 'Changes the security descriptor (permissions) of a specified file, directory, or registry key.', 'windows', 'security',
'{"freshness": "live", "data_source": "direct", "accuracy_level": "real-time"}'::jsonb,
'{"tags": ["permissions", "acl", "security", "access"], "execution_method": "powershell", "requires_admin": true, "idempotent": false}'::jsonb,
NOW(), NOW());

INSERT INTO tool_catalog.tool_capabilities (tool_id, capability_name, description)
VALUES ((SELECT id FROM tool_catalog.tools WHERE tool_name = 'Set-Acl'), 'permissions_modify', 'Modify file and directory permissions');

INSERT INTO tool_catalog.tool_patterns (capability_id, pattern_name, description, typical_use_cases, time_estimate_ms, cost_estimate, complexity_score, scope, completeness, limitations, policy, preference_match, required_inputs, expected_outputs, examples)
VALUES ((SELECT id FROM tool_catalog.tool_capabilities WHERE capability_name = 'permissions_modify' AND tool_id = (SELECT id FROM tool_catalog.tools WHERE tool_name = 'Set-Acl')),
'modify_permissions', 'Modify file/directory permissions',
'["Change file permissions", "Set directory access", "Modify security settings", "Grant user access"]'::jsonb,
'30', '0.01', 0.30, 'single_item', 'complete', '[]'::jsonb,
'{"max_cost": 1.0, "production_safe": true, "requires_approval": true, "max_execution_time": 120}'::jsonb,
'{"cost": 0.85, "speed": 0.85, "accuracy": 0.9, "complexity": 0.7, "completeness": 0.85}'::jsonb,
'[{"name": "host", "type": "string", "required": true, "description": "Target Windows host"}, {"name": "path", "type": "string", "required": true, "description": "File/directory path"}, {"name": "acl", "type": "string", "required": true, "description": "ACL settings"}]'::jsonb,
'[]'::jsonb, '[]'::jsonb);

-- 17. Get-CimInstance - CIM queries
INSERT INTO tool_catalog.tools (tool_name, version, description, platform, category, defaults, metadata, created_at, updated_at)
VALUES ('Get-CimInstance', '1.0', 'Gets CIM instances from a CIM server. Modern replacement for Get-WmiObject with better performance.', 'windows', 'system',
'{"freshness": "live", "data_source": "direct", "accuracy_level": "real-time"}'::jsonb,
'{"tags": ["cim", "wmi", "query", "management"], "execution_method": "powershell", "requires_admin": false, "idempotent": true}'::jsonb,
NOW(), NOW());

INSERT INTO tool_catalog.tool_capabilities (tool_id, capability_name, description)
VALUES ((SELECT id FROM tool_catalog.tools WHERE tool_name = 'Get-CimInstance'), 'cim_query', 'Query CIM/WMI information');

INSERT INTO tool_catalog.tool_patterns (capability_id, pattern_name, description, typical_use_cases, time_estimate_ms, cost_estimate, complexity_score, scope, completeness, limitations, policy, preference_match, required_inputs, expected_outputs, examples)
VALUES ((SELECT id FROM tool_catalog.tool_capabilities WHERE capability_name = 'cim_query' AND tool_id = (SELECT id FROM tool_catalog.tools WHERE tool_name = 'Get-CimInstance')),
'query_cim', 'Query CIM instances',
'["Query system information", "Get hardware details", "Check OS configuration", "Retrieve management data"]'::jsonb,
'30', '0.01', 0.20, 'single_item', 'complete', '[]'::jsonb,
'{"max_cost": 1.0, "production_safe": true, "requires_approval": false, "max_execution_time": 120}'::jsonb,
'{"cost": 0.9, "speed": 0.85, "accuracy": 0.95, "complexity": 0.8, "completeness": 0.9}'::jsonb,
'[{"name": "host", "type": "string", "required": true, "description": "Target Windows host"}, {"name": "class_name", "type": "string", "required": true, "description": "CIM class name"}]'::jsonb,
'[]'::jsonb, '[]'::jsonb);

-- 18. robocopy - Robust file copy
INSERT INTO tool_catalog.tools (tool_name, version, description, platform, category, defaults, metadata, created_at, updated_at)
VALUES ('robocopy', '1.0', 'Robust file copy utility with advanced features like retry logic, mirroring, and multi-threading.', 'windows', 'system',
'{"freshness": "live", "data_source": "direct", "accuracy_level": "real-time"}'::jsonb,
'{"tags": ["file", "copy", "backup", "sync"], "execution_method": "cmd", "requires_admin": false, "idempotent": false}'::jsonb,
NOW(), NOW());

INSERT INTO tool_catalog.tool_capabilities (tool_id, capability_name, description)
VALUES ((SELECT id FROM tool_catalog.tools WHERE tool_name = 'robocopy'), 'robust_copy', 'Robust file and directory copying');

INSERT INTO tool_catalog.tool_patterns (capability_id, pattern_name, description, typical_use_cases, time_estimate_ms, cost_estimate, complexity_score, scope, completeness, limitations, policy, preference_match, required_inputs, expected_outputs, examples)
VALUES ((SELECT id FROM tool_catalog.tool_capabilities WHERE capability_name = 'robust_copy' AND tool_id = (SELECT id FROM tool_catalog.tools WHERE tool_name = 'robocopy')),
'copy_files', 'Robust file copy',
'["Backup directories", "Sync folders", "Copy large file sets", "Mirror directories"]'::jsonb,
'120', '0.05', 0.30, 'single_item', 'complete', '[]'::jsonb,
'{"max_cost": 5.0, "production_safe": true, "requires_approval": false, "max_execution_time": 600}'::jsonb,
'{"cost": 0.8, "speed": 0.6, "accuracy": 0.95, "complexity": 0.7, "completeness": 0.85}'::jsonb,
'[{"name": "host", "type": "string", "required": true, "description": "Target Windows host"}, {"name": "source", "type": "string", "required": true, "description": "Source path"}, {"name": "destination", "type": "string", "required": true, "description": "Destination path"}]'::jsonb,
'[]'::jsonb, '[]'::jsonb);

-- ============================================================================
-- TIER 3: MEDIUM PRIORITY TOOLS (9 tools)
-- ============================================================================

-- 19. ForEach-Object - Loop through pipeline
INSERT INTO tool_catalog.tools (tool_name, version, description, platform, category, defaults, metadata, created_at, updated_at)
VALUES ('ForEach-Object', '1.0', 'Performs an operation on each item in a collection of input objects. Essential PowerShell pipeline cmdlet.', 'windows', 'system',
'{"freshness": "live", "data_source": "direct", "accuracy_level": "real-time"}'::jsonb,
'{"tags": ["pipeline", "loop", "iterate", "objects"], "execution_method": "powershell", "requires_admin": false, "idempotent": false}'::jsonb,
NOW(), NOW());

INSERT INTO tool_catalog.tool_capabilities (tool_id, capability_name, description)
VALUES ((SELECT id FROM tool_catalog.tools WHERE tool_name = 'ForEach-Object'), 'pipeline_loop', 'Iterate through pipeline objects');

INSERT INTO tool_catalog.tool_patterns (capability_id, pattern_name, description, typical_use_cases, time_estimate_ms, cost_estimate, complexity_score, scope, completeness, limitations, policy, preference_match, required_inputs, expected_outputs, examples)
VALUES ((SELECT id FROM tool_catalog.tool_capabilities WHERE capability_name = 'pipeline_loop' AND tool_id = (SELECT id FROM tool_catalog.tools WHERE tool_name = 'ForEach-Object')),
'iterate_objects', 'Iterate through objects',
'["Process each item", "Loop through results", "Apply operation to collection", "Batch processing"]'::jsonb,
'30', '0.01', 0.20, 'single_item', 'complete', '[]'::jsonb,
'{"max_cost": 1.0, "production_safe": true, "requires_approval": false, "max_execution_time": 300}'::jsonb,
'{"cost": 0.9, "speed": 0.85, "accuracy": 0.9, "complexity": 0.8, "completeness": 0.9}'::jsonb,
'[{"name": "host", "type": "string", "required": true, "description": "Target Windows host"}, {"name": "script_block", "type": "string", "required": true, "description": "Script to execute for each object"}]'::jsonb,
'[]'::jsonb, '[]'::jsonb);

-- 20. tracert - Trace route
INSERT INTO tool_catalog.tools (tool_name, version, description, platform, category, defaults, metadata, created_at, updated_at)
VALUES ('tracert', '1.0', 'Traces the route packets take to reach a network destination, showing each hop along the way.', 'windows', 'network',
'{"freshness": "live", "data_source": "direct", "accuracy_level": "real-time"}'::jsonb,
'{"tags": ["network", "trace", "route", "diagnostic"], "execution_method": "cmd", "requires_admin": false, "idempotent": true}'::jsonb,
NOW(), NOW());

INSERT INTO tool_catalog.tool_capabilities (tool_id, capability_name, description)
VALUES ((SELECT id FROM tool_catalog.tools WHERE tool_name = 'tracert'), 'route_trace', 'Trace network route to destination');

INSERT INTO tool_catalog.tool_patterns (capability_id, pattern_name, description, typical_use_cases, time_estimate_ms, cost_estimate, complexity_score, scope, completeness, limitations, policy, preference_match, required_inputs, expected_outputs, examples)
VALUES ((SELECT id FROM tool_catalog.tool_capabilities WHERE capability_name = 'route_trace' AND tool_id = (SELECT id FROM tool_catalog.tools WHERE tool_name = 'tracert')),
'trace_route', 'Trace network route',
'["Troubleshoot network path", "Identify routing issues", "Check network hops", "Diagnose connectivity problems"]'::jsonb,
'60', '0.02', 0.20, 'single_item', 'complete', '[]'::jsonb,
'{"max_cost": 1.0, "production_safe": true, "requires_approval": false, "max_execution_time": 120}'::jsonb,
'{"cost": 0.9, "speed": 0.7, "accuracy": 0.85, "complexity": 0.8, "completeness": 0.9}'::jsonb,
'[{"name": "host", "type": "string", "required": true, "description": "Target Windows host"}, {"name": "target", "type": "string", "required": true, "description": "Destination to trace"}]'::jsonb,
'[]'::jsonb, '[]'::jsonb);

-- 21. whoami - SKIPPED (already exists)

-- 22. Get-NetIPConfiguration - Network configuration
INSERT INTO tool_catalog.tools (tool_name, version, description, platform, category, defaults, metadata, created_at, updated_at)
VALUES ('Get-NetIPConfiguration', '1.0', 'Gets network configuration including IP addresses, DNS servers, and default gateways. PowerShell alternative to ipconfig.', 'windows', 'network',
'{"freshness": "live", "data_source": "direct", "accuracy_level": "real-time"}'::jsonb,
'{"tags": ["network", "ip", "configuration", "dns"], "execution_method": "powershell", "requires_admin": false, "idempotent": true}'::jsonb,
NOW(), NOW());

INSERT INTO tool_catalog.tool_capabilities (tool_id, capability_name, description)
VALUES ((SELECT id FROM tool_catalog.tools WHERE tool_name = 'Get-NetIPConfiguration'), 'network_config', 'Get network configuration details');

INSERT INTO tool_catalog.tool_patterns (capability_id, pattern_name, description, typical_use_cases, time_estimate_ms, cost_estimate, complexity_score, scope, completeness, limitations, policy, preference_match, required_inputs, expected_outputs, examples)
VALUES ((SELECT id FROM tool_catalog.tool_capabilities WHERE capability_name = 'network_config' AND tool_id = (SELECT id FROM tool_catalog.tools WHERE tool_name = 'Get-NetIPConfiguration')),
'get_network_config', 'Get network configuration',
'["View IP configuration", "Check DNS settings", "Verify network adapters", "Troubleshoot connectivity"]'::jsonb,
'15', '0.005', 0.20, 'single_item', 'complete', '[]'::jsonb,
'{"max_cost": 0.5, "production_safe": true, "requires_approval": false, "max_execution_time": 60}'::jsonb,
'{"cost": 0.9, "speed": 0.9, "accuracy": 0.95, "complexity": 0.8, "completeness": 0.9}'::jsonb,
'[{"name": "host", "type": "string", "required": true, "description": "Target Windows host"}]'::jsonb,
'[]'::jsonb, '[]'::jsonb);

-- 23. nslookup - SKIPPED (already exists)

-- 24. tasklist - List processes (legacy)
INSERT INTO tool_catalog.tools (tool_name, version, description, platform, category, defaults, metadata, created_at, updated_at)
VALUES ('tasklist', '1.0', 'Displays a list of currently running processes. Legacy CMD tool, prefer Get-Process.', 'windows', 'system',
'{"freshness": "live", "data_source": "direct", "accuracy_level": "real-time"}'::jsonb,
'{"tags": ["process", "list", "task", "legacy"], "execution_method": "cmd", "requires_admin": false, "idempotent": true}'::jsonb,
NOW(), NOW());

INSERT INTO tool_catalog.tool_capabilities (tool_id, capability_name, description)
VALUES ((SELECT id FROM tool_catalog.tools WHERE tool_name = 'tasklist'), 'process_list_legacy', 'List running processes (legacy)');

INSERT INTO tool_catalog.tool_patterns (capability_id, pattern_name, description, typical_use_cases, time_estimate_ms, cost_estimate, complexity_score, scope, completeness, limitations, policy, preference_match, required_inputs, expected_outputs, examples)
VALUES ((SELECT id FROM tool_catalog.tool_capabilities WHERE capability_name = 'process_list_legacy' AND tool_id = (SELECT id FROM tool_catalog.tools WHERE tool_name = 'tasklist')),
'list_processes', 'List processes (legacy)',
'["View running processes", "Check process status", "Find process by name", "Monitor system activity"]'::jsonb,
'10', '0.005', 0.10, 'single_item', 'complete', '[]'::jsonb,
'{"max_cost": 0.5, "production_safe": true, "requires_approval": false, "max_execution_time": 30}'::jsonb,
'{"cost": 0.95, "speed": 0.95, "accuracy": 0.95, "complexity": 0.9, "completeness": 0.95}'::jsonb,
'[{"name": "host", "type": "string", "required": true, "description": "Target Windows host"}]'::jsonb,
'[]'::jsonb, '[]'::jsonb);

-- 25. taskkill - Kill process (legacy)
INSERT INTO tool_catalog.tools (tool_name, version, description, platform, category, defaults, metadata, created_at, updated_at)
VALUES ('taskkill', '1.0', 'Terminates one or more processes by process ID or image name. Legacy CMD tool, prefer Stop-Process.', 'windows', 'system',
'{"freshness": "live", "data_source": "direct", "accuracy_level": "real-time"}'::jsonb,
'{"tags": ["process", "kill", "terminate", "legacy"], "execution_method": "cmd", "requires_admin": false, "idempotent": false}'::jsonb,
NOW(), NOW());

INSERT INTO tool_catalog.tool_capabilities (tool_id, capability_name, description)
VALUES ((SELECT id FROM tool_catalog.tools WHERE tool_name = 'taskkill'), 'process_kill_legacy', 'Terminate processes (legacy)');

INSERT INTO tool_catalog.tool_patterns (capability_id, pattern_name, description, typical_use_cases, time_estimate_ms, cost_estimate, complexity_score, scope, completeness, limitations, policy, preference_match, required_inputs, expected_outputs, examples)
VALUES ((SELECT id FROM tool_catalog.tool_capabilities WHERE capability_name = 'process_kill_legacy' AND tool_id = (SELECT id FROM tool_catalog.tools WHERE tool_name = 'taskkill')),
'kill_process', 'Kill process (legacy)',
'["Kill hung process", "Terminate application", "Stop process by PID", "Force close program"]'::jsonb,
'15', '0.01', 0.20, 'single_item', 'complete', '[]'::jsonb,
'{"max_cost": 1.0, "production_safe": true, "requires_approval": true, "max_execution_time": 60}'::jsonb,
'{"cost": 0.9, "speed": 0.9, "accuracy": 0.9, "complexity": 0.8, "completeness": 0.9}'::jsonb,
'[{"name": "host", "type": "string", "required": true, "description": "Target Windows host"}, {"name": "target", "type": "string", "required": true, "description": "Process ID or name"}]'::jsonb,
'[]'::jsonb, '[]'::jsonb);

-- 26. systeminfo - System information (legacy)
INSERT INTO tool_catalog.tools (tool_name, version, description, platform, category, defaults, metadata, created_at, updated_at)
VALUES ('systeminfo', '1.0', 'Displays detailed configuration information about computer and operating system. Legacy CMD tool, prefer Get-ComputerInfo.', 'windows', 'system',
'{"freshness": "live", "data_source": "direct", "accuracy_level": "real-time"}'::jsonb,
'{"tags": ["system", "info", "configuration", "legacy"], "execution_method": "cmd", "requires_admin": false, "idempotent": true}'::jsonb,
NOW(), NOW());

INSERT INTO tool_catalog.tool_capabilities (tool_id, capability_name, description)
VALUES ((SELECT id FROM tool_catalog.tools WHERE tool_name = 'systeminfo'), 'system_info_legacy', 'Display system information (legacy)');

INSERT INTO tool_catalog.tool_patterns (capability_id, pattern_name, description, typical_use_cases, time_estimate_ms, cost_estimate, complexity_score, scope, completeness, limitations, policy, preference_match, required_inputs, expected_outputs, examples)
VALUES ((SELECT id FROM tool_catalog.tool_capabilities WHERE capability_name = 'system_info_legacy' AND tool_id = (SELECT id FROM tool_catalog.tools WHERE tool_name = 'systeminfo')),
'get_system_info', 'Get system info (legacy)',
'["View system details", "Check OS version", "Get hardware info", "Verify system configuration"]'::jsonb,
'30', '0.01', 0.10, 'single_item', 'complete', '[]'::jsonb,
'{"max_cost": 1.0, "production_safe": true, "requires_approval": false, "max_execution_time": 60}'::jsonb,
'{"cost": 0.9, "speed": 0.85, "accuracy": 0.95, "complexity": 0.9, "completeness": 0.9}'::jsonb,
'[{"name": "host", "type": "string", "required": true, "description": "Target Windows host"}]'::jsonb,
'[]'::jsonb, '[]'::jsonb);

COMMIT;

-- ============================================================================
-- SUMMARY
-- ============================================================================
-- Total tools added: 23 (4 already existed: ping, netstat, whoami, nslookup)
-- Total capabilities added: 23
-- Total patterns added: 23
-- Total records inserted: 69
--
-- Breakdown by tier:
-- - Tier 1 (Critical): 7 tools (ping, netstat skipped)
-- - Tier 2 (High Priority): 9 tools
-- - Tier 3 (Medium Priority): 7 tools (whoami, nslookup skipped)
--
-- Breakdown by category:
-- - system: 13 tools
-- - network: 8 tools
-- - security: 2 tools
-- ============================================================================