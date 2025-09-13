# OpsConductor RBAC System

## Overview

OpsConductor now implements a comprehensive Role-Based Access Control (RBAC) system that provides fine-grained permissions management across all services and frontend components.

## Architecture

### Database Schema

The RBAC system is built on three main tables:

1. **`identity.roles`** - Defines roles with their permissions
2. **`identity.user_roles`** - Maps users to roles
3. **`identity.users`** - Extended with role support

### Key Components

1. **Frontend Permission System** (`frontend/src/utils/permissions.ts`)
   - Centralized permission definitions
   - Permission checking utilities
   - Role-based UI rendering

2. **Backend RBAC Middleware** (`shared/rbac_middleware.py`)
   - Permission decorators for API endpoints
   - User context extraction from headers
   - Centralized permission validation

3. **API Gateway Integration**
   - Passes user information as headers to downstream services
   - Validates tokens and extracts user permissions
   - Ensures consistent authentication across services

## Permission System

### Permission Categories

- **User Management**: `users:read`, `users:create`, `users:update`, `users:delete`
- **Role Management**: `roles:read`, `roles:create`, `roles:update`, `roles:delete`
- **Job Management**: `jobs:read`, `jobs:create`, `jobs:update`, `jobs:delete`, `jobs:execute`
- **Target Management**: `targets:read`, `targets:create`, `targets:update`, `targets:delete`
- **Execution Monitoring**: `executions:read`
- **Step Libraries**: `step-libraries:read`, `step-libraries:create`, `step-libraries:update`, `step-libraries:delete`
- **Settings**: `settings:read`, `settings:update`, `smtp:config`
- **Notifications**: `notifications:read`, `notifications:create`, `notifications:update`, `notifications:delete`
- **System Administration**: `system:admin`

### Default Roles

1. **Admin** - Full access with wildcard permission (`*`)
2. **Operator** - Can execute jobs and view most resources
3. **Viewer** - Read-only access to basic resources

## Implementation Details

### Frontend

- **Permission Checks**: Components use `hasPermission(user, permission)` to conditionally render UI elements
- **Route Protection**: Pages check permissions and show access denied messages
- **Navigation**: Menu items are hidden/disabled based on user permissions
- **Role Management UI**: Admin users can create/edit roles and assign permissions

### Backend

- **Endpoint Protection**: API endpoints use decorators like `@require_permission(PERMISSIONS.USERS_READ)`
- **Header-based Authentication**: Services receive user context via HTTP headers
- **Consistent Validation**: All services use the same RBAC middleware

### API Gateway

- **Token Validation**: Validates JWT tokens with the identity service
- **User Context Propagation**: Adds user information to request headers:
  - `x-user-id`: User ID
  - `x-username`: Username
  - `x-user-email`: Email
  - `x-user-role`: User's role
  - `x-user-permissions`: Comma-separated list of permissions
  - `x-authenticated`: Boolean flag

## Usage Examples

### Frontend Permission Check
```typescript
import { hasPermission, PERMISSIONS } from '../utils/permissions';

// Hide create button for users without permission
{hasPermission(user, PERMISSIONS.USERS_CREATE) && (
  <button onClick={createUser}>Create User</button>
)}
```

### Backend Endpoint Protection
```python
from rbac_middleware import require_permission, PERMISSIONS

@app.post("/users")
@require_permission(PERMISSIONS.USERS_CREATE)
async def create_user(request: Request, user_data: UserCreate):
    # Only users with users:create permission can access this
    pass
```

### Role Management
```typescript
// Admin users can access role management
if (hasPermission(user, PERMISSIONS.ROLES_READ)) {
  // Show role management interface
}
```

## Migration Notes

The system includes a database migration (`database/rbac-migration.sql`) that:

1. Creates the roles and user_roles tables
2. Sets up default roles (admin, operator, viewer)
3. Assigns the admin role to existing admin users
4. Maintains backward compatibility with existing `is_admin` flags

## Security Features

1. **Principle of Least Privilege**: Users only get permissions they need
2. **Centralized Permission Management**: All permissions defined in one place
3. **Consistent Enforcement**: Same permission system across all services
4. **Audit Trail**: Role assignments are tracked with timestamps
5. **Token-based Authentication**: Secure JWT tokens with user context

## Administration

### Creating Roles
1. Navigate to Settings > Role Management (admin only)
2. Click "Create Role"
3. Define role name, description, and permissions
4. Assign role to users

### Managing Permissions
- Permissions are grouped by functionality for easy management
- Use "Select All" / "Clear All" for bulk permission assignment
- Role changes take effect immediately

### User Assignment
- Users can be assigned roles through the user management interface
- Multiple roles per user are supported (permissions are combined)
- Role changes are logged for audit purposes

## Troubleshooting

### Common Issues

1. **Access Denied Errors**: Check if user has required permissions
2. **Missing Permissions**: Verify role assignments and permission definitions
3. **Token Issues**: Ensure API gateway is properly forwarding user context

### Debugging

- Check browser network tab for permission-related headers
- Verify database role assignments in `identity.user_roles`
- Review service logs for RBAC middleware messages

## Future Enhancements

1. **Resource-level Permissions**: Permissions on specific resources (e.g., specific jobs)
2. **Time-based Permissions**: Temporary role assignments
3. **Permission Inheritance**: Hierarchical role structures
4. **Advanced Audit Logging**: Detailed permission usage tracking