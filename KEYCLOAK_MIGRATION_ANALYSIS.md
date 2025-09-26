# Keycloak Migration Analysis - OpsConductor Identity Service

## 🎯 **Migration Overview**

This document provides a comprehensive analysis of migrating from our custom Identity Service (1,100+ lines) to Keycloak enterprise identity management.

**Current Status:** Phase 2 - Ready to Begin Migration  
**Target:** Replace custom JWT/RBAC with enterprise-grade Keycloak  
**Timeline:** 3-4 weeks (Weeks 2-5 of V3 roadmap)

---

## 📊 **Current Identity Service Analysis**

### **Service Architecture**
- **File:** `/identity-service/main.py` (1,109 lines)
- **Port:** 3001
- **Database:** PostgreSQL `identity` schema
- **Authentication:** Custom JWT with HS256
- **Authorization:** Role-based permissions (RBAC)

### **API Endpoints (15 endpoints)**
```
Authentication:
├── POST /auth/login          → Login with username/password
├── GET  /auth/me            → Get current user info
└── GET  /auth/verify        → Verify token (alias for /auth/me)

User Management:
├── GET    /users            → List users (paginated)
├── POST   /users            → Create user
├── GET    /users/{id}       → Get user by ID
├── PUT    /users/{id}       → Update user
├── DELETE /users/{id}       → Delete user
├── POST   /users/{id}/roles → Assign role to user
└── GET    /users/{id}/roles → Get user roles

Role Management:
├── GET    /available-roles  → List available roles
├── GET    /roles           → List all roles
├── POST   /roles           → Create role
├── PUT    /roles/{id}      → Update role
└── DELETE /roles/{id}      → Delete role
```

### **Database Schema**
```sql
-- Current Tables (4 tables)
identity.users          → User accounts and profiles
identity.roles          → Role definitions with permissions
identity.user_roles     → User-role assignments (many-to-many)
identity.user_sessions  → Session management (unused)
identity.user_preferences → User preferences (unused)
```

### **Current Data**
```
Users: 2 users
├── admin (System Administrator) → Role: admin
└── choa (Andrew Cho)           → Role: admin

Roles: 5 roles
├── admin     → ["*"] (all permissions)
├── manager   → [jobs, targets, executions, users, network read permissions]
├── operator  → [full operational permissions including network write]
├── developer → [development permissions, limited write access]
└── viewer    → [read-only permissions]
```

---

## 🎯 **Keycloak Target Architecture**

### **Keycloak Components**
```
Keycloak Server
├── Realm: opsconductor
├── Clients: 6 service clients
│   ├── identity-service
│   ├── asset-service  
│   ├── automation-service
│   ├── communication-service
│   ├── ai-brain
│   └── network-analyzer-service
├── Users: Migrated from current system
├── Roles: Mapped from current roles
└── Groups: Optional organizational structure
```

### **Authentication Flow**
```
Current: Custom JWT
├── Username/password → Custom validation
├── JWT generation with HS256
├── Token contains: user_id, username, role, permissions
└── 1-hour expiration

Target: Keycloak OAuth2/OIDC
├── Username/password → Keycloak validation
├── OAuth2 Authorization Code flow
├── JWT with RS256 (public key validation)
├── Access token (short-lived) + Refresh token
└── Configurable expiration policies
```

---

## 🔄 **Migration Strategy**

### **Phase 1: Keycloak Deployment (Week 2)**

#### **Day 1-2: Core Deployment**
```yaml
# docker-compose.yml addition
services:
  keycloak:
    image: quay.io/keycloak/keycloak:22.0
    command: start-dev
    environment:
      KC_DB: postgres
      KC_DB_URL: jdbc:postgresql://postgres:5432/keycloak
      KC_DB_USERNAME: keycloak
      KC_DB_PASSWORD: ${KEYCLOAK_DB_PASSWORD}
      KEYCLOAK_ADMIN: admin
      KEYCLOAK_ADMIN_PASSWORD: ${KEYCLOAK_ADMIN_PASSWORD}
      KC_HOSTNAME: ${KEYCLOAK_HOSTNAME:-localhost}
      KC_HOSTNAME_PORT: 8080
      KC_HOSTNAME_STRICT: false
      KC_HOSTNAME_STRICT_HTTPS: false
    ports:
      - "8080:8080"
    depends_on:
      - postgres
    volumes:
      - keycloak_data:/opt/keycloak/data
      - ./keycloak/themes:/opt/keycloak/themes
```

