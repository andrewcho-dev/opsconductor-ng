# OpsConductor Asset Service

The Asset Service is responsible for managing target systems and their connection credentials in OpsConductor. It provides a RESTful API for creating, retrieving, updating, and deleting assets, as well as testing connections to those assets.

## Features

- Consolidated asset management in a single table
- Secure credential storage with encryption
- Support for multiple service types (SSH, HTTP, WinRM, RDP, SMB, SNMP, databases, etc.)
- Connection testing for various protocols including SSH, HTTP, FTP, SMTP, WinRM, RDP, SMB, SNMP, and databases
- Key rotation support for credential encryption

## API Endpoints

### Metadata

- `GET /api/v1/metadata` - Get metadata for dropdowns and form options

### Assets

- `GET /api/v1/assets` - List all assets with optional filtering
- `POST /api/v1/assets` - Create a new asset
- `GET /api/v1/assets/{asset_id}` - Get asset by ID
- `PUT /api/v1/assets/{asset_id}` - Update an asset
- `DELETE /api/v1/assets/{asset_id}` - Delete an asset
- `POST /api/v1/assets/{asset_id}/test` - Test connection to an asset

## Configuration

The Asset Service is configured using environment variables:

- `SERVICE_NAME` - Service name (should be "asset-service")
- `DB_HOST` - Database host
- `DB_PORT` - Database port
- `DB_NAME` - Database name
- `DB_USER` - Database user
- `DB_PASSWORD` - Database password
- `DB_SCHEMA` - Database schema (should be "assets")
- `REDIS_URL` - Redis URL for caching
- `IDENTITY_SERVICE_URL` - URL of the Identity Service
- `AUTOMATION_SERVICE_URL` - URL of the Automation Service
- `ASSET_SERVICE_ENCRYPTION_KEY` - Encryption key for credentials
- `ASSET_SERVICE_PREVIOUS_KEYS` - Previous encryption keys for key rotation (comma-separated)
- `ENCRYPTION_KEY` - Legacy encryption key (for backward compatibility)

## Security

The Asset Service implements several security measures to protect sensitive credential information and ensure secure operations.

### Credential Encryption

The service uses Fernet symmetric encryption (AES-128 in CBC mode with PKCS7 padding) to protect sensitive credential information. This provides:

- Strong encryption of all sensitive fields
- Authentication to prevent tampering with encrypted data
- Protection against padding oracle attacks

### Service-Specific Encryption Keys

Each service uses its own encryption key, which provides:

- Isolation between services
- Ability to rotate keys independently
- Reduced impact if a single key is compromised

### Key Rotation

Key rotation is fully supported to allow for periodic key changes without disrupting service:

1. Generate a new encryption key:
   ```
   python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
   ```

2. Set the new key as `ASSET_SERVICE_ENCRYPTION_KEY` and move the old key to `ASSET_SERVICE_PREVIOUS_KEYS`.

3. Restart the service. Existing credentials will still be decryptable, and new credentials will be encrypted with the new key.

4. Re-encrypt existing credentials with the new key by updating each asset or by running a migration script.

### Recommended Key Rotation Schedule

- **Production environments**: Rotate keys every 90 days
- **Development environments**: Rotate keys every 180 days
- **After security incidents**: Immediately rotate keys if a breach is suspected

### Authentication and Authorization

The Asset Service integrates with the Identity Service for authentication:

- All API endpoints require a valid JWT token
- User identity is extracted from the token for auditing
- Role-based access control is applied to operations

### Secure Connection Testing

Connection testing is implemented with security in mind:

- Credentials are only decrypted when needed for testing
- Timeouts prevent hanging connections
- SSL/TLS verification for secure protocols
- Proper error handling to avoid leaking sensitive information

The service supports specialized connection testing for:

