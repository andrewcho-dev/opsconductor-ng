#!/bin/bash

# Setup script for OpsConductor environment
# This script generates the master encryption key and sets up the .env file

set -e

echo "🔧 Setting up OpsConductor environment..."

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

print_status() {
    if [ $1 -eq 0 ]; then
        echo -e "${GREEN}✓ $2${NC}"
    else
        echo -e "${RED}✗ $2${NC}"
        exit 1
    fi
}

print_info() {
    echo -e "${YELLOW}ℹ $1${NC}"
}

# Check if .env already exists
if [ -f .env ]; then
    print_info ".env file already exists. Backing up to .env.backup"
    cp .env .env.backup
fi

# Generate master key for credentials encryption
print_info "Generating master encryption key..."
MASTER_KEY_B64=$(openssl rand -base64 32)
print_status 0 "Master key generated"

# Generate JWT secrets
print_info "Generating JWT secrets..."
JWT_SECRET=$(openssl rand -base64 64)
JWT_REFRESH_SECRET=$(openssl rand -base64 64)
print_status 0 "JWT secrets generated"

# Create .env file
print_info "Creating .env file..."
cat > .env << EOF
# OpsConductor Environment Configuration
# Generated on $(date)

# Master encryption key for credentials service (base64 encoded, 32 bytes)
MASTER_KEY_B64=${MASTER_KEY_B64}

# JWT Secrets
JWT_SECRET=${JWT_SECRET}
JWT_REFRESH_SECRET=${JWT_REFRESH_SECRET}

# Database Configuration
POSTGRES_DB=opsconductor
POSTGRES_USER=opsconductor
POSTGRES_PASSWORD=opsconductor123

# Service Ports (for development)
AUTH_SERVICE_PORT=3002
USER_SERVICE_PORT=3001
CREDENTIALS_SERVICE_PORT=3004
TARGETS_SERVICE_PORT=3005
FRONTEND_PORT=3000

# External Ports
HTTP_PORT=80
HTTPS_PORT=443
POSTGRES_PORT=5432
EOF

print_status 0 ".env file created"

# Set appropriate permissions
chmod 600 .env
print_status 0 "Set secure permissions on .env file"

echo ""
print_info "Environment setup complete!"
print_info "Master key: ${MASTER_KEY_B64:0:20}... (truncated for security)"
print_info ""
print_info "Next steps:"
print_info "1. Review the .env file and adjust settings if needed"
print_info "2. Run: docker-compose -f docker-compose-updated.yml up -d"
print_info "3. Test the services with the provided test scripts"
print_info ""
print_info "⚠️  IMPORTANT: Keep the .env file secure and never commit it to version control!"

echo ""
echo -e "${GREEN}🎉 Environment setup completed successfully!${NC}"