#### **Day 3-4: Realm Configuration**
```bash
# Create OpsConductor realm
# Configure realm settings:
# - Login settings (remember me, registration, etc.)
# - Session settings (timeout, SSO session idle, etc.)  
# - Security settings (password policies, brute force protection)
# - Email settings (SMTP configuration)
# - Themes (OpsConductor branding)
```

#### **Day 5-7: Client Configuration**
```json
// Service clients configuration
{
  "clients": [
    {
      "clientId": "identity-service",
      "protocol": "openid-connect",
      "clientAuthenticatorType": "client-secret",
      "redirectUris": ["http://localhost:3001/*"],
      "webOrigins": ["*"],
      "serviceAccountsEnabled": true,
      "authorizationServicesEnabled": true
    },
    // ... similar for other services
  ]
}
```

### **Phase 2: Data Migration (Week 3)**

#### **User Migration Script**
```python
# scripts/migrate_users_to_keycloak.py
import asyncio
import asyncpg
from keycloak import KeycloakAdmin

async def migrate_users():
    # Connect to current database
    conn = await asyncpg.connect("postgresql://postgres@localhost/opsconductor")
    
    # Get Keycloak admin client
    keycloak_admin = KeycloakAdmin(
        server_url="http://localhost:8080/",
        username="admin",
        password="admin123",
        realm_name="opsconductor"
    )
    
    # Migrate users
    users = await conn.fetch("SELECT * FROM identity.users")
    for user in users:
        keycloak_user = {
            "username": user['username'],
            "email": user['email'],
            "firstName": user['first_name'],
            "lastName": user['last_name'],
            "enabled": user['is_active'],
            "emailVerified": True,
            "attributes": {
                "telephone": user['telephone'] or "",
                "title": user['title'] or "",
                "legacy_id": str(user['id'])
            }
        }
        
        # Create user in Keycloak
        user_id = keycloak_admin.create_user(keycloak_user)
        
        # Set password (temporary - users should reset)
        keycloak_admin.set_user_password(user_id, "TempPassword123!", temporary=True)
        
        # Assign roles
        user_roles = await conn.fetch(
            "SELECT r.name FROM identity.roles r "
            "JOIN identity.user_roles ur ON r.id = ur.role_id "
            "WHERE ur.user_id = $1", user['id']
        )
        
        for role in user_roles:
            keycloak_admin.assign_realm_roles(user_id, [role['name']])
```

#### **Role Migration Script**
```python
# scripts/migrate_roles_to_keycloak.py
async def migrate_roles():
    conn = await asyncpg.connect("postgresql://postgres@localhost/opsconductor")
    
    keycloak_admin = KeycloakAdmin(
        server_url="http://localhost:8080/",
        username="admin", 
        password="admin123",
        realm_name="opsconductor"
    )
    
    # Migrate roles
    roles = await conn.fetch("SELECT * FROM identity.roles WHERE is_active = true")
    for role in roles:
        keycloak_role = {
            "name": role['name'],
            "description": role['description'],
            "attributes": {
                "permissions": role['permissions']  # Store as attributes
            }
        }
        
        keycloak_admin.create_realm_role(keycloak_role)
```

### **Phase 3: Service Integration (Week 4)**

