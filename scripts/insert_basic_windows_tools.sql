-- Insert basic Windows tools that were missing

-- Get-Content (Read file contents)
INSERT INTO tool_catalog.tools (tool_name, version, description, platform, category, defaults, metadata, created_at, updated_at)
VALUES ('Get-Content', '1.0', 'Reads the content of a file on a Windows system', 'windows', 'system',
'{"freshness": "live", "data_source": "direct", "accuracy_level": "real-time"}'::jsonb,
'{"tags": ["windows", "filesystem", "file", "read", "cat", "type"], "author": "OpsConductor Team", "created": "2025-10-16", "updated": "2025-10-16"}'::jsonb,
NOW(), NOW());

INSERT INTO tool_catalog.tool_capabilities (tool_id, capability_name, description)
VALUES ((SELECT id FROM tool_catalog.tools WHERE tool_name = 'Get-Content'), 'file_reading', 'Read and display file contents');

INSERT INTO tool_catalog.tool_patterns (capability_id, pattern_name, description, typical_use_cases, time_estimate_ms, cost_estimate, complexity_score, scope, completeness, limitations, policy, preference_match, required_inputs, expected_outputs, examples)
VALUES ((SELECT id FROM tool_catalog.tool_capabilities WHERE capability_name = 'file_reading' AND tool_id = (SELECT id FROM tool_catalog.tools WHERE tool_name = 'Get-Content')),
'read_file', 'Read file contents, view file, display file',
'["read file contents", "view file", "display file", "cat file", "type file", "show file contents", "get file text"]'::jsonb,
'500', '1', 0.10, 'single_item', 'complete', '[]'::jsonb,
'{"max_cost": 10, "production_safe": true, "requires_approval": false, "max_execution_time": 60}'::jsonb,
'{"cost": 0.9, "speed": 0.9, "accuracy": 0.9, "complexity": 0.9, "completeness": 0.9}'::jsonb,
'[{"name": "host", "type": "string", "required": true, "validation": ".*", "description": "Target Windows host IP or hostname"}, {"name": "path", "type": "string", "required": true, "validation": ".*", "description": "Full path to the file to read"}]'::jsonb,
'[]'::jsonb, '[]'::jsonb);

-- Copy-Item (Copy files/folders)
INSERT INTO tool_catalog.tools (tool_name, version, description, platform, category, defaults, metadata, created_at, updated_at)
VALUES ('Copy-Item', '1.0', 'Copies files or directories on a Windows system', 'windows', 'system',
'{"freshness": "live", "data_source": "direct", "accuracy_level": "real-time"}'::jsonb,
'{"tags": ["windows", "filesystem", "copy", "cp", "duplicate"], "author": "OpsConductor Team", "created": "2025-10-16", "updated": "2025-10-16"}'::jsonb,
NOW(), NOW());

INSERT INTO tool_catalog.tool_capabilities (tool_id, capability_name, description)
VALUES ((SELECT id FROM tool_catalog.tools WHERE tool_name = 'Copy-Item'), 'file_copy', 'Copy files and directories');

INSERT INTO tool_catalog.tool_patterns (capability_id, pattern_name, description, typical_use_cases, time_estimate_ms, cost_estimate, complexity_score, scope, completeness, limitations, policy, preference_match, required_inputs, expected_outputs, examples)
VALUES ((SELECT id FROM tool_catalog.tool_capabilities WHERE capability_name = 'file_copy' AND tool_id = (SELECT id FROM tool_catalog.tools WHERE tool_name = 'Copy-Item')),
'copy_file', 'Copy file or folder',
'["copy file", "copy folder", "copy directory", "duplicate file", "cp command", "backup file"]'::jsonb,
'1000', '2', 0.20, 'single_item', 'complete', '[]'::jsonb,
'{"max_cost": 20, "production_safe": false, "requires_approval": true, "max_execution_time": 300}'::jsonb,
'{"cost": 0.8, "speed": 0.7, "accuracy": 0.9, "complexity": 0.8, "completeness": 0.9}'::jsonb,
'[{"name": "host", "type": "string", "required": true, "validation": ".*", "description": "Target Windows host IP or hostname"}, {"name": "source", "type": "string", "required": true, "validation": ".*", "description": "Source path to copy from"}, {"name": "destination", "type": "string", "required": true, "validation": ".*", "description": "Destination path to copy to"}]'::jsonb,
'[]'::jsonb, '[]'::jsonb);

