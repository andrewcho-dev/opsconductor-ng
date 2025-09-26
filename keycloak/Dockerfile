FROM quay.io/keycloak/keycloak:26.0.7

# Copy realm configuration
COPY opsconductor-realm-simple.json /opt/keycloak/data/import/

# Set environment variables for import
ENV KEYCLOAK_IMPORT=/opt/keycloak/data/import/opsconductor-realm-simple.json

# Enable health and metrics
ENV KC_HEALTH_ENABLED=true
ENV KC_METRICS_ENABLED=true

# Configure database
ENV KC_DB=postgres

# Configure hostname
ENV KC_HOSTNAME_STRICT=false
ENV KC_HOSTNAME_STRICT_HTTPS=false

# Configure proxy
ENV KC_PROXY=edge

# Enable import on startup
ENV KC_IMPORT_REALM=true

# Build the Keycloak image with optimizations
RUN /opt/keycloak/bin/kc.sh build

# Set the entrypoint
ENTRYPOINT ["/opt/keycloak/bin/kc.sh"]