- **SSH/SFTP**: Tests authentication with password or key-based methods
- **HTTP/HTTPS**: Tests web services with various authentication methods
- **FTP/FTPS**: Tests file transfer connections with secure options
- **SMTP/SMTPS**: Tests email server connections with STARTTLS support
- **WinRM**: Tests Windows Remote Management with domain authentication
- **RDP**: Tests Remote Desktop Protocol connections with domain support
- **SMB/CIFS**: Tests Windows file sharing connections with authentication
- **SNMP**: Tests Simple Network Management Protocol with community strings
- **Databases**: Tests connections to PostgreSQL, MySQL, MongoDB, and Redis

### Audit Logging

The service logs important security events:

- Authentication attempts
- Asset creation and modification
- Credential access
- Connection testing results
- Key rotation events

### Security Best Practices

When working with the Asset Service, follow these best practices:

1. **Generate strong encryption keys**: Always use the cryptography library's key generation function, never create keys manually.

2. **Store keys securely**: Use environment variables or a secrets management service, never hardcode keys in configuration files.

3. **Implement least privilege**: Only grant access to the Asset Service to users who need it.

4. **Regular security reviews**: Periodically review access logs and credential usage.

5. **Secure API access**: Always use HTTPS for API access in production environments.

## Development

### Running Tests

#### Unit Tests

To run the unit tests:

```
cd /home/opsconductor/opsconductor-ng/asset-service
python -m unittest discover tests "test_asset_service.py"
```

To run the shared credential utility tests:

```
cd /home/opsconductor/opsconductor-ng/shared
python -m unittest discover tests "test_credential_utils.py"
```

#### Integration Tests

To run the integration tests:

```
cd /home/opsconductor/opsconductor-ng/asset-service
python -m unittest tests/test_asset_service_integration.py
```

These integration tests verify the API endpoints with a mocked database. They test the full flow of asset management operations:

1. Creating an asset
2. Retrieving an asset
3. Updating an asset
4. Testing connection to an asset
5. Deleting an asset

The tests use FastAPI's TestClient to make requests to the API endpoints and verify the responses.

### Local Development

To run the service locally:

```
cd /home/opsconductor/opsconductor-ng
docker-compose up asset-service
```

## Database Schema

The Asset Service uses a consolidated schema with a single `assets.assets` table that contains all asset information, including credentials. This approach simplifies the data model and improves performance.

## Connection Testing

The Asset Service supports comprehensive testing of connections to assets using various protocols:

### Supported Protocols

- **HTTP/HTTPS**: Tests web services with support for various authentication methods:
  - Basic authentication (username/password)
  - API key authentication
  - Bearer token authentication
  - SSL/TLS for secure connections

- **SSH/SFTP**: Tests SSH connections with support for:
  - Password authentication
  - Private key authentication (with optional passphrase)
  - Proper error handling for authentication failures

- **Database Connections**:
  - PostgreSQL: Full connection testing with authentication
  - MySQL: Full connection testing with authentication
  - MongoDB: Connection and authentication testing
  - Redis: Connection and authentication testing
  - Other database types: Basic TCP connection testing

- **FTP/FTPS**: Tests file transfer connections with:
  - Anonymous or authenticated connections
  - Secure FTP (FTPS) with SSL/TLS
  - Directory listing verification

- **SMTP/SMTPS**: Tests email server connections with:
  - Plain SMTP connections
  - STARTTLS support for upgrading connections
  - Direct SSL/TLS connections (SMTPS)
  - Authentication testing

### Connection Testing Process

1. When a connection test is requested, the service selects the appropriate testing method based on the asset's service type.
2. The service attempts to establish a connection using the stored credentials.
3. The connection status is updated in the database and returned in the API response.
4. Detailed error information is logged for troubleshooting.

### Timeouts and Error Handling

- All connection tests have appropriate timeouts to prevent hanging connections.
- Connection tests gracefully handle various error conditions:
  - Network errors
  - Authentication failures
  - SSL/TLS errors
  - Permission errors
  - Timeout errors

### Fallback Mechanism

If a protocol-specific test fails or the required library is not available, the service falls back to a basic TCP connection test to verify that the port is at least open and reachable.