-- Remove-Item (Delete files/folders)
INSERT INTO tool_catalog.tools (tool_name, version, description, platform, category, defaults, metadata, created_at, updated_at)
VALUES ('Remove-Item', '1.0', 'Deletes files or directories on a Windows system', 'windows', 'system',
'{"freshness": "live", "data_source": "direct", "accuracy_level": "real-time"}'::jsonb,
'{"tags": ["windows", "filesystem", "delete", "remove", "rm", "del"], "author": "OpsConductor Team", "created": "2025-10-16", "updated": "2025-10-16"}'::jsonb,
NOW(), NOW());

INSERT INTO tool_catalog.tool_capabilities (tool_id, capability_name, description)
VALUES ((SELECT id FROM tool_catalog.tools WHERE tool_name = 'Remove-Item'), 'file_deletion', 'Delete files and directories');

INSERT INTO tool_catalog.tool_patterns (capability_id, pattern_name, description, typical_use_cases, time_estimate_ms, cost_estimate, complexity_score, scope, completeness, limitations, policy, preference_match, required_inputs, expected_outputs, examples)
VALUES ((SELECT id FROM tool_catalog.tool_capabilities WHERE capability_name = 'file_deletion' AND tool_id = (SELECT id FROM tool_catalog.tools WHERE tool_name = 'Remove-Item')),
'delete_file', 'Delete file or folder',
'["delete file", "remove file", "delete folder", "remove directory", "del command", "rm command", "erase file"]'::jsonb,
'500', '2', 0.30, 'single_item', 'complete', '["Cannot recover deleted files"]'::jsonb,
'{"max_cost": 20, "production_safe": false, "requires_approval": true, "max_execution_time": 300}'::jsonb,
'{"cost": 0.9, "speed": 0.9, "accuracy": 0.9, "complexity": 0.7, "completeness": 0.9}'::jsonb,
'[{"name": "host", "type": "string", "required": true, "validation": ".*", "description": "Target Windows host IP or hostname"}, {"name": "path", "type": "string", "required": true, "validation": ".*", "description": "Path to the file or directory to delete"}]'::jsonb,
'[]'::jsonb, '[]'::jsonb);

-- Move-Item (Move/rename files/folders)
INSERT INTO tool_catalog.tools (tool_name, version, description, platform, category, defaults, metadata, created_at, updated_at)
VALUES ('Move-Item', '1.0', 'Moves or renames files or directories on a Windows system', 'windows', 'system',
'{"freshness": "live", "data_source": "direct", "accuracy_level": "real-time"}'::jsonb,
'{"tags": ["windows", "filesystem", "move", "rename", "mv"], "author": "OpsConductor Team", "created": "2025-10-16", "updated": "2025-10-16"}'::jsonb,
NOW(), NOW());

INSERT INTO tool_catalog.tool_capabilities (tool_id, capability_name, description)
VALUES ((SELECT id FROM tool_catalog.tools WHERE tool_name = 'Move-Item'), 'file_move', 'Move or rename files and directories');

