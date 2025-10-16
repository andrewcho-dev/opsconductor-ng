-- ============================================================================
-- ENHANCE REMAINING 3 TOOLS
-- ============================================================================
-- Fix pattern names for Compress-Archive, Expand-Archive, Start-Process
-- ============================================================================

BEGIN;

-- 12. Start-Process - Launch processes
UPDATE tool_catalog.tool_patterns
SET 
  description = 'Start process, launch application, run program, execute command, start executable',
  typical_use_cases = '[
    "Launch applications",
    "Start programs",
    "Execute commands",
    "Run executables",
    "Start process with arguments",
    "Launch program as admin",
    "Run command line tools",
    "Execute batch files"
  ]'::jsonb,
  required_inputs = '[
    {
      "name": "host",
      "type": "string",
      "required": true,
      "validation": "^[a-zA-Z0-9.-]+$",
      "description": "Target Windows host IP address or hostname (e.g., ''server01'', ''192.168.1.100'')"
    },
    {
      "name": "file_path",
      "type": "string",
      "required": true,
      "validation": "^[a-zA-Z]:\\\\.*\\.exe$|^[a-zA-Z]:\\\\.*\\.bat$|^[a-zA-Z]:\\\\.*\\.cmd$",
      "description": "Full path to executable file (e.g., ''C:\\Program Files\\app\\program.exe'', ''C:\\scripts\\script.bat'')"
    }
  ]'::jsonb,
  examples = '[
    {
      "query": "Start notepad application",
      "inputs": {
        "host": "server01",
        "file_path": "C:\\Windows\\System32\\notepad.exe"
      },
      "expected_output": "Process started successfully"
    },
    {
      "query": "Run batch script",
      "inputs": {
        "host": "server01",
        "file_path": "C:\\scripts\\backup.bat"
      },
      "expected_output": "Batch script executed"
    }
  ]'::jsonb
WHERE pattern_name = 'launch_process'
  AND capability_id IN (
    SELECT id FROM tool_catalog.tool_capabilities 
    WHERE tool_id = (SELECT id FROM tool_catalog.tools WHERE tool_name = 'Start-Process')
  );

-- 13. Compress-Archive - Create ZIP files
UPDATE tool_catalog.tool_patterns
SET 
  description = 'Create ZIP archive, compress files, create compressed archive, zip files and folders, package directory',
  typical_use_cases = '[
    "Backup files",
    "Archive logs",
    "Package files for transfer",
    "Compress directories",
    "Create ZIP file",
    "Zip folder",
    "Compress multiple files",
    "Create backup archive",
    "Package application files",
    "Bundle files for download"
  ]'::jsonb,
  required_inputs = '[
    {
      "name": "host",
      "type": "string",
      "required": true,
      "validation": "^[a-zA-Z0-9.-]+$",
      "description": "Target Windows host IP address or hostname (e.g., ''server01'', ''192.168.1.100'')"
    },
    {
      "name": "path",
      "type": "string",
      "required": true,
      "validation": "^[a-zA-Z]:\\\\.*|^\\\\\\\\.*",
      "description": "Source file or directory path to compress (e.g., ''C:\\logs'', ''C:\\data\\*.txt'')"
    },
    {
      "name": "destination",
      "type": "string",
      "required": true,
      "validation": "^[a-zA-Z]:\\\\.*\\.zip$|^\\\\\\\\.*\\.zip$",
      "description": "Destination ZIP file path (must end with .zip, e.g., ''C:\\backups\\logs_2025-01-16.zip'')"
    }
  ]'::jsonb,
  examples = '[
    {
      "query": "Zip up the logs directory",
      "inputs": {
        "host": "server01",
        "path": "C:\\logs",
        "destination": "C:\\backups\\logs_backup.zip"
      },
      "expected_output": "ZIP archive created at C:\\backups\\logs_backup.zip"
    },
    {
      "query": "Create backup of application files",
      "inputs": {
        "host": "server01",
        "path": "C:\\app\\*",
        "destination": "C:\\backups\\app_backup_2025-01-16.zip"
      },
      "expected_output": "Application files compressed to C:\\backups\\app_backup_2025-01-16.zip"
    }
  ]'::jsonb
WHERE pattern_name = 'create_zip'
  AND capability_id IN (
    SELECT id FROM tool_catalog.tool_capabilities 
    WHERE tool_id = (SELECT id FROM tool_catalog.tools WHERE tool_name = 'Compress-Archive')
  );

-- 14. Expand-Archive - Extract ZIP files
UPDATE tool_catalog.tool_patterns
SET 
  description = 'Extract ZIP archive, unzip files, decompress archive, extract compressed files, unpack ZIP',
  typical_use_cases = '[
    "Extract ZIP files",
    "Unzip archives",
    "Decompress backups",
    "Extract downloaded files",
    "Unpack compressed data",
    "Restore from archive",
    "Extract specific files",
    "Unzip to directory"
  ]'::jsonb,
  required_inputs = '[
    {
      "name": "host",
      "type": "string",
      "required": true,
      "validation": "^[a-zA-Z0-9.-]+$",
      "description": "Target Windows host IP address or hostname (e.g., ''server01'', ''192.168.1.100'')"
    },
    {
      "name": "path",
      "type": "string",
      "required": true,
      "validation": "^[a-zA-Z]:\\\\.*\\.zip$|^\\\\\\\\.*\\.zip$",
      "description": "Source ZIP file path (must end with .zip, e.g., ''C:\\downloads\\archive.zip'')"
    },
    {
      "name": "destination",
      "type": "string",
      "required": true,
      "validation": "^[a-zA-Z]:\\\\.*|^\\\\\\\\.*",
      "description": "Destination directory path (e.g., ''C:\\extracted'', ''C:\\restore'')"
    }
  ]'::jsonb,
  examples = '[
    {
      "query": "Extract backup archive",
      "inputs": {
        "host": "server01",
        "path": "C:\\backups\\logs_backup.zip",
        "destination": "C:\\restore\\logs"
      },
      "expected_output": "Archive extracted to C:\\restore\\logs"
    },
    {
      "query": "Unzip downloaded file",
      "inputs": {
        "host": "server01",
        "path": "C:\\downloads\\package.zip",
        "destination": "C:\\temp\\extracted"
      },
      "expected_output": "Files extracted to C:\\temp\\extracted"
    }
  ]'::jsonb
WHERE pattern_name = 'extract_zip'
  AND capability_id IN (
    SELECT id FROM tool_catalog.tool_capabilities 
    WHERE tool_id = (SELECT id FROM tool_catalog.tools WHERE tool_name = 'Expand-Archive')
  );

COMMIT;

-- Display results
SELECT 
    t.tool_name,
    jsonb_array_length(tp.typical_use_cases) as use_cases,
    jsonb_array_length(tp.examples) as examples
FROM tool_catalog.tools t
JOIN tool_catalog.tool_capabilities tc ON tc.tool_id = t.id
JOIN tool_catalog.tool_patterns tp ON tp.capability_id = tc.id
WHERE t.tool_name IN ('Compress-Archive', 'Expand-Archive', 'Start-Process')
ORDER BY t.tool_name;