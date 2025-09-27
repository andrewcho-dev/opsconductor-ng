# Traefik Dockerfile for OpsConductor V3
# Phase 5: Advanced Reverse Proxy with SSL Automation

FROM traefik:v3.0

# Install additional tools for debugging and monitoring
RUN apk add --no-cache \
    curl \
    jq \
    openssl \
    ca-certificates

# Create directories for configuration and certificates
RUN mkdir -p /etc/traefik /letsencrypt /var/log/traefik

# Copy configuration files
COPY traefik.yml /etc/traefik/traefik.yml
COPY dynamic.yml /etc/traefik/dynamic.yml

# Set proper permissions
RUN chmod 600 /etc/traefik/traefik.yml /etc/traefik/dynamic.yml
RUN chmod 700 /letsencrypt

# Create non-root user for security
RUN addgroup -g 1000 traefik && \
    adduser -D -s /bin/sh -u 1000 -G traefik traefik

# Change ownership of directories
RUN chown -R traefik:traefik /etc/traefik /letsencrypt /var/log/traefik

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=30s --retries=3 \
    CMD curl -f http://localhost:8081/api/rawdata || exit 1

# Switch to non-root user (but keep root for Docker socket access)
# USER traefik

# Expose ports
EXPOSE 80 443 8080 8081

# Start Traefik
ENTRYPOINT ["traefik"]
CMD ["--configfile=/etc/traefik/traefik.yml"]