INSERT INTO tool_catalog.tool_patterns (capability_id, pattern_name, description, typical_use_cases, time_estimate_ms, cost_estimate, complexity_score, scope, completeness, limitations, policy, preference_match, required_inputs, expected_outputs, examples)
VALUES ((SELECT id FROM tool_catalog.tool_capabilities WHERE capability_name = 'file_move' AND tool_id = (SELECT id FROM tool_catalog.tools WHERE tool_name = 'Move-Item')),
'move_file', 'Move or rename file/folder',
'["move file", "rename file", "move folder", "rename directory", "mv command", "relocate file"]'::jsonb,
'800', '2', 0.20, 'single_item', 'complete', '[]'::jsonb,
'{"max_cost": 20, "production_safe": false, "requires_approval": true, "max_execution_time": 300}'::jsonb,
'{"cost": 0.8, "speed": 0.8, "accuracy": 0.9, "complexity": 0.8, "completeness": 0.9}'::jsonb,
'[{"name": "host", "type": "string", "required": true, "validation": ".*", "description": "Target Windows host IP or hostname"}, {"name": "source", "type": "string", "required": true, "validation": ".*", "description": "Source path to move from"}, {"name": "destination", "type": "string", "required": true, "validation": ".*", "description": "Destination path to move to"}]'::jsonb,
'[]'::jsonb, '[]'::jsonb);

-- New-Item (Create files/folders)
INSERT INTO tool_catalog.tools (tool_name, version, description, platform, category, defaults, metadata, created_at, updated_at)
VALUES ('New-Item', '1.0', 'Creates new files or directories on a Windows system', 'windows', 'system',
'{"freshness": "live", "data_source": "direct", "accuracy_level": "real-time"}'::jsonb,
'{"tags": ["windows", "filesystem", "create", "mkdir", "touch", "new"], "author": "OpsConductor Team", "created": "2025-10-16", "updated": "2025-10-16"}'::jsonb,
NOW(), NOW());

INSERT INTO tool_catalog.tool_capabilities (tool_id, capability_name, description)
VALUES ((SELECT id FROM tool_catalog.tools WHERE tool_name = 'New-Item'), 'file_creation', 'Create new files and directories');

INSERT INTO tool_catalog.tool_patterns (capability_id, pattern_name, description, typical_use_cases, time_estimate_ms, cost_estimate, complexity_score, scope, completeness, limitations, policy, preference_match, required_inputs, expected_outputs, examples)
VALUES ((SELECT id FROM tool_catalog.tool_capabilities WHERE capability_name = 'file_creation' AND tool_id = (SELECT id FROM tool_catalog.tools WHERE tool_name = 'New-Item')),
'create_file', 'Create new file or folder',
'["create file", "create folder", "create directory", "new file", "mkdir command", "touch command", "make directory"]'::jsonb,
'500', '1', 0.15, 'single_item', 'complete', '[]'::jsonb,
'{"max_cost": 10, "production_safe": false, "requires_approval": true, "max_execution_time": 60}'::jsonb,
'{"cost": 0.9, "speed": 0.9, "accuracy": 0.9, "complexity": 0.8, "completeness": 0.9}'::jsonb,
'[{"name": "host", "type": "string", "required": true, "validation": ".*", "description": "Target Windows host IP or hostname"}, {"name": "path", "type": "string", "required": true, "validation": ".*", "description": "Path where the item should be created"}, {"name": "item_type", "type": "string", "required": true, "validation": "^(File|Directory)$", "description": "Type of item to create (File or Directory)"}]'::jsonb,
'[]'::jsonb, '[]'::jsonb);

-- Select-String (Search text in files)
INSERT INTO tool_catalog.tools (tool_name, version, description, platform, category, defaults, metadata, created_at, updated_at)
VALUES ('Select-String', '1.0', 'Searches for text patterns in files on a Windows system', 'windows', 'system',
'{"freshness": "live", "data_source": "direct", "accuracy_level": "real-time"}'::jsonb,
'{"tags": ["windows", "filesystem", "search", "grep", "findstr", "text"], "author": "OpsConductor Team", "created": "2025-10-16", "updated": "2025-10-16"}'::jsonb,
NOW(), NOW());

INSERT INTO tool_catalog.tool_capabilities (tool_id, capability_name, description)
VALUES ((SELECT id FROM tool_catalog.tools WHERE tool_name = 'Select-String'), 'text_search', 'Search for text patterns in files');

