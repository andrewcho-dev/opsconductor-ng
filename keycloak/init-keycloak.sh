#!/bin/bash

# Keycloak Initialization Script for OpsConductor
# This script sets up Keycloak with the OpsConductor realm and initial configuration

set -e

echo "🚀 Starting Keycloak initialization for OpsConductor..."

# Wait for Keycloak to be ready
echo "⏳ Waiting for Keycloak to be ready..."
until curl -f http://localhost:8080/auth/health/ready; do
    echo "Waiting for Keycloak..."
    sleep 5
done

echo "✅ Keycloak is ready!"

# Check if realm already exists
REALM_EXISTS=$(curl -s -o /dev/null -w "%{http_code}" \
    -H "Authorization: Bearer $KEYCLOAK_ADMIN_TOKEN" \
    http://localhost:8080/auth/admin/realms/opsconductor)

if [ "$REALM_EXISTS" = "200" ]; then
    echo "✅ OpsConductor realm already exists"
else
    echo "📦 Creating OpsConductor realm..."
    
    # Import realm configuration
    curl -X POST \
        -H "Authorization: Bearer $KEYCLOAK_ADMIN_TOKEN" \
        -H "Content-Type: application/json" \
        -d @/opt/keycloak/data/import/opsconductor-realm.json \
        http://localhost:8080/auth/admin/realms
    
    echo "✅ OpsConductor realm created successfully"
fi

echo "🎉 Keycloak initialization completed!"

# Display important information
echo ""
echo "📋 Keycloak Configuration Summary:"
echo "   - Admin Console: http://localhost:8080/auth/admin"
echo "   - Realm: opsconductor"
echo "   - Frontend Client: opsconductor-frontend"
echo "   - Services Client: opsconductor-services"
echo "   - Default Admin User: admin/admin123 (temporary password)"
echo "   - Default Operator User: operator/operator123 (temporary password)"
echo ""
echo "⚠️  Remember to change default passwords on first login!"