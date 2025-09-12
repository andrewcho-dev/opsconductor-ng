-- RBAC Migration Script
-- Adds missing fields and updates the roles table for comprehensive RBAC

-- Add is_active field to roles table if it doesn't exist
ALTER TABLE identity.roles ADD COLUMN IF NOT EXISTS is_active BOOLEAN DEFAULT true;

-- Update roles table to have comprehensive permissions
UPDATE identity.roles SET permissions = '["*"]' WHERE name = 'admin';
UPDATE identity.roles SET permissions = '[
  "jobs:read", "jobs:create", "jobs:update", "jobs:execute", "jobs:delete",
  "targets:read", "targets:create", "targets:update", "targets:delete",
  "executions:read", "step-libraries:read"
]' WHERE name = 'operator';
UPDATE identity.roles SET permissions = '[
  "jobs:read", "targets:read", "executions:read"
]' WHERE name = 'viewer';

-- Add more granular roles
INSERT INTO identity.roles (name, description, permissions, is_active) VALUES 
('manager', 'Team Manager', '[
  "jobs:read", "jobs:create", "jobs:update", "jobs:execute",
  "targets:read", "targets:create", "targets:update",
  "executions:read", "users:read", "step-libraries:read"
]', true),
('developer', 'Developer', '[
  "jobs:read", "jobs:create", "jobs:update", "jobs:execute",
  "targets:read", "executions:read", "step-libraries:read", "step-libraries:create", "step-libraries:update"
]', true)
ON CONFLICT (name) DO NOTHING;

-- Ensure all existing users have a role assigned
-- Users with is_admin=true get admin role, others get viewer role
INSERT INTO identity.user_roles (user_id, role_id, assigned_by)
SELECT u.id, r.id, 1
FROM identity.users u
CROSS JOIN identity.roles r
LEFT JOIN identity.user_roles ur ON u.id = ur.user_id AND r.id = ur.role_id
WHERE ur.user_id IS NULL
  AND ((u.is_admin = true AND r.name = 'admin') OR (u.is_admin = false AND r.name = 'viewer'));

COMMIT;