INSERT INTO tool_catalog.tool_patterns (capability_id, pattern_name, description, typical_use_cases, time_estimate_ms, cost_estimate, complexity_score, scope, completeness, limitations, policy, preference_match, required_inputs, expected_outputs, examples)
VALUES ((SELECT id FROM tool_catalog.tool_capabilities WHERE capability_name = 'text_search' AND tool_id = (SELECT id FROM tool_catalog.tools WHERE tool_name = 'Select-String')),
'search_text', 'Search for text in files',
'["search text", "find string", "grep", "findstr", "search in file", "search pattern", "find text in file"]'::jsonb,
'1500', '3', 0.25, 'single_item', 'complete', '[]'::jsonb,
'{"max_cost": 15, "production_safe": true, "requires_approval": false, "max_execution_time": 120}'::jsonb,
'{"cost": 0.8, "speed": 0.7, "accuracy": 0.9, "complexity": 0.8, "completeness": 0.9}'::jsonb,
'[{"name": "host", "type": "string", "required": true, "validation": ".*", "description": "Target Windows host IP or hostname"}, {"name": "pattern", "type": "string", "required": true, "validation": ".*", "description": "Text pattern or regex to search for"}, {"name": "path", "type": "string", "required": true, "validation": ".*", "description": "File path or directory to search in"}]'::jsonb,
'[]'::jsonb, '[]'::jsonb);

-- Stop-Process (Kill processes)
INSERT INTO tool_catalog.tools (tool_name, version, description, platform, category, defaults, metadata, created_at, updated_at)
VALUES ('Stop-Process', '1.0', 'Stops one or more running processes on a Windows system', 'windows', 'system',
'{"freshness": "live", "data_source": "direct", "accuracy_level": "real-time"}'::jsonb,
'{"tags": ["windows", "process", "kill", "stop", "terminate", "taskkill"], "author": "OpsConductor Team", "created": "2025-10-16", "updated": "2025-10-16"}'::jsonb,
NOW(), NOW());

INSERT INTO tool_catalog.tool_capabilities (tool_id, capability_name, description)
VALUES ((SELECT id FROM tool_catalog.tools WHERE tool_name = 'Stop-Process'), 'process_termination', 'Stop or kill running processes');

INSERT INTO tool_catalog.tool_patterns (capability_id, pattern_name, description, typical_use_cases, time_estimate_ms, cost_estimate, complexity_score, scope, completeness, limitations, policy, preference_match, required_inputs, expected_outputs, examples)
VALUES ((SELECT id FROM tool_catalog.tool_capabilities WHERE capability_name = 'process_termination' AND tool_id = (SELECT id FROM tool_catalog.tools WHERE tool_name = 'Stop-Process')),
'kill_process', 'Stop or kill a process',
'["stop process", "kill process", "terminate process", "end process", "taskkill", "force stop process"]'::jsonb,
'500', '2', 0.25, 'single_item', 'complete', '["May cause data loss if process is not saved"]'::jsonb,
'{"max_cost": 15, "production_safe": false, "requires_approval": true, "max_execution_time": 60}'::jsonb,
'{"cost": 0.9, "speed": 0.9, "accuracy": 0.9, "complexity": 0.7, "completeness": 0.9}'::jsonb,
'[{"name": "host", "type": "string", "required": true, "validation": ".*", "description": "Target Windows host IP or hostname"}, {"name": "process_name", "type": "string", "required": false, "validation": ".*", "description": "Process name to stop"}, {"name": "process_id", "type": "integer", "required": false, "validation": ".*", "description": "Process ID to stop"}]'::jsonb,
'[]'::jsonb, '[]'::jsonb);

-- Start-Service (Start Windows services)
INSERT INTO tool_catalog.tools (tool_name, version, description, platform, category, defaults, metadata, created_at, updated_at)
VALUES ('Start-Service', '1.0', 'Starts a stopped Windows service', 'windows', 'system',
'{"freshness": "live", "data_source": "direct", "accuracy_level": "real-time"}'::jsonb,
'{"tags": ["windows", "service", "start", "enable"], "author": "OpsConductor Team", "created": "2025-10-16", "updated": "2025-10-16"}'::jsonb,
NOW(), NOW());