#### **Authentication Middleware Update**
```python
# shared/keycloak_auth.py
from keycloak import KeycloakOpenID
from fastapi import HTTPException, Depends
from fastapi.security import HTTPBearer

class KeycloakAuth:
    def __init__(self):
        self.keycloak_openid = KeycloakOpenID(
            server_url="http://keycloak:8080/",
            client_id="identity-service",
            realm_name="opsconductor",
            client_secret_key="your-client-secret"
        )
    
    async def verify_token(self, token: str) -> dict:
        try:
            # Introspect token
            token_info = self.keycloak_openid.introspect(token)
            if not token_info.get('active'):
                raise HTTPException(401, "Token is not active")
            
            # Get user info
            user_info = self.keycloak_openid.userinfo(token)
            
            return {
                "user_id": user_info.get("sub"),
                "username": user_info.get("preferred_username"),
                "email": user_info.get("email"),
                "roles": token_info.get("realm_access", {}).get("roles", []),
                "permissions": self._extract_permissions(token_info)
            }
        except Exception as e:
            raise HTTPException(401, f"Token verification failed: {e}")
    
    def _extract_permissions(self, token_info: dict) -> list:
        # Extract permissions from roles or token claims
        roles = token_info.get("realm_access", {}).get("roles", [])
        permissions = []
        
        # Map roles to permissions (could be stored in Keycloak attributes)
        role_permission_map = {
            "admin": ["*"],
            "manager": ["jobs:read", "jobs:create", "jobs:update", "jobs:execute", 
                      "targets:read", "targets:create", "targets:update", 
                      "executions:read", "users:read", "network:analysis:read", 
                      "network:monitoring:read"],
            # ... other role mappings
        }
        
        for role in roles:
            permissions.extend(role_permission_map.get(role, []))
        
        return list(set(permissions))  # Remove duplicates

# Update base_service.py
security = HTTPBearer()
keycloak_auth = KeycloakAuth()

async def get_current_user(token: str = Depends(security)):
    return await keycloak_auth.verify_token(token.credentials)
```

#### **Service Updates**
```python
# Update each service to use Keycloak authentication
# Example for asset-service/main.py

from shared.keycloak_auth import get_current_user

@app.get("/assets")
async def get_assets(current_user: dict = Depends(get_current_user)):
    # User is already authenticated and authorized
    # current_user contains: user_id, username, email, roles, permissions
    
    # Check permissions
    if "assets:read" not in current_user["permissions"] and "*" not in current_user["permissions"]:
        raise HTTPException(403, "Insufficient permissions")
    
    # Proceed with business logic
    return await fetch_assets()
```

### **Phase 4: Frontend Integration (Week 5)**

#### **Frontend Authentication Update**
```typescript
// frontend/src/services/auth.ts
class KeycloakAuthService {
  private keycloak: Keycloak;
  
  constructor() {
    this.keycloak = new Keycloak({
      url: 'http://localhost:8080/',
      realm: 'opsconductor',
      clientId: 'opsconductor-frontend'
    });
  }
  
  async init(): Promise<boolean> {
    return await this.keycloak.init({
      onLoad: 'login-required',
      checkLoginIframe: false
    });
  }
  
  login(): void {
    this.keycloak.login();
  }
  
  logout(): void {
    this.keycloak.logout();
  }
  
  getToken(): string | undefined {
    return this.keycloak.token;
  }
  
  getUserInfo(): any {
    return this.keycloak.tokenParsed;
  }
  
  hasRole(role: string): boolean {
    return this.keycloak.hasRealmRole(role);
  }
  
  hasPermission(permission: string): boolean {
    const roles = this.keycloak.realmAccess?.roles || [];
    // Check permission logic based on roles
    return this.checkPermissionFromRoles(roles, permission);
  }
}
```

---

## 🔄 **Migration Phases & Timeline**

### **Week 2: Keycloak Deployment**
- ✅ Deploy Keycloak with PostgreSQL
- ✅ Create OpsConductor realm
- ✅ Configure basic security settings
- ✅ Set up admin users

### **Week 3: Configuration & Migration**
- ✅ Create service clients
- ✅ Configure OAuth2/OIDC flows
- ✅ Migrate users and roles
- ✅ Test authentication flows

