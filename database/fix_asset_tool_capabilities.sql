-- Fix Asset Tool Capabilities
-- Replace generic 'primary_capability' with specific capability names

-- Update asset-query tool to have 'asset_query' capability
UPDATE tool_catalog.tool_capabilities
SET capability_name = 'asset_query',
    description = 'Query and retrieve asset information from the asset management system'
WHERE tool_id IN (SELECT id FROM tool_catalog.tools WHERE tool_name = 'asset-query')
  AND capability_name = 'primary_capability';

-- Update asset-list tool to have 'asset_query' and 'resource_listing' capabilities
UPDATE tool_catalog.tool_capabilities
SET capability_name = 'asset_query',
    description = 'List and enumerate assets from the asset management system'
WHERE tool_id IN (SELECT id FROM tool_catalog.tools WHERE tool_name = 'asset-list')
  AND capability_name = 'primary_capability';

-- Add resource_listing capability to asset-list
INSERT INTO tool_catalog.tool_capabilities (tool_id, capability_name, description, created_at)
SELECT id, 'resource_listing', 'List resources and assets', CURRENT_TIMESTAMP
FROM tool_catalog.tools
WHERE tool_name = 'asset-list'
  AND NOT EXISTS (
    SELECT 1 FROM tool_catalog.tool_capabilities tc
    WHERE tc.tool_id = tools.id AND tc.capability_name = 'resource_listing'
  );

-- Add infrastructure_info capability to asset-query and asset-list
INSERT INTO tool_catalog.tool_capabilities (tool_id, capability_name, description, created_at)
SELECT id, 'infrastructure_info', 'Retrieve infrastructure information', CURRENT_TIMESTAMP
FROM tool_catalog.tools
WHERE tool_name IN ('asset-query', 'asset-list')
  AND NOT EXISTS (
    SELECT 1 FROM tool_catalog.tool_capabilities tc
    WHERE tc.tool_id = tools.id AND tc.capability_name = 'infrastructure_info'
  );

-- Update asset-create tool to have 'asset_management' capability
UPDATE tool_catalog.tool_capabilities
SET capability_name = 'asset_management',
    description = 'Create and manage assets in the asset management system'
WHERE tool_id IN (SELECT id FROM tool_catalog.tools WHERE tool_name = 'asset-create')
  AND capability_name = 'primary_capability';

-- Update asset-update tool to have 'asset_management' capability
UPDATE tool_catalog.tool_capabilities
SET capability_name = 'asset_management',
    description = 'Update asset information in the asset management system'
WHERE tool_id IN (SELECT id FROM tool_catalog.tools WHERE tool_name = 'asset-update')
  AND capability_name = 'primary_capability';

-- Update asset-delete tool to have 'asset_management' capability
UPDATE tool_catalog.tool_capabilities
SET capability_name = 'asset_management',
    description = 'Delete assets from the asset management system'
WHERE tool_id IN (SELECT id FROM tool_catalog.tools WHERE tool_name = 'asset-delete')
  AND capability_name = 'primary_capability';

-- Verify the changes
SELECT t.tool_name, tc.capability_name, tc.description
FROM tool_catalog.tools t
JOIN tool_catalog.tool_capabilities tc ON t.id = tc.tool_id
WHERE t.tool_name LIKE '%asset%'
ORDER BY t.tool_name, tc.capability_name;