INSERT INTO tool_catalog.tool_capabilities (tool_id, capability_name, description)
VALUES ((SELECT id FROM tool_catalog.tools WHERE tool_name = 'Start-Service'), 'service_start', 'Start Windows services');

INSERT INTO tool_catalog.tool_patterns (capability_id, pattern_name, description, typical_use_cases, time_estimate_ms, cost_estimate, complexity_score, scope, completeness, limitations, policy, preference_match, required_inputs, expected_outputs, examples)
VALUES ((SELECT id FROM tool_catalog.tool_capabilities WHERE capability_name = 'service_start' AND tool_id = (SELECT id FROM tool_catalog.tools WHERE tool_name = 'Start-Service')),
'start_service', 'Start a Windows service',
'["start service", "enable service", "run service", "activate service"]'::jsonb,
'1000', '3', 0.30, 'single_item', 'complete', '[]'::jsonb,
'{"max_cost": 20, "production_safe": false, "requires_approval": true, "max_execution_time": 120}'::jsonb,
'{"cost": 0.8, "speed": 0.7, "accuracy": 0.9, "complexity": 0.7, "completeness": 0.9}'::jsonb,
'[{"name": "host", "type": "string", "required": true, "validation": ".*", "description": "Target Windows host IP or hostname"}, {"name": "service_name", "type": "string", "required": true, "validation": ".*", "description": "Name of the service to start"}]'::jsonb,
'[]'::jsonb, '[]'::jsonb);

-- Stop-Service (Stop Windows services)
INSERT INTO tool_catalog.tools (tool_name, version, description, platform, category, defaults, metadata, created_at, updated_at)
VALUES ('Stop-Service', '1.0', 'Stops a running Windows service', 'windows', 'system',
'{"freshness": "live", "data_source": "direct", "accuracy_level": "real-time"}'::jsonb,
'{"tags": ["windows", "service", "stop", "disable"], "author": "OpsConductor Team", "created": "2025-10-16", "updated": "2025-10-16"}'::jsonb,
NOW(), NOW());

INSERT INTO tool_catalog.tool_capabilities (tool_id, capability_name, description)
VALUES ((SELECT id FROM tool_catalog.tools WHERE tool_name = 'Stop-Service'), 'service_stop', 'Stop Windows services');

INSERT INTO tool_catalog.tool_patterns (capability_id, pattern_name, description, typical_use_cases, time_estimate_ms, cost_estimate, complexity_score, scope, completeness, limitations, policy, preference_match, required_inputs, expected_outputs, examples)
VALUES ((SELECT id FROM tool_catalog.tool_capabilities WHERE capability_name = 'service_stop' AND tool_id = (SELECT id FROM tool_catalog.tools WHERE tool_name = 'Stop-Service')),
'stop_service', 'Stop a Windows service',
'["stop service", "disable service", "halt service", "deactivate service"]'::jsonb,
'1000', '3', 0.30, 'single_item', 'complete', '["May affect dependent services"]'::jsonb,
'{"max_cost": 20, "production_safe": false, "requires_approval": true, "max_execution_time": 120}'::jsonb,
'{"cost": 0.8, "speed": 0.7, "accuracy": 0.9, "complexity": 0.7, "completeness": 0.9}'::jsonb,
'[{"name": "host", "type": "string", "required": true, "validation": ".*", "description": "Target Windows host IP or hostname"}, {"name": "service_name", "type": "string", "required": true, "validation": ".*", "description": "Name of the service to stop"}]'::jsonb,
'[]'::jsonb, '[]'::jsonb);

