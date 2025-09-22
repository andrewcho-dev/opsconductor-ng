-- Network Analysis Permissions Migration
-- Adds network analysis permissions to existing roles

-- Update manager role to include network analysis permissions
UPDATE identity.roles SET permissions = '[
  "jobs:read", "jobs:create", "jobs:update", "jobs:execute",
  "targets:read", "targets:create", "targets:update",
  "executions:read", "users:read",
  "network:analysis:read", "network:monitoring:read"
]' WHERE name = 'manager';

-- Update operator role to include full network analysis permissions
UPDATE identity.roles SET permissions = '[
  "jobs:read", "jobs:create", "jobs:update", "jobs:execute", "jobs:delete",
  "targets:read", "targets:create", "targets:update", "targets:delete",
  "executions:read",
  "network:analysis:read", "network:analysis:write",
  "network:monitoring:read", "network:monitoring:write",
  "network:capture:start", "network:capture:stop"
]' WHERE name = 'operator';

-- Update developer role to include read-only network analysis permissions
UPDATE identity.roles SET permissions = '[
  "jobs:read", "jobs:create", "jobs:update", "jobs:execute",
  "targets:read", "executions:read",
  "network:analysis:read", "network:monitoring:read"
]' WHERE name = 'developer';

-- Viewer role remains read-only for basic resources only
-- (no network analysis permissions for security)

COMMIT;