### **Week 4: Service Integration**
- ✅ Update authentication middleware
- ✅ Update all services to use Keycloak
- ✅ Test service-to-service authentication
- ✅ Parallel testing with current system

### **Week 5: Frontend & Cutover**
- ✅ Update frontend authentication
- ✅ User acceptance testing
- ✅ Gradual traffic migration
- ✅ Decommission custom identity service

---

## 📊 **Benefits Analysis**

### **Code Reduction**
- **Eliminated:** 1,100+ lines of custom identity code
- **Replaced with:** ~200 lines of Keycloak integration
- **Maintenance:** Zero custom authentication code to maintain

### **Enterprise Features Gained**
- ✅ **Single Sign-On (SSO)** - SAML, OAuth2, OpenID Connect
- ✅ **Multi-Factor Authentication (MFA)** - TOTP, SMS, Email
- ✅ **User Federation** - LDAP, Active Directory integration
- ✅ **Advanced RBAC** - Fine-grained permissions, groups
- ✅ **Session Management** - Configurable timeouts, concurrent sessions
- ✅ **Brute Force Protection** - Account lockout, CAPTCHA
- ✅ **Audit Logging** - Complete authentication audit trail
- ✅ **Admin UI** - User management, role assignment
- ✅ **Self-Service** - Password reset, profile management
- ✅ **Compliance** - GDPR, SOC2 ready

### **Security Improvements**
- ✅ **RS256 JWT** - Public key validation (vs current HS256)
- ✅ **Token Introspection** - Real-time token validation
- ✅ **Refresh Tokens** - Secure token renewal
- ✅ **Password Policies** - Complexity, expiration, history
- ✅ **Account Lockout** - Brute force protection
- ✅ **Session Security** - Secure session management

---

## ⚠️ **Migration Risks & Mitigation**

### **High Risk Items**
1. **User Experience Changes**
   - **Risk:** Users need to learn new login flow
   - **Mitigation:** Gradual rollout, user training, documentation

2. **Service Integration Complexity**
   - **Risk:** Breaking existing service authentication
   - **Mitigation:** Parallel deployment, feature flags, rollback plan

3. **Data Migration Issues**
   - **Risk:** User/role data corruption or loss
   - **Mitigation:** Full database backup, migration testing, validation scripts

### **Medium Risk Items**
1. **Performance Impact**
   - **Risk:** Additional network calls for token validation
   - **Mitigation:** Token caching, connection pooling, performance testing

2. **Configuration Complexity**
   - **Risk:** Misconfigured clients or roles
   - **Mitigation:** Infrastructure as code, automated testing, peer review

### **Low Risk Items**
1. **Keycloak Learning Curve**
   - **Risk:** Team unfamiliarity with Keycloak
   - **Mitigation:** Training, documentation, community support

---

## 🎯 **Success Criteria**

### **Technical Success**
- ✅ All services authenticate via Keycloak
- ✅ Zero downtime during migration
- ✅ All existing users can login
- ✅ All role-based permissions work correctly
- ✅ Performance maintained or improved

### **Business Success**
- ✅ 1,100+ lines of custom code eliminated
- ✅ Enterprise SSO capabilities available
- ✅ MFA ready for security compliance
- ✅ Admin UI for user management
- ✅ Audit logging for compliance

### **User Success**
- ✅ Seamless login experience
- ✅ No loss of functionality
- ✅ Self-service password reset
- ✅ Better security (MFA available)

---

## 📋 **Next Steps**

### **Immediate Actions (This Week)**
1. **Review and approve migration plan**
2. **Set up development Keycloak instance**
3. **Create migration scripts**
4. **Plan user communication strategy**

### **Week 2 Kickoff**
1. **Deploy Keycloak to development environment**
2. **Create OpsConductor realm and basic configuration**
3. **Begin service client setup**
4. **Start user/role migration script development**

**Ready to proceed with Phase 2 deployment?** 🚀