-- Restart-Service (Restart Windows services)
INSERT INTO tool_catalog.tools (tool_name, version, description, platform, category, defaults, metadata, created_at, updated_at)
VALUES ('Restart-Service', '1.0', 'Restarts a Windows service', 'windows', 'system',
'{"freshness": "live", "data_source": "direct", "accuracy_level": "real-time"}'::jsonb,
'{"tags": ["windows", "service", "restart", "reboot", "reload"], "author": "OpsConductor Team", "created": "2025-10-16", "updated": "2025-10-16"}'::jsonb,
NOW(), NOW());

INSERT INTO tool_catalog.tool_capabilities (tool_id, capability_name, description)
VALUES ((SELECT id FROM tool_catalog.tools WHERE tool_name = 'Restart-Service'), 'service_restart', 'Restart Windows services');

INSERT INTO tool_catalog.tool_patterns (capability_id, pattern_name, description, typical_use_cases, time_estimate_ms, cost_estimate, complexity_score, scope, completeness, limitations, policy, preference_match, required_inputs, expected_outputs, examples)
VALUES ((SELECT id FROM tool_catalog.tool_capabilities WHERE capability_name = 'service_restart' AND tool_id = (SELECT id FROM tool_catalog.tools WHERE tool_name = 'Restart-Service')),
'restart_service', 'Restart a Windows service',
'["restart service", "reboot service", "reload service", "cycle service"]'::jsonb,
'1500', '4', 0.35, 'single_item', 'complete', '["May cause brief service interruption"]'::jsonb,
'{"max_cost": 25, "production_safe": false, "requires_approval": true, "max_execution_time": 120}'::jsonb,
'{"cost": 0.7, "speed": 0.6, "accuracy": 0.9, "complexity": 0.7, "completeness": 0.9}'::jsonb,
'[{"name": "host", "type": "string", "required": true, "validation": ".*", "description": "Target Windows host IP or hostname"}, {"name": "service_name", "type": "string", "required": true, "validation": ".*", "description": "Name of the service to restart"}]'::jsonb,
'[]'::jsonb, '[]'::jsonb);

-- Get-Item (Get file/folder properties)
INSERT INTO tool_catalog.tools (tool_name, version, description, platform, category, defaults, metadata, created_at, updated_at)
VALUES ('Get-Item', '1.0', 'Gets file or directory properties on a Windows system', 'windows', 'system',
'{"freshness": "live", "data_source": "direct", "accuracy_level": "real-time"}'::jsonb,
'{"tags": ["windows", "filesystem", "properties", "stat", "info"], "author": "OpsConductor Team", "created": "2025-10-16", "updated": "2025-10-16"}'::jsonb,
NOW(), NOW());

INSERT INTO tool_catalog.tool_capabilities (tool_id, capability_name, description)
VALUES ((SELECT id FROM tool_catalog.tools WHERE tool_name = 'Get-Item'), 'item_properties', 'Get file and directory properties');

INSERT INTO tool_catalog.tool_patterns (capability_id, pattern_name, description, typical_use_cases, time_estimate_ms, cost_estimate, complexity_score, scope, completeness, limitations, policy, preference_match, required_inputs, expected_outputs, examples)
VALUES ((SELECT id FROM tool_catalog.tool_capabilities WHERE capability_name = 'item_properties' AND tool_id = (SELECT id FROM tool_catalog.tools WHERE tool_name = 'Get-Item')),
'get_properties', 'Get file or folder properties',
'["get file properties", "file info", "directory info", "stat command", "file details", "folder details"]'::jsonb,
'500', '1', 0.10, 'single_item', 'complete', '[]'::jsonb,
'{"max_cost": 10, "production_safe": true, "requires_approval": false, "max_execution_time": 60}'::jsonb,
'{"cost": 0.9, "speed": 0.9, "accuracy": 0.9, "complexity": 0.9, "completeness": 0.9}'::jsonb,
'[{"name": "host", "type": "string", "required": true, "validation": ".*", "description": "Target Windows host IP or hostname"}, {"name": "path", "type": "string", "required": true, "validation": ".*", "description": "Path to the file or directory"}]'::jsonb,
'[]'::jsonb, '[]'::jsonb);